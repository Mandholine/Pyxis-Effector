# Times

La categoría **Time** gestiona el cálculo cronométrico de eventos de subtítulos ASS, permitiendo desfasar fases fonéticas, modular transiciones temporales continuas (`\t`), computar equivalencias de fotogramas e interconectar líneas consecutivas mediante sincronización adaptativa.

### Organización Temática del Volumen:
* **Sección 7.A — Fases Principales, Retiming y Sincronización Inter-Línea:** `Time/Retime` (§1), `Time/Lead In` (§2), `Time/Lead Out` (§3), `Time/Synced` (§4).
* **Sección 7.B — Secciones Intermedias, Bucles y Métricas de Duración:** `Time/Middle 1` (§5), `Time/Middle 2` (§6), `Time/Loop 1` (§7), `Time/Loop 2` (§8), `Time/Duration` (§14), `Time/Offset` (§15).
* **Sección 7.C — Conversión de Formatos, Fotogramas e Interpolación Temporal:** `Time/Parse ASS Time` (§9), `Time/Format ASS Time` (§10), `Time/Time to Frame` (§11), `Time/Frame to Time` (§12), `Time/Ipol` (§13).

---

## 1. Nodo `Time/Retime` (Re-temporización de Fases y Mapeo de `\t`)

* **Categoría Canónica:** `Time` (UI: *Time / Retime*)
* **Propósito:** Re-sincroniza intervalos temporales y re-escala bloques de transformación continua `\t(...)` de ASS según la fase fonética o estructural del elemento activo (`syl`, `line`, `presyl`, `postsyl`, etc.), permitiendo desfases aditivos y aceleración no lineal.

![Time/Retime](img/retime.png)

### 1.1. Encabezado y Modos de Cabecera (*Header Mode Combos*)
1. **`[2.1] Mode` (`phase`):** Selector desplegable que determina el intervalo base de referencia temporal. Dispone de 10 modos de fase fonética y estructural:

| Modo (`phase`) | Intervalo Base [$T_1, T_2$] | Descripción Técnica |
| :--- | :--- | :--- |
| `syl` | $[T_{\text{syl\_start}}, T_{\text{syl\_end}}]$ | **Sílaba Activa (Defecto):** Ventana temporal exacta del canto de la sílaba o carácter. |
| `presyl` | $[T_{\text{syl\_start}}, T_{\text{syl\_start}}]$ | **Pre-Sílaba:** Momento instantáneo de inicio de la sílaba (para efectos preparatorios o transiciones de entrada). |
| `postsyl` | $[T_{\text{syl\_end}}, T_{\text{syl\_end}}]$ | **Post-Sílaba:** Momento instantáneo de finalización de la sílaba (para desvanecimientos o salidas inmediatas). |
| `line` | $[T_{\text{line\_start}}, T_{\text{line\_end}}]$ | **Línea Completa:** Ventana temporal global abarcada por la totalidad de la línea de diálogo. |
| `preline` | $[T_{\text{line\_start}}, T_{\text{line\_start}}]$ | **Pre-Línea:** Instante inicial de la línea. |
| `postline` | $[T_{\text{line\_end}}, T_{\text{line\_end}}]$ | **Post-Línea:** Instante final de la línea. |
| `start2syl` | $[T_{\text{line\_start}}, T_{\text{syl\_start}}]$ | **Entrada a Sílaba (*Lead-In*):** Intervalo desde el inicio de la línea hasta que comienza a cantarse la sílaba activa. |
| `syl2end` | $[T_{\text{syl\_end}}, T_{\text{line\_end}}]$ | **Sílaba al Final (*Lead-Out*):** Intervalo desde que finaliza la sílaba activa hasta que concluye la línea completa. |
| `abs` | $[0, 0]$ | **Absoluto:** Desvincula los tiempos relativos a la sílaba/línea; los valores de `Offset In` y `Offset Out` definen directamente la ventana numérica milimétrica. |
| `sylpct` | $[T_{\text{syl\_start}} + \frac{O_{\text{in}} \cdot D_{\text{syl}}}{100}, T_{\text{syl\_start}} + \frac{O_{\text{out}} \cdot D_{\text{syl}}}{100}]$ | **Porcentaje de Sílaba:** Los desfases `Offset In` y `Offset Out` se interpretan como porcentajes ($0\% \dots 100\%$) de la duración de la sílaba. |

### 1.2. Puertos de Entrada y Propiedades del Cuerpo (*Inputs & Properties*)
1. **`Tags or \t` (`tags`):** Cadena de texto con etiquetas ASS. Puede recibir etiquetas estáticas directas (ej. `\fscx150\fscy150\alpha&HFF&`) o bloques de transformación continua `\t(...)` ya existentes.
2. **`Offset In (ms)` (`offset_in`):** Desplazamiento temporal en milisegundos aplicado al punto inicial $T_1$. Acepta números positivos (retraso), negativos (adelanto) o variables/expresiones dinámicas (defecto: `0`).
3. **`Offset Out (ms)` (`offset_out`):** Desplazamiento temporal en milisegundos aplicado al punto final $T_2$ (defecto: `0`).
4. **`Accel` (`accel`):** Exponente de aceleración de la interpolación ASS en la etiqueta `\t(t1, t2, accel, \tags)`. Un valor de `1.0` genera velocidad constante lineal; valores $< 1.0$ producen desaceleración (*ease-out*); valores $> 1.0$ generan aceleración progresiva (*ease-in*) (defecto: `1.0`).

### 1.3. Puertos de Salida (*Outputs*)
1. **`[1.1] \t Out`:** Bloque de etiquetas formateado en sintaxis ASS `\t(t1, t2, [accel,] \tags)`. Los tiempos $t_1$ y $t_2$ se emiten en el espacio temporal local de la línea de subtítulo (relativos a `0 ms` del inicio de la línea física generada).
2. **`[1.2] Start Time`:** Marca de tiempo inicial absoluta $T_1$ en milisegundos sobre la línea de tiempo global del video.
3. **`[1.3] End Time`:** Marca de tiempo final absoluta $T_2$ en milisegundos sobre la línea de tiempo global del video.
4. **`[1.4] Duration`:** Duración neta calculada en milisegundos: $D = \max(0, T_2 - T_1)$.

### 1.4. Modelo Matemático y Mapeo de Etiquetas `\t`

```
   Inicio Línea                                            Fin Línea
   ├──────────────────────────┬─────────────────┬──────────────────┤
   │        start2syl         │  syl (activa)   │     syl2end      │
   │                          ├────────┬────────┤                  │
   │                          │ presyl │ postsyl│                  │
───┴──────────────────────────┴────────┴────────┴──────────────────┴───► Tiempo
   0 ms                      T_syl_st  T_syl_et  Line_dur
```

#### 1.4.1. Transformación de Bloques `\t(...)` Existentes
Cuando la entrada `Tags or \t` contiene bloques de transformación continua `\t(t_a, t_b, ...)`, el nodo analiza la expresión y recalcula los tiempos relativos preservando los sub-intervalos internos:

$$\tilde{t}_1 = T_{\text{local\_1}} + t_a, \quad \tilde{t}_2 = T_{\text{local\_1}} + t_b$$

Si la etiqueta `\t(...)` no especificaba tiempos previos (ej. `\t(\blur10)`), el nodo inyecta automáticamente la ventana completa calculada de la fase:

$$\text{\textbackslash t}(T_{\text{local\_1}}, T_{\text{local\_2}}, [a,] \text{\textbackslash blur10})$$

#### 1.4.2. Dualidad de Espacios Temporales (Local vs. Global)
> [!IMPORTANT]
> * **Salida `\t Out`:** Opera siempre en tiempo **relativo al inicio de la línea física** ($t=0\text{ ms}$). Esto es indispensable porque la etiqueta `\t` del estándar ASS mide el desfase respecto al tiempo de inicio de la propia línea de subtítulo en pantalla.
> * **Salidas `Start Time` y `End Time`:** Emiten tiempos **absolutos de video**, requeridos cuando se configuran eventos independientes en el nodo `System/Output`.

### 1.5. Sinergias y Buenas Prácticas
* **Efectos de Entrada y Salida Independientes:** Emplear dos nodos `Retime`: uno configurado en `Mode: start2syl` para la animación de entrada (*Lead-In*), y otro en `Mode: syl2end` o `postsyl` para la animación de salida (*Lead-Out*).
* **Encadenamiento con Moduladores:** Conectar la salida `\t Out` al nodo `Concatenate` junto con posiciones `\pos` y estilos base para construir líneas ASS completas en un solo flujo.

