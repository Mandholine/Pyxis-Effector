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

# PyxisNodes/nodes/text_nodes.py
"""Nodos de operaciones de texto y conversión de cadenas."""

import re
from decorators import pyxis_node
from node_engine import NODE_REGISTRY

_TAG_RE = re.compile(r'\{.*?\}')

def _get_text(context, text):
    """Obtiene el texto proporcionado o realiza autocompletado inteligente desde el contexto activo."""
    if text is not None and str(text) != "":
        return str(text)
    if isinstance(context, dict):
        unit = context.get('active_unit') or context.get('syl') or context.get('char') or context.get('word')
        if unit:
            t = getattr(unit, 'text_stripped', getattr(unit, 'text', ''))
            if t: return str(t)
        line = context.get('active_line') or context.get('line')
        if line:
            t = getattr(line, 'text_stripped', getattr(line, 'text', ''))
            if t: return str(t)
    return ""


def text_strip_tags(context, text=""):
    raw = _get_text(context, text)
    clean = _TAG_RE.sub("", raw)
    clean = clean.replace(r"\N", " ").replace(r"\n", " ").replace(r"\h", " ")
    return clean.strip()


def text_upper(context, text=""):
    return _get_text(context, text).upper()


def text_lower(context, text=""):
    return _get_text(context, text).lower()


def text_replace(context, text="", search="", replace=""):
    raw = _get_text(context, text)
    return raw.replace(str(search), str(replace))


def text_substring(context, text="", start=0, length=10):
    st = _get_text(context, text)
    try:
        from node_engine import _eval_num_expr
        s = int(_eval_num_expr(start, context, 0.0)) if str(start).strip() != "" else 0
        l = int(_eval_num_expr(length, context, float(len(st)))) if str(length).strip() != "" else len(st)
        return st[s:s+l]
    except Exception:
        return st


def text_len(context, text=""):
    return len(_get_text(context, text))


def text_contains(context, text="", search=""):
    raw = _get_text(context, text)
    return 1 if str(search) in raw else 0


# -----------------------------------------------------------------------------
# TRANSLITERACIÓN DE KANA (JAPONÉS)
# -----------------------------------------------------------------------------
_KANA_TABLE = [
    # Yōon / Digraphs
    ("kya", "きゃ", "キャ"), ("kyu", "きゅ", "キュ"), ("kyo", "きょ", "キョ"),
    ("sha", "しゃ", "シャ"), ("shu", "しゅ", "シュ"), ("sho", "しょ", "ショ"),
    ("cha", "ちゃ", "チャ"), ("chu", "ちゅ", "チュ"), ("cho", "ちょ", "チョ"),
    ("nya", "にゃ", "ニャ"), ("nyu", "にゅ", "ニュ"), ("nyo", "にょ", "ニョ"),
    ("hya", "ひゃ", "ヒャ"), ("hyu", "ひゅ", "ヒュ"), ("hyo", "ひょ", "ヒョ"),
    ("mya", "みゃ", "ミャ"), ("myu", "みゅ", "ミュ"), ("myo", "みょ", "ミョ"),
    ("rya", "りゃ", "リャ"), ("ryu", "りゅ", "リュ"), ("ryo", "りょ", "リョ"),
    ("gya", "ぎゃ", "ギャ"), ("gyu", "ぎゅ", "ギュ"), ("gyo", "ぎょ", "ギョ"),
    ("ja", "じゃ", "ジャ"),   ("ju", "じゅ", "ジュ"),   ("jo", "じょ", "ジョ"),
    ("bya", "びゃ", "ビャ"), ("byu", "びゅ", "ビュ"), ("byo", "びょ", "ビョ"),
    ("pya", "ぴゃ", "ピャ"), ("pyu", "ぴゅ", "ピュ"), ("pyo", "ぴょ", "ピョ"),
    # Monographs
    ("a", "あ", "ア"),   ("i", "い", "イ"),   ("u", "う", "ウ"),   ("e", "え", "エ"),   ("o", "お", "オ"),
    ("ka", "か", "カ"),  ("ki", "き", "キ"),  ("ku", "く", "ク"),  ("ke", "け", "ケ"),  ("ko", "こ", "コ"),
    ("sa", "さ", "サ"),  ("shi", "し", "シ"), ("su", "す", "ス"),  ("se", "せ", "セ"),  ("so", "そ", "ソ"),
    ("ta", "た", "タ"),  ("chi", "ち", "チ"), ("tsu", "つ", "ツ"), ("te", "て", "テ"),  ("to", "to", "ト"),
    ("na", "な", "ナ"),  ("ni", "に", "ニ"),  ("nu", "ぬ", "ヌ"),  ("ne", "ね", "ネ"),  ("no", "の", "ノ"),
    ("ha", "は", "ハ"),  ("hi", "ひ", "ヒ"),  ("fu", "ふ", "フ"),  ("he", "へ", "ヘ"),  ("ho", "ほ", "ホ"),
    ("ma", "ま", "マ"),  ("mi", "み", "ミ"),  ("mu", "む", "ム"),  ("me", "め", "メ"),  ("mo", "も", "モ"),
    ("ya", "や", "ヤ"),  ("yu", "ゆ", "ユ"),  ("yo", "よ", "ヨ"),
    ("ra", "ら", "ラ"),  ("ri", "り", "リ"),  ("ru", "る", "ル"),  ("re", "れ", "レ"),  ("ro", "ろ", "ロ"),
    ("wa", "わ", "ワ"),  ("wi", "ゐ", "ヰ"),  ("we", "ゑ", "ヱ"),  ("wo", "を", "ヲ"),
    ("n", "ん", "ン"),
    # Dakuten
    ("ga", "が", "ガ"),  ("gi", "ぎ", "ギ"),  ("gu", "ぐ", "グ"),  ("ge", "げ", "ゲ"),  ("go", "ご", "ゴ"),
    ("za", "ざ", "ザ"),  ("ji", "じ", "ジ"),  ("zu", "ず", "ズ"),  ("ze", "ぜ", "ゼ"),  ("zo", "ぞ", "ゾ"),
    ("da", "だ", "ダ"),  ("di", "ぢ", "ヂ"),  ("du", "づ", "ヅ"),  ("de", "で", "デ"),  ("do", "ど", "ド"),
    ("ba", "ば", "バ"),  ("bi", "び", "ビ"),  ("bu", "ぶ", "ブ"),  ("be", "べ", "ベ"),  ("bo", "ぼ", "ボ"),
    # Handakuten
    ("pa", "ぱ", "パ"),  ("pi", "ぴ", "ピ"),  ("pu", "ぷ", "プ"),  ("pe", "ぺ", "ペ"),  ("po", "ぽ", "ポ")
]

