import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import threading
import time
import psutil
import winsound
from plyer import notification
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from collections import deque
import datetime
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json
import os

from app.services.email import EmailService
from app.ui.responsive_bg import ResponsiveGradientBackground
from app.core.responsive import ResponsiveDesign
from app.core.theme import ThemeManager
from app.core.logger import LogManager
from app.ui.live_log import LiveLogWindow
from app.services.storage_reader import StorageTemperatureReader

class TemperatureMonitor:
    def __init__(self, root):
        """Initialize the Temperature Monitor application."""
        self.root = root
        self.root.title("Enhanced Temperature Monitor")
        
        # Initialize components
        self.responsive_design = ResponsiveDesign(root)
        self.scaling_factors = self.responsive_design.get_scaling_factors()
        
        self.theme_manager = ThemeManager()
        self.colors = self.theme_manager.get_theme()
        
        # Monitoring state
        self.is_monitoring = True
        self.alert_monitoring_active = True
        self.monitor_thread = None
        
        # Alert tracking
        self.last_warning_alert = 0
        self.last_critical_alert = 0
        self.warning_cooldown = 3600  # 1 hour cooldown for alerts
        
        # Temperature thresholds (using adjusted temperatures)
        self.critical_temp = 30
        self.warning_temp = 25
        
        # Temperature history (stores adjusted temperatures)
        self.temp_history = deque(maxlen=100)
        self.time_history = deque(maxlen=100)
        
        # For statistics (based on adjusted temperatures)
        self.min_temp = float('inf')
        self.max_temp = float('-inf')
        
        # ============================================================================
        # TEMPERATURE ADJUSTMENT CONFIGURATION
        # ============================================================================
        # This value is subtracted from raw sensor readings to match room temperature
        # Example: If CPU shows 45°C but room is 22°C, set this to 23.0
        self.temperature_adjustment = 13.0  # Adjust this value as needed
        
        # Initialize components
        self.temp_reader = StorageTemperatureReader(apply_adjustment=False)
        
        # Email configuration
        self.email_config = {
            'smtp_server': 'smtp.gmail.com',
            'smtp_port': 587,
            'sender_email': 'nxpisian@gmail.com',
            'sender_password': 'aqkz uykr cmfu oqbm',
            'receiver_email': 'supercompnxp@gmail.com, ian.tolentino.bp@j-display.com, ferrerasroyce@gmail.com, raffy.santiago.rbs@gmail.com'
        }
        
        self.log_manager = LogManager()
        
        # Initialize Email Service AFTER config and log_manager are defined
        self.email_service = EmailService(
            email_config=self.email_config,
            log_manager=self.log_manager
        )
        
        # Create background and setup UI
        self.setup_background()
        self.setup_modern_styles()
        self.load_settings()
        self.setup_ui()
        
        # Start OpenHardwareMonitor
        self.start_openhardware_monitor()
        
        # Start monitoring
        self.start_realtime_updates()
        self.start_email_scheduler()  # Start email scheduler
        
        # Initial log
        self.log_manager.log_system_event("System Start", "Temperature Monitor initialized")
        self.log_manager.log_system_event("Temperature Adjustment", 
                                         f"Adjustment value: -{self.temperature_adjustment}°C")
    
    def apply_temperature_adjustment(self, raw_temp):
        if raw_temp is None:
            return None
        
        # Subtract the adjustment value from raw temperature
        adjusted_temp = raw_temp - self.temperature_adjustment
        
        return adjusted_temp
    
    def start_openhardware_monitor(self):
        """Start OpenHardwareMonitor for temperature reading."""
        print("🚀 Initializing OHM...")
        success = self.temp_reader.run_openhardware_monitor()
        
        if success:
            print("✅ OpenHardwareMonitor is ready")
            time.sleep(3)
            self.temp_reader.initialize_wmi()
        else:
            print("⚠️ Could not start OpenHardwareMonitor")
            messagebox.showwarning(
                "OpenHardwareMonitor Warning",
                "OpenHardwareMonitor could not be started automatically.\n\n"
                "Please ensure:\n"
                "1. OpenHardwareMonitor.exe is in the same directory\n"
                "2. Run it manually as Administrator\n\n"
                "Download from: https://openhardwaremonitor.org/"
            )
    
    def setup_background(self):
        """Setup the responsive gradient background."""
        self.bg_canvas = tk.Canvas(
            self.root,
            highlightthickness=0,
            bg=self.colors['background']
        )
        self.bg_canvas.pack(fill=tk.BOTH, expand=True)
        
        self.root.update()
        
        self.responsive_bg = ResponsiveGradientBackground(
            self.bg_canvas,
            self.root.winfo_width(),
            self.root.winfo_height(),
            self.colors
        )
        
        self.root.bind('<Configure>', self.on_resize)
    
    def on_resize(self, event):
        """Handle window resize events."""
        if event.widget == self.root:
            self.responsive_bg.width = event.width
            self.responsive_bg.height = event.height
            self.responsive_bg.create_responsive_background()
            self.scaling_factors = self.responsive_design.get_scaling_factors()
    
    def setup_modern_styles(self):
        """Configure modern professional styling for ttk widgets."""
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure styles
        style.configure('Modern.TFrame', background=self.colors['surface'])
        style.configure('Card.TFrame', background=self.colors['card_bg'], relief='flat', borderwidth=0)
        
        style.configure('Card.TLabelframe', 
                       background=self.colors['card_bg'],
                       relief='flat',
                       borderwidth=1,
                       bordercolor=self.colors['border'])
        
        style.configure('Card.TLabelframe.Label',
                       background=self.colors['card_bg'],
                       foreground=self.colors['text_primary'],
                       font=('Segoe UI', 10, 'bold'))
        
        # Button styles
        base_font_size = int(9 * self.scaling_factors['font_scale'])
        base_padding = int(6 * self.scaling_factors['padding_scale'])
        
        style.configure('Primary.TButton',
                       background=self.colors['primary'],
                       foreground=self.colors['text_primary'],
                       borderwidth=0,
                       font=('Segoe UI', base_font_size, 'bold'),
                       padding=(12, base_padding))
        
        style.configure('Secondary.TButton',
                       background=self.colors['surface'],
                       foreground=self.colors['text_primary'],
                       borderwidth=1,
                       bordercolor=self.colors['border'],
                       font=('Segoe UI', base_font_size),
                       padding=(10, base_padding-1))
        
        style.map('Primary.TButton',
                 background=[('active', self.colors['secondary']),
                           ('pressed', self.colors['secondary'])])
        
        style.map('Secondary.TButton',
                 background=[('active', self.colors['hover']),
                           ('pressed', self.colors['hover'])])
    
    def toggle_theme(self):
        """Toggle between dark and light themes."""
        self.colors = self.theme_manager.toggle_theme()
        self.update_theme()
    
    def update_theme(self):
        """Update the entire UI with new theme colors."""
        self.responsive_bg.update_theme(self.colors)
        self.update_graph_theme()
        self.setup_modern_styles()
        self.setup_ui()
    
    def update_graph_theme(self):
        """Update matplotlib graph with current theme colors."""
        plt.rcParams['axes.facecolor'] = self.colors['card_bg']
        plt.rcParams['figure.facecolor'] = self.colors['card_bg']
        plt.rcParams['axes.edgecolor'] = self.colors['border']
        plt.rcParams['axes.labelcolor'] = self.colors['text_primary']
        plt.rcParams['text.color'] = self.colors['text_primary']
        plt.rcParams['xtick.color'] = self.colors['text_secondary']
        plt.rcParams['ytick.color'] = self.colors['text_secondary']
        plt.rcParams['font.size'] = 9
        
        if hasattr(self, 'canvas'):
            self.update_graph()
    
    def load_settings(self):
        """Load settings from JSON configuration file."""
        try:
            if os.path.exists('temperature_monitor_settings.json'):
                with open('temperature_monitor_settings.json', 'r') as f:
                    settings = json.load(f)
                    self.critical_temp = settings.get('critical_temp', 30)
                    self.warning_temp = settings.get('warning_temp', 25)
                    # Load temperature adjustment if it exists
                    self.temperature_adjustment = settings.get('temperature_adjustment', 0.0)
        except Exception as e:
            print(f"Error loading settings: {e}")
    
    def save_settings(self):
        """Save current settings to JSON configuration file."""
        try:
            settings = {
                'critical_temp': self.critical_temp,
                'warning_temp': self.warning_temp,
                'temperature_adjustment': self.temperature_adjustment
            }
            with open('temperature_monitor_settings.json', 'w') as f:
                json.dump(settings, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def setup_ui(self):
        """Setup the main user interface."""
        # Clear existing UI
        for widget in self.bg_canvas.winfo_children():
            if isinstance(widget, ttk.Frame):
                widget.destroy()
        
        # Calculate responsive padding
        base_padding = int(20 * self.scaling_factors['padding_scale'])
        
        # Create main frame
        main_frame = ttk.Frame(self.bg_canvas, style='Modern.TFrame', padding=f"{base_padding}")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Configure grid
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        
        # Header section
        header_frame = ttk.Frame(main_frame, style='Modern.TFrame')
        header_frame.grid(row=0, column=0, sticky='ew', pady=(0, base_padding))
        header_frame.columnconfigure(0, weight=1)
        
        # Title with centered layout
        title_frame = ttk.Frame(header_frame, style='Modern.TFrame')
        title_frame.grid(row=0, column=0, sticky='ew')
        title_frame.columnconfigure(0, weight=1)
        
        # Title font size
        title_font_size = int(20 * self.scaling_factors['font_scale'])
        
        # Left side - Title
        title_label = ttk.Label(title_frame, text="Room Temperature Monitor", 
                               background=self.colors['surface'],
                               foreground=self.colors['text_primary'],
                               font=("Segoe UI", title_font_size, "bold"))
        title_label.grid(row=0, column=0, sticky='w')
        
        # Right side - Theme toggle and Live Log button
        header_buttons_frame = ttk.Frame(title_frame, style='Modern.TFrame')
        header_buttons_frame.grid(row=0, column=1, sticky='e')
        
        live_log_button = ttk.Button(header_buttons_frame, text="Live Log", 
                                    command=self.show_live_log,
                                    style='Primary.TButton')
        live_log_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        theme_button = ttk.Button(header_buttons_frame, text="Theme", 
                                 command=self.toggle_theme,
                                 style='Secondary.TButton')
        theme_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Main content area
        content_frame = ttk.Frame(main_frame, style='Modern.TFrame')
        content_frame.grid(row=1, column=0, sticky='nsew')
        content_frame.columnconfigure(0, weight=7)  # Left column
        content_frame.columnconfigure(1, weight=3)  # Right column
        content_frame.rowconfigure(0, weight=1)
        
        # Left column - Metrics and Graph
        left_column = ttk.Frame(content_frame, style='Modern.TFrame')
        left_column.grid(row=0, column=0, sticky='nsew', padx=(0, base_padding//2))
        left_column.columnconfigure(0, weight=1)
        left_column.rowconfigure(1, weight=1)
        
        # Metrics cards
        metrics_frame = ttk.Frame(left_column, style='Modern.TFrame')
        metrics_frame.grid(row=0, column=0, sticky='ew', pady=(0, base_padding))
        metrics_frame.columnconfigure(0, weight=1)
        metrics_frame.columnconfigure(1, weight=1)
        metrics_frame.columnconfigure(2, weight=1)
        
        # Card padding
        card_padding = int(20 * self.scaling_factors['padding_scale'])
        
        # Current temperature card
        current_card = ttk.Frame(metrics_frame, style='Card.TFrame', padding=f"{card_padding}")
        current_card.grid(row=0, column=0, sticky='nsew', padx=(0, base_padding//2))
        
        ttk.Label(current_card, text="Current Temperature", 
                 background=self.colors['card_bg'],
                 foreground=self.colors['text_secondary'],
                 font=("Segoe UI", 10, "bold")).pack(anchor=tk.CENTER)
        
        self.current_temp_var = tk.StringVar(value="--°C")
        temp_font_size = int(24 * self.scaling_factors['font_scale'])
        self.current_temp_display = ttk.Label(current_card, textvariable=self.current_temp_var, 
                                             background=self.colors['card_bg'],
                                             foreground=self.colors['primary'],
                                             font=("Segoe UI", temp_font_size, "bold"))
        self.current_temp_display.pack(anchor=tk.CENTER, pady=(8, 0))
        
        # Source card
        source_card = ttk.Frame(metrics_frame, style='Card.TFrame', padding=f"{card_padding}")
        source_card.grid(row=0, column=1, sticky='nsew', padx=(base_padding//2, base_padding//2))
        
        ttk.Label(source_card, text="Temperature Source", 
                 background=self.colors['card_bg'],
                 foreground=self.colors['text_secondary'],
                 font=("Segoe UI", 10, "bold")).pack(anchor=tk.CENTER)
        
        self.source_var = tk.StringVar(value="Unknown")
        source_label = ttk.Label(source_card, textvariable=self.source_var,
                                background=self.colors['card_bg'],
                                foreground=self.colors['text_primary'],
                                font=("Segoe UI", 12, "bold"))
        source_label.pack(anchor=tk.CENTER, pady=(8, 0))
        
        # Status card
        status_card = ttk.Frame(metrics_frame, style='Card.TFrame', padding=f"{card_padding}")
        status_card.grid(row=0, column=2, sticky='nsew', padx=(base_padding//2, 0))
        
        ttk.Label(status_card, text="Status", 
                 background=self.colors['card_bg'],
                 foreground=self.colors['text_secondary'],
                 font=("Segoe UI", 10, "bold")).pack(anchor=tk.CENTER)
        
        self.status_var = tk.StringVar(value="Initializing...")
        status_font_size = int(12 * self.scaling_factors['font_scale'])
        status_label = ttk.Label(status_card, textvariable=self.status_var,
                                background=self.colors['card_bg'],
                                foreground=self.colors['text_primary'],
                                font=("Segoe UI", status_font_size, "bold"))
        status_label.pack(anchor=tk.CENTER, pady=(8, 0))
        
        # Graph frame
        graph_frame = ttk.Frame(left_column, style='Card.TFrame', padding="15")
        graph_frame.grid(row=1, column=0, sticky='nsew')
        graph_frame.columnconfigure(0, weight=1)
        graph_frame.rowconfigure(0, weight=1)
        
        # Create matplotlib figure
        self.update_graph_theme()
        
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.fig.tight_layout(pad=4.0)
        self.canvas = FigureCanvasTkAgg(self.fig, master=graph_frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky='nsew')
        
        # Right column - Controls and Settings
        right_column = ttk.Frame(content_frame, style='Modern.TFrame')
        right_column.grid(row=0, column=1, sticky='nsew', padx=(base_padding//2, 0))
        right_column.columnconfigure(0, weight=1)
        
        # Alert Controls Section
        alert_frame = ttk.LabelFrame(right_column, text="ALERT CONTROLS", 
                                    style='Card.TLabelframe', padding="15")
        alert_frame.grid(row=0, column=0, sticky='ew', pady=(0, base_padding))
        
        # Alert status
        alert_status_frame = ttk.Frame(alert_frame, style='Card.TFrame')
        alert_status_frame.grid(row=0, column=0, sticky='ew', pady=(0, 12))
        
        ttk.Label(alert_status_frame, text="Alert Status:", 
                 background=self.colors['card_bg'],
                 foreground=self.colors['text_primary'],
                 font=('Segoe UI', 10, 'bold')).grid(row=0, column=0, sticky='w')
        
        self.alert_status_var = tk.StringVar(value="Alerts: ACTIVE")
        alert_status_label = ttk.Label(alert_status_frame, textvariable=self.alert_status_var,
                                      background=self.colors['card_bg'],
                                      foreground=self.colors['success'],
                                      font=('Segoe UI', 11, 'bold'))
        alert_status_label.grid(row=1, column=0, sticky='w', pady=(5, 0))
        
        # Alert control buttons
        alert_buttons_frame = ttk.Frame(alert_frame, style='Card.TFrame')
        alert_buttons_frame.grid(row=1, column=0, sticky='ew')
        alert_buttons_frame.columnconfigure(0, weight=1)
        alert_buttons_frame.columnconfigure(1, weight=1)
        
        self.start_button = ttk.Button(alert_buttons_frame, text="Enable Alerts", 
                                      command=self.start_alert_monitoring, 
                                      style='Primary.TButton')
        self.start_button.grid(row=0, column=0, sticky='ew', padx=(0, 5))
        
        self.stop_button = ttk.Button(alert_buttons_frame, text="Disable Alerts", 
                                     command=self.stop_alert_monitoring, 
                                     state="disabled", 
                                     style='Secondary.TButton')
        self.stop_button.grid(row=0, column=1, sticky='ew', padx=(5, 0))
        
        # Monitoring Controls
        monitor_frame = ttk.LabelFrame(right_column, text="MONITORING CONTROLS", 
                                      style='Card.TLabelframe', padding="15")
        monitor_frame.grid(row=1, column=0, sticky='ew', pady=(0, base_padding))
        
        # Refresh rate control
        refresh_frame = ttk.Frame(monitor_frame, style='Card.TFrame')
        refresh_frame.grid(row=0, column=0, sticky='ew', pady=(0, 15))
        
        ttk.Label(refresh_frame, text="Update Interval (seconds):", 
                 background=self.colors['card_bg'],
                 foreground=self.colors['text_primary'],
                 font=('Segoe UI', 10, 'bold')).grid(row=0, column=0, sticky='w', pady=(0, 8))
        # Interval for graph
        self.refresh_rate_var = tk.StringVar(value="10")
        refresh_combo = ttk.Combobox(refresh_frame, textvariable=self.refresh_rate_var,
                                    values=["10", "30", "60", "300"], 
                                    width=12,
                                    state="readonly")
        refresh_combo.grid(row=1, column=0, sticky='ew', pady=(0, 10))
        
        refresh_button = ttk.Button(refresh_frame, text="Update", 
                                   command=self.manual_refresh, 
                                   style='Primary.TButton')
        refresh_button.grid(row=2, column=0, sticky='ew')
        
        # Utility buttons
        utils_frame = ttk.Frame(monitor_frame, style='Card.TFrame')
        utils_frame.grid(row=1, column=0, sticky='ew', pady=(15, 0))
        
        utils_row1 = ttk.Frame(utils_frame, style='Card.TFrame')
        utils_row1.grid(row=0, column=0, sticky='ew', pady=(0, 8))
        utils_row1.columnconfigure(0, weight=1)
        utils_row1.columnconfigure(1, weight=1)
        utils_row1.columnconfigure(2, weight=1)  # For schedule button
        
        sensor_button = ttk.Button(utils_row1, text="Sensor Info", 
                                  command=self.show_sensor_info, 
                                  style='Secondary.TButton')
        sensor_button.grid(row=0, column=0, sticky='ew', padx=(0, 5))
        
        email_button = ttk.Button(utils_row1, text="Test Email", 
                                 command=self.send_test_email, 
                                 style='Secondary.TButton')
        email_button.grid(row=0, column=1, sticky='ew', padx=(5, 0))
        
        # Schedule button
        schedule_button = ttk.Button(utils_row1, text="Schedule", 
                                   command=self.show_email_schedule, 
                                   style='Secondary.TButton')
        schedule_button.grid(row=0, column=2, sticky='ew', padx=(5, 0))
        
        # Temperature Settings
        settings_frame = ttk.LabelFrame(right_column, text="TEMPERATURE SETTINGS", 
                                       style='Card.TLabelframe', padding="15")
        settings_frame.grid(row=2, column=0, sticky='ew', pady=(0, base_padding))
        
        # Warning temperature
        warning_frame = ttk.Frame(settings_frame, style='Card.TFrame')
        warning_frame.grid(row=0, column=0, sticky='ew', pady=(0, 12))
        
        ttk.Label(warning_frame, text="Warning Threshold (°C):", 
                 background=self.colors['card_bg'],
                 foreground=self.colors['text_primary'],
                 font=('Segoe UI', 9)).grid(row=0, column=0, sticky='w')
        
        self.warning_var = tk.StringVar(value=str(self.warning_temp))
        warning_entry = ttk.Entry(warning_frame, textvariable=self.warning_var, 
                                 width=8,
                                 font=('Segoe UI', 10),
                                 justify=tk.CENTER)
        warning_entry.grid(row=1, column=0, sticky='w', pady=(8, 0))
        
        # Critical temperature
        critical_frame = ttk.Frame(settings_frame, style='Card.TFrame')
        critical_frame.grid(row=1, column=0, sticky='ew', pady=(0, 15))
        
        ttk.Label(critical_frame, text="Critical Threshold (°C):", 
                 background=self.colors['card_bg'],
                 foreground=self.colors['text_primary'],
                 font=('Segoe UI', 9)).grid(row=0, column=0, sticky='w')
        
        self.critical_var = tk.StringVar(value=str(self.critical_temp))
        critical_entry = ttk.Entry(critical_frame, textvariable=self.critical_var, 
                                  width=8,
                                  font=('Segoe UI', 10),
                                  justify=tk.CENTER)
        critical_entry.grid(row=1, column=0, sticky='w', pady=(8, 0))
        
        # Save Settings button
        update_button = ttk.Button(settings_frame, text="Save Settings", 
                                  command=self.update_settings, 
                                  style='Primary.TButton')
        update_button.grid(row=2, column=0, sticky='ew', pady=(10, 0))
        
        # Footer
        footer_frame = ttk.Frame(main_frame, style='Modern.TFrame')
        footer_frame.grid(row=2, column=0, sticky='ew', pady=(base_padding, 0))
        footer_frame.columnconfigure(0, weight=1)
        
        # Last update
        self.last_update_var = tk.StringVar(value="Last update: --")
        last_update_label = ttk.Label(footer_frame, textvariable=self.last_update_var,
                                     background=self.colors['surface'],
                                     foreground=self.colors['text_secondary'],
                                     font=("Segoe UI", 9))
        last_update_label.grid(row=0, column=0, sticky='w')
        
        # Current time
        self.time_var = tk.StringVar(value="--:--:--")
        time_label = ttk.Label(footer_frame, textvariable=self.time_var,
                              background=self.colors['surface'],
                              foreground=self.colors['text_secondary'],
                              font=("Segoe UI", 9))
        time_label.grid(row=0, column=1, sticky='w', padx=(20, 0))
        
        # Next email
        self.next_email_var = tk.StringVar(value="Next report: --")
        next_email_label = ttk.Label(footer_frame, textvariable=self.next_email_var,
                                    background=self.colors['surface'],
                                    foreground=self.colors['text_secondary'],
                                    font=("Segoe UI", 9))
        next_email_label.grid(row=0, column=2, sticky='e')
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        
        self.root.update_idletasks()
    
    def start_email_scheduler(self):
        """Start the email scheduler using EmailService."""
        success = self.email_service.start_scheduler(
            callback_function=self.send_daily_report,
            interval_hours=1
        )
        
        if success:
            print("✅ Email scheduler started")
            self.log_manager.log_system_event("Email Scheduler", "Started")
        else:
            print("❌ Failed to start email scheduler")
            messagebox.showwarning(
                "Email Warning",
                "Email scheduler could not start. Check email configuration."
            )
            self.log_manager.log_system_event("Email Scheduler Error", "Failed to start")
    
    def show_email_schedule(self):
        """Show email schedule for next 24 hours."""
        schedule = self.email_service.get_next_schedule(hours_ahead=24)
        
        schedule_text = "📅 EMAIL SCHEDULE (Next 24 hours):\n" + "="*50 + "\n"
        for i, scheduled_time in enumerate(schedule):
            time_str = scheduled_time.strftime("%H:%M")
            schedule_text += f"{time_str}"
            if i == 0:
                schedule_text += "  ⬅️ Next email"
            schedule_text += "\n"
        
        messagebox.showinfo("Email Schedule", schedule_text)
    
    def show_live_log(self):
        """Show the Live Log window."""
        LiveLogWindow(self.root, self.log_manager, self.theme_manager, self.responsive_design)
    
    def start_realtime_updates(self):
        """Start real-time temperature updates in a separate thread."""
        self.is_monitoring = True
        self.update_time_display()
        self.monitor_thread = threading.Thread(target=self.monitor_temperature, daemon=True)
        self.monitor_thread.start()
    
    def update_time_display(self):
        """Update the current time and next email report display."""
        current_time = datetime.datetime.now().strftime("%H:%M:%S")
        self.time_var.set(f"Time: {current_time}")
        
        try:
            # Get next scheduled time from email service
            schedule = self.email_service.get_next_schedule(hours_ahead=1)
            
            if schedule and len(schedule) > 0:
                next_email = schedule[0]
                now = datetime.datetime.now()
                time_remaining = next_email - now
                total_seconds = int(time_remaining.total_seconds())
                
                if total_seconds > 0:
                    minutes = total_seconds // 60
                    seconds = total_seconds % 60
                    
                    if minutes > 0:
                        self.next_email_var.set(f"Next: {next_email.strftime('%H:%M')} ({minutes}m {seconds}s)")
                    else:
                        self.next_email_var.set(f"Next: {next_email.strftime('%H:%M')} ({seconds}s)")
                else:
                    self.next_email_var.set("Next report: Now")
            else:
                self.next_email_var.set("Next report: --")
        except Exception as e:
            self.next_email_var.set("Next report: --")
        
        self.root.after(1000, self.update_time_display)
    
    def monitor_temperature(self):
        """
        Main monitoring loop for temperature reading.
        """
        while self.is_monitoring:
            try:
                # Get raw temperature from hardware sensors
                raw_temp = self.temp_reader.get_primary_temperature()
                temp_source = self.temp_reader.get_temperature_source()
                
                if raw_temp is not None:
                    # APPLY TEMPERATURE ADJUSTMENT HERE
                    # This converts raw CPU temperature to room-equivalent temperature
                    adjusted_temp = self.apply_temperature_adjustment(raw_temp)
                    
                    # Update statistics based on adjusted temperature
                    if adjusted_temp < self.min_temp:
                        self.min_temp = adjusted_temp
                    if adjusted_temp > self.max_temp:
                        self.max_temp = adjusted_temp
                    
                    # Update display with adjusted temperature
                    self.root.after(0, self.update_display, adjusted_temp, temp_source)
                    
                    # Update history with adjusted temperature
                    self.temp_history.append(adjusted_temp)
                    self.time_history.append(time.time())
                    
                    # Log adjusted temperature
                    status = self.get_temperature_status(adjusted_temp)
                    is_alert = status in ["Warning", "Critical"]
                    
                    self.log_manager.log_temperature(
                        temp=adjusted_temp,
                        source=temp_source,
                        status=status,
                        is_alert=is_alert
                    )
                    
                    # Handle alerts with adjusted temperature
                    if self.alert_monitoring_active:
                        self.handle_temperature_alert(adjusted_temp, temp_source, status)
                
                else:
                    # No temperature data
                    self.root.after(0, self.update_display, None, "No sensor data")
                    self.log_manager.log_system_event("Sensor Error", "No temperature data available")
                
                # Get refresh rate
                try:
                    refresh_delay = max(1, float(self.refresh_rate_var.get()))
                except:
                    refresh_delay = 2
                
                time.sleep(refresh_delay)
            
            except Exception as e:
                print(f"Monitoring error: {e}")
                self.log_manager.log_system_event("Monitoring Error", str(e))
                time.sleep(5)
    
    def handle_temperature_alert(self, adjusted_temp, source, status):
        """Handle temperature alerts with 1-hour cooldown."""
        current_time = time.time()
        
        if status == "Critical":
            if current_time - self.last_critical_alert > self.warning_cooldown:
                # Send desktop notification
                self.root.after(0, self.send_desktop_notification,
                              "🔥 CRITICAL TEMPERATURE ALERT!",
                              f"Temperature: {adjusted_temp:.1f}°C\nSource: {source}",
                              adjusted_temp)
                
                if self.log_manager.should_send_alert_email("CRITICAL", adjusted_temp):
                    self.send_alert_email("CRITICAL", adjusted_temp, source)
                
                self.last_critical_alert = current_time
        
        elif status == "Warning":
            if current_time - self.last_warning_alert > self.warning_cooldown:
                # Send desktop notification
                self.root.after(0, self.send_desktop_notification,
                              "⚠️ HIGH TEMPERATURE WARNING",
                              f"Temperature: {adjusted_temp:.1f}°C\nSource: {source}",
                              adjusted_temp)
                
                if self.log_manager.should_send_alert_email("WARNING", adjusted_temp):
                    self.send_alert_email("WARNING", adjusted_temp, source)
                
                self.last_warning_alert = current_time
    
    def send_desktop_notification(self, title, message, temp):
        """Send system desktop notification using plyer."""
        try:
            notification.notify(
                title=title,
                message=message,
                timeout=10,
                app_name="Temperature Monitor"
            )
            print(f"Desktop notification sent: {title}")
            
        except Exception as e:
            print(f"Error sending desktop notification: {e}")
        
        # Play sound alert
        try:
            winsound.PlaySound("SystemExclamation", winsound.SND_ALIAS)
        except:
            pass
    
    def send_alert_email(self, alert_type, adjusted_temp, source):
        """Send alert email for critical/warning temperatures."""
        return self.email_service.send_alert_email(
            alert_type=alert_type,
            temperature=adjusted_temp,
            source=source,
            warning_temp=self.warning_temp,
            critical_temp=self.critical_temp
        )
    
    def send_test_email(self):
        """Send a harmless test email to verify email functionality."""
        success = self.email_service.send_test_email(
            warning_temp=self.warning_temp,
            critical_temp=self.critical_temp
        )
        
        if success:
            messagebox.showinfo(
                "Test Complete",
                "✅ Test email sent successfully!\n\n"
            )
        else:
            messagebox.showerror(
                "Error",
                "Failed to send test email. Check email configuration."
            )
        
        return success
    
    def send_daily_report(self):
        """Send daily/hourly temperature report email."""
        try:
            # Get raw temperature and apply adjustment
            raw_temp = self.temp_reader.get_primary_temperature()
            source = self.temp_reader.get_temperature_source()
            
            if raw_temp is None:
                return False
            
            # Apply temperature adjustment
            adjusted_temp = self.apply_temperature_adjustment(raw_temp)
            
            success = self.email_service.send_daily_report(
                temperature=adjusted_temp,
                source=source,
                status=self.get_temperature_status(adjusted_temp),
                min_temp=self.min_temp if self.min_temp != float('inf') else 0,
                max_temp=self.max_temp if self.max_temp != float('-inf') else 0,
                warning_temp=self.warning_temp,
                critical_temp=self.critical_temp,
                temperature_adjustment=self.temperature_adjustment
            )
            
            if success:
                print(f"✅ Daily report sent at {datetime.datetime.now().strftime('%H:%M:%S')}")
                # Reset min/max for next period
                self.min_temp = float('inf')
                self.max_temp = float('-inf')
                
                return True
            else:
                print(f"❌ Error sending daily report")
                return False
            
        except Exception as e:
            print(f"❌ Error in daily report: {e}")
            if self.log_manager:
                self.log_manager.log_system_event("Report Error", f"Failed to send daily report: {e}")
            return False
    
    def update_display(self, adjusted_temp, source):
        """Update the UI display with adjusted temperature data."""
        if adjusted_temp is not None:
            self.current_temp_var.set(f"{adjusted_temp:.1f}°C")
            self.source_var.set(source)
            
            # Update status
            status = self.get_temperature_status(adjusted_temp)
            self.status_var.set(f"{status}")
            
            # Update colors based on status
            if status == "Critical":
                self.current_temp_display.config(foreground=self.colors['error'])
                self.status_var.set(f"🔴 {status}")
            elif status == "Warning":
                self.current_temp_display.config(foreground=self.colors['warning'])
                self.status_var.set(f"🟡 {status}")
            else:
                self.current_temp_display.config(foreground=self.colors['success'])
                self.status_var.set(f"🟢 {status}")
        else:
            self.current_temp_var.set("--°C")
            self.source_var.set(source)
            self.status_var.set("No data")
            self.current_temp_display.config(foreground=self.colors['text_secondary'])
        
        # Update time
        update_time = datetime.datetime.now().strftime("%H:%M:%S")
        self.last_update_var.set(f"Updated: {update_time}")
        
        # Update graph
        self.update_graph()
    
    def get_temperature_status(self, adjusted_temp):
        """Get temperature status string based on thresholds."""
        if adjusted_temp is None:
            return "Unknown"
        elif adjusted_temp >= self.critical_temp:
            return "Critical"
        elif adjusted_temp >= self.warning_temp:
            return "Warning"
        else:
            return "Normal"
    
    def update_graph(self):
        """Update the temperature history graph with adjusted temperatures."""
        self.ax.clear()
        
        if len(self.temp_history) > 0:
            # Convert time history to minutes
            if len(self.time_history) > 0:
                start_time = self.time_history[0]
                time_minutes = [(t - start_time) / 60 for t in self.time_history]
            else:
                time_minutes = list(range(len(self.temp_history)))
            
            # Plot adjusted temperature history
            self.ax.plot(time_minutes, self.temp_history, 
                        color=self.colors['primary'], 
                        linewidth=2, 
                        marker='o',
                        markersize=3,
                        label="Temperature (°C)")
            
            # Add threshold lines
            self.ax.axhline(y=self.warning_temp, color='yellow', linestyle='--', 
                          alpha=0.6, label=f'Warning ({self.warning_temp}°C)')
            self.ax.axhline(y=self.critical_temp, color='red', linestyle='--', 
                          alpha=0.6, label=f'Critical ({self.critical_temp}°C)')
            
            # Labels and title
            self.ax.set_xlabel('Time (Minutes)', fontsize=10, fontweight='bold')
            self.ax.set_ylabel('Temperature (°C)', fontsize=10, fontweight='bold')
            self.ax.set_title('Temperature History', fontsize=12, fontweight='bold', pad=20)
            
            # Legend
            self.ax.legend(fontsize=9, framealpha=0.9)
            
            # Grid
            self.ax.grid(True, alpha=0.2, linestyle='-')
            
            # Auto-adjust y-axis
            if self.temp_history:
                current_min = min(self.temp_history)
                current_max = max(self.temp_history)
                padding = max(2, (current_max - current_min) * 0.1)
                self.ax.set_ylim(max(0, current_min - padding), current_max + padding)
        
        else:
            # No data message
            self.ax.text(0.5, 0.5, 'Collecting temperature data...', 
                        horizontalalignment='center', verticalalignment='center',
                        transform=self.ax.transAxes, fontsize=11,
                        bbox=dict(boxstyle="round,pad=0.3", facecolor=self.colors['hover']))
            self.ax.set_xlim(0, 1)
            self.ax.set_ylim(0, 1)
            self.ax.set_xticks([])
            self.ax.set_yticks([])
        
        # Add note about temperature adjustment
        note_text = f"Note: Graph Only logs initially by 10 seconds."
        self.ax.text(0.5, -0.15, note_text, transform=self.ax.transAxes, 
                    fontsize=8, color=self.colors['text_secondary'],
                    horizontalalignment='center', verticalalignment='top',
                    style='italic')
        
        self.fig.tight_layout(rect=[0, 0.05, 1, 0.95])
        self.canvas.draw()
    
    def start_alert_monitoring(self):
        """Start alert monitoring."""
        self.alert_monitoring_active = True
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.alert_status_var.set("Alerts: ACTIVE")
        
        self.log_manager.log_system_event("Alert Monitoring", "Enabled")
        messagebox.showinfo("Alerts Enabled", "Temperature alert monitoring is now active!")
    
    def stop_alert_monitoring(self):
        """Stop alert monitoring."""
        self.alert_monitoring_active = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.alert_status_var.set("Alerts: INACTIVE")
        
        self.log_manager.log_system_event("Alert Monitoring", "Disabled")
        messagebox.showinfo("Alerts Disabled", "Temperature alert monitoring is now inactive.")
    
    def manual_refresh(self):
        """Force an immediate temperature refresh."""
        raw_temp = self.temp_reader.get_primary_temperature()
        source = self.temp_reader.get_temperature_source()
        
        if raw_temp is not None:
            # Apply temperature adjustment
            adjusted_temp = self.apply_temperature_adjustment(raw_temp)
            self.update_display(adjusted_temp, source)
    
    def show_sensor_info(self):
        """Show detailed sensor information in a popup window."""
        info = self.temp_reader.get_all_sensor_info()
        
        # Create a centered popup
        popup = tk.Toplevel(self.root)
        popup.title("Sensor Information")
        
        # Center the popup
        popup_width = 800
        popup_height = 600
        self.responsive_design.center_window(popup, popup_width, popup_height)
        
        popup.minsize(600, 400)
        
        # Set background
        if self.colors['background'] == '#0f172a':
            bg_color = '#1e293b'
            text_bg = '#1e293b'
        else:
            bg_color = '#ffffff'
            text_bg = '#ffffff'
        
        popup.configure(bg=bg_color)
        
        # Make window modal
        popup.transient(self.root)
        popup.grab_set()
        
        # Create scrollable text area
        text_frame = ttk.Frame(popup, style='Modern.TFrame')
        text_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
        
        text_widget = scrolledtext.ScrolledText(
            text_frame,
            wrap=tk.WORD,
            width=80,
            height=25,
            bg=text_bg,
            fg=self.colors['text_primary'],
            font=("Consolas", 9),
            state='normal'
        )
        text_widget.pack(fill=tk.BOTH, expand=True)
        
        # Add adjustment info at the top
        adjustment_info = f"""
SENSOR INFORMATION
"""
        
        # Insert adjustment info followed by sensor info
        text_widget.insert(tk.END, adjustment_info + info)
        text_widget.config(state='disabled')
        
        # Close button
        button_frame = ttk.Frame(popup, style='Modern.TFrame')
        button_frame.pack(pady=(0, 20))
        
        close_button = ttk.Button(button_frame, text="Close", 
                                 command=popup.destroy,
                                 style='Primary.TButton')
        close_button.pack()
    
    def update_settings(self):
        """Update temperature threshold settings."""
        try:
            new_warning = float(self.warning_var.get())
            new_critical = float(self.critical_var.get())
            
            if new_warning >= new_critical:
                messagebox.showerror("Error", "Warning temperature must be lower than critical temperature")
                return
            
            self.warning_temp = new_warning
            self.critical_temp = new_critical
            self.save_settings()
            
            self.log_manager.log_system_event("Settings Update", 
                                            f"Thresholds updated: Warning={new_warning}°C, Critical={new_critical}°C")
            
            messagebox.showinfo("Success", "Temperature settings updated successfully")
        
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers for temperature thresholds")
    
    def on_closing(self):
        """Clean up when closing the application."""
        self.is_monitoring = False
        
        # Stop email scheduler
        self.email_service.stop_scheduler()
        
        self.log_manager.log_system_event("System Shutdown", "Temperature Monitor shutting down")
        self.save_settings()
        self.root.destroy()