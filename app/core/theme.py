class ThemeManager:
    def __init__(self):
        self.current_theme = "dark"
        self.themes = {
            "dark": {
                'primary': '#3b82f6',
                'secondary': '#60a5fa',
                'accent': '#93c5fd',
                'background': '#0f172a',
                'surface': '#1e293b',
                'card_bg': '#1e293b',
                'text_primary': '#f8fafc',
                'text_secondary': '#cbd5e1',
                'success': '#10b981',
                'warning': '#f59e0b',
                'error': '#ef4444',
                'border': '#334155',
                'hover': '#374151',
                'grid_color': '#2d3748',
                'input_bg': '#1e293b',
                'input_fg': '#f8fafc',
            },
            "light": {
                'primary': '#2563eb',
                'secondary': '#3b82f6',
                'accent': '#60a5fa',
                'background': '#f8fafc',
                'surface': '#ffffff',
                'card_bg': '#ffffff',
                'text_primary': '#1e293b',
                'text_secondary': '#475569',
                'success': '#059669',
                'warning': '#d97706',
                'error': '#dc2626',
                'border': '#e2e8f0',
                'hover': '#f1f5f9',
                'grid_color': '#e2e8f0',
                'input_bg': '#ffffff',
                'input_fg': '#1e293b',
            }
        }
    
    def get_theme(self):
        return self.themes[self.current_theme]
    
    def toggle_theme(self):
        self.current_theme = "light" if self.current_theme == "dark" else "dark"
        return self.get_theme()
    
    def set_theme(self, theme_name):
        if theme_name in self.themes:
            self.current_theme = theme_name
        return self.get_theme()