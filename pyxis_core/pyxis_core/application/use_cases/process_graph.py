# -*- coding: utf-8 -*-
# Pyxis Effector — Application Use Cases (Process Graph)
# Copyright (C) 2026 Pyxis Effector contributors
# Licensed under GNU General Public License v3

import time
import traceback
from typing import Callable, Optional

from ...domain.repositories.i_subtitle_repository import ISubtitleRepository
from ..dtos.process_dto import (
    ProcessGraphRequestDTO,
    ProcessGraphResponseDTO,
    ProgressEventDTO,
)
from ..mappers.graph_mapper import GraphMapper
from ..mappers.subtitle_mapper import SubtitleMapper


class ProcessGraphUseCase:
    """Use case to process a subtitle script against a node graph effect."""

    def __init__(self, subtitle_repo: ISubtitleRepository):
        self.subtitle_repo = subtitle_repo
        self._active_engine = None

    def abort(self) -> None:
        """Signals cancellation to the currently running engine."""
        if self._active_engine is not None:
            setattr(self._active_engine, "is_cancelled", True)

    def execute(
        self,
        request: ProcessGraphRequestDTO,
        progress_callback: Optional[Callable[[ProgressEventDTO], None]] = None,
        cancel_checker: Optional[Callable[[], bool]] = None,
    ) -> ProcessGraphResponseDTO:
        start_time = time.perf_counter()

        def _emit_progress(percent: int, phase: str):
            if progress_callback:
                try:
                    progress_callback(ProgressEventDTO(percent=percent, phase=phase))
                except Exception:
                    pass

        try:
            # 1. Parse SubtitleScript
            _emit_progress(5, "Loading subtitle script...")
            if request.ass_path:
                script = self.subtitle_repo.read_from_file(request.ass_path)
            elif request.ass_content:
                script = self.subtitle_repo.read_from_text(request.ass_content)
            else:
                raise ValueError("Must provide either ass_path or ass_content in ProcessGraphRequestDTO")

            # 2. Normalize and Map Graph
            _emit_progress(10, "Parsing node graph...")
            node_graph = GraphMapper.to_domain(request.graph)
            graph_dict = GraphMapper.to_dict(node_graph)

            # 3. Audio preprocessing if required
            audio_source = (
                request.default_audio_source
                or script.audio_file
                or script.video_file
            )

            has_audio_node = any(
                any(k in n.node_type.lower() for k in ("audio", "waveform", "modulador"))
                for n in node_graph.nodes
            )

            if has_audio_node and audio_source:
                try:
                    _emit_progress(15, "Preparing audio source...")
                    from ..mappers.subtitle_mapper import SubtitleMapper
                    # Lazy import infrastructure engines for execution
                    from ...infrastructure.engine.audio_preprocessor import AudioPreprocessor
                    from ...infrastructure.engine.audio_engine import AudioEngine

                    wav_path = AudioPreprocessor.ensure_audio_wav(
                        audio_source,
                        progress_callback=lambda msg: _emit_progress(18, "Converting audio..."),
                    )
                    AudioEngine.load_wav(wav_path)
                    _emit_progress(25, "Audio loaded")
                except Exception as ae:
                    print(f"[Pyxis Audio Preprocessing Warning] {ae}", flush=True)

            # 4. Prepare data for GraphEngine
            raw_styles, raw_dialogues, res_x, res_y, frame_duration = SubtitleMapper.to_engine_structures(script)

            from ...infrastructure.engine.node_engine import GraphEngine

            engine = GraphEngine(
                graph_dict,
                res_x,
                res_y,
                frame_duration,
                default_audio_source=audio_source,
            )
            self._active_engine = engine

            def _check_cancel() -> bool:
                if cancel_checker and cancel_checker():
                    return True
                return bool(getattr(engine, "is_cancelled", False))

            def _engine_progress(data):
                if isinstance(data, dict):
                    pct = int(data.get("percent", 0))
                    phase = str(data.get("phase", "Processing..."))
                    _emit_progress(pct, phase)
                elif isinstance(data, (int, float)):
                    _emit_progress(int(data), "Processing nodes...")

            _emit_progress(30, "Generating effects...")
            generated_lines = engine.process(
                raw_dialogues,
                raw_styles,
                progress_callback=_engine_progress,
                check_cancel_callback=_check_cancel,
            )

            if _check_cancel():
                duration = time.perf_counter() - start_time
                return ProcessGraphResponseDTO(
                    success=False,
                    cancelled=True,
                    lines_count=0,
                    duration_seconds=duration,
                )

            used_indices = list(sorted(getattr(engine, "used_line_indices", [])))

            # 5. Output persistence
            if request.output_path:
                self.subtitle_repo.write_to_file(
                    request.output_path,
                    generated_lines,
                    used_indices=used_indices,
                )

            duration = time.perf_counter() - start_time
            _emit_progress(100, "Done")

            return ProcessGraphResponseDTO(
                success=True,
                lines_count=len(generated_lines),
                duration_seconds=duration,
                lines=generated_lines,
                used_indices=used_indices,
                cancelled=False,
            )

        except Exception as err:
            duration = time.perf_counter() - start_time
            err_trace = traceback.format_exc()
            return ProcessGraphResponseDTO(
                success=False,
                lines_count=0,
                duration_seconds=duration,
                cancelled=False,
                error=err_trace,
            )
        finally:
            self._active_engine = None
