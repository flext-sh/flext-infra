"""Process entrypoint for the canonical centralized flext-infra CLI.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_cli import cli
from flext_infra import main

if __name__ == "__main__":
    cli.exit(main())
