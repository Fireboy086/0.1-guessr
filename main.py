"""
Spotify Guessing Game - Main Entry Point
"""
import os
import sys
import customtkinter as ctk
from app import SpotifyGuessingGameApp
from setup import load_spotify_credentials, setup_spotify_credentials
from config import *

def main():
    # Set customtkinter appearance
    ctk.set_appearance_mode("dark")
    ctk.set_default_color_theme("blue")
    
    # Load Spotify credentials
    client_id, client_secret, redirect_uri = load_spotify_credentials()
    
    if not client_id or not client_secret:
        # Credentials are missing; initiate setup
        setup_spotify_credentials()
        # Reload credentials after setup
        client_id, client_secret, redirect_uri = load_spotify_credentials()
        if not client_id or not client_secret:
            print("Spotify credentials are required to run the application.")
            sys.exit(1)
    
    # Start the app - pass credentials to the app
    app = SpotifyGuessingGameApp(client_id, client_secret, redirect_uri)
    app.mainloop()

if __name__ == "__main__":
    main()
