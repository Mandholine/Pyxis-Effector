# Pyxis Effector - ASS Telemetry & Performance Profiling Engine
# Copyright (C) 2026 @mandholine, @effector2, @pholguinc and Pyxis Effector contributors

from __future__ import annotations

import math
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time

# libass_profiler solo existe como binario de Windows. Mientras no haya un port nativo,
# en Linux/macOS se ejecuta mediante Wine. Un `libass_profiler` nativo (en bin/ o en el
# PATH) tiene prioridad y hace innecesario Wine sin cambiar nada más.
#   PYXIS_DISABLE_WINE=1   no usar Wine nunca
#   PYXIS_WINE=<ruta>      ejecutable de wine concreto
#   PYXIS_WINEPREFIX=<dir> prefijo de Wine (por defecto <datos de usuario>/PyxisNodes/wine)
_WINE_INIT_LOCK = threading.Lock()
_WINE_PREFIX_MARKER = ".pyxis_prefix_ready"
_WINE_RUN_TIMEOUT_S = 600
_MACOS_WINE_BINARIES = (
    "/Applications/Wine Stable.app/Contents/Resources/wine/bin/wine",
    "/Applications/Wine Staging.app/Contents/Resources/wine/bin/wine",
    "/Applications/Wine Devel.app/Contents/Resources/wine/bin/wine",
    "/Applications/CrossOver.app/Contents/SharedSupport/CrossOver/bin/wine",
)


def find_wine() -> str | None:
    """Localiza el ejecutable de Wine, o None si no hay (o está desactivado)."""
    if os.environ.get("PYXIS_DISABLE_WINE") == "1":
        return None
    override = os.environ.get("PYXIS_WINE")
    if override:
        return override if os.path.isfile(override) else shutil.which(override)
    for name in ("wine", "wine64"):
        found = shutil.which(name)
        if found:
            return found
    if sys.platform == "darwin":
        for candidate in _MACOS_WINE_BINARIES:
            if os.path.isfile(candidate):
                return candidate
    return None


def _wine_env() -> dict:
    """Entorno aislado para Wine: prefijo propio y sin pantalla (el profiler es de consola)."""
    try:
        from paths import get_user_data_dir
        data_dir = get_user_data_dir()
    except Exception:
        data_dir = os.path.join(os.path.expanduser("~"), ".local", "share", "PyxisNodes")
    env = dict(os.environ)
    env["WINEPREFIX"] = os.environ.get("PYXIS_WINEPREFIX") or os.path.join(data_dir, "wine")
    env["WINEARCH"] = "win64"
    env["WINEDEBUG"] = "-all"
    env["WINEDLLOVERRIDES"] = "mscoree,mshtml=d"  # evita los diálogos de instalación de Mono/Gecko
    env.pop("DISPLAY", None)
    env.pop("WAYLAND_DISPLAY", None)
    return env


def _ensure_wine_prefix(wine: str, env: dict) -> str | None:
    """Crea el prefijo de Wine una sola vez. Devuelve un mensaje de error, o None si está listo.

    Debe hacerse antes de lanzar los shards en paralelo: varios Wine creando el mismo
    prefijo a la vez lo corromperían.
    """
    prefix = env["WINEPREFIX"]
    marker = os.path.join(prefix, _WINE_PREFIX_MARKER)
    if os.path.isfile(marker):
        return None
    with _WINE_INIT_LOCK:
        if os.path.isfile(marker):
            return None
        try:
            os.makedirs(prefix, exist_ok=True)
            result = subprocess.run([wine, "wineboot", "--init"], env=env, capture_output=True,
                                    text=True, timeout=240)
        except subprocess.TimeoutExpired:
            return f"Wine no terminó de crear el prefijo en {prefix} (tiempo agotado)"
        except OSError as exc:
            return f"No se pudo ejecutar Wine ({wine}): {exc}"
        if result.returncode != 0:
            tail = (result.stderr or result.stdout or "").strip()[-300:]
            return f"Wine no pudo crear el prefijo en {prefix} (código {result.returncode}). {tail}"
        try:
            with open(marker, "w", encoding="utf-8") as fp:
                fp.write("ok\n")
        except OSError:
            pass
    return None


