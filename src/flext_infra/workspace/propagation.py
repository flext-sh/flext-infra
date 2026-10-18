"""Member propagation: this workspace's flext-infra, one pull request per member.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, override

from flext_infra import c, config, m, p, r, s, u
from flext_infra.codegen import FlextInfraCodegenConform
from flext_infra.workspace import FlextInfraWorkspaceDetector


class FlextInfraWorkspacePropagation(s[bool]):
    """Carry this workspace's flext-infra projections to every member.

    Each governed member is conformed inside its own
    publication lane; a member whose projections do not change
    publishes nothing. The first failure ends the run, nothing is merged, and
    every member checkout is left on its integration branch, so a rerun
    continues the same lanes and commits nothing new.
    """

    conform_collaborators: Annotated[
        m.Infra.CodegenConformPorts | None,
        m.Field(
            exclude=True,
            description=(
                "Docs port bound by the FlextInfra facade; the settling "
                "conform fails before any effect without it"
            ),
        ),
    ] = None

    def codegen_conform_collaborators(self) -> p.Infra.CodegenConformPorts | None:
        """Return the capabilities already bound to this propagation invocation.

        Returns:
            The exact supplied ports, including explicit absence.
        """
        return self.conform_collaborators

    @override
    def execute(self) -> p.Result[bool]:
        """Propagate to every generated member in declared order.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        root = self.root
        loaded = FlextInfraWorkspaceDetector.load_workspace_spec(root)
        if loaded.failure:
            return r[bool].from_failure(loaded)
        workspace = loaded.value
        if workspace.repository.role is not c.Infra.MakeProfile.WORKSPACE:
            return r[bool].fail(f"propagation requires a workspace root: {root}")
        revision = u.Cli.capture([c.Infra.GIT, "rev-parse", c.Infra.GIT_HEAD], cwd=root)
        if revision.failure:
            return r[bool].from_failure(revision)
        propagated = self._propagate_members(workspace, revision.value.strip())
        if propagated.failure:
            return propagated
        for consumer in workspace.external_consumers:
            propagated = self._propagate_external_consumer(
                workspace,
                consumer,
                revision.value.strip(),
            )
            if propagated.failure:
                return propagated
        return r[bool].ok(value=True)

    def _propagate_members(
        self,
        workspace: m.Infra.WorkspaceSpec,
        revision: str,
    ) -> p.Result[bool]:
        """Propagate mutable internal FLEXT projections without resolving locks.

        Returns:
            True when every member propagated, else the first failure.

        """
        members = u.Infra.mutable_flext_members(workspace)
        for member in members:
            propagated = self._propagate_member(workspace, member, revision)
            if propagated.failure:
                return propagated
        return r[bool].ok(value=True)

    def _propagate_external_consumer(
        self,
        workspace: m.Infra.WorkspaceSpec,
        consumer: m.Infra.ExternalConsumerSpec,
        revision: str,
    ) -> p.Result[bool]:
        """Advance one external consumer's lane through its own make verbs.

        The consumer's checkout keeps its governance: propagation only runs
        the consumer's declared canonical verbs inside its own lane branch and
        publishes nothing when the run changes nothing.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        consumer_root = consumer.root
        if not consumer_root.is_dir():
            return r[bool].fail(
                f"external consumer root does not exist: {consumer_root}",
            )
        base = u.Infra.resolve_integration_branch(
            consumer_root,
            policy_branch=config.Infra.codegen.branch_policy.integration_branch,
            declared=consumer.integration_branch,
        )
        if base.failure:
            return r[bool].from_failure(base)
        body = self._write_external_body(workspace, consumer, revision)
        if body.failure:
            return r[bool].from_failure(body)
        published = u.Infra.git_publish_lane(
            m.Infra.GitLaneRequest(
                repo_root=consumer_root,
                branch=c.Infra.PROPAGATION_BRANCH,
                base=base.value,
                subject=c.Infra.PROPAGATION_COMMIT_SUBJECT,
                body_file=body.value,
            ),
            lambda: self._settle_external_consumer(consumer),
        )
        if published.failure:
            return published
        self.logger.info(
            "propagation_external_consumer",
            consumer=consumer.name,
            published=published.value,
        )
        if not published.value:
            return published
        return u.Cli.run_checked([c.Infra.GIT, "switch", base.value], cwd=consumer_root)

    @staticmethod
    def _settle_external_consumer(
        consumer: m.Infra.ExternalConsumerSpec,
    ) -> p.Result[bool]:
        """Run the consumer's declared canonical verbs once, in order.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        verbs: list[str] = ["gen"]
        if consumer.fix_namespace:
            verbs.append("fix-namespace")
        if consumer.fix_accessors:
            verbs.append("fix-accessors")
        verbs.extend(("fix", "fmt"))
        for verb in verbs:
            settled = u.Cli.run_checked(
                [c.Infra.MAKE, verb],
                cwd=consumer.root,
            )
            if settled.failure:
                return r[bool].from_failure(settled)
        return r[bool].ok(value=True)

    def _report_directory(self) -> p.Result[Path]:
        """Ensure and return the propagation report directory.

        Returns:
            The resulting ``p.Result[Path]``.

        """
        return u.Cli.ensure_dir(
            u.Cli.resolve_report_dir(
                self.root,
                c.Infra.PROJECT,
                c.Infra.PROPAGATION_REPORT_KEY,
            ),
        )

    def _write_external_body(
        self,
        workspace: m.Infra.WorkspaceSpec,
        consumer: m.Infra.ExternalConsumerSpec,
        revision: str,
    ) -> p.Result[Path]:
        """Write the external consumer's pull-request body under the reports.

        Returns:
            The resulting ``p.Result[Path]``.

        """
        directory = self._report_directory()
        if directory.failure:
            return r[Path].from_failure(directory)
        body = directory.value / f"external-{consumer.name}.md"
        written = u.Cli.files_write_text(
            body,
            f"# Propagate the workspace flext-infra to {consumer.name}\n\n"
            f"`make propagate` at `{workspace.repository.name}` {revision} "
            "advanced this consumer's lane through its own canonical verbs "
            "(gen, declared namespace/accessor repairs, fix, fmt). Nothing else"
            " changed.\n",
        )
        return written.map(lambda _written: body)

    def _propagate_member(
        self,
        workspace: m.Infra.WorkspaceSpec,
        member: m.Infra.RepositoryRef,
        revision: str,
    ) -> p.Result[bool]:
        """Publish one member's settled projections, then return it to its base.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        member_root = self.root / member.path
        base = u.Infra.resolve_integration_branch(
            member_root,
            policy_branch=config.Infra.codegen.branch_policy.integration_branch,
            declared=(
                workspace.integration.branch
                if workspace.integration is not None
                else None
            ),
        )
        if base.failure:
            return r[bool].from_failure(base)
        body = self._write_body(workspace, member, revision)
        if body.failure:
            return r[bool].from_failure(body)
        published = u.Infra.git_publish_lane(
            m.Infra.GitLaneRequest(
                repo_root=member_root,
                branch=c.Infra.PROPAGATION_BRANCH,
                base=base.value,
                subject=c.Infra.PROPAGATION_COMMIT_SUBJECT,
                body_file=body.value,
            ),
            lambda: FlextInfraCodegenConform.execute_request(
                m.Infra.CodegenConformRequest(
                    root=member_root,
                    scope=c.Infra.CodegenConformScope.ALL,
                    mode=c.Infra.CodegenConformMode.APPLY,
                ),
                execution_context=self,
            ).map(lambda _conformed: True),
        )
        if published.failure:
            return published
        self.logger.info(
            "propagation_member",
            member=member.name,
            published=published.value,
        )
        if not published.value:
            return published
        return u.Cli.run_checked([c.Infra.GIT, "switch", base.value], cwd=member_root)

    def _write_body(
        self,
        workspace: m.Infra.WorkspaceSpec,
        member: m.Infra.RepositoryRef,
        revision: str,
    ) -> p.Result[Path]:
        """Write the member's pull-request body under the workspace reports.

        Returns:
            The resulting ``p.Result[Path]``.

        """
        directory = self._report_directory()
        if directory.failure:
            return directory
        body = directory.value / f"{member.name}.md"
        written = u.Cli.files_write_text(
            body,
            f"# Propagate the workspace flext-infra to {member.name}\n\n"
            f"`make propagate` at `{workspace.repository.name}` {revision} "
            "settled this member's managed projections (codegen conform). "
            "Dependency resolution remains exclusive to explicit `make upg`.\n",
        )
        return written.map(lambda _written: body)


__all__: list[str] = ["FlextInfraWorkspacePropagation"]
