"""Public-surface tests for dependency CLI services."""

from __future__ import annotations

import pytest
from flext_tests import tm

from flext_infra import deps


class TestsFlextInfraDepsMain:
    EXPECTED_SERVICES = {
        "detect": "FlextInfraRuntimeDevDependencyDetector",
        "extra-paths": "FlextInfraExtraPathsManager",
        "internal-sync": "FlextInfraInternalDependencySyncService",
        "modernize": "FlextInfraPyprojectModernizer",
        "path-sync": "path_sync",
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
        exported = getattr(deps, service_name)
        if subcommand == "path-sync":
            tm.that(hasattr(exported, "main"), eq=True)
            return
        tm.that(exported, is_=type)
