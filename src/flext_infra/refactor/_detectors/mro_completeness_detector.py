from __future__ import annotations

import operator
from pathlib import Path
from typing import ClassVar, override

import libcst as cst
from libcst import metadata as cst_metadata

from flext_infra import c, m, p
from flext_infra.refactor._models_namespace_enforcer import (
    FlextInfraNamespaceEnforcerModels as nem,
)


class MROCompletenessDetector(
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
        tree = cls._parse_module(
            file_path=file_path,
            stage="mro-completeness-scan",
            parse_failures=_parse_failures,
        )
        if tree is None:
            return []
        facade_name = cls._resolve_facade_class_name(tree=tree, family=family)
        if facade_name is None:
            return []
        facade_node = cls._find_top_level_class(
            tree=tree,
            class_name=facade_name,
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
            candidates,
            key=operator.itemgetter(0),
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
    def _resolve_facade_class_name(*, tree: cst.Module, family: str) -> str | None:
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
        if len(suffix) == 0:
            return None
        for stmt in tree.body:
            if isinstance(stmt, cst.ClassDef) and stmt.name.value.endswith(suffix):
                return stmt.name.value
        return None

    @staticmethod
    def _find_top_level_class(
        *,
        tree: cst.Module,
        class_name: str,
    ) -> cst.ClassDef | None:
        for stmt in tree.body:
            if isinstance(stmt, cst.ClassDef) and stmt.name.value == class_name:
                return stmt
        return None

    @staticmethod
    def _extract_base_name(base: cst.Arg) -> str:
        value = base.value
        if isinstance(value, cst.Name):
            return value.value
        if isinstance(value, cst.Attribute):
            return MROCompletenessDetector._module_to_str(value)
        if isinstance(value, cst.Subscript):
            return MROCompletenessDetector._expr_to_base_name(value.value)
        return ""

    @staticmethod
    def _expr_to_base_name(value: cst.BaseExpression) -> str:
        if isinstance(value, cst.Name):
            return value.value
        if isinstance(value, cst.Attribute):
            return MROCompletenessDetector._module_to_str(value)
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
        tree = MROCompletenessDetector._parse_module(
            file_path=file_path,
            stage="mro-completeness-candidates",
            parse_failures=_parse_failures,
        )
        if tree is None:
            return set()
        wrapper = cst_metadata.MetadataWrapper(tree, unsafe_skip_copy=True)
        positions = wrapper.resolve(cst_metadata.PositionProvider)
        result: set[tuple[str, int]] = set()
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

    @staticmethod
    def _parse_module(
        *,
        file_path: Path,
        stage: str,
        parse_failures: list[nem.ParseFailureViolation] | None,
    ) -> cst.Module | None:
        try:
            source = file_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
            return cst.parse_module(source)
        except UnicodeDecodeError as exc:
            MROCompletenessDetector._append_parse_failure(
                parse_failures=parse_failures,
                file_path=file_path,
                stage=stage,
                error_type=type(exc).__name__,
                detail=str(exc),
            )
            return None
        except OSError as exc:
            MROCompletenessDetector._append_parse_failure(
                parse_failures=parse_failures,
                file_path=file_path,
                stage=stage,
                error_type=type(exc).__name__,
                detail=str(exc),
            )
            return None
        except cst.ParserSyntaxError as exc:
            MROCompletenessDetector._append_parse_failure(
                parse_failures=parse_failures,
                file_path=file_path,
                stage=stage,
                error_type="SyntaxError",
                detail=str(exc),
            )
            return None

    @staticmethod
    def _append_parse_failure(
        *,
        parse_failures: list[nem.ParseFailureViolation] | None,
        file_path: Path,
        stage: str,
        error_type: str,
        detail: str,
    ) -> None:
        if parse_failures is None:
            return
        parse_failures.append(
            nem.ParseFailureViolation.create(
                file=str(file_path),
                stage=stage,
                error_type=error_type,
                detail=detail,
            ),
        )

    @staticmethod
    def _module_to_str(module: cst.BaseExpression | None) -> str:
        if module is None:
            return ""
        if isinstance(module, cst.Name):
            return module.value
        if isinstance(module, cst.Attribute):
            parts: list[str] = []
            current: cst.BaseExpression | cst.Attribute = module
            while isinstance(current, cst.Attribute):
                parts.append(current.attr.value)
                current = current.value
            if isinstance(current, cst.Name):
                parts.append(current.value)
            return ".".join(reversed(parts))
        return ""
