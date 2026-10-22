# Variables

La categoría **Variables** gestiona la introspección de métricas del entorno ASS, la inyección dinámica de identificadores locales evaluados en tiempo real y el almacenamiento persistente clave-valor entre ciclos de ejecución.

### Organización Temática del Volumen:
* **Sección 9.A — Fundamentos Arquitectónicos y Ciclo de Vida del Contexto:** Jerarquía matemática formal de tiempos, tiempos relativos al efecto ($ini$), anidamiento topológico DAG Trace y aislamiento de sub-iteradores.
* **Sección 9.B — Catálogo de Nodos de Variables:** [`Sys Var`](#1-nodo-variablessys-var-variables-del-sistema-y-contexto) (§1), [`Define Vars`](#2-nodo-variablesdefine-vars-definición-de-variables-locales) (§2), [`Get Var`](#3-nodo-variablesget-var-lector-de-variables-del-contexto) (§3), [`Memory`](#4-nodo-variablesmemory-memoria-persistente-clave-valor) (§4).
* **Sección 9.C — Matriz Comparativa, Tipificación de Propiedades y Buenas Prácticas:** Tabla comparativa (§5), tipificación de propiedades (Tipos A/B/C), resolución AST y optimización de memoria.

---

## Arquitectura de Variables y Ciclo de Vida del Contexto

En el grafo de Pyxis, la información contextual fluye jerárquicamente a través de cada nivel de iteración (`line` $\to$ `syl` $\to$ `word` $\to$ `char` $\to$ `sub-bucles`):

```
+─────────────────────────────────────────────────────────────────────────────+
|                         ENTORNO GLOBAL / PROYECTO                          |
|  meta.res_x, meta.res_y, frame_dur, default_audio_source, video_fps         |
+──────────────────────────────────────┬──────────────────────────────────────+
                                       │
                                       ▼
+─────────────────────────────────────────────────────────────────────────────+
|                          NIVEL DE LÍNEA (line / l)                          |
|  l.text, l.start_time, l.end_time, l.dur, l.style, l.layer, l.margin_*, ... |
+──────────────────────────────────────┬──────────────────────────────────────+
                                       │
                                       ▼
+─────────────────────────────────────────────────────────────────────────────+
|                   NIVEL DE UNIDAD ACTIVA (syl / word / char)                 |
|  syl.text, syl.x, syl.y, syl.dur, syl.left, syl.center, syl.i, syl.n, ...   |
+──────────────────────────────────────┬──────────────────────────────────────+
                                       │
                                       ▼
+─────────────────────────────────────────────────────────────────────────────+
|                        CADENA DE BUCLES / SUB-BUCLES                        |
|  fx.i, fx.n, fx.pos_x, fx.pos_y, fx.dur, j, maxj, s_i, a_i, p_i, ratio       |
+──────────────────┬──────────────────────────────────────┬───────────────────+
                   │                                      │
                   ▼                                      ▼
+──────────────────────────────────────+ +────────────────────────────────────+
|     LOCAL STATE (Define Vars)        | |    PERSISTENT STATE (Memory)       |
|  Variables temporales inyectadas     | |  Almacén clave-valor que perdura   |
|  válidas dentro del ciclo actual.    | |  a través de todos los ciclos.     |
+──────────────────────────────────────+ +────────────────────────────────────+
```

### 0.1. Jerarquía Matemática Formal de Tiempos

El formato ASS define las marcas de tiempo de las líneas generadas (`Dialogue`) en el espacio temporal global del vídeo. Sin embargo, las marcas de karaoke `\k` y las transformaciones cinemáticas `\t(t1, t2, tags)` operan en marcos temporales locales relativos al inicio de la línea física generada ($[0, \text{fx.dur}]$).

Pyxis modela esta jerarquía mediante cuatro niveles temporales acoplados:

| Entidad | Propiedades Canónicas | Base Matemática / Ámbito | Variables Relativas al Efecto ($ini = line.start\_time - fx.start\_time$) |
| :--- | :--- | :--- | :--- |
| **`line` / `l`** | `start_time`, `end_time`, `dur`, `mid_time` | **Global del Vídeo ($ms$)** | Referencia temporal absoluta del evento en el timeline. |
| **`syl`** | `start_time`, `end_time`, `dur`, `mid_time` | **Relativo a la Línea ($[0, line.dur]$)** | $syl.syl\_start = ini + syl.start\_time$<br>$syl.syl\_end = syl.syl\_start + syl.dur$<br>$syl.syl\_mid = syl.syl\_start + \frac{syl.dur}{2}$ |
| **`char`** | `start_time`, `end_time`, `dur`, `mid_time` | **Relativo a la Sílaba ($[0, syl.dur]$)** | $char.char\_start = syl.syl\_start + char.start\_time$<br>$char.char\_end = char.char\_start + char.dur$<br>$char.syl\_start = syl.syl\_start$<br>$char.syl\_end = syl.syl\_end$ |
| **`word`** | `start_time`, `end_time`, `dur`, `mid_time` | **Relativo a la Línea ($[0, line.dur]$)** | $word.word\_start = ini + word.start\_time$<br>$word.word\_end = word.word\_start + word.dur$ |
| **`fx`** | `start_time`, `end_time`, `dur` | **Global de la Línea Emitida en ASS** | Define el intervalo $[0, fx.dur]$ sobre el cual libass evalúa $\backslash\text{t}(t_1, t_2, \dots)$. |

#### Relación Algebraica del Desfase de Efecto ($ini$)
Dado un evento con inicio original $line.start\_time$ y un retardo de anticipación (*lead-in*) $\Delta t_{\text{leadin}}$ generado por nodos temporales (`Time/Lead In`, `Time/Retime`), la línea ASS de salida se inicia en:

$$fx.start\_time = line.start\_time - \Delta t_{\text{leadin}}$$

El desfase relativo $ini$ se define como:

$$ini = line.start\_time - fx.start\_time = \Delta t_{\text{leadin}}$$

Por tanto, un transform ASS `\t` aplicado a la sílaba durante su canto exacto utiliza los límites:

$$t_1 = syl.syl\_start = ini + syl.start\_time, \quad t_2 = syl.syl\_end = syl.syl\_start + syl.dur$$

### 0.2. Anidamiento Multidimensional de Sub-bucles (DAG Trace)

Cuando múltiples nodos generadores de piezas o partículas se conectan hacia `System/Output`, el motor resuelve las dependencias en tiempo de renderizado mediante una exploración en post-orden a través de los cables del grafo (**DAG Trace**):

```
                                              ┌───────────────────────────────┐
                                              │     System/Output (Terminal)  │
                                              └───────▲───────────────▲───────┘
                                                      │               │
                                 Canal Return:        │               │ Canal Tags:
                                 Geometría / Piezas   │               │ Modificadores
                                                      │               │
                                         ┌────────────┴───┐       ┌───┴──────────┐
                                         │ Functions/     │       │ Basics/      │
                                         │ Particles      │       │ MultiTag     │
                                         └────────────▲───┘       └──────────────┘
                                                      │
                                         ┌────────────┴───┐
                                         │ Shape/Slicer   │
                                         │ (Bucle Exterior)
                                         └────────────────┘
```

1. **Canal 1 (`Output.Return` — Puerto 5, Geometría):** Se rastrea recursivamente en post-orden desde la raíz *upstream* hasta el puerto `Return`. Si `Slicer` alimenta a `Particles` y este a `Return`, `Slicer` actúa como bucle exterior ($s_i \in [1, s_n]$) y `Particles` como bucle interior ($p_i \in [1, p_n]$ para cada pieza $s_i$).
2. **Canal 2 (`Output.Tags` — Puerto 4, Modificadores):** Se rastrea en post-orden respetando el orden de entradas (`In1`, `In2`, ...) y se evalúa anidado dentro de cada estado geométrico emitido por `Return`.

#### Aislamiento Canónico de Iteradores por Generador
Para evitar colisiones entre niveles de anidamiento, cada familia de generador mantiene su propio espacio de nombres aislado:

| Familia de Nodo Generador | Iterador Ordinal | Total de Unidades | Alias de Expresión |
| :--- | :---: | :---: | :--- |
| **`Shape/Slicer`** | `s_i` | `s_n`, `s_max` | `slice_i`, `slice_n`, `slice_max`, `col`, `row` |
| **`Shape/Union & Divide`** | `d_i` | `d_n`, `d_max` | `divide_i`, `divide_n`, `divide_max` |
| **`Shape/Concentric Borders`** | `b_i` | `b_n`, `b_max` | `ring_i`, `ring_n`, `ring_max` |
| **`Shape/Array`** | `a_i` | `a_n`, `a_max` | `array_i`, `array_n`, `array_max`, `col`, `row` |
| **`Shape/Multi`** | `m_i` | `m_n`, `m_max` | `multi_i`, `multi_n`, `multi_max` |
| **`Functions/Particles`** | `p_i` | `p_n`, `p_max` | `tp_i`, `tp_n`, `tp_max`, `text_p_i`, `text_p_n` |
| **`Functions/IMG to pixels`** | `ip_i` | `ip_n`, `ip_max` | `img_p_i`, `img_p_n`, `total_pixels` |
| **`Functions/Clip Gradient`** | `c_i` | `c_n`, `c_max` | `clip_i`, `clip_n`, `clip_max`, `c_col`, `c_row` |
| **`Functions/Animation`** | `an_i` | `an_n`, `an_max` | `anim_i`, `anim_n`, `anim_max`, `an_j` |
| **`Loops/MaxLoop`** | `j` | `maxj`, `maxloop` | `module`, `m`, `ratio` |

#### Poda Condicional Dinámica (*Context-Aware DAG Trace*)
Al rastrear la topología hacia aguas arriba, si el motor encuentra selectores o conmutadores condicionales (`Basics/Only`, `Functions/Conditioner`, `Basics/Once`), evalúa la condición booleana contra el contexto de iteración activo. El recorrido transita exclusivamente por la rama activa (`True` o `False`), podando la rama inactiva. Esto impide que generadores alternativos se multipliquen erróneamente en serie o que ramas inactivas ejecuten iteraciones fantasma.

---

## 1. Nodo `Variables/Sys Var` (Variables del Sistema y Contexto)

* **Categoría Canónica:** `Variables` (UI: *Variables / Sys Var*)
* **Propósito:** Inspecciona y extrae cualquier métrica nativa del contexto activo (coordenadas, dimensiones métricas en píxeles, tiempos en milisegundos, índices de iteración, propiedades tipográficas de estilos ASS, metadatos de resolución o dimensiones de geometrías vectoriales).

![Variables/Sys Var](img/sys_var.png)

> [!TIP]
> **Selector Interactivo de Variables (SysVar Grid Picker):**
> Al hacer clic o editar el campo **Variable**, se despliega automáticamente un modal interactivo con buscador en tiempo real y filtrado taxonómico por categorías (*Line*, *Syllable*, *Character*, *Word*, *Effect/FX*, *Loops/Globals*, *Temporal Offset*, *Ink Metrics*, *Meta/Project*, *Neighbors & Context*). Dentro de cada categoría, las variables se presentan ordenadas alfabéticamente para una localización inmediata y predecible, permitiendo seleccionar cualquier variable con un solo clic sin necesidad de escribirla manualmente.

---

### 1.1. Encabezado y Modos de Cabecera (*Header Mode Combos*)
El selector desplegable superior del nodo mapea directamente la propiedad `var_name`. Permite alternar con un solo clic entre las variables de contexto más frecuentes del sistema o escribir un identificador libre.

---

### 1.2. Puertos de Entrada y Propiedades del Cuerpo (*Inputs & Properties*)
1. **`Variable` (`var_name`):** Identificador canónico de la variable o ruta de propiedad a consultar (ej. `"syl.text"`, `"line.start_time"`, `"fx.pos_x"`, `"meta.res_x"`, `"shape.width"`). (Defecto: `"syl.text"`).
   * **Tipificación Canónica:** **Tipo C (Texto Plano / Identificador)**. Excluido estrictamente de `ast.parse` para evitar falsos positivos de sintaxis.
   * No requiere puertos de entrada; el valor se extrae directamente del contexto de ejecución enlazado.

---

### 1.3. Puertos de Salida (*Outputs*)
1. **`[1.1] Data`:** Valor escalar, cadena de texto o número flotante/entero correspondiente a la variable solicitada. Si la variable no existe en el contexto, emite una cadena vacía `""` o `0.0`.

---

### 1.4. Taxonomía Exhaustiva de Variables de Sistema Disponibles

A continuación se detalla la matriz canónica completa de variables accesibles mediante `Sys Var`, en el nodo `Define Vars`, en scripts de `Script Code` o en expresiones entre paréntesis `\tag(var)`:

#### 1.4.1. Dominio de Línea (`line.` o `l.`) e Información del Estilo Original
Representa la línea de diálogo activa y su estilo tipográfico asociado definido en el encabezado `[V4+ Styles]` del script ASS. Las propiedades tipográficas reflejan los valores del estilo base (`StyleRef`) o cualquier sobreescritura previa:

| Variable | Tipo | Descripción y Unidad |
| :--- | :---: | :--- |
| `line.text` / `l.text` | `string` | Texto de la línea ASS despojado de etiquetas de estilo y marcas de karaoke. |
| `line.raw_text` / `l.raw_text` | `string` | Texto original de la línea ASS conservando etiquetas `{\...}` y marcas `\k`. |
| `line.start_time` / `l.start_time` | `int` | Tiempo inicial de la línea en milisegundos ($ms$). |
| `line.end_time` / `l.end_time` | `int` | Tiempo final de la línea en milisegundos ($ms$). |
| `line.dur` / `line.duration` / `l.dur` | `int` | Duración neta de la línea en milisegundos: $t_{\text{end}} - t_{\text{start}}$. |
| `line.mid_time` / `l.mid_time` | `float` | Punto temporal medio de la línea: $t_{\text{start}} + \frac{t_{\text{dur}}}{2}$. |
| `line.i` / `l.i` | `int` | Índice ordinal de la línea activa en el lote procesado ($1 \dots N$). |
| `line.n` / `l.n` | `int` | Cantidad total de líneas seleccionadas en el lote. |
| `line.x`, `line.y` | `float` | Coordenadas cartesianas calculadas del centro de la línea en pantalla (px). |
| `line.left`, `line.right` | `float` | Límite horizontal izquierdo y derecho del cuadro delimitador (*Bounding Box*) de la línea (px). |
| `line.top`, `line.bottom` | `float` | Límite vertical superior e inferior del cuadro delimitador de la línea (px). |
| `line.middle`, `line.center` | `float` | Punto central vertical y horizontal de la línea completa (px). |
| `line.width`, `line.height` | `float` | Anchura y altura tipográfica calculada de la línea completa (px). |
| `line.descent`, `line.extlead` | `float` | Métricas tipográficas de descenso (*descent*) e interlineado adicional (*external leading*) de la fuente (px). |
| `line.layer` / `l.layer` | `int` | Número de capa ASS asignado a la línea (Z-order de renderizado). |
| `line.style` / `line.style_name` | `string` | Nombre del estilo ASS asociado a la línea (ej. `"Default"`, `"Romaji"`). |
| `line.actor` / `l.actor` | `string` | Campo de actor/personaje de la línea ASS. |
| `line.effect` / `l.effect` | `string` | Campo de efecto especial de la línea ASS. |
| `line.margin_l`, `line.margin_r`, `line.margin_v` | `int` | Márgenes izquierdo, derecho y vertical definidos en la línea o estilo (px). |
| `line.margin_t`, `line.margin_b` | `int` | Márgenes superior e inferior individuales (px). |
| `line.fontname` | `string` | Nombre de la familia tipográfica configurada en el estilo original (ej. `"Arial"`, `"Montserrat"`). |
| `line.fontsize` | `float` | Tamaño de fuente del estilo base en puntos/píxeles tipográficos ($pt$). |
| `line.bold` | `bool` | Indicador booleano de peso negrita definido en el estilo original (`True` / `False`). |
| `line.italic` | `bool` | Indicador booleano de estilo cursiva definido en el estilo original (`True` / `False`). |
| `line.underline` | `bool` | Indicador booleano de subrayado en el estilo original (`True` / `False`). |
| `line.strikeout` | `bool` | Indicador booleano de texto tachado en el estilo original (`True` / `False`). |
| `line.scale_x`, `line.scale_y` | `float` | Factores de escala tipográfica horizontal y vertical del estilo base en porcentaje ($100.0 = 100\%$). |
| `line.spacing` | `float` | Espaciado o interletreado (*tracking*) entre caracteres en píxeles (`\fsp`). |
| `line.outline` | `float` | Grosor del contorno o borde tipográfico configurado en el estilo original en píxeles (`\bord`). |
| `line.shadow` | `float` | Distancia o profundidad de la sombra arrojada en el estilo original en píxeles (`\shad`). |
| `line.align` | `int` | Alineación Numpad original del estilo base ($1 \dots 9$). |
| `line.color1` .. `line.color4` | `string` | Colores del estilo original: primario (`\1c`), karaoke/secundario (`\2c`), borde (`\3c`) y sombra (`\4c`) en formato ASS `&HBBGGRR&`. |
| `line.alpha1` .. `line.alpha4` | `string` | Canales alfa del estilo original correspondientes a los 4 componentes en formato ASS `&HAA&` ($0 \dots 255$). |
| `line.frz`, `line.frx`, `line.fry` | `float` | Ángulos de rotación 3D intrínsecos de la línea o estilo en grados sexagesimales. |
| `line.fax`, `line.fay` | `float` | Factores de deformación tipográfica por cizallamiento (*shear*) horizontal y vertical. |
| `line.pos_x`, `line.pos_y` | `float` | Posición horizontal y vertical absoluta o sobreescrita de la línea (`\pos`). |
| `line.org_x`, `line.org_y` | `float` | Coordenadas del punto de pivote o anclaje de rotación de la línea (`\org`). |

#### 1.4.2. Dominio de Sílaba (`syl.`), Carácter (`char.`) y Palabra (`word.`)
Representan las unidades atómicas silábicas, de caracteres individuales o palabras desglosadas por `Main Loop`. Cada unidad hereda automáticamente las propiedades tipográficas del estilo base de la línea contenedora o sus sobreescrituras activas:

| Variable | Tipo | Descripción y Unidad |
| :--- | :---: | :--- |
| `syl.text` / `word.text` / `char.text` | `string` | Texto del elemento despojado de etiquetas de estilo. |
| `syl.text_stripped` / `char.text_stripped` | `string` | Texto limpio de la unidad garantizando la omisión de cualquier código de escape. |
| `syl.text_spacestripped` | `string` | Texto de la sílaba despojado adicionalmente de espacios en blanco iniciales y finales. |
| `syl.dur` / `syl.duration` | `int` | Duración de la sílaba en milisegundos ($ms$) asignada por la marca de karaoke `\k`. |
| `syl.start_time`, `syl.end_time` | `int` | Tiempos de inicio y fin relativos a la **línea base** ($ms$). |
| `syl.mid_time` | `float` | Instante medio de la sílaba relativo a la línea: $t_{\text{start}} + \frac{t_{\text{dur}}}{2}$. |
| `syl.syl_start`, `syl.syl_end` | `int` | Tiempos de inicio y fin de la sílaba relativos al **efecto `fx`** ($\text{ini} + \text{syl.start\_time}$). |
| `syl.syl_mid` | `float` | Instante medio de la sílaba relativo al efecto `fx`. |
| `syl.i` / `syl.n` | `int` | Índice de la sílaba en la línea ($1 \dots N$) y total de sílabas. |
| `syl.x`, `syl.y` | `float` | Coordenadas cartesianas absolutas del centro de la sílaba en pantalla (px). |
| `syl.left`, `syl.right` | `float` | Coordenada $X$ izquierda y derecha del cuadro delimitador de la sílaba (px). |
| `syl.top`, `syl.bottom` | `float` | Coordenada $Y$ superior e inferior del cuadro delimitador de la sílaba (px). |
| `syl.center`, `syl.middle` | `float` | Centro horizontal $X$ y vertical $Y$ de la sílaba (px). |
| `syl.width`, `syl.height` | `float` | Dimensiones métricas calculadas de la sílaba (px). |
| `syl.descent`, `syl.descend` | `float` | Altura del descenso tipográfico de la fuente en la sílaba (px). |
| `syl.extlead` | `float` | Interlineado adicional externo de la fuente (px). |
| `syl.prespace`, `syl.postspace` | `string` | Caracteres de espacio en blanco previos o posteriores a la sílaba. |
| `syl.prespacewidth`, `syl.postspacewidth` | `float` | Ancho métrico de los espacios en blanco adyacentes (px). |
| `syl.fontname`, `syl.fontsize` | `string` / `float` | Familia tipográfica heredada del estilo y tamaño en puntos ($pt$). |
| `syl.bold`, `syl.italic` | `bool` | Banderas booleanas de negrita y cursiva heredadas del estilo. |
| `syl.underline`, `syl.strikeout` | `bool` | Banderas booleanas de subrayado y tachado heredadas del estilo. |
| `syl.scale_x`, `syl.scale_y` | `float` | Factores de escala tipográfica heredados ($100.0 = 100\%$). |
| `syl.spacing`, `syl.outline`, `syl.shadow` | `float` | Espaciado (`\fsp`), grosor de borde (`\bord`) y sombra (`\shad`) heredados (px). |
| `syl.color1` .. `syl.color4` | `string` | Colores primario, karaoke, borde y sombra asignados a la sílaba (`&HBBGGRR&`). |
| `syl.alpha1` .. `syl.alpha4` | `string` | Canales alfa primario, karaoke, borde y sombra asignados a la sílaba (`&HAA&`). |
| `syl.align` | `int` | Alineación Numpad activa ($1 \dots 9$). |
| `syl.pos_x`, `syl.pos_y` | `float` | Coordenada de renderizado o anclaje calculada para la sílaba (`\pos`). |
| `syl.org_x`, `syl.org_y` | `float` | Origen o centro de rotación calculado para la sílaba (`\org`). |
| `syl.actor`, `syl.style`, `syl.layer`, `syl.effect` | `str`/`int` | Metadatos heredados de la línea contenedora. |
| `char.dur` / `char.duration` | `int` | Duración calculada del carácter ($ms$). |
| `char.start_time`, `char.end_time` | `int` | Tiempos de inicio y fin relativos a su **sílaba contenedora** ($ms$). |
| `char.mid_time` | `float` | Instante medio del carácter relativo a su sílaba: $t_{\text{start}} + \frac{t_{\text{dur}}}{2}$. |
| `char.char_start`, `char.char_end` | `int` | Tiempos de inicio y fin del carácter relativos al **efecto `fx`** ($\text{syl.syl\_start} + \text{char.start\_time}$). |
| `char.syl_start`, `char.syl_end` | `int` | Tiempos de inicio y fin de la sílaba padre relativos al **efecto `fx`**. |
| `char.i` / `char.n` | `int` | Índice del carácter en la línea ($1 \dots N$) y total de caracteres de la línea. |
| `char.syl_i` | `int` | Índice ordinal del carácter dentro de su sílaba contenedora ($1 \dots N_{\text{syl}}$). |
| `char.word_i` | `int` | Índice ordinal del carácter dentro de su palabra contenedora. |
| `char.x`, `char.y` | `float` | Coordenadas cartesianas absolutas del centro del carácter en pantalla (px). |
| `char.center`, `char.middle` | `float` | Coordenadas centrales del carácter en pantalla (px). |
| `char.left`, `char.right`, `char.top`, `char.bottom` | `float` | Límites rectangulares del cuadro delimitador del carácter (px). |
| `char.width`, `char.height` | `float` | Dimensiones métricas calculadas del glifo del carácter (px). |
| `char.fontname`, `char.fontsize`, `char.color1`..`4` | `var` | Propiedades tipográficas y cromáticas completas heredadas para el carácter. |
| `word.dur` / `word.duration` | `int` | Duración total de la palabra ($ms$). |
| `word.start_time`, `word.end_time` | `int` | Tiempos de inicio y fin relativos a la **línea base** ($ms$). |
| `word.word_start`, `word.word_end` | `int` | Tiempos de inicio y fin relativos al **efecto `fx`** ($\text{ini} + \text{word.start\_time}$). |
| `word.i` / `word.n` | `int` | Índice de la palabra en la línea ($1 \dots N$) y total de palabras. |
| `word.x`, `word.y`, `word.center`, `word.middle` | `float` | Coordenadas espaciales del centro de la palabra (px). |
| `word.left`, `word.right`, `word.top`, `word.bottom` | `float` | Límites rectangulares del cuadro delimitador de la palabra (px). |
| `word.width`, `word.height` | `float` | Dimensiones métricas calculadas de la palabra completa (px). |

#### 1.4.3. Unidades Adyacentes y Banderas Relacionales (`prev.`, `next.`, `is_first`, `is_last`, `has_prev`, `has_next`)
Permiten introspección contextual sobre los elementos vecinos en la cadena de animación sin requerir memoria persistente adicional. Los objetos `prev` y `next` exponen todas las propiedades métricas, temporales y tipográficas del elemento adyacente:

| Variable | Tipo | Descripción |
| :--- | :---: | :--- |
| `prev.text`, `prev.text_stripped` | `string` | Texto del elemento previo en la secuencia. |
| `prev.x`, `prev.y`, `prev.center`, `prev.middle` | `float` | Coordenadas espaciales centrales del elemento anterior (px). |
| `prev.left`, `prev.right`, `prev.top`, `prev.bottom` | `float` | Límites del cuadro delimitador del elemento anterior (px). |
| `prev.width`, `prev.height` | `float` | Dimensiones métricas del elemento anterior (px). |
| `prev.start_time`, `prev.end_time`, `prev.dur` | `int` | Tiempos de inicio, fin y duración del elemento anterior ($ms$). |
| `prev.i`, `prev.n` | `int` | Índice y total correspondientes al elemento previo. |
| `prev.fontname`, `prev.fontsize`, `prev.color1`..`4` | `var` | Propiedades tipográficas y de estilo del elemento previo. |
| `next.*` | `var` | Mismas métricas y propiedades idénticas aplicadas al **siguiente elemento** de la secuencia. |
| `is_first` | `bool` | `True` si el elemento activo es el primero de la secuencia (`i == 1` o sin elemento previo). Accesible también como `syl.is_first`, `char.is_first`, `word.is_first`. |
| `is_last` | `bool` | `True` si el elemento activo es el último de la secuencia (`i == n` o sin elemento siguiente). Accesible también como `syl.is_last`, `char.is_last`, `word.is_last`. |
| `has_prev` | `bool` | `True` si existe una unidad precedente válida en la línea. |
| `has_next` | `bool` | `True` si existe una unidad sucesora válida en la línea. |

#### 1.4.4. Variables por Defecto de Pyxis, Entorno Global y Accesores Rápidos
Estas variables están inyectadas de forma nativa en el contexto de evaluación global de cada nodo (`Define Vars`, `MultiTag`, `Conditioner`, etc.), accesibles sin prefijos:

| Variable | Tipo | Descripción y Fórmula |
| :--- | :---: | :--- |
| `frame_dur` / `fd` | `float` | Duración exacta de un fotograma de vídeo en milisegundos ($\approx 41.67\text{ ms}$ a 23.976/24 FPS o $40.0\text{ ms}$ a 25 FPS). |
| `fps` | `float` | Tasa de fotogramas por segundo del vídeo activo en Aegisub (ej. `23.976`, `24.0`, `29.97`, `60.0`). |
| `ini` | `float` | Desfase temporal relativo de referencia entre la línea y el efecto: $\text{ini} = \text{line.start\_time} - \text{fx.start\_time}$. |
| `st`, `et` | `int` | Alias directos de alta velocidad para `start_time` y `end_time` activos ($ms$). |
| `dur` / `duration` | `int` | Duración neta de la unidad o fotograma activo en milisegundos ($ms$). |
| `time_start`, `time_end`, `time_dur` | `int` | Alias canónicos para instantes temporales del fotograma o sub-elemento. |
| `line_start_time`, `line_end_time`, `line_dur` | `int` | Tiempos de inicio, fin y duración de la línea contenedora ($ms$). |
| `syl_start_time`, `syl_end_time` | `int` | Tiempos de inicio y fin de la sílaba contenedora ($ms$). |
| `i`, `n` | `int` | Iterador ordinal ($1 \dots N$) y número total de unidades en el bucle principal. |
| `rx`, `ry` | `float` | Desplazamientos espaciales acumulados o relativos en los ejes $X$ e $Y$ (px). |
| `ratio` | `float` | Proporción de progreso temporal o modular activa. |
| `module` / `m` | `float` | Ratio normalizado de progreso del sub-bucle: $\text{module} = \frac{j - 1}{\text{maxj} - 1} \in [0.0, 1.0]$. |
| `pos_x`, `pos_y` | `float` | Coordenadas espaciales primarias calculadas para el elemento activo (px). |
| `center`, `middle` | `float` | Centro horizontal y vertical del elemento activo (px). |
| `left`, `right`, `top`, `bottom` | `float` | Coordenadas delimitadoras del elemento activo (px). |
| `width`, `height` | `float` | Anchura y altura del elemento activo (px). |
| `x`, `y` | `float` | Coordenadas cartesianas de referencia del elemento activo (px). |
| `result` | `string` | Variable de retorno estándar en el nodo `System/Script Code` para emitir el texto o tags hacia el pin `Result`. |

#### 1.4.5. Sub-Iteradores de Mallas, Partículas y Sub-bucles
Variables inyectadas dinámicamente cuando se conectan generadores iterativos al puerto `Return` de `System/Output`:

| Variable | Tipo | Generador y Descripción |
| :--- | :---: | :--- |
| `j`, `maxj`, `maxloop` | `int` | Contador ordinal ($1 \dots N$) y total de iteraciones configuradas en `Loops/MaxLoop`. |
| `s_i`, `s_n`, `s_max` | `int` | Índice de la pieza activa ($1 \dots N$) y total de piezas generadas por `Shape/Slicer`. |
| `slice_i`, `slice_n`, `slice_max` | `int` | Alias canónicos de `s_i` y `s_n` para compatibilidad en expresiones. |
| `col`, `row` | `int` | Coordenadas espaciales de columna y fila en segmentaciones matriciales (`Slicer`, `Array`). |
| `a_i`, `a_n` | `int` | Índice ordinal de la partícula activa y total de elementos en matrices de `Shape/Array`. |
| `p_i`, `p_n` | `int` | Índice ordinal y recuento total de partículas en enjambres de `Functions/Particles`. |
| `c_i`, `c_n`, `c_max` | `int` | Índice ordinal y recuento total de cortes en gradientes de `Functions/Clip Gradient`. |
| `clip_i`, `clip_n`, `clip_max` | `int` | Alias canónicos de `c_i` y `c_n` en `Functions/Clip Gradient`. |
| `d_i`, `d_n` | `int` | Índice ordinal y recuento de fragmentos en particiones de `Shape/Union & Divide`. |

#### 1.4.6. Accesores Rápidos Prefijados (`val_*`)
Proporcionan acceso directo, desacoplado y optimizado a las métricas del elemento en curso en expresiones matemáticas y `Sys Var`:

| Variable | Tipo | Métrica Equivalente |
| :--- | :---: | :--- |
| `val_x`, `val_y` | `float` | Coordenadas cartesianas de la unidad activa (`active_unit.x`, `active_unit.y`). |
| `val_left`, `val_right` | `float` | Límite horizontal izquierdo y derecho (`active_unit.left`, `active_unit.right`). |
| `val_top`, `val_bottom` | `float` | Límite vertical superior e inferior (`active_unit.top`, `active_unit.bottom`). |
| `val_center`, `val_middle` | `float` | Centro horizontal y vertical (`active_unit.center`, `active_unit.middle`). |
| `val_width`, `val_height` | `float` | Dimensiones métricas (`active_unit.width`, `active_unit.height`). |
| `val_start` / `val_st` | `float` | Instante inicial en milisegundos (`active_unit.start_time`). |
| `val_end` / `val_et` | `float` | Instante final en milisegundos (`active_unit.end_time`). |
| `val_dur` | `float` | Duración neta en milisegundos (`active_unit.duration`). |
| `val_mid` | `float` | Instante medio de la unidad activa: $t_{\text{start}} + \frac{t_{\text{dur}}}{2}$. |
| `val_i`, `val_n` | `int` | Índice ordinal y total de unidades del elemento activo. |

#### 1.4.7. Sincronización Temporal Inter-Línea (`sync.*`)
El subsistema `sync` calcula la separación temporal o desfase con las líneas adyacentes del diálogo en milisegundos, permitiendo crear animaciones de entrada anticipadas antes de que empiece la línea o transiciones fluidas sin colisiones:

| Variable | Tipo | Criterio de Búsqueda y Descripción |
| :--- | :---: | :--- |
| `sync.next` / `sync.prev` | `float` | Hueco temporal en milisegundos con la siguiente o anterior línea según el orden cronológico estándar (acotado a `max_gap`, 2000 ms por defecto). |
| `sync.order_next`, `sync.order_prev` | `float` | Hueco con la línea inmediatamente contigua en el orden físico de las líneas del archivo ASS. |
| `sync.style_next`, `sync.style_prev` | `float` | Hueco con la siguiente o anterior línea que posea **el mismo estilo tipográfico**. |
| `sync.actor_next`, `sync.actor_prev` | `float` | Hueco con la siguiente o anterior línea que comparta **el mismo actor/personaje**. |
| `sync.effect_next`, `sync.effect_prev` | `float` | Hueco con la siguiente o anterior línea que posea **el mismo campo de efecto**. |
| `sync.layer_next`, `sync.layer_prev` | `float` | Hueco con la siguiente o anterior línea situada en **la misma capa ASS**. |

> [!NOTE]
> **Interpretación de Signos en `sync`:**
> * Un valor **positivo ($> 0$)** indica una pausa o silencio entre ambas líneas (ej. $+850\text{ ms}$).
> * Un valor **negativo ($< 0$)** indica que las dos líneas se solapan simultáneamente en el tiempo (*overlap*).

#### 1.4.8. Temporizadores y Modificadores Integrados (`time.*`)
Permiten calcular retardos y fases de animación secuenciales directamente desde expresiones o mediante `Sys Var`:

| Variable | Tipo | Función Cinemática |
| :--- | :---: | :--- |
| `time.lead_in` | `int` | Retardo previo acumulado por sílaba para animaciones de entrada anticipada (*lead-in*). |
| `time.lead_out` | `int` | Retardo posterior acumulado por sílaba para animaciones de salida (*lead-out*). |
| `time.middle_1` | `int` | Retardo temporal simétrico calculado desde el centro de la línea hacia los extremos. |
| `time.middle_2` | `int` | Retardo temporal simétrico calculado desde los extremos de la línea hacia el centro. |
| `time.loop_1` | `int` | Temporización para bucles cíclicos continuos en la fase de entrada. |
| `time.loop_2` | `int` | Temporización para bucles cíclicos continuos en la fase de salida. |

#### 1.4.9. Presets de la Biblioteca de Formas Vectoriales (`shape.*`)
El espacio de nombres `shape` contiene los trazados vectoriales estándar de Pyxis en formato ASSdraw (`m ... l ... b ...`), accesibles directamente para clips, transformaciones o expresiones en código:

| Preset | Identificador Canónico | Geometría Emitida |
| :--- | :--- | :--- |
| **Círculo** | `shape.circle` | Círculo Bézier perfecto normalizado centrado en $(0, 0)$. |
| **Cuadrado** | `shape.square` | Cuadrado equilátero centrado en $(0, 0)$. |
| **Rectángulo** | `shape.rect` / `shape.rectangle` | Rectángulo paramétrico centrado en $(0, 0)$. |
| **Triángulo** | `shape.triangle` | Triángulo equilátero con vértice superior en $(0, 0)$. |
| **Rombo** | `shape.diamond` / `shape.rhombus` | Rombo geométrico en diamante centrado en $(0, 0)$. |
| **Esquinas Redondeadas** | `shape.rounded_corners` | Rectángulo con fileteado y curvatura Bézier en las 4 esquinas. |
| **Polígonos Regulares** | `shape.pentagon`, `shape.hexagon`, `shape.octagon` | Polígonos regulares equiláteros de 5, 6 y 8 lados. |
| **Estrella** | `shape.star` | Estrella simétrica de 5 puntas. |
| **Corazón** | `shape.heart` | Trazado vectorial de corazón bicúbico centrado. |
| **Sakura** | `shape.sakura` | Pétalo estilizado de flor de cerezo japonés. |
| **Símbolos y Clima** | `shape.cross`, `shape.cloud`, `shape.sun`, `shape.moon`, `shape.flower` | Iconografía vectorial clásica para efectos de partículas. |

#### 1.4.10. Metadatos del Proyecto (`meta.`) y Formas del Contexto
| Variable | Tipo | Descripción |
| :--- | :---: | :--- |
| `meta.res_x`, `meta.res_y` | `int` | Resolución de renderizado del script ASS (`PlayResX`, `PlayResY`, ej. `1280`, `720` o `1920`, `1080`). |
| `shape.width`, `shape.height` | `float` | Anchura y altura en píxeles del trazado vectorial evaluado en el contexto. |
| `shape.left`, `shape.right` | `float` | Límite horizontal mínimo y máximo del trazado vectorial. |
| `shape.top`, `shape.bottom` | `float` | Límite vertical superior e inferior del trazado vectorial. |
| `shape.center_x`, `shape.center_y` | `float` | Centroide geométrico del trazado vectorial: $(\frac{\text{left} + \text{right}}{2}, \frac{\text{top} + \text{bottom}}{2})$. |

#### 1.4.11. Métricas de Tinta Real (`ink.`, `l.ink.`, `syl.ink.`, `char.ink.`, `word.ink.`)
A diferencia de las métricas tipográficas estándar (que calculan la caja delimitadora o *bounding box* tipográfica incluyendo espacios laterales y métricas de fuente), el subsistema **Ink Metrics** analiza los contornos vectoriales reales de los glifos (*visual ink bounds*):

| Variable | Tipo | Descripción |
| :--- | :---: | :--- |
| `ink.width`, `ink.height` | `float` | Anchura y altura neta del dibujo/trazado del elemento activo (px). |
| `ink.left`, `ink.right` | `float` | Límite horizontal izquierdo y derecho de los píxeles de tinta en pantalla (px). |
| `ink.top`, `ink.bottom` | `float` | Límite vertical superior e inferior de los píxeles de tinta en pantalla (px). |
| `ink.center`, `ink.middle` / `ink.x`, `ink.y` | `float` | Centro visual horizontal y vertical exacto de la tinta renderizada (px). |
| `ink.l.*` / `l.ink.*` | `float` | Métricas de tinta completas de la línea de diálogo. |
| `ink.syl.*` / `syl.ink.*` | `float` | Métricas de tinta completas de la sílaba activa. |
| `ink.char.*` / `char.ink.*` | `float` | Métricas de tinta completas del carácter activo. |
| `ink.word.*` / `word.ink.*` | `float` | Métricas de tinta completas de la palabra activa. |

---

### 1.5. Pipeline de Resolución y Precedencia en el Motor

Cuando `Sys Var` o el evaluador de expresiones inspecciona un identificador $V$, ejecuta la siguiente cascada determinista de búsqueda:

```
                  ┌───────────────────────────────┐
                  │   ¿Comienza por 'sync.'?      │ ──► [Sí] ──► Consulta de desfase inter-línea
                  └──────────────┬────────────────┘
                                 │ [No]
                  ┌──────────────▼────────────────┐
                  │    ¿Comienza por 'ink.'?      │ ──► [Sí] ──► Inspección de contornos vectoriales reales
                  └──────────────┬────────────────┘
                                 │ [No]
                  ┌──────────────▼────────────────┐
                  │ ¿Es 'is_first' / 'is_last' /  │ ──► [Sí] ──► Banderas de posición topológica relativa
                  │    'has_prev' / 'has_next'?   │
                  └──────────────┬────────────────┘
                                 │ [No]
                  ┌──────────────▼────────────────┐
                  │ ¿Prefijo 'prev.' o 'next.'?   │ ──► [Sí] ──► Métricas y estilo de unidad contigua
                  └──────────────┬────────────────┘
                                 │ [No]
                  ┌──────────────▼────────────────┐
                  │   ¿Comienza por 'shape.'?     │ ──► [Sí] ──► Presets vectoriales normalizados
                  └──────────────┬────────────────┘
                                 │ [No]
                  ┌──────────────▼────────────────┐
                  │ ¿Es 'frame_dur' o 'ratio'?    │ ──► [Sí] ──► Métrica temporal global o modular activa
                  └──────────────┬────────────────┘
                                 │ [No]
                  ┌──────────────▼────────────────┐
                  │    ¿Comienza por 'val_'?      │ ──► [Sí] ──► Mapeo escalar directo de la unidad activa
                  └──────────────┬────────────────┘
                                 │ [No]
                  ┌──────────────▼────────────────┐
                  │  ¿Prefijo 'fx.' o 'time.'?    │ ──► [Sí] ──► Desfases cinemáticos y temporizadores
                  └──────────────┬────────────────┘
                                 │ [No]
                  ┌──────────────▼────────────────┐
                  │ ¿Prefijo 'line.' / 'syl.' /   │ ──► [Sí] ──► Introspección jerárquica de elementos
                  │        'char.' / 'word.'?     │              y propiedades tipográficas del estilo base
                  └──────────────┬────────────────┘
                                 │ [No]
                  ┌──────────────▼────────────────┐
                  │ ¿Existe en context o meta?    │ ──► [Sí] ──► Identificador de usuario o meta de resolución
                  └──────────────┬────────────────┘
                                 │ [No]
                                 ▼
                         Retorna cadena vacía ("")
```

---

### 1.6. Ejemplo de Producción Verificado

Extracción de coordenadas métricas del glifo y duración nativa para posicionar una sílaba y generar una pulsación de escala durante su canto:

```
[Sys Var (var_name: syl.x)]   ──► [In1] ──┐
[Sys Var (var_name: syl.y)]   ──► [In2] ──┼──► [Dynamic Format] ──► Output.Tags
[Sys Var (var_name: syl.dur)] ──► [In3] ──┘
```

* **Plantilla en `Dynamic Format`:**
  ```text
  {\an5\pos(%s, %s)\t(0, %s, \fscx125\fscy125\1c&H00FFFF&)}
  ```
* **Línea ASS compilada resultante:**
  ```ass
  Dialogue: 0,0:01:12.40,0:01:15.80,Romaji,,0,0,0,,{\an5\pos(412.5, 680.0)\t(0, 320, \fscx125\fscy125\1c&H00FFFF&)}Ka
  ```

---

## 2. Nodo `Variables/Define Vars` (Definición de Variables Locales)

* **Categoría Canónica:** `Variables` (UI: *Variables / Define Vars*)
* **Propósito:** Permite declarar e inyectar un conjunto de variables locales personalizadas evaluadas en tiempo real para cada iteración del grafo. Facilita la creación de cálculos intermedios reutilizables, simplificando expresiones complejas sin sobrecargar la estructura de cables.

![Variables/Define Vars](img/define_vars.png)

---

### 2.1. Encabezado y Modos Operativos
`Define Vars` opera de forma universal tanto como un **nodo de flujo de datos (*pass-through*)** como un **eslabón en la cadena de bucles (*loop chain node*)**. Al hacer clic sobre el área de texto, se abre un editor multilínea con resaltado de sintaxis donde se pueden escribir múltiples asignaciones separadas por saltos de línea.

---

### 2.2. Puertos de Entrada y Propiedades del Cuerpo (*Inputs & Properties*)
1. **`In` (`in_val`):** Entrada de paso (*pass-through*). Puede recibir cualquier tipo de dato (cadenas de tags ASS, geometrías vectoriales, números o cadenas de texto). Si no está conectado, emite el contenido declarado o una cadena vacía.
2. **`Vars` (`variables`):** Bloque de texto multilínea con declaraciones de variables en formato `clave = expresión`.
   * **Tipificación Canónica:** **Tipo A (Fórmula Matemática / Expresión Evaluada)**. Evaluado secuencialmente línea a línea en el entorno del evaluador de expresiones matemáticas.
   * **Sintaxis de Declaración:**
     ```python
     radio = 50 + (syl.i * 10)
     angulo = (j / maxj) * 360
     pos_x = syl.x + math.cos(math.radians(angulo)) * radio
     pos_y = syl.y + math.sin(math.radians(angulo)) * radio
     color_actual = "&H00FFFF&"
     ```

---

### 2.3. Puertos de Salida (*Outputs*)
1. **`[1.1] Out`:** Emite de forma transparente el dato recibido en la entrada `In` (*pass-through*), habiendo inyectado previamente las variables definidas en el diccionario del contexto de ejecución.

#### Efecto en el Contexto de Ejecución:
Todas las variables asignadas en `Vars` quedan registradas inmediatamente en el contexto bajo sus nombres asignados (`radio`, `angulo`, `pos_x`, etc.), quedando disponibles para:
* Nodos `Variables/Get Var`.
* Nodos `Basics/Dynamic Format` o `Basics/Math`.
* Expresiones entre paréntesis `\tag(variable)` en cadenas de texto y plantillas de tags ASS.

> [!NOTE]
> **Re-evaluación Automática con Iteradores de Retorno (*Return Iterators*):**
> Cuando un nodo conectado al puerto `Return` de `System/Output` (como `Shape/Slicer`, `Shape/Array`, `Functions/Particles`, `Functions/IMG to pixels`) genera sub-iteraciones internas (`s_i`, `a_i`, `p_i`, `d_i`, etc.), Pyxis re-evalúa automáticamente todas las variables activas de `Define Vars` para cada pieza o partícula antes de evaluar las etiquetas conectadas al puerto `Tags`. Esto garantiza que llamadas como `by.s_i.R(-30, 30)` o expresiones dependientes de `s_i` se resuelvan con el valor exacto de la pieza activa y no con el valor estático del bucle exterior. Además, las definiciones se encuentran estrictamente aisladas por cola de salida (*Queue Isolation*), impidiendo colisiones entre múltiples nodos `Output`.

---

### 2.4. Sinergia de Inyección en Expresiones

```
                    +---------------------------+
                    | Loops/Main Loop (syl)     |
                    +-------------┬-------------+
                                  │
                                  ▼
                    +---------------------------+
                    | Variables/Define Vars     |
                    |   offset_x = syl.i * 12   |
                    |   rot = by.s_i.R(-20, 20) |
                    +-------------┬-------------+
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
      +---------------------------+ +---------------------------+
      | Variables/Get Var         | | Basics/Dynamic Format     |
      |   var_name: rot           | |   \frz(rot)\fscx(110)     |
      +---------------------------+ +---------------------------+
```

---

### 2.5. Ejemplo de Producción Verificado

Definición de traslación orbital sinusoidal y rotación angular por pieza de `Shape/Slicer`:

* **Declaraciones en `Define Vars` (`variables`):**
  ```python
  radio = 18 + (syl.i * 4)
  angulo = (s_i / s_n) * 360
  pos_x = syl.x + math.cos(math.radians(angulo)) * radio
  pos_y = syl.y + math.sin(math.radians(angulo)) * radio
  rot = (s_i / s_n) * 180
  ```
* **Tag ASS emitido mediante `Basics/Dynamic Format` hacia `Output.Tags`:**
  ```text
  \pos(pos_x, pos_y)\frz(rot)\t(0, syl.dur, \alpha&HFF&)
  ```
* **Línea ASS compilada resultante:**
  ```ass
  Dialogue: 0,0:01:12.40,0:01:15.80,Romaji,,0,0,0,,{\pos(425.2, 672.8)\frz(22.5)\t(0, 320, \alpha&HFF&)}Ka
  ```

---

## 3. Nodo `Variables/Get Var` (Lector de Variables del Contexto)

* **Categoría Canónica:** `Variables` (UI: *Variables / Get Var*)
* **Propósito:** Recupera y emite el valor actual de cualquier variable almacenada en el contexto de ejecución por su nombre literal. Permite desacoplar cables cruzados extensos en el lienzo y leer contadores o variables inyectadas dinámicamente.

![Variables/Get Var](img/get_var.png)

---

### 3.1. Encabezado y Modos Operativos
Diseñado para lectura puntual de alta velocidad. No requiere puertos de entrada y se resuelve en $\mathcal{O}(1)$ mediante acceso directo a la tabla hash del contexto.

---

### 3.2. Puertos de Entrada y Propiedades del Cuerpo (*Inputs & Properties*)
1. **`Name` (`var_name`):** Nombre de la variable a consultar (ej. `"j"`, `"maxj"`, `"module"`, `"custom_val"`, `"offset_x"`). (Defecto: `"j"`).
   * **Tipificación Canónica:** **Tipo C (Texto Plano / Identificador)**. Excluido estrictamente de `ast.parse`.

---

### 3.3. Puertos de Salida (*Outputs*)
1. **`[1.1] Data`:** Valor extraído del contexto. Si la variable no ha sido definida previamente o no existe en el contexto activo, emite una cadena vacía `""`.

---

### 3.4. Casos de Uso Frecuentes de `Get Var`
* **Lectura de Sub-Iteradores:** Extracción directa de contadores secundarios de bucle (`j`, `maxj`, `module`) generados por `Loops/MaxLoop` para alimentar nodos de interpolación o transformaciones afines.
* **Extracción de Variables Inyectadas:** Lectura de resultados calculados por `Variables/Define Vars` o scripts en `System/Script Code`.
* **Desacoplamiento de Cables (*Wireless Routing*):** Evita el enrutamiento complejo de cables a través de grafos extensos cuando un mismo parámetro debe alimentar múltiples ramas periféricas.

---

### 3.5. Ejemplo de Producción Verificado

Extracción desacoplada del iterador `j` de `Loops/MaxLoop` para modular la opacidad y escala de capas duplicadas:

* **Conexión en el Grafo:**
  ```
  [Loops/MaxLoop (iterations: 4)]
  [Variables/Get Var (var_name: "j")] ──► [In1] ──► [Dynamic Format] ──► Output.Tags
  ```
* **Plantilla en `Dynamic Format`:**
  ```text
  {\pos(syl.x, syl.y)\fscx(%s)\fscy(%s)\alpha(%s)}
  ```
* **Línea ASS compilada resultante (para iteración $j = 3$):**
  ```ass
  Dialogue: 0,0:01:12.40,0:01:15.80,Romaji,,0,0,0,,{\pos(412.5, 680.0)\fscx145\fscy145\alpha&H60&}Ka
  ```

---

## 4. Nodo `Variables/Memory` (Memoria Persistente Clave-Valor)

* **Categoría Canónica:** `Variables` (UI: *Variables / Memory*)
* **Propósito:** Proporciona almacenamiento persistente de variables (*State Retention*) a lo largo de toda la sesión de evaluación del grafo. A diferencia de las variables de contexto ordinarias (que se reinician o reasignan en cada nueva sílaba, línea o fotograma), `Memory` preserva sus valores entre ciclos consecutivos, permitiendo construir acumuladores cinemáticos, integradores de trayectoria física, registros de valores extremos ($\min / \max$) y banderas condicionales (*latches*).

![Variables/Memory](img/memory.png)

---

### 4.1. Encabezado y Modos Operativos (*Header Mode Combos*)
1. **`remember` (`save` / `SAVE`):** Modo de escritura y actualización. Almacena el dato recibido en la clave especificada de la memoria global y lo emite inmediatamente hacia la salida para permitir encadenamiento continuo.
2. **`retrieve` (`load` / `LOAD`):** Modo de lectura. Consulta el valor actualmente registrado bajo la clave indicada. Si la clave aún no ha sido inicializada en la sesión, emite el valor predeterminado configurado en `Value / Default`.

---

### 4.2. Puertos de Entrada y Propiedades del Cuerpo (*Inputs & Properties*)
1. **`Key` (`key`):** Identificador o clave textual bajo la cual se almacena el dato (ej. `"prev_x"`, `"accum_rot"`, `"max_width"`).
   * **Tipificación Canónica:** **Tipo C (Texto Plano / Identificador)**. Excluido estrictamente de `ast.parse`.
   * *Precedencia:* Cable conectado $\to$ Campo inline de texto $\to$ Defecto `"ref"`.
2. **`Value` (`value` / `default`):**
   * En modo `remember`: Dato a escribir en la memoria persistente.
   * En modo `retrieve`: Valor de reserva (*fallback / default*) emitido si la clave aún no existe en el almacén.
   * **Tipificación Canónica:** **Tipo A / Tipo C polimórfico** (números escalares, coordenadas, cadenas o vectores).
   * *Precedencia:* Cable conectado $\to$ Campo inline de texto $\to$ Cadena vacía `""`.

---

### 4.3. Puertos de Salida (*Outputs*)
1. **`[1.1] Data`:**
   * En modo `remember`: Emite el mismo valor recién almacenado (modo *pass-through* de escritura).
   * En modo `retrieve`: Emite el valor recuperado de la memoria persistente (o el valor `default` si la clave no fue encontrada).

---

### 4.4. Modelo de Persistencia y Ecuaciones Cinemáticas Acumulativas

El motor de ejecución mantiene un almacén persistente $\mathcal{M} = \{\text{key} \mapsto \text{value}\}$ asociado al ciclo de vida completo de la sesión de renderizado.

#### 4.4.1. Acumulador de Posición / Desplazamiento Acumulado
Para generar una trayectoria donde cada sílaba $i$ comienza en la posición terminal de la sílaba anterior $i-1$:

$$\text{pos}_x(i) = \text{retrieve}(\text{"last\_x"}, \text{default} = X_0) + \Delta x_i$$
$$\text{remember}(\text{"last\_x"}, \text{pos}_x(i))$$

```
                               Ciclo Sílaba i-1                        Ciclo Sílaba i
                         ┌───────────────────────────┐           ┌───────────────────────────┐
                         │ Memory (remember)         │           │ Memory (retrieve)         │
                         │   key: "pos_x"            │           │   key: "pos_x"            │
                         │   val: 320.5 px           │           │   val => 320.5 px         │
                         └─────────────┬─────────────┘           └─────────────┬─────────────┘
                                       │                                       │
                                       ▼                                       ▼
                         ┌───────────────────────────────────────────────────────────┐
                         │             Almacén Global Persistente (_memory)             │
                         │                   {"pos_x": 320.5}                        │
                         └───────────────────────────────────────────────────────────┘
```

#### 4.4.2. Integrador de Velocidad y Gravedad
En simulaciones de partículas y física discreta con sub-bucles `MaxLoop`:

$$v_y(j) = \text{retrieve}(\text{"vel\_y"}, 0.0) + g \cdot \Delta t$$
$$y(j) = \text{retrieve}(\text{"pos\_y"}, Y_0) + v_y(j) \cdot \Delta t$$
$$\text{remember}(\text{"vel\_y"}, v_y(j)) \quad \land \quad \text{remember}(\text{"pos\_y"}, y(j))$$

Donde $g$ representa la constante de aceleración gravitatoria y $\Delta t$ el paso de integración temporal en milisegundos.

---

### 4.5. Sinergias y Buenas Prácticas de Producción

1. **Patrón de Reinicio Estocástico con `Basics/Once`:**
   Al implementar acumuladores cinemáticos inter-línea, es recomendable encadenar un nodo `Basics/Once` para reescribir la memoria al inicio de cada línea (`mode: line`), evitando que los datos residuales de la línea previa contaminen el siguiente evento:
   ```
   [Basics/Once (line)] ──► [Variables/Memory (remember: "accum_x" = 0.0)]
   ```

2. **Detección de Valores Máximos y Cuadros Delimitadores Combinados:**
   Para calcular dinámicamente la anchura máxima de un grupo de glifos en tiempo real:
   ```
   [Math (max: syl.width, Memory.retrieve("max_w", 0))] ──► [Memory (remember: "max_w")]
   ```

3. **Comunicación Cruzada entre Subgrafos Asíncronos:**
   Permite que un subgrafo de cálculo tipográfico guarde parámetros de escala o color en memoria para que un subgrafo posterior de partículas o resplandor los lea sin requerir conexiones complejas de cables a lo largo del lienzo.

---

### 4.6. Ejemplo de Producción Verificado

Acumulador cinemático horizontal entre sílabas en una línea para recrear espaciado dinámico continuo:

* **Conexión en el Grafo:**
  ```
  [Basics/Once (line)] ──► [Memory (mode: remember, key: "last_x", value: line.left)]
  [Memory (mode: retrieve, key: "last_x", default: line.left)] ──► [Math (+ syl.width + 10)] ──► [Memory (mode: remember, key: "last_x")]
  ```
* **Línea ASS compilada resultante:**
  ```ass
  Dialogue: 0,0:01:12.40,0:01:15.80,Romaji,,0,0,0,,{\an7\pos(384.0, 680.0)}Ka
  Dialogue: 0,0:01:12.40,0:01:15.80,Romaji,,0,0,0,,{\an7\pos(424.0, 680.0)}ra
  Dialogue: 0,0:01:12.40,0:01:15.80,Romaji,,0,0,0,,{\an7\pos(462.5, 680.0)}o
  ```

---

## 5. Matriz Comparativa de Nodos de Variables y Almacenamiento

| Nodo | Modo Operativo | Ámbito de Vida (*Scope*) | Complejidad | Comportamiento ante Clave Ausente | Tipificación de Propiedades | Caso de Uso Primario |
| :--- | :--- | :--- | :---: | :--- | :---: | :--- |
| **`Sys Var`** | Consulta de entorno | Solo lectura (Nativo ASS) | $\mathcal{O}(1)$ | Emite cadena vacía `""` | Tipo C (`var_name`) | Extracción de métricas de sílaba, línea, resolución y tiempos. |
| **`Define Vars`** | Inyección local | Ciclo / Iteración actual | $\mathcal{O}(K)$ | Asigna `val_expr` literal si falla | Tipo A (`variables`) | Declaración de variables intermedias y expresiones matemáticas. |
| **`Get Var`** | Lectura dinámica | Contexto activo | $\mathcal{O}(1)$ | Emite cadena vacía `""` | Tipo C (`var_name`) | Lectura rápida desacoplada de variables y contadores `j`. |
| **`Memory`** | Escritura / Lectura | Persistente (Toda la sesión) | $\mathcal{O}(1)$ | Emite valor `default` configurado | Tipo C (`key`), Tipo A/C (`value`) | Acumuladores físicos, cinemática iterativa y conservación de estado. |

---

## 6. Tipificación Canónica de Propiedades (Tipos A, B y C) y Resolución AST

Toda propiedad de tipo cadena en Pyxis se clasifica estrictamente en una de tres categorías canónicas, coordinando el motor de ejecución, el evaluador de cadenas y el validador estático:

### 6.1. Propiedades de Tipo A: Fórmulas Matemáticas y Expresiones AST

* **Comportamiento en Runtime:** Evaluadas numéricamente línea por línea mediante el motor de expresiones de Python. Soportan:
  * Operadores aritméticos estándar: `+`, `-`, `*`, `/`, `//`, `%`, `**`.
  * Expresiones condicionales ternarias: `valor_a if condicion else valor_b`.
  * Funciones de la librería matemática estándar: `math.sin()`, `math.cos()`, `math.radians()`, `math.sqrt()`, `abs()`, `min()`, `max()`, `round()`.
  * Funciones estocásticas deterministas acopladas a iteradores: `by.<iter>.R(min, max)`, `by.syl.R(min, max)`, `R()`, `Rm()`.
* **Comportamiento en Linter:** Analizadas estáticamente mediante `ast.parse(mode="eval")`. El validador comprueba que los identificadores utilizados pertenezcan al conjunto de variables globales conocidas o hayan sido definidos previamente en el grafo, advirtiendo sobre variables no declaradas o sintaxis rota.
* **Propiedades Representativas:**
  * `Variables/Define Vars`: propiedad `variables` (`Vars`).
  * `Basics/Math`: entradas y campos numéricos `A`, `B`.
  * `Functions/Conditioner`: campo `condition`.
  * `Basics/Only`: campo `condition`.
  * `Shape/Filter`: campos `expr_x`, `expr_y`.

### 6.2. Propiedades de Tipo B: Plantillas de Tags ASS y Macros

* **Comportamiento en Runtime:** Procesadas secuencialmente por el evaluador de cadenas (`string_evaluator.py`). Realizan:
  * Sustitución e interpolación de variables entre paréntesis en tags ASS: `\pos(syl.x, syl.y)`, `\frz(rot)`, `\fscxy(escala)`.
  * Resolución de atajos temporales de animación: modificadores de tiempo (`2li`, `3lo`, `1m1`) y números de fotograma (`10f`).
  * Expansión de Dark Tags (`~`, `\tagR(...)`).
  * Las subexpresiones aritméticas contenidas dentro de los paréntesis `\tag(subexpr)` se desvían internamente al evaluador de Tipo A.
* **Comportamiento en Linter:** Inspeccionadas mediante validación de sintaxis de tags ASS (`_validate_tags`), verificando paridad de delimitadores (`{`, `}`, `(`, `)`), número de argumentos requeridos por cada tag ASS y delegando las subexpresiones numéricas a la regla de Tipo A.
* **Propiedades Representativas:**
  * `Basics/Dynamic Format`: campo `format`.
  * `System/Output`: entradas `Tags` y `Return`.
  * `Basics/MultiTag`: campos de prefijo y sufijo de tags.

### 6.3. Propiedades de Tipo C: Texto Plano, Identificadores y Pass-Through

* **Comportamiento en Runtime:** Tratadas como cadenas de texto literales sin análisis de expresiones ni despiece sintáctico.
* **Comportamiento en Linter:** Se valida únicamente el equilibrio básico de paréntesis y llaves para evitar roturas tipográficas en Aegisub. **Están excluidas estrictamente de `ast.parse`** para prevenir falsos positivos sobre cadenas que contengan operadores o texto libre.
* **Propiedades Representativas:**
  * `Variables/Get Var`: campo `var_name`.
  * `Variables/Memory`: campo `key`.
  * `Basics/String`: campo `value`.
  * `Basics/Text`: campo `text`.
  * `Functions/Conditioner`: campos de texto literal `if_true`, `if_false` (cuando no contienen tags ASS con prefijo `\`).

---

## 7. Ámbitos de Vida, Resolución Jerárquica y Prevención de Colisiones

### 7.1. Jerarquía de Ámbitos en Bucles Anidados

Durante el procesamiento de subtítulos, Pyxis recorre una cascada jerárquica de contextos. Las variables de un ámbito superior están disponibles en todos los ámbitos inferiores, pero las variables locales inyectadas en un sub-bucle no persisten fuera de él:

$$\text{Línea (Global)} \longrightarrow \text{Unidad Principal (Sílaba / Char / Palabra)} \longrightarrow \text{Sub-Bucle (MaxLoop)} \longrightarrow \text{Retorno Iterativo (Pieza / Partícula)}$$

1. **Nivel Línea:** `line.*`, `l.*`, `line_start_time`, `line_end_time`, `line_dur`, `meta.res_x`, `meta.res_y`.
2. **Nivel Unidad Principal:** `syl.*`, `char.*`, `word.*`, `x`, `y`, `center`, `middle`, `left`, `right`, `top`, `bottom`, `width`, `height`, `i`, `n`, `dur`, `st`, `et`.
3. **Nivel Sub-Bucle:** `j`, `maxj`, `module`, `maxloop`.
4. **Nivel Retorno Iterativo:** `s_i`, `s_n` (Slicer), `a_i`, `a_n` (Array), `p_i`, `p_n` (Particles), `c_i`, `c_n` (Clip Gradient), `d_i`, `d_n` (Union & Divide).

### 7.2. Aislamiento por Cola de Salida (*Queue Isolation*)

Cuando el grafo contiene múltiples nodos `System/Output`, cada cola de renderizado procesa su subgrafo de forma completamente aislada. Las variables declaradas mediante `Variables/Define Vars` en la rama de la Capa 1 no se filtran ni interfieren con las variables de la Capa 2, garantizando predictibilidad y determinismo.

### 7.3. Directrices para Prevenir Colisiones de Nombres

1. **No sobreescribir identificadores reservados:** Evitar asignar nombres como `x`, `y`, `i`, `n`, `dur`, `st`, `et` en `Define Vars` a menos que se desee explícitamente mutar la cinemática del glifo mediante los propagadores nativos del motor (`_apply_fx_setting`).
2. **Uso de prefijos contextuales:** En efectos complejos con múltiples cálculos intermedios, emplear prefijos claros (ej. `orb_rad`, `p_vel_x`, `wave_phase`) para evitar colisiones con variables globales y facilitar la depuración visual.
3. **Restauración de contadores al anidar generadores:** Al combinar un bucle `Loops/MaxLoop` (`j`) con un generador de retorno como `Shape/Slicer` (`s_i`), no redefinir `j` dentro de `Define Vars`. Leer `j` mediante `Variables/Get Var` o referenciarlo directamente en expresiones.

---

## 8. Buenas Prácticas de Rendimiento y Retención de Estados

### 8.1. Patrón de Reinicio Estocástico y de Línea en `Memory`

Dado que `Variables/Memory` retiene datos durante toda la sesión de renderizado, un acumulador cinemático que sume desplazamientos entre sílabas continuará acumulando valores indefinidamente si no se reinicia. Para delimitar el acumulador a cada línea individual, debe sincronizarse su reinicio mediante `Basics/Once`:

```
[Basics/Once (mode: line)] ──► [Variables/Memory (mode: remember, key: "acc_x", value: 0.0)]
```

Este esquema asegura que al comenzar una nueva línea de diálogo, la clave `"acc_x"` se inicialice a `0.0`, impidiendo arrastres residuales entre eventos distantes.

### 8.2. Criterio de Selección: Conexión por Cable vs. `Get Var`

* **Conexión por Cable:** Recomendada para dependencias locales y directas dentro del mismo subgrafo visual. Mantiene el flujo de datos explícito y autodocumentado en el lienzo.
* **Nodo `Get Var`:** Recomendado en los siguientes escenarios:
  * Cuando un parámetro calculado en un extremo del grafo debe consumirse en múltiples ramas periféricas distantes, evitando el cruce de cables largos (*wire clutter*).
  * Lectura de iteradores inyectados (`j`, `s_i`, `a_i`) que no poseen un puerto físico en el nodo de bucle principal.
  * Consumo de valores en nodos que solo aceptan entradas de texto o campos inline.

### 8.3. Posicionamiento Topológico de `Define Vars`

Para asegurar que las variables declaradas estén disponibles para todos los nodos dependientes en cada iteración, el nodo `Variables/Define Vars` debe situarse **aguas arriba (*upstream*)** de los nodos consumidores, idealmente intercalado en la cadena de paso (*pass-through*) que une el bucle principal (`Loops/Main Loop`) con el nodo de salida (`System/Output`).
