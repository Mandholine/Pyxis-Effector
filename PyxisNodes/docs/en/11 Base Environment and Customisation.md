# Base Environment and Customisation

The **Base Environment** (`preview_base.ass`) provides an isolated workspace for previewing and validating effects independently from the primary subtitle script loaded in Aegisub.
It documents the lifecycle of the file in `%APPDATA%`, the temporal clip window model, its style structure, and reactive hot-reloading.

---

## 1. Architecture and Preview Modes

The **`System/Previewer`** node includes a source toggle that switches between two operational modes:

* **Active Project Mode (Aegisub Icon):** Connects the real-time player to the video, audio, styles, and dialogue lines currently loaded in the active Aegisub session.
* **Base Preset Mode (CD Disc Icon):** Temporarily detaches the player from Aegisub to project the graph output onto the `preview_base.ass` file within a standardised, reproducible laboratory environment.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             PREVIEW MODES MATRIX                            │
├──────────────────────────────────────┬──────────────────────────────────────┤
│                                      │                                      │
│                 ┌────────────────────┴────────────────────┐                 │
│                 ▼                                         ▼                 │
│  ┌──────────────────────────────┐       ┌────────────────────────────────┐  │
│  │   AEGISUB MODE (Aegi Icon)   │       │    BASE MODE (CD Disc Icon)    │  │
│  │   • Active production script │       │    • Isolated %APPDATA% sandbox│  │
│  │   • Session video and audio  │       │    • Fixed laboratory media    │  │
│  │   • Live episode dialogues   │       │    • Controlled test template  │  │
│  └──────────────────────────────┘       └────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Lifecycle and Persistence in `%APPDATA%`

### 2.1. Filesystem Location
The base script resides in the Windows user profile configuration directory:

```
%APPDATA%\PyxisNodes\preview_base.ass
```

*(Standard path: `C:\Users\<User>\AppData\Roaming\PyxisNodes\preview_base.ass`)*.

### 2.2. Zero-Overwrite Policy (User Data Integrity)
Pyxis Effector enforces a strict preservation rule regarding user data:
1. **Initial Execution:** If the file does not exist in `%APPDATA%\PyxisNodes\`, the engine automatically copies the default factory template bundled with the installation package.
2. **Version Upgrades:** Once generated, **Pyxis never overwrites or deletes this file**. All customisations—including custom styles, canvas dimensions, video links, and syllable test phrases—belong exclusively to the user and remain fully persistent across software releases.

### 2.3. Reactive SHA-256 Hash Invalidation (Hot-Reloading)
To eliminate the need to restart the application or re-instantiate the `System/Previewer` node when modifying the base environment, the backend inspects the cryptographic signature of the file:
* Upon each preview compilation request, the engine calculates the `SHA-256` checksum of `preview_base.ass` on disk.
* When the user modifies and saves `preview_base.ass` in Aegisub or an external text editor, the altered hash automatically invalidates the in-memory cache (`_cached_preview_base_info`).
* The player immediately updates native canvas resolution, frame rate, audio track, and typographic geometry in real time.

---

## 3. Mathematical Model of the Temporal Clip Window

Pyxis does not restrict playback to the strict syllable duration of the base script; it dynamically computes an **automated temporal buffer (*Lead-In / Lead-Out Cushion*)** to allow full visual evaluation of entry and exit transitions:

### 3.1. Temporal Window Formulations

Let $\mathcal{D} = \{d_1, d_2, \dots, d_m\}$ be the set of dialogue lines defined in `preview_base.ass`, where each line possesses a start timestamp $t_{\text{start}}(d_i)$ and end timestamp $t_{\text{end}}(d_i)$ in milliseconds:

$$t_{\text{min}} = \min_{d \in \mathcal{D}} \big(t_{\text{start}}(d)\big)$$

$$t_{\text{max}} = \max_{d \in \mathcal{D}} \big(t_{\text{end}}(d)\big)$$

From these bounds, the engine establishes the relative clip interval in seconds:

$$t_{\text{clip\_start}} = \max\left(0.0, \; \frac{t_{\text{min}} - 2000}{1000.0}\right)$$

$$t_{\text{clip\_end}} = \frac{t_{\text{max}} + 2000}{1000.0}$$

$$T_{\text{clip\_dur}} = \max\left(2.0, \; t_{\text{clip\_end}} - t_{\text{clip\_start}}\right)$$

$$t_{\text{clip\_start\_ms}} = \lfloor t_{\text{clip\_start}} \times 1000 \rfloor$$

### 3.2. Practical Function of the 2000 ms Cushion
* **Evaluation of `Time/Lead In` Nodes:** Spatial animations that trigger prior to syllable activation (e.g. off-screen approaches, exponential velocity curves `accel`, or progressive reveals) receive up to 2000 ms of preparatory lead time.
* **Evaluation of `Time/Lead Out` Nodes:** Post-syllable transitions (`\fad`, stochastic particle dispersion, alpha dissolution) retain 2000 ms of trailing playback before the timeline loops.
* **Relative Timeline Scrubbing:** The scrubber in `Previewer` maps relative position $00:00$ precisely to $t_{\text{clip\_start\_ms}}$, allowing designers to inspect the active phase without dead timeline margins.

---

## 4. Anatomy and Internal Structure of `preview_base.ass`

The `preview_base.ass` script adheres to the standard ASS format (*v4.00+*), organised into four functional sections:

```ini
[Script Info]
; Canvas geometry and coordinate system
Title: Default Aegisub file
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: None
PlayResX: 1000
PlayResY: 260

