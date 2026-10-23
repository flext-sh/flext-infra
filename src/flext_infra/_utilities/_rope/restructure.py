"""Native Rope restructuring with lexical admission and import reuse.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import override

from rope.base.project import Project
from rope.refactor.restructure import Restructure
from rope.refactor.wildcards import DefaultWildcard

from flext_infra import m, p, t
from flext_infra._utilities import FlextInfraUtilitiesRopeRuntime


class FlextInfraRopeRestructure(Restructure):
    """Keep native matching and writing while admitting each occurrence."""

    project: p.Infra.RopeProject

    class _IdentityChoices:
        """Delegate every alternative to Rope's exact native identity matcher."""

        def __init__(self, wildcard: p.Infra.RopeWildcard[str]) -> None:
            self._wildcard = wildcard

        @staticmethod
        def get_name() -> str:
            return "identity_choices"

        def matches(self, suspect: p.AttributeProbe, arg: t.StrSequence) -> bool:
            return any(self._wildcard.matches(suspect, choice) for choice in arg)

    def __init__(
        self,
        project: p.AttributeProbe,
        request: m.Infra.RopeRestructureRequest,
    ) -> None:
        """Receive the current consumer's native match and import policies.

        Raises:
            TypeError: The project is not a native Rope project.

        """
        if not isinstance(project, Project):
            message = "Rope restructuring requires a native project"
            raise TypeError(message)
        default: p.Infra.RopeWildcard[str] = DefaultWildcard(project)

        super().__init__(
            project,
            request.pattern,
            request.goal,
            {
                name: value
                if isinstance(value, str)
                else ("identity_choices", tuple(value))
                for name, value in request.arguments.items()
            },
            list(
                request.imports.values()
                if isinstance(request.imports, Mapping)
                else request.imports
            ),
            {
                wildcard.get_name(): wildcard
                for wildcard in (
                    default,
                    self._IdentityChoices(default),
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
        matches: t.SequenceOf[t.Infra.RopeNativeMatch],
        pymodule: t.Infra.RopeNativeSourceModule,
    ) -> t.Infra.RopeNativeChangeComputer:
        """Admit occurrences before the native change computer writes source.

        Returns:
            The upstream source-preserving change computer.

        Raises:
            TypeError: The module is not a native source module.

        """
        if not FlextInfraUtilitiesRopeRuntime.source_module(pymodule):
            message = "Rope restructuring requires a native source module"
            raise TypeError(message)
        selected = [
            match
            for match in matches
            if self.match_filter is None or self.match_filter(pymodule, match)
        ]
        self.matched_count += len(matches)
        self.admitted_count += len(selected)

        return super()._compute_changes(selected, pymodule)

    @override
    def _add_imports(
        self,
        resource: t.Infra.RopeNativeResource,
        source: str,
        imports: t.StrSequence,
    ) -> str:
        """Reuse existing bindings instead of replacing a richer public facade.

        Returns:
            Source emitted by the native import manager.

        """
        selected = imports
        if isinstance(self.import_policy, Mapping):
            names = (
                FlextInfraUtilitiesRopeRuntime
                .require_parsed_module(self.project.get_pymodule(resource))
                .get_scope()
                .get_defined_names()
            )
            selected = tuple(
                declaration
                for binding, declaration in self.import_policy.items()
                if binding not in names
            )

        return super()._add_imports(resource, source, selected)


__all__: list[str] = ["FlextInfraRopeRestructure"]
