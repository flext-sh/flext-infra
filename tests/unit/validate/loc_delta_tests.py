"""Tests for the net-LOC-delta validator (AGENTS.md §3.5).

The pure ``evaluate`` rule fails labelled refactor/cleanup commits with a net
positive delta and passes everything else.

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

from flext_infra.validate import FlextInfraLocDeltaValidator
from tests import tm


class TestsFlextInfraLocDelta:
    """Tests for ``FlextInfraLocDelta``."""

    @staticmethod
    def test_refactor_positive_delta_fails() -> None:
        """Test refactor positive delta fails."""
        result = FlextInfraLocDeltaValidator.evaluate(
            subject="refactor: collapse helpers",
            insertions=10,
            deletions=3,
        )
        tm.ok(result.failure)

    @staticmethod
    def test_refactor_negative_delta_passes() -> None:
        """Test refactor negative delta passes."""
        result = FlextInfraLocDeltaValidator.evaluate(
            subject="refactor: collapse helpers",
            insertions=3,
            deletions=20,
        )
        tm.ok(result.success)

    @staticmethod
    def test_refactor_zero_delta_passes() -> None:
        """Test refactor zero delta passes."""
        result = FlextInfraLocDeltaValidator.evaluate(
            subject="cleanup: drop dead code",
            insertions=5,
            deletions=5,
        )
        tm.ok(result.success)

    @staticmethod
    def test_non_labelled_subject_is_exempt() -> None:
        """Test non labelled subject is exempt."""
        result = FlextInfraLocDeltaValidator.evaluate(
            subject="feat: add new gate",
            insertions=120,
            deletions=0,
        )
        tm.ok(result.success)
