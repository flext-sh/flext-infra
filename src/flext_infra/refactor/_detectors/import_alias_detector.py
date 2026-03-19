from __future__ import annotations

from pathlib import Path
from typing import ClassVar, override

from flext_infra import c, m, p
from flext_infra.refactor._detectors.module_loader import (
    DetectorScanResultBuilder,
)
from flext_infra.refactor._models_namespace_enforcer import (
    FlextInfraNamespaceEnforcerModels as nem,
)


class ImportAliasDetector(p.Infra.Scanner):
    """Detect deep import paths that should use top-level aliases."""

    RUNTIME_ALIAS_NAMES_BY_PACKAGE: ClassVar[dict[str, tuple[str, ...]]] = {
        "flext_core": ("c", "m", "r", "t", "u", "p", "d", "e", "h", "s", "x"),
        "flext_infra": ("c", "m", "t", "u", "p"),
    }

    @classmethod
    def _suggest_alias_import(cls, *, package: str, imported_names: list[str]) -> str:
        allowed = cls.RUNTIME_ALIAS_NAMES_BY_PACKAGE.get(package, ())
        allowed_set = set(allowed)
        unique_names = {name for name in imported_names if name in allowed_set}
        ordered_names = [name for name in allowed if name in unique_names]
        return f"from {package} import {', '.join(ordered_names)}"

    @staticmethod
    def parse_imported_names(import_clause: str) -> list[str]:
        no_comment = import_clause.split("#", maxsplit=1)[0].strip()
        normalized_clause = no_comment.replace("(", "").replace(")", "")
        names: list[str] = []
        for part in normalized_clause.split(","):
            token_text = part.strip()
            if len(token_text) == 0:
                continue
            if " as " in token_text:
                token_text = token_text.split(" as ", maxsplit=1)[0].strip()
            names.append(token_text)
        return names

    @classmethod
    def _discover_package(cls, file_path: Path) -> str:
        src_dir_name = c.Infra.Paths.DEFAULT_SRC_DIR
        parts = file_path.resolve().parts
        try:
            src_index = parts.index(src_dir_name)
        except ValueError:
            return ""
        package_index = src_index + 1
        if package_index >= len(parts):
            return ""
        return parts[package_index]

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
        return DetectorScanResultBuilder.build(
            file_path=file_path,
            detector_name=self.__class__.__name__,
            rule_id="namespace.import_alias",
            violations=violations,
            message_builder=lambda violation: (
                f"Deep import '{violation.current_import}' should use "
                f"'{violation.suggested_import}'"
            ),
        )

    @classmethod
    def detect_file(
        cls,
        *,
        file_path: Path,
        parse_failures: list[nem.ParseFailureViolation] | None = None,
    ) -> list[nem.ImportAliasViolation]:
        """Scan a file and return typed namespace violations."""
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
    ) -> list[nem.ImportAliasViolation]:
        """Scan a file for deep import paths that should use aliases."""
        _ = _parse_failures
        from flext_infra.transformers.import_normalizer import (
            ImportNormalizerTransformer,
        )

        violations_cst = ImportNormalizerTransformer.detect_file(
            file_path=file_path,
            project_package=cls._discover_package(file_path),
            alias_map=c.Infra.RUNTIME_ALIAS_NAMES_BY_PACKAGE,
        )
        return [
            nem.ImportAliasViolation.create(
                file=str(v.file),
                line=v.line,
                current_import=v.current_import,
                suggested_import=v.suggested_import,
            )
            for v in violations_cst
            if v.violation_type == "deep"
        ]
