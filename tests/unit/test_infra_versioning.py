"""Tests for FlextInfraVersioningService.

Tests cover semantic version parsing, bumping, and workspace version operations.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from tests import tf, tm, u

if TYPE_CHECKING:
    from pathlib import Path

    from tests import p, t


class TestsFlextInfraInfraVersioning:
    """Behavior contract for test_infra_versioning."""

    @staticmethod
    @pytest.mark.parametrize(
        ("version", "expected"),
        [
            ("1.2.3", (1, 2, 3)),
            ("1.2.3.dev0", (1, 2, 3)),
            ("1.2.3rc0", (1, 2, 3)),
            ("0.0.0", (0, 0, 0)),
            ("999.888.777", (999, 888, 777)),
        ],
        ids=["standard", "development", "release-candidate", "zero", "large"],
    )
    def test_parse_semver_valid(
        version: str,
        expected: t.Triple[int, int, int],
    ) -> None:
        """Accept only supported canonical PEP 440 release spellings."""
        tm.ok(u.Infra.parse_semver(version), eq=expected)

    @staticmethod
    @pytest.mark.parametrize(
        "version",
        ["1.2", "a.b.c", "1.2.3-beta", "1.2.3-dev", "1.2.3.rc0"],
        ids=[
            "invalid-format",
            "non-numeric",
            "unsupported-suffix",
            "legacy-development",
            "legacy-release-candidate",
        ],
    )
    def test_parse_semver_invalid(version: str) -> None:
        """Reject malformed and legacy release spellings."""
        tm.fail(u.Infra.parse_semver(version), has="invalid semver")

    @staticmethod
    def test_parse_semver_result_type() -> None:
        """Return the canonical three-integer release tuple."""
        tm.ok(u.Infra.parse_semver("1.2.3"), is_=tuple)

    @staticmethod
    @pytest.mark.parametrize(
        ("version", "bump_type", "expected"),
        [
            ("1.2.3", "major", "2.0.0"),
            ("1.2.3", "minor", "1.3.0"),
            ("1.2.3", "patch", "1.2.4"),
            ("0.0.0", "major", "1.0.0"),
        ],
        ids=["major", "minor", "patch", "from-zero"],
    )
    def test_bump_version_valid(
        version: str,
        bump_type: str,
        expected: str,
    ) -> None:
        """Bump each supported semantic release component."""
        tm.ok(u.Infra.bump_version(version, bump_type), eq=expected)

    @staticmethod
    @pytest.mark.parametrize(
        ("version", "bump_type", "error"),
        [
            ("1.2.3", "invalid", "invalid bump type"),
            ("not.a.version", "major", "invalid semver"),
        ],
        ids=["invalid-bump-type", "invalid-version"],
    )
    def test_bump_version_invalid(
        version: str,
        bump_type: str,
        error: str,
    ) -> None:
        """Reject unsupported bump kinds and invalid source versions."""
        tm.fail(u.Infra.bump_version(version, bump_type), has=error)

    @staticmethod
    def test_bump_version_result_type() -> None:
        """Return canonical version text from a valid bump."""
        tm.ok(u.Infra.bump_version("1.2.3", "major"), is_=str)

    @staticmethod
    @pytest.mark.parametrize(
        ("content", "expected", "error"),
        [
            ('[project]\nversion = "1.2.3"\n', "1.2.3", ""),
            (None, "", ""),
            ('[tool]\nname = "test"\n', "", "version not found"),
            ('[project]\nname = "test"\n', "", "version not found"),
            ('[project]\nversion = ""\n', "", "version not found"),
        ],
        ids=[
            "success",
            "missing-file",
            "missing-project-table",
            "missing-version",
            "empty-version",
        ],
    )
    def test_current_workspace_version(
        tmp_path: Path,
        content: str | None,
        expected: str,
        error: str,
    ) -> None:
        """Read only the declared project version from a repository root."""
        if content is not None:
            tf(base_dir=tmp_path).create(content, "pyproject.toml")
        result = u.Infra.current_workspace_version(tmp_path)
        if expected:
            tm.ok(result, eq=expected)
            return
        if error:
            tm.fail(result, has=error)
            return
        tm.fail(result)

    @staticmethod
    @pytest.mark.parametrize(
        ("content", "expected", "error"),
        [
            ('[project]\nversion = "1.0.0"\n', "2.0.0", ""),
            (None, "", ""),
            ('[tool]\nname = "test"\n', "", "missing [project] table"),
        ],
        ids=["success", "missing-file", "missing-project-table"],
    )
    def test_replace_project_version(
        tmp_path: Path,
        content: str | None,
        expected: str,
        error: str,
    ) -> None:
        """Atomically replace only a canonical project version declaration."""
        if content is not None:
            tf(base_dir=tmp_path).create(content, "pyproject.toml")
        result = u.Infra.replace_project_version(tmp_path, "2.0.0")
        if error:
            tm.fail(result, has=error)
            return
        if not expected:
            tm.fail(result)
            return
        tm.ok(result, eq=True)
        tm.ok(u.Infra.current_workspace_version(tmp_path), eq=expected)

    @staticmethod
    def test_version_publisher_returns_original_native_effects(
        tmp_path: Path, native_consumer: p.Tests.NativeConsumer
    ) -> None:
        """The version owner publishes its real plan and retains native authority."""
        script = """
import sys
from pathlib import Path

sys.path.insert(0, sys.argv[1])
from flext_infra import codegen
from flext_infra.validate.fresh_import import FlextInfraValidateFreshImport
from tests import c, m, r, tm, u

runtime_root = Path(sys.argv[1])
root = u.Tests.git_repository(Path(sys.argv[2]) / "repo")
pyproject = u.Tests.WorktreeFixture.write_python_project(root, root.name)
current = tm.ok(u.Infra.current_workspace_version(root))
version = tm.ok(u.Infra.bump_version(current, "patch"))
original = pyproject.read_bytes()
plan = tm.ok(u.Infra.project_version_plan(root, version))
tm.that(plan.before.content, eq=original)
tm.that(pyproject.read_bytes(), eq=original)
producer = tm.ok(FlextInfraValidateFreshImport.capture_producer(
    runtime_root, entrypoint=codegen.FlextInfraCodegenTransaction,
))
owner = codegen.FlextInfraCodegenTransaction(repository_root=root, producer=producer)
receipts = []

def publish(file):
    analysis = m.Infra.CodegenPhaseAnalysis(phase=file.phase, files=(file,))
    result = owner.publish_file_phase_locked(
        root,
        owner.capability_roots(file.phase.value, (root,)),
        analysis,
        policy=m.Infra.CodegenPhasePublicationPolicy(directories=()),
        publication_receipts=receipts,
    )
    if result.failure:
        return r[m.Infra.CodegenPhaseOutcome].from_failure(result)
    if len(receipts) != 1:
        return r[m.Infra.CodegenPhaseOutcome].fail("one native version receipt required")
    return r[m.Infra.CodegenPhaseOutcome].ok(receipts[0])

receipt = tm.ok(u.Infra.publish_project_version(root, version, publish))
tm.that(receipt is receipts[0], eq=True)
tm.that(receipt.written_files, eq=(pyproject,))
tm.ok(codegen.FlextInfraMiseArtifactsVerification.publication_birth_current(receipt))
tm.ok(u.Infra.current_workspace_version(root), eq=version)
"""
        native_consumer(script, str(tmp_path))
