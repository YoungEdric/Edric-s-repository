# voice.py - Speech recognition and text-to-speech for Sarah AI Assistant

import speech_recognition as sr
import threading
import time
from utils import speak, log_message, retry_operation, normalize_text
from config import *

class VoiceHandler:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.is_listening = False
        self.is_wake_word_active = True
        self.wake_word_detected = False
        
        # Adjust for ambient noise
        self.calibrate_microphone()
    
    def calibrate_microphone(self):
        """Calibrate microphone for ambient noise"""
        try:
            log_message("Calibrating microphone for ambient noise...")
            with self.microphone as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=2)
            log_message("Microphone calibration complete")
        except Exception as e:
            log_message(f"Microphone calibration failed: {e}", "ERROR")
    
    def listen_for_wake_word(self, callback=None):
        """
        Continuously listen for wake words
        Args:
            callback: Function to call when wake word is detected
        """
        def listen_loop():
            while self.is_wake_word_active:
                try:
                    with self.microphone as source:
                        # Listen for wake word with short timeout
                        audio = self.recognizer.listen(
                            source, 
                            timeout=WAKE_WORD_TIMEOUT,
                            phrase_time_limit=2
                        )
                    
                    # Recognize speech
                    text = self.recognizer.recognize_google(
                        audio, 
                        language=RECOGNITION_LANGUAGE
                    ).lower()
                    
                    log_message(f"Heard: {text}")
                    
                    # Check for wake words
                    for wake_word in WAKE_WORDS:
                        if wake_word.lower() in text:
                            log_message(f"Wake word detected: {wake_word}")
                            self.wake_word_detected = True
                            
                            if callback:
                                callback()
                            return
                
                except sr.WaitTimeoutError:
                    continue  # Normal timeout, keep listening
                except sr.UnknownValueError:
                    continue  # Couldn't understand audio
                except sr.RequestError as e:
                    log_message(f"Speech recognition service error: {e}", "ERROR")
                    time.sleep(1)
                except Exception as e:
                    log_message(f"Unexpected error in wake word detection: {e}", "ERROR")
                    time.sleep(1)
        
        # Start listening in a separate thread
        listen_thread = threading.Thread(target=listen_loop, daemon=True)
        listen_thread.start()
        log_message("Wake word detection started")
    
    def listen_for_command(self, timeout=None):
        """
        Listen for a voice command after wake word
        Args:
            timeout: Maximum time to wait for command
        Returns:
            str: Recognized command text or None if failed
        """
        if timeout is None:
            timeout = MICROPHONE_PHRASE_TIMEOUT
        
        def listen_operation():
            with self.microphone as source:
                log_message("Listening for command...")
                audio = self.recognizer.listen(
                    source,
                    timeout=MICROPHONE_TIMEOUT,
                    phrase_time_limit=timeout
                )
            
            # Recognize the command
            command = self.recognizer.recognize_google(
                audio,
                language=RECOGNITION_LANGUAGE
            )
            
            log_message(f"Command recognized: {command}")
            return command.lower()
        
        try:
            command = retry_operation(listen_operation)
            return command
        
        except sr.WaitTimeoutError:
            log_message("No command heard within timeout")
            speak("I didn't hear anything. Please try again.")
            return None
        
        except sr.UnknownValueError:
            log_message("Could not understand the command")
            speak("Sorry, I didn't understand that. Could you repeat?")
            return None
        
        except sr.RequestError as e:
            log_message(f"Speech recognition service error: {e}", "ERROR")
            speak("I'm having trouble with speech recognition right now.")
            return None
    
    def start_conversation_mode(self, command_handler):
        """
        Start continuous conversation mode
        Args:
            command_handler: Function to handle recognized commands
        """
        self.is_listening = True
        log_message("Starting conversation mode")
        
        def conversation_loop():
            consecutive_failures = 0
            max_failures = 5
            
            while self.is_listening:
                try:
                    command = self.listen_for_command(timeout=10)
                    
                    if command:
                        consecutive_failures = 0  # Reset failure count
                        
                        # Check for exit commands
                        exit_commands = ['stop', 'exit', 'quit', 'goodbye', 'bye']
                        if any(exit_cmd in command for exit_cmd in exit_commands):
                            speak("Goodbye!")
                            self.stop_listening()
                            break
                        
                        # Handle the command
                        if command_handler:
                            command_handler(command)
                    else:
                        consecutive_failures += 1
                        if consecutive_failures >= max_failures:
                            log_message("Too many consecutive failures, stopping conversation mode")
                            speak("I'm having trouble hearing you. Going back to wake word mode.")
                            self.stop_listening()
                            break
                
                except Exception as e:
                    log_message(f"Error in conversation loop: {e}", "ERROR")
                    consecutive_failures += 1
                    if consecutive_failures >= max_failures:
                        self.stop_listening()
                        break
        
        conversation_thread = threading.Thread(target=conversation_loop, daemon=True)
        conversation_thread.start()
    
    def stop_listening(self):
        """Stop continuous listening mode"""
        self.is_listening = False
        log_message("Stopped conversation mode")
    
    def stop_wake_word_detection(self):
        """Stop wake word detection"""
        self.is_wake_word_active = False
        log_message("Stopped wake word detection")
    
    def is_wake_word_detected(self):
        """Check if wake word was detected"""
        if self.wake_word_detected:
            self.wake_word_detected = False  # Reset flag
            return True
        return False
    
    def test_microphone(self):
        """Test microphone and speech recognition"""
        try:
            speak("Testing microphone. Please say something.")
            
            with self.microphone as source:
                log_message("Listening for test...")
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=3)
            
            text = self.recognizer.recognize_google(audio, language=RECOGNITION_LANGUAGE)
            log_message(f"Test successful. Heard: {text}")
            speak(f"I heard you say: {text}")
            return True
            
        except sr.WaitTimeoutError:
            speak("No audio detected. Please check your microphone.")
            return False
        
        except sr.UnknownValueError:
            speak("I heard audio but couldn't understand it. Please speak clearly.")
            return False
        
        except sr.RequestError as e:
            log_message(f"Speech recognition test failed: {e}", "ERROR")
            speak("Speech recognition service is not available.")
            return False
    
    def get_available_microphones(self):
        """Get list of available microphones"""
        microphones = []
        for index, name in enumerate(sr.Microphone.list_microphone_names()):
            microphones.append({
                'index': index,
                'name': name
            })
        return microphones
    
    def set_microphone_by_index(self, index):
        """Set microphone by device index"""
        try:
            self.microphone = sr.Microphone(device_index=index)
            self.calibrate_microphone()
            log_message(f"Microphone set to device index: {index}")
            return True
        except Exception as e:
            log_message(f"Failed to set microphone: {e}", "ERROR")
            return False
    
    def adjust_recognition_sensitivity(self, energy_threshold=None, dynamic_energy=True):
        """
        Adjust speech recognition sensitivity
        Args:
            energy_threshold: Minimum audio energy to consider for recording
            dynamic_energy: Whether to automatically adjust energy threshold
        """
        if energy_threshold is not None:
            self.recognizer.energy_threshold = energy_threshold
        
        self.recognizer.dynamic_energy_threshold = dynamic_energy
        log_message(f"Recognition sensitivity adjusted: threshold={energy_threshold}, dynamic={dynamic_energy}")
    
    def save_audio_to_file(self, filename="last_recording.wav"):
        """
        Record and save audio to file for debugging
        Args:
            filename: Name of the file to save audio
        """
        try:
            with self.microphone as source:
                speak("Recording... speak now.")
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=10)
            
            # Save audio data
            with open(filename, 'wb') as f:
                f.write(audio.get_wav_data())
            
            log_message(f"Audio saved to {filename}")
            speak(f"Audio recorded and saved to {filename}")
            return True
            
        except Exception as e:
            log_message(f"Failed to save audio: {e}", "ERROR")
            speak("Failed to record audio.")
            return False

# Create global voice handler instance
voice_handler = VoiceHandler()

# Convenience functions for easy import
def listen_for_wake_word(callback=None):
    """Start listening for wake words"""
    return voice_handler.listen_for_wake_word(callback)

def listen_for_command(timeout=None):
    """Listen for a voice command"""
    return voice_handler.listen_for_command(timeout)

def start_conversation_mode(command_handler):
    """Start continuous conversation mode"""
    return voice_handler.start_conversation_mode(command_handler)

def stop_listening():
    """Stop all listening modes"""
    voice_handler.stop_listening()
    voice_handler.stop_wake_word_detection()

def test_microphone():
    """Test microphone functionality"""
    return voice_handler.test_microphone()

def get_available_microphones():
    """Get list of available microphones"""
    return voice_handler.get_available_microphones()

# Log successful module initialization
log_message("Voice module initialized successfully")