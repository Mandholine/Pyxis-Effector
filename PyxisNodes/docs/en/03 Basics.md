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
1. **`[2.1] Value` (`value`):** Editable input field. Its default initial value is blank (`""`), dynamically evaluating to `0` if left empty. Accepts direct numbers (`100`, `-45.2`), ASS context variables (`syl.x`, `line.width`, `j`, `i`, `char.n`), algebraic expressions (`syl.width / 2 + 10`, `sin(j * 0.1) * 50`), or comma-separated lists of numbers and formulas (e.g. `10, 20, 30`). Supports visual line breaks inserted with `Shift + Enter` for convenient multi-line list organisation; during backend evaluation and linting, physical line breaks are automatically stripped to produce a continuous sequence.

### 1.3. Dynamic Evaluation of Expressions
The `value` field is processed dynamically on every execution iteration cycle:
* If the input string contains identifiers registered in the active context (`syl`, `line`, `char`, `video_fps`, etc.), the evaluator substitutes their numerical values prior to calculation.
* If the text contains comma-separated values or formulas, evaluates each component individually and yields the corresponding formatted list.
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
1. **`[2.1] Text` (`value`):** Editable string field. Supports plain text, ASS line break and spacing escape sequences (`\n`, `\N`, `\h`), tag blocks (`{\an5\bord0\shad0}`), or vector drawing paths (`m 0 0 l 100 0 100 100 0 100`). Supports `Shift + Enter` for multi-line formatting in the UI canvas; during backend evaluation and linting, physical line breaks are cleanly collapsed, strictly preserving any explicit ASS line break tags (`\n`, `\N`) intended for the rendered subtitle. If the text contains blocks enclosed in braces `{\...}`, Pyxis string evaluator directly resolves expressions and context variables within the tag parentheses (e.g. `{\pos(syl.center, syl.middle)}` or `\fscx(100 + 20 * i)`) while preserving surrounding literal text.

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

## 5. Node `Basics/Math` (`ke.math` Mathematical Library)

* **Canonical Category:** `Basics` (UI: *Basics / Math*)
* **Purpose:** Brings together all 36 basic (expandable), numeric, sequence, geometric, algebraic, and data operations into a single adaptable node that reconfigures its inputs, controls, and outputs according to the selected operation.

![Basics/Math](img/math.png)

### 5.1. Controls and Canvas Interaction
The node organises its controls into five visual elements:
1. **Header Mode Pills (`Category` and `Operation`):** Click the left pill to switch families (`basic`, `numeric`, `sequence`, `geometry`, `algebra`, `data`) and the right pill to choose the operation. When switching modes, input and output ports reconfigure automatically while keeping compatible wires connected.
2. **`+` and `-` Buttons (`basic` only):** Add or remove input ports (`In1`, `In2`, ..., `InN`) to operate across two or more wired or inline values.
3. **Editable Fields with Sockets:** Accept fixed numbers (`10`), comma-separated lists (`0, 50, 100`), or variables/expressions (`syl.i`, `char.dur / 2`). Connecting a wire to the left socket overrides the inline text.
4. **Cyclic Buttons:** Pills inside the node body (such as `Algorithm`, `Seq Mode`, `Get`, `Axis`, or `Matrix Op`). Each click advances to the next option.
5. **Checkboxes:** Square toggles switched with a single click (`Cycle`, `Random Sign`, `Reals Only`, `Is Row`).

---

### 5.2. `basic` Category (Expandable Arithmetic)

Combines two or more inputs (`In1`, `In2`, ..., `InN`) using the `+` and `-` buttons. Empty inputs are skipped automatically.

* **`add` (Addition):** Sums all inputs (`In1 + In2 + ... + InN`).
* **`sub` (Subtraction):** Subtracts sequentially from the first input (`In1 - In2 - ... - InN`).
* **`mul` (Multiplication):** Multiplies all inputs (`In1 * In2 * ... * InN`).
* **`div` (Division):** Divides sequentially from `In1` (`In1 / In2 / ... / InN`; returns `0` if any divisor is `0`).
* **`mod` (Modulo):** Computes the sequential remainder (`In1 % In2 % ...`; returns `0` if any divisor is `0`).
* **`pow` (Power):** Raises sequentially (`In1 ** In2 ** ...`).
* **`min` (Minimum):** Outputs the smallest numeric value among all inputs.
* **`max` (Maximum):** Outputs the largest numeric value among all inputs.
* **`avg` (Average):** Computes the arithmetic mean of all connected or typed inputs.