### 1.6. Ejemplo Práctico de Producción
* **Transformación Continua en Entrada con Retime:**
  Generando una animación de entrada (*lead-in*) donde cada sílaba escala de 0% a 100% y desvanece de transparente a opaca antes de cantarse:

  ```
  Tags In: \fscx100\fscy100\alpha&H00& ──► Tags or \t ──► [Time/Retime: start2syl, accel=0.8]
                                                                └──► \t Out ──► Tags ──► [System/Output]
  ```

  Alimentando `Tags` de `System/Output` con estilo base `{\an5\pos(syl.center, syl.middle)\fscx0\fscy0\alpha&HFF&}`:
  El nodo resuelve numéricamente los tiempos en milisegundos y emite:
  ```
  {\an5\pos(320, 240)\fscx0\fscy0\alpha&HFF&\t(0, 180, 0.8, \fscx100\fscy100\alpha&H00&)}
  ```
  La sílaba transiciona suavemente durante el intervalo de entrada (*start2syl*) con curva desacelerada (*ease-out*, `accel=0.8`).

---

## 2. Nodo `Time/Lead In` (Desfase Escalonado de Entrada)

* **Categoría Canónica:** `Time` (UI: *Time / Lead In*)
* **Propósito:** Calcula un instante temporal o desplazamiento negativo escalonado según el índice secuencial de la unidad activa ($i$), generando cascadas y transiciones anticipadas previas al canto de la sílaba o carácter.

![Time/Lead In](img/lead_in.png)

### 2.1. Puertos de Entrada y Propiedades del Cuerpo (*Inputs & Properties*)
1. **`Delay (ms)` (`delay_ms`):** Tiempo de retardo escalonado por unidad en milisegundos. Acepta constantes numéricas, variables o expresiones aritméticas inline (defecto: `40`).

### 2.2. Puertos de Salida (*Outputs*)
1. **`[1.1] Data`:** Valor temporal en milisegundos resultante de la fórmula de escalonamiento.

### 2.3. Formulación Matemática del Desfase Escalonado
El nodo evalúa el índice de la unidad activa $i \in \{1, \dots, N\}$ (donde $i$ es el número de sílaba o carácter en el ciclo) y aplica un margen fijo de anticipación de $200\text{ ms}$:

$$T_{\text{out}} = T_{\text{base}} + \Delta_{\text{delay}} \cdot (i - 1) - 200$$

Donde:
* $T_{\text{base}}$ es el tiempo de referencia base (por defecto $0.0\text{ ms}$).
* $\Delta_{\text{delay}}$ es el valor configurado en `Delay (ms)`.
* $i$ es el índice de la sílaba o glifo actual ($1$-based).
* $-200\text{ ms}$ es la constante de anticipación cinemática estándar (*lookahead*).

#### Ejemplo de Progresión ($N=4\text{ unidades}, \Delta=40\text{ ms}$):
* Unidad $1$ ($i=1$): $40 \cdot (1 - 1) - 200 = -200\text{ ms}$
* Unidad $2$ ($i=2$): $40 \cdot (2 - 1) - 200 = -160\text{ ms}$
* Unidad $3$ ($i=3$): $40 \cdot (3 - 1) - 200 = -120\text{ ms}$
* Unidad $4$ ($i=4$): $40 \cdot (4 - 1) - 200 = -80\text{ ms}$

### 2.4. Sinergias y Buenas Prácticas
* **Alimentación de `Retime`:** Conectar la salida `Data` de `Lead In` al puerto `Offset In (ms)` de un nodo `Retime` (en modo `syl` o `start2syl`) para generar una aparición en oleada fluida donde cada letra comienza a animarse secuencialmente antes de su tiempo de canto.

### 2.5. Ejemplo Práctico de Producción
* **Aparición en Cascada Anticipada con Lead In y Retime:**
  Encadenando `Lead In` hacia el puerto `Offset In (ms)` de un nodo `Retime`:

  ```
  [Time/Lead In: delay_ms=40] ──► Data ──► Offset In (ms) ──► [Time/Retime: syl, accel=1.0]
                                                                    └──► \t Out ──► Tags ──► [System/Output]
  ```

  Si la entrada `Tags or \t` de `Retime` recibe `\fscx130\fscy130\1c&H00FFFF&`:
  Para una línea de 4 sílabas, cada elemento comienza a resaltar $200 - 40 \cdot (i - 1)$ ms antes de su canto, creando una oleada continua que anticipa la lectura fonética.

---

## 3. Nodo `Time/Lead Out` (Desfase Escalonado de Salida)

* **Categoría Canónica:** `Time` (UI: *Time / Lead Out*)
* **Propósito:** Calcula un instante temporal o extensión escalonada según la distancia de la unidad activa respecto al final de la línea ($i - n$), generando desvanecimientos progresivos y salidas coordinadas posteriores al canto.

![Time/Lead Out](img/lead_out.png)

### 3.1. Puertos de Entrada y Propiedades del Cuerpo (*Inputs & Properties*)
1. **`Delay (ms)` (`delay_ms`):** Retardo en milisegundos aplicado al escalonamiento de salida (defecto: `40`).

### 3.2. Puertos de Salida (*Outputs*)
1. **`[1.1] Data`:** Valor temporal en milisegundos resultante de la fórmula de salida escalonada.

### 3.3. Formulación Matemática de la Salida Escalonada
El nodo evalúa la posición relativa de la unidad $i$ respecto al total de elementos $n$:

$$T_{\text{out}} = T_{\text{base}} + \Delta_{\text{delay}} \cdot (i - n - 1) + 200$$

Donde:
* $n$ es el número total de unidades en la línea (`syl.n`, `char.n`).
* $+200\text{ ms}$ es la constante de sostenimiento temporal posterior.

#### Ejemplo de Progresión ($n=4\text{ unidades}, \Delta=40\text{ ms}$):
* Unidad $1$ ($i=1$): $40 \cdot (1 - 4 - 1) + 200 = 40 \cdot (-4) + 200 = +40\text{ ms}$
* Unidad $2$ ($i=2$): $40 \cdot (2 - 4 - 1) + 200 = 40 \cdot (-3) + 200 = +80\text{ ms}$
* Unidad $3$ ($i=3$): $40 \cdot (3 - 4 - 1) + 200 = 40 \cdot (-2) + 200 = +120\text{ ms}$
* Unidad $4$ ($i=4$): $40 \cdot (4 - 4 - 1) + 200 = 40 \cdot (-1) + 200 = +160\text{ ms}$

### 3.4. Sinergias y Buenas Prácticas
* **Desaparición Progresiva:** Conectar a `Offset Out (ms)` en `Retime` (en modo `syl` o `postsyl`) para asegurar que la primera sílaba desaparezca primero y la última permanezca más tiempo en pantalla, respetando el sentido de lectura natural.

### 3.5. Ejemplo Práctico de Producción
* **Desvanecimiento Progresivo Posterior con Lead Out:**
  Conectando `Lead Out` a `Offset Out (ms)` en un nodo `Retime` en modo `postsyl`:

  ```
  [Time/Lead Out: delay_ms=50] ──► Data ──► Offset Out (ms) ──► [Time/Retime: postsyl]
                                                                     └──► \t Out ──► Tags ──► [System/Output]
  ```

  Con `Tags or \t: \alpha&HFF&`:
  La primera sílaba inicia su desvanecimiento poco después de cantarse, mientras que las últimas sílabas retienen su visibilidad en pantalla durante un intervalo mayor, evitando que el texto desaparezca de golpe.

---

## 4. Nodo `Time/Synced` (Sincronización Adaptativa Inter-Línea)

* **Categoría Canónica:** `Time` (UI: *Time / Synced*)
* **Propósito:** Calcula dinámicamente el tiempo extra de sostenimiento entre líneas consecutivas de diálogo. Evita cortes abruptos rellenando silencios/pausas musicales, compensa la distancia espacial geométrica entre frases en pantalla y suaviza la transición hacia la siguiente línea.

![Time/Synced](img/synced.png)

