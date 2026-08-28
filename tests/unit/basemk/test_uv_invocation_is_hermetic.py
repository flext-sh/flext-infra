"""Every generated ``uv`` invocation resolves the project's own runtime.

``uv`` honours ``VIRTUAL_ENV``, ``UV_PROJECT`` and ``UV_PROJECT_ENVIRONMENT``
from the ambient environment. A developer or CI job with another project's
virtualenv active therefore hijacks the runtime: the generated Makefile asks
for ``--project <this repo>`` but ``uv`` resolves interpreter and packages from
the *caller's* environment instead.

The template already knows this. ``FLEXT_INFRA_BOOTSTRAP`` and
``PROJECT_FLEXT_INFRA`` both strip all three variables before calling ``uv``.
``UV_RUN`` -- the definition that actually runs pytest, ruff, pyright and mypy
-- stripped only ``PYTHONPATH`` and ``MYPYPATH``, so the gates were the one
surface left exposed.

That gap produced false evidence, not just a slow path: with another project's
venv exported, ``make test`` imported ``flext_infra`` from that venv's
site-packages and validated this repository's tree against a stale installed
copy. Gate results then describe code that is not under test.

This pins the invariant at the template: no ``uv`` invocation may be built
without environment sanitation -- either the definition strips the hijacking
variables itself, or the template overrides and exports them so Make replaces
any inherited value before a recipe runs.
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

# uv reads these to locate the interpreter and the package set. Any one of them
# left in the environment lets the caller redirect a `--project`-pinned run.
_HIJACKING_VARIABLES = ("VIRTUAL_ENV", "UV_PROJECT", "UV_PROJECT_ENVIRONMENT")


def _template_text() -> str:
    """Return the generated-Makefile template source."""
    return _TEMPLATE.read_text(encoding="utf-8")


def _uv_invocation_definitions() -> dict[str, str]:
    """Return every ``NAME := ...`` definition whose value invokes ``uv``.

    Matches the recursive (``=``) and simple (``:=``) assignment forms the
    template uses, keyed by variable name so a failure names the offender.
    """
    return {
        name: value
        for name, value in re.findall(
            r"^([A-Z_]+)\s*:?=\s*(.*(?:\$\(UV\)|\$\(UV_RUN\)).*)$",
            _template_text(),
            re.MULTILINE,
        )
        if "$(UV)" in value and name != "UV_REQUESTED"
    }


def _unstripped_variables(definition: str) -> list[str]:
    """Return the hijacking variables a definition fails to strip."""
    return [
        variable
        for variable in _HIJACKING_VARIABLES
        if f"-u {variable}" not in definition
    ]


def _template_level_guarded_variables() -> frozenset[str]:
    """Return hijacking variables the template overrides and exports globally.

    ``override NAME := ...`` plus ``export`` makes Make replace any inherited
    value before a recipe runs, which is hermeticity by construction: no uv
    invocation built after that point can observe the caller's environment.
    """
    text = _template_text()
    return frozenset(
        variable
        for variable in _HIJACKING_VARIABLES
        if f"override {variable} :=" in text
        and re.search(rf"^export .*\b{variable}\b", text, re.MULTILINE)
    )


def test_every_uv_invocation_strips_environment_hijacking_variables() -> None:
    """No generated ``uv`` call may inherit another project's environment.

    ``uv run --project X`` is not sufficient on its own: ``VIRTUAL_ENV`` and
    friends win over ``--project``, so the command silently executes against a
    foreign runtime and reports gate results for code it never loaded.
    """
    guarded = _template_level_guarded_variables()
    offenders = {
        name: [variable for variable in unstripped if variable not in guarded]
        for name, definition in _uv_invocation_definitions().items()
        if (unstripped := _unstripped_variables(definition))
    }
    offenders = {name: missing for name, missing in offenders.items() if missing}

    assert not offenders, (
        "generated uv invocations inherit environment that overrides "
        f"--project: {offenders}"
    )


def test_uv_invocations_are_actually_present_in_the_template() -> None:
    """Guard the matcher itself against silently matching nothing.

    If the template's assignment style changes, the invariant above would pass
    vacuously. This keeps the contract honest.
    """
    assert _uv_invocation_definitions(), (
        f"no uv invocation definitions found in {_TEMPLATE}"
    )


def test_gate_runner_uses_the_declared_runtime_without_uv_discovery() -> None:
    """Gate execution cannot create or select a workspace environment."""
    definition = re.search(r"^UV_RUN\s*:?=\s*(.+)$", _template_text(), re.MULTILINE)

    assert definition is not None, "template declares no UV_RUN"
    runner = definition.group(1)
    assert "$(UV) run" not in runner
    assert 'PATH="$(RUNTIME_BIN):$(SANITIZED_CALLER_PATH)"' in runner
    assert 'PYTHONPATH="$(PROJECT_ROOT)/src"' in runner


def test_setup_exports_the_owner_lock_outside_parent_workspace_discovery() -> None:
    """Setup resolves only the manifests copied under its declared runtime."""
    template = _template_text()

    assert "UV_SYNC_FLAGS" not in template
    assert '$(UV) sync --project "$(PROJECT_ROOT)"' not in template
    assert 'cp "$(PROJECT_ROOT)/pyproject.toml"' in template
    assert 'cp "$(PROJECT_ROOT)/uv.lock"' in template
    assert (
        '$(UV) export --quiet --project "$(SETUP_MANIFEST_ROOT)" --locked '
        "--all-extras --all-groups --no-emit-project"
    ) in template
    assert '$(UV) pip sync --python "$(RUNTIME_VENV)"' not in template
    assert (
        '$(UV) pip install --python "$(RUNTIME_VENV)" '
        '--link-mode "$(UV_LINK_MODE)" --exact --no-deps '
        '--requirements "$(SETUP_REQUIREMENTS)" --editable "$(PROJECT_ROOT)"'
    ) in template
    assert "--all-packages" not in template
    assert "SETUP_MANIFEST_ROOT := $(RUNTIME_VENV).flext-setup" in template


def test_dependency_locking_uses_an_isolated_manifest_copy() -> None:
    """Lock commands cannot select or rewrite an ancestor workspace lock."""
    template = _template_text()

    assert 'manifest_root="$(RUNTIME_VENV).flext-lock/$$project"' in template
    assert '$(UV) lock --project "$$manifest_root"' in template
    assert '$(UV) lock --project "$$project_root"' not in template
    assert 'cp "$$manifest_root/uv.lock" "$$project_root/uv.lock"' in template


def test_help_documents_the_isolated_setup_environment() -> None:
    """Operators can discover the supported external environment override."""
    assert (
        "'RUNTIME_VENV' 'isolated environment path override (command line only)'"
        in _template_text()
    )


__all__: tuple[str, ...] = ()
