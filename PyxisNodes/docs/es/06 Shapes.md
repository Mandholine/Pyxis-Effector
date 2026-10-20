# Shapes

La categoría **Shape** contiene los nodos de generación, ingestión, manipulación y segmentación geométrica de trazados vectoriales en formato ASSdraw (`m`, `l`, `b`, `s`, `p`, `c`) y máscaras de recorte (`\clip`, `\iclip`).

### Organización Temática del Volumen:
* **Sección 6.A — Generación, Trazado e Ingesta Vectorial:** `Shape/Library` (§1), `Shape/Walker` (§7), `Shape/Stroke` (§8), `Shape/IMG to Shape` (§12).
* **Sección 6.B — Mallas, Matrices y Patrones Concéntricos:** `Shape/Slicer` (§2), `Shape/Concentric Borders` (§6), `Shape/Array` (§11), `Shape/Multi` (§13).
* **Sección 6.C — Álgebra Booleana y Transformaciones No Lineales:** `Shape/Manipulator` (§3), `Shape/Filter` (§4), `Shape/Transform` (§5), `Shape/Union & Divide` (§9), `Shape/Clipper` (§10).

---

## 1. Nodo `Shape/Library` (Primitivas Geométricas)

* **Categoría Canónica:** `Shape` (UI: *Shape / Library*)
* **Propósito:** Emite primitivas geométricas paramétricas precalculadas normalizadas en una caja delimitadora base $[0, 100]$ y centradas en el origen cartesiano local `(0, 0)`.

![Shape/Library](img/library.png)

### 1.1. Tarjeta de Previsualización y Atajos Interactivos
* **Renderizado Vectorial en Vivo:** El nodo incluye en su cuerpo una tarjeta interactiva (*Preview Card*) que dibuja el contorno vectorial seleccionado en tiempo real.
* **Atajos de Apertura del Catálogo Modal:**
  * Clic directo sobre la tarjeta de previsualización gráfica (*Preview Card*).
  * Doble clic sobre cualquier área vacía del cuerpo del nodo.
  * Clic sobre la píldora de forma en la cabecera del nodo.
  Cualquiera de estas acciones despliega el **Catálogo Modal de Primitivas Vectoriales**, permitiendo explorar las 80 formas por categoría o mediante búsqueda por texto.

### 1.2. Catálogo Canónico de 80 Formas (`shape`)
El catálogo se organiza en 10 familias canónicas, con identificadores internos en minúsculas estándar:
* **`shapes` (9):** `circle`, `triangle`, `rectangle`, `circangle`, `pixel`, `pentagon`, `hexagon`, `octagon`, `diamond`.
* **`hearts` (3):** `heart`, `heart2t`, `heartb`.
* **`shines` (4):** `shine1t`, `shine2t`, `shine3t`, `shine4t`.
* **`specials` (5):** `clover`, `feather`, `feather2`, `gear`, `bubble`.
* **`music` (4):** `note1t`, `note2t`, `note3t`, `note4t`.
* **`stars` (11):** `star`, `star1t`, `star2t`, `star3t`, `star4t`, `star5t`, `star6t`, `star7t`, `star8t`, `star9t`, `star10t`.
* **`sakura` (8):** `sakura`, `sakura1t`, `sakura2t`, `sakura3t`, `sakura4t`, `sakura5t`, `sakura6t`, `sakura7t`.
* **`snow` (3):** `snowflake1t`, `snowflake2t`, `snowflake3t`.
* **`flowers` (29):** `flower1t` a `flower29t` (margaritas, crisantemos, girasoles, mandalas y flores multicapa).
* **`geometry` (4):** `crystal17`, `geometric10`, `diagonal13r`, `diagonal13l`.

### 1.3. Puertos de Salida (*Outputs*)
1. **`[1.1] Shape`:** Emite el código de dibujo ASSdraw centrado en `(0, 0)` listo para alimentar `System/Output (Return)` o nodos de procesamiento vectorial downstream (`Stroke`, `Manipulator`, `Slicer`).

### 1.4. Ejemplo Práctico de Producción
* **Emisión de Icono Vectorial con Rotación y Escala:**
  Conectando `Shape` al puerto `Return` de `System/Output` y configurando `category: stars`, `shape: star`:
  
  ```
  [Shape/Library: star] ──► Shape ──► Return ──► [System/Output]
  ```
  
  En un nodo de etiquetas conectado a `System/Output (Tags)`:
  ```
  {\p1\pos(syl.center, syl.middle)\frz(i * 45)\fscx75\fscy75\1c&H00FFFF&\bord1\3c&H0055AA&}
  ```
  El trazado centrado en `(0, 0)` se dibuja exactamente sobre el centroide de la sílaba con escala del 75% y rotación angular dependiente del índice $i$.

---

## 2. Nodo `Shape/Slicer` (Corte y Segmentación Morfológica)

* **Categoría Canónica:** `Shape` (UI: *Shape / Slicer*)
* **Propósito:** Divide una forma vectorial o texto en piezas, fragmentos o celdas geométricas independientes mediante operaciones booleanas aceleradas por *Clipper2*. Los campos de entrada del nodo se reconfiguran dinámicamente según el modo de corte seleccionado.

![Shape/Slicer](img/slicer.png)

### 2.1. Encabezado, Modos de Cabecera y Galería Modal de Mallas (`pyxis-mesh-picker-dialog`)
1. **`[1.1] Slicer`:** Título identificador del nodo.
2. **`[1.2] Modo de Corte` (`[Grid 田]` - Atajo Modal de Mallas):**
   * **Atajo de Apertura:** Un clic directo sobre este botón/píldora en la cabecera abre instantáneamente la **Galería Visual de Patrones de Corte y Mallas** (`pyxis-mesh-picker-dialog`).
   * **Tarjetas con Renderizado SVG Interactivo:** Cada uno de los 23 motores de segmentación se presenta en una tarjeta visual con un icono vectorial SVG dinámico de alta definición que muestra la topología real de corte (panal de abeja para `hex`, celosía triangular para `tri`, cubos 3D para `rhombille`, ondas bézier para `bez`, trazos PCB para `circuit`, teselaciones orgánicas para `voronoi`, etc.).
   * **Categorización Estructurada por Familias de Malla:**
     * **`Standard Grid`:** Cuadrícula rectangular uniforme 1D/2D (`Grid 1D/2D`).
     * **`Polygonal & Organic`:** Mallas poligonales y biológicas (`hex`, `tri`, `dia`, `voronoi`, `delaunay`, `kagome`, `rhombille`, `octagon`).
     * **`Technology & Networks`:** Redes radiales, circuitos y piezas (`ring`, `jigsaw`, `circuit`, `ray`, `web`).
     * **`Architecture & Walls`:** Aparejos de albañilería, bloques y composiciones (`brick`, `mondrian`, `ashlar`, `quad`, `pattern`).
     * **`Waves & Art`:** Diseños ondulados y curvas modulares (`herringbone`, `truchet`, `scallop`, `bez`).
   * **Buscador Reactivo:** Barra de búsqueda en tiempo real para filtrar rápidamente por nombre o descripción técnica.
   * **Reconfiguración Reactiva 1-Clic:** Al seleccionar cualquier patrón, el nodo actualiza inmediatamente su algoritmo, conmuta dinámicamente sus puertos de entrada y propiedades en el cuerpo (ej. de `Cols/Rows` a `Cell Size/Seed/Jitter`) y redimensiona su caja en el lienzo.
3. **`[1.3] Modo de Salida` (`[Loops]`):** Alterna el comportamiento de evaluación entre modo iterador por piezas dentro de un bucle (`Loops`) o generación simultánea de lista/array (`Single / Array`).

---

### 2.2. Parámetros Universales y Controles Globales
Estos parámetros y botones de configuración están presentes o aplican de manera transversal a todos los modos de corte:

1. **`[2.1] Shape`:** Forma vectorial ASSdraw o glifo de texto a cortar. Si no se conecta ningún enlace ni se especifica texto, toma automáticamente el trazado del contexto activo (sílaba, palabra o línea).
2. **`[2.2] Text Scale`:** Factor de escala previo aplicado a la forma antes de proceder a la subdivisión y corte.
3. **`[2.3] Pre-Offset`:** Desplazamiento perimetral (*dilatación / erosión*) aplicado a los contornos de la forma original antes de ejecutar el corte booleano.
4. **`[2.4] Anchor` (Punto de Anclaje, Posicionamiento y Origen Inyectado):** Botón selector que define el sistema de coordenadas local de cada pieza y cómo se inyectan las etiquetas de posición `\pos(x,y)` y origen de rotación/escala `\org(x,y)` en el contexto:
   * **`Piece` (`Piezas`):** 
     * **Posición (`\pos`):** Se reubica en el centroide absoluto de la pieza en pantalla (`pos_x = parent_x + cx`, `pos_y = parent_y + cy`).
     * **Origen Inyectado (`\org`):** Se inyecta `\org(pos_x, pos_y)` en el centroide de la propia pieza.
     * **Trazado Vectorial:** El dibujo se recentra en su origen local `(0, 0)` mediante offset perimetral `(-cx, -cy)`. Permite que cada fragmento rote y escale sobre su propio centro de masa de forma individual.
   * **`Relativo`:** 
     * **Posición (`\pos`):** Mantiene la posición del elemento padre (`parent_x`, `parent_y`).
     * **Origen Inyectado (`\org`):** Se inyecta `\org(parent_x, parent_y)` en el centroide del padre.
     * **Trazado Vectorial:** Conserva las coordenadas relativas originales respecto al origen del padre sin recentrar la pieza individual.
   * **`Parent Org` (`Org Padre` — `parent_org`):** 
     * **Posición (`\pos`):** Se posiciona en el centroide de la pieza (`pos_x = parent_x + cx`, `pos_y = parent_y + cy`).
     * **Origen Inyectado (`\org`):** Se inyecta `\org(parent_x, parent_y)` forzado en el origen del elemento padre.
     * **Trazado Vectorial:** El dibujo se recentra en su origen local `(0, 0)`. Permite que todas las piezas individuales roten orbitando alrededor del centro general de la palabra/sílaba original.
   * **`Pos`:** 
     * **Posición (`\pos`):** Se posiciona en el centroide de la pieza (`pos_x = parent_x + cx`, `pos_y = parent_y + cy`).
     * **Origen Inyectado (`\org`):** No inyecta etiqueta `\org` (`has_org = False`), permitiendo que el motor de renderizado use el punto de alineación estándar `\an`.
     * **Trazado Vectorial:** El dibujo se recentra en su origen local `(0, 0)`.
   * **`Absoluto`:** 
     * **Posición (`\pos`):** Mantiene las coordenadas del padre (`parent_x`, `parent_y`).
     * **Origen Inyectado (`\org`):** No inyecta etiqueta `\org` (`has_org = False`).
     * **Trazado Vectorial:** Las coordenadas absolutas en pantalla se hornean directamente dentro del código ASSdraw de la pieza mediante desplazamiento `(+parent_x, +parent_y)`.
5. **`[2.5] Out:` (Modo de Salida Vectorial):** Botón selector del formato devuelto en el puerto `Piece`:
   * **`Shape`:** Emite el código ASSdraw directo del fragmento cortado (`m ... l ... b ...`).
   * **`\clip`:** Emite la etiqueta de recorte ASS rectangular o poligonal `\clip(m ...)`.
   * **`\iclip`:** Emite la etiqueta de recorte invertido ASS `\iclip(m ...)`.
6. **`[2.6] Bleed`:** Sangrado o solapamiento perimetral entre fragmentos adyacentes. Aplica una dilatación por pieza para erradicar cualquier costura o renderizado imperfecto de líneas divisorias entre piezas contiguas.
7. **`[2.7] Order:` (Ordenamiento Espacial de Fragmentos):** Botón selector del orden de iteración basado en el teclado numérico de 9 posiciones:
   * **`79 (TL->BR)`:** De Arriba-Izquierda (*Top-Left*) a Abajo-Derecha (*Bottom-Right*).
   * **`97 (TR->BL)`:** De Arriba-Derecha (*Top-Right*) a Abajo-Izquierda (*Bottom-Left*).
   * **`13 (BL->TR)`:** De Abajo-Izquierda (*Bottom-Left*) a Arriba-Derecha (*Top-Right*).
   * **`31 (BR->TL)`:** De Abajo-Derecha (*Bottom-Right*) a Arriba-Izquierda (*Top-Left*).
   * **`71 (TL->BL)`:** Vertical descendente columna por columna de izquierda a derecha.
   * **`17 (BL->TL)`:** Vertical ascendente columna por columna de izquierda a derecha.
   * **`39 (BR->TR)`:** Vertical ascendente columna por columna de derecha a izquierda.
   * **`5 (Centro)`:** Desde el centroide de la forma original hacia los extremos exteriores.
8. **`[2.8] s_i, s_n`:** Variables de iteración expuestas en el pie del nodo (`s_i` = índice actual de fragmento $[1 \dots N]$, `s_n` = total de piezas generadas en el corte).

---

### 2.3. Puertos de Salida (*Outputs*)
1. **`[3.1] Piece`:** Código vectorial ASSdraw o etiqueta `\clip`/`\iclip` de la pieza activa correspondiente a la iteración.
2. **`[3.2] X`:** Coordenada cartesiana horizontal $X$ del centroide de la pieza.
3. **`[3.3] Y`:** Coordenada cartesiana vertical $Y$ del centroide de la pieza.
4. **`[3.4] Col`:** Índice de columna espacial asignado a la pieza en la malla.
5. **`[3.5] Row`:** Índice de fila espacial asignado a la pieza en la malla.

---

### 2.4. Entradas y Campos Específicos por Modo de Corte

Cada modo de segmentación reconfigura dinámicamente los campos editables y puertos de entrada en el cuerpo del nodo:

#### 1. Modo `Grid 1D/2D` (`Rejilla 1D/2D`)
* **`Cols`:** Cantidad de divisiones o columnas en el eje horizontal.
* **`Rows`:** Cantidad de divisiones o filas en el eje vertical.
* **`Angle`:** Inclinación angular en grados de la rejilla de corte.
* **`Bleed`:** Sangrado de solapamiento entre celdas.
* **`Accel X`:** Exponente de no-linealidad en la distribución horizontal (genera celdas progresivamente más densas o espaciadas).
* **`Accel Y`:** Exponente de no-linealidad en la distribución vertical.
* **`Text Scale` / `Pre-Offset` / `Anchor` / `Out:` / `Order:`:** Parámetros universales.

#### 2. Modo `Hex` (`Hexagonal`)
* **`Radius`:** Radio circumscrito de los hexágonos regulares que componen la malla panal.
* **`Text Scale` / `Pre-Offset` / `Anchor` / `Out:` / `Bleed` / `Order:`:** Parámetros universales.

#### 3. Modo `Tri` (`Triangular`)
* **`Radius`:** Longitud del semilado de los triángulos equiláteros de la teselación.
* **`Text Scale` / `Pre-Offset` / `Anchor` / `Out:` / `Bleed` / `Order:`:** Parámetros universales.

#### 4. Modo `Dia` (`Diamante / Rombos`)
* **`Radius`:** Semidiagonal mayor y menor de la malla de rombos regulares.
* **`Text Scale` / `Pre-Offset` / `Anchor` / `Out:` / `Bleed` / `Order:`:** Parámetros universales.

#### 5. Modo `Rings` (`Anillos Concéntricos`)
* **`Ring Width`:** Grosor o distancia radial en píxeles de cada anillo concéntrico generado desde el centro.
* **`Text Scale` / `Pre-Offset` / `Anchor` / `Out:` / `Bleed` / `Order:`:** Parámetros universales.

#### 6. Modo `Ray` (`Rayos Radiales`)
* **`Step Angle` / `Rays`:** Paso angular en grados o cantidad de sectores radiales generados desde el centro hacia el perímetro.
* **`Text Scale` / `Pre-Offset` / `Anchor` / `Out:` / `Bleed` / `Order:`:** Parámetros universales.

#### 7. Modo `Voronoi` (`Cristales / Voronoi`)
* **`Cell Size`:** Tamaño medio de las celdas orgánicas generadas por los sitios de dispersión estocástica.
* **`Text Scale` / `Pre-Offset` / `Anchor` / `Out:` / `Bleed` / `Order:`:** Parámetros universales.

#### 8. Modo `Delaunay` (`Low-Poly`)
* **`Cell Size`:** Densidad y distancia entre vértices para la triangulación morfológica no regular (*Low-Poly*).
* **`Text Scale` / `Pre-Offset` / `Anchor` / `Out:` / `Bleed` / `Order:`:** Parámetros universales.

#### 9. Modo `Brick` (`Ladrillos`)
* **`Size X` (Width):** Anchura en píxeles de cada bloque de ladrillo.
* **`Size Y` (Height):** Altura en píxeles de cada hilera de ladrillo.
* **`Text Scale` / `Pre-Offset` / `Anchor` / `Out:` / `Bleed` / `Order:`:** Parámetros universales.

#### 10. Modo `Ashlar` (`Mampostería Irregular`)
* **`Min Width` / `Max Width`:** Rango de anchura aleatoria para los bloques de piedra.
* **`Row Height`:** Altura fija de las hileras de mampostería.
* **`Text Scale` / `Pre-Offset` / `Anchor` / `Out:` / `Bleed` / `Order:`:** Parámetros universales.

#### 11. Modo `Jigsaw` (`Rompecabezas / Puzzle`)
* **`Piece Size`:** Dimensión base de las piezas de puzzle cuadradas con pestañas curvas y cavidades de encastre Bézier.
* **`Text Scale` / `Pre-Offset` / `Anchor` / `Out:` / `Bleed` / `Order:`:** Parámetros universales.

#### 12. Modo `Bez` (`Ondas Bézier`)
* **`Wave Size`:** Tamaño de las celdas delimitadas por bordes sinusoidales Bézier con perturbación orgánica aleatoria.
* **`Text Scale` / `Pre-Offset` / `Anchor` / `Out:` / `Bleed` / `Order:`:** Parámetros universales.

#### 13. Modo `Circuit` (`Circuito Electrónico`)
* **`Grid Size`:** Tamaño de la cuadrícula de la placa de circuitos integrados.
* **`Trace Width`:** Grosor de las pistas y buses conductores.
* **`Via Prob`:** Probabilidad de inserción de terminales circulares (*pads / vías*).
* **`Text Scale` / `Pre-Offset` / `Anchor` / `Out:` / `Bleed` / `Order:`:** Parámetros universales.

#### 14. Modo `Truchet` (`Tuberías / Laberinto`)
* **`Tile Size`:** Dimensión cuadrangular de los azulejos de arcos de círculo tangentes (*Truchet Tiles*).
* **`Text Scale` / `Pre-Offset` / `Anchor` / `Out:` / `Bleed` / `Order:`:** Parámetros universales.

#### 15. Modo `Pattern` (`Patrón Personalizado`)
* **`Pattern Shape`:** Vector o forma ASSdraw utilizado como máscara repetitiva de corte.
* **`Size X` / `Size Y`:** Espaciado horizontal y vertical de repetición del patrón.
* **`Text Scale` / `Pre-Offset` / `Anchor` / `Out:` / `Bleed` / `Order:`:** Parámetros universales.

#### 16. Modo `Mondrian` (Subdivisión Neoplásica)
* **`Min Size`:** Tamaño mínimo de los rectángulos indivisibles.
* **`Chaos`:** Probabilidad de división recursiva en los ejes $X$ e $Y$.

#### 17. Modo `Herringbone` (`Espiga / Zig-Zag`)
* **`Length` / `Width`:** Longitud y anchura de los bloques rectangulares entrelazados a $90^\circ$.

#### 18. Modo `Kagome` (`Trihexagonal`)
* **`Radius`:** Radio de la red geométrica tradicional compuesta por hexágonos y triángulos equiláteros entrelazados.

#### 19. Modo `Rhombille` (`Cubos Isométricos`)
* **`Radius`:** Radio de los rombos a $60^\circ$ dispuestos en perspectiva axonométrica simétrica simulando cubos 3D.

#### 20. Modo `Octagon` (`Mosaico Octogonal`)
* **`Radius`:** Dimensión de los octágonos combinados con pequeños cuadrados de unión.

#### 21. Modo `Scallop` (`Escamas de Pez`)
* **`Radius`:** Radio y arco de curvatura de las escamas semicirculares superpuestas.

#### 22. Modo `Web` (`Telaraña`)
* **`Cols` (Rings):** Cantidad de anillos concéntricos poligonales.
* **`Rows` (Rays):** Cantidad de filamentos radiales desde el epicentro.
* **`Chaos`:** Nivel de irregularidad estocástica en los nudos de la telaraña.

#### 23. Modo `Quad` (`Quadtree`)
* **`Min Size`:** Dimensión mínima de celda en la subdivisión recursiva jerárquica.
* **`Chaos`:** Umbral de probabilidad para la bifurcación de cuadrantes.

### 2.5. Ejemplo Práctico de Producción
* **Dispersión Estocástica en Malla Voronoi (*Shatter Effect*):**
  Conectando la silueta silábica a `Shape/Slicer` configurado en `mode: voronoi`, `cell_size: 25`, `anchor: pieces`:

  ```
  [System/Input: Syl Shape] ──► Shape ──► [Shape/Slicer: voronoi, anchor=pieces]
                                                ├──► Piece ──► Return ──► [System/Output]
                                                └──► (s_i, s_n en contexto)
  ```

  En un nodo de etiquetas conectado a `System/Output (Tags)`:
  ```
  {\p1\pos(syl.center, syl.middle)\t(0, 350, \frz(s_i * 20)\fscx0\fscy0\alpha&HFF&)}
  ```
  Cada fragmento Voronoi rota sobre su propio centroide individual y colapsa progresivamente con una rotación dependiente de `s_i`, manteniendo el anclaje local sin desfasar el trazado general.

---

## 3. Nodo `Shape/Manipulator` (Transformación y Deformación Espacial)

* **Categoría Canónica:** `Shape` (UI: *Shape / Manipulator*)
* **Propósito:** Aplica transformaciones de escala, deformaciones morfológicas, desplazamientos cartesianos, rotaciones 3D matriciales, remuestreo de curvas Bézier y reflexiones especulares sobre trazados vectoriales. Los puertos y campos de entrada en el cuerpo del nodo se reconfiguran dinámicamente según el modo seleccionado.

![Shape/Manipulator](img/manipulator.png)

### 3.1. Encabezado y Salidas
1. **`[1.1] Shape` (Output):** Emite el trazado ASSdraw vectorial modificado tras la evaluación de la transformación geométrica.
2. **`[1.2] Mode`:** Botón selector que alterna entre los 8 modos de manipulación espacial (`Scale`, `Borders`, `Deform`, `Position`, `Redraw`, `3D Rotate`, `Reflect`, `Matrix`).

---

### 3.2. Parámetros Universales Comunes
Estos parámetros aplican de forma transversal a todos los modos de manipulación:

1. **`Shape / Text`:** Forma vectorial ASSdraw o texto a manipular. Si no se conecta ningún enlace, toma el glifo del contexto activo (sílaba, palabra o línea).
2. **`Factor (t)`:** Factor de progresión temporal o interpolación paramétrica ($0.0 \to 1.0$) para animar la transformación de manera continua.
3. **`Anchor` (Punto de Anclaje de Forma Monolítica):** Sistema de referencia espacial utilizado para centrar o proyectar la forma durante la transformación:
   * **`center`:** Centra la masa de la forma alrededor de su centroide local `(0, 0)` (tinta).
   * **`origin`:** Alinea la esquina superior izquierda del cuadro delimitador (*bounding box*) de tinta en el origen `(0, 0)`.
   * **`relative`:** Conserva el origen de coordenadas `(0, 0)` original del trazado sin recentrar a la tinta (ideal para coincidir 1:1 con vectores tipográficos).
   * **`absolute`:** Traslada la geometría directamente a las coordenadas absolutas de pantalla del contexto `(fx.pos_x, fx.pos_y)`.

---

### 3.3. Entradas y Campos Específicos por Modo de Manipulación

#### 1. Modo `Scale` (Escalado Anamórfico)
Permite escalar independientemente los ejes horizontal y vertical con anclaje configurable.
* **`Shape / Text`:** Forma base a escalar.
* **`Factor (t)`:** Progresión de escala ($0.0 \to 1.0$).
* **`Scale X`:** Porcentaje de escala en el eje horizontal (default: `100`%).
* **`Scale Y`:** Porcentaje de escala en el eje vertical (default: `100`%).
* **`Anchor`:** Punto de anclaje de la ampliación/reducción (`center`, `origin`, `absolute`).

#### 2. Modo `Borders` (Expansión y Contracción Perimetral)
Dilata o erosiona paramétricamente los contornos cerrados mediante cálculo de offset morfológico acelerado por Clipper.
* **`Shape / Text`:** Forma base sobre la que se engrosará o adelgazará el perímetro.
* **`Factor (t)`:** Factor de progresión ($0.0 \to 1.0$).
* **`Offset (px)` (`offset_border`):** Distancia en píxeles del desplazamiento perimetral (valores positivos expanden la silueta hacia afuera; valores negativos contraen la masa hacia adentro; default: `2.0`).
* **`Anchor`:** Punto de anclaje de la forma resultante.

#### 3. Modo `Deform` (Deformación Direccional Asimétrica)
Aplica distorsiones y estiramientos direccionales basados en vectores de tracción o empuje sobre la geometría.
* **`Shape / Text`:** Forma base a distorsionar.
* **`Factor (t)`:** Progresión de deformación ($0.0 \to 1.0$).
* **`Offset X`:** Desplazamiento horizontal del vector de deformación.
* **`Offset Y`:** Desplazamiento vertical del vector de deformación.
* **`Def Factor` (`factor`):** Porcentaje de intensidad o escala de la distorsión morfológica (default: `100`%).
* **`Anchor`:** Punto de anclaje de la deformación.

#### 4. Modo `Position` (Desplazamiento Cartesiano Relativo)
Desplaza las coordenadas del dibujo en los ejes $X$ e $Y$ sin alterar la etiqueta de posición ASS `\pos`.
* **`Shape / Text`:** Forma base a desplazar.
* **`Factor (t)`:** Factor de interpolación del desplazamiento ($0.0 \to 1.0$).
* **`Offset X`:** Desplazamiento horizontal en píxeles.
* **`Offset Y`:** Desplazamiento vertical en píxeles.
* **`Anchor`:** Punto de anclaje de referencia (`center`, `origin`, `relative`, `absolute`).

#### 5. Modo `Redraw` (Remuestreo y Densidad Bézier)
Remuestrea y redistribuye los vértices y segmentos de curvas Bézier del trazado para suavizar contornos o añadir mayor densidad de puntos para efectos de deformación posterior.
* **`Shape / Text`:** Forma base a remuestrear.
* **`Factor (t)`:** Progresión de remuestreo ($0.0 \to 1.0$).
* **`Density / Step` (`density`):** Factor de densidad de muestreo de las curvas Bézier (valores más altos generan mayor cantidad de puntos de control interpolados; default: `2.0`).
* **`Anchor`:** Punto de anclaje del contorno remuestreado.

