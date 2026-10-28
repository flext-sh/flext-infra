"""Tests for FlextInfraVersioningService.

Tests cover semantic version parsing, bumping, and workspace version operations.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests import c, t, tf, tm, u


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
        version: str, expected: t.Triple[int, int, ...]
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
            ('[tool]\nname = "test"\n', "", "missing [project] table"),
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
            tf(base_dir=tmp_path).create(content, c.PYPROJECT_FILENAME)
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
            tf(base_dir=tmp_path).create(content, c.PYPROJECT_FILENAME)
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
    def test_render_project_version_preserves_layout_and_scopes_to_project() -> None:
        """Only ``[project].version`` changes; comments and other tables stay."""
        content = (
            '[tool.other]\nversion = "9.9.9"\n\n'
            '[project]\nname = "demo"\n  version = "1.0.0"  # release-owned\n'
        )
        tm.ok(
            u.Infra.render_project_version(content, "1.0.1"),
            eq=content.replace('"1.0.0"', '"1.0.1"'),
        )

    @staticmethod
    def test_render_project_version_rejects_invalid_document() -> None:
        """An unparseable pyproject fails before any rendering."""
        tm.fail(u.Infra.render_project_version("[project\n", "1.0.1"), has="invalid")

    @staticmethod
    def test_version_plan_publishes_through_shared_codegen_publisher(
        tmp_path: Path,
    ) -> None:
        """The version plan is effect-free until the shared publisher writes it."""
        root = u.Tests.git_repository(tmp_path)
        pyproject = u.Tests.WorktreeFixture.write_python_project(root, root.name)
        current = tm.ok(u.Infra.current_workspace_version(root))
        version = tm.ok(u.Infra.bump_version(current, "patch"))
        original = pyproject.read_bytes()
        plan = tm.ok(u.Infra.project_version_plan(root, version))
        tm.that(plan.before.content, eq=original)
        tm.that(pyproject.read_bytes(), eq=original)
        tm.ok(u.Infra.publish_codegen_plans(root, (plan,)), eq=(pyproject,))
        tm.ok(u.Infra.current_workspace_version(root), eq=version)
