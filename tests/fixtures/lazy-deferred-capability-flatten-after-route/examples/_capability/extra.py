"""Examples part flattening an unexported base after a routed base.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_demo import FlextDemoUtilities


class ExamplesFlextDemoCapabilityMixin:
    """In-package base that no initializer exports."""

    MIXIN_VALUE = 4


class ExamplesFlextDemoCapabilityExtra(
    FlextDemoUtilities, ExamplesFlextDemoCapabilityMixin
):
    """Part whose flattened members would shadow the routed base's."""

    EXTRA_VALUE = 3


__all__: list[str] = ["ExamplesFlextDemoCapabilityExtra"]
