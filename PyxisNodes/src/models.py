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
Pyxis Effector - Core Subtitle & Graphical Data Models.

This module defines the canonical data entities that structure ASS dialogue lines,
their decomposed typographic and syllabic elements, spatial metrics, and styles.

Architectural Structure:
- `PyxisUnit`: Canonical base entity for any typographic fragment or timing unit (syllable,
  word, character). Encapsulates geometric metrics, timestamps, neighbour relations, and
  cascading style resolution (override -> line -> defaults).
- `InkMetrics`: Lazy evaluation and caching engine for true visual contour metrics (ink bbox)
  generated from Bézier vector paths (FontVectorEngine / ClipperEngine).
- `InkNamespace`: Context resolution facade for dynamic expressions (ink.syl, ink.char, ink.l).
- `StyleRef`: Parser and normaliser for ASS styles [V4+ Styles], managing numeric types,
  legacy booleans (-1/1), ASS colours (&H00BBGGRR&), and alpha channels.
- `PyxisLine`: Subclass of PyxisUnit representing a complete dialogue line, managing child
  collections (syls, words), margins, inline tag overrides, and global alignment.
- `AdjacentUnitProxy`: Hybrid string/object proxy for canonical directional navigation ('prev', 'next').

Upstream Dependencies:
    - `font_vector_engine.FontVectorEngine`: Vector glyph metrics extraction.
    - `clipper_engine.ClipperEngine`: Geometric bounding box calculation on ASSdraw paths.

Downstream Callers:
    - `ass_parser.py`: Instantiation and population of structures during ASS reading.
    - `karaskel_engine.py`: Spatial layout computation, anchor positioning, and font metrics.
    - `node_engine.GraphEngine`: Injects execution context into the DAG (`line.*`, `syl.*`, `char.*`).
    - `string_evaluator.py`: Resolves variables and attributes in expressions and templates.
    - `node_validator.py`: Validates types and attribute existence at design time.
