"""Public API facade for flext-infra.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from functools import partial
from pathlib import Path
from time import monotonic
from typing import TYPE_CHECKING, ClassVar, override

from flext_infra import (
    FlextInfraGitService,
    c,
    check,
    codegen,
    codemod,
    m,
    p,
    r,
    release,
    s,
    services,
    t,
    u,
    validate,
    workspace,
)
from flext_infra._conform import FlextInfraConformWiring
from flext_infra._preview import FlextInfraPreviewWiring
from flext_infra._utilities import FlextInfraUtilitiesReleaseForge
from flext_infra.codemod._rename import FlextInfraCodemodRenameSymbols
from flext_infra.services import FlextInfraCodegenHandlers, FlextInfraModHandlers

if TYPE_CHECKING:
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
        request: p.Infra.CandidateBootstrapCommand,
    ) -> p.Result[bool]:
        """Compose typed declarations, conform planner and one atomic publisher.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        identity = u.Infra.exact_worktree_root(
            request.repository_root.expanduser().absolute(),
        )
        if identity.failure:
            return r[bool].from_failure(identity)
        source_root = identity.value.repo_root
        inputs = u.Infra.load_codegen_inputs(source_root)
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
        session = workspace.FlextInfraRopeWorkspace.open_workspace(
            resolved_root, rope_repository_root=rope_repository_root
        )
        session.semantic_rename_planner = FlextInfraCodemodRenameSymbols
        session.model_envelope_checker = partial(
            FlextInfraModHandlers.model_envelope_diagnostics, session.repository_root
        )
        return session

    @staticmethod
    def check(request: p.Infra.RunCommand) -> p.Result[bool]:
        """Compose one shared Rope cycle and execute every requested gate.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        return check.FlextInfraWorkspaceChecker(
            repository_root=request.repository_root,
        ).execute_payload(request)

    @staticmethod
    def check_integrity(request: p.Infra.RunCommand) -> p.Result[bool]:
        """Run the same check engine over its declared runtime-integrity subset.

        Returns:
            p.Result[bool]: the integrity verdict of the declared subset.

        """
        return check.FlextInfraWorkspaceChecker(
            repository_root=request.repository_root
        ).execute_integrity(request)

    @staticmethod
    def check_report(
        request: p.Infra.RunCommand,
    ) -> p.Result[p.Infra.CheckReportSummary]:
        """Collect typed invocation facts; each gate retains its actual verdict.

        Returns:
            p.Result[p.Infra.CheckReportSummary]: the collected check report.

        """
        return check.FlextInfraWorkspaceChecker(
            repository_root=request.repository_root
        ).execute_report(request)

    @staticmethod
    def codegen_census(request: p.Infra.CodegenCommand) -> p.Result[str]:
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
    def codegen_auto_fix(request: p.Infra.CodegenAutoFixCommand) -> p.Result[str]:
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

    def release_run(self, request: p.Infra.ReleaseRunCommand) -> p.Result[bool]:
        """Run one release phase with the facade-wired conform ports.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        ownership = request.ownership
        if request.checkpoint_ref is not None:
            selected = FlextInfraGitService.lane_ownership(
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
            release_forge=FlextInfraUtilitiesReleaseForge,
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
        request: p.Infra.ApplyRenamesInput,
    ) -> p.Result[p.Infra.ApplyRenamesReport]:
        """Compose and run one explicitly supplied CSV rename campaign.

        Returns:
            The resulting ``p.Result[p.Infra.ApplyRenamesReport]``.

        """
        return codemod.FlextInfraApplyRenames().run(request)

    @staticmethod
    def validate_namespace(
        request: p.Infra.NamespaceValidateCommand,
    ) -> p.Result[p.Infra.ValidationReport]:
        """Validate one project against the rule catalog.

        Returns:
            The resulting ``p.Result[p.Infra.ValidationReport]``.

        """
        return validate.FlextInfraNamespaceValidator(
            repository_root=request.repository_root,
        ).build_report()

    @staticmethod
    def _mod_selection(request: p.Infra.ModCommand) -> p.Result[bool]:
        """Accept a full-catalog run or a selection of laws the catalog derives.

        A selector-free run converges the complete active catalog (ADR-028
        Decision 18 item 2); a selection only narrows the focus.

        Returns:
            Acceptance, the catalog failure, or the unknown-law failure.

        """
        if request.laws is None:
            return r[bool].ok(value=True)
        catalog = u.Infra.enforcement_catalog()
        if catalog.failure:
            return r[bool].from_failure(catalog)
        unknown = frozenset(request.laws).difference(
            claim.id for claim in catalog.value.claims if claim.active
        )
        if unknown:
            return r[bool].fail(
                "refactor mod --laws names laws no active owner claims: "
                + ", ".join(sorted(unknown))
            )
        return r[bool].ok(value=True)

    @staticmethod
    def _mod_selected_roots(
        root: Path,
        request: p.Infra.ModCommand,
        governed: frozenset[Path],
    ) -> p.Result[frozenset[Path]]:
        """Resolve ``projects`` into governed repository roots before any run.

        Returns:
            Every governed root without ``projects``, the selected roots, or
            the first resolution or out-of-workspace failure.

        """
        if not request.projects:
            return r[frozenset[Path]].ok(governed)
        resolved = u.Infra.resolve_projects(root, tuple(request.projects))
        if resolved.failure:
            return r[frozenset[Path]].from_failure(resolved)
        selected = frozenset(project.path.resolve() for project in resolved.value)
        outside = selected.difference(governed)
        if outside:
            return r[frozenset[Path]].fail(
                "mod --projects selects repositories outside the governed "
                f"workspace: {tuple(sorted(str(item) for item in outside))}"
            )
        return r[frozenset[Path]].ok(selected)

    @staticmethod
    def _mod_repository_order(
        root: Path,
        governed: frozenset[Path],
    ) -> p.Result[tuple[Sequence[str], Mapping[str, Path]]]:
        """Order the governed repositories by their declared dependencies.

        Returns:
            The distributions in dependency order with each repository root,
            or the input, workspace or declaration-mismatch failure.

        """
        result_type = r[tuple[Sequence[str], Mapping[str, Path]]]
        inputs = u.Infra.load_codegen_inputs(root)
        if inputs.failure:
            return result_type.from_failure(inputs)
        observed = workspace.FlextInfraWorkspaceDetector.load_workspace_spec(
            root, inputs=inputs.value
        )
        if observed.failure:
            return result_type.from_failure(observed)
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
            return result_type.fail(
                "mod workspace declarations differ from governed repositories: "
                f"duplicate_paths={len(references) - len(by_root)}; "
                f"missing={tuple(sorted(governed.difference(by_root)))}"
            )
        ordered = u.Infra.workspace_dependency_order(root, references)
        by_distribution = {
            repository.distribution: repository_root
            for repository_root, repository in by_root.items()
        }
        return result_type.ok((ordered, by_distribution))

    @staticmethod
    def _mod_child_request(
        request: p.Infra.ModCommand,
        repository_root: Path,
        *,
        root: Path,
    ) -> p.Infra.ModCommand:
        """Scope one repository run of a workspace mod request.

        Returns:
            The original request for the workspace root, otherwise the same
            selection bound to ``repository_root`` without ``projects``.

        """
        if repository_root == root:
            return request
        return m.Infra.ModCommand(
            repository_root=repository_root,
            projects=None,
            verbose=request.verbose,
            check=request.check,
            dry_run_mode=request.dry_run_mode,
            rename_plan=request.rename_plan,
            consumer_roots=request.consumer_roots,
            rule_id=request.rule_id,
            rule_ids=request.rule_ids,
            laws=request.laws,
        )

    @override
    def mod(
        self,
        request: p.Infra.ModCommand,
        progress: p.Infra.ModProgress,
    ) -> p.Result[t.Cli.ResultValue]:
        """Compose repository codemod runs in the declared dependency order.

        Declared failures arrive as typed Results: a typed failure born for
        one module is converted at its mod phase boundary, where
        ``c.Infra.MOD_FAILURE_MODULE_KEY`` attributes it for quarantine. Every
        other exception escapes raw with its traceback. ``projects`` selects
        exactly those repositories and an unknown name fails before any run.
        A mutating run stops at its first failed prerequisite; later
        repositories are not reported as executed. A check or dry-run mutates
        nothing, so every selected repository runs and one aggregated failure
        names each failing repository. A selector-free run converges the
        complete active catalog; laws, rule IDs, one rule or a rename plan
        only narrow the focus (ADR-028 Decision 18 item 2). Laws are
        validated once against the derived enforcement catalog; each
        repository expands them into its own planned rules.

        Returns:
            The selection failure, the first repository failure for a mutating
            run, the aggregated failure naming every failing repository for
            check/dry-run, or acceptance of every selected run.

        """
        root = u.Infra.resolve_repository_root_or_cwd(request.repository_root)
        governed = frozenset(u.Infra.governed_project_roots(root))
        selected = self._mod_selection(request).flat_map(
            lambda _: self._mod_selected_roots(root, request, governed)
        )
        if selected.failure:
            return r[t.Cli.ResultValue].from_failure(selected)
        selected_roots = selected.value
        if governed == frozenset({root}):
            return super().mod(request, progress)
        order = self._mod_repository_order(root, governed)
        if order.failure:
            return r[t.Cli.ResultValue].from_failure(order)
        ordered, by_distribution = order.value
        failures: list[tuple[str, str]] = []
        for distribution in ordered:
            repository_root = by_distribution[distribution]
            if repository_root not in selected_roots:
                continue
            progress.emit(f"mod: repository {distribution} root={repository_root}")
            completed = super().mod(
                self._mod_child_request(request, repository_root, root=root),
                progress,
            )
            if completed.success:
                continue
            if request.apply:
                return completed
            failures.append((distribution, completed.error or "mod failed"))
        if failures:
            return r[t.Cli.ResultValue].fail(
                f"mod failed in {len(failures)} repositories: "
                + "; ".join(f"{name}: {error}" for name, error in failures)
            )
        return r[t.Cli.ResultValue].ok(value=True)

    @staticmethod
    def mod_text(request: p.Infra.ModTextCommand) -> p.Result[t.Cli.ResultValue]:
        """Compose the standalone authenticated text-rule replay.

        Returns:
            The resulting ``p.Result[t.Cli.ResultValue]``.

        """
        root = u.Infra.resolve_repository_root_or_cwd(request.repository_root)
        return codemod.FlextInfraModTextGateEngine.run(
            root, apply=request.apply, rule_ids=request.rule_ids
        )

    @staticmethod
    def mod_text_candidate(
        request: p.Infra.ModTextCommand,
    ) -> p.Result[t.Cli.ResultValue]:
        """Replay one repository-declared candidate using this healthy provider.

        Returns:
            The resulting ``p.Result[t.Cli.ResultValue]``.

        """
        source_root = u.Infra.resolve_repository_root_or_cwd(request.repository_root)
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
        identity = u.Infra.exact_worktree_root(
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
    ) -> p.Result[tuple[p.Infra.CodegenInputs, p.Infra.WorkspaceRuntimeContext]]:
        """Load the root codegen policy and elect the workspace runtime context.

        Args:
            resolved: Resolved project working directory.
            root: Resolved Git repository root.

        Returns:
            The captured inputs with their elected runtime, or the first failure.

        """
        captured = u.Infra.load_codegen_inputs(root)
        if captured.failure:
            return r[
                tuple[p.Infra.CodegenInputs, p.Infra.WorkspaceRuntimeContext]
            ].from_failure(captured)
        runtime = workspace.FlextInfraWorkspaceDetector.resolution_context(resolved)
        if runtime.failure:
            return r[
                tuple[p.Infra.CodegenInputs, p.Infra.WorkspaceRuntimeContext]
            ].from_failure(runtime)
        return r[tuple[p.Infra.CodegenInputs, p.Infra.WorkspaceRuntimeContext]].ok(
            (captured.value, runtime.value),
        )

    @staticmethod
    def _project_workspace_target(
        root: Path,
        captured: p.Infra.CodegenInputs,
    ) -> p.Result[tuple[p.Infra.WorkspaceSpec, p.Infra.RepositoryConformTarget]]:
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
                tuple[p.Infra.WorkspaceSpec, p.Infra.RepositoryConformTarget]
            ].from_failure(observed)
        target = workspace.FlextInfraWorkspaceDetector.conform_target(
            root,
            observed.value,
            inputs=captured,
        )
        if target.failure:
            return r[
                tuple[p.Infra.WorkspaceSpec, p.Infra.RepositoryConformTarget]
            ].from_failure(target)
        return r[tuple[p.Infra.WorkspaceSpec, p.Infra.RepositoryConformTarget]].ok(
            (observed.value, target.value),
        )

    @staticmethod
    def workspace_tests(
        request: p.Infra.WorkspaceTestsRequest,
        *,
        execution_mode: c.Infra.PytestExecutionMode = (
            c.Infra.PytestExecutionMode.GLOBAL_INCREMENTAL
        ),
    ) -> p.Result[int]:
        """Execute native tests in the selected project contexts.

        Ordinary test failures retain their original first status while every
        selected repository is reached. Interruptions and infrastructure errors
        stop dispatch with their native status; configuration failures escape.
        Discovery and member execution share this operation's clock.
        FULL executes the complete applicable suite once in each project context
        without Testmon, an incremental pre-run or database access.
        A declared file selects only this repository through that same runner.

        Returns:
            The first failing native test status, or zero after every success.

        """
        started_at_monotonic = monotonic()
        context = FlextInfra.project_context(request.repository_root).unwrap()
        if context.identity is None or context.runtime is None:
            return r[int].fail(f"tests require a project context: {context.cwd}")
        root = context.identity.repo_root
        workspace_root = context.runtime.runtime_root
        if (
            request.file is not None
            or request.scope == c.Infra.CodegenConformScope.SELF
        ):
            return r[int].ok(
                validate.FlextInfraPytestRunner.execute_project_context(
                    context,
                    started_at_monotonic=started_at_monotonic,
                    execution_mode=(
                        c.Infra.PytestExecutionMode.FULL
                        if request.file is not None
                        else execution_mode
                    ),
                    target_file=request.file,
                )
            )
        observed = workspace.FlextInfraWorkspaceDetector.load_workspace_spec(
            workspace_root,
        ).unwrap()
        governed = frozenset(u.Infra.governed_project_roots(workspace_root))
        references = tuple(
            repository
            for repository in (observed.repository, *observed.subprojects)
            if (workspace_root / repository.path).resolve() in governed
        )
        ordered = u.Infra.workspace_dependency_order(workspace_root, references)
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
    def project_context(cwd: Path) -> p.Result[p.Infra.WorkspaceProjectContext]:
        """Derive Git, workspace, and effective project facts from ``cwd``.

        Returns:
            The resulting ``p.Result[p.Infra.WorkspaceProjectContext]``.

        """
        resolved = cwd.expanduser().resolve()
        if not resolved.is_dir():
            return r[p.Infra.WorkspaceProjectContext].fail(
                f"project context cwd is not a directory: {resolved}",
            )
        identity = u.Infra.git_identity(m.Infra.GitRepoRequest(repo_root=resolved))
        if identity.failure:
            return r[p.Infra.WorkspaceProjectContext].ok(
                m.Infra.WorkspaceProjectContext(cwd=resolved),
            )
        root = identity.value.repo_root
        captured_runtime = FlextInfra._project_captured_runtime(resolved, root)
        if captured_runtime.failure:
            return r[p.Infra.WorkspaceProjectContext].from_failure(captured_runtime)
        captured, runtime = captured_runtime.value
        workspace_target = FlextInfra._project_workspace_target(root, captured)
        if workspace_target.failure:
            return r[p.Infra.WorkspaceProjectContext].from_failure(workspace_target)
        workspace, target = workspace_target.value
        return r[p.Infra.WorkspaceProjectContext].ok(
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
