"""Test configuration for flext-infra.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import importlib
import sys
import tempfile
from collections.abc import Iterator
from contextlib import ExitStack
from pathlib import Path

import pytest

from flext_infra import config, p
from flext_infra.services.cli_mod_progress import FlextInfraCliModProgress
from tests import c, tm, u

# The installed flext-tests pytest11 plugin owns the shared fixture set; these
# remaining project plugins own the infra-specific fixtures during migration.
# Pytest fixture registration belongs here; reusable construction uses u.Tests.
pytest_plugins = [
    "tests.fixtures.workspace",
    "tests.fixtures.infra",
    "tests.fixtures.provisioning",
]

_TRACKED_CODEGEN_CONFIG_PATH = (
    Path(__file__).resolve().parent.parent
    / c.Infra.CODEGEN_CONFIG_DIR
    / c.Infra.CODEGEN_CONFIG_FILENAME
)
_SESSION_ISOLATION = pytest.StashKey[ExitStack]()
_TRACKED_CODEGEN_CONFIG_BYTES = pytest.StashKey[bytes]()


@pytest.fixture
def real_git_repo(tmp_path: Path) -> Path:
    """Create a real repository through the shared Git construction owner.

    Returns:
        The initialized repository with its initial commit.

    """
    repo_root = tmp_path / "git_repo"
    repo_root.mkdir()
    (repo_root / "README.md").write_text(
        "# Test Repository\n", encoding=c.DEFAULT_ENCODING
    )
    u.Tests.initialize_git_repo(repo_root)
    return repo_root


def pytest_sessionstart(session: pytest.Session) -> None:
    """Isolate the suite's FLEXT caches and snapshot the tracked codegen config.

    Gates resolve their native persistent caches (including Mypy) below
    ``XDG_CACHE_HOME``; a unit test writes only inside session-owned storage,
    so the session scopes that home to one temporary directory per worker and
    restores the environment on exit. The native UV source cache selected
    before that isolation is preserved, so hermetic Git fixtures can read the
    provisioned objects.

    Root cause (flext-eles2): dependency-floor rewrite tests exercised the
    public ``--rewrite-constraints`` entry point through workspaces that never
    declared their own governed SSOT, so the floor writer fell back to the
    packaged/installed ``flext_infra`` config directory — this very checkout
    in an editable install — and silently flipped floors in the real tracked
    file. The floor writer now resolves its target from the modernizer's own
    ``repository_root`` and every workspace fixture declares its own isolated
    ``config/codegen.yaml``; the session snapshot lets
    ``pytest_sessionfinish`` prove the real file stays untouched by the whole
    suite, current and future.
    """
    spec = config.Infra.codegen.make.mypy_cache
    uv_cache = u.Cli.capture([c.Infra.UV, "cache", "dir"]).unwrap().strip()
    isolation = ExitStack()
    cache_home = isolation.enter_context(
        tempfile.TemporaryDirectory(prefix="xdg-cache-"),
    )
    isolation.enter_context(
        u.Tests.env_vars_context({
            "UV_CACHE_DIR": uv_cache,
            spec.data_home_environment_variable: cache_home,
        }),
    )
    session.stash[_SESSION_ISOLATION] = isolation
    session.stash[_TRACKED_CODEGEN_CONFIG_BYTES] = (
        _TRACKED_CODEGEN_CONFIG_PATH.read_bytes()
    )


def pytest_sessionfinish(session: pytest.Session) -> None:
    """Restore the cache environment and fail loud on a tracked config write."""
    session.stash[_SESSION_ISOLATION].close()
    if (
        _TRACKED_CODEGEN_CONFIG_PATH.read_bytes()
        != session.stash[_TRACKED_CODEGEN_CONFIG_BYTES]
    ):
        pytest.exit(
            "test suite modified the tracked repository file "
            f"{_TRACKED_CODEGEN_CONFIG_PATH}; dependency-floor and codegen "
            "writers must target an isolated workspace, never the real "
            "checkout (flext-eles2)",
            returncode=pytest.ExitCode.TESTS_FAILED,
        )


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Resolve native-engine and provisioning applicability before fixtures execute.

    Raises:
        ValueError: If requires_engine arguments must be canonical engine names.

    """
    for item in items:
        item.add_marker(pytest.mark.usefixtures("runner_ci_context_cleared"))
    make = config.Infra.codegen.make
    policy = make.ci
    if u.Infra.env_value(policy.variable).strip() != policy.value:
        return
    excluded_fixtures = frozenset(
        config.Infra.tooling.tools.pytest.ci_excluded_fixtures,
    )
    excluded_engines = frozenset(make.check_gates_default) - frozenset(
        make.check_gates_ci,
    )
    selected: list[pytest.Item] = []
    deselected: list[pytest.Item] = []
    for item in items:
        engines = tuple(
            engine
            for marker in item.iter_markers("requires_engine")
            for engine in marker.args
        )
        if any(not isinstance(engine, str) for engine in engines):
            msg = "requires_engine arguments must be canonical engine names"
            raise ValueError(msg)
        fixtures = tuple(item.fixturenames) if isinstance(item, pytest.Function) else ()
        target = (
            deselected
            if excluded_engines.intersection(engines)
            or excluded_fixtures.intersection(fixtures)
            else selected
        )
        target.append(item)
    if deselected:
        deselected[0].config.hook.pytest_deselected(items=deselected)
    items[:] = selected


