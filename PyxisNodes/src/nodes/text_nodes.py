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

"""Text manipulation and typographic layout nodes."""

import re
from decorators import pyxis_node
from node_engine import NODE_REGISTRY

_TAG_RE = re.compile(r'\{.*?\}')

def _get_text(context, text):
    """Gets the provided text or performs smart autocompletion from the active context."""
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


_KANA_TABLE = [
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
    ("ga", "が", "ガ"),  ("gi", "ぎ", "ギ"),  ("gu", "ぐ", "グ"),  ("ge", "げ", "ゲ"),  ("go", "ご", "ゴ"),
    ("za", "ざ", "ザ"),  ("ji", "じ", "ジ"),  ("zu", "ず", "ズ"),  ("ze", "ぜ", "ゼ"),  ("zo", "ぞ", "ゾ"),
    ("da", "だ", "ダ"),  ("di", "ぢ", "ヂ"),  ("du", "づ", "ヅ"),  ("de", "で", "デ"),  ("do", "ど", "ド"),
    ("ba", "ば", "バ"),  ("bi", "び", "ビ"),  ("bu", "ぶ", "ブ"),  ("be", "べ", "ベ"),  ("bo", "ぼ", "ボ"),
    ("pa", "ぱ", "パ"),  ("pi", "ぴ", "ピ"),  ("pu", "ぷ", "プ"),  ("pe", "ぺ", "ペ"),  ("po", "ぽ", "ポ")
]

_SOKUON_LETTERS = set("bcdfghjklmpqrstvwxyz")


def text_transliterate_kana(context, text="", mode="Romaji to Hiragana"):
    txt = _get_text(context, text)
    if not txt:
        return ""
    
    m = str(mode).strip().lower().replace(" a ", " to ")
    
    if "hiragana to katakana" in m or ("hira" in m and "kata" in m and m.index("hira") < m.index("kata")):
        res = txt
        for _, h, k in _KANA_TABLE:
            res = res.replace(h, k)
        res = res.replace("っ", "ッ")
        return res

    elif "katakana to hiragana" in m or ("kata" in m and "hira" in m and m.index("kata") < m.index("hira")):
        res = txt
        for _, h, k in _KANA_TABLE:
            res = res.replace(k, h)
        res = res.replace("ッ", "っ")
        return res

    elif ("kana to romaji" in m or "hiragana to romaji" in m or "katakana to romaji" in m or
          ("romaji" in m and ("kana" in m or "hira" in m or "kata" in m) and m.index("romaji") > min([m.index(x) for x in ["kana", "hira", "kata"] if x in m]))):
        res = txt
        res = res.replace("っ", "t").replace("ッ", "t")
        for r, h, k in sorted(_KANA_TABLE, key=lambda x: len(x[1]), reverse=True):
            res = res.replace(h, r).replace(k, r)
        return res

    elif "katakana" in m or "kata" in m:
        res = txt.lower()
        for c in _SOKUON_LETTERS:
            res = res.replace(c + c, "ッ" + c)
        for r, _, k in sorted(_KANA_TABLE, key=lambda x: len(x[0]), reverse=True):
            res = res.replace(r, k)
        return res

    else:
        res = txt.lower()
        for c in _SOKUON_LETTERS:
            res = res.replace(c + c, "っ" + c)
        for r, h, _ in sorted(_KANA_TABLE, key=lambda x: len(x[0]), reverse=True):
            res = res.replace(r, h)
        return res


_ROMAJI_SYLLABLES = [
    # Trigraphs
    "kya", "kyu", "kyo", "sha", "shu", "sho", "cha", "chu", "cho",
    "nya", "nyu", "nyo", "hya", "hyu", "hyo", "mya", "myu", "myo",
    "rya", "ryu", "ryo", "gya", "gyu", "gyo", "bya", "byu", "byo",
    "pya", "pyu", "pyo", "tsu", "chi", "shi", "dza", "dzu", "dze", "dzo",
    "jya", "jyu", "jyo",
    # Digraphs
    "ka", "ki", "ku", "ke", "ko", "sa", "su", "se", "so", "ta", "te", "to",
    "na", "ni", "nu", "ne", "no", "ha", "hi", "fu", "he", "ho", "ma", "mi",
    "mu", "me", "mo", "ya", "yu", "yo", "ra", "ri", "ru", "re", "ro", "wa",
    "wi", "we", "wo", "ga", "gi", "gu", "ge", "go", "za", "ji", "zu", "ze",
    "zo", "ja", "ju", "jo", "da", "di", "du", "de", "do", "ba", "bi", "bu",
    "be", "bo", "pa", "pi", "pu", "pe", "po", "fa", "fi", "fe", "fo", "ti", "tu",
    "va", "vi", "vu", "ve", "vo",
    # Monographs
    "a", "i", "u", "e", "o", "n",
    "b", "c", "d", "k", "p", "r", "s", "t", "z", "f", "g", "h", "j", "m", "v", "w", "y"
]
_ROMAJI_SORTED = sorted(_ROMAJI_SYLLABLES, key=len, reverse=True)


