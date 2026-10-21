# potrace_native — Motor Nativo de Vectorización de Imágenes y Formas ASS

Esta carpeta contiene las herramientas nativas en C99 de vectorización para **Pyxis Effector**:
1. **`img2ass`**: Conversor nativo directo de imágenes (PNG con canal alfa, JPG, BMP, WebP) a subtítulos vectoriales **Aegisub ASSDraw** conforme a la especificación técnica de Pyxis (Sección 12: *Shape/IMG to Shape*).
2. **`potrace`**: Binario oficial de **Potrace 1.16** con backend nativo ASS (`-b ass`) y SVG (`--svg`).

---

## 🚀 Compilación Nativa en 1 Segundo

Ejecuta el script incluido:

```bash
cd pyxis_core/pyxis_core/infrastructure/engine/bin/potrace_native
./build.sh
```

El script compila automáticamente usando `clang` (en macOS) o `gcc` (en Linux/Windows) y genera los ejecutables nativos en `bin/`:
- `pyxis_core/pyxis_core/infrastructure/engine/bin/img2ass`
- `pyxis_core/pyxis_core/infrastructure/engine/bin/potrace`

---

## 🎨 Uso conforme a la Documentación Técnica (Sección 12: Shape/IMG to Shape)

### 1. Vectorización directa para Aegisub (Sin dependencias de Python ni herramientas externas)
```bash
cd pyxis_core/pyxis_core/infrastructure/engine/bin

# Vectorizar payasito.png directamente a payasito.ass:
./img2ass images/payasito.png payasito.ass
```
El archivo `payasito.ass` generado incluye automáticamente el tag de producción especificado en la sección 12.6:
```ass
{\p1\pos(960,540)\1c&HFFFFFF&\bord0}m ... b ...{\p0}
```

### 2. Opciones avanzadas (Idénticas a las propiedades del nodo):
```bash
# Modo silueta para extraer el cuerpo completo opaco
./img2ass images/payasito.png payasito.ass --bin_mode silhouette

# Ajustar umbral de corte, tolerancia y suavizado de esquinas
./img2ass images/payasito.png payasito.ass --threshold 140 --tolerance 1.5 --alphamax 1.0

# Cambiar posición de pantalla o escala
./img2ass images/payasito.png payasito.ass --pos 1280 720 --scale 1.5

# Emitir sólo la cadena vectorial ASSDraw pura ('m ... b ...')
./img2ass images/payasito.png --raw
```
