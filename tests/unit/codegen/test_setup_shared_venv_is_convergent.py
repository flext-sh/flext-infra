"""Every profile sharing one virtualenv provisions it the same way.

A workspace member has no ``.venv`` of its own: ``RUNTIME_VENV`` resolves to
``RUNTIME_ROOT/.venv``, the root's environment. Provisioning flags, however,
were derived from the *profile* rather than from the venv's owner, so the root
synced with ``--all-packages`` while a member synced without it.

Both then describe the same directory. Measured against the live workspace
venv: the member's flags report "Would uninstall 214 packages" (the siblings
the root just installed), and the root's flags report "The environment is
outdated" right after the member ran. Each ``setup`` undoes the previous one,
so ``uv sync --check`` never converges and the repair path runs in full every
time -- 1m37s on a second consecutive ``make setup``.

That is also the mechanism behind virtualenvs appearing to be "wiped by
another lane": they were not deleted, they were uninstalled by a member's
``setup`` while another lane was using them.

``RUNTIME_VENV`` already derives from ``RUNTIME_ROOT``. ``UV_SYNC_FLAGS`` must
derive from the same owner, so whoever shares an environment agrees on what
that environment contains.
"""

from __future__ import annotations

import re
from pathlib import Path

_TEMPLATE = (
    Path(__file__).resolve().parents[3]
    / "src"
    / "flext_infra"
    / "templates"
    / "project"
    / "base"
    / "Makefile.j2"
)


def _template_text() -> str:
    """Return the generated-Makefile template source."""
    return _TEMPLATE.read_text(encoding="utf-8")


def _assignment(name: str) -> str:
    """Return the single ``NAME :=`` assignment line for one variable."""
    # re.findall is typed list[Any], so the element would carry Any into the
    # declared str return.
    matches: list[str] = re.findall(
        rf"^{name}\s*:?=.*$", _template_text(), re.MULTILINE
    )
    assert len(matches) == 1, f"expected exactly one {name} assignment, got {matches}"
    return matches[0]


def test_sync_flags_derive_from_the_environment_owner() -> None:
    """Provisioning flags follow the venv's owner, not the caller's profile.

    ``RUNTIME_VENV`` is keyed on ``RUNTIME_ROOT``; a flag set keyed on
    ``make_profile`` instead lets two checkouts sharing one directory disagree
    about its contents.
    """
    flags = _assignment("UV_SYNC_FLAGS")

    assert "make_profile" not in flags, (
        "UV_SYNC_FLAGS branches on the caller profile while RUNTIME_VENV "
        f"branches on the environment owner: {flags}"
    )


def test_shared_environment_is_provisioned_with_every_workspace_package() -> None:
    """A shared environment always contains the whole workspace.

    Omitting ``--all-packages`` makes a sync treat sibling packages as surplus
    and remove them, which is what emptied the shared venv mid-work.
    """
    flags = _assignment("UV_SYNC_FLAGS")

    assert "--all-packages" in flags, (
        f"shared environment would be synced without sibling packages: {flags}"
    )


def test_setup_environment_probes_before_repair() -> None:
    """``uv sync --check`` runs before ``uv sync`` so converged venvs skip repair."""
    recipe = (
        _template_text().split("SETUP_ENVIRONMENT_RECIPE = ", 1)[1].split("\n\n", 1)[0]
    )

    assert " sync " in recipe
    assert "--check" in recipe
    check_index = recipe.index("--check")
    repair_index = recipe.rindex(" sync ")
    assert check_index < repair_index, (
        "repair sync must follow the --check probe in SETUP_ENVIRONMENT_RECIPE"
    )


__all__: tuple[str, ...] = ()
