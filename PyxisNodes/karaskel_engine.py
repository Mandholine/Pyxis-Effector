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

"""Karaskel Auto4 engine ported to pure Python.

Faithfully reproduces the logic of karaskel-auto4.lua by Niels Martin Hansen and Rodrigo Braz Monteiro.
"""

import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any, Tuple
from font_engine import FontEngine


@dataclass
class KaraskelMeta:
    res_x: int = 1280
    res_y: int = 720
    video_x_correct_factor: float = 1.0


@dataclass
class KaraskelHighlight:
    start_time: int
    end_time: int
    duration: int


@dataclass
class KaraskelFurigana:
    i: int
    text: str = ""
    text_stripped: str = ""
    text_spacestripped: str = ""
    isbreak: bool = False
    spillback: bool = False
    width: float = 0.0
    height: float = 0.0
    prespacewidth: float = 0.0
    postspacewidth: float = 0.0
    left: float = 0.0
    center: float = 0.0
    right: float = 0.0
    top: float = 0.0
    middle: float = 0.0
    bottom: float = 0.0
    x: float = 0.0
    y: float = 0.0
    start_time: int = 0
    end_time: int = 0
    duration: int = 0
    kdur: float = 0.0
    tag: str = ""
    inline_fx: str = ""
    highlights: List[KaraskelHighlight] = field(default_factory=list)
    isfuri: bool = True
    syl: Any = None
    style: Any = None
    line: Any = None


@dataclass
class KaraskelSyllable:
    i: int
    text: str = ""
    text_stripped: str = ""
    text_spacestripped: str = ""
    prespace: str = ""
    postspace: str = ""
    start_time: int = 0
    end_time: int = 0
    duration: int = 0
    kdur: float = 0.0
    tag: str = ""
    inline_fx: str = ""
    width: float = 0.0
    height: float = 0.0
    prespacewidth: float = 0.0
    postspacewidth: float = 0.0
    left: float = 0.0
    center: float = 0.0
    right: float = 0.0
    top: float = 0.0
    middle: float = 0.0
    bottom: float = 0.0
    x: float = 0.0
    y: float = 0.0
    highlights: List[KaraskelHighlight] = field(default_factory=list)
    furi: List[KaraskelFurigana] = field(default_factory=list)
    style: Any = None
    line: Any = None


@dataclass
class KaraskelLine:
    raw_text: str = ""
    text_stripped: str = ""
    start_time: int = 0
    end_time: int = 0
    duration: int = 0
    style: str = "Default"
    styleref: Optional[Dict[str, Any]] = None
    furistyle: Optional[Dict[str, Any]] = None
    width: float = 0.0
    height: float = 0.0
    descent: float = 0.0
    extlead: float = 0.0
    margin_l: int = 0
    margin_r: int = 0
    margin_t: int = 0
    margin_b: int = 0
    margin_v: int = 0
    eff_margin_l: float = 0.0
    eff_margin_r: float = 0.0
    eff_margin_t: float = 0.0
    eff_margin_b: float = 0.0
    eff_margin_v: float = 0.0
    left: float = 0.0
    center: float = 0.0
    right: float = 0.0
    top: float = 0.0
    middle: float = 0.0
    bottom: float = 0.0
    x: float = 0.0
    y: float = 0.0
    halign: str = "center"
    valign: str = "bottom"
    kara: List[KaraskelSyllable] = field(default_factory=list)
    furi: List[KaraskelFurigana] = field(default_factory=list)


