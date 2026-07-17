"""Workspace/parser helper tests for deps modernizer."""

from __future__ import annotations


import pytest
from flext_tests import tm

from flext_infra import main
from flext_infra.deps.modernizer import FlextInfraPyprojectModernizer
from tests import c
from tests import u

from pathlib import Path


class TestsFlextInfraDepsModernizerWorkspace:
    """Validate helper behavior through public utilities and entrypoints."""

    @pytest.mark.parametrize(
        ("content", "exists", "expected"),
        [
            pytest.param('key = "value"\n', True, True, id="valid"),
            pytest.param("invalid toml content [[[", True, False, id="invalid"),
            pytest.param("", False, False, id="missing"),
        ],
    )
    def test_toml_read_handles_public_file_cases(
        self, tmp_path: Path, content: str, *, exists: bool, expected: bool
    ) -> None:
        """Verify toml read handles public file cases."""
        toml_file = tmp_path / "test.toml"
        if exists:
            toml_file.write_text(content, encoding="utf-8")
        result = u.Cli.toml_read(toml_file)
        tm.that(result is not None, eq=expected)

    def test_workspace_root_returns_explicit_path(self, tmp_path: Path) -> None:
        """Verify workspace root returns explicit path."""
        explicit = tmp_path / "explicit"
        explicit.mkdir()
        result = u.Infra.resolve_workspace_root_or_cwd(explicit)
        tm.that(str(result), eq=str(explicit.resolve()))

    def test_workspace_root_fallback_returns_non_empty_path(
        self, tmp_path: Path
    ) -> None:
        """Verify workspace root fallback returns non empty path."""
        deep_path = tmp_path / "a" / "b" / "c" / "d" / "e"
        deep_path.mkdir(parents=True, exist_ok=True)
        result = u.Infra.resolve_workspace_root_or_cwd(deep_path)
        tm.that(str(result), ne="")

    def test_main_applies_only_selected_projects(
        self, modernizer_workspace_with_projects: Path
    ) -> None:
        """Verify main applies only selected projects."""
        selected_pyproject = (
            modernizer_workspace_with_projects / "selected" / c.PYPROJECT_FILENAME
        )
        ignored_pyproject = (
            modernizer_workspace_with_projects / "ignored" / c.PYPROJECT_FILENAME
        )
        tm.that(
            main([
                "deps",
                "modernize",
                "--workspace",
                str(modernizer_workspace_with_projects),
                "--apply",
                "--skip-check",
                "--projects",
                "selected",
            ]),
            eq=0,
        )
        tm.that(
            selected_pyproject.read_text(encoding="utf-8"),
            has='build-backend = "hatchling.build"',
        )
        tm.that(ignored_pyproject.read_text(encoding="utf-8"), has='name = "ignored"')

    def test_modernizer_selects_configured_member_by_declared_name(
        self, tmp_path: Path
    ) -> None:
        """Resolve a configured member through its canonical project name."""
        workspace = tmp_path / "workspace"
        member = workspace / "member-dir"
        member.mkdir(parents=True)
        (workspace / c.PYPROJECT_FILENAME).write_text(
            '[project]\nname = "workspace"\nversion = "0.1.0"\n'
            '\n[tool.uv.workspace]\nmembers = ["member-dir"]\n',
            encoding="utf-8",
        )
        (member / c.PYPROJECT_FILENAME).write_text(
            '[project]\nname = "declared-name"\nversion = "0.1.0"\n', encoding="utf-8"
        )

        modernizer = FlextInfraPyprojectModernizer(
            workspace_root=workspace,
            selected_projects=["declared-name"],
            apply_changes=False,
            skip_check=True,
            skip_comments=True,
        )

        tm.that(modernizer.run(), eq=0)

    def test_modernizer_accepts_workspace_only_root_without_constraint_rewrite(
        self, tmp_path: Path
    ) -> None:
        """Do not require root project metadata for member-only modernization."""
        workspace = tmp_path / "workspace"
        member = workspace / "member"
        member.mkdir(parents=True)
        (workspace / c.PYPROJECT_FILENAME).write_text(
            '[tool.uv.workspace]\nmembers = ["member"]\n', encoding="utf-8"
        )
        (member / c.PYPROJECT_FILENAME).write_text(
            '[project]\nname = "member"\nversion = "0.1.0"\n', encoding="utf-8"
        )

        modernizer = FlextInfraPyprojectModernizer(
            workspace_root=workspace,
            selected_projects=["member"],
            apply_changes=False,
            skip_check=True,
            skip_comments=True,
            rewrite_constraints=False,
        )

        tm.that(modernizer.run(), eq=0)

    def test_modernizer_rejects_ambiguous_configured_member_alias(
        self, tmp_path: Path
    ) -> None:
        """Fail loud when one canonical project name selects multiple members."""
        workspace = tmp_path / "workspace"
        (workspace / "first-dir").mkdir(parents=True)
        (workspace / "second-dir").mkdir()
        (workspace / c.PYPROJECT_FILENAME).write_text(
            '[project]\nname = "workspace"\nversion = "0.1.0"\n'
            '\n[tool.uv.workspace]\nmembers = ["first-dir", "second-dir"]\n',
            encoding="utf-8",
        )
        for member_name in ("first-dir", "second-dir"):
            (workspace / member_name / c.PYPROJECT_FILENAME).write_text(
                '[project]\nname = "shared-name"\nversion = "0.1.0"\n', encoding="utf-8"
            )

        ambiguous = FlextInfraPyprojectModernizer(
            workspace_root=workspace,
            selected_projects=["shared-name"],
            apply_changes=False,
            skip_check=True,
            skip_comments=True,
        )
        exact = FlextInfraPyprojectModernizer(
            workspace_root=workspace,
            selected_projects=["first-dir"],
            apply_changes=False,
            skip_check=True,
            skip_comments=True,
        )

        tm.that(ambiguous.run(), eq=2)
        tm.that(exact.run(), eq=0)

    @pytest.mark.parametrize("member_kind", ["absolute", "parent-relative", "symlink"])
    def test_modernizer_rejects_configured_members_outside_workspace(
        self, modernizer_workspace: Path, member_kind: str
    ) -> None:
        """Reject configured members resolving outside root without mutation."""
        external_project = modernizer_workspace.parent / "external"
        external_project.mkdir()
        external_pyproject = external_project / c.PYPROJECT_FILENAME
        original = '[project]\nname = "external"\nversion = "0.1.0"\n'
        external_pyproject.write_text(original, encoding="utf-8")
        if member_kind == "absolute":
            selector = str(external_project)
        elif member_kind == "parent-relative":
            selector = "../external"
        else:
            selector = "linked-external"
            (modernizer_workspace / selector).symlink_to(
                external_project, target_is_directory=True
            )
        (modernizer_workspace / c.PYPROJECT_FILENAME).write_text(
            '[project]\nname = "workspace"\nversion = "0.1.0"\n'
            f'\n[tool.uv.workspace]\nmembers = ["{selector}"]\n',
            encoding="utf-8",
        )

        modernizer = FlextInfraPyprojectModernizer(
            workspace_root=modernizer_workspace,
            selected_projects=[selector],
            apply_changes=True,
            skip_check=True,
            skip_comments=True,
        )

        tm.that(modernizer.run(), eq=2)
        tm.that(external_pyproject.read_text(encoding="utf-8"), eq=original)

    @pytest.mark.parametrize("selector_kind", ["absolute", "parent-relative"])
    def test_modernizer_rejects_undeclared_project_paths(
        self, modernizer_workspace: Path, selector_kind: str
    ) -> None:
        """Reject selectors outside declared workspace members without mutation."""
        external_project = modernizer_workspace.parent / "external"
        external_project.mkdir()
        external_pyproject = external_project / c.PYPROJECT_FILENAME
        original = '[project]\nname = "external"\nversion = "0.1.0"\n'
        external_pyproject.write_text(original, encoding="utf-8")
        selector = (
            str(external_project) if selector_kind == "absolute" else "../external"
        )

        modernizer = FlextInfraPyprojectModernizer(
            workspace_root=modernizer_workspace,
            selected_projects=[selector],
            apply_changes=True,
            skip_check=True,
            skip_comments=True,
        )

        tm.that(modernizer.run(), eq=2)
        tm.that(external_pyproject.read_text(encoding="utf-8"), eq=original)