def _tokenize_romaji_word(word):
    syllables = []
    i = 0
    w_lower = word.lower()
    n = len(word)
    while i < n:
        matched = False
        for syl in _ROMAJI_SORTED:
            if w_lower.startswith(syl, i):
                syllables.append(word[i:i+len(syl)])
                i += len(syl)
                matched = True
                break
        if not matched:
            syllables.append(word[i])
            i += 1
    return syllables


def text_romaji_to_karaoke(context=None, text="", kmode="k", duration=None, **kwargs):
    raw_text = _get_text(context, text)
    if not raw_text:
        return ""
    
    clean_text = _TAG_RE.sub("", raw_text).strip()
    if not clean_text:
        return ""

    clean_kmode = str(kmode or "k").lstrip("\\").strip()
    if clean_kmode not in ("k", "kf", "ko", "K"):
        clean_kmode = "k"

    tokens = re.split(r'(\s+|[^\w\s]+)', clean_text)
    parsed_tokens = []
    total_syllables = 0
    for tok in tokens:
        if not tok:
            continue
        if re.match(r'^\s+$', tok) or re.match(r'^[^\w\s]+$', tok):
            parsed_tokens.append({"type": "separator", "text": tok})
        else:
            syls = _tokenize_romaji_word(tok)
            parsed_tokens.append({"type": "word", "syllables": syls})
            total_syllables += len(syls)

    if total_syllables == 0:
        return clean_text

    dur_cs = None
    if duration is not None and str(duration).strip() != "":
        try:
            from node_engine import _eval_num_expr
            dur_val = float(_eval_num_expr(duration, context, 0.0))
            if dur_val > 0:
                dur_cs = dur_val
        except Exception:
            pass

    if dur_cs is None and isinstance(context, dict):
        unit = context.get('active_unit') or context.get('syl') or context.get('char') or context.get('word')
        u_dur = getattr(unit, 'duration', None)
        if u_dur is not None and u_dur > 0:
            dur_cs = u_dur / 10.0
        else:
            line = context.get('active_line') or context.get('line')
            l_dur = getattr(line, 'duration', None)
            if l_dur is not None and l_dur > 0:
                dur_cs = l_dur / 10.0

    if dur_cs is None or dur_cs <= 0:
        durations = [10] * total_syllables
    else:
        dur_int = max(1, int(round(dur_cs)))
        base = max(1, dur_int // total_syllables)
        rem = dur_int % total_syllables
        durations = [base + (1 if i < rem else 0) for i in range(total_syllables)]

    res = []
    syl_idx = 0
    for item in parsed_tokens:
        if item["type"] == "separator":
            res.append(item["text"])
        else:
            for syl in item["syllables"]:
                d = durations[syl_idx]
                res.append(f"{{\\{clean_kmode}{d}}}{syl}")
                syl_idx += 1

    return "".join(res)


def eval_text_node(context=None, **kwargs):
    """Unified canonical handler for the Basics/Text node."""
    operation = str(kwargs.get("operation", kwargs.get("mode", "strip_tags"))).strip()
    ctx = context or {}

    def get_str(key, default=""):
        val = kwargs.get(key)
        if val is None:
            val = kwargs.get(key.lower())
        if val is None or str(val) == "":
            return default
        return str(val)

    text_input = kwargs.get("Text", kwargs.get("text", kwargs.get("texto", kwargs.get("value"))))
    raw_text = _get_text(ctx, text_input)

    op_clean = operation.lower().replace(" ", "").replace("_", "")

    if op_clean in ("striptags", "strip"):
        clean = _TAG_RE.sub("", raw_text)
        clean = clean.replace(r"\N", " ").replace(r"\n", " ").replace(r"\h", " ")
        return clean.strip()

    elif op_clean in ("uppercase", "upper"):
        return raw_text.upper()

    elif op_clean in ("lowercase", "lower"):
        return raw_text.lower()

    elif op_clean in ("cleanspaces", "spaces"):
        clean = re.sub(r'[ \t]+', ' ', raw_text)
        return clean.strip()

    elif op_clean in ("replace",):
        search = get_str("Search", get_str("search", ""))
        replace = get_str("Replace With", get_str("Replace", get_str("replace", "")))
        return raw_text.replace(search, replace)

    elif op_clean in ("substring", "sub"):
        try:
            from node_engine import _eval_num_expr
            st_val = kwargs.get("Start", kwargs.get("start", 0))
            len_val = kwargs.get("Length", kwargs.get("length", len(raw_text)))
            s = int(_eval_num_expr(st_val, ctx, 0.0)) if str(st_val).strip() != "" else 0
            l = int(_eval_num_expr(len_val, ctx, float(len(raw_text)))) if str(len_val).strip() != "" else len(raw_text)
            return raw_text[s:s+l]
        except Exception:
            return raw_text

    elif op_clean in ("length", "len"):
        return str(len(raw_text))

    elif op_clean in ("contains", "contain"):
        search = get_str("Search", get_str("search", ""))
        return "1" if search in raw_text else "0"

    elif op_clean in ("kana", "transliteratekana"):
        mode = get_str("Kana Mode", get_str("kana_mode", get_str("Mode", get_str("mode", "Romaji to Hiragana"))))
        return text_transliterate_kana(ctx, text=raw_text, mode=mode)

    elif op_clean in ("romajitokaraoke", "tokara", "karaoke"):
        kmode = get_str("K Mode", get_str("k_mode", get_str("kmode", "k")))
        dur_val = kwargs.get("Duration (cs)", kwargs.get("duration", kwargs.get("Duration", None)))
        return text_romaji_to_karaoke(ctx, text=raw_text, kmode=kmode, duration=dur_val)

    else:
        return raw_text



def text_to_shape_node(context, text="", font_name=None, font_size=None, bold=None, italic=None, scale=1.0):
    from font_vector_engine import FontVectorEngine
    return FontVectorEngine.from_context(
        text=text,
        context=context,
        font_name=font_name,
        font_size=font_size,
        bold=bold,
        italic=italic,
        scale=scale
    )


def text_on_path_core(
    shape_str: str,
    context: dict = None,
    mode: str = "Center (Centrado)",
    offset: float = 0.0,
    extra_angle: float = 0.0,
    subdivs: int = 30
):
    """Calculates position and tangential angle of active text element along an ASSdraw path.
    
    Returns tuple: (tag_out, pos_str, angle_str, x_val, y_val, total_length, target_dist)
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

    l_width = float(getattr(line, 'width', getattr(unit, 'width', 0.0))) if line else float(getattr(unit, 'width', 0.0) if unit else 0.0)
    l_left = float(getattr(line, 'left', getattr(unit, 'left', 0.0))) if line else float(getattr(unit, 'left', 0.0) if unit else 0.0)
    u_center = float(getattr(unit, 'center', getattr(unit, 'x', l_left + l_width / 2.0))) if unit else (l_left + l_width / 2.0)
    
    unit_dist_in_line = u_center - l_left if line else (l_width / 2.0)

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
    else:
        lineoffset = (total_len - l_width) / 2.0 + offset_val

    target = lineoffset + unit_dist_in_line

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
                else:
                    u = _map_dist_to_bezier_u(local_d, s_info['chord_lens'], sub)
                    p0, p1, p2, p3 = seg['p0'], seg['p1'], seg['p2'], seg['p3']
                    cur_x, cur_y = _eval_bezier_pt(p0, p1, p2, p3, u)
                    dx, dy = _eval_bezier_tangent(p0, p1, p2, p3, u)
                found_pt = True
                break
        if found_pt:
            break

    if not found_pt:
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
    mode="Center",
    offset=0.0,
    extra_angle=0.0,
    subdivs=30
):
    """Controller for Text on Path node (Functions / Text)."""
    from node_engine import _eval_num_expr

    ctx = context or {}
    shp_val = str(shape or "").strip()
    mode_str = str(mode or "Center").strip()

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


NODE_REGISTRY["Basics/Text"] = eval_text_node
NODE_REGISTRY["Text"] = eval_text_node
NODE_REGISTRY["Functions/Text on Path"] = text_on_path_node
NODE_REGISTRY["Text on Path"] = text_on_path_node
NODE_REGISTRY["Text/Text on Path"] = text_on_path_node
NODE_REGISTRY["Romaji to Karaoke"] = text_romaji_to_karaoke
NODE_REGISTRY["Functions/Romaji to Karaoke"] = text_romaji_to_karaoke
NODE_REGISTRY["Text/Romaji to Karaoke"] = text_romaji_to_karaoke


def _resolve_context_style(context):
    if isinstance(context, dict):
        st = context.get('style') or context.get('active_style') or context.get('styleref')
        if isinstance(st, dict):
            return st
        if st is not None:
            d = {}
            for k in ("name", "fontname", "fontsize", "bold", "italic", "underline", "strikeout",
                      "scale_x", "scale_y", "spacing", "angle", "borderstyle", "outline",
                      "shadow", "align", "alignment", "margin_l", "margin_r", "margin_v",
                      "color1", "color2", "color3", "color4"):
                if hasattr(st, k):
                    d[k] = getattr(st, k)
            if d:
                return d
        line = context.get('active_line') or context.get('line')
        if line and hasattr(line, 'styleref'):
            return _resolve_context_style({'style': line.styleref})
    return {"fontname": "Arial", "fontsize": 30.0, "scale_x": 100.0, "scale_y": 100.0, "spacing": 0.0}


def _split_axis_transitions(t_matches, off_init, tag_name):
    vals = [off_init]
    parsed = []
    for t in t_matches:
        m_t = re.match(r'\\t\(\s*(\d+(?:\.\d+)?)\s*,\s*(\d+(?:\.\d+)?)\s*,', t)
        if not m_t:
            continue
        st = float(m_t.group(1))
        et = float(m_t.group(2))
        m_v = re.search(rf'{re.escape(tag_name)}(-?\d+(?:\.\d+)?)', t)
        v = float(m_v.group(1)) if m_v else 0.0
        vals.append(v)
        parsed.append((st, et, v))

    trans_p = []
    trans_n = []

    for i, (st, et, v) in enumerate(parsed):
        prev_v = vals[i]

        if prev_v >= 0 and v >= 0:
            trans_p.append(f"\\t({st:.2f},{et:.2f},{tag_name}{v:.2f})")
        elif prev_v <= 0 and v <= 0:
            trans_n.append(f"\\t({st:.2f},{et:.2f},{tag_name}{abs(v):.2f})")
        elif prev_v > 0 and v < 0:
            frac = prev_v / (prev_v - v)
            t_split = st + (et - st) * frac
            trans_p.append(f"\\t({st:.2f},{t_split:.2f},{tag_name}0.00)")
            trans_n.append(f"\\t({t_split:.2f},{et:.2f},{tag_name}{abs(v):.2f})")
        elif prev_v < 0 and v > 0:
            frac = abs(prev_v) / (v - prev_v)
            t_split = st + (et - st) * frac
            trans_n.append(f"\\t({st:.2f},{t_split:.2f},{tag_name}0.00)")
            trans_p.append(f"\\t({t_split:.2f},{et:.2f},{tag_name}{v:.2f})")

    return trans_p, trans_n


def move_text_node(
    context=None,
    text=None,
    tags=None,
    dx=0.0,
    dy=0.0,
    ox=0.0,
    oy=0.0,
    trajectory=None,
    anchor="center",
    shape="",
    points=None,
    step_px=7.5,
    t1=0.0,
    t2=None,
    accel=1.0,
    **kwargs
):
    """
    Translates text position using character spacing (fsp) and vertical spacer shapes (fscy),
    matching the exact ASS layout hack from Effector 2's ke.text.move in newkara_library.
    Supports 2D trajectories (shapes or point lists) with geometric anchor normalization.
    """
    from font_engine import FontEngine
    from nodes.tag_nodes import (
        _clean_num,
        _get_default_dur,
        _resample_shape_arc_length,
        _parse_points_input
    )

    configs = kwargs.get("configs") or kwargs.get("segments")
    if isinstance(configs, list) and len(configs) > 0:
        valid_packs = [c for c in configs if isinstance(c, dict)]
        if valid_packs:
            chained = []
            for pack in valid_packs:
                sub_kw = dict(kwargs)
                sub_kw.pop("configs", None)
                sub_kw.pop("segments", None)
                sub_kw.update(pack)
                chained.append(move_text_node(context=context, text=text, tags=tags, **sub_kw))
            return "".join(chained)

    raw_text = _get_text(context, text or kwargs.get("texto") or kwargs.get("text"))
    st_dict = _resolve_context_style(context)

    add_tags = str(tags if tags is not None else (kwargs.get("tags") or kwargs.get("add_tags") or "")).strip()
    if not add_tags and context and isinstance(context, dict):
        add_tags = str(context.get("tags") or context.get("add_tags") or "").strip()
    add_tags = add_tags.replace(r"\\", "\\")

    try:
        w_dot = float(FontEngine.get_text_extents(st_dict, ".")[0])
        w_space = float(FontEngine.get_text_extents(st_dict, " ")[0])
    except Exception:
        w_dot = 7.5
        w_space = 10.0

    is_shape = bool(raw_text.strip().startswith("m ") or raw_text.strip().startswith(r"{\p1}") or raw_text.strip().startswith(r"\p1"))
    if not is_shape:
        trailing_spaces = len(raw_text) - len(raw_text.rstrip(' '))
        ini_x = w_dot + trailing_spaces * w_space
        tagsi = f"{{\\p0}}\\N{{\\r{add_tags}\\q2}}{raw_text}"
        tagsa = "\\r\\alpha&HFF&"
    else:
        ini_x = w_dot
        tagsi = f"{{\\p0}}\\N{{\\r{add_tags}\\p1}}{raw_text}"
        tagsa = "\\p0\\r\\alpha&HFF&"

    def_dur = _get_default_dur(context)
    t1_val = _clean_num(kwargs.get("t1") if "t1" in kwargs else t1, default=0, context=context)
    t1_f = float(t1_val) if t1_val is not None else 0.0
    t2_param = kwargs.get("t2") if "t2" in kwargs else t2
    t2_val = _clean_num(t2_param, default=def_dur, context=context) if t2_param is not None else def_dur
    t2_f = float(t2_val) if t2_val is not None else def_dur

    accel_val = _clean_num(kwargs.get("accel") if "accel" in kwargs else accel, default=1.0, context=context)
    accel_f = float(accel_val) if accel_val is not None else 1.0
    if accel_f <= 0:
        accel_f = 1.0

    ox_f = float(_clean_num(kwargs.get("ox") if "ox" in kwargs else ox, default=0.0, context=context))
    oy_f = float(_clean_num(kwargs.get("oy") if "oy" in kwargs else oy, default=0.0, context=context))
    step_f = float(_clean_num(kwargs.get("step_px") if "step_px" in kwargs else step_px, default=7.5, context=context))
    if step_f <= 0:
        step_f = 7.5

    traj_raw = trajectory if trajectory is not None else (
        kwargs.get("trajectory") or kwargs.get("shape") or kwargs.get("points") or shape or points or ""
    )
    anchor_mode = str(kwargs.get("anchor") if "anchor" in kwargs else anchor or "center").strip().lower()

    pts = []
    if traj_raw:
        pts = _parse_points_input(traj_raw, step_px=step_f)

    if pts:
        if anchor_mode == "first_point":
            p0_x, p0_y = pts[0][0], pts[0][1]
            pts = [(p[0] - p0_x, p[1] - p0_y, p[2] if len(p) >= 3 else 0.0) for p in pts]
        elif anchor_mode == "origin":
            pass
        else:  # "center" fallback
            xs = [p[0] for p in pts]
            ys = [p[1] for p in pts]
            bx = (min(xs) + max(xs)) / 2.0
            by = (min(ys) + max(ys)) / 2.0
            pts = [(p[0] - bx, p[1] - by, p[2] if len(p) >= 3 else 0.0) for p in pts]

    if pts and len(pts) > 1:
        start_x = ox_f + pts[0][0]
        start_y = oy_f + pts[0][1]
    else:
        start_x = ox_f
        start_y = oy_f

    off_x = 2.0 * start_x
    off_y = 2.0 * start_y
    acc_str = f"{accel_f:.2f}," if abs(accel_f - 1.0) > 0.05 else ""

    tagsx_trans = []
    tagsy_trans = []

    if pts and len(pts) > 1:
        tot_time = max(1.0, t2_f - t1_f)
        total_dist = max(1e-6, pts[-1][2])
        has_dist = len(pts[0]) >= 3

        for i in range(1, len(pts)):
            if has_dist:
                norm_d1 = (pts[i-1][2] / total_dist) ** accel_f
                norm_d2 = (pts[i][2] / total_dist) ** accel_f
            else:
                norm_d1 = ((i - 1) / (len(pts) - 1)) ** accel_f
                norm_d2 = (i / (len(pts) - 1)) ** accel_f
            st = int(round(t1_f + tot_time * norm_d1))
            et = int(round(t1_f + tot_time * norm_d2))
            px = ox_f + pts[i][0]
            py = oy_f + pts[i][1]
            tagsx_trans.append(f"\\t({st},{et},\\fsp{px:.2f})")
            tagsy_trans.append(f"\\t({st},{et},\\fscy{py:.2f})")
    else:
        dx_raw = kwargs.get("dx") if "dx" in kwargs else dx
        dy_raw = kwargs.get("dy") if "dy" in kwargs else dy

        st = int(round(t1_f))
        et = int(round(t2_f))

        dx_str = str(dx_raw).strip() if dx_raw is not None else ""
        if "\\" in dx_str:
            tagsx_trans.append(dx_str)
        else:
            dx_f = float(_clean_num(dx_raw, default=0.0, context=context)) if (dx_raw is not None and dx_str != "") else 0.0
            if abs(dx_f) > 1e-5:
                tagsx_trans.append(f"\\t({st},{et},{acc_str}\\fsp{ox_f + dx_f:.2f})")

        dy_str = str(dy_raw).strip() if dy_raw is not None else ""
        if "\\" in dy_str:
            tagsy_trans.append(dy_str)
        else:
            dy_f = float(_clean_num(dy_raw, default=0.0, context=context)) if (dy_raw is not None and dy_str != "") else 0.0
            if abs(dy_f) > 1e-5:
                tagsy_trans.append(f"\\t({st},{et},{acc_str}\\fscy{oy_f + dy_f:.2f})")

    raw_tagsx = "".join(tagsx_trans)
    doubled_tagsx = re.sub(
        r'\\fsp(-?\d+(?:\.\d+)?)',
        lambda m: f"\\fsp{2.0 * float(m.group(1)):.2f}",
        raw_tagsx
    )
    t_matches_x = re.findall(r'\\t\([^)]+\)', doubled_tagsx)
    transfo_px, transfo_nx = _split_axis_transitions(t_matches_x, off_x, "\\fsp")

    mov_x1_val = off_x if off_x >= 0 else 0.0
    mov_x1 = f"\\fsp{mov_x1_val:.2f}"
    mov_x2_val = -off_x if off_x < 0 else 0.0
    mov_x2 = f"\\fsp{mov_x2_val:.2f}"

    raw_tagsy = "".join(tagsy_trans)
    doubled_tagsy = re.sub(
        r'\\fscy(-?\d+(?:\.\d+)?)',
        lambda m: f"\\fscy{2.0 * float(m.group(1)):.2f}",
        raw_tagsy
    )
    t_matches_y = re.findall(r'\\t\([^)]+\)', doubled_tagsy)
    transfo_p, transfo_n = _split_axis_transitions(t_matches_y, off_y, "\\fscy")

    mov_y1_val = off_y if off_y >= 0 else 0.0
    mov_y1 = f"\\r\\fscy{mov_y1_val:.2f}"
    mov_y2_val = -off_y if off_y < 0 else 0.0
    mov_y2 = f"\\r\\fscy{mov_y2_val:.2f}"

    if not is_shape:
        mov_h1 = f"{{\\r\\alpha&HFF&{mov_x1}{''.join(transfo_px)}}}."
        text_block = f"{{\\r{add_tags}\\q2}}{raw_text}"
        mov_h2 = f"{{\\r\\alpha&HFF&{mov_x2}{''.join(transfo_nx)}}}."
    else:
        mov_h1 = f"{{\\p0\\r\\alpha&HFF&{mov_x1}{''.join(transfo_px)}}}."
        text_block = f"{{\\r{add_tags}\\p1}}{raw_text}"
        mov_h2 = f"{{\\p0\\r\\alpha&HFF&{mov_x2}{''.join(transfo_nx)}}}."

    mov_v1 = f"{{{mov_y1}{''.join(transfo_p)}\\p1}}m 0 0 m 0 100 {{\\p0}}\\N"
    mov_v2 = f"\\N{{{mov_y2}{''.join(transfo_n)}\\p1}}m 0 0 m 0 100 "

    return f"{mov_v1}{mov_h1}{text_block}{mov_h2}{mov_v2}"


@pyxis_node("Functions", "Move Text", [])
def MoveTextNode(context=None, *args, **kwargs):
    return move_text_node(context=context, *args, **kwargs)

NODE_REGISTRY["Functions/Move Text"] = MoveTextNode
NODE_REGISTRY["Move Text"] = MoveTextNode
NODE_REGISTRY["Text/Move Text"] = MoveTextNode


