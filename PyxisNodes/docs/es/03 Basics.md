# Basics

La categoría **Basics** reúne los nodos dedicados a la generación, transformación, formateo y enrutamiento de datos primitivos (números, cadenas, colores, expresiones matemáticas y condicionales) para la construcción de efectos en subtítulos ASS.

---

## 1. Nodo `Basics/Number` (Constante Numérica y Expresiones)

* **Categoría Canónica:** `Basics` (UI: *Básicos / Number*)
* **Propósito:** Emite un valor numérico escalar (entero o punto flotante), evaluando constantes, variables del contexto ASS y expresiones algebraicas en tiempo real.

![Basics/Number](img/number.png)

### 1.1. Puertos de Salida (*Outputs*)
1. **`[1.1] Number`:** Emite el valor numérico evaluado como cadena de texto. Si el valor resultante es un entero exacto, se formatea sin decimales (ej. `10`); si contiene decimales, se redondea a un máximo de 4 decimales significativos sin ceros redundantes a la derecha (ej. `12.5`).

### 1.2. Controles y Propiedades del Cuerpo
1. **`[2.1] Value` (`value`):** Campo de entrada editable. Su valor por defecto inicial es vacío (`""`), evaluándose dinámicamente como `0` si permanece en blanco. Acepta números directos (`100`, `-45.2`), variables del contexto ASS (`syl.x`, `line.width`, `j`, `i`, `char.n`), expresiones matemáticas (`syl.width / 2 + 10`, `sin(j * 0.1) * 50`) o listas de valores separadas por comas (ej. `10, 20, 30`). Permite organizar listas en múltiples líneas mediante `Shift + Enter`; en la evaluación del motor y en el linter, los saltos de línea físicos se omiten de forma transparente para generar una secuencia continua.

### 1.3. Evaluación Dinámica de Expresiones
El campo `value` se procesa dinámicamente en cada ciclo de iteración:
* Si el texto contiene identificadores registrados en el contexto (`syl`, `line`, `char`, `video_fps`, etc.), el evaluador sustituye sus valores numéricos antes del cálculo.
* Si el contenido incluye valores o fórmulas separadas por comas, evalúa cada elemento individualmente devolviendo la lista formateada correspondiente.
* Soporta tanto punto decimal (`12.5`) como coma decimal (`12,5`), normalizándola automáticamente.

### 1.4. Sinergias y Buenas Prácticas
* **Control Paramétrico de Tags ASS:** Conectar la salida `Number` a puertos de `Basics/MultiTag` o plantillas en `Basics/Dynamic Format` para modular etiquetas numéricas como `\fscx<val>`, `\fscy<val>`, `\blur<val>` o coordenadas de posición `\pos(syl.center, <val>)`.
* **Cálculo Relativo de Tiempos:** Alimentar puertos de tiempo (`Start Time`, `End Time`) con expresiones directas relativas al contexto (ej. `syl.start_time - 150`, `line.duration + 200`).

---

## 2. Nodo `Basics/String` (Cadena de Texto Literal)

* **Categoría Canónica:** `Basics` (UI: *Básicos / String*)
* **Propósito:** Emite una cadena de texto fija o con macros de contexto para inyectar textos de diálogo, nombres de estilos, comandos de dibujo o secuencias de escape ASS.

![Basics/String](img/string.png)

### 2.1. Puertos de Salida (*Outputs*)
1. **`[1.1] String`:** Emite la cadena de texto configurada en el cuerpo del nodo.

### 2.2. Controles y Propiedades del Cuerpo
1. **`[2.1] Text` (`value`):** Cadena de texto editable. Admite texto plano, secuencias de salto y espaciado ASS (`\n`, `\N`, `\h`), bloques de etiquetas (`{\an5\bord0\shad0}`) o trazados vectoriales (`m 0 0 l 100 0 100 100 0 100`). Permite utilizar `Shift + Enter` para formatear el texto en múltiples líneas en la interfaz; durante la evaluación de backend y el linting, los saltos de línea físicos se eliminan de forma continua, preservando con total fidelidad los códigos de escape ASS (`\n`, `\N`) que el usuario desee incluir en el subtítulo final. Si el texto incluye bloques entre llaves `{\...}`, el evaluador de cadenas de Pyxis resuelve directamente expresiones y variables contextuales dentro de los paréntesis de cada tag (ej. `{\pos(syl.center, syl.middle)}` o `\fscx(100 + 20 * i)`) preservando el texto literal circundante.

### 2.3. Sinergias y Buenas Prácticas
* **Inyección de Bloques de Encabezado:** Conectar `String` a nodos `Basics/Concatenate` o `Output (Tags)` para prefijar combinaciones de formato estático (ej. `{\an5\bord1\blur1.5}`).
* **Aislamiento de Cadenas de Dibujo:** Centralizar código vectorial en un nodo `String` conectado a la entrada `Draw Code` de `Shape/Slicer` o `Shape/Transform` para evitar duplicación de trazados extensos en el grafo.

---

## 3. Nodo `Basics/Text` (Manipulación y Procesamiento de Cadenas)

* **Categoría Canónica:** `Basics` (UI: *Básicos / Text*)
* **Propósito:** Aplica transformaciones de texto, saneamiento de etiquetas ASS, transliteración fonética japonesa y partición métrica silábica sobre cadenas arbitrarias o unidades del contexto activo.

![Basics/Text](img/text.png)

### 3.1. Puertos de Entrada (*Inputs*)
1. **`Text`:** Cadena de entrada a procesar. Si el puerto permanece desconectado, el nodo toma automáticamente el texto de la unidad activa en el contexto en orden de prioridad: `active_unit.text_stripped` $\to$ `syl.text` $\to$ `char.text` $\to$ `line.text`.

### 3.2. Puertos de Salida (*Outputs*)
1. **`[1.1] Out`:** Cadena de texto resultante tras ejecutar la operación seleccionada.

### 3.3. Selector de Operación (`operation`)
El nodo proporciona 10 operaciones de manipulación de cadenas:

| Operación (`operation`) | Descripción Técnica | Comportamiento y Parámetros Auxiliares |
| :--- | :--- | :--- |
| `strip_tags` | Eliminación de etiquetas ASS | Remueve todos los bloques de control `{\...}`, transforma saltos `\N`, `\n` y espacios duros `\h` en espacios estándar, y recorta espacios en blanco en los extremos. |
| `uppercase` | Conversión a mayúsculas | Transforma toda la cadena a caracteres en mayúscula (`str.upper()`). |
| `lowercase` | Conversión a minúsculas | Transforma toda la cadena a caracteres en minúscula (`str.lower()`). |
| `clean_spaces` | Normalización de espaciado | Sustituye repeticiones contiguas de espacios y tabulaciones por un único espacio (`[ \t]+` $\to$ `" "`). |
| `replace` | Reemplazo de subcadenas | Sustituye todas las coincidencias del texto en `Search` por el contenido de `Replace With`. |
| `substring` | Extracción posicional | Extrae una sección de texto a partir del índice `Start` con una extensión de `Length` caracteres (índice base 0). |
| `length` | Longitud de cadena | Cuenta la cantidad total de caracteres y devuelve el valor entero en formato texto. |
| `contains` | Comprobación de contenido | Emite `"1"` si la cadena contiene la subcadena especificada en `Search`, o `"0"` si no coincide. |
| `kana` | Transliteración japonesa | Convierte texto fonético entre Romaji, Hiragana y Katakana según una tabla de equivalencias, resolviendo dígrafos y consonantes geminadas con sokuon (`っ` / `ッ`). |
| `romaji_to_karaoke` | Segmentación silábica automática | Divide palabras en Romaji en sílabas fonéticas válidas y genera marcas de karaoke ASS temporizadas (`\k<dur>`, `\kf<dur>`, `\ko<dur>`), distribuyendo la duración de la línea uniformemente entre las sílabas. |

### 3.4. Detalle de Algoritmos Especiales

#### 3.4.1. Transliteración de Kana (`kana`)
El motor procesa secuencias de texto ordenando los patrones fonéticos por longitud decreciente para dar precedencia a trigramas y dígrafos (`kya`, `tsu`, `chi`, `sha`) frente a monófonos aislados (`ka`, `ta`, `sa`, `a`). Los modos disponibles en `Mode` son:
* `Romaji to Hiragana`: Convierte texto en alfabeto latino a Hiragana (ej. `"sakura"` $\to$ `"さくら"`, `"gakkou"` $\to$ `"がっこう"`).
* `Romaji to Katakana`: Convierte texto en alfabeto latino a Katakana (ej. `"karaoke"` $\to$ `"カラオケ"`).
* `Hiragana to Katakana`: Convierte caracteres Hiragana a sus equivalentes Katakana.
* `Katakana to Hiragana`: Convierte caracteres Katakana a Hiragana.
* `Kana to Romaji`: Decodifica caracteres Hiragana o Katakana a Romaji fonético estándar.

