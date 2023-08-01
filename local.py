from fastapi import FastAPI
from pydantic import BaseModel
import pickle
from fastapi.middleware.cors import CORSMiddleware



movies = pickle.load(open("movies.pkl", "rb"))
similarity = pickle.load(open("similarity.pkl", "rb"))

def recommend(movie_name: str):
    movie_index = movies[movies["title"] == movie_name].index[0]
    distance = list(enumerate(similarity[movie_index]))
    sorted_movies = sorted(distance, key= lambda x: x[1], reverse=True)[1:6]
    
    recommended_movies = []
    for i in sorted_movies:
        movie_data = {
            "id": int(movies.iloc[i[0]]["id"]),
            "title": movies.iloc[i[0]]["title"],
            "tags": movies.iloc[i[0]]["tags"]
        }
        recommended_movies.append(movie_data)

    return recommended_movies

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # for dev; restrict in prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "Hello, World!"}

@app.get("/movies")
def get_movies():
    return {"movies": movies["title"].tolist()}

class MovieRequest(BaseModel):
    movie_name: str

@app.post("/recommend")
def get_recommendations(request: MovieRequest):
    recommendations = recommend(request.movie_name)
    return {
        "movie": request.movie_name,
        "recommendations": recommendations
    }