# -*- coding: utf-8 -*-
# Port de `ke.text` (newkara_library.lua de Effector).
# Copyright (c) 2026, Víctor Manuel Payares - All rights reserved. Ver ke_common.py.

"""Texto: tablas de romaji/kana, limpieza de tags, mayusculas sin tocar tags y conversiones. Puro.

Pendiente (dependen de metricas de fuente / `ke.shape` / estado del motor): `to_shape`, `bezier`,
`to_parts`, `rand`, `move`, `to_kara` (usa `ke.config.text2word`).
Notas: ROMAJI/HIRAGANA/KATAKANA se conservan tal cual, pero NO son tablas paralelas (el orden difiere), asi que
las conversiones por indice del original eran incorrectas. Aqui `syl2hiragana`, `syl2katakana`, `kana2romaji`
y `kana_for_romaji` usan un mapa kana <-> romaji real.
"""

from __future__ import annotations

import re
from typing import List, Optional, Sequence

ROMAJI: List[str] = [
    "kya", "kyu", "kyo", "sha", "shu", "sho", "cha", "chu", "cho", "nya", "nyu", "nyo", "hya", "hyu", "hyo",
    "mya", "myu", "myo", "rya", "ryu", "ryo", "gya", "gyu", "gyo", "bya", "byu", "byo", "pya", "pyu", "pyo",
    "shi", "chi", "tsu", "ya", "yu", "yo", "ka", "ki", "ku", "ke", "ko", "sa", "su", "se", "so", "ta", "te",
    "to", "na", "ni", "nu", "ne", "no", "ha", "hi", "fu", "he", "ho", "ma", "mi", "mu", "me", "mo", "ya", "yu",
    "yo", "ra", "ri", "ru", "re", "ro", "wa", "wi", "we", "wo", "ga", "gi", "gu", "ge", "go", "za", "ji", "zu",
    "ze", "zo", "ja", "ju", "jo", "da", "di", "du", "de", "do", "ba", "bi", "bu", "be", "bo", "pa", "pi", "pu",
    "pe", "po", "a", "i", "u", "e", "o", "n", "b", "c", "d", "k", "p", "r", "s", "t", "z",
]

# Tablas de kana del original, tal cual (no son paralelas a ROMAJI: ver `kana_for_romaji`).
HIRAGANA: List[str] = [
    "あ", "い", "う", "え", "お", "ゃ", "ゅ", "ょ", "か", "き", "く", "け",
    "こ", "きゃ", "きゅ", "きょ", "さ", "し", "す", "せ", "そ", "しゃ", "しゅ", "しょ",
    "た", "ち", "つ", "て", "と", "ちゃ", "ちゅ", "ちょ", "な", "に", "ぬ", "ね",
    "の", "にゃ", "にゅ", "にょ", "は", "ひ", "ふ", "へ", "ほ", "ひゃ", "ひゅ", "ひょ",
    "ま", "み", "む", "め", "も", "みゃ", "みゅ", "みょ", "や", "ゆ", "よ", "ら",
    "り", "る", "れ", "ろ", "りゃ", "りゅ", "りょ", "わ", "ゐ", "ゑ", "を", "ん",
    "が", "ぎ", "ぐ", "げ", "ご", "ぎゃ", "ぎゅ", "ぎょ", "ざ", "じ", "ず", "ぜ",
    "ぞ", "じゃ", "じゅ", "じょ", "だ", "ぢ", "づ", "で", "ど", "ば", "び", "ぶ",
    "べ", "ぼ", "びゃ", "びゅ", "びょ", "ぱ", "ぴ", "ぷ", "ぺ", "ぽ", "ぴゃ", "ぴゅ",
    "ぴょ", "っ", "っ", "っ", "っ", "っ", "っ", "っ", "っ", "っ",
]
KATAKANA: List[str] = [
    "ア", "イ", "ウ", "エ", "オ", "ャ", "ュ", "ョ", "カ", "キ", "ク", "ケ", "コ", "キャ", "キュ", "キョ",
    "サ", "シ", "ス", "セ", "ソ", "シャ", "シュ", "ショ", "タ", "チ", "ッ", "テ", "ト", "チャ", "チュ", "チョ",
    "ナ", "ニ", "ヌ", "ネ", "ノ", "ニャ", "ニュ", "ニョ", "ハ", "ヒ", "フ", "ヘ", "ホ", "ヒャ", "ヒュ", "ヒョ",
    "マ", "ミ", "ム", "メ", "モ", "ミャ", "ミュ", "ミョ", "ヤ", "ユ", "ヨ", "ラ", "リ", "ル", "レ", "ロ",
    "リャ", "リュ", "リョ", "ワ", "ヰ", "ヱ", "ヲ", "ン", "ガ", "ギ", "グ", "ゲ", "ゴ", "ギャ", "ギュ", "ギョ",
    "ザ", "ジ", "ズ", "ゼ", "ゾ", "ジャ", "ジュ", "ジョ", "ダ", "ヂ", "ヅ", "デ", "ド", "バ", "ビ", "ブ", "ベ",
    "ボ", "ビャ", "ビュ", "ビョ", "パ", "ピ", "プ", "ペ", "ポ", "ピャ", "ピュ", "ピョ", "ッ", "ッ", "ッ", "ッ",
    "ッ", "ッ", "ッ", "ッ", "ッ",
]
CHAR_UPPER = list("ABCDEFGHIJKLMNÑOPQRSTUVWXYZ")
CHAR_LOWER = list("abcdefghijklmnñopqrstuvwxyz")
CHAR_NUMBER = list("1234567890")
CHAR_SPECIAL = list("°¬¡!¿?()[]^'-#$%&;:,.<>*~´`¨+/{}|_\\\"")

