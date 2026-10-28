"""Rope DSL interpreter — one rule applied through the single rope index.

Interprets ``m.Infra`` rope DSL documents (engine-map section 8) against the
one rope project of the repository invocation, using rope's native
refactorings only (ADR-028 Decision 17 amendment 2026-10-28): ImportOrganizer
for import organization; the transform verbs operate on the indexed PyModules
through rope's public module surface. The interpreter never re-parses, never
opens a second project and never imports member code.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT.
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

from fnmatch import fnmatch

from rope.refactor.importutils import ImportOrganizer

from flext_core import r
from flext_infra import m, p, t
from flext_infra._utilities._rope.rope_runtime_types import (
    FlextInfraUtilitiesTypesRopeRuntime,
)


class FlextInfraUtilitiesRopeDsl:
    """Apply one rope DSL rule through the repository's single rope index."""

    @classmethod
    def apply_rule(
        cls,
        project: p.Infra.RopeProject,
        rule: m.Infra.RopeDslRule,
    ) -> r[t.VariadicTuple[tuple[str, str]]]:
        """Run one declared rule over the indexed repository sources.

        Returns:
            The affected resource-and-outcome pairs, or the first typed
            failure (unknown capability, matches beyond a cap, native
            application error).

        """
        resources = cls._selected_resources(project, rule.selector)
        if not resources:
            return r[t.VariadicTuple[tuple[str, str]]].ok(())
        if rule.constraint.max_occurrences and len(resources) > (
            rule.constraint.max_occurrences
        ):
            return r[t.VariadicTuple[tuple[str, str]]].fail(
                f"rope rule {rule.id}: {len(resources)} matches exceed cap "
                f"{rule.constraint.max_occurrences}",
            )
        match rule.operation:
            case m.Infra.RopeDslOperation.ORGANIZE_IMPORTS:
                return cls._organize_imports(project, resources)
            case m.Infra.RopeDslOperation.TRANSFORM:
                return cls._transform(project, rule, resources)
            case _:
                return r[t.VariadicTuple[tuple[str, str]]].fail(
                    f"rope rule {rule.id}: operation {rule.operation.value} "
                    "pending vocabulary wiring (engine-map section 8)",
                )

    @classmethod
    def _selected_resources(
        cls,
        project: p.Infra.RopeProject,
        selector: m.Infra.RopeDslSelector,
    ) -> t.VariadicTuple[t.Infra.RopeResource]:
        """Return indexed Python resources a selector admits."""
        admitted: list[t.Infra.RopeResource] = []
        for resource in project.get_python_files():
            stem = resource.path.rpartition(".")[0].replace("/", ".")
            if fnmatch(stem, selector.module_pattern):
                admitted.append(resource)
        return tuple(admitted)

    @classmethod
    def _organize_imports(
        cls,
        project: p.Infra.RopeProject,
        resources: Sequence[t.Infra.RopeResource],
    ) -> r[t.VariadicTuple[tuple[str, str]]]:
        """Apply rope's native ImportOrganizer to selected resources.

        Returns:
            The affected resource-and-outcome pairs.

        """
        effects: list[tuple[str, str]] = []
        organizer = ImportOrganizer(project)
        for resource in resources:
            changes = organizer.organize_imports(resource)
            if changes:
                changes.do()
                effects.append((resource.path, "organize-imports"))
        return r[t.VariadicTuple[tuple[str, str]]].ok(tuple(effects))

    @classmethod
    def _transform(
        cls,
        project: p.Infra.RopeProject,
        rule: m.Infra.RopeDslRule,
        resources: Sequence[t.Infra.RopeResource],
    ) -> r[t.VariadicTuple[tuple[str, str]]]:
        """Apply one declared transform verb through rope module surface.

        Returns:
            The affected resource-and-outcome pairs, or the typed failure
            for a verb outside the closed vocabulary.

        """
        verb = rule.rewrite.verb
        if verb is not m.Infra.RopeDslTransformVerb.ELECT_BARE_LETTER:
            return r[t.VariadicTuple[tuple[str, str]]].fail(
                f"rope rule {rule.id}: transform verb "
                f"{verb.value if verb else '<none>'} not in vocabulary",
            )
        letters = frozenset(rule.constraint.letters)
        effects: list[tuple[str, str]] = [
            (resource.path, "elect-bare-letter")
            for resource in resources
            if FlextInfraUtilitiesRopeDslImportTools.elect_bare_letter(
                project,
                resource,
                letters=letters,
            )
        ]
        return r[t.VariadicTuple[tuple[str, str]]].ok(tuple(effects))


class FlextInfraUtilitiesRopeDslImportTools:
    """Rope-native import statement tools behind the transform verbs.

    Every operation reads the indexed PyModule through rope's public module
    surface (``get_pymodule`` — the one parse the index owns); statements are
    identified from that module's own source so the project's change tracking
    stays authoritative.

    """

    @classmethod
    def elect_bare_letter(
        cls,
        project: p.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        *,
        letters: frozenset[str],
    ) -> bool:
        """Rewrite ``from X import l as a`` to bare ``from X import l``.

        An aliased single-letter facade import whose alias occurs exactly
        once in the module collapses to the bare letter (ADR-028 Decision 10
        spelling election); the single alias use rebinding follows the
        letter.

        Returns:
            Whether the resource changed.

        """
        module = project.get_pymodule(resource)
        source = module.source_code
        changed = False
        for name in sorted(letters):
            marker = f"import {name} as "
            start = 0
            while (at := source.find(marker, start)) != -1:
                line_end = source.find("\n", at)
                tail = source[at + len(marker) : line_end if line_end != -1 else None]
                alias = tail.strip().rstrip(",").partition("(")[0].strip()
                if alias.isidentifier() and alias != name and source.count(alias) == 1:
                    aliased = f"import {name} as {alias}"
                    bare = f"import {name}"
                    if aliased in source:
                        source = source.replace(aliased, bare)
                        source = source.replace(alias, name)
                        changed = True
                start = at + len(marker)
        if changed:
            FlextInfraUtilitiesTypesRopeRuntime.require_file_resource(
                resource, resource.path
            ).write(source)
        return changed


__all__: list[str] = [
    "FlextInfraUtilitiesRopeDsl",
    "FlextInfraUtilitiesRopeDslImportTools",
]
