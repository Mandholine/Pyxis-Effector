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

# PyxisNodes/nodes_library.py
"""Librería principal y registro de nodos de sistema fundamentales para Pyxis Nodes Engine."""

from decorators import system_node
import nodes

# -----------------------------------------------------------------------------
# NODOS DE SISTEMA: BUCLES Y SALIDA
# -----------------------------------------------------------------------------
system_node(
    "Loops", "Main Loop", node_kind="main_loop", outputs=["Loop", "Iterator (i)", "Total (N)"], color="#1E5F3A",
    properties={"iterador": "syl"},
    widgets=[]
)

system_node(
    "Loops", "MaxLoop", node_kind="max_loop", inputs=["Loop In", "Start", "End"], outputs=["Loop Out", "Iterator (j)", "Total (N)"], color="#8A2BE2",
    properties={"modo": "Normal", "veces": "3", "step_ms": "41.7", "start_time": "start_time", "end_time": "end_time", "var_name": "j"},
    widgets=[
        {"type": "combo", "name": "Modo:", "property": "modo", "values": ["Normal", "FBF"]},
        {"type": "text", "name": "Iterations (N)", "property": "veces"},
        {"type": "text", "name": "Step (ms)", "property": "step_ms"},
        {"type": "text", "name": "Start", "property": "start_time"},
        {"type": "text", "name": "End", "property": "end_time"},
        {"type": "text", "name": "Var Name (j)", "property": "var_name"}
    ]
)

system_node(
    "Loops", "Module", node_kind="data", color="#1E5F3A",
    inputs=["Iterator (i)", "Total (N)", "Sub-step (m)"], outputs=["Data"],
    properties={"iter": "i", "total": "N", "sub_m": "0"},
    widgets=[
        {"type": "text", "name": "Iterator (i)", "property": "iter"},
        {"type": "text", "name": "Total (N)", "property": "total"},
        {"type": "text", "name": "Sub-step (m)", "property": "sub_m"}
    ]
)

system_node(
    "System", "Output", node_kind="output", color="#8B0000",
    inputs=["Loop / Domain", "Layer", "Start Time", "End Time", "Tags", "Return", "Queue ID", "Queue Order"],
    outputs=["Preview"],
    properties={"apply_to": "Sel. Lines", "queue_id": "", "queue_order": "", "origin_align": 5},
    widgets=[]
)

system_node(
    "System", "Previewer", node_kind="preview", color="#2563EB",
    inputs=["Output"],
    outputs=[],
    properties={"salida_ids": ""},
    widgets=[
        {"type": "text", "name": "Output IDs", "property": "salida_ids"}
    ]
)

system_node(
    "System", "Benchmark Math", node_kind="data", color="#D97706",
    inputs=["Iterations"], outputs=["Out", "Time ms"],
    properties={"iterations": "10000", "complexity": "Heavy Math (Trig + Sqrt)"},
    widgets=[
        {"type": "text", "name": "Iterations", "property": "iterations"}
    ]
)

# -----------------------------------------------------------------------------
# NODOS DE SISTEMA: VARIABLES
# -----------------------------------------------------------------------------
system_node(
    "Variables", "Define Vars", node_kind="set_vars", 
    inputs=["In"], outputs=["Out"], color="#5F1E5E",
    properties={"variables": ""},
    widgets=[{"type": "text", "name": "Vars", "property": "variables"}]
)

system_node(
    "Variables", "Get Var", node_kind="data", outputs=["Data"], color="#5F1E5E",
    properties={"var_name": "j"},
    widgets=[{"type": "text", "name": "Name", "property": "var_name"}]
)

system_node(
    "Variables", "Memory", node_kind="data", color="#5F1E5E",
    inputs=["Key", "Value"], outputs=["Data"],
    properties={"modo": "Remember (Guardar)", "clave": "ref", "valor": "", "default": ""},
    widgets=[
        {"type": "text", "name": "Key:", "property": "clave"},
        {"type": "text", "name": "Valor / Default:", "property": "valor"}
    ]
)


