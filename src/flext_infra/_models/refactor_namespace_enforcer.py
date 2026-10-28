"""Namespace parse-failure model shared by refactor workflows.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from typing import Annotated

from flext_cli import m

from flext_infra import t
from flext_infra._models import FlextInfraModelsMixins


class FlextInfraModelsNamespaceEnforcer:
    """Namespace parse-failure contract."""

    class ParseFailureViolation(
        FlextInfraModelsMixins.FilePathMixin,
        FlextInfraModelsMixins.ErrorDetailMixin,
        m.ContractModel,
    ):
        """Parse failure violation."""

        stage: Annotated[t.NonEmptyStr, m.Field(description="Parse stage")]
        error_type: Annotated[t.NonEmptyStr, m.Field(description="Error type")]


__all__: list[str] = ["FlextInfraModelsNamespaceEnforcer"]
