# System

The **System** category comprises master nodes for terminal event assembly, real-time interactive previewing via WebAssembly (JASSUB/libass), Python and Lua scripting, and execution performance diagnostics.

---

## 1. Node `System/Output` (Terminal Assembler and ASS Emitter)

* **Canonical Category:** `System` (UI: *System / Output*)
* **Purpose:** Mandatory terminal node of the generation graph. Compiles processed event streams, resolves style and typographic scale precedences, manages hierarchical queue sequencing, and writes resulting dialogue lines into Aegisub's active subtitle script.

![System/Output](img/output.png)

### 1.1. Header Mode Combos
1. **`[2.1] Apply to` (`apply_to`):** Scope of dialogue lines in Aegisub to which the graph is applied:
   * `Sel. Lines` (*Selected Lines*): Processes exclusively lines currently selected in the Aegisub grid.
   * `Style Lines`: Processes lines whose style matches that of the active selection.
   * `All Lines`: Processes every dialogue line in the subtitle file.

### 1.2. Input Ports (*Inputs*)
1. **`Loop / Domain`:** Primary execution flow signal originating from the terminal node of the active branch (`Main Loop`, `MaxLoop`, `Script Code`).
2. **`Layer`:** Target ASS layer number where the generated dialogue line will be placed (e.g. `0`, `1`, `5`). If unwired, inherits the original dialogue line layer.
3. **`Start Time`:** Override start time in milliseconds. If unwired, defaults to the active context's calculated `start_time`.
4. **`End Time`:** Override end time in milliseconds. If unwired, defaults to the active context's calculated `end_time`.
5. **`Tags`:** Consolidated ASS tag block (`{\pos...\1c...\blur...}`). Serialised at the beginning of the dialogue event.
6. **`Return`:** Textual payload of the event: plain dialogue text or ASSdraw vector paths (`m ... l ... b ...`).
7. **`Queue ID`:** Optional alphanumeric identifier to group generated lines into a post-rendering logical queue. Written directly into the `Actor` field of each `Dialogue:` line.
8. **`Queue Order`:** Integer numeric emission priority for the queue to determine ordering in the subtitle document.

### 1.3. Controls and Body Properties
1. **`[2.2] Queue ID` (`queue_id`):** Default queue identifier if the input port remains unwired (default: `""` $\to$ `"default"` queue).
2. **`[2.3] Queue Order` (`queue_order`):** Default numeric emission priority if the input port remains unwired (default: `""` $\to$ order `0`).
3. **`origin_align`:** Numeric origin alignment for anchor calculation (default: `5` / Centre).

### 1.4. Output Ports (*Outputs*)
1. **`[1.1] Preview`:** Dedicated diagnostic output transmitting compiled events directly to `System/Previewer` for interactive canvas playback.

### 1.5. Algorithmic Behaviour and ASS Compilation
During compilation:
1. Validates `start_time` and `end_time` timestamps, ensuring $t_{\text{end}} \ge t_{\text{start}}$.
2. Merges tags received via `Tags`, stripping direct syntax duplicates.
3. **Scale Precedence Hierarchy (`\fscx`/`\fscy`):**
   To prevent libass or VSFilter from applying unintended distortions to vector paths defined in absolute coordinates when the base ASS style specifies a scale other than 100%, the engine enforces a strict 4-tier hierarchy:
   * **Tier 1 (Plain text or karaoke):** The node injects no scale tags; text naturally inherits the scale defined in the ASS style.
   * **Tier 2 (ASS Style):** Sets the baseline typographic scale.
   * **Tier 3 (Vector shapes):** If the emitted payload is a vector path (`\p1`, ASSdraw `m ...`), the engine automatically injects `\fscx100` and `\fscy100` to neutralise style scaling and preserve 1:1 on-screen proportions.
   * **Tier 4 (Explicit user tag):** If the user explicitly connects or types `\fscx` or `\fscy` into the `Tags` port, this override takes precedence over the neutral default.
