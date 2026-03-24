"""Tests for FlextInfraBaseMkValidator.

Exemplar test file: uses tf (file ops), tm (matchers), fixtures, parametrize.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

import pytest
from flext_tests import tf, tm

from flext_infra import FlextInfraBaseMkGenerator, FlextInfraBaseMkValidator
from tests import m

_ROOT = "# root content"


def _generated_content() -> str:
    """Get the canonical generated base.mk content for hash-matching tests."""
    gen = FlextInfraBaseMkGenerator()
    result = gen.generate()
    assert result.is_success
    return result.value


@pytest.fixture
def v() -> FlextInfraBaseMkValidator:
    """Shared validator instance -- eliminates repeated construction."""
    return FlextInfraBaseMkValidator()


class TestBaseMkValidatorCore:
    """Core validation: pass/fail scenarios."""

    def test_missing_root_basemk_fails(
        self,
        tmp_path: Path,
        v: FlextInfraBaseMkValidator,
    ) -> None:
        report = tm.ok(v.validate(tmp_path))
        tm.that(not report.passed, eq=True)
        tm.that(report.summary, has="missing root base.mk")

    def test_matching_basemk_returns_report_model(
        self,
        tmp_path: Path,
        v: FlextInfraBaseMkValidator,
    ) -> None:
        (tmp_path / "base.mk").write_text(
            _generated_content(),
            encoding="utf-8",
        )
        report = tm.ok(v.validate(tmp_path))
        assert isinstance(report, m.Infra.ValidationReport)
        tm.that(report.passed, eq=True)

    def test_stale_basemk_fails(
        self,
        tmp_path: Path,
        v: FlextInfraBaseMkValidator,
    ) -> None:
        tf.create_in("# stale content", "base.mk", tmp_path)
        report = tm.ok(v.validate(tmp_path))
        tm.that(not report.passed, eq=True)
        tm.that(report.summary, has="out of sync")

    def test_matching_basemk_passes(
        self,
        tmp_path: Path,
        v: FlextInfraBaseMkValidator,
    ) -> None:
        (tmp_path / "base.mk").write_text(
            _generated_content(),
            encoding="utf-8",
        )
        report = tm.ok(v.validate(tmp_path))
        tm.that(report.passed, eq=True)
        tm.that(report.summary, has="matches generated template")

    def test_empty_workspace_missing_basemk(
        self,
        tmp_path: Path,
        v: FlextInfraBaseMkValidator,
    ) -> None:
        report = tm.ok(v.validate(tmp_path))
        tm.that(not report.passed, eq=True)


class TestBaseMkValidatorEdgeCases:
    """Edge cases: violation reporting, OS errors."""

    def test_violations_include_stale_message(
        self,
        tmp_path: Path,
        v: FlextInfraBaseMkValidator,
    ) -> None:
        tf.create_in("# different", "base.mk", tmp_path)
        report = tm.ok(v.validate(tmp_path))
        tm.that(not report.passed, eq=True)
        tm.that(report.violations[0], has="stale")

    def test_stale_report_has_violations(
        self,
        tmp_path: Path,
        v: FlextInfraBaseMkValidator,
    ) -> None:
        tf.create_in("# mismatch", "base.mk", tmp_path)
        report = tm.ok(v.validate(tmp_path))
        tm.that(not report.passed, eq=True)
        tm.that(report.violations, length=1)

    def test_oserror_returns_failure(
        self,
        tmp_path: Path,
        v: FlextInfraBaseMkValidator,
    ) -> None:
        basemk = tf.create_in("# content", "base.mk", tmp_path)
        basemk.chmod(0)
        try:
            result = v.validate(tmp_path)
            tm.that(result.is_failure, eq=True)
        finally:
            basemk.chmod(0o644)


class TestBaseMkValidatorSha256:
    """Hash computation: determinism, length, collision resistance."""

    @staticmethod
    def _sha(path: Path) -> str:
        return FlextInfraBaseMkValidator._sha256_file(path)

    def test_hash_is_64char_hex(self, tmp_path: Path) -> None:
        f = tf.create_in("content", "test.txt", tmp_path)
        h = self._sha(f)
        assert isinstance(h, str)
        tm.that(h, length=64)

    def test_same_content_same_hash(self, tmp_path: Path) -> None:
        f1 = tf.create_in("same", "f1.txt", tmp_path)
        f2 = tf.create_in("same", "f2.txt", tmp_path)
        tm.that(self._sha(f1), eq=self._sha(f2))

    def test_different_content_different_hash(self, tmp_path: Path) -> None:
        f1 = tf.create_in("content1", "f1.txt", tmp_path)
        f2 = tf.create_in("content2", "f2.txt", tmp_path)
        tm.that(self._sha(f1), ne=self._sha(f2))


__all__: Sequence[str] = []
