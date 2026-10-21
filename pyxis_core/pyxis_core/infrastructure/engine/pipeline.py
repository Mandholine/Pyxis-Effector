# -*- coding: utf-8 -*-
# Pyxis Effector — Core Execution Pipeline
# Copyright (C) 2026 Pyxis Effector contributors
# Licensed under GNU General Public License v3

"""High-level pipeline and orchestrator for executing Pyxis node graphs on ASS subtitles."""

from dataclasses import dataclass, field
import json
import os
import tempfile
import time
import traceback
from typing import Any, Callable, Dict, List, Optional, Union

from .ass_parser import ASSParser
from .audio_engine import AudioEngine
from .audio_preprocessor import AudioPreprocessor
from .node_engine import GraphEngine


@dataclass
class ProcessingResult:
    """Standardized result returned by PyxisPipeline execution."""

    success: bool
    lines: List[str] = field(default_factory=list)
    lines_count: int = 0
    used_indices: List[int] = field(default_factory=list)
    cancelled: bool = False
    error: Optional[str] = None
    duration_seconds: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "lines_count": self.lines_count,
            "used_indices": self.used_indices,
            "cancelled": self.cancelled,
            "error": self.error,
            "duration_seconds": self.duration_seconds,
        }


class PyxisPipeline:
    """Orchestrator to process subtitle files with Pyxis node effect graphs.

    Decoupled from UI frameworks, desktop windows, or specific IPC servers.
    Can be called directly from CLI, FastAPI background workers, or scripts.
    """

    def __init__(self, default_audio_source: Optional[str] = None):
        self.default_audio_source = default_audio_source
        self._active_engine: Optional[GraphEngine] = None

    @property
    def active_engine(self) -> Optional[GraphEngine]:
        return self._active_engine

    def abort(self) -> None:
        """Signals cancellation to the currently running engine."""
        if self._active_engine is not None:
            setattr(self._active_engine, "is_cancelled", True)

    def process(
        self,
        ass_input: Union[str, os.PathLike],
        graph_data: Union[Dict[str, Any], str, os.PathLike],
        progress_callback: Optional[Callable[[Dict[str, Any]], None]] = None,
        cancel_checker: Optional[Callable[[], bool]] = None,
        output_path: Optional[Union[str, os.PathLike]] = None,
    ) -> ProcessingResult:
        """Executes a node graph against an ASS subtitle input.

        Args:
            ass_input: Path to an ASS file or raw ASS subtitle text.
            graph_data: Dictionary representing the node graph, JSON string, or path to a JSON file.
            progress_callback: Optional callback called with `{'percent': int, 'phase': str}`.
            cancel_checker: Optional callback returning True if execution should abort.
            output_path: Optional path where generated ASS lines will be saved.

        Returns:
            ProcessingResult containing status, lines, and metrics.
        """
        start_time = time.perf_counter()

        def _report(percent: int, phase: str = "Processing..."):
            if progress_callback:
                try:
                    progress_callback({"percent": percent, "phase": phase})
                except Exception:
                    pass

        # 1. Normalize graph_data
        if isinstance(graph_data, (str, os.PathLike)):
            if os.path.isfile(graph_data):
                with open(graph_data, "r", encoding="utf-8") as f:
                    graph_dict = json.load(f)
            else:
                graph_dict = json.loads(str(graph_data))
        elif isinstance(graph_data, dict):
            graph_dict = graph_data
        else:
            raise ValueError(f"Unsupported graph_data format: {type(graph_data)}")

        # 2. Parse ASS input
        temp_ass_path = None
        try:
            if isinstance(ass_input, (str, os.PathLike)) and os.path.isfile(ass_input):
                parsed_ass = ASSParser.read_file(str(ass_input))
            elif isinstance(ass_input, str):
                # Raw ASS content provided; write to a temporary file for ASSParser
                with tempfile.NamedTemporaryFile("w", suffix=".ass", delete=False, encoding="utf-8") as tmp:
                    tmp.write(ass_input)
                    temp_ass_path = tmp.name
                parsed_ass = ASSParser.read_file(temp_ass_path)
            else:
                raise ValueError("ass_input must be an existing file path or ASS text content")

            styles, dialogues, res_x, res_y, frame_duration = parsed_ass
            resolved_audio_source = (
                self.default_audio_source
                or getattr(parsed_ass, "audio_file", "")
                or getattr(parsed_ass, "video_file", "")
            )

            # 3. Pre-load audio if required by any node in the graph
            for node in graph_dict.get("nodes", []):
                n_type = str(node.get("type", ""))
                if any(k in n_type.lower() for k in ("audio", "waveform", "modulador")):
                    node_audio = str(node.get("properties", {}).get("audio_path", "")).strip()
                    src_to_check = node_audio if node_audio else resolved_audio_source
                    if src_to_check:
                        try:
                            _report(5, "Preparing audio source...")
                            wav_path = AudioPreprocessor.ensure_audio_wav(
                                src_to_check,
                                progress_callback=lambda msg: _report(12, "Converting audio..."),
                            )
                            _report(18, "Loading waveform...")
                            AudioEngine.load_wav(wav_path)
                            _report(24, "Audio ready")
                        except Exception as ae:
                            print(f"[Pyxis Audio Preprocessor Warning] {ae}", flush=True)

            # 4. Instantiate GraphEngine
            engine = GraphEngine(
                graph_dict,
                res_x,
                res_y,
                frame_duration,
                default_audio_source=resolved_audio_source,
            )
            self._active_engine = engine

            def _check_cancel() -> bool:
                if cancel_checker and cancel_checker():
                    return True
                return bool(getattr(engine, "is_cancelled", False))

            def _engine_progress_adapter(data):
                if isinstance(data, dict):
                    if progress_callback:
                        progress_callback(data)
                elif isinstance(data, (int, float)):
                    _report(int(data), "Processing nodes...")

            # 5. Execute processing
            generated_lines = engine.process(
                dialogues,
                styles,
                progress_callback=_engine_progress_adapter,
                check_cancel_callback=_check_cancel,
            )

            # Check if cancelled
            if _check_cancel():
                duration = time.perf_counter() - start_time
                return ProcessingResult(
                    success=False,
                    cancelled=True,
                    lines=[],
                    lines_count=0,
                    duration_seconds=duration,
                )

            used_indices = list(sorted(getattr(engine, "used_line_indices", [])))

            # 6. Optionally write to output file
            if output_path:
                os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
                with open(output_path, "w", encoding="utf-8") as out_f:
                    if used_indices:
                        idx_str = ",".join(str(x) for x in used_indices)
                        out_f.write(f"#PYXIS_USED_IDX: {idx_str}\n")
                    out_f.writelines(generated_lines)
                    out_f.flush()

            duration = time.perf_counter() - start_time
            return ProcessingResult(
                success=True,
                lines=generated_lines,
                lines_count=len(generated_lines),
                used_indices=used_indices,
                cancelled=False,
                duration_seconds=duration,
            )

        except Exception as err:
            duration = time.perf_counter() - start_time
            err_trace = traceback.format_exc()
            return ProcessingResult(
                success=False,
                lines=[],
                lines_count=0,
                cancelled=False,
                error=err_trace,
                duration_seconds=duration,
            )
        finally:
            self._active_engine = None
            if temp_ass_path and os.path.exists(temp_ass_path):
                try:
                    os.remove(temp_ass_path)
                except OSError:
                    pass
