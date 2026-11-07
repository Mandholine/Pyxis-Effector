# System

La categoría **System** comprende los nodos de ensamblaje terminal, renderizado interactivo en tiempo real mediante WebAssembly (JASSUB/libass), scripting en Python y Lua, y diagnóstico de rendimiento.

---

## 1. Nodo `System/Output` (Ensamblador Terminal y Emisor ASS)

* **Categoría Canónica:** `System` (UI: *Sistema / Output*)
* **Propósito:** Nodo terminal del grafo de generación. Compila las líneas procesadas, resuelve precedencias de estilo y escala tipográfica, gestiona el ordenamiento jerárquico por colas y escribe los eventos resultantes en el archivo ASS de Aegisub.

![System/Output](img/output.png)

### 1.1. Encabezado y Modos de Cabecera
1. **`[2.1] Apply to` (`apply_to`):** Ámbito de aplicación del efecto sobre el documento de Aegisub:
   * `Sel. Lines` (*Selected Lines*): Procesa exclusivamente las líneas seleccionadas en la grilla de Aegisub.
   * `Style Lines`: Procesa las líneas cuyo estilo coincida con el de la selección activa.
   * `All Lines`: Procesa la totalidad de las líneas de diálogo del archivo.

### 1.2. Puertos de Entrada (*Inputs*)
1. **`Loop / Domain`:** Entrada principal de señal de flujo proveniente del último nodo de la rama (`Main Loop`, `MaxLoop`, `Script Code`).
2. **`Layer`:** Número de capa ASS donde se escribirá la línea (ej. `0`, `1`, `5`). Si no está conectado, hereda la capa original de la línea de diálogo.
3. **`Start Time`:** Tiempo de inicio del evento ASS en milisegundos ($ms$). Si no está conectado, adopta el valor de inicio resuelto por defecto según el iterador de `Main Loop`:
   * Modo `line`: $\text{line.start\_time}$
   * Modo `syl`: $\text{line.start\_time} + \text{syl.start\_time}$
   * Modo `char`: $\text{line.start\_time} + \text{syl.start\_time} + \text{char.start\_time}$
   * Modo `word`: $\text{line.start\_time} + \text{word.start\_time}$
   * *Soberanía Temporal:* Si se conecta una señal a este puerto (o se define `st` / `start_time` en `Define Vars`), el valor recibido define de forma soberana y absoluta el inicio de la línea de subtítulo en la línea de tiempo del vídeo, sin alterar ni contaminar las métricas de karaoke intrínsecas de las unidades hijas (`syl.start_time`, `char.start_time`).
4. **`End Time`:** Tiempo de fin del evento ASS en milisegundos ($ms$). Si no está conectado, adopta el valor final resuelto por defecto según el iterador de `Main Loop`:
   * Modo `line`: $\text{line.end\_time}$
   * Modo `syl`: $\text{line.start\_time} + \text{syl.end\_time}$
   * Modo `char`: $\text{line.start\_time} + \text{syl.start\_time} + \text{char.end\_time}$
   * Modo `word`: $\text{line.start\_time} + \text{word.end\_time}$
   * *Soberanía Temporal:* Si se conecta una señal a este puerto (o se define `et` / `end_time` en `Define Vars`), gobierna directamente el cierre del evento en la línea de tiempo del vídeo.
5. **`Tags`:** Bloque consolidado de etiquetas ASS (`{\pos...\1c...\blur...}`). Se serializa al inicio de la línea de diálogo.
6. **`Return`:** Contenido textual del evento: diálogo plano o comandos vectoriales ASSdraw (`m ... l ... b ...`).
7. **`Queue ID`:** Identificador alfanumérico opcional para agrupar las líneas generadas en una cola lógica post-renderizado. Se escribe en el campo `Actor` de cada línea `Dialogue:`.
8. **`Queue Order`:** Prioridad numérica entera de emisión de la cola para determinar el orden de escritura en el documento de subtítulos.

### 1.3. Controles y Propiedades del Cuerpo
1. **`[2.2] Queue ID` (`queue_id`):** Identificador de cola por defecto si el puerto de entrada permanece desconectado (defecto: `""` $\to$ cola `"default"`).
2. **`[2.3] Queue Order` (`queue_order`):** Prioridad numérica de emisión por defecto si el puerto permanece desconectado (defecto: `""` $\to$ orden `0`).
3. **`origin_align`:** Alineación numérica del origen para el cálculo de anclajes (defecto: `5` / Centro).

