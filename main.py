import configparser
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from config import *
from UI import StartScreen, GameScreen, SummaryScreen, CheersToSetupifyFileForLastingMeThatLongIWantItToBerememberedAsIsButNotForgottenInOurHeartsYouServedMeWellSetupify
from logic import GameLogic
import pygame
import sys

def validate_spotify_connection(sp):
    """Validate Spotify connection by attempting to get current user info."""
    try:
        user = sp.current_user()
        print(f"Successfully connected to Spotify as {user['display_name']}")
        return True
    except Exception as e:
        print("Error connecting to Spotify. Please check your credentials and try again.")
        print(f"Error details: {e}")
        return False

def initialize_spotify():
    config = configparser.ConfigParser()
    config.read('credentials.ini')
    
    try:
        client_id = config.get('SPOTIFY', 'CLIENT_ID')
        client_secret = config.get('SPOTIFY', 'CLIENT_SECRET')
        redirect_uri = config.get('SPOTIFY', 'REDIRECT_URI')
    except (configparser.NoSectionError, configparser.NoOptionError):
        return None
    
    return spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=SCOPE
    ))

def save_credentials(client_id, client_secret):
    config = configparser.ConfigParser()
    config['SPOTIFY'] = {
        'CLIENT_ID': client_id,
        'CLIENT_SECRET': client_secret,
        'REDIRECT_URI': 'http://localhost:8888/callback/'
    }
    with open('credentials.ini', 'w') as configfile:
        config.write(configfile)

def main():
    # Initialize Spotify
    sp = initialize_spotify()
    
    # If no valid credentials, show setup screen
    if sp is None or not validate_spotify_connection(sp):
        setup_screen = CheersToSetupifyFileForLastingMeThatLongIWantItToBerememberedAsIsButNotForgottenInOurHeartsYouServedMeWellSetupify()
        running = True
        
        while running:
            running, client_id, client_secret = setup_screen.update()
            setup_screen.draw()
            
            if client_id and client_secret:
                # Save the new credentials
                save_credentials(client_id, client_secret)
                
                # Try to initialize Spotify again with new credentials
                sp = initialize_spotify()
                if sp and validate_spotify_connection(sp):
                    break
                else:
                    # If validation fails, continue showing setup screen
                    setup_screen.show_error("Invalid credentials. Please try again.")
                    continue
            
            if not running:
                pygame.quit()
                sys.exit()
    
    game_logic = GameLogic(sp)
    clock = pygame.time.Clock()
    
    # Set up initial screen
    current_screen = StartScreen(game_logic)
    running = True
    
    # Main game loop
    while running:
        clock.tick(60)  # Limit to 60 FPS

        if isinstance(current_screen, StartScreen):
            running, next_screen = current_screen.update()
            if next_screen:
                current_screen = GameScreen(game_logic)
            current_screen.draw()

        elif isinstance(current_screen, GameScreen):
            running, next_screen = current_screen.update()
            if next_screen:
                current_screen = SummaryScreen(game_logic)
            current_screen.draw()

        elif isinstance(current_screen, SummaryScreen):
            running, _ = current_screen.update()
            current_screen.draw()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
