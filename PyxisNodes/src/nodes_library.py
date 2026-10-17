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

"""Core library and registration of fundamental system nodes for Pyxis Nodes Engine."""

from decorators import system_node
import nodes

system_node(
    "Loops", "Main Loop", node_kind="main_loop", outputs=["Loop", "Iterator (i)", "Total (N)"], color="#1E5F3A",
    properties={"iterator": "syl", "blank_mode": "no_blank"},
    widgets=[
        {"type": "combo", "name": "Iterator:", "property": "iterator", "values": ["syl", "char", "word", "line"]},
        {"type": "combo", "name": "Blank Mode:", "property": "blank_mode", "values": ["no_blank", "with_blanks"]}
    ]
)

system_node(
    "Loops", "MaxLoop", node_kind="max_loop", inputs=["Loop In", "Start", "End"], outputs=["Loop Out", "Counter", "Total"], color="#8A2BE2",
    properties={"mode": "normal", "iterations": "3", "step_ms": "41.7", "start_time": "start_time", "end_time": "end_time", "var_name": "j"},
    widgets=[
        {"type": "combo", "name": "Mode:", "property": "mode", "values": ["normal", "fbf"]},
        {"type": "text", "name": "Iterations (N)", "property": "iterations"},
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
    widgets=[
        {"type": "combo", "name": "Apply to:", "property": "apply_to", "values": ["Sel. Lines", "Selected Lines", "Style Lines", "All Lines"]}
    ]
)

system_node(
    "System", "Previewer", node_kind="preview", color="#2563EB",
    inputs=["Output"],
    outputs=[],
    properties={"output_ids": ""},
    widgets=[
        {"type": "text", "name": "Output IDs", "property": "output_ids"}
    ]
)

system_node(
    "System", "Script Code", node_kind="step", color="#3B82F6",
    inputs=["Loop In", "In1", "In2"],
    outputs=["Loop Out", "Result"],
    properties={
        "language": "Python",
        "script": "result = 'Hello Pyxis ' + str(in1 if in1 else syl.text)",
        "inputs_count": 2
    },
    widgets=[
        {"type": "combo", "name": "Language", "property": "language", "values": ["Python", "Lua"]}
    ]
)

system_node(
    "System", "Benchmark Math", node_kind="data", color="#D97706",
    inputs=["Iterations"], outputs=["Out", "Time ms"],
    properties={"iterations": "10000", "complexity": "Heavy Math (Trig + Sqrt)"},
    widgets=[
        {"type": "combo", "name": "Complexity", "property": "complexity", "values": ["Heavy Math (Trig + Sqrt)", "Prime Sieve", "Matrix Mult"]}
    ]
)

system_node(
    "Variables", "Sys Var", node_kind="variable_master", color="#5F1E5E",
    inputs=[], outputs=["Data"],
    properties={"var_name": "syl.text"},
    widgets=[{"type": "text", "name": "Variable", "property": "var_name"}]
)

system_node(
    "Variables", "Define Vars", node_kind="set_vars", 
    inputs=["In"], outputs=["Out"], color="#5F1E5E",
    properties={"variables": ""},
    widgets=[{"type": "text", "name": "Vars", "property": "variables"}]
)

system_node(
    "Variables", "Get Var", node_kind="data", color="#5F1E5E",
    inputs=[], outputs=["Data"],
    properties={"var_name": "j"},
    widgets=[{"type": "text", "name": "Name", "property": "var_name"}]
)

system_node(
    "Variables", "Memory", node_kind="data", color="#5F1E5E",
    inputs=["Key", "Value"], outputs=["Data"],
    properties={"mode": "remember", "key": "ref", "value": "", "default": ""},
    widgets=[
        {"type": "combo", "name": "Mode:", "property": "mode", "values": ["remember", "retrieve"]},
        {"type": "text", "name": "Key:", "property": "key"},
        {"type": "text", "name": "Value / Default:", "property": "value"}
    ]
)


system_node(
    "Functions", "Interpolator", node_kind="data", color="#8B5CF6",
    inputs=["Iterator", "Total", "Accel", "V1", "V2"], outputs=["Data", "Batch / List"],
    properties={"iterator": "i", "total": "N", "accel": "1.0", "v1": "0", "v2": "1"},
    widgets=[]
)

system_node(
    "Basics", "Text", node_kind="text", color="#0F766E",
    inputs=["Text"], outputs=["Out"],
    properties={"operation": "strip_tags"},
    widgets=[
        {"type": "combo", "name": "Operation:", "property": "operation", "values": [
            "strip_tags", "uppercase", "lowercase", "clean_spaces", "replace", "substring", "length", "contains", "kana", "romaji_to_karaoke"
        ]}
    ]
)

system_node(
    "Basics", "String", node_kind="data", 
    inputs=[], outputs=["String"], color="#4B4B4B",
    properties={"value": ""},
    widgets=[{"type": "text", "name": "Text", "property": "value"}]
)

system_node(
    "Basics", "Concatenate", node_kind="data", 
    inputs=["In1", "In2"], outputs=["String"], color="#4B4B4B",
    properties={"expandable": True, "separator": "nil"},
    widgets=[]
)

system_node(
    "Basics", "MultiTag", node_kind="tag_master", 
    inputs=["X", "Y"], outputs=["String"], color="#2D5A7B",
    properties={"tag_type": "pos", "x": "fx.pos_x", "y": "fx.pos_y"},
    widgets=[]
)

system_node(
    "Basics", "Dynamic Format", node_kind="data", 
    inputs=["In1"], outputs=["String"], color="#4B4B4B",
    properties={"format": "%s", "expandable": True},
    widgets=[{"type": "text", "name": "Format", "property": "format"}]
)

system_node(
    "Basics", "Number", node_kind="data", 
    inputs=[], outputs=["Number"], color="#1A5F4C",
    properties={"value": "0"},
    widgets=[{"type": "text", "name": "Value", "property": "value"}]
)

system_node(
    "Basics", "Color Picker", node_kind="data", 
    inputs=[], outputs=["Color List", "ASS Color"], color="#1A4A5F",
    properties={"colors": ["#FFFFFF"], "formats": ["ASS"]},
    widgets=[]
)

system_node(
    "Functions", "Conditioner", node_kind="data", color="#8B5CF6",
    inputs=["Condition", "If True", "If False"], outputs=["Out"],
    properties={"condition": "True", "if_true": "", "if_false": ""},
    widgets=[
        {"type": "text", "name": "Condition", "property": "condition"},
        {"type": "text", "name": "If True", "property": "if_true"},
        {"type": "text", "name": "If False", "property": "if_false"}
    ]
)

system_node(
    "Basics", "MultiRandom", node_kind="data", color="#1A5F4C",
    inputs=["Min", "Max", "Step", "Total (N)", "Iterator"], outputs=["Data", "Batch / List"],
    properties={"mode": "R", "min": "0", "max": "100", "step": "", "options": "", "counter": "", "total": "1", "iterator": ""},
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
    inputs=["Progress (0-1)", "Color List", "Total (N)", "Accel"],
    outputs=["ASS Color", "Color List", "Tags"],
    properties={"prog": "char.i / char.n", "colors_str": "#95E648,#3E750C,#ED38CA", "total": "1", "accel": "1.0", "tag_type": "\\1c"},
    widgets=[]
)

system_node(
    "Time", "Lead In", node_kind="data", color="#2563EB",
    inputs=["Delay (ms)"], outputs=["Data"],
    properties={"delay_ms": "40"},
    widgets=[{"type": "text", "name": "Delay (ms)", "property": "delay_ms"}]
)

system_node(
    "Time", "Lead Out", node_kind="data", color="#2563EB",
    inputs=["Delay (ms)"], outputs=["Data"],
    properties={"delay_ms": "40"},
    widgets=[{"type": "text", "name": "Delay (ms)", "property": "delay_ms"}]
)

system_node(
    "Time", "Middle 1", node_kind="data", color="#2563EB",
    inputs=["Delay (ms)"], outputs=["Data"],
    properties={"delay_ms": "30"},
    widgets=[{"type": "text", "name": "Delay (ms)", "property": "delay_ms"}]
)

system_node(
    "Time", "Middle 2", node_kind="data", color="#2563EB",
    inputs=["Delay (ms)"], outputs=["Data"],
    properties={"delay_ms": "30"},
    widgets=[{"type": "text", "name": "Delay (ms)", "property": "delay_ms"}]
)

system_node(
    "Time", "Loop 1", node_kind="data", color="#2563EB",
    inputs=["Delay (ms)"], outputs=["Data"],
    properties={"delay_ms": "30", "mode": "leadin"},
    widgets=[{"type": "text", "name": "Delay (ms)", "property": "delay_ms"}]
)

system_node(
    "Time", "Loop 2", node_kind="data", color="#2563EB",
    inputs=["Delay (ms)"], outputs=["Data"],
    properties={"delay_ms": "30", "mode": "leadin"},
    widgets=[{"type": "text", "name": "Delay (ms)", "property": "delay_ms"}]
)

system_node(
    "Time", "Ipol", node_kind="data", color="#2563EB",
    inputs=["Duration (ms)", "Points / Values", "Acceleration"], outputs=["Data"],
    properties={"dur_ms": "syl.duration", "points": "0, 100", "accel": "1.0"},
    widgets=[
        {"type": "text", "name": "Duration (ms)", "property": "dur_ms"},
        {"type": "text", "name": "Points / Values", "property": "points"},
        {"type": "text", "name": "Acceleration", "property": "accel"}
    ]
)

system_node(
    "Time", "Duration", node_kind="data", color="#2563EB",
    inputs=["Start Time (ms)", "End Time (ms)"], outputs=["Duration (ms)"],
    properties={"start_time": "line.start_time", "end_time": "line.end_time"},
    widgets=[
        {"type": "text", "name": "Start Time (ms)", "property": "start_time"},
        {"type": "text", "name": "End Time (ms)", "property": "end_time"}
    ]
)

system_node(
    "Time", "Offset", node_kind="data", color="#2563EB",
    inputs=["Base (ms)"], outputs=["Time (ms)"],
    properties={"base": "0", "offset_ms": "0"},
    widgets=[{"type": "text", "name": "Offset (ms)", "property": "offset_ms"}]
)

system_node(
    "Time", "Synced", node_kind="data", color="#2563EB",
    inputs=["Constant", "Fade (ms)", "Max Extra", "Delay Line", "Threshold"],
    outputs=["Extra ms", "Sync End"],
    properties={"mode": "order", "progression_const": "0", "fade_dur": "300", "max_added_time": "2000", "delay_ms": "250", "max_gap_threshold": "3000"},
    widgets=[
        {"type": "combo", "name": "Mode:", "property": "mode", "values": ["order", "style", "actor", "layer", "effect"]},
        {"type": "text", "name": "Constant", "property": "progression_const"},
        {"type": "text", "name": "Fade (ms)", "property": "fade_dur"},
        {"type": "text", "name": "Max Extra", "property": "max_added_time"},
        {"type": "text", "name": "Delay Line", "property": "delay_ms"},
        {"type": "text", "name": "Threshold", "property": "max_gap_threshold"}
    ]
)

system_node(
    "Time", "Parse ASS Time", node_kind="data", color="#2563EB",
    inputs=["ASS Time"], outputs=["Time (ms)"],
    properties={"ass_time": "0:00:00.00"},
    widgets=[{"type": "text", "name": "ASS Time", "property": "ass_time"}]
)

system_node(
    "Time", "Format ASS Time", node_kind="data", color="#2563EB",
    inputs=["Time (ms)"], outputs=["ASS Time"],
    properties={"time": "0"},
    widgets=[{"type": "text", "name": "Time (ms)", "property": "time"}]
)

system_node(
    "Time", "Time to Frame", node_kind="data", color="#2563EB",
    inputs=["Time (ms)", "Frame Dur (ms)"], outputs=["Frames (f)"],
    properties={"mode": "round", "source": "custom", "time": "0", "frame_dur": ""},
    widgets=[
        {"type": "combo", "name": "Mode:", "property": "mode", "values": ["round", "floor", "ceil"]},
        {"type": "combo", "name": "Source:", "property": "source", "values": ["custom", "start", "end", "dur"]}
    ]
)

system_node(
    "Time", "Frame to Time", node_kind="data", color="#2563EB",
    inputs=["Frames (f)", "Frame Dur (ms)"], outputs=["Time (ms)", "ASS Time"],
    properties={"format": "ms", "source": "custom", "frames": "1", "frame_dur": "", "iter_name": "j"},
    widgets=[
        {"type": "combo", "name": "Format:", "property": "format", "values": ["ms", "hms", "sec"]},
        {"type": "combo", "name": "Source:", "property": "source", "values": ["custom", "iterator", "i", "j", "J"]}
    ]
)

system_node(
    "Shape", "Library", node_kind="data", color="#105A8C",
    inputs=[], outputs=["Shape"],
    properties={"category": "shapes", "shape": "circle"},
    widgets=[]
)



system_node(
    "Functions", "Clip Gradient", node_kind="data", color="#5B2C6F",
    inputs=["Cols", "Rows", "Angle", "Overlap", "Order"],
    outputs=["Output", "Progress (0-1)", "Index", "Total", "Col", "Row"],
    properties={"cols": "5", "rows": "1", "angle": "0", "padding": "0", "pad_top": "0", "pad_bottom": "0", "pad_left": "0", "pad_right": "0", "overlap": "0.5", "order": "79", "out_mode": "clip"},
    widgets=[]
)

system_node(
    "Basics", "Math", node_kind="math", color="#0D9488",
    inputs=["A", "B"], outputs=["Out"],
    properties={"category": "basic", "operation": "add"},
    widgets=[]
)

system_node(
    "Functions", "Bezier Curve", node_kind="data", color="#8B5CF6",
    inputs=["Origin", "P0", "P1", "P2", "P3", "t", "Subdivs", "Shape", "Points", "Trajectory Mode", "Dist Range", "Seed", "Loops"],
    outputs=["\\pos", "X", "Y", "Tan", "Norm", "Spline", "Spline L", "Spline R"],
    properties={
        "p0": "0,0",
        "p1": "50,100",
        "p2": "150,100",
        "p3": "200,0",
        "t": "0.5",
        "subdivs": "100",
        "mode": "cubic_2d",
        "shape": "",
        "points": "0,0; 50,100; 150,100; 200,0",
        "origin": "",
        "traj_mode": "free_wander",
        "dist_range": "50,120",
        "seed": "1",
        "loops": "8"
    },
    widgets=[
        {"type": "combo", "name": "Mode:", "property": "mode", "values": [
            "cubic_2d", "quadratic_2d", "n_degree", "constant_speed", "shape_contour", "subdivide", "trajectory"
        ]},
        {"type": "text", "name": "Origin:", "property": "origin"},
        {"type": "text", "name": "P0:", "property": "p0"},
        {"type": "text", "name": "P1:", "property": "p1"},
        {"type": "text", "name": "P2:", "property": "p2"},
        {"type": "text", "name": "P3:", "property": "p3"},
        {"type": "text", "name": "t:", "property": "t"},
        {"type": "text", "name": "Subdivs:", "property": "subdivs"},
        {"type": "text", "name": "Shape:", "property": "shape"},
        {"type": "text", "name": "Points:", "property": "points"},
        {"type": "combo", "name": "Trajectory Mode:", "property": "traj_mode", "values": [
            "free_wander", "bounded", "closed_loop"
        ]},
        {"type": "text", "name": "Dist Range:", "property": "dist_range"},
        {"type": "text", "name": "Seed:", "property": "seed"},
        {"type": "text", "name": "Loops:", "property": "loops"},
    ]
)

system_node(
    "Functions", "Particles", node_kind="data", color="#8B5CF6",
    inputs=["Path / Origin", "Particle", "Density", "RedrawDist", "Seed", "Scale", "Numpad Order"],
    outputs=["Shp Out", "\\pos Tag", "X Arr", "Y Arr", "Total"],
    properties={"shape": "", "particle_shape": "", "density": "5.0", "redraw_dist": "0", "seed": "1", "scale": "1.0", "mode": "outline_v2", "order": "79"},
    widgets=[
        {"type": "combo", "name": "Mode:", "property": "mode", "values": ["outline_v2", "border", "inner_fill"]},
        {"type": "combo", "name": "Order:", "property": "order", "values": ["79", "97", "13", "31", "71", "17", "93", "39", "5", "-5", "cw", "ccw", "rand"]},
        {"type": "text", "name": "Particle:", "property": "particle_shape"},
        {"type": "text", "name": "Density:", "property": "density"},
        {"type": "text", "name": "RedrawDist:", "property": "redraw_dist"},
        {"type": "text", "name": "Seed:", "property": "seed"},
        {"type": "text", "name": "Scale:", "property": "scale"}
    ]
)

system_node(
    "Functions", "IMG to pixels", node_kind="data", color="#8B5CF6",
    inputs=["Image Path", "Particle", "Frame", "Step", "Alpha", "Scale", "Anchor", "Order"],
    outputs=["Shp Out", "Color Arr", "\\pos Tag", "X Arr", "Y Arr", "Total", "Pixels Array"],
    properties={"image_path": "", "particle_shape": "", "frame_idx": "1", "frame": "1", "step": "2", "alpha_threshold": "128", "scale": "1.0", "anchor": "center", "order": "79"},
    widgets=[
        {"type": "combo", "name": "Anchor:", "property": "anchor", "values": ["center", "topleft", "topright", "bottomleft", "bottomright"]},
        {"type": "combo", "name": "Order:", "property": "order", "values": ["79", "97", "13", "31", "71", "17", "93", "39", "5", "-5", "cw", "ccw", "rand"]},
        {"type": "text", "name": "Particle:", "property": "particle_shape"},
        {"type": "text", "name": "Image Path:", "property": "image_path"},
        {"type": "text", "name": "Frame:", "property": "frame_idx"},
        {"type": "text", "name": "Step:", "property": "step"},
        {"type": "text", "name": "Alpha:", "property": "alpha_threshold"},
        {"type": "text", "name": "Scale:", "property": "scale"}
    ]
)

system_node(
    "Functions", "Text to Shape", node_kind="data", color="#0F766E",
    inputs=["Text", "Font", "Size", "Scale"],
    outputs=["Shape Out", "Width", "Height"],
    properties={"text": "", "font_name": "", "font_size": "", "scale": ""},
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
        "mode": "center",
        "offset": "0",
        "extra_angle": "0",
        "subdivs": "30"
    },
    widgets=[
        {"type": "combo", "name": "Mode:", "property": "mode", "values": [
            "center", "left", "right", "justified", "animated"
        ]},
        {"type": "text", "name": "Offset:", "property": "offset"},
        {"type": "text", "name": "Extra Angle:", "property": "extra_angle"},
        {"type": "text", "name": "Subdivs:", "property": "subdivs"}
    ]
)

