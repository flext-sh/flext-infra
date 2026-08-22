"""Generated Make setup isolates each worktree environment."""

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


def test_provisioning_replaces_only_a_foreign_environment_symlink() -> None:
    recipe = _recipe("SETUP_ENVIRONMENT_RECIPE")
    assert '[ -L "$(RUNTIME_VENV)" ]' in recipe
    assert 'rm -f "$(RUNTIME_VENV)"' in recipe
    assert '[ ! -x "$(RUNTIME_PYTHON)" ]' in recipe


def test_delegated_runtime_sanitizes_recursive_make_state() -> None:
    member_branch = (
        _template_text()
        .split('if [ "$(RUNTIME_ROOT)" = "$(PROJECT_ROOT)" ]; then', 1)[1]
        .split("\n\n", 1)[0]
    )
    for key in ("MAKEFILES", "GNUMAKEFLAGS", "MAKEFLAGS", "PYTHONPATH"):
        assert f"-u {key}" in member_branch


def test_uv_run_prefers_project_src() -> None:
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
