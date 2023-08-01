from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import pickle
import requests
from fastapi.middleware.cors import CORSMiddleware
from io import BytesIO
import pandas as pd

# Global variables to store loaded data
movies = None
similarity = None

def load_data_from_gcs():
    """Load movies and similarity data from Google Cloud Storage"""
    global movies, similarity
    
    try:
        # URLs for the pickle files
        movies_url = "https://storage.googleapis.com/learning_machine_learning/movies.pkl"
        similarity_url = "https://storage.googleapis.com/learning_machine_learning/similarity.pkl"
        
        # Download movies.pkl
        movies_response = requests.get(movies_url)
        movies_response.raise_for_status()
        movies = pickle.load(BytesIO(movies_response.content))
        
        # Download similarity.pkl
        similarity_response = requests.get(similarity_url)
        similarity_response.raise_for_status()
        similarity = pickle.load(BytesIO(similarity_response.content))
        
        print("Data loaded successfully from Google Cloud Storage")
        
    except requests.RequestException as e:
        print(f"Error downloading files from GCS: {e}")
        raise
    except pickle.UnpicklingError as e:
        print(f"Error unpickling files: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error loading data: {e}")
        raise

def recommend(movie_name: str):
    """Recommend similar movies based on the input movie name"""
    if movies is None or similarity is None:
        raise HTTPException(status_code=500, detail="Data not loaded. Please try again later.")
    
    # Check if movie exists in the dataset
    movie_matches = movies[movies["title"] == movie_name]
    if movie_matches.empty:
        raise HTTPException(status_code=404, detail=f"Movie '{movie_name}' not found in the dataset")
    
    movie_index = movie_matches.index[0]
    distance = list(enumerate(similarity[movie_index]))
    sorted_movies = sorted(distance, key=lambda x: x[1], reverse=True)[1:6]
    
    recommended_movies = []
    for i in sorted_movies:
        movie_data = {
            "id": int(movies.iloc[i[0]]["id"]),
            "title": movies.iloc[i[0]]["title"],
            "tags": movies.iloc[i[0]]["tags"],
            "similarity_score": float(i[1])  # Added similarity score
        }
        recommended_movies.append(movie_data)

    return recommended_movies

# Initialize FastAPI app
app = FastAPI(title="Movie Recommender API", description="API for movie recommendations using content-based filtering")

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for dev; restrict in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    """Load data when the application starts"""
    try:
        load_data_from_gcs()
    except Exception as e:
        print(f"Failed to load data on startup: {e}")
        # You might want to exit the application or set a flag here

@app.get("/")
def read_root():
    return {"message": "Movie Recommender API is running!"}

@app.get("/health")
def health_check():
    """Health check endpoint"""
    data_loaded = movies is not None and similarity is not None
    return {
        "status": "healthy" if data_loaded else "unhealthy",
        "data_loaded": data_loaded
    }

@app.get("/movies")
def get_movies():
    """Get list of all available movies"""
    if movies is None:
        raise HTTPException(status_code=500, detail="Movie data not loaded")
    return {"movies": movies["title"].tolist()}

@app.get("/movies/search/{query}")
def search_movies(query: str):
    """Search for movies containing the query string"""
    if movies is None:
        raise HTTPException(status_code=500, detail="Movie data not loaded")
    
    # Case-insensitive search
    matching_movies = movies[movies["title"].str.contains(query, case=False, na=False)]
    return {"movies": matching_movies["title"].tolist()}

class MovieRequest(BaseModel):
    movie_name: str

@app.post("/recommend")
def get_recommendations(request: MovieRequest):
    """Get movie recommendations based on input movie"""
    try:
        recommendations = recommend(request.movie_name)
        return {
            "movie": request.movie_name,
            "recommendations": recommendations
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating recommendations: {str(e)}")

@app.post("/reload-data")
def reload_data():
    """Manually reload data from Google Cloud Storage"""
    try:
        load_data_from_gcs()
        return {"message": "Data reloaded successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to reload data: {str(e)}")