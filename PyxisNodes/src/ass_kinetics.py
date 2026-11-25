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

"""ASS Kinetics and Preserved Tags Module.

Encapsulates specialized tokenization, temporal remapping, kinematic window
intersection, equivalent relative acceleration derivation, and scalar/colour/alpha
interpolation for preserved ASS override tags.
"""

import math
import re
from contextvars import ContextVar
from typing import Any, Dict, List, Optional, Tuple, Union

# Thread-safe storage for the active effect execution window (fx_st, fx_et)
_ACTIVE_FX_WINDOW: ContextVar[Optional[Tuple[float, float]]] = ContextVar("_ACTIVE_FX_WINDOW", default=None)


def set_active_fx_window(st: float, et: float) -> Any:
    """Sets the active effect execution window in thread-local context.

    Args:
        st: Absolute start timestamp of the effect in milliseconds.
        et: Absolute end timestamp of the effect in milliseconds.

    Returns:
        Token that can be passed to reset_active_fx_window.
    """
    return _ACTIVE_FX_WINDOW.set((float(st), float(et)))


def reset_active_fx_window(token: Any) -> None:
    """Resets the active effect window context variable using a token."""
    try:
        _ACTIVE_FX_WINDOW.reset(token)
    except Exception:
        pass


def get_active_fx_window() -> Optional[Tuple[float, float]]:
    """Retrieves the active effect execution window if set."""
    return _ACTIVE_FX_WINDOW.get()


def _fmt_num(v: float) -> str:
    """Formats numeric values concisely removing superfluous trailing zeros."""
    try:
        fv = float(v)
        if fv.is_integer():
            return str(int(fv))
        res = f"{fv:.3f}".rstrip("0").rstrip(".")
        return res if res else "0"
    except Exception:
        return str(v)


TAG_NAME_REGEX = re.compile(
    r"^\\(1c|2c|3c|4c|c|1a|2a|3a|4a|alpha|fscx|fscy|fsp|fs|frz|frx|fry|fr|fax|fay|"
    r"bord|xbord|ybord|shad|xshad|yshad|blur|be|pbo|p|q|an|a|b|i|u|s|fe|fn|r|"
    r"clip|iclip|move|pos|org|fad|fade|t)",
    re.IGNORECASE,
)


def split_tag_name_and_value(tag_stmt: str) -> Tuple[str, str]:
    """Splits an individual ASS tag into canonical tag name and its argument value string."""
    clean = tag_stmt.strip()
    m = TAG_NAME_REGEX.match(clean)
    if m:
        t_name = "\\" + m.group(1).lower()
        t_val = clean[m.end():]
        return t_name, t_val
    return clean, ""


def parse_tag_blocks(text: str) -> List[str]:
    """Extracts tag block contents enclosed in curly braces {...}.

    Args:
        text: Raw ASS dialogue or unit string.

    Returns:
        List of unbracketed tag strings.
    """
    if not text or "{" not in text:
        return []
    return re.findall(r"\{([^}]*)\}", text)


def tokenize_ass_tags(tags_str: str) -> List[str]:
    """Tokenizes an ASS tag block string into individual tag statements.

    Correctly respects nested parentheses such as `\\t(...)` and `\\clip(...)`.

    Args:
        tags_str: Concatenated ASS tag string (e.g. `\\bord2\\blur1\\t(0,200,\\fscx150)`).

    Returns:
        List of individual tag strings starting with `\\`.
    """
    if not tags_str:
        return []

    clean_str = tags_str.strip()
    if clean_str.startswith("{") and clean_str.endswith("}"):
        clean_str = clean_str[1:-1].strip()

    tokens: List[str] = []
    current: List[str] = []
    depth = 0
    in_tag = False

    i = 0
    n = len(clean_str)
    while i < n:
        c = clean_str[i]
        if c == "\\":
            if depth == 0:
                if current and in_tag:
                    tok = "".join(current).strip()
                    if tok and tok != "\\":
                        tokens.append(tok)
                    current = ["\\"]
                else:
                    current.append("\\")
                in_tag = True
            else:
                current.append(c)
        elif c == "(":
            depth += 1
            current.append(c)
        elif c == ")":
            depth = max(0, depth - 1)
            current.append(c)
        else:
            current.append(c)
        i += 1

    if current:
        tok = "".join(current).strip()
        if tok and tok != "\\":
            tokens.append(tok)

    return tokens


def parse_ass_color(c_str: str) -> Optional[Tuple[int, int, int]]:
    """Parses an ASS BGR color token (&HBBGGRR& or &HBBGGRR) into (B, G, R) ints."""
    m = re.search(r"&H([0-9a-fA-F]{1,6})&?", c_str)
    if not m:
        return None
    val = int(m.group(1), 16)
    r = val & 0xFF
    g = (val >> 8) & 0xFF
    b = (val >> 16) & 0xFF
    return (b, g, r)


