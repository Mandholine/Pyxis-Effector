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
# For any question you can visit: https://discord.gg/fsxRESeQZN

"""Acoustic analysis and audio modulation nodes."""

import math
import os
import re
from typing import Any, Dict, List, Optional, Tuple, Union

from audio_engine import AudioData, AudioEngine
from audio_preprocessor import AudioPreprocessor
from decorators import pyxis_node


def _is_alpha_tag(tag_name: str) -> bool:
    """Determine whether an ASS tag corresponds to transparency or alpha (\\alpha, \\1a, \\2a, \\3a, \\4a)."""
    t = str(tag_name or "").strip().lower().lstrip('\\')
    return t in ["alpha", "1a", "2a", "3a", "4a", "a", "alpha1", "alpha2", "alpha3", "alpha4"]


def _is_color_tag(tag_name: str) -> bool:
    """Determine whether an ASS tag corresponds to colour (\\c, \\1c, \\2c, \\3c, \\4c)."""
    t = str(tag_name or "").strip().lower().lstrip('\\')
    return t in ["c", "1c", "2c", "3c", "4c", "color", "colour", "primary_color", "secondary_color", "outline_color", "shadow_color"]


def _parse_color_list(val_min: Any, val_max: Any) -> List[Tuple[int, int, int]]:
    """Parse a multi-colour palette from min_val and max_val supporting ASS hex (&HBBGGRR&), Web hex (#RRGGBB), or lists."""
    from utils import parse_color_to_rgb
    raw_list: List[str] = []

    def _extract_from(val):
        if isinstance(val, (list, tuple)):
            for item in val:
                _extract_from(item)
        elif isinstance(val, str):
            v_clean = val.strip()
            if ',' in v_clean or ';' in v_clean:
                delimiter = ',' if ',' in v_clean else ';'
                for part in v_clean.split(delimiter):
                    p = part.strip()
                    if p:
                        raw_list.append(p)
            elif v_clean:
                raw_list.append(v_clean)
        elif val is not None:
            s = str(val).strip()
            if s:
                raw_list.append(s)

    _extract_from(val_min)
    _extract_from(val_max)

    if not raw_list:
        return [(255, 255, 255), (0, 0, 255)]

    if len(raw_list) == 1:
        c1 = parse_color_to_rgb(raw_list[0])
        return [(255, 255, 255), c1]

    return [parse_color_to_rgb(c) for c in raw_list]


def _interpolate_color_palette(colors: List[Tuple[int, int, int]], intensity: float) -> Tuple[int, int, int]:
    """Linearly interpolates across a multi-color palette [C0, C1, ... CN-1] based on intensity [0.0, 1.0]."""
    if not colors:
        return (255, 255, 255)
    if len(colors) == 1:
        return colors[0]

    w = max(0.0, min(1.0, float(intensity)))
    num_segments = len(colors) - 1
    pos = w * num_segments
    idx = min(num_segments - 1, max(0, int(math.floor(pos))))
    frac = pos - idx

    c1 = colors[idx]
    c2 = colors[idx + 1]

    r = int(round(c1[0] + frac * (c2[0] - c1[0])))
    g = int(round(c1[1] + frac * (c2[1] - c1[1])))
    b = int(round(c1[2] + frac * (c2[2] - c1[2])))
    return (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b)))


def parse_hex_or_num(val: Any, default: Optional[float] = 0.0) -> Optional[float]:
    """Converts hex strings (&HFF&, &HFF, 0xFF, #FF) or numeric values to float."""
    if val is None:
        return default
    s = str(val).strip()
    if not s:
        return default

    m = re.match(r"^&[hH]([0-9a-fA-F]+)&?$", s)
    if m:
        try:
            return float(int(m.group(1), 16))
        except Exception:
            pass

    m2 = re.match(r"^(?:0[xX]|#)([0-9a-fA-F]+)$", s)
    if m2:
        try:
            return float(int(m2.group(1), 16))
        except Exception:
            pass

    try:
        return float(s)
    except (ValueError, TypeError):
        return default


def _fmt_val_for_tag(v: float, tag_name: str = "") -> str:
    """Formats a value for ASS tags. If tag is alpha (1a, 2a, 3a, 4a, alpha), formats as &HAA&."""
    if _is_alpha_tag(tag_name):
        iv = max(0, min(255, int(round(v))))
        return f"&H{iv:02X}&"
    
    try:
        fv = float(v)
        if fv.is_integer():
            return str(int(fv))
        return f"{fv:.2f}".rstrip('0').rstrip('.')
    except Exception:
        return str(v)


