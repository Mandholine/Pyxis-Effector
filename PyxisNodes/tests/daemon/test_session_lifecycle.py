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

"""Pruebas unitarias para persistencia e integridad de sesiones JSON en PyxisNodes."""

import json 
import os 
import tempfile 
import unittest 
from node_engine import GraphEngine 


class TestSessionLifecycle (unittest .TestCase ):
    """Pruebas de serializacion, deserializacion y persistencia de grafos."""

    def test_session_serialization_and_rehydration (self ):
        graph_data ={
        "nodes":[
        {
        "id":1 ,
        "type":"Loops/Main Loop",
        "properties":{"iterador":"syl"},
        "outputs":[{"name":"Loop","type":"bucle","links":[101 ]}]
        },
        {
        "id":2 ,
        "type":"String",
        "properties":{"valor":"Persistent Node Data"}
        }
        ],
        "links":[]
        }


        json_str =json .dumps (graph_data )
        loaded_data =json .loads (json_str )

        self .assertEqual (len (loaded_data ["nodes"]),2 )
        engine =GraphEngine (loaded_data )
        self .assertEqual (len (engine .nodes ),2 )


if __name__ =="__main__":
    unittest .main ()
