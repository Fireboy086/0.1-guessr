from flask import Flask, render_template, request, redirect, url_for, session
import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
# Import scope from config
from config import SCOPE 

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
# Make sure FLASK_SECRET_KEY is set in your .env file for session security
app.secret_key = os.getenv("FLASK_SECRET_KEY", "fallback-secret-key-please-set") 
# Store token info in session
app.config['SESSION_COOKIE_NAME'] = 'spotify-login-session'

# Spotify Credentials - Loaded from environment variables
CLIENT_ID = os.getenv("SPOTIPY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIPY_CLIENT_SECRET")
REDIRECT_URI = os.getenv("SPOTIPY_REDIRECT_URI")

# Ensure credentials are loaded
if not CLIENT_ID or not CLIENT_SECRET or not REDIRECT_URI:
    raise ValueError("Spotify API credentials (CLIENT_ID, CLIENT_SECRET, REDIRECT_URI) not found in environment variables.")

# --- Spotify Auth Helper ---

TOKEN_INFO_KEY = 'spotify_token_info'

def create_spotify_oauth():
    return SpotifyOAuth(
        client_id=CLIENT_ID,
        client_secret=CLIENT_SECRET,
        redirect_uri=REDIRECT_URI,
        scope=SCOPE)

def get_token_info():
    token_info = session.get(TOKEN_INFO_KEY, None)
    if not token_info:
        return None

    # Check if token is expired
    now = int(time.time())
    is_expired = token_info['expires_at'] - now < 60  # Check 60 seconds buffer

    if is_expired:
        sp_oauth = create_spotify_oauth()
        token_info = sp_oauth.refresh_access_token(token_info['refresh_token'])
        session[TOKEN_INFO_KEY] = token_info
        print("Token was refreshed") # For debugging

    return token_info

# --- Routes --- 

@app.route('/')
def index():
    token_info = get_token_info()
    if not token_info:
        # If not logged in, show the login page
        return render_template('login.html')
    
    # If logged in, get user info and show the index page
    try:
        sp = spotipy.Spotify(auth=token_info['access_token'])
        current_user = sp.current_user()
    except Exception as e:
        # Handle potential errors fetching user info (e.g., token invalid despite check)
        print(f"Error fetching user info: {e}")
        # Clear session and force re-login
        session.pop(TOKEN_INFO_KEY, None)
        session.clear()
        return redirect(url_for('index')) # Redirect back to index, which will now show login

    return render_template('index.html', user=current_user)

@app.route('/login')
def login():
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/callback')
def callback():
    sp_oauth = create_spotify_oauth()
    session.clear() # Clear potential old session data
    code = request.args.get('code')
    
    if not code:
        # Handle error case where user denied access or something went wrong
        error = request.args.get('error', 'Unknown error')
        return f"Error during Spotify callback: {error}. Please try <a href='/login'>logging in</a> again."
        
    try:
        token_info = sp_oauth.get_access_token(code)
        session[TOKEN_INFO_KEY] = token_info
        # Redirect to a logged-in page, e.g., device selection or main game page
        # For now, redirect back to index which will show logged-in status
        return redirect(url_for('index')) 
    except Exception as e:
        # Handle exceptions during token fetching
        print(f"Error getting access token: {e}") # Log error
        return f"Error getting access token: {e}. Please try <a href='/login'>logging in</a> again."


@app.route('/logout')
def logout():
    session.pop(TOKEN_INFO_KEY, None) # Remove the token info
    session.clear() # Clear the entire session
    # Redirect to index, which will now show the login link
    return redirect(url_for('index'))

# --- Main Execution --- 

if __name__ == '__main__':
    # Ensure port matches SPOTIPY_REDIRECT_URI in .env and Spotify Dashboard
    port = int(os.environ.get("PORT", 8888)) 
    app.run(debug=True, port=port) 