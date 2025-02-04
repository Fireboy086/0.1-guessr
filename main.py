import spotipy
from spotipy.oauth2 import SpotifyOAuth
import random
import tkinter as tk
from tkinter import ttk, messagebox
import re
from config import *
from load import *

def levenshtein_distance(s1, s2):
    """
    Returns the Levenshtein distance between two strings s1 and s2.
    The distance is the number of edits (insertions, deletions, substitutions)
    required to transform s1 into s2.
    """
    if s1 == s2:
        return 0
    if len(s1) == 0:
        return len(s2)
    if len(s2) == 0:
        return len(s1)

    dp = [[0] * (len(s2) + 1) for _ in range(len(s1) + 1)]

    for i in range(len(s1) + 1):
        dp[i][0] = i
    for j in range(len(s2) + 1):
        dp[0][j] = j

    for i in range(1, len(s1) + 1):
        for j in range(1, len(s2) + 1):
            cost = 0 if s1[i - 1] == s2[j - 1] else 1
            dp[i][j] = min(
                dp[i - 1][j] + 1,     # deletion
                dp[i][j - 1] + 1,     # insertion
                dp[i - 1][j - 1] + cost  # substitution
            )
    return dp[len(s1)][len(s2)]

def get_all_playlist_tracks(playlist_id):
    """Fetch all tracks from the given playlist."""
    tracks = []
    limit = 100
    offset = 0

    while True:
        response = sp.playlist_items(playlist_id, limit=limit, offset=offset)
        tracks.extend(response['items'])
        if len(response['items']) < limit:
            break
        offset += limit

    # Extract track URIs, names, and artists
    track_uris = [item['track']['uri'] for item in tracks if item['track'] is not None]
    track_names = [item['track']['name'] for item in tracks if item['track'] is not None]
    track_artists = [item['track']['artists'][0]['name'] for item in tracks if item['track'] is not None]
    return track_uris, track_names, track_artists

def get_all_saved_tracks():
    """Fetch all tracks from the user's Liked Songs."""
    tracks = []
    limit = 50
    offset = 0

    while True:
        response = sp.current_user_saved_tracks(limit=limit, offset=offset)
        tracks.extend(response['items'])
        if len(response['items']) < limit:
            break
        offset += limit

    # Extract track URIs, names, and artists
    track_uris = [item['track']['uri'] for item in tracks if item['track'] is not None]
    track_names = [item['track']['name'] for item in tracks if item['track'] is not None]
    track_artists = [item['track']['artists'][0]['name'] for item in tracks if item['track'] is not None]
    return track_uris, track_names, track_artists

def get_user_playlists():
    """Fetch user's playlists."""
    playlists = []
    limit = 50
    offset = 0
    while True:
        response = sp.current_user_playlists(limit=limit, offset=offset)
        playlists.extend(response['items'])
        if len(response['items']) < limit:
            break
        offset += limit
    return playlists

