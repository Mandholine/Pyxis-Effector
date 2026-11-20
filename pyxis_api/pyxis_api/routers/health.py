# -*- coding: utf-8 -*-
from fastapi import APIRouter

import pyxis_core

from .. import __version__

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    return {"status": "ok", "api": __version__, "pyxis_core": pyxis_core.__version__}
