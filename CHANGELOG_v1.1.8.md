# Pyxis Effector v1.1.8 — Notas de la Versión

Notas de la versión correspondientes al ciclo **v1.1.8 (Beta)** de Pyxis Effector. Esta entrega introduce el ensamblador monolínea universal `Basics/Builder`, el nuevo modo `Shadtrick` en `Functions/Move Tag`, el anclaje `Relative2` sin `\org`, renueva integralmente `Basics/Math` bajo el estándar `ke.math`, amplía `Audio/Waveform` con control de anclaje y suavizado, mejora la preservación de etiquetas y propiedades originales de línea, y optimiza de forma sustancial la agilidad del Previsualizador.

---

### Destacados

* **Nuevo Ensamblador Universal `Basics/Builder`:** Compila fragmentos de texto o piezas vectoriales complejas en una única línea ASS continua con barreras de reinicio `\r` opcionales, preservación topológica de huecos interiores, entradas expandibles y sub-bucle propio (`bu_i`, `bu_n`, `max_bu`).
* **Modo `Shadtrick` y `Points` Simplificado en `Functions/Move Tag`:** Traslada piezas vectoriales de forma independiente dentro de una misma línea ASS (ideal junto a `Basics/Builder`) animando `\xshad` y `\yshad`, con listas planas `x1, y1, x2, y2...` y evaluación directa de variables y fórmulas.
* **Nuevo Anchor `Relative2` (`Relativo2`):** Conserva intacta la geometría relativa de cada pieza sin inyectar `\org`, disponible en todos los nodos de fragmentación y partículas.
* **Renovación Integral de `Basics/Math`:** Reconstrucción completa con 5 categorías (`basic` expandible, `numeric`, `sequence`, `geometry`, `algebra`, `data`) y 27 operaciones alineadas al módulo clásico `ke.math`.
* **Previsualizador Más Ágil y Fluido:** Cambio de fuente instantáneo entre plantilla base y proyecto de Aegisub mediante carga directa al instante de inicio, precalentamiento en segundo plano, transición animada de relación de aspecto y pantalla de carga mantenida hasta decodificar el primer fotograma real.
* **Preservación de Tags y Variables Originales de Línea:** Soporte nativo para heredar etiquetas cinéticas desde Aegisub en `Loops/Main Loop`, consultar propiedades originales por línea (`line.<prop>_org`) y utilizar toda la familia de Dark Tags desde `Basics/MultiTag`.

---

### Nuevas Funcionalidades

* **Nodo `Basics/Builder`:**
  * Modos `text` (`splitter`, `multi`, `custom`) y `shape` (`subpaths`, `islands`, `raw_subpaths`) con diseños espaciales `auto`, `embedded_pos`, `advance` y `stack`.
  * Entradas ampliables dinámicamente (`In1`, `In2`...) con botones `+` / `-`, puerto `Tags` dedicado con prioridad de estilo y control `Reset \r` para conservar animaciones `\t` entre segmentos.
* **Modo `Shadtrick` en `Functions/Move Tag`:**
  * Oculta relleno y borde (`\1a&HFF&\3a&HFF&\ko0`) para desplazar cada bloque mediante `\xshad` y `\yshad` y transiciones `\t(...)`, preservando hasta 3 decimales (`0.001` como mínimo de reposo) y respetando el color de sombra configurado externamente (`\4c`).
  * Emite únicamente las transiciones directas entre los puntos indicados (`N - 1` transformaciones `\t(...)` para `N` puntos) sin subdivisiones intermedias innecesarias, aprovechando la interpolación nativa de cada segmento.
  * No emite `\shad`, `\pos`, `\fscx`/`\fscy` ni espaciadores `\p1...\p0`, evitando colisiones dentro de `Basics/Builder`.
  * Interfaz depurada por modo: `Shadtrick` muestra únicamente sus campos activos (sin `Amplitude X`, `Amplitude Y` ni `Step (px)`), usando `0.001, 0.001` como base si `Points` queda vacío.
