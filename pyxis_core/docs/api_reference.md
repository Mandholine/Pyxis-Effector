# Referencia de API (API Reference)

Este documento detalla todas las clases, métodos, firmas y estructuras expuestas públicamente por `pyxis_core`.

---

## 1. Fachada Principal: `PyxisCore`

```python
from pyxis_core import PyxisCore
```

`PyxisCore` actúa como el contenedor de servicios unificado y la puerta de entrada más amigable a todos los casos de uso del motor.

### Constructor

```python
core = PyxisCore(
    subtitle_repo: Optional[ISubtitleRepository] = None,
    template_repo: Optional[ITemplateRepository] = None
)
```
- **`subtitle_repo`**: Implementación de almacenamiento de subtítulos. Por defecto utiliza `FileSubtitleRepository`.
- **`template_repo`**: Implementación de almacenamiento de plantillas. Por defecto utiliza `FileTemplateRepository`.

### Métodos Principales

#### `process(...) -> ProcessGraphResponseDTO`

Procesa un archivo o texto de subtítulos aplicando el grafo de nodos indicado.

```python
response = core.process(
    graph: Union[Dict[str, Any], str],
    ass_path: Optional[str] = None,
    ass_content: Optional[str] = None,
    output_path: Optional[str] = None,
    progress_callback: Optional[Callable[[ProgressEventDTO], None]] = None,
    cancel_checker: Optional[Callable[[], bool]] = None,
    default_audio_source: Optional[str] = None,
) -> ProcessGraphResponseDTO
```

**Parámetros:**
- `graph`: Ruta al archivo `.json` del grafo o `dict` que contiene la definición del grafo (`nodes`, `connections`).
- `ass_path`: Ruta absoluta o relativa al archivo `.ass` original en disco.
- `ass_content`: Cadena de texto con el contenido ASS completo (si no se usa `ass_path`).
- `output_path`: (Opcional) Ruta de destino donde se escribirá el archivo procesado. Si es `None`, el resultado estará en `response.output_content`.
- `progress_callback`: Función que recibe un objeto `ProgressEventDTO` con el porcentaje (`percent`) y la fase actual (`phase`).
- `cancel_checker`: Función que retorna `True` si el usuario o proceso ha solicitado cancelar la operación.
- `default_audio_source`: Ruta a un archivo de audio para análisis de ondas sonoras o beat tracking.

**Retorno (`ProcessGraphResponseDTO`):**
- `success: bool`: Indica si la ejecución concluyó sin errores.
- `lines_count: int`: Cantidad de líneas generadas en el guión final.
- `duration_seconds: float`: Tiempo total empleado en el cálculo.
- `output_path: Optional[str]`: Ruta del archivo guardado, si se indicó.
- `output_content: Optional[str]`: Texto ASS resultante en memoria.
- `error: Optional[str]`: Mensaje de error detallado en caso de fallo.

---

#### `validate(...) -> ValidationResultDTO`

Verifica la integridad de un grafo antes de su ejecución.

```python
result = core.validate(graph: Union[Dict[str, Any], str]) -> ValidationResultDTO
```

**Retorno (`ValidationResultDTO`):**
- `valid: bool`: `True` si el grafo es ejecutable.
- `errors: List[str]`: Lista de errores fatales encontrados (nodos inexistentes, tipos incompatibles, ciclos).
- `warnings: List[str]`: Advertencias sobre posibles entradas no conectadas o valores por defecto.

---

## 2. Entidades de Dominio

### `SubtitleScript`

```python
from pyxis_core import SubtitleScript, DialogueLine, SubtitleStyle, Resolution
```

Representa un guión ASS completo.

**Atributos:**
- `title: str`: Título del script (`[Script Info]`).
- `script_type: str`: Versión de script (`v4.00+`).
- `wrap_style: int`: Modo de ajuste de líneas (0 a 3).
- `scaled_border_and_shadow: bool`: Escalar borde y sombra según la resolución.
- `resolution: Resolution`: Objeto de resolución de renderizado.
- `styles: Dict[str, SubtitleStyle]`: Diccionario con los estilos definidos indexados por su nombre.
- `dialogues: List[DialogueLine]`: Lista de líneas de subtítulo ordenadas cronológicamente.
- `lines_count: int` (propiedad): Retorna `len(dialogues)`.

---

### `DialogueLine`

Representa una línea individual de diálogo o comentario.

**Atributos:**
- `layer: int`: Capa visual (mayor número renderiza encima).
- `start_time: Timecode`: Tiempo inicial de visualización.
- `end_time: Timecode`: Tiempo final de visualización.
- `style: str`: Nombre del estilo asignado.
- `actor: str`: Nombre del personaje/hablante.
- `margin_l: int`, `margin_r: int`, `margin_v: int`: Márgenes locales de la línea.
- `effect: str`: Campo Effect de ASS (utilizado frecuentemente en plantillas o karaoke).
- `text: str`: Texto de la línea, incluyendo etiquetas ASS (`{\pos(x,y)\fad(100,100)}...`).
- `is_comment: bool`: `True` si la línea está marcada como comentario (`Comment:`).
- `duration_ms: int` (propiedad): Duración en milisegundos calculada como `end_time - start_time`.

**Métodos:**
- `to_ass_line() -> str`: Convierte la entidad a una línea con formato ASS válido (`Dialogue: 0,0:00:01.00,...`).

---

### `SubtitleStyle`

Representa la definición tipográfica de un estilo.

**Atributos:**
- `name: str`: Nombre único del estilo.
- `fontname: str`: Nombre de la familia tipográfica (p. ej. `"Arial"`).
- `fontsize: float`: Tamaño de fuente en puntos.
- `primary_color: str`: Color primario en formato ASS `&HAABBGGRR`.
- `secondary_color: str`: Color secundario (usado en karaoke).
- `outline_color: str`: Color del borde exterior.
- `back_color: str`: Color de la sombra proyectada.
- `bold: bool`, `italic: bool`, `underline: bool`, `strikeout: bool`
- `scale_x: float`, `scale_y: float`, `spacing: float`, `angle: float`
- `border_style: int`: `1` para contorno normal, `3` para caja de fondo opaca.
- `outline: float`: Grosor del contorno en píxeles.
- `shadow: float`: Desplazamiento de sombra en píxeles.
- `alignment: int`: Alineación según el teclado numérico (1 a 9).

---

## 3. Objetos de Valor (Value Objects)

### `Timecode`

```python
from pyxis_core import Timecode

tc = Timecode.from_ass("0:01:23.45")
print(tc.milliseconds)  # 83450
print(tc.to_ass())       # "0:01:23.45"

# Operaciones aritméticas inmutables
tc_plus = tc + Timecode(500)
print(tc_plus.to_ass())  # "0:01:23.95"
```

### `Resolution`

```python
from pyxis_core import Resolution

res = Resolution(play_res_x=1920, play_res_y=1080)
print(res.aspect_ratio)     # 1.7777777777777777 (16:9)
print(res.fps)              # 23.976...
```

---

## 4. Adaptadores de Infraestructura

### `TelemetryAdapter`

```python
from pyxis_core.infrastructure.adapters import TelemetryAdapter

report = TelemetryAdapter.analyze_file("subtitulos.ass", fps=23.976)
print(report["summary"]["total_frames"])
print(report["summary"]["dropped_frames_count"])
```

### `ImageTracerAdapter`

```python
from pyxis_core.infrastructure.adapters import ImageTracerAdapter

res = ImageTracerAdapter.trace(
    image_path="icono.png",
    mode="Potrace",
    anchor="Center"
)
print("ASSDraw shape:", res["shape"])
```
