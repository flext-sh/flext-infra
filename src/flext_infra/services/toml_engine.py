"""TOML engine — applies m.Infra.TomlPhaseConfig to docs.

Uses r.traverse + r.safe for railway-oriented phase iteration,
u.Cli.toml_* for all sync/navigate primitives,
s for bootstrap.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from typing import Annotated, override

from pydantic import Field

from flext_infra import c, m, r, s, t, u


class FlextInfraToml(s[Sequence[t.StrSequence]]):
    """Apply ``m.Infra.TomlPhaseConfig`` phases to a TOML document."""

    doc: Annotated[
        t.Cli.TomlDocument,
        Field(exclude=True, description="Target TOML document"),
    ]
    phases: Annotated[
        Sequence[m.Infra.TomlPhaseConfig],
        Field(
            default_factory=list,
            exclude=True,
            description="Phase configs applied to the TOML document",
        ),
    ]

    @classmethod
    def apply_phases(
        cls,
        doc: t.Cli.TomlDocument,
        *phases: m.Infra.TomlPhaseConfig,
    ) -> t.StrSequence:
        """Apply a declarative phase set to one TOML document."""
        return cls(doc=doc, phases=phases).apply()

    @override
    def execute(self) -> r[Sequence[t.StrSequence]]:
        """Apply all phases via r.traverse — fail-fast on first error."""
        return r.traverse(list(self.phases), lambda p: self._apply_phase(self.doc, p))

    def apply(self) -> t.StrSequence:
        """Apply phases and return one flat change list."""
        result = self.execute()
        if result.failure:
            msg = result.error or "failed to apply TOML phases"
            raise ValueError(msg)
        return [change for batch in result.value for change in batch]

    @r.safe
    def _apply_phase(
        self, doc: t.Cli.TomlDocument, phase: m.Infra.TomlPhaseConfig
    ) -> t.StrSequence:
        """Apply one phase. r.safe wraps exceptions as r.fail."""
        return self._apply_phase_inner(doc, phase, parent_path=())

    def _apply_phase_inner(
        self,
        doc: t.Cli.TomlDocument,
        phase: m.Infra.TomlPhaseConfig,
        *,
        parent_path: t.StrSequence,
    ) -> t.StrSequence:
        """Apply one phase recursively without result wrapping."""
        out: MutableSequence[str] = []

        if (
            not phase.operations
            and not phase.nested_tables
            and phase.custom_handler is not None
            and not phase.table_path
        ):
            out.extend(phase.custom_handler(doc))
            return list(out)

        phase_path = (*parent_path, *phase.root_path, *phase.table_path)
        tbl = u.Cli.toml_ensure_path(doc, phase_path)
        pfx = u.Cli.toml_dot_path(*phase_path)

        for operation in phase.operations:
            self._apply_operation(tbl, operation, out, pfx)

        for nested in phase.nested_tables:
            out.extend(
                self._apply_phase_inner(doc, nested, parent_path=phase_path),
            )

        if phase.custom_handler is not None:
            out.extend(phase.custom_handler(doc))

        return list(out)

    @staticmethod
    def _apply_operation(
        tbl: t.Cli.TomlTable,
        operation: t.Infra.TomlOperation,
        out: MutableSequence[str],
        pfx: str,
    ) -> None:
        """Apply one discriminated TOML operation to the target table."""
        match operation.kind:
            case "set":
                u.Cli.toml_sync_value(
                    tbl,
                    operation.key,
                    operation.value,
                    out,
                    f"{u.Cli.toml_dot_path(pfx, operation.key)} set to {operation.value}",
                )
            case "list":
                if operation.strategy in {
                    c.Infra.TOML_MERGE_ADDITIVE,
                    c.Infra.TOML_MERGE_MERGE,
                }:
                    u.Cli.toml_merge_string_list(
                        tbl,
                        operation.key,
                        operation.values,
                        out,
                        f"{u.Cli.toml_dot_path(pfx, operation.key)} updated",
                    )
                else:
                    u.Cli.toml_sync_string_list(
                        tbl,
                        operation.key,
                        operation.values,
                        out,
                        f"{u.Cli.toml_dot_path(pfx, operation.key)} set",
                        sort_values=operation.sort,
                    )
            case "remove":
                FlextInfraToml._remove_operation(tbl, operation, out, pfx)

    @staticmethod
    def _remove_operation(
        tbl: t.Cli.TomlTable,
        operation: m.Infra.TomlRemoveOp,
        out: MutableSequence[str],
        pfx: str,
    ) -> None:
        """Apply one remove operation, optionally under a relative nested table."""
        if not operation.table_path:
            u.Cli.toml_remove_key_if_present(
                tbl,
                operation.key,
                out,
                f"{u.Cli.toml_dot_path(pfx, operation.key)} removed",
            )
            return

        target = u.Cli.toml_table_path(tbl, operation.table_path)
        if target is None:
            return
        u.Cli.toml_remove_key_if_present(
            target,
            operation.key,
            out,
            f"{u.Cli.toml_dot_path(pfx, *operation.table_path, operation.key)} removed",
        )


__all__ = ["FlextInfraToml"]
