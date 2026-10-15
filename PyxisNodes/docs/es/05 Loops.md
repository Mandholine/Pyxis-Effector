# Loops

La categoría **Loops** contiene los nodos que controlan el dominio de iteración de las líneas de diálogo (`syl`, `char`, `word`, `line`), la multiplicación de sub-bucles temporales o fotograma a fotograma (FBF) y el cálculo de progresión normalizada.

---

## 1. Nodo `Loops/Main Loop` (Iterador Principal del Dominio)

* **Categoría Canónica:** `Loops` (UI: *Bucles / Main Loop*)
* **Propósito:** Define el dominio elemental sobre el cual se descompone y procesa cada línea de diálogo seleccionada de Aegisub (`syl`, `char`, `word`, `line`), inicializando el ciclo de vida del grafo y emitiendo la señal de flujo y los contadores métricos de iteración.

```
┌────────────────────────────────────────────────────────┐
│ [Loops] Main Loop               [NO BLANK] [syl ▼]    │
├────────────────────────────────────────────────────────┤
│ (No inputs)                        Loop  [loop] ──────►│
│                            Iterator (i)  [data] ──────►│
│                               Total (N)  [data] ──────►│
├────────────────────────────────────────────────────────┤
│                      syl.i, syl.n                      │
└────────────────────────────────────────────────────────┘
```

### 1.1. Modos de Cabecera (*Header Badges*)
1. **Selector de Dominio (`iterator`):** Conmutable mediante clic directo en el badge superior derecho o en sus propiedades:
   * `syl`: Itera sílaba a sílaba respetando las marcas de tiempo de karaoke (`\k`, `\kf`, `\ko`, `\K`).
   * `char`: Itera glifo a glifo de forma individual, calculando métricas tipográficas para cada carácter.
   * `word`: Itera palabra por palabra delimitadas por espacios en blanco.
   * `line`: Itera una única vez para la línea de diálogo completa como una entidad única.
2. **Tratamiento de Espacios (`blank_mode` / `noblank`):** Conmutable mediante el badge adyacente:
   * `no_blank` (*NO BLANK / Ignorar Espacios*): Omite automáticamente los caracteres de espacio, tabulaciones y saltos de línea. Los contadores de iteración reflejan únicamente elementos visibles ($ci$ y $cn$).
   * `with_blanks` (*WITH BLANK / Todos*): Procesa e itera sobre la totalidad de caracteres, asignando índices e intervalos de tiempo a los espacios en blanco ($i$ y $n$).

### 1.2. Puertos de Salida (*Outputs*)
1. **`[1.1] Loop`:** Emite la señal de flujo de ejecución que sincroniza la cadena de nodos downstream para cada unidad elemental del dominio activo.
2. **`[1.2] Iterator (i)`:** Índice numérico ordinal de la unidad actual dentro del conjunto de la línea (base 1: $1 \dots N$). Inyectado en el contexto como `i`, `syl.i`, `char.i` o `word.i`.
3. **`[1.3] Total (N)`:** Cantidad total de elementos calculados para el dominio activo en la línea correspondiente. Inyectado como `N`, `syl.n`, `char.n` o `word.n`.

### 1.3. Detalle Algorítmico e Inyección de Contexto
Al evaluar cada línea de diálogo de Aegisub, el nodo construye las estructuras métricas y contextuales de la unidad activa:
* **Indexación según espacios:**
  * En modo `no_blank`: $i \leftarrow ci$, $N \leftarrow cn$, garantizando que los índices no tengan saltos numéricos producidos por espacios en blanco.
  * En modo `with_blanks`: $i \leftarrow i_{\text{abs}}$, $N \leftarrow n_{\text{abs}}$, preservando el orden absoluto en la cadena original.
* **Métricas espaciales proyectadas:**
  Calcula y publica las coordenadas cartesianas de la unidad en píxeles:
  `center`, `middle`, `left`, `right`, `top`, `bottom`, `width`, `height`, `x`, `y`.
