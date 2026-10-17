<p align="center">
  <img src="PyxisNodes/web/icon.png" alt="Pyxis Effector Logo" width="128" height="128">
</p>

<h1 align="center">Pyxis Effector</h1>

<p align="center">
  <strong>Motor Visual Basado en Nodos para la Automatización de Efectos de Karaoke en Aegisub</strong>
</p>

<p align="center">
  <a href="https://github.com/Mandholine/Pyxis-Effector/releases">
    <img src="https://img.shields.io/badge/version-1.1.4-blue.svg" alt="Versión">
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/license-GPL--3.0-green.svg" alt="Licencia GPL-3.0">
  </a>
  <img src="https://img.shields.io/badge/Aegisub-Automation%204-orange.svg" alt="Aegisub">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB.svg?logo=python&logoColor=white" alt="Python 3.12">
</p>

<p align="center">
  <a href="https://discord.gg/fsxRESeQZN">
    <img src="https://img.shields.io/badge/Discord-Comunidad-5865F2.svg?logo=discord&logoColor=white" alt="Discord">
  </a>
  <a href="https://x.com/PyxisEffector">
    <img src="https://img.shields.io/badge/X-@PyxisEffector-000000.svg?logo=x&logoColor=white" alt="X (Twitter)">
  </a>
  <a href="https://github.com/Mandholine/Pyxis-Effector">
    <img src="https://img.shields.io/badge/GitHub-Repositorio-181717.svg?logo=github&logoColor=white" alt="GitHub">
  </a>
  <a href="mailto:pyxiseffector@gmail.com">
    <img src="https://img.shields.io/badge/Email-Contacto-EA4335.svg?logo=gmail&logoColor=white" alt="Email">
  </a>
</p>

<p align="center">
  <a href="README.md"><img src="https://img.shields.io/badge/Idioma-Espa%C3%B1ol-2563EB.svg" alt="Español"></a>
  <a href="README.en.md"><img src="https://img.shields.io/badge/Language-English-6B7280.svg" alt="English"></a>
</p>
<p align="center">
  <strong>Español</strong> &bull; <a href="README.en.md">Read in English (en-GB)</a>
</p>

---

## Filosofía y Origen

**Pyxis Effector** renueva y extiende la arquitectura técnica del proyecto legacy **Kara Effector 3.6**, sustituyendo la ejecución secuencial de scripts monolíticos por un entorno visual estructurado en grafos acíclicos dirigidos (DAG). El sistema combina un núcleo en Python 3.12, aceleración por GPU, renderizado WebAssembly en tiempo real y soporte para manipulación vectorial avanzada de subtítulos Advanced SubStation Alpha (ASS).

El nombre proviene de la constelación de **Pyxis** (La Brújula náutica), simbolizando la orientación técnica y la convergencia modular entre tipografía cinética, álgebra espacial, cinemática temporal y lógica algorítmica.

---

## Características Principales

