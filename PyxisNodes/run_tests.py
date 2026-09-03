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

"""Ejecutor unificado de pruebas para Pyxis Node Engine.

Uso:
    python run_tests.py                   # Ejecuta todas las pruebas
    python run_tests.py --suite nodes     # Ejecuta solo pruebas de nodos
    python run_tests.py --suite core      # Ejecuta solo pruebas del motor central
    python run_tests.py --suite daemon    # Ejecuta pruebas de IPC y sesion
    python run_tests.py --suite preview   # Ejecuta pruebas de previsualizacion
    python run_tests.py --suite ui        # Ejecuta pruebas de UI e i18n
    python run_tests.py -v                # Modo detallado (verbose)
"""

import argparse
import os
import sys
import time
import unittest

_ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
if _ROOT_DIR not in sys.path:
    sys.path.insert(0, _ROOT_DIR)

TESTS_DIR = os.path.join(_ROOT_DIR, "tests")

SUITE_MAPPING = {
    "all": TESTS_DIR,
    "nodes": os.path.join(TESTS_DIR, "nodes"),
    "core": os.path.join(TESTS_DIR, "core"),
    "daemon": os.path.join(TESTS_DIR, "daemon"),
    "preview": os.path.join(TESTS_DIR, "preview"),
    "ui": os.path.join(TESTS_DIR, "ui"),
}


def run_test_suite(suite_name: str = "all", pattern: str = "test_*.py", verbose: int = 1) -> bool:
    """Descubre y ejecuta las pruebas de la suite seleccionada."""
    target_dir = SUITE_MAPPING.get(suite_name)
    if not target_dir or not os.path.exists(target_dir):
        print(f"[ERROR] Suite '{suite_name}' no encontrada en: {target_dir}")
        return False

    print("=" * 70)
    print(f"[PYXIS TEST RUNNER] Suite: {suite_name.upper()} | Directorio: {os.path.relpath(target_dir, _ROOT_DIR)}")
    print("=" * 70)

    loader = unittest.defaultTestLoader
    suite = loader.discover(start_dir=target_dir, pattern=pattern, top_level_dir=_ROOT_DIR)

    total_tests = suite.countTestCases()
    if total_tests == 0:
        print(f"[AVISO] No se encontraron pruebas en {target_dir} con patron '{pattern}'.")
        return True

    print(f"Total de pruebas descubiertas: {total_tests}\n")

    start_time = time.perf_counter()
    runner = unittest.TextTestRunner(verbosity=verbose)
    result = runner.run(suite)
    elapsed = time.perf_counter() - start_time

    print("\n" + "=" * 70)
    print(f"[RESUMEN DE EJECUCION] Tiempo transcurrido: {elapsed:.2f}s")
    print(f"  - Ejecutadas: {result.testsRun}")
    print(f"  - Exitosas:   {result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped)}")
    print(f"  - Fallos:     {len(result.failures)}")
    print(f"  - Errores:    {len(result.errors)}")
    print(f"  - Omitidas:   {len(result.skipped)}")
    print("=" * 70)

    if result.wasSuccessful():
        print("[RESULTADO FINAL]: TODAS LAS PRUEBAS PASARON CORRECTAMENTE [OK]\n")
        return True
    else:
        print("[RESULTADO FINAL]: SE DETECTARON ERRORES O FALLOS [FAIL]\n")
        return False


def main():
    parser = argparse.ArgumentParser(description="Ejecutor de pruebas de Pyxis Node Engine")
    parser.add_argument(
        "--suite", "-s",
        choices=["all", "nodes", "core", "daemon", "preview", "ui"],
        default="all",
        help="Suite tematica a ejecutar (por defecto: all)"
    )
    parser.add_argument(
        "--pattern", "-p",
        default="test_*.py",
        help="Patron de nombres de archivo de prueba (por defecto: test_*.py)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="count",
        default=1,
        help="Incrementar nivel de detalle en la salida"
    )

    args = parser.parse_args()
    success = run_test_suite(suite_name=args.suite, pattern=args.pattern, verbose=args.verbose)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
