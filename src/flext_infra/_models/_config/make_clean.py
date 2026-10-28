"""Disposable artifact declarations for the generated Make clean verb.

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
from flext_infra._models._config.contract import FlextInfraModelsConfigContract


class FlextInfraModelsConfigMakeClean:
    """Declarative clean policy composed into the Make config family."""

    class MakeCleanSpec(FlextInfraModelsConfigContract.ConfigContract):
        """Disposable artifacts the generated clean verb removes.

        Stale caches and traces cause FALSE DIAGNOSES, so the disposable set is
        declared data rather than a literal buried in a recipe: every project
        cleans exactly the same things and a new artifact kind is one config row.
        """

        cache_dirs: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Cache directory names removed anywhere in the tree"),
        ]
        root_dirs: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Directories removed at the project root only"),
        ]
        root_files: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Files removed at the project root only"),
        ]
        trace_globs: Annotated[
            tuple[t.NonEmptyStr, ...],
            m.Field(description="Trace/profile globs removed anywhere in the tree"),
        ]


__all__: list[str] = ["FlextInfraModelsConfigMakeClean"]
