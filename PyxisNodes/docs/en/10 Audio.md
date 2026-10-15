# Audio

The **Audio** category provides tools for FFT spectral analysis, energy envelope extraction (RMS and Peak), and procedural synthesis of ASSdraw vector waveforms from the project audio track.
It documents the `Audio/Modulator` and `Audio/Waveform` nodes.

---

## Acoustic Processing and Decoding Architecture

Pyxis Effector processes sound tracks via a pipeline of contiguous memory buffers (NumPy float32 normalised in $[-1.0, 1.0]$):

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          AUDIO TRACK RESOLUTION                             │
│  default_audio_source ──► audio_file / video_file ──► Local file / WAV      │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    PCM DECODING AND BUFFER (AudioData)                      │
│  Sampling Rate (Hz), Channels, float32 Normalisation [-1.0, 1.0]            │
└──────────────────────────────────────┬──────────────────────────────────────┘
                                       │
                    ┌──────────────────┴──────────────────┐
                    ▼                                     ▼
┌──────────────────────────────────────┐ ┌────────────────────────────────────┐
│        TEMPORAL ENERGY O(1)          │ │          FFT SPECTROMETRY          │
│  Prefix Sums (Cumulative squared sum │ │  Precalculated Hann window,        │
│  array _sq_cumsum)                   │ │  2048-point RFFT, LRU Cache        │
│  ──► Instantaneous RMS & Peak        │ │  ──► 16-64 Logarithmic Bands       │
└──────────────────┬───────────────────┘ └─────────────────┬──────────────────┘
                   │                                       │
                   ▼                                       ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        MODULATION AND RENDERING                             │
│  • Audio/Modulator ──► \t(t1,t2,\tag...) Tag Chains or Colour / Alpha Values│
│  • Audio/Waveform  ──► ASSdraw m...l... Vector Paths                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 1. Node `Audio/Modulator` (Spectral ASS Tag Modulator)

* **Canonical Category:** `Audio` (UI: *Audio / Modulator*)
* **Purpose:** Samples acoustic energy within a defined time window, applying spectral filtering and low-pass smoothing to modulate any continuous ASS override tag (`\fscy`, `\fscx`, `\blur`, `\alpha`, `\1c`, `\3c`, `\frz`, `\bord`). Compiles concatenated chains of `\t(t1, t2, \tag...)` transitions or interpolated values for `Loops/MaxLoop` sub-loops.

```
┌─────────────────────────────────────────────────────────────┐
│ Audio/Modulator                              [ Mode: rms v ]│
├─────────────────────────────────────────────────────────────┤
│ (o) [Audio Path]                                            │
│ (o) [Tag]                     [ "fscy"                    ] │
│ (o) [Min Val]                 [ 100                       ] │
│ (o) [Max Val]                 [ 160                       ] │
│ (o) [Gain]                    [ 1.0                       ] │
│ (o) [Step ms]                 [ 41.7                      ] │
│ (o) [Smoothing]               [ 0.2                       ] │
│ (o) [Start Time]              [                           ] │
│ (o) [End Time]                [                           ] │
│                                              Tags Out [1.1] (o)
│                                         Current Value [1.2] (o)
│                                          Values Array [1.3] (o)
│                                           Average RMS [1.4] (o)
└─────────────────────────────────────────────────────────────┘
```

> [!NOTE]
> In `custom` mode, the interface displays the additional `[Min Hz]` and `[Max Hz]` fields to configure the target frequency analysis range.

---

### 1.1. Header Mode Combos
1. **`rms` (`RMS` / `General Volume`):** Evaluates overall root-mean-square acoustic energy power across the full audible spectrum. Suitable for scale pulses, glow, and general volume pumping.
2. **`peak` (`Peak` / `Peak Amplitude`):** Detects instantaneous absolute maximum amplitude. Indicated for dry percussive transients, snares, and drum hits.
3. **`bass` (`Bass` / `20-250 Hz`):** Filters energy within the sub-bass and kick drum band ($20\text{ Hz} \dots 250\text{ Hz}$).
4. **`mids` (`Mids` / `250-4000 Hz`):** Isolates the lead vocal spectrum, brass, and melodic instruments ($250\text{ Hz} \dots 4000\text{ Hz}$).
5. **`highs` (`Highs` / `4-16 kHz`):** Detects cymbals, hi-hats, sibilants, and high-frequency transients ($4000\text{ Hz} \dots 16000\text{ Hz}$).
6. **`custom` (`Custom` / `Custom Band`):** Enables the `Min Hz` and `Max Hz` frequency cutoff controls to isolate specific musical harmonics.

