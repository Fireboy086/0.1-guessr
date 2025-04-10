from flask import Flask, render_template, request, redirect, url_for, session
import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallback-secret-key") # Load secret key from .env or use a default

# --- Spotify Auth --- (Placeholder - will be expanded)

# Need to load client_id, client_secret, redirect_uri from somewhere
# Maybe load_spotify_credentials() from spotify_guessr.py or directly from .env?

# --- Routes --- 

@app.route('/')
def index():
    # Simple index page - later will redirect to login or game
    return "Hello, Spotify Guessr Web!"

# --- Main Execution --- 

if __name__ == '__main__':
    app.run(debug=True, port=8888) # Using port 8888 for consistency with redirect URI 