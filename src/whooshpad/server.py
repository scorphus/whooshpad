#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Whooshpad server - serves the mobile remote control interface."""

import argparse
import socket
from http.server import HTTPServer, SimpleHTTPRequestHandler

try:
    from pynput.keyboard import Controller
except ImportError:  # pragma: no cover
    print("Error: pynput is required. Install it with: pip install pynput")
    print("On macOS, you may need to grant Accessibility permissions.")
    exit(1)

keyboard = Controller()

# MyWhoosh keyboard shortcuts
KEYS = {
    "shift_up": "i",  # Easier gear
    "shift_down": "k",  # Harder gear
    "steer_left": "a",  # Steer left
    "steer_right": "d",  # Steer right
    "emote_1": "1",  # Peace
    "emote_2": "2",  # Wave
    "emote_3": "3",  # Fist bump
    "emote_4": "4",  # Dab
    "emote_5": "5",  # Elbow flick
    "emote_6": "6",  # Toast
    "emote_7": "7",  # Thumbs up
    "ui_toggle": "u",  # Minimal UI
    "hide_ui": "h",  # Hide all (HD only)
}

HTML_PAGE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Whooshpad</title>
    <style>
        * {
            box-sizing: border-box;
            touch-action: manipulation;
            -webkit-tap-highlight-color: transparent;
        }
        html, body {
            margin: 0;
            padding: 0;
            height: 100%;
            overflow: hidden;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
            background: #1a1a2e;
            color: white;
        }
        .container {
            display: flex;
            flex-direction: column;
            height: 100%;
            padding: 10px;
            gap: 10px;
        }
        h1 {
            text-align: center;
            margin: 0;
            padding: 5px;
            font-size: 1.2rem;
            color: #888;
        }
        .section {
            display: flex;
            gap: 10px;
        }
        .section.grow {
            flex: 1;
        }
        button {
            flex: 1;
            border: none;
            border-radius: 12px;
            font-size: 2rem;
            font-weight: bold;
            cursor: pointer;
            transition: transform 0.1s, opacity 0.1s;
            user-select: none;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        button:active {
            transform: scale(0.95);
            opacity: 0.8;
        }
        .shift-up {
            background: linear-gradient(135deg, #00b894, #00cec9);
            color: white;
            font-size: 4rem;
        }
        .shift-down {
            background: linear-gradient(135deg, #e17055, #d63031);
            color: white;
            font-size: 4rem;
        }
        .steer {
            background: linear-gradient(135deg, #6c5ce7, #a29bfe);
            color: white;
        }
        .emote {
            background: linear-gradient(135deg, #fdcb6e, #f39c12);
            color: #333;
            font-size: 1.5rem;
        }
        .ui-btn {
            background: linear-gradient(135deg, #636e72, #2d3436);
            color: white;
            font-size: 1rem;
        }
        .status {
            text-align: center;
            padding: 5px;
            font-size: 0.8rem;
            color: #666;
        }
        .status.active {
            color: #00b894;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Whooshpad</h1>

        <!-- Shifting -->
        <div class="section grow">
            <button class="shift-up" id="btn-shift-up">+</button>
            <button class="shift-down" id="btn-shift-down">-</button>
        </div>

        <!-- Steering -->
        <div class="section">
            <button class="steer" id="btn-steer-left">&larr;</button>
            <button class="steer" id="btn-steer-right">&rarr;</button>
        </div>

        <!-- Emotes -->
        <div class="section">
            <button class="emote" id="btn-emote-1">&#9996;</button>
            <button class="emote" id="btn-emote-2">&#128075;</button>
            <button class="emote" id="btn-emote-3">&#129307;</button>
            <button class="emote" id="btn-emote-4">&#128131;</button>
        </div>
        <div class="section">
            <button class="emote" id="btn-emote-5">&#128170;</button>
            <button class="emote" id="btn-emote-6">&#127867;</button>
            <button class="emote" id="btn-emote-7">&#128077;</button>
        </div>

        <!-- UI Controls -->
        <div class="section">
            <button class="ui-btn" id="btn-ui-toggle">UI</button>
            <button class="ui-btn" id="btn-hide-ui">Hide</button>
        </div>

        <div class="status" id="status">Ready</div>
    </div>
    <script>
        const status = document.getElementById('status');

        async function sendKey(action, label) {
            status.textContent = label + '...';
            status.className = 'status active';

            try {
                const response = await fetch('/key/' + action, { method: 'POST' });
                if (response.ok) {
                    status.textContent = label;
                } else {
                    status.textContent = 'Error!';
                    status.className = 'status';
                }
            } catch (e) {
                status.textContent = 'Connection error';
                status.className = 'status';
            }

            setTimeout(() => {
                status.textContent = 'Ready';
                status.className = 'status';
            }, 400);
        }

        // Button mappings
        const buttons = {
            'btn-shift-up': ['shift_up', 'Shift +'],
            'btn-shift-down': ['shift_down', 'Shift -'],
            'btn-steer-left': ['steer_left', 'Left'],
            'btn-steer-right': ['steer_right', 'Right'],
            'btn-emote-1': ['emote_1', 'Peace'],
            'btn-emote-2': ['emote_2', 'Wave'],
            'btn-emote-3': ['emote_3', 'Fist bump'],
            'btn-emote-4': ['emote_4', 'Dab'],
            'btn-emote-5': ['emote_5', 'Elbow'],
            'btn-emote-6': ['emote_6', 'Toast'],
            'btn-emote-7': ['emote_7', 'Thumbs up'],
            'btn-ui-toggle': ['ui_toggle', 'UI toggle'],
            'btn-hide-ui': ['hide_ui', 'Hide UI'],
        };

        // Bind all buttons
        for (const [id, [action, label]] of Object.entries(buttons)) {
            const btn = document.getElementById(id);
            btn.addEventListener('pointerdown', (e) => {
                e.preventDefault();
                sendKey(action, label);
            });
        }

        // Prevent context menu on long press
        document.addEventListener('contextmenu', e => e.preventDefault());
    </script>
</body>
</html>
"""


class WhooshpadHandler(SimpleHTTPRequestHandler):
    """HTTP request handler for Whooshpad."""

    def do_GET(self):
        """Serve the HTML page."""
        if self.path == "/" or self.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode())
        else:
            self.send_error(404)

    def do_POST(self):
        """Handle key press commands."""
        if self.path.startswith("/key/"):
            action = self.path[5:]  # Remove "/key/" prefix
            if action in KEYS:
                key = KEYS[action]
                keyboard.press(key)
                keyboard.release(key)
                print(f"[{action.upper()}] Pressed '{key}'")
                self.send_response(200)
                self.end_headers()
            else:
                self.send_error(404, f"Unknown action: {action}")
        else:
            self.send_error(404)

    def log_message(self, format, *args):  # pragma: no cover
        """Suppress default logging for cleaner output."""
        pass


def get_local_ip():
    """Get the local IP address of this machine."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return "localhost"


def main():  # pragma: no cover
    """Run the Whooshpad server."""
    parser = argparse.ArgumentParser(description="Whooshpad - Remote control for MyWhoosh")
    parser.add_argument("--port", type=int, default=8765, help="Port to run on (default: 8765)")
    args = parser.parse_args()

    local_ip = get_local_ip()
    server = HTTPServer(("0.0.0.0", args.port), WhooshpadHandler)

    print("=" * 50)
    print("  Whooshpad - Remote Control for MyWhoosh")
    print("=" * 50)
    print("\n  Open on your mobile:")
    print(f"  http://{local_ip}:{args.port}")
    print("\n  Press Ctrl+C to stop\n")
    print("=" * 50)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down...")
        server.shutdown()


if __name__ == "__main__":  # pragma: no cover
    main()
