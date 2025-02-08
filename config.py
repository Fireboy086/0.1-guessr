# config.py

# === Configurable Variables ===

CLIENT_ID = None
CLIENT_SECRET = None
REDIRECT_URI = "http://localhost:8888/callback/"
SCOPE = "user-library-read playlist-read-private user-read-playback-state user-modify-playback-state"

PLAYBACK_DURATION = 5  # Initial playback duration in seconds
WINDOW_TITLE = "Music Guessr"
FONT = ("Arial", 16)
BUTTON_PADDING = 10
BACKGROUND_COLOR = "#1E1E1E"  # Default background color
MAX_GUESS_COUNT = 3  # Maximum number of guesses per song
MAX_LIVES = 3  # Number of lives the player starts with
VOLUME_LEVEL = 50  # Default volume level (0-100)
MAX_REPLAYS = 5  # Maximum number of times a song can be replayed
GUESSING_RANGE = 2  # Maximum Levenshtein distance for partial matches
# =============================
