"""Examples utilities facade composing a part based on an ancestor letter.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from examples._capability import ExamplesFlextDemoCapabilityExtra


class ExamplesFlextDemoUtilities(ExamplesFlextDemoCapabilityExtra):
    """Facade whose part extends a letter another package publishes."""


u = ExamplesFlextDemoUtilities

__all__: list[str] = ["ExamplesFlextDemoUtilities", "u"]