system_node(
    "Functions", "Move Text", node_kind="data", color="#8B5CF6",
    inputs=["Text", "Delta X", "Delta Y", "Offset X", "Offset Y", "Shape (d)", "Points (x1,y1; x2,y2)", "Step (px)", "Start Time (t1)", "End Time (t2)", "Acceleration"],
    outputs=["Text"],
    properties={
        "text": "", "tags": "", "dx": "0", "dy": "0", "ox": "0", "oy": "0",
        "shape": "", "points": "", "trajectory": "", "anchor": "center",
        "step_px": "7.5", "t1": "0", "t2": "fx.dur", "accel": "1.0"
    },
    widgets=[]
)

system_node(
    "Functions", "Move Tag", node_kind="data", color="#8B5CF6",
    inputs=["Tags", "Shape (d)", "Step (px)", "Anchor", "Start Time (t1)", "End Time (t2)", "Acceleration"],
    outputs=["Data"],
    properties={
        "mode": "trajectory",
        "tags": "",
        "shape": "",
        "points": "",
        "dx": "10.0",
        "dy": "10.0",
        "dur": "50",
        "seed": "0",
        "step_px": "7.5",
        "anchor": "center",
        "t1": "0",
        "t2": "fx.dur",
        "accel": "1.0"
    },
    widgets=[
        {"type": "combo", "name": "Mode:", "property": "mode", "values": ["trajectory", "waypoints", "jitter"]},
        {"type": "combo", "name": "Anchor:", "property": "anchor", "values": ["center", "origin", "first_point"]},
        {"type": "text", "name": "Tags:", "property": "tags"},
        {"type": "text", "name": "Shape (d):", "property": "shape"},
        {"type": "text", "name": "Points:", "property": "points"},
        {"type": "text", "name": "Amplitude X (dx):", "property": "dx"},
        {"type": "text", "name": "Amplitude Y (dy):", "property": "dy"},
        {"type": "text", "name": "Step Dur (ms):", "property": "dur"},
        {"type": "text", "name": "Random Seed:", "property": "seed"},
        {"type": "text", "name": "Step (px):", "property": "step_px"},
        {"type": "text", "name": "Start Time (t1):", "property": "t1"},
        {"type": "text", "name": "End Time (t2):", "property": "t2"},
        {"type": "text", "name": "Acceleration:", "property": "accel"}
    ]
)



