# -*- coding: utf-8 -*-
# Los datos de usuario (plantillas, libreria propia) se aislan ANTES de importar la API.
import os
import tempfile

os.environ["XDG_DATA_HOME"] = tempfile.mkdtemp(prefix="pyxis_api_test_")