---

### 5.3. `numeric` Category (Numeric Calculation and Comparisons)

#### `round` — Rounding
Rounds a number or a comma-separated list to the specified number of decimal places, rounding halves (`.5`) upwards.
* **Inputs:** `Value` (number or comma-separated list), `Decimals` (decimal places; default `0`).
* **Output:** `Out`.
* **Example:** `Value = "1.6, 3.25, 8.7"`, `Decimals = 1` $\to$ `"1.6, 3.3, 8.7"`.

#### `clamp` — Bounding and Cyclic Bounce
Keeps a number (or list) inside `Min` and `Max`, regardless of which bound you type first.
* **Inputs & Controls:** `Value`, `Min` (default `0`), `Max` (default `1`), **`Cycle`** checkbox.
* **Output:** `Out`.
* **Behaviour:**
  * With `Cycle` unchecked: values below `Min` clamp to `Min`, and values above `Max` clamp to `Max`.
  * With `Cycle` checked: values exceeding either bound bounce back and forth within the range (handy for continuous pendulum motion).
* **Example:** `Value = 1.2`, `Min = 0`, `Max = 1`, `Cycle = checked` $\to$ `0.8`.

#### `rand` — Advanced Random
Generates random numbers with step increments, weighted sub-ranges, or random selection from a list.
* **Inputs & Controls:**
  * `Min` and `Max`: range bounds. If `Max` is left empty and `Min` contains a comma-separated list (e.g. `"10, 20, 30"`), picks one item at random. If both are empty, outputs a decimal between `0` and `1`.
  * `Step`: allowed increment between values (e.g. `Step = 5` between `0` and `20` only produces `0, 5, 10, 15, 20`).
  * `Range`: weighted sub-range in `rmin, rmax, percentage` format (e.g. `"20, 80, 75"` makes 75% of results fall between 20 and 80).
  * **`Random Sign`** checkbox: randomly multiplies the result by `+1` or `-1`.
* **Output:** `Out`.

#### `factk` — Factorial
Computes the factorial of `N` (rounded up in absolute value; returns `1` for `0`).
* **Inputs:** `N` $\to$ **Output:** `Out`.
* **Example:** `N = 5` $\to$ `120`.

#### `to16` — Hexadecimal Conversion
Converts an integer (or a list) to uppercase hexadecimal text, useful for building ASS colour or alpha channel strings.
* **Inputs:** `Number` $\to$ **Output:** `Out`.
* **Example:** `Number = "255, 16, 12"` $\to$ `"FF, 10, C"`.

#### `equality` — Equality with Tolerance
Compares `A` and `B` and outputs `True` when their difference is smaller than the margin set by `Tolerance` (where `Tolerance = 5` means a difference below `0.00001`).
* **Inputs:** `A`, `B`, `Tolerance` (default `5`) $\to$ **Output:** `Out` (`True` or `False`).

#### `between` — Range Check
Checks whether `Value` lies within the closed interval defined by `Min` and `Max` (bound order is adjusted automatically).
* **Inputs:** `Value`, `Min`, `Max` $\to$ **Output:** `Out` (`True` or `False`).

---

### 5.3. `sequence` Category (Sequences, Counters, and Interpolation)

#### `i` — Discrete Sequence Generator
Turns a positive integer counter `Counter (i)` (such as `syl.i`, `char.i`, or `j`) into repeating numeric patterns without writing conditionals.
* **Inputs & Controls:** `Counter (i)`, **`Algorithm`** cyclic button, `A`, `B`, `C`.
* **Output:** `Out`.
* **Quick guide to all 9 algorithms** (showing outputs for `Counter = 1, 2, 3, 4, 5, 6`):

