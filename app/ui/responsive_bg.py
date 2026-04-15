import tkinter as tk

class ResponsiveGradientBackground:
    """Creates a responsive gradient background"""
    def __init__(self, canvas, width, height, theme_colors):
        self.canvas = canvas
        self.width = width
        self.height = height
        self.theme_colors = theme_colors
        self.gradient_ids = []
        self.create_responsive_background()
    
    def create_responsive_background(self):
        """Create responsive gradient background"""
        for grad_id in self.gradient_ids:
            self.canvas.delete(grad_id)
        self.gradient_ids = []
        
        self.canvas.configure(bg=self.theme_colors['background'])
        
        if self.theme_colors['background'] == '#f8fafc':
            self.create_light_background()
        else:
            self.create_dark_background()
    
    def create_light_background(self):
        """Create light theme background"""
        colors = [
            self.theme_colors['background'],
            '#f1f5f9',
            self.theme_colors['background']
        ]
        
        for i in range(3):
            color_index = i % len(colors)
            grad_id = self.canvas.create_rectangle(
                0, i * self.height // 3,
                self.width, (i + 1) * self.height // 3,
                fill=colors[color_index],
                outline='',
                width=0
            )
            self.gradient_ids.append(grad_id)
        
        self.create_subtle_grid()
    
    def create_dark_background(self):
        """Create dark theme background"""
        colors = [
            self.theme_colors['background'],
            '#1e293b',
            '#334155',
            self.theme_colors['background']
        ]
        
        for i in range(4):
            color_index = i % len(colors)
            grad_id = self.canvas.create_rectangle(
                0, i * self.height // 4,
                self.width, (i + 1) * self.height // 4,
                fill=colors[color_index],
                outline='',
                width=0
            )
            self.gradient_ids.append(grad_id)
        
        self.create_subtle_grid()
        self.create_minimal_decorations()
    
    def create_subtle_grid(self):
        """Add subtle grid pattern"""
        grid_color = self.theme_colors['grid_color']
        max_spacing = max(80, min(120, self.width // 15))
        spacing = max_spacing
        
        if self.width > 600:
            for x in range(0, self.width, spacing):
                line_id = self.canvas.create_line(
                    x, 0, x, self.height,
                    fill=grid_color, 
                    width=0.5, 
                    dash=(2, 4)
                )
                self.gradient_ids.append(line_id)
        
        if self.height > 400:
            for y in range(0, self.height, spacing):
                line_id = self.canvas.create_line(
                    0, y, self.width, y,
                    fill=grid_color, 
                    width=0.5, 
                    dash=(2, 4)
                )
                self.gradient_ids.append(line_id)
    
    def create_minimal_decorations(self):
        """Add minimal decorative elements"""
        if self.theme_colors['background'] == '#f8fafc':
            accent_color = self.theme_colors['accent']
            for i in range(3):
                size = 60 + i * 15
                x = self.width * (i % 3) / 3 + 50
                y = self.height * (i // 3) / 2 + 50
                
                circle_id = self.canvas.create_oval(
                    x - size, y - size, x + size, y + size,
                    fill='', 
                    outline=accent_color,
                    width=0.5,
                    dash=(4, 8)
                )
                self.gradient_ids.append(circle_id)
        else:
            accent_color = self.theme_colors['accent']
            for i in range(4):
                size = 40 + i * 20
                x = self.width * (i % 4) / 4 + 80
                y = self.height * (i // 4) / 2 + 80
                
                circle_id = self.canvas.create_oval(
                    x - size, y - size, x + size, y + size,
                    fill='', 
                    outline=accent_color,
                    width=1,
                    dash=(6, 10)
                )
                self.gradient_ids.append(circle_id)
    
    def update_theme(self, theme_colors):
        """Update background with new theme"""
        self.theme_colors = theme_colors
        self.create_responsive_background()