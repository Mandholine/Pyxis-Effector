# Functions

The **Functions** category contains 16 specialised nodes dedicated to algebraic ASS tag manipulation, oscillator synthesis, conditional logic, colour gradients, kinematics, and vector deformation.

### Chapter Thematic Structure:
* **Section 8.A — Tag Modulation, Oscillators, and Conditional Logic:** [`Tag Manipulator`](#1-node-functionstag-manipulator-ass-tag-manipulator) (§1), [`Tag Oscillator`](#2-node-functionstag-oscillator-periodic-tag-modulator) (§2), [`Glitter`](#3-node-functionsglitter-stochastic-sparkle-generator) (§3), [`Conditioner`](#4-node-functionsconditioner-logical-data-branching) (§4), [`Animation`](#8-node-functionsanimation-fbf-frame-switcher-and-alpha-modulator) (§8).
* **Section 8.B — Colour Gradients, Raster-to-Pixels, and Kinematics:** [`Color Gradient`](#5-node-functionscolor-gradient-multi-stop-colour-gradient) (§5), [`Clip Gradient`](#6-node-functionsclip-gradient-clipping-bands-and-meshes-for-multi-layer-gradients) (§6), [`IMG to pixels`](#7-node-functionsimg-to-pixels-raster-sampling-to-particle-swarms) (§7), [`Polar to Cartesian`](#12-node-functionspolar-to-cartesian-polar-to-cartesian-converter) (§12), [`Interpolator`](#14-node-functionsinterpolator-polymorphic-parametric-interpolator) (§14).
* **Section 8.C — Bézier Curves, Particle Swarms, and Vectorised Typography:** [`Bezier Curve`](#9-node-functionsbezier-curve-2d-bézier-splines-and-trajectories) (§9), [`Move Tag`](#10-node-functionsmove-tag-kinematic-ass-motion-sequences) (§10), [`Move Text`](#11-node-functionsmove-text-coordinated-inline-typographic-motion) (§11), [`Particles`](#13-node-functionsparticles-vector-particle-swarms) (§13), [`Text on Path`](#15-node-functionstext-on-path-text-flow-along-curved-paths) (§15), [`Text to Shape`](#16-node-functionstext-to-shape-typographic-glyph-vectorisation) (§16).

---

## 1. Node `Functions/Tag Manipulator` (ASS Tag Manipulator)

* **Canonical Category:** `Functions` (UI: *Functions / Tag Manipulator*)
* **Purpose:** Executes algebraic transformations on ASS tag strings, including negative parameter inversion (complementary colours, inverted alpha channels, opposing rotations, inverse clipping masks), tag resetting to the active style defaults, and introspection/extraction of numeric and literal values from specific tags.

![Functions/Tag Manipulator](img/tag_manipulator.png)

---

### 1.1. Header Mode Combos
1. **`Mode` (`mode`):** Interactive dropdown selector that switches the operational behaviour of the node and dynamically reconfigures its input and output sockets:
   * **`invert` (INV):** Algebraically inverts each ASS tag contained in the input string (including tags nested inside `\t(...)` blocks).
   * **`reset` (RESET):** Reads the active subtitle style in context and generates override tags that restore baseline default values.
   * **`extractor` (EXTRACT):** Inspects the incoming tag stream, searches for the last occurrence of the tag specified in `Target Tag`, and extracts its clean value, numeric representation, and raw matching block.

---

### 1.2. Input Ports and Body Properties (*Inputs & Properties*)

#### In `invert` (INV) and `reset` (RESET) Modes:
1. **`Tags In` (`tags`):** String containing the ASS tags to process. Accepts direct static tags (e.g. `\frz45\1c&H0000FF&\alpha&H80&`), continuous transformations (e.g. `\t(0,300,\frz-45\fscx150)`), or `"all"` / blank in Reset mode to regenerate the full baseline style. (Default: `""`).

#### In `extractor` (EXTRACT) Mode:
1. **`Tags In` (`tags`):** ASS tag string from which information will be extracted (e.g. `{\pos(320,240)\frz-35.5\1c&H00FF88&}`).
2. **`Target Tag` (`target_tag`):** Name identifier of the tag to search for (with or without leading backslash `\`). Supports canonical ASS aliases such as `frz` / `fr`, `1c` / `c`, `alpha`, `fscx`, `pos`, `org`, `clip`, `blur`, etc. (Default: `"frz"`).

---

### 1.3. Output Ports (*Outputs*)

#### In `invert` (INV) and `reset` (RESET) Modes:
1. **`[1.1] Tags Out`:** Resulting text string containing algebraically transformed tags or style reset override tags.

#### In `extractor` (EXTRACT) Mode:
1. **`[1.1] String`:** Clean text value extracted from the tag without tag prefixes or enclosing parentheses (e.g. `"-35.5"`, `"320,240"`, `"&H00FF88&"`).
2. **`[1.2] Value`:** Numeric floating-point (`float`) conversion of the extracted value. For composite coordinates (e.g. `320,240`), returns the first numeric component (`320.0`). For 1- or 2-digit hexadecimal colour/alpha channels, converts them to their decimal integer equivalent ($0 \dots 255$).
3. **`[1.3] Raw String`:** Complete literal matching tag block as found in the input string (e.g. `\frz-35.5`, `\pos(320,240)`).

---

### 1.4. Algorithmic Detail and ASS Tag Algebra

#### 1.4.1. Algebraic Inversion Rules (`Mode: invert`)
The algorithm parses the lexical stream, decomposes atomic blocks, and applies the following formal mathematical symmetry rules:

| ASS Tag Family | Supported Tags | Mathematical Inversion Rule | Example Input $\to$ Output |
| :--- | :--- | :--- | :--- |
| **Primary & Secondary Colours** | `\c`, `\1c`, `\2c`, `\3c`, `\4c` | **Negative RGB Complementary:**<br>$(R', G', B') = (255 - R, 255 - G, 255 - B)$ | `\1c&H0000FF&` $\to$ `\1c&HFFFF00&` (Blue $\to$ Yellow) |
| **Alpha Channels** | `\alpha`, `\1a`, `\2a`, `\3a`, `\4a` | **Hexadecimal Complement:**<br>$\alpha' = 255 - \alpha$ | `\alpha&H00&` $\to$ `\alpha&HFF&` (Opaque $\to$ Transparent) |
| **Rotations, Shearing & Shadows** | `\frz`, `\frx`, `\fry`, `\fr`, `\fax`, `\fay`, `\fsp`, `\xshad`, `\yshad` | **Arithmetic Sign Inversion:**<br>$V' = -V$ | `\frz35` $\to$ `\frz-35`<br>`\fax0.5` $\to$ `\fax-0.5` |
| **Borders, Blurs & Scalar Shadows** | `\bord`, `\xbord`, `\ybord`, `\blur`, `\be`, `\shad` | **Nullification / Zero Reset:**<br>$V' = 0$ | `\bord4\blur3` $\to$ `\bord0\blur0` |
| **Transformation Scales** | `\fscx`, `\fscy` | **Return to Baseline Scale:**<br>$V' = \text{Style.Scale}$ (or $100\%$) | `\fscx200` $\to$ `\fscx100` |
| **Vector Clipping Masks** | `\clip`, `\iclip` | **Inverse Mask Toggle:**<br>`\clip` $\longleftrightarrow$ `\iclip` | `\clip(m 0 0 ...)` $\to$ `\iclip(m 0 0 ...)` |

#### 1.4.2. Recursive Inversion in Time Blocks `\t(...)`
When the string contains temporal transformation blocks `\t(t1, t2, [accel,] tags)`, the parser isolates the inner tag body, applies algebraic inversion strictly to the nested tags, and recombines the block without modifying time intervals or acceleration curves:

$$\text{\textbackslash t}(100, 400, 1.5, \text{\textbackslash frz45\textbackslash 1c\&H0000FF\&}) \quad \longrightarrow \quad \text{\textbackslash t}(100, 400, 1.5, \text{\textbackslash frz-45\textbackslash 1c\&HFFFF00\&})$$

#### 1.4.3. Baseline Style Reset (`Mode: reset`)
The engine queries the `styleref` of the active context (`active_unit` or `line`) and extracts the baseline values configured in the ASS dialogue header:
* If `Tags In` is empty, `"all"`, or `"todo"`, it generates the comprehensive reset sequence:
  $$\text{\textbackslash 1c}\dots\text{\textbackslash 2c}\dots\text{\textbackslash 3c}\dots\text{\textbackslash 4c}\dots\text{\textbackslash 1a}\dots\text{\textbackslash 2a}\dots\text{\textbackslash 3a}\dots\text{\textbackslash 4a}\dots\text{\textbackslash alpha\&H00\&}\text{\textbackslash fscx}\dots\text{\textbackslash fscy}\dots\text{\textbackslash fs}\dots\text{\textbackslash fsp}\dots\text{\textbackslash bord}\dots\text{\textbackslash shad}\dots\text{\textbackslash frz}\dots$$
* If `Tags In` contains specific tags (e.g. `\1c\fscx`), it generates reset values strictly for the requested tags.

---

### 1.5. Synergies and Practical Workflow Examples
* **Mirror and Symmetry FX:** In twin loops or bi-directional bouncing particles, route one branch directly and pass the other branch through `Tag Manipulator (INV)` to automatically invert angles `\frz`, shear `\fax`, and relative shadow offsets.
* **Coordinate Extraction for Kinematics:** Route the `String` output of `Tag Manipulator (EXTRACT)` configured with `Target Tag: pos` into a `Math` node to derive relative trajectories based on original glyph anchor positions.

### 1.6. Practical Production Example
* **Bilateral Transformation Reflection with Invert Mode:**
  Feeding two concurrent layers to generate an opposing symmetrical motion trail without redundant manual recalculation:

  ```
  [Basics/MultiTag: \frz30\fscx120] ──► Tags In ──► [System/Output (Layer 2)]
                 │
                 └──► Tags In ──► [Functions/Tag Manipulator: mode=invert] ──► Tags Out ──► [System/Output (Layer 1)]
  ```

  * **Layer 2 (Direct):** Emits `{\an5\pos(syl.center, syl.middle)\frz30\fscx120}`.
  * **Layer 1 (Inverted):** Emits `{\an5\pos(syl.center, syl.middle)\frz-30\fscx100}`, flipping rotation to $-30^\circ$ and restoring scale to $100\%$ automatically.

---

## 2. Node `Functions/Tag Oscillator` (Periodic Tag Modulator)

* **Canonical Category:** `Functions` (UI: *Functions / Tag Oscillator*)
* **Purpose:** Continuous generator of periodic, stroboscopic, rhythmic, or wave-based modulations across any ASS property. Compiles temporal sequences into coordinated `\t(...)` blocks over the active element's lifetime.

![Functions/Tag Oscillator](img/tag_oscillator.png)

---

### 2.1. Header Mode Combos
1. **`Oscillation Mode` (`mode`):** Determines the transition envelope and temporal profile:
   * **`wave` (Continuous Wave - Default):** Smooth and continuous transition between states in the tag list ($T_{\text{trans}} = S_i$).
   * **`steps` / `flashes` / `strobe` (Stepped / Strobe):** Instantaneous discrete shifts without intermediate interpolation ($t_2 = t_1 + 1$).
   * **`pulses` (Pulses):** Modulation where the transition occupies $50\%$ of the step while the remainder remains static.
   * **`rhythmic` (Rhythmic):** Time steps are non-uniform, sequentially reading interval durations from `Rhythm Pattern`.
   * **`noise` (Noise):** Step variation with pseudo-random fluctuations.
2. **`Order Mode` (`order_mode`):** Governs tag selection ordering from the provided list:
   * **`sequential` (Sequential - Default):** Cycles through the tag list ($0, 1, 2, \dots, N-1, 0, 1, \dots$).
   * **`pingpong` (Ping-Pong):** Alternates forward and backward ($0, 1, 2, 1, 0, 1, \dots$).
   * **`random` (Random):** Picks a random tag at each step using a deterministic stochastic seed.
   * **`shuffle` (Shuffle without Immediate Repeat):** Selects pseudo-randomly ensuring no consecutive identical tags.

---

### 2.2. Input Ports and Body Properties (*Inputs & Properties*)
1. **`Start Time` (`start_time`):** Oscillator start timestamp in milliseconds relative to the physical line (blank defaults to `0.0 ms`). (Default: `""`).
2. **`End Time` (`end_time`):** Oscillator end timestamp in ms (blank automatically retrieves active element duration `fx.dur`, `syl.duration`, or `line.duration`). (Default: `""`).
3. **`Step (ms)` (`step_ms`):** Duration of each step/cycle in milliseconds. (Default: `200.0`).
4. **`Trans (ms)` (`trans_ms`):** Duration taken to interpolate via `\t` towards the next tag. (Default: `50.0`).
5. **`Duty Cycle` (`duty_cycle`):** Duty cycle ratio in the range $[0.01, 1.0]$. When connected or set, overrides `Trans (ms)` by computing $T_{\text{trans}} = S_i \cdot \text{DutyCycle}$.
6. **`Tags` (`tags`):** Comma-separated or newline-delimited list of tag strings (e.g. `\frz30\fry20, \frz-20\fry-20` or `\1c&HFF0000&, \1c&H00FF00&, \1c&H0000FF&`).
7. **`Accel` (`accel`):** ASS acceleration exponent injected into each `\t(...)` block. (Default: `1.0`).
8. **`Dilate Step` (`dilat_step_ms`):** Additive factor progressively dilating or compressing the step per iteration: $S_i = S_0 + \Delta_{S} \cdot i$. (Default: `0.0`).
9. **`Dilate Trans` (`dilat_trans_ms`):** Additive factor dilating or contracting the transition per iteration: $T_i = T_0 + \Delta_{T} \cdot i$. (Default: `0.0`).
10. **`Seq Offset` (`offset_seq_ms`):** Additional temporal pause injected upon completing a full cycle of the tag list. (Default: `0.0`).
11. **`Rhythm Pattern` (`rhythm_pattern`):** Comma-separated duration list (e.g. `100, 50, 200, 100`) for syncopated rhythmic patterns in `rhythmic` mode.

---

### 2.3. Output Ports (*Outputs*)
1. **`[1.1] Tag Out`:** Compiled continuous chain of ASS `\t(t1, t2, [accel,] tags)` blocks covering the full time span.
2. **`[1.2] Current Val`:** Active tag evaluated at the current frame timestamp (`frame_time` or `fx_start_time`).
3. **`[1.3] Keyframes`:** Structured data list of tuples containing all calculated keyframes `[(t1, t2, tag_str, accel), ...]`.
4. **`[1.4] Values`:** Simple list of tag text states evaluated at each step.

---

### 2.4. Algorithmic Formulation and Kinematics

```
Mode: wave (Continuous Transition)
Tags: [ Tag A, Tag B ]
───┬─────────────┬─────────────┬─────────────┬─────────────► Time (ms)
   │ \t(0,200,B) │\t(200,400,A)│\t(400,600,B)│\t(600,800,A)│
   0            200           400           600           800

Mode: steps / strobe (Instantaneous Switching)
───┬─────────────┬─────────────┬─────────────┬─────────────► Time (ms)
   │ \t(0,1,B)   │ \t(200,201,A) \t(400,401,B)│ \t(600,601,A)
   0            200           400           600           800
```

#### 2.4.1. Step and Transition Calculation per Iteration ($i$)
For each step $i \ge 0$:
1. **Time Step ($S_i$):**
   $$S_i = \begin{cases} \text{RhythmPattern}[i \pmod M] & \text{if } \text{rhythm\_pattern} \ne \emptyset \\ \max(5.0, S_{\text{step}} + \Delta_{\text{dilate\_step}} \cdot i) & \text{otherwise} \end{cases}$$
2. **Transition Window ($T_i$):**
   $$T_i = \begin{cases} 0 & \text{if mode is } \text{steps/strobe/flashes} \\ S_i \cdot \text{clamp}(DC, 0.01, 1.0) & \text{if } \text{DutyCycle is defined} \\ \min(S_i, \max(0.0, T_{\text{trans}} + \Delta_{\text{dilate\_trans}} \cdot i)) & \text{in standard mode} \end{cases}$$
3. **Timestamp Generation:**
   $$t_1 = \text{round}(T_{\text{start}} + t_{\text{curr}}), \quad t_2 = \begin{cases} t_1 + 1 & \text{if } T_i \le 0 \\ \min(t_{\text{end}}, \text{round}(t_1 + T_i)) & \text{otherwise} \end{cases}$$

---

### 2.5. Synergies and Practical Workflow Examples
* **Jitter and Angular Vibrato:** Set `Tags` to `\frz-5, \frz5` with `Step: 60` and `Trans: 30` to generate a continuous subtle vibrato on sung syllables.
* **Audio-Synchronised Pulsing:** Set `Mode: rhythmic` and enter millisecond transient intervals derived from audio tracking (`125, 250, 125, 375`) into `Rhythm Pattern`.

### 2.6. Practical Production Example
* **Kinematic Vibrato and Scale Wave on Sustained Notes:**
  Synthesising continuous harmonic undulation across a glyph over a $300\text{ ms}$ syllable duration:

  ```
  [Functions/Tag Oscillator: mode=wave, step_ms=80, trans_ms=40] ──► Tag Out ──► Tags ──► [System/Output]
     tags: "\frz-4\fscy95, \frz4\fscy105"
  ```

  * **Generated ASS Blocks in `Tag Out`:**
    ```ass
    \t(0,40,\frz-4\fscy95)\t(80,120,\frz4\fscy105)\t(160,200,\frz-4\fscy95)\t(240,280,\frz4\fscy105)
    ```
  * Smoothly interpolates between $\mp 4^\circ$ tilts and $95\%$ to $105\%$ vertical stretch, timing kinetic motion seamlessly with singing rhythm.

---

## 3. Node `Functions/Glitter` (Stochastic Sparkle Generator)

* **Canonical Category:** `Functions` (UI: *Functions / Glitter*)
* **Purpose:** Asynchronous stochastic emitter that generates luminous flashes, pulses, gentle waves, or noise variations across multiple ASS properties simultaneously, simulating organic shimmer and glitter without predictable repetition.

![Functions/Glitter](img/glitter.png)

---

### 3.1. Header Mode Combos
1. **`Mode` (`mode` / `random_profile`):** Selects the temporal envelope and particle morphology:
   * **`flashes` (Fast Sparkle - Default):** Long random pause $\to$ ultra-fast attack ($1 \dots 3\text{ ms}$) $\to$ short sustain ($5 \dots 15\text{ ms}$) $\to$ long decay ($40 \dots 100\text{ ms}$). Ideal for sparkles and glitter.
   * **`pulses` (Pulses):** Moderate pause $\to$ progressive rise ($150 \dots 250\text{ ms}$) $\to$ sustain $\to$ symmetrical fall with non-linear acceleration.
   * **`waves` (Gentle Waves):** Slow, continuous rise-and-fall transitions ($250 \dots 400\text{ ms}$) without sharp pauses.
   * **`noise` (Stochastic Noise):** Ultra-short steps ($15 \dots 50\text{ ms}$) with per-frame random values.

---

### 3.2. Input Ports and Body Properties (*Inputs & Properties*)
1. **`Start Time` (`start_time`):** Effect start timestamp in milliseconds. (Default: `"0"`).
2. **`End Time` (`end_time`):** Effect end timestamp in ms or context expression (e.g. `"fx.dur"`). (Default: `"fx.dur"`).
3. **`Density` (`density`):** Stochastic frequency multiplier. Values $> 1.0$ shorten pauses to generate more sparkles per second; values $< 1.0$ space out events. (Default: `1.0`).
4. **`Seed` (`seed`):** Integer seed ensuring reproducible deterministic pseudo-random output. (Default: `0`).
5. **Expandable Track Inputs (`In 1`, `In 2`, ...):** Each track defines a triplet:
   * **`Tag` (`tag_k`):** ASS tag to animate (e.g. `\fscx`, `\1c`, `\blur`, `\alpha`, `\frz`).
   * **`Min` (`min_k`):** Baseline resting value (number, percentage, hexadecimal colour `#RRGGBB` or `&HBBGGRR&`).
   * **`Max` (`max_k`):** Peak value reached at the apex of the flash.

#### Compound "Dark Tags" Support
`Glitter` automatically recognises and decomposes grouped tags:
* `\fscxy` $\longrightarrow$ animates `\fscx` and `\fscy` in parallel with identical values.
* `\frxyz` $\longrightarrow$ animates `\frx`, `\fry`, and `\frz` simultaneously.
* `\134c` $\longrightarrow$ synchronises primary (`\1c`), border (`\3c`), and shadow (`\4c`) colours.
* `\xybord` $\longrightarrow$ expands to `\xbord` and `\ybord`.
* `\bs` $\longrightarrow$ modulates border `\bord` and shadow `\shad` together.

---

### 3.3. Output Ports (*Outputs*)
1. **`[1.1] List`:** Combined string of all `\t(...)` blocks from all tracks synchronised at identical timestamps.
2. **`[1.2] TAG 1`:** String containing `\t(...)` blocks generated strictly for the first tag track.
3. **`[1.3] TAG 2` (Expandable):** String containing `\t(...)` blocks for the second track, and so on.

---

### 3.4. Algorithmic Detail and Stochastic Envelope Model

```
Profile Envelope: flashes (Sparkle)
Max Value (Apex) ────────┐       /───\
                         │      /     \
                         │     /       \
Base Value (Rest) ───────┴────/         \──────────────
                         ▲    ▲ ▲     ▲ ▲
                         │    │ │     │ │
                         └──┬─┘ └─┬─┘ └─┬────────┘
                         Pause   Attack  Decay
                         (dens)  (1-3ms) (40-100ms)
```

1. **Deterministic Per-Unit Generation:**
   The pseudo-random generator seed is uniquely indexed by the active syllable or glyph ($i$):
   $$\text{Seed}_{\text{local}} = \text{Seed} \cdot 1000 + i + 1337$$
2. **Stochastic Chromatic Interpolation:**
   If `Min` and `Max` boundaries represent colours, the algorithm decomposes channels $(R_1, G_1, B_1)$ and $(R_2, G_2, B_2)$ and interpolates in RGB space:
   $$R_{\text{rand}} = \text{round}(R_1 + (R_2 - R_1) \cdot \text{Factor}), \quad G_{\text{rand}} = \text{round}(G_1 + (G_2 - G_1) \cdot \text{Factor})$$
   Emitting colour codes in ASS `&HBBGGRR&` format.

---

### 3.5. Synergies and Practical Workflow Examples
* **Magic Shimmer / Fairy Dust:** Assign tag `\fscxy` with range `(100, 160)` to `In 1` and tag `\1c` with range `(#FFFFFF, #FFE460)` to `In 2`. Connect output `List` to `System/Output` for simultaneous scale and golden colour bursts.

### 3.6. Practical Production Example
* **Golden Sparkles and Stochastic Micro-Scaling (*Golden Sparkle Flash*):**
  Synthesising asynchronous bursts across individual characters over a $400\text{ ms}$ duration:

  ```
  [Functions/Glitter: mode=flashes, density=1.5, start=0, end=400] ──► List ──► Tags ──► [System/Output]
     In 1: tag=\fscxy, min=100, max=140
     In 2: tag=\1c, min=#FFFFFF, max=#FFD700
  ```

  * **Emitted ASS Blocks in `List`:**
    The node interpolates RGB colour channels and decomposes the `\fscxy` Dark Tag, producing deterministic sequences such as:
    ```ass
    \t(83,85,\fscx133\fscy133\1c&H00D7FF&)\t(93,173,\fscx105\fscy105\1c&HFFFFFF&)\t(208,211,\fscx133\fscy133\1c&H00D7FF&)...
    ```
  * Each glyph receives micro-sparkles offset in time according to its unique index, preventing unnatural uniform flashing.

---

## 4. Node `Functions/Conditioner` (Logical Data Branching)

* **Canonical Category:** `Functions` (UI: *Functions / Conditioner*)
* **Purpose:** Inline reactive conditional evaluator ($A \text{ if } \text{Cond} \text{ else } B$). Branches dataflow to switch between two text values, ASS tag blocks, numeric values, or lists based on logical expressions evaluated against subtitle context.

![Functions/Conditioner](img/conditioner.png)

---

### 4.1. Input Ports and Body Properties (*Inputs & Properties*)
1. **`Condition` (`condition`):** Boolean conditional expression. Accepts boolean constants (`True`, `False`, `1`, `0`), numeric comparisons (`syl.i % 2 == 0`, `char.i > 3`), membership checks (`line.style == "Romaji"`, `'kanji' in line.tags_str`), or incoming boolean cables. (Default: `"True"`).
2. **`If True` (`if_true`):** Data emitted when the condition evaluates to true ($C = \text{True}$). Can be an ASS tag string, number, list, or connected cable. (Default: `""`).
3. **`If False` (`if_false`):** Data emitted when the condition evaluates to false ($C = \text{False}$). (Default: `""`).

---

### 4.2. Output Ports (*Outputs*)
1. **`[1.1] Out`:** The resulting value selected by the conditional evaluation. If the selected data is a list or tuple, the node automatically joins elements with commas `, `.

---

### 4.3. Algorithmic Detail and Context Evaluation

The evaluator executes expressions securely within an isolated environment injected with all ASS context metrics:

| Injected Variable | Type | Description |
| :--- | :---: | :--- |
| `syl.i`, `char.i`, `word.i`, `fx.i`, `j`, `i` | `int` | Sequential index of the active element ($0$-based or $1$-based). |
| `syl.n`, `char.n`, `word.n`, `line.n` | `int` | Total unit count in the iteration group. |
| `line.style`, `line.actor`, `line.effect` | `str` | Original dialogue line metadata. |
| `line.duration`, `syl.duration`, `fx.dur` | `float` | Duration in milliseconds. |
| `syl.text`, `char.text` | `str` | Text content or phoneme of the active glyph. |

#### Evaluation Rule:
$$\text{Out} = \begin{cases} \text{If True} & \text{if } \text{eval}(\text{Condition}, \text{Context}) = \text{True} \\ \text{If False} & \text{otherwise} \end{cases}$$

---

### 4.4. Synergies and Practical Workflow Examples
* **Checkerboard Alternating Colours:** In `Condition`, write `syl.i % 2 == 0`; in `If True`, set `\1c&H00FFFF&` (Cyan); in `If False`, set `\1c&HFF00FF&` (Magenta) to alternate syllable colours.
* **Punctuation and Space Filtering:** Use `Condition: char.text.strip() == ""` to bypass heavy kinematic transformations on whitespace characters.

### 4.5. Practical Production Example
* **Bicolour Alternation by Character Parity (*Even/Odd Bicolour Stagger*):**
  Routing distinct colour and scale styles for each character within the master character loop:

  ```
  [Loops/Main Loop: char] ──► char.i ───────────────────────────────┐
                                                                    ▼
  [Functions/Conditioner: condition="char.i % 2 == 0"] ──► Out ──► Tags ──► [System/Output]
     If True:  "\1c&H00FFFF&\fscxy110"
     If False: "\1c&HFF0088&\fscxy90"
  ```

  * **Rendered ASS Subtitle Output:**
    * **Even characters ($i \in \{2, 4, 6\}$):** Emit `{\an5\pos(char.center, char.middle)\1c&H00FFFF&\fscx110\fscy110}`.
    * **Odd characters ($i \in \{1, 3, 5\}$):** Emit `{\an5\pos(char.center, char.middle)\1c&HFF0088&\fscx90\fscy90}`.
  * Branches render data cleanly in a single node without duplicate layers or empty events.

---

## 5. Node `Functions/Color Gradient` (Multi-Stop Colour Gradient)

* **Canonical Category:** `Functions` (UI: *Functions / Color Gradient*)
* **Purpose:** Generates and interpolates smooth transitions across multiple colour stops (*multi-stop colour gradient*), applying non-linear acceleration curves (*easing*). Evaluates discrete colours at position $t \in [0.0, 1.0]$ or outputs full batch colour lists and ASS tags for characters, syllables, or particles.

![Functions/Color Gradient](img/color_gradient.png)

---

### 5.1. Input Ports and Body Properties (*Inputs & Properties*)
1. **`Progress (0-1)` (`prog`):** Interpolation progress factor $t \in [0.0, 1.0]$. Accepts numeric constants, cables, or dynamic context expressions (e.g. `char.i / char.n`, `syl.i / syl.n`, `j / maxloop`). (Default: `"char.i / char.n"`).
2. **`Color List` (`colors_str`):** String of colour stops separated by commas, spaces, or newlines. Accepts web hex codes (`#RRGGBB`), HTML names, or ASS codes (`&HBBGGRR&`). (Default: `"#95E648,#3E750C,#ED38CA"`).
3. **`Total (N)` (`total`):** Total division count when consuming batch outputs (`Color List` or `Tags`). If $N > 1$, generates $N$ evenly distributed samples between $t=0.0$ and $t=1.0$. (Default: `"1"`).
4. **`Accel` (`accel`):** Non-linear acceleration exponent. A value of `1.0` produces uniform linear interpolation; values $> 1.0$ weight transitions towards the end (*ease-in*); values $< 1.0$ weight transitions towards the start (*ease-out*). (Default: `"1.0"`).
5. **`Tag` (`tag_type`):** ASS tag selector prefixed to colour codes on the `Tags` output (`\1c`, `\2c`, `\3c`, `\4c`, or `\c`). (Default: `"\1c"`).

---

### 5.2. Output Ports (*Outputs*)
1. **`[1.1] ASS Color`:** Discrete ASS colour code `&HBBGGRR&` evaluated at the progress $t$ set in `Progress (0-1)`.
2. **`[1.2] Color List`:** Comma-separated list of ASS colour codes for the $N$ steps if $N > 1$, or the single colour if $N = 1$.
3. **`[1.3] Tags`:** String with the ASS tag prefix injected for each colour (e.g. `\1c&H48E695&` for $N=1$, or `\1c&H48E695&, \1c&H0C753E&, \1c&HCADB38&` for $N > 1$).

---

### 5.3. Algorithmic Detail and Mathematical Model

```
Stops:    C1 (#95E648)          C2 (#3E750C)          C3 (#ED38CA)
          ├──────────────────────────┼──────────────────────────┤
Progress: t = 0.0                  t = 0.5                  t = 1.0
Segment:  └────── Segment 0 ───────┘└────── Segment 1 ───────┘
```

#### 5.3.1. Non-Linear Easing Curve (*Accel*)
Prior to colour interpolation, the input progress $t \in [0.0, 1.0]$ is modulated via the exponential acceleration function:

$$t_{\text{eased}} = \begin{cases} t^{\text{accel}} & \text{if } \text{accel} > 1.0 \\ 1.0 - (1.0 - t)^{1.0 / \text{accel}} & \text{if } 0.0 < \text{accel} < 1.0 \\ t & \text{if } \text{accel} = 1.0 \end{cases}$$

#### 5.3.2. Multi-Segment Mapping and RGB Interpolation
Given $K$ colour stops $\{C_0, C_1, \dots, C_{K-1}\}$:
1. Compute $K-1$ continuous sub-segments:
   $$\text{pos} = t_{\text{eased}} \cdot (K - 1), \quad \text{idx} = \min(K - 2, \lfloor \text{pos} \rfloor), \quad t_{\text{local}} = \text{pos} - \text{idx}$$
2. Extract RGB channels from adjacent stops $C_{\text{idx}} = (R_1, G_1, B_1)$ and $C_{\text{idx}+1} = (R_2, G_2, B_2)$.
3. Calculate channel-wise linear interpolation:
   $$R = \text{round}(R_1 + (R_2 - R_1) \cdot t_{\text{local}})$$
   $$G = \text{round}(G_1 + (G_2 - G_1) \cdot t_{\text{local}})$$
   $$B = \text{round}(B_1 + (B_2 - B_1) \cdot t_{\text{local}})$$
4. Format output into the ASS reverse BGR hexadecimal format: `&HBBGGRR&`.

---

### 5.4. Synergies and Practical Workflow Examples
* **Per-Character Typography Gradients:** Keep `Progress: char.i / char.n` and connect `Tags` directly to `System/Output`. Each character in the phrase automatically receives its interpolated gradient colour.
* **Temporal Colour Keyframing with `Concatenate (Zip)`:** Set `Total: 5`, connect `Tags` to Input 1 of `Basics/Concatenate (Zip)` and a time sequence `\t(0,200,), \t(200,400,), ...` to Input 2 to generate keyframed chromatic transitions.

### 5.5. Practical Production Example
* **Glyph-by-Glyph Chromatic Gradient Across the Line:**
  Generating a continuous three-colour progression (`#FF4500` reddish orange, `#FFD700` gold, `#00FFFF` cyan) with ease-in acceleration across each character:

  ```
  [Loops/Main Loop: mode=char] ──► char.i / char.n ─────────────────────┐
                                                                         ▼
  [Functions/Color Gradient: accel=1.0] ──► Tags (\1c) ──────────────► Tags In ──► [System/Output]
     colors: "#FF4500, #FFD700, #00FFFF"
  ```

  * **ASS Output Emitted in the Subtitle:**
    * **Initial character ($t=0.0$):** Emits `{\an5\pos(320, 240)\1c&H0045FF&}` (pure reddish orange).
    * **Midpoint character ($t \approx 0.5$):** Emits `{\an5\pos(420, 240)\1c&H00D7FF&}` (bright gold).
    * **Final character ($t=1.0$):** Emits `{\an5\pos(520, 240)\1c&HFFFF00&}` (pure electric cyan).
    * Linear RGB interpolation maintains luminance consistency and prevents chromatic stepping.

---

## 6. Node `Functions/Clip Gradient` (Clipping Bands and Meshes for Multi-Layer Gradients)

* **Canonical Category:** `Functions` (UI: *Functions / Clip Gradient*)
* **Purpose:** Subdivides the visual glyph ink area (*Glyph Ink Bounding Box*) of the active element into continuous stripes or two-dimensional matrix meshes ($C \times R$) with sub-pixel overlap, tightly framing the real glyph contour without wasting iterations on empty typographical margins, optimised for simulating continuous multi-layer colour gradients, angular wipes, or cellular transitions in libass without visible raster seams.

![Functions/Clip Gradient](img/clip_gradient.png)

---

### 6.1. Header Mode Combos
1. **`Mode` (`out_mode`):** Dropdown selector defining the emitted output syntax:
   * **`\clip` (`clip` - Default):** Emits standard rectangular `\clip(x1,y1,x2,y2)` or vector `\clip(m x1 y1 l x2 y2 ...)` ASS tags.
   * **`\iclip` (`iclip`):** Emits inverse clipping tags `\iclip(...)`.
   * **`Shape` (`shape`):** Emits pure ASSdraw vector path code (`m ... l ...`) centred at local origin `(0, 0)` to feed geometry nodes.

---

### 6.2. Input Ports and Body Properties (*Inputs & Properties*)
1. **`Cols` (`cols` - Slot `0`):** Number of columns or horizontal subdivisions. (Default: `"5"`).
2. **`Rows` (`rows` - Slot `1`):** Number of rows or vertical subdivisions. Setting `Rows: 1` generates vertical stripes; `Cols: 1` produces horizontal stripes; greater values in both produce 2D matrix meshes ($N = \text{Cols} \times \text{Rows}$). (Default: `"1"`).
3. **`Angle` (`angle` - Slot `2`):** Grid or stripe tilt angle in sexagesimal degrees ($0^\circ \dots 360^\circ$). $0^\circ$ produces orthogonal rectangular cells; oblique angles project closed affine rotated quadrilaterals. (Default: `"0"`).
4. **Directional Expansion Cross (No wire socket — 5 inline textboxes):** Expands the clipping area from the glyph ink edges either per-direction or uniformly:
   * **`Pad Top` (`pad_top` - Top):** Extra pixels to expand upwards. (Default: `"0"`).
   * **`Pad Left` (`pad_left` - Left):** Extra pixels to expand to the left. (Default: `"0"`).
   * **`Padding` (`padding` - Centre):** Uniform pixel distance added simultaneously in all 4 directions on top of each directional margin ($\text{eff}_{\text{dir}} = \text{padding} + \text{pad}_{\text{dir}}$). (Default: `"0"`).
   * **`Pad Right` (`pad_right` - Right):** Extra pixels to expand to the right. (Default: `"0"`).
   * **`Pad Bottom` (`pad_bottom` - Bottom):** Extra pixels to expand downwards. (Default: `"0"`).
5. **`Overlap` (`overlap` - Slot `3`):** Sub-pixel border dilation in pixels applied to each cell to eliminate anti-aliasing seams in libass. (Default: `"0.5"`).
6. **`Order` (`order` - Slot `4`):** Canonical 2D spatial ordering selector (Numpad, radial, and random): `"79"`, `"97"`, `"13"`, `"31"`, `"71"`, `"17"`, `"93"`, `"39"`, `"5"`, `"-5"`, `"cw"`, `"ccw"`, `"rand"`. (Default: `"79"`).

---

### 6.3. Output Ports and Context Variables (*Outputs & Badges*)
1. **`[1.1] Output`:** Compiled ASS tag (`\clip(...)` or `\iclip(...)`) or ASSdraw path for the active cell.
2. **`[1.2] Progress (0-1)`:** Normalised progress factor of the current cell:
   $$\text{Progress} = \frac{k}{N - 1} \in [0.0, 1.0]$$
3. **`[1.3] Index`:** Ordinal index of the active cell ($1$-based: $1 \dots N$).
4. **`[1.4] Total`:** Total configured cell count ($N = \text{Cols} \times \text{Rows}$).
5. **`[1.5] Col`:** Ordinal column of the active cell ($1 \dots \text{Cols}$).
6. **`[1.6] Row`:** Ordinal row of the active cell ($1 \dots \text{Rows}$).

#### Injected Context Variables:
* **`c_i` / `clip_i`:** Active cell index in the cycle.
* **`c_n` / `clip_n` / `clip_max`:** Total number of configured cells ($N$).
* **`c_col` / `col`:** Current column of the active cell ($1$-based).
* **`c_row` / `row`:** Current row of the active cell ($1$-based).

---

### 6.4. Stripe and 2D Mesh Geometry

```
1D Stripes (Cols: 4, Rows: 1)      2D Mesh (Cols: 3, Rows: 2)        Rotated Mesh (Angle θ)
┌───┬───┬───┬───┐                 ┌─────┬─────┬─────┐                ┌───────/───────┐
│   │   │   │   │                 │ 0,0 │ 1,0 │ 2,0 │               / 0,0   / 1,0   /
│ 0 │ 1 │ 2 │ 3 │                 ├─────┼─────┼─────┤              /───────/───────/
│   │   │   │   │                 │ 0,1 │ 1,1 │ 2,1 │             / 0,1   / 1,1   /
└───┴───┴───┴───┘                 └─────┴─────┴─────┘            └───────/───────┘
```

#### 6.4.1. Orthogonal Rectangular Case ($0^\circ$)
When the angle is $0^\circ$, the node outputs simple rectangular AABB `\clip(x1, y1, x2, y2)` coordinates for maximum raster performance in libass:
$$W_{\text{cell}} = \frac{B_{\text{width}}}{C}, \quad H_{\text{cell}} = \frac{B_{\text{height}}}{R}$$
$$x_1 = B_{\text{left}} + c \cdot W_{\text{cell}} - \text{ov}, \quad x_2 = B_{\text{left}} + (c + 1) \cdot W_{\text{cell}} + \text{ov}$$
$$y_1 = B_{\text{top}} + r \cdot H_{\text{cell}} - \text{ov}, \quad y_2 = B_{\text{top}} + (r + 1) \cdot H_{\text{cell}} + \text{ov}$$

#### 6.4.2. Arbitrary Tilted Case ($\theta$)
For oblique angles, the cell bounding dimensions are projected onto the rotated axes $u$ and $v$, rotating the 4 projected cell vertices around the centre $(C_x, C_y)$:
$$P_x = C_x + u \cos \theta - v \sin \theta, \quad P_y = C_y + u \sin \theta + v \cos \theta$$
Emitting a closed 4-point vector path: `\clip(m p1_x p1_y l p2_x p2_y l p3_x p3_y l p4_x p4_y)`.

---

### 6.5. Intelligent Ink Measurement and Agnostic Alignment (`\an1` .. `\an9`)
`Clip Gradient` automatically inspects the type of object returned at the graph output (`Return` on the `Output` node) and the active `\an` alignment to project clipping boundaries with sub-pixel precision over genuine visual ink:
* **Object Ink Measurement (Shape vs. Text):**
  * **Shape (ASSdraw vector path, shape library or slicer pieces):** Detects ASSdraw vector commands or shape generator nodes (`Shape/Library`, `Shape/Manipulator`, `Shape/Slicer`, etc.) and directly calculates the visual ink bounding box of the vector contours.
  * **Text:** Measures the genuine visual ink contour (*Glyph Ink Contour*) of the active unit or karaoke line. If alternative custom text is passed to the return port, the node dynamically vectorises it through the font vector engine to retrieve its exact visual ink boundaries.
* **Agnostic Alignment (Default `\an5` or Stipulated `\an1` .. `\an9`):**
  * Assumes `\an5` by default unless another alignment is stipulated via the `Output` node's alignment widget, context tags, or properties.
  * When `\an7` is stipulated (the canonical convention for particle systems and slicer pieces rotated around their own local axes), the clip anchors its top-left corner directly at `\pos(x, y)` (`left = pos_x`, `top = pos_y`), achieving a millimetre-perfect fit without unwanted offsets. With `\an1` it aligns to the bottom-left corner (`top = pos_y - h`), and analogously across all 9 numpad positions.

---

### 6.6. Synergies and Practical Workflow Examples
* **Multi-Layer Gradients in `MaxLoop`:** Connect `Loops/MaxLoop` set to `Total: 10`, `Clip Gradient` with `Rows: 10` (horizontal stripes), and route `Progress (0-1)` into `Functions/Color Gradient (Progress)`. Each iteration layer receives its respective clipping stripe and exact interpolated colour.

### 6.7. Practical Production Example
* **Seamless Vertical Chromatic Gradient Across 5 Stripes:**
  Subdividing the active text into 5 horizontal stripes with sub-pixel overlap (`overlap=0.5`), assigning to each its interpolated colour between magenta (`#FF007F`) and violet (`#7F00FF`):

  ```
  [Loops/MaxLoop: total=5] ──► j ───────────────────────────────┐
                                                                 ▼
  [Functions/Clip Gradient: cols=1, rows=5] ──► Progress (0-1) ─► Prog ──► [Functions/Color Gradient]
     out_mode: "\clip", overlap: 0.5                             colors: "#FF007F, #7F00FF"
                                    │                                           │
                                    ▼ Output (\clip)                            ▼ Tags (\1c)
                                 Tags In ──────────────────────────────────── Tags In ──► [System/Output]
  ```

  * **ASS Output Emitted in the Subtitle:**
    * **Iteration $j=1$ (top stripe):** Emits `{\clip(300, 199.5, 450, 208.5)\1c&H7F00FF&}`.
    * **Iteration $j=3$ (middle stripe):** Emits `{\clip(300, 215.5, 450, 224.5)\1c&HBF00BF&}`.
    * **Iteration $j=5$ (bottom stripe):** Emits `{\clip(300, 231.5, 450, 240.5)\1c&HFF007F&}`.
    * The $0.5\text{ px}$ boundary overlap absorbs libass sub-pixel rasterisation rounding errors, eliminating visible seam artefacts.

---

## 7. Node `Functions/IMG to pixels` (Raster Sampling to Particle Swarms)

* **Canonical Category:** `Functions` (UI: *Functions / IMG to pixels*)
* **Purpose:** Samples image files (PNG, JPG, WEBP, animated GIF), decomposing opaque pixels into individual vector particles with sampled texture colour `\1c`, alpha channel `\alpha`, Cartesian screen coordinates `\pos(x, y)`, and Numpad spatial ordering, supported by GPU acceleration and global caching.

![Functions/IMG to pixels](img/img_to_pixels.png)

---

### 7.1. Input Ports and Body Properties (*Inputs & Properties*)
1. **`Image Path` (`image_path`):** Absolute filesystem path to the raster image or animated GIF.
2. **`Particle` (`particle_shape`):** ASSdraw vector shape representing each pixel. If empty, generates a micro-square scaled to step size: `m 0 0 l s 0 l s s l 0 s`.
3. **`Frame` (`frame_idx` / `frame`):** Frame index to sample in animated GIFs ($1$-based). (Default: `"1"`).
4. **`Step` (`step`):** Pixel sampling stride. A step of `1` samples every pixel; a step of `2` samples 1 in 4 pixels ($2 \times 2$), significantly reducing ASS line count while preserving silhouettes. (Default: `2`).
5. **`Alpha` (`alpha_threshold`):** Alpha cutoff threshold ($0 \dots 255$). Pixels with opacity below this value are discarded as transparent background. (Default: `128`).
6. **`Scale` (`scale`):** Multiplier applied to coordinates and image dimensions. (Default: `1.0`).
7. **`Anchor` (`anchor`):** Relative anchor point selector (`center`, `topleft`, `topright`, `bottomleft`, `bottomright`). (Default: `"center"`).
8. **`Order` (`order`):** 2D spatial ordering code selector (`79`, `97`, `13`, `31`, `71`, `17`, `93`, `39`, `5`, `-5`, `cw`, `ccw`, `rand`). (Default: `"79"`).

### 7.2. UI Shortcuts and Interaction
> [!TIP]
> * **Double-Click on the Preview Card:** Double-clicking the centre thumbnail area opens the native OS file dialogue to pick image files (`.png`, `.jpg`, `.jpeg`, `.webp`, `.gif`), updating `image_path` and rendering the texture instantly.

---

### 7.3. Output Ports and Context Variables (*Outputs & Badges*)
1. **`[1.1] Shp Out`:** ASSdraw vector code of the active particle for the current iteration.
2. **`[1.2] Color Arr`:** ASS colour code `&HBBGGRR&` sampled from the image texture.
3. **`[1.3] \pos Tag`:** Complete ASS tag `\pos(x, y)` calculated by adding pixel offsets to the element centroid.
4. **`[1.4] X Arr`:** Absolute horizontal screen coordinate $X$ in pixels.
5. **`[1.5] Y Arr`:** Absolute vertical screen coordinate $Y$ in pixels.
6. **`[1.6] Total`:** Total count of active sampled pixels/particles ($N$).
7. **`[1.7] Pixels Array`:** Structured list containing all sampled pixels `[(x, y, r, g, b, alpha), ...]`.

#### Injected Context Variables:
* **`ip_i` / `img_p_i`:** Active particle index in the loop ($1 \dots N$).
* **`ip_n` / `img_p_n` / `total_pixels` / `maxloop`:** Total active particle count.
* **`fx_pos_x`, `fx_pos_y`, `x`, `y`:** Absolute particle coordinates.

---

### 7.4. Algorithmic Detail, Caching and GPU Acceleration

```
Raster Image (Pillow / NumPy)           ASS Vector Swarm
┌────────────────────────┐              ┌────────────────────────┐
│  Pixels with α ≥ 128   │  Sampling    │  ASSdraw Particles     │
│  (x % step == 0)       │ ───────────► │  \pos(x, y)            │
│  (y % step == 0)       │   Step = 2   │  \1c&HBBGGRR&          │
└────────────────────────┘              └────────────────────────┘
```

1. **Boolean Mask Filtering:**
   The image is loaded into a NumPy RGBA matrix of shape $(H, W, 4)$ and filtered via vectorised indexing:
   $$\text{Mask} = (\text{Alpha} \ge \text{Threshold}) \land (X \pmod{\text{Step}} = 0) \land (Y \pmod{\text{Step}} = 0)$$
2. **Global Sampling Cache:**
   Parsed matrices are cached in memory keyed by `(path, frame, step, threshold, scale, anchor, order)`, preventing redundant disk reads during rendering loops.
3. **GPU Acceleration (OpenCL/CUDA):**
   When the GPU backend is active, coordinate translation, affine scaling, and Numpad sorting are dispatched to OpenCL parallel kernels.

---

### 7.5. Synergies and Practical Workflow Examples
* **Logo Disintegration FX:** Route `IMG to pixels` into `Loops/MaxLoop (total_pixels)`, connect `\pos Tag` to `Functions/Move Tag (Trajectory)` with per-particle offset (`ip_i`), and output to `System/Output`.
* **Performance Optimisation:** For high-resolution source images ($1920 \times 1080$), use `Step: 4` or `Step: 6` to keep particle count between $500 \dots 2000$, ensuring 60 FPS playback in the WebAssembly player.

### 7.6. Practical Production Example
* **Raster Emblem Sampling with 2x2 Vector Particle Swarm:**
  Sampling a local PNG file with a stride of $2\text{ px}$ (`step=2`), alpha threshold $128$, and centered anchoring over the active element:

  ```
  [Functions/IMG to pixels: step=2, anchor=center] ──► Total (N) ──► Total ──► [Loops/MaxLoop]
     image_path: "C:/assets/logo_spark.png"                                         │
        │                                                                           │ j (ip_i)
        ├─► Shp Out (m 0 0 l 2 0...) ───────────────► Shape / Text ◄────────────────┘
        ├─► Color Arr (&HBBGGRR&) ──────────────────► Tags In
        └─► \pos Tag (\pos(x, y)) ──────────────────► Tags In ──► [System/Output]
  ```

  * **ASS Output Emitted in the Subtitle:**
    * **Particle 1 ($x=620, y=340$):** Emits `{\an5\pos(620, 340)\1c&H22AAFF&\1a&H00&\p1}m 0 0 l 2 0 l 2 2 l 0 2`.
    * **Particle 250 ($x=640, y=360$):** Emits `{\an5\pos(640, 360)\1c&HFFFFFF&\1a&H00&\p1}m 0 0 l 2 0 l 2 2 l 0 2`.
    * Each micro-square vector particle reproduces its original texture colour sampled via GPU/NumPy, generating exactly $N$ subtitle events corresponding to opaque pixels without evaluating background transparent regions.

---

## 8. Node `Functions/Animation` (FBF Frame Switcher and Alpha Modulator)

* **Canonical Category:** `Functions` (UI: *Functions / Animation*)
* **Purpose:** Generates cyclical animation sequences from a list of ASSdraw shapes, glyphs, or text strings. Operates in two fundamental modes: discrete Frame-by-Frame (*FBF*) switching with synchronised frame indices, or continuous visibility modulation via coordinated alpha channel `\t` blocks (`\alpha` or `\1a..\4a`) compiled into a single subtitle line.

![Functions/Animation](img/animation.png)

---

### 8.1. Header Mode Combos
1. **`FBF` (*Frame-by-Frame*):** Each main loop iteration (`an_i` or `j`) selects the active shape in the sequence. Output `Shape` emits the vector path with alignment `{\an7}`.
2. **`Alpha` (*Synchronised Alpha Modulation*):** Compiles continuous `\t` visibility cycles that switch opacity between visible (`&H00&`) and transparent (`&HFF&`) at calculated time milestones.

---

### 8.2. Input Ports and Body Properties (*Inputs & Properties*)
1. **`Frames / Text` (`frames`):** Sequence of vector shapes or text. Accepts:
   * Library primitive names (e.g. `"Circle, Star, Heart"`).
   * JSON arrays (e.g. `["m 0 0 l 10 10", "m 0 0 l 20 20"]`).
   * Delimited lists (commas, semicolons `;`, or newlines `\n`).
   * Plain text strings (converted to vector glyphs).
   * Context variable references (e.g. `Shapes1`, `my_frames`).
2. **`Step ms` (`step_ms`):** Temporal duration in milliseconds per animation frame. ($41.7\text{ ms} \approx 24\text{ FPS}$; $33.3\text{ ms} \approx 30\text{ FPS}$; $16.6\text{ ms} \approx 60\text{ FPS}$). (Default: `41.7`).
3. **`Start Time` (`start_time`):** Animation start timestamp in milliseconds (`0` or blank adopts effect start `fx.st` / `syl.start_time`).
4. **`End Time` (`end_time`):** Animation end timestamp in milliseconds (`fx.dur` or blank adopts total duration).
5. **`Alpha Tag` (`alpha_tag`):** [Alpha Mode] Modulated ASS transparency tag or composite Dark Tag (`\alpha`, single channels `\1a`, `\2a`, `\3a`, `\4a`, dual channels `\12a`, `\13a`, `\14a`, `\23a`, `\24a`, `\34a`, triple channels `\123a`, `\124a`, `\134a`, `\234a`, or quadruple channel `\1234a`). Allows selective channel switching (e.g. `\13a` modulates primary fill and border simultaneously without affecting the `\4a` shadow). (Default: `"\alpha"`).
6. **`Variable Prefix` (`var_name`):** Identifier prefix for loop context variables. (Default: `"an"`).

---

### 8.3. Output Ports (*Outputs*)

#### In FBF Mode:
1. **`[1.1] Shape`:** ASSdraw vector code of the active frame prefixed with `{\an7}`.
2. **`[1.2] Frame`:** Active frame index (1-based integer: $1, 2, \dots, N$).
3. **`[1.3] Frames List`:** Complete array of all processed vector paths.

#### In Alpha Mode:
1. **`[1.1] Shape`:** Active vector shape wrapped with its temporal visibility tags `{\an7\alpha&HFF&\t(...)\p1}...`.
2. **`[1.2] Tags`:** Isolated ASS tags string (`\an7\alpha&HFF&\t(...)`) without drawing commands.
3. **`[1.3] Frame`:** Active frame index (1-based).
4. **`[1.4] Frames List`:** Full vector paths array.

#### Exposed Context Variables:
* `{var_name}_i` / `an_i`: Active frame index ($1 \dots K$).
* `{var_name}_n` / `an_n`: Total unique frame count ($K$).
* `an_total_cycles`: Full animation loop cycles completed within total duration.

---

### 8.4. Algorithmic Detail and Temporal Synchronisation

Given $K$ frames $\{F_0, F_1, \dots, F_{K-1}\}$, frame interval $\Delta t_{\text{frame}} = \text{step\_ms}$, and interval $[t_{\text{start}}, t_{\text{end}}]$ with duration $D = t_{\text{end}} - t_{\text{start}}$:

```
Frame Index:     F0       F1       F2       F0       F1       F2
Time (ms):    ├───Δt───┼───Δt───┼───Δt───┼───Δt───┼───Δt───┼───Δt───┤
Cycle:        └─────── Cycle 1 ──────────┘└─────── Cycle 2 ──────────┘
```

#### 8.4.1. Cyclic Mapping in FBF Mode
For active iteration $j \ge 1$:
$$\text{active\_idx} = (j - 1) \pmod K$$
$$\text{Frame} = \text{active\_idx} + 1$$
Total frames required to span duration:
$$N_{\text{total}} = \left\lceil \frac{D}{\Delta t_{\text{frame}}} \right\rceil$$

#### 8.4.2. Alpha Transition Generation
For each cycle $k \in [0, N_{\text{cycles}}]$ and local frame $i$:
$$t_1 = \Delta t_{\text{frame}} \cdot (K \cdot k + i)$$
$$t_2 = t_1 + 1.0$$
$$t_3 = \Delta t_{\text{frame}} \cdot (K \cdot k + i + 1)$$
$$t_4 = \min(D, t_3 + 1.0)$$
Injects visibility pair:
$$\backslash\text{t}(t_1, t_2, \text{tag}\&H00\&)\backslash\text{t}(t_3, t_4, \text{tag}\&HFF\&)$$

---

### 8.5. Synergies and Practical Workflow Examples
* **GIFs and Spritesheets:** Route `Shapes Array` from `Shape/IMG to Shape` into `Frames / Text` of `Animation` to playback extracted GIF frame sequences.
* **Integration with `Loops/MaxLoop (fbf)`:** Configure `MaxLoop` in `fbf` mode to automatically iterate the exact frame count required by karaoke line duration.

### 8.6. Practical Production Example
* **Frame-by-Frame Vector Cycle with MaxLoop FBF:**
  Playing back a cyclic sequence of vector shapes (`circle`, `star`, `heart`) at 24 FPS ($41.7\text{ ms}$ per frame):

  ```
  [Loops/MaxLoop: mode=fbf, step_ms=41.7] ──► j ────────────────────────┐
                                                                         ▼
  [Functions/Animation: mode=FBF, step_ms=41.7] ──► Shape ──► Shape / Text ──► [System/Output]
     frames: "circle, star, heart"
  ```

  * **Vector Output Emitted on `Shape`:**
    * **Iteration $j=1$:** Emits `{\an7}m 50 0 b 22 0 0 22 0 50 ...` (library circle primitive).
    * **Iteration $j=2$:** Emits `{\an7}m 38 36 l 0 36 l 31 59 ...` (vector star).
    * **Iteration $j=3$:** Emits `{\an7}m 50 25 b 50 10 35 0 20 0 ...` (vector heart).
    * **Iteration $j=4$:** Automatically wraps around to the initial frame ($1$), cycling seamlessly for the entire subtitle lifetime.

---

## 9. Node `Functions/Bezier Curve` (2D Bézier Splines and Trajectories)

* **Canonical Category:** `Functions` (UI: *Functions / Bezier Curve*)
* **Purpose:** Universal generator, evaluator, and interpolator for 2D parametric Bézier curves. Implements De Casteljau's algorithm for quadratic, cubic, and arbitrary $N$-degree curves, arc-length numerical integration for constant speed, tangent/normal vector derivative extraction, topological curve subdivision, and procedural smooth random wandering trajectories.

![Functions/Bezier Curve](img/bezier_curve.png)

---

### 9.1. Header Mode Combos
1. **`Cubic 2D`:** Classical cubic Bézier curve defined by 4 control points ($P_0, P_1, P_2, P_3$).
2. **`Quadratic 2D`:** Quadratic Bézier curve defined by 3 control points ($P_0, P_1, P_2$).
3. **`N-Degree`:** Arbitrary polynomial curve of degree $N$ defined by a list of points in `Points` ($P_0, P_1, \dots, P_N$).
4. **`Constant Speed`:** Arc-length corrected $t \in [0.0, 1.0]$ mapping via Simpson's rule ensuring uniform speed in pixels/second.
5. **`Shape Contour`:** Parametrically samples an arbitrary ASSdraw vector path connected to `Shape`.
6. **`Subdivide`:** Splits the curve at parameter $t$, generating two independent sub-splines (`Spline L` and `Spline R`).
7. **`Trajectory`:** Procedural generator of smooth random paths using linked cubic splines (`Free Wander`, `Bounded`, `Closed Loop`).

---

### 9.2. Input Ports and Body Properties (*Inputs & Properties*)
1. **`Origin` (`origin`):** Cartesian coordinate $(X_0, Y_0)$ added as an offset to all control points. (Default: `"0,0"`).
2. **`P0, P1, P2, P3` (`p0`, `p1`, `p2`, `p3`):** Control point $(X, Y)$ coordinates. Accepts tuples separated by commas, spaces, or cables.
3. **`t` (`t`):** Parametric evaluation parameter $t \in [0.0, 1.0]$. Accepts context variables like `j / maxloop` or `char.i / char.n`. (Default: `"0.5"`).
4. **`Subdivs` (`subdivs`):** Discrete step count for contour sampling and arc-length integration. (Default: `"100"`).
5. **`Shape` (`shape`):** Input ASSdraw path for `Shape Contour` and `Trajectory` modes.
6. **`Points` (`points`):** Control point list for `N-Degree` mode (e.g. `"0,0; 50,100; 150,100; 200,0"`).
7. **`Trajectory Mode` (`traj_mode`):** Procedural trajectory mode (`"Free Wander"`, `"Bounded"`, `"Closed Loop"`).
8. **`Dist Range` (`dist_range`):** Min/max distance range between random spline nodes (e.g. `"50,120"`).
9. **`Seed` (`seed`):** Deterministic pseudo-random seed for trajectory generation. (Default: `"1"`).
10. **`Loops` (`loops`):** Number of chained cubic segments in the trajectory. (Default: `"8"`).

---

### 9.3. Output Ports (*Outputs*)
1. **`[1.1] \pos`:** Formatted ASS tag `\pos(X, Y)` evaluated at parameter $t$.
2. **`[1.2] X`:** Discrete horizontal coordinate $X(t)$ (integer or 2-decimal float).
3. **`[1.3] Y`:** Discrete vertical coordinate $Y(t)$.
4. **`[1.4] Tan`:** Tangent angle $\theta \in [0^\circ, 360^\circ)$ in degrees, ideal for routing to rotation `\frz`.
5. **`[1.5] Norm`:** Perpendicular normal angle $(\theta + 90^\circ) \pmod{360^\circ}$.
6. **`[1.6] Spline`:** Complete ASSdraw vector path of the curve (e.g. `m X0 Y0 b X1 Y1 X2 Y2 X3 Y3`).
7. **`[1.7] Spline L`:** [Subdivide Mode] ASSdraw path of left segment $[0.0, t]$.
8. **`[1.8] Spline R`:** [Subdivide Mode] ASSdraw path of right segment $[t, 1.0]$.

---

### 9.4. Algorithmic Detail and Mathematical Formulation

```
P1 (50, 100)                     P2 (150, 100)
    ●───────────────────────────────●
   /                                 \
  /           B(t) (X, Y)             \
 /                 ● ───> Tangent      \
●                  │                    ●
P0 (0, 0)          ▼ Normal             P3 (200, 0)
```

#### 9.4.1. De Casteljau's Algorithm (Degree $N$)
Given $n+1$ control points $\{P_0, P_1, \dots, P_n\}$ with $P_i \in \mathbb{R}^2$:
$$P_i^{(0)} = P_i \quad \forall i \in \{0, \dots, n\}$$
$$P_i^{(r)} = (1 - t) P_i^{(r-1)} + t P_{i+1}^{(r-1)} \quad \forall r \in \{1, \dots, n\}, \, i \in \{0, \dots, n-r\}$$
The evaluated point on the curve is $B(t) = P_0^{(n)}$.

For a cubic curve ($n=3$):
$$B(t) = (1-t)^3 P_0 + 3(1-t)^2 t P_1 + 3(1-t) t^2 P_2 + t^3 P_3$$

#### 9.4.2. Derivative, Tangent and Normal
The first derivative $B'(t) = (dx/dt, dy/dt)$ of a degree-$n$ curve is a degree-$(n-1)$ Bézier curve:
$$B'(t) = n \sum_{i=0}^{n-1} (P_{i+1} - P_i) \cdot b_{i, n-1}(t)$$
From velocity vector $(dx, dy)$:
$$\theta_{\text{tan}} = \left( \operatorname{atan2}(dy, dx) \cdot \frac{180}{\pi} + 360^\circ \right) \pmod{360^\circ}$$
$$\theta_{\text{norm}} = (\theta_{\text{tan}} + 90^\circ) \pmod{360^\circ}$$

#### 9.4.3. Arc-Length Correction (Constant Speed)
Cumulative arc-length $s(t)$ is integrated via Simpson's composite rule:
$$s(t) = \int_0^t \sqrt{\left(\frac{dx}{du}\right)^2 + \left(\frac{dy}{du}\right)^2} \, du$$
To evaluate at target distance $s_{\text{target}} = t \cdot s(1.0)$, $s(t^*) = s_{\text{target}}$ is solved using numerical bisection search until convergence ($\epsilon < 10^{-5}$).

#### 9.4.4. De Casteljau Topological Subdivision
At parameter $t$, intermediate points in the De Casteljau pyramid define the new control polygons:
* **Left Segment ($[0, t]$):** $\{P_0^{(0)}, P_0^{(1)}, P_0^{(2)}, \dots, P_0^{(n)}\}$.
* **Right Segment ($[t, 1]$):** $\{P_0^{(n)}, P_1^{(n-1)}, P_2^{(n-2)}, \dots, P_n^{(0)}\}$.

---

### 9.5. Synergies and Practical Workflow Examples
* **Auto-Orienting Missiles and Particles:** Route output `\pos` to position and output `Tan` into `\frz` so moving elements naturally rotate to match path heading.
* **Animated Stroke Drawing with `Shape/Walker`:** Connect output `Spline` to `Path` on `Shape/Walker` to progressively draw curves on screen.

### 9.6. Practical Production Example
* **Kinematic Interpolation Along a Cubic Spline with Tangential Heading:**
  Evaluating a parabolic trajectory defined by 4 control points $P_0(100, 300), P_1(200, 100), P_2(400, 100), P_3(500, 300)$ at parametric midpoint $t=0.5$:

  ```
  [Functions/Bezier Curve: mode=cubic_2d, t=0.5] ──► \pos ──────┐
     p0: "100,300", p1: "200,100", p2: "400,100", p3: "500,300" │
                                           └──► Tan ───┐        ▼
                                                       └──► Tags In ──► [System/Output]
                                                                        Return: "m 0 0 l 20 0 l 20 20 l 0 20"
  ```

  * **De Casteljau Calculation at $t=0.5$:**
    $$B(0.5) = (1-0.5)^3 P_0 + 3(1-0.5)^2(0.5) P_1 + 3(1-0.5)(0.5)^2 P_2 + 0.5^3 P_3$$
    $$B(0.5) = 0.125(100, 300) + 0.375(200, 100) + 0.375(400, 100) + 0.125(500, 300) = (300.0, 150.0)$$
  * **Tangent Evaluation at the Apex:**
    $$B'(0.5) = 3(0.25)(P_1 - P_0) + 6(0.25)(P_2 - P_1) + 3(0.25)(P_3 - P_2) = (450.0, 0.0) \implies \theta = 0^\circ$$
  * **Resulting Generated ASS Line:**
    `Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\an5\pos(300,150)\frz0\p1}m 0 0 l 20 0 l 20 20 l 0 20{\p0}`

---

## 10. Node `Functions/Move Tag` (Kinematic ASS Motion Sequences)

* **Canonical Category:** `Functions` (UI: *Functions / Move Tag*)
* **Purpose:** Generates comprehensive ASS kinematic override blocks (`\pos`, `\fscx`, `\fscy`, `\t`) from vector path geometries, Cartesian waypoints, or stochastic fluctuations (*jitter*). Resamples trajectories at a uniform spatial step (`step_px`), applies non-linear acceleration curves, and recentres coordinate frames.

![Functions/Move Tag](img/move_tag.png)

---

### 10.1. Header Mode Combos
1. **`Trajectory` (`SMOVE`):** Takes an ASSdraw vector shape (`Shape`), computes total arc-length, and divides it into regular segments of max length `step_px` to generate smooth continuous motion.
2. **`Waypoints` (`PMOVE`):** Takes a list of discrete Cartesian points (`Points` or `Shape`) and generates linear or interpolated transitions between waypoints.
3. **`Jitter` (`RMOVE`):** Generates continuous pseudo-random jitter oscillating within range $(\pm \Delta X, \pm \Delta Y)$ at regular time intervals (`dur` ms) with seed reproducibility.

---

### 10.2. Input Ports and Body Properties (*Inputs & Properties*)
1. **`Tags` (`tags`):** Additional ASS tags injected into the final block (e.g. `\1c&HFFFFFF&\blur2`).
2. **`Shape (d)` (`shape`):** ASSdraw path string defining the motion route (e.g. `"m 0 0 b 50 100 150 100 200 0"`).
3. **`Step (px)` (`step_px`):** Max distance in pixels between consecutive trajectory samples. Smaller values increase smoothness at the cost of generating more `\t` tags. (Default: `7.5`).
4. **`Anchor` (`anchor`):** Spatial centring and anchoring mode:
   * `"center"`: Centres trajectory on its bounding box midpoint $(B_{\text{centre}} = (0, 0))$.
   * `"origin"` / `"first_point"`: Locks path start point at $(0, 0)$.
5. **`Start Time (t1)` (`t1`):** Motion start timestamp in milliseconds. (Default: `0`).
6. **`End Time (t2)` (`t2`):** Motion arrival timestamp in milliseconds. (Default: `"fx.dur"`).
7. **`Acceleration` (`accel`):** Kinematic acceleration exponent ($1.0 = \text{linear}$; $> 1.0 = \text{ease-in}$; $< 1.0 = \text{ease-out}$). (Default: `1.0`).

---

### 10.3. Output Ports (*Outputs*)
1. **`[1.1] Data`:** Fully formatted ASS tag string ready for injection:
   $$\backslash\text{an7}\backslash\text{q2}\backslash\text{pos}(X_0, Y_0)\backslash\text{fscx}P_{x0}\backslash\text{fscy}P_{y0}\backslash\text{t}(t_{s1}, t_{e1}, \backslash\text{fscx}P_{x1}\backslash\text{fscy}P_{y1})\dots\backslash\text{p1}\}m\dots\{\backslash\text{p0}$$

---

### 10.4. Algorithmic Detail and Displacement Kinematics

```
Vector Route:     P0 (0,0) ─────── P1 (7.5px) ─────── P2 (15px) ─────── P3 (22.5px)
Mapped Time:      t1               st1 ─── et1        st2 ─── et2       t2
Normal Progress:  0.0              (d1/D)^accel       (d2/D)^accel      1.0
```

Given $M$ sampled points $\{P_0, P_1, \dots, P_{M-1}\}$ with cumulative distances $d_k$ and total distance $D = d_{M-1}$:
1. For each segment $k \in [1, M-1]$:
   $$\tau_1 = \left(\frac{d_{k-1}}{D}\right)^{\text{accel}}, \quad \tau_2 = \left(\frac{d_k}{D}\right)^{\text{accel}}$$
   $$s_t = \text{round}(t_1 + (t_2 - t_1) \cdot \tau_1)$$
   $$e_t = \text{round}(t_1 + (t_2 - t_1) \cdot \tau_2)$$
2. Inject transition:
   $$\backslash\text{t}(s_t, e_t, \backslash\text{fscx}P_{x,k}\backslash\text{fscy}P_{y,k})$$

---

### 10.5. Synergies and Practical Workflow Examples
* **Path-Following Animations:** Route output `Spline` from `Bezier Curve` into `Shape (d)` of `Move Tag` to transport glyphs along Bézier splines with acceleration control.

### 10.6. Practical Production Example
* **Non-Linear Kinematic Displacement with Exponential Acceleration:**
  Generating a 3-segment spatial route over $300\text{ ms}$ with quadratic easing ($\text{accel}=2.0$) from $(100, 200)$ to $(250, 250)$ at a sampling step of $50\text{ px}$:

  ```
  [Functions/Move Tag: mode=trajectory, step_px=50, accel=2.0, t1=0, t2=300]
     shape: "m 100 200 l 170 200 l 250 250" ──► Data ──► Tags In ──► [System/Output]
                                                                     Return: "Text"
  ```

  * **Metric Sampling and Acceleration ($\Delta t = 300\text{ ms}$, $D = 164.34\text{ px}$):**
    * Segment 0 ($d_0 = 0.0$): $\tau_0 = 0.0 \to t = 0\text{ ms}$, coordinates $(100.0, 200.0)$.
    * Segment 1 ($d_1 = 70.0$): $\tau_1 = (70.0 / 164.34)^2 \approx 0.181 \to s_{t1} = 54\text{ ms}$, coordinates $(170.0, 200.0)$.
    * Segment 2 ($d_2 = 164.34$): $\tau_2 = 1.0 \to s_{t2} = 300\text{ ms}$, coordinates $(250.0, 250.0)$.
  * **Emitted ASS Tag Block:**
    `{\an7\q2\pos(100.00,200.00)\fscx100.00\fscy100.00\t(0,54,2.00,\fscx170.00\fscy200.00)\t(54,300,2.00,\fscx250.00\fscy250.00)\p1}m 0 0 m 100 100 {\p0}Text`

---

## 11. Node `Functions/Move Text` (Coordinated Inline Typographic Motion)

* **Canonical Category:** `Functions` (UI: *Functions / Move Text*)
* **Purpose:** Produces complex kinematic animations on text strings without breaking paragraph layout or altering natural font metrics. Employs a dual-axis differential compensation architecture using font spacing (`\fsp`) for the X axis and vertical scaling (`\fscy`) for the Y axis, enclosing text between invisible anchors.

![Functions/Move Text](img/move_text.png)

---

### 11.1. Input Ports and Body Properties (*Inputs & Properties*)
1. **`Text` (`text`):** Text string or ASSdraw shape. If empty, automatically extracts the text of the active syllable or character in context.
2. **`Delta X` (`dx`):** Total Cartesian displacement along the X axis (px).
3. **`Delta Y` (`dy`):** Total Cartesian displacement along the Y axis (px).
4. **`Offset X` (`ox`):** Fixed initial offset along the X axis (px).
5. **`Offset Y` (`oy`):** Fixed initial offset along the Y axis (px).
6. **`Shape (d)` (`shape` / `trajectory`):** Optional ASSdraw path replacing $\Delta X, \Delta Y$ for curved trajectories.
7. **`Points` (`points`):** Discrete control points list for waypoint routing.
8. **`Step (px)` (`step_px`):** Resampling step for vector paths. (Default: `7.5`).
9. **`Start Time (t1)` (`t1`):** Motion start timestamp (ms). (Default: `0`).
10. **`End Time (t2)` (`t2`):** Motion end timestamp (ms). (Default: `"fx.dur"`).
11. **`Acceleration` (`accel`):** Kinematic acceleration exponent. (Default: `1.0`).

---

### 11.2. Output Ports (*Outputs*)
1. **`[1.1] Text`:** Modularized ASS typographic structure containing dual horizontal and vertical compensation blocks:
   $$\text{Block}_{V1} \cdot \text{Block}_{H1} \cdot \{\backslash\text{r}\text{tags}\backslash\text{q2}\}\text{Text} \cdot \text{Block}_{H2} \cdot \text{Block}_{V2}$$

---

### 11.3. Algorithmic Detail and Inline Compensation Architecture

```
Generated Structure:
[ Compensating Linebreak \N Y1 ]
[ Hidden Dot '.' with \fspX1 ] ─── [ PRIMARY TEXT ] ─── [ Hidden Dot '.' with \fspX2 ]
[ Compensating Linebreak \N Y2 ]
```

To move text without modifying neighbouring character flow or relying on screen-space `\pos` coordinates:
1. **Horizontal Axis ($X$):** Injects two transparent dot characters `.` (`\alpha&HFF&`) flanking the text. Modulating spacing `\fsp` with doubled offsets $2 \cdot \Delta X$ shifts text smoothly left/right while maintaining line width.
2. **Vertical Axis ($Y$):** Injects forced line breaks `\N` with micro-drawings scaled via `\fscy` to shift the active line up/down without breaking the global baseline.

---

### 11.4. Synergies and Practical Workflow Examples
* **Smooth Drop-In Entrances:** Use `Move Text` with `Delta Y = -30` and `Accel = 2.0` during phase `presyl` to create an entrance where each syllable smoothly floats down onto the baseline when sung.

### 11.5. Practical Production Example
* **Vertical Drop-In Syllable Entrance Without Breaking Line Layout:**
  Animating a $25\text{ px}$ vertical entrance drop across the first $250\text{ ms}$ of the syllable using typographic spacing and forced break compensation:

  ```
  [Variables/Sys Var: var_name=syl.text] ──► Text ─────────────────┐
                                                                   ▼
  [Functions/Move Text: dy=-25, t1=0, t2=250, accel=1.5] ──► Text ──► Return ──► [System/Output]
  ```

  * **Transformation Mechanics:**
    The node computes the metric width of anchor glyph `.` ($w_{\text{dot}} = 7.5\text{ px}$), encapsulating syllable text between two invisible characters with `\alpha&HFF&` and compensating the vertical axis via a scaled `\fscy` block following a forced line break `\N`.
  * **Generated ASS Dialogue Line:**
    `Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\p0\alpha&HFF&.}{\fscy100\t(0,250,1.5,\fscy0)\p1}m 0 0 l 1 0 l 1 25 l 0 25{\p0}\N{\r\q2}Ka{\p0\alpha&HFF&.}`

---

## 12. Node `Functions/Polar to Cartesian` (Polar to Cartesian Converter)

* **Canonical Category:** `Functions` (UI: *Functions / Polar to Cartesian*)
* **Purpose:** Converts polar coordinates defined by radius $r$ and angle $\theta$ into Cartesian coordinates $(X, Y)$ relative to an origin $(X_0, Y_0)$. Emits formatted positioning tags `\pos(X, Y)` and numeric components for matrix computations.

![Functions/Polar to Cartesian](img/polar_to_certesian.png)

---

### 12.1. Input Ports and Body Properties (*Inputs & Properties*)
1. **`Origin X` (`x`):** Polar origin coordinate $X_0$. Accepts constants or context expressions like `syl.x`, `line.x`, `char.x`. (Default: `"0"`).
2. **`Origin Y` (`y`):** Polar origin coordinate $Y_0$ (e.g. `syl.y`, `line.y`). (Default: `"0"`).
3. **`Angle (°)` (`angle`):** Polar angle $\theta$ in degrees ($0^\circ \dots 360^\circ$). $0^\circ$ points along $+X$ (right); $90^\circ$ points along $+Y$ (down in the ASS coordinate system). (Default: `"0"`).
4. **`Radius` (`radius`):** Vector radius magnitude $r$ in pixels. (Default: `"100"`).

---

### 12.2. Output Ports (*Outputs*)
1. **`[1.1] \pos Tag`:** Formatted ASS position tag `\pos(X, Y)`.
2. **`[1.2] X`:** Resulting absolute Cartesian coordinate $X = X_0 + \Delta X$.
3. **`[1.3] Y`:** Resulting absolute Cartesian coordinate $Y = Y_0 + \Delta Y$.
4. **`[1.4] dX`:** Relative horizontal differential displacement $\Delta X = r \cos(\theta)$.
5. **`[1.5] dY`:** Relative vertical differential displacement $\Delta Y = r \sin(\theta)$.

---

### 12.3. Algorithmic Detail and Trigonometric Model

```
               (X0, Y0)
                  ● ─────────────> X Axis (θ = 0°)
                  │ \
                  │  \  Radius (r)
                  │   \
                  │ θ  \
                  ▼     ● (X, Y)
                Y Axis
```

Given angle in degrees $\theta$, convert to radians:
$$\theta_{\text{rad}} = \theta \cdot \frac{\pi}{180}$$

Differential components and absolute coordinates:
$$\Delta X = r \cdot \cos(\theta_{\text{rad}})$$
$$\Delta Y = r \cdot \sin(\theta_{\text{rad}})$$
$$X = X_0 + \Delta X$$
$$Y = Y_0 + \Delta Y$$

Numeric values are emitted as clean integers if fractional parts are zero, or rounded to 2 decimal places to conserve ASS file size.

---

### 12.4. Synergies and Practical Workflow Examples
* **Radial Particle Bursts:** Connect an iterator like `Basics/MultiRandom` or expression `j * (360 / maxloop)` to `Angle (°)`, set `Radius: 80`, and route `\pos Tag` to `System/Output` for instant circular particle rings.
* **Spiral Inward Orbits:** Modulate `Angle (°)` with `Time/Ipol` while dynamically decreasing `Radius` over time for convergent spiral trajectories.

### 12.5. Practical Production Example
* **Orbital Ring of 8 Particles Around the Syllable:**
  Generating a circular ring of 8 vector elements spaced at $45^\circ$ angular intervals at a fixed radius of $60\text{ px}$ from the syllable centre:

  ```
  [Loops/MaxLoop: total=8] ──► j ──► Angle: (j - 1) * 45 ────────┐
                                                                 ▼
  [Shape/Library: "Star"] ──► Shape ──► Shape / Text ──► [Functions/Polar to Cartesian: radius=60]
                                                            Origin X: syl.x, Origin Y: syl.y
                                                                 │
                                                                 ▼ \pos Tag (\pos(X, Y))
                                                              Tags In ──► [System/Output]
  ```

  * **ASS Output Emitted in the Subtitle:** (assuming `syl.x = 320, syl.y = 240`):
    * **Iteration $j=1$ ($\theta = 0^\circ$):** $\Delta X = 60, \Delta Y = 0 \to$ Emits `{\an5\pos(380, 240)\p1}m 0 0 ...` (right).
    * **Iteration $j=3$ ($\theta = 90^\circ$):** $\Delta X = 0, \Delta Y = 60 \to$ Emits `{\an5\pos(320, 300)\p1}m 0 0 ...` (bottom).
    * **Iteration $j=5$ ($\theta = 180^\circ$):** $\Delta X = -60, \Delta Y = 0 \to$ Emits `{\an5\pos(260, 240)\p1}m 0 0 ...` (left).
    * **Iteration $j=7$ ($\theta = 270^\circ$):** $\Delta X = 0, \Delta Y = -60 \to$ Emits `{\an5\pos(320, 180)\p1}m 0 0 ...` (top).
    * Trigonometric offsets are calculated in floating point and rounded to clean integers or 2 decimal places to minimise ASS event payload.

---

## 13. Node `Functions/Particles` (Vector Particle Swarms)

* **Canonical Category:** `Functions` (UI: *Functions / Particles*)
* **Purpose:** Samples contours or interior meshes of text glyphs or ASSdraw shapes to generate discrete particle swarms. Allows replacing each sampled node with a custom vector particle, sorting spatial order via Numpad directional notations, and applying random jitter.

![Functions/Particles](img/particles.png)

---

### 13.1. Header Mode Combos
1. **`Outline` (`outline_v2` / `border`):** Samples equidistant points along vector perimeter boundaries.
2. **`Inner Fill` (`inner_fill`):** Generates a regular grid of points inside the shape, verifying geometric inclusion via Ray-Casting parity tests.

---

### 13.2. Input Ports and Body Properties (*Inputs & Properties*)
1. **`Path / Origin` (`shape`):** Base ASSdraw path (`m ...`) or primitive name. If empty or given plain text, automatically extracts glyph outlines from the active context (`syl` or `char`).
2. **`Particle` (`particle_shape`):** Vector shape used as an individual particle (e.g. `"Circle"`, `"Star"`, `"Heart"`, or raw ASSdraw). If empty, defaults to a $2 \times 2\text{ px}$ square (`m 0 0 l 2 0 l 2 2 l 0 2`).
3. **`Density` (`density`):** Sampling stride in pixels. In `Outline` mode, sets spacing along contours; in `Inner Fill`, sets grid cell step. (Default: `5.0`).
4. **`RedrawDist` (`redraw_dist`):** Uniform random jitter range $(\pm \Delta x, \pm \Delta y)$ in pixels applied to each particle. (Default: `0.0`).
5. **`Seed` (`seed`):** Deterministic seed for jitter generation. (Default: `1`).
6. **`Scale` (`scale`):** Multiplier applied to particle swarm coordinates. (Default: `1.0`).
7. **`Anchor` (`anchor`):** Interactive cyclic button matching the standard *Piece Anchor* profile found across tessellation nodes (`Slicer`, `Array`, `Union & Divide`). Governs how local particle coordinates and the rotation origin `\org` are projected onto the subtitle canvas:
   * **`pieces` (Canonical default):** Each micro-particle is positioned at its autonomous screen-space coordinates `\pos(x, y)` relative to its glyph or path centroid, while setting `\org(x, y)` precisely at its own geometric centre. This allows subsequent downstream transformations (such as `\frz` spins, `\fscx/\fscy` scaling, or shearing) to rotate each particle independently around its own pivot.
   * **`relative`:** Preserves coordinates relative to the parent text or shape base centroid without asserting `pos_overridden`.
   * **`parent_org`:** Positions the particle at its absolute screen coordinates `\pos(x, y)`, but pins `\org` to the parent text or line origin (`parent_x, parent_y`), enabling coordinated orbital rotations around the source glyph.
   * **`pos`:** Positions the particle at its absolute screen coordinates `\pos(x, y)` without emitting an explicit `\org` override (`has_org = False`).
   * **`absolute`:** Bakes screen coordinates directly into the vector path vertices (`m x y ...`), pinning `\pos` to parent origin and clearing `pos_overridden`.
8. **`Order` (`order`):** Interactive cyclic button for 2D spatial sorting (*Numpad Order*) governing iteration index assignment (`p_i`):
   * `"79"`: Top-Left to Bottom-Right (*TL $\to$ BR*).
   * `"97"`: Top-Right to Bottom-Left (*TR $\to$ BL*).
   * `"13"`: Bottom-Left to Top-Right (*BL $\to$ TR*).
   * `"31"`: Bottom-Right to Top-Left (*BR $\to$ TL*).
   * `"71"`: Descending vertical column on left (Top-Left to Bottom-Left).
   * `"17"`: Ascending vertical column on left (Bottom-Left to Top-Left).
   * `"93"`: Descending vertical column on right (Top-Right to Bottom-Right).
   * `"39"`: Ascending vertical column on right (Bottom-Right to Top-Right).
   * `"5"`: Centrifugal outward (*Inside-Out*).
   * `"-5"`: Centripetal inward (*Outside-In*).
   * `"cw"`: Circular clockwise.
   * `"ccw"`: Circular counter-clockwise.
   * `"rand"`: Pseudo-random shuffle.
   * `"path"`: **Continuous contour trajectory.** Preserves the monotonic arc-length parametrisation sequence ($s \in [0, L]$) evaluated along piecewise linear and Bézier boundary curves. Operates analogously to an embedded *Walker* engine, ensuring downstream tag cascades, reveals, or transformations trace the authentic calligraphic stroke.
   * `"path_inv"`: **Inverted contour trajectory.** Traverses the perimeter in retrograde order ($s \in [L, 0]$).

---

### 13.3. Output Ports (*Outputs*)
1. **`[1.1] Shp Out`:** Combined block with absolute position tag and particle drawing: `{\pos(X, Y)}particle_shape`.
2. **`[1.2] \pos Tag`:** Cartesian position tag `\pos(X, Y)`.
3. **`[1.3] X Arr`:** Horizontal Cartesian coordinate $X$ of the active particle (px).
4. **`[1.4] Y Arr`:** Vertical Cartesian coordinate $Y$ of the active particle (px).
5. **`[1.5] Total`:** Total particle count $N$.

#### Injected Context Variables:
* `p_i` / `tp_i`: Active particle index ($1 \dots N$).
* `p_n` / `tp_n` / `maxloop`: Total particle count ($N$).
* `x, y` / `fx_pos_x, fx_pos_y`: Absolute Cartesian coordinates of active particle.

---

### 13.4. Algorithmic Detail and Spatial Sampling

```
Outline Mode (Perimeter):             Inner Fill Mode (Ray-Casting):
      ● ─── ● ─── ●                        ●   ●   ●   ●   ● (Outside)
     /             \                     ┌───────────────────┐
    ●               ●                    │   ●   ●   ●   ●   │ (Inside: Crossings = 1)
     \             /                     │   ●   ●   ●   ●   │
      ● ─── ● ─── ●                      └───────────────────┘
```

#### 13.4.1. Perimeter Arc-Length Sampling
For each closed contour $C = \{V_0, V_1, \dots, V_m, V_0\}$:
1. Compute cumulative segment distances:
   $$d_k = \|V_{k+1} - V_k\|, \quad D_{\text{total}} = \sum_{k=0}^m d_k$$
2. Generate equidistant sample targets $s_j = j \cdot \text{density}$ for $j \in \left[0, \lfloor D_{\text{total}} / \text{density} \rfloor \right]$.
3. Linearly interpolate each target point on its segment and apply stochastic jitter if $\text{RedrawDist} > 0$:
   $$P_j = P_{\text{interp}} + \begin{pmatrix} U(-\text{redraw\_dist}, \text{redraw\_dist}) \\ U(-\text{redraw\_dist}, \text{redraw\_dist}) \end{pmatrix} \cdot \text{scale}$$

#### 13.4.2. Ray-Casting Interior Grid Sampling
1. Extract bounding box $(X_{\min}, Y_{\min}) \to (X_{\max}, Y_{\max})$ across all contours.
2. Form a regular grid with cell size $\Delta = \text{density}$.
3. For each grid node $(g_x, g_y)$, cast a horizontal ray towards $+X$ and count polygon edge intersections:
   $$\text{inside} = \left(\sum \text{intersections}(g_x, g_y, \text{Edges})\right) \pmod 2 \equiv 1$$
   Points satisfying odd parity are added to the swarm.

---

### 13.5. Synergies and Practical Workflow Examples
* **Particle Text Dissolve:** Connect `Functions/Particles` to `Loops/MaxLoop` configured to iterate $N$ times (`p_n`), animating dispersal outward using `Time/Ipol` or `Functions/Polar to Cartesian`.

### 13.6. Practical Production Example
* **Radial Perimeter Particle Burst from Glyph Contours:**
  Sampling a typographic glyph contour at a density of $8\text{ px}$, replacing each vertex with a micro-star, and traversing them from centre to edge (order `"5"`):

  ```
  [Shape/Library: "Star"] ──► Particle ────────────────────────────┐
                                                                   ▼
  [Functions/Particles: mode=outline_v2, density=8.0, order="5"] ──► Shp Out ──► Return ──► [System/Output]
     Path / Origin: syl.shape
  ```

  * **DAG Trace Sub-Loop Execution:**
    The engine discovers `Particles` along the `Output.Return` dataflow, extracts $N=24$ perimeter points from the glyph, injects loop variables `p_i` ($1 \dots 24$) and `p_n` ($24$), and sorts coordinates radially according to distance from character centroid.
  * **ASS Line Emitted for First Particle ($p_i=1$, closest to centroid):**
    `Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\an5\pos(320.50,238.20)\p1}m 0 0 l 2 0 l 2 2 l 0 2{\p0}`

* **Calligraphic Particle Write-On Workflow (Embedded Walker):**
  When selecting `order="path"`, particles are not reordered into Cartesian or radial bins; rather, they are indexed progressively along the perimeter contour ($s = 0 \to L$). Modulating opacity or scale via `Tags` (e.g. `\alpha!by.p_i.ipol(0, 255, 0, fx.dur)!` or `\t((p_i/p_n)*syl.dur, ((p_i+1)/p_n)*syl.dur, \alpha&H00&)`), each micro-particle illuminates sequentially tracing the continuous glyph outline without needing a separate `Shape/Walker` node.

---

## 14. Node `Functions/Interpolator` (Polymorphic Parametric Interpolator)

* **Canonical Category:** `Functions` (UI: *Functions / Interpolator*)
* **Purpose:** Multi-domain universal parametric interpolation engine. Produces smooth transitions between two or more values ($V_1 \to V_2$) adapting to underlying data types: scalar numbers, colours (Hex/ASS), alpha channels, ASS tag blocks, or complete vector geometries (*vector morphing* with topological resampling).

![Functions/Interpolator](img/interpolador.png)

---

### 14.1. Input Ports and Body Properties (*Inputs & Properties*)
1. **`Iterator` (`iterator`):** Current iteration index or progress value. Accepts:
   * Context iterator names (e.g. `"i"`, `"j"`, `"char.i"`, `"syl.i"`, `"a_i"`).
   * Direct normalised progress values in range $t \in [0.0, 1.0]$.
2. **`Total` (`total`):** Total steps for normalising the iterator ($N$). Accepts `"N"`, `"maxloop"`, `"char.n"`, `"syl.n"`. (Default: `"N"`).
3. **`Accel` (`accel`):** Non-linear acceleration / easing exponent ($1.0 = \text{linear}$; $> 1.0 = \text{ease-in}$; $< 1.0 = \text{ease-out}$). (Default: `"1.0"`).
4. **`V1` (`v1`):** Start value at $t=0.0$. Accepts scalars, colours (`#FF0000`, `&H0000FF&`), tags (`\blur0\fscx100`), or ASSdraw paths (`m 0 0 l 50 0...`).
5. **`V2` (`v2`):** End value at $t=1.0$. Also accepts multi-stop comma-separated strings or JSON arrays for multi-stage keyframe progressions ($V_1 \to V_2 \to V_3 \dots$).

---

### 14.2. Output Ports (*Outputs*)
1. **`[1.1] Data`:** Interpolated discrete output corresponding to active progress $t$.
2. **`[1.2] Batch / List`:** Complete comma-separated list of all $N$ interpolated values for batch assignments.

---

### 14.3. Algorithmic Detail and Polymorphic Type Dispatch

```
Normalised Progress:   t = (Iterator - 1) / (Total - 1)   ───>   t_eased = t^Accel
                                                                     │
              ┌───────────────────┬───────────────────┬──────────────┴──────────────┐
              ▼                   ▼                   ▼                             ▼
       [ Scalars ]          [ Colours ]         [ ASS Tags ]              [ ASSdraw Morphing ]
      V1 + (V2-V1)·t       RGB Interpolated   Keyframe Blending         Equidistant Resampling
```

#### 14.3.1. Normalisation and Easing
Given iterator $i$ and total count $N$:
$$t = \begin{cases} i & \text{if } 0.0 \le i \le 1.0 \text{ and } N=1 \\ \frac{i - 1}{N - 1} & \text{if } N > 1 \\ 0.0 & \text{otherwise} \end{cases}$$
$$t_{\text{eased}} = \begin{cases} t^{\text{accel}} & \text{if } \text{accel} > 1.0 \\ 1.0 - (1.0 - t)^{1.0 / \text{accel}} & \text{if } 0.0 < \text{accel} < 1.0 \\ t & \text{if } \text{accel} = 1.0 \end{cases}$$

#### 14.3.2. Data Type Handling Mechanics
1. **ASSdraw Vector Geometries (Morphing):**
   * Contours are extracted from both shapes using Clipper2.
   * Both contours are resampled to an identical vertex count $M = \max(|C_1|, |C_2|, 30)$ uniformly spaced by arc length.
   * Vertex pairs are linearly interpolated:
     $$P_k(t) = (1 - t_{\text{eased}}) \cdot P_{1,k} + t_{\text{eased}} \cdot P_{2,k}$$
   * The continuous ASSdraw path is reconstructed.
2. **Hex / ASS Colours:**
   * Channels $(R_1, G_1, B_1)$ and $(R_2, G_2, B_2)$ are decomposed and interpolated linearly in RGB space.
3. **ASS Tag Blocks (Keyframing):**
   * Numeric tags (`\fscx`, `\fscy`, `\frz`, `\alpha`, `\blur`, etc.) are parsed and interpolated algebraically.
4. **Numeric Scalars:**
   * $V(t) = V_1 + (V_2 - V_1) \cdot t_{\text{eased}}$, formatted as clean integers where applicable.

---

### 14.4. Synergies and Practical Workflow Examples
* **Vector Morphing:** Connect primitive `"Circle"` to `V1` and primitive `"Star"` to `V2`, routing `Data` into `System/Output` inside a `Loops/MaxLoop` for smooth geometric morphing.

### 14.5. Practical Production Example
* **Geometric Vector Morphing from Circle to Star in 10 FBF Steps:**
  Continuously interpolating between two vector primitives resampled via Clipper2 with non-linear acceleration (`accel=1.5`):

  ```
  [Loops/MaxLoop: total=10] ──► j ──► Iterator ──────────────────┐
                                                                 ▼
  [Functions/Interpolator: total=10, accel=1.5] ──► Data ──► Shape / Text ──► [System/Output]
     v1: "m 50 0 b 22 0...", v2: "m 50 0 l 61 35..."
  ```

  * **ASS Output Emitted in the Subtitle:**
    * **Iteration $j=1$ ($t=0.0$):** Emits `{\an5\pos(320, 240)\p1}m 50 0 l 44.8 0.5 ...` (exact circular contour resampled to 30 nodes).
    * **Iteration $j=6$ ($t \approx 0.556, t_{\text{eased}} \approx 0.415$):** Emits intermediate hybrid geometry with bulging edges transitioning smoothly.
    * **Iteration $j=10$ ($t=1.0$):** Emits `{\an5\pos(320, 240)\p1}m 50 0 l 61 35 l 98 35 ...` (complete regular star).
    * Strict 1:1 vertex correspondence prevents degenerate coordinate collapsing or self-intersecting path glitches during morphing.

---

## 15. Node `Functions/Text on Path` (Text Flow Along Curved Paths)

* **Canonical Category:** `Functions` (UI: *Functions / Text on Path*)
* **Purpose:** Projects, spaces, and orientates text strings or individual glyphs along an ASSdraw vector path or curve. Automatically computes Cartesian coordinates and exact tangential rotation angles (`\frz`) at every point to ensure text follows the natural trajectory curvature.

![Functions/Text on Path](img/text_on_path.png)

---

### 15.1. Header Mode Combos
1. **`Center`:** Centres the full text string across the midpoint of total path length.
2. **`Left`:** Aligns text start at path origin ($d=0$) plus configured `Offset`.
3. **`Right`:** Aligns text end at path termination ($d=L_{\text{total}}$) minus text width.
4. **`Justified`:** Evenly distributes characters or syllables along the full path length ($0.0 \to L_{\text{total}}$).
5. **`Animated`:** Maps parameter `Offset` to normalised range $0.0 \to 1.0$ to animate text flowing along the curve.

---

### 15.2. Input Ports and Body Properties (*Inputs & Properties*)
1. **`Path / Shape` (`shape`):** ASSdraw vector path acting as the spatial guide rail.
2. **`Offset` (`offset`):** Longitudinal displacement offset along the path in pixels (or $0.0 \to 1.0$ progress in `Animated` mode). (Default: `"0"`).
3. **`Extra Angle` (`extra_angle`):** Additional angular offset in degrees added to the computed tangent angle. (Default: `"0"`).
4. **`Subdivs` (`subdivs`):** Number of subdivisions used for internal Bézier sampling along the path. (Default: `"30"`).

---

### 15.3. Output Ports (*Outputs*)
1. **`[1.1] Tag Out`:** Combined string of ASS positioning and tangential rotation tags: `\pos(X, Y)\frz(Angle)`.
2. **`[1.2] \pos Tag`:** Isolated ASS position tag `\pos(X, Y)`.
3. **`[1.3] Angle (\frz)`:** Isolated ASS rotation tag `\frz(Angle)`.
4. **`[1.4] X`:** Discrete horizontal coordinate $X$ on the path (px).
5. **`[1.5] Y`:** Discrete vertical coordinate $Y$ on the path (px).
6. **`[1.6] Length`:** Total arc length $L_{\text{total}}$ of the guide path in pixels.

---

### 15.4. Algorithmic Detail and Curvature Kinematics

```
                 P_tangent (X, Y)
                        ● ───> Tangent Vector (dx, dy)
                       / \
                      /   \ θ = atan2(dx, dy) - 90°
                     /     \
Guide Route: P_start ●       ● P_end (L_total)
```

1. **In-Line Character Metric Mapping:**
   Given total text line metric width $L_{\text{line}}$ and relative character position $d_{\text{char}} = X_{\text{char}} - X_{\text{start}}$:
   $$d_{\text{target}} = \text{lineoffset} + d_{\text{char}}$$
2. **Spatial Path Arc-Length Lookup:**
   Finds segment $S_k$ where target distance $d_{\text{target}}$ resides clamped in $[0, L_{\text{total}}]$, retrieving point $(X, Y)$ and velocity vector $(dx, dy)$.
3. **Tangent and Heading Calculation:**
   $$\theta_{\text{base}} = \left( \operatorname{atan2}(dx, dy) \cdot \frac{180}{\pi} - 90^\circ \right) + \text{extra\_angle}$$
   Angles are wrapped into $(-180^\circ, 180^\circ]$ to prevent sudden 360-degree rotation flips in libass.

---

### 15.5. Synergies and Practical Workflow Examples
* **Dynamic Spline Text Flow:** Route output `Spline` from `Functions/Bezier Curve` into `Path / Shape` of `Text on Path`, linking `Offset` to a time oscillator for undulating sinusoidal text waves.

### 15.6. Practical Production Example
* **Justified Glyph Distribution Along a Guide Arc:**
  Projecting word characters along a parabolic vector path `m 100 250 b 200 150 300 150 400 250` in `justified` mode:

  ```
  [Shape/Library: "Arc"] ──► Path / Shape ────────────────────────┐
                                                                  ▼
  [Functions/Text on Path: mode=justified, subdivs=30] ──► Tag Out ──► Tags In ──► [System/Output]
                                                                                    Return: char.text
  ```

  * **Parametric Mapping per Character:**
    For a 3-character word with active iterator `char.i` ($1, 2, 3$):
    * Character 1 ($d=0\text{ px}$, arc origin): $P_1(100.0, 250.0)$, ascending tangent $\theta = 45^\circ \to$ Emits `{\pos(100,250)\frz45}K`.
    * Character 2 ($d=L/2$, arc apex): $P_2(250.0, 175.0)$, horizontal tangent $\theta = 0^\circ \to$ Emits `{\pos(250,175)\frz0}a`.
    * Character 3 ($d=L$, arc termination): $P_3(400.0, 250.0)$, descending tangent $\theta = -45^\circ \to$ Emits `{\pos(400,250)\frz-45}r`.

---

## 16. Node `Functions/Text to Shape` (Typographic Glyph Vectorisation)

* **Canonical Category:** `Functions` (UI: *Functions / Text to Shape*)
* **Purpose:** Rasterises and vectorises TrueType/OpenType font glyphs into mathematical ASSdraw vector paths (`m ... b ... l ...`). Enables converting syllable text, line text, or alphanumeric constants into vector geometries suitable for boolean operations, morphological slicers (*Slicer*), concentric border extrusion, or particle sampling.

![Functions/Text to Shape](img/text_to_shape.png)

---

### 16.1. Input Ports and Body Properties (*Inputs & Properties*)
1. **`Text` (`text`):** Text string to vectorise. If empty, automatically extracts stripped text from active syllable or line (`syl.text_stripped` or `line.text_stripped`).
2. **`Font` (`font_name`):** Typeface family name (e.g. `"Arial"`, `"Montserrat"`, `"Impact"`). If empty, inherits font from the active ASS subtitle style.
3. **`Size` (`font_size`):** Font size in typographic points. If empty, inherits size from the active ASS style.
4. **`Scale` (`scale`):** Geometric scale multiplier applied to generated vector coordinates. (Default: `"1.0"`).
5. **`Bold` (`bold`):** [Property] Bold style toggle (`true` / `false`).
6. **`Italic` (`italic`):** [Property] Italic style toggle (`true` / `false`).

---

### 16.2. Output Ports (*Outputs*)
1. **`[1.1] Shape Out`:** Complete closed and centred ASSdraw vector path with move `m`, line `l`, and cubic Bézier `b` commands.
2. **`[1.2] Width`:** Net bounding box metric width in pixels ($W$).
3. **`[1.3] Height`:** Net bounding box metric height in pixels ($H$).

---

### 16.3. Algorithmic Detail and High-Precision Typography Engine

```
TrueType/OpenType Font ───> FontVectorEngine (Win32 GDI 64x Subpixel) ───> FontVectorMetrics (Lossless)
                                                                               │
               ┌───────────────────────────────────────────────────────────────┴───────────────────────────────────────────────────────────────┐
               ▼                                                                                                                               ▼
  [ ASSdraw Path `m...b...l...` ]                                                                                     [ Integral Metric Record (O(1)) ]
     For Slicer, Array, Morphs                                                                                    advance_width, cell_height, ascent, descent,
                                                                                                                  lsb, rsb, ink_bbox, delta_x, delta_y
```

1. **Native Subpixel Vector Extraction (64x):** `FontVectorEngine` inspects glyph contour tables using the Win32 GDI API at native 64x subpixel resolution (`ExtTextOutW` inside a path bracket with `BeginPath`), extracting quadratic and cubic font splines into normalised ASSdraw cubic Bézier curves (`b cp1x cp1y cp2x cp2y endx endy`).
2. **Lossless Metric Record (`FontVectorMetrics`):** Unlike conventional rasterisers that discard cell metric properties, `FontVectorEngine` computes and preserves:
   * **Side Bearings:** Left Side Bearing ($\text{LSB}$) and Right Side Bearing ($\text{RSB}$), satisfying the typographic identity:
     $$\text{Advance Width} = \text{LSB} + \text{Ink Width} + \text{RSB}$$
   * **Barycentric Offset ($\Delta X, \Delta Y$):** The exact displacement between typographic pen advance centre and visual ink centroid:
     $$\Delta X = \frac{\text{LSB} - \text{RSB}}{2}$$
   * **Cell Heights and Baseline:** $\text{ascent}$, $\text{descent}$, and $\text{cell\_height}$, ensuring exact vertical screen registration.
3. **Anchor Modes:**
   * **`typographic` (Default):** Origin placed at the typographic advance centre, guaranteeing 1:1 pixel match with libass `\pos(line.center, line.middle)`.
   * **`ink`:** Origin centred on the physical bounding box centroid of drawn ink, suited for particle generation and morphological slicing.
   * **`baseline` / `origin`:** Origin pinned to the typographic pen baseline.

---

### 16.4. Synergies and Practical Workflow Examples
* **Voronoi Text Shatter with `Shape/Slicer`:** Chain `Text to Shape` $\to$ `Shape/Slicer (Voronoi)` to fragment glyphs into polygonal shards for 3D explosion animations.
* **Monolithic Line Fusion with `Shape/Union & Divide (FUSION)`:** Connect `Text to Shape` to `Union & Divide` in `FUSION` mode to emit optimised single-line vector subtitles without overloading libass.

### 16.5. Practical Production Example
* **Subpixel Vectorisation and Outline Extrusion:**
  Transforming active syllable text into native ASSdraw vector geometry to extrude a continuous vector outline via `Shape/Stroke`:

  ```
  [Variables/Sys Var: var_name=syl.text] ──► Text ─────────────────┐
                                                                   ▼
  [Functions/Text to Shape: font_name="Arial", font_size="50"] ──► Shape Out ──► Shape / Text ──► [Shape/Stroke: width=4.0]
                                                                                                    │
                                                                                                    ▼ Shape Out
                                                                                                 Return ──► [System/Output]
  ```

  * **Subpixel Vector Extraction and Metrics:**
    `FontVectorEngine` vectorises glyphs at 64x native subpixel resolution producing normalised cubic curves `m ... b ...`, measuring $W = 42\text{ px}, H = 48\text{ px}$, and retaining the typographic barycentric offset.
  * **ASS Dialogue Line Emitted in the Script:**
    `Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\an5\pos(320,240)\p1}m 0 25 b 0 10 12 0 25 0 b 38 0 50 10 50 25 ...{\p0}`
