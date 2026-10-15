# Interface Anatomy

The Pyxis Effector interface is organised as a modular node-graph workspace structured around a primary editing canvas and peripheral control panels.

---

## 1. General Workspace Layout

The application's main window consists of four functional zones:

```
+-------------------------------------------------------------------------------+
| [1] TOP BAR                                                                   |
+-------------------------------------------------------------------------------+
|                                                                               |
|                                                                               |
| [2] CANVAS WORKSPACE                                                          |
|     (Nodes, connection ports, data cables, and loop/flow links)               |
|                                                                               |
|                                                                               |
|                                                        +----------------------+
| [3] FLOATING CANVAS TOOLBAR                            | [4] TOAST SYSTEM     |
+-------------------------------------------------------------------------------+
```

1. **Top Bar:** Persistence management (save/export), template library, global preferences, and layer generation.
2. **Canvas Workspace:** Two-dimensional editing area where graph nodes are added, organised, and interconnected.
3. **Floating Canvas Toolbar:** Quick-access tools for navigation, zoom level, camera centring, and history actions (*undo/redo*).
4. **Toast Notification System:** Non-intrusive contextual alerts in the bottom-right corner displaying status, diagnostics, and processing times.

---

## 2. Top Bar and Generation Controls

Fixed permanently along the top edge of the window:

```
+-------------------------------------------------------------------------------------------------+
| [1] Brand & Version | [2] Save | [3] Save as... | [4] Library | [5] Settings | [6] Generate Layers |
+-------------------------------------------------------------------------------------------------+
```

1. **Version Identifier:**
   * Engine brand name and active version badge (`v1.1.4`).

2. **Save (`Save` / `Ctrl+S`):**
   * Saves changes directly to the currently opened template or project file.

3. **Save As (`Save as...`):**
   * Exports the entire graph topology to an external `.json` file for backup or distribution.

4. **Template Library (`Library`):**
   * Opens the modal dialogue to search, tag, categorise, and load preset or user-created templates. Supports filtering by Favourites, Recents, and System Presets.

5. **Quick Save (`Quick Save`):**
   * Activates when modifying a template loaded from the library to overwrite it in a single click.

6. **Environment Settings (`Settings`):**
   * Configuration for canvas visual themes, background backdrop (active Aegisub video, reference image, or solid colour), language localisation preferences, and hardware acceleration options.

7. **Primary Layer Generation Button (`Generate Layers`):**
   * Compiles the graph and emits the newly generated subtitle dialogue lines directly into Aegisub's active ASS script. Features an integrated progress bar.

8. **Workload Estimation Card:**
   * Automatically displays upon hovering over **Generate Layers**:
     * **Lines to generate:** Estimated count of resulting ASS dialogue events that will be written into the script.
     * **Input lines:** Total number of subtitle lines currently selected in Aegisub scheduled for processing.
     * **Base units:** Total breakdown of syllables, words, or characters according to the active iterator in `Main Loop`.
     * **Heavy Load Warning:** Preventive visual alert if combined graph complexity exceeds recommended computational thresholds.

---

## 3. Canvas Workspace

Two-dimensional editing space providing free camera navigation, scaling, and multi-selection.

### 3.1. Visual Layer Architecture (*Z-Index Stacking*)
1. **Backdrop Layer:** Neutral background, static reference image, or project video frame loaded from Aegisub for spatial alignment.
2. **Main Node Canvas Layer (`#node_canvas`):** Renders node containers, titles, connection ports, text fields, and interactive widgets.
3. **Foreground & Connection Layer (`#node_canvas_fg`):** Renders connecting cable Bézier curves, multi-selection bounding boxes, and magnetic snapping alignment guides.

### 3.2. Floating Canvas Toolbar
Positioned in the bottom-left corner of the canvas:

1. **Undo (`Undo` / `Ctrl+Z`):** Reverts the most recent canvas modification.
2. **Redo (`Redo` / `Ctrl+Y`):** Restores the most recently undone action.
3. **Centre View (`Home` / `Reset View`):** Repositions the camera to centre all nodes within the viewport at an optimal zoom factor.
4. **Zoom In (`Zoom In` / `+`):** Increases magnification focused on the viewport centre.
5. **Zoom Out (`Zoom Out` / `-`):** Decreases magnification for a panoramic overview of the complete graph.
6. **Default Preset (`Default Preset`):** Resets the canvas to the initial standard graph skeleton (`Main Loop` $\to$ `Output`).

