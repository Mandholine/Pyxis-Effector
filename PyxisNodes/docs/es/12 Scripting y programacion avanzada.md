# Scripting y Programación Avanzada (`System/Script Code`)

El nodo **`System/Script Code`** proporciona un entorno de ejecución algorítmica imperativa (Python y Lua) para manipular datos, evaluar cinemáticas continuas y emitir etiquetas ASS o trazados vectoriales.
Documenta la topología del nodo, los espacios de nombres inyectados, el catálogo de funciones nativas de reemplazo y el despachador determinista `by`.

---

## 1. Topología del Nodo, Puertos y Flujo de Datos

```
┌─────────────────────────────────────────────────────────────┐
│ System/Script Code                   [ Language: Python v ] │
├─────────────────────────────────────────────────────────────┤
│ (o) [0] Loop In                             [0] Loop Out (o)│
│ (o) [1] In1                                   [1] Result (o)│
│ (o) [2] In2                                     [2] Out1 (o)│
│ (o) [3] In3                                     [3] Out2 (o)│
├─────────────────────────────────────────────────────────────┤
│ Inputs Count: [ 2                                         ] │
│ Script Editor: [ Ace Code Editor                          ] │
└─────────────────────────────────────────────────────────────┘
```

### 1.1. Puertos de Entrada (*Inputs*)
1. **`[0] Loop In` (Control / Contexto):** Recibe el flujo de iteración activo (`line`, `syl`, `word`, `char`, `MaxLoop`, `Slicer`). Permite al script acceder al contexto temporal y métrico de la unidad actual y preservar la cadena de ejecución hacia el nodo `System/Output`.
2. **`[1] In1`, `[2] In2`, ..., `[N] InN` (Datos):** Entradas dinámicas configurables (de 1 a 16). Se exponen en el script como variables globales `in1`, `in2`, ..., `inN` (o con el nombre del cable entrante). Si no hay un cable conectado, toman el valor del campo inline correspondiente.

### 1.2. Puertos de Salida (*Outputs*)
1. **`[0] Loop Out` (Control / Contexto):** Reenvía el contexto iterativo enriquecido. Cualquier etiqueta ASS o variable generada en el script viaja por este puerto hacia los nodos descendientes o hacia `System/Output`.
2. **`[1] Result` (Cadena / Dato):** Emite el resultado principal del script (el valor asignado a la variable `result` o el valor devuelto por la última expresión).
3. **`[2] Out1` ... `[N] OutN` (Opcionales):** Sub-salidas dinámicas expuestas cuando el script asigna valores al diccionario `outputs` (en Python: `outputs['out1'] = ...` o `out1 = ...`; en Lua: `outputs.out1 = ...` o `out1 = ...`).

### 1.3. Propiedades del Cuerpo (*Properties*)
1. **`language` (`Language`):** Selector del motor de ejecución: `"Python"` o `"Lua"`.
   * **Tipificación Canónica:** **Tipo C (Selector literal)**.
2. **`inputs_count` (`Inputs Count`):** Número de ranuras de entrada dinámicas expuestas (1 a 16).
   * **Tipificación Canónica:** **Tipo C (Entero)**.
3. **`script` (`Script Code`):** Bloque de código fuente ejecutable.
   * **Tipificación Canónica:** **Tipo A (Código fuente evaluado y validado mediante AST)**.

---

## 2. Ciclo de Ejecución y Preprocesamiento Sintáctico

### 2.1. Inyección de Resultado y Fusión de Etiquetas
El valor final del script se define de dos formas:
1. **Asignación explícita:** Definiendo la variable `result = ...` (en Python o Lua).
2. **Última expresión evaluada:** Si la última línea del script es una expresión (por ejemplo, `pos(syl.x, syl.y) + fscxy(120)`), el motor la captura y la asigna automáticamente a `result`.

