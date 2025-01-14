# config.py

# === Configurable Variables ===

CLIENT_ID = None
CLIENT_SECRET = None
REDIRECT_URI = "http://localhost:8888/callback/"
SCOPE = "user-read-playback-state user-modify-playback-state playlist-read-private user-library-read user-top-read user-read-recently-played"

PLAYBACK_DURATION = 0.5  # Initial playback duration in seconds
WINDOW_TITLE = "Spotify Guessing Game"
FONT = ("Arial", 16)
BUTTON_PADDING = 10
BACKGROUND_COLOR = "#323232"  # Default background color
MAX_GUESS_COUNT = 3  # Maximum number of guesses per song
MAX_LIVES = 3  # Number of lives the player starts with
VOLUME_LEVEL = 80  # Desired volume level (0-100)
# =============================
