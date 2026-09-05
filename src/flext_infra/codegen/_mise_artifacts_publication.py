"""Guarded live publication for a fully journaled Mise artifact set."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import m, u
from flext_infra.codegen import _mise_artifacts_verification as verify

if TYPE_CHECKING:
    from flext_infra import p


def publish(
    owner: p.Infra.MiseArtifactsOwner,
    plan: m.Infra.MiseToolchainWorkspacePlan,
    journal: m.Infra.MiseToolchainJournal,
    publications: tuple[m.Cli.AtomicFilePublication, ...],
    source_plans: tuple[m.Infra.CodegenFilePlan, ...] = (),
) -> p.Result[bool]:
    """Publish changed bytes or modes, then exercise the real consumers."""
    source_check = verify.sources(plan, journal, source_plans)
    if source_check.failure:
        return r[bool].from_failure(source_check)
    changed = 0
    for publication in publications:
        before = publication.before
        replacement = publication.replacement
        if before.content == replacement.content and before.mode == replacement.mode:
            continue
        u.Cli.info(f"mise-toolchain: publish {before.path}")
        written = u.Cli.atomic_apply_file_publication_guarded(publication)
        if written.failure:
            return r[bool].from_failure(written)
        changed += 1
    exact = verify.published(publications)
    if exact.failure:
        return r[bool].from_failure(exact)
    validated = verify.live(owner, plan, publications)
    if validated.failure:
        return r[bool].from_failure(validated)
    journal_sources = verify.sources(plan, journal, source_plans)
    if journal_sources.failure:
        return r[bool].from_failure(journal_sources)
    u.Cli.info(
        "mise-toolchain: published "
        f"{changed} changed artifact(s) across {len(plan.projects)} project(s)"
    )
    return r[bool].ok(True)


__all__: list[str] = ["publish"]
