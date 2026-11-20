# -*- coding: utf-8 -*-
# Generador de codigo Python desde la libreria de efectos de Kara Effector 3.6 legacy (Effector-3.6.lua).
# (c) 2012-2020 Vict8r, Karalaura, NatsuoKE & Itachi Akatsuki.

"""Convierte un efecto de Kara Effector 3.6 (`FxTemplate`) en el codigo Python de un efecto editable. Puro.

Los tiempos salen como `retime(...)` de Python con el modo oficial de Effector. Las expresiones se traducen desde
el lenguaje de plantillas (atajos `50li`, `10r`, `10f`, tablas, `..`, `~=`...). Lo que depende de utilidades de
`Effector-utils-lib-3.6.lua` aun no portadas se llama igual (`tag.clip`, `shape.lmove`...) y, al ejecutarse, avisa en
que linea del Lua esta; lo que no se puede traducir queda como `untranslated(...)` con su texto original.
"""

from __future__ import annotations

import json
import re
from typing import Dict, List, Optional, Tuple

from ..entities.fx_template import FxTemplate
from . import ke_color
from .ke3 import GLOBALS as _KE3_GLOBALS, NAMESPACES as _KE3_NAMESPACES
from .ke_lua import expand_units, lua_expr, split_statements, split_top

_PY_MATH = {"sin", "cos", "tan", "asin", "acos", "atan", "atan2", "ceil", "floor", "pi", "sqrt", "rad", "deg", "log", "ln"}
_BUILTIN = {"len", "min", "max", "abs", "round", "int", "float", "str", "range", "sum", "None", "True", "False", "and",
            "or", "not", "if", "else", "in", "is", "for", "lambda", "type", "tostring", "tonumber", "ipairs", "pairs"}
_PROVIDED = {"fx", "line", "l", "syl", "char", "word", "unit", "j", "maxj", "i", "ratio", "frame_dur", "xres", "yres",
             "format", "start", "end", "text", "sylchar"}
_UNIT_TIME = ("time_li", "time_lo", "time_mid1", "time_mid2")
# nombres que declara el propio codigo generado (no son "faltantes")
_GENERATED = {"fmt", "out", "layer", "pos_x", "pos_y", "tags", "tag_post", "cat", "compose", "lt", "untranslated", "units", "Fx", "Unit",
              "ke3", "run", "NAME", "STYLE", "int", "bool", "kind", "noblank"}


def _py_str(s: str) -> str:
    """Literal de cadena de Python valido (escapa comillas, barras y saltos de linea)."""
    return json.dumps(s, ensure_ascii=False)


def _template_kind(template: str) -> Tuple[str, bool]:
    """(syl|char|word|line, es_soportada). Las plantillas de traduccion u otras especiales se tratan como la
    mas parecida y se avisa."""
    t = (template or "").lower()
    plain = {"syl": "syl", "char": "char", "word": "word", "line": "line"}
    if t in plain:
        return plain[t], True
    for key in ("char", "word", "syl", "line"):
        if key in t:
            return key, False
    return "syl", False


def _identifiers(code: str) -> List[str]:
    """Identificadores libres del codigo Python generado (sin cadenas, sin atributos tras un punto)."""
    stripped = re.sub(r"\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'", '""', code)
    return re.findall(r"(?<![\w.])([A-Za-z_]\w*)", stripped)


def _time_parts(expr: str, kind: str) -> Tuple[Optional[str], str]:
    """Separa una expresion de tiempo en (base, desplazamiento). base: ls | le | ws | we | ss | se | cs | ce | None."""
    s = re.sub(r"\s+", " ", expr.strip())
    s = re.sub(r"\bline\.", "l.", s)
    bases = [("l.start_time + syl.start_time", "ss"), ("l.start_time + syl.end_time", "se"),
             ("l.start_time + word.start_time", "ws"), ("l.start_time + word.end_time", "we"),
             ("l.start_time + char.start_time", "cs"), ("l.start_time + char.end_time", "ce"),
             ("l.start_time", "ls"), ("l.end_time", "le")]
    for text, tag in bases:
        if s.startswith(text):
            rest = s[len(text):].strip()
            if rest and rest[0] not in "+-":
                return None, expr
            return tag, rest or "0"
    return None, expr


