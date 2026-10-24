"""Generated-file plan decisions exposed through ``u.Infra``.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import difflib
import errno
import os
import sys
import time
from collections.abc import Generator
from contextlib import contextmanager
from functools import partial
from itertools import islice
from typing import TYPE_CHECKING

from flext_cli import m as cli_m, u

from flext_infra import c, m, p, r, t

if sys.platform == "win32":
    import msvcrt
else:
    import fcntl

if TYPE_CHECKING:
    from pathlib import Path


class FlextInfraUtilitiesCodegenFilePlan:
    """Derive generated-file effects from immutable planning data."""

    @staticmethod
    def codegen_target_snapshot(
        path: Path,
    ) -> p.Result[cli_m.Cli.AtomicFileState | m.Cli.AtomicDirectoryChainPlan]:
        """Capture the original leaf or the exact still-missing parent chain.

        Returns:
            The observed file state when the leaf exists, the missing-parent
            chain plan when it does not, or the propagated read failure.

        """
        result_type = r[cli_m.Cli.AtomicFileState | m.Cli.AtomicDirectoryChainPlan]
        observed = u.Cli.atomic_read_binary_file_state(path, required=False)
        if observed.failure:
            return result_type.from_failure(observed)
        if observed.value.parent_device is not None:
            return result_type.ok(observed.value)
        witness = u.Cli.atomic_plan_directory_chain(path.parent)
        if witness.failure:
            return result_type.from_failure(witness)
        if not witness.value.directories:
            return result_type.fail(
                f"codegen destination parent changed during snapshot: {path}",
            )
        return result_type.ok(witness.value)

    @staticmethod
    def codegen_initializer_is_authored(content: bytes | None) -> bool:
        """Elect initializer ownership from content and declared generator markers.

        Returns:
            Whether a nonempty existing initializer belongs to its author.

        """
        return (
            content is not None
            and bool(content.strip())
            and not content.startswith(
                tuple(
                    header.encode(c.DEFAULT_ENCODING)
                    for header in c.Infra.AUTOGEN_HEADERS
                ),
            )
        )

    @staticmethod
    def required_file_states(
        paths: t.IterableOf[Path],
    ) -> p.Result[t.VariadicTuple[cli_m.Cli.AtomicFileState]]:
        """Snapshot descriptor-authenticated states for an inventoried path set.

        Every path must exist: an absent input is a planning defect, not an empty
        snapshot.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[cli_m.Cli.AtomicFileState]]``.

        """
        states: list[cli_m.Cli.AtomicFileState] = []
        for path in sorted(set(paths)):
            state = u.Cli.atomic_read_binary_file_state(path, required=True)
            if state.failure:
                return r[tuple[cli_m.Cli.AtomicFileState, ...]].from_failure(state)
            states.append(state.value)
        return r[tuple[cli_m.Cli.AtomicFileState, ...]].ok(tuple(states))

    @staticmethod
    def atomic_file_state_differs(
        before: m.Cli.AtomicFileState,
        *,
        desired_content: bytes | None,
        desired_mode: int | None,
    ) -> bool:
        """Compare the owner's exact bytes, absence marker, and permission bits.

        Both content fields are binary contracts. Decoding with replacement
        would hide distinct invalid UTF-8 bytes; treating None as empty bytes
        would erase the distinction between an absent and an empty file.

        Returns:
            The resulting ``bool``.

        """
        return before.content != desired_content or before.mode != desired_mode

    @staticmethod
    def codegen_file_requires_effect(plan: m.Infra.CodegenFilePlan) -> bool:
        """Whether publication must change a generated-file destination.

        Returns:
            Whether bytes, mode or declared tracking require publication.

        """
        if plan.index_before is not None:
            return True
        if isinstance(plan.before, m.Cli.AtomicDirectoryChainPlan):
            return plan.desired_content is not None
        return FlextInfraUtilitiesCodegenFilePlan.atomic_file_state_differs(
            plan.before,
            desired_content=plan.desired_content,
            desired_mode=plan.desired_mode,
        )

    @staticmethod
    def codegen_fixed_point(
        plans: t.SequenceOf[m.Infra.CodegenFilePlan],
        *,
        subject: str,
    ) -> p.Result[bool]:
        """Reject a re-plan that still has to change any generated destination.

        Returns:
            Success only when no plan requires an effect; otherwise the failure
            names every residual destination with its bounded residual diff.

        """
        residual = tuple(
            plan
            for plan in plans
            if FlextInfraUtilitiesCodegenFilePlan.codegen_file_requires_effect(plan)
        )
        if residual:
            names = ", ".join(str(plan.path) for plan in residual)
            drift = FlextInfraUtilitiesCodegenFilePlan.codegen_file_drift_report(
                residual,
            )
            return r[bool].fail(
                f"{subject} did not reach a fixed point: {names}\n{drift}",
            )
        return r[bool].ok(value=True)

    @staticmethod
    def codegen_file_drift_report(
        plans: t.SequenceOf[m.Infra.CodegenFilePlan],
        *,
        limit: int = 40,
    ) -> str:
        """Report a bounded byte-exact diff, including line endings and presence.

        Escaped byte lines preserve CRLF, missing final newlines, and non-UTF-8
        content. Only equal bytes with different modes are mode-only drift.
        The observed side is the captured physical file, independent of Git state.

        Returns:
            The resulting ``str``.

        Raises:
            ValueError: If codegen drift report limit must be positive.

        """
        if limit <= 0:
            msg = "codegen drift report limit must be positive"
            raise ValueError(msg)
        parts: list[str] = []
        for plan in plans:
            if isinstance(plan.before, m.Cli.AtomicDirectoryChainPlan):
                parts.append(f"{plan.path}: absent parent chain gains content")
                continue
            raw_before = plan.before.content
            old_lines = tuple(
                repr(line) for line in (raw_before or b"").splitlines(keepends=True)
            )
            new_lines = tuple(
                repr(line)
                for line in (plan.desired_content or b"").splitlines(keepends=True)
            )
            observed_mode = (
                oct(plan.before.mode) if plan.before.mode is not None else "absent"
            )
            rendered_mode = (
                oct(plan.desired_mode) if plan.desired_mode is not None else "absent"
            )
            header = (
                f"--- {plan.path} (observed mode={observed_mode})"
                f"\n+++ {plan.path} (rendered mode={rendered_mode})"
            )
            diff = tuple(
                islice(difflib.unified_diff(old_lines, new_lines, lineterm=""), limit),
            )
            if diff:
                parts.append("\n".join((header, *diff)))
                continue
            old_bytes = (
                raw_before.encode("utf-8")
                if isinstance(raw_before, str)
                else (raw_before or b"")
            )
            new_bytes = plan.desired_content or b""
            if old_bytes == new_bytes:
                parts.append(
                    f"{header}\n(content equal: mode-only drift "
                    f"observed={observed_mode} desired={rendered_mode})",
                )
                continue
            # Lines are equal but bytes are not: name the exact tail difference
            # (line endings / trailing newline) instead of a false mode claim.
            parts.append(
                f"{header}\n(lines equal, bytes differ: observed {len(old_bytes)}B "
                f"tail={old_bytes[-24:]!r}; rendered {len(new_bytes)}B "
                f"tail={new_bytes[-24:]!r})",
            )
        return "\n----\n".join(parts)


__all__: list[str] = ["FlextInfraUtilitiesCodegenFilePlan"]
