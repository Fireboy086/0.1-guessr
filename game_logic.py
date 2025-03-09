"""
Game Logic - Core gameplay logic for the Spotify Guessing Game
"""
import re
import random

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

class GameLogic:
    """Manages the core game logic for the Spotify Guessing Game"""
    
    def __init__(self, sp):
        """Initialize the game logic with a Spotify client"""
        self.sp = sp
        self.current_track = None
        self.current_track_name = None
        self.current_track_artist = None
        self.game_mode = "Normal"
        self.track_uris = []
        self.track_names = []
        self.track_artists = []
    
    def get_user_playlists(self):
        """Get the user's playlists including cover images"""
        playlists = []
        limit = 50
        offset = 0
        
        try:
            while True:
                response = self.sp.current_user_playlists(limit=limit, offset=offset)
                playlists.extend(response['items'])
                if len(response['items']) < limit:
                    break
                offset += limit
                
            # Sort playlists by name
            playlists.sort(key=lambda p: p['name'].lower())
            
            # Each playlist object now includes:
            # - name: The playlist name
            # - id: The playlist ID
            # - images: List of image objects with urls
            
            return playlists
        except Exception as e:
            print(f"Error getting user playlists: {e}")
            return []
    
    def get_playlist_tracks(self, playlist_name, custom_url=""):
        """Get tracks from a playlist by name or URL"""
        # Handle Liked Songs
        if playlist_name == "Liked Songs":
            return self._get_liked_songs()
        
        # Handle custom URL
        if playlist_name == "Enter Custom Playlist URL":
            if not custom_url:
                return [], [], []
                
            # Format can be full URL or just playlist ID
            if "spotify:" in custom_url:
                # Handle Spotify URI format (spotify:playlist:ID)
                playlist_id = custom_url.split(":")[-1]
            elif "spotify.com" in custom_url:
                # Handle URL format
                match = re.search(r"playlist[/:]([a-zA-Z0-9]+)", custom_url)
                if not match:
                    return [], [], []
                playlist_id = match.group(1)
            else:
                # Assume it's just the ID
                playlist_id = custom_url
                
            return self._get_playlist_tracks_by_id(playlist_id)
            
        # Handle regular playlist by name
        return self._get_regular_playlist_tracks(playlist_name)
    
    def _get_liked_songs(self):
        """Get the user's liked songs"""
        tracks = []
        limit = 50
        offset = 0
        
        try:
            while True:
                response = self.sp.current_user_saved_tracks(limit=limit, offset=offset)
                tracks.extend(response['items'])
                if len(response['items']) < limit:
                    break
                offset += limit
            
            return self._extract_track_info(tracks)
        except Exception as e:
            print(f"Error getting liked songs: {e}")
            return [], [], []
    
    def _get_regular_playlist_tracks(self, playlist_name):
        """Get tracks from a playlist by name"""
        try:
            # Get all user playlists
            playlists = self.get_user_playlists()
            
            # Find the playlist by name
            playlist_id = None
            for playlist in playlists:
                if playlist['name'] == playlist_name:
                    playlist_id = playlist['id']
                    break
            
            if not playlist_id:
                return [], [], []
                
            return self._get_playlist_tracks_by_id(playlist_id)
        except Exception as e:
            print(f"Error getting playlist tracks: {e}")
            return [], [], []
    
    def _get_playlist_tracks_by_id(self, playlist_id):
        """Get tracks from a playlist by ID"""
        tracks = []
        limit = 100
        offset = 0
        
        try:
            while True:
                response = self.sp.playlist_items(playlist_id, limit=limit, offset=offset)
                tracks.extend(response['items'])
                if len(response['items']) < limit:
                    break
                offset += limit
            
            return self._extract_track_info(tracks)
        except Exception as e:
            print(f"Error getting playlist tracks: {e}")
            return [], [], []
    
    def _extract_track_info(self, tracks):
        """Extract track URIs, names, and artists from track objects"""
        track_uris = []
        track_names = []
        track_artists = []
        
        for item in tracks:
            if item['track'] is not None:
                track_uris.append(item['track']['uri'])
                track_names.append(item['track']['name'])
                track_artists.append(item['track']['artists'][0]['name'])
        
        return track_uris, track_names, track_artists
    
    def play_random(self):
        """Select a random track from the loaded tracks"""
        if not self.track_uris:
            return None, None, None
            
        random_index = random.randint(0, len(self.track_uris) - 1)
        self.current_track = self.track_uris[random_index]
        self.current_track_name = self.track_names[random_index]
        self.current_track_artist = self.track_artists[random_index]
        
        return self.current_track, self.current_track_name, self.current_track_artist
    
    def replay_current_track(self):
        """Return the current track information"""
        return self.current_track, self.current_track_name, self.current_track_artist
    
    def check_guess(self, guess):
        """Check if a guess is correct based on the game mode"""
        if not self.current_track_name or not self.current_track_artist:
            print(f"Error: Missing track information in GameLogic. Name: {self.current_track_name}, Artist: {self.current_track_artist}")
            return False
            
        correct_title = self.current_track_name.lower()
        correct_full = f"{self.current_track_name} by {self.current_track_artist}".lower()
        guess_lower = guess.lower()
        
        # Debug information
        print(f"Checking guess: '{guess_lower}' against '{correct_title}' or '{correct_full}' in mode: {self.game_mode}")
        
        if self.game_mode == "Expert":
            # Exact match on "title by artist"
            return guess_lower == correct_full
        elif self.game_mode == "Harder":
            # Exact match on title only
            return guess_lower == correct_title
        elif self.game_mode == "Hard":
            # Close match with <= 1 error on title, or exact match on full
            title_dist = levenshtein_distance(guess_lower, correct_title)
            result = title_dist <= 1 or guess_lower == correct_full
            print(f"Hard mode: Title distance {title_dist}, Result: {result}")
            return result
        else:  # Normal mode
            # Allow <= 2 errors in either "title" or "title by artist"
            dist_title = levenshtein_distance(guess_lower, correct_title)
            dist_full = levenshtein_distance(guess_lower, correct_full)
            result = dist_title <= 2 or dist_full <= 2
            print(f"Normal mode: Title distance {dist_title}, Full distance {dist_full}, Result: {result}")
            return result
    
    def get_game_mode_rules(self, mode):
        """Get a function that implements the filtering rules for a game mode"""
        def normal_rule(query, item):
            """Normal mode: Show partial matches with Levenshtein distance <= 2"""
            item_lower = item.lower()
            title = item_lower.split(" by ")[0]
            
            # More flexible matching for partial inputs:
            # 1. Show if query is a substring of title or full item
            # 2. OR if the query is close to the beginning of the title
            # 3. OR if the full Levenshtein distance is acceptable
            
            # If query is a substring anywhere
            if query in item_lower:
                return True
                
            # Check if query is the beginning of a word in the title
            title_words = title.split()
            for word in title_words:
                if word.startswith(query):
                    return True
            
            # For shorter queries (1-3 chars), be more lenient
            if len(query) <= 3:
                return True
                
            # For medium queries (4-6 chars), allow prefix matching
            if len(query) <= 6:
                if title.startswith(query):
                    return True
                for word in title_words:
                    if word.startswith(query):
                        return True
            
            # For longer queries, use Levenshtein but with higher threshold
            max_distance = min(2, len(query) // 3)  # Scale with query length
            return levenshtein_distance(query, title) <= max_distance
        
        def hard_rule(query, item):
            """Hard mode: Only show exact matches with <= 1 error in the title"""
            item_lower = item.lower()
            title = item_lower.split(" by ")[0]
            
            # More flexible than before but still restrictive:
            # 1. Show if query is a substring of the beginning of title
            # 2. OR if the query is close to the title with 1 error
            
            # Prefix matching
            if title.startswith(query):
                return True
                
            # Short queries - show more
            if len(query) <= 3:
                return query in title
                
            # Levenshtein matching with restrictions
            return levenshtein_distance(query, title) <= 1 or query == item_lower
        
        def harder_rule(query, item):
            """Harder mode: Only show if exact song name match"""
            title = item.lower().split(" by ")[0]
            
            # Slightly more flexible:
            # 1. Match beginning of title
            # 2. Only exact match for longer queries
            if len(query) <= 3:
                return title.startswith(query)
                
            return query == title
        
        def expert_rule(query, item):
            """Expert mode: Only show if exact 'title by artist' match"""
            # Even in expert mode, show suggestions for short queries
            if len(query) <= 2:
                return item.lower().startswith(query)
                
            return query == item.lower()
        
        rules = {
            "Normal": normal_rule,
            "Hard": hard_rule,
            "Harder": harder_rule,
            "Expert": expert_rule,
            # For backward compatibility
            "HarderHarder": expert_rule
        }
        
        return rules.get(mode, normal_rule)
    
    def set_game_mode(self, mode):
        """Set the game mode"""
        self.game_mode = mode 