4. **Stateful Style Tracker (`ActiveStyleState`):**
   * **Pre-check fast validation:** If the dialogue line contains no override tags (simple karaoke like `{\k50}`), the engine bypasses state machine allocations to speed up plain line processing.
   * **Sequential syllable-level state machine:** When the line contains override tags (`\pos`, `\an`, `\fs`, `\fscx`, `\fscy`, `\fsp`, `\b`, `\i`, `\bord`, `\shad`, `\1c`..`\4c`, `\alpha`, `\1a`..`\4a`, `\frz`, `\r`), the engine cumulatively tracks modifications block by block.
   * **Dynamic typographic measurement:** Unit dimensions (`width`, `height`) are evaluated through the font engine taking active font size and format overrides into account.
   * **Line kinematics and anchor positioning:** An explicit `\pos(x,y)` anchors the dialogue line to those coordinates based on effective alignment `\an`, projecting derived coordinates onto descendant syllables and characters.
   * **Unit inheritance:** Context units (`syl`, `char`, `word`, `line`) expose style properties with cascading fallback: `Unit -> Line -> Style -> Defaults`.
   * **Typographic Spacing Calculation:** When an ASS style defines `Spacing > 0` or an inline `\fsp` tag is present, the engine computes the effective horizontal spacing increment ($S_{\text{eff}} = \text{Spacing} \times \frac{\text{ScaleX}}{100} \times \text{FactorX}$). This increment is applied uniformly between adjacent syllables and individual child glyphs (`char.left`, `char.center`, `char.right`), preserving libass/VSFilter alignment.
5. Serialises the final line into standard ASS dialogue format, assigning `Queue ID` to the `Actor` field:
   $$\texttt{Dialogue: } \text{Layer}, \, t_{\text{start}}, \, t_{\text{end}}, \, \text{Style}, \, \mathbf{Queue\_ID}, \, \text{MarginL}, \, \text{MarginR}, \, \text{MarginV}, \, \text{Effect}, \, \texttt{\{Tags\}} \text{Return}$$
6. **Queue Architecture and Global ASS Output Sequencing:**
   * **Output branch isolation:** Each `Output` node evaluates its branch independently with its own context container, without sharing variables or kinematic states with other terminal nodes.
   * **Global queue sequencing:** Once all branches complete event generation, lines are grouped by `Queue ID` and written into the ASS document using the sorting key:
     $$\text{SortKey}(Q) = \left(\min_{l \in Q}(\text{queue\_order}_l), \, \text{qid}\right)$$
     * **1. Numeric Priority:** Queues with lower numeric `Queue Order` are emitted first.
     * **2. Alphabetical Tiebreaker:** If two or more queues share the identical order, they are sorted alphabetically by `Queue ID`.
     * **3. Default Queue:** Omitted identifiers default to the `"default"` queue.
     * **4. Intra-Queue Order:** Within each queue, lines maintain original event sequence:
       $$\text{SortKey}(l) = (\text{queue\_order}_l, \, \text{line\_idx}_l)$$

### 1.6. Synergies and Best Practices
* **Parallel Multilayer Rendering:** Use separate `Output` nodes to isolate layers (e.g. Layer 0 for shadows with `Queue Order = 1`, Layer 1 for the main text with `Queue Order = 2`).
* **Actor Production Tagging:** Use descriptive identifiers in `Queue ID` (such as `"FX_Outline"` or `"FX_Body"`) to filter, inspect, and toggle generated lines directly within the Aegisub grid.

---

## 2. Node `System/Previewer` (WebAssembly Real-Time Player)

* **Canonical Category:** `System` (UI: *System / Previewer*)
* **Purpose:** Real-time video and subtitle preview player accelerated via WebAssembly (JASSUB/libass), clamped strictly to the active effect time window without requiring pre-rendering transcode delays.

![System/Previewer](img/previewer.png)

### 2.1. Input Ports (*Inputs*)
1. **`Output`:** Signal connection from the `Preview` port of one or more `Output` nodes to composite multilayer previews simultaneously.

### 2.2. Header Actions
1. **`[1.1] Source Toggle`:**
   * **Base Preset (CD Icon / `preview_base.ass`):** Isolated sandbox environment with preloaded video and template.
   * **Active Aegisub Project (Aegisub Icon):** Loads video, audio, styles, and timing from the active Aegisub session.
2. **`[1.2] Pin / Detach Button`:**
   * Detaches the player into a floating overlay window to preserve visual reference while navigating the canvas.
3. **`[1.3] Refresh Button`:**
   * Recompiles branches wired to `Output`, updates the subtitle track in JASSUB/libass, and executes telemetry profiling over generated lines.
   * **Scene Coexistence:** In the viewport, only original lines replaced by the `Output` scope (`Sel. Lines`, `Style Lines`, `All Lines`) are commented out, leaving coexisting dialogue and signs visible.
4. **`[1.4] Hardsub Render Button (FFmpeg Export)`:**
   * Opens the export dialogue to burn subtitles (*hardsub*) into an encoded MP4 video file via FFmpeg. Transcoding runs strictly and exclusively upon triggering this action.

