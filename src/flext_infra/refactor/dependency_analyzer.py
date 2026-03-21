"""Facade for namespace dependency detectors used by refactor checks."""

from __future__ import annotations

from pathlib import Path

from flext_infra.constants import c
from flext_infra.models import m
from flext_infra.refactor._models_namespace_enforcer import (
    FlextInfraNamespaceEnforcerModels as nem,
)
from flext_infra.utilities import u

from ._detectors.class_placement_detector import (
    ClassPlacementDetector,
)
from ._detectors.compatibility_alias_detector import (
    CompatibilityAliasDetector,
)
from ._detectors.cyclic_import_detector import CyclicImportDetector
from ._detectors.dependency_analyzer_base import DependencyAnalyzer
from ._detectors.future_annotations_detector import (
    FutureAnnotationsDetector,
)
from ._detectors.import_alias_detector import ImportAliasDetector
from ._detectors.internal_import_detector import (
    InternalImportDetector,
)
from ._detectors.loose_object_detector import LooseObjectDetector
from ._detectors.manual_protocol_detector import (
    ManualProtocolDetector,
)
from ._detectors.manual_typing_alias_detector import (
    ManualTypingAliasDetector,
)
from ._detectors.mro_completeness_detector import (
    MROCompletenessDetector,
)
from ._detectors.namespace_facade_scanner import (
    NamespaceFacadeScanner,
)
from ._detectors.namespace_source_detector import (
    NamespaceSourceDetector,
)
from ._detectors.runtime_alias_detector import RuntimeAliasDetector


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
