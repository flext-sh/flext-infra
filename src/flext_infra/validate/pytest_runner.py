"""Public cached pytest runner composed from its private strict phases."""

from __future__ import annotations

from flext_infra.validate._pytest_runner.execution import (
    FlextInfraPytestRunnerExecution,
)


class FlextInfraPytestRunner(FlextInfraPytestRunnerExecution):
    """Run the complete suite through one persistent testmon database."""


__all__: list[str] = ["FlextInfraPytestRunner"]