#### 3.4.2. Generador Romaji a Karaoke (`romaji_to_karaoke`)
Segmenta la cadena de entrada en palabras e identifica las unidades silábicas del japonés romanizado. Para una línea con duración total en centisegundos $T$ y $N$ sílabas detectadas:
$$\text{Duración por sílaba } d_i = \left\lfloor \frac{T}{N} \right\rfloor + (1 \text{ si } i < (T \bmod N))$$

Inyecta la etiqueta configurada en `K Mode` (`\k`, `\kf`, `\ko`, `\K`) con su valor en centisegundos antes de cada sílaba emitida (ej. `{\k15}sa{\k20}ku{\k15}ra`).

### 3.5. Sinergias y Buenas Prácticas
* **Saneamiento Previo a Vectorización:** Conectar `strip_tags` a la entrada `Text` de `Basics/Text to Shape` para asegurar que el motor de renderizado vectorial procese exclusivamente glifos limpios sin etiquetas ASS interpoladas.
* **Comprobación Condicional de Texto:** Utilizar la operación `contains` conectada a `Basics/Only` para bifurcar rutas de estilo según palabras clave presentes en el diálogo.

---

## 4. Nodo `Basics/Color Picker` (Selector Cromático y Paletas)

* **Categoría Canónica:** `Basics` (UI: *Básicos / Color Picker*)
* **Propósito:** Selector y gestor de paletas cromáticas con interfaz visual interactiva y conversión directa entre formatos ASS BGR (`&HBBGGRR&`) y Hexadecimal Web (`#RRGGBB`).

![Basics/Color Picker](img/color_picker.png)

### 4.1. Puertos de Salida (*Outputs*)
1. **`[1.1] Color List`:** Emite la lista completa de colores de la paleta activa como una cadena delimitada por comas, respetando el formato configurado en cada muestra (ej. `"&H5500FF&, &HFF9900&, #FFFFFF"`).
2. **`[1.2] ASS Color`:** Emite el color de la muestra principal (Slot 0) formateado estrictamente en sintaxis de color ASS `&HBBGGRR&`.

### 4.2. Controles Interactivos y Muestras de Paleta (*Swatches*)
* **Edición de Muestras:** Al pulsar sobre una muestra de color (*swatch*) se abre el selector cromático con controles deslizantes, previsualización y selector de formato de salida.
* **Gestión de Paleta:** Permite añadir nuevas muestras y definir de forma independiente si cada muestra exporta en formato `ASS` o `HEX`.

### 4.3. Formatos Cromáticos y Conversión BGR
Pyxis convierte internamente entre el orden de canales RGB estándar y la codificación BGR nativa empleada por Aegisub y libass:

$$\text{RGB: } (R, G, B) \implies \text{ASS Color: } \&\text{H}B_{\text{hex}}G_{\text{hex}}R_{\text{hex}}\&$$

* **Formato ASS (`ASS`):** Invierte los canales Rojo y Azul para ajustarse a libass. Por ejemplo:
  * Rojo puro ($R=255, G=0, B=0$) $\implies$ `&H0000FF&`
  * Azul puro ($R=0, G=0, B=255$) $\implies$ `&HFF0000&`
  * Amarillo puro ($R=255, G=255, B=0$) $\implies$ `&H00FFFF&`
* **Formato Hex (`HEX`):** Conserva el formato web `#RRGGBB` para interacción con herramientas externas.

### 4.4. Sinergias y Buenas Prácticas
* **Asignación Rápida de Color en Tags ASS:** Conectar la salida `ASS Color` a las entradas de color primario (`\1c`) o de borde (`\3c`) en nodos `Basics/MultiTag`.
* **Alimentación de Gradientes y Bordes:** Conectar `Color List` directamente al puerto homónimo en `Functions/Color Gradient` o `Shape/Concentric Borders` para generar transiciones policromáticas consistentes.

---

## 5. Nodo `Basics/Math` (Biblioteca Matemática `ke.math`)

* **Categoría Canónica:** `Basics` (UI: *Básicos / Math*)
* **Propósito:** Concentra las 36 operaciones matemáticas básicas (expandibles), numéricas, de secuencias, geométricas, algebraicas y de datos en un único nodo adaptable que cambia sus entradas, controles y salidas según la operación elegida.

![Basics/Math](img/math.png)

### 5.1. Controles e Interacción en el Lienzo
El nodo organiza sus controles en cuatro tipos de elementos visuales:
1. **Píldoras de Cabecera (`Category` y `Operation`):** Haz clic en la píldora izquierda para cambiar de familia (`basic`, `numeric`, `sequence`, `geometry`, `algebra`, `data`) y en la derecha para elegir la operación. Al cambiar de modo, los puertos de entrada y salida se reconfiguran automáticamente manteniendo los cables compatibles.
2. **Botones `+` y `-` (Solo en `basic`):** Añaden o quitan puertos de entrada (`In1`, `In2`, ..., `InN`) para operar con dos o más valores conectados o escritos en línea.
3. **Campos Editables con Zócalo:** Permiten escribir valores fijos (`10`), listas separadas por comas (`0, 50, 100`) o variables/expresiones (`syl.i`, `char.dur / 2`). Si conectas un cable al zócalo izquierdo, el valor del cable tiene prioridad sobre el texto escrito.
4. **Botones Cíclicos:** Píldoras dentro del cuerpo del nodo (como `Algorithm`, `Seq Mode`, `Get`, `Axis` o `Matrix Op`). Cada clic avanza a la siguiente opción.
5. **Casillas de Verificación:** Casillas cuadradas activables con un clic (`Cycle`, `Random Sign`, `Reals Only`, `Is Row`).

---

### 5.2. Categoría `basic` (Aritmética Expandible)

Permite combinar dos o más entradas (`In1`, `In2`, ..., `InN`) mediante los botones `+` y `-`. Las entradas vacías se omiten automáticamente.

* **`add` (Suma):** Suma todas las entradas (`In1 + In2 + ... + InN`).
* **`sub` (Resta):** Resta secuencialmente desde la primera entrada (`In1 - In2 - ... - InN`).
* **`mul` (Multiplicación):** Multiplica todas las entradas (`In1 * In2 * ... * InN`).
* **`div` (División):** Divide secuencialmente desde `In1` (`In1 / In2 / ... / InN`; devuelve `0` si algún divisor es `0`).
* **`mod` (Módulo):** Calcula el resto de la división secuencial (`In1 % In2 % ...`; devuelve `0` si algún divisor es `0`).
* **`pow` (Potencia):** Eleva secuencialmente (`In1 ** In2 ** ...`).
* **`min` (Mínimo):** Emite el valor numérico menor entre todas las entradas.
* **`max` (Máximo):** Emite el valor numérico mayor entre todas las entradas.
* **`avg` (Promedio):** Calcula la media aritmética de todas las entradas conectadas o escritas.

---

### 5.3. Categoría `numeric` (Cálculo Numérico y Comparaciones)

#### `round` — Redondeo
Redondea un número o una lista de números al número de decimales indicado, aplicando redondeo clásico hacia arriba en mitades (`.5` sube al siguiente entero).
* **Entradas:** `Value` (número o lista separada por comas), `Decimals` (cantidad de decimales; por defecto `0`).
* **Salida:** `Out`.
* **Ejemplo:** `Value = "1.6, 3.25, 8.7"`, `Decimals = 1` $\to$ `"1.6, 3.3, 8.7"`.

#### `clamp` — Acotación y Rebote Cíclico
Mantiene un número (o lista) dentro de los límites `Min` y `Max`, sin importar cuál escribas primero.
* **Entradas y Controles:** `Value`, `Min` (defecto `0`), `Max` (defecto `1`), casilla **`Cycle`**.
* **Salida:** `Out`.
* **Comportamiento:**
  * Con `Cycle` desactivado: cualquier valor menor que `Min` se fija en `Min`, y cualquiera mayor que `Max` se fija en `Max`.
  * Con `Cycle` activado: cuando el valor supera un límite, rebota de ida y vuelta dentro del rango (útil para crear movimientos pendulares continuos).
