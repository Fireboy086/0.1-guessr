"""
Spotify Playlist Viewer - A simple tool to view all songs in a Spotify playlist
"""
import re
import os
import sys
import io
import threading
import urllib.request
from PIL import Image, ImageTk
import customtkinter as ctk
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from config import *
from setup import load_spotify_credentials, setup_spotify_credentials

class PlaylistViewer(ctk.CTk):
    """A tool to view all songs in a Spotify playlist"""
    
    def __init__(self):
        super().__init__()
        
        # Window setup
        self.title("Spotify Playlist Viewer")
        self.geometry("900x600")
        self.minsize(800, 500)
        
        # Center the window
        self.center_window()
        
        # Initialize Spotify API
        self.setup_spotify_api()
        
        # Create UI
        self.create_widgets()
        
        # Image cache for playlist covers
        self.image_cache = {}
        
    def center_window(self):
        """Center the window on the screen"""
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        window_width = 900
        window_height = 600
        x = (screen_width - window_width) // 2
        y = (screen_height - window_height) // 2
        self.geometry(f"{window_width}x{window_height}+{x}+{y}")
        
        # Make window appear on top and lift it
        self.lift()
        self.focus_force()
    
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
        
    def setup_spotify_api(self):
        """Set up the Spotify API client"""
        client_id, client_secret, redirect_uri = load_spotify_credentials()
        
        if not client_id or not client_secret:
            # Credentials are missing; initiate setup
            setup_spotify_credentials()
            # Reload credentials after setup
            client_id, client_secret, redirect_uri = load_spotify_credentials()
            if not client_id or not client_secret:
                print("Spotify credentials are required to run the application.")
                sys.exit(1)
        
        # Initialize Spotify client
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            scope=SCOPE
        ))
        
    def create_widgets(self):
        """Create the UI elements"""
        # Main container frame
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # Title label
        self.title_label = ctk.CTkLabel(
            self.main_frame,
            text="Spotify Playlist Viewer",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.pack(pady=(0, 20))
        
        # Input section
        self.input_frame = ctk.CTkFrame(self.main_frame)
        self.input_frame.pack(fill="x", padx=20, pady=10)
        
        # URL entry
        self.url_label = ctk.CTkLabel(
            self.input_frame,
            text="Playlist URL:",
            font=ctk.CTkFont(size=14)
        )
        self.url_label.pack(side="left", padx=(10, 5))
        
        self.url_entry = ctk.CTkEntry(
            self.input_frame,
            width=500,
            placeholder_text="Enter Spotify playlist URL or ID"
        )
        self.url_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.url_entry.bind("<Return>", lambda e: self.load_playlist())
        
        self.load_button = ctk.CTkButton(
            self.input_frame,
            text="Load",
            command=self.load_playlist,
            width=100
        )
        self.load_button.pack(side="right", padx=10)
        
        # Playlist info section
        self.info_frame = ctk.CTkFrame(self.main_frame)
        self.info_frame.pack(fill="x", padx=20, pady=10)
        
        # Cover image (left)
        self.cover_frame = ctk.CTkFrame(self.info_frame, width=150, height=150)
        self.cover_frame.pack(side="left", padx=10, pady=10)
        self.cover_frame.pack_propagate(False)  # Keep fixed size
        
        self.cover_label = ctk.CTkLabel(self.cover_frame, text="")
        self.cover_label.pack(fill="both", expand=True)
        
        # Playlist details (right)
        self.details_frame = ctk.CTkFrame(self.info_frame)
        self.details_frame.pack(side="left", fill="both", expand=True, padx=10, pady=10)
        
        self.playlist_name_label = ctk.CTkLabel(
            self.details_frame,
            text="",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.playlist_name_label.pack(anchor="w", pady=(5, 0))
        
        self.playlist_owner_label = ctk.CTkLabel(
            self.details_frame,
            text="",
            font=ctk.CTkFont(size=14)
        )
        self.playlist_owner_label.pack(anchor="w")
        
        self.track_count_label = ctk.CTkLabel(
            self.details_frame,
            text="",
            font=ctk.CTkFont(size=14)
        )
        self.track_count_label.pack(anchor="w")
        
        # Tracks list section
        self.tracks_frame = ctk.CTkFrame(self.main_frame)
        self.tracks_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Column headers
        self.headers_frame = ctk.CTkFrame(self.tracks_frame)
        self.headers_frame.pack(fill="x", padx=5, pady=(5, 0))
        
        ctk.CTkLabel(
            self.headers_frame, 
            text="#", 
            width=40,
            font=ctk.CTkFont(weight="bold")
        ).pack(side="left", padx=(10, 5))
        
        ctk.CTkLabel(
            self.headers_frame, 
            text="Title", 
            width=300,
            anchor="w",
            font=ctk.CTkFont(weight="bold")
        ).pack(side="left", padx=5, fill="x", expand=True)
        
        ctk.CTkLabel(
            self.headers_frame, 
            text="Artist", 
            width=200,
            anchor="w",
            font=ctk.CTkFont(weight="bold")
        ).pack(side="left", padx=5)
        
        ctk.CTkLabel(
            self.headers_frame, 
            text="Album", 
            width=200,
            anchor="w",
            font=ctk.CTkFont(weight="bold")
        ).pack(side="left", padx=5)
        
        # Scrollable tracks list
        self.tracks_scrollable = ctk.CTkScrollableFrame(self.tracks_frame)
        self.tracks_scrollable.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Status bar
        self.status_frame = ctk.CTkFrame(self.main_frame, height=30)
        self.status_frame.pack(fill="x", padx=20, pady=(10, 0))
        
        self.status_label = ctk.CTkLabel(
            self.status_frame,
            text="Enter a Spotify playlist URL to view tracks",
            font=ctk.CTkFont(size=12)
        )
        self.status_label.pack(side="left", padx=10)
        
        # Set initial cover
        self.show_empty_cover()
    
    def load_playlist(self):
        """Load and display the playlist tracks"""
        # Get playlist URL from entry
        playlist_url = self.url_entry.get().strip()
        if not playlist_url:
            self.set_status("Please enter a Spotify playlist URL or ID")
            return
        
        # Clear existing tracks
        for widget in self.tracks_scrollable.winfo_children():
            widget.destroy()
        
        # Show loading status
        self.set_status("Loading playlist...")
        self.show_loading_cover()
        self.playlist_name_label.configure(text="Loading...")
        self.playlist_owner_label.configure(text="")
        self.track_count_label.configure(text="")
        
        # Extract playlist ID
        playlist_id = self.extract_playlist_id(playlist_url)
        if not playlist_id:
            self.set_status("Invalid playlist URL or ID")
            self.show_error_cover()
            return
        
        # Start thread to load playlist
        threading.Thread(
            target=self._load_playlist_thread,
            args=(playlist_id,),
            daemon=True
        ).start()
    
    def _load_playlist_thread(self, playlist_id):
        """Load playlist in a background thread"""
        try:
            # Get playlist info
            playlist_info = self.sp.playlist(playlist_id)
            
            # Get playlist details
            playlist_name = playlist_info['name']
            playlist_owner = playlist_info['owner']['display_name']
            total_tracks = playlist_info['tracks']['total']
            
            # Get cover image
            if playlist_info['images']:
                cover_url = playlist_info['images'][0]['url']
                threading.Thread(
                    target=self._load_cover_image,
                    args=(cover_url,),
                    daemon=True
                ).start()
            
            # Update UI with playlist info
            self.after(0, lambda: self.playlist_name_label.configure(text=playlist_name))
            self.after(0, lambda: self.playlist_owner_label.configure(text=f"By: {playlist_owner}"))
            self.after(0, lambda: self.track_count_label.configure(text=f"Tracks: {total_tracks}"))
            
            # Get all tracks
            tracks = []
            offset = 0
            limit = 100
            
            while True:
                self.after(0, lambda o=offset, t=total_tracks: self.set_status(f"Loading tracks... {min(o, t)}/{t}"))
                response = self.sp.playlist_items(
                    playlist_id, 
                    limit=limit, 
                    offset=offset,
                    fields="items(track(name,artists,album(name))),next"
                )
                
                # Add track items
                for item in response['items']:
                    track = item['track']
                    if track:  # Skip None tracks
                        tracks.append({
                            'name': track['name'],
                            'artists': ", ".join([artist['name'] for artist in track['artists']]),
                            'album': track['album']['name']
                        })
                
                # Check if we need to get more tracks
                if len(tracks) >= total_tracks or not response.get('next'):
                    break
                    
                offset += limit
            
            # Display tracks
            self.after(0, lambda: self._display_tracks(tracks))
            self.after(0, lambda t=len(tracks): self.set_status(f"Loaded {t} tracks"))
            
        except Exception as e:
            print(f"Error loading playlist: {e}")
            self.after(0, lambda e=str(e): self.set_status(f"Error: {e}"))
            self.after(0, self.show_error_cover)
    
    def _display_tracks(self, tracks):
        """Display tracks in the scrollable frame"""
        # Clear existing tracks first
        for widget in self.tracks_scrollable.winfo_children():
            widget.destroy()
        
        # Add each track as a row
        for i, track in enumerate(tracks, 1):
            # Create a frame for this track
            track_frame = ctk.CTkFrame(self.tracks_scrollable)
            track_frame.pack(fill="x", padx=5, pady=2)
            
            # Set background color alternating
            bg_color = "#2B2B2B" if i % 2 == 0 else None
            if bg_color:
                track_frame.configure(fg_color=bg_color)
            
            # Track number
            ctk.CTkLabel(
                track_frame, 
                text=str(i), 
                width=40
            ).pack(side="left", padx=(10, 5))
            
            # Track name
            ctk.CTkLabel(
                track_frame, 
                text=track['name'], 
                width=300,
                anchor="w"
            ).pack(side="left", padx=5, fill="x", expand=True)
            
            # Artist
            ctk.CTkLabel(
                track_frame, 
                text=track['artists'], 
                width=200,
                anchor="w"
            ).pack(side="left", padx=5)
            
            # Album
            ctk.CTkLabel(
                track_frame, 
                text=track['album'], 
                width=200,
                anchor="w"
            ).pack(side="left", padx=5)
    
    def _load_cover_image(self, url):
        """Load a cover image from URL"""
        try:
            # Check if image is already cached
            if url in self.image_cache:
                self.after(0, lambda: self._set_cover_image(self.image_cache[url]))
                return
                
            # Download image
            with urllib.request.urlopen(url) as response:
                image_data = response.read()
                
            # Process image
            img = Image.open(io.BytesIO(image_data))
            img = img.resize((130, 130), Image.LANCZOS)
            ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(130, 130))
            
            # Cache the image
            self.image_cache[url] = ctk_img
            
            # Set the image in the main thread
            self.after(0, lambda: self._set_cover_image(ctk_img))
        except Exception as e:
            print(f"Error loading cover image: {e}")
            self.after(0, self.show_error_cover)
    
    def _set_cover_image(self, ctk_img):
        """Set the cover image"""
        self.cover_label.configure(image=ctk_img, text="")
        self.cover_label.image = ctk_img  # Keep reference
    
    def show_loading_cover(self):
        """Show loading indicator in cover space"""
        self.cover_label.configure(image=None, text="⏳\nLoading...", fg_color="#FF9800")
    
    def show_empty_cover(self):
        """Show empty cover placeholder"""
        self.cover_label.configure(image=None, text="🎵", fg_color="#555555")
    
    def show_error_cover(self):
        """Show error cover"""
        self.cover_label.configure(image=None, text="❌\nError", fg_color="#F44336")
    
    def extract_playlist_id(self, url):
        """Extract playlist ID from URL or return the ID if already extracted"""
        # Check if it's already just an ID
        if re.match(r"^[a-zA-Z0-9]+$", url):
            return url
            
        # Check for Spotify URI format
        if url.startswith("spotify:playlist:"):
            return url.split(":")[-1]
            
        # Check for URL format
        match = re.search(r"playlist[/:]([a-zA-Z0-9]+)", url)
        if match:
            playlist_id = match.group(1)
            # Remove any query parameters
            playlist_id = playlist_id.split("?")[0]
            return playlist_id
            
        return None
    
    def set_status(self, message):
        """Set the status bar message"""
        self.status_label.configure(text=message)


def main():
    # Set customtkinter appearance
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    # Create and run the app
    app = PlaylistViewer()
    app.mainloop()

if __name__ == "__main__":
    main() 