"""Compatibility re-export: the canonical owner is ``flext_infra.refactor``.

The 2026-09-06 wave half-moved this module: consumers on both paths remained.
Until that move is completed by its owner, this shim keeps every consumer on
one importable symbol instead of a ModuleNotFoundError at codegen time.
"""

from flext_infra.refactor.project_alias_migrator import (
    FlextInfraRefactorProjectAliasMigrator,
)

__all__: list[str] = ["FlextInfraRefactorProjectAliasMigrator"]
