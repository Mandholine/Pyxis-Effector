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


_STYLE_OVERRIDE_CHECK_RE = re.compile(r'\\(?!k\d|K\d|kf\d|ko\d|#)[a-zA-Z1-4]')


@dataclass
class ActiveStyleState:
    """Stateful snapshot of active ASS style and kinematic overrides."""
    fontname: str = "Arial"
    fontsize: float = 40.0
    bold: bool = False
    italic: bool = False
    underline: bool = False
    strikeout: bool = False
    scale_x: float = 100.0
    scale_y: float = 100.0
    spacing: float = 0.0
    outline: float = 2.0
    shadow: float = 0.0
    color1: str = "&H00FFFFFF&"
    color2: str = "&H000000FF&"
    color3: str = "&H00000000&"
    color4: str = "&H00000000&"
    alpha1: str = "&H00&"
    alpha2: str = "&H00&"
    alpha3: str = "&H00&"
    alpha4: str = "&H00&"
    frz: float = 0.0
    frx: float = 0.0
    fry: float = 0.0
    fax: float = 0.0
    fay: float = 0.0
    align: int = 2
    has_align: bool = False
    has_pos: bool = False
    pos_x: float = 0.0
    pos_y: float = 0.0
    has_org: bool = False
    org_x: float = 0.0
    org_y: float = 0.0
    has_move: bool = False
    move_x1: float = 0.0
    move_y1: float = 0.0
    move_x2: float = 0.0
    move_y2: float = 0.0
    move_t1: Optional[int] = None
    move_t2: Optional[int] = None

    @classmethod
    def from_style(cls, base_style: Dict[str, Any]) -> 'ActiveStyleState':
        st = cls()
        st.reset_to(base_style)
        return st

    def reset_to(self, s: Dict[str, Any]) -> None:
        if not s:
            return
        self.fontname = str(s.get('Fontname') or s.get('fontname') or 'Arial')
        try:
            self.fontsize = float(s.get('Fontsize', s.get('fontsize', 40.0)))
        except Exception:
            self.fontsize = 40.0
        b_val = s.get('Bold', s.get('bold', False))
        self.bold = str(b_val).strip() in ['1', '-1', 'true', 'True'] if not isinstance(b_val, bool) else b_val
        i_val = s.get('Italic', s.get('italic', False))
        self.italic = str(i_val).strip() in ['1', '-1', 'true', 'True'] if not isinstance(i_val, bool) else i_val
        u_val = s.get('Underline', s.get('underline', False))
        self.underline = str(u_val).strip() in ['1', '-1', 'true', 'True'] if not isinstance(u_val, bool) else u_val
        s_val = s.get('StrikeOut', s.get('strikeout', False))
        self.strikeout = str(s_val).strip() in ['1', '-1', 'true', 'True'] if not isinstance(s_val, bool) else s_val
        try:
            self.scale_x = float(s.get('ScaleX', s.get('scale_x', 100.0)))
        except Exception:
            self.scale_x = 100.0
        try:
            self.scale_y = float(s.get('ScaleY', s.get('scale_y', 100.0)))
        except Exception:
            self.scale_y = 100.0
        try:
            self.spacing = float(s.get('Spacing', s.get('spacing', 0.0)))
        except Exception:
            self.spacing = 0.0
        try:
            self.outline = float(s.get('Outline', s.get('outline', 2.0)))
        except Exception:
            self.outline = 2.0
        try:
            self.shadow = float(s.get('Shadow', s.get('shadow', 0.0)))
        except Exception:
            self.shadow = 0.0
        self.color1 = str(s.get('PrimaryColour', s.get('color1', '&H00FFFFFF&')))
        self.color2 = str(s.get('SecondaryColour', s.get('color2', '&H000000FF&')))
        self.color3 = str(s.get('OutlineColour', s.get('color3', '&H00000000&')))
        self.color4 = str(s.get('BackColour', s.get('color4', '&H00000000&')))
        self.alpha1 = str(s.get('alpha1', '&H00&'))
        self.alpha2 = str(s.get('alpha2', '&H00&'))
        self.alpha3 = str(s.get('alpha3', '&H00&'))
        self.alpha4 = str(s.get('alpha4', '&H00&'))
        try:
            self.frz = float(s.get('Angle', s.get('angle', 0.0)))
        except Exception:
            self.frz = 0.0
        if not self.has_align:
            try:
                self.align = int(s.get('Alignment', s.get('alignment', s.get('align', 2))))
            except Exception:
                self.align = 2

    def copy(self) -> 'ActiveStyleState':
        c = ActiveStyleState.__new__(ActiveStyleState)
        c.fontname = self.fontname
        c.fontsize = self.fontsize
        c.bold = self.bold
        c.italic = self.italic
        c.underline = self.underline
        c.strikeout = self.strikeout
        c.scale_x = self.scale_x
        c.scale_y = self.scale_y
        c.spacing = self.spacing
        c.outline = self.outline
        c.shadow = self.shadow
        c.color1 = self.color1
        c.color2 = self.color2
        c.color3 = self.color3
        c.color4 = self.color4
        c.alpha1 = self.alpha1
        c.alpha2 = self.alpha2
        c.alpha3 = self.alpha3
        c.alpha4 = self.alpha4
        c.frz = self.frz
        c.frx = self.frx
        c.fry = self.fry
        c.fax = self.fax
        c.fay = self.fay
        c.align = self.align
        c.has_align = self.has_align
        c.has_pos = self.has_pos
        c.pos_x = self.pos_x
        c.pos_y = self.pos_y
        c.has_org = self.has_org
        c.org_x = self.org_x
        c.org_y = self.org_y
        c.has_move = self.has_move
        c.move_x1 = self.move_x1
        c.move_y1 = self.move_y1
        c.move_x2 = self.move_x2
        c.move_y2 = self.move_y2
        c.move_t1 = self.move_t1
        c.move_t2 = self.move_t2
        return c

    def __contains__(self, key: str) -> bool:
        return self.get(key) is not None

    def get(self, key: str, default: Any = None) -> Any:
        clean = key.lower()
        if clean in ('fontname', 'fn'): return self.fontname
        if clean in ('fontsize', 'fs'): return self.fontsize
        if clean == 'bold': return self.bold
        if clean == 'italic': return self.italic
        if clean == 'underline': return self.underline
        if clean == 'strikeout': return self.strikeout
        if clean in ('scale_x', 'scalex', 'fscx'): return self.scale_x
        if clean in ('scale_y', 'scaley', 'fscy'): return self.scale_y
        if clean in ('spacing', 'fsp'): return self.spacing
        if clean in ('outline', 'bord'): return self.outline
        if clean in ('shadow', 'shad'): return self.shadow
        if clean in ('primarycolour', 'color1', '1c', 'c'): return self.color1
        if clean in ('secondarycolour', 'color2', '2c'): return self.color2
        if clean in ('outlinecolour', 'color3', '3c'): return self.color3
        if clean in ('backcolour', 'color4', '4c'): return self.color4
        if clean == 'alpha1': return self.alpha1
        if clean == 'alpha2': return self.alpha2
        if clean == 'alpha3': return self.alpha3
        if clean == 'alpha4': return self.alpha4
        if clean in ('alignment', 'align', 'an'): return self.align
        if clean in ('angle', 'frz', 'fr'): return self.frz
        if hasattr(self, key):
            return getattr(self, key)
        return default

    def __getitem__(self, key: str) -> Any:
        val = self.get(key)
        if val is None and not hasattr(self, key):
            raise KeyError(key)
        return val


