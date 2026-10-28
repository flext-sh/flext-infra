"""Public facade for the canonical persistent-testmon pytest runner.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from flext_infra.validate._pytest_runner import FlextInfraPytestRunnerExecution


class FlextInfraPytestRunner(FlextInfraPytestRunnerExecution):
    """Expose whole-suite cached execution through the public package boundary."""


__all__: tuple[str, ...] = ("FlextInfraPytestRunner",)
