# -*- coding: utf-8 -*-
"""Pruebas de los servicios `ke_*` (port de newkara_library.lua) con los ejemplos del original."""
import random
import unittest

from pyxis_core.domain.services import ke_alpha, ke_color, ke_math, ke_time


class KeMathTests(unittest.TestCase):
    def test_distance_angle_polar(self):
        self.assertEqual(ke_math.distance((0, 0), (3, 4)), 5)
        self.assertAlmostEqual(ke_math.angle((4, 5)), 308.66, places=2)
        self.assertEqual(ke_math.polar(45, 10), (7.071, -7.071))
        self.assertEqual(ke_math.polar(90, 10, "x"), 0)

    def test_equations(self):
        roots = ke_math.cubic(1, -3, -9, -5)
        self.assertAlmostEqual(roots[0], -1, places=5)
        self.assertAlmostEqual(roots[-1], 5, places=5)
        eq = ke_math.equation([-5, -9, -3, 1], reals=True)
        self.assertAlmostEqual(eq[0], -1, places=3)
        self.assertAlmostEqual(eq[-1], 5, places=3)
        self.assertEqual(ke_math.gauss([[5, -3, -1], [2, 1, 4]]), [1, 2])
        self.assertEqual(ke_math.evaluate([5, -7], 2), -9)
        self.assertEqual(ke_math.quadratic(1, -3, 2), [1, 2])

    def test_interpolation(self):
        self.assertEqual(ke_math.ipol([0, 30, 20], 0.7), 26)
        self.assertEqual(ke_math.ipol([0, 10], 0.5), 5)
        self.assertEqual(ke_math.ipol([[10, 50], [20, 150]], 0.5), [15, 100])
        self.assertEqual(ke_math.ipol([0, 10], size=3), [0, 5, 10])

    def test_clamp_and_sequence(self):
        self.assertEqual(ke_math.clamp(3, 5, 10), 5)
        self.assertEqual(ke_math.clamp([3, 7, 12], 5, 10), [5, 7, 10])
        aba = [ke_math.sequence(i, 1, 3, mode="ABA") for i in range(1, 8)]
        self.assertEqual(aba, [1, 2, 3, 2, 1, 2, 3])
        self.assertEqual(ke_math.sequence(1, 1, 3)["N,n"], 1)
        c = ke_math.counter(1)
        self.assertEqual([c(), c(), c()], [1, 2, 3])

    def test_matrix(self):
        m = ke_math.Matrix([2, 3, 4, 1])
        self.assertEqual(m.det, -10)
        self.assertEqual(m * ke_math.Matrix.identity(2), m)
        self.assertEqual(m.inverse() * m, ke_math.Matrix.identity(2))
        self.assertEqual(ke_math.Matrix.identity(3).det, 1)

    def test_rand_bounds_and_circle(self):
        rng = random.Random(7)
        for _ in range(200):
            v = ke_math.rand(5, 10, rng=rng)
            self.assertTrue(5 <= v <= 10)
            self.assertTrue(1 <= ke_math.rand(6, rng=rng) <= 6)
        self.assertIn(ke_math.rand([4, 5, 6], rng=rng), (4, 5, 6))
        (cx, cy), r = ke_math.circle((0, 0), (10, 0), (0, 10))
        self.assertAlmostEqual(cx, 5)
        self.assertAlmostEqual(cy, 5)
        self.assertAlmostEqual(r, 50 ** 0.5)
        self.assertIsNone(ke_math.circle((0, 0), (1, 1), (2, 2)))
        self.assertEqual(ke_math.intersect("0 0 10 10", "0 10 10 0")[:2], (5, 5))
        self.assertIsNone(ke_math.intersect("0 0 1 1", "0 1 1 2"))


