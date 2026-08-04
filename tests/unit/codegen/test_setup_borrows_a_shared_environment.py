"""``setup`` never provisions an environment another checkout owns.

A `make work` lane shares the primary checkout's environment through a symlink at
its own ``.venv`` name. Provisioning that name would sync the owner's directory
from the borrower's project, rewriting the editable pointers the owner and every
sibling lane resolve through. A delegated runtime (a workspace member whose
environment lives at the principal) gets the same link, so generated tooling can
address ``${workspaceFolder}/.venv`` without a cross-project relative hop
(mro-c6di).
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


def _recipe(name: str) -> str:
    """Return one recipe macro body from its assignment to the blank line."""
    body = _template_text().split(f"{name} = ", 1)
    assert len(body) == 2, f"template declares no {name}"
    return body[1].split("\n\n", 1)[0]


def test_provisioning_is_skipped_for_a_borrowed_environment() -> None:
    """A symlinked runtime environment is recognized before any uv call."""
    recipe = _recipe("SETUP_ENVIRONMENT_RECIPE")

    guard = recipe.index('[ -L "$(RUNTIME_VENV)" ]')
    assert guard < recipe.index("$(UV) venv"), (
        "setup creates a venv before checking whether one is borrowed"
    )
    assert guard < recipe.index("$(UV) sync"), (
        "setup syncs before checking whether the environment is borrowed"
    )


def test_a_delegated_runtime_is_linked_at_the_project_environment_name() -> None:
    """The project-local environment name resolves without leaving the project."""
    recipe = _recipe("BORROW_RUNTIME_VENV_RECIPE")

    assert '"$(RUNTIME_VENV)" "$(PROJECT_VENV)"' in recipe
    assert '[ -L "$(PROJECT_VENV)" ]' in recipe, (
        "linking must refuse to replace a real local environment"
    )
    member_branch = _template_text().split(
        'if [ "$(RUNTIME_ROOT)" = "$(PROJECT_ROOT)" ]; then', 1
    )[1]
    assert "$(BORROW_RUNTIME_VENV_RECIPE)" in member_branch.split("\n\n", 1)[0], (
        "a delegated member never links its environment name"
    )


def test_uv_run_prefers_project_src_over_borrowed_editable() -> None:
    """Borrowed envs keep the primary editable; local src must win on PYTHONPATH."""
    template = _template_text()
    assert 'PYTHONPATH="$(PROJECT_ROOT)/src"' in template
    assert "env -u PYTHONPATH -u MYPYPATH $(UV) run" not in template


def test_the_generated_makefile_encodes_no_foreign_path() -> None:
    """No recipe line may address another project or an absolute host path."""
    offenders = [
        stripped
        for line in _template_text().splitlines()
        if (stripped := line.strip())
        and not stripped.startswith("#")
        and (re.search(r"(?<![\w.])\.\./", stripped) or "/home/" in stripped)
    ]

    assert not offenders, f"generated Make encodes a foreign path: {offenders}"


__all__: tuple[str, ...] = ()
