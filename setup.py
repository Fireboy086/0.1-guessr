# setup.py

"""
Setup module for Spotify Guessing Game
Handles Spotify API credentials setup and loading
"""

import webbrowser
import os
import configparser
import sys
import customtkinter as ctk

def setup_spotify_credentials():
    """Guide the user to create Spotify API credentials and collect them."""
    # Create the dialog to collect credentials
    root = ctk.CTk()
    root.title("Spotify API Setup")
    root.geometry("600x600")
    root.resizable(False, False)
    
    frame = ctk.CTkFrame(root)
    frame.pack(fill="both", expand=True, padx=20, pady=20)
    
    # Title
    title_label = ctk.CTkLabel(
        frame, 
        text="Spotify API Credentials Setup", 
        font=ctk.CTkFont(size=20, weight="bold")
    )
    title_label.pack(pady=(0, 20))
    
    # Instructions
    instructions = """
    Please follow these steps to create your Spotify API credentials:
    
    1. Go to https://developer.spotify.com/dashboard/
    2. Log in with your Spotify account
    3. Click on 'Create an App'
    4. Give your app a name and description
    5. Agree to the terms and click 'Create'
    6. Once the app is created, click on 'Edit Settings'
    7. Add 'http://localhost:8888/callback/' to the Redirect URIs
    8. Click 'Save'
    9. Copy the 'Client ID' and 'Client Secret' from the dashboard
    """
    
    # Instructions textbox
    instructions_box = ctk.CTkTextbox(
        frame, 
        width=550, 
        height=200,
        font=ctk.CTkFont(size=14)
    )
    instructions_box.pack(pady=(0, 20), fill="x")
    instructions_box.insert("0.0", instructions)
    instructions_box.configure(state="disabled")
    
    # Open browser button
    browser_button = ctk.CTkButton(
        frame,
        text="Open Spotify Developer Dashboard",
        command=lambda: webbrowser.open("https://developer.spotify.com/dashboard/"),
        height=40,
        font=ctk.CTkFont(size=14)
    )
    browser_button.pack(pady=(0, 20))
    
    # Credentials input
    creds_frame = ctk.CTkFrame(frame)
    creds_frame.pack(fill="x", pady=10)
    
    # Client ID
    ctk.CTkLabel(
        creds_frame, 
        text="Client ID:", 
        font=ctk.CTkFont(size=14)
    ).grid(row=0, column=0, padx=10, pady=10, sticky="e")
    
    client_id_entry = ctk.CTkEntry(creds_frame, width=400)
    client_id_entry.grid(row=0, column=1, padx=10, pady=10, sticky="w")
    
    # Client Secret
    ctk.CTkLabel(
        creds_frame, 
        text="Client Secret:", 
        font=ctk.CTkFont(size=14)
    ).grid(row=1, column=0, padx=10, pady=10, sticky="e")
    
    client_secret_entry = ctk.CTkEntry(creds_frame, width=400)
    client_secret_entry.grid(row=1, column=1, padx=10, pady=10, sticky="w")
    
    # Status message
    status_var = ctk.StringVar(value="")
    status_label = ctk.CTkLabel(
        frame,
        textvariable=status_var,
        font=ctk.CTkFont(size=14),
        text_color=("red", "#FF5555")
    )
    status_label.pack(pady=10)
    
    # Function to save credentials
    def save_credentials():
        client_id = client_id_entry.get().strip()
        client_secret = client_secret_entry.get().strip()
        
        if not client_id or not client_secret:
            status_var.set("Please enter both Client ID and Client Secret")
            return
        
        # Save the credentials
        if save_to_file(client_id, client_secret):
            status_var.set("Credentials saved successfully!")
            status_label.configure(text_color=("green", "#55FF55"))
            root.after(1500, root.destroy)
        else:
            status_var.set("Error saving credentials. Please try again.")
    
    # Save button
    save_button = ctk.CTkButton(
        frame,
        text="Save Credentials",
        command=save_credentials,
        height=40,
        font=ctk.CTkFont(size=14)
    )
    save_button.pack(pady=10)
    
    # Open the window
    root.mainloop()

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
        return True
    except Exception as e:
        print(f"Error saving credentials: {e}")
        return False

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
