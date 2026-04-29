"""Edge-case tests for public modernizer flows."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import FlextInfraPyprojectModernizer
from tests import c


class TestsFlextInfraDepsModernizerMainExtra:
    """Validate edge cases through the public modernizer API."""

    @pytest.mark.parametrize(
        ("content", "expected"),
        [
            pytest.param(None, 2, id="missing-root-pyproject"),
            pytest.param("", 0, id="empty-root-pyproject"),
            pytest.param("[invalid toml {", 2, id="invalid-root-pyproject"),
        ],
    )
    def test_run_handles_root_edge_cases(
        self,
        tmp_path: Path,
        content: str | None,
        expected: int,
    ) -> None:
        workspace = tmp_path / "workspace"
        workspace.mkdir(parents=True, exist_ok=True)
        if content is not None:
            (workspace / c.Infra.PYPROJECT_FILENAME).write_text(
                content,
                encoding="utf-8",
            )
        modernizer = FlextInfraPyprojectModernizer(workspace=workspace)
        tm.that(modernizer.run(), eq=expected)

    def test_audit_returns_zero_after_workspace_is_canonical(
        self,
        modernizer_workspace: Path,
    ) -> None:
        apply_exit = FlextInfraPyprojectModernizer(
            workspace=modernizer_workspace,
            apply_changes=True,
            skip_comments=True,
            skip_check=True,
        ).run()
        audit_exit = FlextInfraPyprojectModernizer(
            workspace=modernizer_workspace,
            audit=True,
            skip_comments=True,
        ).run()
        tm.that(apply_exit, eq=0)
        tm.that(audit_exit, eq=0)

    def test_run_fails_when_selected_project_has_invalid_toml(
        self,
        modernizer_workspace_with_projects: Path,
    ) -> None:
        selected_pyproject = (
            modernizer_workspace_with_projects / "selected" / c.Infra.PYPROJECT_FILENAME
        )
        selected_pyproject.write_text("[invalid", encoding="utf-8")
        modernizer = FlextInfraPyprojectModernizer(
            workspace=modernizer_workspace_with_projects,
            apply_changes=True,
            skip_comments=True,
            skip_check=False,
        )
        tm.that(modernizer.run(), eq=1)

    def test_run_rewrite_constraints_requires_uv_lock(
        self,
        modernizer_workspace: Path,
    ) -> None:
        modernizer = FlextInfraPyprojectModernizer(
            workspace=modernizer_workspace,
            apply_changes=True,
            rewrite_constraints=True,
            skip_comments=True,
            skip_check=True,
        )

        tm.that(modernizer.run(), eq=2)

    def test_run_apply_rewrites_dependency_constraints_from_uv_lock(
        self,
        modernizer_workspace: Path,
    ) -> None:
        (modernizer_workspace / c.Infra.PYPROJECT_FILENAME).write_text(
            (
                "[project]\n"
                'name = "workspace"\n'
                'version = "0.1.0"\n'
                'dependencies = ["requests>=2.0", "httpx[socks]>=0.1; python_version < \'3.14\'", "flext-core"]\n\n'
                "[tool.uv.workspace]\n"
                'members = ["flext-core"]\n\n'
                "[tool.poetry.dependencies]\n"
                'python = ">=3.13,<3.14"\n'
                'rich = ">=10"\n'
                'pendulum = { version = ">=2.0", extras = ["test"] }\n'
                'flext-core = { path = "../flext-core", develop = true }\n'
            ),
            encoding="utf-8",
        )
        (modernizer_workspace / "uv.lock").write_text(
            (
                "version = 1\n"
                "[manifest]\n"
                'members = ["workspace", "flext-core"]\n'
                "[[package]]\n"
                'name = "requests"\n'
                'version = "2.32.4"\n'
                'source = { registry = "https://pypi.org/simple" }\n'
                "[[package]]\n"
                'name = "httpx"\n'
                'version = "0.28.1"\n'
                'source = { registry = "https://pypi.org/simple" }\n'
                "[[package]]\n"
                'name = "rich"\n'
                'version = "14.2.0"\n'
                'source = { registry = "https://pypi.org/simple" }\n'
                "[[package]]\n"
                'name = "pendulum"\n'
                'version = "3.1.0"\n'
                'source = { registry = "https://pypi.org/simple" }\n'
                "[[package]]\n"
                'name = "flext-core"\n'
                'version = "0.12.0-dev"\n'
                'source = { editable = "." }\n'
            ),
            encoding="utf-8",
        )

        modernizer = FlextInfraPyprojectModernizer(
            workspace=modernizer_workspace,
            apply_changes=True,
            rewrite_constraints=True,
            skip_comments=True,
            skip_check=True,
        )

        tm.that(modernizer.run(), eq=0)
        rendered = (modernizer_workspace / c.Infra.PYPROJECT_FILENAME).read_text(
            encoding="utf-8"
        )
        tm.that(rendered, has='"requests>=2.32.4"')
        tm.that(
            rendered,
            has="\"httpx[socks]>=0.28.1; python_version < '3.14'\"",
        )
        tm.that(rendered, has='"flext-core"')
        tm.that(rendered, has='rich = ">=14.2.0"')
        tm.that(rendered, has='version = ">=3.1.0"')

    def test_run_apply_rewrites_constraints_with_compatible_policy(
        self,
        modernizer_workspace: Path,
    ) -> None:
        (modernizer_workspace / c.Infra.PYPROJECT_FILENAME).write_text(
            (
                "[project]\n"
                'name = "workspace"\n'
                'version = "0.1.0"\n'
                'dependencies = ["requests>=2.0"]\n'
            ),
            encoding="utf-8",
        )
        (modernizer_workspace / "uv.lock").write_text(
            (
                "version = 1\n"
                "[manifest]\n"
                'members = ["workspace"]\n'
                "[[package]]\n"
                'name = "requests"\n'
                'version = "2.32.4"\n'
                'source = { registry = "https://pypi.org/simple" }\n'
            ),
            encoding="utf-8",
        )

        modernizer = FlextInfraPyprojectModernizer(
            workspace=modernizer_workspace,
            apply_changes=True,
            rewrite_constraints=True,
            constraint_policy=c.Infra.DependencyConstraintPolicy.COMPATIBLE,
            skip_comments=True,
            skip_check=True,
        )

        tm.that(modernizer.run(), eq=0)
        tm.that(
            (modernizer_workspace / c.Infra.PYPROJECT_FILENAME).read_text(
                encoding="utf-8"
            ),
            has='"requests~=2.32.4"',
        )