def parse_ass_time_ms(t_str: str) -> int:
    if not t_str:
        return -1
    try:
        parts = str(t_str).strip().split(":")
        if len(parts) != 3:
            return -1
        h = int(parts[0])
        m = int(parts[1])
        sec_parts = parts[2].split(".")
        s = int(sec_parts[0])
        frac_str = sec_parts[1] if len(sec_parts) > 1 else "0"
        if len(frac_str) == 2:
            ms = int(frac_str) * 10
        elif len(frac_str) >= 3:
            ms = int(frac_str[:3])
        elif len(frac_str) == 1:
            ms = int(frac_str) * 100
        else:
            ms = 0
        return (h * 3600 + m * 60 + s) * 1000 + ms
    except Exception:
        return -1


def format_ass_time_cs(ms: int) -> str:
    if ms < 0:
        ms = 0
    total_cs = int(round(ms / 10.0))
    cs = total_cs % 100
    total_s = total_cs // 100
    s = total_s % 60
    total_m = total_s // 60
    m = total_m % 60
    h = total_m // 60
    return f"{h}:{m:02d}:{s:02d}.{cs:02d}"


def format_display_time_ms(ms: int) -> str:
    if ms < 0:
        ms = 0
    s_total = ms // 1000
    rem_ms = ms % 1000
    m = (s_total // 60) % 60
    h = s_total // 3600
    s = s_total % 60
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}.{rem_ms:03d}"
    return f"{m:02d}:{s:02d}.{rem_ms:03d}"


def _shift_dialogue_line_zero(raw_line: str, offset_ms: int, clip_window_ms: int | None = None) -> str:
    prefix_len = 9 if raw_line.startswith("Dialogue:") else 8
    body = raw_line[prefix_len:].lstrip()
    parts = body.split(",", 9)
    if len(parts) < 10:
        return raw_line
    st = parse_ass_time_ms(parts[1])
    et = parse_ass_time_ms(parts[2])
    if st < 0 or et <= st:
        return ""
    new_st = max(0, st - offset_ms)
    new_et = et - offset_ms
    if clip_window_ms is not None and new_et > clip_window_ms + 500:
        new_et = clip_window_ms + 500
    if new_et <= new_st:
        return ""
    parts[1] = format_ass_time_cs(new_st)
    parts[2] = format_ass_time_cs(new_et)
    line_out = "Dialogue: " + ",".join(parts)
    if not line_out.endswith("\n"):
        line_out += "\n"
    return line_out


def extract_ass_for_telemetry(ass_content: str) -> dict:
    header_lines = []
    valid_dialogues = []
    invalid_duration_lines = 0
    in_events = False
    has_events_header = False
    has_format_line = False

    for raw_line in (ass_content or "").splitlines(keepends=True):
        clean = raw_line.lstrip("\ufeff")
        stripped = clean.strip()
        if stripped.startswith("[Events]"):
            in_events = True
            has_events_header = True
            header_lines.append("[Events]\n")
            continue

        if not in_events:
            if not stripped.startswith(";"):
                header_lines.append(clean if clean.endswith("\n") else clean + "\n")
        else:
            if stripped.startswith("Format:"):
                if not has_format_line:
                    header_lines.append(clean if clean.endswith("\n") else clean + "\n")
                    has_format_line = True
            elif stripped.startswith("Dialogue:") or stripped.startswith("Dialogue :"):
                prefix_len = 9 if stripped.startswith("Dialogue:") else 10
                parts = stripped[prefix_len:].split(",", 9)
                if len(parts) >= 10:
                    st = parse_ass_time_ms(parts[1])
                    et = parse_ass_time_ms(parts[2])
                    if st >= 0 and et > st:
                        valid_dialogues.append((st, et, stripped))
                    else:
                        invalid_duration_lines += 1

    if not has_events_header:
        header_lines.append("\n[Events]\n")
    if not has_format_line:
        header_lines.append("Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n")

    if valid_dialogues:
        min_start_ms = min(d[0] for d in valid_dialogues)
        max_end_ms = max(d[1] for d in valid_dialogues)
    else:
        min_start_ms = 0
        max_end_ms = 0

    return {
        "header_text": "".join(header_lines),
        "valid_dialogues": valid_dialogues,
        "invalid_duration_lines": invalid_duration_lines,
        "min_start_ms": min_start_ms,
        "max_end_ms": max_end_ms,
    }