def _fmt_val(v: float) -> str:
    """Formats a numeric value for ASS tags removing redundant decimals."""
    return _fmt_val_for_tag(v, "")


def _eval_val(val: Any, context: Optional[dict] = None, default: float = 0.0) -> float:
    """Evaluates a value that can be a number, hexadecimal (&HFF&), or mathematical expression."""
    if val is None or str(val).strip() == "":
        return default
    
    val_str = str(val).strip()
    direct_num = parse_hex_or_num(val_str, default=None)
    if direct_num is not None:
        return direct_num

    try:
        from node_engine import _eval_num_expr
        return float(_eval_num_expr(val_str, context, default))
    except Exception:
        return default


_RESOLVED_AUDIO_CACHE: Dict[str, AudioData] = {}


def clear_resolved_audio_cache():
    """Clears the audio path resolution cache."""
    _RESOLVED_AUDIO_CACHE.clear()


def resolve_audio_data(audio_path: Optional[str] = None, context: Optional[dict] = None) -> Optional[AudioData]:
    """Resolves and loads the AudioData buffer from the given path or Aegisub project with instant caching."""
    src = str(audio_path or "").strip()
    ctx = context if isinstance(context, dict) else {}
    if not src:
        src = str(
            ctx.get("default_audio_source", "") or
            ctx.get("real_audio_file", "") or
            ctx.get("real_video_file", "") or
            ctx.get("audio_file", "") or
            ctx.get("video_file", "")
        ).strip()

    if not src:
        return None

    clean_src = src.strip('"').strip("'")
    lower_s = clean_src.lower()
    if lower_s.startswith("?video:"):
        clean_src = clean_src[7:].strip()
    elif lower_s.startswith("?video"):
        clean_src = clean_src[6:].strip()
    elif lower_s.startswith("?audio:"):
        clean_src = clean_src[7:].strip()
    elif lower_s.startswith("?audio"):
        clean_src = clean_src[6:].strip()
    elif lower_s.startswith("dummy") or "dummy-audio" in lower_s or "silence?" in lower_s or lower_s.startswith("?dummy"):
        return None

    if not clean_src:
        return None

    if clean_src in _RESOLVED_AUDIO_CACHE:
        return _RESOLVED_AUDIO_CACHE[clean_src]

    resolved_path = None
    if os.path.isfile(clean_src):
        resolved_path = os.path.abspath(clean_src)
    else:
        script_file = ctx.get("script_file")
        if script_file and os.path.exists(script_file):
            candidate = os.path.join(os.path.dirname(os.path.abspath(script_file)), clean_src)
            if os.path.isfile(candidate):
                resolved_path = os.path.abspath(candidate)

        if not resolved_path:
            temp_ass = ctx.get("temp_ass")
            if temp_ass and os.path.exists(temp_ass):
                candidate = os.path.join(os.path.dirname(os.path.abspath(temp_ass)), clean_src)
                if os.path.isfile(candidate):
                    resolved_path = os.path.abspath(candidate)

        if not resolved_path:
            script_dir = ctx.get("script_dir")
            if script_dir and os.path.isdir(script_dir):
                candidate = os.path.join(script_dir, clean_src)
                if os.path.isfile(candidate):
                    resolved_path = os.path.abspath(candidate)

    if not resolved_path or not os.path.isfile(resolved_path):
        _RESOLVED_AUDIO_CACHE[clean_src] = None
        return None

    if resolved_path in _RESOLVED_AUDIO_CACHE:
        cached = _RESOLVED_AUDIO_CACHE[resolved_path]
        _RESOLVED_AUDIO_CACHE[clean_src] = cached
        return cached

    try:
        wav_path = AudioPreprocessor.ensure_audio_wav(resolved_path)
        audio_data = AudioEngine.load_wav(wav_path)
        _RESOLVED_AUDIO_CACHE[clean_src] = audio_data
        _RESOLVED_AUDIO_CACHE[resolved_path] = audio_data
        return audio_data
    except Exception as e:
        print(f"[Pyxis Audio Warning] Could not resolve audio '{resolved_path}': {e}", flush=True)
        _RESOLVED_AUDIO_CACHE[clean_src] = None
        _RESOLVED_AUDIO_CACHE[resolved_path] = None
        return None


