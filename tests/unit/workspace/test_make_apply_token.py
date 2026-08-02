"""The public Make boundary accepts the config-owned absent APPLY token."""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import c, config, m, p
from flext_infra.workspace.make_serialization import FlextInfraMakeSerializationService
from tests import u as test_u


_MAKE = config.Infra.codegen.make
_OPERATIONS = {operation.name: operation for operation in _MAKE.operations}
_READ_ONLY_VERB, _READ_ONLY_HANDLER = next(
    (verb, handler)
    for verb in _MAKE.verbs
    for handler in verb.handlers
    if handler.default
    and handler.apply_policy == "never"
    and (operation := _OPERATIONS[verb.operation]).executor == "bootstrap"
    and operation.scope == "self"
    and operation.consistency == "none"
)


@pytest.fixture
def make_repository(tmp_path: Path) -> Path:
    """Create an isolated managed repository for the public Make service."""
    root = tmp_path / "apply-token-probe"
    package = root / "src" / "apply_token_probe"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    (root / c.Infra.PYPROJECT_FILENAME).write_text(
        "[project]\n"
        'name = "apply-token-probe"\n'
        'version = "0.1.0"\n'
        'requires-python = ">=3.13,<3.14"\n',
        encoding="utf-8",
    )
    (root / c.Infra.MAKEFILE_FILENAME).write_text(
        "# selected Make owner\n", encoding="utf-8"
    )
    provider = config.Infra.codegen.default_provider_spec
    test_u.Tests.initialize_git_repo(
        root, f"{provider.base_url.rstrip('/')}/apply-token-probe.git"
    )
    return root


def _execute(make_repository: Path, apply_token: str) -> p.Result[m.Infra.ProcessExit]:
    """Run one read-only invocation through the public boundary."""
    return FlextInfraMakeSerializationService(
        workspace_root=make_repository,
        makefile=make_repository / c.Infra.MAKEFILE_FILENAME,
        verb=_READ_ONLY_VERB.name,
        selector_value=_READ_ONLY_HANDLER.what,
        apply_token=apply_token,
        make_level=0,
    ).execute()


def test_seeded_absent_token_reads_as_not_applying(make_repository: Path) -> None:
    """The value the generated Makefile seeds never trips the APPLY guard."""
    executed = _execute(make_repository, _MAKE.apply_absent_value)

    assert executed.success, executed.error


def test_empty_token_still_reads_as_not_applying(make_repository: Path) -> None:
    """An unset token keeps meaning that mutation was not enabled."""
    executed = _execute(make_repository, "")

    assert executed.success, executed.error


def test_unknown_token_is_still_rejected(make_repository: Path) -> None:
    """Accepting the declared absent value never widens arbitrary input."""
    invalid_token = f"{_MAKE.apply_value}{_MAKE.apply_absent_value}-invalid"
    executed = _execute(make_repository, invalid_token)

    assert executed.failure
    assert _MAKE.apply_value in (executed.error or "")
