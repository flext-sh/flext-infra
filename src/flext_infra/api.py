"""Public API facade for flext-infra.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, override

from flext_infra import c, m, r, s, t, u
from flext_infra._conform_wiring import FlextInfraConformWiring
from flext_infra._preview_wiring import FlextInfraPreviewWiring
from flext_infra.check import FlextInfraWorkspaceChecker
from flext_infra.codegen import (
    FlextInfraCodegenCensus,
    FlextInfraCodegenConform,
    FlextInfraCodegenFixer,
    FlextInfraCodegenMiseArtifacts,
    FlextInfraCodegenPipeline,
    FlextInfraCodegenPreconditions,
    FlextInfraCodegenTransaction,
    FlextInfraMiseArtifactsFiles,
)
from flext_infra.codemod import (
    FlextInfraAccessorRenamePhase,
    FlextInfraApplyRenames,
    FlextInfraCodemodBatchApply,
    FlextInfraCodemodSemanticApply,
    FlextInfraDuplicateApplyPhase,
    FlextInfraImportNormalizationPhase,
    FlextInfraModTextGateEngine,
    FlextInfraNamespaceRelocationPhase,
)
from flext_infra.services import FlextInfraCandidateBootstrapService
from flext_infra.validate import FlextInfraNamespaceValidator
from flext_infra.workspace import (
    FlextInfraRopeWorkspace,
    FlextInfraWorkspaceDetector,
    FlextInfraWorkspaceEnvironmentMixin,
)

if TYPE_CHECKING:
    from flext_infra import p
    from flext_infra.codegen import FlextInfraCodegenProjectNew
    from flext_infra.docs import FlextInfraDocFormatter
    from flext_infra.release import FlextInfraReleaseOrchestrator
    from flext_infra.workspace import FlextInfraWorkspacePropagation


class FlextInfra(
    FlextInfraWorkspaceEnvironmentMixin,
    FlextInfraConformWiring,
    FlextInfraPreviewWiring,
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
        identity = u.Infra.exact_worktree_root(
            request.repository_root.expanduser().absolute(),
        )
        if identity.failure:
            return r[bool].from_failure(identity)
        source_root = identity.value.repo_root
        inputs = u.Infra.load_codegen_inputs(source_root)
        if inputs.failure:
            return r[bool].from_failure(inputs)
        workspace = FlextInfraWorkspaceDetector.load_workspace_spec(
            source_root,
            inputs=inputs.value,
        )
        if workspace.failure:
            return r[bool].from_failure(workspace)
        planner = FlextInfraCodegenConform(
            repository_root=source_root,
            ports=None,
        )
        producer = FlextInfraCodegenPreconditions.capture_producer(
            source_root,
            entrypoint=planner.plan_repositories,
            collaborators=(
                FlextInfraCandidateBootstrapService._plan,
                FlextInfraCandidateBootstrapService,
                FlextInfraMiseArtifactsFiles.write_publication,
            ),
        )
        if producer.failure:
            return r[bool].from_failure(producer)
        planner.producer = producer.value
        return FlextInfraCandidateBootstrapService(
            # The campaign only plans through conform; it publishes through its
            # own transaction and never runs the complete surface.
            planner=planner,
            producer=producer.value,
            transaction=FlextInfraCodegenTransaction(
                FlextInfraCodegenMiseArtifacts(repository_root=source_root),
                producer=producer.value,
            ),
        ).execute(source_root, workspace.value, request, inputs.value.sources)

    @override
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
        return FlextInfraRopeWorkspace.open_workspace(
            resolved_root, rope_repository_root=rope_repository_root
        )

    @staticmethod
    def check(request: m.Infra.RunCommand) -> p.Result[bool]:
        """Compose one shared Rope cycle and execute every requested gate.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        return FlextInfraWorkspaceChecker(
            repository_root=request.repository_root,
        ).execute_payload(request)

    @staticmethod
    def codegen_census(request: m.Infra.CodegenCommand) -> p.Result[str]:
        """Run the read-only census within the facade-owned Rope lifecycle.

        Returns:
            The resulting ``p.Result[str]``.

        """
        return FlextInfraCodegenCensus(
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
        return FlextInfraCodegenFixer(
            repository_root=request.repository_root,
            apply_changes=request.apply,
            check_only=request.check_only,
            dry_run=request.dry_run,
            output_format=request.output_format,
            selected_projects=request.project_names,
            rules_only=request.rules_only,
        ).execute()

    def codegen_pipeline(self, request: m.Infra.CodegenCommand) -> p.Result[str]:
        """Run the codegen pipeline with the facade-wired conform ports.

        Returns:
            The resulting ``p.Result[str]``.

        """
        return FlextInfraCodegenPipeline(
            repository_root=request.repository_root,
            apply_changes=request.apply,
            check_only=request.check_only,
            dry_run=request.dry_run,
            output_format=request.output_format,
            conform_collaborators=self.codegen_conform_collaborators(),
        ).execute()

    def codegen_conform(
        self,
        request: m.Infra.CodegenConformRequest,
        initial_workspace: m.Infra.WorkspaceSpec | None = None,
    ) -> p.Result[m.Infra.CodegenResult]:
        """Conform generated files with the facade-wired cross-family ports.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenResult]``.

        """
        return FlextInfraCodegenConform.execute_request(
            request,
            initial_workspace,
            ports=(
                None
                if c.Infra.CodegenConformMode(request.mode)
                is c.Infra.CodegenConformMode.CHECK
                else self.codegen_conform_collaborators()
            ),
        )

    def codegen_new(
        self,
        command: FlextInfraCodegenProjectNew,
    ) -> p.Result[m.Infra.CodegenResult]:
        """Scaffold one project through conform with the facade-wired ports.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenResult]``.

        """
        return command.model_copy(
            update={"conform_collaborators": self.codegen_conform_collaborators()},
        ).execute()

    def release_run(self, command: FlextInfraReleaseOrchestrator) -> p.Result[bool]:
        """Run one release phase with the facade-wired conform ports.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        return command.model_copy(
            update={"conform_collaborators": self.codegen_conform_collaborators()},
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
        return FlextInfraApplyRenames().run(request)

    def mod(
        self,
        request: m.Infra.ModCommand,
        progress: p.Infra.ModProgress,
    ) -> p.Result[t.Cli.ResultValue]:
        """Compose the codemod use case from typed config and real adapters.

        Returns:
            The resulting ``p.Result[t.Cli.ResultValue]``.

        """
        root = u.Infra.resolve_repository_root_or_cwd(request.repository_root)
        selected = u.Infra.load_refactor_csv_campaigns(root)
        if selected.failure:
            return r[t.Cli.ResultValue].from_failure(selected)
        config = selected.value
        config_dir = root / c.CONFIG_DIR_NAME
        config_root = config_dir.resolve()
        repository_root = root.resolve()
        campaigns: list[m.Infra.ApplyRenamesInput] = []
        for declared in config.campaigns:
            csv = config_dir / declared.csv
            if not csv.resolve().is_relative_to(config_root):
                return r[t.Cli.ResultValue].fail(
                    f"CSV campaign driver escapes config directory: {csv}",
                )
            campaign_roots = tuple(
                (root / value).resolve() for value in declared.roots
            ) or (root,)
            for path in campaign_roots:
                if not path.resolve().is_relative_to(repository_root):
                    return r[t.Cli.ResultValue].fail(
                        f"CSV campaign scan root escapes repository: {path}",
                    )
            campaigns.append(
                m.Infra.ApplyRenamesInput(
                    repository_root=root,
                    csv=str(csv),
                    roots=tuple(str(path) for path in campaign_roots),
                    apply=request.apply
                    and not request.check
                    and not request.dry_run_mode,
                    bindings=declared.bindings,
                    text_globs=declared.text_globs,
                    python_documentation=declared.python_documentation,
                    exclude_globs=declared.exclude_globs,
                ),
            )
        source_preview = self.source_preview(root)
        with self.rope_workspace(root) as rope:
            rename_plan = request.rename_plan or config.semantic_plan
            if rename_plan is not None:
                renamed = FlextInfraCodemodSemanticApply.consume_rename_plan(
                    request.model_copy(update={"rename_plan": rename_plan}),
                    rope,
                    source_preview,
                )
                if renamed.failure:
                    return r[t.Cli.ResultValue].from_failure(renamed)
                rope.refresh()
            return FlextInfraCodemodBatchApply(
                workspace_factory=self.rope_workspace,
                source_preview=source_preview,
                repository_root=root,
                apply_changes=request.apply,
                check_only=request.check,
                dry_run=request.dry_run_mode,
                rename_runner=FlextInfraApplyRenames(),
                progress=progress,
                rope=rope,
                rename_inputs=tuple(campaigns),
                phase_callbacks=(
                    FlextInfraImportNormalizationPhase(),
                    FlextInfraNamespaceRelocationPhase(),
                    FlextInfraDuplicateApplyPhase(),
                    FlextInfraAccessorRenamePhase(source_preview=source_preview),
                ),
            ).execute()

    @staticmethod
    def validate_namespace(
        request: m.Infra.NamespaceValidateCommand,
    ) -> p.Result[m.Infra.ValidationReport]:
        """Validate one project against the rule catalog.

        Returns:
            The resulting ``p.Result[m.Infra.ValidationReport]``.

        """
        return FlextInfraNamespaceValidator(
            repository_root=request.repository_root,
        ).build_report()

    @staticmethod
    def mod_text(request: m.Infra.ModTextCommand) -> p.Result[t.Cli.ResultValue]:
        """Compose the standalone authenticated text-rule replay.

        Returns:
            The resulting ``p.Result[t.Cli.ResultValue]``.

        """
        root = u.Infra.resolve_repository_root_or_cwd(request.repository_root)
        return FlextInfraModTextGateEngine.run(root, apply=request.apply)

    @staticmethod
    def mod_text_candidate(
        request: m.Infra.ModTextCommand,
    ) -> p.Result[t.Cli.ResultValue]:
        """Replay one repository-declared candidate using this healthy provider.

        Returns:
            The resulting ``p.Result[t.Cli.ResultValue]``.

        """
        source_root = u.Infra.resolve_repository_root_or_cwd(request.repository_root)
        workspace = FlextInfraWorkspaceDetector.load_workspace_spec(source_root)
        if workspace.failure:
            return r[t.Cli.ResultValue].from_failure(workspace)
        targets = workspace.value.candidate_bootstrap_targets
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
        return FlextInfraModTextGateEngine.run(
            identity.value.repo_root,
            apply=request.apply,
        )

    @staticmethod
    def _project_git_identity(
        resolved: Path,
    ) -> p.Result[m.Infra.GitIdentityReport | None]:
        """Return the repository Git identity, or ``None`` outside a repository.

        Args:
            resolved: Resolved project working directory.

        Returns:
            The Git identity report, or ``None`` when no Git identity exists.

        """
        identity = u.Infra.git_identity(m.Infra.GitRepoRequest(repo_root=resolved))
        if identity.failure:
            return r[m.Infra.GitIdentityReport | None].ok(value=None)
        return r[m.Infra.GitIdentityReport | None].ok(value=identity.value)

    @staticmethod
    def _project_captured_runtime(
        resolved: Path,
        root: Path,
    ) -> p.Result[t.Pair[m.Infra.CodegenInputs, m.Infra.WorkspaceRuntimeContext]]:
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
                t.Pair[m.Infra.CodegenInputs, m.Infra.WorkspaceRuntimeContext]
            ].from_failure(captured)
        runtime = FlextInfraWorkspaceDetector.resolution_context(resolved)
        if runtime.failure:
            return r[
                t.Pair[m.Infra.CodegenInputs, m.Infra.WorkspaceRuntimeContext]
            ].from_failure(runtime)
        return r[t.Pair[m.Infra.CodegenInputs, m.Infra.WorkspaceRuntimeContext]].ok(
            (captured.value, runtime.value),
        )

    @staticmethod
    def _project_workspace_target(
        root: Path,
        captured: m.Infra.CodegenInputs,
    ) -> p.Result[t.Pair[m.Infra.WorkspaceSpec, m.Infra.RepositoryConformTarget]]:
        """Load the workspace spec and resolve its conform target.

        Args:
            root: Resolved Git repository root.
            captured: Loaded codegen inputs.

        Returns:
            The workspace spec with its conform target, or the first failure.

        """
        workspace = FlextInfraWorkspaceDetector.load_workspace_spec(
            root,
            inputs=captured,
        )
        if workspace.failure:
            return r[
                t.Pair[m.Infra.WorkspaceSpec, m.Infra.RepositoryConformTarget]
            ].from_failure(workspace)
        target = FlextInfraWorkspaceDetector.conform_target(
            root,
            workspace.value,
            inputs=captured,
        )
        if target.failure:
            return r[
                t.Pair[m.Infra.WorkspaceSpec, m.Infra.RepositoryConformTarget]
            ].from_failure(target)
        return r[t.Pair[m.Infra.WorkspaceSpec, m.Infra.RepositoryConformTarget]].ok(
            (workspace.value, target.value),
        )

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
        identity = FlextInfra._project_git_identity(resolved)
        if identity.value is None:
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
