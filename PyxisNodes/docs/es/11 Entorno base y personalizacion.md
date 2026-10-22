# Entorno Base y Personalización

El **Entorno Base** (`preview_base.ass`) proporciona un espacio de trabajo aislado para previsualizar y validar efectos sin depender del archivo de subtítulos principal cargado en Aegisub.
Documenta el ciclo de vida del archivo en `%APPDATA%`, el modelo de ventana temporal del clip, su estructura de estilos y su recarga reactiva.

---

## 1. Arquitectura y Modos de Previsualización

El nodo **`System/Previewer`** cuenta con un selector de origen que conmuta entre dos modos operativos:

* **Modo Proyecto Activo (Icono Aegisub):** Conecta el reproductor en tiempo real al vídeo, audio, estilos y líneas de diálogo actualmente cargadas en la sesión de Aegisub.
* **Modo Plantilla Base (Icono Disco CD):** Desvincula temporalmente el reproductor del archivo de Aegisub y proyecta el efecto sobre el archivo `preview_base.ass` en un entorno de laboratorio estandarizado y reproducible.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          MODOS DE PREVISUALIZACIÓN                          │
├──────────────────────────────────────┬──────────────────────────────────────┤
│                                      │                                      │
│                 ┌────────────────────┴────────────────────┐                 │
│                 ▼                                         ▼                 │
│  ┌──────────────────────────────┐       ┌────────────────────────────────┐  │
│  │   MODO AEGISUB (Icono Aegi)  │       │   MODO BASE (Icono Disco CD)   │  │
│  │   • Script de trabajo activo │       │   • Sandbox aislado %APPDATA%  │  │
│  │   • Vídeo/Audio del proyecto │       │   • Media de laboratorio fija  │  │
│  │   • Diálogos reales activos  │       │   • Karaoke patrón controlado  │  │
│  └──────────────────────────────┘       └────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Ciclo de Vida y Persistencia en `%APPDATA%`

### 2.1. Ubicación Física en el Sistema Operativo
El archivo base reside en el directorio de configuración de usuario de Windows:

```
%APPDATA%\PyxisNodes\preview_base.ass
```

*(Ruta estándar: `C:\Users\<Usuario>\AppData\Roaming\PyxisNodes\preview_base.ass`)*.

