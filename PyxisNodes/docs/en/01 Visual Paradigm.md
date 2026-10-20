# Visual Paradigm

Pyxis Effector implements a directed-graph visual environment for processing and generating subtitles in the ASS (*Advanced SubStation Alpha*) format. The architecture decouples iteration flow, numerical computation, geometric transformations, and tag compilation into interconnected modular nodes.

---

## 1. Fundamental Principles of the Graph

The engine operates as a directed acyclic graph (DAG) where subtitle generation is structured through the interconnection of two link types:

```
[Main Loop] ---> [MaxLoop / Sub-iterator] ---> [Script / Transform] ---> [Output]
     │                                                ▲
     │ (Active Context)                               │ (Data evaluated on demand)
     └───────────────────> [Data Nodes / Tags] ───────┘
```

### 1.1. Flow and Execution Links (*Flow / Loop Links*)
1. **Sequence and Hierarchy:** Establish the temporal order and nesting depth in which effect branches are evaluated.
2. **Control Ports:** Interconnected via `Loop`, `Loop In`, and `Loop Out` ports.
3. **Evaluation Frequency:** Determine how many times each branch executes (per dialogue line, syllable, character, sub-particle, or video frame).
4. **Core Flow Nodes:**
   * `Main Loop` (Base domain iterator).
   * `MaxLoop` (Event multiplier or sub-frame *FBF* loop).
   * `Script Code` (Master Python / Lua code injection node).
   * `Output` (Terminal assembler and ASS dialogue emitter).

### 1.2. Data Links (*Data Links*)
1. **Information Types:** Transport numerical values (`float`/`int`), text strings, Cartesian coordinate pairs $(x, y)$, hexadecimal and ASS colour values (`&HBBGGRR&`), ASSdraw vector paths (`m ... l ... b ...`), and formatted ASS tag blocks (`{\pos...\t...\clip}`).
2. **On-Demand Evaluation (*Lazy Evaluation*):** A data node is only computed when the active execution flow requests its value during the current iteration. If a data branch is not connected to an active flow node, its calculation consumes neither CPU time nor memory.
3. **Dynamic Propagation:** Outputs can branch freely to multiple inputs without performance loss thanks to internal per-cycle memoisation.

---

## 2. Context Hierarchy and Data Lifecycle

Effect processing in Pyxis follows a five-phase hierarchical decomposition and transformation pipeline:

```
[1. Selection in Aegisub]
           │
           ▼
[2. Base Domain: Main Loop] (line / syl / word / char)
           │
           ▼
[3. Sub-domain: MaxLoop] (Clones, Particles, FBF Frames)
           │
           ▼
[4. Data Transformation] (Vectors, Tags, Audio, Interpolations)
           │
           ▼
[5. Terminal Assembly: Output] ───> [New Layered ASS Dialogue Lines]
```

### Phase 1: Selection and Input Parsing
The engine reads the ASS file dialogue lines loaded in Aegisub according to the target scope configured in `Output` (`apply_to`):
* `Sel. Lines`: Exclusively the lines selected in the Aegisub grid.
* `Style Lines`: All lines matching the style of the current selection.
* `All Lines`: The entirety of the dialogue lines in the subtitle file.

Each line is parsed by the syntactic engine and decomposed into its typographic spatial metrics and karaoke timing markers (`\k`, `\kf`, `\ko`).

### Phase 2: Iterative Domain Initialisation (`Main Loop`)
The `Main Loop` node establishes the base iteration unit (`iterator`):
* **`syl`:** Iterates syllable by syllable using karaoke markers. Injects metric and temporal syllable context (`syl.start_time`, `syl.duration`, `syl.text`, etc.).
* **`char`:** Iterates character by character individually. Enables independent typographic kinematic animations for each glyph.
* **`word`:** Iterates word by word delimited by whitespace.
* **`line`:** Iterates once per complete dialogue line.

The `blank_mode` property (`no_blank` / `with_blanks`) controls whether whitespace characters are omitted from the iteration or processed as elements with metric advance width but without a visible glyph.

### Phase 3: Sub-Loop Multiplication (`MaxLoop`) and Topological Generator Nesting
To generate volumetric effects (motion trails, particle swarms, delayed echo replicas, or frame-by-frame *FBF* animations), the flow passes through one or more `MaxLoop` nodes. This node multiplies the current unit by $N$ sub-iterations, injecting a local counter (by default `j` from $1 \dots N$) and subdividing time intervals.

Furthermore, within each leaf iteration of `Main Loop` / `MaxLoop`, the engine automatically traces **sub-loop generator nodes** connected to `Output` (`Shape/Slicer`, `Shape/Union & Divide`, `Shape/Concentric Borders`, `Shape/Array`, `Shape/Multi`, `Functions/Particles`, `Functions/IMG to pixels`, `Functions/Clip Gradient`, `Functions/Animation`) in **topological post-order (root $\to$ leaf)**:
1. **Geometry Channel (`Output.Return`):** Generators wired in series (e.g. `Slicer` $\to$ `Particles`) automatically nest their sub-loops ($s_i = 1 \dots S$ outer $\to$ $p_i = 1 \dots P_k$ inner), propagating anchor coordinates (`pos_x`, `pos_y`, `org_x`, `org_y`) from each parent piece down to its child sub-pieces or particles.
2. **Tags and Clipping Channel (`Output.Tags`):** Evaluated as an inner sub-loop for each piece or particle emitted by `Output.Return` (respecting `In1, In2, ...` port order in `Concatenate`), allowing combinations such as `Slicer` ($s_i$) on `Return` with `Clip Gradient` ($c_i$) and `Animation` ($an_i$) on `Tags` without counter collisions.

