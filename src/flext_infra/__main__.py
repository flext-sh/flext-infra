"""Process entrypoint for the canonical centralized flext-infra CLI.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_cli import cli

# mro-dxrp.8 (Hephaestus): avoid re-entering the root PEP 562 export resolver.
from flext_infra.cli import main

if __name__ == "__main__":
    cli.exit(main())
