import os
import sys
import unittest
from types import SimpleNamespace

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../src")))

from node_engine import GraphEngine, _apply_set_vars_to_context_helper
from node_validator import GraphValidator
from string_evaluator import (
    eval_python_expr,
    eval_pyxis_expr,
    eval_string_template,
    protect_ass_backslashes_in_quotes,
    split_statements_outside_quotes,
)


class TestTernaryAssStandardization(unittest.TestCase):
    """Unit tests covering canonical ASS backslash preservation and ternary parity across engine, evaluator, and linter."""

    def setUp(self):
        self.styles = {
            "Default": {
                "fontname": "Arial",
                "fontsize": 40.0,
                "bold": False,
                "italic": False,
                "underline": False,
                "strikeout": False,
                "scale_x": 100.0,
                "scale_y": 100.0,
                "spacing": 0.0,
                "angle": 0.0,
                "borderstyle": 1,
                "outline": 2.0,
                "shadow": 0.0,
                "align": 2,
                "margin_l": 30,
                "margin_r": 30,
                "margin_v": 30,
            }
        }

    def _make_context(self, line_idx=2, layer=0, syl_start=150, syl_end=300):
        return {
            "l": SimpleNamespace(i=line_idx, layer=layer),
            "line": SimpleNamespace(i=line_idx, layer=layer, start_time=1000, end_time=2500),
            "syl": SimpleNamespace(syl_start=syl_start, syl_end=syl_end, start_time=syl_start, end_time=syl_end, dur=syl_end - syl_start),
            "fx": SimpleNamespace(dur=1500),
            "_custom_vars": {},
        }

    def test_protect_ass_backslashes_is_idempotent_and_safe(self):
        """Ensures ASS escapes inside quotes are protected once while preserving '\\n' separators, escaped quotes, and raw strings."""
        single_esc = r'("\t(2924,3466,\fry360)\4a255\bord2\xbord3\u0\r\N" if l.i == 2 else "")'
        double_esc = r'("\\t(2924,3466,\\fry360)\\4a255\\bord2\\xbord3\\u0\\r\\N" if l.i == 2 else "")'
        raw_pref = r'(r"\t(2924,3466,\fry360)\4a255" if l.i == 2 else "")'

        p_once = protect_ass_backslashes_in_quotes(single_esc)
        p_twice = protect_ass_backslashes_in_quotes(p_once)
        self.assertEqual(p_once, double_esc)
        self.assertEqual(p_twice, p_once)
        self.assertEqual(protect_ass_backslashes_in_quotes(double_esc), double_esc)
        self.assertEqual(protect_ass_backslashes_in_quotes(raw_pref), raw_pref)

        # Standard Python newline separator without ASS tag context remains an actual newline escape
        split_expr = r'"line1\nline2".split("\n")'
        self.assertEqual(eval_python_expr(split_expr), ["line1", "line2"])

        # Escaped interior quotes remain intact
        self.assertEqual(eval_python_expr(r'"say \"hi\""'), 'say "hi"')

    def test_define_vars_quoted_and_unquoted_ternary_parity(self):
        """Verifies quoted, unquoted, doubled, raw, f-string, concatenated, and Lua ternaries produce identical results."""
        ctx_i2 = self._make_context(line_idx=2, layer=0)
        ctx_i3 = self._make_context(line_idx=3, layer=1)
        ctx_i1 = self._make_context(line_idx=1, layer=0)

        variants = [
            r'Anim = (\t(2924,3466,\fry360) if l.i == 2 else \t(1161,1703,\fry360) if l.i == 3 else "")',
            r'Anim = ("\t(2924,3466,\fry360)" if l.i == 2 else "\t(1161,1703,\fry360)" if l.i == 3 else "")',
            r'Anim = ("\\t(2924,3466,\\fry360)" if l.i == 2 else "\\t(1161,1703,\\fry360)" if l.i == 3 else "")',
            r'Anim = (r"\t(2924,3466,\fry360)" if l.i == 2 else r"\t(1161,1703,\fry360)" if l.i == 3 else "")',
            r'Anim = \t(2924,3466,\fry360) if l.i == 2 else \t(1161,1703,\fry360) if l.i == 3 else ""',
            r'Anim = l.i == 2 and \t(2924,3466,\fry360) or l.i == 3 and \t(1161,1703,\fry360) or ""',
            r'Anim = l.i == 2 and "\t(2924,3466,\fry360)" or l.i == 3 and "\t(1161,1703,\fry360)" or ""',
        ]

        for expr in variants:
            c2 = dict(ctx_i2)
            _apply_set_vars_to_context_helper(expr, c2)
            self.assertEqual(c2["Anim"], r"\t(2924,3466,\fry360)", f"Failed for i=2 on: {expr}")
            self.assertNotIn("\t", c2["Anim"])
            self.assertNotIn("\x0c", c2["Anim"])

            c3 = dict(ctx_i3)
            _apply_set_vars_to_context_helper(expr, c3)
            self.assertEqual(c3["Anim"], r"\t(1161,1703,\fry360)", f"Failed for i=3 on: {expr}")

            c1 = dict(ctx_i1)
            _apply_set_vars_to_context_helper(expr, c1)
            self.assertEqual(c1["Anim"], "", f"Failed for i=1 on: {expr}")

        # Test concatenation and f-strings with ASS tags
        c_extra = dict(ctx_i2)
        _apply_set_vars_to_context_helper(
            't1 = 2924\n'
            r'AnimCat = ("\t(" + str(t1) + ",3466,\fry360)" if l.i == 2 else "")' + '\n'
            r'AnimF = (f"\t({t1},3466,\fry360)" if l.i == 2 else "")',
            c_extra,
        )
        self.assertEqual(c_extra["AnimCat"], r"\t(2924,3466,\fry360)")
        self.assertEqual(c_extra["AnimF"], r"\t(2924,3466,\fry360)")

    def test_multiline_defvars_and_isolated_error_recovery(self):
        """Verifies multi-line parenthesized assignments succeed and unclosed delimiter typos do not swallow subsequent variables."""
        multiline_ok = (
            "Anim = (\n"
            '    "\\t(2924,3466,\\fry360)" if l.i == 2\n'
            "    else \"\"\n"
            ")\n"
            "x = 42"
        )
        stmts = split_statements_outside_quotes(multiline_ok)
        self.assertEqual(len(stmts), 2)
        c = self._make_context(line_idx=2)
        _apply_set_vars_to_context_helper(multiline_ok, c)
        self.assertEqual(c["Anim"], r"\t(2924,3466,\fry360)")
        self.assertEqual(c["x"], 42)

        # Unclosed paren on line 1 must still emit second assignment separately
        broken_plus_ok = "bad = (1 + 2\ngood = 99"
        stmts_broken = split_statements_outside_quotes(broken_plus_ok)
        self.assertEqual(stmts_broken, ["bad = (1 + 2", "good = 99"])

    def test_string_template_evaluation_after_newline_and_nested_tags(self):
        """Verifies '(Var)' on a new line after a bare tag is evaluated rather than misparsed as tag arguments."""
        ctx = self._make_context(line_idx=2, layer=0, syl_start=150, syl_end=300)
        _apply_set_vars_to_context_helper(
            r'Anim = ("\t(2924,3466,\fry360)" if l.i == 2 else "")' + "\n"
            r'A1 = ( "\t(syl.syl_start,syl.syl_start,\4a255)\t(syl.syl_end,syl.syl_end,\4a0)" if l.layer != 1 else "" )',
            ctx,
        )
        self.assertEqual(ctx["A1"], r"\t(syl.syl_start,syl.syl_start,\4a255)\t(syl.syl_end,syl.syl_end,\4a0)")

        res_tags = eval_string_template("\\bord1\n(A1)\n\\t(0,200,\\4a255)", ctx)
        self.assertEqual(
            res_tags,
            r"\bord1\t(150,150,\4a&HFF&)\t(300,300,\4a&H00&)\t(0,200,\4a&HFF&)",
        )

        # Direct Basics/String ternary evaluation with quoted and unquoted branches
        direct_quoted = eval_string_template(r'("\t(2924,3466,\fry360)" if l.i == 2 else "")\blur2', ctx)
        direct_unquoted = eval_string_template(r'(\t(2924,3466,\fry360) if l.i == 2 else "")\blur2', ctx)
        self.assertEqual(direct_quoted, r"\t(2924,3466,\fry360)\blur2")
        self.assertEqual(direct_unquoted, r"\t(2924,3466,\fry360)\blur2")

        # Concatenated branch in Basics/String must not naively slice outer quotes
        concat_branch = eval_string_template(r'("\t(" + str(100) + ",200,\fry360)" if l.i == 2 else "")', ctx)
        self.assertEqual(concat_branch, r"\t(100,200,\fry360)")

        # Literal dialogue text parentheses and ASS hex literals remain preserved
        self.assertEqual(eval_string_template('(1999) ("word")', ctx), '(1999) ("word")')
        self.assertEqual(eval_pyxis_expr("(&HFF00FF& if l.i == 2 else &H000000&)", ctx), "&HFF00FF&")

    def test_validator_triad_parity_and_real_error_detection(self):
        """Verifies GraphValidator emits 0 warnings for valid quoted/unquoted ternaries and flags actual errors."""
        def _graph_with_vars(vars_text: str, extra_string: str = "(Anim)(A1)"):
            return {
                "nodes": [
                    {"id": 1, "type": "Loops/Main Loop", "properties": {"iterator": "syl"}, "outputs": []},
                    {"id": 2, "type": "Variables/Define Vars", "properties": {"variables": vars_text}, "outputs": []},
                    {"id": 3, "type": "Basics/String", "properties": {"value": extra_string}, "outputs": []},
                    {"id": 4, "type": "System/Output", "properties": {"apply_to": "all"}},
                ],
                "links": [
                    [1, 1, 0, 2, 0],
                    [2, 2, 0, 4, 0],
                    [3, 3, 0, 4, 4],
                ],
            }

        valid_quoted = (
            'st = line.start_time - 150\n'
            'Anim = ("\\t(2924,3466,\\fry360)" if l.i == 2 else "\\t(1161,1703,\\fry360)" if l.i == 3 else "")\n'
            'A1 = ( "\\t(syl.syl_start,syl.syl_start,\\4a255)\\t(syl.syl_end,syl.syl_end,\\4a0)" if l.layer != 1 else "" )'
        )
        valid_unquoted = (
            'st = line.start_time - 150\n'
            'Anim = (\\t(2924,3466,\\fry360) if l.i == 2 else \\t(1161,1703,\\fry360) if l.i == 3 else "")\n'
            'A1 = ( \\t(syl.syl_start,syl.syl_start,\\4a255)\\t(syl.syl_end,syl.syl_end,\\4a0) if l.layer != 1 else "" )'
        )
        self.assertEqual(GraphValidator(_graph_with_vars(valid_quoted)).validate(), [])
        self.assertEqual(GraphValidator(_graph_with_vars(valid_unquoted)).validate(), [])

        # Missing 'else' branch in unquoted ternary must warn
        missing_else = r'Anim = (\t(2924,3466,\fry360) if l.i == 2)'
        self.assertTrue(len(GraphValidator(_graph_with_vars(missing_else, extra_string="(Anim)")).validate()) > 0)

        # Undefined variable inside condition must warn
        bad_cond = r'Anim = ("\t(0,100,\fry360)" if missing_flag == 2 else "")'
        issues_cond = GraphValidator(_graph_with_vars(bad_cond, extra_string="(Anim)")).validate()
        self.assertTrue(any("missing_flag" in i.get("message", "") or "missing_flag" in i.get("code_snippet", "") for i in issues_cond))

        # Undefined variable inside quoted ASS tag arguments must warn
        bad_arg = r'Anim = ("\t(0, bad_end_time, \fry360)" if l.i == 2 else "")'
        issues_arg = GraphValidator(_graph_with_vars(bad_arg, extra_string="(Anim)")).validate()
        self.assertTrue(len(issues_arg) > 0)

        # Invalid Dark Tag channel inside quoted branch must warn
        bad_channel = r'Anim = ("\5a255" if l.i == 2 else "")'
        issues_chan = GraphValidator(_graph_with_vars(bad_channel, extra_string="(Anim)")).validate()
        self.assertTrue(len(issues_chan) > 0)

    def test_end_to_end_graph_engine_parity_unquoted_vs_quoted(self):
        """Confirms GraphEngine produces identical valid ASS tags for both unquoted and quoted Define Vars ternaries."""
        def _build_graph(quoted: bool):
            anim_val = (
                r'Anim = ("\t(2924,3466,\fry360)" if l.i == 2 else "\t(1161,1703,\fry360)" if l.i == 3 else "")'
                if quoted
                else r'Anim = (\t(2924,3466,\fry360) if l.i == 2 else \t(1161,1703,\fry360) if l.i == 3 else "")'
            )
            a1_val = (
                r'A1 = ( "\t(syl.syl_start,syl.syl_start,\4a255)\t(syl.syl_end,syl.syl_end,\4a0)" if l.layer != 1 else "" )'
                if quoted
                else r'A1 = ( \t(syl.syl_start,syl.syl_start,\4a255)\t(syl.syl_end,syl.syl_end,\4a0) if l.layer != 1 else "" )'
            )
            return {
                "nodes": [
                    {"id": 1, "type": "Loops/Main Loop", "properties": {"iterator": "syl", "blank_mode": "no_blank"}, "inputs": [], "outputs": [{"name": "Loop", "type": "loop", "links": [1]}]},
                    {"id": 2, "type": "Variables/Define Vars", "properties": {"variables": anim_val + "\n" + a1_val}, "inputs": [{"name": "In", "type": "loop", "link": 1}], "outputs": [{"name": "Out", "type": "loop", "links": [2]}]},
                    {"id": 3, "type": "Basics/String", "properties": {"value": "\\bord1\n(Anim)\n(A1)"}, "inputs": [], "outputs": [{"name": "String", "type": "data", "links": [3]}]},
                    {
                        "id": 4,
                        "type": "System/Output",
                        "properties": {"apply_to": "all", "queue_id": "main", "queue_order": "1"},
                        "inputs": [
                            {"name": "Loop / Domain", "type": "loop", "link": 2},
                            {"name": "Layer", "type": "data", "link": None},
                            {"name": "Start Time", "type": "data", "link": None},
                            {"name": "End Time", "type": "data", "link": None},
                            {"name": "Tags", "type": "data", "link": 3},
                        ],
                    },
                ],
                "links": [
                    [1, 1, 0, 2, 0, "loop"],
                    [2, 2, 0, 4, 0, "loop"],
                    [3, 3, 0, 4, 4, "data"],
                ],
            }

        dialogue_items = [
            {"raw": r"Dialogue: 0,0:00:01.00,0:00:02.00,Default,,0,0,0,,{\k30}Wa{\k40}ka", "selected": True},
            {"raw": r"Dialogue: 0,0:00:02.00,0:00:03.50,Default,,0,0,0,,{\k30}Ta{\k40}ko", "selected": True},
            {"raw": r"Dialogue: 1,0:00:03.50,0:00:05.00,Default,,0,0,0,,{\k30}Ko{\k40}i", "selected": True},
        ]

        out_unquoted = GraphEngine(_build_graph(quoted=False)).process(dialogue_items, self.styles, use_multiprocessing=False)
        out_quoted = GraphEngine(_build_graph(quoted=True)).process(dialogue_items, self.styles, use_multiprocessing=False)

        self.assertEqual(len(out_unquoted), 6)
        self.assertEqual(out_unquoted, out_quoted)

        # Verify line 2 (layer 0) gets Anim(2924,3466,\fry360) and A1
        self.assertIn(r"\t(2924,3466,\fry360)", out_quoted[2])
        self.assertIn(r"\4a&HFF&)\t(", out_quoted[2])
        # Verify line 3 (layer 1) gets Anim(1161,1703,\fry360) without A1
        self.assertIn(r"\t(1161,1703,\fry360)", out_quoted[4])
        self.assertNotIn(r"\4a&HFF&", out_quoted[4])
        # Verify no corrupted control characters anywhere
        for line in out_quoted:
            for bad in ("\t", "\x0c", "\x04"):
                self.assertNotIn(bad, line)


if __name__ == "__main__":
    unittest.main()
