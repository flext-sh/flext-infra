"""Public facade fixtures for FLEXT infra tests.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import importlib
import sys
from collections.abc import Iterator
from pathlib import Path

import pytest

from flext_infra import p
from flext_infra.services.cli_mod_progress import FlextInfraCliModProgress
from tests import tm, u


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
