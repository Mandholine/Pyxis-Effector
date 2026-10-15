# Basics

La categoría **Basics** reúne los nodos dedicados a la generación, transformación, formateo y enrutamiento de datos primitivos (números, cadenas, colores, expresiones matemáticas y condicionales) para la construcción de efectos en subtítulos ASS.

---

## 1. Nodo `Basics/Number` (Constante Numérica y Expresiones)

* **Categoría Canónica:** `Basics` (UI: *Básicos / Number*)
* **Propósito:** Emite un valor numérico escalar (entero o punto flotante), evaluando constantes, variables del contexto ASS y expresiones algebraicas en tiempo real.

![Basics/Number](img/number.png)

### 1.1. Puertos de Salida (*Outputs*)
1. **`[1.1] Number`:** Emite el valor numérico evaluado como cadena de texto. Si el valor resultante es un entero exacto, se formatea sin decimales (ej. `10`); si contiene decimales, se trunca a un máximo de 4 decimales significativos sin ceros redundantes a la derecha (ej. `12.5`).

### 1.2. Controles y Propiedades del Cuerpo
1. **`[2.1] Value` (`value`):** Campo de entrada editable. Acepta números directos (`100`, `-45.2`), variables del contexto ASS (`syl.x`, `line.width`, `j`, `i`, `char.n`) o expresiones matemáticas (`syl.width / 2 + 10`, `sin(j * 0.1) * 50`).

### 1.3. Evaluación Dinámica de Expresiones
El campo `value` se procesa dinámicamente en cada ciclo de iteración:
* Si el texto contiene identificadores registrados en el contexto (`syl`, `line`, `char`, `video_fps`, etc.), el evaluador sustituye sus valores numéricos antes del cálculo.
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
1. **`[2.1] Text` (`value`):** Cadena de texto editable. Admite texto plano, secuencias de salto y espaciado ASS (`\N`, `\h`), bloques de etiquetas (`{\an5\bord0\shad0}`) o trazados vectoriales (`m 0 0 l 100 0 100 100 0 100`). Si el texto incluye bloques entre llaves `{\...}`, el evaluador de cadenas de Pyxis resuelve directamente expresiones y variables contextuales dentro de los paréntesis de cada tag (ej. `{\pos(syl.center, syl.middle)}` o `\fscx(100 + 20 * i)`) preservando el texto literal circundante.

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
* **Comprobación Condicional de Texto:** Utilizar la operación `contains` conectada a `Basics/Switch` para bifurcar rutas de estilo según palabras clave presentes en el diálogo.

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

## 5. Nodo `Basics/Math` (Motor Matemático y Curvas)

* **Categoría Canónica:** `Basics` (UI: *Básicos / Math*)
* **Propósito:** Evalúa operaciones aritméticas, trigonométricas, curvas de aceleración (*easing*), oscilaciones periódicas y utilidades de rango estructuradas en 8 familias de cálculo.

![Basics/Math](img/math.png)

### 5.1. Encabezado y Modos de Cabecera
1. **`[2.1] Category` (`category`):** Selector desplegable de la familia matemática:
   * `basic`: Aritmética elemental y álgebra.
   * `trig`: Trigonometría directa, inversa y conversiones angulares.
   * `rounding`: Redondeo al entero más próximo, suelo y techo.
   * `clamping`: Acotación estricta de rangos y comparaciones.
   * `easing`: Curvas de aceleración y desaceleración normalizadas ($t \in [0.0, 1.0]$).
   * `waves`: Osciladores continuos de onda periódica.
   * `random`: Generación pseudoaleatoria con soporte de semilla determinista.
   * `utilities`: Mapeo lineal de rangos e interpolación escalar.
2. **`[2.2] Operation` (`operation`):** Función específica a ejecutar dentro de la familia seleccionada.

### 5.2. Puertos de Entrada (*Inputs*)
1. **`A`:** Operando principal, factor de progreso $t$, ángulo o valor base. Si permanece desconectado, toma el valor numérico configurado en la propiedad interna.
2. **`B`:** Operando secundario, límite superior, frecuencia o valor objetivo.

### 5.3. Puertos de Salida (*Outputs*)
1. **`[1.1] Out`:** Valor escalar resultante. Si el resultado es un entero exacto, se formatea sin decimales (ej. `25`); si es fraccionario, se emite con un máximo de 4 decimales significativos (ej. `0.7071`).

### 5.4. Desglose de las 8 Familias Matemáticas

#### 5.4.1. Familia `basic` (Aritmética)
* **`add` ($A + B$):** Suma algebraica.
* **`sub` ($A - B$):** Resta aritmética.
* **`mul` ($A \cdot B$):** Multiplicación.
* **`div` ($A / B$):** División protegida (emite `0.0` si $B = 0$).
* **`mod` ($A \pmod B$):** Residuo de división entera (emite `0.0` si $B = 0$).
* **`pow` ($A^B$):** Potenciación.
* **`abs` ($|A|$):** Valor absoluto.
* **`neg` ($-A$):** Inversión de signo aritmético.

