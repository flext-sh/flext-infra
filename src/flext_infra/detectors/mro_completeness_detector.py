"""Detector for facade classes missing local MRO composition bases.

This module detects namespace facade classes that are missing bases from their
corresponding family modules, which violates the namespace composition pattern.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import operator
from collections.abc import MutableSequence, Sequence
from pathlib import Path
from typing import ClassVar, override

import libcst as cst
from libcst import metadata as cst_metadata
from pydantic import BaseModel

from flext_infra import (
    c,
    m,
    p,
    t,
    u,
)

from ._base_detector import FlextInfraScanFileMixin


class FlextInfraMROCompletenessDetector(
    FlextInfraScanFileMixin,
    p.Infra.Scanner,
):
    """Detector for facade classes missing MRO composition bases.

    Identifies namespace facade classes that lack bases from their family modules,
    ensuring complete composition of constants, types, protocols, models, and utilities.
    """

    _rule_id: ClassVar[str] = "namespace.mro_completeness"

    FAMILY_DIR_BY_ALIAS: ClassVar[t.StrMapping] = c.Infra.FAMILY_DIRECTORIES

    def __init__(
        self,
        *,
        parse_failures: MutableSequence[m.Infra.ParseFailureViolation] | None = None,
    ) -> None:
        """Initialize the FlextInfraMROCompletenessDetector scanner.

        Args:
            parse_failures: Optional list of previous parse failures to track.

        """
        super().__init__()
        self._parse_failures = parse_failures

    @override
    def _build_message(self, violation: BaseModel) -> str:
        """Format an MRO completeness violation message.

        Args:
            violation: The violation model with facade_class, missing_base, family.

        Returns:
            Human-readable message for the MRO completeness violation.

        """
        fields = violation.model_dump()
        facade_class = fields.get("facade_class", "")
        missing_base = fields.get("missing_base", "")
        family = fields.get("family", "")
        return (
            f"Facade '{facade_class}' missing base '{missing_base}' "
            f"for family '{family}'"
        )

    @override
    def _collect_violations(self, file_path: Path) -> Sequence[BaseModel]:
        """Collect MRO completeness violations for the given file.

        Args:
            file_path: Path to the Python file to scan.

        Returns:
            Sequence of MROCompletenessViolation objects found.

        """
        return type(self).scan_file_impl(
            file_path=file_path,
            _parse_failures=self._parse_failures,
        )

    @classmethod
    def detect_file(
        cls,
        *,
        file_path: Path,
        parse_failures: MutableSequence[m.Infra.ParseFailureViolation] | None = None,
    ) -> Sequence[m.Infra.MROCompletenessViolation]:
        """Detect MRO completeness violations in a file.

        Args:
            file_path: Path to the Python file to analyze.
            parse_failures: Optional list of previous parse failures.

        Returns:
            List of MROCompletenessViolation objects found in the file.

        """
        return cls.scan_file_impl(
            file_path=file_path,
            _parse_failures=parse_failures,
        )

    @classmethod
    def scan_file_impl(
        cls,
        *,
        file_path: Path,
        _parse_failures: MutableSequence[m.Infra.ParseFailureViolation] | None = None,
    ) -> Sequence[m.Infra.MROCompletenessViolation]:
        """Scan a facade file for missing local and dep-graph composition bases.

        Args:
            file_path: Path to the Python file to scan.
            _parse_failures: Optional list to track parse failures.

        Returns:
            List of MROCompletenessViolation for each missing base found.

        """
        family = c.Infra.NAMESPACE_FILE_TO_FAMILY.get(file_path.name)
        if family is None:
            return []
        if file_path.name in c.Infra.NAMESPACE_PROTECTED_FILES:
            return []
        tree = u.Infra.parse_module_cst(file_path)
        if tree is None:
            if _parse_failures is not None:
                _parse_failures.append(
                    m.Infra.ParseFailureViolation.create(
                        file=str(file_path),
                        stage="mro-completeness-scan",
                        error_type="ParseError",
                        detail=f"Failed to parse {file_path.name}",
                    ),
                )
            return []
        facade_name = cls._resolve_facade_class_name(tree=tree, family=family)
        if facade_name is None:
            return []
        facade_node = u.Infra.cst_find_toplevel_class(
            tree=tree,
            class_name=facade_name,
        )
        if facade_node is None:
            return []
        declared_bases = {
            base_name
            for base_name in (
                u.Infra.cst_extract_base_name(base.value) for base in facade_node.bases
            )
            if base_name
        }
        candidates = cls._collect_local_candidates(
            file_path=file_path,
            facade_name=facade_name,
            family=family,
            _parse_failures=_parse_failures,
        )
        # Add dep-graph-based expected parents
        project_root = u.Infra.resolve_project_root(file_path)
        if project_root is not None:
            dep_chains = u.Infra.build_expected_base_chains(
                project_root=project_root,
            )
            dep_bases = dep_chains.get(family, [])
            for dep_base in dep_bases:
                if dep_base not in declared_bases and not any(
                    name == dep_base for name, _line in candidates
                ):
                    candidates.add((dep_base, 1))
        return [
            m.Infra.MROCompletenessViolation.create(
                file=str(file_path),
                line=candidate_line,
                family=family,
                facade_class=facade_name,
                missing_base=candidate_name,
                suggestion=(
                    f"Add '{candidate_name}' to '{facade_name}' inheritance bases"
                ),
            )
            for candidate_name, candidate_line in sorted(
                candidates,
                key=operator.itemgetter(0),
            )
            if candidate_name not in declared_bases
        ]

    @staticmethod
    def _resolve_facade_class_name(*, tree: cst.Module, family: str) -> str | None:
        """Resolve the facade class name for a family.

        Args:
            tree: The CST module to analyze.
            family: The family identifier (e.g., 'c', 't', 'p', 'm', 'u').

        Returns:
            The facade class name, or None if not found.

        """
        for item in tree.body:
            if not isinstance(item, cst.SimpleStatementLine):
                continue
            for stmt in item.body:
                if not isinstance(stmt, cst.Assign):
                    continue
                if not isinstance(stmt.value, cst.Name):
                    continue
                for target in stmt.targets:
                    if (
                        isinstance(target.target, cst.Name)
                        and target.target.value == family
                    ):
                        return stmt.value.value
        suffix = c.Infra.FAMILY_SUFFIXES.get(family, "")
        if not suffix:
            return None
        for stmt in tree.body:
            if isinstance(stmt, cst.ClassDef) and stmt.name.value.endswith(suffix):
                return stmt.name.value
        return None

    @classmethod
    def _collect_local_candidates(
        cls,
        *,
        file_path: Path,
        facade_name: str,
        family: str,
        _parse_failures: MutableSequence[m.Infra.ParseFailureViolation] | None,
    ) -> t.Infra.IntPairSet:
        """Collect candidate base classes from the family module.

        Args:
            file_path: Path to the facade file.
            facade_name: Name of the facade class.
            family: The family identifier.
            _parse_failures: Optional list to track parse failures.

        Returns:
            Set of (class_name, line_number) tuples for candidate bases.

        """
        candidates: t.Infra.IntPairSet = set()
        facade_prefix = facade_name
        candidates.update(
            cls._collect_from_module(
                file_path=file_path,
                facade_prefix=facade_prefix,
                facade_name=facade_name,
                _parse_failures=_parse_failures,
            ),
        )
        family_dir_name = cls.FAMILY_DIR_BY_ALIAS.get(family, "")
        if family_dir_name:
            family_dir = file_path.parent / family_dir_name
            if family_dir.is_dir():
                for child in sorted(family_dir.glob("*.py")):
                    candidates.update(
                        cls._collect_from_module(
                            file_path=child,
                            facade_prefix=facade_prefix,
                            facade_name=facade_name,
                            _parse_failures=_parse_failures,
                        ),
                    )
            family_file = file_path.parent / f"{family_dir_name}.py"
            if family_file.is_file():
                candidates.update(
                    cls._collect_from_module(
                        file_path=family_file,
                        facade_prefix=facade_prefix,
                        facade_name=facade_name,
                        _parse_failures=_parse_failures,
                    ),
                )
        return candidates

    @staticmethod
    def _collect_from_module(
        *,
        file_path: Path,
        facade_prefix: str,
        facade_name: str,
        _parse_failures: MutableSequence[m.Infra.ParseFailureViolation] | None,
    ) -> t.Infra.IntPairSet:
        tree = u.Infra.parse_module_cst(file_path)
        if tree is None:
            if _parse_failures is not None:
                _parse_failures.append(
                    m.Infra.ParseFailureViolation.create(
                        file=str(file_path),
                        stage="mro-completeness-candidates",
                        error_type="ParseError",
                        detail=f"Failed to parse {file_path.name}",
                    ),
                )
            return set()
        wrapper = cst_metadata.MetadataWrapper(tree, unsafe_skip_copy=True)
        positions = wrapper.resolve(cst_metadata.PositionProvider)
        result: t.Infra.IntPairSet = set()
        for stmt in tree.body:
            if not isinstance(stmt, cst.ClassDef):
                continue
            class_name = stmt.name.value
            if class_name == facade_name:
                continue
            if class_name.startswith("_"):
                continue
            if not class_name.startswith(facade_prefix):
                continue
            position = positions.get(stmt)
            line = position.start.line if position is not None else 0
            result.add((class_name, line))
        return result


__all__ = ["FlextInfraMROCompletenessDetector"]
