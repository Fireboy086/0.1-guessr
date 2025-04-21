"""
Spotify Manager - Handles Spotify API interactions
"""
import time
import threading
from config import *

class SpotifyManager:
    """Class to manage Spotify API interactions and playback"""
    
    def __init__(self, sp):
        """Initialize with a Spotify API client"""
        self.sp = sp
        self.current_track = None
        self.current_track_name = None
        self.current_track_artist = None
        self.playback_active = False
        self.pause_timer = None
    
    def get_active_device(self):
        """Get the active Spotify device"""
        try:
            devices = self.sp.devices()
            if not devices['devices']:
                return None
            
            # Return first available device
            return devices['devices'][0]['id']
        except Exception as e:
            print(f"Error getting active device: {e}")
            return None
    
    def _schedule_pause(self, device_id, duration):
        """Schedule a pause after the given duration"""
        def pause_after_delay():
            # Sleep for duration seconds
            time.sleep(duration)
            # Check if playback is still active before pausing
            if self.playback_active:
                try:
                    self.sp.pause_playback(device_id=device_id)
                    self.playback_active = False
                except Exception as e:
                    print(f"Error pausing playback: {e}")
        
        # Cancel any existing timer
        if self.pause_timer and self.pause_timer.is_alive():
            self.playback_active = False
            self.pause_timer.join(0.1)
        
        # Start a new timer
        self.playback_active = True
        self.pause_timer = threading.Thread(target=pause_after_delay)
        self.pause_timer.daemon = True
        self.pause_timer.start()
    
    def _delayed_start(self, track_uri, device_id, start_time, duration):
        """Start playback with a slight delay to prevent API rate limiting"""
        time.sleep(0.1)  # Small delay to prevent rate limiting
        
        try:
            # Set volume
            self.sp.volume(VOLUME_LEVEL, device_id)
        except Exception as e:
            print(f"Error setting volume: {e}")
        
        # Start playback
        try:
            self.sp.start_playback(
                device_id=device_id, 
                uris=[track_uri], 
                position_ms=int(start_time * 1000)
            )
            self._schedule_pause(device_id, duration)
        except Exception as e:
            print(f"Error starting playback: {e}")
            self.playback_active = False
    
    def play_track(self, track_uri, start_time=0, duration=PLAYBACK_DURATION, device_id=None):
        """Play a track for the specified duration"""
        if not device_id:
            device_id = self.get_active_device()
            
        if not device_id:
            print("No active device available for playback.")
            return False
        
        # Start playback in a separate thread
        thread = threading.Thread(
            target=self._delayed_start, 
            args=(track_uri, device_id, start_time, duration)
        )
        thread.daemon = True
        thread.start()
        
        return True
    
    def pause_playback(self, device_id=None):
        """Pause playback on the active device"""
        if not device_id:
            device_id = self.get_active_device()
            
        if not device_id:
            print("No active device available to pause.")
            return False
        
        try:
            self.sp.pause_playback(device_id=device_id)
            self.playback_active = False
            return True
        except Exception as e:
            print(f"Error pausing playback: {e}")
            return False
    
    def play_random_track(self, track_uris, track_names, track_artists):
        """Play a random track from the provided lists"""
        import random
        
        if not track_uris:
            return None, None, None
            
        # Choose a random track
        random_index = random.randint(0, len(track_uris) - 1)
        track_uri = track_uris[random_index]
        track_name = track_names[random_index]
        track_artist = track_artists[random_index]
        
        # Save current track info
        self.current_track = track_uri
        self.current_track_name = track_name
        self.current_track_artist = track_artist
        
        # Start playback
        device_id = self.get_active_device()
        if not device_id:
            return None, None, None
            
        success = self.play_track(track_uri, 0, PLAYBACK_DURATION, device_id)
        if success:
            return track_uri, track_name, track_artist
        else:
            return None, None, None
    
    def replay_song(self, extend_duration=True):
        """Replay the current song, optionally with an extended duration"""
        if not self.current_track:
            return False
            
        device_id = self.get_active_device()
        if not device_id:
            return False
        
        # Determine playback duration
        duration = PLAYBACK_DURATION
        if extend_duration:
            duration += 0.5  # Add extra time
        
        return self.play_track(self.current_track, 0, duration, device_id)
    
    def set_volume(self, volume_level):
        """Set the volume level (0-100)"""
        device_id = self.get_active_device()
        if not device_id:
            return False
            
        try:
            self.sp.volume(volume_level, device_id)
            return True
        except Exception as e:
            print(f"Error setting volume: {e}")
            return False
    
    def get_current_playback_state(self):
        """Get the current playback state"""
        try:
            return self.sp.current_playback()
        except Exception as e:
            print(f"Error getting playback state: {e}")
            return None 