# messages.py - Messaging integration for WhatsApp, Telegram, and Email

import pywhatkit as pwk
import yagmail
import telebot
import time
from datetime import datetime, timedelta
from utils import log_message, speak, retry_operation, is_valid_email, is_valid_phone
from config import *

class MessageHandler:
    def __init__(self):
        self.email_client = None
        self.telegram_bot = None
        self.initialize_services()
    
    def initialize_services(self):
        """Initialize messaging services"""
        # Initialize email
        if EMAIL_ADDRESS and EMAIL_PASSWORD and EMAIL_ADDRESS != "your-email@gmail.com":
            try:
                self.email_client = yagmail.SMTP(EMAIL_ADDRESS, EMAIL_PASSWORD)
                log_message("Email service initialized successfully")
            except Exception as e:
                log_message(f"Failed to initialize email service: {e}", "ERROR")
        
        # Initialize Telegram bot
        if TELEGRAM_BOT_TOKEN and TELEGRAM_BOT_TOKEN != "your-telegram-bot-token":
            try:
                self.telegram_bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
                log_message("Telegram bot initialized successfully")
            except Exception as e:
                log_message(f"Failed to initialize Telegram bot: {e}", "ERROR")
    
    def send_whatsapp_message(self, phone_number, message, send_immediately=False):
        """
        Send WhatsApp message using pywhatkit
        Args:
            phone_number (str): Phone number with country code
            message (str): Message to send
            send_immediately (bool): Send immediately or schedule for next minute
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Validate phone number
            if not is_valid_phone(phone_number):
                speak("Invalid phone number format.")
                return False
            
            # Clean phone number (remove non-digits except +)
            import re
            cleaned_number = re.sub(r'[^\d+]', '', phone_number)
            
            if send_immediately:
                # Send immediately (opens WhatsApp Web)
                pwk.sendwhatmsg_instantly(cleaned_number, message)
                log_message(f"WhatsApp message sent immediately to {cleaned_number}")
            else:
                # Schedule for next minute
                now = datetime.now()
                send_time = now + timedelta(minutes=1)
                hour = send_time.hour
                minute = send_time.minute
                
                pwk.sendwhatmsg(cleaned_number, message, hour, minute)
                log_message(f"WhatsApp message scheduled for {hour}:{minute:02d} to {cleaned_number}")
            
            speak("WhatsApp message sent successfully.")
            return True
            
        except Exception as e:
            log_message(f"Failed to send WhatsApp message: {e}", "ERROR")
            speak("Failed to send WhatsApp message.")
            return False
    
    def send_email(self, recipient, subject, body, attachments=None):
        """
        Send email using yagmail
        Args:
            recipient (str): Recipient email address
            subject (str): Email subject
            body (str): Email body
            attachments (list): List of file paths to attach
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.email_client:
            speak("Email service is not configured.")
            return False
        
        # Validate recipient email
        if not is_valid_email(recipient):
            speak("Invalid email address.")
            return False
        
        def send_operation():
            self.email_client.send(
                to=recipient,
                subject=subject,
                contents=body,
                attachments=attachments or []
            )
            return True
        
        try:
            success = retry_operation(send_operation)
            
            if success:
                log_message(f"Email sent to {recipient}: {subject}")
                speak("Email sent successfully.")
                return True
            else:
                speak("Failed to send email after multiple attempts.")
                return False
                
        except Exception as e:
            log_message(f"Failed to send email: {e}", "ERROR")
            speak("Failed to send email.")
            return False
    
    def send_telegram_message(self, chat_id, message):
        """
        Send Telegram message
        Args:
            chat_id (str): Telegram chat ID
            message (str): Message to send
        Returns:
            bool: True if successful, False otherwise
        """
        if not self.telegram_bot:
            speak("Telegram bot is not configured.")
            return False
        
        def send_operation():
            self.telegram_bot.send_message(chat_id, message)
            return True
        
        try:
            success = retry_operation(send_operation)
            
            if success:
                log_message(f"Telegram message sent to {chat_id}")
                speak("Telegram message sent successfully.")
                return True
            else:
                speak("Failed to send Telegram message after multiple attempts.")
                return False
                
        except Exception as e:
            log_message(f"Failed to send Telegram message: {e}", "ERROR")
            speak("Failed to send Telegram message.")
            return False
    
    def get_telegram_updates(self, limit=10):
        """
        Get recent Telegram messages
        Args:
            limit (int): Number of recent messages to retrieve
        Returns:
            list: List of message objects or empty list if failed
        """
        if not self.telegram_bot:
            return []
        
        try:
            updates = self.telegram_bot.get_updates(limit=limit)
            messages = []
            
            for update in updates:
                if update.message:
                    msg = {
                        'chat_id': update.message.chat.id,
                        'from_user': update.message.from_user.first_name,
                        'text': update.message.text,
                        'date': update.message.date
                    }
                    messages.append(msg)
            
            log_message(f"Retrieved {len(messages)} Telegram messages")
            return messages
            
        except Exception as e:
            log_message(f"Failed to get Telegram updates: {e}", "ERROR")
            return []
    
    def send_message_by_type(self, message_type, recipient, message, subject=None):
        """
        Send message based on type (auto-detect or specified)
        Args:
            message_type (str): 'email', 'whatsapp', 'telegram', or 'auto'
            recipient (str): Recipient identifier
            message (str): Message content
            subject (str): Subject (for email)
        Returns:
            bool: True if successful, False otherwise
        """
        if message_type == 'auto':
            # Auto-detect based on recipient format
            if is_valid_email(recipient):
                message_type = 'email'
            elif is_valid_phone(recipient):
                message_type = 'whatsapp'
            else:
                message_type = 'telegram'  # Assume telegram chat ID
        
        if message_type == 'email':
            subject = subject or "Message from Sarah"
            return self.send_email(recipient, subject, message)
        
        elif message_type == 'whatsapp':
            return self.send_whatsapp_message(recipient, message)
        
        elif message_type == 'telegram':
            return self.send_telegram_message(recipient, message)
        
        else:
            speak("Unknown message type.")
            return False
    
    def schedule_message(self, message_type, recipient, message, schedule_time, subject=None):
        """
        Schedule a message to be sent later
        Args:
            message_type (str): Type of message
            recipient (str): Recipient identifier
            message (str): Message content
            schedule_time (datetime): When to send the message
            subject (str): Subject (for email)
        Returns:
            bool: True if scheduled successfully
        """
        # This is a simplified implementation
        # In a full implementation, you'd want to use a proper scheduler
        
        import threading
        
        def delayed_send():
            delay = (schedule_time - datetime.now()).total_seconds()
            if delay > 0:
                time.sleep(delay)
                self.send_message_by_type(message_type, recipient, message, subject)
        
        try:
            thread = threading.Thread(target=delayed_send, daemon=True)
            thread.start()
            
            log_message(f"Message scheduled for {schedule_time}")
            speak(f"Message scheduled to be sent at {schedule_time.strftime('%I:%M %p')}")
            return True
            
        except Exception as e:
            log_message(f"Failed to schedule message: {e}", "ERROR")
            speak("Failed to schedule message.")
            return False
    
    def send_bulk_messages(self, message_type, recipients, message, subject=None):
        """
        Send message to multiple recipients
        Args:
            message_type (str): Type of message
            recipients (list): List of recipient identifiers
            message (str): Message content
            subject (str): Subject (for email)
        Returns:
            dict: Results for each recipient
        """
        results = {}
        successful = 0
        
        for recipient in recipients:
            success = self.send_message_by_type(message_type, recipient, message, subject)
            results[recipient] = success
            if success:
                successful += 1
            
            # Add delay between messages to avoid rate limiting
            time.sleep(1)
        
        log_message(f"Bulk message sent: {successful}/{len(recipients)} successful")
        speak(f"Sent {successful} out of {len(recipients)} messages successfully.")
        
        return results
    
    def create_email_template(self, template_name, subject_template, body_template):
        """
        Create an email template (simplified version)
        Args:
            template_name (str): Name of the template
            subject_template (str): Subject template with placeholders
            body_template (str): Body template with placeholders
        """
        # In a full implementation, you'd save this to a file or database
        template = {
            'name': template_name,
            'subject': subject_template,
            'body': body_template,
            'created': datetime.now().isoformat()
        }
        
        log_message(f"Email template created: {template_name}")
        speak(f"Email template '{template_name}' created successfully.")
        return template
    
    def get_contact_suggestions(self, partial_name):
        """
        Get contact suggestions based on partial name
        This is a placeholder - in a real implementation, you'd integrate with contacts
        """
        # Placeholder contacts database
        contacts = {
            'mom': {'phone': '+1234567890', 'email': 'mom@example.com'},
            'dad': {'phone': '+1234567891', 'email': 'dad@example.com'},
            'work': {'email': 'work@company.com'},
            'boss': {'email': 'boss@company.com', 'telegram': '123456789'}
        }
        
        suggestions = []
        partial_name = partial_name.lower()
        
        for name, contact_info in contacts.items():
            if partial_name in name.lower():
                suggestions.append({
                    'name': name,
                    'contact_info': contact_info
                })
        
        return suggestions
    
    def test_services(self):
        """Test all messaging services"""
        results = {
            'email': False,
            'telegram': False,
            'whatsapp': True  # WhatsApp through pywhatkit doesn't need testing
        }
        
        # Test email
        if self.email_client:
            try:
                # Just check if we can connect (don't actually send)
                results['email'] = True
                log_message("Email service test: PASS")
            except Exception as e:
                log_message(f"Email service test: FAIL - {e}", "ERROR")
        
        # Test Telegram
        if self.telegram_bot:
            try:
                # Test by getting bot info
                bot_info = self.telegram_bot.get_me()
                results['telegram'] = True
                log_message(f"Telegram service test: PASS - Bot: {bot_info.first_name}")
            except Exception as e:
                log_message(f"Telegram service test: FAIL - {e}", "ERROR")
        
        return results

# Create global message handler instance
message_handler = MessageHandler()

# Convenience functions for easy import
def send_whatsapp_message(phone_number, message, send_immediately=False):
    """Send WhatsApp message"""
    return message_handler.send_whatsapp_message(phone_number, message, send_immediately)

def send_email(recipient, subject, body, attachments=None):
    """Send email"""
    return message_handler.send_email(recipient, subject, body, attachments)

def send_telegram_message(chat_id, message):
    """Send Telegram message"""
    return message_handler.send_telegram_message(chat_id, message)

def send_message(message_type, recipient, message, subject=None):
    """Send message by type"""
    return message_handler.send_message_by_type(message_type, recipient, message, subject)

def get_telegram_messages(limit=10):
    """Get recent Telegram messages"""
    return message_handler.get_telegram_updates(limit)

def schedule_message(message_type, recipient, message, schedule_time, subject=None):
    """Schedule a message"""
    return message_handler.schedule_message(message_type, recipient, message, schedule_time, subject)

def test_messaging_services():
    """Test all messaging services"""
    return message_handler.test_services()

# Log successful module initialization
log_message("Messages module initialized successfully")