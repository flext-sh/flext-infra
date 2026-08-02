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

    @staticmethod
    def _write_registry_constraint_fixture(
        workspace: Path,
    ) -> tuple[tuple[str, str, str], ...]:
        """Write two registry floors and return name/current/locked tuples."""
        registry = (("requests", "2.0", "2.32.4"), ("httpx", "0.1", "0.28.1"))
        requirements = ", ".join(
            f'"{name}>={current}"' for name, current, _locked in registry
        )
        (workspace / c.Infra.PYPROJECT_FILENAME).write_text(
            (
                "[project]\n"
                'name = "workspace"\n'
                'version = "0.1.0"\n'
                f"dependencies = [{requirements}]\n"
            ),
            encoding="utf-8",
        )
        packages = "".join(
            (
                "[[package]]\n"
                f'name = "{name}"\n'
                f'version = "{locked}"\n'
                'source = { registry = "https://pypi.org/simple" }\n'
            )
            for name, _current, locked in registry
        )
        (workspace / c.Infra.UV_LOCK_FILENAME).write_text(
            'version = 1\n[manifest]\nmembers = ["workspace"]\n' + packages,
            encoding="utf-8",
        )
        return registry

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

    def test_run_rewrite_constraints_rejects_member_local_uv_lock(
        self, modernizer_workspace: Path
    ) -> None:
        """Reject a competing lock from a regular workspace member directory."""
        (modernizer_workspace / c.Infra.PYPROJECT_FILENAME).write_text(
            (
                '[project]\nname = "workspace"\nversion = "0.1.0"\n'
                'dependencies = ["requests>=2.0"]\n\n'
                "[tool.uv.workspace]\n"
                'members = ["flext-core"]\n'
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
            ),
            encoding="utf-8",
        )
        member = modernizer_workspace / "flext-core"
        member.mkdir()
        (member / c.Infra.PYPROJECT_FILENAME).write_text(
            '[project]\nname = "flext-core"\nversion = "0.12.0-dev"\n', encoding="utf-8"
        )
        (member / "uv.lock").write_text(
            "version = 1\n[manifest]\nmembers = []\n", encoding="utf-8"
        )
        u.Tests.initialize_git_repo(modernizer_workspace)

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
        tm.ok(
            u.Infra.git_capture(
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

    @pytest.mark.parametrize("selected_index", [0, None], ids=["selected", "full"])
    def test_registry_constraint_rewrite_honors_optional_dependency_selector(
        self, modernizer_workspace: Path, selected_index: int | None
    ) -> None:
        """Rewrite one selected registry floor or every floor when unselected."""
        registry = self._write_registry_constraint_fixture(modernizer_workspace)
        selected_name = (
            registry[selected_index][0].upper() if selected_index is not None else None
        )

        exit_code = FlextInfraPyprojectModernizer(
            workspace_root=modernizer_workspace,
            apply_changes=True,
            rewrite_constraints=True,
            rewrite_dependency=selected_name,
            skip_comments=True,
            skip_check=True,
        ).run()

        rendered = (modernizer_workspace / c.Infra.PYPROJECT_FILENAME).read_text(
            encoding="utf-8"
        )
        tm.that(exit_code, eq=0)
        for index, (name, current, locked) in enumerate(registry):
            expected = locked if selected_index in {None, index} else current
            tm.that(rendered, has=f'"{name}>={expected}"')

    def test_git_dependency_selection_preserves_registry_floors_and_lock_refresh(
        self, modernizer_workspace: Path
    ) -> None:
        """Keep registry floors while preserving the selected Git revision update."""
        registry = self._write_registry_constraint_fixture(modernizer_workspace)
        dependency_name = "fixture-git-dependency"
        previous_revision = "a" * 40
        updated_revision = "b" * 40
        pyproject_path = modernizer_workspace / c.Infra.PYPROJECT_FILENAME
        pyproject_source = pyproject_path.read_text(encoding="utf-8")
        pyproject_path.write_text(
            pyproject_source.replace(
                '"httpx>=0.1"]',
                (
                    f'"httpx>=0.1", "{dependency_name} @ '
                    "git+https://example.invalid/repository.git"
                    f'@{previous_revision}"]'
                ),
                1,
            ),
            encoding="utf-8",
        )
        lock_path = modernizer_workspace / c.Infra.UV_LOCK_FILENAME
        previous_lock = lock_path.read_text(encoding="utf-8") + (
            "[[package]]\n"
            f'name = "{dependency_name}"\n'
            'version = "0.12.0.dev0"\n'
            f'source = {{ git = "https://example.invalid/repository.git?rev={previous_revision}#{previous_revision}" }}\n'
        )
        updated_lock = previous_lock.replace(previous_revision, updated_revision)
        lock_path.write_text(updated_lock, encoding="utf-8")
        payload = u.Cli.toml_mapping_from_text(
            pyproject_path.read_text(encoding="utf-8")
        )
        tm.that(payload, none=False)
        if payload is None:
            pytest.fail("Git dependency fixture must remain valid TOML")
        tm.that(
            u.Infra.declared_dependency_names_from_payload(payload), has=dependency_name
        )
        tm.that(
            u.Infra.locked_dependency_versions(lock_path),
            eq={name: locked for name, _current, locked in registry},
        )

        exit_code = FlextInfraPyprojectModernizer(
            workspace_root=modernizer_workspace,
            apply_changes=True,
            rewrite_constraints=True,
            rewrite_dependency=dependency_name,
            skip_comments=True,
            skip_check=True,
        ).run()

        rendered = (modernizer_workspace / c.Infra.PYPROJECT_FILENAME).read_text(
            encoding="utf-8"
        )
        tm.that(exit_code, eq=0)
        for name, current, _locked in registry:
            tm.that(rendered, has=f'"{name}>={current}"')
        observed_lock = lock_path.read_text(encoding="utf-8")
        tm.that(observed_lock, has=updated_revision)
        tm.that(observed_lock, lacks=previous_revision)
        tm.that(
            observed_lock.replace(updated_revision, previous_revision), eq=previous_lock
        )

    def test_git_only_dependency_selection_accepts_a_valid_non_registry_lock(
        self, modernizer_workspace: Path
    ) -> None:
        """Allow a selected direct requirement when its valid lock has no registry."""
        dependency_name = "fixture-git-dependency"
        revision = "b" * 40
        direct_requirement = (
            f"{dependency_name} @ git+https://example.invalid/repository.git@{revision}"
        )
        pyproject_path = modernizer_workspace / c.Infra.PYPROJECT_FILENAME
        pyproject_path.write_text(
            (
                "[project]\n"
                'name = "workspace"\n'
                'version = "0.1.0"\n'
                f'dependencies = ["{direct_requirement}"]\n'
            ),
            encoding="utf-8",
        )
        (modernizer_workspace / c.Infra.UV_LOCK_FILENAME).write_text(
            (
                "version = 1\n"
                "[[package]]\n"
                f'name = "{dependency_name}"\n'
                'version = "0.12.0.dev0"\n'
                'source = { git = "https://example.invalid/repository.git#revision" }\n'
            ),
            encoding="utf-8",
        )

        exit_code = FlextInfraPyprojectModernizer(
            workspace_root=modernizer_workspace,
            apply_changes=True,
            rewrite_constraints=True,
            rewrite_dependency=dependency_name,
            skip_comments=True,
            skip_check=True,
        ).run()

        tm.that(exit_code, eq=0)
        tm.that(pyproject_path.read_text(encoding="utf-8"), has=direct_requirement)

    @pytest.mark.parametrize(
        "lock_content",
        [
            None,
            "[invalid",
            (
                "version = 1\n"
                "[[package]]\n"
                'name = "different-package"\n'
                'version = "1.0.0"\n'
                'source = { git = "https://example.invalid/different.git#revision" }\n'
            ),
        ],
        ids=["missing", "invalid", "selected-package-absent"],
    )
    def test_git_dependency_selection_rejects_an_unproven_lock(
        self, modernizer_workspace: Path, lock_content: str | None
    ) -> None:
        """Fail closed unless a valid lock contains the selected direct package."""
        dependency_name = "fixture-git-dependency"
        pyproject_path = modernizer_workspace / c.Infra.PYPROJECT_FILENAME
        pyproject_path.write_text(
            (
                "[project]\n"
                'name = "workspace"\n'
                'version = "0.1.0"\n'
                f'dependencies = ["{dependency_name} @ '
                'git+https://example.invalid/repository.git@revision"]\n'
            ),
            encoding="utf-8",
        )
        if lock_content is not None:
            (modernizer_workspace / c.Infra.UV_LOCK_FILENAME).write_text(
                lock_content, encoding="utf-8"
            )

        exit_code = FlextInfraPyprojectModernizer(
            workspace_root=modernizer_workspace,
            apply_changes=True,
            rewrite_constraints=True,
            rewrite_dependency=dependency_name,
            skip_comments=True,
            skip_check=True,
        ).run()

        tm.that(exit_code, eq=2)

    def test_registry_dependency_selection_requires_a_registry_lock_source(
        self, modernizer_workspace: Path
    ) -> None:
        """Reject a registry declaration backed only by a direct-source lock entry."""
        dependency_name = "requests"
        pyproject_path = modernizer_workspace / c.Infra.PYPROJECT_FILENAME
        pyproject_path.write_text(
            (
                "[project]\n"
                'name = "workspace"\n'
                'version = "0.1.0"\n'
                f'dependencies = ["{dependency_name}>=2.0"]\n'
            ),
            encoding="utf-8",
        )
        (modernizer_workspace / c.Infra.UV_LOCK_FILENAME).write_text(
            (
                "version = 1\n"
                "[[package]]\n"
                f'name = "{dependency_name}"\n'
                'version = "2.32.4"\n'
                'source = { git = "https://example.invalid/requests.git#revision" }\n'
            ),
            encoding="utf-8",
        )

        exit_code = FlextInfraPyprojectModernizer(
            workspace_root=modernizer_workspace,
            apply_changes=True,
            rewrite_constraints=True,
            rewrite_dependency=dependency_name,
            skip_comments=True,
            skip_check=True,
        ).run()

        tm.that(exit_code, eq=2)

    def test_dependency_selector_rejects_an_undeclared_distribution(
        self, modernizer_workspace: Path
    ) -> None:
        """Fail closed when a valid selector names no declared requirement."""
        self._write_registry_constraint_fixture(modernizer_workspace)
        pyproject_path = modernizer_workspace / c.Infra.PYPROJECT_FILENAME
        before = pyproject_path.read_text(encoding="utf-8")

        exit_code = FlextInfraPyprojectModernizer(
            workspace_root=modernizer_workspace,
            apply_changes=True,
            rewrite_constraints=True,
            rewrite_dependency="undeclared-dependency",
            skip_comments=True,
            skip_check=True,
        ).run()

        tm.that(exit_code, eq=2)
        tm.that(pyproject_path.read_text(encoding="utf-8"), eq=before)

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
