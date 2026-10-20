# Pyxis Effector - Plugin for Aegisub
# Copyright (C) 2026 @mandholine, @effector2, @pholguinc
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
# For any question you can visit: https://discord.gg/fsxRESeQZN

"""
Module: utils.py
Architectural Role: Pure utility functions for ASS timestamp conversions, colour formatting, and elementary mathematics.

Upstream Dependencies:
    - re: Regular expressions for robust parsing of ASS timestamps (H:MM:SS.CS).

Downstream Callers:
    - ass_parser.py: Converts Dialogue event timestamps and style parameters to integer milliseconds.
    - karaskel_engine.py: Calculates durations and syllable synchronisation.
    - node_engine.py: Formats final output times and transforms colour palettes.
    - nodes/time_nodes.py: Implements Parse ASS Time, Format ASS Time, and Duration nodes.
    - nodes/basics_nodes.py: Implements Color Picker and ASS/Hex colour conversion nodes.

Side Effects and State:
    - 100% pure functions: Zero global mutable state, zero I/O, deterministic, and thread-safe.
"""

import re


def parse_time(time_str: str) -> int:
    """
    Converts an ASS format timestamp (H:MM:SS.CS) into absolute integer milliseconds.

    Supports variable decimal fractions of 1, 2 (standard ASS centiseconds), 3 (milliseconds), or more digits.

    Args:
        time_str (str): ASS time string (e.g. '0:01:23.45', '1:00:00.100').

    Returns:
        int: Cumulative equivalent time in integer milliseconds (ms >= 0). Returns 0 for empty or invalid strings.

    Dependencies & Couplings:
        - Called by ass_parser.py when processing event lines and styles.
        - Called by Time/Parse ASS Time node.
    """
    if not time_str:
        return 0
    match = re.match(r'(\d+):(\d+):(\d+)(?:\.(\d+))?', str(time_str).strip())
    if match:
        h, m, s, frac = match.groups()
        h, m, s = int(h), int(m), int(s)
        if not frac:
            ms = 0
        elif len(frac) == 1:
            ms = int(frac) * 100
        elif len(frac) == 2:
            ms = int(frac) * 10
        elif len(frac) == 3:
            ms = int(frac)
        else:
            ms = int(round(float("0." + frac) * 1000.0))
        return (h * 3600 + m * 60 + s) * 1000 + ms
    return 0


def format_time(ms: int) -> str:
    """
    Converts integer milliseconds into an ASS standard 'H:MM:SS.CS' formatted string.

    Applies the canonical Aegisub rounding algorithm (+5 ms // 10) for precise centisecond quantisation.

    Args:
        ms (int): Time in integer milliseconds (supports prior float conversion with round).

    Returns:
        str: Formatted string as 'H:MM:SS.CS' (e.g. '0:00:05.20'). Returns '0:00:00.00' for negative or invalid values.

    Dependencies & Couplings:
        - Called by node_engine.py and Time/Format ASS Time to compile output subtitle lines.
    """
    try:
        ms = max(0, int(round(float(ms))))
    except (ValueError, TypeError):
        return "0:00:00.00"
    cs_total = (ms + 5) // 10
    cs = cs_total % 100
    s_total = cs_total // 100
    s = s_total % 60
    m_total = s_total // 60
    m = m_total % 60
    h = m_total // 60
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def parse_color_to_rgb(color_str: str) -> tuple[int, int, int]:
    """
    Parses a heterogeneous colour representation into an integer RGB tuple in range [0, 255].

    Supported Formats:
        - ASS Hex with prefix: &HBBGGRR& (6 digits) or &HAABBGGRR& (8 digits, alpha channel ignored).
        - Web Hexadecimal: #RGB (3 digits), #RGBA (4 digits), #RRGGBB (6 digits), #RRGGBBAA (8 digits).

    Args:
        color_str (str): Encoded colour string.

    Returns:
        tuple[int, int, int]: Tuple (r, g, b) with discrete values in range 0..255. Default fallback: (255, 255, 255).

    Dependencies & Couplings:
        - Called by Basics/Color Picker, Functions/Color Gradient, and palette convertors.
    """
    clean = str(color_str).strip()
    if clean.startswith('&H') or clean.startswith('&h'):
        clean_hex = clean.replace('&H', '').replace('&h', '').replace('&', '').strip()
        if len(clean_hex) == 8:
            # ASS 8-digit hex: &HAABBGGRR&
            b = int(clean_hex[2:4], 16)
            g = int(clean_hex[4:6], 16)
            r = int(clean_hex[6:8], 16)
            return r, g, b
        elif len(clean_hex) >= 6:
            # ASS 6-digit hex: &HBBGGRR&
            b = int(clean_hex[0:2], 16)
            g = int(clean_hex[2:4], 16)
            r = int(clean_hex[4:6], 16)
            return r, g, b
    clean_hex = clean.replace('#', '').strip()
    if len(clean_hex) == 3:
        # Shorthand hex #RGB
        r = int(clean_hex[0] * 2, 16)
        g = int(clean_hex[1] * 2, 16)
        b = int(clean_hex[2] * 2, 16)
        return r, g, b
    elif len(clean_hex) == 4:
        # Shorthand hex #RGBA
        r = int(clean_hex[0] * 2, 16)
        g = int(clean_hex[1] * 2, 16)
        b = int(clean_hex[2] * 2, 16)
        return r, g, b
    elif len(clean_hex) == 6:
        # Web hex #RRGGBB
        r = int(clean_hex[0:2], 16)
        g = int(clean_hex[2:4], 16)
        b = int(clean_hex[4:6], 16)
        return r, g, b
    elif len(clean_hex) == 8:
        # Web hex #RRGGBBAA
        r = int(clean_hex[0:2], 16)
        g = int(clean_hex[2:4], 16)
        b = int(clean_hex[4:6], 16)
        return r, g, b
    return 255, 255, 255


def rgb_to_ass_color(r: int, g: int, b: int) -> str:
    """
    Converts integer RGB components into the ASS native tag colour format (&HBBGGRR&).

    Applies automatic clamping to range [0, 255] and reverses byte order to BGR per the ASS specification.

    Args:
        r (int): Red channel intensity (0..255).
        g (int): Green channel intensity (0..255).
        b (int): Blue channel intensity (0..255).

    Returns:
        str: Uppercase ASS colour literal formatted as '&HBBGGRR&' (e.g. '&H0000FF&' for pure red).
    """
    r = max(0, min(255, int(r)))
    g = max(0, min(255, int(g)))
    b = max(0, min(255, int(b)))
    return f"&H{b:02X}{g:02X}{r:02X}&"


def rgb_to_hex_color(r: int, g: int, b: int) -> str:
    """
    Converts integer RGB components into standard web hexadecimal format (#RRGGBB).

    Args:
        r (int): Red channel intensity (0..255).
        g (int): Green channel intensity (0..255).
        b (int): Blue channel intensity (0..255).

    Returns:
        str: Uppercase hexadecimal string formatted as '#RRGGBB' (e.g. '#FF0000' for pure red).
    """
    r = max(0, min(255, int(r)))
    g = max(0, min(255, int(g)))
    b = max(0, min(255, int(b)))
    return f"#{r:02X}{g:02X}{b:02X}"