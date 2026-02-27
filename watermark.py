import io
import os
import logging
from typing import Dict, Optional, Tuple, Union
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader

# --- LOGGING SETUP (Professional Monitoring) ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("WatermarkEngine")

class WatermarkEngine:
    """
    Advanced PDF Watermarking Engine.
    Features: Text/Image support, Grid/Diagonal styles, Metadata, and Link Injection.
    """
    
    def __init__(self, settings: Dict):
        self.settings = settings
        self.opacity = float(settings.get('opacity', 0.3))
        self.content_type = settings.get('type', 'text')
        self.style = settings.get('style', 'diagonal')
        self.content = settings.get('content', '')
        self.url = settings.get('url')
        
        # Color Mapping Strategy
        self.colors_map = {
            'red': colors.red,
            'grey': colors.Color(0.5, 0.5, 0.5, alpha=1),
            'blue': colors.blue,
            'green': colors.green,
            'black': colors.black,
            'white': colors.white
        }
        self.primary_color = self.colors_map.get(settings.get('color', 'grey'), colors.grey)

    def _setup_canvas(self, packet: io.BytesIO) -> canvas.Canvas:
        """Canvas initialize karta hai standard A4/Letter support ke saath."""
        return canvas.Canvas(packet, pagesize=letter)

    def _draw_text_with_stroke(self, can: canvas.Canvas, text: str, x: float, y: float, size: int):
        """
        ADVANCED: Text ko Stroke (Outline) ke saath draw karta hai.
        Isse text dark background par bhi visible rehta hai.
        """
        can.saveState()
        
        # Step 1: Stroke aur Fill Color setup karo
        can.setLineWidth(1)
        can.setStrokeColor(colors.white) # White Border
        can.setFillColor(self.primary_color)
        can.setFillAlpha(self.opacity)
        
        # Step 2: Text ko properly center karne ke liye width calculate karo
        text_width = can.stringWidth(text, "Helvetica-Bold", size)
        start_x = x - (text_width / 2)
        
        # Step 3: TextObject ka use karke Render Mode apply karo
        text_obj = can.beginText()
        text_obj.setTextOrigin(start_x, y)
        text_obj.setFont("Helvetica-Bold", size)
        text_obj.setTextRenderMode(2) # 2 = Fill + Stroke
        text_obj.textOut(text)
        
        # Step 4: Canvas pe draw karo
        can.drawText(text_obj)
        
        can.restoreState()

    def _generate_layer(self) -> io.BytesIO:
        """Main Watermark Layer generate karne wala logic."""
        packet = io.BytesIO()
        can = self._setup_canvas(packet)
        width, height = letter # 612 x 792 points

        # 1. APPLY STYLE (Diagonal vs Grid)
        can.saveState()
        
        if self.style == 'diagonal':
            self._render_diagonal(can, width, height)
        elif self.style == 'grid':
            self._render_grid(can)
            
        can.restoreState()

        # 2. INJECT SMART LINK (Button Style)
        if self.url:
            self._render_link_button(can, width, height)

        can.save()
        packet.seek(0)
        return packet

    def _render_diagonal(self, can: canvas.Canvas, w: float, h: float):
        """Single Diagonal Watermark logic."""
        can.translate(w / 2, h / 2)
        can.rotate(45)

        if self.content_type == 'text':
            # Responsive Font Size
            font_size = 50 if len(self.content) < 15 else 36
            self._draw_text_with_stroke(can, self.content, 0, 0, font_size)
            
        elif self.content_type == 'image' and os.path.exists(self.content):
            img_size = 180
            can.setFillAlpha(self.opacity)
            can.drawImage(self.content, -img_size/2, -img_size/2, 
                         width=img_size, height=img_size, mask='auto', preserveAspectRatio=True)

    def _render_grid(self, can: canvas.Canvas):
        """Dense Grid Tiling Logic."""
        can.rotate(45)
        
        # Configuration for Grid
        if self.content_type == 'text':
            gap = 160
            font_size = 20
        else:
            gap = 180
            img_size = 60

        # Extended Range for Full Coverage
        for x in range(-1000, 2000, gap):
            for y in range(-1000, 2000, gap):
                if self.content_type == 'text':
                    # Grid me stroke heavy ho sakta hai, isliye simple text rakha hai opacity ke saath
                    can.setFont("Helvetica-Bold", font_size)
                    can.setFillColor(self.primary_color)
                    can.setFillAlpha(self.opacity)
                    can.drawCentredString(x, y, self.content)
                
                elif self.content_type == 'image' and os.path.exists(self.content):
                    can.setFillAlpha(self.opacity)
                    can.drawImage(self.content, x, y, width=img_size, height=img_size, mask='auto')

    def _render_link_button(self, can: canvas.Canvas, w: float, h: float):
        """
        PROFESSIONAL LINK: Ek Rounded Button banata hai jo clickable hota hai.
        """
        try:
            can.saveState()
            
            # Settings
            btn_text = "🔗 CLICK HERE TO JOIN"
            pos = self.settings.get('position', 'bottom')
            
            # Coordinates Calculation
            center_x = w / 2
            center_y = h - 15 if pos == 'top' else 40
            
            # Font Settings
            can.setFont("Helvetica-Bold", 12)
            text_width = can.stringWidth(btn_text, "Helvetica-Bold", 12)
            padding_x = 15
            padding_y = 8
            
            # Button Dimensions
            btn_w = text_width + (padding_x * 2)
            btn_h = 20 + padding_y
            x1 = center_x - (btn_w / 2)
            y1 = center_y - (btn_h / 2) + 5
            
            # 1. Draw Button Shadow (3D Effect)
            can.setFillColor(colors.Color(0, 0, 0, alpha=0.2))
            can.roundRect(x1 + 2, y1 - 2, btn_w, btn_h, 8, stroke=0, fill=1)
            
            # 2. Draw Button Body (White Background)
            can.setFillColor(colors.white)
            can.setStrokeColor(colors.blue)
            can.setLineWidth(1)
            can.roundRect(x1, y1, btn_w, btn_h, 8, stroke=1, fill=1)
            
            # 3. Draw Text (Blue)
            can.setFillColor(colors.blue)
            can.drawCentredString(center_x, center_y, btn_text)
            
            # 4. Create Clickable Link (Invisible Hotspot)
            link_rect = (x1, y1, x1 + btn_w, y1 + btn_h)
            can.linkURL(self.url, link_rect, relative=1)
            
            can.restoreState()
            logger.info(f"Link added at {pos}: {self.url}")
            
        except Exception as e:
            logger.error(f"Failed to render link: {e}")

    def process_pdf(self, input_path: str, output_path: str, filename: str = "Doc") -> bool:
        """
        Asli PDF processing pipeline.
        Metadata aur Encryption bhi handle karta hai.
        """
        try:
            # Step 1: Generate Watermark Layer
            layer_packet = self._generate_layer()
            watermark_pdf = PdfReader(layer_packet)
            watermark_page = watermark_pdf.pages[0]

            # Step 2: Read Input PDF
            reader = PdfReader(input_path)
            writer = PdfWriter()

            # Step 3: Merge Layers
            total_pages = len(reader.pages)
            logger.info(f"Processing {total_pages} pages for {filename}")
            
            for i, page in enumerate(reader.pages):
                page.merge_page(watermark_page)
                # Optional: Compress content streams for smaller file size
                # page.compress_content_streams() 
                writer.add_page(page)

            # Step 4: Add Metadata (Branding)
            if self.settings.get('add_metadata'):
                self._add_metadata(writer, filename)

            # Step 5: Save File
            with open(output_path, "wb") as f:
                writer.write(f)
            
            logger.info("PDF Processed Successfully.")
            return True

        except Exception as e:
            logger.critical(f"Critical Error in PDF Processing: {e}")
            return False

    def _add_metadata(self, writer: PdfWriter, filename: str):
        """Hidden Metadata inject karta hai."""
        author = self.settings.get('author', 'Bot User')
        location = self.settings.get('location', 'India')
        link = self.settings.get('url', 'N/A')
        
        metadata = {
            '/Title': filename,
            '/Author': author,
            '/Producer': f"Generated by Advanced Watermark Bot",
            '/Subject': f"Official Document - {link}",
            '/Keywords': f"{location}, Security, PDF, Watermark",
            '/Creator': "Python Automation Tool"
        }
        writer.add_metadata(metadata)


# --- WRAPPER FUNCTION (Main.py compatibility) ---
def add_watermark_to_pdf(input_path, output_path, settings, filename="Document"):
    """
    Wrapper function taaki purana main.py code bina change kiye chale.
    """
    engine = WatermarkEngine(settings)
    return engine.process_pdf(input_path, output_path, filename)