| Algorithm | What it does | Parameter example | Resulting sequence (`i = 1..6`) |
| :--- | :--- | :--- | :--- |
| `+,-` | Alternates `1` and `-1` every `A` steps | `A = 2` | `1, 1, -1, -1, 1, 1` |
| `A,B` | Alternates between `A` and `B` every `C` steps | `A = 10, B = 20, C = 1` | `10, 20, 10, 20, 10, 20` |
| `mxA` | Multiplies `A` stepping up every `B` steps | `A = 5, B = 2` | `5, 5, 10, 10, 15, 15` |
| `A>B` | Cycles from `A` to `B` every `C` steps | `A = 1, B = 3, C = 1` | `1, 2, 3, 1, 2, 3` |
| `ABA` | Ping-pongs between `A` and `B` | `A = 1, B = 3` | `1, 2, 3, 2, 1, 2` |
| `ABB` | Emits `A` on step 1 and `B` thereafter | `A = 5, B = 9` | `5, 9, 9, 9, 9, 9` |
| `ABC` | Emits `A` once and `B` for `C - 1` steps | `A = 1, B = 2, C = 3` | `1, 2, 2, 1, 2, 2` |
| `ACB` | Emits `A` for `C - 1` steps then `B` once | `A = 1, B = 2, C = 3` | `1, 1, 2, 1, 1, 2` |
| `N,n` | Natural numbers repeated `A` times each | `A = 2` | `1, 1, 2, 2, 3, 3` |

#### `count` — Stateful Counter
Keeps an internal counter for that node starting at `Init` and adding `Step` each time it is evaluated during generation.
* **Inputs & Controls:** `Init` (default `1`), `Step` (default `1`), **`Seq Mode`** cyclic button (`none` or any of the 9 `i` algorithms), `A`, `B`, `C`.
* **Output:** `Out`.

#### `normalize` — Progress Normalisation
Converts any number (or ascending list) into a normalised factor between `0` and `1`.
* **Inputs:** `t` (values above `1` are automatically scaled down by the matching power of 10, e.g. `25` $\to$ `0.25`), `Accel` (acceleration exponent; `1` is linear, `2` starts slowly, `0.5` starts fast), and `Shape` (optional: when an ASSDraw path is connected, uses its vertical `Y` profile as the progression curve).
* **Output:** `Out`.

#### `ipol` — Multi-Point Interpolation
Interpolates smoothly across two or more values in `Values` according to progress `t` (between `0` and `1`).
* **Inputs:** `Values` (e.g. `"0, 30, 20"`), `t`, `Accel`, `Shape` (optional ASSDraw shape curve), and `Size` (optional: entering an integer such as `5` outputs the full list of 5 sampled values from start to finish).
* **Output:** `Out`.
* **Example:** `Values = "0, 100"`, `Size = 3` $\to$ `"0, 50, 100"`.

---

### 5.4. `geometry` Category (ASSDraw3 Geometry)

All operations in this category work in the ASSDraw3 coordinate system used by subtitles (origin at top-left, Y-axis pointing downwards).

#### `angle` — Angle Between Points
Computes the angle in degrees (`0` to `360`) formed by one, two, or three points.
* **Inputs:** `P1`, `P2`, `P3` (optional).
  * `P1` only: angle of the point relative to the origin `(0, 0)`.
  * `P1` and `P2`: angle of the segment from `P1` to `P2`.
  * `P1`, `P2`, and `P3`: interior angle between the two segments meeting at `P2`.
* **Output:** `Out`.

#### `polar` — Polar Coordinates
Converts an angle in degrees (`Angle`) and a pixel distance (`Radius`) into Cartesian `(X, Y)` coordinates ready for `\pos` or shapes.
* **Inputs & Controls:** `Angle`, `Radius`, **`Get`** cyclic button (`xy`, `x`, `y`).
* **Outputs:** `X`, `Y`. When `Get` is set to `y`, the primary output emits the vertical `Y` component.
* **Example:** `Angle = 45`, `Radius = 10` $\to$ `X = 7.071`, `Y = -7.071`.

#### `distance` — Distance and Path Length
Measures the pixel distance between `P1` and `P2`, distance from the origin if `P2` is empty, or total length along a multi-vertex polyline or ASSDraw shape in `P1`.
* **Inputs:** `P1`, `P2` $\to$ **Output:** `Out`.
* **Example:** `P1 = "0, 0"`, `P2 = "3, 4"` $\to$ `5`.

#### `intersect` — Segment Intersection
Finds the exact intersection point between the lines defined by `Segment 1` (`x1 y1 x2 y2`) and `Segment 2` (`x3 y3 x4 y4`).
* **Inputs:** `Segment 1`, `Segment 2`.
* **Outputs:** `X`, `Y`, `t` (relative position of the crossing along the first segment; outputs `parallels` on `X` if they never meet).

#### `circle` — Circle Through Three Points
Finds the centre and radius of the unique circle passing through `P1`, `P2`, and `P3` (or the first three points of a shape).
* **Inputs:** `P1`, `P2`, `P3`.
* **Outputs:** `Center X`, `Center Y`, `Radius` (outputs `collineals` on `Center X` if the three points lie on a straight line).

