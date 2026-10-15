# Shapes

The **Shape** category contains nodes for generating, ingesting, manipulating, and geometrically segmenting vector drawings in ASSdraw format (`m`, `l`, `b`, `s`, `p`, `c`) and clipping masks (`\clip`, `\iclip`).

### Thematic Volume Organisation:
* **Section 6.A — Vector Generation, Tracing, and Ingestion:** `Shape/Library` (§1), `Shape/Walker` (§7), `Shape/Stroke` (§8), `Shape/IMG to Shape` (§12).
* **Section 6.B — Meshes, Matrices, and Concentric Patterns:** `Shape/Slicer` (§2), `Shape/Concentric Borders` (§6), `Shape/Array` (§11), `Shape/Multi` (§13).
* **Section 6.C — Boolean Algebra and Non-Linear Transforms:** `Shape/Manipulator` (§3), `Shape/Filter` (§4), `Shape/Transform` (§5), `Shape/Union & Divide` (§9), `Shape/Clipper` (§10).

---

## 1. Node `Shape/Library` (Geometric Primitives)

* **Canonical Category:** `Shape` (UI: *Shape / Library*)
* **Purpose:** Emits precalculated parametric geometric primitives normalised within a base $[0, 100]$ bounding box and centred at the local Cartesian origin `(0, 0)`.

``

### 1.1. Interactive Preview Card and Shortcuts
* **Live Vector Rendering:** The node body includes a live **Preview Card** rendering the vector silhouette of the selected shape in real time.
* **Modal Catalogue Shortcuts:**
  * Direct click on the graphical Preview Card.
  * Double-click anywhere on the node body.
  * Click on the shape button/pill in the header.
  Any of these actions opens the **Visual Vector Primitives Modal Catalogue**, allowing users to explore all 80 shapes by category or via instant text filtering.

### 1.2. Predefined Shape Catalogue (`shape`)
The catalogue comprises 80 precalculated vector primitives normalised within a base $[0, 100]$ bounding box, classified into 10 canonical categories using standard lowercase identifiers:
* **`shapes` (9):** `circle`, `triangle`, `rectangle`, `circangle`, `pixel`, `pentagon`, `hexagon`, `octagon`, `diamond`.
* **`hearts` (3):** `heart`, `heart2t`, `heartb`.
* **`shines` (4):** `shine1t`, `shine2t`, `shine3t`, `shine4t`.
* **`specials` (5):** `clover`, `feather`, `feather2`, `gear`, `bubble`.
* **`music` (4):** `note1t`, `note2t`, `note3t`, `note4t`.
* **`stars` (11):** `star`, `star1t`, `star2t`, `star3t`, `star4t`, `star5t`, `star6t`, `star7t`, `star8t`, `star9t`, `star10t`.
* **`sakura` (8):** `sakura`, `sakura1t`, `sakura2t`, `sakura3t`, `sakura4t`, `sakura5t`, `sakura6t`, `sakura7t`.
* **`snow` (3):** `snowflake1t`, `snowflake2t`, `snowflake3t`.
* **`flowers` (29):** `flower1t` to `flower29t` (daisies, chrysanthemums, sunflowers, mandalas, and multilayered floral vectors).
* **`geometry` (4):** `crystal17`, `geometric10`, `diagonal13r`, `diagonal13l`.

### 1.3. Output Ports (*Outputs*)
1. **`[1.1] Shape`:** Emits the ASSdraw vector code centred at `(0, 0)` ready to feed `System/Output (Return)` or downstream vector processing nodes (`Stroke`, `Manipulator`, `Slicer`).

### 1.4. Practical Production Example
* **Vector Icon Emission with Scale and Rotation:**
  Connecting `Shape` to the `Return` socket of `System/Output` with `category: stars`, `shape: star`:
  
  ```
  [Shape/Library: star] ──► Shape ──► Return ──► [System/Output]
  ```
  
  In a tag node wired to `System/Output (Tags)`:
  ```
  {\p1\pos(syl.center, syl.middle)\frz(i * 45)\fscx75\fscy75\1c&H00FFFF&\bord1\3c&H0055AA&}
  ```
  The vector drawing centred at `(0, 0)` renders directly over the syllable centroid at 75% scale, rotated by $45^\circ \cdot i$.

---

## 2. Node `Shape/Slicer` (Morphological Slicing and Segmentation)

* **Canonical Category:** `Shape` (UI: *Shape*)
* **Purpose:** Slices a vector shape or glyph into independent geometric fragments, cells, or pieces using *Clipper2*-accelerated boolean operations. Input fields dynamically reconfigure according to the selected slicing mode.

![Shape/Slicer](img/slicer.png)

---

### 2.1. Header, Mode Combos, and Modal Mesh Gallery (`pyxis-mesh-picker-dialog`)
1. **`[1.1] Slicer`:** Node title identifier.
2. **`[1.2] Slicing Mode` (`[Grid 田]` — Mesh Picker Modal Shortcut):**
   * **Opening Shortcut:** A direct click on this header button/pill opens the **Visual Slicing Patterns and Mesh Gallery** (`pyxis-mesh-picker-dialog`).
   * **Interactive SVG Preview Cards:** Each of the 23 segmentation engines is rendered on a visual card featuring a high-definition dynamic SVG vector icon illustrating the exact slicing topology (honeycomb for `hex`, triangular lattice for `tri`, 3D isometric cubes for `rhombille`, Bézier waves for `bez`, PCB traces for `circuit`, organic tessellations for `voronoi`, etc.).
   * **Structured Categorisation by Mesh Family:**
     * **`Standard Grid`:** Uniform 1D/2D rectangular grid (`Grid 1D/2D`).
     * **`Polygonal & Organic`:** Polygonal and biological lattices (`hex`, `tri`, `dia`, `voronoi`, `delaunay`, `kagome`, `rhombille`, `octagon`).
     * **`Technology & Networks`:** Radial networks, circuits, and puzzle pieces (`ring`, `jigsaw`, `circuit`, `ray`, `web`).
     * **`Architecture & Walls`:** Masonry bonds, architectural blocks, and compositions (`brick`, `mondrian`, `ashlar`, `quad`, `pattern`).
     * **`Waves & Art`:** Wavy patterns and modular curves (`herringbone`, `truchet`, `scallop`, `bez`).
   * **Reactive Search Filter:** Real-time search bar for rapid filtering by name or technical description.
   * **1-Click Dynamic Reconfiguration:** Selecting any pattern immediately updates the algorithm, switches input sockets and properties in the node body (e.g. from `Cols/Rows` to `Cell Size/Seed/Jitter`), and recalculates node dimensions on the canvas.
3. **`[1.3] Output Mode` (`[Loops]`):** Toggles evaluation behaviour between per-piece iterator loop mode (`Loops`) and simultaneous list/array emission (`Single / Array`).

---

### 2.2. Universal Parameters and Global Controls
These parameters and configuration buttons apply across all slicing modes:

1. **`[2.1] Shape`:** Vector ASSdraw path or text glyph to slice. If unwired and empty, automatically retrieves the active context's shape (syllable, word, or line).
2. **`[2.2] Text Scale`:** Pre-scaling factor applied to the input shape prior to subdivision and slicing.
3. **`[2.3] Pre-Offset`:** Perimeter offset (*dilation / erosion*) applied to original contours before boolean slicing.
4. **`[2.4] Anchor` (Anchor Point, Positioning, and Injected Origin):** Selector button defining the local coordinate system of each piece and how `\pos(x,y)` and `\org(x,y)` tags are injected into context:
   * **`Piece` (`Pieces`):** 
     * **Position (`\pos`):** Re-anchored to the absolute screen centroid of the piece (`pos_x = parent_x + cx`, `pos_y = parent_y + cy`).
     * **Injected Origin (`\org`):** Injects `\org(pos_x, pos_y)` matching the centroid of the piece itself.
     * **Vector Path:** Re-centred at local origin `(0, 0)` via perimeter offset `(-cx, -cy)`. Allows each fragment to rotate and scale around its own centre of mass independently.
   * **`Relative`:** 
     * **Position (`\pos`):** Retains parent element position (`parent_x`, `parent_y`).
     * **Injected Origin (`\org`):** Injects `\org(parent_x, parent_y)` at parent centroid.
     * **Vector Path:** Preserves original relative coordinates relative to parent origin without re-centring the piece.
   * **`Parent Org`:** 
     * **Position (`\pos`):** Positioned at piece centroid (`pos_x = parent_x + cx`, `pos_y = parent_y + cy`).
     * **Injected Origin (`\org`):** Injects `\org(parent_x, parent_y)` forced at parent origin.
     * **Vector Path:** Re-centred at local origin `(0, 0)`. Allows all individual fragments to rotate in orbit around the collective centre of the original word/syllable.
   * **`Pos`:** 
     * **Position (`\pos`):** Positioned at piece centroid (`pos_x = parent_x + cx`, `pos_y = parent_y + cy`).
     * **Injected Origin (`\org`):** Does not inject `\org` tag (`has_org = False`), allowing renderer to use standard `\an` alignment point.
     * **Vector Path:** Re-centred at local origin `(0, 0)`.
   * **`Absolute`:** 
     * **Position (`\pos`):** Retains parent coordinates (`parent_x`, `parent_y`).
     * **Injected Origin (`\org`):** Does not inject `\org` tag (`has_org = False`).
     * **Vector Path:** Absolute screen coordinates are baked directly into the ASSdraw code via offset `(+parent_x, +parent_y)`.
5. **`[2.5] Out:` (Vector Output Mode):** Format selector for data emitted on the `Piece` port:
   * **`Shape`:** Emits raw ASSdraw code of the cut fragment (`m ... l ... b ...`).
   * **`\clip`:** Emits rectangular or polygonal ASS clipping tag `\clip(m ...)`.
   * **`\iclip`:** Emits inverted ASS clipping tag `\iclip(m ...)`.