class PlaylistSelector:
    def __init__(self, master):
        self.master = master
        self.master.title("Select a Playlist")
        self.master.config(bg=BACKGROUND_COLOR)

        self.main_frame = tk.Frame(master, bg=BACKGROUND_COLOR, bd=2, relief=tk.RIDGE)
        self.main_frame.pack(padx=20, pady=20)

        self.label = tk.Label(
            self.main_frame, 
            text="Choose a playlist to start the game:", 
            font=FONT, 
            bg=BACKGROUND_COLOR, 
            fg="white"
        )
        self.label.pack(pady=BUTTON_PADDING)

        # ----- Fetch user playlists -----
        self.playlists = get_user_playlists()
        self.playlist_options = [playlist['name'] for playlist in self.playlists]
        self.playlist_ids = {playlist['name']: playlist['id'] for playlist in self.playlists}

        # Sort playlists
        self.playlist_options.sort()

        # Add Liked Songs + Custom
        self.playlist_options.insert(0, "Liked Songs")
        self.playlist_options.insert(1, "Enter Custom Playlist URL")

        self.playlist_var = tk.StringVar(value=self.playlist_options[0])
        self.playlist_menu = ttk.Combobox(
            self.main_frame,
            textvariable=self.playlist_var,
            values=self.playlist_options,
            state="readonly",
            font=FONT
        )
        self.playlist_menu.pack(pady=BUTTON_PADDING)

        # ----- NEW: Mode Selection -----
        self.modes = ["Normal", "Hard", "Harder", "HarderHarder"]
        self.mode_var = tk.StringVar(value="Normal")  # Default

        self.mode_label = tk.Label(
            self.main_frame,
            text="Select Game Mode:",
            font=FONT,
            bg=BACKGROUND_COLOR,
            fg="white"
        )
        self.mode_label.pack(pady=(BUTTON_PADDING, 0))

        self.mode_menu = ttk.Combobox(
            self.main_frame,
            textvariable=self.mode_var,
            values=self.modes,
            state="readonly",
            font=FONT
        )
        self.mode_menu.pack(pady=BUTTON_PADDING)
        # --------------------------------

        # ----- Custom playlist entry (unchanged) -----
        self.custom_playlist_entry = tk.Entry(self.main_frame, font=FONT, width=50)
        self.custom_playlist_entry.pack(pady=BUTTON_PADDING)
        self.custom_playlist_entry.insert(0, "Enter Spotify Playlist URL here")
        self.custom_playlist_entry.bind("<FocusIn>", self.clear_entry)
        self.custom_playlist_entry.config(state='disabled')

        self.playlist_var.trace('w', self.on_playlist_select)

        self.start_button = tk.Button(
            self.main_frame, 
            text="Start Game",
            command=self.start_game,
            font=FONT,
            bg="#4CAF50",
            fg="black",
            relief=tk.RAISED
        )
        self.start_button.pack(pady=BUTTON_PADDING)

    def clear_entry(self, event):
        """Clear the placeholder text when the entry field gains focus."""
        current_text = self.custom_playlist_entry.get()
        if current_text == "Enter Spotify Playlist URL here":
            self.custom_playlist_entry.delete(0, tk.END)

    def on_playlist_select(self, *args):
        """Enable or disable the custom playlist entry based on selection."""
        selection = self.playlist_var.get()
        if selection == "Enter Custom Playlist URL":
            self.custom_playlist_entry.config(state='normal')
            self.custom_playlist_entry.focus_set()
        else:
            self.custom_playlist_entry.config(state='disabled')

    def start_game(self):
        """Start the guessing game based on the selected playlist and chosen mode."""
        selection = self.playlist_var.get()
        if selection in self.playlist_ids:
            playlist_id = self.playlist_ids[selection]
            track_uris, track_names, track_artists = get_all_playlist_tracks(playlist_id)
        elif selection == "Liked Songs":
            track_uris, track_names, track_artists = get_all_saved_tracks()
        elif selection == "Enter Custom Playlist URL":
            playlist_url = self.custom_playlist_entry.get()
            match = re.search(r"playlist/([a-zA-Z0-9]+)", playlist_url.split('?')[0])
            if match:
                playlist_id = match.group(1)
                track_uris, track_names, track_artists = get_all_playlist_tracks(playlist_id)
            else:
                messagebox.showerror("Error", "Invalid Spotify playlist URL.")
                return
        else:
            messagebox.showerror("Error", "Please select a valid playlist option.")
            return

        # Bail if no tracks found
        if not track_uris:
            messagebox.showerror("Error", "No tracks found in the selected playlist.")
            return

        # ----- Retrieve the selected mode -----
        selected_mode = self.mode_var.get()  # e.g., "Normal", "Hard", etc.
        # --------------------------------------

        # Close the selector window
        self.master.destroy()

        # Create and start the main game window, passing the selected mode
        root = tk.Tk()
        # Notice we pass `game_mode=selected_mode` to GuessingGame
        app = GuessingGame(root, track_uris, track_names, track_artists, game_mode=selected_mode)
        root.mainloop()


