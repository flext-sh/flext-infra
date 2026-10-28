"""Static publication references participating in a native module move.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import importlib.util
from collections.abc import Mapping, Set as AbstractSet
from types import MappingProxyType
from typing import Final, override

import libcst as cst
from libcst.helpers import get_full_name_for_node


class FlextInfraUtilitiesRopeMovePublication:
    """Keep lazy publication module references inside the source-move transaction."""

    @classmethod
    def rewrite_module_move_publications(
        cls,
        source: str,
        *,
        package: str,
        moves: Mapping[str, str],
        exports: Mapping[str, AbstractSet[str]] | None = None,
    ) -> str:
        """Carry exact native module relocations into existing lazy publication data.

        Native Rope owns executable symbol references. This CST pass changes only
        exact import providers and literal installer module targets, preserving
        import aliases, export attributes and all unrelated string payloads.

        When ``exports`` names the relocated module's published keys, a lazy
        entry whose key the destination does not publish keeps its original
        provider: the relocation must never route a publication at a module
        that does not export it, because the family facade's canonical copy
        carries only its own family's names.

        Returns:
            Source with unchanged publication keys and relocated module targets.

        """
        return (
            cst.parse_module(source).visit(cls._Relocate(package, moves, exports)).code
        )

    class _Publication:
        """Decode the installer's literal provider contract for both CST passes."""

        @staticmethod
        def _mapping(value: cst.BaseExpression) -> cst.Dict | None:
            match value:
                case cst.Call(
                    func=cst.Name(value="MappingProxyType"),
                    args=[cst.Arg(value=cst.Dict() as mapping)],
                ):
                    return mapping
                case _:
                    return None

        @staticmethod
        def _target(entry: cst.BaseDictElement) -> tuple[cst.SimpleString, str]:
            """Read the installer's provider or explicit provider/attribute pair.

            Returns:
                The original provider token and exact published attribute.

            Raises:
                TypeError: A key, provider or attribute has the wrong type.
                ValueError: A tuple is not the installer's supported pair shape.

            """
            if not isinstance(entry, cst.DictElement) or not isinstance(
                entry.key, cst.SimpleString
            ):
                message = "Lazy publication move requires literal export keys"
                raise TypeError(message)
            match entry.value:
                case cst.Tuple(
                    elements=[cst.Element(value=module), cst.Element(value=attr)]
                ):
                    pass
                case cst.Tuple():
                    message = "Lazy publication move requires a provider/attribute pair"
                    raise ValueError(message)
                case module:
                    attr = entry.key
            if not isinstance(module, cst.SimpleString) or not isinstance(
                attr, cst.SimpleString
            ):
                message = "Lazy publication move requires literal targets"
                raise TypeError(message)
            if not isinstance(module.evaluated_value, str) or not isinstance(
                attr.evaluated_value, str
            ):
                message = "Lazy publication move requires text targets"
                raise TypeError(message)
            return module, attr.evaluated_value

        @staticmethod
        def _absolute(module: cst.SimpleString, package: str) -> str:
            """Resolve a text token without shortening its qualified root.

            Returns:
                The exact absolute provider name.

            Raises:
                TypeError: The literal is bytes rather than an installer target.

            """
            spelling = module.evaluated_value
            if not isinstance(spelling, str):
                message = "Lazy publication move requires text targets"
                raise TypeError(message)
            return (
                importlib.util.resolve_name(spelling, package)
                if spelling.startswith(".")
                else spelling
            )

    class _Relocate(_Publication, cst.CSTTransformer):
        def __init__(
            self,
            package: str,
            moves: Mapping[str, str],
            exports: Mapping[str, AbstractSet[str]] | None,
        ) -> None:
            self.package: Final = package
            self.moves: Final = MappingProxyType(dict(moves))
            self.exports: Final = (
                MappingProxyType({}) if exports is None else MappingProxyType(exports)
            )

        @override
        def leave_ImportFrom(
            self, original_node: cst.ImportFrom, updated_node: cst.ImportFrom
        ) -> cst.ImportFrom:
            """Keep aliases while relocating an exact imported module provider.

            Returns:
                The original import or its relocated provider.

            Raises:
                ValueError: The provider is not a named module expression.

            """
            if original_node.module is None:
                return updated_node
            module = get_full_name_for_node(original_node.module)
            if module is None:
                message = "Module move requires a named import provider"
                raise ValueError(message)
            absolute = (
                importlib.util.resolve_name(
                    "." * len(original_node.relative) + module, self.package
                )
                if original_node.relative
                else module
            )
            relocated = self.moves.get(absolute)
            return (
                updated_node
                if relocated is None
                else updated_node.with_changes(
                    module=cst.parse_expression(relocated), relative=()
                )
            )

        @override
        def leave_Call(
            self, original_node: cst.Call, updated_node: cst.Call
        ) -> cst.Call:
            if not isinstance(original_node.func, cst.Name) or (
                original_node.func.value != "install_lazy_exports"
            ):
                return updated_node
            return updated_node.with_changes(
                args=tuple(self._argument(argument) for argument in updated_node.args)
            )

        def _argument(self, argument: cst.Arg) -> cst.Arg:
            value = argument.value
            mapping = self._mapping(value)
            if mapping is None or not isinstance(value, cst.Call):
                return argument
            return argument.with_changes(
                value=value.with_changes(
                    args=(
                        value.args[0].with_changes(
                            value=mapping.with_changes(
                                elements=tuple(
                                    self._entry(entry) for entry in mapping.elements
                                )
                            )
                        ),
                    )
                )
            )

        def _entry(self, entry: cst.BaseDictElement) -> cst.BaseDictElement:
            module, _attribute = self._target(entry)
            absolute = self._absolute(module, self.package)
            relocated = self.moves.get(absolute)
            if relocated is None or not isinstance(entry, cst.DictElement):
                return entry
            key = entry.key
            if not isinstance(key, cst.SimpleString):
                return entry
            if self.exports and (
                key.evaluated_value not in self.exports.get(relocated, ())
            ):
                # The destination module does not publish this key: keep the
                # original provider, which still physically exports it inside
                # this transaction; routing it at the canonical copy would
                # resolve a publication to a module that lacks the name.
                return entry
            replacement = (
                "." + relocated[len(self.package) + 1 :]
                if relocated.startswith(f"{self.package}.")
                else relocated
            )
            rewritten = module.with_changes(value=repr(replacement))
            target = entry.value
            if isinstance(target, cst.Tuple):
                first, *remaining = target.elements
                target = target.with_changes(
                    elements=(first.with_changes(value=rewritten), *remaining)
                )
            else:
                target = rewritten
            return entry.with_changes(value=target)


__all__: list[str] = ["FlextInfraUtilitiesRopeMovePublication"]
