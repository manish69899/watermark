# watermark.py - PROFESSIONAL PDF Watermark Engine
# FIXED: Dynamic Per-Page Dimension Detection + Smart Caching for Mixed Page Sizes/Orientations
# IMPROVED: File Size Fix, Better Rendering, Gap Control, Position, Tile Patterns
# ALL FEATURES PRESERVED + NEW: Outline, Advanced Borders, Compression Fix
# NEW FEATURES: Underlay Mode, Dynamic Variables, Multi-line Text Support

import io
import os
import logging
import math
import hashlib
import copy
import gc
from datetime import datetime
from typing import Dict, Tuple, List, Optional, Set
from functools import lru_cache
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.utils import ImageReader

# ============================================
# LOGGING SETUP
# ============================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WatermarkEngine")

# ============================================
# COLOR DEFINITIONS - 18 Colors
# ============================================
COLORS = {
    # Original colors
    'grey': colors.Color(0.5, 0.5, 0.5),
    'red': colors.Color(0.85, 0.15, 0.15),
    'blue': colors.Color(0.15, 0.35, 0.85),
    'green': colors.Color(0.15, 0.55, 0.25),
    'purple': colors.Color(0.55, 0.15, 0.65),
    'orange': colors.Color(0.92, 0.45, 0.10),
    'yellow': colors.Color(0.88, 0.82, 0.10),
    'white': colors.Color(1, 1, 1),
    'black': colors.Color(0, 0, 0),
    'cyan': colors.Color(0.05, 0.75, 0.80),
    'pink': colors.Color(0.92, 0.38, 0.68),
    'brown': colors.Color(0.50, 0.28, 0.10),
    'gold': colors.Color(0.82, 0.62, 0.10),
    'silver': colors.Color(0.72, 0.72, 0.72),
    'navy': colors.Color(0.10, 0.20, 0.45),
    'teal': colors.Color(0.10, 0.50, 0.50),
    'maroon': colors.Color(0.55, 0.10, 0.20),
    # NEW colors
    'indigo': colors.Color(0.29, 0.00, 0.51),
    'coral': colors.Color(1.0, 0.50, 0.31),
    'olive': colors.Color(0.50, 0.50, 0.00),
}

# ============================================
# GAP SETTINGS
# ============================================
GAP_SIZES = {
    'small': 120,
    'medium': 200,
    'large': 300,
}

# ============================================
# SMART WATERMARK CACHE - PER-DIMENSION CACHING
# ============================================
_dimension_cache: Dict[Tuple[int, int], bytes] = {}
_settings_cache_key: str = ""
MAX_CACHE_SIZE = 50


def _get_settings_cache_key(settings: dict) -> str:
    """Generate unique cache key based on watermark settings (not dimensions)"""
    key_data = (
        f"{settings.get('style')}_"
        f"{settings.get('color')}_"
        f"{settings.get('opacity')}_"
        f"{settings.get('fontsize')}_"
        f"{settings.get('rotation')}_"
        f"{settings.get('content', '')[:30]}_"
        f"{settings.get('shadow')}_"
        f"{settings.get('border_style')}_"
        f"{settings.get('border_width')}_"
        f"{settings.get('double_layer')}_"
        f"{settings.get('gradient_effect')}_"
        f"{settings.get('gap')}_"
        f"{settings.get('position')}_"
        f"{settings.get('outline')}_"
        f"{settings.get('tile_pattern')}_"
        f"{settings.get('border_color')}_"
        f"{settings.get('double_layer_color')}_"
        f"{settings.get('outline_width')}_"
        f"{settings.get('underlay')}"  # NEW: Include underlay in cache key
    )
    return hashlib.md5(key_data.encode()).hexdigest()


def _get_dimension_key(width: float, height: float) -> Tuple[int, int]:
    """Normalize dimensions to integer tuple for caching"""
    return (int(round(width)), int(round(height)))


def clear_cache():
    """Clear all watermark caches"""
    global _dimension_cache, _settings_cache_key
    _dimension_cache.clear()
    _settings_cache_key = ""
    gc.collect()
    logger.info("🗑️ All caches cleared")


def safe_int(value, default=0) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value, default=0.0) -> float:
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


