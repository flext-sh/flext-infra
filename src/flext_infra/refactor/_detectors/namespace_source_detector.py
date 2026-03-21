from __future__ import annotations

from pathlib import Path
from typing import Protocol, override, runtime_checkable

from flext_infra.constants import c
from flext_infra.models import m
from flext_infra.protocols import p
from flext_infra.refactor._models_namespace_enforcer import (
    FlextInfraNamespaceEnforcerModels as nem,
)


@runtime_checkable
class _ImportNormalizerTransformerLike(Protocol):
    @staticmethod
    def detect_file(
        *,
        file_path: Path,
        project_package: str,
        alias_map: dict[str, tuple[str, ...]] | None = None,
    ) -> list[object]: ...


class NamespaceSourceDetector(p.Infra.Scanner):
    """Detect alias imports from wrong source packages."""

    def __init__(
        self,
        *,
        project_name: str,
        project_root: Path,
        parse_failures: list[nem.ParseFailureViolation] | None = None,
    ) -> None:
        """Initialize scanner with project configuration."""
        super().__init__()
        self._project_name = project_name
        self._project_root = project_root
        self._parse_failures = parse_failures

    @override
    def scan_file(self, *, file_path: Path) -> m.Infra.ScanResult:
        """Scan a file and return protocol-standardized scan output."""
        violations = type(self).scan_file_impl(
            file_path=file_path,
            project_name=self._project_name,
            project_root=self._project_root,
            _parse_failures=self._parse_failures,
        )
        return m.Infra.ScanResult(
            file_path=file_path,
            violations=[
                m.Infra.ScanViolation(
                    line=violation.line,
                    message=(
                        f"Wrong source for alias '{violation.alias}': "
                        f"'{violation.current_source}' -> '{violation.correct_source}'"
                    ),
                    severity="error",
                    rule_id="namespace.source_alias",
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
        project_root: Path,
        parse_failures: list[nem.ParseFailureViolation] | None = None,
    ) -> list[nem.NamespaceSourceViolation]:
        """Scan a file and return typed namespace violations."""
        return cls.scan_file_impl(
            file_path=file_path,
            project_name=project_name,
            project_root=project_root,
            _parse_failures=parse_failures,
        )

    @classmethod
    def scan_file_impl(
        cls,
        *,
        file_path: Path,
        project_name: str,
        project_root: Path,
        _parse_failures: list[nem.ParseFailureViolation] | None = None,
    ) -> list[nem.NamespaceSourceViolation]:
        """Scan a file for wrong-source alias imports."""
        _ = project_name
        _ = _parse_failures
        package_name = cls._discover_project_package_name(project_root=project_root)
        if len(package_name) == 0:
            return []
        transformers_module = __import__(
            "flext_infra.transformers",
            fromlist=["ImportNormalizerTransformer"],
        )
        transformer_obj = getattr(
            transformers_module,
            "ImportNormalizerTransformer",
            None,
        )
        if not isinstance(transformer_obj, _ImportNormalizerTransformerLike):
            return []
        violations_cst = transformer_obj.detect_file(
            file_path=file_path,
            project_package=package_name,
            alias_map=None,
        )
        violations: list[nem.NamespaceSourceViolation] = []
        for raw in violations_cst:
            violation_type = getattr(raw, "violation_type", "")
            file_value = getattr(raw, "file", "")
            line_value = getattr(raw, "line", 0)
            current_import = getattr(raw, "current_import", "")
            suggested_import = getattr(raw, "suggested_import", "")
            if violation_type != "wrong_source":
                continue
            if not isinstance(file_value, str):
                continue
            if not isinstance(line_value, int):
                continue
            if not isinstance(current_import, str):
                continue
            if not isinstance(suggested_import, str):
                continue
            alias = (
                current_import.rsplit(" ", maxsplit=1)[-1]
                if " " in current_import
                else ""
            )
            current_source = (
                current_import.split(" ")[1] if " " in current_import else ""
            )
            violations.append(
                nem.NamespaceSourceViolation.create(
                    file=file_value,
                    line=line_value,
                    alias=alias,
                    current_source=current_source,
                    correct_source=package_name,
                    current_import=current_import,
                    suggested_import=suggested_import,
                ),
            )
        return violations

    @staticmethod
    def _discover_project_package_name(*, project_root: Path) -> str:
        src_dir = project_root / c.Infra.Paths.DEFAULT_SRC_DIR
        if not src_dir.is_dir():
            return ""
        package_dirs = [
            entry
            for entry in sorted(src_dir.iterdir(), key=lambda item: item.name)
            if entry.is_dir() and (entry / "__init__.py").is_file()
        ]
        if len(package_dirs) == 0:
            return ""
        return package_dirs[0].name

    @classmethod
    def discover_project_package_name(cls, *, project_root: Path) -> str:
        return cls._discover_project_package_name(project_root=project_root)