_RETIME = {
    ("ls", "le"): "line", ("ls", "ls"): "preline", ("le", "le"): "postline",
    ("ws", "we"): "word", ("ws", "ws"): "preword", ("we", "ws"): "postword",
    ("ss", "se"): "syl", ("ss", "ss"): "presyl", ("se", "se"): "postsyl",
    ("cs", "ce"): "char", ("cs", "cs"): "prechar", ("ce", "cs"): "postchar",
    ("ls", "ws"): "start2word", ("we", "le"): "word2end", ("ls", "ss"): "start2syl", ("se", "le"): "syl2end",
    ("ls", "cs"): "start2char", ("ce", "le"): "char2end", ("ss", "cs"): "startsyl2char",
    ("ws", "ss"): "startword2syl", ("ws", "cs"): "startword2char", ("se", "we"): "syl2endword",
    ("ce", "se"): "char2endsyl", ("ce", "we"): "char2endword",
}


def retime_mode(start: str, end: str, kind: str = "syl") -> Optional[Tuple[str, str, str]]:
    """Si (start, end) equivale a un modo de `retime`, devuelve (modo, desplazamiento_inicio, desplazamiento_fin)."""
    (bs, offs), (be, offe) = _time_parts(start, kind), _time_parts(end, kind)
    mode = _RETIME.get((bs, be)) if bs and be else None
    return (mode, offs, offe) if mode else None


