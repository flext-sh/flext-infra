"""Guarded live publication for one fully journaled generation phase."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import m, u
from flext_infra.codegen import _mise_artifacts_files as files

if TYPE_CHECKING:
    from flext_infra import p, t


def publish(
    publications: t.VariadicTuple[m.Infra.CodegenStagedFile],
) -> p.Result[t.VariadicTuple[Path]]:
    """Apply an already durable phase through full-state guarded primitives."""
    written: list[Path] = []
    total = len(publications)
    for index, publication in enumerate(publications, start=1):
        u.Cli.emit_raw(f"  publish [{index}/{total}] {publication.before.path}\n")
        changed = files.write_publication(publication)
        if changed.failure:
            return r[tuple[Path, ...]].from_failure(changed)
        written.append(publication.before.path)
    return r[tuple[Path, ...]].ok(tuple(written))


__all__: list[str] = ["publish"]