"""

from typing import Optional

class PyxisUnit:
    """
    Canonical base entity for any typographic, syllabic, or character unit.

    Represents syllables (`syl`), words (`word`), and individual characters (`char`)
    within the structural hierarchy of an ASS subtitle line. Provides transparent access
    to absolute on-screen coordinates, absolute and relative timing intervals,
    and cascading style property resolution.

    Main Attributes:
        i (int): 1-based index of the unit within its container collection.
        n (int): Total count of sibling units in the collection.
        syl_i (int): Parent syllable index (when the unit represents a character).
        word_i (int): Parent word index.
        text (str): Unit text (may contain original ASS tags if not yet stripped).
        text_stripped (str): Plain text stripped of ASS tags and delimiters.
        duration (int): Duration of the unit in milliseconds.
        start_time (int): Absolute start timestamp in milliseconds (referenced to video).
        end_time (int): Absolute end timestamp in milliseconds.
        width (float): Typographic advance width in pixels.
        height (float): Nominal typographic height in pixels.
        descent (float): Font descent metric in pixels.
        extlead (float): External leading metric in pixels.
        left, center, right (float): Absolute horizontal coordinates in screen pixels.
        top, middle, bottom (float): Absolute vertical coordinates in screen pixels.
        x, y (float): Rendering anchor coordinates in pixels.
        prespace, postspace (str): Leading and trailing whitespace characters.
        line (PyxisLine | None): Reference to parent dialogue line.
        word (PyxisUnit | None): Reference to parent word unit.
        chars (list[PyxisUnit]): List of child character units when unit is syllable or word.
        prev (PyxisUnit | None): Previous sibling unit in sequence.
        next (PyxisUnit | None): Next sibling unit in sequence.
        style_override (StyleRef | None): Local style overrides applied by inline tags on the unit.
    """
    def __init__(self):
        self.i, self.n = 1, 1
        self.syl_i, self.word_i = 1, 1
        self.text, self.text_stripped = "", ""
        self.duration = 0
        self.start_time, self.end_time = 0, 0
        self._mid_time = None

        self.syl_start, self.syl_end, self.syl_mid = 0, 0, 0
        self.word_start, self.word_end, self.word_mid = 0, 0, 0
        self.char_start, self.char_end, self.char_mid = 0, 0, 0

        self.width, self.height, self.descent, self.extlead = 0.0, 0.0, 0.0, 0.0
        self.left, self.center, self.right = 0.0, 0.0, 0.0
        self.top, self.middle, self.bottom = 0.0, 0.0, 0.0
        self.x, self.y = 0.0, 0.0

        self.prespace, self.postspace = "", ""
        self.prespacewidth, self.postspacewidth = 0.0, 0.0

        self.line, self.word = None, None
        self._syl_obj = None
        self.chars = []
        self.prev = None
        self.next = None
        self.style_override = None

    @property
    def is_first(self):
        return (self.i == 1) or (self.prev is None)

    @property
    def is_last(self):
        return (self.i == self.n) or (self.next is None)

    @property
    def has_prev(self):
        return self.prev is not None

    @property
    def has_next(self):
        return self.next is not None

    @property
    def dur(self):
        return self.duration

    @dur.setter
    def dur(self, val):
        self.duration = val

    @property
    def syl(self):
        if self._syl_obj is not None:
            return self._syl_obj
        return self.i

    @syl.setter
    def syl(self, val):
        self._syl_obj = val

    @property
    def mid_time(self):
        if getattr(self, '_mid_time', None) is not None:
            return self._mid_time
        return (self.start_time + self.end_time) / 2.0

    @mid_time.setter
    def mid_time(self, val):
        self._mid_time = val

    @property
    def descend(self):
        return self.descent

    @descend.setter
    def descend(self, val):
        self.descent = float(val)

    @property
    def ink(self):
        if getattr(self, '_ink_obj', None) is None:
            self._ink_obj = InkMetrics(self)
        return self._ink_obj

    @property
    def text_spacestripped(self):
        if getattr(self, '_text_spacestripped', None) is not None:
            return self._text_spacestripped
        return self.text_stripped.strip()

    @text_spacestripped.setter
    def text_spacestripped(self, val):
        self._text_spacestripped = str(val)

    @property
    def color1(self):
        if self.style_override is not None:
            return self.style_override.color1
        return self.line.color1 if self.line else "&H00FFFFFF&"

    @property
    def color2(self):
        if self.style_override is not None:
            return self.style_override.color2
        return self.line.color2 if self.line else "&H000000FF&"

    @property
    def color3(self):
        if self.style_override is not None:
            return self.style_override.color3
        return self.line.color3 if self.line else "&H00000000&"

    @property
    def color4(self):
        if self.style_override is not None:
            return self.style_override.color4
        return self.line.color4 if self.line else "&H00000000&"

    @property
    def alpha1(self):
        if self.style_override is not None:
            return self.style_override.alpha1
        return self.line.alpha1 if self.line else "&H00&"

    @property
    def alpha2(self):
        if self.style_override is not None:
            return self.style_override.alpha2
        return self.line.alpha2 if self.line else "&H00&"

    @property
    def alpha3(self):
        if self.style_override is not None:
            return self.style_override.alpha3
        return self.line.alpha3 if self.line else "&H00&"

    @property
    def alpha4(self):
        if self.style_override is not None:
            return self.style_override.alpha4
        return self.line.alpha4 if self.line else "&H00&"

    @property
    def outline(self):
        if self.style_override is not None:
            return self.style_override.outline
        return self.line.outline if self.line else 2.0

    @property
    def shadow(self):
        if self.style_override is not None:
            return self.style_override.shadow
        return self.line.shadow if self.line else 0.0

    @property
    def fontname(self):
        if self.style_override is not None:
            return self.style_override.fontname
        return self.line.fontname if self.line else "Arial"

    @property
    def fontsize(self):
        if self.style_override is not None:
            return self.style_override.fontsize
        return self.line.fontsize if self.line else 40.0

    @property
    def bold(self):
        if self.style_override is not None:
            return self.style_override.bold
        return self.line.bold if self.line else False

    @property
    def italic(self):
        if self.style_override is not None:
            return self.style_override.italic
        return self.line.italic if self.line else False

    @property
    def underline(self):
        if self.style_override is not None:
            return self.style_override.underline
        return getattr(self.line, 'underline', False) if self.line else False

    @property
    def strikeout(self):
        if self.style_override is not None:
            return self.style_override.strikeout
        return getattr(self.line, 'strikeout', False) if self.line else False

    @property
    def scale_x(self):
        if self.style_override is not None:
            return self.style_override.scale_x
        return self.line.scale_x if self.line else 100.0

    @property
    def scale_y(self):
        if self.style_override is not None:
            return self.style_override.scale_y
        return self.line.scale_y if self.line else 100.0

    @property
    def spacing(self):
        if self.style_override is not None:
            return self.style_override.spacing
        return self.line.spacing if self.line else 0.0

    @property
    def frz(self):
        if self.style_override is not None:
            return self.style_override.frz
        return getattr(self.line, 'frz', 0.0) if self.line else 0.0

    @property
    def frx(self):
        if self.style_override is not None:
            return self.style_override.frx
        return getattr(self.line, 'frx', 0.0) if self.line else 0.0

    @property
    def fry(self):
        if self.style_override is not None:
            return self.style_override.fry
        return getattr(self.line, 'fry', 0.0) if self.line else 0.0

    @property
    def fax(self):
        if self.style_override is not None:
            return self.style_override.fax
        return getattr(self.line, 'fax', 0.0) if self.line else 0.0

    @property
    def fay(self):
        if self.style_override is not None:
            return self.style_override.fay
        return getattr(self.line, 'fay', 0.0) if self.line else 0.0

    @property
    def align(self):
        if self.style_override is not None and self.style_override.has_align:
            return self.style_override.align
        return getattr(self.line, 'align', 2) if self.line else 2

    @property
    def pos_x(self):
        if getattr(self, '_pos_x', None) is not None:
            return self._pos_x
        if self.style_override is not None and self.style_override.has_pos:
            return self.style_override.pos_x
        return self.x

    @pos_x.setter
    def pos_x(self, val):
        self._pos_x = float(val) if val is not None else None

    @property
    def pos_y(self):
        if getattr(self, '_pos_y', None) is not None:
            return self._pos_y
        if self.style_override is not None and self.style_override.has_pos:
            return self.style_override.pos_y
        return self.y

    @pos_y.setter
    def pos_y(self, val):
        self._pos_y = float(val) if val is not None else None

    @property
    def org_x(self):
        if getattr(self, '_org_x', None) is not None:
            return self._org_x
        if self.style_override is not None and self.style_override.has_org:
            return self.style_override.org_x
        if self.line and self.line is not self and getattr(self.line, 'has_org', False):
            return self.line.org_x
        return self.center

    @org_x.setter
    def org_x(self, val):
        self._org_x = float(val) if val is not None else None

    @property
    def org_y(self):
        if getattr(self, '_org_y', None) is not None:
            return self._org_y
        if self.style_override is not None and self.style_override.has_org:
            return self.style_override.org_y
        if self.line and self.line is not self and getattr(self.line, 'has_org', False):
            return self.line.org_y
        return self.middle

    @org_y.setter
    def org_y(self, val):
        self._org_y = float(val) if val is not None else None

class InkMetrics:
    """
    Lazy evaluation and caching engine for true visual contour ink bounding box metrics.

    Unlike standard typographic metrics in `PyxisUnit` (which represent font advance bounding boxes
    and may include empty ascender/descender whitespace), `InkMetrics` calculates the exact bounding box
    occupied by the rendered glyph ink strokes on screen.

    Evaluation Mechanism:
        - On-demand lazy computation: Vector path processing is deferred until the first access
          to any geometric property (`left`, `top`, `width`, etc.).
        - Internal caching: Once computed (`_computed = True`), values are stored in memory.
        - Vectorisation: Invokes `FontVectorEngine.extract_font_params()` and `FontVectorEngine.get_metrics()`.
          If the vector engine provides a Bézier path without precomputed ink metrics, falls back
          to `ClipperEngine.get_bbox()` to measure the clip contour.
        - Typographic fallback: If vectorisation fails (e.g. invisible whitespace, unsupported glyphs,
          or backend error), logs a warning and safely falls back to typographic coordinates
          of the enclosing unit (`u.left`, `u.top`, `u.width`, etc.).

    Exposed Properties:
        left, right, top, bottom (float): Extreme pixel ink boundaries on screen.
        width, height (float): Net visual stroke dimensions.
        center, middle (float): Net visual centroid of the glyph.
        x, y (float): Direct aliases for center and middle.
    """
    def __init__(self, unit=None):
        self._unit = unit
        self._computed = False
        self._left = 0.0
        self._top = 0.0
        self._right = 0.0
        self._bottom = 0.0
        self._width = 0.0
        self._height = 0.0
        self._center = 0.0
        self._middle = 0.0
        self._x = 0.0
        self._y = 0.0

    def _compute(self):
        if self._computed:
            return
        self._computed = True
        u = self._unit
        if not u:
            return

        text = getattr(u, 'text_stripped', getattr(u, 'text', ''))
        u_c_raw = float(getattr(u, 'center', 0.0))
        u_x_raw = float(getattr(u, 'x', 0.0))
        u_l_raw = float(getattr(u, 'left', 0.0))
        u_r_raw = float(getattr(u, 'right', 0.0))
        if u_c_raw != 0.0:
            u_center = u_c_raw
        elif u_x_raw != 0.0:
            u_center = u_x_raw
        elif u_l_raw != 0.0 or u_r_raw != 0.0:
            u_center = (u_l_raw + u_r_raw) / 2.0
        else:
            u_center = 0.0

        u_m_raw = float(getattr(u, 'middle', 0.0))
        u_y_raw = float(getattr(u, 'y', 0.0))
        u_t_raw = float(getattr(u, 'top', 0.0))
        u_b_raw = float(getattr(u, 'bottom', 0.0))
        if u_m_raw != 0.0:
            u_middle = u_m_raw
        elif u_y_raw != 0.0:
            u_middle = u_y_raw
        elif u_t_raw != 0.0 or u_b_raw != 0.0:
            u_middle = (u_t_raw + u_b_raw) / 2.0
        else:
            u_middle = 0.0
        u_width = float(getattr(u, 'width', 0.0))
        u_height = float(getattr(u, 'height', 0.0))
        u_left = float(getattr(u, 'left', u_center - u_width / 2.0))
        u_right = float(getattr(u, 'right', u_center + u_width / 2.0))
        u_top = float(getattr(u, 'top', u_middle - u_height / 2.0))
        u_bottom = float(getattr(u, 'bottom', u_middle + u_height / 2.0))

        if not text or not str(text).strip():
            self._left = u_left
            self._right = u_right
            self._top = u_top
            self._bottom = u_bottom
            self._width = u_width
            self._height = u_height
            self._center = u_center
            self._middle = u_middle
            self._x = u_center
            self._y = u_middle
            return

        try:
            from font_vector_engine import FontVectorEngine
            from clipper_engine import ClipperEngine

            line = getattr(u, 'line', None) if not hasattr(u, 'style_name') else u
            styleref = getattr(line, 'styleref', None) if line else getattr(u, 'styleref', None)

            font_params = FontVectorEngine.extract_font_params(
                text=str(text),
                context={"active_unit": u, "active_line": line, "unit": u, "line": line, "styleref": styleref}
            )

            metrics = FontVectorEngine.get_metrics(
                text=str(font_params["text"]),
                font_name=font_params["font_name"],
                font_size=font_params["font_size"],
                bold=font_params["bold"],
                italic=font_params["italic"],
                scale=font_params["scale"],
                scale_x=font_params["scale_x"],
                scale_y=font_params["scale_y"],
                spacing=font_params["spacing"],
                anchor="typographic"
            )

            if metrics and metrics.ink_width > 0:
                self._left = round(u_center + metrics.ink_min_x, 3)
                self._right = round(u_center + metrics.ink_max_x, 3)
                self._top = round(u_middle + metrics.ink_min_y, 3)
                self._bottom = round(u_middle + metrics.ink_max_y, 3)
                self._width = round(metrics.ink_width, 3)
                self._height = round(metrics.ink_height, 3)
                self._center = round(u_center + metrics.delta_x, 3)
                self._middle = round(u_middle + metrics.delta_y, 3)
                self._x = self._center
                self._y = self._middle
            elif metrics and metrics.shape:
                from clipper_engine import ClipperEngine
                min_x, min_y, max_x, max_y, cx, cy, w, h = ClipperEngine.get_bbox(metrics.shape)
                self._left = round(u_center + min_x, 3)
                self._right = round(u_center + max_x, 3)
                self._top = round(u_middle + min_y, 3)
                self._bottom = round(u_middle + max_y, 3)
                self._width = round(w, 3)
                self._height = round(h, 3)
                self._center = round(u_center + cx, 3)
                self._middle = round(u_middle + cy, 3)
                self._x = self._center
                self._y = self._middle
            else:
                raise ValueError("Empty vector shape")
        except Exception as e:
            print(f"[Pyxis InkMetrics Warning] Error computing glyph ink contour for text '{text}': {e}. Falling back to typographic bounding box.", flush=True)
            self._left = u_left
            self._right = u_right
            self._top = u_top
            self._bottom = u_bottom
            self._width = u_width
            self._height = u_height
            self._center = u_center
            self._middle = u_middle
            self._x = u_center
            self._y = u_middle

    @property
    def left(self): self._compute(); return self._left
    @property
    def right(self): self._compute(); return self._right
    @property
    def top(self): self._compute(); return self._top
    @property
    def bottom(self): self._compute(); return self._bottom
    @property
    def width(self): self._compute(); return self._width
    @property
    def height(self): self._compute(); return self._height
    @property
    def center(self): self._compute(); return self._center
    @property
    def middle(self): self._compute(); return self._middle
    @property
    def x(self): self._compute(); return self._x
    @property
    def y(self): self._compute(); return self._y

    def __getitem__(self, key):
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(key)

    def get(self, key, default=0.0):
        if hasattr(self, key):
            return getattr(self, key)
        return default

    def __repr__(self):
        return f"<InkMetrics w={self.width} h={self.height} center=({self.center},{self.middle})>"


class InkNamespace:
    """
    Context resolution facade for ink metrics (InkMetrics) in dynamic expressions and templates.

    Enables both AST mathematical formulae (`_eval_num_expr`) and macros evaluated by `string_evaluator.py`
    to access visual glyph metrics transparently across hierarchies:
        - `ink.width`, `ink.center`, `ink.top`: Resolves on the active unit in context.
        - `ink.syl.*`: Forces resolution on the active syllable (or parent syllable if unit is a character).
        - `ink.char.*`: Forces resolution on the active character.
        - `ink.word.*`: Forces resolution on the active word.
        - `ink.line.*` or `ink.l.*`: Forces resolution on the complete line.

    If a requested hierarchy does not exist or has no visible strokes, returns an empty `InkMetrics(None)`
    with neutral numeric values (0.0), preventing attribute access exceptions.
    """
    def __init__(self, context=None):
        self._context = context or {}

    @property
    def l(self):
        line = self._context.get('active_line') or self._context.get('line')
        if not line and self._context.get('active_unit'):
            line = getattr(self._context.get('active_unit'), 'line', None)
        return line.ink if line else InkMetrics(None)

    @property
    def line(self):
        return self.l

    @property
    def syl(self):
        syl_obj = self._context.get('syl')
        if not syl_obj and self._context.get('active_unit'):
            u = self._context.get('active_unit')
            if getattr(u, 'unit_type', None) == 'char':
                syl_obj = getattr(u, 'syl', None)
            elif getattr(u, 'unit_type', None) != 'word':
                syl_obj = u
        return syl_obj.ink if syl_obj else InkMetrics(None)

    @property
    def char(self):
        char_obj = self._context.get('char')
        if not char_obj and self._context.get('active_unit'):
            u = self._context.get('active_unit')
            if getattr(u, 'unit_type', None) in ('char', 'character'):
                char_obj = u
        return char_obj.ink if char_obj else InkMetrics(None)

    @property
    def word(self):
        word_obj = self._context.get('word')
        if not word_obj and self._context.get('active_unit'):
            u = self._context.get('active_unit')
            if getattr(u, 'unit_type', None) == 'word':
                word_obj = u
        return word_obj.ink if word_obj else InkMetrics(None)

    def _active_ink(self):
        u = self._context.get('active_unit') or self._context.get('syl') or self._context.get('char') or self._context.get('word') or self._context.get('line')
        return u.ink if u else InkMetrics(None)

    @property
    def left(self): return self._active_ink().left
    @property
    def right(self): return self._active_ink().right
    @property
    def top(self): return self._active_ink().top
    @property
    def bottom(self): return self._active_ink().bottom
    @property
    def width(self): return self._active_ink().width
    @property
    def height(self): return self._active_ink().height
    @property
    def center(self): return self._active_ink().center
    @property
    def middle(self): return self._active_ink().middle
    @property
    def x(self): return self._active_ink().x
    @property
    def y(self): return self._active_ink().y

    def __getitem__(self, key):
        if hasattr(self, key):
            return getattr(self, key)
        raise KeyError(key)

    def get(self, key, default=0.0):
        if hasattr(self, key):
            return getattr(self, key)
        return default

class StyleRef:
    """
    Canonical parser and encapsulator for ASS styles (`[V4+ Styles]`).

    Translates style formatting definitions from the ASS file into strongly typed Python properties,
    homogenising canonical field names (CamelCase / lowercase) and managing safe defaults.

    Conversions Performed:
        - Booleans: Maps legacy ASS flags ('-1', '1', 'true', 'True') to Python booleans
          for `bold`, `italic`, `underline`, `strikeout`.
        - Numerics: Performs safe casting with fallback upon corrupted or missing fields
          for `fontsize` (default 40.0), `scale_x`/`scale_y` (default 100.0), `spacing` (0.0),
          `angle`/`frz` (0.0), `outline`/`bord` (2.0), `shadow`/`shad` (0.0), and `align` (2).
        - Colours and Alphas: Retains canonical ASS `&HAABBGGRR&` representation for `color1` (primary),
          `color2` (secondary/karaoke), `color3` (outline), and `color4` (shadow), alongside individual channels `alpha1..4`.
    """
    def __init__(self, style_dict: Optional[dict] = None):
        if not style_dict:
            style_dict = {}
        self.fontname = str(style_dict.get('Fontname', style_dict.get('fontname', 'Arial')))
        try:
            self.fontsize = float(style_dict.get('Fontsize', style_dict.get('fontsize', 40)))
        except Exception:
            self.fontsize = 40.0
        b_val = style_dict.get('Bold', style_dict.get('bold', False))
        self.bold = str(b_val).strip() in ['1', '-1', 'true', 'True'] if not isinstance(b_val, bool) else b_val
        i_val = style_dict.get('Italic', style_dict.get('italic', False))
        self.italic = str(i_val).strip() in ['1', '-1', 'true', 'True'] if not isinstance(i_val, bool) else i_val
        u_val = style_dict.get('Underline', style_dict.get('underline', False))
        self.underline = str(u_val).strip() in ['1', '-1', 'true', 'True'] if not isinstance(u_val, bool) else u_val
        s_val = style_dict.get('StrikeOut', style_dict.get('Strikeout', style_dict.get('strikeout', False)))
        self.strikeout = str(s_val).strip() in ['1', '-1', 'true', 'True'] if not isinstance(s_val, bool) else s_val
        try:
            self.scale_x = float(style_dict.get('ScaleX', style_dict.get('scale_x', 100)))
        except Exception:
            self.scale_x = 100.0
        try:
            self.scale_y = float(style_dict.get('ScaleY', style_dict.get('scale_y', 100)))
        except Exception:
            self.scale_y = 100.0
        try:
            self.spacing = float(style_dict.get('Spacing', style_dict.get('spacing', 0)))
        except Exception:
            self.spacing = 0.0
        try:
            self.angle = float(style_dict.get('Angle', style_dict.get('angle', style_dict.get('frz', 0.0))))
        except Exception:
            self.angle = 0.0
        self.frz = self.angle
        try:
            self.align = int(float(style_dict.get('Alignment', style_dict.get('align', 2))))
        except Exception:
            self.align = 2

        self.color1 = str(style_dict.get('PrimaryColour', style_dict.get('color1', '&H00FFFFFF&')))
        self.color2 = str(style_dict.get('SecondaryColour', style_dict.get('color2', '&H000000FF&')))
        self.color3 = str(style_dict.get('OutlineColour', style_dict.get('color3', '&H00000000&')))
        self.color4 = str(style_dict.get('BackColour', style_dict.get('color4', '&H00000000&')))

        self.alpha1 = str(style_dict.get('alpha1', '&H00&'))
        self.alpha2 = str(style_dict.get('alpha2', '&H00&'))
        self.alpha3 = str(style_dict.get('alpha3', '&H00&'))
        self.alpha4 = str(style_dict.get('alpha4', '&H00&'))

        try:
            self.outline = float(style_dict.get('Outline', style_dict.get('outline', style_dict.get('bord', 2.0))))
        except Exception:
            self.outline = 2.0
        self.bord = self.outline
        try:
            self.shadow = float(style_dict.get('Shadow', style_dict.get('shadow', style_dict.get('shad', 0.0))))
        except Exception:
            self.shadow = 0.0
        self.shad = self.shadow

class PyxisLine(PyxisUnit):
    """
    Subclass of PyxisUnit representing a complete ASS dialogue event line.

    Encapsulates line-level metadata, timing intervals, layout bounding boxes, and collections
    of child syllabic and word units (`syls`, `words`). Provides cascading style resolution,
    managing inline overrides (`style_override`) against the line's base stylesheet (`styleref`).

    Architectural Responsibilities:
        - Serves as the root container in the Karaskel layout hierarchy.
        - Manages ASS event header fields (layer, actor, effect, margins, comment state).
        - Holds explicit tag overrides parsed from line prefixes (\\pos, \\org, \\move, \\an).
        - Acts as polymorphic target (`self.line = self`) for uniform attribute access.

    Attributes:
        layer (int): ASS rendering layer order (0..N).
        style_name (str): Canonical style identifier matching [V4+ Styles].
        actor (str): Speaker or character identifier string.
        effect (str): Custom effect descriptor field.
        raw_text (str): Complete unstripped dialogue text including all inline ASS tags.
        margin_l, margin_r, margin_v (int): Explicit margins in screen pixels (left, right, vertical).
        margin_t, margin_b (int): Granular top and bottom margins.
        is_selected (bool): Selection flag within the host subtitle editor (Aegisub).
        is_comment (bool): True if the event is a non-rendered comment line.
        syls (list[PyxisUnit]): Decomposed syllabic units parsed by `ass_parser.py`.
        words (list[PyxisUnit]): Decomposed lexical word units.
        styleref (StyleRef): Base typographic style definition assigned to this line.
        style_override (StyleRef | None): Local override containing inline tag overrides.
        has_pos (bool): True if line has explicit \\pos(x, y) coordinates.
        has_org (bool): True if line has explicit \\org(x, y) pivot coordinates.
        has_move (bool): True if line specifies trajectory motion via \\move.
        align_override (int | None): Explicit alignment override from \\an or \\a tags.
    """
    def __init__(self):
        super().__init__()
        self.layer, self.style_name, self.actor, self.effect, self.raw_text = 0, "Default", "", "", ""
        self.margin_l, self.margin_r, self.margin_v = 0, 0, 0
        self.margin_t, self.margin_b = 0, 0
        self.is_selected = False
        self.is_comment = False
        self.syls, self.words = [], []
        self.line = self
        self.styleref = StyleRef()
        self.style_override = None
        self.has_style_override = False
        self.has_pos = False
        self._pos_x = None
        self._pos_y = None
        self.has_org = False
        self._org_x = None
        self._org_y = None
        self.has_move = False
        self.move_x1 = 0.0
        self.move_y1 = 0.0
        self.move_x2 = 0.0
        self.move_y2 = 0.0
        self.move_t1 = None
        self.move_t2 = None
        self.align_override = None

    @property
    def style(self):
        return self.style_name

    @style.setter
    def style(self, val):
        self.style_name = str(val)

    @property
    def color1(self): return self.style_override.color1 if self.style_override else self.styleref.color1
    @property
    def color2(self): return self.style_override.color2 if self.style_override else self.styleref.color2
    @property
    def color3(self): return self.style_override.color3 if self.style_override else self.styleref.color3
    @property
    def color4(self): return self.style_override.color4 if self.style_override else self.styleref.color4
    @property
    def alpha1(self): return self.style_override.alpha1 if self.style_override else self.styleref.alpha1
    @property
    def alpha2(self): return self.style_override.alpha2 if self.style_override else self.styleref.alpha2
    @property
    def alpha3(self): return self.style_override.alpha3 if self.style_override else self.styleref.alpha3
    @property
    def alpha4(self): return self.style_override.alpha4 if self.style_override else self.styleref.alpha4
    @property
    def outline(self): return self.style_override.outline if self.style_override else self.styleref.outline
    @property
    def bord(self): return self.outline
    @property
    def shadow(self): return self.style_override.shadow if self.style_override else self.styleref.shadow
    @property
    def shad(self): return self.shadow
    @property
    def fontname(self): return self.style_override.fontname if self.style_override else self.styleref.fontname
    @property
    def fontsize(self): return self.style_override.fontsize if self.style_override else self.styleref.fontsize
    @property
    def bold(self): return self.style_override.bold if self.style_override else self.styleref.bold
    @property
    def italic(self): return self.style_override.italic if self.style_override else self.styleref.italic
    @property
    def underline(self): return self.style_override.underline if self.style_override else getattr(self.styleref, 'underline', False)
    @property
    def strikeout(self): return self.style_override.strikeout if self.style_override else getattr(self.styleref, 'strikeout', False)
    @property
    def scale_x(self): return self.style_override.scale_x if self.style_override else self.styleref.scale_x
    @property
    def scale_y(self): return self.style_override.scale_y if self.style_override else self.styleref.scale_y
    @property
    def spacing(self): return self.style_override.spacing if self.style_override else self.styleref.spacing
    @property
    def frz(self): return self.style_override.frz if self.style_override else getattr(self.styleref, 'angle', getattr(self.styleref, 'frz', 0.0))
    @property
    def angle(self): return self.frz
    @property
    def frx(self): return self.style_override.frx if self.style_override else 0.0
    @property
    def fry(self): return self.style_override.fry if self.style_override else 0.0
    @property
    def fax(self): return self.style_override.fax if self.style_override else 0.0
    @property
    def fay(self): return self.style_override.fay if self.style_override else 0.0
    @property
    def align(self):
        if self.style_override and self.style_override.has_align:
            return self.style_override.align
        if self.align_override is not None:
            return self.align_override
        return getattr(self.styleref, 'align', 2)

    @align.setter
    def align(self, val):
        self.align_override = int(val) if val is not None else None

    @property
    def pos_x(self):
        if getattr(self, '_pos_x', None) is not None:
            return self._pos_x
        if self.style_override and self.style_override.has_pos:
            return self.style_override.pos_x
        return self.x

    @pos_x.setter
    def pos_x(self, val):
        self._pos_x = float(val) if val is not None else None

    @property
    def pos_y(self):
        if getattr(self, '_pos_y', None) is not None:
            return self._pos_y
        if self.style_override and self.style_override.has_pos:
            return self.style_override.pos_y
        return self.y

    @pos_y.setter
    def pos_y(self, val):
        self._pos_y = float(val) if val is not None else None

    @property
    def org_x(self):
        if getattr(self, '_org_x', None) is not None:
            return self._org_x
        if self.style_override and self.style_override.has_org:
            return self.style_override.org_x
        return self.center

    @org_x.setter
    def org_x(self, val):
        self._org_x = float(val) if val is not None else None

    @property
    def org_y(self):
        if getattr(self, '_org_y', None) is not None:
            return self._org_y
        if self.style_override and self.style_override.has_org:
            return self.style_override.org_y
        return self.middle

    @org_y.setter
    def org_y(self, val):
        self._org_y = float(val) if val is not None else None


class AdjacentUnitProxy(str):
    """
    Hybrid canonical string identifier and transparent proxy for neighbouring units.

    Acts simultaneously as a native lowercase string identifier ('prev' / 'next') for comparisons
    and function arguments (e.g. `sync(prev, ...)`), while dynamically proxying attribute
    access towards the wrapped `PyxisUnit` instance.

    Key Behaviours:
        - Transparent Proxying: Accessing `prev.left` delegates directly to `unit.left`.
        - Strict None Safety: If no neighbour exists, accessing attributes raises a clear `AttributeError`
          stating that the directional unit is None.
        - Boolean Truthiness: Evaluates to True if the underlying unit is present, and False otherwise,
          allowing idiomatic checks such as `if prev: ...`.
        - Introspection & Autocompletion: `__dir__` unions native string methods with all unit properties,
          enabling full code completion in the script editor.
    """
    def __new__(cls, name: str, unit=None):
        clean_name = str(name).strip().lower()
        instance = super().__new__(cls, clean_name)
        if isinstance(unit, AdjacentUnitProxy):
            unit = unit._unit
        instance._unit = unit
        instance._direction = clean_name
        return instance

    def __getattr__(self, name):
        if self._unit is not None:
            return getattr(self._unit, name)
        raise AttributeError(f"'{self._direction}' unit is None; cannot access attribute '{name}'")

    def __bool__(self):
        return self._unit is not None

    @property
    def unit(self):
        return self._unit

    @property
    def direction(self):
        return self._direction

    def __dir__(self):
        base_dir = set(super().__dir__())
        if self._unit is not None:
            base_dir.update(dir(self._unit))
        return sorted(base_dir)
