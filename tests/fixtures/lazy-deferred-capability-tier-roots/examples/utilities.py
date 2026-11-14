"""Examples utilities facade composing the public facade by class name.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_demo import FlextDemoUtilities


class ExamplesFlextDemoUtilities(FlextDemoUtilities):
    """Examples facade extending the public utilities facade."""


u = ExamplesFlextDemoUtilities

__all__: list[str] = ["ExamplesFlextDemoUtilities", "u"]