system_node(
    "Shape", "IMG to Shape", node_kind="data", color="#0F766E",
    inputs=["Image Path", "Frame (j)", "Threshold", "Tolerance", "Smoothing", "Optimization", "Scale Out", "Width Out", "Height Out", "Offset X", "Offset Y", "Image Scale", "Binarize Mode"],
    outputs=["Shape Out", "Width", "Height", "Points", "Shapes Array", "Total Frames"],
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
        "bin_mode": "luminance",
        "mode": "potrace",
        "anchor": "center",
        "invert": "normal",
        "invert_img": "normal"
    },
    widgets=[
        {"type": "combo", "name": "Anchor:", "property": "anchor", "values": ["center", "origin", "relative", "absolute"]},
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
        {"type": "text", "name": "Binarize Mode:", "property": "bin_mode", "default": "luminance"}
    ]
)

system_node(
    "Shape", "Array", node_kind="data", color="#0F766E",
    inputs=["Shape", "Cols", "Rows", "Size X", "Size Y", "Scale X", "Scale Y", "Off X", "Off Y", "Angle", "Step Angle", "Bleed", "Accel", "Text Scale", "Pre-Offset", "Anchor", "Output Type", "Order", "Loop Mode"],
    outputs=["Array", "X", "Y", "Col", "Row", "Angle"],
    properties={
        "mode": "grid", "out_mode": "shape", "anchor": "pieces", "order": "79",
        "overlap": "0", "accel": "1.0", "loop_mode": "shape",
        "cols": "2", "rows": "2", "size_x": "20", "size_y": "20",
        "scale_x": "1.0", "scale_y": "1.0", "offset_x": "0", "offset_y": "0",
        "angle": "0", "step_angle": "0", "text_scale": "1.0", "pre_offset": "0"
    },
    widgets=[]
)