# -----------------------------------------------------------------------------
# NODOS DE FUNCIONES / INTERPOLACIÓN
# -----------------------------------------------------------------------------
system_node(
    "Functions", "Interpolator", node_kind="data", color="#8B5CF6",
    inputs=["Iterator", "Total", "Accel", "V1", "V2"], outputs=["Data"],
    properties={"iterador": "i", "total": "N", "accel": "1.0", "v1": "0", "v2": "1"},
    widgets=[]
)

# -----------------------------------------------------------------------------
# NODOS DE RAÍZ (DIRECTOS EN MENÚ PRINCIPAL "ADD NODE")
# -----------------------------------------------------------------------------
system_node(
    "", "Text", node_kind="text", color="#0F766E",
    inputs=["Text"], outputs=["Out"],
    properties={"operacion": "Strip Tags"},
    widgets=[]
)

system_node(
    "", "String", node_kind="data", 
    inputs=[], outputs=["String"], color="#4B4B4B",
    properties={"valor": ""},
    widgets=[{"type": "text", "name": "Text", "property": "valor"}]
)

system_node(
    "", "Concatenate", node_kind="data", 
    inputs=["In1", "In2"], outputs=["String"], color="#4B4B4B",
    properties={"expandable": True, "separador": "nil"},
    widgets=[]
)

system_node(
    "", "MultiTag", node_kind="tag_master", 
    inputs=["X", "Y"], outputs=["String"], color="#2D5A7B",
    properties={"tag_type": "pos", "x": "0", "y": "0"},
    widgets=[]
)

system_node(
    "", "Dynamic Format", node_kind="data", 
    inputs=["In1"], outputs=["String"], color="#4B4B4B",
    properties={"Formato": "%s", "expandable": True},
    widgets=[{"type": "text", "name": "Formato", "property": "Formato"}]
)

system_node(
    "", "Number", node_kind="data", 
    inputs=[], outputs=["Number"], color="#1A5F4C",
    properties={"valor": "0"},
    widgets=[{"type": "text", "name": "Value", "property": "valor"}]
)

system_node(
    "", "Color Picker", node_kind="data", 
    inputs=[], outputs=["ASS Color"], color="#1A4A5F",
    properties={"colors": ["#FFFFFF"], "formats": ["ASS"]},
    widgets=[]
)

system_node(
    "Functions", "Conditioner", node_kind="data", color="#8B5CF6",
    inputs=["Condition", "If True", "If False"], outputs=["String"],
    properties={"condicion": "True", "si_verdadero": "", "si_falso": ""},
    widgets=[
        {"type": "text", "name": "Condition", "property": "condicion"},
        {"type": "text", "name": "If True", "property": "si_verdadero"},
        {"type": "text", "name": "If False", "property": "si_falso"}
    ]
)

system_node(
    "", "MultiRandom", node_kind="data", color="#1A5F4C",
    inputs=["Min", "Max"], outputs=["Data"],
    properties={"modo": "R", "min": "0", "max": "100", "step": "", "options": "", "counter": ""},
    widgets=[]
)

system_node(
    "Functions", "Polar to Cartesian", node_kind="data", color="#1A5F4C",
    inputs=["Origin X", "Origin Y", "Angle (°)", "Radius"],
    outputs=["\\pos Tag", "X", "Y", "dX", "dY"],
    properties={"x": "0", "y": "0", "angle": "0", "radius": "100"},
    widgets=[]
)

system_node(
    "Functions", "Color Gradient", node_kind="data", color="#8B5CF6",
    inputs=["Progress (0-1)", "Color List"], outputs=["ASS Color"],
    properties={"prog": "char.i / char.n", "colors_str": "#95E648,#3E750C,#ED38CA"},
    widgets=[]
)

# -----------------------------------------------------------------------------
# NODOS DE TIEMPO (EFFECTOR 2 TIME NODES)
# -----------------------------------------------------------------------------
system_node(
    "Time", "Lead In", node_kind="data", color="#2563EB",
    inputs=["Delay (ms)"], outputs=["Data"],
    properties={"delay": "40"},
    widgets=[{"type": "text", "name": "Delay (ms)", "property": "delay"}]
)

