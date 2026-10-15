# Times

The **Time** category handles the chronometric calculation of ASS subtitle events, allowing users to phase-shift phonetic milestones, modulate continuous temporal transitions (`\t`), compute frame equivalences, and interconnect consecutive dialogue lines via adaptive synchronisation.

### Chapter Thematic Structure:
* **Section 7.A — Core Phases, Retiming, and Inter-Line Synchronisation:** `Time/Retime` (§1), `Time/Lead In` (§2), `Time/Lead Out` (§3), `Time/Synced` (§4).
* **Section 7.B — Intermediate Sections, Loops, and Duration Metrics:** `Time/Middle 1` (§5), `Time/Middle 2` (§6), `Time/Loop 1` (§7), `Time/Loop 2` (§8), `Time/Duration` (§14), `Time/Offset` (§15).
* **Section 7.C — Format Conversion, Frame Boundaries, and Temporal Interpolation:** `Time/Parse ASS Time` (§9), `Time/Format ASS Time` (§10), `Time/Time to Frame` (§11), `Time/Frame to Time` (§12), `Time/Ipol` (§13).

---

## 1. Node `Time/Retime` (Phase Retiming and `\t` Mapping)

* **Canonical Category:** `Time` (UI: *Time / Retime*)
* **Purpose:** Resynchronises temporal intervals and dynamically rescales continuous ASS `\t(...)` transformation blocks according to the phonetic or structural phase of the active element (`syl`, `line`, `presyl`, `postsyl`, etc.), enabling additive offsets and non-linear acceleration.

![Time/Retime](img/retime.png)

### 1.1. Header Mode Combos
1. **`[2.1] Mode` (`phase`):** Dropdown selector determining the base temporal reference interval. It features 10 phonetic and structural phase modes:

| Mode (`phase`) | Base Interval [$T_1, T_2$] | Technical Description |
| :--- | :--- | :--- |
| `syl` | $[T_{\text{syl\_start}}, T_{\text{syl\_end}}]$ | **Active Syllable (Default):** Exact temporal singing window of the syllable or character. |
| `presyl` | $[T_{\text{syl\_start}}, T_{\text{syl\_start}}]$ | **Pre-Syllable:** Instantaneous start timestamp of the syllable (for preparatory animations or lead-in transitions). |
| `postsyl` | $[T_{\text{syl\_end}}, T_{\text{syl\_end}}]$ | **Post-Syllable:** Instantaneous ending timestamp of the syllable (for post-singing decays or immediate lead-outs). |
| `line` | $[T_{\text{line\_start}}, T_{\text{line\_end}}]$ | **Full Line:** Global temporal window spanning the entire dialogue line duration. |
| `preline` | $[T_{\text{line\_start}}, T_{\text{line\_start}}]$ | **Pre-Line:** Instantaneous line start timestamp. |
| `postline` | $[T_{\text{line\_end}}, T_{\text{line\_end}}]$ | **Post-Line:** Instantaneous line ending timestamp. |
| `start2syl` | $[T_{\text{line\_start}}, T_{\text{syl\_start}}]$ | **Lead-In to Syllable:** Interval from line start until the active syllable begins singing. |
| `syl2end` | $[T_{\text{syl\_end}}, T_{\text{line\_end}}]$ | **Syllable to Line End (Lead-Out):** Interval from when the active syllable ends singing until the full line concludes. |
| `abs` | $[0, 0]$ | **Absolute:** Decouples timings from syllable/line milestones; `Offset In` and `Offset Out` directly define the numeric millisecond window. |
| `sylpct` | $[T_{\text{syl\_start}} + \frac{O_{\text{in}} \cdot D_{\text{syl}}}{100}, T_{\text{syl\_start}} + \frac{O_{\text{out}} \cdot D_{\text{syl}}}{100}]$ | **Syllable Percentage:** `Offset In` and `Offset Out` are interpreted as percentages ($0\% \dots 100\%$) of the syllable's total duration. |

### 1.2. Input Ports and Body Properties (*Inputs & Properties*)
1. **`Tags or \t` (`tags`):** String containing ASS override tags. Accepts direct static tags (e.g. `\fscx150\fscy150\alpha&HFF&`) or pre-existing continuous transformation blocks `\t(...)`.
2. **`Offset In (ms)` (`offset_in`):** Temporal shift in milliseconds applied to the starting point $T_1$. Accepts positive numbers (delay), negative numbers (advance), variables, or dynamic expressions (default: `0`).
3. **`Offset Out (ms)` (`offset_out`):** Temporal shift in milliseconds applied to the end point $T_2$ (default: `0`).
4. **`Accel` (`accel`):** Acceleration exponent for ASS interpolation in the tag `\t(t1, t2, accel, \tags)`. A value of `1.0` yields constant linear velocity; values $< 1.0$ yield deceleration (*ease-out*); values $> 1.0$ yield progressive acceleration (*ease-in*) (default: `1.0`).

### 1.3. Output Ports (*Outputs*)
1. **`[1.1] \t Out`:** Tag block formatted in ASS syntax `\t(t1, t2, [accel,] \tags)`. Timestamps $t_1$ and $t_2$ are emitted **in the local time space of the subtitle line** (relative to `0 ms` from the physical start of the generated line).
2. **`[1.2] Start Time`:** Absolute start timestamp $T_1$ in milliseconds on the global video timeline.
3. **`[1.3] End Time`:** Absolute end timestamp $T_2$ in milliseconds on the global video timeline.
4. **`[1.4] Duration`:** Net calculated duration in milliseconds: $D = \max(0, T_2 - T_1)$.

### 1.4. Mathematical Model and `\t` Tag Mapping

```
   Line Start                                              Line End
   ├──────────────────────────┬─────────────────┬──────────────────┤
   │        start2syl         │  syl (active)   │     syl2end      │
   │                          ├────────┬────────┤                  │
   │                          │ presyl │ postsyl│                  │
───┴──────────────────────────┴────────┴────────┴──────────────────┴───► Time
   0 ms                      T_syl_st  T_syl_et  Line_dur
```

#### 1.4.1. Transformation of Pre-Existing `\t(...)` Blocks
When the `Tags or \t` input contains continuous transformation blocks `\t(t_a, t_b, ...)`, the node parses the expression and recalculates the relative timings while preserving internal sub-intervals:

$$\tilde{t}_1 = T_{\text{local\_1}} + t_a, \quad \tilde{t}_2 = T_{\text{local\_1}} + t_b$$

If the input `\t(...)` tag specified no prior timings (e.g. `\t(\blur10)`), the node automatically injects the full calculated phase window:

$$\text{\textbackslash t}(T_{\text{local\_1}}, T_{\text{local\_2}}, [a,] \text{\textbackslash blur10})$$

#### 1.4.2. Time Space Duality (Local vs. Global)
> [!IMPORTANT]
> * **Output `\t Out`:** Always operates in time **relative to the physical line start** ($t=0\text{ ms}$). This is essential because the ASS standard `\t` tag measures offsets with respect to the start timestamp of the subtitle dialogue line itself on screen.
> * **Outputs `Start Time` and `End Time`:** Emit **absolute video timestamps**, required when spawning independent timed events in `System/Output`.