* **Entorno visual modular en grafo (DAG):** Composición modular interactiva de efectos conectando puertos de datos y contexto sin requerir programación secuencial obligatoria.
* **Arquitectura híbrida de ejecución:** Núcleo en Python 3.12 con soporte para evaluación paralela multiproceso y aceleración por GPU mediante OpenCL.
* **Previsualización en tiempo real:** Reproductor sincronizado integrado en el canvas mediante renderizado WebAssembly (JASSUB/libass) y ArtPlayer.js.
* **Morfología vectorial y polígonos:** Conversión de glifos a contornos vectoriales, vectorización ráster con Potrace y operaciones booleanas (unión, diferencia, intersección, xor, offsetting) con Clipper2.
* **Procesamiento acústico espectral:** Extracción de envolventes de amplitud RMS, picos acústicos, filtrado por bandas y Transformada Rápida de Fourier (FFT) vinculada al audio del proyecto.
* **Entorno dual de scripting:** Nodos imperativos `System/Script Code` con soporte de ejecución para Python 3.12 y Lua 5.1/LuaJIT a través de un puente bidireccional en C (Lupa).
* **Linter y diagnóstico pre-generación:** Validador sintáctico estático (`node_validator.py`) con análisis AST en tiempo real para Dark Tags ASS, variables no declaradas e integridad topológica.
* **Telemetría y perfilado de renderizado ASS (`libass` + QPC):** Perfilado multi-proceso fotograma a fotograma del coste de renderizado, consumo de Frame Budget y memoria de mapas de bits, con mapa de calor térmico interactivo en el reproductor.
* **Persistencia y gestión de plantillas:** Exportación e importación de grafos completos, aislamiento de sesiones y almacenamiento de plantillas en `%APPDATA%\PyxisNodes\` (Windows), `~/.local/share/PyxisNodes` (Linux/macOS).

---

## Manual Técnico Oficial

Pyxis Effector dispone de una documentación técnica exhaustiva organizada en 12 volúmenes modulares, accesible en [`PyxisNodes/docs/es/`](PyxisNodes/docs/es/) (y su correspondiente versión en inglés británico en [`PyxisNodes/docs/en/`](PyxisNodes/docs/en/)):

| Volumen | Título | Ámbito Técnico Principal |
| :---: | :--- | :--- |
| **01** | [Paradigma Visual y Arquitectura](PyxisNodes/docs/es/01%20Paradigma%20visual.md) | Principios de grafo DAG, ciclo de vida del contexto, tipificación de expresiones y perfilado de renderizado con `libass`. |
| **02** | [Anatomía de la Interfaz](PyxisNodes/docs/es/02%20Anatomia%20de%20la%20interfaz.md) | Barra de herramientas, panel de navegación, lienzo de nodos, modales y atajos de teclado. |
| **03** | [Nodos Básicos y Tipos Primitivos](PyxisNodes/docs/es/03%20Basics.md) | `Number`, `String`, `Text`, `Color Picker`, `Math`, `MultiRandom`, `Concatenate`, `Dynamic Format`, `MultiTag`, `Only`, `Once`. |
| **04** | [Nodos de Sistema y Pipeline](PyxisNodes/docs/es/04%20System.md) | `Output`, `Previewer`, `Script Code`, `Benchmark Math`, pipeline de renderizado y ordenamiento de colas. |
| **05** | [Bucles y Control de Iteración](PyxisNodes/docs/es/05%20Loops.md) | `Main Loop` (sílabas, palabras, caracteres), `MaxLoop` (FBF y partículas) y operador `Module`. |
| **06** | [Geometría y Morfología Vectorial](PyxisNodes/docs/es/06%20Shapes.md) | Primitivas, `Library`, `IMG to Shape`, `Stroke`, `Walker`, `Slicer`, `Array`, `Concentric`, `Multi`, `Manipulator`, `Transform`, `Filter`, `Clipper`, `Union & Divide`. |
| **07** | [Temporalización e Interpolación](PyxisNodes/docs/es/07%20Times.md) | Fases de retiming, desfases `Lead In`/`Out`, sincronización inter-línea `Synced`, deltas `Middle`, bucles `Loop`, conversiones de tiempo y curvas `Ipol`. |
| **08** | [Funciones Cinemáticas y Moduladores](PyxisNodes/docs/es/08%20Functions.md) | `Tag Manipulator`, `Tag Oscillator`, `Glitter`, `Conditioner`, `Animation`, `Color Gradient`, `Clip Gradient`, `IMG to pixels`, `Polar to Cartesian`, splines `Bezier`, partículas y texto vectorial. |
| **09** | [Variables y Gestión de Contexto](PyxisNodes/docs/es/09%20Variables.md) | Jerarquía métrica formal, aislamiento de iteradores DAG, `Sys Var`, `Define Vars`, `Get Var`, `Memory` y tipificación Tipos A/B/C. |
| **10** | [Procesamiento y Reactividad de Audio](PyxisNodes/docs/es/10%20Audio.md) | Decodificación PCM, cálculo $\mathcal{O}(1)$ de RMS mediante Prefix Sums, picos, envolventes, FFT y modos `Modulator` / `Waveform`. |
| **11** | [Entorno Base y Renderizado Autónomo](PyxisNodes/docs/es/11%20Entorno%20base%20y%20personalizacion.md) | Modo Base independiente de Aegisub, ventana cinemática con margen de 2000 ms, plantillas de lienzo e invalidación SHA-256. |
| **12** | [Scripting y Programación Avanzada](PyxisNodes/docs/es/12%20Scripting%20y%20programacion%20avanzada.md) | Entorno dual Python/Lua, generadores funcionales de tags ASS, cinemática, persistencia y motor determinista `by.<iter>.<R>`. |

---

## Instalación y Uso Rápido

### Windows

#### Requisitos del Sistema
* Windows 10 / 11 (64-bit).
* Aegisub 3.2.x, 3.3.x o 3.4.x (versión instalada o portable).
* Microsoft Visual C++ Redistributable (2015-2022 x64).

#### Instrucciones de Instalación
1. Descarga el paquete de lanzamiento más reciente desde la sección de [**Releases**](https://github.com/Mandholine/Pyxis-Effector/releases).
2. Copia el archivo `Pyxis_engine.lua` y el directorio `PyxisNodes` en la carpeta de automatizaciones de Aegisub:
   * **Instalación de usuario estándar:** `%APPDATA%\Aegisub\automation\autoload\`
   * **Instalación de sistema:** `C:\Program Files\Aegisub\automation\autoload\`
   * **Instalación portable:** `<Carpeta_Aegisub>\automation\autoload\`
3. Inicia Aegisub y ejecuta la macro desde la barra superior:
   * **Automatización** $\to$ **Pyxis Node Engine**

### Linux y macOS

Pyxis Effector funciona de forma nativa en Linux y macOS. Cada release incluye un paquete
por plataforma con su propio Python ya preparado (no necesitas instalar nada más salvo,
en su caso, ffmpeg):

| Plataforma | Paquete | Carpeta `autoload` de Aegisub |
| :--- | :--- | :--- |
| Linux x86-64 | `PyxisEffector-v<versión>-linux64.zip` | `~/.config/aegisub/automation/autoload/` |
| Linux ARM64 | `PyxisEffector-v<versión>-linux-arm64.zip` | `~/.config/aegisub/automation/autoload/` |
| macOS Apple Silicon | `PyxisEffector-v<versión>-macos-arm64.zip` | `~/Library/Application Support/Aegisub/automation/autoload/` |
| macOS Intel | `PyxisEffector-v<versión>-macos-x64.zip` | `~/Library/Application Support/Aegisub/automation/autoload/` |

Descomprime el paquete en la carpeta `autoload` (crea `PyxisNodes/`), copia ahí
`pyxis.NodeEngine.lua` y ejecuta **Automatización → Pyxis Node Engine**. Si falta el
motor, la macro ofrece descargarlo automáticamente.

* Linux: **[PyxisNodes/README.linux.md](PyxisNodes/README.linux.md)** (dependencias del sistema, datos XDG, instalación desde el código fuente con `install_linux.sh`, solución de problemas).
* macOS: **[PyxisNodes/README.macos.md](PyxisNodes/README.macos.md)** (Gatekeeper, Homebrew, instalación desde el código fuente con `install_macos.sh`).
* Para construir los paquetes tú mismo: `python tools/build_release.py` (ver `tools/build_release.py --help`).

---

## Equipo y Contribuciones

* **Trota** ([@mandholine](https://github.com/Mandholine)): Diseño e implementación de la interfaz gráfica de nodos, arquitectura del motor en Python, extensiones del ecosistema Kara Effector y documentación técnica.
* **Itachi / Effector** ([@effector2](https://github.com/effector2)): Diseño y desarrollo de bibliotecas de funciones en Lua, algoritmos cinemáticos y lógica de procesamiento. Coautor de Kara Effector legacy.
* **Zaph** ([@pholguinc](https://github.com/pholguinc)): Diseño arquitectónico inicial para el puente de comunicación e interoperabilidad entre Python y Lua.

---

## Agradecimientos Históricos

Reconocimiento y agradecimiento a los desarrolladores y colaboradores del proyecto histórico **Kara Effector 3.6 legacy**, cuyas ideas y algoritmos iniciales en la automatización de subtítulos inspiraron la creación de esta nueva arquitectura visual.

---

## Código Externo y Créditos de Terceros

Pyxis Effector integra y utiliza las siguientes librerías y componentes de código abierto:

* [**LiteGraph.js**](https://github.com/jagenjo/litegraph.js): Motor de grafo de nodos y canvas visual interactivo (Licencia MIT).
* [**Ace Editor**](https://github.com/ajaxorg/ace): Editor de código embebido para nodos de scripting (Licencia BSD).
* [**ArtPlayer.js**](https://artplayer.org/): Reproductor multimedia HTML5 (Licencia MIT).
* [**JASSUB**](https://github.com/ThaUnknown/jassub) / [**libass**](https://github.com/libass/libass): Renderizado de subtítulos ASS compilado en WebAssembly (Licencias MIT / ISC / GPL).
* [**Clipper2**](https://github.com/AngusJohnson/Clipper2) / [**PyClipper**](https://github.com/fonttools/pyclipper): Motor de geometría poligonal, operaciones booleanas y cálculo de offset (Licencia BSL-1.0).
* [**Potrace**](https://potrace.sourceforge.net/): Vectorización y conversión de mapas de bits a trazados vectoriales (Licencia GPL v2+).
* [**KaTeX**](https://katex.org/): Renderizado tipográfico de fórmulas matemáticas en interfaz y documentación (Licencia MIT).
* [**Marked.js**](https://marked.js.org/): Compilador de Markdown para la documentación integrada y tooltips contextuales (Licencia MIT).
* [**Lupa**](https://github.com/scoder/lupa): Puente de comunicación bidireccional en C entre Python y LuaJIT / Lua 5.1 (Licencia MIT).
* [**PyWebView**](https://pywebview.flowrl.com/): Capa de ventana web nativa de escritorio para Windows, macOS y Linux (Licencia BSD-3).
* [**FFmpeg**](https://ffmpeg.org/): Decodificación multimedia, extracción de pistas PCM y procesado de vídeo (Licencias LGPL v2.1+ / GPL v2+).
* [**Python Runtime (Embedded)**](https://www.python.org/): Entorno embebido de Python Software Foundation (Licencia PSF).

---

## Declaración sobre el Uso de Inteligencia Artificial

Como medida de transparencia y claridad de autoría, se hace constar que el desarrollo técnico y la arquitectura de la interfaz web de este proyecto han contado con la asistencia técnica de **Google Gemini** a través de **Antigravity**.

---

## Licencia

Este proyecto está distribuido bajo los términos de la **GNU General Public License v3.0 (GPL-3.0)**. El texto completo se encuentra disponible en el archivo [LICENSE](LICENSE).