from __future__ import annotations

from pathlib import Path

from flext_infra import c, m, u
from flext_infra.refactor._models_namespace_enforcer import (
    FlextInfraNamespaceEnforcerModels as nem,
)


class FlextInfraRefactorDetectorModuleLoader:
    @staticmethod
    def load_python_module(
        file_path: Path,
        *,
        stage: str,
        parse_failures: list[nem.ParseFailureViolation] | None,
    ) -> m.Infra.ParsedPythonModule | None:
        try:
            source = file_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
        except UnicodeDecodeError as exc:
            FlextInfraRefactorDetectorModuleLoader._append_parse_failure(
                parse_failures=parse_failures,
                file_path=file_path,
                stage=stage,
                error_type=type(exc).__name__,
                detail=str(exc),
            )
            return None
        except OSError as exc:
            FlextInfraRefactorDetectorModuleLoader._append_parse_failure(
                parse_failures=parse_failures,
                file_path=file_path,
                stage=stage,
                error_type=type(exc).__name__,
                detail=str(exc),
            )
            return None
        tree = u.Infra.parse_ast_from_source(source)
        if tree is None:
            FlextInfraRefactorDetectorModuleLoader._append_parse_failure(
                parse_failures=parse_failures,
                file_path=file_path,
                stage=stage,
                error_type="SyntaxError",
                detail="invalid python source",
            )
            return None
        return m.Infra.ParsedPythonModule(source=source, tree=tree)

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


__all__ = ["FlextInfraRefactorDetectorModuleLoader"]
