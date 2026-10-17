<p align="center">
  <img src="PyxisNodes/web/icon.png" alt="Pyxis Effector Logo" width="128" height="128">
</p>

<h1 align="center">Pyxis Effector</h1>

<p align="center">
  <strong>Visual Node-Based Karaoke Automation Engine for Aegisub</strong>
</p>

<p align="center">
  <a href="https://github.com/Mandholine/Pyxis-Effector/releases">
    <img src="https://img.shields.io/badge/version-1.1.4-blue.svg" alt="Version">
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/licence-GPL--3.0-green.svg" alt="GPL-3.0 Licence">
  </a>
  <img src="https://img.shields.io/badge/Aegisub-Automation%204-orange.svg" alt="Aegisub">
  <img src="https://img.shields.io/badge/Python-3.12-3776AB.svg?logo=python&logoColor=white" alt="Python 3.12">
</p>

<p align="center">
  <a href="https://discord.gg/fsxRESeQZN">
    <img src="https://img.shields.io/badge/Discord-Community-5865F2.svg?logo=discord&logoColor=white" alt="Discord">
  </a>
  <a href="https://x.com/PyxisEffector">
    <img src="https://img.shields.io/badge/X-@PyxisEffector-000000.svg?logo=x&logoColor=white" alt="X (Twitter)">
  </a>
  <a href="https://github.com/Mandholine/Pyxis-Effector">
    <img src="https://img.shields.io/badge/GitHub-Repository-181717.svg?logo=github&logoColor=white" alt="GitHub">
  </a>
  <a href="mailto:pyxiseffector@gmail.com">
    <img src="https://img.shields.io/badge/Email-Contact-EA4335.svg?logo=gmail&logoColor=white" alt="Email">
  </a>
</p>

<p align="center">
  <a href="README.md"><img src="https://img.shields.io/badge/Language-Espa%C3%B1ol-6B7280.svg" alt="Español"></a>
  <a href="README.en.md"><img src="https://img.shields.io/badge/Language-English%20(en--GB)-2563EB.svg" alt="English (en-GB)"></a>
</p>
<p align="center">
  <a href="README.md">Leer en Español</a> &bull; <strong>English (en-GB)</strong>
</p>

---

## Philosophy and Origin

**Pyxis Effector** renovates and extends the technical architecture of the legacy **Kara Effector 3.6** project, replacing sequential monolithic script execution with a visual environment structured around directed acyclic graphs (DAGs). The system combines a Python 3.12 core, GPU acceleration, real-time WebAssembly rendering, and comprehensive support for Advanced SubStation Alpha (ASS) vector subtitle manipulation.

