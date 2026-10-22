# Basics

The **Basics** category gathers nodes dedicated to primitive data generation, transformation, formatting, and routing (numbers, strings, colours, mathematical expressions, and conditionals) for building ASS subtitle effects.

---

## 1. Node `Basics/Number` (Numeric Constant and Expressions)

* **Canonical Category:** `Basics` (UI: *Basics / Number*)
* **Purpose:** Emits a scalar numerical value (integer or floating-point), evaluating constants, ASS context variables, and algebraic expressions in real time.

![Basics/Number](img/number.png)

### 1.1. Output Ports (*Outputs*)
1. **`[1.1] Number`:** Emits the evaluated numerical value as a formatted text string. If the result is an exact integer, it is formatted without decimal places (e.g. `10`); if fractional, it is rounded to a maximum of 4 significant decimal places with trailing redundant zeroes stripped (e.g. `12.5`).

### 1.2. Controls and Body Properties
1. **`[2.1] Value` (`value`):** Editable input field. Accepts direct numbers (`100`, `-45.2`), ASS context variables (`syl.x`, `line.width`, `j`, `i`, `char.n`), or algebraic expressions (`syl.width / 2 + 10`, `sin(j * 0.1) * 50`).

### 1.3. Dynamic Evaluation of Expressions
The `value` field is processed dynamically on every execution iteration cycle:
* If the input string contains identifiers registered in the active context (`syl`, `line`, `char`, `video_fps`, etc.), the evaluator substitutes their numerical values prior to calculation.
* Supports both decimal points (`12.5`) and decimal commas (`12,5`), normalising them automatically.

### 1.4. Synergies and Best Practices
* **Parametric Control of ASS Tags:** Connect the `Number` output to `Basics/MultiTag` inputs or template placeholders in `Basics/Dynamic Format` to modulate numeric tags such as `\fscx<val>`, `\fscy<val>`, `\blur<val>`, or position coordinates `\pos(syl.center, <val>)`.
* **Relative Timing Calculations:** Feed timing ports (`Start Time`, `End Time`) with direct expressions relative to the context (e.g. `syl.start_time - 150`, `line.duration + 200`).

---

## 2. Node `Basics/String` (Literal Text String)

* **Canonical Category:** `Basics` (UI: *Basics / String*)
* **Purpose:** Emits a fixed text string or one containing context macros to inject dialogue lines, style names, drawing commands, or ASS escape sequences.

![Basics/String](img/string.png)

### 2.1. Output Ports (*Outputs*)
1. **`[1.1] String`:** Emits the text string configured in the node body.

### 2.2. Controls and Body Properties
1. **`[2.1] Text` (`value`):** Editable string field. Supports plain text, ASS line break and spacing escape sequences (`\N`, `\h`), tag blocks (`{\an5\bord0\shad0}`), or vector drawing paths (`m 0 0 l 100 0 100 100 0 100`). If the text contains blocks enclosed in braces `{\...}`, Pyxis string evaluator directly resolves expressions and context variables within the tag parentheses (e.g. `{\pos(syl.center, syl.middle)}` or `\fscx(100 + 20 * i)`) while preserving surrounding literal text.

### 2.3. Synergies and Best Practices
* **Static Header Injection:** Connect `String` to `Basics/Concatenate` or `Output (Tags)` nodes to prepend static formatting combinations (e.g. `{\an5\bord1\blur1.5}`).
* **Drawing Path Isolation:** Centralise vector code into a `String` node wired to the `Draw Code` input of `Shape/Slicer` or `Shape/Transform` to prevent path duplication across the graph.

---

## 3. Node `Basics/Text` (String Manipulation and Processing)

* **Canonical Category:** `Basics` (UI: *Basics / Text*)
* **Purpose:** Applies text transformations, ASS tag sanitisation, Japanese phonetic transliteration, and syllabic metric partitioning over arbitrary strings or active context units.

![Basics/Text](img/text.png)

### 3.1. Input Ports (*Inputs*)
1. **`Text`:** Input string to be processed. If disconnected, the node automatically retrieves the text of the active context unit in priority order: `active_unit.text_stripped` $\to$ `syl.text` $\to$ `char.text` $\to$ `line.text`.

### 3.2. Output Ports (*Outputs*)
1. **`[1.1] Out`:** Resulting text string after executing the selected operation.

### 3.3. Operation Selector (`operation`)
The node provides 10 string manipulation operations:

| Operation (`operation`) | Technical Description | Behaviour & Auxiliary Parameters |
| :--- | :--- | :--- |
| `strip_tags` | ASS tag removal | Removes all `{\...}` control blocks, converts `\N`, `\n`, and `\h` hard spaces into standard spaces, and trims outer whitespace. |
| `uppercase` | Uppercase conversion | Converts the entire string to uppercase characters (`str.upper()`). |
| `lowercase` | Lowercase conversion | Converts the entire string to lowercase characters (`str.lower()`). |
| `clean_spaces` | Spacing normalisation | Replaces contiguous sequences of spaces and tabs with a single space (`[ \t]+` $\to$ `" "`). |
| `replace` | Substring replacement | Replaces all occurrences of the substring in `Search` with `Replace With`. |
| `substring` | Positional extraction | Extracts a substring starting from index `Start` with an extent of `Length` characters (0-based index). |
| `length` | String length | Counts the total character count and returns the integer value formatted as a string. |
| `contains` | Substring presence check | Emits `"1"` if the string contains the substring specified in `Search`, or `"0"` otherwise. |
| `kana` | Japanese transliteration | Converts phonetic text between Romaji, Hiragana, and Katakana via an equivalence table, resolving digraphs and geminate consonants with sokuon (`っ` / `ッ`). |
| `romaji_to_karaoke` | Automatic syllabic segmentation | Splits Romaji words into valid phonetic syllables and generates timed ASS karaoke tags (`\k<dur>`, `\kf<dur>`, `\ko<dur>`), distributing line duration uniformly across syllables. |

### 3.4. Algorithmic Behaviour of Special Modes

#### 3.4.1. Kana Transliteration (`kana`)
The engine processes text sequences by sorting phonetic patterns in descending order of length to give precedence to trigraphs and digraphs (`kya`, `tsu`, `chi`, `sha`) over single vowels or consonants (`ka`, `ta`, `sa`, `a`). Available modes in `Mode`:
* `Romaji to Hiragana`: Converts Latin-script text to Hiragana (e.g. `"sakura"` $\to$ `"さくら"`, `"gakkou"` $\to$ `"がっこう"`).
* `Romaji to Katakana`: Converts Latin-script text to Katakana (e.g. `"karaoke"` $\to$ `"カラオケ"`).
* `Hiragana to Katakana`: Converts Hiragana glyphs into their Katakana counterparts.
* `Katakana to Hiragana`: Converts Katakana glyphs into Hiragana.
* `Kana to Romaji`: Decodes Hiragana or Katakana characters into standard phonetic Romaji.

#### 3.4.2. Romaji to Karaoke Generator (`romaji_to_karaoke`)
Segments the input string into words and identifies the syllabic units of romanised Japanese. For a line with total duration in centiseconds $T$ and $N$ detected syllables:
$$\text{Duration per syllable } d_i = \left\lfloor \frac{T}{N} \right\rfloor + (1 \text{ if } i < (T \bmod N))$$

Injects the tag configured in `K Mode` (`\k`, `\kf`, `\ko`, `\K`) with its value in centiseconds before each emitted syllable (e.g. `{\k15}sa{\k20}ku{\k15}ra`).

### 3.5. Synergies and Best Practices
* **Sanitisation Prior to Vectorisation:** Connect `strip_tags` to the `Text` input of `Basics/Text to Shape` to ensure the vector engine receives clean glyphs without interpolated ASS control codes.
* **Conditional Text Branching:** Use the `contains` operation wired into `Basics/Only` to branch style paths based on keywords found in dialogue text.

---

## 4. Node `Basics/Color Picker` (Colour Selector and Palettes)

* **Canonical Category:** `Basics` (UI: *Basics / Color Picker*)
* **Purpose:** Colour picker and palette manager with an interactive visual interface and direct conversion between ASS BGR (`&HBBGGRR&`) and Web Hexadecimal (`#RRGGBB`) formats.

![Basics/Color Picker](img/color_picker.png)

### 4.1. Output Ports (*Outputs*)
1. **`[1.1] Color List`:** Emits the full list of colours in the active palette as a comma-delimited string, respecting the output format configured on each swatch (e.g. `"&H5500FF&, &HFF9900&, #FFFFFF"`).
2. **`[1.2] ASS Color`:** Emits the primary swatch colour (Slot 0) formatted strictly in ASS BGR syntax `&HBBGGRR&`.

### 4.2. Interactive Controls and Palette Swatches
* **Swatch Editing:** Clicking any colour swatch opens the colour picker with sliders, real-time preview, and output format selector.
* **Palette Management:** Allows adding new swatches and independently defining whether each swatch exports in `ASS` or `HEX` format.

### 4.3. Colour Models and BGR Conversion
Pyxis internally converts between standard RGB channel ordering and the native BGR encoding used by Aegisub and libass:

$$\text{RGB: } (R, G, B) \implies \text{ASS Colour: } \&\text{H}B_{\text{hex}}G_{\text{hex}}R_{\text{hex}}\&$$

