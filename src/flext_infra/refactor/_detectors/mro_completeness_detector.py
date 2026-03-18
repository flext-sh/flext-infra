from __future__ import annotations

import ast
import operator
from pathlib import Path
from typing import ClassVar, override

from flext_infra import c, m, p
from flext_infra.refactor._detectors.python_module_loader_mixin import (
    FlextInfraRefactorDetectorPythonModuleLoaderMixin,
)
from flext_infra.refactor._models_namespace_enforcer import (
    FlextInfraNamespaceEnforcerModels as nem,
)


class MROCompletenessDetector(
    FlextInfraRefactorDetectorPythonModuleLoaderMixin,
    p.Infra.Scanner,
):
    """Detect facade classes missing local MRO composition bases."""

    FAMILY_DIR_BY_ALIAS: ClassVar[dict[str, str]] = {
        "c": "_constants",
        "t": "_typings",
        "p": "_protocols",
        "m": "_models",
        "u": "_utilities",
    }

    def __init__(
        self,
        *,
        parse_failures: list[nem.ParseFailureViolation] | None = None,
    ) -> None:
        """Initialize scanner with project configuration."""
        super().__init__()
        self._parse_failures = parse_failures

    @override
    def scan_file(self, *, file_path: Path) -> m.Infra.ScanResult:
        """Scan a file and return protocol-standardized scan output."""
        violations = type(self).scan_file_impl(
            file_path=file_path,
            _parse_failures=self._parse_failures,
        )
        return m.Infra.ScanResult(
            file_path=file_path,
            violations=[
                m.Infra.ScanViolation(
                    line=violation.line,
                    message=(
                        f"Facade '{violation.facade_class}' missing base "
                        f"'{violation.missing_base}' for family '{violation.family}'"
                    ),
                    severity="error",
                    rule_id="namespace.mro_completeness",
                )
                for violation in violations
            ],
            detector_name=self.__class__.__name__,
        )

    @classmethod
    def detect_file(
        cls,
        *,
        file_path: Path,
        parse_failures: list[nem.ParseFailureViolation] | None = None,
    ) -> list[nem.MROCompletenessViolation]:
        """Scan a file and return typed MRO completeness violations."""
        return cls.scan_file_impl(
            file_path=file_path,
            _parse_failures=parse_failures,
        )

    @classmethod
    def scan_file_impl(
        cls,
        *,
        file_path: Path,
        _parse_failures: list[nem.ParseFailureViolation] | None = None,
    ) -> list[nem.MROCompletenessViolation]:
        """Scan a facade file for missing local composition bases."""
        family = c.Infra.NAMESPACE_FILE_TO_FAMILY.get(file_path.name)
        if family is None:
            return []
        if file_path.name in c.Infra.NAMESPACE_PROTECTED_FILES:
            return []
        parsed = cls._load_python_module(
            file_path,
            stage="mro-completeness-scan",
            parse_failures=_parse_failures,
        )
        if parsed is None:
            return []
        facade_name = cls._resolve_facade_class_name(tree=parsed.tree, family=family)
        if facade_name is None:
            return []
        facade_node = cls._find_top_level_class(
            tree=parsed.tree, class_name=facade_name
        )
        if facade_node is None:
            return []
        declared_bases = {
            base_name
            for base_name in (
                cls._extract_base_name(base) for base in facade_node.bases
            )
            if len(base_name) > 0
        }
        candidates = cls._collect_local_candidates(
            file_path=file_path,
            facade_name=facade_name,
            family=family,
            _parse_failures=_parse_failures,
        )
        violations: list[nem.MROCompletenessViolation] = []
        for candidate_name, candidate_line in sorted(
            candidates, key=operator.itemgetter(0)
        ):
            if candidate_name in declared_bases:
                continue
            violations.append(
                nem.MROCompletenessViolation.create(
                    file=str(file_path),
                    line=candidate_line,
                    family=family,
                    facade_class=facade_name,
                    missing_base=candidate_name,
                    suggestion=(
                        f"Add '{candidate_name}' to '{facade_name}' inheritance bases"
                    ),
                ),
            )
        return violations

    @staticmethod
    def _resolve_facade_class_name(*, tree: ast.Module, family: str) -> str | None:
        for stmt in tree.body:
            if not isinstance(stmt, ast.Assign):
                continue
            if not isinstance(stmt.value, ast.Name):
                continue
            for target in stmt.targets:
                if isinstance(target, ast.Name) and target.id == family:
                    return stmt.value.id
        suffix = c.Infra.NAMESPACE_FACADE_FAMILIES.get(family, "")
        if len(suffix) == 0:
            return None
        for stmt in tree.body:
            if isinstance(stmt, ast.ClassDef) and stmt.name.endswith(suffix):
                return stmt.name
        return None

    @staticmethod
    def _find_top_level_class(
        *, tree: ast.Module, class_name: str
    ) -> ast.ClassDef | None:
        for stmt in tree.body:
            if isinstance(stmt, ast.ClassDef) and stmt.name == class_name:
                return stmt
        return None

    @staticmethod
    def _extract_base_name(base: ast.expr) -> str:
        if isinstance(base, ast.Name):
            return base.id
        if isinstance(base, ast.Attribute):
            return base.attr
        if isinstance(base, ast.Subscript):
            return MROCompletenessDetector._extract_base_name(base.value)
        return ""

    @classmethod
    def _collect_local_candidates(
        cls,
        *,
        file_path: Path,
        facade_name: str,
        family: str,
        _parse_failures: list[nem.ParseFailureViolation] | None,
    ) -> set[tuple[str, int]]:
        candidates: set[tuple[str, int]] = set()
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
        if len(family_dir_name) > 0:
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
        _parse_failures: list[nem.ParseFailureViolation] | None,
    ) -> set[tuple[str, int]]:
        parsed = MROCompletenessDetector._load_python_module(
            file_path,
            stage="mro-completeness-candidates",
            parse_failures=_parse_failures,
        )
        if parsed is None:
            return set()
        result: set[tuple[str, int]] = set()
        for stmt in parsed.tree.body:
            if not isinstance(stmt, ast.ClassDef):
                continue
            if stmt.name == facade_name:
                continue
            if stmt.name.startswith("_"):
                continue
            if not stmt.name.startswith(facade_prefix):
                continue
            result.add((stmt.name, stmt.lineno))
        return result
