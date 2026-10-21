# Guía de Publicación en PyPI (Publishing Guide)

Esta guía explica el procedimiento estándar para empaquetar, validar y publicar `pyxis-core` en **PyPI** (Python Package Index) o **TestPyPI**.

---

## 📋 Requisitos Previos

Asegúrate de contar con las herramientas modernas de empaquetado de Python instaladas:

```bash
python3 -m pip install --upgrade build twine
```

También necesitarás una cuenta en [PyPI](https://pypi.org) (y opcionalmente en [TestPyPI](https://test.pypi.org)) y un **API Token** generado desde tu panel de usuario:
1. Accede a **Account Settings** > **API tokens**.
2. Haz clic en **Add API token**.
3. Guarda el token con formato `pypi-AgEI...`.

---

## 🧹 1. Limpieza de Builds Anteriores

Antes de compilar una nueva versión, elimina los directorios temporales de compilación y dist anteriores:

```bash
cd pyxis_core
rm -rf dist/ build/ *.egg-info
```

---

## 🧪 2. Ejecutar Pruebas Automatizadas

Verifica que todos los tests pasen exitosamente:

```bash
python3 -m pytest tests/
```

Deberás observar `8 passed` (o más).

---

## 🔨 3. Compilar la Distribución (`sdist` y `wheel`)

Ejecuta el constructor estándar de Python:

```bash
python3 -m build
```

Esto generará en la carpeta `dist/`:
- `pyxis_core-0.1.0.tar.gz` (Source distribution - código fuente completo con templates y data)
- `pyxis_core-0.1.0-py3-none-any.whl` (Wheel binario listo para instalación rápida vía `pip`)

---

## 🔍 4. Validar los Archivos Generados con Twine

Antes de intentar subir a PyPI, valida los metadatos y la sintaxis del README:

```bash
python3 -m twine check dist/*
```

**Salida esperada:**
```text
Checking dist/pyxis_core-0.1.0-py3-none-any.whl: PASSED
Checking dist/pyxis_core-0.1.0.tar.gz: PASSED
```

---

## 🚀 5. Publicación de Prueba en TestPyPI (Recomendado)

Sube primero el paquete al entorno de pruebas:

```bash
python3 -m twine upload --repository testpypi dist/*
```

Cuando te pida credenciales:
- **Username:** `__token__`
- **Password:** Pega tu API token de TestPyPI (`pypi-...`).

### Probar la instalación desde TestPyPI:

```bash
python3 -m pip install --index-url https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ pyxis-core
```

---

## 🌐 6. Publicación Oficial en Producción (PyPI)

Cuando hayas validado que la instalación funciona correctamente:

```bash
python3 -m twine upload dist/*
```

Ingresa tus credenciales:
- **Username:** `__token__`
- **Password:** Pega tu API token oficial de PyPI.

¡Listo! En cuestión de segundos tu paquete estará visible públicamente en:
`https://pypi.org/project/pyxis-core/`

Y cualquier persona en el mundo podrá instalarlo con:
```bash
pip install pyxis-core
```

---

## 🔄 Automatización con GitHub Actions (Opcional)

Si utilizas GitHub, puedes configurar un workflow en `.github/workflows/publish-pypi.yml` para publicar automáticamente cada vez que crees un nuevo Release o tag `v*.*.*`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  pypi-publish:
    name: Upload release to PyPI
    runs-on: ubuntu-latest
    permissions:
      id-token: write
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.10"
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install build
      - name: Build package
        run: |
          cd pyxis_core
          python -m build
      - name: Publish package distributions to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
        with:
          packages-dir: pyxis_core/dist/
```