### 1.5. Synergies and Practical Workflow Examples
* **Decoupled Lead-In and Lead-Out Effects:** Use two `Retime` nodes: one configured with `Mode: start2syl` for the entrance animation (*Lead-In*), and another with `Mode: syl2end` or `postsyl` for the exit decay (*Lead-Out*).
* **Chaining with Modulators:** Route the `\t Out` output into `Concatenate` alongside position `\pos` and base styling tags to assemble complete ASS lines in a single stream.

### 1.6. Practical Production Example
* **Continuous Transformation on Lead-In with Retime:**
  Generating a lead-in animation where each syllable scales from 0% to 100% and fades from transparent to opaque prior to singing:

  ```
  Tags In: \fscx100\fscy100\alpha&H00& ──► Tags or \t ──► [Time/Retime: start2syl, accel=0.8]
                                                                └──► \t Out ──► Tags ──► [System/Output]
  ```

  Supplying `Tags` in `System/Output` with base style `{\an5\pos(syl.center, syl.middle)\fscx0\fscy0\alpha&HFF&}`:
  The node emits:
  ```
  {\an5\pos(syl.center, syl.middle)\fscx0\fscy0\alpha&HFF&\t(0, syl.syl_start, 0.8, \fscx100\fscy100\alpha&H00&)}
  ```
  The syllable smoothly transitions over the lead-in window (*start2syl*) with a decelerating easing curve (*ease-out*, `accel=0.8`).

---

## 2. Node `Time/Lead In` (Stepped Lead-In Offset)

* **Canonical Category:** `Time` (UI: *Time / Lead In*)
* **Purpose:** Calculates a stepped temporal offset based on the sequential index ($i$) of the active unit, creating cascaded anticipation waves prior to the singing of each syllable or character.

![Time/Lead In](img/lead_in.png)

### 2.1. Input Ports and Body Properties (*Inputs & Properties*)
1. **`Delay (ms)` (`delay_ms`):** Stepped delay duration per unit in milliseconds. Accepts numeric constants, variables, or inline arithmetic expressions (default: `40`).

### 2.2. Output Ports (*Outputs*)
1. **`[1.1] Data`:** Temporal offset in milliseconds resulting from the stepped formula.

### 2.3. Mathematical Model of Stepped Lead-In
The node evaluates the active unit index $i \in \{1, \dots, N\}$ (where $i$ is the 1-based syllable or character index in the main loop cycle) and applies a fixed lookahead anticipation margin of $-200\text{ ms}$:

$$T_{\text{out}} = T_{\text{base}} + \Delta_{\text{delay}} \cdot (i - 1) - 200$$

Where:
* $T_{\text{base}}$ is the base reference timestamp (default $0.0\text{ ms}$).
* $\Delta_{\text{delay}}$ is the value configured in `Delay (ms)`.
* $i$ is the active unit index ($1$-based).
* $-200\text{ ms}$ is the standard kinematic lookahead constant.

#### Stepping Progression Example ($N=4\text{ units}, \Delta=40\text{ ms}$):
* Unit $1$ ($i=1$): $40 \cdot (1 - 1) - 200 = -200\text{ ms}$
* Unit $2$ ($i=2$): $40 \cdot (2 - 1) - 200 = -160\text{ ms}$
* Unit $3$ ($i=3$): $40 \cdot (3 - 1) - 200 = -120\text{ ms}$
* Unit $4$ ($i=4$): $40 \cdot (4 - 1) - 200 = -80\text{ ms}$

### 2.4. Synergies and Practical Workflow Examples
* **Feeding `Time/Retime`:** Connect the `Data` output of `Lead In` to the `Offset In (ms)` port of a `Time/Retime` node (in `syl` or `start2syl` mode) to produce a fluid cascade where each letter begins animating progressively before its actual singing onset.

### 2.5. Practical Production Example
* **Cascaded Anticipation Wave with Lead In and Retime:**
  Chaining `Lead In` into the `Offset In (ms)` port of a `Retime` node:

  ```
  [Time/Lead In: delay_ms=40] ──► Data ──► Offset In (ms) ──► [Time/Retime: syl, accel=1.0]
                                                                    └──► \t Out ──► Tags ──► [System/Output]
  ```

  If the `Tags or \t` input of `Retime` receives `\fscx130\fscy130\1c&H00FFFF&`:
  For a line with 4 syllables, each element begins accenting $200 - 40 \cdot (i - 1)$ ms before its singing onset, creating a continuous wave anticipating phonetic delivery.

---

## 3. Node `Time/Lead Out` (Stepped Lead-Out Offset)

* **Canonical Category:** `Time` (UI: *Time / Lead Out*)
* **Purpose:** Calculates a stepped temporal extension based on the distance of the active unit from the end of the line ($i - n$), generating progressive decays and coordinated post-singing exit sequences.

![Time/Lead Out](img/lead_out.png)

### 3.1. Input Ports and Body Properties (*Inputs & Properties*)
1. **`Delay (ms)` (`delay_ms`):** Delay in milliseconds applied to the stepped exit sequence (default: `40`).

### 3.2. Output Ports (*Outputs*)
1. **`[1.1] Data`:** Temporal offset in milliseconds resulting from the stepped lead-out formula.

### 3.3. Mathematical Model of Stepped Lead-Out
The node evaluates the relative position of unit $i$ with respect to the total unit count $n$:

$$T_{\text{out}} = T_{\text{base}} + \Delta_{\text{delay}} \cdot (i - n - 1) + 200$$

Where:
* $n$ is the total number of units in the line (`syl.n`, `char.n`).
* $+200\text{ ms}$ is the post-sustain temporal constant.

#### Exit Stepping Progression Example ($n=4\text{ units}, \Delta=40\text{ ms}$):
* Unit $1$ ($i=1$): $40 \cdot (1 - 4 - 1) + 200 = 40 \cdot (-4) + 200 = +40\text{ ms}$
* Unit $2$ ($i=2$): $40 \cdot (2 - 4 - 1) + 200 = 40 \cdot (-3) + 200 = +80\text{ ms}$
* Unit $3$ ($i=3$): $40 \cdot (3 - 4 - 1) + 200 = 40 \cdot (-2) + 200 = +120\text{ ms}$
* Unit $4$ ($i=4$): $40 \cdot (4 - 4 - 1) + 200 = 40 \cdot (-1) + 200 = +160\text{ ms}$

### 3.4. Synergies and Practical Workflow Examples
* **Progressive Reading-Order Disappearance:** Connect `Data` to `Offset Out (ms)` in `Time/Retime` (in `syl` or `postsyl` mode) to ensure earlier syllables fade out first while subsequent syllables remain longer on screen, matching natural reading flow.

### 3.5. Practical Production Example
* **Progressive Trailing Fade with Lead Out:**
  Routing `Lead Out` into `Offset Out (ms)` in a `Retime` node set to `postsyl` mode:

  ```
  [Time/Lead Out: delay_ms=50] ──► Data ──► Offset Out (ms) ──► [Time/Retime: postsyl]
                                                                     └──► \t Out ──► Tags ──► [System/Output]
  ```

  With `Tags or \t: \alpha&HFF&`:
  The first syllable initiates its fade-out shortly after singing finishes, whereas trailing syllables retain their screen presence for a longer duration, preventing abrupt collective disappearance.

---

## 4. Node `Time/Synced` (Adaptive Inter-Line Synchronisation)

* **Canonical Category:** `Time` (UI: *Time / Synced*)
* **Purpose:** Dynamically computes extra sustain time between consecutive dialogue lines. Bridges musical pauses and silences, compensates for screen-space geometric distance between phrases, and smoothens transitions towards the next line.

