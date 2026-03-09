# watermark.py - PROFESSIONAL PDF Watermark Engine
# IMPROVED: File Size Fix, Better Rendering, Gap Control, Position, Tile Patterns
# ALL FEATURES PRESERVED + NEW: Outline, Advanced Borders, Compression Fix

import io
import os
import logging
import math
import hashlib
import copy
import gc
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
# GAP SETTINGS - NEW FEATURE
# ============================================
GAP_SIZES = {
    'small': 120,
    'medium': 200,
    'large': 300,
}

# ============================================
# LAYER CACHE - FIXED: Return COPY not same object
# ============================================
_layer_cache: Dict[str, bytes] = {}  # Store bytes, not BytesIO
MAX_CACHE_SIZE = 30

def _get_cache_key(width: float, height: float, settings: dict) -> str:
    """Generate unique cache key for watermark layer"""
    key_data = (
        f"{width:.0f}_{height:.0f}_"
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
        f"{settings.get('tile_pattern')}"
    )
    return hashlib.md5(key_data.encode()).hexdigest()


def safe_int(value, default=0) -> int:
    """Safely convert to int"""
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value, default=0.0) -> float:
    """Safely convert to float"""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


class WatermarkEngine:
    """
    PROFESSIONAL PDF Watermark Engine - ALL FEATURES + ENHANCED
    
    FEATURES:
    - 8 Watermark Styles
    - 20 Border Styles (Expanded)
    - 18 Colors
    - 8 Opacity Levels
    - Gap/Spacing Control (NEW)
    - Position Presets (NEW)
    - Tile Patterns (NEW)
    - Text Outline Effect (NEW)
    - Multiple Links
    - Custom Font Support
    - 3D Shadow Effect
    - Double Layer Watermark
    - Gradient Effect
    - Page Range Selection
    - Content Stream Compression (File Size Fix)
    """
    
    def __init__(self, settings: dict):
        """Initialize with user settings - SAFE conversion"""
        self.settings = settings if settings else {}
        
        # Basic settings - SAFE conversions
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
        
        # NEW: Gap/Spacing Control
        self.gap_setting = self.settings.get('gap', 'medium')
        if isinstance(self.gap_setting, (int, float)):
            self.gap = safe_int(self.gap_setting, 200)
        else:
            self.gap = GAP_SIZES.get(self.gap_setting, 200)
        
        # NEW: Position
        self.position = self.settings.get('position', 'center')
        
        # NEW: Tile Pattern
        self.tile_pattern = self.settings.get('tile_pattern', 'grid')
        
        # NEW: Text Outline
        self.outline = self.settings.get('outline', False)
        self.outline_width = safe_int(self.settings.get('outline_width'), 2)
        
        # Double Layer Feature
        self.double_layer = self.settings.get('double_layer', False)
        self.double_layer_offset = safe_int(self.settings.get('double_layer_offset'), 5)
        self.double_layer_color = self.settings.get('double_layer_color', 'black')
        
        # Gradient Effect
        self.gradient_effect = self.settings.get('gradient_effect', False)
        
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
        
        logger.info(
            f"Engine Init: style={self.style}, color={self.color_name}, "
            f"opacity={self.opacity}, shadow={self.shadow}, gap={self.gap}, "
            f"position={self.position}, outline={self.outline}"
        )

    def create_watermark_layer(self, width: float, height: float) -> io.BytesIO:
        """Create watermark layer - WITH FIXED CACHING"""
        
        # Check cache first
        cache_key = _get_cache_key(width, height, self.settings)
        if cache_key in _layer_cache:
            logger.info(f"📦 Using cached watermark layer")
            # FIXED: Return NEW BytesIO with copied data, not same object
            return io.BytesIO(_layer_cache[cache_key])
        
        # Create new layer
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
        
        style_method(can, width, height)
        
        # Double Layer Effect - Draw second layer
        if self.double_layer and self.content_type == 'text':
            self._draw_double_layer(can, width, height)
        
        # Draw all links
        for link in self.links:
            if isinstance(link, dict) and link.get('url'):
                self._draw_link_button(can, width, height, link)
        
        can.save()
        
        # FIXED: Store bytes in cache, not BytesIO object
        packet.seek(0)
        data = packet.read()
        
        if len(_layer_cache) < MAX_CACHE_SIZE:
            _layer_cache[cache_key] = data
        
        return io.BytesIO(data)

    # ============================================
    # TEXT DRAWING HELPER - PROFESSIONAL QUALITY
    # ============================================
    def _draw_text_with_shadow(self, can: canvas.Canvas, x: float, y: float, 
                                text: str, draw_func="drawString"):
        """Helper to draw text with professional 3D shadow and outline"""
        can.saveState()
        
        # NEW: Text Outline Effect
        if self.outline and self.content_type == 'text':
            can.setStrokeColor(colors.black)
            can.setLineWidth(self.outline_width)
            can.setFillColor(self.text_color)
            can.setFillAlpha(self.opacity)
            
            # Draw with stroke
            if draw_func == "drawCentredString":
                can.drawCentredString(x, y, text)
            else:
                can.drawString(x, y, text)
            
            can.restoreState()
            return
        
        # 3D Shadow Effect
        if self.shadow:
            shadow_opacity = self.opacity * 0.3
            offset_base = max(2, self.fontsize // 12)
            
            # Multi-layer professional shadow
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
            # Create gradient-like effect with multiple layers
            can.setFillColor(self.text_color)
            can.setFillAlpha(self.opacity * 0.6)
            
            if draw_func == "drawCentredString":
                can.drawCentredString(x, y, text)
            else:
                can.drawString(x, y, text)
            
            # Lighter top layer
            can.setFillAlpha(self.opacity)
            if draw_func == "drawCentredString":
                can.drawCentredString(x + 0.5, y + 0.5, text)
            else:
                can.drawString(x + 0.5, y + 0.5, text)
        else:
            # Normal text
            can.setFillColor(self.text_color)
            can.setFillAlpha(self.opacity)
            
            if draw_func == "drawCentredString":
                can.drawCentredString(x, y, text)
            else:
                can.drawString(x, y, text)
        
        can.restoreState()

    # ============================================
    # GET POSITION COORDINATES - NEW FEATURE
    # ============================================
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

    # ============================================
    # DOUBLE LAYER WATERMARK
    # ============================================
    def _draw_double_layer(self, can: canvas.Canvas, w: float, h: float):
        """Draw second watermark layer for double effect"""
        if self.content_type != 'text' or not self.content:
            return
        
        can.saveState()
        x, y = self._get_position_coords(w, h)
        can.translate(x, y)
        can.rotate(self.rotation + 90)
        
        second_color = COLORS.get(self.double_layer_color, COLORS['black'])
        can.setFillColor(second_color)
        can.setFillAlpha(self.opacity * 0.12)
        can.setFont(self.font_name, self.fontsize * 0.75)
        
        offset = self.double_layer_offset * 3
        can.drawCentredString(offset, offset, self.content)
        
        can.restoreState()

    # ============================================
    # STYLE: DIAGONAL - WITH POSITION SUPPORT
    # ============================================
    def _draw_diagonal(self, can: canvas.Canvas, w: float, h: float):
        can.saveState()
        x, y = self._get_position_coords(w, h)
        can.translate(x, y)
        can.rotate(self.rotation)
        
        if self.content_type == 'text' and self.content:
            can.setFont(self.font_name, self.fontsize)
            self._draw_text_with_shadow(can, 0, 0, self.content, "drawCentredString")
            
        elif self.content_type == 'image' and self.content and os.path.exists(self.content):
            can.setFillAlpha(self.opacity)
            size = self.imgsize
            try:
                can.drawImage(
                    self.content, -size/2, -size/2, 
                    width=size, height=size, 
                    mask='auto', preserveAspectRatio=True
                )
            except Exception as e:
                logger.error(f"Image error: {e}")
        can.restoreState()

    # ============================================
    # STYLE: GRID - WITH GAP CONTROL & TILE PATTERNS
    # ============================================
    def _draw_grid(self, can: canvas.Canvas, w: float, h: float):
        """Grid/tile pattern with gap control"""
        
        # Choose tile pattern
        if self.tile_pattern == 'honeycomb':
            self._draw_honeycomb(can, w, h)
            return
        elif self.tile_pattern == 'wave':
            self._draw_wave_pattern(can, w, h)
            return
        elif self.tile_pattern == 'spiral':
            self._draw_spiral_pattern(can, w, h)
            return
        
        # Standard grid with gap control
        can.saveState()
        can.translate(w / 2, h / 2)
        can.rotate(self.rotation)
        
        if self.content_type == 'text' and self.content:
            fontsize = max(14, self.fontsize // 2)
            can.setFont(self.font_name, fontsize)
        else:
            fontsize = 18
        
        # Use gap setting - this is the key feature!
        gap = self.gap
        
        # Calculate extent based on gap
        extent = int(math.sqrt(w*w + h*h) / 2) + gap
        
        # Draw grid with controlled spacing
        for x in range(-extent, extent + 1, gap):
            for y in range(-extent, extent + 1, gap):
                if self.content_type == 'text' and self.content:
                    self._draw_text_with_shadow(can, x, y, self.content, "drawCentredString")
                elif self.content_type == 'image' and self.content and os.path.exists(self.content):
                    size = self.imgsize // 2
                    can.setFillAlpha(self.opacity)
                    try:
                        can.drawImage(
                            self.content, x - size/2, y - size/2,
                            width=size, height=size, mask='auto'
                        )
                    except:
                        pass
        can.restoreState()

    # ============================================
    # NEW: HONEYCOMB PATTERN
    # ============================================
    def _draw_honeycomb(self, can: canvas.Canvas, w: float, h: float):
        """Honeycomb/hexagonal tile pattern"""
        can.saveState()
        fontsize = max(14, self.fontsize // 2)
        can.setFont(self.font_name, fontsize)
        
        gap = self.gap
        row = 0
        y = h + gap
        
        while y > -gap:
            x_offset = (row % 2) * (gap / 2)
            x = x_offset
            
            while x < w + gap:
                # Apply rotation at each position
                can.saveState()
                can.translate(x, y)
                can.rotate(self.rotation)
                
                if self.content_type == 'text' and self.content:
                    self._draw_text_with_shadow(can, 0, 0, self.content, "drawCentredString")
                
                can.restoreState()
                x += gap
            
            y -= gap * 0.866
            row += 1
        
        can.restoreState()

    # ============================================
    # NEW: WAVE PATTERN
    # ============================================
    def _draw_wave_pattern(self, can: canvas.Canvas, w: float, h: float):
        """Wave-like tile pattern"""
        import math
        can.saveState()
        fontsize = max(14, self.fontsize // 2)
        can.setFont(self.font_name, fontsize)
        
        gap = self.gap
        amplitude = gap * 0.3
        
        y = gap
        wave_idx = 0
        
        while y < h + gap:
            x = gap
            while x < w + gap:
                # Wave offset
                wave_offset = math.sin(x * 0.02 + wave_idx) * amplitude
                
                can.saveState()
                can.translate(x, y + wave_offset)
                can.rotate(self.rotation)
                
                if self.content_type == 'text' and self.content:
                    self._draw_text_with_shadow(can, 0, 0, self.content, "drawCentredString")
                
                can.restoreState()
                x += gap
            
            y += gap
            wave_idx += 0.5
        
        can.restoreState()

    # ============================================
    # NEW: SPIRAL PATTERN
    # ============================================
    def _draw_spiral_pattern(self, can: canvas.Canvas, w: float, h: float):
        """Spiral watermark from center"""
        import math
        can.saveState()
        can.translate(w/2, h/2)
        
        fontsize = max(12, self.fontsize // 2)
        can.setFont(self.font_name, fontsize)
        
        theta = 0
        radius = 30
        
        while radius < min(w, h) / 2:
            x = radius * math.cos(theta)
            y = radius * math.sin(theta)
            
            # Fade out towards edges
            fade = 1 - (radius / (min(w, h) / 2)) * 0.5
            
            can.saveState()
            can.setFillColor(self.text_color)
            can.setFillAlpha(self.opacity * fade)
            can.drawCentredString(x, y, self.content)
            can.restoreState()
            
            theta += 0.4
            radius += max(2, self.gap // 20)
        
        can.restoreState()

    # ============================================
    # STYLE: CORNER
    # ============================================
    def _draw_corner(self, can: canvas.Canvas, w: float, h: float, corner: str):
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
            if corner == 'topright':
                text_width = can.stringWidth(self.content, self.font_name, fontsize)
                self._draw_text_with_shadow(can, x - text_width, y, self.content, "drawString")
            else:
                self._draw_text_with_shadow(can, x, y, self.content, "drawString")
                
        elif self.content_type == 'image' and self.content and os.path.exists(self.content):
            size = self.imgsize // 2
            can.setFillAlpha(self.opacity)
            if corner == 'topright':
                can.drawImage(self.content, x - size, y - size, width=size, height=size, mask='auto')
            else:
                can.drawImage(self.content, x, y, width=size, height=size, mask='auto')
        
        can.restoreState()

    # ============================================
    # STYLE: OVERLAY - OPTIMIZED
    # ============================================
    def _draw_overlay(self, can: canvas.Canvas, w: float, h: float):
        if self.content_type != 'text' or not self.content:
            return
        
        can.saveState()
        fontsize = self.fontsize
        gap = max(fontsize * 4, self.gap)
        
        for y_offset in range(int(h + w), int(-h - w), -gap):
            can.saveState()
            can.translate(0, y_offset)
            can.rotate(-45)
            
            can.setFont(self.font_name, fontsize)
            text = self.content + "  •  "
            text_width = can.stringWidth(text, self.font_name, fontsize)
            
            x = -w
            while x < w * 2:
                self._draw_text_with_shadow(can, x, 0, text, "drawString")
                x += text_width * 1.2
            can.restoreState()
        
        can.restoreState()

    # ============================================
    # STYLE: BORDER - ALL 20 STYLES
    # ============================================
    def _draw_border(self, can: canvas.Canvas, w: float, h: float):
        margin = 25
        inner_margin = margin + 8
        bwidth = max(1, self.border_width)
        
        can.saveState()
        can.setStrokeColor(self.border_color)
        can.setFillColor(self.border_color)
        can.setFillAlpha(self.opacity)
        
        # All 20 border styles
        border_methods = {
            # Original 12 styles
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
            # NEW: 8 advanced styles
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
        
        # Draw text at bottom
        if self.content_type == 'text' and self.content:
            can.saveState()
            can.setFont(self.font_name, 12)
            text_width = can.stringWidth(self.content, self.font_name, 12)
            self._draw_text_with_shadow(can, (w - text_width) / 2, margin - 18, self.content, "drawString")
            can.restoreState()

    # ============================================
    # BORDER DRAWING METHODS - ORIGINAL 12
    # ============================================
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
        can.setDash([4, 4], 0)  # FIXED FOR REPORTLAB 4.X
        can.rect(margin, margin, w - 2*margin, h - 2*margin, stroke=1, fill=0)

    def _draw_symbol_border(self, can, w, h, margin, bwidth, symbol):
        self._draw_corner_symbols(can, w, h, margin, symbol)
        can.setLineWidth(bwidth)
        can.rect(margin + 20, margin + 20, w - 2*margin - 40, h - 2*margin - 40, stroke=1, fill=0)

    def _draw_glitter_border(self, can, w, h, margin, bwidth):
        self._draw_corner_symbols(can, w, h, margin, '✦')
        can.setLineWidth(bwidth)
        can.setDash([2, 3], 0)  # FIXED FOR REPORTLAB 4.X
        can.rect(margin, margin, w - 2*margin, h - 2*margin, stroke=1, fill=0)

    def _draw_elegant_border(self, can, w, h, margin, bwidth):
        can.setLineWidth(1)
        can.rect(margin, margin, w - 2*margin, h - 2*margin, stroke=1, fill=0)
        corner_len = 25
        can.setLineWidth(2)
        corners = [
            (margin, margin, 1, 1),
            (margin, h - margin, 1, -1),
            (w - margin, margin, -1, 1),
            (w - margin, h - margin, -1, -1)
        ]
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
        positions = [
            (margin - 8, margin - 8),
            (margin - 8, h - margin - 8),
            (w - margin - 12, margin - 8),
            (w - margin - 12, h - margin - 8)
        ]
        for x, y in positions:
            can.drawString(x, y, symbol)

    # ============================================
    # NEW: ADVANCED BORDER STYLES (8 NEW)
    # ============================================
    def _draw_wave_border(self, can, w, h, margin, bwidth):
        """Wave-like border pattern"""
        import math
        can.setLineWidth(bwidth)
        
        # Draw wavy lines on all sides
        points = 60
        
        # Top wave
        p = can.beginPath()
        p.moveTo(margin, h - margin)
        for i in range(points + 1):
            x = margin + (w - 2*margin) * i / points
            y = h - margin + math.sin(i * 0.4) * 5
            p.lineTo(x, y)
        can.drawPath(p, stroke=1, fill=0)
        
        # Bottom wave
        p = can.beginPath()
        p.moveTo(margin, margin)
        for i in range(points + 1):
            x = margin + (w - 2*margin) * i / points
            y = margin + math.sin(i * 0.4) * 5
            p.lineTo(x, y)
        can.drawPath(p, stroke=1, fill=0)
        
        # Left and right lines
        can.line(margin, margin, margin, h - margin)
        can.line(w - margin, margin, w - margin, h - margin)

    def _draw_gradient_border(self, can, w, h, margin, bwidth):
        """Multiple overlapping borders for gradient effect"""
        for i in range(5):
            offset = i * 3
            can.setStrokeColor(self.border_color)
            can.setFillAlpha(self.opacity * (1 - i * 0.15))
            can.setLineWidth(bwidth + i * 2)
            can.rect(margin + offset, margin + offset, 
                     w - 2*margin - 2*offset, h - 2*margin - 2*offset, 
                     stroke=1, fill=0)

    def _draw_stamp_border(self, can, w, h, margin, bwidth):
        """Postage stamp style border with perforations"""
        can.setLineWidth(bwidth)
        can.rect(margin + 10, margin + 10, w - 2*margin - 20, h - 2*margin - 20, stroke=1, fill=0)
        
        # Draw perforated edges
        for i in range(int((w - 2*margin) / 12)):
            x = margin + 12 + i * 12
            # Top
            can.circle(x, h - margin, 3, stroke=1, fill=0)
            # Bottom
            can.circle(x, margin, 3, stroke=1, fill=0)
        
        for i in range(int((h - 2*margin) / 12)):
            y = margin + 12 + i * 12
            # Left
            can.circle(margin, y, 3, stroke=1, fill=0)
            # Right
            can.circle(w - margin, y, 3, stroke=1, fill=0)

    def _draw_artdeco_border(self, can, w, h, margin, bwidth):
        """Art Deco geometric pattern border"""
        can.setLineWidth(bwidth)
        can.rect(margin, margin, w - 2*margin, h - 2*margin, stroke=1, fill=0)
        
        # Corner decorations
        corner_size = 25
        corners = [
            (margin, margin, 1, 1),
            (margin, h - margin, 1, -1),
            (w - margin, margin, -1, 1),
            (w - margin, h - margin, -1, -1)
        ]
        
        for x, y, dx, dy in corners:
            # Geometric pattern
            can.setLineWidth(1)
            can.line(x, y, x + corner_size * dx, y)
            can.line(x, y, x, y + corner_size * dy)
            can.line(x + corner_size * dx * 0.5, y, x + corner_size * dx * 0.5, y + corner_size * dy * 0.5)
            can.line(x, y + corner_size * dy * 0.5, x + corner_size * dx * 0.5, y + corner_size * dy * 0.5)

    def _draw_neon_border(self, can, w, h, margin, bwidth):
        """Neon glow effect border"""
        for i in range(8, 0, -1):
            can.setStrokeColor(self.border_color)
            can.setFillAlpha(self.opacity * (i / 16))
            can.setLineWidth(bwidth + i * 2)
            can.rect(margin, margin, w - 2*margin, h - 2*margin, stroke=1, fill=0)

    def _draw_ornament_border(self, can, w, h, margin, bwidth):
        """Corner ornament border"""
        can.setLineWidth(bwidth)
        can.rect(margin + 20, margin + 20, w - 2*margin - 40, h - 2*margin - 40, stroke=1, fill=0)
        
        # Corner ornaments
        ornaments = ['❖', '◆', '✧', '✦']
        can.setFont('Helvetica', 18)
        
        positions = [
            (margin + 5, h - margin - 12),
            (w - margin - 18, h - margin - 12),
            (margin + 5, margin + 2),
            (w - margin - 18, margin + 2)
        ]
        
        for (x, y), ornament in zip(positions, ornaments):
            can.drawString(x, y, ornament)

    def _draw_dashdot_border(self, can, w, h, margin, bwidth):
        """Dash-dot pattern border"""
        can.setLineWidth(bwidth)
        can.setDash([10, 3, 2, 3], 0)  # FIXED FOR REPORTLAB 4.X
        can.rect(margin, margin, w - 2*margin, h - 2*margin, stroke=1, fill=0)

    def _draw_certificate_border(self, can, w, h, margin, bwidth):
        """Certificate style triple line border"""
        for offset in [0, 5, 10]:
            can.setLineWidth(bwidth - offset // 4)
            can.rect(margin + offset, margin + offset, 
                     w - 2*margin - 2*offset, h - 2*margin - 2*offset, stroke=1, fill=0)
        
        # Corner flourishes
        can.setFont('Helvetica', 20)
        can.drawString(margin - 3, h - margin - 10, '❮')
        can.drawString(w - margin - 12, h - margin - 10, '❯')
        can.drawString(margin - 3, margin - 2, '❮')
        can.drawString(w - margin - 12, margin - 2, '❯')

    # ============================================
    # STYLE: HEADER & FOOTER
    # ============================================
    def _draw_header(self, can: canvas.Canvas, w: float, h: float):
        if self.content_type != 'text' or not self.content:
            return
        can.saveState()
        can.setStrokeColor(self.text_color)
        can.setLineWidth(0.5)
        can.setFillAlpha(self.opacity)
        can.line(30, h - 35, w - 30, h - 35)
        
        fontsize = max(12, self.fontsize // 2)
        can.setFont(self.font_name, fontsize)
        text_width = can.stringWidth(self.content, self.font_name, fontsize)
        self._draw_text_with_shadow(can, (w - text_width) / 2, h - 28, self.content, "drawString")
        can.restoreState()

    def _draw_footer(self, can: canvas.Canvas, w: float, h: float):
        if self.content_type != 'text' or not self.content:
            return
        can.saveState()
        can.setStrokeColor(self.text_color)
        can.setLineWidth(0.5)
        can.setFillAlpha(self.opacity)
        can.line(30, 30, w - 30, 30)
        
        fontsize = max(12, self.fontsize // 2)
        can.setFont(self.font_name, fontsize)
        text_width = can.stringWidth(self.content, self.font_name, fontsize)
        self._draw_text_with_shadow(can, (w - text_width) / 2, 12, self.content, "drawString")
        can.restoreState()

    # ============================================
    # DRAW CLICKABLE LINK BUTTON
    # ============================================
    def _draw_link_button(self, can: canvas.Canvas, w: float, h: float, link: dict):
        try:
            url = link.get('url', '')
            position = link.get('position', 'bottomcenter')
            text = link.get('text', '🔗 CLICK HERE')
            if not url:
                return
            
            # Position
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
            
            # Shadow
            can.setFillColor(colors.Color(0, 0, 0, alpha=0.12))
            can.roundRect(x1 + 1.5, y1 - 1.5, btn_w, btn_h, 5, stroke=0, fill=1)
            
            # Button background
            can.setFillColor(colors.Color(0.98, 0.98, 1.0))
            can.setStrokeColor(colors.Color(0.2, 0.4, 0.85))
            can.setLineWidth(1)
            can.roundRect(x1, y1, btn_w, btn_h, 5, stroke=1, fill=1)
            
            # Button text
            can.setFillColor(colors.Color(0.15, 0.3, 0.8))
            can.drawCentredString(x_pos, y_pos - 3, text)
            
            # Link area
            can.linkURL(url, (x1, y1, x1 + btn_w, y1 + btn_h), relative=1)
            can.restoreState()
        except Exception as e:
            logger.error(f"Link error: {e}")

    # ============================================
    # PROCESS PDF - WITH COMPRESSION (FILE SIZE FIX)
    # ============================================
    def process_pdf(self, input_path: str, output_path: str, 
                    filename: str = "document.pdf",
                    progress_callback=None) -> Tuple[bool, str]:
        """Process PDF with COMPRESSION for minimum file size"""
        try:
            if not os.path.exists(input_path):
                return False, "Input file not found"
            
            reader = PdfReader(input_path)
            total_pages = len(reader.pages)
            if total_pages == 0:
                return False, "PDF has no pages"
            
            logger.info(f"📄 Processing: {filename} | Pages: {total_pages}")
            
            writer = PdfWriter()
            
            # Determine pages to watermark
            pages_to_watermark = self._get_pages_to_watermark(total_pages)
            
            # Get dimensions from first page for watermark layer
            if pages_to_watermark:
                first_page = reader.pages[0]
                try:
                    page_width = float(first_page.mediabox.width)
                    page_height = float(first_page.mediabox.height)
                except:
                    page_width, page_height = 612.0, 792.0
                
                # Create watermark once
                watermark_packet = self.create_watermark_layer(page_width, page_height)
                watermark_pdf = PdfReader(watermark_packet)
                watermark_page = watermark_pdf.pages[0]
            
            for index, page in enumerate(reader.pages):
                # Progress callback
                if progress_callback and index % 10 == 0:
                    try:
                        progress_callback(index + 1, total_pages)
                    except:
                        pass
                
                if index in pages_to_watermark:
                    # Merge watermark
                    page.merge_page(watermark_page)
                
                writer.add_page(page)
            
            # Add metadata if requested
            if self.settings.get('add_metadata'):
                self._add_metadata(writer, filename)
            
            # ============================================
            # CRITICAL FIX: COMPRESSION FOR FILE SIZE
            # ============================================
            # Remove duplicate objects
            try:
                writer.remove_duplicates()
            except:
                pass
            
            # Enable content stream compression
            writer.compress_identical_objects = True
            
            # CRITICAL: Compress all content streams
            try:
                for page in writer.pages:
                    page.compress_content_streams()
            except Exception as e:
                logger.warning(f"Content stream compression warning: {e}")
            
            # Write with compression
            with open(output_path, 'wb') as f:
                writer.write(f)
            
            # Log results
            original_size = os.path.getsize(input_path)
            new_size = os.path.getsize(output_path)
            size_change = ((new_size - original_size) / original_size) * 100 if original_size > 0 else 0
            
            logger.info(
                f"✅ Done: {filename} | "
                f"Size: {original_size/1024:.1f}KB → {new_size/1024:.1f}KB ({size_change:+.1f}%)"
            )
            
            # Force garbage collection
            gc.collect()
            
            return True, f"Processed {total_pages} pages"
            
        except Exception as e:
            error = f"Error: {str(e)}"
            logger.error(error)
            return False, error

    # ============================================
    # CUSTOM PAGE RANGE PARSER - FIXED
    # ============================================
    def _get_pages_to_watermark(self, total_pages: int) -> Set[int]:
        """Get set of page indices to watermark with custom range support"""
        if self.page_range == 'all':
            return set(range(total_pages))
        elif self.page_range == 'first':
            return {0} if total_pages > 0 else set()
        elif self.page_range == 'last':
            return {total_pages - 1} if total_pages > 0 else set()
        else:
            # Parse custom page range like "1-5, 8, 10-12"
            pages = set()
            try:
                parts = str(self.page_range).split(',')
                for part in parts:
                    part = part.strip()
                    if '-' in part:
                        start, end = part.split('-')
                        start = int(start.strip()) - 1  # Convert to 0-indexed
                        end = int(end.strip())  # Keep end as is (inclusive)
                        pages.update(range(max(0, start), min(end, total_pages)))
                    else:
                        page = int(part) - 1  # Convert to 0-indexed
                        if 0 <= page < total_pages:
                            pages.add(page)
            except Exception as e:
                logger.warning(f"Invalid page range: {self.page_range}, using all. Error: {e}")
                pages = set(range(total_pages))
            
            return pages

    def _add_metadata(self, writer: PdfWriter, filename: str):
        """Add metadata to PDF"""
        author = self.settings.get('author') or 'Aryan Bot'
        location = self.settings.get('location') or 'Your Heart'
        metadata = {
            '/Title': filename,
            '/Author': author,
            '/Producer': '𝖑𝖔𝖈𝖆𝖑𝖍𝖔𝖘𝖙[Aryan]',
            '/Subject': f'Watermarked - {location}',
            '/Keywords': 'PDF,𝖑𝖔𝖈𝖆𝖑𝖍𝖔𝖘𝖙',
            '/Creator': 'Created by Aryan and localhost, Telegram @hilocalhost'
        }
        writer.add_metadata(metadata)


# ============================================
# WRAPPER FUNCTIONS
# ============================================
def add_watermark_to_pdf(input_path: str, output_path: str, 
                         settings: dict, filename: str = "document.pdf") -> bool:
    """Wrapper function to add watermark"""
    engine = WatermarkEngine(settings)
    success, message = engine.process_pdf(input_path, output_path, filename)
    if not success:
        logger.error(message)
    return success


def get_pdf_page_count(input_path: str) -> int:
    """Get PDF page count"""
    try:
        reader = PdfReader(input_path)
        return len(reader.pages)
    except:
        return 0


def validate_pdf_file(input_path: str) -> Tuple[bool, str]:
    """Validate PDF file"""
    try:
        reader = PdfReader(input_path)
        return True, f"Valid PDF with {len(reader.pages)} pages"
    except Exception as e:
        return False, f"Invalid PDF: {str(e)}"


def clear_cache():
    """Clear watermark layer cache"""
    global _layer_cache
    _layer_cache.clear()
    gc.collect()
    logger.info("🗑️ Layer cache cleared")