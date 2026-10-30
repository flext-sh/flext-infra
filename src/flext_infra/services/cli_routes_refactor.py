"""Refactor CLI route ownership.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import ClassVar

from flext_cli import cli

from flext_infra import c, infra, m, p, r, t, u
from flext_infra.codemod import (
    FlextInfraCodemodAstScan,
    FlextInfraCodemodSemanticApply,
    FlextInfraCodemodSnapshotRefresh,
)
from flext_infra.refactor import (
    FlextInfraNamespaceEnforcer,
    FlextInfraRefactorViolationsSweep,
    FlextInfraWrapperRootNamespaceRefactor,
)
from flext_infra.services import FlextInfraCliModProgress
from flext_infra.transformers import FlextInfraTransformersSemanticPublication


class FlextInfraRefactorRoutes:
    """Own the complete refactor command tuple."""

    @staticmethod
    def execute_rename_plan(
        request: m.Infra.SemanticRenamePlanCommand,
    ) -> p.Result[t.Cli.ResultValue]:
        """Write an inventory-derived artifact, never a caller-authored source map.

        Returns:
            The first planning/write failure or the generated artifact receipt.

        """
        planned = FlextInfraCodemodSemanticApply.publish_rename_plan(
            request, infra.rope_workspace
        )
        if planned.failure:
            return r[t.Cli.ResultValue].from_failure(planned)
        target = (request.repository_root.resolve() / request.output).resolve()
        cli.display_text(
            f"semantic rename plan: {target} files={len(planned.value.edits)}"
        )
        return r[t.Cli.ResultValue].ok(value=True)

    @staticmethod
    def execute_rename_preview(
        request: m.Infra.SemanticRenamePreviewCommand,
    ) -> p.Result[t.Cli.ResultValue]:
        """Read the artifact through the same mod consumer and native staging port.

        Returns:
            The original authentication, runtime or lint failure, or preview proof.

        """
        root = request.repository_root.resolve()
        with infra.rope_workspace(root) as workspace:
            return FlextInfraCodemodSemanticApply.consume_rename_plan(
                m.Infra.ModCommand(
                    repository_root=root, rename_plan=request.plan, check=True
                ),
                workspace,
            )

    @staticmethod
    def execute_move_module(
        request: m.Infra.ModuleMoveCommand,
    ) -> p.Result[t.Cli.ResultValue]:
        """Move a source module through the public workspace and semantic engine.

        Returns:
            The completed semantic relocation result.

        Raises:
            ValueError: If exact-file facts or effects escape the declared repository.

        """
        root = request.repository_root.resolve()
        with infra.rope_workspace(root) as workspace:
            if request.destination_file is not None:
                if workspace.rope_repository_root.resolve() != root:
                    msg = "exact module move requires the native repository owner root"
                    raise ValueError(msg)
                source = (root / request.source_file).resolve()
                target = (root / request.destination_file).resolve()
                if not source.is_relative_to(root) or not target.is_relative_to(root):
                    msg = "exact module move owners escape the declared repository"
                    raise ValueError(msg)
                states = tuple(
                    u.Cli.atomic_read_binary_file_state(
                        resource.real_path, required=True
                    ).unwrap()
                    for resource in workspace.rope_project.get_python_files()
                )
                plans = u.Infra.plan_module_move(
                    workspace.rope_project,
                    source,
                    destination_file=target,
                    inputs=(
                        {
                            state.path: state.content.decode(c.DEFAULT_ENCODING)
                            for state in states
                            if state.content is not None
                        },
                        states,
                    ),
                )
                if plans.failure:
                    return r[t.Cli.ResultValue].from_failure(plans)
                if any(not plan.path.is_relative_to(root) for plan in plans.value):
                    return r[t.Cli.ResultValue].fail(
                        "exact module move effects escape the declared repository"
                    )
                publication = FlextInfraTransformersSemanticPublication
                published = publication.publish_semantic_artifact_plans(
                    plans.value,
                    repository_root=root,
                    options=m.Infra.SemanticPublicationOptions(
                        projection_roots=(root,),
                    ),
                )
                if published.failure:
                    return r[t.Cli.ResultValue].from_failure(published)
            elif request.destination_directory is not None:
                target = u.Infra.move_module(
                    workspace.rope_project,
                    request.source_file,
                    request.destination_directory,
                )
            else:
                return r[t.Cli.ResultValue].fail(
                    "module move requires one validated destination"
                )
        cli.display_text(str(target))
        return r[t.Cli.ResultValue].ok(value=True)

    @staticmethod
    def execute_apply_renames(
        request: m.Infra.ApplyRenamesInput,
    ) -> p.Result[t.Cli.ResultValue]:
        """Display the real rename result and preserve pending-work failure.

        Returns:
            The resulting ``p.Result[t.Cli.ResultValue]``.

        """
        result = infra.apply_renames(request)
        if result.failure:
            return r[t.Cli.ResultValue].from_failure(result)
        report = result.value
        cli.display_text(FlextInfraCliModProgress.render_rename(report))
        if report.occurrences:
            return r[t.Cli.ResultValue].fail(
                f"{report.occurrences} pending source edits",
            )
        return r[t.Cli.ResultValue].ok(value=True)

    @staticmethod
    def execute_mod(request: p.Infra.ModRequest) -> p.Result[t.Cli.ResultValue]:
        """Compose the mod use case and pass through its first failure.

        Returns:
            The resulting ``p.Result[t.Cli.ResultValue]``.

        """
        return infra.mod(request, FlextInfraCliModProgress())

    @staticmethod
    def execute_mod_text(
        request: m.Infra.ModTextCommand,
    ) -> p.Result[t.Cli.ResultValue]:
        """Replay the declared text rules without entering Rope or AST phases.

        Returns:
            The resulting ``p.Result[t.Cli.ResultValue]``.

        """
        return infra.mod_text(request)

    @staticmethod
    def execute_mod_text_candidate(
        request: m.Infra.ModTextCommand,
    ) -> p.Result[t.Cli.ResultValue]:
        """Replay a manifest-declared candidate with the healthy provider.

        Returns:
            The resulting ``p.Result[t.Cli.ResultValue]``.

        """
        return infra.mod_text_candidate(request)

    refactor_routes: ClassVar[tuple[m.Cli.ResultCommandRoute, ...]] = (
        m.Cli.ResultCommandRoute(
            name="rename-plan",
            help_text=(
                "Generate a native semantic rename artifact "
                "from explicit domain decisions"
            ),
            model_cls=m.Infra.SemanticRenamePlanCommand,
            handler=execute_rename_plan,
        ),
        m.Cli.ResultCommandRoute(
            name="rename-preview",
            help_text=(
                "Validate an authenticated rename artifact "
                "in the native candidate runtime"
            ),
            model_cls=m.Infra.SemanticRenamePreviewCommand,
            handler=execute_rename_preview,
        ),
        m.Cli.ResultCommandRoute(
            name="move-module",
            help_text="Move one module and rewire its imports through Rope",
            model_cls=m.Infra.ModuleMoveCommand,
            handler=execute_move_module,
        ),
        m.Cli.ResultCommandRoute(
            name="apply-renames",
            help_text="Check or apply an old,new CSV rename list",
            model_cls=m.Infra.ApplyRenamesInput,
            handler=execute_apply_renames,
        ),
        m.Cli.ResultCommandRoute(
            name="namespace-enforce",
            help_text="Scan workspace for namespace governance violations",
            model_cls=m.Infra.RefactorNamespaceEnforceInput,
            handler=FlextInfraNamespaceEnforcer.execute_command,
        ),
        m.Cli.ResultCommandRoute(
            name="census",
            help_text="Run the authenticated workspace object census",
            model_cls=m.Infra.CensusInput,
            handler=infra.census,
        ),
        m.Cli.ResultCommandRoute(
            name="accessor-migrate",
            help_text="Preview or apply automated get_/set_/is_ migration",
            model_cls=m.Infra.AccessorMigrationInput,
            handler=infra.accessor_migrate,
        ),
        m.Cli.ResultCommandRoute(
            name="wrapper-root-namespace",
            help_text=(
                "Normalize wrapper alias imports to wrapper root and "
                "flatten *.Core.Tests paths"
            ),
            model_cls=FlextInfraWrapperRootNamespaceRefactor,
            handler=FlextInfraWrapperRootNamespaceRefactor.execute,
        ),
        m.Cli.ResultCommandRoute(
            name="mod",
            help_text=(
                "Apply ast-grep, semantic and text rules to a proven fixed point; "
                "make check owns the lint and type verdicts"
            ),
            model_cls=m.Infra.ModCommand,
            handler=execute_mod,
        ),
        m.Cli.ResultCommandRoute(
            name="mod-text",
            help_text="Replay only authenticated declarative text rules",
            model_cls=m.Infra.ModTextCommand,
            handler=execute_mod_text,
        ),
        m.Cli.ResultCommandRoute(
            name="mod-text-candidate",
            help_text="Replay text rules in the declared candidate worktree",
            model_cls=m.Infra.ModTextCommand,
            handler=execute_mod_text_candidate,
        ),
        m.Cli.ResultCommandRoute(
            name="mod-snapshots",
            help_text=(
                "Regenerate the owned ast-grep rule-test snapshots from their "
                "tests; dry-run fails while any snapshot differs"
            ),
            model_cls=FlextInfraCodemodSnapshotRefresh,
            handler=FlextInfraCodemodSnapshotRefresh.execute_command,
        ),
        m.Cli.ResultCommandRoute(
            name="ast",
            help_text=(
                "Run the ast engine standalone: ast-grep cascade plus "
                "sed-by-list cascade (scan report; --apply reaches the "
                "mechanical fixed point); --rules selects exact CSV AST IDs "
                "only, over the complete governed corpus"
            ),
            model_cls=FlextInfraCodemodAstScan,
            handler=FlextInfraCodemodAstScan.execute_command,
        ),
        m.Cli.ResultCommandRoute(
            name=c.Infra.VIOLATIONS_SWEEP_ROUTE_NAME,
            help_text=(
                "Run an ordered --repair-verbs canonical Make sequence with "
                "audit-only --rules focus between full-catalog scans; audit runs "
                "independently for every discovered project and must preserve "
                "sources; introduced findings and partial failures remain red"
            ),
            model_cls=FlextInfraRefactorViolationsSweep,
            handler=FlextInfraRefactorViolationsSweep.execute_command,
            success_message="violations sweep introduced no finding occurrences",
        ),
    )


__all__: list[str] = ["FlextInfraRefactorRoutes"]
