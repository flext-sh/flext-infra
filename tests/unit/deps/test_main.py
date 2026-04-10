"""Public-surface tests for dependency CLI services."""

from __future__ import annotations

import pytest
from flext_tests import tm

from flext_infra import FlextInfraCliDeps, deps


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


class TestDepsMainBehavior:
    def test_help_flag_returns_zero(self) -> None:
        tm.that(FlextInfraCliDeps.run(["--help"]), eq=0)

    def test_no_arguments_returns_usage_error(self) -> None:
        tm.that(FlextInfraCliDeps.run([]), eq=1)

    def test_unknown_subcommand_returns_usage_error(self) -> None:
        tm.that(FlextInfraCliDeps.run(["unknown"]), eq=2)