---

### 1.2. Input Ports and Body Properties (*Inputs & Properties*)
1. **`Audio Path` (`audio_path`):** Filesystem path to the audio or video file. If not connected or specified, Pyxis automatically resolves the soundtrack loaded in the Aegisub project.
   * **Canonical Categorisation:** **Type C (Plain Text / Filepath)**.
2. **`Tag` (`tag_name`):** ASS override tag to animate (e.g. `"fscy"`, `"fscx"`, `"blur"`, `"alpha"`, `"1c"`, `"3c"`, `"frz"`, `"bord"`). (Default: `"fscy"`).
   * **Canonical Categorisation:** **Type C (Literal ASS Tag Identifier)**.
3. **`Min Val` (`min_val`):** Value assigned at zero sound energy ($0.0$).
   * *Scalar:* Baseline numeric value (e.g. `100.0` for scale, `0.0` for blur).
   * *Alpha:* Baseline transparency hexadecimal code (e.g. `&HFF&` or `255`).
   * *Colour:* Baseline colour in Web Hex (`#RRGGBB`), ASS (`&HBBGGRR&`), or a comma-separated colour palette.
   * **Canonical Categorisation:** **Type A / Type C Polymorphic**.
4. **`Max Val` (`max_val`):** Peak value assigned at maximum acoustic energy ($1.0$).
   * **Canonical Categorisation:** **Type A / Type C Polymorphic**.
5. **`Gain` (`gain`):** Linear gain multiplier factor ($\ge 0.0$, default: `1.0`). Amplifies low-level audio tracks.
   * **Canonical Categorisation:** **Type A (Evaluated Expression)**.
6. **`Step ms` (`step_ms`):** Temporal sampling interval in milliseconds ($\ge 10.0\text{ ms}$, default: `41.7\text{ ms}` $\approx 24\text{ FPS}$).
   * **Canonical Categorisation:** **Type A (Evaluated Expression)**.
7. **`Smoothing` (`smoothing`):** Exponential smoothing coefficient $\alpha \in [0.0, 0.95]$ to filter abrupt jitter (Default: `0.2`).
   * **Canonical Categorisation:** **Type A (Evaluated Expression)**.
8. **`Min Hz` / `Max Hz` (`min_hz`, `max_hz`):** Low and high frequency cutoffs in `custom` mode (Hz). (Default: `20.0` and `250.0`).
   * **Canonical Categorisation:** **Type A (Evaluated Expression)**.
9. **`Start Time` / `End Time` (`start_time`, `end_time`):** Analysis time window in milliseconds. If omitted, automatically adopts the active element interval (`fx.start_time`, `fx.end_time`).
   * **Canonical Categorisation:** **Type A (Evaluated Expression)**.

---

### 1.3. Output Ports (*Outputs*)
1. **`[1.1] Tags Out`:** Complete ASS tag string with concatenated continuous temporal transitions:
   $$\text{\textbackslash fscy100\textbackslash t}(0, 42, \text{\textbackslash fscy118})\text{\textbackslash t}(42, 83, \text{\textbackslash fscy152})\dots$$
2. **`[1.2] Current Value`:** Scalar value, ASS colour code, or alpha hex corresponding to the active timestamp (`frame_time` or `fx.start_time`).
3. **`[1.3] Values Array`:** List containing all sampled values across the full analysis window.
4. **`[1.4] Average RMS`:** Scalar average root-mean-square energy ($0.0 \dots 1.0$) across the window.

---

### 1.4. Mathematical Model and Modulation Algorithms

#### 1.4.1. $\mathcal{O}(1)$ RMS Energy Calculation (Prefix Sums)
Given normalised audio sample array $x \in [-1.0, 1.0]$ and cumulative squared sum vector $S_k = \sum_{j=0}^{k-1} x_j^2$:

$$\text{RMS}(t_0, t_1) = \sqrt{\frac{S_{\text{end}} - S_{\text{start}}}{\text{end} - \text{start}}} \cdot \text{Gain}$$

