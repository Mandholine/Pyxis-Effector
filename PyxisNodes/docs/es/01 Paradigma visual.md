# Paradigma Visual

Pyxis Effector implementa un entorno visual basado en grafos dirigidos para el procesamiento y generación de subtítulos en formato ASS (*Advanced SubStation Alpha*). La arquitectura desacopla el flujo de iteración, el cálculo numérico, las transformaciones geométricas y la compilación de etiquetas en nodos modulares interconectados.

---

## 1. Principios Fundamentales del Grafo

El motor opera mediante un grafo dirigido acíclico (DAG) donde la generación de subtítulos se estructura mediante la interconexión de dos tipos de enlaces:

```
[Main Loop] ---> [MaxLoop / Sub-iterador] ---> [Script / Transform] ---> [Output]
     │                                                ▲
     │ (Contexto activo)                              │ (Datos evaluados bajo demanda)
     └───────────────────> [Nodos de Datos / Tags] ───┘
```

### 1.1. Enlaces de Flujo y Ejecución (*Flow / Loop Links*)
1. **Secuencia y Jerarquía:** Establecen el orden temporal y la anidación en la que se evalúan las ramas del efecto.
2. **Puertos de Control:** Se interconectan a través de los puertos `Loop`, `Loop In` y `Loop Out`.
3. **Frecuencia de Evaluación:** Determinan cuántas veces se ejecuta cada rama (por línea, por sílaba, por carácter, por sub-partícula o por fotograma de video).
4. **Nodos Centrales de Flujo:**
   * `Main Loop` (Iterador del dominio base).
   * `MaxLoop` (Multiplicador de eventos o bucle sub-fotograma *FBF*).
   * `Script Code` (Nodo maestro de inyección de código Python / Lua).
   * `Output` (Ensamblador terminal y emisor de líneas ASS).

### 1.2. Enlaces de Datos (*Data Links*)
1. **Tipos de Información:** Transportan valores numéricos (`float`/`int`), cadenas de texto, pares de coordenadas cartesianas $(x, y)$, colores hexadecimales y ASS (`&HBBGGRR&`), código vectorial ASSdraw (`m ... l ... b ...`) y bloques formateados de etiquetas ASS (`{\pos...\t...\clip}`).
2. **Evaluación Bajo Demanda (*Lazy Evaluation*):** Un nodo de datos únicamente se calcula cuando el flujo de ejecución activo solicita su valor en la iteración corriente. Si una rama de datos no está conectada a un nodo de flujo activo, su cálculo no consume tiempo de CPU ni memoria.
3. **Propagación Dinámica:** Las salidas pueden ramificarse libremente hacia múltiples entradas sin pérdida de rendimiento gracias a la memorización interna por ciclo.

---

## 2. Jerarquía de Contextos y Ciclo de Vida de los Datos

El procesamiento de un efecto en Pyxis sigue un flujo jerárquico de descomposición y transformación en cinco fases:

```
[1. Selección en Aegisub]
           │
           ▼
[2. Dominio Base: Main Loop] (line / syl / word / char)
           │
           ▼
[3. Sub-dominio: MaxLoop] (Clones, Partículas, Cuadros FBF)
           │
           ▼
[4. Transformación de Datos] (Vectores, Tags, Audio, Interpolaciones)
           │
           ▼
[5. Ensamblado Terminal: Output] ───> [Nuevas Líneas ASS en Capas]
```

### Fase 1: Selección y Análisis de Entrada
El motor lee las líneas del archivo ASS cargadas en Aegisub según el ámbito configurado en `Output` (`apply_to`):
* `Sel. Lines`: Exclusivamente las líneas seleccionadas en la grilla de Aegisub.
* `Style Lines`: Todas las líneas que coincidan con el estilo de la selección.
* `All Lines`: La totalidad de las líneas de diálogo del archivo.

Cada línea es analizada por el motor sintáctico y descompuesta en sus métricas espaciales tipográficas y marcas de tiempo de karaoke (`\k`, `\kf`, `\ko`).

### Fase 2: Inicialización del Dominio Iterativo (`Main Loop`)
El nodo `Main Loop` establece la unidad base de iteración (`iterator`):
* **`syl`:** Itera sílaba a sílaba utilizando las marcas de karaoke. Inyecta el contexto métrico y temporal de la sílaba (`syl.start_time`, `syl.duration`, `syl.text`, etc.).
* **`char`:** Itera carácter por carácter de forma individual. Permite animaciones cinemáticas tipográficas independientes para cada glifo.
* **`word`:** Itera palabra por palabra delimitadas por espacios.
* **`line`:** Itera una única vez por cada línea de diálogo completa.

La propiedad `blank_mode` (`no_blank` / `with_blanks`) controla si los espacios en blanco se omiten del ciclo o se procesan como elementos con ancho pero sin glifo visible.

### Fase 3: Multiplicación de Sub-bucles (`MaxLoop`) y Anidamiento Topológico de Generadores
Para generar efectos volumétricos (estelas cinemáticas, enjambres de partículas, réplicas con retardo o animaciones fotograma a fotograma *FBF*), el flujo pasa por uno o varios nodos `MaxLoop`. Este nodo multiplica la unidad actual por $N$ sub-iteraciones, inyectando un contador local (por defecto `j` de $1 \dots N$) y subdividiendo los intervalos de tiempo.

Además, dentro de cada hoja de ejecución de `Main Loop` / `MaxLoop`, el motor traza automáticamente los **nodos generadores de sub-bucles** conectados a `Output` (`Shape/Slicer`, `Shape/Union & Divide`, `Shape/Concentric Borders`, `Shape/Array`, `Shape/Multi`, `Functions/Particles`, `Functions/IMG to pixels`, `Functions/Clip Gradient`, `Functions/Animation`) en **orden topológico post-orden (raíz $\to$ hoja)**:
1. **Canal de Geometría (`Output.Return`):** Los generadores conectados en serie (ej. `Slicer` $\to$ `Particles`) anidan sus sub-bucles automáticamente ($s_i = 1 \dots S$ externo $\to$ $p_i = 1 \dots P_k$ interno), propagando las coordenadas de anclaje (`pos_x`, `pos_y`, `org_x`, `org_y`) de cada pieza padre a sus sub-piezas o partículas hijas.
2. **Canal de Etiquetas y Recortes (`Output.Tags`):** Se evalúa como sub-bucle interno para cada pieza o partícula emitida por `Output.Return` (respetando el orden de puertos `In1, In2, ...` en `Concatenate`), permitiendo combinar p. ej. `Slicer` ($s_i$) en `Return` con `Clip Gradient` ($c_i$) y `Animation` ($an_i$) en `Tags` sin colisión de contadores.

