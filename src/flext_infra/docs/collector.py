"""Fixed-effect plan collection through the shared generation transaction.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Annotated, ClassVar

from flext_infra import c, m, r, t, u
from flext_infra.codegen import (
    FlextInfraCodegenMiseArtifacts,
    FlextInfraCodegenPreconditions,
    FlextInfraCodegenTransaction,
)

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraDocCollector:
    """Publish only fully supported source associations under explicit leases."""

    class ScopePublication(m.ArbitraryTypesModel):
        """Validated immutable inputs publishing one plan-collection scope."""

        model_config: ClassVar[m.ConfigDict] = m.ConfigDict(frozen=True)

        scope_root: Annotated[Path, m.Field(description="Physical scope root")]
        configuration_path: Annotated[
            Path,
            m.Field(description="Authenticated collection configuration path"),
        ]
        snapshot: Annotated[
            m.Cli.AtomicFileState,
            m.Field(description="Authenticated configuration byte state"),
        ]
        configuration: Annotated[
            m.Infra.PlanCollectionConfig,
            m.Field(description="Parsed collection configuration"),
        ]
        roots: Annotated[
            t.MappingKV[str, Path],
            m.Field(description="Named scope roots visible to the transaction"),
        ]
        transaction: Annotated[
            FlextInfraCodegenTransaction,
            m.Field(description="Owning generation transaction"),
        ]

    @classmethod
    def collect(cls, request: m.Infra.DocsCollectRequest) -> p.Result[bool]:
        """Authenticate configuration, collect sources, and commit one file phase.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        authenticated = cls._authenticated_configuration(request)
        if authenticated.failure:
            return r[bool].from_failure(authenticated)
        configuration_path, snapshot, configuration = authenticated.value
        roots = {"@canonical": request.repository_root}
        if configuration.projection_root is not None:
            roots["@projection"] = configuration.projection_root.expanduser()
        publication = cls.ScopePublication(
            scope_root=request.repository_root,
            configuration_path=configuration_path,
            snapshot=snapshot,
            configuration=configuration,
            roots=roots,
            transaction=FlextInfraCodegenTransaction(
                FlextInfraCodegenMiseArtifacts(
                    repository_root=request.repository_root,
                ),
            ),
        )
        return publication.transaction.run_files_locked(
            roots,
            lambda scope_root: cls._publish_scope(
                publication.model_copy(update={"scope_root": scope_root}),
            ),
        )

    @classmethod
    def _publish_scope(
        cls,
        publication: FlextInfraDocCollector.ScopePublication,
    ) -> p.Result[bool]:
        """Collect, publish, and re-verify one scope under the transaction lease.

        Args:
            publication: Immutable publication inputs for the elected scope.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        unchanged = cls._require_unchanged(
            publication.configuration_path,
            publication.snapshot,
            "plan collection configuration changed before collection",
        )
        if unchanged.failure:
            return r[bool].from_failure(unchanged)
        bundle = u.Infra.docs_collect_plan_files(
            publication.scope_root,
            publication.configuration,
        )
        incomplete = tuple(
            item for item in bundle.coverage if item.adapter == "private-inventory"
        )
        if incomplete:
            pending = ", ".join(
                f"{item.source_id}:{item.status}:{item.files}" for item in incomplete
            )
            return r[bool].fail(
                f"plan source extraction is incomplete; private "
                f"inventories are not extracted plans: {pending}",
            )
        u.Infra.verify_plan_collection_sources(
            publication.scope_root,
            publication.configuration,
            bundle,
        )
        analysis = cls._staged_phase_analysis(publication.snapshot, bundle)
        if analysis.failure:
            return r[bool].from_failure(analysis)
        published = publication.transaction.publish_file_phase_locked(
            publication.scope_root,
            publication.roots,
            analysis.value,
            m.Infra.CodegenPhasePublicationPolicy(
                directories=tuple(
                    path
                    for path in bundle.required_directories
                    if path not in publication.roots.values()
                ),
            ),
        )
        if published.failure:
            return r[bool].from_failure(published)
        return cls._verified_publication(publication, bundle)

    @staticmethod
    def _staged_phase_analysis(
        snapshot: m.Cli.AtomicFileState,
        bundle: m.Infra.PlanCollectionBundle,
    ) -> p.Result[m.Infra.CodegenPhaseAnalysis]:
        """Stage the collected plans with snapshot-unique source states.

        Args:
            snapshot: Authenticated configuration byte state anchoring inputs.
            bundle: Collected plan bundle with files and source states.

        Returns:
            The staged phase analysis, or the first unique-state failure.

        """
        result_type = r[m.Infra.CodegenPhaseAnalysis]
        inputs = FlextInfraCodegenPreconditions.unique_states(
            (snapshot, *bundle.source_states),
        )
        if inputs.failure:
            return result_type.from_failure(inputs)
        files: list[m.Infra.CodegenFilePlan] = []
        for plan in bundle.files:
            sources = FlextInfraCodegenPreconditions.unique_states(
                (snapshot, *plan.source_states),
            )
            if sources.failure:
                return result_type.from_failure(sources)
            files.append(plan.model_copy(update={"source_states": sources.value}))
        return result_type.ok(
            m.Infra.CodegenPhaseAnalysis(
                phase=c.Infra.CodegenStagedFilePhase.DOCS_COLLECTION,
                files=tuple(files),
                inputs=inputs.value,
            ),
        )

    @classmethod
    def _verified_publication(
        cls,
        publication: FlextInfraDocCollector.ScopePublication,
        bundle: m.Infra.PlanCollectionBundle,
    ) -> p.Result[bool]:
        """Re-verify the configuration, publication, and prunable directories.

        Args:
            publication: Immutable publication inputs for the elected scope.
            bundle: The published plan bundle.

        Returns:
            Whether the scope published and re-verified completely.

        """
        unchanged = cls._require_unchanged(
            publication.configuration_path,
            publication.snapshot,
            "plan collection configuration changed during publication",
        )
        if unchanged.failure:
            return unchanged
        u.Infra.verify_plan_collection_publication(
            publication.scope_root,
            publication.configuration,
            bundle,
        )
        pruned = cls._prune_bundle_directories(bundle)
        if pruned.failure:
            return r[bool].from_failure(pruned)
        return r[bool].ok(value=True)

    @staticmethod
    def _authenticated_configuration(
        request: m.Infra.DocsCollectRequest,
    ) -> p.Result[t.Triple[Path, m.Cli.AtomicFileState, m.Infra.PlanCollectionConfig]]:
        """Authenticate the physical root and parse the collection configuration.

        Returns:
            The resulting ``(configuration_path, snapshot, configuration)`` triple.

        """
        result_type = r[
            t.Triple[Path, m.Cli.AtomicFileState, m.Infra.PlanCollectionConfig]
        ]
        root = request.repository_root
        if not root.is_absolute() or ".." in root.parts or root.resolve() != root:
            return result_type.fail(
                f"plan collection repository root is not a physical "
                f"absolute path: {root}",
            )
        configuration_path = request.configuration
        if not configuration_path.is_absolute():
            configuration_path = root / configuration_path
        captured = u.Cli.atomic_read_binary_file_state(
            configuration_path,
            required=True,
        )
        if captured.failure:
            return result_type.from_failure(captured)
        snapshot = captured.value
        if snapshot.content is None:
            return result_type.fail(
                f"plan collection configuration is absent: {configuration_path}",
            )
        parsed = u.Cli.yaml_parse(snapshot.content.decode("utf-8"))
        if parsed.failure:
            return result_type.from_failure(parsed)
        validated: p.Result[m.Infra.PlanCollectionConfig] = u.validate_value(
            m.Infra.PlanCollectionConfig,
            parsed.value,
            strict=False,
        )
        if validated.failure:
            return result_type.from_failure(validated)
        return result_type.ok((configuration_path, snapshot, validated.value))

    @staticmethod
    def _require_unchanged(
        configuration_path: Path,
        snapshot: m.Cli.AtomicFileState,
        message: str,
    ) -> p.Result[bool]:
        """Require the authenticated configuration bytes to be unchanged.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        current = u.Cli.atomic_read_binary_file_state(
            configuration_path,
            required=True,
        )
        if current.failure:
            return r[bool].from_failure(current)
        if current.value != snapshot:
            return r[bool].fail(message)
        return r[bool].ok(value=True)

    @staticmethod
    def _prune_bundle_directories(
        bundle: m.Infra.PlanCollectionBundle,
    ) -> p.Result[bool]:
        """Delete the bundle's empty prunable directories.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        for directory in bundle.prunable_directories:
            observed = u.Cli.atomic_read_empty_directory_state(
                directory,
                required=False,
            )
            if observed.failure:
                return r[bool].from_failure(observed)
            if not observed.value.exists:
                continue
            removed = u.Cli.atomic_delete_empty_directory_guarded(observed.value)
            if removed.failure:
                return r[bool].from_failure(removed)
        return r[bool].ok(value=True)


__all__: list[str] = ["FlextInfraDocCollector"]