### 2.2. Política de Preservación e Inviolabilidad
Pyxis Effector aplica una política de no sobrescritura sobre los datos de usuario:
1. **Primera Ejecución:** Si el archivo no existe en `%APPDATA%\PyxisNodes\`, el motor copia automáticamente la plantilla maestra de fábrica incluida en el paquete de distribución.
2. **Actualizaciones de Versión:** Una vez generado, **Pyxis jamás sobrescribe ni elimina este archivo**. Todas las personalizaciones de estilos, resoluciones, enlaces de vídeo y textos de prueba pertenecen de forma exclusiva al usuario y persisten entre actualizaciones del software.

### 2.3. Detección Reactiva por Hash SHA-256 (Recarga en Caliente)
Para evitar la necesidad de reiniciar la aplicación o reinstanciar el nodo `System/Previewer` al modificar el entorno base, el backend inspecciona la firma criptográfica del archivo:
* En cada compilación de previsualización, el motor calcula el hash `SHA-256` del archivo en disco.
* Si el usuario edita y guarda `preview_base.ass` en Aegisub o en un editor de texto externo, el cambio de hash invalida automáticamente la caché en memoria (`_cached_preview_base_info`).
* El visor actualiza inmediatamente la resolución nativa, la tasa de fotogramas, la pista sonora y la geometría tipográfica en caliente.

---

## 3. Modelo Matemático de la Ventana Temporal del Clip

El motor de Pyxis no limita la reproducción a la duración estricta de las sílabas del archivo base; calcula dinámicamente una **ventana temporal con colchón (*Lead-In / Lead-Out Buffer*)** para permitir la evaluación completa de transiciones de entrada y salida:

### 3.1. Ecuaciones de Ventana Temporal

Sea $\mathcal{D} = \{d_1, d_2, \dots, d_m\}$ el conjunto de líneas de diálogo presentes en `preview_base.ass`, donde cada línea posee una marca de inicio $t_{\text{start}}(d_i)$ y de fin $t_{\text{end}}(d_i)$ en milisegundos:

$$t_{\text{min}} = \min_{d \in \mathcal{D}} \big(t_{\text{start}}(d)\big)$$

$$t_{\text{max}} = \max_{d \in \mathcal{D}} \big(t_{\text{end}}(d)\big)$$

A partir de estos extremos, el motor establece los límites de reproducción del clip en segundos:

$$t_{\text{clip\_start}} = \max\left(0.0, \; \frac{t_{\text{min}} - 2000}{1000.0}\right)$$

$$t_{\text{clip\_end}} = \frac{t_{\text{max}} + 2000}{1000.0}$$

$$T_{\text{clip\_dur}} = \max\left(2.0, \; t_{\text{clip\_end}} - t_{\text{clip\_start}}\right)$$

$$t_{\text{clip\_start\_ms}} = \lfloor t_{\text{clip\_start}} \times 1000 \rfloor$$

### 3.2. Función Cinemática del Colchón de 2000 ms
* **Evaluación de Nodos `Time/Lead In`:** Las animaciones espaciales que inician antes de la sílaba (ej. aproximaciones desde fuera de pantalla, aceleraciones exponenciales `accel` o apariciones progresivas) disponen de hasta 2000 ms previos para desarrollarse fluidamente.
* **Evaluación de Nodos `Time/Lead Out`:** Los desvanecimientos posteriores (`\fad`, dispersión de partículas, disolución alfa) disponen de 2000 ms posteriores antes del corte del bucle de reproducción.
* **Mapeo Relativo en el Scrubber:** La barra de transporte del nodo `Previewer` mapea el tiempo $00:00$ exactamente a $t_{\text{clip\_start\_ms}}$, garantizando que el usuario analice el intervalo relevante sin tiempos muertos iniciales del archivo de vídeo.

---

## 4. Anatomía y Estructura del Archivo `preview_base.ass`

El archivo `preview_base.ass` es un documento estándar de subtítulos ASS (*v4.00+*). Se divide en cuatro secciones operativas fundamentales:

```ini
[Script Info]
; Configuración global de lienzo y resolución
Title: Default Aegisub file
ScriptType: v4.00+
WrapStyle: 0
ScaledBorderAndShadow: yes
YCbCr Matrix: None
PlayResX: 1000
PlayResY: 260

[Aegisub Project Garbage]
; Vinculación de fuentes multimedia (Vídeo y Audio)
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

## 5. Guía de Personalización Técnica

### 5.1. Paso 1: Configurar la Resolución del Lienzo (`PlayResX` / `PlayResY`)
La resolución del encabezado define el sistema de coordenadas cartesianas sobre el cual se calculan los anclajes absolutos y relativos:
* **Resolución Full HD (1080p):**
  ```ini
  PlayResX: 1920
  PlayResY: 1080
  ```
* **Resolución HD Estándar (720p):**
  ```ini
  PlayResX: 1280
  PlayResY: 720
  ```
> [!NOTE]
> El motor de previsualización WebAssembly (`JASSUB`) y el reproductor de vídeo adaptan automáticamente la relación de aspecto ($\text{AR} = \text{PlayResX} / \text{PlayResY}$) y escalan los fotogramas para mantener las proporciones exactas sin distorsión anamórfica.

### 5.2. Paso 2: Configurar Fuentes Multimedia de Referencia
En la sección `[Aegisub Project Garbage]`, se pueden vincular dos tipos de fuentes:

#### Opción A: Vídeo Virtual Sintético (*Dummy Video* - Recomendado)
No requiere almacenar archivos de vídeo en disco y garantiza inicialización inmediata a 23.976 o 60 FPS:
```ini
Video File: ?dummy:23.976000:40000:1920:1080:26:26:26:
```
* **Sintaxis:** `?dummy:<FPS>:<Fotogramas>:<Ancho>:<Alto>:<R>:<G>:<B>:`
* Los valores `26:26:26:` generan un fondo gris oscuro neutro que proporciona alto contraste visual para partículas blancas, sombras y contornos coloreados.

