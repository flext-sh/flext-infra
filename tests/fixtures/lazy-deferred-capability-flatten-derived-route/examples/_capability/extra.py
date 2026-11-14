"""Examples part flattening an unexported base derived from a routed base.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_demo import FlextDemoUtilities


class ExamplesFlextDemoCapabilityMixin(FlextDemoUtilities):
    """In-package base that no initializer exports."""

    MIXIN_VALUE = 4


class ExamplesFlextDemoCapabilityExtra(ExamplesFlextDemoCapabilityMixin):
    """Part whose flattened base carries a base another package publishes."""

    EXTRA_VALUE = 3


__all__: list[str] = ["ExamplesFlextDemoCapabilityExtra"]
