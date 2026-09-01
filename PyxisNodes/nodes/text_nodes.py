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


# -----------------------------------------------------------------------------
# NODO TEXT ON PATH (BRECHA 6 - EFFECTOR 2 PARITY)
# -----------------------------------------------------------------------------
def text_on_path_core(
    shape_str: str,
    context: dict = None,
    mode: str = "Center (Centrado)",
    offset: float = 0.0,
    extra_angle: float = 0.0,
    subdivs: int = 30
):
    """Calcula la posición y ángulo tangencial del elemento de texto activo a lo largo de una trayectoria ASSdraw.
    
    Basado en el algoritmo original ke.text.bezier(shp, mode, offset) de Effector 2.
    
    Retorna tupla: (tag_out, pos_str, angle_str, x_val, y_val, total_length, target_dist)
    """
    import math
    from nodes.shape_nodes import (
        parse_assdraw_segments,
        _segment_arc_length,
        _map_dist_to_bezier_u,
        _eval_bezier_tangent,
        _eval_bezier_pt,
        resolve_shape_value
    )

    ctx = context if isinstance(context, dict) else {}
    unit = ctx.get('active_unit') or ctx.get('char') or ctx.get('syl') or ctx.get('word') or ctx.get('line')
    line = ctx.get('active_line') or (getattr(unit, 'line', None) if unit else None) or ctx.get('line')

    # Resolver forma / spline
    shp_val = resolve_shape_value(shape_str, ctx)
    if not shp_val and line:
        raw_t = getattr(line, 'raw_text', getattr(line, 'text', ''))
        clip_m = re.search(r'\\i?clip\(([^)]+)\)', raw_t)
        if clip_m:
            shp_val = clip_m.group(1).strip()

    if not shp_val:
        u_cx = float(getattr(unit, 'center', getattr(unit, 'x', 0.0))) if unit else 0.0
        u_cy = float(getattr(unit, 'middle', getattr(unit, 'y', 0.0))) if unit else 0.0
        pos_s = f"\\pos({u_cx:.2f},{u_cy:.2f})".rstrip('0').rstrip('.')
        return pos_s, pos_s, "\\frz0", round(u_cx, 2), round(u_cy, 2), 0.0, 0.0

    contours = parse_assdraw_segments(shp_val)
    if not contours:
        u_cx = float(getattr(unit, 'center', getattr(unit, 'x', 0.0))) if unit else 0.0
        u_cy = float(getattr(unit, 'middle', getattr(unit, 'y', 0.0))) if unit else 0.0
        pos_s = f"\\pos({u_cx:.2f},{u_cy:.2f})".rstrip('0').rstrip('.')
        return pos_s, pos_s, "\\frz0", round(u_cx, 2), round(u_cy, 2), 0.0, 0.0

    sub = max(5, int(subdivs))
    contour_data = []
    total_len = 0.0

    for c in contours:
        c_len = 0.0
        seg_info = []
        for s in c.get('segments', []):
            s_len, chord_lens, chord_pts = _segment_arc_length(s, subdivs=sub)
            seg_info.append({
                'seg': s,
                'len': s_len,
                'chord_lens': chord_lens,
                'chord_pts': chord_pts,
                'start_dist': total_len + c_len,
                'end_dist': total_len + c_len + s_len
            })
            c_len += s_len
        contour_data.append(seg_info)
        total_len += c_len

    if total_len <= 1e-9:
        p0 = contours[0].get('start', (0.0, 0.0))
        pos_s = f"\\pos({p0[0]:.2f},{p0[1]:.2f})".rstrip('0').rstrip('.')
        return pos_s, pos_s, "\\frz0", round(p0[0], 2), round(p0[1], 2), 0.0, 0.0

    # Métricas de línea y unidad de Karaskel
    l_width = float(getattr(line, 'width', getattr(unit, 'width', 0.0))) if line else float(getattr(unit, 'width', 0.0) if unit else 0.0)
    l_left = float(getattr(line, 'left', getattr(unit, 'left', 0.0))) if line else float(getattr(unit, 'left', 0.0) if unit else 0.0)
    u_center = float(getattr(unit, 'center', getattr(unit, 'x', l_left + l_width / 2.0))) if unit else (l_left + l_width / 2.0)
    
    unit_dist_in_line = u_center - l_left if line else (l_width / 2.0)

    # Cálculo de lineoffset según el modo de Effector 2
    mode_clean = str(mode).strip().lower()
    offset_val = float(offset)

    if "left" in mode_clean or "izq" in mode_clean:
        lineoffset = offset_val
    elif "right" in mode_clean or "der" in mode_clean:
        lineoffset = total_len - l_width - offset_val
    elif "justif" in mode_clean:
        if abs(offset_val) > 1e-9:
            lineoffset = (total_len - l_width) * offset_val
        elif unit and hasattr(unit, 'i') and hasattr(unit, 'n'):
            ci = float(getattr(unit, 'i', 1))
            cn = float(getattr(unit, 'n', 1))
            progress_char = (ci - 1.0) / (cn - 1.0) if cn > 1 else 0.5
            lineoffset = (total_len - l_width) * progress_char
        else:
            lineoffset = (total_len - l_width) / 2.0
    elif "anim" in mode_clean or "prog" in mode_clean:
        lineoffset = (total_len - l_width) * (1.0 - offset_val)
    else:  # Center (Default)
        lineoffset = (total_len - l_width) / 2.0 + offset_val

    target = lineoffset + unit_dist_in_line

    # Clamping o muestreo en la trayectoria
    # Si la curva es cerrada o target excede, calcular posición dentro de los límites
    target_clamped = target
    if target_clamped < 0.0:
        target_clamped = 0.0
    elif target_clamped > total_len:
        target_clamped = total_len

    cur_x, cur_y = 0.0, 0.0
    dx, dy = 1.0, 0.0
    found_pt = False

    for c_segs in contour_data:
        for s_info in c_segs:
            s_d0 = s_info['start_dist']
            s_d1 = s_info['end_dist']
            s_len = s_info['len']
            if (s_d0 <= target_clamped <= s_d1) or (target_clamped >= total_len and s_d1 >= total_len - 1e-9):
                local_d = target_clamped - s_d0
                seg = s_info['seg']
                if seg['type'] == 'l':
                    u = local_d / s_len if s_len > 1e-9 else 0.0
                    p0, p1 = seg['p0'], seg['p1']
                    cur_x = p0[0] + u * (p1[0] - p0[0])
                    cur_y = p0[1] + u * (p1[1] - p0[1])
                    dx = p1[0] - p0[0]
                    dy = p1[1] - p0[1]
                else:  # 'b'
                    u = _map_dist_to_bezier_u(local_d, s_info['chord_lens'], sub)
                    p0, p1, p2, p3 = seg['p0'], seg['p1'], seg['p2'], seg['p3']
                    cur_x, cur_y = _eval_bezier_pt(p0, p1, p2, p3, u)
                    dx, dy = _eval_bezier_tangent(p0, p1, p2, p3, u)
                found_pt = True
                break
        if found_pt:
            break

    if not found_pt:
        # Fallback al último punto
        if contour_data and contour_data[-1]:
            last_s = contour_data[-1][-1]['seg']
            p_end = last_s.get('p1' if last_s['type'] == 'l' else 'p3', (0.0, 0.0))
            cur_x, cur_y = p_end[0], p_end[1]
            if last_s['type'] == 'l':
                dx = last_s['p1'][0] - last_s['p0'][0]
                dy = last_s['p1'][1] - last_s['p0'][1]
            else:
                dx, dy = _eval_bezier_tangent(last_s['p0'], last_s['p1'], last_s['p2'], last_s['p3'], 1.0)
        else:
            cur_x, cur_y = contours[0].get('start', (0.0, 0.0))

    if abs(dx) < 1e-9 and abs(dy) < 1e-9:
        dx, dy = 1.0, 0.0

    # Ángulo tangencial armonioso idéntico a ZF text in clip (math.atan2(dx, dy) - 90)
    angle_deg = (math.degrees(math.atan2(dx, dy)) - 90.0) + float(extra_angle)
    while angle_deg > 180.0:
        angle_deg -= 360.0
    while angle_deg <= -180.0:
        angle_deg += 360.0
    angle_deg = round(angle_deg, 2)

    pos_str = f"\\pos({cur_x:.2f},{cur_y:.2f})".rstrip('0').rstrip('.').replace('.\\', '\\')
    if pos_str.endswith('.'):
        pos_str = pos_str[:-1]
    
    frz_val_str = f"{angle_deg:.2f}".rstrip('0').rstrip('.')
    if not frz_val_str or frz_val_str == "-0" or frz_val_str == "0":
        frz_val_str = "0"
    frz_str = f"\\frz{frz_val_str}"

    if angle_deg != 0.0 and frz_val_str != "0":
        tag_out = f"{pos_str}{frz_str}"
    else:
        tag_out = pos_str

    return tag_out, pos_str, frz_str, round(cur_x, 2), round(cur_y, 2), round(total_len, 2), round(target, 2)