system_node(
    "Time", "Lead Out", node_kind="data", color="#2563EB",
    inputs=["Delay (ms)"], outputs=["Data"],
    properties={"delay": "40"},
    widgets=[{"type": "text", "name": "Delay (ms)", "property": "delay"}]
)

system_node(
    "Time", "Middle 1", node_kind="data", color="#2563EB",
    inputs=["Delay (ms)"], outputs=["Data"],
    properties={"delay": "30"},
    widgets=[{"type": "text", "name": "Delay (ms)", "property": "delay"}]
)

system_node(
    "Time", "Middle 2", node_kind="data", color="#2563EB",
    inputs=["Delay (ms)"], outputs=["Data"],
    properties={"delay": "30"},
    widgets=[{"type": "text", "name": "Delay (ms)", "property": "delay"}]
)

system_node(
    "Time", "Loop 1", node_kind="data", color="#2563EB",
    inputs=["Delay (ms)"], outputs=["Data"],
    properties={"delay": "30", "modo": "leadin"},
    widgets=[{"type": "text", "name": "Delay (ms)", "property": "delay"}]
)

system_node(
    "Time", "Loop 2", node_kind="data", color="#2563EB",
    inputs=["Delay (ms)"], outputs=["Data"],
    properties={"delay": "30", "modo": "leadin"},
    widgets=[{"type": "text", "name": "Delay (ms)", "property": "delay"}]
)

system_node(
    "Time", "Time Ipol", node_kind="data", color="#2563EB",
    inputs=["Duration (ms)", "Points / Values", "Acceleration"], outputs=["Data"],
    properties={"dur": "syl.duration", "points": "0, 100", "accel": "1.0"},
    widgets=[]
)

system_node(
    "Time", "Synced Time", node_kind="data", color="#2563EB",
    inputs=["Constant", "Fade (ms)", "Max Extra", "Delay Line", "Threshold"],
    outputs=["Extra ms", "Sync End"],
    properties={"progression_const": "0", "fade_dur": "300", "max_added_time": "2000", "delay": "250", "max_gap_threshold": "3000"},
    widgets=[]
)

# -----------------------------------------------------------------------------
# NODOS SHAPE Y CORTE CON 22 MOTORES DE MALLA
# -----------------------------------------------------------------------------
system_node(
    "Shape", "Shapes Library", node_kind="data", color="#5B2C6F",
    inputs=[], outputs=["Shape"],
    properties={"categoria": "Formas", "forma": "Circulo"},
    widgets=[]
)

system_node(
    "Shape", "Shape Slicer", node_kind="data", color="#5B2C6F",
    inputs=["Shape", "Cols", "Rows", "Size X", "Size Y", "Scale X", "Scale Y", "Off X", "Off Y", "Angle", "Bleed", "Accel", "Text Scale", "Pre-Offset", "Anchor", "Output Type", "Order"],
    outputs=["Piece", "X", "Y", "Col", "Row"],
    properties={"shape": "", "cols": "2", "rows": "2", "size_x": "20", "size_y": "20", "scale_x": "1.0", "scale_y": "1.0", "offset_x": "0", "offset_y": "0", "angle": "0", "overlap": "0", "accel": "1.0", "text_scale": "1.0", "pre_offset": "0", "anchor": "piezas", "out_mode": "Shape", "order": "79", "modo": "Rejilla 1D/2D"},
    widgets=[
        {"type": "combo", "name": "Modo:", "property": "modo", "values": [
            "Rejilla 1D/2D", "hex", "tri", "dia", "ring", "voronoi", "delaunay", "brick", "jigsaw",
            "circuit", "kagome", "rhombille", "herringbone", "mondrian", "truchet", "scallop",
            "ashlar", "bez", "octagon", "ray", "web", "quad", "pattern"
        ]}
    ]
)

