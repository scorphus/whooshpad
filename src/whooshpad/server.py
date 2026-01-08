#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Whooshpad server - serves the mobile remote control interface."""

import argparse
import platform
import socket
from http.server import HTTPServer, SimpleHTTPRequestHandler

try:
    from pynput.keyboard import Controller, Key, KeyCode
except ImportError:  # pragma: no cover
    print("Error: pynput is required. Install it with: pip install pynput")
    print("On macOS, you may need to grant Accessibility permissions.")
    exit(1)

keyboard = Controller()

# Virtual key codes for top-row number keys (not numpad)
_NUMBER_VK = {
    "Darwin": {
        "1": 18,
        "2": 19,
        "3": 20,
        "4": 21,
        "5": 23,
        "6": 22,
        "7": 26,
    },
    "Windows": {
        "1": 0x31,
        "2": 0x32,
        "3": 0x33,
        "4": 0x34,
        "5": 0x35,
        "6": 0x36,
        "7": 0x37,
    },
}


def _make_key(char):
    """Create a key, using virtual key codes for numbers on macOS/Windows."""
    system = platform.system()
    if system in _NUMBER_VK and char in _NUMBER_VK[system]:
        return KeyCode.from_vk(_NUMBER_VK[system][char])
    return char


def _screenshot():
    """Take a screenshot using system keyboard shortcuts."""
    system = platform.system()
    if system == "Darwin":
        # macOS: Cmd+Shift+3
        with keyboard.pressed(Key.cmd):
            with keyboard.pressed(Key.shift):
                keyboard.press("3")
                keyboard.release("3")
    elif system == "Windows":
        # Windows: PrintScreen
        keyboard.press(Key.print_screen)
        keyboard.release(Key.print_screen)


# MyWhoosh keyboard shortcuts
KEYS = {
    "shift_up": "i",  # Easier gear
    "shift_down": "k",  # Harder gear
    "steer_left": "a",  # Steer left
    "steer_right": "d",  # Steer right
    "emote_1": _make_key("1"),  # Peace
    "emote_2": _make_key("2"),  # Wave
    "emote_3": _make_key("3"),  # Fist bump
    "emote_4": _make_key("4"),  # Dab
    "emote_5": _make_key("5"),  # Elbow flick
    "emote_6": _make_key("6"),  # Toast
    "emote_7": _make_key("7"),  # Thumbs up
    "ui_toggle": "u",  # Minimal UI
    "hide_ui": "h",  # Hide all (HD only)
}

FAVICON = """data:image/svg+xml;base64,PHN2ZyB4bWxucz0naHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmcnIHZpZXdCb3g9JzAgMCAxMDAgMTAwJz48cGF0aCBmaWxsPScjMDAwMDAxJyBkPSdNNDYgNWwtMS45NyA5Ljg0YTM1LjcgMzUuNyAwIDAwLTE0LjY1IDYuMDlsLTguMzctNS41OC0yLjgzIDIuODMtMi44MyAyLjgzIDUuNTggOC4zN2EzNS43IDM1LjcgMCAwMC02LjA5IDE0LjY1TDUgNDZ2OGw5Ljg0IDEuOTdhMzUuNyAzNS43IDAgMDA2LjA5IDE0LjY1bC01LjU4IDguMzcgMi44MyAyLjgzIDIuODMgMi44MyA4LjM3LTUuNThhMzUuNyAzNS43IDAgMDAxNC42NSA2LjA5TDQ2IDk1aDhsMS45Ny05Ljg0YTM1LjcgMzUuNyAwIDAwMTQuNjUtNi4wOWw4LjM3IDUuNTggMi44My0yLjgzIDIuODMtMi44My01LjU4LTguMzdhMzUuNyAzNS43IDAgMDA2LjA5LTE0LjY1TDk1IDU0di04bC05Ljc5LTEuOTZhMzUuNyAzNS43IDAgMDAtNi4xLTE0LjcybDUuNTQtOC4zMS0yLjgzLTIuODMtMi44My0yLjgzLTguMzEgNS41NGEzNS43IDM1LjcgMCAwMC0xNC43Mi02LjFMNTQgNWgtOHonLz48Y2lyY2xlIGN4PSc1MCcgY3k9JzUwJyByPScyNi42NScgZmlsbD0nI2ZmY2QyZicvPjxjaXJjbGUgY3g9JzM3LjEyJyBjeT0nNTAnIHI9JzEyJyBmaWxsPScjMDBiODk0Jy8+PHRleHQgeD0nMzcuMTInIHk9JzU2LjM2JyBmb250LXNpemU9JzE4JyBmb250LXdlaWdodD0nYm9sZCcgZm9udC1mYW1pbHk9J0FyaWFsJyB0ZXh0LWFuY2hvcj0nbWlkZGxlJyBmaWxsPScjZmZmJz4mbHQ7PC90ZXh0PjxjaXJjbGUgY3g9JzYyLjg4JyBjeT0nNTAnIHI9JzEyJyBmaWxsPScjZDYzMDMxJy8+PHRleHQgeD0nNjIuODgnIHk9JzU2LjM1JyBmb250LXNpemU9JzE4JyBmb250LXdlaWdodD0nYm9sZCcgZm9udC1mYW1pbHk9J0FyaWFsJyB0ZXh0LWFuY2hvcj0nbWlkZGxlJyBmaWxsPScjZmZmJz4mZ3Q7PC90ZXh0Pjwvc3ZnPgo="""  # noqa

HTML_PAGE = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, user-scalable=no">
    <title>Whooshpad</title>
    <link rel="icon" type="image/svg+xml" href=""" + FAVICON + """>
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
            flex: 5;
        }
        .section.small {
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
            background: linear-gradient(135deg, #81ecec, #00cec9);
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
            <button class="shift-up" id="btn-shift-up">&lt;</button>
            <button class="shift-down" id="btn-shift-down">&gt;</button>
        </div>

        <!-- Steering -->
        <div class="section small">
            <button class="steer" id="btn-steer-left">&larr;</button>
            <button class="steer" id="btn-steer-right">&rarr;</button>
        </div>

        <!-- Emotes -->
        <div class="section small">
            <button class="emote" id="btn-emote-1">&#9996;</button>
            <button class="emote" id="btn-emote-2">&#128075;</button>
            <button class="emote" id="btn-emote-3">&#129307;</button>
            <button class="emote" id="btn-emote-4">&#128131;</button>
        </div>
        <div class="section small">
            <button class="emote" id="btn-emote-5">&#128170;</button>
            <button class="emote" id="btn-emote-6">&#127838;</button>
            <button class="emote" id="btn-emote-7">&#128077;</button>
        </div>

        <!-- UI Controls -->
        <div class="section small">
            <button class="ui-btn" id="btn-ui-toggle">UI</button>
            <button class="ui-btn" id="btn-hide-ui">Hide</button>
            <button class="ui-btn" id="btn-screenshot">&#128248;</button>
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
            'btn-screenshot': ['screenshot', 'Screenshot'],
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
            if action == "screenshot":
                _screenshot()
                print("[SCREENSHOT] Triggered")
                self.send_response(200)
                self.end_headers()
            elif action in KEYS:
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
