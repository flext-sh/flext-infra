"""Protocol definitions for FLEXT infra tests.

Provides TestsFlextInfraProtocols, extending TestsFlextProtocols with
infra-specific protocol definitions for infrastructure testing.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Protocol, runtime_checkable

from flext_tests import FlextTestsProtocols

from flext_infra import FlextInfraProtocols


class TestsFlextInfraProtocols(FlextTestsProtocols, FlextInfraProtocols):
    """Protocol definitions for FLEXT infra tests."""

    class Tests(FlextTestsProtocols.Tests):
        """Tests use inherited flext-tests and production protocols."""

        @runtime_checkable
        class PytestProfileContext(Protocol):
            """Declared runner inputs consumed by the real profiling launcher."""

            @property
            def repository_root(self) -> Path:
                """Root directory of the repository being profiled."""
                ...

            @property
            def target(self) -> Path:
                """Selected test target within the repository."""
                ...

            @property
            def target_file(self) -> Path | None:
                """Explicit test file, when a single-file run is selected."""
                ...

            @property
            def reports(self) -> Path:
                """Destination directory for profiling reports."""
                ...

            @property
            def testmon_db(self) -> Path:
                """Persistent testmon database used by the runner."""
                ...

            @property
            def started_at_monotonic(self) -> float:
                """Monotonic timestamp at the beginning of the profiling run."""
                ...

        class NativeConsumer(Protocol):
            """Run an actual isolated Python consumer with explicit source inputs."""

            def __call__(
                self, code: str, *arguments: str, cwd: Path | None = None
            ) -> None:
                """Assert successful real execution, preserving its causal output."""
                ...


p = TestsFlextInfraProtocols

__all__: list[str] = ["TestsFlextInfraProtocols", "p"]
