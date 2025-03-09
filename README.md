Spotify Guessing Game
i am too lazy to make a readme myself so i used an AI

## Overview

The Spotify Guessing Game is a fun and engaging game where users guess song titles and artists from a playlist. Players can challenge themselves with multiple difficulty levels and modes, including Hard, Harder, and Harder Harder Modes. The game features a modern UI built with customtkinter.

## Features

### Dynamic Difficulty Levels:

- **Normal Mode**: Suggestions include partial matches.
- **Hard Mode**: Suggestions only if input is close to the correct answer.
- **Harder Mode**: Suggestions require exact song name.
- **Harder Harder Mode**: Suggestions require both song name and artist.

### Game Features:
- Beautiful modern UI using customtkinter
- Visual feedback for correct/incorrect guesses
- Playlist Options: Choose from your Spotify playlists, liked songs, or custom playlist URLs.
- Customizable Settings: Configure playback duration, max lives, and volume.
- Konami Code Easter Egg: Unlock configuration settings with a secret code.

## How to Play

1. Launch the game.
2. Select a playlist or enter a custom playlist URL.
3. Choose a game mode.
4. Guess the song playing within the time limit.
5. Review your performance in the summary screen.

## Installation

### Prerequisites
- Python 3.8+
- Spotify Developer Account
- Spotipy Library
- customtkinter Library
- Pillow Library

### Setup
1. Clone the repository:
```
git clone https://github.com/Fireboy086/0.1-guessr.git
```

2. Install dependencies:
```
pip install -r requirements.txt
```

3. Set up Spotify API credentials:
   - Visit Spotify Developer Dashboard.
   - Create a new app and note the Client ID and Client Secret.
   - Add a Redirect URI: http://localhost:8888/callback/.
   - Update the config.py file with your credentials or run the game to input them.

## Configuration

Customize gameplay settings using the Konami code (↑↑↓↓←→←→ba):

- **PLAYBACK_DURATION**: Duration of song playback in seconds.
- **MAX_GUESS_COUNT**: Maximum guesses allowed per song.
- **MAX_LIVES**: Number of lives in a game.
- **VOLUME_LEVEL**: Playback volume (0-100).

## Project Structure

```
.
├── main.py                 # Main entry point
├── app.py                  # Main application window
├── spotify_manager.py      # Handles Spotify API interactions
├── game_logic.py           # Core game logic
├── ui/                     # UI components
│   ├── screens/            # Game screens
│   │   ├── start_screen.py    # Playlist selection screen
│   │   ├── game_screen.py     # Main game screen
│   │   └── summary_screen.py  # End game summary
│   └── components/         # Reusable UI components
├── config.py               # Configuration settings
├── requirements.txt        # Project dependencies
└── README.md               # This file
```

## Troubleshooting

- **Error: No active Spotify device found**:
  Ensure Spotify is running on a device and logged in.

- **Invalid Playlist URL**:
  Check the format of the Spotify playlist URL.

- **Playback Restrictions**:
  Some tracks may be restricted. Skip to the next song in such cases.

## Contribution

Feel free to fork the repository and submit pull requests. Contributions are welcome!

## License

This project is licensed under the MIT License. See LICENSE for more details.