def format_ass_color(b: int, g: int, r: int) -> str:
    """Formats (B, G, R) integer components into canonical ASS hex '&HBBGGRR&'."""
    cb = max(0, min(255, int(round(b))))
    cg = max(0, min(255, int(round(g))))
    cr = max(0, min(255, int(round(r))))
    return f"&H{cb:02X}{cg:02X}{cr:02X}&"


def parse_ass_alpha(a_str: str) -> Optional[int]:
    """Parses an ASS alpha token (&HAA& or &HAA) into an integer [0, 255]."""
    m = re.search(r"&H([0-9a-fA-F]{1,2})&?", a_str)
    if not m:
        return None
    return int(m.group(1), 16)


def format_ass_alpha(a: int) -> str:
    """Formats an alpha integer into canonical ASS hex '&HAA&'."""
    ca = max(0, min(255, int(round(a))))
    return f"&H{ca:02X}&"


def remap_unit_move(
    move_x1: float,
    move_y1: float,
    move_x2: float,
    move_y2: float,
    t1: Optional[float],
    t2: Optional[float],
    orig_st: float,
    orig_et: float,
    fx_st: float,
    fx_et: float,
    default_orig_x: float,
    default_orig_y: float,
    line_x: Optional[float] = None,
    line_y: Optional[float] = None,
) -> Tuple[bool, str]:
    """Remaps an ASS \\move tag to the active effect timeline.

    Interpolates spatial endpoints linearly according to the intersection between
    the effect execution window [fx_st, fx_et] and the original movement duration.

    Args:
        move_x1, move_y1: Original start coordinates.
        move_x2, move_y2: Original target coordinates.
        t1, t2: Original movement timing offsets relative to orig_st (None for full duration).
        orig_st, orig_et: Original line absolute start and end times (ms).
        fx_st, fx_et: Active effect absolute start and end times (ms).
        default_orig_x, default_orig_y: Reference anchor coordinates for the active unit.
        line_x, line_y: Line anchor coordinates for relative offset calculation.

    Returns:
        Tuple (applied: bool, tag_string: str). If applied is False, tag_string contains fallback \\pos.
    """
    l_dur = max(0.0, float(orig_et) - float(orig_st))
    t_start = 0.0 if t1 is None else float(t1)
    t_end = l_dur if t2 is None else float(t2)

    g1 = float(orig_st) + t_start
    g2 = float(orig_st) + t_end

    lx = default_orig_x if line_x is None else float(line_x)
    ly = default_orig_y if line_y is None else float(line_y)
    delta_x = default_orig_x - lx
    delta_y = default_orig_y - ly

    x1_unit = float(move_x1) + delta_x
    y1_unit = float(move_y1) + delta_y
    x2_unit = float(move_x2) + delta_x
    y2_unit = float(move_y2) + delta_y

    i1 = max(float(fx_st), g1)
    i2 = min(float(fx_et), g2)

    # Strict exclusion: effect falls outside or on boundary of kinetic window
    if i2 <= i1 or g2 <= g1:
        # Movement does not occur during this effect window; emit static position at endpoint
        if float(fx_st) >= g2:
            return (False, f"\\pos({_fmt_num(x2_unit)},{_fmt_num(y2_unit)})")
        return (False, f"\\pos({_fmt_num(x1_unit)},{_fmt_num(y1_unit)})")

    u0 = max(0.0, min(1.0, (i1 - g1) / (g2 - g1)))
    u1 = max(0.0, min(1.0, (i2 - g1) / (g2 - g1)))

    nx1 = x1_unit + (x2_unit - x1_unit) * u0
    ny1 = y1_unit + (y2_unit - y1_unit) * u0
    nx2 = x1_unit + (x2_unit - x1_unit) * u1
    ny2 = y1_unit + (y2_unit - y1_unit) * u1

    t_prime_1 = round(i1 - float(fx_st), 2)
    t_prime_2 = round(i2 - float(fx_st), 2)

    return (
        True,
        f"\\move({_fmt_num(nx1)},{_fmt_num(ny1)},{_fmt_num(nx2)},{_fmt_num(ny2)},{_fmt_num(t_prime_1)},{_fmt_num(t_prime_2)})",
    )