---

## 4. Structural Anatomy of a Node

Standard structure of node elements on the canvas:

```
+-------------------------------------------------------------+
| [1] HEADER: Node Title             [4] Mode Selector [v]    |
+-------------------------------------------------------------+
| [2] INPUTS & INLINE FIELDS            |  [3] OUTPUT PORTS   |
| (o) [ Loop In                   ]     |        Loop Out (o) |
| (o) [ 100.0 (or placeholder)    ]     |          Result (o) |
| (o) [                           ]     |        Data Out (o) |
+-------------------------------------------------------------+
| [5] SELECTION BORDER & STATUS         [6] FOOTER / BADGES   |
+-------------------------------------------------------------+
```

1. **Node Header:**
   * Identification strip displaying the functional node title and its distinctive category theme colour.
   * Allows dragging the node across the canvas or collapsing/expanding its body via double-click.

2. **Input Ports with Integrated Inline Fields (*Inline Input Fields*):**
   * Each input slot on the left margin features a circular socket `(o)` and an **editable text field**.
   * **Placeholder Text:** When empty, displays in subdued text the parameter name and its default value (e.g. `Min`, `Max`, `Delay (ms)`).
   * **Cable vs Inline Precedence:** If a constant value or expression is typed into the field, the node evaluates that value. If a cable is connected to socket `(o)`, **the data transported by the cable takes absolute precedence**, overriding the inline field content.
   * **Exception (`Output`):** The terminal `Output` node contains no inline input fields; it displays direct assignment label badges (`Loop / Domain`, `Layer`, `Start Time`, etc.).

3. **Output Ports (*Outputs*, Right Margin):**
   * Circular socket connectors paired with the name of the emitted variable or data stream (`Loop Out`, `Data`, `Result`, `Shape Out`, `\t Out`, etc.).

4. **Header Mode Combos:**
   * Dropdown menus embedded into the top-right corner of the title bar.
   * Allow instant switching of node algorithms or behaviours (e.g. `syl / char / word / line` in `Main Loop`, `Normal / FBF` in `MaxLoop`, modes in `Manipulator`, or `Python / Lua` scripting environments in `Script Code`), dynamically reconfiguring body input slots.

5. **Selection Border & Status:**
   * Perimeter visual glow indicating when a node is actively selected or being edited.

6. **Footers and Context Badges (*Footers / Badges*):**
   * Displays iteration variables exposed to the execution context (`s_i, s_n` in Slicer, `a_i, a_n` in Array, `b_i, b_n` in Concentric Borders, `ish_i, ish_n` in IMG to Shape) or special node flags (`Single shape.`, `ALL`, `SELEC.`, `NO BLANK`).

---

## 5. Categories and Thematic Colour Coding

Pyxis organises its 67 nodes across 8 functional categories, each identified by a distinctive theme colour:

| Category | Functional Role | Example Nodes | Distinctive Colour |
| :--- | :--- | :--- | :--- |
| **`Basics`** | Numeric constants, strings, arithmetic operations, dynamic formatting, and basic routing. | `Math`, `Number`, `String`, `Text`, `Color Picker`, `MultiRandom`, `Concatenate`, `Once`, `Only` | Sky Blue (`#4A90E2`) |
| **`Shape`** | Vector primitives, boolean clipping (Clipper2), paths, affine transforms, morphing, and meshes. | `Library`, `Slicer`, `Manipulator`, `Transform`, `Filter`, `Concentric Borders`, `Stroke`, `Array`, `IMG to Shape` | Emerald Green (`#2ECC71`) |
| **`Time`** | Temporal synchronisation, accelerated timing (`\t`), parametric interpolation (`Ipol`), and offsets. | `Retime`, `Lead In`, `Lead Out`, `Synced`, `Middle 1/2`, `Loop 1/2`, `Ipol`, `Duration`, `Offset` | Golden Orange (`#F39C12`) |
| **`Functions`** | Tag modulators, wave oscillators, chromatic gradients, Bézier splines, and particle systems. | `Tag Manipulator`, `Tag Oscillator`, `Color Gradient`, `Clip Gradient`, `Bezier Curve`, `Particles`, `Text to Shape` | Violet Purple (`#9B59B6`) |
| **`Variables`** | ASS context variables, persistent key-value memory, and dynamic variable definitions. | `Sys Var`, `Define Vars`, `Get Var`, `Memory` | Turquoise (`#1ABC9C`) |
| **`Loops`** | Domain decomposition controllers, event multipliers, and modular steppers. | `Main Loop`, `MaxLoop`, `Module` | Coral Red (`#E74C3C`) |
| **`Audio`** | Spectral audio analysis (FFT), RMS/Peak envelope extraction, and vector waveforms. | `Modulator`, `Waveform` | Amber Yellow (`#F1C40F`) |
| **`System`** | Terminal ASS assembly, WASM-accelerated preview, custom code scripts, and math benchmarks. | `Output`, `Previewer`, `Script Code`, `Benchmark Math` | Steel Grey (`#7F8C8D`) |