system_node(
    "Shape", "Slicer", node_kind="data", color="#0F766E",
    inputs=["Shape", "Cols", "Rows", "Size X", "Size Y", "Scale X", "Scale Y", "Off X", "Off Y", "Angle", "Bleed", "Accel", "Text Scale", "Pre-Offset", "Anchor", "Output Type", "Order"],
    outputs=["Piece", "X", "Y", "Col", "Row"],
    properties={
        "mode": "grid", "out_mode": "shape", "anchor": "pieces", "order": "79",
        "overlap": "0", "accel": "1.0",
        "cols": "2", "rows": "2", "size_x": "20", "size_y": "20",
        "scale_x": "1.0", "scale_y": "1.0", "offset_x": "0", "offset_y": "0",
        "angle": "0", "text_scale": "1.0", "pre_offset": "0"
    },
    widgets=[
        {"type": "combo", "name": "Mode:", "property": "mode", "values": [
            "grid", "hex", "tri", "diamond", "rings", "voronoi", "delaunay", "brick",
            "jigsaw", "circuit", "kagome", "cubes", "herringbone", "mondrian", "truchet",
            "scallop", "ashlar", "bezier", "octagon", "rays", "web", "quad", "modular"
        ]}
    ]
)

system_node(
    "Shape", "Stroke", node_kind="data", color="#0F766E",
    inputs=["Shape / Text", "Width (px)"],
    outputs=["Shape Out", "Width"],
    properties={
        "width": "4.0", "join_mode": "round", "cap_mode": "bezier", "miter_limit": "2.0"
    },
    widgets=[
        {"type": "combo", "name": "Join Mode:", "property": "join_mode", "values": ["round", "miter", "bevel"]},
        {"type": "combo", "name": "Cap Mode:", "property": "cap_mode", "values": ["round", "square", "flat", "bezier"]}
    ]
)