> [!IMPORTANT]
> **Fusión Transparente de Etiquetas ASS:** Si la cadena contenida en `result` posee sintaxis de etiquetas ASS (`\` o `{...}`), Pyxis la fusiona automáticamente en `context["loop_tags"]` mediante el motor `merge_ass_tags`. Esto significa que no necesitas conectar cables manuales a un combinador de etiquetas: basta con retornar las etiquetas desde el script para que se incorporen a la línea final generada por `System/Output`.

### 2.2. Emisión Mixta: Tags + Dibujo Vectorial (Shapes) o Texto en 'result'

¿Qué ocurre cuando el script genera simultáneamente etiquetas y contenido imprimible (por ejemplo `result = f"{{{pos(syl.x, syl.y)}\\p1}}{shape_star()}"` o `result = "{\\c&HFF&}Texto"`)?

El comportamiento del motor depende de la topología de conexión hacia el nodo `System/Output`:

1. **Si el nodo Script Code solo está intercalado en el bucle (`Loop In` $\to$ `Loop Out`) sin cablear `Result`:**
   * Pyxis detecta los caracteres `\` o `{` e intenta fusionar la cadena en `context["loop_tags"]` mediante `merge_ass_tags`.
   * `merge_ass_tags` aísla los bloques dentro de `{...}` para el encabezado de etiquetas, pero **no sustituye el contenido imprimible de la línea**.
   * El puerto `Return` de `System/Output` (que por defecto toma el texto original de la sílaba `syl.text_stripped`) seguirá gobernando el dibujo o texto de la línea, y cualquier forma vectorial devuelta fuera de las llaves en `result` no reemplazará a la sílaba.

2. **Si el cable `Result` se conecta al puerto `Return` (puerto 5) de `System/Output`:**
   * La cadena completa ingresa directamente al pipeline de renderizado final.
   * `System/Output` procesa la entrada mediante **`evaluate_ass_line_tag_blocks()`**:
     - Detecta la presencia de `\p1` o comandos de dibujo ASSdraw (`m `, `l `, `b `, etc.).
     - Valida, limpia y fusiona los bloques `{...}` de tags de forma segura.
     - Mantiene el trazado vectorial o el texto posterior **100% intacto y sin alterar**.
   * Resultado final en el script ASS:
     ```ass
     Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\pos(640,360)\p1\1c&HFFFFFF&}m 0 0 l 50 0 l 25 -50
     ```

#### Las Tres Formas Canónicas de Emitir Tags + Shape/Texto:
* **Método A (Línea Completa en `Result` $\to$ Cable a `Return`):**
  ```python
  tags = pos(syl.x, syl.y) + r"\p1" + c1(syl.color1)
  dibujo = shape_star()
  result = f"{{{tags}}}{dibujo}"
  # Conexión: Result -> puerto Return (5) de System/Output
  ```
* **Método B (Separación Modular con `outputs` — Recomendado):**
  ```python
  # Tags emitidos automáticamente por Loop Out
  result = pos(syl.x, syl.y) + r"\p1" + c1("&H00FFFF&") + fscxy(120)
  # Dibujo vectorial emitido por sub-salida
  outputs['out1'] = shape_circle()
  # Conexión: Out1 -> puerto Return (5) de System/Output
  ```
* **Método C (Inyección Directa en Contexto):**
  ```python
  context["return_raw"] = shape_heart()
  result = pos(syl.x, syl.y) + r"\p1" + c1("&H0000FF&")
  ```

### 2.3. Macros y Atajos Sintácticos Automáticos
Antes de la compilación de bytecode, el motor de Pyxis aplica un preprocesamiento léxico mediante expresiones regulares para resolver atajos temporales:
* **Multiplicadores de tiempo inmediatos:**
  * `2li` $\to$ `2 * li`
  * `-1.5lo` $\to$ `-1.5 * lo`
  * `3m1` $\to$ `3 * m1`
* **Frames y Ratios:**
  * `10f` $\to$ `(10 * frame_dur)` (convierte automáticamente 10 fotogramas a milisegundos según el FPS activo).
  * `1.5r` $\to$ `(1.5 * ratio)` (escala la magnitud espacial según el ratio de aspecto o módulo activo).

---

## 3. Espacio de Nombres y Contexto Inyectado

El entorno de scripting expone de forma directa e inmutable todas las métricas tipográficas y cinemáticas de la unidad que está siendo procesada.

### 3.1. Unidad Sílaba (`syl`)
Representa la sílaba en curso dentro del bucle de karaoke:

| Propiedad | Tipo | Descripción |
| :--- | :--- | :--- |
| `syl.text` | `str` | Texto limpio de la sílaba (sin tags de karaoke ni de formato). |
| `syl.text_stripped` | `str` | Texto sin espacios ni saltos de línea superfluos. |
| `syl.i` | `int` | Índice de la sílaba dentro de la línea ($1 \le i \le n$). |
| `syl.n` | `int` | Número total de sílabas en la línea. |
| `syl.duration` / `syl.dur` | `int` | Duración de la sílaba en milisegundos (tiempo $\backslash k$). |
| `syl.start_time` / `syl.st` | `int` | Tiempo absoluto de inicio en milisegundos. |
| `syl.end_time` / `syl.et` | `int` | Tiempo absoluto de fin en milisegundos. |
| `syl.mid_time` | `float` | Punto temporal medio absoluto ($\frac{st + et}{2}$). |
| `syl.syl_start` | `int` | Desfase en milisegundos desde el inicio de la línea de diálogo. |
| `syl.syl_end` | `int` | Desfase en milisegundos desde el final de la sílaba hasta el inicio de la línea. |
| `syl.x`, `syl.y` | `float` | Posición $(X, Y)$ calculada según la alineación y estilo de la sílaba. |
| `syl.center`, `syl.middle` | `float` | Coordenadas exactas del baricentro geométrico de la sílaba. |
| `syl.left`, `syl.right` | `float` | Límites horizontales (caja tipográfica envolvente). |
| `syl.top`, `syl.bottom` | `float` | Límites verticales (caja tipográfica envolvente). |
| `syl.width`, `syl.height` | `float` | Dimensiones tipográficas calculadas con métricas GDI/FreeType. |
| `syl.color1` ... `syl.color4` | `str` | Colores ASS del estilo base (`&HBBGGRR&`). |
| `syl.fontsize` | `float` | Tamaño nominal de la fuente en puntos. |
| `syl.fontname` | `str` | Nombre de la familia tipográfica activa. |
| `syl.bold`, `syl.italic` | `bool` | Banderas de negrita y cursiva. |
| `syl.is_first`, `syl.is_last` | `bool` | `True` si es la primera o la última sílaba de la línea. |
| `syl.has_prev`, `syl.has_next` | `bool` | `True` si existe una sílaba contigua anterior o posterior. |

### 3.2. Línea de Diálogo (`line` / `l`)
Representa la línea completa de subtítulo de Aegisub:
* `line.text`: Texto completo sin tags ASS.
* `line.raw_text`: Cadena original completa con todos sus tags de formato y override.
* `line.start_time`, `line.end_time`, `line.duration`: Tiempos absolutos de la línea (en ms).
* `line.i`, `line.n`: Número correlativo de la línea y total de líneas seleccionadas.
* `line.layer`: Capa ASS del diálogo (entero).
* `line.style`: Nombre del estilo asignado en Aegisub.
* `line.actor`, `line.effect`: Campos Actor y Efecto de la línea.
* `line.margin_l`, `line.margin_r`, `line.margin_v`: Márgenes de pantalla configurados.
* `line.width`, `line.height`: Ancho y alto tipográfico total de la línea renderizada.
* `line.center`, `line.middle`, `line.left`, `line.right`, `line.top`, `line.bottom`: Límites espaciales de la línea en pantalla.

### 3.3. Carácter (`char`) y Palabra (`word`)
Si el bucle activo desciende a granularidad de caracteres o palabras, `char` y `word` exponen el mismo conjunto de propiedades métricas que `syl`:
* Posición: `char.x`, `char.y`, `char.center`, `char.middle`, `char.width`, `char.height`.
* Tiempos: `char.start_time`, `char.end_time`, `char.duration`, `char.char_start`, `char.char_end`.
* Índices: `char.i`, `char.n`, `char.is_first`, `char.is_last`.

### 3.4. Cuadro de Efecto (`fx`)
Cuando se ejecutan efectos cinemáticos o sistemas de partículas que alteran la posición de renderizado respecto a la línea original:
* `fx.pos_x`, `fx.pos_y` (o `fx.x`, `fx.y`): Coordenadas actuales del punto de emisión.
* `fx.org_x`, `fx.org_y`: Coordenadas del centro de rotación y escalado ($\backslash org$).
* `fx.start_time`, `fx.end_time`, `fx.dur`: Ventana temporal activa de la línea resultante.
* `fx.i`, `fx.n`: Índice de la partícula o clon generado en la iteración.

### 3.5. Métricas de Tinta Real (`ink`)
A diferencia de las dimensiones tipográficas nominales (`syl.width`, `syl.height`), que incluyen espacios en blanco, ascendentes y márgenes de interletraje de la fuente, el objeto `ink` describe el **bounding box exacto de los píxeles/vectores dibujados**:
* `ink.width`, `ink.height`: Anchura y altura real del glifo trazado.
* `ink.center`, `ink.middle`: Centroide geométrico del glifo real.
* `ink.left`, `ink.right`, `ink.top`, `ink.bottom`: Coordenadas absolutas de los bordes del dibujo.

### 3.6. Navegación entre Vecinos (`prev` y `next`)
Permite inspeccionar los datos de la unidad anterior o siguiente para crear efectos de arrastre, propagación en cadena o sincronización relativa:
* `prev.text`, `prev.x`, `prev.y`, `prev.start_time`, `prev.duration`
* `next.text`, `next.x`, `next.y`, `next.start_time`, `next.duration`
* En caso de no existir unidad previa o siguiente (por ejemplo, en la primera o última sílaba), `prev` y `next` devuelven proxies seguros que retornan valores neutros (`0`, `""`) sin provocar excepciones de ejecución (`NullReferenceException` o `AttributeError`).

### 3.7. Variables Globales e Iteradores de Malla
* `s_i`, `s_n`: Índice y total de piezas generadas por el nodo `Shape/Slicer`.
* `col`, `row`: Columna y fila espacial en mallas de corte 2D.
* `j`, `maxloop`: Índice correlativo y total de repeticiones en el nodo `Loops/MaxLoop`.
* `a_i`, `a_n`: Índice y total de elementos en matrices o partículas.
* `frame_dur` (alias `fd`): Duración en ms de un solo fotograma ($1000 / FPS$, típicamente $41.7\,\text{ms}$ a 23.976 fps o $16.6\,\text{ms}$ a 60 fps).
* `fps`: Tasa de fotogramas por segundo del proyecto.

---

## 4. Catálogo de Funciones de Reemplazo Nodal

El script tiene acceso directo a funciones predefinidas que replican de forma exacta el comportamiento de los nodos visuales de Pyxis:

### 4.1. Generadores de Etiquetas ASS
 
Todas las funciones de etiquetas formatean automáticamente los valores numéricos con una precisión de hasta 3 decimales (omitiendo ceros decimales innecesarios, por ejemplo `pos(100.0, 200.5)` $\to$ `\pos(100,200.5)`):
 
| Función | Salida Generada | Descripción |
| :--- | :--- | :--- |
| `pos(x, y)` | `\pos(x,y)` | Posicionamiento absoluto en coordenadas de pantalla. |
| `move(x1, y1, x2, y2, [t1, t2])` | `\move(...)` | Desplazamiento lineal entre dos puntos con ventana de tiempo opcional. |
| `org(x, y)` | `\org(x,y)` | Punto de pivote para rotaciones ($\backslash frz, \backslash frx, \backslash fry$) y escalas. |
| `fad(tin, tout)` | `\fad(tin,tout)` | Desvanecimiento de entrada y salida en milisegundos. |
| `fade(a1, a2, a3, t1, t2, t3, t4)` | `\fade(...)` | Desvanecimiento continuo de 3 alfas y 4 puntos temporales. |
| `clip(x1, y1, x2, y2)` | `\clip(x1,y1,x2,y2)` | Máscara de recorte rectangular. |
| `clip(shape_str)` | `\clip(dibu)` | Máscara de recorte vectorial según dibujo ASS. |
| `iclip(...)` | `\iclip(...)` | Máscara de recorte invertida (rectangular o vectorial). |
| `c1(col)`, `c2(col)`, `c3(col)`, `c4(col)` | `\1c...`, `\2c...`, etc. | Color primario, karaoke, borde y sombra (`&HBBGGRR&` o `#RRGGBB`). |
| `a1(val)`, `a2(val)`, `a3(val)`, `a4(val)` | `\1a...`, `\2a...`, etc. | Opacidad específica por canal (`&HAA&`, de 0 a 255). |
| `alpha(val)` | `\alpha&HAA&` | Opacidad global del elemento. |
| `fscx(v)`, `fscy(v)` | `\fscx...`, `\fscy...` | Escalado porcentual independiente ($100 = 100\%$). |
| `fscxy(x, [y])` | `\fscx...\fscy...` | Escalado bidimensional en una sola invocación. |
| `frz(deg)` | `\frz...` | Rotación en el plano 2D sobre el eje Z (grados). |
| `frx(deg)`, `fry(deg)` | `\frx...`, `\fry...` | Rotación 3D sobre los ejes X e Y. |
| `fax(v)`, `fay(v)` | `\fax...`, `\fay...` | Deformación por cizallamiento (*shear*). |
| `bord(px)` | `\bord...` | Grosor del contorno o borde en píxeles. |
| `shad(px)` | `\shad...` | Distancia de la sombra paralela en píxeles. |
| `blur(sigma)` | `\blur...` | Desenfoque gaussiano (sigma en píxeles). |
| `an(numpad)` | `\an...` | Alineación del texto o forma (notación numpad del 1 al 9). |
| `trans([t1, t2], [accel], tags)` | `\t(...)` | Animación temporal e interpolación de tags entre $t_1$ y $t_2$. |
| `ass_color(r, g, b)` | `&HBBGGRR&` | Conversión de RGB decimal ($0-255$) a hexadecimal BGR de ASS. |
| `ass_alpha(val)` | `&HAA&` | Conversión de transparencia ($0-255$) a hexadecimal ASS. |
| `random_color()` | `&HBBGGRR&` | Generador de color aleatorio en formato ASS. |
| `random_alpha()` | `&HAA&` | Generador de alfa aleatorio en formato ASS. |

### 4.2. Matemáticas, Cinemática e Interpolación

| Función | Definición Matemática / Comportamiento |
| :--- | :--- |
| `clamp(val, min_v, max_v)` | Restringe $val$ al intervalo cerrado $[min\_v, max\_v]$. |
| `lerp(a, b, t)` | Interpolación lineal paramétrica: $a + (b - a) \cdot t$ con $t \in [0.0, 1.0]$. |
| `map_range(v, in_min, in_max, out_min, out_max)` | Remapea linealmente un valor desde una escala de origen a otra de destino. |
| `ease_in(t)`, `ease_out(t)`, `ease_in_out(t)` | Curvas de aceleración y desaceleración cuadráticas estándar. |
| `cubic_in(t)`, `cubic_out(t)` | Curvas de aceleración y desaceleración cúbicas ($t^3$). |
| `elastic(t)` | Curva oscilatoria con amortiguación de resorte elástico. |
| `bounce(t)` | Curva de rebote balístico con decaimiento físico progresivo. |
| `back(t)` | Curva con anticipación y sobreimpulso (*overshoot*). |
| `ipol(t, a, b, curve)` | Interpola entre $a$ y $b$ aplicando la curva especificada (`"ease_in"`, `"cubic_out"`, `"bounce"`). |
| `bezier(t, p0, p1, p2, p3)` | Curva Bézier cúbica 1D evaluada paramétricamente en $t$. |
| `polar(angle_deg, dist)` | Convierte coordenadas polares $(\theta, r)$ a vector cartesiano $(x, y)$: $x = r \cos(\theta)$, $y = r \sin(\theta)$. |

### 4.3. Osciladores y Ondas
Generan funciones periódicas en base a tiempo $t$, frecuencia $freq$, amplitud $amp$ y fase $offset$:
* `sine_wave(t, freq=1.0, amp=1.0, offset=0.0)`: Onda senoidal armónica.
* `square_wave(t, freq=1.0, amp=1.0, offset=0.0)`: Onda cuadrada discreta ($\pm amp$).
* `triangle_wave(t, freq=1.0, amp=1.0, offset=0.0)`: Onda triangular con pendientes lineales continuas.
* `sawtooth_wave(t, freq=1.0, amp=1.0, offset=0.0)`: Onda diente de sierra (rampa lineal periódica).

### 4.4. Tiempos Paramétricos y Sincronización entre Líneas

| Función | Descripción |
| :--- | :--- |
| `time_lead_in(delay, [base])` (o `li(delay)`) | Calcula el inicio escalonado de entrada de la unidad en milisegundos. |
| `time_lead_out(delay, [base])` (o `lo(delay)`) | Calcula el fin escalonado de salida de la unidad en milisegundos. |
| `time_middle_1(delay, [base])` (o `m1(delay)`) | Secuencia radial desde el centro de la línea hacia los extremos. |
| `time_middle_2(delay, [base])` (o `m2(delay)`) | Secuencia radial inversa desde los extremos hacia el centro. |
| `time_loop_1(delay, [mode])` (o `l1(delay)`) | Bucle de tiempo continuo para efectos de entrada cíclica. |
| `time_loop_2(delay, [mode])` (o `l2(delay)`) | Bucle de tiempo continuo para efectos de salida cíclica. |
| `time_to_frame(ms, [fps])` | Convierte un intervalo temporal en milisegundos al número entero de frame correspondiente. |
| `duration(obj)` | Obtiene la duración en ms del objeto o contexto suministrado. |
| `parse_ass_time("0:01:23.45")` | Convierte una cadena de tiempo ASS a milisegundos enteros. |
| `format_ass_time(ms)` | Convierte milisegundos enteros al formato timestamp estándar de ASS (`H:MM:SS.cs`). |
| `sync.next`, `sync.prev` | Distancia temporal en milisegundos hasta la siguiente o anterior línea de diálogo. |
| `sync.style_next`, `sync.actor_next` | Distancia temporal a la siguiente línea que coincida con el mismo estilo o actor. |
| `calculate_sync_gap(dir, mode, max_gap)` | Función general de consulta de espacios y solapamientos entre diálogos. |

### 4.5. Generación de Formas Vectoriales Nativas

El script puede emitir directamente trazados vectoriales ASSdraw para su uso como siluetas, partículas o recortes:
* `shape_circle()`, `shape_square()`, `shape_rectangle()`
* `shape_triangle()`, `shape_rhombus()`, `shape_rounded_corners()`
* `shape_pentagon()`, `shape_hexagon()`, `shape_octagon()`
* `shape_star()`, `shape_heart()`
* `resolve_shape(name)`: Resuelve cualquier figura registrada en la biblioteca de formas.

### 4.6. Reactividad de Audio Espectral
* `audio_rms(start_ms, end_ms, [path])`: Amplitud media cuadrática del audio en la ventana temporal ($0.0 \dots 1.0$).
* `audio_peak(start_ms, end_ms, [path])`: Amplitud de pico máximo alcanzada en la ventana ($0.0 \dots 1.0$).
* `audio_band(start_ms, end_ms, min_hz, max_hz, [path])`: Energía acústica filtrada en una banda específica de frecuencias (por ejemplo, graves de 20 Hz a 120 Hz).
* `audio_fft(start_ms, end_ms, num_bands, min_hz, max_hz, [path])`: Devuelve una lista (o tabla Lua) con los valores normalizados de los canales espectrales tras aplicar la Transformada Rápida de Fourier.

### 4.7. Memoria Persistente y Estado Compartido
* `remember(clave, valor)`: Guarda un valor en la memoria compartida del motor. Este dato sobrevive a través de diferentes iteraciones de sílabas, caracteres y líneas completas.
* `recall(clave, default=None)`: Recupera el valor guardado previamente o retorna `default` si aún no ha sido inicializado.
* `tag_only(condicion, tag_str)`: Emite `tag_str` única y exclusivamente si la expresión booleana `condicion` es verdadera; en caso contrario, emite una cadena vacía.

---

## 5. El Motor Estocástico Determinado (`R` y el Despachador `by`)

Las funciones pseudoaleatorias estándar sin semilla contextual fija producen valores divergentes en cada evaluación o fotograma, induciendo inestabilidad espacial (*jittering*).

Pyxis resuelve este comportamiento integrando un **motor pseudoaleatorio determinista con semilla derivada de la topología del nodo y los índices de iteración**:

### 5.1. Funciones Aleatorias Básicas

* `R(min, max)`: Número aleatorio entero o flotante escalonado dependiente del contexto actual.
* `Rs(min, max)`: Aleatorio **bipolar simétrico** (genera valores en $\pm [min, max]$).
* `Rc(min, max)` / `Rcs(min, max)`: Aleatorio centesimal con 2 decimales de precisión.
* `Rd(min, max)` / `Rds(min, max)`: Aleatorio decimal con 1 decimal de precisión.
* `Rm(min, max)` / `Rms(min, max)`: Aleatorio milesimal con 3 decimales de precisión.
* `Rr(min, max)`: Aleatorio escalado automáticamente por la resolución del video.
* `Rstep(min, max, step)`: Aleatorio cuantizado a saltos múltiplos de `step` (útil para ángulos: `Rstep(0, 360, 45)`).
* `R2d(min, max)`: Genera un par de coordenadas independientes `"X,Y"`.
* `Rbool(prob=50)`: Devuelve booleano `True` con la probabilidad porcentual indicada ($0-100\%$).
* `Rcolor(c1, c2)`: Interpola un color ASS aleatorio entre dos tonos dados.
* `Re("opcionA, opcionB, opcionC")`: Selecciona aleatoriamente uno de los elementos de una lista separada por comas.

### 5.2. El Operador Despachador Determinista `by`

Para garantizar que un valor aleatorio se evalúe **exactamente una sola vez por cada sílaba, partícula o sub-bucle**, se utiliza la sintaxis:

$$\text{by}.\langle \text{iterador} \rangle.\langle \text{modo\_R} \rangle(\text{args})$$

**Ejemplos de sintaxis:**
```python
# Un ángulo aleatorio estable por cada sílaba (no cambia si hay sub-bucles internos)
ang = by.syl.R(-45, 45)

# Una variación de velocidad única por cada pieza de slicer
vel_x = by.s_i.Rms(-150, 150)

# Un desplazamiento vertical por cada clon del nodo MaxLoop (j)
offset_y = by.j.Rs(20, 80)
```

---

## 6. Diferencias Prácticas: Python frente a Lua

| Característica | Modo Python (`language: "Python"`) | Modo Lua (`language: "Lua"`) |
| :--- | :--- | :--- |
| **Indexación** | Basada en cero ($0 \dots N-1$) para listas nativas. | Basada en uno ($1 \dots N$) para tablas. |
| **Métricas** | `syl.i`, `line.i` son enteros 1-based en ambos. | `syl.i`, `line.i` son enteros 1-based en ambos. |
| **Estructuras de Datos** | Diccionarios `{}` y Listas `[]`. | Tablas `{}` asociativas y numéricas. |
| **Salida Principal** | `result = ...` o última expresión. | `result = ...` o `return ...`. |
| **Salidas Múltiples** | `outputs['out1'] = val` o `out1 = val`. | `outputs.out1 = val` o `out1 = val`. |
| **Condicionales** | `x = a if cond else b` | `x = cond and a or b` |
| **Concatenación** | `+` (cadenas) o f-strings `f"{a}{b}"` | `..` (operador de concatenación) |
| **Librería Matemática** | `math.sin`, `math.pi`, `abs`, etc. | `math.sin`, `math.pi`, `math.abs`, etc. |
| **Nil / None** | `None` | `nil` |

---

## 7. Qué SE PUEDE y Qué NO SE PUEDE Hacer en el Nodo Script

### ✅ Lo que SÍ se puede hacer:
1. **Modelar cinemática y física personalizada:** Escribir simulaciones de gravedad, trayectorias helicoidales, gravedad inversa, osciladores armónicos acoplados o resortes con damping manual.
2. **Manipular cadenas ASS de forma masiva:** Limpiar, mutar o combinar etiquetas dinámicamente con las utilidades nativas (`merge_ass_tags`, `strip_tags`, `pos`, `move`).
3. **Controlar el flujo con condicionales complejos:** Bifurcar el estilo o comportamiento según el actor, capa, número de sílaba, posición en pantalla o tiempo restante para la próxima línea.
4. **Distribuir datos a múltiples nodos:** Usar `outputs['out1']`, `outputs['out2']`, etc., para enviar simultáneamente coordenadas calculadas a otros nodos del lienzo.
5. **Persistir estados complejos:** Crear contadores acumulativos, estelas de partículas o memorias de posición previas mediante `remember()` y `recall()`.

### ❌ Lo que NO se debe hacer (Límites y Reglas Críticas):
1. **Llamadas I/O síncronas bloqueantes dentro de iteraciones:**
   - *Prohibido:* Abrir archivos de disco (`open()`) o consultar bases de datos en cada evaluación de sílaba o partícula. Si necesitas leer un archivo externo, léelo una sola vez con `recall` o guárdalo en memoria compartida.
2. **Modificar objetos del sistema en caliente:**
   - *Prohibido:* Intentar reasignar punteros internos o mutar diccionarios inmutables del host (`context["_engine"] = None`). El contexto inyectado es para lectura de métricas y emisión de etiquetas.
3. **Mezclar tipos en etiquetas numéricas:**
   - *Evitar:* Inyectar valores `None`, `nil` o cadenas no validadas dentro de etiquetas ASS numéricas (ej. `\pos(None, 20)`). Las funciones utilitarias de Pyxis (`pos()`, `fscx()`) filtran y sanean automáticamente los valores numéricos para prevenir excepciones de sintaxis.
4. **Bucles infinitos o complejidad descontrolada:**
   - Si un script se ejecuta dentro de un bucle anidado (`Slicer` $\times$ `MaxLoop`), el código se ejecutará $P \times J$ veces por sílaba. Mantén los cálculos en complejidad temporal constante $\mathcal{O}(1)$ por iteración, evitando bucles `while` sin cota estricta de salida.
5. **Indentación irregular en Python:**
   - El linter en tiempo real de Pyxis pre-valida el script antes de la ejecución. Un error de indentación generará una advertencia visual inmediata en el panel de diagnósticos del nodo.

---

## 8. Ejemplos Prácticos de Producción

### 8.1. Ejemplo A: Aparición Elástica con Anticipación y Resorte (Python)

Este script reemplaza por completo una cadena de nodos de tiempo, interpolador, oscilador y tags:

```python
# Cálculo del factor paramétrico t según el tiempo de lead-in de la sílaba
t_in = clamp((line.start_time + syl.syl_start - fx.start_time) / 300.0, 0.0, 1.0)

# Curva de resorte elástico aplicada a la escala horizontal y vertical
scale = lerp(0.0, 100.0, elastic(t_in))

# Pequeña rotación Z con anticipación que se amortigua al asentarse
rot = lerp(by.syl.Rs(30, 60), 0.0, back(t_in))

# Desvanecimiento de entrada
alpha_val = lerp(255, 0, t_in)

# Generación y retorno de las etiquetas ASS limpias
result = pos(syl.x, syl.y) + fscxy(scale) + frz(rot) + alpha(ass_alpha(alpha_val))
```

### 8.2. Ejemplo B: Desintegración Balística de Partículas con Gravedad (Lua)

Modelado de dispersión física para partículas generadas con `Slicer` o `MaxLoop`:

```lua
-- Parámetros físicos evaluados con el despachador determinista 'by'
local ang = by.s_i.R(0, 360)
local speed = by.s_i.R(80, 250)
local gravity = 120.0

-- Tiempo normalizado desde el instante de activación de la sílaba
local t = clamp((fx.start_time - syl.start_time) / syl.duration, 0.0, 1.0)

-- Desplazamiento vectorial cartesiano
local rad = math.rad(ang)
local dx = math.cos(rad) * speed * t
local dy = (math.sin(rad) * speed * t) + (0.5 * gravity * t * t)

-- Rotación acumulada durante la caída
local rz = by.s_i.Rs(90, 360) * t

-- Resultado inyectado directamente al pipeline ASS
result = pos(syl.x + dx, syl.y + dy) .. frz(rz) .. fad(0, 150)
```

### 8.3. Ejemplo C: Pulso Espectral Reactivo a Graves de Audio (Python)

Modulación reactiva que analiza la pista de audio vinculada en Aegisub:

```python
# Analizar la energía en la banda de graves (bombos y bajos: 30 a 120 Hz)
bass_energy = audio_band(syl.start_time, syl.end_time, min_hz=30, max_hz=120)

# Remapear la energía acústica (0.0..1.0) a un incremento de escala y brillo
scale_boost = map_range(bass_energy, 0.0, 1.0, 100.0, 160.0)
blur_amount = map_range(bass_energy, 0.0, 1.0, 1.0, 6.0)

# Variación armónica adicional usando onda senoidal rápida
wave = sine_wave(syl.i * 0.2, freq=2.0, amp=15.0)

# Emitir transformaciones dinámicas
result = pos(syl.x, syl.y + wave) + fscxy(scale_boost) + blur(blur_amount)
```

---

## 9. Diagnóstico y Depuración en Tiempo Real

1. **Linter Integrado:** Al escribir en el editor Ace del nodo, cualquier error de sintaxis en Python (`ast.parse`) o en Lua se marca instantáneamente con subrayado de advertencia y se lista en el panel de diagnósticos con la línea y sugerencia de corrección.
2. **Autocompletado Contextual (`Ctrl + Espacio`):** El editor de código reconoce todas las variables contextuales (`syl.*`, `char.*`, `line.*`, `ink.*`), los generadores funcionales de tags y los atajos del despachador `by.<iterador>.*` con ayuda contextual flotante en HTML.
3. **Tolerancia a Errores en Ejecución:** Si un script arroja una excepción durante la generación, Pyxis captura el error y emite un mensaje estructurado `[Err Python Script: ...]` o `[Err Lua Script: ...]` en la consola de depuración, evitando que el proceso maestro de Aegisub se congele o aborte abruptamente.
