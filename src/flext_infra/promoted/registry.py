"""Promoted-command framework: in-memory command registry discovered from script headers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.promoted.base import RegistryError
from flext_infra.promoted.headers import parse_alias_spec
from flext_infra.promoted.invocation import (
    validate_all_choices,
    validate_command_contract,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

    from flext_infra import p


class Registry:
    """In-memory view discovered from script headers; never a static catalog."""

    def __init__(self) -> None:
        """Initialize an empty command registry."""
        self._commands: dict[str, dict[str, p.Infra.Promoted.Command]] = {}
        self._aliases: dict[str, p.Infra.Promoted.AliasTarget] = {}

    def add(self, command: p.Infra.Promoted.Command) -> None:
        """Add one command and its aliases to the registry.

        Raises:
            RegistryError: When the ``(verb, WHAT)`` pair is already registered
                or an alias name already points to a different target.

        """
        from flext_infra import m

        by_what = self._commands.setdefault(command.verb, {})
        if command.what in by_what:
            msg = f"comando duplicado: {command.verb} WHAT={command.what}"
            raise RegistryError(msg)
        by_what[command.what] = command
        for alias in command.aliases:
            alias_name, target_what = parse_alias_spec(alias, command)
            target = m.Infra.Promoted.AliasTarget(verb=command.verb, what=target_what)
            previous = self._aliases.get(alias_name)
            if previous and previous != target:
                msg = (
                    f"alias duplicado: {alias_name} aponta para {previous.verb} WHAT={previous.what} "
                    f"e {target.verb} WHAT={target.what}"
                )
                raise RegistryError(msg)
            self._aliases[alias_name] = target

    def validate(self) -> None:
        """Validate registry invariants after command discovery.

        Raises:
            RegistryError: When no promoted command was discovered or any
                verb/alias invariant is violated.

        """
        if not self._commands:
            msg = "nenhum comando promovido encontrado em scripts/<verbo>/<WHAT>"
            raise RegistryError(msg)
        for verb, commands in sorted(self._commands.items()):
            self._validate_verb(verb, commands)
        self._validate_aliases()

    @staticmethod
    def _validate_verb(
        verb: str, commands: Mapping[str, p.Infra.Promoted.Command]
    ) -> None:
        """Validate one promoted command verb namespace.

        Raises:
            RegistryError: When the verb lacks a ``WHAT=all`` command, declares
                more than one domain, declares aliases outside ``WHAT=all``, or
                a command violates its header contract or WHAT choices.

        """
        if "all" not in commands:
            msg = f"verbo '{verb}' sem"
            raise RegistryError(msg)
        domains = {command.domain for command in commands.values()}
        if len(domains) != 1:
            valid = ", ".join(sorted(domains))
            msg = f"verbo '{verb}' declara mais de um domain: {valid}"
            raise RegistryError(msg)
        for command in commands.values():
            if command.what != "all" and command.aliases:
                msg = f"{command.path}: aliases devem ser declarados apenas em"
                raise RegistryError(msg)
            validate_command_contract(command)
        validate_all_choices(verb, commands)

    def _validate_aliases(self) -> None:
        """Validate alias targets against discovered commands.

        Raises:
            RegistryError: When an alias collides with a promoted verb, points
                to an unknown verb, or points to a WHAT that does not exist.

        """
        for alias, target in self._aliases.items():
            if alias in self._commands:
                msg = f"alias '{alias}' colide com verbo promovido"
                raise RegistryError(msg)
            if target.verb not in self._commands:
                msg = f"alias '{alias}' aponta para verbo desconhecido {target.verb}"
                raise RegistryError(msg)
            if target.what not in self._commands[target.verb]:
                msg = f"alias '{alias}' aponta para {target.verb} WHAT={target.what}, mas a acao nao existe"
                raise RegistryError(msg)

    def resolve_verb(self, verb: str) -> str:
        """Resolve a public verb or alias to the canonical verb.

        Returns:
            The canonical verb: the alias target verb when ``verb`` is an
            alias, otherwise ``verb`` itself.

        Raises:
            RegistryError: When the resolved verb is not registered.

        """
        target = self._aliases.get(verb)
        resolved = target.verb if target is not None else verb
        if resolved not in self._commands:
            msg = f"verbo '{verb}' desconhecido"
            raise RegistryError(msg)
        return resolved

    def alias_target(self, verb: str) -> p.Infra.Promoted.AliasTarget | None:
        """Return the alias target for a requested verb, if any."""
        return self._aliases.get(verb)

    def commands(self, verb: str) -> Mapping[str, p.Infra.Promoted.Command]:
        """Return commands registered for a verb or alias."""
        return self._commands[self.resolve_verb(verb)]

    def command(self, verb: str, what: str) -> p.Infra.Promoted.Command:
        """Return one command by verb and WHAT.

        Raises:
            RegistryError: When ``what`` is not a valid WHAT for ``verb``.

        """
        commands = self.commands(verb)
        if what not in commands:
            valid = " ".join(sorted(commands))
            msg = f"WHAT='{what}' invalido para {verb}. Validos: {valid}"
            raise RegistryError(msg)
        return commands[what]

    def verbs(self) -> list[str]:
        """Return registered verbs in display order."""
        return sorted(self._commands)

    def aliases_for(self, verb: str) -> list[str]:
        """Return aliases that point to one canonical verb."""
        return sorted(
            alias for alias, target in self._aliases.items() if target.verb == verb
        )

    def has(self, verb: str, what: str) -> bool:
        """Return whether a (verb, WHAT) command is already registered.

        FLEXT-STRICT (p/ outro agente): usado pelo discover para que o consumidor
        (raiz scripts/) so preenche lacunas — o submodulo (SCRIPTS) tem prioridade.
        """
        return what in self._commands.get(verb, {})