![Time/Synced](img/synced.png)

### 4.1. Input Ports and Body Properties (*Inputs & Properties*)
1. **`Mode` (`mode`):** Match criterion for pairing the current line with the subsequent line (`next_line`):
   * `order`: Strictly follows sequential line order in the active dialogue list without filtering.
   * `style`: Matches the next line sharing the exact same ASS style name (`style_name`).
   * `actor`: Matches the next line sharing the exact same actor name (`actor`).
   * `layer`: Matches the next line sharing the exact same ASS layer index (`layer`).
   * `effect`: Matches the next line sharing the exact same ASS effect field (`effect`).
2. **`Constant` (`progression_const`):** Progression multiplier based on character density (ms per glyph) (default: `0`).
3. **`Fade (ms)` (`fade_dur`):** Duration of the planned visual fade-out in milliseconds (default: `300`).
4. **`Max Extra` (`max_added_time`):** Upper limit (*cap*) of extra time in milliseconds permitted to be appended to the line (default: `2000`).
5. **`Delay Line` (`delay_ms`):** Minimum gap threshold required to treat an interval as an inter-line silence (default: `250`).
6. **`Threshold` (`max_gap_threshold`):** Maximum silence threshold. If the musical pause between the current and subsequent line exceeds this threshold, the algorithm classifies it as an independent long pause and avoids stretching the line across the gap (default: `3000`).

### 4.2. Output Ports (*Outputs*)
1. **`[1.1] Extra ms`:** Net additional milliseconds calculated ($\Delta t_{\text{extra}}$).
2. **`[1.2] Sync End`:** Absolute synchronised end timestamp ($T_{\text{line\_end}} + \Delta t_{\text{extra}}$) ready to be injected into the ASS dialogue end time.

### 4.3. Algorithmic Detail and Spatial-Temporal Compensation Model

```
  Current Line                      Inter-Line Gap               Next Line
├──────────────────────┤◄────────────────────────────────►├──────────────────────┤
0 ms               Curr_End                            Next_Start            Next_End
                       │                                  │
                       └───► [ Adaptive Synchronisation ] ◄──┘
                             • Spatial gap compensation (X jump)
                             • Character progression density
                             • Fade-out duration deduction
```

The synchronisation algorithm evaluates the following sequence for every dialogue line:

#### 1. Current Line Density and Base Progression ($P_{2,\text{curr}}$)
Reading load is calculated based on element count $C_{\text{curr}}$:
$$P_{2,\text{curr}} = k_{\text{prog}} \cdot \max(0, C_{\text{curr}} - 1) + \Delta_{\text{delay}}$$

#### 2. Inter-Line Gap Evaluation ($\Delta_{\text{gap}}$)
$$\Delta_{\text{gap}} = T_{\text{next, start}} - T_{\text{curr, end}}$$

* **Case A (Isolated line or terminal line without successor):**
  $$\Delta t_{\text{extra}} = \min\left(M_{\text{max}}, \max(0, P_{2,\text{curr}})\right)$$

* **Case B (Overlapping or seamless lines, $\Delta_{\text{gap}} < \Delta_{\text{delay}}$):**
  $$\Delta t_{\text{extra}} = 0.0\text{ ms}$$

* **Case C (Long Silence / Gap Exceeding Threshold, $\Delta_{\text{gap}} > \text{Threshold}$):**
  Applies natural line progression without forcing an artificial bridge to the next phrase:
  $$\Delta t_{\text{extra}} = \min\left(M_{\text{max}}, \max(0, P_{2,\text{curr}})\right)$$

* **Case D (Standard Adaptive Bridge, $\Delta_{\text{delay}} \le \Delta_{\text{gap}} \le \text{Threshold}$):**
  The algorithm inspects the 2D spatial footprint of both lines using their vector glyph ink bounds or typographic boxes ($[X_{\text{min}}, X_{\text{max}}], [Y_{\text{min}}, Y_{\text{max}}]$) alongside explicit layout properties (`\pos`, `align`):

  1. **Subcase D.1 — Detached Screen Footprints (Disjoint Areas):**
     If the dialogue lines do not share the same vertical row band (for instance, top header in `\an8` versus bottom footer in `\an2`, or vertical displacement $|Y_{\text{curr}} - Y_{\text{next}}| > 0.5 \cdot \text{height}$):
     * **Character progression is completely omitted** ($P_2 = 0$).
     * The sustain of the current line is extended solely to bridge the gap until the next line appears, synchronising its fade-out:
       $$T_{\text{ideal\_end}} = T_{\text{next, start}} - \text{Fade}_{\text{dur}}$$

  2. **Subcase D.2 — Shared Space / Same-Origin Replacement:**
     If both lines share the same vertical band but share their horizontal origin or anchor (for example, consecutive left-aligned lines in `\an4`, right-aligned in `\an6`, or centred lines replacing the same row, where horizontal gap $X_{\text{next, left}} - X_{\text{curr, right}} \le 0$):
     * Evaluates average transition duration based on character count:
       $$T_{\text{trans}} = \frac{P_{2,\text{curr}} + P_{2,\text{next}}}{2}$$
     * **No false forward spatial leap:** Spatial displacement compensation is not added ($\Delta t_{\text{spatial}} = 0.0\text{ ms}$).
       $$T_{\text{ideal\_end}} = T_{\text{next, start}} + T_{\text{trans}} - \text{Fade}_{\text{dur}}$$

  3. **Subcase D.3 — Continuous Inline Row (Seamless Progression):**
     If both lines share the vertical row and the subsequent line is positioned consecutively along the horizontal reading direction ($X_{\text{next, left}} > X_{\text{curr, right}}$):
     * Evaluates the geometric horizontal screen jump:
       $$\text{Jump} = X_{\text{next, left}} - X_{\text{curr, right}}$$
       $$\Delta t_{\text{spatial}} = \left(\frac{\text{Jump}}{w_{\text{avg}}}\right) \cdot k_{\text{prog}}$$
     * Where $w_{\text{avg}}$ is dynamically sampled from measured glyph advances (`line.chars` via `FontEngine`).
     * Seamless ideal end timestamp:
       $$T_{\text{ideal\_end}} = T_{\text{next, start}} + T_{\text{trans}} + \Delta t_{\text{spatial}} - \text{Fade}_{\text{dur}}$$

  Finally, the net extra time is capped within the configured boundaries:
  $$\Delta t_{\text{extra}} = \min\left(M_{\text{max}}, \max(0, T_{\text{ideal\_end}} - T_{\text{curr, end}})\right)$$

### 4.4. Synergies and Practical Workflow Examples
* **Automatic Gap Filling in Continuous Karaoke:** Connect `Sync End` directly to the `End Time` port of `System/Output`. This guarantees subtitles remain visible across short pauses and fade out precisely when the next line renders.
* **Integration with `Retime`:** Route `Extra ms` into the `Offset Out` parameter of `Time/Retime` (in `line` or `postline` mode) to stretch background fx layers (*glow*, concentric outlines, particle swarms) over the extended duration.

### 4.5. Practical Production Example
* **Continuous Inter-Line Bridge Across Musical Pauses:**
  Extending physical line duration via `Synced` connected to `System/Output`:

  ```
  [Time/Synced: mode=style, fade_dur=300, max_extra=2500] ──► Sync End ──► End Time ──► [System/Output]
  ```

  Inside the ASS override block:
  ```
  {\pos(line.center, line.bottom - 40)\fad(200, 300)}
  ```
  If the subsequent line begins 1200 ms later, `Synced` stretches the current line's end timestamp up to $T_{\text{next, start}} - 300$, allowing the 300 ms fade-out to finish exactly as the incoming line appears on screen.