### Fase 4: Evaluación y Deformación
Los nodos de datos conectados computan las posiciones `\pos`, deformaciones morfológicas de vectores (cortes con `Slicer`, hinchado con `Transform`, extrusión con `Stroke`), degradados de color con `Color Gradient`, modulaciones de audio con `Modulator` y transformaciones temporales aceleradas con `Retime` e `Ipol`.

### Fase 5: Ensamblado, Aislamiento y Emisión (`Output`)
El nodo terminal `Output` recopila los flujos procesados, consolida los bloques de etiquetas del puerto `Tags` y los dibujos/textos del puerto `Return`, resuelve colisiones sintácticas entre tags, aplica las capas de renderizado (`Layer`) y emite las nuevas líneas de subtítulo generadas directamente hacia el documento de Aegisub.

#### Arquitectura Multi-Output y Aislamiento de Contexto
Al requerir múltiples capas o componentes visuales concurrentes (por ejemplo, sombra, cuerpo de glifo y partículas), se instancian múltiples nodos `System/Output` en el mismo lienzo:
* **Independencia Total de Ramas:** Cada nodo `Output` constituye una terminal autónoma que evalúa su propia rama conectada hacia aguas arriba (*upstream*).
* **Aislamiento de Contexto (`context`):** El motor genera un contexto limpio y privado para cada rama e iteración. Las variables locales, cálculos temporales o mutaciones efectuadas en la rama de un nodo `Output` no se filtran, no contaminan ni se comparten con las ramas de otros nodos `Output`. El hecho de compartir el mismo lienzo o converger en la misma pista no altera la estanqueidad de sus datos.

#### Sistema de Colas de Salida (`Queue ID` y `Queue Order`)
Las colas de emisión actúan exclusivamente como **contenedores de secuenciación y agrupamiento post-renderizado** sobre las líneas ya generadas, sin intervenir en el cómputo lógico de los nodos:
1. **Identificador de Cola (`Queue ID` $\to$ Campo `Actor` en ASS):**
   * El texto asignado a `Queue ID` identifica el bloque lógico de emisión y se inyecta directamente en el campo `Actor` del evento ASS resultante:
     $$\texttt{Dialogue: Layer}, \, t_{\text{start}}, \, t_{\text{end}}, \, \text{Style}, \, \mathbf{Queue\_ID}, \, \text{MarginL}, \, \text{MarginR}, \, \text{MarginV}, \, \text{Effect}, \, \text{Text}$$
   * Permite filtrar y clasificar las capas generadas en la grilla de Aegisub.
2. **Prioridad Numérica de Emisión (`Queue Order`):**
   * Controla el orden secuencial en el que se imprimirán las líneas en el documento final.
   * **Jerarquía Global de Emisión:** El motor agrupa las líneas por cola y procesa primero **todas las colas de menor `Queue Order` para todas las líneas de diálogo**, seguidas íntegramente por las colas de orden superior:
     $$\text{SortKey}(Q) = \left(\min_{l \in Q} (\text{queue\_order}_l), \, \text{qid}\right)$$
   * **Reglas de Desempate y Fallbacks:**
     * *Empate numérico o sin orden:* Si dos o más colas no especifican `Queue Order` (o comparten el mismo valor entero), se ordenan **alfabéticamente por su `Queue ID`**.
     * *Campos vacíos:* Si no se especifica ni `Queue ID` ni `Queue Order`, las líneas se integran en la cola `"default"` y se ordenan de manera estable según el orden de creación del nodo (`ID` en el lienzo).
     * *Dentro de cada cola:* Las líneas se ordenan secuencialmente por el índice original de la línea de diálogo (`line_idx`) y el orden interno del evento.

---

## 3. Persistencia de Estados y Variables de Contexto

Pyxis permite registrar, transferir y acumular estados a lo largo de las distintas fases de evaluación:

1. **`Define Vars` (`Variables`):** Inyecta variables personalizadas al contexto de ejecución (ej. `my_scale = 120`, `custom_color = "#FF00AA"`), haciéndolas accesibles de inmediato para cualquier expresión en la iteración actual.
2. **`Get Var` (`Variables`):** Lee y emite el valor de cualquier variable del contexto (`i`, `j`, `N`, `syl.duration`, `line.start_time`, `fx.pos_x`, etc.).
3. **`Memory` (`Variables`):** Almacén clave-valor persistente con dos modos operativos:
   * `remember`: Almacena el valor actual bajo una clave designada.
   * `retrieve`: Recupera el último valor guardado bajo esa clave en iteraciones anteriores. Permite crear acumuladores de posición, trayectorias cinemáticas continuas o lectores de estados previos.

---

## 4. Tabla de Variables y Métricas del Contexto ASS

Pyxis Effector organiza las variables de tiempo y espacio de forma **jerárquica y modular**:
* **`line` / `l`:** Tiempos **globales / absolutos** del vídeo ($ms$), métricas del *bounding box* y atributos del estilo original de Aegisub.
* **`syl` / `word`:** Tiempos **locales relativos** al inicio de la línea base ($[0, \text{line.dur}]$).
* **`char`:** Tiempos **locales relativos** al inicio de su sílaba contenedora ($[0, \text{syl.dur}]$).
* **`fx`:** Rango temporal de la línea generada en ASS ($[0, \text{fx.dur}]$). Permite evaluar transformaciones `\t(...)` en el tiempo del efecto mediante el offset $\text{ini} = \text{line.start\_time} - \text{fx.start\_time}$.

En cualquier campo de expresión, condición o script de Pyxis, las siguientes variables contextuales están disponibles de forma nativa organizadas por dominio:

### 4.1. Dominio de Línea de Origen (`line.` o `l.`)
Representa la línea de diálogo activa leída de Aegisub. Proporciona sus marcas de tiempo absolutas, texto, metadatos de cabecera ASS, coordenadas métricas de pantalla y márgenes:

| Variable | Tipo | Descripción y Unidad | Ejemplo de Uso |
| :--- | :---: | :--- | :--- |
| `line.start_time` / `l.start_time` | `int` | Tiempo de inicio absoluto de la línea en el vídeo ($ms$). | `line.start_time - 500` |
| `line.end_time` / `l.end_time` | `int` | Tiempo de fin absoluto de la línea en el vídeo ($ms$). | `line.end_time + 300` |
| `line.dur` / `line.duration` / `l.dur` | `int` | Duración neta de la línea ($ms$): $t_{\text{end}} - t_{\text{start}}$. | `line.dur / 2` |
| `line.mid_time` / `l.mid_time` | `float` | Instante temporal medio de la línea: $t_{\text{start}} + \frac{t_{\text{dur}}}{2}$. | `line.mid_time` |
| `line_start_time`, `line_end_time`, `line_dur` | `int` | Alias globales planos sin prefijo para los tiempos de la línea ($ms$). | `line_start_time` |
| `line.i` / `l.i` | `int` | Índice ordinal de la línea activa en el lote procesado ($1 \dots N$). | `line.i == 1` |
| `line.n` / `l.n` | `int` | Cantidad total de líneas seleccionadas en el lote. | `line.i / line.n` |
| `line.text` / `l.text` | `string` | Texto de la línea despojado de etiquetas de estilo y marcas de karaoke. | `len(line.text)` |
| `line.raw_text` / `l.raw_text` | `string` | Texto original de la línea conservando etiquetas `{\...}` y marcas `\k`. | `line.raw_text` |
| `line.style` / `line.style_name` | `string` | Nombre canónico del estilo ASS asignado a la línea en Aegisub. | `line.style == "Default"` |
| `line.actor` / `l.actor` | `string` | Campo de actor o personaje de la línea ASS. | `line.actor` |
| `line.effect` / `l.effect` | `string` | Campo descriptor de efecto especial de la línea ASS. | `line.effect` |
| `line.layer` / `l.layer` | `int` | Número de capa ASS asignado a la línea (profundidad $Z$). | `line.layer + 1` |
| `line.center`, `line.middle` / `l.x`, `l.y` | `float` | Centro horizontal ($X$) y vertical ($Y$) del *bounding box* de la línea (px). | `line.center, line.middle` |
| `line.left`, `line.right` | `float` | Borde delimitador horizontal izquierdo y derecho de la línea (px). | `line.right - line.left` |
| `line.top`, `line.bottom` | `float` | Borde delimitador vertical superior e inferior de la línea (px). | `line.bottom` |
| `line.width`, `line.height` | `float` | Anchura y altura calculadas del texto de la línea completa (px). | `line.width` |
| `line.descent` (o `l.descend`), `line.extlead` | `float` | Altura de descenso tipográfico e interlineado adicional externo (px). | `line.bottom + line.descent` |
| `line.pos_x`, `line.pos_y` | `float` | Posición horizontal y vertical absoluta de la línea (`\pos` explícito o calculado). | `line.pos_x, line.pos_y` |
| `line.org_x`, `line.org_y` | `float` | Coordenadas de pivote o anclaje de rotación de la línea (`\org` o centro métrico). | `line.org_x, line.org_y` |
| `line.margin_l`, `line.margin_r`, `line.margin_v` | `int` | Márgenes izquierdo, derecho y vertical configurados en la línea o estilo (px). | `line.margin_l` |
| `line.margin_t`, `line.margin_b` | `int` | Márgenes superior e inferior individuales desglosados (px). | `line.margin_t` |

### 4.2. Estilo de Origen (`line.<style_prop>`)
Propiedades tipográficas, cromáticas, de contorno y de alineación heredadas del encabezado `[V4+ Styles]` del archivo ASS o sobreescritas en la línea:

| Variable | Tipo | Descripción y Formato | Ejemplo de Uso |
| :--- | :---: | :--- | :--- |
| `line.fontname` | `string` | Familia tipográfica configurada en el estilo original (ej. `"Arial"`, `"Montserrat"`). | `line.fontname` |
| `line.fontsize` | `float` | Tamaño de fuente del estilo base en puntos/píxeles ($pt$). | `line.fontsize * 1.5` |
| `line.bold` | `bool` | Indicador booleano de peso negrita definido en el estilo (`True` / `False`). | `line.bold` |
| `line.italic` | `bool` | Indicador booleano de estilo cursiva definido en el estilo (`True` / `False`). | `line.italic` |
| `line.underline` | `bool` | Indicador booleano de subrayado definido en el estilo (`True` / `False`). | `line.underline` |
| `line.strikeout` | `bool` | Indicador booleano de texto tachado definido en el estilo (`True` / `False`). | `line.strikeout` |
| `line.align` | `int` | Alineación Numpad configurada en el estilo de origen ($1 \dots 9$). | `line.align` |
| `line.scale_x`, `line.scale_y` | `float` | Escalas porcentuales horizontal y vertical del estilo base ($100.0 = 100\%$). | `line.scale_x` |
| `line.spacing` | `float` | Espaciado o interletreado (*tracking*) entre caracteres en píxeles (`\fsp`). | `line.spacing` |
| `line.outline` / `line.bord` | `float` | Grosor del contorno o borde tipográfico del estilo en píxeles (`\bord`). | `line.outline` |
| `line.shadow` / `line.shad` | `float` | Distancia o profundidad de sombra arrojada del estilo en píxeles (`\shad`). | `line.shadow` |
| `line.color1` | `string` | Color primario del estilo (`\1c`) en formato ASS `&HBBGGRR&`. | `line.color1` |
| `line.color2` | `string` | Color secundario o de karaoke del estilo (`\2c`) en formato ASS `&HBBGGRR&`. | `line.color2` |
| `line.color3` | `string` | Color del contorno o borde del estilo (`\3c`) en formato ASS `&HBBGGRR&`. | `line.color3` |
| `line.color4` | `string` | Color de la sombra del estilo (`\4c`) en formato ASS `&HBBGGRR&`. | `line.color4` |
| `line.alpha1` .. `line.alpha4` | `string` | Canales alfa individuales (1: primario, 2: karaoke, 3: borde, 4: sombra) en ASS `&HAA&`. | `line.alpha1` |
| `line.angle` / `line.frz` | `float` | Ángulo nominal de rotación $Z$ configurado en el estilo en grados sexagesimales. | `line.frz` |
| `line.frx`, `line.fry` | `float` | Ángulos de rotación 3D intrínsecos de la línea en grados sexagesimales. | `line.frx` |
| `line.fax`, `line.fay` | `float` | Factores de deformación tipográfica por cizallamiento oblicuo (*shear*). | `line.fax` |

### 4.3. Unidades Derivadas: Sílabas (`syl`), Caracteres (`char`) y Palabras (`word`)
Unidades generadas al iterar con `Main Loop` en modo `syl`, `char` o `word`. Cada unidad hereda automáticamente las propiedades tipográficas del estilo base (`syl.fontname`, `syl.color1`..`4`, `syl.fontsize`, `char.fontname`, etc.):