# Tags que se conservan con keeptags (regex equivalentes a los patrones Lua del original).
KEEPTAGS = [
    r"\\bord-?\d[.\d]*", r"\\xbord-?\d[.\d]*", r"\\ybord-?\d[.\d]*", r"\\shad-?\d[.\d]*", r"\\xshad-?\d[.\d]*",
    r"\\yshad-?\d[.\d]*", r"\\blur-?\d[.\d]*", r"\\be-?\d[.\d]*", r"\\3c[\d&]*[.\dH0-9A-Fa-f&]*", r"\\fscx-?\d[.\d]*",
    r"\\fscy-?\d[.\d]*", r"\\alpha[\d&]*[.\dH0-9A-Fa-f&]*", r"\\fax-?\d[.\d]*", r"\\fay-?\d[.\d]*",
    r"\\1a[\d&]*[.\dH0-9A-Fa-f&]*", r"\\frx-?\d[.\d]*", r"\\fry-?\d[.\d]*", r"\\3a[\d&]*[.\dH0-9A-Fa-f&]*",
    r"\\fsp-?\d[.\d]*", r"\\fs-?\d[.\d]*", r"\\4a[\d&]*[.\dH0-9A-Fa-f&]*", r"\\clip\([^)]*\)", r"\\iclip\([^)]*\)",
    r"\\1?c[\d&]*[.\dH0-9A-Fa-f&]*", r"\\fad\([^)]*\)", r"\\fr[z]*-?\d[.\d]*", r"\\4c[\d&]*[.\dH0-9A-Fa-f&]*",
]

_TAG_BLOCK = re.compile(r"\{[^{}]*\}")


def remove(text: str, mode: str) -> str:
    """ke.text.remove: mode = "tags" | "extra_space" | "space_in_tags"."""
    if mode == "tags":
        return _TAG_BLOCK.sub("", text)
    if mode == "extra_space":
        return text.strip(" \t")

    if mode == "space_in_tags":
        def tidy(block: re.Match) -> str:
            shapes = re.sub(r"m\s+-?\d[.\-\d mlb]*", lambda m: m.group(0).replace(" ", "\u20ac"), block.group(0))
            return shapes.replace(" ", "").replace("\u20ac", " ")
        return _TAG_BLOCK.sub(tidy, text)
    return text


def _map_outside_tags(text: str, fn) -> str:
    parts = re.split(r"(\{[^{}]*\})", text)
    return "".join(p if p.startswith("{") else fn(p) for p in parts)


def to_upper(text: str) -> str:
    """ke.text.to_upper: mayusculas sin tocar los bloques {tags}."""
    return _map_outside_tags(text, str.upper)


def to_lower(text: str) -> str:
    """ke.text.to_lower: minusculas sin tocar los bloques {tags}."""
    return _map_outside_tags(text, str.lower)


def char2byte(text: str) -> List[int]:
    """Codigos de cada caracter (code points)."""
    return [ord(c) for c in text]