### 4.1. Puertos de Entrada y Propiedades del Cuerpo (*Inputs & Properties*)
1. **`Mode` (`mode`):** Criterio de búsqueda para emparejar con la siguiente línea (`next_line`):
   * `order`: Respeta estrictamente el orden secuencial de la lista de líneas activas sin filtros.
   * `style`: Busca la siguiente línea que comparta exactamente el mismo estilo (`style_name`).
   * `actor`: Busca la siguiente línea que comparta exactamente el mismo actor (`actor`).
   * `layer`: Busca la siguiente línea que comparta el mismo número de capa ASS (`layer`).
   * `effect`: Busca la siguiente línea que comparta el mismo campo de efecto ASS (`effect`).
2. **`Constant` (`progression_const`):** Coeficiente multiplicador de progresión por densidad de caracteres (ms por glifo) (defecto: `0`).
3. **`Fade (ms)` (`fade_dur`):** Duración del desvanecimiento visual (*fade-out*) previsto en milisegundos (defecto: `300`).
4. **`Max Extra` (`max_added_time`):** Límite máximo (*cap*) de tiempo extra en milisegundos que se permite añadir a la línea (defecto: `2000`).
5. **`Delay Line` (`delay_ms`):** Tiempo mínimo de separación requerido para considerar que existe una brecha o pausa entre líneas (defecto: `250`).
6. **`Threshold` (`max_gap_threshold`):** Umbral de silencio máximo. Si la pausa musical entre la línea actual y la siguiente supera este umbral, el algoritmo asume que es una pausa larga independiente y no extiende la línea hasta la siguiente (defecto: `3000`).

### 4.2. Puertos de Salida (*Outputs*)
1. **`[1.1] Extra ms`:** Cantidad neta de milisegundos adicionales calculada ($\Delta t_{\text{extra}}$).
2. **`[1.2] Sync End`:** Marca de tiempo final absoluta sincronizada ($T_{\text{line\_end}} + \Delta t_{\text{extra}}$) lista para inyectar en el tiempo de fin de la línea ASS.

### 4.3. Detalle Algorítmico y Modelo de Compensación Espacio-Temporal

```
  Línea Actual                      Pausa / Gap                  Línea Siguiente
├──────────────────────┤◄────────────────────────────────►├──────────────────────┤
0 ms               Curr_End                            Next_Start            Next_End
                       │                                  │
                       └───► [ Sincronización Adaptativa ] ◄──┘
                             • Compensación espacial (Salto X)
                             • Progresión por caracteres
                             • Deducción de Fade-out
```

El algoritmo de sincronización ejecuta la siguiente secuencia de evaluación por cada línea:

#### 1. Densidad y Progresión Base de la Línea Actual ($P_{2,\text{curr}}$)
Se calcula la carga de lectura de la línea según su cantidad de elementos $C_{\text{curr}}$:
$$P_{2,\text{curr}} = k_{\text{prog}} \cdot \max(0, C_{\text{curr}} - 1) + \Delta_{\text{delay}}$$

#### 2. Evaluación de la Brecha Inter-Línea ($\Delta_{\text{gap}}$)
$$\Delta_{\text{gap}} = T_{\text{next, start}} - T_{\text{curr, end}}$$

* **Caso A (Línea Aislada o sin línea posterior):**
  $$\Delta t_{\text{extra}} = \min\left(M_{\text{max}}, \max(0, P_{2,\text{curr}})\right)$$

* **Caso B (Líneas Solapadas o continuas, $\Delta_{\text{gap}} < \Delta_{\text{delay}}$):**
  $$\Delta t_{\text{extra}} = 0.0\text{ ms}$$

* **Caso C (Pausa Excesiva / Silencio Largo, $\Delta_{\text{gap}} > \text{Threshold}$):**
  Se aplica la progresión natural de la línea sin forzar el puente hacia la siguiente:
  $$\Delta t_{\text{extra}} = \min\left(M_{\text{max}}, \max(0, P_{2,\text{curr}})\right)$$

* **Caso D (Puente Adaptativo Normal, $\Delta_{\text{delay}} \le \Delta_{\text{gap}} \le \text{Threshold}$):**
  El algoritmo analiza la ocupación espacial 2D de ambas líneas mediante sus límites de tinta (`ink`) o cajas tipográficas ($[X_{\text{min}}, X_{\text{max}}], [Y_{\text{min}}, Y_{\text{max}}]$) y sus coordenadas explícitas (`\pos`, `align`):

  1. **Subcaso D.1 — Desacopladas en Pantalla (Espacios Inconexos):**
     Si las líneas no comparten la misma franja vertical en pantalla (por ejemplo, cabecera superior en `\an8` vs. pie de página en `\an2`, o alturas verticales con desfase $|Y_{\text{curr}} - Y_{\text{next}}| > 0.5 \cdot \text{alto}$):
     * Se omite por completo la progresión por caracteres ($P_2 = 0$).
     * Se extiende la permanencia de la línea actual exclusivamente para rellenar la brecha hasta que la siguiente entre, coordinando su desvanecimiento:
       $$T_{\text{ideal\_end}} = T_{\text{next, start}} - \text{Fade}_{\text{dur}}$$

  2. **Subcaso D.2 — Mismo Espacio / Reemplazo con Anclaje Común:**
     Si ambas líneas comparten la misma franja vertical pero coinciden en el anclaje u origen lateral (por ejemplo, dos líneas consecutivas con alineación a la izquierda `\an4`, a la derecha `\an6` o centradas reemplazando el mismo renglón, donde la brecha horizontal $X_{\text{next, left}} - X_{\text{curr, right}} \le 0$):
     * Se activa la duración de transición promedio por densidad de caracteres:
       $$T_{\text{trans}} = \frac{P_{2,\text{curr}} + P_{2,\text{next}}}{2}$$
     * **Sin salto espacial ficticio:** No se suma compensación de desplazamiento hacia adelante ($\Delta t_{\text{spatial}} = 0.0\text{ ms}$).
       $$T_{\text{ideal\_end}} = T_{\text{next, start}} + T_{\text{trans}} - \text{Fade}_{\text{dur}}$$

  3. **Subcaso D.3 — Mismo Renglón Contiguo (Lectura y Animación Continua):**
     Si ambas líneas comparten la franja vertical y la siguiente línea está ubicada a continuación horizontalmente en sentido de lectura ($X_{\text{next, left}} > X_{\text{curr, right}}$):
     * Se calcula el salto geométrico horizontal:
       $$\text{Salto} = X_{\text{next, left}} - X_{\text{curr, right}}$$
       $$\Delta t_{\text{spatial}} = \left(\frac{\text{Salto}}{w_{\text{avg}}}\right) \cdot k_{\text{prog}}$$
     * Donde $w_{\text{avg}}$ se extrae fielmente de las métricas reales de los glifos medidos (`line.chars` vía `FontEngine`).
     * Tiempo ideal de finalización continuo:
       $$T_{\text{ideal\_end}} = T_{\text{next, start}} + T_{\text{trans}} + \Delta t_{\text{spatial}} - \text{Fade}_{\text{dur}}$$

  Finalmente, el tiempo extra neto se acota por el límite configurado:
  $$\Delta t_{\text{extra}} = \min\left(M_{\text{max}}, \max(0, T_{\text{ideal\_end}} - T_{\text{curr, end}})\right)$$

### 4.4. Sinergias y Buenas Prácticas
* **Relleno Automático en Karaokes Continuos:** Conectar la salida `Sync End` directamente al puerto `End Time` de `System/Output`. Esto garantiza que los subtítulos permanezcan visibles durante los silencios cortos y se desvanezcan exactamente cuando la siguiente línea aparece.
* **Integración con `Retime`:** Utilizar la salida `Extra ms` en el parámetro `Offset Out` de `Retime` (modo `line` o `postline`) para expandir las animaciones de fondo (*glow*, bordes concéntricos o partículas) al tiempo extra calculado.

### 4.5. Ejemplo Práctico de Producción
* **Puente Continuo Inter-Línea sin Cortes en Pausas Musicales:**
  Extendiendo la duración física de la línea actual mediante `Synced` conectado a `System/Output`:

  ```
  [Time/Synced: mode=style, fade_dur=300, max_extra=2500] ──► Sync End ──► End Time ──► [System/Output]
  ```

  En el bloque de tags:
  ```
  {\pos(line.center, line.bottom - 40)\fad(200, 300)}
  ```
  Si la siguiente línea comienza 1200 ms después, `Synced` extiende el tiempo final de la línea actual hasta $T_{\text{next, start}} - 300$, permitiendo que el `\fad` de 300 ms concluya exactamente cuando la nueva frase aparece en pantalla.