Where $\text{start} = \lfloor t_0 \cdot \frac{f_s}{1000} \rfloor$ and $\text{end} = \lfloor t_1 \cdot \frac{f_s}{1000} \rfloor$, with $f_s$ representing the PCM sample rate in Hz.

#### 1.4.2. Exponential Smoothing (Low-Pass Filter)
For a time series of raw energy intensities $I_0, I_1, \dots, I_N$:

$$S_0 = I_0$$
$$S_k = S_{k-1} + (1 - \alpha) \cdot (I_k - S_{k-1}) \quad \forall k \ge 1$$

Where $\alpha \in [0.0, 0.95]$ denotes the `smoothing` parameter.

#### 1.4.3. Polymorphic Colour Palette Interpolation
If the target tag is a colour tag (`\1c`, `\2c`, `\3c`, `\4c`) and an $M$-colour palette $[C_0, C_1, \dots, C_{M-1}]$ is specified:

$$p = \text{intensity} \cdot (M - 1), \quad \text{idx} = \lfloor p \rfloor, \quad f = p - \text{idx}$$
$$C(t) = C_{\text{idx}} + f \cdot (C_{\text{idx}+1} - C_{\text{idx}})$$

---

### 1.5. Production-Verified Example

Simultaneous modulation of vertical scale `\fscy` driven by bass (`bass`) and glow `\blur` driven by peak amplitude (`peak`):

```
[Audio/Modulator (mode: bass, tag: "fscy", min: 100, max: 155, gain: 1.2)] ──► [In1] ──┐
[Audio/Modulator (mode: peak, tag: "blur", min: 0.5, max: 5.0)]             ──► [In2] ──┼──► [Dynamic Format] ──► Output.Tags
```

* **Template in `Dynamic Format`:**
  ```text
  {\pos(syl.center, syl.middle)%s%s}
  ```
* **Resulting Compiled ASS Line:**
  ```ass
  Dialogue: 0,0:01:12.40,0:01:15.80,Romaji,,0,0,0,,{\pos(412.5, 680.0)\fscy100\t(0, 42, \fscy148)\t(42, 83, \fscy112)\blur0.5\t(0, 42, \blur4.2)\t(42, 83, \blur1.1)}Ka
  ```

---

## 2. Node `Audio/Waveform` (Vector Oscilloscopes and Spectrograms)

* **Canonical Category:** `Audio` (UI: *Audio / Waveform*)
* **Purpose:** Synthesises real-time ASSdraw vector paths (`m ... l ...`) representing the instantaneous acoustic signal. Allows rendering continuous ribbon oscilloscopes, spectral bar equalisers, baseline-filled waves, polar circular visualisers, and reactive particle matrices.

```
┌─────────────────────────────────────────────────────────────┐
│ Audio/Waveform                      [ Mode: oscilloscope v ]│
├─────────────────────────────────────────────────────────────┤
│ (o) [Audio Path]                                            │
│ (o) [Width]                   [ 400.0                     ] │
│ (o) [Height]                  [ 60.0                      ] │
│ (o) [Samples]                 [ 32                        ] │
│ (o) [Gain]                    [ 1.0                       ] │
│ (o) [Thickness]               [ 2.0                       ] │
│ (o) [Scale]                   [ 1.0                       ] │
│ (o) [Start Time]              [                           ] │
│ (o) [End Time]                [                           ] │
│                                             Shape Out [1.1] (o)
│                                              \pos Tag [1.2] (o)
│                                               X Array [1.3] (o)
│                                               Y Array [1.4] (o)
│                                           Bands Array [1.5] (o)
└─────────────────────────────────────────────────────────────┘
```

---

### 2.1. Header Mode Combos (*Graphic Topologies*)

```
1. Oscilloscope (Ribbon):            2. FFT Bars (Equaliser):
    ┌──┐   /\   ┌──┐                     ┌─┐   ┌─┐   ┌─┐
────┘  └──/  \──┘  └────                 │ │ ┌─┤ │ ┌─┤ │ ┌─┐
                                         │ │ │ │ │ │ │ │ │ │
3. Filled Wave (Baseline):           4. Radial (Polar Ring):
     /\     /\                                 ● ─── ●
    /  \   /  \                               /   ●   \
  ─/────\_/────\────────                     ●    |    ●
  ██████████████████████                      \   ●   /
                                               ● ─── ●
```