#### 6. Modo `3D Rotate` (Rotación Tridimensional Matricial)
Proyecta y rota la forma vectorial en el espacio tridimensional mediante álgebra lineal matricial, simulando giros axonométricos y perspectiva cónica.
* **`Shape / Text`:** Forma base a rotar tridimensionalmente.
* **`Factor (t)`:** Progresión del ángulo de rotación ($0.0 \to 1.0$).
* **`Rotate X` (`angle_x`):** Ángulo de rotación en grados sobre el eje $X$ (inclinación vertical / cabeceo con perspectiva).
* **`Rotate Y` (`angle_y`):** Ángulo de rotación en grados sobre el eje $Y$ (giro lateral / guiñada con perspectiva).
* **`Rotate Z` (`angle_z`):** Ángulo de rotación en grados sobre el eje $Z$ (rotación coplanar en pantalla / equivalente a `\frz`).
* **`Anchor`:** Centro de giro tridimensional (`center`, `origin`, `relative`, `absolute`).

#### 7. Modo `Reflect` (Reflejo y Espejado Simétrico)
Genera el reflejo simétrico especular de la forma respecto a un eje cartesiano y plano de referencia.
* **`Shape / Text`:** Forma base a reflejar.
* **`Factor (t)`:** Factor de interpolación del reflejo ($0.0 \to 1.0$).
* **`Axis`:** Eje de reflexión simétrica (`none` para conservar la forma original sin reflejar, `x` para inversión horizontal / izquierda-derecha, `y` para inversión vertical / arriba-abajo, `xy` para inversión diagonal).
* **`Offset X`:** Desplazamiento del eje de simetría en el plano horizontal.
* **`Offset Y`:** Desplazamiento del eje de simetría en el plano vertical.
* **`Anchor`:** Punto de anclaje de la proyección especular.

#### 8. Modo `Matrix` (Pipeline Maestro de Transformación Matricial)
Combina en una única pasada vectorial optimizada todos los operadores espaciales afines, morfológicos y tridimensionales:
$$\text{Desfase Clipper (Offset Border)} \longrightarrow \text{Remuestreo (Density)} \longrightarrow \text{Escala} \longrightarrow \text{Cizallamiento (Skew)} \longrightarrow \text{Rotación 3D Euler} \longrightarrow \text{Reflexión} \longrightarrow \text{Traslación (Offset)}$$

* **`Shape / Text`:** Trazado ASSdraw o texto de entrada.
* **`Factor (t)`:** Factor de interpolación paramétrica global ($0.0 \to 1.0$).
* **`Scale X` / `Scale Y`:** Porcentajes de escalado horizontal y vertical independientes (default: `100`%).
* **`Skew X` / `Skew Y`:** Factores de cizallamiento transversal (*shear*) en los ejes $X$ e $Y$.
* **`Rotate X` / `Rotate Y` / `Rotate Z`:** Ángulos de rotación en grados sobre los 3 ejes cartesianos (Euler con proyección de perspectiva cónica $fov$).
* **`Offset X` / `Offset Y`:** Desplazamientos cartesianos en píxeles.
* **`Offset Border`:** Desfase perimetral geométrico previo mediante Clipper en píxeles (valores positivos dilatan/expanden la forma; valores negativos la erosionan/contraen; default: `0.0`).
* **`Axis`:** Eje de reflexión especular (`none`, `x`, `y`, `xy`).
* **`Density`:** Remuestreo previo de curvas Bézier (default: `0` para desactivado; $> 0$ para densificar con paso en px).
* **`Anchor`:** Punto de anclaje de referencia espacial (`center`, `origin`, `relative`, `absolute`).

---

### 3.4. Ejemplo Práctico de Producción
* **Rotación 3D en Perspectiva de una Primitiva Vectorial:**
  Transformando una estrella de `Shape/Library` con rotación en el eje $Y$ (guiñada 3D) modulada por el tiempo de la sílaba:

  ```
  [Shape/Library: star] ──► Shape ──► Shape / Text ──► [Shape/Manipulator: 3D Rotate, Rotate Y=70]
                                                             └──► Shape ──► Return ──► [System/Output]
  ```

  En un nodo de etiquetas conectado a `System/Output (Tags)`:
  ```
  {\p1\pos(syl.center, syl.middle)\1c&H00FFFF&\bord1\3c&H003366&\t(0, syl.dur, \1c&HFF0088&)}
  ```
  La estrella rota tridimensionalmente sobre su centroide local proyectando perspectiva cónica, mientras sus colores transicionan sin desfasar el punto de anclaje de la sílaba.

---

## 4. Nodo `Shape/Filter` (Modulación y Perturbación de Vértices)

* **Categoría Canónica:** `Shape` (UI: *Shape / Filter*)
* **Propósito:** Modifica analítica, morfológica o estocásticamente las coordenadas de los vértices individuales de un trazado ASSdraw vectorial mediante la evaluación continua de expresiones matemáticas personalizadas, transformaciones cinemáticas escalonadas por subcontornos o perturbación estocástica controlada (*jitter / noise*).
* **Color Temático:** `#0F766E` / `#5B2C6F`

![Shape/Filter](img/filter.png)

---

### 4.1. Encabezado y Modos de Cabecera (*Header Mode Combos*)
El nodo dispone de un selector desplegable en su cabecera que reconfigura reactivamente los puertos de entrada y las propiedades del cuerpo según la técnica de deformación deseada:
1. **`Vertices` (Expresiones Analíticas por Vértice):** Aplica transformaciones matemáticas paramétricas sobre cada coordenada $(x, y)$ individual en función de variables de posición cartesianas, polares y métricas de contorno.
2. **`Group` (Transformaciones Progresivas por Subcontornos):** Itera sobre cada subcontorno cerrado o isla independiente (`m ...`) del trazado compuesto, aplicando giros, escalas y desplazamientos acumulativos por pieza.
3. **`Noise` (Perturbación Estocástica de Vértices):** Desplaza aleatoriamente cada vértice dentro de una ventana de dispersión elíptica o rectangular, con control de densidad geométrica previa y semilla determinista.

---

### 4.2. Puertos de Entrada y Propiedades del Cuerpo (*Inputs & Properties*)

#### 1. Modo `Vertices` (Expresiones Analíticas y Cinemática Paramétrica)
Evalúa expresiones algebraicas en tiempo real sobre cada par ordenado $(x_k, y_k)$ del trazado. Permite deformaciones orgánicas de alta complejidad (ondulaciones periódicas, vórtices gravitatorios, torsiones polares, expansiones balísticas y disoluciones no lineales).

1. **`[2.1] Shape / Text` (`shape`):** Trazado ASSdraw base o texto. Si se omite la entrada por cable, toma el glifo del contexto activo (`syl.text` o `line.text`).
2. **`[2.2] Expr X` (`expr_x`):** Expresión matemática que calcula la nueva posición horizontal del vértice (default: `x`).
3. **`[2.3] Expr Y` (`expr_y`):** Expresión matemática que calcula la nueva posición vertical del vértice (default: `y`).
4. **`[2.4] Factor (t)` (`t`):** Factor de modulación temporal o interpolación paramétrica ($0.0 \le t \le 1.0$). Modula suavemente el tránsito entre la geometría original y la calculada (default: `1.0`).
5. **`[2.5] Subdivs` (`subdivs`):** Factor de refinamiento y subdivisión previa de curvas Bézier y segmentos rectos antes de aplicar las ecuaciones (default: `0`).

##### Catálogo Exhaustivo de Variables en `Expr X` y `Expr Y`:
* **Coordenadas Cartesianas Absolutas:**
  * `x`, `y`: Coordenadas originales actuales del vértice evaluado en el lienzo local.
  * `cx`, `cy` (`Cx`, `Cy`): Coordenadas del centroide geométrico de la masa del trazado:
    $$cx = \frac{x_{\min} + x_{\max}}{2}, \quad cy = \frac{y_{\min} + y_{\max}}{2}$$
  * `width`, `height`: Dimensiones totales de la caja delimitadora (*bounding box*): $W = x_{\max} - x_{\min}$, $H = y_{\max} - y_{\min}$.
  * `minx`, `miny`, `maxx`, `maxy`: Coordenadas límite extremas del *bounding box*.
* **Coordenadas Normalizadas Relativas $(0.0 \to 1.0)$:**
  * `mx`, `my` (`Mx`, `My`): Posición porcentual normalizada del vértice respecto al *bounding box*:
    $$mx = \frac{x - x_{\min}}{\max(10^{-6}, W)}, \quad my = \frac{y - y_{\min}}{\max(10^{-6}, H)}$$
* **Métricas Polares y Distancias Euclidianas:**
  * `do`, `Do`: Distancia euclidiana desde el origen local `(0, 0)` hasta el vértice actual: $do = \sqrt{x^2 + y^2}$.
  * `dc`, `Dc`: Distancia euclidiana desde el centroide `(cx, cy)` hasta el vértice: $dc = \sqrt{(x - cx)^2 + (y - cy)^2}$.
  * `ao`, `Ao`: Ángulo polar en grados sexagesimales ($0^\circ \le ao < 360^\circ$) respecto al origen `(0, 0)`.
  * `ac`, `Ac`: Ángulo polar en grados sexagesimales ($0^\circ \le ac < 360^\circ$) respecto al centroide `(cx, cy)`.
* **Índices y Métricas de Secuencia:**
  * `k`, `i`, `Pk`: Índice ordinal 1-based del vértice evaluado ($1 \le k \le N$).
  * `n`, `Pn`: Cantidad total de vértices que componen el trazado.
  * `mp`, `Mp`: Progreso longitudinal normalizado del vértice a lo largo del recorrido perimetral: $mp = \frac{k - 1}{N - 1}$ (o $0.0$ si $N \le 1$).
  * `t`: Valor numérico actual del parámetro `Factor (t)`.
* **Funciones Matemáticas Disponibles:**
  * *Trigonométricas:* `sin(rad)`, `cos(rad)`, `tan(rad)`, `asin(v)`, `acos(v)`, `atan2(y, x)`.
  * *Conversión Angular y Constantes:* `rad(deg)` (grados a radianes), `deg(rad)` (radianes a grados), `pi`, `PI`.
  * *Álgebra y Exponenciales:* `sqrt(v)`, `abs(v)`, `min(a, b)`, `max(a, b)`, `exp(v)`, `log(v)`.
  * *Discretización y Redondeo:* `floor(v)`, `ceil(v)`, `round(v)`.

> [!IMPORTANT]
> **Aislamiento de Ámbito (*Scope Isolation*) y Tolerancia a Fallos:**  
> El evaluador matemático de `Vertices` opera en un entorno algebraico estricto y seguro. Funciones de azar externas como `Rs()` o `R()` **no existen** en este ámbito. Si una expresión contiene funciones indefinidas o errores sintácticos, el nodo activa automáticamente su mecanismo de tolerancia a fallos, preservando el vértice intacto ($x_{\text{final}} = x, y_{\text{final}} = y$) sin interrumpir el motor. Para deformaciones aleatorias, utilice el modo nativo **`Noise`** o funciones armónicas pseudoaleatorias basadas en `k`.

---

#### 2. Modo `Group` (Transformaciones Escalonadas por Subcontornos)
Segmenta la forma en sus islas vectoriales o subcontornos cerrados independientes (identificados por comandos de inicio de trazado `m ...`) y aplica transformaciones acumulativas progresivas a cada pieza.

1. **`[2.1] Shape / Text` (`shape`):** Trazado multitrazo compuesto (ej. glifos como "i", "j", "!", "¿", kanjis de múltiples trazos o formas fracturadas por *Slicer*).
2. **`[2.2] Factor (t)` (`t`):** Modulador temporal global ($0.0 \to 1.0$).
3. **`[2.3] Rotation Step` (`rot_step`):** Incremento angular en grados sexagesimales acumulado sucesivamente por pieza (default: `0.0`).
4. **`[2.4] Scale Step` (`scale_step`):** Porcentaje de escala acumulativo por pieza (default: `100.0`%).
5. **`[2.5] Offset X` (`offset_x`):** Desplazamiento horizontal acumulativo por pieza en píxeles (default: `0.0`).
6. **`[2.6] Offset Y` (`offset_y`):** Desplazamiento vertical acumulativo por pieza en píxeles (default: `0.0`).
7. **`[2.7] Anchor` (`anchor`):** Punto de anclaje local para el giro y escalado de cada isla (`center`, `origin`, `relative`, `absolute`).

---

#### 3. Modo `Noise` (Perturbación Estocástica de Vértices)
Inyecta fluctuaciones estocásticas uniformes a cada vértice dentro de una envolvente elíptica o rectangular, ideal para estilización analógica (*boiling line*, tiza, fuego, energía eléctrica, vapor o degradación orgánica).

1. **`[2.1] Shape / Text` (`shape`):** Trazado ASSdraw base a perturbar.
2. **`[2.2] Radius X` (`radius_x`):** Radio máximo de dispersión pseudoaleatoria horizontal en píxeles: $\Delta x \in [-R_x, +R_x]$ (default: `5.0`).
3. **`[2.3] Radius Y` (`radius_y`):** Radio máximo de dispersión pseudoaleatoria vertical en píxeles: $\Delta y \in [-R_y, +R_y]$ (default: `5.0`).
4. **`[2.4] Subdivs` (`subdivs`):** Nivel de subdivisión previa de curvas Bézier y aristas rectas antes de inyectar la perturbación (default: `2.0`).
5. **`[2.5] Seed` (`seed`):** Semilla numérica entera para el generador pseudoaleatorio determinista (default: `0`).

---

### 4.3. Puertos de Salida (*Outputs*)
1. **`[1.1] Shape`:** Emite el trazado ASSdraw vectorial modificado resultante (`m ... l ... b ...`), con las nuevas coordenadas proyectadas y listas para su renderizado o procesamiento booleano posterior.

---

### 4.4. Modelo Matemático y Comportamiento Algorítmico