| Unidad | Variable | Descripción y Unidad | Ejemplo de Uso |
| :--- | :--- | :--- | :--- |
| **Sílaba (`syl`)** | `syl.start_time`, `syl.end_time` | Tiempos de inicio y fin relativos al comienzo de la línea ($ms$). | `syl.start_time` |
| | `syl.dur` / `syl.duration` | Duración del karaoke de la sílaba en milisegundos ($ms$). | `syl.dur` |
| | `syl.mid_time` | Instante medio relativo de la sílaba: $t_{\text{start}} + \frac{t_{\text{dur}}}{2}$. | `syl.mid_time` |
| | `syl.syl_start`, `syl.syl_end`, `syl.syl_mid` | Rango temporal de la sílaba relativo al efecto `fx` ($\text{ini} + \text{syl.start\_time}$). | `\t(syl.syl_start, syl.syl_end, \tags)` |
| | `syl.i` / `syl.n` | Índice de la sílaba en la línea ($1 \dots N$) y total de sílabas. | `syl.i / syl.n` |
| | `syl.text`, `syl.text_stripped` | Texto de la sílaba sin etiquetas ni marcas de karaoke. | `syl.text` |
| | `syl.center`, `syl.middle` / `syl.x`, `syl.y` | Centro horizontal ($X$) y vertical ($Y$) del *bounding box* de la sílaba (px). | `syl.center, syl.middle` |
| | `syl.left`, `syl.right`, `syl.top`, `syl.bottom` | Borde izquierdo, derecho, superior e inferior de la sílaba (px). | `syl.right - syl.left` |
| | `syl.width`, `syl.height` | Anchura y altura métricas calculadas de la sílaba (px). | `syl.width` |
| | `syl.descent`, `syl.extlead` | Altura de descenso tipográfico y espaciado de línea en la sílaba (px). | `syl.descent` |
| | `syl.prespace`, `syl.postspace` | Espacios en blanco precedentes o posteriores de la sílaba. | `syl.prespace` |
| | `syl.pos_x`, `syl.pos_y`, `syl.org_x`, `syl.org_y` | Coordenadas de anclaje de posición y centro de rotación de la sílaba. | `syl.pos_x, syl.pos_y` |
| **Carácter (`char`)** | `char.start_time`, `char.end_time` | Tiempos de inicio y fin relativos al comienzo de su **sílaba contenedora** ($ms$). | `char.start_time` |
| | `char.dur` / `char.duration` | Duración temporal calculada del carácter individual ($ms$). | `char.dur` |
| | `char.mid_time` | Instante medio relativo del carácter dentro de su sílaba. | `char.mid_time` |
| | `char.char_start`, `char.char_end`, `char.char_mid` | Rango temporal del carácter relativo al efecto `fx` ($ms$). | `\t(char.char_start, char.char_end, \tags)` |
| | `char.syl_start`, `char.syl_end`, `char.syl_mid` | Rango temporal de la sílaba contenedora relativo al efecto `fx` ($ms$). | `\t(char.syl_start, char.syl_end, \tags)` |
| | `char.i` / `char.n` | Índice del carácter en la línea ($1 \dots N$) y total de caracteres. | `char.i` |
| | `char.syl_i`, `char.word_i` | Índice posicional del carácter dentro de su sílaba y dentro de su palabra. | `char.syl_i` |
| | `char.text` | Glifo del carácter activo. | `char.text` |
| | `char.center`, `char.middle` / `char.x`, `char.y` | Coordenadas centrales del carácter en pantalla (px). | `char.center, char.middle` |
| | `char.left`, `char.right`, `char.top`, `char.bottom` | Límites del cuadro delimitador del glifo del carácter (px). | `char.left` |
| | `char.width`, `char.height` | Dimensiones métricas del glifo del carácter (px). | `char.width` |
| | `char.descent`, `char.extlead` | Métricas tipográficas de descenso y espaciado del glifo (px). | `char.descent` |
| **Palabra (`word`)** | `word.start_time`, `word.end_time`, `word.dur`, `word.mid_time` | Tiempos de inicio, fin, duración y punto medio relativos a la línea ($ms$). | `word.start_time` |
| | `word.word_start`, `word.word_end`, `word.word_mid` | Tiempos de inicio, fin y punto medio relativos al efecto `fx` ($ms$). | `word.word_start` |
| | `word.i` / `word.n` | Índice de la palabra en la línea ($1 \dots N$) y total de palabras. | `word.i` |
| | `word.text` | Texto de la palabra completa despojado de etiquetas. | `word.text` |
| | `word.center`, `word.middle` / `word.x`, `word.y` | Centro horizontal ($X$) y vertical ($Y$) de la palabra en pantalla (px). | `word.center, word.middle` |
| | `word.left`, `word.right`, `word.top`, `word.bottom` | Bounding box delimitador de la palabra completa (px). | `word.right` |
| | `word.width`, `word.height` | Anchura y altura de la palabra completa (px). | `word.width` |
| | `word.descent`, `word.extlead` | Métricas tipográficas de descenso y espaciado de la palabra (px). | `word.descent` |

### 4.4. Métricas de Tinta Real (`ink`) y Unidades Vecinas (`prev` / `next`)

| Categoría | Variable | Descripción | Ejemplo de Uso |
| :--- | :--- | :--- | :--- |
| **Tinta Real (`ink`)** | `ink.width`, `ink.height` | Anchura y altura del trazado/glifo real renderizado (sin márgenes de caja tipográfica). | `ink.width` |
| | `ink.center`, `ink.middle` / `ink.x`, `ink.y` | Centro horizontal ($X$) y vertical ($Y$) basado en los contornos reales de tinta. | `ink.center, ink.middle` |
| | `ink.left`, `ink.right`, `ink.top`, `ink.bottom` | Bounding box exacto de los píxeles de tinta proyectados en coordenadas de pantalla. | `ink.left` |
| | `ink.l.*`, `ink.syl.*`, `ink.char.*`, `ink.word.*` | Acceso explícito por ámbito a las métricas de tinta de la línea, sílaba, carácter o palabra. | `ink.syl.center` |
| **Vecinos (`prev` / `next`)** | `prev.*` / `next.*` | Introspección sobre la unidad anterior o siguiente (`text`, `dur`, `start_time`, `x`, `y`, `width`, etc.). | `prev.width` |
| | `is_first`, `is_last` | Banderas booleanas que indican si la unidad es la primera o la última de la secuencia. | `is_first` |
| | `has_prev`, `has_next` | `True` si existe una unidad precedente o sucesora válida en la cadena. | `has_prev` |