* **Nuevo Anclaje `Relative2` (`Relativo2`):**
  * Disponible en `Shape/Slicer`, `Shape/Array`, `Shape/Union & Divide`, `Shape/Concentric Borders` y `Functions/Particles`.
  * Mantiene la posición y geometría relativas respecto al elemento padre igual que `Relative`, pero omite la inyección automática de `\org` para no fijar el pivote de rotación o escala en el centro padre.
* **Renovación de `Basics/Math`:**
  * Nueva categoría principal `basic` (por defecto al instanciar el nodo) con puertos expandibles y 9 operaciones aritméticas/reductoras (`add`, `sub`, `mul`, `div`, `mod`, `pow`, `min`, `max`, `avg`).
  * Categorías especializadas `numeric`, `sequence`, `geometry`, `algebra` y `data` con botones cíclicos y casillas nativas.
* **Controles `Anchor` y `Smoothing` en `Audio/Waveform`:**
  * Nuevo botón cíclico **Anchor** (`Center`, `Origin`, `Relative`, `Absolute`) con `"center"` como valor por defecto, desplazando de forma unificada la geometría y los arreglos de coordenadas respecto al recuadro de la onda.
  * Nuevo campo **Smoothing** (`0.0` a `0.95`, defecto `"0.2"`) con filtro exponencial paso bajo para suavizar saltos bruscos entre muestras y bandas espectrales en todos los modos.
* **Preservación de Tags y Propiedades Originales:**
  * Opción **Preserve Tags** en `Loops/Main Loop` para transferir etiquetas estáticas y cinéticas (`\move`, `\t`, `\fad`, `\fade`) con remapeo temporal exacto al intervalo del efecto.
  * Acceso directo en scripts y expresiones a `line.<prop>_org` / `l.<prop>_org` y sintaxis Dark Tag `!line.<prop>!`.
* **Catálogo Completo de Dark Tags en `Basics/MultiTag`:** Integración de todas las familias de Dark Tags (etiquetas compuestas, auto-origen 3D, restauración de estilo, ratios y estocásticos `*R`) con apertura directa del selector modal desde la cabecera.
* **Recortes Rectangulares Automáticos (`\clip` / `\iclip`):** Los nodos de formas y recortes emiten automáticamente la forma compacta `\clip(x1,y1,x2,y2)` cuando la geometría resultante es un rectángulo alineado a los ejes, optimizando el renderizado final.

---

### Mejoras de Flujo y Ergonomía

* **Sintaxis Plana en `Points` (`x1, y1, x2, y2...`) con Variables y Fórmulas:** En `Functions/Move Tag` (`Waypoints` y `Shadtrick`), la entrada `Points` ahora se escribe como una lista simple separada por comas y evalúa directamente variables y expresiones del contexto (compatible con `Basics/Dynamic Format` y `Variables/Define Vars`).
* **Aislamiento de Llamadas Aleatorias y Agrupación por Variable:** Cada invocación de `R(...)` o `by.<iter>.R*(...)` en una expresión (incluso varias en la misma línea, como `R(10) + R(10) + R(10)`) o en variables distintas se calcula de forma independiente; solo almacenar el resultado en una variable conserva el mismo valor dentro de esa iteración.
* **Transición de Fuentes y Seeking en `System/Previewer`:**
  * Eliminación del salto doble al cambiar de fuente, manteniendo el indicador difuso de carga hasta que el primer fotograma esté listo para mostrarse sin fotogramas grises residuales.
  * Transición animada suave de relación de aspecto al alternar en ambas direcciones entre la plantilla base y Aegisub.
  * Arrastre de la barra de búsqueda (*seeking*) fluido sin congelamiento de imagen ni subtítulos, y barra superior adaptable en ventanas compactas.
  * Cálculo preciso de la ventana reproducible `±2 s` excluyendo líneas vacías o sin contenido visible, junto con manejo unificado de ámbitos (`Sel. Lines`, `All Lines`, `Style Lines`) en `System/Output`.