* **ASS Format (`ASS`):** Inverts Red and Blue channels to match libass syntax. For example:
  * Pure Red ($R=255, G=0, B=0$) $\implies$ `&H0000FF&`
  * Pure Blue ($R=0, G=0, B=255$) $\implies$ `&HFF0000&`
  * Pure Yellow ($R=255, G=255, B=0$) $\implies$ `&H00FFFF&`
* **Hex Format (`HEX`):** Retains standard `#RRGGBB` web format for interoperability with external tools.

### 4.4. Synergies and Best Practices
* **Direct Tag Colour Assignment:** Connect the `ASS Color` output to primary (`\1c`) or border (`\3c`) colour inputs on `Basics/MultiTag` nodes.
* **Feeding Gradients and Borders:** Connect `Color List` directly to the matching port in `Functions/Color Gradient` or `Shape/Concentric Borders` to produce consistent polychromatic transitions.

---

## 5. Node `Basics/Math` (Mathematical Engine and Curves)

* **Canonical Category:** `Basics` (UI: *Basics / Math*)
* **Purpose:** Evaluates arithmetic, trigonometric, acceleration curve (*easing*), periodic oscillation, and range utility operations structured across 8 calculation families.

![Basics/Math](img/math.png)

### 5.1. Header Mode Combos
1. **`[2.1] Category` (`category`):** Dropdown selector for the mathematical family:
   * `basic`: Elementary arithmetic and algebra.
   * `trig`: Direct and inverse trigonometry, plus angular conversions.
   * `rounding`: Nearest integer rounding, floor, and ceiling.
   * `clamping`: Strict range bounding and boundary comparisons.
   * `easing`: Normalised acceleration and deceleration curves ($t \in [0.0, 1.0]$).
   * `waves`: Continuous periodic waveform oscillators.
   * `random`: Pseudo-random generation with deterministic seed support.
   * `utilities`: Linear range re-mapping and scalar interpolation.
2. **`[2.2] Operation` (`operation`):** Specific calculation function to execute within the selected family.

### 5.2. Input Ports (*Inputs*)
1. **`A`:** Primary operand, progress factor $t$, angle, or base value. If disconnected, uses the numerical value configured in the internal property.
2. **`B`:** Secondary operand, upper bound, frequency, or destination target.

### 5.3. Output Ports (*Outputs*)
1. **`[1.1] Out`:** Resulting scalar numerical value. If the calculation yields an exact integer, it is formatted without decimal places (e.g. `25`); if fractional, it outputs up to 4 significant decimal places (e.g. `0.7071`).

### 5.4. Breakdown of the 8 Mathematical Families

#### 5.4.1. `basic` Family (Arithmetic)
* **`add` ($A + B$):** Algebraic addition.
* **`sub` ($A - B$):** Arithmetic subtraction.
* **`mul` ($A \cdot B$):** Multiplication.
* **`div` ($A / B$):** Protected division (returns `0.0` if $B = 0$).
* **`mod` ($A \pmod B$):** Integer modulo remainder (returns `0.0` if $B = 0$).
* **`pow` ($A^B$):** Power exponentiation.
* **`abs` ($|A|$):** Absolute value.
* **`neg` ($-A$):** Arithmetic sign negation.

#### 5.4.2. `trig` Family (Trigonometry)
Direct trigonometric functions (`sin`, `cos`, `tan`) expect angle $A$ in **sexagesimal degrees** ($0^\circ \dots 360^\circ$) to match the rotation convention of ASS subtitle tags (`\frz`, `\frx`, `\fry`). Inverse functions return results directly in degrees.

* **`sin`:** $\sin\left(\frac{A \cdot \pi}{180}\right)$
* **`cos`:** $\cos\left(\frac{A \cdot \pi}{180}\right)$
* **`tan`:** $\tan\left(\frac{A \cdot \pi}{180}\right)$
* **`asin` / `arcsin`:** $\arcsin(\text{clamp}(A, -1, 1)) \cdot \frac{180}{\pi} \in [-90^\circ, 90^\circ]$
* **`acos` / `arccos`:** $\arccos(\text{clamp}(A, -1, 1)) \cdot \frac{180}{\pi} \in [0^\circ, 180^\circ]$
* **`atan` / `arctan`:** $\arctan(A) \cdot \frac{180}{\pi} \in (-90^\circ, 90^\circ)$
* **`atan2`:** $\text{atan2}(Y, X) \cdot \frac{180}{\pi}$ where $Y = A$ and $X = B$, in range $[-180^\circ, 180^\circ]$
* **`rad` / `radians`:** Converts degrees to radians: $A \cdot \frac{\pi}{180}$.
* **`deg` / `degrees`:** Converts radians to degrees: $A \cdot \frac{180}{\pi}$.

