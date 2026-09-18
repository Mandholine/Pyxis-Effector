<p align="center">
  <img src="PyxisNodes/web/icon.png" alt="Pyxis Effector Logo" width="128" height="128">
</p>

<h1 align="center">Pyxis Effector</h1>

<p align="center">
  <strong>Visual Node-Based Karaoke Automation Engine for Aegisub</strong>
</p>

<p align="center">
  <a href="https://github.com/Mandholine/Pyxis-Effector/releases">
    <img src="https://img.shields.io/badge/version-1.1.0-blue.svg" alt="Versión">
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/license-GPL--3.0-green.svg" alt="Licencia GPL-3.0">
  </a>
  <img src="https://img.shields.io/badge/Aegisub-Automation%204-orange.svg" alt="Aegisub">
  <img src="https://img.shields.io/badge/Python-3.11-3776AB.svg?logo=python&logoColor=white" alt="Python 3.11">
  <a href="https://discord.gg/rYsARc3fB9">
    <img src="https://img.shields.io/badge/Discord-Comunidad-5865F2.svg?logo=discord&logoColor=white" alt="Discord">
  </a>
</p>

<p align="center">
  <a href="README.md"><img src="https://img.shields.io/badge/Idioma-Espa%C3%B1ol-2563EB.svg" alt="Español"></a>
  <a href="README.en.md"><img src="https://img.shields.io/badge/Language-English-6B7280.svg" alt="English"></a>
</p>
<p align="center">
  <strong>Español</strong> &bull; <a href="README.en.md">Read in English</a>
</p>

---

## Filosofía y Origen

**Pyxis Effector** nace para dar continuidad y evolución al proyecto legacy **Kara Effector 3.6**, renovando su arquitectura desde los cimientos con una interfaz visual moderna, atractiva y diseñada para ofrecer la máxima personalización y flexibilidad en la creación de efectos para subtítulos ASS.

El nombre del proyecto está inspirado en la constelación de **Pyxis** (La Brújula). Del mismo modo que un lienzo de nodos conecta líneas de lógica para generar composiciones complejas, buscamos que esta herramienta sea un punto de unión entre ideas y creadores, permitiendo a tipógrafos, karaokers y programadores llevar a cabo sus proyectos más ambiciosos.

El proyecto se encuentra en una **etapa avanzada de desarrollo**, en constante evolución y con la meta de seguir ampliando sus capacidades creativas y técnicas.

---

## Características Principales

* **Entorno visual basado en nodos:** Construcción de efectos interactivos sin depender exclusivamente de scripts estáticos.
* **Arquitectura híbrida de alto rendimiento:** Núcleo optimizado en Python 3.11 con soporte para multiprocesamiento paralelo y aceleración por GPU.
* **Previsualización en tiempo real:** Reproductor integrado en el canvas mediante renderizado acelerado WebAssembly (JASSUB) y ArtPlayer.
* **Procesamiento de audio y espectro:** Detección de transitorios, envolventes y sincronización temporal precisa con el flujo de audio.
* **Manipulación y vectorización de fuentes:** Trazado de glifos a curvas vectoriales y soporte para polígonos complejos.
* **Nodos de código integrados:** Editor embebido para inyectar lógica personalizada en Lua y Python en cualquier punto del flujo.
* **Gestión de plantillas y persistencia:** Guardado y exportación de grafos completos con librerías de estilos predefinidos.

---

## Instalación y Uso Rápido

1. Descarga la versión más reciente desde la sección de **Releases** del repositorio.
2. Copia el archivo `Pyxis_engine.lua` y la carpeta `PyxisNodes` dentro del directorio de automatizaciones de Aegisub:
   * **Instalación estándar:** `%APPDATA%\Aegisub\automation\autoload\`
   * **Aegisub portable:** `<Carpeta_Aegisub>\automation\autoload\`
3. Inicia Aegisub y accede al menú superior:
   * **Automatización** -> **Pyxis Node Engine**

---

## Equipo y Contribuciones

* **Trota** ([@mandholine](https://github.com/Mandholine)): Diseño e implementación de la interfaz de usuario de nodos, portado y arquitectura integral del motor a Python, extensiones y mejoras del ecosistema Kara Effector.
* **Itachi / Effector** ([@effector2](https://github.com/effector2)): Diseño y desarrollo de las librerías de funciones en Lua y lógica de procesamiento. Participante histórico en el desarrollo de Kara Effector legacy.
* **Zaph** ([@pholguinc](https://github.com/pholguinc)): Diseño de la arquitectura inicial para el puente de comunicación e interacción entre Python y Lua.

---

## Agradecimientos

Dedicamos un agradecimiento especial a los desarrolladores y contribuidores originales de **Kara Effector 3.6 legacy**. Su esfuerzo y visión en la automatización de efectos sentaron las bases que inspiraron la creación de esta nueva generación.

---

## Código Externo y Créditos de Terceros

Pyxis Effector integra y hace uso de estas tecnologías y librerías de código abierto:

* [**LiteGraph.js**](https://github.com/jagenjo/litegraph.js): Motor de grafo de nodos y canvas visual (Licencia MIT).
* [**Ace Editor**](https://github.com/ajaxorg/ace): Editor de código embebido para nodos de scripting (Licencia BSD).
* [**ArtPlayer.js**](https://artplayer.org/): Reproductor de vídeo HTML5 (Licencia MIT).
* [**JASSUB**](https://github.com/ThaUnknown/jassub) / [**libass**](https://github.com/libass/libass): Renderizado de subtítulos ASS en WebAssembly (Licencias MIT / ISC / GPL).
* [**Potrace**](https://potrace.sourceforge.net/): Utilidad de vectorización y trazado de mapas de bits a curvas (Licencia GPL v2+).
* [**FFmpeg**](https://ffmpeg.org/): Framework multimedia para decodificación, extracción de audio y transcodificación de vídeo (Licencias LGPL v2.1+ / GPL v2+).
* [**Python Runtime (Embedded)**](https://www.python.org/): Entorno de ejecución embebido de Python Software Foundation (Licencia PSF).

---

## Declaración sobre el Uso de Inteligencia Artificial

Como medida de transparencia y claridad de autoría, se hace constar que la interfaz web de este proyecto ha sido desarrollada utilizando como herramienta de asistencia técnica la inteligencia artificial **Google Gemini** mediante **Antigravity**.

---

## Licencia

Este proyecto está bajo los términos de la **GNU General Public License v3.0 (GPL-3.0)**. Puedes consultar el texto completo en el archivo [LICENSE](LICENSE).

---

## Comunidad y Soporte

Para dudas, sugerencias, compartir nodos o reportar problemas, puedes unirte a nuestro servidor de Discord:

* **Discord Oficial:** [discord.gg/rYsARc3fB9](https://discord.gg/rYsARc3fB9)