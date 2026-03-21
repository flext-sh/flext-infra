"""Facade for namespace dependency detectors used by refactor checks."""

from __future__ import annotations

from pathlib import Path

from flext_infra import (
    ClassPlacementDetector,
    CompatibilityAliasDetector,
    CyclicImportDetector,
    DependencyAnalyzer,
    FlextInfraNamespaceEnforcerModels as nem,
    FutureAnnotationsDetector,
    ImportAliasDetector,
    InternalImportDetector,
    LooseObjectDetector,
    ManualProtocolDetector,
    ManualTypingAliasDetector,
    MROCompletenessDetector,
    NamespaceFacadeScanner,
    NamespaceSourceDetector,
    RuntimeAliasDetector,
    c,
    m,
    u,
)


class FlextInfraRefactorDependencyAnalyzerFacade:
    @staticmethod
    def load_python_module(
        file_path: Path,
        *,
        stage: str = "scan",
        parse_failures: list[nem.ParseFailureViolation] | None = None,
    ) -> m.Infra.ParsedPythonModule | None:
        """Load and parse a Python module while recording parse failures."""
        try:
            source = file_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
        except UnicodeDecodeError as exc:
            if parse_failures is not None:
                parse_failures.append(
                    nem.ParseFailureViolation.create(
                        file=str(file_path),
                        stage=stage,
                        error_type=type(exc).__name__,
                        detail=str(exc),
                    ),
                )
            return None
        except OSError as exc:
            if parse_failures is not None:
                parse_failures.append(
                    nem.ParseFailureViolation.create(
                        file=str(file_path),
                        stage=stage,
                        error_type=type(exc).__name__,
                        detail=str(exc),
                    ),
                )
            return None
        tree = u.Infra.parse_ast_from_source(source)
        if tree is None:
            if parse_failures is not None:
                parse_failures.append(
                    nem.ParseFailureViolation.create(
                        file=str(file_path),
                        stage=stage,
                        error_type="SyntaxError",
                        detail="invalid python source",
                    ),
                )
            return None
        return m.Infra.ParsedPythonModule(source=source, tree=tree)

    NamespaceFacadeScanner = NamespaceFacadeScanner
    LooseObjectDetector = LooseObjectDetector
    ImportAliasDetector = ImportAliasDetector
    NamespaceSourceDetector = NamespaceSourceDetector
    InternalImportDetector = InternalImportDetector
    ManualProtocolDetector = ManualProtocolDetector
    ClassPlacementDetector = ClassPlacementDetector
    MROCompletenessDetector = MROCompletenessDetector
    CyclicImportDetector = CyclicImportDetector
    RuntimeAliasDetector = RuntimeAliasDetector
    FutureAnnotationsDetector = FutureAnnotationsDetector
    ManualTypingAliasDetector = ManualTypingAliasDetector
    CompatibilityAliasDetector = CompatibilityAliasDetector


__all__ = [
    "ClassPlacementDetector",
    "CompatibilityAliasDetector",
    "CyclicImportDetector",
    "DependencyAnalyzer",
    "FlextInfraRefactorDependencyAnalyzerFacade",
    "FutureAnnotationsDetector",
    "ImportAliasDetector",
    "InternalImportDetector",
    "LooseObjectDetector",
    "MROCompletenessDetector",
    "ManualProtocolDetector",
    "ManualTypingAliasDetector",
    "NamespaceFacadeScanner",
    "NamespaceSourceDetector",
    "RuntimeAliasDetector",
]
