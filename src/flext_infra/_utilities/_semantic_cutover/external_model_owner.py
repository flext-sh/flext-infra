"""Native renames for external model holders whose path owns their namespace.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from collections.abc import Mapping
from pathlib import Path

from flext_cli import u

from flext_infra import c, m, p, r


class FlextInfraUtilitiesSemanticCutoverExternalModelOwner:
    """Rename one external ``ProjectModel*`` class through native Rope identity."""

    @classmethod
    def _plan_external_model_owner(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        sources: Mapping[Path, str],
    ) -> p.Result[tuple[p.Infra.SemanticMigrationEdit, ...]]:
        """Plan only path-derived external model holder renames.

        Returns:
            Native declaration, reference, and lazy-export edits, if any.

        Raises:
            ValueError: If native rename would move a module.

        """
        planner = workspace.semantic_rename_planner
        if planner is None:
            message = "external model owner requires the injected native rename planner"
            raise ValueError(message)
        decisions: list[p.Infra.SemanticRenameDecision] = []
        for path, source in sorted(sources.items()):
            decision = cls._external_model_owner_decision(
                workspace, path, source, planner
            )
            if decision is not None:
                decisions.append(decision)
        if not decisions:
            return r[tuple[p.Infra.SemanticMigrationEdit, ...]].ok(())
        updates, moves = planner.plan_native_candidates(
            (workspace.rope_project,), sources, decisions
        )
        if moves:
            msg = "external model owner rename must not move modules"
            raise ValueError(msg)
        return r[tuple[p.Infra.SemanticMigrationEdit, ...]].ok(
            tuple(
                m.Infra.SemanticMigrationEdit(
                    file_path=path,
                    original_source=sources[path],
                    updated_source=updated,
                    changes=("renamed external model holder from its path",),
                )
                for path, updated in sorted(updates.items())
                if updated is not None and updated != sources[path]
            )
        )

    @classmethod
    def _external_model_owner_decision(
        cls,
        workspace: p.Infra.RopeWorkspaceDsl,
        path: Path,
        source: str,
        planner: p.Infra.NativeSemanticRenamePlanner,
    ) -> p.Infra.SemanticRenameDecision | None:
        """Return the one eligible external class holder in ``path``.

        Generated files, facade roots, private model families, and ambiguous or
        occupied module targets are deliberately not candidates.

        Returns:
            The native rename decision, or ``None`` when the module is ineligible.

        """
        if path.name == c.Infra.INIT_PY or source.startswith(c.Infra.AUTOGEN_HEADER):
            return None
        convention = workspace.convention(path)
        policy = convention.module_policy
        if (
            not policy.project_prefix
            or policy.expected_family is not None
            or "_models" in path.parts
        ):
            return None
        tree = ast.parse(source, filename=str(path))
        target = cls._external_model_owner_target(convention)
        holders = tuple(
            node
            for node in tree.body
            if isinstance(node, ast.ClassDef)
            and not node.name.startswith("_")
            and node.name.startswith(f"{policy.project_prefix}Model")
        )
        if len(holders) != 1 or holders[0].name == target:
            return None
        # A class with the path-derived name already declared is a collision,
        # not evidence that another holder should be renamed.
        if any(
            isinstance(node, ast.ClassDef) and node.name == target for node in tree.body
        ):
            return None
        declaration = planner.inventoried_declaration(
            workspace, f"{convention.module_name}.{holders[0].name}"
        )
        return m.Infra.SemanticRenameDecision(
            declaration=declaration,
            replacement_name=target,
            reason="external model holder derives its public owner from module path",
        )

    @staticmethod
    def _external_model_owner_target(
        convention: p.Infra.RopeModuleConvention,
    ) -> str:
        """Derive ``Project<Directory><Module>`` from the module convention.

        Returns:
            The path-derived external owner name.

        """
        directories = tuple(convention.package_name.split("."))[1:]
        return "".join((
            convention.module_policy.project_prefix,
            *(u.derive_class_stem(part.strip("_")) for part in directories),
            u.derive_class_stem(convention.file_path.stem.strip("_")),
        ))


__all__: list[str] = ["FlextInfraUtilitiesSemanticCutoverExternalModelOwner"]
