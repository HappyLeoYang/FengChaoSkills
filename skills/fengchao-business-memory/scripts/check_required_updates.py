#!/usr/bin/env python3
"""Compatibility wrapper for strict git-change memory checks."""

from fengchao import main


if __name__ == "__main__":
    raise SystemExit(main(["check", "--require-records-for-git-changes"]))
