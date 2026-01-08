<p align="center">
  <img src="logo-gear.svg" alt="Whooshpad logo" width="128">
  <h1 tabindex="-1" class="heading-element" dir="auto" align="center">Whooshpad</h1>
</p>

[![Build](https://github.com/scorphus/whooshpad/actions/workflows/test.yml/badge.svg)](https://github.com/scorphus/whooshpad/actions/workflows/test.yml)
[![Coverage](https://codecov.io/gh/scorphus/whooshpad/branch/main/graph/badge.svg)](https://codecov.io/gh/scorphus/whooshpad)
[![PyPI](https://img.shields.io/pypi/v/whooshpad.svg)](https://pypi.org/project/whooshpad/)
[![Python](https://img.shields.io/pypi/pyversions/whooshpad.svg)](https://pypi.org/project/whooshpad/)
[![License](https://img.shields.io/pypi/l/whooshpad.svg)](https://github.com/scorphus/whooshpad/blob/main/LICENSE)

A mobile-friendly remote control for [MyWhoosh](https://www.mywhoosh.com/) virtual cycling.

Run Whooshpad on the computer where MyWhoosh is running, then open the web interface on your phone to control shifting, steering, emotes, and UI.

## Installation

```bash
pip install whooshpad
```

## Usage

1. Start Whooshpad on your computer:
   ```bash
   whooshpad
   ```

2. Open the displayed URL on your mobile (e.g., `http://192.168.1.100:8765`)

3. Use the buttons to control MyWhoosh!

## Controls

- **Shifting**: < (easier) / > (harder)
- **Steering**: Left / Right arrows
- **Emotes**: Peace, Wave, Fist bump, Dab, Elbow flick, Toast, Thumbs up
- **UI**: Toggle minimal UI / Hide all controls
- **Screenshot**: System screenshot (Cmd+Shift+3 on macOS, PrintScreen on Windows)

## Options

```bash
whooshpad --port 8080  # Use a different port
```

## macOS Note

On macOS, you may need to grant Accessibility permissions to your terminal or Python in System Preferences > Security & Privacy > Privacy > Accessibility.

## License

BSD-3-Clause
