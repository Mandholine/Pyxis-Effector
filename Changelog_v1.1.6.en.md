# Change History — Pyxis Effector

Public release notes and version history of Pyxis Effector for the karaoke creation community, Aegisub subtitle editors, and kinetic typography designers.

---

## Pyxis Effector v1.1.6 — Interactive In-Node Previewers, AppData Portability, and Geometric Precision

Release notes for the complete **v1.1.6** release of Pyxis Effector, consolidating the major features and refinements delivered across the 1.1.5 cycle.

### Highlights
This release marks a substantial leap forward in usability and architecture for Pyxis Effector. It introduces native in-node interactive previewers with cursor-focal zoom and pan, embeds a real-time vector animation player directly onto the node canvas, guarantees smooth installation without administrator privileges within Aegisub's user directory (`%APPDATA%`), expands universal mathematical expression support across geometric nodes, and accelerates complex polygon transformations by up to 90%.

---

### What's New

#### 1. Interactive In-Node Previewers
* **New In-Node Animation Player (`Functions/Animation`):**
  * Integrated a real-time vector animation player directly within the body of the node.
  * Features native transport controls: an interactive *Play / Pause* toggle, step-by-step frame buttons (`<`, `>`), an active frame counter (`frame / total`), and an interactive timeline scrub bar.
  * Automatically detects and resolves vector frame sequences from upstream connected nodes (such as animated GIFs or frame sequences traced via `IMG to Shape`), ASSdraw path arrays, or typographic glyphs.
* **Complete Overhaul of Image Previewers (`Shape/IMG to Shape` and `IMG to pixels`):**
  * **Native Canvas 2D Rendering:** Eliminated legacy HTML/SVG DOM overlays in favour of hardware-accelerated drawing on the LiteGraph canvas. Panning and zooming across the node graph no longer suffers from lag, visual tearing, or coordinate desynchronisation.
  * **Focal Zoom and Pan:** Supports smooth mouse-wheel zooming centred directly at the cursor position, mouse drag panning, and instant double-click resetting.
  * **Sequence Navigation Bar:** Integrated a header control bar with stepper buttons and a track scrubber to inspect individual frames of animated GIFs and image sequences.
  * **Visual Mode Selectors:** One-click switching between *Overlay*, *Image*, *Vector* (traced paths), and *Pixels* (sampled point grid) modes.
  * **Missing Media Diagnostic:** Displays a clear flashing warning indicator whenever image paths are missing or files cannot be parsed.

#### 2. Native User-Space Operation
* **Zero-Administrator Installation:** Pyxis Effector now operates natively and portably when placed inside Aegisub's user automation directory:
  ```
  %APPDATA%\Aegisub\automation\autoload\PyxisNodes\
  ```
* **Automatic Windows Security Unblocking (MOTW):** During its initial preflight check, the engine automatically detects and strips Windows *Mark of the Web* streams (`:Zone.Identifier`) from bundled .NET Framework assemblies, `WebView2` libraries, and executable binaries. Users can simply extract the release archive into AppData without encountering Code Access Security (CAS) crashes.

#### 3. Kinetic Geometry and Particle Enhancements
* **Path Sealing in Particles (`Functions/Particles`):** Added the **Close Path** toggle, allowing users to force open contours and glyph strokes closed before distributing perimeter particles.
* **Deterministic Particle Dispersion by Seed (`Functions/Particles`):** Seed-based pseudo-randomisation is now fully independent, guaranteeing consistent and repeatable particle distributions across render cycles.
* **Choreographed Ordering in Procedural Patterns (`Shape/Multi`):** Added an interactive **Order** selector across *Concentric Squares*, *Diagonal Stripes*, *Concentric Rings*, *Segmented Border*, *Radial Rosette*, and *Tunnel / Cascade* modes to animate progressive reveals driven by factor $t$.
* **Radial Explosion in Shape Arrays (`Shape/Array`):** Added the **Explosion** parameter in *Formation* mode to disperse pieces radially outward or inward while preserving the base typographic scale.

---

### Workflow and Performance Improvements

* **High-Performance Geometric Acceleration:** Implemented an in-memory caching pipeline for polygon offsets and boolean difference operations in `Shape/Multi` and `Shape/Union & Divide`, slashing repetitive evaluation latency in complex animations by up to 90% (from ~486 ms down to ~6 ms on intricate silhouettes).
* **Universal Mathematical Expression Evaluation:**
  * **`Shape/Array`:** All numeric parameters (*Cols*, *Rows*, *Spacing*, *Radius*, *Scale*, etc.) now evaluate arithmetic formulas and runtime context variables (`syl.i`, `line.dur`, custom variables).
  * **`Shape/Transform` (Flexor Mode):** The *Curve / Angle* parameter dynamically parses math expressions and variables when configured with numerical bending angles.
  * **`Shape/Concentric Borders`:** The *Separation* property now supports parenthesised arithmetic operations within comma-delimited step lists (e.g. `5, (2 * syl.i), 10`).
* **Modular Web Frontend Architecture:** Decomposed the monolithic web client into category modules under `web/nodes/`, shrinking the main document from 1.8 MB to 63 KB and boosting overall graph responsiveness.
* **Trajectory Fidelity in Particle Resampling:** The *RedrawDist* algorithm in `Functions/Particles` cleanly discretises lines and Bézier splines without rounding sharp corners or distorting contours when redraw distance is zero.
* **Aspect-Ratio Preservation in Segmented Borders:** `Shape/Multi` in *Segmented Border* mode maintains strict 1:1 proportional contours around connected custom silhouettes, avoiding anamorphic stretching.

---

### Bug Fixes

* **Pixel-Perfect Typographic Alignment:** Corrected anchor offset calculations in `Shape/Array` (*Formation* mode) and `Shape/Multi` that previously caused vertical drift when overlaying patterns over centred subtitle text (`\an5`).
* **Coordinate Collapse in Unified Arrays:** Fixed an issue where monolithic output modes in `Shape/Array` collapsed all emitted pieces to origin $(0, 0)$.
* **Animation Order Propagation in Engine:** Fixed an issue where interactive piece order choices in `Shape/Multi` were omitted during final subtitle generation.
* **Canvas Signature Integrity:** Synchronised `Shape/Array` sockets to expose all 9 canonical outputs and operational widgets accurately.