def compute_relative_accel(u0: float, u1: float, a: float) -> float:
    """Calculates equivalent relative acceleration a' for clipped transform window.

    Uses logarithmic least-squares approximation across representative sample points
    when window is clipped and original acceleration deviates from linearity.

    Args:
        u0: Normalized start fraction in [0.0, 1.0].
        u1: Normalized end fraction in [0.0, 1.0].
        a: Original acceleration power exponent.

    Returns:
        Equivalent relative acceleration exponent.
    """
    if abs(a - 1.0) <= 1e-4:
        return 1.0
    if u0 <= 1e-6:
        return round(a, 3)
    if u1 <= u0:
        return 1.0

    p0 = math.pow(max(0.0, u0), a)
    p1 = math.pow(max(0.0, u1), a)
    denom_p = p1 - p0
    if abs(denom_p) < 1e-7:
        return 1.0

    sample_s = (0.1, 0.25, 0.4, 0.55, 0.7, 0.85, 0.95)
    num = 0.0
    den = 0.0
    for s in sample_s:
        u_s = u0 + s * (u1 - u0)
        p_s = math.pow(max(0.0, u_s), a)
        g_s = max(1e-7, min(1.0, (p_s - p0) / denom_p))
        ln_s = math.log(s)
        ln_g = math.log(g_s)
        num += ln_s * ln_g
        den += ln_s * ln_s

    if den > 0.0:
        a_prime = max(0.01, num / den)
        return round(a_prime, 3)
    return round(a, 3)


def _lerp_num(v0: float, v1: float, progress: float) -> float:
    """Linear interpolation helper between two numbers."""
    return v0 + (v1 - v0) * progress


def _interpolate_tag_value(
    tag_name: str,
    val_str: str,
    v0: Any,
    progress: float,
) -> Tuple[str, Any]:
    """Interpolates an individual tag value at the given progression fraction."""
    # 1. Colors
    if tag_name in ("\\1c", "\\2c", "\\3c", "\\4c", "\\c"):
        target_rgb = parse_ass_color(val_str)
        if target_rgb is not None:
            base_rgb = parse_ass_color(str(v0)) if (v0 and parse_ass_color(str(v0))) else target_rgb
            cur_b = _lerp_num(base_rgb[0], target_rgb[0], progress)
            cur_g = _lerp_num(base_rgb[1], target_rgb[1], progress)
            cur_r = _lerp_num(base_rgb[2], target_rgb[2], progress)
            new_hex = format_ass_color(round(cur_b), round(cur_g), round(cur_r))
            return f"{tag_name}{new_hex}", new_hex
        return f"{tag_name}{val_str}", val_str

    # 2. Alphas
    if tag_name in ("\\1a", "\\2a", "\\3a", "\\4a", "\\alpha"):
        target_a = parse_ass_alpha(val_str)
        if target_a is not None:
            base_a = parse_ass_alpha(str(v0)) if (v0 and parse_ass_alpha(str(v0)) is not None) else 0
            cur_a = _lerp_num(base_a, target_a, progress)
            new_alpha = format_ass_alpha(round(cur_a))
            return f"{tag_name}{new_alpha}", new_alpha
        return f"{tag_name}{val_str}", val_str

    # 3. Numeric scalars
    m_num = re.match(r"^([+-]?\d+(?:\.\d+)?)(.*)$", val_str.strip())
    if m_num:
        try:
            target_n = float(m_num.group(1))
            suffix = m_num.group(2)
            try:
                base_n = float(v0) if v0 is not None else target_n
            except Exception:
                base_n = target_n
            cur_n = _lerp_num(base_n, target_n, progress)
            res_str = f"{tag_name}{_fmt_num(cur_n)}{suffix}"
            return res_str, cur_n
        except Exception:
            pass

    # 4. Rectangular clips
    if tag_name in ("\\clip", "\\iclip") and "(" in val_str:
        m_clip = re.match(r"^\(\s*([+-]?\d+(?:\.\d+)?)\s*,\s*([+-]?\d+(?:\.\d+)?)\s*,\s*([+-]?\d+(?:\.\d+)?)\s*,\s*([+-]?\d+(?:\.\d+)?)\s*\)$", val_str.strip())
        if m_clip:
            c_coords = [float(m_clip.group(idx)) for idx in range(1, 5)]
            b_coords = c_coords
            if v0 and isinstance(v0, (list, tuple)) and len(v0) == 4:
                b_coords = [float(v0[k]) for k in range(4)]
            lerped = [_lerp_num(b_coords[k], c_coords[k], progress) for k in range(4)]
            coords_str = ",".join(_fmt_num(val) for val in lerped)
            return f"{tag_name}({coords_str})", lerped

    return f"{tag_name}{val_str}", val_str