class _Gen:
    def __init__(self, fx: FxTemplate, style: Optional[str], name: Optional[str]):
        self.fx, self.style, self.name = fx, style, name or fx.name
        self.kind, self.supported = _template_kind(fx.template)
        self.unit = "unit" if self.kind == "line" else self.kind
        self.notes: List[str] = []
        self.defined: set = set()

    # ---- traduccion de un campo ------------------------------------------------------------------------
    def expr(self, field: str, raw: object, join: bool = False) -> str:
        """Python equivalente de un campo; si no compila, `untranslated(campo, texto_original)`."""
        text = str(raw if raw is not None else "").strip()
        if not text:
            return '""' if join else "None"
        try:
            parts = [expand_units(p.strip(), self.unit) for p in split_top(text)] if join else [expand_units(text, self.unit)]
            py = [lua_expr(p, shift_indices=False) for p in parts]
            code = py[0] if len(py) == 1 else "cat(%s)" % ", ".join(py)
            compile(code, "<%s>" % field, "eval")
            return code
        except SyntaxError:
            self.notes.append("%s sin traducir" % field)
            return "untranslated(%s, %s)" % (_py_str(field), _py_str(text))

    # ---- generacion -----------------------------------------------------------------------------------
    def build(self) -> str:
        fx, kind, unit = self.fx, self.kind, self.unit
        body: List[str] = ["j, maxj = 1, 1"]     # como en Effector: existen antes del bucle
        center_x = self.expr("center_x", fx.center_x) if str(fx.center_x).strip() else None
        center_y = self.expr("center_y", fx.center_y) if str(fx.center_y).strip() else None
        body.append("fx = Fx(%s%s)" % (unit, ", pos_x=%s, pos_y=%s" % (center_x or "None", center_y or "None")
                                       if (center_x or center_y) else ""))
        body.append("ke3.bind(fx, line, %s, 1)" % unit)
        # variables (sentencias de Lua)
        for stmt in split_statements(str(fx.variables or "")):
            stmt = re.sub(r"^local\s+", "", stmt)
            m = re.match(r"([A-Za-z_]\w*)\s*=(?!=)\s*(.*)$", stmt, re.S)
            if m and not stmt.startswith("function"):
                body.append("%s = %s" % (m.group(1), self.expr("variables." + m.group(1), m.group(2))))
                self.defined.add(m.group(1))
            else:
                body.append("# TODO (variables): sentencia de Lua sin traducir: %s" % stmt.replace("\n", " ")[:110])
                self.notes.append("variables sin traducir")
        # tiempos: retime oficial
        found = retime_mode(str(fx.start), str(fx.end), kind)
        if found:
            mode, t1, t2 = found
            a = self.expr("start", t1.lstrip("+ ")) if t1 != "0" else "0"
            b = self.expr("end", t2.lstrip("+ ")) if t2 != "0" else "0"
            body.append('start, end = ke3.time.retime(%s, "%s", %s, %s)' % (unit, mode, a, b))
        else:
            body.append("start = %s" % self.expr("start", fx.start))
            body.append("end = %s" % self.expr("end", fx.end))
        # tras retime: el tiempo de la linea de efecto es parte del estado `fx` (lo usan tag.clip, etc.)
        body.append("fx.start_time, fx.end_time, fx.dur = start, end, end - start")
        # bucle: `loop` es una tabla {v, h, 3}; maxj = loop_v * loop_h * loop_3 (como en Effector-3.6.lua)
        loop_parts = [p.strip() for p in split_top(str(fx.loop)) if p.strip()] or ["1"]
        looped = loop_parts != ["1"]
        if looped:
            exprs = [self.expr("loop", p) for p in loop_parts[:3]]
            exprs += ["1"] * (3 - len(exprs))
            body.append("fx.loop_v, fx.loop_h, fx.loop_3 = %s" % ", ".join("ceil(%s)" % e for e in exprs))
            body.append("fx.maxloop_fx = maxj = fx.loop_v * fx.loop_h * fx.loop_3")
        inner: List[str] = ["ke3.bind(fx, line, %s, j)" % unit]
        inner.append("text = %s" % self.expr("return", fx.return_, join=True))
        for axis, value in (("x", fx.pos_x), ("y", fx.pos_y)):
            parts = split_top(str(value))
            if len(parts) > 1:
                inner.append("# TODO: pos_%s tiene varios valores (movimiento): %s" % (axis, str(value).strip()))
            inner.append("pos_%s = %s" % (axis, self.expr("pos_" + axis, parts[0] if parts else value)))
        shape_tags = ""
        if fx.kind == "SHfx":
            def col(c):
                try:
                    return ke_color.ass(str(c))
                except ValueError:
                    return "&HFFFFFF&"
            shape_tags = "\\1c%s\\3c%s\\4c%s\\p1" % (col(fx.color1), col(fx.color3), col(fx.color4))
        tags = self.expr("add_tags", fx.add_tags, join=True) if str(fx.add_tags or "").strip() else '""'
        inner.append("tags = %s" % tags)
        if str(fx.add_tags or "").strip():
            inner.append("tags = tag_post(tags, %s, start)   # tags compuestos, \\t(modo, ...) -> tiempos reales" % unit)
        align = self.expr("align", fx.align) if str(fx.align).strip() else "5"
        layer = self.expr("layer", fx.layer) if str(fx.layer).strip() else "0"
        extra = shape_tags.replace("\\", "\\\\")
        inner.append('out.add(compose(%s, pos_x, pos_y, tags, "%s") + str(text), start, end, layer=int(%s), line=line)'
                     % (align, extra, layer))
        code_text = "\n".join(re.sub(r"\s+#[^\"']*$", "", l) for l in body + inner if not l.lstrip().startswith("#"))
        used = set(_identifiers(code_text))
        self.used = used
        pre, imports = self._preamble(used)
        return self._assemble(pre, imports, body, inner, looped)

    def _preamble(self, used: set) -> Tuple[List[str], List[str]]:
        unit, pre = self.unit, []
        math_names = sorted(n for n in used if n in _PY_MATH and n not in ("rad", "deg", "ln"))
        imports = ["ke3", "fmt", "units", "Fx", "cat", "compose", "tag_post", "untranslated"] + (["Unit"] if self.kind == "line" else [])
        for n in sorted(used & set(_KE3_GLOBALS)):
            pre.append("%s = ke3.%s" % (n, n))
        for ns in sorted(used & set(_KE3_NAMESPACES)):
            pre.append("%s = ke3.%s" % (ns, ns))
        if "lt" in used:
            pre.append("lt = ke3.LuaTable")
        if "l" in used:
            pre.append("l = line")
        if "ratio" in used:
            pre.append("ratio = ke3.ENV.ratio")
        if "frame_dur" in used:
            pre.append("frame_dur = ke3.ENV.frame_dur")
        for n in ("xres", "yres"):
            if n in used:
                pre.append("%s = ke3.ENV.%s" % (n, n))
        if "format" in used:
            pre.append("format = lambda fmt_, *args: fmt_ % args")
        if "rad" in used:
            pre.append("rad = lambda x: x * ke3.PI / 180")
        if "deg" in used:
            pre.append("deg = lambda x: x * 180 / ke3.PI")
        if "ln" in used:
            pre.append("ln = ke3.LN")
        for n in math_names:
            pre.append("%s = ke3.%s" % (n, n))
        if "retime" in used:
            pre.append('retime = untranslated("retime()", "retime(...) dentro de un campo (cambia el tiempo de la linea de efecto)")')
        missing = sorted(n for n in used
                         if n not in _PROVIDED | _BUILTIN | _PY_MATH | set(_KE3_GLOBALS) | set(_KE3_NAMESPACES)
                         | self.defined | set(_UNIT_TIME) | _GENERATED
                         and not re.fullmatch(r"\d+", n))
        if missing:
            imports.append("missing")
            pre = ['%s = missing("%s")' % (n, n) for n in missing] + pre
        return pre, imports

    def _assemble(self, pre: List[str], imports: List[str], body: List[str], inner: List[str], looped: bool) -> str:
        fx, unit = self.fx, self.unit
        used_text = "\n".join(body + inner)
        uses_time = [n for n in _UNIT_TIME if re.search(r"(?<![\w.])%s\(" % n, used_text)]
        shorts = {
            "time_li": "time_li = lambda d=None, m=None: ke3.time.li(%s, d, m)",
            "time_lo": "time_lo = lambda d=None, m=None: ke3.time.lo(%s, d, m)",
            "time_mid1": "time_mid1 = lambda d=None: ke3.time.mid1(%s, d)",
            "time_mid2": "time_mid2 = lambda d=None: ke3.time.mid2(%s, d)",
        }
        lines = [
            "# -*- coding: utf-8 -*-",
            '"""%s -- efecto de Kara Effector 3.6 (%s, plantilla %s). Generado desde Effector-3.6.lua; editalo libremente."""'
            % (self.name, fx.kind_name, fx.template),
            "from pyxis_fx import %s" % ", ".join(imports),
            "from math import sin, cos, tan, asin, acos, atan, atan2, ceil, floor, pi, sqrt  # noqa: F401",
            "",
            "NAME = %s" % _py_str(self.name),
            "STYLE = %s" % (_py_str(self.style) if self.style else "None"),
            "",
            "",
            "def run(line, out):",
        ] + ["    " + p for p in pre]
        if not self.supported:
            lines.append("    # TODO: plantilla %r de Effector sin equivalente exacto; se usa la unidad `%s`" % (fx.template, self.kind))
        ind = "    "
        if self.kind == "line":
            lines.append(ind + "unit = Unit(line, line, line.start_time, line.end_time, line.start_time, "
                         'line.end_time, 1, 1, kind="word")')
        else:
            lines.append(ind + 'for %s in units(line, "%s", noblank=%s):' % (self.kind, self.kind, bool(fx.noblank)))
            ind += "    "
        used = getattr(self, "used", set())
        if self.kind == "char" and "syl" in used:
            lines.append(ind + "syl = char.parent_syl")
        if self.kind == "char" and "sylchar" in used:
            lines.append(ind + "sylchar = char.sylchar")
        if self.kind in ("char", "syl") and "word" in used:
            lines.append(ind + "word = %s.parent_word" % self.kind)
        for n in uses_time:
            lines.append(ind + shorts[n] % unit)
        loop_at = next((i for i, b in enumerate(body) if b.startswith("fx.maxloop_fx")), None)
        for i, b in enumerate(body):
            lines.append(ind + b)
        if loop_at is not None:
            lines.append(ind + "for j in range(1, maxj + 1):")
            lines += [ind + "    " + b for b in inner]
        else:
            lines += [ind + b for b in inner]
        if self.notes:
            lines.insert(2, "# NOTA: campos sin traducir (marcados): %s" % ", ".join(sorted(set(self.notes))))
        return "\n".join(lines) + "\n"


