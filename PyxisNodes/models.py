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

from typing import Optional

class PyxisUnit:
    def __init__(self):
        self.i, self.n = 1, 1
        self.syl_i, self.word_i = 1, 1
        self.text, self.text_stripped = "", ""
        self.duration = 0
        self.start_time, self.end_time = 0, 0
        self._mid_time = None

        # Tiempos relativos respecto al inicio de la línea madre
        self.syl_start, self.syl_end = 0, 0
        self.word_start, self.word_end = 0, 0
        self.char_start, self.char_end = 0, 0

        # Dimensiones y posiciones
        self.width, self.height, self.descent, self.extlead = 0.0, 0.0, 0.0, 0.0
        self.left, self.center, self.right = 0.0, 0.0, 0.0
        self.top, self.middle, self.bottom = 0.0, 0.0, 0.0
        self.x, self.y = 0.0, 0.0

        # Espaciado de sílabas/palabras
        self.prespace, self.postspace = "", ""
        self.prespacewidth, self.postspacewidth = 0.0, 0.0

        # Jerarquía de referencias
        self.line, self.word = None, None
        self._syl_obj = None
        self.chars = []

    @property
    def dur(self):
        return self.duration

    @dur.setter
    def dur(self, val):
        self.duration = val

    @property
    def start(self):
        rel = getattr(self, 'syl_start', None)
        if rel is None or rel == 0:
            rel = getattr(self, 'word_start', None)
        if rel is None or rel == 0:
            rel = getattr(self, 'char_start', None)
        if rel is not None and rel != 0:
            return rel
        line_st = getattr(self.line, 'start_time', 0) if self.line else 0
        return max(0, self.start_time - line_st)

    @start.setter
    def start(self, val):
        self.syl_start = val

    @property
    def end(self):
        rel = getattr(self, 'syl_end', None)
        if rel is None or rel == 0:
            rel = getattr(self, 'word_end', None)
        if rel is None or rel == 0:
            rel = getattr(self, 'char_end', None)
        if rel is not None and rel != 0:
            return rel
        line_st = getattr(self.line, 'start_time', 0) if self.line else 0
        return max(0, self.end_time - line_st)

    @end.setter
    def end(self, val):
        self.syl_end = val

    @property
    def st(self):
        return self.start_time

    @st.setter
    def st(self, val):
        self.start_time = val

    @property
    def et(self):
        return self.end_time

    @et.setter
    def et(self, val):
        self.end_time = val

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
    def text_spacestripped(self):
        if getattr(self, '_text_spacestripped', None) is not None:
            return self._text_spacestripped
        return self.text_stripped.strip()

    @text_spacestripped.setter
    def text_spacestripped(self, val):
        self._text_spacestripped = str(val)

class StyleRef:
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

        # Primary, Secondary, Outline, Back Colours & Alphas
        self.color1 = str(style_dict.get('PrimaryColour', style_dict.get('color1', '&H00FFFFFF&')))
        self.color2 = str(style_dict.get('SecondaryColour', style_dict.get('color2', '&H000000FF&')))
        self.color3 = str(style_dict.get('OutlineColour', style_dict.get('color3', '&H00000000&')))
        self.color4 = str(style_dict.get('BackColour', style_dict.get('color4', '&H00000000&')))

        self.alpha1 = str(style_dict.get('alpha1', '&H00&'))
        self.alpha2 = str(style_dict.get('alpha2', '&H00&'))
        self.alpha3 = str(style_dict.get('alpha3', '&H00&'))
        self.alpha4 = str(style_dict.get('alpha4', '&H00&'))

        try:
            self.outline = float(style_dict.get('Outline', style_dict.get('outline', 2.0)))
        except Exception:
            self.outline = 2.0
        try:
            self.shadow = float(style_dict.get('Shadow', style_dict.get('shadow', 0.0)))
        except Exception:
            self.shadow = 0.0

class PyxisLine(PyxisUnit):
    def __init__(self):
        super().__init__()
        self.layer, self.style_name, self.actor, self.effect, self.raw_text = 0, "Default", "", "", ""
        self.margin_l, self.margin_r, self.margin_v = 0, 0, 0
        self.margin_t, self.margin_b = 0, 0
        self.is_selected = False
        self.syls, self.words = [], []
        self.line = self
        self.styleref = StyleRef()

    @property
    def style(self):
        return self.style_name

    @style.setter
    def style(self, val):
        self.style_name = str(val)

    @property
    def color1(self): return self.styleref.color1
    @property
    def color2(self): return self.styleref.color2
    @property
    def color3(self): return self.styleref.color3
    @property
    def color4(self): return self.styleref.color4
    @property
    def alpha1(self): return self.styleref.alpha1
    @property
    def alpha2(self): return self.styleref.alpha2
    @property
    def alpha3(self): return self.styleref.alpha3
    @property
    def alpha4(self): return self.styleref.alpha4
    @property
    def outline(self): return self.styleref.outline
    @property
    def shadow(self): return self.styleref.shadow