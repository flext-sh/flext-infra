"""Runtime vs dev dependency detector CLI with deptry, pip-check, and typing analysis.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from flext_infra import m, p, u
from flext_infra.deps import (
    FlextInfraDependencyDetectionService,
    FlextInfraDependencyDetectorRuntime,
)


class FlextInfraRuntimeDevDependencyDetector:
    """Compose dependency detection from the canonical validated command."""

    log = u.fetch_logger(__name__)

    @classmethod
    def execute(cls, params: m.Infra.DetectCommand) -> p.Result[bool]:
        """Execute dependency detection and generate workspace report.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        # This command is the CLI composition point of the detect route: it
        # wires the dependency-analysis port into the runtime it drives.
        runtime = FlextInfraDependencyDetectorRuntime(
            detector=cls(),
            deps=FlextInfraDependencyDetectionService(),
        )
        return runtime.run(params)


__all__: list[str] = ["FlextInfraRuntimeDevDependencyDetector"]
