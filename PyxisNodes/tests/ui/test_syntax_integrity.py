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

"""Pruebas de integridad sintactica (AST parsing) en todos los modulos Python del proyecto."""

import ast 
import os 
import unittest 


class TestSyntaxIntegrity (unittest .TestCase ):
    """Verifica que todos los archivos Python del proyecto compilen correctamente sin errores sintacticos."""

    def test_all_py_files_ast_parse (self ):
        base_dir =os .path .dirname (os .path .dirname (os .path .dirname (os .path .abspath (__file__ ))))
        py_files =[]

        for root ,dirs ,files in os .walk (base_dir ):
            if "python"in root or "__pycache__"in root or ".venv"in root :
                continue 
            for f in files :
                if f .endswith (".py"):
                    py_files .append (os .path .join (root ,f ))

        self .assertGreater (len (py_files ),10 ,"Deben encontrarse al menos 10 archivos Python en el proyecto")

        errors =[]
        for py_file in py_files :
            try :
                with open (py_file ,"r",encoding ="utf-8",errors ="ignore")as fh :
                    source =fh .read ()
                ast .parse (source ,filename =py_file )
            except Exception as e :
                errors .append (f"{os .path .relpath (py_file ,base_dir )}: {e }")

        self .assertEqual (errors ,[],f"Errores de sintaxis detectados: {errors }")


if __name__ =="__main__":
    unittest .main ()