[Aegisub Project Garbage]
; Reference video and audio bindings
Last Style Storage: Default
Audio File: dummy-audio:silence?sr=44100&bd=16&ch=1&ln=396900000
Video File: ?dummy:23.976000:361:1000:260:150:150:150:c
Video AR Value: 3.846154
Video Zoom Percent: 1.187500
Active Line: 1
Video Position: 120

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Arial,65,&H00FFFFFF,&H000000FF,&H007A3419,&H007A1C42,0,0,0,0,100,100,0,0,1,2,2,2,10,10,100,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 1,0:00:05.00,0:00:10.00,Default,,0,0,0,,{\k43}Ma{\k65}ry {\k44}te{\k87}nía {\k65}un {\k65}cor{\k44}de{\k43}ri{\k44}to
```

---

## 5. Technical Customisation Guide

### 5.1. Step 1: Set Native Canvas Resolution (`PlayResX` / `PlayResY`)
The script resolution establishes the Cartesian plane for both absolute positioning and relative anchor offsets:
* **Full HD Resolution (1080p):**
  ```ini
  PlayResX: 1920
  PlayResY: 1080
  ```
* **Standard HD Resolution (720p):**
  ```ini
  PlayResX: 1280
  PlayResY: 720
  ```
> [!NOTE]
> The WebAssembly rendering engine (`JASSUB`) and ArtPlayer adapt automatically to the aspect ratio ($\text{AR} = \text{PlayResX} / \text{PlayResY}$) and scale output surfaces to eliminate anamorphic distortion.

### 5.2. Step 2: Configure Reference Media Sources
Under `[Aegisub Project Garbage]`, specify your preferred testing assets:

#### Option A: Synthetic Dummy Video (Recommended)
Provides instant startup at 23.976 or 60 FPS without requiring physical video storage on disk:
```ini
Video File: ?dummy:23.976000:40000:1920:1080:26:26:26:
```
* **Syntax:** `?dummy:<FPS>:<FrameCount>:<Width>:<Height>:<R>:<G>:<B>:`
* The colour values `26:26:26:` produce a neutral dark grey backdrop that provides clean contrast for white particles, outline strokes, and luminous glows.

#### Option B: Real Local Video and Audio Media
When calibrating lip synchronisation, spectral envelope modulation with `Audio/Modulator`, or transient detection in `Audio/Waveform`, point directly to a local multimedia file:
```ini
Video File: C:\KaraokeResources\test_track_1080p.mp4
Audio File: C:\KaraokeResources\test_track_1080p.mp4
```
> [!TIP]
> If the video file contains an embedded audio track, specifying `Video File` is sufficient; Pyxis automatically decodes and routes the acoustic stream to the PCM buffer and spectral analyser.

### 5.3. Step 3: Calibrate Baseline Typographic Styles (`[V4+ Styles]`)
Pyxis scans `[V4+ Styles]` and extracts the **first defined style** as the canonical reference:
* **`Fontname`:** Font family installed on the system or located in `%APPDATA%\PyxisNodes\fonts\`.
* **`Fontsize`:** Primary typographic height in script pixels (e.g. `65` to `80` for 1080p).
* **`PrimaryColour` (`&HAABBGGRR&`):** Main glyph fill colour.
* **`Outline` and `OutlineColour`:** Outline stroke width and colour for stroke nodes and concentric border rings.
* **`Alignment`:** Standard ASS alignment (`5` for screen centre, `2` for lower third).

### 5.4. Step 4: Define Representative Test Karaoke Events (`[Events]`)
Structure the dialogue phrase to include varied syllable lengths and glyph shapes:
```ini
Dialogue: 0,0:00:03.00,0:00:09.00,Default,,0,0,0,,{\k45}Kyou{\k40}kai {\k60}no {\k50}Ka{\k55}na{\k70}ta
```
* **Short Syllables ($\le 200\text{ ms}$):** Ideal for verifying high-velocity impacts, snap eases, and elastic rebounds.
* **Sustained Syllables ($\ge 600\text{ ms}$):** Optimal for observing continuous harmonic oscillators (`Tag Oscillator`) or continuous particle emission trails.
* **Complex Glyphs:** Include dense Kanji characters or letters with isolated counter-spaces (`B`, `P`, `o`, `8`) to audit Clipper2 polygon orientation and winding rules.

---

## 6. Master Production Reference Template (Full HD 1080p)

The following listing is a complete, production-ready `preview_base.ass` script configured for Full HD 1080p at 23.976 FPS with high-contrast background shading:

```ini
[Script Info]
; Pyxis Effector - Customised Laboratory Sandbox
Title: Pyxis Sandbox Environment
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: TV.709
PlayResX: 1920
PlayResY: 1080

