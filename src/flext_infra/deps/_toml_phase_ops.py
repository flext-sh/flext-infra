"""TOML operation appliers for the TOML phase (cohesive mixin, §3.1 split).

Holds the discriminated ``m.Cli.TomlOperation`` appliers for both the
``t.Cli.TomlTable`` (document) and ``t.MutableJsonMapping`` (payload) paths.
Composed into ``FlextInfraTomlPhaseService`` via MRO.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra import c, m, p, t, u


class FlextInfraTomlPhaseOps:
    """Discriminated TOML operation appliers shared by the TOML phase."""

    @staticmethod
    def _apply_operation(
        tbl: t.Cli.TomlTable,
        operation: p.Cli.TomlOperation,
        out: t.MutableSequenceOf[str],
        pfx: str,
    ) -> None:
        """Apply one discriminated TOML operation to the target table."""
        if isinstance(operation, m.Cli.TomlSetOp):
            if u.Cli.toml_sync_value(tbl, operation.key, operation.value):
                out.append(
                    f"{u.Cli.toml_dot_path(pfx, operation.key)} set to "
                    f"{operation.value}"
                )
            return
        if isinstance(operation, m.Cli.TomlListOp):
            if operation.strategy in {
                c.Cli.TomlMergeMode.ADDITIVE,
                c.Cli.TomlMergeMode.MERGE,
            }:
                if u.Cli.toml_merge_string_list(tbl, operation.key, operation.values):
                    out.append(f"{u.Cli.toml_dot_path(pfx, operation.key)} updated")
                return
            if u.Cli.toml_sync_string_list(
                tbl, operation.key, operation.values, sort_values=operation.sort
            ):
                out.append(f"{u.Cli.toml_dot_path(pfx, operation.key)} set")
            return
        FlextInfraTomlPhaseOps._remove_operation(tbl, operation, out, pfx)

    @staticmethod
    def _apply_payload_operation(
        tbl: t.MutableJsonMapping,
        operation: p.Cli.TomlOperation,
        out: t.MutableSequenceOf[str],
        pfx: str,
    ) -> None:
        """Apply one discriminated TOML operation to one plain mapping table."""
        match operation.kind:
            case c.Cli.TomlOperationKind.SET:
                if u.Cli.toml_mapping_sync_value(tbl, operation.key, operation.value):
                    out.append(
                        f"{u.Cli.toml_dot_path(pfx, operation.key)} set to "
                        f"{operation.value}"
                    )
            case c.Cli.TomlOperationKind.LIST:
                if operation.strategy in {
                    c.Cli.TomlMergeMode.ADDITIVE,
                    c.Cli.TomlMergeMode.MERGE,
                }:
                    if u.Cli.toml_mapping_merge_string_list(
                        tbl, operation.key, operation.values
                    ):
                        out.append(f"{u.Cli.toml_dot_path(pfx, operation.key)} updated")
                elif u.Cli.toml_mapping_sync_string_list(
                    tbl, operation.key, operation.values, sort_values=operation.sort
                ):
                    out.append(f"{u.Cli.toml_dot_path(pfx, operation.key)} set")
            case c.Cli.TomlOperationKind.REMOVE:
                FlextInfraTomlPhaseOps._remove_payload_operation(
                    tbl, operation, out, pfx
                )

    @staticmethod
    def _remove_operation(
        tbl: t.Cli.TomlTable,
        operation: p.Cli.TomlRemoveOp,
        out: t.MutableSequenceOf[str],
        pfx: str,
    ) -> None:
        """Apply one remove operation, optionally under a relative nested table."""
        if not operation.table_path:
            if u.Cli.toml_remove_key_if_present(tbl, operation.key):
                out.append(f"{u.Cli.toml_dot_path(pfx, operation.key)} removed")
            return

        target = u.Cli.toml_table_path(tbl, operation.table_path)
        if target is None:
            return
        if u.Cli.toml_remove_key_if_present(target, operation.key):
            out.append(
                f"{u.Cli.toml_dot_path(pfx, *operation.table_path, operation.key)} "
                "removed"
            )

    @staticmethod
    def _remove_payload_operation(
        tbl: t.MutableJsonMapping,
        operation: p.Cli.TomlRemoveOp,
        out: t.MutableSequenceOf[str],
        pfx: str,
    ) -> None:
        """Apply one remove operation to one plain mapping payload."""
        if not operation.table_path:
            if u.Cli.toml_mapping_remove_key_if_present(tbl, operation.key):
                out.append(f"{u.Cli.toml_dot_path(pfx, operation.key)} removed")
            return
        target = u.Cli.toml_mapping_path(tbl, operation.table_path)
        if target is None:
            return
        if u.Cli.toml_mapping_remove_key_if_present(target, operation.key):
            out.append(
                f"{u.Cli.toml_dot_path(pfx, *operation.table_path, operation.key)} "
                "removed"
            )


__all__: list[str] = ["FlextInfraTomlPhaseOps"]