#### 5.4.3. `rounding` Family (Rounding)
* **`round`:** Rounds $A$ to the nearest integer.
* **`floor`:** Largest integer less than or equal ($\lfloor A \rfloor$).
* **`ceil`:** Smallest integer greater than or equal ($\lceil A \rceil$).

#### 5.4.4. `easing` Family (Progression Curves)
Accepts a normalised progress factor $t = \text{clamp}(A, 0.0, 1.0)$ and outputs the transformed value within $[0.0, 1.0]$:

* **`ease_in`:** Initial quadratic acceleration: $f(t) = t^2$.
* **`ease_out`:** Terminal quadratic deceleration: $f(t) = 1 - (1 - t)^2$.
* **`ease_in_out`:** Combined acceleration and deceleration:
  $$f(t) = \begin{cases} 2t^2 & \text{if } t < 0.5 \\ 1 - \frac{(-2t + 2)^2}{2} & \text{if } t \ge 0.5 \end{cases}$$
* **`cubic_in`:** Cubic acceleration: $f(t) = t^3$.
* **`cubic_out`:** Cubic deceleration: $f(t) = 1 - (1 - t)^3$.
* **`expo`:** Exponential progression: $f(t) = 2^{10(t - 1)}$ for $t > 0$.
* **`elastic`:** Damped elastic oscillation.
* **`bounce`:** Multi-impact ballistic bounce.
* **`back`:** Anticipation overshoot: $f(t) = (c_1 + 1)t^3 - c_1 t^2$ where $c_1 = 1.70158$.

#### 5.4.5. `waves` Family (Periodic Oscillators)
Generates continuous temporal oscillations driven by $t = A$, frequency $f = \text{freq}$, amplitude $A_{\text{amp}} = \text{amp}$, and constant offset $\text{Offset}$:

* **`sine`:** $y(t) = A_{\text{amp}} \cdot \sin(2\pi \cdot f \cdot t) + \text{Offset}$
* **`square`:** Emits $+A_{\text{amp}} + \text{Offset}$ during positive half-cycles and $-A_{\text{amp}} + \text{Offset}$ during negative ones.
* **`triangle`:** Continuous bidirectional ramp: for $\phi = (t \cdot f) \pmod 1$, $y(t) = A_{\text{amp}} \cdot (2|2\phi - 1| - 1) + \text{Offset}$.
* **`sawtooth`:** Linear upward ramp with instant drop: for $\phi = (t \cdot f) \pmod 1$, $y(t) = A_{\text{amp}} \cdot (2\phi - 1) + \text{Offset}$.

#### 5.4.6. `utilities` and `clamping` Families
* **`clamp`:** Bounds $A$ within interval $[\text{Min}, \text{Max}]$.
* **`lerp`:** Linear interpolation between $A$ and $B$ driven by $t \in [0.0, 1.0]$: $\text{lerp}(A, B, t) = A + (B - A) \cdot t$.
* **`map_range`:** Proportional re-mapping of $A$ from $[\text{MinIn}, \text{MaxIn}]$ to $[\text{MinOut}, \text{MaxOut}]$.
* **`min` / `max`:** Compares $A$ and $B$, returning the minimum or maximum value.
* **`random`:** Uniform pseudo-random generator within $[\text{Min}, \text{Max}]$ with optional seed (`Seed`).

### 5.5. Synergies and Best Practices
* **Harmonic ASS Rotation Oscillation:** Connect a `waves/sine` output directly into an `\frz` field in `Basics/Dynamic Format` to produce cyclical rocking (e.g. `\frz(%s)` with an amplitude of $10^\circ$).
* **Non-Linear Scale Transitions:** Wire the `Out` port of an `easing/ease_out` curve into the `\fscx` and `\fscy` ports of `Basics/MultiTag` to animate smooth entrance reveals from 0% to 100%.

---

## 6. Node `Basics/MultiRandom` (Deterministic Stochastic Generator)

* **Canonical Category:** `Basics` (UI: *Basics / MultiRandom*)
* **Purpose:** Generates scalar pseudo-random values or deterministic lists for spatial scattering, tag jitter, and stochastic sequences across 15 modes.

![Basics/MultiRandom](img/multirandom.png)

### 6.1. Input Ports (*Inputs*)
1. **`Min`:** Lower bound of the generation range, start colour, or option list.
2. **`Max`:** Upper bound of the range or destination colour.
3. **`Step`:** Discrete quantisation step between generated values.
4. **`Total (N)`:** Total count of values to emit when consuming the `Batch / List` output.
5. **`Iterator`:** Scope variable governing value memoisation (e.g. `s_i`, `j`, `syl`, `char`, `line`). If left empty, calculates a fresh value on every call.

### 6.2. Output Ports (*Outputs*)
1. **`[1.1] Data`:** Emits a single random value evaluated for the active iteration.
2. **`[1.2] Batch / List`:** Emits a comma-separated list of $N$ random values (`v1, v2, v3, ...`), suitable for feeding parameter lists or particle arrays.

