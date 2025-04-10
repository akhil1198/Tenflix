from routers import movies
import logging
from datetime import datetime
from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware


# Configuring logging
logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Initializing FastAPI
app = FastAPI(
    title="Movie & TV Show Recommendation API",
    description="API for querying and getting recommendations for movies and TV shows",
    version="1.0.0"
)

# CORS middleware for react frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# movie router
app.include_router(movies.router)

# Health check endpoint


@app.get("/health", status_code=status.HTTP_200_OK)
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "timestamp": datetime.now().isoformat()}

# Home endpoint


@app.get("/", status_code=status.HTTP_200_OK)
async def health_check():
    """Home endpoint."""
    return "Welcome to the Tenflix Server! Right now, it's ", datetime.now().isoformat(), "which means its time for a movie recommendation! "

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
