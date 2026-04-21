"""Shared CLI registration helpers for flext-infra domain groups."""

from __future__ import annotations

from typing import ClassVar

from flext_cli import FlextCli

from flext_infra import c, m, t


class FlextInfraCliGroupBase:
    """Base helper for domain-owned CLI route declarations."""

    _CLI_SERVICE: ClassVar[FlextCli] = FlextCli()
    routes: ClassVar[tuple[m.Cli.ResultCommandRoute, ...]] = ()

    @staticmethod
    def route(
        *,
        name: str,
        help_text: str,
        model_cls: type[object],
        handler: t.Cli.ResultRouteHandler,
        success_message: str | None = None,
    ) -> m.Cli.ResultCommandRoute:
        """Build one declarative result route."""
        return m.Cli.ResultCommandRoute(
            name=name,
            help_text=help_text,
            model_cls=model_cls,
            handler=handler,
            success_message=success_message,
        )

    @classmethod
    def register_routes(cls, app: t.Cli.CliApp) -> None:
        """Register the class-owned routes on the provided app."""
        cls._CLI_SERVICE.register_result_routes(app, cls.routes)


class FlextInfraCliRegistryMixin:
    """Dispatch CLI group registration through MRO-owned domain mixins."""

    def register_group(self, group: str, app: t.Cli.CliApp) -> None:
        """Register one command group using the composed MRO surface."""
        match group:
            case c.Infra.CLI_GROUP_BASEMK:
                self.register_basemk(app)
            case c.Infra.CLI_GROUP_CHECK:
                self.register_check(app)
            case c.Infra.CLI_GROUP_CODEGEN:
                self.register_codegen(app)
            case c.Infra.CLI_GROUP_DEPS:
                self.register_deps(app)
            case c.Infra.CLI_GROUP_DOCS:
                self.register_docs(app)
            case c.Infra.CLI_GROUP_GITHUB:
                self.register_github(app)
            case c.Infra.CLI_GROUP_MAINTENANCE:
                self.register_maintenance(app)
            case c.Infra.CLI_GROUP_REFACTOR:
                self.register_refactor(app)
            case c.Infra.CLI_GROUP_RELEASE:
                self.register_release(app)
            case c.Infra.CLI_GROUP_VALIDATE:
                self.register_validate(app)
            case c.Infra.CLI_GROUP_WORKSPACE:
                self.register_workspace(app)
            case _:
                msg = f"unknown group '{group}'"
                raise ValueError(msg)

    def register_basemk(self, app: t.Cli.CliApp) -> None:
        """Register basemk CLI commands."""
        raise NotImplementedError

    def register_check(self, app: t.Cli.CliApp) -> None:
        """Register check CLI commands."""
        raise NotImplementedError

    def register_codegen(self, app: t.Cli.CliApp) -> None:
        """Register codegen CLI commands."""
        raise NotImplementedError

    def register_deps(self, app: t.Cli.CliApp) -> None:
        """Register deps CLI commands."""
        raise NotImplementedError

    def register_docs(self, app: t.Cli.CliApp) -> None:
        """Register docs CLI commands."""
        raise NotImplementedError

    def register_github(self, app: t.Cli.CliApp) -> None:
        """Register github CLI commands."""
        raise NotImplementedError

    def register_maintenance(self, app: t.Cli.CliApp) -> None:
        """Register maintenance CLI commands."""
        raise NotImplementedError

    def register_refactor(self, app: t.Cli.CliApp) -> None:
        """Register refactor CLI commands."""
        raise NotImplementedError

    def register_release(self, app: t.Cli.CliApp) -> None:
        """Register release CLI commands."""
        raise NotImplementedError

    def register_validate(self, app: t.Cli.CliApp) -> None:
        """Register validate CLI commands."""
        raise NotImplementedError

    def register_workspace(self, app: t.Cli.CliApp) -> None:
        """Register workspace CLI commands."""
        raise NotImplementedError


__all__: list[str] = ["FlextInfraCliGroupBase", "FlextInfraCliRegistryMixin"]