### 4.5. Sub-bucles (`MaxLoop`), Efecto (`fx`) y Variables Globales de Entorno

| Categoría | Variable | Descripción y Fórmula | Ejemplo de Uso |
| :--- | :--- | :--- | :--- |
| **Sub-bucle (`MaxLoop`)**| `j` | Índice de la sub-iteración activa ($1 \dots N$). | `j` |
| | `maxj` / `maxloop` | Total de repeticiones configuradas en el sub-bucle. | `maxj` |
| | `module` / `m` / `ratio` | Progreso normalizado de la sub-iteración: $\frac{j - 1}{\text{maxj} - 1} \in [0.0, 1.0]$. | `module` |
| **Efecto (`fx`)** | `fx.pos_x`, `fx.pos_y` | Coordenadas de posición de anclaje resuelta para el elemento activo en pantalla. | `fx.pos_x, fx.pos_y` |
| | `fx.start_time`, `fx.end_time` | Tiempos de inicio y fin de la línea ASS generada ($ms$). | `fx.start_time` |
| | `fx.dur` | Duración efectiva de la línea generada en ASS ($ms$). | `fx.dur` |
| **Entorno Global** | `fps` | Tasa de fotogramas por segundo del vídeo activo en Aegisub (ej. `23.976`, `60.0`). | `fps` |
| | `frame_dur` / `fd` | Duración de un fotograma en milisegundos: $\frac{1000}{\text{fps}}$ (ej. $41.708$ ms a $23.976$ fps). | `3 * fd` |
| | `ini` | Desfase temporal relativo: $\text{ini} = \text{line.start\_time} - \text{fx.start\_time}$ ($ms$). | `ini + syl.start_time` |
| | `st`, `et`, `dur` | Tiempos de inicio, fin y duración activos del elemento procesado ($ms$). | `st, et` |
| | `maxgap` | Techo temporal máximo para mediciones inter-línea con `sync()` ($ms$, por defecto `2000.0`). | `maxgap` |

---

## 5. Motor de Evaluación de Expresiones y Resolución de Strings

Pyxis Effector incorpora un motor interno de resolución dinámico (el evaluador numérico contextual y el procesador de plantillas de texto) capaz de computar expresiones matemáticas, operadores ternarios de Python y variables embebidas directamente en las cajas de texto, nodos de cadena y bloques de tags ASS:

### 5.1. Evaluación Numérica y Algebraica en Cajas de Texto
Cualquier campo numérico (en `MultiTag`, `Math`, `Retime`, `Slicers`, `Particles`, etc.) evalúa operaciones matemáticas en tiempo real:
* **Álgebra directa y funciones:** `syl.center + (i * 15)`, `line.width / 2`, `math.sin(t) * 50`.
* **Atajos Pyxis de fotogramas y ratios:** `3f` ($3 \times \text{frame\_dur}$), `0.5r` ($50\%$ de la duración).
* **Hexadecimales ASS:** `&HFF&` se interpreta numéricamente como `255`.

### 5.2. Expresiones Ternarias de Python
En nodos de variables (`Define Vars`) o campos condicionales se soportan sentencias ternarias nativas de Python:
```python
angle = 1.4 if l.layer == 1 else -1.4
color_fx = "&H00FF00&" if syl.i % 2 == 0 else "&H0000FF&"
```

### 5.3. Evaluador Universal de Strings y Bloques de Tags ASS
Los bloques de etiquetas delimitados por llaves `{\...}` en cualquier nodo productor de subtítulos (incluyendo `Basics/String`, `Basics/MultiTag`, `System/Output`, transformaciones vectoriales y capas cinemáticas) son procesados por el motor de evaluación de plantillas antes de la exportación final.

> [!IMPORTANT]
> **Aislamiento de Trazados ASSdraw:** El evaluador de expresiones y macros opera exclusivamente sobre el interior de los bloques de etiquetas `{\...}`. Todo texto plano o comando de dibujo vectorial (`m 0 0 l 100 0 ...`) ubicado fuera de las llaves permanece 100% inmune, garantizando que coordenadas geométricas complejas nunca se confundan con identificadores o variables.

El lenguaje de plantillas integra 4 mecanismos universales de resolución:

1. **Expresiones algebraicas y variables directas en paréntesis de tags ASS (`\tag(...)`):**
   * Rotaciones y escalas: `\frz(angle2)`, `\frz(j * 15)`, `\fscxy(120 + i*5)`.
   * Posiciones y pivotes: `\pos(syl.center + 10, syl.middle)`, `\org(fx.pos_x, fx.pos_y - 1000)`.
   * Alfas y colores: `\alpha(255)`, `\1a(128)`, `\1c(line.color1)`, `\1c(ass_color(255, 128, 0))`.
2. **Transformaciones temporales `\t(...)` dinámicas:**
   * Tiempos y tags evaluados: `\t(0, 150, \frz0)\t(fx.dur-150, fx.dur, \frz(angle2))`.
3. **Expresiones, variables y ternarios aislados entre paréntesis `(...)`:**
   * Evaluación de variables, atributos y cálculos fuera de tags: `(syl.text)`, `(syl.dur)`, `(fx.dur)`, `(j * 15)`, `(line.text)`.
   * Selección condicional de etiquetas o valores dentro del bloque: `(\blur3 if i == 1 else \blur0)`, `(Colores())`.
4. **Conversión automática de alfas decimales a hexadecimal ASS:**
   * Conversión en tiempo real de enteros a hex ASS: `\4a100` $\to$ `\4a&H64&`, `\alpha255` $\to$ `\alpha&HFF&`, `\1a0` $\to$ `\1a&H00&`.

---

### 5.4. Catálogo Canónico de Dark Tags (Tags Compuestos y de Contexto)

Los *Dark Tags* son macros compactas de alta velocidad que expanden sintaxis abreviadas a secuencias canónicas ASS puras:

#### 5.4.1. Rotaciones con Auto-Origen (`\fr*o`)
Inyectan automáticamente la etiqueta `\org(X, Y)` tomando como centro de gravedad las coordenadas del elemento activo en el fotograma actual (`fx.pos_x`, `fx.pos_y` o `syl.center`, `syl.middle`):

