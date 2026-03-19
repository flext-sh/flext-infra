from __future__ import annotations

from pathlib import Path
from typing import override

from flext_infra import c, m, p
from flext_infra.refactor._models_namespace_enforcer import (
    FlextInfraNamespaceEnforcerModels as nem,
)


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
        from flext_infra.transformers.import_normalizer import (
            ImportNormalizerTransformer,
        )

        violations_cst = ImportNormalizerTransformer.detect_file(
            file_path=file_path,
            project_package=package_name,
            alias_map=c.Infra.RUNTIME_ALIAS_NAMES_BY_PACKAGE,
        )
        return [
            nem.NamespaceSourceViolation.create(
                file=str(v.file),
                line=v.line,
                alias=(
                    v.current_import.rsplit(" ", maxsplit=1)[-1]
                    if " " in v.current_import
                    else ""
                ),
                current_source=(
                    v.current_import.split(" ")[1] if " " in v.current_import else ""
                ),
                correct_source=package_name,
                current_import=v.current_import,
                suggested_import=v.suggested_import,
            )
            for v in violations_cst
            if v.violation_type == "wrong_source"
        ]

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
