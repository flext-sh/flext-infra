"""Fleet verbs: one mutating Make verb carried through runtime dependency waves.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, override

from flext_core import t
from flext_infra import c, m, p, r, s, u
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector
from flext_infra.workspace.environment_provenance import (
    FlextInfraWorkspaceEnvironmentProvenance,
)
from flext_infra.workspace.lifecycle import FlextInfraWorkspaceLifecycle


class FlextInfraWorkspaceFleetVerbs(s[m.Infra.LifecycleReport]):
    """Run one mutating verb serially in dependency-first member order.

    Each member's selected Makefile runs from the containing workspace root.
    The runtime graph owns dependency waves and lexical ties within each wave.
    A failed invocation stops subsequent members; the report retains the
    complete planned scope, including invocations not reached after a failure.
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
                    repository_root=root / member.path,
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
        receipts = list(pending)
        original: p.Result[p.Cli.ProcessOutcome] | None = None
        attempted = 0
        for index, receipt in enumerate(pending):
            receipts[index], original = FlextInfraWorkspaceLifecycle.run_receipt(
                receipt,
                (),
            )
            attempted += 1
            if original.failure:
                break
        u.Cli.info(
            f"[fleet {verb}] attempted={attempted} declared={len(pending)}",
        )
        report = m.Infra.LifecycleReport(
            workspace_root=root,
            scope=scope,
            receipts=tuple(receipts),
        )
        published = u.Infra.publish_refactor_report_evidence(
            root,
            report,
            relative_path=c.Infra.FLEET_REPORT_RELATIVE_PATH,
        )
        if published.failure:
            if original is not None and original.failure:
                u.Cli.error(f"receipt publication failed: {published.error}")
                if original.exception is not None:
                    original.exception.add_note(
                        f"receipt publication failed: {published.error}",
                    )
                return result_type.from_failure(original)
            return result_type.from_failure(published)
        if original is not None and original.failure:
            return result_type.from_failure(original)
        return result_type.ok(report)

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
        authenticated = FlextInfraWorkspaceEnvironmentProvenance.editable_members(root)
        if authenticated.failure:
            return r[t.SequenceOf[m.Infra.RepositoryRef]].from_failure(authenticated)
        eligible = tuple(
            member
            for member in authenticated.value
            if requested is None or member.name in requested
        )
        by_distribution = {member.distribution: member for member in eligible}
        ordered = tuple(
            by_distribution[name]
            for name in u.Infra.workspace_dependency_order(root, eligible)
        )
        return r[t.SequenceOf[m.Infra.RepositoryRef]].ok(ordered)


__all__: list[str] = ["FlextInfraWorkspaceFleetVerbs"]
