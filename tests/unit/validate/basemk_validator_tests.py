"""Tests for FlextInfraBaseMkValidator.

Exemplar test file: uses tf (file ops), tm (matchers), fixtures, parametrize.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

import pytest
from flext_tests import tf, tm

from flext_infra.basemk.generator import FlextInfraBaseMkGenerator
from flext_infra.validate.basemk_validator import FlextInfraBaseMkValidator
from tests import m, t, u

_ROOT: Final[str] = "# root content"


def _generated_content() -> str:
    """Get the canonical generated base.mk content for hash-matching tests."""
    gen = FlextInfraBaseMkGenerator()
    result = gen.generate_basemk()
    tm.ok(result)
    generated_content: str = result.value
    return generated_content


@pytest.fixture
def v() -> FlextInfraBaseMkValidator:
    """Shared validator instance -- eliminates repeated construction."""
    return FlextInfraBaseMkValidator()


class TestBaseMkValidatorCore:
    """Core validation: pass/fail scenarios."""

    def test_missing_root_basemk_fails(
        self, tmp_path: Path, v: FlextInfraBaseMkValidator
    ) -> None:
        result = v.build_report(tmp_path)
        tm.ok(result)
        report = result.unwrap()
        tm.that(not report.passed, eq=True)
        tm.that(report.summary, has="missing canonical base.mk")

    def test_matching_basemk_returns_report_model(
        self, tmp_path: Path, v: FlextInfraBaseMkValidator
    ) -> None:
        (tmp_path / "base.mk").write_text(_generated_content(), encoding="utf-8")
        result = v.build_report(tmp_path)
        tm.ok(result)
        report = result.unwrap()
        tm.that(report, is_=m.Infra.ValidationReport)
        tm.that(report.passed, eq=True)

    def test_stale_basemk_fails(
        self, tmp_path: Path, v: FlextInfraBaseMkValidator
    ) -> None:
        tf(base_dir=tmp_path).create("# stale content", "base.mk")
        result = v.build_report(tmp_path)
        tm.ok(result)
        report = result.unwrap()
        tm.that(not report.passed, eq=True)
        tm.that(report.summary, has="out of sync")

    def test_matching_basemk_passes(
        self, tmp_path: Path, v: FlextInfraBaseMkValidator
    ) -> None:
        (tmp_path / "base.mk").write_text(_generated_content(), encoding="utf-8")
        result = v.build_report(tmp_path)
        tm.ok(result)
        report = result.unwrap()
        tm.that(report.passed, eq=True)
        tm.that(report.summary, has="matches generated template")

    def test_empty_workspace_missing_basemk(
        self, tmp_path: Path, v: FlextInfraBaseMkValidator
    ) -> None:
        result = v.build_report(tmp_path)
        tm.ok(result)
        report = result.unwrap()
        tm.that(not report.passed, eq=True)


class TestBaseMkValidatorEdgeCases:
    """Edge cases: violation reporting, OS errors."""

    def test_violations_include_stale_message(
        self, tmp_path: Path, v: FlextInfraBaseMkValidator
    ) -> None:
        tf(base_dir=tmp_path).create("# different", "base.mk")
        result = v.build_report(tmp_path)
        tm.ok(result)
        report = result.unwrap()
        tm.that(not report.passed, eq=True)
        tm.that(report.violations[0], has="stale")

    def test_stale_report_has_violations(
        self, tmp_path: Path, v: FlextInfraBaseMkValidator
    ) -> None:
        tf(base_dir=tmp_path).create("# mismatch", "base.mk")
        result = v.build_report(tmp_path)
        tm.ok(result)
        report = result.unwrap()
        tm.that(not report.passed, eq=True)
        tm.that(report.violations, length=1)

    def test_oserror_returns_failure(
        self, tmp_path: Path, v: FlextInfraBaseMkValidator
    ) -> None:
        basemk = tf(base_dir=tmp_path).create("# content", "base.mk")
        basemk.chmod(0)
        try:
            result = v.build_report(tmp_path)
            tm.that(result.failure, eq=True)
        finally:
            basemk.chmod(0o644)


class TestBaseMkValidatorSha256:
    """Hash computation: determinism, length, collision resistance."""

    @staticmethod
    def _sha(path: Path) -> str:
        sha_value: str = u.Cli.sha256_file(path)
        return sha_value

    def test_hash_is_64char_hex(self, tmp_path: Path) -> None:
        f = tf(base_dir=tmp_path).create("content", "test.txt")
        h = self._sha(f)
        tm.that(h, is_=str)
        tm.that(h, length=64)

    def test_same_content_same_hash(self, tmp_path: Path) -> None:
        f1 = tf(base_dir=tmp_path).create("same", "f1.txt")
        f2 = tf(base_dir=tmp_path).create("same", "f2.txt")
        tm.that(self._sha(f1), eq=self._sha(f2))

    def test_different_content_different_hash(self, tmp_path: Path) -> None:
        f1 = tf(base_dir=tmp_path).create("content1", "f1.txt")
        f2 = tf(base_dir=tmp_path).create("content2", "f2.txt")
        tm.that(self._sha(f1), ne=self._sha(f2))


__all__: t.StrSequence = []
