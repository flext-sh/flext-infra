"""compat: flext_infra._profile_entry -> the canonical flext-infra CLI.

fix: regenerate the consumer Makefile with ``make gen``; its gen and mod recipes
then call ``python -m flext_infra`` with ``FLEXT_INFRA_PROFILE_OUTPUT``. This
pass-through exists only while generated Makefiles still invoke it, and is
deleted when none does.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import sys
import warnings

if __name__ == "__main__":
    warnings.warn(
        "compat: flext_infra._profile_entry -> python -m flext_infra with "
        "FLEXT_INFRA_PROFILE_OUTPUT; fix: run make gen to regenerate the Makefile",
        DeprecationWarning,
        stacklevel=1,
    )
    # The profile destination is settings data, read once by the CLI entry.
    os.environ["FLEXT_INFRA_PROFILE_OUTPUT"] = sys.argv[1]
    from flext_infra import FlextInfraCli

    raise SystemExit(FlextInfraCli.infra_main(sys.argv[2:]))