1. **`oscilloscope` (`Oscillo` / `Continuous Ribbon`):** Continuous ribbon vector path with uniform metric thickness (`Thickness`) following the temporal acoustic waveform.
2. **`fftbars` (`Bars` / `Spectrum Bars`):** Rectangular bar chart equaliser calculated via RFFT across frequency bands.
3. **`filledwave` (`Filled` / `Filled Wave`):** Continuous closed polygon connecting the wave contour to the bottom baseline.
4. **`radial` (`Radial` / `Circular Visualiser`):** Polar ring projection where frequencies or amplitudes modulate outer radius relative to the centre.
5. **`points` (`Points` / `Particle Cloud`):** Array of disconnected rectangles centred at each wave sample.

---

### 2.2. Input Ports and Body Properties (*Inputs & Properties*)
1. **`Audio Path` (`audio_path`):** Filesystem path to audio track or automatic resolution from Aegisub.
   * **Canonical Categorisation:** **Type C (Plain Text / Filepath)**.
2. **`Width` (`width`):** Total bounding box width in pixels (Default: `400.0 px`).
   * **Canonical Categorisation:** **Type A (Evaluated Expression)**.
3. **`Height` (`height`):** Maximum graphic height in pixels (Default: `60.0 px`).
   * **Canonical Categorisation:** **Type A (Evaluated Expression)**.
4. **`Samples` (`samples`):** Number of temporal samples or spectral bands ($4 \dots 512$, Default: `32`).
   * **Canonical Categorisation:** **Type A (Evaluated Expression)**.
5. **`Gain` (`gain`):** Amplitude scaling factor ($\ge 0.01$, Default: `1.0`).
   * **Canonical Categorisation:** **Type A (Evaluated Expression)**.
6. **`Thickness` (`thickness`):** Metric stroke width in pixels for `oscilloscope` and `points` modes ($\ge 1.0\text{ px}$, Default: `2.0 px`).
   * **Canonical Categorisation:** **Type A (Evaluated Expression)**.
7. **`Scale` (`scale`):** Vertical deflection or radial expansion multiplier ($\ge 0.01$, Default: `1.0`).
   * **Canonical Categorisation:** **Type A (Evaluated Expression)**.
8. **`Min Hz` / `Max Hz` (`min_hz`, `max_hz`):** Frequency range for FFT analysis in `fftbars` and `radial` modes ($20\text{ Hz} \dots 16000\text{ Hz}$).
   * **Canonical Categorisation:** **Type A (Evaluated Expression)**.
9. **`Start Time` / `End Time` (`start_time`, `end_time`):** Sample extraction time window in milliseconds.
   * **Canonical Categorisation:** **Type A (Evaluated Expression)**.

---

### 2.3. Output Ports (*Outputs*)
1. **`[1.1] Shape Out`:** Closed monolithic ASSdraw vector path (`m ... l ...`), ready to feed into `System/Output` or manipulate via `Shape` nodes.
2. **`[1.2] \pos Tag`:** ASS positioning tag calculated at geometric centre: `\pos(cx, cy)`.
3. **`[1.3] X Array`:** Array containing horizontal $X$ coordinates for all generated vertices.
4. **`[1.4] Y Array`:** Array containing vertical $Y$ coordinates for all generated vertices.
5. **`[1.5] Bands Array`:** Array containing normalised spectral amplitudes or energies ($0.0 \dots 1.0$) for each band.

---

### 2.4. Geometric Vector Construction Formulas

#### 2.4.1. `Oscilloscope` Topology (Dual-Polygon Ribbon)
For each temporal sample $s_i \in [-1.0, 1.0]$ with $i \in [0, N-1]$ and thickness $T$:

$$p_x(i) = \frac{i}{N - 1} \cdot W$$
$$p_y(i) = \frac{H}{2} - s_i \cdot \frac{H}{2} \cdot \text{Scale}$$
$$\text{Top}(i) = \left(p_x(i), p_y(i) - \frac{T}{2}\right), \quad \text{Bottom}(i) = \left(p_x(i), p_y(i) + \frac{T}{2}\right)$$

The vector path traverses all $\text{Top}$ points from left to right and returns across $\text{Bottom}$ points in reverse order:

$$\text{Shape} = \text{m } \text{Top}_0 \text{ l } \text{Top}_1 \dots \text{Top}_{N-1} \text{ l } \text{Bottom}_{N-1} \dots \text{Bottom}_0$$