_SOKUON_LETTERS = set("bcdfghjklmpqrstvwxyz")


def text_transliterate_kana(context, text="", mode="Romaji a Hiragana"):
    txt = _get_text(context, text)
    if not txt:
        return ""
    
    m = str(mode).strip().lower()
    
    # 1. Hiragana a Katakana
    if "hiragana a katakana" in m or ("hira" in m and "kata" in m and m.startswith("hira")):
        res = txt
        for _, h, k in _KANA_TABLE:
            res = res.replace(h, k)
        res = res.replace("っ", "ッ")
        return res

    # 2. Katakana a Hiragana
    elif "katakana a hiragana" in m or ("kata" in m and "hira" in m and m.startswith("kata")):
        res = txt
        for _, h, k in _KANA_TABLE:
            res = res.replace(k, h)
        res = res.replace("ッ", "っ")
        return res

    # 3. Kana a Romaji
    elif "romaji" in m and ("kana a romaji" in m or "hiragana a romaji" in m or "katakana a romaji" in m):
        res = txt
        res = res.replace("っ", "t").replace("ッ", "t")
        for r, h, k in sorted(_KANA_TABLE, key=lambda x: len(x[1]), reverse=True):
            res = res.replace(h, r).replace(k, r)
        return res

    # 4. Romaji a Katakana
    elif "katakana" in m:
        res = txt.lower()
        for c in _SOKUON_LETTERS:
            res = res.replace(c + c, "ッ" + c)
        for r, _, k in sorted(_KANA_TABLE, key=lambda x: len(x[0]), reverse=True):
            res = res.replace(r, k)
        return res

    # 5. Romaji a Hiragana (Default)
    else:
        res = txt.lower()
        for c in _SOKUON_LETTERS:
            res = res.replace(c + c, "っ" + c)
        for r, h, _ in sorted(_KANA_TABLE, key=lambda x: len(x[0]), reverse=True):
            res = res.replace(r, h)
        return res


