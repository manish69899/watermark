# watermark.py - Advanced PDF Watermark Engine
# FIXED VERSION - Proper None handling, all features working

import io
import os
import logging
import math
from typing import Dict, Tuple, List
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter

# ============================================
# LOGGING SETUP
# ============================================
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WatermarkEngine")


# ============================================
# COLOR DEFINITIONS - 12 Colors
# ============================================
COLORS = {
    'grey': colors.Color(0.5, 0.5, 0.5),
    'red': colors.Color(0.9, 0.1, 0.1),
    'blue': colors.Color(0.1, 0.3, 0.9),
    'green': colors.Color(0.1, 0.6, 0.2),
    'purple': colors.Color(0.6, 0.1, 0.7),
    'orange': colors.Color(0.95, 0.5, 0.1),
    'yellow': colors.Color(0.9, 0.85, 0.1),
    'white': colors.Color(1, 1, 1),
    'black': colors.Color(0, 0, 0),
    'cyan': colors.Color(0, 0.8, 0.85),
    'pink': colors.Color(0.95, 0.4, 0.7),
    'brown': colors.Color(0.55, 0.3, 0.1),
    'gold': colors.Color(0.85, 0.65, 0.1),
    'silver': colors.Color(0.75, 0.75, 0.75),
}


def safe_int(value, default=0):
    """Safely convert to int, return default if None or invalid"""
    if value is None:
        return default
    try:
        return int(value)
    except (ValueError, TypeError):
        return default


def safe_float(value, default=0.0):
    """Safely convert to float, return default if None or invalid"""
    if value is None:
        return default
    try:
        return float(value)
    except (ValueError, TypeError):
        return default


