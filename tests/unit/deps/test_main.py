"""Public-surface tests for dependency CLI services."""

from __future__ import annotations

import pytest
from flext_tests import tm

from flext_infra import deps
from flext_infra.deps.detector import FlextInfraRuntimeDevDependencyDetector
from flext_infra.deps.extra_paths import FlextInfraExtraPathsManager
from flext_infra.deps.internal_sync import FlextInfraInternalDependencySyncService
from flext_infra.deps.modernizer import FlextInfraPyprojectModernizer
from flext_infra.deps.path_sync import main as path_sync_main


class TestsFlextInfraDepsMain:
    EXPECTED_SERVICES = (
        (
            "detect",
            deps.FlextInfraRuntimeDevDependencyDetector,
            FlextInfraRuntimeDevDependencyDetector,
        ),
        ("extra-paths", deps.FlextInfraExtraPathsManager, FlextInfraExtraPathsManager),
        (
            "internal-sync",
            deps.FlextInfraInternalDependencySyncService,
            FlextInfraInternalDependencySyncService,
        ),
        (
            "modernize",
            deps.FlextInfraPyprojectModernizer,
            FlextInfraPyprojectModernizer,
        ),
        ("path-sync", deps.path_sync.main, path_sync_main),
    )

    @pytest.mark.parametrize(
        ("subcommand", "exported", "expected"),
        EXPECTED_SERVICES,
        ids=[subcommand for subcommand, _, _ in EXPECTED_SERVICES],
    )
    def test_public_service_is_importable(
        self,
        subcommand: str,
        exported: object,
        expected: object,
    ) -> None:
        del subcommand
        tm.that(exported, eq=expected)