def byte2char(codes: Sequence[int]) -> str:
    return "".join(chr(c) for c in codes)


def _to_hiragana(kata: str) -> str:
    return "".join(chr(ord(c) - 0x60) if "ァ" <= c <= "ヶ" else c for c in kata)


def _to_katakana(hira: str) -> str:
    return "".join(chr(ord(c) + 0x60) if "ぁ" <= c <= "ゖ" else c for c in hira)


_KANA_ROMAJI = {
    "あ": "a", "い": "i", "う": "u", "え": "e", "お": "o", "か": "ka", "き": "ki", "く": "ku", "け": "ke", "こ": "ko",
    "さ": "sa", "し": "shi", "す": "su", "せ": "se", "そ": "so", "た": "ta", "ち": "chi", "つ": "tsu", "て": "te",
    "と": "to", "な": "na", "に": "ni", "ぬ": "nu", "ね": "ne", "の": "no", "は": "ha", "ひ": "hi", "ふ": "fu",
    "へ": "he", "ほ": "ho", "ま": "ma", "み": "mi", "む": "mu", "め": "me", "も": "mo", "や": "ya", "ゆ": "yu",
    "よ": "yo", "ら": "ra", "り": "ri", "る": "ru", "れ": "re", "ろ": "ro", "わ": "wa", "ゐ": "wi", "ゑ": "we",
    "を": "wo", "ん": "n", "が": "ga", "ぎ": "gi", "ぐ": "gu", "げ": "ge", "ご": "go", "ざ": "za", "じ": "ji",
    "ず": "zu", "ぜ": "ze", "ぞ": "zo", "だ": "da", "ぢ": "di", "づ": "du", "で": "de", "ど": "do", "ば": "ba",
    "び": "bi", "ぶ": "bu", "べ": "be", "ぼ": "bo", "ぱ": "pa", "ぴ": "pi", "ぷ": "pu", "ぺ": "pe", "ぽ": "po",
}
_ROMAJI_KANA = {v: k for k, v in _KANA_ROMAJI.items()}
_ROMAJI_KANA.update({"si": "し", "ti": "ち", "tu": "つ", "hu": "ふ", "zi": "じ"})
_SMALL = {"ゃ": "a", "ゅ": "u", "ょ": "o"}
_DIGRAPH_BASE = {"ky": "き", "sh": "し", "ch": "ち", "ny": "に", "hy": "ひ", "my": "み", "ry": "り", "gy": "ぎ",
                 "j": "じ", "by": "び", "py": "ぴ"}


def kana_for_romaji(syl: str, katakana: bool = False) -> Optional[str]:
    """Kana de una silaba romaji ("ka" -> か, "kya" -> きゃ); None si no se reconoce."""
    key = syl.strip().lower()
    kana = _ROMAJI_KANA.get(key)
    if kana is None and len(key) >= 2 and key[-1] in "auo" and key[:-1] in _DIGRAPH_BASE:
        kana = _DIGRAPH_BASE[key[:-1]] + {v: k for k, v in _SMALL.items()}[key[-1]]
    if kana is None:
        return None
    return _to_katakana(kana) if katakana else kana


def syl2hiragana(text: str) -> str:
    """ke.text.syl2hiragana: romaji o katakana -> hiragana (el resto, intacto)."""
    return kana_for_romaji(text) or _to_hiragana(text)


def syl2katakana(text: str) -> str:
    """ke.text.syl2katakana: romaji o hiragana -> katakana (el resto, intacto)."""
    return kana_for_romaji(text, katakana=True) or _to_katakana(text)


def kana2romaji(text: str) -> str:
    """ke.text.kana2romaji: kana (hiragana o katakana) -> romaji, con digrafos (きゃ -> kya) y っ (geminada)."""
    hira, out, i = _to_hiragana(text), [], 0
    while i < len(hira):
        c = hira[i]
        nxt = hira[i + 1] if i + 1 < len(hira) else ""
        base = _KANA_ROMAJI.get(c)
        if base and base.endswith("i") and nxt in _SMALL:
            stem = base[:-1]
            out.append(stem + _SMALL[nxt] if stem in ("sh", "ch", "j") else stem + "y" + _SMALL[nxt])
            i += 2
            continue
        if c == "っ" and nxt in _KANA_ROMAJI:
            out.append(_KANA_ROMAJI[nxt][0])
        else:
            out.append(base or c)
        i += 1
    return "".join(out)
