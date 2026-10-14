"""Fleet verbs: one mutating Make verb carried through runtime dependency waves.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Annotated, override

from flext_core import t
from flext_infra import c, m, p, r, s, u
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector


class FlextInfraWorkspaceFleetVerbs(s[m.Infra.LifecycleReport]):
    """Run one mutating verb serially in dependency-first member order.

    Each member's selected Makefile runs from the containing workspace root.
    The runtime graph owns dependency waves and lexical ties within each wave.
    A failed invocation stops subsequent members; the report retains the
    complete declared scope and receipts only for attempted invocations.
    """

    verb: Annotated[
        c.Infra.FleetVerb,
        m.Field(description="Mutating verb carried to every governed member"),
    ]
    members: Annotated[
        t.StrSequence | None,
        m.Field(
            description=(
                "Restrict the run to the named workspace members; an "
                "undeclared name fails loud instead of being ignored"
            ),
        ),
    ] = None

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
        selected_members = self._selected_members(workspace, root)
        if selected_members.failure:
            return r[m.Infra.LifecycleReport].from_failure(selected_members)
        # The service contract stores enum values; str() reads either form.
        verb = str(self.verb)
        pending = self._pending_receipts(root, selected_members.value, verb)
        if pending.failure:
            return r[m.Infra.LifecycleReport].from_failure(pending)
        return self._published_report(
            root,
            selected_members.value,
            pending.value,
            verb,
        )

    @staticmethod
    def _pending_receipts(
        root: Path,
        members: t.SequenceOf[m.Infra.RepositoryRef],
        verb: str,
    ) -> p.Result[t.SequenceOf[m.Infra.LifecycleReceipt]]:
        """Build one serial receipt per selected member on its own Makefile.

        Returns:
            The pending receipts, or the failure naming the missing Makefile.

        """
        result_type = r[t.SequenceOf[m.Infra.LifecycleReceipt]]
        for member in members:
            makefile = root / member.path / c.Infra.MAKEFILE_FILENAME
            if not makefile.is_file():
                return result_type.fail(
                    f"fleet member Makefile is missing: {makefile}",
                )
        output_dir = root / c.Infra.FLEET_REPORT_RELATIVE_PATH.with_suffix("")
        return result_type.ok(
            tuple(
                m.Infra.LifecycleReceipt(
                    command=(
                        c.Infra.MAKE,
                        "-f",
                        (member.path / c.Infra.MAKEFILE_FILENAME).as_posix(),
                        verb,
                    ),
                    cwd=root,
                    output_file=output_dir / f"{member.distribution}-{verb}.log",
                )
                for member in members
            ),
        )

    def _published_report(
        self,
        root: Path,
        members: t.SequenceOf[m.Infra.RepositoryRef],
        pending: t.SequenceOf[m.Infra.LifecycleReceipt],
        verb: str,
    ) -> p.Result[m.Infra.LifecycleReport]:
        """Run the pending receipts serially and publish the report evidence.

        Returns:
            The published lifecycle report, or the first member failure with
            its captured output.

        """
        result_type = r[m.Infra.LifecycleReport]
        scope = tuple(root / member.path for member in members)
        u.Cli.info(f"[fleet {verb}] {len(pending)} members, serial dependency order")
        attempted: list[m.Infra.LifecycleReceipt] = []
        for receipt in pending:
            observed = self._run_member(receipt)
            attempted.append(observed)
            if observed.error is not None:
                break
        receipts = tuple(attempted)
        u.Cli.info(
            f"[fleet {verb}] attempted={len(receipts)} declared={len(pending)}",
        )
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
            return result_type.from_failure(published)
        failed = next(
            (receipt for receipt in receipts if receipt.error is not None),
            None,
        )
        if failed is not None:
            return result_type.fail(
                f"{failed.error}\n{self._captured(failed.output_file)}",
            )
        return result_type.ok(report)

    @staticmethod
    def _run_member(receipt: m.Infra.LifecycleReceipt) -> m.Infra.LifecycleReceipt:
        """Run one member's verb into its receipt file and report its status.

        Returns:
            The receipt with the observed exit and the failure, if any.

        """
        started = time.monotonic()
        member_name = Path(receipt.command[-2]).parent.name
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
                receipt.command[-1], member_name, result=False, elapsed=elapsed
            )
            return receipt.model_copy(update={"error": run.error})
        succeeded = u.Cli.process_succeeded(run.value)
        u.Cli.status(
            receipt.command[-1], member_name, result=succeeded, elapsed=elapsed
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
            update={
                "outcome": m.Cli.ProcessOutcome.model_validate(
                    run.value,
                    from_attributes=True,
                ),
                "error": error,
            },
        )

    @staticmethod
    def _captured(output_file: Path) -> str:
        """Return a failed member's captured output for the causal failure.

        Returns:
            The captured combined output, or the read failure itself.

        """
        read = u.Cli.files_read_text(output_file)
        return read.value if read.success else str(read.error)

    def _selected_members(
        self,
        workspace: m.Infra.WorkspaceSpec,
        root: Path,
    ) -> p.Result[t.SequenceOf[m.Infra.RepositoryRef]]:
        """Apply the member filter to the declared mutable members.

        Returns:
            The selected members in dependency order, or the failure naming
            every undeclared requested member.
        """
        declared = tuple(u.Infra.mutable_flext_members(workspace))
        if not declared:
            return r[t.SequenceOf[m.Infra.RepositoryRef]].fail(
                "fleet verbs require declared mutable members",
            )
        requested = frozenset(self.members) if self.members else None
        if requested is not None:
            unknown = sorted(requested - {member.name for member in declared})
            if unknown:
                return r[t.SequenceOf[m.Infra.RepositoryRef]].fail(
                    "fleet verbs: undeclared member name(s): " + ", ".join(unknown),
                )
        by_distribution = {member.distribution: member for member in declared}
        ordered = tuple(
            by_distribution[name]
            for name in u.Infra.workspace_dependency_order(root, declared)
        )
        if requested is None:
            return r[t.SequenceOf[m.Infra.RepositoryRef]].ok(ordered)
        return r[t.SequenceOf[m.Infra.RepositoryRef]].ok(
            tuple(member for member in ordered if member.name in requested),
        )


__all__: list[str] = ["FlextInfraWorkspaceFleetVerbs"]
