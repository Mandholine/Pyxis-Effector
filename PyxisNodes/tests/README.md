<!-- Pyxis Effector - Guía de Pruebas Automatizadas y Actualización Segura -->
# Guía de Pruebas Automatizadas de Pyxis Node Engine

Este documento describe la arquitectura de la suite de pruebas automatizadas de Pyxis Node Engine, cómo ejecutarlas en entornos locales y de integración continua, y las pautas obligatorias para actualizar o añadir nuevos nodos y subsistemas con total seguridad.

---

## 1. Arquitectura de la Suite de Pruebas

La infraestructura de pruebas está organizada de forma modular en cinco dominios temáticos bajo el directorio `tests/`:

```
PyxisNodes/
├── run_tests.py                 # Ejecutor unificado de pruebas por línea de comandos
└── tests/
    ├── README.md                # Este documento de arquitectura y guía
    ├── test_helpers.py          # Clases base, fixtures y generadores de datos ASS
    │
    ├── nodes/                   # Pruebas de Nodos Individuales y Bibliotecas
    │   ├── __init__.py
    │   ├── test_math_nodes.py       # Operaciones matemáticas, vectores, interpoladores
    │   ├── test_shape_nodes.py      # Formas geométricas, slicing, walkers, offset
    │   ├── test_time_nodes.py       # Retiming, temporizadores, sincro de sílabas
    │   ├── test_particle_nodes.py   # Emisores de partículas, orden numpad, morph
    │   ├── test_text_nodes.py       # Text on Path, manipuladores de cadenas, kerning
    │   ├── test_audio_nodes.py      # Análisis acústico, RMS, Peak, FFT, moduladores
    │   └── test_system_nodes.py     # Sys Var, Code Node (Python/Lua), registro global
    │
    ├── core/                    # Pruebas del Motor de Grafos y Renderizado
    │   ├── __init__.py
    │   ├── test_node_engine.py      # GraphEngine, resolución topológica, bucles
    │   ├── test_string_evaluator.py # Plantillas dinámicas de strings y expresiones
    │   ├── test_karaskel_engine.py  # Silabación, métricas tipográficas y paridad
    │   ├── test_clipper_engine.py   # Operaciones booleanas poligonales (Clipper)
    │   └── test_gpu_engine.py       # Aceleración GPU y fallback seguro a CPU
    │
    ├── daemon/                  # Pruebas de IPC y Persistencia
    │   ├── __init__.py
    │   ├── test_daemon_ipc.py       # Comunicación HTTP/IPC, sockets y bloqueos (.lock)
    │   ├── test_session_lifecycle.py# Serialización/deserialización de sesiones JSON
    │   └── test_template_store.py   # CRUD de plantillas de usuario y metadatos
    │
    ├── preview/                 # Pruebas de Previsualización y Reproducción
    │   ├── __init__.py
    │   ├── test_preview_engine.py   # Renderizado en tiempo real, salida multi-puerto
    │   └── test_preview_parity.py   # Recursos estáticos y mallas de corte en preview
    │
    └── ui/                      # Pruebas de Interfaz de Usuario y Sintaxis
        ├── __init__.py
        ├── test_i18n.py             # Paridad de diccionarios de idiomas (ES / EN)
        └── test_syntax_integrity.py # Análisis AST de todos los módulos Python
```

---

## 2. Cómo Ejecutar las Pruebas

Las pruebas se ejecutan directamente mediante el script central `run_tests.py` utilizando el intérprete Python embebido o del entorno de desarrollo:

### 2.1 Ejecutar Todas las Pruebas
```powershell
.\python\python.exe run_tests.py --suite all
```

### 2.2 Ejecutar una Suite Específica
Para validar rápidamente un área en desarrollo sin ejecutar la suite completa:

```powershell
# Solo pruebas de nodos individuales
.\python\python.exe run_tests.py --suite nodes

# Solo pruebas del motor de grafos y Karaskel
.\python\python.exe run_tests.py --suite core

# Solo pruebas de comunicación daemon e IPC
.\python\python.exe run_tests.py --suite daemon

# Solo pruebas de previsualización en tiempo real
.\python\python.exe run_tests.py --suite preview

# Solo pruebas de UI, traducción e integridad sintáctica
.\python\python.exe run_tests.py --suite ui
```

### 2.3 Modo Detallado (Verbose)
Para inspeccionar cada caso de prueba individualmente con sus nombres completos:
```powershell
.\python\python.exe run_tests.py --suite nodes -v
```

---

## 3. Guía de Actualización Segura de Nodos

Al añadir un nuevo nodo o modificar uno existente, siga obligatoriamente estos pasos para garantizar que el plugin no sufra regresiones:

### Paso 1: Definir el Nodo y Decoradores
Registre la función del nodo en el módulo correspondiente (`nodes/math_nodes.py`, `nodes/shape_nodes.py`, etc.) utilizando el decorador `@pyxis_node`:

```python
from decorators import pyxis_node

@pyxis_node(
    category="Shape",
    name="Shape Sizer",
    inputs=[{"name": "Shape", "type": "shape"}, {"name": "Factor", "type": "float"}],
    outputs=[{"name": "Shape", "type": "shape"}]
)
def shape_sizer_node(context, shape="", factor=1.0, **kwargs):
    # Implementacion
    return processed_shape
```

### Paso 2: Crear la Prueba Unitaria
Añada los casos de prueba en el archivo de suite correspondiente dentro de `tests/nodes/` heredando de `PyxisTestCase` o `unittest.TestCase`:

1. **Prueba de Valores por Defecto**: Verifique que la función maneje entradas vacías (`""`, `None`) sin lanzar excepciones.
2. **Prueba de Transformación Nominal**: Verifique la salida esperada con datos estándar.
3. **Prueba de Integración en Grafo**: Verifique que `GraphEngine` evalúe el nodo correctamente conectado dentro de un flujo.

Ejemplo:
```python
import unittest
from node_engine import GraphEngine

class TestNewFeature(unittest.TestCase):
    def test_feature_nominal(self):
        graph = {
            "nodes": [
                {"id": 1, "type": "Shape/Shape Sizer", "properties": {"factor": "2.0"}}
            ],
            "links": []
        }
        engine = GraphEngine(graph)
        res = engine.evaluate_data_node(1, {})
        self.assertIsNotNone(res)
```

### Paso 3: Validar Paridad en i18n
Si el nodo incluye nuevas propiedades o descripciones visibles para el usuario en la interfaz gráfica:
1. Declare las claves en `web/i18n.js` bajo las secciones `es` y `en`.
2. Ejecute la suite de UI para confirmar que ambas secciones tienen exactamente las mismas claves:
   ```powershell
   .\python\python.exe run_tests.py --suite ui
   ```

---

## 4. Checklist de Lanzamiento de Versión

Antes de desplegar cambios a la carpeta de producción `autoload/` o generar un release:

- [ ] Todas las 5 suites temáticas pasan al 100% sin fallos ni errores:
      `.\python\python.exe run_tests.py --suite all`
- [ ] No se utilizan emojis Unicode en código fuente, comentarios, mensajes de consola ni documentación (utilice únicamente iconos SVG en la interfaz).
- [ ] La versión del motor está unificada en todos los componentes:
      - `Pyxis_engine.lua` (`script_version = "X.Y.Z"`)
      - `PyxisNodes/main.py` (`PYXIS_ENGINE_VERSION = "X.Y.Z"`)
      - `PyxisNodes/template_store.py` (`PYXIS_ENGINE_VERSION = "X.Y.Z"`)
      - `PyxisNodes/web/index.html` (`<span class="brand-badge">vX.Y.Z</span>`)
- [ ] Los cambios han sido sincronizados a `autoload/PyxisNodes` y validados en Aegisub.