# GUI for the guessing system
class GuessingGame:
    def __init__(
        self, master,
        track_uris,
        track_names,
        track_artists,
        game_mode  # <-- Gamemodes are "Normal" "Hard" "Harder" "HarderHarder"
    ):
        self.master = master
        self.master.title(WINDOW_TITLE)
        self.master.config(bg=BACKGROUND_COLOR)

        # Create the main game frame first
        self.game_frame = tk.Frame(master, bg=BACKGROUND_COLOR)
        self.game_frame.pack(padx=20, pady=20)

        self.track_uris = track_uris
        self.track_names = track_names
        self.track_artists = track_artists
        self.current_track = None
        self.correct_answer = None
        self.current_artist = None
        self.replay_count = 0
        self.current_play_time = PLAYBACK_DURATION  # Initial playback duration
        self.revealed_seconds = self.current_play_time
        self.guess_count = 0
        self.guesses = []
        self.played_songs = []
        self.lives = MAX_LIVES
        self.game_mode = game_mode

        # ------------------ NEW: GAME MODE ------------------ #
        self.game_mode = game_mode  # "Normal", "Hard", "Harder", or "HarderHarder"

        # Handle window closing event
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

        # GUI Elements
        self.label = tk.Label(
            self.game_frame, 
            text="Guess the Song!", 
            font=("Arial", 16, "bold"), 
            bg=BACKGROUND_COLOR, 
            fg="white"
        )
        self.label.pack(pady=BUTTON_PADDING)

        self.lives_label = tk.Label(
            self.game_frame, 
            text=f"Lives: {self.lives}", 
            font=("Arial", 13), 
            bg=BACKGROUND_COLOR, 
            fg="white"
        )
        self.lives_label.pack(pady=BUTTON_PADDING)

        self.type_frame = tk.Frame(self.game_frame, bg=BACKGROUND_COLOR)
        self.type_frame.pack(pady=BUTTON_PADDING)

        # Entry box and suggestions
        self.entry = tk.Entry(self.type_frame, font=FONT, width=40)
        self.entry.pack(side=tk.LEFT, padx=5)
        self.entry.bind("<KeyRelease>", self.update_suggestions)
        self.entry.bind("<Return>", self.on_entry_return)
        self.entry.focus_set()

        # Suggestions listbox
        self.suggestions = tk.Listbox(
            self.type_frame, 
            font=FONT, 
            width=40, 
            height=5, 
            bg="#404040", 
            fg="white", 
            highlightbackground="#FFFF00", 
            highlightthickness=1, 
            selectbackground="#606060"
        )
        self.suggestions.pack(side=tk.LEFT, padx=5)

        # Corrected: only Listbox events call on_suggestion_select
        self.suggestions.bind('<<ListboxSelect>>', self.on_suggestion_select)
        self.suggestions.bind("<Double-Button-1>", self.on_suggestion_double_click)
        self.suggestions.bind("<Return>", self.on_suggestion_return)
        self.suggestions.bind("<Up>", self.on_suggestion_key_press)
        self.suggestions.bind("<Down>", self.on_suggestion_key_press)

        self.entry.bind("<Up>", self.on_entry_up_down)
        self.entry.bind("<Down>", self.on_entry_up_down)

        self.buttons_frame = tk.Frame(self.game_frame, bg=BACKGROUND_COLOR)
        self.buttons_frame.pack(pady=BUTTON_PADDING)

        # Control Buttons
        self.quit_button = tk.Button(
            self.buttons_frame, 
            text="Quit Game", 
            command=self.quit_game, 
            font=("Arial", 12, "bold"),
            bg="#F44336", 
            fg="black"
        )
        self.quit_button.pack(side=tk.LEFT, padx=5)

        self.show_summary_button = tk.Button(
            self.buttons_frame, 
            text="Show Summary", 
            command=self.show_summary_and_quit, 
            font=("Arial", 12, "bold"),
            bg="#FF9800", 
            fg="black"
        )
        self.show_summary_button.pack(side=tk.LEFT, padx=5)

        self.give_up_button = tk.Button(
            self.buttons_frame, 
            text="Give Up", 
            command=self.give_up, 
            font=("Arial", 12, "bold"),
            bg="#9C27B0", 
            fg="black"
        )
        self.give_up_button.pack(side=tk.LEFT, padx=5)

        self.replay_button = tk.Button(
            self.buttons_frame, 
            text="Replay 0.5s", 
            command=self.replay_song, 
            font=("Arial", 12, "bold"),
            bg="#2196F3", 
            fg="black"
        )
        self.replay_button.pack(side=tk.LEFT, padx=5)

        # Konami Code sequence
        self.konami_sequence = [
            'Up', 'Up', 'Down', 'Down', 'Left', 'Right', 'Left', 'Right', 'b', 'a'
        ]
        self.konami_index = 0  # Index to track progress in the Konami sequence

        self.master.bind('<KeyPress>', self.detect_konami_code)

        self.play_random_track()

    # -------------------- KONAMI CODE & CONFIG WINDOW -------------------- #
    def detect_konami_code(self, event):
        key = event.keysym
        expected_key = self.konami_sequence[self.konami_index]
        if key.lower() == expected_key.lower():
            self.konami_index += 1
            if self.konami_index == len(self.konami_sequence):
                self.konami_index = 0
                self.open_configuration_window()
        else:
            self.konami_index = 0

    def open_configuration_window(self):
        config_window = tk.Toplevel(self.master)
        config_window.title("Configuration")
        config_window.config(bg=BACKGROUND_COLOR)

        variables = {
            'PLAYBACK_DURATION': ('Playback Duration (seconds)', PLAYBACK_DURATION),
            'MAX_GUESS_COUNT': ('Max Guesses per Song', MAX_GUESS_COUNT),
            'MAX_LIVES': ('Max Lives', MAX_LIVES),
            'VOLUME_LEVEL': ('Volume Level (0-100)', VOLUME_LEVEL),
        }
        self.config_entries = {}
        for idx, (var_name, (label_text, default_value)) in enumerate(variables.items()):
            label = tk.Label(
                config_window, text=label_text, font=FONT, bg=BACKGROUND_COLOR, fg="white"
            )
            label.grid(row=idx, column=0, padx=10, pady=5, sticky='e')
            entry = tk.Entry(config_window, font=FONT)
            entry.insert(0, str(default_value))
            entry.grid(row=idx, column=1, padx=10, pady=5)
            self.config_entries[var_name] = entry

        save_button = tk.Button(
            config_window, 
            text="Save", 
            command=self.save_configuration, 
            font=FONT, 
            bg="#4CAF50", 
            fg="black"
        )
        save_button.grid(row=len(variables), column=0, columnspan=2, pady=BUTTON_PADDING)

    def save_configuration(self):
        global PLAYBACK_DURATION, MAX_GUESS_COUNT, MAX_LIVES, VOLUME_LEVEL
        try:
            PLAYBACK_DURATION = float(self.config_entries['PLAYBACK_DURATION'].get())
            MAX_GUESS_COUNT = int(self.config_entries['MAX_GUESS_COUNT'].get())
            MAX_LIVES = int(self.config_entries['MAX_LIVES'].get())
            VOLUME_LEVEL = int(self.config_entries['VOLUME_LEVEL'].get())

            self.current_play_time = PLAYBACK_DURATION
            self.lives = MAX_LIVES
            self.lives_label.config(text=f"Lives: {self.lives}")
            messagebox.showinfo("Configuration", "Configuration updated successfully.")
        except ValueError:
            messagebox.showerror("Error", "Please enter valid values.")

    # -------------------- SPOTIFY DEVICE & PLAYBACK -------------------- #
    def get_active_device(self):
        devices = sp.devices()
        if not devices['devices']:
            self.label.config(text="No active Spotify device found! Start Spotify on a device.")
            return None
        return devices['devices'][0]['id']

    def play_track(self, track_uri, start_time, duration, device_id):
        if not device_id:
            print("No active device available for playback.")
            return

        # Set volume
        try:
            sp.volume(VOLUME_LEVEL, device_id)
        except spotipy.exceptions.SpotifyException as e:
            print(f"Error setting volume: {e}")

        # Start playback
        try:
            sp.start_playback(device_id=device_id, uris=[track_uri], position_ms=int(start_time * 1000))
        except spotipy.exceptions.SpotifyException as e:
            print(f"Error starting playback: {e}")
            self.label.config(text="Error playing track. Skipping to next.")
            self.master.after(2000, self.play_random_track)
            return

        self.master.after(int(duration * 1000), lambda: self.pause_playback(device_id))

    def pause_playback(self, device_id):
        try:
            sp.pause_playback(device_id=device_id)
        except spotipy.exceptions.SpotifyException as e:
            print(f"Error pausing playback: {e}")

    # -------------------- MAIN GAME FLOW -------------------- #
    def play_random_track(self):
        if self.lives <= 0:
            self.label.config(text="Game Over! You're out of lives.")
            self.show_summary()
            return
        if len(self.track_uris) == 0:
            self.label.config(text="No more songs in the playlist.")
            self.show_summary()
            return

        self.replay_count = 0
        self.current_play_time = PLAYBACK_DURATION
        self.revealed_seconds = self.current_play_time
        self.guess_count = 0
        self.guesses = []

        random_index = random.randint(0, len(self.track_uris) - 1)
        
        #if we want to remove the track from the list after it's been used
        
        # self.current_track = self.track_uris.pop(random_index)
        # self.correct_answer = self.track_names.pop(random_index)
        # self.current_artist = self.track_artists.pop(random_index)
        
        """Shuffle mode"""
        
        self.current_track = self.track_uris[random_index]
        self.correct_answer = self.track_names[random_index]
        self.current_artist = self.track_artists[random_index]

        device_id = self.get_active_device()
        if not device_id:
            self.label.config(text="No active Spotify device found! Start Spotify on a device.")
            return

        self.play_track(self.current_track, 0, self.current_play_time, device_id)
        self.label.config(text=f"Guess the Song! (Mode: {self.game_mode})")

    def replay_song(self):
        if self.replay_count < 5:
            self.replay_count += 1
            self.revealed_seconds += PLAYBACK_DURATION
            device_id = self.get_active_device()
            if not device_id:
                self.label.config(text="No active Spotify device found! Start Spotify on a device.")
                return
            self.play_track(self.current_track, 0, self.revealed_seconds, device_id)

    # -------------------- MODE-BASED SUGGESTIONS -------------------- #
    def update_suggestions(self, event=None):
        """Update autocomplete suggestions based on user input and the current game mode."""
        query = self.entry.get().strip().lower()
        self.suggestions.delete(0, tk.END)

        if not query:
            return

        # Build a list of possible "song by artist" combos
        all_full_names = list(set([
            f"{name} by {artist}"
            for name, artist in zip(
                self.track_names + [self.correct_answer],
                self.track_artists + [self.current_artist]
            )
        ]))

        # Filter them according to the current mode logic
        matched = self.get_mode_based_suggestions(query, all_full_names)

        for match in matched:
            self.suggestions.insert(tk.END, match)
        if matched:
            self.suggestions.selection_set(0)

    def get_mode_based_suggestions(self, query, options):
        """
        Return suggestions based on the game mode:

        Normal Mode:
          - Show partial matches, including artist names
          - Levenshtein distance <= 2 is allowed for matching

        Hard Mode:
          - Suggestions appear only if:
             there's one clear match OR
             the song name is exactly correct (<= 1 error).
          - Could also show if the user typed exactly (with <=1 error in the title).

        Harder Mode:
          - Only exact song name match (no corrections allowed).

        Harder Harder Mode:
          - Exact "title by artist" match (no corrections).
        """
        results = []

        def title_of(s):
            return s.lower().split(" by ")[0]

        if self.game_mode == "Normal":
            for item in options:
                item_lower = item.lower()
                # If query is a substring or within Levenshtein distance <= 2
                if (query in item_lower) or (levenshtein_distance(query, item_lower) <= 2):
                    results.append(item)

        elif self.game_mode == "Hard":
            # 1) If there's exactly one partial match for 'query', show that
            subset = [x for x in options if query in x.lower()]
            if len(subset) == 1:
                results.append(subset[0])
            # 2) If the user typed the song name with <=1 error, show it
            for item in options:
                dist = levenshtein_distance(query, title_of(item))
                if dist <= 1 or query == title_of(item):
                    results.append(item)

        elif self.game_mode == "Harder":
            # Only show if the exact song name matches with no corrections
            for item in options:
                if title_of(item) == query:
                    results.append(item)

        elif self.game_mode == "HarderHarder":
            # Only show if "title by artist" is an exact match
            for item in options:
                if item.lower() == query:
                    results.append(item)

        return list(set(results))

    # -------------------- SUGGESTION/ENTRY EVENTS -------------------- #
    def on_suggestion_select(self, event):
        """
        Fill the entry box with the selected suggestion ONLY if the event
        comes from the suggestions Listbox.
        """
        if event.widget != self.suggestions:
            return  # Prevent error if somehow triggered from another widget

        selection = self.suggestions.curselection()
        if selection:
            index = selection[0]
            value = self.suggestions.get(index)
            self.entry.delete(0, tk.END)
            self.entry.insert(0, value)

    def on_suggestion_double_click(self, event):
        """Submit guess when double-click on the suggestion."""
        if event.widget != self.suggestions:
            return
        self.on_suggestion_select(event)
        self.secure_guess()

    def on_suggestion_return(self, event):
        """Submit guess when Enter is pressed in the suggestions list."""
        if event.widget != self.suggestions:
            return
        self.on_suggestion_select(event)
        self.secure_guess()

    def on_suggestion_key_press(self, event):
        """Handle up/down arrow keys in suggestions listbox."""
        if event.keysym == "Up":
            if self.suggestions.curselection():
                index = self.suggestions.curselection()[0]
                if index > 0:
                    self.suggestions.selection_clear(index)
                    self.suggestions.selection_set(index - 1)
                    self.suggestions.see(index - 1)
        elif event.keysym == "Down":
            if self.suggestions.curselection():
                index = self.suggestions.curselection()[0]
                if index < self.suggestions.size() - 1:
                    self.suggestions.selection_clear(index)
                    self.suggestions.selection_set(index + 1)
                    self.suggestions.see(index + 1)

    def on_entry_up_down(self, event):
        """Move focus to suggestions list when Up/Down is pressed in the entry."""
        if event.keysym == "Down":
            self.suggestions.focus_set()
            if self.suggestions.size() > 0:
                self.suggestions.selection_set(0)
                self.suggestions.activate(0)
        elif event.keysym == "Up":
            self.suggestions.focus_set()
            if self.suggestions.size() > 0:
                last_index = self.suggestions.size() - 1
                self.suggestions.selection_set(last_index)
                self.suggestions.activate(last_index)

    def on_entry_return(self, event):
        """
        Submit the guess when Enter is pressed in the entry.
        If suggestions exist, we focus the listbox first to allow selecting.
        """
        if self.suggestions.size() > 0:
            self.suggestions.focus_set()
            self.suggestions.selection_set(0)
            self.suggestions.activate(0)
            self.on_suggestion_return(event)
        else:
            self.secure_guess()

    # -------------------- GUESS CHECKING -------------------- #
    def secure_guess(self, event=None):
        guess = self.entry.get().strip()
        if not guess:
            self.label.config(text="Please enter a guess!")
            return

        self.guesses.append(guess)
        correct_full_lower = f"{self.correct_answer} by {self.current_artist}".lower()
        correct_full = f"{self.correct_answer} by {self.current_artist}"
        guess_lower = guess.lower()

        # Evaluate correctness based on self.game_mode
        if self.is_correct_guess(guess_lower,guess, correct_full_lower, correct_full):
            self.flash_feedback("green")
            self.label.config(text=f"Correct! The song was: {self.correct_answer} by {self.current_artist}")
            self.played_songs.append({
                'song': f"{self.correct_answer} by {self.current_artist}",
                'guesses': self.guesses.copy(),
                'result': 'Correct',
                'time_revealed': self.revealed_seconds
            })
            self.master.after(1000, self.play_random_track)
        else:
            self.flash_feedback("red")
            self.guess_count += 1
            if self.guess_count >= MAX_GUESS_COUNT:
                self.lives -= 1
                self.lives_label.config(text=f"Lives: {self.lives}")
                self.label.config(text=f"Out of guesses! The song was: {self.correct_answer} by {self.current_artist}")
                self.played_songs.append({
                    'song': f"{self.correct_answer} by {self.current_artist}",
                    'guesses': self.guesses.copy(),
                    'result': 'Incorrect',
                    'time_revealed': self.revealed_seconds
                })
                self.master.after(2000, self.play_random_track)
            else:
                left = MAX_GUESS_COUNT - self.guess_count
                self.label.config(text=f"Incorrect! {left} guesses left.")

        # Clear entry & suggestions
        self.entry.delete(0, tk.END)
        self.suggestions.delete(0, tk.END)
        self.entry.focus_set()

    def is_correct_guess(self, guess_lower, guess, correct_full_lower, correct_full):
        """
        Check correctness differently for each mode.
        We compare 'title' alone or 'title by artist' depending on mode.
        """
        title_only = self.correct_answer.lower()

        if self.game_mode == "HarderHarder":
            # exact match on "title by artist"
            return guess == correct_full

        elif self.game_mode == "Harder":
            # exact match on title or "title by artist"
            return guess_lower == title_only or guess_lower == correct_full_lower or guess == correct_full

        elif self.game_mode == "Hard":
            # allow <= 1 error in the title
            if levenshtein_distance(guess, title_only) <= 1:
                return True
            # or exact match with "title by artist"
            if guess_lower == correct_full_lower:
                return True
            return False

        else:  # Normal mode
            # allow <= 2 errors in either "title" or "title by artist"
            dist_title = levenshtein_distance(guess_lower, title_only)
            dist_full = levenshtein_distance(guess_lower, correct_full_lower)
            if dist_title <= 2 or dist_full <= 2:
                return True
            return False

    # -------------------- GIVE UP & FLASH FEEDBACK -------------------- #
    def give_up(self):
        self.lives -= 1
        self.lives_label.config(text=f"Lives: {self.lives}")
        self.label.config(text=f"Skipping... The song was: {self.correct_answer} by {self.current_artist}")
        self.played_songs.append({
            'song': f"{self.correct_answer} by {self.current_artist}",
            'guesses': self.guesses.copy(),
            'result': 'Skipped'
        })
        self.master.after(2000, self.play_random_track)

    def flash_feedback(self, color):
        original_color = self.master.cget('bg')
        self.master.config(bg=color)
        self.master.after(500, lambda: self.master.config(bg=original_color))

    # -------------------- EXIT & SUMMARY -------------------- #
    def on_closing(self):
        self.master.destroy()

    def quit_game(self):
        self.master.destroy()

    def show_summary_and_quit(self):
        self.show_summary()

    def show_summary(self):
        self.master.withdraw()
        summary_window = tk.Toplevel()
        summary_window.title("Game Summary")
        summary_window.config(bg=BACKGROUND_COLOR)
        
        # Set initial window size
        summary_window.geometry("600x1000")
        
        summary_label = tk.Label(
            summary_window, text="Game Summary", font=("Arial", 20, "bold"),
            bg=BACKGROUND_COLOR, fg="#00FF00"
        )
        summary_label.pack(pady=BUTTON_PADDING)

        canvas = tk.Canvas(summary_window, bg=BACKGROUND_COLOR, highlightthickness=0)
        scrollbar = tk.Scrollbar(summary_window, orient="vertical", command=canvas.yview)
        scroll_frame = tk.Frame(canvas, bg=BACKGROUND_COLOR)

        scroll_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scroll_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        for idx, song_info in enumerate(self.played_songs, start=1):
            if song_info['result'] == "Incorrect":
                label_color = "#FF4449"
            elif song_info['result'] == "Skipped":
                label_color = "#FFBD16"
            else:
                label_color = "#69FFAA"
            song_label = tk.Label(
                scroll_frame,
                text=f"{idx}. {song_info['song']} - {song_info['result']}",
                font=FONT, bg=BACKGROUND_COLOR, fg=label_color
            )
            song_label.pack(pady=(BUTTON_PADDING // 2, 0))
            
            if song_info['guesses']:
                guesses_label = tk.Label(
                    scroll_frame, text="Your Guesses:",
                    font=("Arial", 14, "underline"), bg=BACKGROUND_COLOR, fg="#ADFF2F"
                )
                guesses_label.pack()

                for guess in song_info['guesses']:
                    guess_item = tk.Label(
                        scroll_frame, text=guess, font=("Arial", 12),
                        bg=BACKGROUND_COLOR, fg="white"
                    )
                    guess_item.pack()
                
                time_revealed_label = tk.Label(
                    scroll_frame, text=f"Time Revealed: {song_info['time_revealed']} seconds",
                    font=FONT, bg=BACKGROUND_COLOR, fg="white"
                )
                time_revealed_label.pack()

            separator = tk.Label(
                scroll_frame, text="--------------------",
                font=FONT, bg=BACKGROUND_COLOR, fg="#00CED1"
            )
            separator.pack()

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        exit_button = tk.Button(
            summary_window, text="Exit", command=self.force_quit,
            font=FONT
        )
        exit_button.pack(pady=BUTTON_PADDING)

        summary_window.protocol("WM_DELETE_WINDOW", self.force_quit)
        self.summary_window = summary_window

    def force_quit(self):
        if hasattr(self, 'summary_window'):
            self.summary_window.destroy()
        self.master.destroy()
        exit()

# Main program
if __name__ == "__main__":
    root = tk.Tk()
    root.attributes("-topmost", True)
    app = PlaylistSelector(root)
    root.mainloop()