def parse_profiler_csv(csv_path: str, offset_ms: int = 0, clip_start_ms: int = 0, max_rel_ms: int | None = None) -> list:
    frames = []
    if not csv_path or not os.path.isfile(csv_path):
        return frames

    with open(csv_path, "r", encoding="utf-8", errors="ignore") as fp:
        for line in fp:
            s = line.strip()
            if not s or s.startswith("time,") or ":" not in s:
                continue
            parts = s.split(",")
            if len(parts) != 5:
                continue
            rel_ms = parse_ass_time_ms(parts[0])
            if rel_ms < 0:
                continue
            if max_rel_ms is not None and rel_ms >= max_rel_ms:
                continue
            try:
                total_bytes = int(parts[1])
                largest_bytes = int(parts[2])
                image_count = int(parts[3])
                render_ms = round(float(parts[4]) * 1000.0, 3)
                if image_count <= 0 and total_bytes <= 0:
                    render_ms = 0.0
            except (ValueError, TypeError):
                continue

            abs_t_ms = offset_ms + rel_ms
            frames.append({
                "t_ms": abs_t_ms,
                "rel_s": round(max(0.0, (abs_t_ms - clip_start_ms) / 1000.0), 3),
                "render_ms": render_ms,
                "total_bytes": total_bytes,
                "largest_bytes": largest_bytes,
                "image_count": image_count,
            })

    # Suppress cold-start font/DirectWrite initialization spike on the first active frames of each shard
    active_indices = [idx for idx, f in enumerate(frames) if f["image_count"] > 0]
    if len(active_indices) >= 2:
        ref_slice = active_indices[3:6] if len(active_indices) >= 6 else active_indices[1:3]
        steady_ms = min(frames[i]["render_ms"] for i in ref_slice)
        warmup_cutoff = active_indices[min(2, len(active_indices) - 1)]
        for i in range(warmup_cutoff + 1):
            if frames[i]["render_ms"] > steady_ms:
                frames[i]["render_ms"] = steady_ms

    # Suppress isolated single-frame font-face cache misses (forward neighbor check)
    for i in range(len(frames) - 2):
        f0, f1, f2 = frames[i], frames[i + 1], frames[i + 2]
        if (
            f0["image_count"] > 0
            and f0["image_count"] == f1["image_count"] == f2["image_count"]
            and abs(f0["total_bytes"] - f1["total_bytes"]) <= max(512, f1["total_bytes"] * 0.12)
        ):
            baseline_next = max(f1["render_ms"], f2["render_ms"])
            if f0["render_ms"] > max(0.8, baseline_next * 2.0):
                f0["render_ms"] = round((f1["render_ms"] + f2["render_ms"]) * 0.5, 3)

    # Suppress isolated tail-end single-frame spikes at the end of a shard or before silence (backward neighbor check)
    for i in range(2, len(frames)):
        f_prev2, f_prev1, f0 = frames[i - 2], frames[i - 1], frames[i]
        if f0["image_count"] <= 0 or f_prev1["image_count"] <= 0 or f_prev2["image_count"] <= 0:
            continue
        is_tail_frame = (i >= len(frames) - 2) or (frames[i + 1]["image_count"] <= 0)
        bytes_not_growing = f0["total_bytes"] <= max(f_prev1["total_bytes"] * 1.15, f_prev1["total_bytes"] + 512)
        same_geometry = (
            f0["image_count"] == f_prev1["image_count"] == f_prev2["image_count"]
            and abs(f0["total_bytes"] - f_prev1["total_bytes"]) <= max(512, f_prev1["total_bytes"] * 0.12)
        )
        if (is_tail_frame and bytes_not_growing) or same_geometry:
            baseline_prev = max(f_prev1["render_ms"], f_prev2["render_ms"])
            if f0["render_ms"] > max(0.8, baseline_prev * 2.0):
                f0["render_ms"] = round((f_prev1["render_ms"] + f_prev2["render_ms"]) * 0.5, 3)

    return frames


