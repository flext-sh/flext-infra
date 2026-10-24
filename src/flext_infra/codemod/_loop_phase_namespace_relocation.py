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
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Plan selected declarations while retaining the full reference readscope.

        Returns:
            The planned file plans, or the first planning failure.

        """
        cascade = FlextInfraNamespaceRelocationCascade()
        working = dict(sources)
        effects: t.MutableMappingKV[Path, m.Infra.CodegenFilePlan] = {}
        for project_root in u.Infra.governed_project_roots(root):
            if not u.Infra.namespace_enabled(project_root):
                continue
            py_files = tuple(
                path
                for path in working
                if path.is_relative_to(project_root)
                and path.suffix in {c.Infra.EXT_PYTHON, c.Infra.EXT_PYTHON_STUB}
                and (u.Infra.project_root(path) or project_root) == project_root
            )
            planned = cascade.plan(
                m.Infra.NamespaceRelocationRequest(
                    project_root=project_root,
                    findings=cascade.findings_from_report(
                        project_root, py_files, preflight.entries, scan_root=root
                    ),
                    py_files=py_files,
                    sources=working,
                ),
                rope_project=rope_workspace.rope_project,
            )
            if planned.failure:
                return planned
            for plan in planned.value:
                if plan.desired_content is None:
                    return r[tuple[m.Infra.CodegenFilePlan, ...]].fail(
                        f"declaration relocation unexpectedly retired "
                        f"a module: {plan.path}"
                    )
                previous = effects.get(plan.path)
                effects[plan.path] = (
                    plan
                    if previous is None
                    else m.Infra.CodegenFilePlan(
                        project=plan.project,
                        path=plan.path,
                        before=previous.before,
                        desired_content=plan.desired_content,
                        desired_mode=plan.desired_mode,
                        owner=plan.owner,
                    )
                )
                working[plan.path] = plan.desired_content.decode(c.DEFAULT_ENCODING)
        return r[tuple[m.Infra.CodegenFilePlan, ...]].ok(tuple(effects.values()))

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
        inventory = u.Infra.iter_python_files(
            m.Infra.SourceScanRequest(
                project_roots=tuple(u.Infra.governed_project_roots(root)),
            )
        )
        if inventory.failure:
            return r[bool].from_failure(inventory)
        planned = FlextInfraNamespaceRelocationPhase.plan(
            root,
            preflight,
            rope_workspace,
            sources={
                path: path.read_text(encoding=c.DEFAULT_ENCODING)
                for path in inventory.value
            },
        )
        if planned.failure:
            return r[bool].from_failure(planned)
        return FlextInfraNamespaceRelocationCascade.publish_plan(root, planned.value)


__all__: list[str] = ["FlextInfraNamespaceRelocationPhase"]