| Dark Tag | Sintaxis Directa | Sintaxis Evaluada | Expansión ASS Generada |
| :--- | :--- | :--- | :--- |
| `\fro`, `\frzo` | `\fro45`, `\frzo-30` | `\fro(j * 15)` | `\org(X, Y)\frz<val>` |
| `\frxo` | `\frxo30` | `\frxo(syl.i * 5)` | `\org(X, Y)\frx<val>` |
| `\fryo` | `\fryo60` | `\fryo(sin(j) * 45)` | `\org(X, Y)\fry<val>` |
| `\frxyo` | `\frxyo45` | `\frxyo(15)` | `\org(X, Y)\frx<val>\fry<val>` |
| `\frxzo` | `\frxzo30` | `\frxzo(20)` | `\org(X, Y)\frx<val>\frz<val>` |
| `\fryzo` | `\fryzo45` | `\fryzo(25)` | `\org(X, Y)\fry<val>\frz<val>` |
| `\frxyzo` | `\frxyzo30` | `\frxyzo(10)` | `\org(X, Y)\frx<val>\fry<val>\frz<val>` |

#### 5.4.2. Escalas y Tamaño por Ratio de Estilo (`\fsc*r`, `\fsr`)
Multiplican el valor nominal configurado en el estilo de Aegisub (`style.scale_x`, `style.scale_y`, `style.fontsize`) por el factor multiplicador especificado:

| Dark Tag | Sintaxis Directa | Sintaxis Evaluada | Expansión ASS Generada |
| :--- | :--- | :--- | :--- |
| `\fscxr` | `\fscxr1.5` | `\fscxr(1.0 + 0.2*j)` | `\fscx(style.scale_x * ratio)` |
| `\fscyr` | `\fscyr0.8` | `\fscyr(cos(t))` | `\fscy(style.scale_y * ratio)` |
| `\fscxyr` | `\fscxyr2.0` | `\fscxyr(1.5)` | `\fscx(style.scale_x * ratio)\fscy(style.scale_y * ratio)` |
| `\fsr` | `\fsr1.2` | `\fsr(1.0 + syl.i * 0.1)` | `\fs(style.fontsize * ratio)` |

#### 5.4.3. Transformaciones Temporales Contextuales (`\te`, `\ts`, `\tc`, `\tw`)
Atajos temporales paramétricos que se adaptan a la duración total del efecto o a la posición cronológica del elemento:

| Dark Tag | Sintaxis de Uso | Expansión ASS Resultante | Descripción Operativa |
| :--- | :--- | :--- | :--- |
| `\te` | `\te(t1, t2, \tags)`<br>`\te(t1, t2, accel, \tags)`<br>`\te(t, \tags)` | `\t(fx.dur - t2, fx.dur - t1, \tags)`<br>`\t(fx.dur - t2, fx.dur - t1, accel, \tags)`<br>`\t(fx.dur - t, fx.dur, \tags)` | Animación invertida respecto al fin de la línea (`fx.dur`). |
| `\ts` | `\ts(t1, t2, \tags)`<br>`\ts(t1, t2, accel, \tags)`<br>`\ts(t, \tags)` | `\t(syl.start + t1, syl.start + t2, \tags)`<br>`\t(syl.start + t1, syl.start + t2, accel, \tags)`<br>`\t(syl.start, syl.start + t, \tags)` | Animación relativa al inicio temporal de la sílaba. |
| `\tc` | `\tc(t1, t2, \tags)`<br>`\tc(t1, t2, accel, \tags)`<br>`\tc(t, \tags)` | `\t(char.start + t1, char.start + t2, \tags)`<br>`\t(char.start + t1, char.start + t2, accel, \tags)`<br>`\t(char.start, char.start + t, \tags)` | Animación relativa al inicio temporal del carácter. |
| `\tw` | `\tw(t1, t2, \tags)`<br>`\tw(t1, t2, accel, \tags)`<br>`\tw(t, \tags)` | `\t(word.start + t1, word.start + t2, \tags)`<br>`\t(word.start + t1, word.start + t2, accel, \tags)`<br>`\t(word.start, word.start + t, \tags)` | Animación relativa al inicio temporal de la palabra. |

#### 5.4.4. Tags Multicanal y Agrupados
| Dark Tag | Expansión ASS Directa | Ejemplo |
| :--- | :--- | :--- |
| `\fscxy` | `\fscx<val>\fscy<val>` | `\fscxy150` $\to$ `\fscx150\fscy150` |
| `\faxy` | `\fax<val>\fay<val>` | `\faxy0.2` $\to$ `\fax0.2\fay0.2` |
| `\frxyz`, `\frxy`, `\frxz`, `\fryz` | Rotaciones 3D combinadas | `\frxyz45` $\to$ `\frx45\fry45\frz45` |
| `\xybord`, `\xyshad`, `\bs` | Bordes y sombras simultáneos | `\bs3` $\to$ `\bord3\shad3` |
| `\[1-4]+c` (ej. `\134c`, `\13c`, `\234c`) | Asignación simultánea de color | `\134c&H00FFFF&` $\to$ `\1c&H00FFFF&\3c&H00FFFF&\4c&H00FFFF&` |
| `\[1-4]+a` (ej. `\134a`, `\14a`, `\34a`) | Asignación simultánea de alfa | `\134a&H80&` $\to$ `\1a&H80&\3a&H80&\4a&H80&` |

#### 5.4.5. Macros de Restauración de Estilo (`\tag~`) y Generación Estocástica (`\tagR(...)`)
* **Restauración (`~`):** Recupera instantáneamente los valores definidos en la plantilla de estilo original: `\c~` (color primario), `\fscxy~` (escala $X/Y$ base), `\fs~` (tamaño de fuente), `\bs~` (borde y sombra base), `\134c~`, `\134a~`, `\frxyz~`, `\blur~`.
* **Estocásticos (`R`):** Genera variaciones aleatorias continuas o discretas integradas: `\frzR(-30, 30)`, `\134cR()`, `\alphaR(0, 128)`, `\froR(-20, 20)`, `\fscxyrR(1.0, 1.5)`.

---

## 6. Sincronización Inter-Línea y Detección de Gaps (`sync`)

Pyxis Effector incorpora el sistema de sincronización inter-línea **`sync`**, diseñado para medir dinámicamente la separación temporal (*gap* en milisegundos) entre la línea de diálogo activa y su línea adyacente anterior o posterior según el orden de aparición original del subtítulo o por criterios de coincidencia.

### 6.1. Función de Sistema `sync()`
Accesible directamente desde expresiones de tiempo, propiedades de nodos y scripts:

```python
sync(direction="next", mode="order", max_gap=2000)
```

* **`direction` (1º argumento):** `next` (siguiente línea) o `prev` (línea anterior). Por defecto: `next`.
* **`mode` (2º argumento):** Criterio de coincidencia de línea original:
  * `1` o `"order"` *(default)*: Siguiente/anterior línea en orden de aparición en el subtítulo (ignorando líneas de comentario).
  * `2` o `"style"`: Líneas que coincidan en el estilo ASS (`line.style`).
  * `3` o `"actor"`: Líneas que coincidan en el actor (`line.actor`).
  * `4` o `"effect"`: Líneas que coincidan en el campo de efecto (`line.effect`).
  * `5` o `"layer"`: Líneas que coincidan en el número de capa (`line.layer`).
* **`max_gap` (3º argumento):** Límite superior en milisegundos (por defecto `2000.0` ms o el valor definido en `maxgap`).

#### Ejemplos de uso en reajuste de tiempos:
```python
# Extiende el final del efecto la mitad del gap a la siguiente línea (máximo 2000ms):
end_time = l.end_time + (sync(next, order) / 2)

# Adelanta el inicio del efecto la mitad del gap a la línea anterior con el mismo estilo (máximo 1500ms):
start_time = l.start_time - (sync(prev, style, 1500) / 2)

# Uso con identificadores numéricos:
start_time = l.start_time - (sync(prev, 2) / 2)
```

### 6.2. Namespace de Propiedades Globales (`sync.*`)
Para animaciones en bloques de tags ASS (`\fad`, `\t`), Pyxis inyecta el namespace `sync` con propiedades directas:

| Propiedad | Dirección | Filtro de Modo | Valor de Retorno |
| :--- | :---: | :---: | :--- |
| `sync.next` / `sync.order_next` | `next` | `order` | Gap a la siguiente línea de diálogo (ms). |
| `sync.prev` / `sync.order_prev` | `prev` | `order` | Gap a la línea de diálogo anterior (ms). |
| `sync.style_next` / `sync.style_prev` | `next` / `prev` | `style` | Gap a la línea adyacente con mismo estilo. |
| `sync.actor_next` / `sync.actor_prev` | `next` / `prev` | `actor` | Gap a la línea adyacente con mismo actor. |
| `sync.effect_next` / `sync.effect_prev` | `next` / `prev` | `effect` | Gap a la línea adyacente con mismo efecto. |
| `sync.layer_next` / `sync.layer_prev` | `next` / `prev` | `layer` | Gap a la línea adyacente con misma capa. |

#### Ejemplos de uso en Tags ASS:
```ass
{\fad(sync.order_prev / 2, sync.order_next / 2)}
{\t(0, sync.style_next, \fscxy120)}
{\t(fx.dur - sync.next / 2, fx.dur, \alpha&HFF&)}
```

### 6.3. Sobreescritura del Techo Temporal (`maxgap`)
El límite por defecto de 2000ms puede redefinirse global o localmente para todas las evaluaciones de `sync.*` asignando la variable `maxgap` en un nodo `Define Vars` o en un script Python/Lua:
```python
maxgap = 3500
```
Todas las llamadas posteriores a `sync.order_next` o `sync(next, order)` utilizarán automáticamente `3500.0` como techo máximo.

### 6.4. Comportamiento en Solapamientos y Límites
* **Líneas Solapadas ($\text{gap} < 0$):** Si las dos líneas se superponen temporalmente, `sync` devuelve el valor negativo exacto ($\Delta t < 0$), informando la magnitud del encimado.
* **Sin línea adyacente (primera/última):** Si no existe una línea que cumpla el criterio, retorna el techo `maxgap` configurado.

---

## 7. Telemetría de Rendimiento ASS y Estimación Pre-Generación (`Telemetry`)

En composiciones que combinan bucles fotograma a fotograma (`MaxLoop` en modo `fbf`), segmentación poligonal (`Shape/Slicer`), partículas (`Functions/Particles`) o desenfoques (`\blur`), la carga de reproducción depende principalmente del **coste computacional de rasterización y composición de mapas de bits por fotograma** en `libass`.

El diagnóstico de rendimiento se estructura en dos fases: **Estimación Estática Pre-Generación** y **Telemetría de Renderizado por Fotograma**.

```
[Topología del Grafo + Selección ASS]
                 │
                 ├──► [1. Estimación Pre-Generación (Hover en Generate Layers)]
                 │      • Concurrencia Sweep-Line (Peak Simultaneous Lines)
                 │      • Factor de Expansión y Peso ASS Estimado (KB / MB)
                 │      • Perfil Vectorial (FBF / Slicer / Particles / Audio / Script)
                 │
                 └──► [2. Telemetría Nativa libass (Refresh en Previewer / Scan en Telemetry)]
                        • Renderizado C nativo paralelo + reloj de hardware QPC (1 µs)
                        • Curva de carga integrada en la barra del Previewer
                        • Panel de diagnóstico (4 métricas superpuestas + navegación 2D)
```

### 7.1. Estimación Estática Pre-Generación
Al situar el cursor sobre el botón **`Generate Layers`**, el motor evalúa la topología activa y las líneas de entrada sin necesidad de compilar el efecto:

1. **Líneas Estimadas y Factor de Expansión:**
   Calcula el total de eventos `Dialogue:` que emitirán los nodos `System/Output` conectados ($\hat{N}_{\text{out}}$) y la relación de multiplicación respecto a las líneas originales seleccionadas ($N_{\text{in}}$):
   $$\text{Expansion Ratio} = \frac{\hat{N}_{\text{out}}}{\max(1, N_{\text{in}})}$$
2. **Concurrencia Máxima de Líneas (*Sweep-Line Peak Simultaneous Lines*):**
   La concurrencia instantánea mide cuántas capas coexisten simultáneamente en pantalla en un instante temporal $t$. El estimador aplica un algoritmo de barrido de intervalos temporales (*Sweep-Line*) sobre los eventos $[t_{\text{start}}, t_{\text{end}})$ proyectados por cada rama:
   $$L_{\text{peak}} = \max_{t} \sum_{k=1}^{\hat{N}_{\text{out}}} \mathbf{1}_{[t_{\text{start}, k},\, t_{\text{end}, k})}(t)$$
   Esta métrica cuantifica el número máximo de capas superpuestas en el fotograma más denso del efecto.