* **Ejemplo:** `Value = 1.2`, `Min = 0`, `Max = 1`, `Cycle = activado` $\to$ `0.8`.

#### `rand` — Aleatorio Avanzado
Genera números aleatorios con control de incremento, subrangos ponderados o selección directa sobre listas.
* **Entradas y Controles:**
  * `Min` y `Max`: límites del rango. Si dejas `Max` vacío y escribes una lista en `Min` (ej. `"10, 20, 30"`), elige uno de esos elementos al azar. Si ambos quedan vacíos, emite un decimal entre `0` y `1`.
  * `Step`: incremento permitido entre valores (ej. `Step = 5` entre `0` y `20` solo genera `0, 5, 10, 15, 20`).
  * `Range`: subrango con probabilidad en formato `rmin, rmax, porcentaje` (ej. `"20, 80, 75"` hace que el 75% de los resultados caiga entre 20 y 80).
  * Casilla **`Random Sign`**: multiplica el resultado por `+1` o `-1` al azar.
* **Salida:** `Out`.

#### `factk` — Factorial
Calcula el factorial de `N` (redondeado hacia arriba en valor absoluto; para `0` devuelve `1`).
* **Entradas:** `N` $\to$ **Salida:** `Out`.
* **Ejemplo:** `N = 5` $\to$ `120`.

#### `to16` — Conversión a Hexadecimal
Convierte un número entero (o una lista) a texto hexadecimal en mayúsculas, útil para construir canales de color o transparencia en etiquetas ASS.
* **Entradas:** `Number` $\to$ **Salida:** `Out`.
* **Ejemplo:** `Number = "255, 16, 12"` $\to$ `"FF, 10, C"`.

#### `equality` — Igualdad con Tolerancia
Compara `A` y `B` y emite `True` si su diferencia es menor que el margen definido por `Tolerance` (donde `Tolerance = 5` equivale a una diferencia menor a `0.00001`).
* **Entradas:** `A`, `B`, `Tolerance` (defecto `5`) $\to$ **Salida:** `Out` (`True` o `False`).

#### `between` — Comprobación de Rango
Comprueba si `Value` está dentro del intervalo cerrado formado por `Min` y `Max` (el orden de `Min` y `Max` se ajusta automáticamente).
* **Entradas:** `Value`, `Min`, `Max` $\to$ **Salida:** `Out` (`True` o `False`).

---

### 5.3. Categoría `sequence` (Secuencias, Contadores e Interpolación)

#### `i` — Generador de Secuencias Discretas
Transforma un contador entero positivo `Counter (i)` (como `syl.i`, `char.i` o `j`) en patrones numéricos repetitivos sin escribir condicionales.
* **Entradas y Controles:** `Counter (i)`, botón cíclico **`Algorithm`**, `A`, `B`, `C`.
* **Salida:** `Out`.
* **Guía rápida de los 9 algoritmos** (mostrando la salida para `Counter = 1, 2, 3, 4, 5, 6`):

| Algoritmo | Qué hace | Ejemplo con parámetros | Secuencia resultante (`i = 1..6`) |
| :--- | :--- | :--- | :--- |
| `+,-` | Alterna `1` y `-1` cada `A` pasos | `A = 2` | `1, 1, -1, -1, 1, 1` |
| `A,B` | Alterna entre `A` y `B` cada `C` pasos | `A = 10, B = 20, C = 1` | `10, 20, 10, 20, 10, 20` |
| `mxA` | Multiplica `A` escalando cada `B` pasos | `A = 5, B = 2` | `5, 5, 10, 10, 15, 15` |
| `A>B` | Recorre de `A` a `B` en ciclo cada `C` pasos | `A = 1, B = 3, C = 1` | `1, 2, 3, 1, 2, 3` |
| `ABA` | Sube y baja entre `A` y `B` (ida y vuelta) | `A = 1, B = 3` | `1, 2, 3, 2, 1, 2` |
| `ABB` | Emite `A` en el primer paso y `B` en el resto | `A = 5, B = 9` | `5, 9, 9, 9, 9, 9` |
| `ABC` | Emite `A` una vez y `B` durante `C - 1` pasos | `A = 1, B = 2, C = 3` | `1, 2, 2, 1, 2, 2` |
| `ACB` | Emite `A` durante `C - 1` pasos y luego `B` | `A = 1, B = 2, C = 3` | `1, 1, 2, 1, 1, 2` |
| `N,n` | Números naturales repetidos `A` veces cada uno | `A = 2` | `1, 1, 2, 2, 3, 3` |

#### `count` — Contador con Estado
Mantiene un contador interno propio para ese nodo que empieza en `Init` y avanza sumando `Step` cada vez que se evalúa durante la generación.
* **Entradas y Controles:** `Init` (defecto `1`), `Step` (defecto `1`), botón cíclico **`Seq Mode`** (`none` o cualquiera de los 9 algoritmos de `i`), `A`, `B`, `C`.
* **Salida:** `Out`.

#### `normalize` — Normalización de Progreso
Convierte cualquier número (o lista progresiva) en un factor normalizado entre `0` y `1`.
* **Entradas:** `t` (si es mayor que `1`, se divide automáticamente por la potencia de 10 correspondiente, ej. `25` $\to$ `0.25`), `Accel` (exponente de aceleración; `1` es lineal, `2` arranca lento, `0.5` arranca rápido) y `Shape` (opcional: si conectas un trazado ASSDraw, usa la altura vertical `Y` de la forma como curva de progreso).
* **Salida:** `Out`.

#### `ipol` — Interpolación Multipunto
Calcula el valor intermedio a lo largo de una lista de dos o más puntos en `Values` según el progreso `t` (entre `0` y `1`).
* **Entradas:** `Values` (ej. `"0, 30, 20"`), `t`, `Accel`, `Shape` (curva opcional mediante forma ASSDraw) y `Size` (opcional: si escribes un entero como `5`, genera la lista completa de 5 valores muestreados de principio a fin).
* **Salida:** `Out`.
* **Ejemplo:** `Values = "0, 100"`, `Size = 3` $\to$ `"0, 50, 100"`.

---

### 5.4. Categoría `geometry` (Geometría ASSDraw3)

Todas las operaciones de esta categoría trabajan en el sistema de coordenadas ASSDraw3 utilizado por los subtítulos (origen arriba a la izquierda y eje Y apuntando hacia abajo).

#### `angle` — Ángulo entre Puntos
Calcula el ángulo en grados (de `0` a `360`) formado por uno, dos o tres puntos.
* **Entradas:** `P1`, `P2`, `P3` (opcional).
  * Con `P1` solo: ángulo del punto respecto al origen `(0, 0)`.
  * Con `P1` y `P2`: ángulo del segmento que va de `P1` a `P2`.
  * Con `P1`, `P2` y `P3`: ángulo interior entre los dos segmentos unidos en `P2`.
* **Salida:** `Out`.

#### `polar` — Coordenadas Polares
Convierte un ángulo en grados (`Angle`) y una distancia en píxeles (`Radius`) en coordenadas cartesianas `(X, Y)` listas para usar en `\pos` o en formas.
* **Entradas y Controles:** `Angle`, `Radius`, botón cíclico **`Get`** (`xy`, `x`, `y`).
* **Salidas:** `X`, `Y`. Cuando el botón `Get` está en `y`, ambos puertos o la salida principal entregan la componente vertical `Y`.
* **Ejemplo:** `Angle = 45`, `Radius = 10` $\to$ `X = 7.071`, `Y = -7.071`.

#### `distance` — Distancia y Longitud de Trazado
Calcula la distancia en píxeles entre dos puntos `P1` y `P2`, la distancia al origen si `P2` está vacío, o la longitud total recorrida si `P1` contiene una polilínea o forma ASSDraw con múltiples vértices.
* **Entradas:** `P1`, `P2` $\to$ **Salida:** `Out`.
* **Ejemplo:** `P1 = "0, 0"`, `P2 = "3, 4"` $\to$ `5`.

#### `intersect` — Intersección de Segmentos
Calcula el punto exacto donde se cruzan las rectas definidas por `Segment 1` (`x1 y1 x2 y2`) y `Segment 2` (`x3 y3 x4 y4`).
* **Entradas:** `Segment 1`, `Segment 2`.
* **Salidas:** `X`, `Y`, `t` (posición relativa del cruce sobre el primer segmento; si no se cruzan, emite `parallels` en `X`).

