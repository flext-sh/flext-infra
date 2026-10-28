"""Public API facade for flext-infra.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from time import monotonic
from typing import TYPE_CHECKING, ClassVar, override

from flext_cli import u

import flext_infra
from flext_infra import (
    FlextInfraConformWiring,
    FlextInfraPreviewWiring,
    c,
    check,
    codegen,
    codemod,
    m,
    r,
    release,
    s,
    services,
    t,
    validate,
    workspace,
)
from flext_infra.services import FlextInfraCodegenHandlers, FlextInfraModHandlers

if TYPE_CHECKING:
    from flext_infra import p
    from flext_infra.docs import FlextInfraDocFormatter
    from flext_infra.workspace import FlextInfraWorkspacePropagation


class FlextInfra(
    FlextInfraConformWiring,
    FlextInfraPreviewWiring,
    FlextInfraCodegenHandlers,
    FlextInfraModHandlers,
    s[t.JsonDict],
):
    """Thin public FLEXT facade over infra services."""

    app_name: ClassVar[str] = "flext-infra"

    @staticmethod
    def bootstrap_candidate(
        request: m.Infra.CandidateBootstrapCommand,
    ) -> p.Result[bool]:
        """Compose typed declarations, conform planner and one atomic publisher.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        identity = flext_infra.u.Infra.exact_worktree_root(
            request.repository_root.expanduser().absolute(),
        )
        if identity.failure:
            return r[bool].from_failure(identity)
        source_root = identity.value.repo_root
        inputs = flext_infra.u.Infra.load_codegen_inputs(source_root)
        if inputs.failure:
            return r[bool].from_failure(inputs)
        observed = workspace.FlextInfraWorkspaceDetector.load_workspace_spec(
            source_root,
            inputs=inputs.value,
        )
        if observed.failure:
            return r[bool].from_failure(observed)
        return services.FlextInfraCandidateBootstrapService(
            planner=codegen.FlextInfraCodegenConform.Generate(
                repository_root=source_root,
                state=m.Infra.CodegenConformState(repository_root=source_root),
            ),
        ).execute(source_root, observed.value, request)

    def rope_workspace(
        self,
        repository_root: Path | None = None,
        rope_repository_root: Path | None = None,
    ) -> p.Infra.RopeWorkspaceDsl:
        """Open the public Rope workspace DSL directly from the facade.

        Returns:
            The resulting ``p.Infra.RopeWorkspaceDsl``.

        """
        # NOTE (multi-agent, flext-wkii.17.24): Rope reads its source policy
        # directly from config.Infra at the service boundary.

        resolved_root = (
            self.repository_root if repository_root is None else repository_root
        )
        return workspace.FlextInfraRopeWorkspace.open_workspace(
            resolved_root, rope_repository_root=rope_repository_root
        )

    @staticmethod
    def check(request: m.Infra.RunCommand) -> p.Result[bool]:
        """Compose one shared Rope cycle and execute every requested gate.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        return check.FlextInfraWorkspaceChecker(
            repository_root=request.repository_root,
        ).execute_payload(request)

    @staticmethod
    def check_integrity(request: m.Infra.RunCommand) -> p.Result[bool]:
        """Run the same check engine over its declared runtime-integrity subset.

        Returns:
            p.Result[bool]: the integrity verdict of the declared subset.

        """
        return check.FlextInfraWorkspaceChecker(
            repository_root=request.repository_root
        ).execute_integrity(request)

    @staticmethod
    def check_report(
        request: m.Infra.RunCommand,
    ) -> p.Result[m.Infra.CheckReportSummary]:
        """Collect typed invocation facts; each gate retains its actual verdict.

        Returns:
            p.Result[m.Infra.CheckReportSummary]: the collected check report.

        """
        return check.FlextInfraWorkspaceChecker(
            repository_root=request.repository_root
        ).execute_report(request)

    @staticmethod
    def codegen_census(request: m.Infra.CodegenCommand) -> p.Result[str]:
        """Run the read-only census within the facade-owned Rope lifecycle.

        Returns:
            The resulting ``p.Result[str]``.

        """
        return codegen.FlextInfraCodegenCensus(
            repository_root=request.repository_root,
            apply_changes=request.apply,
            check_only=request.check_only,
            dry_run=request.dry_run,
            output_format=request.output_format,
        ).execute()

    @staticmethod
    def codegen_auto_fix(request: m.Infra.CodegenAutoFixCommand) -> p.Result[str]:
        """Run namespace fixes within the facade-owned Rope lifecycle.

        Returns:
            The resulting ``p.Result[str]``.

        """
        return codegen.FlextInfraCodegenFixer(
            repository_root=request.repository_root,
            apply_changes=request.apply,
            check_only=request.check_only,
            dry_run=request.dry_run,
            output_format=request.output_format,
            selected_projects=request.projects,
            rules_only=request.rules_only,
        ).execute()

    def release_run(self, request: m.Infra.ReleaseRunCommand) -> p.Result[bool]:
        """Run one release phase with the facade-wired conform ports.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        ownership = request.ownership
        if request.checkpoint_ref is not None:
            selected = flext_infra.FlextInfraGitService.lane_ownership(
                m.Infra.GitLaneOwnershipRequest(
                    repo_root=request.root,
                    checkpoint_ref=request.checkpoint_ref,
                ),
            )
            if selected.failure:
                return r[bool].from_failure(selected)
            ownership = selected.value
        return release.FlextInfraReleaseOrchestrator(
            repository_root=request.repository_root,
            apply_changes=request.apply_changes,
            check_only=request.check_only,
            dry_run=request.dry_run,
            output_format=request.output_format,
            project_filter=request.project_filter,
            report_path=request.report_path,
            output_dir=request.output_dir,
            selected_projects=request.projects,
            phase=request.phase,
            index=request.index,
            pr_title=request.pr_title,
            ownership=ownership,
            conform_collaborators=self.codegen_conform_collaborators(),
        ).execute()

    def workspace_propagate(
        self,
        command: FlextInfraWorkspacePropagation,
    ) -> p.Result[bool]:
        """Propagate to every member with the facade-wired conform ports.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        return command.model_copy(
            update={"conform_collaborators": self.codegen_conform_collaborators()},
        ).execute()

    def docs_format(self, command: FlextInfraDocFormatter) -> p.Result[bool]:
        """Format docs through the facade-bound markdown format gate.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        return command.model_copy(
            update={"format_gate": self.markdown_format_gate},
        ).execute()

    @staticmethod
    def apply_renames(
        request: m.Infra.ApplyRenamesInput,
    ) -> p.Result[m.Infra.ApplyRenamesReport]:
        """Compose and run one explicitly supplied CSV rename campaign.

        Returns:
            The resulting ``p.Result[m.Infra.ApplyRenamesReport]``.

        """
        return codemod.FlextInfraApplyRenames().run(request)

    @staticmethod
    def validate_namespace(
        request: m.Infra.NamespaceValidateCommand,
    ) -> p.Result[m.Infra.ValidationReport]:
        """Validate one project against the rule catalog.

        Returns:
            The resulting ``p.Result[m.Infra.ValidationReport]``.

        """
        return validate.FlextInfraNamespaceValidator(
            repository_root=request.repository_root,
        ).build_report()

    @override
    def mod(
        self,
        request: p.Infra.ModRequest,
        progress: p.Infra.ModProgress,
    ) -> p.Result[t.Cli.ResultValue]:
        """Compose repository codemod runs in the declared dependency order.

        Returns:
            The first repository failure, or acceptance of every governed run.

        """
        root = flext_infra.u.Infra.resolve_repository_root_or_cwd(
            request.repository_root
        )
        governed = frozenset(flext_infra.u.Infra.governed_project_roots(root))
        if governed == {root}:
            return FlextInfraModHandlers.mod(self, request, progress)
        inputs = flext_infra.u.Infra.load_codegen_inputs(root)
        if inputs.failure:
            return r[t.Cli.ResultValue].from_failure(inputs)
        observed = workspace.FlextInfraWorkspaceDetector.load_workspace_spec(
            root, inputs=inputs.value
        )
        if observed.failure:
            return r[t.Cli.ResultValue].from_failure(observed)
        references = tuple(
            repository
            for repository in (
                observed.value.repository,
                *observed.value.subprojects,
            )
            if (root / repository.path).resolve() in governed
        )
        by_root = {
            (root / repository.path).resolve(): repository for repository in references
        }
        if len(by_root) != len(references) or frozenset(by_root) != governed:
            return r[t.Cli.ResultValue].fail(
                "mod workspace declarations differ from governed repositories: "
                f"duplicate_paths={len(references) - len(by_root)}; "
                f"missing={tuple(sorted(governed.difference(by_root)))}"
            )
        ordered = flext_infra.u.Infra.workspace_dependency_order(root, references)
        by_distribution = {
            repository.distribution: repository_root
            for repository_root, repository in by_root.items()
        }
        for distribution in ordered:
            repository_root = by_distribution[distribution]
            progress.emit(f"mod: repository {distribution} root={repository_root}")
            child_request = (
                request
                if repository_root == root
                else m.Infra.ModCommand(
                    repository_root=repository_root,
                    apply=request.apply,
                    check=request.check,
                    dry_run_mode=request.dry_run_mode,
                    consumer_roots=request.consumer_roots,
                )
            )
            completed = FlextInfraModHandlers.mod(self, child_request, progress)
            if completed.failure:
                return completed
        return r[t.Cli.ResultValue].ok(value=True)

    @staticmethod
    def mod_text(request: m.Infra.ModTextCommand) -> p.Result[t.Cli.ResultValue]:
        """Compose the standalone authenticated text-rule replay.

        Returns:
            The resulting ``p.Result[t.Cli.ResultValue]``.

        """
        root = flext_infra.u.Infra.resolve_repository_root_or_cwd(
            request.repository_root
        )
        return codemod.FlextInfraModTextGateEngine.run(root, apply=request.apply)

    @staticmethod
    def mod_text_candidate(
        request: m.Infra.ModTextCommand,
    ) -> p.Result[t.Cli.ResultValue]:
        """Replay one repository-declared candidate using this healthy provider.

        Returns:
            The resulting ``p.Result[t.Cli.ResultValue]``.

        """
        source_root = flext_infra.u.Infra.resolve_repository_root_or_cwd(
            request.repository_root
        )
        observed = workspace.FlextInfraWorkspaceDetector.load_workspace_spec(
            source_root
        )
        if observed.failure:
            return r[t.Cli.ResultValue].from_failure(observed)
        targets = observed.value.candidate_bootstrap_targets
        if len(targets) != 1:
            return r[t.Cli.ResultValue].fail(
                "mod-text-candidate requires exactly one candidate_bootstrap_target",
            )
        # Non-strict: a missing declared worktree is graded by the exact-root
        # owner's typed failure instead of escaping as FileNotFoundError.
        identity = flext_infra.u.Infra.exact_worktree_root(
            (source_root / targets[0].path).resolve(),
        )
        if identity.failure:
            return r[t.Cli.ResultValue].from_failure(identity)
        return codemod.FlextInfraModTextGateEngine.run(
            identity.value.repo_root,
            apply=request.apply,
        )

    @staticmethod
    def _project_captured_runtime(
        resolved: Path,
        root: Path,
    ) -> p.Result[tuple[m.Infra.CodegenInputs, m.Infra.WorkspaceRuntimeContext]]:
        """Load the root codegen policy and elect the workspace runtime context.

        Args:
            resolved: Resolved project working directory.
            root: Resolved Git repository root.

        Returns:
            The captured inputs with their elected runtime, or the first failure.

        """
        captured = flext_infra.u.Infra.load_codegen_inputs(root)
        if captured.failure:
            return r[
                tuple[m.Infra.CodegenInputs, m.Infra.WorkspaceRuntimeContext]
            ].from_failure(captured)
        runtime = workspace.FlextInfraWorkspaceDetector.resolution_context(resolved)
        if runtime.failure:
            return r[
                tuple[m.Infra.CodegenInputs, m.Infra.WorkspaceRuntimeContext]
            ].from_failure(runtime)
        return r[tuple[m.Infra.CodegenInputs, m.Infra.WorkspaceRuntimeContext]].ok(
            (captured.value, runtime.value),
        )

    @staticmethod
    def _project_workspace_target(
        root: Path,
        captured: m.Infra.CodegenInputs,
    ) -> p.Result[tuple[m.Infra.WorkspaceSpec, m.Infra.RepositoryConformTarget]]:
        """Load the workspace spec and resolve its conform target.

        Args:
            root: Resolved Git repository root.
            captured: Loaded codegen inputs.

        Returns:
            The workspace spec with its conform target, or the first failure.

        """
        observed = workspace.FlextInfraWorkspaceDetector.load_workspace_spec(
            root,
            inputs=captured,
        )
        if observed.failure:
            return r[
                tuple[m.Infra.WorkspaceSpec, m.Infra.RepositoryConformTarget]
            ].from_failure(observed)
        target = workspace.FlextInfraWorkspaceDetector.conform_target(
            root,
            observed.value,
            inputs=captured,
        )
        if target.failure:
            return r[
                tuple[m.Infra.WorkspaceSpec, m.Infra.RepositoryConformTarget]
            ].from_failure(target)
        return r[tuple[m.Infra.WorkspaceSpec, m.Infra.RepositoryConformTarget]].ok(
            (observed.value, target.value),
        )

    @staticmethod
    def workspace_tests(
        request: m.Infra.WorkspaceTestsRequest,
        *,
        execution_mode: c.Infra.PytestExecutionMode = (
            c.Infra.PytestExecutionMode.GLOBAL_INCREMENTAL
        ),
    ) -> p.Result[int]:
        """Require original global primary source proof before native test engines.

        Ordinary test failures retain their original first status while every
        selected repository is reached. Interruptions and infrastructure errors
        stop dispatch with their native status; configuration failures escape.
        Admission, discovery and member execution share this operation's clock.
        FULL executes the complete applicable suite once in each project context
        without Testmon, an incremental pre-run or database access.

        Returns:
            The first failing native test status, or zero after every success.

        """
        started_at_monotonic = monotonic()
        context = FlextInfra.project_context(request.repository_root).unwrap()
        if context.identity is None or context.runtime is None:
            return r[int].fail(f"tests require a project context: {context.cwd}")
        root = context.identity.repo_root
        workspace_root = context.runtime.runtime_root
        admitted = flext_infra.u.Infra.git_require_green_check_receipt(
            workspace_root,
            flext_infra.u.Infra.load_codegen_inputs(workspace_root).unwrap().spec.make,
            phase=c.Infra.CheckPhase.PRIMARY,
            plan_global_targets=check.FlextInfraWorkspaceChecker(
                repository_root=workspace_root,
            ).plan_global_targets,
        )
        if admitted.failure:
            return r[int].from_failure(admitted)
        observed = workspace.FlextInfraWorkspaceDetector.load_workspace_spec(
            workspace_root,
        ).unwrap()
        governed = frozenset(flext_infra.u.Infra.governed_project_roots(workspace_root))
        references = tuple(
            repository
            for repository in (observed.repository, *observed.subprojects)
            if (workspace_root / repository.path).resolve() in governed
        )
        ordered = flext_infra.u.Infra.workspace_dependency_order(
            workspace_root, references
        )
        by_distribution = {
            repository.distribution: (workspace_root / repository.path).resolve()
            for repository in references
        }
        if frozenset(by_distribution.values()) != governed:
            return r[int].fail(
                "tests workspace declarations differ from governed roots"
            )
        status = 0
        for distribution in ordered:
            selected = by_distribution[distribution]
            if request.scope == c.Infra.CodegenConformScope.SELF and selected != root:
                continue
            u.Cli.info(f"tests: repository {distribution} root={selected}")
            project = (
                context
                if selected == root
                else FlextInfra.project_context(selected).unwrap()
            )
            outcome = validate.FlextInfraPytestRunner.execute_project_context(
                project,
                started_at_monotonic=started_at_monotonic,
                execution_mode=execution_mode,
            )
            u.Cli.info(f"tests: repository {distribution} exit={outcome}")
            if outcome:
                if outcome != c.Infra.Pytest.ExitCode.TESTS_FAILED:
                    return r[int].ok(outcome)
                if not status:
                    status = outcome
        return r[int].ok(status)

    @staticmethod
    def project_context(cwd: Path) -> p.Result[m.Infra.WorkspaceProjectContext]:
        """Derive Git, workspace, and effective project facts from ``cwd``.

        Returns:
            The resulting ``p.Result[m.Infra.WorkspaceProjectContext]``.

        """
        resolved = cwd.expanduser().resolve()
        if not resolved.is_dir():
            return r[m.Infra.WorkspaceProjectContext].fail(
                f"project context cwd is not a directory: {resolved}",
            )
        identity = flext_infra.u.Infra.git_identity(
            m.Infra.GitRepoRequest(repo_root=resolved)
        )
        if identity.failure:
            return r[m.Infra.WorkspaceProjectContext].ok(
                m.Infra.WorkspaceProjectContext(cwd=resolved),
            )
        root = identity.value.repo_root
        captured_runtime = FlextInfra._project_captured_runtime(resolved, root)
        if captured_runtime.failure:
            return r[m.Infra.WorkspaceProjectContext].from_failure(captured_runtime)
        captured, runtime = captured_runtime.value
        workspace_target = FlextInfra._project_workspace_target(root, captured)
        if workspace_target.failure:
            return r[m.Infra.WorkspaceProjectContext].from_failure(workspace_target)
        workspace, target = workspace_target.value
        return r[m.Infra.WorkspaceProjectContext].ok(
            m.Infra.WorkspaceProjectContext(
                cwd=resolved,
                identity=identity.value,
                workspace=workspace,
                target=target,
                governed=True,
                runtime=runtime,
            ),
        )

    @override
    def execute(self) -> p.Result[t.JsonDict]:
        """Execute a lightweight facade health report.

        Returns:
            The resulting ``p.Result[t.JsonDict]``.

        """
        report: t.JsonDict = {
            "service": "flext-infra",
            "status": "ok",
            "repository_root": str(self.repository_root),
            "apply_changes": self.apply_changes,
        }
        return r[t.JsonDict].ok(report)


infra: FlextInfra = FlextInfra.fetch_global()
"""Shared FlextInfra facade instance."""


__all__: list[str] = ["FlextInfra", "infra"]
