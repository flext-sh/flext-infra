# AUTO-GENERATED FILE — Regenerate with: make check
"""Flext Infra.codemod. Gates package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import install_lazy_exports

if TYPE_CHECKING:
    from flext_infra.codemod._gates.findings import FlextInfraModGateFindings
    from flext_infra.codemod._gates.fixtures import FlextInfraModGateFixtures
    from flext_infra.codemod._gates.runner import FlextInfraModGateRunner
    from flext_infra.codemod._gates.scanner import FlextInfraModGateScanner


__all__: tuple[str, ...] = (
    "FlextInfraModGateFindings",
    "FlextInfraModGateFixtures",
    "FlextInfraModGateRunner",
    "FlextInfraModGateScanner",
)

install_lazy_exports(
    __name__,
    globals(),
    {
        "FlextInfraModGateFindings": ".findings",
        "FlextInfraModGateFixtures": ".fixtures",
        "FlextInfraModGateRunner": ".runner",
        "FlextInfraModGateScanner": ".scanner",
    },
    public_exports=__all__,
)
