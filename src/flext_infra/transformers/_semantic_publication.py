"""Guarded live publication for semantic migration file plans."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import m, u

if TYPE_CHECKING:
    from flext_infra import p, t


def publish_semantic_file_plan(plan: m.Infra.SemanticFilePlan) -> p.Result[bool]:
    """Publish one SemanticFilePlan through the journal system."""
    if plan.desired_content is None:
        return r[bool].ok(True)
    before = plan.before
    mode = plan.desired_mode
    if mode is None:
        return r[bool].fail(f"semantic desired mode is absent: {plan.path}")
    # Stage the desired content
    staging_path = plan.path.with_name(f".{plan.path.name}.semantic-staging")
    staged_before = u.Cli.atomic_read_binary_file_state(staging_path, required=False)
    if staged_before.failure:
        return r[bool].from_failure(staged_before)
    written = u.Cli.atomic_write_binary_file_guarded(
        staged_before.value, plan.desired_content, permission_mode=mode
    )
    if written.failure:
        return r[bool].from_failure(written)
    staged = u.Cli.atomic_read_binary_file_state(staging_path, required=True)
    if staged.failure:
        return r[bool].from_failure(staged)
    replacement = staged.value

    # Publish through the guarded atomic primitives
    # The zero-residue law prohibits leaving backup copies beside managed destinations
    from flext_infra.codegen import FlextInfraMiseArtifactsFiles as files

    return files.write_publication(
        m.Infra.CodegenStagedFile(
            phase="semantic",
            project=plan.project,
            before=before,
            replacement=replacement,
        )
    )


def publish_semantic_file_plans(
    plans: t.SequenceOf[m.Infra.SemanticFilePlan],
) -> p.Result[t.VariadicTuple[Path]]:
    """Apply semantic file plans through full-state guarded primitives."""
    written: list[Path] = []
    total = len(plans)
    for index, plan in enumerate(plans, start=1):
        u.Cli.emit_raw(f"  semantic publish [{index}/{total}] {plan.path}\n")
        changed = publish_semantic_file_plan(plan)
        if changed.failure:
            return r[tuple[Path, ...]].from_failure(changed)
        written.append(plan.path)
    return r[tuple[Path, ...]].ok(tuple(written))


__all__: list[str] = ["publish_semantic_file_plan", "publish_semantic_file_plans"]
