import os
import pandas as pd
import requests
import json
import datetime as datetime
import logging
from tqdm import tqdm
import numpy as np
from typing import Dict, List, Optional, Union
import time

logging.basicConfig(level=logging.INFO, format=(
    '%(asctime)s - %(levelname)s - %(message)s'))
logger = logging.getLogger(__name__)

# This pipeline fetches data from various sources, transforms them and stores them as a CSV in the processed_data folder.


class MovieDataPipeline:
    def __init__(self, imdb_data_path: str, tmdb_api_key: str, movielens_data_path: str, output_path: str):
        self.imdb_data_path = imdb_data_path
        self.tmdb_api_key = tmdb_api_key
        self.movielens_data_path = movielens_data_path
        self.output_path = output_path

        # output directory
        os.makedirs(output_path, exist_ok=True)
        self.base_url = "https://api.themoviedb.org/3"

    def extract_imdb_data(self) -> Dict[str, pd.DataFrame]:
        logger.info('Extracting IMDb data...')
        imdb_files = {
            'basics': os.path.join(self.imdb_data_path, 'title.basics.tsv'),
            'ratings': os.path.join(self.imdb_data_path, 'title.ratings.tsv'),
            'crew': os.path.join(self.imdb_data_path, 'title.crew.tsv'),
            'principals': os.path.join(self.imdb_data_path, 'title.principals.tsv'),
            'names': os.path.join(self.imdb_data_path, 'name.basics.tsv')
        }

        imdb_data = {}

        for name, file_path in imdb_files.items():
            try:
                logger.info(f"Reading {name} file..")
                imdb_data[name] = pd.read_csv(
                    file_path, sep='\t', low_memory=False)
                logger.info(
                    f"Successfully loaded {name} with {len(imdb_data[name])} rows")
            except Exception as e:
                logger.error(f"Error loading {name}: {str(e)}")
                imdb_data[name] = pd.DataFrame()

        return imdb_data

    def extract_movielens_data(self) -> Dict[str, pd.DataFrame]:
        logger.info("Extracting MovieLens data...")

        movielens_files = {
            'movies': os.path.join(self.movielens_data_path, 'movies.csv'),
            'ratings': os.path.join(self.movielens_data_path, 'ratings.csv'),
            'tags': os.path.join(self.movielens_data_path, 'tags.csv'),
            'links': os.path.join(self.movielens_data_path, 'links.csv')
        }

        movielens_data = {}
        for name, file_path in movielens_files.items():
            try:
                logger.info(f"Reading {name} file...")
                movielens_data[name] = pd.read_csv(file_path)
                logger.info(
                    f"Successfully loaded {name} with {len(movielens_data[name])} rows")
            except Exception as e:
                logger.error(f"Error loading {name}: {str(e)}")
                movielens_data[name] = pd.DataFrame()

        return movielens_data

    def fetch_tmdb_data(self, imdb_ids: List[str], batch_size: int = 50) -> List[Dict]:
        """
        Fetch movie data from TMDB API using IMDb IDs.
        """
        logger.info(f"Fetching TMDB data for {len(imdb_ids)} movies...")

        tmdb_data = []

        # Process in batches to avoid rate limiting on the API
        for i in tqdm(range(0, len(imdb_ids), batch_size)):
            batch = imdb_ids[i:i+batch_size]

            for imdb_id in batch:
                try:
                    # Finding TMDB ID from IMDb ID
                    find_url = f"{self.base_url}/find/{imdb_id}"
                    params = {
                        "api_key": self.tmdb_api_key,
                        "external_source": "imdb_id"
                    }

                    response = requests.get(find_url, params=params)

                    if response.status_code == 200:
                        data = response.json()

                        # Checking here if movie or TV show was found
                        movie_results = data.get("movie_results", [])
                        tv_results = data.get("tv_results", [])

                        if movie_results:
                            tmdb_id = movie_results[0]["id"]
                            media_type = "movie"
                        elif tv_results:
                            tmdb_id = tv_results[0]["id"]
                            media_type = "tv"
                        else:
                            continue

                        # Getting detailed data
                        details_url = f"{self.base_url}/{media_type}/{tmdb_id}"
                        details_params = {
                            "api_key": self.tmdb_api_key,
                            "append_to_response": "credits,similar,recommendations,keywords,videos"
                        }

                        details_response = requests.get(
                            details_url, params=details_params)

                        if details_response.status_code == 200:
                            movie_data = details_response.json()
                            movie_data["imdb_id"] = imdb_id
                            movie_data["media_type"] = media_type
                            tmdb_data.append(movie_data)

                    # Adding delay here to avoid rate limiting
                    time.sleep(0.25)

                except Exception as e:
                    logger.error(
                        f"Error fetching TMDB data for {imdb_id}: {str(e)}")

        logger.info(
            f"Successfully fetched TMDB data for {len(tmdb_data)} movies")
        return tmdb_data

    def transform_data(self, imdb_data: Dict[str, pd.DataFrame], movielens_data: Dict[str, pd.DataFrame], tmdb_data: List[Dict]) -> Dict[str, pd.DataFrame]:
        logger.info("Transforming and merging data...")

        # Converting TMDB data to DataFrame
        tmdb_df = pd.DataFrame(tmdb_data)

        # Processing basic movie information
        basics_df = imdb_data['basics']
        ratings_df = imdb_data['ratings']

        # Filtering for movies and TV shows
        basics_filtered = basics_df[basics_df['titleType'].isin(
            ['movie', 'tvMovie', 'tvSeries', 'tvMiniSeries'])]

        # Merging IMDb data here
        imdb_merged = pd.merge(
            basics_filtered,
            ratings_df,
            on='tconst',
            how='left'
        )

        # Mapping MovieLens to IMDb IDs using links
        if not movielens_data['links'].empty and 'imdbId' in movielens_data['links'].columns:
            # Add 'tt' prefix to imdbId and convert to string
            movielens_data['links']['imdb_id'] = 'tt' + \
                movielens_data['links']['imdbId'].astype(str).str.zfill(7)

            # Merge MovieLens ratings
            ml_ratings = movielens_data['ratings'].groupby('movieId').agg({
                'rating': ['mean', 'count']
            })
            ml_ratings.columns = ['ml_rating_avg', 'ml_rating_count']
            ml_ratings = ml_ratings.reset_index()

            # Merge with links to get IMDb IDs
            ml_ratings = pd.merge(
                ml_ratings,
                movielens_data['links'],
                on='movieId',
                how='left'
            )

            # Now merging with the main dataframe
            imdb_merged = pd.merge(
                imdb_merged,
                ml_ratings,
                left_on='tconst',
                right_on='imdb_id',
                how='left'
            )

        # Processing the TMDB data for final enrichment
        if not tmdb_df.empty:
            # Extracting all the key TMDB features
            tmdb_features = tmdb_df[[
                'imdb_id', 'id', 'media_type', 'popularity', 'vote_average', 'vote_count']]

            final_df = pd.merge(
                imdb_merged,
                tmdb_features,
                left_on='tconst',
                right_on='imdb_id',
                how='left'
            )
        else:
            final_df = imdb_merged

        # Creating separate dataframes for movies and shows for easier processing
        movies_df = final_df[final_df['titleType'].isin(['movie', 'tvMovie'])]
        shows_df = final_df[final_df['titleType'].isin(
            ['tvSeries', 'tvMiniSeries'])]

        # Extracting genres into a separate table here
        genres_df = self._extract_genres(final_df)

        # doing the same with cast and crew here
        cast_df, crew_df = self._extract_people(imdb_data, final_df)

        transformed_data = {
            'movies': movies_df,
            'shows': shows_df,
            'genres': genres_df,
            'cast': cast_df,
            'crew': crew_df,
            'tmdb_raw': tmdb_df
        }

        return transformed_data

    def _extract_genres(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Extract genres into a separate normalized table.
        """
        genre_rows = []

        for _, row in df.iterrows():
            if pd.notna(row['genres']) and row['genres'] != '\\N':
                genres = row['genres'].split(',')
                for genre in genres:
                    genre_rows.append({
                        'tconst': row['tconst'],
                        'genre': genre.strip()
                    })

        return pd.DataFrame(genre_rows)

    def _extract_people(
        self,
        imdb_data: Dict[str, pd.DataFrame],
        movie_df: pd.DataFrame
    ) -> tuple:
        """
        Extract cast and crew into separate normalized tables.
        """
        principals_df = imdb_data['principals']
        names_df = imdb_data['names']
        crew_source_df = imdb_data['crew']

        # Filter to only include titles in the dataset
        valid_titles = set(movie_df['tconst'].tolist())
        principals_filtered = principals_df[principals_df['tconst'].isin(
            valid_titles)]

        # Process cast
        cast_df = principals_filtered[principals_filtered['category'].isin([
                                                                           'actor', 'actress'])]
        cast_df = pd.merge(
            cast_df,
            names_df[['nconst', 'primaryName']],
            on='nconst',
            how='left'
        )

        crew_rows = []

        crew_from_principals = principals_filtered[principals_filtered['category'].isin(
            ['director', 'writer', 'producer', 'composer', 'cinematographer']
        )]

        for _, row in crew_from_principals.iterrows():
            crew_rows.append({
                'tconst': row['tconst'],
                'nconst': row['nconst'],
                'role': row['category']
            })

        # from crew table
        if not crew_source_df.empty:
            for _, row in crew_source_df.iterrows():
                if row['tconst'] in valid_titles:
                    # process movie directors
                    if pd.notna(row.get('directors')) and row['directors'] != '\\N':
                        directors = row['directors'].split(',')
                        for director in directors:
                            crew_rows.append({
                                'tconst': row['tconst'],
                                'nconst': director.strip(),
                                'role': 'director'
                            })

                    # process the writers
                    if pd.notna(row.get('writers')) and row['writers'] != '\\N':
                        writers = row['writers'].split(',')
                        for writer in writers:
                            crew_rows.append({
                                'tconst': row['tconst'],
                                'nconst': writer.strip(),
                                'role': 'writer'
                            })

        crew_df = pd.DataFrame(crew_rows)

        crew_df = pd.merge(
            crew_df,
            names_df[['nconst', 'primaryName']],
            on='nconst',
            how='left'
        )

        return cast_df, crew_df

    def load_data(self, transformed_data: Dict[str, pd.DataFrame]) -> None:
        """
        Save transformed data to files.
        """
        logger.info("Saving processed data...")

        for name, df in transformed_data.items():
            output_file = os.path.join(self.output_path, f"{name}.csv")
            df.to_csv(output_file, index=False)
            logger.info(
                f"Saved {name} data with {len(df)} rows to {output_file}")

    def create_embeddings_data(self) -> pd.DataFrame:
        """
        this function creates a dataset specifically for generating embeddings. it basically combines relevant fields into document chunks for RAG.
        Using only a sample of the data to speed up processing on CPU
        """
        logger.info("Creating data for embeddings...")

        movies_df = pd.read_csv(os.path.join(
            self.output_path, "movies.csv"), low_memory=False)
        shows_df = pd.read_csv(os.path.join(
            self.output_path, "shows.csv"), low_memory=False)
        genres_df = pd.read_csv(os.path.join(
            self.output_path, "genres.csv"), low_memory=False)
        cast_df = pd.read_csv(os.path.join(
            self.output_path, "cast.csv"), low_memory=False)
        crew_df = pd.read_csv(os.path.join(
            self.output_path, "crew.csv"), low_memory=False)

        logger.info(
            f"Loaded {len(movies_df)} movies and {len(shows_df)} shows")

        # Sampling data
        movies_sample_size = min(10000, len(movies_df))
        shows_sample_size = min(7000, len(shows_df))

        logger.info(
            f"Sampling {movies_sample_size} movies and {shows_sample_size} shows")

        movies_df = movies_df.sample(n=movies_sample_size, random_state=42)
        shows_df = shows_df.sample(n=shows_sample_size, random_state=42)

        # Combining vboth movies and shows
        all_titles = pd.concat([movies_df, shows_df])
        logger.info(f"Total titles after sampling: {len(all_titles)}")

        # Getting the valid title IDs from the sample data
        valid_title_ids = set(all_titles['tconst'].tolist())

        # Filtering related tables to only include data for our sampled titles
        genres_df = genres_df[genres_df['tconst'].isin(valid_title_ids)]
        cast_df = cast_df[cast_df['tconst'].isin(valid_title_ids)]
        crew_df = crew_df[crew_df['tconst'].isin(valid_title_ids)]

        logger.info(
            f"Filtered to {len(genres_df)} genre entries, {len(cast_df)} cast entries, and {len(crew_df)} crew entries")

        if 'ordering' in cast_df.columns:
            cast_df = cast_df.sort_values(
                by=['ordering']).groupby('tconst').head(3)
        else:
            # If ordering column doesn't exist, just take the first 3
            cast_df = cast_df.groupby('tconst').head(3)

        # Creating embeddings data
        embedding_rows = []

        for _, title in all_titles.iterrows():
            tconst = title['tconst']

            # Basic info
            title_type = title['titleType']
            is_movie = title_type in ['movie', 'tvMovie']
            media_type = "Movie" if is_movie else "TV Show"

            title_text = title['primaryTitle']
            if pd.notna(title.get('originalTitle')) and title['originalTitle'] != title['primaryTitle']:
                title_text += f" (Original title: {title['originalTitle']})"

            year_text = ""
            if pd.notna(title.get('startYear')) and title['startYear'] != '\\N':
                year_text = f"{title['startYear']}"
                if not is_movie and pd.notna(title.get('endYear')) and title['endYear'] != '\\N':
                    year_text += f"-{title['endYear']}"

            # Get genres
            title_genres = genres_df[genres_df['tconst'] == tconst]
            if not title_genres.empty:
                genres_text = ", ".join([str(genre)
                                        for genre in title_genres['genre'].tolist()])
            else:
                genres_text = ""

            # Getting top cast
            title_cast = cast_df[cast_df['tconst'] == tconst]
            if not title_cast.empty:
                # Converting to strings before joining
                cast_names = [str(name)
                              for name in title_cast['primaryName'].tolist()]
                cast_text = ", ".join(cast_names)
            else:
                cast_text = ""

            directors = crew_df[(crew_df['tconst'] == tconst)
                                & (crew_df['role'] == 'director')]
            if not directors.empty:
                directors_text = ", ".join([str(name)
                                            for name in directors['primaryName'].tolist()])
            else:
                directors_text = ""

            writers = crew_df[(crew_df['tconst'] == tconst) &
                              (crew_df['role'] == 'writer')]
            if not writers.empty:
                writers_text = ", ".join([str(name)
                                          for name in writers['primaryName'].tolist()])
            else:
                writers_text = ""

            # Get ratings
            imdb_rating = ""
            if pd.notna(title.get('averageRating')) and pd.notna(title.get('numVotes')):
                imdb_rating = f"{title['averageRating']}/10 ({title['numVotes']} votes)"

            # Create content (truncate plot to reduce embedding size)
            plot_text = ""
            if pd.notna(title.get('plot')):
                plot_text = title['plot'][:200]  # Limit plot to 200 characters
                if len(str(title['plot'])) > 200:
                    plot_text += "..."
            elif pd.notna(title.get('outline')):
                plot_text = title['outline'][:200]
                if len(str(title['outline'])) > 200:
                    plot_text += "..."

            # constructing the chunk text here
            chunk_text = f"{title_text} ({year_text}) - {media_type}\n\n"

            if genres_text:
                chunk_text += f"Genres: {genres_text}\n"

            if imdb_rating:
                chunk_text += f"IMDb Rating: {imdb_rating}\n"

            if directors_text:
                chunk_text += f"Director(s): {directors_text}\n"

            if writers_text:
                chunk_text += f"Writer(s): {writers_text}\n"

            if cast_text:
                chunk_text += f"Cast: {cast_text}\n"

            if plot_text:
                chunk_text += f"\nPlot: {plot_text}\n"

            # Add to rows
            embedding_rows.append({
                'tconst': tconst,
                'title': title_text,
                'year': year_text,
                'media_type': media_type,
                'chunk_text': chunk_text,
                'genres': genres_text,
                'directors': directors_text,
                'cast': cast_text,
                'plot': plot_text,
            })

        embedding_df = pd.DataFrame(embedding_rows)

        logger.info(f"Created {len(embedding_df)} embedding rows")

        # Save to file
        output_file = os.path.join(self.output_path, "embeddings_data.csv")
        embedding_df.to_csv(output_file, index=False)
        logger.info(
            f"Saved embeddings data with {len(embedding_df)} rows to {output_file}")

        return embedding_df

    def run_pipeline(self, skip_extraction: bool = False) -> None:
        """
        Run the complete ETL pipeline.
        """
        logger.info("Starting Movie Data Pipeline...")

        # Check if processed data already exists to skip directly to creating the embeddings
        embeddings_file = os.path.join(self.output_path, "embeddings_data.csv")
        movies_file = os.path.join(self.output_path, "movies.csv")
        shows_file = os.path.join(self.output_path, "shows.csv")

        if skip_extraction and os.path.exists(movies_file) and os.path.exists(shows_file):
            logger.info(
                "Processed data files found. Skipping extraction and transformation.")

            # Skip to embeddings creation if embeddings don't exist yet
            if not os.path.exists(embeddings_file):
                logger.info(
                    "Creating embeddings data from existing processed files...")
                self.create_embeddings_data()
            else:
                logger.info(
                    "Embeddings data already exists. Pipeline complete.")

            return

        # Extracting data
        imdb_data = self.extract_imdb_data()
        movielens_data = self.extract_movielens_data()

        sample_size = 100  # Adjust based on rate limits and time constraints on the API
        imdb_ids_sample = imdb_data['basics'][imdb_data['basics']['titleType'].isin(
            ['movie', 'tvMovie', 'tvSeries', 'tvMiniSeries']
        )]['tconst'].sample(sample_size).tolist()

        # Fetch TMDB data
        tmdb_data = self.fetch_tmdb_data(imdb_ids_sample)

        # Transform data
        transformed_data = self.transform_data(
            imdb_data, movielens_data, tmdb_data)

        # Load data
        self.load_data(transformed_data)

        # Create embeddings data
        self.create_embeddings_data()

        logger.info("Movie Data Pipeline completed successfully!")


if __name__ == "__main__":
    pipeline = MovieDataPipeline(
        imdb_data_path="/Users/akhilshridhar/Downloads/MovieRecommendationSystem/backend/data/tmdb",
        tmdb_api_key="48f0c87cacf05a4e7e35e316b5c51a53",
        movielens_data_path="/Users/akhilshridhar/Downloads/MovieRecommendationSystem/backend/data/movielens",
        output_path="./processed_data"
    )

    pipeline.run_pipeline(skip_extraction=True)
