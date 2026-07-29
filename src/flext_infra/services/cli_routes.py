"""Registry-selected composition for every flext-infra CLI route."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

from flext_infra.cli_registry import (
    CLI_COMMAND_DESCRIPTIONS,
    CLI_COMMAND_LOADERS,
    CLI_GROUP_WHAT_STRATEGIES,
)

if TYPE_CHECKING:
    from flext_infra import p, t


class CliRouteService:
    """Resolve exactly one implementation from the generated route registry."""

    @staticmethod
    def command_descriptions(group: str) -> t.StrMapping:
        """Return the selected group's generated lightweight descriptors."""
        return CLI_COMMAND_DESCRIPTIONS.get(group, {})

    @classmethod
    def route_names(cls, group: str) -> frozenset[str]:
        """Return public names from the generated registry."""
        return frozenset(cls.command_descriptions(group))

    @staticmethod
    def what_strategy(group: str) -> str:
        """Return the config-owned ``--what`` translation strategy."""
        return CLI_GROUP_WHAT_STRATEGIES[group]

    @staticmethod
    def _route_loader(group: str, command: str) -> p.Infra.CliRouteLoader:
        """Import only the exact loader referenced by the generated registry."""
        from flext_infra import p

        loader_ref = CLI_COMMAND_LOADERS[group][command]
        module_name, _, owner_ref = loader_ref.partition(":")
        owner_name, _, method_name = owner_ref.partition(".")
        owner = getattr(import_module(module_name), owner_name, None)
        loader = getattr(owner, method_name, None)
        if not isinstance(loader, p.Infra.CliRouteLoader):
            msg = f"invalid CLI route loader '{loader_ref}'"
            raise TypeError(msg)
        return loader

    @classmethod
    def routes_for(
        cls, group: str, command: str | None = None
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Load only the exact selected command route."""
        if command is None:
            return ()
        loader = cls._route_loader(group, command)
        return loader(name=command, help_text=CLI_COMMAND_DESCRIPTIONS[group][command])


__all__: list[str] = ["CliRouteService"]