def parse_style_override_block(
    tag_content: str,
    state: ActiveStyleState,
    styles_map: Dict[str, Any],
    base_style: Dict[str, Any]
) -> None:
    """Parses ASS override tags sequentially within a {...} block, updating active style state."""
    # \r[style_name]
    for r_m in re.finditer(r'\\r([^\\}]*)', tag_content):
        r_arg = r_m.group(1).strip()
        if r_arg and r_arg in styles_map:
            state.reset_to(styles_map[r_arg])
        else:
            state.reset_to(base_style)

    # \pos(x, y)
    pos_m = re.search(r'\\pos\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)', tag_content)
    if pos_m:
        state.has_pos = True
        state.pos_x = float(pos_m.group(1))
        state.pos_y = float(pos_m.group(2))

    # \move(x1, y1, x2, y2[, t1, t2])
    move_m = re.search(r'\\move\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)(?:\s*,\s*(\d+)\s*,\s*(\d+))?\s*\)', tag_content)
    if move_m:
        state.has_move = True
        state.move_x1 = float(move_m.group(1))
        state.move_y1 = float(move_m.group(2))
        state.move_x2 = float(move_m.group(3))
        state.move_y2 = float(move_m.group(4))
        state.move_t1 = int(move_m.group(5)) if move_m.group(5) is not None else None
        state.move_t2 = int(move_m.group(6)) if move_m.group(6) is not None else None

    # \org(x, y)
    org_m = re.search(r'\\org\(\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*\)', tag_content)
    if org_m:
        state.has_org = True
        state.org_x = float(org_m.group(1))
        state.org_y = float(org_m.group(2))

    # \an1..9
    an_m = re.search(r'\\an([1-9])', tag_content)
    if an_m:
        state.align = int(an_m.group(1))
        state.has_align = True

    # \fn...
    fn_m = re.search(r'\\fn([^\\}]+)', tag_content)
    if fn_m:
        state.fontname = fn_m.group(1).strip()

    # \fs...
    fs_m = re.search(r'\\fs(\d+(?:\.\d+)?)', tag_content)
    if fs_m:
        try: state.fontsize = float(fs_m.group(1))
        except Exception: pass

    # \fscx...
    fscx_m = re.search(r'\\fscx(\d+(?:\.\d+)?)', tag_content)
    if fscx_m:
        try: state.scale_x = float(fscx_m.group(1))
        except Exception: pass

    # \fscy...
    fscy_m = re.search(r'\\fscy(\d+(?:\.\d+)?)', tag_content)
    if fscy_m:
        try: state.scale_y = float(fscy_m.group(1))
        except Exception: pass

    # \fsp...
    fsp_m = re.search(r'\\fsp(-?\d+(?:\.\d+)?)', tag_content)
    if fsp_m:
        try: state.spacing = float(fsp_m.group(1))
        except Exception: pass

    # \b...
    b_m = re.search(r'\\b([01]|\d{3})', tag_content)
    if b_m:
        bv = b_m.group(1)
        state.bold = (bv == '1' or (bv.isdigit() and int(bv) >= 600))

    # \i...
    i_m = re.search(r'\\i([01])', tag_content)
    if i_m:
        state.italic = (i_m.group(1) == '1')

    # \u...
    u_m = re.search(r'\\u([01])', tag_content)
    if u_m:
        state.underline = (u_m.group(1) == '1')

    # \s...
    s_m = re.search(r'\\s([01])', tag_content)
    if s_m:
        state.strikeout = (s_m.group(1) == '1')

    # \bord...
    bord_m = re.search(r'\\bord(\d+(?:\.\d+)?)', tag_content)
    if bord_m:
        try: state.outline = float(bord_m.group(1))
        except Exception: pass

    # \shad...
    shad_m = re.search(r'\\shad(\d+(?:\.\d+)?)', tag_content)
    if shad_m:
        try: state.shadow = float(shad_m.group(1))
        except Exception: pass

    # Colors: \1c / \c, \2c, \3c, \4c
    c1_m = re.search(r'\\(?:1c|c)(&H[0-9a-fA-F]{6,8}&)', tag_content)
    if c1_m:
        state.color1 = c1_m.group(1).upper()
    c2_m = re.search(r'\\2c(&H[0-9a-fA-F]{6,8}&)', tag_content)
    if c2_m:
        state.color2 = c2_m.group(1).upper()
    c3_m = re.search(r'\\3c(&H[0-9a-fA-F]{6,8}&)', tag_content)
    if c3_m:
        state.color3 = c3_m.group(1).upper()
    c4_m = re.search(r'\\4c(&H[0-9a-fA-F]{6,8}&)', tag_content)
    if c4_m:
        state.color4 = c4_m.group(1).upper()

    # Alpha: \alpha, \1a, \2a, \3a, \4a
    alpha_m = re.search(r'\\alpha(&H[0-9a-fA-F]{2}&)', tag_content)
    if alpha_m:
        av = alpha_m.group(1).upper()
        state.alpha1 = av
        state.alpha2 = av
        state.alpha3 = av
        state.alpha4 = av
    for idx_a in range(1, 5):
        a_m = re.search(rf'\\{idx_a}a(&H[0-9a-fA-F]{{2}}&)', tag_content)
        if a_m:
            setattr(state, f'alpha{idx_a}', a_m.group(1).upper())

    # Rotations: \frz / \fr, \frx, \fry
    frz_m = re.search(r'\\fr(?:z)?(-?\d+(?:\.\d+)?)', tag_content)
    if frz_m:
        try: state.frz = float(frz_m.group(1))
        except Exception: pass
    frx_m = re.search(r'\\frx(-?\d+(?:\.\d+)?)', tag_content)
    if frx_m:
        try: state.frx = float(frx_m.group(1))
        except Exception: pass
    fry_m = re.search(r'\\fry(-?\d+(?:\.\d+)?)', tag_content)
    if fry_m:
        try: state.fry = float(fry_m.group(1))
        except Exception: pass

    # Shearing: \fax, \fay
    fax_m = re.search(r'\\fax(-?\d+(?:\.\d+)?)', tag_content)
    if fax_m:
        try: state.fax = float(fax_m.group(1))
        except Exception: pass
    fay_m = re.search(r'\\fay(-?\d+(?:\.\d+)?)', tag_content)
    if fay_m:
        try: state.fay = float(fay_m.group(1))
        except Exception: pass


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
    style_override: Optional[ActiveStyleState] = None


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
    prespace_left: float = 0.0
    postspace_left: float = 0.0
    highlights: List[KaraskelHighlight] = field(default_factory=list)
    furi: List[KaraskelFurigana] = field(default_factory=list)
    style: Any = None
    line: Any = None
    style_override: Optional[ActiveStyleState] = None


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
    has_style_override: bool = False
    has_pos: bool = False
    pos_x: float = 0.0
    pos_y: float = 0.0
    has_org: bool = False
    org_x: float = 0.0
    org_y: float = 0.0
    has_move: bool = False
    move_x1: float = 0.0
    move_y1: float = 0.0
    move_x2: float = 0.0
    move_y2: float = 0.0
    move_t1: Optional[int] = None
    move_t2: Optional[int] = None
    align_override: Optional[int] = None
    style_override: Optional[ActiveStyleState] = None


