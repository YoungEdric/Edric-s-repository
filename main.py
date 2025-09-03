# main.py - Main entry point for Sarah AI Assistant

import sys
import time
import threading
import signal
from datetime import datetime

# Import Sarah modules
from utils import speak, log_message, get_greeting, setup_logging
from voice import voice_handler, listen_for_wake_word, listen_for_command
from tasks import process_command
from config import *

class SarahAssistant:
    def __init__(self):
        self.running = False
        self.wake_word_active = True
        self.conversation_mode = False
        self.setup_signal_handlers()
        
        log_message("Sarah AI Assistant initializing...")
        
    def setup_signal_handlers(self):
        """Setup signal handlers for graceful shutdown"""
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        log_message(f"Received signal {signum}, shutting down gracefully...")
        self.shutdown()
        sys.exit(0)
    
    def startup_sequence(self):
        """Perform startup checks and initialization"""
        log_message("Starting Sarah AI Assistant startup sequence...")
        
        try:
            # Test voice system
            speak("Initializing Sarah AI Assistant...")
            
            # Perform system checks
            self.perform_system_checks()
            
            # Greet user
            greeting = get_greeting()
            startup_message = f"{greeting} Sarah AI Assistant is now active and listening for wake words."
            speak(startup_message)
            
            log_message("Startup sequence completed successfully")
            return True
            
        except Exception as e:
            log_message(f"Startup sequence failed: {e}", "ERROR")
            speak("I encountered an error during startup. Please check the logs.")
            return False
    
    def perform_system_checks(self):
        """Perform basic system checks"""
        log_message("Performing system checks...")
        
        # Test microphone
        try:
            from voice import test_microphone
            if DEBUG_MODE:
                log_message("Microphone test available in debug mode")
        except Exception as e:
            log_message(f"Microphone test failed: {e}", "WARNING")
        
        # Check AI service
        try:
            from ai import is_ai_available
            if is_ai_available():
                log_message("AI service: Available")
            else:
                log_message("AI service: Not available - check API key", "WARNING")
        except Exception as e:
            log_message(f"AI service check failed: {e}", "WARNING")
        
        # Check messaging services
        try:
            from messages import test_messaging_services
            service_status = test_messaging_services()
            for service, status in service_status.items():
                status_text = "Available" if status else "Not configured"
                log_message(f"{service.title()} service: {status_text}")
        except Exception as e:
            log_message(f"Messaging service check failed: {e}", "WARNING")
        
        log_message("System checks completed")
    
    def start(self):
        """Start the Sarah AI Assistant"""
        if self.running:
            log_message("Sarah is already running")
            return
        
        self.running = True
        
        # Perform startup sequence
        if not self.startup_sequence():
            self.running = False
            return False
        
        try:
            # Start main loop
            self.main_loop()
            
        except KeyboardInterrupt:
            log_message("Received keyboard interrupt")
            self.shutdown()
        except Exception as e:
            log_message(f"Fatal error in main loop: {e}", "ERROR")
            self.shutdown()
        
        return True
    
    def main_loop(self):
        """Main application loop"""
        log_message("Entering main loop - listening for wake words")
        
        while self.running:
            try:
                if self.wake_word_active:
                    # Listen for wake word
                    self.listen_for_wake_word()
                else:
                    # If wake word detection is disabled, wait
                    time.sleep(1)
                    
            except Exception as e:
                log_message(f"Error in main loop: {e}", "ERROR")
                time.sleep(1)
    
    def listen_for_wake_word(self):
        """Listen for wake word and handle activation"""
        try:
            log_message("Listening for wake word...")
            
            # Set up wake word detection
            wake_word_detected = threading.Event()
            
            def wake_word_callback():
                wake_word_detected.set()
            
            # Start listening for wake word
            voice_handler.listen_for_wake_word(wake_word_callback)
            
            # Wait for wake word detection
            while self.running and self.wake_word_active:
                if wake_word_detected.wait(timeout=1.0):
                    log_message("Wake word detected!")
                    self.handle_wake_word_activation()
                    wake_word_detected.clear()
                    break
                
        except Exception as e:
            log_message(f"Wake word detection error: {e}", "ERROR")
            time.sleep(1)
    
    def handle_wake_word_activation(self):
        """Handle wake word activation and get command"""
        try:
            # Acknowledge wake word
            speak("Yes?")
            
            # Listen for command
            command = listen_for_command(timeout=10)
            
            if command:
                log_message(f"Command received: {command}")
                
                # Process the command
                success = process_command(command)
                
                if not success:
                    speak("I'm sorry, I couldn't complete that task.")
                
                # Check if user wants to enter conversation mode
                if any(phrase in command.lower() for phrase in ['let\'s chat', 'conversation mode', 'keep listening']):
                    self.enter_conversation_mode()
                    
            else:
                log_message("No command received after wake word")
                speak("I didn't hear anything. Try saying my name again if you need help.")
                
        except Exception as e:
            log_message(f"Wake word activation handling failed: {e}", "ERROR")
            speak("Sorry, I had trouble processing your request.")
    
    def enter_conversation_mode(self):
        """Enter continuous conversation mode"""
        log_message("Entering conversation mode")
        speak("Entering conversation mode. I'll keep listening until you say goodbye.")
        
        self.conversation_mode = True
        
        try:
            # Start continuous listening
            def command_handler(command):
                if command:
                    success = process_command(command)
                    if not success:
                        speak("I'm sorry, I couldn't complete that task.")
            
            voice_handler.start_conversation_mode(command_handler)
            
            # Wait until conversation mode ends
            while self.conversation_mode and voice_handler.is_listening:
                time.sleep(1)
            
            log_message("Exited conversation mode")
            speak("Conversation mode ended. I'm back to listening for wake words.")
            
        except Exception as e:
            log_message(f"Conversation mode error: {e}", "ERROR")
            speak("There was an issue with conversation mode.")
        finally:
            self.conversation_mode = False
    
    def shutdown(self):
        """Shutdown Sarah AI Assistant gracefully"""
        if not self.running:
            return
        
        log_message("Shutting down Sarah AI Assistant...")
        speak("Goodbye! Sarah AI Assistant is shutting down.")
        
        self.running = False
        self.wake_word_active = False
        self.conversation_mode = False
        
        try:
            # Stop voice handler
            voice_handler.stop_listening()
            voice_handler.stop_wake_word_detection()
            
            # Stop any running services
            from security import stop_security_monitoring
            stop_security_monitoring()
            
            log_message("Sarah AI Assistant shutdown completed")
            
        except Exception as e:
            log_message(f"Error during shutdown: {e}", "ERROR")
    
    def restart(self):
        """Restart Sarah AI Assistant"""
        log_message("Restarting Sarah AI Assistant...")
        speak("Restarting...")
        
        self.shutdown()
        time.sleep(2)
        
        # Reset state
        self.__init__()
        self.start()
    
    def get_status(self):
        """Get current status of Sarah"""
        return {
            'running': self.running,
            'wake_word_active': self.wake_word_active,
            'conversation_mode': self.conversation_mode,
            'uptime': datetime.now().isoformat()
        }
    
    def toggle_wake_word_detection(self):
        """Toggle wake word detection on/off"""
        self.wake_word_active = not self.wake_word_active
        status = "enabled" if self.wake_word_active else "disabled"
        speak(f"Wake word detection {status}")
        log_message(f"Wake word detection {status}")
    
    def run_diagnostic(self):
        """Run system diagnostic"""
        log_message("Running system diagnostic...")
        speak("Running system diagnostic...")
        
        try:
            # Test voice system
            from voice import test_microphone
            mic_test = test_microphone()
            
            # Test AI
            from ai import is_ai_available
            ai_available = is_ai_available()
            
            # Test modules
            modules_status = {
                'voice': mic_test,
                'ai': ai_available,
                'tasks': True,  # Always available
                'utils': True   # Always available
            }
            
            # Report results
            working_modules = sum(modules_status.values())
            total_modules = len(modules_status)
            
            diagnostic_result = f"Diagnostic complete. {working_modules} out of {total_modules} modules working properly."
            speak(diagnostic_result)
            log_message(f"Diagnostic results: {modules_status}")
            
            return modules_status
            
        except Exception as e:
            log_message(f"Diagnostic failed: {e}", "ERROR")
            speak("Diagnostic encountered errors. Check the logs for details.")
            return {}