def remap_fade(
    fade_token: str,
    orig_st: float,
    orig_et: float,
    fx_st: float,
    fx_et: float,
) -> Tuple[bool, str]:
    """Remaps \\fad(tin, tout) or \\fade(...) to the active effect timeline."""
    l_dur = max(0.0, float(orig_et) - float(orig_st))
    fx_dur = max(0.0, float(fx_et) - float(fx_st))

    # Pattern for \fad(tin, tout)
    m_fad = re.match(r"^\\fad\(\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*\)$", fade_token)
    if m_fad:
        tin = float(m_fad.group(1))
        tout = float(m_fad.group(2))
        a1, a2, a3 = 255, 0, 255
        g1 = float(orig_st)
        g2 = float(orig_st) + tin
        g3 = float(orig_et) - tout
        g4 = float(orig_et)
    else:
        # Pattern for \fade(a1, a2, a3, t1, t2, t3, t4)
        m_fade = re.match(
            r"^\\fade\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*([+-]?\d+(?:\.\d+)?)\s*,\s*([+-]?\d+(?:\.\d+)?)\s*,\s*([+-]?\d+(?:\.\d+)?)\s*,\s*([+-]?\d+(?:\.\d+)?)\s*\)$",
            fade_token,
        )
        if not m_fade:
            return (False, "")
        a1 = int(m_fade.group(1))
        a2 = int(m_fade.group(2))
        a3 = int(m_fade.group(3))
        g1 = float(orig_st) + float(m_fade.group(4))
        g2 = float(orig_st) + float(m_fade.group(5))
        g3 = float(orig_st) + float(m_fade.group(6))
        g4 = float(orig_st) + float(m_fade.group(7))

    def _eval_alpha_at(t: float) -> float:
        if t <= g1:
            return float(a1)
        if g1 < t < g2:
            span = g2 - g1
            return float(a1) + (float(a2) - float(a1)) * ((t - g1) / span) if span > 0 else float(a2)
        if g2 <= t <= g3:
            return float(a2)
        if g3 < t < g4:
            span = g4 - g3
            return float(a2) + (float(a3) - float(a2)) * ((t - g3) / span) if span > 0 else float(a3)
        return float(a3)

    cur_a_start = _eval_alpha_at(float(fx_st))
    cur_a_end = _eval_alpha_at(float(fx_et))

    # Check if fade active during this window
    alpha_points = [cur_a_start]
    for mid_pt in (g2, g3):
        if float(fx_st) < mid_pt < float(fx_et):
            alpha_points.append(_eval_alpha_at(mid_pt))
    alpha_points.append(cur_a_end)

    if all(abs(ap - 0.0) < 0.5 for ap in alpha_points):
        # Fully opaque throughout; default in ASS, omit fade tag
        return (False, "")

    if max(alpha_points) - min(alpha_points) < 1.0:
        # Uniform alpha throughout effect
        const_a = int(round(cur_a_start))
        if const_a > 0:
            return (True, f"\\alpha{format_ass_alpha(const_a)}")
        return (False, "")

    # Multi-point ramp inside effect
    t1_p = 0
    t2_p = round(max(0.0, min(fx_dur, g2 - float(fx_st))), 2)
    t3_p = round(max(0.0, min(fx_dur, g3 - float(fx_st))), 2)
    t4_p = round(fx_dur, 2)

    return (
        True,
        f"\\fade({int(round(cur_a_start))},{int(round(a2))},{int(round(cur_a_end))},{_fmt_num(t1_p)},{_fmt_num(t2_p)},{_fmt_num(t3_p)},{_fmt_num(t4_p)})",
    )