def audio_rms(start_ms=None, end_ms=None, gain=1.0, audio_path=None, context=None, **kwargs) -> float:
    """Calculates RMS energy (0.0 to 1.0) in the specified time interval with optional gain."""
    ctx = context if isinstance(context, dict) else {}
    unit = ctx.get("active_unit")

    st = float(start_ms if start_ms is not None else ctx.get("unit_abs_start_time", ctx.get("fx_start_time", getattr(unit, "start_time", 0))))
    et = float(end_ms if end_ms is not None else ctx.get("unit_abs_end_time", ctx.get("fx_end_time", getattr(unit, "end_time", 0))))
    g = float(kwargs.get("gain", gain))

    audio_obj = resolve_audio_data(audio_path, ctx)
    if not audio_obj:
        return 0.0
    return round(audio_obj.get_rms(st, et, gain=g), 4)


def audio_peak(start_ms=None, end_ms=None, gain=1.0, audio_path=None, context=None, **kwargs) -> float:
    """Calculates absolute peak amplitude (0.0 to 1.0) in the specified time interval with optional gain."""
    ctx = context if isinstance(context, dict) else {}
    unit = ctx.get("active_unit")

    st = float(start_ms if start_ms is not None else ctx.get("unit_abs_start_time", ctx.get("fx_start_time", getattr(unit, "start_time", 0))))
    et = float(end_ms if end_ms is not None else ctx.get("unit_abs_end_time", ctx.get("fx_end_time", getattr(unit, "end_time", 0))))
    g = float(kwargs.get("gain", gain))

    audio_obj = resolve_audio_data(audio_path, ctx)
    if not audio_obj:
        return 0.0
    return round(audio_obj.get_peak(st, et, gain=g), 4)


def audio_band(start_ms=None, end_ms=None, min_hz=20.0, max_hz=250.0, gain=1.0, audio_path=None, context=None, **kwargs) -> float:
    """Calculates frequency energy (0.0 to 1.0) in the band [min_hz, max_hz] with optional gain."""
    ctx = context if isinstance(context, dict) else {}
    unit = ctx.get("active_unit")

    st = float(start_ms if start_ms is not None else ctx.get("unit_abs_start_time", ctx.get("fx_start_time", getattr(unit, "start_time", 0))))
    et = float(end_ms if end_ms is not None else ctx.get("unit_abs_end_time", ctx.get("fx_end_time", getattr(unit, "end_time", 0))))
    f_min = float(kwargs.get("min_hz", min_hz))
    f_max = float(kwargs.get("max_hz", max_hz))
    g = float(kwargs.get("gain", gain))

    audio_obj = resolve_audio_data(audio_path, ctx)
    if not audio_obj:
        return 0.0
    return round(audio_obj.get_band_weight(st, et, f_min, f_max, gain=g), 4)


def audio_fft(start_ms=None, end_ms=None, num_bands=16, min_hz=20.0, max_hz=16000.0, gain=1.0, audio_path=None, context=None, **kwargs) -> List[float]:
    """Calculates FFT spectrum divided into N logarithmic musical bands with optional gain."""
    ctx = context if isinstance(context, dict) else {}
    unit = ctx.get("active_unit")

    st = float(start_ms if start_ms is not None else ctx.get("unit_abs_start_time", ctx.get("fx_start_time", getattr(unit, "start_time", 0))))
    et = float(end_ms if end_ms is not None else ctx.get("unit_abs_end_time", ctx.get("fx_end_time", getattr(unit, "end_time", 0))))
    n_bands = int(kwargs.get("num_bands", num_bands))
    f_min = float(kwargs.get("min_hz", min_hz))
    f_max = float(kwargs.get("max_hz", max_hz))
    g = float(kwargs.get("gain", gain))

    audio_obj = resolve_audio_data(audio_path, ctx)
    if not audio_obj:
        return [0.0] * n_bands
    return [round(b, 4) for b in audio_obj.get_fft_bands(st, et, n_bands, f_min, f_max, gain=g)]


