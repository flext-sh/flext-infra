"""Generated native rule that rewires inline type sets to their constants.

Outside the constants family no module spells a runtime type set (ADR-028).
Each tuple-of-classes constant the project's constants facade exposes is
elected by value, with no naming filter and no list. The renderer emits ONE
native rule: ``isinstance($VALUE, $SET)`` constrained to the declared sets,
with one rewriter per constant that replaces ``$SET`` by the constant. Each set
is matched exactly, in any operand order, as a tuple or as a ``|`` union,
structurally and linearly in the set size.

A member is matched by every spelling the facade law admits outside the
constants family: a builtin by its bare name, a stdlib class as its top-level
module exposes it (``ast.Name``), and any class through each constants-facade
alias that binds it (``c.Infra.Cst.ClassDef``). A set with a member that has no
admitted spelling is not rewired. Two constants holding the same set are an
SSOT defect, and rendering fails with both paths; a constant annotated with the
stdlib ``warnings.deprecated`` compat marker is the intended second owner during
its rewiring window and is not elected.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import builtins
import inspect
import re
import sys
import warnings
from importlib import import_module
from pathlib import Path

from flext_infra import c, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodemodNativePackageUtilities,
    FlextInfraUtilitiesPyproject,
)


class FlextInfraUtilitiesCodemodTypeSetRules:
    """Render the inline-type-set rewire rule of the constants facade."""

    @classmethod
    def codemod_type_set_rules(cls, project: Path) -> t.MappingKV[str, t.JsonMapping]:
        """Render the type-set rule of the project's constants facade.

        Returns:
            The single native rule document keyed by its rule id, or nothing
            when the facade declares no rewirable type set.

        Raises:
            ValueError: If two unmarked constants hold the same type set.

        """
        package = FlextInfraUtilitiesPyproject.project_package_name(project)
        facade = getattr(import_module(package), c.Infra.FacadeFamily.C, None)
        if not inspect.isclass(facade):
            return {}
        root = (c.Infra.FacadeFamily.C,)
        aliases = cls._facade_aliases(facade, root)
        owners: dict[frozenset[type], str] = {}
        sets: list[tuple[str, t.JsonMapping]] = []
        for path, classes in cls._type_set_constants(facade, root):
            reference = ".".join(path)
            members = frozenset(classes)
            if members in owners:
                msg = f"type set declared twice: {owners[members]} and {reference}"
                raise ValueError(msg)
            owners[members] = reference
            spellings = tuple(cls._spellings(item, aliases) for item in classes)
            if all(spellings):
                sets.append((reference, cls._type_set_rule(spellings)))
        if not sets:
            return {}
        rule_id = c.Infra.CODEMOD_TYPE_SET_SHAPE
        return {rule_id: cls._type_set_document(rule_id, sets)}

    @staticmethod
    def _type_set_document(
        rule_id: str, sets: t.SequenceOf[tuple[str, t.JsonMapping]]
    ) -> t.JsonMapping:
        """Build the one rule whose rewriters replace each declared set.

        Returns:
            The native rule document.

        """
        names = [f"set-{index}" for index in range(len(sets))]
        return {
            "id": rule_id,
            "language": "python",
            "severity": "error",
            "files": ["**/*.py"],
            "ignores": ["**/constants.py", "**/_constants/**"],
            "utils": {
                name: rule for name, (_reference, rule) in zip(names, sets, strict=True)
            },
            "rule": {"pattern": "isinstance($VALUE, $SET)"},
            "constraints": {"SET": {"any": [{"matches": name} for name in names]}},
            "rewriters": [
                {"id": f"to-{name}", "rule": {"matches": name}, "fix": reference}
                for name, (reference, _rule) in zip(names, sets, strict=True)
            ],
            "transform": {
                "CONSTANT": {
                    "rewrite": {
                        "source": "$SET",
                        "rewriters": [f"to-{name}" for name in names],
                    }
                }
            },
            "fix": "isinstance($VALUE, $CONSTANT)",
            "message": "Inline type set: read the constant that declares it.",
        }

    @staticmethod
    def _type_set_rule(spellings: t.SequenceOf[t.StrSequence]) -> t.JsonMapping:
        """Match one exact type set as a tuple or a ``|`` union, any order.

        Returns:
            The native rule of one set.

        """
        members = [
            {"any": [{"pattern": spelling} for spelling in options]}
            for options in spellings
        ]
        operand = {"any": [{"kind": "attribute"}, {"kind": "identifier"}]}
        return {
            "any": [
                {
                    "all": [
                        {"kind": "tuple"},
                        *({"has": member} for member in members),
                        {"not": {"has": {**operand, "not": {"any": members}}}},
                    ]
                },
                {
                    "all": [
                        {"kind": "binary_operator"},
                        *({"has": {"stopBy": "end", **member}} for member in members),
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

    @classmethod
    def _type_set_constants(
        cls, owner: type, path: t.StrSequence
    ) -> t.SequenceOf[tuple[t.StrSequence, t.SequenceOf[type]]]:
        """Collect every unmarked tuple-of-classes constant of ``owner``.

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
                    if cls.codemod_compat_marker(klass, name) is None:
                        found.setdefault(key, value)
                elif cls._namespace_of(klass, value):
                    for nested, classes in cls._type_set_constants(value, key):
                        found.setdefault(tuple(nested), tuple(classes))
        return tuple(found.items())

    @classmethod
    def codemod_compat_rules(cls, project: Path) -> t.MappingKV[str, t.JsonMapping]:
        """Render the rule that fails and rewires reads of compat-marked constants.

        Every attribute of the constants facade whose annotation carries the
        stdlib compat marker contributes one rewriter from its facade path to
        the new path its marker names. The declaration is never matched, only
        reads are, so the marked alias survives until its last reader is gone.

        Returns:
            The single native rule document keyed by its rule id, or nothing
            when the facade marks no constant.

        Raises:
            ValueError: If a marker message breaks the compat grammar or names
                an old path other than the attribute's own facade path.

        """
        package = FlextInfraUtilitiesPyproject.project_package_name(project)
        facade = getattr(import_module(package), c.Infra.FacadeFamily.C, None)
        if not inspect.isclass(facade):
            return {}
        grammar = re.compile(c.Infra.CODEMOD_COMPAT_MESSAGE_PATTERN)
        moves: dict[str, str] = {}
        for path, message in cls._compat_markers(facade, (c.Infra.FacadeFamily.C,)):
            old = ".".join(path)
            parsed = grammar.match(message)
            if parsed is None or parsed["old"] != old:
                msg = f"compat marker of {old} breaks its grammar: {message!r}"
                raise ValueError(msg)
            moves[old] = parsed["new"]
        if not moves:
            return {}
        rule_id = c.Infra.CODEMOD_COMPAT_READ_SHAPE
        names = {old: f"to-{index}" for index, old in enumerate(sorted(moves))}
        exact = (
            FlextInfraUtilitiesCodemodNativePackageUtilities.codemod_exact_names_rule
        )
        return {
            rule_id: {
                "id": rule_id,
                "language": "python",
                "severity": "error",
                "files": ["**/*.py"],
                "rule": {
                    "kind": "attribute",
                    "pattern": "$OLD",
                    "not": {"inside": {"kind": "attribute", "field": "object"}},
                },
                "constraints": {
                    "OLD": exact(tuple(moves))
                },
                "rewriters": [
                    {
                        "id": names[old],
                        "rule": exact((old,)),
                        "fix": new,
                    }
                    for old, new in sorted(moves.items())
                ],
                "transform": {
                    "NEW": {
                        "rewrite": {
                            "source": "$OLD",
                            "rewriters": [names[old] for old in sorted(moves)],
                        }
                    }
                },
                "fix": "$NEW",
                "message": (
                    "Read of a compat-marked constant: read the new owner its "
                    "marker names."
                ),
            }
        }

    @classmethod
    def _compat_markers(
        cls, owner: type, path: t.StrSequence
    ) -> t.SequenceOf[tuple[t.StrSequence, str]]:
        """Collect every compat-marked attribute of ``owner`` and its namespaces.

        Returns:
            Each marked attribute's facade path with its marker message.

        """
        found: dict[tuple[str, ...], str] = {}
        for klass in owner.__mro__:
            for name, value in vars(klass).items():
                if name.startswith("_"):
                    continue
                key = (*path, name)
                message = cls.codemod_compat_marker(klass, name)
                if message is not None:
                    found.setdefault(key, message)
                elif cls._namespace_of(klass, value):
                    for nested, nested_message in cls._compat_markers(value, key):
                        found.setdefault(tuple(nested), nested_message)
        return tuple(found.items())

    @staticmethod
    def codemod_compat_marker(klass: type, name: str) -> str | None:
        """Return the compat message a class attribute's annotation carries.

        The marker is the stdlib PEP 702 decorator used as ``Annotated``
        metadata (``Annotated[ClassVar[...], warnings.deprecated("compat: ...")]``),
        read from the attribute's own annotation source.

        Returns:
            The marker message, or ``None`` for an unmarked attribute.

        """
        raw = vars(klass).get("__annotations__", {}).get(name)
        if not isinstance(raw, str):
            return None
        marker = warnings.deprecated.__name__
        for node in ast.walk(ast.parse(raw, mode="eval")):
            if not (isinstance(node, ast.Call) and node.args):
                continue
            callee = node.func
            named = (isinstance(callee, ast.Name) and callee.id == marker) or (
                isinstance(callee, ast.Attribute)
                and callee.attr == marker
                and isinstance(callee.value, ast.Name)
                and callee.value.id == warnings.__name__
            )
            message = node.args[0]
            if (
                named
                and isinstance(message, ast.Constant)
                and isinstance(message.value, str)
            ):
                return message.value
        return None

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
