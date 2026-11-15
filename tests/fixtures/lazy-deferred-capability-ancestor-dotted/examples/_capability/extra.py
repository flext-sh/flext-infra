"""Examples part whose base is an attribute of another package's facade.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_demo import FlextDemoUtilities


class ExamplesFlextDemoCapabilityExtra(FlextDemoUtilities.Demo):
    """Namespace part extending a namespace of the source package's facade."""

    EXTRA_VALUE = 3


__all__: list[str] = ["ExamplesFlextDemoCapabilityExtra"]
