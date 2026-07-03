"""Project-selection service base for flext-infra command services."""

from __future__ import annotations

from typing import Annotated

from flext_infra import m, t
from flext_infra._base_projects import FlextInfraProjectSelectionMixin
from flext_infra.base import FlextInfraServiceBase


class FlextInfraProjectSelectionServiceBase[TDomainResult: t.Cli.ResultValue](
    FlextInfraServiceBase[TDomainResult],
    FlextInfraProjectSelectionMixin,
):
    """Shared service foundation for commands that target workspace projects."""

    selected_projects: Annotated[
        t.StrSequence | None,
        m.Field(alias="projects", description="Projects to process"),
    ] = None


__all__: list[str] = ["FlextInfraProjectSelectionServiceBase"]