6. **`[2.6] Bleed`:** Perimeter overlap between adjacent fragments. Dilates each piece to eradicate visual hairline rendering seams between touching pieces.
7. **`[2.7] Order:` (Spatial Piece Ordering):** 9-point numpad iteration order selector:
   * **`79 (TL->BR)`:** Top-Left to Bottom-Right.
   * **`97 (TR->BL)`:** Top-Right to Bottom-Left.
   * **`13 (BL->TR)`:** Bottom-Left to Top-Right.
   * **`31 (BR->TL)`:** Bottom-Right to Top-Left.
   * **`71 (TL->BL)`:** Vertical descending column by column (Left to Right).
   * **`17 (BL->TL)`:** Vertical ascending column by column (Left to Right).
   * **`39 (BR->TR)`:** Vertical ascending column by column (Right to Left).
   * **`5 (Centre)`:** Radial expansion from original shape centroid to outer edges.
8. **`[2.8] s_i, s_n`:** Iteration variables exposed in footer (`s_i` = active piece index $[1 \dots N]$, `s_n` = total pieces generated).

---

### 2.3. Output Ports (*Outputs*)
1. **`[3.1] Piece`:** ASSdraw vector code or `\clip`/`\iclip` tag for the active piece iteration.
2. **`[3.2] X`:** Horizontal Cartesian coordinate $X$ of piece centroid.
3. **`[3.3] Y`:** Vertical Cartesian coordinate $Y$ of piece centroid.
4. **`[3.4] Col`:** Spatial column index assigned to piece in mesh.
5. **`[3.5] Row`:** Spatial row index assigned to piece in mesh.

---

### 2.4. Mode-Specific Inputs and Parameters

#### 1. `Grid 1D/2D` Mode
* **`Cols`:** Horizontal division count.
* **`Rows`:** Vertical division count.
* **`Angle`:** Cutting grid angular tilt in degrees.
* **`Bleed`:** Overlap bleed between cells.
* **`Accel X` / `Accel Y`:** Non-linearity exponent across horizontal/vertical axes.
* **Universal parameters:** `Text Scale` / `Pre-Offset` / `Anchor` / `Out:` / `Order:`.

#### 2. `Hex` (Hexagonal) Mode
* **`Radius`:** Circumscribed radius of regular honeycomb hexagons.
* **Universal parameters:** `Text Scale` / `Pre-Offset` / `Anchor` / `Out:` / `Bleed` / `Order:`.

#### 3. `Tri` (Triangular) Mode
* **`Radius`:** Half-side length of equilateral triangles.
* **Universal parameters:** `Text Scale` / `Pre-Offset` / `Anchor` / `Out:` / `Bleed` / `Order:`.

#### 4. `Dia` (Diamond / Rhombus) Mode
* **`Radius`:** Major and minor semi-diagonal of rhombus mesh.
* **Universal parameters:** `Text Scale` / `Pre-Offset` / `Anchor` / `Out:` / `Bleed` / `Order:`.

#### 5. `Rings` (Concentric Rings) Mode
* **`Ring Width`:** Radial width in pixels per concentric ring.
* **Universal parameters:** `Text Scale` / `Pre-Offset` / `Anchor` / `Out:` / `Bleed` / `Order:`.

#### 6. `Ray` (Radial Rays) Mode
* **`Step Angle` / `Rays`:** Angular step in degrees or radial sector count from centre to perimeter.
* **Universal parameters:** `Text Scale` / `Pre-Offset` / `Anchor` / `Out:` / `Bleed` / `Order:`.

#### 7. `Voronoi` (Voronoi Crystals) Mode
* **`Cell Size`:** Average cell dimension produced by stochastic site distribution.
* **Universal parameters:** `Text Scale` / `Pre-Offset` / `Anchor` / `Out:` / `Bleed` / `Order:`.

#### 8. `Delaunay` (Low-Poly) Mode
* **`Cell Size`:** Vertex density and spacing for irregular Delaunay triangulation.
* **Universal parameters:** `Text Scale` / `Pre-Offset` / `Anchor` / `Out:` / `Bleed` / `Order:`.

#### 9. `Brick` (Bricks) Mode
* **`Size X` (Width) / `Size Y` (Height):** Pixel width and height per brick block.
* **Universal parameters:** `Text Scale` / `Pre-Offset` / `Anchor` / `Out:` / `Bleed` / `Order:`.

#### 10. `Ashlar` (Irregular Stonework) Mode
* **`Min Width` / `Max Width`:** Random width range for stone blocks.
* **`Row Height`:** Fixed height per stone row.
* **Universal parameters:** `Text Scale` / `Pre-Offset` / `Anchor` / `Out:` / `Bleed` / `Order:`.

#### 11. `Jigsaw` (Puzzle Pieces) Mode
* **`Piece Size`:** Base dimension for jigsaw puzzle pieces with Bézier tabs and sockets.
* **Universal parameters:** `Text Scale` / `Pre-Offset` / `Anchor` / `Out:` / `Bleed` / `Order:`.

#### 12. `Bez` (Bézier Waves) Mode
* **`Wave Size`:** Cell size bounded by sinusoidal Bézier curves with organic perturbations.
* **Universal parameters:** `Text Scale` / `Pre-Offset` / `Anchor` / `Out:` / `Bleed` / `Order:`.

#### 13. `Circuit` (Electronic PCB) Mode
* **`Grid Size`:** PCB grid pitch.
* **`Trace Width`:** Conductor trace width.
* **`Via Prob`:** Circular pad insertion probability.
* **Universal parameters:** `Text Scale` / `Pre-Offset` / `Anchor` / `Out:` / `Bleed` / `Order:`.

#### 14. `Truchet` (Truchet Tiles) Mode
* **`Tile Size`:** Square tile dimension for tangent circular arc patterns.
* **Universal parameters:** `Text Scale` / `Pre-Offset` / `Anchor` / `Out:` / `Bleed` / `Order:`.

#### 15. `Pattern` (Custom Pattern) Mode
* **`Pattern Shape`:** External ASSdraw vector used as repeated cutting stamp.
* **`Size X` / `Size Y`:** Pattern repetition spacing.
* **Universal parameters:** `Text Scale` / `Pre-Offset` / `Anchor` / `Out:` / `Bleed` / `Order:`.

#### 16. `Mondrian` (Neoplastic Subdivision) Mode
* **`Min Size`:** Minimum indivisible rectangle dimension.
* **`Chaos`:** Recursive splitting probability across $X$ and $Y$.

#### 17. `Herringbone` (Herringbone Zig-Zag) Mode
* **`Length` / `Width`:** Block length and width interlocking at $90^\circ$.

#### 18. `Kagome` (Trihexagonal) Mode
* **`Radius`:** Radius of traditional trihexagonal lattice of interlaced triangles and hexagons.

#### 19. `Rhombille` (3D Isometric Cubes) Mode
* **`Radius`:** Radius of $60^\circ$ rhombi simulating 3D axonometric cubes.

#### 20. `Octagon` (Octagonal Tile) Mode
* **`Radius`:** Dimension of octagons paired with junction squares.

#### 21. `Scallop` (Fish Scales) Mode
* **`Radius`:** Radius and curvature arc of overlapping semicircular scales.

#### 22. `Web` (Spiderweb) Mode
* **`Cols` (Rings) / `Rows` (Rays):** Polygonal concentric rings and radial spokes.
* **`Chaos`:** Stochastic nodal irregularity.

#### 23. `Quad` (Quadtree) Mode
* **`Min Size`:** Minimum cell dimension in recursive quadtree partitioning.
* **`Chaos`:** Splitting probability threshold.

### 2.5. Practical Production Example
* **Stochastic Voronoi Shatter Effect:**
  Routing the syllable outline into `Shape/Slicer` configured with `mode: voronoi`, `cell_size: 25`, and `anchor: pieces`:

  ```
  [System/Input: Syl Shape] ──► Shape ──► [Shape/Slicer: voronoi, anchor=pieces]
                                                ├──► Piece ──► Return ──► [System/Output]
                                                └──► (s_i, s_n in context)
  ```

  In a tag node wired to `System/Output (Tags)`:
  ```
  {\p1\pos(syl.center, syl.middle)\t(0, 350, \frz(s_i * 20)\fscx0\fscy0\alpha&HFF&)}
  ```
  Each Voronoi piece rotates around its individual centroid and collapses progressively with an angular deflection proportional to `s_i`, maintaining the local anchor without shifting the overall drawing origin.

---

## 3. Node `Shape/Manipulator` (Spatial Transformation and Deformation)

* **Canonical Category:** `Shape` (UI: *Shape*)
* **Purpose:** Applies anamorphic scaling, morphological perimeter offsets, Cartesian translation, 3D matrix rotations, Bézier resampling, and specular reflection over vector paths. Body fields dynamically reconfigure per mode.

![Shape/Manipulator](img/manipulator.png)

---

### 3.1. Header and Outputs
1. **`[1.1] Shape` (Output):** Emits modified ASSdraw vector path following geometric transformation.
2. **`[1.2] Mode`:** Selector toggling among 8 spatial manipulation modes (`Scale`, `Borders`, `Deform`, `Position`, `Redraw`, `3D Rotate`, `Reflect`, `Matrix`).

---

### 3.2. Common Universal Parameters
1. **`Shape / Text`:** Vector ASSdraw path or text. If unwired, defaults to active context glyph (syllable, word, or line).
2. **`Factor (t)`:** Parametric progress factor ($0.0 \to 1.0$) for animating continuous transformations.
3. **`Anchor` (Monolithic Shape Reference System):**
   * **`center`:** Centres shape mass at local origin `(0, 0)` (ink centroid).
   * **`origin`:** Aligns top-left corner of ink bounding box to `(0, 0)`.
   * **`relative`:** Preserves the shape's native coordinate origin `(0, 0)` without ink recentring (ideal for 1:1 typographic alignment).
   * **`absolute`:** Translates geometry directly to screen coordinates `(fx.pos_x, fx.pos_y)`.

---

### 3.3. Mode-Specific Inputs and Properties

#### 1. `Scale` (Anamorphic Scaling) Mode
* **`Scale X` / `Scale Y`:** Independent horizontal and vertical scaling percentages (default: `100`%).
* **`Factor (t)` / `Anchor`:** Universal parameters (`center`, `origin`, `relative`, `absolute`).

#### 2. `Borders` (Perimeter Expansion / Contraction) Mode
Dilates or erodes closed contours via Clipper morphological offset.
* **`Offset (px)` (`offset_border`):** Pixel offset distance (positive expands outwards; negative contracts inwards; default: `2.0`).
* **`Factor (t)` / `Anchor`:** Universal parameters.

