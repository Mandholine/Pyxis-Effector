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

import json
import tempfile
import unittest
from pathlib import Path

from template_store import TemplateStore


class TemplateStoreTests(unittest.TestCase):
    def test_save_list_load_and_delete(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = TemplateStore(Path(temp_dir) / "templates", "3.4.2")
            graph = {
                "last_node_id": 2,
                "last_link_id": 1,
                "nodes": [
                    {
                        "id": 1,
                        "type": "Loops/Main Loop",
                        "pos": [200, 250],
                        "size": [140, 80],
                        "flags": {"collapsed": True},
                        "properties": {"iterador": "syl"},
                    }
                ],
                "links": [],
            }

            saved = store.save_template("Fade / Sílaba", "Prueba", graph)
            self.assertEqual(saved["name"], "Fade / Sílaba")
            self.assertEqual(saved["node_count"], 1)
            self.assertEqual(saved["aegisub_version"], "3.4.2")

            listed = store.list_templates()
            self.assertEqual(len(listed), 1)
            self.assertEqual(listed[0]["template_id"], saved["template_id"])

            loaded = store.load_template(saved["template_id"])
            self.assertEqual(loaded["graph"], graph)
            self.assertTrue(loaded["graph"]["nodes"][0]["flags"]["collapsed"])

            template_file = next(Path(temp_dir).glob("templates/*.json"))
            json.loads(template_file.read_text(encoding="utf-8"))

            # Validar que un grafo vacío o inválido lanza error
            from template_store import TemplateStoreError
            with self.assertRaises(TemplateStoreError):
                store.save_template("Vacío", "", {"nodes": []})

            store.delete_template(saved["template_id"])
            self.assertEqual(store.list_templates(), [])

    def test_overwrite_favorite_and_migration(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            store = TemplateStore(Path(temp_dir) / "templates", "3.4.2")
            graph = {"nodes": [{"id": 1, "type": "Loops/Main Loop"}]}

            saved = store.save_template("Original", "Comentario", graph)
            template_id = saved["template_id"]
            created_at = saved["created_at"]

            # Toggle favorite
            new_fav = store.toggle_favorite(template_id)
            self.assertTrue(new_fav)

            # Overwrite template
            updated_graph = {"nodes": [{"id": 1, "type": "Loops/Main Loop"}, {"id": 2, "type": "System/Output"}]}
            overwritten = store.save_template("Original Editado", "Nuevo comentario", updated_graph, template_id=template_id)

            self.assertEqual(overwritten["template_id"], template_id)
            self.assertEqual(overwritten["name"], "Original Editado")
            self.assertEqual(overwritten["node_count"], 2)
            self.assertEqual(overwritten["created_at"], created_at)
            self.assertTrue(overwritten["is_favorite"])

            # Verify only one template file exists
            files = [f for f in (Path(temp_dir) / "templates").glob("*.json") if not f.name.startswith(".")]
            self.assertEqual(len(files), 1)

    def test_schema_migration(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            templates_dir = Path(temp_dir) / "templates"
            store = TemplateStore(templates_dir, "3.4.2")

            # Create a legacy single file document with schema_version 0
            templates_dir.mkdir(parents=True, exist_ok=True)
            doc_file = templates_dir / "20260101_000000_Legacy_12345678.json"
            legacy_doc = {
                "schema_version": 0,
                "metadata": {
                    "template_id": "12345678",
                    "name": "Legacy Template"
                },
                "graph": {"nodes": [{"id": 1, "type": "Math/Suma"}]}
            }
            doc_file.write_text(json.dumps(legacy_doc), encoding="utf-8")

            loaded = store.load_template("12345678")
            self.assertEqual(loaded["schema_version"], 1)
            self.assertEqual(loaded["metadata"]["node_count"], 1)
            self.assertIn("Math/Suma", loaded["metadata"]["node_types"])


if __name__ == "__main__":
    unittest.main()