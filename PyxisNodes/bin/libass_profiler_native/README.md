# libass_profiler Native — Clean-Room C99 Reimplementation

> **Location:** `Version en desarrollo/PyxisNodes/bin/libass_profiler_native/`  
> **Purpose:** Replaces the legacy precompiled Windows binary (`libass_profiler.exe`) with a clean-room native C99 implementation portable across **Linux**, **macOS**, and **Windows**, completely removing Wine and emulation layers from POSIX platforms.

---

## 1. Executive Summary

The Pyxis Effector ASS telemetry engine (`ass_telemetry_engine.py`) employs a dedicated benchmark utility (`libass_profiler`) to profile frame-by-frame rendering performance of Advanced SubStation Alpha scripts. In Windows, this binary executes natively. On Linux and macOS, previous community wrappers attempted to invoke `libass_profiler.exe` via Wine, which introduced:
1. Significant process startup overhead when forking multiple shards in parallel.
2. Fragile path translation between UNIX paths and Windows drive letters (`Z:\tmp\...`).
3. Friction on macOS packaging where Wine is heavy or unavailable.

A clean-room reverse engineering of the original binary confirmed it is a lightweight C benchmark wrapper (~100 lines) linking directly against `libass`, originating from the [assytics](https://github.com/N0r01/specter-fansub-tools/tree/main/assytics) utility developed by **N0r01** in `specter-fansub-tools`. This native C99 implementation is 100% compatible with the input arguments and output CSV protocol of Pyxis Effector.

---

## 2. Technical Specification

### 2.1. CLI Arguments
```text
libass version <version>
Usage: libass_profiler <assfile> <output> [--fps <val>]
output is optional and defaults to output.csv
```

### 2.2. Output CSV Schema
* **Line 1:** Source ASS script file path.
* **Line 2 (Header):**
  ```csv
  time,total_image_size,largest_image_size,image_count,time_benchmark
  ```
* **Data Rows:** Formatted via `"%s,%lld,%lld,%lld,%lf\n"`, where:
  * `time`: ASS timestamp (`H:MM:SS.mmm`).
  * `total_image_size`: Sum of bitmap memory across all rendered `ASS_Image` objects: `(h - 1) * stride + w`.
  * `largest_image_size`: Maximum single bitmap memory in frame.
  * `image_count`: Total count of rendered image slices.
  * `time_benchmark`: High-resolution render duration in seconds measured using monotonic timers (`clock_gettime(CLOCK_MONOTONIC)` on POSIX, `QueryPerformanceCounter` on Windows).

---

## 3. Build Instructions

### 3.1. Linux (Ubuntu / Debian / Linux Mint)
```bash
sudo apt update
sudo apt install build-essential pkg-config libass-dev

cd "Version en desarrollo/PyxisNodes/bin/libass_profiler_native"
make
make install
```

### 3.2. Linux (Arch Linux / Manjaro)
```bash
sudo pacman -S base-devel pkgconf libass

cd "Version en desarrollo/PyxisNodes/bin/libass_profiler_native"
make
make install
```

### 3.3. macOS (Apple Silicon & Intel via Homebrew)
```bash
brew install libass pkg-config

cd "Version en desarrollo/PyxisNodes/bin/libass_profiler_native"
make
make install
```

### 3.4. Windows (MSYS2 / MinGW-w64)
```cmd
pacman -S mingw-w64-x86_64-gcc mingw-w64-x86_64-libass
build.bat
```

