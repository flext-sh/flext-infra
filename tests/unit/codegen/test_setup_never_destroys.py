"""``setup`` provisions tooling and never destroys tracked working trees.

``setup`` is invoked automatically, from every verb and from the pre-commit
hook, so anything it mutates it mutates constantly and unattended. That makes
it the one verb allowed to *create* what is missing and forbidden to *destroy*
what exists.

Two live incidents pinned this contract:

``uv venv --clear`` wiped the shared workspace virtualenv on every single
invocation. A concurrent lane's ``setup`` emptied the venv mid-work, and an
unrelated run then failed with ``No module named 'flext_infra'``. The venv is
disposable -- an operator may delete it and ``setup`` must rebuild it -- but
rebuilding it on every call is not provisioning, it is churn.

The submodule recipe ran ``git checkout``/``git pull``/``submodule update``
against every managed gitlink. Invoked inside a member, it reached back into
that member and tried to check out over uncommitted work: "Your local changes
to the following files would be overwritten by checkout". Git refused, so
nothing was lost, but the attempt is the defect.

Working trees, submodules and worktrees are never disposable: they carry
uncommitted work that exists nowhere else. ``setup`` may read and report on
them; it may never move, reset, or overwrite them.
"""

from __future__ import annotations

import re
from pathlib import Path

_TEMPLATES = Path(__file__).resolve().parents[3] / "src" / "flext_infra" / "templates"
_MAKEFILE = _TEMPLATES / "project" / "base" / "Makefile.j2"
_SUBMODULES = _TEMPLATES / "project" / "base" / "submodule_setup_recipe.j2"

# Each pattern moves, replaces or discards tracked content. A verb that runs
# unattended on every invocation may never reach for one of them.
_DESTRUCTIVE_GIT = (
    r"git\b[^\n]*\bcheckout\b",
    r"git\b[^\n]*\bpull\b",
    r"git\b[^\n]*\breset\b",
    r"git\b[^\n]*\bclean\b",
    r"git\b[^\n]*\bsubmodule\b[^\n]*\bupdate\b",
    r"git\b[^\n]*\bworktree\b[^\n]*\b(remove|prune)\b",
)


def _setup_recipe_text() -> str:
    """Return every template line ``setup`` can execute.

    ``_builtin_setup_environment`` is the whole of ``setup``'s body, and it
    pulls in the submodule recipe as a prerequisite, so both files form the
    reachable surface.
    """
    return f"{_MAKEFILE.read_text(encoding='utf-8')}\n{_SUBMODULES.read_text(encoding='utf-8')}"


def _offending_lines(pattern: str) -> list[str]:
    """Return the recipe lines that EXECUTE one destructive pattern.

    A recipe may name a destructive command inside a diagnostic so the operator
    knows what to run by hand; that text is guidance, not execution. Only lines
    that actually invoke the command count, so ``printf``/``echo`` diagnostics
    are excluded rather than the pattern being weakened.
    """
    return [
        stripped
        for line in _setup_recipe_text().splitlines()
        if (stripped := line.strip())
        and re.search(pattern, stripped)
        and not stripped.startswith(("printf", "echo", "#"))
    ]


def test_setup_never_runs_a_destructive_git_operation() -> None:
    """No reachable ``setup`` line may move or discard tracked content.

    ``setup`` runs on every verb and every commit. A destructive git call on
    that path is not a rare hazard, it is a scheduled one.
    """
    offenders = {
        pattern: lines
        for pattern in _DESTRUCTIVE_GIT
        if (lines := _offending_lines(pattern))
    }

    assert not offenders, (
        f"setup reaches destructive git operations: {offenders}"
    )


def test_setup_never_clears_the_virtualenv() -> None:
    """A present virtualenv is repaired in place, never recreated.

    ``uv sync`` already reconciles installs, upgrades and removals, so
    ``--clear`` adds no correctness and costs a full reinstall while other
    lanes are using the same environment.
    """
    offenders = _offending_lines(r"venv\b[^\n]*--clear")

    assert not offenders, f"setup clears the virtualenv: {offenders}"


__all__: tuple[str, ...] = ()
