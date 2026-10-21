# -*- coding: utf-8 -*-
# Pyxis Effector — Infrastructure Repositories (File Subtitle Repository)
# Copyright (C) 2026 Pyxis Effector contributors
# Licensed under GNU General Public License v3

import os
import tempfile
from typing import List, Optional

from ...domain.entities.subtitle import SubtitleScript
from ...domain.repositories.i_subtitle_repository import ISubtitleRepository
from ...application.mappers.subtitle_mapper import SubtitleMapper
from ..engine.ass_parser import ASSParser


class FileSubtitleRepository(ISubtitleRepository):
    """Concrete repository that reads and writes ASS subtitle files using ASSParser."""

    def read_from_file(self, file_path: str) -> SubtitleScript:
        if not os.path.isfile(file_path):
            raise FileNotFoundError(f"Subtitle file not found: {file_path}")

        parsed_data = ASSParser.read_file(file_path)
        audio_src = getattr(parsed_data, "audio_file", "")
        video_src = getattr(parsed_data, "video_file", "")
        return SubtitleMapper.to_domain(parsed_data, audio_file=audio_src, video_file=video_src)

    def read_from_text(self, text_content: str) -> SubtitleScript:
        tmp_path = None
        try:
            with tempfile.NamedTemporaryFile("w", suffix=".ass", delete=False, encoding="utf-8") as tmp:
                tmp.write(text_content)
                tmp_path = tmp.name
            return self.read_from_file(tmp_path)
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except OSError:
                    pass

    def write_to_file(
        self,
        file_path: str,
        generated_lines: List[str],
        used_indices: Optional[List[int]] = None,
    ) -> None:
        os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            if used_indices:
                idx_str = ",".join(str(x) for x in sorted(used_indices))
                f.write(f"#PYXIS_USED_IDX: {idx_str}\n")
            f.writelines(generated_lines)
            f.flush()
