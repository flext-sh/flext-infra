"""Declared initial generation and bounded Make dispatcher recovery.

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

from pathlib import Path
from typing import Annotated, override

from flext_infra import c, m, p, r, u
from flext_infra._conform import FlextInfraConformWiring
from flext_infra.codegen import FlextInfraCodegenConform, FlextInfraCodegenExecution
from flext_infra.workspace import FlextInfraWorkspaceDetector


class FlextInfraCodegenMakeBootstrap(
    FlextInfraConformWiring,
    FlextInfraCodegenExecution[bool],
):
    """Compose the existing Make planner, publisher and receipt verifier."""

    model_config = m.ConfigDict(use_enum_values=False)
    kind: Annotated[
        c.Infra.ProjectKind | None,
        m.Field(
            description=(
                "Explicit governance kind belonging only to the requested target"
            ),
        ),
    ] = None

    def _admit_new_target(self, requested: Path) -> p.Result[bool]:
        """Admit a new target's own declaration against the requested kind.

        Returns:
            Success, or the admission failure or kind conflict.

        """
        admitted = FlextInfraWorkspaceDetector.load_workspace_spec(requested)
        if admitted.failure:
            return r[bool].from_failure(admitted)
        if self.kind is not None and self.kind is not admitted.value.repository.kind:
            return r[bool].fail(
                "bootstrap kind conflicts with the new target's own declaration: "
                f"{requested}",
            )
        return r[bool].ok(value=True)

    def _conform_existing_target(
        self, requested: Path
    ) -> p.Result[p.Infra.CodegenResult]:
        """Conform the Makefile surface of an existing target.

        Returns:
            The native conformance result for the Makefile surface.

        """
        return FlextInfraCodegenConform.execute_request(
            m.Infra.CodegenConformRequest(
                root=requested,
                what=c.Infra.CodegenConformSurface.MAKEFILE,
                mode=(
                    c.Infra.CodegenConformMode.CHECK
                    if self.effective_dry_run
                    else c.Infra.CodegenConformMode.APPLY
                ),
                declaration_kind=self.kind,
            ),
            execution_context=None,
        )

    @override
    def execute(self) -> p.Result[bool]:
        """Publish an admitted new tree or this existing target's Make bootstrap.

        Returns:
            A completed native publication receipt or the original failure.

        """
        requested = self.repository_root.expanduser().absolute()
        identity = u.Infra.exact_worktree_root(requested)
        if identity.failure:
            return r[bool].from_failure(identity)
        metadata = requested / c.PYPROJECT_FILENAME
        new_project = not metadata.exists() and not metadata.is_symlink()
        if new_project:
            admitted = self._admit_new_target(requested)
            if admitted.failure:
                return admitted
            request = m.Infra.CodegenGenerateRequest(root=requested)
            if self.effective_dry_run:
                return (
                    FlextInfraCodegenConform.Generate
                    .from_request(request, execution_context=self)
                    .flat_map(lambda executor: executor.check_managed(request))
                    .map(lambda _: True)
                )
            conformed = FlextInfraCodegenConform.Generate.execute_request(
                request, execution_context=self
            )
        else:
            conformed = self._conform_existing_target(requested)
            if self.effective_dry_run:
                return conformed.map(lambda _: True)
        return conformed.map(lambda _: True)


__all__: list[str] = ["FlextInfraCodegenMakeBootstrap"]
