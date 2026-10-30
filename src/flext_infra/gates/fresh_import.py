"""Fresh-process import quality gate.

Imports the checkout's published package and its declared entry points in
fresh child processes of the checkout's own runtime. ``make check`` and staged
generation admission share this proof, using the physical environment that
``make setup`` provisions rather than creating or borrowing a candidate venv.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import time
from collections.abc import Sequence
from typing import TYPE_CHECKING, ClassVar, override

from flext_infra import c, m, u
from flext_infra.gates import FlextInfraGates
from flext_infra.validate import FlextInfraValidateFreshImport

if TYPE_CHECKING:
    from pathlib import Path


class FlextInfraGatesFreshImport(FlextInfraGates):
    """Fresh-process import gate over the checkout's own package."""

    gate_id: ClassVar[str] = c.Infra.FRESH_IMPORT
    gate_name: ClassVar[str] = "Fresh-Process Import"
    can_fix: ClassVar[bool] = False
    requires_python_targets: ClassVar[bool] = True

    @override
    def selected_for(self, project_dir: Path, ctx: m.Infra.GateContext) -> bool:
        """Select a project that publishes an importable package layout.

        The canonical layout owner reads project metadata; no copied workspace
        package flag may override that public contract.

        Returns:
            Whether the project publishes a Python package to import.

        """
        return (
            super().selected_for(project_dir, ctx)
            and u.Infra.layout(project_dir) is not None
        )

    @override
    def check(
        self,
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.GateExecution:
        """Import the project's package and entry points in fresh processes.

        Returns:
            The resulting ``m.Infra.GateExecution``.

        """
        started = time.monotonic()
        # Live checks derive their runtime from the checkout. Candidate admission
        # explicitly binds that physical owner without borrowing its source tree.
        # ``build_report`` keeps violations
        # structured so a broken invocation (missing runtime, unreadable
        # manifest) grades apart from failed probes.
        return self._build_validation_report_result(
            project_dir,
            FlextInfraValidateFreshImport(
                repository_root=project_dir,
                runtime_root=ctx.runtime_root,
            ).build_report(repository_roots=(project_dir,)),
            ctx=ctx,
            started=started,
        )

    @override
    def check_files(
        self,
        files: Sequence[Path],
        project_dir: Path,
        ctx: m.Infra.GateContext,
    ) -> m.Infra.GateExecution:
        """Validate package imports when a source file selects this gate.

        The import contract belongs to the published package, not an individual
        source file. Run the same fresh-process proof as the project-level gate;
        there is no external checker command to receive file arguments.

        Returns:
            The package import proof, or no acceptance for nonexistent targets.

        """
        if files:
            selected = tuple(path for path in files if path.exists())
            if not selected:
                return self._skip_result(project_dir, ctx, time.monotonic())
            for path in selected:
                _ = path.relative_to(project_dir)
        return self.check(project_dir, ctx)


__all__: list[str] = ["FlextInfraGatesFreshImport"]
