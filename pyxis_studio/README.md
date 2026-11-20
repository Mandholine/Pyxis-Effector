# Pyxis Studio

App de escritorio (Flutter: macOS, Windows, Linux) para crear efectos **por nodos**. Habla con `pyxis_api` (FastAPI sobre `pyxis-core`).

- **Paleta** de nodos por categoría (catálogo de la API), **lienzo** con enlaces (arrastra de una salida a una entrada, rueda = zoom,
  Supr = borrar), **inspector** de propiedades, plantillas (abrir/guardar), **Validar** y **Ejecutar** con progreso y cancelación.
- Al ejecutar escribe el resultado en `<ass>.pyxis.ass`; el macro de Aegisub lo importa al cerrar la app.

```bash
flutter pub get && flutter test
flutter run -d macos            # con la API en marcha: python -m pyxis_api
flutter build macos --release   # build/macos/Build/Products/Release/pyxis_studio.app
```

`PYXIS_API` cambia la URL de la API (por defecto `http://127.0.0.1:28723`). Normalmente la lanza el macro **Pyxis Effect Studio**
eligiendo el modo **Nodos**: arranca la API, abre la sesión con el `.ass`, abre esta app y, al cerrarla, apaga la API.
