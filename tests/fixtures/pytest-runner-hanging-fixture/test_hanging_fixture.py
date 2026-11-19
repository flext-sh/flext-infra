"""Consumer suite whose setup fixture outlives the runner's process deadline.

The process deadline sends SIGTERM while this fixture sleeps, and a setup
fixture is not bounded by the per-item call timeout. The session must still
publish its JUnit report and accounting instead of dying as ``unknown``.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import time

import pytest


def test_a_completes() -> None:
    """Complete one item before the hanging setup starts."""
    assert True


@pytest.fixture
def hanging() -> None:
    """Hold the setup past the process deadline."""
    time.sleep(600)


def test_b_hangs_in_setup(hanging: None) -> None:
    """Block in setup until the deadline interrupts the session."""
    assert hanging is None
