"""Shared typed behavior for CLI route services."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from flext_infra import p, t


class CliRouteBase:
    """Provide the common result-value widening contract for route handlers."""

    @staticmethod
    def command_route[TModel: t.Cli.ModelLike, TResult: t.Cli.ResultValue](
        name: str,
        help_text: str,
        model_cls: t.ModelClass[TModel],
        handler: p.Cli.ResultCommandHandler[TModel, TResult],
        *,
        success_message: str | None = None,
    ) -> t.SequenceOf[p.Cli.ResultCommandRoute]:
        """Build one selected route from its registry-owned descriptor."""
        from flext_infra import m

        def execute(params: TModel) -> p.Result[t.Cli.ResultValue]:
            return handler(params).map(CliRouteBase.as_route_value)

        return (
            m.Cli.ResultCommandRoute(
                name=name,
                help_text=help_text,
                model_cls=model_cls,
                handler=execute,
                success_message=success_message,
            ),
        )

    @staticmethod
    def as_route_value(value: t.Cli.ResultValue) -> t.Cli.ResultValue:
        """Widen a concrete result payload to the CLI route contract value."""
        return value


__all__: list[str] = ["CliRouteBase"]
