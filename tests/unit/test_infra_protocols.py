"""Tests for p facade.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from tests import p, tm


class TestsFlextInfraInfraProtocols:
    """Test p class import and structure."""

    @staticmethod
    def test_flext_infra_protocols_is_importable() -> None:
        """Test that p can be imported."""
        tm.that(p, none=False)
