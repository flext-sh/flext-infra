"""Declarative TOML phase application over one normalized pyproject payload.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING

from flext_cli import u

from flext_infra import c, m, r, t
from flext_infra._utilities import FlextInfraUtilitiesMiseBinary

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraUtilitiesPyprojectTomlPhases:
    """Apply ``m.Infra.DepsToml.PhaseConfig`` phases to plain TOML payloads."""

    @classmethod
    def format_toml_source(
        cls,
        source: str,
        *,
        path: Path,
        toolchain_root: Path,
        taplo_version: str,
        process_timeout_seconds: int = c.Infra.TIMEOUT_DEFAULT,
    ) -> p.Result[str]:
        """Format TOML through the configured workspace Taplo toolchain.

        ``taplo_version`` is the declared selector and keys the format cache;
        Mise resolves the executable, through the committed mise.lock wherever
        it pins Taplo (``managed_mise_binary``).

        Returns:
            The resulting ``p.Result[str]``.

        """
        config_path = toolchain_root / c.Infra.TAPLO_CONFIG_FILENAME
        config_content = config_path.read_bytes() if config_path.is_file() else b""
        resolved_path = path.resolve()
        resolved_toolchain_root = toolchain_root.resolve()
        execution_root = next(
            candidate
            for candidate in (resolved_toolchain_root, *resolved_toolchain_root.parents)
            if candidate.is_dir()
        )
        relative_path = (
            resolved_path.relative_to(resolved_toolchain_root).as_posix()
            if resolved_path.is_relative_to(resolved_toolchain_root)
            else resolved_path.relative_to(resolved_path.parent).as_posix()
        )
        return cls._format_toml_source_cached(
            source,
            relative_path=relative_path,
            config=(
                config_path.resolve() if config_content else None,
                u.Cli.sha256_bytes(config_content),
            ),
            taplo=(taplo_version, process_timeout_seconds, execution_root),
        )

    @staticmethod
    @lru_cache(maxsize=c.Infra.CONTENT_CACHE_MAXSIZE)
    def _format_toml_source_cached(
        source: str,
        *,
        relative_path: str,
        config: tuple[Path | None, str],
        taplo: tuple[str, int, Path],
    ) -> p.Result[str]:

        taplo_result = FlextInfraUtilitiesPyprojectTomlPhases._taplo_binary(taplo[2])
        if taplo_result.failure:
            return r[str].from_failure(taplo_result)
        config_path, _config_digest = config
        _taplo_version, process_timeout_seconds, execution_root = taplo
        command = [
            str(taplo_result.value),
            "format",
            "-",
            "--stdin-filepath",
            relative_path,
        ]
        if config_path is not None:
            command.extend(("--config", str(config_path)))
        # Generated content must not pass through normalized text model fields.
        result = u.Cli.run_bytes(
            command,
            cwd=execution_root,
            options=m.Cli.ProcessOptions(
                input_data=source.encode(c.DEFAULT_ENCODING),
            ),
            timeout=process_timeout_seconds,
        )
        if result.failure:
            return r[str].from_failure(result)
        output = result.value
        if not u.Cli.process_succeeded(output.outcome):
            detail = (
                (output.stderr or output.stdout)
                .decode(c.DEFAULT_ENCODING, errors="backslashreplace")
                .strip()
            )
            return r[str].fail(
                f"taplo format failed ({output.outcome.raw_return_code}): {detail}",
            )
        try:
            formatted = output.stdout.decode(c.DEFAULT_ENCODING)
        except UnicodeDecodeError as exc:
            return r[str].fail(
                f"taplo format returned non-UTF-8 output: {exc}",
                exception=exc,
            )
        return r[str].ok(formatted)

    @staticmethod
    def _taplo_binary(execution_root: Path) -> p.Result[Path]:
        """Resolve Make's declared Taplo executable through Mise.

        Returns:
            The resulting ``p.Result[Path]``.

        """
        return FlextInfraUtilitiesMiseBinary.managed_mise_binary(
            c.Infra.TAPLO_MISE_TOOL_NAME,
            execution_root,
        )

    @classmethod
    def apply_toml_phases(
        cls,
        payload: t.MutableJsonMapping,
        *phases: m.Infra.DepsToml.PhaseConfig,
    ) -> Sequence[str]:
        """Apply declarative phases in order and return one flat change list.

        Returns:
            The resulting ``Sequence[str]``.

        """
        return [
            change
            for phase in phases
            for change in cls._apply_toml_phase(payload, phase, parent_path=())
        ]

    @classmethod
    def _apply_toml_phase(
        cls,
        payload: t.MutableJsonMapping,
        phase: m.Infra.DepsToml.PhaseConfig,
        *,
        parent_path: Sequence[str],
    ) -> Sequence[str]:
        """Apply one phase and its nested tables below ``parent_path``.

        Returns:
            The resulting ``Sequence[str]``.

        """
        phase_path = (*parent_path, *phase.root_path, *phase.table_path)
        table = u.Cli.toml_mapping_ensure_path(payload, phase_path)
        prefix = u.Cli.toml_dot_path(*phase_path)
        changes = [
            f"{u.Cli.toml_dot_path(prefix, *path)} {outcome}"
            for operation in phase.operations
            for path, outcome in cls._apply_toml_operation(table, operation)
        ]
        for nested in phase.nested_tables:
            changes.extend(
                cls._apply_toml_phase(payload, nested, parent_path=phase_path),
            )
        return changes

    @staticmethod
    def _apply_toml_operation(
        table: t.MutableJsonMapping,
        operation: m.Infra.DepsToml.SetOp
        | m.Infra.DepsToml.ListOp
        | m.Infra.DepsToml.RemoveOp,
    ) -> Sequence[tuple[Sequence[str], str]]:
        """Apply one operation; return its ``(relative key path, outcome)`` change.

        Returns:
            The resulting ``Sequence[tuple[Sequence[str], str]]``.

        """
        if isinstance(operation, m.Infra.DepsToml.SetOp):
            changed = u.Cli.toml_mapping_sync_value(
                table,
                operation.key,
                operation.value,
            )
            return (((operation.key,), f"set to {operation.value}"),) if changed else ()
        if isinstance(operation, m.Infra.DepsToml.ListOp):
            if operation.strategy == c.Infra.TomlMergeMode.REPLACE:
                changed = u.Cli.toml_mapping_sync_string_list(
                    table,
                    operation.key,
                    operation.values,
                    sort_values=operation.sort,
                )
                return (((operation.key,), "set"),) if changed else ()
            changed = u.Cli.toml_mapping_merge_string_list(
                table,
                operation.key,
                operation.values,
            )
            return (((operation.key,), "updated"),) if changed else ()
        target = (
            u.Cli.toml_mapping_path(table, operation.table_path)
            if operation.table_path
            else table
        )
        removed = target is not None and u.Cli.toml_mapping_remove_key_if_present(
            target,
            operation.key,
        )
        return (((*operation.table_path, operation.key), "removed"),) if removed else ()


__all__: list[str] = ["FlextInfraUtilitiesPyprojectTomlPhases"]
