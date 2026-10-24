"""Workspace-wide Rope-only census orchestration.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import time
from collections.abc import Callable
from pathlib import Path
from typing import override

from flext_cli import cli

from flext_infra import c, m, p, r, t, u
from flext_infra.codemod import (
    FlextInfraCodemodDuplicateApply,
    FlextInfraCodemodSemanticApply,
)
from flext_infra.refactor import (
    FlextInfraRefactorCensusCollectHelpersMixin,
    FlextInfraRefactorCensusRenderMixin,
)


class FlextInfraRefactorCensus(
    FlextInfraRefactorCensusCollectHelpersMixin,
    FlextInfraRefactorCensusRenderMixin,
):
    """Rope object census across the workspace: inventory and its analyses.

    Code-shape rules are rule data run by the one engine (``make mod`` and the
    codemod gate); the census reports what only a workspace object inventory
    can see — duplicate definitions, unreferenced objects and tier placement —
    and, when applying, removes the unreferenced objects it proved removable.
    Immutable census options are composed as data, independently of the service
    lifecycle and injected source-preview capability.
    """

    source_preview: t.Port[p.Infra.SourcePreview] = m.Field(
        exclude=True,
        description="Injected authenticated source preview capability",
    )
    workspace_factory: Callable[[Path, Path | None], p.Infra.RopeWorkspaceDsl] = (
        m.Field(exclude=True, description="Injected candidate Rope workspace factory")
    )

    @property
    def json_output_path(self) -> Path | None:
        """Resolved JSON export path when provided."""
        path: Path | None = u.Infra.normalize_optional_path(self.options.json_output)
        return path

    @property
    def impact_map_output_path(self) -> Path | None:
        """Resolved impact-map export path when provided."""
        path: Path | None = u.Infra.normalize_optional_path(
            self.options.impact_map_output,
        )
        return path

    def _rope_root_for_selection(self) -> Path | None:
        """Return a project-scoped Rope root when exactly one project is selected.

        Workspace-wide scans (zero or many projects) keep the canonical workspace
        root so cross-project rules such as duplicate detection remain accurate.

        Returns:
            A project-scoped Rope root when exactly one project is selected.

        """
        names: t.StrSequence | None = self.project_names
        if names is None or len(names) != 1:
            return None
        project_name: str = names[0]
        project_path: Path = self.root / project_name
        if project_path.is_dir():
            return project_path
        return None

    def _execution_reports(
        self,
    ) -> t.Pair[m.Infra.WorkspaceReport, m.Infra.WorkspaceReport]:
        """Return the final report and the pre-apply report the impact map reads.

        Returns:
            The final report and the pre-apply report the impact map reads.

        """
        started = time.monotonic()
        with self.workspace_factory(
            self.root,
            self._rope_root_for_selection(),
        ) as rope:
            constant_edits: t.VariadicTuple[m.Infra.SemanticMigrationEdit] = ()
            if (
                (rule_names := u.Infra.normalize_sequence_values(self.options.rules))
                is not None
                and c.Infra.SemanticCutoverPhase.CONSTANT_CONSUMERS in rule_names
            ):
                planned_constants = FlextInfraCodemodSemanticApply.census_constants(
                    self.root,
                    rope,
                    apply=self.apply_changes and not self.effective_dry_run,
                    workspace_factory=self.workspace_factory,
                )
                if planned_constants.failure:
                    # An unprovable constant-consumer phase is reported
                    # read-only: the census never aborts the other actionable
                    # rewrites the mod loop already applied.
                    cli.display_text(
                        "census: constant-consumers read-only "
                        f"reason={planned_constants.error or 'unprovable rewrite'}",
                    )
                else:
                    constant_edits = planned_constants.value
                    cli.display_text(
                        "census: constant-consumers "
                        f"files={len(constant_edits)} "
                        f"bindings={sum(len(edit.changes) for edit in constant_edits)} "
                        f"applied={self.apply_changes and not self.effective_dry_run}",
                    )
                rope.refresh()
            impact_report = self._collect_report(
                rope, source_preview=self.source_preview
            )
            report = impact_report
            duplicate_plans: t.VariadicTuple[m.Infra.DuplicateCurePlan] = ()
            duplicate_files = duplicate_copies = duplicate_bindings = 0
            if (
                rule_names := u.Infra.normalize_sequence_values(self.options.rules)
            ) is not None and c.Infra.CensusRule.DUPLICATE in rule_names:
                cure = FlextInfraCodemodDuplicateApply.census_duplicates(
                    self.root,
                    rope,
                    impact_report.duplicates,
                    apply=self.apply_changes and not self.effective_dry_run,
                ).unwrap()
                duplicate_plans = cure.plans
                duplicate_files = cure.files_changed
                duplicate_copies = cure.copies_removed
                duplicate_bindings = cure.bindings_rewired
                cli.display_text(
                    "census: duplicate-cure "
                    f"files={duplicate_files} "
                    f"copies={duplicate_copies} "
                    f"bindings={duplicate_bindings} "
                    f"plans={len(duplicate_plans)} "
                    f"applied={self.apply_changes and not self.effective_dry_run}",
                )
                if duplicate_files:
                    rope.reload()
                    report = self._collect_report(
                        rope, source_preview=self.source_preview
                    )
            if (
                self.apply_changes
                and not self.effective_dry_run
                and self._apply_removal_candidates(rope, report)
            ):
                rope.refresh()
                report = self._collect_report(rope, source_preview=self.source_preview)
        finalized = report.model_copy(
            update={
                "scan_duration_seconds": time.monotonic() - started,
                "constant_consumer_files": len(constant_edits),
                "constant_consumer_bindings": sum(
                    len(edit.changes) for edit in constant_edits
                ),
                "duplicate_cure_files": duplicate_files,
                "duplicate_cure_copies": duplicate_copies,
                "duplicate_cure_bindings": duplicate_bindings,
                "duplicate_cure_plans": duplicate_plans,
            },
        )
        return finalized, impact_report

    def build_report(self) -> m.Infra.WorkspaceReport:
        """Build the canonical workspace census report without CLI side effects.

        Returns:
            The resulting ``m.Infra.WorkspaceReport``.

        """
        report, _ = self._execution_reports()
        return report

    @override
    def execute(self) -> p.Result[m.Infra.WorkspaceReport]:
        """Execute the census with one shared Rope session.

        Returns:
            The resulting ``p.Result[m.Infra.WorkspaceReport]``.

        """
        report, impact_report = self._execution_reports()
        cli.display_text(self.render_text(report))
        if self.json_output_path is not None:
            u.Infra.export_pydantic_json(report, self.json_output_path)
            u.Cli.info(f"JSON report exported to: {self.json_output_path}")
        if self.impact_map_output_path is not None:
            impact_result = u.Infra.write_impact_map(
                self._impact_map_results(impact_report),
                self.impact_map_output_path,
            )
            if impact_result.failure:
                return r[m.Infra.WorkspaceReport].from_failure(impact_result)
            u.Cli.info(f"Impact map exported to: {self.impact_map_output_path}")
        return r[m.Infra.WorkspaceReport].ok(report)


__all__: list[str] = ["FlextInfraRefactorCensus"]