def main():
    """Main entry point"""
    print("=" * 50)
    print("      Sarah AI Voice Assistant")
    print("=" * 50)
    print(f"Starting up at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("Press Ctrl+C to shutdown gracefully")
    print("=" * 50)
    
    # Initialize logging
    setup_logging()
    
    try:
        # Create and start Sarah
        sarah = SarahAssistant()
        success = sarah.start()
        
        if not success:
            print("\nFailed to start Sarah AI Assistant")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
        sys.exit(0)
    except Exception as e:
        print(f"\nFatal error: {e}")
        log_message(f"Fatal error in main: {e}", "ERROR")
        sys.exit(1)

def run_test_mode():
    """Run Sarah in test mode for development"""
    print("Running Sarah in test mode...")
    
    # Test individual components
    try:
        # Test voice
        from voice import test_microphone
        print("Testing microphone...")
        test_microphone()
        
        # Test AI (if configured)
        from ai import is_ai_available, ask_question
        if is_ai_available():
            print("Testing AI...")
            response = ask_question("Hello, this is a test")
            print(f"AI Response: {response}")
        
        # Test basic command processing
        from tasks import process_command
        print("Testing command processing...")
        process_command("what time is it")
        
        print("Test mode completed successfully!")
        
    except Exception as e:
        print(f"Test mode failed: {e}")

if __name__ == "__main__":
    # Check for command line arguments
    if len(sys.argv) > 1:
        if sys.argv[1] == "--test":
            run_test_mode()
        elif sys.argv[1] == "--help":
            print("Sarah AI Assistant")
            print("Usage: python main.py [options]")
            print("Options:")
            print("  --test    Run in test mode")
            print("  --help    Show this help message")
        else:
            print(f"Unknown option: {sys.argv[1]}")
            print("Use --help for available options")
    else:
        # Normal startup
        main()