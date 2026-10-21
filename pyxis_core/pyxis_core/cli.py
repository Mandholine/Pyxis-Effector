# -*- coding: utf-8 -*-
# Pyxis Effector — Core Subtitle & Node Engine Library
# Copyright (C) 2026 Pyxis Effector contributors
# Licensed under GNU General Public License v3

"""Command Line Interface (CLI) for pyxis-core."""

import argparse
import json
import os
import sys
from typing import Optional

from . import PyxisCore, __version__
from .infrastructure.adapters import TelemetryAdapter


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="pyxis-core",
        description="Pyxis Core — High-performance node-based subtitle effector engine",
    )
    parser.add_argument(
        "-v", "--version", action="version", version=f"pyxis-core {__version__}"
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Command: process
    proc_parser = subparsers.add_parser("process", help="Process an ASS subtitle script using a node graph")
    proc_parser.add_argument("-g", "--graph", required=True, help="Path to effect graph JSON file")
    proc_parser.add_argument("-a", "--ass", required=True, help="Path to input ASS subtitle file")
    proc_parser.add_argument("-o", "--output", help="Path to output ASS subtitle file")
    proc_parser.add_argument("--audio", help="Optional audio source path for waveform/beat analysis")

    # Command: validate
    val_parser = subparsers.add_parser("validate", help="Validate a node graph effect JSON file")
    val_parser.add_argument("-g", "--graph", required=True, help="Path to effect graph JSON file to validate")

    # Command: telemetry
    tel_parser = subparsers.add_parser("telemetry", help="Analyze ASS subtitle performance and dropped frames")
    tel_parser.add_argument("-a", "--ass", required=True, help="Path to ASS subtitle file")
    tel_parser.add_argument("--fps", type=float, default=23.976, help="Target frame rate (default: 23.976)")
    tel_parser.add_argument("-o", "--output", help="Path to save JSON telemetry analysis report")

    # Command: info
    subparsers.add_parser("info", help="Display system, architecture, and engine information")

    return parser


def _cmd_process(args) -> int:
    if not os.path.isfile(args.graph):
        sys.stderr.write(f"Error: Graph file not found: {args.graph}\n")
        return 1
    if not os.path.isfile(args.ass):
        sys.stderr.write(f"Error: ASS subtitle file not found: {args.ass}\n")
        return 1

    core = PyxisCore()

    def on_progress(p):
        sys.stdout.write(f"\r[{p.percent:3d}%] {p.phase}")
        sys.stdout.flush()

    response = core.process(
        graph=args.graph,
        ass_path=args.ass,
        output_path=args.output,
        progress_callback=on_progress,
        default_audio_source=args.audio,
    )
    sys.stdout.write("\n")

    if response.success:
        print(f"Success! Generated {response.lines_count} lines in {response.duration_seconds:.2f}s.")
        if response.output_path:
            print(f"Output saved to: {response.output_path}")
        return 0
    else:
        sys.stderr.write(f"Processing failed: {response.error}\n")
        return 2


def _cmd_validate(args) -> int:
    if not os.path.isfile(args.graph):
        sys.stderr.write(f"Error: Graph file not found: {args.graph}\n")
        return 1

    try:
        with open(args.graph, "r", encoding="utf-8") as f:
            graph_data = json.load(f)
    except Exception as e:
        sys.stderr.write(f"Error reading JSON graph: {e}\n")
        return 1

    core = PyxisCore()
    result = core.validate(graph_data)

    if result.valid:
        print(f"Graph '{args.graph}' is VALID (Nodes: {result.node_count}, Warnings: {len(result.warnings)})")
        for w in result.warnings:
            print(f"  [Warning] {w}")
        return 0
    else:
        sys.stderr.write(f"Graph '{args.graph}' is INVALID with {len(result.errors)} errors:\n")
        for err in result.errors:
            sys.stderr.write(f"  - {err}\n")
        return 2


def _cmd_telemetry(args) -> int:
    if not os.path.isfile(args.ass):
        sys.stderr.write(f"Error: ASS subtitle file not found: {args.ass}\n")
        return 1

    print(f"Analyzing ASS rendering telemetry at {args.fps} FPS: {args.ass}")
    report = TelemetryAdapter.analyze_file(args.ass, fps=args.fps)

    summary = report.get("summary", {})
    print("-" * 50)
    print(f"Total Frames:          {summary.get('total_frames', 'N/A')}")
    print(f"Dropped Frames:        {summary.get('dropped_frames_count', 0)}")
    print(f"Max Render Time:       {summary.get('max_render_time_ms', 0):.2f} ms")
    print(f"Avg Render Time:       {summary.get('avg_render_time_ms', 0):.2f} ms")
    print(f"Total Duration:        {summary.get('duration_seconds', 0):.2f} s")
    print("-" * 50)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=2)
        print(f"Telemetry report written to: {args.output}")

    return 0


def _cmd_info() -> int:
    from .infrastructure.engine.system.paths import BIN_DIR, DATA_DIR, get_bin_path

    print("=" * 60)
    print(f"Pyxis Core — Version {__version__}")
    print("=" * 60)
    print("Clean Architecture Layers:")
    print("  • Domain:         Entities, Value Objects, Repository Interfaces")
    print("  • Application:    Use Cases (Process, Validate, Templates), DTOs, Mappers")
    print("  • Infrastructure: Subtitle/Template Repos, Engine Subsystems, Adapters")
    print()
    print("Engine Directories:")
    print(f"  • Data directory:    {DATA_DIR}")
    print(f"  • Bin directory:     {BIN_DIR}")
    print()
    print("External Native Tool Resolution:")
    for tool in ("img2ass", "potrace", "libass_profiler", "ffmpeg"):
        path = get_bin_path(tool)
        status = "Found" if path and os.path.exists(path) else "Not found (Fallback to PATH/System)"
        print(f"  • {tool:18s}: {status} ({path})")
    print("=" * 60)
    return 0


def main(argv=None) -> int:
    """Main CLI entry point for pyxis-core."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "process":
        return _cmd_process(args)
    elif args.command == "validate":
        return _cmd_validate(args)
    elif args.command == "telemetry":
        return _cmd_telemetry(args)
    elif args.command == "info":
        return _cmd_info()

    return 0


if __name__ == "__main__":
    sys.exit(main())
