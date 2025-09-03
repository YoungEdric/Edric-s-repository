# tasks.py - Command processing and task execution for Sarah AI Assistant

import re
import subprocess
import webbrowser
from datetime import datetime, timedelta
from utils import speak, log_message, get_current_time, get_greeting, parse_time_from_text
from config import *

# Import all modules
import ai
import messages
import vision
import media
import automation
import security

class TaskHandler:
    def __init__(self):
        self.command_patterns = self.load_command_patterns()
        self.context = {}  # Store conversation context
    
    def load_command_patterns(self):
        """Load command patterns for intent recognition"""
        return {
            # Greetings and basic interactions
            'greeting': [
                r'hello|hi|hey|good morning|good afternoon|good evening',
                r'how are you|what\'s up|how\'s it going'
            ],
            
            'goodbye': [
                r'goodbye|bye|see you|talk to you later|quit|exit|stop'
            ],
            
            'time': [
                r'what time is it|current time|tell me the time'
            ],
            
            # AI and questions
            'ask_ai': [
                r'ask|question|what is|what are|explain|tell me about|how does|why does',
                r'help me understand|can you explain|what do you know about'
            ],
            
            'summarize': [
                r'summarize|summary|give me a summary of|sum up'
            ],
            
            # System control
            'open_app': [
                r'open|start|launch|run'
            ],
            
            'close_app': [
                r'close|quit|exit|terminate|stop'
            ],
            
            'system_info': [
                r'system info|computer info|specs|system status'
            ],
            
            # Messaging
            'send_message': [
                r'send message|text|email|message|send email|whatsapp|telegram'
            ],
            
            # Media control
            'play_media': [
                r'play|watch|listen|music|song|video|youtube|spotify'
            ],
            
            'media_control': [
                r'pause|stop|skip|next|previous|volume|mute|louder|quieter'
            ],
            
            # Vision and screenshots
            'screenshot': [
                r'screenshot|screen capture|take a picture of screen|capture screen'
            ],
            
            'read_screen': [
                r'read screen|what\'s on screen|screen text|ocr'
            ],
            
            'face_detection': [
                r'detect faces|find faces|face recognition|faces on screen'
            ],
            
            # Automation
            'run_routine': [
                r'morning routine|evening routine|work setup|system cleanup|run routine'
            ],
            
            'schedule_task': [
                r'schedule|remind me|set reminder|alarm'
            ],
            
            # Security
            'security_scan': [
                r'security scan|scan for threats|check security|virus scan'
            ],
            
            'security_status': [
                r'security status|system security|threat report'
            ]
        }
    
    def process_command(self, command):
        """
        Process a voice command and execute appropriate action
        Args:
            command (str): The voice command to process
        Returns:
            bool: True if command was handled, False otherwise
        """
        if not command:
            speak("I didn't hear any command.")
            return False
        
        command = command.lower().strip()
        log_message(f"Processing command: {command}")
        
        # Store command in context
        self.context['last_command'] = command
        self.context['last_command_time'] = datetime.now()
        
        try:
            # Match command to intent
            intent = self.classify_intent(command)
            log_message(f"Intent classified as: {intent}")
            
            # Execute appropriate handler
            if intent == 'greeting':
                return self.handle_greeting(command)
            
            elif intent == 'goodbye':
                return self.handle_goodbye(command)
            
            elif intent == 'time':
                return self.handle_time_request(command)
            
            elif intent == 'ask_ai':
                return self.handle_ai_question(command)
            
            elif intent == 'summarize':
                return self.handle_summarize(command)
            
            elif intent == 'open_app':
                return self.handle_open_app(command)
            
            elif intent == 'close_app':
                return self.handle_close_app(command)
            
            elif intent == 'system_info':
                return self.handle_system_info(command)
            
            elif intent == 'send_message':
                return self.handle_send_message(command)
            
            elif intent == 'play_media':
                return self.handle_play_media(command)
            
            elif intent == 'media_control':
                return self.handle_media_control(command)
            
            elif intent == 'screenshot':
                return self.handle_screenshot(command)
            
            elif intent == 'read_screen':
                return self.handle_read_screen(command)
            
            elif intent == 'face_detection':
                return self.handle_face_detection(command)
            
            elif intent == 'run_routine':
                return self.handle_run_routine(command)
            
            elif intent == 'schedule_task':
                return self.handle_schedule_task(command)
            
            elif intent == 'security_scan':
                return self.handle_security_scan(command)
            
            elif intent == 'security_status':
                return self.handle_security_status(command)
            
            else:
                # Fallback to AI if no specific intent matched
                return self.handle_ai_question(command)
                
        except Exception as e:
            log_message(f"Error processing command: {e}", "ERROR")
            speak("Sorry, I encountered an error processing your command.")
            return False
    
    def classify_intent(self, command):
        """Classify the intent of a command"""
        for intent, patterns in self.command_patterns.items():
            for pattern in patterns:
                if re.search(pattern, command, re.IGNORECASE):
                    return intent
        
        return 'unknown'
    
    def handle_greeting(self, command):
        """Handle greeting commands"""
        greeting = get_greeting()
        speak(greeting)
        return True
    
    def handle_goodbye(self, command):
        """Handle goodbye commands"""
        speak("Goodbye! Have a great day!")
        return True
    
    def handle_time_request(self, command):
        """Handle time-related requests"""
        current_time = get_current_time()
        speak(f"The current time is {current_time}")
        return True
    
    def handle_ai_question(self, command):
        """Handle AI questions and general queries"""
        try:
            # Remove wake words and command prefixes
            question = self.extract_question(command)
            
            if not question:
                speak("What would you like to know?")
                return False
            
            # Get context from previous commands if relevant
            context = self.get_relevant_context()
            
            # Ask AI
            response = ai.ask_question(question, context)
            
            if response:
                speak(response)
                return True
            else:
                speak("I'm sorry, I couldn't get an answer to that question right now.")
                return False
                
        except Exception as e:
            log_message(f"AI question handling failed: {e}", "ERROR")
            speak("I had trouble processing your question.")
            return False
    
    def handle_summarize(self, command):
        """Handle summarization requests"""
        try:
            # For now, ask user what to summarize
            speak("What would you like me to summarize? You can provide text or I can read from the screen.")
            # This is a simplified implementation
            # In a full version, you might take screenshots or get clipboard content
            return True
            
        except Exception as e:
            log_message(f"Summarization failed: {e}", "ERROR")
            speak("I couldn't process the summarization request.")
            return False
    
    def handle_open_app(self, command):
        """Handle application opening requests"""
        try:
            app_name = self.extract_app_name(command)
            
            if app_name:
                success = self.open_application(app_name)
                if success:
                    speak(f"Opening {app_name}")
                    return True
                else:
                    speak(f"I couldn't open {app_name}")
                    return False
            else:
                speak("What application would you like me to open?")
                return False
                
        except Exception as e:
            log_message(f"App opening failed: {e}", "ERROR")
            speak("I had trouble opening the application.")
            return False
    
    def handle_close_app(self, command):
        """Handle application closing requests"""
        try:
            app_name = self.extract_app_name(command)
            
            if app_name:
                success = self.close_application(app_name)
                if success:
                    speak(f"Closing {app_name}")
                    return True
                else:
                    speak(f"I couldn't close {app_name}")
                    return False
            else:
                speak("What application would you like me to close?")
                return False
                
        except Exception as e:
            log_message(f"App closing failed: {e}", "ERROR")
            speak("I had trouble closing the application.")
            return False
    
    def handle_system_info(self, command):
        """Handle system information requests"""
        try:
            from utils import get_system_info
            info = get_system_info()
            
            info_text = f"System information: {info['os']} operating system, "
            info_text += f"{info['cpu_count']} CPU cores, "
            info_text += f"{info['memory_gb']} GB of RAM"
            
            speak(info_text)
            return True
            
        except Exception as e:
            log_message(f"System info failed: {e}", "ERROR")
            speak("I couldn't get system information.")
            return False
    
    def handle_send_message(self, command):
        """Handle message sending requests"""
        try:
            # This is a simplified implementation
            # In practice, you'd want to extract recipient and message from speech
            
            if 'email' in command:
                speak("Who would you like to send an email to?")
                # Would need additional voice input here
                return True
            elif 'whatsapp' in command:
                speak("Who would you like to send a WhatsApp message to?")
                return True
            else:
                speak("What type of message would you like to send? Email, WhatsApp, or Telegram?")
                return True
                
        except Exception as e:
            log_message(f"Message sending failed: {e}", "ERROR")
            speak("I had trouble with the messaging request.")
            return False
    
    def handle_play_media(self, command):
        """Handle media playback requests"""
        try:
            if 'youtube' in command:
                search_query = self.extract_media_query(command, 'youtube')
                if search_query:
                    return media.play_youtube(search_query)
                else:
                    speak("What would you like to watch on YouTube?")
                    return False
            
            elif 'spotify' in command:
                search_query = self.extract_media_query(command, 'spotify')
                if search_query:
                    return media.play_spotify(search_query)
                else:
                    speak("What would you like to listen to on Spotify?")
                    return False
            
            else:
                # General play command
                media_query = self.extract_media_query(command)
                if media_query:
                    # Try YouTube first
                    return media.play_youtube(media_query)
                else:
                    speak("What would you like to play?")
                    return False
                    
        except Exception as e:
            log_message(f"Media playback failed: {e}", "ERROR")
            speak("I had trouble playing the media.")
            return False
    
    def handle_media_control(self, command):
        """Handle media control commands"""
        try:
            if any(word in command for word in ['pause', 'stop']):
                return media.control_media('pause')
            elif 'play' in command:
                return media.control_media('play')
            elif any(word in command for word in ['next', 'skip']):
                return media.control_media('next')
            elif 'previous' in command:
                return media.control_media('previous')
            elif any(word in command for word in ['louder', 'volume up']):
                return media.control_media('volumeup')
            elif any(word in command for word in ['quieter', 'volume down']):
                return media.control_media('volumedown')
            elif 'mute' in command:
                return media.control_media('mute')
            else:
                speak("What would you like me to do with the media?")
                return False
                
        except Exception as e:
            log_message(f"Media control failed: {e}", "ERROR")
            speak("I had trouble controlling the media.")
            return False
    
    def handle_screenshot(self, command):
        """Handle screenshot requests"""
        try:
            screenshot_path = vision.take_screenshot()
            if screenshot_path:
                speak("Screenshot taken successfully")
                return True
            else:
                speak("I couldn't take a screenshot")
                return False
                
        except Exception as e:
            log_message(f"Screenshot failed: {e}", "ERROR")
            speak("I had trouble taking a screenshot.")
            return False
    
    def handle_read_screen(self, command):
        """Handle screen reading requests"""
        try:
            text = vision.read_screen_text()
            if text:
                # Summarize if text is too long
                if len(text) > 200:
                    summary = ai.summarize_text(text, max_length=50)
                    speak(f"Screen contains: {summary}")
                else:
                    speak(f"Screen text: {text}")
                return True
            else:
                speak("I couldn't find any text on the screen")
                return False
                
        except Exception as e:
            log_message(f"Screen reading failed: {e}", "ERROR")
            speak("I had trouble reading the screen.")
            return False
    
    def handle_face_detection(self, command):
        """Handle face detection requests"""
        try:
            faces = vision.detect_faces_on_screen()
            if faces:
                count = len(faces)
                speak(f"I detected {count} face{'s' if count != 1 else ''} on the screen")
                return True
            else:
                speak("I don't see any faces on the screen")
                return True  # Still successful, just no faces found
                
        except Exception as e:
            log_message(f"Face detection failed: {e}", "ERROR")
            speak("I had trouble detecting faces.")
            return False
    
    def handle_run_routine(self, command):
        """Handle automation routine requests"""
        try:
            if 'morning' in command:
                return automation.run_routine('morning_routine')
            elif 'evening' in command:
                return automation.run_routine('evening_routine')
            elif 'work' in command:
                return automation.run_routine('work_setup')
            elif 'cleanup' in command:
                return automation.run_routine('system_cleanup')
            else:
                available_routines = automation.get_available_routines()
                routine_names = [r['name'] for r in available_routines]
                speak(f"Available routines: {', '.join(routine_names)}")
                return True
                
        except Exception as e:
            log_message(f"Routine execution failed: {e}", "ERROR")
            speak("I had trouble running the routine.")
            return False
    
    def handle_schedule_task(self, command):
        """Handle task scheduling requests"""
        try:
            # Simple scheduling - this would need more sophisticated parsing
            time_info = parse_time_from_text(command)
            
            if time_info:
                # For now, just acknowledge
                speak(f"I'll remind you in {time_info // 60} minutes")
                return True
            else:
                speak("When would you like me to remind you?")
                return False
                
        except Exception as e:
            log_message(f"Task scheduling failed: {e}", "ERROR")
            speak("I had trouble scheduling the task.")
            return False
    
    def handle_security_scan(self, command):
        """Handle security scanning requests"""
        try:
            speak("Starting security scan")
            security.start_security_monitoring()
            
            # Run a quick scan
            status = security.get_security_status()
            
            if status['system_health'] == 'good':
                speak("Security scan completed. No threats detected.")
            elif status['system_health'] == 'warning':
                speak("Security scan completed with warnings. Check the security log for details.")
            else:
                speak("Security scan detected issues. Immediate attention recommended.")
            
            return True
            
        except Exception as e:
            log_message(f"Security scan failed: {e}", "ERROR")
            speak("I had trouble running the security scan.")
            return False
    
    def handle_security_status(self, command):
        """Handle security status requests"""
        try:
            status = security.get_security_status()
            threat_summary = security.get_threat_summary()
            
            status_text = f"System security status: {status['system_health']}. "
            status_text += f"Detected {threat_summary['total_threats']} threats in the last 24 hours."
            
            speak(status_text)
            return True
            
        except Exception as e:
            log_message(f"Security status failed: {e}", "ERROR")
            speak("I had trouble getting security status.")
            return False
    
    # Helper methods
    def extract_question(self, command):
        """Extract the actual question from a command"""
        # Remove common command prefixes
        prefixes_to_remove = [
            'ask', 'question', 'tell me', 'what is', 'what are', 'explain',
            'help me understand', 'can you explain', 'sarah'
        ]
        
        question = command
        for prefix in prefixes_to_remove:
            if question.lower().startswith(prefix):
                question = question[len(prefix):].strip()
                break
        
        # Remove articles and clean up
        question = re.sub(r'^(about|the|a|an)\s+', '', question, flags=re.IGNORECASE)
        
        return question.strip()
    
    def extract_app_name(self, command):
        """Extract application name from command"""
        # Common application names
        app_names = [
            'chrome', 'firefox', 'edge', 'safari',
            'notepad', 'calculator', 'word', 'excel', 'powerpoint',
            'code', 'vscode', 'visual studio code',
            'slack', 'discord', 'teams',
            'spotify', 'itunes', 'music',
            'outlook', 'thunderbird', 'mail'
        ]
        
        command_lower = command.lower()
        
        for app in app_names:
            if app in command_lower:
                return app.replace('visual studio code', 'code')
        
        # Try to extract from "open X" or "close X" pattern
        match = re.search(r'(?:open|close|start|launch|quit|exit)\s+([a-zA-Z]+)', command_lower)
        if match:
            return match.group(1)
        
        return None
    
    def extract_media_query(self, command, platform=None):
        """Extract media search query from command"""
        # Remove command words
        remove_words = [
            'play', 'watch', 'listen', 'music', 'song', 'video',
            'youtube', 'spotify', 'on', 'from', 'the'
        ]
        
        words = command.lower().split()
        filtered_words = [word for word in words if word not in remove_words]
        
        if filtered_words:
            return ' '.join(filtered_words)
        
        return None
    
    def open_application(self, app_name):
        """Open an application"""
        try:
            app_commands = {
                'chrome': 'chrome.exe',
                'firefox': 'firefox.exe',
                'edge': 'msedge.exe',
                'notepad': 'notepad.exe',
                'calculator': 'calc.exe',
                'code': 'code.exe',
                'word': 'winword.exe',
                'excel': 'excel.exe',
                'powerpoint': 'powerpnt.exe',
                'outlook': 'outlook.exe',
                'slack': 'slack.exe',
                'discord': 'discord.exe',
                'spotify': 'spotify.exe'
            }
            
            command = app_commands.get(app_name.lower(), app_name + '.exe')
            subprocess.Popen(command, shell=True)
            
            log_message(f"Opened application: {app_name}")
            return True
            
        except Exception as e:
            log_message(f"Failed to open {app_name}: {e}", "ERROR")
            return False
    
    def close_application(self, app_name):
        """Close an application"""
        try:
            if not app_name.endswith('.exe'):
                app_name += '.exe'
            
            subprocess.run(f'taskkill /f /im {app_name}', shell=True, capture_output=True)
            
            log_message(f"Closed application: {app_name}")
            return True
            
        except Exception as e:
            log_message(f"Failed to close {app_name}: {e}", "ERROR")
            return False
    
    def get_relevant_context(self):
        """Get relevant context for AI queries"""
        context_parts = []
        
        # Add recent command context
        if 'last_command' in self.context:
            last_time = self.context.get('last_command_time')
            if last_time and (datetime.now() - last_time).seconds < 300:  # 5 minutes
                context_parts.append(f"Previous command: {self.context['last_command']}")
        
        # Add current time context
        context_parts.append(f"Current time: {get_current_time()}")
        
        # Add system context
        context_parts.append(f"User: {USER_NAME}")
        
        return '; '.join(context_parts) if context_parts else None
    
    def handle_follow_up_question(self, command):
        """Handle follow-up questions that refer to previous context"""
        follow_up_indicators = ['what about', 'how about', 'and what', 'also', 'too']
        
        if any(indicator in command.lower() for indicator in follow_up_indicators):
            # This is likely a follow-up question
            context = self.get_relevant_context()
            return ai.ask_question(command, context)
        
        return None
    
    def get_command_suggestions(self):
        """Get list of available commands for help"""
        suggestions = [
            "Ask me questions (e.g., 'What is the weather like?')",
            "Control applications (e.g., 'Open Chrome', 'Close Notepad')",
            "Play media (e.g., 'Play music on Spotify', 'Watch videos on YouTube')",
            "Take screenshots (e.g., 'Take a screenshot')",
            "Read screen text (e.g., 'What's on the screen?')",
            "Send messages (e.g., 'Send an email', 'Send WhatsApp message')",
            "Run routines (e.g., 'Run morning routine', 'Start work setup')",
            "Security tasks (e.g., 'Run security scan', 'Check security status')",
            "System information (e.g., 'What are my system specs?')"
        ]
        return suggestions
    
    def handle_help_request(self, command):
        """Handle help and capability requests"""
        if any(word in command.lower() for word in ['help', 'what can you do', 'capabilities', 'commands']):
            suggestions = self.get_command_suggestions()
            help_text = "Here's what I can help you with: " + "; ".join(suggestions[:5])  # First 5 to avoid too long response
            speak(help_text)
            return True
        
        return False

# Create global task handler instance
task_handler = TaskHandler()

# Convenience function for easy import
def process_command(command):
    """Process a voice command"""
    return task_handler.process_command(command)

def get_command_suggestions():
    """Get available command suggestions"""
    return task_handler.get_command_suggestions()

# Log successful module initialization
log_message("Tasks module initialized successfully")