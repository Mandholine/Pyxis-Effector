# -*- coding: utf-8 -*-
"""Libreria de efectos y utilidades de Kara Effector 3.6 legacy (Effector-3.6.lua / Effector-utils-lib-3.6.lua)."""
import json
import os
import random
import sys
import tempfile
import types
import unittest
from types import SimpleNamespace as NS

from pyxis_core.domain.entities import FX_KINDS, FxTemplate
from pyxis_core.domain.services import ke3, ke_fxcodegen, ke_lua, ke_shape as ksh, ke_tag, ke_time, ke_units
from pyxis_core.domain.services.ke3_index import UTILS_INDEX
from pyxis_core.infrastructure.repositories import FxLibraryRepository
from pyxis_core.infrastructure.repositories import lua_effector

LUAS = os.path.join(os.path.dirname(__file__), "..", "..", "luas-old")


def ke_shape_bounds(code):
    shp = ksh.Shape(code)
    return (round(shp.minx, 3), round(shp.miny, 3), round(shp.maxx, 3), round(shp.maxy, 3))


def _repo():
    return FxLibraryRepository(user_file=os.path.join(tempfile.mkdtemp(), "fx.json"))


class ParserTests(unittest.TestCase):
    SAMPLE = (
        '\t-- comentario\n'
        '\tFoo_Bar = effector.create_fx( "LIfx", "Foo_Bar", "Syl", true, false, "#FFFFFF", "#848484", "#454545", "0", "0", '
        '"0", "l.start_time + 50li - delay", "l.start_time + syl.start_time", "", "", "", "", "syl.center", "syl.middle", '
        '"", "", "5", "0", "fx.pos_x", "fx.pos_y", "", "2", "", "syl.text", "\\"\\\\\\\\fad(120,0)\\"", '
        '"jump = 25r;\\noffy = 4r", "Lua", false, false )\n'
        '\tNo_Es = otra.cosa( "x" )\n')

    def test_parse_args_and_escapes(self):
        args, end = lua_effector.parse_args('"a\\nb", 3, 1.5, true, nil, "q\\"q" ) resto', 0)
        self.assertEqual(args, ["a\nb", 3, 1.5, True, None, 'q"q'])
        with self.assertRaises(ValueError):
            lua_effector.parse_args("???", 0)

    def test_parse_effects(self):
        fx = lua_effector.parse_effects(self.SAMPLE)
        self.assertEqual(len(fx), 1)
        f = fx[0]
        self.assertEqual((f.kind, f.name, f.template, f.noblank, f.vertical), ("LIfx", "Foo_Bar", "Syl", True, False))
        self.assertEqual((f.start, f.end, f.align, f.layer, f.loop), ("l.start_time + 50li - delay",
                                                                    "l.start_time + syl.start_time", "5", "0", "2"))
        self.assertEqual(f.variables, "jump = 25r;\noffy = 4r")
        self.assertEqual(f.add_tags, '"\\\\fad(120,0)"')
        self.assertEqual(len(f.to_sequence()), 35)
        self.assertEqual(f.display_name, "Foo Bar")
        self.assertEqual(f.kind_name, "lead-in")


