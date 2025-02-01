import pygame
import sys
# import time
import math
from config import *  # Use the same config as main.py
import pygame.gfxdraw  # For smoother drawing

# Initialize Pygame with optimized settings
pygame.init()
pygame.mixer.pre_init(44100, -16, 2, 2048)  # Optimize sound
pygame.event.set_allowed([pygame.QUIT, pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.MOUSEMOTION])

# Screen Setup with double buffering
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.DOUBLEBUF)
pygame.display.set_caption(WINDOW_TITLE)
clock = pygame.time.Clock()  # For consistent frame rate

class Theme:
    def __init__(self):
        # Convert hex colors from config.py to RGB
        self.background = tuple(int(BACKGROUND_COLOR.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
        self.primary = (76, 175, 80)  # Green
        self.secondary = (100, 100, 100)  # Gray
        self.accent = (0, 255, 0)  # Bright green
        self.separator = (120, 120, 120)  # Gray
        self.text = (255, 255, 255)  # White
        self.ghost_text = (175, 175, 175)  # Gray
        self.hover = (134,180,255)  # Light blue
        self.error = (255, 0, 0)  # Red
        self.warning = (255, 165, 0)  # Orange
        
        # Fonts with caching
        self._font_cache = {}
        self.title_font = self.get_font("cuadra", 100)
        self.button_font = self.get_font(None, 32)
        self.label_font = self.get_font(None, 28)
        self.song_info_font = self.get_font(None, 56)
        self.input_font = self.get_font(None, 40)
        
        # Sizes
        self.button_radius = 5
        self.input_height = 50
        self.autoguess_height = 200
        self.padding = 20
        
        self.white = (255, 255, 255)
        self.black = (0, 0, 0)
        self.gray = (120, 120, 120)
        self.red = (255, 0, 0)
        self.orange = (255, 165, 0)
        self.green = (0, 255, 0)
        self.blue = (0, 0, 255)
        self.light_blue = (134,180,255)
        self.light_green = (175,255,175)
        self.light_gray = (200,200,200)
        self.light_red = (255,175,175)
        self.light_orange = (255,200,175)
        self.light_yellow = (255,255,175)
        self.light_purple = (200,175,255)

    def get_font(self, name, size):
        key = (name, size)
        if key not in self._font_cache:
            if name:
                font_path = pygame.font.match_font(name)
                if font_path:
                    self._font_cache[key] = pygame.font.Font(font_path, size)
                else:
                    self._font_cache[key] = pygame.font.Font(None, size)  # Fall back to default system font
            else:
                self._font_cache[key] = pygame.font.Font(None, size)  # Use default system font
        return self._font_cache[key]

# Initialize theme
theme = Theme()

# Surface caching for common elements
cached_surfaces = {}

def get_cached_surface(key, creation_func):
    if key not in cached_surfaces:
        cached_surfaces[key] = creation_func()
    return cached_surfaces[key]

# Colors using config.py values
BACKGROUND_COLOR = tuple(int(BACKGROUND_COLOR.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))  # Convert hex to RGB
BUTTON_COLOR = (100, 100, 100)
BUTTON_HOVER_COLOR = (120, 120, 120)
TEXT_COLOR = (255, 255, 255)
ACCENT_COLOR = (0, 255, 0)  # Green for highlights

# Fonts
pygame.font.init()
TITLE_FONT = pygame.font.Font(None, 48)
BUTTON_FONT = pygame.font.Font(None, 32)
LABEL_FONT = pygame.font.Font(None, 28)


# =======================================
# Game Settings
# =======================================
GUESSING_RANGE = 1
MAX_LIVES = 3
#----------------------------------------

def levenshtein_distance(s1, s2):
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)

    if len(s2) == 0:
        return len(s1)

    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row

    return previous_row[-1]

def draw_rounded_rect(surface, rect, color, radius):
    """Draw a rounded rectangle using pygame.draw functions"""
    x, y, width, height = rect
    # Draw the main rectangle
    pygame.draw.rect(surface, color, (x + radius, y, width - 2*radius, height))
    pygame.draw.rect(surface, color, (x, y + radius, width, height - 2*radius))
    # Draw the rounded corners
    pygame.draw.circle(surface, color, (x + radius, y + radius), radius)
    pygame.draw.circle(surface, color, (x + width - radius, y + radius), radius)
    pygame.draw.circle(surface, color, (x + radius, y + height - radius), radius)
    pygame.draw.circle(surface, color, (x + width - radius, y + height - radius), radius)

class Button:
    def __init__(self, x, y, width, height, text, 
                 color=None, hover_color=None, text_color=None):
        self.rect = pygame.Rect(x - width//2, y - height//2, width, height)
        self.text = text
        self.color = color or theme.secondary
        self.hover_color = hover_color or theme.hover
        self.text_color = text_color or theme.text
        self.is_hovered = False
        self._cached_surfaces = {}

    def draw(self, surface):
        key = (self.rect.size, self.color, self.hover_color, self.is_hovered)
        if key not in self._cached_surfaces:
            surf = pygame.Surface(self.rect.size, pygame.SRCALPHA)
            current_color = self.hover_color if self.is_hovered else self.color
            # Draw the rounded rectangle
            draw_rounded_rect(surf, surf.get_rect(), current_color, theme.button_radius)
            text_surface = theme.button_font.render(self.text, True, self.text_color)
            text_rect = text_surface.get_rect(center=surf.get_rect().center)
            surf.blit(text_surface, text_rect)
            self._cached_surfaces[key] = surf
        surface.blit(self._cached_surfaces[key], self.rect.topleft)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1 and self.rect.collidepoint(event.pos):
                return True
        return False

class Dropdown:
    def __init__(self, x, y, width, height, options, font, drop_height=None):
        self.rect = pygame.Rect(x - width//2, y - height//2, width, height)
        self.options = [str(opt) for opt in options]  # Convert all options to strings
        self.font = font
        self.selected_option = str(options[0]) if options else ""  # Convert to string
        self.is_open = False
        self.drop_height = drop_height or 200
        # Create a ScrollableBox for options with smaller line size
        dropdown_height = min(self.drop_height, len(options) * height)  # Max height of 200 pixels
        self.options_box = ScrollableBox(
            pygame.Rect(
                self.rect.x,
                self.rect.bottom,
                width,
                dropdown_height
            ),
            font,
            theme.text,
            BUTTON_COLOR,
            border_radius=5,
            show_separators=True,
            show_scrollbar=True,
            text_align="center",
            line_size=height  # Use the height parameter as line size
        )
        self.options_box.set_text(self.options)

    def draw(self, surface, out_color):
        # Main dropdown box
        pygame.draw.rect(surface, theme.gray, self.rect, border_radius=5)
        pygame.draw.rect(surface, out_color, self.rect, width=3, border_radius=5)

        # Render selected option with truncation if needed
        text_surface = self.font.render(str(self.selected_option), True, theme.text)
        max_width = self.rect.width - 40  # Leave space for arrow and padding
        if text_surface.get_width() > max_width:
            truncated_text = str(self.selected_option)
            while text_surface.get_width() > max_width:
                truncated_text = truncated_text[:-1]
                text_surface = self.font.render(truncated_text + "...", True, theme.text)
        
        text_rect = text_surface.get_rect(center=self.rect.center)
        surface.blit(text_surface, text_rect)

        # Draw dropdown arrow
        arrow_size = 10
        arrow_points = [
            (self.rect.right - 20, self.rect.centery - arrow_size//2),
            (self.rect.right - 10, self.rect.centery - arrow_size//2),
            (self.rect.right - 15, self.rect.centery + arrow_size//2)
        ]
        pygame.draw.polygon(surface, theme.text, arrow_points)

        # Draw dropdown options if open
        if self.is_open:
            self.options_box.draw(surface, "", out_color)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                # Toggle dropdown if main box is clicked
                if self.rect.collidepoint(event.pos):
                    self.is_open = not self.is_open
                    return True

                # Handle option selection when dropdown is open
                if self.is_open:
                    # Get visible lines from options_box
                    visible_start = self.options_box.scroll_offset
                    visible_end = visible_start + (self.options_box.rect.height - 20) // self.options_box.line_size+1
                    visible_options = self.options_box.text_lines[visible_start:visible_end]
                    
                    # Calculate click position relative to visible options
                    click_y = event.pos[1] - self.options_box.rect.y - 10
                    option_height = self.options_box.line_size  # Use the correct line size
                    clicked_index = click_y // option_height
                    
                    if 0 <= clicked_index < len(visible_options):
                        self.selected_option = str(visible_options[clicked_index]['text'])  # Convert to string
                        self.is_open = False
                        return True

        # Handle scrolling in options box when open
        if self.is_open:
            self.options_box.handle_event(event)

        return False

class ScrollableBox:
    def __init__(self, rect, font, text_color, bg_color, border_radius=0, max_distance=2, 
                 line_color=None, text_align="left", show_separators=True, show_scrollbar=True,
                 line_size=None,max_height=None):
        self.rect = rect
        self.font = font
        self.text_color = text_color
        self.bg_color = bg_color
        self.border_radius = border_radius
        self.last_text_input = ""
        self.hide_all_answers = False
        self.text_lines = []  # Will store dictionaries instead of strings
        self.visible_lines = []
        self.scroll_offset = 0
        self.scroll_speed = 1
        self.is_hovered = False
        self.slider_width = 10
        self.is_dragging = False
        self.max_distance = max_distance
        self.line_color = line_color or self.bg_color  # Default line color is now background color
        self.text_align = text_align  # "left", "center", "right"
        self.show_separators = show_separators
        self.show_scrollbar = show_scrollbar
        self.line_size = line_size or self.font.get_linesize()  # Use custom line size or font's default
        self.available_height = self.rect.height
        self.standartMaxLines = self.available_height // self.line_size+1
        self.max_lines = self.standartMaxLines
        self.max_height = max_height or self.available_height
    def add_text(self, text, text_color=None, line_color=None, line_size=None):
        line_data = {
            'text': str(text),
            'text_color': text_color or self.text_color,
            'line_color': line_color or self.line_color,
            'line_size': line_size or self.line_size
        }
        self.text_lines.append(line_data)
        self.update_scroll()
        if len(self.text_lines) > self.standartMaxLines:
            self.max_lines = self.standartMaxLines-1
        
    def set_text(self, text_list):
        # Convert each item to a dictionary if it's not already
        self.text_lines = []
        for item in text_list:
            if isinstance(item, dict):
                # Ensure all required keys exist with defaults
                line_data = {
                    'text': str(item.get('text', '')),
                    'text_color': item.get('text_color', self.text_color),
                    'line_color': item.get('line_color', self.line_color),
                    'line_size': item.get('line_size', self.line_size)
                }
                self.text_lines.append(line_data)
            else:
                # If it's not a dictionary, create one with default values
                self.text_lines.append({
                    'text': str(item),
                    'text_color': self.text_color,
                    'line_color': self.line_color,
                    'line_size': self.line_size
                })
        self.update_scroll()
        if len(self.text_lines) > self.standartMaxLines:
            self.max_lines = self.standartMaxLines-1

    def clear_text(self):
        self.text_lines = []
        self.visible_lines = []
        self.max_lines = self.standartMaxLines
        self.update_scroll()

    def update_scroll(self):
        # Calculate max lines based on available height
        if len(self.visible_lines) > self.max_lines:
            self.scroll_offset = len(self.visible_lines) - self.max_lines
        else:
            self.scroll_offset = 0

    def draw(self, surface, text_input, out_color=None):
        # Draw main box
        pygame.draw.rect(surface, self.bg_color, self.rect, border_radius=self.border_radius)
        
        # Draw outline if out_color is provided and not the default color
        if out_color and out_color != (0, 0, 0):  # Default color is black (0, 0, 0)
            pygame.draw.rect(surface, out_color, self.rect, width=3, border_radius=self.border_radius)
        
        # Filter text lines based on if input text appears as a substring
        if text_input == "" and self.hide_all_answers:
            filtered_lines = []
        else:
            filtered_lines = [line for line in self.text_lines 
                            if all(word in line['text'].lower() 
                                  for word in text_input.lower().split())]
        
        # Check if the exact match exists
        exact_match = next((line for line in filtered_lines 
                          if line['text'] == text_input), None)
        
        # Move the exact match to the top of the list
        if exact_match is not None:
            filtered_lines.remove(exact_match)
            filtered_lines.insert(0, exact_match)
            filtered_lines.insert(1, {
                'text': '',
                'text_color': self.text_color,
                'line_color': self.line_color,
                'line_size': self.line_size
            })
        
        self.visible_lines = filtered_lines
        
        # Get visible portion of lines
        visible_lines = filtered_lines[self.scroll_offset:self.scroll_offset + self.max_lines]
        
        # Draw each line
        current_y = self.rect.y + 10
        total_height = 0  
        for i, line_data in enumerate(visible_lines):
            # Truncate text if it's too long for the box
            text_surface = self.font.render(str(line_data['text']), True, line_data['text_color'])
            max_width = self.rect.width - (40 if self.show_scrollbar else 20)
            if text_surface.get_width() > max_width:
                truncated_text = str(line_data['text'])
                while text_surface.get_width() > max_width:
                    truncated_text = truncated_text[:-1]
                    text_surface = self.font.render(truncated_text + "...", True, line_data['text_color'])
                text_surface = self.font.render(truncated_text + "...", True, line_data['text_color'])
            
            # Scale font size based on line_size
            scaled_font = theme.get_font(None,line_data['line_size'])
            text_surface = scaled_font.render(str(line_data['text']), True, line_data['text_color'])
            max_width = self.rect.width - (40 if self.show_scrollbar else 20)
            if text_surface.get_width() > max_width:
                truncated_text = str(line_data['text'])
                while text_surface.get_width() > max_width:
                    truncated_text = truncated_text[:-1]
                    text_surface = scaled_font.render(truncated_text + "...", True, line_data['text_color'])
                text_surface = scaled_font.render(truncated_text + "...", True, line_data['text_color'])
            
            text_rect = text_surface.get_rect()
            
            line_height = line_data['line_size']
            if total_height + line_height > self.available_height:
                break  # Stop drawing lines if we exceed available height
            
            # Handle text alignment
            if self.text_align == "center":
                text_rect.centerx = self.rect.centerx
            elif self.text_align == "right":
                text_rect.right = self.rect.right - (20 if self.show_scrollbar else 10)
            else:  # left align
                text_rect.left = self.rect.x + 10
            
            # Calculate Y position with proper padding
            text_rect.y = current_y
            surface.blit(text_surface, text_rect)
            
            # Update current_y and total_height for next line
            current_y += line_height
            total_height += line_height

        # Update scroll if text input has changed
        if text_input != self.last_text_input and text_input != "":
            self.update_scroll()
            self.last_text_input = text_input
            
        # Draw separator lines between lines        
        if self.show_separators:
            separator_y = self.rect.y + 5
            for i, line_data in enumerate(visible_lines[:-1]):  # Don't draw separator after last line
                separator_y += line_data['line_size']
                if separator_y-self.rect.y > self.max_height:
                    break
                pygame.draw.line(surface, theme.separator, 
                               (self.rect.x, separator_y), 
                               (self.rect.right - (15 if self.show_scrollbar and len(self.visible_lines) > self.max_lines else 0), separator_y), 1)

        # Draw scroll bar if enabled
        if self.show_scrollbar and len(self.visible_lines) > self.max_lines:
            # Draw scroll bar background
            scroll_bg_rect = pygame.Rect(
                self.rect.right - self.slider_width - 5,
                self.rect.y + 5,
                self.slider_width,
                self.rect.height - 10
            )
            lighter_bg = tuple(min(c + 30, 255) for c in self.bg_color[:3])
            pygame.draw.rect(surface, lighter_bg, scroll_bg_rect, border_radius=self.slider_width//2)

            # Draw scroll handle
            total_scroll_range = max(0, len(self.visible_lines) - self.max_lines)
            
            if total_scroll_range <= 0:
                handle_height = scroll_bg_rect.height
            else:
                handle_height = max(30, scroll_bg_rect.height // (total_scroll_range + 1))
            
            scroll_progress = 0 if total_scroll_range <= 0 else self.scroll_offset / total_scroll_range
            handle_y = scroll_bg_rect.y + scroll_progress * (scroll_bg_rect.height - handle_height)
            
            handle_rect = pygame.Rect(
                scroll_bg_rect.x,
                handle_y,
                self.slider_width,
                handle_height
            )
            pygame.draw.rect(surface, theme.primary, handle_rect, border_radius=self.slider_width//2)

    def get_mode_based_suggestions(self, query, options, mode="Normal"):
        """
        Return suggestions based on the game mode:
        Normal Mode: Show partial matches, including artist names
        Hard Mode: Show only if close match or exact song name
        Harder Mode: Only exact song name match
        Expert Mode: Exact "title by artist" match
        """
        query = query.lower()
        results = []

        def title_of(s):
            return s.lower().split(" by ")[0] if " by " in s else s.lower()

        if mode == "Normal":
            for item in options:
                item_lower = str(item).lower()
                # If query is a substring or within Levenshtein distance <= 2
                if (query in item_lower) or (levenshtein_distance(query, item_lower) <= 2):
                    results.append(item)

        elif mode == "Hard":
            # 1) If there's exactly one partial match for 'query', show that
            subset = [x for x in options if query in str(x).lower()]
            if len(subset) == 1:
                results.append(subset[0])
            # 2) If the user typed the song name with <=1 error, show it
            for item in options:
                dist = levenshtein_distance(query, title_of(str(item)))
                if dist <= 1 or query == title_of(str(item)):
                    results.append(item)

        elif mode == "Harder":
            # Only show if the exact song name matches with no corrections
            for item in options:
                if title_of(str(item)) == query:
                    results.append(item)

        elif mode == "Expert":
            # Only show if "title by artist" is an exact match
            for item in options:
                if str(item).lower() == query:
                    results.append(item)

        return list(set(results))

    def handle_event(self, event, game_screen=None):
        if event.type == pygame.MOUSEMOTION:
            self.is_hovered = self.rect.collidepoint(event.pos)
            
            if self.is_dragging:
                total_scroll_range = max(0, len(self.visible_lines) - self.max_lines)
                
                if total_scroll_range > 0:
                    scroll_area_height = self.rect.height - 10
                    mouse_y = event.pos[1] - (self.rect.y + 5)
                    scroll_fraction = mouse_y / scroll_area_height
                    self.scroll_offset = int(scroll_fraction * total_scroll_range)
                    self.scroll_offset = max(0, min(self.scroll_offset, total_scroll_range))
                return True

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if self.rect.collidepoint(event.pos):
                    # Get visible lines
                    visible_start = self.scroll_offset
                    visible_end = visible_start + self.max_lines
                    visible_options = self.visible_lines[visible_start:visible_end]
                    
                    # Calculate click position relative to visible options
                    click_y = event.pos[1] - self.rect.y - 10
                    option_height = self.line_size
                    clicked_index = click_y // option_height
                    
                    if 0 <= clicked_index < len(visible_options):
                        selected_option = visible_options[clicked_index]['text']
                        if game_screen:
                            game_screen.input_text = selected_option
                        return True

                scroll_bar_rect = pygame.Rect(
                    self.rect.right - self.slider_width - 5,
                    self.rect.y + 5,
                    self.slider_width,
                    self.rect.height - 10
                )
                if scroll_bar_rect.collidepoint(event.pos):
                    self.is_dragging = True
                    return True

        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.is_dragging = False

        if event.type == pygame.MOUSEWHEEL and self.is_hovered:
            self.scroll_offset -= event.y * self.scroll_speed
            self.scroll_offset = max(0, min(self.scroll_offset, len(self.visible_lines) - self.max_lines))
            return True

        return False

class StartScreen:
    def __init__(self):
        self.game_modes = ["Normal", "Hard", "Harder", "Extreme"]
        self.selected_mode = "Normal"
        self.playlist_options = ["Liked Songs", "Custom Playlist","abhsbdahsdashdashdjashdljahsdlhalsdhald0","01982750126509729375012357","!#^!#%^@$*&%&(&(*)&(&&#@#^","DFGWERTVGWYAWSRYTBSVUYSVETBVY"]
        self.selected_playlist = "Liked Songs"

        # Create widgets
        self.setup_widgets()

    def setup_widgets(self):
        # Mode Selection Dropdown
        self.mode_dropdown = Dropdown(
            x=SCREEN_WIDTH//2, 
            y=200, 
            width=300, 
            height=40,
            drop_height = 200,
            options=self.game_modes, 
            font=theme.button_font
        )

        # Playlist Selection Dropdown
        self.playlist_dropdown = Dropdown(
            x=SCREEN_WIDTH//2, 
            y=300, 
            width=300, 
            height=40,
            options=self.playlist_options, 
            font=theme.button_font
        )

        # Start Game Button
        self.start_button = Button(
            x=SCREEN_WIDTH//2, 
            y=500, 
            width=200, 
            height=50,
            text="Start Game", 
            color=theme.primary,
            hover_color=theme.hover
        )

    def get_title_color(self):
        # Generate a smooth color gradient based on the current time
        current_time = pygame.time.get_ticks()
        r = (math.sin(current_time * 0.001) + 1) / 2 * 200 + 55 # Range 55-255
        g = (math.sin(current_time * 0.002) + 1) / 2 * 200 + 55 # Range 55-255  
        b = (math.sin(current_time * 0.003) + 1) / 2 * 200 + 55 # Range 55-255
        return (int(r), int(g), int(b))

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            # Handle events in reverse order of drawing (topmost first)
            if self.mode_dropdown.is_open:
                if self.mode_dropdown.handle_event(event):
                    continue
            if self.playlist_dropdown.is_open:
                if self.playlist_dropdown.handle_event(event):
                    continue
            if self.start_button.handle_event(event):
                print(f"Starting game with mode: {self.mode_dropdown.selected_option}")
                print(f"Playlist: {self.playlist_dropdown.selected_option}")
                return False
            
            # Handle dropdown toggles only if no other dropdown is open
            if not self.playlist_dropdown.is_open:
                if self.mode_dropdown.handle_event(event):
                    continue
            if not self.mode_dropdown.is_open:
                if self.playlist_dropdown.handle_event(event):
                    continue

        return True

    def draw(self):
        screen.fill(theme.background)
        
        # Draw title with color cycling effect
        title_color = self.get_title_color()
        title_text = theme.title_font.render("Music Guesser", True, title_color)
        title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, 75))
        screen.blit(title_text, title_rect)
        
        # Draw mode dropdown label
        mode_label = theme.label_font.render("Select Game Mode:", True, theme.text)
        mode_label_rect = mode_label.get_rect(center=(SCREEN_WIDTH//2, 150))
        screen.blit(mode_label, mode_label_rect)
        
        # Draw playlist dropdown label
        playlist_label = theme.label_font.render("Select Playlist:", True, theme.text)
        playlist_label_rect = playlist_label.get_rect(center=(SCREEN_WIDTH//2, 250))
        screen.blit(playlist_label, playlist_label_rect)
        
        # Draw widgets in correct order
        self.start_button.draw(screen)
        self.playlist_dropdown.draw(screen,title_color)
        self.mode_dropdown.draw(screen,title_color)
        
        pygame.display.flip()

class SummaryScreen:
    def __init__(self, game_data=None):
        self.setup_widgets(game_data)
        self._last_draw_time = 0
        self._min_draw_interval = 16  # ~60 FPS

    def setup_widgets(self, game_data):
        # Create a large scrollable box for the summary
        summary_rect = pygame.Rect(
            theme.padding,
            theme.padding,
            SCREEN_WIDTH - 2*theme.padding,
            SCREEN_HEIGHT - 2*theme.padding - 100  # Leave space for close button
        )
        self.summary_box = ScrollableBox(
            summary_rect,
            theme.input_font,
            theme.text,
            theme.secondary,
            border_radius=theme.button_radius,
            line_color=theme.light_gray,
            text_align="center",
            show_separators=True,
            show_scrollbar=True
        )

        # Add example summary data
        example_data = [
            {"text": "Game Summary", "line_size":100},
            "",
            "Songs Played: 10",
            "Correct Guesses: 7",
            "Total Score: 700",
            "",
            "Song History:",
            {"text": "1. Blinding Lights - The Weekend (Incorrect)", "text_color": theme.error},
            {"text": "2. Dance Monkey - Tones and I (Correct)", "text_color": theme.accent},
            {"text": "3. Uptown Funk - Bruno Mars (Correct)", "text_color": theme.accent},
            {"text": "3. Uptown Funk - Bruno Mars (Correct)", "text_color": theme.accent},
            {"text": "3. Uptown Funk - Bruno Mars (Correct)", "text_color": theme.accent},
            {"text": "3. Uptown Funk - Bruno Mars (Correct)", "text_color": theme.accent},
            {"text": "3. Uptown Funk - Bruno Mars (Correct)", "text_color": theme.accent},
            {"text": "3. Uptown Funk - Bruno Mars (Correct)", "text_color": theme.accent},
            {"text": "3. Uptown Funk - Bruno Mars (Correct)", "text_color": theme.accent},
            {"text": "3. Uptown Funk - Bruno Mars (Correct)", "text_color": theme.accent},
            {"text": "3. Uptown Funk - Bruno Mars (Correct)", "text_color": theme.accent}
        ]
        
        self.summary_box.set_text(example_data)

        # Create close button
        self.close_button = Button(
            SCREEN_WIDTH//2,
            SCREEN_HEIGHT - theme.padding - 25,
            200,
            50,
            "Close",
            color=theme.error
        )

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if self.close_button.handle_event(event):
                return False

            if self.summary_box.handle_event(event):
                continue

        return True

    def draw(self):
        current_time = pygame.time.get_ticks()
        if current_time - self._last_draw_time < self._min_draw_interval:
            return
        self._last_draw_time = current_time

        screen.fill(theme.background)
        
        # # Draw title
        # title_text = theme.title_font.render("Game Summary", True, theme.accent)
        # title_rect = title_text.get_rect(center=(SCREEN_WIDTH//2, 40))
        # screen.blit(title_text, title_rect)
        
        # Draw summary box
        self.summary_box.draw(screen, "")
        
        # Draw close button
        self.close_button.draw(screen)
        
        pygame.display.flip()

    def update(self):
        # No animations to update in summary screen for now
        pass

class GameScreen:
    def __init__(self):
        self.lives = MAX_LIVES
        self.feedback_alpha = 0
        self.feedback_color = None
        self.feedback_timer = 0
        self.feedback_duration = 500  # 0.5 seconds
        self.slide_out_offest = 80
        self.song_info = ""
        self.song_info_y = -20
        self.song_info_target_y = self.song_info_y + self.slide_out_offest
        self.song_info_visible = False
        self.song_info_timer = 0
        self.song_info_duration = 1500  # 1.5 seconds
        self.song_info_slide_in_speed = 0.2
        self.song_info_slide_out_steps = [5, 5, 4, 3, 2, 1]  # Step sizes for slide-out animation
        self.song_info_slide_out_speed = 1  # Pixels per second for slide-out animation
        self.song_info_fade_out_duration = 500  # Duration of fade-out effect in milliseconds
        self.song_info_fade_out_alpha = 255  # Initial alpha value for fade-out effect
        self.show_play_window = False
        self.show_autoguess_box = True
        self.show_summary = False
        self.setup_widgets()
        self._last_draw_time = 0
        self._min_draw_interval = 16  # ~60 FPS
        self.last_key_press_time = 0
        self.last_key_spam_time = 0
        self.held_key = None

    def setup_widgets(self):
        # Input Box
        self.input_box = pygame.Rect(
            theme.padding, 
            100, 
            SCREEN_WIDTH - 2*theme.padding, 
            theme.input_height
        )
        self.input_text = ""
        self.ghost_text = "Type here..."
        self.active = False

        # Autoguess Window
        autoguess_rect = pygame.Rect(
            theme.padding, 
            self.input_box.bottom + theme.padding, 
            SCREEN_WIDTH - 2*theme.padding, 
            theme.autoguess_height
        )
        self.autoguess_box = ScrollableBox(
            autoguess_rect, 
            theme.input_font, 
            theme.text, 
            theme.secondary, 
            border_radius=theme.button_radius,
            max_distance = GUESSING_RANGE,
            line_size=32,
            text_align="left"  # Set text alignment to left
        )
        
        for i in range(100,1000,10):
            self.autoguess_box.add_text(i)

        # Buttons
        button_width = 150
        button_spacing = (SCREEN_WIDTH - 4*button_width) // 5
        self.buttons = [
            Button(
                button_spacing + button_width//2, 
                450, 
                button_width, 
                50, 
                "Replay", 
                color=theme.primary
            ),
            Button(
                2*button_spacing + 3*button_width//2, 
                450, 
                button_width, 
                50, 
                "Give Up", 
                color=theme.warning
            ),
            Button(
                3*button_spacing + 5*button_width//2, 
                450, 
                button_width, 
                50, 
                "Quit", 
                color=theme.error
            ),
            Button(
                4*button_spacing + 7*button_width//2, 
                450, 
                button_width, 
                50, 
                "Summary", 
                color=theme.secondary
            )
        ]

        # Lives Display
        self.lives_label = None
        self.update_lives_label()

    def update_lives_label(self):
        lives_text = f"Lives: {self.lives}"
        self.lives_label = theme.label_font.render(lives_text, True, theme.text)
        self.lives_label_rect = self.lives_label.get_rect(center=(SCREEN_WIDTH // 2, 20))  # Adjusted y-coordinate

    def show_song_info(self, song, artist):
        self.song_info = "{} by {}".format(song, artist)
        self.song_info_y = -20
        self.song_info_visible = True
        self.song_info_timer = pygame.time.get_ticks()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            
            # Handle input box
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.input_box.collidepoint(event.pos):
                    self.active = True
                else:
                    self.active = False

            if event.type == pygame.KEYDOWN and self.active:
                if event.key == pygame.K_RETURN:
                    # Process input
                    self.process_input(self.input_text)
                    self.input_text = ""
                elif event.key == pygame.K_BACKSPACE:
                    if pygame.key.get_mods() & (pygame.KMOD_CTRL | pygame.KMOD_CMD):
                        # Clear the entire input text if Ctrl or Cmd is held
                        self.input_text = ""
                    else:
                        self.input_text = self.input_text[:-1]
                else:
                    self.input_text += event.unicode
                    self.last_key_press_time = pygame.time.get_ticks()
                    self.held_key = event.unicode

            if event.type == pygame.KEYUP:
                if event.key == self.held_key:
                    self.held_key = None

            # Handle buttons
            for button in self.buttons:
                if button.handle_event(event):
                    if button.text == "Replay":
                        self.show_play_window = True
                        self.play_animation(5000)  # Play the animation for 5 seconds
                    elif button.text == "Give Up":
                        self.lives = max(0, self.lives - 1)
                        self.show_feedback(False)
                        self.update_lives_label()
                        self.show_song_info("Song Title", "Artist Name")
                    elif button.text == "Quit":
                        return False
                    elif button.text == "Summary":
                        self.show_summary = True
                        return False

            # Handle scrolling in autoguess box
            if self.autoguess_box.handle_event(event, game_screen=self):
                continue

        current_time = pygame.time.get_ticks()
        if self.held_key is not None and current_time - self.last_key_press_time >= 500:
            # Start spamming the held key after 0.5 seconds
            if current_time - self.last_key_spam_time >= 100:
                self.input_text += self.held_key
                self.last_key_spam_time = current_time

        if self.input_text == "" and not self.active:
            self.ghost_text = "Type here..."
        else:
            self.ghost_text = ""

        return True

    def process_input(self, text):
        if text:
            print(f"Guessing song: {text}")

    def show_feedback(self, correct):
        self.feedback_color = theme.accent if correct else theme.error
        self.feedback_alpha = 255
        self.feedback_timer = pygame.time.get_ticks()

    def update(self):
        current_time = pygame.time.get_ticks()
        if current_time - self.feedback_timer < self.feedback_duration:
            elapsed_time = current_time - self.feedback_timer
            self.feedback_alpha = int(255 * (1 - elapsed_time / self.feedback_duration))
        else:
            self.feedback_alpha = 0

        # Update song info animation
        if self.song_info_visible:
            current_time = pygame.time.get_ticks()
            elapsed_time = current_time - self.song_info_timer
            if elapsed_time < self.song_info_duration:
                if self.song_info_y < self.song_info_target_y:
                    self.song_info_y += (self.song_info_target_y - self.song_info_y) * self.song_info_slide_in_speed
            else:
                if self.song_info_y < self.input_box.top+20:  # Move down behind text box
                    if self.song_info_slide_out_steps:
                        step = self.song_info_slide_out_steps[0]
                        self.song_info_y += step  # Move down instead of up
                        if self.song_info_y >= self.input_box.top+20:
                            self.song_info_slide_out_steps.pop(0)
                    else:
                        self.song_info_y += self.song_info_slide_out_speed
                        self.song_info_fade_out_alpha = max(0, self.song_info_fade_out_alpha - (255 * self.song_info_slide_out_speed / self.song_info_fade_out_duration))
                        if self.song_info_fade_out_alpha <= 0:
                            self.song_info_visible = False

    def draw(self, do_flip=True):
        current_time = pygame.time.get_ticks()
        if current_time - self._last_draw_time < self._min_draw_interval:
            return
        self._last_draw_time = current_time
        
        screen.fill(theme.background)
        
        # Draw song info
        if self.song_info_visible:
            song_info_text = theme.song_info_font.render(self.song_info, True, theme.text)
            song_info_rect = song_info_text.get_rect(center=(SCREEN_WIDTH // 2, int(self.song_info_y)))
            song_info_text.set_alpha(self.song_info_fade_out_alpha)
            screen.blit(song_info_text, song_info_rect)
        
        # Draw lives label
        screen.blit(self.lives_label, self.lives_label_rect)
        
        # Draw input box
        pygame.draw.rect(screen, theme.secondary, self.input_box, border_radius=theme.button_radius)

        # Calculate the maximum number of characters that can fit within the input box width
        max_chars = (self.input_box.width) // theme.input_font.size("A")[0]  # Approximate width of a character

        # Get the visible portion of the input text
        visible_input_text = self.input_text[-max_chars:]  # Slice the input text to get the last max_chars characters

        input_surface = theme.input_font.render(visible_input_text, True, theme.text)
        ghost_text_surface = theme.input_font.render(self.ghost_text, True, theme.ghost_text)

        screen.blit(input_surface, (self.input_box.x + 10, self.input_box.y + 10))
        screen.blit(ghost_text_surface, (self.input_box.x + 10, self.input_box.y + 10))
        
        # Draw typing indicator
        if self.active:
            # Blink every 30 frames (2 times per second at 60fps)
            if (pygame.time.get_ticks() // 500) % 2 == 0:  # 500ms = half second
                indicator_rect = pygame.Rect(
                    self.input_box.left + 10 + input_surface.get_width(),
                    self.input_box.y + 10,
                    10,
                    self.input_box.height - 20
                )
                pygame.draw.rect(screen, theme.accent, indicator_rect)
        # Draw autoguess window or empty window based on show_play_window flag
        if not self.show_play_window or self.show_autoguess_box:
            self.autoguess_box.draw(screen, self.input_text)
        else:
            empty_window_rect = pygame.Rect(
                theme.padding,
                self.input_box.bottom + theme.padding,
                SCREEN_WIDTH - 2 * theme.padding,
                theme.autoguess_height
            )
            pygame.draw.rect(screen, theme.background, empty_window_rect, border_radius=theme.button_radius)
        
        # Draw buttons
        for button in self.buttons:
            button.draw(screen)
        
        # Draw feedback gradient with fade out effect
        if self.feedback_alpha > 0:
            gradient_width = SCREEN_WIDTH // 10  # Adjust the gradient width
            feedback_surface = pygame.Surface((gradient_width, SCREEN_HEIGHT), pygame.SRCALPHA)
            for i in range(gradient_width):
                alpha = int(self.feedback_alpha * (1 - i / gradient_width))
                color = self.feedback_color + (alpha,)
                pygame.draw.line(feedback_surface, color, (i, 0), (i, SCREEN_HEIGHT))
            
            # Fade out effect
            feedback_surface.set_alpha(self.feedback_alpha)
            
            screen.blit(feedback_surface, (0, 0))
            screen.blit(pygame.transform.flip(feedback_surface, True, False), (SCREEN_WIDTH - gradient_width, 0))
        
        if do_flip:
            pygame.display.flip()

    def play_animation(self, msPlayTime):
        
        # Create a surface for the animation
        animation_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        original_rect = self.autoguess_box.rect.copy()
        play_time = msPlayTime / 1000
        
        # Animation parameters
        grow_duration = 500  # ms
        shrink_duration = 500  # ms
        spin_duration = msPlayTime - grow_duration - shrink_duration
        start_time = pygame.time.get_ticks()
        
        # Animation loop
        while True:
            current_time = pygame.time.get_ticks()
            elapsed = current_time - start_time
            
            # Clear animation surface
            animation_surface.fill((0, 0, 0, 0))
            
            # Handle window growing
            if elapsed < grow_duration:
                progress = elapsed / grow_duration
                width = original_rect.width * progress
                height = original_rect.height * progress
                rect = pygame.Rect(
                    original_rect.centerx - width/2,
                    original_rect.centery - height/2,
                    width,
                    height
                )
                # Draw window with visible color
                pygame.draw.rect(animation_surface, theme.primary, rect, border_radius=theme.button_radius)
                pygame.draw.rect(animation_surface, theme.white, rect, 3, border_radius=theme.button_radius)
            
            # Handle spinning
            elif elapsed < grow_duration + spin_duration:
                rect = original_rect
                
                # Hide autoguess box at start of animation
                self.show_autoguess_box = False
                
                # Draw main window
                pygame.draw.rect(animation_surface, theme.primary, rect, border_radius=theme.button_radius)
                pygame.draw.rect(animation_surface, theme.white, rect, 3, border_radius=theme.button_radius)
                
                # Draw larger disc (80% of window size instead of 60%)
                disc_size = min(rect.width, rect.height) * 2  # Changed from 0.6 to 0.8
                disc_rect = pygame.Rect(0, 0, disc_size, disc_size)
                disc_rect.center = rect.center
                disc_rect.centery += rect.height * 0.05  # Reduced offset from 0.1 to 0.05
                
                # Draw disc components
                pygame.draw.circle(animation_surface, theme.background, disc_rect.center, disc_size//2)
                pygame.draw.circle(animation_surface, theme.light_gray, disc_rect.center, disc_size//10)
                pygame.draw.circle(animation_surface, theme.black, disc_rect.center, disc_size//18)
                pygame.draw.circle(animation_surface, theme.white, disc_rect.center, disc_size//2, 2)
                
                # Draw spinning animation with adjusted radius
                num_dots = 8
                radius = disc_size//2 * 0.7  # Changed from 0.8 to 0.7 to account for larger disc
                center = disc_rect.center
                angle = (elapsed - grow_duration) / spin_duration * 360
                
                for i in range(num_dots):
                    dot_angle = angle + (i * 360 / num_dots)
                    x = center[0] + radius * math.cos(math.radians(dot_angle))
                    y = center[1] + radius * math.sin(math.radians(dot_angle))
                    alpha = int(255 * (1 - (i / num_dots)))
                    dot_color = theme.accent + (alpha,)
                    pygame.draw.circle(animation_surface, dot_color, (int(x), int(y)), 8)
                
                # Draw text labels
                time_text = theme.label_font.render(f"Play Time: {play_time:.1f}s", True, theme.text)
                time_rect = time_text.get_rect(midtop=(rect.left + 100, rect.top + 20))
                animation_surface.blit(time_text, time_rect)
                
                guess_text = theme.label_font.render("Guess the Song", True, theme.text)
                guess_rect = guess_text.get_rect(midtop=(rect.right - 100, rect.top + 20))
                animation_surface.blit(guess_text, guess_rect)
            
            # Handle window shrinking
            elif elapsed < grow_duration + spin_duration + shrink_duration:
                if not self.show_autoguess_box:
                    self.show_autoguess_box = True
                progress = 1 - (elapsed - grow_duration - spin_duration) / shrink_duration
                width = original_rect.width * progress
                height = original_rect.height * progress
                rect = pygame.Rect(
                    original_rect.centerx - width/2,
                    original_rect.centery - height/2,
                    width,
                    height
                )
                pygame.draw.rect(animation_surface, theme.primary, rect, border_radius=theme.button_radius)
                pygame.draw.rect(animation_surface, theme.white, rect, 3, border_radius=theme.button_radius)
            
            else:
                break
            
            # Draw the main screen
            self.handle_events()
            self.draw(do_flip=False)
            
            # Draw the animation surface
            screen.blit(animation_surface, (0, 0))
            pygame.display.flip()
            
            # Maintain consistent frame rate
            clock.tick(60)
        
        # Reset states after animation
        self.show_play_window = False
        self.draw()

def main():
    # Start with StartScreen
    start_screen = StartScreen()
    running = True
    current_screen = start_screen
    
    while running:
        clock.tick(60)  # Limit to 60 FPS
        
        if isinstance(current_screen, StartScreen):
            running = current_screen.handle_events()
            current_screen.draw()
            if not running:
                current_screen = GameScreen()
                running = True
        
        elif isinstance(current_screen, GameScreen):
            running = current_screen.handle_events()
            if current_screen.show_summary:
                current_screen = SummaryScreen()
                running = True
            current_screen.update()
            current_screen.draw()
        
        elif isinstance(current_screen, SummaryScreen):
            running = current_screen.handle_events()
            current_screen.draw()
    
    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