def audio_modulator_master(
    context: Optional[dict] = None,
    audio_path: str = "",
    tag_name: str = "fscy",
    min_val: Any = "100",
    max_val: Any = "160",
    gain: Any = "1.0",
    step_ms: Any = "41.7",
    smoothing: Any = "0.2",
    mode: str = "rms",
    min_hz: Any = "20",
    max_hz: Any = "250",
    start_time: Any = "",
    end_time: Any = "",
    output_slot_index: int = 0,
    **kwargs
) -> Union[str, float, List[float], List[str]]:
    """Generate continuous ASS \\t transitions, instantaneous values, or arrays driven by audio telemetry.

    Samples audio amplitude or spectral energy over the active unit interval or custom window,
    applies gain amplification, temporal smoothing, and maps the resulting intensity into
    numeric, alpha (&HAA&), or interpolated colour palettes (&HBBGGRR&).

    Args:
        context (Optional[dict]): Execution graph context providing active unit, timestamps, and audio source.
        audio_path (str): Explicit filesystem path to audio file, or empty string to use context defaults.
        tag_name (str): Target ASS override tag without leading slash (e.g. 'fscy', 'fscx', 'alpha', '1c').
        min_val (Any): Baseline value or colour corresponding to silence (intensity = 0.0).
        max_val (Any): Peak value or colour corresponding to maximum audio energy (intensity = 1.0).
        gain (Any): Linear amplitude multiplier applied prior to normalisation. Defaults to 1.0.
        step_ms (Any): Temporal sampling resolution in milliseconds (e.g. 41.7 ms for 24 fps).
        smoothing (Any): Exponential moving average smoothing factor [0.0, 0.95].
        mode (str): Acoustic analysis mode ('rms', 'peak', 'bass', 'mid', 'high', 'custom').
        min_hz (Any): Lower bound frequency in Hz for 'custom' bandpass mode.
        max_hz (Any): Upper bound frequency in Hz for 'custom' bandpass mode.
        start_time (Any): Optional explicit window start timestamp in milliseconds.
        end_time (Any): Optional explicit window end timestamp in milliseconds.
        output_slot_index (int): Output slot selector (0: continuous \\t string, 1: instantaneous value, 2: value list, 3: average RMS).
        **kwargs: Additional fallback keyword arguments.

    Returns:
        Union[str, float, List[float], List[str]]: Formatted ASS tag string, instantaneous numeric/colour value, or array of samples.
    """
    gain_val = kwargs.get("gain", gain)
    modo_val = kwargs.get("mode", mode)
    ctx = context if isinstance(context, dict) else {}
    unit = ctx.get("active_unit")
    line = ctx.get("line")

    fx_st = float(ctx.get("fx_start_time", ctx.get("effect_st", ctx.get("start_time", getattr(unit, "start_time", getattr(line, "start_time", 0.0))))))
    fx_et = float(ctx.get("fx_end_time", ctx.get("effect_et", ctx.get("end_time", getattr(unit, "end_time", getattr(line, "end_time", 0.0))))))
    fx_dur = max(1.0, float(ctx.get("fx_dur", ctx.get("effect_dur", ctx.get("dur", max(1.0, fx_et - fx_st))))))

    st_str = str(start_time if start_time is not None else "").strip()
    et_str = str(end_time if end_time is not None else "").strip()

    is_custom_time = bool(st_str or et_str)
    if is_custom_time:
        st = float(_eval_val(start_time, ctx, default=fx_st)) if st_str else fx_st
        et = float(_eval_val(end_time, ctx, default=fx_et)) if et_str else fx_et
    else:
        st = fx_st
        et = fx_et

    dur = max(1.0, et - st)

    raw_tag = str(tag_name or "fscy").strip().lstrip('\\')
    if not raw_tag:
        raw_tag = "fscy"

    is_alpha = _is_alpha_tag(raw_tag)
    is_color = _is_color_tag(raw_tag)

    if is_color:
        palette = _parse_color_list(min_val, max_val)
        v_min = 0.0
        v_max = 1.0
    else:
        v_min_default = 0.0 if is_alpha else 100.0
        v_max_default = 255.0 if is_alpha else 160.0

        v_min = _eval_val(min_val, ctx, default=v_min_default)
        v_max = _eval_val(max_val, ctx, default=v_max_default)

    gain_factor = max(0.0, _eval_val(gain_val, ctx, default=1.0))
    step = max(10.0, _eval_val(step_ms, ctx, default=41.7))
    smooth_factor = max(0.0, min(0.95, _eval_val(smoothing, ctx, default=0.2)))
    f_min = _eval_val(min_hz, ctx, default=20.0)
    f_max = _eval_val(max_hz, ctx, default=250.0)

    audio_obj = resolve_audio_data(audio_path, ctx)

    num_steps = max(1, int(math.ceil(dur / step)))
    raw_intensities: List[float] = []

    mode_clean = str(modo_val or "RMS").strip().lower()

    if audio_obj:
        for k in range(num_steps + 1):
            t0 = st + k * step
            t1 = min(et, t0 + step)
            if t0 >= et:
                t0 = max(st, et - 1)
                t1 = et

            if "peak" in mode_clean or "pico" in mode_clean:
                intensity = audio_obj.get_peak(t0, t1, gain=gain_factor)
            elif "bass" in mode_clean or "bajo" in mode_clean:
                intensity = audio_obj.get_band_weight(t0, t1, 20.0, 250.0, gain=gain_factor)
            elif "mid" in mode_clean or "medio" in mode_clean:
                intensity = audio_obj.get_band_weight(t0, t1, 250.0, 4000.0, gain=gain_factor)
            elif "high" in mode_clean or "agudo" in mode_clean:
                intensity = audio_obj.get_band_weight(t0, t1, 4000.0, 16000.0, gain=gain_factor)
            elif "custom" in mode_clean or "banda" in mode_clean or "personaliz" in mode_clean:
                intensity = audio_obj.get_band_weight(t0, t1, f_min, f_max, gain=gain_factor)
            else:
                intensity = audio_obj.get_rms(t0, t1, gain=gain_factor)

            raw_intensities.append(max(0.0, min(1.0, intensity)))
    else:
        raw_intensities = [0.0] * (num_steps + 1)

    if smooth_factor > 0 and len(raw_intensities) > 1:
        smoothed_intensities = [raw_intensities[0]]
        for i in range(1, len(raw_intensities)):
            prev = smoothed_intensities[-1]
            curr = raw_intensities[i]
            smoothed_intensities.append(prev + (1.0 - smooth_factor) * (curr - prev))
        intensities = smoothed_intensities
    else:
        intensities = raw_intensities

    if is_color:
        from utils import rgb_to_ass_color
        vals = [rgb_to_ass_color(*_interpolate_color_palette(palette, inten)) for inten in intensities]
    else:
        vals = [v_min + inten * (v_max - v_min) for inten in intensities]

    avg_rms = sum(raw_intensities) / len(raw_intensities) if raw_intensities else 0.0
    if output_slot_index == 3:
        return round(avg_rms, 4)

    if output_slot_index == 2:
        if is_color:
            return list(vals)
        if is_alpha:
            return [_fmt_val_for_tag(v, raw_tag) for v in vals]
        return [round(v, 2) for v in vals]

    if output_slot_index == 1:
        current_time = float(ctx.get("frame_time", ctx.get("fx_start_time", st)))
        rel_pos = max(0.0, min(1.0, (current_time - st) / dur))
        idx_float = rel_pos * (len(intensities) - 1)
        idx_low = int(math.floor(idx_float))
        idx_high = min(len(intensities) - 1, idx_low + 1)
        frac = idx_float - idx_low
        interp_inten = intensities[idx_low] + frac * (intensities[idx_high] - intensities[idx_low])
        if is_color:
            from utils import rgb_to_ass_color
            return rgb_to_ass_color(*_interpolate_color_palette(palette, interp_inten))
        interp_val = v_min + interp_inten * (v_max - v_min)
        if is_alpha:
            return _fmt_val_for_tag(interp_val, raw_tag)
        return round(interp_val, 2)

    tag_prefix = f"\\{raw_tag}"
    v0_str = vals[0] if is_color else _fmt_val_for_tag(vals[0], raw_tag)
    chain_parts = [f"{tag_prefix}{v0_str}"]

    rel_offset = (st - fx_st) if is_custom_time else 0.0

    for k in range(1, len(vals)):
        t_start = int(rel_offset + (k - 1) * step)
        t_end = int(min(rel_offset + dur, rel_offset + k * step))
        if t_end > t_start:
            v_curr_str = str(vals[k]) if is_color else _fmt_val_for_tag(vals[k], raw_tag)
            v_prev_str = str(vals[k - 1]) if is_color else _fmt_val_for_tag(vals[k - 1], raw_tag)
            if v_curr_str != v_prev_str or k == len(vals) - 1:
                t_s_clamped = max(0, t_start)
                t_e_clamped = max(1, t_end)
                chain_parts.append(f"\\t({t_s_clamped},{t_e_clamped},{tag_prefix}{v_curr_str})")

    return "".join(chain_parts)


