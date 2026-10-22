# Loops

The **Loops** category contains nodes that govern the decomposition domain of dialogue lines (`syl`, `char`, `word`, `line`), the execution of temporal or frame-by-frame (FBF) sub-loops, and the calculation of normalised progression factors.

---

## 1. Node `Loops/Main Loop` (Primary Domain Iterator)

* **Canonical Category:** `Loops` (UI: *Loops / Main Loop*)
* **Purpose:** Establishes the fundamental domain over which each selected Aegisub dialogue line is decomposed and processed (`syl`, `char`, `word`, `line`), initialising the graph lifecycle and emitting the execution flow signal and metric iteration counters.

![Loops/Main Loop](img/main_loop.png)

### 1.1. Header Badges
1. **Domain Selector (`iterator`):** Switchable via direct click on the top-right header badge or within properties:
   * `syl`: Iterates syllable by syllable respecting karaoke timing tags (`\k`, `\kf`, `\ko`, `\K`).
   * `char`: Iterates glyph by glyph individually, computing typographic metrics per character.
   * `word`: Iterates word by word delimited by whitespace.
   * `line`: Iterates once for the entire dialogue line as a single monolithic entity.
2. **Whitespace Handling (`blank_mode` / `noblank`):** Switchable via the adjacent header badge:
   * `no_blank` (*NO BLANK / Ignore Spaces*): Automatically skips whitespace characters, tabs, and line breaks. Iteration counters reflect visible elements only ($ci$ and $cn$).
   * `with_blanks` (*WITH BLANK / All*): Processes all characters, assigning indices and timing intervals to whitespace elements ($i$ and $n$).

### 1.2. Output Ports (*Outputs*)
1. **`[1.1] Loop`:** Emits the primary execution flow signal that drives and synchronises downstream nodes for each elemental unit of the active domain.
2. **`[1.2] Iterator (i)`:** 1-based ordinal numerical index of the active unit within the line ($1 \dots N$). Injected into the context as `i`, `syl.i`, `char.i`, or `word.i`.
3. **`[1.3] Total (N)`:** Total count of elements calculated for the active domain within the line. Injected as `N`, `syl.n`, `char.n`, or `word.n`.

### 1.3. Algorithmic Detail and Context Injection
Upon evaluating each Aegisub dialogue line, the node constructs contextual metric structures for the active unit:
* **Whitespace-dependent indexing:**
  * In `no_blank` mode: $i \leftarrow ci$, $N \leftarrow cn$, ensuring ordinal indices contain no numeric gaps caused by whitespace.
  * In `with_blanks` mode: $i \leftarrow i_{\text{abs}}$, $N \leftarrow n_{\text{abs}}$, preserving absolute sequence order in the source line.
* **Projected spatial metrics:**
  Calculates and exposes the unit's pixel Cartesian coordinates:
  `center`, `middle`, `left`, `right`, `top`, `bottom`, `width`, `height`, `x`, `y`.
* **Timing intervals:**
  Establishes boundaries $[t_{\text{start}}, t_{\text{end}}]$ and duration $t_{\text{dur}} = t_{\text{end}} - t_{\text{start}}$ for the active unit.
* **Injected global variables:**
  `i`, `n`, `fx_i`, `fx_n`, alongside the active unit object (`syl`, `char`, `word`, or `line`).

### 1.4. Practical Production Example
* **Staggered Parabolic Offset per Syllable:**
  Connecting `Loop` to the `Loop / Domain` input of `System/Output` with `iterator: syl`:
  
  ```
  [Main Loop: syl] ──► Loop ──► [System/Output]
                   ──► Iterator (i)
                   ──► Total (N)
  ```
  
  In a tag node connected to `Output (Tags)`:
  ```
  {\pos(syl.center, syl.middle - 25 * math.sin(math.pi * (syl.i - 1) / max(1, syl.n - 1)))\k(syl.dur / 10)}
  ```
  
  For a line with $N = 5$ syllables, the third syllable ($i = 3$) achieves peak displacement:
  $$\Delta y = -25 \cdot \sin\left(\pi \cdot \frac{2}{4}\right) = -25 \text{ px}$$

