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

"""Pruebas unitarias para el almacenamiento, versionado y metadatos de plantillas (TemplateStore)."""

import os
import tempfile
import unittest
from template_store import TemplateStore, PYXIS_ENGINE_VERSION


class TestTemplateStore(unittest.TestCase):
    """Pruebas de operaciones CRUD y metadatos en TemplateStore."""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.store = TemplateStore(templates_dir=self.temp_dir, aegisub_version="3.4.2")
        self.sample_graph = {
            "nodes": [
                {"id": 1, "type": "Loops/Main Loop", "properties": {}},
                {"id": 2, "type": "String", "properties": {"valor": "Test"}}
            ],
            "links": []
        }

    def test_save_and_load_template(self):
        meta = self.store.save_template(
            name="Mi Efecto Especial",
            comment="Efecto de prueba unitaria",
            graph_data=self.sample_graph
        )
        self.assertEqual(meta["name"], "Mi Efecto Especial")
        self.assertEqual(meta["pyxis_engine_version"], PYXIS_ENGINE_VERSION)
        self.assertEqual(meta["node_count"], 2)

        # Listar plantillas
        templates = self.store.list_templates()
        self.assertEqual(len(templates), 1)
        self.assertEqual(templates[0]["name"], "Mi Efecto Especial")

    def test_load_template_content(self):
        meta = self.store.save_template(
            name="Template Para Carga",
            comment="",
            graph_data=self.sample_graph
        )
        t_id = meta["template_id"]
        loaded = self.store.load_template(t_id)
        self.assertIn("graph", loaded)
        self.assertEqual(len(loaded["graph"]["nodes"]), 2)

    def test_delete_template(self):
        meta = self.store.save_template(
            name="Para Borrar",
            comment="",
            graph_data=self.sample_graph
        )
        t_id = meta["template_id"]
        self.assertEqual(len(self.store.list_templates()), 1)

        self.store.delete_template(t_id)
        self.assertEqual(len(self.store.list_templates()), 0)


if __name__ == "__main__":
    unittest.main()
