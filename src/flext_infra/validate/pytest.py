"""Extracted facade class for pytest.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra.validate._pytest import FlextInfraValidatePytestDiagXml


class FlextInfraValidatePytest(
    FlextInfraValidatePytestDiagXml,
):
    """Facade for pytest."""


__all__: list[str] = ["FlextInfraValidatePytest"]