class KeColorAlphaTimeTests(unittest.TestCase):
    def test_color(self):
        self.assertEqual(ke_color.ass(255, 0, 128), "&H8000FF&")
        self.assertEqual(ke_color.ass("#FF0080"), "&H8000FF&")
        self.assertEqual(ke_color.ass("&H00112233"), "&H112233&")
        self.assertEqual(ke_color.to_rgb("&HB7F0AA&"), [170, 240, 183])
        self.assertEqual(ke_color.hsv_to_rgb(0, 1, 1), "&H0000FF&")
        h, s, v = ke_color.to_hsv("&H0000FF&")
        self.assertEqual((round(h), s, v), (0, 1, 1))
        self.assertEqual(ke_color.ipol(["&H000000&", "&HFFFFFF&"], 0.5), "&H808080&")
        self.assertRegex(ke_color.random(rng=random.Random(1)), r"^&H[0-9A-F]{6}&$")

    def test_alpha(self):
        self.assertEqual(ke_alpha.ass(0), "&H00&")
        self.assertEqual(ke_alpha.ass(255), "&HFF&")
        self.assertEqual(ke_alpha.ass("&H0F&"), "&H0F&")
        self.assertEqual(ke_alpha.ass([0, 255]), ["&H00&", "&HFF&"])
        self.assertEqual(ke_alpha.ass("FF", True), 255)
        self.assertEqual(ke_alpha.ipol(["&H00&", "&HFF&"], 0.5), "&H80&")

    def test_time(self):
        self.assertEqual(ke_time.hms_to_ms("0:00:34.952"), 34952)
        self.assertEqual(ke_time.hms_to_ms("0:00:34.95"), 34950)
        self.assertEqual(ke_time.ms_to_hms(540.945), "0:00:00.541")
        self.assertEqual(ke_time.ms_to_hms(5645), "0:00:05.645")
        self.assertEqual(ke_time.time_to_frame(2000, 1000 / 24), 48)
        self.assertEqual(ke_time.leadin(1), -200)
        self.assertEqual(ke_time.leadout(5, 5), 160)
        self.assertEqual(ke_time.ipol([0, 100], n=2), [[[0, 50], [50, 100]]])


if __name__ == "__main__":
    unittest.main()


class KeStringTests(unittest.TestCase):
    def test_count_array_parts(self):
        from pyxis_core.domain.services import ke_string as ks
        self.assertEqual(ks.count(["&HF58628&", "&HFF00FF&"], "color"), [1, 1])
        self.assertEqual(ks.count("a1 b22 c333", "number"), 3)
        self.assertEqual(ks.array("abc"), ["a", "b", "c"])
        self.assertEqual(ks.array("\\bord2\\blur1", r"\\[a-z]+(\d+)"), [("2",), ("1",)])
        self.assertEqual(ks.parts("por ejemplo", 2), ["po", "r ", "ej", "em", "pl", "o"])
        self.assertEqual(sorted(ks.disorder("texto")), sorted("texto"))

    def test_protect_change_delete(self):
        from pyxis_core.domain.services import ke_string as ks
        s, saved = ks.protect("foo(8)bar(0)demo6 foo(demo)", r"\w+\(\w*\)")
        self.assertEqual(s, "<x><x>demo6 <x>")
        self.assertEqual(saved, ["foo(8)", "bar(0)", "foo(demo)"])
        self.assertEqual(ks.unprotect(s, saved), "foo(8)bar(0)demo6 foo(demo)")
        t = r"\blur3\t(\blur1)"
        self.assertEqual(ks.change(t, r"(\\[a-z]+)(\d+)", lambda tag, v: tag + str(2 * int(v)), protect_=r"\\t\([^)]*\)"),
                         r"\blur6\t(\blur1)")
        self.assertEqual(ks.change(r"\1c&H0000FF&\t(\1c&HFF00AA&)\1c&H00FFFF&ru", r"\\1c&H[0-9A-F]+&",
                                   "", nochange=1, protect_=r"\\t\([^)]*\)"),
                         r"\1c&H0000FF&\t(\1c&HFF00AA&)ru")
        self.assertEqual(ks.delete("a1b2c3", r"\d", except_=[2]), "ab2c")
        self.assertEqual(ks.index_variable(r"\fr(-5i)\frx(10 - i)"), r"\fr(-5 * 0)\frx(10 - 1)")