class KaraskelEngine:
    """Standalone pure Python Karaskel Auto4 engine."""

    furigana_scale: float = 0.5

    @staticmethod
    def has_style_override_tags(raw_text: str) -> bool:
        """Microsecond fast-check determining if ASS text contains non-karaoke override tags."""
        if not raw_text or "{" not in raw_text or "\\" not in raw_text:
            return False
        return bool(_STYLE_OVERRIDE_CHECK_RE.search(raw_text))

    @staticmethod
    def get_effective_spacing(style: Any, meta: Optional[KaraskelMeta] = None) -> float:
        """Calculates effective horizontal spacing per character interval in ASS PlayRes coordinates."""
        if style is None:
            return 0.0
        if hasattr(style, "spacing"):
            sp = float(getattr(style, "spacing", 0.0) or 0.0)
            sc = float(getattr(style, "scale_x", 100.0) or 100.0)
        elif isinstance(style, dict):
            sp = float(style.get("spacing") or style.get("Spacing") or 0.0)
            sc = float(style.get("scale_x") or style.get("ScaleX") or 100.0)
        else:
            return 0.0
        video_factor = getattr(meta, "video_x_correct_factor", 1.0) if meta else 1.0
        return sp * (sc / 100.0) * video_factor

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
        has_overrides = cls.has_style_override_tags(raw_text)
        line.has_style_override = has_overrides

        base_style = {}
        active_state = None
        if has_overrides:
            base_style = styles.get(line.style) or styles.get("Default") or (list(styles.values())[0] if styles else {})
            active_state = ActiveStyleState.from_style(base_style)

        kara_tokens = cls._parse_karaoke_tokens(raw_text, 0)

        cur_inline_fx = ""
        worksyl = KaraskelSyllable(i=0)
        worksyl.line = line

        for i, token in enumerate(kara_tokens):
            if has_overrides and active_state is not None:
                for block in re.findall(r"\{([^}]+)\}", token["text"]):
                    parse_style_override_block(block, active_state, styles, base_style)

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
                    if has_overrides and active_state is not None:
                        furi.style_override = active_state.copy()

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
                if has_overrides and active_state is not None:
                    worksyl.style_override = active_state.copy()
            else:
                worksyl.duration += token["duration"]
                worksyl.kdur += token["duration"] / 10.0
                worksyl.end_time = token["end_time"]
                if has_overrides and active_state is not None:
                    worksyl.style_override = active_state.copy()

        line.kara.append(worksyl)

        if has_overrides and active_state is not None:
            line.style_override = active_state.copy()
            line.has_pos = active_state.has_pos
            line.pos_x = active_state.pos_x
            line.pos_y = active_state.pos_y
            line.has_org = active_state.has_org
            line.org_x = active_state.org_x
            line.org_y = active_state.org_y
            line.has_move = active_state.has_move
            line.move_x1 = active_state.move_x1
            line.move_y1 = active_state.move_y1
            line.move_x2 = active_state.move_x2
            line.move_y2 = active_state.move_y2
            line.move_t1 = active_state.move_t1
            line.move_t2 = active_state.move_t2
            if active_state.has_align:
                line.align_override = active_state.align

    @classmethod
    def _parse_karaoke_tokens(cls, raw_text: str, line_start_time: int = 0) -> List[Dict[str, Any]]:
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

        eff_line_style = line.style_override if line.style_override is not None else line.styleref
        line.width, line.height, line.descent, line.extlead = FontEngine.get_text_extents(eff_line_style, line.text_stripped)
        line.width *= meta.video_x_correct_factor

        for syl in line.kara:
            syl_style = syl.style_override if syl.style_override is not None else line.styleref
            syl.style = syl_style
            syl.width, syl.height = FontEngine.get_text_extents(syl_style, syl.text_spacestripped)[:2]
            syl.width *= meta.video_x_correct_factor
            syl.prespacewidth = FontEngine.get_text_extents(syl_style, syl.prespace)[0] * meta.video_x_correct_factor
            syl.postspacewidth = FontEngine.get_text_extents(syl_style, syl.postspace)[0] * meta.video_x_correct_factor

        furi_style_name = line.style + "-furigana"
        if furi_style_name in styles:
            line.furistyle = styles[furi_style_name]
        else:
            line.furistyle = None

        if line.furistyle:
            for furi in line.furi:
                furi_style = furi.style_override if furi.style_override is not None else line.furistyle
                furi.style = furi_style
                furi.width, furi.height = FontEngine.get_text_extents(furi_style, furi.text)[:2]
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

        align = line.align_override if line.align_override is not None else int(styleref.get("Alignment") or styleref.get("align") or 2)

        if line.has_pos:
            line.x = line.pos_x
            line.y = line.pos_y

            if align in (1, 4, 7):
                line.left = line.x
                line.center = line.left + line.width / 2.0
                line.right = line.left + line.width
                line.halign = "left"
            elif align in (2, 5, 8):
                line.left = line.x - line.width / 2.0
                line.center = line.x
                line.right = line.left + line.width
                line.halign = "center"
            elif align in (3, 6, 9):
                line.right = line.x
                line.left = line.right - line.width
                line.center = line.left + line.width / 2.0
                line.halign = "right"

            if 1 <= align <= 3:
                line.bottom = line.y
                line.middle = line.bottom - line.height / 2.0
                line.top = line.bottom - line.height
                line.valign = "bottom"
            elif 4 <= align <= 6:
                line.top = line.y - line.height / 2.0
                line.middle = line.y
                line.bottom = line.top + line.height
                line.valign = "middle"
            elif 7 <= align <= 9:
                line.top = line.y
                line.middle = line.top + line.height / 2.0
                line.bottom = line.top + line.height
                line.valign = "top"
        else:
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
            if syl.style_override is not None and syl.style_override.has_pos:
                syl_align = syl.style_override.align
                syl.x = syl.style_override.pos_x
                syl.y = syl.style_override.pos_y
                if syl_align in (1, 4, 7):
                    syl.left = syl.x
                    syl.center = syl.left + syl.width / 2.0
                    syl.right = syl.left + syl.width
                elif syl_align in (2, 5, 8):
                    syl.left = syl.x - syl.width / 2.0
                    syl.center = syl.x
                    syl.right = syl.left + syl.width
                elif syl_align in (3, 6, 9):
                    syl.right = syl.x
                    syl.left = syl.right - syl.width
                    syl.center = syl.left + syl.width / 2.0

                if 1 <= syl_align <= 3:
                    syl.bottom = syl.y
                    syl.middle = syl.bottom - syl.height / 2.0
                    syl.top = syl.bottom - syl.height
                elif 4 <= syl_align <= 6:
                    syl.top = syl.y - syl.height / 2.0
                    syl.middle = syl.y
                    syl.bottom = syl.top + syl.height
                elif 7 <= syl_align <= 9:
                    syl.top = syl.y
                    syl.middle = syl.top + syl.height / 2.0
                    syl.bottom = syl.top + syl.height
                syl.prespace_left = syl.left - syl.prespacewidth
                syl.postspace_left = syl.right
            else:
                syl.left += line.left
                syl.center += line.left
                syl.right += line.left
                syl.prespace_left += line.left
                syl.postspace_left += line.left
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
        """Maquetación básica de sílabas preservando espaciado inter-componentes e inter-sílabas."""
        curx = 0.0
        max_h = line.height
        has_prev_text = False
        for syl in line.kara:
            eff_sp = cls.get_effective_spacing(syl.style, meta)

            if syl.prespace:
                if has_prev_text:
                    curx += eff_sp
                syl.prespace_left = curx
                curx += syl.prespacewidth
                has_prev_text = True
            else:
                syl.prespace_left = curx

            if syl.text_spacestripped:
                if has_prev_text:
                    curx += eff_sp
                syl.left = curx
                syl.center = syl.left + syl.width / 2.0
                syl.right = syl.left + syl.width
                curx += syl.width
                has_prev_text = True
            else:
                syl.left = curx
                syl.center = curx
                syl.right = curx

            if syl.postspace:
                if has_prev_text:
                    curx += eff_sp
                syl.postspace_left = curx
                curx += syl.postspacewidth
                has_prev_text = True
            else:
                syl.postspace_left = curx

            if syl.height > max_h:
                max_h = syl.height

        if line.has_style_override and len(line.kara) > 1:
            line.width = curx
            line.height = max_h

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

        has_prev_text = False
        for syl in line.kara:
            eff_sp = cls.get_effective_spacing(syl.style, meta)
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
                has_prev_text = False

            if syl.prespace:
                if has_prev_text:
                    lg["basewidth"] += eff_sp
                lg["basewidth"] += syl.prespacewidth
                has_prev_text = True
            if syl.text_spacestripped:
                if has_prev_text:
                    lg["basewidth"] += eff_sp
                lg["basewidth"] += syl.width
                has_prev_text = True
            if syl.postspace:
                if has_prev_text:
                    lg["basewidth"] += eff_sp
                lg["basewidth"] += syl.postspacewidth
                has_prev_text = True

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
            has_prev_text_lg = False
            for syl in lg["syls"]:
                eff_sp = cls.get_effective_spacing(syl.style, meta)
                if syl.prespace:
                    if has_prev_text_lg:
                        curx += eff_sp
                    syl.prespace_left = curx
                    curx += syl.prespacewidth
                    has_prev_text_lg = True
                else:
                    syl.prespace_left = curx

                if syl.text_spacestripped:
                    if has_prev_text_lg:
                        curx += eff_sp
                    syl.left = curx
                    syl.center = syl.left + syl.width / 2.0
                    syl.right = syl.left + syl.width
                    curx += syl.width
                    has_prev_text_lg = True
                else:
                    syl.left = curx
                    syl.center = curx
                    syl.right = curx

                if syl.postspace:
                    if has_prev_text_lg:
                        curx += eff_sp
                    syl.postspace_left = curx
                    curx += syl.postspacewidth
                    has_prev_text_lg = True
                else:
                    syl.postspace_left = curx

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
