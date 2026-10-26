"""Static publication references participating in a native module move.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import importlib.util
from collections.abc import Mapping, Sequence

import libcst as cst
from libcst.helpers import get_full_name_for_node


class FlextInfraUtilitiesRopeMovePublication:
    """Keep lazy publication module references inside the source-move transaction."""

    @classmethod
    def plan_retired_module_publication_repairs(
        cls,
        sources: Mapping[str, str],
        *,
        consumers: Sequence[str],
    ) -> dict[str, tuple[str, dict[str, str]]]:
        """Complete source moves whose existing lazy targets name retired modules.

        ``sources`` is the caller's authenticated package module inventory.
        Export names remain unchanged. Each retired provider must have exactly
        one current declaration for its existing published class.

        Returns:
            Changed module text and the exact relocation evidence per consumer.

        Raises:
            ValueError: A retired publication has missing or competing owners.

        """
        parsed = {name: cst.parse_module(source) for name, source in sources.items()}
        declarations: dict[str, list[str]] = {}
        for module, tree in parsed.items():
            for statement in tree.body:
                if isinstance(statement, cst.ClassDef):
                    declarations.setdefault(statement.name.value, []).append(module)
        repaired: dict[str, tuple[str, dict[str, str]]] = {}
        for consumer, tree in parsed.items():
            if consumer not in consumers:
                continue
            package = consumer.removesuffix(".__init__")
            moves: dict[str, str] = {}

            class Locate(cst.CSTVisitor):
                def visit_Call(self, node: cst.Call) -> None:
                    if not (
                        isinstance(node.func, cst.Name)
                        and node.func.value == "install_lazy_exports"
                    ):
                        return
                    for argument in node.args:
                        mapping = argument.value
                        if not (
                            isinstance(mapping, cst.Call)
                            and isinstance(mapping.func, cst.Name)
                            and mapping.func.value == "MappingProxyType"
                            and len(mapping.args) == 1
                            and isinstance(mapping.args[0].value, cst.Dict)
                        ):
                            continue
                        for entry in mapping.args[0].value.elements:
                            if not (
                                isinstance(entry, cst.DictElement)
                                and isinstance(entry.key, cst.SimpleString)
                            ):
                                message = "Lazy move repair requires literal exports"
                                raise ValueError(message)
                            target = entry.value
                            module = (
                                target.elements[0].value
                                if isinstance(target, cst.Tuple) and target.elements
                                else target
                            )
                            attribute = (
                                target.elements[1].value
                                if isinstance(target, cst.Tuple)
                                and len(target.elements) == 2
                                else entry.key
                            )
                            if not (
                                isinstance(module, cst.SimpleString)
                                and isinstance(attribute, cst.SimpleString)
                            ):
                                message = "Lazy move repair requires literal targets"
                                raise ValueError(message)
                            spelling = module.evaluated_value
                            exported = attribute.evaluated_value
                            if not isinstance(spelling, str) or not isinstance(
                                exported, str
                            ):
                                message = "Lazy move repair requires text targets"
                                raise ValueError(message)
                            absolute = (
                                importlib.util.resolve_name(spelling, package)
                                if spelling.startswith(".")
                                else spelling
                            )
                            if (
                                absolute in parsed
                                or absolute.partition(".")[0]
                                != consumer.partition(".")[0]
                            ):
                                continue
                            owners = declarations.get(exported, ())
                            if len(owners) != 1:
                                message = (
                                    "Retired lazy publication has no unique owner: "
                                    f"{consumer}:{exported}:{absolute}; "
                                    f"owners={tuple(owners)}"
                                )
                                raise ValueError(message)
                            existing = moves.setdefault(absolute, owners[0])
                            if existing != owners[0]:
                                message = (
                                    "Retired lazy module has split declarations: "
                                    f"{absolute}; owners={existing},{owners[0]}"
                                )
                                raise ValueError(message)

            tree.visit(Locate())
            if moves:
                repaired[consumer] = (
                    cls.rewrite_module_move_publications(
                        sources[consumer], package=package, moves=moves
                    ),
                    moves,
                )
        return repaired

    @staticmethod
    def rewrite_module_move_publications(
        source: str,
        *,
        package: str,
        moves: Mapping[str, str],
    ) -> str:
        """Relocate existing installer targets without changing their export names.

        Only literal module targets inside the canonical lazy installer are
        rewritten. The native module move owns import and symbol references;
        these data references need the same exact relocation map.

        Returns:
            Source with the same publication keys and relocated module targets.

        Raises:
            ValueError: An installer contains a nonliteral module target.

        """

        class Relocate(cst.CSTTransformer):
            def leave_ImportFrom(
                self,
                original_node: cst.ImportFrom,
                updated_node: cst.ImportFrom,
            ) -> cst.ImportFrom:
                if original_node.module is None:
                    return updated_node
                module = get_full_name_for_node(original_node.module)
                if module is None:
                    message = "Module move requires a named import provider"
                    raise ValueError(message)
                absolute = (
                    importlib.util.resolve_name(
                        "." * len(original_node.relative) + module, package
                    )
                    if original_node.relative
                    else module
                )
                relocated = moves.get(absolute)
                return (
                    updated_node
                    if relocated is None
                    else updated_node.with_changes(
                        module=cst.parse_expression(relocated),
                        relative=(),
                    )
                )

            def leave_Call(
                self, original_node: cst.Call, updated_node: cst.Call
            ) -> cst.Call:
                if not (
                    isinstance(original_node.func, cst.Name)
                    and original_node.func.value == "install_lazy_exports"
                ):
                    return updated_node
                arguments: list[cst.Arg] = []
                for argument in updated_node.args:
                    value = argument.value
                    if not (
                        isinstance(value, cst.Call)
                        and isinstance(value.func, cst.Name)
                        and value.func.value == "MappingProxyType"
                        and len(value.args) == 1
                        and isinstance(value.args[0].value, cst.Dict)
                    ):
                        arguments.append(argument)
                        continue
                    entries: list[cst.DictElement] = []
                    for entry in value.args[0].value.elements:
                        if not isinstance(entry, cst.DictElement):
                            message = "Lazy publication move requires literal entries"
                            raise ValueError(message)
                        target = entry.value
                        module = (
                            target.elements[0].value
                            if isinstance(target, cst.Tuple) and target.elements
                            else target
                        )
                        if not isinstance(module, cst.SimpleString):
                            message = "Lazy publication move requires literal targets"
                            raise ValueError(message)
                        spelling = module.evaluated_value
                        if not isinstance(spelling, str):
                            message = "Lazy publication move requires text targets"
                            raise ValueError(message)
                        absolute = (
                            importlib.util.resolve_name(spelling, package)
                            if spelling.startswith(".")
                            else spelling
                        )
                        relocated = moves.get(absolute)
                        if relocated is not None:
                            replacement = (
                                "." + relocated[len(package) + 1 :]
                                if relocated.startswith(f"{package}.")
                                else relocated
                            )
                            rewritten = module.with_changes(value=repr(replacement))
                            if isinstance(target, cst.Tuple):
                                first = target.elements[0]
                                if not isinstance(first, cst.Element):
                                    message = "Lazy publication move requires a module"
                                    raise ValueError(message)
                                target = target.with_changes(
                                    elements=(
                                        first.with_changes(value=rewritten),
                                        *target.elements[1:],
                                    )
                                )
                            else:
                                target = rewritten
                        entries.append(entry.with_changes(value=target))
                    mapping = value.args[0].value.with_changes(elements=entries)
                    arguments.append(
                        argument.with_changes(
                            value=value.with_changes(
                                args=(value.args[0].with_changes(value=mapping),)
                            )
                        )
                    )
                return updated_node.with_changes(args=arguments)

        return cst.parse_module(source).visit(Relocate()).code


__all__: list[str] = ["FlextInfraUtilitiesRopeMovePublication"]
