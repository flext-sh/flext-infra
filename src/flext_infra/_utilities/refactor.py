"""Refactor helper utilities for infrastructure code analysis.

Centralizes rope-based helpers previously defined as module-level
functions in ``flext_infra.refactor.analysis``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path

from pydantic import TypeAdapter, ValidationError

from flext_infra import (
    FlextInfraUtilitiesIteration,
    FlextInfraUtilitiesRefactorCensus,
    FlextInfraUtilitiesRefactorCli,
    FlextInfraUtilitiesRefactorEngine,
    FlextInfraUtilitiesRefactorMroScan,
    FlextInfraUtilitiesRefactorMroTransform,
    FlextInfraUtilitiesRefactorNamespace,
    FlextInfraUtilitiesRefactorPolicy,
    c,
    t,
)


class FlextInfraUtilitiesRefactor(
    FlextInfraUtilitiesRefactorPolicy,
    FlextInfraUtilitiesRefactorEngine,
    FlextInfraUtilitiesRefactorMroScan,
    FlextInfraUtilitiesRefactorNamespace,
    FlextInfraUtilitiesRefactorMroTransform,
    FlextInfraUtilitiesIteration,
    FlextInfraUtilitiesRefactorCli,
    FlextInfraUtilitiesRefactorCensus,
):
    """Rope-based refactor helpers for code analysis.

    Usage via namespace::

        from flext_infra import u

        methods = u.Infra.extract_public_methods_from_dir(package_dir)
    """

    _STRING_LIST_ADAPTER: TypeAdapter[Sequence[str]] = TypeAdapter(Sequence[str])

    @staticmethod
    def entry_list(value: t.Infra.InfraValue | None) -> Sequence[t.StrMapping]:
        """Normalize class-nesting settings entries to a strict list."""
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
        try:
            return list(
                FlextInfraUtilitiesRefactor._STRING_LIST_ADAPTER.validate_python(
                    value,
                )
            )
        except TypeError as exc:
            msg = "expected list value"
            raise TypeError(msg) from exc
        except ValidationError as exc:
            msg = "expected list value"
            raise ValueError(msg) from exc

    @staticmethod
    def normalize_module_path(path_value: str | Path) -> str:
        path = Path(str(path_value).replace("\\", "/"))
        parts = path.parts
        if c.Infra.DEFAULT_SRC_DIR in parts:
            src_index = parts.index(c.Infra.DEFAULT_SRC_DIR)
            suffix = parts[src_index + 1 :]
            if suffix:
                return Path(*suffix).as_posix()
        return path.as_posix().lstrip("./")


__all__ = ["FlextInfraUtilitiesRefactor"]