#### 3. `Deform` (Asymmetric Directional Deformation) Mode
Applies directional distortion vectors.
* **`Offset X` / `Offset Y`:** Horizontal and vertical deformation vector components.
* **`Def Factor` (`factor`):** Intensity/scale percentage of morphological distortion (default: `100`%).
* **`Factor (t)` / `Anchor`:** Universal parameters.

#### 4. `Position` (Relative Cartesian Shift) Mode
Translates drawing coordinates in $X$ and $Y$ without altering the ASS `\pos` tag.
* **`Offset X` / `Offset Y`:** Pixel offsets in horizontal and vertical axes.
* **`Factor (t)` / `Anchor`:** Universal parameters (`center`, `origin`, `relative`, `absolute`).

#### 5. `Redraw` (Bézier Resampling & Density) Mode
Resamples and redistributes Bézier curve vertices for smoothing or dense tessellation.
* **`Density / Step` (`density`):** Sampling density factor (higher values generate more interpolated control points; default: `2.0`).
* **`Factor (t)` / `Anchor`:** Universal parameters.

#### 6. `3D Rotate` (Matrix 3D Rotation) Mode
Projects and rotates vector paths in 3D space using matrix linear algebra with perspective.
* **`Rotate X` (`angle_x`):** Pitch rotation in degrees around $X$ axis.
* **`Rotate Y` (`angle_y`):** Yaw rotation in degrees around $Y$ axis.
* **`Rotate Z` (`angle_z`):** Coplanar screen roll rotation in degrees around $Z$ axis (equivalent to `\frz`).
* **`Factor (t)` / `Anchor`:** Universal parameters (`center`, `origin`, `relative`, `absolute`).

#### 7. `Reflect` (Specular Mirror Reflection) Mode
Mirrors shape across a reference Cartesian axis.
* **`Axis`:** Reflection axis (`none` to keep original unmirrored shape, `x` for horizontal inversion / left-right, `y` for vertical inversion / top-bottom, `xy` for diagonal inversion).
* **`Offset X` / `Offset Y`:** Symmetry axis displacement.
* **`Factor (t)` / `Anchor`:** Universal parameters.

#### 8. `Matrix` (Master Spatial Matrix Pipeline) Mode
Combines all affine, morphological, and 3D spatial transformations in a single optimised vector pass:
$$\text{Clipper Offset (Offset Border)} \longrightarrow \text{Resampling (Density)} \longrightarrow \text{Scale} \longrightarrow \text{Shear (Skew)} \longrightarrow \text{3D Euler Rotation} \longrightarrow \text{Reflection} \longrightarrow \text{Translation (Offset)}$$

* **`Shape / Text`:** Input ASSdraw vector path or text.
* **`Factor (t)`:** Global parametric interpolation factor ($0.0 \to 1.0$).
* **`Scale X` / `Scale Y`:** Independent horizontal and vertical scale percentages (default: `100`%).
* **`Skew X` / `Skew Y`:** Transverse shear/skew factors along $X$ and $Y$ axes.
* **`Rotate X` / `Rotate Y` / `Rotate Z`:** Euler rotation angles in degrees across all 3 Cartesian axes with conical perspective projection ($fov$).
* **`Offset X` / `Offset Y`:** Cartesian translation in pixels.
* **`Offset Border`:** Prior geometric contour offset distance via Clipper in pixels (positive dilates/expands; negative erodes/contracts; default: `0.0`).
* **`Axis`:** Specular mirror reflection axis (`none`, `x`, `y`, `xy`).
* **`Density`:** Prior Bézier resampling step (default: `0` for disabled; $> 0$ for px-step subdivision).
* **`Anchor`:** Spatial anchor reference (`center`, `origin`, `relative`, `absolute`).

---

### 3.4. Practical Production Example
* **Perspective 3D Rotation of a Vector Primitive:**
  Transforming a star primitive from `Shape/Library` with rotation around the $Y$ axis (3D yaw) modulated across syllable time:

  ```
  [Shape/Library: star] ──► Shape ──► Shape / Text ──► [Shape/Manipulator: 3D Rotate, Rotate Y=70]
                                                             └──► Shape ──► Return ──► [System/Output]
  ```

  In a tag node wired to `System/Output (Tags)`:
  ```
  {\p1\pos(syl.center, syl.middle)\1c&H00FFFF&\bord1\3c&H003366&\t(0, syl.dur, \1c&HFF0088&)}
  ```
  The star rotates three-dimensionally around its local centroid projecting conical perspective, while colours smoothly transition without shifting the syllable anchor.

---

## 4. Node `Shape/Filter` (Vertex Modulation and Perturbation)

* **Canonical Category:** `Shape` (UI: *Shape / Filter*)
* **Purpose:** Modifies vertex coordinates of ASSdraw vector paths analytically, morphologically, or stochastically through continuous mathematical expressions, stepped cinematic subcontour transforms, or controlled stochastic perturbation (*jitter / noise*).
* **Thematic Colour:** `#0F766E` / `#5B2C6F`

![Shape/Filter](img/filter.png)

---

### 4.1. Header and Header Mode Combos
The node features a header drop-down selector that reactively reconfigures input ports and body properties according to the chosen deformation paradigm:
1. **`Vertices` (Per-Vertex Analytical Expressions):** Applies parametric mathematical transforms to each individual $(x, y)$ coordinate based on Cartesian, polar, and contour progression metrics.
2. **`Group` (Stepped Subcontour Transforms):** Iterates over each closed subcontour or independent island (`m ...`) in a compound path, applying progressive cumulative rotations, scaling, and spatial offsets per piece.
3. **`Noise` (Stochastic Vertex Perturbation):** Jitters each vertex within an elliptical or rectangular dispersion window, featuring deterministic seed control and prior geometric subdivision.

---

### 4.2. Input Ports and Body Properties (*Inputs & Properties*)

#### 1. `Vertices` (Per-Vertex Analytical Expressions & Parametric Kinematics) Mode
Evaluates algebraic expressions in real time over each ordered pair $(x_k, y_k)$ of the path. Enables high-complexity organic deformations (harmonic ripples, gravitational vortices, polar twists, ballistic dispersion, and non-linear melting).

1. **`[2.1] Shape / Text` (`shape`):** Base ASSdraw path or text. If disconnected, inherits the glyph from the active context (`syl.text` or `line.text`).
2. **`[2.2] Expr X` (`expr_x`):** Mathematical expression calculating the new horizontal vertex position (default: `x`).
3. **`[2.3] Expr Y` (`expr_y`):** Mathematical expression calculating the new vertical vertex position (default: `y`).
4. **`[2.4] Factor (t)` (`t`):** Temporal modulation factor or parametric interpolator ($0.0 \le t \le 1.0$). Smoothly blends between original geometry and calculated targets (default: `1.0`).
5. **`[2.5] Subdivs` (`subdivs`):** Refinement factor for pre-subdividing Bézier curves and straight line spans prior to expression evaluation (default: `0`).

##### Exhaustive Variable Reference in `Expr X` and `Expr Y`:
* **Absolute Cartesian Coordinates:**
  * `x`, `y`: Current original coordinates of the evaluated vertex in local space.
  * `cx`, `cy` (`Cx`, `Cy`): Coordinates of the geometric centroid of the shape's mass:
    $$cx = \frac{x_{\min} + x_{\max}}{2}, \quad cy = \frac{y_{\min} + y_{\max}}{2}$$
  * `width`, `height`: Total dimensions of the bounding box: $W = x_{\max} - x_{\min}$, $H = y_{\max} - y_{\min}$.
  * `minx`, `miny`, `maxx`, `maxy`: Bounding box extents.
* **Relative Normalised Coordinates $(0.0 \to 1.0)$:**
  * `mx`, `my` (`Mx`, `My`): Normalised percentage position of the vertex within the bounding box:
    $$mx = \frac{x - x_{\min}}{\max(10^{-6}, W)}, \quad my = \frac{y - y_{\min}}{\max(10^{-6}, H)}$$
* **Polar Metrics and Euclidean Distances:**
  * `do`, `Do`: Euclidean distance from the local origin `(0, 0)` to the vertex: $do = \sqrt{x^2 + y^2}$.
  * `dc`, `Dc`: Euclidean distance from the centroid `(cx, cy)` to the vertex: $dc = \sqrt{(x - cx)^2 + (y - cy)^2}$.
  * `ao`, `Ao`: Polar angle in degrees ($0^\circ \le ao < 360^\circ$) relative to the local origin `(0, 0)`.
  * `ac`, `Ac`: Polar angle in degrees ($0^\circ \le ac < 360^\circ$) relative to the centroid `(cx, cy)`.
* **Sequence Indices & Contour Progression:**
  * `k`, `i`, `Pk`: 1-based ordinal index of the evaluated vertex ($1 \le k \le N$).
  * `n`, `Pn`: Total number of vertices comprising the path.
  * `mp`, `Mp`: Normalised longitudinal progress of the vertex along the perimeter: $mp = \frac{k - 1}{N - 1}$ (or $0.0$ if $N \le 1$).
  * `t`: Active numerical value of `Factor (t)`.
* **Available Mathematical Functions:**
  * *Trigonometric:* `sin(rad)`, `cos(rad)`, `tan(rad)`, `asin(v)`, `acos(v)`, `atan2(y, x)`.
  * *Angular Conversion & Constants:* `rad(deg)` (degrees to radians), `deg(rad)` (radians to degrees), `pi`, `PI`.
  * *Algebra & Exponentials:* `sqrt(v)`, `abs(v)`, `min(a, b)`, `max(a, b)`, `exp(v)`, `log(v)`.
  * *Discretisation & Rounding:* `floor(v)`, `ceil(v)`, `round(v)`.

> [!IMPORTANT]
> **Scope Isolation and Fault-Tolerant Fallback:**  
> The mathematical evaluator in `Vertices` mode executes within a strict, deterministic algebraic sandbox. External stochastic functions such as `Rs()` or `R()` **do not exist** in this scope. If an expression references undefined symbols or contains syntax errors, the node engages its safe fallback mechanism, preserving the vertex intact ($x_{\text{final}} = x, y_{\text{final}} = y$) without throwing fatal graph exceptions. For stochastic motion, switch to native **`Noise`** mode or utilize deterministic harmonic hash formulas based on `k`.