#### 4.4.1. Interpolación Paramétrica en Modo `Vertices`
Dada una coordenada original $\vec{p} = (x, y)$ y las soluciones resultantes de las expresiones evaluadas $\vec{p}_{\text{calc}} = (\text{res}_x, \text{res}_y)$, la posición final emitida viene dada por la combinación convexa:

$$\vec{p}_{\text{final}}(t) = \vec{p} + t \cdot (\vec{p}_{\text{calc}} - \vec{p}) = \begin{pmatrix} x + t \cdot (\text{res}_x - x) \\ y + t \cdot (\text{res}_y - y) \end{pmatrix}$$

Donde $t \in [0.0, 1.0]$. Cuando $t = 0.0$, el trazado permanece inalterado; cuando $t = 1.0$, adopta la deformación calculada al 100%.

#### 4.4.2. Función del Parámetro `Subdivs` (Control de Frecuencia Espacial)
Las figuras tipográficas y primitivas vectoriales suelen definir tramos lineales extensos con solo dos vértices extremos (por ejemplo, el asta vertical de una "I" o los lados de un rectángulo). Si se evalúa una onda sinusoidal o ruido sin subdivisión previa, solo vibran los extremos, manteniendo la recta rígida.
* **$\text{Subdivs} = 0$:** Preserva la topología original de vértices. Idóneo para deformaciones globales *Low-Poly* o poligonales facetadas.
* **$\text{Subdivs} \ge 1.0$:** Subdivide recursivamente cada segmento recto y arco Bézier en $2^{\text{subdivs}}$ tramos preservando continuidad $C^1$. Al elevar la densidad de puntos, las ecuaciones de onda se reflejan como curvaturas continuas de alta fidelidad, y el modo `Noise` genera texturas rugosas de micro-frecuencia.

#### 4.4.3. Cinemática Acumulativa en Modo `Group`
Para un trazado segmentado en $M$ piezas con índice $j \in [0, M - 1]$:
$$\theta_j = j \cdot \text{Rot Step} \cdot t$$
$$S_j = \max\left(0.001, \, 1.0 + j \cdot \left(\frac{\text{Scale Step} - 100.0}{100.0}\right) \cdot t\right)$$
$$\Delta x_j = j \cdot \text{Offset X} \cdot t, \quad \Delta y_j = j \cdot \text{Offset Y} \cdot t$$

Cada subcontorno se escala y rota alrededor de su punto de anclaje local determinado por `Anchor`, permitiendo desarticulaciones balísticas por capas.

#### 4.4.4. Perturbación Estocástica y Animación en Modo `Noise`
En el modo `Noise`, cada vértice se traslada mediante variables aleatorias independientes uniformemente distribuidas:
$$x' = x + \Delta x, \quad \Delta x \sim \mathcal{U}(-R_x, \, +R_x)$$
$$y' = y + \Delta y, \quad \Delta y \sim \mathcal{U}(-R_y, \, +R_y)$$

* **Semilla Estática (`Seed` fija):** El mapa de perturbación es determinista y congruente, ideal para congelar siluetas rasgadas o desgastadas.
* **Semilla Dinámica (`Seed` variable):** Conectando el iterador de fotograma (`fx_i`, `j`, o una función temporal basada en `st`) al puerto `Seed`, el patrón de ruido muta en cada cuadro, produciendo la vibración orgánica característica del dibujo animado tradicional a mano alzada (*line boil*).

---

### 4.5. Catálogo de Recetas y Fórmulas Prácticas

#### Receta 1: Ondulación Sinusoidal / Efecto Bandera Flotante (Modo `Vertices`)
Aplica un oleaje transversal a lo largo del eje horizontal con subdivisión para flexionar las astas tipográficas:
* **`Subdivs`:** `2`
* **`Expr X`:** `x`
* **`Expr Y`:** `y + sin(rad(x * 6 + t * 360)) * 12`

#### Receta 2: Vórtice / Torsión Polar Gravitatoria (Modo `Vertices`)
Hace girar los vértices alrededor del centroide con un ángulo proporcional a su distancia $dc$, creando un remolino galáctico:
* **`Subdivs`:** `1`
* **`Expr X`:** `cx + dc * cos(rad(ac + dc * 1.5 * t))`
* **`Expr Y`:** `cy - dc * sin(rad(ac + dc * 1.5 * t))`

#### Receta 3: Pseudo-Ruido Caótico Armónico (Modo `Vertices`)
Genera perturbaciones de aspecto estocástico en modo `Vertices` sin depender de generadores externos, mediante frecuencias armónicas no congruentes sobre el índice del vértice $k$:
* **`Expr X`:** `x + sin(k * 12.9898) * 4 * t`
* **`Expr Y`:** `y + cos(k * 78.2330) * 4 * t`

#### Receta 4: Disolución por Ruido Vibrante / Estilo Tiza (Modo `Noise`)
Convierte tipografías vectoriales en trazos de tiza o contornos inestables en constante agitación:
* Encadenamiento: `Text to Shape` $\to$ `Shape/Filter (Noise)` $\to$ `Salida (Retorno)`
* **`Radius X`:** `3.5`
* **`Radius Y`:** `3.5`
* **`Subdivs`:** `2`
* **`Seed`:** `fx_i` *(varía en cada fotograma del bucle FBF)*

---

## 5. Nodo `Shape/Transform` (Morfología y Curvatura)

* **Categoría Canónica:** `Shape` (UI: *Shape / Transform*)
* **Propósito:** Realiza operaciones avanzadas de transformación no lineal sobre trazados vectoriales ASSdraw: hinchado radial (*Inflate*), cizallamiento angular (*Skew*), redondeo/biselado de esquinas (*Round Corners*), flexión sobre splines guía (*Flexor*) y metamorfosis continua entre múltiples formas (*Distort / Distort2*). Las entradas en el cuerpo del nodo se reconfiguran dinámicamente según el modo seleccionado.

![Shape/Transform](img/transform.png)

### 5.1. Encabezado y Salidas
1. **`[1.1] Shape` (Output):** Emite el trazado ASSdraw transformado resultante de la operación morfológica.
2. **`[1.2] Mode`:** Botón selector que alterna entre los 6 modos de transformación (`Inflate`, `Skew`, `Round Corners`, `Flexor`, `Distort`, `Distort2`).

---

### 5.2. Parámetros Universales Comunes
Estos parámetros aplican de forma transversal a las transformaciones:

1. **`Shape / Text`:** Forma vectorial ASSdraw o texto base a transformar. Si no se conecta ningún enlace, toma el glifo del contexto activo (sílaba, palabra o línea).
2. **`Factor (t)`:** Factor de progresión temporal o interpolación paramétrica ($0.0 \to 1.0$) que anima la transición suavemente desde el estado original hacia la forma transformada.
3. **`Anchor` (Punto de Anclaje y Relación Espacial entre Siluetas):** Define el sistema de coordenadas local y la relación geométrica de superposición y alineación entre la silueta de origen y la silueta objetivo durante la transformación o metamorfosis (*morphing*):
   * **Superposición y Normalización Automática:** Antes de la interpolación de vértices, la silueta objetivo se escala proporcionalmente y se superpone sobre la silueta base para hacer coincidir sus dimensiones relativas. Durante la animación ($t = 0.0 \to 1.0$), el *bounding box* resultante evoluciona de manera continua ($W(t) = W_A(1-t) + W_B(t)$ y $H(t) = H_A(1-t) + H_B(t)$).
   * **Comportamiento y Alineación según el Anchor seleccionado:**
     * **`center` (Por Defecto - Alineación Concéntrica):** 
       * **Relación entre siluetas:** Alinea ambas formas haciendo coincidir sus centroides geométricos $(\frac{x_{\min}+x_{\max}}{2}, \frac{y_{\min}+y_{\max}}{2})$.
       * **Efecto Visual:** El dibujo ASSdraw final se centra en `(0, 0)`, de modo que al aplicarse con `\pos(x, y)` o alineación central (`\an5`), la metamorfosis ocurre concéntricamente en el centro exacto del glifo o partícula, expandiéndose y contrayéndose simétricamente en todas las direcciones.
      * **`origin` (Alineación Superior Izquierda de Tinta):** 
        * **Relación entre siluetas:** Alinea ambas formas por su vértice superior izquierdo $(x_{\min}, y_{\min})$.
        * **Efecto Visual:** El origen `(0, 0)` se fija en la esquina superior izquierda del *bounding box*. Al renderizarse (ej. `\an7`), la transformación se proyecta hacia la derecha y hacia abajo, manteniendo inmóvil la esquina superior izquierda común de ambas figuras.
      * **`absolute` (Alineación Absoluta de Contexto / Pantalla):** 
        * **Relación entre siluetas:** Conserva la posición espacial relativa del glifo original en pantalla (`fx.pos_x`, `fx.pos_y`), alineando la masa de la metamorfosis con la ubicación real del subtítulo en el canvas.
---

### 5.3. Entradas y Campos Específicos por Modo de Transformación

#### 1. Modo `Inflate` (Hinchado Radial / Esferificación)
Proyecta y deforma radialmente los vértices hacia afuera o hacia adentro tomando como referencia una envolvente circular o elíptica centrada en la masa de la forma.
* **`Shape / Text`:** Trazado base a inflar o desinflar.
* **`Factor (t)`:** Progresión de hinchado ($0.0 \to 1.0$).
* **`Ratio`:** Proporción o intensidad de la fuerza de inflado radial (default: `1.0`).
* **`Anchor`:** Punto de anclaje central de la expansión/contracción radial (`center`, `origin`, `absolute`).
* **`Inflate Mode` (Propiedad / Widget):** Geometría de referencia de inflado (`Circle` para esferificación circular uniforme, `Ellipse` para hinchado proporcional al ancho y alto del bounding box).

#### 2. Modo `Skew` (Cizallamiento / Inclinación 2D)
Aplica una deformación angular oblicua sobre los ejes cartesianos manteniendo paralelas las líneas opuestas.
* **`Shape / Text`:** Trazado base a inclinar.
* **`Factor (t)`:** Progresión de inclinación ($0.0 \to 1.0$).
* **`Angle X`:** Ángulo de cizallamiento horizontal en grados (desliza las líneas horizontales paralelamente sobre el eje $X$).
* **`Angle Y`:** Ángulo de cizallamiento vertical en grados (desliza las líneas verticales paralelamente sobre el eje $Y$).
* **`Anchor`:** Punto de anclaje base del cizallamiento.

#### 3. Modo `Round Corners` (Redondeo y Biselado de Vértices)
Detecta los vértices y ángulos agudos del trazado poligonal y los reemplaza por arcos de curva Bézier suavizados o cortes achaflanados.
* **`Shape / Text`:** Trazado poligonal con esquinas a suavizar.
* **`Factor (t)`:** Progresión del redondeo ($0.0 \to 1.0$).
* **`Radius (px)` (`radius`):** Radio de curvatura o profundidad de corte de las esquinas en píxeles (default: `10.0`).
* **`Anchor`:** Punto de anclaje del trazado (`center`, `origin`, `relative`, `absolute`).
* **`Corner Mode` (Propiedad / Widget):** Tipo de unión geométrica en las esquinas:
  * **`Round`:** Arcos de circunferencia suavizados mediante curvas cúbicas Bézier.
  * **`Bevel`:** Chaflán recto biselado que une los dos lados mediante un segmento lineal plano.
  * **`Miter`:** Inglete puntiagudo extendido con límite de proyección.

#### 4. Modo `Flexor` / `Bend` (Flexión sobre Curvas y Splines Guía)
Pliega y flexiona la forma a lo largo de un arco paramétrico o una curva spline ASSdraw personalizada.
* **`Shape / Text`:** Trazado base a flexionar.
* **`Factor (t)` / `Bend (t)`:** Factor de progresión de la flexión ($0.0 \to 1.0$).
* **`Curve / Angle` (`curve`):** Grados de curvatura angular numérica (ej. `30`, `45`, `-60`) o código ASSdraw completo de una curva guía (`m ... b ...`) sobre la cual se proyectará el dibujo.
* **`Anchor`:** Punto de anclaje de la proyección (`center`, `origin`, `relative`, `absolute`).
* **`Axis` (Propiedad):** Eje rector de la flexión (`x` para doblar la forma horizontalmente a lo largo del arco, `y` para doblar en sentido vertical).

#### 5. Modo `Distort` (Metamorfosis Vectorial de 2 Formas - *Morphing*)
Ejecuta una interpolación perimetral continua y adaptativa entre una forma de origen (`Shape / Text`) y una forma objetivo de destino (`Target Shape`). Soporta tanto dibujos ASSdraw nativos como glifos de texto vectorizados:
* **`Shape / Text`:** Trazado vectorial o cadena de texto de origen en el instante inicial ($t = 0.0$). Si recibe texto, se vectoriza automáticamente con la tipografía y estilo de la línea.
* **`Target Shape`:** Trazado vectorial o texto objetivo en el instante final ($t = 1.0$).
* **`Factor (t)`:** Factor de progresión de la metamorfosis ($0.0 \to 1.0$).
* **`Energy` (`Fluidez`):** Coeficiente de elasticidad y modulación armónica fluida durante la transición ($0 < t < 1$). Aplica una función de onda sinusoidal $W(t) = \sin(\pi \cdot t)$ sobre las manetas de control Bézier intermedias ($\vec{p_1}, \vec{p_2}$), otorgando una deformación elástica sin alterar la coincidencia geométrica en $t = 0$ y $t = 1$ (default: `0.35`).
* **`Step (px)` (`Paso`):** Resolución de subdivisión métrica en píxeles. Si `Step (px)` $> 0.05$, divide las curvas y segmentos del contorno cada $N$ píxeles exactos ($\text{pasos} = \max(1, \text{round}(L / s_{px}))$), garantizando un remuestreo perimetral uniforme antes de la correspondencia de vértices (default: `0` para cálculo adaptativo).
* **`Anchor`:** Punto de anclaje de alineación y superposición espacial entre ambas siluetas (`center`, `origin`, `relative`, `absolute`).

