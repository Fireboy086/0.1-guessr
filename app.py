from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
# Import scope and admin ID from config
from config import SCOPE, ADMIN_USER_ID
# Import credential loading function
from spotify_guessr import load_spotify_credentials
# Import SpotifyManager
from spotify_manager import SpotifyManager
# Import GameLogic (needed later)
from game_logic import GameLogic

# Load environment variables from .env file (primarily for FLASK_SECRET_KEY)
load_dotenv()

app = Flask(__name__)
# Make sure FLASK_SECRET_KEY is set in your .env file for session security
app.secret_key = os.getenv("FLASK_SECRET_KEY")
if not app.secret_key:
    raise ValueError("FLASK_SECRET_KEY not found in environment variables. Please set it in a .env file.")

# Store token info in session
app.config['SESSION_COOKIE_NAME'] = 'spotify-login-session'

# Spotify Credentials - Loaded from credentials.ini
CLIENT_ID, CLIENT_SECRET, REDIRECT_URI = load_spotify_credentials()

# Ensure credentials are loaded
if not CLIENT_ID or not CLIENT_SECRET or not REDIRECT_URI:
    # Adjust error message to reflect loading from .ini
    raise ValueError("Spotify API credentials (CLIENT_ID, CLIENT_SECRET, REDIRECT_URI) could not be loaded from credentials.ini. Please ensure the file exists and is correctly formatted.")

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

@app.route('/callback/')
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
        
        # --- Check for Admin --- 
        session['is_admin'] = False # Default to False
        try:
            sp = spotipy.Spotify(auth=token_info['access_token'])
            current_user = sp.current_user()
            user_id = current_user['id']
            session['user_id'] = user_id # Store user ID regardless
            # Check against configured Admin ID
            if user_id == ADMIN_USER_ID:
                session['is_admin'] = True
                print(f"Admin user {user_id} logged in.") # Log admin login
            else:
                 print(f"Regular user {user_id} logged in.")
        except Exception as e:
            print(f"Error fetching user ID for admin check: {e}")
            session['user_id'] = None
        # --- End Admin Check ---

        # Redirect to index
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

# --- Game Setup Routes ---

@app.route('/select-device', methods=['GET', 'POST'])
def select_device():
    token_info = get_token_info()
    if not token_info:
        return redirect(url_for('index'))

    try:
        sp = spotipy.Spotify(auth=token_info['access_token'])
        spotify_manager = SpotifyManager(sp)

        if request.method == 'POST':
            device_id = request.form.get('device_id')
            if device_id:
                # Verify the selected device_id is valid (optional but good practice)
                available_devices = spotify_manager.get_available_devices()
                if any(d['id'] == device_id for d in available_devices):
                    session['device_id'] = device_id
                    # Redirect to the next step (playlist selection)
                    return redirect(url_for('select_playlist')) # Adjust if route name is different
                else:
                    flash("Invalid device selected. Please try again.")
                    # Fall through to GET to re-render the device list
            else:
                flash("Please select a device.")
                # Fall through to GET to re-render the device list

        # GET request: Fetch and display devices
        devices = spotify_manager.get_available_devices()
        # Note: get_available_devices already returns a list of dicts with 'id', 'name', 'type'
        return render_template('select_device.html', devices=devices)

    except spotipy.exceptions.SpotifyException as e:
        # Handle potential API errors (e.g., token expired, network issue)
        print(f"Spotify API error in select_device: {e}")
        flash(f"Error communicating with Spotify: {e}. Please try logging out and back in.")
        return redirect(url_for('logout')) # Redirect to logout might be safest
    except Exception as e:
        print(f"Unexpected error in select_device: {e}")
        flash("An unexpected error occurred. Please try again.")
        return redirect(url_for('index'))