class KeTagTextTests(unittest.TestCase):
    STYLE = {"color1": "&HFFFFFF&", "color3": "&H000000&", "alpha1": "&H00&", "outline": 2, "shadow": 1,
             "scale_x": 100, "scale_y": 100, "fontsize": 40, "angle": 0, "spacing": 0}

    def test_array(self):
        from pyxis_core.domain.services import ke_tag as kt
        tags = kt.array(r"\frz-32\blur-2\1a&HFF&\bordR(2,6)\org(80,90)\t(0,80,\1c&HFF00FF&\bord1)")
        self.assertEqual([t["tag"] for t in tags], ["\\frz", "\\blur", "\\1a", "\\bord", "\\org", "\\t1"])
        self.assertEqual(tags[0]["val"], "-32")
        self.assertEqual(tags[2]["val"], "&HFF&")
        self.assertEqual(tags[3]["val"], "R(2,6)")
        t = tags[-1]
        self.assertEqual(t["times"], [0, 80, 1])
        self.assertEqual(t["tags"], r"\1c&HFF00FF&\bord1")

    def test_default_inverse(self):
        from pyxis_core.domain.services import ke_tag as kt
        self.assertEqual(kt.default(r"\fscx250\t(0,300,\1a&HFF&)", self.STYLE), r"\fscx100\1a&H00&")
        self.assertEqual(kt.inverse(r"\fscx250\t(0,300,\1a&HAA&\frz45)", self.STYLE), r"\fscx100\1a&H55&\frz-45")
        self.assertEqual(kt.inverse(r"\1c&HFFFF00&", self.STYLE), r"\1c&H0000FF&")

    def test_dark_ipol_only_clip(self):
        from pyxis_core.domain.services import ke_tag as kt
        self.assertEqual(kt.expand_dark(r"\fscxy150\bs2"), r"\fscx150\fscy150\bord2\shad2")
        self.assertEqual(kt.ipol([r"\blur0\1a&H00&", r"\blur10\1a&HFF&"], 0.5), r"\blur5\1a&H80&")
        self.assertEqual(kt.only(True, "a", "b"), "a")
        self.assertEqual(kt.only(False, "a"), "")
        self.assertEqual(kt.clip(0, 0, 100, 50, j=2, loop=(2, 1)), r"\clip(50.0,0.0,100.0,50.0)")

    def test_text(self):
        from pyxis_core.domain.services import ke_text as kx
        self.assertEqual(kx.remove(r"{\an5}hola {\b1}mundo", "tags"), "hola mundo")
        self.assertEqual(kx.remove("  hola\t", "extra_space"), "hola")
        self.assertEqual(kx.remove(r"{\pos(1, 2) \bord 3}x", "space_in_tags"), r"{\pos(1,2)\bord3}x")
        self.assertEqual(kx.to_upper(r"{\an5}hola {\b1}mundo"), r"{\an5}HOLA {\b1}MUNDO")
        self.assertEqual(kx.to_lower(r"{\an5}HOLA"), r"{\an5}hola")
        self.assertEqual(kx.syl2hiragana("カ"), "か")
        self.assertEqual(kx.syl2hiragana("kya"), "きゃ")
        self.assertEqual(kx.syl2katakana("shi"), "シ")
        self.assertEqual(kx.kana2romaji("しゃ"), "sha")
        self.assertEqual(kx.kana2romaji("がっこう"), "gakkou")
        self.assertEqual(kx.syl2katakana("きゃ"), "キャ")
        self.assertEqual(kx.kana2romaji("ほうかい"), "houkai")
        self.assertEqual(kx.kana2romaji("キャ"), "kya")
        self.assertEqual(kx.byte2char(kx.char2byte("abc")), "abc")
        self.assertEqual((len(kx.ROMAJI), len(kx.HIRAGANA), len(kx.KATAKANA)), (118, 118, 118))
        self.assertEqual(kx.HIRAGANA[:5], ["あ", "い", "う", "え", "お"])
        self.assertEqual(kx.kana_for_romaji("ka"), "か")