---

#### 2. `Group` (Stepped Subcontour Transforms) Mode
Splits the vector shape into its constituent independent closed subcontours or islands (delimited by path start commands `m ...`) and applies progressive cumulative kinematics per piece.

1. **`[2.1] Shape / Text` (`shape`):** Compound multi-stroke path (e.g. glyphs such as "i", "j", "!", "?", multi-radical kanji, or shapes pre-fractured by *Slicer*).
2. **`[2.2] Factor (t)` (`t`):** Global temporal interpolator ($0.0 \to 1.0$).
3. **`[2.3] Rotation Step` (`rot_step`):** Successive angular increment in degrees applied per piece (default: `0.0`).
4. **`[2.4] Scale Step` (`scale_step`):** Successive scaling percentage applied per piece (default: `100.0`%).
5. **`[2.5] Offset X` (`offset_x`):** Successive horizontal displacement per piece in pixels (default: `0.0`).
6. **`[2.6] Offset Y` (`offset_y`):** Successive vertical displacement per piece in pixels (default: `0.0`).
7. **`[2.7] Anchor` (`anchor`):** Local pivot point for rotation and scaling of each island (`center`, `origin`, `relative`, `absolute`).

---

#### 3. `Noise` (Stochastic Vertex Perturbation) Mode
Injects uniform stochastic perturbations to each vertex within an elliptical or rectangular envelope. Ideal for analogue styling (*line boil*, chalk, fire jitter, electrical arcs, steam, or organic disintegration).

1. **`[2.1] Shape / Text` (`shape`):** Base ASSdraw path to jitter.
2. **`[2.2] Radius X` (`radius_x`):** Maximum horizontal random dispersion radius in pixels: $\Delta x \in [-R_x, +R_x]$ (default: `5.0`).
3. **`[2.3] Radius Y` (`radius_y`):** Maximum vertical random dispersion radius in pixels: $\Delta y \in [-R_y, +R_y]$ (default: `5.0`).
4. **`[2.4] Subdivs` (`subdivs`):** Pre-subdivision density for Bézier curves and straight lines prior to noise evaluation (default: `2.0`).
5. **`[2.5] Seed` (`seed`):** Integer seed for the deterministic pseudo-random generator (default: `0`).

---

### 4.3. Output Ports (*Outputs*)
1. **`[1.1] Shape`:** Emits the resulting modified ASSdraw vector code (`m ... l ... b ...`), with updated coordinates ready for downstream rendering or boolean operations.

---

### 4.4. Mathematical Model and Algorithmic Behaviour

#### 4.4.1. Parametric Interpolation in `Vertices` Mode
Given an original coordinate $\vec{p} = (x, y)$ and the evaluated expression solutions $\vec{p}_{\text{calc}} = (\text{res}_x, \text{res}_y)$, the final output position is generated via convex combination:

$$\vec{p}_{\text{final}}(t) = \vec{p} + t \cdot (\vec{p}_{\text{calc}} - \vec{p}) = \begin{pmatrix} x + t \cdot (\text{res}_x - x) \\ y + t \cdot (\text{res}_y - y) \end{pmatrix}$$

Where $t \in [0.0, 1.0]$. At $t = 0.0$, geometry remains unaffected; at $t = 1.0$, the calculated deformation is fully reached.

#### 4.4.2. Role of the `Subdivs` Parameter (Spatial Frequency Control)
Standard font outlines and geometric primitives frequently define extended straight spans using only two endpoint vertices (e.g. the vertical stem of an "I" or the edges of a box). Evaluating sine ripples or noise without subdivision only displaces the endpoints, keeping the intermediate line rigid.
* **$\text{Subdivs} = 0$:** Retains the original vertex count. Best for low-poly faceted deformations.
* **$\text{Subdivs} \ge 1.0$:** Recursively subdivides each straight segment and cubic Bézier span into $2^{\text{subdivs}}$ pieces while preserving $C^1$ continuity. With higher vertex density, wave equations render as smooth continuous ripples, and `Noise` produces high-frequency organic textures.

#### 4.4.3. Cumulative Kinematics in `Group` Mode
For a path segmented into $M$ subpieces indexed by $j \in [0, M - 1]$:
$$\theta_j = j \cdot \text{Rot Step} \cdot t$$
$$S_j = \max\left(0.001, \, 1.0 + j \cdot \left(\frac{\text{Scale Step} - 100.0}{100.0}\right) \cdot t\right)$$
$$\Delta x_j = j \cdot \text{Offset X} \cdot t, \quad \Delta y_j = j \cdot \text{Offset Y} \cdot t$$

Each subcontour is scaled and rotated around its local anchor specified by `Anchor`, allowing layered ballistic piece flurries.

#### 4.4.4. Stochastic Perturbation and Animation in `Noise` Mode
In `Noise` mode, each vertex is shifted by independent uniform random variables:
$$x' = x + \Delta x, \quad \Delta x \sim \mathcal{U}(-R_x, \, +R_x)$$
$$y' = y + \Delta y, \quad \Delta y \sim \mathcal{U}(-R_y, \, +R_y)$$

* **Static Seed (`Seed` fixed):** Generates a frozen, reproducible ragged silhouette.
* **Dynamic Seed (`Seed` variable):** Feeding the frame iterator (`fx_i`, `j`, or a time-driven variable based on `st`) to `Seed` causes the noise field to refresh each frame, creating the traditional hand-drawn vibrating look (*line boil*).

---

### 4.5. Practical Recipes and Design Patterns

#### Recipe 1: Horizontal Sine Ripple / Floating Banner (`Vertices` Mode)
Produces a transversal travelling wave across the horizontal axis with subdivision to flex letter stems:
* **`Subdivs`:** `2`
* **`Expr X`:** `x`
* **`Expr Y`:** `y + sin(rad(x * 6 + t * 360)) * 12`

#### Recipe 2: Gravitational Vortex / Polar Twist (`Vertices` Mode)
Rotates vertices around the centroid with an angle proportional to Euclidean distance $dc$:
* **`Subdivs`:** `1`
* **`Expr X`:** `cx + dc * cos(rad(ac + dc * 1.5 * t))`
* **`Expr Y`:** `cy - dc * sin(rad(ac + dc * 1.5 * t))`

#### Recipe 3: Deterministic Pseudo-Noise Ripple (`Vertices` Mode)
Generates chaotic stochastic-looking vertex shifts within `Vertices` mode without external random calls, using non-congruent harmonic frequencies over vertex index $k$:
* **`Expr X`:** `x + sin(k * 12.9898) * 4 * t`
* **`Expr Y`:** `y + cos(k * 78.2330) * 4 * t`

#### Recipe 4: Animated Line Boil / Chalk Shimmer (`Noise` Mode)
Transforms vector typography into vibrating analogue chalk or electrical outlines:
* Graph: `Text to Shape` $\to$ `Shape/Filter (Noise)` $\to$ `Output (Return)`
* **`Radius X`:** `3.5`
* **`Radius Y`:** `3.5`
* **`Subdivs`:** `2`
* **`Seed`:** `fx_i` *(updates each frame in an FBF loop)*

---

## 5. Node `Shape/Transform` (Morphology and Curvature)

* **Canonical Category:** `Shape` (UI: *Shape*)
* **Purpose:** Performs non-linear morphological transforms on ASSdraw paths: radial inflation (*Inflate*), angular skew (*Skew*), corner filleting/bevelling (*Round Corners*), spline bending (*Flexor*), and continuous 2-shape or 3-stage shape morphing (*Distort / Distort2*).

![Shape/Transform](img/transform.png)

---

### 5.1. Header and Outputs
1. **`[1.1] Shape` (Output):** Emits morphed/transformed ASSdraw path.
2. **`[1.2] Mode`:** Selector switching between 6 transform modes (`Inflate`, `Skew`, `Round Corners`, `Flexor`, `Distort`, `Distort2`).

---

### 5.2. Universal Parameters & Silhouette Overlay Behaviour
* **`Shape / Text`:** Input vector path or text.
* **`Factor (t)`:** Progress factor ($0.0 \to 1.0$) animating the transition.
* **`Anchor` (Spatial Morph Alignment):**
  * **Automatic Normalisation:** Target shape is proportionally scaled and overlaid onto source shape. Bounding box evolves smoothly: $W(t) = W_A(1-t) + W_B(t)$ and $H(t) = H_A(1-t) + H_B(t)$.
  * **`center` (Concentric Alignment — Default):** Aligns centroids $(\frac{x_{\min}+x_{\max}}{2}, \frac{y_{\min}+y_{\max}}{2})$, centring output at `(0, 0)` for concentric expansion/contraction.
  * **`origin` (Top-Left Alignment):** Aligns top-left corners $(x_{\min}, y_{\min})$, fixing `(0, 0)` at top-left.
  * **`absolute` (Screen Alignment):** Retains screen position `(fx.pos_x, fx.pos_y)`.

---

### 5.3. Mode-Specific Inputs and Parameters

#### 1. `Inflate` (Radial Spherification) Mode
* **`Ratio`:** Radial inflation strength ratio (default: `1.0`).
* **`Inflate Mode`:** `Circle` (Uniform spherical) or `Ellipse` (Proportional to bounding box).

#### 2. `Skew` (2D Angular Shear) Mode
* **`Angle X` / `Angle Y`:** Horizontal and vertical shear angles in degrees.

#### 3. `Round Corners` (Vertex Fillet & Bevel) Mode
* **`Radius (px)` (`radius`):** Corner fillet radius or bevel depth in pixels (default: `10.0`).
* **`Corner Mode`:** `Round` (Cubic Bézier arcs), `Bevel` (Linear chamfer), or `Miter` (Extended sharp corner).
* **`Anchor`:** Spatial anchor (`center`, `origin`, `relative`, `absolute`).

#### 4. `Flexor` / `Bend` (Spline Bending) Mode
Bends geometry along a numerical arc or custom ASSdraw curve.
* **`Curve / Angle` (`curve`):** Angular degrees (e.g. `30`, `-45`) or full ASSdraw spline (`m ... b ...`).
* **`Axis`:** Bending axis (`x` for horizontal curve, `y` for vertical).
* **`Anchor`:** Spatial anchor (`center`, `origin`, `relative`, `absolute`).