### Phase 4: Evaluation and Deformation
Connected data nodes compute `\pos` coordinates, morphological vector deformations (slicing with `Slicer`, inflating/scaling with `Transform`, stroking/extruding with `Stroke`), colour gradients with `Color Gradient`, audio modulations with `Modulator`, and accelerated time transformations with `Retime` and `Ipol`.

### Phase 5: Assembly, Isolation, and Emission (`Output`)
The terminal `Output` node gathers processed execution streams, consolidates tag blocks from the `Tags` port and vector drawings/text from the `Return` port, resolves syntactic tag collisions, applies rendering layers (`Layer`), and emits the resulting subtitle lines directly into the active Aegisub document.

#### Multi-Output Architecture and Context Isolation
When an effect requires generating concurrent rendering layers (for example, a shadow, a glyph body, and particles), multiple `System/Output` nodes are instantiated on the same canvas:
* **Complete Branch Independence:** Every `Output` node constitutes an autonomous terminal that independently evaluates its own connected upstream tree.
* **Context Isolation (`context`):** The engine initialises a clean, private context dictionary for each branch and iteration. Local variables, temporal calculations, or inline mutations evaluated within one `Output` branch do not leak, contaminate, or interact with parallel `Output` branches. Sharing the canvas or converging into the same subtitle track never compromises data encapsulation.

#### Output Queue Sequencing System (`Queue ID` and `Queue Order`)
Output queues operate strictly as **post-rendering sorting and sequencing containers** over already generated lines, without influencing node evaluation or runtime logic:
1. **Queue Identifier (`Queue ID` $\to$ ASS `Actor` Field):**
   * The text assigned to `Queue ID` identifies the logical emission pass and is directly written into the `Actor` field of the resulting ASS event:
     $$\texttt{Dialogue: Layer}, \, t_{\text{start}}, \, t_{\text{end}}, \, \text{Style}, \, \mathbf{Queue\_ID}, \, \text{MarginL}, \, \text{MarginR}, \, \text{MarginV}, \, \text{Effect}, \, \text{Text}$$
   * This facilitates sorting, filtering, and layer management directly inside Aegisub's subtitle grid.
2. **Numeric Emission Priority (`Queue Order`):**
   * Dictates the sequential order in which generated line blocks are written into the final ASS document.
   * **Global Emission Hierarchy:** The engine groups lines by queue and emits **all queues of lower numeric `Queue Order` across all dialogue lines first**, followed comprehensively by queues of higher orders:
     $$\text{SortKey}(Q) = \left(\min_{l \in Q} (\text{queue\_order}_l), \, \text{qid}\right)$$
   * **Tiebreaking and Fallback Rules:**
     * *Equal order or omitted order:* If two or more queues lack an explicit `Queue Order` (or share the identical integer order), the engine sorts them **alphabetically by their `Queue ID`**.
     * *Empty fields:* When both `Queue ID` and `Queue Order` are omitted, lines default to the `"default"` queue, stably preserving the node's creation order (`ID` on canvas).
     * *Intra-queue sorting:* Within each individual queue, lines are ordered sequentially by dialogue line index (`line_idx`) and internal event order:
        $$\text{SortKey}(l) = (\text{queue\_order}_l, \, \text{line\_idx}_l)$$

---

## 3. State Persistence and Context Variables

Pyxis provides mechanisms to register, transfer, and accumulate states across different evaluation phases:

1. **`Define Vars` (`Variables`):** Injects custom variables into the execution context (e.g. `my_scale = 120`, `custom_color = "#FF00AA"`), making them immediately accessible to any downstream expression in the current iteration.
2. **`Get Var` (`Variables`):** Reads and emits the value of any variable from the context (`i`, `j`, `N`, `syl.duration`, `line.start_time`, `fx.pos_x`, etc.).
3. **`Memory` (`Variables`):** Persistent key-value storage with two operating modes:
   * `remember`: Stores the current value under a designated key.
   * `retrieve`: Retrieves the last value saved under that key from previous iterations. Enables position accumulators, continuous kinematic trajectories, or historical state lookups.

---

## 4. ASS Context Variables and Metrics Reference

Pyxis Effector organises timing and spatial variables in a **hierarchical and modular** architecture:
* **`line` / `l`:** **Global / absolute** video timeline timestamps ($ms$).
* **`syl` / `word`:** **Local relative** offsets from the start of the base dialogue line ($[0, \text{line.dur}]$).
* **`char`:** **Local relative** offsets from the start of its parent syllable ($[0, \text{syl.dur}]$).
* **`fx`:** Temporal lifespan of the generated ASS dialogue line ($[0, \text{fx.dur}]$). Enables evaluating ASS transform blocks `\t(...)` accurately using the offset $\text{ini} = \text{line.start\_time} - \text{fx.start\_time}$.

Across any expression field, condition, or script within Pyxis, the following contextual variables are natively available organised by domain:

### 4.1. Original Line Domain (`line.` or `l.`)
Represents the active dialogue line ingested from Aegisub. Provides its absolute timestamps, text, ASS header metadata, metric screen coordinates, and margins:

| Variable | Type | Description and Unit | Usage Example |
| :--- | :---: | :--- | :--- |
| `line.start_time` / `l.start_time` | `int` | Absolute start timestamp of the line in the video timeline ($ms$). | `line.start_time - 500` |
| `line.end_time` / `l.end_time` | `int` | Absolute end timestamp of the line in the video timeline ($ms$). | `line.end_time + 300` |
| `line.dur` / `line.duration` / `l.dur` | `int` | Net duration of the line ($ms$): $t_{\text{end}} - t_{\text{start}}$. | `line.dur / 2` |
| `line.mid_time` / `l.mid_time` | `float` | Midpoint timestamp of the line: $t_{\text{start}} + \frac{t_{\text{dur}}}{2}$. | `line.mid_time` |
| `line_start_time`, `line_end_time`, `line_dur` | `int` | Flat global aliases without prefixes for line timestamps ($ms$). | `line_start_time` |
| `line.i` / `l.i` | `int` | Ordinal index of the active line in the processed batch ($1 \dots N$). | `line.i == 1` |
| `line.n` / `l.n` | `int` | Total count of selected lines in the batch. | `line.i / line.n` |
| `line.text` / `l.text` | `string` | Dialogue text stripped of styling tags and karaoke markup. | `len(line.text)` |
| `line.raw_text` / `l.raw_text` | `string` | Original dialogue text preserving tags `{\...}` and `\k` markup. | `line.raw_text` |
| `line.style` / `line.style_name` | `string` | Canonical name of the ASS style assigned to the line in Aegisub. | `line.style == "Default"` |
| `line.actor` / `l.actor` | `string` | Actor or character field of the ASS line. | `line.actor` |
| `line.effect` / `l.effect` | `string` | Special effect descriptor field of the ASS line. | `line.effect` |
| `line.layer` / `l.layer` | `int` | ASS layer index assigned to the line ($Z$-ordering depth). | `line.layer + 1` |
| `line.center`, `line.middle` / `l.x`, `l.y` | `float` | Horizontal ($X$) and vertical ($Y$) centre of the line bounding box (px). | `line.center, line.middle` |
| `line.left`, `line.right` | `float` | Left and right horizontal boundary coordinates of the line (px). | `line.right - line.left` |
| `line.top`, `line.bottom` | `float` | Top and bottom vertical boundary coordinates of the line (px). | `line.bottom` |
| `line.width`, `line.height` | `float` | Metric width and height of the complete line text (px). | `line.width` |
| `line.descent` (or `l.descend`), `line.extlead` | `float` | Typographical font descent and external leading metrics (px). | `line.bottom + line.descent` |
| `line.pos_x`, `line.pos_y` | `float` | Absolute horizontal and vertical position of the line (explicit `\pos` or calculated). | `line.pos_x, line.pos_y` |
| `line.org_x`, `line.org_y` | `float` | Rotation pivot or origin coordinates of the line (`\org` or metric centre). | `line.org_x, line.org_y` |
| `line.margin_l`, `line.margin_r`, `line.margin_v` | `int` | Left, right, and vertical subtitle margins configured on the line or style (px). | `line.margin_l` |
| `line.margin_t`, `line.margin_b` | `int` | Granular individual top and bottom margins (px). | `line.margin_t` |

### 4.2. Original Style Domain (`line.<style_prop>`)
Typographical, colour, outline, and alignment properties inherited from the ASS file `[V4+ Styles]` header or overridden on the line:

| Variable | Type | Description and Format | Usage Example |
| :--- | :---: | :--- | :--- |
| `line.fontname` | `string` | Font family configured in the original style (e.g. `"Arial"`, `"Montserrat"`). | `line.fontname` |
| `line.fontsize` | `float` | Base style font size in typographical points/pixels ($pt$). | `line.fontsize * 1.5` |
| `line.bold` | `bool` | Boolean flag for bold weight in the style (`True` / `False`). | `line.bold` |
| `line.italic` | `bool` | Boolean flag for italic posture in the style (`True` / `False`). | `line.italic` |
| `line.underline` | `bool` | Boolean flag for underline formatting in the style (`True` / `False`). | `line.underline` |
| `line.strikeout` | `bool` | Boolean flag for strikeout formatting in the style (`True` / `False`). | `line.strikeout` |
| `line.align` | `int` | Original Numpad alignment defined in the style ($1 \dots 9$). | `line.align` |
| `line.scale_x`, `line.scale_y` | `float` | Horizontal and vertical scale percentage factors of the base style ($100.0 = 100\%$). | `line.scale_x` |
| `line.spacing` | `float` | Letter-spacing or character tracking in pixels (`\fsp`). | `line.spacing` |
| `line.outline` / `line.bord` | `float` | Stroke outline width of the style in pixels (`\bord`). | `line.outline` |
| `line.shadow` / `line.shad` | `float` | Drop shadow depth/distance of the style in pixels (`\shad`). | `line.shadow` |
| `line.color1` | `string` | Primary colour of the style (`\1c`) in ASS format `&HBBGGRR&`. | `line.color1` |
| `line.color2` | `string` | Secondary / karaoke colour of the style (`\2c`) in ASS format `&HBBGGRR&`. | `line.color2` |
| `line.color3` | `string` | Outline / border colour of the style (`\3c`) in ASS format `&HBBGGRR&`. | `line.color3` |
| `line.color4` | `string` | Shadow colour of the style (`\4c`) in ASS format `&HBBGGRR&`. | `line.color4` |
| `line.alpha1` .. `line.alpha4` | `string` | Individual alpha channels (1: primary, 2: karaoke, 3: outline, 4: shadow) in ASS `&HAA&`. | `line.alpha1` |
| `line.angle` / `line.frz` | `float` | Nominal $Z$-rotation angle defined in the style in sexagesimal degrees. | `line.frz` |
| `line.frx`, `line.fry` | `float` | Intrinsic 3D rotation angles of the line in sexagesimal degrees. | `line.frx` |
| `line.fax`, `line.fay` | `float` | Typographical shear deformation factors along $X$ and $Y$. | `line.fax` |

### 4.3. Derived Units: Syllables (`syl`), Characters (`char`), and Words (`word`)
Units decomposed during `Main Loop` iteration in `syl`, `char`, or `word` mode. Each unit automatically inherits typographical properties from the base style (`syl.fontname`, `syl.color1`..`4`, `syl.fontsize`, `char.fontname`, etc.):