#### 5.4.2. Familia `trig` (Trigonometría)
Las funciones trigonométricas directas (`sin`, `cos`, `tan`) esperan el ángulo $A$ en **grados sexagesimales** ($0^\circ \dots 360^\circ$) para coincidir con la convención de rotación en subtítulos ASS (`\frz`, `\frx`, `\fry`). Las funciones inversas devuelven el resultado directamente en grados.

* **`sin`:** $\sin\left(\frac{A \cdot \pi}{180}\right)$
* **`cos`:** $\cos\left(\frac{A \cdot \pi}{180}\right)$
* **`tan`:** $\tan\left(\frac{A \cdot \pi}{180}\right)$
* **`asin` / `arcsin`:** $\arcsin(\text{clamp}(A, -1, 1)) \cdot \frac{180}{\pi} \in [-90^\circ, 90^\circ]$
* **`acos` / `arccos`:** $\arccos(\text{clamp}(A, -1, 1)) \cdot \frac{180}{\pi} \in [0^\circ, 180^\circ]$
* **`atan` / `arctan`:** $\arctan(A) \cdot \frac{180}{\pi} \in (-90^\circ, 90^\circ)$
* **`atan2`:** $\text{atan2}(Y, X) \cdot \frac{180}{\pi}$ con $Y = A$ y $X = B$, en rango $[-180^\circ, 180^\circ]$
* **`rad` / `radians`:** Convierte grados a radianes: $A \cdot \frac{\pi}{180}$.
* **`deg` / `degrees`:** Convierte radianes a grados: $A \cdot \frac{180}{\pi}$.

#### 5.4.3. Familia `rounding` (Redondeo)
* **`round`:** Redondea $A$ al entero más próximo.
* **`floor`:** Mayor entero menor o igual ($\lfloor A \rfloor$).
* **`ceil`:** Menor entero mayor o igual ($\lceil A \rceil$).

#### 5.4.4. Familia `easing` (Curvas de Progresión)
Recibe un factor de progreso $t = \text{clamp}(A, 0.0, 1.0)$ y devuelve el valor transformado en $[0.0, 1.0]$:

* **`ease_in`:** Aceleración cuadrática inicial: $f(t) = t^2$.
* **`ease_out`:** Desaceleración cuadrática final: $f(t) = 1 - (1 - t)^2$.
* **`ease_in_out`:** Aceleración y desaceleración combinadas:
  $$f(t) = \begin{cases} 2t^2 & \text{si } t < 0.5 \\ 1 - \frac{(-2t + 2)^2}{2} & \text{si } t \ge 0.5 \end{cases}$$
* **`cubic_in`:** Aceleración cúbica: $f(t) = t^3$.
* **`cubic_out`:** Desaceleración cúbica: $f(t) = 1 - (1 - t)^3$.
* **`expo`:** Progresión exponencial: $f(t) = 2^{10(t - 1)}$ para $t > 0$.
* **`elastic`:** Oscilación elástica amortiguada.
* **`bounce`:** Rebote segmentado en 4 impactos progresivos.
* **`back`:** Anticipación o sobreimpulso balístico: $f(t) = (c_1 + 1)t^3 - c_1 t^2$ con $c_1 = 1.70158$.

#### 5.4.5. Familia `waves` (Osciladores Periódicos)
Genera oscilaciones temporales continuas a partir de $t = A$, frecuencia $f = \text{freq}$, amplitud $A_{\text{amp}} = \text{amp}$ y desfase $\text{Offset}$:

* **`sine`:** $y(t) = A_{\text{amp}} \cdot \sin(2\pi \cdot f \cdot t) + \text{Offset}$
* **`square`:** Emite $+A_{\text{amp}} + \text{Offset}$ durante el semiciclo positivo y $-A_{\text{amp}} + \text{Offset}$ en el negativo.
* **`triangle`:** Rampa bidireccional continua: para $\phi = (t \cdot f) \pmod 1$, $y(t) = A_{\text{amp}} \cdot (2|2\phi - 1| - 1) + \text{Offset}$.
* **`sawtooth`:** Rampa lineal ascendente con reinicio instantáneo: para $\phi = (t \cdot f) \pmod 1$, $y(t) = A_{\text{amp}} \cdot (2\phi - 1) + \text{Offset}$.

