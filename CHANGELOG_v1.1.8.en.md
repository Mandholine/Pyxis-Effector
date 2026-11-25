# Pyxis Effector v1.1.8 — Release Notes

Release notes for the **v1.1.8 (Beta)** cycle of Pyxis Effector. This release introduces the universal single-line assembler `Basics/Builder`, the new `Shadtrick` mode in `Functions/Move Tag`, the `Relative2` anchor without `\org`, completely redesigns `Basics/Math` around the `ke.math` standard, expands `Audio/Waveform` with spatial anchor and smoothing controls, enhances original line tag/property preservation, and substantially improves Previewer responsiveness.

---

### Highlights

* **New Universal Assembler `Basics/Builder`:** Compiles text fragments or intricate vector pieces into a single continuous ASS line with optional `\r` reset barriers, topological interior-hole retention, expandable inputs, and an isolated sub-loop (`bu_i`, `bu_n`, `max_bu`).
* **`Shadtrick` Mode & Simplified `Points` in `Functions/Move Tag`:** Moves vector pieces independently within a single ASS line (ideal inside `Basics/Builder`) by animating `\xshad` and `\yshad`, with flat `x1, y1, x2, y2...` lists and direct variable/formula evaluation.
* **New `Relative2` Anchor Mode:** Preserves each piece's relative geometry without injecting `\org`, available across all piece-splitting and particle nodes.
* **Complete Overhaul of `Basics/Math`:** Rebuilt from the ground up with 5 categories (expandable `basic`, `numeric`, `sequence`, `geometry`, `algebra`, `data`) and 27 operations aligned with the classic `ke.math` standard.
* **Snappier, Smoother Previewer:** Faster source toggling between the base template and active Aegisub session via direct start-time seeking, background metadata pre-warming, animated aspect-ratio transitions, and a loading overlay held until the first real video frame is decoded.
* **Original Line Tag & Property Preservation:** Native support for inheriting kinetic tags from Aegisub in `Loops/Main Loop`, querying original per-line properties (`line.<prop>_org`), and accessing the full Dark Tags catalogue in `Basics/MultiTag`.

---

### What's New

* **`Basics/Builder` Node:**
  * Supports `text` (`splitter`, `multi`, `custom`) and `shape` (`subpaths`, `islands`, `raw_subpaths`) modes with `auto`, `embedded_pos`, `advance`, and `stack` spatial layouts.
  * Dynamically expandable inputs (`In1`, `In2`...) via `+` / `-` buttons, a dedicated `Tags` port with style precedence, and an optional `Reset \r` toggle that preserves upstream `\t` animations across segments.
* **`Functions/Move Tag` — `Shadtrick` Mode:**
  * Hides fill and border (`\1a&HFF&\3a&HFF&\ko0`) and animates relative displacements via `\xshad`, `\yshad`, and `\t(...)`, preserving 3-decimal precision (`0.001` minimum) whilst respecting external shadow colour tags (`\4c`).
  * Emits strictly direct transitions between waypoints (`N - 1` `\t(...)` transforms for `N` points) without redundant intermediate subdivisions, relying on native per-segment interpolation.
  * Omits `\shad`, `\pos`, `\fscx`/`\fscy`, and `\p1...\p0` spacers, preventing conflicts inside `Basics/Builder`.
  * Mode-specific inputs: `Shadtrick` exposes only its relevant fields (removing `Amplitude X`, `Amplitude Y`, and `Step (px)`), defaulting to `0.001, 0.001` when `Points` is left empty.
* **New `Relative2` Anchor Mode:**
  * Available in `Shape/Slicer`, `Shape/Array`, `Shape/Union & Divide`, `Shape/Concentric Borders`, and `Functions/Particles`.
  * Keeps piece coordinates relative to the parent origin identically to `Relative`, whilst omitting automatic `\org` injection so rotation and scaling pivots are not locked to the parent centre.
* **`Basics/Math` Redesign:**
  * New expandable `basic` category (set as default on node creation) with 9 arithmetic and reduction operations (`add`, `sub`, `mul`, `div`, `mod`, `pow`, `min`, `max`, `avg`).
  * Dedicated `numeric`, `sequence`, `geometry`, `algebra`, and `data` categories with cyclic header pills and native checkboxes.
* **`Anchor` and `Smoothing` Controls in `Audio/Waveform`:**
  * New cyclic **Anchor** button (`Center`, `Origin`, `Relative`, `Absolute`, defaulting to `"center"`), translating generated vector paths and coordinate arrays uniformly relative to the waveform bounding box.
  * New **Smoothing** field (`0.0` to `0.95`, default `"0.2"`) applying an exponential low-pass filter to smooth abrupt jumps across samples and spectral bands in all modes.
* **Original Line Tag & Property Preservation:**
  * New **Preserve Tags** toggle in `Loops/Main Loop` to carry over static and kinetic tags (`\move`, `\t`, `\fad`, `\fade`) with accurate temporal remapping into the effect window.
  * Direct access in scripts and expressions to `line.<prop>_org` / `l.<prop>_org` and Dark Tag `!line.<prop>!` syntax.