| Unit | Variable | Description and Unit | Usage Example |
| :--- | :--- | :--- | :--- |
| **Syllable (`syl`)** | `syl.start_time`, `syl.end_time` | Start and end timestamps relative to the dialogue line start ($ms$). | `syl.start_time` |
| | `syl.dur` / `syl.duration` | Karaoke duration of the syllable in milliseconds ($ms$). | `syl.dur` |
| | `syl.mid_time` | Relative midpoint timestamp of the syllable: $t_{\text{start}} + \frac{t_{\text{dur}}}{2}$. | `syl.mid_time` |
| | `syl.syl_start`, `syl.syl_end`, `syl.syl_mid` | Syllable temporal window relative to generated `fx` line ($\text{ini} + \text{syl.start\_time}$). | `\t(syl.syl_start, syl.syl_end, \tags)` |
| | `syl.i` / `syl.n` | Syllable index within line ($1 \dots N$) and total syllables. | `syl.i / syl.n` |
| | `syl.text`, `syl.text_stripped` | Text or glyph of the syllable stripped of tags and karaoke marks. | `syl.text` |
| | `syl.center`, `syl.middle` / `syl.x`, `syl.y` | Horizontal ($X$) and vertical ($Y$) centre of the syllable bounding box (px). | `syl.center, syl.middle` |
| | `syl.left`, `syl.right`, `syl.top`, `syl.bottom` | Left, right, top, and bottom boundary coordinates of the syllable (px). | `syl.right - syl.left` |
| | `syl.width`, `syl.height` | Calculated metric dimensions of the syllable (px). | `syl.width` |
| | `syl.descent`, `syl.extlead` | Typographical descent height and line spacing for the syllable (px). | `syl.descent` |
| | `syl.prespace`, `syl.postspace` | Preceding and trailing whitespace of the syllable. | `syl.prespace` |
| | `syl.pos_x`, `syl.pos_y`, `syl.org_x`, `syl.org_y` | Position anchor and rotation centre coordinates of the syllable. | `syl.pos_x, syl.pos_y` |
| **Character (`char`)** | `char.start_time`, `char.end_time` | Start and end timestamps relative to its **parent syllable** start ($ms$). | `char.start_time` |
| | `char.dur` / `char.duration` | Calculated duration of the individual character glyph ($ms$). | `char.dur` |
| | `char.mid_time` | Relative midpoint timestamp of the character within its syllable. | `char.mid_time` |
| | `char.char_start`, `char.char_end`, `char.char_mid` | Character temporal window relative to generated `fx` line ($ms$). | `\t(char.char_start, char.char_end, \tags)` |
| | `char.syl_start`, `char.syl_end`, `char.syl_mid` | Parent syllable temporal window relative to generated `fx` line ($ms$). | `\t(char.syl_start, char.syl_end, \tags)` |
| | `char.i` / `char.n` | Character index within the line ($1 \dots N$) and total characters. | `char.i` |
| | `char.syl_i`, `char.word_i` | Positional index of the character within its syllable and word. | `char.syl_i` |
| | `char.text` | Glyph of the active character. | `char.text` |
| | `char.center`, `char.middle` / `char.x`, `char.y` | Screen centre coordinates of the character glyph (px). | `char.center, char.middle` |
| | `char.left`, `char.right`, `char.top`, `char.bottom` | Boundary coordinates of the character glyph bounding box (px). | `char.left` |
| | `char.width`, `char.height` | Metric dimensions of the character glyph (px). | `char.width` |
| | `char.descent`, `char.extlead` | Typographical descent and spacing metrics of the character glyph (px). | `char.descent` |
| **Word (`word`)** | `word.start_time`, `word.end_time`, `word.dur`, `word.mid_time` | Start, end, duration, and midpoint timestamps relative to the line ($ms$). | `word.start_time` |
| | `word.word_start`, `word.word_end`, `word.word_mid` | Start, end, and midpoint timestamps relative to generated `fx` line ($ms$). | `word.word_start` |
| | `word.i` / `word.n` | Word index within line ($1 \dots N$) and total words. | `word.i` |
| | `word.text` | Text of the complete word stripped of tags. | `word.text` |
| | `word.center`, `word.middle` / `word.x`, `word.y` | Horizontal ($X$) and vertical ($Y$) centre of the word on screen (px). | `word.center, word.middle` |
| | `word.left`, `word.right`, `word.top`, `word.bottom` | Bounding box boundary coordinates of the complete word (px). | `word.right` |
| | `word.width`, `word.height` | Metric dimensions of the complete word (px). | `word.width` |
| | `word.descent`, `word.extlead` | Typographical descent and spacing metrics of the word (px). | `word.descent` |

### 4.4. Real Ink Metrics (`ink`) and Neighbouring Units (`prev` / `next`)

| Category | Variable | Description | Usage Example |
| :--- | :--- | :--- | :--- |
| **Real Ink (`ink`)** | `ink.width`, `ink.height` | Width and height of the actual rendered contour/glyph (excluding font box padding). | `ink.width` |
| | `ink.center`, `ink.middle` / `ink.x`, `ink.y` | Horizontal ($X$) and vertical ($Y$) centre based on actual rendered ink contours. | `ink.center, ink.middle` |
| | `ink.left`, `ink.right`, `ink.top`, `ink.bottom` | Exact bounding box of the rendered ink pixels in screen coordinates. | `ink.left` |
| | `ink.l.*`, `ink.syl.*`, `ink.char.*`, `ink.word.*` | Explicit scope-based access to the ink metrics of the line, syllable, character, or word. | `ink.syl.center` |
| **Neighbours (`prev` / `next`)** | `prev.*` / `next.*` | Introspection over the preceding or subsequent unit (`text`, `dur`, `start_time`, `x`, `y`, `width`, etc.). | `prev.width` |
| | `is_first`, `is_last` | Boolean flags indicating whether the unit is the first or last in the sequence. | `is_first` |
| | `has_prev`, `has_next` | `True` if a valid predecessor or successor unit exists in the chain. | `has_prev` |

