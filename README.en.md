<p align="center">
  <img src="PyxisNodes/web/icon.png" alt="Pyxis Effector Logo" width="128" height="128">
</p>

<h1 align="center">Pyxis Effector</h1>

<p align="center">
  <strong>Visual Node-Based Karaoke Automation Engine for Aegisub</strong>
</p>

<p align="center">
  <a href="https://github.com/Mandholine/Pyxis-Effector/releases">
    <img src="https://img.shields.io/badge/version-1.0.4-blue.svg" alt="Version">
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/license-GPL--3.0-green.svg" alt="GPL-3.0 License">
  </a>
  <img src="https://img.shields.io/badge/Aegisub-Automation%204-orange.svg" alt="Aegisub">
  <img src="https://img.shields.io/badge/Python-3.11-3776AB.svg?logo=python&logoColor=white" alt="Python 3.11">
  <a href="https://discord.gg/rYsARc3fB9">
    <img src="https://img.shields.io/badge/Discord-Community-5865F2.svg?logo=discord&logoColor=white" alt="Discord">
  </a>
</p>

<p align="center">
  <a href="README.md"><img src="https://img.shields.io/badge/Language-Espa%C3%B1ol-6B7280.svg" alt="Español"></a>
  <a href="README.en.md"><img src="https://img.shields.io/badge/Language-English-2563EB.svg" alt="English"></a>
</p>
<p align="center">
  <a href="README.md">Leer en Español</a> &bull; <strong>English</strong>
</p>

---

## Philosophy and Origin

**Pyxis Effector** was created to continue and evolve the legacy **Kara Effector 3.6** project, rebuilding its architecture from the ground up with a modern, visually engaging node-based interface designed to provide maximum customization and workflow flexibility for Advanced SubStation Alpha (ASS) karaoke effects.

The project is named after the **Pyxis** constellation (The Compass). In the same way that a canvas of nodes connects lines of logic to produce intricate subtitle compositions, our goal is for this tool to serve as a nexus between ideas and creators, enabling typesetters, karaokers, and programmers to bring their most ambitious visions to life.

The project is currently in an **advanced development stage**, under active evolution with the goal of continually expanding its creative and technical capabilities.

---

## Key Features

* **Visual Node-Based Workspace:** Design interactive effects without relying solely on rigid, linear script-writing.
* **High-Performance Hybrid Architecture:** Optimized Python 3.11 core with parallel multiprocessing and GPU acceleration support.
* **Real-Time Live Preview:** Integrated canvas player powered by WebAssembly-accelerated ASS rendering (JASSUB) and ArtPlayer.
* **Audio and Spectrum Processing:** Audio waveform analysis, transient detection, envelopes, and precision time synchronization.
* **Vector Font and Glyph Manipulation:** Trace glyphs into vector curves and generate custom polygon shapes via Potrace.
* **Embedded Scripting Nodes:** On-the-fly execution nodes supporting custom Lua and Python logic injected anywhere in the execution graph.
* **Template Store and Persistence:** Save, export, and load complete graph setups with preset style libraries.

---

## Quick Installation and Usage

1. Download the latest release from the repository's **Releases** section.
2. Copy the `Pyxis_engine.lua` file and the `PyxisNodes` directory into your Aegisub automation autoload folder:
   * **Standard Installation:** `%APPDATA%\Aegisub\automation\autoload\`
   * **Portable Aegisub:** `<Aegisub_Folder>\automation\autoload\`
3. Launch Aegisub and navigate to the top menu:
   * **Automation** -> **Pyxis Node Engine**

---

## Team and Contributions

* **Trota** ([@mandholine](https://github.com/Mandholine)): Visual node UI design and implementation, complete Python engine architecture and porting, Kara Effector ecosystem extensions and enhancements.
* **Itachi / Effector** ([@effector2](https://github.com/effector2)): Core Lua function libraries, automation algorithms, and processing logic. Historic developer of legacy Kara Effector.
* **Zaph** ([@pholguinc](https://github.com/pholguinc)): Architectural design for the initial Python-Lua communication bridge.

---

## Acknowledgments

We extend our sincere gratitude to the original developers and contributors of **Kara Effector 3.6 legacy**. Their pioneering dedication to effect automation laid the foundation that inspired this next-generation engine.

---

## Third-Party Code and External Credits

Pyxis Effector integrates and builds upon these open-source technologies and libraries:

* [**LiteGraph.js**](https://github.com/jagenjo/litegraph.js): Node graph rendering engine and visual canvas (MIT License).
* [**Ace Editor**](https://github.com/ajaxorg/ace): Embedded code editor for scripting nodes (BSD License).
* [**ArtPlayer.js**](https://artplayer.org/): HTML5 video playback framework (MIT License).
* [**JASSUB**](https://github.com/ThaUnknown/jassub) / [**libass**](https://github.com/libass/libass): WebAssembly ASS subtitle rendering engine (MIT / ISC / GPL Licenses).
* [**Potrace**](https://potrace.sourceforge.net/): Bitmap-to-vector curve tracing utility (GPL v2+ License).
* [**FFmpeg**](https://ffmpeg.org/): Multimedia framework for audio extraction, decoding, and video transcoding (LGPL v2.1+ / GPL v2+ Licenses).
* [**Python Runtime (Embedded)**](https://www.python.org/): Embedded Python Software Foundation distribution (PSF License).

---

## AI Disclosure and Transparency Notice

In the interest of transparency and clear authorship practices, please note that the web interface of this project was developed using **Google Gemini** artificial intelligence via **Antigravity** as a technical assistance tool.

---

## License

This project is licensed under the terms of the **GNU General Public License v3.0 (GPL-3.0)**. Full text is available in the [LICENSE](LICENSE) file.

---

## Community and Support

For questions, suggestions, sharing node presets, or reporting issues, join our official Discord server:

* **Official Discord:** [discord.gg/rYsARc3fB9](https://discord.gg/rYsARc3fB9)