#### `rotate` — 2D / 3D Rotation for Points and Shapes
Rotates a `(x, y, z)` point or every vertex of a full ASSDraw shape around the chosen axis.
* **Inputs & Controls:** `Point / Shape` (coordinates or ASSDraw `m ... l ...` string), `Angle` (degrees), **`Axis`** cyclic button (`z`, `x`, `y`).
* **Outputs:** `Out` (`x, y, z` list or rotated ASSDraw string), `X`, `Y`, `Z`.

---

### 5.5. `algebra` Category (Equations and Matrices)

#### `quadratic` — Quadratic Equation
Finds the real roots of a second-degree equation (`c1*x^2 + c2*x + c3 = 0`) sorted in ascending order.
* **Inputs:** `c1 (x^2)`, `c2 (x)`, `c3 (1)` $\to$ **Output:** `Roots`.

#### `cubic` — Cubic Equation
Finds the real roots of a third-degree equation (`c1*x^3 + c2*x^2 + c3*x + c4 = 0`).
* **Inputs:** `c1 (x^3)`, `c2 (x^2)`, `c3 (x)`, `c4 (1)` $\to$ **Output:** `Roots`.

#### `resolve` — Automatic Solver
Takes descending coefficients in `Coefficients` (stripping leading zeros) and automatically solves linear, quadratic, or cubic equations.
* **Inputs:** `Coefficients` $\to$ **Output:** `Roots`.

#### `equation` — N-Degree Polynomials
Computes all roots of an arbitrary-degree polynomial given ascending coefficients (e.g. `"-5, -9, -3, 1"` represents `-5 - 9x - 3x^2 + x^3 = 0`).
* **Inputs & Controls:** `Coefficients`, **`Reals Only`** checkbox (when checked, hides complex roots).
* **Output:** `Roots`.

#### `evaluate` — Polynomial Evaluation
Evaluates the polynomial defined in `Coefficients` (ascending order) at `t`.
* **Inputs:** `Coefficients`, `t` $\to$ **Output:** `Out`.
* **Example:** `Coefficients = "5, -7"`, `t = 2` (computes `5 - 7*2`) $\to$ `-9`.

#### `gauss` — Linear Equation System
Solves an `n` by `n` system of linear equations by entering augmented matrix rows separated by semicolons `;`.
* **Inputs:** `Matrix` (e.g. `"5, -3, -1; 2, 1, 4"` represents `5x - 3y = -1` and `2x + y = 4`).
* **Output:** `Solutions` (e.g. `"1, 2"`, or `"singular system"` when no unique solution exists).

#### `matrix` — Matrix Algebra
Performs operations on square matrices and row vectors. Separate rows with `;` or enter a flat list of numbers (e.g. `"1, 2, 3, 4"` builds a 2x2 matrix).
* **Inputs & Controls:**
  * **`Matrix Op`** cyclic button:
    * `mul`: Multiplies `Matrix A` by `Matrix B` (accepts another matrix, a scalar number, or a vector).
    * `add` / `sub`: Element-wise addition or subtraction between `Matrix A` and `Matrix B` (or a scalar).
    * `neg`: Negates every element in `Matrix A`.
    * `det`: Computes the determinant of `Matrix A`.
    * `inverse`: Computes the inverse matrix of `Matrix A` (or outputs `singular matrix` if the determinant is 0).
    * `identity`: Builds an identity matrix of size `N` (using the first number in `Matrix A`).
    * `rotate`: Multiplies `Matrix A` by the 3D rotation matrix defined in `Angles (x,y,z)`.
    * `eq`: Checks whether `Matrix A` and `Matrix B` are equal (`True` or `False`).
    * `toarray`: Flattens `Matrix A` into a comma-separated list.
  * **`Is Row`** checkbox: treats `Matrix A` as a row vector instead of a square matrix.
* **Outputs:** `Out` (formatted result) and `Det` (matrix determinant).

---

### 5.6. `data` Category (Extraction and Formatting)

#### `getpair` — Extract Numeric Pair
Extracts the first two numbers found in `Values` (handy for reading `(x, y)` coordinates from text or ASSDraw paths). If the second number is missing, repeats the first or falls back to `Default Y`; if empty, uses `Default X` and `Default Y`.
* **Inputs:** `Values`, `Default X`, `Default Y` $\to$ **Outputs:** `X`, `Y`.