The project is named after the **Pyxis** constellation (The Mariner's Compass), symbolising technical orientation and the modular convergence between kinetic typography, spatial geometry, temporal kinematics, and algorithmic logic.

---

## Key Features

* **Modular DAG Visual Canvas:** Interactive visual effect composition by interconnecting data and context ports without requiring mandatory sequential scripting.
* **Hybrid Execution Architecture:** Optimised Python 3.12 runtime supporting multi-process parallel evaluation and OpenCL GPU acceleration.
* **Real-Time Synchronised Preview:** Integrated canvas player powered by WebAssembly-compiled ASS rendering (JASSUB/libass) and ArtPlayer.js.
* **Vector Morphology and Polygons:** Glyph outline conversion, bitmap raster vectorisation via Potrace, and boolean polygon operations (union, difference, intersection, xor, offsetting) via Clipper2.
* **Spectral Acoustic Analysis:** Root Mean Square (RMS) power envelopes, acoustic peaks, frequency band filtering, and Fast Fourier Transform (FFT) linked to project audio.
* **Dual Scripting Environment:** Imperative `System/Script Code` nodes with native execution support for Python 3.12 and Lua 5.1/LuaJIT via a low-latency bidirectional C bridge (Lupa).
* **Pre-Generation Linter and Diagnostics:** Static syntax validator (`node_validator.py`) with real-time AST analysis for ASS Dark Tags, undeclared variables, and topological integrity.
* **ASS Render Telemetry and Profiling (`libass` + QPC):** Multi-process frame-by-frame profiling of subtitle render costs, frame budget consumption, and bitmap memory, with an interactive workload heatmap in the player. Native on Windows; on Linux and macOS it runs through Wine (provisional workaround).
* **Persistence and Template Management:** Full graph export/import, session isolation, and user template storage in `%APPDATA%\PyxisNodes\` (Windows) or `~/.local/share/PyxisNodes` (Linux/macOS).

---

## Official Technical Manual

Pyxis Effector includes a comprehensive technical manual structured across 12 modular volumes, available in British English in [`PyxisNodes/docs/en/`](PyxisNodes/docs/en/) (and in Spanish in [`PyxisNodes/docs/es/`](PyxisNodes/docs/es/)):

| Volume | Title | Primary Technical Scope |
| :---: | :--- | :--- |
| **01** | [Visual Paradigm and Architecture](PyxisNodes/docs/en/01%20Visual%20Paradigm.md) | DAG principles, context lifecycle, expression classification, and `libass` render telemetry. |
| **02** | [Interface Anatomy and Controls](PyxisNodes/docs/en/02%20Interface%20Anatomy.md) | Toolbar, navigation drawer, node canvas, modal dialogues, and keyboard shortcuts. |
| **03** | [Basic Nodes and Primitive Types](PyxisNodes/docs/en/03%20Basics.md) | `Number`, `String`, `Text`, `Color Picker`, `Math`, `MultiRandom`, `Concatenate`, `Dynamic Format`, `MultiTag`, `Only`, `Once`. |
| **04** | [System Nodes and Pipeline](PyxisNodes/docs/en/04%20System.md) | `Output`, `Previewer`, `Script Code`, `Benchmark Math`, rendering pipeline, and queue sorting. |
| **05** | [Loops and Iteration Control](PyxisNodes/docs/en/05%20Loops.md) | `Main Loop` (syllables, words, characters), `MaxLoop` (FBF and particles), and the `Module` operator. |
| **06** | [Vector Geometry and Morphology](PyxisNodes/docs/en/06%20Shapes.md) | Primitives, `Library`, `IMG to Shape`, `Stroke`, `Walker`, `Slicer`, `Array`, `Concentric`, `Multi`, `Manipulator`, `Transform`, `Filter`, `Clipper`, `Union & Divide`. |
| **07** | [Timing and Interpolation](PyxisNodes/docs/en/07%20Times.md) | Retiming phases, `Lead In`/`Out` offsets, `Synced` inter-line continuity, `Middle` intervals, `Loop` cycles, conversions, and `Ipol` curves. |
| **08** | [Kinematic Functions and Modulators](PyxisNodes/docs/en/08%20Functions.md) | `Tag Manipulator`, `Tag Oscillator`, `Glitter`, `Conditioner`, `Animation`, `Color Gradient`, `Clip Gradient`, `IMG to pixels`, `Polar to Cartesian`, `Bezier` splines, particles, and vector text. |
| **09** | [Variables and Context Management](PyxisNodes/docs/en/09%20Variables.md) | Formal metric hierarchy, DAG iterator isolation, `Sys Var`, `Define Vars`, `Get Var`, `Memory`, and Type A/B/C classification. |
| **10** | [Audio Processing and Reactivity](PyxisNodes/docs/en/10%20Audio.md) | PCM decoding, $\mathcal{O}(1)$ Prefix Sums RMS calculation, peaks, envelopes, FFT, and `Modulator` / `Waveform` modes. |
| **11** | [Base Environment and Standalone Rendering](PyxisNodes/docs/en/11%20Base%20Environment%20and%20Customisation.md) | Standalone Base Mode independent of Aegisub, kinematic window with 2000 ms padding, canvas templates, and SHA-256 cache invalidation. |
| **12** | [Scripting and Advanced Programming](PyxisNodes/docs/en/12%20Scripting%20and%20Advanced%20Programming.md) | Dual Python/Lua runtime, functional ASS tag generators, kinematics, persistent memory, and the deterministic `by.<iter>.<R>` dispatcher. |

---

## Quick Installation and Usage

Installation is the same on every platform:

1. Download [`pyxis.NodeEngine.lua`](https://raw.githubusercontent.com/Mandholine/Pyxis-Effector/main/pyxis.NodeEngine.lua) (it is also attached to every release in [**Releases**](https://github.com/Mandholine/Pyxis-Effector/releases)).
2. Copy it into Aegisub's `automation/autoload` folder (see the table).
3. Open Aegisub and run **Automation** $\to$ **Pyxis Node Engine**. The first time, the macro offers to download the engine (`PyxisNodes/`) automatically.

If you would rather install it by hand or offline, download the package for your platform from [**Releases**](https://github.com/Mandholine/Pyxis-Effector/releases) and unzip it into that same folder (it creates `PyxisNodes/`). Each package ships its own Python and ffmpeg, so nothing else needs installing.

| Platform | Package | Aegisub `autoload` folder |
| :--- | :--- | :--- |
| Windows 10 / 11 (64-bit) | `PyxisEffector-v<version>-win64.zip` | `%APPDATA%\Aegisub\automation\autoload\` (user), `C:\Program Files\Aegisub\automation\autoload\` (system-wide) or `<Aegisub_Folder>\automation\autoload\` (portable) |
| Linux x86-64 | `PyxisEffector-v<version>-linux64.zip` | `~/.config/aegisub/automation/autoload/` |
| Linux ARM64 | `PyxisEffector-v<version>-linux-arm64.zip` | `~/.config/aegisub/automation/autoload/` |
| macOS Apple Silicon | `PyxisEffector-v<version>-macos-arm64.zip` | `~/Library/Application Support/Aegisub/automation/autoload/` |
| macOS Intel | `PyxisEffector-v<version>-macos-x64.zip` | `~/Library/Application Support/Aegisub/automation/autoload/` |

> **If you have `Pyxis_engine.lua`** from an earlier version, delete it: it is the same script under another name and Aegisub would load the macro twice.

**Requirements:** Aegisub 3.2.x, 3.3.x or 3.4.x (Automation 4). On Windows, also the Microsoft Visual C++ Redistributable (2015-2022 x64); if the Microsoft Edge WebView2 Runtime is missing, Pyxis offers to install it on first launch.

* Linux: **[PyxisNodes/README.linux.md](PyxisNodes/README.linux.md)** (system dependencies, XDG data locations, installing from source with `install_linux.sh`, troubleshooting; in Spanish).
* macOS: **[PyxisNodes/README.macos.md](PyxisNodes/README.macos.md)** (Gatekeeper, Homebrew, installing from source with `install_macos.sh`; in Spanish). macOS support is implemented but **has not been tested on real Mac hardware yet**.
* To build the packages yourself (and to download or compile ffmpeg): [tools/README.md](tools/README.md) (in Spanish).

---

## Team and Contributions

* **Trota** ([@mandholine](https://github.com/Mandholine)): Visual node UI design and implementation, Python engine architecture, Kara Effector ecosystem extensions, and technical documentation.
* **Itachi / Effector** ([@effector2](https://github.com/effector2)): Lua core function libraries, kinematic algorithms, and automation logic. Historical developer of legacy Kara Effector.
* **Zaph** ([@pholguinc](https://github.com/pholguinc)): Architectural design for the initial Python-Lua communication and interoperability bridge.

---

## Historical Acknowledgments

Special recognition is extended to the developers and contributors of the historical **Kara Effector 3.6 legacy** project, whose pioneering concepts and subtitle automation algorithms laid the foundation that inspired this visual node architecture.

---

## Third-Party Code and External Credits

Pyxis Effector integrates and builds upon the following open-source libraries and technologies:

* [**LiteGraph.js**](https://github.com/jagenjo/litegraph.js): Interactive visual canvas and node graph execution engine (MIT Licence).
* [**Ace Editor**](https://github.com/ajaxorg/ace): Embedded code editor for scripting nodes (BSD Licence).
* [**ArtPlayer.js**](https://artplayer.org/): HTML5 multimedia video player (MIT Licence).
* [**JASSUB**](https://github.com/ThaUnknown/jassub) / [**libass**](https://github.com/libass/libass): WebAssembly-compiled ASS subtitle renderer (MIT / ISC / GPL Licences).
* [**Clipper2**](https://github.com/AngusJohnson/Clipper2) / [**PyClipper**](https://github.com/fonttools/pyclipper): Polygon clipping, boolean operations, and contour offsetting engine (BSL-1.0 Licence).
* [**Potrace**](https://potrace.sourceforge.net/): Bitmap-to-vector curve tracing utility (GPL v2+ Licence).
* [**KaTeX**](https://katex.org/): Fast mathematical formula typesetting engine for interface and documentation (MIT Licence).
* [**Marked.js**](https://marked.js.org/): Markdown parser and compiler for integrated documentation and tooltips (MIT Licence).
* [**Lupa**](https://github.com/scoder/lupa): High-performance C bridge connecting Python to LuaJIT / Lua 5.1 (MIT Licence).
* [**PyWebView**](https://pywebview.flowrl.com/): Lightweight desktop webview window wrapper for Windows, macOS and Linux (BSD-3 Licence).
* [**FFmpeg**](https://ffmpeg.org/): Multimedia decoding, PCM stream extraction, and video processing. The core is LGPL v2.1+, but the packages ship **GPL v2+** builds (with libx264, libass and libwebp) from [BtbN](https://github.com/BtbN/FFmpeg-Builds) (Windows and Linux) and [martin-riedl.de](https://ffmpeg.martin-riedl.de) (macOS).
* [**Python**](https://www.python.org/) via [**python-build-standalone**](https://github.com/astral-sh/python-build-standalone): Standalone interpreter bundled in every package (PSF Licence).
* [**PyQt6**](https://www.riverbankcomputing.com/software/pyqt/) / [**Qt WebEngine**](https://www.qt.io/): Graphical interface bundled in the Linux packages (GPL v3 / LGPL v3 Licences).
* [**FreeType**](https://freetype.org/) / [**freetype-py**](https://github.com/rougier/freetype-py): Font metrics and outlines on Linux and macOS (FreeType / BSD Licences).
* [**NumPy**](https://numpy.org/) / [**Pillow**](https://python-pillow.org/): Particle, audio and image processing (BSD-3 / HPND Licences).
* [**Wine**](https://www.winehq.org/): Optional; runs `libass_profiler.exe` on Linux and macOS (LGPL v2.1+ Licence).

---

## AI Disclosure and Transparency Notice

In the interest of transparency and clear authorship practices, please note that:

* The technical design and web interface architecture of this project were developed with technical assistance from **Google Gemini** via **Antigravity**.
* Linux and macOS support (engine adaptation, packaging with a bundled Python, continuous integration and the `tools/` scripts) was developed with the assistance of AI models: **Claude** (Anthropic) and **MiMo 2.6 Pro** (Xiaomi), the latter through **OpenCode Go**.

---

## Licence

Copyright (C) 2026 @mandholine, @effector2, @pholguinc and the Pyxis Effector contributors.

This project is distributed under the terms of the **GNU General Public License v3.0 (GPL-3.0)**. Full text is available in the [LICENSE](LICENSE) file.
