# Programming and Using Nodes from Code (`Script Code` and `Define Vars`)

This volume serves as a practical reference guide for calling Pyxis nodes, helper functions, and vector library shapes directly from code inside [`System/Script Code`](04%20System.md#3-node-systemscript-code-embedded-python--lua-code-execution) (Python and Lua) and from expressions or assignments inside [`Variables/Define Vars`](09%20Variables.md#2-node-variablesdefine-vars-local-variable-definition).

> [!NOTE]
> The visual anatomy, ports, and interface of `System/Script Code` are documented in [Volume 4: System](04%20System.md#3-node-systemscript-code-embedded-python--lua-code-execution). The full catalogue of context properties (`line.*`, `syl.*`, `char.*`, `word.*`, `fx.*`, `ink.*`, `prev.*`, `next.*`, `time.*`, `meta.*`, and sub-loop iterators) is detailed in [Volume 9: Variables](09%20Variables.md). This volume avoids duplicating those tables and focuses strictly on **how to programme and combine each node from code**.

### Thematic Organisation of This Volume:
* **Section 12.A — Execution Models and Scope Rules:** Real differences between `Define Vars`, `Script Code (Python)`, and `Script Code (Lua)`, tuple unpacking, and passing `None` into node functions.
* **Section 12.B — Vector Shape Library (`Shape/Library`) in Code:** Canonical lowercase naming without underscores, resolving via `shape.<name>`, `fx.shape.<name>`, `resolve_shape("shape.<name>")`, full 80-shape catalogue, and procedural composition in code.
* **Section 12.C — Complete Reference for Calling Nodes from Code:** Signatures, key arguments, return values, and practical examples across [`Basics`](#1-basics-nodes-and-ass-tag-helpers), [`Shape`](#2-shape-nodes-geometry-and-composition-in-code), [`Functions`](#3-functions-nodes-in-code), [`Time`](#4-time-nodes-and-temporal-shorthands), [`Audio`](#5-audio-nodes-and-telemetry), and [`Variables / Loops / System`](#6-variables-loops-and-system-nodes).
* **Section 12.D — Practical Recipes and Troubleshooting:** Copy-ready workflows and common mistakes when calling nodes in scripts.

---

## Section 12.A — Execution Models and Scope Rules

Before calling Pyxis functions, it helps to understand the exact capabilities of each code environment:

| Feature | `Variables/Define Vars` | `Script Code (Python)` | `Script Code (Lua)` |
| :--- | :--- | :--- | :--- |
| **Primary purpose** | Compute and inject local variables or mutate attributes before tags/outputs evaluate. | Multi-step Python logic, node composition, and multiple outputs. | Fast imperative logic on LuaJIT with native tables. |
| **Returning values** | Line-by-line or `;`-separated assignments (`x = ...`, `a, b = ...`). | Trailing expression, `result = ...`, or `outputs[1..N]` dictionary. | `return ...`, `result = ...`, or `outputs[1..N]` table. |
| **Syntax shorthands** | `2f`, `1.5r`, `2li`, `&HAABBGGRR&` hex, `~=`, Lua ternaries (`cond and A or B`) and Python ternaries (`A if cond else B`). | `2f`, `1.5r`, `2li`, full Python 3 syntax. | Standard Lua syntax; use `* frame_dur`, `* ratio`, `2 * li`. |
| **Access to node functions** | **Yes** (via automatic Python fallback; pass `None` as first argument). | **Yes** (all registered Pyxis node functions; pass `None` as first argument). | **No** (built-in helpers only; does not expose Python node functions). |
| **Access to `Shape/Library`** | `shape.<name>`, `resolve_shape("shape.<name>")`, `eval_shapes_lib_node(None, shape="<name>")`. | `fx.shape.<name>`, `resolve_shape("shape.<name>")`, `eval_shapes_lib_node(None, shape="<name>")`. | `resolve_shape("shape.<name>")` and legacy `shape_*()` aliases. |
| **Tuple unpacking / indexing** | **Right-hand indexing** (`x = func(None, ...)[0]`, as node calls serialise on assignment). | **Native unpacking** (`a, b, c = func(None, ...)`). | Only where a Lua helper returns multiple values (`polar`). |
| **Inline comments** | `# comment` and `-- comment`. | `# comment`. | `-- comment`. |

### Core Rule When Calling Node Functions (`context = None`)

Every node function exposed in `Script Code (Python)` and `Define Vars` takes `context` as its **first positional parameter** (many without a default value). Inside the script execution scope, however, **there is no global variable named `context`** (unit entities are bound directly as `syl`, `line`, `fx`, `ink`, `j`, etc.).

1. **Always pass `None` as the first positional argument** when calling a node function from code:
   ```python
   # Correct: None as first argument plus keyword parameters
   stroke = shape_stroke_node(None, shape=resolve_shape("shape.circle"), width=4.0)
   dx, dy = eval_math_node(None, category="geometry", operation="polar", angle=45, radius=80)
   ```
   ```python
   # Incorrect: raises NameError ('context' is not defined) or TypeError
   stroke = shape_stroke_node(context, shape="m 0 0 l 10 10", width=4.0)
   stroke = shape_stroke_node(shape="m 0 0 l 10 10", width=4.0)
   ```
2. **Pass coordinates and times explicitly:** When `None` is passed, the node cannot read implicit fallback metrics from a unit object. Supply `x`, `y`, `start_time`, `end_time`, `prog`, `shape`, etc. directly from context variables (`syl.center`, `syl.syl_start`, `fx.pos_x`).
3. **Extract specific tuple slots according to environment:** Several nodes return multi-output tuples (such as `shape_walker_node` or `clip_gradient_node`). In **`Script Code (Python)`** you can unpack them directly (`a, b = ...`); in **`Define Vars`**, because each assignment stringifies script return values, index the desired slot directly on the right-hand side (`[0]`, `[1]`, etc.):
   ```python
   # In Script Code (Python): native unpacking
   shp, pos_tag, frz_ang, total_len, tip_x, tip_y = shape_walker_node(None, shape=fx.shape.circle, progress=0.5)

   # In Define Vars: index the exact slot inside the expression
   shp = shape_walker_node(None, shape=shape.circle, progress=0.5)[0]
   pos_tag = shape_walker_node(None, shape=shape.circle, progress=0.5)[1]
   ```

### Context Mutation and Multiple Outputs (`outputs` / `out`)

* **Reading and updating cycle state:** In `Script Code (Python)` and `Define Vars`, mutating `fx.pos_x`, `fx.pos_y`, `fx.st`, `fx.et`, `fx.layer`, `fx.align`, or mutable attributes on `syl.*`, `char.*`, `word.*`, `line.*` synchronises those updates downstream.
* **Protected and immutable properties:** Original `.ass` ground-truth timings (`line.start_time`, `line.end_time`, `line.dur`, `line.layer`, `syl.start_time`, `syl.end_time`) and event metadata (`effect`, `actor`, `margins`, `queueid`, `queueorder`) are shielded against in-place overwriting. To shift emission timing or layer, always assign to `fx.st` / `fx.start_time`, `fx.et` / `fx.end_time`, or `fx.layer`.
* **Multiple output sockets in `Script Code`:**
  * Assigning `outputs[1]`, `outputs[2]` (or `out[1]`, `out[2]` in Python; `outputs[1]` in Lua) drives additional output sockets added to the node on the canvas.
  * The trailing expression (Python), `return` (Lua), or `result = ...` drives the main `Result` output.

---

## Section 12.B — Vector Shape Library (`Shape/Library`) in Code

All 80 vector shapes bundled in `Shape/Library` use **strictly lowercase names with zero underscores** (`circangle`, `diamond`, `heart2t`, `flower1t`, `star10t`, `diagonal13r`, etc.). Any identifier containing underscores in `shape.*` (such as `shape.rounded_corners`) or deprecated aliases (`shape.rect`, `shape.rhombus`, `shape.cross`, `shape.flower`) returns an empty string.

### Resolving and Composing Presets in Code

1. **In `Define Vars` and inline expression fields:** Use `shape.<name>` directly:
   ```python
   base = shape.circangle
   flower = shape.flower1t
   ```
2. **In `Script Code (Python)`:** Use **`fx.shape.<name>`**, **`resolve_shape("shape.<name>")`**, or **`eval_shapes_lib_node(None, shape="<name>")`**:
   ```python
   # All three return the exact same ASSDraw path for flower1t
   f1 = fx.shape.flower1t
   f2 = resolve_shape("shape.flower1t")
   f3 = eval_shapes_lib_node(None, shape="flower1t")
   ```
   > [!IMPORTANT]
   > Inside `Script Code (Python)`, bare `shape.<name>` is **not** bound in the global scope; use `fx.shape.<name>` or `resolve_shape("shape.<name>")`.
3. **In `Script Code (Lua)`:** Use **`resolve_shape("shape.<name>")`**:
   ```lua
   local shp = resolve_shape("shape.heart2t")
   return "\\p1}" .. shp
   ```
4. **Mandatory `"shape."` prefix rule in `resolve_shape()`:**
   `resolve_shape(value)` distinguishes among library presets, raw ASSDraw commands (`m ... l ...`), and plain text:
   * `resolve_shape("shape.star")` loads the 5-pointed star preset from the library.
   * `resolve_shape("star")` (**without** `"shape."`) vectorises the literal word `"star"` into glyph outlines using the active context font.
   * Lists and JSON arrays are also supported in Python/`Define Vars`: `resolve_shape(["shape.circle", "shape.star1t"])` returns a list of resolved paths.

### Complete Catalogue of All 80 Canonical Identifiers

| Family | Canonical Identifiers (`<name>`) | Count |
| :--- | :--- | :---: |
| **Shapes** | `circle`, `triangle`, `rectangle`, `circangle`, `pixel`, `pentagon`, `hexagon`, `octagon`, `diamond` | 9 |
| **Hearts** | `heart`, `heart2t`, `heartb` | 3 |
| **Shines** | `shine1t`, `shine2t`, `shine3t`, `shine4t` | 4 |
| **Specials** | `clover`, `feather`, `feather2`, `gear`, `bubble` | 5 |
| **Music** | `note1t`, `note2t`, `note3t`, `note4t` | 4 |
| **Stars** | `star`, `star1t`, `star2t`, `star3t`, `star4t`, `star5t`, `star6t`, `star7t`, `star8t`, `star9t`, `star10t` | 11 |
| **Sakura** | `sakura`, `sakura1t`, `sakura2t`, `sakura3t`, `sakura4t`, `sakura5t`, `sakura6t`, `sakura7t` | 8 |
| **Snow** | `snowflake1t`, `snowflake2t`, `snowflake3t` | 3 |
| **Flowers** | `flower1t`, `flower2t`, `flower3t`, `flower4t`, `flower5t`, `flower6t`, `flower7t`, `flower8t`, `flower9t`, `flower10t`, `flower11t`, `flower12t`, `flower13t`, `flower14t`, `flower15t`, `flower16t`, `flower17t`, `flower18t`, `flower19t`, `flower20t`, `flower21t`, `flower22t`, `flower23t`, `flower24t`, `flower25t`, `flower26t`, `flower27t`, `flower28t`, `flower29t` | 29 |
| **Geometry** | `crystal17`, `geometric10`, `diagonal13r`, `diagonal13l` | 4 |

> [!NOTE]
> **Legacy compatibility functions:** For backwards compatibility with older templates, 11 standalone functions still exist (`shape_circle()`, `shape_square()`, `shape_rectangle()`, `shape_triangle()`, `shape_rhombus()`, `shape_rounded_corners()`, `shape_pentagon()`, `shape_hexagon()`, `shape_octagon()`, `shape_star()`, `shape_heart()`). For new code, always prefer the 80 canonical identifiers via `shape.<name>`, `fx.shape.<name>`, or `resolve_shape("shape.<name>")` (for instance `circangle` instead of `rounded_corners` and `diamond` instead of `rhombus`).

### Procedural Shape Composition in Code

By chaining a library preset with `Shape/*` node functions in Python or `Define Vars`, you can scale, centre, subtract, and outline geometry without wiring extra nodes on the canvas:

```python
# Scale a flower around (0,0), subtract a centre circle, and generate a 3 px outline
base = resolve_shape("shape.flower10t")
scaled = shape_manipulator(None, drawing=base, op_mode="scale", scale_x=0.8, scale_y=0.8, mode="center")
hole = shape_manipulator(None, drawing=fx.shape.circle, op_mode="scale", scale_x=0.35, scale_y=0.35, mode="center")
ring = shape_clipper_node(None, shape_a=scaled, shape_b=hole, mode="difference", anchor="center")
outline = shape_stroke_node(None, shape=ring, width=3.0, join_mode="round")
```

---

## Section 12.C — Complete Reference for Calling Nodes from Code

This section covers all 69 canonical Pyxis nodes grouped across their 8 categories: the Python function or built-in helper that represents each node, its key arguments, its return structure, and which nodes belong strictly to graph topology.

---

### 1. `Basics` Nodes and ASS Tag Helpers

#### 1.1 Native ASS Tag Helpers (Python, Lua, and `Define Vars`)
Provide a compact alternative to `Basics/MultiTag` inside code:

| Function | ASS Output | Signature and Usage Notes |
| :--- | :--- | :--- |
| `pos(x, y)` | `\pos(x,y)` | Accepts numeric expressions or scalars. |
| `move(x1, y1, x2, y2[, t1, t2])` | `\move(...)` | Emits 4-argument `\move` when `t1, t2` are omitted. |
| `org(x, y)` | `\org(x,y)` | 2D/3D rotation and scale origin. |
| `fad(in_ms, out_ms)` | `\fad(t1,t2)` | Simple fade-in and fade-out. |
| `fade(a1, a2, a3, t1, t2, t3, t4)` | `\fade(...)` | Seven-argument multi-stage alpha fade. |
| `clip(...)` / `iclip(...)` | `\clip(...)` / `\iclip(...)` | Accepts 4 coordinates `(x1,y1,x2,y2)`, 1 drawing string `(drawing)`, or `(scale, drawing)`. |
| `c1(c)`..`c4(c)` / `color_1(c)`..`color_4(c)` | `\1c...` to `\4c...` | Accepts `#RRGGBB` or `&HBBGGRR&`. |
| `a1(a)`..`a4(a)` / `alpha(a)` | `\1a...` to `\4a...`, `\alpha...` | Accepts integers `0..255` or `&HXX&`. |
| `trans(t1, t2[, accel], tags)` / `trans(tags)` | `\t(...)` | Supports 1, 3, or 4 arguments. |
| `fscx(v)`, `fscy(v)`, `fscxy(x[, y])` | `\fscx`, `\fscy` | `fscxy(x)` sets both X and Y scale equally. |
| `frz(v)`, `frx(v)`, `fry(v)`, `fax(v)`, `fay(v)` | Rotation & shear | Degrees for `fr*`; decimal shear factor for `fa*`. |
| `bord(v)`, `shad(v)`, `blur(v)`, `an(v)` | Border, shadow, blur, alignment | Numeric scalar (`an(5)`). |
| `ass_color(r, g=None, b=None)` / `ass_alpha(a)` | `&HBBGGRR&` / `&HAA&` | Also converts `#RRGGBB` when passed as a single argument: `ass_color("#FF8800")`. |
| `random_color()` / `random_alpha()` | Random ASS colour / alpha | Returns ASS hex string ready for concatenation. |
| `tag_only(cond, tag)` | `tag` or `""` | Available in Python (`Script Code`). |

#### 1.2 `Basics/MultiTag` -> `tag_master(...)`
Generates any standard ASS tag or Dark Tag supported by `MultiTag` from Python or `Define Vars`.
* **Signature:** `tag_master(None, tag_type="pos", **kwargs)`
* **Key arguments:** `tag_type` (`"pos"`, `"move"`, `"org"`, `"fscx"`, `"fscy"`, `"frz"`, `"1c"`, `"alpha"`, `"clip"`, `"blur"`, etc.) plus the corresponding tag inputs (`x`, `y`, `x1`, `y1`, `x2`, `y2`, `t1`, `t2`, `val`, `shape`, etc.).
* **Example:**
  ```python
  t_pos = tag_master(None, tag_type="pos", x=syl.center, y=syl.middle)
  t_rot = tag_master(None, tag_type="frz", val=15)
  ```

#### 1.3 `Basics/Math` -> `eval_math_node(...)` and Math Helpers
* **Direct helpers (Python, Lua, and `Define Vars`):**
  * Bounds & mapping: `clamp(val, min_val=0.0, max_val=1.0)`, `lerp(a, b, t)`, `map_range(val, in_min, in_max, out_min, out_max)` (alias `map_value`), `ipol(t, a, b, curve="linear")`.
  * Easing curves (`t` in `[0, 1]`): `ease_in(t)`, `ease_out(t)`, `ease_in_out(t)`, `cubic_in(t)`, `cubic_out(t)`, `elastic(t)`, `bounce(t)`, `back(t)`.
  * Periodic waves: `sine_wave(t, freq=1.0, amp=1.0, offset=0.0)`, `square_wave(...)`, `triangle_wave(...)`, `sawtooth_wave(...)`.
  * Geometry & Bézier: `polar(angle_deg, dist)` returns tuple `(dx, dy)` in Python/`Define Vars` or two values in Lua (`local dx, dy = polar(45, 80)`); `bezier(t, p0, p1, p2, p3)` evaluates **scalar control values per axis** (not tuples).
* **Full node call (`ke.math`):** `eval_math_node(None, category="numeric", operation="round", **kwargs)`
  * Available categories and operations (27 operations across 5 categories):
    * `category="numeric"`: `round` (`value`, `decimal`), `clamp` (`num`, `min_val`, `max_val`, `cycle`), `rand` (`num1`, `num2`, `step`, `range`, `sign`), `factk` (`n`), `to16` (`num`), `equality` (`n1`, `n2`, `tolerance`), `between` (`num`, `n1`, `n2`).
    * `category="sequence"`: `i` (`counter`, `seq_mode`, `a`, `b`, `c`), `count` (`init`, `step`, `seq_mode`, `a`, `b`, `c`, `node_id`), `normalize` (`t`, `accel`, `shape`), `ipol` (`values`, `t`, `accel`, `shape`, `size`).
    * `category="geometry"`: `angle` (`p1`, `p2`, `p3`), `polar` (`angle`, `radius`, `get`), `distance` (`p1`, `p2`), `intersect` (`s1`, `s2`), `circle` (`p1`, `p2`, `p3`), `rotate` (`p`, `angle`, `axis`).
    * `category="algebra"`: `quadratic` (`c1`, `c2`, `c3`), `cubic` (`c1`, `c2`, `c3`, `c4`), `resolve` (`coefficients`), `equation` (`coefficients`, `reals`), `evaluate` (`coefficients`, `t`), `gauss` (`matrix`), `matrix` (`matrix_op`, `matrix_a`, `matrix_b`, `angles`, `is_row`).
    * `category="data"`: `getpair` (`val`, `defx`, `defy`), `getnumbers` (`val`), `format` (`fmt`, `values`).
* **Example:**
  ```python
  pattern = eval_math_node(None, category="sequence", operation="i", counter=syl.i, seq_mode="+,-", a=1)
  px, py = eval_math_node(None, category="geometry", operation="polar", angle=45, radius=80)
  ```

#### 1.4 `Basics/MultiRandom` -> `R*`, `by`, and `math_random_master(...)`
* **Direct deterministic helpers (Python, Lua, and `Define Vars`):**
  * `R(mn, mx[, step])`, `Rs` (signed), `Rc` (hundredths `0.01`), `Rd` (tenths `0.1`), `Rm` (thousandths `0.001`), `Rds`/`Rcs`/`Rms` (signed decimals), `Rr` (`R`), `Rstep(mn, mx, step)` (stepped discrete values), `R2d(mn, mx)` (2D vector), `Rbool(prob=50.0)`, `Rcolor(c1, c2)`, `Re("opt1,opt2,opt3")`, `Rfake(...)`, alias `rand`.
  * **Deterministic scoping via `by`:** Pass `by=by.syl`, `by=by.char`, `by=by.word`, `by=by.line`, `by=by.j`, `by=by.s` as a keyword argument to any `R*` function, or chain directly (`by.syl.R(10, 50)`, `by.line.Rcolor("#FF0000", "#0000FF")`, `by.j.Rbool(40)`).
* **Full node call:** `math_random_master(None, mode="R", min_val=None, max_val=None, step=None, options="", counter="", total=1, output_slot_index=0, iterator="", by="")` (`output_slot_index=1` produces batch lists when `total > 1`).

#### 1.5 `Basics/Text` -> `eval_text_node(...)`, `text_romaji_to_karaoke(...)`, and Helpers
* **Quick helpers (Python, Lua, and `Define Vars`):** `strip_tags(text)` and `kana(text)` (Japanese transliteration/cleaning).
* **Full `Basics/Text` node call:**
  `eval_text_node(None, operation="strip_tags", text="", ...)`
  * `operation`: `"strip_tags"`, `"uppercase"`, `"lowercase"`, `"cleanspaces"`, `"replace"` (`Search`, `Replace With`), `"substring"` (`Start`, `Length`), `"length"`, `"contains"`, `"transliteratekana"`, `"romajitokaraoke"`.
* **Direct phonetic helper:** `text_romaji_to_karaoke(None, text="sakura", duration=1200, kmode="k")` returns `"{\k400}sa{\k400}ku{\k400}ra"`.

#### 1.6 `Basics/Builder` and Pure Data/Flow Nodes
* **`Basics/Builder` -> `BuilderNode(None, items_in=None, mode="text", sub_mode="splitter", split_by="syl", source="active_unit", repeat="2", custom_text="", delim=",", shape_layout="auto", shape_split_mode="subpaths")`:** Extracts and normalises text or vector piece lists (`list[str]`) prepared for monoline stream assembly. Inside `Script Code` or `Define Vars`, per-piece tag assembly is performed directly in a `for` loop.
* **Nodes with native language equivalents (no node call needed):**
  * `Basics/Number` and `Basics/String` -> numeric literals or strings (`100`, `"\\blur2"`).
  * `Basics/Color Picker` -> `ass_color(r, g, b)` / `ass_color("#RRGGBB")` or lists of ASS hex strings.
  * `Basics/Concatenate` and `Basics/Dynamic Format` -> `f"{a}{b}"` / `",".join(items)` in Python, `a .. b` or `string.format(...)` in Lua.
  * `Basics/Only` -> `if ... else ...` conditionals or `tag_only(cond, tag)`.
  * `Basics/Once` -> `is_first` / `syl.i == 1` or `remember("key", value)` on the first iteration.

---

### 2. `Shape` Nodes (Geometry and Composition in Code)

All `Shape/*` node functions accept resolved `Shape/Library` paths (`fx.shape.*`, `shape.*`, or `resolve_shape("shape.<name>")`) and return ASSDraw geometry ready for `\p1` or `\clip(...)`.

| Node | Python Function (`Script Code` / `Define Vars`) | Key Parameters | Return Value |
| :--- | :--- | :--- | :--- |
| `Shape/Library` | `eval_shapes_lib_node(None, shape="circle")` | `shape` (canonical name or `"shape.<name>"`) | `str` (ASSDraw) |
| `Shape/Manipulator` | `shape_manipulator(None, drawing="", op_mode="scale", scale_x=1.0, scale_y=1.0, rot=0.0, offset_x=0.0, offset_y=0.0, offset_border=0.0, mode="center", density=2.0, angle_x=0.0, angle_y=0.0, angle_z=0.0, axis=None, t=1.0, skew_x=0.0, skew_y=0.0)` | `op_mode`: `"scale"`, `"rotate"`, `"offset"`, `"offset_border"`, `"perspective"`, `"skew"`, `"subdivide"`, `"invert"`; `mode` sets anchor (`"center"`, `"origin"`, `"relative"`, `"absolute"`, `"pos"`). | `str` (ASSDraw) |
| `Shape/Transform` | `shape_transform(None, drawing="", mode="inflate", t=None, ratio=1.0, inflate_mode="circle", anchor="center", angle_x=0.0, angle_y=0.0, radius=10.0, corner_mode="round", curve=None, bend_t=1.0, axis="x", target_shape="", mid_shape="", step_px=0.0)` | `mode`: `"inflate"`, `"3d_tilt"`, `"round_corners"`, `"bend"`, `"morph"`, `"resample"`. | `str` (ASSDraw) |
| `Shape/Filter` | `shape_filter(None, drawing="", mode="vertices", expr_x="x", expr_y="y", t=1.0, subdivs=0.0, rot_step=0.0, scale_step=100.0, offset_x=0.0, offset_y=0.0, anchor="center", radius_x=5.0, radius_y=5.0, seed=0)` | `mode`: `"vertices"` (evaluates per-vertex `expr_x`/`expr_y` formulas), `"echo"`, `"jitter"`. | `str` (ASSDraw) |
| `Shape/Multi` | `shape_multi(None, drawing="", mode="concentric_squares", size=100.0, width=70.0, height=50.0, px="4", bord="4", space=0.0, length=20.0, sides=6, rings=1, n_layers=25, dx=0.0, dy=0.0, parts=12, r_out=50.0, r_in=0.0, size1=100.0, size2=10.0, loop=8, separation=0.0, angle=0.0, t=1.0, anchor="center", tags="", out_mode="shape", loop_mode="shape", tip_style="Arrow", fold_w=0.0, slant=0.35, r_hole=15.0, order="normal")` | `mode`: `"concentric_squares"`, `"polygon"`, `"arrow"`, `"banner"`, `"spiral"`, `"starburst"`, etc. (see [Vol. 6](06%20Shapes.md)). | `str` (ASSDraw or tags per `out_mode`) |
| `Shape/Stroke` | `shape_stroke_node(None, shape="", width=4.0, join_mode="round", cap_mode="bezier", miter_limit=2.0)` | `join_mode`: `"round"`, `"miter"`, `"bevel"`; `cap_mode`: `"bezier"`, `"round"`, `"square"`, `"flat"`. | `str` (outlined ASSDraw) |
| `Shape/Clipper` | `shape_clipper_node(None, shape_a="", shape_b="", mode="difference", delta=0.0, subj_fill="evenodd", clip_fill="evenodd", join_type="round", end_type="closed_polygon", miter_limit=2.0, post_offset="", clean_dist=0.0, anchor="center", out_mode="shape")` | `mode`: `"difference"`, `"intersection"`, `"union"`, `"xor"`, `"offset"`, `"minkowski_sum"`, `"minkowski_diff"`; `out_mode`: `"shape"` or `"clip"`. | `str` (or `list` per `out_mode`) |
| `Shape/Union & Divide` | `shape_union_divide_node(None, drawing="", shape_b="", mode=None, anchor=None, fill_type=None, clean_self_intersect=None, index_j=None, index_d=None, order=None)` | `mode`: `"union"`, `"divide"`, `"split"`, `"extract"`, `"holes"`. | `str` or `list[str]` |
| `Shape/Concentric Borders` | `shape_concentric_borders_node(None, shape="", separation=5.0, overlap=0.5, scale=1.0, mode="hollow", loop_count=5, out_mode="shape", anchor="relative")` | `mode`: `"hollow"`, `"filled"`, `"rings"`; `anchor`: `"relative"`, `"center"`, `"pos"`, etc. | **4-Tuple:** `(shape_out, pos_str, ring_idx, total_rings)` |
| `Shape/Array` | `shape_array_node(None, particle=..., mode="grid", out_mode="loops", cols=5, rows=3, spacing_x=0.0, spacing_y=0.0, explosion=0.0, rings=3, radius=50.0, radius_step=30.0, rotate_step=0.0, count=20, turns=2.0, max_radius=100.0, angle_step=0.0, area_width=150.0, area_height=100.0, scale=1.0, t=1.0, anchor="pieces", order="79", seed=1, tags="")` | `mode`: `"grid"`, `"circle"`, `"spiral"`, `"random"`; `out_mode`: `"shape"` or `"loops"`. | **9-Tuple:** `(shape_out, pos_str, x, y, angle, a_i, a_n, col, row)` |
| `Shape/Walker` | `shape_walker_node(None, shape="", progress=1.0, start_t=0.0, mode="global", invert=False, subdivs=30, close_path=False)` | `progress` in `0.0..1.0`; `mode`: `"global"` or `"per_contour"`. | **6-Tuple:** `(shape_out, pos_tag, frz_angle, total_len, tip_x, tip_y)` |

> [!NOTE]
> **Graph-topology-only `Shape` nodes:** `Shape/Slicer` and `Shape/IMG to Shape` do not expose standalone script functions because `Slicer` drives full DAG sub-loop iterations (`s_i`, `s_n`) and `IMG to Shape` orchestrates the Potrace pipeline on disk files within `GraphEngine`. Wire those nodes on the canvas and consume their iterators or sockets from `Define Vars` or `Script Code`.

---

### 3. `Functions` Nodes in Code

| Node | Python Function or Equivalent Helper | Key Arguments and Slots (`output_slot_index`) | Return Value |
| :--- | :--- | :--- | :--- |
| `Functions/Conditioner` | `node_conditioner(None, condition=True, if_true="", if_false="")` | Also replaceable with `A if cond else B` in Python / `Define Vars`. | Selected value (`Any`) |
| `Functions/Color Gradient` | `node_color_gradient(None, prog="0.5", colors_str="#FF0000,#0000FF", total=1, accel=1.0, tag_type="\\1c", output_slot_index=0)` | `output_slot_index`: `0` = single ASS hex colour (`&H..&`); `1` = comma-separated colour list; `2` = formatted tag list (`\1c&H..&`). | `str` |
| `Functions/Tag Oscillator` | `tag_oscillator_node(None, start_time=0, end_time=1000, step_ms=200.0, trans_ms=50.0, duty_cycle=None, tags="\\frz30,\\frz-30", accel=1.0, dilat_step_ms=0.0, dilat_trans_ms=0.0, offset_seq_ms=0.0, rhythm_pattern="", mode=None, order_mode=None, output_slot_index=0)` | `output_slot_index`: `0` = full `\t(...)` sequence; `1` = active tag; `2` = keyframes list; `3` = tag list. | `str` or `list` |
| `Functions/Glitter` | `glitter_node(None, start_time=0, end_time=1000, density=1.0, mode="R", seed=0, tags="\\alpha", mins="&H00&", maxs="&HFF&", output_slot_index=0)` | `tags`, `mins`, and `maxs` accept comma-separated strings or lists; `output_slot_index=0` returns full block, `1` the first tag row. | `str` |
| `Functions/Clip Gradient` | `clip_gradient_node(None, cols=5, rows=1, angle=0, padding=0, pad_top=0, pad_bottom=0, pad_left=0, pad_right=0, overlap=0.5, order="79", out_mode="clip")` | `out_mode`: `"clip"`, `"iclip"`, or `"shape"`. | **6-Tuple:** `(output, progress, index, total, col, row)` |
| `Functions/Move Tag` | `MoveTagNode(None, mode="Trajectory", tags=None, shape="", points=None, dx=0.0, dy=0.0, dur=200, seed=0, step_px=7.5, anchor="center", t1=0, t2=None, accel=1.0)` | `mode`: `"Trajectory"`, `"Waypoints"`, `"Jitter"`. | `str` (ASS `\t(...)` block) |
| `Functions/Move Text` | `MoveTextNode(None, text="", tags=None, dx=0.0, dy=0.0, ox=0.0, oy=0.0, trajectory=None, anchor="center", shape="", points=None, step_px=7.5, t1=0.0, t2=None, accel=1.0)` | Shifts layout position without resetting `\pos` via `\fsp` spacers and `\N` breaks. | `str` (composite ASS block) |
| `Functions/Tag Manipulator` | `TagManipulatorNode(None, mode="Invert", tags="", target_tag="")` | `mode`: `"Invert"`, `"Reset"`, `"Extractor"`. | `str` or scalar |
| `Functions/Animation` | `AnimationNode(None, frames="", step_ms=41.7, start_time="", end_time="", mode="fbf", alpha_tag="\\alpha", order="sequential", output_slot_index=0, anchor="relative", base="0")` | `frames`: Python list or delimited string; `mode`: `"fbf"` or `"alpha"`; `output_slot_index`: `0` = active shape/tag, `1` = frame index, `2` = processed list. | `str`, `int`, or `list` |
| `Functions/Text on Path` | `text_on_path_node(None, shape="", mode="Center", offset=0.0, extra_angle=0.0, subdivs=30)` | `offset` in `0.0..1.0` along the vector path. | **6-Tuple:** `(tag_out, pos_tag, frz_tag, x, y, length)` |
| `Functions/IMG to pixels` | `particle_image_node(None, image_path="", particle_shape="", frame="1", step=2, alpha_threshold=128, scale=1.0, anchor="center", order="79", frame_idx=None)` | Samples image pixels or GIF frames. | **6-Tuple:** `(abs_x, abs_y, color_ass, alpha_ass, shape_str, total_pixels)` |

**Direct equivalents for the remaining `Functions` nodes:**
* `Functions/Polar to Cartesian` -> **`polar(angle_deg, dist)`** (returns `(dx, dy)`; add to `fx.pos_x` and `fx.pos_y`).
* `Functions/Bezier Curve` -> **`bezier(t, p0, p1, p2, p3)`** called separately per coordinate axis.
* `Functions/Interpolator` -> **`lerp(a, b, t)`**, **`ipol(t, a, b, curve)`**, and **`map_range(val, in_min, in_max, out_min, out_max)`**.
* `Functions/Text to Shape` -> **`resolve_shape(text)`** passing plain text **without** the `"shape."` prefix (e.g. `resolve_shape(syl.text_stripped)`).
* `Functions/Particles` -> Graph-topology-only particle loop generator (`p_i`, `p_n`).

---

### 4. `Time` Nodes and Temporal Shorthands

Pyxis binds dynamic timing objects across `Define Vars`, `Script Code (Python)`, and `Script Code (Lua)`:

#### 4.1 Phase Stagger Shorthands and Numeric Macros
* **Scalable modifier objects:** `li` (Lead In), `lo` (Lead Out), `m1` (Middle 1), `m2` (Middle 2), `l1` (Loop 1), `l2` (Loop 2).
* **Compact syntax (Python and `Define Vars`):** `2li` or `2 * li` evaluates a `2` ms Lead In step; `li()` uses the default (`40` ms); `li(60)` uses `60` ms per unit; `li + 150` adds a fixed offset. In Lua, write multiplication explicitly (`2 * li` or `li(60)`).
* **Unit macros (Python and `Define Vars`):** `10f` expands to `10 * frame_dur` (~417.08 ms at 23.976 fps); `1.5r` expands to `1.5 * ratio` (`m_i / m_n` or `j / maxj` progress).
* **Explicit functions (matching the 6 stagger nodes):**
  * `time_lead_in(delay=40, base=None)` / `time_lead_out(delay=40, base=None)`
  * `time_middle_1(delay=30, base=None)` / `time_middle_2(delay=30, base=None)`
  * `time_loop_1(delay=30, mode="leadin", base=None)` / `time_loop_2(delay=30, mode="leadin", base=None)`

#### 4.2 Temporal Utilities, `Retime`, and `Synced`
* **`Time/Duration`:** `duration(syl)` or `time_duration(None, start_time=t1, end_time=t2)` -> duration in ms (`float`).
* **`Time/Offset`:** `time_offset(None, base=t, offset_ms=-150)` -> `t + offset_ms`.
* **`Time/Ipol`:** `time_ipol(None, dur_ms=1000, points="0,100,200", accel=1.0)` -> segmented ms interval string/brackets.
* **`Time/Parse ASS Time`:** `parse_ass_time("0:00:01.55")` or `time_parse_ass(None, ass_time="0:00:01.55")` -> `1550` (`int`).
* **`Time/Format ASS Time`:** `format_ass_time(1550)` or `time_format_ass(None, time=1550)` -> `"0:00:01.55"`.
* **`Time/Time to Frame`:** `time_to_frame(ms, fps=23.976)` or `time_to_frame_node(None, time=ms, frame_dur=frame_dur, mode="Round", source="Custom")` (`mode`: `"Ceil"`, `"Floor"`, `"Round"`).
* **`Time/Frame to Time`:** `frame_to_time_node(None, frames=24, frame_dur=frame_dur, format="MS", source="Custom")` (`format`: `"MS"`, `"HMS"`, `"SEC"`).
* **`Time/Retime`:** `RetimeNode(None, phase="abs", tags="\\fscx150", offset_in=0, offset_out=0, accel=1.0, custom_start=100, custom_end=500)` (when calling directly with `None`, use `phase="abs"` with `custom_start`/`custom_end`, or compose `trans(syl.syl_start, syl.syl_end, ...)` from unit properties).
* **`Time/Synced`:** Use the injected **`sync`** object directly (`sync.next`, `sync.prev`, `sync.order_next`, `sync.style_next`, `sync.actor_next`, `sync.effect_next`, `sync.layer_next` and their `*_prev` counterparts) or `calculate_sync_gap(maxgap=2000)`. Calling `time_synchronized_extra_node` requires an active line context inside the running graph to compute multi-line offsets automatically.

---

### 5. `Audio` Nodes and Telemetry

#### 5.1 Telemetry Helpers (Python, Lua, and `Define Vars`)
Return normalised energy values ready to drive scale, blur, or colour animations at any timestamp:
* **`audio_rms(start_ms=None, end_ms=None, gain=1.0, audio_path=None)` -> `float`:** Root-mean-square energy within the interval.
* **`audio_peak(start_ms=None, end_ms=None, gain=1.0, audio_path=None)` -> `float`:** Peak amplitude within the interval.
* **`audio_band(start_ms=None, end_ms=None, min_hz=20.0, max_hz=250.0, gain=1.0, audio_path=None)` -> `float`:** Energy isolated inside a frequency band (for example sub-bass `20`–`150` Hz).
* **`audio_fft(start_ms=None, end_ms=None, num_bands=16, min_hz=20.0, max_hz=16000.0, gain=1.0, audio_path=None)` -> `list[float]`:** Spectral amplitudes across `num_bands` logarithmic frequency bands.

> [!TIP]
> If a master audio track has already been assigned in the preview panel or via `Audio/Modulator` / `Audio/Waveform`, you may omit `audio_path` (or pass `""`/`None`) so Pyxis resolves the project default audio source automatically.

#### 5.2 Full Audio Nodes (`Script Code (Python)` and `Define Vars`)
* **`Audio/Modulator`:** `audio_modulator_node(None, audio_path="", tag_name="fscy", min_val="100", max_val="160", gain="1.0", step_ms="41.7", smoothing="0.2", mode="rms", min_hz="20", max_hz="250", start_time="", end_time="", output_slot_index=0)`
  * `output_slot_index`: `0` = `\t(...)` sequence, `1` = current scalar value, `2` = values array, `3` = average RMS.
* **`Audio/Waveform`:** `audio_waveform_node(None, audio_path="", mode="oscilloscope", width="400", height="60", samples="32", gain="1.0", thickness="2", min_hz="20", max_hz="16000", scale="1.0", smoothing="0.2", start_time="", end_time="", anchor="center", output_slot_index=0)`
  * `output_slot_index`: `0` = ASSDraw path, `1` = `\pos` tag, `2` = X array, `3` = Y array, `4` = bands array.

---

### 6. `Variables`, `Loops`, and `System` Nodes

* **`Variables/Memory` -> `remember(key, value)` and `recall(key, default="")`:**
  Available directly in Python, Lua, and `Define Vars` during graph execution to store initial positions, first-pass random colours, or cross-iteration state (in `Define Vars`, `remember` also accepts an optional third boolean condition: `remember("c0", random_color(), is_first)`). The node function `memory_node(None, ...)` is also registered.
* **`Variables/Define Vars`, `Variables/Get Var`, `Variables/Sys Var`:**
  Inside `Script Code` or `Define Vars`, read and assign variables directly by identifier (`my_angle = syl.i * 15`, `fx.pos_x = syl.center + 10`) without needing to invoke `get_var_node`, `sys_var_node`, or `define_vars_node`.
* **`Loops/Main Loop`, `Loops/MaxLoop`, `Loops/Module`:**
  Control how many lines, units, or passes the DAG emits and cannot replace graph iteration by calling `main_loop_node(None)` in code. Read `i`, `n`, `j`, `maxj`, `ratio` (`module`), and preserved source tags (`syl.tags` / `line.tags` when `preserve_tags` is enabled on `Main Loop`) directly instead. Likewise, every line exposes the canonical `line.<prop>_org` (`l.<prop>_org`) set using style property names and initial ASS tag values from the line (with automatic fallback to `styleref`, excluding karaoke timings and `\t(...)`): `color1_org`..`color4_org`, `alpha_org`, `alpha1_org`..`alpha4_org`, `fontname_org`, `fontsize_org`, `scale_x_org`, `scale_y_org`, `spacing_org`, `bold_org`, `italic_org`, `underline_org`, `strikeout_org`, `encoding_org`, `q_org`, `align_org`, `frz_org`, `frx_org`, `fry_org`, `fax_org`, `fay_org`, `pos_org`, `org_org`, `outline_org`, `xbord_org`, `ybord_org`, `shadow_org`, `xshad_org`, `yshad_org`, `blur_org`, `be_org`, `fad_org`, `clip_org`, `iclip_org`; together with the Dark Tag `!line.<prop>!` (e.g. `\1c!line.color4!`, `\bord!line.shadow!`, `\13c!line.color1!`) to inject any preserved property into any tag of the ASS template.
* **`System/Output`, `System/Previewer`, `System/Script Code`, `System/Benchmark Math`:**
  Structural sink, WASM browser preview, script host, and benchmark nodes that always operate as canvas blocks.

---

## Section 12.D — Practical Recipes (`Define Vars` + `Script Code`)

### Recipe 1 — `Define Vars`: Tuple Indexing and Library Shapes
Compute procedural geometry in a single `Define Vars` pass so downstream `MultiTag` or string templates can consume the variables:

```python
-- Canonical library shape (no underscores) and 3 px vector outline
flower_base = shape.flower10t
flower_outline = shape_stroke_node(None, shape=flower_base, width=3.0, join_mode="round")

-- Direct indexing of Clip Gradient slots 0 (clip) and 1 (progress) (cols=4, rows=1)
clip_strip = clip_gradient_node(None, cols=4, rows=1, angle=15, out_mode="clip")[0]
clip_prog = clip_gradient_node(None, cols=4, rows=1, angle=15, out_mode="clip")[1]

-- Interpolated gradient colour driven by the active strip progress
strip_colour = node_color_gradient(None, prog=clip_prog, colors_str="#FF4E50,#FC913A,#F9D423", tag_type="\\1c", output_slot_index=0)
```

### Recipe 2 — `Script Code (Python)`: Procedural Badge with Multiple `outputs`
Combines `resolve_shape("shape.circangle")`, `shape_manipulator`, `shape_clipper_node`, and `node_color_gradient`, emitting the geometry on `Result` and tags on `outputs[1]`:

```python
# Scale a rounded rectangle to the syllable visual ink bounds + padding
base = resolve_shape("shape.circangle")
sx = (ink.width + 24.0) / 100.0
sy = (ink.height + 14.0) / 100.0
badge = shape_manipulator(None, drawing=base, op_mode="scale", scale_x=sx, scale_y=sy, mode="center")

# Punch out a star in the centre using Clipper2 boolean difference
star = shape_manipulator(None, drawing=fx.shape.star1t, op_mode="scale", scale_x=0.22, scale_y=0.22, mode="center")
cutout = shape_clipper_node(None, shape_a=badge, shape_b=star, mode="difference", anchor="center")

# Colour gradient across syllables
prog = (syl.i - 1) / max(1, syl.n - 1)
bg_col = node_color_gradient(None, prog=prog, colors_str="#1E3C72,#2A5298,#E94057", output_slot_index=0)

outputs[1] = pos(syl.center, syl.middle) + an(5) + c1(bg_col) + bord(0)
result = cutout
```

### Recipe 3 — `Script Code (Python)`: Kinetic Orbit, Audio Reactivity, and Stagger Timing
Computes an orbital offset around each syllable modulated by low-frequency audio energy and staggered lead-in/out windows:

```python
# Staggered timing offsets
t_in = syl.i * 35 - 200
fx.st = line.start_time + t_in
fx.et = line.end_time + 180

# Deterministic polar displacement per syllable + bass energy (20-160 Hz)
ang = R(0, 360, by=by.syl) + (j * 25)
radius = 18.0 + audio_band(syl.start_time, syl.end_time, min_hz=20, max_hz=160, gain=1.2) * 35.0
dx, dy = polar(ang, radius)

osc = tag_oscillator_node(
    None,
    start_time=syl.syl_start,
    end_time=syl.syl_end,
    step_ms=120,
    trans_ms=60,
    tags="\\fscx115\\fscy115,\\fscx100\\fscy100",
    output_slot_index=0
)

move(syl.center + dx, syl.middle + dy, syl.center, syl.middle, 0, abs(t_in)) + osc
```

### Recipe 4 — `Script Code (Lua)`: Persistent Per-Character Shimmer with `resolve_shape`
Uses `remember` / `recall` in Lua alongside `resolve_shape("shape.star4t")` and `by.char`:

```lua
local key = "col_" .. tostring(char.i)
local col = recall(key, "")
if col == "" then
    col = by.char.Rcolor("#FFE259", "#FFA751")
    remember(key, col)
end

local shp = resolve_shape("shape.star4t")
local scale = math.floor(lerp(40, 120, (char.i - 1) / math.max(1, char.n - 1)))

outputs[1] = pos(char.center, char.middle) .. an(5) .. c1(col) .. fscxy(scale) .. fad(120, 180)
return shp
```

---

## Section 12.E — Common Mistakes and Diagnostics When Calling Nodes in Code

| Symptom / Error | Root Cause | Direct Fix |
| :--- | :--- | :--- |
| `[Err Python Script: name 'context' is not defined]` | Passed `context` as the first argument to a node function. | Always pass **`None`** as the first argument (`eval_math_node(None, ...)`). |
| `TypeError: missing 1 required positional argument: 'context'` | Omitted the first positional argument when calling with keyword arguments only. | Prepend **`None`** before keyword arguments: `shape_manipulator(None, drawing=..., op_mode="scale")`. |
| `resolve_shape("star")` draws the letters `"star"` instead of a star shape | Missing the mandatory `"shape."` prefix. | Use **`resolve_shape("shape.star")`**; without `"shape."`, Pyxis vectorises the text using the active font. |
| `shape.rounded_corners`, `shape.rhombus`, `shape.rect`, or `shape.flower` return `""` | Used deprecated or snake_case names that do not exist among the 80 presets. | Use canonical names without underscores: **`circangle`**, **`diamond`**, **`rectangle`**, **`flower1t`**..**`flower29t`**. |
| `NameError: name 'shape' is not defined` inside `Script Code (Python)` | Top-level `shape` lives in `Define Vars`; inside `Script Code` it is exposed on `fx` or via `resolve_shape`. | In `Script Code (Python)`, use **`fx.shape.<name>`** or **`resolve_shape("shape.<name>")`**. |
| `[Err Lua Script: attempt to call a nil value]` calling `shape_stroke_node` or `tag_master` | Lua only exposes built-in helpers and not Python `NODE_REGISTRY` node functions. | Switch the `Script Code` node language to **Python** or move the call into **`Define Vars`**. |
| `TypeError: float() argument must be a real number, not 'tuple'` in `bezier(...)` | Passed `(x, y)` tuples instead of scalar numbers to `bezier(t, p0, p1, p2, p3)`. | Compute each axis independently: `bx = bezier(t, x0, x1, x2, x3)` and `by_y = bezier(t, y0, y1, y2, y3)`. |
| Concatenating `shape_walker_node` or `clip_gradient_node` prints a tuple `('...', ...)` | Those nodes return multi-slot tuples (4, 6, or 9 elements). | Unpack the tuple (`shp, pos_t, ang, ... = shape_walker_node(...)`) or index the desired slot (`[0]`, `[1]`). |
