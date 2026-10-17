"""Native Rope restructuring with lexical admission and import reuse.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import override

from rope.refactor.restructure import Restructure
from rope.refactor.wildcards import DefaultWildcard

from flext_infra import m, p, t
from flext_infra._utilities._rope_core_pymodule import (
    FlextInfraUtilitiesRopeCorePyModuleMixin,
)


class FlextInfraRopeRestructure(Restructure):
    """Keep native matching and writing while admitting each occurrence."""

    class _IdentityChoices:
        """Delegate every alternative to Rope's exact native identity matcher."""

        def __init__(self, project: p.Infra.RopeProject) -> None:
            self._wildcard: p.Infra.RopeWildcard[str] = DefaultWildcard(project)

        @staticmethod
        def get_name() -> str:
            return "identity_choices"

        def matches(self, suspect: p.AttributeProbe, arg: t.StrSequence) -> bool:
            return any(self._wildcard.matches(suspect, choice) for choice in arg)

    def __init__(
        self,
        project: p.Infra.RopeProject,
        request: m.Infra.RopeRestructureRequest,
    ) -> None:
        """Receive the current consumer's native match and import policies."""
        constraints = {
            name: value
            if isinstance(value, str)
            else ("identity_choices", tuple(value))
            for name, value in request.arguments.items()
        }
        super().__init__(
            project,
            request.pattern,
            request.goal,
            args=constraints,
            imports=list(
                request.imports.values()
                if isinstance(request.imports, Mapping)
                else request.imports
            ),
            wildcards={
                wildcard.get_name(): wildcard
                for wildcard in (
                    DefaultWildcard(project),
                    self._IdentityChoices(project),
                )
            },
        )
        self.match_filter = request.match_filter
        self.import_policy = request.imports
        self.matched_count = 0
        self.admitted_count = 0

    @override
    def _compute_changes(
        self,
        matches: t.SequenceOf[p.Infra.RopeContractMatch],
        pymodule: p.Infra.RopePyModule,
    ) -> t.Infra.RopeChangeComputer:
        """Admit occurrences before the native change computer writes source.

        Returns:
            The upstream source-preserving change computer.

        """
        selected = (
            list(matches)
            if self.match_filter is None
            else [match for match in matches if self.match_filter(pymodule, match)]
        )
        self.matched_count += len(matches)
        self.admitted_count += len(selected)
        computer: t.Infra.RopeChangeComputer = super()._compute_changes(
            selected, pymodule
        )
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

        Raises:
            TypeError: The native import manager did not emit source text.

        """
        selected = imports
        if isinstance(self.import_policy, Mapping):
            project: p.Infra.RopeProject = self.project
            names = (
                FlextInfraUtilitiesRopeCorePyModuleMixin.resolve_pymodule(
                    project, resource
                )
                .get_scope()
                .get_defined_names()
            )
            selected = tuple(
                declaration
                for binding, declaration in self.import_policy.items()
                if binding not in names
            )
        emitted = super()._add_imports(resource, source, list(selected))
        if not isinstance(emitted, str):
            message = "Rope import manager did not emit source text"
            raise TypeError(message)
        return emitted


__all__: list[str] = ["FlextInfraRopeRestructure"]