system_node(
    "Shape", "Walker", node_kind="data", color="#0F766E",
    inputs=["Shape / Text", "Progress (t)", "Start (t)", "Subdivs"],
    outputs=["Shape Out", r"\pos Tag", r"Angle (\frz)", "Length", "Tip X", "Tip Y"],
    properties={
        "progress": "1.0", "start_t": "0.0", "mode": "global", "invert": "normal", "subdivs": "30", "close_path": False
    },
    widgets=[
        {"type": "combo", "name": "Mode:", "property": "mode", "values": ["global", "piece"]},
        {"type": "combo", "name": "Invert:", "property": "invert", "values": ["normal", "inverted"]},
        {"type": "toggle", "name": "Close Path", "property": "close_path", "default": False}
    ]
)

system_node(
    "Shape", "Manipulator", node_kind="data", color="#0F766E",
    inputs=["Shape / Text", "Factor (t)", "Scale X", "Scale Y", "Anchor"],
    outputs=["Shape"],
    properties={
        "mode": "scale", "anchor": "center", "axis": "none", "t": "1.0",
        "scale_x": "100", "scale_y": "100", "angle": "0",
        "skew_x": "0", "skew_y": "0", "density": "0.0", "offset_border": "0"
    },
    widgets=[
        {"type": "combo", "name": "Mode:", "property": "mode", "values": [
            "scale", "rotate", "reflect", "redraw", "deform", "position", "borders", "matrix"
        ]},
        {"type": "combo", "name": "Anchor:", "property": "anchor", "values": [
            "center", "origin", "relative", "absolute"
        ]},
        {"type": "combo", "name": "Axis:", "property": "axis", "values": ["none", "x", "y", "xy"]},
        {"type": "text", "name": "Factor (t):", "property": "t", "default": "1.0"},
        {"type": "text", "name": "Scale X:", "property": "scale_x", "default": "100"},
        {"type": "text", "name": "Scale Y:", "property": "scale_y", "default": "100"},
        {"type": "text", "name": "Angle:", "property": "angle", "default": "0"},
        {"type": "text", "name": "Offset Border:", "property": "offset_border", "default": "0"}
    ]
)