#### 6. Modo `Distort2` (Metamorfosis Vectorial en 3 Etapas)
Permite transiciones morfológicas continuas en tres fases encadenadas: Forma Inicial ($t = 0.0$) $\to$ Forma Intermedia ($t = 0.5$) $\to$ Forma Final ($t = 1.0$):
* **`Shape / Text`:** Trazado vectorial o texto inicial ($t = 0.0$).
* **`Mid Shape`:** Trazado vectorial o texto de paso intermedio alcanzado al $50\%$ de la animación ($t = 0.5$).
* **`Target Shape`:** Trazado vectorial o texto objetivo final ($t = 1.0$).
* **`Factor (t)`:** Progresión global de la metamorfosis en 3 etapas ($0.0 \to 1.0$).
* **`Energy` (`Fluidez`):** Coeficiente de modulación armónica fluida sobre las tangentes Bézier (default: `0.35`).
* **`Step (px)` (`Paso`):** Subdivisión métrica por cantidad de píxeles para remuestreo perimetral uniforme (default: `0`).
* **`Anchor`:** Punto de anclaje espacial de alineación (`center`, `origin`, `relative`, `absolute`).

---

### 5.4. Ejemplo Práctico de Producción
* **Metamorfosis Vectorial de Texto a Primitiva (Morphing):**
  Transformando la silueta tipográfica de la sílaba en una estrella de `Shape/Library` durante el tiempo activo de la nota:

  ```
  [System/Input: Syl Shape] ──► Shape / Text ──┐
                                              ├──► [Shape/Transform: Distort, Energy=0.35]
  [Shape/Library: star] ────► Target Shape ───┘          └──► Shape ──► Return ──► [System/Output]
  ```

  Enlazando `Factor (t)` a la progresión normalizada del tiempo de la sílaba y configurando `System/Output (Tags)`:
  ```
  {\p1\pos(syl.center, syl.middle)\1c&H00FFFF&\bord1\3c&H000000&\t(0, syl.dur, \1c&H0088FF&)}
  ```
  El glifo de la sílaba se deforma perimetralmente de manera continua hacia el contorno de la estrella sobre el centroide local sin desfasar el anclaje central.

---

## 6. Nodo `Shape/Concentric Borders` (Capas y Bordes Concéntricos)

* **Categoría Canónica:** `Shape` (UI: *Shape / Concentric Borders*)
* **Propósito:** Genera anillos concéntricos, contornos escalonados u ondas perimetrales sucesivas hacia afuera a partir de un contorno vectorial base utilizando el motor de dilatación geométrica y diferencias booleanas de *Clipper*.

![Shape/Concentric Borders](img/concentric_borders.png)

### 6.1. Encabezado y Barra de Título
1. **`[1.1] Concentric Borders`:** Título identificador del nodo.
2. **`[1.2] Modo de Salida Vectorial` (`out_mode`):** Botón selector situado en la esquina superior derecha de la **barra de título**. Define el formato del resultado emitido por el puerto de salida `Shape`:
   * **`Shape`:** Emite el código de dibujo ASSdraw directo del anillo o borde (`m ... l ... b ...`).
   * **`\clip` (`Clip`):** Emite la etiqueta de recorte ASS `\clip(m ...)` con el trazado posicionado en coordenadas absolutas de pantalla.
   * **`\iclip` (`iClip`):** Emite la etiqueta de recorte invertido ASS `\iclip(m ...)`.

---

### 6.2. Puertos de Entrada, Controles y Modos del Cuerpo
1. **`[2.1] Shape / Text`:** Contorno, silueta ASSdraw o texto inicial a partir del cual se calcularán las capas concéntricas. Si no se conecta ninguna entrada, toma automáticamente la forma del elemento activo en el contexto (sílaba, palabra o línea).
2. **`[2.2] Mode: [Hollow / Solid]` (Modo de Relleno o Hueco en el Cuerpo):** Botón selector ubicado en el cuerpo del nodo (segunda ranura) que define la topología de las capas:
   * **`Hollow (borders)` / `Hollow`:** Todos los anillos generados son bandas huecas de grosor constante calculadas mediante la diferencia booleana entre el contorno exterior dilatado y el contorno interior:
     $$\text{Ring}_i = \text{BooleanDifference}(\text{Outer}_i, \text{Inner}_i)$$
   * **`Solid (filled borders)` / `Solid`:** El primer elemento inicial ($i = 1$) conserva el relleno sólido completo de la forma base original, mientras que las capas concéntricas subsiguientes ($i \ge 2$) se computan como anillos huecos perimetrales hacia afuera.
3. **`[2.3] Max Rings` (`loop_count`):** Cantidad máxima total de capas concéntricas a generar en la secuencia de bucle (default: `5`). Define el valor de `b_n` y `maxloop`.
4. **`[2.4] Separación (px)` (`separation`):** Distancia en píxeles de separación o grosor de dilatación entre anillos sucesivos. Admite un valor numérico fijo (ej. `5.0`) o listas de patrones separados por comas (ej. `5, 2, 8, 3`) para generar ritmos concéntricos alternados de grosor variable.
5. **`[2.5] Solape (px)` (`overlap`):** Margen de solapamiento en píxeles entre capas contiguas (default: `0.5`). Elimina fisuras o costuras de renderizado causadas por el antialiasing del motor libass/VSFilter al unir piezas adyacentes.
6. **`[2.6] Anchor` (`Center` / `Relativo` / `Absoluto` / `Piezas`):** Botón selector que determina el punto de anclaje y sistema de coordenadas de referencia espacial para la geometría generada.
7. **`[2.7] b_i, b_n`:** Variables de iteración expuestas en el pie del nodo (`b_i` / `ring_i` = índice del anillo actual $[1 \dots N]$, `b_n` / `ring_n` = total de anillos concéntricos producidos).

---

### 6.3. Puertos de Salida (*Outputs*)
1. **`[3.1] Shape`:** Trazado ASSdraw o etiqueta `\clip`/`\iclip` del anillo correspondiente a la iteración activa `b_i`.
2. **`[3.2] \pos`:** Etiqueta `\pos(x,y)` calculada para posicionar el centroide del anillo en el lienzo.
3. **`[3.3] Index`:** Índice del anillo actual ($1 \dots \text{Max Rings}$).
4. **`[3.4] Total`:** Cantidad total de capas o anillos producidos ($b\_n$).

### 6.4. Ejemplo Práctico de Producción
* **Ondas Perimetrales Concéntricas con Desvanecimiento Gradual:**
  Conectando la silueta silábica a `Shape/Concentric Borders` con `loop_count: 5`, `separation: 6`, `mode: hollow`:

  ```
  [System/Input: Syl Shape] ──► Shape / Text ──► [Shape/Concentric Borders: hollow, max=5]
                                                       ├──► Shape ──► Return ──► [System/Output]
                                                       └──► (b_i, b_n en contexto)
  ```

  En un nodo de etiquetas conectado a `System/Output (Tags)`:
  ```
  {\p1\pos(syl.center, syl.middle)\1c&H00FFFF&\bord0\1a&H44&\t(0, 400, \fscx(100 + b_i * 15)\fscy(100 + b_i * 15)\1a&HFF&)}
  ```
  Genera 5 capas concéntricas sucesivas de grosor 6 px que se expanden hacia el exterior atenuando progresivamente su opacidad según el índice `b_i`.

---

## 7. Nodo `Shape/Walker` (Trayectorias y Trazado Progresivo)

* **Categoría Canónica:** `Shape` (UI: *Shape / Walker*)
* **Propósito:** Recorre e integra paramétricamente la longitud de arco de una forma vectorial ASSdraw, calculando la segmentación progresiva del trazado (*write-on / stroke trimming*) en el intervalo $[start\_t, progress]$ y emitiendo la posición cartesiana `\pos` y el ángulo tangencial `\frz` en la punta de avance.

![Shape/Walker](img/walker.png)

### 7.1. Modos de Cabecera y Parámetros
1. **Modo de Integración (`mode`):**
   * `global`: Integra la longitud de arco total acumulada sumando todos los subcontornos o trazos independientes de la forma. El intervalo $[0.0, 1.0]$ recorre secuencialmente la geometría completa de inicio a fin.
   * `piece`: Aplica el avance $[0.0, 1.0]$ de forma simultánea e independiente sobre cada subcontorno `m` de la figura (adecuado para escritura paralela de múltiples glifos).
2. **Sentido de Avance (`invert`):**
   * `normal`: Recorre los vértices en el orden natural en que fueron generados.
   * `inverted`: Invierte el sentido perimetral del recorrido (de fin a inicio).

### 7.2. Puertos de Entrada y Propiedades del Cuerpo
1. **`[2.1] Shape / Text`:** Trazado vectorial ASSdraw o texto a recorrer.
2. **`[2.2] Progress (t)` (`progress`):** Factor de avance final del segmento recortado ($t_2 \in [0.0, 1.0]$, defecto: `1.0`).
3. **`[2.3] Start (t)` (`start_t`):** Factor de avance inicial del segmento ($t_1 \in [0.0, 1.0]$, defecto: `0.0`). Permite generar ventanas móviles o estelas perimetrales.
4. **`[2.4] Subdivs` (`subdivs`):** Pasos de subdivisión por curva Bézier para el muestreo de longitud de arco (defecto: `30`).
5. **`[2.5] Close Path` (`close_path`):** Booleano (defecto: `False`). Si es `True`, inserta un comando rectilíneo `l` hacia el punto inicial `m` de cada contorno si este finaliza abierto.

### 7.3. Puertos de Salida (*Outputs*)
1. **`[1.1] Shape Out`:** Trazado vectorial ASSdraw recortado entre $t_1$ y $t_2$.
2. **`[1.2] \pos Tag`:** Etiqueta ASS `\pos(x,y)` calculada en la punta del trazado ($t_2$) proyectada sobre las coordenadas de pantalla.
3. **`[1.3] Angle (\frz)`:** Ángulo tangencial en grados sexagesimales en la punta de avance, orientado a lo largo de la tangente geométrica de la curva.
4. **`[1.4] Length`:** Longitud de arco efectiva en píxeles del segmento emitido.
5. **`[1.5] Tip X`:** Coordenada cartesiana horizontal absoluta de la punta.
6. **`[1.6] Tip Y`:** Coordenada cartesiana vertical absoluta de la punta.

### 7.4. Detalle Algorítmico y Modelo Matemático
1. **Muestreo de Longitud de Arco:**
   Para cada spline cúbica de Bézier $\mathbf{B}(u) = (1-u)^3\mathbf{P}_0 + 3(1-u)^2u\mathbf{P}_1 + 3(1-u)u^2\mathbf{P}_2 + u^3\mathbf{P}_3$, se evalúan $S = \text{subdivs}$ cuerdas consecutivas:
   $$L_{\text{arc}} = \sum_{j=1}^{S} \|\mathbf{B}(j/S) - \mathbf{B}((j-1)/S)\|$$
2. **Recorte Paramétrico:**
   Las marcas $s_1 = start\_t \cdot L_{\text{total}}$ y $s_2 = progress \cdot L_{\text{total}}$ determinan los puntos exactos de corte, evaluados mediante el algoritmo de De Casteljau.
3. **Cálculo Tangencial y Posicionamiento:**
   $$\theta = \operatorname{atan2}\left(\frac{dy}{du}, \, \frac{dx}{du}\right) \cdot \frac{180}{\pi}$$
   $$\text{pos}_x = x_{\text{parent}} + \text{Tip X}, \quad \text{pos}_y = y_{\text{parent}} + \text{Tip Y}$$

### 7.5. Ejemplo Práctico de Producción
* **Efecto de Trazado Creciente (*Write-on*) con Partícula Guía:**
  Alimentando `Progress (t)` mediante la progresión de `Loops/Module` ($0.0 \to 1.0$):
  
  ```
  Línea 1 (Trazo dibujado en expansión):
  Conectar Shape Out a System/Output (Return)
  Tags: {\p1\pos(syl.center, syl.middle)\1c&H00FFFF&\bord0}
  
  Línea 2 (Partícula o chispa anclada a la punta):
  Conectar Tip X, Tip Y y Angle (\frz) a Variables (o pasar \pos Tag directo):
  Tags: {\p1\pos(tip_x, tip_y)\frz(angle)\1c&HFFFFFF&\bord0}
  Return: m -4 -4 l 4 0 l -4 4
  ```

---

## 8. Nodo `Shape/Stroke` (Extrusión de Grosor en Trazados y Líneas)

* **Categoría Canónica:** `Shape` (UI: *Shape / Stroke*)
* **Propósito:** Convierte líneas abiertas, contornos esqueléticos o trazados vectoriales sin grosor en polígonos cerrados de doble contorno con grosor paramétrico y control topológico de uniones angulares y remates terminales mediante *Clipper2*.

![Shape/Stroke](img/stroke.png)

### 8.1. Puertos de Entrada (*Inputs*)
1. **`Shape / Text`:** Trazado vectorial ASSdraw de línea abierta, curva o texto sobre el que se aplicará la extrusión.
2. **`Width (px)`:** Entrada dinámica opcional para modular el grosor en píxeles. Si no está conectada, evalúa la propiedad `width`.

### 8.2. Controles y Propiedades del Cuerpo
1. **`[2.1] Width (px)` (`width`):** Grosor perimetral volumétrico total en píxeles (defecto: `4.0`, mínimo: $0.01$).
2. **`[2.2] Join Mode` (`join_mode`):** Tipo de unión geométrica en vértices y esquinas intermedias:
   * `round`: Esquinas redondeadas continuas mediante arcos circulares.
   * `miter`: Unión en inglete puntiagudo con corte según límite de bisel.
   * `bevel`: Esquinas biseladas con chaflán recto plano.