def resolve_preserved_tags(
    source_unit_or_text: Any,
    orig_st: Optional[float] = None,
    orig_et: Optional[float] = None,
    fx_st: Optional[float] = None,
    fx_et: Optional[float] = None,
    is_shape_output: bool = False,
    current_style: Optional[Dict[str, Any]] = None,
) -> str:
    """Resolves and remaps preserved ASS override tags to the active effect timeline.

    Filters control tags (\\k, \\K, \\kf, \\ko, \\kt, \\-*), applies static styling overrides,
    and recalculates kinetic tags (\\move, \\t, \\fad, \\fade) taking into account the
    temporal overlap between original line timing and active effect timing.

    Args:
        source_unit_or_text: PyxisUnit, PyxisLine, or raw tag block string.
        orig_st: Original line start time in ms (derived from unit if omitted).
        orig_et: Original line end time in ms (derived from unit if omitted).
        fx_st: Active effect start time in ms (derived from context if omitted).
        fx_et: Active effect end time in ms (derived from context if omitted).
        is_shape_output: When True, filters font/scale tags (\\fn, \\fs, \\fscx, \\fscy).
        current_style: Optional dictionary with fallback style metrics.

    Returns:
        Concatenated ASS override tag string ready for emission.
    """
    raw_blocks: List[str] = []
    line_st = 0.0
    line_et = 0.0

    # Extract raw blocks and reference timing
    if hasattr(source_unit_or_text, "line") or hasattr(source_unit_or_text, "raw_text"):
        unit = source_unit_or_text
        parent_line = getattr(unit, "line", None) or unit
        line_st = float(getattr(parent_line, "start_time", 0.0))
        line_et = float(getattr(parent_line, "end_time", 0.0))

        # Check for explicit stored raw tags
        stored_raw = getattr(unit, "raw_override_tags", None)
        if stored_raw:
            raw_blocks = stored_raw if isinstance(stored_raw, list) else [str(stored_raw)]
        else:
            u_text = getattr(unit, "text", "")
            l_text = getattr(parent_line, "raw_text", getattr(parent_line, "text", ""))
            raw_blocks = parse_tag_blocks(u_text)
            if not raw_blocks and l_text:
                raw_blocks = parse_tag_blocks(l_text)
    elif isinstance(source_unit_or_text, str):
        raw_blocks = parse_tag_blocks(source_unit_or_text)
        if not raw_blocks and source_unit_or_text.startswith("\\"):
            raw_blocks = [source_unit_or_text]

    if not raw_blocks:
        return ""

    if orig_st is not None:
        line_st = float(orig_st)
    if orig_et is not None:
        line_et = float(orig_et)

    # Determine active effect window
    eff_st = float(line_st)
    eff_et = float(line_et)
    active_window = get_active_fx_window()

    if fx_st is not None and fx_et is not None:
        eff_st = float(fx_st)
        eff_et = float(fx_et)
    elif active_window is not None:
        eff_st = float(active_window[0])
        eff_et = float(active_window[1])
    elif hasattr(source_unit_or_text, "start_time") and hasattr(source_unit_or_text, "end_time"):
        # Local fallback to unit timing if not inside an active effect emission
        u_st = float(getattr(source_unit_or_text, "start_time", 0.0))
        u_et = float(getattr(source_unit_or_text, "end_time", 0.0))
        if hasattr(source_unit_or_text, "line") and getattr(source_unit_or_text, "line") is not source_unit_or_text:
            eff_st = line_st + u_st
            eff_et = line_st + u_et
        else:
            eff_st = u_st
            eff_et = u_et

    l_dur = max(0.0, line_et - line_st)

    # Parse all tag statements across blocks
    all_statements: List[str] = []
    for blk in raw_blocks:
        all_statements.extend(tokenize_ass_tags(blk))

    static_tags: Dict[str, str] = {}
    ordered_kinetic: List[str] = []
    current_values: Dict[str, Any] = {}

    # Font tags to omit on vector shape outputs
    shape_filtered_tags = ("\\fn", "\\fs", "\\fscx", "\\fscy")

    for stmt in all_statements:
        clean = stmt.strip()
        if not clean or not clean.startswith("\\"):
            continue

        # 1. Skip control tags
        if clean.startswith(("\\k", "\\K", "\\kf", "\\ko", "\\kt", "\\-")):
            continue
        if re.match(r"^\\p[0-9]", clean) and not clean.startswith("\\pbo"):
            continue

        # 2. Vector shape filtering
        if is_shape_output and any(clean.startswith(ft) for ft in shape_filtered_tags):
            continue

        # 3. Skip positioning and origin tags (\move, \pos, \org)
        # Handled with canonical precedence in GraphEngine._apply_defaults
        if clean.startswith(("\\move(", "\\pos(", "\\org(")):
            continue

        # 4. Handle \fad / \fade
        if clean.startswith(("\\fad(", "\\fade(")):
            applied, f_tag = remap_fade(clean, line_st, line_et, eff_st, eff_et)
            if applied and f_tag:
                ordered_kinetic.append(f_tag)
            continue

        # 5. Handle transform \t
        if clean.startswith("\\t("):
            m_t = re.match(r"^\\t\((.*)\)$", clean, re.DOTALL)
            if not m_t:
                continue
            inner_content = m_t.group(1).strip()
            # Split before first \
            idx_slash = inner_content.find("\\")
            if idx_slash == -1:
                continue
            args_part = inner_content[:idx_slash].strip()
            tags_part = inner_content[idx_slash:].strip()

            t_args = [arg.strip() for arg in args_part.split(",") if arg.strip()]
            t1_val = 0.0
            t2_val = l_dur
            accel_val = 1.0

            if len(t_args) == 1:
                try:
                    accel_val = float(t_args[0])
                except Exception:
                    accel_val = 1.0
            elif len(t_args) == 2:
                try:
                    t1_val = float(t_args[0])
                    t2_val = float(t_args[1])
                except Exception:
                    pass
            elif len(t_args) >= 3:
                try:
                    t1_val = float(t_args[0])
                    t2_val = float(t_args[1])
                    accel_val = float(t_args[2])
                except Exception:
                    pass

            g1 = line_st + t1_val
            g2 = line_st + t2_val

            # Intersection with effect window
            i1 = max(eff_st, g1)
            i2 = min(eff_et, g2)

            sub_tags = tokenize_ass_tags(tags_part)

            if i2 <= i1 or g2 <= g1:
                # Outside active kinetic span
                if eff_st >= g2:
                    # Transform already completed before this effect; update static accumulator to target
                    for sub in sub_tags:
                        p_name, p_val = split_tag_name_and_value(sub)
                        if not (is_shape_output and any(p_name.startswith(ft) for ft in shape_filtered_tags)):
                            static_tags[p_name] = sub
                            current_values[p_name] = p_val
                continue

            # Within active kinetic span
            u0 = max(0.0, min(1.0, (i1 - g1) / (g2 - g1)))
            u1 = max(0.0, min(1.0, (i2 - g1) / (g2 - g1)))

            p0 = math.pow(u0, accel_val)
            p1 = math.pow(u1, accel_val)

            a_prime = compute_relative_accel(u0, u1, accel_val)

            t_prime_1 = round(i1 - eff_st, 2)
            t_prime_2 = round(i2 - eff_st, 2)

            interpolated_p1_tags: List[str] = []

            for sub in sub_tags:
                p_name, p_val = split_tag_name_and_value(sub)
                if not p_name.startswith("\\"):
                    continue

                if is_shape_output and any(p_name.startswith(ft) for ft in shape_filtered_tags):
                    continue

                v0 = current_values.get(p_name)
                # If effect begins mid-transform (u0 > 0), set intermediate static value at p0
                if u0 > 1e-4:
                    tag_p0_str, cur_val_p0 = _interpolate_tag_value(p_name, p_val, v0, p0)
                    static_tags[p_name] = tag_p0_str
                    current_values[p_name] = cur_val_p0

                # Interpolate target value at p1 for \t
                tag_p1_str, cur_val_p1 = _interpolate_tag_value(p_name, p_val, v0, p1)
                interpolated_p1_tags.append(tag_p1_str)
                current_values[p_name] = cur_val_p1

            if interpolated_p1_tags:
                sub_tags_str = "".join(interpolated_p1_tags)
                if abs(a_prime - 1.0) <= 1e-3:
                    ordered_kinetic.append(f"\\t({_fmt_num(t_prime_1)},{_fmt_num(t_prime_2)},{sub_tags_str})")
                else:
                    ordered_kinetic.append(f"\\t({_fmt_num(t_prime_1)},{_fmt_num(t_prime_2)},{_fmt_num(a_prime)},{sub_tags_str})")
            continue

        # 6. Static tag statement
        p_name, p_val = split_tag_name_and_value(clean)
        static_tags[p_name] = clean
        current_values[p_name] = p_val

    # Combine static base tags followed by kinetic transformations
    result_parts: List[str] = list(static_tags.values()) + ordered_kinetic
    return "".join(result_parts)


