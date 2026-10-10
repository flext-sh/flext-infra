"""Fleet verbs: one mutating Make verb carried to every governed member at once.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Annotated, override

from flext_infra import FlextInfraWorkspaceDetector, c, config, m, p, r, s, u


class FlextInfraWorkspaceFleetVerbs(s[m.Infra.LifecycleReport]):
    """Run one mutating verb in every governed member, concurrently.

    Each member runs its own public Make verb in its own repository, so the
    verb rewrites only that member and behaves exactly as a member-local run.
    The members are independent git roots: they run in
    ``Infra.codegen.fleet_workers`` concurrent processes, each captured in
    its own receipt, and the report keeps declared order. The first failed
    member in declared order fails the run with its captured output.
    """

    verb: Annotated[
        c.Infra.FleetVerb,
        m.Field(description="Mutating verb carried to every governed member"),
    ]

    @override
    def execute(self) -> p.Result[m.Infra.LifecycleReport]:
        """Run the verb in every governed member and publish the receipts.

        Returns:
            The typed receipts on success, otherwise the first member failure.

        """
        root = self.root.expanduser().resolve()
        loaded = FlextInfraWorkspaceDetector.load_workspace_spec(root)
        if loaded.failure:
            return r[m.Infra.LifecycleReport].from_failure(loaded)
        workspace = loaded.value
        if workspace.repository.role is not c.Infra.MakeProfile.WORKSPACE:
            return r[m.Infra.LifecycleReport].fail(
                f"fleet verbs require a workspace root: {root}",
            )
        scope = tuple(
            root / member.path for member in u.Infra.mutable_flext_members(workspace)
        )
        # The service contract stores enum values; str() reads either form.
        verb = str(self.verb)
        output_dir = root / c.Infra.FLEET_REPORT_RELATIVE_PATH.with_suffix("")
        pending = tuple(
            m.Infra.LifecycleReceipt(
                command=(c.Infra.MAKE, verb),
                cwd=cwd,
                output_file=output_dir / f"{cwd.name}-{verb}.log",
            )
            for cwd in scope
        )
        workers = max(1, min(config.Infra.codegen.fleet_workers, len(pending)))
        u.Cli.info(f"[fleet {verb}] {len(pending)} members, {workers} workers")
        with ThreadPoolExecutor(max_workers=workers) as pool:
            receipts = tuple(pool.map(self._run_member, pending))
        report = m.Infra.LifecycleReport(
            workspace_root=root,
            scope=scope,
            receipts=receipts,
        )
        published = u.Infra.publish_refactor_report_evidence(
            root,
            report,
            relative_path=c.Infra.FLEET_REPORT_RELATIVE_PATH,
        )
        if published.failure:
            return r[m.Infra.LifecycleReport].from_failure(published)
        failed = next(
            (receipt for receipt in receipts if receipt.error is not None),
            None,
        )
        if failed is not None:
            return r[m.Infra.LifecycleReport].fail(
                f"{failed.error}\n{self._captured(failed.output_file)}",
            )
        return r[m.Infra.LifecycleReport].ok(report)

    @staticmethod
    def _run_member(receipt: m.Infra.LifecycleReceipt) -> m.Infra.LifecycleReceipt:
        """Run one member's verb into its receipt file and report its status.

        Returns:
            The receipt with the observed exit and the failure, if any.

        """
        started = time.monotonic()
        run = u.Cli.run_to_file(
            receipt.command,
            receipt.output_file,
            cwd=receipt.cwd,
            options=m.Cli.ProcessOptions(
                remove_env_keys=c.Infra.ORCHESTRATOR_REMOVE_ENV_KEYS,
            ),
        )
        elapsed = time.monotonic() - started
        if run.failure:
            u.Cli.status(
                receipt.command[-1], receipt.cwd.name, result=False, elapsed=elapsed
            )
            return receipt.model_copy(update={"error": run.error})
        succeeded = u.Cli.process_succeeded(run.value)
        u.Cli.status(
            receipt.command[-1], receipt.cwd.name, result=succeeded, elapsed=elapsed
        )
        error = (
            None
            if succeeded
            else (
                f"failed ({run.value.raw_return_code}): "
                f"{' '.join(receipt.command)} in {receipt.cwd}; "
                f"timed_out={run.value.timed_out}, "
                f"forwarded_signal={run.value.forwarded_signal}; "
                f"output={receipt.output_file}"
            )
        )
        return receipt.model_copy(
            update={"exit_code": run.value.raw_return_code, "error": error},
        )

    @staticmethod
    def _captured(output_file: Path) -> str:
        """Return a failed member's captured output for the causal failure.

        Returns:
            The captured combined output, or the read failure itself.

        """
        read = u.Cli.files_read_text(output_file)
        return read.value if read.success else str(read.error)


__all__: list[str] = ["FlextInfraWorkspaceFleetVerbs"]
