"""Unit tests for ViolationKey content-stable violation identifier.

Validates content hashing, stability, boundary conditions, immutability,
and the frozenset reconciliation business use case.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import pytest
from flext_tests import tm

from tests import m, t


def _violation(
    *,
    module: str = "src/file.py",
    rule: str = "NS-001",
    line: int = 5,
    message: str = "test violation",
    fixable: bool = True,
) -> m.Infra.CensusViolation:
    return m.Infra.CensusViolation(
        module=module,
        rule=rule,
        line=line,
        message=message,
        fixable=fixable,
    )


_SOURCE_10 = [f"line {i}" for i in range(10)]


class TestViolationKeyFromViolation:
    """Tests for ViolationKey.from_violation() factory."""

    def test_from_violation_produces_content_hash(self) -> None:
        """ViolationKey has correct module, rule, and a non-empty content_hash."""
        v = _violation(module="src/models.py", rule="NS-002", line=5)
        key = m.Infra.ViolationKey.from_violation(v, _SOURCE_10)
        tm.that(key.module, eq="src/models.py")
        tm.that(key.rule, eq="NS-002")
        tm.that(len(key.content_hash) > 0, eq=True)

    def test_content_hash_stable_across_calls(self) -> None:
        """Same input produces identical hash on repeated calls."""
        v = _violation(line=4)
        key_a = m.Infra.ViolationKey.from_violation(v, _SOURCE_10)
        key_b = m.Infra.ViolationKey.from_violation(v, _SOURCE_10)
        tm.that(key_a.content_hash, eq=key_b.content_hash)

    def test_content_hash_changes_with_context(self) -> None:
        """Different surrounding lines produce different hash."""
        v = _violation(line=4)
        alt_source = [f"different {i}" for i in range(10)]
        key_original = m.Infra.ViolationKey.from_violation(v, _SOURCE_10)
        key_altered = m.Infra.ViolationKey.from_violation(v, alt_source)
        tm.that(key_original.content_hash != key_altered.content_hash, eq=True)

    def test_boundary_line_zero(self) -> None:
        """Violation at line=0 does not crash."""
        v = _violation(line=0)
        key = m.Infra.ViolationKey.from_violation(v, _SOURCE_10)
        tm.that(len(key.content_hash) > 0, eq=True)

    def test_boundary_last_line(self) -> None:
        """Violation at line beyond source_lines length does not crash."""
        v = _violation(line=999)
        key = m.Infra.ViolationKey.from_violation(v, _SOURCE_10)
        # Context window clamps to source bounds; hash is of empty string.
        tm.that(len(key.content_hash) > 0, eq=True)

    def test_frozen_model(self) -> None:
        """ViolationKey is immutable (frozen=True)."""
        v = _violation()
        key = m.Infra.ViolationKey.from_violation(v, _SOURCE_10)
        with pytest.raises(Exception):
            key.module = "changed"  # type: ignore[misc]

    def test_frozenset_reconciliation(self) -> None:
        """Two sets of ViolationKeys can be compared for fixed/remaining violations."""
        v1 = _violation(module="a.py", rule="NS-001", line=2)
        v2 = _violation(module="b.py", rule="NS-002", line=3)
        v3 = _violation(module="c.py", rule="NS-003", line=4)

        before = frozenset({
            m.Infra.ViolationKey.from_violation(v1, _SOURCE_10),
            m.Infra.ViolationKey.from_violation(v2, _SOURCE_10),
            m.Infra.ViolationKey.from_violation(v3, _SOURCE_10),
        })

        # After fixing, only v1 and v3 remain.
        after = frozenset({
            m.Infra.ViolationKey.from_violation(v1, _SOURCE_10),
            m.Infra.ViolationKey.from_violation(v3, _SOURCE_10),
        })

        fixed = before - after
        remaining = before & after

        tm.that(len(fixed), eq=1)
        tm.that(len(remaining), eq=2)
        # The fixed violation is the NS-002 one.
        fixed_key = next(iter(fixed))
        tm.that(fixed_key.module, eq="b.py")
        tm.that(fixed_key.rule, eq="NS-002")


__all__: t.StrSequence = []