system_node(
    "Shape", "Transform", node_kind="data", color="#0F766E",
    inputs=["Shape / Text", "Factor (t)", "Ratio", "Anchor"],
    outputs=["Shape"],
    properties={
        "mode": "inflate", "anchor": "center", "axis": "x", "t": "1.0",
        "ratio": "1.0", "inflate_mode": "circle"
    },
    widgets=[
        {"type": "combo", "name": "Mode:", "property": "mode", "values": [
            "inflate", "skew", "round_corners", "flexor", "distort", "distort2"
        ]},
        {"type": "combo", "name": "Anchor:", "property": "anchor", "values": [
            "center", "origin", "relative", "absolute"
        ]},
        {"type": "combo", "name": "Axis:", "property": "axis", "values": ["x", "y"]},
        {"type": "combo", "name": "Inflate Mode:", "property": "inflate_mode", "values": ["circle", "ellipse"]},
        {"type": "text", "name": "Factor (t):", "property": "t", "default": "1.0"},
        {"type": "text", "name": "Ratio:", "property": "ratio", "default": "1.0"}
    ]
)

system_node(
    "Shape", "Filter", node_kind="data", color="#0F766E",
    inputs=["Shape / Text", "Expr X", "Expr Y", "Factor (t)", "Subdivs"],
    outputs=["Shape"],
    properties={
        "mode": "vertices", "expr_x": "x", "expr_y": "y", "t": "1.0",
        "subdivs": "0", "anchor": "center"
    },
    widgets=[
        {"type": "combo", "name": "Mode:", "property": "mode", "values": ["vertices", "group", "noise"]},
        {"type": "combo", "name": "Anchor:", "property": "anchor", "values": ["center", "origin", "relative", "absolute"]},
        {"type": "text", "name": "Expr X:", "property": "expr_x", "default": "x"},
        {"type": "text", "name": "Expr Y:", "property": "expr_y", "default": "y"},
        {"type": "text", "name": "Factor (t):", "property": "t", "default": "1.0"},
        {"type": "text", "name": "Subdivs:", "property": "subdivs", "default": "0"}
    ]
)