* **Aceleración en macOS (Apple Silicon):** Caché de índices tipográficos en disco, optimización de métricas de fuentes y cálculo lineal de texto para arranques y previsualizaciones mucho más veloces.
* **Scripting, Expresiones y Diagnóstico:**
  * Evaluación y validación unificadas de expresiones ternarias y etiquetas ASS con o sin comillas en `Variables/Define Vars` y `Basics/String`.
  * Actualización dinámica inmediata de `fx.start_time`, `fx.end_time` y `fx.dur` tras modificar `st`/`et` en `System/Script Code` (Python y Lua), con aislamiento estricto entre múltiples ramas `System/Output`.
  * Autocompletado y validador sincronizados con los 69 nodos del sistema y calibración fiel del indicador de carga de trabajo según la telemetría real.

---

### Correcciones de Errores

* **Aleatoriedad `by.bu_i` en `Basics/Builder` y Variables Independientes:** Resuelto el fallo donde `by.bu_i.R*(...)` repetía el mismo valor en todas las piezas de `Basics/Builder` al declararse previamente en `Variables/Define Vars`, así como el conflicto donde dos variables diferentes con la misma expresión aleatoria devolvían resultados idénticos.
* **Posicionamiento con `Preserve Tags` y `\move`:** Resuelto el problema por el cual heredar el `\pos` original de la línea junto a un `\move` generado por el grafo anulaba el desplazamiento y colapsaba las formas en la posición base.
* **Cuantización Temporal en Centisegundos ASS:** Unificado el redondeo temporal entre los tiempos `Start`/`End` exportados y el remapeo cinético de `\move`, `\fad` y `\t`, eliminando saltos alternados de un fotograma en efectos paso a paso o FBF.
* **Lienzo y Controles de Nodos:**
  * Eliminados los círculos amarillos residuales en el lienzo tras soltar cables de conexión.
  * Corregido el cálculo de ancho dinámico al cambiar de modo en `Basics/Math`, evitando recortes o desalineaciones antes del primer redibujado.
  * Solucionado el desfase de índice en la previsualización de muestras de `Basics/Color Picker` hacia `Basics/MultiTag` y preservada la distinción de mayúsculas en tags estocásticos `*R`.
* **Persistencia y Renderizado del Previsualizador:**
  * Corregidos los casos en que `System/Previewer` perdía su relación de aspecto, su estado desacoplado o quedaba oculto al recargar una plantilla o iniciar la sesión.
  * Restaurada la estabilidad de renderizado en Windows y Linux y actualizada la resolución automática de descarga de FFmpeg.
* **Geometría y Ordenamiento 2D:**
  * Preservados los órdenes no numéricos (`cw`, `ccw`, `rand`) en `Shape/Slicer`, restringidas las opciones `path`/`path_inv` únicamente a nodos con trazado guía, unificadas las propiedades `Bleed` y `Pre-Offset` en los 23 modos de `Slicer`, y corregida la curva de retorno en cortes tipo rompecabezas (`jigsaw`).

---

### Avisos de Compatibilidad y Migración

> [!NOTE]
> * **Consolidación en `Basics/Builder`:** Se retiraron el modo `merge` de `Basics/Concatenate` (conservando `basic` y `zip` con selector de separador independiente) y el modo `Fusion Tags` de `Shape/Union & Divide`. Los flujos de composición monolínea ahora se construyen de forma unificada en `Basics/Builder`.
> * **`Functions/Move Tag` (`Points`):** Se retiró la sintaxis anterior con punto y coma (`;`) y saltos de línea en `Points` en favor del formato plano separado por comas (`x1, y1, x2, y2...`).
> * **`Audio/Waveform`:** La propiedad `Anchor` pasa a tener `"center"` como valor por defecto y `Smoothing` inicia en `"0.2"`.
> * **`Basics/Math`:** Las plantillas que empleaban modos anteriores deben actualizar sus operaciones al nuevo catálogo de 5 categorías y 27 operaciones compatibles con `ke.math`.
