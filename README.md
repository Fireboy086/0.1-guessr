Spotify Guessing Game
i am too lazy to make a readme myself so i used an AI


Overview


The Spotify Guessing Game is a fun and engaging game where users guess song titles and artists from a playlist. Players can challenge themselves with multiple difficulty levels and modes, including Hard, Harder, and Harder Harder Modes. The game features a dynamic point system to make gameplay exciting and competitive.


Features


Dynamic Difficulty Levels:


Normal Mode: Suggestions include partial matches.

Hard Mode: Suggestions only if input is close to the correct answer.

Harder Mode: Suggestions require exact song name.

Harder Harder Mode: Suggestions require both song name and artist.


Point System: Earn points based on accuracy, speed, and fewer mistakes.


Konami Code Easter Egg: Unlock configuration settings with a secret code.


Playlist Options: Choose from your Spotify playlists, liked songs, or custom playlist URLs.


Customizable Settings: Configure playback duration, max lives, and volume.


How to Play


Launch the game.

Select a playlist or enter a custom playlist URL.

Guess the song playing within the time limit.

Earn points for correct guesses and speed.

Track your progress and performance in the summary screen.


Installation


Prerequisites

Python 3.8+

Spotify Developer Account

Spotipy Library

Tkinter (pre-installed with Python on most systems)

Setup

Clone the repository:

git clone https://github.com/Fireboy086/0.1-guessr.git

Install dependencies:

pip install -r requirements.txt

Set up Spotify API credentials:

Visit Spotify Developer Dashboard.

Create a new app and note the Client ID and Client Secret.

Add a Redirect URI: http://localhost:8080.

Update the config.py file with your credentials.


Configuration


Customize gameplay settings in config.py:

PLAYBACK_DURATION: Duration of song playback in seconds.

MAX_GUESS_COUNT: Maximum guesses allowed per song.

MAX_LIVES: Number of lives in a game.

VOLUME_LEVEL: Playback volume (0-100).

HARD_MODE: Toggle for Hard Mode.

HARDER_MODE: Toggle for Harder Mode.

HARDER_HARDER_MODE: Toggle for Harder Harder Mode.


Point System

Correct Guess: Earn 10 points.

Fast Guess Bonus: Earn additional points for guessing within 5 seconds.

Lives Left Bonus: Earn points for unused lives at the end of the game.

Harder Modes: Higher difficulty modes yield more points per correct guess.

Troubleshooting

Error: No active Spotify device found:

Ensure Spotify is running on a device and logged in.

Invalid Playlist URL:

Check the format of the Spotify playlist URL.

Playback Restrictions:

Some tracks may be restricted. Skip to the next song in such cases.

Contribution

Feel free to fork the repository and submit pull requests. Contributions are welcome!

License

This project is licensed under the MIT License. See LICENSE for more details.