---

---

## 5. Nodo `Time/Middle 1` (Desfase Simétrico de Entrada Centrada)

* **Categoría Canónica:** `Time` (UI: *Time / Middle 1*)
* **Propósito:** Calcula un desplazamiento temporal simétrico por secciones respecto al centro geométrico/secuencial de la línea. Permite que las animaciones de entrada comiencen simultáneamente desde los extremos hacia el centro (convergentes) o desde el centro hacia los extremos (divergentes).

![Time/Middle 1](img/middle_1.png)

### 5.1. Puertos de Entrada y Propiedades del Cuerpo (*Inputs & Properties*)
1. **`Delay (ms)` (`delay_ms`):** Multiplicador de retardo en milisegundos por cada salto de unidad hacia/desde el centro. Acepta constantes numéricas, variables o expresiones evaluables (defecto: `30`).

### 5.2. Puertos de Salida (*Outputs*)
1. **`[1.1] Data`:** Marca de desplazamiento temporal en milisegundos calculada según la mitad en que se ubica la unidad activa.

### 5.3. Formulación Matemática de la Simetría de Entrada
El nodo divide la secuencia de $n$ unidades en dos mitades a partir del eje central $\frac{n + 1}{2}$. Evalúa el índice activo $i \in \{1, \dots, n\}$ aplicando una función por tramos:

$$\text{offset} = \begin{cases} 
\Delta_{\text{delay}} \cdot (i - 1) - 200, & \text{si } i \le \frac{n + 1}{2} \\[6pt]
\Delta_{\text{delay}} \cdot (n - i + 0.5) - 200, & \text{si } i > \frac{n + 1}{2}
\end{cases}$$

$$T_{\text{out}} = T_{\text{base}} + \text{offset}$$

Donde:
* $i$ es el índice secuencial de la sílaba o carácter activo ($1 \le i \le n$).
* $n$ es el número total de unidades en la línea (`syl.n` o `char.n`).
* $\Delta_{\text{delay}}$ es el valor configurado en `Delay (ms)`.
* $-200\text{ ms}$ es el margen de anticipación cinemática base (*lookahead*).

#### Ejemplo de Evaluación Simétrica ($n=4\text{ unidades}, \Delta=30\text{ ms}$, Punto medio $= 2.5$):
* Unidad $1$ ($i=1 \le 2.5$): $30 \cdot (1 - 1) - 200 = -200.0\text{ ms}$
* Unidad $2$ ($i=2 \le 2.5$): $30 \cdot (2 - 1) - 200 = -170.0\text{ ms}$
* Unidad $3$ ($i=3 > 2.5$): $30 \cdot (4 - 3 + 0.5) - 200 = 30 \cdot 1.5 - 200 = -155.0\text{ ms}$
* Unidad $4$ ($i=4 > 2.5$): $30 \cdot (4 - 4 + 0.5) - 200 = 30 \cdot 0.5 - 200 = -185.0\text{ ms}$

### 5.4. Sinergias y Buenas Prácticas
* **Ondas de Entrada en V (*Chevron / Wing In*):** Conectar la salida `Data` de `Middle 1` al puerto `Offset In (ms)` de `Time/Retime` (en modo `syl` o `start2syl`). Los extremos de la frase se animarán primero, convergiendo fluidamente hacia el centro.

### 5.5. Ejemplo Práctico de Producción
* **Onda Convergente de Entrada hacia el Centro:**
  Configuración con `Middle 1` alimentando `Offset In (ms)` en `Time/Retime`:

  ```
  [Time/Middle 1: delay_ms=35] ──► Data ──► Offset In (ms) ──► [Time/Retime: start2syl, accel=0.8]
                                                                    └──► \t Out ──► Tags ──► [System/Output]
  ```

  Con `Tags or \t: \fscx100\fscy100\1c&H00FFFF&` y estilo base `{\an5\fscx0\fscy0\1c&HFFFFFF&}`:
  Para una línea con 6 caracteres, las letras exteriores ($i=1$ e $i=6$) inician su escalado primero, seguidas progresivamente por las interiores hasta converger en las dos centrales ($i=3, 4$), creando una aparición simétrica en ala o flecha (*chevron*).

---

## 6. Nodo `Time/Middle 2` (Desfase Simétrico de Salida Centrada)

* **Categoría Canónica:** `Time` (UI: *Time / Middle 2*)
* **Propósito:** Calcula un desplazamiento temporal simétrico por secciones anclado al final de la línea ($T_{\text{end}}$). Permite que los desvanecimientos o transiciones de salida se coordinen simétricamente desde o hacia el centro de la frase.

![Time/Middle 2](img/middle_2.png)

### 6.1. Puertos de Entrada y Propiedades del Cuerpo (*Inputs & Properties*)
1. **`Delay (ms)` (`delay_ms`):** Multiplicador de retardo en milisegundos para el escalonamiento simétrico de salida (defecto: `30`).

### 6.2. Puertos de Salida (*Outputs*)
1. **`[1.1] Data`:** Desplazamiento temporal en milisegundos relativo al final de la unidad o línea.

### 6.3. Formulación Matemática de la Simetría de Salida
El cálculo de `Middle 2` invierte la orientación temporal para anclarse en la cola del evento:

$$\text{offset} = \begin{cases} 
\Delta_{\text{delay}} \cdot (i - n - 1) - 200, & \text{si } i \ge \frac{n + 1}{2} \\[6pt]
\Delta_{\text{delay}} \cdot (-i + 0.5) - 200, & \text{si } i < \frac{n + 1}{2}
\end{cases}$$

$$T_{\text{out}} = T_{\text{base}} + \text{offset}$$

#### Ejemplo de Evaluación Simétrica de Salida ($n=4\text{ unidades}, \Delta=30\text{ ms}$, Punto medio $= 2.5$):
* Unidad $1$ ($i=1 < 2.5$): $30 \cdot (-1 + 0.5) - 200 = 30 \cdot (-0.5) - 200 = -215.0\text{ ms}$
* Unidad $2$ ($i=2 < 2.5$): $30 \cdot (-2 + 0.5) - 200 = 30 \cdot (-1.5) - 200 = -245.0\text{ ms}$
* Unidad $3$ ($i=3 \ge 2.5$): $30 \cdot (3 - 4 - 1) - 200 = 30 \cdot (-2) - 200 = -260.0\text{ ms}$
* Unidad $4$ ($i=4 \ge 2.5$): $30 \cdot (4 - 4 - 1) - 200 = 30 \cdot (-1) - 200 = -230.0\text{ ms}$

### 6.4. Sinergias y Buenas Prácticas
* **Salidas en Cortina Espejada:** Conectar la salida `Data` de `Middle 2` a `Offset Out (ms)` en `Time/Retime` para sincronizar disoluciones o caídas de partículas donde los glifos centrales desaparecen antes o después que los laterales.

### 6.5. Ejemplo Práctico de Producción
* **Disolución Simétrica de Salida desde el Centro:**
  Conectando `Middle 2` al puerto `Offset Out (ms)` en `Time/Retime` en modo `postsyl`:

  ```
  [Time/Middle 2: delay_ms=40] ──► Data ──► Offset Out (ms) ──► [Time/Retime: postsyl]
                                                                     └──► \t Out ──► Tags ──► [System/Output]
  ```

  Con `Tags or \t: \alpha&HFF&`:
  Los glifos centrales concluyen su tiempo de canto e inician el desvanecimiento inmediatamente, mientras que los caracteres laterales permanecen sostenidos en pantalla durante más tiempo antes de apagarse, produciendo una apertura en cortina espejada.

---

## 7. Nodo `Time/Loop 1` (Temporizador para Sub-Bucles Primarios)

* **Categoría Canónica:** `Time` (UI: *Time / Loop 1*)
* **Propósito:** Genera desfases temporales escalonados o simétricos para las iteraciones generadas dentro de un sub-bucle secundario `Loops/MaxLoop` (modo normal o FBF), evaluando directamente la variable de iteración local $j$ (`fx_i`) frente al total de repeticiones $\text{maxj}$ (`fx_n`).

