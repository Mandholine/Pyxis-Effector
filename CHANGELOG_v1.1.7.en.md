# Pyxis Effector v1.1.6 — Release Notes

Release notes for the **v1.1.6** release cycle of Pyxis Effector. This milestone consolidates native cross-platform architecture, significantly accelerates the node generation engine, revamps the interactive preview system with dual-engine rendering modes, and perfects geometric fidelity in typographic vector workflows.

---

### Highlights

* **100% Native Cross-Platform Architecture:** Complete, independent support for Windows, Linux, and macOS without emulation layers, featuring native FreeType font metrics, optimised C99 telemetry, and seamless media tool provisioning.
* **Dual Interactive Preview (Typesetting vs mpv):** A new visual engine switcher in the Previewer node allowing instantaneous toggling between traditional 1:1 pixel-perfect Aegisub/VSFilter typesetting fidelity and high-DPI isotropic mpv rendering with automatic anamorphic compensation.
* **Substantial Graph Performance Gains (OPT-01 to OPT-05):** Comprehensive engine optimisation delivering more than a 75% reduction in processing time across dense loops and kinetic typography graphs (exceeding 200 lines per second on a single thread).
* **Pure Typographic Geometry without Compounding Scale:** Font vector contours are now generated at 100% base scale, delegating anamorphic aspect scaling exclusively to the ASS renderer and eliminating distortions in slicers and extrusions.

---

### What's New

* **Dual Rendering Mode in Previewer:** A quick-toggle selector button in the `System/Previewer` node header, unpinned floating window, and fullscreen mode enables seamless switching between:
  * **Typesetting Mode:** 1:1 identical to Aegisub and VSFilter rasterisation at script PlayRes dimensions.
  * **mpv Mode:** Screen-space High-DPI vector rasterisation maintaining crisp outlines, smooth gradients, and automatic pixel aspect ratio correction (PAR/DAR).
* **Automated One-Click Multimedia Provisioning:** The previewer proactively detects missing media dependencies and presents a non-intrusive dialogue to download and configure native binaries in the background with a progress indicator, requiring zero administrator privileges.
* **Island Separation in Shape/Union & Divide:** Added the **Split Mode** selector (*Islands* vs *Path*) in Fusion (Tags) mode, allowing contiguous slices from `Shape/Slicer` to retain their individual identity for independent colouring and styling without undesirable boolean merging.
* **Non-Linear Acceleration in Geometric Interpolation:** New **accel** input socket and property in `Shape/Union & Divide` for modulating vector and colour transitions with smooth power curves (*ease-in* and *ease-out*).
* **Base Visibility Control in Functions/Animation:** Added the **Base** parameter in Alpha mode, allowing subtitle designers to set a base transparency level for active frames without forcing 100% opacity.
* **Expanded Multi-Channel Palette in Functions/Color Gradient:** Introduced 12 multi-channel colour combinations (`\12c`, `\13c`, `\14c`, `\23c`, `\24c`, `\34c`, `\123c`, `\124c`, `\134c`, `\234c`, `\1234c`, `\c`) with direct generation of clean, libass-compliant ASS tags.
* **Contour Erosion in Shape/Manipulator:** Full support for negative **Offset Border** values in both Borders and Matrix modes, enabling fine perimeter erosion and thinning of intricate vector shapes with interior holes, dissolving smoothly to empty paths upon full erosion.

---

### Improvements & Ergonomics

* **Ergonomic Redesign of Inline Text Inputs:** The `Basics/String` and `Basics/Number` nodes have been refined for predictable and intuitive editing:
  * Compact default height (60 px) with automatic text wrapping to node boundaries.
  * Keyboard shortcut `Shift+Enter` for inserting deliberate visual line breaks to format multi-line lists or expressions without prematurely confirming input.
  * Exact 1:1 sub-pixel visual parity in font size, padding, and alignment between canvas resting mode and interactive inline editing.
  * Smooth mouse-wheel scrolling and minimalist scrollbars without node box deformation.
  * The `Basics/Number` node now initialises with an empty field by default, speeding up direct value entry.
* **Variable Sovereignty in Define Vars:** Temporal attributes (`st`, `et`, `dur`), visual layers (`layer`), and typographic alignment (`align`) can now be modified directly from `Variables/Define Vars`. These follow a four-tier canonical precedence hierarchy (`Base Unit < Define Vars < Explicit Output < Tags`), strictly shielding original unit metrics against accidental mutation.
* **Tag Preservation Across Geometric Nodes:** Transformation, clipping, and vector generator nodes now isolate, preserve, and cleanly reintegrate upstream ASS tags, allowing complex effect chaining without loss of colours, rotations, or nested animations.
* **Isolated Hierarchical Randomness:** Calls to scoped pseudorandom helpers (`by.j`, `by.char.R`) maintain independent stochastic sequences across distinct characters without accidental collisions.
* **Transparent Media Adaptation:** Incompatible audio streams (such as AC-3 or DTS) are automatically converted in the background into integrated, browser-supported formats, preventing playback stalls or muted audio.
* **Seamless Fullscreen Recovery:** Eliminated black screens and viewport desynchronisation when toggling between canvas workspace and fullscreen preview.

---

### Bug Fixes

* **Resolution of Compounding Scale on Vector Contours:** Fixed an issue where text-to-vector paths pre-baked font style scaling into geometry and subsequently underwent secondary scaling by the ASS renderer, causing vector extrusions and slicers to render noticeably narrower than typographic text.
* **Exact Colour Parity with Aegisub:** Synchronised YCbCr matrix handling and `ScaledBorderAndShadow` flags in the preview engine, eliminating hue shifts and scaling discrepancies in borders or shadows when zooming.
* **Floating-Point Stability:** Mitigated IEEE-754 precision residuals and suppressed scientific notation in coordinate strings, preventing particles and text elements from snapping to coordinates (0, 0).
* **Shape Library Namespace Enforcement:** Library vector presets now strictly require the canonical `shape.` prefix, preventing plain words matching shape names (e.g. "heart", "star", "diamond") from being misclassified as geometric shapes.
* **Balanced Commas in Nested Functions:** The `Basics/Number` node and static graph linter now correctly process expressions containing multi-argument mathematical helpers (such as `clamp`, `lerp`, or random ranges `R(min, max)`) without raising false syntax errors.
* **Custom Node Size Retention:** Nodes with user-adjusted dimensions (such as `Functions/Animation`) retain their custom size across mode switches and property edits without collapsing to default dimensions.

---

### Compatibility & Migration Notes

> [!NOTE]
> * **Library Shapes:** Any references to built-in vector shapes within templates or expressions must use the canonical `shape.<name>` prefix (for example, `shape.star` or `shape.heart`), ensuring that standard lyric text remains vectorised faithfully.
> * **Vector Extrusion Scaling:** Following the removal of double pre-scaling in `FontVectorEngine`, existing templates that incorporated manual scale-correction factors to compensate for extrusion narrowing will now align pixel-for-pixel at native 100% style scale.
