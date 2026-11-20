"""Consumer suite whose slow item declares a forbidden explicit timeout.

The FLEXT slow-timeout policy owns the budget of a slow item: an explicit
``pytest.mark.timeout`` on top of it is a collection-time policy violation.
The runner must reject the selection and name this module.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import pytest


@pytest.mark.slow
@pytest.mark.timeout(1)
def test_breaks_policy() -> None:
    """Run under the slow marker with a forbidden per-item timeout."""