#### 5. `Distort` (2-Shape Vector Morphing) Mode
Adaptive perimeter morphing between source and target shapes (supports text-to-vector on the fly).
* **`Target Shape`:** Final destination vector path or text glyph at $t = 1.0$.
* **`Energy`:** Elastic harmonic modulation coefficient on Bézier handles: $W(t) = \sin(\pi \cdot t)$ (default: `0.35`).
* **`Step (px)`:** Metric subdivision in pixels for uniform perimeter resampling ($\text{steps} = \max(1, \text{round}(L / s_{px}))$; default `0` for adaptive).
* **`Anchor`:** Spatial morph alignment anchor (`center`, `origin`, `relative`, `absolute`).

#### 6. `Distort2` (3-Stage Vector Morphing) Mode
Continuous 3-stage morph: Start ($t=0.0$) $\to$ Mid ($t=0.5$) $\to$ Target ($t=1.0$).
* **`Mid Shape`:** Intermediate shape at $t = 0.5$.
* **`Target Shape`:** Final shape at $t = 1.0$.
* **`Energy`:** Harmonic modulation coefficient on Bézier handles (default: `0.35`).
* **`Step (px)`:** Metric subdivision in pixels (default: `0`).
* **`Anchor`:** Spatial morph alignment anchor (`center`, `origin`, `relative`, `absolute`).

---

### 5.4. Practical Production Example
* **Vector Text-to-Primitive Morphing:**
  Morphed transition from the syllable typographical silhouette into a star primitive from `Shape/Library` across syllable active duration:

  ```
  [System/Input: Syl Shape] ──► Shape / Text ──┐
                                              ├──► [Shape/Transform: Distort, Energy=0.35]
  [Shape/Library: star] ────► Target Shape ───┘          └──► Shape ──► Return ──► [System/Output]
  ```

  Wired with `Factor (t)` tied to normalised syllable time progress and configuring `System/Output (Tags)`:
  ```
  {\p1\pos(syl.center, syl.middle)\1c&H00FFFF&\bord1\3c&H000000&\t(0, syl.dur, \1c&H0088FF&)}
  ```
  The syllable glyph continuously deforms perimetrically towards the star contour around its local centroid without altering the central anchor.

---

## 6. Node `Shape/Concentric Borders` (Concentric Layers and Borders)

* **Canonical Category:** `Shape` (UI: *Shape*)
* **Purpose:** Generates outward concentric rings, stepped contours, or perimeter ripple shockwaves from a base vector shape using Clipper offset dilation and boolean difference operations.

![Shape/Concentric Borders](img/concentric_borders.png)

---

### 6.1. Header and Outputs
1. **`[1.1] Concentric Borders`:** Node title identifier.
2. **`[1.2] Vector Output Mode` (`out_mode`):**
   * **`Shape`:** Emits raw ASSdraw code of the ring (`m ... l ... b ...`).
   * **`\clip` (`Clip`):** Emits ASS clipping tag `\clip(m ...)` positioned in screen coordinates.
   * **`\iclip` (`iClip`):** Emits inverted ASS clipping tag `\iclip(m ...)`.

---

### 6.2. Body Inputs and Properties
1. **`[2.1] Shape / Text`:** Base vector path or text.
2. **`[2.2] Mode: [Hollow / Solid]`:**
   * **`Hollow (borders)`:** All rings are constant-width hollow bands:
     $$\text{Ring}_i = \text{BooleanDifference}(\text{Outer}_i, \text{Inner}_i)$$
   * **`Solid (filled borders)`:** First layer ($i = 1$) is solid fill; subsequent layers ($i \ge 2$) are outward hollow rings.
3. **`[2.3] Max Rings` (`loop_count`):** Total concentric layers to generate (default: `5`). Defines `b_n` and `maxloop`.
4. **`[2.4] Separation (px)` (`separation`):** Dilation thickness per ring. Supports fixed floats (`5.0`) or comma-separated lists (`5, 2, 8, 3`) for alternating rhythms.
5. **`[2.5] Overlap (px)` (`overlap`):** Boundary overlap in pixels between adjacent layers (default: `0.5`) to eliminate subpixel anti-aliasing gaps in libass.
6. **`[2.6] Anchor`:** Spatial anchor (`Center`, `Relative`, `Absolute`, `Piece`).
7. **`[2.7] b_i, b_n`:** Iteration variables in footer (`b_i` = active ring index $[1 \dots N]$, `b_n` = total rings).

---

### 6.3. Output Ports (*Outputs*)
1. **`[3.1] Shape`:** ASSdraw path or `\clip`/`\iclip` tag for current ring `b_i`.
2. **`[3.2] \pos`:** Injected `\pos(x,y)` tag positioning ring centroid on canvas.
3. **`[3.3] Index`:** Active ring index ($1 \dots \text{Max Rings}$).
4. **`[3.4] Total`:** Total generated rings ($b\_n$).

### 6.4. Practical Production Example
* **Concentric Perimeter Shockwaves with Progressive Fade:**
  Routing syllable outline into `Shape/Concentric Borders` with `loop_count: 5`, `separation: 6`, `mode: hollow`:

  ```
  [System/Input: Syl Shape] ──► Shape / Text ──► [Shape/Concentric Borders: hollow, max=5]
                                                       ├──► Shape ──► Return ──► [System/Output]
                                                       └──► (b_i, b_n in context)
  ```

  In a tag node wired to `System/Output (Tags)`:
  ```
  {\p1\pos(syl.center, syl.middle)\1c&H00FFFF&\bord0\1a&H44&\t(0, 400, \fscx(100 + b_i * 15)\fscy(100 + b_i * 15)\1a&HFF&)}
  ```
  Generates 5 concentric bands of 6 px thickness expanding outward whilst progressively fading out opacity according to index `b_i`.

---

## 7. Node `Shape/Walker` (Trajectories and Progressive Path Tracing)

* **Canonical Category:** `Shape` (UI: *Shape / Walker*)
* **Purpose:** Traverses and parametrically integrates the arc length of an ASSdraw vector path, calculating progressive stroke trimming (*write-on / stroke trimming*) across the $[start\_t, progress]$ interval, and emitting the Cartesian `\pos` tag and tangential angle `\frz` at the advancing tip.

### 7.1. Header Modes and Parameters
1. **Integration Mode (`mode`):**
   * `global`: Integrates cumulative total arc length across all subcontours or independent path segments. The $[0.0, 1.0]$ range traverses the complete compound geometry sequentially from start to end.
   * `piece`: Evaluates progress $[0.0, 1.0]$ simultaneously and independently across each `m` subcontour (ideal for concurrent write-on across all glyphs in a word).
2. **Traversal Direction (`invert`):**
   * `normal`: Traverses vertices in their natural construction order.
   * `inverted`: Reverses perimeter traversal direction (end to start).

### 7.2. Input Ports and Body Properties
1. **`[2.1] Shape / Text`:** Vector ASSdraw path or text glyph to traverse.
2. **`[2.2] Progress (t)` (`progress`):** Terminal progress factor of the trimmed segment ($t_2 \in [0.0, 1.0]$, default: `1.0`).
3. **`[2.3] Start (t)` (`start_t`):** Starting progress factor of the segment ($t_1 \in [0.0, 1.0]$, default: `0.0`). Enables travelling window or trailing ribbon effects.
4. **`[2.4] Subdivs` (`subdivs`):** Number of linear chord subdivisions per Bézier segment for arc-length integration (default: `30`).
5. **`[2.5] Close Path` (`close_path`):** Boolean toggle (default: `False`). When `True`, appends a closing `l` command returning to the initial `m` vertex if the contour finishes unclosed.

### 7.3. Output Ports (*Outputs*)
1. **`[1.1] Shape Out`:** Trimmed ASSdraw vector path between $t_1$ and $t_2$.
2. **`[1.2] \pos Tag`:** ASS `\pos(x,y)` tag computed at the advancing tip ($t_2$), projected into screen coordinates.
3. **`[1.3] Angle (\frz)`:** Tangential angle in sexagesimal degrees at the lead tip, oriented along the path curve tangent.
4. **`[1.4] Length`:** Effective arc length in pixels of the emitted segment.
5. **`[1.5] Tip X`:** Absolute horizontal Cartesian coordinate of the tip.
6. **`[1.6] Tip Y`:** Absolute vertical Cartesian coordinate of the tip.

### 7.4. Algorithmic Detail and Mathematical Model
1. **Arc-Length Integration:**
   For each cubic Bézier segment $\mathbf{B}(u) = (1-u)^3\mathbf{P}_0 + 3(1-u)^2u\mathbf{P}_1 + 3(1-u)u^2\mathbf{P}_2 + u^3\mathbf{P}_3$, evaluates $S = \text{subdivs}$ discrete chords:
   $$L_{\text{arc}} = \sum_{j=1}^{S} \|\mathbf{B}(j/S) - \mathbf{B}((j-1)/S)\|$$
2. **Parametric Trimming:**
   Target distances $s_1 = start\_t \cdot L_{\text{total}}$ and $s_2 = progress \cdot L_{\text{total}}$ locate trimming boundaries, evaluated using De Casteljau's subdivision algorithm.
3. **Tangential Angle and Positioning:**
   $$\theta = \operatorname{atan2}\left(\frac{dy}{du}, \, \frac{dx}{du}\right) \cdot \frac{180}{\pi}$$
   $$\text{pos}_x = x_{\text{parent}} + \text{Tip X}, \quad \text{pos}_y = y_{\text{parent}} + \text{Tip Y}$$

### 7.5. Practical Production Example
* **Progressive Write-On Effect with Leading Particle:**
  Feeding `Progress (t)` from `Loops/Module` ($0.0 \to 1.0$):
  
  ```
  Line 1 (Expanding vector stroke):
  Route Shape Out to System/Output (Return)
  Tags: {\p1\pos(syl.center, syl.middle)\1c&H00FFFF&\bord0}
  
  Line 2 (Leading particle or spark anchored at the tip):
  Route Tip X, Tip Y and Angle (\frz) to Variables (or wire \pos Tag directly):
  Tags: {\p1\pos(tip_x, tip_y)\frz(angle)\1c&HFFFFFF&\bord0}
  Return: m -4 -4 l 4 0 l -4 4
  ```

---

