"""
Settings Screen for Spotify Guessing Game
"""
import customtkinter as ctk
from config import *

class SettingsScreen(ctk.CTkFrame):
    """Settings screen for the Spotify Guessing Game"""
    
    def __init__(self, parent, spotify_manager, game_settings=None):
        super().__init__(parent, fg_color=("#f0f0f0", "#1e1e1e"), corner_radius=0)
        self.parent = parent
        self.spotify_manager = spotify_manager
        self.game_settings = game_settings or {}
        
        # Create UI elements
        self._create_widgets()
        
        # Load devices
        self.after(100, self._load_devices)
    
    def _create_widgets(self):
        """Create all UI widgets for the settings screen"""
        # Master layout
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)  # Header
        self.rowconfigure(1, weight=1)  # Content
        self.rowconfigure(2, weight=0)  # Footer
        
        # ===== HEADER SECTION =====
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 0))
        
        # Title
        self.title_label = ctk.CTkLabel(
            self.header_frame, 
            text="Settings", 
            font=ctk.CTkFont(family="Helvetica", size=24, weight="bold"),
        )
        self.title_label.pack(pady=(10, 5))
        
        # ===== CONTENT SECTION =====
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.rowconfigure(0, weight=1)
        
        # Settings Frame
        self.settings_frame = ctk.CTkFrame(self.content_frame, corner_radius=15)
        self.settings_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Spotify Settings Section
        self.spotify_label = ctk.CTkLabel(
            self.settings_frame,
            text="Spotify Settings",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.spotify_label.pack(pady=(15, 5), padx=15, anchor="w")
        
        # Volume Control
        self.volume_frame = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        self.volume_frame.pack(fill="x", padx=15, pady=(10, 5))
        
        self.volume_label = ctk.CTkLabel(
            self.volume_frame,
            text="Volume:",
            font=ctk.CTkFont(size=14)
        )
        self.volume_label.pack(side="left", padx=(0, 10))
        
        self.volume_var = ctk.IntVar(value=VOLUME_LEVEL)
        self.volume_slider = ctk.CTkSlider(
            self.volume_frame,
            from_=0,
            to=100,
            number_of_steps=20,
            variable=self.volume_var,
            command=self._on_volume_change
        )
        self.volume_slider.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.volume_value_label = ctk.CTkLabel(
            self.volume_frame,
            text=f"{VOLUME_LEVEL}%",
            font=ctk.CTkFont(size=14),
            width=40
        )
        self.volume_value_label.pack(side="left")
        
        # Device Selection
        self.device_frame = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        self.device_frame.pack(fill="x", padx=15, pady=(15, 5))
        
        self.device_label = ctk.CTkLabel(
            self.device_frame,
            text="Spotify Device:",
            font=ctk.CTkFont(size=14)
        )
        self.device_label.pack(anchor="w", padx=(0, 10), pady=(0, 5))
        
        self.devices_var = ctk.StringVar(value="Loading devices...")
        self.devices_dropdown = ctk.CTkOptionMenu(
            self.device_frame,
            variable=self.devices_var,
            values=["Loading devices..."],
            command=self._on_device_change,
            width=300
        )
        self.devices_dropdown.pack(anchor="w", pady=(0, 5))
        
        self.refresh_devices_button = ctk.CTkButton(
            self.device_frame,
            text="Refresh Devices",
            command=self._load_devices,
            width=150
        )
        self.refresh_devices_button.pack(anchor="w", pady=(0, 10))
        
        # Playback Duration
        self.playback_frame = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        self.playback_frame.pack(fill="x", padx=15, pady=(15, 5))
        
        self.playback_label = ctk.CTkLabel(
            self.playback_frame,
            text="Playback Duration (seconds):",
            font=ctk.CTkFont(size=14)
        )
        self.playback_label.pack(anchor="w", padx=(0, 10), pady=(0, 5))
        
        self.playback_var = ctk.DoubleVar(value=PLAYBACK_DURATION)
        self.playback_slider = ctk.CTkSlider(
            self.playback_frame,
            from_=0.1,
            to=5.0,
            number_of_steps=49,
            variable=self.playback_var,
            command=self._on_playback_change
        )
        self.playback_slider.pack(fill="x", padx=(0, 10), pady=(0, 5))
        
        self.playback_value_label = ctk.CTkLabel(
            self.playback_frame,
            text=f"{PLAYBACK_DURATION}s",
            font=ctk.CTkFont(size=14),
            width=40
        )
        self.playback_value_label.pack(anchor="w")
        
        # ===== FOOTER SECTION =====
        self.footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.footer_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
        
        # Back button
        self.back_button = ctk.CTkButton(
            self.footer_frame,
            text="Save & Return",
            command=self._save_and_return,
            height=40,
            fg_color=("#1DB954", "#1DB954"),
            hover_color=("#18a449", "#18a449")
        )
        self.back_button.pack(side="right", padx=10)
    
    def _load_devices(self):
        """Load available Spotify devices"""
        devices = self.spotify_manager.get_available_devices()
        
        if not devices:
            self.devices_dropdown.configure(values=["No devices found"])
            self.devices_var.set("No devices found")
            return
        
        # Format device options
        device_options = [f"{d['name']} ({d['type']})" for d in devices]
        
        # Store device IDs for lookup
        self.device_map = {f"{d['name']} ({d['type']})": d['id'] for d in devices}
        
        # Update dropdown
        self.devices_dropdown.configure(values=device_options)
        
        # Set current device if one is already selected
        current_device_id = self.spotify_manager.selected_device_id
        
        if current_device_id:
            # Find matching device in our list
            for display_name, device_id in self.device_map.items():
                if device_id == current_device_id:
                    self.devices_var.set(display_name)
                    break
        else:
            # Set first device as default
            self.devices_var.set(device_options[0])
            # Select this device
            self._on_device_change(device_options[0])
    
    def _on_volume_change(self, value):
        """Handle volume slider change"""
        volume = int(value)
        self.volume_value_label.configure(text=f"{volume}%")
        self.spotify_manager.set_volume(volume)
        
    def _on_device_change(self, selected_device):
        """Handle device selection change"""
        if selected_device in self.device_map:
            device_id = self.device_map[selected_device]
            self.spotify_manager.set_device(device_id)
    
    def _on_playback_change(self, value):
        """Handle playback duration slider change"""
        duration = round(float(value), 1)
        self.playback_value_label.configure(text=f"{duration}s")
        
    def _save_and_return(self):
        """Save settings and return to start screen"""
        settings = {
            'volume': int(self.volume_var.get()),
            'playback_duration': round(float(self.playback_var.get()), 1)
        }
        
        # Update app settings
        self.parent.update_settings(settings)
        
        # Return to start screen
        self.parent.show_start_screen()

class CheatSettingsScreen(ctk.CTkFrame):
    """Secret cheat and advanced settings screen for the Spotify Guessing Game"""
    
    def __init__(self, parent, game_settings=None):
        super().__init__(parent, fg_color=("#f0f0f0", "#1e1e1e"), corner_radius=0)
        self.parent = parent
        self.game_settings = game_settings or {}
        # Create UI elements
        self._create_widgets()
    
    def _create_widgets(self):
        """Create all UI widgets for the cheat settings screen"""
        # Master layout
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)  # Header
        self.rowconfigure(1, weight=1)  # Content
        self.rowconfigure(2, weight=0)  # Footer
        
        # ===== HEADER SECTION =====
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 0))
        
        # Title
        self.title_label = ctk.CTkLabel(
            self.header_frame, 
            text="✨ Secret Settings & Cheats ✨", 
            font=ctk.CTkFont(family="Helvetica", size=24, weight="bold"),
            text_color=("#FF5733", "#FF5733")
        )
        self.title_label.pack(pady=(10, 5))
        
        # ===== CONTENT SECTION =====
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.rowconfigure(0, weight=1)
        
        # Cheats Frame
        self.cheats_frame = ctk.CTkFrame(self.content_frame, corner_radius=15)
        self.cheats_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
        
        # Game Settings Section
        self.game_label = ctk.CTkLabel(
            self.cheats_frame,
            text="Game Settings",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.game_label.pack(pady=(15, 5), padx=15, anchor="w")
        
        # Max Guess Count
        self.guess_frame = ctk.CTkFrame(self.cheats_frame, fg_color="transparent")
        self.guess_frame.pack(fill="x", padx=15, pady=(10, 5))
        
        self.guess_label = ctk.CTkLabel(
            self.guess_frame,
            text="Max Guesses per Song:",
            font=ctk.CTkFont(size=14)
        )
        self.guess_label.pack(side="left", padx=(0, 10))
        
        self.guess_var = ctk.IntVar(value=MAX_GUESS_COUNT)
        self.guess_slider = ctk.CTkSlider(
            self.guess_frame,
            from_=1,
            to=10,
            number_of_steps=9,
            variable=self.guess_var,
            command=self._on_guess_change
        )
        self.guess_slider.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.guess_value_label = ctk.CTkLabel(
            self.guess_frame,
            text=f"{MAX_GUESS_COUNT}",
            font=ctk.CTkFont(size=14),
            width=20
        )
        self.guess_value_label.pack(side="left")
        
        # Max Lives
        self.lives_frame = ctk.CTkFrame(self.cheats_frame, fg_color="transparent")
        self.lives_frame.pack(fill="x", padx=15, pady=(15, 5))
        
        self.lives_label = ctk.CTkLabel(
            self.lives_frame,
            text="Max Lives:",
            font=ctk.CTkFont(size=14)
        )
        self.lives_label.pack(side="left", padx=(0, 10))
        
        self.lives_var = ctk.IntVar(value=MAX_LIVES)
        self.lives_slider = ctk.CTkSlider(
            self.lives_frame,
            from_=1,
            to=10,
            number_of_steps=9,
            variable=self.lives_var,
            command=self._on_lives_change
        )
        self.lives_slider.pack(side="left", fill="x", expand=True, padx=(0, 10))
        
        self.lives_value_label = ctk.CTkLabel(
            self.lives_frame,
            text=f"{MAX_LIVES}",
            font=ctk.CTkFont(size=14),
            width=20
        )
        self.lives_value_label.pack(side="left")
        
        # Cheats Section
        self.cheats_label = ctk.CTkLabel(
            self.cheats_frame,
            text="Cheats",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.cheats_label.pack(pady=(25, 5), padx=15, anchor="w")
        
        # Infinite Lives
        self.infinite_lives_var = ctk.BooleanVar(value=False)
        self.infinite_lives_check = ctk.CTkCheckBox(
            self.cheats_frame,
            text="Infinite Lives",
            variable=self.infinite_lives_var,
            font=ctk.CTkFont(size=14),
            checkbox_width=20,
            checkbox_height=20
        )
        self.infinite_lives_check.pack(anchor="w", padx=15, pady=(10, 5))
        
        # Show Answers
        self.show_answers_var = ctk.BooleanVar(value=False)
        self.show_answers_check = ctk.CTkCheckBox(
            self.cheats_frame,
            text="Show Answers (Debug Mode)",
            variable=self.show_answers_var,
            font=ctk.CTkFont(size=14),
            checkbox_width=20,
            checkbox_height=20
        )
        self.show_answers_check.pack(anchor="w", padx=15, pady=(5, 5))
        
        # Skip Verification
        self.skip_verification_var = ctk.BooleanVar(value=False)
        self.skip_verification_check = ctk.CTkCheckBox(
            self.cheats_frame,
            text="Skip Answer Verification",
            variable=self.skip_verification_var,
            font=ctk.CTkFont(size=14),
            checkbox_width=20,
            checkbox_height=20
        )
        self.skip_verification_check.pack(anchor="w", padx=15, pady=(5, 15))
        
        # ===== FOOTER SECTION =====
        self.footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.footer_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=(0, 20))
        
        # Back button
        self.back_button = ctk.CTkButton(
            self.footer_frame,
            text="Save & Return",
            command=self._save_and_return,
            height=40,
            fg_color=("#FF5733", "#FF5733"),
        )
        self.back_button.pack(side="right", padx=10)
    
    def _on_guess_change(self, value):
        """Handle max guess slider change"""
        guesses = int(value)
        self.guess_value_label.configure(text=f"{guesses}")
        
    def _on_lives_change(self, value):
        """Handle max lives slider change"""
        lives = int(value)
        self.lives_value_label.configure(text=f"{lives}")
        
    def _save_and_return(self):
        """Save settings and return to start screen"""
        # Save normal settings
        settings = {
            'max_guesses': int(self.guess_var.get()),
            'max_lives': int(self.lives_var.get())
        }
        self.parent.update_settings(settings)
        
        # Save cheat settings
        cheat_settings = {
            'infinite_lives': self.infinite_lives_var.get(),
            'show_answers': self.show_answers_var.get(),
            'skip_verification': self.skip_verification_var.get()
        }
        self.parent.update_settings(cheat_settings, is_cheat=True)
        
        # Return to start screen
        self.parent.show_start_screen()