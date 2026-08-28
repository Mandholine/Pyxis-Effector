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

# tests/test_syntax_and_ui_integrity.py
"""Pruebas automatizadas de integridad de sintaxis para Python, HTML y JavaScript (PyxisNodes WebUI)."""

import os
import glob
import ast
import re
import unittest
import html.parser


class TestSyntaxAndUIIntegrity(unittest.TestCase):

    def setUp(self):
        self.pyxisnodes_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.index_html_path = os.path.join(self.pyxisnodes_dir, 'web', 'index.html')

    def test_python_codebase_syntax(self):
        """Verifica que todos los archivos .py del proyecto compilen sin errores de sintaxis AST."""
        py_files = []
        for root, _, files in os.walk(self.pyxisnodes_dir):
            if 'python' in root or '.venv' in root or '__pycache__' in root:
                continue
            for f in files:
                if f.endswith('.py'):
                    py_files.append(os.path.join(root, f))

        self.assertGreater(len(py_files), 0, "No se encontraron archivos .py para validar.")

        for py_file in py_files:
            rel_path = os.path.relpath(py_file, self.pyxisnodes_dir)
            with self.subTest(file=rel_path):
                with open(py_file, 'r', encoding='utf-8') as f:
                    code = f.read()
                try:
                    ast.parse(code, filename=rel_path)
                except SyntaxError as e:
                    self.fail(f"Error de sintaxis Python en {rel_path} línea {e.lineno}: {e.msg}")

    def test_html_structure(self):
        """Verifica que el archivo index.html posea una estructura HTML5 válida."""
        self.assertTrue(os.path.exists(self.index_html_path), "No se encontró web/index.html")

        with open(self.index_html_path, 'r', encoding='utf-8') as f:
            content = f.read()

        class HTMLSyntaxChecker(html.parser.HTMLParser):
            pass

        parser = HTMLSyntaxChecker()
        try:
            parser.feed(content)
        except Exception as e:
            self.fail(f"Error de parseo HTML en web/index.html: {e}")

    def test_javascript_object_structures_balance(self):
        """Verifica la sintaxis y balance de llaves ({}), corchetes ([]) y paréntesis (()) de las estructuras JS clave de index.html."""
        self.assertTrue(os.path.exists(self.index_html_path), "No se encontró web/index.html")

        with open(self.index_html_path, 'r', encoding='utf-8') as f:
            content = f.read()

        for obj_name in ['DYNAMIC_NODE_MODES', 'MODE_INPUT_SPECS', 'ANCHOR_MODES', 'OUT_MODES']:
            match = re.search(r'const\s+' + obj_name + r'\s*=\s*([\{\[\s\S]*?\n\s*\}?\]?;)', content)
            self.assertIsNotNone(match, f"No se encontró la definición del objeto JS {obj_name} en index.html")
            obj_str = match.group(1)

            stack = []
            for line_num, line in enumerate(obj_str.splitlines(), 1):
                clean_line = line.strip()
                if clean_line.startswith('//'):
                    continue
                
                # Ignorar comas o cadenas dentro de comillas simples/dobles
                in_quote = None
                for ch in clean_line:
                    if in_quote:
                        if ch == in_quote:
                            in_quote = None
                        continue
                    if ch in ("'", '"'):
                        in_quote = ch
                        continue

                    if ch in '({[':
                        stack.append((ch, line_num))
                    elif ch in ')}]':
                        self.assertTrue(len(stack) > 0, f"Cierre '{ch}' desbalanceado en {obj_name} línea {line_num}: {clean_line}")
                        top, open_line = stack.pop()
                        self.assertTrue(
                            (top == '(' and ch == ')') or (top == '{' and ch == '}') or (top == '[' and ch == ']'),
                            f"Descalce '{top}' (línea {open_line}) con '{ch}' en {obj_name} línea {line_num}: {clean_line}"
                        )
            self.assertEqual(len(stack), 0, f"Quedaron {len(stack)} aperturas sin cerrar en {obj_name}")


if __name__ == '__main__':
    unittest.main()