#### `circle` — Circunferencia por Tres Puntos
Calcula el centro y el radio del círculo único que pasa por `P1`, `P2` y `P3` (o los tres primeros puntos de una forma).
* **Entradas:** `P1`, `P2`, `P3`.
* **Salidas:** `Center X`, `Center Y`, `Radius` (si los tres puntos están alineados en una recta, emite `collineals` en `Center X`).

#### `rotate` — Rotación 2D / 3D de Puntos y Formas
Rota un punto `(x, y, z)` o todos los vértices de una forma ASSDraw completa alrededor del eje seleccionado.
* **Entradas y Controles:** `Point / Shape` (coordenadas o cadena ASSDraw `m ... l ...`), `Angle` (grados), botón cíclico **`Axis`** (`z`, `x`, `y`).
* **Salidas:** `Out` (lista `x, y, z` o la cadena ASSDraw ya rotada), `X`, `Y`, `Z`.

---

### 5.5. Categoría `algebra` (Ecuaciones y Matrices)

#### `quadratic` — Ecuación Cuadrática
Encuentra las raíces reales de una ecuación de segundo grado (`c1*x^2 + c2*x + c3 = 0`) ordenadas de menor a mayor.
* **Entradas:** `c1 (x^2)`, `c2 (x)`, `c3 (1)` $\to$ **Salida:** `Roots`.

#### `cubic` — Ecuación Cúbica
Encuentra las raíces reales de una ecuación de tercer grado (`c1*x^3 + c2*x^2 + c3*x + c4 = 0`).
* **Entradas:** `c1 (x^3)`, `c2 (x^2)`, `c3 (x)`, `c4 (1)` $\to$ **Salida:** `Roots`.

#### `resolve` — Solucionador Automático
Recibe una lista de coeficientes en orden descendente en `Coefficients` (descartando ceros iniciales) y resuelve automáticamente ecuaciones lineales, cuadráticas o cúbicas.
* **Entradas:** `Coefficients` $\to$ **Salida:** `Roots`.

#### `equation` — Polinomios de Grado N
Calcula todas las raíces de un polinomio de cualquier grado ingresando los coeficientes en orden ascendente (ej. `"-5, -9, -3, 1"` representa `-5 - 9x - 3x^2 + x^3 = 0`).
* **Entradas y Controles:** `Coefficients`, casilla **`Reals Only`** (si está activada, oculta las raíces complejas).
* **Salida:** `Roots`.

#### `evaluate` — Evaluación Polinómica
Calcula el valor del polinomio definido en `Coefficients` (orden ascendente) en el punto `t`.
* **Entradas:** `Coefficients`, `t` $\to$ **Salida:** `Out`.
* **Ejemplo:** `Coefficients = "5, -7"`, `t = 2` (calcula `5 - 7*2`) $\to$ `-9`.

#### `gauss` — Sistema de Ecuaciones Lineales
Resuelve un sistema de `n` ecuaciones con `n` incógnitas escribiendo las filas de la matriz aumentada separadas por punto y coma `;`.
* **Entradas:** `Matrix` (ej. `"5, -3, -1; 2, 1, 4"` representa `5x - 3y = -1` y `2x + y = 4`).
* **Salida:** `Solutions` (ej. `"1, 2"`, o `"singular system"` si no tiene solución única).

#### `matrix` — Álgebra Matricial
Realiza operaciones sobre matrices cuadradas y vectores fila. Las filas se separan con `;` o se escriben como lista plana de números (ej. `"1, 2, 3, 4"` equivale a una matriz 2x2).
* **Entradas y Controles:**
  * Botón cíclico **`Matrix Op`**:
    * `mul`: Multiplica `Matrix A` por `Matrix B` (acepta otra matriz, un escalar numérico o un vector).
    * `add` / `sub`: Suma o resta elemento a elemento entre `Matrix A` y `Matrix B` (o un escalar).
    * `neg`: Invierte el signo de todos los elementos de `Matrix A`.
    * `det`: Calcula el determinante de `Matrix A`.
    * `inverse`: Calcula la matriz inversa de `Matrix A` (o emite `singular matrix` si su determinante es 0).
    * `identity`: Crea una matriz identidad de tamaño `N` (tomando el primer número de `Matrix A`).
    * `rotate`: Multiplica `Matrix A` por la matriz de rotación 3D definida en `Angles (x,y,z)`.
    * `eq`: Comprueba si `Matrix A` y `Matrix B` son iguales (`True` o `False`).
    * `toarray`: Convierte `Matrix A` en una lista plana separada por comas.
  * Casilla **`Is Row`**: trata `Matrix A` como un vector fila en lugar de matriz cuadrada.
* **Salidas:** `Out` (resultado formateado) y `Det` (determinante de la matriz).

---

### 5.6. Categoría `data` (Extracción y Formateo)

#### `getpair` — Extraer Par Numérico
Extrae los dos primeros números encontrados en `Values` (útil para leer coordenadas `(x, y)` desde texto o trazados ASSDraw). Si falta el segundo número, repite el primero o usa `Default Y`; si está vacío, usa `Default X` y `Default Y`.
* **Entradas:** `Values`, `Default X`, `Default Y` $\to$ **Salidas:** `X`, `Y`.

#### `getnumbers` — Extraer Todos los Números
Extrae cualquier número presente en una cadena de texto, par de coordenadas o forma ASSDraw (`Input`) y los devuelve separados por coma.
* **Entradas:** `Input` $\to$ **Salida:** `Out`.
* **Ejemplo:** `Input = "m 1 2 l -3.5 4"` $\to$ `"1, 2, -3.5, 4"`.

#### `format` — Formateo de Texto
Inserta los valores de `Values` (separados por comas) dentro de marcadores de formato como `%s`, `%d` o `%X` en `Format`.
* **Entradas:** `Format`, `Values` $\to$ **Salida:** `Out`.
* **Ejemplo:** `Format = "pos(%d, %d)"`, `Values = "10, 20"` $\to$ `"pos(10, 20)"`.

---

### 5.7. Flujos Prácticos de Producción

1. **Alternar el giro de sílabas pares e impares:**
   ```
   [Basics/Math (sequence / i, Algorithm: +,-)] ──► Out ──► \frz ──► [Basics/MultiTag]
   ```
   Escribe `syl.i` en `Counter (i)` y `1` en `A`; obtendrás `+1` y `-1` alternados para inclinar cada sílaba sin condicionales.

2. **Distribuir letras o partículas en círculo alrededor de un punto:**
   ```
   [Basics/Math (geometry / polar)] ──► X ──► X ──► [Basics/MultiTag (\pos)]
                                    └──► Y ──► Y ──┘
   ```
   Conecta el ángulo proporcional al índice de cada elemento (`360 * (char.i - 1) / char.n`) en `Angle` y la distancia deseada en `Radius`.

3. **Curva de movimiento guiada por una figura:**
   ```
   [Shape/Library] ──► Shape ──► Shape ──► [Basics/Math (sequence / ipol)] ──► Out ──► [Basics/MultiTag]
   ```
   Al conectar cualquier forma en `Shape`, `ipol` usa su perfil vertical como curva de aceleración entre los valores definidos en `Values`.

4. **Rotar una figura completa directamente en el grafo:**
   ```
   [Shape/Library] ──► Shape ──► Point / Shape ──► [Basics/Math (geometry / rotate)] ──► Out ──► [System/Output]
   ```
   Con `Axis` en `z`, todos los vértices de la figura giran según el ángulo indicado y salen listos como dibujo ASSDraw.

---

## 6. Nodo `Basics/MultiRandom` (Generador Estocástico Determinista)

* **Categoría Canónica:** `Basics` (UI: *Básicos / MultiRandom*)
* **Propósito:** Genera valores pseudoaleatorios escalares o listas deterministas para dispersión espacial, fluctuaciones de tags y secuencias estocásticas en 15 modalidades.

![Basics/MultiRandom](img/multirandom.png)

### 6.1. Puertos de Entrada (*Inputs*)
1. **`Min`:** Límite inferior del rango de generación, color inicial o lista de opciones.
2. **`Max`:** Límite superior del rango o color final.
3. **`Step`:** Intervalo de cuantización discreta entre valores generados.
4. **`Total (N)`:** Cantidad total de valores a emitir cuando se utiliza la salida `Batch / List`.
5. **`Iterator`:** Variable de ámbito que gobierna la memorización del valor (ej. `s_i`, `j`, `syl`, `char`, `line`). Si permanece vacío, se calcula un nuevo valor en cada evaluación.