### 4.5. Sub-loops (`MaxLoop`), Generated Effect (`fx`), and Global Environment

| Category | Variable | Description and Formula | Usage Example |
| :--- | :--- | :--- | :--- |
| **Sub-loop (`MaxLoop`)**| `j` | Active sub-iteration index ($1 \dots N$). | `j` |
| | `maxj` / `maxloop` | Total configured repetitions in the sub-loop. | `maxj` |
| | `module` / `m` / `ratio` | Normalised sub-loop progress: $\frac{j - 1}{\text{maxj} - 1} \in [0.0, 1.0]$. | `module` |
| **Effect (`fx`)** | `fx.pos_x`, `fx.pos_y` | Resolved anchor position coordinates for the active element on screen. | `fx.pos_x, fx.pos_y` |
| | `fx.start_time`, `fx.end_time` | Absolute start and end timestamps of the generated ASS dialogue line ($ms$). | `fx.start_time` |
| | `fx.dur` | Effective duration of the generated ASS line ($ms$). | `fx.dur` |
| **Global Environment** | `fps` | Frames per second rate of the active video in Aegisub (e.g. `23.976`, `60.0`). | `fps` |
| | `frame_dur` / `fd` | Duration of one video frame in milliseconds: $\frac{1000}{\text{fps}}$ (e.g. $41.708$ ms at $23.976$ fps). | `3 * fd` |
| | `ini` | Relative temporal offset: $\text{ini} = \text{line.start\_time} - \text{fx.start\_time}$ ($ms$). | `ini + syl.start_time` |
| | `st`, `et`, `dur` | Active start, end, and duration times of the processed element ($ms$). | `st, et` |
| | `maxgap` | Upper threshold for inter-line measurements with `sync()` ($ms$, default `2000.0`). | `maxgap` |

---

## 5. Expression Evaluation and String Resolution Engine

Pyxis Effector incorporates a dynamic internal resolution engine (the contextual numerical evaluator and template processor) capable of computing mathematical expressions, Python ternary operators, and embedded variables directly inside text inputs, string nodes, and ASS tag blocks:

### 5.1. Numerical and Algebraic Evaluation in Text Fields
Any numerical field (in `MultiTag`, `Math`, `Retime`, `Slicers`, `Particles`, etc.) evaluates mathematical operations in real time:
* **Direct algebra and functions:** `syl.center + (i * 15)`, `line.width / 2`, `math.sin(t) * 50`.
* **Pyxis frame and ratio shortcuts:** `3f` ($3 \times \text{frame\_dur}$), `0.5r` ($50\%$ of the duration).
* **ASS Hexadecimals:** `&HFF&` is numerically evaluated as `255`.

### 5.2. Python Ternary Expressions
Variable nodes (`Define Vars`) and conditional fields support native Python ternary syntax:
```python
angle = 1.4 if l.layer == 1 else -1.4
color_fx = "&H00FF00&" if syl.i % 2 == 0 else "&H0000FF&"
```

### 5.3. Universal String and ASS Tag Block Evaluator
Tag blocks delimited by curly braces `{\...}` in any subtitle-producing node (including `Basics/String`, `Basics/MultiTag`, `System/Output`, vector transforms, and kinematic layers) are processed by the template evaluation engine prior to final export.

> [!IMPORTANT]
> **ASSdraw Path Isolation:** The expression and macro evaluator operates exclusively within the interior of curly-braced tag blocks `{\...}`. All raw text and vector drawing commands (`m 0 0 l 100 0 ...`) residing outside braces remain 100% untouched, ensuring that complex geometric coordinates are never misinterpreted as identifiers or variables.

The templating language integrates 4 universal resolution mechanisms:

1. **Direct algebraic expressions and variables inside ASS tag parentheses (`\tag(...)`):**
   * Rotations and scales: `\frz(angle2)`, `\frz(j * 15)`, `\fscxy(120 + i*5)`.
   * Positions and pivots: `\pos(syl.center + 10, syl.middle)`, `\org(fx.pos_x, fx.pos_y - 1000)`.
   * Alphas and colours: `\alpha(255)`, `\1a(128)`, `\1c(line.color1)`, `\1c(ass_color(255, 128, 0))`.
2. **Dynamic temporal transformations `\t(...)`:**
   * Evaluated timestamps and tags: `\t(0, 150, \frz0)\t(fx.dur-150, fx.dur, \frz(angle2))`.
3. **Isolated expressions, variables, and ternaries in parentheses `(...)`:**
   * Evaluation of variables, attributes, and computations outside tags: `(syl.text)`, `(syl.dur)`, `(fx.dur)`, `(j * 15)`, `(line.text)`.
   * Conditional tag or value selection within the block: `(\blur3 if i == 1 else \blur0)`, `(Colores())`.
4. **Automatic decimal alpha conversion to ASS hexadecimal:**
   * Real-time conversion of integers to ASS hex: `\4a100` $\to$ `\4a&H64&`, `\alpha255` $\to$ `\alpha&HFF&`, `\1a0` $\to$ `\1a&H00&`.

---

### 5.4. Canonical Catalogue of Dark Tags (Composite and Contextual Tags)

*Dark Tags* are high-speed compact macros that expand shorthand syntax into pure canonical ASS sequences:

#### 5.4.1. Rotations with Auto-Origin (`\fr*o`)
Automatically inject the `\org(X, Y)` tag using the active element's centre of gravity in the current frame (`fx.pos_x`, `fx.pos_y` or `syl.center`, `syl.middle`) as the pivot:

| Dark Tag | Direct Syntax | Evaluated Syntax | Emitted ASS Expansion |
| :--- | :--- | :--- | :--- |
| `\fro`, `\frzo` | `\fro45`, `\frzo-30` | `\fro(j * 15)` | `\org(X, Y)\frz<val>` |
| `\frxo` | `\frxo30` | `\frxo(syl.i * 5)` | `\org(X, Y)\frx<val>` |
| `\fryo` | `\fryo60` | `\fryo(sin(j) * 45)` | `\org(X, Y)\fry<val>` |
| `\frxyo` | `\frxyo45` | `\frxyo(15)` | `\org(X, Y)\frx<val>\fry<val>` |
| `\frxzo` | `\frxzo30` | `\frxzo(20)` | `\org(X, Y)\frx<val>\frz<val>` |
| `\fryzo` | `\fryzo45` | `\fryzo(25)` | `\org(X, Y)\fry<val>\frz<val>` |
| `\frxyzo` | `\frxyzo30` | `\frxyzo(10)` | `\org(X, Y)\frx<val>\fry<val>\frz<val>` |

#### 5.4.2. Scale and Font Size by Style Ratio (`\fsc*r`, `\fsr`)
Multiply the nominal value defined in the Aegisub style (`style.scale_x`, `style.scale_y`, `style.fontsize`) by the specified multiplier factor:

| Dark Tag | Direct Syntax | Evaluated Syntax | Emitted ASS Expansion |
| :--- | :--- | :--- | :--- |
| `\fscxr` | `\fscxr1.5` | `\fscxr(1.0 + 0.2*j)` | `\fscx(style.scale_x * ratio)` |
| `\fscyr` | `\fscyr0.8` | `\fscyr(cos(t))` | `\fscy(style.scale_y * ratio)` |
| `\fscxyr` | `\fscxyr2.0` | `\fscxyr(1.5)` | `\fscx(style.scale_x * ratio)\fscy(style.scale_y * ratio)` |
| `\fsr` | `\fsr1.2` | `\fsr(1.0 + syl.i * 0.1)` | `\fs(style.fontsize * ratio)` |

#### 5.4.3. Contextual Temporal Transformations (`\te`, `\ts`, `\tc`, `\tw`)
Parametric timing shortcuts that adapt to total effect duration or the chronological placement of the element:

| Dark Tag | Usage Syntax | Resulting ASS Expansion | Operational Description |
| :--- | :--- | :--- | :--- |
| `\te` | `\te(t1, t2, \tags)`<br>`\te(t1, t2, accel, \tags)`<br>`\te(t, \tags)` | `\t(fx.dur - t2, fx.dur - t1, \tags)`<br>`\t(fx.dur - t2, fx.dur - t1, accel, \tags)`<br>`\t(fx.dur - t, fx.dur, \tags)` | Inverted animation timed relative to the end of the line duration (`fx.dur`). |
| `\ts` | `\ts(t1, t2, \tags)`<br>`\ts(t1, t2, accel, \tags)`<br>`\ts(t, \tags)` | `\t(syl.start + t1, syl.start + t2, \tags)`<br>`\t(syl.start + t1, syl.start + t2, accel, \tags)`<br>`\t(syl.start, syl.start + t, \tags)` | Animation relative to syllable start time. |
| `\tc` | `\tc(t1, t2, \tags)`<br>`\tc(t1, t2, accel, \tags)`<br>`\tc(t, \tags)` | `\t(char.start + t1, char.start + t2, \tags)`<br>`\t(char.start + t1, char.start + t2, accel, \tags)`<br>`\t(char.start, char.start + t, \tags)` | Animation relative to character start time. |
| `\tw` | `\tw(t1, t2, \tags)`<br>`\tw(t1, t2, accel, \tags)`<br>`\tw(t, \tags)` | `\t(word.start + t1, word.start + t2, \tags)`<br>`\t(word.start + t1, word.start + t2, accel, \tags)`<br>`\t(word.start, word.start + t, \tags)` | Animation relative to word start time. |

#### 5.4.4. Multichannel and Grouped Tags
| Dark Tag | Direct ASS Expansion | Example |
| :--- | :--- | :--- |
| `\fscxy` | `\fscx<val>\fscy<val>` | `\fscxy150` $\to$ `\fscx150\fscy150` |
| `\faxy` | `\fax<val>\fay<val>` | `\faxy0.2` $\to$ `\fax0.2\fay0.2` |
| `\frxyz`, `\frxy`, `\frxz`, `\fryz` | Combined 3D rotations | `\frxyz45` $\to$ `\frx45\fry45\frz45` |
| `\xybord`, `\xyshad`, `\bs` | Simultaneous borders and shadows | `\bs3` $\to$ `\bord3\shad3` |
| `\[1-4]+c` (e.g. `\134c`, `\13c`, `\234c`) | Simultaneous colour assignment | `\134c&H00FFFF&` $\to$ `\1c&H00FFFF&\3c&H00FFFF&\4c&H00FFFF&` |
| `\[1-4]+a` (e.g. `\134a`, `\14a`, `\34a`) | Simultaneous alpha assignment | `\134a&H80&` $\to$ `\1a&H80&\3a&H80&\4a&H80&` |

#### 5.4.5. Style Restoration Macros (`\tag~`) and Stochastic Generation (`\tagR(...)`)
* **Restoration (`~`):** Instantly retrieves values defined in the original style template: `\c~` (primary colour), `\fscxy~` (base $X/Y$ scale), `\fs~` (font size), `\bs~` (base border and shadow), `\134c~`, `\134a~`, `\frxyz~`, `\blur~`.
* **Stochastics (`R`):** Generates integrated continuous or discrete random variations: `\frzR(-30, 30)`, `\134cR()`, `\alphaR(0, 128)`, `\froR(-20, 20)`, `\fscxyrR(1.0, 1.5)`.

---

## 6. Inter-Line Synchronisation and Gap Detection (`sync`)

