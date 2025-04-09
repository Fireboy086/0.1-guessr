#!/usr/bin/env python3
"""
Spotify Guessing Game - CLI Version
"""
import os
import sys
import random
import time
import spotipy
from spotipy.oauth2 import SpotifyOAuth
import configparser

# Import core modules
from game_logic import GameLogic, levenshtein_distance 
from spotify_manager import SpotifyManager
from config import *

# Override GameLogic.check_guess method to remove debug prints
class CLIGameLogic(GameLogic):
    """Override GameLogic to remove debug printing"""
    
    def check_guess(self, guess):
        """Check if a guess is correct based on the game mode without debug prints"""
        if not self.current_track_name or not self.current_track_artist:
            print(f"Error: Missing track information in GameLogic.")
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
        else:  # Normal mode
            # Allow <= 2 errors in either "title" or "title by artist"
            dist_title = levenshtein_distance(guess_lower, correct_title)
            dist_full = levenshtein_distance(guess_lower, correct_full)
            return dist_title <= 2 or dist_full <= 2

def load_spotify_credentials():
    """Load Spotify API credentials from the configuration file."""
    if not os.path.exists('credentials.ini'):
        return None, None, 'http://localhost:8888/callback/'

    try:
        config = configparser.ConfigParser()
        config.read('credentials.ini')

        if 'SPOTIFY' in config:
            client_id = config['SPOTIFY'].get('CLIENT_ID')
            client_secret = config['SPOTIFY'].get('CLIENT_SECRET')
            redirect_uri = config['SPOTIFY'].get('REDIRECT_URI', 'http://localhost:8888/callback/')
            return client_id, client_secret, redirect_uri
        else:
            return None, None, 'http://localhost:8888/callback/'
    except Exception as e:
        print(f"Error loading credentials: {e}")
        return None, None, 'http://localhost:8888/callback/'

def setup_spotify_credentials():
    """Guide the user to create Spotify API credentials and collect them."""
    print("\n===== Spotify API Credentials Setup =====")
    print("\nPlease follow these steps to create your Spotify API credentials:")
    print("1. Go to https://developer.spotify.com/dashboard/")
    print("2. Log in with your Spotify account")
    print("3. Click on 'Create an App'")
    print("4. Give your app a name and description")
    print("5. Agree to the terms and click 'Create'")
    print("6. Once the app is created, click on 'Edit Settings'")
    print("7. Add 'http://localhost:8888/callback/' to the Redirect URIs")
    print("8. Click 'Save'")
    print("9. Copy the 'Client ID' and 'Client Secret' from the dashboard")
    
    client_id = input("\nEnter your Client ID: ").strip()
    client_secret = input("Enter your Client Secret: ").strip()
    
    if not client_id or not client_secret:
        print("Both Client ID and Client Secret are required.")
        return False
    
    return save_to_file(client_id, client_secret)

def save_to_file(client_id, client_secret):
    """Save credentials to a configuration file."""
    try:
        config = configparser.ConfigParser()
        config['SPOTIFY'] = {
            'CLIENT_ID': client_id,
            'CLIENT_SECRET': client_secret,
            'REDIRECT_URI': 'http://localhost:8888/callback/'
        }

        with open('credentials.ini', 'w') as configfile:
            config.write(configfile)
        print("Credentials saved successfully!")
        return True
    except Exception as e:
        print(f"Error saving credentials: {e}")
        return False

def select_device(spotify_manager):
    """Select a Spotify device for playback"""
    devices = spotify_manager.get_available_devices()
    
    if not devices:
        print("No active Spotify devices found. Please open Spotify on a device.")
        return False
    
    print("\n===== Select Spotify Device =====")
    for i, device in enumerate(devices):
        print(f"{i+1}. {device['name']} ({device['type']})")
    
    try:
        selection = int(input("\nSelect a device number: ")) - 1
        if 0 <= selection < len(devices):
            spotify_manager.set_device(devices[selection]['id'])
            print(f"Selected device: {devices[selection]['name']}")
            return True
        else:
            print("Invalid selection.")
            return False
    except ValueError:
        print("Please enter a valid number.")
        return False

def select_game_mode():
    """Select game difficulty mode"""
    modes = ["Normal", "Hard", "Harder", "Expert"]
    
    print("\n===== Select Game Mode =====")
    print("1. Normal - Partial matches allowed")
    print("2. Hard - Close matches allowed")
    print("3. Harder - Exact title matches only")
    print("4. Expert - Exact 'title by artist' matches only")
    
    try:
        selection = int(input("\nSelect mode (1-4): ")) - 1
        if 0 <= selection < len(modes):
            return modes[selection]
        else:
            print("Invalid selection, using Normal mode.")
            return "Normal"
    except ValueError:
        print("Invalid input, using Normal mode.")
        return "Normal"

def select_playlist(game_logic):
    """Select a playlist to play from"""
    print("\n===== Select Playlist =====")
    
    # Get user playlists
    playlists = game_logic.get_user_playlists()
    
    if not playlists:
        print("No playlists found. Make sure you have playlists in your Spotify account.")
        return None, None, None
    
    # Add Liked Songs and Custom URL options
    all_options = [{"name": "Liked Songs", "id": "liked"}] + playlists + [{"name": "Enter Custom Playlist URL", "id": "custom"}]
    
    # Display playlists
    for i, playlist in enumerate(all_options):
        print(f"{i+1}. {playlist['name']}")
    
    # Get selection
    try:
        selection = int(input("\nSelect a playlist (1-{}): ".format(len(all_options)))) - 1
        if 0 <= selection < len(all_options):
            selected = all_options[selection]
            
            if selected["id"] == "custom":
                # Handle custom URL
                url = input("Enter Spotify playlist URL or ID: ").strip()
                return game_logic.get_playlist_tracks("Enter Custom Playlist URL", url)
            else:
                # Handle regular playlist or Liked Songs
                return game_logic.get_playlist_tracks(selected["name"])
        else:
            print("Invalid selection.")
            return None, None, None
    except ValueError:
        print("Please enter a valid number.")
        return None, None, None