system_node(
    "Shape", "Shape Manipulator", node_kind="data", color="#5B2C6F",
    inputs=["Shape / Texto", "Scale X", "Scale Y", "Angle", "Offset X", "Offset Y", "Border Offset", "Anchor"],
    outputs=["Shape"],
    properties={"shape": "", "scale_x": "100", "scale_y": "100", "angle": "0", "offset_x": "0", "offset_y": "0", "offset_border": "0.0", "anchor": "center", "mode": "Escalar"},
    widgets=[]
)

system_node(
    "Shape", "Shape Transform", node_kind="data", color="#7D3C98",
    inputs=["Shape / Texto", "Factor (t)", "Ratio", "Anchor"],
    outputs=["Shape"],
    properties={"shape": "", "mode": "Inflate", "t": "0.5", "ratio": "1.0", "inflate_mode": "Circle", "angle_x": "0", "angle_y": "0", "radius": "10.0", "corner_mode": "Round", "curve": "30", "bend_t": "1.0", "axis": "x", "target_shape": "", "energy": "0.35", "step_px": "0", "anchor": "center"},
    widgets=[]
)

system_node(
    "Shape", "Concentric Borders", node_kind="data", color="#5B2C6F",
    inputs=["Shape / Text", "Base Mode", "Max Rings", "Separation", "Overlap", "Anchor"],
    outputs=["Shape", "\\pos", "Index", "Total"],
    properties={"shape": "", "modo": "Hueco (borders)", "loop_count": "5", "separation": "5", "overlap": "0.5", "out_mode": "Shape", "anchor": "relativo"},
    widgets=[]
)

system_node(
    "Shape", "Shape Walker", node_kind="data", color="#5B2C6F",
    inputs=["Shape / Text", "Progress (t)", "Start (t)", "Subdivs"],
    outputs=["Shape Out", "\\pos Tag", "Angle (\\frz)", "Length", "Tip X", "Tip Y"],
    properties={"shape": "", "progress": "1.0", "start_t": "0.0", "modo": "Global (Continuo)", "invert": "0", "subdivs": "30"},
    widgets=[]
)

system_node(
    "Functions", "Clip Gradient", node_kind="data", color="#5B2C6F",
    inputs=["Stripes", "Angle", "Padding", "Overlap", "Order"],
    outputs=["Output", "Progress (0-1)", "Index", "Total"],
    properties={"num_clips": "5", "angle": "0", "padding": "4", "overlap": "0.5", "order": "Normal", "out_mode": "Clip"},
    widgets=[]
)

system_node(
    "", "Math", node_kind="math", color="#0D9488",
    inputs=["A", "B"], outputs=["Out"],
    properties={"categoria": "Basico", "operacion": "Suma"},
    widgets=[]
)

# -----------------------------------------------------------------------------
# NODOS DE BEZIER, PARTÍCULAS Y TEXTO CON DESPLEGABLES
# -----------------------------------------------------------------------------
system_node(
    "Functions", "Bezier Curve", node_kind="data", color="#8B5CF6",
    inputs=["P0", "P1", "P2", "P3", "t", "Subdivs"],
    outputs=["\\pos", "X", "Y", "Tan", "Norm", "Spline"],
    properties={"p0": "0,0", "p1": "50,100", "p2": "150,100", "p3": "200,0", "t": "0.5", "subdivs": "100", "modo": "Cúbica 2D"},
    widgets=[]
)