---

## 5. Node `Time/Middle 1` (Symmetrical Centred Lead-In Offset)

* **Canonical Category:** `Time` (UI: *Time / Middle 1*)
* **Purpose:** Computes a symmetrical, section-based temporal displacement relative to the geometric/sequential centre of the line. Allows entrance animations to converge inward from the extremities towards the centre or radiate outward from the centre to the edges.

![Time/Middle 1](img/middle_1.png)

### 5.1. Input Ports and Body Properties (*Inputs & Properties*)
1. **`Delay (ms)` (`delay_ms`):** Delay multiplier in milliseconds per unit step towards/from the centre. Accepts numeric constants, variables, or expressions (default: `30`).

### 5.2. Output Ports (*Outputs*)
1. **`[1.1] Data`:** Temporal displacement in milliseconds calculated according to the half where the active unit resides.

### 5.3. Mathematical Model of Symmetrical Lead-In
The node bisects the sequence of $n$ units into two halves across the central axis $\frac{n + 1}{2}$. It evaluates the active index $i \in \{1, \dots, n\}$ using a piecewise function:

$$\text{offset} = \begin{cases} 
\Delta_{\text{delay}} \cdot (i - 1) - 200, & \text{if } i \le \frac{n + 1}{2} \\[6pt]
\Delta_{\text{delay}} \cdot (n - i + 0.5) - 200, & \text{if } i > \frac{n + 1}{2}
\end{cases}$$

$$T_{\text{out}} = T_{\text{base}} + \text{offset}$$

Where:
* $i$ is the active sequential index ($1 \le i \le n$).
* $n$ is the total unit count (`syl.n` or `char.n`).
* $\Delta_{\text{delay}}$ is the configured value in `Delay (ms)`.
* $-200\text{ ms}$ is the base kinematic lookahead margin.

#### Symmetrical Evaluation Example ($n=4\text{ units}, \Delta=30\text{ ms}$, Midpoint $= 2.5$):
* Unit $1$ ($i=1 \le 2.5$): $30 \cdot (1 - 1) - 200 = -200.0\text{ ms}$
* Unit $2$ ($i=2 \le 2.5$): $30 \cdot (2 - 1) - 200 = -170.0\text{ ms}$
* Unit $3$ ($i=3 > 2.5$): $30 \cdot (4 - 3 + 0.5) - 200 = 30 \cdot 1.5 - 200 = -155.0\text{ ms}$
* Unit $4$ ($i=4 > 2.5$): $30 \cdot (4 - 4 + 0.5) - 200 = 30 \cdot 0.5 - 200 = -185.0\text{ ms}$

### 5.4. Synergies and Practical Workflow Examples
* **V-Shaped Wave Entrances (*Chevron / Wing In*):** Connect `Data` from `Middle 1` to `Offset In (ms)` on `Time/Retime` (in `syl` or `start2syl` mode). The outer edges of the sentence animate first, converging fluidly towards the centre.

### 5.5. Practical Production Example
* **Convergent Centre-Bound Entrance Wave:**
  Configuration with `Middle 1` feeding `Offset In (ms)` on `Time/Retime`:

  ```
  [Time/Middle 1: delay_ms=35] ──► Data ──► Offset In (ms) ──► [Time/Retime: start2syl, accel=0.8]
                                                                    └──► \t Out ──► Tags ──► [System/Output]
  ```

  With `Tags or \t: \fscx100\fscy100\1c&H00FFFF&` and base styling `{\an5\fscx0\fscy0\1c&HFFFFFF&}`:
  For a line with 6 characters, the outer glyphs ($i=1$ and $i=6$) begin scaling first, followed sequentially by inner letters until converging at the centre pair ($i=3, 4$), achieving a symmetrical chevron reveal.

---

## 6. Node `Time/Middle 2` (Symmetrical Centred Lead-Out Offset)

* **Canonical Category:** `Time` (UI: *Time / Middle 2*)
* **Purpose:** Computes a symmetrical, section-based temporal displacement anchored to the end of the line ($T_{\text{end}}$). Allows fade-outs and exit transitions to coordinate symmetrically to or from the centre of the sentence.

![Time/Middle 2](img/middle_2.png)

### 6.1. Input Ports and Body Properties (*Inputs & Properties*)
1. **`Delay (ms)` (`delay_ms`):** Delay multiplier in milliseconds for symmetrical exit sequencing (default: `30`).

### 6.2. Output Ports (*Outputs*)
1. **`[1.1] Data`:** Temporal displacement in milliseconds relative to the end of the unit or line.

### 6.3. Mathematical Model of Symmetrical Lead-Out
The calculation of `Middle 2` reverses temporal orientation to anchor to the tail of the event:

$$\text{offset} = \begin{cases} 
\Delta_{\text{delay}} \cdot (i - n - 1) - 200, & \text{if } i \ge \frac{n + 1}{2} \\[6pt]
\Delta_{\text{delay}} \cdot (-i + 0.5) - 200, & \text{if } i < \frac{n + 1}{2}
\end{cases}$$

$$T_{\text{out}} = T_{\text{base}} + \text{offset}$$

#### Symmetrical Exit Evaluation Example ($n=4\text{ units}, \Delta=30\text{ ms}$, Midpoint $= 2.5$):
* Unit $1$ ($i=1 < 2.5$): $30 \cdot (-1 + 0.5) - 200 = 30 \cdot (-0.5) - 200 = -215.0\text{ ms}$
* Unit $2$ ($i=2 < 2.5$): $30 \cdot (-2 + 0.5) - 200 = 30 \cdot (-1.5) - 200 = -245.0\text{ ms}$
* Unit $3$ ($i=3 \ge 2.5$): $30 \cdot (3 - 4 - 1) - 200 = 30 \cdot (-2) - 200 = -260.0\text{ ms}$
* Unit $4$ ($i=4 \ge 2.5$): $30 \cdot (4 - 4 - 1) - 200 = 30 \cdot (-1) - 200 = -230.0\text{ ms}$

### 6.4. Synergies and Practical Workflow Examples
* **Mirrored Curtain Exits:** Connect `Data` from `Middle 2` to `Offset Out (ms)` in `Time/Retime` to coordinate dissolving letters or falling particles where central characters vanish before or after the outer flanks.

### 6.5. Practical Production Example
* **Symmetrical Centre-Out Exit Dissolve:**
  Routing `Middle 2` into `Offset Out (ms)` in a `Time/Retime` node set to `postsyl` mode:

  ```
  [Time/Middle 2: delay_ms=40] ──► Data ──► Offset Out (ms) ──► [Time/Retime: postsyl]
                                                                     └──► \t Out ──► Tags ──► [System/Output]
  ```

  With `Tags or \t: \alpha&HFF&`:
  The centre characters finish singing and initiate their fade-out immediately, whereas flank characters remain visible longer on screen, producing a mirrored curtain opening effect.

---

## 7. Node `Time/Loop 1` (Timing Generator for Primary Sub-Loops)

