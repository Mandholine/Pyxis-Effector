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
Module: ass_parser.py
Architectural Role: Autonomous Advanced SubStation Alpha (ASS) file parser and typographic tokenisation engine.

This module parses ASS script files into memory structures, resolving resolution headers, styles,
project metadata, and dialogue events. It decomposes dialogue lines into discrete typographical
hierarchies (lines, syllables, words, characters, furigana) with accurate spatial positioning,
timing, and style cascading.

Architecture and Pipeline:
    1. ASS File Tokenisation: Parses [Script Info], [V4+ Styles], [Events], [Aegisub Project Garbage],
       and [Pyxis Config] sections (`ASSParser.read_file`).
    2. Header and Dummy Media Resolution: Extracts PlayResX/Y, FrameDuration, video/audio paths,
       and parses ?dummy video strings.
    3. Event Decomposition: Tokenises raw ASS Dialogue lines into structured PyxisLine entities
       via `KaraokeProcessor.process_line`.
    4. Syllable and Character Layout: Integrates with `KaraskelEngine` and `FontEngine` to compute
       metrics without reliance on external Lua engines or Aegisub runtime comments.
    5. Structural Linking: Assembles word boundaries, calculates proportional character durations,
       computes contiguous visible indices (ci, cn), and links adjacent siblings (prev, next).

Upstream Dependencies:
    - re, math: Standard pattern matching and numeric functions.
    - utils.parse_time: Converts H:MM:SS.CS timestamps to integer milliseconds.
    - models: Instantiates PyxisLine, PyxisUnit, and StyleRef.
    - font_engine.FontEngine: Typographic width and extent measurements.
    - karaskel_engine.KaraskelEngine: Core layout positioning and font dimension calculation.

Downstream Callers:
    - node_engine.GraphEngine: Ingests parsed dialogues and styles to drive DAG execution.
    - main.py: Loads ASS project files and passes parsed metadata to the UI.
    - pyxis_daemon.py: Previews and renders subtitles on incoming IPC requests.
    - benchmark_runner.py: Evaluates parser throughput and stress workloads.

Side Effects and State:
    - Passive file reading via UTF-8 with BOM stripping (`utf-8-sig`).
    - Zero global mutable state; instantiates isolated, immutable or freshly bound data structures.
