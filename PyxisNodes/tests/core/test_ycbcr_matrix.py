# -*- coding: utf-8 -*-
"""Unit tests for YCbCr Matrix parsing and metadata propagation in Pyxis Effector.

Validates that ASSParser extracts YCbCr Matrix headers accurately from [Script Info],
preserves defaults when omitted, and maintains full backwards compatibility with
the ASSParseResult tuple structure.
"""

import os
import sys
import tempfile
import unittest

# Ensure src/ is on sys.path
_SRC_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "Version en desarrollo", "PyxisNodes", "src"))
if _SRC_DIR not in sys.path:
    sys.path.insert(0, _SRC_DIR)

from ass_parser import ASSParser, ASSParseResult


class TestYCbCrMatrixParsing(unittest.TestCase):
    """Test suite for YCbCr Matrix header tokenisation and extraction."""

    def _create_temp_ass(self, script_info_lines: list[str]) -> str:
        """Helper to create a temporary .ass file with given Script Info lines."""
        content = "[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\n"
        for l in script_info_lines:
            content += l + "\n"
        content += "\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n"
        content += "Style: Default,Arial,50,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,0,2,10,10,10,1\n"
        content += "\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n"
        content += "Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,Test line\n"

        fd, path = tempfile.mkstemp(suffix=".ass", text=True)
        with open(fd, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def test_ycbcr_matrix_tv709(self):
        """Verify parsing of standard TV.709 matrix."""
        path = self._create_temp_ass(["YCbCr Matrix: TV.709"])
        try:
            parsed = ASSParser.read_file(path)
            self.assertEqual(parsed.ycbcr_matrix, "TV.709")
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_ycbcr_matrix_tv601(self):
        """Verify parsing of SD TV.601 matrix."""
        path = self._create_temp_ass(["YCbCr Matrix: TV.601"])
        try:
            parsed = ASSParser.read_file(path)
            self.assertEqual(parsed.ycbcr_matrix, "TV.601")
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_ycbcr_matrix_pc709(self):
        """Verify parsing of full-range PC.709 matrix."""
        path = self._create_temp_ass(["YCbCr Matrix: PC.709"])
        try:
            parsed = ASSParser.read_file(path)
            self.assertEqual(parsed.ycbcr_matrix, "PC.709")
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_ycbcr_matrix_none(self):
        """Verify parsing of explicit None matrix."""
        path = self._create_temp_ass(["YCbCr Matrix: None"])
        try:
            parsed = ASSParser.read_file(path)
            self.assertEqual(parsed.ycbcr_matrix, "None")
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_ycbcr_matrix_case_insensitivity(self):
        """Verify case insensitivity when reading the header key."""
        path = self._create_temp_ass(["ycbcr matrix: tv.709"])
        try:
            parsed = ASSParser.read_file(path)
            self.assertEqual(parsed.ycbcr_matrix, "tv.709")
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_ycbcr_matrix_default_when_missing(self):
        """Verify default fallback to 'None' when header is omitted."""
        path = self._create_temp_ass([])
        try:
            parsed = ASSParser.read_file(path)
            self.assertEqual(parsed.ycbcr_matrix, "None")
        finally:
            if os.path.exists(path):
                os.remove(path)

    def test_tuple_unpacking_compatibility(self):
        """Ensure 5-tuple unpacking contract remains unbroken."""
        path = self._create_temp_ass(["YCbCr Matrix: TV.709"])
        try:
            parsed = ASSParser.read_file(path)
            styles, dialogues, res_x, res_y, frame_dur = parsed
            self.assertEqual(res_x, 1920)
            self.assertEqual(res_y, 1080)
            self.assertEqual(len(dialogues), 1)
            self.assertEqual(parsed.ycbcr_matrix, "TV.709")
        finally:
            if os.path.exists(path):
                os.remove(path)


if __name__ == "__main__":
    unittest.main()
