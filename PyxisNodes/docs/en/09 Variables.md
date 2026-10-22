# Variables

The **Variables** category manages ASS environment metric introspection, real-time dynamic injection of evaluated local identifiers, and persistent key-value storage across execution cycles.

### Volume Structure:
* **Section 9.A — Architectural Foundations and Context Lifecycle:** Formal mathematical time hierarchy, effect-relative timing ($ini$), DAG Trace topological nesting, and iterator isolation.
* **Section 9.B — Variables Node Catalogue:** [`Sys Var`](#1-node-variablessys-var-system-and-context-variables) (§1), [`Define Vars`](#2-node-variablesdefine-vars-local-variable-definition) (§2), [`Get Var`](#3-node-variablesget-var-context-variable-reader) (§3), [`Memory`](#4-node-variablesmemory-persistent-key-value-store) (§4).
* **Section 9.C — Comparative Matrix, Property Typification, and Best Practices:** Comparative table (§5), property typification (Types A/B/C), AST resolution, and memory optimisation.

---

## Variable Architecture and Context Lifecycle

In the Pyxis graph, contextual data flows hierarchically through each iteration tier (`line` $\to$ `syl` $\to$ `word` $\to$ `char` $\to$ `sub-loops`):

```
+─────────────────────────────────────────────────────────────────────────────+
|                         GLOBAL / PROJECT ENVIRONMENT                        |
|  meta.res_x, meta.res_y, frame_dur, default_audio_source, video_fps         |
+──────────────────────────────────────┬──────────────────────────────────────+
                                       │
                                       ▼
+─────────────────────────────────────────────────────────────────────────────+
|                            LINE LEVEL (line / l)                            |
|  l.text, l.start_time, l.end_time, l.dur, l.style, l.layer, l.margin_*, ... |
+──────────────────────────────────────┬──────────────────────────────────────+
                                       │
                                       ▼
+─────────────────────────────────────────────────────────────────────────────+
|                    ACTIVE UNIT LEVEL (syl / word / char)                    |
|  syl.text, syl.x, syl.y, syl.dur, syl.left, syl.center, syl.i, syl.n, ...   |
+──────────────────────────────────────┬──────────────────────────────────────+
                                       │
                                       ▼
+─────────────────────────────────────────────────────────────────────────────+
|                        LOOP / SUB-LOOP CHAIN LEVEL                          |
|  fx.i, fx.n, fx.pos_x, fx.pos_y, fx.dur, j, maxj, s_i, a_i, p_i, ratio       |
+──────────────────┬──────────────────────────────────────┬───────────────────+
                   │                                      │
                   ▼                                      ▼
+──────────────────────────────────────+ +────────────────────────────────────+
|     LOCAL STATE (Define Vars)        | |    PERSISTENT STATE (Memory)       |
|  Temporary injected variables valid  | |  Key-value store that persists     |
|  strictly within the active cycle.   | |  across all execution cycles.      |
+──────────────────────────────────────+ +────────────────────────────────────+
```

### 0.1. Formal Mathematical Time Hierarchy

The ASS format defines generated line timestamps (`Dialogue`) within the global video timeline. However, karaoke tags `\k` and kinematic transforms `\t(t1, t2, tags)` operate within local temporal frames relative to the start of the physically generated line ($[0, \text{fx.dur}]$).

Pyxis models this hierarchy through four coupled temporal tiers:

| Entity | Canonical Properties | Mathematical Base / Scope | Effect-Relative Variables ($ini = line.start\_time - fx.start\_time$) |
| :--- | :--- | :--- | :--- |
| **`line` / `l`** | `start_time`, `end_time`, `dur`, `mid_time` | **Global Video Timeline ($ms$)** | Absolute temporal reference of the event in the timeline. |
| **`syl`** | `start_time`, `end_time`, `dur`, `mid_time` | **Line-Relative ($[0, line.dur]$)** | $syl.syl\_start = ini + syl.start\_time$<br>$syl.syl\_end = syl.syl\_start + syl.dur$<br>$syl.syl\_mid = syl.syl\_start + \frac{syl.dur}{2}$ |
| **`char`** | `start_time`, `end_time`, `dur`, `mid_time` | **Syllable-Relative ($[0, syl.dur]$)** | $char.char\_start = syl.syl\_start + char.start\_time$<br>$char.char\_end = char.char\_start + char.dur$<br>$char.syl\_start = syl.syl\_start$<br>$char.syl\_end = syl.syl\_end$ |
| **`word`** | `start_time`, `end_time`, `dur`, `mid_time` | **Line-Relative ($[0, line.dur]$)** | $word.word\_start = ini + word.start\_time$<br>$word.word\_end = word.word\_start + word.dur$ |
| **`fx`** | `start_time`, `end_time`, `dur` | **Global Generated ASS Line** | Defines the $[0, fx.dur]$ interval over which libass evaluates $\backslash\text{t}(t_1, t_2, \dots)$. |

#### Algebraic Relationship of Effect Lead-In Offset ($ini$)
Given an event with original timestamp $line.start\_time$ and an anticipation lead-in offset $\Delta t_{\text{leadin}}$ generated by timing nodes (`Time/Lead In`, `Time/Retime`), the output ASS line commences at:

$$fx.start\_time = line.start\_time - \Delta t_{\text{leadin}}$$

The relative offset $ini$ is defined as:

$$ini = line.start\_time - fx.start\_time = \Delta t_{\text{leadin}}$$

Consequently, an ASS transform `\t` applied to a syllable during its exact singing interval employs the bounds:

$$t_1 = syl.syl\_start = ini + syl.start\_time, \quad t_2 = syl.syl\_end = syl.syl\_start + syl.dur$$

### 0.2. DAG Trace Multidimensional Sub-loop Nesting

When multiple piece or particle generator nodes connect towards `System/Output`, the engine resolves dependencies at render time through a post-order traversal across the graph wiring (**DAG Trace**):

```
                                              ┌───────────────────────────────┐
                                              │     System/Output (Terminal)  │
                                              └───────▲───────────────▲───────┘
                                                      │               │
                                  Return Channel:     │               │ Tags Channel:
                                  Geometry / Pieces   │               │ Modifiers
                                                      │               │
                                          ┌────────────┴───┐       ┌───┴──────────┐
                                          │ Functions/     │       │ Basics/      │
                                          │ Particles      │       │ MultiTag     │
                                          └────────────▲───┘       └──────────────┘
                                                      │
                                          ┌────────────┴───┐
                                          │ Shape/Slicer   │
                                          │ (Outer Loop)   │
                                          └────────────────┘
```

1. **Channel 1 (`Output.Return` — Port 5, Geometry):** Recursively traced in post-order from the upstream root to the `Return` port. If `Slicer` feeds `Particles` and the latter connects to `Return`, `Slicer` operates as the outer loop ($s_i \in [1, s_n]$) and `Particles` as the inner loop ($p_i \in [1, p_n]$ for each slice $s_i$).
2. **Channel 2 (`Output.Tags` — Port 4, Modifiers):** Traced in post-order respecting input connection order (`In1`, `In2`, ...) and evaluated nested within each geometric state emitted by `Return`.

#### Canonical Iterator Isolation by Generator
To prevent collisions across nesting tiers, each generator family maintains its own isolated namespace:

| Generator Node Family | Ordinal Iterator | Unit Count | Expression Aliases |
| :--- | :---: | :---: | :--- |
| **`Shape/Slicer`** | `s_i` | `s_n`, `s_max` | `slice_i`, `slice_n`, `slice_max`, `col`, `row` |
| **`Shape/Union & Divide`** | `d_i` | `d_n`, `d_max` | `divide_i`, `divide_n`, `divide_max` |
| **`Shape/Concentric Borders`** | `b_i` | `b_n`, `b_max` | `ring_i`, `ring_n`, `ring_max` |
| **`Shape/Array`** | `a_i` | `a_n`, `a_max` | `array_i`, `array_n`, `array_max`, `col`, `row` |
| **`Shape/Multi`** | `m_i` | `m_n`, `m_max` | `multi_i`, `multi_n`, `multi_max` |
| **`Functions/Particles`** | `p_i` | `p_n`, `p_max` | `tp_i`, `tp_n`, `tp_max`, `text_p_i`, `text_p_n` |
| **`Functions/IMG to pixels`** | `ip_i` | `ip_n`, `ip_max` | `img_p_i`, `img_p_n`, `total_pixels` |
| **`Functions/Clip Gradient`** | `c_i` | `c_n`, `c_max` | `clip_i`, `clip_n`, `clip_max`, `c_col`, `c_row` |
| **`Functions/Animation`** | `an_i` | `an_n`, `an_max` | `anim_i`, `anim_n`, `anim_max`, `an_j` |
| **`Loops/MaxLoop`** | `j` | `maxj`, `maxloop` | `module`, `m`, `ratio` |

#### Context-Aware Conditional Pruning (*Context-Aware DAG Trace*)
When tracing topology upstream, if the engine encounters conditional selectors or switches (`Basics/Only`, `Functions/Conditioner`, `Basics/Once`), it evaluates the boolean condition against the active iteration context. Traversal proceeds strictly through the active branch (`True` or `False`), pruning the inactive branch. This prevents alternative generators from improperly multiplying in series or inactive branches from executing phantom iterations.

---

## 1. Node `Variables/Sys Var` (System and Context Variables)

* **Canonical Category:** `Variables` (UI: *Variables / Sys Var*)
* **Purpose:** Inspects and extracts native context metrics from the active element (Cartesian coordinates, metric pixel dimensions, timestamps in milliseconds, iteration indices, ASS style typographic properties, project resolution metadata, or vector path dimensions).

![Variables/Sys Var](img/sys_var.png)

> [!TIP]
> **Interactive Variable Picker (SysVar Grid Picker):**
> Clicking or editing the **Variable** field automatically opens an interactive modal with real-time search filtering and taxonomic categorisation (*Line*, *Syllable*, *Character*, *Word*, *Effect/FX*, *Loops/Globals*, *Temporal Offset*, *Ink Metrics*, *Meta/Project*, *Neighbors & Context*). Within each category, variables are presented strictly sorted alphabetically for immediate and predictable discovery, enabling instant 1-click selection without manual typing.

---

### 1.1. Header Mode Combos
The top header dropdown directly maps the `var_name` property, allowing 1-click switching between frequently used system context variables or direct entry of a freeform identifier.

---

### 1.2. Input Ports and Body Properties (*Inputs & Properties*)
1. **`Variable` (`var_name`):** Canonical variable identifier or property path to query (e.g. `"syl.text"`, `"line.start_time"`, `"fx.pos_x"`, `"meta.res_x"`, `"shape.width"`). (Default: `"syl.text"`).
   * **Canonical Typification:** **Type C (Plain Text / Identifier)**. Strictly excluded from `ast.parse` to eliminate false syntax errors.
   * Operates without input ports; the value is resolved directly from the active bound execution context.

---

### 1.3. Output Ports (*Outputs*)
1. **`[1.1] Data`:** Scalar value, text string, or floating-point/integer number corresponding to the requested variable. If the variable does not exist in context, emits an empty string `""` or `0.0`.

---

### 1.4. Exhaustive Taxonomy of Available System Variables

The following tables document the complete canonical matrix of context variables accessible via `Sys Var`, in the `Define Vars` node, in `Script Code` scripts, or in parenthesized `\tag(var)` expressions:

#### 1.4.1. Line Domain (`line.` or `l.`) and Original Style Information
Represents the active dialogue line and its associated typographical style defined in the `[V4+ Styles]` section of the ASS script. Typographical properties reflect the baseline style (`StyleRef`) or any preceding inline overrides:

| Variable | Type | Description and Units |
| :--- | :---: | :--- |
| `line.text` / `l.text` | `string` | ASS dialogue text stripped of style override tags and karaoke markers. |
| `line.raw_text` / `l.raw_text` | `string` | Raw ASS line text preserving all `{\...}` override tags and `\k` markers. |
| `line.start_time` / `l.start_time` | `int` | Line start timestamp in milliseconds ($ms$). |
| `line.end_time` / `l.end_time` | `int` | Line end timestamp in milliseconds ($ms$). |
| `line.dur` / `line.duration` / `l.dur` | `int` | Net line duration in milliseconds: $t_{\text{end}} - t_{\text{start}}$. |
| `line.mid_time` / `l.mid_time` | `float` | Temporal midpoint of the line: $t_{\text{start}} + \frac{t_{\text{dur}}}{2}$. |
| `line.i` / `l.i` | `int` | Ordinal index of the active line in the processed batch ($1 \dots N$). |
| `line.n` / `l.n` | `int` | Total count of selected dialogue lines in the batch. |
| `line.x`, `line.y` | `float` | Calculated Cartesian screen coordinates of the line centre (px). |
| `line.left`, `line.right` | `float` | Left and right horizontal boundaries of the line's bounding box (px). |
| `line.top`, `line.bottom` | `float` | Top and bottom vertical boundaries of the line's bounding box (px). |
| `line.middle`, `line.center` | `float` | Vertical and horizontal centre coordinates of the full line (px). |
| `line.width`, `line.height` | `float` | Calculated typographical width and height of the full line (px). |
| `line.descent`, `line.extlead` | `float` | Font typographical descent and external leading metrics of the font (px). |
| `line.layer` / `l.layer` | `int` | ASS layer number assigned to the dialogue line (rendering Z-order). |
| `line.style` / `line.style_name` | `string` | Name of the ASS style associated with the line (e.g. `"Default"`, `"Romaji"`). |
| `line.actor` / `l.actor` | `string` | Actor / character field of the ASS dialogue line. |
| `line.effect` / `l.effect` | `string` | Special effect field of the ASS dialogue line. |
| `line.margin_l`, `line.margin_r`, `line.margin_v` | `int` | Left, right, and vertical margins defined on the line or style (px). |
| `line.margin_t`, `line.margin_b` | `int` | Specific top and bottom margins (px). |
| `line.fontname` | `string` | Typographical font family name defined in the original style (e.g. `"Arial"`, `"Montserrat"`). |
| `line.fontsize` | `float` | Font size of the baseline style in points / typographical pixels ($pt$). |
| `line.bold` | `bool` | Boolean flag indicating bold weight defined in the original style (`True` / `False`). |
| `line.italic` | `bool` | Boolean flag indicating italic slant defined in the original style (`True` / `False`). |
| `line.underline` | `bool` | Boolean flag indicating underline decoration in the original style (`True` / `False`). |
| `line.strikeout` | `bool` | Boolean flag indicating strikeout decoration in the original style (`True` / `False`). |
| `line.scale_x`, `line.scale_y` | `float` | Horizontal and vertical font scale percentages of the baseline style ($100.0 = 100\%$). |
| `line.spacing` | `float` | Typographical letter tracking / spacing in pixels (`\fsp`). |
| `line.outline` | `float` | Outline / border thickness defined in the original style in pixels (`\bord`). |
| `line.shadow` | `float` | Drop shadow distance / depth defined in the original style in pixels (`\shad`). |
| `line.align` | `int` | Baseline style numpad alignment ($1 \dots 9$). |
| `line.color1` .. `line.color4` | `string` | Original style colours: primary (`\1c`), secondary/karaoke (`\2c`), outline (`\3c`), and shadow (`\4c`) in ASS `&HBBGGRR&` format. |
| `line.alpha1` .. `line.alpha4` | `string` | Original style alpha channels for the 4 colour planes in ASS `&HAA&` format ($0 \dots 255$). |
| `line.frz`, `line.frx`, `line.fry` | `float` | Intrinsic 3D rotation angles of the line or style in degrees. |
| `line.fax`, `line.fay` | `float` | Horizontal and vertical typographical shear factors. |
| `line.pos_x`, `line.pos_y` | `float` | Absolute or overridden screen position coordinates of the line (`\pos`). |
| `line.org_x`, `line.org_y` | `float` | Origin or pivot coordinates for rotational transformations (`\org`). |

#### 1.4.2. Syllable (`syl.`), Character (`char.`), and Word (`word.`) Domains
Represent the atomic syllable units, individual characters, or words segmented by `Main Loop`. Each unit automatically inherits the typographical and colour attributes of its parent line's baseline style or active overrides:

| Variable | Type | Description and Units |
| :--- | :---: | :--- |
| `syl.text` / `word.text` / `char.text` | `string` | Text content of the element stripped of override tags. |
| `syl.text_stripped` / `char.text_stripped` | `string` | Clean unit text guaranteeing omission of any embedded tags. |
| `syl.text_spacestripped` | `string` | Syllable text additionally stripped of leading and trailing whitespace. |
| `syl.dur` / `syl.duration` | `int` | Duration of the syllable in milliseconds ($ms$) assigned by `\k` tags. |
| `syl.start_time`, `syl.end_time` | `int` | Start and end timestamps relative to the **baseline dialogue line** ($ms$). |
| `syl.mid_time` | `float` | Relative midpoint timestamp of the syllable: $t_{\text{start}} + \frac{t_{\text{dur}}}{2}$. |
| `syl.syl_start`, `syl.syl_end` | `int` | Start and end timestamps of the syllable relative to generated **effect line `fx`** ($\text{ini} + \text{syl.start\_time}$). |
| `syl.syl_mid` | `float` | Midpoint timestamp of the syllable relative to effect line `fx`. |
| `syl.i` / `syl.n` | `int` | Syllable index within line ($1 \dots N$) and total syllables. |
| `syl.x`, `syl.y` | `float` | Absolute Cartesian screen coordinates of the syllable centre (px). |
| `syl.left`, `syl.right` | `float` | Left and right horizontal boundaries of the syllable bounding box (px). |
| `syl.top`, `syl.bottom` | `float` | Top and bottom vertical boundaries of the syllable bounding box (px). |
| `syl.center`, `syl.middle` | `float` | Horizontal $X$ and vertical $Y$ centre coordinates of the syllable (px). |
| `syl.width`, `syl.height` | `float` | Calculated metric dimensions of the syllable (px). |
| `syl.descent`, `syl.descend` | `float` | Font typographical descent height for the syllable (px). |
| `syl.extlead` | `float` | External leading spacing of the font (px). |
| `syl.prespace`, `syl.postspace` | `string` | Leading and trailing whitespace characters adjacent to the syllable. |
| `syl.prespacewidth`, `syl.postspacewidth` | `float` | Metric pixel width of adjacent leading and trailing whitespaces. |
| `syl.fontname`, `syl.fontsize` | `string` / `float` | Inherited font family name and font size in points ($pt$). |
| `syl.bold`, `syl.italic` | `bool` | Inherited bold and italic boolean flags. |
| `syl.underline`, `syl.strikeout` | `bool` | Inherited underline and strikeout boolean flags. |
| `syl.scale_x`, `syl.scale_y` | `float` | Inherited font scale factors ($100.0 = 100\%$). |
| `syl.spacing`, `syl.outline`, `syl.shadow` | `float` | Inherited letter spacing (`\fsp`), border outline width (`\bord`), and shadow depth (`\shad`) (px). |
| `syl.color1` .. `syl.color4` | `string` | Primary, secondary, outline, and shadow colours assigned to the syllable (`&HBBGGRR&`). |
| `syl.alpha1` .. `syl.alpha4` | `string` | Primary, secondary, outline, and shadow alpha channels assigned to the syllable (`&HAA&`). |
| `syl.align` | `int` | Active numpad alignment ($1 \dots 9$). |
| `syl.pos_x`, `syl.pos_y` | `float` | Calculated rendering anchor coordinate for the syllable (`\pos`). |
| `syl.org_x`, `syl.org_y` | `float` | Calculated origin or rotation pivot for the syllable (`\org`). |
| `syl.actor`, `syl.style`, `syl.layer`, `syl.effect` | `str`/`int` | Metadata inherited from the parent dialogue line. |
| `char.dur` / `char.duration` | `int` | Calculated duration of the character glyph ($ms$). |
| `char.start_time`, `char.end_time` | `int` | Start and end timestamps relative to its **parent syllable** ($ms$). |
| `char.mid_time` | `float` | Relative midpoint timestamp of the character within its syllable: $t_{\text{start}} + \frac{t_{\text{dur}}}{2}$. |
| `char.char_start`, `char.char_end` | `int` | Start and end timestamps of the character relative to generated **effect line `fx`** ($\text{syl.syl\_start} + \text{char.start\_time}$). |
| `char.syl_start`, `char.syl_end` | `int` | Start and end timestamps of parent syllable relative to generated **effect line `fx`**. |
| `char.i` / `char.n` | `int` | Character index within the line ($1 \dots N$) and total characters. |
| `char.syl_i` | `int` | Positional index of the character within its parent syllable ($1 \dots N_{\text{syl}}$). |
| `char.word_i` | `int` | Positional index of the character within its parent word. |
| `char.x`, `char.y` | `float` | Absolute Cartesian screen coordinates of the character glyph centre (px). |
| `char.center`, `char.middle` | `float` | Screen centre coordinates of the character glyph (px). |
| `char.left`, `char.right`, `char.top`, `char.bottom` | `float` | Bounding box boundaries of the character glyph (px). |
| `char.width`, `char.height` | `float` | Calculated metric dimensions of the character glyph (px). |
| `char.fontname`, `char.fontsize`, `char.color1`..`4` | `var` | Complete typographical and colour properties inherited for the character. |
| `word.dur` / `word.duration` | `int` | Total duration of the word ($ms$). |
| `word.start_time`, `word.end_time` | `int` | Start and end timestamps relative to the **baseline dialogue line** ($ms$). |
| `word.word_start`, `word.word_end` | `int` | Start and end timestamps of the word relative to generated **effect line `fx`** ($\text{ini} + \text{word.start\_time}$). |
| `word.i` / `word.n` | `int` | Word index within line ($1 \dots N$) and total words. |
| `word.x`, `word.y`, `word.center`, `word.middle` | `float` | Screen centre coordinates of the word (px). |
| `word.left`, `word.right`, `word.top`, `word.bottom` | `float` | Bounding box boundaries of the word (px). |
| `word.width`, `word.height` | `float` | Calculated metric dimensions of the full word (px). |

#### 1.4.3. Adjacent Units and Relational Sequence Flags (`prev.`, `next.`, `is_first`, `is_last`, `has_prev`, `has_next`)
Provide contextual introspection over neighbouring elements in the animation chain without requiring additional persistent memory. The proxy objects `prev` and `next` expose all metric, temporal, and typographical properties of the adjacent element:

| Variable | Type | Description |
| :--- | :---: | :--- |
| `prev.text`, `prev.text_stripped` | `string` | Text of the previous element in the sequence. |
| `prev.x`, `prev.y`, `prev.center`, `prev.middle` | `float` | Spatial centre coordinates of the previous element (px). |
| `prev.left`, `prev.right`, `prev.top`, `prev.bottom` | `float` | Bounding box boundaries of the previous element (px). |
| `prev.width`, `prev.height` | `float` | Metric dimensions of the previous element (px). |
| `prev.start_time`, `prev.end_time`, `prev.dur` | `int` | Start time, end time, and duration of the previous element ($ms$). |
| `prev.i`, `prev.n` | `int` | Index and total count corresponding to the previous element. |
| `prev.fontname`, `prev.fontsize`, `prev.color1`..`4` | `var` | Typographical and style properties of the previous element. |
| `next.*` | `var` | Identical metrics and properties applied to the **next element** in the sequence. |
| `is_first` | `bool` | `True` if the active element is the first in the sequence (`i == 1` or without predecessor). Also accessible as `syl.is_first`, `char.is_first`, `word.is_first`. |
| `is_last` | `bool` | `True` if the active element is the last in the sequence (`i == n` or without successor). Also accessible as `syl.is_last`, `char.is_last`, `word.is_last`. |
| `has_prev` | `bool` | `True` if a valid predecessor unit exists in the line. |
| `has_next` | `bool` | `True` if a valid successor unit exists in the line. |

#### 1.4.4. Pyxis Default Variables, Global Environment, and Quick Accessors
These variables are natively injected into the global evaluation context of every node (`Define Vars`, `MultiTag`, `Conditioner`, etc.), accessible without prefixes:

| Variable | Type | Description and Formula |
| :--- | :---: | :--- |
| `frame_dur` / `fd` | `float` | Single video frame duration in milliseconds ($\approx 41.67\text{ ms}$ at 23.976/24 FPS or $40.0\text{ ms}$ at 25 FPS). |
| `fps` | `float` | Frames per second rate of the active video in Aegisub (e.g. `23.976`, `24.0`, `29.97`, `60.0`). |
| `ini` | `float` | Relative baseline time offset between dialogue line and effect: $\text{ini} = \text{line.start\_time} - \text{fx.start\_time}$. |
| `st`, `et` | `int` | High-speed direct aliases for active `start_time` and `end_time` ($ms$). |
| `dur` / `duration` | `int` | Net duration of the active unit or frame in milliseconds ($ms$). |
| `time_start`, `time_end`, `time_dur` | `int` | Canonical aliases for sub-element or frame timestamps. |
| `line_start_time`, `line_end_time`, `line_dur` | `int` | Start, end, and duration timestamps of the parent dialogue line ($ms$). |
| `syl_start_time`, `syl_end_time` | `int` | Start and end timestamps of the parent syllable ($ms$). |
| `i`, `n` | `int` | Ordinal iterator ($1 \dots N$) and total unit count in the primary loop. |
| `rx`, `ry` | `float` | Relative or accumulated horizontal and vertical spatial offsets (px). |
| `ratio` | `float` | Active temporal or modular progress ratio. |
| `module` / `m` | `float` | Normalised sub-loop progress ratio: $\text{module} = \frac{j - 1}{\text{maxj} - 1} \in [0.0, 1.0]$. |
| `pos_x`, `pos_y` | `float` | Primary spatial coordinates calculated for the active element (px). |
| `center`, `middle` | `float` | Horizontal and vertical centre of the active element (px). |
| `left`, `right`, `top`, `bottom` | `float` | Bounding box coordinates of the active element (px). |
| `width`, `height` | `float` | Width and height of the active element (px). |
| `x`, `y` | `float` | Reference Cartesian coordinates of the active element (px). |
| `result` | `string` | Standard return variable in the `System/Script Code` node for emitting text or tags to the `Result` pin. |

#### 1.4.5. Sub-Iterators of Meshes, Particles, and Sub-Loops
Variables dynamically injected when iterative generators are wired to the `Return` port of `System/Output`:

| Variable | Type | Generator and Description |
| :--- | :---: | :--- |
| `j`, `maxj`, `maxloop` | `int` | Ordinal counter ($1 \dots N$) and total iterations configured in `Loops/MaxLoop`. |
| `s_i`, `s_n`, `s_max` | `int` | Active piece index ($1 \dots N$) and total piece count generated by `Shape/Slicer`. |
| `slice_i`, `slice_n`, `slice_max` | `int` | Canonical aliases of `s_i` and `s_n` for expression compatibility. |
| `col`, `row` | `int` | Spatial column and row coordinates in cellular matrix segmentations (`Slicer`, `Array`). |
| `a_i`, `a_n` | `int` | Ordinal index of active particle and total elements in `Shape/Array` matrices. |
| `p_i`, `p_n` | `int` | Ordinal index and total particle count in `Functions/Particles` swarms. |
| `c_i`, `c_n`, `c_max` | `int` | Ordinal index and total slice count in `Functions/Clip Gradient`. |
| `clip_i`, `clip_n`, `clip_max` | `int` | Canonical aliases of `c_i` and `c_n` in `Functions/Clip Gradient`. |
| `d_i`, `d_n` | `int` | Ordinal index and count of polygons in `Shape/Union & Divide` partitions. |

#### 1.4.6. Quick Prefixed Accessors (`val_*`)
Provide direct, decoupled, and optimsied access to metrics of the current active element in mathematical expressions and `Sys Var`:

| Variable | Type | Equivalent Metric |
| :--- | :---: | :--- |
| `val_x`, `val_y` | `float` | Cartesian coordinates of the active unit (`active_unit.x`, `active_unit.y`). |
| `val_left`, `val_right` | `float` | Left and right horizontal boundaries (`active_unit.left`, `active_unit.right`). |
| `val_top`, `val_bottom` | `float` | Top and bottom vertical boundaries (`active_unit.top`, `active_unit.bottom`). |
| `val_center`, `val_middle` | `float` | Horizontal and vertical centre coordinates (`active_unit.center`, `active_unit.middle`). |
| `val_width`, `val_height` | `float` | Typographical dimensions (`active_unit.width`, `active_unit.height`). |
| `val_start` / `val_st` | `float` | Start timestamp in milliseconds (`active_unit.start_time`). |
| `val_end` / `val_et` | `float` | End timestamp in milliseconds (`active_unit.end_time`). |
| `val_dur` | `float` | Net duration in milliseconds (`active_unit.duration`). |
| `val_mid` | `float` | Temporal midpoint of the active unit: $t_{\text{start}} + \frac{t_{\text{dur}}}{2}$. |
| `val_i`, `val_n` | `int` | Ordinal index and total unit count of the active element. |

#### 1.4.7. Inter-Line Temporal Synchronisation (`sync.*`)
The `sync` subsystem calculates the temporal gap or offset with adjacent dialogue lines in milliseconds, enabling anticipation animations prior to line start or seamless collision-free transitions:

| Variable | Type | Search Criterion and Description |
| :--- | :---: | :--- |
| `sync.next` / `sync.prev` | `float` | Temporal gap in milliseconds to the next or previous line according to standard chronological order (capped at `max_gap`, 2000 ms by default). |
| `sync.order_next`, `sync.order_prev` | `float` | Gap to the immediately contiguous line in the physical line order of the ASS file. |
| `sync.style_next`, `sync.style_prev` | `float` | Gap to the next or previous line sharing **the same typographical style**. |
| `sync.actor_next`, `sync.actor_prev` | `float` | Gap to the next or previous line sharing **the same actor / character**. |
| `sync.effect_next`, `sync.effect_prev` | `float` | Gap to the next or previous line sharing **the same effect field**. |
| `sync.layer_next`, `sync.layer_prev` | `float` | Gap to the next or previous line located on **the same ASS layer**. |

> [!NOTE]
> **Sign Interpretation in `sync`:**
> * A **positive value ($> 0$)** indicates a pause or silence between both lines (e.g. $+850\text{ ms}$).
> * A **negative value ($< 0$)** indicates that both dialogue lines overlap simultaneously in time (*overlap*).

#### 1.4.8. Integrated Timers and Modifiers (`time.*`)
Enable computing sequential animation delays and phases directly from expressions or via `Sys Var`:

| Variable | Type | Kinematic Function |
| :--- | :---: | :--- |
| `time.lead_in` | `int` | Cumulative lead-in delay per syllable for anticipation animations (*lead-in*). |
| `time.lead_out` | `int` | Cumulative lead-out delay per syllable for exit animations (*lead-out*). |
| `time.middle_1` | `int` | Symmetrical delay calculated outward from the centre of the line towards the edges. |
| `time.middle_2` | `int` | Symmetrical delay calculated inward from the edges of the line towards the centre. |
| `time.loop_1` | `int` | Continuous cyclic animation timing in the entrance phase. |
| `time.loop_2` | `int` | Continuous cyclic animation timing in the exit phase. |

#### 1.4.9. Vector Shape Library Presets (`shape.*`)
The `shape` namespace provides Pyxis standard vector paths in ASSdraw format (`m ... l ... b ...`), accessible directly for clips, morphing transformations, or expressions in code:

| Preset | Canonical Identifier | Emitted Geometry |
| :--- | :--- | :--- |
| **Circle** | `shape.circle` | Perfect normalised Bézier circle centred at $(0, 0)$. |
| **Square** | `shape.square` | Equilateral square centred at $(0, 0)$. |
| **Rectangle** | `shape.rect` / `shape.rectangle` | Parametric rectangle centred at $(0, 0)$. |
| **Triangle** | `shape.triangle` | Equilateral triangle with top apex at $(0, 0)$. |
| **Rhombus** | `shape.diamond` / `shape.rhombus` | Diamond rhombus shape centred at $(0, 0)$. |
| **Rounded Corners** | `shape.rounded_corners` | Rectangle with fillet Bézier corner curvature on all 4 corners. |
| **Regular Polygons** | `shape.pentagon`, `shape.hexagon`, `shape.octagon` | Regular equilateral 5-, 6-, and 8-sided polygons. |
| **Star** | `shape.star` | Symmetrical 5-pointed star. |
| **Heart** | `shape.heart` | Bicubic centred vector heart path. |
| **Sakura** | `shape.sakura` | Stylised Japanese cherry blossom petal. |
| **Symbols and Weather** | `shape.cross`, `shape.cloud`, `shape.sun`, `shape.moon`, `shape.flower` | Classical vector iconography for particle animations. |

#### 1.4.10. Project Metadata (`meta.`) and Context Shapes
| Variable | Type | Description |
| :--- | :---: | :--- |
| `meta.res_x`, `meta.res_y` | `int` | Script rendering resolution (`PlayResX`, `PlayResY`, e.g. `1280`, `720` or `1920`, `1080`). |
| `shape.width`, `shape.height` | `float` | Bounding box pixel width and height of the evaluated vector path in context. |
| `shape.left`, `shape.right` | `float` | Minimum and maximum horizontal extents of the vector path. |
| `shape.top`, `shape.bottom` | `float` | Minimum and maximum vertical extents of the vector path. |
| `shape.center_x`, `shape.center_y` | `float` | Geometric centroid of the vector path: $(\frac{\text{left} + \text{right}}{2}, \frac{\text{top} + \text{bottom}}{2})$. |

#### 1.4.11. Visual Ink Metrics (`ink.`, `l.ink.`, `syl.ink.`, `char.ink.`, `word.ink.`)
Unlike standard typographical metrics (which compute the typographical bounding box including side-bearings and font ascender/descender margins), the **Ink Metrics** subsystem computes the actual vector contours of the rendered glyphs (*visual ink bounds*):

| Variable | Type | Description |
| :--- | :---: | :--- |
| `ink.width`, `ink.height` | `float` | Net pixel width and height of the rendered contour/glyph for the active unit (px). |
| `ink.left`, `ink.right` | `float` | Left and right boundary coordinates of the rendered ink pixels in screen space (px). |
| `ink.top`, `ink.bottom` | `float` | Top and bottom boundary coordinates of the rendered ink pixels in screen space (px). |
| `ink.center`, `ink.middle` / `ink.x`, `ink.y` | `float` | Exact horizontal and vertical centre of the rendered visual ink (px). |
| `ink.l.*` / `l.ink.*` | `float` | Complete ink metrics for the active dialogue line. |
| `ink.syl.*` / `syl.ink.*` | `float` | Complete ink metrics for the active syllable. |
| `ink.char.*` / `char.ink.*` | `float` | Complete ink metrics for the active character. |
| `ink.word.*` / `word.ink.*` | `float` | Complete ink metrics for the active word. |

---

### 1.5. Resolution Pipeline and Lookup Precedence

When `Sys Var` or the expression engine evaluates an identifier $V$, it executes the following deterministic lookup cascade:

```
                  ┌───────────────────────────────┐
                  │      Starts with 'sync.'?     │ ──► [Yes] ──► Inter-line temporal synchronisation query
                  └──────────────┬────────────────┘
                                 │ [No]
                  ┌──────────────▼────────────────┐
                  │      Starts with 'ink.'?      │ ──► [Yes] ──► Real visual ink vector contour inspection
                  └──────────────┬────────────────┘
                                 │ [No]
                  ┌──────────────▼────────────────┐
                  │ Is 'is_first' / 'is_last' /   │ ──► [Yes] ──► Topological relative position flags
                  │    'has_prev' / 'has_next'?   │
                  └──────────────┬────────────────┘
                                 │ [No]
                  ┌──────────────▼────────────────┐
                  │   Prefix 'prev.' or 'next.'?  │ ──► [Yes] ──► Adjacent unit metrics and typography
                  └──────────────┬────────────────┘
                                 │ [No]
                  ┌──────────────▼────────────────┐
                  │      Starts with 'shape.'?    │ ──► [Yes] ──► Normalised vector shape presets
                  └──────────────┬────────────────┘
                                 │ [No]
                  ┌──────────────▼────────────────┐
                  │   Is 'frame_dur' or 'ratio'?  │ ──► [Yes] ──► Active global temporal or modular progress
                  └──────────────┬────────────────┘
                                 │ [No]
                  ┌──────────────▼────────────────┐
                  │      Starts with 'val_'?      │ ──► [Yes] ──► Fast direct active unit scalar mapping
                  └──────────────┬────────────────┘
                                 │ [No]
                  ┌──────────────▼────────────────┐
                  │   Prefix 'fx.' or 'time.'?    │ ──► [Yes] ──► Kinematic offsets and integrated timers
                  └──────────────┬────────────────┘
                                 │ [No]
                  ┌──────────────▼────────────────┐
                  │   Prefix 'line.' / 'syl.' /   │ ──► [Yes] ──► Hierarchical element introspection
                  │        'char.' / 'word.'?     │               and baseline style properties
                  └──────────────┬────────────────┘
                                 │ [No]
                  ┌──────────────▼────────────────┐
                  │  Exists in context or meta?   │ ──► [Yes] ──► User-defined identifier or resolution metadata
                  └──────────────┬────────────────┘
                                 │ [No]
                                 ▼
                         Returns empty string ("")
```

---

### 1.6. Production-Verified Example

Extracting glyph metric coordinates and native syllable duration to position text and trigger a scale pulse during singing:

```
[Sys Var (var_name: syl.x)]   ──► [In1] ──┐
[Sys Var (var_name: syl.y)]   ──► [In2] ──┼──► [Dynamic Format] ──► Output.Tags
[Sys Var (var_name: syl.dur)] ──► [In3] ──┘
```

* **Template in `Dynamic Format`:**
  ```text
  {\an5\pos(%s, %s)\t(0, %s, \fscx125\fscy125\1c&H00FFFF&)}
  ```
* **Resulting Compiled ASS Line:**
  ```ass
  Dialogue: 0,0:01:12.40,0:01:15.80,Romaji,,0,0,0,,{\an5\pos(412.5, 680.0)\t(0, 320, \fscx125\fscy125\1c&H00FFFF&)}Ka
  ```

---

## 2. Node `Variables/Define Vars` (Local Variable Definition)

* **Canonical Category:** `Variables` (UI: *Variables / Define Vars*)
* **Purpose:** Declares and injects custom local variables evaluated in real time for each graph iteration cycle. Enables creating reusable intermediate calculations and simplifying complex expressions without cluttering the canvas with wire connections.

![Variables/Define Vars](img/define_vars.png)

---

### 2.1. Header Mode Combos
`Define Vars` operates universally both as a **pass-through dataflow node** and as a **loop chain node**. Clicking on the text area opens a multi-line code editor with syntax highlighting to write multiple newline-delimited assignments.

---

### 2.2. Input Ports and Body Properties (*Inputs & Properties*)
1. **`In` (`in_val`):** Pass-through input port. Accepts any data type (ASS tag strings, vector geometries, numbers, or text strings). If unwired, emits declared variables or an empty string.
2. **`Vars` (`variables`):** Multi-line text block containing variable declarations formatted as `key = expression`.
   * **Canonical Typification:** **Type A (Mathematical Formula / Evaluated Expression)**. Sequentially evaluated line-by-line within the mathematical expression evaluator environment.
   * **Declaration Syntax:**
     ```python
     radius = 50 + (syl.i * 10)
     angle = (j / maxj) * 360
     pos_x = syl.x + math.cos(math.radians(angle)) * radius
     pos_y = syl.y + math.sin(math.radians(angle)) * radius
     current_colour = "&H00FFFF&"
     ```

---

### 2.3. Output Ports (*Outputs*)
1. **`[1.1] Out`:** Transparently relays the data received at input `In` (*pass-through*), after injecting all defined variables into the active execution context dictionary.

#### Execution Context Side Effects:
All variables declared in `Vars` are immediately registered in context under their designated names (`radius`, `angle`, `pos_x`, etc.), becoming available to:
* Downstream `Variables/Get Var` nodes.
* `Basics/Dynamic Format` or `Basics/Math` nodes.
* Parenthesized `\tag(variable)` expressions in text strings and ASS override tag templates.

> [!NOTE]
> **Automatic Re-evaluation with Return Iterators:**
> When a node connected to the `Return` port of `System/Output` (such as `Shape/Slicer`, `Shape/Array`, `Functions/Particles`, `Functions/IMG to pixels`) generates internal sub-iterations (`s_i`, `a_i`, `p_i`, `d_i`, etc.), Pyxis automatically re-evaluates all active `Define Vars` declarations for each slice or particle prior to evaluating the tags connected to the `Tags` port. This ensures that expressions such as `by.s_i.R(-30, 30)` or formulas depending on `s_i` resolve to the exact per-piece value rather than a stale outer-loop value. Furthermore, variable definitions are strictly isolated per output queue (*Queue Isolation*), preventing cross-talk between multiple `Output` nodes.

---

### 2.4. Context Injection Synergy

```
                    +---------------------------+
                    | Loops/Main Loop (syl)     |
                    +-------------┬-------------+
                                  │
                                  ▼
                    +---------------------------+
                    | Variables/Define Vars     |
                    |   offset_x = syl.i * 12   |
                    |   rot = by.s_i.R(-20, 20) |
                    +-------------┬-------------+
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
      +---------------------------+ +---------------------------+
      | Variables/Get Var         | | Basics/Dynamic Format     |
      |   var_name: rot           | |   \frz(rot)\fscx(110)     |
      +---------------------------+ +---------------------------+
```

---

### 2.5. Production-Verified Example

Defining sinusoidal orbital translation and per-piece angular rotation for `Shape/Slicer`:

* **Declarations in `Define Vars` (`variables`):**
  ```python
  radius = 18 + (syl.i * 4)
  angle = (s_i / s_n) * 360
  pos_x = syl.x + math.cos(math.radians(angle)) * radius
  pos_y = syl.y + math.sin(math.radians(angle)) * radius
  rot = (s_i / s_n) * 180
  ```
* **ASS Tag Emitted via `Basics/Dynamic Format` towards `Output.Tags`:**
  ```text
  \pos(pos_x, pos_y)\frz(rot)\t(0, syl.dur, \alpha&HFF&)
  ```
* **Resulting Compiled ASS Line:**
  ```ass
  Dialogue: 0,0:01:12.40,0:01:15.80,Romaji,,0,0,0,,{\pos(425.2, 672.8)\frz(22.5)\t(0, 320, \alpha&HFF&)}Ka
  ```

---

## 3. Node `Variables/Get Var` (Context Variable Reader)

* **Canonical Category:** `Variables` (UI: *Variables / Get Var*)
* **Purpose:** Retrieves and outputs the current value of any context variable by its literal identifier name. Enables wireless routing across complex graphs and decoupled reading of loop iterators or dynamically injected variables.

![Variables/Get Var](img/get_var.png)

---

### 3.1. Header Mode Combos
Engineered for ultra-fast, zero-overhead queries. Requires no input ports and resolves in $\mathcal{O}(1)$ via direct hash-map context lookup.

---

### 3.2. Input Ports and Body Properties (*Inputs & Properties*)
1. **`Name` (`var_name`):** Variable identifier to query (e.g. `"j"`, `"maxj"`, `"module"`, `"custom_val"`, `"offset_x"`). (Default: `"j"`).
   * **Canonical Typification:** **Type C (Plain Text / Identifier)**. Strictly excluded from `ast.parse`.

---

### 3.3. Output Ports (*Outputs*)
1. **`[1.1] Data`:** Value extracted from context. If the variable has not been defined or does not exist in the active context, emits an empty string `""`.

---

### 3.4. Common Practical Use Cases
* **Reading Sub-Iterators:** Direct extraction of secondary loop counters (`j`, `maxj`, `module`) spawned by `Loops/MaxLoop` to feed interpolation or affine transform nodes.
* **Reading Injected Variables:** Reading results computed by `Variables/Define Vars` or scripts in `System/Script Code`.
* **Wireless Graph Routing:** Eliminates long crossing wires across expansive node graphs when a single calculated metric must feed multiple peripheral branches.

---

### 3.5. Production-Verified Example

Decoupled extraction of iterator `j` from `Loops/MaxLoop` to modulate opacity and scale across duplicate layers:

* **Graph Connections:**
  ```
  [Loops/MaxLoop (iterations: 4)]
  [Variables/Get Var (var_name: "j")] ──► [In1] ──► [Dynamic Format] ──► Output.Tags
  ```
* **Template in `Dynamic Format`:**
  ```text
  {\pos(syl.x, syl.y)\fscx(%s)\fscy(%s)\alpha(%s)}
  ```
* **Resulting Compiled ASS Line (for iteration $j = 3$):**
  ```ass
  Dialogue: 0,0:01:12.40,0:01:15.80,Romaji,,0,0,0,,{\pos(412.5, 680.0)\fscx145\fscy145\alpha&H60&}Ka
  ```

---

## 4. Node `Variables/Memory` (Persistent Key-Value Store)

* **Canonical Category:** `Variables` (UI: *Variables / Memory*)
* **Purpose:** Provides persistent variable storage (*State Retention*) across the entire graph evaluation session. Unlike standard context variables (which reset on each new syllable, line, or frame), `Memory` preserves values between consecutive execution cycles, enabling cumulative kinematics, numerical trajectory integrators, extreme value tracking ($\min / \max$), and conditional latches.

![Variables/Memory](img/memory.png)

---

### 4.1. Header Mode Combos
1. **`remember` (`save` / `SAVE`):** Write and update mode. Stores incoming data under the specified key in global memory and immediately passes it to the output for chaining.
2. **`retrieve` (`load` / `LOAD`):** Read mode. Queries the current value stored under the specified key. If the key has not been initialised in the session, emits the fallback value configured in `Value / Default`.

---

### 4.2. Input Ports and Body Properties (*Inputs & Properties*)
1. **`Key` (`key`):** Textual identifier or key name under which data is stored (e.g. `"prev_x"`, `"accum_rot"`, `"max_width"`).
   * **Canonical Typification:** **Type C (Plain Text / Identifier)**. Strictly excluded from `ast.parse`.
   * *Precedence:* Connected cable $\to$ Inline text field $\to$ Default `"ref"`.
2. **`Value` (`value` / `default`):**
   * In `remember` mode: Data to write into persistent memory.
   * In `retrieve` mode: Fallback default value emitted if the key does not yet exist in storage.
   * **Canonical Typification:** **Type A / Type C Polymorphic** (scalar numbers, coordinates, strings, or vector shapes).
   * *Precedence:* Connected cable $\to$ Inline text field $\to$ Empty string `""`.

---

### 4.3. Output Ports (*Outputs*)
1. **`[1.1] Data`:**
   * In `remember` mode: Emits the newly stored value (write pass-through mode).
   * In `retrieve` mode: Emits the value retrieved from persistent memory (or `default` if the key was not found).

---

### 4.4. Persistence Model and Cumulative Kinematic Formulations

The execution engine maintains a session-wide persistent dictionary $\mathcal{M} = \{\text{key} \mapsto \text{value}\}$ across the entire render run.

#### 4.4.1. Position Accumulator / Cumulative Offset
To generate a trajectory where each syllable $i$ starts at the ending position of the previous syllable $i-1$:

$$\text{pos}_x(i) = \text{retrieve}(\text{"last\_x"}, \text{default} = X_0) + \Delta x_i$$
$$\text{remember}(\text{"last\_x"}, \text{pos}_x(i))$$

```
                               Syllable Cycle i-1                      Syllable Cycle i
                         ┌───────────────────────────┐           ┌───────────────────────────┐
                         │ Memory (remember)         │           │ Memory (retrieve)         │
                         │   key: "pos_x"            │           │   key: "pos_x"            │
                         │   val: 320.5 px           │           │   val => 320.5 px         │
                         └─────────────┬─────────────┘           └─────────────┬─────────────┘
                                       │                                       │
                                       ▼                                       ▼
                         ┌───────────────────────────────────────────────────────────┐
                         │             Persistent Memory Store (_memory)              │
                         │                   {"pos_x": 320.5}                        │
                         └───────────────────────────────────────────────────────────┘
```

#### 4.4.2. Velocity and Gravity Integrator
In particle simulations and discrete physics with `MaxLoop` sub-loops:

$$v_y(j) = \text{retrieve}(\text{"vel\_y"}, 0.0) + g \cdot \Delta t$$
$$y(j) = \text{retrieve}(\text{"pos\_y"}, Y_0) + v_y(j) \cdot \Delta t$$
$$\text{remember}(\text{"vel\_y"}, v_y(j)) \quad \land \quad \text{remember}(\text{"pos\_y"}, y(j))$$

Where $g$ represents gravitational acceleration and $\Delta t$ the temporal integration step in milliseconds.

---

### 4.5. Production Synergies and Best Practices

1. **Deterministic Reset Pattern with `Basics/Once`:**
   When implementing inter-line kinematic accumulators, chain a `Basics/Once` node to reset memory at the start of each line (`mode: line`), ensuring residual state from earlier lines does not pollute subsequent events:
   ```
   [Basics/Once (line)] ──► [Variables/Memory (remember: "accum_x" = 0.0)]
   ```

2. **Dynamic Bounding Box and Extent Tracking:**
   To calculate maximum glyph width dynamically across a phrase in real time:
   ```
   [Math (max: syl.width, Memory.retrieve("max_w", 0))] ──► [Memory (remember: "max_w")]
   ```

3. **Decoupled Cross-Subgraph Communication:**
   Allows an upstream typographic calculation subgraph to save scaling or colour parameters in memory for a downstream particle or glow subgraph to read without routing wires across the canvas.

---

### 4.6. Production-Verified Example

Continuous horizontal inter-syllable kinematic accumulator across a line for dynamic flowing spacing:

* **Graph Connections:**
  ```
  [Basics/Once (line)] ──► [Memory (mode: remember, key: "last_x", value: line.left)]
  [Memory (mode: retrieve, key: "last_x", default: line.left)] ──► [Math (+ syl.width + 10)] ──► [Memory (mode: remember, key: "last_x")]
  ```
* **Resulting Compiled ASS Line:**
  ```ass
  Dialogue: 0,0:01:12.40,0:01:15.80,Romaji,,0,0,0,,{\an7\pos(384.0, 680.0)}Ka
  Dialogue: 0,0:01:12.40,0:01:15.80,Romaji,,0,0,0,,{\an7\pos(424.0, 680.0)}ra
  Dialogue: 0,0:01:12.40,0:01:15.80,Romaji,,0,0,0,,{\an7\pos(462.5, 680.0)}o
  ```

---

## 5. Comparative Matrix of Variables and Storage Nodes

| Node | Operating Mode | Lifecycle Scope | Complexity | Behaviour on Missing Key | Property Categorisation | Primary Use Case |
| :--- | :--- | :--- | :---: | :--- | :---: | :--- |
| **`Sys Var`** | Environment query | Read-only (Native ASS context) | $\mathcal{O}(1)$ | Emits empty string `""` | Type C (`var_name`) | Extracting syllable, line, resolution, and time metrics. |
| **`Define Vars`** | Local injection | Active iteration cycle | $\mathcal{O}(K)$ | Assigns literal `val_expr` on failure | Type A (`variables`) | Declaring intermediate variables and mathematical expressions. |
| **`Get Var`** | Dynamic query | Active context | $\mathcal{O}(1)$ | Emits empty string `""` | Type C (`var_name`) | Decoupled reading of variables and loop iterators (`j`). |
| **`Memory`** | Write / Read | Persistent (Full session) | $\mathcal{O}(1)$ | Emits configured `default` value | Type C (`key`), Type A/C (`value`) | Physical accumulators, iterative kinematics, and state retention. |

---

## 6. Canonical Property Categorisation (Types A, B, and C) and AST Resolution

Every string property across Pyxis is strictly categorised into one of three canonical evaluation classes, coordinating the execution engine, string evaluator, and static linter:

### 6.1. Type A Properties: Mathematical Formulas and AST Expressions

* **Runtime Behaviour:** Evaluated numerically line-by-line via the Python expression engine. Supported syntax includes:
  * Standard arithmetic operators: `+`, `-`, `*`, `/`, `//`, `%`, `**`.
  * Ternary conditional expressions: `value_a if condition else value_b`.
  * Standard mathematical library functions: `math.sin()`, `math.cos()`, `math.radians()`, `math.sqrt()`, `abs()`, `min()`, `max()`, `round()`.
  * Deterministic stochastic functions tied to iterators: `by.<iter>.R(min, max)`, `by.syl.R(min, max)`, `R()`, `Rm()`.
* **Linter Behaviour:** Analysed statically via `ast.parse(mode="eval")`. The validator verifies that identifiers belong to known global variables or were declared upstream in the graph, warning of undeclared variables or syntax errors.
* **Representative Properties:**
  * `Variables/Define Vars`: `variables` property (`Vars`).
  * `Basics/Math`: numerical inputs and fields `A`, `B`.
  * `Functions/Conditioner`: `condition` field.
  * `Basics/Only`: `condition` field.
  * `Shape/Filter`: `expr_x`, `expr_y` fields.

### 6.2. Type B Properties: ASS Tag Templates and Macros

* **Runtime Behaviour:** Processed sequentially by the string evaluator (`string_evaluator.py`). Operations performed:
  * Variable substitution and interpolation within tag parentheses: `\pos(syl.x, syl.y)`, `\frz(rot)`, `\fscxy(scale)`.
  * Animation timing shortcuts: time modifiers (`2li`, `3lo`, `1m1`) and frame numbers (`10f`).
  * Dark Tag expansions (`~`, `\tagR(...)`).
  * Arithmetic subexpressions enclosed in parentheses `\tag(subexpr)` are routed internally to the Type A evaluator.
* **Linter Behaviour:** Checked via ASS tag syntax validation (`_validate_tags`), verifying delimiter parity (`{`, `}`, `(`, `)`), expected argument counts for each ASS tag, and delegating numerical subexpressions to Type A validation rules.
* **Representative Properties:**
  * `Basics/Dynamic Format`: `format` field.
  * `System/Output`: `Tags` and `Return` inputs.
  * `Basics/MultiTag`: tag prefix and suffix fields.

### 6.3. Type C Properties: Plain Text, Identifiers, and Pass-Through

* **Runtime Behaviour:** Treated as literal strings without expression parsing or code evaluation.
* **Linter Behaviour:** Only basic delimiter balancing (`()`, `{}`) is verified to prevent subtitle formatting breakages in Aegisub. **Strictly excluded from `ast.parse`** to avoid false positives on arbitrary text or operator-like strings.
* **Representative Properties:**
  * `Variables/Get Var`: `var_name` field.
  * `Variables/Memory`: `key` field.
  * `Basics/String`: `value` field.
  * `Basics/Text`: `text` field.
  * `Functions/Conditioner`: literal text fields `if_true`, `if_false` (when containing no ASS tags prefixed with `\`).

---

## 7. Lifecycle Scopes, Hierarchical Resolution, and Collision Prevention

### 7.1. Scope Hierarchy in Nested Loops

During subtitle processing, Pyxis descends through a strict hierarchical cascade of contexts. Variables from higher scopes are inherited by all child scopes, but local variables injected within a sub-loop do not leak upwards:

$$\text{Line (Global)} \longrightarrow \text{Primary Unit (Syllable / Char / Word)} \longrightarrow \text{Sub-Loop (MaxLoop)} \longrightarrow \text{Iterative Return (Piece / Particle)}$$

1. **Line Level:** `line.*`, `l.*`, `line_start_time`, `line_end_time`, `line_dur`, `meta.res_x`, `meta.res_y`.
2. **Primary Unit Level:** `syl.*`, `char.*`, `word.*`, `x`, `y`, `center`, `middle`, `left`, `right`, `top`, `bottom`, `width`, `height`, `i`, `n`, `dur`, `st`, `et`.
3. **Sub-Loop Level:** `j`, `maxj`, `module`, `maxloop`.
4. **Iterative Return Level:** `s_i`, `s_n` (Slicer), `a_i`, `a_n` (Array), `p_i`, `p_n` (Particles), `c_i`, `c_n` (Clip Gradient), `d_i`, `d_n` (Union & Divide).

### 7.2. Output Queue Isolation (*Queue Isolation*)

When the graph contains multiple `System/Output` nodes, each render queue processes its subgraph in complete isolation. Variables declared via `Variables/Define Vars` in Layer 1 branch do not leak into or interfere with Layer 2 branch variables, guaranteeing predictability and determinism.

### 7.3. Guidelines for Preventing Name Collisions

1. **Do not overwrite reserved identifiers:** Avoid assigning variables named `x`, `y`, `i`, `n`, `dur`, `st`, `et` in `Define Vars` unless intentionally updating glyph kinematics through native engine prop propagation (`_apply_fx_setting`).
2. **Use contextual prefixes:** In complex effect chains, employ descriptive prefixes (e.g. `orb_rad`, `p_vel_x`, `wave_phase`) to avoid collisions with global variables and enhance graph readability.
3. **Preserve loop counters in nested structures:** When combining a `Loops/MaxLoop` sub-loop (`j`) with an iterative return generator like `Shape/Slicer` (`s_i`), do not reassign `j` in `Define Vars`. Access `j` via `Variables/Get Var` or reference it directly in expressions.

---

## 8. Performance Best Practices and State Retention

### 8.1. Stochastic and Line-Reset Pattern in `Memory`

Because `Variables/Memory` preserves data across the entire render session, a kinematic accumulator summing displacements between syllables will continue accumulating indefinitely unless reset. To bound accumulation to each individual dialogue line, reset it conditionally using `Basics/Once`:

```
[Basics/Once (mode: line)] ──► [Variables/Memory (mode: remember, key: "acc_x", value: 0.0)]
```

This pattern guarantees that when a new dialogue line begins, the `"acc_x"` key is re-initialised to `0.0`, preventing state carryover between separate lines.

### 8.2. Design Decision: Direct Wire vs. `Get Var`

* **Direct Cable Connection:** Recommended for local and immediate dependencies within the same visual subgraph. Keeps data flow explicit and visible on the canvas.
* **`Get Var` Node:** Recommended in the following scenarios:
  * When a parameter computed on one side of a large canvas must feed distant peripheral branches, eliminating long crossing wires (*wire clutter*).
  * Reading dynamically injected iterators (`j`, `s_i`, `a_i`) that lack physical output pins on the loop node.
  * Supplying values to nodes that only offer inline text fields.

### 8.3. Topological Placement of `Define Vars`

To ensure declared variables are available to all dependent nodes during each iteration, the `Variables/Define Vars` node must be placed **upstream** of consumer nodes, ideally inserted along the pass-through execution path linking `Loops/Main Loop` to `System/Output`.