def play_game(spotify_manager, game_logic, track_uris, track_names, track_artists, game_mode):
    """Main game loop"""
    # Game variables
    lives = MAX_LIVES
    total_score = 0
    played_songs = []
    current_round = 0
    
    # Set game mode in the game logic
    game_logic.set_game_mode(game_mode)
    
    # Save tracks in game_logic
    game_logic.track_uris = track_uris
    game_logic.track_names = track_names
    game_logic.track_artists = track_artists
    
    # Instructions
    print("\n===== Game Instructions =====")
    print(f"1. Listen to the song clip")
    print(f"2. Guess the song title")
    print(f"3. You have {MAX_GUESS_COUNT} attempts per song and {lives} lives total")
    print(f"4. Game mode: {game_mode}")
    input("\nPress Enter to start the game...")
    
    while lives > 0 and len(played_songs) < 10:  # Play up to 10 songs or until game over
        current_round += 1
        print(f"\n===== Round {current_round} =====")
        print(f"Lives remaining: {lives}")
        
        # Play a random track
        track_uri, track_name, track_artist = spotify_manager.play_random_track(track_uris, track_names, track_artists)
        
        if not track_uri:
            print("Error playing track. Make sure Spotify is open and your device is active.")
            break
        
        # Make sure game_logic has the current track info
        game_logic.current_track = track_uri
        game_logic.current_track_name = track_name
        game_logic.current_track_artist = track_artist
        
        # Allow time for playback
        time.sleep(PLAYBACK_DURATION + 0.5)  # Add a small buffer
        
        # Initialize round data
        guesses_remaining = MAX_GUESS_COUNT
        correctly_guessed = False
        round_data = {
            "track_name": track_name,
            "track_artist": track_artist,
            "guesses": [],
            "correctly_guessed": False
        }
        
        # Guessing loop
        while guesses_remaining > 0 and not correctly_guessed:
            print(f"\nGuesses remaining: {guesses_remaining}")
            guess = input("Your guess: ").strip()
            
            # Skip if empty
            if not guess:
                print("Please enter a guess.")
                continue
                
            # Add to guesses
            round_data["guesses"].append(guess)
            
            # Check if correct
            if game_logic.check_guess(guess):
                correctly_guessed = True
                round_data["correctly_guessed"] = True
                total_score += guesses_remaining
                print(f"\n✅ Correct! The song is: {track_name} by {track_artist}")
                print(f"+{guesses_remaining} points")
            else:
                guesses_remaining -= 1
                if guesses_remaining > 0:
                    print("❌ Incorrect, try again!")
                    replay = input("Replay the track? (y/n): ").lower()
                    if replay == 'y':
                        spotify_manager.replay_song()
                        time.sleep(PLAYBACK_DURATION + 0.5)
        
        # If all guesses used and not correct
        if not correctly_guessed:
            lives -= 1
            print(f"\n❌ Out of guesses! The song was: {track_name} by {track_artist}")
            print(f"Lives remaining: {lives}")
        
        # Add round data to played songs
        played_songs.append(round_data)
        
        if lives > 0 and len(played_songs) < 10:
            continue_game = input("\nContinue to next song? (y/n): ").lower()
            if continue_game != 'y':
                break
    
    # Game summary
    print("\n===== Game Summary =====")
    print(f"Total score: {total_score}")
    print(f"Songs played: {len(played_songs)}")
    print(f"Correct guesses: {sum(1 for song in played_songs if song['correctly_guessed'])}")
    
    # Return to main menu
    print("\nGame over. Thanks for playing!")
    return total_score, played_songs

def main():
    """Main entry point for the CLI version of Spotify Guessing Game"""
    print("===== Spotify Guessing Game - CLI Version =====")
    
    # Load Spotify credentials
    client_id, client_secret, redirect_uri = load_spotify_credentials()
    
    if not client_id or not client_secret:
        # Credentials are missing; initiate setup
        if not setup_spotify_credentials():
            print("Spotify credentials are required to run the application.")
            sys.exit(1)
        # Reload credentials after setup
        client_id, client_secret, redirect_uri = load_spotify_credentials()
        if not client_id or not client_secret:
            print("Spotify credentials are required to run the application.")
            sys.exit(1)
    
    # Initialize Spotify client
    try:
        sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=SCOPE
        ))
        # Test API connection
        sp.current_user()
    except Exception as e:
        print(f"Error connecting to Spotify: {e}")
        print("Please check your credentials and internet connection.")
        sys.exit(1)
    
    # Initialize managers
    spotify_manager = SpotifyManager(sp)
    game_logic = CLIGameLogic(sp)  # Use our custom class
    
    # Main program loop
    while True:
        print("\n===== Main Menu =====")
        print("1. Start Game")
        print("2. Select Device")
        print("3. Exit")
        
        choice = input("\nSelect an option (1-3): ").strip()
        
        if choice == '1':
            # Select playlist
            track_uris, track_names, track_artists = select_playlist(game_logic)
            
            if not track_uris:
                print("Failed to load playlist or no tracks found.")
                continue
                
            # Select game mode
            game_mode = select_game_mode()
            
            # Start game
            play_game(spotify_manager, game_logic, track_uris, track_names, track_artists, game_mode)
            
        elif choice == '2':
            # Select device
            select_device(spotify_manager)
            
        elif choice == '3':
            print("Thanks for playing!")
            break
            
        else:
            print("Invalid choice, please try again.")

if __name__ == "__main__":
    main() 