@pytest.fixture
def mod_progress() -> p.Infra.ModProgress:
    """Provide the real CLI progress adapter to public mod consumers.

    Returns:
        The progress port used by the normal CLI route.

    """
    return FlextInfraCliModProgress()


@pytest.fixture
def installed_dependency_path(tmp_path: Path) -> Iterator[Path]:
    """Expose real non-src package files through the selected import environment.

    Yields:
        Each ``Path``.

    """
    location = tmp_path / "installed"
    location.mkdir()
    sys.path.insert(0, str(location))
    importlib.invalidate_caches()
    try:
        yield location
    finally:
        sys.path.remove(str(location))
        importlib.invalidate_caches()


@pytest.fixture
def infra_subprocess() -> p.Cli.CommandRunner:
    """Provide the public CLI utility facade for subprocess tests.

    Returns:
        The public command runner implemented by ``u.Cli``.

    """
    return u.Cli()


@pytest.fixture
def infra_toml() -> p.Cli.CommandRunner:
    """Provide the public CLI utility facade for TOML tests.

    Returns:
        The public command runner implemented by ``u.Cli``.

    """
    return u.Cli()


@pytest.fixture
def infra_git() -> u.Infra:
    """Provide the public infrastructure utility facade for Git tests.

    Returns:
        The resulting ``u.Infra``.

    """
    return u.Infra()


@pytest.fixture
def infra_io() -> u.Infra:
    """Provide the public infrastructure utility facade for I/O tests.

    Returns:
        The resulting ``u.Infra``.

    """
    return u.Infra()


@pytest.fixture
def infra_path() -> u.Infra:
    """Provide the public infrastructure utility facade for path tests.

    Returns:
        The resulting ``u.Infra``.

    """
    return u.Infra()


@pytest.fixture
def infra_patterns() -> u.Infra:
    """Provide the public infrastructure utility facade for pattern tests.

    Returns:
        The resulting ``u.Infra``.

    """
    return u.Infra()


@pytest.fixture
def infra_selection() -> u.Infra:
    """Provide the public infrastructure utility facade for selection tests.

    Returns:
        The resulting ``u.Infra``.

    """
    return u.Infra()


@pytest.fixture
def infra_safe_command_output(
    infra_subprocess: p.Cli.CommandRunner,
    infra_test_workspace: Path,
) -> str:
    """Capture successful public command output inside the test workspace.

    Returns:
        The resulting ``str``.

    """
    echo_result = infra_subprocess.capture(
        ["echo", "infra-ok"],
        cwd=infra_test_workspace,
    )
    tm.ok(echo_result)
    pwd_result = infra_subprocess.capture(["pwd"], cwd=infra_test_workspace)
    tm.ok(pwd_result)
    return f"{echo_result.value.strip()}|{pwd_result.value.strip()}"
