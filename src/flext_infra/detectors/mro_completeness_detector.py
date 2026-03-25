"""Detector for facade classes missing local MRO composition bases.

This module detects namespace facade classes that are missing bases from their
corresponding family modules, which violates the namespace composition pattern.

Uses rope semantic analysis exclusively — no CST/AST fallbacks.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import operator
import re
from collections.abc import MutableSequence, Sequence
from pathlib import Path
from typing import ClassVar, override

from pydantic import BaseModel

from flext_infra import (
    c,
    m,
    p,
    t,
    u,
)

from ._base_detector import FlextInfraScanFileMixin

_ALIAS_ASSIGNMENT_RE = re.compile(r"^(\w)\s*=\s*(\w+)", re.MULTILINE)


class FlextInfraMROCompletenessDetector(
    FlextInfraScanFileMixin,
    p.Infra.Scanner,
):
    """Detector for facade classes missing MRO composition bases.

    Identifies namespace facade classes that lack bases from their family modules,
    ensuring complete composition of constants, types, protocols, models, and utilities.

    All analysis uses rope semantic APIs via u.Infra.* — no CST dependencies.
    """

    _rule_id: ClassVar[str] = "namespace.mro_completeness"

    FAMILY_DIR_BY_ALIAS: ClassVar[t.StrMapping] = c.Infra.FAMILY_DIRECTORIES

    def __init__(
        self,
        *,
        rope_project: t.Infra.RopeProject,
        parse_failures: MutableSequence[m.Infra.ParseFailureViolation] | None = None,
    ) -> None:
        """Initialize the detector.

        Args:
            rope_project: Rope Project for semantic class resolution.
            parse_failures: Optional list to track parse failures.

        """
        super().__init__()
        self._rope_project = rope_project
        self._parse_failures = parse_failures

    @override
    def _build_message(self, violation: BaseModel) -> str:
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
        return type(self).scan_file_impl(
            file_path=file_path,
            rope_project=self._rope_project,
            _parse_failures=self._parse_failures,
        )

    @classmethod
    def detect_file(
        cls,
        *,
        file_path: Path,
        rope_project: t.Infra.RopeProject,
        parse_failures: MutableSequence[m.Infra.ParseFailureViolation] | None = None,
    ) -> Sequence[m.Infra.MROCompletenessViolation]:
        """Detect MRO completeness violations in a file."""
        return cls.scan_file_impl(
            file_path=file_path,
            rope_project=rope_project,
            _parse_failures=parse_failures,
        )

    @classmethod
    def scan_file_impl(
        cls,
        *,
        file_path: Path,
        rope_project: t.Infra.RopeProject,
        _parse_failures: MutableSequence[m.Infra.ParseFailureViolation] | None = None,
    ) -> Sequence[m.Infra.MROCompletenessViolation]:
        """Scan a facade file for missing local and dep-graph composition bases."""
        family = c.Infra.NAMESPACE_FILE_TO_FAMILY.get(file_path.name)
        if family is None:
            return []
        if file_path.name in c.Infra.NAMESPACE_PROTECTED_FILES:
            return []
        resource = u.Infra.get_resource_from_path(rope_project, file_path)
        if resource is None:
            if _parse_failures is not None:
                _parse_failures.append(
                    m.Infra.ParseFailureViolation.create(
                        file=str(file_path),
                        stage="mro-completeness-scan",
                        error_type="ResourceNotFound",
                        detail=f"Rope cannot resolve {file_path.name}",
                    ),
                )
            return []
        facade_name = cls._resolve_facade_class_name(
            rope_project=rope_project,
            resource=resource,
            family=family,
        )
        if facade_name is None:
            return []
        declared_bases = set(
            u.Infra.get_class_bases(rope_project, resource, facade_name),
        )
        candidates = cls._collect_local_candidates(
            file_path=file_path,
            facade_name=facade_name,
            family=family,
            rope_project=rope_project,
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
    def _resolve_facade_class_name(
        *,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        family: str,
    ) -> str | None:
        """Resolve the facade class name for a family from a module.

        Strategy:
        1. Find alias assignment ``family = ClassName`` via source scan.
        2. Fallback: find class ending with the family suffix via rope.
        """
        source = resource.read()
        for match in _ALIAS_ASSIGNMENT_RE.finditer(source):
            if match.group(1) == family:
                return match.group(2)
        suffix = c.Infra.FAMILY_SUFFIXES.get(family, "")
        if not suffix:
            return None
        for class_name in u.Infra.get_module_classes(rope_project, resource):
            if class_name.endswith(suffix):
                return class_name
        return None

    @classmethod
    def _collect_local_candidates(
        cls,
        *,
        file_path: Path,
        facade_name: str,
        family: str,
        rope_project: t.Infra.RopeProject,
    ) -> t.Infra.IntPairSet:
        """Collect candidate base classes from the family module and subdirectories."""
        candidates: t.Infra.IntPairSet = set()
        candidates.update(
            cls._collect_from_module(
                file_path=file_path,
                facade_prefix=facade_name,
                facade_name=facade_name,
                rope_project=rope_project,
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
                            facade_prefix=facade_name,
                            facade_name=facade_name,
                            rope_project=rope_project,
                        ),
                    )
            family_file = file_path.parent / f"{family_dir_name}.py"
            if family_file.is_file():
                candidates.update(
                    cls._collect_from_module(
                        file_path=family_file,
                        facade_prefix=facade_name,
                        facade_name=facade_name,
                        rope_project=rope_project,
                    ),
                )
        return candidates

    @staticmethod
    def _collect_from_module(
        *,
        file_path: Path,
        facade_prefix: str,
        facade_name: str,
        rope_project: t.Infra.RopeProject,
    ) -> t.Infra.IntPairSet:
        """Collect class candidates from a single module via rope semantic analysis."""
        resource = u.Infra.get_resource_from_path(rope_project, file_path)
        if resource is None:
            return set()
        class_lines = u.Infra.get_module_class_lines(rope_project, resource)
        return {
            (name, line)
            for name, line in class_lines.items()
            if name != facade_name
            and not name.startswith("_")
            and name.startswith(facade_prefix)
        }


__all__ = ["FlextInfraMROCompletenessDetector"]