## 8. Node `Shape/Stroke` (Thickness Extrusion for Paths and Lines)

* **Canonical Category:** `Shape` (UI: *Shape / Stroke*)
* **Purpose:** Converts open lines, vector skeletons, or unfilled paths into closed double-contour polygonal drawings with parametric stroke thickness and topological control over corner joins and terminal caps via *Clipper2*.

``

### 8.1. Input Ports (*Inputs*)
1. **`Shape / Text`:** Vector ASSdraw path of an open line, curve, or text glyph to extrude.
2. **`Width (px)`:** Optional dynamic input to modulate stroke thickness in pixels. If unwired, evaluates the `width` property.

### 8.2. Controls and Body Properties
1. **`[2.1] Width (px)` (`width`):** Total volumetric boundary thickness in pixels (default: `4.0`, minimum: $0.01$).
2. **`[2.2] Join Mode` (`join_mode`):** Geometric join type at intermediate corners and vertices:
   * `round`: Continuous circular arc corners.
   * `miter`: Pointed miter joint truncated at miter limit.
   * `bevel`: Flat bevelled chamfer joins.
3. **`[2.3] Cap Mode` (`cap_mode`):** Terminal cap type at open line ends:
   * `round`: Exact semicircle of radius $w/2$.
   * `bezier`: Smooth cubic Bézier rounded cap.
   * `flat`: Flat perpendicular cut directly at endpoint.
   * `square`: Square cap extended by distance $w/2$ beyond the endpoint.
4. **`[2.4] Miter Limit` (`miter_limit`):** Maximum ratio between miter length and stroke thickness before bevelling occurs (default: `2.0`, minimum: $1.0$).

### 8.3. Output Ports (*Outputs*)
1. **`[1.1] Shape Out`:** Resulting closed ASSdraw polygon (`m ... l ... b ...`) with stroke and caps applied, ready for `\p1` rendering.
2. **`[1.2] Width`:** Effective applied numerical stroke width in pixels.

### 8.4. Algorithmic Detail and Offset Topology
The node delegates path dilation to Clipper2's bilateral offset engine:
* Each open line segment produces an extruded rectangle of dimensions $L \times w$.
* At angular deflections, polygonal wedges are inserted according to `join_mode`.
* If input geometry is already a closed polygon, `Stroke` generates a hollow boundary ribbon of width $w$ centred upon the original boundary.

### 8.5. Practical Production Example
* **Thick Outlined Contour with Bézier Caps on Primitive:**
  Extruding vertices from a linear path or a `Shape/Library` primitive:
  
  ```
  [Shape/Library: triangle] ──► Shape ──► Shape / Text ──► [Shape/Stroke: width=6, join=round] ──► Shape Out ──► Output (Return)
  ```
  
  In a tag node wired to `System/Output (Tags)`:
  ```
  {\p1\pos(syl.center, syl.middle)\1c&HFF0066&\bord1\3c&H000000&}
  ```
  Produces a hollow triangular polygon with 6-pixel thick boundaries and rounded corners.

---

## 9. Node `Shape/Union & Divide` (Topological Decomposition, Union, and Tag Fusion)

* **Canonical Category:** `Shape` (UI: *Shape*)
* **Purpose:** Multifunctional Clipper topology node. Decomposes compound paths into genuine vector islands via polygon hierarchy analysis (*PolyTree*), splits simple subpaths, merges silhouettes via boolean union, or packages multiple pieces into a single ASS drawing line by interleaving style tag blocks with keyframe interpolation.

![Shape/Union & Divide](img/union_&_divide.png)

---

### 9.1. Header Mode Selector (`mode`)
1. **`[DIVIDE]` (`PolyTree Divide`):** Exact topological decomposition into closed islands while distinguishing internal cut-out holes (e.g. letters "O", "B", "8", kanji).
2. **`[UNION]` (`Boolean Union`):** Boolean geometric merger of two overlapping shapes, removing inner boundaries.
3. **`[SUB-PATHS]` (`Naive Sub-Paths`):** Direct split by `m ...` start commands without hole hierarchy calculation.
4. **`[FUSION]` (`Tag Fusion with Keyframes`):** Assembles multiple vector islands into a **single ASS dialogue line** (`{\tags1}m... {\tags2}m...`).

---

### 9.2. Mode-Specific Inputs and Parameters

#### 1. `[DIVIDE]` (PolyTree Divide) Mode
* **`[2.1] Shape In`:** Input ASSdraw path or text.
* **`[2.2] Rule:` (`fill_type`):** Winding fill rule (`EvenOdd`, `NonZero`, `Positive`, `Negative`).
* **`[2.3] Clean:` (`clean_self_intersect`):** Auto-cleaning of self-intersecting edges (`Auto (1)`, `Off (0)`).
* **`[2.4] Anchor` (`Pieces`):** Anchor selector (`Pieces`, `Relative`, `Parent Org`, `Pos`, `Absolute`).
* **`[2.5] Order:` (`order`):** Spatial piece ordering (`79`, `97`, `13`, `31`, `71`, `17`, `93`, `39`, `5`, `-5`, `cw`, `ccw`, `rand`).

#### 2. `[UNION]` (Boolean Union) Mode
* **`[2.1] Shape In (A)`:** First base vector shape (`shape`).
* **`[2.1b] Shape In (B)`:** Second vector shape (`shape_b`) to merge.
* **`[2.2] Rule:` / `[2.3] Clean:` / `[2.4] Anchor`:** Boolean parameters.

#### 3. `[SUB-PATHS]` (Naive Sub-Paths) Mode
* **`[2.1] Shape In`:** ASSdraw path with multiple `m` subpaths.
* **`[2.2] Anchor` / `[2.3] Order:`:** Spatial parameters (`79`, `97`, `13`, `31`, `71`, `17`, `93`, `39`, `5`, `-5`, `cw`, `ccw`, `rand`).

#### 4. `[FUSION]` (Tag Fusion with Keyframes) Mode
Packages multiple islands into a single ASS line, reducing line count:
* **`[2.1] Shape In`:** Multi-path shape, text, or list of shapes.
* **`[2.2] Tag Mode:` (`tagmode`):**
  * **`ipol` (Progressive Interpolated):** Treats tag list as *keyframes*, interpolating smoothly between start and end ($0.0 \to 1.0$) for colour gradients (`\1c`), rotations (`\frz`), alphas (`\alpha`), or blur (`\blur`).
  * **`line` (Strict 1:1 Linear):** Maps tag blocks 1-to-1 to each piece in order. Extra pieces receive `{\p1}`; excess tags are discarded.
* **`[2.3] Tags` (`tags`):** Comma-separated ASS tags or hexadecimal colour list (e.g. `\1c&H0000FF&, \1c&H00FF00&, \1c&HFF0000&`).
* **`[2.4] Anchor` / `[2.5] Order:`:** Spatial parameters (`79`, `97`, `13`, `31`, `71`, `17`, `93`, `39`, `5`, `-5`, `cw`, `ccw`, `rand`).

---

### 9.3. Output Ports (*Outputs*) and Node Footer
1. **`[3.1] Shape Out`:** Emits active piece `d_i` in divide modes, or unified single drawing in union/fusion modes.
2. **`[3.2] Out List`:** JSON list containing all generated vector pieces for batch downstream chaining.
3. **`[3.3] BBox Data`:** Metric bounding box data string (`min_x,min_y,max_x,max_y,cx,cy,width,height`).

* **Node Footer (`d_i, d_n`):** Context variables granting access to the nested inner sub-loop generated by `Union & Divide` (`d_i` = active piece index $[1 \dots N]$, `d_n` / `d_max` = total count of pieces or islands generated in the partition).

---

---

### 9.5. Synergy with `Concatenate (Zip)`
Pairing `Union & Divide (FUSION)` with `Concatenate (Zip)` enables parallel multi-attribute matrix generation (e.g. combining gradient colours, oscillating `\blur`, and `\fscx` offsets) into a single compact ASS dialogue event, eliminating layer overlap artefacts.

---

### 9.6. Practical Production Example
* **Topological Island Decomposition with Staggered Gravitational Drop:**
  Decomposing a complex kanji or word into independent closed islands (`DIVIDE`) and animating the drop of each island with time offset governed by `d_i`:

  ```
  [System/Input: Syl Shape] ──► Shape In ──► [Shape/Union & Divide: DIVIDE, order=79, anchor=pieces]
                                                   ├──► Shape Out ──► Return ──► [System/Output]
                                                   └──► (d_i, d_n in context)
  ```

  In a tag node wired to `System/Output (Tags)`:
  ```
  {\p1\pos(syl.center, syl.middle)\t(d_i * 40, d_i * 40 + 300, \frz(d_i * 15)\fscx0\fscy0\alpha&HFF&)}
  ```
  Each vector island drops and rotates around its own local centroid with a 40 ms staggered offset per piece, preserving internal cut-out holes (PolyTree) without collapsing the overall silhouette.

---

## 10. Node `Shape/Clipper` (Advanced Vector Boolean Operations and Morphological Slicing)

* **Canonical Category:** `Shape` (UI: *Shape / Clipper*)
* **Purpose:** Applies Boolean operations (difference, intersection, union, XOR), morphological perimeter offsets, and Minkowski sum/difference between two closed or open vector geometries via the high-precision Clipper2 engine. Emits ASSdraw path commands (`Shape Out`) or clipping tags (`\clip`, `\iclip`).

![Shape/Clipper](img/clipper.png)

---

### 10.1. Header and Operation Modes (`mode`)
1. **`[1.1] Clipper`:** Node title identifier.
2. **`[1.2] Mode Selector Button` (`mode`):**
   * **`difference` (`Difference / Subtraction A - B`):** Subtracts geometry `Shape B (Clip)` from the base subject `Shape A (Subject)`. Ideal for punching custom holes, notches, and negative silhouettes.
   * **`intersection` (`Intersection A ∩ B`):** Preserves exclusively the shared spatial region where both shapes overlap.
   * **`union` (`Union A ∪ B`):** Merges both geometries into a unified outline, eliminating internal boundary seams.
   * **`xor` (`XOR / Symmetric Difference`):** Emits areas belonging to A or B, excluding the overlapping intersection region.
   * **`offset` (`Offset / Perimetric Dilation`):** Expands ($\Delta > 0$) or contracts ($\Delta < 0$) the perimeter of `Shape A` according to the pixel distance configured in `Delta (px)` with join and end-cap control.
   * **`minkowski_sum` (`Minkowski Sum A ⊕ B`):** Sweeps and dilates the pattern outline of `Shape B` along the entire perimeter of `Shape A`.
   * **`minkowski_diff` (`Minkowski Difference`):** Calculates the morphological difference between the outlines of both shapes.

