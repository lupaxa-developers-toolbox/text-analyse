"""Allow ``python -m lupaxa.text_analyse`` to run the CLI."""

from __future__ import annotations

from lupaxa.text_analyse.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
