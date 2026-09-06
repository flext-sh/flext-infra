"""Validated receipt and publication candidates for Mise transactions."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import m, u
from flext_infra.codegen import _mise_artifacts_files as files

if TYPE_CHECKING:
    from flext_infra import p, t


def publication_plan(
    projects: t.VariadicTuple[m.Infra.MiseToolchainProjectState],
    stages: t.VariadicTuple[Path],
) -> p.Result[t.VariadicTuple[m.Infra.CodegenStagedFile]]:
    """Bind each staged artifact to its exact pre-lock destination state."""
    publications: list[m.Infra.CodegenStagedFile] = []
    for project, stage in zip(projects, stages, strict=True):
        before_states = (
            project.config.before,
            project.artifacts.unix_launcher,
            project.artifacts.windows_launcher,
            project.artifacts.lock,
        )
        for before, (name, mode) in zip(
            before_states, files.PUBLICATION_SPECS, strict=True
        ):
            replacement = files.read_state(stage / name, required=True)
            if replacement.failure or replacement.value.content is None:
                return r[tuple[m.Infra.CodegenStagedFile, ...]].fail(
                    replacement.error or f"missing staged Mise artifact: {name}"
                )
            if replacement.value.mode != mode:
                return r[tuple[m.Infra.CodegenStagedFile, ...]].fail(
                    f"staged Mise artifact mode differs: {stage / name}"
                )
            if not u.Infra.atomic_file_state_differs(
                before,
                desired_content=replacement.value.content,
                desired_mode=replacement.value.mode,
            ):
                continue
            publications.append(
                m.Infra.CodegenStagedFile(
                    phase="mise",
                    project=project.layout.root,
                    before=before,
                    replacement=replacement.value,
                )
            )
    return r[tuple[m.Infra.CodegenStagedFile, ...]].ok(tuple(publications))


__all__: list[str] = ["publication_plan"]
