"""MRO migration scanner utilities for the MRO utility chain.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import re
from collections.abc import MutableSequence, Sequence
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
    def mro_scan_workspace(
        *,
        workspace_root: Path,
        target: str,
    ) -> tuple[Sequence[m.Infra.MROScanReport], int]:
        """Scan workspace and collect migration reports for a target family."""
        if target not in c.Infra.MRO_TARGETS:
            return ([], 0)
        results: MutableSequence[m.Infra.MROScanReport] = []
        scanned = 0
        target_specs = FlextInfraUtilitiesRefactorMroScan._mro_scan_target_specs(
            target=target,
        )
        for project_root in FlextInfraUtilitiesRefactorMroScan._mro_scan_project_roots(
            workspace_root=workspace_root,
        ):
            for target_spec in target_specs:
                for (
                    file_path
                ) in FlextInfraUtilitiesRefactorMroScan._mro_scan_iter_target_files(
                    project_root=project_root,
                    target_spec=target_spec,
                ):
                    scanned += 1
                    result = FlextInfraUtilitiesRefactorMroScan.mro_scan_file(
                        file_path=file_path,
                        project_root=project_root,
                        target_spec=target_spec,
                    )
                    if result is None or not result.candidates:
                        continue
                    results.append(result)
        return (results, scanned)

    @staticmethod
    def mro_scan_file(
        *,
        file_path: Path,
        project_root: Path,
        target_spec: m.Infra.MROTargetSpec,
    ) -> m.Infra.MROScanReport | None:
        """Scan one file and return migration candidates when found."""
        tree = FlextInfraUtilitiesParsing.parse_module_ast(file_path)
        if tree is None:
            return None
        constants_class = (
            FlextInfraUtilitiesRefactorMroScan._mro_scan_facade_class_name(
                tree=tree,
                target_spec=target_spec,
            )
        )
        if not constants_class:
            return None
        module = FlextInfraUtilitiesRefactorMroScan._mro_scan_module_path(
            file_path=file_path,
            project_root=project_root,
        )
        candidates: MutableSequence[m.Infra.MROSymbolCandidate] = []
        for stmt in tree.body:
            candidate = (
                FlextInfraUtilitiesRefactorMroScan._mro_scan_candidate_from_statement(
                    stmt=stmt,
                    target_spec=target_spec,
                )
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
    def _mro_scan_candidate_from_statement(
        *,
        stmt: ast.stmt,
        target_spec: m.Infra.MROTargetSpec,
    ) -> m.Infra.MROSymbolCandidate | None:
        if target_spec.family_alias == "t":
            return FlextInfraUtilitiesRefactorMroScan._mro_scan_typing_candidate_from_statement(
                stmt=stmt,
            )
        if target_spec.family_alias == "p":
            return FlextInfraUtilitiesRefactorMroScan._mro_scan_protocol_candidate_from_statement(
                stmt=stmt,
            )
        if isinstance(stmt, ast.AnnAssign):
            if not isinstance(stmt.target, ast.Name):
                return None
            if not FlextInfraUtilitiesRefactorMroScan._MRO_SCAN_CONSTANT_PATTERN.match(
                stmt.target.id,
            ):
                return None
            if not FlextInfraUtilitiesRefactorMroScan._mro_scan_is_final_annotation(
                annotation=stmt.annotation,
            ):
                return None
            return m.Infra.MROSymbolCandidate(
                symbol=stmt.target.id,
                line=stmt.lineno,
                kind="constant",
                class_name="",
                facade_name="",
            )
        if isinstance(stmt, ast.Assign):
            if len(stmt.targets) != 1:
                return None
            target = stmt.targets[0]
            if not isinstance(target, ast.Name):
                return None
            if not FlextInfraUtilitiesRefactorMroScan._MRO_SCAN_CONSTANT_PATTERN.match(
                target.id,
            ):
                return None
            return m.Infra.MROSymbolCandidate(
                symbol=target.id,
                line=stmt.lineno,
                kind="constant",
                class_name="",
                facade_name="",
            )
        return None

    @staticmethod
    def _mro_scan_project_roots(*, workspace_root: Path) -> Sequence[Path]:
        return FlextInfraUtilitiesIteration.discover_project_roots(
            workspace_root=workspace_root,
        )

    @staticmethod
    def _mro_scan_target_specs(
        *,
        target: str,
    ) -> tuple[m.Infra.MROTargetSpec, ...]:
        constants_spec = m.Infra.MROTargetSpec(
            family_alias="c",
            file_names=c.Infra.MRO_CONSTANTS_FILE_NAMES,
            package_directory=c.Infra.MRO_CONSTANTS_DIRECTORY,
            class_suffix=c.Infra.CONSTANTS_CLASS_SUFFIX,
        )
        typings_spec = m.Infra.MROTargetSpec(
            family_alias="t",
            file_names=c.Infra.MRO_TYPINGS_FILE_NAMES,
            package_directory=c.Infra.MRO_TYPINGS_DIRECTORY,
            class_suffix="Types",
        )
        protocols_spec = m.Infra.MROTargetSpec(
            family_alias="p",
            file_names=c.Infra.MRO_PROTOCOLS_FILE_NAMES,
            package_directory=c.Infra.MRO_PROTOCOLS_DIRECTORY,
            class_suffix="Protocols",
        )
        models_spec = m.Infra.MROTargetSpec(
            family_alias="m",
            file_names=c.Infra.MRO_MODELS_FILE_NAMES,
            package_directory=c.Infra.MRO_MODELS_DIRECTORY,
            class_suffix="Models",
        )
        utilities_spec = m.Infra.MROTargetSpec(
            family_alias="u",
            file_names=c.Infra.MRO_UTILITIES_FILE_NAMES,
            package_directory=c.Infra.MRO_UTILITIES_DIRECTORY,
            class_suffix="Utilities",
        )
        if target == "constants":
            return (constants_spec,)
        if target == "typings":
            return (typings_spec,)
        if target == "protocols":
            return (protocols_spec,)
        if target == "models":
            return (models_spec,)
        if target == "utilities":
            return (utilities_spec,)
        return (
            constants_spec,
            typings_spec,
            protocols_spec,
            models_spec,
            utilities_spec,
        )

    @staticmethod
    def _mro_scan_iter_target_files(
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
    def _mro_scan_module_path(*, file_path: Path, project_root: Path) -> str:
        rel = file_path.relative_to(project_root)
        parts = [part for part in rel.with_suffix("").parts if part != "src"]
        return ".".join(parts)

    @staticmethod
    def _mro_scan_is_final_annotation(*, annotation: ast.expr) -> bool:
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
    def _mro_scan_facade_class_name(
        *,
        tree: ast.Module,
        target_spec: m.Infra.MROTargetSpec,
    ) -> str:
        for stmt in tree.body:
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
        for stmt in tree.body:
            if not isinstance(stmt, ast.ClassDef):
                continue
            if stmt.name.endswith(target_spec.class_suffix):
                return stmt.name
        return ""

    @staticmethod
    def _mro_scan_typing_candidate_from_statement(
        *,
        stmt: ast.stmt,
    ) -> m.Infra.MROSymbolCandidate | None:
        if isinstance(stmt, ast.TypeAlias):
            symbol = stmt.name.id
            if (
                FlextInfraUtilitiesRefactorMroScan._MRO_SCAN_TYPE_CANDIDATE_PATTERN.match(
                    symbol,
                )
                is None
            ):
                return None
            return m.Infra.MROSymbolCandidate(
                symbol=symbol,
                line=stmt.lineno,
                kind="typealias",
                class_name="",
                facade_name="",
            )
        if isinstance(stmt, ast.AnnAssign):
            if not isinstance(stmt.target, ast.Name):
                return None
            symbol = stmt.target.id
            if (
                FlextInfraUtilitiesRefactorMroScan._MRO_SCAN_TYPE_CANDIDATE_PATTERN.match(
                    symbol,
                )
                is None
            ):
                return None
            if not FlextInfraUtilitiesRefactorMroScan._mro_scan_is_type_alias_annotation(
                annotation=stmt.annotation,
            ):
                return None
            return m.Infra.MROSymbolCandidate(
                symbol=symbol,
                line=stmt.lineno,
                kind="typealias",
                class_name="",
                facade_name="",
            )
        if isinstance(stmt, ast.Assign):
            if len(stmt.targets) != 1 or not isinstance(stmt.targets[0], ast.Name):
                return None
            symbol = stmt.targets[0].id
            if (
                FlextInfraUtilitiesRefactorMroScan._MRO_SCAN_TYPE_CANDIDATE_PATTERN.match(
                    symbol,
                )
                is None
            ):
                return None
            if not FlextInfraUtilitiesRefactorMroScan._mro_scan_is_typing_factory_call(
                expr=stmt.value,
            ):
                return None
            return m.Infra.MROSymbolCandidate(
                symbol=symbol,
                line=stmt.lineno,
                kind="typevar",
                class_name="",
                facade_name="",
            )
        return None

    @staticmethod
    def _mro_scan_protocol_candidate_from_statement(
        *,
        stmt: ast.stmt,
    ) -> m.Infra.MROSymbolCandidate | None:
        if not isinstance(stmt, ast.ClassDef):
            return None
        has_protocol_base = False
        for base_expr in stmt.bases:
            if isinstance(base_expr, ast.Name) and base_expr.id == "Protocol":
                has_protocol_base = True
                break
            if isinstance(base_expr, ast.Attribute) and base_expr.attr == "Protocol":
                has_protocol_base = True
                break
            if isinstance(base_expr, ast.Subscript):
                root_expr = base_expr.value
                if isinstance(root_expr, ast.Name) and root_expr.id == "Protocol":
                    has_protocol_base = True
                    break
                if (
                    isinstance(root_expr, ast.Attribute)
                    and root_expr.attr == "Protocol"
                ):
                    has_protocol_base = True
                    break
        if not has_protocol_base:
            return None
        return m.Infra.MROSymbolCandidate(
            symbol=stmt.name,
            line=stmt.lineno,
            kind="protocol",
            class_name="",
            facade_name="",
        )

    @staticmethod
    def _mro_scan_is_type_alias_annotation(*, annotation: ast.expr) -> bool:
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
    def _mro_scan_is_typing_factory_call(*, expr: ast.expr) -> bool:
        if not isinstance(expr, ast.Call):
            return False
        func = expr.func
        if isinstance(func, ast.Name):
            return func.id in {"TypeVar", "ParamSpec", "TypeVarTuple", "NewType"}
        if isinstance(func, ast.Attribute):
            return func.attr in {"TypeVar", "ParamSpec", "TypeVarTuple", "NewType"}
        return False


__all__ = ["FlextInfraUtilitiesRefactorMroScan"]
