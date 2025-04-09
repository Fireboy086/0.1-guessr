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
from ui.screens.settings_screen import SettingsScreen, CheatSettingsScreen

class SpotifyGuessingGameApp(ctk.CTk):
    """Main application class for the Spotify Guessing Game"""
    
    def __init__(self, client_id=None, client_secret=None, redirect_uri=None):
        super().__init__()
        
        # Window setup
        self.title(WINDOW_TITLE)
        self.geometry("1000x700")
        self.minsize(800, 600)
        
        # Center the window
        self.center_window()
        
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
        self.game_settings = {}
        
        # Configure grid layout (4x4)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)
        
        # Konami code support
        self.konami_sequence = ['Up', 'Up', 'Down', 'Down', 'Left', 'Right', 'Left', 'Right', 'b', 'a']
        self.konami_index = 0
        self.bind('<KeyPress>', self.detect_konami_code)
        
        # Check for multiple devices
        self.check_spotify_devices()
        
        # Add settings dictionary to store all settings
        self.settings = {
            'volume': VOLUME_LEVEL,
            'playback_duration': PLAYBACK_DURATION,
            'max_guesses': MAX_GUESS_COUNT,
            'max_lives': MAX_LIVES,
            'cheats': {
                'infinite_lives': False,
                'show_answers': False,
                'skip_verification': False
            }
        }
    
    def check_spotify_devices(self):
        """Check for available Spotify devices and prompt if needed"""
        devices = self.spotify_manager.get_available_devices()
        
        if len(devices) > 1:
            # Multiple devices available, show device selection
            self.show_device_selection(devices)
        elif len(devices) == 1:
            # Just one device, select it automatically
            self.spotify_manager.set_device(devices[0]['id'])
            # Show start screen
            self.show_start_screen()
        else:
            # No devices found, just show start screen
            self.show_start_screen()
    
    def show_device_selection(self, devices):
        """Show a dialog to select the Spotify device"""
        device_window = ctk.CTkToplevel(self)
        device_window.title("Select Spotify Device")
        device_window.geometry("500x300")
        device_window.transient(self)
        device_window.grab_set()
        
        # Center the window
        self.center_toplevel(device_window, 500, 300)
        
        # Create a frame for the device options
        device_frame = ctk.CTkFrame(device_window)
        device_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Label
        label = ctk.CTkLabel(
            device_frame, 
            text="Select a Spotify Device for Playback",
            font=ctk.CTkFont(size=16, weight="bold")
        )
        label.pack(pady=(0, 20))
        
        # Radio buttons for device selection
        device_var = ctk.StringVar(value="")
        
        for i, device in enumerate(devices):
            device_button = ctk.CTkRadioButton(
                device_frame,
                text=f"{device['name']} ({device['type']})",
                variable=device_var,
                value=device['id'],
                font=ctk.CTkFont(size=14)
            )
            device_button.pack(anchor="w", padx=20, pady=5)
            
            # Auto-select first device
            if i == 0:
                device_var.set(device['id'])
        
        # Note about changing later
        note_label = ctk.CTkLabel(
            device_frame, 
            text="You can change this later in Settings",
            font=ctk.CTkFont(size=12),
            text_color="gray"
        )
        note_label.pack(pady=(10, 0))
        
        # Continue button
        continue_button = ctk.CTkButton(
            device_frame,
            text="Continue",
            command=lambda: self._on_device_selected(device_var.get(), device_window),
            height=40,
            fg_color=("#1DB954", "#1DB954")
        )
        continue_button.pack(pady=(20, 0))
    
    def _on_device_selected(self, device_id, window):
        """Handle device selection and close dialog"""
        if device_id:
            self.spotify_manager.set_device(device_id)
        
        # Close device selection window
        window.destroy()
        
        # Show the start screen
        self.show_start_screen()
    
    def show_start_screen(self):
        """Switch to the start screen"""
        if self.current_screen:
            self.current_screen.destroy()
        
        self.current_screen = StartScreen(self, self.game_logic)
        self.current_screen.grid(row=0, column=0, sticky="nsew")
    
    def show_settings_screen(self):
        """Switch to the settings screen"""
        if self.current_screen:
            self.current_screen.destroy()
        
        self.current_screen = SettingsScreen(self, self.spotify_manager, self.game_settings)
        self.current_screen.grid(row=0, column=0, sticky="nsew")
    
    def show_cheat_settings_screen(self):
        """Switch to the cheat settings screen"""
        if self.current_screen:
            self.current_screen.destroy()
        
        self.current_screen = CheatSettingsScreen(self, self.game_settings)
        self.current_screen.grid(row=0, column=0, sticky="nsew")
    
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
            self.game_mode,
            self.game_settings
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
                self.show_cheat_settings_screen()
        else:
            self.konami_index = 0
    
    def center_window(self):
        """Center the window on the screen"""
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = 1000
        window_height = 700
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Make window appear on top and lift it
        self.lift()
        self.focus_force()
    
    def open_configuration_window(self):
        """Open a modal window for game configuration"""
        config_window = ctk.CTkToplevel(self)
        config_window.title("Configuration")
        config_window.geometry("500x300")
        config_window.transient(self)
        config_window.grab_set()
        
        # Center the configuration window
        self.center_toplevel(config_window, 500, 300)
        
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
            command=lambda: self.save_configuration(config_window),
            fg_color=("#1DB954", "#1DB954")
        )
        save_button.grid(row=row, column=0, columnspan=2, pady=20)
    
    def save_configuration(self, window=None):
        """Save configuration values"""
        try:
            # Update global variables
            global PLAYBACK_DURATION, MAX_GUESS_COUNT, MAX_LIVES, VOLUME_LEVEL
            
            PLAYBACK_DURATION = float(self.config_entries['PLAYBACK_DURATION'].get())
            MAX_GUESS_COUNT = int(self.config_entries['MAX_GUESS_COUNT'].get())
            MAX_LIVES = int(self.config_entries['MAX_LIVES'].get())
            VOLUME_LEVEL = int(self.config_entries['VOLUME_LEVEL'].get())
            
            # Set Spotify volume
            self.spotify_manager.set_volume(VOLUME_LEVEL)
            
            # Close window if provided
            if window:
                window.destroy()
                
            # Show confirmation
            print("Configuration saved successfully!")
        
        except ValueError as e:
            # Show error
            error_label = ctk.CTkLabel(
                self.config_entries['PLAYBACK_DURATION'].master,
                text=f"Error: {str(e)}. Please use valid numbers.",
                text_color="red"
            )
            error_label.grid(row=len(self.config_entries) + 1, column=0, columnspan=2, pady=10)
            
            # Remove error after 3 seconds
            self.after(3000, error_label.destroy)
    
    def center_toplevel(self, window, width, height):
        """Center a toplevel window relative to the main window"""
        x = self.winfo_x() + (self.winfo_width() - width) // 2
        y = self.winfo_y() + (self.winfo_height() - height) // 2
        window.geometry(f"{width}x{height}+{x}+{y}")
        
        # Make window appear on top
        window.lift()
        window.focus_force()

    def update_settings(self, new_settings, is_cheat=False):
        """Update app settings when they change"""
        if is_cheat:
            self.settings['cheats'].update(new_settings)
        else:
            # Update normal settings
            self.settings.update(new_settings)
            
            # Update global config values
            global VOLUME_LEVEL, PLAYBACK_DURATION, MAX_GUESS_COUNT, MAX_LIVES
            VOLUME_LEVEL = new_settings.get('volume', VOLUME_LEVEL)
            PLAYBACK_DURATION = new_settings.get('playback_duration', PLAYBACK_DURATION)
            MAX_GUESS_COUNT = new_settings.get('max_guesses', MAX_GUESS_COUNT)
            MAX_LIVES = new_settings.get('max_lives', MAX_LIVES)