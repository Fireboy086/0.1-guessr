"""
Summary Screen - Displays game results at the end of a session
"""
import customtkinter as ctk

class SummaryScreen(ctk.CTkFrame):
    """Summary screen for displaying game results"""
    
    def __init__(self, parent, played_songs):
        super().__init__(parent, corner_radius=10)
        self.parent = parent
        self.played_songs = played_songs
        
        # Create UI
        self.create_widgets()
    
    def create_widgets(self):
        """Create the UI elements"""
        # Title
        self.title_label = ctk.CTkLabel(
            self,
            text="Game Summary",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.pack(pady=(20, 10))
        
        # Stats
        self.stats_frame = ctk.CTkFrame(self)
        self.stats_frame.pack(fill="x", padx=20, pady=10)
        
        # Calculate stats
        total = len(self.played_songs)
        correct = sum(1 for song in self.played_songs if song['result'] == 'Correct')
        skipped = sum(1 for song in self.played_songs if song['result'] == 'Skipped')
        incorrect = sum(1 for song in self.played_songs if song['result'] == 'Incorrect')
        
        # Display stats
        stats_text = f"Total Songs: {total}  |  Correct: {correct}  |  Incorrect: {incorrect}  |  Skipped: {skipped}"
        self.stats_label = ctk.CTkLabel(
            self.stats_frame,
            text=stats_text,
            font=ctk.CTkFont(size=16)
        )
        self.stats_label.pack(pady=10)
        
        # Create scrollable frame for song results
        self.results_frame = ctk.CTkScrollableFrame(
            self,
            width=700,
            height=400
        )
        self.results_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # Add each song result
        for idx, song_info in enumerate(self.played_songs, start=1):
            self.add_song_result(idx, song_info)
        
        # Buttons frame
        self.buttons_frame = ctk.CTkFrame(self)
        self.buttons_frame.pack(fill="x", padx=20, pady=20)
        
        # Menu button
        self.menu_button = ctk.CTkButton(
            self.buttons_frame,
            text="Return to Menu",
            command=self._on_menu_button_click,
            width=150,
            height=40,
            font=ctk.CTkFont(size=16),
            fg_color=("#f0f0f0", "#1e1e1e")
        )
        self.menu_button.pack(side="left", padx=20)
        
        # Quit button
        self.quit_button = ctk.CTkButton(
            self.buttons_frame,
            text="Quit Game",
            command=self._on_quit_button_click,
            width=150,
            height=40,
            font=ctk.CTkFont(size=16),
            fg_color="#F44336",
            hover_color="#D32F2F"
        )
        self.quit_button.pack(side="right", padx=20)
    
    def add_song_result(self, idx, song_info):
        """Add a song result entry to the results frame"""
        # Create a frame for this song
        song_frame = ctk.CTkFrame(self.results_frame)
        song_frame.pack(fill="x", padx=5, pady=5, ipadx=5, ipady=5)
        
        # Set color based on result
        if song_info['result'] == "Correct":
            result_color = "#69FFAA"  # Green
            song_frame.configure(fg_color=("#EFFFEE", "#1E3B2E"))
        elif song_info['result'] == "Skipped":
            result_color = "#FFBD16"  # Yellow
            song_frame.configure(fg_color=("#FFF8E0", "#3B3420"))
        else:  # Incorrect
            result_color = "#FF4449"  # Red
            song_frame.configure(fg_color=("#FFEEEE", "#3B2020"))
        
        # Song title and result
        title_text = f"{idx}. {song_info['song']} - {song_info['result']}"
        title_label = ctk.CTkLabel(
            song_frame,
            text=title_text,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=result_color
        )
        title_label.pack(anchor="w", padx=10, pady=(10, 5))
        
        # Time revealed
        if 'time_revealed' in song_info:
            time_label = ctk.CTkLabel(
                song_frame,
                text=f"Time Revealed: {song_info['time_revealed']} seconds",
                font=ctk.CTkFont(size=14)
            )
            time_label.pack(anchor="w", padx=10, pady=(0, 5))
        
        # Guesses section
        if song_info['guesses']:
            guesses_label = ctk.CTkLabel(
                song_frame,
                text="Your Guesses:",
                font=ctk.CTkFont(size=14, weight="bold", underline=True)
            )
            guesses_label.pack(anchor="w", padx=10, pady=(5, 0))
            
            # Add each guess
            for i, guess in enumerate(song_info['guesses'], 1):
                guess_label = ctk.CTkLabel(
                    song_frame,
                    text=f"{i}. {guess}",
                    font=ctk.CTkFont(size=12)
                )
                guess_label.pack(anchor="w", padx=20, pady=(0, 2))
    
    def return_to_menu(self):
        """Return to the start screen"""
        self.parent.show_start_screen()
    
    def quit_game(self):
        """Exit the application"""
        self.parent.quit()
    
    # Button event handlers
    def _on_menu_button_click(self):
        """Handle menu button click"""
        self.return_to_menu()
        
    def _on_quit_button_click(self):
        """Handle quit button click"""
        self.quit_game() 