def text_on_path_node(
    context=None,
    shape="",
    mode="Center (Centrado)",
    offset=0.0,
    extra_angle=0.0,
    subdivs=30
):
    """Controlador para el nodo Text on Path (Functions / Text)."""
    from node_engine import _eval_num_expr

    ctx = context or {}
    shp_val = str(shape or "").strip()
    mode_str = str(mode or "Center (Centrado)").strip()

    off_val = float(_eval_num_expr(offset, ctx, 0.0))
    extra_ang = float(_eval_num_expr(extra_angle, ctx, 0.0))
    sub_val = int(float(_eval_num_expr(subdivs, ctx, 30.0)))

    tag_out, pos_str, frz_str, x_val, y_val, total_len, target_dist = text_on_path_core(
        shape_str=shp_val,
        context=ctx,
        mode=mode_str,
        offset=off_val,
        extra_angle=extra_ang,
        subdivs=sub_val
    )

    return tag_out, pos_str, frz_str, x_val, y_val, total_len


# Registros en NODE_REGISTRY
NODE_REGISTRY["Text"] = eval_text_node
NODE_REGISTRY["Functions/Text on Path"] = text_on_path_node
NODE_REGISTRY["Text on Path"] = text_on_path_node
NODE_REGISTRY["Text/Text on Path"] = text_on_path_node

