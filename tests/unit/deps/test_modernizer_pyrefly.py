"""Pyrefly phase tests for deps modernizer."""

from __future__ import annotations

from collections.abc import MutableMapping
from typing import TYPE_CHECKING

import tomlkit
from flext_tests import tm

from flext_infra import c, config
from flext_infra.deps.extra_paths import FlextInfraExtraPathsManager
from flext_infra.deps.modernizer import FlextInfraPyprojectModernizer
from flext_infra.deps.phases.ensure_pyrefly import FlextInfraEnsurePyreflyConfigPhase
from tests import t, u

if TYPE_CHECKING:
    from pathlib import Path

    from tests import m


class TestsFlextInfraModernizerPyrefly:
    """Tests pyrefly settings phase behavior."""

    def test_modernizer_uses_git_topology_for_analyzer_virtualenvs(
        self, tmp_path: Path
    ) -> None:
        """Distinguish an attached submodule from an independent linked worktree."""
        child_origin = tmp_path / "child-origin"
        child_origin.mkdir()
        tm.ok(u.Cli.run_raw(["git", "init"], cwd=child_origin))
        pyproject_text = "[project]\nname = 'fixture-child'\nversion = '0.1.0'\n"
        (child_origin / "pyproject.toml").write_text(pyproject_text, encoding="utf-8")
        tm.ok(u.Cli.run_raw(["git", "add", "pyproject.toml"], cwd=child_origin))
        tm.ok(
            u.Cli.run_raw(
                [
                    "git",
                    "-c",
                    "user.name=FLEXT Tests",
                    "-c",
                    "user.email=tests@flext.dev",
                    "commit",
                    "-m",
                    "fixture",
                ],
                cwd=child_origin,
            )
        )
        workspace = tmp_path / "workspace"
        workspace.mkdir()
        tm.ok(u.Cli.run_raw(["git", "init"], cwd=workspace))
        tm.ok(
            u.Cli.run_raw(
                [
                    "git",
                    "-c",
                    "protocol.file.allow=always",
                    "submodule",
                    "add",
                    str(child_origin),
                    "attached",
                ],
                cwd=workspace,
            )
        )
        linked = tmp_path / "linked"
        tm.ok(
            u.Cli.run_raw(
                ["git", "worktree", "add", "--detach", str(linked)], cwd=child_origin
            )
        )
        attached = workspace / "attached"
        for project_dir in (attached, linked):
            changes = FlextInfraPyprojectModernizer(
                workspace_root=project_dir,
                apply_changes=True,
                skip_comments=True,
                skip_check=True,
            ).process_file(
                project_dir / "pyproject.toml",
                canonical_dev=(),
                dry_run=False,
                skip_comments=True,
            )
            tm.that(changes, lacks="failed to resolve")

        attached_payload = u.Cli.toml_mapping_from_text(
            (attached / "pyproject.toml").read_text(encoding="utf-8")
        )
        linked_payload = u.Cli.toml_mapping_from_text(
            (linked / "pyproject.toml").read_text(encoding="utf-8")
        )
        if attached_payload is None or linked_payload is None:
            message = "modernized pyproject must remain valid TOML"
            raise AssertionError(message)
        attached_tool = u.Cli.json_as_mapping(attached_payload["tool"])
        linked_tool = u.Cli.json_as_mapping(linked_payload["tool"])
        attached_pyrefly = u.Cli.json_as_mapping(attached_tool["pyrefly"])
        linked_pyrefly = u.Cli.json_as_mapping(linked_tool["pyrefly"])
        attached_pyright = u.Cli.json_as_mapping(attached_tool["pyright"])
        linked_pyright = u.Cli.json_as_mapping(linked_tool["pyright"])
        rules = config.Infra.tooling.tools.pyright.path_rules
        tm.that(
            attached_pyrefly["python-interpreter-path"],
            eq=f"{rules.project_venv_path}/{rules.venv_name}/bin/python",
        )
        tm.that(attached_pyright["venvPath"], eq=rules.project_venv_path)
        tm.that(
            linked_pyrefly["python-interpreter-path"],
            eq=f"{rules.root_venv_path}/{rules.venv_name}/bin/python",
        )
        tm.that(linked_pyright["venvPath"], eq=rules.root_venv_path)

    def test_ensure_pyrefly_config_sets_fields_root(
        self, tool_config_document: m.Infra.ToolConfigDocument
    ) -> None:
        """Verify root projects receive the canonical Pyrefly fields."""
        doc = tomlkit.document()
        doc["tool"] = tomlkit.table()
        phase = FlextInfraEnsurePyreflyConfigPhase(tool_config_document)
        _ = phase.apply(doc, is_root=True)

    def test_ensure_pyrefly_config_non_root(
        self, tool_config_document: m.Infra.ToolConfigDocument
    ) -> None:
        """Verify child projects receive Pyrefly configuration changes."""
        doc = tomlkit.document()
        doc["tool"] = tomlkit.table()
        changes = FlextInfraEnsurePyreflyConfigPhase(tool_config_document).apply(
            doc, is_root=False
        )
        tm.that(changes, empty=False)

    def test_ensure_pyrefly_config_removes_fallback_interpreter_name(
        self, tool_config_document: m.Infra.ToolConfigDocument
    ) -> None:
        """Verify the obsolete fallback interpreter setting is removed."""
        doc = tomlkit.document()
        doc["tool"] = tomlkit.table()
        tool = doc["tool"]
        tm.that(tool, is_=MutableMapping)
        tool["pyrefly"] = tomlkit.table()
        pyrefly = tool["pyrefly"]
        tm.that(pyrefly, is_=MutableMapping)
        pyrefly["fallback-python-interpreter-name"] = "python"

        changes = FlextInfraEnsurePyreflyConfigPhase(tool_config_document).apply(
            doc, is_root=True
        )

        tm.that("python-interpreter-path" in pyrefly, eq=True)
        tm.that("fallback-python-interpreter-name" in pyrefly, eq=False)
        tm.that(
            any(
                "tool.pyrefly.fallback-python-interpreter-name removed" in change
                for change in changes
            ),
            eq=True,
        )

    def test_ensure_pyrefly_config_phase_apply_python_version(
        self, tool_config_document: m.Infra.ToolConfigDocument
    ) -> None:
        """Verify the canonical Python version is written."""
        doc = tomlkit.document()
        doc["tool"] = tomlkit.table()
        tool = doc["tool"]
        tm.that(tool, is_=MutableMapping)
        tool["pyrefly"] = tomlkit.table()
        _ = FlextInfraEnsurePyreflyConfigPhase(tool_config_document).apply(
            doc, is_root=True
        )
        pyrefly = tool["pyrefly"]
        tm.that(pyrefly, is_=MutableMapping)
        tm.that(u.Cli.toml_unwrap_item(pyrefly["python-version"]), eq="3.13")

    def test_ensure_pyrefly_config_phase_apply_ignore_errors(
        self, tool_config_document: m.Infra.ToolConfigDocument
    ) -> None:
        """Verify generated-code error handling follows canonical policy."""
        doc = tomlkit.document()
        doc["tool"] = tomlkit.table()
        tool = doc["tool"]
        tm.that(tool, is_=MutableMapping)
        tool["pyrefly"] = tomlkit.table()
        _ = FlextInfraEnsurePyreflyConfigPhase(tool_config_document).apply(
            doc, is_root=True
        )
        pyrefly = tool["pyrefly"]
        tm.that(pyrefly, is_=MutableMapping)
        tm.that(
            u.Cli.toml_unwrap_item(pyrefly["ignore-errors-in-generated-code"]), eq=True
        )

    def test_ensure_pyrefly_config_phase_apply_search_path(
        self, tool_config_document: m.Infra.ToolConfigDocument
    ) -> None:
        """Verify the default Pyrefly search path is written."""
        doc = tomlkit.document()
        doc["tool"] = tomlkit.table()
        tool = doc["tool"]
        tm.that(tool, is_=MutableMapping)
        tool["pyrefly"] = tomlkit.table()
        _ = FlextInfraEnsurePyreflyConfigPhase(tool_config_document).apply(
            doc, is_root=True
        )
        pyrefly = tool["pyrefly"]
        tm.that(pyrefly, is_=MutableMapping)
        tm.that(u.Cli.toml_unwrap_item(pyrefly["search-path"]), eq=["src"])

    def test_ensure_pyrefly_config_phase_apply_search_path_with_project_context(
        self, tmp_path: Path, tool_config_document: m.Infra.ToolConfigDocument
    ) -> None:
        """Verify project context contributes existing source directories."""
        project_dir = tmp_path / "flext-core"
        project_dir.mkdir()
        for directory in ("src", "tests", "examples", "scripts"):
            (project_dir / directory).mkdir()
        (project_dir / "tests" / "test_placeholder.py").write_text(
            "def test_placeholder() -> None:\n    assert True\n", encoding="utf-8"
        )

        doc = tomlkit.document()
        doc["tool"] = tomlkit.table()
        tool = doc["tool"]
        tm.that(tool, is_=MutableMapping)
        tool["pyrefly"] = tomlkit.table()

        _ = FlextInfraEnsurePyreflyConfigPhase(tool_config_document).apply(
            doc,
            is_root=False,
            project_dir=project_dir,
            paths_manager=FlextInfraExtraPathsManager(workspace_root=tmp_path),
        )

        pyrefly = tool["pyrefly"]
        tm.that(pyrefly, is_=MutableMapping)
        search_path = u.Cli.toml_unwrap_item(pyrefly["search-path"])
        tm.that(search_path, eq=[".", "src"])

    def test_ensure_pyrefly_config_uses_declared_future_source_root(
        self, tmp_path: Path, tool_config_document: m.Infra.ToolConfigDocument
    ) -> None:
        """Keep pre-write import roots identical to post-write discovery."""
        project_dir = tmp_path / "flext-core"
        project_dir.mkdir()
        doc = tomlkit.document()

        _ = FlextInfraEnsurePyreflyConfigPhase(tool_config_document).apply(
            doc,
            is_root=False,
            project_dir=project_dir,
            paths_manager=FlextInfraExtraPathsManager(workspace_root=tmp_path),
            declared_python_dirs=("src", "tests"),
        )

        tool = doc["tool"]
        tm.that(tool, is_=MutableMapping)
        pyrefly = tool["pyrefly"]
        tm.that(pyrefly, is_=MutableMapping)
        tm.that(u.Cli.toml_unwrap_item(pyrefly["search-path"]), eq=[".", "src"])
        tm.that(
            u.Cli.toml_unwrap_item(pyrefly[c.Infra.PROJECT_INCLUDES]),
            eq=["src/**/*.py*", "tests/**/*.py*"],
        )

    def test_ensure_pyrefly_config_uses_pyright_include_when_available(
        self, tmp_path: Path, tool_config_document: m.Infra.ToolConfigDocument
    ) -> None:
        """Verify Pyright include paths feed project-scoped Pyrefly config."""
        project_dir = tmp_path / "flext-core"
        project_dir.mkdir()
        for directory in ("src", "tests"):
            (project_dir / directory).mkdir()
        (project_dir / c.Infra.PYPROJECT_FILENAME).write_text(
            "[tool.pyright]\ninclude = ['src']\n", encoding="utf-8"
        )

        doc = tomlkit.document()
        doc["tool"] = tomlkit.table()
        tool = doc["tool"]
        tm.that(tool, is_=MutableMapping)
        tool["pyrefly"] = tomlkit.table()

        _ = FlextInfraEnsurePyreflyConfigPhase(tool_config_document).apply(
            doc,
            is_root=False,
            project_dir=project_dir,
            paths_manager=FlextInfraExtraPathsManager(workspace_root=tmp_path),
        )

        pyrefly = tool["pyrefly"]
        tm.that(pyrefly, is_=MutableMapping)
        project_includes = u.Cli.toml_unwrap_item(pyrefly[c.Infra.PROJECT_INCLUDES])
        tm.that(project_includes, eq=["src/**/*.py*", "tests/**/*.py*"])

    def test_ensure_pyrefly_config_phase_apply_search_path_with_root_context(
        self, tmp_path: Path, tool_config_document: m.Infra.ToolConfigDocument
    ) -> None:
        """Verify root context includes workspace dependency source paths."""
        for directory in ("src", "tests"):
            (tmp_path / directory).mkdir()
        (tmp_path / "tests" / "__init__.py").write_text("", encoding="utf-8")
        (tmp_path / "pyproject.toml").write_text(
            (
                "[project]\n"
                "name = 'flext'\n"
                "dependencies = ['flext-core']\n"
                "[tool.uv.workspace]\n"
                "members = ['flext-core']\n"
            ),
            encoding="utf-8",
        )
        dep_root = tmp_path / "flext-core"
        dep_root.mkdir()
        (dep_root / ".git").mkdir()
        (dep_root / "Makefile").write_text("", encoding="utf-8")
        (dep_root / "pyproject.toml").write_text(
            "[project]\nname = 'flext-core'\n", encoding="utf-8"
        )
        (dep_root / "src" / "flext_core").mkdir(parents=True)
        (dep_root / "src" / "flext_core" / "__init__.py").write_text(
            "", encoding="utf-8"
        )

        doc = tomlkit.document()
        doc["tool"] = tomlkit.table()
        tool = doc["tool"]
        tm.that(tool, is_=MutableMapping)
        tool["pyrefly"] = tomlkit.table()

        _ = FlextInfraEnsurePyreflyConfigPhase(tool_config_document).apply(
            doc,
            is_root=True,
            project_dir=tmp_path,
            paths_manager=FlextInfraExtraPathsManager(workspace_root=tmp_path),
        )

        pyrefly = tool["pyrefly"]
        tm.that(pyrefly, is_=MutableMapping)
        search_path = u.Cli.toml_unwrap_item(pyrefly["search-path"])
        tm.that(search_path, eq=[".", "flext-core/src", "src"])

    def test_ensure_pyrefly_config_phase_apply_errors(
        self, tool_config_document: m.Infra.ToolConfigDocument
    ) -> None:
        """Verify the canonical Pyrefly error table is populated."""
        doc = tomlkit.document()
        doc["tool"] = tomlkit.table()
        tool = doc["tool"]
        tm.that(tool, is_=MutableMapping)
        tool["pyrefly"] = tomlkit.table()
        _ = FlextInfraEnsurePyreflyConfigPhase(tool_config_document).apply(
            doc, is_root=True
        )
        pyrefly = tool["pyrefly"]
        tm.that(pyrefly, is_=MutableMapping)
        errors = pyrefly["errors"]
        tm.that(errors, is_=MutableMapping)
        tm.that(len(errors), gt=0)

    def test_ensure_pyrefly_config_phase_removes_stale_error_keys(
        self, tool_config_document: m.Infra.ToolConfigDocument
    ) -> None:
        """Verify stale error keys are removed from TOML documents."""
        doc = tomlkit.document()
        doc["tool"] = tomlkit.table()
        tool = doc["tool"]
        tm.that(tool, is_=MutableMapping)
        tool["pyrefly"] = tomlkit.table()
        pyrefly = tool["pyrefly"]
        tm.that(pyrefly, is_=MutableMapping)
        pyrefly["errors"] = tomlkit.table()
        errors = pyrefly["errors"]
        tm.that(errors, is_=MutableMapping)
        errors["annotation-mismatch"] = "error"

        changes = FlextInfraEnsurePyreflyConfigPhase(tool_config_document).apply(
            doc, is_root=True
        )

        tm.that("annotation-mismatch" in errors, eq=False)
        tm.that("bad-argument-count" in errors, eq=True)
        tm.that(
            any(
                "tool.pyrefly.errors.annotation-mismatch removed" in c for c in changes
            ),
            eq=True,
        )

    def test_ensure_pyrefly_config_payload_removes_stale_error_keys(
        self, tool_config_document: m.Infra.ToolConfigDocument
    ) -> None:
        """Verify stale error keys are removed from plain payloads."""
        errors: t.JsonDict = {"annotation-mismatch": "error"}
        pyrefly: t.JsonDict = {"errors": errors}
        tool: t.JsonDict = {"pyrefly": pyrefly}
        payload: t.MutableJsonMapping = {"tool": tool}

        changes = FlextInfraEnsurePyreflyConfigPhase(
            tool_config_document
        ).apply_payload(payload, is_root=True)

        errors_after = t.Infra.MUTABLE_INFRA_MAPPING_ADAPTER.validate_python(
            u.Cli.toml_mapping_path(payload, (c.Infra.TOOL, c.Infra.PYREFLY, "errors"))
        )
        tm.that("annotation-mismatch" in errors_after, eq=False)
        tm.that("bad-argument-count" in errors_after, eq=True)
        tm.that(
            any(
                "tool.pyrefly.errors.annotation-mismatch removed" in c for c in changes
            ),
            eq=True,
        )

    def test_ensure_pyrefly_config_phase_is_idempotent(
        self, tool_config_document: m.Infra.ToolConfigDocument
    ) -> None:
        """Verify a second Pyrefly phase run produces no changes."""
        doc = tomlkit.document()
        phase = FlextInfraEnsurePyreflyConfigPhase(tool_config_document)

        _ = phase.apply(doc, is_root=True)
        second_changes = phase.apply(doc, is_root=True)

        tm.that(second_changes, empty=True)
