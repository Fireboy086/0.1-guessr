import spotipy
from spotipy.exceptions import SpotifyException
from config import *
import random
import time
import threading

class SpotifyPlayer:
    def __init__(self, sp):
        """Initialize the Spotify player with a Spotify client instance."""
        self.sp = sp
        self.current_track = None
        self.current_track_name = None
        self.current_artist = None
        self.replay_count = 0
        self.current_play_time = PLAYBACK_DURATION
        self.last_device_id = None
        self.volume_level = VOLUME_LEVEL
        self.play_timer = None
        self.is_playing = False

    def get_active_device(self):
        """Check for an active Spotify device."""
        try:
            devices = self.sp.devices()
            if not devices['devices']:
                print("No active Spotify device found! Start Spotify on a device.")
                return None
            
            # First try to find an active device
            for device in devices['devices']:
                if device['is_active']:
                    self.last_device_id = device['id']
                    return device['id']
            
            # If no active device, use the first available one
            self.last_device_id = devices['devices'][0]['id']
            return devices['devices'][0]['id']
        except SpotifyException as e:
            print(f"Error getting devices: {e}")
            return None

    def _schedule_pause(self, device_id, duration):
        """Schedule pausing playback after duration."""
        def pause_after_delay():
            time.sleep(duration)
            if self.is_playing:  # Only pause if we haven't already stopped
                self.pause_playback(device_id)
                self.is_playing = False

        # Cancel any existing timer
        if self.play_timer and self.play_timer.is_alive():
            self.is_playing = False
            self.play_timer.join()

        # Start new timer
        self.is_playing = True
        self.play_timer = threading.Thread(target=pause_after_delay)
        self.play_timer.daemon = True  # Make thread exit when main program exits
        self.play_timer.start()

    def play_track(self, track_uri, start_time=0, duration=PLAYBACK_DURATION, device_id=None):
        """Play the track for a specific duration starting from the specified time."""
        if not device_id:
            device_id = self.get_active_device()
            if not device_id:
                print("No active device available for playback.")
                return False

        # Set volume to desired level
        try:
            self.sp.volume(self.volume_level, device_id)
        except SpotifyException as e:
            print(f"Error setting volume: {e}")
            # Continue even if volume setting fails

        # Start playback
        try:
            self.sp.start_playback(device_id=device_id, uris=[track_uri], position_ms=int(start_time * 1000))
            # Schedule pausing after the specified duration
            self._schedule_pause(device_id, duration)
            return True
        except SpotifyException as e:
            print(f"Error starting playback: {e}")
            return False

    def pause_playback(self, device_id=None):
        """Pause playback on the specified device."""
        if not device_id:
            device_id = self.last_device_id or self.get_active_device()
            if not device_id:
                return False

        try:
            self.sp.pause_playback(device_id=device_id)
            self.is_playing = False
            return True
        except SpotifyException as e:
            print(f"Error pausing playback: {e}")
            return False

    def play_random_track(self, track_uris, track_names, track_artists):
        """Play a random track from the provided lists."""
        if not track_uris:
            print("No tracks available to play.")
            return None, None, None

        self.replay_count = 0
        self.current_play_time = PLAYBACK_DURATION

        # Select random track
        random_index = random.randint(0, len(track_uris) - 1)
        self.current_track = track_uris[random_index]
        self.current_track_name = track_names[random_index]
        self.current_artist = track_artists[random_index]

        # Get device and play
        device_id = self.get_active_device()
        if not device_id:
            print("No active Spotify device found! Start Spotify on a device.")
            return None, None, None

        # Play the track
        success = self.play_track(self.current_track, 0, self.current_play_time, device_id)
        if success:
            return self.current_track, self.current_track_name, self.current_artist
        return None, None, None

    def replay_song(self, extend_duration=True):
        """Replay the current song with optional duration extension."""
        if self.replay_count >= MAX_REPLAYS:
            print("Maximum replays reached!")
            return False

        if extend_duration:
            self.current_play_time += PLAYBACK_DURATION
        self.replay_count += 1

        device_id = self.get_active_device()
        if not device_id:
            print("No active Spotify device found! Start Spotify on a device.")
            return False

        return self.play_track(self.current_track, 0, self.current_play_time, device_id)

    def set_volume(self, volume_level):
        """Set the playback volume (0-100)."""
        self.volume_level = max(0, min(100, volume_level))
        device_id = self.last_device_id or self.get_active_device()
        if device_id:
            try:
                self.sp.volume(self.volume_level, device_id)
                return True
            except SpotifyException as e:
                print(f"Error setting volume: {e}")
        return False

    def get_current_playback_state(self):
        """Get the current playback state."""
        try:
            return self.sp.current_playback()
        except SpotifyException as e:
            print(f"Error getting playback state: {e}")
            return None 