#### `getnumbers` — Extract All Numbers
Extracts every number from a text string, coordinate pair, or ASSDraw shape (`Input`) as a comma-separated list.
* **Inputs:** `Input` $\to$ **Output:** `Out`.
* **Example:** `Input = "m 1 2 l -3.5 4"` $\to$ `"1, 2, -3.5, 4"`.

#### `format` — String Formatting
Inserts comma-separated values from `Values` into placeholders such as `%s`, `%d`, or `%X` in `Format`.
* **Inputs:** `Format`, `Values` $\to$ **Output:** `Out`.
* **Example:** `Format = "pos(%d, %d)"`, `Values = "10, 20"` $\to$ `"pos(10, 20)"`.

---

### 5.7. Practical Production Workflows

1. **Alternate tilt between odd and even syllables:**
   ```
   [Basics/Math (sequence / i, Algorithm: +,-)] ──► Out ──► \frz ──► [Basics/MultiTag]
   ```
   Type `syl.i` in `Counter (i)` and `1` in `A`; it emits `+1` and `-1` alternately to tilt each syllable without conditionals.

2. **Arrange letters or particles in a circle around a centre:**
   ```
   [Basics/Math (geometry / polar)] ──► X ──► X ──► [Basics/MultiTag (\pos)]
                                    └──► Y ──► Y ──┘
   ```
   Wire an angle proportional to each item's index (`360 * (char.i - 1) / char.n`) into `Angle` and the desired distance into `Radius`.

3. **Motion curve driven by a shape profile:**
   ```
   [Shape/Library] ──► Shape ──► Shape ──► [Basics/Math (sequence / ipol)] ──► Out ──► [Basics/MultiTag]
   ```
   When any shape is wired into `Shape`, `ipol` uses its vertical profile as the easing curve across the values in `Values`.

4. **Rotate an entire shape directly in the graph:**
   ```
   [Shape/Library] ──► Shape ──► Point / Shape ──► [Basics/Math (geometry / rotate)] ──► Out ──► [System/Output]
   ```
   With `Axis` set to `z`, every vertex in the shape rotates by the specified angle and outputs ready-to-use ASSDraw geometry.

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

* **Hierarchical Scope Inheritance:** Sub-loops (`by.j`, `by.s_i`, `by.p_i`) inherit the hierarchy of the enclosing active unit (`line` -> `char`/`syl`/`word` -> sub-loop). Thus, particle $j=1$ for character 1 generates values independently from particle $j=1$ for character 2. Concurrently, `by.char.R(...)` preserves its exact memoised value across all $j$ iterations of that same character, recalculating only when advancing to the subsequent character.
* **Callsite Isolation:** Every time you write `R(...)` or `by.<iter>.R*(...)` (even multiple times in the same expression, such as `R(10) + R(10) + R(10)`, or across separate variables such as `Origenx` and `Origeny`), each call is evaluated independently and never collides with other calls.
* **Grouping via Variables vs. Mixed Scopes:** The only way to reuse the exact same random result across multiple places within an iteration is to **store it in a variable** and reference that variable:
  * If you define `my_var = by.char.R(10)` and reuse `my_var` across tags or ports, it returns the same number across all sub-loops of that character (and updates only when advancing to the next character).
  * If you combine scopes in one variable, e.g. `my_var = by.j.R(10) + by.char.R(10)`, the `by.char.R(10)` term stays constant per character whilst `by.j.R(10)` changes on every `j` cycle, so `my_var` produces a distinct value per `(char, j)` pair (and only repeats if you read `my_var` multiple times within that same `(char, j)` pass).
  * If you use `R(10)` without `by.`, each call draws a fresh value on every loop iteration where it is evaluated.

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

## 7. Node `Basics/Concatenate` (Extensible Concatenator and Zip)

* **Canonical Category:** `Basics` (UI: *Basics / Concatenate:)
* **Purpose:** Assembles multiple text fragments, ASS tags, or keyframe sequences via two header-selectable operational modes (`basic`, `zip`), incorporating a contextual separator selector in the lower-right corner for basic mode. For assembling and styling complex vector shapes in a continuous monolithic stream with or without `\r` style resets, canonically use `Basics/Builder`.

![Basics/Concatenate](img/concatenate.png)

### 7.1. Input Ports and Dynamic Expansion
* **`In1`, `In2`, $\dots$, `InN`:** Sequential data input sockets. Clicking the expansion button `(+)` adds additional input slots continuously.
* **Precedence:** If a port has no connected wire, the node falls back to the value entered manually into its inline text field.