class ASSTelemetryManager:
    def __init__(self, profiler_exe_path: str | None = None):
        self.profiler_exe = profiler_exe_path or self._locate_profiler()
        self._lock = threading.Lock()
        self._job_counter = 0
        self._active_procs = {}
        self._active_dirs = {}
        self._last_result = None

    @staticmethod
    def _locate_profiler() -> str:
        """Ruta del profiler: nativo si existe; en POSIX, si no, el .exe de Windows (se ejecuta con Wine)."""
        exe_name = "libass_profiler.exe" if os.name == "nt" else "libass_profiler"
        try:
            from paths import get_bin_path
            found = get_bin_path("libass_profiler")
            if os.path.isfile(found):
                return found
            if os.name != "nt":
                found_exe = get_bin_path("libass_profiler.exe")
                if os.path.isfile(found_exe):
                    return found_exe
            return found
        except Exception:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            names = [exe_name] if os.name == "nt" else [exe_name, exe_name + ".exe"]
            candidates = [
                os.path.join(base_dir, rel, name)
                for name in names
                for rel in ("bin", os.path.join("..", "bin"), "")
            ]
            return next((c for c in candidates if os.path.exists(c)), candidates[0])

    def _resolve_runner(self) -> dict:
        """Decide cómo ejecutar el profiler: nativo o mediante Wine.

        Devuelve {"kind", "prefix", "env", "timeout", "error"}; ``prefix`` es la lista de
        argumentos previa al .ass y al .csv. Si no se puede ejecutar, "error" explica por qué.
        """
        exe = self.profiler_exe
        if not exe or not os.path.isfile(exe):
            return {"error": f"Profiler binary not found: {exe}"}

        if os.name == "nt" or not exe.lower().endswith(".exe"):
            return {"kind": "native", "prefix": [exe], "env": None, "timeout": None, "error": None}

        wine = find_wine()
        if not wine:
            return {"error": (
                "libass_profiler solo existe como binario de Windows y no se encontró Wine para ejecutarlo. "
                "Instala wine (p. ej. 'sudo apt install wine' / 'sudo pacman -S wine' / 'brew install --cask wine-stable') "
                "o coloca un libass_profiler nativo en PyxisNodes/bin/."
            )}
        env = _wine_env()
        prefix_error = _ensure_wine_prefix(wine, env)
        if prefix_error:
            return {"error": prefix_error}
        return {"kind": "wine", "prefix": [wine, exe], "env": env, "timeout": _WINE_RUN_TIMEOUT_S, "error": None}

    def get_last_result(self) -> dict | None:
        return self._last_result

    def clear_last_result(self) -> None:
        self.cancel_active_jobs()
        with self._lock:
            self._last_result = None

    def cancel_active(self) -> int:
        return self.cancel_active_jobs()

    def cancel_active_jobs(self) -> int:
        with self._lock:
            self._job_counter += 1
            current_id = self._job_counter
            procs = list(self._active_procs.values())
            self._active_procs.clear()
            dirs = list(self._active_dirs.values())
            self._active_dirs.clear()

        for proc in procs:
            try:
                if proc and proc.poll() is None:
                    proc.kill()
            except Exception:
                pass

        for d in dirs:
            try:
                if d and os.path.isdir(d):
                    shutil.rmtree(d, ignore_errors=True)
            except Exception:
                pass

        return current_id

    def profile_ass_content(self, ass_content: str, **kwargs) -> dict:
        return self.run_telemetry(ass_content=ass_content, **kwargs)

    def run_telemetry(
        self,
        ass_content: str,
        fps: float = 23.976,
        clip_start_ms: int | None = None,
        clip_end_ms: int | None = None,
        max_workers: int | None = None,
        source: str = "base",
        res_x: int = 1920,
        res_y: int = 1080,
        **_extra_kwargs,
    ) -> dict:
        t_wall_start = time.perf_counter()
        job_id = self.cancel_active_jobs()

        runner = self._resolve_runner()
        if runner.get("error"):
            return {
                "status": "error",
                "success": False,
                "job_id": job_id,
                "message": runner["error"],
                "error": runner["error"],
            }
        with self._lock:
            if self._job_counter != job_id:
                return {"success": False, "cancelled": True, "job_id": job_id}

        fps_val = float(fps) if fps and float(fps) > 0 else 23.976
        frame_budget_ms = round(1000.0 / fps_val, 3)

        extracted = extract_ass_for_telemetry(ass_content)
        valid_dialogues = extracted["valid_dialogues"]
        invalid_duration_lines = extracted["invalid_duration_lines"]
        min_start_ms = extracted["min_start_ms"]
        max_end_ms = extracted["max_end_ms"]
        header_text = extracted["header_text"]

        eff_clip_start_ms = int(clip_start_ms) if clip_start_ms is not None else (max(0, min_start_ms - 2000) if valid_dialogues else 0)
        eff_clip_end_ms = (
            int(clip_end_ms)
            if (clip_end_ms is not None and int(clip_end_ms) > eff_clip_start_ms)
            else ((max_end_ms + 2000) if valid_dialogues else max(eff_clip_start_ms + 5000, 15000))
        )

        if valid_dialogues and (clip_start_ms is not None or clip_end_ms is not None):
            windowed_dialogues = []
            for st, et, raw_l in valid_dialogues:
                if et > eff_clip_start_ms and st < eff_clip_end_ms:
                    clamped_st = max(st, eff_clip_start_ms)
                    clamped_et = min(et, eff_clip_end_ms)
                    if clamped_et > clamped_st:
                        windowed_dialogues.append((clamped_st, clamped_et, raw_l))
            valid_dialogues = windowed_dialogues
            if valid_dialogues:
                min_start_ms = min(d[0] for d in valid_dialogues)
                max_end_ms = max(d[1] for d in valid_dialogues)

        if not valid_dialogues:
            eff_start = eff_clip_start_ms
            eff_end = eff_clip_end_ms
            elapsed_s = round(time.perf_counter() - t_wall_start, 3)
            empty_res = {
                "status": "ok",
                "success": True,
                "job_id": job_id,
                "source": source,
                "runner": runner["kind"],
                "fps": round(fps_val, 3),
                "frame_budget_ms": frame_budget_ms,
                "clip_start_ms": eff_start,
                "clip_end_ms": eff_end,
                "active_start_ms": eff_start,
                "active_end_ms": eff_end,
                "elapsed_sec": elapsed_s,
                "summary": {
                    "fps": round(fps_val, 3),
                    "frame_budget_ms": frame_budget_ms,
                    "clip_start_ms": eff_start,
                    "clip_end_ms": eff_end,
                    "total_frames": 0,
                    "active_frames": 0,
                    "peak_ms": 0.0,
                    "peak_render_ms": 0.0,
                    "peak_frame": 0,
                    "peak_time_ms": eff_start,
                    "avg_ms": 0.0,
                    "avg_render_ms": 0.0,
                    "p95_ms": 0.0,
                    "p95_render_ms": 0.0,
                    "peak_budget_pct": 0.0,
                    "budget_usage_pct": 0.0,
                    "dropped_frames": 0,
                    "dropped_frames_count": 0,
                    "dropped_pct": 0.0,
                    "dropped_frames_pct": 0.0,
                    "warning_frames_count": 0,
                    "peak_total_kb": 0.0,
                    "peak_total_size_bytes": 0,
                    "peak_largest_kb": 0.0,
                    "peak_largest_size_bytes": 0,
                    "peak_objects": 0,
                    "peak_image_count": 0,
                    "avg_image_count": 0.0,
                    "elapsed_ms": round(elapsed_s * 1000.0, 1),
                    "workers_used": 1,
                    "invalid_duration_lines": invalid_duration_lines,
                    "dialogue_lines_count": 0,
                },
                "frames": [],
                "hotspots": [],
            }
            self._last_result = empty_res
            return empty_res

        if eff_clip_end_ms <= eff_clip_start_ms:
            eff_clip_end_ms = eff_clip_start_ms + max(2000, max_end_ms - min_start_ms)

        active_span_ms = max(1, max_end_ms - min_start_ms)
        cpu_cores = os.cpu_count() or 4
        limit_workers = min(16, cpu_cores) if max_workers is None else max(1, int(max_workers))

        if len(valid_dialogues) >= 60 and active_span_ms >= 2000 and limit_workers > 1:
            num_shards = min(limit_workers, max(2, active_span_ms // 1500))
        else:
            num_shards = 1

        work_dir = tempfile.mkdtemp(prefix=f"pyxis_telemetry_{job_id}_")
        with self._lock:
            if self._job_counter != job_id:
                shutil.rmtree(work_dir, ignore_errors=True)
                return {"success": False, "cancelled": True, "job_id": job_id}
            self._active_dirs[job_id] = work_dir

        try:
            shard_specs = []
            shard_dur_ms = int(math.ceil(active_span_ms / float(num_shards)))

            for idx in range(num_shards):
                c_start = min_start_ms + idx * shard_dur_ms
                c_end = max_end_ms if idx == num_shards - 1 else min(max_end_ms, c_start + shard_dur_ms)
                if c_end <= c_start:
                    continue
                window_len = c_end - c_start
                ass_file = os.path.join(work_dir, f"shard_{idx}.ass")
                csv_file = os.path.join(work_dir, f"shard_{idx}.csv")

                shifted_lines = []
                for st, et, raw_l in valid_dialogues:
                    if et > c_start and st < c_end:
                        s_line = _shift_dialogue_line_zero(raw_l, c_start, clip_window_ms=window_len)
                        if s_line:
                            shifted_lines.append(s_line)

                if not shifted_lines:
                    continue

                with open(ass_file, "w", encoding="utf-8") as fp:
                    fp.write(header_text)
                    fp.writelines(shifted_lines)

                shard_specs.append({
                    "idx": idx,
                    "c_start": c_start,
                    "c_end": c_end,
                    "window_len": window_len,
                    "ass_file": ass_file,
                    "csv_file": csv_file,
                })

            creationflags = 0
            if os.name == "nt":
                creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0x08000000)

            spawned = []
            for spec in shard_specs:
                with self._lock:
                    if self._job_counter != job_id:
                        return {"success": False, "cancelled": True, "job_id": job_id}
                    if runner["kind"] == "wine":
                        # Wine recibe rutas relativas: cwd ya es work_dir y evita convertir rutas Unix a DOS
                        profiler_args = [os.path.basename(spec["ass_file"]), os.path.basename(spec["csv_file"])]
                    else:
                        profiler_args = [spec["ass_file"], spec["csv_file"]]
                    proc = subprocess.Popen(
                        [*runner["prefix"], *profiler_args],
                        cwd=work_dir,
                        env=runner["env"],
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        creationflags=creationflags,
                    )
                    self._active_procs[f"{job_id}_{spec['idx']}"] = proc
                    spawned.append((spec, proc))

            for spec, proc in spawned:
                try:
                    proc.wait(timeout=runner["timeout"])
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait()
                spec["returncode"] = proc.returncode
                with self._lock:
                    self._active_procs.pop(f"{job_id}_{spec['idx']}", None)
                    if self._job_counter != job_id:
                        return {"success": False, "cancelled": True, "job_id": job_id}

            if runner["kind"] == "wine" and spawned and not any(os.path.isfile(s["csv_file"]) for s, _ in spawned):
                codes = ", ".join(str(s.get("returncode")) for s, _ in spawned)
                msg = f"libass_profiler (Wine) no generó resultados (códigos de salida: {codes}). Revisa la instalación de Wine."
                return {"status": "error", "success": False, "job_id": job_id, "message": msg, "error": msg}

            active_frames = []
            for spec, _ in spawned:
                max_rel = spec["window_len"] if spec["idx"] < len(spawned) - 1 else (spec["window_len"] + 50)
                parsed_chunk = parse_profiler_csv(
                    spec["csv_file"],
                    offset_ms=spec["c_start"],
                    clip_start_ms=eff_clip_start_ms,
                    max_rel_ms=max_rel,
                )
                active_frames.extend(parsed_chunk)

            active_frames.sort(key=lambda x: x["t_ms"])

            # Deduplicate any boundary frame with identical or <15ms timestamp distance and clamp to [eff_clip_start_ms, eff_clip_end_ms]
            deduped_raw = []
            for f_item in active_frames:
                if f_item["t_ms"] < eff_clip_start_ms or f_item["t_ms"] > eff_clip_end_ms:
                    continue
                if deduped_raw and abs(f_item["t_ms"] - deduped_raw[-1]["t_ms"]) < 15:
                    if f_item["render_ms"] > deduped_raw[-1]["render_ms"]:
                        deduped_raw[-1] = f_item
                else:
                    deduped_raw.append(f_item)

            # Fill interior silent gaps between shards/dialogues and pad leading & trailing silence inside [eff_clip_start_ms, eff_clip_end_ms]
            step_ms = 1000.0 / fps_val
            deduped_active = []
            for f_item in deduped_raw:
                if deduped_active:
                    prev_t = deduped_active[-1]["t_ms"]
                    gap_ms = f_item["t_ms"] - prev_t
                    if gap_ms > step_ms * 1.65:
                        g_idx = 1
                        while True:
                            t_gap = int(round(prev_t + g_idx * step_ms))
                            if t_gap >= f_item["t_ms"] - 15:
                                break
                            deduped_active.append({
                                "t_ms": t_gap,
                                "rel_s": round(max(0.0, (t_gap - eff_clip_start_ms) / 1000.0), 3),
                                "render_ms": 0.0,
                                "total_bytes": 0,
                                "largest_bytes": 0,
                                "image_count": 0,
                            })
                            g_idx += 1
                deduped_active.append(f_item)

            leading_frames = []
            first_active_ms = deduped_active[0]["t_ms"] if deduped_active else min_start_ms
            if first_active_ms > eff_clip_start_ms + step_ms:
                k = 0
                while True:
                    t_cur = int(round(eff_clip_start_ms + k * step_ms))
                    if t_cur >= first_active_ms - 15:
                        break
                    leading_frames.append({
                        "t_ms": t_cur,
                        "rel_s": round(max(0.0, (t_cur - eff_clip_start_ms) / 1000.0), 3),
                        "render_ms": 0.0,
                        "total_bytes": 0,
                        "largest_bytes": 0,
                        "image_count": 0,
                    })
                    k += 1

            trailing_frames = []
            last_active_ms = deduped_active[-1]["t_ms"] if deduped_active else max_end_ms
            if eff_clip_end_ms > last_active_ms + step_ms:
                k = 1
                while True:
                    t_cur = int(round(last_active_ms + k * step_ms))
                    if t_cur > eff_clip_end_ms:
                        break
                    trailing_frames.append({
                        "t_ms": t_cur,
                        "rel_s": round(max(0.0, (t_cur - eff_clip_start_ms) / 1000.0), 3),
                        "render_ms": 0.0,
                        "total_bytes": 0,
                        "largest_bytes": 0,
                        "image_count": 0,
                    })
                    k += 1

            all_frames = leading_frames + deduped_active + trailing_frames
            for f_idx, f_obj in enumerate(all_frames):
                f_obj["frame"] = f_idx
                f_obj["time_ms"] = f_obj["t_ms"]
                f_obj["total_kb"] = round(f_obj.get("total_bytes", 0) / 1024.0, 2)
                f_obj["largest_kb"] = round(f_obj.get("largest_bytes", 0) / 1024.0, 2)
                f_obj["objects"] = f_obj.get("image_count", 0)

            # Compute KPI metrics over the active non-silent frames (and full timeline where applicable)
            non_silent_active = [f for f in deduped_active if f.get("image_count", 0) > 0]
            metric_source = non_silent_active if non_silent_active else (deduped_active if deduped_active else all_frames)
            render_vals = [f["render_ms"] for f in metric_source]
            sorted_renders = sorted(render_vals)
            n_active = len(metric_source)

            peak_frame_obj = max(metric_source, key=lambda x: x["render_ms"]) if metric_source else None
            peak_render_ms = round(max(render_vals), 3) if render_vals else 0.0
            peak_frame_num = peak_frame_obj.get("frame", 0) if peak_frame_obj else 0
            peak_time_ms = peak_frame_obj.get("t_ms", eff_clip_start_ms) if peak_frame_obj else eff_clip_start_ms
            avg_render_ms = round(sum(render_vals) / n_active, 3) if n_active > 0 else 0.0
            p95_idx = min(n_active - 1, int(math.floor(n_active * 0.95))) if n_active > 0 else 0
            p95_render_ms = round(sorted_renders[p95_idx], 3) if sorted_renders else 0.0
            peak_budget_pct = round((peak_render_ms / frame_budget_ms) * 100.0, 1) if frame_budget_ms > 0 else 0.0

            dropped_count = sum(1 for v in render_vals if v > frame_budget_ms)
            warning_count = sum(1 for v in render_vals if (frame_budget_ms * 0.5) <= v <= frame_budget_ms)
            dropped_pct = round((dropped_count / n_active) * 100.0, 2) if n_active > 0 else 0.0

            peak_total_bytes = max((f["total_bytes"] for f in metric_source), default=0)
            peak_largest_bytes = max((f["largest_bytes"] for f in metric_source), default=0)
            peak_total_kb = round(peak_total_bytes / 1024.0, 2)
            peak_largest_kb = round(peak_largest_bytes / 1024.0, 2)
            peak_image_count = max((f["image_count"] for f in metric_source), default=0)
            avg_image_count = round(sum(f["image_count"] for f in metric_source) / n_active, 1) if n_active > 0 else 0.0

            # Build top distinct hotspots (separated by at least 800 ms)
            candidates = sorted(metric_source, key=lambda x: (x["render_ms"], x["total_bytes"]), reverse=True)
            hotspots = []
            for cand in candidates:
                if cand["render_ms"] <= 0.0:
                    break
                if any(abs(cand["t_ms"] - h["t_ms"]) < 800 for h in hotspots):
                    continue
                ratio = cand["render_ms"] / frame_budget_ms if frame_budget_ms > 0 else 0.0
                if ratio >= 1.0:
                    sev = "critical"
                elif ratio >= 0.5:
                    sev = "warning"
                else:
                    sev = "nominal"
                hotspots.append({
                    "rank": len(hotspots) + 1,
                    "frame": cand.get("frame", 0),
                    "t_ms": cand["t_ms"],
                    "time_ms": cand["t_ms"],
                    "rel_s": cand["rel_s"],
                    "display_time": format_display_time_ms(max(0, cand["t_ms"] - eff_clip_start_ms)),
                    "abs_display_time": format_display_time_ms(cand["t_ms"]),
                    "render_ms": cand["render_ms"],
                    "budget_pct": round(ratio * 100.0, 1),
                    "total_bytes": cand["total_bytes"],
                    "total_kb": round(cand["total_bytes"] / 1024.0, 2),
                    "largest_bytes": cand["largest_bytes"],
                    "largest_kb": round(cand["largest_bytes"] / 1024.0, 2),
                    "image_count": cand["image_count"],
                    "objects": cand["image_count"],
                    "severity": sev,
                })
                if len(hotspots) >= 8:
                    break

            elapsed_s = round(time.perf_counter() - t_wall_start, 3)
            result = {
                "status": "ok",
                "success": True,
                "job_id": job_id,
                "source": source,
                "runner": runner["kind"],
                "fps": round(fps_val, 3),
                "frame_budget_ms": frame_budget_ms,
                "clip_start_ms": eff_clip_start_ms,
                "clip_end_ms": eff_clip_end_ms,
                "active_start_ms": min_start_ms,
                "active_end_ms": max_end_ms,
                "workers_used": len(spawned),
                "elapsed_sec": elapsed_s,
                "summary": {
                    "fps": round(fps_val, 3),
                    "frame_budget_ms": frame_budget_ms,
                    "clip_start_ms": eff_clip_start_ms,
                    "clip_end_ms": eff_clip_end_ms,
                    "total_frames": len(all_frames),
                    "active_frames": n_active,
                    "peak_ms": peak_render_ms,
                    "peak_render_ms": peak_render_ms,
                    "peak_frame": peak_frame_num,
                    "peak_time_ms": peak_time_ms,
                    "avg_ms": avg_render_ms,
                    "avg_render_ms": avg_render_ms,
                    "p95_ms": p95_render_ms,
                    "p95_render_ms": p95_render_ms,
                    "peak_budget_pct": peak_budget_pct,
                    "budget_usage_pct": peak_budget_pct,
                    "dropped_frames": dropped_count,
                    "dropped_frames_count": dropped_count,
                    "dropped_pct": dropped_pct,
                    "dropped_frames_pct": dropped_pct,
                    "warning_frames_count": warning_count,
                    "peak_total_kb": peak_total_kb,
                    "peak_total_size_bytes": peak_total_bytes,
                    "peak_largest_kb": peak_largest_kb,
                    "peak_largest_size_bytes": peak_largest_bytes,
                    "peak_objects": peak_image_count,
                    "peak_image_count": peak_image_count,
                    "avg_image_count": avg_image_count,
                    "elapsed_ms": round(elapsed_s * 1000.0, 1),
                    "workers_used": len(spawned),
                    "invalid_duration_lines": invalid_duration_lines,
                    "dialogue_lines_count": len(valid_dialogues),
                },
                "frames": all_frames,
                "hotspots": hotspots,
            }
            self._last_result = result
            return result
        finally:
            with self._lock:
                self._active_dirs.pop(job_id, None)
            try:
                if os.path.isdir(work_dir):
                    shutil.rmtree(work_dir, ignore_errors=True)
            except Exception:
                pass


GLOBAL_TELEMETRY_MANAGER = ASSTelemetryManager()
