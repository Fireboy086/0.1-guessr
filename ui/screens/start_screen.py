"""
Start Screen for Spotify Guessing Game
"""
import re
import os
import threading
import urllib.request
from io import BytesIO
from PIL import Image, ImageTk
import customtkinter as ctk
from urllib.parse import urlparse

class StartScreen(ctk.CTkFrame):
    """Playlist selection screen for the Spotify Guessing Game"""
    
    def __init__(self, parent, game_logic):
        super().__init__(parent, fg_color=("#f0f0f0", "#1e1e1e"), corner_radius=0)
        self.parent = parent
        # Center window on screen
        screen_width = self.parent.winfo_screenwidth()
        screen_height = self.parent.winfo_screenheight()
        x = (screen_width - 1000) // 2
        y = (screen_height - 1000) // 2
        self.parent.geometry(f"1000x1000+{x}+{y}")
        self.game_logic = game_logic
        
        # Image cache for playlist covers
        self.image_cache = {}
        self.current_cover_task = None
        self.current_playlist_id = None
        self._current_cover_image = None  # Keep reference to prevent garbage collection
        
        # Create UI elements
        self._create_widgets()
        
        # Load default playlists in background
        self.after(100, self._load_default_playlists)
    
    def _create_widgets(self):
        """Create all UI widgets"""
        # Master layout
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=0)  # Header
        self.rowconfigure(1, weight=1)  # Content
        self.rowconfigure(2, weight=0)  # Settings
        self.rowconfigure(3, weight=0)  # Footer
        
        # ===== HEADER SECTION =====
        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 0))
        
        # Title with Spotify-like styling
        self.title_label = ctk.CTkLabel(
            self.header_frame, 
            text="Spotify Guessing Game", 
            font=ctk.CTkFont(family="Helvetica", size=28, weight="bold"),
            text_color=("#1DB954", "#1DB954")  # Spotify green
        )
        self.title_label.pack(pady=(10, 5))
        
        # Subtitle
        self.subtitle_label = ctk.CTkLabel(
            self.header_frame,
            text="Test your music knowledge!",
            font=ctk.CTkFont(size=16),
            text_color=("gray50", "gray70")
        )
        self.subtitle_label.pack(pady=(0, 10))
        
        # ===== CONTENT SECTION =====
        self.content_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.content_frame.grid(row=1, column=0, sticky="nsew", padx=20, pady=10)
        self.content_frame.columnconfigure(0, weight=1)
        self.content_frame.columnconfigure(1, weight=1)
        self.content_frame.rowconfigure(0, weight=1)
        
        # Left panel - Playlist Selection
        self.left_panel = ctk.CTkFrame(self.content_frame, corner_radius=15)
        self.left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=10)
        
        # Playlist section title
        self.playlist_header = ctk.CTkLabel(
            self.left_panel,
            text="Select a Playlist",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.playlist_header.pack(pady=(15, 5), padx=15, anchor="w")
        
        # Playlist type tabs
        self.tab_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        self.tab_frame.pack(fill="x", padx=15, pady=(5, 0))
        
        self.tab_var = ctk.StringVar(value="default")
        
        self.default_tab = ctk.CTkButton(
            self.tab_frame,
            text="Default",
            command=lambda: self._change_tab("default"),
            fg_color=("#1DB954", "#1DB954"),
            text_color="white",
            corner_radius=8,
            width=100,
            height=30
        )
        self.default_tab.pack(side="left", padx=(0, 5))
        
        self.custom_tab = ctk.CTkButton(
            self.tab_frame,
            text="Custom URL",
            command=lambda: self._change_tab("custom"),
            fg_color="transparent",
            hover_color=("gray80", "gray30"),
            corner_radius=8,
            width=100,
            height=30
        )
        self.custom_tab.pack(side="left")
        
        # ===== SETTINGS SECTION =====
        self.settings_frame = ctk.CTkFrame(self, corner_radius=15)
        self.settings_frame.grid(row=2, column=0, sticky="ew", padx=20, pady=10)
        
        # Settings title
        self.settings_header = ctk.CTkLabel(
            self.settings_frame,
            text="Game Settings",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.settings_header.pack(pady=(15, 5), padx=15, anchor="w")
        
        # Settings content frame
        self.settings_content = ctk.CTkFrame(self.settings_frame, fg_color="transparent")
        self.settings_content.pack(fill="x", padx=15, pady=(5, 15))
        
        # Game mode selection
        self.mode_frame = ctk.CTkFrame(self.settings_content, fg_color="transparent")
        self.mode_frame.pack(fill="x", pady=5)
        
        self.mode_label = ctk.CTkLabel(
            self.mode_frame,
            text="Game Mode:",
            font=ctk.CTkFont(size=14)
        )
        self.mode_label.pack(side="left", padx=(0, 10))
        
        self.mode_var = ctk.StringVar(value="Normal")
        self.mode_menu = ctk.CTkOptionMenu(
            self.mode_frame,
            values=["Normal", "Hard", "Harder", "Expert"],
            variable=self.mode_var,
            command=self._update_mode_description,
            width=120
        )
        self.mode_menu.pack(side="left")
        
        # Mode description
        self.mode_desc = ctk.CTkLabel(
            self.mode_frame,
            text="",
            font=ctk.CTkFont(size=12),
            text_color=("gray50", "gray70")
        )
        self.mode_desc.pack(side="left", padx=10)
        
        # Playback settings frame
        self.playback_frame = ctk.CTkFrame(self.settings_content, fg_color="transparent")
        self.playback_frame.pack(fill="x", pady=5)
        
        # Per reveal slider
        self.perreveal_label = ctk.CTkLabel(
            self.playback_frame,
            text="Seconds per reveal:",
            font=ctk.CTkFont(size=14)
        )
        self.perreveal_label.pack(side="left", padx=(0, 10))
        
        self.perreveal_var = ctk.DoubleVar(value=1.0)
        self.perreveal_slider = ctk.CTkSlider(
            self.playback_frame,
            from_=0.5,
            to=3.0,
            number_of_steps=5,
            variable=self.perreveal_var,
            width=120
        )
        self.perreveal_slider.pack(side="left")
        
        self.perreveal_value = ctk.CTkLabel(
            self.playback_frame,
            text="1.0s",
            font=ctk.CTkFont(size=12)
        )
        self.perreveal_value.pack(side="left", padx=10)
        
        # Random start checkbox
        self.randomstart_var = ctk.BooleanVar(value=True)
        self.randomstart_check = ctk.CTkCheckBox(
            self.playback_frame,
            text="Random start position",
            variable=self.randomstart_var,
            font=ctk.CTkFont(size=14)
        )
        self.randomstart_check.pack(side="left", padx=20)
        
        # Update initial mode description
        self._update_mode_description()
        
        # Bind slider to update value label
        self.perreveal_slider.configure(command=self._update_perreveal_value)
        
        # Playlist selection container (scrollable)
        self.playlist_container = ctk.CTkScrollableFrame(
            self.left_panel,
            fg_color="transparent",
            corner_radius=0
        )
        self.playlist_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Playlist option buttons (will be populated)
        self.playlist_buttons = []
        self.selected_playlist = None
        
        # Loading indicator for playlists
        self.playlist_loading = ctk.CTkLabel(
            self.playlist_container,
            text="Loading playlists...",
            font=ctk.CTkFont(size=14),
            text_color=("gray50", "gray70")
        )
        self.playlist_loading.pack(pady=20)
        
        # Custom URL frame (initially hidden)
        self.custom_url_frame = ctk.CTkFrame(self.left_panel, fg_color="transparent")
        
        # URL input with validation
        self.url_label = ctk.CTkLabel(
            self.custom_url_frame,
            text="Enter Spotify Playlist URL:",
            font=ctk.CTkFont(size=14)
        )
        self.url_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        self.url_entry_frame = ctk.CTkFrame(self.custom_url_frame, fg_color="transparent")
        self.url_entry_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.url_entry = ctk.CTkEntry(
            self.url_entry_frame,
            placeholder_text="spotify:playlist:id or https://...",
            height=35,
            font=ctk.CTkFont(size=14)
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        self.url_submit = ctk.CTkButton(
            self.url_entry_frame,
            text="Load",
            command=self._validate_custom_url,
            width=60,
            height=35,
            corner_radius=8
        )
        self.url_submit.pack(side="right")
        
        # Bind events to URL entry
        self.url_entry.bind("<Return>", lambda event: self._validate_custom_url())
        
        # Message label for URL validation
        self.url_message = ctk.CTkLabel(
            self.custom_url_frame,
            text="",
            font=ctk.CTkFont(size=13),
            text_color=("#1DB954", "#1DB954")
        )
        self.url_message.pack(fill="x", padx=10, pady=(0, 10))
        
        # Right panel - Preview & Settings
        self.right_panel = ctk.CTkFrame(self.content_frame, corner_radius=15)
        self.right_panel.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=10)
        
        # Make the right panel content scrollable
        self.right_scroll = ctk.CTkScrollableFrame(
            self.right_panel,
            fg_color="transparent",
            corner_radius=0
        )
        self.right_scroll.pack(fill="both", expand=True, padx=0, pady=0)
        
        # Cover image section
        self.cover_frame = ctk.CTkFrame(self.right_scroll, fg_color="transparent")
        self.cover_frame.pack(fill="x", padx=20, pady=20)
        
        self.cover_title = ctk.CTkLabel(
            self.cover_frame,
            text="Playlist Preview",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.cover_title.pack(anchor="w", pady=(0, 10))
        
        # Cover image placeholder
        self.cover_image = ctk.CTkLabel(
            self.cover_frame,
            text="Select a playlist",
            font=ctk.CTkFont(size=14),
            fg_color=("gray90", "gray20"),
            corner_radius=10,
            width=200,
            height=200
        )
        self.cover_image.pack(pady=10)
        
        # Playlist info
        self.playlist_info = ctk.CTkLabel(
            self.cover_frame,
            text="",
            font=ctk.CTkFont(size=14),
            justify="center"
        )
        self.playlist_info.pack(pady=(5, 15))
        
        # ===== FOOTER SECTION =====
        self.footer_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.footer_frame.grid(row=3, column=0, sticky="ew", padx=20, pady=(0, 20))
        
        # Start game button
        self.start_button = ctk.CTkButton(
            self.footer_frame,
            text="Start Game",
            command=self._on_start_button_click,
            font=ctk.CTkFont(size=16, weight="bold"),
            fg_color=("#1DB954", "#1DB954"),
            hover_color=("#19A347", "#19A347"),
            corner_radius=10,
            height=45,
            width=200
        )
        self.start_button.pack(pady=15)
        self.start_button.configure(state="disabled")  # Initially disabled
    
    def _change_tab(self, tab):
        """Switch between default and custom playlist tabs"""
        # Provide immediate feedback and prevent double-clicks
        self.default_tab.configure(state="disabled") 
        self.custom_tab.configure(state="disabled")
        self.update_idletasks()
        
        self.tab_var.set(tab)
        
        if tab == "default":
            # Highlight default tab
            self.default_tab.configure(fg_color=("#1DB954", "#1DB954"), text_color="white")
            self.custom_tab.configure(fg_color="transparent", text_color=("black", "white"))
            
            # Show playlist container, hide custom URL frame
            self.playlist_container.pack(fill="both", expand=True, padx=10, pady=10)
            self.custom_url_frame.pack_forget()
            
            # Reset custom URL entry
            self.url_entry.delete(0, "end")
            self.url_message.configure(text="")
            
            # Restore selection if available
            if self.selected_playlist:
                self._select_playlist(self.selected_playlist)
        else:
            # Highlight custom tab
            self.custom_tab.configure(fg_color=("#1DB954", "#1DB954"), text_color="white")
            self.default_tab.configure(fg_color="transparent", text_color=("black", "white"))
            
            # Hide playlist container, show custom URL frame
            self.playlist_container.pack_forget()
            self.custom_url_frame.pack(fill="both", expand=True, padx=10, pady=10)
            
            # Clear selected playlist
            self._clear_selection()
            
            # Focus URL entry
            self.url_entry.focus_set()
        
        # Re-enable tabs after a short delay
        self.after(200, lambda: self._enable_tabs())
    
    def _enable_tabs(self):
        """Re-enable tabs after tab switch"""
        self.default_tab.configure(state="normal")
        self.custom_tab.configure(state="normal")
    
    def _load_default_playlists(self):
        """Load default playlists in background thread"""
        threading.Thread(target=self._fetch_playlists, daemon=True).start()
    
    def _fetch_playlists(self):
        """Fetch playlists from Spotify API"""
        try:
            # Try different function names depending on what's available in game_logic
            if hasattr(self.game_logic, 'get_available_playlists'):
                options = self.game_logic.get_available_playlists()
            elif hasattr(self.game_logic, 'get_user_playlists'):
                # Format the user playlists into the expected structure
                user_playlists = self.game_logic.get_user_playlists()
                options = {
                    "Your Playlists": {playlist['name']: playlist['id'] for playlist in user_playlists},
                    "Spotify Recommendations": {
                        "Liked Songs": "liked_songs",
                        "On Repeat": "recently_played"  # Changed from "Recently Played" to "On Repeat"
                    }
                }
            else:
                # Fallback to some default options
                options = {
                    "Spotify Recommendations": {
                        "Liked Songs": "liked_songs",
                        "On Repeat": "recently_played"  # Changed from "Recently Played" to "On Repeat"
                    }
                }
            
            # Update UI in main thread
            if options:
                self.after(0, lambda: self._update_playlist_options(options))
            else:
                self.after(0, lambda: self._show_playlist_error())
        except Exception as e:
            print(f"Error fetching playlists: {e}")
            self.after(0, lambda: self._show_playlist_error())
    
    def _update_playlist_options(self, options):
        """Update playlist options in the UI"""
        # Remove loading indicator
        self.playlist_loading.pack_forget()
        
        # Clear existing buttons
        for button in self.playlist_buttons:
            button.destroy()
        self.playlist_buttons = []
        
        # Sort categories to ensure Spotify Recommendations are at the top
        sorted_categories = sorted(
            options.keys(),
            key=lambda x: 0 if "Spotify" in x else 1  # This puts Spotify first
        )
        
        # Create a button for each playlist option
        for category in sorted_categories:
            playlists = options[category]
            
            # Category label
            category_label = ctk.CTkLabel(
                self.playlist_container,
                text=category,
                font=ctk.CTkFont(size=16, weight="bold"),
                anchor="w"
            )
            category_label.pack(fill="x", padx=5, pady=(15, 5))
            
            # Playlists in this category
            for name, value in playlists.items():
                button = ctk.CTkButton(
                    self.playlist_container,
                    text=name,
                    anchor="w",
                    fg_color="transparent",
                    hover_color=("gray85", "gray30"),
                    corner_radius=8,
                    height=35,
                    command=lambda v=value, n=name: self._select_playlist(v, n)
                )
                button.pack(fill="x", padx=5, pady=3)
                self.playlist_buttons.append(button)
        
        # Enable start button once options are loaded
        if self.playlist_buttons:
            # Select first playlist by default
            first_playlist = self.playlist_buttons[0]
            first_playlist.invoke()
    
    def _show_playlist_error(self):
        """Show error when playlists can't be loaded"""
        self.playlist_loading.configure(
            text="Failed to load playlists.\nTry restarting the app.",
            text_color=("red", "#ff5555")
        )
    
    def _select_playlist(self, playlist_id, name=None):
        """Select a playlist from the options"""
        # Ensure UI is responsive during selection
        self.update_idletasks()
        
        # Clear previous selection
        self._clear_selection()
        
        # Store selected playlist
        self.selected_playlist = playlist_id
        
        # Highlight selected button with visual feedback
        for button in self.playlist_buttons:
            if button.cget("text") == name:
                button.configure(
                    fg_color=("#1DB954", "#1DB954"),
                    text_color=("white", "white")
                )
                # Force update to show selection immediately
                self.update_idletasks()
                break
        
        # Update cover image
        self._load_playlist_cover(playlist_id, name)
        
        # Enable start button
        self.start_button.configure(state="normal")
        self.update_idletasks()
    
    def _clear_selection(self):
        """Clear playlist selection"""
        self.selected_playlist = None
        
        # Reset button styles
        for button in self.playlist_buttons:
            button.configure(
                fg_color="transparent",
                text_color=("black", "white")
            )
    
    def _validate_custom_url(self):
        """Validate custom playlist URL"""
        # Provide immediate feedback
        self.url_submit.configure(state="disabled")
        self.update_idletasks()
        
        url = self.url_entry.get().strip()
        
        if not url:
            self._show_url_message("Please enter a playlist URL", "red")
            self.url_submit.configure(state="normal")
            return
        
        # Show loading state
        self.url_message.configure(text="Loading playlist...", text_color=("orange", "orange"))
        self.cover_image.configure(text="Loading...", fg_color=("gray90", "gray20"))
        self.update_idletasks()
        
        # Extract playlist ID
        playlist_id = self._extract_playlist_id(url)
        
        if not playlist_id:
            self._show_url_message("Invalid playlist URL format", "red")
            self.url_submit.configure(state="normal")
            return
        
        # Update entry with extracted ID
        self.url_entry.delete(0, "end")
        self.url_entry.insert(0, playlist_id)
        
        # Fetch playlist info in background
        threading.Thread(
            target=self._fetch_custom_playlist_info,
            args=(playlist_id,),
            daemon=True
        ).start()
        
        # Re-enable submit button after a short delay
        self.after(500, lambda: self.url_submit.configure(state="normal"))
    
    def _extract_playlist_id(self, url):
        """Extract playlist ID from various URL formats"""
        # Handle empty input
        if not url or url.strip() == "":
            return None
            
        # Already an ID format
        if re.match(r"^[a-zA-Z0-9]+$", url):
            return url
            
        # Spotify URI format
        if url.startswith("spotify:playlist:"):
            return url.split(":")[-1]
        
        # Try to extract from URL
        try:
            # Parse the URL
            parsed = urlparse(url)
            
            # Handle spotify.com URLs
            if "spotify.com" in parsed.netloc:
                path_parts = parsed.path.split('/')
                if "playlist" in path_parts:
                    idx = path_parts.index("playlist")
                    if idx + 1 < len(path_parts):
                        return path_parts[idx + 1].split("?")[0]
            
            # Try regex as fallback
            match = re.search(r"playlist[/:]([a-zA-Z0-9]+)", url)
            if match:
                return match.group(1).split("?")[0]
                
        except Exception as e:
            print(f"Error extracting playlist ID: {e}")
            
        return None
    
    def _fetch_custom_playlist_info(self, playlist_id):
        """Fetch custom playlist info"""
        try:
            # Get playlist info from Spotify
            playlist_info = self.game_logic.sp.playlist(playlist_id)
            
            # Extract relevant info
            name = playlist_info['name']
            owner = playlist_info['owner']['display_name']
            total_tracks = playlist_info['tracks']['total']
            
            # Get cover image
            image_url = None
            if playlist_info['images'] and len(playlist_info['images']) > 0:
                image_url = playlist_info['images'][0]['url']
            
            # Update UI in main thread
            self.after(0, lambda: self._show_custom_playlist_success(
                playlist_id, name, owner, total_tracks, image_url
            ))
            
        except Exception as e:
            print(f"Error fetching custom playlist: {e}")
            self.after(0, lambda: self._show_url_message(
                "Couldn't load playlist. Check the URL/ID", "red"
            ))
            self.after(0, lambda: self.cover_image.configure(
                text="Error loading playlist",
                fg_color=("#ffcccc", "#552222")
            ))
    
    def _show_custom_playlist_success(self, playlist_id, name, owner, track_count, image_url):
        """Show successful custom playlist load"""
        # Update message
        self._show_url_message(f"Successfully loaded: {name}", "green")
        
        # Update info
        self.playlist_info.configure(
            text=f"Name: {name}\nBy: {owner}\nTracks: {track_count}"
        )
        
        # Store playlist ID
        self.selected_playlist = playlist_id
        
        # Enable start button
        self.start_button.configure(state="normal")
        
        # Load cover image
        if image_url:
            self._load_cover_image(image_url)
        else:
            self.cover_image.configure(
                text=f"{name}",
                fg_color=("#cccccc", "#333333")
            )
    
    def _show_url_message(self, message, color):
        """Show message for URL validation"""
        colors = {
            "red": ("#ff3333", "#ff5555"),
            "green": ("#1DB954", "#1DB954"),
            "orange": ("#FFA500", "#FFA500")
        }
        
        self.url_message.configure(
            text=message,
            text_color=colors.get(color, ("black", "white"))
        )
    
    def _load_playlist_cover(self, playlist_id, name=None):
        """Load cover for the selected playlist"""
        self.current_playlist_id = playlist_id
        
        # Show loading state
        self.cover_image.configure(
            text="Loading...",
            fg_color=("gray90", "gray20"),
            image=None
        )
        
        # Update playlist info
        if name:
            self.playlist_info.configure(text=f"Selected: {name}")
        
        # Handle special playlists with generic images
        if playlist_id == "liked_songs":
            self._show_generic_cover("liked", "Liked Songs")
            return
        elif playlist_id == "recently_played":
            self._show_generic_cover("recent", "On Repeat")  # Changed from "Recently Played" to "On Repeat"
            return
        
        # Start thread to fetch playlist info and cover
        threading.Thread(
            target=self._fetch_playlist_info,
            args=(playlist_id,),
            daemon=True
        ).start()
    
    def _fetch_playlist_info(self, playlist_id):
        """Fetch playlist info in background"""
        try:
            # Get playlist details from Spotify
            playlist_info = self.game_logic.sp.playlist(playlist_id)
            
            # Extract info
            name = playlist_info['name']
            owner = playlist_info['owner']['display_name']
            total_tracks = playlist_info['tracks']['total']
            
            # Get cover image URL
            image_url = None
            if playlist_info['images'] and len(playlist_info['images']) > 0:
                image_url = playlist_info['images'][0]['url']
            
            # Update UI in main thread
            self.after(0, lambda: self._update_playlist_info(
                name, owner, total_tracks
            ))
            
            # Load cover image if available
            if image_url:
                self._load_cover_image(image_url)
                
        except Exception as e:
            print(f"Error fetching playlist info: {e}")
            self.after(0, lambda: self._show_generic_cover("error", "Error loading cover"))
    
    def _update_playlist_info(self, name, owner, track_count):
        """Update playlist info display"""
        self.playlist_info.configure(
            text=f"Name: {name}\nBy: {owner}\nTracks: {track_count}"
        )
    
    def _load_cover_image(self, url):
        """Load cover image from URL"""
        # Cancel any existing tasks
        if self.current_cover_task:
            self.current_cover_task = None
            
        # Check if image is already cached
        if url in self.image_cache:
            self._set_cover_image(self.image_cache[url])
            return
            
        # Create a new task
        task_id = id(url)
        self.current_cover_task = task_id
        
        # Load image in background thread
        threading.Thread(
            target=self._fetch_cover_image,
            args=(url, task_id),
            daemon=True
        ).start()
    
    def _fetch_cover_image(self, url, task_id):
        """Fetch cover image in background thread"""
        try:
            # Skip if this task was cancelled
            if self.current_cover_task != task_id:
                return
                
            # Download image
            with urllib.request.urlopen(url) as response:
                image_data = response.read()
                
            # Skip if task was cancelled during download
            if self.current_cover_task != task_id:
                return
                
            # Process image
            image = Image.open(BytesIO(image_data))
            image = image.resize((180, 180), Image.LANCZOS)
            
            # Create CTk image
            ctk_img = ctk.CTkImage(light_image=image, dark_image=image, size=(180, 180))
            
            # Cache the image
            self.image_cache[url] = ctk_img
            
            # Update UI in main thread
            if self.current_cover_task == task_id:
                self.after(0, lambda: self._set_cover_image(ctk_img))
                
        except Exception as e:
            print(f"Error loading cover image: {e}")
            if self.current_cover_task == task_id:
                self.after(0, lambda: self._show_generic_cover("error", "Error loading cover"))
    
    def _set_cover_image(self, ctk_img):
        """Set the cover image"""
        # First forget any existing image to avoid conflicts
        self.cover_image.configure(image=None, text="")
        self.update_idletasks()
        
        # Now set the new image
        self.cover_image.configure(text="", image=ctk_img)
        
        # Store reference to prevent garbage collection
        self._current_cover_image = ctk_img
    
    def _show_generic_cover(self, cover_type, text=None):
        """Show a generic cover image"""
        color_map = {
            "liked": ("#4CAF50", "#2E7D32"),
            "recent": ("#2196F3", "#1565C0"),
            "error": ("#F44336", "#C62828"),
            "default": ("#9E9E9E", "#616161")
        }
        
        fg_color = color_map.get(cover_type, color_map["default"])
        
        # Set default text if none provided
        if text is None:
            if cover_type == "liked":
                text = "Liked Songs"
            elif cover_type == "recent":
                text = "On Repeat"  # Changed from "Recently Played" to "On Repeat"
            elif cover_type == "error":
                text = "Error loading playlist"
            else:
                text = "Select a playlist"
        
        # Check if we should load a custom image for special playlists
        if cover_type == "liked":
            # Try to load heart image from resources
            try:
                import os
                heart_image_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "resources", "liked_songs.png")
                print(f"Loading liked songs image from: {heart_image_path}")
                
                if os.path.exists(heart_image_path):
                    from PIL import Image
                    heart_image = Image.open(heart_image_path)
                    heart_image = heart_image.resize((180, 180), Image.LANCZOS)
                    ctk_img = ctk.CTkImage(light_image=heart_image, dark_image=heart_image, size=(180, 180))
                    
                    # First forget any existing image to avoid conflicts
                    self.cover_image.configure(image=None, text="")
                    self.update_idletasks()
                    
                    # Now set the new image
                    self.cover_image.configure(text="", image=ctk_img, fg_color="transparent")
                    
                    # Store reference to prevent garbage collection
                    self._current_cover_image = ctk_img
                    return
                else:
                    print(f"Liked songs image not found at: {heart_image_path}")
            except Exception as e:
                print(f"Could not load liked songs image: {e}")
                # Fall back to text-only version if image fails to load
        
        elif cover_type == "recent":
            # Try to load on repeat image from resources
            try:
                import os
                repeat_image_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "resources", "on_repeat.png")
                print(f"Loading on repeat image from: {repeat_image_path}")
                
                if os.path.exists(repeat_image_path):
                    from PIL import Image
                    repeat_image = Image.open(repeat_image_path)
                    repeat_image = repeat_image.resize((180, 180), Image.LANCZOS)
                    ctk_img = ctk.CTkImage(light_image=repeat_image, dark_image=repeat_image, size=(180, 180))
                    
                    # First forget any existing image to avoid conflicts
                    self.cover_image.configure(image=None, text="")
                    self.update_idletasks()
                    
                    # Now set the new image
                    self.cover_image.configure(text="", image=ctk_img, fg_color="transparent")
                    
                    # Store reference to prevent garbage collection
                    self._current_cover_image = ctk_img
                    return
                else:
                    print(f"On repeat image not found at: {repeat_image_path}")
            except Exception as e:
                print(f"Could not load on repeat image: {e}")
                # Fall back to text-only version if image fails to load
        
        # First forget any existing image to avoid conflicts
        self.cover_image.configure(image=None)
        self.update_idletasks()
        
        # Use text-only cover if no image available
        self.cover_image.configure(
            text=text,
            fg_color=fg_color
        )
    
    def _update_mode_description(self):
        """Update mode description based on selection"""
        # This is already covered in the radio buttons
        pass
    
    def _on_start_button_click(self):
        """Handle start button click"""
        # Disable button to prevent double clicks and provide visual feedback
        self.start_button.configure(
            state="disabled",
            text="Loading...",
            fg_color=("gray70", "gray30")
        )
        
        # Force update the UI before proceeding
        self.update_idletasks()
        
        # Start game after short delay
        self.after(100, self._start_game)
    
    def _start_game(self):
        """Start the game with current settings"""
        try:
            # Get game settings
            guessdiff = self.mode_var.get()
            perreveal = self.perreveal_var.get()
            randomstart = self.randomstart_var.get()
            game_settings = (guessdiff, perreveal, randomstart)
            
            # Get selected playlist
            playlist_id = self.selected_playlist
            
            if not playlist_id:
                self._show_error("Please select a playlist first")
                return
            
            # Show loading state with feedback
            self.start_button.configure(text="Fetching tracks...")
            self.update_idletasks()
            
            if self.tab_var.get() == "default":
                # Start game with selected default playlist
                threading.Thread(
                    target=self._start_with_default_playlist,
                    args=(playlist_id, game_settings),
                    daemon=True
                ).start()
            else:
                # Start game with custom playlist
                threading.Thread(
                    target=self._start_with_custom_playlist,
                    args=(playlist_id, game_settings),
                    daemon=True
                ).start()
                
        except Exception as e:
            print(f"Error starting game: {e}")
            self._show_error(f"Error starting game: {str(e)}")
            
        finally:
            # Reset button state after delay (even if an error occurs)
            self.after(100, lambda: self._reset_start_button())
    
    def _reset_start_button(self):
        """Reset the start button to its default state"""
        self.start_button.configure(
            state="normal",
            text="Start Game",
            fg_color=("#1DB954", "#1DB954")
        )
        
        # Force update the UI
        self.update_idletasks()
    
    def _start_with_default_playlist(self, playlist_id, game_settings):
        """Start game with default playlist"""
        try:
            # Update button
            self.after(0, lambda: self.start_button.configure(text="Loading tracks..."))
            
            print(f"Starting game with playlist_id: {playlist_id}, settings: {game_settings}")
            
            # Call the correct method based on what's available
            if playlist_id == "liked_songs":
                print("Fetching liked songs...")
                # Need to handle liked songs specially
                try:
                    track_uris, track_names, track_artists = self.game_logic._get_liked_songs()
                    print(f"Got {len(track_uris) if track_uris else 0} liked songs")
                except Exception as e:
                    print(f"Error fetching liked songs: {e}")
                    # Try alternative method
                    tracks = self.game_logic.sp.current_user_saved_tracks(limit=50)
                    if 'items' in tracks:
                        print(f"Found {len(tracks['items'])} tracks with alternative method")
                        # Extract track info directly
                        track_uris = []
                        track_names = []
                        track_artists = []
                        for item in tracks['items']:
                            if 'track' in item and item['track']:
                                track = item['track']
                                track_uris.append(track['uri'])
                                track_names.append(track['name'])
                                artists = ", ".join([a['name'] for a in track['artists']])
                                track_artists.append(artists)
                    else:
                        raise Exception("Could not fetch liked songs directly")
            elif playlist_id == "recently_played":
                print("Fetching recently played songs...")
                try:
                    # Try getting directly from recently played
                    recent_tracks = self.game_logic.sp.current_user_recently_played(limit=50)
                    if 'items' in recent_tracks:
                        print(f"Found {len(recent_tracks['items'])} recently played tracks")
                        # Extract track info directly
                        track_uris = []
                        track_names = []
                        track_artists = []
                        for item in recent_tracks['items']:
                            if 'track' in item and item['track']:
                                track = item['track']
                                # Avoid duplicates
                                if track['uri'] not in track_uris:
                                    track_uris.append(track['uri'])
                                    track_names.append(track['name'])
                                    artists = ", ".join([a['name'] for a in track['artists']])
                                    track_artists.append(artists)
                        print(f"Extracted {len(track_uris)} unique tracks")
                    else:
                        # Try on-repeat playlist as fallback
                        print("No recently played tracks found, trying On Repeat playlist...")
                        tracks = self.game_logic.sp.current_user_top_tracks(limit=50)
                        if 'items' in tracks:
                            print(f"Found {len(tracks['items'])} top tracks")
                            track_uris = []
                            track_names = []
                            track_artists = []
                            for track in tracks['items']:
                                track_uris.append(track['uri'])
                                track_names.append(track['name'])
                                artists = ", ".join([a['name'] for a in track['artists']])
                                track_artists.append(artists)
                        else:
                            raise Exception("Could not find recently played or top tracks")
                except Exception as e:
                    print(f"Error getting recently played: {e}")
                    raise
            else:
                # Try using get_playlist_tracks with default playlist name
                print(f"Fetching playlist with id {playlist_id}")
                
                # First try _get_playlist_tracks_by_id
                try:
                    track_uris, track_names, track_artists = self.game_logic._get_playlist_tracks_by_id(playlist_id)
                    print(f"Successfully got {len(track_uris)} tracks by ID")
                except Exception as direct_e:
                    print(f"Failed to get by ID: {direct_e}, trying alternative methods")
                    
                    # Try with the name
                    try:
                        name_mapping = {
                            "liked_songs": "Liked Songs",
                            "recently_played": "Recently Played"
                        }
                        playlist_name = name_mapping.get(playlist_id, playlist_id)
                        track_uris, track_names, track_artists = self.game_logic.get_playlist_tracks(playlist_name)
                        print(f"Got {len(track_uris)} tracks by name")
                    except Exception as name_e:
                        print(f"Failed to get by name: {name_e}, trying direct Spotify API")
                        
                        # Direct Spotify API call as last resort
                        try:
                            results = self.game_logic.sp.playlist_items(
                                playlist_id, 
                                fields="items.track(name,uri,artists)",
                                limit=50
                            )
                            
                            if 'items' in results and results['items']:
                                print(f"Got {len(results['items'])} tracks directly from Spotify API")
                                track_uris = []
                                track_names = []
                                track_artists = []
                                for item in results['items']:
                                    if 'track' in item and item['track']:
                                        track = item['track']
                                        track_uris.append(track['uri'])
                                        track_names.append(track['name'])
                                        artists = ", ".join([a['name'] for a in track['artists']])
                                        track_artists.append(artists)
                            else:
                                raise Exception("No tracks found in playlist")
                        except Exception as spotify_e:
                            print(f"All methods failed. Final error: {spotify_e}")
                            raise
            
            # Print track information
            print(f"Track URIs type: {type(track_uris)}, Track names type: {type(track_names)}")
            print(f"Number of tracks: URIs={len(track_uris) if track_uris else 0}, Names={len(track_names) if track_names else 0}")
            
            # Check if we got enough tracks
            if not track_uris or len(track_uris) < 5:
                error_msg = f"Not enough tracks in playlist (need at least 5, got {len(track_uris) if track_uris else 0})"
                print(f"Error: {error_msg}")
                self.after(0, lambda msg=error_msg: self._show_error(msg))
                return
            
            # Launch game in main thread
            self.after(0, lambda u=track_uris, n=track_names, a=track_artists, m=game_settings: 
            self._launch_game(u, n, a, m))
            
        except Exception as e:
            error_msg = f"Error starting game with default playlist: {str(e)}"
            print(error_msg)
            # Pass the error message directly in the lambda to avoid scope issues
            self.after(0, lambda msg=error_msg: self._show_error(f"Error: {msg}"))
    
    def _start_with_custom_playlist(self, playlist_id, game_settings):
        """Start game with custom playlist"""
        try:
            # Update button
            self.after(0, lambda: self.start_button.configure(text="Loading tracks..."))
            
            # Try different approaches to get tracks
            try:
                # First try the direct method if available
                if hasattr(self.game_logic, '_get_playlist_tracks_by_id'):
                    track_uris, track_names, track_artists = self.game_logic._get_playlist_tracks_by_id(playlist_id)
                    if track_uris and len(track_uris) >= 5:
                        self.after(0, lambda u=track_uris, n=track_names, a=track_artists, m=game_settings: 
                        self._launch_game(u, n, a, m))
                        return
            except Exception as inner_e:
                print(f"First method failed: {inner_e}. Trying alternative...")
            
            # Fetch tracks directly from Spotify if the first method failed
            limit = 100
            offset = 0
            results = self.game_logic.sp.playlist_items(
                playlist_id,
                fields="items.track(name,uri,artists),next",
                limit=limit,
                offset=offset
            )

            if not results or 'items' not in results or len(results['items']) < 5:
                error_msg = "Not enough tracks in playlist (need at least 5)"
                print(f"Error: {error_msg}")
                self.after(0, lambda msg=error_msg: self._show_error(msg))
                return

            # Extract track details and handle pagination
            tracks = []
            while True:
                for item in results['items']:
                    if item['track'] and item['track'].get('uri'):
                        tracks.append(item['track'])

                if results.get('next'):
                    offset += limit
                    results = self.game_logic.sp.playlist_items(
                        playlist_id,
                        fields="items.track(name,uri,artists),next",
                        limit=limit,
                        offset=offset
                    )
                else:
                    break
            
            if len(tracks) < 5:
                error_msg = "Not enough playable tracks (need at least 5)"
                print(f"Error: {error_msg}")
                self.after(0, lambda msg=error_msg: self._show_error(msg))
                return
                
            # Prepare track data
            track_uris = [t['uri'] for t in tracks]
            track_names = [t['name'] for t in tracks]
            track_artists = [", ".join([a['name'] for a in t['artists']]) for t in tracks]
            
            # Launch game in main thread
            self.after(0, lambda u=track_uris, n=track_names, a=track_artists, m=game_settings: 
            self._launch_game(u, n, a, m))
            
        except Exception as e:
            error_msg = f"Error starting game with custom playlist: {str(e)}"
            print(error_msg)
            # Pass the error message directly in the lambda to avoid scope issues
            self.after(0, lambda msg=error_msg: self._show_error(f"Error: {msg}"))
    
    def _launch_game(self, track_uris, track_names, track_artists, game_settings):
        """Launch the game with the loaded tracks"""
        print(f"Launching game with {len(track_uris)} tracks in settings: {game_settings}")
        # Call the parent method to start the game
        try:
            # Ensure the game mode name is correct
            # Map "HarderHarder" to "Expert" if needed for backward compatibility
            if game_settings[0] == "HarderHarder":
                game_settings = ("Expert", game_settings[1], game_settings[2])
                print("Mapping 'HarderHarder' mode to 'Expert' for compatibility")
            
            # Set the game settings in game_logic if needed
            if hasattr(self.game_logic, 'set_game_settings'):
                self.game_logic.set_game_settings(game_settings)
                
            # Call the appropriate method on parent to start the game
            if hasattr(self.parent, 'start_game'):
                self.parent.start_game(track_uris, track_names, track_artists, game_settings)
            elif hasattr(self.parent, 'show_game_screen'):
                self.parent.show_game_screen(track_uris, track_names, track_artists, game_settings)
            else:
                raise Exception("Parent object has no method to start the game")
        except Exception as e:
            error_msg = f"Error launching game: {str(e)}"
            print(error_msg)
            self._show_error(f"Error: {error_msg}")
    
    def _show_error(self, message):
        """Show an error message in a modal window"""
        # Reset button
        self.start_button.configure(state="normal", text="Start Game")
        
        error_window = ctk.CTkToplevel(self)
        error_window.title("Error")
        error_window.geometry("300x150")
        error_window.transient(self.parent)
        error_window.grab_set()
        
        # Center the error window
        self.center_toplevel(error_window, 300, 150)
        
        # Error message
        ctk.CTkLabel(
            error_window,
            text=message,
            font=ctk.CTkFont(size=14),
            wraplength=250
        ).pack(pady=(20, 10), padx=20)
        
        # OK button
        ctk.CTkButton(
            error_window,
            text="OK",
            command=error_window.destroy
        ).pack(pady=(0, 20))
        
    def center_toplevel(self, window, width, height):
        """Center a toplevel window on the screen"""
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        window.geometry(f"{width}x{height}+{x}+{y}")
        
        # Make window appear on top and lift it
        window.lift()
        window.focus_force()
    
    def _update_perreveal_value(self, value):
        """Update the perreveal value label"""
        self.perreveal_value.configure(text=f"{value:.1f}s") 