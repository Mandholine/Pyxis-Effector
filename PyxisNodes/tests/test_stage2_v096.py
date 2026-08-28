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

# tests/test_stage2_v096.py
import unittest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from nodes.tag_nodes import node_condicionador
from nodes.math_nodes import math_random_master

class TestStage2V096(unittest.TestCase):
    def test_condicionador_true_condition(self):
        ctx = {}
        res = node_condicionador(ctx, condicion=True, si_verdadero=r"\fscx120", si_falso="")
        self.assertEqual(res, r"\fscx120")

    def test_condicionador_false_condition(self):
        ctx = {}
        res = node_condicionador(ctx, condicion=False, si_verdadero=r"\fscx120", si_falso="")
        self.assertEqual(res, "")

    def test_condicionador_truthy_string(self):
        ctx = {}
        res = node_condicionador(ctx, condicion="1", si_verdadero="YES", si_falso="NO")
        self.assertEqual(res, "YES")

    def test_condicionador_falsy_string(self):
        ctx = {}
        res = node_condicionador(ctx, condicion="0", si_verdadero="YES", si_falso="NO")
        self.assertEqual(res, "NO")

    def test_random_r(self):
        ctx = {}
        val = float(math_random_master(ctx, modo="R", min_val=10, max_val=20))
        self.assertTrue(10 <= val <= 20)

    def test_random_rs(self):
        ctx = {}
        val = float(math_random_master(ctx, modo="Rs", min_val=10, max_val=20))
        self.assertTrue(10 <= abs(val) <= 20)

    def test_random_rc(self):
        ctx = {}
        val_str = math_random_master(ctx, modo="Rc", min_val=0, max_val=1)
        self.assertEqual(len(val_str.split('.')[1]), 2)
        val = float(val_str)
        self.assertTrue(0 <= val <= 1)

    def test_random_re(self):
        ctx = {}
        opts = "red, green, blue"
        val = math_random_master(ctx, modo="Re", options=opts)
        self.assertIn(val, ["red", "green", "blue"])

    def test_random_rfake_deterministic(self):
        ctx = {"i": 5}
        val1 = math_random_master(ctx, modo="Rfake", min_val=0, max_val=50, counter=5)
        val2 = math_random_master(ctx, modo="Rfake", min_val=0, max_val=50, counter=5)
        self.assertEqual(val1, val2)

    def test_random_context_vars(self):
        ctx = {"j": 5, "rx": 1280}
        val = float(math_random_master(ctx, modo="R", min_val="j", max_val="j*10"))
        self.assertTrue(5.0 <= val <= 50.0)

    def test_random_comma_decimal(self):
        ctx = {}
        val = float(math_random_master(ctx, modo="Rd", min_val="0,5", max_val="5,0", step="0,5"))
        self.assertTrue(0.5 <= val <= 5.0)

    def test_random_math_expression(self):
        ctx = {}
        val = float(math_random_master(ctx, modo="R", min_val="10+5", max_val="100/2"))
        self.assertTrue(15.0 <= val <= 50.0)

    def test_random_empty_step_keeps_range(self):
        ctx = {}
        val = float(math_random_master(ctx, modo="R", min_val="200", max_val="500", step=""))
        self.assertTrue(200.0 <= val <= 500.0)

    def test_random_extended_modes(self):
        ctx = {}
        col = math_random_master(ctx, modo="Rcolor", min_val="&HFFFFFF&", max_val="&H000000&")
        self.assertTrue(col.startswith("&H") and col.endswith("&"))

        r2d = math_random_master(ctx, modo="R2d", min_val="10", max_val="20")
        parts = r2d.split(",")
        self.assertEqual(len(parts), 2)
        self.assertTrue(10.0 <= float(parts[0]) <= 20.0)
        self.assertTrue(10.0 <= float(parts[1]) <= 20.0)

        rbool = math_random_master(ctx, modo="Rbool", min_val="100")
        self.assertEqual(rbool, "True")

        rstep = float(math_random_master(ctx, modo="Rstep", min_val="0", max_val="100", step="45"))
        self.assertIn(rstep, [0.0, 45.0, 90.0])

    def test_graphengine_random_re_connected(self):
        from node_engine import GraphEngine
        graph = {
            'nodes': [
                {
                    'id': 1,
                    'type': 'String',
                    'properties': {'valor': 'op1, op2, op3'},
                    'inputs': [],
                    'outputs': [{'name': 'String', 'type': 'data'}]
                },
                {
                    'id': 2,
                    'type': 'MultiRandom',
                    'properties': {'modo': 'Re', 'options': ''},
                    'inputs': [{'name': 'Options', 'link': 100}],
                    'outputs': [{'name': 'Data', 'type': 'data'}]
                }
            ],
            'links': [[100, 1, 0, 2, 0]]
        }
        engine = GraphEngine(graph)
        res = engine.evaluate_data_node(2, {})
        self.assertIn(res, ['op1', 'op2', 'op3'])

    def test_graphengine_random_rcolor_connected(self):
        from node_engine import GraphEngine
        graph = {
            'nodes': [
                {
                    'id': 1,
                    'type': 'String',
                    'properties': {'valor': '&H0000FF&'},
                    'inputs': [],
                    'outputs': [{'name': 'String', 'type': 'data'}]
                },
                {
                    'id': 2,
                    'type': 'MultiRandom',
                    'properties': {'modo': 'Rcolor', 'min': '&HFFFFFF&', 'max': '&H000000&'},
                    'inputs': [{'name': 'Color Min', 'link': None}, {'name': 'Color Max', 'link': 200}],
                    'outputs': [{'name': 'Data', 'type': 'data'}]
                }
            ],
            'links': [[200, 1, 0, 2, 1]]
        }
        engine = GraphEngine(graph)
        res = engine.evaluate_data_node(2, {})
        self.assertTrue(res.startswith('&H') and res.endswith('&'))

    def test_graphengine_random_and_condicionador(self):
        from node_engine import GraphEngine
        graph = {
            'nodes': [
                {
                    'id': 1,
                    'type': 'MultiRandom',
                    'properties': {'modo': 'Rd', 'min': '10', 'max': '50', 'step': '0.5'},
                    'inputs': [],
                    'outputs': [{'name': 'random', 'type': 'data'}]
                },
                {
                    'id': 2,
                    'type': 'Functions/Conditioner',
                    'properties': {'condicion': 'sili.syl % 2 == 0', 'si_verdadero': 'AZUL', 'si_falso': 'BLANCO'},
                    'inputs': [{'name': 'Condition'}, {'name': 'If True'}, {'name': 'If False'}],
                    'outputs': [{'name': 'resultado', 'type': 'data'}]
                }
            ],
            'links': []
        }
        engine = GraphEngine(graph)
        ctx_par = {'sili': type('Sili', (), {'syl': 2})()}
        ctx_impar = {'sili': type('Sili', (), {'syl': 3})()}

        val_rnd = float(engine.evaluate_data_node(1, ctx_par))
        self.assertTrue(10.0 <= val_rnd <= 50.0)

        val_cond_par = engine.evaluate_data_node(2, ctx_par)
        self.assertEqual(val_cond_par, 'AZUL')

        val_cond_impar = engine.evaluate_data_node(2, ctx_impar)
        self.assertEqual(val_cond_impar, 'BLANCO')

if __name__ == "__main__":
    unittest.main()
