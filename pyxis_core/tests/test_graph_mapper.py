# -*- coding: utf-8 -*-
import unittest

from pyxis_core.application.mappers.graph_mapper import GraphMapper


class TestGraphMapper(unittest.TestCase):
    ENGINE_GRAPH = {
        "nodes": [{"id": 1, "type": "Loops/Main Loop", "properties": {"iterator": "char"},
                   "outputs": [{"name": "Loop", "links": [7]}]},
                  {"id": 2, "type": "System/Output", "properties": {},
                   "inputs": [{"name": "Loop / Domain", "link": 7}]}],
        "links": [[7, 1, 0, 2, 0, "loop"]],
    }

    def test_engine_format_is_kept_with_its_links(self):
        out = GraphMapper.to_engine_dict(self.ENGINE_GRAPH)
        self.assertIs(out, self.ENGINE_GRAPH)                       # sin normalizar: no se pierden links ni ranuras
        self.assertEqual(out["links"], [[7, 1, 0, 2, 0, "loop"]])

    def test_old_normalisation_dropped_the_links(self):
        # documenta el fallo que se corrigio: la ruta de dominio no conserva `links`
        lossy = GraphMapper.to_dict(GraphMapper.to_domain(self.ENGINE_GRAPH))
        self.assertNotIn("links", lossy)

    def test_domain_format_is_mapped(self):
        domain = {"nodes": [{"id": "a", "type": "X/Y"}], "connections": [{"from_node": "a", "from_socket": "o", "to_node": "b", "to_socket": "i"}]}
        out = GraphMapper.to_engine_dict(domain)
        self.assertEqual(out["connections"][0]["from_node"], "a")

    def test_json_string_is_accepted(self):
        import json
        self.assertEqual(GraphMapper.to_engine_dict(json.dumps(self.ENGINE_GRAPH))["links"], self.ENGINE_GRAPH["links"])


if __name__ == "__main__":
    unittest.main()
