from __future__ import annotations

from pathlib import Path

from flext_infra import m
from flext_infra.refactor._detectors.module_loader import (
    FlextInfraRefactorDetectorModuleLoader,
)
from flext_infra.refactor._models_namespace_enforcer import (
    FlextInfraNamespaceEnforcerModels as nem,
)


class FlextInfraRefactorDetectorPythonModuleLoaderMixin:
    @staticmethod
    def _load_python_module(
        file_path: Path,
        *,
        stage: str,
        parse_failures: list[nem.ParseFailureViolation] | None,
    ) -> m.Infra.ParsedPythonModule | None:
        return FlextInfraRefactorDetectorModuleLoader.load_python_module(
            file_path,
            stage=stage,
            parse_failures=parse_failures,
        )


__all__ = ["FlextInfraRefactorDetectorPythonModuleLoaderMixin"]