* **Canonical Category:** `Time` (UI: *Time / Loop 1*)
* **Purpose:** Generates stepped or symmetrical temporal offsets for iterations spawned within a primary `Loops/MaxLoop` sub-loop (normal or FBF mode), evaluating the local iteration index $j$ (`fx_i`) against total repetitions $\text{maxj}$ (`fx_n`).

![Time/Loop 1](img/loop_1.png)

### 7.1. Header Mode Combos
1. **`[2.1] Mode` (`mode`):** Determines the kinematic distribution profile across the $j$ sub-loop iterations:

| Mode (`mode`) | Offset Equation ($\text{offset}$) | Kinematic Behaviour |
| :--- | :--- | :--- |
| `leadin` (Default) | $\Delta \cdot (j - 1) - 200$ | **Progressive Cascade:** Each sub-layer $j$ triggers sequentially after the previous one with lead-in anticipation. |
| `leadout` | $\Delta \cdot (j - \text{maxj} - 1) + 200$ | **Stepped Lead-Out:** Sub-layers conclude sequentially following event completion. |
| `middle1` | $\begin{cases} \Delta \cdot (j - 1) - 200, & j \le \frac{\text{maxj}+1}{2} \\ \Delta \cdot (\text{maxj} - j + 0.5) - 200, & j > \frac{\text{maxj}+1}{2} \end{cases}$ | **Symmetrical Lead-In:** Iterated layers converge from the outer loop boundaries towards the centre. |
| `middle2` | $\begin{cases} \Delta \cdot (j - \text{maxj} - 1) - 200, & j \ge \frac{\text{maxj}+1}{2} \\ \Delta \cdot (-j + 0.5) - 200, & j < \frac{\text{maxj}+1}{2} \end{cases}$ | **Symmetrical Lead-Out:** Symmetrical exit centred across the sub-iteration set. |

### 7.2. Input Ports and Body Properties (*Inputs & Properties*)
1. **`Delay (ms)` (`delay_ms`):** Temporal offset step in milliseconds applied between consecutive sub-loop iterations (default: `30`).

### 7.3. Output Ports (*Outputs*)
1. **`[1.1] Data`:** Temporal offset in milliseconds calculated for the active iteration $j$.

### 7.4. Lifecycle and Context Variables
> [!NOTE]
> Unlike `Lead In` or `Middle 1` (which consume the index $i \in [1, n]$ of the syllable/character in the `Main Loop`), `Time/Loop 1` automatically inspects the internal sub-loop context:
> * **$j$ (`fx_i`):** Active repetition index ($1, 2, \dots, \text{maxj}$).
> * **$\text{maxj}$ (`fx_n`):** Total repetition cap configured in `MaxLoop`.

### 7.5. Synergies and Practical Workflow Examples
* **Multi-Layer Ghosting and Echo Trails:** Chain `Loops/Main Loop` $\to$ `Loops/MaxLoop (5 iterations)` $\to$ `Time/Loop 1 (Mode: leadin, Delay: 40ms)` $\to$ `Time/Retime`. Each of the 5 layers renders with progressive temporal displacement, producing motion trails and glowing optical echoes.

### 7.6. Practical Production Example
* **Multi-Layer Echo Trail with MaxLoop and Loop 1:**
  Generating 3 displaced ghost layers trailing behind the main element:

  ```
  [Loops/MaxLoop: count=3] ──► j ──► (Local context j)
                                           │
  [Time/Loop 1: mode=leadin, delay_ms=45] ──► Data ──► Offset In (ms) ──► [Time/Retime: syl]
                                                                              └──► \t Out ──► Tags ──► [System/Output]
  ```

  Combined with layer opacity modulation `{\1a(120 + j * 40)}`:
  Each iteration $j \in \{1, 2, 3\}$ renders with a 45 ms delay relative to the preceding layer, forming a rhythmic kinetic motion blur trail synchronised with singing delivery (evaluating to `\1a&HA0&`, `\1a&HC8&`, and `\1a&HF0&`).

---

## 8. Node `Time/Loop 2` (Timing Generator for Nested Sub-Loops)

* **Canonical Category:** `Time` (UI: *Time / Loop 2*)
* **Purpose:** Identical in kinematic formulations to `Time/Loop 1`, but specifically engineered to operate on **second-level nested sub-loops**, consuming the uppercase iteration variable $J$ against total count $\text{maxJ}$.

![Time/Loop 2](img/loop_2.png)

### 8.1. Header Mode Combos
1. **`[2.1] Mode` (`mode`):** Dropdown selector identical to `Loop 1` (`leadin`, `leadout`, `middle1`, `middle2`).

### 8.2. Input Ports and Body Properties (*Inputs & Properties*)
1. **`Delay (ms)` (`delay_ms`):** Delay step in milliseconds applied between iterations $J$ (default: `30`).

### 8.3. Output Ports (*Outputs*)
1. **`[1.1] Data`:** Temporal offset in milliseconds resulting for the active nested sub-iteration $J$.

### 8.4. Comparative Matrix: Temporal Iteration Scopes

| Timing Node | Index Variable | Total Boundary | Operating Scope / Hierarchy |
| :--- | :---: | :---: | :--- |
| `Lead In` / `Lead Out` / `Middle 1` / `Middle 2` | $i$ (`syl.i`, `char.i`) | $n$ (`syl.n`, `char.n`) | **Master Loop (`Main Loop`):** Iterating across syllables, characters, words, or lines. |
| `Loop 1` | $j$ (`fx_i`) | $\text{maxj}$ (`fx_n`) | **Primary Sub-Loop (`MaxLoop` Level 1):** Multi-layer replicas or FBF frames. |
| `Loop 2` | $J$ | $\text{maxJ}$ | **Nested Sub-Loop (`MaxLoop` Level 2):** Fractal arrays, nested swarms, or compound subsampling. |

### 8.5. Synergies and Practical Workflow Examples
* **Two-Dimensional Loops (Space-Time Matrix):** When constructing particle grids where an outer `MaxLoop (X)` nests an inner `MaxLoop (Y)`, employ `Time/Loop 1` to modulate column delays ($j$) and `Time/Loop 2` to modulate row delays ($J$), adding both outputs in a `Math (add)` node before passing into `Time/Retime`.

### 8.6. Practical Production Example
* **2D Temporal Matrix with Nested Loops (Columns and Rows):**
  Synchronising a particle grid generated across two nested `MaxLoop` nodes:

  ```
  [Loops/MaxLoop X: cols=4] ──► j
       └──► [Loops/MaxLoop Y: rows=3] ──► J
                 │
  [Time/Loop 1: leadin, delay=30] ──► Data ──► In 1 ──► [Basics/Math: add]
  [Time/Loop 2: leadin, delay=60] ──► Data ──► In 2 ─────────┘   │
                                                                 └──► Offset In (ms) ──► [Time/Retime: syl]
  ```

  Summing the delays produces a diagonal wavefront sweep ($30 \cdot (j-1) + 60 \cdot (J-1)$ ms), triggering each cell in 2D space sequentially.

---

## 9. Node `Time/Parse ASS Time` (ASS Timecode Decoder to Milliseconds)

* **Canonical Category:** `Time` (UI: *Time / Parse ASS Time*)
* **Purpose:** Parses and converts standard ASS subtitle timestamps (`H:MM:SS.CS` or `H:MM:SS.MMM`) into a scalar numeric integer representing milliseconds.

![Time/Parse ASS Time](img/parse_ass_time.png)