* **Intervalo temporal:**
  Define los límites $[t_{\text{start}}, t_{\text{end}}]$ y la duración $t_{\text{dur}} = t_{\text{end}} - t_{\text{start}}$ de la sílaba o carácter.
* **Variables globales inyectadas:**
  `i`, `n`, `fx_i`, `fx_n`, junto con el objeto de datos correspondiente (`syl`, `char`, `word` o `line`).

### 1.4. Ejemplo Práctico de Producción
* **Desplazamiento Parabólico Escalonado por Sílaba:**
  Conectando `Loop` al puerto `Loop / Domain` de `System/Output` y configurando `iterator: syl`:
  
  ```
  [Main Loop: syl] ──► Loop ──► [System/Output]
                   ──► Iterator (i)
                   ──► Total (N)
  ```
  
  En un nodo de tags conectado a `Output (Tags)`:
  ```
  {\pos(syl.center, syl.middle - 20)\k(syl.dur / 10)}
  ```
  
  Para una línea con $N = 5$ sílabas, la tercera sílaba ($i = 3$) alcanzará la elevación máxima:
  $$\Delta y = -25 \cdot \sin\left(\pi \cdot \frac{2}{4}\right) = -25 \text{ px}$$

---

## 2. Nodo `Loops/MaxLoop` (Multiplicador de Sub-bucles y Generador FBF)

* **Categoría Canónica:** `Loops` (UI: *Bucles / MaxLoop*)
* **Propósito:** Multiplica y expande el flujo de ejecución entrante dentro del elemento activo en $N$ sub-iteraciones temporales o copias concurrentes (`normal`), o segmenta el intervalo temporal en fotogramas discretos regulares (`fbf`).

```
┌────────────────────────────────────────────────────────┐
│ [Loops] MaxLoop                            [NORMAL ▼]  │
├────────────────────────────────────────────────────────┤
│ ► [loop] Loop In                 Loop Out  [loop] ────►│
│                                   Counter  [data] ────►│
│   Iterations (N): [ 3        ]      Total  [data] ────►│
│   Var Name (j):   [ j        ]                         │
├────────────────────────────────────────────────────────┤
│                         j, maxj                        │
└────────────────────────────────────────────────────────┘

┌────────────────────────────────────────────────────────┐
│ [Loops] MaxLoop                               [FBF ▼]  │
├────────────────────────────────────────────────────────┤
│ ► [loop] Loop In                 Loop Out  [loop] ────►│
│ ► [data] Start                    Counter  [data] ────►│
│ ► [data] End                        Total  [data] ────►│
│   Step (ms):    [ 41.7     ]                           │
│   Inicio (ms):  [ start_time]                          │
│   Fin (ms):     [ end_time  ]                          │
│   Var Name (j): [ j        ]                           │
├────────────────────────────────────────────────────────┤
│                         j, maxj                        │
└────────────────────────────────────────────────────────┘
```

### 2.1. Modos de Cabecera y Reconfiguración Dinámica
El modo operativo se selecciona mediante el botón interactivo de la cabecera:
1. **`normal` (*NORMAL*):**
   * Multiplica la evaluación del sub-grafo downstream en $N$ repeticiones concurrentes.
   * Mantiene invariantes los tiempos de inicio y fin originales del elemento base (`start_time`, `end_time`).
   * Puertos de entrada activos: `Loop In`.
   * Propiedades visibles: `iterations` (defecto: `"3"`), `var_name` (defecto: `"j"`).
2. **`fbf` (*Frame by Frame*):**
   * Divide el intervalo temporal $[Start, End]$ en fotogramas uniformes de paso `step_ms`.
   * Puertos de entrada activos: `Loop In`, `Start`, `End`.
   * Propiedades visibles: `step_ms` (defecto: `"41.7"` $\approx 23.976\text{ fps}$), `start_time` (defecto: `"start_time"`), `end_time` (defecto: `"end_time"`), `var_name` (defecto: `"j"`).

