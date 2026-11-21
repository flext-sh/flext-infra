"""Consumer suite whose only item hangs in setup past the process deadline.

No item completes before the deadline, so the JUnit report holds no
testcase: the run is the unfinished timeout, never a completed lifecycle.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import time

import pytest


@pytest.fixture
def hanging() -> None:
    """Hold the setup past the process deadline."""
    time.sleep(600)


def test_hangs_in_setup(hanging: None) -> None:
    """Block in setup until the deadline interrupts the session."""
    assert hanging is None