---

## 6. Navigation, Gestures, and Keyboard Shortcuts

| Action | Mouse / Keyboard Control | Result |
| :--- | :--- | :--- |
| **Pan Canvas** | Middle Mouse Button (wheel click) or Right-click and drag | Pans the camera in any direction. |
| **Adjust Zoom** | Mouse Scroll Wheel | Smoothly zooms into or out of the canvas. |
| **Select / Move Node** | Left-click header and drag | Selects and repositions nodes individually. |
| **Box Multi-Selection** | Left-click and drag on empty canvas background | Draws a rectangular marquee selection box. |
| **Create Connection (Cable)** | Drag from output socket `(o)` to input socket `(o)` | Connects two compatible nodes with an elastic wire. |
| **Disconnect Port** | Click on a connected socket | Detaches and removes the connected cable. |
| **Node Spawn Context Menu** | Right-click on empty canvas background | Opens the node catalogue and quick search palette. |
| **Delete Nodes / Cables** | `Delete` or `Backspace` key | Removes all currently selected elements. |
| **Duplicate Nodes** | `Ctrl + D` or `Ctrl + C` / `Ctrl + V` | Clones selected nodes while preserving parameters. |
| **Save Project / Template** | `Ctrl + S` | Saves changes to the active graph. |
| **Undo / Redo** | `Ctrl + Z` / `Ctrl + Y` | Navigates the canvas modification history. |
| **Centre View on Graph** | `Home` key or Toolbar button | Centres all graph nodes within the viewport. |
| **Integrated Debug Console** | `F1` key (or `Esc` to close) | Opens real-time log console (operable even during window initialisation). |

---

## 7. Modal Windows and Dedicated Editors

1. **Script Code Editor (`Script Code`):**
   * Dedicated editing environment for Python and Lua scripting featuring syntax highlighting, line numbers, and live error validation (unclosed `end` blocks, missing colons, mismatched delimiters).
   * Reusable template manager to store and load custom automation functions.

2. **Colour Picker (`Color Picker`):**
   * HSV/RGB chromatic wheel with alpha channel slider, predefined swatch palettes, and direct export to ASS (`&HBBGGRR&`) and Web Hexadecimal (`#RRGGBB`) formats.

3. **Integrated Debug Console (`Debug Console` — `F1`):**
   * Real-time backend log viewer and diagnostic monitor accessible at any time (including during window initialisation).
   * Features live search filtering, auto-scroll toggle, clipboard copying, and log clearing without interrupting background execution or resizing the window.

4. **Template Library (`Library`):**
   * Catalogue with search by name or tags, node count previews, and safe loading with graph integrity verification.

5. **ASS Telemetry Panel and Workload Estimation (`Telemetry`):**
   * **Pre-Generation Workload Tooltip (`Generate Layers`):** Hovering over the generation button displays estimated output lines, **Sweep-Line Concurrency**, **Expansion Ratio**, **Estimated ASS Weight** (`KB`/`MB`), active subsystem badges (`FBF`, `Slicer`, `Particles`, `Audio`, `Script`), the latest telemetry summary, and a direct button to launch `Telemetry`.
   * **Telemetry Panel (16:9):** Diagnostic workspace arranged into three regions: live video viewport with per-frame telemetry HUD (top-left), frame budget gauge (`Frame Budget %`), KPI cards, and critical hotspots list (top-right), and a full-width unified multi-metric chart with bottom minimap and 2D navigation (`Scroll Wheel` X-zoom at cursor, `Ctrl/Shift + Wheel` Y-scale, `Middle Mouse Drag` 2D pan, `Left Click/Drag` video scrubbing, and `R`/`Home` to reset zoom).

---