### 6.2. Puertos de Salida (*Outputs*)
1. **`[1.1] Data`:** Emite un único valor aleatorio evaluado para la iteración actual.
2. **`[1.2] Batch / List`:** Emite una lista de $N$ valores aleatorios separados por comas (`v1, v2, v3, ...`), adecuada para alimentar listas de parámetros o matrices de partículas.

### 6.3. Despachador de Ámbito en Expresiones (`by.<iterador>.<R_modo>`)
Para invocar aleatoriedad determinista memorizada por iterador dentro de expresiones ASS o scripts Python:
* **En Expresiones ASS:**
  ```text
  \frz(by.syl.Rs(15))
  \fscx(100 + by.char.R(0, 30))
  ```
* **En Scripts (`Define Vars` / `Script Code`):**
  ```python
  angle = by.s_i.Rms(0.01, 0.02)          # Mismo valor durante el ciclo del trozo de Slicer
  offset = by.j.Rs(10)                    # Mismo valor durante la repetición de MaxLoop
  color = by.syl.Rcolor("#FFFFFF", "#0088FF") # Mismo color para toda la sílaba
  ```
Dentro del mismo ciclo del iterador indicado, las llamadas repetidas devuelven el mismo valor almacenado en caché. Al avanzar el iterador, el motor recalcula el valor automáticamente.

* **Herencia Jerárquica de Ámbito:** Los sub-bucles (`by.j`, `by.s_i`, `by.p_i`) heredan la jerarquía de la unidad activa superior (`line` -> `char`/`syl`/`word` -> sub-bucle). De este modo, la partícula $j=1$ del carácter 1 genera valores independientes de la partícula $j=1$ del carácter 2. A su vez, `by.char.R(...)` mantiene su valor idéntico para todos los ciclos de $j$ dentro del mismo carácter, recalculándose únicamente al avanzar de carácter.
* **Aislamiento por Punto de Llamada (*Callsite Isolation*):** Cada vez que escribes `R(...)` o `by.<iter>.R*(...)` (incluso varias veces en la misma fórmula, como `R(10) + R(10) + R(10)`, o en dos variables distintas como `Origenx` y `Origeny`), cada llamada se calcula por separado y nunca se mezclan entre sí.
* **Agrupación mediante Variables vs. Combinaciones Mixtas:** Lo único que mantiene un mismo resultado en varios sitios dentro de una iteración es **guardarlo en una variable** y reutilizar esa variable:
  * Si defines `mi_var = by.char.R(10)` y la usas en varios tags o puertos, obtendrás el mismo número en todos los bucles de ese carácter (y cambiará al pasar al siguiente carácter).
  * Si combinas ámbitos en una variable, por ejemplo `mi_var = by.j.R(10) + by.char.R(10)`, el término `by.char.R(10)` permanece constante por carácter mientras `by.j.R(10)` cambia en cada ciclo `j`, de modo que `mi_var` entregará un valor distinto por cada combinación `(char, j)` (y solo devolverá el mismo valor si lees `mi_var` varias veces dentro de esa misma pasada).
  * Si usas `R(10)` sin `by.`, cada llamada genera un número nuevo en cada iteración del bucle donde se evalúe.

### 6.4. Catálogo de los 15 Modos de Aleatoriedad (`mode`)

| Modo (`mode`) | Nombre / Tipo | Descripción Algorítmica y Rango | Ejemplo de Salida |
| :--- | :--- | :--- | :--- |
| `R` | Aleatorio Uniforme | Números aleatorios entre `Min` y `Max` cuantizados a múltiplos de `Step`. Si los extremos y el paso son enteros, devuelve enteros exactos. | `42` |
| `Rs` | Simétrico Bipolar | Aplica un signo aleatorio equiprobable ($\pm 1$) sobre el valor uniforme: $\text{res} = R(\text{Min}, \text{Max}) \cdot (\pm 1)$. | `-35` o `35` |
| `Rr` | Relativo a Resolución | Escala el valor en proporción al ancho horizontal del script ASS ($R_x$ relativo a $1280\text{ px}$): $\text{res} = R \cdot \frac{R_x}{1280}$. | `68.5` |
| `Rd` | Decimal Simple | Flotante uniforme acotado a 1 decimal de precisión ($0.1$). | `14.3` |
| `Rc` | Centesimal | Flotante uniforme acotado a 2 decimales de precisión ($0.01$). | `87.25` |
| `Rm` | Milésimas | Flotante uniforme de alta precisión a 3 decimales ($0.001$). | `3.142` |
| `Rds` | Decimal Bipolar | Variante de `Rd` con signo equiprobable ($\pm$). | `-12.4` |
| `Rcs` | Centesimal Bipolar | Variante de `Rc` con signo equiprobable ($\pm$). | `-45.82` |
| `Rms` | Milésimas Bipolar | Variante de `Rm` con signo equiprobable ($\pm$). | `+0.915` |
| `Re` | Selección Discreta | Selecciona al azar un elemento a partir de una lista delimitada por comas en `Options` (ej. `\blur1, \blur3, \blur6`). | `\blur3` |
| `Rfake` | Hash Determinista | Generador congruencial dependiente exclusivamente del contador de iteración ($i$ o $j$): $\text{Hash}(c) = (c \cdot 9301 + 49297) \pmod{233280}$. | `18` |
| `Rcolor` | Interpolación Cromática | Genera un color aleatorio interpolando uniformemente entre `Min` y `Max` en espacio RGB, o seleccionando de una lista si `Min` contiene comas. | `&H7FA412&` |
| `R2d` | Coordenadas 2D | Emite un par cartesiano aleatorio independiente en formato `"X,Y"`. | `120.5,-45.2` |
| `Rbool` | Booleano Probabilístico | Devuelve `"True"` o `"False"` según un umbral de probabilidad porcentual $P \in [0, 100]$ indicado en `Min`. | `"True"` |
| `Rstep` | Paso Cuantizado | Genera valores restringidos estrictamente a múltiplos enteros de `Step` (ej. rotaciones en múltiplos de $45^\circ$). | `180` |

### 6.5. Sinergias y Buenas Prácticas
* **Fluctuación Espacial Controlada:** Conectar la salida `Data` en modo `Rs` con rango $[2, 8]$ a un desplazamiento posicional $\Delta x$ para añadir vibración orgánica a cada glifo o sílaba sin perder la legibilidad del texto base.
* **Variedad Cromática por Sílaba:** Utilizar `Rcolor` con ámbito `by.syl` conectado al puerto `\1c` de `Basics/MultiTag` para que cada sílaba mantenga un color uniforme internamente pero diferente respecto a las demás.

---

## 7. Nodo `Basics/Concatenate` (Concatenador Extensible y Zip)

* **Categoría Canónica:** `Basics` (UI: *Básicos / Concatenate*)
* **Propósito:** Ensambla múltiples fragmentos de texto, etiquetas ASS o secuencias de keyframes mediante dos modos de operación (`basic`, `zip`) seleccionables desde la cabecera, incorporando un selector contextual de separador en la esquina inferior derecha para el modo básico. Para ensamblar y estilizar formas vectoriales complejas de forma monolínea con o sin reinicio de estilo `\r`, utilice canónicamente `Basics/Builder`.

![Basics/Concatenate](img/concatenate.png)

### 7.1. Puertos de Entrada y Expansión Dinőmica
* **`In1`, `In2`, $\dots$, `InN`:** Puertos de entrada secuenciales. Al conectar o añadir puertos mediante el botón `(+)`, el nodo agrega ranuras adicionales de forma continua.
* **Precedencia:** Si un puerto no tiene cable de enlace conectado, el nodo toma el valor escrito manualmente en su campo de texto inline.

### 7.2. Puertos de Salida (*Outputs*)
1. **`[1.1] String`:** Cadena de texto resultante tras ensamblar las entradas activas según el modo seleccionado.

### 7.3. Modos Operativos Principales (`mode`)
La píldora en el extremo derecho de la barra de título conmuta entre los 2 modos canónicos:

| Modo (`mode`) | Insignia UI | Descripción Algorítmica |
| :--- | :--: | :--- |
| `basic` | `BASIC` | Concatenación lineal de entradas intercalando el delimitador seleccionado en el cuerpo (`separator`). |
| `zip` | `ZIP` | Entrelazado posicional elemento a elemento para generar listas de keyframes temporizados. |

### 7.4. Selector de Separator en Modo Básico (`separator`)
Cuando el nodo opera en modo `basic`, se dibuja un botón interactivo en la esquina inferior derecha (bajo el puerto de salida *Texto / String*). Al pulsarlo, cicla entre los delimitadores soportados:

| Separador (`separator`) | Pñldora UI | Carácter Inyectado | Caso de Uso Típico |
| :--- | :--: | :--- | :--- |
| `nil` | `NONE` | *(Ninguno)* | Unión continua directa (ej. `\pos(X,Yi\blur2\1c&HFFFFFF&`). |
| `space` | `SPACE` | Espacio " " | Secuencias de palabras o comandos ASSdraw simples. |
| `comma` | `,` | Coma , | Listas de parámetros y arrays de valores numéricos. |
| `semicolon` | `;` | Punto y coma ; | Agrupación de instrucciones o sentencias de scripting. |
| `newline` | `ENTER` | Salto de línea `\n` | Subtítulos apilados en múltiples líneas de diálogo. |

*Nota:* En el modo `zip`, el botón de separator se oculta automáticamente del lienzo interactivo, ya que gestiona su propia unión algorítmica sin requirir delimitadores textuales.

### 7.5. Algoritmo de Entrelazado Paralelo (*Modo zip*)
Cuando `mode` se configura en `zip`, el nodo trata cada entrada como una lista de elementos separados por comas y los combina elemento a elemento:

$$\text{In}_1 = [A_1, A_2, A_3], \quad \text{In}_2 = [B_1, B_2, B_3] \implies \text{Out} = [A_1 B_1, \, A_2 B_2, \, A_3 B_3]$$

1. Descompone cada entrada activa en una secuencia de tokens.
2. Si el campo inline de un puerto contiene un prefijo de tag (ej. `\1c`, `Yblur`), lo antepone a cada token individual de esa lista.
3. Empareja los elementos posición a posición hasta alcanzar la longitud de la lista más corta con más de un elemento, emitiendo una lista de keyframes fusionados delimitada por comas.

### 7.6. Sinergias y Buenas Prácticas
* **Ensamblado Limpio de Bloques ASS:** Usar `mode: basic` con `separator: nil` para fusionar salidas de `MultiTag` o cadenas directas sin insertar espacios accidentales que puedan alterar el renderizado de libass.
* **Construcción de Keyframes Vectorizados:** Emplear `mode: zip` combinando una lista de colores de `Functions/Color Gradient` con una lista de opacidades para alimentar secuencias de transformación por fotograma.

---


## 8. Nodo `Basics/Dynamic Format` (Formateador Dinámico de Cadenas)

* **Categoría Canónica:** `Basics` (UI: *Básicos / Dynamic Format*)
* **Propósito:** Ensambla cadenas de texto mediante plantillas con especificadores de formato estilo `printf` (`%s`, `%d`, `%f`, `%.2f`, `%04d`, `%x`) y vectorización automática sobre listas delimitadas por comas.

![Basics/Dynamic Format](img/dynamic_format.png)

### 8.1. Puertos de Entrada (*Inputs*)
1. **`In1`, `In2`, $\dots$, `InN`:** Valores escalares o listas que se inyectan en los marcadores de posición posicionales (`%...`) de la plantilla.

### 8.2. Puertos de Salida (*Outputs*)
1. **`[1.1] String`:** Cadena resultante tras aplicar el formateo. Si las entradas son listas, devuelve la serie de resultados formateados combinados mediante comas.

### 8.3. Especificadores Soportados en `format`

| Especificador | Tipo Esperado | Conversión Aplicada | Ejemplo con Entrada `42.68` |
| :--- | :--- | :--- | :--- |
| `%s` | Cualquier dato | Inserción directa como texto. | `"42.68"` |
| `%d` / `%i` | Entero | Conversión a número entero. | `"42"` |
| `%04d` | Entero con relleno | Entero rellenado con ceros hasta 4 dígitos. | `"0042"` |
| `%f` | Flotante | Representación estándar en punto flotante. | `"42.680000"` |
| `%.2f` | Flotante acotado | Formateo restringido exactamente a 2 decimales. | `"42.68"` |
| `%x` / `%X` | Hexadecimal | Entero convertido a base 16 en minúsculas o mayúsculas. | `"2a"` / `"2A"` |

### 8.4. Vectorización Automática sobre Listas
Si alguna entrada recibe una lista de valores delimitada por comas (ej. `In1 = "10, 20, 30"`, `In2 = "0.5, 1.0, 1.5"`), `Dynamic Format` repite la plantilla para cada par de elementos:

$$\text{Plantilla: } \texttt{\\blur\%s\\bord\%s} \implies \texttt{"\\blur10\\bord0.5, \\blur20\\bord1.0, \\blur30\\bord1.5"}$$

### 8.5. Sinergias y Buenas Prácticas
* **Construcción de Tags con Precisión Numérica:** Usar `\pos(%.1f,%.1f)` o `\fscx%d\fscy%d` para garantizar que los valores numéricos evaluados se redondeen con la precisión requerida sin generar cadenas con exceso de decimales en el archivo ASS.
* **Transformaciones Temporizadas Dinámicas:** Plantillas complejas como `\t(%d,%d,\fscx%d\fscy%d)` permiten cablear cálculos de tiempos y escalas de forma compacta en un único nodo antes de la salida final.

---

## 9. Nodo `Basics/MultiTag` (Generador Universal de Etiquetas ASS)

* **Categoría Canónica:** `Basics` (UI: *Básicos / MultiTag*)
* **Propósito:** Genera y serializa etiquetas de estilo, transformaciones espaciales, cinemática, colorimetría, canal alfa y recorte para subtítulos ASS.

![Basics/MultiTag](img/multitag.png)

### 9.1. Encabezado, Modos y Atajos Interactivos
1. **`[2.1] Tag Type` (`tag_type`):** Selector desplegable que define el tipo de etiqueta ASS a generar y reconfigura los puertos de entrada correspondientes:

```text
[ \pos ] ───> Inputs: [ X, Y ]
[ \move ] ──> Inputs: [ X1, Y1, X2, Y2, T1, T2 ]
[ \org ] ───> Inputs: [ X, Y ]
[ \t ] ─────> Inputs: [ Tags, T1, T2, Accel ]
[ \clip ] ──> Inputs: [ Shape / Drawing ]
[ \1c..\4c ]> Inputs: [ Color ]
[ \alpha ] ─> Inputs: [ Alpha (0..255) ]
[ Escalar ] > Inputs: [ Value ] (ej. \fscx, \frz, \blur, \bord)
```

2. **Acceso al Catálogo de Tags y Apertura por Clic Único:**
   * Al hacer un **solo clic en la píldora de modo de la cabecera** (o doble clic sobre el cuerpo del nodo), se despliega de inmediato el catálogo modal interactivo de etiquetas ASS y Dark Tags con buscador en tiempo real. Un clic ya no cicla los tags manualmente; toda la selección se efectúa directamente desde el menú modal.

### 9.2. Puertos de Salida (*Outputs*)
1. **`[1.1] String`:** Emite el bloque de texto con la etiqueta ASS formateada y serializada con sintaxis válida (ej. `\pos(640,360)`, `\t(0,500,2.0,\fscx150\fscy150)`).

