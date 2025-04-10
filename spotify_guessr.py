#!/usr/bin/env python3
"""
Spotify Guessing Game - Core Logic & Setup
"""
import os
# import sys # No longer needed here
import random
# import time # No longer needed here
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import configparser

# Import core modules
from game_logic import GameLogic, levenshtein_distance 
from spotify_manager import SpotifyManager
# Keep config import for constants
from config import *

# Override GameLogic.check_guess method to remove debug prints (if any)
# Or keep it if it provides specific CLI behavior logic beyond just prints
class CLIGameLogic(GameLogic):
    """Override GameLogic for any specific CLI needs (currently none beyond base)"""
    
    # The check_guess method doesn't print, so the override isn't strictly
    # needed unless we add CLI-specific logic later. We keep it for now.
    def check_guess(self, guess):
        """Check if a guess is correct based on the game mode."""
        if not self.current_track_name or not self.current_track_artist:
            # Maybe raise an error instead of printing?
            # For now, returning False is okay as the interface handles user feedback
            # print(f"Error: Missing track information in GameLogic.") # Removed print
            return False
            
        correct_title = self.current_track_name.lower()
        correct_full = f"{self.current_track_name} by {self.current_track_artist}".lower()
        guess_lower = guess.lower()
        
        if self.game_mode == "Expert":
            # Exact match on "title by artist"
            return guess_lower == correct_full
        elif self.game_mode == "Harder":
            # Exact match on title only
            return guess_lower == correct_title
        elif self.game_mode == "Hard":
            # Close match with <= 1 error on title, or exact match on full
            title_dist = levenshtein_distance(guess_lower, correct_title)
            return title_dist <= 1 or guess_lower == correct_full
        else:  # Normal mode (Default)
            # Allow <= 2 errors in either "title" or "title by artist"
            dist_title = levenshtein_distance(guess_lower, correct_title)
            dist_full = levenshtein_distance(guess_lower, correct_full)
            return dist_title <= 2 or dist_full <= 2

    # Add a method to explicitly set the current track details needed for check_guess
    def set_current_track(self, uri, name, artist):
        self.current_track = uri # Keep track of URI too if needed later
        self.current_track_name = name
        self.current_track_artist = artist


def load_spotify_credentials():
    """Load Spotify API credentials from the configuration file.
    
    Returns:
        tuple: (client_id, client_secret, redirect_uri) or (None, None, default_uri) if error/not found.
    """
    default_uri = 'http://localhost:8888/callback/'
    if not os.path.exists('credentials.ini'):
        return None, None, default_uri

    try:
        config = configparser.ConfigParser()
        config.read('credentials.ini')

        if 'SPOTIFY' in config:
            client_id = config['SPOTIFY'].get('CLIENT_ID')
            client_secret = config['SPOTIFY'].get('CLIENT_SECRET')
            redirect_uri = config['SPOTIFY'].get('REDIRECT_URI', default_uri)
            # Basic check if values exist
            if client_id and client_secret:
                return client_id, client_secret, redirect_uri
            else:
                 return None, None, redirect_uri # Return None if keys exist but values are empty
        else:
            return None, None, default_uri
    except Exception as e:
        # Log error ideally, but for now return None
        # print(f"Error loading credentials: {e}") # Removed print
        return None, None, default_uri

# This function is now called by the CLI interface
def save_to_file(client_id, client_secret, redirect_uri='http://localhost:8888/callback/'):
    """Save credentials to a configuration file.
    
    Args:
        client_id (str): Spotify Client ID.
        client_secret (str): Spotify Client Secret.
        redirect_uri (str): Redirect URI (defaults to localhost).

    Returns:
        bool: True if saving was successful, False otherwise.
    """
    try:
        config = configparser.ConfigParser()
        config['SPOTIFY'] = {
            'CLIENT_ID': client_id,
            'CLIENT_SECRET': client_secret,
            'REDIRECT_URI': redirect_uri
        }

        with open('credentials.ini', 'w') as configfile:
            config.write(configfile)
        # print("Credentials saved successfully!") # Removed print
        return True
    except Exception as e:
        # print(f"Error saving credentials: {e}") # Removed print
        # Log error ideally
        return False
    
# Removed setup_spotify_credentials - Moved to cli_interface.py
# Removed select_device - Moved to cli_interface.py
# Removed select_game_mode - Moved to cli_interface.py
# Removed select_playlist - Moved to cli_interface.py
# Removed play_game - Logic moved to run_game_loop in cli_interface.py
# Removed main - Moved to cli_interface.py

# This file now primarily contains:
# - Core settings/constants (via config import)
# - Credential loading/saving logic (callable by the interface)
# - CLIGameLogic class (if needed)
# - It no longer runs directly using `if __name__ == "__main__":`

# Potential further refactoring:
# - Move CLIGameLogic fully into cli_interface.py if it's purely for CLI overrides?
# - Move load/save credentials into config.py or a dedicated credentials module? 