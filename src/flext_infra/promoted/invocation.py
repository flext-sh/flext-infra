"""Promoted-command framework: promoted invocation contract validation."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from flext_infra.promoted.base import (
    INCIDENT_MUTATION_REQUIRED_PARAMS,
    PROMOTED_APPLY_VALUES,
    RegistryError,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from flext_infra import p


def validate_invocation(
    command: p.Infra.Promoted.Command, *, require_required: bool = True
) -> None:
    """Validate environment parameters before command execution.

    Raises:
        RegistryError: When a required parameter has no value (with
            ``require_required``) or a supplied value is not among the
            parameter's declared choices.

    """
    for param in command.params:
        value = param_value(param, command)
        if require_required and param.required and not value:
            msg = (
                f"{command.verb} WHAT={command.what}: parametro obrigatorio ausente: "
                f"{param.name}; exemplo: {command.example}"
            )
            raise RegistryError(msg)
        if value and param.choices and value not in param.choices:
            valid = "|".join(param.choices)
            msg = f"{command.verb} WHAT={command.what}: {param.name}={value!r} invalido; validos: {valid}"
            raise RegistryError(msg)


def validate_command_contract(command: p.Infra.Promoted.Command) -> None:
    """Validate static command header rules.

    Raises:
        RegistryError: When a declared ``APPLY`` parameter's choices are not a
            subset of ``{"N"}`` (R28: ``APPLY=Y`` is unsupported), or an
            incident-domain mutation omits a required incident parameter.

    """
    param_by_name = {param.name: param for param in command.params}
    apply_param = param_by_name.get("APPLY")
    if apply_param is not None and not set(apply_param.choices) <= {"N"}:
        msg = (
            "[PROMOTED-APPLY] command declares unsupported APPLY choices "
            f"{tuple(apply_param.choices)!r} — violator: {command.path} · "
            "fix: declare APPLY choices as ('N',) or omit the APPLY "
            "parameter (mutation is the default) · "
            "ref: rules/workflow/canonical-commands"
        )
        raise RegistryError(msg)
    if command.domain == "incident" and command.mutates:
        ensure_required_params(
            command, param_by_name, INCIDENT_MUTATION_REQUIRED_PARAMS
        )


def validate_apply_env(command: p.Infra.Promoted.Command) -> str:
    """Validate the ambient ``APPLY`` value against the R28 contract.

    Mutation is the default for every promoted command; ``APPLY=N`` selects
    check/dry-run mode where the command mutates. Any other value — in
    particular the legacy ``APPLY=Y`` — is a hard error.

    Returns:
        The stripped ``APPLY`` value: ``""`` to mutate, ``"N"`` for check mode.

    Raises:
        RegistryError: When ``APPLY`` carries any value other than ``""`` or
            ``"N"``.

    """
    value = os.environ.get("APPLY", "").strip()
    if value not in PROMOTED_APPLY_VALUES:
        msg = (
            f"[PROMOTED-APPLY] unsupported APPLY value {value!r} — violator: "
            f"{command.path} · fix: omit APPLY (mutation is default) or pass "
            "APPLY=N for check mode · ref: rules/workflow/canonical-commands"
        )
        raise RegistryError(msg)
    return value


def validate_all_choices(
    verb: str, commands: Mapping[str, p.Infra.Promoted.Command]
) -> None:
    """Validate WHAT choices on the verb's all command.

    Raises:
        RegistryError: When the ``WHAT=all`` command's declared choices
            diverge from the verb's promoted commands.

    """
    all_command = commands["all"]
    what_param = next(
        (param for param in all_command.params if param.name == "WHAT"), None
    )
    if what_param is None or not what_param.choices:
        return
    declared = tuple(sorted(what_param.choices))
    # The catalog is a LOCAL contract: it mirrors the project that owns the
    # `all` command. A lower-priority root (a parent workspace filling gaps for
    # a nested consumer) must not force every subrepo to enumerate the parent's
    # surface, which would freeze one repository's catalog into another's.
    # Lazy import: executor depends on this module's param_value.
    from flext_infra.promoted.executor import project_root_for

    owner = project_root_for(all_command.path)
    actual = tuple(
        sorted(
            what
            for what, command in commands.items()
            if project_root_for(command.path) == owner
        )
    )
    if declared != actual:
        msg = (
            f"{all_command.path}: choices de WHAT divergem dos comandos promovidos para {verb}: "
            f"declared={','.join(declared)} actual={','.join(actual)}"
        )
        raise RegistryError(msg)


def ensure_required_params(
    command: p.Infra.Promoted.Command,
    params: Mapping[str, p.Infra.Promoted.Param],
    names: Iterable[str],
) -> None:
    """Ensure required parameters are declared for a command contract.

    Raises:
        RegistryError: When any named parameter is undeclared or not marked
            required.

    """
    for name in names:
        param = params.get(name)
        if param is None or not param.required:
            msg = f"{command.path}: parametro {name} deve ser obrigatorio"
            raise RegistryError(msg)


def param_value(
    param: p.Infra.Promoted.Param, command: p.Infra.Promoted.Command
) -> str:
    """Return one parameter value from environment or default."""
    if param.name == "WHAT":
        return command.what
    value = os.environ.get(param.name)
    return param.default.strip() if value is None else value.strip()
