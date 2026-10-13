"""Refactor CLI route ownership.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import ClassVar

from flext_cli import cli

from flext_infra import c, infra, m, p, r, t, u
from flext_infra.codegen import FlextInfraCodegenProtocolModels
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
        root = request.repository_root.resolve()
        target = (root / request.output).resolve()
        if not target.is_relative_to(root):
            return r[t.Cli.ResultValue].fail("rename plan output escapes workspace")
        selections = m.Infra.SemanticRenameSelections.model_validate_json(
            request.decisions
        )
        with infra.rope_workspace(root) as workspace:
            planned = FlextInfraCodemodSemanticApply.build_rename_plan(
                root, workspace, selections
            )
        if planned.failure:
            return r[t.Cli.ResultValue].from_failure(planned)
        content = planned.value.model_dump_json(indent=2, round_trip=True)
        if m.Infra.SemanticRenamePlan.model_validate_json(content) != planned.value:
            return r[t.Cli.ResultValue].fail(
                "rename artifact did not round-trip exactly"
            )
        written = u.Cli.atomic_write_text_file(target, content + "\n")
        if written.failure:
            return r[t.Cli.ResultValue].from_failure(written)
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
                infra.source_preview(root),
            ).map(lambda accepted: accepted)

    @staticmethod
    def execute_move_module(
        request: m.Infra.ModuleMoveCommand,
    ) -> p.Result[t.Cli.ResultValue]:
        """Move a source module through the public workspace and semantic engine.

        Returns:
            The completed semantic relocation result.
        """
        with infra.rope_workspace(request.repository_root) as workspace:
            target = u.Infra.move_module(
                workspace.rope_project,
                request.source_file,
                request.destination_directory,
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
    def execute_mod(request: m.Infra.ModCommand) -> p.Result[t.Cli.ResultValue]:
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

    refactor_routes: ClassVar[t.VariadicTuple[m.Cli.ResultCommandRoute]] = (
        m.Cli.ResultCommandRoute(
            name="rename-plan",
            help_text="Generate a native semantic rename artifact from explicit domain decisions",
            model_cls=m.Infra.SemanticRenamePlanCommand,
            handler=execute_rename_plan,
        ),
        m.Cli.ResultCommandRoute(
            name="rename-preview",
            help_text="Validate an authenticated rename artifact in the native candidate runtime",
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
            help_text="Run a Rope-only workspace census for Python objects",
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
            name="protocol-models",
            help_text=(
                "Assemble the member's generated structural protocols from "
                "its validated models; dry-run reports drift"
            ),
            model_cls=FlextInfraCodegenProtocolModels,
            handler=FlextInfraCodegenProtocolModels.execute_command,
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
