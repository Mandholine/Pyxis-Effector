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

"""Pre-generation Graph Validator & Linter.

Analyses the active graph before rendering to detect:
1. Critical system conflicts (Red): Missing output node, data-node cycles, etc.
2. Syntax and expression warnings (Orange): Python/Lua scripts, Define Vars,
   delimiters, invalid Dark Tags, and ASS tag arguments that would break
   the string evaluator.
"""

from __future__ import annotations

import ast
import difflib
import re
from typing import Any, Dict, List, Optional, Set, Tuple


_KNOWN_GLOBAL_VARS: Set[str] = {
    # 1. Context Objects and Namespaces
    "fx", "syl", "char", "word",
    "line", "l", "furi", "meta", "time", "by", "sync",
    "math", "shape", "context", "unit", "active_unit", "active_line", "ink",

    # 2. Iterators, Indices, and Counters
    "i", "n", "j", "maxj", "k", "maxk", "m", "N", "ci", "cn", "si", "wi", "syl_i", "word_i",
    "fx_i", "fx_n", "maxloop", "col", "row", "c_col", "c_row", "idx", "count", "total",
    "val_i", "val_n", "result",
    "s_i", "s_n", "s_max", "slice_i", "slice_n", "slice_max",
    "d_i", "d_n", "d_max", "divide_i", "divide_n", "divide_max",
    "b_i", "b_n", "b_max", "ring_i", "ring_n", "ring_max",
    "a_i", "a_n", "a_max", "array_i", "array_n", "array_max",
    "m_i", "m_n", "m_max", "multi_i", "multi_n", "multi_max",
    "p_i", "p_n", "p_max", "particle_i", "particle_n", "particle_max",
    "tp_i", "tp_n", "tp_max", "text_p_i", "text_p_n", "text_p_max",
    "ip_i", "ip_n", "ip_max", "img_p_i", "img_p_n", "img_p_max", "total_pixels",
    "c_i", "c_n", "c_max", "clip_i", "clip_n", "clip_max",
    "an_i", "an_n", "an_max", "anim_i", "anim_n", "anim_max", "an_j",

    # 3. Spatial, Coordinates, and Box Dimensions
    "x", "y", "ox", "oy", "pos_x", "pos_y", "org_x", "org_y",
    "fx_pos_x", "fx_pos_y", "fx_org_x", "fx_org_y", "has_org", "pos_overridden",
    "fx_align", "origin_align", "align",
    "left", "right", "top", "bottom", "center", "middle", "width", "height",
    "descent", "extlead", "prespacewidth", "postspacewidth",
    "val_left", "val_center", "val_right", "val_top", "val_middle", "val_bottom",
    "val_width", "val_height", "val_x", "val_y", "cx", "cy", "w", "h",
    "do", "dc", "ao", "ac", "k", "Pk", "Pn", "minx", "miny", "maxx", "maxy", "Cx", "Cy",

    # 4. Timing and Durations
    "st", "et", "dur", "start", "end", "mid", "mid_time", "kdur", "start_time", "end_time", "duration",
    "syl_start", "syl_end", "syl_mid", "char_start", "char_end", "char_mid", "word_start", "word_end", "word_mid",
    "ini", "val_start", "val_st", "val_end", "val_et", "val_dur", "val_mid", "maxgap", "max_gap",
    "frame_st", "frame_et", "frame_start_time", "frame_end_time", "frame_time",
    "effect_st", "effect_et", "effect_dur", "fx_st", "fx_et", "fx_dur", "fx_start_time", "fx_end_time",
    "line_start_time", "line_end_time", "line_dur",
    "unit_abs_start_time", "unit_abs_end_time",
    "frame_dur", "fd", "fps",
    "t", "t1", "t2", "t3", "t4", "dt",
    "li", "lo", "m1", "m2", "l1", "l2",
    "time_lead_in", "time_lead_out", "time_middle_1", "time_middle_2", "time_loop_1", "time_loop_2",

    # 5. ASS Subtitle Attributes & Context Helpers
    "layer", "style", "actor", "text", "text_stripped", "margin_l", "margin_r", "margin_v", "effect",
    "ratio", "module", "prog", "progress", "order", "prev", "next", "is_first", "is_last",
    "has_prev", "has_next", "val", "value", "v", "v1", "v2", "accel", "step", "seed",
    "return_raw",
    "p0", "p1", "p2", "p3", "color", "c", "r", "g", "b", "a",
    "color1", "color2", "color3", "color4",
    "alpha1", "alpha2", "alpha3", "alpha4",
    "fontname", "fontsize", "bold", "italic", "underline", "strikeout",
    "scale_x", "scale_y", "spacing", "outline", "shadow", "angle",
    "remember", "recall", "memory",

    # 6. Python Built-ins, Keywords & Constants
    "min", "max", "abs", "round", "int", "float", "pow", "sum", "len", "str", "bool",
    "True", "False", "None", "true", "false", "nil", "null", "yes", "no",
    "range", "enumerate", "zip", "list", "dict", "set", "tuple", "map", "filter",
    "all", "any", "chr", "ord", "hex", "bin", "oct", "repr", "sorted", "reversed",
    "pi", "e", "tau", "inf", "nan", "PI",

    # 7. Math Functions & Constants
    "sin", "cos", "tan", "asin", "acos", "sqrt", "ceil", "floor", "atan2", "degrees", "radians", "rad", "deg",
    "hypot", "log", "exp",

    # 8. Random Functions
    "R", "Rs", "Rc", "Rd", "Rm", "Rds", "Rcs", "Rms", "Rr", "Rstep", "R2d",
    "Rbool", "Rcolor", "Re", "Rfake", "rand", "random",
    "random_color", "random_alpha", "color_random", "alpha_random",

    # 9. Audio Functions
    "audio_rms", "audio_peak", "audio_band", "audio_fft",

    # 10. Animation, Interpolation & Easing Functions
    "clamp", "lerp", "map_range", "map_value", "ease_in", "ease_out", "ease_in_out",
    "cubic_in", "cubic_out", "elastic", "bounce", "back", "sine_wave", "square_wave",
    "triangle_wave", "sawtooth_wave", "polar", "bezier", "ipol",

    # 11. Time, Shape & Tag Generation Functions
    "time_to_frame", "duration", "parse_ass_time", "format_ass_time", "format", "calculate_sync_gap",
    "strip_tags", "kana", "pos", "move", "org", "fad", "fade", "clip", "iclip",
    "c1", "c2", "c3", "c4", "color_1", "color_2", "color_3", "color_4",
    "a1", "a2", "a3", "a4", "alpha", "trans", "fscx", "fscy", "fscxy",
    "frz", "frx", "fry", "fax", "fay", "bord", "shad", "blur", "an",
    "ass_color", "ass_alpha", "move_tag", "move_text", "tag_only",
    "resolve_shape", "shape_circle", "shape_square", "shape_rectangle", "shape_triangle",
    "shape_rhombus", "shape_rounded_corners", "shape_pentagon", "shape_hexagon",
    "shape_octagon", "shape_star", "shape_heart",

    # 12. Internal / Sanitization Dummies
    "__dummy_format__", "__color__"
}

try:
    from decorators import NODE_REGISTRY
    for _k, _v in NODE_REGISTRY.items():
        if hasattr(_v, "__name__"):
            _KNOWN_GLOBAL_VARS.add(_v.__name__)
except Exception:
    pass

# Mapeo canónico de iteradores y totales de sub-bucles a sus tipos de nodos generadores
_SUBLOOP_GENERATOR_VARS: Dict[str, Tuple[str, ...]] = {
    # 1. Slicer
    "s_i": ("Shape/Slicer", "Slicer"),
    "slice_i": ("Shape/Slicer", "Slicer"),
    "s_n": ("Shape/Slicer", "Slicer"),
    "s_max": ("Shape/Slicer", "Slicer"),
    "slice_n": ("Shape/Slicer", "Slicer"),
    "slice_max": ("Shape/Slicer", "Slicer"),
    "slicer_loop_count": ("Shape/Slicer", "Slicer"),

    # 2. Union & Divide
    "d_i": ("Shape/Union & Divide", "Union & Divide"),
    "divide_i": ("Shape/Union & Divide", "Union & Divide"),
    "d_n": ("Shape/Union & Divide", "Union & Divide"),
    "d_max": ("Shape/Union & Divide", "Union & Divide"),
    "divide_n": ("Shape/Union & Divide", "Union & Divide"),
    "divide_max": ("Shape/Union & Divide", "Union & Divide"),

    # 3. Particles (also generated by IMG to pixels)
    "p_i": ("Functions/Particles", "Particles", "Functions/IMG to pixels", "IMG to pixels"),
    "particle_i": ("Functions/Particles", "Particles", "Functions/IMG to pixels", "IMG to pixels"),
    "p_n": ("Functions/Particles", "Particles", "Functions/IMG to pixels", "IMG to pixels"),
    "p_max": ("Functions/Particles", "Particles", "Functions/IMG to pixels", "IMG to pixels"),
    "particle_n": ("Functions/Particles", "Particles", "Functions/IMG to pixels", "IMG to pixels"),
    "particle_max": ("Functions/Particles", "Particles", "Functions/IMG to pixels", "IMG to pixels"),

    # 4. Rings
    "b_i": ("Shape/Rings", "Rings"),
    "ring_i": ("Shape/Rings", "Rings"),
    "b_n": ("Shape/Rings", "Rings"),
    "b_max": ("Shape/Rings", "Rings"),
    "ring_n": ("Shape/Rings", "Rings"),
    "ring_max": ("Shape/Rings", "Rings"),

    # 5. Array
    "a_i": ("Shape/Array", "Array"),
    "array_i": ("Shape/Array", "Array"),
    "a_n": ("Shape/Array", "Array"),
    "a_max": ("Shape/Array", "Array"),
    "array_n": ("Shape/Array", "Array"),
    "array_max": ("Shape/Array", "Array"),

    # 6. Multi Shape
    "m_i": ("Shape/Multi Shape", "Multi Shape"),
    "multi_i": ("Shape/Multi Shape", "Multi Shape"),
    "m_n": ("Shape/Multi Shape", "Multi Shape"),
    "m_max": ("Shape/Multi Shape", "Multi Shape"),
    "multi_n": ("Shape/Multi Shape", "Multi Shape"),
    "multi_max": ("Shape/Multi Shape", "Multi Shape"),

    # 7. Text Particles aliases (generated by Functions/Particles)
    "tp_i": ("Functions/Particles", "Particles"),
    "text_p_i": ("Functions/Particles", "Particles"),
    "tp_n": ("Functions/Particles", "Particles"),
    "tp_max": ("Functions/Particles", "Particles"),
    "text_p_n": ("Functions/Particles", "Particles"),
    "text_p_max": ("Functions/Particles", "Particles"),

    # 8. Image Pixels (generated by Functions/IMG to pixels)
    "ip_i": ("Functions/IMG to pixels", "IMG to pixels"),
    "img_p_i": ("Functions/IMG to pixels", "IMG to pixels"),
    "ip_n": ("Functions/IMG to pixels", "IMG to pixels"),
    "ip_max": ("Functions/IMG to pixels", "IMG to pixels"),
    "img_p_n": ("Functions/IMG to pixels", "IMG to pixels"),
    "img_p_max": ("Functions/IMG to pixels", "IMG to pixels"),
    "total_pixels": ("Functions/IMG to pixels", "IMG to pixels"),

    # 9. Clip Gradient
    "c_i": ("Functions/Clip Gradient", "Clip Gradient"),
    "clip_i": ("Functions/Clip Gradient", "Clip Gradient"),
    "c_n": ("Functions/Clip Gradient", "Clip Gradient"),
    "c_max": ("Functions/Clip Gradient", "Clip Gradient"),
    "clip_n": ("Functions/Clip Gradient", "Clip Gradient"),
    "clip_max": ("Functions/Clip Gradient", "Clip Gradient"),

    # 10. Animation
    "an_i": ("Functions/Animation", "Animation"),
    "anim_i": ("Functions/Animation", "Animation"),
    "an_j": ("Functions/Animation", "Animation"),
    "an_n": ("Functions/Animation", "Animation"),
    "an_max": ("Functions/Animation", "Animation"),
    "anim_n": ("Functions/Animation", "Animation"),
    "anim_max": ("Functions/Animation", "Animation"),
}

