"""Tests utilities facade composing the examples facade by class name.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from examples import ExamplesFlextDemoUtilities


class TestsFlextDemoUtilities(ExamplesFlextDemoUtilities):
    """Tests facade extending the examples utilities facade."""


u = TestsFlextDemoUtilities

__all__: list[str] = ["TestsFlextDemoUtilities", "u"]