---

### 10.2. Input Ports and Dynamic Configuration Controls
1. **`[2.1] Shape A (Subject)`:** Primary base vector shape or subject upon which the Boolean or morphological operation is executed. If omitted, falls back to the active context geometry.
2. **`[2.2] Shape B (Clip)`:** Secondary vector shape acting as a cutting mask, Minkowski pattern, or second operand.
3. **`[2.3] Subj Fill:` (`subj_fill`):** Cyclic button for subject shape A winding fill rule (`EvenOdd`, `NonZero`, `Positive`, `Negative`).
4. **`[2.4] Clip Fill:` (`clip_fill`):** Cyclic button for cutting shape B winding fill rule (`EvenOdd`, `NonZero`, `Positive`, `Negative`).
5. **`[2.5] Delta (px):` (`delta`):** Radial displacement distance in pixels for `offset` mode (supports positive values for dilation, negative values for erosion, and dynamic mathematical expressions).
6. **`[2.6] Join Mode:` (`join_type`):** Cyclic button for corner join style in offset mode (`Round`, `Miter`, `Square`, `Bevel`).
7. **`[2.7] End Mode:` (`end_type`):** Cyclic button for terminal cap style for open or closed paths (`Closed Polygon`, `Closed Line`, `Open Round`, `Open Square`, `Open Butt`).
8. **`[2.8] Miter Limit:` (`miter_limit`):** Maximum miter extension limit before sharp corners are chamfered (default: `2.0`).
9. **`[2.9] Post-Offset:` (`post_offset`):** Secondary perimetric dilation/contraction offset applied directly to the resulting silhouette following Boolean operations (`difference`, `intersection`, `union`, `xor`, `minkowski`). Allows expanding ($\text{px} > 0$) or contracting ($\text{px} < 0$) the cut result without chaining a second Clipper node (supports mathematical expressions; empty or `0.0` applies no post-offset).
10. **`[2.10] Clean Dist:` (`clean_dist`):** Pixel threshold distance for cleaning and simplifying colinear or degenerate micro-vertices via `CleanPolygons` ($0.0 = \text{disabled}$).
11. **`[2.11] Simple:` (`strictly_simple`):** Boolean toggle button (`FALSE` / `TRUE`). Enforces strictly simple polygon topology without self-intersections or coincident vertices.
12. **`[2.12] Rev Subj:` (`reverse_subj`):** Boolean toggle button (`FALSE` / `TRUE`). Inverts clockwise / anti-clockwise winding direction of the subject shape.
13. **`[2.13] Rev Clip:` (`reverse_clip`):** Boolean toggle button (`FALSE` / `TRUE`). Inverts winding direction of the clipping shape.
14. **`[2.14] Anchor:` (`anchor`):** Dropdown selector for geometric anchoring (`center`, `origin`, `relative`, `absolute`). In `relative` mode, preserves native coordinates without recentring to ink extremes.
15. **`[2.15] Out Mode:` (`out_mode`):** Cyclic button for output format (`Shape` plain ASSdraw code, `Clip` `\clip(...)` tag, `iClip` `\iclip(...)` tag).

---

### 10.3. Output Ports (*Outputs*)
1. **`[1.1] Shape Out`:** Emits the resulting ASSdraw vector path code or formatted `{\clip(...)}` / `{\iclip(...)}` tags.
2. **`[1.2] Out List`:** Emits structured list of resulting vector pieces or islands for downstream chaining or loop processing.
3. **`[1.3] BBox Data`:** Emits dictionary containing spatial bounding box metrics (`x1`, `y1`, `x2`, `y2`, `cx`, `cy`, `w`, `h`).

---

### 10.4. Practical Production Example
* **Negative Boolean Cut-Out with Perimeter Dilation:**
  Subtracting a star pattern (`Shape B`) from the syllable typographical glyph (`Shape A`) in `difference` mode with dilation post-offset:

  ```
  [System/Input: Syl Shape] ──► Shape A (Subject) ──┐
                                                    ├──► [Shape/Clipper: difference, Post-Offset=1.5]
  [Shape/Library: star] ────► Shape B (Clip) ─────┘          └──► Shape Out ──► Return ──► [System/Output]
  ```

  In a tag node wired to `System/Output (Tags)`:
  ```
  {\p1\pos(syl.center, syl.middle)\1c&HFFFFFF&\bord2\3c&HFF0055&}
  ```
  Generates a punched silhouette where the star cuts through the typographic body, leaving a 1.5 px expanded perimeter tolerance contour.

---

## 11. Node `Shape/Array` (Spatial Distribution, Matrices, and Vector Formations)

* **Canonical Category:** `Shape` (UI: *Shape*)
* **Purpose:** Multiplies and distributes shape instances across regular matrices, hexagonal lattices, concentric rings, parametric spirals, random scatter, or guide silhouette lattices. Supports per-piece iteration (`LOOPS`) or monolithic unified assembly (`SHAPE`).

![Shape/Array](img/array.png)

---

### 11.1. Dual Header Buttons
1. **`[1.1] Array`:** Node title identifier.
2. **`[1.2] Output / Execution Mode` (`out_mode`):**
   * **`[LOOPS]` (Iterator / Loop Mode):** Iterates element by element via context variables `a_i` and `a_n`. Emits individual particles on port `Piece` with separate `\pos(x,y)` tags and orientation angles `\frz`. Footer displays `a_i, a_n`.
   * **`[SHAPE]` (Monolithic Unified Shape Mode):** Merges all instances into a **single continuous ASSdraw stream** (`m ... l ... b ... m ...`), renaming port to `Shape Out`. Supports tag fusion via `Tags` port. Generates 1 dialogue line with `a_i = 1, a_n = 1` and footer `Single shape.`.
3. **`[1.3] Geometric Formation Mode` (`mode`):**
   * **`[GRID]`:** 2D orthogonal matrix of Columns $\times$ Rows.
   * **`[FORM]`:** Lattice sampled along vertices or fill of a guide shape/text.
   * **`[RINGS]`:** Concentric radial rings with radius steps and rotational offsets.
   * **`[SPIRAL]`:** Continuous parametric spiral with revolution and radius controls.
   * **`[SCATTER]`:** Pseudo-random bounded particle swarm with reproducible seed.
   * **`[HEX]`:** Hexagonal honeycomb grid with $60^\circ$ row offsets ($\Delta y = \Delta x \cdot \frac{\sqrt{3}}{2}$).

---

### 11.2. Universal Parameters (All Modes)
1. **`[2.1] Particle`:** Base ASSdraw vector shape or particle code.
2. **`[2.6] Scale`:** Particle scale multiplier ($1.0 = 100\%$).
3. **`[2.7] Factor (t)` (`t` / `progress`):** Progress factor ($0.0 \to 1.0$) controlling visible count: $\text{Visible} = \text{round}(\text{Total} \cdot t)$.
4. **`[2.8] Anchor`:** Spatial reference (`Piece`, `Relative`, `Parent Org`, `Pos`, `Absolute`).
5. **`[2.9] Order:`:** Spatial ordering (`79`, `97`, `13`, `31`, `71`, `17`, `5`, `cw`, `ccw`).
6. **`[2.10] Tags`:** ASS tag string for tag fusion in `SHAPE` mode.
7. **`[2.11] a_i, a_n`:** Footer iteration variables ($a\_i \in [1 \dots N]$).

---

### 11.3. Mode-Specific Dynamic Inputs

#### 1. `[GRID]` Mode
* **`[2.2] Cols` / `[2.3] Rows`:** Column and row counts.
* **`[2.4] Spacing X` / `[2.5] Spacing Y`:** Inter-cell spacing in pixels.

#### 2. `[FORM]` Mode
* **`[2.2] Formation`:** Guide ASSdraw path or text silhouette.
* **`[2.3] Spacing`:** Sampling step spacing between particles.

#### 3. `[RINGS]` Mode
* **`[2.2] Rings`:** Total concentric ring count.
* **`[2.3] Count / Ring`:** Particles per ring (single number or comma-separated list `6, 12, 18, 24`). If empty, automatically calculates optimal density:
  $$N_k = \text{round}\left(\frac{2 \pi \cdot R_k}{\text{Diameter} + \text{Spacing}}\right)$$
* **`[2.4] Radius` / `[2.5] Radius Step`:** Inner radius and radial increment per ring.
* **`[2.5b] Rotate Step`:** Angular twist offset in degrees per ring.

#### 4. `[SPIRAL]` Mode
* **`[2.2] Count` / `[2.3] Turns` / `[2.4] Max Radius`:** Total particles, revolution count, and outer radius.
* **`[2.5] Angle Step`:** Angular step (if `0`, computes uniformly $\theta_i = \frac{i}{N-1} \cdot \text{Turns} \cdot 360^\circ$).

#### 5. `[SCATTER]` Mode
* **`[2.2] Count` / `[2.3] Width` / `[2.4] Height` / `[2.5] Seed`:** Particle count, bounding dimensions, and deterministic seed.

#### 6. `[HEX]` Mode
* **`[2.2] Cols` / `[2.3] Rows` / `[2.4] Spacing`:** Hex grid dimensions and margin.

---

### 11.4. Output Ports (*Outputs*)
1. **`[3.1] Piece` / `Shape Out`:** Emits active particle in `[LOOPS]` or unified drawing in `[SHAPE]`.
2. **`[3.2] \pos Tag`:** Injected `\pos(x, y)` tag.
3. **`[3.3] X` / `[3.4] Y`:** Absolute pixel coordinates.
4. **`[3.5] Angle (\frz)`:** Tangential orientation angle in degrees ($\theta$).
5. **`[3.6] Index (a_i)` / `[3.7] Total (a_n)`:** Active index and total count.
6. **`[3.8] Col / Ring` / `[3.9] Row / IdxRing`:** Column/ring and row/ring-index coordinates.

