"""Process entrypoint for the canonical centralized flext-infra CLI."""

from __future__ import annotations

import sys

from flext_infra.cli import main

if __name__ == "__main__":
    sys.exit(main())
