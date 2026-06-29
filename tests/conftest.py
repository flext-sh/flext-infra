"""Test configuration for flext-infra."""

from __future__ import annotations

import importlib
import sys
from collections.abc import Iterator
from pathlib import Path
from types import ModuleType

import pytest
from flext_tests import (
    reset_settings as _shared_reset_settings,
    settings as _shared_settings,
    settings_factory as _shared_settings_factory,
)

import flext_infra as infra_pkg
from flext_infra import FlextInfraSettings
from tests import c, t, u

reset_settings = _shared_reset_settings
settings = _shared_settings
settings_factory = _shared_settings_factory

pytest_plugins = [
    "tests.unit.fixtures",
    "tests.unit.fixtures_git",
]


@pytest.fixture
def reset_infra_settings(reset_settings: None) -> Iterator[None]:
    """Reset project-specific infra settings around each test."""
    del reset_settings
    FlextInfraSettings.reset_for_testing()
    yield
    FlextInfraSettings.reset_for_testing()


@pytest.fixture
def infra_public_root() -> ModuleType:
    """Reload the root public package after clearing lazy-export caches."""
    for export_name in c.Tests.INFRA_PUBLIC_ROOT_EXPORTS:
        _ = infra_pkg.__dict__.pop(export_name, None)
    for module_name in c.Tests.INFRA_PUBLIC_WRAPPER_MODULES:
        _ = sys.modules.pop(module_name, None)
    return importlib.reload(infra_pkg)


def _is_collectable_test_module(collection_path: Path) -> bool:
    tests_root = Path(__file__).parent
    try:
        collection_path.relative_to(tests_root)
    except ValueError:
        return True

    file_name = collection_path.name
    if collection_path.suffix != ".py" or file_name == "conftest.py":
        return True

    return file_name.startswith("test_") or file_name.endswith("_tests.py")


def pytest_ignore_collect(
    collection_path: Path,
    config: pytest.Config,
) -> bool | None:
    del config
    if _is_collectable_test_module(collection_path):
        return None
    return True


def pytest_collection_modifyitems(
    config: pytest.Config,
    items: list[pytest.Item],
) -> None:
    kept_items: list[pytest.Item] = []
    deselected_items: list[pytest.Item] = []

    for item in items:
        if _is_collectable_test_module(Path(item.path)):
            item.add_marker(pytest.mark.usefixtures("reset_infra_settings"))
            kept_items.append(item)
            continue
        deselected_items.append(item)

    if deselected_items:
        config.hook.pytest_deselected(items=deselected_items)
        items[:] = kept_items


@pytest.fixture
def infra_test_workspace(tmp_path: Path) -> Path:
    workspace = tmp_path / "workspace"
    src_pkg = workspace / "src" / "infra_pkg"
    src_pkg.mkdir(parents=True, exist_ok=True)
    (workspace / "pyproject.toml").write_text(
        "[project]\nname='infra-pkg'\nversion='0.0.0'\n",
        encoding="utf-8",
    )
    (workspace / "Makefile").write_text("help:\n\t@pwd\n", encoding="utf-8")
    (src_pkg / "__init__.py").write_text("", encoding="utf-8")
    return workspace


@pytest.fixture
def infra_subprocess() -> u.Cli:
    return u.Cli()


@pytest.fixture
def infra_toml() -> u.Cli:
    return u.Cli()


@pytest.fixture
def infra_git() -> u.Infra:
    return u.Infra()


@pytest.fixture
def infra_io() -> u.Infra:
    return u.Infra()


@pytest.fixture
def infra_path() -> u.Infra:
    return u.Infra()


@pytest.fixture
def infra_patterns() -> u.Infra:
    return u.Infra()


@pytest.fixture
def infra_selection() -> u.Infra:
    return u.Infra()


@pytest.fixture
def infra_reporting() -> u.Infra:
    return u.Infra()


@pytest.fixture
def infra_safe_command_output(
    infra_subprocess: u.Cli,
    infra_test_workspace: Path,
) -> str:
    echo_result = infra_subprocess.capture(
        ["echo", "infra-ok"],
        cwd=infra_test_workspace,
    )
    assert echo_result.success
    pwd_result = infra_subprocess.capture(["pwd"], cwd=infra_test_workspace)
    assert pwd_result.success
    return f"{echo_result.value.strip()}|{pwd_result.value.strip()}"


@pytest.fixture
def infra_git_repo(
    infra_subprocess: u.Cli,
    infra_test_workspace: Path,
) -> Path:
    repo = infra_test_workspace / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    assert infra_subprocess.run_checked(["git", "init"], cwd=repo).success
    assert infra_subprocess.run_checked(
        ["git", "config", "user.email", "infra@example.com"],
        cwd=repo,
    ).success
    assert infra_subprocess.run_checked(
        ["git", "config", "user.name", "Infra Fixtures"],
        cwd=repo,
    ).success
    return repo


@pytest.fixture
def rope_project(tmp_path: Path) -> Iterator[t.Infra.RopeProject]:
    """Shared minimal rope project for refactor unit tests."""
    project = u.Infra.init_rope_project(tmp_path, project_prefix="__never__")
    yield project
    project.close()