### 6.3. Scope Dispatcher in Expressions (`by.<iterator>.<R_mode>`)
To invoke deterministic random values cached per iterator inside ASS expressions or Python scripts:
* **In ASS Expressions:**
  ```text
  \frz(by.syl.Rs(15))
  \fscx(100 + by.char.R(0, 30))
  ```
* **In Scripts (`Define Vars` / `Script Code`):**
  ```python
  angle = by.s_i.Rms(0.01, 0.02)            # Constant value during the active Slicer piece
  offset = by.j.Rs(10)                      # Constant value across the MaxLoop cycle
  colour = by.syl.Rcolor("#FFFFFF", "#0088FF") # Constant colour for the entire syllable
  ```
Within the same cycle of the specified iterator, repeated queries return the identical memoised value. When the iterator advances, the engine automatically recomputes and stores a new value.

### 6.4. Catalogue of the 15 Random Modes (`mode`)

| Mode (`mode`) | Name / Type | Algorithmic Description & Range | Example Output |
| :--- | :--- | :--- | :--- |
| `R` | Uniform Random | Random numbers between `Min` and `Max` quantised to multiples of `Step`. If bounds and step are integers, returns exact integers. | `42` |
| `Rs` | Bipolar Symmetric | Applies an equiprobable sign ($\pm 1$) over the uniform value: $\text{res} = R(\text{Min}, \text{Max}) \cdot (\pm 1)$. | `-35` or `35` |
| `Rr` | Resolution Relative | Scales value relative to script horizontal width ($R_x$ relative to $1280\text{ px}$): $\text{res} = R \cdot \frac{R_x}{1280}$. | `68.5` |
| `Rd` | Single Decimal | Uniform float constrained to 1 decimal place of precision ($0.1$). | `14.3` |
| `Rc` | Centesimal | Uniform float constrained to 2 decimal places of precision ($0.01$). | `87.25` |
| `Rm` | Millesimal | High-precision uniform float constrained to 3 decimal places ($0.001$). | `3.142` |
| `Rds` | Bipolar Decimal | Variant of `Rd` with equiprobable sign ($\pm$). | `-12.4` |
| `Rcs` | Bipolar Centesimal | Variant of `Rc` with equiprobable sign ($\pm$). | `-45.82` |
| `Rms` | Bipolar Millesimal | Variant of `Rm` with equiprobable sign ($\pm$). | `+0.915` |
| `Re` | Discrete Choice | Randomly selects an element from a comma-separated list in `Options` (e.g. `\blur1, \blur3, \blur6`). | `\blur3` |
| `Rfake` | Deterministic Hash | Congruential generator dependent strictly on iteration counter ($i$ or $j$): $\text{Hash}(c) = (c \cdot 9301 + 49297) \pmod{233280}$. | `18` |
| `Rcolor` | Chromatic Interpolation | Generates a random colour uniformly interpolating between `Min` and `Max` in RGB space, or picking from a list if `Min` contains commas. | `&H7FA412&` |
| `R2d` | 2D Coordinates | Emits an independent Cartesian pair in `"X,Y"` format. | `120.5,-45.2` |
| `Rbool` | Probabilistic Boolean | Returns `"True"` or `"False"` based on a percentage threshold $P \in [0, 100]$ in `Min`. | `"True"` |
| `Rstep` | Quantised Step | Generates values strictly constrained to integer multiples of `Step` (e.g. rotations in multiples of $45^\circ$). | `180` |

### 6.5. Synergies and Best Practices
* **Controlled Spatial Jitter:** Wire a `Data` output in `Rs` mode with range $[2, 8]$ into a position displacement $\Delta x$ to impart organic vibration without compromising text legibility.
* **Per-Syllable Chromatic Variety:** Use `Rcolor` scoped with `by.syl` connected to the `\1c` input of `Basics/MultiTag` so that each syllable displays a unique hue while keeping its constituent characters uniform.

---

## 7. Node `Basics/Concatenate` (Extensible Concatenator and Zip Mode)

* **Canonical Category:** `Basics` (UI: *Basics / Concatenate*)
* **Purpose:** Assembles multiple text strings, ASS tags, or vector commands into a unified string via a configurable separator or parallel interleaving (`zip` mode).

![Basics/Concatenate](img/concatenate.png)

### 7.1. Input Ports and Dynamic Expansion
* **`In1`, `In2`, $\dots$, `InN`:** Sequential input sockets. Connecting or clicking `(+)` dynamically appends extra slots continuously.
* **Precedence:** If a port has no incoming connection wire, the node uses the value typed into its inline text field.

