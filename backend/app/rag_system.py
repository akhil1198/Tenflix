import os
import logging
import json
from typing import Dict, List, Optional, Union, Any
import pandas as pd
import time
from datetime import datetime

import openai
from openai import OpenAI

from vector_database import MovieVectorDB
from dotenv import load_dotenv  # type: ignore

load_dotenv()
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MovieRAGSystem:
    """
    the core Retrieval-Augmented Generation (RAG) system for movie and TV show recommendations.
    it combines vector search with LLM-powered generation from OpenAI.
    """

    def __init__(
        self,
        vector_db: MovieVectorDB,
        openai_api_key: str,
        model_name: str = "gpt-4o",
        max_tokens: int = 1000,
        temperature: float = 0.7
    ):
        """
        Initializing the RAG system.
        """
        self.vector_db = vector_db  # for storage
        self.openai_api_key = openai_api_key  # for llm
        self.model_name = model_name  # openai model
        self.max_tokens = max_tokens
        self.temperature = temperature

        # Initializing the OpenAI client
        logger.info(f"Initializing OpenAI client with model {model_name}")
        self.client = OpenAI(api_key=openai_api_key)

        # Tracking usage
        self.usage_log = []

    def _log_usage(self, query_type: str, query: str, response_length: int) -> None:
        """
        Log system usage for analytics.
        """
        self.usage_log.append({
            "timestamp": datetime.now().isoformat(),
            "query_type": query_type,
            "query": query,
            "response_length": response_length
        })

    def generate_system_prompt(self, context: List[str]) -> str:
        """
        Generate the system prompt for the LLM based on retrieved context.
        """

        # for openai
        system_prompt = """You are a knowledgeable Movie and TV Show Recommendation Assistant. 
You provide accurate information and thoughtful recommendations about movies and TV shows.
Use the following retrieved information to answer the user's question.
If the retrieved information doesn't contain specific examples matching the query,
you should acknowledge this and then provide some general recommendations that might match,
clearly indicating they are general suggestions not from the database.

Retrieved Information:
"""

        # Add retrieved context to the prompt
        for i, doc in enumerate(context):
            system_prompt += f"\n[Document {i+1}]\n{doc}\n"

        system_prompt += "\nAnswer the user's question based only on the information provided above."
        return system_prompt

    def query_llm(self, system_prompt: str, user_query: str) -> str:
        """
        Query the LLM with system prompt and user query.
        """
        try:
            logger.info(
                f"Querying LLM with prompt length {len(system_prompt)}")

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_query}
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature
            )

            response_text = response.choices[0].message.content

            # Logging openai token usage
            total_tokens = response.usage.total_tokens
            logger.info(f"Query complete. Used {total_tokens} tokens.")

            return response_text

        except Exception as e:
            logger.error(f"Error querying LLM: {str(e)}")
            return "I'm sorry, I encountered an error while processing your request."

    def _parse_user_intent(self, query: str) -> Dict[str, Any]:
        """
        Parse user intent to determine query type and extract filters.
        """
        try:

            system_prompt = """You are a helpful assistant that analyzes movie and TV show related queries.
Given a user query, determine what type of request it is and extract any relevant filters.
Only respond with a JSON object having the following structure:
{
  "type": one of ["recommendation", "information", "comparison", "search", "other"],
  "filters": {
    "genres": ["genre1", "genre2"],
    "year_range": [start_year, end_year] or null,
    "actors": ["actor1", "actor2"],
    "directors": ["director1"],
    "similar_to": ["movie title"],
    "keywords": ["keyword1", "keyword2"]
  },
  "search_query": "extracted search terms for vector search"
}
"""

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query}
                ],
                max_tokens=500,
                temperature=0.1
            )
            print("response --- ", response)
            intent_text = response.choices[0].message.content.strip()

            # Extracting the JSON from potential markdown code blocks
            if "```json" in intent_text:
                intent_text = intent_text.split(
                    "```json")[1].split("```")[0].strip()
            elif "```" in intent_text:
                intent_text = intent_text.split(
                    "```")[1].split("```")[0].strip()

            intent_data = json.loads(intent_text)
            logger.info(
                f"Extracted intent: {intent_data['type']} with {len(intent_data['filters'])} filters")
            return intent_data

        except Exception as e:
            logger.error(f"Error parsing user intent: {str(e)}")
            # Return default intent
            return {
                "type": "search",
                "filters": {},
                "search_query": query
            }

    def _construct_vector_query(self, intent_data: Dict[str, Any]) -> Dict:
        """
        Construct vector database query based on intent data.
        """
        # Extract the search query
        search_query = intent_data.get("search_query", "")

        # Extracting and processing all the filters
        filters = {}
        intent_filters = intent_data.get("filters", {})

        if "genres" in intent_filters and intent_filters["genres"]:
            genre_list = "|".join(intent_filters["genres"])
            filters["genres"] = {"$contains": genre_list}

        if "year_range" in intent_filters and intent_filters["year_range"]:
            year_range = intent_filters["year_range"]
            if len(year_range) == 2 and year_range[0] and year_range[1]:
                filters["year"] = {"$gte": str(
                    year_range[0]), "$lte": str(year_range[1])}
            elif year_range[0]:
                filters["year"] = {"$gte": str(year_range[0])}
            elif year_range[1]:
                filters["year"] = {"$lte": str(year_range[1])}

        if "directors" in intent_filters and intent_filters["directors"]:
            director_list = "|".join(intent_filters["directors"])
            filters["directors"] = {"$contains": director_list}

        if "actors" in intent_filters and intent_filters["actors"]:
            actor_list = "|".join(intent_filters["actors"])
            filters["cast"] = {"$contains": actor_list}

        return {
            "query_text": search_query,
            "filters": filters if filters else None
        }

    def answer_question(self, user_query: str, n_results: int = 5) -> str:
        """
        Answer a user question using the RAG approach.
        """
        logger.info(f"Processing query: '{user_query}'")

        try:
            # Parse the user intent
            intent_data = self._parse_user_intent(user_query)

            # Construct the vector query
            vector_query = self._construct_vector_query(intent_data)

            # Retrieve all the relevant documents
            if vector_query["filters"]:
                logger.info(
                    f"Executing hybrid search with filters: {vector_query['filters']}")
                results = self.vector_db.hybrid_search(
                    query_text=vector_query["query_text"],
                    metadata_filters=vector_query["filters"],
                    n_results=n_results
                )
            else:
                logger.info("Executing semantic search without filters")
                results = self.vector_db.query_similar(
                    query_text=vector_query["query_text"],
                    n_results=n_results
                )

            # Extract documents from results
            if not results["documents"]:
                documents = []
            elif isinstance(results["documents"], list) and isinstance(results["documents"][0], list):
                documents = results["documents"][0]  # For query results
            else:
                documents = results["documents"]  # For get results

            if not documents:
                response = "I couldn't find any movies or shows matching your query in my database."
                self._log_usage("no_results", user_query, len(response))
                return response

            # Generate system prompt with context
            system_prompt = self.generate_system_prompt(documents)

            # Query the LLM
            response = self.query_llm(system_prompt, user_query)

            self._log_usage(intent_data["type"], user_query, len(response))

            return response

        except Exception as e:
            logger.error(f"Error answering question: {str(e)}")
            return "I'm sorry, I encountered an error while processing your request."

    def get_recommendations(
        self,
        preferences: str,
        n_results: int = 5,
        excluded_titles: Optional[List[str]] = None
    ) -> str:
        """
        Get personalized recommendations based on user preferences.
        """
        logger.info(f"Getting recommendations based on: '{preferences}'")

        try:
            # Parse the preferences into an intent
            intent_data = self._parse_user_intent(
                f"Recommend movies based on {preferences}")

            # Construct the vector query
            vector_query = self._construct_vector_query(intent_data)

            # Retrieve all the relevant documents just like in answer_question
            if vector_query["filters"]:
                results = self.vector_db.hybrid_search(
                    query_text=vector_query["query_text"],
                    metadata_filters=vector_query["filters"],
                    n_results=n_results * 2  # Get more to allow for filtering
                )
            else:
                results = self.vector_db.query_similar(
                    query_text=vector_query["query_text"],
                    n_results=n_results * 2  # Get more to allow for filtering
                )

            if not results["documents"] or not results["metadatas"]:
                documents = []
                metadatas = []
            elif isinstance(results["documents"], list) and isinstance(results["documents"][0], list):
                documents = results["documents"][0]
                metadatas = results["metadatas"][0]
            else:
                documents = results["documents"]
                metadatas = results["metadatas"]

            # Filtering out all the excluded titles if provided
            if excluded_titles and metadatas:
                filtered_documents = []
                filtered_metadatas = []

                for doc, meta in zip(documents, metadatas):
                    if meta.get("title") not in excluded_titles:
                        filtered_documents.append(doc)
                        filtered_metadatas.append(meta)

                documents = filtered_documents[:n_results]
                metadatas = filtered_metadatas[:n_results]
            else:
                # Limit to requested number
                documents = documents[:n_results]
                metadatas = metadatas[:n_results] if metadatas else []

            if not documents:
                response = "I couldn't find any recommendations matching your preferences."
                self._log_usage("no_recommendations",
                                preferences, len(response))
                return response

            system_prompt = """You are a Movie and TV Show Recommendation Assistant.
Based on the user's preferences, provide personalized recommendations from the retrieved items.
Explain why each recommendation matches their preferences.
Format the response in a clear, engaging way, with titles, years, and brief descriptions.

Retrieved Items:
"""

            # Add the retrieved context
            for i, (doc, meta) in enumerate(zip(documents, metadatas)):
                system_prompt += f"\n[Item {i+1}]\n{doc}\n"

            system_prompt += "\nProvide personalized recommendations based on the user's preferences."

            # Query LLM
            response = self.query_llm(
                system_prompt, f"Based on my interest in {preferences}, what would you recommend?")

            self._log_usage("recommendation", preferences, len(response))

            return response

        except Exception as e:
            logger.error(f"Error getting recommendations: {str(e)}")
            return "I'm sorry, I encountered an error while processing your recommendation request."

    def compare_titles(self, titles: List[str]) -> str:
        """
        Compare multiple movies or TV shows.
        """
        logger.info(f"Comparing titles: {titles}")

        try:
            all_documents = []

            for title in titles:
                # Search for the title
                results = self.vector_db.query_similar(
                    query_text=title,
                    n_results=1
                )

                # Extract document
                if results["documents"] and results["documents"][0]:
                    all_documents.append(results["documents"][0][0])

            if not all_documents:
                response = "I couldn't find any of the titles you mentioned in my database."
                self._log_usage("no_comparison", str(titles), len(response))
                return response

            system_prompt = """You are a Movie and TV Show Comparison Assistant.
Compare the following movies or TV shows, highlighting similarities and differences in:
- Genres, themes, and tone
- Directors and their styles
- Cast and performances
- Critical reception and audience response
- Cultural impact and legacy

Retrieved Information:
"""

            for i, doc in enumerate(all_documents):
                system_prompt += f"\n[Item {i+1}]\n{doc}\n"

            system_prompt += "\nProvide a thoughtful comparison of these titles."

            title_list = ", ".join(titles)
            user_query = f"Please compare these titles: {title_list}"

            response = self.query_llm(system_prompt, user_query)

            self._log_usage("comparison", title_list, len(response))

            return response

        except Exception as e:
            logger.error(f"Error comparing titles: {str(e)}")
            return "I'm sorry, I encountered an error while processing your comparison request."

    def export_usage_log(self, output_file: str = "usage_log.json") -> None:
        """
        Export usage log to a file.
        """
        try:
            with open(output_file, 'w') as f:
                json.dump(self.usage_log, f, indent=2)
            logger.info(f"Exported usage log to {output_file}")
        except Exception as e:
            logger.error(f"Error exporting usage log: {str(e)}")


if __name__ == "__main__":
    from vector_database import MovieVectorDB

    # Initialize vector database
    vector_db = MovieVectorDB(
        data_path="./processed_data",
        db_path="./chroma_db",
        collection_name="movie_collection"
    )

    # Initialize RAG system
    rag_system = MovieRAGSystem(
        vector_db=vector_db,
        openai_api_key=os.environ.get("OPENAI_API_KEY"),
        model_name="gpt-4o",
        max_tokens=1000,
        temperature=0.7
    )