### 1.4. Puertos de Salida (*Outputs*)
1. **`[1.1] Preview`:** Transmite los eventos compilados directamente al nodo `System/Previewer` para previsualización interactiva.

### 1.5. Detalle Algorítmico y Compilación ASS
Durante la compilación:
1. Valida las marcas temporales `start_time` y `end_time`, garantizando $t_{\text{end}} \ge t_{\text{start}}$.
2. Fusiona las etiquetas recibidas en `Tags`, eliminando duplicados sintácticos directos.
3. **Precedencia de Escala (`\fscx`/`\fscy`):**
   Para evitar que libass o VSFilter apliquen deformaciones involuntarias sobre trazados vectoriales definidos en coordenadas absolutas cuando el estilo ASS base tiene una escala distinta del 100%, se aplica la siguiente jerarquía de 4 niveles:
   * **Nivel 1 (Texto plano o karaoke):** El nodo no añade etiquetas de escala; el texto hereda la escala configurada en el estilo.
   * **Nivel 2 (Estilo ASS):** Define la escala base por defecto.
   * **Nivel 3 (Formas vectoriales):** Si el cuerpo emitido es un trazado vectorial (`\p1`, ASSdraw `m ...`), el motor inyecta `\fscx100` y `\fscy100` para neutralizar el factor del estilo y preservar las proporciones 1:1 en pantalla.
   * **Nivel 4 (Etiqueta explícita del usuario):** Si el usuario conecta o escribe explícitamente `\fscx` o `\fscy` en el puerto `Tags`, esta etiqueta prevalece sobre el valor neutro.
4. **Rastreador de Estado de Estilos (`ActiveStyleState`):**
   * **Comprobación previa de sobreescritura:** Si la línea de diálogo no contiene etiquetas de control (karaoke simple como `{\k50}`), el motor omite la instanciación de la máquina de estados de estilo para agilizar el procesamiento.
   * **Máquina de estados por sílaba:** Si la línea incluye etiquetas (`\pos`, `\an`, `\fs`, `\fscx`, `\fscy`, `\fsp`, `\b`, `\i`, `\bord`, `\shad`, `\1c`..`\4c`, `\alpha`, `\1a`..`\4a`, `\frz`, `\r`), el motor rastrea acumulativamente las modificaciones bloque por bloque.
   * **Medición tipográfica dinámica:** Las dimensiones de cada unidad (`width`, `height`) se calculan a través del motor tipográfico considerando el tamaño y formato efectivos de la fuente activa.
   * **Posicionamiento y anclaje:** La presencia de `\pos(x,y)` ancla la línea a dichas coordenadas en función de la alineación efectiva `\an`, proyectando las coordenadas derivadas hacia las sílabas y caracteres hijos.
   * **Herencia en unidades:** Las entidades de contexto (`syl`, `char`, `word`, `line`) exponen las propiedades de estilo con jerarquía de resolución en cascada: `Unidad -> Línea -> Estilo -> Valores por defecto`.
   * **Cálculo de Espaciado Tipográfico:** Cuando el estilo define `Spacing > 0` o se inyecta `\fsp`, el motor calcula el espaciado horizontal efectivo ($S_{\text{eff}} = \text{Spacing} \times \frac{\text{ScaleX}}{100} \times \text{FactorX}$). Este incremento se aplica de manera uniforme entre sílabas contiguas y entre los glifos individuales (`char.left`, `char.center`, `char.right`), manteniendo la alineación horizontal de libass/VSFilter.
5. Serializa la línea final en formato estándar ASS, asignando `Queue ID` al campo `Actor`:
   $$\texttt{Dialogue: } \text{Layer}, \, t_{\text{start}}, \, t_{\text{end}}, \, \text{Style}, \, \mathbf{Queue\_ID}, \, \text{MarginL}, \, \text{MarginR}, \, \text{MarginV}, \, \text{Effect}, \, \texttt{\{Tags\}} \text{Return}$$