#### 2.4.2. `Radial` Topology (Polar Projection)
For $N$ samples distributed uniformly around the circumference:

$$\theta_i = \frac{2\pi i}{N}, \quad R_i = R_{\text{base}} + \text{val}_i \cdot R_{\max} \cdot \text{Scale}$$
$$P_x(i) = c_x + R_i \cos(\theta_i), \quad P_y(i) = c_y + R_i \sin(\theta_i)$$

$$\text{Shape} = \text{m } P_0 \text{ l } P_1 \dots \text{ l } P_{N-1} \text{ l } P_0$$

#### 2.4.3. `FFT Bars` Topology (Equaliser)
For $N$ logarithmic bands with slot width $W_{\text{slot}} = \frac{W}{N}$ and bar width $W_{\text{bar}} = 0.8 \cdot W_{\text{slot}}$:

$$x_0(i) = i \cdot W_{\text{slot}}, \quad x_1(i) = x_0(i) + W_{\text{bar}}$$
$$h_i = \max(1.0, \min(H, \text{val}_i \cdot H \cdot \text{Scale}))$$
$$y_0 = H, \quad y_1(i) = H - h_i$$

Each bar is serialised as an independent closed rectangle:

$$\text{Bar}_i = \text{m } x_0(i) \text{ } y_0 \text{ l } x_0(i) \text{ } y_1(i) \text{ l } x_1(i) \text{ } y_1(i) \text{ l } x_1(i) \text{ } y_0$$

---

### 2.5. Production-Verified Example

Reactive spectral equaliser generated frame-by-frame (FBF) via `Loops/MaxLoop`:

* **Graph Connections:**
  ```
  [Loops/Main Loop (line)] ──► [Loops/MaxLoop (mode: fbf)] ──► [Audio/Waveform (mode: fftbars, samples: 16, width: 320, height: 40)] ──► Output.Tags
  ```
* **Resulting Compiled ASS Line (Frame 1):**
  ```ass
  Dialogue: 0,0:01:12.40,0:01:12.44,Romaji,,0,0,0,,{\an5\pos(640, 680)\p1\1c&H00FFFF&}m 0 40 l 0 18.2 l 16 18.2 l 16 40 m 20 40 l 20 8.5 l 36 8.5 l 36 40
  ```

---

### 2.6. Production FX Synergies

1. **Frame-by-Frame Sub-Loops (*FBF*) with `Loops/MaxLoop`:**
   Connecting `Loops/MaxLoop (fbf)` before `Audio/Waveform` dynamically updates `fx.start_time` and `fx.end_time` for each video frame, yielding latency-free reactive oscilloscopes.
2. **Dynamic Text Clipping with Waveforms (`\clip`):**
   Connecting `Shape Out` from `Audio/Waveform` to the `Clip` input of `Basics/MultiTag` or routing it through `Functions/Clip Gradient` creates dynamic clipping masks that reveal karaoke text in sync with musical beats.
3. **Audio-Reactive Particle Dispersion:**
   Connecting `Shape Out` to the `Path / Origin` input of `Functions/Particles` causes particle swarms to emit directly from acoustic wave crests and transients.

---

## 3. Comparative Matrix of Audio Nodes

| Parameter / Feature | `Audio/Modulator` | `Audio/Waveform` |
| :--- | :--- | :--- |
| **Primary Output Type** | Animated ASS Tag Chains (`\t`) | ASSdraw Vector Paths (`m...l...`) |
| **Analysis Domain** | RMS, Peak, Bass, Mids, Highs, Custom Band | Time Domain (PCM) and Frequency Domain (RFFT) |
| **Available Topologies** | Scalar / Colour / Alpha / `\t` Chains | Oscilloscope, FFT Bars, Filled, Radial, Points |
| **Colour Palette Support** | Yes (continuous RGB/Hex interpolation) | N/A (Pure vector geometry) |
| **FBF Compatibility** | Yes (via `Current Value` [Slot 1.2]) | Native (Generates distinct geometry per frame) |
| **Input Property Typing** | Type A (numerics/expressions), Type C (tags/paths)| Type A (dimensions/frequencies), Type C (paths/modes) |
| **Primary FX Use Case** | Glow, bounce, scale, and colour pulsating to music | Visual equalisers, oscilloscopes, and reactive backdrops |
