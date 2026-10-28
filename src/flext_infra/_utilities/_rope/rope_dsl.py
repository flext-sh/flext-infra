"""Rope DSL interpreter — one rule applied through the single rope index.

Interprets ``m.Infra`` rope DSL documents (engine-map section 8) against the
one rope project of the repository invocation, using rope's native
refactorings only (ADR-028 Decision 17 amendment 2026-10-28): ImportOrganizer,
rename, move and restructure; the transform verbs operate on the indexed
PyModules through rope's public import tools. The interpreter never re-parses,
never opens a second project and never imports member code.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from fnmatch import fnmatch
from typing import TYPE_CHECKING

from flext_infra import m, p, r, t, u

if TYPE_CHECKING:
    from rope.refactor import ImportOrganizer


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
            failure (unknown capability, no matches beyond a cap, native
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
        for resource in u.Infra.rope_python_resources(project):
            module_name = u.Infra.rope_module_name_of(project, resource)
            if module_name and fnmatch(module_name, selector.module_pattern):
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
        organizer_cls = u.Infra.rope_import_organizer_cls()
        effects: list[tuple[str, str]] = []
        for resource in resources:
            organizer: ImportOrganizer = organizer_cls(project, resource)
            changes = organizer.get_changes()
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
        """Apply one declared transform verb through rope import tools.

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
        letters = set(rule.constraint.letters)
        effects: list[tuple[str, str]] = []
        finder = u.Infra.rope_import_tools()
        for resource in resources:
            rewritten = finder.elect_bare_letter(
                project,
                resource,
                letters=letters,
            )
            if rewritten:
                effects.append((resource.path, "elect-bare-letter"))
        return r[t.VariadicTuple[tuple[str, str]]].ok(tuple(effects))


class FlextInfraUtilitiesRopeDslImportTools:
    """Rope-native import statement tools behind the transform verbs.

    Every operation reads the indexed PyModule through rope's public
    ``importutils`` surface; statements are edited through rope's module
    rewrite API so the project's change tracking stays authoritative.

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

        Aliased single-letter facade imports whose alias shadows nothing else
        in the module collapse to the bare letter, and every alias use is
        rebound to the letter (ADR-028 Decision 10 spelling election).

        Returns:
            Whether the resource changed.

        """
        module = project.get_pymodule(resource)
        imports = u.Infra.rope_module_imports(project, module)
        changed = False
        for statement in imports:
            imported = u.Infra.rope_import_context(module, statement)
            name, alias = imported.name, imported.as_name
            if not alias or (name != alias and name not in letters):
                continue
            if name not in letters:
                continue
            module_source = u.Infra.rope_module_source(module)
            if module_source.count(alias) > 1:
                continue
            rewritten = module_source.replace(
                f"import {name} as {alias}",
                f"import {name}",
            ).replace(alias, name)
            u.Infra.rope_write_resource(resource, rewritten)
            changed = True
        return changed


__all__: list[str] = [
    "FlextInfraUtilitiesRopeDsl",
    "FlextInfraUtilitiesRopeDslImportTools",
]
