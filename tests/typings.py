"""Type system for FLEXT infra tests.

Provides TestsFlextInfraTypes, extending TestsFlextTypes with infra-specific
type definitions for infrastructure testing.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from pathlib import Path

from flext_tests import t as flext_tests_t

from flext_infra import t as flext_infra_t


class TestsFlextInfraTypes(flext_infra_t):
    """Type system for FLEXT infra tests composed from the production facade."""

    class Tests(flext_tests_t.Tests):
        """Tests use inherited flext-tests and production typing contracts."""

        type SourceCandidate = Callable[
            [
                Mapping[Path, str],
                tuple[Path, ...],
            ],
            Mapping[Path, str],
        ]


t = TestsFlextInfraTypes

__all__: list[str] = ["TestsFlextInfraTypes", "t"]
