"""Examples utilities facade composing the capability part of each scenario.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from examples._capability import ExamplesFlextDemoCapabilityExtra


class ExamplesFlextDemoUtilities(ExamplesFlextDemoCapabilityExtra):
    """Facade whose part each scenario bases on another package's export."""


u = ExamplesFlextDemoUtilities

__all__: list[str] = ["ExamplesFlextDemoUtilities", "u"]