class WatermarkEngine:
    """
    Advanced PDF Watermark Engine
    
    Features:
    - 8 Watermark Styles
    - 12 Border Styles
    - 12 Colors
    - 8 Opacity Levels
    - Multiple Links
    - Proper Filename Handling
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
        
        # Border settings - SAFE conversions
        self.border_style = self.settings.get('border_style') or 'simple'
        self.border_color_name = self.settings.get('border_color') or 'grey'
        self.border_width = safe_int(self.settings.get('border_width'), 2)
        
        # Links (multiple)
        self.links = self.settings.get('links') or []
        if not isinstance(self.links, list):
            self.links = []
        
        # Get color objects
        self.text_color = COLORS.get(self.color_name, COLORS['grey'])
        self.border_color = COLORS.get(self.border_color_name, COLORS['grey'])
        
        logger.info(f"Engine: style={self.style}, color={self.color_name}, opacity={self.opacity}, fontsize={self.fontsize}")

    def get_page_size(self, reader: PdfReader) -> Tuple[float, float]:
        """Get actual page size from PDF"""
        try:
            page = reader.pages[0]
            width = float(page.mediabox.width)
            height = float(page.mediabox.height)
            return width, height
        except:
            return 612.0, 792.0

    def create_watermark_layer(self, width: float, height: float) -> io.BytesIO:
        """Create watermark layer for one page"""
        packet = io.BytesIO()
        can = canvas.Canvas(packet, pagesize=(width, height))
        
        # Draw watermark based on style
        if self.style == 'diagonal':
            self._draw_diagonal(can, width, height)
        elif self.style == 'grid':
            self._draw_grid(can, width, height)
        elif self.style == 'topright':
            self._draw_corner(can, width, height, 'topright')
        elif self.style == 'bottomleft':
            self._draw_corner(can, width, height, 'bottomleft')
        elif self.style == 'overlay':
            self._draw_overlay(can, width, height)
        elif self.style == 'border':
            self._draw_border(can, width, height)
        elif self.style == 'header':
            self._draw_header(can, width, height)
        elif self.style == 'footer':
            self._draw_footer(can, width, height)
        else:
            # Default to diagonal
            self._draw_diagonal(can, width, height)
        
        # Draw all links
        for link in self.links:
            if isinstance(link, dict) and link.get('url'):
                self._draw_link_button(can, width, height, link)
        
        can.save()
        packet.seek(0)
        return packet

    # ============================================
    # STYLE: DIAGONAL
    # ============================================
    def _draw_diagonal(self, can: canvas.Canvas, w: float, h: float):
        """Diagonal center watermark"""
        can.saveState()
        can.translate(w / 2, h / 2)
        can.rotate(self.rotation)
        
        if self.content_type == 'text' and self.content:
            can.setFont('Helvetica-Bold', self.fontsize)
            can.setFillColor(self.text_color)
            can.setFillAlpha(self.opacity)
            can.drawCentredString(0, 0, self.content)
            
        elif self.content_type == 'image' and self.content and os.path.exists(self.content):
            can.setFillAlpha(self.opacity)
            size = self.imgsize
            can.drawImage(self.content, -size/2, -size/2, 
                         width=size, height=size, mask='auto', preserveAspectRatio=True)
        
        can.restoreState()

    # ============================================
    # STYLE: GRID
    # ============================================
    def _draw_grid(self, can: canvas.Canvas, w: float, h: float):
        """Grid/tiled watermark pattern"""
        can.saveState()
        can.translate(w / 2, h / 2)
        can.rotate(self.rotation)
        
        if self.content_type == 'text' and self.content:
            fontsize = max(12, self.fontsize // 2)
            gap = max(100, len(self.content) * 8)
        else:
            fontsize = 20
            gap = self.imgsize + 50
        
        extent = int(math.sqrt(w*w + h*h)) + 200
        
        for x in range(-extent, extent + 1, gap):
            for y in range(-extent, extent + 1, gap):
                if self.content_type == 'text' and self.content:
                    can.setFont('Helvetica-Bold', fontsize)
                    can.setFillColor(self.text_color)
                    can.setFillAlpha(self.opacity)
                    can.drawCentredString(x, y, self.content)
                elif self.content_type == 'image' and self.content and os.path.exists(self.content):
                    size = self.imgsize // 2
                    can.setFillAlpha(self.opacity)
                    can.drawImage(self.content, x - size/2, y - size/2,
                                 width=size, height=size, mask='auto')
        
        can.restoreState()

    # ============================================
    # STYLE: CORNER
    # ============================================
    def _draw_corner(self, can: canvas.Canvas, w: float, h: float, corner: str):
        """Corner placement watermark"""
        margin = 40
        fontsize = max(12, self.fontsize // 2)
        
        if corner == 'topright':
            x = w - margin
            y = h - margin - fontsize
        else:
            x = margin
            y = margin
        
        can.saveState()
        
        if self.content_type == 'text' and self.content:
            can.setFont('Helvetica-Bold', fontsize)
            can.setFillColor(self.text_color)
            can.setFillAlpha(self.opacity)
            
            if corner == 'topright':
                text_width = can.stringWidth(self.content, 'Helvetica-Bold', fontsize)
                can.drawString(x - text_width, y, self.content)
            else:
                can.drawString(x, y, self.content)
                
        elif self.content_type == 'image' and self.content and os.path.exists(self.content):
            size = self.imgsize // 2
            can.setFillAlpha(self.opacity)
            if corner == 'topright':
                can.drawImage(self.content, x - size, y - size, width=size, height=size, mask='auto')
            else:
                can.drawImage(self.content, x, y, width=size, height=size, mask='auto')
        
        can.restoreState()

    # ============================================
    # STYLE: OVERLAY
    # ============================================
    def _draw_overlay(self, can: canvas.Canvas, w: float, h: float):
        """Full page overlay watermark"""
        if self.content_type != 'text' or not self.content:
            return
        
        can.saveState()
        
        fontsize = self.fontsize
        gap = fontsize * 3
        
        for y_offset in range(int(h + w), int(-h - w), -gap):
            can.saveState()
            can.translate(0, y_offset)
            can.rotate(-45)
            
            can.setFont('Helvetica-Bold', fontsize)
            can.setFillColor(self.text_color)
            can.setFillAlpha(self.opacity * 0.5)
            
            text = self.content + "  •  "
            text_width = can.stringWidth(text, 'Helvetica-Bold', fontsize)
            x = -w
            while x < w * 2:
                can.drawString(x, 0, text)
                x += text_width
            
            can.restoreState()
        
        can.restoreState()

    # ============================================
    # STYLE: BORDER - 12 DIFFERENT STYLES
    # ============================================
    def _draw_border(self, can: canvas.Canvas, w: float, h: float):
        """Draw border - 12 different styles"""
        margin = 25
        inner_margin = margin + 8
        bwidth = max(1, self.border_width)
        
        can.saveState()
        can.setStrokeColor(self.border_color)
        can.setFillColor(self.border_color)
        can.setFillAlpha(self.opacity)
        
        # 1. SIMPLE
        if self.border_style == 'simple':
            can.setLineWidth(bwidth)
            can.rect(margin, margin, w - 2*margin, h - 2*margin, stroke=1, fill=0)
        
        # 2. DOUBLE
        elif self.border_style == 'double':
            can.setLineWidth(bwidth)
            can.rect(margin, margin, w - 2*margin, h - 2*margin, stroke=1, fill=0)
            can.setLineWidth(max(1, bwidth - 1))
            can.rect(inner_margin, inner_margin, w - 2*inner_margin, h - 2*inner_margin, stroke=1, fill=0)
        
        # 3. THICK
        elif self.border_style == 'thick':
            can.setLineWidth(bwidth + 4)
            can.rect(margin, margin, w - 2*margin, h - 2*margin, stroke=1, fill=0)
        
        # 4. DOTTED
        elif self.border_style == 'dotted':
            can.setLineWidth(bwidth)
            can.setDash(4, 4)
            can.rect(margin, margin, w - 2*margin, h - 2*margin, stroke=1, fill=0)
        
        # 5. STAR
        elif self.border_style == 'star':
            self._draw_corner_symbols(can, w, h, margin, '★')
            can.setLineWidth(bwidth)
            can.rect(margin + 20, margin + 20, w - 2*margin - 40, h - 2*margin - 40, stroke=1, fill=0)
        
        # 6. DIAMOND
        elif self.border_style == 'diamond':
            self._draw_corner_symbols(can, w, h, margin, '◆')
            can.setLineWidth(bwidth)
            can.rect(margin + 18, margin + 18, w - 2*margin - 36, h - 2*margin - 36, stroke=1, fill=0)
        
        # 7. CIRCLE
        elif self.border_style == 'circle':
            self._draw_corner_symbols(can, w, h, margin, '●')
            can.setLineWidth(bwidth)
            can.rect(margin + 15, margin + 15, w - 2*margin - 30, h - 2*margin - 30, stroke=1, fill=0)
        
        # 8. SQUARE
        elif self.border_style == 'square':
            self._draw_corner_symbols(can, w, h, margin, '■')
            can.setLineWidth(bwidth)
            can.rect(margin + 18, margin + 18, w - 2*margin - 36, h - 2*margin - 36, stroke=1, fill=0)
        
        # 9. GLITTER
        elif self.border_style == 'glitter':
            self._draw_corner_symbols(can, w, h, margin, '✦')
            can.setLineWidth(bwidth)
            can.setDash(2, 3)
            can.rect(margin, margin, w - 2*margin, h - 2*margin, stroke=1, fill=0)
        
        # 10. ELEGANT
        elif self.border_style == 'elegant':
            can.setLineWidth(1)
            can.rect(margin, margin, w - 2*margin, h - 2*margin, stroke=1, fill=0)
            corner_len = 25
            can.setLineWidth(2)
            # Corners
            can.line(margin, margin, margin + corner_len, margin)
            can.line(margin, margin, margin, margin + corner_len)
            can.line(margin, h - margin, margin + corner_len, h - margin)
            can.line(margin, h - margin, margin, h - margin - corner_len)
            can.line(w - margin, margin, w - margin - corner_len, margin)
            can.line(w - margin, margin, w - margin, margin + corner_len)
            can.line(w - margin, h - margin, w - margin - corner_len, h - margin)
            can.line(w - margin, h - margin, w - margin, h - margin - corner_len)
        
        # 11. FLOWER
        elif self.border_style == 'flower':
            self._draw_corner_symbols(can, w, h, margin, '✿')
            can.setLineWidth(bwidth)
            can.rect(margin + 20, margin + 20, w - 2*margin - 40, h - 2*margin - 40, stroke=1, fill=0)
        
        # 12. CORPORATE
        elif self.border_style == 'corporate':
            can.setLineWidth(bwidth + 3)
            can.rect(margin, margin, w - 2*margin, h - 2*margin, stroke=1, fill=0)
            can.setLineWidth(1)
            can.rect(margin + 6, margin + 6, w - 2*margin - 12, h - 2*margin - 12, stroke=1, fill=0)
        
        # Default to simple
        else:
            can.setLineWidth(bwidth)
            can.rect(margin, margin, w - 2*margin, h - 2*margin, stroke=1, fill=0)
        
        can.restoreState()
        
        # Draw text at bottom
        if self.content_type == 'text' and self.content:
            can.saveState()
            can.setFont('Helvetica-Bold', 12)
            can.setFillColor(self.text_color)
            can.setFillAlpha(self.opacity)
            text_width = can.stringWidth(self.content, 'Helvetica-Bold', 12)
            can.drawString((w - text_width) / 2, margin - 18, self.content)
            can.restoreState()

    def _draw_corner_symbols(self, can: canvas.Canvas, w: float, h: float, margin: float, symbol: str):
        """Draw decorative symbols at corners"""
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
    # STYLE: HEADER
    # ============================================
    def _draw_header(self, can: canvas.Canvas, w: float, h: float):
        """Header watermark at top"""
        if self.content_type != 'text' or not self.content:
            return
        
        can.saveState()
        
        can.setStrokeColor(self.text_color)
        can.setLineWidth(0.5)
        can.setFillAlpha(self.opacity)
        can.line(30, h - 35, w - 30, h - 35)
        
        fontsize = max(12, self.fontsize // 2)
        can.setFont('Helvetica-Bold', fontsize)
        can.setFillColor(self.text_color)
        text_width = can.stringWidth(self.content, 'Helvetica-Bold', fontsize)
        can.drawString((w - text_width) / 2, h - 28, self.content)
        
        can.restoreState()

    # ============================================
    # STYLE: FOOTER
    # ============================================
    def _draw_footer(self, can: canvas.Canvas, w: float, h: float):
        """Footer watermark at bottom"""
        if self.content_type != 'text' or not self.content:
            return
        
        can.saveState()
        
        can.setStrokeColor(self.text_color)
        can.setLineWidth(0.5)
        can.setFillAlpha(self.opacity)
        can.line(30, 30, w - 30, 30)
        
        fontsize = max(12, self.fontsize // 2)
        can.setFont('Helvetica-Bold', fontsize)
        can.setFillColor(self.text_color)
        text_width = can.stringWidth(self.content, 'Helvetica-Bold', fontsize)
        can.drawString((w - text_width) / 2, 12, self.content)
        
        can.restoreState()

    # ============================================
    # DRAW CLICKABLE LINK BUTTON
    # ============================================
    def _draw_link_button(self, can: canvas.Canvas, w: float, h: float, link: dict):
        """Draw a clickable link button"""
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
            can.setFillColor(colors.Color(0, 0, 0, alpha=0.15))
            can.roundRect(x1 + 1, y1 - 1, btn_w, btn_h, 5, stroke=0, fill=1)
            
            # Button
            can.setFillColor(colors.Color(0.97, 0.97, 1.0))
            can.setStrokeColor(colors.Color(0.2, 0.4, 0.85))
            can.setLineWidth(1)
            can.roundRect(x1, y1, btn_w, btn_h, 5, stroke=1, fill=1)
            
            # Text
            can.setFillColor(colors.Color(0.15, 0.3, 0.8))
            can.drawCentredString(x_pos, y_pos - 3, text)
            
            # Clickable
            can.linkURL(url, (x1, y1, x1 + btn_w, y1 + btn_h), relative=1)
            
            can.restoreState()
            
        except Exception as e:
            logger.error(f"Link error: {e}")

    # ============================================
    # PROCESS PDF
    # ============================================
    def process_pdf(self, input_path: str, output_path: str, filename: str = "document.pdf") -> Tuple[bool, str]:
        """Main PDF processing function"""
        try:
            # Validate input
            if not os.path.exists(input_path):
                return False, "Input file not found"
            
            # Read input PDF
            reader = PdfReader(input_path)
            total_pages = len(reader.pages)
            
            if total_pages == 0:
                return False, "PDF has no pages"
            
            # Get page size
            page_width, page_height = self.get_page_size(reader)
            logger.info(f"Processing: {filename}, Pages: {total_pages}")
            
            # Create watermark layer
            watermark_packet = self.create_watermark_layer(page_width, page_height)
            watermark_pdf = PdfReader(watermark_packet)
            watermark_page = watermark_pdf.pages[0]
            
            # Create output
            writer = PdfWriter()
            
            # Merge watermark on each page
            for page in reader.pages:
                page.merge_page(watermark_page)
                writer.add_page(page)
            
            # Add metadata
            if self.settings.get('add_metadata'):
                self._add_metadata(writer, filename)
            
            # Write output
            with open(output_path, 'wb') as f:
                writer.write(f)
            
            logger.info(f"Success: {filename}")
            return True, f"Processed {total_pages} pages"
            
        except Exception as e:
            error = f"Error: {str(e)}"
            logger.error(error)
            return False, error

    def _add_metadata(self, writer: PdfWriter, filename: str):
        """Add hidden metadata to PDF"""
        author = self.settings.get('author') or 'Aryan Bot'
        location = self.settings.get('location') or 'Your Heart'
        
        metadata = {
            '/Title': filename,
            '/Author': author,
            '/Producer': '𝖑𝖔𝖈𝖆𝖑𝖍𝖔𝖘𝖙[Aryan]',
            '/Subject': f'Watermarked - {location}',
            '/Keywords': 'PDF,𝖑𝖔𝖈𝖆𝖑𝖍𝖔𝖘𝖙',
            '/Creator': 'Created by Aryan and localhost ,contact me on Telegram @hilocalhost'
        }
        writer.add_metadata(metadata)


# ============================================
# WRAPPER FUNCTION
# ============================================
def add_watermark_to_pdf(input_path: str, output_path: str, settings: dict, filename: str = "document.pdf") -> bool:
    """Wrapper function"""
    engine = WatermarkEngine(settings)
    success, message = engine.process_pdf(input_path, output_path, filename)
    if not success:
        logger.error(message)
    return success


def get_pdf_page_count(input_path: str) -> int:
    """Get number of pages in PDF"""
    try:
        reader = PdfReader(input_path)
        return len(reader.pages)
    except:
        return 0


def validate_pdf_file(input_path: str) -> Tuple[bool, str]:
    """Validate if file is a valid PDF"""
    try:
        reader = PdfReader(input_path)
        pages = len(reader.pages)
        return True, f"Valid PDF with {pages} pages"
    except Exception as e:
        return False, f"Invalid PDF: {str(e)}"
