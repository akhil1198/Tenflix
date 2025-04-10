import pandas as pd
import numpy as np
import os
import logging
from tqdm import tqdm
import json
from typing import Dict, List, Tuple, Union, Optional

import sentence_transformers
from sentence_transformers import SentenceTransformer

from chromadb import Client, Settings
from chromadb.config import Settings
import chromadb.utils.embedding_functions as embedding_functions
from chromadb import PersistentClient
from chromadb.config import Settings
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MovieVectorDB:
    """
    Handles vector database operations for the Movie/TV Show RAG system.
    """

    def __init__(
        self,
        data_path: str,
        embedding_model_name: str = "all-MiniLM-L6-v2",
        db_path: str = "./chroma_db",
        collection_name: str = "movie_collection"
    ):
        """
        Initialize the vector database handler.
        """
        self.data_path = data_path
        self.embedding_model_name = embedding_model_name
        self.db_path = db_path
        self.collection_name = collection_name

        logger.info(f"Loading embedding model: {embedding_model_name}")
        self.embedding_model = SentenceTransformer(embedding_model_name)

        # Setting up the embedding function for ChromaDB
        self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=embedding_model_name
        )

        logger.info(f"Initializing ChromaDB at {db_path}")
        self.chroma_client = PersistentClient(
            path=db_path,
            settings=Settings(allow_reset=True)
        )

        try:
            self.collection = self.chroma_client.create_collection(
                name=collection_name,
                embedding_function=self.embedding_function
            )
            logger.info(f"Created new collection: {collection_name}")
        except Exception as e:
            try:
                self.collection = self.chroma_client.get_collection(
                    name=collection_name,
                    embedding_function=self.embedding_function
                )
                logger.info(f"Using existing collection: {collection_name}")
            except Exception:
                logger.error(f"Could not create or get collection: {str(e)}")
                raise

    def load_embeddings_data(self) -> pd.DataFrame:
        """
        Load the embeddings data created by the ETL pipeline.
        """
        embeddings_file = os.path.join(self.data_path, "embeddings_data.csv")
        logger.info(f"Loading embeddings data from {embeddings_file}")

        try:
            df = pd.read_csv(embeddings_file)
            logger.info(f"Loaded {len(df)} records for embeddings")
            return df
        except Exception as e:
            logger.error(f"Error loading embeddings data: {str(e)}")
            raise

    def create_embeddings(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Create embeddings for a list of texts.
        """
        logger.info(f"Creating embeddings for {len(texts)} texts")

        embeddings = []

        # Processing in batches
        for i in tqdm(range(0, len(texts), batch_size)):
            batch_texts = texts[i:i+batch_size]
            batch_embeddings = self.embedding_model.encode(batch_texts)
            embeddings.extend(batch_embeddings)

        return np.array(embeddings)

    def populate_vector_db(self) -> None:
        """
        Populate the vector database with movie/show data.
        """
        logger.info("Starting to populate vector database")

        df = self.load_embeddings_data()

        # Check if collection already has data
        if self.collection.count() > 0:
            logger.warning(
                f"Collection already contains {self.collection.count()} items")
            user_input = input("Do you want to clear and repopulate? (y/n): ")
            if user_input.lower() == 'y':
                self.collection.delete(where={})
                logger.info("Cleared existing collection")
            else:
                logger.info("Keeping existing data, skipping population")
                return

        # Prepare data for ChromaDB
        ids = df['tconst'].tolist()
        texts = df['chunk_text'].tolist()

        # Prepare the metadata
        metadatas = []
        for _, row in df.iterrows():
            metadata = {
                'title': row['title'],
                'year': row['year'],
                'media_type': row['media_type'],
                'genres': row['genres'],
                'directors': row['directors'],
                'cast': row['cast'][:200] if isinstance(row['cast'], str) else '',
            }
            metadatas.append(metadata)

        batch_size = 100

        for i in tqdm(range(0, len(ids), batch_size)):
            end_idx = min(i + batch_size, len(ids))

            batch_ids = ids[i:end_idx]
            batch_texts = texts[i:end_idx]
            batch_metadatas = metadatas[i:end_idx]

            try:
                self.collection.add(
                    ids=batch_ids,
                    documents=batch_texts,
                    metadatas=batch_metadatas
                )
            except Exception as e:
                logger.error(f"Error adding batch {i} to {end_idx}: {str(e)}")

        logger.info(
            f"Successfully populated vector database with {self.collection.count()} items")

        # Persist database to disk
        self.chroma_client.persist()
        logger.info("Vector database persisted to disk")

    def query_similar(
        self,
        query_text: str,
        n_results: int = 5,
        filter_criteria: Optional[Dict] = None
    ) -> Dict:
        """
        Query the vector database for similar movies/shows.
        """
        logger.info(f"Querying for: '{query_text}'")

        try:
            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results,
                where=filter_criteria
            )

            return results
        except Exception as e:
            logger.error(f"Error during query: {str(e)}")
            return {"ids": [], "documents": [], "metadatas": [], "distances": []}

    def filter_by_metadata(
        self,
        metadata_field: str,
        metadata_value: str,
        n_results: int = 5
    ) -> Dict:
        """
        Query movies/shows by metadata fields.
        """
        logger.info(f"Filtering by {metadata_field}: '{metadata_value}'")

        try:
            results = self.collection.get(
                where={metadata_field: {"$eq": metadata_value}},
                limit=n_results
            )

            if not results['ids']:
                name_variations = [
                    metadata_value,  # Full name
                    metadata_value.split()[-1],  # Last name
                    metadata_value.split()[0],  # First name
                ]

                for variation in name_variations:
                    results = self.collection.get(
                        where={metadata_field: {"$eq": variation}},
                        limit=n_results
                    )
                    if results['ids']:
                        break

            return results
        except Exception as e:
            logger.error(f"Error during metadata filter: {str(e)}")
            return {"ids": [], "documents": [], "metadatas": []}

    def hybrid_search(
        self,
        query_text: str,
        metadata_filters: Optional[Dict] = None,
        n_results: int = 5
    ) -> Dict:
        """
        Perform hybrid search combining semantic similarity with metadata filtering.
        """
        logger.info(
            f"Hybrid search for: '{query_text}' with filters: {metadata_filters}")

        try:
            logger.info(
                f"Collection has {self.collection.count()} total documents")
            sample = self.collection.get(limit=1)
            if sample["ids"]:
                logger.info(f"Sample metadata: {sample['metadatas'][0]}")

            results = self.collection.query(
                query_texts=[query_text],
                n_results=n_results * 3
            )

            logger.info(
                f"Found {len(results['ids'][0])} results without filters")

            # If we have the metadata filters
            if metadata_filters and results["ids"][0]:
                filtered_indices = []

                for i, meta in enumerate(results["metadatas"][0]):
                    include = True

                    # Check for case-insensitive substring match
                    if metadata_filters.get("genres") and meta.get("genres"):
                        genres_lower = meta["genres"].lower()
                        filter_genres = metadata_filters["genres"].get(
                            "$contains", "").lower()

                        # Check for common variations, testing for sci-fi for now
                        genre_match = False
                        if "sci-fi" in filter_genres:
                            sci_fi_terms = [
                                "sci-fi", "science fiction", "scifi", "sci fi"]
                            for term in sci_fi_terms:
                                if term in genres_lower:
                                    genre_match = True
                                    break
                        else:
                            genre_match = any(genre.strip().lower() in genres_lower
                                              for genre in filter_genres.split("|"))

                        if not genre_match:
                            include = False

                    if metadata_filters.get("year") and meta.get("year"):
                        try:
                            if "-" in meta["year"]:
                                item_year = int(meta["year"].split("-")[0])
                            else:
                                item_year = int(meta["year"])

                            # Checking for bounds
                            if metadata_filters["year"].get("$gte") and item_year < int(metadata_filters["year"]["$gte"]):
                                include = False
                            if metadata_filters["year"].get("$lte") and item_year > int(metadata_filters["year"]["$lte"]):
                                include = False
                        except (ValueError, TypeError):
                            pass

                    if include:
                        filtered_indices.append(i)

                # Apply filters to results
                if filtered_indices:
                    filtered_ids = [results["ids"][0][i]
                                    for i in filtered_indices]
                    filtered_docs = [results["documents"][0][i]
                                     for i in filtered_indices]
                    filtered_meta = [results["metadatas"][0][i]
                                     for i in filtered_indices]
                    filtered_dist = [results["distances"][0][i]
                                     for i in filtered_indices]

                    # Limit to requested number
                    filtered_ids = filtered_ids[:n_results]
                    filtered_docs = filtered_docs[:n_results]
                    filtered_meta = filtered_meta[:n_results]
                    filtered_dist = filtered_dist[:n_results]

                    return {
                        "ids": [filtered_ids],
                        "documents": [filtered_docs],
                        "metadatas": [filtered_meta],
                        "distances": [filtered_dist]
                    }
                else:
                    # when there are no results
                    return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

            if results["ids"][0]:
                logger.info("Top 5 initial results:")
                for i in range(min(5, len(results["metadatas"][0]))):
                    logger.info(f"Title: {results['metadatas'][0][i].get('title')} - "
                                f"Year: {results['metadatas'][0][i].get('year')} - "
                                f"Genres: {results['metadatas'][0][i].get('genres')}")

            return results

        except Exception as e:
            logger.error(f"Error during hybrid search: {str(e)}")
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}


if __name__ == "__main__":
    vector_db = MovieVectorDB(
        data_path="./processed_data",
        db_path="./chroma_db",
        collection_name="movie_collection"
    )

    # Populating the database
    vector_db.populate_vector_db()

    # def print_query_results(results):
    #     """Helper function to print query results safely"""
    #     if results and results.get("documents") and results["documents"][0]:
    #         for i, (doc, meta) in enumerate(zip(results["documents"][0], results["metadatas"][0])):
    #             print(
    #                 f"{i+1}. {meta.get('title', 'Unknown Title')} ({meta.get('year', 'Unknown Year')}) - {meta.get('media_type', 'Unknown Type')}")
    #             print(f"   Genres: {meta.get('genres', 'No genres')}")
    #             print(f"   Directors: {meta.get('directors', 'Unknown')}")
    #             print()
    #     else:
    #         print("No results found.")

    print("\nTotal items in collection:", vector_db.collection.count())

    # print("\nSimilar to 'science fiction movies with aliens':")
    # results = vector_db.query_similar(
    #     "science fiction movies with aliens", n_results=3)
    # print_query_results(results)

    # print("\nMovies directed by Christopher Nolan:")
    # results = vector_db.filter_by_metadata(
    #     "directors", "Christopher Nolan", n_results=3)
    # print_query_results(results)

    # print("\nHybrid search for 'funny action movies' from recent years:")
    # results = vector_db.hybrid_search(
    #     "funny action movies",
    #     metadata_filters={"year": {"$gte": "2010"}},  # Note the string
    #     n_results=3
    # )
    # print_query_results(results)