class RepositoryTests(unittest.TestCase):
    def test_builtin_library_matches_effector_36(self):
        repo = _repo()
        self.assertEqual(len(repo.all()), 3946)
        self.assertEqual(repo.counts(), {"LIfx": 1029, "HLfx": 415, "LOfx": 988, "SHfx": 427, "TLfx": 1060, "FTfx": 27})
        self.assertEqual(set(repo.counts()), set(FX_KINDS))
        # el mismo nombre puede existir como lead-in y lead-out
        a, b = repo.get("Animated_Clip_VI_tags_functions", "LIfx"), repo.get("Animated_Clip_VI_tags_functions", "LOfx")
        self.assertEqual((a.kind, b.kind), ("LIfx", "LOfx"))
        self.assertEqual(a.start, "l.start_time + 50li - delay")
        self.assertEqual(b.start, "l.start_time + syl.end_time")
        self.assertEqual(repo.get("Animated Clip VI tags functions", "LIfx"), a)      # nombre legible
        self.assertEqual(len(repo.search("oscill", "LIfx")), len([f for f in repo.by_kind("LIfx") if "oscill" in f.name.lower()]))
        self.assertEqual(len(repo.search("clip", "LIfx", limit=5)), 5)
        self.assertIsNone(repo.get("no_existe"))

    def test_included_list_equals_the_lua_file(self):
        lua = os.path.join(LUAS, "Effector-3.6.lua")
        if not os.path.exists(lua):
            self.skipTest("Effector-3.6.lua no esta junto al repo")
        with open(lua, encoding="utf-8-sig", errors="replace") as fh:
            parsed = lua_effector.parse_effects(fh.read())
        seen, unique = set(), []
        for f in parsed:
            if (f.kind, f.name) not in seen:
                seen.add((f.kind, f.name))
                unique.append(f)
        self.assertEqual(unique, _repo().all())

    def test_user_effects(self):
        repo = _repo()
        fx = FxTemplate.from_sequence(["SHfx", "mi_fx", "Char"])
        repo.add(fx)
        self.assertEqual(repo.get("mi fx"), fx)
        self.assertEqual(len(repo.all()), 3947)
        self.assertFalse(repo.remove("Animated_Clip_VI_tags_functions"))              # los incluidos no se borran
        self.assertTrue(repo.remove("mi_fx"))
        self.assertEqual(len(repo.all()), 3946)
        with self.assertRaises(ValueError):
            repo.add(FxTemplate.from_sequence(["XXfx", "x"]))
        lua = os.path.join(tempfile.mkdtemp(), "l.lua")
        with open(lua, "w", encoding="utf-8") as fh:
            fh.write(ParserTests.SAMPLE)
        self.assertEqual([f.name for f in repo.import_lua(lua)], ["Foo_Bar"])
        self.assertEqual(repo.get("Foo_Bar").loop, "2")


class RetimeCodegenTests(unittest.TestCase):
    def test_retime_mode_from_start_end_fields(self):
        rm = ke_fxcodegen.retime_mode
        self.assertEqual(rm("l.start_time", "l.end_time"), ("line", "0", "0"))
        self.assertEqual(rm("l.start_time + 50li - delay", "l.start_time + syl.start_time"), ("start2syl", "+ 50li - delay", "0"))
        self.assertEqual(rm("l.start_time + syl.start_time", "l.start_time + syl.end_time"), ("syl", "0", "0"))
        self.assertEqual(rm("l.start_time + syl.end_time", "l.end_time + 200"), ("syl2end", "0", "+ 200"))
        self.assertEqual(rm("l.start_time + char.start_time", "l.start_time + char.end_time")[0], "char")
        self.assertEqual(rm("l.start_time + word.start_time", "l.start_time + word.end_time")[0], "word")
        self.assertIsNone(rm("fx.algo", "l.end_time"))

    def test_generated_code_uses_python_retime(self):
        repo = _repo()
        code = ke_fxcodegen.fx_to_python(repo.get("Animated_Clip_VI_tags_functions", "LIfx"), "Romaji", "sdsda")
        self.assertIn('start, end = ke3.time.retime(syl, "start2syl", time_li(50) - delay, 0)', code)
        self.assertIn("time_li = lambda d=None, m=None: ke3.time.li(syl, d, m)", code)
        self.assertIn("jump = (25 * ratio)", code)                     # 25r -> 25 * ratio
        self.assertIn("clips = lt({1: ", code)                         # tabla de Lua -> LuaTable (indices desde 1)
        self.assertIn('STYLE = "Romaji"', code)
        out = ke_fxcodegen.fx_to_python(repo.get("Animated_Clip_VI_tags_functions", "LOfx"), None)
        self.assertIn('ke3.time.retime(syl, "syl2end"', out)
        self.assertIn("STYLE = None", out)

    def test_all_library_entries_generate_compilable_python(self):
        for fx in _repo().all():
            compile(ke_fxcodegen.fx_to_python(fx, "Default"), fx.name, "exec")

    def test_untranslatable_field_fails_loudly_not_silently(self):
        fx = FxTemplate.from_sequence(["LIfx", "x", "Syl"] + [True, False, "#FFF", "#FFF", "#FFF", "0", "0", "0"] +
                                      ["l.start_time", "l.end_time"] + [""] * 4 + ["syl.center", "syl.middle", "", "", "5", "0",
                                      "fx.pos_x", "fx.pos_y", "", "1", "", "syl.text @@ roto", "", ""])
        code = ke_fxcodegen.fx_to_python(fx, "Default")
        compile(code, "gen", "exec")
        self.assertIn('untranslated("return"', code)
        self.assertIn("# NOTA: campos sin traducir", code)
        with self.assertRaises(NotImplementedError):
            ke3.untranslated("return", "syl.text @@ roto")

    def test_generated_effect_runs_with_fake_line(self):
        syl = NS(start_time=0, end_time=430, word=1, is_blank=False, center=10, middle=20, left=0, right=20, top=0, bottom=40, width=20, height=40,
                 text_stripped="Ma", text="{\\k43}Ma", chars=[], i=1, n=1)
        line = NS(start_time=5000, end_time=10000, syls=[syl], words=[NS(start_time=0, end_time=430, is_blank=False)])
        added = []
        out = NS(add=lambda text, s, e, layer=0, line=None: added.append((text, s, e, layer)))
        fake = types.ModuleType("pyxis_fx")
        fake.ke3, fake.units, fake.Unit, fake.Fx = ke3, ke_units.units, ke_units.Unit, ke_units.Fx
        fake.cat, fake.tag_post, fake.untranslated, fake.compose = ke3.cat, ke3.tag_post, ke3.untranslated, ke3.compose
        fake.missing = lambda name: None
        fake.fmt = lambda v: str(int(v)) if float(v).is_integer() else str(v)
        sys.modules["pyxis_fx"] = fake
        try:
            env = {}
            exec(compile(ke_fxcodegen.fx_to_python(_repo().by_kind("HLfx")[0], None), "gen", "exec"), env)
        finally:
            sys.modules.pop("pyxis_fx", None)
        env["run"](line, out)
        self.assertTrue(added)                                  # el primer HLfx de la libreria genera lineas


