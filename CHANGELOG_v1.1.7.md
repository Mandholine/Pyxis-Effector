# Pyxis Effector v1.1.6 — Notas de la Versión

Notas de la versión correspondientes al ciclo **v1.1.6** de Pyxis Effector. Esta entrega consolida la arquitectura multiplataforma nativa, amplía sustancialmente el rendimiento del motor de generación por nodos, renueva el sistema de previsualización interactiva con soporte para modos duales y perfecciona la precisión geométrica de los contornos vectoriales.

---

### Destacados

* **Arquitectura 100% Nativa Multiplataforma:** Soporte completo e independiente para Windows, Linux y macOS sin capas de emulación, incorporando tipografía FreeType nativa, telemetría de rendimiento optimizada y aprovisionamiento directo de herramientas multimedia.
* **Previsualización Interactiva Dual (Typesetting vs mpv):** Nuevo selector de motor visual en el nodo Previsualizador que permite alternar en tiempo real entre la fidelidad pixelar tradicional de Aegisub/VSFilter y la nitidez vectorial de alta definición de mpv con compensación anamórfica automática.
* **Aceleración Drástica de Procesamiento (OPT-01 a OPT-05):** Optimización integral del motor de grafos reduciendo en más de un 75% los tiempos de renderizado en bucles densos y plantillas cinéticas complejas (alcanzando más de 200 líneas por segundo en ejecución monohilo).
* **Precisión Geométrica Pura sin Doble Escalado:** Generación de vectores tipográficos al 100% de escala base, delegando la deformación anamórfica de estilos y tags exclusivamente al renderizador ASS y erradicando deformaciones en rebanadores y extrusiones.

---

### Nuevas Funcionalidades

* **Modo de Renderizado Dual en el Previsualizador:** Se incorporó un botón selector en la cabecera del nodo `System/Previewer`, ventana desacoplada y modo pantalla completa para alternar al instante entre:
  * **Modo Typesetting:** Renderizado idéntico 1:1 a Aegisub y VSFilter a resolución nativa del guion.
  * **Modo mpv:** Rasterización vectorial en alta definición (High-DPI) en espacio de pantalla con preservación de bordes nítidos y proporciones de aspecto automáticas (PAR/DAR).
* **Aprovisionamiento Multimedia Automático con un Clic:** El previsualizador detecta preventivamente la ausencia de herramientas auxiliares de video e incorpora un asistente visual que permite descargarlas e instalarlas en segundo plano de manera transparente, con barra de progreso y sin requerir permisos de administrador.
* **Modo de Partición en Shape/Union & Divide:** Nuevo control selector **Split Mode** (*Islands* vs *Path*) en el modo Fusion (Tags), permitiendo conservar rebanadas contiguas de `Shape/Slicer` como islas independientes para aplicarles estilos o colores individuales sin que se suelden entre sí.
* **Control de Aceleración en Interpolación Geométrica:** Entrada y parámetro **accel** en `Shape/Union & Divide` para modular con curvas no lineales suaves (*ease-in* y *ease-out*) las transiciones entre formas vectoriales y colores.
* **Nivel Base de Visibilidad en Functions/Animation:** Nuevo parámetro **Base** en el modo Alpha para definir la opacidad base de los fotogramas sin forzar opacidad completa al 100%.
* **Paleta Multicanal Expandida en Functions/Color Gradient:** Incorporación de 12 combinaciones multicanal de color (`\12c`, `\13c`, `\14c`, `\23c`, `\24c`, `\34c`, `\123c`, `\124c`, `\134c`, `\234c`, `\1234c`, `\c`) con generación directa de etiquetas ASS compatibles con libass.
* **Erosión y Adelgazamiento Perimetral en Shape/Manipulator:** Soporte completo para valores negativos en **Offset Border** tanto en modo Borders como Matrix, facilitando el adelgazamiento controlado de siluetas complejas con huecos interiores y disolución suave al desaparecer.

---

### Mejoras de Flujo y Ergonomía

