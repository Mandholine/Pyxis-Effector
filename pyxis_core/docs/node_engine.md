# Motor de Nodos y Efectos (Node Engine)

El núcleo de generación visual de `pyxis-core` se basa en un motor de grafos nodales de flujo de datos acíclico dirigido (**DAG**). Permite construir efectos visuales complejos sin escribir código repetitivo de temporización o dibujo.

---

## 🔄 Ciclo de Vida y Evaluación de un Grafo

1. **Compilación / Toposort:**  
   El grafo de nodos se analiza topológicamente para determinar el orden exacto de ejecución de los nodos. Se detectan dependencias circulares o desconexiones.
2. **Iteración de Contexto:**  
   El motor itera sobre las líneas del archivo ASS (o sobre sílabas en modo karaoke). Para cada elemento, genera un objeto `Context`.
3. **Flujo de Datos:**  
   Los puertos de salida (`output ports`) transfieren valores tipados (números, strings, curvas de interpolación, vectores, matrices de partículas) hacia los puertos de entrada (`input ports`) de los nodos conectados.
4. **Ensamblado de Etiquetas ASS:**  
   Los nodos finales del flujo inyectan etiquetas de estilo y transformación (como `\pos`, `\fscx`, `\fscy`, `\clip`, `\t`, `\c`, `\p1...{\p0}`) en la línea final de diálogo.

---

## 📦 Categorías de Nodos Disponibles

Los nodos se encuentran organizados en submódulos especializados dentro de `pyxis_core.infrastructure.engine.graph.nodes`:

### 1. Nodos de Texto (`text_nodes.py`)
- **`TextSplitter`**: Divide un diálogo por caracteres, palabras, líneas o sílabas de karaoke (`\k`).
- **`TextCase`**: Modifica la capitalización (mayúsculas, minúsculas, título).
- **`TextFilter`**: Limpia o extrae etiquetas ASS incrustadas en el texto original.

### 2. Nodos de Tiempo e Interpolación (`time_nodes.py`)
- **`TimeOffset`**: Aplica desfases de entrada y salida (`lead_in`, `lead_out`) relativos al tiempo de inicio o fin de la línea.
- **`EasingCurve`**: Genera curvas de interpolación matemáticas (Linear, Ease-In, Ease-Out, Ease-InOut, Elastic, Bounce, Cubic Bézier).
- **`StaggerDelay`**: Introduce retardos escalonados progresivos entre caracteres o palabras consecutivas.

### 3. Nodos de Posición y Transformación (`shape_nodes.py`)
- **`PositionEffect`**: Calcula coordenadas cartesianas `\pos(x, y)` estáticas o animadas con aceleración.
- **`ScaleEffect`**: Ajusta escalas horizontales y verticales (`\fscx`, `\fscy`).
- **`RotationEffect`**: Controla ángulos de rotación en 3 ejes (`\frz`, `\frx`, `\fry`).
- **`OriginEffect`**: Fija el pivote de transformación (`\org(x, y)`).

### 4. Nodos de Formas y Geometría ASSDraw
- **`ShapeDrawer`**: Permite dibujar primitivas vectoriales (círculos, estrellas, rectángulos redondeados, polígonos regulares).
- **`VectorClip`**: Genera cajas de recorte o siluetas vectoriales (`\clip(...)` / `\iclip(...)`).
- **`ClipperBoolean`**: Ejecuta operaciones booleanas de unión, diferencia e intersección de caminos vectoriales.

### 5. Nodos de Partículas (`particle_nodes.py`)
- **`ParticleEmitter`**: Emisor de partículas 2D con simulación de física (gravedad, velocidad inicial, fricción, dispersión angular y tiempo de vida).
- **`ParticleForce`**: Campos de fuerza (viento, turbulencia simétrica, atracción/repulsión a un punto).

### 6. Nodos de Audio y Sincronización (`audio_nodes.py`)
- **`AudioWaveform`**: Muestrea la amplitud de la pista de audio en el rango de tiempo de la línea.
- **`BeatDetector`**: Dispara pulsos y efectos basados en los golpes de ritmo de la música.
- **`SpectrumBand`**: Filtra frecuencias específicas (bajos, medios, agudos) para modular parámetros visuales.

### 7. Nodos de Lógica y Matemáticas (`math_nodes.py`, `loop_nodes.py`, `variable_nodes.py`)
- **`MathOperation`**: Suma, resta, multiplicación, división, potencias, módulo, funciones trigonométricas (seno, coseno, tangente).
- **`RandomGenerator`**: Generador de números aleatorios pseudo-deterministas basados en una semilla fija por línea.
- **`LoopNode`**: Repite la generación de líneas duplicadas con variaciones de desenfoque (`\blur`) o sombra para lograr efectos de resplandor (*glow*).

---

## 🛠️ Cómo Crear un Nodo Personalizado

Para registrar un nuevo nodo en el motor de Pyxis:

```python
from pyxis_core.infrastructure.engine.graph.node_engine import register_node

@register_node("CustomGlowNode")
def custom_glow_node(context, blur_amount=5.0, color="&H0000FFFF", iterations=3):
    """Genera capas superpuestas con niveles crecientes de desenfoque."""
    generated_tags = []
    for i in range(1, iterations + 1):
        step_blur = blur_amount * (i / iterations)
        tag = f"\\blur{step_blur:.1f}\\1c{color}\\alpha&H{int(255 * (i / iterations)):02X}&"
        generated_tags.append(tag)
    
    return {"tags": generated_tags}
```

El nuevo nodo estará inmediatamente disponible para ser referenciado por su nombre en cualquier grafo JSON cargado por `PyxisCore`.