* **Full Dark Tags Catalogue in `Basics/MultiTag`:** Integrated all Dark Tag families (compound tags, 3D auto-origin, style restoration, ratios, and stochastic `*R` tags) with one-click modal selection from the node header.
* **Automatic Rectangular Clip Optimisation (`\clip` / `\iclip`):** Shape and clipping nodes automatically emit compact 2-point `\clip(x1,y1,x2,y2)` tags whenever the resulting geometry is an axis-aligned rectangle, improving libass/VSFilter rendering efficiency.

---

### Improvements & Ergonomics

* **Flat Comma-Separated `Points` (`x1, y1, x2, y2...`) with Expressions:** In `Functions/Move Tag` (`Waypoints` and `Shadtrick`), `Points` now uses a flat comma-separated list and evaluates context variables and arithmetic expressions directly (working seamlessly with `Basics/Dynamic Format` and `Variables/Define Vars`).
* **Independent Random Calls & Variable Grouping:** Every `R(...)` or `by.<iter>.R*(...)` call inside an expression (even multiple calls on the same line, such as `R(10) + R(10) + R(10)`) or across distinct variables evaluates independently; assigning a random expression to a variable remains the canonical way to share the same value within an iteration.
* **Source Switching & Seeking in `System/Previewer`:**
  * Eliminated redundant double-seek overhead when switching sources and held the blurred loading overlay until the first frame at the target timestamp is painted, preventing leftover grey frames on first load.
  * Smooth animated aspect-ratio adjustment when switching in both directions between the base template and Aegisub.
  * Responsive timeline scrubbing without video or subtitle stalls, plus a responsive top toolbar for compact windows.
  * Accurate `±2 s` playback window filtering that excludes empty or non-renderable lines, alongside unified scope resolution (`Sel. Lines`, `All Lines`, `Style Lines`) in `System/Output`.
* **macOS (Apple Silicon) Performance Gains:** Disk-cached font indexing, optimised font metrics, and linear text layout calculations significantly accelerate startup and live previewing.
* **Scripting, Expressions & Diagnostics:**
  * Unified evaluation and linting of quoted and unquoted ternary expressions and ASS tags in `Variables/Define Vars` and `Basics/String`.
  * Immediate dynamic updates for `fx.start_time`, `fx.end_time`, and `fx.dur` after modifying `st`/`et` inside `System/Script Code` (Python and Lua), with strict branch isolation across multiple `System/Output` nodes.
  * Autocompletion and static graph validation synchronised across all 69 system nodes, plus calibrated workload indicators driven by real telemetry metrics.

---

### Bug Fixes

* **Sub-loop `by.bu_i` Randomness in `Basics/Builder` & Variable Isolation:** Resolved an issue where `by.bu_i.R*(...)` produced identical values across all pieces in `Basics/Builder` when pre-defined in `Variables/Define Vars`, and fixed separate variables with identical random expressions returning the same value instead of independent draws.
* **Positioning with `Preserve Tags` and `\move`:** Fixed an issue where preserving a line's original `\pos` alongside a graph-generated `\move` overrode the motion and collapsed shapes onto the original static position.
* **ASS Centisecond Timing Quantisation:** Unified temporal rounding between exported `Start`/`End` timestamps and kinetic tag remapping (`\move`, `\fad`, `\t`), eliminating alternating single-frame jitter in stepped and FBF effects.
* **Canvas & Node Controls:**
  * Cleared leftover yellow slot highlights on the canvas after releasing link drags.
  * Fixed dynamic width calculation when switching modes in `Basics/Math`, preventing clipped controls prior to the first redraw.
  * Resolved an off-by-one swatch preview indexing issue between `Basics/Color Picker` and `Basics/MultiTag`, and preserved uppercase stochastic `*R` tag names.
* **Previewer Persistence & Playback:**
  * Fixed cases where `System/Previewer` lost its saved aspect ratio or unpinned floating state, or remained hidden after template reloads and cold restarts.
  * Restored rendering stability on Windows and Linux and updated automatic FFmpeg download resolution.
* **2D Geometry & Ordering:**
  * Preserved non-numeric ordering modes (`cw`, `ccw`, `rand`) in `Shape/Slicer`, restricted `path`/`path_inv` ordering to path-guided nodes, standardised `Bleed` and `Pre-Offset` properties across all 23 `Slicer` modes, and fixed the return Bézier curve in `jigsaw` cuts.

---

### Compatibility & Migration Notes

> [!NOTE]
> * **Consolidation into `Basics/Builder`:** The legacy `merge` mode in `Basics/Concatenate` (which retains `basic` and `zip` with a standalone separator selector) and `Fusion Tags` mode in `Shape/Union & Divide` have been retired. Single-line composite workflows are now handled canonically by `Basics/Builder`.
> * **`Functions/Move Tag` (`Points`):** Semicolon (`;`) and newline delimiters in `Points` have been retired in favour of the flat comma-separated format (`x1, y1, x2, y2...`).
> * **`Audio/Waveform`:** `Anchor` now defaults to `"center"` and `Smoothing` defaults to `"0.2"`.
> * **`Basics/Math`:** Existing templates using retired legacy operations should be updated to the 5-category, 27-operation `ke.math` specification (with expandable `basic` mode as default).
