"""Promoted-command framework: help and dry-run rendering for the promoted dispatcher."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.promoted.invocation import param_value

if TYPE_CHECKING:
    from collections.abc import Iterable

    from flext_infra import p
    from flext_infra.promoted.registry import Registry


def render_requested_help(registry: Registry, requested: str) -> str:
    """Render global, verb, or command help from the discovered registry.

    Returns:
        The requested help text.

    """
    # "all" is the conventional catalog selector (make help WHAT=all, the
    # help/all command) and maps to the same global catalog as bare help.
    if requested in {"", "help", "all"}:
        return render_global_help(registry)
    if "/" in requested:
        verb, what = requested.split("/", 1)
        return render_command_help(registry, verb, what)
    return render_verb_help(registry, requested)


def render_global_help(registry: Registry) -> str:
    """Render every discovered verb and the canonical invocation rules.

    Returns:
        The workspace-level help text.

    """
    lines = ["cosmos - make <verbo> WHAT=<acao> [PARAM=value ...]", ""]
    for verb in registry.verbs():
        command = registry.command(verb, "all")
        aliases = registry.aliases_for(verb)
        suffix = f" (alias: {', '.join(aliases)})" if aliases else ""
        lines.append(f"  {verb:14} [{command.domain:12}] {command.summary}{suffix}")
    lines.extend([
        "",
        "make <verbo> mostra o help do verbo e todos os WHAT.",
        "make help WHAT=<verbo> mostra o mesmo help.",
        (
            "make help WHAT=<verbo>/<acao> ou make <verbo> WHAT=<acao> "
            "OPTIONS=Y mostra uma acao."
        ),
        "Comandos mutadores exigem APPLY=Y.",
        (
            "Novos comandos vivem em scripts/<verbo>/<WHAT>.sh|py com header "
            "cosmos-command."
        ),
    ])
    return "\n".join(lines)


def render_verb_help(registry: Registry, requested_verb: str) -> str:
    """Render one verb, its actions, parameters, rules, and examples.

    Returns:
        The verb-level help text.

    """
    verb = registry.resolve_verb(requested_verb)
    aliases = registry.aliases_for(verb)
    alias_suffix = f" (alias: {', '.join(aliases)})" if aliases else ""
    lines = [
        f"make {requested_verb} WHAT=<WHAT>{alias_suffix}",
        "",
        "WHAT disponiveis:",
    ]
    commands = registry.commands(verb)
    for what, command in sorted(commands.items()):
        marker = " [mutates]" if command.mutates else ""
        lines.append(f"  {what:20} [{command.domain:12}] {command.summary}{marker}")
    command_params = [
        (what, command) for what, command in sorted(commands.items()) if command.params
    ]
    if command_params:
        lines.extend(["", "Opcoes por WHAT:"])
        for what, command in command_params:
            lines.append(f"  {what:20} {format_params_inline(command.params)}")
        lines.extend([
            "",
            "Detalhe de uma acao:",
            f"  make help WHAT={requested_verb}/<WHAT>",
            f"  make {requested_verb} WHAT=<WHAT> OPTIONS=Y",
        ])
    rules = sorted({rule for command in commands.values() for rule in command.rules})
    if rules:
        lines.extend(["", "Regras:"])
        lines.extend(f"  - {rule}" for rule in rules)
    examples = sorted({
        example_for(command, requested_verb) for command in commands.values()
    })
    if examples:
        lines.extend(["", "Exemplos:"])
        lines.extend(f"  {example}" for example in examples)
    return "\n".join(lines)


def render_command_help(registry: Registry, requested_verb: str, what: str) -> str:
    """Render the complete contract for one promoted command.

    Returns:
        The command-level help text.

    """
    command = registry.command(requested_verb, what)
    lines = [
        f"make {requested_verb} WHAT={what}",
        "",
        f"Dominio: {command.domain}",
        f"Muta: {'sim' if command.mutates else 'nao'}",
    ]
    if command.mutates:
        lines.append("Dry-run: sem APPLY=Y, o dispatcher nao executa a acao.")
    lines.extend(["", command.summary, command.description])
    if command.params:
        lines.extend(["", "Parametros:"])
        for param in command.params:
            required = " obrigatorio" if param.required else ""
            default = f" default={param.default}" if param.default else ""
            choices = f" choices={','.join(param.choices)}" if param.choices else ""
            lines.append(f"  {param.name:24} {param.help}{required}{default}{choices}")
    if command.rules:
        lines.extend(["", "Regras:"])
        lines.extend(f"  - {rule}" for rule in command.rules)
    lines.extend(["", "Exemplo:", f"  {example_for(command, requested_verb)}"])
    return "\n".join(lines)


def render_dry_run(
    command: p.Infra.Promoted.Command, requested_verb: str, what: str
) -> str:
    """Render the non-mutating inspection of one mutating command.

    Returns:
        The dry-run report.

    """
    lines = [
        "DRY-RUN: nenhuma mutacao executada.",
        f"Comando: make {requested_verb} WHAT={what}",
        f"Dominio: {command.domain}",
        f"Resumo: {command.summary}",
        "Regra: comando mutador exige APPLY=Y.",
    ]
    if command.rules:
        lines.extend(["", "Regras aplicadas:"])
        lines.extend(f"  - {rule}" for rule in command.rules)
    if command.params:
        lines.extend(["", "Parametros atuais:"])
        missing: list[p.Infra.Promoted.Param] = []
        for param in command.params:
            value = param_value(param, command)
            shown = value or "<ausente>"
            required = "obrigatorio" if param.required else "opcional"
            choices = f" choices={','.join(param.choices)}" if param.choices else ""
            lines.append(
                f"  {param.name:24} {shown:24} {required}{choices} - {param.help}"
            )
            if param.required and not value:
                missing.append(param)
        if missing:
            lines.extend(["", "Faltando antes de executar:"])
            lines.extend(f"  {param.name}=<valor>  # {param.help}" for param in missing)
    lines.extend([
        "",
        "Execucao canonica:",
        f"  {example_for(command, requested_verb)}",
        ("  # repita com APPLY=Y somente depois de conferir dominio, escopo e bead."),
    ])
    return "\n".join(lines)


def format_params_inline(params: Iterable[p.Infra.Promoted.Param]) -> str:
    """Render compact parameter metadata for verb help.

    Returns:
        The comma-separated parameter contract.

    """
    parts: list[str] = []
    for param in params:
        suffix = "*" if param.required else ""
        detail: list[str] = []
        if param.default:
            detail.append(f"default={param.default}")
        if param.choices:
            detail.append(f"choices={','.join(param.choices)}")
        rendered = f"{param.name}{suffix}"
        if detail:
            rendered = f"{rendered}({';'.join(detail)})"
        parts.append(rendered)
    return ", ".join(parts)


def example_for(command: p.Infra.Promoted.Command, requested_verb: str) -> str:
    """Render a declared example through the requested alias when needed.

    Returns:
        The canonical or alias-adjusted example.

    """
    canonical = f"make {command.verb}"
    requested = f"make {requested_verb}"
    if (
        requested_verb != command.verb
        and command.example == f"{canonical} WHAT={command.what}"
    ):
        return requested
    if command.example.startswith(canonical):
        return requested + command.example[len(canonical) :]
    return command.example
