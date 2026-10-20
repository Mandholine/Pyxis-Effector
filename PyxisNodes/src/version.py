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
# For any question you can visit: https://discord.gg/fsxRESeQZN

"""Canonical version definition and metadata for Pyxis Effector.

Serves as the Single Source of Truth (SSOT) for the Python backend runtime,
IPC daemon, PyWebView window titles, and client authentication tokens.
"""

PYXIS_VERSION = "1.1.5"
PYXIS_STAGE = "Beta"
PYXIS_STAGE_SHORT = "beta"

PYXIS_VERSION_STRING = f"v{PYXIS_VERSION}"
PYXIS_FULL_VERSION = f"{PYXIS_STAGE} v{PYXIS_VERSION}"
PYXIS_APP_ID = f"Mandholine.Pyxis.NodeEngine.{PYXIS_VERSION}"
PYXIS_CLIENT_AUTH = f"pyxis-{PYXIS_STAGE_SHORT}-{PYXIS_VERSION}-client"


def get_version_dict():
    """Returns a dictionary containing all canonical version identifiers.

    Returns:
        dict: Version properties including version number, stage, and formatted strings.
    """
    return {
        "version": PYXIS_VERSION,
        "stage": PYXIS_STAGE,
        "stage_short": PYXIS_STAGE_SHORT,
        "version_string": PYXIS_VERSION_STRING,
        "full_version": PYXIS_FULL_VERSION,
        "app_id": PYXIS_APP_ID,
        "client_auth": PYXIS_CLIENT_AUTH,
    }
