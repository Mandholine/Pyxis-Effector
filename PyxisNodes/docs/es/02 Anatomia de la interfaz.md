# Anatomía de la Interfaz

La interfaz de Pyxis Effector se organiza como un espacio de trabajo modular basado en nodos, estructurado en torno a un lienzo principal de edición y paneles de control periféricos.

---

## 1. Distribución General del Espacio de Trabajo

La ventana principal de la aplicación se compone de cuatro zonas funcionales:

```
+-------------------------------------------------------------------------------+
| [1] BARRA SUPERIOR (TOP BAR)                                                  |
+-------------------------------------------------------------------------------+
|                                                                               |
|                                                                               |
| [2] LIENZO DE TRABAJO (CANVAS WORKSPACE)                                      |
|     (Nodos, puertos de conexión, cables de datos y enlaces de flujo)          |
|                                                                               |
|                                                                               |
|                                                        +----------------------+
| [3] BARRA DE HERRAMIENTAS FLOTANTE                     | [4] NOTIFICACIONES   |
+-------------------------------------------------------------------------------+
```

1. **Barra Superior (*Top Bar*):** Gestión de persistencia (guardar/exportar), biblioteca de plantillas, preferencias globales y generación de capas.
2. **Lienzo de Trabajo (*Canvas Workspace*):** Área de edición bidimensional donde se agregan, organizan e interconectan los nodos del grafo.
3. **Barra de Herramientas Flotante (*Canvas Toolbar*):** Acceso rápido para navegación, nivel de zoom, centrado de cámara y acciones de historial (*undo/redo*).
4. **Sistema de Notificaciones (*Toast System*):** Alertas contextuales no invasivas en la esquina inferior derecha con información de estado, diagnóstico y tiempos de procesamiento.

---

## 2. Barra Superior (*Top Bar*) y Control de Generación

Ubicada de forma fija en el margen superior de la ventana:

```
+-------------------------------------------------------------------------------------------------+
| [1] Marca y Versión | [2] Guardar | [3] Guardar Como | [4] Biblioteca | [5] Ajustes | [6] Generar Capas |
+-------------------------------------------------------------------------------------------------+
```

1. **Identificador de Versión:**
   * Nombre del motor y distintivo de versión activa (`v1.1.4`).

2. **Guardar (`Save` / `Ctrl+S`):**
   * Guarda los cambios directamente sobre la plantilla o archivo actualmente abierto.

3. **Guardar Como (`Save as...`):**
   * Exporta la topología completa del grafo a un archivo externo `.json` para respaldo o distribución.

4. **Biblioteca de Plantillas (`Library`):**
   * Despliega la ventana modal para buscar, etiquetar, categorizar y cargar plantillas predefinidas o creadas por el usuario. Permite filtrado por Favoritos, Recientes y Plantillas de Sistema.

5. **Guardado Rápido de Plantilla (`Quick Save`):**
   * Se activa al editar una plantilla cargada de la biblioteca para sobrescribirla con un solo clic.

6. **Ajustes del Entorno (`Settings`):**
   * Configuración de temas visuales del lienzo, fondo (video activo de Aegisub, imagen de referencia o color sólido), preferencias de idioma y opciones de aceleración gráfica.

7. **Botón Principal de Generación de Capas (`Generate Layers`):**
   * Compila el grafo y emite las nuevas líneas de subtítulos hacia el archivo ASS de Aegisub. Muestra una barra de progreso integrada.

8. **Tarjeta de Estimación de Carga de Trabajo (*Workload Estimation Card*):**
   * Se despliega automáticamente al situar el cursor sobre **Generate Layers**:
     * **Líneas a generar:** Cantidad estimada de eventos de diálogo ASS resultantes que se escribirán en el script.
     * **Líneas de entrada:** Total de líneas de subtítulo seleccionadas en Aegisub que serán procesadas.
     * **Unidades base:** Desglose total de sílabas, palabras o caracteres según el iterador activo en `Main Loop`.
     * **Alerta de Carga Masiva:** Notificación visual preventiva si la complejidad combinada supera umbrales recomendados de tiempo de cómputo.