6. **Ordenamiento y Secuenciación por Colas:**
   * **Aislamiento entre ramas de salida:** Cada nodo `Output` evalúa su rama de forma independiente con un contenedor de contexto propio, sin compartir variables ni estados cinemáticos con otros nodos terminales.
   * **Criterio de ordenamiento global:** Una vez compiladas todas las ramas, las líneas se agrupan por `Queue ID` y se insertan en el archivo ASS según la clave:
     $$\text{SortKey}(Q) = \left(\min_{l \in Q}(\text{queue\_order}_l), \, \text{qid}\right)$$
     * **1. Prioridad Numérica:** Se emiten primero las colas con menor `Queue Order` numérico.
     * **2. Desempate Alfabético:** Si dos o más colas comparten el mismo orden, se ordenan alfabéticamente por `Queue ID`.
     * **3. Cola por Omisión:** Si no se especifica cola ni orden, convergen en la cola `"default"`.
     * **4. Secuencia Interna:** Dentro de cada cola, las líneas conservan el orden del evento original:
       $$\text{SortKey}(l) = (\text{queue\_order}_l, \, \text{line\_idx}_l)$$

### 1.6. Sinergias y Buenas Prácticas
* **Composición Multicapa:** Utilizar nodos `Output` independientes para separar elementos en capas superpuestas (ej. Capa 0 para sombras con `Queue Order = 1`, Capa 1 para el texto principal con `Queue Order = 2`).
* **Identificación por Actor:** Asignar identificadores descriptivos en `Queue ID` (como `"FX_Borde"` o `"FX_Relleno"`) para filtrar, ordenar o revisar las líneas generadas directamente en la grilla de Aegisub.

---

## 2. Nodo `System/Previewer` (Reproductor en Tiempo Real WebAssembly)

* **Categoría Canónica:** `System` (UI: *Sistema / Previewer*)
* **Propósito:** Proporciona previsualización de video y subtítulos en tiempo real acelerada por WebAssembly (JASSUB/libass), acotada al intervalo temporal del efecto sin requerir transcodificación previa.

![System/Previewer](img/previewer.png)

### 2.1. Puertos de Entrada (*Inputs*)
1. **`Output`:** Conexión de señal proveniente del puerto `Preview` de uno o más nodos `Output` para componer previsualizaciones multicapa.

### 2.2. Acciones de Cabecera
1. **`[1.1] Selector de Fuente (Source Toggle)`:**
   * **Plantilla Base (Icono CD / `preview_base.ass`):** Entorno de prueba aislado con video y plantilla precargados.
   * **Proyecto Activo en Aegisub (Icono Aegisub):** Carga el video, audio, estilos y tiempos abiertos en la sesión de Aegisub.
2. **`[1.2] Modo de Renderizado (`render_mode` — Typesetting / mpv)`:**
   * **Disponibilidad:** Conmutable en cualquier momento desde la cabecera del nodo, la barra superior de la ventana flotante desanclada y la barra inferior de transporte en pantalla completa.
   * **Modo Typesetting (Icono circular `TS` / `"typesetting"`, predeterminado):** Rasteriza los subtítulos sobre el lienzo nativo del video replicando 1:1 el comportamiento de Aegisub y VSFilter. En videos anamórficos preserva la relación de aspecto 1:1 rectangular de tipografías y vectores sin deformación ($PAR = 1.0$), resultando idóneo para alinear carteles, trazos y máscaras vectoriales sobre los píxeles reales del cuadro.
   * **Modo mpv (Icono circular `Play` / `"mpv"`):** Emula de forma idéntica el motor de renderizado por defecto de mpv:
     * **Rasterización en Espacio de Pantalla (High-DPI):** Genera los glifos directamente a la resolución física del monitor, manteniendo contornos definidos al ampliar con zoom sin pixelación de texturas.
     * **Proporciones Isotrópicas de Tipografía:** Inyecta en memoria las cabeceras `LayoutResX` y `LayoutResY` para evitar el aplastamiento horizontal o vertical de fuentes cuando la relación de aspecto de `PlayRes` difiere de la del contenedor de video.
     * **Estiramiento Anamórfico Nativo:** En videos con píxeles no cuadrados ($SAR \neq DAR$, como 1440x1080 o 720x480 mostrados en 16:9), comunica la resolución de almacenamiento a libass para aplicar el Pixel Aspect Ratio ($PAR = DAR / SAR$) y estirar horizontalmente los glifos y trazos exactamente igual que el reproductor mpv.
     * **Ámbito Aislado:** Opera exclusivamente dentro del visor interactivo en tiempo real; no altera las líneas compiladas por `Output` ni la codificación en disco de `Hardsub`.
3. **`[1.3] Botón Fijar / Desanclar (Pin / Detach)`:**
   * Desacopla el visor del nodo y lo convierte en una ventana flotante para mantener la referencia visual al desplazarse por el lienzo.
