import os
import datetime
import threading
import time
from tkinter import messagebox

class LogManager:
    """Enhanced logger with intelligent logging"""
    
    def __init__(self):
        self.daily_logs_dir = "Daily logs"
        self.current_log_file = None
        self.log_buffer = []
        self.last_log_index = 0
        self.last_log_time = 0
        self.last_alert_time = {}
        self.alert_email_sent = {}
        self.setup_logging()
    
    def setup_logging(self):
        """Setup logging infrastructure"""
        if not os.path.exists(self.daily_logs_dir):
            os.makedirs(self.daily_logs_dir)
            print(f"✅ Created Daily logs directory: {self.daily_logs_dir}")
        
        self.current_log_file = self.get_current_log_file()
        print(f"✅ Logging to: {self.current_log_file}")
    
    def get_current_log_file(self):
        """Get the current log file path based on current date"""
        current_date = datetime.datetime.now().strftime("%Y-%m-%d")
        return os.path.join(self.daily_logs_dir, f"temperature_logs_{current_date}.logs")
    
    def log_temperature(self, temp, source, status="Normal", is_alert=False):
        """
        Intelligent temperature logging:
        - Logs every minute during normal operation
        - Logs immediately for alerts
        - 1-hour cooldown for same alerts
        """
        current_time = time.time()
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if is_alert:
            log_entry = f"[{timestamp}] ⚠️ {status}: {temp:.1f}°C (Source: {source})"
            
            # Check 1-hour cooldown for same alert
            alert_key = f"{status}_{temp:.0f}"
            if alert_key in self.last_alert_time:
                time_since_last = current_time - self.last_alert_time[alert_key]
                if time_since_last < 3600:
                    print(f"⚠️ Alert suppressed (1-hour cooldown): {status} - {temp:.1f}°C")
                    return
            
            self.last_alert_time[alert_key] = current_time
        else:
            # Normal logging - only log once per 5 minute
            if current_time - self.last_log_time < 300:
                return
            log_entry = f"[{timestamp}] 📊 {temp:.1f}°C (Source: {source}, Status: {status})"
            self.last_log_time = current_time
        
        # Add to buffer and persist
        self.log_buffer.append(log_entry)
        
        # Persist to file
        threading.Thread(target=self._write_to_file, 
                        args=(log_entry,),
                        daemon=True).start()
        
        print(log_entry)
    
    def log_system_event(self, event_type, message):
        """Log system events"""
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] 🔧 {event_type}: {message}"
        
        self.log_buffer.append(log_entry)
        threading.Thread(target=self._write_to_file, 
                        args=(log_entry,),
                        daemon=True).start()
        
        print(log_entry)
    
    def should_send_alert_email(self, alert_type, temp):
        """Check if we should send email for this alert (1-hour cooldown)"""
        alert_key = f"{alert_type}_{temp:.0f}"
        current_time = time.time()
        
        if alert_key in self.alert_email_sent:
            time_since_last = current_time - self.alert_email_sent[alert_key]
            if time_since_last < 3600:
                return False
        
        self.alert_email_sent[alert_key] = current_time
        return True
    
    def _write_to_file(self, log_entry):
        """Write log entry to file"""
        try:
            current_file = self.get_current_log_file()
            if current_file != self.current_log_file:
                self.current_log_file = current_file
            
            with open(self.current_log_file, 'a', encoding='utf-8', errors='replace') as f:
                f.write(log_entry + "\n")
        except Exception as e:
            print(f"Error writing to log file: {e}")
    
    def get_all_logs(self):
        """Get all logs from all .logs files"""
        all_logs = []
        
        try:
            if not os.path.exists(self.daily_logs_dir):
                return all_logs
            
            log_files = []
            try:
                log_files = [f for f in os.listdir(self.daily_logs_dir) 
                           if f.startswith('temperature_logs_') and f.endswith('.logs')]
            except (FileNotFoundError, PermissionError):
                return all_logs
            
            if not log_files:
                return all_logs
            
            log_files.sort()
            
            for log_file in log_files:
                log_path = os.path.join(self.daily_logs_dir, log_file)
                file_logs = self._read_log_file_with_encoding(log_path)
                if file_logs:
                    all_logs.extend(file_logs)
            
            return all_logs
            
        except Exception as e:
            print(f"❌ Error reading logs: {e}")
            return all_logs
    
    def _read_log_file_with_encoding(self, file_path):
        """Read log file trying multiple encodings"""
        encodings = ['utf-8', 'latin-1', 'cp1252', 'iso-8859-1', 'utf-16']
        
        for encoding in encodings:
            try:
                with open(file_path, 'r', encoding=encoding, errors='replace') as f:
                    logs = f.readlines()
                    cleaned_logs = [log.strip() for log in logs if log.strip()]
                    return cleaned_logs
            except Exception:
                continue
        
        return []
    
    def get_new_logs(self):
        """Get new logs since last check"""
        current_logs = self.get_all_logs()
        new_logs = current_logs[self.last_log_index:]
        self.last_log_index = len(current_logs)
        return new_logs
    
    def get_logs_for_time_range(self, start_datetime, end_datetime):
        """Get logs for a specific time range"""
        logs = []
        
        try:
            if not os.path.exists(self.daily_logs_dir):
                return logs
            
            current_date = start_datetime.date()
            end_date = end_datetime.date()
            
            while current_date <= end_date:
                log_file = os.path.join(self.daily_logs_dir, 
                                      f"temperature_logs_{current_date.strftime('%Y-%m-%d')}.logs")
                
                if os.path.exists(log_file):
                    file_logs = self._read_log_file_with_encoding(log_file)
                    if file_logs:
                        for log_entry in file_logs:
                            try:
                                timestamp_str = log_entry.split(']')[0][1:]
                                log_datetime = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                                
                                if start_datetime <= log_datetime <= end_datetime:
                                    logs.append(log_entry)
                            except ValueError:
                                continue
                
                current_date += datetime.timedelta(days=1)
                
        except Exception as e:
            print(f"❌ Error reading logs for time range: {e}")
        
        return logs