3. **Peso ASS Estimado (`KB` / `MB`) y Perfil de Renderizado:**
   Pondera la longitud esperada de cada línea según las operaciones presentes en el grafo (trazados vectoriales ASSdraw, recortes `\clip`, transformaciones `\t`) y muestra los identificadores de subsistemas activos (`FBF`, `Slicer`, `Particles`, `Audio`, `Script`).

### 7.2. Motor de Telemetría Nativa Multi-Proceso (`libass` + QPC)
Al ejecutar **`Refresh`** en el nodo `System/Previewer` (o **`Scan`** en el panel `Telemetry`), el motor perfila el rendimiento de renderizado mediante la biblioteca nativa `libass`:

1. **Aislamiento del Efecto Evaluado:**
   El motor de telemetría evalúa **exclusivamente las líneas generadas por el efecto** junto con los estilos y metadatos del script, aislando las líneas no modificadas para que las métricas reflejen con exactitud el coste atribuible al grafo activo.
2. **Paralelismo Multi-Worker y Cronometraje de Hardware (`QPC`):**
   El rango temporal del clip previsualizado se divide en lotes entre múltiples procesos paralelos (`multiprocessing`). Cada proceso inicializa una instancia de `libass` a la resolución del proyecto ($\text{PlayResX} \times \text{PlayResY}$) y ejecuta `ass_render_frame` fotograma a fotograma utilizando el contador de rendimiento de hardware ($\text{QPC}$, resolución de $1\,\mu\text{s}$).
3. **Presupuesto Temporal de Fotograma (*Frame Budget*):**
   Para mantener la reproducción a la cadencia de vídeo sin pérdida de cuadros (*frame drops*), el tiempo de renderizado de cada fotograma ($T_{\text{render}}$) debe permanecer por debajo del intervalo temporal de fotograma definido por los $\text{FPS}$:
   $$\text{Budget}_{\text{ms}} = \frac{1000}{\text{FPS}}, \qquad \text{Budget \%} = \frac{T_{\text{render}}}{\text{Budget}_{\text{ms}}} \times 100\%$$
   A $23.976\,\text{fps}$ el presupuesto por fotograma es de $41.71\,\text{ms}$, mientras que a $60\,\text{fps}$ es de $16.67\,\text{ms}$. Todo fotograma cuyo coste supere $\text{Budget}_{\text{ms}}$ ($\text{Budget \%} > 100\%$) se registra como una caída de fotograma potencial.
4. **Inspección de Memoria de Bitmaps y Primitivas (`ASS_Image`):**
   En cada fotograma $f$, el motor recorre la lista enlazada de mapas de bits alfa generados por `libass` ($\{I_1, I_2, \dots, I_M\}$) y extrae tres métricas estructurales:
   * **`ASS Objects` ($M_f$):** Cantidad total de primitivas de imagen compuestas en el fotograma.
   * **`Total Bitmap RAM`:** Suma de la huella de memoria de los mapas de bits activos en el fotograma:
     $$\text{RAM}_{\text{total}}(f) = \frac{1}{1024} \sum_{m=1}^{M_f} \left( w_m \times h_m \right) \quad [\text{KB}]$$
   * **`Largest Bitmap`:** Huella del mayor mapa de bits individual en el fotograma:
     $$\text{RAM}_{\text{max}}(f) = \frac{1}{1024} \max_{1 \le m \le M_f} \left( w_m \times h_m \right) \quad [\text{KB}]$$

### 7.3. Panel Telemetry y Controles de Navegación
El panel **`Telemetry`** (accesible desde el tooltip de `Generate Layers` o pulsando sobre la curva de carga en el `Previewer`) presenta el diagnóstico en tres regiones sincronizadas:

1. **Visor de Vídeo y HUD por Fotograma (Cuadrante Superior Izquierdo):**
   * El reproductor del nodo `System/Previewer` se sincroniza con el visor conservando el estado de reproducción, pista de subtítulos y nivel de zoom focal.
   * Dispone de control de redimensionamiento manteniendo la relación de aspecto nativa del vídeo.
   * Barra inferior con HUD numérico: número de fotograma (`F`), código de tiempo (`MM:SS.mmm`), coste de renderizado (`ms`), memoria de mapas de bits (`KB`/`MB`) y conteo de objetos (`obj`).
2. **Tacómetro de Presupuesto, Tarjetas KPI y Puntos Críticos (Cuadrante Superior Derecho):**
   * **Arco de Presupuesto (`Frame Budget %`):** Tacómetro vectorial semicircular que indica el porcentaje de carga máxima respecto al presupuesto de fotograma disponible.
   * **Tarjetas KPI:** Valores consolidados del clip: `Peak Render Time` (fotograma y marca temporal), `Average Render` (con percentil `P95`), `Frame Drops` (conteo y porcentaje del clip excedido), `Peak Bitmap RAM` (con `Max Single`) y `Peak ASS Objects`.
   * **Lista de Puntos Críticos (*Critical Hotspots*):** Registro de los picos locales de mayor carga del efecto; al seleccionar un elemento, el cabezal de vídeo y el gráfico se posicionan en el fotograma correspondiente.
3. **Gráfico Superpuesto y Navegación 2D (Mitad Inferior):**
   * **Superposición de 4 Métricas y Multiplicadores de Escala ($1\times$ – $10\times$):** Curvas continuas de `Render Time (ms)`, `Total Bitmap RAM`, `Largest Bitmap` y `ASS Objects` junto a la cota horizontal del límite de presupuesto (`FPS Budget Limit`). Las métricas pueden alternarse individualmente y admiten multiplicadores de escala vertical (`1x`, `2x`, `5x`, `10x`).
   * **Navegación e Interacción:**
     * **`Rueda del Ratón`:** Zoom horizontal ($X$) centrado en la posición del cursor.
     * **`Ctrl + Rueda` / `Shift + Rueda`:** Ajuste de escala vertical ($Y$).
     * **`Botón Central + Arrastre`:** Desplazamiento bidimensional ($X$ e $Y$).
     * **`Clic Izquierdo + Arrastre`:** Desplazamiento temporal (*scrubbing*) sincronizado con el vídeo.
     * **`Tecla R` / `Home`:** Restablece la vista al $100\%$ del rango temporal.

> [!NOTE]
> **Ciclo de Vida Limpio por Sesión:** Tanto el gráfico del menú `Telemetry` como el mapa de calor térmico del `Previewer` inician completamente vacíos al abrir una nueva sesión o instanciar un nodo `Previewer`, poblándose únicamente con los datos reales obtenidos tras aplicar o refrescar el efecto actual.
