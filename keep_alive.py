# keep_alive.py - Advanced Bot Alive System
# 100% Compatible with Render, Replit, Heroku, and UptimeRobot

import threading
import http.server
import socketserver
import logging
import os

logger = logging.getLogger("KeepAlive")

# ============================================
# MODERN PREMIUM UI (HTML/CSS)
# ============================================
# Modern Glassmorphism dark theme dashboard for health checks
HTML_CONTENT = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Watermark Bot | System Status</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap" rel="stylesheet">
    <style>
        :root { 
            --bg: #0f172a; 
            --card: rgba(30, 41, 59, 0.7); 
            --text: #f8fafc; 
            --accent: #3b82f6; 
            --success: #22c55e; 
        }
        body { 
            margin: 0; 
            font-family: 'Inter', sans-serif; 
            background: var(--bg); 
            color: var(--text); 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            min-height: 100vh; 
            overflow: hidden; 
        }
        /* Glowing Orbs in background */
        .orb { position: absolute; border-radius: 50%; filter: blur(80px); opacity: 0.4; z-index: -1; }
        .orb-1 { top: -10%; left: -10%; width: 400px; height: 400px; background: var(--accent); }
        .orb-2 { bottom: -10%; right: -10%; width: 300px; height: 300px; background: var(--success); }
        
        /* Modern Glass Card */
        .glass-card { 
            background: var(--card); 
            backdrop-filter: blur(16px); 
            -webkit-backdrop-filter: blur(16px);
            border: 1px solid rgba(255,255,255,0.05); 
            padding: 40px; 
            border-radius: 24px; 
            text-align: center; 
            box-shadow: 0 25px 50px -12px rgba(0,0,0,0.5); 
            width: 90%; 
            max-width: 400px; 
        }
        .logo { font-size: 56px; margin-bottom: 10px; animation: float 3s ease-in-out infinite; }
        h1 { font-size: 26px; font-weight: 700; margin: 0 0 8px 0; letter-spacing: -0.5px; }
        p { color: #94a3b8; font-size: 15px; margin: 0 0 24px 0; }
        
        /* Glowing Status Badge */
        .status-badge { 
            display: inline-flex; 
            align-items: center; 
            gap: 10px; 
            background: rgba(34, 197, 94, 0.1); 
            color: var(--success); 
            padding: 10px 20px; 
            border-radius: 99px; 
            font-weight: 600; 
            font-size: 15px; 
            border: 1px solid rgba(34, 197, 94, 0.2); 
            box-shadow: 0 0 20px rgba(34, 197, 94, 0.1);
        }
        .pulse { 
            width: 12px; 
            height: 12px; 
            background: var(--success); 
            border-radius: 50%; 
            box-shadow: 0 0 0 0 rgba(34,197,94, 0.7); 
            animation: pulse 2s infinite; 
        }
        .footer { margin-top: 30px; font-size: 13px; color: #64748b; font-weight: 400; }
        
        /* Animations */
        @keyframes pulse { 
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.7); } 
            70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(34, 197, 94, 0); } 
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(34, 197, 94, 0); } 
        }
        @keyframes float { 
            0% { transform: translateY(0px); } 
            50% { transform: translateY(-10px); } 
            100% { transform: translateY(0px); } 
        }
    </style>
</head>
<body>
    <div class="orb orb-1"></div>
    <div class="orb orb-2"></div>
    <div class="glass-card">
        <div class="logo">🤖</div>
        <h1>Watermark Engine</h1>
        <p>Enterprise PDF Processing System</p>
        <div class="status-badge">
            <div class="pulse"></div>
            System Online & Active
        </div>
        <div class="footer">
            Routing Network: Render.com<br>
            Awaiting UptimeRobot Ping...
        </div>
    </div>
</body>
</html>
"""

# ============================================
# SIMPLE HTTP SERVER (FALLBACK)
# ============================================
class KeepAliveHandler(http.server.BaseHTTPRequestHandler):
    """Simple HTTP handler for health checks"""
    
    def do_GET(self):
        """Handle GET requests"""
        self.send_response(200)
        self.send_header('Content-type', 'text/html; charset=utf-8')
        self.end_headers()
        self.wfile.write(HTML_CONTENT.encode('utf-8'))
    
    def log_message(self, format, *args):
        """Suppress default logging to keep console clean"""
        pass

def run_server(port: int):
    """Run the basic keep-alive HTTP server"""
    try:
        socketserver.TCPServer.allow_reuse_address = True
        # 🔴 ASLI FIX: "0.0.0.0" is strictly required by Render for external port scanning
        with socketserver.TCPServer(("0.0.0.0", port), KeepAliveHandler) as httpd:
            logger.info(f"🌐 Primary HTTP Server active on 0.0.0.0:{port}")
            httpd.serve_forever()
    except Exception as e:
        logger.error(f"HTTP server error: {e}")


# ============================================
# FLASK SERVER (PRIMARY - RECOMMENDED FOR RENDER)
# ============================================
def keep_alive_flask(port: int):
    """Advanced Flask-based keep-alive (Better routing and stability)"""
    from flask import Flask
    
    # Hide Flask spam logs
    log = logging.getLogger('werkzeug')
    log.setLevel(logging.ERROR)
    
    app = Flask(__name__)
    
    @app.route('/')
    def home():
        return HTML_CONTENT
    
    @app.route('/health')
    def health():
        return {'status': 'System is perfectly healthy', 'code': 200}
    
    # 🔴 ASLI FIX: host='0.0.0.0' guarantees Render will find the port
    logger.info(f"🌐 Advanced Flask Server active on 0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port, debug=False, use_reloader=False)


# ============================================
# MASTER LAUNCHER
# ============================================
def keep_alive():
    """Smart launcher: Tries Flask first, falls back to Basic HTTP"""
    # Render assigns dynamic ports via $PORT. Defaults to 8080 locally.
    port = int(os.environ.get("PORT", 8080))
    
    try:
        # Flask is much more stable on Render, let's try it first
        import flask
        server_thread = threading.Thread(target=keep_alive_flask, args=(port,), daemon=True)
    except ImportError:
        # If Flask isn't installed, fallback to the built-in HTTP server
        logger.warning("Flask not found. Falling back to Basic HTTP Server...")
        server_thread = threading.Thread(target=run_server, args=(port,), daemon=True)
        
    server_thread.start()
    logger.info("✅ Keep-alive background worker successfully injected")


# ============================================
# TESTING
# ============================================
if __name__ == "__main__":
    print("Starting Web Server...")
    keep_alive()
    
    # Keep the main thread alive if run directly
    import time
    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        print("Server shutdown complete.")