class WatermarkEngine:
    """
    PROFESSIONAL PDF Watermark Engine
    
    FEATURES:
    - 8 Watermark Styles
    - 20 Border Styles
    - 18 Colors
    - 8 Opacity Levels
    - Gap/Spacing Control
    - Position Presets
    - Tile Patterns
    - Text Outline Effect
    - Multiple Links
    - Custom Font Support
    - 3D Shadow Effect
    - Double Layer Watermark
    - Gradient Effect
    - Page Range Selection
    - Content Stream Compression
    
    *** NEW FEATURES ***
    - UNDERLAY MODE: Watermark behind content (professional)
    - DYNAMIC VARIABLES: {page}, {total}, {date}, {filename}, {time}
    - MULTI-LINE TEXT: Support for \\n in watermarks
    """
    
    def __init__(self, settings: dict):
        """Initialize with user settings"""
        self.settings = settings if settings else {}
        
        # Basic settings
        self.content_type = self.settings.get('type') or 'text'
        self.content = self.settings.get('content') or ''
        self.style = self.settings.get('style') or 'diagonal'
        self.opacity = safe_float(self.settings.get('opacity'), 0.3)
        self.color_name = self.settings.get('color') or 'grey'
        self.fontsize = safe_int(self.settings.get('fontsize'), 48)
        self.rotation = safe_int(self.settings.get('rotation'), 45)
        self.imgsize = safe_int(self.settings.get('imgsize'), 150)
        
        # Border settings
        self.border_style = self.settings.get('border_style') or 'simple'
        self.border_color_name = self.settings.get('border_color') or 'grey'
        self.border_width = safe_int(self.settings.get('border_width'), 2)
        
        # Premium Features
        self.shadow = (
            self.settings.get('shadow') == True or 
            self.settings.get('add_shadow') == True or 
            self.settings.get('shadow') == 'yes'
        )
        self.page_range = self.settings.get('page_range') or 'all'
        
        # Gap/Spacing Control
        self.gap_setting = self.settings.get('gap', 'medium')
        if isinstance(self.gap_setting, (int, float)):
            self.gap = safe_int(self.gap_setting, 200)
        else:
            self.gap = GAP_SIZES.get(self.gap_setting, 200)
        
        # Position
        self.position = self.settings.get('position', 'center')
        
        # Tile Pattern
        self.tile_pattern = self.settings.get('tile_pattern', 'grid')
        
        # Text Outline
        self.outline = self.settings.get('outline', False)
        self.outline_width = safe_int(self.settings.get('outline_width'), 2)
        
        # Double Layer Feature
        self.double_layer = self.settings.get('double_layer', False)
        self.double_layer_offset = safe_int(self.settings.get('double_layer_offset'), 5)
        self.double_layer_color = self.settings.get('double_layer_color', 'black')
        
        # Gradient Effect
        self.gradient_effect = self.settings.get('gradient_effect', False)
        
        # ============================================
        # NEW FEATURE: UNDERLAY MODE
        # ============================================
        # underlay=True = watermark BEHIND content (professional look)
        # underlay=False = watermark ON TOP of content (default)
        self.underlay = (
            self.settings.get('underlay') == True or
            self.settings.get('underlay') == 'yes' or
            self.settings.get('layer_order') == 'under'
        )
        
        # Custom Font Handling
        self.font_path = self.settings.get('font_path', '')
        self.font_name = 'Helvetica-Bold'
        self._custom_font_loaded = False
        
        if self.font_path and os.path.exists(self.font_path):
            try:
                font_name = f'CustomFont_{hash(self.font_path) % 10000}'
                pdfmetrics.registerFont(TTFont(font_name, self.font_path))
                self.font_name = font_name
                self._custom_font_loaded = True
                logger.info(f"✅ Custom font loaded: {self.font_path}")
            except Exception as e:
                logger.warning(f"⚠️ Font load error, using default: {e}")
        
        # Links
        self.links = self.settings.get('links') or []
        if not isinstance(self.links, list):
            self.links = []
        
        # Get color objects
        self.text_color = COLORS.get(self.color_name, COLORS['grey'])
        self.border_color = COLORS.get(self.border_color_name, COLORS['grey'])
        
        # Initialize settings cache key
        global _settings_cache_key
        _settings_cache_key = _get_settings_cache_key(self.settings)
        
        logger.info(
            f"Engine Init: style={self.style}, color={self.color_name}, "
            f"opacity={self.opacity}, shadow={self.shadow}, underlay={self.underlay}"
        )

    # ============================================
    # NEW FEATURE: DYNAMIC VARIABLES REPLACEMENT
    # ============================================
    def _replace_variables(self, text: str, page_num: int = 1, total_pages: int = 1, 
                          filename: str = "document.pdf") -> str:
        """
        Replace dynamic variables in text with actual values.
        
        Supported Variables:
        - {page} or {p}      : Current page number (1-indexed)
        - {total} or {t}     : Total number of pages
        - {date} or {d}      : Current date (DD-MM-YYYY)
        - {time}             : Current time (HH:MM)
        - {datetime}         : Date and time (DD-MM-YYYY HH:MM)
        - {filename} or {f}  : PDF filename without extension
        - {year} or {y}      : Current year (YYYY)
        - {month} or {m}     : Current month (MM)
        - {day}              : Current day (DD)
        """
        if not text or '{' not in text:
            return text
        
        from datetime import datetime
        now = datetime.now()
        
        # Get filename without extension
        clean_filename = os.path.splitext(os.path.basename(filename))[0]
        
        # Replace all variables
        replacements = {
            # Page numbers
            '{page}': str(page_num),
            '{p}': str(page_num),
            '{total}': str(total_pages),
            '{t}': str(total_pages),
            
            # Date/Time
            '{date}': now.strftime('%d-%m-%Y'),
            '{d}': now.strftime('%d-%m-%Y'),
            '{time}': now.strftime('%H:%M'),
            '{datetime}': now.strftime('%d-%m-%Y %H:%M'),
            '{year}': now.strftime('%Y'),
            '{y}': now.strftime('%Y'),
            '{month}': now.strftime('%m'),
            '{m}': now.strftime('%m'),
            '{day}': now.strftime('%d'),
            
            # Filename
            '{filename}': clean_filename,
            '{f}': clean_filename,
        }
        
        result = text
        for var, value in replacements.items():
            result = result.replace(var, value)
        
        return result

    # ============================================
    # NEW FEATURE: MULTI-LINE TEXT HANDLING
    # ============================================
    def _split_multiline(self, text: str) -> List[str]:
        """
        Split text into multiple lines.
        
        Supports:
        - \\n (literal backslash-n)
        - Actual newline characters
        """
        if not text:
            return []
        
        # Handle both \n literal and actual newlines
        text = text.replace('\\n', '\n')
        lines = text.split('\n')
        
        return [line for line in lines if line.strip()]

    def _draw_multiline_text(self, can: canvas.Canvas, x: float, y: float, 
                             text: str, draw_func: str = "drawCentredString",
                             page_num: int = 1, total_pages: int = 1,
                             filename: str = "document.pdf") -> float:
        """
        Draw multi-line text with proper vertical spacing.
        
        Returns: Total height of all lines drawn
        """
        lines = self._split_multiline(text)
        if not lines:
            return 0
        
        # Replace variables in each line
        lines = [self._replace_variables(line, page_num, total_pages, filename) 
                 for line in lines]
        
        # Calculate line height based on font size
        line_height = self.fontsize * 1.2  # 20% extra spacing
        
        # Total height of text block
        total_height = line_height * (len(lines) - 1)
        
        # Starting Y position (centered vertically)
        current_y = y + (total_height / 2) if draw_func == "drawCentredString" else y
        
        for i, line in enumerate(lines):
            if i > 0:
                current_y -= line_height
            
            if draw_func == "drawCentredString":
                self._draw_text_with_shadow(can, x, current_y, line, "drawCentredString")
            else:
                self._draw_text_with_shadow(can, x, current_y, line, "drawString")
        
        return total_height

    def create_watermark_layer(self, width: float, height: float, 
                               page_num: int = 1, total_pages: int = 1,
                               filename: str = "document.pdf") -> io.BytesIO:
        """Create watermark layer with multi-line and variable support"""
        
        dim_key = _get_dimension_key(width, height)
        
        # For variables to work, we can't cache if variables are present
        has_variables = self.content and '{' in self.content
        is_multiline = self.content and ('\n' in self.content or '\\n' in self.content)
        
        # Skip cache if dynamic content (variables or multi-line with variables)
        if not has_variables and dim_key in _dimension_cache:
            current_key = _get_settings_cache_key(self.settings)
            global _settings_cache_key
            if current_key == _settings_cache_key:
                logger.info(f"📦 Using cached watermark: {dim_key[0]}x{dim_key[1]}")
                return io.BytesIO(_dimension_cache[dim_key])
        
        # Create new layer
        logger.info(f"🆕 Creating watermark: {dim_key[0]}x{dim_key[1]}")
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=(width, height))
        
        # Draw watermark based on style
        style_method = {
            'diagonal': self._draw_diagonal,
            'grid': self._draw_grid,
            'topright': lambda c, w, h: self._draw_corner(c, w, h, 'topright'),
            'bottomleft': lambda c, w, h: self._draw_corner(c, w, h, 'bottomleft'),
            'overlay': self._draw_overlay,
            'border': self._draw_border,
            'header': self._draw_header,
            'footer': self._draw_footer,
        }.get(self.style, self._draw_diagonal)
        
        style_method(can, width, height, page_num, total_pages, filename)
        
        # Double Layer Effect
        if self.double_layer and self.content_type == 'text':
            self._draw_double_layer(can, width, height, page_num, total_pages, filename)
        
        # Draw all links
        for link in self.links:
            if isinstance(link, dict) and link.get('url'):
                self._draw_link_button(can, width, height, link)
        
        can.save()
        
        # Cache only if no variables (static content)
        packet.seek(0)
        data = packet.read()
        
        if not has_variables and len(_dimension_cache) < MAX_CACHE_SIZE:
            _dimension_cache[dim_key] = data
        
        return io.BytesIO(data)

    def _get_page_dimensions(self, page) -> Tuple[float, float, str]:
        """Extract page dimensions considering rotation"""
        try:
            raw_width = float(page.mediabox.width)
            raw_height = float(page.mediabox.height)
            
            rotation = 0
            if hasattr(page, 'get') and '/Rotate' in page:
                rotation = int(page['/Rotate'])
            
            if rotation in [90, 270, -90, -270]:
                effective_width = raw_height
                effective_height = raw_width
            else:
                effective_width = raw_width
                effective_height = raw_height
            
            orientation = 'portrait' if effective_height >= effective_width else 'landscape'
            return effective_width, effective_height, orientation
        except:
            return 612.0, 792.0, 'portrait'

    # ============================================
    # TEXT DRAWING HELPER
    # ============================================
    def _draw_text_with_shadow(self, can: canvas.Canvas, x: float, y: float, 
                               text: str, draw_func: str = "drawString"):
        """Draw text with shadow/outline effects"""
        can.saveState()
        
        # Outline Effect
        if self.outline:
            can.setStrokeColor(colors.black)
            can.setLineWidth(self.outline_width)
            can.setFillColor(self.text_color)
            can.setFillAlpha(self.opacity)
            
            if draw_func == "drawCentredString":
                can.drawCentredString(x, y, text)
            else:
                can.drawString(x, y, text)
            can.restoreState()
            return
        
        # Shadow Effect
        if self.shadow:
            shadow_opacity = self.opacity * 0.3
            offset_base = max(2, self.fontsize // 12)
            
            for layer in range(3, 0, -1):
                can.setFillColor(COLORS['black'])
                can.setFillAlpha(shadow_opacity * (layer / 6))
                offset = offset_base * layer
                
                if draw_func == "drawCentredString":
                    can.drawCentredString(x + offset, y - offset, text)
                else:
                    can.drawString(x + offset, y - offset, text)
        
        # Gradient Effect
        if self.gradient_effect:
            can.setFillColor(self.text_color)
            can.setFillAlpha(self.opacity * 0.6)
            
            if draw_func == "drawCentredString":
                can.drawCentredString(x, y, text)
            else:
                can.drawString(x, y, text)
            
            can.setFillAlpha(self.opacity)
            if draw_func == "drawCentredString":
                can.drawCentredString(x + 0.5, y + 0.5, text)
            else:
                can.drawString(x + 0.5, y + 0.5, text)
        else:
            can.setFillColor(self.text_color)
            can.setFillAlpha(self.opacity)
            
            if draw_func == "drawCentredString":
                can.drawCentredString(x, y, text)
            else:
                can.drawString(x, y, text)
        
        can.restoreState()

    def _get_position_coords(self, w: float, h: float) -> Tuple[float, float]:
        """Get x, y coordinates based on position setting"""
        positions = {
            'center': (w / 2, h / 2),
            'topright': (w * 0.75, h * 0.75),
            'topleft': (w * 0.25, h * 0.75),
            'bottomleft': (w * 0.25, h * 0.25),
            'bottomright': (w * 0.75, h * 0.25),
            'topcenter': (w / 2, h * 0.75),
            'bottomcenter': (w / 2, h * 0.25),
        }
        return positions.get(self.position, (w / 2, h / 2))

    def _draw_double_layer(self, can: canvas.Canvas, w: float, h: float,
                          page_num: int = 1, total_pages: int = 1, filename: str = "document.pdf"):
        """Draw second watermark layer"""
        if self.content_type != 'text' or not self.content:
            return
        
        # Process variables
        text = self._replace_variables(self.content, page_num, total_pages, filename)
        
        can.saveState()
        x, y = self._get_position_coords(w, h)
        can.translate(x, y)
        can.rotate(self.rotation + 90)
        
        second_color = COLORS.get(self.double_layer_color, COLORS['black'])
        can.setFillColor(second_color)
        can.setFillAlpha(self.opacity * 0.12)
        can.setFont(self.font_name, self.fontsize * 0.75)
        
        # Handle multi-line in double layer
        lines = self._split_multiline(text)
        if lines:
            line_height = self.fontsize * 0.75 * 1.2
            start_y = (len(lines) - 1) * line_height / 2
            
            for i, line in enumerate(lines):
                offset = self.double_layer_offset * 3
                can.drawCentredString(offset, start_y - i * line_height + offset, line)
        else:
            offset = self.double_layer_offset * 3
            can.drawCentredString(offset, offset, text)
        
        can.restoreState()

    # ============================================
    # STYLE: DIAGONAL - WITH MULTI-LINE & VARIABLES
    # ============================================
    def _draw_diagonal(self, can: canvas.Canvas, w: float, h: float,
                       page_num: int = 1, total_pages: int = 1,
                       filename: str = "document.pdf"):
        can.saveState()
        x, y = self._get_position_coords(w, h)
        can.translate(x, y)
        can.rotate(self.rotation)
        
        if self.content_type == 'text' and self.content:
            # Replace variables
            processed_text = self._replace_variables(self.content, page_num, total_pages, filename)
            
            can.setFont(self.font_name, self.fontsize)
            
            # Check for multi-line
            lines = self._split_multiline(processed_text)
            if len(lines) > 1:
                line_height = self.fontsize * 1.2
                start_y = (len(lines) - 1) * line_height / 2
                
                for i, line in enumerate(lines):
                    self._draw_text_with_shadow(can, 0, start_y - i * line_height, line)
            else:
                self._draw_text_with_shadow(can, 0, 0, processed_text)
            
        elif self.content_type == 'image' and self.content and os.path.exists(self.content):
            can.setFillAlpha(self.opacity)
            size = self.imgsize
            try:
                can.drawImage(self.content, -size/2, -size/2, 
                             width=size, height=size, mask='auto', preserveAspectRatio=True)
            except Exception as e:
                logger.error(f"Image error: {e}")
        can.restoreState()

    # ============================================
    # STYLE: GRID - WITH MULTI-LINE & VARIABLES
    # ============================================
    def _draw_grid(self, can: canvas.Canvas, w: float, h: float,
                   page_num: int = 1, total_pages: int = 1,
                   filename: str = "document.pdf"):
        """Grid/tile pattern with multi-line support"""
        
        if self.tile_pattern == 'honeycomb':
            self._draw_honeycomb(can, w, h, page_num, total_pages, filename)
            return
        elif self.tile_pattern == 'wave':
            self._draw_wave_pattern(can, w, h, page_num, total_pages, filename)
            return
        elif self.tile_pattern == 'spiral':
            self._draw_spiral_pattern(can, w, h, page_num, total_pages, filename)
            return
        
        can.saveState()
        can.translate(w / 2, h / 2)
        can.rotate(self.rotation)
        
        if self.content_type == 'text' and self.content:
            fontsize = max(14, self.fontsize // 2)
            can.setFont(self.font_name, fontsize)
            
            # Process variables
            processed_text = self._replace_variables(self.content, page_num, total_pages, filename)
            lines = self._split_multiline(processed_text)
        else:
            fontsize = 18
            lines = None
        
        gap = self.gap
        extent = int(math.sqrt(w*w + h*h) / 2) + gap
        
        for x in range(-extent, extent + 1, gap):
            for y in range(-extent, extent + 1, gap):
                if self.content_type == 'text' and self.content:
                    if lines and len(lines) > 1:
                        line_height = fontsize * 1.1
                        start_y = (len(lines) - 1) * line_height / 2
                        for i, line in enumerate(lines):
                            self._draw_text_with_shadow(can, x, start_y - i * line_height + y, line)
                    elif lines:
                        self._draw_text_with_shadow(can, x, y, lines[0])
                    else:
                        self._draw_text_with_shadow(can, x, y, processed_text)
                        
                elif self.content_type == 'image' and self.content and os.path.exists(self.content):
                    size = self.imgsize // 2
                    can.setFillAlpha(self.opacity)
                    try:
                        can.drawImage(self.content, x - size/2, y - size/2,
                                     width=size, height=size, mask='auto')
                    except:
                        pass
        can.restoreState()

    def _draw_honeycomb(self, can: canvas.Canvas, w: float, h: float,
                        page_num: int = 1, total_pages: int = 1,
                        filename: str = "document.pdf"):
        """Honeycomb pattern with variables"""
        can.saveState()
        fontsize = max(14, self.fontsize // 2)
        can.setFont(self.font_name, fontsize)
        
        processed_text = self._replace_variables(self.content, page_num, total_pages, filename)
        lines = self._split_multiline(processed_text)
        
        gap = self.gap
        row = 0
        y = h + gap
        
        while y > -gap:
            x_offset = (row % 2) * (gap / 2)
            x = x_offset
            
            while x < w + gap:
                can.saveState()
                can.translate(x, y)
                can.rotate(self.rotation)
                
                if self.content_type == 'text' and self.content:
                    if lines and len(lines) > 1:
                        line_height = fontsize * 1.1
                        start_y = (len(lines) - 1) * line_height / 2
                        for i, line in enumerate(lines):
                            self._draw_text_with_shadow(can, 0, start_y - i * line_height, line)
                    elif lines:
                        self._draw_text_with_shadow(can, 0, 0, lines[0])
                
                can.restoreState()
                x += gap
            
            y -= gap * 0.866
            row += 1
        
        can.restoreState()

    def _draw_wave_pattern(self, can: canvas.Canvas, w: float, h: float,
                          page_num: int = 1, total_pages: int = 1,
                          filename: str = "document.pdf"):
        """Wave pattern with variables"""
        can.saveState()
        fontsize = max(14, self.fontsize // 2)
        can.setFont(self.font_name, fontsize)
        
        processed_text = self._replace_variables(self.content, page_num, total_pages, filename)
        lines = self._split_multiline(processed_text)
        
        gap = self.gap
        amplitude = gap * 0.3
        
        y = gap
        wave_idx = 0
        
        while y < h + gap:
            x = gap
            while x < w + gap:
                wave_offset = math.sin(x * 0.02 + wave_idx) * amplitude
                
                can.saveState()
                can.translate(x, y + wave_offset)
                can.rotate(self.rotation)
                
                if self.content_type == 'text' and self.content:
                    if lines and len(lines) > 1:
                        line_height = fontsize * 1.1
                        start_y = (len(lines) - 1) * line_height / 2
                        for i, line in enumerate(lines):
                            self._draw_text_with_shadow(can, 0, start_y - i * line_height, line)
                    elif lines:
                        self._draw_text_with_shadow(can, 0, 0, lines[0])
                
                can.restoreState()
                x += gap
            
            y += gap
            wave_idx += 0.5
        
        can.restoreState()

    def _draw_spiral_pattern(self, can: canvas.Canvas, w: float, h: float,
                            page_num: int = 1, total_pages: int = 1,
                            filename: str = "document.pdf"):
        """Spiral pattern with variables"""
        can.saveState()
        can.translate(w/2, h/2)
        
        fontsize = max(12, self.fontsize // 2)
        can.setFont(self.font_name, fontsize)
        
        processed_text = self._replace_variables(self.content, page_num, total_pages, filename)
        
        theta = 0
        radius = 30
        
        while radius < min(w, h) / 2:
            x = radius * math.cos(theta)
            y = radius * math.sin(theta)
            
            fade = 1 - (radius / (min(w, h) / 2)) * 0.5
            
            can.saveState()
            can.setFillColor(self.text_color)
            can.setFillAlpha(self.opacity * fade)
            can.drawCentredString(x, y, processed_text)
            can.restoreState()
            
            theta += 0.4
            radius += max(2, self.gap // 20)
        
        can.restoreState()

    def _draw_corner(self, can: canvas.Canvas, w: float, h: float, corner: str,
                    page_num: int = 1, total_pages: int = 1,
                    filename: str = "document.pdf"):
        margin = 50
        fontsize = max(14, self.fontsize // 2)
        
        if corner == 'topright':
            x = w - margin
            y = h - margin - fontsize
        else:
            x = margin
            y = margin
        
        can.saveState()
        
        if self.content_type == 'text' and self.content:
            can.setFont(self.font_name, fontsize)
            
            processed_text = self._replace_variables(self.content, page_num, total_pages, filename)
            lines = self._split_multiline(processed_text)
            
            if lines and len(lines) > 1:
                line_height = fontsize * 1.2
                for i, line in enumerate(lines):
                    if corner == 'topright':
                        text_width = can.stringWidth(line, self.font_name, fontsize)
                        self._draw_text_with_shadow(can, x - text_width, y - i * line_height, line)
                    else:
                        self._draw_text_with_shadow(can, x, y + i * line_height, line)
            else:
                if corner == 'topright':
                    text_width = can.stringWidth(processed_text, self.font_name, fontsize)
                    self._draw_text_with_shadow(can, x - text_width, y, processed_text)
                else:
                    self._draw_text_with_shadow(can, x, y, processed_text)
                
        elif self.content_type == 'image' and self.content and os.path.exists(self.content):
            size = self.imgsize // 2
            can.setFillAlpha(self.opacity)
            if corner == 'topright':
                can.drawImage(self.content, x - size, y - size, width=size, height=size, mask='auto')
            else:
                can.drawImage(self.content, x, y, width=size, height=size, mask='auto')
        
        can.restoreState()

    def _draw_overlay(self, can: canvas.Canvas, w: float, h: float,
                     page_num: int = 1, total_pages: int = 1,
                     filename: str = "document.pdf"):
        if self.content_type != 'text' or not self.content:
            return
        
        can.saveState()
        fontsize = self.fontsize
        gap = max(fontsize * 4, self.gap)
        
        processed_text = self._replace_variables(self.content, page_num, total_pages, filename)
        
        # For overlay, use first line only or single line
        lines = self._split_multiline(processed_text)
        text = lines[0] if lines else processed_text
        text = text + "  •  "
        
        for y_offset in range(int(h + w), int(-h - w), -gap):
            can.saveState()
            can.translate(0, y_offset)
            can.rotate(-45)
            
            can.setFont(self.font_name, fontsize)
            text_width = can.stringWidth(text, self.font_name, fontsize)
            
            x = -w
            while x < w * 2:
                self._draw_text_with_shadow(can, x, 0, text)
                x += text_width * 1.2
            can.restoreState()
        
        can.restoreState()

    # ============================================
    # STYLE: BORDER - ALL 20 STYLES
    # ============================================
    def _draw_border(self, can: canvas.Canvas, w: float, h: float,
                    page_num: int = 1, total_pages: int = 1,
                    filename: str = "document.pdf"):
        margin = 25
        inner_margin = margin + 8
        bwidth = max(1, self.border_width)
        
        can.saveState()
        can.setStrokeColor(self.border_color)
        can.setFillColor(self.border_color)
        can.setFillAlpha(self.opacity)
        
        border_methods = {
            'simple': lambda: self._draw_simple_border(can, w, h, margin, bwidth),
            'double': lambda: self._draw_double_border(can, w, h, margin, inner_margin, bwidth),
            'thick': lambda: self._draw_thick_border(can, w, h, margin, bwidth),
            'dotted': lambda: self._draw_dotted_border(can, w, h, margin, bwidth),
            'star': lambda: self._draw_symbol_border(can, w, h, margin, bwidth, '★'),
            'diamond': lambda: self._draw_symbol_border(can, w, h, margin, bwidth, '◆'),
            'circle': lambda: self._draw_symbol_border(can, w, h, margin, bwidth, '●'),
            'square': lambda: self._draw_symbol_border(can, w, h, margin, bwidth, '■'),
            'glitter': lambda: self._draw_glitter_border(can, w, h, margin, bwidth),
            'elegant': lambda: self._draw_elegant_border(can, w, h, margin, bwidth),
            'flower': lambda: self._draw_symbol_border(can, w, h, margin, bwidth, '✿'),
            'corporate': lambda: self._draw_corporate_border(can, w, h, margin, bwidth),
            'wave': lambda: self._draw_wave_border(can, w, h, margin, bwidth),
            'gradient': lambda: self._draw_gradient_border(can, w, h, margin, bwidth),
            'stamp': lambda: self._draw_stamp_border(can, w, h, margin, bwidth),
            'artdeco': lambda: self._draw_artdeco_border(can, w, h, margin, bwidth),
            'neon': lambda: self._draw_neon_border(can, w, h, margin, bwidth),
            'ornament': lambda: self._draw_ornament_border(can, w, h, margin, bwidth),
            'dashdot': lambda: self._draw_dashdot_border(can, w, h, margin, bwidth),
            'certificate': lambda: self._draw_certificate_border(can, w, h, margin, bwidth),
        }
        
        method = border_methods.get(self.border_style, border_methods['simple'])
        method()
        
        can.restoreState()
        
        # Draw text at bottom with variables
        if self.content_type == 'text' and self.content:
            can.saveState()
            can.setFont(self.font_name, 12)
            
            processed_text = self._replace_variables(self.content, page_num, total_pages, filename)
            lines = self._split_multiline(processed_text)
            
            if lines and len(lines) > 1:
                line_height = 14
                start_y = margin - 18
                for i, line in enumerate(lines):
                    text_width = can.stringWidth(line, self.font_name, 12)
                    self._draw_text_with_shadow(can, (w - text_width) / 2, start_y - i * line_height, line)
            else:
                text_width = can.stringWidth(processed_text, self.font_name, 12)
                self._draw_text_with_shadow(can, (w - text_width) / 2, margin - 18, processed_text)
            
            can.restoreState()

    # Border drawing methods (unchanged)
    def _draw_simple_border(self, can, w, h, margin, bwidth):
        can.setLineWidth(bwidth)
        can.rect(margin, margin, w - 2*margin, h - 2*margin, stroke=1, fill=0)

    def _draw_double_border(self, can, w, h, margin, inner_margin, bwidth):
        can.setLineWidth(bwidth)
        can.rect(margin, margin, w - 2*margin, h - 2*margin, stroke=1, fill=0)
        can.setLineWidth(max(1, bwidth - 1))
        can.rect(inner_margin, inner_margin, w - 2*inner_margin, h - 2*inner_margin, stroke=1, fill=0)

    def _draw_thick_border(self, can, w, h, margin, bwidth):
        can.setLineWidth(bwidth + 4)
        can.rect(margin, margin, w - 2*margin, h - 2*margin, stroke=1, fill=0)

    def _draw_dotted_border(self, can, w, h, margin, bwidth):
        can.setLineWidth(bwidth)
        can.setDash([4, 4], 0)
        can.rect(margin, margin, w - 2*margin, h - 2*margin, stroke=1, fill=0)

    def _draw_symbol_border(self, can, w, h, margin, bwidth, symbol):
        self._draw_corner_symbols(can, w, h, margin, symbol)
        can.setLineWidth(bwidth)
        can.rect(margin + 20, margin + 20, w - 2*margin - 40, h - 2*margin - 40, stroke=1, fill=0)

    def _draw_glitter_border(self, can, w, h, margin, bwidth):
        self._draw_corner_symbols(can, w, h, margin, '✦')
        can.setLineWidth(bwidth)
        can.setDash([2, 3], 0)
        can.rect(margin, margin, w - 2*margin, h - 2*margin, stroke=1, fill=0)

    def _draw_elegant_border(self, can, w, h, margin, bwidth):
        can.setLineWidth(1)
        can.rect(margin, margin, w - 2*margin, h - 2*margin, stroke=1, fill=0)
        corner_len = 25
        can.setLineWidth(2)
        corners = [(margin, margin, 1, 1), (margin, h - margin, 1, -1),
                   (w - margin, margin, -1, 1), (w - margin, h - margin, -1, -1)]
        for x, y, dx, dy in corners:
            can.line(x, y, x + corner_len * dx, y)
            can.line(x, y, x, y + corner_len * dy)

    def _draw_corporate_border(self, can, w, h, margin, bwidth):
        can.setLineWidth(bwidth + 3)
        can.rect(margin, margin, w - 2*margin, h - 2*margin, stroke=1, fill=0)
        can.setLineWidth(1)
        can.rect(margin + 6, margin + 6, w - 2*margin - 12, h - 2*margin - 12, stroke=1, fill=0)

    def _draw_corner_symbols(self, can, w, h, margin, symbol):
        can.setFont('Helvetica', 16)
        positions = [(margin - 8, margin - 8), (margin - 8, h - margin - 8),
                     (w - margin - 12, margin - 8), (w - margin - 12, h - margin - 8)]
        for x, y in positions:
            can.drawString(x, y, symbol)

    def _draw_wave_border(self, can, w, h, margin, bwidth):
        can.setLineWidth(bwidth)
        points = 60
        
        p = can.beginPath()
        p.moveTo(margin, h - margin)
        for i in range(points + 1):
            x = margin + (w - 2*margin) * i / points
            y = h - margin + math.sin(i * 0.4) * 5
            p.lineTo(x, y)
        can.drawPath(p, stroke=1, fill=0)
        
        p = can.beginPath()
        p.moveTo(margin, margin)
        for i in range(points + 1):
            x = margin + (w - 2*margin) * i / points
            y = margin + math.sin(i * 0.4) * 5
            p.lineTo(x, y)
        can.drawPath(p, stroke=1, fill=0)
        
        can.line(margin, margin, margin, h - margin)
        can.line(w - margin, margin, w - margin, h - margin)

    def _draw_gradient_border(self, can, w, h, margin, bwidth):
        for i in range(5):
            offset = i * 3
            can.setStrokeColor(self.border_color)
            can.setFillAlpha(self.opacity * (1 - i * 0.15))
            can.setLineWidth(bwidth + i * 2)
            can.rect(margin + offset, margin + offset, 
                     w - 2*margin - 2*offset, h - 2*margin - 2*offset, stroke=1, fill=0)

    def _draw_stamp_border(self, can, w, h, margin, bwidth):
        can.setLineWidth(bwidth)
        can.rect(margin + 10, margin + 10, w - 2*margin - 20, h - 2*margin - 20, stroke=1, fill=0)
        
        for i in range(int((w - 2*margin) / 12)):
            x = margin + 12 + i * 12
            can.circle(x, h - margin, 3, stroke=1, fill=0)
            can.circle(x, margin, 3, stroke=1, fill=0)
        
        for i in range(int((h - 2*margin) / 12)):
            y = margin + 12 + i * 12
            can.circle(margin, y, 3, stroke=1, fill=0)
            can.circle(w - margin, y, 3, stroke=1, fill=0)

    def _draw_artdeco_border(self, can, w, h, margin, bwidth):
        can.setLineWidth(bwidth)
        can.rect(margin, margin, w - 2*margin, h - 2*margin, stroke=1, fill=0)
        
        corner_size = 25
        corners = [(margin, margin, 1, 1), (margin, h - margin, 1, -1),
                   (w - margin, margin, -1, 1), (w - margin, h - margin, -1, -1)]
        
        for x, y, dx, dy in corners:
            can.setLineWidth(1)
            can.line(x, y, x + corner_size * dx, y)
            can.line(x, y, x, y + corner_size * dy)
            can.line(x + corner_size * dx * 0.5, y, x + corner_size * dx * 0.5, y + corner_size * dy * 0.5)
            can.line(x, y + corner_size * dy * 0.5, x + corner_size * dx * 0.5, y + corner_size * dy * 0.5)

    def _draw_neon_border(self, can, w, h, margin, bwidth):
        for i in range(8, 0, -1):
            can.setStrokeColor(self.border_color)
            can.setFillAlpha(self.opacity * (i / 16))
            can.setLineWidth(bwidth + i * 2)
            can.rect(margin, margin, w - 2*margin, h - 2*margin, stroke=1, fill=0)

    def _draw_ornament_border(self, can, w, h, margin, bwidth):
        can.setLineWidth(bwidth)
        can.rect(margin + 20, margin + 20, w - 2*margin - 40, h - 2*margin - 40, stroke=1, fill=0)
        
        ornaments = ['❖', '◆', '✧', '✦']
        can.setFont('Helvetica', 18)
        positions = [(margin + 5, h - margin - 12), (w - margin - 18, h - margin - 12),
                     (margin + 5, margin + 2), (w - margin - 18, margin + 2)]
        for (x, y), ornament in zip(positions, ornaments):
            can.drawString(x, y, ornament)

    def _draw_dashdot_border(self, can, w, h, margin, bwidth):
        can.setLineWidth(bwidth)
        can.setDash([10, 3, 2, 3], 0)
        can.rect(margin, margin, w - 2*margin, h - 2*margin, stroke=1, fill=0)

    def _draw_certificate_border(self, can, w, h, margin, bwidth):
        for offset in [0, 5, 10]:
            can.setLineWidth(bwidth - offset // 4)
            can.rect(margin + offset, margin + offset, 
                     w - 2*margin - 2*offset, h - 2*margin - 2*offset, stroke=1, fill=0)
        
        can.setFont('Helvetica', 20)
        can.drawString(margin - 3, h - margin - 10, '❮')
        can.drawString(w - margin - 12, h - margin - 10, '❯')
        can.drawString(margin - 3, margin - 2, '❮')
        can.drawString(w - margin - 12, margin - 2, '❯')

    # ============================================
    # STYLE: HEADER & FOOTER - WITH VARIABLES
    # ============================================
    def _draw_header(self, can: canvas.Canvas, w: float, h: float,
                    page_num: int = 1, total_pages: int = 1,
                    filename: str = "document.pdf"):
        if self.content_type != 'text' or not self.content:
            return
        
        can.saveState()
        can.setStrokeColor(self.text_color)
        can.setLineWidth(0.5)
        can.setFillAlpha(self.opacity)
        can.line(30, h - 35, w - 30, h - 35)
        
        fontsize = max(12, self.fontsize // 2)
        can.setFont(self.font_name, fontsize)
        
        processed_text = self._replace_variables(self.content, page_num, total_pages, filename)
        lines = self._split_multiline(processed_text)
        
        if lines and len(lines) > 1:
            line_height = fontsize * 1.1
            for i, line in enumerate(lines):
                text_width = can.stringWidth(line, self.font_name, fontsize)
                self._draw_text_with_shadow(can, (w - text_width) / 2, h - 28 - i * line_height, line)
        else:
            text_width = can.stringWidth(processed_text, self.font_name, fontsize)
            self._draw_text_with_shadow(can, (w - text_width) / 2, h - 28, processed_text)
        
        can.restoreState()

    def _draw_footer(self, can: canvas.Canvas, w: float, h: float,
                    page_num: int = 1, total_pages: int = 1,
                    filename: str = "document.pdf"):
        if self.content_type != 'text' or not self.content:
            return
        
        can.saveState()
        can.setStrokeColor(self.text_color)
        can.setLineWidth(0.5)
        can.setFillAlpha(self.opacity)
        can.line(30, 30, w - 30, 30)
        
        fontsize = max(12, self.fontsize // 2)
        can.setFont(self.font_name, fontsize)
        
        processed_text = self._replace_variables(self.content, page_num, total_pages, filename)
        lines = self._split_multiline(processed_text)
        
        if lines and len(lines) > 1:
            line_height = fontsize * 1.1
            for i, line in enumerate(lines):
                text_width = can.stringWidth(line, self.font_name, fontsize)
                self._draw_text_with_shadow(can, (w - text_width) / 2, 12 + i * line_height, line)
        else:
            text_width = can.stringWidth(processed_text, self.font_name, fontsize)
            self._draw_text_with_shadow(can, (w - text_width) / 2, 12, processed_text)
        
        can.restoreState()

    def _draw_link_button(self, can: canvas.Canvas, w: float, h: float, link: dict):
        try:
            url = link.get('url', '')
            position = link.get('position', 'bottomcenter')
            text = link.get('text', '🔗 CLICK HERE')
            if not url:
                return
            
            if 'top' in position:
                y_pos = h - 22
            else:
                y_pos = 18
            
            if 'left' in position:
                x_pos = 80
            elif 'right' in position:
                x_pos = w - 80
            else:
                x_pos = w / 2
            
            can.saveState()
            can.setFont('Helvetica-Bold', 10)
            text_width = can.stringWidth(text, 'Helvetica-Bold', 10)
            btn_w = text_width + 20
            btn_h = 18
            x1 = x_pos - btn_w / 2
            y1 = y_pos - btn_h / 2
            
            can.setFillColor(colors.Color(0, 0, 0, alpha=0.12))
            can.roundRect(x1 + 1.5, y1 - 1.5, btn_w, btn_h, 5, stroke=0, fill=1)
            
            can.setFillColor(colors.Color(0.98, 0.98, 1.0))
            can.setStrokeColor(colors.Color(0.2, 0.4, 0.85))
            can.setLineWidth(1)
            can.roundRect(x1, y1, btn_w, btn_h, 5, stroke=1, fill=1)
            
            can.setFillColor(colors.Color(0.15, 0.3, 0.8))
            can.drawCentredString(x_pos, y_pos - 3, text)
            
            can.linkURL(url, (x1, y1, x1 + btn_w, y1 + btn_h), relative=1)
            can.restoreState()
        except Exception as e:
            logger.error(f"Link error: {e}")

    # ============================================
    # PROCESS PDF - WITH UNDERLAY MODE
    # ============================================
    def process_pdf(self, input_path: str, output_path: str, 
                    filename: str = "document.pdf",
                    progress_callback=None) -> Tuple[bool, str]:
        """
        Process PDF with:
        - Dynamic per-page dimensions
        - UNDERLAY MODE (watermark behind content)
        - DYNAMIC VARIABLES per page
        - MULTI-LINE TEXT support
        """
        try:
            if not os.path.exists(input_path):
                return False, "Input file not found"
            
            reader = PdfReader(input_path)
            total_pages = len(reader.pages)
            if total_pages == 0:
                return False, "PDF has no pages"
            
            # Log underlay mode
            if self.underlay:
                logger.info(f"📄 UNDERLAY MODE: Watermark will be BEHIND content")
            
            logger.info(f"📄 Processing: {filename} | Pages: {total_pages}")
            
            writer = PdfWriter()
            pages_to_watermark = self._get_pages_to_watermark(total_pages)
            
            # Cache for watermarks (only for static content - no variables)
            watermark_cache: Dict[Tuple[int, int], any] = {}
            dimension_stats: Dict[Tuple[int, int], int] = {}
            
            # Check if content has dynamic variables
            has_variables = self.content and '{' in self.content
            if has_variables:
                logger.info("📊 Dynamic variables detected - per-page watermark generation enabled")
            
            for index, page in enumerate(reader.pages):
                if progress_callback and index % 10 == 0:
                    try:
                        progress_callback(index + 1, total_pages)
                    except:
                        pass
                
                if index in pages_to_watermark:
                    page_width, page_height, orientation = self._get_page_dimensions(page)
                    dim_key = _get_dimension_key(page_width, page_height)
                    
                    dimension_stats[dim_key] = dimension_stats.get(dim_key, 0) + 1
                    
                    # For pages with variables, always create fresh watermark
                    if has_variables:
                        watermark_packet = self.create_watermark_layer(
                            page_width, page_height, 
                            page_num=index + 1, 
                            total_pages=total_pages,
                            filename=filename
                        )
                        watermark_pdf = PdfReader(watermark_packet)
                        watermark_page = watermark_pdf.pages[0]
                    else:
                        # Use cache for static content
                        if dim_key not in watermark_cache:
                            logger.info(f"📐 Page {index + 1}: NEW dimension {dim_key[0]}x{dim_key[1]} ({orientation})")
                            watermark_packet = self.create_watermark_layer(page_width, page_height)
                            watermark_pdf = PdfReader(watermark_packet)
                            watermark_cache[dim_key] = watermark_pdf.pages[0]
                        else:
                            logger.info(f"♻️ Page {index + 1}: REUSING cached watermark")
                        
                        watermark_page = watermark_cache[dim_key]
                    
                    # ============================================
                    # UNDERLAY MODE: Watermark BEHIND content
                    # ============================================
                    if self.underlay:
                        # UNDERLAY: Merge watermark UNDER the page content
                        # This makes watermark appear BEHIND text/images
                        watermark_page.merge_page(page)
                        writer.add_page(watermark_page)
                        logger.debug(f"Page {index + 1}: UNDERLAY applied")
                    else:
                        # OVERLAY (default): Watermark ON TOP of content
                        page.merge_page(watermark_page)
                        writer.add_page(page)
                else:
                    writer.add_page(page)
            
            # Log summary
            logger.info(f"📊 Dimension Summary for {filename}:")
            for dim, count in dimension_stats.items():
                logger.info(f"   • {dim[0]}x{dim[1]}: {count} pages")
            
            if self.settings.get('add_metadata'):
                self._add_metadata(writer, filename)
            
            # Compression
            try:
                writer.remove_duplicates()
            except:
                pass
            
            writer.compress_identical_objects = True
            
            try:
                for page in writer.pages:
                    page.compress_content_streams()
            except Exception as e:
                logger.warning(f"Compression warning: {e}")
            
            with open(output_path, 'wb') as f:
                writer.write(f)
            
            original_size = os.path.getsize(input_path)
            new_size = os.path.getsize(output_path)
            size_change = ((new_size - original_size) / original_size) * 100 if original_size > 0 else 0
            
            logger.info(f"✅ Done: {filename} | Size: {original_size/1024:.1f}KB → {new_size/1024:.1f}KB ({size_change:+.1f}%)")
            
            gc.collect()
            return True, f"Processed {total_pages} pages"
            
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            return False, str(e)

    def _get_pages_to_watermark(self, total_pages: int) -> Set[int]:
        """Get set of page indices to watermark"""
        if self.page_range == 'all':
            return set(range(total_pages))
        elif self.page_range == 'first':
            return {0} if total_pages > 0 else set()
        elif self.page_range == 'last':
            return {total_pages - 1} if total_pages > 0 else set()
        else:
            pages = set()
            try:
                parts = str(self.page_range).split(',')
                for part in parts:
                    part = part.strip()
                    if '-' in part:
                        start, end = part.split('-')
                        start = int(start.strip()) - 1
                        end = int(end.strip())
                        pages.update(range(max(0, start), min(end, total_pages)))
                    else:
                        page = int(part) - 1
                        if 0 <= page < total_pages:
                            pages.add(page)
            except:
                pages = set(range(total_pages))
            return pages

    def _add_metadata(self, writer: PdfWriter, filename: str):
        """Add metadata to PDF"""
        author = self.settings.get('author') or 'Aryan Bot'
        location = self.settings.get('location') or 'India'
        writer.add_metadata({
            '/Title': filename,
            '/Author': author,
            '/Producer': 'localhost[Aryan]',
            '/Subject': f'Watermarked - {location}',
            '/Keywords': 'PDF,localhost',
            '/Creator': 'Created by Aryan @localhost'
        })


# ============================================
# WRAPPER FUNCTIONS
# ============================================
def add_watermark_to_pdf(input_path: str, output_path: str, 
                         settings: dict, filename: str = "document.pdf") -> bool:
    engine = WatermarkEngine(settings)
    success, message = engine.process_pdf(input_path, output_path, filename)
    if not success:
        logger.error(message)
    return success


def get_pdf_page_count(input_path: str) -> int:
    try:
        return len(PdfReader(input_path).pages)
    except:
        return 0


def validate_pdf_file(input_path: str) -> Tuple[bool, str]:
    try:
        return True, f"Valid PDF with {len(PdfReader(input_path).pages)} pages"
    except Exception as e:
        return False, f"Invalid PDF: {e}"


def clear_cache():
    global _dimension_cache, _settings_cache_key
    _dimension_cache.clear()
    _settings_cache_key = ""
    gc.collect()
    logger.info("🗑️ All caches cleared")
