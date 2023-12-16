from typing import Iterable
import streamlit as st
import pandas as pd
import asyncio
import aiohttp
import joblib


similarity = joblib.load("./similarity.pkl")
new_movies_df = pd.read_csv("./new_movies_df.csv")

API_KEY = "64387cef"


def recommend(movie, length) -> list[str]:
    """
    The `recommend` function takes a movie title and a length as input, and returns a list of
    recommended movies based on similarity scores.

    :param movie: The movie parameter is the title of the movie for which you want to get
    recommendations
    :param length: The "length" parameter specifies the number of movie recommendations that you want to
    receive
    :return: a list of recommended movies. The length of the list is determined by the "length"
    parameter passed to the function.
    """
    index = new_movies_df[new_movies_df["title"] == movie].index[0]
    distances = sorted(
        list(enumerate(similarity[index])), reverse=True, key=lambda x: x[1]
    )
    recommendations = []
    for i in distances[1:]:
        if movie in new_movies_df.iloc[i[0]].title:
            continue
        recommendations.append(new_movies_df.iloc[i[0]].title)
    return recommendations[:length]


async def getMovieData(name: str, session: aiohttp.ClientSession):
    """
    The function `getMovieData` is an asynchronous function that takes in a movie name and a session
    object, and makes a GET request to the OMDB API to retrieve movie data.

    :param name: The name of the movie you want to get data for
    :type name: str
    :param session: The `session` parameter is an instance of `aiohttp.ClientSession`. It is used to
    make HTTP requests asynchronously. It allows you to reuse the same TCP connection for multiple
    requests, which can improve performance
    :type session: aiohttp.ClientSession
    :return: the response from the API call as a JSON object.
    """
    try:
        async with session.get(
            url=f"https://www.omdbapi.com/?apikey={API_KEY}&t={name}"
        ) as response:
            resp = await response.json()
            return resp

    except Exception as e:
        print("Unable to get url {} due to {}.".format(name, e.__class__))


async def getAllMovies(name: Iterable[str]):
    async with aiohttp.ClientSession() as session:
        ret = await asyncio.gather(*[getMovieData(name, session) for name in name])
        print("Finalized all. Returned  list of {} outputs.".format(len(ret)))
        return ret


# Create custom styles for my cards
st.markdown(
    """
            <style>
                .card-container{
                    display:flex;
                    flex-wrap:wrap;
                    align-items: center;
                    justify-content:space-around;
                    gap:16px;
                }
                .card{
                    flex: 1 1 220px;
                    max-width:240px;
                    position:relative;
                    border-radius: 16px;
                    overflow:hidden;
                    height:360px;
                }
                .card-image{
                    position:absolute;
                    inset:0;
                    object-fit:cover;
                    width:100%;
                    height:100%;
                }
                .card-content{
                    position:relative;
                    height:100%;
                    background-color:rgba(0,0,0,0.2);
                    z-index:3;
                    padding: 16px 8px;
                    display:flex;
                    flex-direction:column;
                    justify-content:flex-end;
                }
                .card-content .heading{
                    font-size:24px;
                    font-weight:700;
                }
                .card-content .rating{
                    position:absolute;
                    top:8px;
                    right:16px;
                    display:flex;
                    align-items:center;
                    justify-content:center;                        
                    height:40px;
                    width:40px;
                    font-weight:700;
                    background-color: rgb(24 24 27);
                    border-radius:999px;
                }
                
            </style>
            """,
    unsafe_allow_html=True,
)


def card(imdb_id, name, image, rating):
    """
    The `card` function takes in a name, image URL, and rating, and returns an HTML card element with
    the provided information.

    :param imdb_id: The Imdb id of the movie
    :param name: The name of the card, which will be displayed as the heading
    :param image: The `image` parameter is the URL or file path of the image associated with the card.
    It is used to display the image in the card
    :param rating: The rating parameter is a numerical value representing the rating of the card
    :return: The code is returning an HTML card element with the provided name, image, and rating. The
    rating is displayed with a color that corresponds to its value.
    """
    color = "rgb(220, 38, 38)"
    if rating > 5.5:
        color = "rgb(251, 146, 60)"
    if rating > 7.5:
        color = "rgb(34, 197, 94)"
    url = (
        f"https://www.imdb.com/title/{imdb_id}"
        if imdb_id is not None
        else "https://www.imdb.com/"
    )
    return f"""
           <a href="{url}" target="_blank" class="card">
            <img class="card-image" src="{image}" alt="{name}"/>
            <div class="card-content">
                <span class="rating" style="color:{color};">{rating}</span>
                <span class="heading">{name}</span>
            </div>
           </a>
           """


def handle_card_data(data):
    """
    The function `handle_card_data` takes in a dictionary `data` and returns a `card` object with the
    name, image, and rating extracted from the dictionary, or an empty string if the dictionary is None.

    :param data: The `data` parameter is a dictionary that contains information about a movie. It is
    expected to have the following keys:
    :return: an instance of the `card` class with the `name`, `image`, and `rating` attributes set based
    on the data provided. If the `data` parameter is `None`, an empty string is returned.
    """
    empty_values = ["N/A", None]
    if data is not None:
        title = data.get("Title")
        image = (
            "https://images.unsplash.com/photo-1702651250304-2d1d94d1f847?q=80&w=1887&auto=format"
            if data.get("Poster") in empty_values
            else data.get("Poster")
        )
        rating = 0 if data.get("imdbRating") in empty_values else data.get("imdbRating")
        imdb_id = None if data.get("imdbID") in empty_values else data.get("imdbID")
        return card(
            imdb_id=imdb_id,
            name=title,
            image=image,
            rating=float(rating),
        )
    return ""


async def main():
    """
    The `main` function is an asynchronous function that creates a movie recommendation app using the
    Streamlit library in Python.
    """
    st.title("Ignite Movie Recommender 🔥")
    st.write("Get Movie recommendations in a snap of a finger.")
    st.header("Recommendations ✨")
    st.write("Select your favourite movies and awesome recommendations")
    with st.form("movie-recommendation"):
        movie = st.selectbox(
            "Choose your movie",
            new_movies_df["title"].unique(),
        )
        no_of_recommendations = st.slider("How many recommendations", 1, 10)
        st.form_submit_button("Submit")
    recommendations = recommend(movie, no_of_recommendations)
    result = await getAllMovies(recommendations)

    cards = "".join(map(handle_card_data, result))

    st.markdown(
        f"""
        <div class="card-container">
        {cards}
        </div>
        """,
        unsafe_allow_html=True,
    )


asyncio.run(main())
