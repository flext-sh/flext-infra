from __future__ import annotations

import ast
from pathlib import Path
from typing import override

from flext_infra.codegen._codegen_ast_parsing import FlextInfraCodegenAstParsing
from flext_infra.codegen._codegen_execution import FlextInfraCodegenExecution


class FlextInfraUtilitiesCodegen(
    FlextInfraCodegenExecution, FlextInfraCodegenAstParsing,
):
    @staticmethod
    @override
    def infer_package(path: Path) -> str:
        """Infer package name from file path."""
        return FlextInfraCodegenAstParsing.infer_package(path)

    @staticmethod
    @override
    def extract_exports(tree: ast.Module) -> tuple[bool, list[str]]:
        """Extract __all__ exports from AST module."""
        return FlextInfraCodegenAstParsing.extract_exports(tree)

    @staticmethod
    @override
    def extract_inline_constants(tree: ast.Module) -> dict[str, str]:
        """Extract inline string constants from AST module."""
        return FlextInfraCodegenAstParsing.extract_inline_constants(tree)


__all__ = ["FlextInfraUtilitiesCodegen"]
