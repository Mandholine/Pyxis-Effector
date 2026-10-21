# Arquitectura del Sistema (Clean Architecture)

`pyxis-core` implementa los principios de **Clean Architecture** (Arquitectura Limpia) propuestos por Robert C. Martin ("Uncle Bob"). El objetivo principal es lograr la total independencia de la lógica de negocio respecto a interfaces gráficas, frameworks web, sistemas de archivos o bibliotecas externas.

---

## 🏛️ El Modelo de Capas concéntricas

El flujo de dependencias sigue la **Regla de Dependencia**: el código de las capas internas no conoce nada sobre las capas externas.

```
       +-------------------------------------------------------+
       |                  INFRASTRUCTURE                       |
       |  (FileSubtitleRepository, AudioAdapter, Potrace,      |
       |   libass_profiler, ClipperEngine, PyxisProfiler)      |
       +-------------------------------------------------------+
                                  |
                                  v
       +-------------------------------------------------------+
       |                   APPLICATION                         |
       |  (ProcessGraphUseCase, ValidateGraphUseCase,          |
       |   ManageTemplatesUseCase, DTOs, Mappers)              |
       +-------------------------------------------------------+
                                  |
                                  v
       +-------------------------------------------------------+
       |                     DOMAIN                            |
       |  (SubtitleScript, DialogueLine, SubtitleStyle,        |
       |   NodeGraph, Timecode, Resolution, Repository I/F)    |
       +-------------------------------------------------------+
```

---

## 1. Capa de Dominio (`pyxis_core.domain`)

La capa más interna y pura. No contiene referencias a bibliotecas externas pesadas ni a sistemas de archivos.

### Entidades (`domain/entities`)
- **`SubtitleScript`**: Representación en memoria de un archivo completo de subtítulos ASS (cabeceras `[Script Info]`, diccionario de `SubtitleStyle` y lista de eventos `DialogueLine`).
- **`DialogueLine`**: Cada evento de diálogo o comentario (`Layer`, `Start`, `End`, `Style`, `Actor`, `Margins`, `Effect`, `Text`).
- **`SubtitleStyle`**: Estilo tipográfico ASS (`Fontname`, `Fontsize`, colores primario/secundario/borde/sombra, alineación, márgenes).
- **`NodeGraph`**, **`NodeItem`**, **`NodeConnection`**: Estructuras matemáticas que describen el grafo de cálculo y sus conexiones de flujo de datos.
- **`EffectTemplate`**: Metadatos y definición de efectos reutilizables y empaquetados.

### Objetos de Valor (`domain/value_objects`)
- **`Timecode`**: Objeto inmutable que modela tiempos de subtítulo con precisión de milisegundos y provee conversión bidireccional exacta con el formato ASS estándar `H:MM:SS.cs`.
- **`Resolution`**: Objeto inmutable que define las dimensiones del lienzo (`PlayResX`, `PlayResY`), cálculo de relación de aspecto (`aspect_ratio`) y duración del fotograma (`fps`).

### Interfaces de Repositorio (`domain/repositories`)
- **`ISubtitleRepository`**: Define los contratos abstractos para leer y escribir guiones de subtítulos:
  - `read_from_file(path: str) -> SubtitleScript`
  - `read_from_text(content: str) -> SubtitleScript`
  - `write_to_file(script: SubtitleScript, path: str) -> None`
  - `write_to_text(script: SubtitleScript) -> str`
- **`ITemplateRepository`**: Contrato para persistir y consultar plantillas de efectos.

---

## 2. Capa de Aplicación (`pyxis_core.application`)

Contiene la orquestación de la lógica de casos de uso y la transferencia desacoplada de información.

### Casos de Uso (`application/use_cases`)
- **`ProcessGraphUseCase`**: Coordina la carga del guión, la resolución del grafo, la invocación del motor de cálculo nodal y la serialización del resultado con soporte de cancelación y callbacks de progreso.
- **`ValidateGraphUseCase`**: Valida exhaustivamente que un grafo de nodos contenga sintaxis correcta, conexiones válidas entre tipos de datos compatibles y que no contenga ciclos prohibidos.
- **`ManageTemplatesUseCase`**: Permite listar, cargar, registrar y eliminar plantillas de efectos.

### Objetos de Transferencia de Datos (`application/dtos`)
- **`ProcessGraphRequestDTO`**, **`ProcessGraphResponseDTO`**, **`ProgressEventDTO`**
- **`ValidateGraphRequestDTO`**, **`ValidationResultDTO`**
- **`TemplateDTO`**, **`TemplateListDTO`**

### Mappers (`application/mappers`)
- **`SubtitleMapper`**: Convierte entre representaciones de diccionarios/JSON y entidades puras de dominio `SubtitleScript`.
- **`GraphMapper`**: Convierte grafos en formato dict/JSON a entidades `NodeGraph`.

---

## 3. Capa de Infraestructura (`pyxis_core.infrastructure`)

Implementa los detalles técnicos, acceso a hardware, persistencia y algoritmos de bajo nivel.

### Repositorios Concretos (`infrastructure/repositories`)
- **`FileSubtitleRepository`**: Implementa `ISubtitleRepository` leyendo y escribiendo ficheros `.ass` en el sistema de archivos con encoding UTF-8 / UTF-8 con BOM.
- **`FileTemplateRepository`**: Implementa `ITemplateRepository` almacenando plantillas JSON en disco.

### Adaptadores (`infrastructure/adapters`)
- **`ImageTracerAdapter`**: Interfaz de alto nivel para vectorizar imágenes a formas vectoriales ASSDraw (`{\p1}...{\p0}`).
- **`TelemetryAdapter`**: Invoca el binario de profiling nativo `libass_profiler` para medir el impacto en la CPU y los fotogramas caídos.
- **`FontAdapter`**: Consulta y resolución de métricas tipográficas y vectores de glifos con FreeType y el sistema operativo.
- **`AudioAdapter`**: Procesamiento de ondas sonoras y preprocesamiento de audio para sincronización.

### Motores Internos (`infrastructure/engine`)
- **`graph/node_engine.py`**: El motor ejecutor del pipeline de grafos que compila las funciones de los nodos y evalúa los datos fila por fila o sílaba por sílaba.
- **`geometry/clipper_engine.py`**: Operaciones booleanas vectoriales (unión, diferencia, intersección, offset) utilizando `pyclipper`.
- **`subtitles/karaskel_engine.py`**: Motor Karaskel de cálculo de posiciones, anchos de palabras y temporizaciones de karaoke silábico.
