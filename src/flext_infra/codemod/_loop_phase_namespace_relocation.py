"""Namespace-relocation phase of the codemod fixed-point loop.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, r, t, u
from flext_infra.refactor import FlextInfraNamespaceRelocationCascade

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraNamespaceRelocationPhase:
    """Relocation callback: the rule catalog's namespace repairs in the loop."""

    name: str = "namespace-relocations"

    @staticmethod
    def plan(
        root: Path,
        preflight: m.Infra.ModScanReport,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        *,
        sources: t.MappingKV[Path, str],
        source_states: t.VariadicTuple[m.Cli.AtomicFileState],
        declared_files: t.VariadicTuple[m.Infra.CodegenFilePlan] = (),
    ) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
        """Plan selected declarations while retaining the full reference readscope."""
        cascade = FlextInfraNamespaceRelocationCascade()
        working = dict(sources)
        originals = {state.path: state for state in source_states}
        effects: t.MutableMappingKV[Path, m.Infra.CodegenFilePlan] = {}
        declarations = {plan.path: plan for plan in declared_files}
        for project_root in u.Infra.governed_project_roots(root):
            if not u.Infra.namespace_enabled(project_root):
                continue
            py_files = tuple(
                path for path in working
                if path.is_relative_to(project_root)
                and path.suffix in {c.Infra.EXT_PYTHON, c.Infra.EXT_PYTHON_STUB}
                and (u.Infra.project_root(path) or project_root) == project_root
            )
            findings = cascade.findings_from_report(
                project_root, py_files, preflight.entries, scan_root=root,
            )
            planned = cascade.plan(
                project_root=project_root, rope_project=rope_workspace.rope_project,
                findings=findings, py_files=py_files, sources=working,
                source_states=tuple(originals.values()),
                declared_files=tuple(declarations.values()),
            )
            if planned.failure:
                return r[m.Infra.CodegenPhaseAnalysis].from_failure(planned)
            for state in planned.value.inputs:
                previous = originals.setdefault(state.path, state)
                if previous != state:
                    return r[m.Infra.CodegenPhaseAnalysis].fail(
                        f"relocation original receipts disagree: {state.path}"
                    )
            for plan in planned.value.files:
                effects[plan.path] = plan
                declarations[plan.path] = plan
                if plan.desired_content is None:
                    return r[m.Infra.CodegenPhaseAnalysis].fail(
                        f"declaration relocation unexpectedly retired a module: {plan.path}"
                    )
                working[plan.path] = plan.desired_content.decode(c.DEFAULT_ENCODING)
        return r[m.Infra.CodegenPhaseAnalysis].ok(m.Infra.CodegenPhaseAnalysis(
            phase=c.Infra.CodegenStagedFilePhase.SEMANTIC,
            files=tuple(effects.values()), inputs=tuple(originals.values()),
        ))

    @staticmethod
    def apply(
        root: Path,
        preflight: m.Infra.ModScanReport,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
    ) -> p.Result[bool]:
        """Run every declared relocation the preflight captured, per project.

        Returns:
            The resulting ``p.Result[bool]`` — ``True`` marks changed sources.

        """
        inventory = u.Infra.iter_python_files(m.Infra.SourceScanRequest(
            project_roots=tuple(u.Infra.governed_project_roots(root)),
        ))
        if inventory.failure:
            return r[bool].from_failure(inventory)
        states = tuple(
            u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()
            for path in inventory.value
        )
        planned = FlextInfraNamespaceRelocationPhase.plan(
            root, preflight, rope_workspace,
            sources={state.path: state.content.decode(c.DEFAULT_ENCODING)
                     for state in states if state.content is not None},
            source_states=states,
        )
        if planned.failure:
            return r[bool].from_failure(planned)
        return FlextInfraNamespaceRelocationCascade.publish_plan(root, planned.value)


__all__: list[str] = ["FlextInfraNamespaceRelocationPhase"]