# ==============================================================================
# Line Original Tag Extraction (line.<prop>_org)
# ==============================================================================

LINE_ORG_TAG_KEYS = frozenset({
    "color1_org", "color2_org", "color3_org", "color4_org",
    "alpha_org", "alpha1_org", "alpha2_org", "alpha3_org", "alpha4_org",
    "fontname_org", "fontsize_org", "scale_x_org", "scale_y_org", "spacing_org",
    "bold_org", "italic_org", "underline_org", "strikeout_org", "encoding_org", "q_org",
    "align_org", "frz_org", "frx_org", "fry_org", "fax_org", "fay_org",
    "pos_org", "org_org",
    "outline_org", "xbord_org", "ybord_org",
    "shadow_org", "xshad_org", "yshad_org",
    "blur_org", "be_org",
    "fad_org", "clip_org", "iclip_org",
})

_KARAOKE_TIMING_TAGS = frozenset({"\\k", "\\kf", "\\ko", "\\K", "\\kt"})


def _normalize_ass_color_6(val: Any, fallback: str) -> str:
    """Normalize an ASS color literal to canonical 6-digit '&HBBGGRR&' format."""
    if not val:
        return fallback
    raw = str(val).strip().strip("&").lstrip("hH")
    hex_chars = "".join(c for c in raw if c in "0123456789abcdefABCDEF")
    if len(hex_chars) == 8:
        hex_chars = hex_chars[2:]
    elif len(hex_chars) < 6:
        hex_chars = hex_chars.zfill(6)
    elif len(hex_chars) > 6:
        hex_chars = hex_chars[-6:]
    if len(hex_chars) == 6:
        return f"&H{hex_chars.upper()}&"
    return fallback


