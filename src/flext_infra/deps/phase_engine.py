"""TOML engine — applies m.Infra.TomlPhaseConfig to docs.

Uses one cached per-document path resolver plus
u.Cli.toml_* sync/navigate primitives,
s for bootstrap.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    MutableMapping,
    MutableSequence,
    Sequence,
)
from typing import Annotated, override

from flext_infra import c, m, p, r, s, t, u


class FlextInfraPhaseEngine(s[Sequence[t.StrSequence]]):
    """Apply ``m.Infra.TomlPhaseConfig`` phases to a TOML document."""

    doc: Annotated[
        t.Cli.TomlDocument,
        m.Field(exclude=True, description="Target TOML document"),
    ]
    phases: Annotated[
        Sequence[m.Infra.TomlPhaseConfig],
        m.Field(
            default_factory=tuple,
            description="Ordered TOML transformation phases to apply.",
        ),
    ]
    _table_cache: dict[tuple[str, ...], t.Cli.TomlTable] = u.PrivateAttr(
        default_factory=dict
    )

    @classmethod
    def apply_phases(
        cls,
        doc: t.Cli.TomlDocument,
        *phases: m.Infra.TomlPhaseConfig,
    ) -> t.StrSequence:
        """Apply a declarative phase set to one TOML document."""
        engine = cls.model_construct(doc=doc, phases=phases)
        try:
            return engine.apply()
        except Exception as exc:
            msg = str(exc) or "failed to apply TOML phases"
            raise ValueError(msg) from exc

    @classmethod
    def apply_payload_phases(
        cls,
        payload: MutableMapping[str, t.Cli.JsonValue],
        *phases: m.Infra.TomlPhaseConfig,
    ) -> t.StrSequence:
        """Apply one declarative phase set to one plain TOML payload."""
        try:
            return [
                change
                for phase in phases
                for change in cls._apply_payload_phase(
                    payload,
                    phase,
                    parent_path=(),
                )
            ]
        except Exception as exc:
            msg = str(exc) or "failed to apply TOML payload phases"
            raise ValueError(msg) from exc

    @override
    def execute(self) -> p.Result[Sequence[t.StrSequence]]:
        """Apply all phases and preserve the existing result contract."""
        try:
            return r[Sequence[t.StrSequence]].ok(
                tuple(self._apply_phase(phase) for phase in self.phases),
            )
        except Exception as exc:
            return r[Sequence[t.StrSequence]].fail(str(exc))

    def apply(self) -> t.StrSequence:
        """Apply phases and return one flat change list."""
        try:
            return self._flatten_batches()
        except Exception as exc:
            msg = str(exc) or "failed to apply TOML phases"
            raise ValueError(msg) from exc

    def _apply_phase(self, phase: m.Infra.TomlPhaseConfig) -> t.StrSequence:
        """Apply one phase without result-wrapper overhead in the hot path."""
        return self._apply_phase_inner(phase, parent_path=())

    @classmethod
    def _apply_payload_phase(
        cls,
        payload: MutableMapping[str, t.Cli.JsonValue],
        phase: m.Infra.TomlPhaseConfig,
        *,
        parent_path: tuple[str, ...],
    ) -> t.StrSequence:
        """Apply one phase recursively against one normalized payload."""
        if phase.custom_handler is not None:
            msg = f"payload phases do not support custom handlers: {phase.name}"
            raise ValueError(msg)
        out: MutableSequence[str] = []
        phase_path = (*parent_path, *phase.root_path, *phase.table_path)
        table = u.Cli.toml_mapping_ensure_path(payload, phase_path)
        prefix = u.Cli.toml_dot_path(*phase_path)
        for operation in phase.operations:
            cls._apply_payload_operation(table, operation, out, prefix)
        for nested in phase.nested_tables:
            out.extend(
                cls._apply_payload_phase(
                    payload,
                    nested,
                    parent_path=phase_path,
                )
            )
        return out

    def _batches(self) -> tuple[t.StrSequence, ...]:
        """Return one batch of changes per configured phase."""
        return tuple(self._apply_phase(phase) for phase in self.phases)

    def _flatten_batches(self) -> t.StrSequence:
        """Flatten all phase batches into one change list."""
        return [change for batch in self._batches() for change in batch]

    def _resolve_phase_table(self, phase_path: tuple[str, ...]) -> t.Cli.TomlTable:
        """Resolve and cache one TOML table path for the current document."""
        cached_table = self._table_cache.get(phase_path)
        if cached_table is not None:
            return cached_table
        table = u.Cli.toml_ensure_path(self.doc, phase_path)
        self._table_cache[phase_path] = table
        return table

    def _apply_phase_inner(
        self,
        phase: m.Infra.TomlPhaseConfig,
        *,
        parent_path: tuple[str, ...],
    ) -> t.StrSequence:
        """Apply one phase recursively using cached path resolution."""
        out: MutableSequence[str] = []

        if (
            not phase.operations
            and not phase.nested_tables
            and phase.custom_handler is not None
            and not phase.table_path
        ):
            out.extend(phase.custom_handler(self.doc))
            return out

        phase_path = (*parent_path, *phase.root_path, *phase.table_path)
        tbl = self._resolve_phase_table(phase_path)
        pfx = u.Cli.toml_dot_path(*phase_path)

        for operation in phase.operations:
            self._apply_operation(tbl, operation, out, pfx)

        for nested in phase.nested_tables:
            out.extend(
                self._apply_phase_inner(nested, parent_path=phase_path),
            )

        if phase.custom_handler is not None:
            out.extend(phase.custom_handler(self.doc))

        return out

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
                FlextInfraPhaseEngine._remove_operation(tbl, operation, out, pfx)

    @staticmethod
    def _apply_payload_operation(
        tbl: MutableMapping[str, t.Cli.JsonValue],
        operation: t.Infra.TomlOperation,
        out: MutableSequence[str],
        pfx: str,
    ) -> None:
        """Apply one discriminated TOML operation to one plain mapping table."""
        match operation.kind:
            case "set":
                u.Cli.toml_mapping_sync_value(
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
                    u.Cli.toml_mapping_merge_string_list(
                        tbl,
                        operation.key,
                        operation.values,
                        out,
                        f"{u.Cli.toml_dot_path(pfx, operation.key)} updated",
                    )
                else:
                    u.Cli.toml_mapping_sync_string_list(
                        tbl,
                        operation.key,
                        operation.values,
                        out,
                        f"{u.Cli.toml_dot_path(pfx, operation.key)} set",
                        sort_values=operation.sort,
                    )
            case "remove":
                FlextInfraPhaseEngine._remove_payload_operation(
                    tbl, operation, out, pfx
                )

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

    @staticmethod
    def _remove_payload_operation(
        tbl: MutableMapping[str, t.Cli.JsonValue],
        operation: m.Infra.TomlRemoveOp,
        out: MutableSequence[str],
        pfx: str,
    ) -> None:
        """Apply one remove operation to one plain mapping payload."""
        if not operation.table_path:
            u.Cli.toml_mapping_remove_key_if_present(
                tbl,
                operation.key,
                out,
                f"{u.Cli.toml_dot_path(pfx, operation.key)} removed",
            )
            return
        target = u.Cli.toml_mapping_path(tbl, operation.table_path)
        if target is None:
            return
        u.Cli.toml_mapping_remove_key_if_present(
            target,
            operation.key,
            out,
            f"{u.Cli.toml_dot_path(pfx, *operation.table_path, operation.key)} removed",
        )


__all__: list[str] = ["FlextInfraPhaseEngine"]
