"""Public-surface tests for dependency CLI services."""

from __future__ import annotations

import pytest
from flext_tests import tm

from flext_infra import deps


class TestPublicDepsSurface:
    EXPECTED_SERVICES = {
        "detect": "FlextInfraRuntimeDevDependencyDetector",
        "extra-paths": "FlextInfraExtraPathsManager",
        "internal-sync": "FlextInfraInternalDependencySyncService",
        "modernize": "FlextInfraPyprojectModernizer",
        "path-sync": "FlextInfraUtilitiesDependencyPathSync",
    }

    @pytest.mark.parametrize(
        ("subcommand", "service_name"),
        list(EXPECTED_SERVICES.items()),
        ids=list(EXPECTED_SERVICES.keys()),
    )
    def test_public_service_is_importable(
        self,
        subcommand: str,
        service_name: str,
    ) -> None:
        del subcommand
        service_cls = getattr(deps, service_name)
        tm.that(hasattr(service_cls, "main"), eq=True)