_SHAPE_PRESETS: Set[str] = {
    # 1. shapes (9)
    "circle", "triangle", "rectangle", "circangle", "pixel", "pentagon", "hexagon", "octagon", "diamond",
    # 2. hearts (3)
    "heart", "heart2t", "heartb",
    # 3. shines (4)
    "shine1t", "shine2t", "shine3t", "shine4t",
    # 4. specials (5)
    "clover", "feather", "feather2", "gear", "bubble",
    # 5. music (4)
    "note1t", "note2t", "note3t", "note4t",
    # 6. stars (11)
    "star", "star1t", "star2t", "star3t", "star4t", "star5t", "star6t", "star7t", "star8t", "star9t", "star10t",
    # 7. sakura (8)
    "sakura", "sakura1t", "sakura2t", "sakura3t", "sakura4t", "sakura5t", "sakura6t", "sakura7t",
    # 8. snow (3)
    "snowflake1t", "snowflake2t", "snowflake3t",
    # 9. flowers (29)
    "flower1t", "flower2t", "flower3t", "flower4t", "flower5t", "flower6t", "flower7t", "flower8t", "flower9t",
    "flower10t", "flower11t", "flower12t", "flower13t", "flower14t", "flower15t", "flower16t", "flower17t", "flower18t", "flower19t",
    "flower20t", "flower21t", "flower22t", "flower23t", "flower24t", "flower25t", "flower26t", "flower27t", "flower28t", "flower29t",
    # 10. geometry (4)
    "crystal17", "geometric10", "diagonal13r", "diagonal13l"
}


def _is_drawing_or_shape(text: str) -> bool:
    """
    Determines whether a given string corresponds to a known shape preset or raw ASSdraw vector drawing.

    Args:
        text: Input string to test against shape catalog or drawing command syntax.

    Returns:
        bool: True if the string matches a canonical shape preset or starts with an ASSdraw vector command ('m').
    """
    clean = text.strip()
    if not clean:
        return False
    clean_lower = clean.lower()
    if clean_lower in _SHAPE_PRESETS:
        return True
    # Vector drawings must start with the move command 'm' (e.g. 'm 0 0', 'm-10 -20')
    if re.match(r'^m\s*-?\d+', clean_lower) or clean_lower.startswith(('m ', 'm-')):
        return True
    return False


_VALID_RESTORATION_TAGS: Set[str] = {
    "c", "alpha", "fscxy", "fscx", "fscy", "fs", "fsp", "fn", "an",
    "xybord", "xbord", "ybord", "bord", "xyshad", "xshad", "yshad", "shad", "bs",
    "frxyz", "frxy", "frxz", "fryz", "frz", "fr", "frx", "fry",
    "blur", "be", "faxy", "fax", "fay", "b", "i", "u", "s"
}

_INVALID_STOCHASTIC_BASE_TAGS: Set[str] = {
    "pos", "org", "clip", "iclip", "p", "an", "k", "kf", "ko", "K", "q",
    "r", "t", "te", "ts", "tc", "tw", "move", "fad", "fade"
}

_EXPR_TRAILING_OPERATOR_PATTERN = re.compile(
    r'(?:==|!=|~=|<=|>=|<|>|\+|\-|\*|/|%|\*\*|\b(?:and|or|not|is|in)\b)$'
)

_EXPR_LEADING_OPERATOR_PATTERN = re.compile(
    r'^(?:==|!=|~=|<=|>=|<|>|\*|/|%|\*\*|\b(?:and|or|is|in)\b)'
)

_EXPR_CONSECUTIVE_BINARY_OPS_PATTERN = re.compile(
    r'(?:==|!=|~=|<=|>=|<|>|\+|\-|\*|/|%|\*\*|\b(?:and|or|is|in)\b)\s*(?:==|!=|~=|<=|>=|<|>|\*|/|%|\*\*|\b(?:and|or|is|in)\b)'
)

_EXPR_ASSIGNMENT_EQUAL_PATTERN = re.compile(
    r'(?<![!=<>~])=(?![=])'
)

_EXPR_TRIPLE_EQUAL_PATTERN = re.compile(
    r'===+'
)

_EXPR_JS_LOGICAL_OPS_PATTERN = re.compile(
    r'(&&|\|\|)'
)

_LUA_RUNTIME: Optional[Any] = None


def _get_lua_runtime() -> Optional[Any]:
    """
    Retrieves or initialises a cached Lua runtime instance via lupa.

    Returns:
        Optional[Any]: Active LuaRuntime instance if lupa is available; otherwise None.
    """
    global _LUA_RUNTIME
    if _LUA_RUNTIME is None:
        try:
            import lupa
            _LUA_RUNTIME = lupa.LuaRuntime()
        except ImportError:
            _LUA_RUNTIME = None
    return _LUA_RUNTIME


def _extract_ass_tags(text: str) -> List[Tuple[str, str, int, int]]:
    """
    Extracts all '\\tag(inner)' pairs from text with balanced parenthesis and quotation matching.

    Args:
        text: Subtitle text or override block to inspect.

    Returns:
        List[Tuple[str, str, int, int]]: List of tuples containing:
            (tag_name, inner_content, start_index, end_index)
            where end_index is the closing parenthesis position.
    """
    results: List[Tuple[str, str, int, int]] = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] == '\\':
            m = re.match(r'\\([a-zA-Z0-9_]+)', text[i:])
            if m:
                tag_name = m.group(1)
                after_tag_idx = i + m.end()
                if after_tag_idx < n and text[after_tag_idx] == '(':
                    depth = 1
                    j = after_tag_idx + 1
                    in_quote: Optional[str] = None
                    prev_ch = '('
                    while j < n and depth > 0:
                        ch = text[j]
                        if in_quote is not None:
                            if ch == in_quote and prev_ch != '\\':
                                in_quote = None
                        elif ch in ('"', "'") and prev_ch != '\\':
                            in_quote = ch
                        elif ch == '(':
                            depth += 1
                        elif ch == ')':
                            depth -= 1
                        prev_ch = ch
                        j += 1
                    if depth == 0:
                        inner = text[after_tag_idx + 1 : j - 1]
                        results.append((tag_name, inner, i, j - 1))
                        i = j
                        continue
        i += 1
    return results


def _split_top_level_commas(s: str) -> List[str]:
    """
    Splits a string by commas that reside strictly outside parentheses, brackets, braces, and quotes.

    Args:
        s: Raw argument string or parameter list.

    Returns:
        List[str]: Trimmed components split at top-level comma delimiters.
    """
    parts: List[str] = []
    current: List[str] = []
    depth = 0
    bracket_depth = 0
    brace_depth = 0
    in_quote: Optional[str] = None
    prev_ch = ""

    for ch in s:
        if in_quote is not None:
            current.append(ch)
            if ch == in_quote and prev_ch != '\\':
                in_quote = None
            prev_ch = ch
            continue

        if ch in ('"', "'") and prev_ch != '\\':
            in_quote = ch
            current.append(ch)
        elif ch == '(':
            depth += 1
            current.append(ch)
        elif ch == ')':
            if depth > 0:
                depth -= 1
            current.append(ch)
        elif ch == '[':
            bracket_depth += 1
            current.append(ch)
        elif ch == ']':
            if bracket_depth > 0:
                bracket_depth -= 1
            current.append(ch)
        elif ch == '{':
            brace_depth += 1
            current.append(ch)
        elif ch == '}':
            if brace_depth > 0:
                brace_depth -= 1
            current.append(ch)
        elif ch == ',' and depth == 0 and bracket_depth == 0 and brace_depth == 0:
            parts.append("".join(current).strip())
            current = []
        else:
            current.append(ch)
        prev_ch = ch

    if current:
        parts.append("".join(current).strip())
    elif s.strip().endswith(','):
        parts.append("")

    return parts


def _split_statements_outside_quotes(s: str) -> List[str]:
    """
    Splits text by semicolons or newlines that reside strictly outside quotation marks.

    Args:
        s: Compound code statement or multi-line variable declaration block.

    Returns:
        List[str]: Individual statements stripped of extraneous surrounding whitespace.
    """
    parts: List[str] = []
    current: List[str] = []
    in_quote: Optional[str] = None
    prev_ch = ""

    for ch in s:
        if in_quote is not None:
            current.append(ch)
            if ch == in_quote and prev_ch != '\\':
                in_quote = None
            prev_ch = ch
            continue

        if ch in ('"', "'") and prev_ch != '\\':
            in_quote = ch
            current.append(ch)
        elif ch in (';', '\n'):
            line_str = "".join(current).strip()
            if line_str:
                parts.append(line_str)
            current = []
        else:
            current.append(ch)
        prev_ch = ch

    if current:
        line_str = "".join(current).strip()
        if line_str:
            parts.append(line_str)

    return parts


def _strip_string_literals(s: str) -> str:
    """
    Replaces contents of string literals (single or double quoted) with empty quotes to prevent false-positive parsing.

    Args:
        s: Raw code or expression string.

    Returns:
        str: Sanitised expression with literal string bodies stripped.
    """
    return re.sub(r'(\'(?:[^\'\\]|\\.)*\'|"(?:[^"\\]|\\.)*")', '""', s)


