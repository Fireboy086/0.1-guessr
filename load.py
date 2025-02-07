# load.py

import spotipy
from spotipy.oauth2 import SpotifyOAuth
from config import *
import Setupify
import sys

# Load Spotify credentials
client_id, client_secret, redirect_uri = Setupify.load_spotify_credentials()

if not client_id or not client_secret:
    # Credentials are missing; initiate setup
    Setupify.setup_spotify_credentials()
    # Reload credentials after setup
    client_id, client_secret, redirect_uri = Setupify.load_spotify_credentials()
    if not client_id or not client_secret:
        print("Spotify credentials are required to run the application.")
        sys.exit(1)

# Initialize Spotify API client
sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
    client_id=client_id,
    client_secret=client_secret,
    redirect_uri=redirect_uri,
    scope=SCOPE
))

def get_all_playlist_tracks(playlist_id):
    """Fetch all tracks from the given playlist."""
    tracks = []
    limit = 100
    offset = 0

    while True:
        response = sp.playlist_items(playlist_id, limit=limit, offset=offset)
        tracks.extend(response['items'])
        if len(response['items']) < limit:
            break
        offset += limit

    # Extract track URIs, names, and artists
    track_uris = [item['track']['uri'] for item in tracks if item['track'] is not None]
    track_names = [item['track']['name'] for item in tracks if item['track'] is not None]
    track_artists = [item['track']['artists'][0]['name'] for item in tracks if item['track'] is not None]
    return track_uris, track_names, track_artists

def get_all_saved_tracks():
    """Fetch all tracks from the user's Liked Songs."""
    tracks = []
    limit = 50
    offset = 0

    while True:
        response = sp.current_user_saved_tracks(limit=limit, offset=offset)
        tracks.extend(response['items'])
        if len(response['items']) < limit:
            break
        offset += limit

    # Extract track URIs, names, and artists
    track_uris = [item['track']['uri'] for item in tracks if item['track'] is not None]
    track_names = [item['track']['name'] for item in tracks if item['track'] is not None]
    track_artists = [item['track']['artists'][0]['name'] for item in tracks if item['track'] is not None]
    return track_uris, track_names, track_artists

def get_user_playlists():
    """Fetch user's playlists."""
    playlists = []
    limit = 50
    offset = 0
    while True:
        response = sp.current_user_playlists(limit=limit, offset=offset)
        playlists.extend(response['items'])
        if len(response['items']) < limit:
            break
        offset += limit
    return playlists