### 11.5. Practical Production Example
* **Circular Constellation of Radial Particles:**
  Generating a concentric ring formation of 12 stars orbiting the syllable with continuous tangential orientation (`mode: rings, out_mode: loops, rings: 1, count: 12, radius: 45`):

  ```
  [Shape/Library: star] ──► Particle ──► [Shape/Array: rings, count=12, r=45]
                                               ├──► Piece ──► Return ──► [System/Output]
                                               ├──► \pos Tag ──► Tags ──► [System/Output]
                                               └──► Angle (\frz) ──► (angle)
  ```

  In a tag node wired to `System/Output (Tags)`:
  ```
  {\p1\pos(x, y)\frz(angle)\1c&H00FFFF&\bord0\t(0, 300, \fscx150\fscy150\1c&HFF0088&)}
  ```
  Each of the 12 stars is positioned on the circular perimeter and automatically oriented facing outward via the computed tangential angle.

---

## 12. Node `Shape/IMG to Shape` (Image and Animated GIF Vectorisation)

* **Canonical Category:** `Shape` (UI: *Shape / IMG to Shape*)
* **Purpose:** Vectorises raster images (PNG, JPG, WebP) or animated GIF sequences into continuous ASSdraw vector paths (`m`, `l`, `b`) via the integrated Potrace engine, polygonal approximation (Douglas-Peucker), or gradient edge detection.

### 12.1. Canvas Shortcuts and Frame Navigation
1. **File Loading Shortcut (Double-Click):**
   Double-clicking the Preview Card or any empty area of the node body opens the native operating system file picker dialogue (`select_image_dialog`) to load compatible files (`.png`, `.jpg`, `.jpeg`, `.webp`, `.gif`). The selected absolute path is written directly into `image_path`.
2. **Animated GIF Transport Controls:**
   When an animation file with multiple frames is detected (`total_frames > 1`), interactive transport controls appear:
   * Step buttons `[◀]` and `[▶]` for stepping frame by frame.
   * Horizontal scrubber timeline for real-time interactive inspection across all animation frames.

### 12.2. Vectorisation Engines (`mode`)
1. **`potrace`:** Generates smooth continuous splines composed of cubic Bézier curves (`m`, `l`, `b`) via intermediate polygon decomposition, corner curvature calculation, and subpixel smoothing.
2. **`polygon`:** Strict linear polygonal approximation (`m`, `l`) based on the Douglas-Peucker algorithm. Reduces vertex count whilst preserving sharp angular edges.
3. **`borders`:** Perimeter contour detection based on luminance gradients (Sobel operator).

### 12.3. Binarisation Modes (`bin_mode`)
1. **`luminance`:** Evaluates the greyscale brightness of each pixel against the `threshold` ($0 \dots 255$).
2. **`silhouette` / `alpha`:** Evaluates transparency on the alpha channel of transparent PNG/WebP images against the threshold.
3. **`borders`:** Binarises based on first derivatives of the intensity map.

### 12.4. Input Ports (*Inputs*) and Properties
1. **`[2.1] Image Path` (`image_path`):** Absolute or relative file path to image or animated GIF.
2. **`[2.2] Frame (j)` (`frame_idx`):** Target frame ordinal index to decode ($1 \dots \text{Total Frames}$). If left empty or at `"1"` when loading a GIF, the engine binds dynamically to loop variable `ish_i` or `j` to emit the complete animation sequence.
3. **`[2.3] Threshold` (`threshold`):** Binarisation cut-off level ($0 \dots 255$, default: `128`).
4. **`[2.4] Tolerance` (`tolerance`):** Intermediate vertex simplification tolerance (default: `1.0`).
5. **`[2.5] Smoothing` (`alphamax`):** Maximum corner curvature parameter in Potrace (default: `1.0`).
6. **`[2.6] Optimization` (`opttoler`):** Bézier curve optimisation tolerance for merging collinear segments (default: `0.2`).
7. **`[2.7] Scale Out` (`out_scale`):** Multiplier scale factor applied to the emitted vector path (default: `1.0`).
8. **`[2.8] Width Out` (`out_w`) / `Height Out` (`out_h`):** Forced pixel bounding dimensions. Setting `0.0` preserves native dimensions.
9. **`[2.9] Offset X` (`offset_x`) / `Offset Y` (`offset_y`):** Cartesian coordinate shifts in pixels applied to all vertices.
10. **`[2.10] Image Scale` (`img_scale`):** Pre-scaling factor applied to the bitmap before vectorisation analysis.
11. **`[2.11] Binarize Mode` (`bin_mode`):** Segmentation method (`luminance`, `silhouette`, `borders`).
12. **`[2.12] Anchor` (`anchor`):** Cartesian anchor reference:
    * `center`: Centres the vector drawing at local origin `(0, 0)` based on its centroid.
    * `origin`: Aligns top-left corner to `(0, 0)`.
    * `relative`: Retains original raster relative coordinates.
    * `absolute`: Projects onto screen by adding context coordinates `(fx.pos_x, fx.pos_y)`.
13. **`invert` / `invert_img`:** Toggles to invert foreground/background polarity or invert colour channels before binarisation.

### 12.5. Output Ports (*Outputs*)
1. **`[1.1] Shape Out`:** Continuous ASSdraw vector path (`m ... l ... b ...`) of the vectorised frame.
2. **`[1.2] Width`:** Effective width in pixels of the resulting vector path.
3. **`[1.3] Height`:** Effective height in pixels of the resulting vector path.
4. **`[1.4] Points`:** Total count of generated vertices and Bézier control points.
5. **`[1.5] Shapes Array`:** Array of independent vector islands for downstream piecewise processing.
6. **`[1.6] Total Frames`:** Total detected frames in the file. Injects `ish_n` and `ish_max` into context.

### 12.6. Practical Production Example
* **Frame-by-Frame Vectorised Animated GIF Playback:**
  Chaining `MaxLoop (fbf)` with `Shape/IMG to Shape`:
  
  ```
  [MaxLoop: fbf, step_ms=41.7] ──► Loop In ──► [System/Output]
                               ──► Counter ──► Frame (j) ──► [IMG to Shape: logo.gif] ──► Shape Out ──► Output (Return)
  ```
  
  In a tag node wired to `System/Output (Tags)`:
  ```
  {\p1\pos(syl.center, syl.middle)\1c&HFFFFFF&\bord0}
  ```
  Each video frame evaluates frame $j$ of the animated GIF, rendering clean vector graphics without raster pixelation.

---

## 13. Node `Shape/Multi` (Concentric Patterns and Nested Polygons)

* **Canonical Category:** `Shape` (UI: *Shape*)
* **Purpose:** Procedural generator for nested polygonal patterns, concentric grids, and parametric compound geometries.

![Shape/Multi](img/multi.png)

### 13.1. Procedural Generation Engines (`mode`)
The node incorporates 10 dedicated geometric algorithms:
1. **`concentric_squares`:** Nested concentric squares with configurable perimeter thickness and step.
2. **`diagonal_stripes`:** Stylised diagonal stripe hatch pattern bounded within width `width` and height `height`.
3. **`concentric_rings`:** Concentric circular rings or rings derived from a base guide silhouette (`base_shape`).
4. **`polygonal_mosaic`:** Regular polygonal mosaic governed by side count (`sides`) and concentric layer count (`n_layers`).
5. **`multi_shape_mosaic`:** Modular grid of distributed shapes with Cartesian translation steps (`dx`, `dy`).
6. **`segmented_border`:** Segmented perimeter frame with regular intervals and notches of length `length`.
7. **`radial_rosette`:** Circular rosette composed of radial angular petals or sectors (`parts`, `r_out`, `r_in`).
8. **`tunnel_cascade`:** Geometric tunnel cascade with diminishing scale (`size1`, `size2`), loops (`loop`), and progressive rotation (`angle`).
9. **`banner`:** Decorative plaque or stylised ribbon with selectable terminals (`tip_style`: Arrow, Fold) and fold flaps.
10. **`gear`:** Parametric mechanical cogwheel with tooth count (`teeth`), outer radius (`r_out`), inner radius (`r_in`), and central bore (`r_hole`).

### 13.2. Input Ports and Body Properties
1. **`Mode` (`mode`):** Active procedural generation algorithm selector.
2. **`Size` (`size`):** Base dimension of the outer pattern (default: `100.0`).
3. **`Px Pattern` (`px_pattern`):** Sequential thickness or separation pattern (accepts numeric values or comma-separated lists).
4. **`Separation` (`separation`):** Inter-layer spacing or dilation offset between neighbouring elements.
5. **`Factor (t)` (`t`):** Parametric progress ($0.0 \to 1.0$) for animating sequential emergence or scale.
6. **`Anchor` (`anchor`):** Spatial reference frame:
   * **`center`:** Centres compound generated geometry at Cartesian origin `(0, 0)`.
   * **`origin`:** Aligns top-left corner of bounding box at `(0, 0)`.
   * **`relative`:** Preserves relative displacement from parent without ink recentring.
   * **`absolute`:** Positions geometry directly at screen coordinates `(fx.pos_x, fx.pos_y)`.
7. **`Tags` (`tags`):** ASS tags or color attributes to interleave in emitted vector code.
8. **`Out Mode` (`out_mode`):** Emitted format (`Shape`, `\clip`, `\iclip`).
9. **`Loop Mode` (`loop_mode`):** Toggles between monolithic unified drawing (`Shape`) and piece-by-piece iteration (`Loops`, exposing footer variables `m_i` and `m_n`).

### 13.3. Output Ports (*Outputs*)
1. **`[3.1] Shape`:** Composite ASSdraw vector code (or active piece in `Loops` mode).

### 13.4. Practical Production Example
* **Decorative Backdrop Plaque Behind Dialogue:**
  Configuring `Shape/Multi` with `mode: banner`, `width: 260`, `height: 48`, and `anchor: center`:

  ```
  [Shape/Multi: banner, w=260, h=48] ──► Shape ──► Return ──► [System/Output]
  ```

  In a tag node wired to `System/Output (Tags)` set to an underlay layer (`layer: 0`):
  ```
  {\p1\pos(line.center, line.middle)\1c&H1A1A2E&\bord2\3c&HE94560&}
  ```
  Renders a sharp polygonal banner centred directly behind the dialogue line, serving as a stylised title plaque.
