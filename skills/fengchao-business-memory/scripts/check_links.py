#!/usr/bin/env python3
"""Compatibility wrapper for `fengchao.py check`."""

from fengchao import main


if __name__ == "__main__":
    raise SystemExit(main(["check"]))