3. **`[2.3] Cap Mode` (`cap_mode`):** Tipo de remate terminal en los extremos de líneas abiertas:
   * `round`: Semicírculo exacto de radio $w/2$.
   * `bezier`: Remate redondeado suavizado por curvatura cúbica Bézier.
   * `flat`: Corte plano perpendicular directo al vector final.
   * `square`: Extremo cuadrado extendido una distancia $w/2$ más allá del vértice final.
4. **`[2.4] Miter Limit` (`miter_limit`):** Relación máxima entre la longitud del inglete y el grosor del trazo antes de truncarse en bisel (defecto: `2.0`, mínimo: $1.0$).

### 8.3. Puertos de Salida (*Outputs*)
1. **`[1.1] Shape Out`:** Trazado poligonal ASSdraw cerrado resultante (`m ... l ... b ...`) con el grosor y remates aplicados, listo para rellenar con `\p1`.
2. **`[1.2] Width`:** Grosor numérico efectivo aplicado en píxeles.

### 8.4. Detalle Algorítmico y Topología de Offset
El nodo procesa la geometría delegando en el motor de dilatación bilateral de Clipper2:
* Cada segmento lineal abierto genera un rectángulo de dimensiones $L \times w$.
* En vértices de deflexión angular, se inserta una cuña poligonal gobernada por `join_mode`.
* Si la geometría de entrada ya corresponde a un polígono cerrado, `Stroke` genera una banda perimetral hueca de ancho $w$ centrada sobre el borde original.

### 8.5. Ejemplo Práctico de Producción
* **Contorno Grueso con Remate Bézier sobre Primitiva:**
  Extruyendo los vértices de una forma lineal o un contorno de `Shape/Library`:
  
  ```
  [Shape/Library: triangle] ──► Shape ──► Shape / Text ──► [Shape/Stroke: width=6, join=round] ──► Shape Out ──► Output (Return)
  ```
  
  En un nodo de etiquetas conectado a `System/Output (Tags)`:
  ```
  {\p1\pos(syl.center, syl.middle)\1c&HFF0066&\bord1\3c&H000000&}
  ```
  Produce una silueta triangular hueca con bordes de 6 píxeles de grosor y uniones redondeadas.

---

## 9. Nodo `Shape/Union & Divide` (Desglose Topológico, Unión y Fusión con Tags)

* **Categoría Canónica:** `Shape` (UI: *Shape / Union & Divide*)
* **Propósito:** Nodo multifuncional de topología vectorial basado en *Clipper*. Permite descomponer trazados complejos en islas vectoriales reales mediante análisis de jerarquía de polígonos (*PolyTree*), separar subrutas simples, unir siluetas mediante unión booleana o fusionar múltiples piezas en un único bloque de dibujo intercalando etiquetas ASS con soporte de *keyframes* e interpolación.

![Shape/Union & Divide](img/union_&_divide.png)

---

### 9.2. Encabezado y Barra de Título
1. **`[1.1] Union & Divide`:** Título identificador del nodo.
2. **`[1.2] Botón Selector de Modo` (`mode`):** Botón ubicado en la esquina superior derecha de la barra de título que conmuta entre las 4 operaciones topológicas disponibles:
   * **`[DIVIDE]` (`Dividir (PolyTree)`):** Desglose topológico exacto en islas cerradas e independientes distinguiendo agujeros internos.
   * **`[UNION]` (`Unir (Boolean Union)`):** Fusión geométrica booleana de dos formas o listas de trazados.
   * **`[SUB-PATHS]` (`Sub-Ruta (Naive)`):** Separación directa e inmediata por comandos `m ...` de inicio de subtrazo.
   * **`[FUSION]` (`Fusión (Tags)`):** Ensamblado monolítico de múltiples piezas en una única línea de dibujo intercalando bloques de etiquetas ASS (`{\tags1}m... {\tags2}m...`).

---

### 9.3. Entradas, Controles y Modos Específicos

#### 1. Modo `[DIVIDE]` (Dividir PolyTree)
Analiza la estructura anidada del trazado mediante el árbol de polígonos de Clipper (*PolyTree*). A diferencia de una simple separación por comandos `m`, este modo distingue correctamente entre contornos exteriores e islas con agujeros internos (por ejemplo, en letras como "O", "B", "A", "8" o caracteres kanji complejos), agrupando cada figura externa con sus respectivos huecos en una pieza cerrada autónoma.
* **`[2.1] Shape In`:** Trazado ASSdraw o texto a descomponer en islas.
* **`[2.2] Rule:` (`fill_type`):** Regla de devanado y relleno booleano (`EvenOdd`, `NonZero`, `Positive`, `Negative`).
* **`[2.3] Clean:` (`clean_self_intersect`):** Limpieza automática de auto-intersecciones de bordes (`Auto (1)` activado, `Off (0)` desactivado).
* **`[2.4] Anchor` (`Pieces`):** Botón selector de anclaje de referencia espacial (`Pieces` recentra cada pieza en su centroide local, `Relative`, `Parent Org` / `Org Padre`, `Pos`, `Absolute`).
* **`[2.5] Order:` (`order`):** Criterio de ordenamiento espacial de las piezas para la secuencia de iteración (`79 (TL->BR)`, `97 (TR->BL)`, `13 (BL->TR)`, `31 (BR->TL)`, `71 (TL->BL)`, `17 (BL->TL)`, `93 (TR->BR)`, `39 (BR->TR)`, `5 (Centro)`, `-5 (Inverso)`, `cw` horario, `ccw` antihorario, `rand` aleatorio, `path` secuencia de dibujo original, `path_inv` secuencia invertida).

#### 2. Modo `[UNION]` (Unir Boolean Union)
Combina dos siluetas vectoriales superpuestas en un único trazado unificado, fusionando las masas y eliminando automáticamente cualquier línea perimetral o solapamiento interno.
* **`[2.1] Shape In (A)`:** Primera forma vectorial base (`shape`).
* **`[2.1b] Shape In (B)`:** Segunda forma vectorial (`shape_b`) a fusionar con la primera.
* **`[2.2] Rule:` (`fill_type`):** Regla de relleno booleano (`EvenOdd`, `NonZero`).
* **`[2.3] Clean:` (`clean_self_intersect`):** Limpieza automática de auto-intersecciones (`Auto (1)`).
* **`[2.4] Anchor` (`Pieces`):** Punto de anclaje de la figura unificada resultante.

#### 3. Modo `[SUB-PATHS]` (Sub-Ruta Naive)
Descompone el dibujo dividiendo de manera directa por cada comando de inicio `m ...` sin realizar cálculos topológicos de agujeros. Es ideal para formas abiertas, siluetas sencillas o líneas de caligrafía.
* **`[2.1] Shape In`:** Trazado ASSdraw con múltiples comandos `m`.
* **`[2.2] Anchor` (`Pieces`):** Punto de anclaje de los subcaminos resultantes.
* **`[2.3] Order:` (`order`):** Criterio de ordenamiento espacial de los subcaminos (`79`, `97`, `13`, `31`, `71`, `17`, `93`, `39`, `5`, `-5`, `cw`, `ccw`, `rand`, `path`, `path_inv`).

#### 4. Modo `[FUSION]` (Fusión Tags con Keyframes)
Permite empaquetar múltiples islas vectoriales en una **única línea de dibujo ASS** (`{\tags1}m ... {\tags2}m ...`), eliminando la necesidad de generar múltiples líneas en el archivo subtítulo. Permite estilizar individualmente cada pieza mediante bloques de etiquetas y transiciones de color.
* **`[2.1] Shape In`:** Trazado multitrazo, texto o lista de formas vectoriales independientes a fusionar.
* **`[2.2] Tag Mode:` (`tagmode`):** Mecanismo de asignación de etiquetas:
  * **`ipol` (Interpolado Progresivo):** Trata la lista de etiquetas como *keyframes*. Calcula la progresión espacial ($0.0 \to 1.0$) y realiza una interpolación matemática suave de los valores entre la primera y la última pieza (ideal para gradientes continuos de color `\1c`, rotaciones progresivas `\frz`, variaciones de transparencia `\alpha` o desenfoque `\blur`).
  * **`line` (Lineal 1:1 Estricto):** Asigna cada bloque de etiquetas de la lista uno a uno a su pieza correspondiente según el orden establecido. Si faltan etiquetas, el resto de piezas recibe `{\p1}`; si sobran, se descartan ordenadamente.
* **`[2.3] Tags` (`tags`):** Lista de etiquetas ASS o colores hexadecimales separados por comas o bloques (ej. `\1c&H0000FF&, \1c&H00FF00&, \1c&HFF0000&` o `#87F337, #61FBC7, #AF6DF6`).
* **`[2.4] Anchor` (`Pieces`):** Anclaje espacial de alineación.
* **`[2.5] Order:` (`order`):** Orden espacial en que se asignan o interpolan los tags sobre las piezas (`79`, `97`, `13`, `31`, `71`, `17`, `93`, `39`, `5`, `-5`, `cw`, `ccw`, `rand`, `path`, `path_inv`).

---

### 9.4. Puertos de Salida (*Outputs*) y Pie del Nodo
1. **`[3.1] Shape Out`:** Emite el trazado ASSdraw resultante:
   * En modos de división (`DIVIDE`, `SUB-PATHS`): Emite la pieza individual correspondiente a la iteración activa `d_i`.
   * En modos de unión y fusión (`UNION`, `FUSION`): Emite la forma única unificada o la cadena compuesta con etiquetas intercaladas.
2. **`[3.2] Out List`:** Emite una lista en formato JSON con todas las piezas vectoriales generadas para procesamiento por lotes o encadenamiento con otros nodos.
3. **`[3.3] BBox Data`:** Emite una cadena con los datos métricos del *bounding box* global (`min_x,min_y,max_x,max_y,cx,cy,width,height`).

* **Pie del Nodo (`d_i, d_n`):** Variables de contexto de acceso al sub-bucle/loop interno anidado generado por `Union & Divide` (`d_i` = índice ordinal de la pieza activa $[1 \dots N]$, `d_n` / `d_max` = cantidad total de piezas o islas generadas en la partición).

---

---

### 9.6. Ejemplo Práctico de Producción
* **Descomposición Topológica en Islas con Caída Gravitatoria Secuencial:**
  Dividiendo un kanji o palabra compleja en piezas cerradas independientes (`DIVIDE`) y animando la caída de cada isla con retardo temporal gobernado por `d_i`:

  ```
  [System/Input: Syl Shape] ──► Shape In ──► [Shape/Union & Divide: DIVIDE, order=79, anchor=pieces]
                                                   ├──► Shape Out ──► Return ──► [System/Output]
                                                   └──► (d_i, d_n en contexto)
  ```

  En un nodo de etiquetas conectado a `System/Output (Tags)`:
  ```
  {\p1\pos(syl.center, syl.middle)\t(d_i * 40, d_i * 40 + 300, \frz(d_i * 15)\fscx0\fscy0\alpha&HFF&)}
  ```
  Cada isla vectorial desciende y rota sobre su propio centroide con un retardo escalonado de 40 ms por pieza, preservando los agujeros internos (PolyTree) sin colapsar la silueta general.

---

## 10. Nodo `Shape/Clipper` (Operaciones Booleanas Vectoriales Avanzadas y Morfología de Corte)

* **Categoría Canónica:** `Shape` (UI: *Shape / Clipper*)
* **Propósito:** Aplica operaciones booleanas (diferencia, intersección, unión, XOR), desfases perimetrales morfológicos y sumas/diferencias de Minkowski entre dos geometrías vectoriales cerradas o abiertas mediante el motor de alta precisión Clipper2. Emite código de dibujo ASSdraw (`Shape Out`) o etiquetas de recorte (`\clip`, `\iclip`).

![Shape/Clipper](img/clipper.png)

---

### 10.1. Encabezado y Modos de Operación (`mode`)
1. **`[1.1] Clipper`:** Título identificador del nodo.
2. **`[1.2] Botón Selector de Modo` (`mode`):**
   * **`difference` (`Diferencia / Sustracción A - B`):** Sustrae la geometría `Shape B (Clip)` de la forma base `Shape A (Subject)`. Ideal para troquelar agujeros, mordiscos y siluetas negativas personalizadas.
   * **`intersection` (`Intersección A ∩ B`):** Conserva exclusivamente la región espacial común donde ambas formas se superponen.
   * **`union` (`Unión A ∪ B`):** Fusiona ambas geometrías en un único contorno unificado, eliminando líneas divisorias internas.
   * **`xor` (`XOR / Diferencia Simétrica`):** Emite las áreas pertenecientes a A o a B, pero excluyendo la zona donde se intersectan.
   * **`offset` (`Offset / Dilatación perimetral`):** Expande ($\Delta > 0$) o contrae ($\Delta < 0$) el contorno de `Shape A` según la distancia en píxeles configurada en `Delta (px)` con control de uniones y remates.
   * **`minkowski_sum` (`Suma de Minkowski A ⊕ B`):** Desliza y extiende el contorno patrón de `Shape B` a lo largo de todo el perímetro de `Shape A`.
   * **`minkowski_diff` (`Diferencia de Minkowski`):** Calcula la diferencia morfológica entre los contornos de ambas formas.

---