![Time/Loop 1](img/loop_1.png)

### 7.1. Encabezado y Modos de Cabecera (*Header Mode Combos*)
1. **`[2.1] Mode` (`mode`):** Determina el perfil cinemático de distribución temporal a lo largo de las $j$ iteraciones del sub-bucle:

| Modo (`mode`) | Ecuación de Desfase ($\text{offset}$) | Comportamiento Cinematográfico |
| :--- | :--- | :--- |
| `leadin` (Defecto) | $\Delta \cdot (j - 1) - 200$ | **Cascada Progresiva:** Cada sub-capa $j$ inicia secuencialmente tras la anterior con anticipación. |
| `leadout` | $\Delta \cdot (j - \text{maxj} - 1) + 200$ | **Salida Escalonada:** Las sub-capas concluyen en orden secuencial tras el final del evento. |
| `middle1` | $\begin{cases} \Delta \cdot (j - 1) - 200, & j \le \frac{\text{maxj}+1}{2} \\ \Delta \cdot (\text{maxj} - j + 0.5) - 200, & j > \frac{\text{maxj}+1}{2} \end{cases}$ | **Simetría de Entrada:** Las capas iteradas convergen desde los bordes del bucle hacia el centro. |
| `middle2` | $\begin{cases} \Delta \cdot (j - \text{maxj} - 1) - 200, & j \ge \frac{\text{maxj}+1}{2} \\ \Delta \cdot (-j + 0.5) - 200, & j < \frac{\text{maxj}+1}{2} \end{cases}$ | **Simetría de Salida:** Salida simétrica centrada respecto al conjunto de sub-iteraciones. |

### 7.2. Puertos de Entrada y Propiedades del Cuerpo (*Inputs & Properties*)
1. **`Delay (ms)` (`delay_ms`):** Tiempo de desfase en milisegundos aplicado entre iteraciones consecutivas del sub-bucle (defecto: `30`).

### 7.3. Puertos de Salida (*Outputs*)
1. **`[1.1] Data`:** Valor temporal en milisegundos calculado para la iteración actual $j$.

### 7.4. Ciclo de Vida y Variables Consumidas
> [!NOTE]
> A diferencia de `Lead In` o `Middle 1` (que leen el índice $i \in [1, n]$ del elemento silábico/carácter en el `Main Loop`), `Time/Loop 1` inspecciona automáticamente el contexto interno del sub-bucle:
> * **$j$ (`fx_i`):** Índice de la repetición activa ($1, 2, \dots, \text{maxj}$).
> * **$\text{maxj}$ (`fx_n`):** Límite máximo de repeticiones configurado en `MaxLoop`.

### 7.5. Sinergias y Buenas Prácticas
* **Efectos Multi-Capa con Retardo (*Ghosting / Echo Trails*):** Encadenar `Loops/Main Loop` $\to$ `Loops/MaxLoop (5 iteraciones)` $\to$ `Time/Loop 1 (Mode: leadin, Delay: 40ms)` $\to$ `Time/Retime`. Cada una de las 5 capas se renderizará desfasada en el tiempo, creando estelas de movimiento o ecos luminosos transparentes.

### 7.6. Ejemplo Práctico de Producción
* **Estela de Ecos Multi-Capa con MaxLoop y Loop 1:**
  Generando 3 capas fantasma desfasadas tras el elemento principal:

  ```
  [Loops/MaxLoop: count=3] ──► j ──► (Contexto local j)
                                           │
  [Time/Loop 1: mode=leadin, delay_ms=45] ──► Data ──► Offset In (ms) ──► [Time/Retime: syl]
                                                                              └──► \t Out ──► Tags ──► [System/Output]
  ```

  Combinado con modulación de opacidad por capa `{\1a(120 + j * 40)}`:
  Cada iteración $j \in \{1, 2, 3\}$ se renderiza con un retardo temporal adicional de 45 ms respecto a la anterior, formando un rastro de desenfoque cinético (*motion blur trail*) sincronizado al canto (evaluando a `\1a&HA0&`, `\1a&HC8&` y `\1a&HF0&`).

---

## 8. Nodo `Time/Loop 2` (Temporizador para Sub-Bucles Anidados)

* **Categoría Canónica:** `Time` (UI: *Time / Loop 2*)
* **Propósito:** Idéntico en formulación cinemática a `Time/Loop 1`, pero diseñado específicamente para operar sobre **sub-bucles anidados de segundo nivel**, consumiendo la variable de iteración mayúscula $J$ frente al total $\text{maxJ}$.

![Time/Loop 2](img/loop_2.png)

### 8.1. Encabezado y Modos de Cabecera (*Header Mode Combos*)
1. **`[2.1] Mode` (`mode`):** Selector desplegable idéntico a `Loop 1` (`leadin`, `leadout`, `middle1`, `middle2`).

### 8.2. Puertos de Entrada y Propiedades del Cuerpo (*Inputs & Properties*)
1. **`Delay (ms)` (`delay_ms`):** Tiempo de retardo en milisegundos aplicado entre iteraciones $J$ (defecto: `30`).

### 8.3. Puertos de Salida (*Outputs*)
1. **`[1.1] Data`:** Valor temporal en milisegundos resultante para la sub-iteración anidada actual $J$.

### 8.4. Matriz Comparativa: Ámbitos de Iteración de Tiempo

| Nodo de Tiempo | Variable de Índice | Límite Total | Ámbito Operativo / Jerarquía |
| :--- | :---: | :---: | :--- |
| `Lead In` / `Lead Out` / `Middle 1` / `Middle 2` | $i$ (`syl.i`, `char.i`) | $n$ (`syl.n`, `char.n`) | **Bucle Maestro (`Main Loop`):** Iteración sobre sílabas, caracteres, palabras o líneas. |
| `Loop 1` | $j$ (`fx_i`) | $\text{maxj}$ (`fx_n`) | **Sub-bucle Primario (`MaxLoop` Nivel 1):** Repeticiones multicapa o fotogramas FBF. |
| `Loop 2` | $J$ | $\text{maxJ}$ | **Sub-bucle Anidado (`MaxLoop` Nivel 2):** Fractales, enjambres anidados o sub-muestreos complejos. |

### 8.5. Sinergias y Buenas Prácticas
* **Bucles Bi-Dimensionales (Matriz Espacio-Tiempo):** Cuando se construyen efectos con rejillas de partículas donde un `MaxLoop (X)` anida a otro `MaxLoop (Y)`, utilizar `Time/Loop 1` para modular el desfase por columna ($j$) y `Time/Loop 2` para modular el desfase por fila ($J$), sumando ambas salidas en un nodo `Basics/Math (add)` hacia `Time/Retime`.

### 8.6. Ejemplo Práctico de Producción
* **Matriz Temporal 2D con Bucles Anidados (Columnas y Filas):**
  Sincronizando una cuadrícula de partículas generada mediante dos nodos `MaxLoop` anidados:

  ```
  [Loops/MaxLoop X: cols=4] ──► j
       └──► [Loops/MaxLoop Y: rows=3] ──► J
                 │
  [Time/Loop 1: leadin, delay=30] ──► Data ──► In 1 ──► [Basics/Math: add]
  [Time/Loop 2: leadin, delay=60] ──► Data ──► In 2 ─────────┘   │
                                                                 └──► Offset In (ms) ──► [Time/Retime: syl]
  ```

  La suma de retardos produce un barrido diagonal ($30 \cdot (j-1) + 60 \cdot (J-1)$ ms), activando cada celda de la matriz secuencialmente en el espacio 2D.

---

## 9. Nodo `Time/Parse ASS Time` (Decodificador de Marcas ASS a Milisegundos)

* **Categoría Canónica:** `Time` (UI: *Time / Parse ASS Time*)
* **Propósito:** Parsea y convierte marcas horarias estándar de subtítulos ASS (`H:MM:SS.CS` o `H:MM:SS.MMM`) a un valor escalar numérico en milisegundos enteros.

![Time/Parse ASS Time](img/parse_ass_time.png)

### 9.1. Puertos de Entrada y Propiedades del Cuerpo (*Inputs & Properties*)
1. **`ASS Time` (`ass_time`):** Cadena de texto que contiene la marca de tiempo a parsear (ej. `"0:01:23.45"` o `"1:12:05.120"`). Si este puerto no está conectado y el campo inline se deja en blanco, el nodo extrae automáticamente la marca de tiempo de inicio del elemento activo en el contexto (`unit.start_str` $\to$ `line.start_str`) (defecto: `"0:00:00.00"`).

