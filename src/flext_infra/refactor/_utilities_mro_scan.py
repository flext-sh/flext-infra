"""MRO migration scanner utilities for the MRO utility chain.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import re
from collections.abc import Mapping, MutableSequence, Sequence
from pathlib import Path

from flext_infra import (
    FlextInfraUtilitiesIteration,
    FlextInfraUtilitiesParsing,
    c,
    m,
    t,
)


class FlextInfraUtilitiesRefactorMroScan:
    _MRO_SCAN_CONSTANT_PATTERN: re.Pattern[str] = re.compile(r"^_?[A-Z][A-Z0-9_]*$")
    _MRO_SCAN_TYPE_CANDIDATE_PATTERN: re.Pattern[str] = re.compile(
        r"^_?[A-Za-z][A-Za-z0-9_]*$",
    )

    @staticmethod
    def scan_workspace(
        *,
        workspace_root: Path,
        target: str,
    ) -> t.Infra.Pair[Sequence[m.Infra.MROScanReport], int]:
        """Scan workspace and collect migration reports for a target family."""
        if target not in c.Infra.MRO_TARGETS:
            return ([], 0)
        results: MutableSequence[m.Infra.MROScanReport] = []
        scanned = 0
        target_specs = FlextInfraUtilitiesRefactorMroScan._target_specs(
            target=target,
        )
        for project_root in FlextInfraUtilitiesRefactorMroScan._project_roots(
            workspace_root=workspace_root,
        ):
            for target_spec in target_specs:
                for file_path in FlextInfraUtilitiesRefactorMroScan._iter_target_files(
                    project_root=project_root,
                    target_spec=target_spec,
                ):
                    scanned += 1
                    result = FlextInfraUtilitiesRefactorMroScan.scan_file(
                        file_path=file_path,
                        project_root=project_root,
                        target_spec=target_spec,
                    )
                    if result is None or not result.candidates:
                        continue
                    results.append(result)
        return (results, scanned)

    @staticmethod
    def scan_file(
        *,
        file_path: Path,
        project_root: Path,
        target_spec: m.Infra.MROTargetSpec,
    ) -> m.Infra.MROScanReport | None:
        """Scan one file and return migration candidates when found."""
        tree = FlextInfraUtilitiesParsing.parse_module_ast(file_path)
        if tree is None:
            return None
        constants_class = FlextInfraUtilitiesRefactorMroScan._facade_class_name(
            tree=tree,
            target_spec=target_spec,
        )
        if not constants_class:
            return None
        module = FlextInfraUtilitiesRefactorMroScan._module_path(
            file_path=file_path,
            project_root=project_root,
        )
        candidates: MutableSequence[m.Infra.MROSymbolCandidate] = []
        for stmt in tree.body:
            candidate = FlextInfraUtilitiesRefactorMroScan._candidate_from_statement(
                stmt=stmt,
                target_spec=target_spec,
            )
            if candidate is not None:
                candidates.append(candidate)
        return m.Infra.MROScanReport(
            file=str(file_path),
            module=module,
            constants_class=constants_class,
            facade_alias=target_spec.family_alias,
            candidates=tuple(candidates),
        )

    @staticmethod
    def _candidate_from_statement(
        *,
        stmt: ast.stmt,
        target_spec: m.Infra.MROTargetSpec,
    ) -> m.Infra.MROSymbolCandidate | None:
        if target_spec.family_alias == "t":
            return FlextInfraUtilitiesRefactorMroScan._typing_candidate_from_statement(
                stmt=stmt,
            )
        if target_spec.family_alias == "p":
            return (
                FlextInfraUtilitiesRefactorMroScan._protocol_candidate_from_statement(
                    stmt=stmt,
                )
            )
        return FlextInfraUtilitiesRefactorMroScan._constant_candidate_from_statement(
            stmt=stmt,
        )

    @staticmethod
    def _constant_candidate_from_statement(
        *,
        stmt: ast.stmt,
    ) -> m.Infra.MROSymbolCandidate | None:
        """Extract a constant candidate from an AnnAssign or Assign statement."""
        symbol = FlextInfraUtilitiesRefactorMroScan._extract_constant_symbol(stmt=stmt)
        if symbol is None:
            return None
        return m.Infra.MROSymbolCandidate(
            symbol=symbol,
            line=stmt.lineno,
            kind="constant",
            class_name="",
            facade_name="",
        )

    @staticmethod
    def _extract_constant_symbol(*, stmt: ast.stmt) -> str | None:
        """Return the constant symbol name if the statement is a valid constant."""
        if isinstance(stmt, ast.AnnAssign):
            return FlextInfraUtilitiesRefactorMroScan._constant_from_ann_assign(
                stmt=stmt,
            )
        if isinstance(stmt, ast.Assign):
            return FlextInfraUtilitiesRefactorMroScan._constant_from_assign(
                stmt=stmt,
            )
        return None

    @staticmethod
    def _constant_from_ann_assign(*, stmt: ast.AnnAssign) -> str | None:
        """Extract constant name from a Final-annotated AnnAssign."""
        if not isinstance(stmt.target, ast.Name):
            return None
        if not FlextInfraUtilitiesRefactorMroScan._MRO_SCAN_CONSTANT_PATTERN.match(
            stmt.target.id,
        ):
            return None
        if not FlextInfraUtilitiesRefactorMroScan._is_final_annotation(
            annotation=stmt.annotation,
        ):
            return None
        return stmt.target.id

    @staticmethod
    def _constant_from_assign(*, stmt: ast.Assign) -> str | None:
        """Extract constant name from an UPPER_CASE Assign."""
        if len(stmt.targets) != 1:
            return None
        target = stmt.targets[0]
        if not isinstance(target, ast.Name):
            return None
        if not FlextInfraUtilitiesRefactorMroScan._MRO_SCAN_CONSTANT_PATTERN.match(
            target.id,
        ):
            return None
        return target.id

    @staticmethod
    def _project_roots(*, workspace_root: Path) -> Sequence[Path]:
        return FlextInfraUtilitiesIteration.discover_project_roots(
            workspace_root=workspace_root,
        )

    @staticmethod
    def _target_specs(
        *,
        target: str,
    ) -> t.Infra.VariadicTuple[m.Infra.MROTargetSpec]:
        all_specs = FlextInfraUtilitiesRefactorMroScan._build_all_target_specs()
        spec_by_name = {spec.family_alias: spec for spec in all_specs}
        target_name_to_alias: Mapping[str, str] = {
            "constants": "c",
            "typings": "t",
            "protocols": "p",
            "models": "m",
            "utilities": "u",
        }
        alias = target_name_to_alias.get(target)
        if alias is not None and alias in spec_by_name:
            return (spec_by_name[alias],)
        return all_specs

    @staticmethod
    def _build_all_target_specs() -> t.Infra.VariadicTuple[m.Infra.MROTargetSpec]:
        """Construct the full set of MRO target specs."""
        return (
            m.Infra.MROTargetSpec(
                family_alias="c",
                file_names=c.Infra.MRO_CONSTANTS_FILE_NAMES,
                package_directory=c.Infra.MRO_CONSTANTS_DIRECTORY,
                class_suffix=c.Infra.CONSTANTS_CLASS_SUFFIX,
            ),
            m.Infra.MROTargetSpec(
                family_alias="t",
                file_names=c.Infra.MRO_TYPINGS_FILE_NAMES,
                package_directory=c.Infra.MRO_TYPINGS_DIRECTORY,
                class_suffix="Types",
            ),
            m.Infra.MROTargetSpec(
                family_alias="p",
                file_names=c.Infra.MRO_PROTOCOLS_FILE_NAMES,
                package_directory=c.Infra.MRO_PROTOCOLS_DIRECTORY,
                class_suffix="Protocols",
            ),
            m.Infra.MROTargetSpec(
                family_alias="m",
                file_names=c.Infra.MRO_MODELS_FILE_NAMES,
                package_directory=c.Infra.MRO_MODELS_DIRECTORY,
                class_suffix="Models",
            ),
            m.Infra.MROTargetSpec(
                family_alias="u",
                file_names=c.Infra.MRO_UTILITIES_FILE_NAMES,
                package_directory=c.Infra.MRO_UTILITIES_DIRECTORY,
                class_suffix="Utilities",
            ),
        )

    @staticmethod
    def _iter_target_files(
        *,
        project_root: Path,
        target_spec: m.Infra.MROTargetSpec,
    ) -> Sequence[Path]:
        candidates: t.Infra.PathSet = set()
        for directory_name in c.Infra.MRO_SCAN_DIRECTORIES:
            root: Path = project_root / directory_name
            if not root.is_dir():
                continue
            for file_path in FlextInfraUtilitiesIteration.iter_directory_python_files(
                root,
            ):
                if file_path.name in target_spec.file_names:
                    candidates.add(file_path)
                    continue
                if target_spec.package_directory in file_path.parts:
                    candidates.add(file_path)
        return sorted(candidates)

    @staticmethod
    def _module_path(*, file_path: Path, project_root: Path) -> str:
        rel = file_path.relative_to(project_root)
        parts = [part for part in rel.with_suffix("").parts if part != "src"]
        return ".".join(parts)

    @staticmethod
    def _is_final_annotation(*, annotation: ast.expr) -> bool:
        final_name = c.Infra.FINAL_ANNOTATION_NAME
        if isinstance(annotation, ast.Name):
            return annotation.id == final_name
        if isinstance(annotation, ast.Attribute):
            return annotation.attr == final_name
        if isinstance(annotation, ast.Subscript):
            base = annotation.value
            if isinstance(base, ast.Name):
                return base.id == final_name
            if isinstance(base, ast.Attribute):
                return base.attr == final_name
        return False

    @staticmethod
    def _facade_class_name(
        *,
        tree: ast.Module,
        target_spec: m.Infra.MROTargetSpec,
    ) -> str:
        from_alias = FlextInfraUtilitiesRefactorMroScan._facade_from_alias_assign(
            body=tree.body,
            target_spec=target_spec,
        )
        if from_alias:
            return from_alias
        return FlextInfraUtilitiesRefactorMroScan._facade_from_class_def(
            body=tree.body,
            target_spec=target_spec,
        )

    @staticmethod
    def _facade_from_alias_assign(
        *,
        body: Sequence[ast.stmt],
        target_spec: m.Infra.MROTargetSpec,
    ) -> str:
        """Find facade class name from ``alias = ClassName`` assignments."""
        for stmt in body:
            if not isinstance(stmt, ast.Assign):
                continue
            if len(stmt.targets) != 1:
                continue
            target = stmt.targets[0]
            if (
                not isinstance(target, ast.Name)
                or target.id != target_spec.family_alias
            ):
                continue
            if not isinstance(stmt.value, ast.Name):
                continue
            class_name = stmt.value.id
            if class_name.endswith(target_spec.class_suffix):
                return class_name
        return ""

    @staticmethod
    def _facade_from_class_def(
        *,
        body: Sequence[ast.stmt],
        target_spec: m.Infra.MROTargetSpec,
    ) -> str:
        """Find facade class name from a ClassDef with matching suffix."""
        for stmt in body:
            if isinstance(stmt, ast.ClassDef) and stmt.name.endswith(
                target_spec.class_suffix,
            ):
                return stmt.name
        return ""

    @staticmethod
    def _typing_candidate_from_statement(
        *,
        stmt: ast.stmt,
    ) -> m.Infra.MROSymbolCandidate | None:
        extracted = FlextInfraUtilitiesRefactorMroScan._extract_typing_symbol(stmt=stmt)
        if extracted is None:
            return None
        symbol, kind = extracted
        return m.Infra.MROSymbolCandidate(
            symbol=symbol,
            line=stmt.lineno,
            kind=kind,
            class_name="",
            facade_name="",
        )

    @staticmethod
    def _extract_typing_symbol(
        *,
        stmt: ast.stmt,
    ) -> t.Infra.StrPair | None:
        """Return (symbol, kind) for a typing-related statement, or None."""
        if isinstance(stmt, ast.TypeAlias):
            symbol = stmt.name.id
            if not FlextInfraUtilitiesRefactorMroScan._is_valid_type_symbol(
                symbol=symbol,
            ):
                return None
            return (symbol, "typealias")
        if isinstance(stmt, ast.AnnAssign):
            return FlextInfraUtilitiesRefactorMroScan._extract_typing_from_ann_assign(
                stmt=stmt,
            )
        if isinstance(stmt, ast.Assign):
            return FlextInfraUtilitiesRefactorMroScan._extract_typing_from_assign(
                stmt=stmt,
            )
        return None

    @staticmethod
    def _extract_typing_from_ann_assign(
        *,
        stmt: ast.AnnAssign,
    ) -> t.Infra.StrPair | None:
        """Extract (symbol, 'typealias') from a TypeAlias-annotated AnnAssign."""
        if not isinstance(stmt.target, ast.Name):
            return None
        symbol = stmt.target.id
        if not FlextInfraUtilitiesRefactorMroScan._is_valid_type_symbol(symbol=symbol):
            return None
        if not FlextInfraUtilitiesRefactorMroScan._is_type_alias_annotation(
            annotation=stmt.annotation,
        ):
            return None
        return (symbol, "typealias")

    @staticmethod
    def _extract_typing_from_assign(
        *,
        stmt: ast.Assign,
    ) -> t.Infra.StrPair | None:
        """Extract (symbol, 'typevar') from a typing factory call Assign."""
        if len(stmt.targets) != 1 or not isinstance(stmt.targets[0], ast.Name):
            return None
        symbol = stmt.targets[0].id
        if not FlextInfraUtilitiesRefactorMroScan._is_valid_type_symbol(symbol=symbol):
            return None
        if not FlextInfraUtilitiesRefactorMroScan._is_typing_factory_call(
            expr=stmt.value,
        ):
            return None
        return (symbol, "typevar")

    @staticmethod
    def _is_valid_type_symbol(*, symbol: str) -> bool:
        """Check if symbol matches the type candidate naming pattern."""
        return (
            FlextInfraUtilitiesRefactorMroScan._MRO_SCAN_TYPE_CANDIDATE_PATTERN.match(
                symbol,
            )
            is not None
        )

    @staticmethod
    def _protocol_candidate_from_statement(
        *,
        stmt: ast.stmt,
    ) -> m.Infra.MROSymbolCandidate | None:
        if not isinstance(stmt, ast.ClassDef):
            return None
        if not FlextInfraUtilitiesRefactorMroScan._has_protocol_base(
            bases=stmt.bases,
        ):
            return None
        return m.Infra.MROSymbolCandidate(
            symbol=stmt.name,
            line=stmt.lineno,
            kind="protocol",
            class_name="",
            facade_name="",
        )

    @staticmethod
    def _has_protocol_base(*, bases: Sequence[ast.expr]) -> bool:
        """Check whether any base expression refers to Protocol."""
        for base_expr in bases:
            if FlextInfraUtilitiesRefactorMroScan._is_protocol_reference(
                expr=base_expr,
            ):
                return True
        return False

    @staticmethod
    def _is_protocol_reference(*, expr: ast.expr) -> bool:
        """Check if a single base expression refers to Protocol."""
        if isinstance(expr, ast.Name):
            return expr.id == "Protocol"
        if isinstance(expr, ast.Attribute):
            return expr.attr == "Protocol"
        if isinstance(expr, ast.Subscript):
            root_expr = expr.value
            if isinstance(root_expr, ast.Name):
                return root_expr.id == "Protocol"
            if isinstance(root_expr, ast.Attribute):
                return root_expr.attr == "Protocol"
        return False

    @staticmethod
    def _is_type_alias_annotation(*, annotation: ast.expr) -> bool:
        alias_name = "TypeAlias"
        if isinstance(annotation, ast.Name):
            return annotation.id == alias_name
        if isinstance(annotation, ast.Attribute):
            return annotation.attr == alias_name
        if isinstance(annotation, ast.Subscript):
            base = annotation.value
            if isinstance(base, ast.Name):
                return base.id == alias_name
            if isinstance(base, ast.Attribute):
                return base.attr == alias_name
        return False

    @staticmethod
    def _is_typing_factory_call(*, expr: ast.expr) -> bool:
        if not isinstance(expr, ast.Call):
            return False
        func = expr.func
        if isinstance(func, ast.Name):
            return func.id in {"TypeVar", "ParamSpec", "TypeVarTuple", "NewType"}
        if isinstance(func, ast.Attribute):
            return func.attr in {"TypeVar", "ParamSpec", "TypeVarTuple", "NewType"}
        return False


__all__ = ["FlextInfraUtilitiesRefactorMroScan"]
