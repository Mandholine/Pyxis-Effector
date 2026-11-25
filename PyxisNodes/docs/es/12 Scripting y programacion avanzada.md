# Programación y Uso de Nodos desde Código (`Script Code` y `Define Vars`)

Este volumen funciona como guía práctica de referencia para invocar los nodos, funciones auxiliares y formas vectoriales de Pyxis directamente desde código en [`System/Script Code`](04%20System.md#3-nodo-systemscript-code-ejecución-de-código-embebido-python-y-lua) (Python y Lua) y desde expresiones o asignaciones en [`Variables/Define Vars`](09%20Variables.md#2-nodo-variablesdefine-vars-definición-de-variables-locales).

> [!NOTE]
> La anatomía visual, puertos e interfaz de `System/Script Code` están documentados en el [Volumen 4: System](04%20System.md#3-nodo-systemscript-code-ejecución-de-código-embebido-python-y-lua). El catálogo completo de propiedades del contexto (`line.*`, `syl.*`, `char.*`, `word.*`, `fx.*`, `ink.*`, `prev.*`, `next.*`, `time.*`, `meta.*` e iteradores de sub-bucles) se detalla en el [Volumen 9: Variables](09%20Variables.md). Este volumen evita duplicar esas tablas y se centra exclusivamente en **cómo programar y combinar cada nodo desde código**.

### Organización Temática del Volumen:
* **Sección 12.A — Modelos de Ejecución y Alcance:** Diferencias reales entre `Define Vars`, `Script Code (Python)` y `Script Code (Lua)`, desempaquetado de tuplas y paso de `None` en funciones de nodos.
* **Sección 12.B — Biblioteca de Formas (`Shape/Library`) en Código:** Nomenclatura canónica sin guiones bajos, resolución con `shape.<nombre>`, `fx.shape.<nombre>`, `resolve_shape("shape.<nombre>")`, catálogo completo de 80 formas y composición vectorial en código.
* **Sección 12.C — Catálogo Completo de Uso de Nodos desde Código:** Firma, argumentos clave, salidas y ejemplos prácticos para los nodos de [`Basics`](#1-nodos-de-basics-y-helpers-de-tags-ass), [`Shape`](#2-nodos-de-shape-geometría-y-composiciones-en-código), [`Functions`](#3-nodos-de-functions-en-código), [`Time`](#4-nodos-de-time-y-atajos-temporales), [`Audio`](#5-nodos-de-audio-y-telemetría) y [`Variables / Loops / System`](#6-nodos-de-variables-loops-y-system).
* **Sección 12.D — Recetas Prácticas y Diagnóstico de Errores Frecuentes:** Flujos completos copiables y errores habituales al llamar nodos en script.

---

## Sección 12.A — Modelos de Ejecución y Reglas de Alcance

Antes de invocar funciones de Pyxis, conviene entender qué soporta exactamente cada bloque de código:

| Característica | `Variables/Define Vars` | `Script Code (Python)` | `Script Code (Lua)` |
| :--- | :--- | :--- | :--- |
| **Propósito principal** | Calcular e inyectar variables locales o mutar atributos antes de tags/salidas. | Lógica multipaso en Python, composición de nodos y múltiples salidas. | Lógica imperativa rápida sobre LuaJIT con tablas nativas. |
| **Retorno de resultado** | Asignaciones por línea o separadas por `;` (`x = ...`, `a, b = ...`). | Última expresión evaluada, `result = ...`, o diccionario `outputs[1..N]`. | `return ...`, `result = ...`, o tabla `outputs[1..N]`. |
| **Atajos sintácticos** | `2f`, `1.5r`, `2li`, hex `&HAABBGGRR&`, `~=`, ternaria Lua (`cond and A or B`) y Python (`A if cond else B`). | `2f`, `1.5r`, `2li`, sintaxis completa de Python 3. | Sintaxis estándar de Lua; usar `* frame_dur`, `* ratio`, `2 * li`. |
| **Acceso a funciones de nodos** | **Sí** (vía respaldo automático a Python; pasar `None` como primer argumento). | **Sí** (todas las funciones registradas de Pyxis; pasar `None` como primer argumento). | **No** (solo helpers integrados, no expone funciones de nodos Python). |
| **Acceso a `Shape/Library`** | `shape.<nombre>`, `resolve_shape("shape.<nombre>")`, `eval_shapes_lib_node(None, shape="<nombre>")`. | `fx.shape.<nombre>`, `resolve_shape("shape.<nombre>")`, `eval_shapes_lib_node(None, shape="<nombre>")`. | `resolve_shape("shape.<nombre>")` y alias heredados `shape_*()`. |
| **Desempaquetado / Indexación de tuplas** | **Indexación en expresión** (`x = func(None, ...)[0]`, ya que las llamadas a nodos se serializan al asignarse). | **Desempaquetado nativo** (`a, b, c = func(None, ...)`). | Solo donde un helper Lua devuelve múltiples valores (`polar`). |
| **Comentarios en línea** | `# comentario` y `-- comentario`. | `# comentario`. | `-- comentario`. |

### Regla Fundamental al Invocar Funciones de Nodos (`context = None`)

Todas las funciones de nodos expuestas en `Script Code (Python)` y `Define Vars` reciben `context` como **primer parámetro posicional** (muchas sin valor por defecto). Sin embargo, en el ámbito de ejecución del script **no existe una variable global llamada `context`** (las entidades se inyectan directamente como `syl`, `line`, `fx`, `ink`, `j`, etc.).

1. **Pase siempre `None` como primer argumento posicional** al llamar un nodo desde código:
   ```python
   # Correcto: primer argumento None y parámetros por nombre
   trazo = shape_stroke_node(None, shape=resolve_shape("shape.circle"), width=4.0)
   dx, dy = eval_math_node(None, category="geometry", operation="polar", angle=45, radius=80)
   ```
   ```python
   # Incorrecto: provocaría NameError ('context' is not defined) o TypeError
   trazo = shape_stroke_node(context, shape="m 0 0 l 10 10", width=4.0)
   trazo = shape_stroke_node(shape="m 0 0 l 10 10", width=4.0)
   ```
2. **Suministre los valores explícitos si el nodo normalmente leería del grafo:** Al pasar `None`, el nodo no lee coordenadas ni tiempos por defecto de una unidad implícita. Pase explícitamente `x`, `y`, `start_time`, `end_time`, `prog`, `shape`, etc. desde las variables de contexto (`syl.center`, `syl.syl_start`, `fx.pos_x`).
3. **Extraiga ranuras concretas de tuplas según el entorno:** Varios nodos devuelven tuplas de múltiples salidas (por ejemplo `shape_walker_node` o `clip_gradient_node`). En **`Script Code (Python)`** puede desempaquetarlas directamente (`a, b = ...`); en **`Define Vars`**, como cada asignación convierte el retorno del script a escalar/cadena, indexe directamente en el lado derecho la ranura deseada (`[0]`, `[1]`, etc.):
   ```python
   # En Script Code (Python): desempaquetado nativo
   shp, pos_tag, frz_ang, total_len, tip_x, tip_y = shape_walker_node(None, shape=fx.shape.circle, progress=0.5)

   # En Define Vars: indexar directamente la ranura en la misma expresión
   shp = shape_walker_node(None, shape=shape.circle, progress=0.5)[0]
   pos_tag = shape_walker_node(None, shape=shape.circle, progress=0.5)[1]
   ```

### Mutación de Contexto y Salidas Múltiples (`outputs` / `out`)

* **Lectura y escritura del estado del ciclo:** En `Script Code (Python)` y `Define Vars`, modificar `fx.pos_x`, `fx.pos_y`, `fx.st`, `fx.et`, `fx.layer`, `fx.align` o atributos editables de `syl.*`, `char.*`, `word.*`, `line.*` sincroniza los cambios hacia los nodos conectados aguas abajo.
* **Propiedades protegidas e inmutables:** Los tiempos base originales del archivo `.ass` (`line.start_time`, `line.end_time`, `line.dur`, `line.layer`, `syl.start_time`, `syl.end_time`) y metadatos del evento (`effect`, `actor`, `margins`, `queueid`, `queueorder`) están blindados contra sobrescritura accidental. Para desplazar la emisión de la línea resultante, modifique siempre `fx.st` / `fx.start_time`, `fx.et` / `fx.end_time` o `fx.layer`.
* **Múltiples puertos de salida en `Script Code`:**
  * Asignar `outputs[1]`, `outputs[2]` (o `out[1]`, `out[2]` en Python; `outputs[1]` en Lua) expone valores hacia los puertos adicionales del nodo cuando se añaden salidas en el editor.
  * El valor devuelto como última expresión (Python), `return` (Lua) o `result = ...` alimenta la salida principal `Result`.

---

## Sección 12.B — Biblioteca de Formas (`Shape/Library`) en Código

Las 80 formas vectoriales incluidas en `Shape/Library` siguen una **nomenclatura canónica estrictamente en minúsculas y sin guiones bajos** (`circangle`, `diamond`, `heart2t`, `flower1t`, `star10t`, `diagonal13r`, etc.). Toda referencia con guiones bajos en `shape.*` (como `shape.rounded_corners`) o nombres obsoletos (`shape.rect`, `shape.rhombus`, `shape.cross`, `shape.flower`) devuelve una cadena vacía.

### Formas de Invocar y Componer Presets en Código

1. **En `Define Vars` y parámetros en línea:** Use `shape.<nombre>` directamente:
   ```python
   base = shape.circangle
   flor = shape.flower1t
   ```
2. **En `Script Code (Python)`:** Use **`fx.shape.<nombre>`** o **`resolve_shape("shape.<nombre>")`** o **`eval_shapes_lib_node(None, shape="<nombre>")`**:
   ```python
   # Las tres formas producen el mismo trazado ASSDraw de flower1t
   f1 = fx.shape.flower1t
   f2 = resolve_shape("shape.flower1t")
   f3 = eval_shapes_lib_node(None, shape="flower1t")
   ```
   > [!IMPORTANT]
   > En `Script Code (Python)` el identificador suelto `shape.<nombre>` **no** está en el ámbito global: utilice `fx.shape.<nombre>` o `resolve_shape("shape.<nombre>")`.
3. **En `Script Code (Lua)`:** Utilice **`resolve_shape("shape.<nombre>")`**:
   ```lua
   local shp = resolve_shape("shape.heart2t")
   return "\\p1}" .. shp
   ```
4. **Regla obligatoria del prefijo `"shape."` en `resolve_shape()`:**
   `resolve_shape(valor)` distingue entre presets de la librería, trazados ASSDraw (`m ... l ...`) y texto plano:
   * `resolve_shape("shape.star")` carga el preset de estrella de 5 puntas de la librería.
   * `resolve_shape("star")` (**sin** `"shape."`) convierte literalmente la palabra `"star"` en contornos vectoriales usando la tipografía activa del contexto.
   * También acepta listas o JSON en Python/Define Vars: `resolve_shape(["shape.circle", "shape.star1t"])` devuelve la lista de ambos trazados resueltos.

### Catálogo Completo de los 80 Identificadores Canónicos

| Familia | Identificadores Canónicos (`<nombre>`) | Cantidad |
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
> **Funciones heredadas en desuso:** Por compatibilidad con plantillas antiguas siguen existiendo 11 funciones sin prefijo de librería (`shape_circle()`, `shape_square()`, `shape_rectangle()`, `shape_triangle()`, `shape_rhombus()`, `shape_rounded_corners()`, `shape_pentagon()`, `shape_hexagon()`, `shape_octagon()`, `shape_star()`, `shape_heart()`). Para código nuevo utilice siempre los 80 nombres canónicos mediante `shape.<nombre>`, `fx.shape.<nombre>` o `resolve_shape("shape.<nombre>")` (por ejemplo `circangle` en lugar de `rounded_corners` y `diamond` en lugar de `rhombus`).

### Composición Procedural de Formas en Código

Al encadenar un preset con nodos de `Shape/*` en Python o `Define Vars`, el trazado se escala, centra, bordea o recorta sin cablear múltiples nodos en el lienzo:

```python
# Escalar una flor al centro (0,0), aplicar borde hueco de 3px y restar un circulo central
base = resolve_shape("shape.flower10t")
escalada = shape_manipulator(None, drawing=base, op_mode="scale", scale_x=0.8, scale_y=0.8, mode="center")
agujero = shape_manipulator(None, drawing=fx.shape.circle, op_mode="scale", scale_x=0.35, scale_y=0.35, mode="center")
anillo = shape_clipper_node(None, shape_a=escalada, shape_b=agujero, mode="difference", anchor="center")
borde = shape_stroke_node(None, shape=anillo, width=3.0, join_mode="round")
```

---

## Sección 12.C — Catálogo Completo de Uso de Nodos desde Código

Esta sección cubre los 69 nodos canónicos de Pyxis agrupados en sus 8 categorías: qué función Python o helper directo los representa, sus parámetros clave, su formato de retorno y cuándo un nodo pertenece exclusivamente a la topología visual del grafo.

---

### 1. Nodos de `Basics` y Helpers de Tags ASS

#### 1.1 Helpers Nativos de Tags ASS (Python, Lua y `Define Vars`)
Sustituyen de forma compacta al nodo `Basics/MultiTag` dentro de scripts:

| Función | Equivalente ASS | Notas de firma y uso |
| :--- | :--- | :--- |
| `pos(x, y)` | `\pos(x,y)` | Acepta números o expresiones evaluadas. |
| `move(x1, y1, x2, y2[, t1, t2])` | `\move(...)` | Si se omiten `t1, t2`, emite versión corta de 4 argumentos. |
| `org(x, y)` | `\org(x,y)` | Pivote de rotación/escala 2D/3D. |
| `fad(in_ms, out_ms)` | `\fad(t1,t2)` | Fundido de entrada y salida. |
| `fade(a1, a2, a3, t1, t2, t3, t4)` | `\fade(...)` | Fundido complejo en 3 niveles alfa. |
| `clip(...)` / `iclip(...)` | `\clip(...)` / `\iclip(...)` | Acepta 4 números `(x1,y1,x2,y2)` o 1 cadena vectorial `(drawing)` o `(scale, drawing)`. |
| `c1(c)`..`c4(c)` / `color_1(c)`..`color_4(c)` | `\1c...` a `\4c...` | Acepta `#RRGGBB` o `&HBBGGRR&`. |
| `a1(a)`..`a4(a)` / `alpha(a)` | `\1a...` a `\4a...`, `\alpha...` | Acepta enteros `0..255` o `&HXX&`. |
| `trans(t1, t2[, accel], tags)` / `trans(tags)` | `\t(...)` | Admite 1, 3 o 4 argumentos. |
| `fscx(v)`, `fscy(v)`, `fscxy(x[, y])` | `\fscx`, `\fscy` | `fscxy(x)` aplica el mismo valor a X e Y. |
| `frz(v)`, `frx(v)`, `fry(v)`, `fax(v)`, `fay(v)` | Rotación y sesgado | Grados para `fr*`; factor decimal para `fa*`. |
| `bord(v)`, `shad(v)`, `blur(v)`, `an(v)` | Borde, sombra, desenfoque, anclaje | Escalar numérico (`an(5)`). |
| `ass_color(r, g=None, b=None)` / `ass_alpha(a)` | `&HBBGGRR&` / `&HAA&` | También convierte `#RRGGBB` si se pasa un solo argumento en `ass_color("#FF8800")`. |
| `random_color()` / `random_alpha()` | Color o alfa aleatorio ASS | Devuelve cadena hex ASS lista para concatenar. |
| `tag_only(cond, tag)` | `tag` o `""` | Disponible en Python (`Script Code`). |

#### 1.2 `Basics/MultiTag` -> `tag_master(...)`
Genera cualquier etiqueta ASS o Dark Tag soportado por `MultiTag` desde Python o `Define Vars`.
* **Firma:** `tag_master(None, tag_type="pos", **kwargs)`
* **Parámetros clave:** `tag_type` (`"pos"`, `"move"`, `"org"`, `"fscx"`, `"fscy"`, `"frz"`, `"1c"`, `"alpha"`, `"clip"`, `"blur"`, etc.) más los parámetros nominales del tag (`x`, `y`, `x1`, `y1`, `x2`, `y2`, `t1`, `t2`, `val`, `shape`, etc.).
* **Ejemplo:**
  ```python
  t_pos = tag_master(None, tag_type="pos", x=syl.center, y=syl.middle)
  t_rot = tag_master(None, tag_type="frz", val=15)
  ```

#### 1.3 `Basics/Math` -> `eval_math_node(...)` y Helpers Matemáticos
* **Helpers directos (Python, Lua y `Define Vars`):**
  * Límites y mapeo: `clamp(val, min_val=0.0, max_val=1.0)`, `lerp(a, b, t)`, `map_range(val, in_min, in_max, out_min, out_max)` (alias `map_value`), `ipol(t, a, b, curve="linear")`.
  * Curvas de aceleración (`t` en `[0, 1]`): `ease_in(t)`, `ease_out(t)`, `ease_in_out(t)`, `cubic_in(t)`, `cubic_out(t)`, `elastic(t)`, `bounce(t)`, `back(t)`.
  * Ondas periódicas: `sine_wave(t, freq=1.0, amp=1.0, offset=0.0)`, `square_wave(...)`, `triangle_wave(...)`, `sawtooth_wave(...)`.
  * Geometría y Bézier: `polar(angle_deg, dist)` devuelve tupla `(dx, dy)` (en Python/Define Vars) o dos valores en Lua (`local dx, dy = polar(45, 80)`); `bezier(t, p0, p1, p2, p3)` evalúa **escalares por eje** (no tuplas).
* **Llamada completa al nodo (`ke.math`):** `eval_math_node(None, category="numeric", operation="round", **kwargs)`
  * Categorías y operaciones disponibles (27 operaciones en 5 categorías):
    * `category="numeric"`: `round` (`value`, `decimal`), `clamp` (`num`, `min_val`, `max_val`, `cycle`), `rand` (`num1`, `num2`, `step`, `range`, `sign`), `factk` (`n`), `to16` (`num`), `equality` (`n1`, `n2`, `tolerance`), `between` (`num`, `n1`, `n2`).
    * `category="sequence"`: `i` (`counter`, `seq_mode`, `a`, `b`, `c`), `count` (`init`, `step`, `seq_mode`, `a`, `b`, `c`, `node_id`), `normalize` (`t`, `accel`, `shape`), `ipol` (`values`, `t`, `accel`, `shape`, `size`).
    * `category="geometry"`: `angle` (`p1`, `p2`, `p3`), `polar` (`angle`, `radius`, `get`), `distance` (`p1`, `p2`), `intersect` (`s1`, `s2`), `circle` (`p1`, `p2`, `p3`), `rotate` (`p`, `angle`, `axis`).
    * `category="algebra"`: `quadratic` (`c1`, `c2`, `c3`), `cubic` (`c1`, `c2`, `c3`, `c4`), `resolve` (`coefficients`), `equation` (`coefficients`, `reals`), `evaluate` (`coefficients`, `t`), `gauss` (`matrix`), `matrix` (`matrix_op`, `matrix_a`, `matrix_b`, `angles`, `is_row`).
    * `category="data"`: `getpair` (`val`, `defx`, `defy`), `getnumbers` (`val`), `format` (`fmt`, `values`).
* **Ejemplo:**
  ```python
  patron = eval_math_node(None, category="sequence", operation="i", counter=syl.i, seq_mode="+,-", a=1)
  px, py = eval_math_node(None, category="geometry", operation="polar", angle=45, radius=80)
  ```

#### 1.4 `Basics/MultiRandom` -> `R*`, `by` y `math_random_master(...)`
* **Helpers deterministas directos (Python, Lua y `Define Vars`):**
  * `R(mn, mx[, step])`, `Rs` (con signo), `Rc` (centésimas `0.01`), `Rd` (décimas `0.1`), `Rm` (milésimas `0.001`), `Rds`/`Rcs`/`Rms` (decimales con signo), `Rr` (`R`), `Rstep(mn, mx, step)` (discreto por paso), `R2d(mn, mx)` (2D), `Rbool(prob=50.0)`, `Rcolor(c1, c2)`, `Re("op1,op2,op3")`, `Rfake(...)`, alias `rand`.
  * **Ámbito determinista `by`:** Puede pasar `by=by.syl`, `by=by.char`, `by=by.word`, `by=by.line`, `by=by.j`, `by=by.s` como argumento a cualquier `R*`, o encadenarlo como método (`by.syl.R(10, 50)`, `by.line.Rcolor("#FF0000", "#0000FF")`, `by.j.Rbool(40)`).
* **Llamada completa al nodo:** `math_random_master(None, mode="R", min_val=None, max_val=None, step=None, options="", counter="", total=1, output_slot_index=0, iterator="", by="")` (`output_slot_index=1` genera la lista por lotes cuando `total > 1`).

#### 1.5 `Basics/Text` -> `eval_text_node(...)`, `text_romaji_to_karaoke(...)` y Helpers
* **Helpers rápidos (Python, Lua y `Define Vars`):** `strip_tags(texto)` y `kana(texto)` (conversión/limpieza japonesa).
* **Llamada completa al nodo `Basics/Text`:**
  `eval_text_node(None, operation="strip_tags", text="", ...)`
  * `operation`: `"strip_tags"`, `"uppercase"`, `"lowercase"`, `"cleanspaces"`, `"replace"` (`Search`, `Replace With`), `"substring"` (`Start`, `Length`), `"length"`, `"contains"`, `"transliteratekana"`, `"romajitokaraoke"`.
* **Helper fonético directo:** `text_romaji_to_karaoke(None, text="sakura", duration=1200, kmode="k")` devuelve `"{\k400}sa{\k400}ku{\k400}ra"`.

#### 1.6 `Basics/Builder` y Nodos Puros de Datos/Flujo
* **`Basics/Builder` -> `BuilderNode(None, items_in=None, mode="text", sub_mode="splitter", split_by="syl", source="active_unit", repeat="2", custom_text="", delim=",", shape_layout="auto", shape_split_mode="subpaths")`:** Extrae la lista de piezas/fragmentos de texto o forma preparados para ensamblado monolinea (`list[str]`). En `Define Vars` o `Script Code`, el ensamblado de etiquetas por pieza se realiza concatenando cadenas directamente en bucle `for`.
* **Nodos con equivalentes nativos del lenguaje (no requieren llamada a nodo):**
  * `Basics/Number` y `Basics/String` -> literales numéricos o cadenas (`100`, `"\\blur2"`).
  * `Basics/Color Picker` -> `ass_color(r, g, b)` / `ass_color("#RRGGBB")` o tuplas/listas de hex ASS.
  * `Basics/Concatenate` y `Basics/Dynamic Format` -> `f"{a}{b}"` / `",".join(lista)` en Python, `a .. b` o `string.format(...)` en Lua.
  * `Basics/Only` -> condicionales `if ... else ...` o `tag_only(cond, tag)`.
  * `Basics/Once` -> `is_first` / `syl.i == 1` o `remember("clave", valor)` en el primer ciclo.

---

### 2. Nodos de `Shape` (Geometría y Composiciones en Código)

Todas las funciones de `Shape/*` admiten trazados de `Shape/Library` resueltos (`fx.shape.*`, `shape.*` o `resolve_shape("shape.<nombre>")`) y devuelven ASSDraw listo para `\p1` o `\clip(...)`.

| Nodo | Función Python (`Script Code` / `Define Vars`) | Parámetros Principales | Valor de Retorno |
| :--- | :--- | :--- | :--- |
| `Shape/Library` | `eval_shapes_lib_node(None, shape="circle")` | `shape` (nombre canónico o `"shape.<nombre>"`) | `str` (ASSDraw) |
| `Shape/Manipulator` | `shape_manipulator(None, drawing="", op_mode="scale", scale_x=1.0, scale_y=1.0, rot=0.0, offset_x=0.0, offset_y=0.0, offset_border=0.0, mode="center", density=2.0, angle_x=0.0, angle_y=0.0, angle_z=0.0, axis=None, t=1.0, skew_x=0.0, skew_y=0.0)` | `op_mode`: `"scale"`, `"rotate"`, `"offset"`, `"offset_border"`, `"perspective"`, `"skew"`, `"subdivide"`, `"invert"`; `mode` define anclaje (`"center"`, `"origin"`, `"relative"`, `"absolute"`, `"pos"`). | `str` (ASSDraw) |
| `Shape/Transform` | `shape_transform(None, drawing="", mode="inflate", t=None, ratio=1.0, inflate_mode="circle", anchor="center", angle_x=0.0, angle_y=0.0, radius=10.0, corner_mode="round", curve=None, bend_t=1.0, axis="x", target_shape="", mid_shape="", step_px=0.0)` | `mode`: `"inflate"`, `"3d_tilt"`, `"round_corners"`, `"bend"`, `"morph"`, `"resample"`. | `str` (ASSDraw) |
| `Shape/Filter` | `shape_filter(None, drawing="", mode="vertices", expr_x="x", expr_y="y", t=1.0, subdivs=0.0, rot_step=0.0, scale_step=100.0, offset_x=0.0, offset_y=0.0, anchor="center", radius_x=5.0, radius_y=5.0, seed=0)` | `mode`: `"vertices"` (evalúa fórmulas `expr_x`/`expr_y` por vértice), `"echo"`, `"jitter"`. | `str` (ASSDraw) |
| `Shape/Multi` | `shape_multi(None, drawing="", mode="concentric_squares", size=100.0, width=70.0, height=50.0, px="4", bord="4", space=0.0, length=20.0, sides=6, rings=1, n_layers=25, dx=0.0, dy=0.0, parts=12, r_out=50.0, r_in=0.0, size1=100.0, size2=10.0, loop=8, separation=0.0, angle=0.0, t=1.0, anchor="center", tags="", out_mode="shape", loop_mode="shape", tip_style="Arrow", fold_w=0.0, slant=0.35, r_hole=15.0, order="normal")` | `mode`: `"concentric_squares"`, `"polygon"`, `"arrow"`, `"banner"`, `"spiral"`, `"starburst"`, etc. (ver [Vol. 6](06%20Shapes.md)). | `str` (ASSDraw o tags según `out_mode`) |
| `Shape/Stroke` | `shape_stroke_node(None, shape="", width=4.0, join_mode="round", cap_mode="bezier", miter_limit=2.0)` | `join_mode`: `"round"`, `"miter"`, `"bevel"`; `cap_mode`: `"bezier"`, `"round"`, `"square"`, `"flat"`. | `str` (ASSDraw del contorno) |
| `Shape/Clipper` | `shape_clipper_node(None, shape_a="", shape_b="", mode="difference", delta=0.0, subj_fill="evenodd", clip_fill="evenodd", join_type="round", end_type="closed_polygon", miter_limit=2.0, post_offset="", clean_dist=0.0, anchor="center", out_mode="shape")` | `mode`: `"difference"`, `"intersection"`, `"union"`, `"xor"`, `"offset"`, `"minkowski_sum"`, `"minkowski_diff"`; `out_mode`: `"shape"` o `"clip"`. | `str` (o `list` según `out_mode`) |
| `Shape/Union & Divide` | `shape_union_divide_node(None, drawing="", shape_b="", mode=None, anchor=None, fill_type=None, clean_self_intersect=None, index_j=None, index_d=None, order=None)` | `mode`: `"union"`, `"divide"`, `"split"`, `"extract"`, `"holes"`. | `str` o `list[str]` |
| `Shape/Concentric Borders` | `shape_concentric_borders_node(None, shape="", separation=5.0, overlap=0.5, scale=1.0, mode="hollow", loop_count=5, out_mode="shape", anchor="relative")` | `mode`: `"hollow"`, `"filled"`, `"rings"`; `anchor`: `"relative"`, `"center"`, `"pos"`, etc. | **Tupla (4):** `(shape_out, pos_str, ring_idx, total_rings)` |
| `Shape/Array` | `shape_array_node(None, particle=..., mode="grid", out_mode="loops", cols=5, rows=3, spacing_x=0.0, spacing_y=0.0, explosion=0.0, rings=3, radius=50.0, radius_step=30.0, rotate_step=0.0, count=20, turns=2.0, max_radius=100.0, angle_step=0.0, area_width=150.0, area_height=100.0, scale=1.0, t=1.0, anchor="pieces", order="79", seed=1, tags="")` | `mode`: `"grid"`, `"circle"`, `"spiral"`, `"random"`; `out_mode`: `"shape"` o `"loops"`. | **Tupla (9):** `(shape_out, pos_str, x, y, angle, a_i, a_n, col, row)` |
| `Shape/Walker` | `shape_walker_node(None, shape="", progress=1.0, start_t=0.0, mode="global", invert=False, subdivs=30, close_path=False)` | `progress` en `0.0..1.0`; `mode`: `"global"` o `"per_contour"`. | **Tupla (6):** `(shape_out, pos_tag, frz_angle, total_len, tip_x, tip_y)` |

> [!NOTE]
> **Nodos solo de topología en `Shape`:** `Shape/Slicer` y `Shape/IMG to Shape` no tienen función directa en código porque `Slicer` genera sub-iteraciones completas del grafo (`s_i`, `s_n`) y `IMG to Shape` orquesta el pipeline de Potrace sobre archivos de disco dentro del motor de grafo. Conecte esos nodos en el lienzo y consuma sus iteradores o puertos desde `Define Vars` o `Script Code`.

---

### 3. Nodos de `Functions` en Código

| Nodo | Función Python o Helper Equivalente | Parámetros Clave y Ranuras (`output_slot_index`) | Valor de Retorno |
| :--- | :--- | :--- | :--- |
| `Functions/Conditioner` | `node_conditioner(None, condition=True, if_true="", if_false="")` | También sustituible por `A if cond else B` en Python / `Define Vars`. | Valor elegido (`Any`) |
| `Functions/Color Gradient` | `node_color_gradient(None, prog="0.5", colors_str="#FF0000,#0000FF", total=1, accel=1.0, tag_type="\\1c", output_slot_index=0)` | `output_slot_index`: `0` = color hex ASS (`&H..&`); `1` = lista separada por comas de colores; `2` = lista de tags formateados (`\1c&H..&`). | `str` |
| `Functions/Tag Oscillator` | `tag_oscillator_node(None, start_time=0, end_time=1000, step_ms=200.0, trans_ms=50.0, duty_cycle=None, tags="\\frz30,\\frz-30", accel=1.0, dilat_step_ms=0.0, dilat_trans_ms=0.0, offset_seq_ms=0.0, rhythm_pattern="", mode=None, order_mode=None, output_slot_index=0)` | `output_slot_index`: `0` = secuencia `\t(...)` completa; `1` = tag activo; `2` = lista de keyframes; `3` = lista de tags. | `str` o `list` |
| `Functions/Glitter` | `glitter_node(None, start_time=0, end_time=1000, density=1.0, mode="R", seed=0, tags="\\alpha", mins="&H00&", maxs="&HFF&", output_slot_index=0)` | `tags`, `mins` y `maxs` aceptan cadenas separadas por comas o listas; `output_slot_index=0` devuelve bloque completo, `1` la primera fila de tag. | `str` |
| `Functions/Clip Gradient` | `clip_gradient_node(None, cols=5, rows=1, angle=0, padding=0, pad_top=0, pad_bottom=0, pad_left=0, pad_right=0, overlap=0.5, order="79", out_mode="clip")` | `out_mode`: `"clip"`, `"iclip"` o `"shape"`. | **Tupla (6):** `(output, progress, index, total, col, row)` |
| `Functions/Move Tag` | `MoveTagNode(None, mode="Trajectory", tags=None, shape="", points=None, dx=0.0, dy=0.0, dur=200, seed=0, step_px=7.5, anchor="center", t1=0, t2=None, accel=1.0)` | `mode`: `"Trajectory"`, `"Waypoints"`, `"Jitter"`. | `str` (bloque ASS `\t(...)`) |
| `Functions/Move Text` | `MoveTextNode(None, text="", tags=None, dx=0.0, dy=0.0, ox=0.0, oy=0.0, trajectory=None, anchor="center", shape="", points=None, step_px=7.5, t1=0.0, t2=None, accel=1.0)` | Desplaza texto sin resetear `\pos` mediante espaciadores `\fsp` y saltos `\N`. | `str` (bloque ASS compuesto) |
| `Functions/Tag Manipulator` | `TagManipulatorNode(None, mode="Invert", tags="", target_tag="")` | `mode`: `"Invert"`, `"Reset"`, `"Extractor"`. | `str` o escalar |
| `Functions/Animation` | `AnimationNode(None, frames="", step_ms=41.7, start_time="", end_time="", mode="fbf", alpha_tag="\\alpha", order="sequential", output_slot_index=0, anchor="relative", base="0")` | `frames`: lista Python o cadena delimitada; `mode`: `"fbf"` o `"alpha"`; `output_slot_index`: `0` = forma/tag activo, `1` = índice, `2` = lista procesada. | `str`, `int` o `list` |
| `Functions/Text on Path` | `text_on_path_node(None, shape="", mode="Center", offset=0.0, extra_angle=0.0, subdivs=30)` | `offset` en `0.0..1.0` a lo largo del trazado vectorial. | **Tupla (6):** `(tag_out, pos_tag, frz_tag, x, y, length)` |
| `Functions/IMG to pixels` | `particle_image_node(None, image_path="", particle_shape="", frame="1", step=2, alpha_threshold=128, scale=1.0, anchor="center", order="79", frame_idx=None)` | Lee píxeles de imagen o fotograma GIF. | **Tupla (6):** `(abs_x, abs_y, color_ass, alpha_ass, shape_str, total_pixels)` |

**Equivalentes directos para el resto de nodos de `Functions`:**
* `Functions/Polar to Cartesian` -> **`polar(angle_deg, dist)`** (devuelve `(dx, dy)`; sumar luego a `fx.pos_x` y `fx.pos_y`).
* `Functions/Bezier Curve` -> **`bezier(t, p0, p1, p2, p3)`** llamado por separado para X e Y.
* `Functions/Interpolator` -> **`lerp(a, b, t)`**, **`ipol(t, a, b, curve)`** y **`map_range(val, in_min, in_max, out_min, out_max)`**.
* `Functions/Text to Shape` -> **`resolve_shape(texto)`** pasando texto plano **sin** prefijo `"shape."` (ej. `resolve_shape(syl.text_stripped)`).
* `Functions/Particles` -> Nodo solo de topología de grafo (emite sub-bucle iterativo `p_i`, `p_n`).

---

### 4. Nodos de `Time` y Atajos Temporales

Pyxis inyecta objetos dinámicos de tiempo tanto en `Define Vars` como en `Script Code` (Python y Lua):

#### 4.1 Atajos de Desfase de Fase y Macros Numéricas
* **Objetos multiplicables:** `li` (Lead In), `lo` (Lead Out), `m1` (Middle 1), `m2` (Middle 2), `l1` (Loop 1), `l2` (Loop 2).
* **Sintaxis compacta (Python y `Define Vars`):** `2li` o `2 * li` equivale a un paso de `2` ms en Lead In; `li()` usa el retardo por defecto (`40` ms); `li(60)` usa `60` ms por unidad; `li + 150` suma un desfase fijo. En Lua use multiplicación explícita (`2 * li` o `li(60)`).
* **Macros de unidad (Python y `Define Vars`):** `10f` multiplica `10 * frame_dur` (~417.08 ms a 23.976 fps); `1.5r` multiplica `1.5 * ratio` (progreso `m_i / m_n` o `j / maxj`).
* **Funciones explícitas (equivalentes a los 6 nodos de desfase):**
  * `time_lead_in(delay=40, base=None)` / `time_lead_out(delay=40, base=None)`
  * `time_middle_1(delay=30, base=None)` / `time_middle_2(delay=30, base=None)`
  * `time_loop_1(delay=30, mode="leadin", base=None)` / `time_loop_2(delay=30, mode="leadin", base=None)`

#### 4.2 Utilidades Temporales, `Retime` y `Synced`
* **`Time/Duration`:** `duration(syl)` o `time_duration(None, start_time=t1, end_time=t2)` -> milisegundos (`float`).
* **`Time/Offset`:** `time_offset(None, base=t, offset_ms=-150)` -> `t + offset_ms`.
* **`Time/Ipol`:** `time_ipol(None, dur_ms=1000, points="0,100,200", accel=1.0)` -> cadena o brackets segmentados en ms.
* **`Time/Parse ASS Time`:** `parse_ass_time("0:00:01.55")` o `time_parse_ass(None, ass_time="0:00:01.55")` -> `1550` (`int`).
* **`Time/Format ASS Time`:** `format_ass_time(1550)` o `time_format_ass(None, time=1550)` -> `"0:00:01.55"`.
* **`Time/Time to Frame`:** `time_to_frame(ms, fps=23.976)` o `time_to_frame_node(None, time=ms, frame_dur=frame_dur, mode="Round", source="Custom")` (`mode`: `"Ceil"`, `"Floor"`, `"Round"`).
* **`Time/Frame to Time`:** `frame_to_time_node(None, frames=24, frame_dur=frame_dur, format="MS", source="Custom")` (`format`: `"MS"`, `"HMS"`, `"SEC"`).
* **`Time/Retime`:** `RetimeNode(None, phase="abs", tags="\\fscx150", offset_in=0, offset_out=0, accel=1.0, custom_start=100, custom_end=500)` (en llamadas directas con `None`, use `phase="abs"` con `custom_start`/`custom_end`, o use en `Define Vars`/`Script Code` los tiempos locales de unidad `syl.syl_start`, `syl.syl_end` dentro de `trans(...)`).
* **`Time/Synced`:** Utilice directamente el objeto inyectado **`sync`** (`sync.next`, `sync.prev`, `sync.order_next`, `sync.style_next`, `sync.actor_next`, `sync.effect_next`, `sync.layer_next` y sus equivalentes `*_prev`) o `calculate_sync_gap(maxgap=2000)`. La función `time_synchronized_extra_node` requiere estar evaluándose dentro de una línea activa del grafo para calcular compensaciones multi-línea automáticas.

---

### 5. Nodos de `Audio` y Telemetría

#### 5.1 Helpers de Telemetría (Python, Lua y `Define Vars`)
Devuelven energía normalizada lista para modular escalas, desenfoques o colores en cualquier instante temporal:
* **`audio_rms(start_ms=None, end_ms=None, gain=1.0, audio_path=None)` -> `float`:** Energía media cuadrática en el intervalo indicado.
* **`audio_peak(start_ms=None, end_ms=None, gain=1.0, audio_path=None)` -> `float`:** Amplitud pico en el intervalo indicado.
* **`audio_band(start_ms=None, end_ms=None, min_hz=20.0, max_hz=250.0, gain=1.0, audio_path=None)` -> `float`:** Energía aislada en una banda de frecuencia (por ejemplo sub-graves `20`–`150` Hz).
* **`audio_fft(start_ms=None, end_ms=None, num_bands=16, min_hz=20.0, max_hz=16000.0, gain=1.0, audio_path=None)` -> `list[float]`:** Lista con el espectro distribuido en `num_bands` bandas logarítmicas.

> [!TIP]
> Si el usuario ya asignó un archivo de audio maestro en el panel de previsualización o mediante `Audio/Modulator` / `Audio/Waveform`, puede omitir `audio_path` (o pasar `""`/`None`) para que Pyxis lea automáticamente la fuente de audio por defecto del proyecto.

#### 5.2 Nodos Completos de Audio (`Script Code (Python)` y `Define Vars`)
* **`Audio/Modulator`:** `audio_modulator_node(None, audio_path="", tag_name="fscy", min_val="100", max_val="160", gain="1.0", step_ms="41.7", smoothing="0.2", mode="rms", min_hz="20", max_hz="250", start_time="", end_time="", output_slot_index=0)`
  * `output_slot_index`: `0` = secuencia `\t(...)`, `1` = valor escalar actual, `2` = arreglo de valores, `3` = promedio RMS.
* **`Audio/Waveform`:** `audio_waveform_node(None, audio_path="", mode="oscilloscope", width="400", height="60", samples="32", gain="1.0", thickness="2", min_hz="20", max_hz="16000", scale="1.0", smoothing="0.2", start_time="", end_time="", anchor="center", output_slot_index=0)`
  * `output_slot_index`: `0` = trazado ASSDraw, `1` = tag `\pos`, `2` = arreglo X, `3` = arreglo Y, `4` = arreglo de bandas.

---

### 6. Nodos de `Variables`, `Loops` y `System`

* **`Variables/Memory` -> `remember(clave, valor)` y `recall(clave, defecto="")`:**
  Disponibles directamente en Python, Lua y `Define Vars` durante la ejecución de un grafo para guardar posiciones iniciales, colores sorteados en la primera pasada o estados acumulados entre iteraciones (en `Define Vars` admite además un tercer argumento booleano condicional: `remember("c0", random_color(), is_first)`). También existe la función `memory_node(None, ...)`.
* **`Variables/Define Vars`, `Variables/Get Var`, `Variables/Sys Var`:**
  Dentro de `Script Code` o `Define Vars`, lea y escriba variables por nombre directo (`mi_angulo = syl.i * 15`, `fx.pos_x = syl.center + 10`) sin necesidad de llamar a `get_var_node`, `sys_var_node` o `define_vars_node`.
* **`Loops/Main Loop`, `Loops/MaxLoop`, `Loops/Module`:**
  Controlan cuántas líneas/unidades/iteraciones emite el DAG y no se sustituyen llamando a `main_loop_node(None)` desde código. En su lugar, consulte directamente `i`, `n`, `j`, `maxj`, `ratio` (`module`) y la propiedad de preservación `syl.tags` / `line.tags` cuando `preserve_tags` está activo en `Main Loop`. Asimismo, toda línea expone el juego canónico `line.<prop>_org` (`l.<prop>_org`) con los nombres de propiedad del estilo y los valores iniciales de los tags ASS de la línea (con respaldo automático a `styleref`, excluyendo tiempos de karaoke y `\t(...)`): `color1_org`..`color4_org`, `alpha_org`, `alpha1_org`..`alpha4_org`, `fontname_org`, `fontsize_org`, `scale_x_org`, `scale_y_org`, `spacing_org`, `bold_org`, `italic_org`, `underline_org`, `strikeout_org`, `encoding_org`, `q_org`, `align_org`, `frz_org`, `frx_org`, `fry_org`, `fax_org`, `fay_org`, `pos_org`, `org_org`, `outline_org`, `xbord_org`, `ybord_org`, `shadow_org`, `xshad_org`, `yshad_org`, `blur_org`, `be_org`, `fad_org`, `clip_org`, `iclip_org`; junto con el Dark Tag `!line.<prop>!` (ej. `\1c!line.color4!`, `\bord!line.shadow!`, `\13c!line.color1!`) para inyectar cualquier propiedad conservada en cualquier tag de la plantilla ASS.
* **`System/Output`, `System/Previewer`, `System/Script Code`, `System/Benchmark Math`:**
  Nodos estructurales de emisión final, previsualización en navegador WASM y benchmark de rendimiento; siempre operan como bloques en el lienzo.

---

## Sección 12.D — Recetas Prácticas (`Define Vars` + `Script Code`)

### Receta 1 — `Define Vars`: Indexación de Tuplas y Formas de la Librería
Prepare variables geométricas en una sola pasada de `Define Vars` para consumirlas luego en `MultiTag` o en cadenas de texto:

```python
-- Forma canonica de la libreria (sin guiones bajos) y contorno de 3 px
flor_base = shape.flower10t
flor_contorno = shape_stroke_node(None, shape=flor_base, width=3.0, join_mode="round")

-- Indexado de las ranuras 0 (clip) y 1 (progreso) de Clip Gradient (cols=4, rows=1)
clip_tira = clip_gradient_node(None, cols=4, rows=1, angle=15, out_mode="clip")[0]
clip_prog = clip_gradient_node(None, cols=4, rows=1, angle=15, out_mode="clip")[1]

-- Color degradado interpolado segun el progreso de la tira actual
color_tira = node_color_gradient(None, prog=clip_prog, colors_str="#FF4E50,#FC913A,#F9D423", tag_type="\\1c", output_slot_index=0)
```

### Receta 2 — `Script Code (Python)`: Insignia Procedural con Múltiples Salidas (`outputs`)
Combina `resolve_shape("shape.circangle")`, `shape_manipulator`, `shape_clipper_node` y `node_color_gradient` devolviendo el dibujo en `Result` y los tags en `outputs[1]`:

```python
# Escala un rectangulo redondeado al tamaño de tinta de la silaba + margen
base = resolve_shape("shape.circangle")
sx = (ink.width + 24.0) / 100.0
sy = (ink.height + 14.0) / 100.0
tarjeta = shape_manipulator(None, drawing=base, op_mode="scale", scale_x=sx, scale_y=sy, mode="center")

# Perforar una estrella en el centro usando Clipper2
estrella = shape_manipulator(None, drawing=fx.shape.star1t, op_mode="scale", scale_x=0.22, scale_y=0.22, mode="center")
insignia = shape_clipper_node(None, shape_a=tarjeta, shape_b=estrella, mode="difference", anchor="center")

# Color segun indice de silaba
prog = (syl.i - 1) / max(1, syl.n - 1)
c_fondo = node_color_gradient(None, prog=prog, colors_str="#1E3C72,#2A5298,#E94057", output_slot_index=0)

outputs[1] = pos(syl.center, syl.middle) + an(5) + c1(c_fondo) + bord(0)
result = insignia
```

### Receta 3 — `Script Code (Python)`: Órbita Cinética, Audio Reactivo y Stagger `li` / `lo`
Calcula una órbita alrededor de la sílaba con reacción a sub-graves y temporización por macros `li` / `lo`:

```python
# Tiempos escalonados usando el retraso nativo de fase
t_in = syl.i * 35 - 200
fx.st = line.start_time + t_in
fx.et = line.end_time + 180

# Desplazamiento polar determinista por silaba y pulso de audio en graves (20-160 Hz)
ang = R(0, 360, by=by.syl) + (j * 25)
radio = 18.0 + audio_band(syl.start_time, syl.end_time, min_hz=20, max_hz=160, gain=1.2) * 35.0
dx, dy = polar(ang, radio)

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

### Receta 4 — `Script Code (Lua)`: Destello Persistente por Carácter con `resolve_shape`
Aprovecha `remember` / `recall` en Lua junto con `resolve_shape("shape.star4t")` y `by.char`:

```lua
local clave = "col_" .. tostring(char.i)
local col = recall(clave, "")
if col == "" then
    col = by.char.Rcolor("#FFE259", "#FFA751")
    remember(clave, col)
end

local shp = resolve_shape("shape.star4t")
local escala = math.floor(lerp(40, 120, (char.i - 1) / math.max(1, char.n - 1)))

outputs[1] = pos(char.center, char.middle) .. an(5) .. c1(col) .. fscxy(escala) .. fad(120, 180)
return shp
```

---

## Sección 12.E — Errores Frecuentes y Diagnóstico al Llamar Nodos en Código

| Síntoma / Error | Causa Real | Solución Directa |
| :--- | :--- | :--- |
| `[Err Python Script: name 'context' is not defined]` | Se pasó `context` como primer argumento a una función de nodo. | Pase siempre **`None`** como primer argumento (`eval_math_node(None, ...)`). |
| `TypeError: missing 1 required positional argument: 'context'` | Se omitió el primer argumento posicional al llamar con solo `kwargs`. | Incluya **`None`** antes de los argumentos con nombre: `shape_manipulator(None, drawing=..., op_mode="scale")`. |
| `resolve_shape("star")` dibuja letras `"star"` en lugar de la estrella | Falta el prefijo obligatorio `"shape."`. | Escriba **`resolve_shape("shape.star")`**; sin `"shape."`, Pyxis vectoriza la cadena como texto con la fuente activa. |
| `shape.rounded_corners`, `shape.rhombus`, `shape.rect` o `shape.flower` devuelven `""` | Se usó nomenclatura antigua o con guiones bajos que no existe en los 80 presets. | Use los nombres canónicos sin guiones bajos: **`circangle`**, **`diamond`**, **`rectangle`**, **`flower1t`**..**`flower29t`**. |
| `NameError: name 'shape' is not defined` dentro de `Script Code (Python)` | El objeto raíz `shape` vive en `Define Vars`, mientras que en `Script Code` se accede vía `fx` o `resolve_shape`. | En `Script Code (Python)` use **`fx.shape.<nombre>`** o **`resolve_shape("shape.<nombre>")`**. |
| `[Err Lua Script: attempt to call a nil value]` al invocar `shape_stroke_node` o `tag_master` | Lua solo expone helpers nativos y no las funciones `NODE_REGISTRY` de Python. | Cambie el lenguaje del nodo `Script Code` a **Python** o traslade esa llamada a **`Define Vars`**. |
| `TypeError: float() argument must be a real number, not 'tuple'` en `bezier(...)` | Se pasaron tuplas `(x, y)` en lugar de escalares a `bezier(t, p0, p1, p2, p3)`. | Calcule cada coordenada por separado: `bx = bezier(t, x0, x1, x2, x3)` y `by_y = bezier(t, y0, y1, y2, y3)`. |
| Concatenar el resultado de `shape_walker_node` o `clip_gradient_node` imprime una tupla `('...', ...)` | Esos nodos devuelven tuplas de múltiples ranuras (4, 6 o 9 elementos). | Desempaquete (`shp, pos_t, ang, ... = shape_walker_node(...)`) o tome el índice exacto (`[0]`, `[1]`). |
