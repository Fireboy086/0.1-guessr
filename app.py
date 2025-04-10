from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import os
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import time
import random # Import random
# Import scope, admin ID, constants from config
from config import SCOPE, ADMIN_USER_ID, MAX_LIVES, MAX_GUESS_COUNT 
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

# --- !! ADDED SCOPE DEBUG PRINT !! ---
print(f"DEBUG: Imported SCOPE = \"{SCOPE}\"")
# --- !! END ADDED SCOPE DEBUG PRINT !! ---

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
        # --- !! ADDED SCOPE DEBUG PRINT !! ---
        print(f"DEBUG: /callback - Token Info Scopes: {token_info.get('scope')}")
        # --- !! END ADDED SCOPE DEBUG PRINT !! ---
        session[TOKEN_INFO_KEY] = token_info
        
        # --- Check for Admin --- 
        session['is_admin'] = False # Default to False
        try:
            sp = spotipy.Spotify(auth=token_info['access_token'])
            current_user_profile = sp.me() 
            # --- !! REMOVING FULL DEBUG PRINT !! ---
            # print(f"DEBUG: Full sp.me() response:\n{current_user_profile}") 
            # --- !! END REMOVED DEBUG PRINT !! ---
            
            user_id = None
            user_product = 'unknown'
            
            # Safely try to access fields
            if current_user_profile and isinstance(current_user_profile, dict):
                user_id = current_user_profile.get('id')
                user_product = current_user_profile.get('product', 'unknown') # Now this should work
            else:
                 print("ERROR: sp.me() did not return a valid dictionary.")

            session['user_id'] = user_id # Store user ID (or None)
            
            # Debug: Print values for admin check
            # print(f"DEBUG: Checking Admin - Fetched User ID: {user_id}, Config Admin ID: {ADMIN_USER_ID}") # Removing extra admin debug
            
            # Store premium status
            session['is_premium'] = user_product == 'premium'
            print(f"DEBUG: Callback check - User product: {user_product}, is_premium session value: {session['is_premium']}") # Keep this one for now
            
            # Check against configured Admin ID (only if user_id was found)
            if user_id and user_id == ADMIN_USER_ID:
                session['is_admin'] = True
                print(f"Admin user {user_id} logged in.") 
            elif user_id:
                 print(f"Regular user {user_id} logged in.")
            else:
                 print("Could not determine user ID for admin check.")
                 
        except Exception as e:
            print(f"CRITICAL Error fetching user profile details: {e}")
            import traceback
            traceback.print_exc() 
            session['user_id'] = None
            session['is_premium'] = False
            session['is_admin'] = False
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
                # Handle SDK selection
                if device_id == "web_playback_sdk":
                    if session.get('is_premium', False):
                        session['device_id'] = device_id
                        print("Web Playback SDK selected as device.")
                        return redirect(url_for('select_playlist'))
                    else:
                        flash("Web playback requires a Spotify Premium account.", "error")
                        # Fall through to GET
                else:
                    # Verify the selected physical device_id (as before)
                    available_devices = spotify_manager.get_available_devices()
                    if any(d['id'] == device_id for d in available_devices):
                        session['device_id'] = device_id
                        return redirect(url_for('select_playlist')) 
                    else:
                        flash("Invalid device selected. Please try again.", "error")
                        # Fall through to GET
            else:
                flash("Please select a device.", "error")
                # Fall through to GET

        # GET request: Fetch and display devices (fetch is done below now)
        devices = spotify_manager.get_available_devices()
        is_premium = session.get('is_premium', False) 
        # print(f"DEBUG: /select-device route - is_premium value read from session: {is_premium}") # Removing this debug
        return render_template('select_device.html', devices=devices, is_premium=is_premium)

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