---

## 2. Node `Loops/MaxLoop` (Sub-Loop Multiplier and FBF Generator)

* **Canonical Category:** `Loops` (UI: *Loops / MaxLoop*)
* **Purpose:** Multiplies and expands incoming execution flow within the active unit into $N$ temporal sub-iterations or concurrent replicas (`normal`), or segments the time interval into discrete regular video frames (`fbf`).

![Loops/MaxLoop](img/maxloop.png)

### 2.1. Header Modes and Dynamic Layout
The operating mode is toggled via the interactive header button:
1. **`normal` (*NORMAL*):**
   * Multiplies downstream subgraph evaluation into $N$ concurrent repetitions.
   * Keeps the original start and end timestamps of the base element invariant (`start_time`, `end_time`).
   * Active input ports: `Loop In`.
   * Visible properties: `iterations` (default: `"3"`), `var_name` (default: `"j"`).
2. **`fbf` (*Frame by Frame*):**
   * Divides the time range $[Start, End]$ into uniform frames of duration `step_ms`.
   * Active input ports: `Loop In`, `Start`, `End`.
   * Visible properties: `step_ms` (default: `"41.7"` $\approx 23.976\text{ fps}$), `start_time` (default: `"start_time"`), `end_time` (default: `"end_time"`), `var_name` (default: `"j"`).

### 2.2. Input Ports (*Inputs*)
1. **`Loop In`:** Execution signal from `Main Loop` or an upstream sub-loop.
2. **`Start` (`fbf` mode):** Start timestamp in milliseconds. If unwired, evaluates the `start_time` property or active context value (`start_time`).
3. **`End` (`fbf` mode):** End timestamp in milliseconds. If unwired, evaluates the `end_time` property or active context value (`end_time`).

### 2.3. Controls and Body Properties
1. **`[2.1] Iterations (N)` (`iterations`):** Total repetition count in `normal` mode. Supports dynamic evaluable expressions.
2. **`[2.2] Step (ms)` (`step_ms`):** Millisecond duration per frame in `fbf` mode (minimum: $1.0\text{ ms}$).
3. **`[2.3] Inicio (ms)` (`start_time`):** Default start time expression in `fbf` mode.
4. **`[2.4] Fin (ms)` (`end_time`):** Default end time expression in `fbf` mode.
5. **`[2.5] Var Name` (`var_name`):** Identifier of the iteration counter variable injected into local context (default: `"j"`).

### 2.4. Output Ports (*Outputs*)
1. **`[1.1] Loop Out`:** Emits the multiplied flow signal to downstream receiver nodes.
2. **`[1.2] Counter`:** Ordinal index of the active sub-iteration ($1 \dots N$).
3. **`[1.3] Total`:** Total number of scheduled iterations ($N$).

### 2.5. Mathematical Model and Temporal Distribution
* **Normal Mode:**
  Evaluates for each $j \in [1, N]$. Each execution retains the element's $[t_{\text{start}}, t_{\text{end}}]$ bounds and sets:
  $$\text{var\_name} = j, \quad \text{var\_name\_max} = N, \quad \text{fx\_i} = j, \quad \text{fx\_n} = N$$
* **FBF (Frame by Frame) Mode:**
  Given $Start$, $End$, and frame duration $\Delta t = step\_ms$, computes total frame count:
  $$N = \left\lceil \frac{End - Start}{\Delta t} \right\rceil$$
  For each frame $k \in [1, N]$:
  $$t_{\text{start}}^{(k)} = Start + (k - 1) \cdot \Delta t$$
  $$t_{\text{end}}^{(k)} = \min(End, Start + k \cdot \Delta t)$$
  $$t_{\text{dur}}^{(k)} = t_{\text{end}}^{(k)} - t_{\text{start}}^{(k)}$$
  The local context is updated with timing variables `st`, `et`, `start_time`, `end_time`, `frame_start_time`, `frame_end_time`, `frame_dur`, `fd`, `fx_start_time`, `fx_end_time`, `fx_dur`, and sets `in_fbf_loop = True`.