### 9.2. Puertos de Salida (*Outputs*)
1. **`[1.1] Time (ms)`:** Valor numérico entero correspondiente al tiempo total acumulado en milisegundos.

### 9.3. Formulación Matemática de Decodificación
Dada una marca de tiempo estructurada como $\text{Horas } H$, $\text{Minutos } M$, $\text{Segundos } S$ y $\text{Centisegundos } CS$:

$$T_{\text{ms}} = (3600 \cdot H + 60 \cdot M + S) \cdot 1000 + CS \cdot 10$$

#### Ejemplo de Conversión:
$$\text{"0:01:23.45"} \implies (0 + 60 + 23) \cdot 1000 + 45 \cdot 10 = 83000 + 450 = 83450\text{ ms}$$

### 9.4. Sinergias y Buenas Prácticas
* **Aritmética Temporal sobre Marcas Directas:** Permite decodificar marcas de cabecera de diálogos y operar con nodos `Basics/Math` o `Time/Offset` para calcular retardos exactos antes de re-inyectar el resultado en `Time/Format ASS Time` o `System/Output`.

### 9.5. Ejemplo Práctico de Producción
* **Decodificación y Desfase Aritmético de Tiempos Fijos:**
  Extrayendo una marca horaria literal para desplazarla algebraicamente 500 ms hacia adelante:

  ```
  [Time/Parse ASS Time: ass_time="0:01:15.50"] ──► Time (ms) ──► In 1 ──► [Basics/Math: add, in2=500]
                                                                                └──► In 1 ──► [Time/Format ASS Time]
                                                                                                    └──► ASS Time ──► "0:01:16.00"
  ```
  La marca decodificada (75500 ms) se incrementa a 76000 ms y se recompone en formato ASS estándar sin pérdidas de precisión.

---

## 10. Nodo `Time/Format ASS Time` (Codificador de Milisegundos a Marca ASS)

* **Categoría Canónica:** `Time` (UI: *Time / Format ASS Time*)
* **Propósito:** Convierte un valor numérico escalar de milisegundos a la cadena de marca horaria formal requerida por el estándar ASS (`H:MM:SS.CS`).

![Time/Format ASS Time](img/format_ass_time.png)

### 10.1. Puertos de Entrada y Propiedades del Cuerpo (*Inputs & Properties*)
1. **`Time (ms)` (`time`):** Valor numérico en milisegundos (entero, flotante o expresión matemática evaluable). Si el puerto no está conectado y el campo está vacío, toma el tiempo de inicio de la sílaba o línea (`unit.start_time` $\to$ `line.start_time`) (defecto: `"0"`).

### 10.2. Puertos de Salida (*Outputs*)
1. **`[1.1] ASS Time`:** Cadena de texto formateada con relleno de ceros según la sintaxis estándar de Aegisub / libass: `H:MM:SS.CS` (con centisegundos de dos dígitos).

### 10.3. Formulación Matemática de Codificación
A partir del tiempo total en milisegundos $T_{\text{ms}}$:

$$H = \left\lfloor \frac{T_{\text{ms}}}{3600000} \right\rfloor$$
$$M = \left\lfloor \frac{T_{\text{ms}} \bmod 3600000}{60000} \right\rfloor$$
$$S = \left\lfloor \frac{T_{\text{ms}} \bmod 60000}{1000} \right\rfloor$$
$$CS = \left\lfloor \frac{T_{\text{ms}} \bmod 1000}{10} \right\rfloor$$

$$\text{ASS Time} = H : \text{pad}_2(M) : \text{pad}_2(S) . \text{pad}_2(CS)$$

Donde $\text{pad}_2(x)$ antepone un cero a la izquierda si el valor es menor que $10$.

### 10.4. Sinergias y Buenas Prácticas
* **Generación Dinámica de Eventos:** Conectar la salida `ASS Time` a constructores de eventos en `Script Code` o cadenas personalizadas de diálogo cuando se generan archivos `.ass` multipista desacoplados del flujo estándar.

### 10.5. Ejemplo Práctico de Producción
* **Formateo de Intervalos Calculados para Metadatos de Efecto:**
  Transformando la salida numérica calculada de un retardo en marca horaria ASS:

  ```
  [Time/Offset: base=line.start_time, offset_ms=1200] ──► Time (ms) ──► Time (ms) ──► [Time/Format ASS Time]
                                                                                              └──► ASS Time
  ```
  Si `line.start_time` es 10000 ms, `Offset` emite 11200 ms y `Format ASS Time` produce exactamente `"0:00:11.20"`.

---

## 11. Nodo `Time/Time to Frame` (Conversión de Tiempo a Número de Fotograma)

* **Categoría Canónica:** `Time` (UI: *Time / Time to Frame*)
* **Propósito:** Calcula la cantidad o el número de fotograma del video ($f$) correspondiente a una marca de tiempo o intervalo en milisegundos, tomando como base la tasa de cuadros por segundo (*FPS*) del proyecto.

![Time/Time to Frame](img/time_to_frame.png)

### 11.1. Encabezado y Modos de Cabecera (*Header Mode Combos*)
1. **`[2.1] Mode` (`mode`):** Método de discretización matemática para redondear el número de fotograma:
   * `round` (Defecto): Redondeo al fotograma más próximo ($\lfloor x + 0.5 \rfloor$).
   * `floor`: Truncamiento hacia abajo ($\lfloor x \rfloor$), ideal para índices de fotogramas indexados en base 0 en la línea de tiempo.
   * `ceil`: Redondeo hacia arriba ($\lceil x \rceil$), ideal para calcular la cantidad total de fotogramas que abarca una duración no nula.
2. **`[2.2] Source` (`source`):** Origen del tiempo a convertir:
   * `custom` (Defecto): Toma el valor proporcionado en el puerto `Time (ms)` o la propiedad inline.
   * `start`: Extrae automáticamente el tiempo de inicio de la unidad o línea activa (`unit.start_time` $\to$ `line.start_time`).
   * `end`: Extrae automáticamente el tiempo de finalización (`unit.end_time` $\to$ `line.end_time`).
   * `dur`: Extrae automáticamente la duración neta (`unit.duration` $\to$ `line.duration`).

### 11.2. Puertos de Entrada y Propiedades del Cuerpo (*Inputs & Properties*)
1. **`Time (ms)` (`time`):** Tiempo en milisegundos a convertir. Acepta números directos, marcas ASS `H:MM:SS.CS` o variables de contexto.
2. **`Frame Dur (ms)` (`frame_dur`):** Duración de un fotograma en milisegundos. Si está desconectado o vacío, toma el valor contextual global del video cargado en Aegisub (por defecto $41.708\text{ ms}$, equivalente a $23.976\text{ fps}$).

### 11.3. Puertos de Salida (*Outputs*)
1. **`[1.1] Frames (f)`:** Número entero de fotogramas resultante.

### 11.4. Formulación Matemática de Discretización por Cuadro
Dada la duración por cuadro $fd = \frac{1000}{\text{FPS}}$ y el tiempo resuelto $T$:

$$f_{\text{ceil}} = \left\lceil \frac{T}{fd} \right\rceil, \quad f_{\text{floor}} = \left\lfloor \frac{T}{fd} \right\rfloor, \quad f_{\text{round}} = \left\lfloor \frac{T}{fd} + 0.5 \right\rfloor$$

#### Tabla de Equivalencias de Duración por Cuadro según FPS:
| Tasa de Cuadros (FPS) | Duración por Cuadro ($fd$) | Cuadros para $1000\text{ ms}$ (Ceil) |
| :---: | :---: | :---: |
| **$23.976\text{ fps}$** | $\approx 41.7083\text{ ms}$ | $24\text{ frames}$ |
| **$24.000\text{ fps}$** | $\approx 41.6667\text{ ms}$ | $24\text{ frames}$ |
| **$29.970\text{ fps}$** | $\approx 33.3667\text{ ms}$ | $30\text{ frames}$ |
| **$30.000\text{ fps}$** | $\approx 33.3333\text{ ms}$ | $30\text{ frames}$ |
| **$60.000\text{ fps}$** | $\approx 16.6667\text{ ms}$ | $60\text{ frames}$ |

