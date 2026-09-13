"""Promoted-command framework: promoted dispatcher entrypoints and verb routing."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import TYPE_CHECKING, NoReturn

from flext_infra.promoted.base import (
    RegistryError,
    discovered_workspace_spec,
    env_enabled,
)
from flext_infra.promoted.discovery import discover
from flext_infra.promoted.executor import ensure_local_python, run
from flext_infra.promoted.invocation import validate_apply_env, validate_invocation
from flext_infra.promoted.registry import Registry
from flext_infra.promoted.rendering import (
    render_command_help,
    render_dry_run,
    render_requested_help,
    render_verb_help,
)

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from flext_infra import p


def main(
    argv: Sequence[str] | None = None,
    *,
    script_roots: Sequence[Path] | None = None,
    spec: p.Infra.Promoted.WorkspaceSpec | None = None,
) -> int:
    """Run the promoted command dispatcher.

    Returns:
        The process exit code: the dispatch result, or ``2`` when a
        ``RegistryError`` escapes the dispatch.

    """
    from flext_infra import u

    args = tuple(sys.argv[1:] if argv is None else argv)
    try:
        return run_dispatch(args, script_roots=script_roots, spec=spec)
    except RegistryError as exc:
        u.Cli.error(str(exc))
        return 2


def run_dispatch(
    args: Sequence[str],
    *,
    script_roots: Sequence[Path] | None = None,
    spec: p.Infra.Promoted.WorkspaceSpec | None = None,
) -> int:
    """Run dispatcher logic after common RegistryError handling.

    Returns:
        The selected command's exit code; ``0`` for ``--validate`` and
        successfully rendered help.

    """
    resolved_spec = spec if spec is not None else discovered_workspace_spec()
    ensure_local_python(resolved_spec)
    registry = discover(script_roots=script_roots, spec=resolved_spec)
    if args and args[0] == "--validate":
        return 0
    if not args or args[0] in {"help", "--help", "-h"}:
        requested = os.environ.get("WHAT", "").strip()
        sys.stdout.write(render_requested_help(registry, requested) + "\n")
        return 0
    return dispatch(registry, args[0])


def dispatch(registry: Registry, requested_verb: str) -> int:
    """Dispatch one requested verb to its selected promoted command.

    R28 (operator decision A, 2026-09-12): mutation is the default. An
    absent ``APPLY`` executes a mutating command; ``APPLY=N`` selects
    check/dry-run mode; any other ``APPLY`` value is a hard error.

    Returns:
        The executed command's exit code; ``0`` for rendered help and for a
        mutating command's check-mode (``APPLY=N``) dry run.

    """
    alias_target = registry.alias_target(requested_verb)
    verb = registry.resolve_verb(requested_verb)
    requested_what = os.environ.get("WHAT", "").strip()
    if requested_what == "help":
        sys.stdout.write(render_verb_help(registry, requested_verb) + "\n")
        return 0
    if not requested_what:
        if alias_target is not None and alias_target.what != "all":
            what = alias_target.what
        else:
            sys.stdout.write(render_verb_help(registry, requested_verb) + "\n")
            return 0
    else:
        what = requested_what
    command = registry.command(verb, what)
    if env_enabled("HELP") or env_enabled("OPTIONS"):
        sys.stdout.write(render_command_help(registry, requested_verb, what) + "\n")
        return 0
    apply_value = validate_apply_env(command)
    is_dry_run = command.mutates and apply_value == "N"
    validate_invocation(command, require_required=not is_dry_run)
    if is_dry_run:
        sys.stdout.write(render_dry_run(command, requested_verb, what) + "\n")
        return 0
    return run(command)


def require_dispatched(path: Path) -> None:
    """Fail if a promoted Python command is run outside scripts/dispatch.py.

    FLEXT-STRICT (p/ outro agente): a guarda Python emite a MESMA mensagem
    canonica do bash (scripts/shell/cosmos-command.sh) em stderr antes do
    exit 2, para que a validacao do gate (scripts/check/makefile.sh) capture a
    substring "comandos publicos devem ser executados via make". Sem shim/alias:
    a string e o contrato publico compartilhado entre comandos .sh e .py.

    Raises:
        SystemExit: With code ``2``, after the canonical error line is written
            to stderr, when the command was not launched through the
            dispatcher.

    """
    expected = str(path.resolve())
    if (
        os.environ.get("COSMOS_COMMAND_DISPATCHED") == "Y"
        and os.environ.get("COSMOS_COMMAND_PATH") == expected
    ):
        return
    sys.stderr.write(
        "ERRO: comandos publicos devem ser executados via make <verbo> WHAT=<acao>\n"
    )
    raise SystemExit(2)


def promoted_main(script_file: str | Path, handler: Callable[[], int]) -> NoReturn:
    """Run a promoted Python command through the canonical dispatcher guard.

    Raises:
        SystemExit: Always — with code ``2`` when the dispatcher guard fails,
            otherwise with the handler's exit code.

    """
    require_dispatched(Path(script_file))
    raise SystemExit(handler())


if __name__ == "__main__":
    raise SystemExit(main())
