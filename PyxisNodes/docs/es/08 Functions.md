# Functions

La categoría **Functions** contiene 16 nodos especializados en la manipulación algebraica de etiquetas ASS, generación de osciladores, evaluación condicional, gradientes cromáticos, cinemática y deformación vectorial.

### Organización Temática del Volumen:
* **Sección 8.A — Modulación de Tags, Osciladores y Lógica Condicional:** [`Tag Manipulator`](#1-nodo-functionstag-manipulator-manipulador-de-tags) (§1), [`Tag Oscillator`](#2-nodo-functionstag-oscillator-oscilador-de-tags) (§2), [`Glitter`](#3-nodo-functionsglitter-generador-estocástico-de-destellos) (§3), [`Conditioner`](#4-nodo-functionsconditioner-condicionador-lógico) (§4), [`Animation`](#8-nodo-functionsanimation-animación-fbf-y-modulación-alfa) (§8).
* **Sección 8.B — Gradientes Cromáticos, Ráster a Píxeles y Cinemática:** [`Color Gradient`](#5-nodo-functionscolor-gradient-gradiente-de-color-multicapa) (§5), [`Clip Gradient`](#6-nodo-functionsclip-gradient-bandas-y-mallas-de-recorte-para-degradados) (§6), [`IMG to pixels`](#7-nodo-functionsimg-to-pixels-muestreo-ráster-a-partículas) (§7), [`Polar to Cartesian`](#12-nodo-functionspolar-to-cartesian-conversor-polar-a-cartesiano) (§12), [`Interpolator`](#14-nodo-functionsinterpolator-interpolador-paramétrico-polimórfico) (§14).
* **Sección 8.C — Curvas Bézier, Emisión de Partículas y Tipografía Vectorial:** [`Bezier Curve`](#9-nodo-functionsbezier-curve-curvas-y-splines-bézier-2d) (§9), [`Move Tag`](#10-nodo-functionsmove-tag-cinemática-y-trayectorias-de-movimiento-ass) (§10), [`Move Text`](#11-nodo-functionsmove-text-movimiento-cinemático-tipográfico-coordinado) (§11), [`Particles`](#13-nodo-functionsparticles-enjambres-de-partículas-vectoriales) (§13), [`Text on Path`](#15-nodo-functionstext-on-path-texto-adaptado-sobre-curvas) (§15), [`Text to Shape`](#16-nodo-functionstext-to-shape-vectorización-tipográfica-de-glifos) (§16).

---

## 1. Nodo `Functions/Tag Manipulator` (Manipulador de Tags)

* **Categoría Canónica:** `Functions` (UI: *Funciones / Tag Manipulator*)
* **Propósito:** Realiza transformaciones algebraicas sobre cadenas de etiquetas ASS, incluyendo la inversión negativa de parámetros (colores complementarios, alfas invertidos, rotaciones opuestas, máscaras inversas), reseteo de etiquetas a los valores por defecto del estilo ASS activo del contexto, e introspección/extracción de valores numéricos y literales de cualquier tag específico.

![Functions/Tag Manipulator](img/tag_manipulator.png)

### 1.1. Encabezado y Modos de Cabecera (*Header Mode Combos*)
1. **`Mode` (`mode`):** Selector desplegable interactivo que conmuta el comportamiento operativo del nodo y reconfigura dinámicamente sus entradas y salidas:
   * **`invert` (INV):** Invierte algebraicamente cada etiqueta ASS contenida en la entrada (incluso dentro de bloques `\t(...)`).
   * **`reset` (RESET):** Lee el estilo de subtítulo activo en el contexto y genera las etiquetas de reseteo a sus valores base predeterminados.
   * **`extractor` (EXTRACT):** Inspecciona la cadena de tags entrante, busca la última aparición de la etiqueta especificada en `Target Tag` y extrae su valor limpio, su representación numérica y su bloque original completo.

---

### 1.2. Puertos de Entrada y Propiedades del Cuerpo (*Inputs & Properties*)

#### En Modos `invert` (INV) y `reset` (RESET):
1. **`Tags In` (`tags`):** Cadena de texto que contiene las etiquetas ASS a procesar. Acepta etiquetas estáticas directas (ej. `\frz45\1c&H0000FF&\alpha&H80&`), transformaciones continuas (ej. `\t(0,300,\frz-45\fscx150)`), o el valor `"all"` / vacío en modo Reset para regenerar todo el estilo base. (Defecto: `""`).

#### En Modo `extractor` (EXTRACT):
1. **`Tags In` (`tags`):** Cadena de etiquetas ASS desde donde se extraerá la información (ej. `{\pos(320,240)\frz-35.5\1c&H00FF88&}`).
2. **`Target Tag` (`target_tag`):** Nombre identificador de la etiqueta a buscar (con o sin barra invertida `\`). Soporta alias canónicos ASS como `frz` / `fr`, `1c` / `c`, `alpha`, `fscx`, `pos`, `org`, `clip`, `blur`, etc. (Defecto: `"frz"`).

---

### 1.3. Puertos de Salida (*Outputs*)

#### En Modos `invert` (INV) y `reset` (RESET):
1. **`[1.1] Tags Out`:** Cadena de texto resultante con las etiquetas ASS transformadas algebraicamente o restablecidas al estilo base.

#### En Modo `extractor` (EXTRACT):
1. **`[1.1] String`:** Valor textual limpio extraído de la etiqueta sin la cabecera del tag ni paréntesis (ej. `"-35.5"`, `"320,240"`, `"&H00FF88&"`).
2. **`[1.2] Value`:** Conversión numérica en coma flotante (`float`) del valor extraído. Si el valor es de coordenadas compuestas (ej. `320,240`), devuelve el primer componente numérico (`320.0`). Si es un canal de color o alfa hexadecimal de 1 o 2 dígitos, lo convierte a su entero decimal correspondiente ($0 \dots 255$).
3. **`[1.3] Raw String`:** Fragmento literal completo del tag coincidente tal como se encontró en la cadena de entrada (ej. `\frz-35.5`, `\pos(320,240)`).

---

### 1.4. Detalle Algorítmico y Álgebra de Tags ASS

#### 1.4.1. Reglas de Inversión Algebraica (`Mode: invert`)

El algoritmo analiza la cadena léxica, descompone bloques atómicos y aplica las siguientes reglas formales de simetría matemática:

| Familia de Tags ASS | Etiquetas Soportadas | Regla de Inversión Matemática | Ejemplo Entrada $\to$ Salida |
| :--- | :--- | :--- | :--- |
| **Colores Primario y Secundarios** | `\c`, `\1c`, `\2c`, `\3c`, `\4c` | **Complementario RGB Negativo:**<br>$(R', G', B') = (255 - R, 255 - G, 255 - B)$ | `\1c&H0000FF&` $\to$ `\1c&HFFFF00&` (Azul $\to$ Amarillo) |
| **Canales Alfa** | `\alpha`, `\1a`, `\2a`, `\3a`, `\4a` | **Complemento Hexadecimal:**<br>$\alpha' = 255 - \alpha$ | `\alpha&H00&` $\to$ `\alpha&HFF&` (Opaco $\to$ Transparente) |
| **Rotaciones, Cizallamiento y Sombras** | `\frz`, `\frx`, `\fry`, `\fr`, `\fax`, `\fay`, `\fsp`, `\xshad`, `\yshad` | **Inversión de Signo Aritmético:**<br>$V' = -V$ | `\frz35` $\to$ `\frz-35`<br>`\fax0.5` $\to$ `\fax-0.5` |
| **Bordes, Difuminado y Sombras Escalares** | `\bord`, `\xbord`, `\ybord`, `\blur`, `\be`, `\shad` | **Anulación / Reseteo a Cero:**<br>$V' = 0$ | `\bord4\blur3` $\to$ `\bord0\blur0` |
| **Escalas de Transformación** | `\fscx`, `\fscy` | **Retorno a Escala Base:**<br>$V' = \text{Style.Scale}$ (o $100\%$) | `\fscx200` $\to$ `\fscx100` |
| **Máscaras Vectoriales de Recorte** | `\clip`, `\iclip` | **Conmutación de Máscara Inversa:**<br>`\clip` $\longleftrightarrow$ `\iclip` | `\clip(m 0 0 ...)` $\to$ `\iclip(m 0 0 ...)` |

#### 1.4.2. Inversión Recursiva en Bloques de Tiempo `\t(...)`
Cuando la cadena contiene bloques temporales `\t(t1, t2, [accel,] tags)`, el analizador aísla el cuerpo interior de etiquetas, aplica la inversión algebraica exclusivamente a los comandos internos y recombina el bloque sin alterar los intervalos de tiempo ni la curva de aceleración:

$$\text{\textbackslash t}(100, 400, 1.5, \text{\textbackslash frz45\textbackslash 1c\&H0000FF\&}) \quad \longrightarrow \quad \text{\textbackslash t}(100, 400, 1.5, \text{\textbackslash frz-45\textbackslash 1c\&HFFFF00\&})$$

#### 1.4.3. Reseteo a Estilo Base (`Mode: reset`)
El motor consulta la referencia `styleref` del contexto activo (`active_unit` o `line`) y extrae los valores configurados en el archivo ASS de Aegisub:
* Si `Tags In` está vacío, `"all"` o `"todo"`, genera la secuencia integral de reseteo:
  $$\text{\textbackslash 1c}\dots\text{\textbackslash 2c}\dots\text{\textbackslash 3c}\dots\text{\textbackslash 4c}\dots\text{\textbackslash 1a}\dots\text{\textbackslash 2a}\dots\text{\textbackslash 3a}\dots\text{\textbackslash 4a}\dots\text{\textbackslash alpha\&H00\&}\text{\textbackslash fscx}\dots\text{\textbackslash fscy}\dots\text{\textbackslash fs}\dots\text{\textbackslash fsp}\dots\text{\textbackslash bord}\dots\text{\textbackslash shad}\dots\text{\textbackslash frz}\dots$$
* Si `Tags In` contiene etiquetas específicas (ej. `\1c\fscx`), genera únicamente los valores de reseteo para los tags solicitados.

---

### 1.5. Sinergias y Buenas Prácticas
* **Creación de Efectos Espejo y Simetría:** En bucles dobles o partículas que rebotan hacia ambos lados, alimentar una rama con los tags directos y la otra rama pasando por `Tag Manipulator (INV)` para invertir automáticamente ángulos `\frz`, inclinación `\fax` y posición relativa de sombra.
* **Extracción de Coordenadas para Cinemáticas:** Conectar la salida `String` de un `Tag Manipulator (EXTRACT)` con `Target Tag: pos` hacia un nodo `Math` para derivar trayectorias relativas basadas en la posición original del glifo.

### 1.6. Ejemplo Práctico de Producción
* **Reflejo Bilateral de Transformaciones con Modo Invert:**
  Alimentando dos capas simultáneas para generar una estela simétrica opuesta sin recalcular fórmulas manuales:

  ```
  [Basics/MultiTag: \frz30\fscx120] ──► Tags In ──► [System/Output (Layer 2)]
                 │
                 └──► Tags In ──► [Functions/Tag Manipulator: mode=invert] ──► Tags Out ──► [System/Output (Layer 1)]
  ```

  * **Capa 2 (Directa):** Emite `{\an5\pos(syl.center, syl.middle)\frz30\fscx120}`.
  * **Capa 1 (Invertida):** Emite `{\an5\pos(syl.center, syl.middle)\frz-30\fscx100}`, invirtiendo la rotación a $-30^\circ$ y restaurando la escala a $100\%$ de forma automática.

---

## 2. Nodo `Functions/Tag Oscillator` (Oscilador de Tags)

* **Categoría Canónica:** `Functions` (UI: *Funciones / Tag Oscillator*)
* **Propósito:** Generador continuo de modulaciones periódicas, estroboscópicas, rítmicas o por ondas sobre cualquier propiedad ASS. Compila secuencias temporales en bloques `\t(...)` coordinados a lo largo del intervalo de vida del elemento.

![Functions/Tag Oscillator](img/tag_oscillator.png)

### 2.1. Encabezado y Modos de Cabecera (*Header Mode Combos*)
1. **`Oscillation Mode` (`mode`):** Determina la forma y comportamiento de la transición temporal:
   * **`wave` (Onda Continua - Defecto):** Transición suave y continua entre los estados de la lista de tags ($T_{\text{trans}} = S_i$).
   * **`steps` / `flashes` / `strobe` (Paso / Estroboscópico):** Cambios instantáneos y discretos sin interpolación intermedia ($t_2 = t_1 + 1$).
   * **`pulses` (Pulsos):** Modulación donde la transición ocupa el $50\%$ del paso y el resto se mantiene estático.
   * **`rhythmic` (Rítmico):** Los pasos de tiempo no son uniformes, sino que se leen secuencialmente de una lista de milisegundos en `Rhythm Pattern`.
   * **`noise` (Ruido):** Variación de paso con fluctuaciones pseudoaleatorias.
2. **`Order Mode` (`order_mode`):** Controla el orden de selección de la lista de tags provista:
   * **`sequential` (Secuencial - Defecto):** Recorre la lista de tags en orden cíclico ($0, 1, 2, \dots, N-1, 0, 1, \dots$).
   * **`pingpong` (Rebote):** Avanza y retrocede alternativamente ($0, 1, 2, 1, 0, 1, \dots$).
   * **`random` (Aleatorio):** Selecciona un tag al azar en cada paso utilizando una semilla estocástica determinista.
   * **`shuffle` (Aleatorio sin Repetición Inmediata):** Elige pseudoaleatoriamente garantizando no repetir el mismo tag en pasos consecutivos.

---

### 2.2. Puertos de Entrada y Propiedades del Cuerpo (*Inputs & Properties*)
1. **`Start Time` (`start_time`):** Instante inicial del oscilador en milisegundos relativos a la línea física. Si se deja vacío, toma `0.0 ms`. (Defecto: `""`).
2. **`End Time` (`end_time`):** Instante final del oscilador en ms. Si se deja vacío, toma automáticamente la duración del elemento activo (`fx.dur`, `syl.duration` o `line.duration`). (Defecto: `""`).
3. **`Step (ms)` (`step_ms`):** Duración de cada ciclo o paso en milisegundos. (Defecto: `200.0`).
4. **`Trans (ms)` (`trans_ms`):** Tiempo que tarda en realizar la interpolación `\t` hacia el nuevo tag. (Defecto: `50.0`).
5. **`Duty Cycle` (`duty_cycle`):** Factor de ciclo de trabajo en el rango $[0.01, 1.0]$. Cuando se conecta o rellena, sobrescribe a `Trans (ms)` calculando $T_{\text{trans}} = S_i \cdot \text{DutyCycle}$.
6. **`Tags` (`tags`):** Lista de cadenas de tags separadas por coma o salto de línea (ej. `\frz30\fry20, \frz-20\fry-20` o `\1c&HFF0000&, \1c&H00FF00&, \1c&H0000FF&`).
7. **`Accel` (`accel`):** Exponente de aceleración ASS inyectado en cada bloque `\t(...)`. (Defecto: `1.0`).
8. **`Dilate Step` (`dilat_step_ms`):** Factor aditivo que dilata o comprime progresivamente el paso en cada iteración: $S_i = S_0 + \Delta_{S} \cdot i$. (Defecto: `0.0`).
9. **`Dilate Trans` (`dilat_trans_ms`):** Factor aditivo que dilata o contrae la transición en cada iteración: $T_i = T_0 + \Delta_{T} \cdot i$. (Defecto: `0.0`).
10. **`Seq Offset` (`offset_seq_ms`):** Pausa temporal adicional inyectada al completar un ciclo completo de la lista de tags. (Defecto: `0.0`).
11. **`Rhythm Pattern` (`rhythm_pattern`):** Lista de duraciones separadas por comas (ej. `100, 50, 200, 100`) para generar patrones rítmicos y sincopados en modo `rhythmic`.

---

### 2.3. Puertos de Salida (*Outputs*)
1. **`[1.1] Tag Out`:** Cadena continua de bloques ASS compilados `\t(t1, t2, [accel,] tags)` que cubre todo el intervalo temporal del elemento.
2. **`[1.2] Current Val`:** Etiqueta activa evaluada puntualmente en el fotograma o tiempo actual del contexto (`frame_time` o `fx_start_time`).
3. **`[1.3] Keyframes`:** Estructura de datos (lista de tuplas) con todos los fotogramas clave calculados `[(t1, t2, tag_str, accel), ...]`.
4. **`[1.4] Values`:** Lista simple de los estados de texto de tags evaluados en cada paso.

---

### 2.4. Formulación Algorítmica y Cinemática

```
Modo: wave (Transición Continua)
Tags: [ Tag A, Tag B ]
───┬─────────────┬─────────────┬─────────────┬─────────────► Tiempo (ms)
   │ \t(0,200,B) │\t(200,400,A)│\t(400,600,B)│\t(600,800,A)│
   0            200           400           600           800

Modo: steps / strobe (Conmutación Instantánea)
───┬─────────────┬─────────────┬─────────────┬─────────────► Tiempo (ms)
   │ \t(0,1,B)   │ \t(200,201,A) \t(400,401,B)│ \t(600,601,A)
   0            200           400           600           800
```

#### 2.4.1. Cálculo del Paso y Transición por Iteración ($i$)
Para cada paso $i \ge 0$:
1. **Paso Temporal ($S_i$):**
   $$S_i = \begin{cases} \text{RhythmPattern}[i \pmod M] & \text{si } \text{rhythm\_pattern} \ne \emptyset \\ \max(5.0, S_{\text{step}} + \Delta_{\text{dilate\_step}} \cdot i) & \text{en otro caso} \end{cases}$$
2. **Ventana de Transición ($T_i$):**
   $$T_i = \begin{cases} 0 & \text{si es modo } \text{steps/strobe/flashes} \\ S_i \cdot \text{clamp}(DC, 0.01, 1.0) & \text{si se definió } \text{DutyCycle} \\ \min(S_i, \max(0.0, T_{\text{trans}} + \Delta_{\text{dilate\_trans}} \cdot i)) & \text{en modo estándar} \end{cases}$$
3. **Generación de Marcas de Tiempo:**
   $$t_1 = \text{round}(T_{\text{start}} + t_{\text{curr}}), \quad t_2 = \begin{cases} t_1 + 1 & \text{si } T_i \le 0 \\ \min(t_{\text{end}}, \text{round}(t_1 + T_i)) & \text{en otro caso} \end{cases}$$

---

### 2.5. Sinergias y Buenas Prácticas
* **Efecto de Temblor (*Jitter*) u Oscilación Angular:** Conectar en `Tags` los valores `\frz-5, \frz5` con `Step: 60` y `Trans: 30` para generar un vibrato continuo en la sílaba cantada.
* **Palpitar al Ritmo de la Música:** Configurar `Mode: rhythmic` e ingresar en `Rhythm Pattern` los intervalos de milisegundos extraídos de los transitorios del audio (`125, 250, 125, 375`).

### 2.6. Ejemplo Práctico de Producción
* **Vibrato Cinemático de Ángulo y Escala en Sostenidos:**
  Generando una ondulación armónica continua sobre el glifo durante toda la duración de la sílaba ($300\text{ ms}$):

  ```
  [Functions/Tag Oscillator: mode=wave, step_ms=80, trans_ms=40] ──► Tag Out ──► Tags ──► [System/Output]
     tags: "\frz-4\fscy95, \frz4\fscy105"
  ```

  * **Bloques ASS Generados en `Tag Out`:**
    ```ass
    \t(0,40,\frz-4\fscy95)\t(80,120,\frz4\fscy105)\t(160,200,\frz-4\fscy95)\t(240,280,\frz4\fscy105)
    ```
  * Interpola suavemente entre inclinaciones $\mp 4^\circ$ y compresiones/elongaciones del $95\%$ al $105\%$, coordinando la animación automáticamente con el tiempo de canto.

---

## 3. Nodo `Functions/Glitter` (Generador Estocástico de Destellos)

* **Categoría Canónica:** `Functions` (UI: *Funciones / Glitter*)
* **Propósito:** Emisor estocástico asincrónico para generar destellos de brillo (*flashes*), pulsaciones luminosas, oleajes o variaciones de ruido sobre múltiples propiedades ASS simultáneamente, simulando resplandores orgánicos y destellos de purpurina sin patrones repetitivos predecibles.

![Functions/Glitter](img/glitter.png)

### 3.1. Encabezado y Modos de Cabecera (*Header Mode Combos*)
1. **`Mode` (`mode` / `random_profile`):** Selecciona la envolvente temporal y morfología de las partículas estocásticas:
   * **`flashes` (Destello Rápido - Defecto):** Pausa aleatoria larga $\to$ ataque ultra-rápido ($1 \dots 3\text{ ms}$) $\to$ sostenimiento corto ($5 \dots 15\text{ ms}$) $\to$ decaimiento largo ($40 \dots 100\text{ ms}$). Ideal para chispas y purpurina.
   * **`pulses` (Pulsaciones):** Pausa moderada $\to$ subida progresiva ($150 \dots 250\text{ ms}$) $\to$ sostenimiento $\to$ bajada simétrica con aceleración no lineal.
   * **`waves` / `oleaje` (Oleaje Suave):** Transiciones lentas y continuas de subida y bajada ($250 \dots 400\text{ ms}$) sin pausas pronunciadas.
   * **`noise` (Ruido Estocástico):** Pasos ultra-cortos ($15 \dots 50\text{ ms}$) con valores aleatorios directos por fotograma.

---

### 3.2. Puertos de Entrada y Propiedades del Cuerpo (*Inputs & Properties*)
1. **`Start Time` (`start_time`):** Instante inicial del efecto en milisegundos. (Defecto: `"0"`).
2. **`End Time` (`end_time`):** Instante final en ms o expresión contextual (ej. `"fx.dur"`). (Defecto: `"fx.dur"`).
3. **`Density` (`density`):** Factor multiplicador de frecuencia estocástica. Valores $> 1.0$ reducen el tiempo entre pausas generando mayor cantidad de destellos por segundo; valores $< 1.0$ espacian los eventos. (Defecto: `1.0`).
4. **`Seed` (`seed`):** Semilla entera que garantiza la reproducibilidad pseudoaleatoria determinista en cada renderizado. (Defecto: `0`).
5. **Entradas Expandibles de Pistas (`In 1`, `In 2`, ...):** Cada pista define una terna compuesta por:
   * **`Tag` (`tag_k`):** Etiqueta ASS a animar (ej. `\fscx`, `\1c`, `\blur`, `\alpha`, `\frz`).
   * **`Min` (`min_k`):** Valor base inferior (número, porcentaje, color hexadecimal `#RRGGBB` o `&HBBGGRR&`).
   * **`Max` (`max_k`):** Valor cúspide superior al alcanzar el destello máximo.

#### Soporte de "Dark Tags" Compuestos
`Glitter` reconoce y descompone automáticamente etiquetas agrupadas (*Dark Tags*):
* `\fscxy` $\longrightarrow$ anima en paralelo `\fscx` y `\fscy` con el mismo valor.
* `\frxyz` $\longrightarrow$ anima en paralelo `\frx`, `\fry` y `\frz`.
* `\134c` $\longrightarrow$ sincroniza los colores primario (`\1c`), borde (`\3c`) y sombra (`\4c`).
* `\xybord` $\longrightarrow$ expande a `\xbord` y `\ybord`.
* `\bs` $\longrightarrow$ modula conjuntamente borde `\bord` y sombra `\shad`.

---

### 3.3. Puertos de Salida (*Outputs*)
1. **`[1.1] List`:** Cadena concatenada combinada con todos los bloques `\t(...)` de todas las pistas sincronizadas en los mismos instantes temporales.
2. **`[1.2] TAG 1`:** Cadena con los bloques `\t(...)` generados exclusivamente para la primera pista de tags.
3. **`[1.3] TAG 2` (Expandible):** Cadena con los bloques `\t(...)` de la segunda pista, y así sucesivamente para cada pista conectada.

---

### 3.4. Detalle Algorítmico y Modelo de Envolvente Estocástica

```
Envolvente del Perfil: flashes (Destello)
Valor Max (Cúspide) ─────┐       /───\
                         │      /     \
                         │     /       \
Valor Base (Reposo) ─────┴────/         \──────────────
                         ▲    ▲ ▲     ▲ ▲
                         │    │ │     │ │
                         └──┬─┘ └─┬─┘ └─┬────────┘
                         Pausa   Ataque Decaimiento
                         (dens)  (1-3ms)(40-100ms)
```

1. **Generación Determinista por Unidad:**
   La semilla del generador pseudoaleatorio se indexa unívocamente por el glifo o sílaba activa ($i$):
   $$\text{Seed}_{\text{local}} = \text{Seed} \cdot 1000 + i + 1337$$
2. **Interpolación Cromática Estocástica:**
   Si los límites `Min` y `Max` corresponden a colores, el algoritmo descompone los canales $(R_1, G_1, B_1)$ y $(R_2, G_2, B_2)$ e interpola en el espacio de color RGB:
   $$R_{\text{rand}} = \text{round}(R_1 + (R_2 - R_1) \cdot \text{Factor}), \quad G_{\text{rand}} = \text{round}(G_1 + (G_2 - G_1) \cdot \text{Factor})$$
   Emitiendo el código de color en formato ASS `&HBBGGRR&`.

---

### 3.5. Sinergias y Buenas Prácticas
* **Efecto de Chispa Mágica / Purpurina:** Conectar en `In 1` el tag `\fscxy` con rango `(100, 160)` y en `In 2` el tag `\1c` con rango `(#FFFFFF, #FFE460)`. Conectar la salida `List` a `Output` para lograr destellos de escala y color dorado simultáneos.

### 3.6. Ejemplo Práctico de Producción
* **Destellos Dorados y Micro-Escalado Aleatorio (*Golden Sparkle Flash*):**
  Generando ráfagas asincrónicas sobre caracteres individuales a lo largo de una duración de $400\text{ ms}$:

  ```
  [Functions/Glitter: mode=flashes, density=1.5, start=0, end=400] ──► List ──► Tags ──► [System/Output]
     In 1: tag=\fscxy, min=100, max=140
     In 2: tag=\1c, min=#FFFFFF, max=#FFD700
  ```

  * **Bloques ASS Emitidos en `List`:**
    El nodo interpola los canales RGB del color y descompone el Dark Tag `\fscxy`, generando secuencias deterministas como:
    ```ass
    \t(83,85,\fscx133\fscy133\1c&H00D7FF&)\t(93,173,\fscx105\fscy105\1c&HFFFFFF&)\t(208,211,\fscx133\fscy133\1c&H00D7FF&)...
    ```
  * Cada glifo recibe micro-destellos en instantes de tiempo desfasados según su índice, evitando patrones de parpadeo artificiales o repetitivos.

---

## 4. Nodo `Functions/Conditioner` (Condicionador Lógico)

* **Categoría Canónica:** `Functions` (UI: *Funciones / Conditioner*)
* **Propósito:** Evaluador condicional reactivo inline ($A \text{ if } \text{Cond} \text{ else } B$). Permite bifurcar el flujo de datos para alternar entre dos valores de texto, bloques de etiquetas ASS, valores numéricos o listas completas basándose en expresiones lógicas evaluadas sobre el contexto del subtítulo.

![Functions/Conditioner](img/conditioner.png)

### 4.1. Puertos de Entrada y Propiedades del Cuerpo (*Inputs & Properties*)
1. **`Condition` (`condition`):** Expresión condicional booleana. Acepta constantes booleanas (`True`, `False`, `1`, `0`), comparaciones numéricas (`syl.i % 2 == 0`, `char.i > 3`), operadores de pertenencia (`line.style == "Romaji"`, `'kanji' in line.tags_str`), o cables booleanos. (Defecto: `"True"`).
2. **`If True` (`if_true`):** Dato a emitir cuando la condición se evalúa como verdadera ($C = \text{True}$). Puede ser una cadena de tags ASS, número, lista o cable conectado. (Defecto: `""`).
3. **`If False` (`if_false`):** Dato a emitir cuando la condición se evalúa como falsa ($C = \text{False}$). (Defecto: `""`).

---

### 4.2. Puertos de Salida (*Outputs*)
1. **`[1.1] Out`:** El valor resultante seleccionado según la evaluación de la condición. Si el dato de entrada seleccionado es una lista o tupla, el nodo une automáticamente sus elementos separados por comas `, `.

---

### 4.3. Detalle Algorítmico y Evaluación del Contexto

El evaluador ejecuta la expresión de manera segura en un entorno aislado donde se inyectan todas las variables métricas y de estado del contexto ASS:

| Variable Inyectada | Tipo | Descripción |
| :--- | :---: | :--- |
| `syl.i`, `char.i`, `word.i`, `fx.i`, `j`, `i` | `int` | Índice secuencial del elemento activo ($0$-based o $1$-based). |
| `syl.n`, `char.n`, `word.n`, `line.n` | `int` | Cantidad total de elementos en el grupo de iteración. |
| `line.style`, `line.actor`, `line.effect` | `str` | Metadatos de la línea de diálogo original. |
| `line.duration`, `syl.duration`, `fx.dur` | `float` | Duraciones en milisegundos. |
| `syl.text`, `char.text` | `str` | Contenido del texto o fonema del glifo activo. |

#### Regla de Evaluación:
$$\text{Out} = \begin{cases} \text{If True} & \text{si } \text{eval}(\text{Condition}, \text{Context}) = \text{True} \\ \text{If False} & \text{en cualquier otro caso} \end{cases}$$

---

### 4.4. Sinergias y Buenas Prácticas
* **Alternancia Cromática / Efecto Tablero:** Conectar en `Condition` la expresión `syl.i % 2 == 0`, en `If True` el color `\1c&H00FFFF&` (Cian) y en `If False` el color `\1c&HFF00FF&` (Magenta) para alternar el color de cada sílaba.
* **Tratamiento Diferencial para Puntuación o Espacios:** Usar `Condition: char.text.strip() == ""` para anular transformaciones cinemáticas pesadas en caracteres invisibles.

### 4.5. Ejemplo Práctico de Producción
* **Bicolor Escalonado por Paridad de Carácter (*Even/Odd Bicolor Stagger*):**
  Ruteando estilos de color y escala alternos para cada letra dentro del bucle maestro de caracteres:

  ```
  [Loops/Main Loop: char] ──► char.i ───────────────────────────────┐
                                                                    ▼
  [Functions/Conditioner: condition="char.i % 2 == 0"] ──► Out ──► Tags ──► [System/Output]
     If True:  "\1c&H00FFFF&\fscxy110"
     If False: "\1c&HFF0088&\fscxy90"
  ```

  * **Resultado ASS en el Subtítulo:**
    * **Caracteres pares ($i \in \{2, 4, 6\}$):** Emiten `{\an5\pos(char.center, char.middle)\1c&H00FFFF&\fscx110\fscy110}`.
    * **Caracteres impares ($i \in \{1, 3, 5\}$):** Emiten `{\an5\pos(char.center, char.middle)\1c&HFF0088&\fscx90\fscy90}`.
  * Bifurca el flujo de renderizado en un solo nodo sin duplicar capas ni generar llamadas vacías.

---

## 5. Nodo `Functions/Color Gradient` (Gradiente de Color Multicapa)

* **Categoría Canónica:** `Functions` (UI: *Funciones / Color Gradient*)
* **Propósito:** Genera e interpola transiciones suaves entre múltiples paradas de color (*multi-stop color gradient*), aplicando curvas de aceleración no lineal (*easing*). Permite evaluar colores puntuales en una posición $t \in [0.0, 1.0]$ o generar listas completas de colores y etiquetas ASS para asignación secuencial sobre caracteres, sílabas o partículas.

![Functions/Color Gradient](img/color_gradient.png)

### 5.1. Puertos de Entrada y Propiedades del Cuerpo (*Inputs & Properties*)
1. **`Progress (0-1)` (`prog`):** Factor de posición de interpolación $t \in [0.0, 1.0]$. Acepta constantes numéricas, cables o expresiones dinámicas del contexto (ej. `char.i / char.n`, `syl.i / syl.n`, `j / maxloop`). (Defecto: `"char.i / char.n"`).
2. **`Color List` (`colors_str`):** Cadena con la lista de paradas de color separadas por comas, espacios o saltos de línea. Acepta códigos hexadecimales web (`#RRGGBB`), nombres HTML o códigos ASS (`&HBBGGRR&`). (Defecto: `"#95E648,#3E750C,#ED38CA"`).
3. **`Total (N)` (`total`):** Cantidad total de divisiones requeridas cuando se consumen las salidas en lote (`Color List` o `Tags`). Si $N > 1$, el nodo genera $N$ muestras distribuidas uniformemente entre $t=0.0$ y $t=1.0$. (Defecto: `"1"`).
4. **`Accel` (`accel`):** Exponente de aceleración no lineal para la curva de interpolación. Un valor de `1.0` produce interpolación lineal uniforme; valores $> 1.0$ concentran la transición al final (*ease-in*); valores $< 1.0$ concentran la transición al inicio (*ease-out*). (Defecto: `"1.0"`).
5. **`Tag` (`tag_type`):** Selector de etiqueta ASS inyectada como prefijo en la salida `Tags` (`\1c`, `\2c`, `\3c`, `\4c` o `\c`). (Defecto: `"\1c"`).

---

### 5.2. Puertos de Salida (*Outputs*)
1. **`[1.1] ASS Color`:** Código de color ASS puntual `&HBBGGRR&` evaluado en el progreso $t$ configurado en `Progress (0-1)`.
2. **`[1.2] Color List`:** Lista de códigos de color ASS separados por coma `, ` para los $N$ pasos si $N > 1$, o el color puntual si $N = 1$.
3. **`[1.3] Tags`:** Cadena con el prefijo de etiqueta ASS inyectado a cada color (ej. `\1c&H48E695&` si $N=1$, o `\1c&H48E695&, \1c&H0C753E&, \1c&HCADB38&` si $N > 1$).

---

### 5.3. Detalle Algorítmico y Modelo Matemático

```
Paradas:  C1 (#95E648)          C2 (#3E750C)          C3 (#ED38CA)
          ├──────────────────────────┼──────────────────────────┤
Progreso: t = 0.0                  t = 0.5                  t = 1.0
Segmento: └────── Segmento 0 ───────┘└────── Segmento 1 ───────┘
```

#### 5.3.1. Curva de Relajación no Lineal (*Easing / Accel*)
Antes de la interpolación cromática, el progreso de entrada $t \in [0.0, 1.0]$ se modula mediante la función de aceleración exponencial:

$$t_{\text{eased}} = \begin{cases} t^{\text{accel}} & \text{si } \text{accel} > 1.0 \\ 1.0 - (1.0 - t)^{1.0 / \text{accel}} & \text{si } 0.0 < \text{accel} < 1.0 \\ t & \text{si } \text{accel} = 1.0 \end{cases}$$

#### 5.3.2. Mapeo Multi-Segmento e Interpolación RGB
Si la lista contiene $K$ colores de parada $\{C_0, C_1, \dots, C_{K-1}\}$:
1. Se calculan $K-1$ sub-segmentos continuos:
   $$\text{pos} = t_{\text{eased}} \cdot (K - 1), \quad \text{idx} = \min(K - 2, \lfloor \text{pos} \rfloor), \quad t_{\text{local}} = \text{pos} - \text{idx}$$
2. Se extraen los canales RGB de los dos colores adyacentes $C_{\text{idx}} = (R_1, G_1, B_1)$ y $C_{\text{idx}+1} = (R_2, G_2, B_2)$.
3. Se calcula la interpolación lineal por canal:
   $$R = \text{round}(R_1 + (R_2 - R_1) \cdot t_{\text{local}})$$
   $$G = \text{round}(G_1 + (G_2 - G_1) \cdot t_{\text{local}})$$
   $$B = \text{round}(B_1 + (B_2 - B_1) \cdot t_{\text{local}})$$
4. Se codifica el resultado en la convención de color ASS en orden inverso BGR: `&HBBGGRR&`.

---

### 5.4. Sinergias y Buenas Prácticas
* **Degradado Tipográfico Carácter a Carácter:** Mantener `Progress: char.i / char.n` y conectar la salida `Tags` directamente a `System/Output`. Cada letra de la frase adoptará automáticamente su color correspondiente en el gradiente.
* **Keyframes Temporales de Color con `Concatenate (Zip)`:** Configurar `Total: 5`, conectar la salida `Tags` a la entrada 1 de un `Concatenate (Zip)` y una secuencia de tiempos `\t(0,200,), \t(200,400,), ...` a la entrada 2 para generar animaciones de transición cromática por fotogramas clave.

### 5.5. Ejemplo Práctico de Producción
* **Degradado Cromático Glifo por Glifo a lo Largo de la Línea:**
  Generando una progresión continua de tres colores (`#FF4500` naranja, `#FFD700` dorado, `#00FFFF` cian) con aceleración ease-in sobre cada carácter de la frase:

  ```
  [Loops/Main Loop: mode=char] ──► char.i / char.n ─────────────────────┐
                                                                         ▼
  [Functions/Color Gradient: accel=1.2] ──► Tags (\1c) ──────────────► Tags In ──► [System/Output]
     colors: "#FF4500, #FFD700, #00FFFF"
  ```

  * **Resultado ASS Emitido en el Subtítulo:**
    * **Carácter inicial ($t=0.0$):** Emite `{\an5\pos(320, 240)\1c&H0045FF&}` (naranja rojizo puro).
    * **Carácter central ($t \approx 0.5$):** Emite `{\an5\pos(420, 240)\1c&H00D7FF&}` (dorado brillante).
    * **Carácter final ($t=1.0$):** Emite `{\an5\pos(520, 240)\1c&HFFFF00&}` (cian eléctrico puro).
    * La interpolación en espacio RGB conserva la luminosidad y genera un gradiente continuo sin saltos cromáticos.

---

## 6. Nodo `Functions/Clip Gradient` (Bandas y Mallas de Recorte para Degradados)

* **Categoría Canónica:** `Functions` (UI: *Funciones / Clip Gradient*)
* **Propósito:** Divide el área de tinta visual del texto (*Glyph Ink Bounding Box*) del elemento activo en franjas o mallas matriciales bidimensionales ($C \times R$) continuas con solapamiento milimétrico (*overlap*), ajustándose exactamente al trazado real de los glifos sin desperdiciar iteraciones en márgenes tipográficos vacíos, optimizado para simular degradados de color multicapa continuos, barridos angulares o transiciones reticulares en libass sin líneas de costura visibles.

![Functions/Clip Gradient](img/clip_gradient.png)

### 6.1. Encabezado y Modos de Cabecera (*Header Mode Combos*)
1. **`Mode` (`out_mode`):** Selector desplegable que define la sintaxis de salida generada:
   * **`\clip` (`clip` - Defecto):** Emite etiquetas ASS estándar de recorte `\clip(x1,y1,x2,y2)` o vectoriales `\clip(m x1 y1 l x2 y2 ...)`.
   * **`\iclip` (`iclip`):** Emite etiquetas ASS de recorte inverso `\iclip(...)`.
   * **`Shape` (`shape`):** Emite el trazado poligonal en código ASSdraw puro (`m ... l ...`) centrado en el origen local `(0, 0)` para alimentar nodos de geometría vectorial.

---

### 6.2. Puertos de Entrada y Propiedades del Cuerpo (*Inputs & Properties*)
1. **`Cols` (`cols` - Slot `0`):** Número de columnas o subdivisiones horizontales. (Defecto: `"5"`).
2. **`Rows` (`rows` - Slot `1`):** Número de filas o subdivisiones verticales. Fijar `Rows: 1` opera como franjas verticales; `Cols: 1` genera franjas horizontales; valores mayores en ambos generan mallas matriciales 2D ($N = \text{Cols} \times \text{Rows}$). (Defecto: `"1"`).
3. **`Angle` (`angle` - Slot `2`):** Ángulo de inclinación de la cuadrícula o franjas en grados sexagesimales ($0^\circ \dots 360^\circ$). $0^\circ$ genera celdas rectangulares ortogonales; cualquier ángulo oblicuo proyecta cuadriláteros rotados afines cerrados. (Defecto: `"0"`).
4. **Cruceta de Expansión Direccional (Sin puerto de cable — 5 cuadros inline):** Permite expandir el área de recorte desde los bordes de la tinta del glifo de forma independiente o uniforme:
   * **`Pad Top` (`pad_top` - Superior):** Píxeles adicionales a expandir hacia arriba. (Defecto: `"0"`).
   * **`Pad Left` (`pad_left` - Izquierdo):** Píxeles adicionales a expandir hacia la izquierda. (Defecto: `"0"`).
   * **`Padding` (`padding` - Central):** Distancia uniforme en píxeles que se añade simultáneamente en las 4 direcciones, sumándose a cada margen direccional ($\text{eff}_{\text{dir}} = \text{padding} + \text{pad}_{\text{dir}}$). (Defecto: `"0"`).
   * **`Pad Right` (`pad_right` - Derecho):** Píxeles adicionales a expandir hacia la derecha. (Defecto: `"0"`).
   * **`Pad Bottom` (`pad_bottom` - Inferior):** Píxeles adicionales a expandir hacia abajo. (Defecto: `"0"`).
5. **`Overlap` (`overlap` - Slot `3`):** Expansión milimétrica de solapamiento en píxeles aplicada a los bordes de cada celda para erradicar las líneas de costura o artefactos de renderizado (*anti-aliasing seams*) en libass. (Defecto: `"0.5"`).
6. **`Order` (`order` - Slot `4`):** Selector de ordenamiento espacial 2D canónico (Numpad, radial y aleatorio): `"79"`, `"97"`, `"13"`, `"31"`, `"71"`, `"17"`, `"93"`, `"39"`, `"5"`, `"-5"`, `"cw"`, `"ccw"`, `"rand"`. (Defecto: `"79"`).

---

### 6.3. Puertos de Salida y Variables de Contexto (*Outputs & Badges*)
1. **`[1.1] Output`:** Etiqueta ASS compilada (`\clip(...)` o `\iclip(...)`) o trazado ASSdraw correspondiente a la celda activa del ciclo.
2. **`[1.2] Progress (0-1)`:** Factor de avance normalizado de la celda actual:
   $$\text{Progress} = \frac{k}{N - 1} \in [0.0, 1.0]$$
3. **`[1.3] Index`:** Índice ordinal de la celda activa ($1$-based: $1 \dots N$).
4. **`[1.4] Total`:** Cantidad total de celdas configuradas ($N = \text{Cols} \times \text{Rows}$).
5. **`[1.5] Col`:** Columna ordinal de la celda activa ($1 \dots \text{Cols}$).
6. **`[1.6] Row`:** Fila ordinal de la celda activa ($1 \dots \text{Rows}$).

#### Variables Inyectadas al Contexto de Iteración:
* **`c_i` / `clip_i`:** Índice de la celda activa en el ciclo.
* **`c_n` / `clip_n` / `clip_max`:** Número total de celdas configuradas ($N$).
* **`c_col` / `col`:** Columna actual de la celda activa ($1$-based).
* **`c_row` / `row`:** Fila actual de la celda activa ($1$-based).

---

### 6.4. Geometría de Franjas y Mallas 2D

```
Franjas 1D (Cols: 4, Rows: 1)      Malla 2D (Cols: 3, Rows: 2)       Malla Rotada (Ángulo θ)
┌───┬───┬───┬───┐                 ┌─────┬─────┬─────┐                ┌───────/───────┐
│   │   │   │   │                 │ 0,0 │ 1,0 │ 2,0 │               / 0,0   / 1,0   /
│ 0 │ 1 │ 2 │ 3 │                 ├─────┼─────┼─────┤              /───────/───────/
│   │   │   │   │                 │ 0,1 │ 1,1 │ 2,1 │             / 0,1   / 1,1   /
└───┴───┴───┴───┘                 └─────┴─────┴─────┘            └───────/───────┘
```

#### 6.4.1. Caso Rectangular Ortogonal ($0^\circ$)
Cuando el ángulo es $0^\circ$, el nodo genera cajas rectangulares simples AABB `\clip(x1, y1, x2, y2)` con máxima velocidad de rasterizado en libass:
$$W_{\text{cell}} = \frac{B_{\text{width}}}{C}, \quad H_{\text{cell}} = \frac{B_{\text{height}}}{R}$$
$$x_1 = B_{\text{left}} + c \cdot W_{\text{cell}} - \text{ov}, \quad x_2 = B_{\text{left}} + (c + 1) \cdot W_{\text{cell}} + \text{ov}$$
$$y_1 = B_{\text{top}} + r \cdot H_{\text{cell}} - \text{ov}, \quad y_2 = B_{\text{top}} + (r + 1) \cdot H_{\text{cell}} + \text{ov}$$

#### 6.4.2. Caso Inclinado Arbitrario ($\theta$)
Para ángulos oblicuos, se proyectan las dimensiones sobre los ejes rotados $u$ y $v$, rotando los 4 vértices proyectados de la celda alrededor del centro $(C_x, C_y)$:
$$P_x = C_x + u \cos \theta - v \sin \theta, \quad P_y = C_y + u \sin \theta + v \cos \theta$$
Emitiendo un trazado vectorial cerrado de 4 puntos: `\clip(m p1_x p1_y l p2_x p2_y l p3_x p3_y l p4_x p4_y)`.

---

### 6.5. Detección Inteligente de Tinta y Alineación Agnóstica (`\an1` .. `\an9`)
`Clip Gradient` inspecciona automáticamente el tipo de objeto retornado en la salida del grafo (`Return` del nodo `Output`) y la alineación `\an` activa para proyectar los recortes con exactitud sobre la tinta real:
* **Medición de Tinta del Objeto (Shape vs. Texto):**
  * **Shape (vectorial ASSdraw, biblioteca de formas o piezas):** Detecta comandos vectoriales o nodos de dibujo (`Shape/Library`, `Shape/Manipulator`, `Shape/Slicer`, etc.) y calcula la *bounding box* de tinta real del vector.
  * **Texto:** Mide la tinta visual real de los glifos (*Glyph Ink Contour*) de la unidad o línea activa; si se devuelve un texto personalizado, lo vectoriza dinámicamente mediante el motor tipográfico para obtener su tinta real.
* **Alineación Agnóstica (Default `\an5` o estipulada `\an1` .. `\an9`):**
  * Asume `\an5` por defecto salvo que se estipule otra alineación mediante el widget de alineación de `Output`, tags del contexto o propiedades.
  * Si se estipula `\an7` (convención canónica para partículas y piezas rotadas sobre su propio eje), el recorte fija su esquina superior izquierda directamente en `\pos(x, y)` (`left = pos_x`, `top = pos_y`), logrando un calce milimétrico sin offsets indeseados. Con `\an1` alinea a la esquina inferior izquierda (`top = pos_y - h`), y análogamente para cada posición del numpad.

---

### 6.6. Sinergias y Buenas Prácticas
* **Degradados Multicapa en Bucles `MaxLoop`:** Conectar `MaxLoop` configurado con `Total: 10`, conectar `Clip Gradient` con `Rows: 10` (franjas horizontales) y alimentar la salida `Progress (0-1)` hacia un nodo `Color Gradient (Progress)`. Cada capa generada por `MaxLoop` contendrá su franja de recorte correspondiente y su color exacto interpolado, formando un degradado continuo perfecto.

### 6.7. Ejemplo Práctico de Producción
* **Degradado Cromático Vertical en 5 Franjas sin Costuras:**
  Dividiendo el texto activo en 5 franjas horizontales con solapamiento milimétrico (`overlap=0.5`), asignando a cada una su color interpolado entre magenta (`#FF007F`) y violeta (`#7F00FF`):

  ```
  [Loops/MaxLoop: total=5] ──► j ───────────────────────────────┐
                                                                 ▼
  [Functions/Clip Gradient: cols=1, rows=5] ──► Progress (0-1) ─► Prog ──► [Functions/Color Gradient]
     out_mode: "\clip", overlap: 0.5                             colors: "#FF007F, #7F00FF"
                                    │                                           │
                                    ▼ Output (\clip)                            ▼ Tags (\1c)
                                 Tags In ──────────────────────────────────── Tags In ──► [System/Output]
  ```

  * **Resultado ASS Emitido en el Subtítulo:**
    * **Iteración $j=1$ (franja superior):** Emite `{\clip(300, 199.5, 450, 208.5)\1c&H7F00FF&}`.
    * **Iteración $j=3$ (franja intermedia):** Emite `{\clip(300, 215.5, 450, 224.5)\1c&HBF00BF&}`.
    * **Iteración $j=5$ (franja inferior):** Emite `{\clip(300, 231.5, 450, 240.5)\1c&HFF007F&}`.
    * El solapamiento de $0.5\text{ px}$ en las coordenadas de recorte absorbe imperfecciones de redondeo subpíxel de libass, eliminando artefactos de costura visual.

---

## 7. Nodo `Functions/IMG to pixels` (Muestreo Ráster a Partículas)

* **Categoría Canónica:** `Functions` (UI: *Funciones / IMG to pixels*)
* **Propósito:** Muestrea archivos de imagen (PNG, JPG, WEBP, GIF animado) descomponiendo los píxeles opacos en partículas vectoriales individuales con color `\1c` extraído de la textura, canal alfa `\alpha`, posiciones cartesianas `\pos(x, y)` y ordenamiento espacial Numpad, con aceleración por GPU y caché global optimizada.

![Functions/IMG to pixels](img/img_to_pixels.png)

### 7.1. Puertos de Entrada y Propiedades del Cuerpo (*Inputs & Properties*)
1. **`Image Path` (`image_path`):** Ruta absoluta al archivo de imagen o GIF animado en el sistema local.
2. **`Particle` (`particle_shape`):** Forma vectorial ASSdraw que representará a cada píxel. Si se deja vacío, genera automáticamente un micro-cuadrado proporcional al paso: `m 0 0 l s 0 l s s l 0 s`.
3. **`Frame` (`frame_idx` / `frame`):** Número de fotograma a muestrear en GIFs animados ($1$-based). (Defecto: `"1"`).
4. **`Step` (`step`):** Paso de muestreo en píxeles. Un paso de `1` muestrea cada píxel individual; un paso de `2` muestrea 1 de cada 4 píxeles ($2 \times 2$), reduciendo drásticamente la carga de líneas ASS mientras mantiene la silueta visual. (Defecto: `2`).
5. **`Alpha` (`alpha_threshold`):** Umbral de corte del canal alfa ($0 \dots 255$). Los píxeles con opacidad inferior a este valor se descartan como fondo transparente. (Defecto: `128`).
6. **`Scale` (`scale`):** Factor multiplicador de escala espacial aplicado a las coordenadas y tamaño de la imagen. (Defecto: `1.0`).
7. **`Anchor` (`anchor`):** Selector de punto de anclaje relativo (`center`, `topleft`, `topright`, `bottomleft`, `bottomright`). (Defecto: `"center"`).
8. **`Order` (`order`):** Selector de código de ordenamiento espacial 2D (`79`, `97`, `13`, `31`, `71`, `17`, `93`, `39`, `5`, `-5`, `cw`, `ccw`, `rand`). (Defecto: `"79"`).

### 7.2. Atajos de Interfaz y Clics Interactivos (*UI Shortcuts & Interaction*)
> [!TIP]
> * **Doble Clic sobre la Tarjeta de Previsualización (*Preview Card*):** Al hacer doble clic en el área de la miniatura central de la tarjeta, se abre de forma inmediata el explorador de archivos nativo del sistema operativo para seleccionar directamente archivos de imagen (`.png`, `.jpg`, `.jpeg`, `.webp`, `.gif`), actualizando la propiedad `image_path` y renderizando la textura sin tener que copiar manualmente rutas de disco.

---

### 7.3. Puertos de Salida y Variables de Contexto (*Outputs & Badges*)
1. **`[1.1] Shp Out`:** Código vectorial ASSdraw de la partícula activa en la iteración actual.
2. **`[1.2] Color Arr`:** Código de color ASS `&HBBGGRR&` muestreado del píxel correspondiente en la textura de la imagen.
3. **`[1.3] \pos Tag`:** Etiqueta ASS completa `\pos(x, y)` calculada sumando la posición relativa del píxel a las coordenadas del centro del elemento activo.
4. **`[1.4] X Arr`:** Coordenada cartesiana $X$ absoluta en píxeles de pantalla.
5. **`[1.5] Y Arr`:** Coordenada cartesiana $Y$ absoluta en píxeles de pantalla.
6. **`[1.6] Total`:** Cantidad total de píxeles/partículas activas encontradas en la imagen ($N$).
7. **`[1.7] Pixels Array`:** Lista estructurada completa con todos los píxeles muestreados `[(x, y, r, g, b, alpha), ...]`.

#### Variables Inyectadas al Contexto de Iteración:
* **`ip_i` / `img_p_i`:** Índice del píxel/partícula activa en el ciclo ($1 \dots N$).
* **`ip_n` / `img_p_n` / `total_pixels` / `maxloop`:** Total de partículas activas.
* **`fx_pos_x`, `fx_pos_y`, `x`, `y`:** Coordenadas absolutas de la partícula activa.

---

### 7.4. Detalle Algorítmico, Caché y Aceleración por GPU

```
Imagen Ráster (Pillow / NumPy)          Enjambre Vectorial ASS
┌────────────────────────┐              ┌────────────────────────┐
│  Píxeles con α ≥ 128   │  Muestreo    │  Partículas ASSdraw    │
│  (x % step == 0)       │ ───────────► │  \pos(x, y)            │
│  (y % step == 0)       │   Step = 2   │  \1c&HBBGGRR&          │
└────────────────────────┘              └────────────────────────┘
```

1. **Extracción y Filtrado por Máscara Booleana:**
   La imagen se convierte en una matriz NumPy RGBA de dimensiones $(H, W, 4)$. Se filtran los índices mediante indexación vectorizada:
   $$\text{Mask} = (\text{Alpha} \ge \text{Threshold}) \land (X \pmod{\text{Step}} = 0) \land (Y \pmod{\text{Step}} = 0)$$
2. **Caché Global de Muestreo:**
   El resultado de las matrices de píxeles se almacena en memoria caché indexado por `(ruta, frame, step, threshold, scale, anchor, order)`, evitando re-leer o procesar la imagen en cada iteración del bucle.
3. **Aceleración por GPU (OpenCL/CUDA):**
   Si el gestor de GPU está activo en el entorno del sistema, las transformaciones afines de traslación, escala y ordenamiento Numpad de las coordenadas se ejecutan en paralelo en la GPU.

---

### 7.5. Sinergias y Buenas Prácticas
* **Desintegración y Reconstrucción de Logotipos:** Conectar `IMG to pixels` a un bucle `MaxLoop (total_pixels)`, conectar la salida `\pos Tag` a un nodo `Move Tag (Trajectory)` o `Tag Oscillator` con retardo escalonado por partícula (`ip_i`), y emitir a `Output`. Las partículas volarán desde sus posiciones originales hacia el exterior dispersándose en pantalla.
* **Optimización de Carga:** Para imágenes de alta resolución (ej. $1920 \times 1080$), emplear siempre `Step: 4` o `Step: 6` para mantener el conteo de partículas entre $500 \dots 2000$ unidades, asegurando una previsualización fluida a 60 FPS en el visor WebAssembly.

### 7.6. Ejemplo Práctico de Producción
* **Muestreo Ráster de Emblema con Enjambre Vectorial 2x2:**
  Muestreando un archivo PNG local con paso de $2\text{ px}$ (`step=2`), umbral de transparencia $128$ y anclaje centrado sobre el elemento activo:

  ```
  [Functions/IMG to pixels: step=2, anchor=center] ──► Total (N) ──► Total ──► [Loops/MaxLoop]
     image_path: "C:/assets/logo_spark.png"                                         │
        │                                                                           │ j (ip_i)
        ├─► Shp Out (m 0 0 l 2 0...) ───────────────► Shape / Text ◄────────────────┘
        ├─► Color Arr (&HBBGGRR&) ──────────────────► Tags In
        └─► \pos Tag (\pos(x, y)) ──────────────────► Tags In ──► [System/Output]
  ```

  * **Resultado ASS Emitido en el Subtítulo:**
    * **Partícula 1 ($x=620, y=340$):** Emite `{\an5\pos(620, 340)\1c&H22AAFF&\1a&H00&\p1}m 0 0 l 2 0 l 2 2 l 0 2`.
    * **Partícula 250 ($x=640, y=360$):** Emite `{\an5\pos(640, 360)\1c&HFFFFFF&\1a&H00&\p1}m 0 0 l 2 0 l 2 2 l 0 2`.
    * Cada micro-cuadrado vectorial adopta su color original de textura muestreado por GPU/NumPy, emitiendo exactamente $N$ líneas correspondientes a los píxeles opacos sin procesar zonas transparentes.

---

## 8. Nodo `Functions/Animation` (Animación FBF y Modulación Alfa)

* **Categoría Canónica:** `Functions` (UI: *Funciones / Animation*)
* **Propósito:** Genera secuencias de animación cíclicas a partir de una lista de formas vectoriales ASSdraw, glifos o cadenas tipográficas. Admite dos modos operativos fundamentales: conmutación fotograma a fotograma (*Frame-by-Frame / FBF*) con sincronización de cuadros, o modulación por transparencia mediante bloques de canal alfa (`\alpha` o `\1a..\4a`) sincronizados en una única línea de subtítulo.

![Functions/Animation](img/animation.png)

### 8.1. Encabezado y Modos Operativos (*Header Mode Combos*)
1. **`FBF` (*Frame-by-Frame*):** Cada iteración del bucle principal (`an_i` o `j`) selecciona el fotograma correspondiente dentro de la secuencia. La salida `Shape` emite el trazado vectorial del cuadro activo prefijado con alineación `{\an7}`.
2. **`Alpha` (*Modulación Alfa Sincronizada*):** Genera una cadena continua de transiciones de visibilidad `\t` que enciende (`&H00&`) y apaga (`&HFF&`) cíclicamente cada forma en sus intervalos de tiempo calculados.

---

### 8.2. Puertos de Entrada y Propiedades del Cuerpo (*Inputs & Properties*)
1. **`Frames / Text` (`frames`):** Secuencia de formas vectoriales o texto. Acepta:
   * Nombres de primitivas de librería (ej. `"Circle, Star, Heart"`).
   * Arrays JSON (ej. `["m 0 0 l 10 10", "m 0 0 l 20 20"]`).
   * Listas separadas por comas, punto y coma `;` o saltos de línea `\n`.
   * Cadenas de texto ordinarias (convertidas automáticamente a vectores de fuente tipográfica).
   * Referencias directas a variables del contexto (ej. `Shapes1`, `my_frames`).
2. **`Step ms` (`step_ms`):** Duración temporal en milisegundos de cada fotograma individual de la animación. Un valor de `41.7` equivale aproximadamente a 24 FPS; `33.3` a 30 FPS; `16.6` a 60 FPS. (Defecto: `41.7`).
3. **`Start Time` (`start_time`):** Instante de inicio de la animación en milisegundos relativos al evento activo (`0` o vacío toma el inicio del efecto `fx.st` / `syl.start_time`).
4. **`End Time` (`end_time`):** Instante de finalización de la animación (`fx.dur` o vacío toma la duración total del efecto).
5. **`Alpha Tag` (`alpha_tag`):** [Modo Alpha] Etiqueta ASS o Dark Tag multicanal de transparencia modulada (`\alpha`, canales individuales `\1a`, `\2a`, `\3a`, `\4a`, dobles `\12a`, `\13a`, `\14a`, `\23a`, `\24a`, `\34a`, triples `\123a`, `\124a`, `\134a`, `\234a` o cuádruple `\1234a`). Permite conmutar la visibilidad de canales específicos (por ejemplo, `\13a` modula relleno primario y borde simultáneamente sin afectar la sombra `\4a`). (Defecto: `"\alpha"`).
6. **`Variable Prefix` (`var_name`):** Prefijo identificador para las variables de bucle inyectadas en el contexto. (Defecto: `"an"`).

---

### 8.3. Puertos de Salida (*Outputs*)

#### En Modo FBF:
1. **`[1.1] Shape`:** Código vectorial ASSdraw del fotograma activo con prefijo `{\an7}` si no contiene tags previos.
2. **`[1.2] Frame`:** Número del fotograma actual evaluado (entero base 1: $1, 2, \dots, N$).
3. **`[1.3] Frames List`:** Lista completa de todos los trazados vectoriales procesados.

#### En Modo Alpha:
1. **`[1.1] Shape`:** Forma vectorial activa encapsulada con su bloque de tags de visibilidad temporal `{\an7\alpha&HFF&\t(...)\p1}...`.
2. **`[1.2] Tags`:** Cadena exclusiva de etiquetas ASS generadas (`\an7\alpha&HFF&\t(...)`) sin el código de dibujo.
3. **`[1.3] Frame`:** Número del fotograma actual evaluado (base 1).
4. **`[1.4] Frames List`:** Lista completa de trazados vectoriales.

#### Variables Expuestas en Contexto:
* `{var_name}_i` / `an_i`: Índice del fotograma actual ($1 \dots K$).
* `{var_name}_n` / `an_n`: Cantidad total de fotogramas únicos disponibles ($K$).
* `an_total_cycles`: Cantidad de repeticiones completas del ciclo de animación dentro de la duración total.

---

### 8.4. Detalle Algorítmico y Sincronización Temporal

Dado un conjunto de $K$ fotogramas $\{F_0, F_1, \dots, F_{K-1}\}$, un tiempo de cuadro $\Delta t_{\text{frame}} = \text{step\_ms}$ y un intervalo total $[t_{\text{start}}, t_{\text{end}}]$ con duración $D = t_{\text{end}} - t_{\text{start}}$:

```
Índice de Cuadro:   F0       F1       F2       F0       F1       F2
Tiempo (ms):     ├───Δt───┼───Δt───┼───Δt───┼───Δt───┼───Δt───┼───Δt───┤
Ciclo:           └─────── Ciclo 1 ──────────┘└─────── Ciclo 2 ──────────┘
```

#### 8.4.1. Mapeo Cíclico en Modo FBF
En cada iteración del bucle con iterador activo $j \ge 1$:
$$\text{active\_idx} = (j - 1) \pmod K$$
$$\text{Frame} = \text{active\_idx} + 1$$
El total de cuadros generados para cubrir la duración total es:
$$N_{\text{total}} = \left\lceil \frac{D}{\Delta t_{\text{frame}}} \right\rceil$$

#### 8.4.2. Generación de Transiciones en Modo Alpha
Para cada ciclo $k \in [0, N_{\text{ciclos}}]$ y cada fotograma con índice local $i$:
$$t_1 = \Delta t_{\text{frame}} \cdot (K \cdot k + i)$$
$$t_2 = t_1 + 1.0$$
$$t_3 = \Delta t_{\text{frame}} \cdot (K \cdot k + i + 1)$$
$$t_4 = \min(D, t_3 + 1.0)$$
Se inyecta la pareja de visibilidad:
$$\backslash\text{t}(t_1, t_2, \text{tag}\&H00\&)\backslash\text{t}(t_3, t_4, \text{tag}\&HFF\&)$$

---

### 8.5. Sinergias y Buenas Prácticas
* **GIFs y Spritesheets con `Shape/IMG to Shape`:** Conectar la salida `Shapes Array` de un `IMG to Shape` directamente a la entrada `Frames / Text` de `Animation` para reproducir animaciones extraídas de GIFs cuadro a cuadro.
* **Integración con `Loops/MaxLoop (fbf)`:** Configurar un `MaxLoop` en modo `fbf` para que itere automáticamente la cantidad exacta de cuadros requerida por la duración del karaoke.

### 8.6. Ejemplo Práctico de Producción
* **Ciclo Vectorial Fotograma a Fotograma con MaxLoop FBF:**
  Reproduciendo una secuencia cíclica de formas vectoriales (`circle`, `star`, `heart`) a 24 FPS ($41.7\text{ ms}$ por cuadro):

  ```
  [Loops/MaxLoop: mode=fbf, step_ms=41.7] ──► j ────────────────────────┐
                                                                         ▼
  [Functions/Animation: mode=FBF, step_ms=41.7] ──► Shape ──► Shape / Text ──► [System/Output]
     frames: "circle, star, heart"
  ```

  * **Resultado Vectorial Emitido en `Shape`:**
    * **Iteración $j=1$:** Emite `{\an7}m 50 0 b 22 0 0 22 0 50 ...` (primitiva de círculo de librería).
    * **Iteración $j=2$:** Emite `{\an7}m 38 36 l 0 36 l 31 59 ...` (estrella vectorial).
    * **Iteración $j=3$:** Emite `{\an7}m 50 25 b 50 10 35 0 20 0 ...` (corazón vectorial).
    * **Iteración $j=4$:** Retorna automáticamente al fotograma inicial ($1$), repitiendo el bucle de forma infinita y continua durante la vida del subtítulo.

---

## 9. Nodo `Functions/Bezier Curve` (Curvas y Splines Bézier 2D)

* **Categoría Canónica:** `Functions` (UI: *Funciones / Bezier Curve*)
* **Propósito:** Generador, evaluador e interpolador universal de curvas paramétricas de Bézier 2D. Implementa el algoritmo de De Casteljau para curvas cuadráticas, cúbicas y de grado arbitrario $N$, integración numérica de longitud de arco para velocidad constante, extracción de derivadas vectoriales (tangentes y normales), subdivisión topológica de curvas y generación de trayectorias estocásticas suaves.

![Functions/Bezier Curve](img/bezier_curve.png)

### 9.1. Encabezado y Modos Operativos (*Header Mode Combos*)
1. **`Cubic 2D`:** Curva Bézier cúbica clásica definida por 4 puntos de control ($P_0, P_1, P_2, P_3$).
2. **`Quadratic 2D`:** Curva Bézier cuadrática definida por 3 puntos de control ($P_0, P_1, P_2$).
3. **`N-Degree`:** Curva polinómica de orden arbitrario $N$ definida por una lista de puntos en `Points` ($P_0, P_1, \dots, P_N$).
4. **`Constant Speed`:** Mapeo de $t \in [0.0, 1.0]$ corregido por longitud de arco mediante regla de Simpson para garantizar velocidad uniforme en píxeles/segundo.
5. **`Shape Contour`:** Muestrea paramétricamente un trazado ASSdraw arbitrario conectado a la entrada `Shape`.
6. **`Subdivide`:** Divide la curva en el punto paramétrico $t$ generando dos nuevos splines independientes (`Spline L` y `Spline R`).
7. **`Trajectory`:** Generador procedural de trayectorias aleatorias continuas mediante splines cúbicos concatenados (`Free Wander`, `Bounded`, `Closed Loop`).

---

### 9.2. Puertos de Entrada y Propiedades del Cuerpo (*Inputs & Properties*)
1. **`Origin` (`origin`):** Coordenada cartesiana $(X_0, Y_0)$ de origen aditivo que se suma a todos los puntos de la curva. (Defecto: `"0,0"`).
2. **`P0, P1, P2, P3` (`p0`, `p1`, `p2`, `p3`):** Coordenadas $(X, Y)$ de los puntos de control. Acepta tuplas separadas por comas, espacios o cables.
3. **`t` (`t`):** Factor de evaluación paramétrica $t \in [0.0, 1.0]$. Acepta variables dinámicas como `j / maxloop` o `char.i / char.n`. (Defecto: `"0.5"`).
4. **`Subdivs` (`subdivs`):** Número de segmentos discretos para el muestreo de contornos vectoriales y cálculo de longitud de arco. (Defecto: `"100"`).
5. **`Shape` (`shape`):** Trazado vectorial ASSdraw para los modos `Shape Contour` y `Trajectory`.
6. **`Points` (`points`):** Lista de puntos de control para modo `N-Degree` (ej. `"0,0; 50,100; 150,100; 200,0"`).
7. **`Trajectory Mode` (`traj_mode`):** Tipo de trayectoria procedural (`"Free Wander"`, `"Bounded"`, `"Closed Loop"`).
8. **`Dist Range` (`dist_range`):** Rango de distancia mínima y máxima entre nodos aleatorios (ej. `"50,120"`).
9. **`Seed` (`seed`):** Semilla pseudoaleatoria determinista para modo `Trajectory`. (Defecto: `"1"`).
10. **`Loops` (`loops`):** Cantidad de segmentos cúbicos encadenados en la trayectoria. (Defecto: `"8"`).

---

### 9.3. Puertos de Salida (*Outputs*)
1. **`[1.1] \pos`:** Etiqueta ASS formateada `\pos(X, Y)` evaluada en el punto $t$.
2. **`[1.2] X`:** Coordenada cartesiana $X(t)$ puntual (entero o float a 2 decimales).
3. **`[1.3] Y`:** Coordenada cartesiana $Y(t)$ puntual.
4. **`[1.4] Tan`:** Ángulo de inclinación de la tangente $\theta \in [0^\circ, 360^\circ)$ en grados, ideal para conectar a rotación `\frz`.
5. **`[1.5] Norm`:** Ángulo de la normal perpendicular a la curva $(\theta + 90^\circ) \pmod{360^\circ}$.
6. **`[1.6] Spline`:** Trazado vectorial ASSdraw completo de la curva (ej. `m X0 Y0 b X1 Y1 X2 Y2 X3 Y3`).
7. **`[1.7] Spline L`:** [Modo Subdivide] Trazado ASSdraw del segmento izquierdo $[0.0, t]$.
8. **`[1.8] Spline R`:** [Modo Subdivide] Trazado ASSdraw del segmento derecho $[t, 1.0]$.

---

### 9.4. Detalle Algorítmico y Formulación Matemática

```
P1 (50, 100)                     P2 (150, 100)
    ●───────────────────────────────●
   /                                 \
  /           B(t) (X, Y)             \
 /                 ● ───> Tangente     \
●                  │                    ●
P0 (0, 0)          ▼ Normal             P3 (200, 0)
```

#### 9.4.1. Algoritmo de De Casteljau (Grado $N$)
Dado un conjunto de $n+1$ puntos de control $\{P_0, P_1, \dots, P_n\}$ con $P_i \in \mathbb{R}^2$:
$$P_i^{(0)} = P_i \quad \forall i \in \{0, \dots, n\}$$
$$P_i^{(r)} = (1 - t) P_i^{(r-1)} + t P_{i+1}^{(r-1)} \quad \forall r \in \{1, \dots, n\}, \, i \in \{0, \dots, n-r\}$$
El punto final en la curva es $B(t) = P_0^{(n)}$.

Para una curva cúbica ($n=3$):
$$B(t) = (1-t)^3 P_0 + 3(1-t)^2 t P_1 + 3(1-t) t^2 P_2 + t^3 P_3$$

#### 9.4.2. Derivada, Tangente y Normal
La primera derivada vectorial $B'(t) = (dx/dt, dy/dt)$ de una curva de grado $n$ es una curva Bézier de grado $n-1$:
$$B'(t) = n \sum_{i=0}^{n-1} (P_{i+1} - P_i) \cdot b_{i, n-1}(t)$$
A partir del vector velocidad $(dx, dy)$:
$$\theta_{\text{tan}} = \left( \operatorname{atan2}(dy, dx) \cdot \frac{180}{\pi} + 360^\circ \right) \pmod{360^\circ}$$
$$\theta_{\text{norm}} = (\theta_{\text{tan}} + 90^\circ) \pmod{360^\circ}$$

#### 9.4.3. Corrección por Longitud de Arco (Velocidad Constante)
La longitud acumulada $s(t)$ se calcula integrando la norma de la velocidad mediante la regla de Simpson:
$$s(t) = \int_0^t \sqrt{\left(\frac{dx}{du}\right)^2 + \left(\frac{dy}{du}\right)^2} \, du$$
Para evaluar en una distancia objetivo $s_{\text{target}} = t \cdot s(1.0)$, se resuelve $s(t^*) = s_{\text{target}}$ mediante búsqueda por bisección numérica hasta alcanzar convergencia ($\epsilon < 10^{-5}$).

#### 9.4.4. Subdivisión Topológica de De Casteljau
En el instante $t$, los puntos intermedios generados en la pirámide de De Casteljau definen exactamente los nuevos polígonos de control:
* **Segmento Izquierdo ($[0, t]$):** $\{P_0^{(0)}, P_0^{(1)}, P_0^{(2)}, \dots, P_0^{(n)}\}$.
* **Segmento Derecho ($[t, 1]$):** $\{P_0^{(n)}, P_1^{(n-1)}, P_2^{(n-2)}, \dots, P_n^{(0)}\}$.

---

### 9.5. Sinergias y Buenas Prácticas
* **Orientación Automática de Proyectiles y Partículas:** Conectar la salida `\pos` a la posición del objeto y la salida `Tan` a la entrada `Angle` de un `MultiTag` o directamente al tag `\frz` para que los elementos roten orientándose naturalmente según el sentido de avance de la trayectoria.
* **Escritura Animada con `Shape/Walker`:** Conectar la salida `Spline` de `Bezier Curve` a la entrada `Path` de un `Shape/Walker` para trazar la curva en pantalla de forma progresiva.

### 9.6. Ejemplo Práctico de Producción
* **Interpolación Cinemática sobre Spline Cúbico con Orientación Tangencial:**
  Evaluando una trayectoria parabólica definida por 4 puntos de control $P_0(100, 300), P_1(200, 100), P_2(400, 100), P_3(500, 300)$ en el punto medio paramétrico $t=0.5$:

  ```
  [Functions/Bezier Curve: mode=cubic_2d, t=0.5] ──► \pos ──────┐
     p0: "100,300", p1: "200,100", p2: "400,100", p3: "500,300" │
                                           └──► Tan ───┐        ▼
                                                       └──► Tags In ──► [System/Output]
                                                                        Return: "m 0 0 l 20 0 l 20 20 l 0 20"
  ```

  * **Cálculo de De Casteljau en $t=0.5$:**
    $$B(0.5) = (1-0.5)^3 P_0 + 3(1-0.5)^2(0.5) P_1 + 3(1-0.5)(0.5)^2 P_2 + 0.5^3 P_3$$
    $$B(0.5) = 0.125(100, 300) + 0.375(200, 100) + 0.375(400, 100) + 0.125(500, 300) = (300.0, 150.0)$$
  * **Cálculo de Tangente en el Vértice Superior:**
    $$B'(0.5) = 3(0.25)(P_1 - P_0) + 6(0.25)(P_2 - P_1) + 3(0.25)(P_3 - P_2) = (450.0, 0.0) \implies \theta = 0^\circ$$
  * **Línea ASS Resultante Generada:**
    `Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\an5\pos(300,150)\frz0\p1}m 0 0 l 20 0 l 20 20 l 0 20{\p0}`

---

## 10. Nodo `Functions/Move Tag` (Cinemática y Trayectorias de Movimiento ASS)

* **Categoría Canónica:** `Functions` (UI: *Funciones / Move Tag*)
* **Propósito:** Genera bloques cinemáticos completos de etiquetas ASS (`\pos`, `\fscx`, `\fscy`, `\t`) a partir de formas vectoriales de trazado, waypoints cartesianos o fluctuaciones estocásticas (*jitter*). Re-muestrea la trayectoria según un paso métrico uniforme en píxeles (`step_px`), aplica curvas de aceleración exponencial no lineal y reposiciona el sistema de anclaje.

![Functions/Move Tag](img/move_tag.png)

### 10.1. Encabezado y Modos Operativos (*Header Mode Combos*)
1. **`Trajectory` (`SMOVE`):** Toma una forma vectorial ASSdraw (`Shape`), calcula su longitud de arco total y la divide en segmentos regulares de longitud máxima `step_px` para generar una trayectoria continua suave.
2. **`Waypoints` (`PMOVE`):** Toma una lista de puntos cartesianos discretos (`Points` o `Shape`) y genera transiciones lineales o interpoladas entre cada hito.
3. **`Jitter` (`RMOVE`):** Genera una trayectoria de fluctuación pseudoaleatoria continua oscilando en un rango $(\pm \Delta X, \pm \Delta Y)$ con intervalos de tiempo regulares (`dur` ms) y semilla reproducible (`seed`).

---

### 10.2. Puertos de Entrada y Propiedades del Cuerpo (*Inputs & Properties*)
1. **`Tags` (`tags`):** Etiquetas ASS adicionales que se inyectan dentro del bloque final (ej. `\1c&HFFFFFF&\blur2`).
2. **`Shape (d)` (`shape`):** Cadena de trazado vectorial ASSdraw que define la ruta espacial del movimiento (ej. `"m 0 0 b 50 100 150 100 200 0"`).
3. **`Step (px)` (`step_px`):** Distancia máxima en píxeles entre dos muestras consecutivas de la trayectoria. Valores más pequeños aumentan la suavidad a costa de generar más tags `\t`. (Defecto: `7.5`).
4. **`Anchor` (`anchor`):** Modo de centrado y anclaje espacial:
   * `"center"`: Centra la trayectoria en el punto medio de su caja delimitadora $(B_{\text{center}} = (0, 0))$.
   * `"origin"` / `"first_point"`: Fija el punto inicial del trazado en $(0, 0)$.
5. **`Start Time (t1)` (`t1`):** Tiempo inicial de inicio de movimiento en milisegundos. (Defecto: `0`).
6. **`End Time (t2)` (`t2`):** Tiempo final de llegada en milisegundos. (Defecto: `"fx.dur"`).
7. **`Acceleration` (`accel`):** Exponente de aceleración cinemática. $1.0 = \text{lineal}$; $> 1.0 = \text{acelerado (ease-in)}$; $< 1.0 = \text{desacelerado (ease-out)}$. (Defecto: `1.0`).

---

### 10.3. Puertos de Salida (*Outputs*)
1. **`[1.1] Data`:** Cadena completa de etiquetas ASS formateada lista para ser inyectada al texto o forma:
   $$\backslash\text{an7}\backslash\text{q2}\backslash\text{pos}(X_0, Y_0)\backslash\text{fscx}P_{x0}\backslash\text{fscy}P_{y0}\backslash\text{t}(t_{s1}, t_{e1}, \backslash\text{fscx}P_{x1}\backslash\text{fscy}P_{y1})\dots\backslash\text{p1}\}m\dots\{\backslash\text{p0}$$

---

### 10.4. Detalle Algorítmico y Cinemática de Desplazamiento

```
Ruta Vectorial:   P0 (0,0) ─────── P1 (7.5px) ─────── P2 (15px) ─────── P3 (22.5px)
Tiempo Mapeado:   t1               st1 ─── et1        st2 ─── et2       t2
Progreso Normal:  0.0              (d1/D)^accel       (d2/D)^accel      1.0
```

Dado un conjunto de $M$ puntos muestreados $\{P_0, P_1, \dots, P_{M-1}\}$ con distancias acumuladas $d_k$ y distancia total $D = d_{M-1}$:
1. Para cada segmento $k \in [1, M-1]$:
   $$\tau_1 = \left(\frac{d_{k-1}}{D}\right)^{\text{accel}}, \quad \tau_2 = \left(\frac{d_k}{D}\right)^{\text{accel}}$$
   $$s_t = \text{round}(t_1 + (t_2 - t_1) \cdot \tau_1)$$
   $$e_t = \text{round}(t_1 + (t_2 - t_1) \cdot \tau_2)$$
2. Se inyecta la transición:
   $$\backslash\text{t}(s_t, e_t, \backslash\text{fscx}P_{x,k}\backslash\text{fscy}P_{y,k})$$

---

### 10.5. Sinergias y Buenas Prácticas
* **Sincronización con Curvas Complejas:** Conectar la salida `Spline` de un `Bezier Curve` directamente a la entrada `Shape (d)` de `Move Tag` para trasladar sílabas o glifos a lo largo de splines Bézier con control continuo de aceleración.

### 10.6. Ejemplo Práctico de Producción
* **Desplazamiento Cinemático No Lineal con Aceleración Exponencial:**
  Generando una trayectoria espacial de 3 segmentos a lo largo de $300\text{ ms}$ con aceleración cuadrática ($\text{accel}=2.0$) desde $(100, 200)$ hasta $(250, 250)$ con paso de muestreo de $50\text{ px}$:

  ```
  [Functions/Move Tag: mode=trajectory, step_px=50, accel=2.0, t1=0, t2=300]
     shape: "m 100 200 l 170 200 l 250 250" ──► Data ──► Tags In ──► [System/Output]
                                                                     Return: "Texto"
  ```

  * **Muestreo Métrico y Aceleración ($\Delta t = 300\text{ ms}$, $D = 174.34\text{ px}$):**
    * Segmento 0 ($d_0 = 0.0$): $\tau_0 = 0.0 \to t = 0\text{ ms}$, posición $(100.0, 200.0)$.
    * Segmento 1 ($d_1 = 70.0$): $\tau_1 = (70.0 / 174.34)^2 \approx 0.161 \to s_{t1} = 48\text{ ms}$, posición $(170.0, 200.0)$.
    * Segmento 2 ($d_2 = 174.34$): $\tau_2 = 1.0 \to s_{t2} = 300\text{ ms}$, posición $(250.0, 250.0)$.
  * **Bloque de Tags ASS Emitido:**
    `{\an7\q2\pos(100.00,200.00)\fscx100.00\fscy100.00\t(0,48,2.00,\fscx170.00\fscy200.00)\t(48,300,2.00,\fscx250.00\fscy250.00)\p1}m 0 0 m 100 100 {\p0}Texto`

---

## 11. Nodo `Functions/Move Text` (Movimiento Cinemático Tipográfico Coordinado)

* **Categoría Canónica:** `Functions` (UI: *Funciones / Move Text*)
* **Propósito:** Genera animaciones cinemáticas tipográficas complejas sobre cadenas de texto sin alterar su métrica de espaciado natural ni romper el layout del párrafo. Utiliza una arquitectura de compensación diferencial en dos ejes mediante espaciado de fuente (`\fsp`) para el eje X y escala vertical (`\fscy`) para el eje Y, encapsulando el texto entre puntos invisibles de anclaje.

![Functions/Move Text](img/move_text.png)

### 11.1. Puertos de Entrada y Propiedades del Cuerpo (*Inputs & Properties*)
1. **`Text` (`text`):** Cadena de texto tipográfico o dibujo ASSdraw. Si está vacío, extrae automáticamente el texto de la sílaba o carácter activo en el contexto.
2. **`Delta X` (`dx`):** Desplazamiento cartesiano total en el eje X (px).
3. **`Delta Y` (`dy`):** Desplazamiento cartesiano total en el eje Y (px).
4. **`Offset X` (`ox`):** Desfase inicial fijo en el eje X (px).
5. **`Offset Y` (`oy`):** Desfase inicial fijo en el eje Y (px).
6. **`Shape (d)` (`shape` / `trajectory`):** Trazado vectorial ASSdraw opcional que reemplaza a $\Delta X, \Delta Y$ para seguir trayectorias curvas arbitrarias.
7. **`Points` (`points`):** Lista de puntos discretos de control de ruta.
8. **`Step (px)` (`step_px`):** Paso de muestreo para trayectorias vectoriales. (Defecto: `7.5`).
9. **`Start Time (t1)` (`t1`):** Tiempo de inicio de la traslación (ms). (Defecto: `0`).
10. **`End Time (t2)` (`t2`):** Tiempo de fin de la traslación (ms). (Defecto: `"fx.dur"`).
11. **`Acceleration` (`accel`):** Exponente de aceleración cinemática. (Defecto: `1.0`).

---

### 11.2. Puertos de Salida (*Outputs*)
1. **`[1.1] Text`:** Estructura tipográfica ASS modularizada con los bloques dobles de compensación de movimiento horizontal y vertical:
   $$\text{Block}_{V1} \cdot \text{Block}_{H1} \cdot \{\backslash\text{r}\text{tags}\backslash\text{q2}\}\text{Texto} \cdot \text{Block}_{H2} \cdot \text{Block}_{V2}$$

---

### 11.3. Detalle Algorítmico y Mecánica de Compensación Tipográfica

```
Estructura Generada:
[ Salto \N Compensador Y1 ]
[ Punto '.' Oculto con \fspX1 ] ─── [ TEXTO PRINCIPAL ] ─── [ Punto '.' Oculto con \fspX2 ]
[ Salto \N Compensador Y2 ]
```

Para mover un texto sin alterar el flujo inline de caracteres vecinos ni depender de coordenadas absolutas de pantalla `\pos`:
1. **Eje Horizontal ($X$):** Se inyectan dos caracteres punto `.` con transparencia total (`\alpha&HFF&`) a la izquierda y derecha del texto. Modulando la propiedad de espaciado tipográfico `\fsp` con valores duplicados $2 \cdot \Delta X$, el texto se desplaza suavemente hacia la izquierda o derecha mientras el ancho total ocupado en la línea permanece invariable.
2. **Eje Vertical ($Y$):** Se inyectan saltos de línea forzados `\N` con micro-dibujos vectoriales escalados verticalmente mediante `\fscy` para desplazar la línea activa hacia arriba o abajo sin alterar la línea de base tipográfica global.

---

### 11.4. Sinergias y Buenas Prácticas
* **Animaciones de Entrada/Salida Suaves:** Emplear `Move Text` con `Delta Y = -30` y `Accel = 2.0` durante la fase `presyl` para hacer que cada sílaba baje flotando suavemente desde la parte superior al momento de ser cantada.

### 11.5. Ejemplo Práctico de Producción
* **Entrada Flotante Vertical de Sílaba sin Desplazar el Layout:**
  Animando una caída vertical de $25\text{ px}$ en los primeros $250\text{ ms}$ de la sílaba mediante compensación por espaciado tipográfico y saltos forzados:

  ```
  [Variables/Sys Var: var_name=syl.text] ──► Text ─────────────────┐
                                                                   ▼
  [Functions/Move Text: dy=-25, t1=0, t2=250, accel=1.5] ──► Text ──► Return ──► [System/Output]
  ```

  * **Mecánica de Transformación:**
    El nodo calcula el ancho métrico del glifo de anclaje `.` ($w_{\text{dot}} = 7.5\text{ px}$), encapsulando el texto de la sílaba entre dos caracteres invisibles con `\alpha&HFF&` y compensando el eje vertical mediante un bloque escalado `\fscy` precedido de salto de línea forzado `\N`.
  * **Línea ASS Generada:**
    `Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\p0\alpha&HFF&.}{\fscy100\t(0,250,1.5,\fscy0)\p1}m 0 0 l 1 0 l 1 25 l 0 25{\p0}\N{\r\q2}Ka{\p0\alpha&HFF&.}`

---

## 12. Nodo `Functions/Polar to Cartesian` (Conversor Polar a Cartesiano)

* **Categoría Canónica:** `Functions` (UI: *Funciones / Polar to Cartesian*)
* **Propósito:** Transforma coordenadas polares definidas por un radio vector $r$ y un ángulo polar $\theta$ en coordenadas cartesianas $(X, Y)$ relativas a un punto de origen $(X_0, Y_0)$. Emite directamente la etiqueta de posicionamiento `\pos(X, Y)` y los componentes numéricos escalares y diferenciales para su uso en cálculos matriciales.

![Functions/Polar to Cartesian](img/polar_to_certesian.png)

### 12.1. Puertos de Entrada y Propiedades del Cuerpo (*Inputs & Properties*)
1. **`Origin X` (`x`):** Coordenada cartesiana $X_0$ del centro u origen polar. Acepta constantes o expresiones del contexto como `syl.x`, `line.x`, `char.x`. (Defecto: `"0"`).
2. **`Origin Y` (`y`):** Coordenada cartesiana $Y_0$ del centro u origen polar (ej. `syl.y`, `line.y`). (Defecto: `"0"`).
3. **`Angle (°)` (`angle`):** Ángulo polar $\theta$ expresado en grados sexagesimales ($0^\circ \dots 360^\circ$). Un ángulo de $0^\circ$ apunta en la dirección positiva del eje X (derecha); $90^\circ$ en la dirección positiva del eje Y (abajo en el sistema ASS). (Defecto: `"0"`).
4. **`Radius` (`radius`):** Magnitud o longitud del radio vector $r$ en píxeles. (Defecto: `"100"`).

---

### 12.2. Puertos de Salida (*Outputs*)
1. **`[1.1] \pos Tag`:** Etiqueta ASS de posición formateada `\pos(X, Y)`.
2. **`[1.2] X`:** Coordenada cartesiana absoluta resultante $X = X_0 + \Delta X$.
3. **`[1.3] Y`:** Coordenada cartesiana absoluta resultante $Y = Y_0 + \Delta Y$.
4. **`[1.4] dX`:** Desplazamiento diferencial horizontal relativo $\Delta X = r \cos(\theta)$.
5. **`[1.5] dY`:** Desplazamiento diferencial vertical relativo $\Delta Y = r \sin(\theta)$.

---

### 12.3. Detalle Algorítmico y Modelo Trigonométrico

```
               (X0, Y0)
                  ● ─────────────> Eje X (θ = 0°)
                  │ \
                  │  \  Radio (r)
                  │   \
                  │ θ  \
                  ▼     ● (X, Y)
                Eje Y
```

Dado el ángulo en grados sexagesimales $\theta$, se convierte a radianes:
$$\theta_{\text{rad}} = \theta \cdot \frac{\pi}{180}$$

Las componentes diferenciales y las coordenadas absolutas se calculan como:
$$\Delta X = r \cdot \cos(\theta_{\text{rad}})$$
$$\Delta Y = r \cdot \sin(\theta_{\text{rad}})$$
$$X = X_0 + \Delta X$$
$$Y = Y_0 + \Delta Y$$

Los valores numéricos se formatean como enteros limpios si no presentan parte fraccionaria, o redondeados a 2 decimales para evitar saturación de caracteres en el script ASS.

---

### 12.4. Sinergias y Buenas Prácticas
* **Distribución Radial de Partículas u Orbes:** Conectar un generador de iteración como `Basics/MultiRandom` o una expresión `j * (360 / maxloop)` a la entrada `Angle (°)`, fijar `Radius: 80` y conectar la salida `\pos Tag` a un `System/Output`. Esto generará al instante anillos circulares u explosiones radiales perfectamente distribuidas alrededor de cada sílaba.
* **Órbitas Planetarias Circulares y Espirales:** Modular `Angle (°)` con un oscilador de tiempo `Time/Ipol` y reducir dinámicamente `Radius` a lo largo del tiempo para generar trayectorias espirales convergentes hacia el centro del texto.

### 12.5. Ejemplo Práctico de Producción
* **Anillo Orbital de 8 Partículas Alrededor de la Sílaba:**
  Generando una corona circular de 8 elementos vectoriales distribuidos en pasos angulares de $45^\circ$ a un radio constante de $60\text{ px}$ desde el centro de la sílaba:

  ```
  [Loops/MaxLoop: total=8] ──► j ──► Angle: (j - 1) * 45 ────────┐
                                                                 ▼
  [Shape/Library: "Star"] ──► Shape ──► Shape / Text ──► [Functions/Polar to Cartesian: radius=60]
                                                            Origin X: syl.x, Origin Y: syl.y
                                                                 │
                                                                 ▼ \pos Tag (\pos(X, Y))
                                                              Tags In ──► [System/Output]
  ```

  * **Resultado ASS Emitido en el Subtítulo:** (asumiendo `syl.x = 320, syl.y = 240`):
    * **Iteración $j=1$ ($\theta = 0^\circ$):** $\Delta X = 60, \Delta Y = 0 \to$ Emite `{\an5\pos(380, 240)\p1}m 0 0 ...` (derecha).
    * **Iteración $j=3$ ($\theta = 90^\circ$):** $\Delta X = 0, \Delta Y = 60 \to$ Emite `{\an5\pos(320, 300)\p1}m 0 0 ...` (abajo).
    * **Iteración $j=5$ ($\theta = 180^\circ$):** $\Delta X = -60, \Delta Y = 0 \to$ Emite `{\an5\pos(260, 240)\p1}m 0 0 ...` (izquierda).
    * **Iteración $j=7$ ($\theta = 270^\circ$):** $\Delta X = 0, \Delta Y = -60 \to$ Emite `{\an5\pos(320, 180)\p1}m 0 0 ...` (arriba).
    * Los desplazamientos trigonométricos se calculan en punto flotante y se redondean a enteros limpios o 2 decimales para optimizar la salida ASS.

---

## 13. Nodo `Functions/Particles` (Enjambres de Partículas Vectoriales)

* **Categoría Canónica:** `Functions` (UI: *Funciones / Particles*)
* **Propósito:** Muestrea contornos o mallas interiores de texto o formas vectoriales ASSdraw para generar enjambres de partículas discretas. Permite sustituir cada punto muestreado por una micro-forma vectorial personalizada, reordenar la secuencia espacial según el teclado numérico (Numpad) y aplicar fluctuación aleatoria (*jitter*).

![Functions/Particles](img/particles.png)

### 13.1. Encabezado y Modos Operativos (*Header Mode Combos*)
1. **`Outline` (`outline_v2` / `border`):** Muestrea puntos equidistantes a lo largo del perímetro o borde exterior de los contornos vectoriales.
2. **`Inner Fill` (`inner_fill` / `relleno`):** Genera una cuadrícula regular de puntos en el interior de la forma, verificando la inclusión geométrica mediante el algoritmo Ray-Casting (paridad impar de cruces).

---

### 13.2. Puertos de Entrada y Propiedades del Cuerpo (*Inputs & Properties*)
1. **`Path / Origin` (`shape`):** Trazado vectorial base ASSdraw (`m ...`) o nombre de primitiva. Si se deja vacío o se pasa una cadena tipográfica, Pyxis extrae automáticamente el contorno del glifo del contexto activo (`syl` o `char`).
2. **`Particle` (`particle_shape`):** Forma vectorial empleada como partícula individual (ej. `"Circle"`, `"Star"`, `"Heart"` o código ASSdraw directo). Si está vacío, utiliza un cuadrado básico de $2 \times 2$ px (`m 0 0 l 2 0 l 2 2 l 0 2`).
3. **`Density` (`density`):** Paso métrico de muestreo en píxeles. En modo `Outline`, define la distancia entre partículas a lo largo del trazo; en modo `Inner Fill`, define la separación de la grilla de relleno. (Defecto: `5.0`).
4. **`RedrawDist` (`redraw_dist`):** Rango de dispersión o fluctuación aleatoria uniforme $(\pm \Delta x, \pm \Delta y)$ aplicada a cada partícula en píxeles. (Defecto: `0.0`).
5. **`Seed` (`seed`):** Semilla determinista para la generación pseudoaleatoria de dispersión. (Defecto: `1`).
6. **`Scale` (`scale`):** Factor multiplicador de escala aplicado a las coordenadas del conjunto de partículas. (Defecto: `1.0`).
7. **`Anchor` (`anchor`):** Selector cíclico interactivo de perfil *Piece Anchor* idéntico a los nodos de fragmentación (`Slicer`, `Array`, `Union & Divide`). Determina cómo se proyectan las coordenadas locales de cada partícula y el centroide de rotación `\org` sobre el sistema de coordenadas de pantalla del subtítulo:
   * **`pieces` (Defecto canónico):** Cada micro-partícula se posiciona en sus coordenadas absolutas independientes `\pos(x, y)` calculadas a partir del centroide de su glifo o contorno base, y establece `\org(x, y)` exactamente en su propio baricentro. Esto permite que transformaciones posteriores (como giros `\frz`, escalados `\fscx/\fscy` o deformaciones angulares) roten cada partícula de forma autónoma sobre su propio eje.
   * **`relative`:** Conserva el origen de coordenadas relativo al centroide base del texto o forma padre, sin sobreescribir `pos_overridden`.
   * **`parent_org`:** Posiciona la partícula en sus coordenadas absolutas `\pos(x, y)`, pero ancla el centro de rotación `\org` en el origen global del texto o línea padre (`parent_x, parent_y`), permitiendo giros orbitales coordinados alrededor del elemento origen.
   * **`pos`:** Posiciona la partícula en sus coordenadas absolutas `\pos(x, y)` sin forzar una etiqueta `\org` explícita (`has_org = False`).
   * **`absolute`:** Integra las coordenadas absolutas directamente horneadas en los vértices del trazado vectorial (`m x y ...`), situando `\pos` en el origen padre y desactivando `pos_overridden`.
8. **`Order` (`order`):** Selector cíclico interactivo de perfil 2D (*Numpad Order*) para la secuencia de recorrido y asignación de índices iterativos (`p_i`):
   * `"79"`: Arriba-Izquierda $\to$ Abajo-Derecha (*Top-Left to Bottom-Right*).
   * `"97"`: Arriba-Derecha $\to$ Abajo-Izquierda (*Top-Right to Bottom-Left*).
   * `"13"`: Abajo-Izquierda $\to$ Arriba-Derecha (*Bottom-Left to Top-Right*).
   * `"31"`: Abajo-Derecha $\to$ Arriba-Izquierda (*Bottom-Right to Top-Left*).
   * `"71"`: Columna vertical descendente izquierda (Arriba-Izquierda $\to$ Abajo-Izquierda).
   * `"17"`: Columna vertical ascendente izquierda (Abajo-Izquierda $\to$ Arriba-Izquierda).
   * `"93"`: Columna vertical descendente derecha (Arriba-Derecha $\to$ Abajo-Derecha).
   * `"39"`: Columna vertical ascendente derecha (Abajo-Derecha $\to$ Arriba-Derecha).
   * `"5"`: Radial centrífugo desde el centro hacia el exterior (*Inside-Out*).
   * `"-5"`: Radial centrípeto desde el exterior hacia el centro (*Outside-In*).
   * `"cw"`: Radial circular en sentido horario (*Clockwise*).
   * `"ccw"`: Radial circular en sentido antihorario (*Counter-Clockwise*).
   * `"rand"`: Desorden pseudoaleatorio (*Shuffle*).
   * `"path"`: **Trayectoria perimetral continua.** Preserva el orden secuencial de arco en que se calculan los vértices del contorno vectorial ($s \in [0, L]$). Actúa de forma análoga a un nodo *Walker* integrado, permitiendo que cascadas de tags, apariciones y desvanecimientos sigan fielmente el trazo caligráfico o la silueta original.
   * `"path_inv"`: **Trayectoria perimetral invertida.** Recorre el contorno en sentido retrógrado ($s \in [L, 0]$).

---

### 13.3. Puertos de Salida (*Outputs*)
1. **`[1.1] Shp Out`:** Bloque combinado con la etiqueta de posición absoluta y la partícula vectorial: `{\pos(X, Y)}forma_particula`.
2. **`[1.2] \pos Tag`:** Etiqueta ASS de posición cartesiana puntual `\pos(X, Y)`.
3. **`[1.3] X Arr`:** Coordenada cartesiana horizontal $X$ de la partícula activa (px).
4. **`[1.4] Y Arr`:** Coordenada cartesiana vertical $Y$ de la partícula activa (px).
5. **`[1.5] Total`:** Cantidad total $N$ de partículas generadas en el enjambre.

#### Variables Inyectadas al Contexto:
* `p_i` / `tp_i`: Índice de la partícula actual evaluada ($1 \dots N$).
* `p_n` / `tp_n` / `maxloop`: Cantidad total de partículas en el enjambre ($N$).
* `x, y` / `fx_pos_x, fx_pos_y`: Coordenadas cartesianas absolutas de la partícula activa.

---

### 13.4. Detalle Algorítmico y Muestreo Espacial

```
Modo Outline (Perímetro):            Modo Inner Fill (Ray-Casting):
      ● ─── ● ─── ●                        ●   ●   ●   ●   ● (Fuera)
     /             \                     ┌───────────────────┐
    ●               ●                    │   ●   ●   ●   ●   │ (Dentro: Cruces = 1)
     \             /                     │   ●   ●   ●   ●   │
      ● ─── ● ─── ●                      └───────────────────┘
```

#### 13.4.1. Muestreo Perimetral por Longitud de Arco
Para cada contorno vectorial cerrado $C = \{V_0, V_1, \dots, V_m, V_0\}$:
1. Se calcula la distancia acumulada de cada segmento:
   $$d_k = \|V_{k+1} - V_k\|, \quad D_{\text{total}} = \sum_{k=0}^m d_k$$
2. Se generan objetivos de muestreo equidistantes $s_j = j \cdot \text{density}$ para $j \in \left[0, \lfloor D_{\text{total}} / \text{density} \rfloor \right]$.
3. Cada punto objetivo se interpola linealmente en su segmento correspondiente y se perturba estocásticamente si $\text{RedrawDist} > 0$:
   $$P_j = P_{\text{interp}} + \begin{pmatrix} U(-\text{redraw\_dist}, \text{redraw\_dist}) \\ U(-\text{redraw\_dist}, \text{redraw\_dist}) \end{pmatrix} \cdot \text{scale}$$

#### 13.4.2. Muestreo de Relleno por Algoritmo Ray-Casting
1. Se extrae la caja delimitadora $(X_{\min}, Y_{\min}) \to (X_{\max}, Y_{\max})$ de todos los contornos.
2. Se genera una cuadrícula uniforme en pasos de tamaño $\Delta = \text{density}$.
3. Para cada nodo $(g_x, g_y)$, se proyecta un rayo horizontal hacia $+X$ y se contabiliza el número de intersecciones con los bordes de los polígonos:
   $$\text{inside} = \left(\sum \text{intersecciones}(g_x, g_y, \text{Bordes})\right) \pmod 2 \equiv 1$$
   Si el punto es interior, se incorpora al enjambre.

---

### 13.5. Sinergias y Buenas Prácticas
* **Desintegración Tipográfica en Partículas:** Conectar `Functions/Particles` a un `Loops/MaxLoop` configurado para iterar $N$ veces (`p_n`), animando la dispersión con `Time/Ipol` o `Functions/Polar to Cartesian` hacia direcciones divergentes.

### 13.6. Ejemplo Práctico de Producción
* **Dispersión Radial de Partículas Perimetrales desde el Glifo:**
  Muestreando el contorno de un glifo tipográfico con densidad de $8\text{ px}$, sustituyendo cada vértice por una micro-estrella y recorriéndolas del centro hacia los bordes (orden `"5"`):

  ```
  [Shape/Library: "Star"] ──► Particle ────────────────────────────┐
                                                                   ▼
  [Functions/Particles: mode=outline_v2, density=8.0, order="5"] ──► Shp Out ──► Return ──► [System/Output]
     Path / Origin: syl.shape
  ```

  * **Ejecución del Sub-bucle DAG Trace:**
    El motor detecta `Particles` en la cadena de `Output.Return`, extrae $N=24$ puntos a lo largo del perímetro del glifo, inyecta las variables de iteración `p_i` ($1 \dots 24$) y `p_n` ($24$) y ordena las coordenadas radialmente según su distancia al centroide del carácter.
  * **Línea ASS Emitida para la Primera Partícula ($p_i=1$, baricentro más cercano):**
    `Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\an5\pos(320.50,238.20)\p1}m 0 0 l 2 0 l 2 2 l 0 2{\p0}`

* **Efecto Caligráfico de Escritura con Partículas (Walker Integrado):**
  Al seleccionar `order="path"`, las partículas no se reordenan cartesiana ni radialmente, sino que se indexan progresivamente a lo largo del trazo perimetral ($s = 0 \to L$). Modulando la aparición con una fórmula en `Tags` (ej. `\alpha!by.p_i.ipol(0, 255, 0, fx.dur)!` o `\t((p_i/p_n)*syl.dur, ((p_i+1)/p_n)*syl.dur, \alpha&H00&)`), cada micro-partícula se ilumina secuencialmente siguiendo la silueta continua de la fuente o figura sin requerir el nodo `Shape/Walker`.

---

## 14. Nodo `Functions/Interpolator` (Interpolador Paramétrico Polimórfico)

* **Categoría Canónica:** `Functions` (UI: *Funciones / Interpolator*)
* **Propósito:** Motor de interpolación paramétrica universal multidominio. Permite realizar transiciones suaves entre dos o más valores ($V_1 \to V_2$) adaptándose automáticamente al tipo de dato subyacente: números escalares, colores (Hex o ASS), canales de transparencia alfa, bloques de etiquetas ASS o geometrías vectoriales completas (*morphing* con re-muestreo topológico).

![Functions/Interpolator](img/interpolador.png)

### 14.1. Puertos de Entrada y Propiedades del Cuerpo (*Inputs & Properties*)
1. **`Iterator` (`iterator`):** Valor de iteración o progreso actual. Acepta:
   * Nombres de iteradores de contexto (ej. `"i"`, `"j"`, `"char.i"`, `"syl.i"`, `"a_i"`).
   * Valores normalizados directos en rango $t \in [0.0, 1.0]$.
2. **`Total` (`total`):** Valor total de pasos para normalizar el iterador ($N$). Acepta `"N"`, `"maxloop"`, `"char.n"`, `"syl.n"`. (Defecto: `"N"`).
3. **`Accel` (`accel`):** Exponente de aceleración o relajación no lineal (*easing*). Un valor de `1.0` es lineal; $> 1.0$ acelera al final (*ease-in*); $< 1.0$ desacelera (*ease-out*). (Defecto: `"1.0"`).
4. **`V1` (`v1`):** Valor inicial en $t=0.0$. Acepta escalares, colores (`#FF0000`, `&H0000FF&`), tags (`\blur0\fscx100`) o formas ASSdraw (`m 0 0 l 50 0...`).
5. **`V2` (`v2`):** Valor final en $t=1.0$. También admite cadenas multi-parada separadas por coma o arrays JSON para crear transiciones de múltiples tramos ($V_1 \to V_2 \to V_3 \dots$).

---

### 14.2. Puertos de Salida (*Outputs*)
1. **`[1.1] Data`:** Resultado puntual interpolado correspondiente al progreso $t$ del iterador activo.
2. **`[1.2] Batch / List`:** Lista completa de todos los $N$ valores interpolados separados por comas `, ` para asignaciones en lote.

---

### 14.3. Detalle Algorítmico y Detección Polimórfica

```
Progreso Normalizado:   t = (Iterator - 1) / (Total - 1)   ───>   t_eased = t^Accel
                                                                      │
              ┌───────────────────┬───────────────────┬───────────────┴───────────────┐
              ▼                   ▼                   ▼                               ▼
       [ Escalares ]        [ Colores ]         [ Tags ASS ]                 [ ASSdraw (Morphing) ]
      V1 + (V2-V1)·t       RGB Interpolado    Keyframes Mezclados           Re-muestreo Equidistante
```

#### 14.3.1. Normalización y Easing
Dado el iterador $i$ y el total $N$:
$$t = \begin{cases} i & \text{si } 0.0 \le i \le 1.0 \text{ y } N=1 \\ \frac{i - 1}{N - 1} & \text{si } N > 1 \\ 0.0 & \text{en otro caso} \end{cases}$$
$$t_{\text{eased}} = \begin{cases} t^{\text{accel}} & \text{si } \text{accel} > 1.0 \\ 1.0 - (1.0 - t)^{1.0 / \text{accel}} & \text{si } 0.0 < \text{accel} < 1.0 \\ t & \text{si } \text{accel} = 1.0 \end{cases}$$

#### 14.3.2. Mecánicas por Tipo de Dato
1. **Geometrías ASSdraw (*Morphing* Vectorial):**
   * Extrae los contornos de ambas formas con Clipper2.
   * Re-muestrea ambos contornos a una cantidad idéntica de vértices $M = \max(|C_1|, |C_2|, 30)$ distribuidos uniformemente por longitud de arco.
   * Interpola linealmente cada par de vértices homólogos:
     $$P_k(t) = (1 - t_{\text{eased}}) \cdot P_{1,k} + t_{\text{eased}} \cdot P_{2,k}$$
   * Reconstruye el trazado ASSdraw continuo resultante.
2. **Colores Hex / ASS:**
   * Descompone los canales $(R_1, G_1, B_1)$ y $(R_2, G_2, B_2)$ e interpola independientemente cada canal en espacio lineal.
3. **Bloques de Etiquetas ASS (*Keyframing*):**
   * Parsea numéricamente las etiquetas presentes en ambos bloques (`\fscx`, `\fscy`, `\frz`, `\alpha`, `\blur`, etc.) e interpola cada atributo de forma algebraica.
4. **Valores Numéricos Escalares:**
   * $V(t) = V_1 + (V_2 - V_1) \cdot t_{\text{eased}}$, formateado limpiamente como entero si carece de decimales.

---

### 14.4. Sinergias y Buenas Prácticas
* **Morphing Vectorial Fluido:** Conectar una primitiva `"Circle"` a `V1` y una primitiva `"Star"` a `V2`, conectando la salida `Data` a `System/Output` dentro de un `Loops/MaxLoop` para lograr una metamorfosis suave entre ambas geometrías.

### 14.5. Ejemplo Práctico de Producción
* **Metamorfosis Vectorial (Morphing) de Círculo a Estrella en 10 Pasos FBF:**
  Interpolando continuamente las geometrías de dos primitivas vectoriales re-muestreadas por Clipper2 con aceleración no lineal (`accel=1.5`):

  ```
  [Loops/MaxLoop: total=10] ──► j ──► Iterator ──────────────────┐
                                                                 ▼
  [Functions/Interpolator: total=10, accel=1.5] ──► Data ──► Shape / Text ──► [System/Output]
     v1: "m 50 0 b 22 0...", v2: "m 50 0 l 61 35..."
  ```

  * **Resultado ASS Emitido en el Subtítulo:**
    * **Iteración $j=1$ ($t=0.0$):** Emite `{\an5\pos(320, 240)\p1}m 50 0 l 44.8 0.5 ...` (contorno circular exacto re-muestreado a 30 nodos).
    * **Iteración $j=6$ ($t \approx 0.556, t_{\text{eased}} \approx 0.415$):** Emite la geometría intermedia con aristas abombadas en transición suave continua.
    * **Iteración $j=10$ ($t=1.0$):** Emite `{\an5\pos(320, 240)\p1}m 50 0 l 61 35 l 98 35 ...` (estrella regular completa).
    * La correspondencia topológica 1:1 de vértices evita colapsos de coordenadas o cruces indeseados de trazo durante el morphing.

---

## 15. Nodo `Functions/Text on Path` (Texto Adaptado sobre Curvas)

* **Categoría Canónica:** `Functions` (UI: *Funciones / Text on Path*)
* **Propósito:** Proyecta, distribuye y orienta cadenas de texto o glifos individuales a lo largo de un trazado vectorial ASSdraw o curva arbitraria. Calcula automáticamente la coordenada cartesiana y la rotación tangencial exacta (`\frz`) en cada punto para que el texto siga la curvatura natural del trazo.

![Functions/Text on Path](img/text_on_path.png)

### 15.1. Encabezado y Modos de Alineación (*Header Mode Combos*)
1. **`Center`:** Centra toda la cadena de texto sobre el punto medio de la longitud total del trazo vectorial.
2. **`Left`:** Alinea el inicio del texto en el comienzo del trazado ($d=0$) más el `Offset` configurado.
3. **`Right`:** Alinea el final del texto en el extremo terminal del trazado ($d=L_{\text{total}}$) menos el ancho del texto.
4. **`Justified`:** Distribuye uniformemente los caracteres o sílabas a lo largo de toda la longitud del trazo ($0.0 \to L_{\text{total}}$).
5. **`Animated`:** Mapea el parámetro `Offset` en un rango normalizado $0.0 \to 1.0$ para animar el recorrido continuo del texto fluyendo sobre la curva.

---

### 15.2. Puertos de Entrada y Propiedades del Cuerpo (*Inputs & Properties*)
1. **`Path / Shape` (`shape`):** Trazado vectorial ASSdraw que actúa como guía o riel espacial para el texto.
2. **`Offset` (`offset`):** Desfase de desplazamiento longitudinal sobre el trazo en píxeles (o progreso $0.0 \to 1.0$ en modo `Animated`). (Defecto: `"0"`).
3. **`Extra Angle` (`extra_angle`):** Rotación angular adicional en grados sexagesimales que se suma algebraicamente al ángulo tangencial calculado. (Defecto: `"0"`).
4. **`Subdivs` (`subdivs`):** Número de subdivisiones para el muestreo de curvas Bézier internas dentro del trazo guía. (Defecto: `"30"`).

---

### 15.3. Puertos de Salida (*Outputs*)
1. **`[1.1] Tag Out`:** Cadena combinada de etiquetas ASS de posicionamiento y rotación tangencial: `\pos(X, Y)\frz(Angle)`.
2. **`[1.2] \pos Tag`:** Etiqueta ASS exclusiva de posición `\pos(X, Y)`.
3. **`[1.3] Angle (\frz)`:** Etiqueta ASS exclusiva de rotación `\frz(Angle)`.
4. **`[1.4] X`:** Coordenada cartesiana horizontal puntual $X$ sobre la curva (px).
5. **`[1.5] Y`:** Coordenada cartesiana vertical puntual $Y$ sobre la curva (px).
6. **`[1.6] Length`:** Longitud de arco total $L_{\text{total}}$ del trazado vectorial guía en píxeles.

---

### 15.4. Detalle Algorítmico y Cinemática de Curvatura

```
                 P_tangente (X, Y)
                        ● ───> Vector Tangente (dx, dy)
                       / \
                      /   \ θ = atan2(dy, dx) - 90°
                     /     \
Ruta Guía: P_inicio ●       ● P_fin (L_total)
```

1. **Mapeo Métrico del Carácter en la Línea:**
   Dado el ancho métrico total de la línea de texto $L_{\text{line}}$ y la posición relativa del carácter activo $d_{\text{char}} = X_{\text{char}} - X_{\text{inicio}}$:
   $$d_{\text{target}} = \text{lineoffset} + d_{\text{char}}$$
2. **Localización Espacial en el Trazo:**
   Se busca el segmento $S_k$ donde cae la distancia $d_{\text{target}}$ acotada en $[0, L_{\text{total}}]$, evaluando el punto $(X, Y)$ y el vector de velocidad $(dx, dy)$.
3. **Cálculo de la Tangente e Inclinación:**
   $$\theta_{\text{base}} = \left( \operatorname{atan2}(dy, dx) \cdot \frac{180}{\pi} - 90^\circ \right) + \text{extra\_angle}$$
   El ángulo se normaliza en el rango $(-180^\circ, 180^\circ]$ para evitar saltos bruscos de giro en libass.

---

### 15.5. Sinergias y Buenas Prácticas
* **Curvas Dinámicas con `Functions/Bezier Curve`:** Conectar la salida `Spline` de un `Bezier Curve` a la entrada `Path / Shape` de `Text on Path`, vinculando `Offset` a un oscilador temporal para hacer que el texto ondulé continuamente a lo largo de una ola sinusoidal o spline dinámico.

### 15.6. Ejemplo Práctico de Producción
* **Distribución Justificada de Glifos a lo Largo de un Arco Guía:**
  Proyectando los caracteres de una palabra sobre un trazado vectorial parabólico `m 100 250 b 200 150 300 150 400 250` en modo `justified`:

  ```
  [Shape/Library: "Arc"] ──► Path / Shape ────────────────────────┐
                                                                  ▼
  [Functions/Text on Path: mode=justified, subdivs=30] ──► Tag Out ──► Tags In ──► [System/Output]
                                                                                    Return: char.text
  ```

  * **Mapeo Paramétrico por Carácter:**
    Para una palabra de 3 caracteres con iterador activo `char.i` ($1, 2, 3$):
    * Carácter 1 ($d=0\text{ px}$, inicio del arco): $P_1(100.0, 250.0)$, tangente $\theta = -45^\circ \to$ Emite `{\pos(100,250)\frz-45}K`.
    * Carácter 2 ($d=L/2$, ápice del arco): $P_2(250.0, 175.0)$, tangente horizontal $\theta = 0^\circ \to$ Emite `{\pos(250,175)\frz0}a`.
    * Carácter 3 ($d=L$, extremo final): $P_3(400.0, 250.0)$, tangente descendente $\theta = 45^\circ \to$ Emite `{\pos(400,250)\frz45}r`.

---

## 16. Nodo `Functions/Text to Shape` (Vectorización Tipográfica de Glifos)

* **Categoría Canónica:** `Functions` (UI: *Funciones / Text to Shape*)
* **Propósito:** Rasteriza y vectoriza glifos de fuentes tipográficas TrueType/OpenType a trazados vectoriales matemáticos ASSdraw (`m ... b ... l ...`). Permite convertir cualquier texto de sílaba, línea o constante alfanumérica en una geometría vectorial manipulable por operaciones booleanas, segmentadores morfológicos (*Slicer*), extrusión de bordes concéntricos o enjambres de partículas.

![Functions/Text to Shape](img/text_to_shape.png)

### 16.1. Puertos de Entrada y Propiedades del Cuerpo (*Inputs & Properties*)
1. **`Text` (`text`):** Cadena de texto a vectorizar. Si está vacía, extrae automáticamente el texto despojado de tags de la sílaba o carácter activo en el contexto (`syl.text_stripped` o `line.text_stripped`).
2. **`Font` (`font_name`):** Nombre de la familia tipográfica (ej. `"Arial"`, `"Montserrat"`, `"Impact"`). Si está vacío, hereda la fuente del estilo de subtítulo ASS activo.
3. **`Size` (`font_size`):** Tamaño de fuente en puntos tipográficos. Si está vacío, hereda el tamaño del estilo ASS activo.
4. **`Scale` (`scale`):** Factor multiplicador de escala geométrica aplicado a las coordenadas vectoriales generadas. (Defecto: `"1.0"`).
5. **`Bold` (`bold`):** [Propiedad] Forzado de estilo en negrita (`true` / `false`).
6. **`Italic` (`italic`):** [Propiedad] Forzado de estilo en cursiva (`true` / `false`).

---

### 16.2. Puertos de Salida (*Outputs*)
1. **`[1.1] Shape Out`:** Trazado vectorial ASSdraw completo con comandos de movimiento `m`, líneas `l` y curvas Bézier `b` cerrado y centrado.
2. **`[1.2] Width`:** Ancho total métrico en píxeles de la caja delimitadora del vector generado ($W$).
3. **`[1.3] Height`:** Altura total métrica en píxeles de la caja delimitadora del vector generado ($H$).

---

#### 16.3. Detalle Algorítmico y Motor de Vectorización Tipográfica Subpíxel

```
Fuente TrueType/OpenType ───> FontVectorEngine (Win32 GDI 64x Subpixel) ───> FontVectorMetrics (Sin Pérdida)
                                                                                  │
                ┌─────────────────────────────────────────────────────────────────┴─────────────────────────────────────────────────────────────────┐
                ▼                                                                                                                                   ▼
   [ Trazado ASSdraw `m...b...l...` ]                                                                                  [ Ficha Métrica Integral (O(1)) ]
       Para Slicer, Array, Morphs                                                                                   advance_width, cell_height, ascent, descent,
                                                                                                                    lsb, rsb, ink_bbox, delta_x, delta_y
```

1. **Extracción Vectorial en Subpíxel Nativo (64x):** `FontVectorEngine` consulta las tablas de contornos de la fuente tipográfica activa mediante la API Win32 GDI a escala subpíxel 64x (`ExtTextOutW` con `BeginPath`), extrayendo splines cuadráticos y cúbicos de los glifos como curvas Bézier cúbicas normalizadas ASSdraw (`b cp1x cp1y cp2x cp2y endx endy`).
2. **Retención Métrica No Destructiva (`FontVectorMetrics`):** A diferencia de los conversores convencionales que descartan las propiedades de la celda tipográfica, `FontVectorEngine` calcula simultáneamente:
   * **Rodamientos Laterales (*Side Bearings*):** $\text{LSB}$ (margen izquierdo) y $\text{RSB}$ (margen derecho), satisfaciendo la identidad tipográfica:
     $$\text{Advance Width} = \text{LSB} + \text{Ink Width} + \text{RSB}$$
   * **Desfase Baricéntrico ($\Delta X, \Delta Y$):** Desplazamiento exacto entre el centro de avance de la pluma y el baricentro geométrico de la tinta:
     $$\Delta X = \frac{\text{LSB} - \text{RSB}}{2}$$
   * **Alturas de Celda y Línea Base:** $\text{ascent}$, $\text{descent}$ y $\text{cell\_height}$, asegurando congruencia vertical absoluta.
3. **Modos de Anclaje (*Anchor Modes*):**
   * **`typographic` (Por defecto):** Origen centrado en el espacio de avance del texto, garantizando calce idéntico con `\pos(line.center, line.middle)` de libass.
   * **`ink`:** Origen centrado en el baricentro físico de la tinta, ideal para mallas morfológicas y explosión de partículas.
   * **`baseline` / `origin`:** Origen fijado en la línea base de la pluma tipográfica.

---

### 16.4. Sinergias y Buenas Prácticas
* **Segmentación Voronoi de Texto con `Shape/Slicer`:** Conectar `Text to Shape` $\to$ `Shape/Slicer (Voronoi)` para fragmentar un texto en trozos poligonales y animar su explosión o desintegración tridimensional.
* **Fusión Monolítica con `Shape/Union & Divide (FUSION)`:** Conectar `Text to Shape` a `Union & Divide` en modo `FUSION` para emitir subtítulos de línea única optimizados sin sobrecargar el motor de renderizado de libass.

### 16.5. Ejemplo Práctico de Producción
* **Vectorización Subpíxel y Extrusión con Trazo Grueso:**
  Transformando el texto de la sílaba activa en geometría vectorial nativa ASSdraw para aplicarle un borde vectorial continuo mediante `Shape/Stroke`:

  ```
  [Variables/Sys Var: var_name=syl.text] ──► Text ─────────────────┐
                                                                   ▼
  [Functions/Text to Shape: font_name="Arial", font_size="50"] ──► Shape Out ──► Shape / Text ──► [Shape/Stroke: width=4.0]
                                                                                                    │
                                                                                                    ▼ Shape Out
                                                                                                 Return ──► [System/Output]
  ```

  * **Extracción Vectorial y Métrica Subpíxel:**
    `FontVectorEngine` vectoriza el glifo a resolución 64x generando curvas cúbicas normalizadas `m ... b ...`, calculando $W = 42\text{ px}, H = 48\text{ px}$ y reteniendo el offset baricéntrico tipográfico.
  * **Línea ASS Emitida en el Script:**
    `Dialogue: 0,0:00:01.00,0:00:03.00,Default,,0,0,0,,{\an5\pos(320,240)\p1}m 0 25 b 0 10 12 0 25 0 b 38 0 50 10 50 25 ...{\p0}`
