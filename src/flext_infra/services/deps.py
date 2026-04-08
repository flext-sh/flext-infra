"""Public dependency service mixin for the infra API facade."""

from __future__ import annotations

from collections.abc import Sequence
from functools import partialmethod

from flext_infra import FlextInfraCliDeps
from flext_infra.services._cli_base import FlextInfraServiceCliRunnerMixin


class FlextInfraServiceDepsMixin(FlextInfraServiceCliRunnerMixin):
    """Expose dependency CLI execution through the public infra facade."""

    run_deps_cli = partialmethod(
        FlextInfraServiceCliRunnerMixin._run_cli,
        FlextInfraCliDeps.run,
    )


__all__: Sequence[str] = ("FlextInfraServiceDepsMixin",)
