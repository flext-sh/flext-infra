"""Public check service mixin for the infra API facade."""

from __future__ import annotations

from collections.abc import Sequence
from functools import partialmethod

from flext_infra import FlextInfraCliCheck
from flext_infra.services._cli_base import FlextInfraServiceCliRunnerMixin


class FlextInfraServiceCheckMixin(FlextInfraServiceCliRunnerMixin):
    """Expose check CLI execution through the public infra facade."""

    run_check_cli = partialmethod(
        FlextInfraServiceCliRunnerMixin._run_cli,
        FlextInfraCliCheck.run,
    )


__all__: Sequence[str] = ("FlextInfraServiceCheckMixin",)