def fx_to_python(fx: FxTemplate, style: Optional[str] = None, name: Optional[str] = None) -> str:
    """Codigo Python completo del efecto de Kara Effector 3.6 (usa `units`, `retime` y `ke3`)."""
    return _Gen(fx, style, name).build()


def support_report(fx: FxTemplate, code: Optional[str] = None) -> Dict[str, object]:
    """Que le falta a este efecto para ejecutarse: {"supported": bool, "missing": [funciones de ke3 sin portar],
    "notes": [campos sin traducir, nombres desconocidos...]}. `supported` = el codigo generado no usa nada sin portar."""
    from . import ke3
    code = code if code is not None else fx_to_python(fx, "Default", fx.name)
    body = code.split("def run(line, out):", 1)[1]
    no_comments = re.sub(r"\s+#[^\"']*$", "", body, flags=re.M)
    stripped = re.sub(r"\"(?:[^\"\\]|\\.)*\"|'(?:[^'\\]|\\.)*'", '""', no_comments)
    have = set(ke3.ported())
    namespaces = "|".join(ke3.NAMESPACES)
    calls = {m.group(1) + "." + m.group(2) for m in re.finditer(r"\b(%s)\.(\w+)\s*\(" % namespaces, stripped)}
    calls |= {n for n in ke3.GLOBALS if re.search(r"(?<![\w.])%s\(" % n, stripped)}
    missing = sorted(c for c in calls if c not in have)
    if re.search(r"tag\.clip\((?:[^()]|\([^()]*\))*?[\"'][^\"']*shape\.\w+", no_comments):
        missing.append("tag.clip(movimiento con shape.*)")          # el movimiento en texto se evalua con funciones de shape
    notes: List[str] = []
    if "untranslated(" in stripped:
        notes.append("campos sin traducir")
    notes += ["%s (no existe)" % m.group(1) for m in re.finditer(r'^\s*(\w+) = missing\("', body, re.M)]
    if "# TODO" in body:
        notes.append("sentencias con TODO")
    return {"supported": not missing and not notes, "missing": missing, "notes": notes}
