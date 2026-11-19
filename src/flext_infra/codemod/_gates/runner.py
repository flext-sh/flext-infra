"""Subprocess tool execution helper for codemod gate measurement.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import shutil
import sys
import time
from collections.abc import Sequence
from pathlib import Path

from flext_infra import m, p, r, settings, u


class FlextInfraModGateRunner:
    """Execute managed native scanners and preserve finding/failure receipts."""

    @staticmethod
    def _path_depth(path: Path) -> int:
        """Return path depth for deterministic deepest-owner selection.

        Returns:
            Path depth for deterministic deepest-owner selection.

        """
        return len(path.parts)

    @staticmethod
    def _run_tool(
        root: Path,
        command: Sequence[str],
        *,
        outputs: tuple[Path, Path, Path],
        finding_exit_code: int | None = None,
        runner: p.Cli.CommandRunner = u.Cli,
    ) -> p.Result[p.Cli.ProcessOutcome]:
        """Run one AST tool and preserve its documented finding status.

        Resolve and authenticate in Make's declared tool-owning invocation
        context first. Execute the absolute managed binary in the consumer
        directory, so neither a shim nor that directory can select another tool.

        Returns:
            The fully reaped outcome; streams remain in their caller-owned files.

        """
        stdout_file, stderr_file, artifact_root = outputs
        owner_root = u.Infra.runtime_environment_dir(
            Path.cwd(),
            runtime_root=settings.fetch_global().Infra.runtime_root,
        ).parent
        binary = u.Infra.managed_mise_binary(command[0], owner_root)
        if binary.failure:
            return r[p.Cli.ProcessOutcome].from_failure(binary)
        sys.stderr.write(
            f"mod: start {' '.join(command[:2])} args={max(0, len(command) - 2)}\n",
        )
        sys.stderr.flush()
        started = time.monotonic()
        run = runner.run_to_file(
            (str(binary.value), *command[1:]),
            stdout_file,
            cwd=root,
            options=m.Cli.ProcessOptions(stderr_file=stderr_file),
        )
        if run.failure:
            return r[p.Cli.ProcessOutcome].from_failure(run)
        outcome = run.value
        sys.stderr.write(
            f"mod: finish {command[0]} exit={outcome.raw_return_code} "
            f"duration={time.monotonic() - started:.2f}s "
            f"stdout_file={stdout_file}\n",
        )
        sys.stderr.flush()
        if not u.Cli.process_succeeded(outcome):
            if (
                outcome.raw_return_code == finding_exit_code
                and not outcome.timed_out
                and outcome.forwarded_signal is None
            ):
                return r[p.Cli.ProcessOutcome].ok(outcome)
            stream_receipts = tuple(
                u.Infra.publish_mod_native_artifact(
                    artifact_root,
                    Path(shutil.copy2(path, path.with_name(f"{path.name}.receipt"))),
                )
                for path in (stdout_file, stderr_file)
            )
            detail = "\n".join(
                f"{channel}={receipt.path} size={receipt.size} sha256={receipt.sha256}"
                for channel, receipt in zip(
                    ("stdout", "stderr"), stream_receipts, strict=True
                )
            )
            return r[p.Cli.ProcessOutcome].fail(
                f"{command[0]} exited with code {outcome.raw_return_code} "
                f"timed_out={outcome.timed_out} "
                f"forwarded_signal={outcome.forwarded_signal}\n{detail}",
            )
        stderr = u.Cli.atomic_read_binary_file_receipt(
            stderr_file, required=True
        ).unwrap()
        if stderr.size != 0:
            receipt = u.Infra.publish_mod_native_artifact(artifact_root, stderr_file)
            return r[p.Cli.ProcessOutcome].fail(
                f"{command[0]} emitted unexpected stderr: {receipt.path} "
                f"size={receipt.size} sha256={receipt.sha256}"
            )
        return r[p.Cli.ProcessOutcome].ok(outcome)


__all__: list[str] = ["FlextInfraModGateRunner"]
