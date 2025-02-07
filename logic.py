import random
import re
from config import *

def levenshtein_distance(s1, s2):
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]

class GameLogic:
    def __init__(self, sp):
        self.sp = sp
        self.track_uris = []
        self.track_names = []
        self.track_artists = []
        self.current_track_index = 0
        self.current_track_name = ""
        self.current_track_artist = ""
        self.score = 0
        self.lives = MAX_LIVES
        self.game_mode = "Normal"  # Default game mode
        self.typed = True
        
    def get_user_playlists(self):
        playlists = []
        limit = 50
        offset = 0

        while True:
            response = self.sp.current_user_playlists(limit=limit, offset=offset)
            playlists.extend(response['items'])
            
            if len(response['items']) < limit:
                break
            
            offset += limit

        # Extract playlist names
        playlist_names = [playlist['name'] for playlist in playlists]

        # Insert "Liked Songs" and "Custom Playlist" at the beginning
        playlist_names.insert(0, "Liked Songs")
        playlist_names.insert(1, "Custom Playlist")

        return playlist_names

    def get_playlist_tracks(self, playlist_name, custom_url=""):
        # Handle Liked Songs
        if playlist_name == "Liked Songs":
            return self._get_liked_songs()
        # Handle Custom Playlist URL
        elif playlist_name == "Custom Playlist":
            return self._get_custom_playlist_tracks(custom_url)
        # Handle regular playlists
        else:
            return self._get_regular_playlist_tracks(playlist_name)

    def _get_liked_songs(self):
        tracks = []
        offset = 0
        while True:
            response = self.sp.current_user_saved_tracks(limit=50, offset=offset)
            tracks.extend(response['items'])
            if len(response['items']) < 50:
                break
            offset += 50
            
        return self._extract_track_info(tracks)

    def _get_custom_playlist_tracks(self, custom_url):
        if not custom_url:
            return [], [], []
        
        # Extract playlist ID from URL
        match = re.search(r"playlist/([a-zA-Z0-9]+)", custom_url.split('?')[0])
        if not match:
            return [], [], []
        
        playlist_id = match.group(1)
        return self._get_playlist_tracks_by_id(playlist_id)

    def _get_regular_playlist_tracks(self, playlist_name):
        playlists = []
        limit = 50
        offset = 0
        
        # Get all user playlists
        while True:
            response = self.sp.current_user_playlists(limit=limit, offset=offset)
            playlists.extend(response['items'])
            if len(response['items']) < limit:
                break
            offset += limit
            
        # Find the selected playlist
        playlist_id = None
        for playlist in playlists:
            if playlist['name'] == playlist_name:
                playlist_id = playlist['id']
                break
                
        if not playlist_id:
            return [], [], []
        
        return self._get_playlist_tracks_by_id(playlist_id)

    def _get_playlist_tracks_by_id(self, playlist_id):
        tracks = []
        offset = 0
        while True:
            response = self.sp.playlist_tracks(playlist_id, offset=offset)
            tracks.extend(response['items'])
            if len(response['items']) < 100:
                break
            offset += 100
            
        return self._extract_track_info(tracks)

    def _extract_track_info(self, tracks):
        track_uris = []
        track_names = []
        track_artists = []
        
        for track in tracks:
            if track['track'] is None:
                continue
            track_uris.append(track['track']['uri'])
            track_names.append(track['track']['name'])
            track_artists.append(track['track']['artists'][0]['name'])
        
        return track_uris, track_names, track_artists

    def select_random_track(self):
        self.current_track_index = random.randint(0, len(self.track_names) - 1)
        self.current_track_name = self.track_names[self.current_track_index]
        self.current_track_artist = self.track_artists[self.current_track_index]
        print(self.current_track_name, self.current_track_artist)
        return self.current_track_name, self.current_track_artist

    def check_guess(self, guess):
        if not guess:
            return False, 0, "Please enter a song name"

        bonus_multiplier = 2 if self.typed else 1
        guess_lower = guess.lower()
        
        if guess_lower == self.current_track_name.lower():
            points = 5 * bonus_multiplier
            message = f"Correct! {points} points!" + (" (Typed bonus!)" if bonus_multiplier > 1 else "")
            return True, points, message
        elif guess_lower == f"{self.current_track_name} by {self.current_track_artist}".lower():
            points = 10 * bonus_multiplier
            message = f"Correct! {points} points!" + (" (Typed bonus!)" if bonus_multiplier > 1 else "")
            return True, points, message
        else:
            self.lives = max(0, self.lives - 1)
            return False, 0, "Incorrect guess"

    def get_game_mode_rules(self, mode):
        def normal_rule(query, item):
            parts = item.lower().split(" by ")
            if len(parts) != 2:
                return False
            song, artist = parts
            query_parts = query.lower().split(" by ")
            
            if len(query_parts) == 2:
                query_song, query_artist = query_parts
                return (query_song.strip() in song) and (query_artist.strip() in artist)
            return query.lower() in song

        def hard_rule(query, item):
            parts = item.lower().split(" by ")
            if len(parts) != 2:
                return False
            song, artist = parts
            query_parts = query.lower().split(" by ")
            
            if len(query_parts) == 2:
                query_song, query_artist = query_parts
                return (query_song.strip() in song) and (query_artist.strip() in artist)
            return query.lower() in song

        def harder_rule(query, item):
            parts = item.lower().split(" by ")
            if len(parts) != 2:
                return False
            song, artist = parts
            query_parts = query.lower().split(" by ")
            
            if len(query_parts) == 2:
                query_song, query_artist = query_parts
                return (query_song.strip() == song) and (query_artist.strip() in artist)
            return query.lower() == song

        def expert_rule(query, item):
            return query.lower() == item.lower()

        rules = {
            "Normal": (False, normal_rule),
            "Hard": (True, hard_rule),
            "Harder": (True, harder_rule),
            "Expert": (True, expert_rule)
        }
        
        return rules.get(mode, (False, normal_rule))

    def set_game_mode(self, mode):
        self.game_mode = mode 
        
        
if __name__ == "__main__":
    import main as M
    M.main()