#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Tests for whooshpad server."""

import platform
from io import BytesIO

import pytest
from pynput.keyboard import KeyCode

from whooshpad.server import (
    HTML_PAGE,
    KEYS,
    WhooshpadHandler,
    _make_key,
    _screenshot,
    get_local_ip,
)


def test_make_key_returns_keycode_for_numbers_on_macos_windows(mocker):
    """Test _make_key returns KeyCode for numbers on macOS/Windows."""
    mocker.patch("whooshpad.server.platform.system", return_value="Darwin")
    key = _make_key("1")
    assert isinstance(key, KeyCode)
    assert key.vk == 18  # macOS vk for "1"

    mocker.patch("whooshpad.server.platform.system", return_value="Windows")
    key = _make_key("2")
    assert isinstance(key, KeyCode)
    assert key.vk == 0x32  # Windows vk for "2"


def test_make_key_returns_string_for_non_numbers():
    """Test _make_key returns string for non-number characters."""
    key = _make_key("a")
    assert key == "a"


def test_make_key_returns_string_on_other_platforms(mocker):
    """Test _make_key returns string on unsupported platforms."""
    mocker.patch("whooshpad.server.platform.system", return_value="Linux")
    key = _make_key("1")
    assert key == "1"


def test_screenshot_on_macos(mocker):
    """Test _screenshot uses Cmd+Shift+3 on macOS."""
    mocker.patch("whooshpad.server.platform.system", return_value="Darwin")
    mock_keyboard = mocker.patch("whooshpad.server.keyboard")
    _screenshot()
    assert mock_keyboard.pressed.call_count == 2
    mock_keyboard.press.assert_called_once_with("3")
    mock_keyboard.release.assert_called_once_with("3")


def test_screenshot_on_windows(mocker):
    """Test _screenshot uses PrintScreen on Windows."""
    mocker.patch("whooshpad.server.platform.system", return_value="Windows")
    mock_keyboard = mocker.patch("whooshpad.server.keyboard")
    mock_key = mocker.patch("whooshpad.server.Key")
    _screenshot()
    mock_keyboard.press.assert_called_once_with(mock_key.print_screen)
    mock_keyboard.release.assert_called_once_with(mock_key.print_screen)


def test_screenshot_on_other_platforms(mocker):
    """Test _screenshot does nothing on unsupported platforms."""
    mocker.patch("whooshpad.server.platform.system", return_value="Linux")
    mock_keyboard = mocker.patch("whooshpad.server.keyboard")
    _screenshot()
    mock_keyboard.press.assert_not_called()
    mock_keyboard.release.assert_not_called()


def test_keys_contains_shifting():
    """Test that shifting keys are defined."""
    assert "shift_up" in KEYS
    assert "shift_down" in KEYS
    assert KEYS["shift_up"] == "i"
    assert KEYS["shift_down"] == "k"


def test_keys_contains_steering():
    """Test that steering keys are defined."""
    assert "steer_left" in KEYS
    assert "steer_right" in KEYS
    assert KEYS["steer_left"] == "a"
    assert KEYS["steer_right"] == "d"


def test_keys_contains_emotes():
    """Test that emote keys are defined."""
    for i in range(1, 8):
        assert f"emote_{i}" in KEYS
        key = KEYS[f"emote_{i}"]
        if platform.system() in ("Darwin", "Windows"):
            assert isinstance(key, KeyCode)
            assert key.vk is not None
        else:
            assert key == str(i)


def test_keys_contains_ui_controls():
    """Test that UI control keys are defined."""
    assert "ui_toggle" in KEYS
    assert "hide_ui" in KEYS
    assert KEYS["ui_toggle"] == "u"
    assert KEYS["hide_ui"] == "h"


def test_html_page_contains_buttons():
    """Test that HTML page contains all control buttons."""
    assert "btn-shift-up" in HTML_PAGE
    assert "btn-shift-down" in HTML_PAGE
    assert "btn-steer-left" in HTML_PAGE
    assert "btn-steer-right" in HTML_PAGE
    assert "btn-ui-toggle" in HTML_PAGE


def test_html_page_is_valid_html():
    """Test that HTML page has basic structure."""
    assert "<!DOCTYPE html>" in HTML_PAGE
    assert "<html>" in HTML_PAGE
    assert "</html>" in HTML_PAGE
    assert "<head>" in HTML_PAGE
    assert "<body>" in HTML_PAGE


def test_get_local_ip_returns_string():
    """Test that get_local_ip returns a string."""
    ip = get_local_ip()
    assert isinstance(ip, str)
    assert len(ip) > 0


