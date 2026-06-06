#!/usr/bin/env python3
"""Print the next FengChao record path for a title."""

from __future__ import annotations

import argparse
from pathlib import Path

from fengchao import next_record_path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("title")
    parser.add_argument("--directory", default="task-records")
    args = parser.parse_args()
    print(next_record_path(Path(args.directory), args.title))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
