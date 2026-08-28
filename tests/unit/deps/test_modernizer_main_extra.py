"""Edge-case tests for public modernizer flows."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from flext_infra.deps.modernizer import FlextInfraPyprojectModernizer
from flext_tests import tm
from tests import c, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraDepsModernizerMainExtra:
    """Validate edge cases through the public modernizer API."""

    @pytest.mark.parametrize(
        ("content", "expected"),
        [
            pytest.param(None, 2, id="missing-root-pyproject"),
            pytest.param("", 2, id="empty-root-pyproject"),
            pytest.param("[invalid toml {", 2, id="invalid-root-pyproject"),
        ],
    )
    def test_run_handles_root_edge_cases(
        self, tmp_path: Path, content: str | None, expected: int
    ) -> None:
        """Fail loud for missing, empty, or invalid root project contracts."""
        workspace = tmp_path / "workspace"
        workspace.mkdir(parents=True, exist_ok=True)
        if content is not None:
            (workspace / c.Infra.PYPROJECT_FILENAME).write_text(
                content, encoding="utf-8"
            )
        modernizer = FlextInfraPyprojectModernizer(workspace_root=workspace)
        tm.that(modernizer.run(), eq=expected)

    def test_audit_returns_zero_after_workspace_is_canonical(
        self, modernizer_workspace: Path
    ) -> None:
        """Reach a fixed point after one canonical apply."""
        apply_exit = FlextInfraPyprojectModernizer(
            workspace_root=modernizer_workspace,
            apply_changes=True,
            skip_comments=True,
            skip_check=True,
        ).run()
        audit_exit = FlextInfraPyprojectModernizer(
            workspace_root=modernizer_workspace, audit=True, skip_comments=True
        ).run()
        tm.that(apply_exit, eq=0)
        tm.that(audit_exit, eq=0)

    def test_run_fails_when_selected_project_has_invalid_toml(
        self, modernizer_workspace_with_projects: Path
    ) -> None:
        """Report invalid TOML from an explicitly selected declared member."""
        selected_pyproject = (
            modernizer_workspace_with_projects / "selected" / c.Infra.PYPROJECT_FILENAME
        )
        selected_pyproject.write_text("[invalid", encoding="utf-8")
        modernizer = FlextInfraPyprojectModernizer(
            workspace_root=modernizer_workspace_with_projects,
            apply_changes=True,
            skip_comments=True,
            skip_check=False,
        )
        tm.that(modernizer.run(), eq=1)

    def test_run_rewrite_constraints_requires_uv_lock(
        self, modernizer_workspace: Path
    ) -> None:
        """Reject constraint rewriting when the lock SSOT is unavailable."""
        modernizer = FlextInfraPyprojectModernizer(
            workspace_root=modernizer_workspace,
            apply_changes=True,
            rewrite_constraints=True,
            skip_comments=True,
            skip_check=True,
        )

        tm.that(modernizer.run(), eq=2)

    def test_run_rewrite_constraints_preserves_attached_submodule_lock(
        self, modernizer_workspace: Path
    ) -> None:
        """Treat an attached Git submodule lock as inactive standalone metadata."""
        source_repository = modernizer_workspace.parent / "flext-core-source"
        source_repository.mkdir()
        (source_repository / c.Infra.PYPROJECT_FILENAME).write_text(
            '[project]\nname = "flext-core"\nversion = "0.12.0-dev"\n', encoding="utf-8"
        )
        package_init = source_repository / "src" / "flext_core" / "__init__.py"
        package_init.parent.mkdir(parents=True)
        package_init.write_text('"""FLEXT Core test package."""\n', encoding="utf-8")
        member_lock_content = (
            "version = 1\n"
            "[manifest]\n"
            'members = ["flext-core"]\n'
            "[[package]]\n"
            'name = "typing-extensions"\n'
            'version = "4.15.0"\n'
            'source = { registry = "https://pypi.org/simple" }\n'
        )
        (source_repository / c.Infra.UV_LOCK_FILENAME).write_text(
            member_lock_content, encoding="utf-8"
        )
        u.Tests.initialize_git_repo(source_repository)

        (modernizer_workspace / c.Infra.PYPROJECT_FILENAME).write_text(
            (
                '[project]\nname = "workspace"\nversion = "0.1.0"\n'
                'dependencies = ["requests>=2.0"]\n\n'
                "[tool.uv.workspace]\n"
                'members = ["flext-core"]\n'
            ),
            encoding="utf-8",
        )
        (modernizer_workspace / c.Infra.UV_LOCK_FILENAME).write_text(
            (
                "version = 1\n"
                "[manifest]\n"
                'members = ["workspace", "flext-core"]\n'
                "[[package]]\n"
                'name = "requests"\n'
                'version = "2.32.4"\n'
                'source = { registry = "https://pypi.org/simple" }\n'
            ),
            encoding="utf-8",
        )
        u.Tests.initialize_git_repo(modernizer_workspace)
        u.Tests.git_bootstrap(
            modernizer_workspace,
            (
                "-c",
                "protocol.file.allow=always",
                "submodule",
                "add",
                str(source_repository),
                "flext-core",
            ),
        )
        member_lock = modernizer_workspace / "flext-core" / c.Infra.UV_LOCK_FILENAME

        exit_code = FlextInfraPyprojectModernizer(
            workspace_root=modernizer_workspace,
            apply_changes=True,
            rewrite_constraints=True,
            skip_comments=True,
            skip_check=True,
        ).run()

        tm.that(exit_code, eq=0)
        tm.that(member_lock.read_text(encoding="utf-8"), eq=member_lock_content)
        tm.that(
            (modernizer_workspace / c.Infra.PYPROJECT_FILENAME).read_text(
                encoding="utf-8"
            ),
            has='"requests>=2.32.4"',
        )

    def test_run_apply_rewrites_dependency_constraints_from_uv_lock(
        self, modernizer_workspace: Path
    ) -> None:
        """Rewrite registry constraints while preserving internal dependencies."""
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
        member = modernizer_workspace / "flext-core"
        package = member / "src" / "flext_core"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text("", encoding="utf-8")
        (member / c.Infra.PYPROJECT_FILENAME).write_text(
            '[project]\nname = "flext-core"\nversion = "0.12.0-dev"\n', encoding="utf-8"
        )

        modernizer = FlextInfraPyprojectModernizer(
            workspace_root=modernizer_workspace,
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
        tm.that(rendered, has="\"httpx[socks]>=0.28.1; python_version < '3.14'\"")
        tm.that(rendered, has='"flext-core"')
        tm.that(rendered, has='rich = ">=14.2.0"')
        tm.that(rendered, has='version = ">=3.1.0"')

    def test_run_apply_rewrites_constraints_as_open_floor(
        self, modernizer_workspace: Path
    ) -> None:
        """Use uv.lock as the floor without imposing an artificial upper bound."""
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
            workspace_root=modernizer_workspace,
            apply_changes=True,
            rewrite_constraints=True,
            skip_comments=True,
            skip_check=True,
        )

        tm.that(modernizer.run(), eq=0)
        tm.that(
            (modernizer_workspace / c.Infra.PYPROJECT_FILENAME).read_text(
                encoding="utf-8"
            ),
            has='"requests>=2.32.4"',
        )

    def test_run_scopes_default_audit_to_root_without_external_siblings(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Keep default modernization inside the declared workspace boundary."""
        workspace = tmp_path / "flext"
        workspace.mkdir()
        (workspace / c.Infra.PYPROJECT_FILENAME).write_text(
            "[project]\nname='flext'\n", encoding="utf-8"
        )
        external = tmp_path / "gruponos-data"
        (external / "src" / "gruponos_data").mkdir(parents=True)
        external_pyproject = external / c.Infra.PYPROJECT_FILENAME
        external_pyproject.write_text(
            "[project]\nname='gruponos-data'\ndependencies=['flext-core']\n",
            encoding="utf-8",
        )

        modernizer = FlextInfraPyprojectModernizer(
            workspace_root=workspace, audit=True, skip_comments=True
        )

        tm.that(modernizer.run(), eq=1)
        output = capsys.readouterr().out
        tm.that(output, has="pyproject.toml:")
        tm.that(output, lacks=str(external_pyproject.resolve()))
        tm.that(output, lacks="not in the subpath")

    def test_conform_source_preserves_taplo_process_error(self, tmp_path: Path) -> None:
        """Return the exact formatter process failure from the public conform path."""
        (tmp_path / ".taplo.toml").write_text('include = ["/x/["]\n', encoding="utf-8")
        source = '[project]\nname = "sample"\nversion = "0.1.0"\n'
        modernizer = FlextInfraPyprojectModernizer(workspace_root=tmp_path)

        result = modernizer.conform_source(source, path=tmp_path / "pyproject.toml")

        error = tm.fail(result)
        tm.that(error, has=["taplo format failed (1)", str(tmp_path / ".taplo.toml")])
        tm.that(
            error, lacks=["couldn't exec process", "pyproject tooling render failed"]
        )