### 10.2. Puertos de Entrada y Controles de Configuración Dinámica
1. **`[2.1] Shape A (Subject)`:** Forma vectorial principal o sujeto sobre el que se aplica la operación booleana o morfológica. Si se omite, toma la geometría activa del contexto.
2. **`[2.2] Shape B (Clip)`:** Forma vectorial secundaria que actúa como máscara de corte, patrón de Minkowski o segundo operando.
3. **`[2.3] Subj Fill:` (`subj_fill`):** Botón cíclico de regla de relleno y devanado para la forma sujeto A (`EvenOdd`, `NonZero`, `Positive`, `Negative`).
4. **`[2.4] Clip Fill:` (`clip_fill`):** Botón cíclico de regla de relleno y devanado para la forma de corte B (`EvenOdd`, `NonZero`, `Positive`, `Negative`).
5. **`[2.5] Delta (px):` (`delta`):** Desplazamiento radial en píxeles para el modo `offset` (soporta valores positivos para dilatación, negativos para erosión y expresiones dinámicas).
6. **`[2.6] Join Mode:` (`join_type`):** Botón cíclico de estilo de unión de esquinas en modo offset (`Round` redondeado, `Miter` inglete, `Square` cuadrado, `Bevel` biselado).
7. **`[2.7] End Mode:` (`end_type`):** Botón cíclico de remate de extremos para trazados abiertos o cerrados (`Closed Polygon`, `Closed Line`, `Open Round`, `Open Square`, `Open Butt`).
8. **`[2.8] Miter Limit:` (`miter_limit`):** Límite de inglete máximo antes de biselar esquinas agudas (default: `2.0`).
9. **`[2.9] Post-Offset:` (`post_offset`):** Desfase o dilatación/contracción perimetral secundaria aplicada sobre la silueta resultante tras la operación booleana (`difference`, `intersection`, `union`, `xor`, `minkowski`). Permite expandir ($\text{px} > 0$) o contraer ($\text{px} < 0$) el resultado del corte sin requerir encadenar un segundo nodo Clipper (admite expresiones matemáticas; si se deja vacío o en `0.0`, no aplica post-offset).
10. **`[2.10] Clean Dist:` (`clean_dist`):** Distancia umbral en píxeles para limpieza y simplificación de micro-vértices colineales o degenerados mediante `CleanPolygons` ($0.0 = \text{desactivado}$).
11. **`[2.11] Simple:` (`strictly_simple`):** Botón conmutador booleano (`FALSE` / `TRUE`). Garantiza polígonos estrictamente simples sin auto-intersecciones o vértices coincidentes.
12. **`[2.12] Rev Subj:` (`reverse_subj`):** Botón conmutador booleano (`FALSE` / `TRUE`). Invierte el sentido de devanado de la forma sujeto.
13. **`[2.13] Rev Clip:` (`reverse_clip`):** Botón conmutador booleano (`FALSE` / `TRUE`). Invierte el sentido de devanado de la forma de corte.
14. **`[2.14] Anchor:` (`anchor`):** Selector desplegable de anclaje geométrico (`center`, `origin`, `relative`, `absolute`). En modo `relative` preserva el origen espacial sin recentrar a los extremos de la tinta.
15. **`[2.15] Out Mode:` (`out_mode`):** Botón cíclico de formato de salida devuelto (`Shape` código ASSdraw plano, `Clip` etiqueta `\clip(...)`, `iClip` etiqueta `\iclip(...)`).

---

### 10.3. Puertos de Salida (*Outputs*)
1. **`[1.1] Shape Out`:** Emite el código ASSdraw resultante o la etiqueta formateada `{\clip(...)}` / `{\iclip(...)}`.
2. **`[1.2] Out List`:** Emite la lista de piezas o islas resultantes en formato estructurado para encadenamiento o procesamiento por bucles.
3. **`[1.3] BBox Data`:** Emite el diccionario con las métricas espaciales del cuadro delimitador (`x1`, `y1`, `x2`, `y2`, `cx`, `cy`, `w`, `h`).

---

### 10.4. Ejemplo Práctico de Producción
* **Troquelado Booleano Negativo con Desfase Perimetral:**
  Sustrayendo un patrón de estrella (`Shape B`) del glifo tipográfico de la sílaba (`Shape A`) en modo `difference` con post-offset de dilatación:

  ```
  [System/Input: Syl Shape] ──► Shape A (Subject) ──┐
                                                    ├──► [Shape/Clipper: difference, Post-Offset=1.5]
  [Shape/Library: star] ────► Shape B (Clip) ─────┘          └──► Shape Out ──► Return ──► [System/Output]
  ```

  En un nodo de etiquetas conectado a `System/Output (Tags)`:
  ```
  {\p1\pos(syl.center, syl.middle)\1c&HFFFFFF&\bord2\3c&HFF0055&}
  ```
  Genera una silueta troquelada donde la estrella queda perforada sobre el cuerpo tipográfico, con un margen perimetral expandido de 1.5 px.

---

## 11. Nodo `Shape/Array` (Distribución Espacial, Matrices y Formaciones Vectoriales)

* **Categoría Canónica:** `Shape` (UI: *Shape / Array*)
* **Propósito:** Multiplica y distribuye geométricamente instancias de una forma o partícula en matrices regulares, mallas hexagonales, anillos concéntricos, espirales paramétricas, dispersiones aleatorias o lattices basados en siluetas. Admite ejecución iterativa línea por línea (`LOOPS`) o ensamblado monolítico en un único trazo unificado (`SHAPE`).

![Shape/Array](img/array.png)

### 11.1. Encabezado y Botones Dobles de la Barra de Título
1. **`[1.1] Array`:** Título identificador del nodo.
2. **`[1.2] Modo de Salida / Ejecución` (`out_mode`):** Botón selector primario que define la estrategia de emisión de los elementos:
   * **`[LOOPS]` (Modo Iterador / Bucle):** El nodo actúa como un generador que itera elemento por elemento a través de las variables de contexto `a_i` (índice actual) y `a_n` (total de elementos). En cada ciclo de evaluación emite una única partícula en el puerto `Piece` ubicada en sus coordenadas individuales de pantalla (`\pos(x,y)`), exponiendo su ángulo de inclinación `\frz`, columna, fila o anillo. El pie del nodo muestra `a_i, a_n`.
   * **`[SHAPE]` (Modo Forma Monolítica Unificada):** Ensambla y fusiona todas las instancias del arreglo en una **única cadena de dibujo ASSdraw continua** (`m ... l ... b ... m ...`), renombrando el primer puerto de salida a `Shape Out`. Si se conecta una lista de etiquetas al puerto `Tags`, ejecuta una fusión vectorial intercalando bloques de estilos (`{\tags1}m... {\tags2}m...`). En este modo no se generan líneas duplicadas en el archivo ASS, fijando `a_i = 1`, `a_n = 1` y mostrando `Single shape.` (*Un solo shape.*) en el pie del nodo.
3. **`[1.3] Modo de Formación Geométrica` (`mode`):** Botón selector secundario que conmuta entre las 6 topologías espaciales de distribución:
   * **`[GRID]` (Rejilla Ortogonal):** Matriz bidimensional regular de columnas $\times$ filas con control independiente de espaciado en $X$ e $Y$.
   * **`[FORM]` (Lattice sobre Silueta Guía):** Distribuye partículas sobre los vértices o el relleno de una forma/texto vectorial externo.
   * **`[RINGS]` (Anillos Concéntricos Radiales):** Formaciones circulares concéntricas con paso de radio y rotación angular por anillo.
   * **`[SPIRAL]` (Espiral Paramétrica):** Distribución continua a lo largo de una espiral con control de vueltas y radio máximo.
   * **`[SCATTER]` (Dispersión Estocástica / Aleatoria):** Nube de partículas pseudoaleatoria delimitada en un área rectangular con semilla reproducible.
   * **`[HEX]` (Panal de Abeja / Rejilla Hexagonal):** Matriz hexagonal con filas impares desplazadas a $60^\circ$ ($\Delta y = \Delta x \cdot \frac{\sqrt{3}}{2}$).

---

### 11.2. Parámetros Universales (Comunes a Todos los Modos)
1. **`[2.1] Particle`:** Código ASSdraw de la forma base o partícula a replicar (ej. un círculo, estrella, diamante, polígono o fragmento vectorial).
2. **`[2.6] Scale`:** Factor multiplicador de escala aplicado a cada partícula individual ($1.0 = 100\%$).
3. **`[2.7] Factor (t)` (`t` / `progress`):** Factor de progresión o visibilidad ($0.0 \to 1.0$). Controla la cantidad efectiva de partículas generadas/visibles en función del ordenamiento espacial:
   $$\text{Visibles} = \text{round}(\text{Total} \cdot t)$$
   Permite animar la aparición secuencial o construcción progresiva de la formación completa.
4. **`[2.8] Anchor` (Sistema de Anclaje y Origen Inyectado):**
   * **`Piece` (`Piezas`):** Centra cada partícula en su propio centroide local e inyecta `\pos(x_i, y_i)` y `\org(x_i, y_i)` correspondientes a la posición absoluta de esa celda en pantalla.
   * **`Relativo`:** Mantiene las partículas dibujadas con respecto al centroide del padre (`parent_x, parent_y`) sin alterar las coordenadas base de la línea.
   * **`Parent Org` (`Org Padre` — `parent_org`):** Sitúa el origen vectorial `\org` en las coordenadas centrales del texto o sílaba padre, permitiendo rotaciones globales centradas en la palabra mientras las piezas están dispersas.
   * **`Pos`:** Inyecta exclusivamente `\pos(x_i, y_i)` desactivando la sobreescritura de `\org`.
   * **`Absoluto`:** Proyecta las coordenadas directamente en el espacio absoluto del lienzo fijando `\pos(0,0)`.
5. **`[2.9] Order:` (Criterio de Ordenamiento Espacial):** Regula el orden secuencial de los índices $a\_i = 1 \dots N$ y la secuencia de aparición al animar `Factor (t)`:
   * **Teclado numérico:** `79 (TL->BR)` (Izquierda a Derecha, Arriba a Abajo), `97` (Derecha a Izquierda, Arriba a Abajo), `13` (Izquierda a Derecha, Abajo a Arriba), `31` (Derecha a Izquierda, Abajo a Arriba), `71` (Vertical descendente por columnas), `17` (Vertical ascendente por columnas).
   * **Centro y Radiales:** `5` (Expansión desde el centroide hacia los bordes), `cw` (Sentido horario), `ccw` (Sentido antihorario).
6. **`[2.10] Tags`:** Cadena de etiquetas ASS o colores a fusionar cuando se utiliza `out_mode = Shape` o a evaluar por instancia.
7. **`[2.11] a_i, a_n`:** Variables de iteración expuestas en el pie del nodo (`a_i` = índice del elemento actual $[1 \dots N]$, `a_n` = total de elementos calculados en la formación).

---

### 11.3. Entradas Dinámicas Específicas por Modo de Formación

#### 1. Modo `[GRID]` (Rejilla Matricial $Cols \times Rows$)
* **`[2.2] Cols`:** Cantidad de columnas horizontales (default: `5`).
* **`[2.3] Rows`:** Cantidad de filas verticales (default: `3`).
* **`[2.4] Spacing X`:** Espacio horizontal en píxeles entre los centros de celdas contiguas (default: `0`).
* **`[2.5] Spacing Y`:** Espacio vertical en píxeles entre los centros de filas contiguas (default: `0`).

#### 2. Modo `[FORM]` (Lattice sobre Silueta Guía)
* **`[2.2] Formation`:** Código de dibujo ASSdraw o texto guía que sirve de matriz o silueta base sobre la cual se muestrean y posicionan las partículas.
* **`[2.3] Spacing`:** Separación perimetral o paso de muestreo entre partículas adyacentes.

#### 3. Modo `[RINGS]` (Anillos Concéntricos Radiales)
* **`[2.2] Rings`:** Cantidad total de capas o anillos circulares concéntricos (default: `3`).
* **`[2.3] Count / Ring`:** Cantidad de partículas por anillo. Puede especificarse como un valor numérico único (ej. `8`) o como una lista separada por comas para definir densidades crecientes por capa (ej. `6, 12, 18, 24`). Si se deja vacío, el nodo calcula automáticamente la cantidad óptima según el perímetro de cada anillo:
  $$N_k = \text{round}\left(\frac{2 \pi \cdot R_k}{\text{Diámetro} + \text{Spacing}}\right)$$
* **`[2.4] Radius`:** Radio del primer anillo interior en píxeles (default: `50.0`).
* **`[2.5] Radius Step`:** Incremento de distancia radial entre anillos consecutivos (default: `30.0`).
* **`[2.5b] Rotate Step`:** Desfase angular en grados aplicado a cada anillo sucesivo para crear patrones entrelazados o espiralados (default: `0.0`).

#### 4. Modo `[SPIRAL]` (Espiral Continua Paramétrica)
* **`[2.2] Count`:** Cantidad total de partículas a distribuir a lo largo de la espiral (default: `20`).
* **`[2.3] Turns`:** Número de revoluciones o vueltas completas de $360^\circ$ (default: `2.0`).
* **`[2.4] Max Radius`:** Radio exterior máximo alcanzado en el extremo final de la espiral (default: `100.0`).
* **`[2.5] Angle Step`:** Incremento angular fijo en grados entre partículas consecutivas. Si se establece en `0`, el nodo calcula el ángulo uniformemente en función de las vueltas totales:
  $$\theta_i = t_i \cdot \text{Turns} \cdot 360^\circ \quad \text{donde} \quad t_i = \frac{i}{N - 1}$$

#### 5. Modo `[SCATTER]` (Dispersión Aleatoria Delimitada)
* **`[2.2] Count`:** Cantidad total de partículas aleatorias (default: `20`).
* **`[2.3] Width` (`area_width`):** Ancho del área rectangular de dispersión en píxeles (default: `150.0`).
* **`[2.4] Height` (`area_height`):** Alto del área rectangular de dispersión en píxeles (default: `100.0`).
* **`[2.5] Seed`:** Semilla numérica pseudoaleatoria determinista. Garantiza que la misma semilla genere exactamente la misma distribución en cada fotograma.

