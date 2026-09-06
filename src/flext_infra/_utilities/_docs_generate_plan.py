"""Normalized artifact inventory and destination planning for generated docs."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_cli import u as cli_u
from flext_core import r
from flext_infra._utilities._docs_generate_sources import (
    FlextInfraUtilitiesDocsGenerateSourcesMixin,
)
from flext_infra._utilities.base import FlextInfraUtilitiesBase
from flext_infra._utilities.docs_contract import FlextInfraUtilitiesDocsContract
from flext_infra.models import m
from flext_infra.typings import t

if TYPE_CHECKING:
    from flext_infra.protocols import p

type DocsRenderedArtifactTuple = t.Triple[Path, Path, str | None]


class FlextInfraUtilitiesDocsGeneratePlanMixin(
    FlextInfraUtilitiesDocsGenerateSourcesMixin
):
    """Normalize rendered artifacts and bind them to exact destination states."""

    @staticmethod
    def docs_normalize_artifacts(
        artifacts: t.SequenceOf[DocsRenderedArtifactTuple],
    ) -> p.Result[tuple[DocsRenderedArtifactTuple, ...]]:
        """Validate one unique lexical owner and target without dereferencing."""
        normalized: list[DocsRenderedArtifactTuple] = []
        targets: set[Path] = set()
        for project, target, content in artifacts:
            if (
                not project.is_absolute()
                or not target.is_absolute()
                or ".." in project.parts
                or ".." in target.parts
            ):
                return r[tuple[DocsRenderedArtifactTuple, ...]].fail(
                    f"docs publication paths must be absolute and lexical: {target}"
                )
            try:
                target.relative_to(project)
            except ValueError:
                return r[tuple[DocsRenderedArtifactTuple, ...]].fail(
                    f"docs publication target escapes project {project}: {target}"
                )
            if target in targets:
                return r[tuple[DocsRenderedArtifactTuple, ...]].fail(
                    f"duplicate docs publication target: {target}"
                )
            targets.add(target)
            normalized.append((project, target, content))
        return r[tuple[DocsRenderedArtifactTuple, ...]].ok(tuple(normalized))

    @staticmethod
    def docs_required_directories(
        bundle: m.Infra.DocsGenerationBundle,
    ) -> p.Result[tuple[Path, ...]]:
        """Return unique target directories ordered parent before child."""
        required: set[Path] = set()
        for scoped in bundle.scopes:
            for artifact in scoped.artifacts:
                if artifact.desired_content is None:
                    continue
                parent = scoped.scope.path
                for part in artifact.relative_path.parent.parts:
                    parent /= part
                    required.add(parent)
        return r[tuple[Path, ...]].ok(
            tuple(sorted(required, key=FlextInfraUtilitiesBase.path_depth_then_text))
        )

    @staticmethod
    def docs_file_plans(
        bundle: m.Infra.DocsGenerationBundle,
    ) -> p.Result[tuple[m.Infra.CodegenFilePlan, ...]]:
        """Snapshot targets from the canonical rendered artifact inventory."""
        workspace_root = bundle.scopes[0].scope.path
        scope_roots = tuple(scoped.scope.path for scoped in bundle.scopes)
        stable = FlextInfraUtilitiesDocsGeneratePlanMixin.docs_verify_sources(
            workspace_root, bundle.source_states, extra_roots=scope_roots
        )
        if stable.failure:
            return r[tuple[m.Infra.CodegenFilePlan, ...]].from_failure(stable)
        plans: list[m.Infra.CodegenFilePlan] = []
        for scoped in bundle.scopes:
            for artifact in scoped.artifacts:
                planned = FlextInfraUtilitiesDocsContract.docs_file_plan(
                    scoped.scope.path,
                    scoped.scope.path / artifact.relative_path,
                    artifact.desired_content,
                    desired_mode=artifact.desired_mode,
                    source_states=bundle.source_states,
                )
                if planned.failure:
                    return r[tuple[m.Infra.CodegenFilePlan, ...]].from_failure(planned)
                plans.append(planned.value)
        stable = FlextInfraUtilitiesDocsGeneratePlanMixin.docs_verify_sources(
            workspace_root, bundle.source_states, extra_roots=scope_roots
        )
        if stable.failure:
            return r[tuple[m.Infra.CodegenFilePlan, ...]].from_failure(stable)
        return r[tuple[m.Infra.CodegenFilePlan, ...]].ok(tuple(plans))

    @staticmethod
    def _prune_generated_tree_artifacts(
        project: Path, root: Path, rendered: t.SequenceOf[tuple[Path, str]]
    ) -> p.Result[tuple[DocsRenderedArtifactTuple, ...]]:
        """Describe stale files owned by one generated tree as absent artifacts."""
        planned = cli_u.Cli.atomic_plan_directory_chain(root)
        if planned.failure:
            return r[tuple[DocsRenderedArtifactTuple, ...]].from_failure(planned)
        if planned.value.directories:
            return r[tuple[DocsRenderedArtifactTuple, ...]].ok(())
        inventory = cli_u.Cli.atomic_inventory_physical_tree(root)
        if inventory.failure:
            return r[tuple[DocsRenderedArtifactTuple, ...]].from_failure(inventory)
        expected_paths = {
            path for path, _content in rendered if path.is_relative_to(root)
        }
        return r[tuple[DocsRenderedArtifactTuple, ...]].ok(
            tuple(
                (project, entry.path, None)
                for entry in inventory.value.entries
                if entry.kind == "file"
                and entry.path.suffix == ".md"
                and entry.path not in expected_paths
            )
        )


__all__: list[str] = ["FlextInfraUtilitiesDocsGeneratePlanMixin"]