### 7.2. Output Ports
1. **[1.1] String`:** Resulting string after assembling all active inputs according to the selected mode.

### 7.3. Main Operational Modes (`mode`)
Flipping the mode pill button on the right side of the title bar cycles between the 2 unified canonical modes:

| Mode (`mode`) | UI Badge | Algorithmic Description |
| :--- | :--: | :--- |
| `basic` | `BASIC` | Linear concatenation of inputs interleaving the delimiter selected in the node body (`separator`). |
| `zip` | `ZIP` | Element-to-element positional interleaving for producing temporal keyframe lists. |

### 7.4. Contextual Separator Selector in Basic Mode (`separator`)
When `basic` mode is active, an interactive cyclic button is drawn at the bottom-right corner (under the *String* output port). Clicking it cycles through the five supported delimiters:

| Separator (`separator`) | UI Pill | Injected Character | Typical Use Case |
| :--- | :--:(��贴���贴���4)���������9=9����9�������ɕ�Ёх�����������������q��̡`�d�q�����pŌ�!������4)�����������MA
���M����������]�ɐ�͕�Օ���́�ȁ������MM�Ʌ܁��ѡ̸��4)���������������
��������A�Ʌ��ѕȁ����́�����յ�ɥ����Ʌ�̸��4)��͕�����������퀁�M�����������M��ѥ�����չ��ɥ�́�ȁ͍ɥ�ѥ����хѕ����̸��4)����ݱ�������9QI���9�ݱ�����q����5ձѤ�������х������Չѥѱ�̸��4(4(�9�є訁%�������������ѡ��͕��Ʌѽȁ���ѽ���́��ѽ��ѥ����䁡�������ɽ��ѡ�����م̰��́�Ё������́��́�ݸ�����ɥѡ������������ݥѡ��Ёɕ�եɥ���ѕ��Յ��������ѕ�̸4(4(����ܸԸ�A�Ʌ�����i������ɥѡ����5��������4)]������������͕́ЁѼ�������ѡ��������ɕ��́���������Ё�́��������͕��Ʌѕ�����Ё����ѕ�́��������́ѡ�����ͥѥ�������ͥѥ���4(4(��qѕ���%��|Ā�m|İ�|Ȱ�|�t��q�Յ��qѕ���%��|Ȁ�m	|İ�	|Ȱ�	|�t�q������́qѕ���=����m|ā	|İ�p��|ȁ	|Ȱ�p��|́	|�t��4(4(ĸ�M����́�������ѥٔ�����Ё��Ѽ���͕�Օ�������ѽ���̸4(ȸ�%���������Н́����������������х��́��х���ɕ����������pō����q���ɀ����Ё�ɕ����́�ЁѼ��ٕ�䁥���٥�Յ��ѽ�������ѡ�Ё���и4(̸�A���́�ѕ�́��ͥѥ�������ͥѥ������Ѽ�ѡ������Ѡ����ѡ��͡��ѕ�Ё���ЁݥѠ���ɔ�ѡ��������ѕ�������ѥ�����������͕��Ʌѕ�����Ё�����ɝ������Ʌ��̸4(4(����ܸظ�M幕ɝ��́����	��ЁAɅ�ѥ���4(����
�����ML�	������͕����訨�U͔������聉�ͥ���ݥѠ��͕��Ʌѽ�聹����Ѽ���ɝ��������́�ɽ���5ձѥQ�����ȁɅ܁��ɥ��́ݥѡ��Ё��͕�ѥ����������х��ݡ�ѕ������ѡ�Ё��䁍�����Ё�����́ɕ���ɥ���4(����Y��ѽɥ͕��-��Ʌ���
ɕ�ѥ��訨�U͔�����������Ѽ����������������ȁ���Ё�ɽ���չ�ѥ��̽
���ȁɅ����р�ݥѠ����������䁱��ЁѼ��ɥٔ���ȵ�Ʌ������Ʌ����Ʌ�͙�ɵ�ѥ��̸4(4(���4(

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

2. **Tag Catalogue Modal & Single-Click Access:**
   * A **single click on the header mode pill** (or double-clicking the node body) immediately displays the interactive **ASS & Dark Tag Catalogue Modal** with real-time search. Clicking the mode pill no longer cycles tags manually; all selection is performed directly through the modal catalogue.

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
* **Standard Scaling, Rotation & Styling:** `\fscx`, `\fscy`, `\frz`, `\frx`, `\fry`, `\fax`, `\fay`, `\bord`, `\xbord`, `\ybord`, `\shad`, `\xshad`, `\yshad`, `\blur`, `\be`, `\fs`, `\fsp`, `\fn`, `\an`, `\r`, `\q`, `\b`, `\i`, `\u`, `\s`, `\k`, `\kf`, `\ko`, `\p`, `\pbo`.
* **Pyxis Dark Tag Extensions Catalogue:**
  * **Composite & Multi-Channel:** `\fscxy` (proportional scale X and Y), `\faxy` (proportional shear), `\xybord` (outline width X and Y), `\xyshad` (shadow distance X and Y), `\bs` (simultaneous border and shadow), `\frxy`, `\frxz`, `\fryz`, `\frxyz` (3D compound rotations), multi-channel colours (`\134c`, `\13c`, `\14c`, `\34c`, `\12c`, `\23c`), and multi-channel alpha opacities (`\134a`, `\13a`, `\14a`, `\34a`, `\12a`, `\23a`).
  * **Auto-Origin 3D (`o`):** 3D rotation tags automatically anchored to the metric centre of the element without requiring manual `\org` coordinate calculation (`\fro`, `\frzo`, `\frxo`, `\fryo`, `\frxyo`, `\frxzo`, `\fryzo`, `\frxyzo`).
  * **Baseline Style Restoration (`~`):** Parameterless override tags that instantly restore values from the baseline style header (`\c~`, `\alpha~`, `\fscxy~`, `\fscx~`, `\fscy~`, `\fs~`, `\fsp~`, `\fn~`, `\an~`, `\bord~`, `\shad~`, `\bs~`, `\blur~`, `\be~`, `\frz~`, `\frx~`, `\fry~`, `\frxyz~`, `\faxy~`, `\b~`, `\i~`, `\u~`, `\s~`, and multi-channel restorations `\134c~`..`\34c~`, `\134a~`..`\34a~`).
  * **Style Ratio Scaling (`r`):** Multiplies baseline style metrics by an arbitrary scalar ratio (`\fscxyr`, `\fscxr`, `\fscyr`, `\fsr`).
  * **Stochastic Randomisation (`R`):** Unit-level pseudo-random variance (`\cR`, `\1cR`..`\4cR`, `\alphaR`, `\1aR`..`\4aR`, `\fscxyR`, `\frzR`, `\bordR`, `\shadR`, `\bsR`, `\blurR`, `\fsR`, `\fspR`).
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


---

## 12. Node `Basics/Builder` (Monoline Block Assembler with Sub-Loop)

* **Canonical Category:** `Basics` (UI: *Basics / Builder*)
* **Purpose:** Assembles multiple text segments or vector shape pieces into a **single ASS dialogue line**. Features expandable data inputs with a fixed top `Tags` port and dynamic `In1`, `In2`, ... ports (extended via `+` and `-` buttons). Allows controlling via `Reset \r` whether each block is isolated with style reset barriers (`\r`) (re-injecting global animations into every sub-block) or emitted as a continuous `\p1` drawing stream where intermediate blocks receive static style overrides (such as `\1c` colour gradients or border/alpha shifts) without resetting the drawing mode, automatically preserving and deduplicating upstream temporal transformations (`\t(...)`) from nodes like `Animation`.

![Basics/Builder](img/builder.png)

### 12.1. Mode and Sub-Mode Buttons
1. **Header Mode Button (`TEXT` / `SHAPE` — `mode` property):**
   * `text`: Joins text fragments (syllables, characters, words, repetitions, or custom lists) within a single subtitle line.
   * `shape`: Joins multiple vector drawing pieces (`\p1`) with automatic libass inline cursor advance neutralisation.
2. **Secondary Header Mode Selector (`SPLIT` / `MULTI` / `CUSTOM` — `sub_mode` property):**
   * `splitter` (`SPLIT`): Splits the text source into syllables, characters, or words (in `text` mode), or decomposes a compound vector drawing into individual sub-shapes (in `shape` mode).
   * `multi` (`MULTI`): Clones the input text or shape `repeat` times inside the same ASS line, allowing you to customise colour, scale, or offset per copy using `bu_i`.
   * `custom` (`CUSTOM`): Splits a list of text items or vector drawings by a chosen delimiter (`delim`) and assembles each element as an independent block.

### 12.2. Input and Output Ports

| Direction | Port | Type | Description |
| :--- | :--- | :--- | :--- |
| **Input 0** | `Tags` | `data` | Fixed top port. ASS override tags (or upstream chains from nodes such as `Color Gradient`, `MultiTag`, or `Interpolator`) re-evaluated for each block using `bu_i`, `bu_n`, and `max_bu`. |
| **Inputs 1+** | `In1`, `In2`, ... | `data` | Dynamically expandable data ports (`+` / `-`). Receive the individual text items or vector shapes to assemble. Each connected input provides its own piece preserving its original holes and contours. |
| **Output 0** | `Return` | `data` | Final monoline ASS payload ready to connect to the `Text` port of `System/Output`. |
| **Output 1** | `Items Out` | `data` | Native list of extracted pieces prior to tag injection, useful for feeding parallel nodes. |

### 12.3. Contextual Body Controls

| Property | Visible in | Options / Type | Description |
| :--- | :--- | :--- | :--- |
| `split_by` | `text` + `splitter` | `syl`, `char`, `word` | Granularity used to partition the text (by syllables, characters, or words). |
| `source` | `text` + (`splitter` or `multi`) when `In` ports unwired | `active_unit`, `line`, `text_field` | Selects whether text is read from the active main-loop unit, the full dialogue line, or the manual field. |
| `repeat` | `multi` | Numeric expression (`2` by default) | Number of copies generated inside the same line. Accepts numbers or mathematical formulas. |
| `custom_text` | `custom` when `In` ports unwired | Text or drawing template | List of items separated by the selected delimiter (e.g. `One, Two, Three`). |
| `delim` | `custom` | `,`, `;`, `\|`, `newline`, `space` | Separator character used to split items in `custom` mode. |
| `shape_split_mode` | `shape` + `splitter` | `subpaths`, `islands`, `raw_subpaths` | Geometric decomposition method: `subpaths` preserves inner holes (such as the counters inside letters `O`, `A`, `B`) attached to their outer parent contour; `islands` merges polygons via Clipper; `raw_subpaths` splits directly at every `m` command. |
| `shape_layout` | `shape` | `auto`, `embedded_pos`, `advance`, `stack` | Spatial compensation across pieces: `auto` detects embedded `\pos` coordinates or stacks; `embedded_pos` shifts each piece by its relative `\pos(x,y)` offset from the first piece; `advance` lets shapes advance side by side; `stack` overlays all pieces on the same `(0,0)` origin. |
| `inject_r` | All | Cyclic button (`ON` / `OFF`) | Controls `\r` barrier injection. When `ON`, isolates each block with `\r` and re-injects global animations and styles. When `OFF`, maintains a continuous `\p1` drawing stream, consolidates `\t(...)` transforms once in the header, and injects only static style overrides (`\1c`, `\3c`, `\alpha`, `\bord`, etc.) between pieces. |

### 12.4. Internal Sub-Loop Variables (`bu_i`, `bu_n`, `max_bu`)
As `Builder` constructs the monoline stream piece by piece, it injects three local variables readable by any node wired into its `Tags` port:
* **`bu_i`**: 1-based index of the current piece (`1`, `2`, `3`...).
* **`bu_n`** and **`max_bu`**: Total number of pieces assembled by the node.
* **Per-piece stochastic values (`by.bu_i.R(min, max)`)**: Generates distinct yet deterministic random values for each block in the line (e.g. `\frz(by.bu_i.R(-15, 15))`).
* **Scale override priority in `shape` mode**: By default, `Builder` inserts `\p1\fscx100\fscy100` in every drawing block so style font scaling does not distort vector geometry. If you provide an explicit `\fscx`, `\fscy`, or `\fscxy` tag in `Tags`, your custom scale automatically overrides the default `100` value.

### 12.5. Synergies and Best Practices
* **Replacing `Concatenate` (merge mode) and `Union & Divide` (fusion mode):**
  * To combine multiple independent vector shapes whilst preserving their internal holes and spatial alignment, connect each shape to an `In` port on `Builder` (`In1`, `In2`, etc.).
  * For continuous multi-piece colour gradients without breaking the vector drawing mode or cutting outlines, switch `Reset \r` to `OFF` and feed the gradient via the top `Tags` port.
  * When your shapes carry upstream animations from `Functions/Animation` (such as an `\alpha` fade with `\t` keyframes), `Builder` automatically extracts the temporal transforms, deduplicates them in the line header, and guarantees that every piece animates in perfect unison.
