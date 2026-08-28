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
# For any question you can visit: https://discord.gg/rYsARc3fB9

# utils.py (v0.8)
import re

def parse_time(time_str: str) -> int:
    """Convierte tiempo ASS 0:00:00.00 a milisegundos absolutos"""
    match = re.match(r'(\d+):(\d+):(\d+)\.(\d+)', time_str.strip())
    if match:
        h, m, s, cs = map(int, match.groups())
        return (h * 3600 + m * 60 + s) * 1000 + cs * 10
    return 0

def format_time(ms: int) -> str:
    """Convierte milisegundos absolutos a formato ASS"""
    ms = max(0, ms)
    cs = (ms % 1000) // 10
    s = (ms // 1000) % 60
    m = (ms // 60000) % 60
    h = ms // 3600000
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"

def parse_color_to_rgb(color_str: str):
    clean = str(color_str).strip()
    if clean.startswith('&H') or clean.startswith('&h'):
        clean_hex = clean.replace('&H', '').replace('&h', '').replace('&', '').strip()
        if len(clean_hex) >= 6:
            b = int(clean_hex[0:2], 16)
            g = int(clean_hex[2:4], 16)
            r = int(clean_hex[4:6], 16)
            return r, g, b
    clean_hex = clean.replace('#', '').strip()
    if len(clean_hex) == 6:
        r = int(clean_hex[0:2], 16)
        g = int(clean_hex[2:4], 16)
        b = int(clean_hex[4:6], 16)
        return r, g, b
    elif len(clean_hex) == 8:
        r = int(clean_hex[2:4], 16)
        g = int(clean_hex[4:6], 16)
        b = int(clean_hex[6:8], 16)
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