---

## 3. Lienzo de Trabajo (*Canvas Workspace*)

Espacio de trabajo bidimensional para la edición del grafo mediante navegación libre, escalado y selección múltiple.

### 3.1. Arquitectura de Capas Visuales (*Z-Index Stacking*)
1. **Capa de Fondo:** Fondo neutro, imagen estática o video del proyecto cargado desde Aegisub para referencia espacial.
2. **Capa Principal de Nodos (`#node_canvas`):** Renderizado de las cajas de nodos, títulos, puertos de conexión, campos de texto y widgets interactivos.
3. **Capa de Conexiones y Selección (`#node_canvas_fg`):** Renderizado de curvas de cables de conexión, marcos de selección múltiple y guías de alineación magnética.

### 3.2. Barra de Herramientas Flotante (*Canvas Toolbar*)
Situada en la esquina inferior izquierda:

1. **Deshacer (`Undo` / `Ctrl+Z`):** Revierte la última modificación en el lienzo.
2. **Rehacer (`Redo` / `Ctrl+Y`):** Restaura la última acción deshecha.
3. **Centrar Vista (`Home` / `Reset View`):** Reubica la cámara centrando todo el grafo en pantalla con un factor de zoom óptimo.
4. **Acercar Zoom (`Zoom In` / `+`):** Aumenta el nivel de ampliación focalizado en el centro de la vista.
5. **Alejar Zoom (`Zoom Out` / `-`):** Reduce el zoom para una vista panorámica del grafo completo.
6. **Cargar Grafo Predeterminado (`Default Preset`):** Restablece el lienzo a la estructura estándar inicial (`Main Loop` $\to$ `Output`).

---

## 4. Anatomía Estructural de un Nodo

Estructura estándar de las cajas de nodos en el lienzo:

```
+-------------------------------------------------------------+
| [1] CABECERA: Nombre del Nodo      [4] Selector de Modo [v] |
+-------------------------------------------------------------+
| [2] ENTRADAS Y CAMPOS INLINE          |  [3] PUERTOS SALIDA |
| (o) [ Loop In                   ]     |        Loop Out (o) |
| (o) [ 100.0 (o placeholder)     ]     |          Result (o) |
| (o) [                           ]     |        Data Out (o) |
+-------------------------------------------------------------+
| [5] BORDE DE SELECCIÓN Y ESTADO       [6] BADGE / ITERADOR  |
+-------------------------------------------------------------+
```

1. **Cabecera del Nodo:**
   * Franja identificativa con el nombre funcional del nodo y color distintivo de su categoría.
   * Permite arrastrar el nodo para reposicionarlo en el lienzo o colapsar/expandir su cuerpo mediante doble clic.

2. **Puertos de Entrada con Cajas de Texto Integradas (*Inline Input Fields*):**
   * Cada ranura de entrada en el lateral izquierdo cuenta con un conector circular `(o)` y un **campo de texto editable**.
   * **Texto de ayuda (*Placeholder*):** Cuando el campo está vacío, muestra en color tenue el nombre del parámetro y su valor predeterminado (ej. `Min`, `Max`, `Delay (ms)`).
   * **Prioridad Cable vs. Campo:** Si se escribe un valor constante o expresión en el campo, el nodo evalúa dicho valor. Si se conecta un cable al conector `(o)`, **el dato transportado por el cable toma prioridad absoluta**, ignorando el texto del campo.
   * **Excepción (`Output`):** El nodo terminal `Output` no dispone de cajas de texto inline en sus entradas; en su lugar muestra etiquetas de texto de asignación directa (`Loop / Domain`, `Layer`, `Start Time`, etc.).

3. **Puertos de Salida (*Outputs*, Lateral Derecho):**
   * Conectores circulares acompañados del nombre de la variable o dato generado (`Loop Out`, `Data`, `Result`, `Shape Out`, `\t Out`, etc.).