def audio_waveform_master(
    context: Optional[dict] = None,
    audio_path: str = "",
    mode: str = "oscilloscope",
    width: Any = "400",
    height: Any = "60",
    samples: Any = "32",
    gain: Any = "1.0",
    thickness: Any = "2",
    min_hz: Any = "20",
    max_hz: Any = "16000",
    scale: Any = "1.0",
    start_time: Any = "",
    end_time: Any = "",
    output_slot_index: int = 0,
    **kwargs
) -> Union[str, List[float]]:
    """Generate ASSDraw vector waveforms or spectral visualisations driven by audio telemetry.

    Extracts time-domain audio samples or logarithmic FFT spectral bands and constructs
    vector geometries (oscilloscope, equalizer bars, radial circular meter, filled wave, or point clouds).

    Args:
        context (Optional[dict]): Execution graph context providing unit, timestamps, and position coordinates.
        audio_path (str): Explicit audio file path or empty string to use context defaults.
        mode (str): Visualisation mode ('oscilloscope', 'bars'/'fftbars', 'radial', 'filled'/'filledwave', 'points').
        width (Any): Bounding box canvas width in pixels.
        height (Any): Bounding box canvas height in pixels.
        samples (Any): Number of discrete points or equalizer bands to evaluate (4 to 512).
        gain (Any): Amplitude gain factor applied to audio samples.
        thickness (Any): Stroke thickness in pixels for oscilloscope and point radii.
        min_hz (Any): Lower frequency threshold in Hz for FFT spectrum analysis.
        max_hz (Any): Upper frequency threshold in Hz for FFT spectrum analysis.
        scale (Any): Vertical or radial amplitude scaling multiplier.
        start_time (Any): Optional explicit window start timestamp in milliseconds.
        end_time (Any): Optional explicit window end timestamp in milliseconds.
        output_slot_index (int): Output slot selector (0: ASSDraw shape string, 1: \\pos tag, 2: X-coords, 3: Y-coords, 4: raw values).
        **kwargs: Additional fallback keyword arguments.

    Returns:
        Union[str, List[float]]: ASSDraw drawing string, \\pos string, coordinate list, or raw sample array.
    """
    w_val = kwargs.get("width", kwargs.get("ancho", width))
    h_val = kwargs.get("height", kwargs.get("alto", height))
    samples_val = kwargs.get("samples", kwargs.get("muestras", samples))
    gain_val = kwargs.get("gain", kwargs.get("ganancia", gain))
    thick_val = kwargs.get("thickness", kwargs.get("grosor", thickness))
    scale_val = kwargs.get("scale", kwargs.get("escala", scale))
    modo_val = kwargs.get("mode", kwargs.get("modo", mode))

    ctx = context if isinstance(context, dict) else {}
    unit = ctx.get("active_unit")
    line = ctx.get("line")

    fx_st = float(ctx.get("frame_start_time", ctx.get("fx_start_time", ctx.get("effect_st", ctx.get("start_time", getattr(unit, "start_time", getattr(line, "start_time", 0.0)))))))
    fx_et = float(ctx.get("frame_end_time", ctx.get("fx_end_time", ctx.get("effect_et", ctx.get("end_time", getattr(unit, "end_time", getattr(line, "end_time", 0.0)))))))
    if fx_et <= fx_st:
        frame_dur = float(ctx.get("frame_dur", ctx.get("fd", 41.708)))
        fx_et = fx_st + max(10.0, frame_dur)

    st_str = str(start_time if start_time is not None else "").strip()
    et_str = str(end_time if end_time is not None else "").strip()

    if st_str or et_str:
        st = float(_eval_val(start_time, ctx, default=fx_st)) if st_str else fx_st
        et = float(_eval_val(end_time, ctx, default=fx_et)) if et_str else fx_et
    else:
        st = fx_st
        et = fx_et

    w = max(10.0, _eval_val(w_val, ctx, default=400.0))
    h = max(4.0, _eval_val(h_val, ctx, default=60.0))
    num_samples = max(4, min(512, int(_eval_val(samples_val, ctx, default=32.0))))
    gain_fac = max(0.01, _eval_val(gain_val, ctx, default=1.0))
    thick = max(1.0, _eval_val(thick_val, ctx, default=2.0))
    scale_fac = max(0.01, _eval_val(scale_val, ctx, default=1.0))
    f_min = _eval_val(min_hz, ctx, default=20.0)
    f_max = _eval_val(max_hz, ctx, default=16000.0)

    center_x = float(ctx.get("x", getattr(unit, "center", getattr(unit, "x", w / 2.0))))
    center_y = float(ctx.get("y", getattr(unit, "middle", getattr(unit, "y", h / 2.0))))

    audio_obj = resolve_audio_data(audio_path, ctx)

    mode_clean = str(modo_val or "oscilloscope").strip().lower()
    x_coords: List[float] = []
    y_coords: List[float] = []
    raw_values: List[float] = []

    if "barra" in mode_clean or "bar" in mode_clean or "fftbars" in mode_clean:
        if audio_obj:
            raw_values = audio_obj.get_fft_bands(st, et, num_bands=num_samples, min_hz=f_min, max_hz=f_max, gain=gain_fac)
        else:
            raw_values = [0.0] * num_samples

        bar_slot_w = w / float(num_samples)
        bar_w = max(1.0, bar_slot_w * 0.8)
        shape_parts: List[str] = []

        for i, val in enumerate(raw_values):
            x0 = round(i * bar_slot_w, 1)
            x1 = round(x0 + bar_w, 1)
            bar_h = round(max(1.0, min(h, val * h * scale_fac)), 1)
            y0 = round(h, 1)
            y1 = round(h - bar_h, 1)

            shape_parts.append(f"m {_fmt_val(x0)} {_fmt_val(y0)} l {_fmt_val(x0)} {_fmt_val(y1)} l {_fmt_val(x1)} {_fmt_val(y1)} l {_fmt_val(x1)} {_fmt_val(y0)}")
            x_coords.extend([x0, x0, x1, x1])
            y_coords.extend([y0, y1, y1, y0])

        shape_str = " ".join(shape_parts) + " "

    elif "radial" in mode_clean or "circ" in mode_clean:
        if audio_obj:
            raw_values = audio_obj.get_fft_bands(st, et, num_bands=num_samples, min_hz=f_min, max_hz=f_max, gain=gain_fac)
        else:
            raw_values = [0.0] * num_samples

        cx = w / 2.0
        cy = h / 2.0
        r_base = min(w, h) * 0.25
        r_max = (min(w, h) * 0.22) * scale_fac

        points_outer: List[Tuple[float, float]] = []
        for i in range(num_samples):
            theta = (float(i) / float(num_samples)) * 2.0 * math.pi
            val = raw_values[i % len(raw_values)]
            r_curr = r_base + val * r_max
            px = round(cx + r_curr * math.cos(theta), 1)
            py = round(cy + r_curr * math.sin(theta), 1)
            points_outer.append((px, py))
            x_coords.append(px)
            y_coords.append(py)

        shape_parts = [f"m {_fmt_val(points_outer[0][0])} {_fmt_val(points_outer[0][1])}"]
        for p in points_outer[1:]:
            shape_parts.append(f"l {_fmt_val(p[0])} {_fmt_val(p[1])}")
        shape_parts.append(f"l {_fmt_val(points_outer[0][0])} {_fmt_val(points_outer[0][1])}")
        shape_str = " ".join(shape_parts) + " "

    elif "rellen" in mode_clean or "filled" in mode_clean or "filledwave" in mode_clean:
        if audio_obj:
            raw_values = audio_obj.get_samples(st, et, num_points=num_samples, gain=gain_fac)
        else:
            raw_values = [0.0] * num_samples

        mid_y = h / 2.0
        shape_parts = [f"m 0 {_fmt_val(mid_y)}"]
        for i, s in enumerate(raw_values):
            px = round((i / float(num_samples - 1)) * w, 1) if num_samples > 1 else 0.0
            py = round(mid_y - s * (h / 2.0) * scale_fac, 1)
            shape_parts.append(f"l {_fmt_val(px)} {_fmt_val(py)}")
            x_coords.append(px)
            y_coords.append(py)

        shape_parts.append(f"l {_fmt_val(w)} {_fmt_val(h)} l 0 {_fmt_val(h)} l 0 {_fmt_val(mid_y)}")
        shape_str = " ".join(shape_parts) + " "

    elif "punto" in mode_clean or "point" in mode_clean or "points" in mode_clean:
        if audio_obj:
            raw_values = audio_obj.get_samples(st, et, num_points=num_samples, gain=gain_fac)
        else:
            raw_values = [0.0] * num_samples

        mid_y = h / 2.0
        r = max(1.0, thick / 2.0)
        shape_parts = []
        for i, s in enumerate(raw_values):
            cx_pt = round((i / float(num_samples - 1)) * w, 1) if num_samples > 1 else 0.0
            cy_pt = round(mid_y - s * (h / 2.0) * scale_fac, 1)
            x_coords.append(cx_pt)
            y_coords.append(cy_pt)
            x0 = round(cx_pt - r, 1)
            x1 = round(cx_pt + r, 1)
            y0 = round(cy_pt - r, 1)
            y1 = round(cy_pt + r, 1)
            shape_parts.append(f"m {_fmt_val(x0)} {_fmt_val(y0)} l {_fmt_val(x1)} {_fmt_val(y0)} l {_fmt_val(x1)} {_fmt_val(y1)} l {_fmt_val(x0)} {_fmt_val(y1)}")
        shape_str = " ".join(shape_parts) + " "

    else:
        if audio_obj:
            raw_values = audio_obj.get_samples(st, et, num_points=num_samples, gain=gain_fac)
        else:
            raw_values = [0.0] * num_samples

        mid_y = h / 2.0
        half_thick = thick / 2.0

        top_points: List[Tuple[float, float]] = []
        bot_points: List[Tuple[float, float]] = []

        for i, s in enumerate(raw_values):
            px = round((i / float(num_samples - 1)) * w, 1) if num_samples > 1 else 0.0
            py = mid_y - s * (h / 2.0) * scale_fac
            top_points.append((px, round(py - half_thick, 1)))
            bot_points.append((px, round(py + half_thick, 1)))
            x_coords.append(px)
            y_coords.append(round(py, 1))

        shape_parts = [f"m {_fmt_val(top_points[0][0])} {_fmt_val(top_points[0][1])}"]
        for p in top_points[1:]:
            shape_parts.append(f"l {_fmt_val(p[0])} {_fmt_val(p[1])}")
        for p in reversed(bot_points):
            shape_parts.append(f"l {_fmt_val(p[0])} {_fmt_val(p[1])}")
        shape_parts.append(f"l {_fmt_val(top_points[0][0])} {_fmt_val(top_points[0][1])}")
        shape_str = " ".join(shape_parts) + " "

    if output_slot_index == 4:
        return [round(v, 4) for v in raw_values]

    if output_slot_index == 3:
        return y_coords

    if output_slot_index == 2:
        return x_coords

    if output_slot_index == 1:
        return f"\\pos({_fmt_val(center_x)},{_fmt_val(center_y)})"

    return shape_str


