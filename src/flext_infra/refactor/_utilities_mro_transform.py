"""LibCST-driven migration of module constants into MRO constants facades.

Centralizes the ``FlextInfraRefactorMROMigrationTransformer`` logic
into the MRO utility chain.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, MutableMapping, MutableSequence, Sequence
from pathlib import Path

import libcst as cst

from flext_infra import (
    FlextInfraRefactorMROPrivateInlineTransformer,
    FlextInfraRefactorMROQualifiedReferenceTransformer,
    FlextInfraUtilitiesParsing,
    c,
    m,
    t,
)


class FlextInfraUtilitiesRefactorMroTransform:
    """Move module-level constants into the constants facade class.

    Usage via namespace::

        from flext_infra import u

        code, migration, symbol_map = u.Infra.migrate_file(
            scan_result=scan_result,
        )
    """

    @staticmethod
    def migrate_file(
        *,
        scan_result: m.Infra.MROScanReport,
    ) -> t.Infra.Triple[str, m.Infra.MROFileMigration, t.StrMapping]:
        """Transform a candidate file and return code plus symbol map."""
        source = Path(scan_result.file).read_text(encoding=c.Infra.Encoding.DEFAULT)
        module = FlextInfraUtilitiesParsing.parse_cst_from_source(source)
        empty_migration = m.Infra.MROFileMigration(
            file=scan_result.file,
            module=scan_result.module,
            moved_symbols=(),
            created_classes=(),
        )
        if module is None:
            return (source, empty_migration, {})
        candidate_symbols = {candidate.symbol for candidate in scan_result.candidates}
        moved_statements, retained_module_body = (
            FlextInfraUtilitiesRefactorMroTransform._classify_statements(
                module=module,
                candidate_symbols=candidate_symbols,
            )
        )
        if not moved_statements:
            return (source, empty_migration, {})
        moved_by_symbol = dict(moved_statements)
        ordered_symbols = [symbol for symbol, _ in moved_statements]
        class_name = scan_result.constants_class or c.Infra.DEFAULT_CONSTANTS_CLASS
        transformed_body, symbol_map, created_classes = (
            FlextInfraUtilitiesRefactorMroTransform._build_transformed_body(
                retained_body=retained_module_body,
                moved_by_symbol=moved_by_symbol,
                ordered_symbols=ordered_symbols,
                class_name=class_name,
            )
        )
        updated_module = module.with_changes(body=tuple(transformed_body))
        facade_alias = scan_result.facade_alias or class_name
        updated_module = FlextInfraUtilitiesRefactorMroTransform._apply_rewriters(
            module=updated_module,
            moved_by_symbol=moved_by_symbol,
            ordered_symbols=ordered_symbols,
            symbol_map=symbol_map,
            facade_alias=facade_alias,
        )
        migration = m.Infra.MROFileMigration(
            file=scan_result.file,
            module=scan_result.module,
            moved_symbols=tuple(ordered_symbols),
            created_classes=created_classes,
        )
        return (updated_module.code, migration, symbol_map)

    @staticmethod
    def _classify_statements(
        *,
        module: cst.Module,
        candidate_symbols: t.Infra.StrSet,
    ) -> t.Infra.Pair[
        Sequence[t.Infra.Pair[str, cst.CSTNode]],
        Sequence[cst.CSTNode],
    ]:
        """Partition module body into moved vs retained statements."""
        moved: MutableSequence[t.Infra.Pair[str, cst.CSTNode]] = []
        retained: MutableSequence[cst.CSTNode] = []
        for stmt in module.body:
            extracted = (
                FlextInfraUtilitiesRefactorMroTransform._extract_moved_statement(
                    statement=stmt,
                    candidate_symbols=candidate_symbols,
                )
            )
            if extracted is None:
                retained.append(stmt)
            else:
                moved.append(extracted)
        return (moved, retained)

    @staticmethod
    def _build_transformed_body(
        *,
        retained_body: Sequence[cst.CSTNode],
        moved_by_symbol: Mapping[str, cst.CSTNode],
        ordered_symbols: t.StrSequence,
        class_name: str,
    ) -> t.Infra.Triple[
        Sequence[cst.CSTNode],
        t.MutableStrMapping,
        tuple[str, ...],
    ]:
        """Merge moved symbols into the facade class within the retained body."""
        transformed_body: MutableSequence[cst.CSTNode] = []
        symbol_map: t.MutableStrMapping = {}
        class_found = False
        for retained_stmt in retained_body:
            if (
                isinstance(retained_stmt, cst.ClassDef)
                and retained_stmt.name.value == class_name
            ):
                class_found = True
                transformed_class, class_symbol_map = (
                    FlextInfraUtilitiesRefactorMroTransform._migrate_constants_class(
                        class_def=retained_stmt,
                        moved_by_symbol=moved_by_symbol,
                        ordered_symbols=ordered_symbols,
                    )
                )
                transformed_body.append(transformed_class)
                symbol_map.update(class_symbol_map)
                continue
            transformed_body.append(retained_stmt)
        created_classes: tuple[str, ...] = ()
        if not class_found:
            new_class, class_symbol_map = (
                FlextInfraUtilitiesRefactorMroTransform._create_constants_class(
                    class_name=class_name,
                    moved_by_symbol=moved_by_symbol,
                    ordered_symbols=ordered_symbols,
                )
            )
            transformed_body.append(new_class)
            symbol_map.update(class_symbol_map)
            created_classes = (class_name,)
        return (transformed_body, symbol_map, created_classes)

    @staticmethod
    def _apply_rewriters(
        *,
        module: cst.Module,
        moved_by_symbol: Mapping[str, cst.CSTNode],
        ordered_symbols: t.StrSequence,
        symbol_map: t.StrMapping,
        facade_alias: str,
    ) -> cst.Module:
        """Apply private-inline and qualified-reference transformers."""
        replacement_values = (
            FlextInfraUtilitiesRefactorMroTransform._collect_private_replacements(
                moved_by_symbol=moved_by_symbol,
                ordered_symbols=ordered_symbols,
            )
        )
        inline_transformer = FlextInfraRefactorMROPrivateInlineTransformer(
            replacement_values=replacement_values,
        )
        module = module.visit(inline_transformer)
        qualified_renames = (
            FlextInfraUtilitiesRefactorMroTransform._build_qualified_renames(
                symbol_map=symbol_map,
                facade_alias=facade_alias,
            )
        )
        if qualified_renames:
            qualified_transformer = FlextInfraRefactorMROQualifiedReferenceTransformer(
                renames=qualified_renames,
            )
            module = module.visit(qualified_transformer)
        return module

    @staticmethod
    def _collect_private_replacements(
        *,
        moved_by_symbol: Mapping[str, cst.CSTNode],
        ordered_symbols: t.StrSequence,
    ) -> MutableMapping[str, cst.BaseExpression]:
        """Collect replacement values for private (underscore-prefixed) symbols."""
        replacement_values: MutableMapping[str, cst.BaseExpression] = {}
        for symbol in ordered_symbols:
            if not symbol.startswith("_"):
                continue
            value = FlextInfraUtilitiesRefactorMroTransform._statement_value(
                statement=moved_by_symbol[symbol],
            )
            if value is not None:
                replacement_values[symbol] = value
        return replacement_values

    @staticmethod
    def _build_qualified_renames(
        *,
        symbol_map: t.StrMapping,
        facade_alias: str,
    ) -> MutableMapping[str, cst.BaseExpression]:
        """Build qualified attribute expressions for public dotted symbol paths."""
        qualified_renames: MutableMapping[str, cst.BaseExpression] = {}
        for symbol, target_path in symbol_map.items():
            if symbol.startswith("_") or "." not in target_path:
                continue
            parts = target_path.split(".")
            current: cst.BaseExpression = cst.Name(facade_alias)
            for part in parts:
                current = cst.Attribute(value=current, attr=cst.Name(part))
            qualified_renames[symbol] = current
        return qualified_renames

    @staticmethod
    def _extract_moved_statement(
        *,
        statement: cst.CSTNode,
        candidate_symbols: t.Infra.StrSet,
    ) -> t.Infra.Pair[str, cst.CSTNode] | None:
        extracted = FlextInfraUtilitiesRefactorMroTransform._extract_symbol_and_node(
            statement=statement,
        )
        if extracted is None:
            return None
        symbol, node = extracted
        if symbol not in candidate_symbols:
            return None
        return (symbol, node)

    @staticmethod
    def _extract_symbol_and_node(
        *,
        statement: cst.CSTNode,
    ) -> t.Infra.Pair[str, cst.CSTNode] | None:
        """Return (symbol, node) from a top-level statement, or None."""
        if isinstance(statement, cst.ClassDef):
            return (statement.name.value, statement)
        if isinstance(statement, cst.TypeAlias):
            return (statement.name.value, statement)
        if not isinstance(statement, cst.SimpleStatementLine):
            return None
        return FlextInfraUtilitiesRefactorMroTransform._extract_symbol_from_simple(
            statement=statement,
        )

    @staticmethod
    def _extract_symbol_from_simple(
        *,
        statement: cst.SimpleStatementLine,
    ) -> t.Infra.Pair[str, cst.CSTNode] | None:
        """Extract (symbol, inner_node) from a single-statement simple line."""
        if len(statement.body) != 1:
            return None
        first_stmt = statement.body[0]
        symbol = FlextInfraUtilitiesRefactorMroTransform._symbol_from_simple_stmt(
            stmt=first_stmt,
        )
        if symbol is None:
            return None
        return (symbol, first_stmt)

    @staticmethod
    def _symbol_from_simple_stmt(
        *,
        stmt: cst.BaseSmallStatement,
    ) -> str | None:
        """Extract the symbol name from an AnnAssign, Assign, or TypeAlias."""
        if isinstance(stmt, cst.AnnAssign):
            return stmt.target.value if isinstance(stmt.target, cst.Name) else None
        if isinstance(stmt, cst.Assign):
            return FlextInfraUtilitiesRefactorMroTransform._symbol_from_assign(
                stmt=stmt,
            )
        if isinstance(stmt, cst.TypeAlias):
            return stmt.name.value
        return None

    @staticmethod
    def _symbol_from_assign(*, stmt: cst.Assign) -> str | None:
        """Extract symbol name from a single-target Assign."""
        if len(stmt.targets) != 1:
            return None
        assign_target = stmt.targets[0].target
        if not isinstance(assign_target, cst.Name):
            return None
        return assign_target.value

    @staticmethod
    def _migrate_constants_class(
        *,
        class_def: cst.ClassDef,
        moved_by_symbol: Mapping[str, cst.CSTNode],
        ordered_symbols: t.StrSequence,
    ) -> t.Infra.Pair[cst.ClassDef, t.StrMapping]:
        retained_class_body, alias_by_symbol, alias_replacement_values = (
            FlextInfraUtilitiesRefactorMroTransform._partition_class_body(
                class_body=class_def.body.body,
                moved_by_symbol=moved_by_symbol,
            )
        )
        is_types_facade = class_def.name.value.endswith("Types")
        symbol_map, moved_lines, moved_core_lines = (
            FlextInfraUtilitiesRefactorMroTransform._retarget_ordered_symbols(
                ordered_symbols=ordered_symbols,
                moved_by_symbol=moved_by_symbol,
                alias_by_symbol=alias_by_symbol,
                alias_replacement_values=alias_replacement_values,
                is_types_facade=is_types_facade,
            )
        )
        final_body = FlextInfraUtilitiesRefactorMroTransform._assemble_class_body(
            retained_body=retained_class_body,
            moved_lines=moved_lines,
            moved_core_lines=moved_core_lines,
        )
        return (
            class_def.with_changes(
                body=class_def.body.with_changes(body=tuple(final_body)),
            ),
            symbol_map,
        )

    @staticmethod
    def _partition_class_body(
        *,
        class_body: Sequence[cst.CSTNode],
        moved_by_symbol: Mapping[str, cst.CSTNode],
    ) -> t.Infra.Triple[
        Sequence[cst.CSTNode],
        t.MutableStrMapping,
        MutableMapping[str, cst.BaseExpression],
    ]:
        """Split class body into retained statements, alias mappings, and replacement values."""
        retained: MutableSequence[cst.CSTNode] = []
        alias_by_symbol: t.MutableStrMapping = {}
        alias_replacement_values: MutableMapping[str, cst.BaseExpression] = {}
        for statement in class_body:
            alias = FlextInfraUtilitiesRefactorMroTransform._extract_alias_assignment(
                statement=statement,
            )
            if alias is not None and alias[1] in moved_by_symbol:
                alias_by_symbol[alias[1]] = alias[0]
                private_value = (
                    FlextInfraUtilitiesRefactorMroTransform._statement_value(
                        statement=moved_by_symbol[alias[1]],
                    )
                )
                if private_value is not None:
                    alias_replacement_values[alias[0]] = private_value
                continue
            retained.append(statement)
        return (retained, alias_by_symbol, alias_replacement_values)

    @staticmethod
    def _retarget_ordered_symbols(
        *,
        ordered_symbols: t.StrSequence,
        moved_by_symbol: Mapping[str, cst.CSTNode],
        alias_by_symbol: t.StrMapping,
        alias_replacement_values: Mapping[str, cst.BaseExpression],
        is_types_facade: bool,
    ) -> t.Infra.Triple[
        t.MutableStrMapping,
        Sequence[cst.CSTNode],
        Sequence[cst.CSTNode],
    ]:
        """Build symbol map and retargeted nodes, split into regular vs core lines."""
        symbol_map: t.MutableStrMapping = {}
        added_targets: t.Infra.StrSet = set()
        moved_lines: MutableSequence[cst.CSTNode] = []
        moved_core_lines: MutableSequence[cst.CSTNode] = []
        for symbol in ordered_symbols:
            target = alias_by_symbol.get(
                symbol,
            ) or FlextInfraUtilitiesRefactorMroTransform._default_target(
                symbol=symbol,
            )
            moved_statement = moved_by_symbol[symbol]
            use_core_namespace = is_types_facade and isinstance(
                moved_statement,
                cst.TypeAlias,
            )
            map_target = f"Core.{target}" if use_core_namespace else target
            if map_target in added_targets:
                continue
            added_targets.add(map_target)
            symbol_map[symbol] = map_target
            replacement_value = alias_replacement_values.get(target)
            moved_node = FlextInfraUtilitiesRefactorMroTransform._retarget_statement(
                statement=moved_statement,
                target_name=target,
                replacement_value=replacement_value,
            )
            if use_core_namespace:
                moved_core_lines.append(moved_node)
            else:
                moved_lines.append(moved_node)
        return (symbol_map, moved_lines, moved_core_lines)

    @staticmethod
    def _assemble_class_body(
        *,
        retained_body: Sequence[cst.CSTNode],
        moved_lines: Sequence[cst.CSTNode],
        moved_core_lines: Sequence[cst.CSTNode],
    ) -> Sequence[cst.BaseStatement]:
        """Combine retained, core, and moved nodes into the final class body."""
        cleaned_body = [
            statement
            for statement in retained_body
            if not (
                moved_lines
                and isinstance(statement, cst.SimpleStatementLine)
                and (len(statement.body) == 1)
                and isinstance(statement.body[0], cst.Pass)
            )
        ]
        final_nodes: MutableSequence[cst.CSTNode] = [*cleaned_body]
        if moved_core_lines:
            final_nodes = FlextInfraUtilitiesRefactorMroTransform._integrate_core_lines(
                final_nodes=final_nodes,
                moved_core_lines=moved_core_lines,
            )
        final_nodes.extend(moved_lines)
        final_body = [
            statement
            for statement in final_nodes
            if isinstance(statement, cst.BaseStatement)
        ]
        if not final_body:
            final_body = [cst.SimpleStatementLine(body=[cst.Pass()])]
        return final_body

    @staticmethod
    def _integrate_core_lines(
        *,
        final_nodes: MutableSequence[cst.CSTNode],
        moved_core_lines: Sequence[cst.CSTNode],
    ) -> MutableSequence[cst.CSTNode]:
        """Merge core-namespace lines into the class body, creating _Core if needed."""
        has_existing_core = any(
            isinstance(s, cst.ClassDef) and s.name.value == "Core" for s in final_nodes
        )
        if has_existing_core:
            merged_body, _ = FlextInfraUtilitiesRefactorMroTransform._merge_core_class(
                class_body=final_nodes,
                moved_core_lines=moved_core_lines,
                target_class_name="Core",
            )
            return list(merged_body)
        merged_body, inserted_core = (
            FlextInfraUtilitiesRefactorMroTransform._merge_core_class(
                class_body=final_nodes,
                moved_core_lines=moved_core_lines,
                target_class_name="_Core",
            )
        )
        result = list(merged_body)
        if inserted_core and (
            not FlextInfraUtilitiesRefactorMroTransform._has_core_alias(
                class_body=result,
            )
        ):
            result.append(
                FlextInfraUtilitiesRefactorMroTransform._core_alias_statement(),
            )
        return result

    @staticmethod
    def _create_constants_class(
        *,
        class_name: str,
        moved_by_symbol: Mapping[str, cst.CSTNode],
        ordered_symbols: t.StrSequence,
    ) -> t.Infra.Pair[cst.ClassDef, t.StrMapping]:
        class_template = cst.ClassDef(
            name=cst.Name(class_name),
            body=cst.IndentedBlock(body=()),
        )
        class_body: MutableSequence[cst.BaseStatement] = []
        core_body: MutableSequence[cst.BaseStatement] = []
        symbol_map: t.MutableStrMapping = {}
        is_types_facade = class_name.endswith("Types")
        for symbol in ordered_symbols:
            target = FlextInfraUtilitiesRefactorMroTransform._default_target(
                symbol=symbol,
            )
            statement = moved_by_symbol[symbol]
            use_core_namespace = is_types_facade and isinstance(
                statement,
                cst.TypeAlias,
            )
            symbol_map[symbol] = f"Core.{target}" if use_core_namespace else target
            moved_node = FlextInfraUtilitiesRefactorMroTransform._retarget_statement(
                statement=statement,
                target_name=target,
                replacement_value=None,
            )
            if isinstance(moved_node, cst.BaseStatement):
                if use_core_namespace:
                    core_body.append(moved_node)
                else:
                    class_body.append(moved_node)
        if core_body:
            class_body.extend(
                [
                    cst.ClassDef(
                        name=cst.Name("_Core"),
                        body=cst.IndentedBlock(body=tuple(core_body)),
                    ),
                    FlextInfraUtilitiesRefactorMroTransform._core_alias_statement(),
                ],
            )
        return (
            class_template.with_changes(
                body=class_template.body.with_changes(body=tuple(class_body)),
            ),
            symbol_map,
        )

    @staticmethod
    def _extract_alias_assignment(
        *,
        statement: cst.CSTNode,
    ) -> t.Infra.StrPair | None:
        if not isinstance(statement, cst.SimpleStatementLine):
            return None
        if len(statement.body) != 1:
            return None
        assign = statement.body[0]
        if isinstance(assign, cst.AnnAssign):
            return FlextInfraUtilitiesRefactorMroTransform._alias_from_ann_assign(
                assign=assign,
            )
        if isinstance(assign, cst.Assign):
            return FlextInfraUtilitiesRefactorMroTransform._alias_from_assign(
                assign=assign,
            )
        return None

    @staticmethod
    def _alias_from_ann_assign(*, assign: cst.AnnAssign) -> t.Infra.StrPair | None:
        """Extract (target, value) name pair from an annotated assignment."""
        if not isinstance(assign.target, cst.Name):
            return None
        if not isinstance(assign.value, cst.Name):
            return None
        return (assign.target.value, assign.value.value)

    @staticmethod
    def _alias_from_assign(*, assign: cst.Assign) -> t.Infra.StrPair | None:
        """Extract (target, value) name pair from a plain assignment."""
        if len(assign.targets) != 1:
            return None
        if not isinstance(assign.targets[0].target, cst.Name):
            return None
        if not isinstance(assign.value, cst.Name):
            return None
        return (assign.targets[0].target.value, assign.value.value)

    @staticmethod
    def _default_target(*, symbol: str) -> str:
        stripped = symbol.lstrip("_")
        return stripped or symbol

    @staticmethod
    def _statement_value(
        *,
        statement: cst.CSTNode,
    ) -> cst.BaseExpression | None:
        if isinstance(statement, cst.TypeAlias):
            return statement.value
        if isinstance(statement, cst.AnnAssign):
            return statement.value
        if isinstance(statement, cst.Assign):
            return statement.value
        return None

    @staticmethod
    def _retarget_statement(
        *,
        statement: cst.CSTNode,
        target_name: str,
        replacement_value: cst.BaseExpression | None,
    ) -> cst.CSTNode:
        if isinstance(statement, cst.ClassDef):
            return FlextInfraUtilitiesRefactorMroTransform._retarget_class_def(
                statement=statement,
                target_name=target_name,
            )
        if isinstance(statement, cst.TypeAlias):
            return cst.SimpleStatementLine(
                body=[statement.with_changes(name=cst.Name(target_name))],
            )
        if isinstance(statement, cst.AnnAssign):
            return FlextInfraUtilitiesRefactorMroTransform._retarget_ann_assign(
                statement=statement,
                target_name=target_name,
                replacement_value=replacement_value,
            )
        if isinstance(statement, cst.Assign):
            return FlextInfraUtilitiesRefactorMroTransform._retarget_assign(
                statement=statement,
                target_name=target_name,
                replacement_value=replacement_value,
            )
        msg = "unsupported constant statement type"
        raise ValueError(msg)

    @staticmethod
    def _retarget_class_def(
        *,
        statement: cst.ClassDef,
        target_name: str,
    ) -> cst.ClassDef:
        """Rename a ClassDef to the target name if needed."""
        if statement.name.value == target_name:
            return statement
        return statement.with_changes(name=cst.Name(target_name))

    @staticmethod
    def _retarget_ann_assign(
        *,
        statement: cst.AnnAssign,
        target_name: str,
        replacement_value: cst.BaseExpression | None,
    ) -> cst.SimpleStatementLine:
        """Re-target an annotated assignment with optional value replacement."""
        changes: MutableMapping[str, cst.Name | cst.BaseExpression] = {
            "target": cst.Name(target_name),
        }
        if replacement_value is not None:
            changes["value"] = replacement_value
        return cst.SimpleStatementLine(
            body=[statement.with_changes(**changes)],
        )

    @staticmethod
    def _retarget_assign(
        *,
        statement: cst.Assign,
        target_name: str,
        replacement_value: cst.BaseExpression | None,
    ) -> cst.SimpleStatementLine:
        """Re-target a plain assignment with optional value replacement."""
        assign_value = replacement_value or statement.value
        return cst.SimpleStatementLine(
            body=[
                statement.with_changes(
                    targets=(cst.AssignTarget(target=cst.Name(target_name)),),
                    value=assign_value,
                ),
            ],
        )

    @staticmethod
    def _merge_core_class(
        *,
        class_body: Sequence[cst.CSTNode],
        moved_core_lines: Sequence[cst.CSTNode],
        target_class_name: str = "_Core",
    ) -> t.Infra.Pair[Sequence[cst.CSTNode], bool]:
        for index, statement in enumerate(class_body):
            if not (
                isinstance(statement, cst.ClassDef)
                and statement.name.value == target_class_name
            ):
                continue
            existing_names = {
                FlextInfraUtilitiesRefactorMroTransform._statement_symbol(
                    statement=item,
                )
                for item in statement.body.body
            }
            appended_lines = [
                moved
                for moved in moved_core_lines
                if FlextInfraUtilitiesRefactorMroTransform._statement_symbol(
                    statement=moved,
                )
                not in existing_names
            ]
            existing_body: Sequence[cst.BaseStatement] = [
                item
                for item in statement.body.body
                if isinstance(item, cst.BaseStatement)
            ]
            updated_core = statement.with_changes(
                body=statement.body.with_changes(
                    body=(*existing_body, *appended_lines),
                ),
            )
            merged = [*class_body]
            merged[index] = updated_core
            return (merged, False)
        merged_body = [
            *class_body,
            cst.ClassDef(
                name=cst.Name(target_class_name),
                body=cst.IndentedBlock(
                    body=tuple(
                        item
                        for item in moved_core_lines
                        if isinstance(item, cst.BaseStatement)
                    ),
                ),
                leading_lines=(cst.EmptyLine(),),
            ),
        ]
        return (merged_body, True)

    @staticmethod
    def _statement_symbol(*, statement: cst.CSTNode) -> str:
        if isinstance(statement, cst.TypeAlias):
            return statement.name.value
        if isinstance(statement, cst.SimpleStatementLine) and len(statement.body) == 1:
            base_statement = statement.body[0]
            if isinstance(base_statement, cst.TypeAlias):
                return base_statement.name.value
            if isinstance(base_statement, cst.AnnAssign) and isinstance(
                base_statement.target,
                cst.Name,
            ):
                return base_statement.target.value
            if (
                isinstance(base_statement, cst.Assign)
                and len(base_statement.targets) == 1
            ):
                assign_target = base_statement.targets[0].target
                if isinstance(assign_target, cst.Name):
                    return assign_target.value
        return ""

    @staticmethod
    def _core_alias_statement() -> cst.SimpleStatementLine:
        return cst.SimpleStatementLine(
            body=[
                cst.Assign(
                    targets=(cst.AssignTarget(target=cst.Name("Core")),),
                    value=cst.Name("_Core"),
                ),
            ],
        )

    @staticmethod
    def _has_core_alias(*, class_body: Sequence[cst.CSTNode]) -> bool:
        for statement in class_body:
            if isinstance(statement, cst.ClassDef) and statement.name.value == "Core":
                return True
            alias = FlextInfraUtilitiesRefactorMroTransform._extract_alias_assignment(
                statement=statement,
            )
            if alias == ("Core", "_Core"):
                return True
        return False


__all__ = ["FlextInfraUtilitiesRefactorMroTransform"]
