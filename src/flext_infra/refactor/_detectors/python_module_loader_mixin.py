"""Mixin providing Python module loading functionality for detectors.

This module provides a mixin class for detectors that need to load and parse
Python modules as part of their analysis.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra.refactor._detectors.module_loader import (
    FlextInfraRefactorDetectorModuleLoader,
)
from flext_infra.refactor._models_namespace_enforcer import (
    FlextInfraNamespaceEnforcerModels as nem,
)

if TYPE_CHECKING:
    from flext_infra import m


class FlextInfraRefactorDetectorPythonModuleLoaderMixin:
    """Mixin providing Python module loading functionality for detectors."""

    @staticmethod
    def _load_python_module(
        file_path: Path,
        *,
        stage: str,
        parse_failures: list[nem.ParseFailureViolation] | None,
    ) -> m.Infra.ParsedPythonModule | None:
        """Load and parse a Python module from a file.

        Args:
            file_path: Path to the Python file to load.
            stage: Processing stage name for error tracking.
            parse_failures: Optional list to accumulate parse failure violations.

        Returns:
            ParsedPythonModule with source and AST, or None if parsing failed.

        """
        return FlextInfraRefactorDetectorModuleLoader.load_python_module(
            file_path,
            stage=stage,
            parse_failures=parse_failures,
        )


__all__ = ["FlextInfraRefactorDetectorPythonModuleLoaderMixin"]