### 2.2. Puertos de Entrada (*Inputs*)
1. **`Loop In`:** Señal de flujo proveniente de `Main Loop` o de otro sub-bucle previo.
2. **`Start` (Modo `fbf`):** Marca de tiempo inicial en milisegundos. Si no está conectado, evalúa la propiedad `start_time` o el valor del contexto activo (`start_time`).
3. **`End` (Modo `fbf`):** Marca de tiempo final en milisegundos. Si no está conectado, evalúa la propiedad `end_time` o el valor del contexto activo (`end_time`).

### 2.3. Controles y Propiedades del Cuerpo
1. **`[2.1] Iterations (N)` (`iterations`):** Cantidad total de repeticiones en modo `normal`. Admite expresiones matemáticas evaluables.
2. **`[2.2] Step (ms)` (`step_ms`):** Duración de cada fotograma en modo `fbf` (mínimo: $1.0\text{ ms}$).
3. **`[2.3] Inicio (ms)` (`start_time`):** Expresión temporal inicial por defecto en modo `fbf`.
4. **`[2.4] Fin (ms)` (`end_time`):** Expresión temporal final por defecto en modo `fbf`.
5. **`[2.5] Var Name` (`var_name`):** Identificador de la variable de iteración inyectada al contexto local (defecto: `"j"`).

### 2.4. Puertos de Salida (*Outputs*)
1. **`[1.1] Loop Out`:** Emite la señal de flujo multiplicada hacia los nodos receptores del sub-grafo.
2. **`[1.2] Counter`:** Índice ordinal de la sub-iteración activa ($1 \dots N$).
3. **`[1.3] Total`:** Conteo total de iteraciones programadas ($N$).

### 2.5. Modelo Matemático y Temporal
* **Modo Normal:**
  El nodo itera para cada $j \in [1, N]$. Cada evaluación preserva el intervalo $[t_{\text{start}}, t_{\text{end}}]$ del elemento y define:
  $$\text{var\_name} = j, \quad \text{var\_name\_max} = N, \quad \text{fx\_i} = j, \quad \text{fx\_n} = N$$
* **Modo FBF (Cuadro a Cuadro):**
  A partir de $Start$, $End$ y $\Delta t = step\_ms$, calcula el total de fotogramas:
  $$N = \left\lceil \frac{End - Start}{\Delta t} \right\rceil$$
  Para cada cuadro $k \in [1, N]$:
  $$t_{\text{start}}^{(k)} = Start + (k - 1) \cdot \Delta t$$
  $$t_{\text{end}}^{(k)} = \min(End, Start + k \cdot \Delta t)$$
  $$t_{\text{dur}}^{(k)} = t_{\text{end}}^{(k)} - t_{\text{start}}^{(k)}$$
  Se actualizan en el contexto local las variables de tiempo `st`, `et`, `start_time`, `end_time`, `frame_start_time`, `frame_end_time`, `frame_dur`, `fd`, `fx_start_time`, `fx_end_time`, `fx_dur` y se activa la bandera `in_fbf_loop = True`.

### 2.6. Ejemplos Prácticos de Producción
* **Ejemplo 1 (Modo Normal): Extrusión de Sombras por Capas:**
  Configuración: `mode: normal`, `iterations: 4`, `var_name: j`.
  Genera 4 capas desplazadas con atenuación progresiva de opacidad:
  ```
  {\pos(syl.center + j * 1.5, syl.middle + j * 1.5)\1c&H000000&\1a&H80&\3a&HFF&}
  ```
  Para $j = 1$, el desplazamiento es $(1.5, 1.5)$; para $j = 4$, es $(6.0, 6.0)$, produciendo una sombra direccional densa.

* **Ejemplo 2 (Modo FBF): Coordenadas por Fotograma sin `\t`:**
  Configuración: `mode: fbf`, `step_ms: 41.7`, `var_name: j`.
  Cada línea emitida representa un único fotograma de vídeo con coordenadas exactas:
  ```
  {\pos(syl.center + j * 4, syl.middle)\alpha&H00&}
  ```

---

## 3. Nodo `Loops/Module` (Muestreo Modular y Progreso Normalizado)