4. **Selectores de Modo en Cabecera (*Header Mode Combos*):**
   * Menús desplegables integrados en el extremo derecho del título.
   * Permiten alternar instantáneamente el algoritmo o comportamiento del nodo (ej. `syl / char / word / line` en `Main Loop`, `Normal / FBF` en `MaxLoop`, modos en `Manipulator` o lenguajes `Python / Lua` en `Script Code`), reconfigurando dinámicamente las entradas del cuerpo.

5. **Borde de Selección y Estado:**
   * Resaltado visual en el perímetro que indica cuándo el nodo está seleccionado o en edición activa.

6. **Badges e Información al Pie (*Footers / Badges*):**
   * Muestra las variables de iteración expuestas al contexto (`s_i, s_n` en Slicer, `a_i, a_n` en Array, `b_i, b_n` en Concentric Borders, `ish_i, ish_n` en IMG to Shape) o estados especiales del nodo (`Single shape.`, `ALL`, `SELEC.`, `NO BLANK`).

---

## 5. Clasificación de Nodos por Categoría y Código de Color

Pyxis organiza sus 67 nodos en 8 categorías funcionales identificables mediante colores temáticos:

| Categoría Canónica | Nombre en UI | Rol Funcional | Ejemplos de Nodos | Color Distintivo |
| :--- | :--- | :--- | :--- | :--- |
| **`Basics`** | `Básicos` | Constantes numéricas, cadenas, operaciones matemáticas, formateo dinámico y control simple. | `Math`, `Number`, `String`, `Text`, `Color Picker`, `MultiRandom`, `Concatenate`, `Once`, `Only` | Azul Celeste (`#4A90E2`) |
| **`Shape`** | `Shape` | Primitivas, cortes booleanos (Clipper2), trazados, transformaciones afines, deformaciones y mallas. | `Library`, `Slicer`, `Manipulator`, `Transform`, `Filter`, `Concentric Borders`, `Stroke`, `Array`, `IMG to Shape` | Verde Esmeralda (`#2ECC71`) |
| **`Time`** | `Tiempo` | Sincronización temporal, re-tiempo acelerado (`\t`), interpolación paramétrica (`Ipol`) y desfases. | `Retime`, `Lead In`, `Lead Out`, `Synced`, `Middle 1/2`, `Loop 1/2`, `Ipol`, `Duration`, `Offset` | Naranja Dorado (`#F39C12`) |
| **`Functions`** | `Funciones` | Moduladores de tags, osciladores de onda, gradientes cromáticos, splines Bézier y partículas. | `Tag Manipulator`, `Tag Oscillator`, `Color Gradient`, `Clip Gradient`, `Bezier Curve`, `Particles`, `Text to Shape` | Púrpura Violeta (`#9B59B6`) |
| **`Variables`** | `Variables` | Variables de contexto ASS, memoria persistente clave-valor y generadores de variables dinámicas. | `Sys Var`, `Define Vars`, `Get Var`, `Memory` | Turquesa (`#1ABC9C`) |
| **`Loops`** | `Bucles` | Control de dominio de descomposición, multiplicadores de eventos y pasos modulares. | `Main Loop`, `MaxLoop`, `Module` | Rojo Coral (`#E74C3C`) |
| **`Audio`** | `Audio` | Análisis espectral de audio (FFT), extracción de envolventes RMS/Peak y formas de onda vectoriales. | `Modulator`, `Waveform` | Amarillo Ámbar (`#F1C40F`) |
| **`System`** | `Sistema` | Ensamblado terminal ASS, previsualización acelerada WASM, scripts de código y pruebas de rendimiento. | `Output`, `Previewer`, `Script Code`, `Benchmark Math` | Gris Acero (`#7F8C8D`) |

---

## 6. Navegación, Gestos y Atajos de Teclado

