# media.py - Media control and playback for YouTube, Spotify, and local files

import pywhatkit as pwk
import webbrowser
import subprocess
import os
import requests
import json
from urllib.parse import quote
from utils import log_message, speak, retry_operation
from config import *

class MediaHandler:
    def __init__(self):
        self.current_media = None
        self.media_history = []
        self.volume_level = 50
        self.is_playing = False
    
    def play_youtube_video(self, search_query, open_video=True):
        """
        Search and play YouTube video
        Args:
            search_query (str): Video search query
            open_video (bool): Whether to open video in browser
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if open_video:
                # Use pywhatkit to play immediately
                pwk.playonyt(search_query)
                log_message(f"Playing YouTube video: {search_query}")
                speak(f"Playing {search_query} on YouTube.")
            else:
                # Just get the URL without opening
                search_url = f"https://www.youtube.com/results?search_query={quote(search_query)}"
                log_message(f"YouTube search URL generated: {search_url}")
                speak(f"Found YouTube search for {search_query}")
            
            # Add to history
            self.add_to_history('youtube', search_query)
            self.current_media = {'type': 'youtube', 'title': search_query}
            self.is_playing = True
            
            return True
            
        except Exception as e:
            log_message(f"Failed to play YouTube video: {e}", "ERROR")
            speak("Sorry, I couldn't play the YouTube video.")
            return False
    
    def search_youtube(self, query, max_results=5):
        """
        Search YouTube and return video information
        Args:
            query (str): Search query
            max_results (int): Maximum number of results
        Returns:
            list: List of video information dictionaries
        """
        try:
            # This is a simplified search - for production, use YouTube API
            search_url = f"https://www.youtube.com/results?search_query={quote(query)}"
            
            # For now, return a placeholder structure
            # In production, you'd parse the YouTube API response
            results = [{
                'title': f"Search results for: {query}",
                'url': search_url,
                'description': f"YouTube search for {query}"
            }]
            
            log_message(f"YouTube search completed: {query}")
            return results
            
        except Exception as e:
            log_message(f"YouTube search failed: {e}", "ERROR")
            return []
    
    def play_spotify_track(self, search_query):
        """
        Search and play Spotify track (requires Spotify app)
        Args:
            search_query (str): Track search query
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Open Spotify search URL
            spotify_search_url = f"https://open.spotify.com/search/{quote(search_query)}"
            webbrowser.open(spotify_search_url)
            
            log_message(f"Opening Spotify search: {search_query}")
            speak(f"Searching for {search_query} on Spotify.")
            
            # Add to history
            self.add_to_history('spotify', search_query)
            self.current_media = {'type': 'spotify', 'title': search_query}
            
            return True
            
        except Exception as e:
            log_message(f"Failed to open Spotify: {e}", "ERROR")
            speak("Sorry, I couldn't open Spotify.")
            return False
    
    def play_local_media(self, file_path):
        """
        Play local media file
        Args:
            file_path (str): Path to media file
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not os.path.exists(file_path):
                speak("Media file not found.")
                return False
            
            # Get file extension to determine media type
            file_ext = os.path.splitext(file_path)[1].lower()
            
            if file_ext in ['.mp3', '.wav', '.flac', '.m4a', '.aac']:
                media_type = 'audio'
            elif file_ext in ['.mp4', '.avi', '.mkv', '.mov', '.wmv']:
                media_type = 'video'
            else:
                speak("Unsupported media format.")
                return False
            
            # Open with default system player
            if os.name == 'nt':  # Windows
                os.startfile(file_path)
            elif os.name == 'posix':  # macOS and Linux
                subprocess.call(['open' if os.uname().sysname == 'Darwin' else 'xdg-open', file_path])
            
            filename = os.path.basename(file_path)
            log_message(f"Playing local {media_type}: {filename}")
            speak(f"Playing {filename}")
            
            # Add to history
            self.add_to_history('local', filename)
            self.current_media = {'type': 'local', 'title': filename, 'path': file_path}
            self.is_playing = True
            
            return True
            
        except Exception as e:
            log_message(f"Failed to play local media: {e}", "ERROR")
            speak("Sorry, I couldn't play the media file.")
            return False
    
    def control_media(self, action):
        """
        Control media playback (play, pause, stop, etc.)
        Args:
            action (str): Control action ('play', 'pause', 'stop', 'next', 'previous')
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Use keyboard shortcuts for media control
            import pyautogui
            
            action = action.lower()
            
            if action in ['play', 'pause', 'playpause']:
                pyautogui.press('playpause')
                self.is_playing = not self.is_playing
                status = "playing" if self.is_playing else "paused"
                speak(f"Media {status}")
                
            elif action == 'stop':
                pyautogui.press('stop')
                self.is_playing = False
                speak("Media stopped")
                
            elif action in ['next', 'skip']:
                pyautogui.press('nexttrack')
                speak("Skipped to next track")
                
            elif action in ['previous', 'back']:
                pyautogui.press('prevtrack')
                speak("Going back to previous track")
                
            elif action in ['volumeup', 'louder']:
                pyautogui.press('volumeup')
                self.volume_level = min(100, self.volume_level + 10)
                speak("Volume increased")
                
            elif action in ['volumedown', 'quieter']:
                pyautogui.press('volumedown')
                self.volume_level = max(0, self.volume_level - 10)
                speak("Volume decreased")
                
            elif action == 'mute':
                pyautogui.press('volumemute')
                speak("Audio muted")
                
            else:
                speak(f"Unknown media control action: {action}")
                return False
            
            log_message(f"Media control executed: {action}")
            return True
            
        except Exception as e:
            log_message(f"Media control failed: {e}", "ERROR")
            speak("Media control failed.")
            return False
    
    def set_volume(self, volume_percent):
        """
        Set system volume
        Args:
            volume_percent (int): Volume level (0-100)
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            volume_percent = max(0, min(100, volume_percent))
            
            if os.name == 'nt':  # Windows
                # Use Windows-specific volume control
                from ctypes import cast, POINTER
                from comtypes import CLSCTX_ALL
                from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume
                
                devices = AudioUtilities.GetSpeakers()
                interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
                volume = cast(interface, POINTER(IAudioEndpointVolume))
                volume.SetMasterScalarVolume(volume_percent / 100, None)
                
            else:
                # Use amixer for Linux/macOS (requires alsa-utils)
                subprocess.run(['amixer', 'set', 'Master', f'{volume_percent}%'], 
                             check=True, capture_output=True)
            
            self.volume_level = volume_percent
            log_message(f"Volume set to {volume_percent}%")
            speak(f"Volume set to {volume_percent} percent")
            
            return True
            
        except Exception as e:
            log_message(f"Failed to set volume: {e}", "ERROR")
            speak("Sorry, I couldn't change the volume.")
            return False
    
    def get_current_media_info(self):
        """
        Get information about currently playing media
        Returns:
            dict: Current media information
        """
        if not self.current_media:
            return {"status": "No media currently playing"}
        
        info = self.current_media.copy()
        info['is_playing'] = self.is_playing
        info['volume'] = self.volume_level
        
        return info
    
    def search_local_media(self, search_term, media_dirs=None):
        """
        Search for local media files
        Args:
            search_term (str): Search term
            media_dirs (list): Directories to search in
        Returns:
            list: List of matching files
        """
        if media_dirs is None:
            # Default media directories
            media_dirs = [
                os.path.expanduser("~/Music"),
                os.path.expanduser("~/Videos"),
                os.path.expanduser("~/Downloads")
            ]
        
        media_extensions = ['.mp3', '.wav', '.flac', '.m4a', '.aac', 
                           '.mp4', '.avi', '.mkv', '.mov', '.wmv']
        
        matching_files = []
        search_term_lower = search_term.lower()
        
        try:
            for directory in media_dirs:
                if not os.path.exists(directory):
                    continue
                
                for root, dirs, files in os.walk(directory):
                    for file in files:
                        file_lower = file.lower()
                        file_ext = os.path.splitext(file)[1].lower()
                        
                        if file_ext in media_extensions and search_term_lower in file_lower:
                            full_path = os.path.join(root, file)
                            matching_files.append({
                                'filename': file,
                                'path': full_path,
                                'directory': root,
                                'size': os.path.getsize(full_path)
                            })
            
            log_message(f"Found {len(matching_files)} local media files matching '{search_term}'")
            return matching_files
            
        except Exception as e:
            log_message(f"Local media search failed: {e}", "ERROR")
            return []
    
    def create_playlist(self, name, items):
        """
        Create a playlist (simplified implementation)
        Args:
            name (str): Playlist name
            items (list): List of media items
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            playlist = {
                'name': name,
                'items': items,
                'created': datetime.now().isoformat(),
                'total_items': len(items)
            }
            
            # In a full implementation, you'd save this to a file
            log_message(f"Playlist '{name}' created with {len(items)} items")
            speak(f"Created playlist '{name}' with {len(items)} items")
            
            return True
            
        except Exception as e:
            log_message(f"Failed to create playlist: {e}", "ERROR")
            return False
    
    def add_to_history(self, media_type, title):
        """Add media to play history"""
        history_entry = {
            'type': media_type,
            'title': title,
            'played_at': datetime.now().isoformat()
        }
        
        self.media_history.append(history_entry)
        
        # Keep only recent history
        if len(self.media_history) > 50:
            self.media_history = self.media_history[-50:]
    
    def get_media_history(self, limit=10):
        """
        Get recent media history
        Args:
            limit (int): Number of recent items to return
        Returns:
            list: Recent media history
        """
        return self.media_history[-limit:] if self.media_history else []
    
    def clear_media_history(self):
        """Clear media play history"""
        self.media_history = []
        log_message("Media history cleared")
        speak("Media history cleared")
    
    def get_media_recommendations(self, based_on_history=True):
        """
        Get media recommendations (simplified)
        Args:
            based_on_history (bool): Whether to base recommendations on history
        Returns:
            list: List of recommendations
        """
        recommendations = []
        
        if based_on_history and self.media_history:
            # Analyze history for patterns (simplified)
            recent_types = [item['type'] for item in self.media_history[-10:]]
            most_common_type = max(set(recent_types), key=recent_types.count)
            
            if most_common_type == 'youtube':
                recommendations = [
                    "Popular music videos",
                    "Trending videos",
                    "Educational content"
                ]
            elif most_common_type == 'spotify':
                recommendations = [
                    "Discover Weekly",
                    "Release Radar",
                    "Daily Mix"
                ]
        else:
            # Generic recommendations
            recommendations = [
                "Popular music",
                "Latest movies",
                "Trending videos",
                "Podcasts"
            ]
        
        return recommendations
    
    def open_media_app(self, app_name):
        """
        Open media application
        Args:
            app_name (str): Name of the app to open
        Returns:
            bool: True if successful, False otherwise
        """
        app_commands = {
            'spotify': {
                'windows': 'spotify.exe',
                'darwin': 'open -a Spotify',
                'linux': 'spotify'
            },
            'youtube': {
                'windows': 'start https://youtube.com',
                'darwin': 'open https://youtube.com',
                'linux': 'xdg-open https://youtube.com'
            },
            'vlc': {
                'windows': 'vlc.exe',
                'darwin': 'open -a VLC',
                'linux': 'vlc'
            }
        }
        
        app_name_lower = app_name.lower()
        
        if app_name_lower not in app_commands:
            speak(f"I don't know how to open {app_name}")
            return False
        
        try:
            import platform
            system = platform.system().lower()
            if system == 'darwin':
                system = 'darwin'
            elif system == 'linux':
                system = 'linux'
            else:
                system = 'windows'
            
            command = app_commands[app_name_lower].get(system)
            
            if command:
                if system == 'windows' and 'start ' in command:
                    subprocess.run(command, shell=True)
                else:
                    subprocess.run(command.split())
                
                log_message(f"Opened {app_name}")
                speak(f"Opening {app_name}")
                return True
            else:
                speak(f"Cannot open {app_name} on this system")
                return False
                
        except Exception as e:
            log_message(f"Failed to open {app_name}: {e}", "ERROR")
            speak(f"Sorry, I couldn't open {app_name}")
            return False

# Create global media handler instance
media_handler = MediaHandler()

# Convenience functions for easy import
def play_youtube(search_query):
    """Play YouTube video"""
    return media_handler.play_youtube_video(search_query)

def play_spotify(search_query):
    """Play Spotify track"""
    return media_handler.play_spotify_track(search_query)

def play_local_media(file_path):
    """Play local media file"""
    return media_handler.play_local_media(file_path)

def control_media(action):
    """Control media playback"""
    return media_handler.control_media(action)

def set_volume(volume_percent):
    """Set system volume"""
    return media_handler.set_volume(volume_percent)

def search_local_media(search_term, media_dirs=None):
    """Search for local media files"""
    return media_handler.search_local_media(search_term, media_dirs)

def get_current_media():
    """Get current media information"""
    return media_handler.get_current_media_info()

def get_media_history(limit=10):
    """Get media play history"""
    return media_handler.get_media_history(limit)

def open_media_app(app_name):
    """Open media application"""
    return media_handler.open_media_app(app_name)

# Log successful module initialization
log_message("Media module initialized successfully")