### 7.2. Output Ports (*Outputs*)
1. **`[1.1] String`:** Resulting text string after joining active inputs.

### 7.3. Separator Modes (`separator`)

| Separator (`separator`) | Injected Character | Purpose / Use Case |
| :--- | :---: | :--- |
| `nil` / `none` / `""` | *(None)* | Seamless continuous join (e.g. merging tags into a block `\pos(X,Y)\blur2\1c&HFFFFFF&`). |
| `space` / `" "` | Space | Word separation or coordinate lists in ASSdraw instructions (`m 0 0 l 10 10`). |
| `comma` / `","` | Comma `,` | Constructing delimited lists for palette nodes or value arrays. |
| `semicolon` / `";"` | Semicolon `;` | Grouping data parameters or script sequences. |
| `newline` / `"\n"` | Line break | Generating multiline subtitles or stacked dialogue blocks. |
| `zip` | *(Interleaved)* | Positional parallel combination algorithm for value lists. |

### 7.4. Parallel Interleaving Algorithm (*Vector Zip*)
When `separator` is set to `zip`, the node treats each input as a comma-separated list and joins them element by element:

$$\text{In}_1 = [A_1, A_2, A_3], \quad \text{In}_2 = [B_1, B_2, B_3] \implies \text{Out} = [A_1 B_1, \, A_2 B_2, \, A_3 B_3]$$

1. Decomposes each active input into a sequence of tokens.
2. If an input port's inline field contains a tag prefix (e.g. `\1c`, `\blur`), it prepends it to each individual token of that list.
3. Pairs tokens position by position up to the length of the shortest list containing more than one item, outputting a comma-separated list of merged keyframes.

### 7.5. Synergies and Best Practices
* **Clean ASS Block Assembly:** Set `separator` to `nil` when combining outputs from `MultiTag` or literal strings to prevent unintended spaces that could affect libass rendering.
* **Vectorised Keyframe Generation:** Use `zip` mode pairing a colour list from `Functions/Color Gradient` with an alpha list to drive complex per-frame transitions.

---

## 8. Node `Basics/Dynamic Format` (Dynamic String Formatter)

* **Canonical Category:** `Basics` (UI: *Basics / Dynamic Format*)
* **Purpose:** Assembles text strings using templates with `printf`-style format specifiers (`%s`, `%d`, `%f`, `%.2f`, `%04d`, `%x`) and automatic vectorisation over comma-delimited lists.

![Basics/Dynamic Format](img/dynamic_format.png)

### 8.1. Input Ports (*Inputs*)
1. **`In1`, `In2`, $\dots$, `InN`:** Scalar values or lists injected into the positional format specifiers (`%...`) of the template.

### 8.2. Output Ports (*Outputs*)
1. **`[1.1] String`:** Formatted string result. If inputs are lists, returns the series of formatted strings joined with commas.

### 8.3. Format Specifiers in `format`

| Specifier | Expected Type | Conversion Applied | Example with Input `42.68` |
| :--- | :--- | :--- | :--- |
| `%s` | Any data | Direct textual insertion. | `"42.68"` |
| `%d` / `%i` | Integer | Converted to integer. | `"42"` |
| `%04d` | Padded Integer | Zero-padded integer up to 4 digits. | `"0042"` |
| `%f` | Float | Standard floating-point representation. | `"42.680000"` |
| `%.2f` | Bounded Float | Restricted to exactly 2 decimal places. | `"42.68"` |
| `%x` / `%X` | Hexadecimal | Integer converted to base 16 in lowercase or uppercase. | `"2a"` / `"2A"` |

### 8.4. Automatic List Vectorisation
If any connected input receives a comma-separated list of values (e.g. `In1 = "10, 20, 30"`, `In2 = "0.5, 1.0, 1.5"`), `Dynamic Format` repeats the template for each paired element:

$$\text{Template: } \texttt{\\blur\%s\\bord\%s} \implies \texttt{"\\blur10\\bord0.5, \\blur20\\bord1.0, \\blur30\\bord1.5"}$$

### 8.5. Synergies and Best Practices
* **Precise ASS Numeric Formatting:** Use `\pos(%.1f,%.1f)` or `\fscx%d\fscy%d` to ensure calculated numeric parameters are formatted with required precision without generating excessive decimals in the ASS file.
* **Compact Timed Transforms:** Complex templates like `\t(%d,%d,\fscx%d\fscy%d)` let you bundle timing and scaling calculations compactly into a single node before final output.

---

## 9. Node `Basics/MultiTag` (Universal ASS Tag Generator)

* **Canonical Category:** `Basics` (UI: *Basics / MultiTag*)
* **Purpose:** Comprehensive generator and serialiser for all ASS (*Advanced SubStation Alpha*) style tags, spatial transforms, kinematics, alpha transparency, colourimetry, and vector clip masks.

