# security.py - Security monitoring and threat detection for Sarah AI Assistant

import psutil
import os
import hashlib
import threading
import time
from datetime import datetime, timedelta
import json
import requests
from utils import log_message, speak
from config import *

class SecurityHandler:
    def __init__(self):
        self.is_monitoring = False
        self.monitoring_thread = None
        self.threat_log = []
        self.whitelisted_processes = set()
        self.baseline_processes = set()
        self.load_security_data()
    
    def load_security_data(self):
        """Load security configuration and whitelists"""
        try:
            # Load baseline processes (common system processes)
            self.baseline_processes = {
                'explorer.exe', 'dwm.exe', 'winlogon.exe', 'csrss.exe',
                'lsass.exe', 'services.exe', 'svchost.exe', 'chrome.exe',
                'firefox.exe', 'notepad.exe', 'calculator.exe', 'taskmgr.exe',
                'code.exe', 'spotify.exe', 'slack.exe', 'discord.exe',
                'python.exe', 'pythonw.exe', 'conhost.exe', 'cmd.exe'
            }
            
            # Load user whitelisted processes
            self.whitelisted_processes = set(self.baseline_processes)
            
            log_message("Security data loaded successfully")
            
        except Exception as e:
            log_message(f"Failed to load security data: {e}", "ERROR")
    
    def start_monitoring(self, interval=SECURITY_SCAN_INTERVAL):
        """
        Start continuous security monitoring
        Args:
            interval (int): Monitoring interval in seconds
        """
        if self.is_monitoring:
            log_message("Security monitoring is already running")
            return
        
        self.is_monitoring = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop, 
            args=(interval,), 
            daemon=True
        )
        self.monitoring_thread.start()
        
        log_message("Security monitoring started")
        speak("Security monitoring activated")
    
    def stop_monitoring(self):
        """Stop security monitoring"""
        self.is_monitoring = False
        log_message("Security monitoring stopped")
        speak("Security monitoring deactivated")
    
    def _monitoring_loop(self, interval):
        """Main monitoring loop"""
        while self.is_monitoring:
            try:
                # Perform security checks
                self.scan_running_processes()
                self.check_system_resources()
                self.monitor_network_connections()
                
                time.sleep(interval)
                
            except Exception as e:
                log_message(f"Security monitoring error: {e}", "ERROR")
                time.sleep(interval)
    
    def scan_running_processes(self):
        """Scan for suspicious running processes"""
        try:
            current_processes = []
            suspicious_processes = []
            
            for proc in psutil.process_iter(['pid', 'name', 'exe', 'cmdline', 'cpu_percent', 'memory_percent']):
                try:
                    proc_info = proc.info
                    if proc_info['name']:
                        current_processes.append(proc_info)
                        
                        # Check for suspicious process names
                        proc_name_lower = proc_info['name'].lower()
                        
                        for suspicious_term in SUSPICIOUS_PROCESSES:
                            if suspicious_term in proc_name_lower:
                                suspicious_processes.append(proc_info)
                                self.log_threat('suspicious_process', proc_info)
                                break
                        
                        # Check for processes with suspicious resource usage
                        if proc_info['cpu_percent'] and proc_info['cpu_percent'] > 90:
                            if proc_info['name'] not in self.whitelisted_processes:
                                self.log_threat('high_cpu_usage', proc_info)
                        
                        if proc_info['memory_percent'] and proc_info['memory_percent'] > 50:
                            if proc_info['name'] not in self.whitelisted_processes:
                                self.log_threat('high_memory_usage', proc_info)
                
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    continue
            
            # Check for new unknown processes
            current_names = {proc['name'] for proc in current_processes}
            new_processes = current_names - self.whitelisted_processes
            
            if new_processes:
                for proc_name in new_processes:
                    # Don't alert for every new process, just log it
                    log_message(f"New process detected: {proc_name}", "INFO")
            
            if suspicious_processes:
                log_message(f"Found {len(suspicious_processes)} suspicious processes")
                
        except Exception as e:
            log_message(f"Process scan failed: {e}", "ERROR")
    
    def check_system_resources(self):
        """Check system resources for anomalies"""
        try:
            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            if cpu_percent > 95:
                self.log_threat('high_system_cpu', {'cpu_percent': cpu_percent})
            
            # Memory usage
            memory = psutil.virtual_memory()
            if memory.percent > 90:
                self.log_threat('high_system_memory', {'memory_percent': memory.percent})
            
            # Disk usage
            disk = psutil.disk_usage('/')
            if disk.percent > 95:
                self.log_threat('low_disk_space', {'disk_percent': disk.percent})
            
            # Network activity (simplified check)
            network = psutil.net_io_counters()
            # This is a simplified check - you'd want to track deltas over time
            
        except Exception as e:
            log_message(f"System resource check failed: {e}", "ERROR")
    
    def monitor_network_connections(self):
        """Monitor network connections for suspicious activity"""
        try:
            connections = psutil.net_connections(kind='inet')
            suspicious_connections = []
            
            for conn in connections:
                if conn.status == psutil.CONN_ESTABLISHED:
                    # Check for connections to suspicious IPs or ports
                    if conn.raddr:
                        remote_ip = conn.raddr.ip
                        remote_port = conn.raddr.port
                        
                        # Check for suspicious ports
                        suspicious_ports = [1337, 31337, 12345, 54321, 9999]
                        if remote_port in suspicious_ports:
                            suspicious_connections.append(conn)
                            self.log_threat('suspicious_network_connection', {
                                'remote_ip': remote_ip,
                                'remote_port': remote_port,
                                'pid': conn.pid
                            })
            
            if suspicious_connections:
                log_message(f"Found {len(suspicious_connections)} suspicious network connections")
                
        except Exception as e:
            log_message(f"Network monitoring failed: {e}", "ERROR")
    
    def log_threat(self, threat_type, details):
        """Log a security threat"""
        threat_entry = {
            'timestamp': datetime.now().isoformat(),
            'type': threat_type,
            'details': details,
            'severity': self.get_threat_severity(threat_type)
        }
        
        self.threat_log.append(threat_entry)
        
        # Keep only recent threats (last 1000)
        if len(self.threat_log) > 1000:
            self.threat_log = self.threat_log[-1000:]
        
        log_message(f"SECURITY THREAT: {threat_type} - {details}", "WARNING")
        
        # Alert user for high severity threats
        if threat_entry['severity'] == 'high':
            speak(f"Security alert: {threat_type} detected")
    
    def get_threat_severity(self, threat_type):
        """Determine threat severity level"""
        high_severity = [
            'suspicious_process',
            'malware_detected',
            'unauthorized_access',
            'suspicious_network_connection'
        ]
        
        medium_severity = [
            'high_cpu_usage',
            'high_memory_usage',
            'unusual_file_activity'
        ]
        
        if threat_type in high_severity:
            return 'high'
        elif threat_type in medium_severity:
            return 'medium'
        else:
            return 'low'
    
    def scan_file_for_threats(self, file_path):
        """
        Scan a specific file for threats
        Args:
            file_path (str): Path to file to scan
        Returns:
            dict: Scan results
        """
        try:
            if not os.path.exists(file_path):
                return {'error': 'File not found'}
            
            result = {
                'file_path': file_path,
                'file_size': os.path.getsize(file_path),
                'scan_time': datetime.now().isoformat(),
                'threats_found': [],
                'is_safe': True
            }
            
            # Calculate file hash
            result['file_hash'] = self.calculate_file_hash(file_path)
            
            # Check file extension
            file_ext = os.path.splitext(file_path)[1].lower()
            suspicious_extensions = ['.exe', '.scr', '.bat', '.cmd', '.pif', '.com', '.vbs', '.js']
            
            if file_ext in suspicious_extensions:
                result['threats_found'].append({
                    'type': 'suspicious_extension',
                    'description': f'File has potentially dangerous extension: {file_ext}'
                })
            
            # Check file size (very large files might be suspicious)
            if result['file_size'] > 100 * 1024 * 1024:  # 100MB
                result['threats_found'].append({
                    'type': 'large_file_size',
                    'description': f'Unusually large file: {result["file_size"]} bytes'
                })
            
            # Simple entropy check for packed/encrypted files
            entropy = self.calculate_file_entropy(file_path)
            if entropy > 7.5:  # High entropy might indicate encryption/packing
                result['threats_found'].append({
                    'type': 'high_entropy',
                    'description': f'High entropy detected: {entropy:.2f} (possible encryption/packing)'
                })
            
            # Check against known malware hashes (simplified)
            if self.check_hash_reputation(result['file_hash']):
                result['threats_found'].append({
                    'type': 'known_malware_hash',
                    'description': 'File hash matches known malware signature'
                })
            
            result['is_safe'] = len(result['threats_found']) == 0
            
            if not result['is_safe']:
                self.log_threat('file_threat_detected', result)
            
            log_message(f"File scan completed: {file_path} - {'Safe' if result['is_safe'] else 'Threats found'}")
            return result
            
        except Exception as e:
            log_message(f"File scan failed for {file_path}: {e}", "ERROR")
            return {'error': str(e)}
    
    def calculate_file_hash(self, file_path, algorithm='sha256'):
        """Calculate hash of a file"""
        try:
            hash_obj = hashlib.new(algorithm)
            
            with open(file_path, 'rb') as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    hash_obj.update(chunk)
            
            return hash_obj.hexdigest()
            
        except Exception as e:
            log_message(f"Failed to calculate hash for {file_path}: {e}", "ERROR")
            return None
    
    def calculate_file_entropy(self, file_path, block_size=1024):
        """Calculate entropy of a file to detect encryption/packing"""
        try:
            import math
            from collections import Counter
            
            byte_counts = Counter()
            total_bytes = 0
            
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(block_size)
                    if not chunk:
                        break
                    
                    for byte in chunk:
                        byte_counts[byte] += 1
                        total_bytes += 1
            
            if total_bytes == 0:
                return 0
            
            # Calculate Shannon entropy
            entropy = 0
            for count in byte_counts.values():
                probability = count / total_bytes
                if probability > 0:
                    entropy -= probability * math.log2(probability)
            
            return entropy
            
        except Exception as e:
            log_message(f"Failed to calculate entropy for {file_path}: {e}", "ERROR")
            return 0
    
    def check_hash_reputation(self, file_hash):
        """
        Check file hash against known malware databases (simplified)
        Args:
            file_hash (str): File hash to check
        Returns:
            bool: True if hash is known to be malicious
        """
        try:
            # This is a simplified implementation
            # In production, you'd integrate with services like VirusTotal API
            
            # Placeholder for known bad hashes
            known_bad_hashes = set([
                # Add known malware hashes here
                '44d88612fea8a8f36de82e1278abb02f',  # Example hash
            ])
            
            return file_hash.lower() in known_bad_hashes
            
        except Exception as e:
            log_message(f"Hash reputation check failed: {e}", "ERROR")
            return False
    
    def quarantine_file(self, file_path):
        """
        Move suspicious file to quarantine directory
        Args:
            file_path (str): Path to file to quarantine
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            if not os.path.exists(file_path):
                return False
            
            # Create quarantine directory
            quarantine_dir = os.path.join(DATA_DIR, 'quarantine')
            if not os.path.exists(quarantine_dir):
                os.makedirs(quarantine_dir)
            
            # Generate unique quarantine filename
            filename = os.path.basename(file_path)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            quarantine_filename = f"{timestamp}_{filename}"
            quarantine_path = os.path.join(quarantine_dir, quarantine_filename)
            
            # Move file to quarantine
            import shutil
            shutil.move(file_path, quarantine_path)
            
            # Log quarantine action
            quarantine_info = {
                'original_path': file_path,
                'quarantine_path': quarantine_path,
                'quarantined_at': datetime.now().isoformat()
            }
            
            self.log_threat('file_quarantined', quarantine_info)
            log_message(f"File quarantined: {file_path} -> {quarantine_path}")
            speak(f"Suspicious file quarantined: {filename}")
            
            return True
            
        except Exception as e:
            log_message(f"Failed to quarantine file {file_path}: {e}", "ERROR")
            return False
    
    def get_system_security_status(self):
        """Get overall system security status"""
        try:
            status = {
                'monitoring_active': self.is_monitoring,
                'recent_threats': len([t for t in self.threat_log if 
                                     datetime.fromisoformat(t['timestamp']) > datetime.now() - timedelta(hours=24)]),
                'total_threats_logged': len(self.threat_log),
                'last_scan': datetime.now().isoformat(),
                'system_health': 'good',
                'recommendations': []
            }
            
            # Check system health indicators
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            if cpu_percent > 80:
                status['system_health'] = 'warning'
                status['recommendations'].append('High CPU usage detected')
            
            if memory.percent > 85:
                status['system_health'] = 'warning'
                status['recommendations'].append('High memory usage detected')
            
            if disk.percent > 90:
                status['system_health'] = 'critical'
                status['recommendations'].append('Low disk space - cleanup recommended')
            
            # Check for recent threats
            recent_high_threats = [t for t in self.threat_log if 
                                 t['severity'] == 'high' and 
                                 datetime.fromisoformat(t['timestamp']) > datetime.now() - timedelta(hours=1)]
            
            if recent_high_threats:
                status['system_health'] = 'critical'
                status['recommendations'].append('Recent high-severity threats detected')
            
            return status
            
        except Exception as e:
            log_message(f"Failed to get security status: {e}", "ERROR")
            return {'error': str(e)}
    
    def cleanup_threat_log(self, days_old=30):
        """Clean up old threat log entries"""
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)
            
            original_count = len(self.threat_log)
            self.threat_log = [
                threat for threat in self.threat_log
                if datetime.fromisoformat(threat['timestamp']) > cutoff_date
            ]
            
            removed_count = original_count - len(self.threat_log)
            log_message(f"Cleaned up {removed_count} old threat log entries")
            
            return removed_count
            
        except Exception as e:
            log_message(f"Threat log cleanup failed: {e}", "ERROR")
            return 0
    
    def add_to_whitelist(self, process_name):
        """Add process to whitelist"""
        try:
            self.whitelisted_processes.add(process_name.lower())
            log_message(f"Added to whitelist: {process_name}")
            speak(f"Process {process_name} added to security whitelist")
            return True
            
        except Exception as e:
            log_message(f"Failed to add to whitelist: {e}", "ERROR")
            return False
    
    def remove_from_whitelist(self, process_name):
        """Remove process from whitelist"""
        try:
            if process_name.lower() in self.whitelisted_processes:
                self.whitelisted_processes.remove(process_name.lower())
                log_message(f"Removed from whitelist: {process_name}")
                speak(f"Process {process_name} removed from security whitelist")
                return True
            else:
                return False
                
        except Exception as e:
            log_message(f"Failed to remove from whitelist: {e}", "ERROR")
            return False
    
    def get_threat_summary(self, hours=24):
        """Get summary of threats in the last N hours"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            recent_threats = [
                threat for threat in self.threat_log
                if datetime.fromisoformat(threat['timestamp']) > cutoff_time
            ]
            
            summary = {
                'total_threats': len(recent_threats),
                'high_severity': len([t for t in recent_threats if t['severity'] == 'high']),
                'medium_severity': len([t for t in recent_threats if t['severity'] == 'medium']),
                'low_severity': len([t for t in recent_threats if t['severity'] == 'low']),
                'threat_types': {},
                'time_period': f"Last {hours} hours"
            }
            
            # Count threat types
            for threat in recent_threats:
                threat_type = threat['type']
                summary['threat_types'][threat_type] = summary['threat_types'].get(threat_type, 0) + 1
            
            return summary
            
        except Exception as e:
            log_message(f"Failed to generate threat summary: {e}", "ERROR")
            return {'error': str(e)}
    
    def export_threat_log(self, filename=None):
        """Export threat log to file"""
        try:
            if not filename:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename = f"threat_log_{timestamp}.json"
            
            filepath = os.path.join(LOGS_DIR, filename)
            
            with open(filepath, 'w') as f:
                json.dump(self.threat_log, f, indent=2)
            
            log_message(f"Threat log exported to: {filepath}")
            return filepath
            
        except Exception as e:
            log_message(f"Failed to export threat log: {e}", "ERROR")
            return None

# Create global security handler instance
security_handler = SecurityHandler()

# Convenience functions for easy import
def start_security_monitoring(interval=SECURITY_SCAN_INTERVAL):
    """Start security monitoring"""
    return security_handler.start_monitoring(interval)

def stop_security_monitoring():
    """Stop security monitoring"""
    return security_handler.stop_monitoring()

def scan_file(file_path):
    """Scan file for threats"""
    return security_handler.scan_file_for_threats(file_path)

def quarantine_file(file_path):
    """Quarantine suspicious file"""
    return security_handler.quarantine_file(file_path)

def get_security_status():
    """Get security status"""
    return security_handler.get_system_security_status()

def get_threat_summary(hours=24):
    """Get threat summary"""
    return security_handler.get_threat_summary(hours)

def add_to_security_whitelist(process_name):
    """Add process to security whitelist"""
    return security_handler.add_to_whitelist(process_name)

def export_security_log(filename=None):
    """Export security log"""
    return security_handler.export_threat_log(filename)

# Log successful module initialization
log_message("Security module initialized successfully")