class KaraskelEngine:
    """Standalone pure Python Karaskel Auto4 engine."""

    furigana_scale: float = 0.5

    @classmethod
    def collect_head(cls, script_info: Dict[str, Any], styles: Dict[str, Any],
                     video_size: Optional[Tuple[int, int]] = None,
                     generate_furigana: bool = False) -> Tuple[KaraskelMeta, Dict[str, Any]]:
        meta = KaraskelMeta()
        meta.res_x = int(script_info.get("PlayResX") or script_info.get("playresx") or 1280)
        meta.res_y = int(script_info.get("PlayResY") or script_info.get("playresy") or 720)

        if video_size and video_size[0] > 0 and video_size[1] > 0:
            video_x, video_y = video_size
            meta.video_x_correct_factor = (video_y / video_x) / (meta.res_y / meta.res_x)

        styles_map = dict(styles)

        if generate_furigana:
            to_add = {}
            for name, st in list(styles_map.items()):
                if isinstance(name, str) and not name.endswith("-furigana"):
                    furi_name = name + "-furigana"
                    if furi_name not in styles_map:
                        fs = dict(st)
                        fs["name"] = furi_name
                        fs["fontsize"] = float(st.get("fontsize") or st.get("Fontsize") or 35) * cls.furigana_scale
                        fs["outline"] = float(st.get("outline") or st.get("Outline") or 2) * cls.furigana_scale
                        fs["shadow"] = float(st.get("shadow") or st.get("Shadow") or 1) * cls.furigana_scale
                        to_add[furi_name] = fs
            styles_map.update(to_add)

        return meta, styles_map

    @classmethod
    def preproc_line_text(cls, meta: KaraskelMeta, styles: Dict[str, Any], line: KaraskelLine) -> None:
        """Preprocesses line text extracting karaoke syllables, durations, and furigana."""
        line.kara = []
        line.furi = []
        line.text_stripped = ""
        line.duration = line.end_time - line.start_time

        raw_text = line.raw_text
        kara_tokens = cls._parse_karaoke_tokens(raw_text, line.start_time)

        cur_inline_fx = ""
        worksyl = KaraskelSyllable(i=0)
        worksyl.line = line

        for i, token in enumerate(kara_tokens):
            fx_match = re.search(r"\{.*\\-([^}\\]+)", token["text"])
            if fx_match:
                cur_inline_fx = fx_match.group(1)

            space_match = re.match(r"^([ \t]*)([\s\S]*?)([ \t]*)$", token["text_stripped"])
            if space_match:
                prespace, syltext, postspace = space_match.groups()
            else:
                prespace, syltext, postspace = "", token["text_stripped"], ""

            prefix = syltext[:1] if syltext else ""

            if prefix != "#" and prefix != "＃" and i > 0:
                line.kara.append(worksyl)
                worksyl = KaraskelSyllable(i=len(line.kara))
                worksyl.line = line

            hl = KaraskelHighlight(
                start_time=token["start_time"],
                end_time=token["end_time"],
                duration=token["duration"]
            )
            worksyl.highlights.append(hl)

            if "|" in syltext or "｜" in syltext:
                syltext = syltext.replace("｜", "|")
                if "|" in syltext:
                    maintext, furitext = syltext.split("|", 1)
                    syltext = maintext

                    furi = KaraskelFurigana(i=len(line.furi) + 1)
                    furi.syl = worksyl

                    furi_prefix = furitext[:1] if furitext else ""
                    if furi_prefix == "!" or furi_prefix == "！":
                        furi.isbreak = True
                        furi.spillback = False
                        furitext = furitext[1:]
                    elif furi_prefix == "<" or furi_prefix == "＜":
                        furi.isbreak = True
                        furi.spillback = True
                        furitext = furitext[1:]
                    else:
                        furi.isbreak = False
                        furi.spillback = False

                    furi.start_time = token["start_time"]
                    furi.end_time = token["end_time"]
                    furi.duration = token["duration"]
                    furi.kdur = token["duration"] / 10.0
                    furi.text = furitext
                    furi.text_stripped = furitext
                    furi.text_spacestripped = furitext
                    furi.line = line
                    furi.tag = token["tag"]
                    furi.inline_fx = cur_inline_fx
                    furi.prespace = ""
                    furi.postspace = ""
                    furi.highlights = [hl]
                    furi.isfuri = True

                    line.furi.append(furi)
                    worksyl.furi.append(furi)

            if not worksyl.text or (prefix != "#" and prefix != "＃"):
                line.text_stripped += prespace + syltext + postspace

                worksyl.text = token["text"]
                worksyl.duration = token["duration"]
                worksyl.kdur = token["duration"] / 10.0
                worksyl.start_time = token["start_time"]
                worksyl.end_time = token["end_time"]
                worksyl.tag = token["tag"]
                worksyl.line = line
                worksyl.i = len(line.kara)
                worksyl.text_stripped = prespace + syltext + postspace
                worksyl.inline_fx = cur_inline_fx
                worksyl.text_spacestripped = syltext
                worksyl.prespace = prespace
                worksyl.postspace = postspace
            else:
                worksyl.duration += token["duration"]
                worksyl.kdur += token["duration"] / 10.0
                worksyl.end_time = token["end_time"]

        line.kara.append(worksyl)

    @classmethod
    def _parse_karaoke_tokens(cls, raw_text: str, line_start_time: int) -> List[Dict[str, Any]]:
        """Parses ASS dialogue text into karaoke tokens equivalent to aegisub.parse_karaoke_data in C++.

        Accurately handles \\k, \\kf, \\ko, \\K, multi-tag brackets, lead-in text, and multi-highlights (#).
        """
        tokens = []
        parts = re.split(r"(\{.*?\})", raw_text)

        current_time = line_start_time
        cur_text = ""
        cur_tag = ""
        cur_dur_ms = 0
        has_k_tag = False

        for part in parts:
            if not part:
                continue

            if part.startswith("{") and part.endswith("}"):
                tag_content = part[1:-1]
                k_matches = list(re.finditer(r"\\([kK][fo]?)(\d+)", tag_content))
                if k_matches:
                    for km in k_matches:
                        if has_k_tag:
                            tokens.append({
                                "text": cur_text,
                                "text_stripped": re.sub(r"\{.*?\}", "", cur_text),
                                "duration": cur_dur_ms,
                                "start_time": current_time,
                                "end_time": current_time + cur_dur_ms,
                                "tag": cur_tag
                            })
                            current_time += cur_dur_ms
                            cur_text = ""
                        else:
                            tokens.append({
                                "text": cur_text,
                                "text_stripped": re.sub(r"\{.*?\}", "", cur_text),
                                "duration": 0,
                                "start_time": current_time,
                                "end_time": current_time,
                                "tag": ""
                            })
                            cur_text = ""

                        tag_name = km.group(1)
                        dur_cs = int(km.group(2))
                        cur_tag = tag_name
                        cur_dur_ms = dur_cs * 10
                        has_k_tag = True
                    cur_text += part
                else:
                    cur_text += part
            else:
                cur_text += part

        if cur_text or not tokens:
            tokens.append({
                "text": cur_text,
                "text_stripped": re.sub(r"\{.*?\}", "", cur_text),
                "duration": cur_dur_ms if has_k_tag else 0,
                "start_time": current_time,
                "end_time": current_time + (cur_dur_ms if has_k_tag else 0),
                "tag": cur_tag
            })

        return tokens

    @classmethod
    def preproc_line_size(cls, meta: KaraskelMeta, styles: Dict[str, Any], line: KaraskelLine) -> None:
        """Pre-calcula las dimensiones de línea, sílabas y furigana usando FontEngine."""
        if not line.kara:
            cls.preproc_line_text(meta, styles, line)

        if line.style in styles:
            line.styleref = styles[line.style]
        else:
            line.styleref = styles.get("Default") or (list(styles.values())[0] if styles else {})

        line.width, line.height, line.descent, line.extlead = FontEngine.get_text_extents(line.styleref, line.text_stripped)
        line.width *= meta.video_x_correct_factor

        for syl in line.kara:
            syl.style = line.styleref
            syl.width, syl.height = FontEngine.get_text_extents(syl.style, syl.text_spacestripped)[:2]
            syl.width *= meta.video_x_correct_factor
            syl.prespacewidth = FontEngine.get_text_extents(syl.style, syl.prespace)[0] * meta.video_x_correct_factor
            syl.postspacewidth = FontEngine.get_text_extents(syl.style, syl.postspace)[0] * meta.video_x_correct_factor

        furi_style_name = line.style + "-furigana"
        if furi_style_name in styles:
            line.furistyle = styles[furi_style_name]
        else:
            line.furistyle = None

        if line.furistyle:
            for furi in line.furi:
                furi.style = line.furistyle
                furi.width, furi.height = FontEngine.get_text_extents(furi.style, furi.text)[:2]
                furi.width *= meta.video_x_correct_factor
                furi.prespacewidth = 0.0
                furi.postspacewidth = 0.0

    @classmethod
    def preproc_line_pos(cls, meta: KaraskelMeta, styles: Dict[str, Any], line: KaraskelLine) -> None:
        """Calcula el posicionamiento y maquetación de la línea, sílabas y furigana."""
        if not line.styleref:
            cls.preproc_line_size(meta, styles, line)

        if line.furistyle:
            cls.do_furigana_layout(meta, styles, line)
        else:
            cls.do_basic_layout(meta, styles, line)

        styleref = line.styleref or {}
        line.margin_v = line.margin_t
        line.eff_margin_l = line.margin_l if line.margin_l > 0 else int(styleref.get("MarginL") or styleref.get("margin_l") or 0)
        line.eff_margin_r = line.margin_r if line.margin_r > 0 else int(styleref.get("MarginR") or styleref.get("margin_r") or 0)
        line.eff_margin_t = line.margin_t if line.margin_t > 0 else int(styleref.get("MarginV") or styleref.get("MarginT") or styleref.get("margin_t") or 0)
        line.eff_margin_b = line.margin_b if line.margin_b > 0 else int(styleref.get("MarginV") or styleref.get("MarginB") or styleref.get("margin_b") or 0)
        line.eff_margin_v = line.eff_margin_t

        align = int(styleref.get("Alignment") or styleref.get("align") or 2)

        if align in (1, 4, 7):
            line.left = float(line.eff_margin_l)
            line.center = line.left + line.width / 2.0
            line.right = line.left + line.width
            line.x = line.left
            line.halign = "left"
        elif align in (2, 5, 8):
            line.left = (meta.res_x - line.eff_margin_l - line.eff_margin_r - line.width) / 2.0 + line.eff_margin_l
            line.center = line.left + line.width / 2.0
            line.right = line.left + line.width
            line.x = line.center
            line.halign = "center"
        elif align in (3, 6, 9):
            line.left = meta.res_x - line.eff_margin_r - line.width
            line.center = line.left + line.width / 2.0
            line.right = line.left + line.width
            line.x = line.right
            line.halign = "right"

        if 1 <= align <= 3:
            line.bottom = meta.res_y - float(line.eff_margin_b)
            line.middle = line.bottom - line.height / 2.0
            line.top = line.bottom - line.height
            line.y = line.bottom
            line.valign = "bottom"
        elif 4 <= align <= 6:
            line.top = (meta.res_y - line.eff_margin_t - line.eff_margin_b - line.height) / 2.0 + line.eff_margin_t
            line.middle = line.top + line.height / 2.0
            line.bottom = line.top + line.height
            line.y = line.middle
            line.valign = "middle"
        elif 7 <= align <= 9:
            line.top = float(line.eff_margin_t)
            line.middle = line.top + line.height / 2.0
            line.bottom = line.top + line.height
            line.y = line.top
            line.valign = "top"

        for syl in line.kara:
            syl.left += line.left
            syl.center += line.left
            syl.right += line.left
            syl.top = line.top
            syl.middle = line.middle
            syl.bottom = line.bottom
            syl.x = syl.center
            syl.y = syl.middle

        for furi in line.furi:
            furi.left += line.left
            furi.center += line.left
            furi.right += line.left
            furi.bottom = line.top
            furi.top = line.top - furi.height
            furi.middle = furi.top + furi.height / 2.0
            furi.x = furi.center
            furi.y = furi.top + furi.height / 2.0

    @classmethod
    def do_basic_layout(cls, meta: KaraskelMeta, styles: Dict[str, Any], line: KaraskelLine) -> None:
        """Maquetación básica de sílabas sin furigana."""
        curx = 0.0
        for syl in line.kara:
            syl.left = curx + syl.prespacewidth
            syl.center = syl.left + syl.width / 2.0
            syl.right = syl.left + syl.width
            curx = curx + syl.prespacewidth + syl.width + syl.postspacewidth

    @classmethod
    def do_furigana_layout(cls, meta: KaraskelMeta, styles: Dict[str, Any], line: KaraskelLine) -> None:
        """Algoritmo avanzado de maquetación de furigana por grupos de diseño (lgroups)."""
        lgroups = []
        lgsentinel = {
            "basewidth": 0.0,
            "furiwidth": 0.0,
            "syls": [],
            "furi": [],
            "spillback": False,
            "left": 0.0,
            "right": 0.0,
            "rightspill": 0.0,
            "leftspill": 0.0
        }
        lgroups.append(dict(lgsentinel))

        last_had_furi = False
        lg = {
            "basewidth": 0.0,
            "furiwidth": 0.0,
            "syls": [],
            "furi": [],
            "spillback": False,
            "left": 0.0,
            "right": 0.0,
            "rightspill": 0.0,
            "leftspill": 0.0
        }

        for syl in line.kara:
            has_furi = len(syl.furi) > 0
            is_break = has_furi and syl.furi[0].isbreak

            if (not has_furi or is_break or not last_had_furi) and lg["basewidth"] > 0:
                lgroups.append(lg)
                lg = {
                    "basewidth": 0.0,
                    "furiwidth": 0.0,
                    "syls": [],
                    "furi": [],
                    "spillback": False,
                    "left": 0.0,
                    "right": 0.0,
                    "rightspill": 0.0,
                    "leftspill": 0.0
                }
                last_had_furi = False

            lg["basewidth"] += syl.prespacewidth + syl.width + syl.postspacewidth
            lg["syls"].append(syl)

            for furi in syl.furi:
                lg["furiwidth"] += furi.width
                lg["spillback"] = lg["spillback"] or furi.spillback
                lg["furi"].append(furi)
                last_had_furi = True

        lgroups.append(lg)
        lgroups.append(dict(lgsentinel))

        curx = 0.0
        for i in range(1, len(lgroups) - 1):
            lg = lgroups[i]
            prev = lgroups[i - 1]

            if lg["furiwidth"] == 0:
                lg["left"] = curx
                lg["right"] = lg["left"] + lg["basewidth"]
                if prev.get("rightspill", 0) > 0:
                    lg["leftspill"] = 0.0
                    lg["rightspill"] = prev["rightspill"] - lg["basewidth"]
                    prev["rightspill"] = 0.0
                curx = curx + lg["basewidth"]

            elif lg["furiwidth"] <= lg["basewidth"]:
                if prev.get("rightspill", 0) > 0:
                    curx = curx + prev["rightspill"]
                    prev["rightspill"] = 0.0
                lg["left"] = curx
                lg["right"] = lg["left"] + lg["basewidth"]
                curx = curx + lg["basewidth"]
                lg["leftspill"] = (lg["furiwidth"] - lg["basewidth"]) / 2.0
                lg["rightspill"] = lg["leftspill"]

            else:
                if prev.get("rightspill", 0) > 0:
                    curx = curx + prev["rightspill"]
                    prev["rightspill"] = 0.0

                if lg["spillback"]:
                    lg["leftspill"] = (lg["furiwidth"] - lg["basewidth"]) / 2.0
                    lg["rightspill"] = lg["leftspill"]
                    if prev.get("rightspill") is not None:
                        lg["left"] = curx + lg["leftspill"]
                    else:
                        lg["left"] = curx
                else:
                    lg["leftspill"] = 0.0
                    lg["rightspill"] = lg["furiwidth"] - lg["basewidth"]
                    lg["left"] = curx

                lg["right"] = lg["left"] + lg["basewidth"]
                curx = lg["right"]

        for lg in lgroups:
            if not lg["syls"]:
                continue
            curx = lg["left"]
            for syl in lg["syls"]:
                syl.left = curx + syl.prespacewidth
                syl.center = syl.left + syl.width / 2.0
                syl.right = syl.left + syl.width
                curx = syl.right + syl.postspacewidth

            if curx > line.width:
                line.width = curx

            if lg["furiwidth"] < lg["basewidth"] or lg["spillback"]:
                curx = lg["left"] + (lg["basewidth"] - lg["furiwidth"]) / 2.0
            else:
                curx = lg["left"]

            for furi in lg["furi"]:
                furi.left = curx
                furi.center = furi.left + furi.width / 2.0
                furi.right = furi.left + furi.width
                curx = furi.right

    @classmethod
    def preproc_line(cls, meta: KaraskelMeta, styles: Dict[str, Any], line: KaraskelLine) -> None:
        """Main entry point to preprocess the complete line."""
        cls.preproc_line_pos(meta, styles, line)
