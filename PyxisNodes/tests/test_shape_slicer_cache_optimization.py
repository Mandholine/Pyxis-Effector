# tests/test_shape_slicer_cache_optimization.py
import unittest
import time
from clipper_engine import ClipperEngine, _SLICE_GRID_CACHE, _PARSE_ASSDRAW_CACHE
from node_engine import GraphEngine

class MockUnit:
    def __init__(self, name="TestSyl", shape="m 0 0 l 100 0 l 100 100 l 0 100"):
        self.name = name
        self.text = name
        self.shape = shape
        self.center = 50.0
        self.middle = 50.0
        self.pos_x = 50.0
        self.pos_y = 50.0
        self.x = 50.0
        self.y = 50.0
        self.start_time = 0
        self.end_time = 1000
        self.duration = 1000
        self._slicer_cache = {}

class TestShapeSlicerCacheOptimization(unittest.TestCase):

    def setUp(self):
        ClipperEngine.clear_cache()

    def test_intra_loop_cache_invokes_slice_grid_only_once(self):
        """Verifica que dentro del bucle de una unidad activa (j = 1..N), slice_grid se invoca exactamente 1 sola vez."""
        graph_json = {
            "nodes": [
                {
                    "id": 10,
                    "type": "Functions/Shape Slicer",
                    "properties": {"modo": "hex", "Radius": 15, "anchor": "piezas", "out_mode": "Shape"},
                    "inputs": [{"name": "Shape", "value": "m 0 0 l 100 0 l 100 100 l 0 100"}]
                },
                {
                    "id": 20,
                    "type": "Outputs/Output",
                    "properties": {"apply_to": "all"},
                    "inputs": [{"name": "Return", "link": 100}]
                }
            ],
            "links": [[100, 10, 0, 20, 1, "string"]]
        }
        engine = GraphEngine(graph_json)

        unit = MockUnit("Syl1")
        
        orig_slice_grid = ClipperEngine.slice_grid
        call_count = 0
        def counted_slice_grid(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            return orig_slice_grid(*args, **kwargs)

        ClipperEngine.slice_grid = counted_slice_grid
        try:
            for j in range(1, 21):
                ctx = {"j": j, "active_unit": unit, "syl": unit, "line": None}
                res = engine.evaluate_data_node(10, ctx, 0)
                self.assertIsNotNone(res)
                self.assertTrue(len(str(res)) > 0)

            self.assertEqual(call_count, 1, f"slice_grid se llamo {call_count} veces en lugar de 1 sola vez.")
        finally:
            ClipperEngine.slice_grid = orig_slice_grid

    def test_global_lru_cache_hit_returns_instantaneous(self):
        """Verifica que llamadas repetidas con los mismos parametros retornen inmediatamente desde _SLICE_GRID_CACHE."""
        sq = "m 0 0 l 100 0 l 100 100 l 0 100"
        
        t0 = time.perf_counter()
        p1 = ClipperEngine.slice_grid(sq, engine_mode="voronoi", size_x=20)
        t_first = (time.perf_counter() - t0) * 1000

        self.assertGreater(len(p1), 0)
        self.assertGreater(len(_SLICE_GRID_CACHE), 0)

        t1 = time.perf_counter()
        for _ in range(100):
            p2 = ClipperEngine.slice_grid(sq, engine_mode="voronoi", size_x=20)
            self.assertEqual(len(p1), len(p2))
        t_subsequent = (time.perf_counter() - t1) * 1000

        avg_hit_time = t_subsequent / 100.0
        self.assertLess(avg_hit_time, 0.05, f"Cache hit promedio fue {avg_hit_time:.4f} ms")

    def test_cache_invalidation_on_parameter_change(self):
        """Verifica que al cambiar parametros la cache no mezcle resultados y genere el nuevo corte."""
        sq = "m 0 0 l 100 0 l 100 100 l 0 100"
        
        p_hex15 = ClipperEngine.slice_grid(sq, engine_mode="hex", size_x=15)
        p_hex30 = ClipperEngine.slice_grid(sq, engine_mode="hex", size_x=30)
        p_tri15 = ClipperEngine.slice_grid(sq, engine_mode="tri", size_x=15)

        self.assertNotEqual(len(p_hex15), len(p_hex30))
        self.assertNotEqual(len(p_hex15), len(p_tri15))

    def test_parse_assdraw_cache_speedup(self):
        """Verifica que parse_assdraw este memoizado y aumente el rendimiento."""
        sq = "m 0 0 l 100 0 l 100 100 l 0 100"
        cnt1 = ClipperEngine.parse_assdraw(sq)
        self.assertGreater(len(cnt1), 0)
        self.assertIn((sq, 10), _PARSE_ASSDRAW_CACHE)

        t0 = time.perf_counter()
        for _ in range(1000):
            cnt2 = ClipperEngine.parse_assdraw(sq)
        elapsed = (time.perf_counter() - t0) * 1000
        avg_time_us = (elapsed / 1000.0) * 1000.0
        self.assertLess(avg_time_us, 50.0, f"Parse assdraw cache hit promedio {avg_time_us:.2f} us demasiado lento")

    def test_clear_cache(self):
        """Verifica que ClipperEngine.clear_cache limpie los almacenes de memoria."""
        sq = "m 0 0 l 100 0 l 100 100 l 0 100"
        ClipperEngine.slice_grid(sq, engine_mode="hex", size_x=15)
        ClipperEngine.parse_assdraw(sq)

        self.assertGreater(len(_SLICE_GRID_CACHE), 0)
        self.assertGreater(len(_PARSE_ASSDRAW_CACHE), 0)

        ClipperEngine.clear_cache()
        self.assertEqual(len(_SLICE_GRID_CACHE), 0)
        self.assertEqual(len(_PARSE_ASSDRAW_CACHE), 0)

if __name__ == "__main__":
    unittest.main()
