"""Declarative package selectors for uv resolution policy.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import Annotated

from flext_cli import m, t

from flext_infra._models._config.contract import FlextInfraConfigModelsContract


class FlextInfraConfigModelsUv:
    """Foundational uv declarations resolved before their consumers."""

    class UvPackageSelectorSpec(FlextInfraConfigModelsContract.ConfigContract):
        """Package selector for one official uv scoped dependency exclusion."""

        name: Annotated[t.NonEmptyStr, m.Field(description="Selected package name")]
        version: Annotated[
            t.NonEmptyStr | None,
            m.Field(description="Optional selected package version expression"),
        ] = None
