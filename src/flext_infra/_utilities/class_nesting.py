"""Automatic class-nesting plans derived from the public Rope workspace."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import c, m

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraUtilitiesClassNesting:
    """Plan class nesting from semantic module ownership instead of record lists."""

    @staticmethod
    def class_nesting_plan(
        rope_workspace: p.Infra.RopeWorkspaceDsl, file_path: Path
    ) -> p.Result[tuple[m.Infra.ClassNestingViolation, ...]]:
        """Return top-level classes that must move under the declared module owner."""
        resolved_file = file_path.resolve()
        family = c.Infra.NAMESPACE_FILE_TO_FAMILY.get(resolved_file.name)
        if family is None:
            family = next(
                (
                    alias
                    for alias, directory in c.Infra.FAMILY_DIRECTORIES.items()
                    if resolved_file.parent.name == directory
                ),
                None,
            )
        if family is None:
            return r[tuple[m.Infra.ClassNestingViolation, ...]].ok(())
        convention = rope_workspace.convention(resolved_file)
        top_level_classes = tuple(
            item
            for item in rope_workspace.objects(
                resolved_file, include_local_scopes=False, include_references=False
            )
            if item.kind == "class" and item.class_path == item.name
        )
        if len(top_level_classes) <= 1:
            return r[tuple[m.Infra.ClassNestingViolation, ...]].ok(())

        target_namespace = convention.module_policy.expected_family
        owners = tuple(
            item for item in top_level_classes if item.name == target_namespace
        )
        if target_namespace is None or len(owners) != 1:
            class_names = ", ".join(item.name for item in top_level_classes)
            return r[tuple[m.Infra.ClassNestingViolation, ...]].fail(
                "class-nesting requires exactly one declared module owner "
                f"for {convention.module_name}; discovered: {class_names}"
            )

        relative_file = resolved_file.relative_to(
            rope_workspace.repository_root.resolve()
        ).as_posix()
        confidence = max(
            c.Infra.CONFIDENCE_RANKS, key=c.Infra.CONFIDENCE_RANKS.__getitem__
        )
        return r[tuple[m.Infra.ClassNestingViolation, ...]].ok(
            tuple(
                m.Infra.ClassNestingViolation(
                    file=relative_file,
                    line=max(1, item.line),
                    class_name=item.name,
                    target_namespace=target_namespace,
                    confidence=confidence,
                    rewrite_scope=c.Infra.RK_FILE,
                )
                for item in top_level_classes
                if item.name != target_namespace
            )
        )


__all__: list[str] = ["FlextInfraUtilitiesClassNesting"]