![Basics/MultiTag](img/multitag.png)

---

### 9.1. Header Mode Combos and Interactive Shortcuts
1. **`[2.1] Tag Type` (`tag_type`):** Dropdown selector that switches the ASS tag type and reconfigures input ports dynamically:

```
[ \pos ] ───> Inputs: [ X, Y ]
[ \move ] ──> Inputs: [ X1, Y1, X2, Y2, T1, T2 ]
[ \org ] ───> Inputs: [ X, Y ]
[ \t ] ─────> Inputs: [ Tags, T1, T2, Accel ]
[ \clip ] ──> Inputs: [ Shape / Drawing ]
[ \1c..\4c ]> Inputs: [ Color ]
[ \alpha ] ─> Inputs: [ Alpha (0..255) ]
[ Scalar ] ─> Inputs: [ Value ] (e.g. \fscx, \frz, \blur, \bord)
```

2. **Double-Click Shortcut & Tag Catalogue Modal:**
   * **Double-clicking the node body** or **clicking the mode pill in the header** opens the **Visual ASS Tag Catalogue**.
   * Real-time search filter by tag name, prefix, or visual category (*Positioning, Kinematics, Colourimetry, Alpha, Scaling, Borders, Typography, Karaoke*).

---

### 9.2. Output Ports (*Outputs*)
1. **`[1.1] String`:** Emits the formatted ASS tag block with valid syntax (e.g. `\pos(640,360)`, `\t(0,500,2.0,\fscx150\fscy150)`).

### 9.3. Supported ASS Tag Catalogue
* **`pos` $\to$ `\pos(X,Y)`:** Cartesian screen position.
* **`move` $\to$ `\move(X1,Y1,X2,Y2[,T1,T2])`:** Kinematic linear motion between two coordinates.
* **`org` $\to$ `\org(X,Y)`:** Cartesian origin point for rotations (`\frz`) and affine shear transforms.
* **`t` $\to$ `\t([T1,T2,][Accel,]Tags)`:** Continuous parametric intermediate tag animation.
* **`fad` $\to$ `\fad(FadeIn,FadeOut)`:** Simple millisecond fade in / fade out.
* **`fade` $\to$ `\fade(A1,A2,A3,T1,T2,T3,T4)`:** Complex 3-point timed alpha fade.
* **`clip` / `iclip` $\to$ `\clip(Shape)` / `\iclip(Shape)`:** Direct or inverted vector clipping mask.
* **`1c` $\dots$ `4c` $\to$ `\1c&HBBGGRR&` $\dots$ `\4c&HBBGGRR&`:** Primary fill, inactive karaoke, border, and shadow colours.
* **`alpha`, `1a` $\dots$ `4a` $\to$ `\alpha&HAA&` $\dots$ `\4a&HAA&`:** Global or channel-specific opacity.
* **Scale and Rotation:** `\fscx`, `\fscy`, `\frz`, `\frx`, `\fry`, `\fax`, `\fay`.
* **Border and Shadow:** `\bord`, `\xbord`, `\ybord`, `\shad`, `\xshad`, `\yshad`.
* **Blur and Smoothing:** `\blur`, `\be`.
* **Typography and Alignment:** `\an`, `\fs`, `\fsp`, `\q`.

### 9.4. Synergies and Best Practices
* **Parametric Modulation:** Wire numeric outputs (`Basics/Number` or `Basics/Math`) into `\fscx`, `\fscy`, or `\frz` to centralise transforms without manual string concatenations.
* **Direct Tag Assembly:** Connect the `String` outputs of multiple `MultiTag` nodes to `Basics/Concatenate` with `nil` separator to form the final `{\...}` override block before output.

---

## 10. Node `Basics/Only` (Conditional Branching and Filtering)

* **Canonical Category:** `Basics` (UI: *Basics / Only*)
* **Purpose:** Routes or filters data streams according to a logical condition evaluated against the metric variables of the active ASS context.

![Basics/Only](img/only_a.png)

### 10.1. Header Mode Combos
1. **`[2.1] Mode` (`mode`):** Toggles node socket topology:
   * `select` (*Selector / Ternary 2 $\to$ 1*): Features two input sockets (`True`, `False`) and one output (`Out`). If the condition is true, emits data from `True`; if false, emits data from `False`.
   * `split` (*Diverter 1 $\to$ 2*): Features one input socket (`In`) and two outputs (`True`, `False`). If the condition is true, routes input data to `True` and emits an empty string `""` on `False`; if false, emits `""` on `True` and routes input data to `False`.

![Basics/Only (Filter Mode)](img/only_b.png)

### 10.2. Socket Definitions by Mode

#### `select` Mode (2 $\to$ 1)
* **Inputs:**
  * `True`: Data emitted when condition evaluates to true.
  * `False`: Data emitted when condition evaluates to false.