class LuaTranslatorTests(unittest.TestCase):
    def test_tables_units_statements(self):
        self.assertEqual(ke_lua.lua_tables('{ [ 1 ] = "a, b", [ "times" ] = { 0, d / 2 }, x = 3 }'),
                         'lt({1: "a, b", "times": lt({1: 0, 2: d / 2}), "x": 3})')
        self.assertEqual(ke_lua.expand_units("l.start_time + 50li - delay + 10f + 25r*D + 50mid2"),
                         "l.start_time + time_li(50) - delay + (10 * frame_dur) + (25 * ratio)*D + time_mid2(50)")
        self.assertEqual(ke_lua.expand_units('"10r y 50li"'), '"10r y 50li"')                  # dentro de cadenas no
        self.assertEqual(ke_lua.lua_expr("a ~= nil and #t", shift_indices=False), "a != None and len(t)")
        self.assertEqual(ke_lua.split_statements('a = 1;\nb = {\n\t[1] = "x;y",\n};\nc = true'),
                         ["a = 1", 'b = {\n\t[1] = "x;y",\n}', "c = true"])


class Ke3Tests(unittest.TestCase):
    def test_random_family(self):
        random.seed(3)
        for _ in range(100):
            self.assertTrue(5 <= ke3.R(5, 10) <= 10)
            self.assertTrue(1 <= ke3.R(6) <= 6)
            self.assertTrue(-10 <= ke3.Rs(10) <= 10 and ke3.Rs(10) != 0)
            self.assertTrue(5 <= ke3.Rd(5, 10) <= 10)                            # R(50, 100) / 10: 1 decimal
            self.assertTrue(5 <= ke3.Rc(5, 10) <= 10)                            # R(500, 1000) / 100: 2 decimales
        ke3.ENV.ratio = 2.0
        try:
            for _ in range(50):
                self.assertTrue(10 <= ke3.Rr(5, 10) <= 20)                       # R(5*ratio, 10*ratio)
                self.assertTrue(abs(ke3.Rsr(10)) <= 20)
                self.assertTrue(20 <= abs(ke3.Rdrs(10, 20)) <= 40)                # R(100, 200) * 0.1 * ratio(2)
            self.assertIs(ke3.Rrs, ke3.Rsr)
        finally:
            ke3.ENV.ratio = 1.0
        self.assertIn(ke3.Re([4, 5, 6]), (4, 5, 6))
        self.assertIn(ke3.Re({"a": 7}), (7,))

    def test_unported_functions_say_where_they_are(self):
        with self.assertRaises(NotImplementedError) as ctx:
            ke3.tag.oscill                                   # sigue sin portar
        self.assertIn("tag.oscill", str(ctx.exception))
        self.assertIn("linea %d" % UTILS_INDEX["tag.oscill"], str(ctx.exception))
        with self.assertRaises(AttributeError):
            ke3.tag.no_existe_en_el_lua
        self.assertEqual(ke3.shape.rectangle, ksh.RECTANGLE)
        self.assertTrue(ke3.shape.cristal17.startswith("m 56 50"))
        self.assertEqual(ke3.tag.only(True, "a", "b"), "a")

    def test_coverage_report(self):
        cov = ke3.coverage(["math.R", "tag.only", "tag.clip", "tag.oscill", "shape.size", "inventada.x"])
        self.assertIn("tag.only", cov["ported"])
        self.assertIn("tag.clip", cov["ported"])
        self.assertIn("tag.oscill", cov["missing"])
        self.assertIn("inventada.x", cov["unknown"])
        self.assertIn("R", ke3.ported())
        self.assertGreater(len(UTILS_INDEX), 300)

    def _clip_ctx(self, loops=(2, 2), dur=1000):
        line = NS(start_time=0, end_time=1000, outline=2, shadow=0, height=40)
        unit = NS(line=line, center=125, middle=100, left=100, right=150, top=80, bottom=120, width=50, height=40,
                  text_stripped="ma")
        fx = ke_units.Fx(unit)
        fx.loop_v, fx.loop_h = loops
        fx.dur = dur
        return fx, line, unit

    def test_tag_clip_grid_modes(self):
        fx, line, unit = self._clip_ctx((2, 2))
        cells = []
        for j in range(1, 5):                                   # modo 79 (por defecto): izquierda->derecha, arriba->abajo
            ke3.bind(fx, line, unit, j)
            cells.append(ke3.tag.clip())
        self.assertEqual(cells, ["\\clip(98,78,125,100)", "\\clip(125,78,152,100)",
                                 "\\clip(98,100,125,122)", "\\clip(125,100,152,122)"])    # cubre 98..152 x 78..122
        ke3.bind(fx, line, unit, 1)
        self.assertEqual(ke3.tag.clip(None, None, None, None, 31), "\\clip(125,100,152,122)")  # modo 31: desde abajo-derecha
        self.assertEqual(ke3.tag.clip(None, None, None, None, 71), "\\clip(98,78,125,100)")
        self.assertEqual(ke3.tag.clip(None, None, None, None, 999), cells[0])                  # modo invalido -> 79
        # rectangulo explicito (el de tu efecto): tag.clip(fx.pos_l - l.height, fx.pos_t, syl.width + 2*l.height, syl.height)
        self.assertEqual(ke3.tag.clip(fx.pos_l - line.height, fx.pos_t, unit.width + 2 * line.height, unit.height),
                         "\\clip(58,78,125,100)")

    def test_tag_clip_with_table_movement(self):
        fx, line, unit = self._clip_ctx((1, 1), dur=600)
        ke3.bind(fx, line, unit, 1)
        # dos posiciones: clip inicial + un \t a lo largo de toda la duracion del efecto
        self.assertEqual(ke3.tag.clip(None, None, None, None, None, {1: 0, 2: 0, 3: 10, 4: 5}),
                         "\\clip(98,78,152,122)\\t(0,600,\\clip(108,83,162,127))")
        # con tiempos explicitos al final (indice impar)
        self.assertEqual(ke3.tag.clip(None, None, None, None, None, {1: 0, 2: 0, 3: 10, 4: 5, 5: {1: 100, 2: 300}}),
                         "\\clip(98,78,152,122)\\t(100,300,\\clip(108,83,162,127))")
        with self.assertRaises(NotImplementedError):
            ke3.tag.clip(None, None, None, None, None, "shape.rmove( 0.4 * line.height )")
        ke3.CTX.fx = None
        with self.assertRaises(RuntimeError):
            ke3.tag.clip()

    def test_loop_is_the_product_of_the_loop_table(self):
        fx = FxTemplate.from_sequence(["LIfx", "x", "Syl", True, False, "#FFF", "#FFF", "#FFF", "0", "0", "0", "l.start_time",
                                       "l.end_time", "", "", "", "", "syl.center", "syl.middle", "", "", "5", "0", "fx.pos_x",
                                       "fx.pos_y", "", "2, 3", "", "syl.text", "tag.clip()"])
        code = ke_fxcodegen.fx_to_python(fx, "Default")
        self.assertIn("fx.loop_v, fx.loop_h, fx.loop_3 = ceil(2), ceil(3), ceil(1)", code)
        self.assertIn("fx.maxloop_fx = maxj = fx.loop_v * fx.loop_h * fx.loop_3", code)
        self.assertIn("ke3.bind(fx, line, syl, j)", code)
        self.assertIn("fx.start_time, fx.end_time, fx.dur = start, end, end - start", code)

    def test_shape_lmove(self):
        fx, line, unit = self._clip_ctx((1, 1), dur=500)
        line.descent = 8
        ke3.bind(fx, line, unit, 1)
        coords = {1: 125, 2: 100, 3: 125, 4: 80, 5: 125, 6: 100}
        # con tiempos explicitos: el texto sube 20 px a los 80 ms y vuelve a los 500 ms
        self.assertEqual(ke3.shape.lmove(coords, {1: 0, 2: 80, 3: 80, 4: 500}),
                         "\\an7\\q2\\pos(0,0)\\fscx100\\fscy112\\t(0,80,1,\\fscx100\\fscy92)\\t(80,500,1,\\fscx100\\fscy112)"
                         "\\p1}m 0 0 m 100 100 {\\p0\\r")
        # sin tiempos: se reparten segun la longitud de cada tramo; una x negativa desplaza el \pos
        out = ke3.shape.lmove({1: 0, 2: 100, 3: 100, 4: 100, 5: 100, 6: 300})
        self.assertIn("\\pos(-25,0)\\fscx0\\fscy112", out)
        self.assertIn("\\t(0,166.67,1,", out)
        self.assertIn("\\t(166.67,500,1,", out)
        # 0 despues de la primera posicion = fx.dur; negativo = desde el final
        self.assertIn("\\t(0,500,1,", ke3.shape.lmove({1: 125, 2: 100, 3: 125, 4: 80}, {1: 0, 2: 0}))
        self.assertIn("\\t(100,400,1,", ke3.shape.lmove({1: 125, 2: 100, 3: 125, 4: 80}, {1: 100, 2: -100}))
        self.assertEqual(ke3.new_pos(0, 0), "\\pos(0,0)")

    def test_lua_table_and_compose(self):
        t = ke3.LuaTable({1: "a", "times": 5})
        self.assertEqual((t[1], t.times, t.no_existe, len(t)), ("a", 5, None, 2))
        t.extra = 7
        self.assertEqual(t["extra"], 7)
        # compone el bloque de tags: \an y \pos por defecto salvo que los tags traigan los suyos
        self.assertEqual(ke3.compose(5, 193, 127.5, "\\fad(100,0)"), "{\\an5\\pos(193,127.5)\\fad(100,0)}")
        lm = "\\an7\\q2\\pos(0,0)\\fscx100\\fscy112\\p1}m 0 0 m 100 100 {\\p0\\r"
        self.assertEqual(ke3.compose(5, 193, 127.5, lm), "{" + lm + "}")                     # no duplica \an ni \pos
        self.assertEqual(ke3.compose(5, 1, 2, "\\move(0,0,5,5)"), "{\\an5\\move(0,0,5,5)}")
        self.assertEqual(ke3.compose(7, 1, 2, "", "\\p1"), "{\\an7\\pos(1,2)\\p1}")

    def test_shape_utils(self):
        sh, lt, rect = ke3.shape, ke3.LuaTable, ksh.RECTANGLE
        self.assertEqual(sh.size(rect, 120, 45), "m 0 0 l 0 45 l 120 45 l 120 0 l 0 0 ")
        self.assertEqual(sh.size(rect, 120, 0), "m 0 0 l 0 120 l 120 120 l 120 0 l 0 0 ")      # 0 = proporcional
        self.assertEqual(sh.size(rect, "2x", lt({1: 20})), "m 0 0 l 0 120 l 200 120 l 200 0 l 0 0 ")   # "2x", {delta}
        self.assertEqual(sh.displace(rect, 10, 5), "m 10 5 l 10 105 l 110 105 l 110 5 l 10 5 ")
        self.assertEqual(sh.displace(rect, "incenter"), "m -50 -50 l -50 50 l 50 50 l 50 -50 l -50 -50 ")
        self.assertEqual(sh.displace("m 10 10 l 20 20 ", "origin"), "m 0 0 l 10 10 ")
        self.assertEqual(sh.displace(rect, 100, 100, "first"), "m 100 100 l 100 200 l 200 200 l 200 100 l 100 100 ")
        self.assertEqual(sh.reflect("m 0 0 l 0 50 l 30 50 l 30 30 ", "y"), "m 0 0 l 0 50 l -30 50 l -30 30 ")   # rel. por defecto 0
        self.assertEqual(sh.reflect("m 0 0 l 0 50 ", "x", 100), "m 0 100 l 0 50 ")
        self.assertEqual(sh.reverse("m 0 0 l 0 20 l 20 20 l 20 0 "), "m 20 0 l 20 20 l 0 20 l 0 0 ")
        self.assertEqual((sh.width(rect), sh.height(rect)), (100, 100))
        parts = sh.divide("m 50 53 l 23 66 l 20 96 l 46 84 m 50 53 l 54 84 l 81 97 l 78 66 ")
        self.assertEqual(dict(parts), {1: "m 50 53 l 23 66 l 20 96 l 46 84 ", 2: "m 50 53 l 54 84 l 81 97 l 78 66 "})
        self.assertTrue(sh.divide("m 0 0 l 5 5 ", "default")[1].startswith("m 5 5 m 0 0 m 0 0"))
        many = sh.size(lt({1: rect, 2: sh.circle}), 50, 50)                                     # tablas de shapes
        self.assertEqual(sorted(many.keys()), [1, 2])
        self.assertEqual(ke_shape_bounds(many[1]), (0, 0, 50, 50))
        rot = sh.rotate(rect, 90, "center")
        self.assertEqual(ke_shape_bounds(rot), (0, 0, 100, 100))
        self.assertEqual(sh.rotate("m 10 0 l 0 0 ", 90), "m 0 -10 l 0 0 ")

    def test_support_report(self):
        repo = _repo()
        ok = ke_fxcodegen.support_report(repo.get("demo_hilight") or repo.by_kind("HLfx")[0])
        self.assertIn("supported", ok)
        needs = ke_fxcodegen.support_report(repo.get("Animated_Clip_VII_tags_functions_oscill", "LIfx"))
        self.assertFalse(needs["supported"])
        self.assertIn("tag.oscill", needs["missing"])
        # los de traduccion (plantillas sobre texto sin karaoke) estan marcados como no soportados
        self.assertFalse(ke_fxcodegen.support_report(repo.by_kind("TLfx")[0])["supported"])
        total = sum(1 for f in repo.all() if ke_fxcodegen.support_report(f)["supported"])
        self.assertGreater(total, 500)

    def test_animated_clip_shorthand(self):
        env = {"jump": 25, "fx": NS(dur=170)}
        src = "\\clip(-10,-10,10,4)( { 0, 80, 0, -jump }, { 80, fx.dur, 0, 0 } )"
        self.assertEqual(ke_tag.clip_moves(src, env),
                         "\\clip(-10,-10,10,4)\\t(0,80,\\clip(-10,-35,10,-21))\\t(80,170,\\clip(-10,-10,10,4))")
        # la linea completa del reporte: solo cambia la parte del clip
        line = "\\an7\\q2\\pos(0,0)\\fscx215\\p1}m 0 0 m 100 100 {\\p0\\r" + src
        self.assertTrue(ke_tag.clip_moves(line, env).startswith("\\an7\\q2\\pos(0,0)\\fscx215\\p1}m 0 0 m 100 100 {\\p0\\r\\clip(-10,-10,10,4)\\t(0,80,"))
        self.assertEqual(ke_tag.clip_moves("\\iclip(0,0,10,10)( { 0, 100, 5, 5, 0.8 } )\\blur2", {}),
                         "\\iclip(0,0,10,10)\\t(0,100,0.8,\\iclip(5,5,15,15))\\blur2")   # con aceleracion
        self.assertEqual(ke_tag.clip_moves("\\clip(0,0,10,10)\\fad(1,2)", {}), "\\clip(0,0,10,10)\\fad(1,2)")
        self.assertEqual(ke_tag.clip_moves("\\clip(m 0 0 l 5 5)( {0,1,2,3} )", {}), "\\clip(m 0 0 l 5 5)( {0,1,2,3} )")  # shapes: no
        bad = "\\clip(0,0,10,10)( { 0, nada, 5, 5 } )"
        self.assertEqual(ke_tag.clip_moves(bad, {}), bad)                                       # no evaluable: queda igual
        line_obj = NS(start_time=0, end_time=1000)
        unit = NS(line=line_obj, word_start=0, word_end=100, syl_start=0, syl_end=100, char_start=None, char_end=None)
        self.assertEqual(ke3.tag_post(src, unit, 0, env), "\\clip(-10,-10,10,4)\\t(0,80,\\clip(-10,-35,10,-21))\\t(80,170,\\clip(-10,-10,10,4))")

    def test_split_tags(self):
        self.assertEqual(ke_tag.split_tags("\\an7\\pos(1,2)\\fad(1,2)"), ["\\an7", "\\pos(1,2)", "\\fad(1,2)"])
        self.assertEqual(ke_tag.split_tags("\\p0\\r\\t(0,d / 2,\\3cR( nil, 86 ))( 0, d / 2 )\\fad(120,0)"),
                         ["\\p0", "\\r", "\\t(0,d / 2,\\3cR( nil, 86 ))( 0, d / 2 )", "\\fad(120,0)"])
        self.assertEqual(ke_tag.split_tags("\\clip(a,b)( { 0, 1 }, { 2, 3 } )\\blur2"),
                         ["\\clip(a,b)( { 0, 1 }, { 2, 3 } )", "\\blur2"])
        self.assertEqual("".join(ke_tag.split_tags("x\\a\\b(\\c)")), "x\\a\\b(\\c)")

    def test_cat_and_tag_post(self):
        self.assertEqual(ke3.cat("a", None, 2, 1.5, ""), "a21.5")
        line = NS(start_time=1000, end_time=3000)
        u = NS(line=line, word_start=1000, word_end=1430, syl_start=1000, syl_end=1430, char_start=None, char_end=None)
        self.assertEqual(ke3.tag_post("\\fscxy150\\t(syl,0,0,\\fscx120)", u, 1000), "\\fscx150\\fscy150\\t(0,430,\\fscx120)")