### 9.1. Input Ports and Body Properties (*Inputs & Properties*)
1. **`ASS Time` (`ass_time`):** String containing the timestamp to parse (e.g. `"0:01:23.45"` or `"1:12:05.120"`). If unlinked and left blank, the node automatically extracts the start timecode of the active context unit (`unit.start_str` $\to$ `line.start_str`) (default: `"0:00:00.00"`).

### 9.2. Output Ports (*Outputs*)
1. **`[1.1] Time (ms)`:** Integer numerical value representing total accumulated milliseconds.

### 9.3. Mathematical Model of Timestamp Decoding
Given a timestamp structured with $\text{Hours } H$, $\text{Minutes } M$, $\text{Seconds } S$, and $\text{Centiseconds } CS$:

$$T_{\text{ms}} = (3600 \cdot H + 60 \cdot M + S) \cdot 1000 + CS \cdot 10$$

#### Conversion Example:
$$\text{"0:01:23.45"} \implies (0 + 60 + 23) \cdot 1000 + 45 \cdot 10 = 83000 + 450 = 83450\text{ ms}$$

### 9.4. Synergies and Practical Workflow Examples
* **Direct Timecode Arithmetic:** Enables decoding raw dialogue header timestamps to perform calculations with `Basics/Math` or `Time/Offset` before re-encoding via `Time/Format ASS Time` or injecting into `System/Output`.

### 9.5. Practical Production Example
* **Timestamp Decoding and Algebraic Shift:**
  Parsing a static timecode to advance it algebraically by 500 ms:

  ```
  [Time/Parse ASS Time: ass_time="0:01:15.50"] ──► Time (ms) ──► In 1 ──► [Basics/Math: add, in2=500]
                                                                                └──► In 1 ──► [Time/Format ASS Time]
                                                                                                    └──► ASS Time ──► "0:01:16.00"
  ```
  The decoded value (75500 ms) increments to 76000 ms and is re-encoded into standard ASS format with zero precision loss.

---

## 10. Node `Time/Format ASS Time` (Milliseconds to ASS Timecode Encoder)

* **Canonical Category:** `Time` (UI: *Time / Format ASS Time*)
* **Purpose:** Converts a scalar numeric millisecond value into the formal timestamp string required by the ASS standard (`H:MM:SS.CS`).

![Time/Format ASS Time](img/format_ass_time.png)

### 10.1. Input Ports and Body Properties (*Inputs & Properties*)
1. **`Time (ms)` (`time`):** Numeric value in milliseconds (integer, float, or evaluable mathematical expression). If unlinked and empty, adopts the start timestamp of the active syllable or line (`unit.start_time` $\to$ `line.start_time`) (default: `"0"`).

### 10.2. Output Ports (*Outputs*)
1. **`[1.1] ASS Time`:** Zero-padded text string conforming to standard Aegisub / libass syntax: `H:MM:SS.CS` (with 2-digit centiseconds).

### 10.3. Mathematical Model of Timestamp Encoding
From total milliseconds $T_{\text{ms}}$:

$$H = \left\lfloor \frac{T_{\text{ms}}}{3600000} \right\rfloor$$
$$M = \left\lfloor \frac{T_{\text{ms}} \bmod 3600000}{60000} \right\rfloor$$
$$S = \left\lfloor \frac{T_{\text{ms}} \bmod 60000}{1000} \right\rfloor$$
$$CS = \left\lfloor \frac{T_{\text{ms}} \bmod 1000}{10} \right\rfloor$$

$$\text{ASS Time} = H : \text{pad}_2(M) : \text{pad}_2(S) . \text{pad}_2(CS)$$

Where $\text{pad}_2(x)$ prepends a leading zero if $x < 10$.

### 10.4. Synergies and Practical Workflow Examples
* **Dynamic Event Generation:** Connect the `ASS Time` output to custom event builders in `Script Code` or dialogue string generators when exporting multi-track `.ass` files decoupled from standard output streams.

### 10.5. Practical Production Example
* **Formatting Computed Durations for Dialogue Overrides:**
  Converting a computed delayed timestamp into an ASS timecode string:

  ```
  [Time/Offset: base=line.start_time, offset_ms=1200] ──► Time (ms) ──► Time (ms) ──► [Time/Format ASS Time]
                                                                                              └──► ASS Time
  ```
  If `line.start_time` is 10000 ms, `Offset` yields 11200 ms and `Format ASS Time` outputs `"0:00:11.20"`.

---

## 11. Node `Time/Time to Frame` (Time to Frame Number Conversion)

* **Canonical Category:** `Time` (UI: *Time / Time to Frame*)
* **Purpose:** Calculates the discrete video frame count or frame index ($f$) corresponding to a millisecond timestamp or duration, based on the project's frames-per-second (*FPS*) rate.

![Time/Time to Frame](img/time_to_frame.png)

### 11.1. Header Mode Combos
1. **`[2.1] Mode` (`mode`):** Mathematical discretisation method for frame rounding:
   * `round` (Default): Nearest-frame rounding ($\lfloor x + 0.5 \rfloor$).
   * `floor`: Truncation down ($\lfloor x \rfloor$), ideal for 0-indexed timeline frame indices.
   * `ceil`: Rounding up ($\lceil x \rceil$), ideal for calculating the total frame span of a non-zero duration.
2. **`[2.2] Source` (`source`):** Origin of the timestamp to convert:
   * `custom` (Default): Consumes the value provided in the `Time (ms)` port or inline property.
   * `start`: Automatically extracts the start timestamp of the active context unit (`unit.start_time` $\to$ `line.start_time`).
   * `end`: Automatically extracts the end timestamp (`unit.end_time` $\to$ `line.end_time`).
   * `dur`: Automatically extracts the net duration (`unit.duration` $\to$ `line.duration`).

### 11.2. Input Ports and Body Properties (*Inputs & Properties*)
1. **`Time (ms)` (`time`):** Time in milliseconds to convert. Accepts direct numbers, ASS timestamps `H:MM:SS.CS`, or context variables.
2. **`Frame Dur (ms)` (`frame_dur`):** Single-frame duration in milliseconds. If unlinked or empty, retrieves the global video context from Aegisub (default $41.708\text{ ms}$, corresponding to $23.976\text{ fps}$).

### 11.3. Output Ports (*Outputs*)
1. **`[1.1] Frames (f)`:** Resulting integer frame count.

### 11.4. Mathematical Model of Frame Discretisation
Given frame duration $fd = \frac{1000}{\text{FPS}}$ and resolved time $T$:

$$f_{\text{ceil}} = \left\lceil \frac{T}{fd} \right\rceil, \quad f_{\text{floor}} = \left\lfloor \frac{T}{fd} \right\rfloor, \quad f_{\text{round}} = \left\lfloor \frac{T}{fd} + 0.5 \right\rfloor$$

#### Frame Duration Equivalences by FPS:
| Frame Rate (FPS) | Frame Duration ($fd$) | Frames for $1000\text{ ms}$ (Ceil) |
| :---: | :---: | :---: |
| **$23.976\text{ fps}$** | $\approx 41.7083\text{ ms}$ | $24\text{ frames}$ |
| **$24.000\text{ fps}$** | $\approx 41.6667\text{ ms}$ | $24\text{ frames}$ |
| **$29.970\text{ fps}$** | $\approx 33.3667\text{ ms}$ | $30\text{ frames}$ |
| **$30.000\text{ fps}$** | $\approx 33.3333\text{ ms}$ | $30\text{ frames}$ |
| **$60.000\text{ fps}$** | $\approx 16.6667\text{ ms}$ | $60\text{ frames}$ |