system_node(
    "Functions", "Particles", node_kind="data", color="#8B5CF6",
    inputs=["Path / Origen", "Particle", "Density", "RedrawDist", "Seed", "Scale", "Numpad Order"],
    outputs=["Shp Out", "\\pos Tag", "X Arr", "Y Arr", "Total"],
    properties={"shape": "", "particle_shape": "", "density": "5.0", "redraw_dist": "0", "seed": "1", "scale": "1.0", "modo": "Contorno v2", "order": "79"},
    widgets=[
        {"type": "combo", "name": "Modo:", "property": "modo", "values": ["Contorno v2", "Borde (Contorno)", "Relleno Interior"]},
        {"type": "combo", "name": "Order:", "property": "order", "values": ["79 (TL->BR)", "13 (BL->TR)", "97 (TR->BL)", "31 (BR->TL)", "5 (Centro->Afuera)", "-5 (Afuera->Centro)", "71 (Columnas)", "Rand (Aleatorio)"]},
        {"type": "text", "name": "Particle:", "property": "particle_shape"},
        {"type": "text", "name": "Density:", "property": "density"},
        {"type": "text", "name": "RedrawDist:", "property": "redraw_dist"},
        {"type": "text", "name": "Seed:", "property": "seed"},
        {"type": "text", "name": "Scale:", "property": "scale"}
    ]
)

system_node(
    "Functions", "IMG to pixels", node_kind="data", color="#8B5CF6",
    inputs=["Image Path", "Particle", "Frame", "Step", "Alpha", "Scale", "Anchor", "Numpad Order"],
    outputs=["Shp Out", "Color Arr", "\\pos Tag", "X Arr", "Y Arr", "Total", "Pixels Array"],
    properties={"image_path": "", "particle_shape": "", "frame": "1", "step": "2", "alpha_threshold": "128", "scale": "1.0", "anchor": "Center", "order": "79"},
    widgets=[
        {"type": "combo", "name": "Anchor:", "property": "anchor", "values": ["Center", "TopLeft", "TopRight", "BottomLeft", "BottomRight"]},
        {"type": "combo", "name": "Order:", "property": "order", "values": ["79 (TL->BR)", "13 (BL->TR)", "97 (TR->BL)", "31 (BR->TL)", "5 (Centro->Afuera)", "-5 (Afuera->Centro)", "71 (Columnas)", "Rand (Aleatorio)"]},
        {"type": "text", "name": "Particle:", "property": "particle_shape"},
        {"type": "text", "name": "Image Path:", "property": "image_path"},
        {"type": "text", "name": "Frame:", "property": "frame"},
        {"type": "text", "name": "Step:", "property": "step"},
        {"type": "text", "name": "Alpha:", "property": "alpha_threshold"},
        {"type": "text", "name": "Scale:", "property": "scale"}
    ]
)

system_node(
    "Functions", "Text to Shape", node_kind="data", color="#0F766E",
    inputs=["Text", "Font", "Size", "Scale"],
    outputs=["Shape Out", "Width", "Height"],
    properties={"text": "", "font_name": "Arial", "font_size": "100", "scale": "1.0"},
    widgets=[
        {"type": "text", "name": "Text:", "property": "text"},
        {"type": "text", "name": "Font:", "property": "font_name"},
        {"type": "text", "name": "Size:", "property": "font_size"},
        {"type": "text", "name": "Scale:", "property": "scale"}
    ]
)

system_node(
    "Functions", "Text on Path", node_kind="data", color="#0F766E",
    inputs=["Path / Shape", "Offset", "Extra Angle", "Subdivs"],
    outputs=["Tag Out", "\\pos Tag", "Angle (\\frz)", "X", "Y", "Length"],
    properties={
        "shape": "",
        "modo": "Center (Centrado)",
        "offset": "0",
        "extra_angle": "0",
        "subdivs": "30"
    },
    widgets=[]
)


