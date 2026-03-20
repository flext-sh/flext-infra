from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import override

import libcst as cst
from libcst.metadata import CodeRange, MetadataWrapper, PositionProvider

from flext_infra import c, m, p
from flext_infra.refactor._models_namespace_enforcer import (
    FlextInfraNamespaceEnforcerModels as nem,
)

from .namespace_facade_scanner import NamespaceFacadeScanner


class LooseObjectDetector(p.Infra.Scanner):
    """Detect loose top-level objects that should be inside namespace classes."""

    ALLOWED_TOP_LEVEL = frozenset({"__all__", "__version__", "__version_info__"})

    def __init__(
        self,
        *,
        project_name: str,
        parse_failures: list[nem.ParseFailureViolation] | None = None,
    ) -> None:
        """Initialize scanner with project configuration."""
        super().__init__()
        self._project_name = project_name
        self._parse_failures = parse_failures

    @override
    def scan_file(self, *, file_path: Path) -> m.Infra.ScanResult:
        """Scan a file and return protocol-standardized scan output."""
        violations = type(self).scan_file_impl(
            file_path=file_path,
            project_name=self._project_name,
            _parse_failures=self._parse_failures,
        )
        return m.Infra.ScanResult(
            file_path=file_path,
            violations=[
                m.Infra.ScanViolation(
                    line=violation.line,
                    message=(
                        f"Loose {violation.kind} '{violation.name}' outside namespace"
                    ),
                    severity="error",
                    rule_id="namespace.loose_object",
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
        project_name: str,
        parse_failures: list[nem.ParseFailureViolation] | None = None,
    ) -> list[nem.LooseObjectViolation]:
        """Scan a file and return typed namespace violations."""
        return cls.scan_file_impl(
            file_path=file_path,
            project_name=project_name,
            _parse_failures=parse_failures,
        )

    @classmethod
    def scan_file_impl(
        cls,
        *,
        file_path: Path,
        project_name: str,
        _parse_failures: list[nem.ParseFailureViolation] | None = None,
    ) -> list[nem.LooseObjectViolation]:
        """Scan a file for loose top-level objects outside namespace classes."""
        _ = _parse_failures
        if file_path.name in c.Infra.NAMESPACE_PROTECTED_FILES:
            return []
        if file_path.name in c.Infra.NAMESPACE_SETTINGS_FILE_NAMES:
            return []
        try:
            tree = cst.parse_module(file_path.read_text(encoding="utf-8"))
        except cst.ParserSyntaxError:
            return []
        wrapper = MetadataWrapper(tree)
        module = wrapper.module
        positions = wrapper.resolve(PositionProvider)
        namespace_classes = cls._find_namespace_classes(tree=module)
        class_stem = NamespaceFacadeScanner.project_class_stem(
            project_name=project_name
        )
        violations: list[nem.LooseObjectViolation] = []
        for stmt in module.body:
            violation = cls._check_statement(
                stmt=stmt,
                namespace_classes=namespace_classes,
                file_path=file_path,
                class_stem=class_stem,
                positions=positions,
            )
            if violation is not None:
                violations.append(violation)
        return violations

    @classmethod
    def _check_statement(
        cls,
        *,
        stmt: cst.BaseStatement,
        namespace_classes: set[str],
        file_path: Path,
        class_stem: str,
        positions: Mapping[cst.CSTNode, CodeRange],
    ) -> nem.LooseObjectViolation | None:
        if isinstance(stmt, cst.SimpleStatementLine):
            for small_stmt in stmt.body:
                violation = cls._check_small_statement(
                    stmt=small_stmt,
                    file_path=file_path,
                    class_stem=class_stem,
                    positions=positions,
                )
                if violation is not None:
                    return violation
            return None
        if isinstance(stmt, cst.If):
            return None
        if isinstance(stmt, cst.ClassDef):
            if stmt.name.value in namespace_classes:
                return None
            return None
        if isinstance(stmt, cst.FunctionDef):
            name = stmt.name.value
            if name.startswith("__") and name.endswith("__"):
                return None
            if name.startswith("_"):
                return None
            return nem.LooseObjectViolation.create(
                file=str(file_path),
                line=cls._line_for(node=stmt, positions=positions),
                name=name,
                kind="function",
                suggestion=f"{class_stem}Utilities",
            )
        return None

    @classmethod
    def _check_small_statement(
        cls,
        *,
        stmt: cst.BaseSmallStatement,
        file_path: Path,
        class_stem: str,
        positions: Mapping[cst.CSTNode, CodeRange],
    ) -> nem.LooseObjectViolation | None:
        if isinstance(stmt, (cst.Import, cst.ImportFrom)):
            return None
        if isinstance(stmt, cst.Expr) and isinstance(
            stmt.value,
            (cst.SimpleString, cst.ConcatenatedString, cst.Integer),
        ):
            return None
        if isinstance(stmt, cst.AnnAssign) and isinstance(stmt.target, cst.Name):
            name = stmt.target.value
            if name in cls.ALLOWED_TOP_LEVEL:
                return None
            if name.startswith("_"):
                return None
            if c.Infra.NAMESPACE_CONSTANT_PATTERN.match(name):
                return nem.LooseObjectViolation.create(
                    file=str(file_path),
                    line=cls._line_for(node=stmt, positions=positions),
                    name=name,
                    kind="constant",
                    suggestion=f"{class_stem}Constants",
                )
        if isinstance(stmt, cst.Assign):
            for assignment_target in stmt.targets:
                target = assignment_target.target
                if not isinstance(target, cst.Name):
                    continue
                name = target.value
                if name in cls.ALLOWED_TOP_LEVEL:
                    return None
                if len(name) <= c.Infra.NAMESPACE_MIN_ALIAS_LENGTH:
                    return None
                if name.startswith("_"):
                    return None
                if c.Infra.NAMESPACE_CONSTANT_PATTERN.match(name):
                    return nem.LooseObjectViolation.create(
                        file=str(file_path),
                        line=cls._line_for(node=stmt, positions=positions),
                        name=name,
                        kind="constant",
                        suggestion=f"{class_stem}Constants",
                    )
        name = cls._type_alias_name(stmt=stmt)
        if name and name not in cls.ALLOWED_TOP_LEVEL:
            return nem.LooseObjectViolation.create(
                file=str(file_path),
                line=cls._line_for(node=stmt, positions=positions),
                name=name,
                kind="typealias",
                suggestion=f"{class_stem}Types",
            )
        return None

    @staticmethod
    def _type_alias_name(*, stmt: cst.BaseSmallStatement) -> str:
        if hasattr(cst, "TypeAlias") and isinstance(stmt, cst.TypeAlias):
            return stmt.name.value
        if (
            isinstance(stmt, cst.AnnAssign)
            and isinstance(stmt.target, cst.Name)
            and LooseObjectDetector._module_to_str(stmt.annotation.annotation)
            == "TypeAlias"
        ):
            return stmt.target.value
        return ""

    @staticmethod
    def _find_namespace_classes(*, tree: cst.Module) -> set[str]:
        classes: set[str] = set()
        for stmt in tree.body:
            LooseObjectDetector._collect_namespace_classes(node=stmt, classes=classes)
        return classes

    @staticmethod
    def _collect_namespace_classes(*, node: cst.CSTNode, classes: set[str]) -> None:
        if isinstance(node, cst.ClassDef):
            for suffix in c.Infra.FAMILY_SUFFIXES.values():
                if node.name.value.endswith(suffix):
                    classes.add(node.name.value)
                    break
        for child in node.children:
            LooseObjectDetector._collect_namespace_classes(node=child, classes=classes)

    @staticmethod
    def _module_to_str(module: cst.BaseExpression | None) -> str:
        if module is None:
            return ""
        if isinstance(module, cst.Name):
            return module.value
        if isinstance(module, cst.Attribute):
            parts: list[str] = []
            current: cst.BaseExpression = module
            while isinstance(current, cst.Attribute):
                parts.append(current.attr.value)
                current = current.value
            if isinstance(current, cst.Name):
                parts.append(current.value)
            return ".".join(reversed(parts))
        return ""

    @staticmethod
    def _line_for(
        *,
        node: cst.CSTNode,
        positions: Mapping[cst.CSTNode, CodeRange],
    ) -> int:
        code_range = positions.get(node)
        if code_range is None:
            return 1
        return code_range.start.line