def test_get_local_ip_returns_valid_format():
    """Test that get_local_ip returns localhost or valid IP format."""
    ip = get_local_ip()
    if ip != "localhost":
        parts = ip.split(".")
        assert len(parts) == 4
        for part in parts:
            assert part.isdigit()
            assert 0 <= int(part) <= 255


def test_get_local_ip_fallback_on_error(mocker):
    """Test that get_local_ip returns localhost on socket error."""
    mock_socket = mocker.patch("whooshpad.server.socket.socket")
    mock_socket.return_value.connect.side_effect = Exception("Network error")

    ip = get_local_ip()
    assert ip == "localhost"


@pytest.fixture
def mock_handler(mocker):
    """Create a mock WhooshpadHandler."""
    mocker.patch("whooshpad.server.keyboard")
    handler = mocker.MagicMock(spec=WhooshpadHandler)
    handler.path = "/"
    handler.wfile = BytesIO()
    handler.send_response = mocker.MagicMock()
    handler.send_header = mocker.MagicMock()
    handler.end_headers = mocker.MagicMock()
    handler.send_error = mocker.MagicMock()
    return handler


def test_handler_do_get_index(mock_handler):
    """Test GET / returns HTML page."""
    mock_handler.path = "/"
    WhooshpadHandler.do_GET(mock_handler)

    mock_handler.send_response.assert_called_once_with(200)
    mock_handler.send_header.assert_called_once_with("Content-type", "text/html")
    mock_handler.end_headers.assert_called_once()


def test_handler_do_get_index_html(mock_handler):
    """Test GET /index.html returns HTML page."""
    mock_handler.path = "/index.html"
    WhooshpadHandler.do_GET(mock_handler)

    mock_handler.send_response.assert_called_once_with(200)


def test_handler_do_get_404(mock_handler):
    """Test GET unknown path returns 404."""
    mock_handler.path = "/unknown"
    WhooshpadHandler.do_GET(mock_handler)

    mock_handler.send_error.assert_called_once_with(404)


def test_handler_do_post_shift_up(mock_handler, mocker):
    """Test POST /key/shift_up presses the correct key."""
    mock_keyboard = mocker.patch("whooshpad.server.keyboard")
    mock_handler.path = "/key/shift_up"

    WhooshpadHandler.do_POST(mock_handler)

    mock_keyboard.press.assert_called_once_with("i")
    mock_keyboard.release.assert_called_once_with("i")
    mock_handler.send_response.assert_called_once_with(200)


def test_handler_do_post_shift_down(mock_handler, mocker):
    """Test POST /key/shift_down presses the correct key."""
    mock_keyboard = mocker.patch("whooshpad.server.keyboard")
    mock_handler.path = "/key/shift_down"

    WhooshpadHandler.do_POST(mock_handler)

    mock_keyboard.press.assert_called_once_with("k")
    mock_keyboard.release.assert_called_once_with("k")


def test_handler_do_post_steer_left(mock_handler, mocker):
    """Test POST /key/steer_left presses the correct key."""
    mock_keyboard = mocker.patch("whooshpad.server.keyboard")
    mock_handler.path = "/key/steer_left"

    WhooshpadHandler.do_POST(mock_handler)

    mock_keyboard.press.assert_called_once_with("a")
    mock_keyboard.release.assert_called_once_with("a")


def test_handler_do_post_emote(mock_handler, mocker):
    """Test POST /key/emote_1 presses the correct key."""
    mock_keyboard = mocker.patch("whooshpad.server.keyboard")
    mock_handler.path = "/key/emote_1"

    WhooshpadHandler.do_POST(mock_handler)

    # On macOS, emotes use KeyCode with virtual key codes
    expected_key = KEYS["emote_1"]
    mock_keyboard.press.assert_called_once_with(expected_key)
    mock_keyboard.release.assert_called_once_with(expected_key)


def test_handler_do_post_unknown_action(mock_handler):
    """Test POST /key/unknown returns 404."""
    mock_handler.path = "/key/unknown"

    WhooshpadHandler.do_POST(mock_handler)

    mock_handler.send_error.assert_called_once()


def test_handler_do_post_invalid_path(mock_handler):
    """Test POST /invalid returns 404."""
    mock_handler.path = "/invalid"

    WhooshpadHandler.do_POST(mock_handler)

    mock_handler.send_error.assert_called_once_with(404)


def test_handler_do_post_screenshot(mock_handler, mocker):
    """Test POST /key/screenshot triggers screenshot."""
    mock_screenshot = mocker.patch("whooshpad.server._screenshot")
    mock_handler.path = "/key/screenshot"

    WhooshpadHandler.do_POST(mock_handler)

    mock_screenshot.assert_called_once()
    mock_handler.send_response.assert_called_once_with(200)