def _normalize_ass_alpha_2(val: Any, fallback: str = "&H00&") -> str:
    """Normalize an ASS alpha literal to canonical 2-digit '&HAA&' format."""
    if val is None or val == "":
        return fallback
    s = str(val).strip()
    if s.isdigit():
        num = max(0, min(255, int(s)))
        return f"&H{num:02X}&"
    raw = s.strip("&").lstrip("hH")
    hex_chars = "".join(c for c in raw if c in "0123456789abcdefABCDEF")
    if not hex_chars:
        return fallback
    if len(hex_chars) > 2:
        hex_chars = hex_chars[-2:]
    return f"&H{hex_chars.zfill(2).upper()}&"


def _build_styleref_org_defaults(styleref: Any) -> dict:
    """Build the default *_org dictionary from a line's StyleRef and ASS neutral defaults."""
    c1 = _normalize_ass_color_6(getattr(styleref, "color1", "&HFFFFFF&"), "&HFFFFFF&")
    c2 = _normalize_ass_color_6(getattr(styleref, "color2", "&H0000FF&"), "&H0000FF&")
    c3 = _normalize_ass_color_6(getattr(styleref, "color3", "&H000000&"), "&H000000&")
    c4 = _normalize_ass_color_6(getattr(styleref, "color4", "&H000000&"), "&H000000&")

    a1 = _normalize_ass_alpha_2(getattr(styleref, "alpha1", "&H00&"), "&H00&")
    a2 = _normalize_ass_alpha_2(getattr(styleref, "alpha2", "&H00&"), "&H00&")
    a3 = _normalize_ass_alpha_2(getattr(styleref, "alpha3", "&H00&"), "&H00&")
    a4 = _normalize_ass_alpha_2(getattr(styleref, "alpha4", "&H00&"), "&H00&")

    outline_val = float(getattr(styleref, "outline", getattr(styleref, "bord", 2.0)) or 0.0)
    shadow_val = float(getattr(styleref, "shadow", getattr(styleref, "shad", 0.0)) or 0.0)

    return {
        "color1_org": c1,
        "color2_org": c2,
        "color3_org": c3,
        "color4_org": c4,
        "alpha_org": "&H00&",
        "alpha1_org": a1,
        "alpha2_org": a2,
        "alpha3_org": a3,
        "alpha4_org": a4,
        "fontname_org": str(getattr(styleref, "fontname", "Arial") or "Arial"),
        "fontsize_org": float(getattr(styleref, "fontsize", 40.0) or 40.0),
        "scale_x_org": float(getattr(styleref, "scale_x", 100.0) if getattr(styleref, "scale_x", None) is not None else 100.0),
        "scale_y_org": float(getattr(styleref, "scale_y", 100.0) if getattr(styleref, "scale_y", None) is not None else 100.0),
        "spacing_org": float(getattr(styleref, "spacing", 0.0) or 0.0),
        "bold_org": 1 if getattr(styleref, "bold", False) else 0,
        "italic_org": 1 if getattr(styleref, "italic", False) else 0,
        "underline_org": 1 if getattr(styleref, "underline", False) else 0,
        "strikeout_org": 1 if getattr(styleref, "strikeout", False) else 0,
        "encoding_org": int(getattr(styleref, "encoding", 1) or 1),
        "q_org": 0,
        "align_org": int(getattr(styleref, "align", 2) or 2),
        "frz_org": float(getattr(styleref, "angle", getattr(styleref, "frz", 0.0)) or 0.0),
        "frx_org": 0.0,
        "fry_org": 0.0,
        "fax_org": 0.0,
        "fay_org": 0.0,
        "pos_org": "",
        "org_org": "",
        "outline_org": outline_val,
        "xbord_org": outline_val,
        "ybord_org": outline_val,
        "shadow_org": shadow_val,
        "xshad_org": shadow_val,
        "yshad_org": shadow_val,
        "blur_org": 0.0,
        "be_org": 0.0,
        "fad_org": "",
        "clip_org": "",
        "iclip_org": "",
    }


def _extract_leading_tag_blocks(raw_text: str) -> List[str]:
    """Return unbracketed contents of consecutive leading {...} blocks before any dialogue text."""
    blocks: List[str] = []
    i = 0
    n = len(raw_text)
    while i < n:
        if raw_text[i].isspace():
            i += 1
            continue
        if raw_text[i] == "{":
            close_idx = raw_text.find("}", i + 1)
            if close_idx == -1:
                break
            blocks.append(raw_text[i + 1 : close_idx])
            i = close_idx + 1
            continue
        break
    return blocks


def _parse_float_safe(val: str, fallback: float) -> float:
    try:
        return float(val.strip())
    except Exception:
        return fallback


def _parse_int_safe(val: str, fallback: int) -> int:
    try:
        return int(float(val.strip()))
    except Exception:
        return fallback