Pyxis Effector incorporates the inter-line synchronisation engine **`sync`**, designed to dynamically measure the temporal gap (in milliseconds) between the active dialogue line and its adjacent previous or subsequent line according to original subtitle order or matching criteria.

### 6.1. System Function `sync()`
Accessible directly in timing expressions, node properties, and script nodes:

```python
sync(direction="next", mode="order", max_gap=2000)
```

* **`direction` (1st parameter):** `next` (subsequent line) or `prev` (preceding line). Default: `next`.
* **`mode` (2nd parameter):** Original line matching criterion:
  * `1` or `"order"` *(default)*: Next/previous dialogue line in chronological subtitle appearance order (ignoring comment lines).
  * `2` or `"style"`: Lines matching the active ASS style (`line.style`).
  * `3` or `"actor"`: Lines matching the active actor (`line.actor`).
  * `4` or `"effect"`: Lines matching the active ASS Effect field (`line.effect`).
  * `5` or `"layer"`: Lines matching the active ASS rendering layer (`line.layer`).
* **`max_gap` (3rd parameter):** Upper boundary cap in milliseconds (default: `2000.0` ms or the value defined in `maxgap`).

#### Practical Timing Adjustment Examples:
```python
# Extends the effect end by half the gap to the next line (capped at 2000ms):
end_time = l.end_time + (sync(next, order) / 2)

# Advances effect start by half the gap to the previous line with matching style (capped at 1500ms):
start_time = l.start_time - (sync(prev, style, 1500) / 2)

# Numeric mode index invocation:
start_time = l.start_time - (sync(prev, 2) / 2)
```

### 6.2. Global Property Namespace (`sync.*`)
For tag animations and ASS transform blocks (`\fad`, `\t`), Pyxis injects the `sync` namespace with direct property accessors:

| Property | Direction | Mode Filter | Return Value |
| :--- | :---: | :---: | :--- |
| `sync.next` / `sync.order_next` | `next` | `order` | Gap to the next dialogue line in ms. |
| `sync.prev` / `sync.order_prev` | `prev` | `order` | Gap to the previous dialogue line in ms. |
| `sync.style_next` / `sync.style_prev` | `next` / `prev` | `style` | Gap to adjacent line with matching style. |
| `sync.actor_next` / `sync.actor_prev` | `next` / `prev` | `actor` | Gap to adjacent line with matching actor. |
| `sync.effect_next` / `sync.effect_prev` | `next` / `prev` | `effect` | Gap to adjacent line with matching effect. |
| `sync.layer_next` / `sync.layer_prev` | `next` / `prev` | `layer` | Gap to adjacent line with matching layer. |

#### Usage Examples in ASS Tags:
```ass
{\fad(sync.order_prev / 2, sync.order_next / 2)}
{\t(0, sync.style_next, \fscxy120)}
{\t(fx.dur - sync.next / 2, fx.dur, \alpha&HFF&)}
```

### 6.3. Dynamic Ceiling Override (`maxgap`)
The default 2000ms ceiling can be redefined globally or locally for all `sync.*` evaluations by assigning the `maxgap` variable in a `Define Vars` node or inside a Python/Lua script:
```python
maxgap = 3500
```
All subsequent evaluations of `sync.order_next` or `sync(next, order)` will automatically use `3500.0` as the upper cap.

### 6.4. Overlapping Lines and Boundary Behaviour
* **Overlapping Lines ($\text{gap} < 0$):** If two lines overlap temporally, `sync` returns the exact negative float value ($\Delta t < 0$), providing the precise overlap duration.
* **Missing Adjacent Line (First/Last):** When no matching line exists, `sync` returns the configured `maxgap` ceiling.

---

## 7. ASS Performance Telemetry and Pre-Generation Workload Estimation (`Telemetry`)

In compositions combining frame-by-frame loops (`MaxLoop` in `fbf` mode), polygonal slicing (`Shape/Slicer`), particles (`Functions/Particles`), or blurs (`\blur`), playback performance is primarily governed by the **computational cost of per-frame rasterisation and bitmap compositing** in `libass`.

The performance diagnostic framework comprises two stages: **Static Pre-Generation Estimation** and **Per-Frame Rendering Telemetry**.

```
[Graph Topology + ASS Selection]
                 │
                 ├──► [1. Pre-Generation Estimation (Hover on Generate Layers)]
                 │      • Sweep-Line Concurrency (Peak Simultaneous Lines)
                 │      • Expansion Ratio & Estimated ASS Weight (KB / MB)
                 │      • Vector Render Profile (FBF / Slicer / Particles / Audio / Script)
                 │
                 └──► [2. Native libass Telemetry (Refresh in Previewer / Scan in Telemetry)]
                        • Parallel native C rendering + hardware QPC timer (1 µs)
                        • Integrated workload curve on the Previewer transport bar
                        • Diagnostic panel (4 overlaid metrics + 2D navigation)
```

### 7.1. Static Pre-Generation Workload Estimation
Hovering over the **`Generate Layers`** button statically evaluates the active graph topology and input lines without compiling the effect:

1. **Estimated Lines and Expansion Ratio:**
   Computes the projected number of `Dialogue:` events that connected `System/Output` nodes will emit ($\hat{N}_{\text{out}}$) alongside the multiplication factor relative to selected source lines ($N_{\text{in}}$):
   $$\text{Expansion Ratio} = \frac{\hat{N}_{\text{out}}}{\max(1, N_{\text{in}})}$$
2. **Maximum Line Concurrency (*Sweep-Line Peak Simultaneous Lines*):**
   Instantaneous concurrency measures how many layers coexist simultaneously on screen at a given time $t$. The estimator applies an interval *Sweep-Line* algorithm across the projected $[t_{\text{start}}, t_{\text{end}})$ spans of each branch:
   $$L_{\text{peak}} = \max_{t} \sum_{k=1}^{\hat{N}_{\text{out}}} \mathbf{1}_{[t_{\text{start}, k},\, t_{\text{end}, k})}(t)$$
   This metric quantifies the peak number of overlapping layers at the densest frame of the effect.
