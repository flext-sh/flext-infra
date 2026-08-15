"""Project-owned managed-artifact models for the deps subpackage.

Why this is a separate module: a ``default_factory`` runs while the class
body executes, so a nested model cannot name a sibling through the outer
class — that name is still unbound. The previous code hid this with a
``default_factory=lambda: Outer.Sibling()`` deferral, which turned a
structural defect into a runtime one.

The fix is the workspace's diamond-MRO composition: each layer declares the
model it owns and inherits the layer below, so every referenced model is a
resolved base-class attribute at definition time. Defaults stay direct
callables; no deferred-resolution lambda, no self-referential model.
"""

from __future__ import annotations

from types import MappingProxyType
from typing import Annotated

from flext_cli import m
from flext_infra import t


class FlextInfraModelsDepsToolConfigProjectRuff:
    """Innermost layer: the Ruff slice a project may own."""

    class ProjectRuffConfig(m.ArbitraryTypesModel):
        """Project-owned Ruff additions for generated managed artifacts."""

        per_file_ignores: Annotated[
            t.MappingKV[str, t.StrSequence],
            m.Field(
                description="Project-local per-file rules merged with global policy."
            ),
        ] = m.Field(default_factory=lambda: MappingProxyType({}))


class FlextInfraModelsDepsToolConfigProjectArtifacts(
    FlextInfraModelsDepsToolConfigProjectRuff
):
    """Managed-artifact layer; ``ProjectRuffConfig`` is an inherited attribute."""

    class ProjectManagedArtifactsConfig(m.ArbitraryTypesModel):
        """Project-owned configuration for generated artifacts."""

        Ruff: Annotated[
            FlextInfraModelsDepsToolConfigProjectRuff.ProjectRuffConfig,
            m.Field(description="Ruff additions owned by the current project."),
        ] = m.Field(
            default_factory=FlextInfraModelsDepsToolConfigProjectRuff.ProjectRuffConfig
        )


class FlextInfraModelsDepsToolConfigProject(
    FlextInfraModelsDepsToolConfigProjectArtifacts
):
    """Document layer composing every project-owned managed-artifact model."""

    class ProjectConfigDocument(m.ArbitraryTypesModel):
        """Relevant managed-artifact slice loaded from project config files."""

        ManagedArtifacts: Annotated[
            FlextInfraModelsDepsToolConfigProjectArtifacts.ProjectManagedArtifactsConfig,
            m.Field(description="Project-local managed artifact configuration."),
        ] = m.Field(
            default_factory=(
                FlextInfraModelsDepsToolConfigProjectArtifacts.ProjectManagedArtifactsConfig
            )
        )


__all__: list[str] = [
    "FlextInfraModelsDepsToolConfigProject",
    "FlextInfraModelsDepsToolConfigProjectArtifacts",
    "FlextInfraModelsDepsToolConfigProjectRuff",
]