* **Categoría Canónica:** `Loops` (UI: *Bucles / Module*)
* **Propósito:** Calcula el factor de progresión lineal normalizada en el rango $[0.0, 1.0]$ o divisiones con desplazamiento modular a partir de contadores ordinales de iteración ($i, j$).

```
┌────────────────────────────────────────────────────────┐
│ [Loops] Module                                         │
├────────────────────────────────────────────────────────┤
│ ► [data] Iterator (i)                    Data  [data] ─►│
│ ► [data] Total (N)                                     │
│ ► [data] Sub-step (m)                                  │
│   Iterator (i):  [ i        ]                          │
│   Total (N):     [ N        ]                          │
│   Sub-step (m):  [ 0        ]                          │
└────────────────────────────────────────────────────────┘
```

### 3.1. Puertos de Entrada (*Inputs*)
1. **`Iterator (i)`:** Índice actual de la iteración. Si no está conectado, evalúa la propiedad `iter`.
2. **`Total (N)`:** Cantidad total de elementos de referencia. Si no está conectado, evalúa la propiedad `total`.
3. **`Sub-step (m)`:** Desplazamiento o compensación fraccionaria. Si no está conectado, evalúa la propiedad `sub_m`.

### 3.2. Controles y Propiedades del Cuerpo
1. **`[2.1] Iterator (i)` (`iter`):** Expresión o identificador del índice (defecto: `"i"`).
2. **`[2.2] Total (N)` (`total`):** Expresión o identificador del total (defecto: `"N"`).
3. **`[2.3] Sub-step (m)` (`sub_m`):** Expresión del valor de desplazamiento (defecto: `"0"`).

### 3.3. Puertos de Salida (*Outputs*)
1. **`[1.1] Data`:** Valor numérico resultante de la progresión normalizada.

### 3.4. Detalle Algorítmico y Formulación Matemática
El nodo evalúa numéricamente los tres operandos ($i, N, m$) en el contexto activo y aplica:

$$\text{Denominador} = N + m - 1.0$$

$$\text{Data} = \begin{cases} \dfrac{i - 1.0 + m}{\text{Denominador}} & \text{si } \text{Denominador} \neq 0 \text{ y } N > 1.0 \\ m & \text{en cualquier otro caso} \end{cases}$$

#### Formato Numérico de Salida:
1. El resultado se redondea a 4 cifras decimales: $R = \text{round}(\text{Data}, 4)$.
2. Si $R$ es un número entero exacto, se formatea sin punto decimal (ej. `0` o `1`).
3. Si incluye parte fraccionaria, se serializa con un máximo de 4 decimales, eliminando ceros no significativos a la derecha (ej. `0.25`, `0.3333`).

#### Comportamiento con $m = 0$:
Para $i = 1 \dots N$ con $N > 1$:
* Primer elemento ($i = 1$): $\text{Data} = \frac{0}{N - 1} = 0$
* Último elemento ($i = N$): $\text{Data} = \frac{N - 1}{N - 1} = 1$
* El valor emitido divide el intervalo unitario $[0.0, 1.0]$ en $N - 1$ segmentos uniformes.

### 3.5. Ejemplos Prácticos de Producción
* **Modulación de Curvas Easing sobre Escala:**
  Conectando `Data` al puerto de entrada de una fórmula cuadrática o al nodo `Basics/Math (Category: easing)` para transformar una distribución espacial de caracteres en una escala no lineal:
  
  ```
  [Main Loop: char] ──► Iterator (i) ──► [Module] ──► Data ──► [Tags]
                    ──► Total (N)    ──►
  ```
  
  Conectando `Data` a la propiedad `Tags`:
  ```
  {\fscx(100 + Data * 50)\fscy(100 + Data * 50)}
  ```
  Para el primer carácter ($Data = 0.0$), la escala es `\fscx100\fscy100`. Para el carácter medio en $N = 5$ ($Data = 0.5$), la escala alcanza `\fscx125\fscy125`, y para el último ($Data = 1.0$), `\fscx150\fscy150`.