system_node(
    "Shape", "Clipper", node_kind="data", color="#0F766E",
    inputs=["Shape A", "Shape B", "Mode", "Delta (px)", "Subj Fill", "Clip Fill", "Join Mode", "End Mode", "Miter Limit", "Post-Offset", "Clean Dist", "Anchor"],
    outputs=["Shape Out", "Out List", "BBox Data"],
    properties={
        "mode": "difference",
        "shape_a": "",
        "shape_b": "",
        "delta": "0.0",
        "post_offset": "",
        "subj_fill": "evenodd",
        "clip_fill": "evenodd",
        "join_type": "round",
        "end_type": "closed_polygon",
        "miter_limit": "2.0",
        "arc_tolerance": "0.25",
        "clean_dist": "0.0",
        "strictly_simple": "0",
        "reverse_subj": "0",
        "reverse_clip": "0",
        "anchor": "center",
        "out_mode": "shape",
        "scale": "10000.0"
    },
    widgets=[
        {"type": "combo", "name": "Mode:", "property": "mode", "values": [
            "difference", "intersection", "union", "xor", "offset", "minkowski_sum", "minkowski_diff"
        ]},
        {"type": "text", "name": "Shape A (Subject):", "property": "shape_a", "default": ""},
        {"type": "text", "name": "Shape B (Clip):", "property": "shape_b", "default": ""},
        {"type": "text", "name": "Delta (px):", "property": "delta", "default": "0.0"},
        {"type": "combo", "name": "Subj Fill:", "property": "subj_fill", "values": [
            "evenodd", "nonzero", "positive", "negative"
        ]},
        {"type": "combo", "name": "Clip Fill:", "property": "clip_fill", "values": [
            "evenodd", "nonzero", "positive", "negative"
        ]},
        {"type": "combo", "name": "Join Mode:", "property": "join_type", "values": [
            "round", "miter", "square"
        ]},
        {"type": "combo", "name": "End Mode:", "property": "end_type", "values": [
            "closed_polygon", "closed_line", "open_round", "open_square", "open_butt"
        ]},
        {"type": "text", "name": "Miter Limit:", "property": "miter_limit", "default": "2.0"},
        {"type": "text", "name": "Post-Offset:", "property": "post_offset", "default": ""},
        {"type": "text", "name": "Clean Dist:", "property": "clean_dist", "default": "0.0"},
        {"type": "combo", "name": "Anchor:", "property": "anchor", "values": [
            "center", "origin", "relative", "absolute"
        ]},
        {"type": "combo", "name": "Out Mode:", "property": "out_mode", "values": [
            "shape", "clip", "iclip"
        ]},
        {"type": "combo", "name": "Strictly Simple:", "property": "strictly_simple", "values": ["0", "1"]},
        {"type": "combo", "name": "Reverse Subj:", "property": "reverse_subj", "values": ["0", "1"]},
        {"type": "combo", "name": "Reverse Clip:", "property": "reverse_clip", "values": ["0", "1"]}
    ]
)

system_node(
    "Shape", "Union & Divide", node_kind="data", color="#0F766E",
    inputs=["Shape In", "Fill Rule", "Auto-Intersect", "Anchor", "Order"],
    outputs=["Shape Out", "Out List", "BBox Data"],
    properties={
        "mode": "divide",
        "fill_type": "evenodd",
        "clean_self_intersect": "1",
        "anchor": "pieces",
        "order": "79",
        "shape": "",
        "shape_b": "",
        "tagmode": "ipol",
        "tags": ""
    },
    widgets=[
        {"type": "combo", "name": "Mode:", "property": "mode", "values": [
            "divide", "union", "subpaths", "fusion"
        ]},
        {"type": "combo", "name": "Fill Rule:", "property": "fill_type", "values": [
            "evenodd", "nonzero", "positive", "negative"
        ]},
        {"type": "combo", "name": "Anchor:", "property": "anchor", "values": [
            "pieces", "relative", "parent_org", "pos", "absolute"
        ]},
        {"type": "combo", "name": "Order:", "property": "order", "values": [
            "79", "97", "13", "31", "71", "17", "93", "39", "5", "-5", "cw", "ccw", "rand"
        ]},
        {"type": "text", "name": "Auto-Intersect:", "property": "clean_self_intersect", "default": "1"}
    ]
)

system_node(
    "Shape", "Multi", node_kind="data", color="#0F766E",
    inputs=["Mode", "Size", "Px Pattern", "Separation", "Factor (t)", "Anchor", "Tags"],
    outputs=["Shape"],
    properties={
        "mode": "concentric_squares", "size": "100.0", "width": "70.0", "height": "50.0",
        "anchor": "center", "px": "4", "space": "0.0", "separation": "0.0",
        "angle": "0.0", "t": "1.0", "tags": "", "loop_mode": "shape", "out_mode": "shape"
    },
    widgets=[
        {"type": "combo", "name": "Mode:", "property": "mode", "values": [
            "concentric_squares", "multi_shape_mosaic", "concentric_rings", "honeycomb", "pixel_art"
        ]},
        {"type": "combo", "name": "Anchor:", "property": "anchor", "values": [
            "center", "origin", "relative", "absolute"
        ]},
        {"type": "text", "name": "Size:", "property": "size", "default": "100.0"},
        {"type": "text", "name": "Width:", "property": "width", "default": "70.0"},
        {"type": "text", "name": "Height:", "property": "height", "default": "50.0"},
        {"type": "text", "name": "Px Pattern:", "property": "px", "default": "4"},
        {"type": "text", "name": "Separation:", "property": "separation", "default": "0.0"},
        {"type": "text", "name": "Factor (t):", "property": "t", "default": "1.0"}
    ]
)