@pyxis_node("Audio", "Modulator", ["Audio Path", "Tag", "Min Val", "Max Val", "Gain", "Step ms", "Smoothing", "Start Time", "End Time"])
def audio_modulator_node(
    context=None,
    audio_path="",
    tag_name="fscy",
    min_val="100",
    max_val="160",
    gain="1.0",
    step_ms="41.7",
    smoothing="0.2",
    mode="rms",
    min_hz="20",
    max_hz="250",
    start_time="",
    end_time="",
    output_slot_index=0,
    **kwargs
):
    """Pyxis registry wrapper for the Audio/Modulator node."""
    return audio_modulator_master(
        context=context,
        audio_path=audio_path,
        tag_name=tag_name,
        min_val=min_val,
        max_val=max_val,
        gain=gain,
        step_ms=step_ms,
        smoothing=smoothing,
        mode=mode,
        min_hz=min_hz,
        max_hz=max_hz,
        start_time=start_time,
        end_time=end_time,
        output_slot_index=output_slot_index,
        **kwargs
    )


@pyxis_node("Audio", "Waveform", ["Audio Path", "Width", "Height", "Samples", "Gain", "Thickness", "Scale", "Start Time", "End Time"])
def audio_waveform_node(
    context=None,
    audio_path="",
    mode="oscilloscope",
    width="400",
    height="60",
    samples="32",
    gain="1.0",
    thickness="2",
    min_hz="20",
    max_hz="16000",
    scale="1.0",
    start_time="",
    end_time="",
    output_slot_index=0,
    **kwargs
):
    """Pyxis registry wrapper for the Audio/Waveform node."""
    return audio_waveform_master(
        context=context,
        audio_path=audio_path,
        mode=mode,
        width=width,
        height=height,
        samples=samples,
        gain=gain,
        thickness=thickness,
        min_hz=min_hz,
        max_hz=max_hz,
        scale=scale,
        start_time=start_time,
        end_time=end_time,
        output_slot_index=output_slot_index,
        **kwargs
    )