#### Opción B: Archivos Locales de Vídeo y Audio
Cuando se requiera calibrar sincronismo labial, modulación acústica con `Audio/Modulator` o transitorios con `Audio/Waveform`, apunte a archivos multimedia locales:
```ini
Video File: C:\KaraokeResources\test_track_1080p.mp4
Audio File: C:\KaraokeResources\test_track_1080p.mp4
```
> [!TIP]
> Si el archivo de vídeo contiene una pista de audio integrada, basta con declarar la ruta en `Video File`; Pyxis extraerá y enrutará automáticamente el flujo sonoro al motor PCM y al modulador espectral.

### 5.3. Paso 3: Calibrar Estilos Tipográficos (`[V4+ Styles]`)
Pyxis inspecciona la sección `[V4+ Styles]` y extrae el **primer estilo definido** como estilo maestro por defecto:
* **`Fontname`:** Familia tipográfica instalada en el sistema o alojada en `%APPDATA%\PyxisNodes\fonts\`.
* **`Fontsize`:** Altura de referencia en píxeles de guion (ej. `65` a `80` para 1080p).
* **`PrimaryColour` (`&HAABBGGRR&`):** Color del cuerpo del glifo.
* **`Outline` y `OutlineColour`:** Grosor métrico y color del contorno inicial.
* **`Alignment`:** Anclaje estándar ASS (`5` para centro exacto en pantalla o `2` para subtítulos inferiores).

### 5.4. Paso 4: Definir la Frase de Prueba en `[Events]`
La línea de diálogo base debe contener una variedad equilibrada de sílabas para probar diferentes condiciones geométricas:
```ini
Dialogue: 0,0:00:03.00,0:00:09.00,Default,,0,0,0,,{\k45}Kyou{\k40}kai {\k60}no {\k50}Ka{\k55}na{\k70}ta
```
* **Sílabas cortas ($\le 200\text{ ms}$):** Ideales para validar impactos de alta velocidad, transiciones rápidas (*snap eases*) y rebotes elásticos (*Bounce* / *elastic rebounds*).
* **Sílabas largas ($\ge 600\text{ ms}$):** Ideales para observar osciladores continuos (`Tag Oscillator`), gradientes dinámicos o emisiones de partículas sostenidas.
* **Complejidad glífica:** Incluir kanjis densos si se trabaja con morfología vectorial o caracteres con islas cerradas (ej. `B`, `P`, `o`, `8`) para verificar operaciones booleanas de unión y corte en Clipper2, así como la orientación y reglas de devanado (*winding rules*) de los polígonos.

---

## 6. Plantilla Maestra Full HD 1080p de Referencia

A continuación se proporciona una plantilla de `preview_base.ass` configurada para resolución Full HD 1080p a 23.976 FPS con fondo neutro de alto contraste:

```ini
[Script Info]
; Archivo Base Personalizado de Laboratorio - Pyxis Effector
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

## 7. Buenas Prácticas de Flujo de Trabajo

1. **Uso de Vídeos Virtuales para Compartir Plantillas:**
   * Al exportar grafos o plantillas para otros usuarios, mantenga el vídeo en modo `?dummy:...`. De este modo, cualquier diseñador podrá abrir la plantilla y previsualizarla sin requerir rutas absolutas de vídeo inexistentes en su máquina.
2. **Pruebas Tipográficas con Fuentes Locales:**
   * Al diseñar con tipografías experimentales, ubique los archivos `.ttf` o `.otf` en `%APPDATA%\PyxisNodes\fonts\`. Pyxis vectoriza y renderiza estas fuentes localmente mediante FreeType/HarfBuzz y libass sin exigir su instalación en el sistema operativo Windows.
3. **Procedimiento de Restablecimiento de Fábrica:**
   * Para restaurar el archivo base a su configuración original de fábrica, cierre Pyxis Effector, elimine `%APPDATA%\PyxisNodes\preview_base.ass` y reinicie la aplicación; el motor regenerará una copia limpia automáticamente.
