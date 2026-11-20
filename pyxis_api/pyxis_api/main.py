# -*- coding: utf-8 -*-
"""Aplicacion FastAPI de Pyxis Effector (consumida por la app Flutter «Pyxis Studio» y por el macro de Aegisub)."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import __version__
from .routers import cache, effects, fx, graph, health, nodes, session, templates

app = FastAPI(title="Pyxis API", version=__version__,
              description="Servicios de Pyxis Effector sobre pyxis-core: grafos de nodos, plantillas, libreria de efectos y scripts.")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

PREFIX = "/api/v1"
for r in (health.router, nodes.router, graph.router, templates.router, fx.router, effects.router, session.router, cache.router):
    app.include_router(r, prefix=PREFIX)
