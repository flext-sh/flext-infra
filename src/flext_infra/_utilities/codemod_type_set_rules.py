"""Generated native rules that rewire inline type sets to their constants.

Outside the constants family no module spells a runtime type set (ADR-028).
Each tuple-of-classes constant the project's constants facade exposes is
elected by value, with no naming filter and no list. The renderer emits one
native rule per constant. The rule matches that exact set in any operand
order, as a tuple or as a ``|`` union, structurally and linearly in the set
size, and its fix reads the constant.

A member is matched by every spelling the facade law admits outside the
constants family: a builtin by its bare name, a stdlib class as its top-level
module exposes it (``ast.Name``), and any class through each constants-facade
alias that binds it (``c.Infra.Cst.ClassDef``). A set with a member that has no
admitted spelling produces no rule. Two constants holding the same set are an
SSOT defect, and rendering fails with both paths.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import builtins
import inspect
import sys
from importlib import import_module
from pathlib import Path

from flext_infra import c, t
from flext_infra._utilities import FlextInfraUtilitiesPyproject


class FlextInfraUtilitiesCodemodTypeSetRules:
    """Render one inline-type-set rewire rule per declared type-set constant."""

    @classmethod
    def codemod_type_set_rules(cls, project: Path) -> t.MappingKV[str, t.JsonMapping]:
        """Render the type-set rules of the project's constants facade.

        Returns:
            One native rule document per type-set constant, keyed by rule id.

        Raises:
            ValueError: If two constants hold the same type set.

        """
        package = FlextInfraUtilitiesPyproject.project_package_name(project)
        facade = getattr(import_module(package), c.Infra.FacadeFamily.C, None)
        if not inspect.isclass(facade):
            return {}
        root = (c.Infra.FacadeFamily.C,)
        aliases = cls._facade_aliases(facade, root)
        owners: dict[frozenset[type], str] = {}
        documents: dict[str, t.JsonMapping] = {}
        for path, classes in cls._type_set_constants(facade, root):
            reference = ".".join(path)
            members = frozenset(classes)
            if members in owners:
                msg = f"type set declared twice: {owners[members]} and {reference}"
                raise ValueError(msg)
            owners[members] = reference
            spellings = tuple(cls._spellings(item, aliases) for item in classes)
            if not all(spellings):
                continue
            rule_id = c.Infra.CODEMOD_GENERATED_ID_SEPARATOR.join((
                c.Infra.CODEMOD_TYPE_SET_SHAPE,
                "-".join(part.lower().replace("_", "-") for part in path[1:]),
            ))
            documents[rule_id] = cls._type_set_document(rule_id, reference, spellings)
        return documents

    @staticmethod
    def _type_set_document(
        rule_id: str, reference: str, spellings: t.SequenceOf[t.StrSequence]
    ) -> t.JsonMapping:
        """Build the rule matching one exact type set in either spelling.

        Returns:
            The native rule document.

        """
        members = [
            {"any": [{"pattern": spelling} for spelling in options]}
            for options in spellings
        ]
        present = [{"has": member} for member in members]
        present_anywhere = [{"has": {"stopBy": "end", **member}} for member in members]
        operand = {"any": [{"kind": "attribute"}, {"kind": "identifier"}]}
        return {
            "id": rule_id,
            "language": "python",
            "severity": "error",
            "files": ["**/*.py"],
            "ignores": ["**/constants.py", "**/_constants/**"],
            "rule": {"pattern": "isinstance($VALUE, $SET)"},
            "constraints": {
                "SET": {
                    "any": [
                        {
                            "all": [
                                {"kind": "tuple"},
                                *present,
                                {
                                    "not": {
                                        "has": {
                                            **operand,
                                            "not": {"any": members},
                                        }
                                    }
                                },
                            ]
                        },
                        {
                            "all": [
                                {"kind": "binary_operator"},
                                *present_anywhere,
                                {
                                    "not": {
                                        "has": {
                                            "stopBy": "end",
                                            **operand,
                                            "inside": {"kind": "binary_operator"},
                                            "not": {"any": members},
                                        }
                                    }
                                },
                            ]
                        },
                    ]
                }
            },
            "fix": f"isinstance($VALUE, {reference})",
            "message": f"Inline type set: read the constant {reference}.",
        }

    @classmethod
    def _type_set_constants(
        cls, owner: type, path: t.StrSequence
    ) -> t.SequenceOf[tuple[t.StrSequence, t.SequenceOf[type]]]:
        """Collect every tuple-of-classes constant of ``owner`` and its namespaces.

        Returns:
            Each constant's attribute path with its classes, first binding wins.

        """
        found: dict[tuple[str, ...], tuple[type, ...]] = {}
        for klass in owner.__mro__:
            for name, value in vars(klass).items():
                if name.startswith("_"):
                    continue
                key = (*path, name)
                if (
                    isinstance(value, tuple)
                    and len(value) > 1
                    and all(inspect.isclass(item) for item in value)
                ):
                    found.setdefault(key, value)
                elif cls._namespace_of(klass, value):
                    for nested, classes in cls._type_set_constants(value, key):
                        found.setdefault(tuple(nested), tuple(classes))
        return tuple(found.items())

    @classmethod
    def _facade_aliases(
        cls, owner: type, path: t.StrSequence
    ) -> t.MappingKV[type, t.StrSequence]:
        """Map each class the facade binds as an alias to its attribute paths.

        Returns:
            Class to every facade path that binds it, first binding per path.

        """
        found: dict[type, list[str]] = {}
        seen: set[tuple[str, ...]] = set()
        for klass in owner.__mro__:
            for name, value in vars(klass).items():
                key = (*path, name)
                if name.startswith("_") or key in seen or not inspect.isclass(value):
                    continue
                seen.add(key)
                if cls._namespace_of(klass, value):
                    for item, nested in cls._facade_aliases(value, key).items():
                        found.setdefault(item, []).extend(nested)
                else:
                    found.setdefault(value, []).append(".".join(key))
        return {item: tuple(paths) for item, paths in found.items()}

    @staticmethod
    def _namespace_of(klass: type, value: object) -> bool:
        """Tell whether ``value`` is a namespace class nested in ``klass``.

        Returns:
            ``True`` for a class declared inside ``klass``'s body.

        """
        return inspect.isclass(value) and value.__qualname__.startswith(
            f"{klass.__qualname__}."
        )

    @staticmethod
    def _spellings(
        item: type, aliases: t.MappingKV[type, t.StrSequence]
    ) -> t.StrSequence:
        """Every source spelling of ``item`` admitted outside the constants family.

        Returns:
            The bare builtin name, the ``<stdlib module>.<name>`` spelling when
            that stdlib module binds the class, and each constants-facade alias
            path; empty when none applies.

        """
        options: list[str] = []
        if getattr(builtins, item.__name__, None) is item:
            options.append(item.__name__)
        top = item.__module__.partition(".")[0]
        if (
            top in sys.stdlib_module_names
            and getattr(import_module(top), item.__name__, None) is item
        ):
            options.append(f"{top}.{item.__name__}")
        options.extend(aliases.get(item, ()))
        return tuple(options)


__all__: list[str] = ["FlextInfraUtilitiesCodemodTypeSetRules"]
