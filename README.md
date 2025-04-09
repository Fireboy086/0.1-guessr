# Spotify Guessing Game (CLI)

A command-line version of the Spotify song guessing game. Test your music knowledge by listening to song snippets and guessing the titles.

## Features

- CLI-based interface, no UI dependencies
- Connect to your Spotify account to access your playlists
- Four difficulty levels: Normal, Hard, Harder, and Expert
- Play with your own playlists, liked songs, or any Spotify playlist URL
- Test your musical knowledge in a fun and challenging way

## Requirements

- Python 3.6+
- Spotify Premium account
- Active Spotify device (phone, desktop app, web player, etc.)

## Installation

### Quick Install
1. Run the installation script:
   ```
   ./install.sh
   ```

### Manual Installation
1. Clone this repository
2. Install the required packages:
   ```
   pip install -r requirements.txt
   ```

## Setup

1. You'll need to create a Spotify Developer App to use this game
2. The first time you run the game, you'll be guided through this process
3. You'll need your Spotify Client ID and Client Secret, which you can get from the Spotify Developer Dashboard

## Usage

1. Run the game using one of these methods:
   ```
   # If you used the installation script
   ./spotify_guessr.py
   
   # Or using Python directly
   python3 spotify_guessr.py
   ```

2. Follow the on-screen instructions to:
   - Select a Spotify device for playback
   - Choose a playlist to play from
   - Select a difficulty level
   - Start guessing songs!

## Game Modes

- **Normal**: Partial matches and up to 2 errors allowed
- **Hard**: Close matches with up to 1 error allowed
- **Harder**: Exact title matches only
- **Expert**: Exact "title by artist" matches only

## Tips

- Make sure Spotify is open on a device before starting the game
- Higher difficulty modes require more precise guesses
- You can replay song snippets if you need another listen

## License

See the LICENSE file for details.
