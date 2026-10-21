# Adaptadores y Herramientas Nativas

`pyxis-core` complementa la lógica pura de Python con algoritmos de alto rendimiento implementados en C/C++ y herramientas del sistema para tareas computacionalmente intensivas como el trazado de contornos vectoriales y el análisis de telemetría de renderizado en tiempo real.

---

## 1. Vectorizador de Imágenes: `img2ass` / `potrace`

Conforme a la especificación técnica de Pyxis Effector, `img2ass` permite transformar imágenes de mapas de bits (PNG con transparencia alfa, JPG, WebP) en comandos nativos de dibujo ASSDraw (`{\p1}m ... b ... c ...{\p0}`).

### Características:
- **Detección automática de transparencia:** Recorta el canal alfa y calcula el contorno exacto sin recuadros exteriores artificiales.
- **Suavizado de curvas Bézier:** Algoritmo Potrace para generar curvas suaves de bajo peso en el script.
- **Puntos de anclaje configurables:** Centrado automático (`Center`), superior izquierdo (`TopLeft`), o según el punto de alineación del estilo ASS.

### Uso mediante el Adaptador de Python:

```python
from pyxis_core.infrastructure.adapters import ImageTracerAdapter

# Vectorizar imagen a dibujo ASS
resultado = ImageTracerAdapter.trace(
    image_path="icono.png",
    mode="Potrace",          # Modo de vectorización
    anchor="Center",         # Posición del pivote (0,0) en el dibujo
    turdsize=2,              # Filtro para eliminar manchas pequeñas o ruido
    alphamax=1.0             # Suavizado de esquinas
)

print(f"Dimensiones: {resultado['width']} x {resultado['height']} px")
print(f"Puntos vectoriales: {resultado['points']}")
print(f"Comando ASSDraw generado:")
print(resultado["shape"][:100] + "...")
```

### Ejecución directa desde consola:

```bash
# Sintaxis: ./img2ass <imagen_entrada> <ass_salida>
pyxis_core/pyxis_core/infrastructure/engine/bin/img2ass logo.png logo.ass
```

---

## 2. Telemetría y Profiling: `libass_profiler`

Para garantizar que un efecto de subtítulos complejo no cause caídas de tasa de refresco en reproductores como mpv, VLC o Aegisub, `pyxis-core` integra el analizador nativo `libass_profiler`.

### Métricas Analizadas:
- **Dropped Frames:** Cuántos fotogramas sobrepasan el presupuesto temporal asignado (p. ej. > 41.7 ms a 23.976 fps).
- **Tiempo de renderizado promedio y máximo (ms):** Identifica picos de carga en escenas con miles de partículas o etiquetas `\clip` complejas.
- **Histograma de rendimiento:** Distribución de tiempos por percentiles (p50, p95, p99).

### Uso desde Python:

```python
from pyxis_core.infrastructure.adapters import TelemetryAdapter

# Analizar rendimiento a 23.976 fps
reporte = TelemetryAdapter.analyze_file("karaoke_efecto.ass", fps=23.976)

resumen = reporte["summary"]
print("Total de fotogramas:", resumen["total_frames"])
print("Fotogramas caídos (lag):", resumen["dropped_frames_count"])
print(f"Render time máximo: {resumen['max_render_time_ms']:.2f} ms")
print(f"Render time medio: {resumen['avg_render_time_ms']:.2f} ms")
```

---

## 3. Motor Tipográfico y Métricas: `FontAdapter`

Para calcular la posición exacta de cada carácter y sílaba sin depender de la GUI de Aegisub, `FontAdapter` utiliza `freetype-py` y las fuentes instaladas en el sistema operativo:

- Medición precisa de anchos y altos en píxeles de cualquier cadena de texto.
- Extracción de glifos en curvas Bézier para manipulación morfométrica.
- Soporte para fuentes TrueType (`.ttf`), OpenType (`.otf`) y Web Fonts (`.woff`).

```python
from pyxis_core.infrastructure.adapters import FontAdapter

ancho = FontAdapter.get_text_width("Hola Mundo", font_name="Arial", font_size=48.0)
print(f"Ancho estimado: {ancho:.2f} px")
```

---

## 4. Resolución y Búsqueda de Binarios en el Sistema

El gestor canónico de rutas (`paths.py`) localiza automáticamente los ejecutables necesarios en el siguiente orden de prioridad:

1. Directorio interno `pyxis_core/infrastructure/engine/bin/`.
2. Raíz de la instalación de Pyxis.
3. Variable de entorno `$PATH` del sistema (incluyendo `/opt/homebrew/bin`, `/usr/local/bin` en macOS).