@app.route('/select-playlist', methods=['GET', 'POST'])
def select_playlist():
    token_info = get_token_info()
    if not token_info:
        return redirect(url_for('index'))
    if 'device_id' not in session:
        flash("Please select a device first.", "error")
        return redirect(url_for('select_device'))

    try:
        sp = spotipy.Spotify(auth=token_info['access_token'])
        # Use the base GameLogic for web, CLIGameLogic might have CLI specifics
        # If CLIGameLogic becomes necessary, instantiate it instead.
        game_logic = GameLogic(sp) 

        if request.method == 'POST':
            custom_url = request.form.get('custom_url', '').strip()
            playlist_id = request.form.get('playlist_id')
            source_name = "Custom URL/ID" # Default if using URL
            
            if custom_url:
                playlist_id_or_url = custom_url
            elif playlist_id:
                playlist_id_or_url = playlist_id
                if playlist_id == 'liked':
                    source_name = "Liked Songs"
                else:
                    # Get playlist name for feedback/session info (optional)
                    try:
                       playlist_details = sp.playlist(playlist_id, fields='name')
                       source_name = playlist_details.get('name', playlist_id) 
                    except Exception:
                       source_name = playlist_id # Fallback to ID if name fetch fails
            else:
                flash("Please select a playlist or enter a custom URL.", "error")
                # Fall through to GET to show form again
                # Need to fetch playlists again for the template
                playlists = game_logic.get_user_playlists() # Fetch playlists for re-render
                return render_template('select_playlist.html', playlists=playlists)

            # Fetch tracks using the selected source
            track_uris, track_names, track_artists = game_logic.get_playlist_tracks(source_name, playlist_id_or_url)

            if not track_uris:
                flash(f"Could not load tracks from '{source_name}'. It might be empty, private, or invalid.", "error")
                # Fetch playlists again for the template
                playlists = game_logic.get_user_playlists() 
                return render_template('select_playlist.html', playlists=playlists)
            
            # Store track info in session
            session['track_uris'] = track_uris
            session['track_names'] = track_names
            session['track_artists'] = track_artists
            session['playlist_name'] = source_name # Store for reference

            # --- Prepare debug info if enabled ---
            debug_track_list = []
            if session.get('debug_enabled'):
                # Combine names and artists for display
                debug_track_list = list(zip(track_names, track_artists))
            # --- End debug info ---

            # Clear potential old game state
            session.pop('game_state', None) 

            # Redirect to the next step (mode selection)
            # Pass debug info along ONLY if needed on the next page (likely not for mode select)
            return redirect(url_for('select_mode')) # Adjust if route name is different

        # GET request: Fetch user playlists and display form
        playlists = game_logic.get_user_playlists()
        # Pass empty debug list for GET request
        return render_template('select_playlist.html', playlists=playlists, debug_track_list=[]) 

    except spotipy.exceptions.SpotifyException as e:
        print(f"Spotify API error in select_playlist: {e}")
        flash(f"Error communicating with Spotify: {e}. Please try logging out and back in.", "error")
        return redirect(url_for('logout'))
    except Exception as e:
        print(f"Unexpected error in select_playlist: {e}")
        flash("An unexpected error occurred. Please try again.", "error")
        # Pass empty debug list on error redirect as well
        return render_template('select_playlist.html', playlists=game_logic.get_user_playlists() if 'game_logic' in locals() else [], debug_track_list=[])
        # Or maybe redirect to index: return redirect(url_for('index'))

# --- Admin Routes ---

@app.route('/toggle-debug', methods=['POST'])
def toggle_debug():
    if not session.get('is_admin', False):
        flash("Unauthorized access.", "error")
        return redirect(url_for('index'))

    session['debug_enabled'] = not session.get('debug_enabled', False)
    # Redirect back to the page the user was on
    # request.referrer gives the URL of the previous page
    return redirect(request.referrer or url_for('index'))

# --- Main Execution --- 

if __name__ == '__main__':
    # Ensure port matches SPOTIPY_REDIRECT_URI in .env and Spotify Dashboard
    port = int(os.environ.get("PORT", 8888)) 
    app.run(debug=True, port=port) 