### 11.5. Sinergias y Buenas Prácticas
* **Alimentación de Bucles FBF:** Conectar `Time to Frame` (en modo `Source: dur` y `Mode: ceil`) al puerto `Total` o propiedad de repeticiones de `Loops/MaxLoop (fbf)` para garantizar que el bucle itere exactamente la cantidad de fotogramas reales que dura la sílaba en el video.

### 11.6. Ejemplo Práctico de Producción
* **Dimensionamiento Exacto de Iteraciones FBF:**
  Calculando los cuadros requeridos para cubrir la duración de la sílaba activa a 23.976 fps:

  ```
  [Time/Time to Frame: source=dur, mode=ceil] ──► Frames (f) ──► Count / Reps ──► [Loops/MaxLoop: fbf]
  ```
  Si la sílaba dura 450 ms y $fd \approx 41.708$ ms:
  $$\left\lceil \frac{450}{41.708} \right\rceil = \lceil 10.789 \rceil = 11\text{ frames}$$
  `MaxLoop` itera exactamente 11 veces, cubriendo toda la extensión temporal sin dejar huecos o fotogramas vacíos.

---

## 12. Nodo `Time/Frame to Time` (Conversión de Fotograma a Tiempo y Formatos)

* **Categoría Canónica:** `Time` (UI: *Time / Frame to Time*)
* **Propósito:** Multiplica un número de fotograma o contador de iteración ($f$, $j$, $J$, $i$) por la duración del fotograma para obtener su equivalencia temporal en milisegundos, marcas ASS o segundos.

![Time/Frame to Time](img/frame_to_time.png)

### 12.1. Encabezado y Modos de Cabecera (*Header Mode Combos*)
1. **`[2.1] Format` (`format`):** Formato de la salida primaria `[1.1] Time`:
   * `ms` (Defecto): Milisegundos numéricos redondeados a dos decimales (ej. `2000.0`).
   * `hms`: Cadena formateada en sintaxis horaria ASS (ej. `"0:00:02.00"`).
   * `sec`: Segundos en punto flotante con tres decimales (ej. `2.000`).
2. **`[2.2] Source` (`source`):** Origen de la variable o número de fotograma a evaluar:
   * `custom` (Defecto): Toma el valor ingresado en el puerto `Frames (f)` o el campo inline `frames`.
   * `iterator`: Lee una variable de iteración personalizada especificada en `iter_name` (ej. `k`, `step_i`, o expresiones como `k * 2`).
   * `j`: Extrae automáticamente el contador de sub-bucle activo `j` (`fx_i`).
   * `J`: Extrae automáticamente el contador de sub-bucle anidado `J`.
   * `i`: Extrae automáticamente el índice secuencial de la unidad `unit.i`.

### 12.2. Puertos de Entrada y Propiedades del Cuerpo (*Inputs & Properties*)
1. **`Frames (f)` (`frames`):** Cantidad o índice de fotograma (utilizado cuando `Source` es `custom`) (defecto: `1`).
2. **`Frame Dur (ms)` (`frame_dur`):** Duración del fotograma en milisegundos ($fd$). Si se omite, se infiere del entorno de video ($41.708\text{ ms}$).

### 12.3. Puertos de Salida (*Outputs*)
1. **`[1.1] Time`:** Tiempo convertido según el formato configurado en `Format` (`ms`, `hms` o `sec`).
2. **`[1.2] ASS Time`:** Emite **siempre** la marca temporal formateada en estándar ASS (`0:00:00.00`), independientemente del formato seleccionado en la cabecera.

### 12.4. Formulación Matemática de Proyección de Cuadros
Dado el número de fotograma resuelto $f$ y la duración de cuadro $fd$:

$$T_{\text{ms}} = f \cdot fd$$

* Si `Format` es `ms`: $T_{\text{out}} = \text{round}(T_{\text{ms}}, 2)$
* Si `Format` es `sec`: $T_{\text{out}} = \text{round}\left(\frac{T_{\text{ms}}}{1000}, 3\right)$
* Si `Format` es `hms`: $T_{\text{out}} = \text{format\_time}(T_{\text{ms}})$

### 12.5. Sinergias y Buenas Prácticas
* **Sincronización Fotograma a Fotograma (FBF):** Dentro de un bucle `Loops/MaxLoop (fbf)`, utilizar `Frame to Time` con `Source: j` para calcular en cada cuadro exacto el tiempo relativo transcurrido. Dicha salida puede alimentar directamente la entrada `Base (ms)` de `Time/Offset` o el factor de interpolación $t$ en curvas Bézier y deformaciones vectoriales.

### 12.6. Ejemplo Práctico de Producción
* **Proyección Temporal Continua en Bucle FBF:**
  Calculando el tiempo transcurrido en cada fotograma $j$ dentro de una animación FBF:

  ```
  [Loops/MaxLoop: fbf] ──► Contexto j
                                │
  [Time/Frame to Time: source=j, format=ms] ──► Time ──► Base (ms) ──► [Time/Offset: offset_ms=syl.start_time]
                                                                             └──► Time (ms) ──► Start Time ──► [System/Output]
  ```
  Cada línea FBF generada adquiere su marca de inicio absoluta de video correspondiente al fotograma actual ($T = T_{\text{syl\_start}} + j \cdot fd$), garantizando perfecta sincronía cuadro a cuadro en Aegisub.

---

## 13. Nodo `Time/Ipol` (Segmentador Temporal No Lineal y Easing)

* **Categoría Canónica:** `Time` (UI: *Time / Ipol*)
* **Propósito:** Divide una duración total ($D_{\text{ms}}$) en una secuencia ordenada de sub-intervalos temporales normalizados $[t_0, t_1], [t_1, t_2], \dots$, aplicando curvas de aceleración exponencial (`accel`) sobre una lista arbitraria de puntos de control (*keyframes* o valores intermedios).

![Time/Ipol](img/ipol.png)

### 13.1. Puertos de Entrada y Propiedades del Cuerpo (*Inputs & Properties*)
1. **`Duration (ms)` (`dur_ms`):** Duración total del intervalo a subdividir en milisegundos. Si está vacío o desconectado, adopta automáticamente la duración de la unidad activa (`unit.duration` $\to 1000\text{ ms}$) (defecto: `"syl.duration"`).
2. **`Points / Values` (`points`):** Lista de valores escalares separados por comas que definen la cantidad de etapas o puntos de parada (ej. `"0, 100"` para $1$ segmento; `"0, 50, 100"` para $2$ segmentos; `"0, 20, 80, 100"` para $3$ segmentos) (defecto: `"0, 100"`).
3. **`Acceleration` (`accel`):** Exponente de curvatura no lineal de la aceleración. Acepta valores decimales mayores que cero (defecto: `1.0`):
   * $\text{accel} = 1.0$: Interpolación estrictamente lineal (distribución equiespaciada).
   * $\text{accel} > 1.0$: Curva *Ease-In* (arranque lento con aceleración progresiva hacia el final).
   * $\text{accel} < 1.0$: Curva *Ease-Out* (arranque rápido con desaceleración progresiva).

### 13.2. Puertos de Salida (*Outputs*)
1. **`[1.1] Data`:** Cadena de texto formateada con los sub-intervalos calculados entre corchetes, separados por comas (ej. `"[0.0, 500.0], [500.0, 1000.0]"`).

### 13.3. Formulación Matemática de la Segmentación Temporal
Dada una lista de $M$ puntos de control $\{p_0, p_1, \dots, p_M\}$, la cantidad de segmentos temporales resultantes es $K = M - 1$. 

Para cada índice de corte $k \in \{1, \dots, K\}$, se calcula la fracción normalizada $u_k$:

$$u_k = \frac{k}{K}, \quad u_k \in (0.0, 1.0]$$

El instante temporal acumulado $t_k$ correspondiente al final del segmento $k$ se evalúa aplicando la potencia de aceleración:

$$t_k = D_{\text{ms}} \cdot (u_k)^{\text{accel}}$$

Los sub-intervalos generados corresponden a:

$$I_k = [t_{k-1}, t_k] \quad \text{con } t_0 = 0.0\text{ ms}$$