### 9.3. Catálogo de Etiquetas ASS Soportadas
* **`pos` $\to$ `\pos(X,Y)`:** Posición cartesiana del elemento en pantalla.
* **`move` $\to$ `\move(X1,Y1,X2,Y2[,T1,T2])`:** Desplazamiento lineal cinemático entre dos coordenadas.
* **`org` $\to$ `\org(X,Y)`:** Punto de origen cartesiano para rotaciones (`\frz`) y deformaciones afines.
* **`t` $\to$ `\t([T1,T2,][Accel,]Tags)`:** Animación paramétrica continua de etiquetas interpoladas.
* **`fad` $\to$ `\fad(FadeIn,FadeOut)`:** Fundido simple de entrada y salida en milisegundos.
* **`fade` $\to$ `\fade(A1,A2,A3,T1,T2,T3,T4)`:** Fundido de opacidad de 3 niveles temporizados.
* **`clip` / `iclip` $\to$ `\clip(Shape)` / `\iclip(Shape)`:** Máscaras de recorte vectorial directa o invertida.
* **`1c` $\dots$ `4c` $\to$ `\1c&HBBGGRR&` $\dots$ `\4c&HBBGGRR&`:** Colores de relleno, karaoke secundario, borde y sombra.
* **`alpha`, `1a` $\dots$ `4a` $\to$ `\alpha&HAA&` $\dots$ `\4a&HAA&`:** Opacidad global o por canal específico.
* **Escala y Rotación:** `\fscx`, `\fscy`, `\frz`, `\frx`, `\fry`, `\fax`, `\fay`.
* **Borde y Sombra:** `\bord`, `\xbord`, `\ybord`, `\shad`, `\xshad`, `\yshad`.
* **Desenfoque:** `\blur`, `\be`.
* **Tipografía y Disposición:** `\an`, `\fs`, `\fsp`, `\fn`, `\r`, `\q`, `\b`, `\i`, `\u`, `\s`.
* **Catálogo de Dark Tags (Extensiones Avanzadas de Pyxis):**
  * **Compuestos y Multicanal:** `\fscxy` (escala uniforme X e Y), `\faxy` (cizallado uniforme), `\xybord` (borde uniforme), `\xyshad` (sombra uniforme), `\bs` (borde y sombra simultáneos), `\frxy`, `\frxz`, `\fryz`, `\frxyz` (rotaciones 3D compuestas), colores multicanal (`\134c`, `\13c`, `\14c`, `\34c`, `\12c`, `\23c`) y transparencias multicanal (`\134a`, `\13a`, `\14a`, `\34a`, `\12a`, `\23a`).
  * **Auto-Origen 3D (`o`):** Rotaciones referenciadas automáticamente al centro métrico del elemento sin necesidad de declarar `\org` (`\fro`, `\frzo`, `\frxo`, `\fryo`, `\frxyo`, `\frxzo`, `\fryzo`, `\frxyzo`).
  * **Restauración de Estilo Original (`~`):** Restablece instantáneamente el valor de estilo base del diálogo sin parámetros (`\c~`, `\alpha~`, `\fscxy~`, `\fscx~`, `\fscy~`, `\fs~`, `\fsp~`, `\fn~`, `\an~`, `\bord~`, `\shad~`, `\bs~`, `\blur~`, `\be~`, `\frz~`, `\frx~`, `\fry~`, `\frxyz~`, `\faxy~`, `\b~`, `\i~`, `\u~`, `\s~`, y canales combinados `\134c~`..`\34c~`, `\134a~`..`\34a~`).
  * **Ratio de Estilo (`r`):** Multiplica el valor del estilo original por un factor relativo (`\fscxyr`, `\fscxr`, `\fscyr`, `\fsr`).
  * **Estocásticos Deterministas (`R`):** Generación aleatoria por unidad (`\cR`, `\1cR`..`\4cR`, `\alphaR`, `\1aR`..`\4aR`, `\fscxyR`, `\frzR`, `\bordR`, `\shadR`, `\bsR`, `\blurR`, `\fsR`, `\fspR`).

### 9.4. Sinergias y Buenas Prácticas
* **Modulación Paramétrica:** Cablear puertos numéricos (`Basics/Number` o `Basics/Math`) a `\fscx`, `\fscy` o `\frz` para centralizar transformaciones de escala o giros sin manipulación manual de cadenas.
* **Ensamblado Directo:** Conectar la salida `String` de múltiples nodos `MultiTag` a un nodo `Basics/Concatenate` con separador `nil` para construir el bloque de sobreescritura `{\...}` final antes de la salida de renderizado.

---

## 10. Nodo `Basics/Only` (Derivación y Filtrado Condicional)

* **Categoría Canónica:** `Basics` (UI: *Básicos / Only*)
* **Propósito:** Enruta o filtra flujos de datos según una condición lógica evaluada contra las variables métricas del contexto ASS activo.

![Basics/Only](img/only_a.png)

### 10.1. Encabezado y Modos Operativos
1. **`[2.1] Mode` (`mode`):** Conmuta la topología de puertos del nodo:
   * `select` (*Selector / Ternario 2 $\to$ 1*): Dispone de dos puertos de entrada (`True`, `False`) y una salida (`Out`). Si la condición es verdadera, emite el dato de `True`; si es falsa, emite el de `False`.
   * `split` (*Desviador 1 $\to$ 2*): Dispone de un puerto de entrada (`In`) y dos salidas (`True`, `False`). Si la condición es verdadera, canaliza el dato hacia `True` y emite cadena vacía `""` en `False`; si es falsa, emite `""` en `True` y canaliza el dato hacia `False`.

![Basics/Only (Filter Mode)](img/only_b.png)

### 10.2. Puertos según Modo Operativo

#### Modo `select` (2 $\to$ 1)
* **Entradas:**
  * `True`: Dato emitido si la condición se cumple.
  * `False`: Dato emitido si la condición no se cumple.
* **Salidas:**
  * `[1.1] Out`: Valor seleccionado según el resultado de la condición.

#### Modo `split` (1 $\to$ 2)
* **Entradas:**
  * `In`: Flujo de datos a derivar.
* **Salidas:**
  * `[1.1] True`: Emite el dato de entrada si la condición es verdadera; emite `""` si es falsa.
  * `[1.2] False`: Emite el dato de entrada si la condición es falsa; emite `""` si es verdadera.

### 10.3. Controles y Propiedades del Cuerpo
1. **`[2.2] Condition` (`condition`):** Expresión lógica evaluada en cada iteración (ej. `char.i == 1`, `syl.duration > 300`, `j % 2 == 0`, `'kanji' in line.tags_str`). Defecto: `"True"`.

### 10.4. Modelo Lógico de Evaluación

$$\text{Modo select:} \quad \text{Out} = \begin{cases} \text{Input}(\text{True}) & \text{si } \text{eval}(\text{condition}) = \text{True} \\ \text{Input}(\text{False}) & \text{si } \text{eval}(\text{condition}) = \text{False} \end{cases}$$

$$\text{Modo split:} \quad (\text{Out}_{\text{True}}, \text{Out}_{\text{False}}) = \begin{cases} (\text{Input}, \texttt{""}) & \text{si } \text{eval}(\text{condition}) = \text{True} \\ (\texttt{""}, \text{Input}) & \text{si } \text{eval}(\text{condition}) = \text{False} \end{cases}$$

### 10.5. Sinergias y Buenas Prácticas
* **Diferenciación de Carácter Inicial:** Configurar `condition: char.i == 1` para aplicar un tamaño ampliado (`\fs40`) o color especial exclusivamente a la primera letra de cada palabra o línea.
* **Alternancia Cromática Par/Impar:** En modo `select`, alimentar dos colores distintos en `True` y `False` con `condition: char.i % 2 == 0` para generar patrones de texto bicolor coordinados.

---

## 11. Nodo `Basics/Once` (Evaluación Única con Caché por Ámbito)

* **Categoría Canónica:** `Basics` (UI: *Básicos / Once*)
* **Propósito:** Retiene en caché el valor de su entrada para evitar reevaluaciones en un mismo ámbito de ejecución (línea, palabra, sílaba, carácter o sub-bucle).

![Basics/Once](img/once.png)

### 11.1. Encabezado y Modos de Ámbito
1. **`[2.1] Mode` (`mode`):** Nivel de jerarquía y ciclo de vida de la memoria caché:
   * `global`: Se evalúa una sola vez para toda la ejecución de la macro sobre el script.
   * `line`: Se evalúa una vez al inicio de cada línea de diálogo.
   * `word`: Se evalúa una vez al inicio de cada palabra.
   * `syl`: Se evalúa una vez al inicio de cada sílaba de karaoke.
   * `char`: Se evalúa una vez por cada carácter.
   * `loop`: Se evalúa una vez por cada ciclo del sub-bucle especificado en `iterator` (defecto: `j`).

### 11.2. Puertos de Entrada (*Inputs*)
1. **`In`:** Entrada de datos cuyo resultado se desea memorizar (ej. trazados vectoriales procedentes de `Text to Shape`, `IMG to Shape` o selecciones de color).

### 11.3. Controles y Propiedades del Cuerpo
1. **`[2.2] Iterator` (`iterator`):** Nombre de la variable de iteración a monitorizar cuando `mode = "loop"` (defecto: `"j"`).

### 11.4. Puertos de Salida (*Outputs*)
1. **`[1.1] Out`:** Emite el valor almacenado en caché sin reevaluar el subgrafo conectado a la entrada.

### 11.5. Arquitectura de Caché y Hashing de Ámbito
El motor construye una clave de caché unívoca compuesta por el identificador del nodo y la clave del ámbito activo:

$$\text{CacheKey} = \langle \text{NodeID}, \, \text{ScopeKey} \rangle$$

