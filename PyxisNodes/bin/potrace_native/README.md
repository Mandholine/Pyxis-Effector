# potrace_native — Native Image & ASS Vectorisation Engine

> **Location:** `Version en desarrollo/PyxisNodes/bin/potrace_native/`  
> **Purpose:** Pure C99 native vectorisation toolset for **Pyxis Effector**, providing both `potrace` (v1.16 with native ASS and SVG backends) and `img2ass` (direct image-to-ASSDraw converter using `potracelib` and `stb_image`).

---

## 1. Components

1. **`potrace` (v1.16):** Official Potrace bitmap tracer augmented with a native Aegisub ASSDraw output backend (`-b ass`) alongside standard SVG (`--svg`) and EPS backends.
2. **`img2ass`:** Direct native converter from raster images (PNG with alpha channel, JPEG, BMP, WebP) to Aegisub ASSDraw vector geometry (`m`, `l`, `b`), matching the Pyxis `Shape/IMG to Shape` specification with zero Python or external CLI dependencies.

---

## 2. Fast Native Compilation

Execute the included single-step build script (no autotools required):

```bash
cd "Version en desarrollo/PyxisNodes/bin/potrace_native"
./build.sh
```

The script automatically selects `clang` (on macOS) or `gcc` (on Linux) and outputs the compiled native executables into `PyxisNodes/bin/`:
* `Version en desarrollo/PyxisNodes/bin/potrace`
* `Version en desarrollo/PyxisNodes/bin/img2ass`

---

## 3. Usage (`img2ass`)

### 3.1. Direct Image-to-ASS Conversion
```bash
./img2ass input.png output.ass
```

### 3.2. Advanced Parameters
```bash
# Silhouette mode to extract opaque alpha boundaries
./img2ass input.png output.ass --bin_mode silhouette

# Adjust luminance cutoff, curve simplification tolerance, and corner smoothing
./img2ass input.png output.ass --threshold 140 --tolerance 1.5 --alphamax 1.0

# Custom screen position or scale factor
./img2ass input.png output.ass --pos 1280 720 --scale 1.5

# Emit raw ASSDraw vector path string ('m ... b ...') to stdout
./img2ass input.png --raw
```
