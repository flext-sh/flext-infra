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
    try:
        from flext_infra.codegen._mise_artifacts_files import (
            FlextInfraMiseArtifactsFiles as files,
        )
    except ImportError:
        # Fallback for non-codegen paths - use direct atomic publish
        return _direct_publish(before, replacement)
    return files.write_publication(
        m.Infra.CodegenStagedFile(
            phase="semantic",
            project=plan.project,
            before=before,
            replacement=replacement,
        )
    )


def _direct_publish(
    before: m.Cli.AtomicFileState, replacement: m.Cli.AtomicFileState
) -> p.Result[bool]:
    """Direct atomic publish without journal - used when codegen journal unavailable."""
    published = u.Cli.atomic_publish_staged_binary_file_guarded(before, replacement)
    if published.failure:
        return r[bool].from_failure(published)
    observed = published.value
    observed_identity = (
        observed.path,
        observed.parent_device,
        observed.parent_inode,
        observed.content,
        observed.mode,
        observed.device,
        observed.inode,
        observed.link_count,
        observed.file_attributes,
        observed.reparse_tag,
    )
    replacement_identity = (
        before.path,
        before.parent_device,
        before.parent_inode,
        replacement.content,
        replacement.mode,
        replacement.device,
        replacement.inode,
        replacement.link_count,
        replacement.file_attributes,
        replacement.reparse_tag,
    )
    if observed_identity != replacement_identity:
        return r[bool].fail(
            f"published semantic file differs from staged identity: {before.path}"
        )
    return r[bool].ok(True)


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