| Acción | Control de Ratón / Teclado | Resultado |
| :--- | :--- | :--- |
| **Moverse por el lienzo (Paneo)** | Botón central del ratón (pulsar rueda) o Clic derecho y arrastre | Desplaza la cámara en cualquier dirección. |
| **Ajustar Zoom** | Rueda del ratón (*Scroll*) | Acerca o aleja la vista de forma continua. |
| **Seleccionar / Mover Nodo** | Clic izquierdo sobre cabecera y arrastre | Selecciona y reposiciona nodos individualmente. |
| **Selección Múltiple** | Clic izquierdo sostenido en fondo vacío | Traza un cuadro rectangular de selección masiva. |
| **Crear Conexión (Cable)** | Arrastre desde puerto de salida `(o)` a puerto de entrada `(o)` | Conecta dos nodos compatibles con cable elástico. |
| **Desconectar Puerto** | Clic sobre un puerto conectado | Desconecta y retira el cable enlazado. |
| **Menú Contextual de Creación** | Clic derecho en fondo vacío del lienzo | Abre el catálogo y buscador rápido de nodos. |
| **Eliminar Nodos / Cables** | Tecla `Supr` (*Delete*) o `Retroceso` (*Backspace*) | Elimina los elementos actualmente seleccionados. |
| **Duplicar Nodos** | `Ctrl + D` o `Ctrl + C` / `Ctrl + V` | Clona los nodos seleccionados preservando parámetros. |
| **Guardar Proyecto / Plantilla** | `Ctrl + S` | Guarda los cambios del grafo activo. |
| **Deshacer / Rehacer** | `Ctrl + Z` / `Ctrl + Y` | Navega por el historial de cambios del lienzo. |
| **Centrar Vista en el Grafo** | Tecla `Home` o botón en barra de herramientas | Centra todos los nodos en la ventana. |
| **Consola de Depuración Integrada** | Tecla `F1` (o `Esc` para cerrar) | Abre la consola de logs en tiempo real (operativa incluso durante la inicialización de la ventana). |

---

## 7. Ventanas Modales y Editores Especializados

1. **Editor de Código Script (`Script Code`):**
   * Entorno de edición para Python y Lua con resaltado de sintaxis, numeración de líneas y validación de errores en vivo (bloques `end` sin cerrar, dos puntos faltantes, delimitadores desparejados).
   * Gestor de plantillas reutilizables para guardar y cargar funciones frecuentes.

2. **Selector de Color (`Color Picker`):**
   * Rueda cromática HSV/RGB con ajuste de canal alfa, paletas de muestras predefinidas y exportación directa a formato ASS (`&HBBGGRR&`) y Hexadecimal (`#RRGGBB`).

3. **Consola de Depuración Integrada (`Debug Console` - `F1`):**
   * Visor de logs y diagnósticos de backend en tiempo real, accesible en cualquier momento (incluso durante la inicialización de la ventana).
   * Incluye filtrado de búsqueda en vivo, auto-scroll, copiado al portapapeles y limpieza de registros sin afectar el proceso ni las dimensiones de la ventana.

4. **Biblioteca de Plantillas (`Library`):**
   * Catálogo con búsqueda por nombre o etiquetas, previsualización de cantidad de nodos y verificación de integridad de grafo.

5. **Panel de Telemetría y Estimación de Carga (`Telemetry`):**
   * **Tooltip de Estimación Pre-Generación (`Generate Layers`):** Al situar el cursor sobre el botón de generación, muestra en tiempo real las líneas estimadas, la **Concurrencia de Líneas** (*Sweep-Line Concurrency*), el **Factor de Expansión**, el **Peso ASS Estimado** (`KB`/`MB`), identificadores de subsistemas activos (`FBF`, `Slicer`, `Particles`, `Audio`, `Script`), el resumen del último escaneo y un acceso directo a `Telemetry`.
   * **Panel Telemetry (16:9):** Diagnóstico distribuido en tres regiones: visor de vídeo con HUD de telemetría por fotograma (arriba-izquierda), tacómetro de presupuesto (`Frame Budget %`), tarjetas KPI y lista de puntos críticos (arriba-derecha), y gráfico superpuesto con minimapa y navegación 2D (`Rueda` zoom X en cursor, `Ctrl/Shift + Rueda` escala Y, `Botón Central` paneo 2D, `Clic Izquierdo` desplazamiento temporal de vídeo y `R`/`Home` para restablecer vista).