@app.route('/select-mode', methods=['GET', 'POST'])
def select_mode():
    token_info = get_token_info()
    if not token_info:
        return redirect(url_for('index'))
    # Ensure previous steps are done
    if 'device_id' not in session:
        flash("Please select a device first.", "error")
        return redirect(url_for('select_device'))
    if 'track_uris' not in session:
        flash("Please select a playlist first.", "error")
        return redirect(url_for('select_playlist'))

    if request.method == 'POST':
        # Get selections from form
        game_mode = request.form.get('guessing_difficulty')
        playback_duration_str = request.form.get('playback_duration')
        playback_start = request.form.get('playback_start')

        # Validate selections
        valid_modes = ["Normal", "Hard", "Harder", "Expert"]
        valid_durations = ["3.0", "2.0", "1.0", "0.5"]
        valid_starts = ["start", "random"]

        if not game_mode or game_mode not in valid_modes:
            flash("Invalid guessing difficulty selected.", "error")
            return render_template('select_mode.html')
        if not playback_duration_str or playback_duration_str not in valid_durations:
            flash("Invalid playback duration selected.", "error")
            return render_template('select_mode.html')
        if not playback_start or playback_start not in valid_starts:
            flash("Invalid playback start position selected.", "error")
            return render_template('select_mode.html')

        # Store valid selections in session
        session['game_mode'] = game_mode
        session['playback_duration'] = float(playback_duration_str) # Store as float
        session['playback_start'] = playback_start

        # Clear any old game state before starting a new game
        session.pop('game_state', None)

        # Redirect to the main game play route
        return redirect(url_for('play_game'))

    # GET request: show the form
    return render_template('select_mode.html')

# --- Game Play Route ---

