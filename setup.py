# setup.py

import webbrowser
import tkinter as tk
from tkinter import messagebox
import os
import configparser

def setup_spotify_credentials():
    """Guide the user to create Spotify API credentials and collect them."""
    print("Spotify API credentials are required to run this application.")
    print("Please follow the instructions to create your own Spotify API credentials.")
    print("1. Go to https://developer.spotify.com/dashboard/")
    print("2. Log in with your Spotify account.")
    print("3. Click on 'Create an App'.")
    print("4. Give your app a name and description.")
    print("5. Agree to the terms and click 'Create'.")
    print("6. Once the app is created, click on 'Edit Settings'.")
    print("7. Add 'http://localhost:8888/callback/' to the Redirect URIs and click 'Add'.")
    print("8. Click 'Save'.")
    print("9. Copy the 'Client ID' and 'Client Secret' from the app's dashboard.")

    # Open the Spotify Developer Dashboard in the default web browser
    webbrowser.open("https://developer.spotify.com/dashboard/")

    # Prompt the user to enter the CLIENT_ID and CLIENT_SECRET
    client_id = input("Enter your Spotify Client ID: ").strip()
    client_secret = input("Enter your Spotify Client Secret: ").strip()

    # Save the credentials to a configuration file
    config = configparser.ConfigParser()
    config['SPOTIFY'] = {
        'CLIENT_ID': client_id,
        'CLIENT_SECRET': client_secret,
        'REDIRECT_URI': 'http://localhost:8888/callback/'
    }

    with open('credentials.ini', 'w') as configfile:
        config.write(configfile)

    print("Credentials saved successfully.")

def load_spotify_credentials():
    """Load Spotify API credentials from the configuration file."""
    if not os.path.exists('credentials.ini'):
        return None, None, None

    config = configparser.ConfigParser()
    config.read('credentials.ini')

    if 'SPOTIFY' in config:
        client_id = config['SPOTIFY'].get('CLIENT_ID')
        client_secret = config['SPOTIFY'].get('CLIENT_SECRET')
        redirect_uri = config['SPOTIFY'].get('REDIRECT_URI', 'http://localhost:8888/callback/')
        return client_id, client_secret, redirect_uri
    else:
        return None, None, None
