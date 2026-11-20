# pyxis_api

API local (FastAPI) de Pyxis Effector. Expone la librería `pyxis-core` a la app Flutter **Pyxis Studio** y al macro de Aegisub.

```bash
python3 -m venv .venv && .venv/bin/pip install -e ../pyxis_core -e ".[test]"
.venv/bin/python -m pyxis_api --port 28723        # docs interactivas: http://127.0.0.1:28723/docs
.venv/bin/python -m pytest tests
```

Variables: `PYXIS_WORKSPACE` (por defecto `~/PyxisEffects`: efectos `.py` y `effect_base.py`), `XDG_DATA_HOME` (plantillas y librería del usuario).

## Endpoints (`/api/v1`)

| Módulo | Rutas |
|---|---|
| health | `GET /health` |
| nodes | `GET /nodes/manifest`, `GET /nodes/categories` (catálogo para la paleta) |
| graph | `POST /graph/validate`, `POST /graph/process`, `POST /graph/abort`, `WS /graph/ws/progress` |
| templates | `GET/POST /templates`, `GET/DELETE /templates/{id}` |
| fx | `GET /fx/kinds`, `GET /fx?kind=&q=&status=&only_supported=`, `GET /fx/{kind}/{name}/source` (3.946 efectos de Kara Effector 3.6) |
| effects | `GET/POST /effects`, `GET/PUT/DELETE /effects/{name}` (scripts Python del usuario) |
| session | `POST /session/open`, `GET /session/info`, `POST /session/shutdown` |

El grafo viaja en el mismo JSON que usa el motor (`nodes` + `links`). Ver `PLAN_API_FLUTTER.md` en la raíz.
