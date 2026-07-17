"""Release orchestration service."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Annotated, override

from flext_core import r
from flext_infra import c, m, t, u
from flext_infra.base_selection import FlextInfraProjectSelectionServiceBase
from flext_infra.release._orchestrator_dispatch import (
    FlextInfraReleaseOrchestratorDispatchMixin,
)
from flext_infra.release.orchestrator_phases import FlextInfraReleaseOrchestratorPhases

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraReleaseOrchestrator(
    FlextInfraReleaseOrchestratorDispatchMixin,
    FlextInfraReleaseOrchestratorPhases,
    FlextInfraProjectSelectionServiceBase[bool],
):
    """Service for release lifecycle orchestration."""

    version: Annotated[str, m.Field(description="Version string")] = ""
    tag: Annotated[str, m.Field(description="Git tag (e.g. v1.0.0)")] = ""
    push: Annotated[bool, m.Field(description="Push to remote")] = False
    dev_suffix: Annotated[bool, m.Field(description="Add dev suffix")] = False
    phase: Annotated[str, m.Field(description="Release phase")] = "all"
    bump: Annotated[str, m.Field(description="Bump type (major/minor/patch)")] = ""
    interactive: Annotated[
        int, m.Field(description="Interactive mode (1=yes, 0=no)")
    ] = 1
    next_dev: Annotated[bool, m.Field(description="Prepare next dev version")] = False
    next_bump: Annotated[str, m.Field(description="Next bump type")] = "minor"
    create_branches: Annotated[
        int, m.Field(description="Create release branches (1=yes, 0=no)")
    ] = 1

    @override
    def _build_targets(
        self, workspace_root: Path, project_names: t.StrSequence
    ) -> p.Result[t.SequenceOf[t.Pair[str, Path]]]:
        """Resolve release build targets."""
        targets: t.MutableSequenceOf[t.Pair[str, Path]] = []
        projects_result = u.Infra.resolve_projects(workspace_root, project_names)
        if projects_result.failure:
            return r[t.SequenceOf[t.Pair[str, Path]]].fail(
                projects_result.error or "release project resolution failed"
            )
        targets.extend(
            (project.name, project.path)
            for project in projects_result.value
            if project.name.startswith("flext-")
        )
        seen: t.Infra.StrSet = set()
        unique: t.MutableSequenceOf[t.Pair[str, Path]] = []
        for name, path in targets:
            if name in seen or not path.exists():
                continue
            seen.add(name)
            unique.append((name, path))
        return r[t.SequenceOf[t.Pair[str, Path]]].ok(unique)

    @override
    def _version_files(
        self, workspace_root: Path, project_names: t.StrSequence
    ) -> p.Result[t.SequenceOf[Path]]:
        """Resolve candidate pyproject files for version updates."""
        files: t.MutableSequenceOf[Path] = [workspace_root / c.Infra.PYPROJECT_FILENAME]
        projects_result = u.Infra.resolve_projects(workspace_root, project_names)
        if projects_result.failure:
            return r[t.SequenceOf[Path]].fail(
                projects_result.error or "version project resolution failed"
            )
        for project in projects_result.value:
            pyproject = project.path / c.Infra.PYPROJECT_FILENAME
            if pyproject.exists():
                files.append(pyproject)
        return r[t.SequenceOf[Path]].ok(
            sorted({path.resolve() for path in files if path.exists()})
        )


__all__: list[str] = ["FlextInfraReleaseOrchestrator"]