#### 5.4.6. Familias `utilities` y `clamping`
* **`clamp`:** Acota $A$ en el intervalo $[\text{Min}, \text{Max}]$.
* **`lerp`:** Interpolación lineal entre $A$ y $B$ según $t \in [0.0, 1.0]$: $\text{lerp}(A, B, t) = A + (B - A) \cdot t$.
* **`map_range`:** Mapeo proporcional de $A$ desde $[\text{MinIn}, \text{MaxIn}]$ hacia $[\text{MinOut}, \text{MaxOut}]$.
* **`min` / `max`:** Compara $A$ y $B$ devolviendo el valor mínimo o máximo.
* **`random`:** Generador pseudoaleatorio uniforme en $[\text{Min}, \text{Max}]$ con semilla opcional (`Seed`).

### 5.5. Sinergias y Buenas Prácticas
* **Modulación de Oscilación en Rotación ASS:** Conectar la salida `waves/sine` directamente a un campo `\frz` en `Basics/Dynamic Format` para producir balanceo armónico (ej. `\frz(%s)` con amplitud de $10^\circ$).
* **Interpolación No Lineal de Escalas:** Conectar el puerto `Out` de una curva `easing/ease_out` a los puertos `\fscx` y `\fscy` de `Basics/MultiTag` para animar entradas suaves desde 0% hasta 100%.

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

## 7. Nodo `Basics/Concatenate` (Concatenador Extensible y Modo Zip)

* **Categoría Canónica:** `Basics` (UI: *Básicos / Concatenate*)
* **Propósito:** Ensambla múltiples fragmentos de texto, etiquetas ASS o comandos vectoriales en una cadena unificada mediante separador configurable o entrelazado paralelo (modo `zip`).

![Basics/Concatenate](img/concatenate.png)

### 7.1. Puertos de Entrada y Expansión Dinámica
* **`In1`, `In2`, $\dots$, `InN`:** Puertos de entrada secuenciales. Al conectar o añadir puertos mediante el botón `(+)`, el nodo agrega ranuras adicionales de forma continua.
* **Precedencia:** Si un puerto no tiene cable de enlace conectado, el nodo toma el valor escrito manualmente en su campo de texto inline.

### 7.2. Puertos de Salida (*Outputs*)
1. **`[1.1] String`:** Cadena de texto resultante tras ensamblar las entradas activas.

### 7.3. Modos de Separador (`separator`)

| Separador (`separator`) | Carácter Inyectado | Propósito / Caso de Uso |
| :--- | :---: | :--- |
| `nil` / `none` / `""` | *(Ninguno)* | Unión continua directa (ej. fusión de tags en bloque `\pos(X,Y)\blur2\1c&HFFFFFF&`). |
| `space` / `" "` | Espacio | Separación de palabras o secuencias de coordenadas en instrucciones ASSdraw (`m 0 0 l 10 10`). |
| `comma` / `","` | Coma `,` | Construcción de listas delimitadas para nodos de paleta o arrays de valores. |
| `semicolon` / `";"` | Punto y coma `;` | Agrupación de especificaciones de datos o scripts. |
| `newline` / `"\n"` | Salto de línea | Generación de múltiples líneas de subtítulos o bloques de texto apilados. |
| `zip` | *(Entrelazado)* | Algoritmo de combinación paralela posicional para listas de valores. |

### 7.4. Algoritmo de Entrelazado Paralelo (*Vector Zip*)
Cuando `separator` se configura en `zip`, el nodo trata cada entrada como una lista de elementos separados por comas y los combina elemento a elemento:

$$\text{In}_1 = [A_1, A_2, A_3], \quad \text{In}_2 = [B_1, B_2, B_3] \implies \text{Out} = [A_1 B_1, \, A_2 B_2, \, A_3 B_3]$$

1. Descompone cada entrada activa en una secuencia de tokens.
2. Si el campo inline de un puerto contiene un prefijo de tag (ej. `\1c`, `\blur`), lo antepone a cada token individual de esa lista.
3. Empareja los elementos posición a posición hasta alcanzar la longitud de la lista más corta con más de un elemento, emitiendo una lista de keyframes fusionados delimitada por comas.

### 7.5. Sinergias y Buenas Prácticas
* **Ensamblado Limpio de Bloques ASS:** Configurar `separator` en `nil` para fusionar salidas de `MultiTag` o cadenas directas sin insertar espacios accidentales que puedan alterar el renderizado de libass.
* **Construcción de Keyframes Vectorizados:** Emplear el modo `zip` combinando una lista de colores de `Functions/Color Gradient` con una lista de opacidades para alimentar secuencias de transformación por fotograma.

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

2. **Acceso al Catálogo de Tags:**
   * Al pulsar dos veces sobre el cuerpo del nodo o hacer clic en la píldora de modo en la cabecera se abre el selector modal con el catálogo completo de etiquetas ASS organizadas por familias funcionales (*Posicionamiento, Cinemática, Colorimetría, Alfa, Escalas, Bordes, Tipografía, Karaoke*).

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
* **Tipografía y Disposición:** `\an`, `\fs`, `\fsp`, `\q`.

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

