# automation.py - Multi-step automation and workflows for Sarah AI Assistant

import subprocess
import os
import time
import threading
from datetime import datetime, timedelta
import json
from utils import log_message, speak, get_current_time
from config import *

class AutomationHandler:
    def __init__(self):
        self.active_routines = {}
        self.scheduled_tasks = []
        self.routine_templates = self.load_default_routines()
    
    def load_default_routines(self):
        """Load default automation routines"""
        return {
            'morning_routine': {
                'name': 'Morning Routine',
                'description': 'Start your day with essential apps and information',
                'steps': [
                    {'type': 'speak', 'content': 'Good morning! Starting your morning routine.'},
                    {'type': 'open_app', 'app': 'chrome'},
                    {'type': 'wait', 'seconds': 3},
                    {'type': 'open_url', 'url': 'https://gmail.com'},
                    {'type': 'wait', 'seconds': 2},
                    {'type': 'open_url', 'url': 'https://calendar.google.com', 'new_tab': True},
                    {'type': 'speak', 'content': 'Morning routine completed. Have a great day!'}
                ]
            },
            'work_setup': {
                'name': 'Work Setup',
                'description': 'Prepare your workspace for productivity',
                'steps': [
                    {'type': 'speak', 'content': 'Setting up your work environment.'},
                    {'type': 'open_app', 'app': 'code'},  # VS Code
                    {'type': 'open_app', 'app': 'slack'},
                    {'type': 'open_app', 'app': 'notion'},
                    {'type': 'speak', 'content': 'Work environment ready!'}
                ]
            },
            'evening_routine': {
                'name': 'Evening Routine',
                'description': 'Wind down and prepare for tomorrow',
                'steps': [
                    {'type': 'speak', 'content': 'Starting evening routine.'},
                    {'type': 'close_app', 'app': 'chrome'},
                    {'type': 'close_app', 'app': 'slack'},
                    {'type': 'open_app', 'app': 'spotify'},
                    {'type': 'speak', 'content': 'Evening routine completed. Good night!'}
                ]
            },
            'system_cleanup': {
                'name': 'System Cleanup',
                'description': 'Clean temporary files and optimize system',
                'steps': [
                    {'type': 'speak', 'content': 'Starting system cleanup.'},
                    {'type': 'system_command', 'command': 'cleanmgr /sagerun:1'},  # Windows
                    {'type': 'clear_temp_files'},
                    {'type': 'empty_recycle_bin'},
                    {'type': 'speak', 'content': 'System cleanup completed.'}
                ]
            }
        }
    
    def run_routine(self, routine_name, custom_steps=None):
        """
        Execute an automation routine
        Args:
            routine_name (str): Name of the routine to run
            custom_steps (list): Custom steps to execute instead of template
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if custom_steps:
                steps = custom_steps
                routine_display_name = routine_name
            elif routine_name in self.routine_templates:
                routine = self.routine_templates[routine_name]
                steps = routine['steps']
                routine_display_name = routine['name']
            else:
                speak(f"Unknown routine: {routine_name}")
                return False
            
            log_message(f"Starting routine: {routine_display_name}")
            speak(f"Starting {routine_display_name.lower()}")
            
            # Track active routine
            routine_id = f"{routine_name}_{int(time.time())}"
            self.active_routines[routine_id] = {
                'name': routine_display_name,
                'started': datetime.now(),
                'current_step': 0,
                'total_steps': len(steps)
            }
            
            success_count = 0
            
            for i, step in enumerate(steps):
                self.active_routines[routine_id]['current_step'] = i + 1
                
                log_message(f"Executing step {i+1}/{len(steps)}: {step.get('type')}")
                
                if self.execute_step(step):
                    success_count += 1
                else:
                    log_message(f"Step {i+1} failed: {step}", "WARNING")
            
            # Mark routine as completed
            del self.active_routines[routine_id]
            
            success_rate = success_count / len(steps)
            log_message(f"Routine completed: {success_count}/{len(steps)} steps successful")
            
            if success_rate >= 0.8:  # 80% success rate
                return True
            else:
                speak("Routine completed with some issues.")
                return False
                
        except Exception as e:
            log_message(f"Routine execution failed: {e}", "ERROR")
            speak("Routine execution failed.")
            return False
    
    def execute_step(self, step):
        """
        Execute a single automation step
        Args:
            step (dict): Step definition
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            step_type = step.get('type')
            
            if step_type == 'speak':
                content = step.get('content', '')
                speak(content)
                return True
            
            elif step_type == 'wait':
                seconds = step.get('seconds', 1)
                time.sleep(seconds)
                return True
            
            elif step_type == 'open_app':
                app_name = step.get('app', '')
                return self.open_application(app_name)
            
            elif step_type == 'close_app':
                app_name = step.get('app', '')
                return self.close_application(app_name)
            
            elif step_type == 'open_url':
                url = step.get('url', '')
                new_tab = step.get('new_tab', False)
                return self.open_url(url, new_tab)
            
            elif step_type == 'system_command':
                command = step.get('command', '')
                return self.run_system_command(command)
            
            elif step_type == 'send_keys':
                keys = step.get('keys', '')
                return self.send_keys(keys)
            
            elif step_type == 'click':
                x = step.get('x', 0)
                y = step.get('y', 0)
                return self.click_at_position(x, y)
            
            elif step_type == 'clear_temp_files':
                return self.clear_temp_files()
            
            elif step_type == 'empty_recycle_bin':
                return self.empty_recycle_bin()
            
            elif step_type == 'take_screenshot':
                filename = step.get('filename')
                from vision import take_screenshot
                return take_screenshot(filename) is not None
            
            elif step_type == 'send_message':
                message_type = step.get('message_type', 'email')
                recipient = step.get('recipient', '')
                message = step.get('message', '')
                subject = step.get('subject')
                from messages import send_message
                return send_message(message_type, recipient, message, subject)
            
            else:
                log_message(f"Unknown step type: {step_type}", "WARNING")
                return False
                
        except Exception as e:
            log_message(f"Step execution failed: {e}", "ERROR")
            return False
    
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
                'vscode': 'code.exe',
                'slack': 'slack.exe',
                'discord': 'discord.exe',
                'spotify': 'spotify.exe',
                'outlook': 'outlook.exe',
                'word': 'winword.exe',
                'excel': 'excel.exe',
                'powerpoint': 'powerpnt.exe',
                'notion': 'notion.exe'
            }
            
            command = app_commands.get(app_name.lower(), app_name)
            
            if os.name == 'nt':  # Windows
                subprocess.Popen(command, shell=True)
            else:  # macOS/Linux
                subprocess.Popen([command])
            
            log_message(f"Opened application: {app_name}")
            return True
            
        except Exception as e:
            log_message(f"Failed to open {app_name}: {e}", "ERROR")
            return False
    
    def close_application(self, app_name):
        """Close an application"""
        try:
            if os.name == 'nt':  # Windows
                subprocess.run(f'taskkill /f /im {app_name}.exe', shell=True, capture_output=True)
            else:  # macOS/Linux
                subprocess.run(['pkill', '-f', app_name], capture_output=True)
            
            log_message(f"Closed application: {app_name}")
            return True
            
        except Exception as e:
            log_message(f"Failed to close {app_name}: {e}", "ERROR")
            return False
    
    def open_url(self, url, new_tab=False):
        """Open URL in browser"""
        try:
            import webbrowser
            
            if new_tab:
                webbrowser.open_new_tab(url)
            else:
                webbrowser.open(url)
            
            log_message(f"Opened URL: {url}")
            return True
            
        except Exception as e:
            log_message(f"Failed to open URL {url}: {e}", "ERROR")
            return False
    
    def run_system_command(self, command):
        """Run a system command"""
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            
            if result.returncode == 0:
                log_message(f"System command executed successfully: {command}")
                return True
            else:
                log_message(f"System command failed: {command} - {result.stderr}", "ERROR")
                return False
                
        except Exception as e:
            log_message(f"System command error: {e}", "ERROR")
            return False
    
    def send_keys(self, keys):
        """Send keyboard input"""
        try:
            import pyautogui
            
            # Handle special keys
            if keys.startswith('ctrl+'):
                key_combo = keys.split('+')
                pyautogui.hotkey(*key_combo)
            elif keys.startswith('alt+'):
                key_combo = keys.split('+')
                pyautogui.hotkey(*key_combo)
            else:
                pyautogui.write(keys)
            
            log_message(f"Sent keys: {keys}")
            return True
            
        except Exception as e:
            log_message(f"Failed to send keys: {e}", "ERROR")
            return False
    
    def click_at_position(self, x, y):
        """Click at specific screen coordinates"""
        try:
            import pyautogui
            pyautogui.click(x, y)
            
            log_message(f"Clicked at position: ({x}, {y})")
            return True
            
        except Exception as e:
            log_message(f"Failed to click at ({x}, {y}): {e}", "ERROR")
            return False
    
    def clear_temp_files(self):
        """Clear temporary files"""
        try:
            temp_dirs = [
                os.environ.get('TEMP', ''),
                os.environ.get('TMP', ''),
                '/tmp'  # Linux/macOS
            ]
            
            files_deleted = 0
            
            for temp_dir in temp_dirs:
                if os.path.exists(temp_dir):
                    for filename in os.listdir(temp_dir):
                        try:
                            file_path = os.path.join(temp_dir, filename)
                            if os.path.isfile(file_path):
                                os.remove(file_path)
                                files_deleted += 1
                        except:
                            continue  # Skip files that can't be deleted
            
            log_message(f"Deleted {files_deleted} temporary files")
            return True
            
        except Exception as e:
            log_message(f"Failed to clear temp files: {e}", "ERROR")
            return False
    
    def empty_recycle_bin(self):
        """Empty the recycle bin"""
        try:
            if os.name == 'nt':  # Windows
                subprocess.run('rd /s /q %systemdrive%\\$Recycle.bin', shell=True, capture_output=True)
            else:  # macOS/Linux
                trash_dirs = [
                    os.path.expanduser('~/.Trash'),
                    os.path.expanduser('~/.local/share/Trash')
                ]
                
                for trash_dir in trash_dirs:
                    if os.path.exists(trash_dir):
                        subprocess.run(['rm', '-rf', f'{trash_dir}/*'], shell=True)
            
            log_message("Recycle bin emptied")
            return True
            
        except Exception as e:
            log_message(f"Failed to empty recycle bin: {e}", "ERROR")
            return False
    
    def schedule_routine(self, routine_name, schedule_time, repeat=None):
        """
        Schedule a routine to run at specific time
        Args:
            routine_name (str): Name of routine to schedule
            schedule_time (datetime): When to run the routine
            repeat (str): Repeat interval ('daily', 'weekly', 'monthly', None)
        Returns:
            str: Task ID if scheduled successfully, None otherwise
        """
        try:
            task_id = f"scheduled_{routine_name}_{int(time.time())}"
            
            task = {
                'id': task_id,
                'routine_name': routine_name,
                'schedule_time': schedule_time,
                'repeat': repeat,
                'created': datetime.now(),
                'active': True
            }
            
            self.scheduled_tasks.append(task)
            
            # Start scheduler thread if not already running
            self.start_scheduler()
            
            log_message(f"Routine scheduled: {routine_name} at {schedule_time}")
            speak(f"Routine {routine_name} scheduled for {schedule_time.strftime('%I:%M %p')}")
            
            return task_id
            
        except Exception as e:
            log_message(f"Failed to schedule routine: {e}", "ERROR")
            return None
    
    def start_scheduler(self):
        """Start the task scheduler thread"""
        if not hasattr(self, '_scheduler_running') or not self._scheduler_running:
            self._scheduler_running = True
            scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
            scheduler_thread.start()
            log_message("Task scheduler started")
    
    def _scheduler_loop(self):
        """Main scheduler loop"""
        while self._scheduler_running and self.scheduled_tasks:
            try:
                current_time = datetime.now()
                
                for task in self.scheduled_tasks[:]:  # Create a copy to iterate
                    if not task.get('active', True):
                        continue
                    
                    schedule_time = task['schedule_time']
                    
                    if current_time >= schedule_time:
                        # Execute the routine
                        routine_name = task['routine_name']
                        log_message(f"Executing scheduled routine: {routine_name}")
                        
                        self.run_routine(routine_name)
                        
                        # Handle repeat scheduling
                        repeat = task.get('repeat')
                        if repeat:
                            if repeat == 'daily':
                                task['schedule_time'] = schedule_time + timedelta(days=1)
                            elif repeat == 'weekly':
                                task['schedule_time'] = schedule_time + timedelta(weeks=1)
                            elif repeat == 'monthly':
                                task['schedule_time'] = schedule_time + timedelta(days=30)
                        else:
                            # Remove one-time task
                            self.scheduled_tasks.remove(task)
                
                time.sleep(60)  # Check every minute
                
            except Exception as e:
                log_message(f"Scheduler error: {e}", "ERROR")
                time.sleep(60)
        
        self._scheduler_running = False
    
    def create_custom_routine(self, name, description, steps):
        """
        Create a custom automation routine
        Args:
            name (str): Routine name
            description (str): Routine description
            steps (list): List of steps
        Returns:
            bool: True if created successfully
        """
        try:
            routine_key = name.lower().replace(' ', '_')
            
            self.routine_templates[routine_key] = {
                'name': name,
                'description': description,
                'steps': steps,
                'created': datetime.now().isoformat(),
                'custom': True
            }
            
            log_message(f"Custom routine created: {name}")
            speak(f"Custom routine '{name}' created successfully")
            
            return True
            
        except Exception as e:
            log_message(f"Failed to create custom routine: {e}", "ERROR")
            return False
    
    def get_available_routines(self):
        """Get list of available routines"""
        routines = []
        
        for key, routine in self.routine_templates.items():
            routines.append({
                'key': key,
                'name': routine['name'],
                'description': routine['description'],
                'steps': len(routine['steps']),
                'custom': routine.get('custom', False)
            })
        
        return routines
    
    def get_active_routines(self):
        """Get currently running routines"""
        return self.active_routines.copy()
    
    def get_scheduled_tasks(self):
        """Get scheduled tasks"""
        return [task for task in self.scheduled_tasks if task.get('active', True)]
    
    def cancel_scheduled_task(self, task_id):
        """Cancel a scheduled task"""
        for task in self.scheduled_tasks:
            if task['id'] == task_id:
                task['active'] = False
                log_message(f"Scheduled task cancelled: {task_id}")
                speak("Scheduled task cancelled")
                return True
        
        return False
    
    def iot_control(self, device_type, action, device_id=None):
        """
        Control IoT devices (placeholder implementation)
        Args:
            device_type (str): Type of device ('light', 'thermostat', 'switch')
            action (str): Action to perform ('on', 'off', 'toggle', 'set_temperature')
            device_id (str): Specific device ID (optional)
        Returns:
            bool: True if successful, False otherwise
        """
        # This is a placeholder - integrate with actual IoT platforms
        try:
            log_message(f"IoT Control: {device_type} - {action} - {device_id}")
            speak(f"Controlling {device_type}: {action}")
            
            # Simulate IoT control
            time.sleep(1)
            
            return True
            
        except Exception as e:
            log_message(f"IoT control failed: {e}", "ERROR")
            return False

# Create global automation handler instance
automation_handler = AutomationHandler()

# Convenience functions for easy import
def run_routine(routine_name, custom_steps=None):
    """Run an automation routine"""
    return automation_handler.run_routine(routine_name, custom_steps)

def schedule_routine(routine_name, schedule_time, repeat=None):
    """Schedule a routine"""
    return automation_handler.schedule_routine(routine_name, schedule_time, repeat)

def create_custom_routine(name, description, steps):
    """Create custom routine"""
    return automation_handler.create_custom_routine(name, description, steps)

def get_available_routines():
    """Get available routines"""
    return automation_handler.get_available_routines()

def get_active_routines():
    """Get active routines"""
    return automation_handler.get_active_routines()

def get_scheduled_tasks():
    """Get scheduled tasks"""
    return automation_handler.get_scheduled_tasks()

def cancel_task(task_id):
    """Cancel scheduled task"""
    return automation_handler.cancel_scheduled_task(task_id)

def control_iot_device(device_type, action, device_id=None):
    """Control IoT device"""
    return automation_handler.iot_control(device_type, action, device_id)

# Log successful module initialization
log_message("Automation module initialized successfully")