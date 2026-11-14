# AUTO-GENERATED FILE — Regenerate with: make gen
"""Flext Infra. Utilities. Project package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core.lazy import defer_lazy_bases, install_lazy_exports

if TYPE_CHECKING:
    from flext_infra._utilities._project.discovery_candidates import (
        FlextInfraUtilitiesProjectDiscoveryCandidates,
    )
    from flext_infra._utilities._project.discovery_shape import (
        FlextInfraUtilitiesProjectDiscoveryShape,
    )


__all__: tuple[str, ...] = (
    "FlextInfraUtilitiesProjectDiscoveryCandidates",
    "FlextInfraUtilitiesProjectDiscoveryShape",
)

install_lazy_exports(
    __name__,
    globals(),
    {
        "FlextInfraUtilitiesProjectDiscoveryCandidates": ".discovery_candidates",
        "FlextInfraUtilitiesProjectDiscoveryShape": ".discovery_shape",
    },
    public_exports=__all__,
    deferred_members={
        "FlextInfraUtilitiesProjectDiscoveryCandidates": (
            "repository_operation_targets",
            "discover_project_candidates",
            "repository_nonparticipant_paths",
        ),
        "FlextInfraUtilitiesProjectDiscoveryShape": (
            "detected_project_kind",
            "_uses_flext_imports",
            "_is_nonparticipant",
            "_looks_like_project",
            "nearest_project_root",
        ),
    },
)

defer_lazy_bases(
    __name__,
    {
        "FlextInfraUtilitiesProjectDiscoveryCandidates": (
            (".", "FlextInfraUtilitiesProjectDiscoveryShape"),
        ),
    },
)