* **Rediseño Ergonómico de Cajas de Texto Inline:** Los nodos `Basics/String` y `Basics/Number` fueron rediseñados para ofrecer una edición cómoda y predecible:
  * Cajas compactas de tamaño predeterminado optimizado (60 px de alto) con ajuste automático de texto al ancho del nodo (*word-wrap*).
  * Soporte para el atajo de teclado `Shift+Enter`, permitiendo saltos de línea visuales para organizar listas y fórmulas sin enviar el valor antes de tiempo.
  * Paridad visual 1:1 exacta en tamaño de fuente, posición y márgenes entre el modo de lectura en el lienzo y el editor interactivo.
  * Barra de desplazamiento suave y navegación por rueda de ratón sin deformaciones de la caja.
  * El nodo `Basics/Number` ahora inicia con el campo vacío por defecto, agilizando la escritura directa.
* **Soberanía y Jerarquía de Variables en Define Vars:** Las variables de tiempo (`st`, `et`, `dur`), capa (`layer`) y alineación (`align`) ahora pueden modificarse directamente desde `Variables/Define Vars`, aplicando una jerarquía de precedencia clara de 4 niveles (`Línea Base < Define Vars < Salida Explícita < Tags`) y protegiendo las variables de métrica ground-truth de la unidad contra mutaciones accidentales.
* **Preservación Integral de Estilos en Nodos de Álgebra Geométrica:** Los nodos de deformación, recorte y generación vectorial ahora separan y reintegran limpiamente los bloques de tags ASS entrantes, permitiendo encadenar efectos sin perder colores, rotaciones o animaciones previas.
* **Aislamiento de Generación Aleatoria:** Las llamadas a números aleatorios jerárquicos (`by.j`, `by.char.R`) mantienen secuencias estocásticas independientes entre caracteres distintos sin colisiones indeseadas.
* **Conversión de Medios Automática y Silenciosa:** Detección de pistas de audio incompatibles con navegadores (como AC-3 o DTS), generando automáticamente una versión optimizada en segundo plano para reproducción inmediata sin cortes de sonido.
* **Restauración Instantánea al Salir de Pantalla Completa:** Erradicación de pantallas negras o desincronización de dimensiones al alternar entre pantalla completa y lienzo en el reproductor.

---

### Correcciones de Errores

* **Eliminación del Doble Escalado en Vectores Tipográficos:** Resuelto el problema por el cual textos convertidos a vector heredaban la escala del estilo en la geometría y volvían a ser escalados por libass en tiempo de renderizado, provocando que extrusiones y rebanados resultaran significativamente más estrechos que el texto de referencia.
* **Paridad de Color Exacta con Aegisub:** Sincronización de la matriz de color YCbCr y del atributo `ScaledBorderAndShadow` en el motor de previsualización, eliminando variaciones de matiz y desfases en bordes o sombras al hacer zoom.
* **Estabilidad Numérica de Punto Flotante:** Corrección de residuos infinitesimales y prevención de notación científica en fórmulas de posición, evitando que partículas o textos se desplazaran inesperadamente a las coordenadas (0, 0).
* **Reconocimiento de Nombres Propios de Formas:** Se estableció el prefijo canónico `shape.` para siluetas de biblioteca, evitando que palabras de texto coincidentes (como "heart", "star" o "diamond") fueran interceptadas como formas geométricas.
* **Tolerancia a Comas en Funciones Anidadas:** El nodo `Basics/Number` y el validador del grafo ahora procesan de forma balanceada expresiones con funciones de múltiples argumentos (como `clamp`, `lerp` o rangos aleatorios `R(min, max)`) sin generar errores de sintaxis espurios.
* **Preservación de Tamaños Personalizados:** Los nodos con dimensiones manuales ajustadas por el usuario (como `Functions/Animation`) mantienen estrictamente su tamaño al editar propiedades o alternar modos en la cabecera.

---

### Avisos de Compatibilidad y Migración

> [!NOTE]
> * **Formas de Biblioteca:** Cualquier referencia a figuras vectoriales predefinidas en plantillas o expresiones de nodos debe incluir el prefijo canónico `shape.<nombre>` (por ejemplo, `shape.star` o `shape.heart`), garantizando la vectorización pura de texto regular sin ambigüedades.
> * **Escalado de Extrusiones Vectoriales:** Debido a la eliminación del doble pre-escalado en `FontVectorEngine`, las plantillas que aplicaban factores de compensación manual para contrarrestar el estrechamiento anterior ahora coinciden píxel a píxel de forma nativa al 100% de escala del estilo.