class KeRetimeTests(unittest.TestCase):
    """retime/units sobre objetos simulados con el mismo contrato que pyxis-core."""

    @staticmethod
    def _line():
        from types import SimpleNamespace as NS
        mk = lambda **k: NS(**k)
        chars1 = [mk(start_time=0, end_time=100, is_blank=False, text_stripped="a", center=1),
                  mk(start_time=100, end_time=200, is_blank=False, text_stripped="b", center=2)]
        chars2 = [mk(start_time=0, end_time=150, is_blank=False, text_stripped="c", center=3),
                  mk(start_time=150, end_time=300, is_blank=True, text_stripped=" ", center=4)]
        syls = [mk(start_time=0, end_time=200, word=1, is_blank=False, chars=chars1),
                mk(start_time=200, end_time=500, word=2, is_blank=False, chars=chars2)]
        words = [mk(start_time=0, end_time=200, is_blank=False), mk(start_time=200, end_time=500, is_blank=False)]
        return mk(start_time=1000, end_time=3000, syls=syls, words=words)

    def test_units(self):
        from pyxis_core.domain.services import ke_units
        line = self._line()
        chars = list(ke_units.units(line, "char"))
        self.assertEqual([c.text_stripped for c in chars], ["a", "b", "c"])        # sin el espacio
        self.assertEqual((chars[2].abs_start, chars[2].abs_end), (1200, 1500))      # unico caracter visible: toda la silaba
        self.assertEqual((chars[2].syl_start, chars[2].syl_end, chars[2].si, chars[2].syln), (1200, 1500, 2, 2))
        self.assertEqual((chars[2].word_start, chars[2].word_end, chars[2].wi), (1200, 1500, 2))
        self.assertEqual(len(list(ke_units.units(line, "char", noblank=False))), 4)
        self.assertEqual([(u.abs_start, u.abs_end) for u in ke_units.units(line, "syl")], [(1000, 1200), (1200, 1500)])
        self.assertEqual([u.wi for u in ke_units.units(line, "word")], [1, 2])

    def test_char_times_split_evenly_and_sylchar(self):
        from types import SimpleNamespace as NS
        from pyxis_core.domain.services import ke_units
        mk = NS
        # silaba de 300 ms con 3 caracteres (+ un espacio) con tiempos de pyxis-core desiguales
        chars = [mk(start_time=0, end_time=50, is_blank=False, text_stripped="a", center=1),
                 mk(start_time=50, end_time=250, is_blank=False, text_stripped="b", center=2),
                 mk(start_time=250, end_time=290, is_blank=False, text_stripped="c", center=3),
                 mk(start_time=290, end_time=300, is_blank=True, text_stripped=" ", center=4)]
        syl = mk(start_time=100, end_time=400, word=1, is_blank=False, chars=chars)
        line = mk(start_time=1000, end_time=2000, syls=[syl], words=[mk(start_time=100, end_time=400, is_blank=False)])
        cs = list(ke_units.units(line, "char"))
        self.assertEqual([(c.abs_start, c.abs_end) for c in cs], [(1100, 1200), (1200, 1300), (1300, 1400)])   # 300/3 c/u
        self.assertEqual([(c.sylchar.i, c.sylchar.n) for c in cs], [(1, 3), (2, 3), (3, 3)])
        self.assertEqual([(c.sylchar.start_time, c.sylchar.mid_time, c.sylchar.end_time) for c in cs][1], (100, 150, 200))
        self.assertEqual((cs[0].start_time, cs[0].end_time), (100, 200))              # relativos al inicio de la linea
        self.assertEqual(cs[0].parent_syl.kind, "syl")

    def test_retime_modes(self):
        from pyxis_core.domain.services import ke_time, ke_units
        line = self._line()
        c = list(ke_units.units(line, "char"))[2]   # "c": char 1200-1500 (unico visible), syl 1200-1500, palabra 1200-1500, linea 1000-3000
        rt = lambda mode, a=0, b=0, **kw: ke_time.retime(c, mode, a, b, **kw)
        self.assertEqual(rt("line"), (1000, 3000))
        self.assertEqual(rt("preline", 10, 20), (1010, 1020))
        self.assertEqual(rt("postline", 10, 20), (3010, 3020))
        self.assertEqual(rt("start2syl", -400, 0), (600, 1200))
        self.assertEqual(rt("syl2end", 0, 100), (1500, 3100))
        self.assertEqual(rt("syl"), (1200, 1500))
        self.assertEqual(rt("word"), (1200, 1500))
        self.assertEqual(rt("char"), (1200, 1500))
        self.assertEqual(rt("prechar", -50, 50), (1150, 1250))
        self.assertEqual(rt("char2endsyl"), (1500, 1500))
        self.assertEqual(rt("startword2char"), (1200, 1200))
        self.assertEqual(rt("set", 100, 200), (100, 200))
        self.assertEqual(rt("abs", 100, 200), (100, 200))
        # tal como esta escrito en el original: postword/postchar terminan en el INICIO de la unidad
        self.assertEqual(rt("postword", 0, 0), (1500, 1200))
        self.assertEqual(rt("postchar", 0, 0), (1500, 1200))
        # porcentajes
        self.assertEqual(rt("linepct", 0, 50), (1000, 2000))
        self.assertEqual(rt("sylpct", 25, 75), (1275, 1425))
        self.assertEqual(rt("charpct", 0, 100), (1200, 1500))
        # tiempo del efecto (fx*)
        self.assertEqual(rt("fxtime", 5, 10, fx=(2000, 2500)), (2005, 2510))
        self.assertEqual(rt("fxpct", 0, 50, fx=(2000, 3000)), (2000, 2500))
        self.assertEqual(rt("sylmodule", 0, 0, j=2, maxj=3), (1300, 1400))
        self.assertEqual(rt("syl", "0:00:00.10", 0), (1300, 1500))          # HMS admitido
        self.assertEqual(ke_time.retime(c, "syl", 0, 0, origin=1000), (200, 500))   # relativo al inicio del efecto
        self.assertEqual(rt("modo_inexistente"), (1000, 3000))              # "default" del original: la linea
        for mode in ke_time.RETIME_MODES:
            if "furi" in mode:
                with self.assertRaises(ValueError):                         # sin furigana en pyxis-core
                    rt(mode)
            else:
                self.assertEqual(len(rt(mode)), 2)
        self.assertEqual(len(ke_time.RETIME_MODES), 41)
        # leadin escalonado con la formula del ejemplo (-400 + 400/syln*si)
        self.assertEqual(ke_time.retime(c, "start2syl", -400 + 400 / c.syln * c.si, 0), (1000, 1200))

    def test_time_li_lo_mid_by_unit(self):
        from types import SimpleNamespace as NS
        from pyxis_core.domain.services import ke_time
        line = NS(start_time=1000, end_time=3000)
        u = NS(line=line, i=3, n=9, si=2, syln=4, wi=1, wn=2, syl_start=1400, syl_end=1900, word_start=1000, word_end=1900)
        self.assertEqual(ke_time.time_li(u, 50), 50 * 2 - 200)
        self.assertEqual(ke_time.time_li(u), 40 * 2 - 200)                          # retardo por defecto 40
        self.assertEqual(ke_time.time_li(u, 50, "syl"), 400 + 50 * 1 - 200)
        self.assertEqual(ke_time.time_lo(u, 50), 50 * (3 - 9 - 1) + 200)
        self.assertEqual(ke_time.time_lo(u, 50, "syl"), 900 + 50 * (2 - 4 - 1) + 200)
        self.assertEqual(ke_time.time_mid1(u, 40), ke_time.mid1(3, 9, 40))
        self.assertEqual(ke_time.time_mid2(u), ke_time.mid2(3, 9, 30))

    def test_transform(self):
        from pyxis_core.domain.services import ke_tag
        self.assertEqual(ke_tag.transform(0, 200, "\\fscx120"), "\\t(0,200,\\fscx120)")
        self.assertEqual(ke_tag.transform(0, 200, "\\fscx120", 2), "\\t(0,200,2,\\fscx120)")
