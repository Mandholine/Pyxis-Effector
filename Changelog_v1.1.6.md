# Historial de Cambios — Pyxis Effector

Registro público de versiones y notas de lanzamiento de Pyxis Effector para la comunidad de creadores de karaoke, editores de Aegisub y diseñadores de tipografía cinética.

---

## Pyxis Effector v1.1.6 — Previsualizadores Interactivos, Portabilidad en AppData y Precisión Geométrica

Notas de la versión completa **v1.1.6** de Pyxis Effector, consolidando las innovaciones introducidas desde la versión 1.1.5 original y su ciclo de optimización.

### Destacados
Esta versión representa una de las mayores transformaciones ergonómicas y arquitectónicas de Pyxis Effector. Se incorporan visores interactivos nativos con zoom y desplazamiento dentro de los nodos visuales, se introduce un reproductor de animación vectorial en tiempo real, se garantiza la instalación limpia sin permisos de administrador en la carpeta de usuario de Aegisub (`%APPDATA%`), y se expande el soporte universal de expresiones matemáticas junto con aceleraciones de hasta un 90% en transformaciones geométricas complejas.

---

### Novedades y Nuevas Funcionalidades

#### 1. Previsualizadores Interactivos Integrados en Nodos
* **Nuevo Reproductor de Animación en el Nodo (`Functions/Animation`):**
  * Se implementó un reproductor vectorial dinámico integrado en el cuerpo del propio nodo.
  * Incluye controles de transporte en tiempo real: botón interactivo de *Play / Pause*, navegación paso a paso cuadro a cuadro, indicador del fotograma activo (`cuadro / total`) y barra de deslizamiento temporal (*scrubber*).
  * Soporta detección automática de cuadros vectoriales a partir de nodos upstream conectados (como secuencias de imágenes y GIFs animados vectorizados desde `IMG to Shape`), listas de trazados ASSdraw o glifos tipográficos.
* **Rediseño Integral de Visores de Imagen (`Shape/IMG to Shape` e `IMG to pixels`):**
  * **Renderizado Directo en Canvas:** Se eliminó la antigua superposición de elementos HTML/SVG externos, migrando a dibujo acelerado nativo en el lienzo. Esto elimina cualquier desfase visual o parpadeo al desplazarse o hacer zoom por el grafo.
  * **Zoom y Desplazamiento Focalizado:** Es posible hacer zoom con la rueda del ratón directamente sobre la tarjeta del visor (centrado exactamente en el cursor), arrastrar la imagen con el botón del ratón (*pan*) y reajustar la vista original con doble clic.
  * **Barra de Navegación de Secuencias:** Cabecera interactiva con botones previo/siguiente y barra de seguimiento para examinar fotogramas en animaciones y GIFs.
  * **Selectores de Modo Visual:** Alternancia en un clic entre vistas *Overlay* (superposición), *Image* (imagen pura), *Vector* (trazado resultante) y *Pixels* (matriz de partículas).
  * **Diagnóstico de Rutas:** Animación visual de alerta en caso de rutas de archivo inexistentes o imágenes dañadas.

#### 2. Soporte e Instalación Autónoma en Espacio de Usuario
* **Instalación sin Privilegios de Administrador:** Pyxis Effector ahora opera de forma 100% nativa cuando se instala en la carpeta de automatización de usuario de Aegisub:
  ```
  %APPDATA%\Aegisub\automation\autoload\PyxisNodes\
  ```
* **Auto-Desbloqueo de Seguridad de Windows (MOTW):** El motor detecta y elimina automáticamente la marca de procedencia de Internet (*Mark of the Web* / flujos `:Zone.Identifier`) en librerías nativas, .NET Framework y WebView2 durante el primer arranque. Esto evita bloqueos de seguridad del sistema operativo.

#### 3. Control de Geometría y Partículas
* **Cierre Forzado de Contornos en Partículas (`Functions/Particles`):** Nueva opción **Close Path**, que permite sellar figuras o glifos abiertos antes de emitir partículas perimetrales.
* **Dispersión Determinista por Semilla (`Functions/Particles`):** Control estocástico desacoplado mediante el parámetro **Seed**, asegurando que las dispersiones aleatorias sean idénticas y reproducibles en cada renderizado.
* **Secuenciador de Orden en Patrones Procedurales (`Shape/Multi`):** Selector de orden (**Order**) en los modos *Concentric Squares*, *Diagonal Stripes*, *Concentric Rings*, *Segmented Border*, *Radial Rosette* y *Tunnel / Cascade* para animar la aparición progresiva de piezas mediante el factor temporal $t$.
* **Dispersión Radial en Arreglos (`Shape/Array`):** Nueva propiedad **Explosion** en modo *Formation*, permitiendo expandir o contraer las piezas radialmente sin alterar la escala tipográfica original.

---

### Mejoras de Flujo y Rendimiento

* **Aceleración Geométrica de Alto Rendimiento:** Memoización y optimización de operaciones booleanas de corte y dilatación perimetral en `Shape/Multi` y `Shape/Union & Divide`, reduciendo los tiempos de reevaluación repetitiva en animaciones complejas hasta en un 90% (de ~486 ms a ~6 ms en figuras densas).
* **Soporte Universal de Fórmulas Matemáticas y Expresiones:**
  * **`Shape/Array`:** Admisión completa de fórmulas matemáticas y variables de contexto (`syl.i`, `line.dur`, variables de usuario) en todos sus parámetros numéricos (*Cols*, *Rows*, *Spacing*, *Radius*, *Scale*, etc.).
  * **`Shape/Transform` (Flexor):** Admisión de operaciones aritméticas y variables dinámicas en el parámetro de curvatura angular (*Curve / Angle*).
  * **`Shape/Concentric Borders`:** La propiedad *Separation* ahora admite operaciones matemáticas con paréntesis anidados dentro de listas separadas por comas (por ejemplo: `5, (2 * syl.i), 10`).
* **Arquitectura Web Modular y Ligera:** El frontend se reestructuró en módulos independientes organizados por categorías en `web/nodes/`, reduciendo la carga del documento principal a una fracción ligera (de 1,8 MB a 63 KB) y acelerando la respuesta general del lienzo.
* **Preservación de Trazados en Remuestreo:** El algoritmo *RedrawDist* de `Functions/Particles` ahora discretiza rectas y curvas Bézier de forma limpia y transparente, conservando esquinas vivas y contornos idénticos cuando la distancia es cero.
* **Proporciones Fieles en Marcos Segmentados:** `Shape/Multi` en modo *Segmented Border* preserva relaciones de aspecto y contornos 1:1 alrededor de formas personalizadas, evitando deformaciones anamórficas involuntarias.

---

### Correcciones de Errores

* **Alineación Tipográfica Milimétrica en Aegisub:** Resuelto el desfase vertical al superponer arreglos (`Shape/Array`) y patrones concéntricos (`Shape/Multi`) sobre texto con alineación central (`\an5`).
* **Colapso de Coordenadas en Arreglos Monolíticos:** Corregido el problema en `Shape/Array` que provocaba que las partículas se colapsaran en el punto `(0, 0)` en modos de salida unificada.
* **Propagación del Orden de Animación:** Corregido el fallo por el cual la propiedad de orden seleccionada en `Shape/Multi` no se aplicaba al motor durante el procesamiento final.
* **Integridad de Firmas en el Lienzo:** Normalizada la firma de `Shape/Array` para exponer con fidelidad sus 9 ranuras de salida canónicas y sus widgets de configuración.