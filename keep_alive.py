# keep_alive.py - Keep Bot Alive on Hosting Platforms
# Works with Replit, Render, and similar platforms

import threading
import http.server
import socketserver
import logging
import os

logger = logging.getLogger("KeepAlive")

# ============================================
# SIMPLE HTTP SERVER
# ============================================
class KeepAliveHandler(http.server.BaseHTTPRequestHandler):
    """Simple HTTP handler for health checks"""
    
    def do_GET(self):
        """Handle GET requests"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Watermark Bot - Online</title>
            <style>
                body {
                    font-family: 'Segoe UI', Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    height: 100vh;
                    margin: 0;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    color: white;
                }
                .container {
                    text-align: center;
                    padding: 40px;
                    background: rgba(255,255,255,0.1);
                    border-radius: 20px;
                    backdrop-filter: blur(10px);
                }
                h1 { font-size: 2.5em; margin-bottom: 10px; }
                p { font-size: 1.2em; opacity: 0.9; }
                .status {
                    display: inline-block;
                    width: 15px;
                    height: 15px;
                    background: #4ade80;
                    border-radius: 50%;
                    margin-right: 10px;
                    animation: pulse 2s infinite;
                }
                @keyframes pulse {
                    0%, 100% { opacity: 1; }
                    50% { opacity: 0.5; }
                }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🤖 Watermark Bot</h1>
                <p><span class="status"></span> Bot is running successfully!</p>
                <p>Telegram PDF Watermark Service</p>
            </div>
        </body>
        </html>
        """
        self.wfile.write(html_content.encode())
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass


def run_server(port: int = 8080):
    """Run the keep-alive HTTP server"""
    try:
        with socketserver.TCPServer(("", port), KeepAliveHandler) as httpd:
            logger.info(f"🌐 Keep-alive server running on port {port}")
            httpd.serve_forever()
    except OSError as e:
        if "Address already in use" in str(e):
            logger.warning(f"Port {port} already in use, skipping keep_alive...")
        else:
            logger.error(f"Keep-alive server error: {e}")
    except Exception as e:
        logger.error(f"Keep-alive server error: {e}")


def keep_alive():
    """Start keep-alive server in a background thread"""
    port = int(os.environ.get("PORT", 8080))
    
    server_thread = threading.Thread(
        target=run_server,
        args=(port,),
        daemon=True
    )
    server_thread.start()
    logger.info("✅ Keep-alive thread started")


# ============================================
# ALTERNATIVE: FLASK SERVER (if needed)
# ============================================
def keep_alive_flask():
    """Alternative Flask-based keep-alive (requires Flask)"""
    try:
        from flask import Flask
        
        app = Flask(__name__)
        
        @app.route('/')
        def home():
            return """
            <html>
            <head><title>Watermark Bot</title></head>
            <body style="background:#667eea;color:white;text-align:center;padding-top:100px;font-family:Arial">
                <h1>🤖 Watermark Bot</h1>
                <p>Bot is running!</p>
            </body>
            </html>
            """
        
        @app.route('/health')
        def health():
            return {'status': 'ok'}
        
        port = int(os.environ.get("PORT", 8080))
        app.run(host='0.0.0.0', port=port)
        
    except ImportError:
        logger.warning("Flask not installed, using simple HTTP server...")
        keep_alive()


# ============================================
# MAIN
# ============================================
if __name__ == "__main__":
    print("Starting keep-alive server...")
    keep_alive()
    # Keep the main thread alive
    import time
    while True:
        time.sleep(60)
