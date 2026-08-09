"""Utilities facade for flext-infra.

Re-exports flext_core utilities and adds infrastructure-specific
utility namespaces. All methods are exposed directly as ``u.Infra.<method>()``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_cli import u
from flext_core.lazy import FlextLazyAttribute, lazy

if TYPE_CHECKING:
    from flext_infra._utilities.infra import FlextInfraUtilitiesInfra


class FlextInfraUtilities(u):
    """Utility namespace for flext-infra; extends FlextUtilities.

    Usage::

        from flext_infra import m, u

        u.Infra.git_status(m.Infra.GitStatusRequest(repo_root=Path(".")))
        u.Cli.toml_read_json(path)
        u.Infra.discover_projects(workspace_root)
        u.Infra.parse_semver("1.2.3")
    """

    Infra: FlextLazyAttribute[type[FlextInfraUtilitiesInfra]] = lazy.attribute(
        "Infra",
        {"Infra": ("flext_infra._utilities.infra", "FlextInfraUtilitiesInfra")},
        globals(),
        __name__,
    )


u = FlextInfraUtilities

__all__: list[str] = ["FlextInfraUtilities", "u"]
