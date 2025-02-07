import configparser
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from config import *
from UI import StartScreen, GameScreen, SummaryScreen
from logic import GameLogic
import pygame
import sys

def initialize_spotify():
    config = configparser.ConfigParser()
    config.read('credentials.ini')
    client_id = config.get('SPOTIFY', 'CLIENT_ID')
    client_secret = config.get('SPOTIFY', 'CLIENT_SECRET')
    redirect_uri = config.get('SPOTIFY', 'REDIRECT_URI')
    
    return spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=client_id,
        client_secret=client_secret,
        redirect_uri=redirect_uri,
        scope=SCOPE
    ))

def main():
    # Initialize core components
    sp = initialize_spotify()
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