3. **Estimated ASS Weight (`KB` / `MB`) and Render Profile:**
   Weights the expected line byte length based on operations present in the graph (ASSdraw vector paths, `\clip` masks, `\t` transforms) and displays active subsystem badges (`FBF`, `Slicer`, `Particles`, `Audio`, `Script`).

### 7.2. Multi-Process Native Telemetry Engine (`libass` + QPC)
When executing **`Refresh`** in the `System/Previewer` node (or **`Scan`** in the `Telemetry` panel), the engine profiles rendering performance via the native `libass` C library:

1. **Isolation of the Evaluated Effect:**
   The telemetry engine evaluates **exclusively the dialogue lines generated by the effect** alongside script styles and metadata, isolating unmodified lines so that metrics accurately reflect the computational cost attributable to the active graph.
2. **Multi-Worker Parallelism and Hardware Timing (`QPC`):**
   The preview clip frame range is partitioned in batches across multiple parallel processes (`multiprocessing`). Each process initialises a `libass` instance at project resolution ($\text{PlayResX} \times \text{PlayResY}$) and executes `ass_render_frame` frame-by-frame using the hardware performance counter ($\text{QPC}$, $1\,\mu\text{s}$ resolution).
3. **Frame Budget Threshold (*Frame Budget*):**
   To maintain playback at video cadence without dropped frames (*frame drops*), the rendering duration of each frame ($T_{\text{render}}$) must remain below the frame duration defined by video $\text{FPS}$:
   $$\text{Budget}_{\text{ms}} = \frac{1000}{\text{FPS}}, \qquad \text{Budget \%} = \frac{T_{\text{render}}}{\text{Budget}_{\text{ms}}} \times 100\%$$
   At $23.976\,\text{fps}$ the per-frame budget is $41.71\,\text{ms}$, whereas at $60\,\text{fps}$ it is $16.67\,\text{ms}$. Any frame whose cost exceeds $\text{Budget}_{\text{ms}}$ ($\text{Budget \%} > 100\%$) is recorded as a potential frame drop.
4. **Bitmap Memory and Primitive Inspection (`ASS_Image`):**
   On every frame $f$, the engine traverses the linked list of alpha bitmaps produced by `libass` ($\{I_1, I_2, \dots, I_M\}$) and extracts three structural metrics:
   * **`ASS Objects` ($M_f$):** Total count of image primitives composited in the frame.
   * **`Total Bitmap RAM`:** Cumulative memory footprint of all active bitmaps in the frame:
     $$\text{RAM}_{\text{total}}(f) = \frac{1}{1024} \sum_{m=1}^{M_f} \left( w_m \times h_m \right) \quad [\text{KB}]$$
   * **`Largest Bitmap`:** Footprint of the largest single bitmap in the frame:
     $$\text{RAM}_{\text{max}}(f) = \frac{1}{1024} \max_{1 \le m \le M_f} \left( w_m \times h_m \right) \quad [\text{KB}]$$

### 7.3. Telemetry Panel and Navigation Controls
The **`Telemetry`** panel (accessible via the `Generate Layers` tooltip or by clicking the workload curve in the `Previewer`) presents diagnostics across three synchronised regions:

1. **Video Viewport and Per-Frame HUD (Top-Left Quadrant):**
   * The `System/Previewer` player docks into the viewport, preserving playback position, subtitle track, and focal zoom.
   * Features a resize control maintaining native video aspect ratio.
   * Lower HUD bar showing frame index (`F`), timecode (`MM:SS.mmm`), render duration (`ms`), bitmap memory (`KB`/`MB`), and object count (`obj`).
2. **Budget Gauge, KPI Cards, and Critical Points (Top-Right Quadrant):**
   * **Budget Arc Gauge (`Frame Budget %`):** Semicircular vector gauge indicating peak load percentage relative to available frame budget.
   * **KPI Summary Cards:** Consolidated clip values: `Peak Render Time` (frame and timestamp), `Average Render` (with `P95` percentile), `Frame Drops` (count and percentage of clip exceeded), `Peak Bitmap RAM` (with `Max Single`), and `Peak ASS Objects`.
   * **Critical Hotspots List:** Ranked record of local peak loads; selecting an entry positions both the video playhead and chart on the corresponding frame.
3. **Overlaid Chart and 2D Navigation (Bottom Half):**
   * **4-Metric Overlay and Scale Multipliers ($1\times$ – $10\times$):** Continuous curves for `Render Time (ms)`, `Total Bitmap RAM`, `Largest Bitmap`, and `ASS Objects` alongside the horizontal budget threshold (`FPS Budget Limit`). Metrics can be toggled individually and support vertical scale multipliers (`1x`, `2x`, `5x`, `10x`).
   * **Navigation and Interaction:**
     * **`Mouse Scroll Wheel`:** Horizontal ($X$) zoom centred on the cursor position.
     * **`Ctrl + Wheel` / `Shift + Wheel`:** Vertical ($Y$) scale adjustment.
     * **`Middle Mouse Button + Drag`:** Two-dimensional ($X$ and $Y$) panning.
     * **`Left-Click + Drag`:** Video scrubbing synchronised with the player.
     * **`R` / `Home` Key:** Restores view to $100\%$ of the temporal range.

> [!NOTE]
> **Clean Per-Session Lifecycle:** Both the `Telemetry` cockpit chart and the `Previewer` thermal heatmap start completely empty when launching a new session or instantiating a `Previewer` node, populating strictly with live measurements after applying or refreshing the current effect.
