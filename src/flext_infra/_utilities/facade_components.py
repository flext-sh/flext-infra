"""Facade component relocation: a family class read as a namespace moves to its letter.

Every facade letter, and every namespace class nested in it, composes family
component classes by MRO. A consumer that reads a member through the component
class (``FlextInfraConstantsPytest.X``) instead of the facade namespace
(``c.Infra.X``) bypasses the facade alphabet; the generated rules here rewrite
it, with the mapping derived from the runtime composition, never listed.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
import sys
from importlib import import_module
from importlib.metadata import packages_distributions
from pathlib import Path

from flext_infra import c, config, p, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodemodNativePackageUtilities,
    FlextInfraUtilitiesCodemodNativeUtilities,
    FlextInfraUtilitiesFacadeMembers,
    FlextInfraUtilitiesPyproject,
)


class FlextInfraUtilitiesFacadeComponents:
    """Derive component-to-namespace references and render their relocation."""

    @classmethod
    def facade_component_references(
        cls, project: Path
    ) -> t.MappingKV[t.StrPair, frozenset[str]]:
        """Map each facade namespace to the component references it composes.

        A facade letter, or a namespace class nested in it, composes family
        component classes by MRO (``class Infra(FlextInfraConstantsPytest)``).
        Each public member a lineage component declares yields the exact
        ``Component.member`` text under ``letter`` or ``letter.Namespace``
        when the namespace binds the identical object; a reference two
        namespaces would both claim is ambiguous and never relocates.

        Returns:
            Component references keyed by the composing root package and the
            ``letter[.Namespace]`` target.

        """
        package = FlextInfraUtilitiesPyproject.project_package_name(project)
        letters = sorted(set(config.Infra.tooling.facade_members.owners.values()))
        claims: dict[str, set[t.StrPair]] = {}
        for root in FlextInfraUtilitiesFacadeMembers.facade_member_lineage(
            package, letters
        ):
            for holder, target in cls._facade_namespace_holders(root, letters):
                for reference in cls._composed_references(root, letters, holder):
                    claims.setdefault(reference, set()).add((root, target))
        references: dict[t.StrPair, set[str]] = {}
        for reference, targets in claims.items():
            if len(targets) == 1:
                references.setdefault(next(iter(targets)), set()).add(reference)
        return {key: frozenset(found) for key, found in sorted(references.items())}

    @staticmethod
    def _facade_namespace_holders(
        root: str, letters: t.StrSequence
    ) -> t.SequenceOf[tuple[type, str]]:
        """List each facade letter of ``root`` and every namespace class it nests.

        Returns:
            Each holder class with its ``letter[.Namespace]`` reference text.

        """
        module = import_module(root)
        holders: list[tuple[type, str]] = []
        for letter in letters:
            facade = getattr(module, letter, None)
            if not isinstance(facade, type):
                continue
            holders.append((facade, letter))
            holders.extend(
                (nested, f"{letter}.{name}")
                for name, nested in vars(facade).items()
                if isinstance(nested, type)
                and nested.__qualname__ == f"{facade.__qualname__}.{name}"
            )
        return tuple(holders)

    @classmethod
    def _composed_references(
        cls, root: str, letters: t.StrSequence, holder: type
    ) -> t.StrSequence:
        """Reference each member a component base of ``holder`` composes into it.

        A base is a component when ``root`` declares it and it is not itself a
        facade letter of ``root``; its public member counts when the holder
        resolves the identical object by MRO (a lazy alias is never evaluated).

        Returns:
            The exact ``Component.member`` texts.

        """
        module = import_module(root)
        facades = {getattr(module, letter, None) for letter in letters}
        return tuple(
            f"{base.__name__}.{member}"
            for base in holder.__bases__
            if base.__module__.partition(".")[0] == root and base not in facades
            for member in dir(base)
            if not member.startswith("_")
            and FlextInfraUtilitiesFacadeMembers.declared_by_package(base, member, root)
            and member in dir(holder)
            and getattr(holder, member) is getattr(base, member)
        )

    @classmethod
    def codemod_facade_component_rules(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> t.MappingKV[str, t.JsonMapping]:
        """Render the one rule relocating every component reference to its namespace.

        ``Component.member`` becomes ``letter.Namespace.member`` where the
        component is bound by a module-level import, the letter is bound by a
        module-level import of the package that composes the namespace (the
        own package for own components, any lineage package for upstream
        ones), neither is shadowed, and the reference is never assigned
        through. One ``any`` branch per namespace carries its exact
        references and letter guard, and one rewriter per namespace emits the
        replacement; no document is rendered per package or letter. An own
        component inside its own letter's family never matches: that letter is
        never bound from the own package there (ENFORCE-051).

        Returns:
            The single native rule document keyed by its rule id, or nothing
            when the lineage composes no component.

        """
        del snapshot
        root = project.absolute()
        package = FlextInfraUtilitiesPyproject.project_package_name(root)
        references = cls.facade_component_references(root)
        if not references:
            return {}
        own = tuple(
            FlextInfraUtilitiesCodemodNativeUtilities.codemod_own_package_names(root)
        )
        members = FlextInfraUtilitiesFacadeMembers
        lineage = members.facade_member_lineage(
            package, sorted(set(config.Infra.tooling.facade_members.owners.values()))
        )
        sources = sorted({*lineage, *own})
        targets: dict[str, set[str]] = {}
        guards: dict[str, t.StrSequence] = {}
        for (composer, target), found in references.items():
            targets.setdefault(target, set()).update(found)
            guards[target] = own if composer == package else sources
        rule_id = (
            f"{c.Infra.FACADE_COMPONENT_RELOCATE_SHAPE}"
            f"{c.Infra.CODEMOD_GENERATED_ID_SEPARATOR}{package}"
        )
        return {
            rule_id: {
                "id": rule_id,
                "language": c.Infra.CODEMOD_PYTHON_LANGUAGE,
                "severity": "error",
                "rule": {
                    "all": [
                        {"kind": "attribute"},
                        {"pattern": "$REF"},
                        {"pattern": "$COMPONENT.$MEMBER"},
                        {
                            "has": {
                                "field": "object",
                                "all": [
                                    {"pattern": "$COMPONENT"},
                                    members.facade_letter_bound_rule(
                                        {"pattern": "$COMPONENT"}, sources
                                    ),
                                ],
                            }
                        },
                        {
                            "any": [
                                {
                                    "regex": members.exact_alternation(sorted(found)),
                                    **members.facade_letter_bound_rule(
                                        {
                                            "regex": "^"
                                            + re.escape(target.partition(".")[0])
                                            + "$"
                                        },
                                        guards[target],
                                    ),
                                }
                                for target, found in sorted(targets.items())
                            ]
                        },
                        {
                            "not": {
                                "inside": {
                                    "kind": "assignment",
                                    "field": "left",
                                    "stopBy": "end",
                                }
                            }
                        },
                    ]
                },
                "rewriters": [
                    {
                        "id": f"to-{index}",
                        "rule": {
                            "regex": members.exact_alternation(sorted(found)),
                            "pattern": "$OWNER.$NAME",
                        },
                        "fix": f"{target}.$NAME",
                    }
                    for index, (target, found) in enumerate(sorted(targets.items()))
                ],
                "transform": {
                    "RELOCATED": {
                        "rewrite": {
                            "source": "$REF",
                            "rewriters": [
                                f"to-{index}" for index in range(len(targets))
                            ],
                        }
                    }
                },
                "fix": "$RELOCATED",
                "message": (
                    "Family class `$COMPONENT` read as a namespace: read "
                    "`$RELOCATED` through the facade letter."
                ),
            }
        }

    @classmethod
    def facade_library_prefixes(cls, project: Path) -> t.StrTuple:
        """Name every third-party distribution the project's imports resolve to.

        Each top-level module the project imports that is neither the standard
        library, the own package nor a FLEXT facade package is mapped to the
        installed distributions that provide it (``git`` resolves to
        ``gitpython``, so the capability prefix ``git_`` is not a library
        prefix). Nothing is listed: the set is the dependency declaration as
        installed.

        Returns:
            The normalized distribution names, sorted.

        """
        root = project.absolute()
        native = FlextInfraUtilitiesCodemodNativePackageUtilities
        known = {
            *sys.stdlib_module_names,
            *native.codemod_facade_packages(root),
            *FlextInfraUtilitiesCodemodNativeUtilities.codemod_own_package_names(root),
        }
        providers = packages_distributions()
        return tuple(
            sorted({
                distribution.lower().replace("-", "_").replace(".", "_")
                for module in native.codemod_imported_top_modules(root)
                if module not in known and not module.startswith("_")
                for distribution in providers.get(module, ())
            })
        )

    @classmethod
    def codemod_library_member_name_rules(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> t.MappingKV[str, t.JsonMapping]:
        """Render the one rule banning a library-prefixed facade member.

        A facade export is prefixed by its capability (``git_``,
        ``refactor_``, ``workspace_``), never by the third-party library that
        implements it (``rope_project``, ``RopeProject``, ``pytest_runner``):
        only the c/t/p/m/u families know the library (ADR-028; operator
        ruling 2026-10-25). The prefixes are the installed distributions of
        the project's imports (``facade_library_prefixes``). Detection-only:
        the rename map is produced from this scan and applied by the mass
        rename tooling with a deprecated-signature window.

        Returns:
            The single rule document keyed by its rule id, or nothing when the
            project imports no third-party library.

        """
        del snapshot
        root = project.absolute()
        prefixes = cls.facade_library_prefixes(root)
        if not prefixes:
            return {}
        snake = "|".join(re.escape(prefix) for prefix in prefixes)
        camel = "|".join(
            re.escape(prefix.replace("_", " ").title().replace(" ", ""))
            for prefix in prefixes
        )
        letters = "|".join(
            re.escape(letter)
            for letter in sorted(
                set(config.Infra.tooling.facade_members.owners.values())
            )
        )
        package = FlextInfraUtilitiesPyproject.project_package_name(root)
        rule_id = (
            f"{c.Infra.FACADE_LIBRARY_MEMBER_SHAPE}"
            f"{c.Infra.CODEMOD_GENERATED_ID_SEPARATOR}{package}"
        )
        return {
            rule_id: {
                "id": rule_id,
                "language": c.Infra.CODEMOD_PYTHON_LANGUAGE,
                "severity": "error",
                "rule": {
                    "kind": "attribute",
                    "regex": rf"^(?:{letters})\.",
                    "has": {
                        "field": "attribute",
                        "regex": rf"^(?:(?:{snake})(?:_|$)|(?:{camel})(?:[A-Z]|$))",
                    },
                },
                "message": (
                    "Facade member prefixed by a library name: export it under "
                    "its capability prefix instead."
                ),
            }
        }


__all__: list[str] = ["FlextInfraUtilitiesFacadeComponents"]
