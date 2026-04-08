"""Pyrefly phase tests for deps modernizer."""

from __future__ import annotations

from collections.abc import MutableMapping
from pathlib import Path

import tomlkit
from flext_tests import tm
from tests import m, u

from flext_infra import (
    FlextInfraEnsurePyreflyConfigPhase,
    FlextInfraExtraPathsManager,
)


def _test_tool_config() -> m.Infra.ToolConfigDocument:
    result = u.Infra.load_tool_config()
    tm.that(not result.is_failure, eq=True)
    if result.is_failure:
        msg = "failed to load tool config"
        raise ValueError(msg)
    return result.value


class TestEnsurePyreflyConfigPhase:
    """Tests pyrefly config phase behavior."""

    def test_ensure_pyrefly_config_sets_fields_root(self) -> None:
        doc = tomlkit.document()
        doc["tool"] = tomlkit.table()
        phase = FlextInfraEnsurePyreflyConfigPhase(_test_tool_config())
        _ = phase.apply(doc, is_root=True)

    def test_ensure_pyrefly_config_non_root(self) -> None:
        doc = tomlkit.document()
        doc["tool"] = tomlkit.table()
        changes = FlextInfraEnsurePyreflyConfigPhase(_test_tool_config()).apply(
            doc,
            is_root=False,
        )
        tm.that(changes, empty=False)


def test_ensure_pyrefly_config_phase_apply_python_version() -> None:
    doc = tomlkit.document()
    doc["tool"] = tomlkit.table()
    tool = doc["tool"]
    assert isinstance(tool, MutableMapping)
    tm.that(tool, is_=MutableMapping)
    tool["pyrefly"] = tomlkit.table()
    _ = FlextInfraEnsurePyreflyConfigPhase(_test_tool_config()).apply(
        doc,
        is_root=True,
    )
    pyrefly = tool["pyrefly"]
    assert isinstance(pyrefly, MutableMapping)
    tm.that(pyrefly, is_=MutableMapping)
    assert u.Cli.toml_unwrap_item(pyrefly["python-version"]) == "3.13"


def test_ensure_pyrefly_config_phase_apply_ignore_errors() -> None:
    doc = tomlkit.document()
    doc["tool"] = tomlkit.table()
    tool = doc["tool"]
    assert isinstance(tool, MutableMapping)
    tm.that(tool, is_=MutableMapping)
    tool["pyrefly"] = tomlkit.table()
    _ = FlextInfraEnsurePyreflyConfigPhase(_test_tool_config()).apply(
        doc,
        is_root=True,
    )
    pyrefly = tool["pyrefly"]
    assert isinstance(pyrefly, MutableMapping)
    tm.that(pyrefly, is_=MutableMapping)
    assert u.Cli.toml_unwrap_item(pyrefly["ignore-errors-in-generated-code"]) is True


def test_ensure_pyrefly_config_phase_apply_search_path() -> None:
    doc = tomlkit.document()
    doc["tool"] = tomlkit.table()
    tool = doc["tool"]
    assert isinstance(tool, MutableMapping)
    tm.that(tool, is_=MutableMapping)
    tool["pyrefly"] = tomlkit.table()
    _ = FlextInfraEnsurePyreflyConfigPhase(_test_tool_config()).apply(
        doc,
        is_root=True,
    )
    pyrefly = tool["pyrefly"]
    assert isinstance(pyrefly, MutableMapping)
    tm.that(pyrefly, is_=MutableMapping)
    assert u.Cli.toml_unwrap_item(pyrefly["search-path"]) == ["src"]


def test_ensure_pyrefly_config_phase_apply_search_path_with_project_context(
    tmp_path: Path,
) -> None:
    project_dir = tmp_path / "flext-core"
    project_dir.mkdir()
    for directory in ("src", "tests", "examples", "scripts"):
        (project_dir / directory).mkdir()

    doc = tomlkit.document()
    doc["tool"] = tomlkit.table()
    tool = doc["tool"]
    assert isinstance(tool, MutableMapping)
    tm.that(tool, is_=MutableMapping)
    tool["pyrefly"] = tomlkit.table()

    _ = FlextInfraEnsurePyreflyConfigPhase(_test_tool_config()).apply(
        doc,
        is_root=False,
        project_dir=project_dir,
        paths_manager=FlextInfraExtraPathsManager(workspace_root=tmp_path),
    )

    pyrefly = tool["pyrefly"]
    assert isinstance(pyrefly, MutableMapping)
    tm.that(pyrefly, is_=MutableMapping)
    search_path = u.Cli.toml_unwrap_item(pyrefly["search-path"])
    assert search_path == [".", "src"]


def test_ensure_pyrefly_config_phase_apply_errors() -> None:
    doc = tomlkit.document()
    doc["tool"] = tomlkit.table()
    tool = doc["tool"]
    assert isinstance(tool, MutableMapping)
    tm.that(tool, is_=MutableMapping)
    tool["pyrefly"] = tomlkit.table()
    _ = FlextInfraEnsurePyreflyConfigPhase(_test_tool_config()).apply(
        doc,
        is_root=True,
    )
    pyrefly = tool["pyrefly"]
    assert isinstance(pyrefly, MutableMapping)
    errors = pyrefly["errors"]
    assert isinstance(errors, MutableMapping)
    tm.that(errors, is_=MutableMapping)
    tm.that(len(errors), gt=0)


def test_ensure_pyrefly_config_phase_is_idempotent() -> None:
    doc = tomlkit.document()
    phase = FlextInfraEnsurePyreflyConfigPhase(_test_tool_config())

    _ = phase.apply(doc, is_root=True)
    second_changes = phase.apply(doc, is_root=True)

    tm.that(second_changes, eq=[])
