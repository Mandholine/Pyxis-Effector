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

# tests/test_math_node_v103.py
import math
import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from nodes.math_nodes import eval_math_node, _eval_num


class TestUnifiedMathNode(unittest.TestCase):
    def test_eval_num_helper(self):
        ctx = {"x": 10, "syl": {"duration": 500}}
        self.assertEqual(_eval_num("15.5", ctx), 15.5)
        self.assertEqual(_eval_num("x", ctx), 10.0)
        self.assertEqual(_eval_num("syl.duration", ctx), 500.0)
        self.assertEqual(_eval_num("x * 2 + 5", ctx), 25.0)

    # -------------------------------------------------------------------------
    # 1. CATEGORÍA: BASICO
    # -------------------------------------------------------------------------
    def test_basico_suma(self):
        res = eval_math_node(None, categoria="Basico", operacion="Suma", A=10, B=25)
        self.assertEqual(res, 35.0)

    def test_basico_resta(self):
        res = eval_math_node(None, categoria="Basico", operacion="Resta", A=50, B=15)
        self.assertEqual(res, 35.0)

    def test_basico_multiplicacion(self):
        res = eval_math_node(None, categoria="Basico", operacion="Multiplicacion", A=6, B=7)
        self.assertEqual(res, 42.0)

    def test_basico_division(self):
        res = eval_math_node(None, categoria="Basico", operacion="Division", A=100, B=4)
        self.assertEqual(res, 25.0)
        # Safe div by 0
        res_zero = eval_math_node(None, categoria="Basico", operacion="Division", A=100, B=0)
        self.assertEqual(res_zero, 0.0)

    def test_basico_modulo(self):
        res = eval_math_node(None, categoria="Basico", operacion="Modulo", A=10, B=3)
        self.assertEqual(res, 1.0)
        # Modulo by 0
        res_zero = eval_math_node(None, categoria="Basico", operacion="Modulo", A=10, B=0)
        self.assertEqual(res_zero, 0.0)

    def test_basico_potencia(self):
        res = eval_math_node(None, categoria="Basico", operacion="Potencia", A=2, B=8)
        self.assertEqual(res, 256.0)

    def test_basico_absoluto(self):
        res = eval_math_node(None, categoria="Basico", operacion="Absoluto", A=-42)
        self.assertEqual(res, 42.0)

    def test_basico_negativo(self):
        res = eval_math_node(None, categoria="Basico", operacion="Negativo", A=15)
        self.assertEqual(res, -15.0)

    def test_basico_redondear(self):
        res = eval_math_node(None, categoria="Basico", operacion="Redondear", A=3.7)
        self.assertEqual(res, 4.0)

    def test_basico_piso(self):
        res = eval_math_node(None, categoria="Basico", operacion="Piso", A=3.9)
        self.assertEqual(res, 3.0)

    def test_basico_techo(self):
        res = eval_math_node(None, categoria="Basico", operacion="Techo", A=3.1)
        self.assertEqual(res, 4.0)

    # -------------------------------------------------------------------------
    # 2. CATEGORÍA: TRIGONO
    # -------------------------------------------------------------------------
    def test_trigono_seno(self):
        res = eval_math_node(None, categoria="Trigono", operacion="Seno", A=90)
        self.assertAlmostEqual(res, 1.0, places=5)

    def test_trigono_coseno(self):
        res = eval_math_node(None, categoria="Trigono", operacion="Coseno", A=0)
        self.assertAlmostEqual(res, 1.0, places=5)

    def test_trigono_tangente(self):
        res = eval_math_node(None, categoria="Trigono", operacion="Tangente", A=45)
        self.assertAlmostEqual(res, 1.0, places=5)

    def test_trigono_arcseno(self):
        res = eval_math_node(None, categoria="Trigono", operacion="ArcSeno", A=1.0)
        self.assertAlmostEqual(res, 90.0, places=5)

    def test_trigono_arccoseno(self):
        res = eval_math_node(None, categoria="Trigono", operacion="ArcCoseno", A=1.0)
        self.assertAlmostEqual(res, 0.0, places=5)

    def test_trigono_arctangente(self):
        res = eval_math_node(None, categoria="Trigono", operacion="ArcTangente", A=1.0)
        self.assertAlmostEqual(res, 45.0, places=5)

    def test_trigono_arctangente2(self):
        res = eval_math_node(None, categoria="Trigono", operacion="ArcTangente2", Y=10, X=10)
        self.assertAlmostEqual(res, 45.0, places=5)

    def test_trigono_radianes(self):
        res = eval_math_node(None, categoria="Trigono", operacion="Radianes", Grados=180)
        self.assertAlmostEqual(res, math.pi, places=5)

    def test_trigono_grados(self):
        res = eval_math_node(None, categoria="Trigono", operacion="Grados", Radianes=math.pi)
        self.assertAlmostEqual(res, 180.0, places=5)

    # -------------------------------------------------------------------------
    # 3. CATEGORÍA: EASING
    # -------------------------------------------------------------------------
    def test_easing_ease_in(self):
        self.assertEqual(eval_math_node(None, categoria="Easing", operacion="EaseIn", t=0.0), 0.0)
        self.assertEqual(eval_math_node(None, categoria="Easing", operacion="EaseIn", t=0.5), 0.25)
        self.assertEqual(eval_math_node(None, categoria="Easing", operacion="EaseIn", t=1.0), 1.0)

    def test_easing_ease_out(self):
        self.assertEqual(eval_math_node(None, categoria="Easing", operacion="EaseOut", t=0.0), 0.0)
        self.assertEqual(eval_math_node(None, categoria="Easing", operacion="EaseOut", t=0.5), 0.75)
        self.assertEqual(eval_math_node(None, categoria="Easing", operacion="EaseOut", t=1.0), 1.0)

    def test_easing_ease_in_out(self):
        self.assertEqual(eval_math_node(None, categoria="Easing", operacion="EaseInOut", t=0.0), 0.0)
        self.assertEqual(eval_math_node(None, categoria="Easing", operacion="EaseInOut", t=0.5), 0.5)
        self.assertEqual(eval_math_node(None, categoria="Easing", operacion="EaseInOut", t=1.0), 1.0)

    def test_easing_cubic_in(self):
        self.assertAlmostEqual(eval_math_node(None, categoria="Easing", operacion="CubicIn", t=0.5), 0.125, places=5)

    def test_easing_cubic_out(self):
        self.assertAlmostEqual(eval_math_node(None, categoria="Easing", operacion="CubicOut", t=0.5), 0.875, places=5)

    def test_easing_exponencial(self):
        self.assertEqual(eval_math_node(None, categoria="Easing", operacion="Exponencial", t=0.0), 0.0)
        self.assertEqual(eval_math_node(None, categoria="Easing", operacion="Exponencial", t=1.0), 1.0)

    def test_easing_elastico(self):
        self.assertEqual(eval_math_node(None, categoria="Easing", operacion="Elastico", t=0.0), 0.0)
        self.assertEqual(eval_math_node(None, categoria="Easing", operacion="Elastico", t=1.0), 1.0)

    def test_easing_rebote(self):
        self.assertEqual(eval_math_node(None, categoria="Easing", operacion="Rebote", t=0.0), 0.0)
        self.assertEqual(eval_math_node(None, categoria="Easing", operacion="Rebote", t=1.0), 1.0)

    def test_easing_retroceso(self):
        self.assertEqual(eval_math_node(None, categoria="Easing", operacion="Retroceso", t=0.0), 0.0)
        self.assertAlmostEqual(eval_math_node(None, categoria="Easing", operacion="Retroceso", t=1.0), 1.0, places=5)

    # -------------------------------------------------------------------------
    # 4. CATEGORÍA: ONDAS
    # -------------------------------------------------------------------------
    def test_ondas_seno(self):
        res0 = eval_math_node(None, categoria="Ondas", operacion="Seno", t=0.0, Frecuencia=1.0, Amplitud=10.0, Offset=5.0)
        self.assertAlmostEqual(res0, 5.0, places=5)
        res_quarter = eval_math_node(None, categoria="Ondas", operacion="Seno", t=0.25, Frecuencia=1.0, Amplitud=10.0, Offset=5.0)
        self.assertAlmostEqual(res_quarter, 15.0, places=5)

    def test_ondas_cuadrada(self):
        res = eval_math_node(None, categoria="Ondas", operacion="Cuadrada", t=0.1, Frecuencia=1.0, Amplitud=10.0, Offset=0.0)
        self.assertEqual(res, 10.0)

    def test_ondas_triangulo(self):
        res = eval_math_node(None, categoria="Ondas", operacion="Triangulo", t=0.0, Frecuencia=1.0, Amplitud=10.0, Offset=0.0)
        self.assertAlmostEqual(res, 10.0, places=5)

    def test_ondas_diente_sierra(self):
        res = eval_math_node(None, categoria="Ondas", operacion="DienteSierra", t=0.0, Frecuencia=1.0, Amplitud=10.0, Offset=0.0)
        self.assertAlmostEqual(res, -10.0, places=5)

    # -------------------------------------------------------------------------
    # 5. CATEGORÍA: UTILIDADES
    # -------------------------------------------------------------------------
    def test_utilidades_clamp(self):
        self.assertEqual(eval_math_node(None, categoria="Utilidades", operacion="Clamp", Valor=150, Min=0, Max=100), 100.0)
        self.assertEqual(eval_math_node(None, categoria="Utilidades", operacion="Clamp", Valor=-50, Min=0, Max=100), 0.0)

    def test_utilidades_lerp(self):
        self.assertEqual(eval_math_node(None, categoria="Utilidades", operacion="Lerp", A=10, B=20, t=0.5), 15.0)

    def test_utilidades_minimo(self):
        self.assertEqual(eval_math_node(None, categoria="Utilidades", operacion="Minimo", A=10, B=20), 10.0)

    def test_utilidades_maximo(self):
        self.assertEqual(eval_math_node(None, categoria="Utilidades", operacion="Maximo", A=10, B=20), 20.0)

    def test_utilidades_aleatorio(self):
        res1 = eval_math_node(None, categoria="Utilidades", operacion="Aleatorio", Min=5.0, Max=15.0, Semilla=12345)
        res2 = eval_math_node(None, categoria="Utilidades", operacion="Aleatorio", Min=5.0, Max=15.0, Semilla=12345)
        self.assertEqual(res1, res2)
        self.assertTrue(5.0 <= res1 <= 15.0)

    def test_utilidades_mapear_rango(self):
        res = eval_math_node(None, categoria="Utilidades", operacion="MapearRango", Valor=50, MinIn=0, MaxIn=100, MinOut=0, MaxOut=10)
        self.assertEqual(res, 5.0)

    def test_graph_engine_math_node_evaluation(self):
        from node_engine import GraphEngine
        math_node = {
            "id": 1,
            "type": "Math",
            "properties": {"categoria": "Basico", "operacion": "Suma"},
            "inputs": [{"name": "A", "value": "15"}, {"name": "B", "value": "27"}]
        }
        graph_data = {"nodes": [math_node], "links": []}
        engine = GraphEngine(graph_data)
        res = engine.evaluate_data_node(1, {})
        self.assertEqual(res, "42")


if __name__ == "__main__":
    unittest.main()