system_node(
    "Shape", "Concentric Borders", node_kind="data", color="#0F766E",
    inputs=["Shape / Text", "Base Mode", "Max Rings", "Separation", "Overlap", "Anchor"],
    outputs=["Shape", r"\pos", "Index", "Total"],
    properties={
        "shape": "", "mode": "hollow", "loop_count": "5", "separation": "5",
        "overlap": "0.5", "out_mode": "shape", "anchor": "relative"
    },
    widgets=[
        {"type": "combo", "name": "Base Mode:", "property": "mode", "values": ["hollow", "solid"]},
        {"type": "combo", "name": "Output Mode:", "property": "out_mode", "values": ["shape", "clip", "iclip"]},
        {"type": "combo", "name": "Anchor:", "property": "anchor", "values": ["relative", "pieces", "parent_org", "pos", "absolute"]},
        {"type": "text", "name": "Max Rings:", "property": "loop_count", "default": "5"},
        {"type": "text", "name": "Separation:", "property": "separation", "default": "5"},
        {"type": "text", "name": "Overlap:", "property": "overlap", "default": "0.5"}
    ]
)


system_node(
    "Functions", "Tag Manipulator", node_kind="data", color="#1D4ED8",
    inputs=["Tags In", "Target Tag"],
    outputs=["Tags Out", "Value", "Raw String"],
    properties={"mode": "invert", "tags": "", "target_tag": "frz"},
    widgets=[
        {"type": "combo", "name": "Mode:", "property": "mode", "values": ["invert", "reset", "extractor"]},
        {"type": "text", "name": "Tags In:", "property": "tags"},
        {"type": "text", "name": "Target Tag:", "property": "target_tag"}
    ]
)

system_node(
    "Functions", "Animation", node_kind="data", color="#8B5CF6",
    inputs=["Frames / Text", "Step ms", "Start Time", "End Time"],
    outputs=["Shape", "Frame", "Frames List"],
    properties={
        "mode": "fbf",
        "frames": "",
        "step_ms": "41.7",
        "start_time": "",
        "end_time": "",
        "alpha_tag": r"\alpha",
        "order": "sequential",
        "var_name": "an"
    },
    widgets=[]
)

system_node(
    "Time", "Retime", node_kind="data", color="#2563EB",
    inputs=["Tags or \\t", "Offset In (ms)", "Offset Out (ms)", "Accel"],
    outputs=[r"\t Out", "Start Time", "End Time", "Duration"],
    properties={
        "phase": "syl",
        "tags": "",
        "offset_in": "0",
        "offset_out": "0",
        "accel": "1.0",
        "custom_start": "0",
        "custom_end": "0"
    },
    widgets=[
        {"type": "combo", "name": "Mode:", "property": "phase", "values": [
            "syl", "presyl", "postsyl", "line", "preline", "postline",
            "start2syl", "syl2end", "abs", "sylpct"
        ]},
        {"type": "text", "name": "Tags or \\t:", "property": "tags"},
        {"type": "text", "name": "Offset In (ms):", "property": "offset_in"},
        {"type": "text", "name": "Offset Out (ms):", "property": "offset_out"},
        {"type": "text", "name": "Accel:", "property": "accel"}
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
        "rhythm_pattern": "", "mode": "wave", "order_mode": "sequential"
    },
    widgets=[]
)

system_node(
    "Functions", "Glitter", node_kind="data", color="#8B5CF6",
    inputs=["Start Time", "End Time", "Density", "In 1"],
    outputs=["List", "TAG 1"],
    properties={
        "expandable": True,
        "start_time": "0",
        "end_time": "fx.dur",
        "density": "1.0",
        "mode": "flashes",
        "seed": "0",
        "tags": [r"\fscx"],
        "mins": ["150"],
        "maxs": ["250"]
    },
    widgets=[]
)

system_node(
    "Basics", "Once", node_kind="data", color="#6366F1",
    inputs=["In"],
    outputs=["Out"],
    properties={
        "mode": "line",
        "iterator": "j"
    },
    widgets=[]
)

system_node(
    "Basics", "Only", node_kind="data", color="#10B981",
    inputs=["True", "False"],
    outputs=["Out"],
    properties={
        "condition": "True",
        "mode": "select"
    },
    widgets=[]
)

system_node(
    "Audio", "Modulator", node_kind="data", color="#0284C7",
    inputs=["Audio Path", "Tag", "Min Val", "Max Val", "Gain", "Step ms", "Smoothing", "Start Time", "End Time"],
    outputs=["Tags Out", "Current Value", "Values Array", "Average RMS"],
    properties={
        "audio_path": "",
        "tag_name": "fscy",
        "min_val": "100",
        "max_val": "160",
        "gain": "1.0",
        "step_ms": "41.7",
        "smoothing": "0.2",
        "mode": "rms",
        "min_hz": "20",
        "max_hz": "250",
        "start_time": "",
        "end_time": ""
    },
    widgets=[]
)

system_node(
    "Audio", "Waveform", node_kind="data", color="#0284C7",
    inputs=["Audio Path", "Width", "Height", "Samples", "Gain", "Thickness", "Scale", "Start Time", "End Time"],
    outputs=["Shape Out", "\\pos Tag", "X Array", "Y Array", "Bands Array"],
    properties={
        "audio_path": "",
        "mode": "oscilloscope",
        "width": "400",
        "height": "60",
        "samples": "32",
        "gain": "1.0",
        "thickness": "2",
        "scale": "1.0",
        "min_hz": "20",
        "max_hz": "16000",
        "start_time": "",
        "end_time": ""
    },
    widgets=[]
)