_PAREN_ARG_TAGS = {
    "\\pos": "pos_org",
    "\\org": "org_org",
    "\\fad": "fad_org",
    "\\fade": "fad_org",
    "\\clip": "clip_org",
    "\\iclip": "iclip_org",
}

_FLOAT_PROP_TAGS = {
    "\\fs": "fontsize_org",
    "\\fscx": "scale_x_org",
    "\\fscy": "scale_y_org",
    "\\fsp": "spacing_org",
    "\\frz": "frz_org",
    "\\fr": "frz_org",
    "\\frx": "frx_org",
    "\\fry": "fry_org",
    "\\fax": "fax_org",
    "\\fay": "fay_org",
    "\\blur": "blur_org",
    "\\be": "be_org",
    "\\xbord": "xbord_org",
    "\\ybord": "ybord_org",
    "\\xshad": "xshad_org",
    "\\yshad": "yshad_org",
}

_INT_PROP_TAGS = {
    "\\an": "align_org",
    "\\b": "bold_org",
    "\\i": "italic_org",
    "\\u": "underline_org",
    "\\s": "strikeout_org",
    "\\fe": "encoding_org",
    "\\q": "q_org",
}

_COLOR_PROP_TAGS = {
    "\\c": "color1_org",
    "\\1c": "color1_org",
    "\\2c": "color2_org",
    "\\3c": "color3_org",
    "\\4c": "color4_org",
}

_ALPHA_PROP_TAGS = {
    "\\1a": "alpha1_org",
    "\\2a": "alpha2_org",
    "\\3a": "alpha3_org",
    "\\4a": "alpha4_org",
}


def extract_line_org_props(line_obj: Any) -> dict:
    """
    Extract all canonical line-level original ASS tag properties (<prop>_org)
    from a PyxisLine's leading override blocks, falling back to styleref defaults.
    Excludes karaoke timing tags (\\k, \\kf, \\ko, \\K, \\kt) and animated \\t(...) transforms.
    """
    styleref = getattr(line_obj, "styleref", None)
    defaults = _build_styleref_org_defaults(styleref)
    props = defaults.copy()

    raw_text = getattr(line_obj, "raw_text", "") or ""
    blocks = _extract_leading_tag_blocks(raw_text)
    if not blocks:
        raw_override_tags = getattr(line_obj, "raw_override_tags", None)
        if raw_override_tags and raw_text == "":
            blocks = [raw_override_tags[0]]

    for block in blocks:
        for tok in tokenize_ass_tags(block):
            if not tok.startswith("\\"):
                continue
            if tok.startswith("\\t(") or tok == "\\t":
                continue
            if tok.startswith("\\r"):
                props = defaults.copy()
                continue

            # Parenthesized geometry / timing / clip tags
            if "(" in tok and tok.endswith(")"):
                paren_idx = tok.find("(")
                t_name = tok[:paren_idx]
                if t_name in _PAREN_ARG_TAGS:
                    props[_PAREN_ARG_TAGS[t_name]] = tok[paren_idx + 1 : -1].strip()
                continue

            p_name, p_val = split_tag_name_and_value(tok)
            if p_name in _KARAOKE_TIMING_TAGS:
                continue

            if p_name == "\\fn":
                fn_clean = p_val.strip()
                if fn_clean:
                    props["fontname_org"] = fn_clean
            elif p_name in _COLOR_PROP_TAGS:
                key = _COLOR_PROP_TAGS[p_name]
                props[key] = _normalize_ass_color_6(p_val, defaults[key])
            elif p_name == "\\alpha":
                a_val = _normalize_ass_alpha_2(p_val, "&H00&")
                props["alpha_org"] = a_val
                props["alpha1_org"] = a_val
                props["alpha2_org"] = a_val
                props["alpha3_org"] = a_val
                props["alpha4_org"] = a_val
            elif p_name in _ALPHA_PROP_TAGS:
                key = _ALPHA_PROP_TAGS[p_name]
                props[key] = _normalize_ass_alpha_2(p_val, defaults[key])
            elif p_name == "\\bord":
                v = _parse_float_safe(p_val, defaults["outline_org"])
                props["outline_org"] = v
                props["xbord_org"] = v
                props["ybord_org"] = v
            elif p_name == "\\shad":
                v = _parse_float_safe(p_val, defaults["shadow_org"])
                props["shadow_org"] = v
                props["xshad_org"] = v
                props["yshad_org"] = v
            elif p_name in _FLOAT_PROP_TAGS:
                key = _FLOAT_PROP_TAGS[p_name]
                props[key] = _parse_float_safe(p_val, defaults[key])
            elif p_name in _INT_PROP_TAGS:
                key = _INT_PROP_TAGS[p_name]
                props[key] = _parse_int_safe(p_val, defaults[key])

    return props