system_node(
    "Shape", "IMG to Shape", node_kind="data", color="#0F766E",
    inputs=["Image Path", "Frame (j)", "Threshold", "Tolerance", "Smoothing", "Optimization", "Scale Out", "Width Out", "Height Out", "Offset X", "Offset Y", "Image Scale", "Binarize Mode"],
    outputs=["Shape Out", "Width", "Height", "Puntos", "Shapes Array", "Total Frames"],
    properties={
        "image_path": "",
        "frame_idx": "1",
        "threshold": "128",
        "tolerance": "1.0",
        "alphamax": "1.0",
        "opttoler": "0.2",
        "out_scale": "1.0",
        "out_w": "0.0",
        "out_h": "0.0",
        "offset_x": "0.0",
        "offset_y": "0.0",
        "img_scale": "1.0",
        "bin_mode": "Luminancia",
        "modo": "Potrace",
        "anchor": "Center",
        "invert": "Normal",
        "invert_img": "Normal"
    },
    widgets=[
        {"type": "text", "name": "Image Path:", "property": "image_path", "default": ""},
        {"type": "text", "name": "Frame (j):", "property": "frame_idx", "default": "1"},
        {"type": "text", "name": "Threshold:", "property": "threshold", "default": "128"},
        {"type": "text", "name": "Tolerance:", "property": "tolerance", "default": "1.0"},
        {"type": "text", "name": "Smoothing:", "property": "alphamax", "default": "1.0"},
        {"type": "text", "name": "Optimization:", "property": "opttoler", "default": "0.2"},
        {"type": "text", "name": "Scale Out:", "property": "out_scale", "default": "1.0"},
        {"type": "text", "name": "Width Out:", "property": "out_w", "default": "0.0"},
        {"type": "text", "name": "Height Out:", "property": "out_h", "default": "0.0"},
        {"type": "text", "name": "Offset X:", "property": "offset_x", "default": "0.0"},
        {"type": "text", "name": "Offset Y:", "property": "offset_y", "default": "0.0"},
        {"type": "text", "name": "Image Scale:", "property": "img_scale", "default": "1.0"},
        {"type": "text", "name": "Binarize Mode:", "property": "bin_mode", "default": "Luminancia"}
    ]
)


system_node(
    "Functions", "Tag Oscillator", node_kind="data", color="#1D4ED8",
    inputs=["Start Time", "End Time", "Step (ms)", "Trans (ms)", "Duty Cycle", "Tags", "Accel", "Dilate Step", "Dilate Trans", "Seq Offset", "Rhythm Pattern"],
    outputs=["Tag Out", "Current Val", "Keyframes", "Values"],
    properties={
        "start_time": "", "end_time": "", "step_ms": "200.0", "trans_ms": "50.0",
        "duty_cycle": "", "tags": r"\frz30\fry20,\frz-20\fry-20", "accel": "1.0",
        "dilat_step_ms": "0.0", "dilat_trans_ms": "0.0", "offset_seq_ms": "0.0",
        "rhythm_pattern": "", "modo_oscilacion": "Onda", "modo_orden": "Secuencial"
    },
    widgets=[]
)

# -----------------------------------------------------------------------------
# NODOS DE AUDIO (EFFECTOR AUDIO NODES)
# -----------------------------------------------------------------------------
system_node(
    "Audio", "Audio Modulator", node_kind="data", color="#0284C7",
    inputs=["Audio Path", "Tag", "Min Val", "Max Val", "Ganancia", "Step ms", "Smoothing", "Start Time", "End Time"],
    outputs=["Tags Out", "Current Value", "Array Valores", "RMS Promedio"],
    properties={
        "audio_path": "",
        "tag_name": "fscy",
        "min_val": "100",
        "max_val": "160",
        "gain": "1.0",
        "step_ms": "41.7",
        "smoothing": "0.2",
        "modo": "RMS (Volumen)",
        "min_hz": "20",
        "max_hz": "250",
        "start_time": "",
        "end_time": ""
    },
    widgets=[]
)

system_node(
    "Audio", "Audio Waveform", node_kind="data", color="#0284C7",
    inputs=["Audio Path", "Width", "Height", "Samples", "Ganancia", "Thickness", "Scale", "Start Time", "End Time"],
    outputs=["Shape Out", "\\pos Tag", "X Array", "Y Array", "Bandas Array"],
    properties={
        "audio_path": "",
        "modo": "Osciloscopio",
        "ancho": "400",
        "alto": "60",
        "muestras": "32",
        "gain": "1.0",
        "grosor": "2",
        "escala": "1.0",
        "min_hz": "20",
        "max_hz": "16000",
        "start_time": "",
        "end_time": ""
    },
    widgets=[]
)