```
t=0 ms                                                  t=D ms
├─────────────────────────┼───────────────────────────────────┤
  Intervalo 1: [t_0, t_1]       Intervalo 2: [t_1, t_2]
```

#### Ejemplo de Segmentación ($D = 1000\text{ ms}$, Puntos $= \text{"0, 50, 100"}$, $K=2$ segmentos):
* **Lineal ($\text{accel} = 1.0$):**
  * $k=1 \implies u_1 = 0.5 \implies t_1 = 1000 \cdot (0.5)^1 = 500.0\text{ ms} \implies [0.0, 500.0]$
  * $k=2 \implies u_2 = 1.0 \implies t_2 = 1000 \cdot (1.0)^1 = 1000.0\text{ ms} \implies [500.0, 1000.0]$
  * **Salida `Data`:** `"[0.0, 500.0], [500.0, 1000.0]"`
* **Ease-In Cuadrático ($\text{accel} = 2.0$):**
  * $k=1 \implies u_1 = 0.5 \implies t_1 = 1000 \cdot (0.5)^2 = 250.0\text{ ms} \implies [0.0, 250.0]$
  * $k=2 \implies u_2 = 1.0 \implies t_2 = 1000 \cdot (1.0)^2 = 1000.0\text{ ms} \implies [250.0, 1000.0]$
  * **Salida `Data`:** `"[0.0, 250.0], [250.0, 1000.0]"`

### 13.4. Sinergias y Buenas Prácticas
* **Alimentación de Animaciones Multi-Fase:** Conectar la salida `Data` de `Ipol` a nodos de animación o constructores de transformaciones complejas `\t` en `Script Code` para subdividir el tiempo de canto de una sílaba en dos o más etapas cinemáticas coordinadas (ej. golpe inicial rápido de escala seguido de retorno suave).

### 13.5. Ejemplo Práctico de Producción
* **Animación Bifásica de Impacto y Asentamiento:**
  Subdividiendo una sílaba de 600 ms en dos fases con aceleración no lineal (`points="0, 30, 100"`, `accel=1.5`):

  ```
  [Time/Ipol: dur_ms=600, points="0, 30, 100", accel=1.5] ──► Data
  ```
  El nodo devuelve los sub-intervalos: `[0.0, 212.1], [212.1, 600.0]`.
  En el bloque ASS:
  ```
  {\t(0, 212, \fscx140\fscy140)\t(212, 600, 0.8, \fscx100\fscy100)}
  ```
  El glifo salta bruscamente al 140% durante los primeros 212 ms (fase de impacto) y regresa suavemente al 100% durante los 388 ms restantes con curva decelerada.

---

## 14. Nodo `Time/Duration` (Cálculo de Duración Neta)

* **Categoría Canónica:** `Time` (UI: *Time / Duration*)
* **Propósito:** Calcula la duración escalar neta en milisegundos entre dos marcas temporales ($T_{\text{start}}$ y $T_{\text{end}}$), o devuelve la duración activa del elemento contextual si las entradas no están conectadas.

![Time/Duration](img/duration.png)

### 14.1. Puertos de Entrada y Propiedades del Cuerpo (*Inputs & Properties*)
1. **`Start Time (ms)` (`start_time`):** Marca de tiempo inicial en milisegundos o variable de contexto (ej. `line.start_time`, `syl.start_time`) (defecto: `"line.start_time"`).
2. **`End Time (ms)` (`end_time`):** Marca de tiempo final en milisegundos o variable de contexto (ej. `line.end_time`, `syl.end_time`) (defecto: `"line.end_time"`).

### 14.2. Puertos de Salida (*Outputs*)
1. **`[1.1] Duration (ms)`:** Valor escalar entero correspondiente a la diferencia no negativa entre ambas marcas temporales.

### 14.3. Formulación Matemática de Duración Neta
Dados los instantes $T_{\text{start}}$ y $T_{\text{end}}$ evaluados dinámicamente en el contexto:

$$D = \max\left(0, \text{round}(T_{\text{end}} - T_{\text{start}})\right)$$

#### Comportamiento Contextual Automático:
Si ambas entradas y propiedades se encuentran vacías o no especificadas, el nodo inspecciona la jerarquía contextual para extraer directamente la duración intrínseca del elemento activo:

$$D = \text{unit.duration} \implies \text{syl.duration} \implies \text{line.duration} \implies 0\text{ ms}$$

### 14.4. Sinergias y Buenas Prácticas
* **Medición de Intervalos Personalizados:** Conectar las salidas `Start Time` y `End Time` de un nodo `Time/Retime` hacia `Time/Duration` para calcular la duración exacta de una fase fonética con offsets incluidos antes de mapearla en curvas Bézier o escalas proporcionales.

### 14.5. Ejemplo Práctico de Producción
* **Modulación de Velocidad de Rotación por Duración Fonética:**
  Conectando `Start Time` y `End Time` de una sílaba hacia `Time/Duration`:

  ```
  [Time/Retime: syl] ──┬──► Start Time ──► Start Time (ms) ──► [Time/Duration]
                       └──► End Time   ──► End Time (ms)   ───────┘   │
                                                                      └──► Duration (ms) ──► In 1 ──► [Basics/Math: div, in2=100]
                                                                                                             └──► Rot Speed
  ```

  Si una sílaba rápida dura 200 ms, la velocidad resultante produce giros ágiles de `\frz`; si la vocal es sostenida (1200 ms), el giro se suaviza automáticamente para cubrir todo el intervalo sin aceleraciones bruscas.

---

## 15. Nodo `Time/Offset` (Desfase Temporal Aditivo y Sustractivo)

* **Categoría Canónica:** `Time` (UI: *Time / Offset*)
* **Propósito:** Aplica un desplazamiento o retardo temporal en milisegundos sobre una marca de tiempo base, permitiendo adelantos (valores negativos) o retrasos (valores positivos).

![Time/Offset](img/offset.png)

### 15.1. Puertos de Entrada y Propiedades del Cuerpo (*Inputs & Properties*)
1. **`Base (ms)` (`time_in` / `base`):** Marca de tiempo de origen en milisegundos. Si no está conectada, el nodo extrae automáticamente el tiempo de inicio del elemento contextual activo (`unit.start_time` $\to$ `line.start_time` $\to 0$).
2. **`Offset (ms)` (`offset_ms` / `offset`):** Cantidad de milisegundos a sumar o restar a la base. Acepta números positivos, negativos o expresiones evaluables (defecto: `"100"`).

### 15.2. Puertos de Salida (*Outputs*)
1. **`[1.1] Time (ms)`:** Marca de tiempo resultante tras aplicar el desplazamiento.

### 15.3. Formulación Matemática de Desfase
$$T_{\text{out}} = \text{round}(T_{\text{base}} + \Delta_{\text{offset}})$$

#### Ejemplos:
* **Retardo Positivo:** $T_{\text{base}} = 1000\text{ ms}, \Delta_{\text{offset}} = 250\text{ ms} \implies T_{\text{out}} = 1250\text{ ms}$
* **Anticipación Negativa:** $T_{\text{base}} = 1000\text{ ms}, \Delta_{\text{offset}} = -150\text{ ms} \implies T_{\text{out}} = 850\text{ ms}$

### 15.4. Sinergias y Buenas Prácticas
* **Desplazamiento Dinámico de Ventanas:** Conectar a la salida `End Time` de `Time/Retime` con un `Offset: 200` para extender el tiempo de permanencia de una línea antes de enviarla a `System/Output`.
* **Cálculo de Puntos Clave de Animación:** Generar marcas de tiempo intermedias para sincronizar el disparo de destellos de `Functions/Glitter` o partículas justo antes o después del inicio de la palabra cantada.

### 15.5. Ejemplo Práctico de Producción
* **Ampliación de Tiempo de Permanencia de Silueta:**
  Extender la visibilidad de una sombra o borde exterior tras el final de la línea:

  ```
  [Time/Retime: line] ──► End Time ──► Base (ms) ──► [Time/Offset: offset_ms=250]
                                                             └──► Time (ms) ──► End Time ──► [System/Output]
  ```

  En el bloque ASS:
  ```
  {\pos(line.center, line.middle)\bord5\3c&H000000&\t(line.duration, line.duration + 250, \alpha&HFF&)}
  ```
  El borde se mantiene 250 ms después de que la capa tipográfica principal se apaga, desvaneciéndose limpiamente hacia negro.

