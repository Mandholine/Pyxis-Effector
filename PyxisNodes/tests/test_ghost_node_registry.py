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

# PyxisNodes/tests/test_ghost_node_registry.py
"""
Suite de Pruebas Reutilizable para Detectar Asignaciones y Nodos Fantasma en PyxisNodes.
Examina automáticamente los decoradores @pyxis_node, system_node(), NODE_REGISTRY y web/index.html.
"""

import unittest
import os
import re

# Categorías y rutas desaprobadas (legacy/fantasmas) que NO deben registrarse en el sistema
DISALLOWED_GHOST_PREFIXES = [
    "Shape/Formas/",
    "Shape/Estrellas/",
    "Shape/Especiales/",
    "Shape/Notas/",
    "Shape/Sakura/",
    "Shape/Corte/",
    "Text/Operaciones/",
    "Text/Especial/",
    "Texto/",
    "Tags/Tag Oscilador",
    "Time/Operaciones/"
]

class TestGhostNodeRegistry(unittest.TestCase):
    def setUp(self):
        self.base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.nodes_dir = os.path.join(self.base_dir, "nodes")
        self.nodes_lib_path = os.path.join(self.base_dir, "nodes_library.py")
        self.index_html_path = os.path.join(self.base_dir, "web", "index.html")

    def test_no_ghost_decorators_in_nodes_directory(self):
        """Verifica que ningún archivo en nodes/ contenga decoradores @pyxis_node con categorías desaprobadas."""
        ghosts_found = []
        
        for fname in os.listdir(self.nodes_dir):
            if fname.endswith(".py"):
                fpath = os.path.join(self.nodes_dir, fname)
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                matches = re.findall(r'@pyxis_node\(\s*["\']([^"\']*)["\']\s*,\s*["\']([^"\']*)["\']', content)
                for cat, name in matches:
                    full_key = f"{cat}/{name}" if cat else name
                    for ghost_prefix in DISALLOWED_GHOST_PREFIXES:
                        if full_key.startswith(ghost_prefix) or (cat + "/").startswith(ghost_prefix):
                            ghosts_found.append(f"{fname} -> {full_key}")

        self.assertEqual(len(ghosts_found), 0, f"Se encontraron decoradores fantasma en nodes/: {ghosts_found}")

    def test_no_ghost_nodes_in_nodes_library(self):
        """Verifica que nodes_library.py no contenga llamadas system_node() con categorías desaprobadas."""
        ghosts_found = []
        with open(self.nodes_lib_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        matches = re.findall(r'system_node\(\s*["\']([^"\']*)["\']\s*,\s*["\']([^"\']*)["\']', content)
        for cat, name in matches:
            full_key = f"{cat}/{name}" if cat else name
            for ghost_prefix in DISALLOWED_GHOST_PREFIXES:
                if full_key.startswith(ghost_prefix) or (cat + "/").startswith(ghost_prefix):
                    ghosts_found.append(f"nodes_library.py -> {full_key}")

        self.assertEqual(len(ghosts_found), 0, f"Se encontraron registros system_node fantasma: {ghosts_found}")

    def test_node_registry_dict_cleanliness(self):
        """Verifica que el diccionario global NODE_REGISTRY de Python no contenga claves fantasma."""
        from decorators import NODE_REGISTRY
        
        # Importar dinámicamente todos los módulos de nodos para poblar NODE_REGISTRY
        import nodes.shape_nodes
        import nodes.text_nodes
        import nodes.tag_nodes
        import nodes.time_nodes
        import nodes.variable_nodes

        ghosts_found = []
        for reg_key in NODE_REGISTRY.keys():
            for ghost_prefix in DISALLOWED_GHOST_PREFIXES:
                if reg_key.startswith(ghost_prefix):
                    ghosts_found.append(reg_key)

        self.assertEqual(len(ghosts_found), 0, f"Se encontraron registros en NODE_REGISTRY desaprobados: {ghosts_found}")

    def test_web_index_html_has_wildcard_ghost_cleanup(self):
        """Verifica que web/index.html contenga la lógica de limpieza de prefijos desaprobados en registerSystemNodes."""
        with open(self.index_html_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()

        self.assertIn("k.startsWith(\"Shape/Formas/\")", content, "Falta la limpieza de Shape/Formas/ en index.html")
        self.assertIn("k.startsWith(\"Shape/Estrellas/\")", content, "Falta la limpieza de Shape/Estrellas/ en index.html")
        self.assertIn("k.startsWith(\"Text/Operaciones/\")", content, "Falta la limpieza de Text/Operaciones/ en index.html")

if __name__ == "__main__":
    unittest.main()
