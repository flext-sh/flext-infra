"""Refactor helper utilities for infrastructure code analysis.

Centralizes rope-based helpers previously defined as module-level
functions in ``flext_infra.refactor.analysis``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, MutableSequence, Sequence
from pathlib import Path

from pydantic import ValidationError

from flext_core import FlextUtilities
from flext_infra import (
    FlextInfraUtilitiesDiscovery,
    FlextInfraUtilitiesIteration,
    FlextInfraUtilitiesRefactorCensus,
    FlextInfraUtilitiesRefactorCli,
    FlextInfraUtilitiesRefactorMroScan,
    FlextInfraUtilitiesRefactorMroTransform,
    FlextInfraUtilitiesRefactorNamespace,
    FlextInfraUtilitiesRefactorPydantic,
    FlextInfraUtilitiesRefactorPydanticAnalysis,
    c,
    t,
)
from flext_infra.refactor._utilities_engine import FlextInfraUtilitiesRefactorEngine
from flext_infra.refactor._utilities_policy import FlextInfraUtilitiesRefactorPolicy


class FlextInfraUtilitiesRefactor(
    FlextInfraUtilitiesRefactorPolicy,
    FlextInfraUtilitiesRefactorEngine,
    FlextInfraUtilitiesRefactorMroScan,
    FlextInfraUtilitiesRefactorNamespace,
    FlextInfraUtilitiesRefactorMroTransform,
    FlextInfraUtilitiesRefactorPydantic,
    FlextInfraUtilitiesRefactorPydanticAnalysis,
    FlextInfraUtilitiesIteration,
    FlextInfraUtilitiesDiscovery,
    FlextInfraUtilitiesRefactorCli,
    FlextInfraUtilitiesRefactorCensus,
):
    """Rope-based refactor helpers for code analysis.

    Usage via namespace::

        from flext_infra import u

        methods = u.Infra.extract_public_methods_from_dir(package_dir)
    """

    @staticmethod
    def module_path(*, file_path: Path, project_root: Path) -> str:
        """Compute dotted module path relative to a project root.

        Strips the ``src/`` directory component and file extension.

        Args:
            file_path: Absolute path to a Python file.
            project_root: Root directory of the project.

        Returns:
            Dotted module path (e.g., ``"flext_infra.refactor.engine"``).

        """
        rel = file_path.relative_to(project_root)
        parts = [
            part
            for part in rel.with_suffix("").parts
            if part != c.Infra.Paths.DEFAULT_SRC_DIR
        ]
        return ".".join(parts)

    _MODULE_FAMILY_KEYS: t.StrSequence = (
        "_models",
        "_utilities",
        "_dispatcher",
        "_decorators",
        "_runtime",
    )

    @staticmethod
    def module_family_from_path(path: str) -> str:
        """Resolve module family key from a source file path."""
        normalized = path.replace("\\", "/")
        for key in FlextInfraUtilitiesRefactor._MODULE_FAMILY_KEYS:
            if key in normalized:
                return key
        return "other_private"

    @staticmethod
    def entry_list(value: t.Infra.InfraValue | None) -> Sequence[t.StrMapping]:
        """Normalize class-nesting config entries to a strict list."""
        if value is None:
            return []
        try:
            return t.Infra.STR_MAPPING_SEQ_ADAPTER.validate_python(value)
        except ValidationError:
            msg = "class nesting entries must be a list"
            raise ValueError(msg) from None

    @staticmethod
    def string_list(value: t.Infra.InfraValue | None) -> t.StrSequence:
        """Normalize policy fields that should contain string collections."""
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        if not isinstance(value, list):
            msg = "expected list value"
            raise TypeError(msg)
        try:
            validated: Sequence[t.Infra.InfraValue] = (
                t.Infra.INFRA_SEQ_ADAPTER.validate_python(value)
            )
        except ValidationError as exc:
            msg = "expected list value"
            raise ValueError(msg) from exc
        for item in validated:
            if not isinstance(item, str):
                msg = "expected list value"
                raise TypeError(msg)
        return [v for v in validated if isinstance(v, str)]

    @staticmethod
    def mapping_list(
        value: t.Infra.InfraValue | None,
    ) -> Sequence[Mapping[str, t.Infra.InfraValue]]:
        """Normalize policy fields that should contain mapping collections."""
        if value is None:
            return []
        if isinstance(value, list):
            try:
                value_items: Sequence[t.Infra.InfraValue] = (
                    t.Infra.INFRA_SEQ_ADAPTER.validate_python(value)
                )
            except ValidationError as exc:
                msg = "expected Sequence[Mapping[str, t.Infra.InfraValue]] value"
                raise ValueError(msg) from exc
            normalized: MutableSequence[Mapping[str, t.Infra.InfraValue]] = []
            for item in value_items:
                if not FlextUtilities.is_mapping(item):
                    continue
                normalized.append(
                    t.Infra.INFRA_MAPPING_ADAPTER.validate_python(item),
                )
            return normalized
        msg = "expected Sequence[Mapping[str, t.Infra.InfraValue]] value"
        raise ValueError(msg)

    @staticmethod
    def has_required_fields(
        entry: t.Infra.InfraValue,
        required_fields: t.StrSequence,
    ) -> bool:
        if not FlextUtilities.is_mapping(entry):
            return False
        return all(key in entry for key in required_fields)

    @staticmethod
    def normalize_module_path(path_value: Path) -> str:
        parts = path_value.parts
        if c.Infra.Paths.DEFAULT_SRC_DIR in parts:
            src_index = parts.index(c.Infra.Paths.DEFAULT_SRC_DIR)
            suffix = parts[src_index + 1 :]
            if suffix:
                return Path(*suffix).as_posix()
        return path_value.as_posix().lstrip("./")

    @staticmethod
    def rewrite_scope(entry: t.StrMapping) -> str:
        raw_scope = entry.get(c.Infra.ReportKeys.REWRITE_SCOPE, c.Infra.ReportKeys.FILE)
        scope = FlextUtilities.norm_str(raw_scope, case="lower")
        if scope in {
            c.Infra.ReportKeys.FILE,
            c.Infra.PROJECT,
            c.Infra.ReportKeys.WORKSPACE,
        }:
            return scope
        msg = f"unsupported rewrite_scope: {raw_scope}"
        raise ValueError(msg)


__all__ = ["FlextInfraUtilitiesRefactor"]