### 11.5. Synergies and Practical Workflow Examples
* **Feeding FBF Loops:** Connect `Time to Frame` (in `Source: dur` and `Mode: ceil`) to the `Total` port or repetitions property of `Loops/MaxLoop (fbf)` to ensure the loop iterates for the exact number of actual video frames spanning the syllable.

### 11.6. Practical Production Example
* **Precise Iteration Count for FBF Loops:**
  Calculating the exact frame count spanning the active syllable at 23.976 fps:

  ```
  [Time/Time to Frame: source=dur, mode=ceil] ──► Frames (f) ──► Count / Reps ──► [Loops/MaxLoop: fbf]
  ```
  For a 450 ms syllable with $fd \approx 41.708$ ms:
  $$\left\lceil \frac{450}{41.708} \right\rceil = \lceil 10.789 \rceil = 11\text{ frames}$$
  `MaxLoop` iterates exactly 11 times, ensuring full temporal coverage without dropped or surplus frames.

---

## 12. Node `Time/Frame to Time` (Frame to Time and Format Conversion)

* **Canonical Category:** `Time` (UI: *Time / Frame to Time*)
* **Purpose:** Multiplies a video frame number or loop counter ($f$, $j$, $J$, $i$) by the frame duration to yield its temporal equivalent in milliseconds, ASS timecodes, or seconds.

![Time/Frame to Time](img/frame_to_time.png)

### 12.1. Header Mode Combos
1. **`[2.1] Format` (`format`):** Primary output format on `[1.1] Time`:
   * `ms` (Default): Numeric milliseconds rounded to two decimal places (e.g. `2000.0`).
   * `hms`: Formatted string in ASS timecode syntax (e.g. `"0:00:02.00"`).
   * `sec`: Floating-point seconds with three decimal places (e.g. `2.000`).
2. **`[2.2] Source` (`source`):** Origin of the frame index or variable to evaluate:
   * `custom` (Default): Consumes the value entered in the `Frames (f)` port or inline property `frames`.
   * `iterator`: Reads a custom iteration variable specified in `iter_name` (e.g. `k`, `step_i`, or expressions like `k * 2`).
   * `j`: Automatically extracts the active sub-loop counter `j` (`fx_i`).
   * `J`: Automatically extracts the active nested sub-loop counter `J`.
   * `i`: Automatically extracts the unit sequential index `unit.i`.

### 12.2. Input Ports and Body Properties (*Inputs & Properties*)
1. **`Frames (f)` (`frames`):** Frame count or index (used when `Source` is `custom`) (default: `1`).
2. **`Frame Dur (ms)` (`frame_dur`):** Frame duration in milliseconds ($fd$). If omitted, inferred from the video environment ($41.708\text{ ms}$).

### 12.3. Output Ports (*Outputs*)
1. **`[1.1] Time`:** Converted time according to the format selected in `Format` (`ms`, `hms`, or `sec`).
2. **`[1.2] ASS Time`:** **Always** emits the timecode formatted in ASS standard (`0:00:00.00`), regardless of the header format selection.

### 12.4. Mathematical Model of Frame Projection
Given resolved frame number $f$ and frame duration $fd$:

$$T_{\text{ms}} = f \cdot fd$$

* If `Format` is `ms`: $T_{\text{out}} = \text{round}(T_{\text{ms}}, 2)$
* If `Format` is `sec`: $T_{\text{out}} = \text{round}\left(\frac{T_{\text{ms}}}{1000}, 3\right)$
* If `Format` is `hms`: $T_{\text{out}} = \text{format\_time}(T_{\text{ms}})$

### 12.5. Synergies and Practical Workflow Examples
* **Frame-by-Frame (FBF) Synchronisation:** Inside a `Loops/MaxLoop (fbf)` loop, use `Frame to Time` with `Source: j` to calculate elapsed relative time on each exact frame. This output can directly feed the `Base (ms)` input of `Time/Offset` or interpolation progress $t$ in Bézier curves and vector deformations.

### 12.6. Practical Production Example
* **Continuous Temporal Projection in an FBF Loop:**
  Calculating the exact elapsed time for each frame $j$ in an FBF animation:

  ```
  [Loops/MaxLoop: fbf] ──► Context j
                                │
  [Time/Frame to Time: source=j, format=ms] ──► Time ──► Base (ms) ──► [Time/Offset: offset_ms=syl.start_time]
                                                                             └──► Time (ms) ──► Start Time ──► [System/Output]
  ```
  Each generated FBF line receives its exact absolute video start timestamp ($T = T_{\text{syl\_start}} + j \cdot fd$), locking animations frame-accurately in Aegisub.

---

## 13. Node `Time/Ipol` (Non-Linear Temporal Segmenter and Easing)

* **Canonical Category:** `Time` (UI: *Time / Ipol*)
* **Purpose:** Divides a total duration ($D_{\text{ms}}$) into an ordered sequence of normalised sub-intervals $[t_0, t_1], [t_1, t_2], \dots$, applying exponential acceleration curves (`accel`) across an arbitrary list of keyframes or intermediate control points.

![Time/Ipol](img/ipol.png)

### 13.1. Input Ports and Body Properties (*Inputs & Properties*)
1. **`Duration (ms)` (`dur_ms`):** Total interval duration to subdivide in milliseconds. If empty or unlinked, automatically adopts the active unit duration (`unit.duration` $\to 1000\text{ ms}$) (default: `"syl.duration"`).
2. **`Points / Values` (`points`):** Comma-separated list of scalar values defining stage milestones or keyframes (e.g. `"0, 100"` for $1$ segment; `"0, 50, 100"` for $2$ segments; `"0, 20, 80, 100"` for $3$ segments) (default: `"0, 100"`).
3. **`Acceleration` (`accel`):** Non-linear curvature exponent. Accepts decimal values greater than zero (default: `1.0`):
   * $\text{accel} = 1.0$: Strictly linear interpolation (equally spaced stages).
   * $\text{accel} > 1.0$: *Ease-In* curve (slow departure with progressive acceleration towards the end).
   * $\text{accel} < 1.0$: *Ease-Out* curve (fast departure with progressive deceleration).

### 13.2. Output Ports (*Outputs*)
1. **`[1.1] Data`:** Formatted string containing calculated bracketed sub-intervals, separated by commas (e.g. `"[0.0, 500.0], [500.0, 1000.0]"`).

### 13.3. Mathematical Model of Temporal Segmentation
Given a list of $M$ control points $\{p_0, p_1, \dots, p_M\}$, the resulting number of temporal segments is $K = M - 1$.

For each boundary index $k \in \{1, \dots, K\}$, the normalised fraction $u_k$ is computed:

$$u_k = \frac{k}{K}, \quad u_k \in (0.0, 1.0]$$

The accumulated timestamp $t_k$ corresponding to the end of segment $k$ is evaluated using the acceleration power:

$$t_k = D_{\text{ms}} \cdot (u_k)^{\text{accel}}$$

The generated sub-intervals correspond to:

$$I_k = [t_{k-1}, t_k] \quad \text{with } t_0 = 0.0\text{ ms}$$

```
t=0 ms                                                  t=D ms
├─────────────────────────┼───────────────────────────────────┤
   Interval 1: [t_0, t_1]        Interval 2: [t_1, t_2]
```

