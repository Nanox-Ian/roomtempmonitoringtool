"""
Email Service Module for Temperature Monitor
Handles all email-related functionality including alerts and scheduled reports.
"""

import datetime
import smtplib
import time
import threading
import json
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

class EmailService:
    """Email service for handling alerts and scheduled reports."""
    
    def __init__(self, email_config=None, log_manager=None):
        """
        Initialize Email Service.
        
        Args:
            email_config (dict): Email configuration
            log_manager (LogManager): Logger instance
        """
        self.email_config = email_config or self._get_default_config()
        self.log_manager = log_manager
        self.is_active = True
        self.scheduler_thread = None
        self.last_email_time = None
        
        # Schedule tracking
        self.next_scheduled_time = None
        
        # Setup logging
        self.logger = self._setup_logger()
        
    def _get_default_config(self):
        """Get default email configuration."""
        self.email_config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'sender_email': 'nxpisian@gmail.com',
            'sender_password': 'aqkz uykr cmfu oqbm',
            'receiver_email': 'supercompnxp@gmail.com, ian.tolentino.bp@j-display.com, ferrerasroyce@gmail.com, raffy.santiago.rbs@gmail.com'
        }
    
    def _setup_logger(self):
        """Setup logger for email service."""
        logger = logging.getLogger('EmailService')
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
        return logger
    
    def load_config(self, config_path='email_config.json'):
        """Load email configuration from JSON file."""
        try:
            if os.path.exists(config_path):
                with open(config_path, 'r') as f:
                    self.email_config.update(json.load(f))
                self.logger.info("Email configuration loaded")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error loading email config: {e}")
            return False
    
    def save_config(self, config_path='email_config.json'):
        """Save email configuration to JSON file."""
        try:
            with open(config_path, 'w') as f:
                json.dump(self.email_config, f, indent=4)
            self.logger.info("Email configuration saved")
            return True
        except Exception as e:
            self.logger.error(f"Error saving email config: {e}")
            return False
    
    def validate_config(self):
        """Validate email configuration."""
        required_keys = ['smtp_server', 'smtp_port', 'sender_email', 
                        'sender_password', 'receiver_email']
        
        for key in required_keys:
            if key not in self.email_config or not self.email_config[key]:
                self.logger.error(f"Missing email configuration: {key}")
                return False
        
        # Validate email format
        if '@' not in self.email_config['sender_email']:
            self.logger.error("Invalid sender email format")
            return False
        
        return True
    
    def calculate_next_hour_time(self):
        """
        Calculate the exact datetime for the next hour.
        
        Returns:
            datetime: Next exact hour datetime (e.g., 10:00:00)
        """
        now = datetime.datetime.now()
        next_hour = (now + datetime.timedelta(hours=1)).replace(
            minute=0, second=0, microsecond=0
        )
        return next_hour
    
    def calculate_time_until_next_hour(self):
        """
        Calculate seconds until next exact hour.
        
        Returns:
            float: Seconds until next hour
        """
        now = datetime.datetime.now()
        next_hour = self.calculate_next_hour_time()
        return (next_hour - now).total_seconds()
    
    def start_scheduler(self, callback_function, interval_hours=1):
        """
        Start email scheduler to run at exact hours.
        
        Args:
            callback_function (callable): Function to call when email should be sent
            interval_hours (int): Hours between emails (default: 1)
        """
        if not self.validate_config():
            self.logger.error("Cannot start scheduler - invalid email configuration")
            return False
        
        self.is_active = True
        
        def scheduler_loop():
            """Main scheduler loop."""
            self.logger.info("Email scheduler started")
            
            # Calculate initial sleep time
            sleep_seconds = self.calculate_time_until_next_hour()
            
            # If we're at exactly :00:00, send immediately
            now = datetime.datetime.now()
            if now.minute == 0 and now.second < 5:  # Small buffer
                self.logger.info("At exact hour, sending immediate report")
                callback_function()
                sleep_seconds = interval_hours * 3600
            
            self.logger.info(f"Next email in {sleep_seconds:.0f} seconds")
            
            while self.is_active:
                try:
                    # Sleep until next scheduled time
                    time.sleep(sleep_seconds)
                    
                    # Execute callback (send email)
                    self.logger.info(f"Sending scheduled email at {datetime.datetime.now().strftime('%H:%M:%S')}")
                    callback_function()
                    
                    # Calculate next scheduled time
                    sleep_seconds = interval_hours * 3600
                    
                    # Update next scheduled time
                    self.next_scheduled_time = datetime.datetime.now() + datetime.timedelta(seconds=sleep_seconds)
                    
                    self.logger.info(f"Email sent. Next scheduled for: {self.next_scheduled_time.strftime('%H:%M:%S')}")
                    
                except Exception as e:
                    self.logger.error(f"Scheduler error: {e}")
                    # Sleep for 1 minute on error
                    time.sleep(60)
        
        # Start scheduler thread
        self.scheduler_thread = threading.Thread(target=scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        return True
    
    def stop_scheduler(self):
        """Stop email scheduler."""
        self.is_active = False
        self.logger.info("Email scheduler stopped")
    
    def get_next_schedule(self, hours_ahead=24):
        """
        Get schedule for next X hours.
        
        Args:
            hours_ahead (int): How many hours ahead to schedule
            
        Returns:
            list: List of datetime strings for scheduled emails
        """
        schedule = []
        now = datetime.datetime.now()
        
        # Calculate next hour
        next_hour = self.calculate_next_hour_time()
        
        # Generate schedule
        for i in range(hours_ahead):
            scheduled_time = next_hour + datetime.timedelta(hours=i)
            schedule.append(scheduled_time)
        
        return schedule
    
    def send_email(self, subject, body, is_html=False):
        """
        Send an email.
        
        Args:
            subject (str): Email subject
            body (str): Email body content
            is_html (bool): Whether body is HTML
            
        Returns:
            bool: Success status
        """
        if not self.validate_config():
            self.logger.error("Cannot send email - invalid configuration")
            return False
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_config['sender_email']
            msg['To'] = self.email_config['receiver_email']
            msg['Subject'] = subject
            
            # Attach body
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
            
            # Connect to SMTP server
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['sender_email'], self.email_config['sender_password'])
            
            # Send email
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"✅ Email sent: {subject}")
            
            # Log to system log if available
            if self.log_manager:
                self.log_manager.log_system_event("Email Sent", f"Subject: {subject}")
            
            return True
            
        except smtplib.SMTPAuthenticationError:
            self.logger.error("❌ Email authentication failed. Check username/password.")
            return False
        except smtplib.SMTPException as e:
            self.logger.error(f"❌ SMTP error: {e}")
            return False
        except Exception as e:
            self.logger.error(f"❌ Error sending email: {e}")
            return False
    
    def send_alert_email(self, alert_type, temperature, source, warning_temp, critical_temp):
        """
        Send alert email for critical/warning temperatures.
        
        Args:
            alert_type (str): "CRITICAL" or "WARNING"
            temperature (float): Current temperature
            source (str): Temperature source
            warning_temp (float): Warning threshold
            critical_temp (float): Critical threshold
        
        Returns:
            bool: Success status
        """
        if alert_type == "CRITICAL":
            subject = f"🚨 CRITICAL Temperature Alert - {temperature:.1f}°C"
            color = "🔴"
            urgency = "IMMEDIATE ACTION REQUIRED"
        else:
            subject = f"⚠️ Warning Temperature Alert - {temperature:.1f}°C"
            color = "🟡"
            urgency = "Monitor Closely"
        
        # Build email body
        body = f"""
{color} TEMPERATURE ALERT

Alert Type: {alert_type} {color}
Current Temperature: {temperature:.1f}°C

Source: SERVER ROOM
Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Urgency: {urgency}

Current Thresholds:
• Warning: {warning_temp}°C
• Critical: {critical_temp}°C

Recommended Actions:
1. Check cooling system
2. Ensure proper ventilation
3. Monitor temperature trends
4. Consider reducing system load

This is an automated alert from the Temperature Monitoring System.
The system will continue to monitor and send updates every hour if the issue persists.

Device: {os.environ.get('COMPUTERNAME', 'Unknown Device')}
"""
        
        return self.send_email(subject, body)
    
    def send_test_email(self, warning_temp, critical_temp):
        """
        Send a test email to verify email functionality.
        
        Args:
            warning_temp (float): Warning threshold
            critical_temp (float): Critical threshold
            
        Returns:
            bool: Success status
        """
        subject = "✅ Temperature Monitor - System Test"
        
        body = f"""
✅ TEMPERATURE MONITOR - SYSTEM TEST

This is a TEST EMAIL to verify system functionality.

Test Information:
• Test Type: System Verification
• Time: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
• Status: System is operational

What this test confirms:
✓ Email system is working correctly
✓ Temperature monitoring is active
✓ Alerts will be sent when needed
✓ System is running normally

Current Settings:
• Warning Threshold: {warning_temp}°C
• Critical Threshold: {critical_temp}°C

This is an automated test email.

Test ID: {int(time.time())}
"""
        
        success = self.send_email(subject, body)
        
        if success and self.log_manager:
            self.log_manager.log_system_event("System Test", "Harmless test email sent")
        
        return success
    
    def send_daily_report(self, temperature, source, status, min_temp, max_temp, 
                         warning_temp, critical_temp, temperature_adjustment=0.0):
        """
        Send daily/hourly temperature report email.
        
        Args:
            temperature (float): Current temperature
            source (str): Temperature source
            status (str): Temperature status
            min_temp (float): Minimum temperature in period
            max_temp (float): Maximum temperature in period
            warning_temp (float): Warning threshold
            critical_temp (float): Critical threshold
            temperature_adjustment (float): Temperature adjustment applied
            
        Returns:
            bool: Success status
        """
        subject = f"Temperature Report - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}"
        
        # Format min/max temps
        min_temp_str = f"{min_temp:.1f}°C" if min_temp != float('inf') else 'N/A'
        max_temp_str = f"{max_temp:.1f}°C" if max_temp != float('-inf') else 'N/A'
        
        # Build email body
        body = f"""        
TEMPERATURE MONITORING REPORT
Nanox Philippines Inc. – Server Room
{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

CURRENT STATUS

• Temperature: {temperature:.1f}°C 
• Source: SERVER ROOM
• Status: {status}

TEMPERATURE SUMMARY (PAST 1 HOUR)

• Minimum Temperature: {min_temp_str}
• Maximum Temperature: {max_temp_str}

This is an automated system-generated report from the Temperature Monitoring System.
No action is required unless a warning or critical status is indicated above.

IT Infrastructure Monitoring
Nanox Philippines Inc.
"""     
        success = self.send_email(subject, body)
        
        if success and self.log_manager:
            self.log_manager.log_system_event("Daily Report", "Email report sent")
        
        return success
    
    def get_status(self):
        """Get current email service status."""
        status = {
            'active': self.is_active,
            'sender': self.email_config.get('sender_email', 'Not configured'),
            'receiver': self.email_config.get('receiver_email', 'Not configured'),
            'next_scheduled': self.next_scheduled_time.strftime('%H:%M:%S') if self.next_scheduled_time else 'Not scheduled'
        }
        
        return status