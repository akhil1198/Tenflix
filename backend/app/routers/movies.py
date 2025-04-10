import logging
from fastapi import APIRouter, HTTPException, Query, status

from models.schemas import QueryRequest, RecommendationRequest, ComparisonRequest
from vector_database import MovieVectorDB
from rag_system import MovieRAGSystem
from dotenv import load_dotenv  # type: ignore
import os

load_dotenv()
logger = logging.getLogger(__name__)
router = APIRouter(prefix="/movies", tags=["movies"])

# Initializing vectordb and rag components
vector_db = MovieVectorDB(
    data_path="./processed_data",
    db_path="./chroma_db",
    collection_name="movie_collection"
)

print("************************* OPENAI_API_KEY - ",
      os.environ.get("OPENAI_API_KEY"))

rag_system = MovieRAGSystem(
    vector_db=vector_db,
    openai_api_key=os.environ.get("OPENAI_API_KEY"),
    model_name="gpt-4o",
    max_tokens=1000,
    temperature=0.7
)

# search api


@router.get("/search", status_code=status.HTTP_200_OK)
async def search_movies(
    query: str = Query(..., description="Search query"),
    limit: int = Query(10, description="Number of results to return")
):
    """Search for movies and TV shows."""
    try:
        results = vector_db.query_similar(
            query_text=query,
            n_results=limit
        )

        # Formatting results
        formatted_results = []

        if results["documents"] and results["metadatas"]:
            if isinstance(results["documents"][0], list):
                documents = results["documents"][0]
                metadatas = results["metadatas"][0]
            else:
                documents = results["documents"]
                metadatas = results["metadatas"]

            for meta in metadatas:
                formatted_results.append({
                    "title": meta.get("title", ""),
                    "year": meta.get("year", ""),
                    "media_type": meta.get("media_type", ""),
                    "genres": meta.get("genres", "").split(", ") if meta.get("genres") else []
                })

        return {"results": formatted_results}

    except Exception as e:
        logger.error(f"Error in search: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during search"
        )


@router.post("/query", status_code=status.HTTP_200_OK)
async def query_information(request: QueryRequest):
    """Queries information about movies and TV shows."""
    try:
        answer = rag_system.answer_question(request.query)
        print("heres the answer ---------------------- ", answer)
        return {"answer": answer}

    except Exception as e:
        logger.error(f"Error in query: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during query processing"
        )

# recommendation API


@router.post("/recommend", status_code=status.HTTP_200_OK)
async def recommend_movies(request: RecommendationRequest):
    """Gets movie recommendations based on preferences."""
    try:
        recommendations = rag_system.get_recommendations(
            preferences=request.preferences,
            excluded_titles=[]
        )

        return {"recommendations": recommendations}

    except Exception as e:
        logger.error(f"Error in recommendations: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during recommendation processing"
        )

# comparison API


@router.post("/compare", status_code=status.HTTP_200_OK)
async def compare_movies(request: ComparisonRequest):
    """Compare multiple movies or TV shows."""
    try:
        comparison = rag_system.compare_titles(request.titles)
        return {"comparison": comparison}

    except Exception as e:
        logger.error(f"Error in comparison: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An error occurred during comparison"
        )