[Aegisub Project Garbage]
Video File: ?dummy:23.976000:40000:1920:1080:24:28:32:
Audio File: ?dummy:23.976000:40000:1920:1080:24:28:32:

[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Default,Cinzel Decorative,76,&H00FFFFFF,&H000000FF,&H00141619,&H80000000,1,0,0,0,100,100,1.5,0,1,3.0,1.5,5,40,40,40,1

[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
Dialogue: 0,0:00:03.00,0:00:08.50,Default,,0,0,0,,{\k45}Py{\k35}xis {\k60}Ef{\k50}fec{\k40}tor {\k75}Nodes
```

---

## 7. Recommended Production Workflows

1. **Synthetic Video Sharing:**
   * When publishing template graphs for community sharing, configure the base environment with `?dummy:...`. This ensures that downstream users can open and preview your effects without encountering missing media alerts.
2. **Local Font Staging:**
   * When designing with boutique or custom display typography, place your `.ttf` or `.otf` font files in `%APPDATA%\PyxisNodes\fonts\`. Pyxis vectorises and renders these fonts locally via FreeType/HarfBuzz and libass without requiring system-wide installation.
3. **Factory Reset Procedure:**
   * To restore the base environment to its initial distribution defaults, close Pyxis Effector, delete `%APPDATA%\PyxisNodes\preview_base.ass`, and relaunch the application; the engine automatically writes a fresh copy.