### 2.6. Practical Production Examples
* **Example 1 (Normal Mode): Multi-Layer Drop Shadow Extrusion:**
  Configuration: `mode: normal`, `iterations: 4`, `var_name: j`.
  Generates 4 offset layers with progressive opacity attenuation:
  ```
  {\pos(syl.center + j * 1.5, syl.middle + j * 1.5)\1c&H000000&\1a&H80&\3a&HFF&}
  ```
  For $j = 1$, displacement is $(1.5, 1.5)$; for $j = 4$, it reaches $(6.0, 6.0)$, producing dense directional shading.

* **Example 2 (FBF Mode): Frame-by-Frame Coordinates without `\t`:**
  Configuration: `mode: fbf`, `step_ms: 41.7`, `var_name: j`.
  Each generated line represents an individual video frame with discrete coordinates:
  ```
  {\pos(syl.center + j * 4, syl.middle)\alpha&H00&}
  ```

---

## 3. Node `Loops/Module` (Modular Sampling and Normalised Progress)

* **Canonical Category:** `Loops` (UI: *Loops / Module*)
* **Purpose:** Computes the normalised progression factor across the $[0.0, 1.0]$ interval or modular offset divisions from ordinal loop counters ($i, j$).

![Loops/Module](img/module.png)

### 3.1. Input Ports (*Inputs*)
1. **`Iterator (i)`:** Current iteration index. If unwired, evaluates the `iter` property.
2. **`Total (N)`:** Total count of reference elements. If unwired, evaluates the `total` property.
3. **`Sub-step (m)`:** Additional offset or subdivision parameter. If unwired, evaluates the `sub_m` property.

### 3.2. Controls and Body Properties
1. **`[2.1] Iterator (i)` (`iter`):** Expression or identifier for the index (default: `"i"`).
2. **`[2.2] Total (N)` (`total`):** Expression or identifier for the total count (default: `"N"`).
3. **`[2.3] Sub-step (m)` (`sub_m`):** Offset value expression (default: `"0"`).

### 3.3. Output Ports (*Outputs*)
1. **`[1.1] Data`:** Numerical result of the normalised progression.

### 3.4. Algorithmic Detail and Mathematical Formulation
The node evaluates all three operands ($i, N, m$) within the active execution context and computes:

$$\text{Denominator} = N + m - 1.0$$

$$\text{Data} = \begin{cases} \dfrac{i - 1.0 + m}{\text{Denominator}} & \text{if } \text{Denominator} \neq 0 \text{ and } N > 1.0 \\ m & \text{otherwise} \end{cases}$$

#### Output Serialisation Rules:
1. The result is rounded to 4 decimal places: $R = \text{round}(\text{Data}, 4)$.
2. If $R$ is an exact integer, it is serialised without decimal points (e.g. `0` or `1`).
3. If it contains a fractional component, it is formatted with up to 4 decimal places, omitting trailing zeroes (e.g. `0.25`, `0.3333`).

#### Behaviour when $m = 0$:
For $i = 1 \dots N$ where $N > 1$:
* First unit ($i = 1$): $\text{Data} = \frac{0}{N - 1} = 0$
* Last unit ($i = N$): $\text{Data} = \frac{N - 1}{N - 1} = 1$
* The output divides the unit interval $[0.0, 1.0]$ into $N - 1$ uniform increments.

### 3.5. Practical Production Examples
* **Easing Curve Scale Modulation:**
  Routing `Data` into a quadratic deceleration formula or the `Basics/Math (Category: easing)` node to map character sequence order to non-linear typographic scaling:
  
  ```
  [Main Loop: char] ──► Iterator (i) ──► [Module] ──► Data ──► [Tags]
                    ──► Total (N)    ──►
  ```
  
  Connecting `Data` to the `Tags` property:
  ```
  {\fscx(100 + Data * 50)\fscy(100 + Data * 50)}
  ```
  For the first character ($Data = 0.0$), scale is `\fscx100\fscy100`. For the central character when $N = 5$ ($Data = 0.5$), scale reaches `\fscx125\fscy125`, and for the final character ($Data = 1.0$), `\fscx150\fscy150`.
