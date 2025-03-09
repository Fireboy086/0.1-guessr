"""
Main app class for Spotify Guessing Game using customtkinter
"""
import os
import random
import customtkinter as ctk
from PIL import Image, ImageTk
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from config import *

# Import our modules
from spotify_manager import SpotifyManager
from game_logic import GameLogic, levenshtein_distance
from ui.screens.start_screen import StartScreen
from ui.screens.game_screen import GameScreen
from ui.screens.summary_screen import SummaryScreen

class SpotifyGuessingGameApp(ctk.CTk):
    """Main application class for the Spotify Guessing Game"""
    
    def __init__(self, client_id=None, client_secret=None, redirect_uri=None):
        super().__init__()
        
        # Window setup
        self.title(WINDOW_TITLE)
        self.geometry("1000x700")
        self.minsize(800, 600)
        
        # Use provided credentials or fall back to config values
        self.client_id = client_id or CLIENT_ID
        self.client_secret = client_secret or CLIENT_SECRET
        self.redirect_uri = redirect_uri or REDIRECT_URI
        
        # Initialize Spotify client
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=self.client_id,
            client_secret=self.client_secret,
            redirect_uri=self.redirect_uri,
            scope=SCOPE
        ))
        
        # Initialize managers
        self.spotify_manager = SpotifyManager(self.sp)
        self.game_logic = GameLogic(self.sp)
        
        # Set up UI variables
        self.current_screen = None
        self.track_uris = []
        self.track_names = []
        self.track_artists = []
        self.game_mode = "Normal"
        self.played_songs = []
        
        # Configure grid layout (4x4)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Start with the start screen
        self.show_start_screen()
        
        # Konami code support
        self.konami_sequence = ['Up', 'Up', 'Down', 'Down', 'Left', 'Right', 'Left', 'Right', 'b', 'a']
        self.konami_index = 0
        self.bind('<KeyPress>', self.detect_konami_code)
    
    def show_start_screen(self):
        """Switch to the start screen"""
        if self.current_screen:
            self.current_screen.destroy()
        
        self.current_screen = StartScreen(self, self.game_logic)
        self.current_screen.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
    
    def show_game_screen(self, track_uris, track_names, track_artists, game_mode):
        """Switch to the game screen with the selected playlist"""
        if self.current_screen:
            self.current_screen.destroy()
        
        self.track_uris = track_uris
        self.track_names = track_names
        self.track_artists = track_artists
        self.game_mode = game_mode
        self.played_songs = []
        
        self.current_screen = GameScreen(
            self, 
            self.game_logic,
            self.spotify_manager,
            self.track_uris,
            self.track_names,
            self.track_artists,
            self.game_mode
        )
        self.current_screen.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
        
        # Start the game
        self.current_screen.play_random_track()
    
    def show_summary_screen(self, played_songs):
        """Switch to the summary screen"""
        if self.current_screen:
            self.current_screen.destroy()
        
        self.current_screen = SummaryScreen(self, played_songs)
        self.current_screen.grid(row=0, column=0, sticky="nsew", padx=20, pady=20)
    
    def detect_konami_code(self, event):
        """Check for Konami code sequence to open configuration window"""
        key = event.keysym
        expected_key = self.konami_sequence[self.konami_index]
        if key.lower() == expected_key.lower():
            self.konami_index += 1
            if self.konami_index == len(self.konami_sequence):
                self.konami_index = 0
                self.open_configuration_window()
        else:
            self.konami_index = 0
    
    def open_configuration_window(self):
        """Open a modal window for game configuration"""
        config_window = ctk.CTkToplevel(self)
        config_window.title("Configuration")
        config_window.geometry("500x300")
        config_window.transient(self)
        config_window.grab_set()
        
        # Create a frame for the configuration options
        config_frame = ctk.CTkFrame(config_window)
        config_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Variables for our configuration
        variables = {
            'PLAYBACK_DURATION': ('Playback Duration (seconds)', PLAYBACK_DURATION),
            'MAX_GUESS_COUNT': ('Max Guesses per Song', MAX_GUESS_COUNT),
            'MAX_LIVES': ('Max Lives', MAX_LIVES),
            'VOLUME_LEVEL': ('Volume Level (0-100)', VOLUME_LEVEL),
        }
        
        # Create entries for each configuration option
        self.config_entries = {}
        row = 0
        for var_name, (label_text, default_value) in variables.items():
            label = ctk.CTkLabel(config_frame, text=label_text)
            label.grid(row=row, column=0, padx=10, pady=10, sticky="w")
            
            entry = ctk.CTkEntry(config_frame, width=100)
            entry.insert(0, str(default_value))
            entry.grid(row=row, column=1, padx=10, pady=10)
            
            self.config_entries[var_name] = entry
            row += 1
        
        # Save button
        save_button = ctk.CTkButton(
            config_frame, 
            text="Save", 
            command=self.save_configuration
        )
        save_button.grid(row=row, column=0, columnspan=2, pady=20)
    
    def save_configuration(self):
        """Save the configuration values"""
        global PLAYBACK_DURATION, MAX_GUESS_COUNT, MAX_LIVES, VOLUME_LEVEL
        
        try:
            PLAYBACK_DURATION = float(self.config_entries['PLAYBACK_DURATION'].get())
            MAX_GUESS_COUNT = int(self.config_entries['MAX_GUESS_COUNT'].get())
            MAX_LIVES = int(self.config_entries['MAX_LIVES'].get())
            VOLUME_LEVEL = int(self.config_entries['VOLUME_LEVEL'].get())
            
            # Update the current game screen if it exists
            if isinstance(self.current_screen, GameScreen):
                self.current_screen.current_play_time = PLAYBACK_DURATION
                self.current_screen.lives = MAX_LIVES
                self.current_screen.update_lives_label()
            
            # Show success message
            message = ctk.CTkToplevel(self)
            message.title("Success")
            message.geometry("300x100")
            message.transient(self)
            message.grab_set()
            
            ctk.CTkLabel(message, text="Configuration updated successfully.").pack(pady=20)
            ctk.CTkButton(message, text="OK", command=message.destroy).pack()
            
        except ValueError:
            # Show error message
            message = ctk.CTkToplevel(self)
            message.title("Error")
            message.geometry("300x100")
            message.transient(self)
            message.grab_set()
            
            ctk.CTkLabel(message, text="Please enter valid values.").pack(pady=20)
            ctk.CTkButton(message, text="OK", command=message.destroy).pack() 