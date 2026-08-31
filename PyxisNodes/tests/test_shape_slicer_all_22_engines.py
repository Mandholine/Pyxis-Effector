import sys
import os
import math
import pytest

# Ensure imports resolve
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from clipper_engine import ClipperEngine
from node_engine import GraphEngine

ALL_22_ENGINES = [
    "Rejilla 1D/2D",
    "hex",
    "tri",
    "dia",
    "ring",
    "ray",
    "quad",
    "bez",
    "jigsaw",
    "voronoi",
    "delaunay",
    "ashlar",
    "brick",
    "mondrian",
    "herringbone",
    "scallop",
    "web",
    "rhombille",
    "octagon",
    "kagome",
    "truchet",
    "circuit",
    "pattern"
]

TEST_SHAPE_SQUARE = "m 0 0 l 100 0 l 100 100 l 0 100"
TEST_SHAPE_COMPLEX = "m 0 0 l 200 0 l 200 50 l 50 50 l 50 150 l 200 150 l 200 200 l 0 200"

@pytest.mark.parametrize("engine", ALL_22_ENGINES)
def test_clipper_engine_direct_slicing(engine):
    """Verifica que cada uno de los 22 motores de corte genere piezas válidas con ASSDraw y centro (cx, cy)."""
    pieces = ClipperEngine.slice_grid(
        TEST_SHAPE_SQUARE,
        engine_mode=engine,
        cols=3,
        rows=3,
        size_x=20,
        size_y=20,
        accel_x=1.0,
        accel_y=1.0,
        order=79
    )
    assert len(pieces) > 0, f"Engine '{engine}' failed to generate any pieces."
    
    for idx, p in enumerate(pieces):
        code = p.get("code", "")
        cx = p.get("cx")
        cy = p.get("cy")
        
        assert code and str(code).strip().startswith("m "), f"Piece {idx} of {engine} does not start with 'm ': {code}"
        assert cx is not None and not math.isnan(cx), f"Piece {idx} of {engine} has invalid cx: {cx}"
        assert cy is not None and not math.isnan(cy), f"Piece {idx} of {engine} has invalid cy: {cy}"
        # Check that centers are within reasonable vicinity of the 100x100 box
        assert -100 <= cx <= 200, f"Piece {idx} cx out of range: {cx}"
        assert -100 <= cy <= 200, f"Piece {idx} cy out of range: {cy}"

@pytest.mark.parametrize("engine", ALL_22_ENGINES)
def test_clipper_engine_complex_shape(engine):
    """Verifica el corte sobre siluetas no convexas con huecos y recodos."""
    pieces = ClipperEngine.slice_grid(
        TEST_SHAPE_COMPLEX,
        engine_mode=engine,
        cols=4,
        rows=4,
        size_x=25,
        size_y=25,
        overlap=1.0
    )
    assert len(pieces) > 0, f"Engine '{engine}' failed on complex shape."
    for p in pieces:
        assert p.get("code", "").startswith("m ")

@pytest.mark.parametrize("engine", ALL_22_ENGINES)
def test_node_engine_shape_slicer_evaluation(engine):
    """Verifica que GraphEngine evalúe Shape Slicer en cada modo y devuelva el ASSDraw correcto."""
    node = {
        "id": 101,
        "type": "Shape/Shape Slicer",
        "properties": {
            "modo": engine,
            "shape": TEST_SHAPE_SQUARE,
            "Cols": 2,
            "Rows": 2,
            "Size X": 20,
            "Size Y": 20,
            "out_mode": "shape"
        },
        "inputs": []
    }
    
    ge = GraphEngine({"nodes": [node], "links": []})
    context = {"j": 1}
    result = ge.evaluate_data_node(101, context)
    assert isinstance(result, str), f"Evaluation of {engine} returned non-string: {type(result)}"
    assert not result.startswith("[Err"), f"Evaluation of {engine} failed with error: {result}"
    assert result.strip().startswith("m "), f"Evaluation of {engine} did not output valid ASSDraw: {result[:50]}"
    assert context.get("j_max", 0) > 0, f"Context j_max not set for {engine}"

def test_spatial_sorting_radial():
    """Verifica ordenamiento espacial radial (order=5)."""
    pieces = ClipperEngine.slice_grid(
        TEST_SHAPE_SQUARE,
        engine_mode="hex",
        size_x=15,
        order=5 # Radial from center
    )
    assert len(pieces) >= 2
    # El primer elemento debería estar más cerca del centro (50, 50) que el último
    d_first = math.sqrt((pieces[0]["cx"] - 50)**2 + (pieces[0]["cy"] - 50)**2)
    d_last = math.sqrt((pieces[-1]["cx"] - 50)**2 + (pieces[-1]["cy"] - 50)**2)
    assert d_first <= d_last + 1.0

if __name__ == "__main__":
    print("Running pytest on test_shape_slicer_all_22_engines.py...")
    pytest.main(["-v", __file__])