"""

import re
import math
from typing import Any, Dict, List, Optional, Tuple

from utils import parse_time
from models import PyxisLine, PyxisUnit, StyleRef
from font_engine import FontEngine
from karaskel_engine import KaraskelEngine, KaraskelMeta, KaraskelLine

StyleDict = Dict[str, str]
MetricsDict = Dict[str, Any]
DialogueItem = Dict[str, Any]


def _csv_floats(value: str) -> List[float]:
    if not value:
        return []
    out: List[float] = []
    for part in value.split(','):
        part = part.strip()
        if not part:
            continue
        try:
            out.append(float(part))
        except Exception:
            pass
    return out


def _split_metric_string(met_str: str) -> Dict[str, str]:
    parts: Dict[str, str] = {}
    for chunk in met_str.split(';'):
        if '=' not in chunk:
            continue
        key, value = chunk.split('=', 1)
        parts[key.strip()] = value.strip()
    return parts


def _make_unit() -> PyxisUnit:
    return PyxisUnit()


DUMMY_VIDEO_REGEX = re.compile(
    r"^\?dummy:([0-9.]+):(\d+):(\d+):(\d+):(\d+):(\d+):(\d+)(?::([a-zA-Z]))?",
    re.IGNORECASE
)
DUMMY_AUDIO_REGEX = re.compile(r"^dummy-audio:silence", re.IGNORECASE)


class ASSParseResult(tuple):
    """
    Structured 5-element tuple representing the parsed ASS document, enriched with named properties.

    Maintains backwards compatibility with standard 5-tuple unpacking `(styles, dialogues, res_x, res_y, frame_dur)`
    while exposing auxiliary media metadata as first-class attributes.

    Attributes:
        styles (dict[str, dict]): Mapping of style names to raw style definition dictionaries.
        dialogues (list[dict]): List of raw dialogue/comment event lines with optional pre-parsed metrics.
        res_x (int): Horizontal script resolution (PlayResX or video width), guaranteed even.
        res_y (int): Vertical script resolution (PlayResY or video height), guaranteed even.
        frame_dur (float): Video frame duration in milliseconds (default 41.708 ms for ~23.976 fps).
        audio_file (str): Associated audio file path or URI from project metadata.
        video_file (str): Associated video file path or ?dummy video specification string.
        video_ar (float): Video aspect ratio value if defined in project garbage.
        video_pos (int): Current frame playback position in Aegisub.
        dummy_info (dict): Extracted parameters if video_file is an Aegisub dummy video.
        is_dummy_video (bool): True if the video stream is synthetic/dummy.
        is_dummy_audio (bool): True if the audio stream is dummy or silent.
        script_file (str): Original ASS script filepath recorded in Pyxis config.
    """
    def __new__(cls, styles, dialogues, res_x, res_y, frame_dur, audio_file="", video_file="",
                video_ar=0.0, video_pos=0, dummy_info=None, is_dummy_video=False, is_dummy_audio=False,
                script_file=""):
        obj = super().__new__(cls, (styles, dialogues, res_x, res_y, frame_dur))
        obj.styles = styles
        obj.dialogues = dialogues
        obj.res_x = res_x
        obj.res_y = res_y
        obj.frame_dur = frame_dur
        obj.audio_file = audio_file
        obj.video_file = video_file
        obj.video_ar = video_ar
        obj.video_pos = video_pos
        obj.dummy_info = dummy_info or {}
        obj.is_dummy_video = is_dummy_video
        obj.is_dummy_audio = is_dummy_audio
        obj.script_file = script_file
        return obj


class ASSParser:
    """
    Parser for Advanced SubStation Alpha (.ass) subtitle files.

    Reads ASS files from disk, segments sections by standard header markers, and extracts
    project configuration, styles, and raw dialogue events.
    """
    @staticmethod
    def read_file(filepath: str) -> ASSParseResult:
        """
        Parses an ASS file from disk and returns an enriched ASSParseResult container.

        Processes Sections:
            - [Script Info]: Script resolution (PlayResX, PlayResY).
            - [Pyxis Config]: Embedded project properties (FrameDuration, linked files).
            - [Aegisub Project Garbage]: Editor metadata (Audio/Video File, AR, position).
            - [V4+ Styles]: Typographic style formatting records.
            - [Events]: Dialogue and comment lines with inline metrics compatibility.

        Args:
            filepath (str): Absolute or relative filesystem path to the .ass file.

        Returns:
            ASSParseResult: Container tuple with styles, dialogues, resolution, and media info.
        """
        styles: Dict[str, StyleDict] = {}
        dialogues: List[DialogueItem] = []
        raw_res_x: Optional[int] = None
        raw_res_y: Optional[int] = None
        frame_dur: Optional[float] = None
        audio_file: str = ""
        video_file: str = ""
        script_file: str = ""
        video_ar: float = 0.0
        video_pos: int = 0
        dummy_info: Dict[str, Any] = {}
        is_dummy_video: bool = False
        is_dummy_audio: bool = False

        try:
            with open(filepath, 'r', encoding='utf-8-sig', errors='ignore') as f:
                lines = f.readlines()
            in_styles, in_events, in_info, in_config, in_garbage = False, False, False, False, False
            format_fields: List[str] = []
            current_metrics: Optional[MetricsDict] = None

            for line in lines:
                line = line.lstrip('\ufeff').strip()
                if line.startswith('[Script Info]'):
                    in_info, in_config, in_garbage, in_styles, in_events = True, False, False, False, False
                elif line.startswith('[Pyxis Config]'):
                    in_info, in_config, in_garbage, in_styles, in_events = False, True, False, False, False
                elif line.startswith('[Aegisub Project Garbage]'):
                    in_info, in_config, in_garbage, in_styles, in_events = False, False, True, False, False
                elif line.startswith('[V4+ Styles]'):
                    in_info, in_config, in_garbage, in_styles, in_events = False, False, False, True, False
                elif line.startswith('[Events]'):
                    in_info, in_config, in_garbage, in_styles, in_events = False, False, False, False, True
                elif in_info:
                    if line.startswith('PlayResX:'):
                        try:
                            raw_res_x = int(line.split(':', 1)[1].strip())
                        except Exception:
                            pass
                    elif line.startswith('PlayResY:'):
                        try:
                            raw_res_y = int(line.split(':', 1)[1].strip())
                        except Exception:
                            pass
                elif in_config:
                    if line.startswith('FrameDuration:'):
                        try:
                            frame_dur = float(line.split(':', 1)[1].strip())
                        except Exception:
                            pass
                    elif line.startswith('AudioFile:'):
                        audio_file = line.split(':', 1)[1].strip()
                    elif line.startswith('VideoFile:'):
                        video_file = line.split(':', 1)[1].strip()
                    elif line.startswith('ScriptFile:'):
                        script_file = line.split(':', 1)[1].strip()
                elif in_garbage:
                    if line.startswith('Audio File:') and not audio_file:
                        audio_file = line.split(':', 1)[1].strip()
                    elif line.startswith('Video File:') and not video_file:
                        video_file = line.split(':', 1)[1].strip()
                    elif line.startswith('Video AR Value:'):
                        try:
                            video_ar = float(line.split(':', 1)[1].strip())
                        except Exception:
                            pass
                    elif line.startswith('Video Position:'):
                        try:
                            video_pos = int(line.split(':', 1)[1].strip())
                        except Exception:
                            pass
                elif in_styles and line.startswith('Format:'):
                    format_fields = [f.strip() for f in line[7:].split(',')]
                elif in_styles and line.startswith('Style:'):
                    values = [v.strip() for v in line[6:].split(',')]
                    styles[values[0]] = {format_fields[i]: values[i] for i in range(len(values))}
                elif in_events:
                    if line.startswith('Comment:') and ('PyxisMetrics' in line or 'h=' in line):
                        try:
                            met_str = line.split(',PyxisMetrics,', 1)[-1] if ',PyxisMetrics,' in line else line.split(',', 9)[-1]
                            parts = _split_metric_string(met_str)
                            current_metrics = {
                                'h': float(parts.get('h', 35)),
                                'd': float(parts.get('d', 0)),
                                'e': float(parts.get('e', 0)),
                                'sel': int(parts.get('sel', 0)) == 1,
                                'rw': float(parts.get('rw', 0)),
                                'l': float(parts.get('l', 0)),
                                'c': float(parts.get('c', 0)),
                                'r': float(parts.get('r', 0)),
                                't': float(parts.get('t', 0)),
                                'm': float(parts.get('m', 0)),
                                'b': float(parts.get('b', 0)),
                                'syl_lefts': _csv_floats(parts.get('syl_lefts', '')),
                                'syl_centers': _csv_floats(parts.get('syl_centers', '')),
                                'syl_rights': _csv_floats(parts.get('syl_rights', '')),
                                'syl_widths': _csv_floats(parts.get('syl_widths', '')),
                                'syl_starts': [int(float(x)) for x in _csv_floats(parts.get('syl_starts', ''))],
                                'syl_ends': [int(float(x)) for x in _csv_floats(parts.get('syl_ends', ''))],
                                'w': _csv_floats(parts.get('w', '')),
                            }
                        except Exception:
                            pass
                    elif line.startswith('Dialogue:') or line.startswith('Comment:'):
                        prefix_len = 9 if line.startswith('Dialogue:') else 8
                        parts_fx = line[prefix_len:].split(',', 9)
                        line_effect = parts_fx[8].strip() if len(parts_fx) >= 9 else ""
                        if line_effect != "pyxis_fx":
                            dialogues.append({'raw': line, 'metrics': current_metrics})
                        current_metrics = None
        except Exception:
            pass

        if video_file:
            m_dummy = DUMMY_VIDEO_REGEX.match(video_file)
            if m_dummy:
                is_dummy_video = True
                fps_val = float(m_dummy.group(1))
                frames_val = int(m_dummy.group(2))
                w_val = int(m_dummy.group(3))
                h_val = int(m_dummy.group(4))
                r_val = int(m_dummy.group(5))
                g_val = int(m_dummy.group(6))
                b_val = int(m_dummy.group(7))
                pattern_val = m_dummy.group(8) or "c"
                color_hex = f"{r_val:02x}{g_val:02x}{b_val:02x}"
                dummy_info = {
                    "fps": fps_val,
                    "frames": frames_val,
                    "width": w_val,
                    "height": h_val,
                    "r": r_val,
                    "g": g_val,
                    "b": b_val,
                    "pattern": pattern_val,
                    "color_hex": color_hex
                }
                if frame_dur is None and fps_val > 0:
                    frame_dur = 1000.0 / fps_val
            elif "dummy" in video_file.lower():
                is_dummy_video = True

        if audio_file:
            if DUMMY_AUDIO_REGEX.match(audio_file) or "dummy" in audio_file.lower() or "silence" in audio_file.lower():
                is_dummy_audio = True

        final_res_x = raw_res_x if (raw_res_x is not None and raw_res_x > 0) else dummy_info.get("width", 1280)
        final_res_y = raw_res_y if (raw_res_y is not None and raw_res_y > 0) else dummy_info.get("height", 720)

        final_res_x = max(2, final_res_x - (final_res_x % 2))
        final_res_y = max(2, final_res_y - (final_res_y % 2))

        final_frame_dur = frame_dur if (frame_dur is not None and frame_dur > 0) else 41.708

        return ASSParseResult(
            styles, dialogues, final_res_x, final_res_y, final_frame_dur,
            audio_file, video_file, video_ar, video_pos, dummy_info,
            is_dummy_video, is_dummy_audio, script_file
        )


class KaraokeProcessor:
    """
    Typographical tokeniser and layout processor for ASS dialogue lines.

    Orchestrates the conversion of raw ASS Dialogue/Comment strings into fully measured
    and linked `PyxisLine` objects with child syllabic (`syls`), lexical (`words`),
    and character (`chars`) units.
    """
    def __init__(self, res_x: int = 1280, res_y: int = 720, frame_dur: float = 41.708) -> None:
        self.res_x: int = res_x
        self.res_y: int = res_y
        self.frame_dur: float = frame_dur

    def process_line(self, raw_line: str, style: StyleDict,
                     metrics: Optional[MetricsDict] = None) -> Optional[PyxisLine]:
        """
        Parses a raw ASS event line into a structured PyxisLine with full geometric and temporal layout.

        Execution Steps:
            1. Regex matching of ASS dialogue fields (layer, start, end, style, actor, margins, effect, text).
            2. Header pre-processing via `KaraskelEngine.preproc_line()` for layout bounding box and tags.
            3. Syllable segmentation:
               - If karaoke tags exist (`\\k`, `\\K`, `\\kf`, `\\ko`): extracts duration per syllable from `k_line.kara`.
               - If plain text: synthesises word-based syllable units with equal or proportional intervals.
            4. Character segmentation: allocates proportional character duration based on glyph advance width
               measured by `FontEngine.get_char_widths()`.
            5. Word aggregation: groups contiguous non-whitespace characters into `PyxisUnit` word objects.
            6. Topological linking: assigns contiguous visible indices (`ci`, `cn`) and binds `prev` and `next` proxies.

        Args:
            raw_line (str): Raw ASS Dialogue or Comment line string.
            style (StyleDict): Base typographic style dictionary corresponding to the line's style name.
            metrics (Optional[MetricsDict]): Precomputed metrics dictionary (e.g. from Aegisub PyxisMetrics).

        Returns:
            Optional[PyxisLine]: Fully structured dialogue line, or None if raw_line failed regex matching.
        """
        match = re.match(
            r'(?:Dialogue|Comment):\s*(\d+),([^,]+),([^,]+),([^,]*),([^,]*),(\-?\d+),(\-?\d+),(\-?\d+),([^,]*),(.*)',
            raw_line
        )
        if not match:
            return None

        groups = match.groups()
        if groups[8].strip() == "pyxis_fx":
            return None

        line = PyxisLine()
        raw_stripped = raw_line.strip()
        line.is_comment = raw_stripped.startswith("Comment:") or raw_stripped.startswith("Comment :")
        line.layer = int(groups[0])
        line.start_time, line.end_time = parse_time(groups[1]), parse_time(groups[2])
        line.duration = line.end_time - line.start_time
        line.style_name, line.actor = groups[3], groups[4]
        line.margin_l, line.margin_r, line.margin_v = int(groups[5]), int(groups[6]), int(groups[7])
        line.effect, line.raw_text = groups[8], groups[9]
        line.styleref = StyleRef(style)

        meta = KaraskelMeta(res_x=self.res_x, res_y=self.res_y)
        style_name = style.get('Name') or style.get('name') or line.style_name or "Default"
        styles_map = {style_name: style}

        k_line = KaraskelLine(
            raw_text=line.raw_text,
            start_time=line.start_time,
            end_time=line.end_time,
            style=style_name,
            margin_l=line.margin_l,
            margin_r=line.margin_r,
            margin_t=line.margin_v,
            margin_b=line.margin_v
        )

        KaraskelEngine.preproc_line(meta, styles_map, k_line)

        line.text_stripped = k_line.text_stripped
        line.width = k_line.width
        line.height = k_line.height
        line.descent = k_line.descent
        line.extlead = k_line.extlead
        line.left = k_line.left
        line.center = k_line.center
        line.right = k_line.right
        line.top = k_line.top
        line.middle = k_line.middle
        line.bottom = k_line.bottom
        line.x = k_line.x
        line.y = k_line.y
        line.mid_time = line.start_time + line.duration / 2.0
        line.has_style_override = k_line.has_style_override
        line.style_override = k_line.style_override
        line.has_pos = k_line.has_pos
        line.pos_x = k_line.pos_x
        line.pos_y = k_line.pos_y
        line.has_org = k_line.has_org
        line.org_x = k_line.org_x
        line.org_y = k_line.org_y
        line.has_move = k_line.has_move
        line.move_x1 = k_line.move_x1
        line.move_y1 = k_line.move_y1
        line.move_x2 = k_line.move_x2
        line.move_y2 = k_line.move_y2
        line.move_t1 = k_line.move_t1
        line.move_t2 = k_line.move_t2
        line.align_override = k_line.align_override

        if metrics and isinstance(metrics, dict):
            line.is_selected = bool(metrics.get('sel', False))
        else:
            line.is_selected = False

        has_karaoke = any(k_syl.duration > 0 or k_syl.kdur > 0 for k_syl in k_line.kara) or bool(re.search(r"\\[kK][fo]?\d+", line.raw_text))

        if has_karaoke:
            char_idx = 1
            visible_syl_idx = 1

            for k_syl in k_line.kara:
                syl = _make_unit()
                syl.line = line
                syl.style_override = k_syl.style_override
                if not k_syl.text_spacestripped:
                    syl.i = 0
                else:
                    syl.i = visible_syl_idx
                    visible_syl_idx += 1

                syl.text = k_syl.text
                syl.text_stripped = k_syl.text_stripped
                syl.text_spacestripped = k_syl.text_spacestripped
                syl.start_time = k_syl.start_time
                syl.end_time = k_syl.end_time
                syl.duration = k_syl.duration
                syl.mid_time = syl.start_time + (syl.duration / 2.0)
                syl.width = k_syl.width
                syl.height = k_syl.height
                syl.descent = k_line.descent
                syl.extlead = k_line.extlead
                syl.left = k_syl.left
                syl.center = k_syl.center
                syl.right = k_syl.right
                syl.top = k_syl.top
                syl.middle = k_syl.middle
                syl.bottom = k_syl.bottom
                syl.x = k_syl.x
                syl.y = k_syl.y
                syl.prespace = k_syl.prespace
                syl.postspace = k_syl.postspace
                syl.prespacewidth = k_syl.prespacewidth
                syl.postspacewidth = k_syl.postspacewidth
                syl.prespace_left = k_syl.prespace_left
                syl.postspace_left = k_syl.postspace_left
                syl.tag = k_syl.tag
                syl.inline_fx = k_syl.inline_fx
                syl.kdur = k_syl.kdur

                line.syls.append(syl)

                txt_strip = k_syl.text_stripped or ""
                syl_eff_style = syl.style_override if syl.style_override is not None else style
                char_metrics = FontEngine.get_char_layout_metrics(syl_eff_style, txt_strip)
                syl_cw_sum = sum(m["advance"] for m in char_metrics) if char_metrics else 1.0

                eff_sp = KaraskelEngine.get_effective_spacing(syl_eff_style, meta)
                n_pre = len(k_syl.prespace or "")
                n_text = len(k_syl.text_spacestripped or "")
                n_post = len(k_syl.postspace or "")

                current_x = k_syl.prespace_left if n_pre > 0 else k_syl.left
                current_t = 0

                for i_c, c in enumerate(txt_strip):
                    if i_c == n_pre and n_text > 0:
                        current_x = k_syl.left
                    elif i_c == (n_pre + n_text) and n_post > 0:
                        current_x = k_syl.postspace_left

                    m = char_metrics[i_c] if i_c < len(char_metrics) else {
                        "advance": syl.width / len(txt_strip) if txt_strip else 10.0,
                        "isolated_width": syl.width / len(txt_strip) if txt_strip else 10.0,
                        "is_ligature": False
                    }
                    adv = m["advance"]
                    w_iso = m["isolated_width"]

                    char_dur = int(syl.duration * (adv / syl_cw_sum)) if syl_cw_sum > 0 else 0
                    if i_c == len(txt_strip) - 1:
                        char_dur = max(0, syl.duration - current_t)

                    char = _make_unit()
                    char.syl = syl
                    char.line = line
                    char.style_override = syl.style_override
                    char.i = char_idx
                    char.text = c
                    char.text_stripped = c
                    char.duration = int(char_dur)
                    char.dur = int(char_dur)
                    char.start_time = int(current_t)
                    char.end_time = int(current_t + char_dur)
                    char.mid_time = char.start_time + (char.duration / 2.0)
                    char.width = w_iso
                    char.height = line.height
                    char.descent = line.descent
                    char.extlead = line.extlead
                    char.left = current_x
                    char.right = current_x + w_iso
                    char.center = current_x + (w_iso / 2.0)
                    char.top = line.top
                    char.middle = line.middle
                    char.bottom = line.bottom
                    char.x = char.center
                    char.y = char.middle

                    syl.chars.append(char)
                    line.chars.append(char)

                    current_x += (adv + eff_sp)
                    current_t += char_dur
                    char_idx += 1
        else:
            txt_strip = k_line.text_stripped or ""
            line_eff_style = line.style_override if line.style_override is not None else style
            char_metrics = FontEngine.get_char_layout_metrics(line_eff_style, txt_strip)
            eff_sp = KaraskelEngine.get_effective_spacing(line_eff_style, meta)
            all_chars = []
            cur_x = k_line.left
            for i_c, c in enumerate(txt_strip):
                m = char_metrics[i_c] if i_c < len(char_metrics) else {
                    "advance": 10.0,
                    "isolated_width": 10.0,
                    "is_ligature": False
                }
                adv = m["advance"]
                w_iso = m["isolated_width"]

                ch = _make_unit()
                ch.line = line
                ch.style_override = line.style_override
                ch.i = i_c + 1
                ch.text = c
                ch.text_stripped = c
                ch.width = w_iso
                ch.height = line.height
                ch.descent = line.descent
                ch.extlead = line.extlead
                ch.left = cur_x
                ch.right = cur_x + w_iso
                ch.center = cur_x + (w_iso / 2.0)
                ch.top = line.top
                ch.middle = line.middle
                ch.bottom = line.bottom
                ch.x = ch.center
                ch.y = ch.middle
                all_chars.append(ch)
                cur_x += (adv + eff_sp)

            word_char_groups = []
            curr_g = []
            for ch in all_chars:
                if ch.text_stripped.isspace():
                    if curr_g:
                        word_char_groups.append(curr_g)
                        curr_g = []
                else:
                    curr_g.append(ch)
            if curr_g:
                word_char_groups.append(curr_g)
            if not word_char_groups and all_chars:
                word_char_groups = [all_chars]

            N = len(word_char_groups)
            word_dur = (line.duration / N) if N > 0 else line.duration

            for i, w_chars in enumerate(word_char_groups, 1):
                w_st = int((i - 1) * word_dur)
                w_et = int(line.duration) if i == N else int(i * word_dur)
                w_d = max(0, w_et - w_st)

                syl = _make_unit()
                syl.line = line
                syl.style_override = line.style_override
                syl.i = i
                syl.n = N
                syl.ci = i
                syl.cn = N
                syl.start_time = w_st
                syl.end_time = w_et
                syl.duration = w_d
                syl.dur = w_d
                syl.kdur = w_d / 10.0
                syl.mid_time = w_st + (w_d / 2.0)
                syl.text = "".join(c.text for c in w_chars)
                syl.text_stripped = "".join(c.text_stripped for c in w_chars)
                syl.text_spacestripped = syl.text_stripped.strip()
                syl.height = line.height
                syl.descent = line.descent
                syl.extlead = line.extlead
                syl.left = w_chars[0].left if w_chars else k_line.left
                syl.right = w_chars[-1].right if w_chars else k_line.right
                syl.width = max(0.0, syl.right - syl.left) if w_chars else 0.0
                syl.center = syl.left + (syl.width / 2.0)
                syl.top = line.top
                syl.middle = line.middle
                syl.bottom = line.bottom
                syl.x = syl.center
                syl.y = syl.middle
                syl.prespace = ""
                syl.postspace = " " if i < N else ""
                syl.prespacewidth = 0.0
                syl.prespace_left = syl.left
                syl.postspacewidth = FontEngine.get_text_extents(line_eff_style, syl.postspace)[0] if syl.postspace else 0.0
                syl.postspace_left = syl.right
                syl.tag = "k"
                syl.inline_fx = ""
                syl.chars = w_chars

                syl_cw_sum = sum(c.width for c in w_chars) or 1.0
                curr_c_t = 0
                for idx_w, c in enumerate(w_chars):
                    c.syl = syl
                    c_dur = int(w_d * (c.width / syl_cw_sum)) if syl_cw_sum > 0 else 0
                    if idx_w == len(w_chars) - 1:
                        c_dur = max(0, w_d - curr_c_t)
                    c.start_time = int(curr_c_t)
                    c.duration = int(c_dur)
                    c.dur = int(c_dur)
                    c.end_time = int(curr_c_t + c_dur)
                    c.mid_time = c.start_time + (c.duration / 2.0)
                    curr_c_t += c_dur

                line.syls.append(syl)

            for ch in all_chars:
                if not getattr(ch, 'syl', None):
                    idx_in_all = all_chars.index(ch)
                    if idx_in_all > 0:
                        prev_c = all_chars[idx_in_all - 1]
                        ch.start_time = prev_c.end_time
                        ch.end_time = prev_c.end_time
                        ch.duration = 0
                        ch.dur = 0
                        ch.mid_time = prev_c.end_time
                        ch.syl = getattr(prev_c, 'syl', None)
                    else:
                        ch.start_time = 0
                        ch.end_time = 0
                        ch.duration = 0
                        ch.dur = 0
                        ch.mid_time = 0
                line.chars.append(ch)

        self._build_words_from_chars(line)

        for k_furi in k_line.furi:
            furi = _make_unit()
            furi.line = line
            furi.style_override = k_furi.style_override
            furi.i = k_furi.i
            furi.text = k_furi.text
            furi.text_stripped = k_furi.text_stripped
            furi.start_time = k_furi.start_time
            furi.end_time = k_furi.end_time
            furi.duration = k_furi.duration
            furi.width = k_furi.width
            furi.height = k_furi.height
            furi.left = k_furi.left
            furi.center = k_furi.center
            furi.right = k_furi.right
            furi.top = k_furi.top
            furi.middle = k_furi.middle
            furi.bottom = k_furi.bottom
            furi.x = k_furi.x
            furi.y = k_furi.y
            line.furi.append(furi)

        self._update_ns(line)
        return line

    def _build_words_from_chars(self, line: PyxisLine) -> None:
        """
        Constructs lexical word units (`line.words`) by aggregating non-whitespace character sequences.

        Args:
            line (PyxisLine): Active dialogue line containing populated `chars` collection.
        """
        word_idx: int = 1
        word_chars: List[PyxisUnit] = []
        for char in line.chars:
            if char.text_stripped.isspace():
                if word_chars:
                    self._create_word(line, word_chars, word_idx)
                    word_idx += 1
                    word_chars = []
            else:
                word_chars.append(char)

        if word_chars:
            self._create_word(line, word_chars, word_idx)

    def _create_word(self, line: PyxisLine, chars: List[PyxisUnit], index: int) -> PyxisUnit:
        """
        Creates and binds a single PyxisUnit word entity from a list of constituent character units.

        Calculates aggregated start/end timestamps, bounding box bounds (left, right, width),
        and updates parent/child references between characters, syllables, and words.

        Args:
            line (PyxisLine): Enclosing dialogue line.
            chars (List[PyxisUnit]): Contiguous character units forming the word.
            index (int): 1-based index of the word within the line.

        Returns:
            PyxisUnit: Newly constructed and bound word unit.
        """
        word = _make_unit()
        word.line, word.chars, word.i = line, chars, index
        word.style_override = getattr(chars[0], 'style_override', None) if chars else getattr(line, 'style_override', None)
        for c in chars:
            c.word = word
            syl_obj = getattr(c, 'syl', None)
            if isinstance(syl_obj, PyxisUnit) and not c.text_stripped.isspace():
                if not getattr(syl_obj, 'word', None):
                    syl_obj.word = word
        word.text = "".join(c.text for c in chars)
        word.text_stripped = "".join(c.text_stripped for c in chars)
        word.duration = sum(c.duration for c in chars)
        word.dur = word.duration
        if chars:
            c0 = chars[0]
            syl0 = getattr(c0, 'syl', None)
            syl0_st = getattr(syl0, 'start_time', 0) if isinstance(syl0, PyxisUnit) else 0
            word.start_time = syl0_st + c0.start_time
        else:
            word.start_time = 0
        word.end_time = word.start_time + word.duration
        word.mid_time = word.start_time + (word.duration / 2.0)
        word.left = chars[0].left if chars else line.left
        word.right = chars[-1].right if chars else line.right
        word.width = max(0.0, word.right - word.left)
        word.center = word.left + (word.width / 2.0)
        word.height = line.height
        word.top = chars[0].top if chars else line.top
        word.bottom = chars[0].bottom if chars else line.bottom
        word.middle = line.middle
        word.x = word.center
        word.y = word.middle
        word.descent, word.extlead = line.descent, line.extlead
        line.words.append(word)
        return word

    def _update_ns(self, line: PyxisLine) -> None:
        """
        Normalises total counts, sequential indices, and establishes bidirectional neighbour links.

        Iterates over `line.syls`, `line.words`, and `line.chars` to:
            - Calculate total count (`n`) and total visible count (`cn`).
            - Assign 1-based visible counter index (`ci`) skipping whitespace tokens (`is_blank`).
            - Bind intra-unit relative indices (`syl_i`, `word_i`).
            - Establish sequential neighbour navigation (`prev` and `next`).

        Args:
            line (PyxisLine): Dialogue line with populated child collections.
        """
        line.dur = line.duration
        line.x, line.y = line.center, line.middle

        vis_syls = [u for u in line.syls if str(getattr(u, 'text_stripped', '')).strip()]
        total_syls = len(vis_syls) if vis_syls else len(line.syls)

        syl_ci = 1
        for u in line.syls:
            u.is_blank = not bool(str(getattr(u, 'text_stripped', '')).strip())
            u.cn = total_syls
            if not u.is_blank:
                u.ci = syl_ci
                syl_ci += 1
            else:
                u.ci = max(1, syl_ci - 1)
            u.n = total_syls
            u.dur = u.duration
            u.x, u.y = u.center, u.middle

        vis_words = [w for w in line.words if str(getattr(w, 'text_stripped', '')).strip()]
        total_words = len(vis_words) if vis_words else len(line.words)

        word_ci = 1
        for u in line.words:
            u.is_blank = not bool(str(getattr(u, 'text_stripped', '')).strip())
            u.cn = total_words
            if not u.is_blank:
                u.ci = word_ci
                word_ci += 1
            else:
                u.ci = max(1, word_ci - 1)
            u.n = total_words
            u.dur = u.duration
            u.x, u.y = u.center, u.middle

        vis_chars = [c for c in line.chars if str(getattr(c, 'text_stripped', '')).strip()]
        total_chars = len(vis_chars) if vis_chars else len(line.chars)

        char_ci = 1
        for u in line.chars:
            u.is_blank = not bool(str(getattr(u, 'text_stripped', '')).strip())
            u.cn = total_chars
            if not u.is_blank:
                u.ci = char_ci
                char_ci += 1
            else:
                u.ci = max(1, char_ci - 1)
            u.n = total_chars
            u.dur = u.duration
            u.x, u.y = u.center, u.middle
            
            if u.syl and hasattr(u.syl, 'chars') and u in u.syl.chars:
                u.syl_i = u.syl.chars.index(u) + 1
            if u.word and hasattr(u.word, 'chars') and u in u.word.chars:
                u.word_i = u.word.chars.index(u) + 1

        for i, u in enumerate(line.syls):
            u.prev = line.syls[i - 1] if i > 0 else None
            u.next = line.syls[i + 1] if i + 1 < len(line.syls) else None

        for i, u in enumerate(line.words):
            u.prev = line.words[i - 1] if i > 0 else None
            u.next = line.words[i + 1] if i + 1 < len(line.words) else None

        for i, u in enumerate(line.chars):
            u.prev = line.chars[i - 1] if i > 0 else None
            u.next = line.chars[i + 1] if i + 1 < len(line.chars) else None