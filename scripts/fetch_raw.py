#!/usr/bin/env python3
"""Backward-compatible entrypoint → scripts/ingestion/run_phase_2_1.py"""

import runpy
from pathlib import Path

if __name__ == "__main__":
    runpy.run_path(
        str(Path(__file__).resolve().parent / "ingestion" / "run_phase_2_1.py"),
        run_name="__main__",
    )
