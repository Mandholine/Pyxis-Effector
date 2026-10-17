# Pyxis Effector - Plugin for Aegisub
# Copyright (C) 2026 @mandholine, @effector2, @pholguinc
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation version 3.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <https://www.gnu.org/licenses/>.
# For any question you can visit: https://discord.gg/rYsARc3fB9

"""Gestor canónico de rutas y resolución de binarios/assets de Pyxis Effector."""

import os
import shutil
import sys

SRC_DIR = os.path.dirname(os.path.abspath(__file__))
PYXIS_ROOT_DIR = os.path.dirname(SRC_DIR)
BIN_DIR = os.path.join(PYXIS_ROOT_DIR, "bin")
WEB_DIR = os.path.join(PYXIS_ROOT_DIR, "web")
DOCS_DIR = os.path.join(PYXIS_ROOT_DIR, "docs")
TEMPLATES_DIR = os.path.join(PYXIS_ROOT_DIR, "templates")
PREVIEW_BASE_ASS = os.path.join(PYXIS_ROOT_DIR, "preview_base.ass")

IS_WINDOWS = os.name == "nt"


def get_user_data_dir() -> str:
    """Retorna el directorio de datos por usuario de PyxisNodes.

    Windows: %APPDATA%\\PyxisNodes (comportamiento histórico intacto).
    Linux/macOS: $XDG_DATA_HOME/PyxisNodes o ~/.local/share/PyxisNodes.
    """
    if IS_WINDOWS:
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    else:
        base = os.environ.get("XDG_DATA_HOME") or os.path.join(os.path.expanduser("~"), ".local", "share")
    return os.path.join(base, "PyxisNodes")


def get_bin_path(binary_name: str) -> str:
    """Retorna la ruta absoluta a un binario buscando en bin/, luego en la raíz, o en el PATH del sistema.

    En Windows se busca con sufijo .exe; en Linux/macOS se acepta tanto el nombre
    con .exe (binarios empaquetados) como el equivalente nativo sin sufijo.
    """
    if IS_WINDOWS:
        names = [f"{binary_name}.exe"] if not binary_name.lower().endswith(".exe") else [binary_name]
    else:
        names = []
        if binary_name.lower().endswith(".exe"):
            names.append(binary_name[:-4])
        names.append(binary_name)

    fallback_target = None
    for exe_name in names:
        # 1. Buscar en bin/
        bin_target = os.path.join(BIN_DIR, exe_name)
        if fallback_target is None:
            fallback_target = bin_target
        if os.path.exists(bin_target):
            return bin_target

        # 2. Buscar en la raíz de PyxisNodes
        root_target = os.path.join(PYXIS_ROOT_DIR, exe_name)
        if os.path.exists(root_target):
            return root_target

        # 3. Buscar en el PATH del sistema
        system_path = shutil.which(exe_name)
        if system_path:
            return system_path

    # Fallback al target en bin/
    return fallback_target


def get_web_path(resource: str = "") -> str:
    """Retorna la ruta absoluta a la carpeta web/ o un recurso interno."""
    if resource:
        return os.path.join(WEB_DIR, resource)
    return WEB_DIR


def get_docs_path(resource: str = "") -> str:
    """Retorna la ruta absoluta a la carpeta docs/ o un documento interno."""
    if resource:
        return os.path.join(DOCS_DIR, resource)
    return DOCS_DIR


def get_templates_path(resource: str = "") -> str:
    """Retorna la ruta absoluta a la carpeta templates/ o un template interno."""
    if resource:
        return os.path.join(TEMPLATES_DIR, resource)
    return TEMPLATES_DIR
