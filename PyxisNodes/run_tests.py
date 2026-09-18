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

"""Unified test runner for Pyxis Node Engine.

Usage:
    python run_tests.py                   # Run all tests
    python run_tests.py --suite nodes     # Run node tests only
    python run_tests.py --suite core      # Run core engine tests only
    python run_tests.py --suite daemon    # Run daemon & IPC tests only
    python run_tests.py --suite preview   # Run preview tests only
    python run_tests.py --suite ui        # Run UI and i18n tests only
    python run_tests.py -v                # Verbose mode
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
    print(f"[PYXIS TEST RUNNER] Suite: {suite_name.upper()} | Directory: {os.path.relpath(target_dir, _ROOT_DIR)}")
    print("=" * 70)

    loader = unittest.defaultTestLoader
    suite = loader.discover(start_dir=target_dir, pattern=pattern, top_level_dir=_ROOT_DIR)

    total_tests = suite.countTestCases()
    if total_tests == 0:
        print(f"[AVISO] No se encontraron pruebas en {target_dir} con patron '{pattern}'.")
        return True

    print(f"Total tests discovered: {total_tests}\n")

    start_time = time.perf_counter()
    runner = unittest.TextTestRunner(verbosity=verbose)
    result = runner.run(suite)
    elapsed = time.perf_counter() - start_time

    print("\n" + "=" * 70)
    print(f"[EXECUTION SUMMARY] Elapsed time: {elapsed:.2f}s")
    print(f"  - Executed:   {result.testsRun}")
    print(f"  - Successful: {result.testsRun - len(result.failures) - len(result.errors) - len(result.skipped)}")
    print(f"  - Failures:   {len(result.failures)}")
    print(f"  - Errors:     {len(result.errors)}")
    print(f"  - Skipped:    {len(result.skipped)}")
    print("=" * 70)

    if result.wasSuccessful():
        print("[FINAL RESULT]: ALL TESTS PASSED SUCCESSFULLY [OK]\n")
        return True
    else:
        print("[FINAL RESULT]: ERRORS OR FAILURES DETECTED [FAIL]\n")
        return False


def main():
    parser = argparse.ArgumentParser(description="Pyxis Node Engine Test Runner")
    parser.add_argument(
        "--suite", "-s",
        choices=["all", "nodes", "core", "daemon", "preview", "ui"],
        default="all",
        help="Test suite to run (default: all)"
    )
    parser.add_argument(
        "--pattern", "-p",
        default="test_*.py",
        help="Test file pattern (default: test_*.py)"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="count",
        default=1,
        help="Increase output verbosity"
    )

    args = parser.parse_args()
    success = run_test_suite(suite_name=args.suite, pattern=args.pattern, verbose=args.verbose)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
