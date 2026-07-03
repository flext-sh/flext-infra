"""Tests for p facade.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra.tests.protocols import p


class TestsFlextInfraInfraProtocols:
    """Test p class import and structure."""

    def test_flext_infra_protocols_is_importable(self) -> None:
        """Test that p can be imported."""
        assert p is not None
