import spotipy
from spotipy.oauth2 import SpotifyOAuth
import random
import tkinter as tk
from tkinter import ttk, messagebox
import re
import spotipy
from spotipy.oauth2 import SpotifyOAuth
from config import *
from load import *

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

        # Frame styling for a slightly nicer look
        self.main_frame = tk.Frame(master, bg=BACKGROUND_COLOR, bd=2, relief=tk.RIDGE)
        self.main_frame.pack(padx=20, pady=20)

        self.label = tk.Label(
            self.main_frame, 
            text="Choose a playlist to start the game:", 
            font=("Arial", 14, "bold"), 
            bg=BACKGROUND_COLOR, 
            fg="white"
        )
        self.label.pack(pady=BUTTON_PADDING)

        # Fetch user's playlists and extract names and IDs
        self.playlists = get_user_playlists()
        self.playlist_options = [playlist['name'] for playlist in self.playlists]
        self.playlist_ids = {playlist['name']: playlist['id'] for playlist in self.playlists}

        # Sort playlists alphabetically
        self.playlist_options.sort()

        # Add "Liked Songs" and the custom playlist option at the top
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

        self.custom_playlist_entry = tk.Entry(self.main_frame, font=FONT, width=50)
        self.custom_playlist_entry.pack(pady=BUTTON_PADDING)
        self.custom_playlist_entry.insert(0, "Enter Spotify Playlist URL here")
        self.custom_playlist_entry.bind("<FocusIn>", self.clear_entry)
        self.custom_playlist_entry.config(state='disabled')  # Disable until needed

        self.playlist_var.trace('w', self.on_playlist_select)

        self.start_button = tk.Button(
            self.main_frame, 
            text="Start Game", 
            command=self.start_game, 
            font=("Arial", 12, "bold"), 
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
        """Start the guessing game based on the selected playlist."""
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

        if not track_uris:
            messagebox.showerror("Error", "No tracks found in the selected playlist.")
            return

        self.master.destroy()
        root = tk.Tk()
        app = GuessingGame(root, track_uris, track_names, track_artists)
        root.mainloop()

# GUI for the guessing system
class GuessingGame:
    def __init__(self, master, track_uris, track_names, track_artists):
        self.master = master
        self.master.title(WINDOW_TITLE)
        self.master.config(bg=BACKGROUND_COLOR)

        # Data tracking
        self.track_uris = track_uris
        self.track_names = track_names
        self.track_artists = track_artists
        self.current_track = None
        self.correct_answer = None
        self.current_artist = None
        self.replay_count = 0
        self.current_play_time = PLAYBACK_DURATION  # Initial playback duration
        self.revealed_seconds = self.current_play_time
        self.guess_count = 0  # Initialize guess count
        self.guesses = []  # Store user's guesses
        self.played_songs = []  # Store all played songs and guesses
        self.lives = MAX_LIVES  # Initialize lives

        # Handle window closing event
        self.master.protocol("WM_DELETE_WINDOW", self.on_closing)

        # Main frame for the guessing game
        self.game_frame = tk.Frame(master, bg=BACKGROUND_COLOR, bd=2, relief=tk.RIDGE)
        self.game_frame.pack(padx=20, pady=20)

        # Label for instructions/status
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

        self.type_frame = tk.Frame(self.game_frame, bg=BACKGROUND_COLOR, bd=2, relief=tk.GROOVE)
        self.type_frame.pack(pady=BUTTON_PADDING)

        # Entry box
        self.entry = tk.Entry(self.type_frame, font=FONT, width=40)
        self.entry.pack(side=tk.LEFT, padx=5)
        self.entry.bind("<KeyRelease>", self.update_suggestions)
        self.entry.bind("<Return>", self.on_entry_return)  # Enter key
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
        self.suggestions.bind('<<ListboxSelect>>', self.on_suggestion_select)
        self.suggestions.bind("<Double-Button-1>", self.on_suggestion_double_click)
        self.suggestions.bind("<Return>", self.on_suggestion_return)
        self.suggestions.bind("<Up>", self.on_suggestion_key_press)
        self.suggestions.bind("<Down>", self.on_suggestion_key_press)

        self.entry.bind("<Up>", self.on_entry_up_down)
        self.entry.bind("<Down>", self.on_entry_up_down)

        # Control buttons frame
        self.buttons_frame = tk.Frame(self.game_frame, bg=BACKGROUND_COLOR, bd=2, relief=tk.RIDGE)
        self.buttons_frame.pack(pady=BUTTON_PADDING)

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
        self.konami_sequence = ['Up', 'Up', 'Down', 'Down', 'Left', 'Right', 'Left', 'Right', 'b', 'a']
        self.konami_index = 0  # Index to track progress

        self.master.bind('<KeyPress>', self.detect_konami_code)

        # Start the first random track
        self.play_random_track()

    # -------------------- KONAMI CODE -------------------- #
    def detect_konami_code(self, event):
        """Detect the Konami Code and open the configuration window."""
        key = event.keysym
        expected_key = self.konami_sequence[self.konami_index]

        # Normalize keys
        if key.lower() == expected_key.lower():
            self.konami_index += 1
            if self.konami_index == len(self.konami_sequence):
                self.konami_index = 0
                self.open_configuration_window()
        else:
            self.konami_index = 0  # reset if broken

    def open_configuration_window(self):
        """Open a window to change variables for testing."""
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
            label = tk.Label(config_window, text=label_text, font=FONT, bg=BACKGROUND_COLOR, fg="white")
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
        """Save the configuration changes."""
        global PLAYBACK_DURATION, MAX_GUESS_COUNT, MAX_LIVES, VOLUME_LEVEL

        try:
            PLAYBACK_DURATION = float(self.config_entries['PLAYBACK_DURATION'].get())
            MAX_GUESS_COUNT = int(self.config_entries['MAX_GUESS_COUNT'].get())
            MAX_LIVES = int(self.config_entries['MAX_LIVES'].get())
            VOLUME_LEVEL = int(self.config_entries['VOLUME_LEVEL'].get())

            # Update the game variables
            self.current_play_time = PLAYBACK_DURATION
            self.lives = MAX_LIVES
            self.lives_label.config(text=f"Lives: {self.lives}")
            messagebox.showinfo("Configuration", "Configuration updated successfully.")
        except ValueError:
            messagebox.showerror("Error", "Please enter valid values.")

    # -------------------- SPOTIFY HANDLING -------------------- #
    def get_active_device(self):
        """Check for an active Spotify device."""
        devices = sp.devices()
        if not devices['devices']:
            self.label.config(text="No active Spotify device found! Start Spotify on a device.")
            return None
        return devices['devices'][0]['id']

    def play_track(self, track_uri, start_time, duration, device_id):
        """Play the track for a given duration from a start time."""
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

        # Schedule pause
        self.master.after(int(duration * 1000), lambda: self.pause_playback(device_id))

    def pause_playback(self, device_id):
        """Pause playback on the specified device."""
        try:
            sp.pause_playback(device_id=device_id)
        except spotipy.exceptions.SpotifyException as e:
            print(f"Error pausing playback: {e}")

    # -------------------- GAME FLOW -------------------- #
    def play_random_track(self):
        """Select a random track and play."""
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
        self.current_track = self.track_uris.pop(random_index)
        self.correct_answer = self.track_names.pop(random_index)
        self.current_artist = self.track_artists.pop(random_index)

        device_id = self.get_active_device()
        if not device_id:
            self.label.config(text="No active Spotify device found! Start Spotify on a device.")
            return

        # Play
        self.play_track(self.current_track, 0, self.revealed_seconds, device_id)
        self.label.config(text="Guess the Song!")

    def replay_song(self):
        """Replay the current track, extending total play time by 0.5s each time."""
        if self.replay_count < 5:
            self.replay_count += 1
            self.revealed_seconds += PLAYBACK_DURATION
            device_id = self.get_active_device()
            if not device_id:
                self.label.config(text="No active Spotify device found! Start Spotify on a device.")
                return

            self.play_track(self.current_track, 0, self.revealed_seconds, device_id)

    # -------------------- AUTOCOMPLETE SUGGESTIONS -------------------- #
    def update_suggestions(self, event=None):
        """Update the suggestions listbox based on the user's input."""
        query = self.entry.get().strip().lower()
        self.suggestions.delete(0, tk.END)

        if not query:
            return

        # Build full song names
        full_names = list(set([
            f"{name} by {artist}"
            for name, artist in zip(
                self.track_names + [self.correct_answer],
                self.track_artists + [self.current_artist]
            )
        ]))

        # Filter matches
        matches = [full_name for full_name in full_names if query in full_name.lower()]

        for match in matches:
            self.suggestions.insert(tk.END, match)

        if matches:
            self.suggestions.selection_set(0)

    def on_suggestion_select(self, event):
        """Select suggestion."""
        selection = event.widget.curselection()
        if selection:
            index = selection[0]
            value = event.widget.get(index)
            self.entry.delete(0, tk.END)
            self.entry.insert(0, value)

    def on_suggestion_double_click(self, event):
        """Double-click to confirm guess."""
        self.on_suggestion_select(event)
        self.secure_guess()

    def on_suggestion_return(self, event):
        """Enter key in the suggestions list."""
        self.on_suggestion_select(event)
        self.secure_guess()

    def on_suggestion_key_press(self, event):
        """Navigate suggestions with up/down."""
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
        """Move focus to suggestions when pressing up/down."""
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
        """Enter key in the entry box."""
        if self.suggestions.size() > 0:
            self.suggestions.focus_set()
            self.suggestions.selection_set(0)
            self.suggestions.activate(0)
            self.on_suggestion_return(event)
        else:
            self.secure_guess()

    # -------------------- GUESS HANDLING -------------------- #
    def secure_guess(self, event=None):
        """Check if the user's guess is correct."""
        guess = self.entry.get().strip()
        if not guess:
            self.label.config(text="Please enter a guess!")
            return

        self.guesses.append(guess)

        correct_full = f"{self.correct_answer} by {self.current_artist}".lower()
        if guess.lower() == self.correct_answer.lower() or guess.lower() == correct_full:
            self.flash_feedback("green")
            self.label.config(text=f"Correct! The song was: {self.correct_answer} by {self.current_artist}")
            self.played_songs.append({
                'song': f"{self.correct_answer} by {self.current_artist}",
                'guesses': self.guesses.copy(),
                'result': 'Correct'
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
                    'result': 'Incorrect'
                })
                self.master.after(2000, self.play_random_track)
            else:
                guesses_left = MAX_GUESS_COUNT - self.guess_count
                self.label.config(text=f"Incorrect! {guesses_left} guesses left.")

        # Clear text box and suggestions
        self.entry.delete(0, tk.END)
        self.suggestions.delete(0, tk.END)
        self.entry.focus_set()

    def give_up(self):
        """Skip the current track."""
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
        """Flash the window background with a color."""
        original_color = self.master.cget('bg')
        self.master.config(bg=color)
        self.master.after(500, lambda: self.master.config(bg=original_color))

    # -------------------- EXIT & SUMMARY -------------------- #
    def on_closing(self):
        """When the window closes, show summary."""
        self.show_summary()

    def quit_game(self):
        """Quit the game and show summary."""
        self.show_summary()

    def show_summary_and_quit(self):
        """Show summary and end the game with no way back."""
        self.show_summary()

    def show_summary(self):
        """Show a summary of all played songs and guesses."""
        self.master.withdraw()

        summary_window = tk.Toplevel()
        summary_window.title("Game Summary")
        summary_window.config(bg=BACKGROUND_COLOR)

        summary_label = tk.Label(
            summary_window, 
            text="Game Summary", 
            font=("Arial", 20, "bold"), 
            bg=BACKGROUND_COLOR, 
            fg="#00FF00"
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
            song_label = tk.Label(
                scroll_frame, 
                text=f"{idx}. {song_info['song']} - {song_info['result']}", 
                font=FONT, 
                bg=BACKGROUND_COLOR, 
                fg="#FFD700"
            )
            song_label.pack(pady=(BUTTON_PADDING // 2, 0))

            guesses_label = tk.Label(
                scroll_frame, 
                text="Your Guesses:", 
                font=("Arial", 14, "underline"), 
                bg=BACKGROUND_COLOR, 
                fg="#ADFF2F"
            )
            guesses_label.pack()

            for guess in song_info['guesses']:
                guess_item = tk.Label(
                    scroll_frame, 
                    text=guess, 
                    font=("Arial", 12), 
                    bg=BACKGROUND_COLOR, 
                    fg="white"
                )
                guess_item.pack()

            separator = tk.Label(
                scroll_frame, 
                text="--------------------", 
                font=FONT, 
                bg=BACKGROUND_COLOR, 
                fg="#00CED1"
            )
            separator.pack()

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        exit_button = tk.Button(
            summary_window, 
            text="Exit", 
            command=self.force_quit, 
            font=FONT,
            bg="#F44336", 
            fg="black"
        )
        exit_button.pack(pady=BUTTON_PADDING)

        summary_window.protocol("WM_DELETE_WINDOW", self.force_quit)
        self.summary_window = summary_window

    def force_quit(self):
        """Exit the application."""
        if hasattr(self, 'summary_window'):
            self.summary_window.destroy()
        self.master.destroy()
        exit()

# Main program
if __name__ == "__main__":
    root = tk.Tk()
    app = PlaylistSelector(root)
    root.mainloop()
