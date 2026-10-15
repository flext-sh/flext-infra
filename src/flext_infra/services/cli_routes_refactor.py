"""Refactor CLI route ownership.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
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
    def _authenticated_rename_state(
        root: Path,
        output: Path,
        target: Path,
    ) -> p.Result[m.Cli.AtomicFileState]:
        """Authenticate the planned artifact destination inside its workspace.

        Args:
            root: Resolved governed workspace root.
            output: Workspace-relative artifact destination.
            target: Resolved artifact destination.

        Returns:
            The observed atomic file state, or the first containment failure.

        """
        if not target.is_relative_to(root):
            return r[m.Cli.AtomicFileState].fail(
                "rename plan output escapes workspace",
            )
        return u.Cli.atomic_read_binary_file_state(root / output)

    @staticmethod
    def _planned_rename_plan(
        root: Path,
        selections: m.Infra.SemanticRenameSelections,
    ) -> p.Result[m.Infra.SemanticRenamePlan]:
        """Build the inventory-derived rename plan inside a Rope workspace.

        Args:
            root: Resolved governed workspace root.
            selections: Explicit domain rename decisions.

        Returns:
            The planned artifact, or the planning failure.

        """
        with infra.rope_workspace(root) as workspace:
            planned = FlextInfraCodemodSemanticApply.build_rename_plan(
                root,
                workspace,
                selections,
            )
        if planned.failure:
            return r[m.Infra.SemanticRenamePlan].from_failure(planned)
        return planned

    @staticmethod
    def _validated_rename_content(
        before: m.Cli.AtomicFileState,
        planned: m.Infra.SemanticRenamePlan,
        target: Path,
        root: Path,
    ) -> p.Result[str]:
        """Reject aliased outputs, foreign workspaces and non-round-trip content.

        Args:
            before: Observed atomic state of the artifact destination.
            planned: Freshly built rename plan.
            target: Resolved artifact destination.
            root: Resolved governed workspace root.

        Returns:
            The exact serialized artifact content, or the first conflict failure.

        """
        if any(
            state.path == target
            or (
                before.inode is not None
                and (state.device, state.inode) == (before.device, before.inode)
            )
            for state in planned.candidate.inputs
        ):
            return r[str].fail(
                "rename plan output aliases a governed candidate input",
            )
        if before.content is not None:
            previous = m.Infra.SemanticRenamePlan.model_validate_json(before.content)
            if previous.candidate.workspace != root:
                return r[str].fail(
                    "rename plan output belongs to another workspace",
                )
        content = planned.model_dump_json(indent=2, round_trip=True)
        if m.Infra.SemanticRenamePlan.model_validate_json(content) != planned:
            return r[str].fail(
                "rename artifact did not round-trip exactly",
            )
        return r[str].ok(value=content)

    @staticmethod
    def _published_rename_content(
        before: m.Cli.AtomicFileState,
        content: str,
        inputs: t.VariadicTuple[m.Cli.AtomicFileState],
    ) -> p.Result[bool]:
        """Authenticate candidate inputs, then write the artifact atomically.

        Args:
            before: Observed atomic state of the artifact destination.
            content: Validated serialized artifact content.
            inputs: Governed candidate inputs requiring authentication.

        Returns:
            Whether the artifact was published, or the first failure.

        """
        authenticated = u.Cli.atomic_verify_binary_file_states(inputs)
        if authenticated.failure:
            return r[bool].from_failure(authenticated)
        written = u.Cli.atomic_write_text_file_guarded(before, content + "\n")
        if written.failure:
            return r[bool].from_failure(written)
        return r[bool].ok(value=True)

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
        observed = FlextInfraRefactorRoutes._authenticated_rename_state(
            root, request.output, target
        )
        if observed.failure:
            return r[t.Cli.ResultValue].from_failure(observed)
        selections = m.Infra.SemanticRenameSelections.model_validate_json(
            request.decisions
        )
        planned = FlextInfraRefactorRoutes._planned_rename_plan(root, selections)
        if planned.failure:
            return r[t.Cli.ResultValue].from_failure(planned)
        content = FlextInfraRefactorRoutes._validated_rename_content(
            observed.value, planned.value, target, root
        )
        if content.failure:
            return r[t.Cli.ResultValue].from_failure(content)
        published = FlextInfraRefactorRoutes._published_rename_content(
            observed.value, content.value, planned.value.candidate.inputs
        )
        if published.failure:
            return r[t.Cli.ResultValue].from_failure(published)
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