#### 6. Modo `[HEX]` (Rejilla Hexagonal / Panal de Abeja)
* **`[2.2] Cols`:** Cantidad de columnas (default: `5`).
* **`[2.3] Rows`:** Cantidad de filas (default: `3`).
* **`[2.4] Spacing`:** Margen de separación adicional entre celdas hexagonales.

---

### 11.4. Puertos de Salida (*Outputs*)
1. **`[3.1] Piece` / `Shape Out`:** Trazado vectorial ASSdraw emitido:
   * En `[LOOPS]`: Etiquetado como **`Piece`**, emite el código ASSdraw de la partícula individual correspondiente a la iteración $a\_i$.
   * En `[SHAPE]`: Etiquetado como **`Shape Out`**, emite el trazado monolítico compuesto con todas las partículas posicionadas y fusionadas.
2. **`[3.2] \pos Tag`:** Etiqueta ASS `\pos(x, y)` calculada para la partícula actual.
3. **`[3.3] X`:** Coordenada cartesiana $X$ absoluta en píxeles de la partícula actual.
4. **`[3.4] Y`:** Coordenada cartesiana $Y$ absoluta en píxeles de la partícula actual.
5. **`[3.5] Angle (\frz)`:** Ángulo tangencial o rotación en grados ($\theta$) de la partícula en su ubicación espacial (útil para orientar flechas o estrellas orientadas radialmente en `Rings` o `Spiral`).
6. **`[3.6] Index (a_i)`:** Índice numérico del elemento actual ($1 \dots a\_n$).
7. **`[3.7] Total (a_n)`:** Cantidad total de partículas generadas en la formación.
8. **`[3.8] Col / Ring`:** Índice de la columna activa (en `Grid` / `Hex`) o número de anillo concéntrico actual (en `Rings`).
9. **`[3.9] Row / IdxRing`:** Índice de la fila activa (en `Grid` / `Hex`) o posición del elemento dentro de su anillo (en `Rings`).

### 11.5. Ejemplo Práctico de Producción
* **Constelación Circular de Partículas Radiales:**
  Generando una formación de 12 estrellas en anillo concéntrico alrededor de la sílaba con rotación tangencial continua (`mode: rings, out_mode: loops, rings: 1, count: 12, radius: 45`):

  ```
  [Shape/Library: star] ──► Particle ──► [Shape/Array: rings, count=12, r=45]
                                               ├──► Piece ──► Return ──► [System/Output]
                                               ├──► \pos Tag ──► Tags ──► [System/Output]
                                               └──► Angle (\frz) ──► (angle)
  ```

  En un nodo de etiquetas conectado a `System/Output (Tags)`:
  ```
  {\p1\pos(x, y)\frz(angle)\1c&H00FFFF&\bord0\t(0, 300, \fscx150\fscy150\1c&HFF0088&)}
  ```
  Cada una de las 12 estrellas se posiciona en el perímetro circular y se orienta automáticamente apuntando hacia el exterior mediante el ángulo tangencial calculado.

---

## 12. Nodo `Shape/IMG to Shape` (Vectorización de Imágenes y Animaciones GIF)

* **Categoría Canónica:** `Shape` (UI: *Shape / IMG to Shape*)
* **Propósito:** Vectoriza imágenes rasterizadas (PNG, JPG, WebP) o secuencias de animaciones GIF convirtiéndolas en trazados vectoriales ASSdraw (`m`, `l`, `b`) mediante el motor integrado Potrace, aproximación poligonal (Douglas-Peucker) o extracción perimetral por gradiente.

![Shape/IMG to Shape](img/img_to_shape.png)

### 12.1. Atajos de Interfaz y Navegación de Cuadros
1. **Atajo de Carga de Archivo (Doble Clic):**
   Un doble clic sobre la tarjeta de previsualización (*Preview Card*) o sobre cualquier área vacía del cuerpo del nodo abre el selector nativo de archivos del sistema operativo para cargar imágenes compatibles (`.png`, `.jpg`, `.jpeg`, `.webp`, `.gif`). La ruta seleccionada se inyecta directamente en `image_path`.
2. **Transporte de Animaciones GIF:**
   Al detectar un archivo con múltiples fotogramas (`total_frames > 1`), el nodo despliega los controles interactivos de transporte:
   * Botones de paso de cuadro `[◀]` y `[▶]`.
   * Barra horizontal de desplazamiento (*Scrubber*) para examinar la vectorización en tiempo real cuadro a cuadro.

### 12.2. Modos de Vectorización (`mode`)
1. **`potrace`:** Genera splines continuas suaves compuestas por curvas cúbicas de Bézier (`m`, `l`, `b`) mediante descomposición poligonal intermedia, cálculo de curvatura en esquinas y aproximación subpíxel.
2. **`polygon`:** Aproximación poligonal rectilínea estricta (`m`, `l`) basada en el algoritmo de Douglas-Peucker. Reduce la cantidad de vértices preservando contornos angulares nítidos.
3. **`borders`:** Detección de contornos perimetrales basada en gradiente de luminancia (operador Sobel).

### 12.3. Modos de Binarización (`bin_mode`)
1. **`luminance`:** Evalúa el brillo en escala de grises de cada píxel frente al umbral `threshold` ($0 \dots 255$).
2. **`silhouette` / `alpha`:** Evalúa la opacidad del canal alfa de imágenes transparentes PNG/WebP frente al umbral.
3. **`borders`:** Binariza a partir de las derivadas del mapa de intensidad.

### 12.4. Puertos de Entrada (*Inputs*) y Propiedades
1. **`[2.1] Image Path` (`image_path`):** Ruta absoluta o relativa al archivo de imagen o animación GIF.
2. **`[2.2] Frame (j)` (`frame_idx`):** Índice ordinal del fotograma a decodificar ($1 \dots \text{Total Frames}$). Si se deja vacío o en `"1"` al cargar un GIF, el motor enlaza automáticamente con la variable de iteración `ish_i` o `j` para emitir la animación completa en bucle.
3. **`[2.3] Threshold` (`threshold`):** Nivel de corte para la binarización ($0 \dots 255$, defecto: `128`).
4. **`[2.4] Tolerance` (`tolerance`):** Factor de simplificación de vértices intermedios (defecto: `1.0`).
5. **`[2.5] Smoothing` (`alphamax`):** Parámetro de curvatura máxima en esquinas para Potrace (defecto: `1.0`).
6. **`[2.6] Optimization` (`opttoler`):** Tolerancia de optimización para la fusión de curvas Bézier (defecto: `0.2`).
7. **`[2.7] Scale Out` (`out_scale`):** Factor multiplicador de escala aplicado al trazado vectorial final (defecto: `1.0`).
8. **`[2.8] Width Out` (`out_w`) / `Height Out` (`out_h`):** Dimensiones explícitas de ajuste forzado en píxeles. Si se configuran en `0.0`, se respeta el tamaño natural.
9. **`[2.9] Offset X` (`offset_x`) / `Offset Y` (`offset_y`):** Desplazamiento cartesiano en píxeles aplicado a los vértices.
10. **`[2.10] Image Scale` (`img_scale`):** Factor de reescalado previo del mapa de bits antes del análisis vectorial.
11. **`[2.11] Binarize Mode` (`bin_mode`):** Selector del método de segmentación (`luminance`, `silhouette`, `borders`).
12. **`[2.12] Anchor` (`anchor`):** Sistema de anclaje cartesiano:
    * `center`: Centra el trazado en el origen cartesiano local `(0, 0)` según su centroide.
    * `origin`: Alinea la esquina superior izquierda a `(0, 0)`.
    * `relative`: Conserva las coordenadas relativas nativas del archivo gráfico.
    * `absolute`: Proyecta el trazado en pantalla sumando las coordenadas del contexto `(fx.pos_x, fx.pos_y)`.
13. **`invert` / `invert_img`:** Conmutadores para invertir la polaridad de primer plano/fondo o invertir los canales de la imagen antes de binarizar.

### 12.5. Puertos de Salida (*Outputs*)
1. **`[1.1] Shape Out`:** Trazado vectorial ASSdraw continuo (`m ... l ... b ...`) del fotograma procesado.
2. **`[1.2] Width`:** Anchura efectiva del dibujo vectorial resultante en píxeles.
3. **`[1.3] Height`:** Altura efectiva del dibujo vectorial resultante en píxeles.
4. **`[1.4] Points`:** Conteo total de vértices y puntos de control generados.
5. **`[1.5] Shapes Array`:** Lista de sub-islas vectoriales independientes para procesamiento por piezas.
6. **`[1.6] Total Frames`:** Conteo total de fotogramas detectados en el archivo. Inyecta `ish_n` e `ish_max` al contexto.

### 12.6. Ejemplo Práctico de Producción
* **Reproducción de GIF Animado Vectorizado Fotograma a Fotograma:**
  Encadenando `MaxLoop (fbf)` con `Shape/IMG to Shape`:
  
  ```
  [MaxLoop: fbf, step_ms=41.7] ──► Loop In ──► [System/Output]
                               ──► Counter ──► Frame (j) ──► [IMG to Shape: logo.gif] ──► Shape Out ──► Output (Return)
  ```
  
  En un nodo de etiquetas conectado a `System/Output (Tags)`:
  ```
  {\p1\pos(syl.center, syl.middle)\1c&HFFFFFF&\bord0}
  ```
  Cada fotograma de vídeo evalúa el cuadro exacto $j$ del GIF animado, emitiendo el trazado vectorial nativo sin pérdida de nitidez.

---

## 13. Nodo `Shape/Multi` (Patrones Concéntricos y Polígonos Anidados)

* **Categoría Canónica:** `Shape` (UI: *Shape / Multi*)
* **Propósito:** Generador procedural de patrones poligonales anidados, retículas concéntricas y geometrías compuestas paramétricas.

![Shape/Multi](img/multi.png)

### 13.1. Modos Procedurales de Generación (`mode`)
El nodo integra 10 algoritmos geométricos especializados:
1. **`concentric_squares`:** Cuadrados concéntricos anidados con grosor perimetral y paso configurable.
2. **`diagonal_stripes`:** Trama de franjas diagonales estilizadas acotadas dentro de una caja de ancho `width` y alto `height`.
3. **`concentric_rings`:** Anillos circulares concéntricos o basados en silueta base (`base_shape`).
4. **`polygonal_mosaic`:** Mosaico regular poligonal con número de lados (`sides`) y capas concéntricas (`n_layers`).
5. **`multi_shape_mosaic`:** Retícula modular de geometrías distribuidas con paso de traslación horizontal y vertical (`dx`, `dy`).
6. **`segmented_border`:** Marco perimetral segmentado con muescas o intervalos regulares de longitud `length`.
7. **`radial_rosette`:** Roseta circular con pétalos o segmentos angulares radiales (`parts`, `r_out`, `r_in`).
8. **`tunnel_cascade`:** Cascada geométrica en efecto túnel con escala decreciente (`size1`, `size2`), repeticiones (`loop`) y rotación progresiva (`angle`).
9. **`banner`:** Placa decorativa o cinta estilizada con terminales configurables (`tip_style`: Arrow, Fold) y pestañas laterales.
10. **`gear`:** Engranaje mecánico paramétrico con dientes (`teeth`), radio exterior (`r_out`), radio interior (`r_in`) y orificio central (`r_hole`).

### 13.2. Puertos de Entrada (*Inputs*) y Propiedades
1. **`Mode` (`mode`):** Selector del algoritmo procedural activo.
2. **`Size` (`size`):** Dimensión base del patrón exterior (default: `100.0`).
3. **`Px Pattern` (`px_pattern`):** Patrón secuencial de grosores o separaciones (admite valores numéricos o listas separadas por comas).
4. **`Separation` (`separation`):** Distancia de separación o espaciado entre capas o elementos adyacentes.
5. **`Factor (t)` (`t`):** Progresión temporal ($0.0 \to 1.0$) para animar la aparición secuencial o escala de las capas.
6. **`Anchor` (`anchor`):** Sistema de anclaje de referencia espacial:
   * **`center`:** Centra el conjunto de la forma generada en el origen cartesiano `(0, 0)`.
   * **`origin`:** Alinea la esquina superior izquierda de la caja delimitadora en `(0, 0)`.
   * **`relative`:** Conserva el desplazamiento relativo al padre sin recentrar.
   * **`absolute`:** Posiciona la forma directamente en las coordenadas absolutas de pantalla `(fx.pos_x, fx.pos_y)`.
7. **`Tags` (`tags`):** Cadena de etiquetas ASS o colores a intercalar en el código vectorial emitido.
8. **`Out Mode` (`out_mode`):** Formato devuelto (`Shape`, `\clip`, `\iclip`).
9. **`Loop Mode` (`loop_mode`):** Conmuta entre emisión monolítica unificada (`Shape`) e iteración pieza por pieza (`Loops`, exponiendo las variables de contexto `m_i` y `m_n`).

### 13.3. Puertos de Salida (*Outputs*)
1. **`[3.1] Shape`:** Código de dibujo vectorial ASSdraw compuesto resultante (o pieza activa en modo `Loops`).

### 13.4. Ejemplo Práctico de Producción
* **Estandarte Decorativo Detrás del Título:**
  Configurando `Shape/Multi` en `mode: banner`, `width: 260`, `height: 48`, `anchor: center`:

  ```
  [Shape/Multi: banner, w=260, h=48] ──► Shape ──► Return ──► [System/Output]
  ```

  En un nodo de etiquetas conectado a `System/Output (Tags)` con capa inferior (`layer: 0`):
  ```
  {\p1\pos(line.center, line.middle)\1c&H1A1A2E&\bord2\3c&HE94560&}
  ```
  Dibuja un estandarte poligonal centrado en el medio de la línea de diálogo actuando como placa de fondo estilizada.
