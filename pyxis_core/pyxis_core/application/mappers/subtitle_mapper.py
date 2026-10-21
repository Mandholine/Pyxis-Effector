# -*- coding: utf-8 -*-
# Pyxis Effector — Application Mappers (Subtitles)
# Copyright (C) 2026 Pyxis Effector contributors
# Licensed under GNU General Public License v3

from typing import Any, Dict, List, Tuple
from ...domain.entities.subtitle import SubtitleScript, DialogueLine, SubtitleStyle
from ...domain.value_objects.resolution import Resolution
from ...domain.value_objects.timecode import Timecode


class SubtitleMapper:
    """Maps between raw ASS parser structures and SubtitleScript domain entities."""

    @staticmethod
    def to_domain(raw_tuple: Tuple[Any, Any, int, int, float], audio_file: str = "", video_file: str = "") -> SubtitleScript:
        """Converts raw (styles_dict, dialogues_list, res_x, res_y, frame_dur) into SubtitleScript."""
        raw_styles, raw_dialogues, res_x, res_y, frame_duration = raw_tuple

        # Resolution VO
        resolution = Resolution(
            play_res_x=int(res_x or 1920),
            play_res_y=int(res_y or 1080),
            frame_duration=float(frame_duration or 41.7083),
        )

        # Styles Map
        domain_styles: Dict[str, SubtitleStyle] = {}
        if isinstance(raw_styles, dict):
            for name, s_dict in raw_styles.items():
                if isinstance(s_dict, dict):
                    domain_styles[name] = SubtitleStyle(
                        name=name,
                        fontname=s_dict.get("fontname", "Arial"),
                        fontsize=float(s_dict.get("fontsize", 48.0)),
                        primary_color=s_dict.get("color1", "&H00FFFFFF"),
                        secondary_color=s_dict.get("color2", "&H000000FF"),
                        outline_color=s_dict.get("color3", "&H00000000"),
                        back_color=s_dict.get("color4", "&H00000000"),
                        bold=bool(s_dict.get("bold", False)),
                        italic=bool(s_dict.get("italic", False)),
                        underline=bool(s_dict.get("underline", False)),
                        strikeout=bool(s_dict.get("strikeout", False)),
                        scale_x=float(s_dict.get("scale_x", 100.0)),
                        scale_y=float(s_dict.get("scale_y", 100.0)),
                        spacing=float(s_dict.get("spacing", 0.0)),
                        angle=float(s_dict.get("angle", 0.0)),
                        border_style=int(s_dict.get("border_style", 1)),
                        outline=float(s_dict.get("outline", 2.0)),
                        shadow=float(s_dict.get("shadow", 0.0)),
                        alignment=int(s_dict.get("alignment", 2)),
                        margin_l=int(s_dict.get("margin_l", 10)),
                        margin_r=int(s_dict.get("margin_r", 10)),
                        margin_v=int(s_dict.get("margin_v", 10)),
                        encoding=int(s_dict.get("encoding", 1)),
                    )

        # Dialogues List
        domain_dialogues: List[DialogueLine] = []
        if isinstance(raw_dialogues, list):
            for i, d in enumerate(raw_dialogues):
                if isinstance(d, dict):
                    # Could have start_time as int ms or str
                    start_val = d.get("start", 0)
                    end_val = d.get("end", 0)
                    start_tc = Timecode(int(start_val)) if isinstance(start_val, (int, float)) else Timecode.from_ass(str(start_val))
                    end_tc = Timecode(int(end_val)) if isinstance(end_val, (int, float)) else Timecode.from_ass(str(end_val))

                    domain_dialogues.append(
                        DialogueLine(
                            index=i,
                            layer=int(d.get("layer", 0)),
                            start_time=start_tc,
                            end_time=end_tc,
                            style=str(d.get("style", "Default")),
                            actor=str(d.get("actor", "")),
                            margin_l=int(d.get("margin_l", 0)),
                            margin_r=int(d.get("margin_r", 0)),
                            margin_v=int(d.get("margin_v", 0)),
                            effect=str(d.get("effect", "")),
                            text=str(d.get("text", "")),
                            is_comment=bool(d.get("is_comment", False) or d.get("comment", False)),
                        )
                    )

        return SubtitleScript(
            resolution=resolution,
            audio_file=audio_file,
            video_file=video_file,
            styles=domain_styles,
            dialogues=domain_dialogues,
        )

    @staticmethod
    def to_engine_structures(script: SubtitleScript) -> Tuple[Dict[str, Any], List[Dict[str, Any]], int, int, float]:
        """Converts SubtitleScript back to structures expected by GraphEngine."""
        raw_styles: Dict[str, Any] = {}
        for name, st in script.styles.items():
            raw_styles[name] = {
                "fontname": st.fontname,
                "fontsize": st.fontsize,
                "color1": st.primary_color,
                "color2": st.secondary_color,
                "color3": st.outline_color,
                "color4": st.back_color,
                "bold": st.bold,
                "italic": st.italic,
                "underline": st.underline,
                "strikeout": st.strikeout,
                "scale_x": st.scale_x,
                "scale_y": st.scale_y,
                "spacing": st.spacing,
                "angle": st.angle,
                "border_style": st.border_style,
                "outline": st.outline,
                "shadow": st.shadow,
                "alignment": st.alignment,
                "margin_l": st.margin_l,
                "margin_r": st.margin_r,
                "margin_v": st.margin_v,
                "encoding": st.encoding,
            }

        raw_dialogues: List[Dict[str, Any]] = []
        for d in script.dialogues:
            raw_dialogues.append({
                "layer": d.layer,
                "start": d.start_time.milliseconds,
                "end": d.end_time.milliseconds,
                "style": d.style,
                "actor": d.actor,
                "margin_l": d.margin_l,
                "margin_r": d.margin_r,
                "margin_v": d.margin_v,
                "effect": d.effect,
                "text": d.text,
                "comment": d.is_comment,
            })

        return (
            raw_styles,
            raw_dialogues,
            script.resolution.play_res_x,
            script.resolution.play_res_y,
            script.resolution.frame_duration,
        )
