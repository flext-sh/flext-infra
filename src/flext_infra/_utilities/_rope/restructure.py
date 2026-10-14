"""Native Rope restructuring with lexical admission and import reuse.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Callable
from typing import override

from rope.refactor.restructure import Restructure

from flext_infra import p, t


class FlextInfraRopeRestructure(Restructure):
    """Keep native matching and writing while admitting each occurrence."""

    def __init__(
        self,
        project: p.Infra.RopeProject,
        pattern: str,
        goal: str,
        *,
        args: t.MappingKV[str, str],
        imports: t.StrSequence,
        match_filter: Callable[[p.Infra.RopePyModule, p.Infra.RopeContractMatch], bool]
        | None = None,
        import_bindings: t.MappingKV[str, str] | None = None,
    ) -> None:
        """Receive the current consumer's native match and import policies."""
        super().__init__(project, pattern, goal, args=dict(args), imports=list(imports))
        self.match_filter = match_filter
        self.import_bindings = import_bindings
        self.matched_count = 0
        self.admitted_count = 0

    @override
    def _compute_changes(
        self,
        matches: t.SequenceOf[p.Infra.RopeContractMatch],
        pymodule: p.Infra.RopePyModule,
    ) -> p.Infra.RopeChangeComputer:
        """Admit occurrences before the native change computer writes source.

        Returns:
            The upstream source-preserving change computer.

        Raises:
            TypeError: When Rope does not satisfy its change-computer contract.
        """
        selected = (
            list(matches)
            if self.match_filter is None
            else [match for match in matches if self.match_filter(pymodule, match)]
        )
        self.matched_count += len(matches)
        self.admitted_count += len(selected)
        computer = super()._compute_changes(selected, pymodule)
        if not isinstance(computer, p.Infra.RopeChangeComputer):
            message = "Rope returned an invalid source change computer"
            raise TypeError(message)
        return computer

    @override
    def _add_imports(
        self,
        resource: p.Infra.RopeResource,
        source: str,
        imports: t.StrSequence,
    ) -> str:
        """Reuse existing bindings instead of replacing a richer public facade.

        Returns:
            Source emitted by the native import manager.
        """
        selected = imports
        if self.import_bindings is not None:
            names = self.project.get_pymodule(resource).get_scope().get_defined_names()
            selected = tuple(
                declaration
                for binding, declaration in self.import_bindings.items()
                if binding not in names
            )
        return super()._add_imports(resource, source, list(selected))


__all__: list[str] = ["FlextInfraRopeRestructure"]
