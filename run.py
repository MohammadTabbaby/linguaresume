#!/usr/bin/env python3
"""Backward-compatible wrapper around the new CLI."""
import sys
from linguaresume.cli import main

if __name__ == "__main__":
    # Convert legacy `python run.py job.txt` → `python -m linguaresume tailor job.txt`
    if len(sys.argv) > 1 and sys.argv[1] not in ("tailor", "validate", "pdf", "translate", "--help", "-h"):
        sys.argv.insert(1, "tailor")
    main()