@app.route('/play_game', methods=['GET', 'POST'])
def play_game():
    token_info = get_token_info()
    if not token_info:
        # For AJAX requests, return error status
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify(error="Not authenticated"), 401
        return redirect(url_for('index'))

    # --- !! ADDED SCOPE DEBUG PRINT !! ---
    print(f"DEBUG: /play_game - Token Info Scopes (before passing to template): {token_info.get('scope')}")
    # --- !! END ADDED SCOPE DEBUG PRINT !! ---

    # Check if all necessary setup info is in session
    required_setup = ['device_id', 'track_uris', 'track_names', 'track_artists', 
                        'game_mode', 'playback_duration', 'playback_start']
    if not all(key in session for key in required_setup):
        flash("Game setup incomplete. Please start from the beginning.", "error")
        # Redirect to the first step of setup
        return redirect(url_for('select_device')) 

    # Initialize managers
    try:
        sp = spotipy.Spotify(auth=token_info['access_token'])
        spotify_manager = SpotifyManager(sp)
        # Use base GameLogic, set mode from session later if needed for check_guess
        game_logic = GameLogic(sp) 
    except Exception as e:
        print(f"Error initializing Spotify objects in play_game: {e}")
        flash("Error connecting to Spotify. Please log out and back in.", "error")
        return redirect(url_for('logout'))

    # Retrieve game settings from session
    track_uris = session['track_uris']
    track_names = session['track_names']
    track_artists = session['track_artists']
    device_id = session['device_id']
    playback_duration = session['playback_duration'] # Already float
    playback_start_mode = session['playback_start'] # 'start' or 'random'
    game_mode = session['game_mode'] # Guessing difficulty

    # Load or initialize game state from session
    game_state = session.get('game_state', None)
    is_new_game_or_round = False
    if game_state is None:
        # Start a new game
        game_state = {
            'score': 0,
            'lives': MAX_LIVES,
            'round': 1,
            'played_indices': [], # Keep track of indices played
            'current_song_index': -1, # Index of the current song in the main lists
            'current_song_details': None, # Dict with {uri, name, artist}
            'guesses_left': MAX_GUESS_COUNT,
            'replays_left': 5, # Fixed replay limit
            'correctly_guessed': False
        }
        is_new_game_or_round = True # Mark to play song later in GET
        session['game_state'] = game_state
        print("--- New Game Started ---")
    
    # --- Handle POST requests (Guessing, Replaying) --- 
    if request.method == 'POST':
        action = request.form.get('action')
        # Make sure we have a game state
        if not game_state:
             return jsonify(error="Game state not found"), 400

        if action == 'guess':
            guess = request.form.get('guess', '').strip()
            if not guess:
                return jsonify(error="Please enter a guess.", status='warning'), 400
            if not game_state['current_song_details']:
                 return jsonify(error="No song playing.", status='error'), 400
            if game_state['guesses_left'] <= 0:
                return jsonify(error="No guesses left for this round.", status='error'), 400

            # Prepare GameLogic instance for checking the guess
            # We need to set the current track details and game mode
            game_logic.current_track_name = game_state['current_song_details']['name']
            game_logic.current_track_artist = game_state['current_song_details']['artist']
            game_logic.game_mode = game_mode # Set the guessing difficulty
            
            print(f"Checking guess: '{guess}' for song: '{game_logic.current_track_name}' by '{game_logic.current_track_artist}' in mode '{game_mode}'")

            is_correct = game_logic.check_guess(guess)

            response_data = {}
            status_code = 200

            if is_correct:
                points_earned = game_state['guesses_left'] # Or some other scoring logic
                game_state['score'] += points_earned
                game_state['correctly_guessed'] = True
                response_data = {
                    'result': 'correct',
                    'message': f"✅ Correct! The song was: {game_logic.current_track_name} by {game_logic.current_track_artist}. +{points_earned} points!",
                    'score': game_state['score'],
                    'lives': game_state['lives'] # Include current lives
                }
                # DO NOT save game_state here yet, next round needs to start
            else:
                game_state['guesses_left'] -= 1
                if game_state['guesses_left'] <= 0:
                    # Out of guesses for this song
                    game_state['lives'] -= 1
                    game_state['correctly_guessed'] = True # Mark to move to next round
                    response_data = {
                        'result': 'incorrect_final',
                        'message': f"❌ Out of guesses! The song was: {game_logic.current_track_name} by {game_logic.current_track_artist}. Lives left: {game_state['lives']}",
                        'score': game_state['score'],
                        'lives': game_state['lives']
                    }
                    if game_state['lives'] <= 0:
                         response_data['game_over'] = True
                         response_data['message'] += " Game Over!"
                else:
                    # Incorrect, but guesses remain
                    response_data = {
                        'result': 'incorrect',
                        'message': f"❌ Incorrect, try again!",
                        'guesses_left': game_state['guesses_left']
                    }
            
            # Save updated state *after* determining response
            session['game_state'] = game_state
            return jsonify(response_data), status_code

        elif action == 'replay':
            # Handle replay logic
            if game_state['replays_left'] > 0 and game_state['current_song_details']:
                game_state['replays_left'] -= 1
                session['game_state'] = game_state # Save state change
                
                # Replay the current song
                current_track_uri = game_state['current_song_details']['uri']
                start_position_ms = 0 # Default to start for replay
                # If random mode was chosen, maybe replay from a *different* random spot?
                # For simplicity now, replay always starts from 0 or the original random spot?
                # Let's just replay the exact snippet for now.
                
                # Need to get the original start position if it was random
                original_start_ms = game_state.get('current_song_start_ms', 0)
                
                try:
                    print(f"Replaying track: {current_track_uri} on device: {device_id} from {original_start_ms}ms")
                    spotify_manager.play_track_snippet(current_track_uri, device_id, playback_duration, original_start_ms)
                    return jsonify(result='replayed', replays_left=game_state['replays_left'], message='Song replayed!'), 200
                except Exception as e:
                    return jsonify(error=f"Error replaying song: {e}", status='error'), 500
            else:
                return jsonify(error="No more replays left or no song playing.", status='warning'), 400
        
        # Fallback for unknown POST action
        return jsonify(error="Unknown action"), 400

    # --- Handle GET request --- 
    # (Or proceeding after a correct/final guess via JS trigger)

    # Check if game is over (before starting next round)
    if game_state and game_state['lives'] <= 0:
        # Handle game over - maybe clear state and redirect?
        # For AJAX: return jsonify({'game_over': True, 'score': game_state['score']})
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
             return jsonify(game_over=True, final_score=game_state.get('score', 0))
        else:
             flash(f"Game Over! Final Score: {game_state.get('score', 0)}", "info")
             session.pop('game_state', None) # Clear state on game over
             return redirect(url_for('index'))

    # Check if we need to start a new round (or first round)
    # 'correctly_guessed' is now set when round ends (correctly or out of guesses)
    if is_new_game_or_round or (game_state and game_state['correctly_guessed']): 
        print(f"--- Starting Round Logic (Round {game_state['round']}) ---")
        # Pick a new song that hasn't been played
        available_indices = [i for i in range(len(track_uris)) if i not in game_state['played_indices']]
        
        if not available_indices:
            # Handle game won/finished
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                 return jsonify(game_over=True, status='won', final_score=game_state.get('score', 0))
            else:
                 flash(f"Wow! You guessed all songs! Final Score: {game_state.get('score', 0)}", "success")
                 session.pop('game_state', None)
                 return redirect(url_for('index'))
        
        current_song_index = random.choice(available_indices)
        
        # Update game state for new round (as before)
        # Reset correctly_guessed flag *here*
        game_state['correctly_guessed'] = False 
        game_state['current_song_index'] = current_song_index
        game_state['played_indices'].append(current_song_index)
        game_state['current_song_details'] = {
            'uri': track_uris[current_song_index],
            'name': track_names[current_song_index],
            'artist': track_artists[current_song_index]
        }
        game_state['guesses_left'] = MAX_GUESS_COUNT
        game_state['replays_left'] = 5 # Reset replays for new song
        # Increment round *after* the first song is processed
        if not is_new_game_or_round:
             game_state['round'] += 1

        # Determine start position for playback
        start_position_ms = 0
        if playback_start_mode == 'random':
            try:
                # Get track duration to calculate a random start point
                # Make sure track_uri is valid
                track_info = sp.track(game_state['current_song_details']['uri'])
                duration_ms = track_info['duration_ms']
                # Play somewhere in the first 80%? Avoid starting too close to the end.
                # Ensure duration_ms is greater than playback_duration in ms
                playback_duration_ms = int(playback_duration * 1000)
                if duration_ms > playback_duration_ms + 1000: # Add buffer
                     max_start = int(duration_ms * 0.8) # Don't start too late
                     if max_start > playback_duration_ms:
                         start_position_ms = random.randint(0, max_start - playback_duration_ms)
                     else:
                         start_position_ms = 0 # Fallback if song is very short
                else:
                    start_position_ms = 0 # Fallback if song is too short
            except Exception as e:
                print(f"Error getting track duration for random start: {e}")
                start_position_ms = 0 # Default to start if error
        
        game_state['current_song_start_ms'] = start_position_ms # Store the start time for replays

        # Play the snippet *only if not using the SDK*
        if session.get('device_id') != 'web_playback_sdk':
            try:
                print(f"Playing track via Spotify Manager: {game_state['current_song_details']['uri']} on device: {device_id} from {start_position_ms}ms")
                spotify_manager.play_track_snippet(
                    game_state['current_song_details']['uri'], 
                    device_id, 
                    playback_duration, 
                    start_position_ms
                )
            except Exception as e:
                 print(f"Error playing track snippet via SpotifyManager: {e}")
                 # Handle error - maybe return JSON error for AJAX?
                 if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                     return jsonify(error=f"Error playing song: {e}"), 500
                 else:
                     flash(f"Error playing song: {e}. Please ensure the device is active.", "error")
                     # Maybe redirect? return redirect(url_for('select_device'))
        else:
            # If SDK is selected, JS will handle playback after getting the track info
            print("SDK playback selected. Skipping backend playback initiation.")
        
        session['game_state'] = game_state
        print(f"State after starting round: {game_state}") 

    # Determine if SDK player should be used
    use_sdk_player = session.get('device_id') == 'web_playback_sdk'

    # If AJAX request (likely for /next_round trigger), return game state
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        # Return necessary state for UI update + SDK playback trigger
        state_for_js = {
            'round': game_state['round'],
            'score': game_state['score'],
            'lives': game_state['lives'],
            'guesses_left': game_state['guesses_left'],
            'replays_left': game_state['replays_left'],
            'use_sdk_player': use_sdk_player # Flag for JS
        }
        # Include song details if SDK needs to play it
        if use_sdk_player and game_state.get('current_song_details'):
             state_for_js['current_song_uri'] = game_state['current_song_details'].get('uri')
             state_for_js['current_song_start_ms'] = game_state.get('current_song_start_ms')
             # Also send duration needed for JS pause timer
             state_for_js['playback_duration_s'] = session.get('playback_duration') 

        # Include details needed only for debug panel update (if enabled)
        if session.get('debug_enabled') and game_state.get('current_song_details'):
            state_for_js['current_song_name'] = game_state['current_song_details'].get('name', 'N/A')
            state_for_js['current_song_artist'] = game_state['current_song_details'].get('artist', 'N/A')
            if not use_sdk_player: # Add URI/start only if not already added for SDK
                state_for_js['current_song_uri'] = game_state['current_song_details'].get('uri', 'N/A')
                state_for_js['current_song_start_ms'] = game_state.get('current_song_start_ms', 'N/A')
        
        return jsonify(state_for_js)

    # If regular GET request, render the full page template
    # Pass access token needed for SDK initialization
    access_token = token_info['access_token'] if token_info else None
    return render_template('play_game.html', game_state=session.get('game_state'), access_token=access_token, use_sdk_player=use_sdk_player)

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
    # Listen on all interfaces to be accessible on the local network
    app.run(host='0.0.0.0', debug=True, port=port) 