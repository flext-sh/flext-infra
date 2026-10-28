"""Census collection-gate + module-selection helpers — extracted concern.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from collections.abc import Sequence
from typing import TYPE_CHECKING, ClassVar

from flext_cli import cli

from flext_infra import config, m, u
from flext_infra.refactor import FlextInfraRefactorCensusCollect

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraRefactorCensusCollectHelpers(FlextInfraRefactorCensusCollect):
    """Select the modules to inventory and drive the census collection.

    Owns validated census options and inherits the native collection/report
    implementation and project-selection state used by ``_collect_report``.
    """

    model_config: ClassVar[m.ConfigDict] = m.Infra.CensusOptions.model_config

    options: m.Infra.CensusOptions = m.Field(
        default_factory=m.Infra.CensusOptions,
        description="Validated census filters and report destinations",
    )

    @staticmethod
    def _should_collect_object_references(rule_names: Sequence[str] | None) -> bool:
        """Decide whether to collect object references.

        Returns:
            The resulting ``bool``.

        """
        if rule_names is None:
            return True
        return "unused" in rule_names

    @staticmethod
    def production_module(module: m.Infra.RopeModuleIndexEntry) -> bool:
        """Return whether a module belongs to one configured production root.

        Returns:
            Whether a module belongs to one configured production root.

        """
        project_root = module.project_root
        if project_root is None:
            return False
        resolved_file = module.file_path.resolve()
        resolved_root = project_root.resolve()
        if not resolved_file.is_relative_to(resolved_root):
            return False
        parts = resolved_file.relative_to(resolved_root).parts
        return bool(parts) and (parts[0] in config.Infra.source_scan.roots)

    def _collect_report(
        self,
        rope: p.Infra.RopeWorkspaceDsl,
        *,
        source_preview: p.Infra.SourcePreview,
    ) -> m.Infra.WorkspaceReport:
        """Inventory the selected modules then assemble the census report.

        Returns:
            The resulting ``m.Infra.WorkspaceReport``.

        """
        kind_names = u.Infra.normalize_sequence_values(self.options.kinds)
        rule_names = u.Infra.normalize_sequence_values(self.options.rules)
        scan_config = m.Infra.ScanConfig(
            kind_names=kind_names,
            rule_names=rule_names,
            selected_families=self._selected_families(
                u.Infra.normalize_sequence_values(self.options.families),
            ),
            selected_kinds=frozenset(kind_names) if kind_names else None,
            selected_rules=frozenset(rule_names) if rule_names else None,
            include_object_references=self._should_collect_object_references(
                rule_names,
            ),
            include_local_scopes=self.options.include_local_scopes,
        )
        findings = m.Infra.ScanFindings(project_objects={}, report_projects=set())
        current_project = None
        for module in rope.modules(project_names=self.project_names):
            if self.production_module(module):
                if current_project != module.project_root:
                    current_project = module.project_root
                    cli.display_text(f"census: scan {current_project}")
                self._scan_module(rope, module, scan_config, findings=findings)
        return self._assemble_report(
            rope,
            source_preview=source_preview,
            findings=findings,
            scan_config=scan_config,
        )


__all__: list[str] = ["FlextInfraRefactorCensusCollectHelpers"]