# -----------------------------------------------------------------------------
# NODO MAESTRO UNIFICADO TEXT
# -----------------------------------------------------------------------------
def eval_text_node(context=None, **kwargs):
    """Manejador unificado para el Nodo Maestro Text."""
    operacion = str(kwargs.get("operacion", kwargs.get("modo", "Strip Tags"))).strip()
    ctx = context or {}

    def get_str(key, default=""):
        val = kwargs.get(key)
        if val is None:
            val = kwargs.get(key.lower())
        if val is None or str(val) == "":
            return default
        return str(val)

    text_input = kwargs.get("Text")
    if text_input is None:
        text_input = kwargs.get("Texto")
    if text_input is None:
        text_input = kwargs.get("texto")
    if text_input is None:
        text_input = kwargs.get("text")
    raw_text = _get_text(ctx, text_input)

    op_clean = operacion.lower().replace(" ", "").replace("á", "a").replace("ú", "u").replace("í", "i")

    # 1. Strip Tags
    if op_clean in ("striptags", "limpiartags", "strip"):
        clean = _TAG_RE.sub("", raw_text)
        clean = clean.replace(r"\N", " ").replace(r"\n", " ").replace(r"\h", " ")
        return clean.strip()

    # 2. Mayusculas
    elif op_clean in ("mayusculas", "upper", "mayus"):
        return raw_text.upper()

    # 3. Minusculas
    elif op_clean in ("minusculas", "lower", "minus"):
        return raw_text.lower()

    # 4. Reemplazar
    elif op_clean in ("reemplazar", "replace"):
        search = get_str("Buscar", get_str("search", ""))
        replace = get_str("Reemplazar Por", get_str("Reemplazar", get_str("replace", "")))
        return raw_text.replace(search, replace)

    # 5. Subcadena
    elif op_clean in ("subcadena", "substring", "sub"):
        try:
            from node_engine import _eval_num_expr
            st_val = kwargs.get("Start", kwargs.get("inicio", kwargs.get("start", 0)))
            len_val = kwargs.get("Longitud", kwargs.get("longitud", kwargs.get("length", len(raw_text))))
            s = int(_eval_num_expr(st_val, ctx, 0.0)) if str(st_val).strip() != "" else 0
            l = int(_eval_num_expr(len_val, ctx, float(len(raw_text)))) if str(len_val).strip() != "" else len(raw_text)
            return raw_text[s:s+l]
        except Exception:
            return raw_text

    # 6. Longitud
    elif op_clean in ("longitud", "len", "length"):
        return str(len(raw_text))

    # 7. Contener
    elif op_clean in ("contener", "contains"):
        search = get_str("Buscar", get_str("search", ""))
        return "1" if search in raw_text else "0"

    # 8. Kana
    elif op_clean in ("kana", "transliterarkana", "transliterar"):
        modo = get_str("Modo", get_str("modo", "Romaji a Hiragana"))
        return text_transliterate_kana(ctx, text=raw_text, mode=modo)

    else:
        return raw_text


# -----------------------------------------------------------------------------
# NODOS ESPECIALES DE FUENTES VECTORIALES (FASE 2)
# -----------------------------------------------------------------------------
def text_to_shape_node(context, text="", font_name=None, font_size=None, bold=False, italic=False, scale=1.0):
    unit = context.get('active_unit') if isinstance(context, dict) else None
    line = context.get('active_line') if isinstance(context, dict) else (context.get('line') if isinstance(context, dict) else None)
    styleref = getattr(line, 'styleref', None) if line else None
    if not styleref and unit:
        styleref = getattr(unit, 'styleref', None)
        if not styleref and hasattr(unit, 'line') and getattr(unit, 'line', None):
            styleref = getattr(unit.line, 'styleref', None)
    
    txt_val = str(text) if (text is not None and text != "") else (getattr(unit, 'text_stripped', getattr(unit, 'text', '')) if unit else "")
    if not txt_val and line:
        txt_val = getattr(line, 'text_stripped', getattr(line, 'text', ''))
        
    if txt_val and str(txt_val).strip().lower().startswith("shape."):
        from nodes.shape_nodes import resolve_shape_value
        return resolve_shape_value(txt_val, context)
        
    if font_name is not None and str(font_name).strip() != "":
        fn = str(font_name).strip()
    elif styleref and getattr(styleref, 'fontname', None):
        fn = str(styleref.fontname)
    elif line and getattr(line, 'style', None):
        fn = str(line.style)
    else:
        fn = "Arial"
        
    if font_size is not None and str(font_size).strip() != "":
        try: fs = int(float(font_size))
        except: fs = 100
    elif styleref and getattr(styleref, 'fontsize', None):
        try: fs = int(float(styleref.fontsize))
        except: fs = 100
    elif unit and getattr(unit, 'height', None):
        try: fs = int(float(unit.height))
        except: fs = 100
    else:
        fs = 100
        
    b_val = bool(bold) if bold is not None else (bool(getattr(styleref, 'bold', False)) if styleref else False)
    i_val = bool(italic) if italic is not None else (bool(getattr(styleref, 'italic', False)) if styleref else False)
    
    sc = 1.0
    try: sc = float(scale)
    except: sc = 1.0
    
    from font_vector_engine import FontVectorEngine
    return FontVectorEngine.text_to_shape(txt_val, font_name=fn, font_size=fs, bold=b_val, italic=i_val, scale=sc)


# Registros en NODE_REGISTRY
NODE_REGISTRY["Text"] = eval_text_node