4. **`[1.4] Botón Refrescar (Refresh)`:**
   * Recompila las ramas conectadas a `Output`, actualiza la pista de subtítulos en JASSUB/libass y ejecuta la medición de telemetría sobre las líneas generadas.
   * **Coexistencia en Escena:** En el visor se comentan exclusivamente las líneas reemplazadas por el ámbito de `Output` (`Sel. Lines`, `Style Lines`, `All Lines`), manteniendo visibles los diálogos y carteles coexistentes del archivo original.
   * **Ventana de Reproducción:** El tramo reproducible se delimita a las líneas aplicadas con un margen de 2 segundos antes y después. Si existe una selección activa en Aegisub, la ventana se centra en las líneas seleccionadas aunque el ámbito de `Output` sea `Style Lines` o `All Lines`, evitando que la previsualización abarque el archivo completo.
   * **Compatibilidad de Audio:** El audio se reproduce directamente cuando el motor del visor lo decodifica de forma nativa (AAC, MP3, Opus, Vorbis, FLAC y PCM estándar en MP4, MKV/MKA, WebM, Ogg, FLAC o WAV). Cuando el archivo de video contiene formatos no soportados por el navegador (AC-3, E-AC-3, DTS, TrueHD, MP2, WMA, ADPCM, entre otros), Pyxis genera un archivo unificado MP4 mediante copia directa de video sin recodificación (`-c:v copy`) y transcodificación ligera a AAC (`-c:a aac -movflags +faststart`), preservando la sincronización cuadro a cuadro nativa y evitando bloqueos de búfer.
5. **`[1.5] Botón Renderizar Hardsub (Exportación FFmpeg)`:**
   * Abre el asistente de exportación para compilar el video con subtítulos incrustados (*hardsub*) mediante FFmpeg en un archivo MP4. La codificación FFmpeg se ejecuta exclusivamente al accionar este botón.

### 2.3. Barra de Transporte y Controles de Reproducción
1. **`[2.1] Barra de Desplazamiento Relativa:`** Línea temporal acotada a la duración del efecto ($0 \dots T_{\text{dur}}$), con sincronización por fotograma (`requestAnimationFrame`).
2. **`[2.2] Indicador de Tiempo Relativo:`** Muestra la posición y duración del efecto en formato `MM:SS`.
3. **`[2.3] Control de Volumen:`** Botón de silencio y control deslizante de ganancia.
4. **`[2.4] Cuadro Anterior (-1 Frame):`** Retrocede un fotograma exacto.
5. **`[2.5] Salto Atrás (-10s):`** Desplaza la reproducción 10 segundos hacia atrás dentro del rango del efecto.
6. **`[2.6] Play / Pausa:`** Control de reproducción continua.
7. **`[2.7] Salto Adelante (+10s):`** Desplaza la reproducción 10 segundos hacia adelante dentro del rango del efecto.
8. **`[2.8] Cuadro Siguiente (+1 Frame):`** Avanza un fotograma exacto.
9. **`[2.9] Menú de Ajustes:`** Selector de bucle continuo y velocidad de reproducción ($0.25\times, 0.5\times, 1.0\times, 1.5\times, 2.0\times$).
10. **`[2.10] Pantalla Completa:`** Maximiza el área de video. La barra de transporte conserva el acceso al selector de modo de renderizado (`TS` / `Play`) y eleva automáticamente las notificaciones emergentes por encima de los controles interactivos, con paso libre de clics para no interrumpir el uso.
11. **`[2.11] Fondo Gris Neutro:`** Al reproducir pistas de audio sin video, el área de visualización utiliza un fondo neutro (`#2a2a2a`) para contraste de texto.
12. **`[2.12] Mapa Térmico de Rendimiento (Thermal Heatmap):`**
    * Traza el costo de renderizado fotograma a fotograma de las líneas del efecto mediante una curva en spline, coloreada según el presupuesto temporal ($\text{Budget}_{\text{ms}} = 1000 / \text{FPS}$): cian (carga baja), verde (moderada), naranja (cercana al límite) y rojo (exceso de presupuesto $>100\%$).
    * Al posicionar el cursor sobre la barra de búsqueda, la curva se expande mostrando la cuadrícula de referencia, la latencia en milisegundos (`MM:SS.mmm · X.X ms`) y el enlace directo **`TELEMETRY ↗`**.