class Effector4PortTests(unittest.TestCase):
    """Piezas de effector-auto4.lua / utils-lib (mid1, mid2, formas predefinidas, movevc)."""

    def test_mid1_mid2(self):
        self.assertEqual(ke_time.mid2(1, 9, 40), -220)
        self.assertEqual(ke_time.mid2(9, 9, 40), -240)
        self.assertEqual(ke_time.mid2(5, 9, 40), -400)
        self.assertEqual(ke_time.mid1(3, 9, 40), ke_time.middle(3, 9, 40))
        self.assertEqual(ke_time.loop(2, 9, 40, "mid2"), ke_time.mid2(2, 9, 40))

    def test_predefined_shapes(self):
        self.assertTrue(ksh.cristal17.startswith("m 56 50 l 64 100 l 38 78 l 56 50"))
        for name in ("flower20t", "geometric10", "diagonal13l", "pentagon", "hexagon", "circangle"):
            self.assertTrue(getattr(ksh, name).startswith("m "), name)
        self.assertEqual(ksh.circle, ksh.CIRCLE)

    def test_tag_movevc(self):
        tag = ke_tag.movevc(ksh.RECTANGLE, 200, 150)                       # sin movimiento: clip colocado, sin \movevc
        self.assertEqual(tag, "\\clip(m 150 100 l 150 200 l 250 200 l 250 100 l 150 100 )")
        moving = ke_tag.movevc(ksh.RECTANGLE, 200, 150, 30, 0, 0, 500)
        self.assertIn("\\movevc(150,100,180,100,0,500)", moving)
        self.assertTrue(ke_tag.movevci(ksh.RECTANGLE, 200, 150).startswith("\\iclip("))


if __name__ == "__main__":
    unittest.main()