#### Segmentation Examples ($D = 1000\text{ ms}$, Points $= \text{"0, 50, 100"}$, $K=2$ segments):
* **Linear ($\text{accel} = 1.0$):**
  * $k=1 \implies u_1 = 0.5 \implies t_1 = 1000 \cdot (0.5)^1 = 500.0\text{ ms} \implies [0.0, 500.0]$
  * $k=2 \implies u_2 = 1.0 \implies t_2 = 1000 \cdot (1.0)^1 = 1000.0\text{ ms} \implies [500.0, 1000.0]$
  * **Output `Data`:** `"[0.0, 500.0], [500.0, 1000.0]"`
* **Quadratic Ease-In ($\text{accel} = 2.0$):**
  * $k=1 \implies u_1 = 0.5 \implies t_1 = 1000 \cdot (0.5)^2 = 250.0\text{ ms} \implies [0.0, 250.0]$
  * $k=2 \implies u_2 = 1.0 \implies t_2 = 1000 \cdot (1.0)^2 = 1000.0\text{ ms} \implies [250.0, 1000.0]$
  * **Output `Data`:** `"[0.0, 250.0], [250.0, 1000.0]"`

### 13.4. Synergies and Practical Workflow Examples
* **Multi-Stage Animations:** Route `Data` from `Ipol` into animation scripting or multi-phase `\t` transformation builders to split a syllable's singing window into coordinated sub-stages (e.g. an initial rapid scale burst followed by a smooth settling return).

### 13.5. Practical Production Example
* **Two-Phase Impact and Settle Animation:**
  Subdividing a 600 ms syllable into two stages with non-linear easing (`points="0, 30, 100"`, `accel=1.5`):

  ```
  [Time/Ipol: dur_ms=600, points="0, 30, 100", accel=1.5] ──► Data
  ```
  The node outputs sub-intervals: `[0.0, 98.6], [98.6, 600.0]`.
  In the ASS override block:
  ```
  {\t(0, 99, \fscx140\fscy140)\t(99, 600, 0.8, \fscx100\fscy100)}
  ```
  The glyph surges quickly to 140% over the first 99 ms (impact phase) and relaxes back to 100% across the remaining 501 ms with a smooth decelerating easing curve.

---

## 14. Node `Time/Duration` (Net Duration Calculation)

* **Canonical Category:** `Time` (UI: *Time / Duration*)
* **Purpose:** Calculates the net scalar duration in milliseconds between two timestamps ($T_{\text{start}}$ and $T_{\text{end}}$), or returns the active context unit duration if inputs remain unwired.

![Time/Duration](img/duration.png)

### 14.1. Input Ports and Body Properties (*Inputs & Properties*)
1. **`Start Time (ms)` (`start_time`):** Start timestamp in milliseconds or context variable (e.g. `line.start_time`, `syl.start_time`) (default: `"line.start_time"`).
2. **`End Time (ms)` (`end_time`):** End timestamp in milliseconds or context variable (e.g. `line.end_time`, `syl.end_time`) (default: `"line.end_time"`).

### 14.2. Output Ports (*Outputs*)
1. **`[1.1] Duration (ms)`:** Integer scalar value representing the non-negative difference between both timestamps.

### 14.3. Mathematical Model of Net Duration
Given timestamps $T_{\text{start}}$ and $T_{\text{end}}$ evaluated dynamically in context:

$$D = \max\left(0, \text{round}(T_{\text{end}} - T_{\text{start}})\right)$$

#### Automatic Contextual Fallback:
If both inputs and inline fields are empty or unassigned, the node traverses the context hierarchy to extract the intrinsic duration of the active element:

$$D = \text{unit.duration} \implies \text{syl.duration} \implies \text{line.duration} \implies 0\text{ ms}$$

### 14.4. Synergies and Practical Workflow Examples
* **Custom Interval Measurement:** Connect the `Start Time` and `End Time` outputs of `Time/Retime` into `Time/Duration` to compute the exact duration of a retimed phase (including offsets) prior to mapping it into Bézier curves or proportional scales.

### 14.5. Practical Production Example
* **Rotation Speed Modulation by Phonetic Duration:**
  Routing `Start Time` and `End Time` from a syllable into `Time/Duration`:

  ```
  [Time/Retime: syl] ──┬──► Start Time ──► Start Time (ms) ──► [Time/Duration]
                       └──► End Time   ──► End Time (ms)   ───────┘   │
                                                                      └──► Duration (ms) ──► In 1 ──► [Basics/Math: div, in2=100]
                                                                                                             └──► Rot Speed
  ```

  If a rapid syllable lasts 200 ms, the resulting speed generates brisk `\frz` angular spins; for a sustained vowel (1200 ms), the rotation smoothly elongates to span the full interval without harsh acceleration.

---

## 15. Node `Time/Offset` (Additive and Subtractive Temporal Offset)

* **Canonical Category:** `Time` (UI: *Time / Offset*)
* **Purpose:** Applies an additive or subtractive temporal shift in milliseconds to a base timestamp, allowing advances (negative values) or delays (positive values).

![Time/Offset](img/offset.png)

### 15.1. Input Ports and Body Properties (*Inputs & Properties*)
1. **`Base (ms)` (`time_in` / `base`):** Base reference timestamp in milliseconds. If unwired, automatically extracts the start time of the active context unit (`unit.start_time` $\to$ `line.start_time` $\to 0$).
2. **`Offset (ms)` (`offset_ms` / `offset`):** Milliseconds to add or subtract from the base. Accepts positive numbers, negative numbers, or evaluable expressions (default: `"100"`).

### 15.2. Output Ports (*Outputs*)
1. **`[1.1] Time (ms)`:** Resulting timestamp after applying the temporal offset.

### 15.3. Mathematical Model of Temporal Offset
$$T_{\text{out}} = \text{round}(T_{\text{base}} + \Delta_{\text{offset}})$$

#### Examples:
* **Positive Delay:** $T_{\text{base}} = 1000\text{ ms}, \Delta_{\text{offset}} = 250\text{ ms} \implies T_{\text{out}} = 1250\text{ ms}$
* **Negative Advance:** $T_{\text{base}} = 1000\text{ ms}, \Delta_{\text{offset}} = -150\text{ ms} \implies T_{\text{out}} = 850\text{ ms}$

### 15.4. Synergies and Practical Workflow Examples
* **Dynamic Window Shifting:** Connect to the `End Time` output of `Time/Retime` with `Offset: 200` to extend the on-screen presence of a line before passing it to `System/Output`.
* **Animation Trigger Milestones:** Generate intermediate timestamps to synchronise sparkle bursts from `Functions/Glitter` or particle emissions just before or after a sung syllable starts.

### 15.5. Practical Production Example
* **Silhouette Screen-Sustain Extension:**
  Extending the visibility of a background drop-shadow or border outline after the dialogue line ends:

  ```
  [Time/Retime: line] ──► End Time ──► Base (ms) ──► [Time/Offset: offset_ms=250]
                                                             └──► Time (ms) ──► End Time ──► [System/Output]
  ```

  Inside the ASS override block:
  ```
  {\pos(line.center, line.middle)\bord5\3c&H000000&\t(line.duration, line.duration + 250, \alpha&HFF&)}
  ```
  The outline remains visible 250 ms after the main foreground type extinguishes, fading out cleanly towards black.
