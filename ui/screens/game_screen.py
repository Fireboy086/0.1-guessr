"""
Game Screen - Main game screen where the guessing happens
"""
import random
import time
import customtkinter as ctk
from config import *
from game_logic import levenshtein_distance

class GameScreen(ctk.CTkFrame):
    """Main game screen for the Spotify Guessing Game"""
    
    def __init__(self, parent, game_logic, spotify_manager, track_uris, track_names, track_artists, game_mode, game_settings=None):
        super().__init__(parent, corner_radius=10, fg_color="transparent")
        self.parent = parent
        self.game_logic = game_logic
        self.spotify_manager = spotify_manager
        
        # Game state
        self.track_uris = track_uris
        self.track_names = track_names
        self.track_artists = track_artists
        self.game_mode = game_mode
        self.current_track = None
        self.correct_answer = None
        self.current_artist = None
        self.replay_count = 0
        self.current_play_time = PLAYBACK_DURATION
        self.revealed_seconds = PLAYBACK_DURATION
        self.guess_count = 0
        self.lives = MAX_LIVES
        self.guesses = []
        self.played_songs = []
        
        # Game settings
        self.game_settings = game_settings or {}
        self.show_answers = self.game_settings.get('show_answers', False)
        self.infinite_lives = self.game_settings.get('infinite_lives', False)
        self.skip_verification = self.game_settings.get('skip_verification', False)
        
        # Suggestion list state
        self.suggestion_buttons = []
        self.current_suggestion_index = -1  # Currently selected suggestion
        
        # Create UI
        self.create_widgets()
        
        # Set up animation variables
        self.feedback_color = None
        self.feedback_time = 0
        self.feedback_duration = 500  # ms
        self.song_info_visible = False
        self.song_info_time = 0
        self.song_info_duration = 3000  # ms
        
        # Default frame color (for resetting after feedback)
        self.default_fg_color = "transparent"
        
        # Start update loop
        self.update_loop()
    
    def create_widgets(self):
        """Create the UI elements"""
        # Header frame
        self.header_frame = ctk.CTkFrame(self)
        self.header_frame.pack(fill="x", padx=20, pady=(20, 0))
        
        # Title
        self.title_label = ctk.CTkLabel(
            self.header_frame,
            text=f"Guess the Song! (Mode: {self.game_mode})",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.title_label.pack(pady=10)
        
        # Lives counter with infinite indicator if enabled
        lives_text = "Lives: ∞" if self.infinite_lives else f"Lives: {self.lives}"
        self.lives_label = ctk.CTkLabel(
            self.header_frame,
            text=lives_text,
            font=ctk.CTkFont(size=16)
        )
        self.lives_label.pack(pady=(0, 10))
        
        # Debug mode indicator
        if self.show_answers:
            self.debug_frame = ctk.CTkFrame(self, fg_color="#FF5733")
            self.debug_frame.pack(fill="x", padx=20, pady=(0, 10))
            
            self.debug_label = ctk.CTkLabel(
                self.debug_frame,
                text="DEBUG MODE: Answers will be shown",
                font=ctk.CTkFont(size=14, weight="bold"),
                text_color="white"
            )
            self.debug_label.pack(pady=5)
        
        # Song info frame (hidden initially)
        self.song_info_frame = ctk.CTkFrame(self)
        self.song_info_frame.pack(fill="x", padx=20, pady=10)
        self.song_info_frame.pack_forget()  # Hide initially
        
        self.song_info_label = ctk.CTkLabel(
            self.song_info_frame,
            text="",
            font=ctk.CTkFont(size=16)
        )
        self.song_info_label.pack(pady=10)
        
        # Input frame
        self.input_frame = ctk.CTkFrame(self)
        self.input_frame.pack(fill="x", padx=20, pady=10)
        
        # Search frame (entry + suggestions)
        self.search_frame = ctk.CTkFrame(self.input_frame)
        self.search_frame.pack(fill="x", padx=10, pady=10)
        
        # Entry field
        self.entry = ctk.CTkEntry(
            self.search_frame,
            width=500,
            height=40,
            placeholder_text="Type your guess here...",
            font=ctk.CTkFont(size=16)
        )
        self.entry.pack(side="top", fill="x", padx=10, pady=(10, 5))
        self.entry.bind("<KeyRelease>", self.update_suggestions)
        self.entry.bind("<Return>", self.on_entry_return)
        self.entry.bind("<Up>", self.on_entry_up_down)
        self.entry.bind("<Down>", self.on_entry_up_down)
        
        # Suggestions list
        self.suggestions_frame = ctk.CTkFrame(self.search_frame)
        self.suggestions_frame.pack(fill="x", padx=10, pady=(0, 10))
        
        self.suggestions_listbox = ctk.CTkScrollableFrame(
            self.suggestions_frame,
            height=150
        )
        self.suggestions_listbox.pack(fill="x", expand=True)
        
        # Controls frame
        self.controls_frame = ctk.CTkFrame(self)
        self.controls_frame.pack(fill="x", padx=20, pady=10)
        
        # Buttons
        self.buttons_frame = ctk.CTkFrame(self.controls_frame)
        self.buttons_frame.pack(fill="x", padx=10, pady=10)
        
        # Configure a 4-column layout for buttons
        self.buttons_frame.columnconfigure(0, weight=1)
        self.buttons_frame.columnconfigure(1, weight=1)
        self.buttons_frame.columnconfigure(2, weight=1)
        self.buttons_frame.columnconfigure(3, weight=1)
        
        # Replay button
        self.replay_button = ctk.CTkButton(
            self.buttons_frame,
            text="Replay 0.5s",
            command=self._on_replay_button_click,
            width=120,
            height=35,
            font=ctk.CTkFont(size=14),
            fg_color="#2196F3",
            hover_color="#1976D2"
        )
        self.replay_button.grid(row=0, column=0, padx=10, pady=10)
        
        # Give up button
        self.give_up_button = ctk.CTkButton(
            self.buttons_frame,
            text="Give Up",
            command=self._on_give_up_button_click,
            width=120,
            height=35,
            font=ctk.CTkFont(size=14),
            fg_color="#9C27B0",
            hover_color="#7B1FA2"
        )
        self.give_up_button.grid(row=0, column=1, padx=10, pady=10)
        
        # Summary button
        self.summary_button = ctk.CTkButton(
            self.buttons_frame,
            text="Show Summary",
            command=self._on_summary_button_click,
            width=120,
            height=35,
            font=ctk.CTkFont(size=14),
            fg_color="#FF9800",
            hover_color="#F57C00"
        )
        self.summary_button.grid(row=0, column=2, padx=10, pady=10)
        
        # Quit button
        self.quit_button = ctk.CTkButton(
            self.buttons_frame,
            text="Quit Game",
            command=self._on_quit_button_click,
            width=120,
            height=35,
            font=ctk.CTkFont(size=14),
            fg_color="#F44336",
            hover_color="#D32F2F"
        )
        self.quit_button.grid(row=0, column=3, padx=10, pady=10)
        
        # Focus the entry
        self.entry.focus_set()
    
    def update_loop(self):
        """Main update loop for animations"""
        try:
            current_time = int(time.time() * 1000)  # Current time in ms
            
            # Update feedback animation
            if self.feedback_color:
                elapsed = current_time - self.feedback_time
                if elapsed > self.feedback_duration:
                    self.feedback_color = None
                    self.configure(fg_color=self.default_fg_color)  # Use default color
                else:
                    # Make it fade out
                    alpha = 1.0 - (elapsed / self.feedback_duration)
                    self.configure(fg_color=self.get_fade_color(self.feedback_color, alpha))
            
            # Update song info visibility
            if self.song_info_visible:
                elapsed = current_time - self.song_info_time
                if elapsed > self.song_info_duration:
                    self.song_info_visible = False
                    self.song_info_frame.pack_forget()
            
            # Schedule next update - reduce frequency to 30 FPS to improve responsiveness
            self.after(33, self.update_loop)  # ~30 FPS
        except Exception as e:
            print(f"Error in update loop: {e}")
            # Ensure we keep calling the update loop even if there's an error
            self.after(33, self.update_loop)
    
    def get_fade_color(self, color, alpha):
        """Fade a color toward the background color"""
        if color == "green":
            return f"#{int(76*alpha):02x}{int(175*alpha):02x}{int(80*alpha):02x}"
        elif color == "red":
            return f"#{int(244*alpha):02x}{int(67*alpha):02x}{int(54*alpha):02x}"
        else:
            return "transparent"
    
    def play_random_track(self):
        """Play a random track from the playlist"""
        if not self.infinite_lives and self.lives <= 0:
            self.title_label.configure(text="Game Over! You're out of lives.")
            return
            
        if len(self.track_uris) == 0:
            self.title_label.configure(text="No more songs in the playlist.")
            return
        
        # Reset game state for the new track
        self.replay_count = 0
        self.current_play_time = PLAYBACK_DURATION
        self.revealed_seconds = PLAYBACK_DURATION
        self.guess_count = 0
        self.guesses = []
        
        # Get a random track
        random_index = random.randint(0, len(self.track_uris) - 1)
        self.current_track = self.track_uris[random_index]
        self.correct_answer = self.track_names[random_index]
        self.current_artist = self.track_artists[random_index]
        
        # Update the game logic with the current track information
        self.game_logic.current_track = self.current_track
        self.game_logic.current_track_name = self.correct_answer
        self.game_logic.current_track_artist = self.current_artist
        
        # Show debug info if enabled
        if self.show_answers:
            self.title_label.configure(text=f"DEBUG - Answer: {self.correct_answer}")
        else:
            self.title_label.configure(text=f"Guess the Song! (Mode: {self.game_mode})")
        
        # Play the track
        success = self.spotify_manager.play_track(
            self.current_track, 
            start_time=0, 
            duration=self.current_play_time
        )
        
        if not success:
            self.title_label.configure(text="Error playing track. Check your Spotify device.")
        
        # Clear the entry
        self.entry.delete(0, "end")
        self.entry.focus_set()
        
        # Clear suggestions
        self.clear_suggestions()
    
    def replay_song(self):
        """Replay the current song with extended duration"""
        if self.replay_count < 5:
            self.replay_count += 1
            self.revealed_seconds += PLAYBACK_DURATION
            
            # Ensure game logic has the current track information
            self.game_logic.current_track = self.current_track
            self.game_logic.current_track_name = self.correct_answer
            self.game_logic.current_track_artist = self.current_artist
            
            success = self.spotify_manager.play_track(
                self.current_track,
                start_time=0,
                duration=self.revealed_seconds
            )
            
            if not success:
                self.title_label.configure(text="Error replaying track. Check your Spotify device.")
    
    def update_suggestions(self, event=None):
        """Update the suggestions based on user input"""
        query = self.entry.get().strip().lower()
        
        # Clear previous suggestions
        self.clear_suggestions()
        
        if not query:
            return
        
        # Build list of song suggestions
        all_full_names = list(set([
            f"{name} by {artist}"
            for name, artist in zip(
                self.track_names + [self.correct_answer],
                self.track_artists + [self.current_artist]
            )
        ]))
        
        # Get filtering function for current game mode
        filter_func = self.game_logic.get_game_mode_rules(self.game_mode)
        
        # Filter suggestions
        matched = [item for item in all_full_names if filter_func(query, item.lower())]
        matched.sort()  # Sort alphabetically
        
        # Create buttons for each suggestion
        if matched:
            for i, suggestion in enumerate(matched[:10]):  # Limit to 10 suggestions
                suggestion_button = ctk.CTkButton(
                    self.suggestions_listbox,
                    text=suggestion,
                    anchor="w",
                    fg_color=("#f0f0f0", "#1e1e1e"),
                    text_color=("gray10", "gray90"),
                    hover_color=("gray80", "gray30"),
                    height=30,
                    command=lambda s=suggestion: self._on_suggestion_click(s)
                )
                suggestion_button.pack(fill="x", padx=5, pady=2)
                
                # Store reference to button
                self.suggestion_buttons.append(suggestion_button)
                
                # Bind keyboard navigation
                suggestion_button.bind("<Up>", 
                    lambda e, idx=i: self._on_suggestion_key_press(e, idx, -1))
                suggestion_button.bind("<Down>", 
                    lambda e, idx=i: self._on_suggestion_key_press(e, idx, 1))
                suggestion_button.bind("<Return>", 
                    lambda e, s=suggestion: self._on_suggestion_enter(e, s))
        elif len(query) >= 3:
            # Show "no matches" message if query is long enough
            no_match_label = ctk.CTkLabel(
                self.suggestions_listbox,
                text=f"No matches for '{query}'",
                fg_color="transparent",
                text_color=("gray50", "gray70"),
                anchor="w",
                height=30
            )
            no_match_label.pack(fill="x", padx=10, pady=10)
            
            # Add hint based on game mode
            if self.game_mode == "Normal":
                hint_text = "Try a different spelling or shorter input"
            elif self.game_mode == "Hard":
                hint_text = "Exact match needed (±1 error)"
            elif self.game_mode == "Harder":
                hint_text = "Exact song title needed"
            else:  # Expert mode
                hint_text = "Exact 'title by artist' needed"
                
            hint_label = ctk.CTkLabel(
                self.suggestions_listbox,
                text=hint_text,
                fg_color="transparent", 
                text_color=("#1DB954", "#1DB954"),
                anchor="w",
                height=20
            )
            hint_label.pack(fill="x", padx=10, pady=(0,10))
            
            # Store reference to clean up later
            self.suggestion_buttons.append(no_match_label)
            self.suggestion_buttons.append(hint_label)
    
    def _on_suggestion_click(self, suggestion):
        """Wrapper for suggestion click to improve responsiveness"""
        self.select_suggestion(suggestion)
    
    def _on_suggestion_key_press(self, event, current_idx, direction):
        """Handle up/down keys within the suggestion list"""
        if direction == -1:
            # If at the first suggestion, go back to entry field
            if current_idx == 0:
                self.entry.focus_set()
                # Clear selection highlighting
                self.suggestion_buttons[current_idx].configure(
                    fg_color="transparent",
                    text_color=("gray10", "gray90")
                )
                self.current_suggestion_index = -1
                # Restore original text
                return
            # Otherwise select the previous suggestion
            self._select_suggestion_at_index(current_idx - 1)
        elif direction == 1:
            # If at the last suggestion, stay there
            if current_idx == len(self.suggestion_buttons) - 1:
                return
            # Otherwise select the next suggestion
            self._select_suggestion_at_index(current_idx + 1)
                
    def _on_suggestion_enter(self, event, suggestion):
        """Handle Enter key on a suggestion button"""
        self.select_suggestion(suggestion)
    
    def clear_suggestions(self):
        """Clear all suggestions"""
        # Remove all suggestion buttons
        for button in self.suggestion_buttons:
            button.destroy()
        self.suggestion_buttons = []
        
        # Reset suggestion index
        self.current_suggestion_index = -1
    
    def select_suggestion(self, suggestion):
        """Select a suggestion and fill the entry"""
        self.entry.delete(0, "end")
        self.entry.insert(0, suggestion)
        self.secure_guess()
    
    def on_entry_up_down(self, event):
        """Handle up/down keys in the entry field"""
        if not self.suggestion_buttons:
            return
            
        if event.keysym == "Down":
            # Focus and highlight first suggestion
            self._select_suggestion_at_index(0)
        elif event.keysym == "Up":
            # Focus and highlight last suggestion
            self._select_suggestion_at_index(len(self.suggestion_buttons) - 1)
    
    def _select_suggestion_at_index(self, index):
        """Select the suggestion at the given index"""
        if 0 <= index < len(self.suggestion_buttons):
            # Reset all buttons to default style
            for btn in self.suggestion_buttons:
                btn.configure(
                    fg_color="transparent",
                    text_color=("gray10", "gray90")
                )
            
            # Highlight the selected button
            self.suggestion_buttons[index].configure(
                fg_color=("gray75", "gray25"),
                text_color=("black", "white")
            )
            
            # Set focus on the button
            self.suggestion_buttons[index].focus_set()
            
            # Extract the suggestion text and update entry field
            suggestion_text = self.suggestion_buttons[index].cget("text")
            self.entry.delete(0, "end")
            self.entry.insert(0, suggestion_text)
            
            # Store current selection index
            self.current_suggestion_index = index
    
    def on_entry_return(self, event):
        """Handle Enter key in the entry field"""
        self.secure_guess()
    
    def secure_guess(self):
        """Process the user's guess"""
        guess_text = self.entry.get().strip()
        if not guess_text:
            return
            
        # Add to guesses list
        self.guesses.append(guess_text)
        
        # Skip verification if enabled
        if self.skip_verification:
            # Auto win
            self.show_feedback(True)
            self.title_label.configure(text="Correct!")
            self.show_song_info(self.correct_answer, self.current_artist)
            
            # Record the result
            self.played_songs.append({
                'song': f"{self.correct_answer} by {self.current_artist}",
                'guesses': self.guesses.copy(),
                'result': 'Correct',
                'time_revealed': self.revealed_seconds
            })
            
            # Play next track after delay
            self.after(2000, self.play_random_track)
            return
            
        # Check if the guess is correct using fuzzy matching
        normalized_guess = guess_text.lower()
        normalized_answer = self.correct_answer.lower()
        
        # Calculate normalized Levenshtein distance
        max_len = max(len(normalized_guess), len(normalized_answer))
        distance = levenshtein_distance(normalized_guess, normalized_answer)
        normalized_distance = distance / max_len if max_len > 0 else 1.0
        
        # Consider correct if the normalized distance is below threshold
        # For shorter titles, be more lenient
        threshold = 0.4 if len(normalized_answer) < 10 else 0.3
        
        is_correct = (normalized_distance <= threshold or 
                    normalized_answer in normalized_guess or
                    normalized_guess in normalized_answer)
        
        if is_correct:
            self.show_feedback(True)
            self.title_label.configure(text="Correct!")
            self.show_song_info(self.correct_answer, self.current_artist)
            
            # Record the result
            self.played_songs.append({
                'song': f"{self.correct_answer} by {self.current_artist}",
                'guesses': self.guesses.copy(),
                'result': 'Correct',
                'time_revealed': self.revealed_seconds
            })
            
            # Play next track after delay
            self.after(2000, self.play_random_track)
        else:
            self.show_feedback(False)
            self.guess_count += 1
            
            if self.guess_count >= MAX_GUESS_COUNT:
                if not self.infinite_lives:
                    self.lives -= 1
                    self.update_lives_label()
                
                self.title_label.configure(text="Out of guesses!")
                self.show_song_info(self.correct_answer, self.current_artist)
                
                # Record the result
                self.played_songs.append({
                    'song': f"{self.correct_answer} by {self.current_artist}",
                    'guesses': self.guesses.copy(),
                    'result': 'Incorrect',
                    'time_revealed': self.revealed_seconds
                })
                
                # Play next track after delay
                self.after(2000, self.play_random_track)
            else:
                left = MAX_GUESS_COUNT - self.guess_count
                self.title_label.configure(text=f"Incorrect! {left} guesses left.")
        
        # Clear entry & suggestions
        self.entry.delete(0, "end")
        self.clear_suggestions()
        self.entry.focus_set()
    
    def give_up(self):
        """Skip the current song"""
        if not self.infinite_lives:
            self.lives -= 1
            self.update_lives_label()
        
        self.title_label.configure(text="Skipping...")
        self.show_song_info(self.correct_answer, self.current_artist)
        
        # Record the result
        self.played_songs.append({
            'song': f"{self.correct_answer} by {self.current_artist}",
            'guesses': self.guesses.copy(),
            'result': 'Skipped',
            'time_revealed': self.revealed_seconds
        })
        
        # Play next track after delay
        self.after(2000, self.play_random_track)
    
    def update_lives_label(self):
        """Update the lives counter"""
        if self.infinite_lives:
            self.lives_label.configure(text="Lives: ∞")
        else:
            self.lives_label.configure(text=f"Lives: {self.lives}")
    
    def show_song_info(self, song, artist):
        """Show the song info"""
        self.song_info_label.configure(text=f"{song} by {artist}")
        self.song_info_frame.pack(fill="x", padx=20, pady=10, after=self.header_frame)
        self.song_info_visible = True
        self.song_info_time = int(time.time() * 1000)
    
    def show_feedback(self, correct):
        """Show visual feedback for correct/incorrect guess"""
        self.feedback_color = "green" if correct else "red"
        self.feedback_time = int(time.time() * 1000)
        
        # Set initial color
        color = "#4CAF50" if correct else "#F44336"
        self.configure(fg_color=color)
        
        # Make sure the animation continues
        if not self.feedback_color:
            self.feedback_color = "green" if correct else "red"
    
    def show_summary(self):
        """Show the game summary screen"""
        self.parent.show_summary_screen(self.played_songs)
    
    def quit_game(self):
        """Quit the game and return to the start screen"""
        self.parent.show_start_screen()
    
    # Button event handler methods
    def _on_replay_button_click(self):
        """Handle replay button click"""
        self.replay_song()
        
    def _on_give_up_button_click(self):
        """Handle give up button click"""
        self.give_up()
        
    def _on_summary_button_click(self):
        """Handle summary button click"""
        self.show_summary()
        
    def _on_quit_button_click(self):
        """Handle quit button click"""
        self.quit_game() 