### 2.4. Navegación en el Visor (Zoom y Desplazamiento)
1. **Zoom con Rueda del Ratón:** Amplía o reduce el encuadre tomando la posición del cursor como punto focal (de $1.0\times$ a $8.0\times$).
2. **Desplazamiento con Botón Central:** Arrastrar con el botón central del ratón permite recorrer el área ampliada.
3. **Restablecimiento con Tecla 'R':** Pulsar la tecla `R` sobre el reproductor devuelve el zoom a $1.0\times$ y centra el encuadre.
4. **Fidelidad de Bordes y Sombras (`ScaledBorderAndShadow`):** Al aplicar zoom o redimensionar el visor, libass consulta el encabezado del archivo activo para escalar fielmente el grosor de bordes (`\bord`), sombras (`\shad`) y desenfoques (`\blur`), garantizando concordancia absoluta con la configuración fijada en Aegisub o en `preview_base.ass`.

### 2.5. Conexión con el Panel `Telemetry`
Al abrir el panel de **`Telemetry`** desde el mapa térmico:
1. **Transferencia del Visor:** La instancia activa del reproductor se traslada al panel de diagnóstico manteniendo el fotograma actual, nivel de zoom y estado de reproducción. Al cerrar el panel, regresa a su posición en el lienzo.
2. **Sincronización:** Desplazar el cursor en los gráficos o listas de eventos críticos salta automáticamente al fotograma correspondiente en el reproductor.

### 2.6. Sinergias y Buenas Prácticas
* **Comprobación Inmediata de Efectos:** Conectar la salida `Preview` para validar sincronía y estética antes de escribir en Aegisub, reduciendo la necesidad de pruebas intermedias en la grilla.
* **Detección de Cuellos de Botella:** Observar las crestas de la curva térmica para identificar acumulaciones excesivas de desenfoque (`\blur`) o máscaras de recorte complejas (`\clip`).
* **Fidelidad de Edición frente a Reproducción:** Mantener **`Typesetting (TS)`** al alinear carteles y máscaras vectoriales sobre el fotograma original sin estiramientos anamórficos, y conmutar a **`mpv`** para evaluar cómo verá el espectador los subtítulos en su reproductor, verificando tanto la nitidez High-DPI como la deformación anamórfica o la adaptación a proporciones de pantalla dispares.

---

## 3. Nodo `System/Script Code` (Ejecución de Código Embebido Python y Lua)

* **Categoría Canónica:** `System` (UI: *Sistema / Script Code*)
* **Propósito:** Ejecuta fragmentos de código en Python 3.11 o Lua 5.1/LuaJIT dentro del flujo del grafo, con acceso bidireccional a variables del contexto ASS y funciones auxiliares de tags.

![System/Script Code](img/script_code.png)

### 3.1. Encabezado y Selector de Lenguaje
1. **`[1.1] Language` (`language`):** Motor de ejecución:
   * `Python`: Entorno nativo Python 3.11 con acceso a librerías estándar (`math`, `random`, `re`).
   * `Lua`: Entorno de scripting Lua estándar mediante Lupa/LuaJIT con compatibilidad para sintaxis tradicional de macros de Aegisub.

### 3.2. Puertos de Entrada y Salida
1. **`Loop In`:** Entrada de flujo de ejecución.
2. **`In1`, `In2`, $\dots$, `InN`:** Puertos dinámicos de entrada accesibles dentro del script mediante variables `in1`, `in2`, etc.
3. **`[2.1] Loop Out`:** Emite el flujo hacia el siguiente nodo de la cadena.
4. **`[2.2] Result`:** Emite el valor asignado a la variable `result` en el script (texto, tags ASS o trazados vectoriales).

### 3.3. Propiedades del Cuerpo
1. **`script`:** Código fuente a ejecutar (defecto: `result = 'Hello Pyxis ' + str(in1 if in1 else syl.text)`).
2. **`inputs_count`:** Cantidad de puertos de entrada dinámicos (defecto: `2`).

### 3.4. Variables y Funciones en Ámbito

Tanto en Python como en Lua, el script dispone de las siguientes entidades:

| Variable / Objeto | Descripción | Atributos Principales |
| :--- | :--- | :--- |
| `syl` | Sílaba activa del contexto | `x, y, center, middle, left, right, top, bottom, start_time, end_time, dur, text, text_stripped, i, n, prev, next, is_first, is_last, has_prev, has_next, ink` |
| `char` | Carácter activo del contexto | `x, y, center, middle, left, top, start_time, end_time, dur, text, i, n, prev, next, is_first, is_last, has_prev, has_next, ink` |
| `word` | Palabra activa del contexto | `x, y, center, start_time, end_time, dur, text, i, n, prev, next, is_first, is_last, has_prev, has_next, ink` |
| `line` / `l` | Línea de diálogo completa | `text, raw_text, style, layer, start_time, end_time, duration, margin_l, margin_r, margin_v, actor, effect, ink` |
| `prev` / `next` | Unidad vecina anterior y posterior | Acceso a métricas y textos de la unidad adyacente (`prev.text`, `prev.dur`, `prev.x`, `next.x`) |
| `is_first` / `is_last` | Banderas booleanas | `True` si la unidad es la primera / última de la secuencia |
| `has_prev` / `has_next`| Banderas de existencia | `True` si existe una unidad adyacente anterior / posterior |
| `ink` | Métricas de tinta real | `ink.width`, `ink.height`, `ink.center`, `ink.middle`, `ink.left`, `ink.right`, `ink.top`, `ink.bottom` |
| `fx` | Estructura cinemática | `pos_x, pos_y, org_x, org_y, start_time, end_time, dur, align, i, n` |
| `in1`, `in2`, $\dots$ | Entradas conectadas | Valores recibidos en los puertos `In1`, `In2`, etc. |
| `outputs` / `out` | Salidas múltiples | Asignación por nombre (`outputs["Custom"] = val`) o índice (`out2 = val`). |
| `result` | Salida principal | Contenido emitido por el puerto `Result`. |

#### Funciones Auxiliares Disponibles:
* **Constructores ASS:** `pos(x,y)`, `move(x1,y1,x2,y2[,t1,t2])`, `org(x,y)`, `fad(in,out)`, `fade(...)`, `clip(shp)`, `iclip(shp)`, `c1(col)`, `c2(col)`, `c3(col)`, `c4(col)`, `alpha(a)`, `trans(tags)`, `fscx(v)`, `fscy(v)`, `frz(v)`, `blur(v)`, `bord(v)`, `shad(v)`.
* **Interpolación y Matemáticas:** `clamp(v,min,max)`, `lerp(a,b,t)`, `map_range(v,in_min,in_max,out_min,out_max)`, `ease_in(t)`, `ease_out(t)`, `ease_in_out(t)`, `cubic_in(t)`, `cubic_out(t)`, `elastic(t)`, `bounce(t)`, `back(t)`.
* **Ondas Periódicas:** `sine_wave(t,freq,amp,offset)`, `square_wave(...)`, `triangle_wave(...)`, `sawtooth_wave(...)`.
* **Formatos Temporales:** `time_to_frame(ms,fps)`, `duration(obj)`, `parse_ass_time(str)`, `format_ass_time(ms)`, `strip_tags(txt)`.

---

## 4. Nodo `System/Benchmark Math` (Diagnóstico de Rendimiento)

* **Categoría Canónica:** `System` (UI: *Sistema / Benchmark Math*)
* **Propósito:** Mide el rendimiento computacional ejecutando algoritmos matemáticos intensivos (trigonometría, criba de números primos o multiplicación de matrices) y registrando el tiempo transcurrido en milisegundos.

![System/Benchmark Math](img/benchmark_math.png)

### 4.1. Puertos de Entrada (*Inputs*)
1. **`Iterations`:** Cantidad de iteraciones a ejecutar (defecto: `10000`). Si no está conectado, toma el valor de la propiedad interna.

### 4.2. Controles y Propiedades del Cuerpo
1. **`[2.1] Complexity` (`complexity`):** Algoritmo de prueba:
   * `Heavy Math (Trig + Sqrt)`: Bucles de funciones trigonométricas ($\sin, \cos$) combinadas con raíces cuadradas ($\sqrt{x}$).
   * `Prime Sieve`: Algoritmo de comprobación y cribado de números primos.
   * `Matrix Mult`: Multiplicación de matrices $25 \times 25$ en memoria.
2. **`[2.2] Iterations` (`iterations`):** Número de repeticiones (defecto: `10000`).

### 4.3. Puertos de Salida (*Outputs*)
1. **`[1.1] Out`:** Cadena con el dato de entrada recibido o resumen del tiempo transcurrido en formato `[Bench: X.XXms]`.
2. **`[1.2] Time ms`:** Tiempo total de cálculo en milisegundos medido con resolución de alta precisión (`time.perf_counter()`).

### 4.4. Sinergias y Buenas Prácticas
* **Diagnóstico de Eficiencia:** Intercalar `Benchmark Math` en grafos extensos para medir tiempos de ejecución antes y después de aplicar memorización con `Basics/Once`.

