import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import re

class LiveLogWindow:
    """Live Log window for displaying real-time temperature logs"""
    def __init__(self, parent, log_manager, theme_manager, responsive_design):
        self.parent = parent
        self.log_manager = log_manager
        self.theme_manager = theme_manager
        self.responsive_design = responsive_design
        self.colors = self.theme_manager.get_theme()
        self.window = None
        self.is_running = True
        self.create_window()
    
    def create_window(self):
        """Create the Live Log window"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Live Temperature Log")
        
        # Center window
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        window_width = min(1000, screen_width - 100)
        window_height = min(700, screen_height - 100)
        self.responsive_design.center_window(self.window, window_width, window_height)
        
        self.window.minsize(800, 600)
        
        # Set background color
        if self.colors['background'] == '#0f172a':
            bg_color = '#1e293b'
            text_bg = '#1e293b'
        else:
            bg_color = '#ffffff'
            text_bg = '#ffffff'
        
        self.window.configure(bg=bg_color)
        
        # Make window modal
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Configure grid
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(1, weight=1)
        
        # Header
        header_frame = ttk.Frame(self.window, style='Modern.TFrame')
        header_frame.grid(row=0, column=0, sticky='ew', padx=15, pady=15)
        header_frame.columnconfigure(0, weight=1)
        
        title_label = ttk.Label(header_frame, text="Live Temperature Log", 
                               background=bg_color,
                               foreground=self.colors['text_primary'],
                               font=("Segoe UI", 16, "bold"))
        title_label.grid(row=0, column=0, sticky='w')
        
        # Buttons frame
        button_frame = ttk.Frame(header_frame, style='Modern.TFrame')
        button_frame.grid(row=0, column=1, sticky='e')
        
        search_export_button = ttk.Button(button_frame, text="Search & Export by Time Range", 
                                         command=self.show_time_search_modal,
                                         style='Secondary.TButton')
        search_export_button.pack(side=tk.RIGHT, padx=(10, 0))
        
        # Status info
        self.status_var = tk.StringVar(value="Showing: Live Logs")
        status_label = ttk.Label(header_frame, textvariable=self.status_var,
                                background=bg_color,
                                foreground=self.colors['text_secondary'],
                                font=("Segoe UI", 9))
        status_label.grid(row=1, column=0, sticky='w', pady=(5, 0))
        
        # Log display area
        log_frame = ttk.Frame(self.window, style='Modern.TFrame')
        log_frame.grid(row=1, column=0, sticky='nsew', padx=15, pady=(0, 15))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        # Create scrollable text area
        self.log_text = scrolledtext.ScrolledText(
            log_frame,
            wrap=tk.WORD,
            width=120,
            height=30,
            bg=text_bg,
            fg=self.colors['text_primary'],
            font=("Consolas", 9),
            insertbackground=self.colors['text_primary'],
            state='disabled'
        )
        self.log_text.grid(row=0, column=0, sticky='nsew')
        
        # Load existing logs
        self.refresh_log_display()
        
        # Start live updates
        self.update_live_log()
        
        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def show_time_search_modal(self):
        """Show the time range search and export modal window"""
        TimeRangeSearchWindow(self.window, self.log_manager, self.theme_manager, self.responsive_design)
    
    def refresh_log_display(self):
        """Refresh the log display with current logs"""
        logs = self.log_manager.get_all_logs()
        
        self.log_text.config(state='normal')
        self.log_text.delete(1.0, tk.END)
        
        if logs:
            for log_entry in logs[-1000:]:
                self.log_text.insert(tk.END, log_entry + "\n")
            
            self.log_text.see(tk.END)
        else:
            self.log_text.insert(tk.END, "No logs available yet...\n")
        
        self.log_text.config(state='disabled')
    
    def update_live_log(self):
        """Update the log display with new entries"""
        if self.is_running and self.window.winfo_exists():
            new_logs = self.log_manager.get_new_logs()
            
            if new_logs:
                self.log_text.config(state='normal')
                
                for log_entry in new_logs:
                    self.log_text.insert(tk.END, log_entry + "\n")
                
                self.log_text.see(tk.END)
                self.log_text.config(state='disabled')
            
            self.window.after(1000, self.update_live_log)
    
    def on_close(self):
        """Handle window close"""
        self.is_running = False
        self.window.destroy()


class TimeRangeSearchWindow:
    """Modal window for time range search and export"""
    def __init__(self, parent, log_manager, theme_manager, responsive_design):
        self.parent = parent
        self.log_manager = log_manager
        self.theme_manager = theme_manager
        self.responsive_design = responsive_design
        self.colors = self.theme_manager.get_theme()
        self.window = None
        self.current_logs = []
        self.create_window()
    
    def create_window(self):
        """Create the time search and export modal window"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Search and Export Logs by Time Range")
        
        # Center window
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        window_width = min(1100, screen_width - 100)
        window_height = min(700, screen_height - 100)
        self.responsive_design.center_window(self.window, window_width, window_height)
        
        self.window.minsize(900, 600)
        
        # Set background color
        if self.colors['background'] == '#0f172a':
            bg_color = '#1e293b'
            text_bg = '#1e293b'
        else:
            bg_color = '#ffffff'
            text_bg = '#ffffff'
        
        self.window.configure(bg=bg_color)
        
        # Make window modal
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Configure grid
        self.window.columnconfigure(0, weight=1)
        self.window.rowconfigure(1, weight=1)
        
        # Header
        header_frame = ttk.Frame(self.window, style='Modern.TFrame')
        header_frame.grid(row=0, column=0, sticky='ew', padx=15, pady=15)
        header_frame.columnconfigure(1, weight=1)
        
        title_label = ttk.Label(header_frame, text="Search and Export Logs by Time Range", 
                               background=bg_color,
                               foreground=self.colors['text_primary'],
                               font=("Segoe UI", 16, "bold"))
        title_label.grid(row=0, column=0, sticky='w')
        
        # Controls frame
        controls_frame = ttk.Frame(self.window, style='Modern.TFrame')
        controls_frame.grid(row=1, column=0, sticky='ew', padx=15, pady=(0, 10))
        controls_frame.columnconfigure(1, weight=1)
        
        # Date and time range selection
        datetime_frame = ttk.Frame(controls_frame, style='Modern.TFrame')
        datetime_frame.grid(row=0, column=0, sticky='ew', pady=(0, 10))
        datetime_frame.columnconfigure(1, weight=1)
        datetime_frame.columnconfigure(3, weight=1)
        
        # Start date and time
        start_frame = ttk.Frame(datetime_frame, style='Modern.TFrame')
        start_frame.grid(row=0, column=0, sticky='w', padx=(0, 20))
        
        ttk.Label(start_frame, text="Start Date & Time:", 
                 background=bg_color,
                 foreground=self.colors['text_secondary'],
                 font=('Segoe UI', 9, 'bold')).grid(row=0, column=0, sticky='w', columnspan=2)
        
        # Date entry
        ttk.Label(start_frame, text="Date (YYYY-MM-DD):", 
                 background=bg_color,
                 foreground=self.colors['text_secondary'],
                 font=('Segoe UI', 8)).grid(row=1, column=0, sticky='w', pady=(5, 2))
        
        self.start_date_var = tk.StringVar(value=datetime.datetime.now().strftime("%Y-%m-%d"))
        start_date_entry = ttk.Entry(start_frame, textvariable=self.start_date_var, width=12, font=('Segoe UI', 8))
        start_date_entry.grid(row=2, column=0, sticky='w', pady=(0, 5))
        
        # Time entry
        ttk.Label(start_frame, text="Time (HH:MM):", 
                 background=bg_color,
                 foreground=self.colors['text_secondary'],
                 font=('Segoe UI', 8)).grid(row=1, column=1, sticky='w', padx=(10, 0), pady=(5, 2))
        
        self.start_time_var = tk.StringVar(value="00:00")
        start_time_entry = ttk.Entry(start_frame, textvariable=self.start_time_var, width=8, font=('Segoe UI', 8))
        start_time_entry.grid(row=2, column=1, sticky='w', padx=(10, 0), pady=(0, 5))
        
        # End date and time
        end_frame = ttk.Frame(datetime_frame, style='Modern.TFrame')
        end_frame.grid(row=0, column=1, sticky='w', padx=(0, 20))
        
        ttk.Label(end_frame, text="End Date & Time:", 
                 background=bg_color,
                 foreground=self.colors['text_secondary'],
                 font=('Segoe UI', 9, 'bold')).grid(row=0, column=0, sticky='w', columnspan=2)
        
        # Date entry
        ttk.Label(end_frame, text="Date (YYYY-MM-DD):", 
                 background=bg_color,
                 foreground=self.colors['text_secondary'],
                 font=('Segoe UI', 8)).grid(row=1, column=0, sticky='w', pady=(5, 2))
        
        self.end_date_var = tk.StringVar(value=datetime.datetime.now().strftime("%Y-%m-%d"))
        end_date_entry = ttk.Entry(end_frame, textvariable=self.end_date_var, width=12, font=('Segoe UI', 8))
        end_date_entry.grid(row=2, column=0, sticky='w', pady=(0, 5))
        
        # Time entry
        ttk.Label(end_frame, text="Time (HH:MM):", 
                 background=bg_color,
                 foreground=self.colors['text_secondary'],
                 font=('Segoe UI', 8)).grid(row=1, column=1, sticky='w', padx=(10, 0), pady=(5, 2))
        
        self.end_time_var = tk.StringVar(value="23:59")
        end_time_entry = ttk.Entry(end_frame, textvariable=self.end_time_var, width=8, font=('Segoe UI', 8))
        end_time_entry.grid(row=2, column=1, sticky='w', padx=(10, 0), pady=(0, 5))
        
        # Quick time range buttons
        quick_buttons_frame = ttk.Frame(datetime_frame, style='Modern.TFrame')
        quick_buttons_frame.grid(row=0, column=2, sticky='w')
        
        ttk.Label(quick_buttons_frame, text="Quick Ranges:", 
                 background=bg_color,
                 foreground=self.colors['text_secondary'],
                 font=('Segoe UI', 9, 'bold')).grid(row=0, column=0, sticky='w', columnspan=2)
        
        # Quick range buttons
        button_frame = ttk.Frame(quick_buttons_frame, style='Modern.TFrame')
        button_frame.grid(row=1, column=0, sticky='w', pady=(5, 0))
        
        ttk.Button(button_frame, text="Last Hour", 
                  command=lambda: self.set_quick_range(1),
                  style='Secondary.TButton', width=10).grid(row=0, column=0, padx=(0, 5))
        
        ttk.Button(button_frame, text="Last 6 Hours", 
                  command=lambda: self.set_quick_range(6),
                  style='Secondary.TButton', width=10).grid(row=0, column=1, padx=(0, 5))
        
        ttk.Button(button_frame, text="Last 24 Hours", 
                  command=lambda: self.set_quick_range(24),
                  style='Secondary.TButton', width=10).grid(row=0, column=2, padx=(0, 5))
        
        ttk.Button(button_frame, text="Today", 
                  command=self.set_today_range,
                  style='Secondary.TButton', width=10).grid(row=1, column=0, padx=(0, 5), pady=(5, 0))
        
        ttk.Button(button_frame, text="Yesterday", 
                  command=self.set_yesterday_range,
                  style='Secondary.TButton', width=10).grid(row=1, column=1, padx=(0, 5), pady=(5, 0))
        
        ttk.Button(button_frame, text="Last 7 Days", 
                  command=lambda: self.set_quick_range(7*24),
                  style='Secondary.TButton', width=10).grid(row=1, column=2, padx=(0, 5), pady=(5, 0))
        
        # Buttons frame
        action_frame = ttk.Frame(controls_frame, style='Modern.TFrame')
        action_frame.grid(row=1, column=0, sticky='ew')
        action_frame.columnconfigure(0, weight=1)
        
        # Search button
        search_button = ttk.Button(action_frame, text="Search Logs", 
                                  command=self.search_logs,
                                  style='Primary.TButton')
        search_button.grid(row=0, column=0, sticky='w', padx=(0, 10))
        
        # Export button
        self.export_button = ttk.Button(action_frame, text="Export Results", 
                                       command=self.export_logs,
                                       style='Secondary.TButton',
                                       state="disabled")
        self.export_button.grid(row=0, column=1, sticky='w', padx=(0, 10))
        
        # Enhanced graph button
        self.graph_button = ttk.Button(action_frame, text="Enhanced Graph View", 
                                      command=self.show_enhanced_graph,
                                      style='Secondary.TButton',
                                      state="disabled")
        self.graph_button.grid(row=0, column=2, sticky='w')
        
        # Results info
        info_frame = ttk.Frame(controls_frame, style='Modern.TFrame')
        info_frame.grid(row=2, column=0, sticky='ew', pady=(10, 0))
        
        self.results_var = tk.StringVar(value="Enter time range and click 'Search Logs'")
        results_label = ttk.Label(info_frame, textvariable=self.results_var,
                                background=bg_color,
                                foreground=self.colors['text_secondary'],
                                font=("Segoe UI", 9))
        results_label.pack(anchor='w')
        
        # Main content area
        content_frame = ttk.Frame(self.window, style='Modern.TFrame')
        content_frame.grid(row=2, column=0, sticky='nsew', padx=15, pady=(0, 15))
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(0, weight=1)
        
        # Create scrollable text area
        self.log_text = scrolledtext.ScrolledText(
            content_frame,
            wrap=tk.WORD,
            width=100,
            height=25,
            bg=text_bg,
            fg=self.colors['text_primary'],
            font=("Consolas", 9),
            insertbackground=self.colors['text_primary'],
            state='disabled'
        )
        self.log_text.grid(row=0, column=0, sticky='nsew')
        
        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.on_close)
    
    def set_quick_range(self, hours):
        """Set time range for last N hours"""
        end_time = datetime.datetime.now()
        start_time = end_time - datetime.timedelta(hours=hours)
        
        self.start_date_var.set(start_time.strftime("%Y-%m-%d"))
        self.start_time_var.set(start_time.strftime("%H:%M"))
        self.end_date_var.set(end_time.strftime("%Y-%m-%d"))
        self.end_time_var.set(end_time.strftime("%H:%M"))
    
    def set_today_range(self):
        """Set time range for today"""
        today = datetime.datetime.now()
        self.start_date_var.set(today.strftime("%Y-%m-%d"))
        self.start_time_var.set("00:00")
        self.end_date_var.set(today.strftime("%Y-%m-%d"))
        self.end_time_var.set("23:59")
    
    def set_yesterday_range(self):
        """Set time range for yesterday"""
        yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
        self.start_date_var.set(yesterday.strftime("%Y-%m-%d"))
        self.start_time_var.set("00:00")
        self.end_date_var.set(yesterday.strftime("%Y-%m-%d"))
        self.end_time_var.set("23:59")
    
    def search_logs(self):
        """Search logs for the selected time range"""
        try:
            start_datetime_str = f"{self.start_date_var.get()} {self.start_time_var.get()}"
            end_datetime_str = f"{self.end_date_var.get()} {self.end_time_var.get()}"
            
            # Validate datetime
            try:
                start_datetime = datetime.datetime.strptime(start_datetime_str, "%Y-%m-%d %H:%M")
                end_datetime = datetime.datetime.strptime(end_datetime_str, "%Y-%m-%d %H:%M")
                
                if start_datetime > end_datetime:
                    messagebox.showerror("Error", "Start time cannot be after end time")
                    return
                
            except ValueError:
                messagebox.showerror("Error", "Invalid datetime format")
                return
            
            # Get logs for the time range
            self.current_logs = self.log_manager.get_logs_for_time_range(start_datetime, end_datetime)
            
            # Clear and update log display
            self.log_text.config(state='normal')
            self.log_text.delete(1.0, tk.END)
            
            if self.current_logs:
                for log_entry in self.current_logs:
                    self.log_text.insert(tk.END, log_entry + "\n")
                
                self.log_text.see(1.0)
                
                # Update results info
                log_count = len(self.current_logs)
                self.results_var.set(f"Found {log_count} log entries from {start_datetime_str} to {end_datetime_str}")
                
                # Enable export and graph buttons
                self.export_button.config(state="normal")
                self.graph_button.config(state="normal")
            
            else:
                self.log_text.insert(tk.END, "No logs found for the specified time range.\n")
                self.results_var.set("No logs found for the specified time range")
                self.export_button.config(state="disabled")
                self.graph_button.config(state="disabled")
            
            self.log_text.config(state='disabled')
        
        except Exception as e:
            messagebox.showerror("Search Error", f"Failed to search logs: {str(e)}")
    
    def show_enhanced_graph(self):
        """Show the enhanced graph view"""
        if not self.current_logs:
            messagebox.showinfo("No Data", "No logs to generate graph")
            return
        
        try:
            start_datetime_str = f"{self.start_date_var.get()} {self.start_time_var.get()}"
            end_datetime_str = f"{self.end_date_var.get()} {self.end_time_var.get()}"
            
            start_datetime = datetime.datetime.strptime(start_datetime_str, "%Y-%m-%d %H:%M")
            end_datetime = datetime.datetime.strptime(end_datetime_str, "%Y-%m-%d %H:%M")
            
            EnhancedGraphWindow(self.window, start_datetime, end_datetime, self.current_logs, 
                              self.theme_manager, self.responsive_design)
        
        except Exception as e:
            messagebox.showerror("Graph Error", f"Failed to generate graph: {str(e)}")
    
    def export_logs(self):
        """Export logs to file"""
        if not self.current_logs:
            messagebox.showinfo("No Data", "No logs to export")
            return
        
        try:
            # Export to Downloads folder
            downloads_path = os.path.join(os.path.expanduser("~"), "Downloads")
            export_filename = f"temperature_logs_export_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            export_path = os.path.join(downloads_path, export_filename)
            
            with open(export_path, 'w', encoding='utf-8') as f:
                f.write("# Temperature Logs Export\n")
                f.write(f"# Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("#\n")
                for log_entry in self.current_logs:
                    f.write(log_entry + "\n")
            
            messagebox.showinfo("Export Successful", f"Logs exported to:\n{export_path}")
        
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export logs: {str(e)}")
    
    def on_close(self):
        """Handle window close"""
        self.window.destroy()


class EnhancedGraphWindow:
    """Enhanced graph window with adjustable time resolution"""
    
    def __init__(self, parent, start_datetime, end_datetime, logs, theme_manager, responsive_design):
        self.parent = parent
        self.start_datetime = start_datetime
        self.end_datetime = end_datetime
        self.logs = logs
        self.theme_manager = theme_manager
        self.responsive_design = responsive_design
        self.colors = self.theme_manager.get_theme()
        self.resolution = "auto"  # auto, 10min, 30min, 1hour, 1day
        self.window = None
        self.create_window()
    
    def create_window(self):
        """Create the enhanced graph window"""
        self.window = tk.Toplevel(self.parent)
        self.window.title("Enhanced Temperature Graph")
        
        # Center window
        screen_width = self.window.winfo_screenwidth()
        screen_height = self.window.winfo_screenheight()
        window_width = min(1200, screen_width - 100)
        window_height = min(800, screen_height - 100)
        self.responsive_design.center_window(self.window, window_width, window_height)
        
        self.window.minsize(1000, 700)
        
        # Set background
        if self.colors['background'] == '#0f172a':
            bg_color = '#1e293b'
        else:
            bg_color = '#ffffff'
        
        self.window.configure(bg=bg_color)
        
        # Make window modal
        self.window.transient(self.parent)
        self.window.grab_set()
        
        # Header with controls
        header_frame = ttk.Frame(self.window, style='Modern.TFrame')
        header_frame.grid(row=0, column=0, sticky='ew', padx=20, pady=20)
        
        # Title
        title_text = f"Temperature Graph: {self.start_datetime.strftime('%Y-%m-%d %H:%M')} to {self.end_datetime.strftime('%Y-%m-%d %H:%M')}"
        title_label = ttk.Label(header_frame, text=title_text,
                               background=bg_color,
                               foreground=self.colors['text_primary'],
                               font=("Segoe UI", 16, "bold"))
        title_label.grid(row=0, column=0, sticky='w')
        
        # Resolution controls
        control_frame = ttk.Frame(header_frame, style='Modern.TFrame')
        control_frame.grid(row=1, column=0, sticky='w', pady=(15, 0))
        
        ttk.Label(control_frame, text="Graph Resolution:", 
                 background=bg_color,
                 foreground=self.colors['text_secondary'],
                 font=('Segoe UI', 10)).grid(row=0, column=0, sticky='w')
        
        self.resolution_var = tk.StringVar(value="auto")
        
        resolutions = [
            ("Auto (Smart)", "auto"),
            ("10 Minutes", "10min"),
            ("30 Minutes", "30min"),
            ("1 Hour", "1hour"),
            ("1 Day", "1day"),
            ("All Points", "all")
        ]
        
        for i, (text, value) in enumerate(resolutions):
            btn = ttk.Radiobutton(control_frame, text=text, value=value,
                                 variable=self.resolution_var,
                                 command=self.update_graph)
            btn.grid(row=0, column=i+1, padx=(10, 5))
        
        # Main content area
        content_frame = ttk.Frame(self.window, style='Modern.TFrame')
        content_frame.grid(row=1, column=0, sticky='nsew', padx=20, pady=(0, 20))
        content_frame.columnconfigure(0, weight=1)
        content_frame.rowconfigure(0, weight=1)
        
        # Create graph
        self.setup_graph(content_frame)
        
        # Handle window close
        self.window.protocol("WM_DELETE_WINDOW", self.window.destroy)
    
    def parse_temperature_data(self):
        """Parse temperature data from logs"""
        temperature_entries = []
        
        for log_entry in self.logs:
            # Try to extract temperature using regex
            temp_match = re.search(r'(\d+\.?\d*)\s*°C', log_entry)
            if temp_match:
                try:
                    # Extract timestamp
                    timestamp_str = log_entry.split(']')[0][1:]
                    timestamp = datetime.datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
                    
                    temperature = float(temp_match.group(1))
                    temperature_entries.append({
                        'timestamp': timestamp,
                        'temperature': temperature,
                        'log_entry': log_entry
                    })
                except Exception:
                    continue
        
        return temperature_entries
    
    def setup_graph(self, parent):
        """Setup the matplotlib graph"""
        temperature_entries = self.parse_temperature_data()
        
        if not temperature_entries:
            self.show_no_data_message(parent)
            return
        
        # Sort by timestamp
        temperature_entries.sort(key=lambda x: x['timestamp'])
        
        # Get data based on resolution
        dates, temperatures = self.get_data_by_resolution(temperature_entries)
        
        # Create figure
        self.fig, self.ax = plt.subplots(figsize=(12, 6))
        self.fig.patch.set_facecolor(self.colors['card_bg'])
        
        # Set colors based on theme
        if self.colors['background'] == '#0f172a':
            text_color = 'white'
            grid_color = '#2d3748'
            line_color = '#60a5fa'
        else:
            text_color = 'black'
            grid_color = '#e2e8f0'
            line_color = '#2563eb'
        
        # Plot graph
        self.ax.plot(dates, temperatures, marker='o', color=line_color, 
                    linewidth=2, markersize=4, label="Temperature (°C)")
        
        # Add threshold lines (example values)
        warning_temp = 25
        critical_temp = 30
        self.ax.axhline(y=warning_temp, color='yellow', linestyle='--', 
                       alpha=0.6, label=f'Warning ({warning_temp}°C)')
        self.ax.axhline(y=critical_temp, color='red', linestyle='--', 
                       alpha=0.6, label=f'Critical ({critical_temp}°C)')
        
        # Labels and title
        self.ax.set_xlabel("Time", color=text_color, fontsize=12)
        self.ax.set_ylabel("Temperature (°C)", color=text_color, fontsize=12)
        
        resolution_text = self.get_resolution_text()
        self.ax.set_title(f"Temperature History {resolution_text}\n"
                         f"{self.start_datetime.strftime('%Y-%m-%d %H:%M')} to "
                         f"{self.end_datetime.strftime('%Y-%m-%d %H:%M')}", 
                         color=text_color, fontsize=14, fontweight='bold', pad=15)
        
        # Styling
        self.ax.legend(fontsize=10, framealpha=0.9)
        self.ax.grid(True, linestyle="--", alpha=0.3, color=grid_color)
        self.ax.tick_params(colors=text_color)
        
        # Style axes
        self.ax.set_facecolor(self.colors['card_bg'])
        for spine in self.ax.spines.values():
            spine.set_color(text_color)
        
        # Format x-axis based on time range
        self.format_x_axis(dates)
        
        # Auto-adjust y-axis
        if temperatures:
            min_temp = min(temperatures)
            max_temp = max(temperatures)
            padding = (max_temp - min_temp) * 0.1 if max_temp > min_temp else 2
            self.ax.set_ylim(min_temp - padding, max_temp + padding)
        
        plt.tight_layout()
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=parent)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky='nsew')
        self.canvas.draw()
    
    def get_data_by_resolution(self, temperature_entries):
        """Get data aggregated by selected resolution"""
        resolution = self.resolution_var.get()
        
        if resolution == "all":
            # Return all data points
            dates = [entry['timestamp'] for entry in temperature_entries]
            temps = [entry['temperature'] for entry in temperature_entries]
            return dates, temps
        
        # Calculate time range
        time_range = self.end_datetime - self.start_datetime
        
        # Auto-detect best resolution
        if resolution == "auto":
            if time_range.total_seconds() <= 3600:  # 1 hour or less
                resolution = "10min"
            elif time_range.total_seconds() <= 86400:  # 1 day or less
                resolution = "30min"
            else:
                resolution = "1hour"
        
        # Group data by resolution
        grouped_data = {}
        
        for entry in temperature_entries:
            timestamp = entry['timestamp']
            temp = entry['temperature']
            
            # Determine time bucket
            if resolution == "10min":
                bucket_minutes = (timestamp.minute // 10) * 10
                bucket_time = timestamp.replace(minute=bucket_minutes, second=0, microsecond=0)
            elif resolution == "30min":
                bucket_minutes = (timestamp.minute // 30) * 30
                bucket_time = timestamp.replace(minute=bucket_minutes, second=0, microsecond=0)
            elif resolution == "1hour":
                bucket_time = timestamp.replace(minute=0, second=0, microsecond=0)
            elif resolution == "1day":
                bucket_time = timestamp.replace(hour=0, minute=0, second=0, microsecond=0)
            
            # Add to bucket
            if bucket_time not in grouped_data:
                grouped_data[bucket_time] = {'temps': [], 'count': 0}
            
            grouped_data[bucket_time]['temps'].append(temp)
            grouped_data[bucket_time]['count'] += 1
        
        # Calculate averages
        dates = []
        temps = []
        
        for bucket_time, data in sorted(grouped_data.items()):
            if data['temps']:
                dates.append(bucket_time)
                temps.append(sum(data['temps']) / len(data['temps']))
        
        return dates, temps
    
    def get_resolution_text(self):
        """Get text description of current resolution"""
        resolution = self.resolution_var.get()
        
        resolutions = {
            "auto": "(Auto Resolution)",
            "10min": "(10-Minute Resolution)",
            "30min": "(30-Minute Resolution)",
            "1hour": "(Hourly Resolution)",
            "1day": "(Daily Resolution)",
            "all": "(All Data Points)"
        }
        
        return resolutions.get(resolution, "")
    
    def format_x_axis(self, dates):
        """Format x-axis based on date range"""
        if not dates:
            return
        
        time_range = dates[-1] - dates[0]
        
        if time_range.total_seconds() <= 86400:  # 1 day or less
            date_format = mdates.DateFormatter('%H:%M\n%m/%d')
        elif time_range.total_seconds() <= 604800:  # 1 week or less
            date_format = mdates.DateFormatter('%m/%d\n%H:00')
        else:
            date_format = mdates.DateFormatter('%Y-%m-%d')
        
        self.ax.xaxis.set_major_formatter(date_format)
        plt.xticks(rotation=45)
    
    def update_graph(self):
        """Update graph with new resolution"""
        if hasattr(self, 'canvas'):
            self.canvas.get_tk_widget().destroy()
        
        # Get content frame and replot
        content_frame = self.window.children['!frame2']
        self.setup_graph(content_frame)
    
    def show_no_data_message(self, parent):
        """Show message when no data is available"""
        no_data_frame = ttk.Frame(parent, style='Modern.TFrame')
        no_data_frame.grid(row=0, column=0, sticky='nsew')
        
        no_data_label = ttk.Label(no_data_frame, 
                                text="No temperature data found in the selected time range",
                                background=self.colors['surface'],
                                foreground=self.colors['text_secondary'],
                                font=("Segoe UI", 14))
        no_data_label.pack(expand=True)