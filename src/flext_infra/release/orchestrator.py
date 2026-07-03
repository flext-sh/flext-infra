"""Release orchestration service."""

from __future__ import annotations

from pathlib import Path
from typing import Annotated, override

from flext_infra import c, m, t, u
from flext_infra.base_selection import FlextInfraProjectSelectionServiceBase
from flext_infra.release._orchestrator_dispatch import (
    FlextInfraReleaseOrchestratorDispatchMixin,
)
from flext_infra.release.orchestrator_phases import FlextInfraReleaseOrchestratorPhases


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
        int,
        m.Field(description="Interactive mode (1=yes, 0=no)"),
    ] = 1
    next_dev: Annotated[bool, m.Field(description="Prepare next dev version")] = False
    next_bump: Annotated[str, m.Field(description="Next bump type")] = "minor"
    create_branches: Annotated[
        int,
        m.Field(description="Create release branches (1=yes, 0=no)"),
    ] = 1

    @override
    def _build_targets(
        self,
        workspace_root: Path,
        project_names: t.StrSequence,
    ) -> t.SequenceOf[t.Pair[str, Path]]:
        """Resolve release build targets."""
        targets: t.MutableSequenceOf[t.Pair[str, Path]] = [
            (c.Infra.RK_ROOT, workspace_root),
        ]
        projects_result = u.Infra.resolve_projects(workspace_root, project_names)
        if projects_result.success:
            targets.extend((p.name, p.path) for p in projects_result.value)
        seen: t.Infra.StrSet = set()
        unique: t.MutableSequenceOf[t.Pair[str, Path]] = []
        for name, path in targets:
            if name in seen or not path.exists():
                continue
            seen.add(name)
            unique.append((name, path))
        return unique

    @override
    def _version_files(
        self,
        workspace_root: Path,
        project_names: t.StrSequence,
    ) -> t.SequenceOf[Path]:
        """Resolve candidate pyproject files for version updates."""
        files: t.MutableSequenceOf[Path] = [
            workspace_root / c.Infra.PYPROJECT_FILENAME,
        ]
        projects_result = u.Infra.resolve_projects(workspace_root, project_names)
        if projects_result.success:
            for project in projects_result.value:
                pyproject = project.path / c.Infra.PYPROJECT_FILENAME
                if pyproject.exists():
                    files.append(pyproject)
        return sorted({path.resolve() for path in files if path.exists()})


__all__: list[str] = ["FlextInfraReleaseOrchestrator"]