class GraphValidator:
    """
    Pre-generation diagnostic validator for Pyxis graph topology, syntax, scripts, and string expressions.

    Responsibilities:
    1. System Topology Verification (Critical / Red):
       - Asserts presence of required sink node ('System/Output').
       - Executes 3-colour depth-first search (DFS) to detect circular dependency loops among data nodes.
    2. Variable Harvesting and Scope Resolution:
       - Traverses 'Define Vars', 'Script Code', 'MaxLoop', 'Get Var', 'Set Var', and 'Memory' nodes.
       - Discovers user-declared identifiers, variables, iterators, and functions to populate dynamic scope.
    3. Diagnostic Issue Aggregation:
       - Standardises severity ('critical', 'warning'), node location, source code snippet, error message,
         i18n localisation keys, and corrective suggestions.
    """

    def __init__(self, graph_data: Dict[str, Any]):
        """
        Initialises the validator with raw serialised graph data from LiteGraph / Pyxis.

        Args:
            graph_data: Dictionary representing canvas state containing 'nodes' and 'links' lists.
        """
        self.graph_data = graph_data if isinstance(graph_data, dict) else {}
        self.nodes: List[Dict[str, Any]] = self.graph_data.get("nodes", []) if isinstance(self.graph_data.get("nodes"), list) else []
        self.links: List[Any] = self.graph_data.get("links", []) if isinstance(self.graph_data.get("links"), list) else []
        self.issues: List[Dict[str, Any]] = []
        self.user_defined_vars: Set[str] = set()
        self.present_node_types: Set[str] = set()
        for n in self.nodes:
            if isinstance(n, dict):
                nt = str(n.get("type", "")).strip()
                if nt:
                    self.present_node_types.add(nt)
                    if "/" in nt:
                        self.present_node_types.add(nt.split("/", 1)[1].strip())
        self._warned_subloop_vars: Set[Tuple[Optional[int], str]] = set()

    def validate(self) -> List[Dict[str, Any]]:
        """
        Executes all validation routines sequentially and returns aggregated diagnostic issues.

        Order of validation:
        1. User-defined variable harvesting ('_collect_user_defined_vars').
        2. System topology and data-node cycle verification ('_validate_system_topology').
        3. Node-specific linting and property inspection ('_validate_node').

        Returns:
            List[Dict[str, Any]]: List of diagnostic issue dictionaries.
        """
        self.issues = []
        self.user_defined_vars = self._collect_user_defined_vars()
        self._validate_system_topology()

        for node in self.nodes:
            if not isinstance(node, dict):
                continue
            self._validate_node(node)

        return self.issues

    def _collect_user_defined_vars(self) -> Set[str]:
        """
        Scans all graph nodes to discover and collect user-defined variables, functions, and iterators.

        Returns:
            Set[str]: Set of user-declared variable and function names available to expressions.
        """
        collected: Set[str] = set()

        for node in self.nodes:
            if not isinstance(node, dict):
                continue
            ntype = str(node.get("type", ""))
            props = node.get("properties", {}) if isinstance(node.get("properties"), dict) else {}

            # 1. Variables/Define Vars
            if ntype in ("Variables/Define Vars", "Define Vars"):
                vars_str = str(props.get("variables", ""))
                if vars_str and vars_str.strip():
                    lines = _split_statements_outside_quotes(vars_str)
                    for line in lines:
                        clean = line.strip()
                        if not clean or clean.startswith(("#", "--")):
                            continue
                        if "=" in clean:
                            lhs = clean.split("=", 1)[0].strip()
                            targets = [t.strip() for t in lhs.split(",")]
                            for target in targets:
                                base_id = target.split(".")[0].strip()
                                if base_id and base_id.isidentifier():
                                    collected.add(base_id)
                                if "." in target:
                                    prop_id = target.split(".", 1)[1].strip()
                                    if prop_id and prop_id.isidentifier():
                                        collected.add(prop_id)

            # 2. System/Script Code
            elif ntype in ("System/Script Code", "Script Code"):
                lang = str(props.get("language", "Python")).strip().lower()
                script = str(props.get("script", ""))
                if script and script.strip():
                    if "python" in lang:
                        try:
                            tree = ast.parse(script, mode="exec")
                            for item in ast.walk(tree):
                                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                                    collected.add(item.name)
                                elif isinstance(item, ast.Name) and isinstance(item.ctx, ast.Store):
                                    collected.add(item.id)
                        except Exception:
                            for m in re.finditer(r'^\s*def\s+([a-zA-Z_]\w*)', script, re.M):
                                collected.add(m.group(1))
                            for m in re.finditer(r'([a-zA-Z_]\w*)\s*=', script):
                                collected.add(m.group(1))
                    else:  # Lua
                        for m in re.finditer(r'\bfunction\s+([a-zA-Z_]\w*)', script):
                            collected.add(m.group(1))
                        for m in re.finditer(r'([a-zA-Z_]\w*)\s*=\s*function\b', script):
                            collected.add(m.group(1))
                        for m in re.finditer(r'(?:^|[;\n])\s*(?:local\s+)?([a-zA-Z_]\w*(?:\s*,\s*[a-zA-Z_]\w*)*)\s*=', script):
                            for var in m.group(1).split(','):
                                var_clean = var.strip()
                                if var_clean and var_clean.isidentifier():
                                    collected.add(var_clean)
                        # Collect Lua numeric for iterators: for var = start, stop[, step] do
                        for m in re.finditer(r'\bfor\s+([a-zA-Z_]\w*)\s*=', script):
                            var_clean = m.group(1).strip()
                            if var_clean and var_clean.isidentifier():
                                collected.add(var_clean)
                        # Collect Lua generic for iterators: for var1, var2 in iter do
                        for m in re.finditer(r'\bfor\s+([a-zA-Z_]\w*(?:\s*,\s*[a-zA-Z_]\w*)*)\s+in\b', script):
                            for var in m.group(1).split(','):
                                var_clean = var.strip()
                                if var_clean and var_clean.isidentifier():
                                    collected.add(var_clean)

            # 3. Loops/MaxLoop
            elif ntype in ("Loops/MaxLoop", "MaxLoop"):
                v = str(props.get("var_name", "j")).strip()
                if v and v.isidentifier():
                    collected.add(v)
                    collected.add(f"max{v}")
                    collected.add(f"{v}_max")

            # 4. Variables/Get Var & Set Var
            elif ntype in ("Variables/Get Var", "Get Var", "Variables/Set Var", "Set Var"):
                v = str(props.get("var_name", "")).strip()
                if v and v.isidentifier():
                    collected.add(v)

            # 5. Variables/Memory
            elif ntype in ("Variables/Memory", "Memory"):
                v = str(props.get("key", "")).strip()
                if v and v.isidentifier():
                    collected.add(v)

        return collected

    @staticmethod
    def _suggest_variable(name: str, valid_vars: Set[str]) -> Optional[str]:
        """
        Provides intelligent variable suggestions for mistyped or missing namespace identifiers.

        Heuristics:
        1. Missing namespace dot prefix (e.g. 'fxpos_x' -> 'fx.pos_x', 'syldur' -> 'syl.dur').
        2. Shorthand 'l_' prefix for line attributes (e.g. 'l_dur' -> 'l.dur').
        3. Fuzzy string matching using difflib against known and user-defined identifiers.

        Args:
            name: Identifier string extracted from expression or script.
            valid_vars: Universe of recognised global and user-defined variables.

        Returns:
            Optional[str]: Suggested correction if a plausible match is found; otherwise None.
        """
        clean_name = name.strip()
        if not clean_name:
            return None

        # 1. Check for missing namespace dot (e.g. fxpos_x -> fx.pos_x, syldur -> syl.dur)
        known_prefixes = ("fx", "syl", "char", "word", "line", "by", "sync", "math", "shape", "ink", "prev", "next")
        common_attrs = {
            "dur", "duration", "start_time", "end_time", "st", "et", "mid", "mid_time",
            "text", "pos_x", "pos_y", "org_x", "org_y", "x", "y", "left", "right", "top",
            "bottom", "center", "middle", "width", "height", "align", "i", "n", "j", "tag"
        }
        for prefix in known_prefixes:
            if clean_name.startswith(prefix + "_"):
                remainder = clean_name[len(prefix) + 1:]
                if remainder:
                    return f"{prefix}.{remainder}"
            elif clean_name.startswith(prefix) and len(clean_name) > len(prefix):
                remainder = clean_name[len(prefix):]
                if remainder in common_attrs:
                    return f"{prefix}.{remainder}"

        # 2. Check for 'l_' shorthand for line (e.g. l_dur -> l.dur, l_start_time -> l.start_time)
        if clean_name.startswith("l_") and len(clean_name) > 2:
            return f"l.{clean_name[2:]}"

        # 3. Fuzzy match against known and user-defined variables
        candidates = [v for v in valid_vars if not v.startswith("_") and len(v) > 1]
        matches = difflib.get_close_matches(clean_name, candidates, n=1, cutoff=0.7)
        if matches:
            return matches[0]

        return None

    def _add_issue(
        self,
        severity: str,
        node_id: Optional[int],
        node_title: str,
        category: str,
        field: str,
        line: Optional[int],
        code_snippet: str,
        error_msg: str,
        suggestion: str,
        msg_key: Optional[str] = None,
        sug_key: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Registers a structured diagnostic issue for frontend inspection and user remediation.

        Args:
            severity: Issue severity ('critical' for execution-blocking errors, 'warning' for linter advice).
            node_id: Numerical ID of the offending node, or None for graph-wide issues.
            node_title: Visual title or display label of the node.
            category: High-level classification ('System', 'Syntax', 'Variables', 'ASS Tags', etc.).
            field: Specific input widget or property field name where the issue originated.
            line: 1-indexed line number within script or multi-line property, if applicable.
            code_snippet: Excerpt of the problematic code or formula.
            error_msg: Human-readable error message in English.
            suggestion: Actionable guidance to fix the error.
            msg_key: i18n translation key for the error message.
            sug_key: i18n translation key for the suggestion.
            params: Interpolation parameters for localised messages.
        """
        self.issues.append({
            "severity": severity,
            "node_id": node_id,
            "node_title": node_title,
            "category": category,
            "field": field,
            "line": line,
            "code_snippet": code_snippet,
            "error_msg": error_msg,
            "suggestion": suggestion,
            "msg_key": msg_key,
            "sug_key": sug_key,
            "params": params or {}
        })

    # =========================================================================
    # 1. System Topology Validation (Red / Critical)
    # =========================================================================

    def _validate_system_topology(self) -> None:
        """
        Validates fundamental graph topology required for compilation and execution.

        Checks performed:
        1. Asserts presence of at least one 'System/Output' node in the active canvas.
        2. Verifies absence of circular dependency cycles among connected data nodes.
        """
        # 1. Check for presence of System/Output node
        output_nodes = [
            n for n in self.nodes
            if isinstance(n, dict) and n.get("type") in ("System/Output", "Output")
        ]
        if not output_nodes:
            self._add_issue(
                severity="critical",
                node_id=None,
                node_title="System/Output",
                category="System",
                field="Topology",
                line=None,
                code_snippet="No System/Output node found",
                error_msg="No 'System/Output' node found in graph.",
                suggestion="Add a 'System/Output' node to compile and generate output subtitles.",
                msg_key="diagnostics.msg.missing_output",
                sug_key="diagnostics.sug.missing_output"
            )

        # 2. Cycle detection on data nodes
        self._check_data_node_cycles()

    def _check_data_node_cycles(self) -> None:
        """
        Detects circular dependencies among connected data nodes using 3-colour DFS graph traversal.

        Algorithm:
        1. Builds an adjacency list mapping source node IDs to destination node IDs from graph links.
        2. Tracks node states in a 'visited' dictionary:
           - 0: Unvisited node.
           - 1: Currently visiting (active in current recursion stack / ancestor path).
           - 2: Fully visited (all descendants explored without detecting cycles).
        3. If an edge reaches a node in state 1 (visiting), a circular dependency cycle is detected.
        4. Reconstructs the exact cycle path ('NodeA -> NodeB -> NodeA') and registers a critical issue.
        """
        node_by_id = {n["id"]: n for n in self.nodes if isinstance(n, dict) and "id" in n}
        adj: Dict[int, List[int]] = {nid: [] for nid in node_by_id}

        for link in self.links:
            if isinstance(link, (list, tuple)) and len(link) >= 4:
                src_id = link[1]
                dst_id = link[3]
                if src_id in adj and dst_id in node_by_id:
                    adj[src_id].append(dst_id)

        visited: Dict[int, int] = {}  # 0=unvisited, 1=visiting, 2=visited

        def dfs(curr: int, path: List[int]) -> bool:
            visited[curr] = 1
            for nxt in adj.get(curr, []):
                if visited.get(nxt, 0) == 1:
                    cycle_nodes = path[path.index(nxt):] + [nxt]
                    cycle_names = [node_by_id.get(cid, {}).get("title") or node_by_id.get(cid, {}).get("type") or str(cid) for cid in cycle_nodes]
                    self._add_issue(
                        severity="critical",
                        node_id=curr,
                        node_title=node_by_id.get(curr, {}).get("title") or "Node",
                        category="System",
                        field="Connections",
                        line=None,
                        code_snippet=" -> ".join(cycle_names),
                        error_msg="Circular dependency detected between data nodes.",
                        suggestion="Break the connection loop between these nodes to allow topological evaluation.",
                        msg_key="diagnostics.msg.circular_dependency",
                        sug_key="diagnostics.sug.circular_dependency"
                    )
                    return True
                elif visited.get(nxt, 0) == 0:
                    if dfs(nxt, path + [nxt]):
                        return True
            visited[curr] = 2
            return False

        for nid in node_by_id:
            if visited.get(nid, 0) == 0:
                dfs(nid, [nid])

    # =========================================================================
    # 2. Node Dispatcher & Specialized Validation
    # =========================================================================

    def _validate_node(self, node: Dict[str, Any]) -> None:
        """
        Dispatches an individual graph node to specialised validation routines based on category and type.

        Routes node properties to dedicated checkers:
        - 'System/Script Code': Dispatched to '_validate_script_node' (Python / Lua).
        - 'Variables/Define Vars': Dispatched to '_validate_defvars_node'.
        - 'Basics/MultiTag': Dispatched to '_validate_multitag_node'.
        - 'Functions/Conditioner': Dispatched to '_validate_conditioner_node'.
        - 'Basics/Only': Dispatched to '_validate_only_node'.
        - 'Shape/Filter': Dispatched to '_validate_filter_node'.
        - 'Basics/Number': Dispatched to '_validate_number_node'.
        - 'Loops/MaxLoop': Dispatched to '_validate_maxloop_node'.
        - 'Loops/Module': Dispatched to '_validate_module_node'.
        - 'Functions/Interpolator': Dispatched to '_validate_interpolator_node'.
        - All unhandled string properties: Dispatched to '_validate_string_property'.

        Args:
            node: Node dictionary containing 'id', 'type', 'title', and 'properties'.
        """
        node_type = str(node.get("type", ""))
        node_id = node.get("id")
        node_title = node.get("title") or node_type or f"Node {node_id}"
        category = node_type.split("/")[0] if "/" in node_type else "General"
        props = node.get("properties", {}) if isinstance(node.get("properties"), dict) else {}

        if node_type in ("System/Script Code", "Script Code"):
            self._validate_script_node(node_id, node_title, category, props)
        elif node_type in ("Variables/Define Vars", "Define Vars"):
            self._validate_defvars_node(node_id, node_title, category, props)
        elif node_type in ("Basics/MultiTag", "MultiTag"):
            self._validate_multitag_node(node_id, node_title, category, props)
        elif node_type in ("Functions/Conditioner", "Conditioner"):
            self._validate_conditioner_node(node_id, node_title, category, props)
        elif node_type in ("Basics/Only", "Only", "Functions/Only") or node_title == "Only":
            self._validate_only_node(node_id, node_title, category, props)
        elif node_type in ("Shape/Filter", "Filter"):
            self._validate_filter_node(node_id, node_title, category, props)
        elif node_type in ("Basics/Number", "Number") or node_title == "Number":
            self._validate_number_node(node_id, node_title, category, props)
        elif node_type in ("Loops/MaxLoop", "MaxLoop") or node_title == "MaxLoop":
            self._validate_maxloop_node(node_id, node_title, category, props)
        elif node_type in ("Loops/Module", "Module") or node_title == "Module":
            self._validate_module_node(node_id, node_title, category, props)
        elif node_type in ("Functions/Interpolator", "Interpolator") or node_title == "Interpolator":
            self._validate_interpolator_node(node_id, node_title, category, props)

        # Inspect all string properties across any node for general syntax/delimiters/dark tags
        for prop_name, prop_val in props.items():
            if isinstance(prop_val, str) and prop_val.strip():
                if node_type in ("System/Script Code", "Script Code") and prop_name == "script":
                    continue  # Script is already validated in _validate_script_node
                if node_type in ("Variables/Define Vars", "Define Vars") and prop_name == "variables":
                    continue  # Variables string is already validated in _validate_defvars_node
                if node_type in ("Basics/MultiTag", "MultiTag") and not prop_val.strip().startswith('\\'):
                    continue  # Value expressions are already validated in _validate_multitag_node
                if node_type in ("Functions/Conditioner", "Conditioner") and prop_name in ("condition", "if_true", "if_false"):
                    continue  # Condition and branches are already validated in _validate_conditioner_node
                if (node_type in ("Basics/Only", "Only", "Functions/Only") or node_title == "Only") and prop_name == "condition":
                    continue  # Condition expression is already validated in _validate_only_node
                if node_type in ("Shape/Filter", "Filter") and prop_name in ("expr_x", "expr_y"):
                    continue  # Filter expressions are already validated in _validate_filter_node
                if (node_type in ("Basics/Number", "Number") or node_title == "Number") and prop_name == "value":
                    continue  # Number value expression is already validated in _validate_number_node
                if (node_type in ("Loops/MaxLoop", "MaxLoop") or node_title == "MaxLoop") and prop_name in ("iterations", "step_ms", "start_time", "end_time", "var_name"):
                    continue  # MaxLoop expressions are already validated in _validate_maxloop_node
                if (node_type in ("Loops/Module", "Module") or node_title == "Module") and prop_name in ("iter", "total", "sub_m"):
                    continue  # Module expressions are already validated in _validate_module_node
                if (node_type in ("Functions/Interpolator", "Interpolator") or node_title == "Interpolator") and prop_name in ("iterator", "total", "accel", "v1", "v2"):
                    continue  # Interpolator expressions are already validated in _validate_interpolator_node
                self._validate_string_property(node_id, node_title, category, prop_name, prop_val)

    def _validate_multitag_node(
        self,
        node_id: Optional[int],
        node_title: str,
        category: str,
        props: Dict[str, Any]
    ) -> None:
        """
        Validates property expressions, delimiters, and tag formats inside MultiTag nodes.

        Args:
            node_id: Numerical ID of the node.
            node_title: Visual label of the node.
            category: High-level classification category.
            props: Dictionary of node properties.
        """
        for prop_name, prop_val in props.items():
            if prop_name in ("tag_type", "type"):
                continue
            if isinstance(prop_val, str) and prop_val.strip():
                clean_val = prop_val.strip()
                if clean_val.startswith('\\'):
                    # Handled by _validate_string_property (ASS tag arguments)
                    continue
                if _is_drawing_or_shape(clean_val):
                    continue
                self._check_delimiters_balance(node_id, node_title, category, prop_name, clean_val)
                self._validate_expression(node_id, node_title, category, prop_name, clean_val)

    def _validate_conditioner_node(
        self,
        node_id: Optional[int],
        node_title: str,
        category: str,
        props: Dict[str, Any]
    ) -> None:
        """
        Validates condition formulas and branch expressions inside Conditioner nodes.

        Checks both the condition expression and the 'if_true' / 'if_false' output branches,
        verifying delimiter balance and routing ASS tag strings to '_validate_string_property'.

        Args:
            node_id: Numerical ID of the node.
            node_title: Visual label of the node.
            category: High-level classification category.
            props: Dictionary of node properties.
        """
        cond = props.get("condition")
        if isinstance(cond, str) and cond.strip():
            clean_cond = cond.strip()
            self._check_delimiters_balance(node_id, node_title, category, "condition", clean_cond)
            self._validate_expression(node_id, node_title, category, "condition", clean_cond)

        for branch_key in ("if_true", "if_false"):
            branch_val = props.get(branch_key)
            if isinstance(branch_val, str) and branch_val.strip():
                clean_branch = branch_val.strip()
                if '\\' in clean_branch:
                    self._validate_string_property(node_id, node_title, category, branch_key, clean_branch)
                elif not _is_drawing_or_shape(clean_branch):
                    self._check_delimiters_balance(node_id, node_title, category, branch_key, clean_branch)

    def _validate_filter_node(
        self,
        node_id: Optional[int],
        node_title: str,
        category: str,
        props: Dict[str, Any]
    ) -> None:
        """
        Validates coordinate transformation expressions ('expr_x', 'expr_y') inside Shape/Filter nodes.

        Args:
            node_id: Numerical ID of the node.
            node_title: Visual label of the node.
            category: High-level classification category.
            props: Dictionary of node properties.
        """
        for expr_key in ("expr_x", "expr_y"):
            expr_val = props.get(expr_key)
            if isinstance(expr_val, str) and expr_val.strip():
                clean_expr = expr_val.strip()
                self._check_delimiters_balance(node_id, node_title, category, expr_key, clean_expr)
                self._validate_expression(node_id, node_title, category, expr_key, clean_expr)

    def _validate_only_node(
        self,
        node_id: Optional[int],
        node_title: str,
        category: str,
        props: Dict[str, Any]
    ) -> None:
        """
        Validates filtering condition expressions inside Basics/Only nodes across all supported formats.

        Args:
            node_id: Numerical ID of the node.
            node_title: Visual label of the node.
            category: High-level classification category.
            props: Dictionary of node properties.
        """
        cond = props.get("condition")
        if isinstance(cond, str) and cond.strip():
            clean_cond = cond.strip()
            # Also check delimiter balance (parentheses, braces) on the condition
            self._check_delimiters_balance(node_id, node_title, category, "condition", clean_cond)
            # Evaluate expression syntax, operands, and variables
            self._validate_expression(node_id, node_title, category, "condition", clean_cond)

    def _validate_number_node(
        self,
        node_id: Optional[int],
        node_title: str,
        category: str,
        props: Dict[str, Any]
    ) -> None:
        """
        Validates numeric value expressions inside Basics/Number nodes.

        Args:
            node_id: Numerical ID of the node.
            node_title: Visual label of the node.
            category: High-level classification category.
            props: Dictionary of node properties.
        """
        val = props.get("value")
        if isinstance(val, str) and val.strip():
            clean_val = val.strip()
            self._check_delimiters_balance(node_id, node_title, category, "value", clean_val)
            self._validate_expression(node_id, node_title, category, "value", clean_val)

    def _validate_maxloop_node(
        self,
        node_id: Optional[int],
        node_title: str,
        category: str,
        props: Dict[str, Any]
    ) -> None:
        """
        Validates loop configuration expressions ('iterations', 'step_ms', 'start_time', 'end_time') inside Loops/MaxLoop nodes.

        Args:
            node_id: Numerical ID of the node.
            node_title: Visual label of the node.
            category: High-level classification category.
            props: Dictionary of node properties.
        """
        for expr_key in ("iterations", "step_ms", "start_time", "end_time"):
            val = props.get(expr_key)
            if isinstance(val, str) and val.strip():
                clean_val = val.strip()
                self._check_delimiters_balance(node_id, node_title, category, expr_key, clean_val)
                self._validate_expression(node_id, node_title, category, expr_key, clean_val)

    def _validate_module_node(
        self,
        node_id: Optional[int],
        node_title: str,
        category: str,
        props: Dict[str, Any]
    ) -> None:
        """
        Validates mathematical modulo expressions ('iter', 'total', 'sub_m') inside Loops/Module nodes.

        Args:
            node_id: Numerical ID of the node.
            node_title: Visual label of the node.
            category: High-level classification category.
            props: Dictionary of node properties.
        """
        for expr_key in ("iter", "total", "sub_m"):
            val = props.get(expr_key)
            if isinstance(val, str) and val.strip():
                clean_val = val.strip()
                self._check_delimiters_balance(node_id, node_title, category, expr_key, clean_val)
                self._validate_expression(node_id, node_title, category, expr_key, clean_val)

    def _validate_interpolator_node(
        self,
        node_id: Optional[int],
        node_title: str,
        category: str,
        props: Dict[str, Any]
    ) -> None:
        """
        Validates interpolation parameters ('iterator', 'total', 'accel', 'v1', 'v2') inside Functions/Interpolator nodes.

        Args:
            node_id: Numerical ID of the node.
            node_title: Visual label of the node.
            category: High-level classification category.
            props: Dictionary of node properties.
        """
        for expr_key in ("iterator", "total", "accel", "v1", "v2"):
            val = props.get(expr_key)
            if isinstance(val, str) and val.strip():
                clean_val = val.strip()
                self._check_delimiters_balance(node_id, node_title, category, expr_key, clean_val)
                self._validate_expression(node_id, node_title, category, expr_key, clean_val)

    # =========================================================================
    # 3. System/Script Code Validation (Python / Lua)
    # =========================================================================

    def _validate_script_node(self, node_id: Optional[int], node_title: str, category: str, props: Dict[str, Any]) -> None:
        """
        Validates embedded script syntax and structure for Python and Lua in System/Script Code nodes.

        Features:
        - Flags empty scripts with non-blocking suggestions.
        - Python: Parses code using 'ast.parse(script, mode="exec")', extracting precise line numbers,
          code snippets, missing colons, unclosed delimiters, and indentation mismatches.
        - Lua: Dispatches to '_validate_lua_script' for multi-stage lexical and structural linting.

        Args:
            node_id: Numerical ID of the node.
            node_title: Visual label of the node.
            category: High-level classification category.
            props: Dictionary of node properties containing 'language' and 'script'.
        """
        lang = str(props.get("language", "Python")).strip().lower()
        script = str(props.get("script", ""))

        if not script or not script.strip():
            self._add_issue(
                severity="warning",
                node_id=node_id,
                node_title=node_title,
                category=category,
                field="script",
                line=1,
                code_snippet="",
                error_msg="The script is empty.",
                suggestion="Write code or connect inputs to process data.",
                msg_key="diagnostics.msg.empty_script",
                sug_key="diagnostics.sug.empty_script"
            )
            return

        if "python" in lang:
            try:
                ast.parse(script, mode="exec")
            except SyntaxError as e:
                snippet = e.text.strip() if e.text else script.splitlines()[e.lineno - 1].strip() if (e.lineno and e.lineno <= len(script.splitlines())) else ""
                msg = str(e.msg)
                suggestion = "Check Python syntax on this line."
                sug_key = "diagnostics.sug.python_syntax_general"
                if "expected ':'" in msg.lower() or snippet.endswith(("if", "else", "elif", "for", "while", "def", "class", "try", "except", "finally")):
                    suggestion = "Add a colon (:) at the end of the statement."
                    sug_key = "diagnostics.sug.python_colon"
                elif "was never closed" in msg.lower() or "unterminated string" in msg.lower() or "eol while scanning" in msg.lower():
                    suggestion = "Close open parentheses, braces, brackets, or quotes."
                    sug_key = "diagnostics.sug.python_close_delims"
                elif "unexpected indent" in msg.lower() or "unindent does not match" in msg.lower():
                    suggestion = "Fix indentation level or whitespace."
                    sug_key = "diagnostics.sug.python_indent"

                self._add_issue(
                    severity="warning",
                    node_id=node_id,
                    node_title=node_title,
                    category=category,
                    field="script (Python)",
                    line=e.lineno,
                    code_snippet=snippet,
                    error_msg=f"Python syntax error: {msg}",
                    suggestion=suggestion,
                    msg_key="diagnostics.msg.python_syntax_error",
                    sug_key=sug_key,
                    params={"msg": msg}
                )
            except Exception as ex:
                self._add_issue(
                    severity="warning",
                    node_id=node_id,
                    node_title=node_title,
                    category=category,
                    field="script (Python)",
                    line=None,
                    code_snippet="",
                    error_msg=f"Error analyzing script: {ex}",
                    suggestion="Check Python code structure.",
                    msg_key="diagnostics.msg.python_analyze_error",
                    sug_key="diagnostics.sug.python_analyze_error",
                    params={"msg": str(ex)}
                )
        elif "lua" in lang:
            self._validate_lua_script(node_id, node_title, category, script)

    def _validate_lua_script(self, node_id: Optional[int], node_title: str, category: str, script: str) -> None:
        """
        Performs multi-stage lexical and structural linting on Lua script code.

        Validation pipeline:
        1. Operator Sanitisation & Syntax Checking:
           - Detects invalid operators transposed from Python/C ('!=', '&&', '||') outside comments and strings,
             suggesting Lua equivalents ('~=', 'and', 'or').
        2. Real Compiler Verification (via lupa):
           - Compiles script using an embedded Lua engine to catch true grammar and block errors without false positives.
           - Maps runtime error messages (e.g. unclosed 'function', 'if', 'for' blocks) to precise source lines.
        3. Fallback Structural Block Balancer:
           - When lupa is unavailable or fails, counts opening block constructs ('function', 'do', 'if ... then')
             against closing 'end' statements, identifying orphan 'end' tokens and unclosed blocks.

        Args:
            node_id: Numerical ID of the node.
            node_title: Visual label of the node.
            category: High-level classification category.
            script: Full source text of the Lua script.
        """
        lines = script.splitlines()

        # 1. Check for invalid operators commonly brought over from Python (outside strings)
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith(("--", "//")):
                continue
            # Strip comments to prevent false positives inside inline comments
            line_no_comments = re.sub(r'--.*$', '', stripped)
            # Strip string literals from line to prevent false positives inside strings
            line_no_strings = re.sub(r'"[^"\\]*(?:\\.[^"\\]*)*"', '""', re.sub(r"'[^'\\]*(?:\\.[^'\\]*)*'", "''", line_no_comments))
            if "!=" in line_no_strings:
                self._add_issue(
                    severity="warning",
                    node_id=node_id,
                    node_title=node_title,
                    category=category,
                    field="script (Lua)",
                    line=idx,
                    code_snippet=stripped,
                    error_msg="Inequality operator '!=' is invalid in Lua.",
                    suggestion="In Lua inequality is written '~=' instead of '!='.",
                    msg_key="diagnostics.msg.lua_invalid_op_ne",
                    sug_key="diagnostics.sug.lua_invalid_op_ne"
                )
            if "&&" in line_no_strings:
                self._add_issue(
                    severity="warning",
                    node_id=node_id,
                    node_title=node_title,
                    category=category,
                    field="script (Lua)",
                    line=idx,
                    code_snippet=stripped,
                    error_msg="Logical operator '&&' is invalid in Lua.",
                    suggestion="In Lua logical conjunction is written 'and' instead of '&&'.",
                    msg_key="diagnostics.msg.lua_invalid_op_and",
                    sug_key="diagnostics.sug.lua_invalid_op_and"
                )
            if "||" in line_no_strings:
                self._add_issue(
                    severity="warning",
                    node_id=node_id,
                    node_title=node_title,
                    category=category,
                    field="script (Lua)",
                    line=idx,
                    code_snippet=stripped,
                    error_msg="Logical operator '||' is invalid in Lua.",
                    suggestion="In Lua logical disjunction is written 'or' instead of '||'.",
                    msg_key="diagnostics.msg.lua_invalid_op_or",
                    sug_key="diagnostics.sug.lua_invalid_op_or"
                )

        # 2. Primary validation: Real Lua compilation via lupa (if available)
        lua = _get_lua_runtime()
        if lua is not None:
            try:
                # Sanitize invalid operators temporarily so Lua compiler can continue
                # and detect block closure errors or downstream syntax issues
                sanitized = re.sub(r'!=', '~=', script)
                sanitized = re.sub(r'&&', ' and ', sanitized)
                sanitized = re.sub(r'\|\|', ' or ', sanitized)
                lua.compile(sanitized)
                return  # Completely valid Lua code, zero false positives!
            except Exception as e:
                err_str = str(e)
                line_no = None
                msg = err_str
                m = re.search(r':(\d+):\s*(.*)', err_str)
                if m:
                    try:
                        line_no = int(m.group(1))
                        msg = m.group(2).strip()
                    except ValueError:
                        pass

                snippet = ""
                if line_no and 1 <= line_no <= len(lines):
                    snippet = lines[line_no - 1].strip()
                elif lines:
                    snippet = lines[-1].strip()

                # Humanize and localize common Lua syntax errors
                m_unclosed = re.search(r"'end'\s+expected\s+\(to\s+close\s+'([^']+)'\s+at\s+line\s+(\d+)\)", msg)
                m_end_eof = re.search(r"'end'\s+expected\s+near\s+<eof>", msg)

                if m_unclosed:
                    block_type = m_unclosed.group(1)
                    open_line = int(m_unclosed.group(2))
                    line_no = open_line
                    if 1 <= open_line <= len(lines):
                        snippet = lines[open_line - 1].strip()
                    error_msg = f"Unclosed '{block_type}' block opened at line {open_line} (missing 'end' statement before end of script)."
                    suggestion = f"Add an 'end' statement to properly close the '{block_type}' block from line {open_line}."
                    msg_key = "diagnostics.msg.lua_unclosed_block_at_line"
                    sug_key = "diagnostics.sug.lua_unclosed_block_at_line"
                    params = {"block": block_type, "open_line": open_line}
                elif m_end_eof:
                    error_msg = "Missing 'end' statement before end of script."
                    suggestion = "Add the missing 'end' statement to close the open block."
                    msg_key = "diagnostics.msg.lua_end_expected_eof"
                    sug_key = "diagnostics.sug.lua_end_expected_eof"
                    params = {}
                else:
                    # Sanitize any raw <eof> compiler jargon into human-readable text
                    clean_msg = re.sub(r'<eof>', 'end of script', msg)
                    suggestion = "Check block structure or syntax on this line."
                    sug_key = "diagnostics.sug.lua_syntax_error"
                    sug_params: Dict[str, Any] = {}
                    if "expected" in clean_msg.lower():
                        suggestion = f"Fix expected syntax: {clean_msg}"
                        sug_key = "diagnostics.sug.lua_expected"
                        sug_params = {"msg": clean_msg}

                    error_msg = f"Lua syntax error: {clean_msg}"
                    msg_key = "diagnostics.msg.lua_syntax_error"
                    params = {"msg": clean_msg, **sug_params}

                self._add_issue(
                    severity="warning",
                    node_id=node_id,
                    node_title=node_title,
                    category=category,
                    field="script (Lua)",
                    line=line_no,
                    code_snippet=snippet,
                    error_msg=error_msg,
                    suggestion=suggestion,
                    msg_key=msg_key,
                    sug_key=sug_key,
                    params=params
                )
                if "end" in msg.lower():
                    return

        # 3. Fallback block balance check (when lupa is not installed or syntax error occurred)
        open_blocks = 0
        # In Lua, blocks closed by 'end' are opened by: function, do, or if ... then
        # 'elseif' and 'else' continue the existing if block and must NOT open a new block!
        block_openers = re.compile(r'\b(function|do)\b|\bif\b.*?\bthen\b')
        block_closers = re.compile(r'\bend\b')

        for idx, line in enumerate(lines, start=1):
            clean_line = re.sub(r'--.*$', '', line)
            clean_line = re.sub(r'"[^"\\]*(?:\\.[^"\\]*)*"', '""', clean_line)
            clean_line = re.sub(r"'[^'\\]*(?:\\.[^'\\]*)*'", "''", clean_line)
            # Remove elseif clauses so they don't count as new block openers
            clean_line = re.sub(r'\belseif\b.*?\bthen\b', '', clean_line)

            num_opens = len(block_openers.findall(clean_line))
            num_closes = len(block_closers.findall(clean_line))
            open_blocks += (num_opens - num_closes)

            if open_blocks < 0:
                self._add_issue(
                    severity="warning",
                    node_id=node_id,
                    node_title=node_title,
                    category=category,
                    field="script (Lua)",
                    line=idx,
                    code_snippet=line.strip(),
                    error_msg="Orphan 'end' statement without prior open block.",
                    suggestion="Remove extra 'end' or open the corresponding block (function/if/for/while).",
                    msg_key="diagnostics.msg.lua_orphan_end",
                    sug_key="diagnostics.sug.lua_orphan_end"
                )
                open_blocks = 0

        if open_blocks > 0:
            self._add_issue(
                severity="warning",
                node_id=node_id,
                node_title=node_title,
                category=category,
                field="script (Lua)",
                line=len(lines),
                code_snippet=lines[-1].strip() if lines else "",
                error_msg=f"Unclosed Lua blocks ({open_blocks} missing 'end' statement(s)).",
                suggestion="Add the required 'end' statements to close open blocks.",
                msg_key="diagnostics.msg.lua_unclosed_blocks",
                sug_key="diagnostics.sug.lua_unclosed_blocks",
                params={"count": open_blocks}
            )

    # =========================================================================
    # 4. Variables/Define Vars Validation
    # =========================================================================

    def _validate_defvars_node(self, node_id: Optional[int], node_title: str, category: str, props: Dict[str, Any]) -> None:
        """
        Validates multi-line variable declarations and assignments inside Variables/Define Vars nodes.

        Validation rules:
        1. Ensures each statement contains a valid assignment operator '='.
        2. Validates left-hand side identifier syntax (allowing comma-separated targets and dot properties like 'fx.pos_x').
        3. Strips trailing Lua ('--') and Python ('#') comments outside quotes.
        4. Verifies non-empty right-hand side expressions and routes them to '_validate_expression'.

        Args:
            node_id: Numerical ID of the node.
            node_title: Visual label of the node.
            category: High-level classification category.
            props: Dictionary of node properties containing 'variables'.
        """
        vars_str = str(props.get("variables", ""))
        if not vars_str or not vars_str.strip():
            return

        lines = _split_statements_outside_quotes(vars_str)

        for idx, line in enumerate(lines, start=1):
            clean_line = line.strip()
            if not clean_line or clean_line.startswith(('#', '--')):
                continue

            if '=' not in clean_line:
                self._add_issue(
                    severity="warning",
                    node_id=node_id,
                    node_title=node_title,
                    category=category,
                    field="variables",
                    line=idx,
                    code_snippet=clean_line,
                    error_msg="Line missing assignment operator '='.",
                    suggestion="Define variables using 'name = expression' syntax.",
                    msg_key="diagnostics.msg.defvars_missing_assign",
                    sug_key="diagnostics.sug.defvars_missing_assign"
                )
                continue

            key, expr = clean_line.split('=', 1)
            key = key.strip()
            expr = expr.strip()

            targets = [k.strip() for k in key.split(',')]
            valid_targets = bool(targets) and all(
                target and all(p.isidentifier() for p in target.split('.'))
                for target in targets
            )
            if not key or not valid_targets:
                self._add_issue(
                    severity="warning",
                    node_id=node_id,
                    node_title=node_title,
                    category=category,
                    field="variables",
                    line=idx,
                    code_snippet=clean_line,
                    error_msg=f"Invalid variable identifier '{key}'.",
                    suggestion="Identifiers must start with a letter or underscore and contain only alphanumeric characters (e.g. 'offset', 'fx.pos_x').",
                    msg_key="diagnostics.msg.defvars_invalid_id",
                    sug_key="diagnostics.sug.defvars_invalid_id",
                    params={"key": key}
                )

            # Strip inline Lua '--' or Python '#' comments outside quotes from expr
            expr_clean = expr
            in_q = None
            comment_start = -1
            prev_c = ""
            for ci, c in enumerate(expr):
                if in_q is not None:
                    if c == in_q and prev_c != '\\':
                        in_q = None
                elif c in ('"', "'") and prev_c != '\\':
                    in_q = c
                elif c == '#' and in_q is None:
                    comment_start = ci
                    break
                elif c == '-' and prev_c == '-' and in_q is None:
                    comment_start = ci - 1
                    break
                prev_c = c
            if comment_start != -1:
                expr_clean = expr[:comment_start].strip()

            if not expr_clean:
                self._add_issue(
                    severity="warning",
                    node_id=node_id,
                    node_title=node_title,
                    category=category,
                    field="variables",
                    line=idx,
                    code_snippet=clean_line,
                    error_msg=f"Variable '{key}' has no expression assigned.",
                    suggestion="Assign a value or formula on the right side of '=' (e.g. 'x = 150').",
                    msg_key="diagnostics.msg.defvars_empty_expr",
                    sug_key="diagnostics.sug.defvars_empty_expr",
                    params={"key": key}
                )
            else:
                self._validate_expression(node_id, node_title, category, f"variables ({key})", expr_clean, line=idx)

    # =========================================================================
    # 5. Delimiters, Dark Tags, and ASS Expression Validation
    # =========================================================================

    def _validate_string_property(
        self,
        node_id: Optional[int],
        node_title: str,
        category: str,
        prop_name: str,
        text: str
    ) -> None:
        """
        Scans a generic string property for delimiter mismatches, invalid Dark Tags, and malformed ASS tag arguments.

        Inspection pipeline:
        1. Delimiter balance verification ('_check_delimiters_balance').
        2. Dark Tag syntax and channel validation ('_check_dark_tags').
        3. ASS tag argument count and format inspection ('_check_ass_tag_arguments').

        Args:
            node_id: Numerical ID of the node.
            node_title: Visual label of the node.
            category: High-level classification category.
            prop_name: Name of the property field being validated.
            text: Raw string expression or subtitle override template.
        """
        # 1. Delimiter balance checks
        self._check_delimiters_balance(node_id, node_title, category, prop_name, text)

        # 2. Dark Tags checks
        self._check_dark_tags(node_id, node_title, category, prop_name, text)

        # 3. ASS Tag arguments validation
        self._check_ass_tag_arguments(node_id, node_title, category, prop_name, text)

    def _check_delimiters_balance(
        self,
        node_id: Optional[int],
        node_title: str,
        category: str,
        prop_name: str,
        text: str
    ) -> None:
        """
        Verifies balanced parentheses '()' and ASS override block braces '{}' with quotation awareness.

        Features:
        - Ignores opening and closing delimiters nested inside single or double quotes.
        - Tracks delimiter counts and detects premature closing tokens (e.g. stack underflow on ')' or '}').
        - Emits localised diagnostic warnings detailing the exact counts of opening vs closing symbols.

        Args:
            node_id: Numerical ID of the node.
            node_title: Visual label of the node.
            category: High-level classification category.
            prop_name: Name of the property field being validated.
            text: Raw string expression or subtitle override template.
        """
        open_parens = 0
        close_parens = 0
        open_braces = 0
        close_braces = 0
        mismatch_paren = False
        mismatch_brace = False

        in_quote: Optional[str] = None
        prev_ch = ""
        paren_stack = 0
        brace_stack = 0

        for ch in text:
            if in_quote is not None:
                if ch == in_quote and prev_ch != '\\':
                    in_quote = None
                prev_ch = ch
                continue

            if ch in ('"', "'") and prev_ch != '\\':
                in_quote = ch
            elif ch == '(':
                open_parens += 1
                paren_stack += 1
            elif ch == ')':
                close_parens += 1
                if paren_stack > 0:
                    paren_stack -= 1
                else:
                    mismatch_paren = True
            elif ch == '{':
                open_braces += 1
                brace_stack += 1
            elif ch == '}':
                close_braces += 1
                if brace_stack > 0:
                    brace_stack -= 1
                else:
                    mismatch_brace = True
            prev_ch = ch

        if open_parens != close_parens or mismatch_paren:
            self._add_issue(
                severity="warning",
                node_id=node_id,
                node_title=node_title,
                category=category,
                field=prop_name,
                line=None,
                code_snippet=text[:80] + ("..." if len(text) > 80 else ""),
                error_msg=f"Unbalanced parentheses ({open_parens} '(' vs {close_parens} ')').",
                suggestion="Ensure each opening '(' has a matching closing ')'.",
                msg_key="diagnostics.msg.delimiters_unbalanced_parens",
                sug_key="diagnostics.sug.delimiters_unbalanced_parens",
                params={"open": open_parens, "close": close_parens}
            )

        if open_braces != close_braces or mismatch_brace:
            self._add_issue(
                severity="warning",
                node_id=node_id,
                node_title=node_title,
                category=category,
                field=prop_name,
                line=None,
                code_snippet=text[:80] + ("..." if len(text) > 80 else ""),
                error_msg=f"Unbalanced ASS block braces ({open_braces} '{{' vs {close_braces} '}}').",
                suggestion="Verify ASS tag blocks are correctly enclosed between {{ and }}.",
                msg_key="diagnostics.msg.delimiters_unbalanced_braces",
                sug_key="diagnostics.sug.delimiters_unbalanced_braces",
                params={"open": open_braces, "close": close_braces}
            )

    def _check_dark_tags(
        self,
        node_id: Optional[int],
        node_title: str,
        category: str,
        prop_name: str,
        text: str
    ) -> None:
        """
        Validates Pyxis Dark Tag extensions including style restoration (~), stochastic variants (\\tagR), and ratio scaling.

        Validation checks:
        1. Style restoration with tilde '~' (e.g. '\\c~', '\\alpha~', '\\bord~'):
           - Enforces that restoration is only applied to valid typographic style attributes ('_VALID_RESTORATION_TAGS')
             or canonical multi-channel colour/alpha tags ('[1-4]+[ca]').
        2. Stochastic Dark Tags '\\tagR(...)':
           - Rejects base tags that do not support randomisation ('_INVALID_STOCHASTIC_BASE_TAGS', such as '\\pos', '\\clip').
        3. Multi-channel colour and alpha channel digits:
           - Enforces that digit sequences in multi-channel tags (e.g. '\\134c') strictly use channels 1 to 4.
        4. Style ratio scaling tags ('\\fscxr', '\\fscyr', '\\fscxyr', '\\fsr'):
           - Rejects non-numeric alphabetic arguments, requiring numeric multipliers or parenthesised formulas.

        Args:
            node_id: Numerical ID of the node.
            node_title: Visual label of the node.
            category: High-level classification category.
            prop_name: Name of the property field being validated.
            text: Raw string expression or subtitle override template.
        """
        if "\\" not in text:
            return

        # 1. Restoration tags with virgulilla ~
        for match in re.finditer(r'\\([a-zA-Z0-9]+)~', text):
            tag_name = match.group(1).lower()
            # Allow individual or multi-channel [1-4]+[ca]
            is_multi_ca = bool(re.match(r'^[1-4]+[ca]$', tag_name))
            if tag_name not in _VALID_RESTORATION_TAGS and not is_multi_ca:
                self._add_issue(
                    severity="warning",
                    node_id=node_id,
                    node_title=node_title,
                    category=category,
                    field=prop_name,
                    line=None,
                    code_snippet=match.group(0),
                    error_msg=f"Invalid restoration Dark Tag: '{match.group(0)}'.",
                    suggestion="Tilde '~' can only be applied to active style properties (color, alpha, fscx, fscy, fs, fsp, bord, shad, blur, frz, fax, fay).",
                    msg_key="diagnostics.msg.dark_tag_invalid_restore",
                    sug_key="diagnostics.sug.dark_tag_invalid_restore",
                    params={"tag": match.group(0)}
                )

        # 2. Stochastic tags \tagR(...)
        for match in re.finditer(r'\\([a-zA-Z0-9]+)R\(', text):
            tag_name = match.group(1).lower()
            if tag_name in _INVALID_STOCHASTIC_BASE_TAGS:
                self._add_issue(
                    severity="warning",
                    node_id=node_id,
                    node_title=node_title,
                    category=category,
                    field=prop_name,
                    line=None,
                    code_snippet=match.group(0) + "...",
                    error_msg=f"Invalid stochastic Dark Tag: '\\{tag_name}R(...)'.",
                    suggestion=f"Tag '\\{tag_name}' does not support stochastic 'R(...)'. Use transformation or color tags (e.g. \\frzR(-30, 30), \\1cR()).",
                    msg_key="diagnostics.msg.dark_tag_invalid_stochastic",
                    sug_key="diagnostics.sug.dark_tag_invalid_stochastic",
                    params={"tag": tag_name}
                )

        # 3. Multi-channel color and alpha digits outside 1-4
        for match in re.finditer(r'\\([0-9]+)([ca])(?![a-zA-Z])', text):
            digits = match.group(1)
            chan_type = match.group(2)
            invalid_digits = [d for d in digits if d not in ('1', '2', '3', '4')]
            if invalid_digits:
                type_str = "color" if chan_type == 'c' else "alpha"
                self._add_issue(
                    severity="warning",
                    node_id=node_id,
                    node_title=node_title,
                    category=category,
                    field=prop_name,
                    line=None,
                    code_snippet=match.group(0),
                    error_msg=f"Invalid {type_str} channel with digit(s) {invalid_digits}.",
                    suggestion="ASS channels only accept digits 1 to 4 (1=primary, 2=karaoke, 3=border, 4=shadow).",
                    msg_key="diagnostics.msg.dark_tag_invalid_channel",
                    sug_key="diagnostics.sug.dark_tag_invalid_channel",
                    params={"type": type_str, "digits": str(invalid_digits)}
                )

        # 4. Style ratio tags with invalid non-numeric, non-parenthesized arguments
        for match in re.finditer(r'\\(fscxr|fscyr|fscxyr|fsr)([a-zA-Z]+)(?=[\\\}\s]|$)', text):
            tag = match.group(1)
            arg = match.group(2)
            self._add_issue(
                severity="warning",
                node_id=node_id,
                node_title=node_title,
                category=category,
                field=prop_name,
                line=None,
                code_snippet=match.group(0),
                error_msg=f"Ratio tag '\\{tag}' with non-numeric argument '{arg}'.",
                suggestion=f"Ratio tags require a numeric multiplier or an expression in parentheses (e.g. \\{tag}1.5 or \\{tag}(syl.dur / 100)).",
                msg_key="diagnostics.msg.dark_tag_invalid_ratio",
                sug_key="diagnostics.sug.dark_tag_invalid_ratio",
                params={"tag": tag, "arg": arg}
            )

    def _check_ass_tag_arguments(
        self,
        node_id: Optional[int],
        node_title: str,
        category: str,
        prop_name: str,
        text: str
    ) -> None:
        """
        Inspects parameters within ASS tag parentheses, verifying argument counts, coordinates, and nested expressions.

        Tag families validated:
        - '\\pos(x, y)' and '\\org(x, y)': Enforces exactly 2 non-empty coordinate arguments.
        - '\\fad(fade_in, fade_out)': Enforces exactly 2 duration parameters.
        - '\\fade(a1, a2, a3, t1, t2, t3, t4)': Enforces exactly 7 arguments.
        - '\\move(x1, y1, x2, y2[, t1, t2])': Enforces either 4 coordinates or 4 coordinates and 2 time keyframes.
        - Plain text tags ('\\fn', '\\r'): Excluded from mathematical expression analysis to prevent false positives.
        - Transform tags ('\\t', '\\te', '\\ts', '\\tc', '\\tw'): Recursively inspects nested tags and validates time/accel formulas.
        - Clipping tags ('\\clip', '\\iclip'): Distinguishes vector drawings from rectangular coordinates.
        - Composite and kinematic tags: Evaluates comma-separated arguments via '_validate_expression'.

        Args:
            node_id: Numerical ID of the node.
            node_title: Visual label of the node.
            category: High-level classification category.
            prop_name: Name of the property field being validated.
            text: Raw string expression or subtitle override template.
        """
        tags = _extract_ass_tags(text)
        for tag_name, inner, start_idx, end_idx in tags:
            tag_name_lower = tag_name.lower()
            inner_clean = inner.strip()

            # Empty checks on mandatory tags
            if tag_name_lower in ("pos", "org"):
                if not inner_clean:
                    self._add_issue(
                        severity="warning",
                        node_id=node_id,
                        node_title=node_title,
                        category=category,
                        field=prop_name,
                        line=None,
                        code_snippet=text[start_idx : end_idx + 1],
                        error_msg=f"Tag '\\{tag_name}()' is empty or missing arguments.",
                        suggestion=f"Tag '\\{tag_name}' requires two coordinates: \\{tag_name}(x, y).",
                        msg_key="diagnostics.msg.tag_empty_required",
                        sug_key="diagnostics.sug.tag_empty_required",
                        params={"tag": tag_name}
                    )
                    continue

                args = _split_top_level_commas(inner_clean)
                valid_count = len([a for a in args if a.strip()])
                if len(args) != 2 or valid_count != 2:
                    self._add_issue(
                        severity="warning",
                        node_id=node_id,
                        node_title=node_title,
                        category=category,
                        field=prop_name,
                        line=None,
                        code_snippet=text[start_idx : end_idx + 1],
                        error_msg=f"Tag '\\{tag_name}' has {valid_count} argument(s) instead of 2.",
                        suggestion=f"Provide exactly 2 coordinates: \\{tag_name}(x, y).",
                        msg_key="diagnostics.msg.tag_arg_count_mismatch",
                        sug_key="diagnostics.sug.tag_arg_count_mismatch",
                        params={"tag": tag_name, "count": valid_count, "expected": 2}
                    )
                for arg in args:
                    if arg:
                        self._validate_expression(node_id, node_title, category, f"{prop_name} (\\{tag_name})", arg)
                continue

            # Fade tags \fad and \fade
            if tag_name_lower == "fad":
                args = _split_top_level_commas(inner_clean)
                valid_count = len([a for a in args if a.strip()])
                if len(args) != 2 or valid_count != 2:
                    self._add_issue(
                        severity="warning",
                        node_id=node_id,
                        node_title=node_title,
                        category=category,
                        field=prop_name,
                        line=None,
                        code_snippet=text[start_idx : end_idx + 1],
                        error_msg=f"Tag '\\fad' has {valid_count} argument(s) instead of 2.",
                        suggestion="Provide exactly 2 durations: \\fad(fade_in, fade_out).",
                        msg_key="diagnostics.msg.tag_arg_count_mismatch",
                        sug_key="diagnostics.sug.tag_arg_count_mismatch",
                        params={"tag": tag_name, "count": valid_count, "expected": 2}
                    )
                for arg in args:
                    if arg:
                        self._validate_expression(node_id, node_title, category, f"{prop_name} (\\{tag_name})", arg)
                continue

            if tag_name_lower == "fade":
                args = _split_top_level_commas(inner_clean)
                valid_count = len([a for a in args if a.strip()])
                if len(args) != 7 or valid_count != 7:
                    self._add_issue(
                        severity="warning",
                        node_id=node_id,
                        node_title=node_title,
                        category=category,
                        field=prop_name,
                        line=None,
                        code_snippet=text[start_idx : end_idx + 1],
                        error_msg=f"Tag '\\fade' has {valid_count} argument(s) instead of 7.",
                        suggestion="Provide exactly 7 arguments: \\fade(a1, a2, a3, t1, t2, t3, t4).",
                        msg_key="diagnostics.msg.tag_arg_count_mismatch",
                        sug_key="diagnostics.sug.tag_arg_count_mismatch",
                        params={"tag": tag_name, "count": valid_count, "expected": 7}
                    )
                for arg in args:
                    if arg:
                        self._validate_expression(node_id, node_title, category, f"{prop_name} (\\{tag_name})", arg)
                continue

            # Move tag \move
            if tag_name_lower == "move":
                args = _split_top_level_commas(inner_clean)
                valid_count = len([a for a in args if a.strip()])
                if len(args) not in (4, 6) or valid_count not in (4, 6) or len(args) != valid_count:
                    self._add_issue(
                        severity="warning",
                        node_id=node_id,
                        node_title=node_title,
                        category=category,
                        field=prop_name,
                        line=None,
                        code_snippet=text[start_idx : end_idx + 1],
                        error_msg=f"Tag '\\move' has {valid_count} argument(s) instead of 4 or 6.",
                        suggestion="Provide 4 coordinates or 4 coordinates and 2 times: \\move(x1, y1, x2, y2[, t1, t2]).",
                        msg_key="diagnostics.msg.tag_arg_count_mismatch",
                        sug_key="diagnostics.sug.tag_arg_count_mismatch",
                        params={"tag": tag_name, "count": valid_count, "expected": "4 or 6"}
                    )
                for arg in args:
                    if arg:
                        self._validate_expression(node_id, node_title, category, f"{prop_name} (\\{tag_name})", arg)
                continue

            # String literal tags \fn (font name) and \r (style name reset) - do NOT treat as math expressions
            if tag_name_lower in ("fn", "r"):
                continue

            # Transform tags \t, \te, \ts, \tc, \tw
            if tag_name_lower in ("t", "te", "ts", "tc", "tw"):
                args = _split_top_level_commas(inner_clean)
                found_tag_payload = False
                for arg in args:
                    if not arg:
                        continue
                    if found_tag_payload or arg.startswith('\\'):
                        found_tag_payload = True
                        # Tag payload: recursively inspect any tags inside
                        self._check_ass_tag_arguments(node_id, node_title, category, prop_name, arg)
                    elif re.match(r'^%(\d+)?(?:\.\d+)?[sdifgaA]$', arg) or re.match(r'^\{[a-zA-Z0-9_]*\}$', arg):
                        # Format placeholder for tags (e.g. \t(0, 200, %s))
                        found_tag_payload = True
                    else:
                        # Time / accel parameter
                        self._validate_expression(node_id, node_title, category, f"{prop_name} (\\{tag_name})", arg)
                continue

            # Clip tags \clip and \iclip
            if tag_name_lower in ("clip", "iclip"):
                # Check if it's a vector clip (starts with drawing command)
                if _is_drawing_or_shape(inner_clean):
                    continue
                args = _split_top_level_commas(inner_clean)
                if len(args) == 4:
                    for arg in args:
                        if arg:
                            self._validate_expression(node_id, node_title, category, f"{prop_name} (\\{tag_name})", arg)
                elif len(args) == 2:
                    self._validate_expression(node_id, node_title, category, f"{prop_name} (\\{tag_name})", args[0])
                    if not _is_drawing_or_shape(args[1]):
                        self._validate_expression(node_id, node_title, category, f"{prop_name} (\\{tag_name})", args[1])
                elif len(args) == 1:
                    if not _is_drawing_or_shape(args[0]):
                        self._validate_expression(node_id, node_title, category, f"{prop_name} (\\{tag_name})", args[0])
                else:
                    self._add_issue(
                        severity="warning",
                        node_id=node_id,
                        node_title=node_title,
                        category=category,
                        field=prop_name,
                        line=None,
                        code_snippet=text[start_idx : end_idx + 1],
                        error_msg=f"Tag '\\{tag_name}' has {len(args)} arguments instead of 4.",
                        suggestion=f"Provide 4 coordinates: \\{tag_name}(x1, y1, x2, y2) or a vector drawing.",
                        msg_key="diagnostics.msg.tag_arg_count_mismatch",
                        sug_key="diagnostics.sug.tag_arg_count_mismatch",
                        params={"tag": tag_name, "count": len(args), "expected": 4}
                    )
                continue

            # General tags with parentheses (e.g. \1c(Colores()), \frz(angle), \fscxyr(2.0))
            args = _split_top_level_commas(inner_clean)
            for arg in args:
                if arg:
                    self._validate_expression(node_id, node_title, category, f"{prop_name} (\\{tag_name})", arg)

    # =========================================================================
    # 6. AST Expression Helper
    # =========================================================================

    def _validate_expression(
        self,
        node_id: Optional[int],
        node_title: str,
        category: str,
        field: str,
        expr_str: str,
        line: Optional[int] = None
    ) -> None:
        """
        Validates mathematical formulas, conditionals, and operands using Python AST in eval mode.

        Validation pipeline:
        1. Boolean literal string short-circuit: Bypasses AST for 'true', 'false', '1', '0', 'yes', 'no'.
        2. Syntax normalisation: Translates '^' to '**', '~=' to '!=', unit shortcuts ('10f', '2r', '2li'),
           hexadecimal ASS colour literals ('&H00FFFFFF&'), and web hex colours ('#FFFFFF').
        3. JavaScript syntax detection: Rejects '&&', '||', and '===' outside quotation marks with Python equivalents.
        4. AST Parsing: Compiles expression with 'ast.parse(sanitized, mode="eval")', classifying syntax errors
           (missing operands, dangling operators, unclosed delimiters, missing 'else' in conditional expressions).
        5. Variable inspection: Dispatches parsed AST tree to '_check_ast_variables'.

        Args:
            node_id: Numerical ID of the node.
            node_title: Visual label of the node.
            category: High-level classification category.
            field: Name or description of the expression field.
            expr_str: Raw expression string.
            line: 1-indexed line number if within a multi-line property.
        """
        clean_expr = expr_str.strip()
        if not clean_expr:
            return

        # 1. Check for boolean literal strings supported by eval_condition_bool
        clean_expr_lower = clean_expr.lower()
        if clean_expr_lower in ("true", "false", "1", "0", "yes", "no", "nil", "t", "f"):
            return

        # 2. Pre-process specific syntax translations supported by eval_condition_bool
        # Exponentiation via ^ (converted to ** in engine)
        sanitized = clean_expr.replace("^", "**")

        # Lua inequality ~= (converted to != in engine)
        sanitized = sanitized.replace("~=", "!=")

        # Skip raw format placeholders (e.g. %s, %d, %f, {0}, {name})
        if re.match(r'^%(\d+)?(?:\.\d+)?[sdifgaA]$', sanitized) or re.match(r'^\{[a-zA-Z0-9_]*\}$', sanitized):
            return

        # Replace unit shortcuts (e.g. 10f, 1.5r, 2li, 3lo, 1m1, 2m2, 1l1, 2l2) with dummy floats / expressions
        sanitized = re.sub(r'(?<![a-zA-Z0-9_#&.%])([+-]?\d+(?:\.\d+)?)\s*[fr]\b', r'\1', sanitized)
        sanitized = re.sub(r'(?<![a-zA-Z0-9_])([+-]?\d+(?:\.\d+)?)\s*(li|lo|m1|m2|l1|l2)\b', r'\1 * \2', sanitized)

        # Allow simple ASS color hex literal &HBBGGRR& or &HBBGGRR without quotes in expressions
        sanitized = re.sub(r'&[hH][0-9a-fA-F]+&?|&[0-9a-fA-F]{6,8}&', r'"&H00FFFFFF&"', sanitized)

        # Allow web hex colors like #FFFFFF or #FFF
        sanitized = re.sub(r'#[0-9a-fA-F]{3,8}\b', r'"#FFFFFF"', sanitized)

        # Allow positional format specifiers embedded in formulas (e.g. %s, %d, {0})
        sanitized = re.sub(r'%(\d+)?(?:\.\d+)?[sdifgaA]\b', r'__dummy_format__', sanitized)
        sanitized = re.sub(r'\{[0-9]+\}', r'__dummy_format__', sanitized)

        stripped_for_ops = _strip_string_literals(clean_expr)

        # 4. Check for JavaScript logical operators && or || outside quotes
        js_match = _EXPR_JS_LOGICAL_OPS_PATTERN.search(stripped_for_ops)
        if js_match:
            op = js_match.group(1)
            py_op = "and" if op == "&&" else "or"
            self._add_issue(
                severity="warning",
                node_id=node_id,
                node_title=node_title,
                category=category,
                field=field,
                line=line,
                code_snippet=clean_expr,
                error_msg=f"Logical operator '{op}' is invalid in Python expressions.",
                suggestion=f"Use Python logical operator '{py_op}' instead of '{op}'.",
                msg_key="diagnostics.msg.expr_invalid_js_op",
                sug_key="diagnostics.sug.expr_invalid_js_op",
                params={"op": op, "py_op": py_op}
            )
            return

        # 5. Check for triple equal === outside quotes
        if _EXPR_TRIPLE_EQUAL_PATTERN.search(stripped_for_ops):
            self._add_issue(
                severity="warning",
                node_id=node_id,
                node_title=node_title,
                category=category,
                field=field,
                line=line,
                code_snippet=clean_expr,
                error_msg="Strict equality operator '===' is invalid in Python expressions.",
                suggestion="Use standard equality operator '==' for comparisons.",
                msg_key="diagnostics.msg.expr_triple_equal",
                sug_key="diagnostics.sug.expr_triple_equal"
            )
            return

        try:
            tree = ast.parse(sanitized, mode="eval")
        except SyntaxError as e:
            # If parsing failed and a single '=' was used outside quotes, suggest '=='
            if _EXPR_ASSIGNMENT_EQUAL_PATTERN.search(stripped_for_ops):
                self._add_issue(
                    severity="warning",
                    node_id=node_id,
                    node_title=node_title,
                    category=category,
                    field=field,
                    line=line,
                    code_snippet=clean_expr,
                    error_msg="Assignment operator '=' found where comparison is expected.",
                    suggestion="Use comparison operator '==' instead of assignment '='.",
                    msg_key="diagnostics.msg.expr_assignment_equal",
                    sug_key="diagnostics.sug.expr_assignment_equal"
                )
                return

            msg = str(e.msg)
            suggestion = "Check mathematical operators and variable names."
            sug_key = "diagnostics.sug.expr_general"
            if "expected 'else'" in msg.lower():
                suggestion = "Python conditional expressions require 'else' (e.g. 'val1 if condition else val2')."
                sug_key = "diagnostics.sug.expr_conditional_else"
            elif "was never closed" in msg.lower() or "unmatched" in msg.lower():
                suggestion = "Close or balance parentheses in the expression."
                sug_key = "diagnostics.sug.expr_unmatched_parens"
            elif _EXPR_TRAILING_OPERATOR_PATTERN.search(clean_expr):
                suggestion = "Expression ends with an operator missing its second operand."
                sug_key = "diagnostics.sug.expr_trailing_op"
            elif _EXPR_LEADING_OPERATOR_PATTERN.search(clean_expr):
                suggestion = "Expression starts with an operator missing its first operand."
                sug_key = "diagnostics.sug.expr_leading_op"
            elif _EXPR_CONSECUTIVE_BINARY_OPS_PATTERN.search(clean_expr):
                suggestion = "Expression has consecutive operators missing intermediate operands."
                sug_key = "diagnostics.sug.expr_consecutive_ops"

            self._add_issue(
                severity="warning",
                node_id=node_id,
                node_title=node_title,
                category=category,
                field=field,
                line=line,
                code_snippet=clean_expr,
                error_msg=f"Invalid expression syntax: {msg}",
                suggestion=suggestion,
                msg_key="diagnostics.msg.expr_invalid_syntax",
                sug_key=sug_key,
                params={"msg": msg}
            )
            return
        except Exception:
            return

        # Check for undefined variables in the expression AST
        self._check_ast_variables(node_id, node_title, category, field, clean_expr, tree, line=line)

    def _check_ast_variables(
        self,
        node_id: Optional[int],
        node_title: str,
        category: str,
        field: str,
        code_snippet: str,
        tree: ast.AST,
        line: Optional[int] = None
    ) -> None:
        """
        Traverses parsed AST expression tree to verify referenced identifiers against known and graph-defined variables.

        Rules:
        - Resolves locally scoped variables in comprehensions (list, set, dict) and lambda expressions.
        - Identifies loaded names ('ast.Load') and verifies presence in '_KNOWN_GLOBAL_VARS' or 'self.user_defined_vars'.
        - For unrecognised variables, invokes '_suggest_variable' to generate intelligent "Did you mean?" suggestions.

        Args:
            node_id: Numerical ID of the node.
            node_title: Visual label of the node.
            category: High-level classification category.
            field: Name or description of the expression field.
            code_snippet: Original code excerpt for display in diagnostics.
            tree: Parsed AST tree of the expression.
            line: Optional line number.
        """
        all_valid_vars = _KNOWN_GLOBAL_VARS | self.user_defined_vars

        # Collect locally scoped names (e.g. comprehensions and lambdas)
        local_names: Set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                for gen in node.generators:
                    for target_node in ast.walk(gen.target):
                        if isinstance(target_node, ast.Name):
                            local_names.add(target_node.id)
            elif isinstance(node, ast.Lambda):
                for arg in node.args.args:
                    local_names.add(arg.arg)

        # Find loaded variable names not defined anywhere
        checked: Set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and isinstance(node.ctx, ast.Load):
                var_name = node.id
                if var_name in checked:
                    continue
                checked.add(var_name)

                if var_name not in all_valid_vars and var_name not in local_names:
                    sug = self._suggest_variable(var_name, all_valid_vars)
                    if sug:
                        error_msg = f"Undefined variable '{var_name}' in expression."
                        suggestion = f"Did you mean '{sug}'?"
                        sug_key = "diagnostics.sug.undefined_var_did_you_mean"
                        params = {"name": var_name, "suggestion": sug}
                    else:
                        error_msg = f"Undefined variable '{var_name}' in expression."
                        suggestion = "Verify the variable name or define it in 'Variables/Define Vars' or a Script node."
                        sug_key = "diagnostics.sug.undefined_var_general"
                        params = {"name": var_name}

                    self._add_issue(
                        severity="warning",
                        node_id=node_id,
                        node_title=node_title,
                        category=category,
                        field=field,
                        line=line,
                        code_snippet=code_snippet,
                        error_msg=error_msg,
                        suggestion=suggestion,
                        msg_key="diagnostics.msg.undefined_var",
                        sug_key=sug_key,
                        params=params
                    )
                elif var_name in _SUBLOOP_GENERATOR_VARS:
                    # Comprobar si el nodo generador requerido existe en el grafo
                    gen_types = _SUBLOOP_GENERATOR_VARS[var_name]
                    has_gen = any(gt in self.present_node_types for gt in gen_types)
                    warn_key = (node_id, var_name)
                    if not has_gen and warn_key not in self._warned_subloop_vars:
                        self._warned_subloop_vars.add(warn_key)
                        gen_name = gen_types[0]
                        self._add_issue(
                            severity="warning",
                            node_id=node_id,
                            node_title=node_title,
                            category=category,
                            field=field,
                            line=line,
                            code_snippet=code_snippet,
                            error_msg=f"Sub-loop variable '{var_name}' used without its generator node ('{gen_name}') in the graph.",
                            suggestion=f"Add a '{gen_name}' node to provide active values for '{var_name}'. It defaults to neutral (0 or 1) when inactive.",
                            msg_key="diagnostics.msg.orphan_subloop_var",
                            sug_key="diagnostics.sug.orphan_subloop_var",
                            params={"var": var_name, "gen": gen_name}
                        )
