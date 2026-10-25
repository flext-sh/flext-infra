"""pytest constants, enums and exceptions, declared once for the whole fleet.

``c.Infra.Pytest`` is the single owner: flext-tests inherits it under
``c.Tests``. Constants, enums and exceptions live here by the facade-member
ownership of their object kind.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import ClassVar

import pytest


class FlextInfraConstantsPytest:
    """pytest constants published under ``c.Infra.Pytest``."""

    class Pytest:
        """pytest constants, enums and exceptions; flext-tests inherits them."""

        MARK: ClassVar[pytest.MarkGenerator] = pytest.mark
        FAIL: ClassVar = pytest.fail
        SKIP: ClassVar = pytest.skip
        ExitCode = pytest.ExitCode
        FixtureLookupError = pytest.FixtureLookupError
        UsageError = pytest.UsageError


__all__: list[str] = ["FlextInfraConstantsPytest"]
