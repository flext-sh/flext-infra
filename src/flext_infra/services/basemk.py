"""Public basemk service mixin for the infra API facade."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import FlextInfraBaseMkGenerator, m, p, t

if TYPE_CHECKING:
    from flext_infra import FlextInfraServiceBase


class FlextInfraServiceBasemkMixin:
    """Expose canonical base.mk operations through the public infra facade."""

    def generate_basemk(
        self: FlextInfraServiceBase[t.MutableRecursiveContainerMapping],
        settings: m.Infra.BaseMkConfig | t.ScalarMapping | None = None,
    ) -> p.Result[str]:
        """Generate base.mk content using the current facade context."""
        return FlextInfraBaseMkGenerator.model_validate(
            self.command_payload(),
        ).generate_basemk(settings)


__all__: t.StrSequence = ("FlextInfraServiceBasemkMixin",)