Donde $\text{ScopeKey}$ se genera según el modo activo:
* `global` $\to \texttt{"global"}$
* `line` $\to \texttt{"line\_" + LineID}$
* `word` $\to \texttt{"line\_" + LineID + "\_word\_" + WordID}$
* `syl` $\to \texttt{"line\_" + LineID + "\_syl\_" + SylID}$
* `char` $\to \texttt{"line\_" + LineID + "\_char\_" + CharID}$
* `loop` $\to \texttt{"line\_" + LineID + "\_loop\_" + IteratorName + "\_" + IteratorValue}$

Si $\text{CacheKey}$ existe en memoria, devuelve el resultado almacenado en tiempo $\mathcal{O}(1)$, omitiendo el cómputo de la rama conectada aguas arriba.

### 11.6. Sinergias y Buenas Prácticas
* **Aceleración de Renderizado Vectorial (`Text to Shape`):** Conectar un nodo `Once (mode: char)` a la salida de `Text to Shape` al generar efectos multicapa con `MaxLoop` o `Shape/Array`. Esto previene la rasterización repetida del glifo en cada iteración del bucle, procesando la forma una sola vez por carácter.
* **Valores Aleatorios Homogéneos por Sílaba:** Intercalar `Once (mode: syl)` tras un generador estocástico para asegurar que todos los fragmentos o partículas derivados de una misma sílaba compartan el mismo valor numérico aleatorio.


---

## 12. Nodo `Basics/Builder` (Ensamblador Monolínea de Bloques con Sub-Bucle)

* **Categoría Canónica:** `Basics` (UI: *Básicos / Constructor*)
* **Propósito:** Ensambla múltiples fragmentos de texto o piezas vectoriales dentro de **una única línea de diálogo ASS**. Presenta entradas ampliables con puerto fijo superior `Tags` y puertos de datos `In1`, `In2`, ... dinámicos (ampliables mediante botones `+` y `-`). Permite controlar mediante `Reset \r` si cada bloque se aísla con barreras `\r` (reinyectando animaciones globales en cada sub-bloque) o si se emite como un único trazo continuo `\p1` donde los bloques intermedios reciben sobreescrituras estáticas de estilo (como degradados `\1c` o variaciones de borde/alpha) sin reiniciar el modo de dibujo, deduplicando automáticamente transformaciones temporales (`\t(...)`) de nodos previos como `Animation`.

![Basics/Builder](img/builder.png)

### 12.1. Botones de Modo y Sub-Modo
1. **Botón de Encabezado (`TEXT` / `SHAPE` — propiedad `mode`):**
   * `text`: Ensambla fragmentos de texto (sílabas, caracteres, palabras, repeticiones o listas personalizadas) en una sola línea.
   * `shape`: Ensambla múltiples piezas de dibujo vectorial (`\p1`) con neutralización automática del avance de cursor inline de libass.
2. **Selector Secundario de Cabecera (`SPLIT` / `MULTI` / `CUSTOM` — propiedad `sub_mode`):**
   * `splitter` (`SPLIT`): Divide la fuente de texto por sílabas, caracteres o palabras (en modo `text`), o descompone una figura compuesta en sub-formas individuales (en modo `shape`).
   * `multi` (`MULTI`): Clona el texto o la forma de entrada `repeat` veces dentro de la misma línea ASS, permitiendo dar un color, escala o desfase distinto a cada copia usando `bu_i`.
   * `custom` (`CUSTOM`): Toma una lista de textos o formas separadas por un delimitador (`delim`) y ensambla cada elemento como un bloque independiente.

### 12.2. Puertos de Entrada y Salida

| Dirección | Puerto | Tipo | Descripción |
| :--- | :--- | :--- | :--- |
| **Entrada 0** | `Tags` | `data` | Puerto fijo superior. Etiquetas ASS (o cadena conectada de nodos como `Color Gradient`, `MultiTag` o `Interpolator`) que se reevalúan en cada bloque usando `bu_i`, `bu_n` y `max_bu`. |
| **Entradas 1+** | `In1`, `In2`, ... | `data` | Puertos ampliables dinámicamente (`+` / `-`). Reciben las piezas de texto o formas vectoriales a ensamblar. Cada entrada conectada aporta su propia pieza preservando huecos y contornos originales. |
| **Salida 0** | `Return` | `data` | Cadena monolínea final lista para conectarse al puerto `Text` de `System/Output`. |
| **Salida 1** | `Items Out` | `data` | Lista nativa de las piezas extraídas antes de inyectar las etiquetas, útil para alimentar otros nodos en paralelo. |

### 12.3. Controles Contextuales del Cuerpo

| Propiedad | Visible en | Opciones / Tipo | Descripción |
| :--- | :--- | :--- | :--- |
| `split_by` | `text` + `splitter` | `syl`, `char`, `word` | Unidad en la que se divide el texto (por sílabas, letras o palabras). |
| `source` | `text` + (`splitter` o `multi`) sin cables en `In` | `active_unit`, `line`, `text_field` | Indica si el texto se extrae de la unidad activa del bucle principal, de toda la línea o del campo manual. |
| `repeat` | `multi` | Expresión numérica (`2` por defecto) | Cantidad de copias generadas en la misma línea. Acepta números o fórmulas matemáticas. |
| `custom_text` | `custom` sin cables en `In` | Plantilla de texto o dibujos | Lista de elementos separados por el delimitador elegido (ej. `Uno, Dos, Tres`). |
| `delim` | `custom` | `,`, `;`, `\|`, `newline`, `space` | Separador utilizado para dividir los elementos en modo `custom`. |
| `shape_split_mode` | `shape` + `splitter` | `subpaths`, `islands`, `raw_subpaths` | Método de separación geométrica: `subpaths` conserva los huecos internos (como el interior de las letras `O`, `A`, `B`) unidos a su contorno padre; `islands` funde polígonos con Clipper; `raw_subpaths` corta de forma directa en cada comando `m`. |
| `shape_layout` | `shape` | `auto`, `embedded_pos`, `advance`, `stack` | Compensación espacial entre piezas: `auto` detecta coordenadas `\pos` embebidas o apila; `embedded_pos` traslada cada pieza según su `\pos(x,y)` respecto a la primera; `advance` deja que las formas avancen una al lado de otra; `stack` superpone todas las piezas en el mismo origen `(0,0)`. |
| `inject_r` | Todos | Botón cíclico (`ON` / `OFF`) | Control de barrera `\r`. Si está en `ON`, separa cada bloque con `\r` y reinyecta animaciones y tags globales. Si está en `OFF`, mantiene un trazado continuo `\p1`, coloca las transformaciones `\t(...)` una sola vez en la cabecera e inyecta únicamente sobreescrituras estáticas de estilo (`\1c`, `\3c`, `\alpha`, `\bord`, etc.) entre piezas. |

### 12.4. Variables del Sub-Bucle Interno (`bu_i`, `bu_n`, `max_bu`)
Mientras `Builder` construye la línea pieza por pieza, inyecta tres variables locales que cualquier nodo conectado a su puerto `Tags` puede leer:
* **`bu_i`**: Número de la pieza actual (empezando en `1`, `2`, `3`...).
* **`bu_n`** y **`max_bu`**: Cantidad total de piezas ensambladas en el nodo.
* **Aleatoriedad por pieza (`by.bu_i.R(min, max)`)**: Permite generar valores aleatorios distintos pero estables para cada bloque de la línea (ej. `\frz(by.bu_i.R(-15, 15))`).
* **Prioridad de escala en modo `shape`**: Por defecto, `Builder` inserta `\p1\fscx100\fscy100` en cada bloque de dibujo para evitar que el tamaño de fuente del estilo distorsione las figuras. Si conectas tu propio `\fscx`, `\fscy` o `\fscxy` en `Tags`, tu escala reemplaza automáticamente el valor `100` por defecto.

### 12.5. Sinergias y Buenas Prácticas
* **Reemplazo de `Concatenate` (modo merge) y `Union & Divide` (modo fusión):**
  * Para unir varias formas vectoriales independientes conservando sus huecos y posiciones relativas, conecta cada figura a un puerto `In` de `Builder` (`In1`, `In2`, etc.).
  * Si deseas un degradado de color continuo sin reiniciar el trazo vectorial ni cortar los bordes, desactiva `Reset \r` (`OFF`) y envía el degradado por el puerto superior `Tags`.
  * Si tus formas vienen animadas desde `Functions/Animation` (por ejemplo, con un desvanecimiento `\alpha` y curvas `\t`), `Builder` detecta las transformaciones temporales entrantes, las deduplica en la cabecera y asegura que todas las piezas se animen en perfecta sincronía.
