"""Test configuration for flext-infra."""

from __future__ import annotations

import importlib
import sys
from pathlib import Path

import pytest
from flext_tests import tm

import flext_infra as infra_pkg
from tests import c
from tests import u

from collections.abc import Iterator
from types import ModuleType

from tests import t

# NOTE(mro-p68a.9.4, agent codex): the installed flext-tests pytest11 plugin is
# the only fixture owner; conftest must not re-export or shadow its fixtures.
pytest_plugins = ["tests.unit.fixtures", "tests.unit.fixtures_git"]


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


def pytest_ignore_collect(collection_path: Path, config: pytest.Config) -> bool | None:
    """Collect only executable test modules from the canonical test tree."""
    del config
    if _is_collectable_test_module(collection_path):
        return None
    return True


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Deselect non-test facade modules that pytest plugins may discover."""
    kept_items: list[pytest.Item] = []
    deselected_items: list[pytest.Item] = []

    for item in items:
        if _is_collectable_test_module(Path(item.path)):
            # mro-wkii.4.15: settings identity is fixed at process startup.
            kept_items.append(item)
            continue
        deselected_items.append(item)

    if deselected_items:
        config.hook.pytest_deselected(items=deselected_items)
        items[:] = kept_items


@pytest.fixture
def infra_test_workspace(tmp_path: Path) -> Path:
    """Create a minimal typed project workspace for public service tests."""
    workspace = tmp_path / "workspace"
    src_pkg = workspace / "src" / "infra_pkg"
    src_pkg.mkdir(parents=True, exist_ok=True)
    (workspace / "pyproject.toml").write_text(
        "[project]\nname='infra-pkg'\nversion='0.0.0'\n", encoding="utf-8"
    )
    (workspace / "Makefile").write_text("help:\n\t@pwd\n", encoding="utf-8")
    (src_pkg / "__init__.py").write_text("", encoding="utf-8")
    return workspace


@pytest.fixture
def infra_subprocess() -> u.Cli:
    """Provide the public CLI utility facade for subprocess tests."""
    return u.Cli()


@pytest.fixture
def infra_toml() -> u.Cli:
    """Provide the public CLI utility facade for TOML tests."""
    return u.Cli()


@pytest.fixture
def infra_git() -> u.Infra:
    """Provide the public infrastructure utility facade for Git tests."""
    return u.Infra()


@pytest.fixture
def infra_io() -> u.Infra:
    """Provide the public infrastructure utility facade for I/O tests."""
    return u.Infra()


@pytest.fixture
def infra_path() -> u.Infra:
    """Provide the public infrastructure utility facade for path tests."""
    return u.Infra()


@pytest.fixture
def infra_patterns() -> u.Infra:
    """Provide the public infrastructure utility facade for pattern tests."""
    return u.Infra()


@pytest.fixture
def infra_selection() -> u.Infra:
    """Provide the public infrastructure utility facade for selection tests."""
    return u.Infra()


@pytest.fixture
def infra_reporting() -> u.Infra:
    """Provide the public infrastructure utility facade for reporting tests."""
    return u.Infra()


@pytest.fixture
def infra_safe_command_output(
    infra_subprocess: u.Cli, infra_test_workspace: Path
) -> str:
    """Capture successful public command output inside the test workspace."""
    echo_result = infra_subprocess.capture(
        ["echo", "infra-ok"], cwd=infra_test_workspace
    )
    tm.ok(echo_result)
    pwd_result = infra_subprocess.capture(["pwd"], cwd=infra_test_workspace)
    tm.ok(pwd_result)
    return f"{echo_result.value.strip()}|{pwd_result.value.strip()}"


@pytest.fixture
def infra_git_repo(infra_subprocess: u.Cli, infra_test_workspace: Path) -> Path:
    """Initialize a local Git repository through the public CLI facade."""
    repo = infra_test_workspace / "repo"
    repo.mkdir(parents=True, exist_ok=True)
    tm.ok(infra_subprocess.run_checked(["git", "init"], cwd=repo))
    tm.ok(
        infra_subprocess.run_checked(
            ["git", "config", "user.email", "infra@example.com"], cwd=repo
        )
    )
    tm.ok(
        infra_subprocess.run_checked(
            ["git", "config", "user.name", "Infra Fixtures"], cwd=repo
        )
    )
    return repo


@pytest.fixture
def rope_project(tmp_path: Path) -> Iterator[t.Infra.RopeProject]:
    """Shared minimal rope project for refactor unit tests."""
    project = u.Infra.init_rope_project(tmp_path, project_prefix="__never__")
    yield project
    project.close()
