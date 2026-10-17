# Pyxis Effector - Plugin for Aegisub
# Copyright (C) 2026 @mandholine, @effector2, @pholguinc and Pyxis Effector contributors
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
# For any question you can visit: https://discord.gg/rYsARc3fB9

import re

def parse_time(time_str: str) -> int:
    """Converts ASS time 0:00:00.00 to absolute milliseconds, supporting 1, 2, 3 or more fractional digits."""
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
    """Converts absolute milliseconds to ASS format with standard Aegisub centisecond rounding."""
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

def parse_color_to_rgb(color_str: str):
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
    r = max(0, min(255, int(r)))
    g = max(0, min(255, int(g)))
    b = max(0, min(255, int(b)))
    return f"&H{b:02X}{g:02X}{r:02X}&"

def rgb_to_hex_color(r: int, g: int, b: int) -> str:
    r = max(0, min(255, int(r)))
    g = max(0, min(255, int(g)))
    b = max(0, min(255, int(b)))
    return f"#{r:02X}{g:02X}{b:02X}"