* **Outputs:**
  * `[1.1] Out`: Value selected based on condition outcome.

#### `split` Mode (1 $\to$ 2)
* **Inputs:**
  * `In`: Data stream to be routed.
* **Outputs:**
  * `[1.1] True`: Emits input data if condition evaluates to true; emits `""` otherwise.
  * `[1.2] False`: Emits input data if condition evaluates to false; emits `""` otherwise.

### 10.3. Controls and Body Properties
1. **`[2.2] Condition` (`condition`):** Logical expression evaluated on every iteration (e.g. `char.i == 1`, `syl.duration > 300`, `j % 2 == 0`, `'kanji' in line.tags_str`). Default: `"True"`.

### 10.4. Mathematical Model and Logical Evaluation

$$\text{select mode:} \quad \text{Out} = \begin{cases} \text{Input}(\text{True}) & \text{if } \text{eval}(\text{condition}) = \text{True} \\ \text{Input}(\text{False}) & \text{if } \text{eval}(\text{condition}) = \text{False} \end{cases}$$

$$\text{split mode:} \quad (\text{Out}_{\text{True}}, \text{Out}_{\text{False}}) = \begin{cases} (\text{Input}, \texttt{""}) & \text{if } \text{eval}(\text{condition}) = \text{True} \\ (\texttt{""}, \text{Input}) & \text{if } \text{eval}(\text{condition}) = \text{False} \end{cases}$$

### 10.5. Synergies and Best Practices
* **Drop-Cap Initial Character Styling:** Set `condition: char.i == 1` to apply enlarged font size (`\fs40`) or distinctive colours exclusively to the initial letter of each word or line.
* **Odd/Even Alternating Colours:** In `select` mode, feed two distinct colours into `True` and `False` with `condition: char.i % 2 == 0` to create coordinated alternating text patterns.

---

## 11. Node `Basics/Once` (Single Evaluation with Scope Cache)

* **Canonical Category:** `Basics` (UI: *Basics / Once*)
* **Purpose:** Caches its evaluated input value to avoid redundant recomputations within the same execution scope (line, word, syllable, character, or sub-loop).

![Basics/Once](img/once.png)

### 11.1. Header Mode Combos
1. **`[2.1] Mode` (`mode`):** Hierarchy level and lifecycle scope of the memory cache:
   * `global`: Evaluated once across the entire macro execution run over the script.
   * `line`: Evaluated once at the beginning of each dialogue line.
   * `word`: Evaluated once at the start of each word.
   * `syl`: Evaluated once at the start of each karaoke syllable.
   * `char`: Evaluated once per character.
   * `loop`: Evaluated once per sub-loop cycle defined in `iterator` (default: `j`).

### 11.2. Input Ports (*Inputs*)
1. **`In`:** Data input whose computation should be cached (e.g. vector glyph paths from `Text to Shape`, `IMG to Shape`, or colour selections).

### 11.3. Controls and Body Properties
1. **`[2.2] Iterator` (`iterator`):** Name of the loop variable to monitor when `mode = "loop"` (default: `"j"`).

### 11.4. Output Ports (*Outputs*)
1. **`[1.1] Out`:** Emits the cached value without re-evaluating the upstream input subgraph.

### 11.5. Cache Architecture and Scope Hashing
The engine creates a unique cache key composed of the node identifier and the active scope key:

$$\text{CacheKey} = \langle \text{NodeID}, \, \text{ScopeKey} \rangle$$

Where $\text{ScopeKey}$ is generated dynamically based on active mode:
* `global` $\to \texttt{"global"}$
* `line` $\to \texttt{"line\_" + LineID}$
* `word` $\to \texttt{"line\_" + LineID + "\_word\_" + WordID}$
* `syl` $\to \texttt{"line\_" + LineID + "\_syl\_" + SylID}$
* `char` $\to \texttt{"line\_" + LineID + "\_char\_" + CharID}$
* `loop` $\to \texttt{"line\_" + LineID + "\_loop\_" + IteratorName + "\_" + IteratorValue}$

If $\text{CacheKey}$ exists in memory, it immediately returns the stored value in $\mathcal{O}(1)$ time, bypassing upstream graph execution.

### 11.6. Synergies and Best Practices
* **Vector Glyph Acceleration (`Text to Shape`):** Place a `Once (mode: char)` node after `Text to Shape` when driving multi-pass effects via `MaxLoop` or `Shape/Array`. This prevents re-rasterising font glyphs on every loop pass, computing vector geometry once per character.
* **Homogeneous Per-Syllable Randomness:** Insert `Once (mode: syl)` after a stochastic generator to ensure all fragments or particles originating from a syllable share the identical random numerical value.