### 2.3. Transport Bar and Playback Controls
1. **`[2.1] Relative Scrubber Bar:`** Draggable timeline mapped to effect duration ($0 \dots T_{\text{dur}}$), synchronised via frame callbacks (`requestAnimationFrame`).
2. **`[2.2] Relative Timecode Display:`** Displays current position and total duration in `MM:SS` format.
3. **`[2.3] Volume Controls:`** Mute toggle button and audio gain slider.
4. **`[2.4] Previous Frame (-1 Frame):`** Steps back exactly one frame.
5. **`[2.5] Jump Backward (-10s):`** Shifts playback 10 seconds backwards within the effect window.
6. **`[2.6] Play / Pause Toggle:`** Continuous playback toggle.
7. **`[2.7] Jump Forward (+10s):`** Shifts playback 10 seconds forwards within the effect window.
8. **`[2.8] Next Frame (+1 Frame):`** Steps forward exactly one frame.
9. **`[2.9] Settings Menu:`** Loop playback toggle and playback speed selector ($0.25\times, 0.5\times, 1.0\times, 1.5\times, 2.0\times$).
10. **`[2.10] Fullscreen Toggle:`** Maximises video viewport.
11. **`[2.11] Solid Neutral Grey Background:`** Standalone audio tracks render over a neutral grey backdrop (`#2a2a2a`) for optimal subtitle contrast.
12. **`[2.12] Thermal Heatmap:`**
    * Plots per-frame rendering cost of generated lines via a spline curve, colour-coded against the frame budget ($\text{Budget}_{\text{ms}} = 1000 / \text{FPS}$): cyan (low load), green (moderate), orange (near limit), and red (budget exceeded $>100\%$).
    * Hovering over the seekbar vertically expands the curve, displaying the reference grid, latency readouts (`MM:SS.mmm · X.X ms`), and direct **`TELEMETRY ↗`** shortcut.

### 2.4. Viewport Navigation (Zoom and Pan)
1. **Mouse Wheel Focal Zoom:** Zooms in or out centring on the pointer position (from $1.0\times$ to $8.0\times$).
2. **Middle Mouse Button Pan:** Dragging with the middle button navigates the magnified viewport.
3. **'R' Key Reset:** Pressing `R` over the player resets zoom to $1.0\times$ and centres the viewport.

### 2.5. Docking with the `Telemetry` Panel
When opening the **`Telemetry`** diagnostic panel from the heatmap:
1. **Live Player Transfer:** The active player instance transfers to the diagnostic panel preserving current frame, zoom level, and playback state. Closing the panel docks the player back onto the canvas.
2. **Bidirectional Seeking:** Scrubbing charts or clicking critical events immediately seeks the video player to that frame.

### 2.6. Synergies and Best Practices
* **Immediate Effect Validation:** Wire the `Preview` output to verify timing and aesthetics prior to writing lines into Aegisub.
* **Bottleneck Detection:** Observe heatmap peaks to identify excessive blur (`\blur`) or complex clip masks (`\clip`).

---

## 3. Node `System/Script Code` (Embedded Python & Lua Code Execution)

* **Canonical Category:** `System` (UI: *System / Script Code*)
* **Purpose:** Executes inline code snippets in Python 3.12 or Lua 5.1/LuaJIT within the graph flow, with bidirectional access to ASS context variables and tag utility functions.

![System/Script Code](img/script_code.png)

### 3.1. Header Mode Combos
1. **`[1.1] Language` (`language`):** Execution engine:
   * `Python`: Native Python 3.12 environment with access to standard modules (`math`, `random`, `re`).
   * `Lua`: Standard Lua scripting via Lupa/LuaJIT with compatibility for traditional Aegisub macro syntax.

### 3.2. Input and Output Ports
1. **`Loop In`:** Execution flow input.
2. **`In1`, `In2`, $\dots$, `InN`:** Dynamic data input sockets accessible inside the script via variables `in1`, `in2`, etc.
3. **`[2.1] Loop Out`:** Propagates flow to downstream nodes.
4. **`[2.2] Result`:** Emits the payload assigned to `result` (text, ASS tags, or vector paths).

### 3.3. Body Properties
1. **`script`:** Source code to execute (default: `result = 'Hello Pyxis ' + str(in1 if in1 else syl.text)`).
2. **`inputs_count`:** Number of dynamic input sockets (default: `2`).

### 3.4. In-Scope Variables and Functions

In both Python and Lua, scripts have access to the following entities:

| Variable / Object | Description | Primary Attributes |
| :--- | :--- | :--- |
| `syl` | Active context syllable | `x, y, center, middle, left, right, top, bottom, start_time, end_time, dur, text, text_stripped, i, n, prev, next, is_first, is_last, has_prev, has_next, ink` |
| `char` | Active context character | `x, y, center, middle, left, top, start_time, end_time, dur, text, i, n, prev, next, is_first, is_last, has_prev, has_next, ink` |
| `word` | Active context word | `x, y, center, start_time, end_time, dur, text, i, n, prev, next, is_first, is_last, has_prev, has_next, ink` |
| `line` / `l` | Complete dialogue line | `text, raw_text, style, layer, start_time, end_time, duration, margin_l, margin_r, margin_v, actor, effect, ink` |
| `prev` / `next` | Preceding and succeeding neighbor units | Access to metrics and text of adjacent units (`prev.text`, `prev.dur`, `prev.x`, `next.x`) |
| `is_first` / `is_last` | Boolean boundary flags | `True` if unit is first / last in sequence |
| `has_prev` / `has_next`| Boolean neighbor flags | `True` if adjacent neighbor exists |
| `ink` | True ink contour metrics | `ink.width`, `ink.height`, `ink.center`, `ink.middle`, `ink.left`, `ink.right`, `ink.top`, `ink.bottom` |
| `fx` | Kinematic override structure | `pos_x, pos_y, org_x, org_y, start_time, end_time, dur, align, i, n` |
| `in1`, `in2`, $\dots$ | Connected data inputs | Values received at ports `In1`, `In2`, etc. |
| `outputs` / `out` | Multiple outputs | Assignment by name (`outputs["Custom"] = val`) or index (`out2 = val`). |
| `result` | Primary output | Content emitted through the `Result` port. |

#### Injected Utility Functions:
* **ASS Tag Constructors:** `pos(x,y)`, `move(x1,y1,x2,y2[,t1,t2])`, `org(x,y)`, `fad(in,out)`, `fade(...)`, `clip(shp)`, `iclip(shp)`, `c1(col)`, `c2(col)`, `c3(col)`, `c4(col)`, `alpha(a)`, `trans(tags)`, `fscx(v)`, `fscy(v)`, `frz(v)`, `blur(v)`, `bord(v)`, `shad(v)`.
* **Interpolation and Mathematics:** `clamp(v,min,max)`, `lerp(a,b,t)`, `map_range(v,in_min,in_max,out_min,out_max)`, `ease_in(t)`, `ease_out(t)`, `ease_in_out(t)`, `cubic_in(t)`, `cubic_out(t)`, `elastic(t)`, `bounce(t)`, `back(t)`.
* **Periodic Waves:** `sine_wave(t,freq,amp,offset)`, `square_wave(...)`, `triangle_wave(...)`, `sawtooth_wave(...)`.
* **Time Formats:** `time_to_frame(ms,fps)`, `duration(obj)`, `parse_ass_time(str)`, `format_ass_time(ms)`, `strip_tags(txt)`.

---

## 4. Node `System/Benchmark Math` (Performance Diagnostics)

* **Canonical Category:** `System` (UI: *System / Benchmark Math*)
* **Purpose:** Measures computational performance by executing intensive mathematical algorithms (trigonometry, prime sieves, or matrix multiplication) and reporting elapsed time in milliseconds.

![System/Benchmark Math](img/benchmark_math.png)

### 4.1. Input Ports (*Inputs*)
1. **`Iterations`:** Number of iterations to execute (default: `10000`). If unwired, evaluates the internal property.

### 4.2. Controls and Body Properties
1. **`[2.1] Complexity` (`complexity`):** Test algorithm:
   * `Heavy Math (Trig + Sqrt)`: Loops of trigonometric functions ($\sin, \cos$) combined with square roots ($\sqrt{x}$).
   * `Prime Sieve`: Prime number checking and sieving algorithm.
   * `Matrix Mult`: In-memory $25 \times 25$ matrix multiplication.
2. **`[2.2] Iterations` (`iterations`):** Repetition count (default: `10000`).

### 4.3. Output Ports (*Outputs*)
1. **`[1.1] Out`:** String containing input data received or elapsed time summary formatted as `[Bench: X.XXms]`.
2. **`[1.2] Time ms`:** Total calculation time in milliseconds measured with high-resolution precision (`time.perf_counter()`).

### 4.4. Synergies and Best Practices
* **Efficiency Profiling:** Insert `Benchmark Math` into large graphs to benchmark host execution speed before and after optimisations using `Basics/Once`.
