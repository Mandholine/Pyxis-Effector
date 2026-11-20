# -*- coding: utf-8 -*-
"""`python -m pyxis_api [--host 127.0.0.1] [--port 28723]`: arranca el daemon local."""
import argparse


def main() -> None:
    import uvicorn

    ap = argparse.ArgumentParser(prog="pyxis-api")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=28723)
    a = ap.parse_args()
    uvicorn.run("pyxis_api.main:app", host=a.host, port=a.port, log_level="info")


if __name__ == "__main__":
    main()
