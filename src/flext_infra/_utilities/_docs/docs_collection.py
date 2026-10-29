"""Deterministic plan collection through existing documentation file plans.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableMapping, Sequence
from datetime import UTC, datetime
from hashlib import sha256
from pathlib import Path

from flext_infra import c, m
from flext_infra._utilities._docs import (
    FlextInfraUtilitiesDocsCollectionSources,
    FlextInfraUtilitiesDocsContract,
)


class FlextInfraUtilitiesDocsCollection(FlextInfraUtilitiesDocsCollectionSources):
    """Plan effects only; the shared publisher owns publication and locking."""

    class _CollectionState:
        """Mutable accumulators one collection pass fills."""

        def __init__(
            self,
            canonical: Path,
            projection: Path | None,
            manifest: m.Infra.PlanCollectionManifest,
            configuration: m.Infra.PlanCollectionConfig,
        ) -> None:
            self.canonical = canonical
            self.projection = projection
            self.manifest = manifest
            self.configuration = configuration
            self.states: MutableMapping[Path, m.Cli.AtomicFileState] = {}
            self.desired: MutableMapping[Path, bytes] = {}
            self.history = list(manifest.revisions)
            self.observed = {
                (item.identity, item.digest) for item in manifest.revisions
            }
            self.revisions_by_identity = {
                item.identity: item for item in manifest.revisions
            }
            self.coverage: list[m.Infra.PlanCollectionCoverage] = []
            self.invalid_owned: MutableMapping[Path, str] = {}

        def absorb_owned_artifacts(self) -> None:
            """Record desired canonical bytes and flag mutated owned artifacts."""
            canonical_plans = {
                self.canonical / revision.canonical_path
                for revision in self.manifest.revisions
            }
            for artifact in self.manifest.artifacts:
                path = self.canonical / artifact.relative_path
                content = self.states[path].content
                if content is None:
                    self.invalid_owned[path] = artifact.digest
                    continue
                if (
                    path not in canonical_plans
                    and sha256(content).hexdigest() != artifact.digest
                ):
                    self.invalid_owned[path] = artifact.digest
                    continue
                self.desired[path] = content

        def absorb_artifacts(
            self,
            artifacts: tuple[m.Cli.AtomicFileState, ...],
        ) -> None:
            """Merge one path's collected states, rejecting concurrent change.

            Raises:
                ValueError: If collection source changed during read.

            """
            for state in artifacts:
                previous = self.states.get(state.path)
                if previous is not None and previous != state:
                    msg = f"collection source changed during read: {state.path}"
                    raise ValueError(msg)
                self.states[state.path] = state

        def previous_revision(
            self,
            path: Path,
        ) -> m.Infra.PlanCollectionRevision | None:
            """Return the recorded revision that owns one collected path.

            Returns:
                The resulting ``m.Infra.PlanCollectionRevision | None``.

            """
            projection = self.projection
            return next(
                (
                    item
                    for item in self.manifest.revisions
                    if self.canonical / item.canonical_path == path
                    or (
                        projection is not None
                        and path.is_relative_to(projection)
                        and item.canonical_path == path.relative_to(projection)
                    )
                ),
                None,
            )

        def record_revision(self, revision: m.Infra.PlanCollectionRevision) -> None:
            """Append one new revision identity to the history."""
            key = (revision.identity, revision.digest)
            if key not in self.observed:
                self.history.append(revision)
                self.observed.add(key)
                self.revisions_by_identity[revision.identity] = revision

        def record_private(
            self,
            source: m.Infra.PlanCollectionSource,
            paths: tuple[Path, ...],
        ) -> None:
            """Record a private-inventory source's coverage."""
            self.coverage.append(
                m.Infra.PlanCollectionCoverage(
                    source_id=source.id,
                    provider=source.provider,
                    adapter=source.adapter,
                    files=len(paths),
                    status="private-inventory" if paths else "empty",
                    private_paths=paths,
                ),
            )

        @staticmethod
        def require_publishable(source: m.Infra.PlanCollectionSource) -> None:
            """Require a plan-artifacts publication approval.

            Raises:
                ValueError: If file source requires publication approval.

            """
            if source.publication != "plan-artifacts":
                msg = f"file source requires publication approval: {source.id}"
                raise ValueError(msg)

        def record_public(
            self,
            source: m.Infra.PlanCollectionSource,
            paths: tuple[Path, ...],
        ) -> None:
            """Record a published source's coverage."""
            self.coverage.append(
                m.Infra.PlanCollectionCoverage(
                    source_id=source.id,
                    provider=source.provider,
                    adapter=source.adapter,
                    files=len(paths),
                    status="collected" if paths else "empty",
                ),
            )

        def sorted_revisions(self) -> list[m.Infra.PlanCollectionRevision]:
            """Return the history sorted by source time, then identity.

            Returns:
                The resulting ``list[m.Infra.PlanCollectionRevision]``.

            """
            return sorted(
                self.revisions_by_identity.values(),
                key=lambda item: (
                    item.source_updated_at_utc is not None,
                    item.source_updated_at_utc or "",
                    item.identity,
                ),
            )

        def verify_immutable_owned(self) -> None:
            """Require flagged immutable artifacts to remain byte-identical.

            Raises:
                ValueError: If immutable canonical artifact changed or
                    disappeared.

            """
            for path, digest in self.invalid_owned.items():
                content = self.desired.get(path)
                if content is None or sha256(content).hexdigest() != digest:
                    msg = f"immutable canonical artifact changed or disappeared: {path}"
                    raise ValueError(msg)

        def record_manifest(self) -> None:
            """Serialize the updated manifest into the desired outputs."""
            manifest_path = self.canonical / "collection-manifest.json"
            owned = {item.relative_path: item for item in self.manifest.artifacts}
            owned.update({
                path.relative_to(self.canonical): m.Infra.PlanCollectionOwnedArtifact(
                    relative_path=path.relative_to(self.canonical),
                    digest=sha256(content).hexdigest(),
                )
                for path, content in self.desired.items()
            })
            self.desired[manifest_path] = (
                m.Infra.PlanCollectionManifest(
                    configuration_sha256=(
                        FlextInfraUtilitiesDocsCollectionSources
                        .collection_configuration_digest(self.configuration)
                    ),
                    coverage=tuple(self.coverage),
                    revisions=tuple(self.history),
                    artifacts=tuple(owned[path] for path in sorted(owned)),
                ).model_dump_json(indent=2)
                + "\n"
            ).encode()

        def mirror_projection(self) -> None:
            """Mirror every desired canonical output into the projection root."""
            projection = self.projection
            if projection is not None:
                for path, content in tuple(self.desired.items()):
                    self.desired[projection / path.relative_to(self.canonical)] = (
                        content
                    )

    @classmethod
    def _validated_collection_roots(
        cls,
        repository_root: Path,
        configuration: m.Infra.PlanCollectionConfig,
    ) -> tuple[Path, Path, Path | None]:
        """Validate and resolve the collection canonical and projection roots.

        Returns:
            The resulting ``(root, canonical, projection)`` triple.

        Raises:
            ValueError: If unsafe canonical collection directory; or if unsafe
                collection projection association.

        """
        root = repository_root.absolute()
        relative = configuration.canonical_dir
        if relative.is_absolute() or not relative.parts or ".." in relative.parts:
            msg = f"unsafe canonical collection directory: {relative}"
            raise ValueError(msg)
        canonical = root / relative
        projection = (
            configuration.projection_root.expanduser()
            if configuration.projection_root is not None
            else None
        )
        if projection is not None and (
            not projection.is_absolute()
            or ".." in projection.parts
            or projection == canonical
        ):
            msg = f"unsafe collection projection association: {projection}"
            raise ValueError(msg)
        return root, canonical, projection

    @staticmethod
    def _require_unique_sources(
        configuration: m.Infra.PlanCollectionConfig,
    ) -> None:
        """Require every collection source identity to be unique.

        Raises:
            ValueError: If collection source identities must be unique.

        """
        identifiers = tuple(source.id for source in configuration.sources)
        if len(set(identifiers)) != len(identifiers):
            msg = "collection source identities must be unique"
            raise ValueError(msg)

    @classmethod
    def _disabled_collection_bundle(
        cls,
        root: Path,
        state: _CollectionState,
    ) -> m.Infra.PlanCollectionBundle:
        """Plan removal-only effects when collection is disabled.

        Returns:
            The resulting ``m.Infra.PlanCollectionBundle``.

        """
        canonical = state.canonical
        owned_outputs = {
            canonical / "collection-manifest.json",
            *(
                canonical / artifact.relative_path
                for artifact in state.manifest.artifacts
            ),
        }
        for path in owned_outputs:
            cls.collection_capture(path, state.states)
        plans_list = [
            FlextInfraUtilitiesDocsContract.docs_file_plan(
                root,
                path,
                None,
                desired_mode=None,
                inputs=tuple(state.states.values()),
            ).unwrap()
            for path in sorted(owned_outputs)
        ]
        directories = {
            parent
            for path in owned_outputs
            for parent in path.parents
            if parent != canonical and parent.is_relative_to(canonical)
        }
        return m.Infra.PlanCollectionBundle(
            files=tuple(plans_list),
            prunable_directories=tuple(
                sorted(
                    directories,
                    key=lambda path: (len(path.parts), path.as_posix()),
                    reverse=True,
                ),
            ),
            revisions=(),
            coverage=(),
        )

    @classmethod
    def _collect_source_paths(
        cls,
        source_root: Path,
        source: m.Infra.PlanCollectionSource,
        paths: tuple[Path, ...],
        state: _CollectionState,
        excluded_outputs: tuple[Path, ...],
    ) -> None:
        """Collect every published artifact of one source path set."""
        for path in paths:
            artifacts = cls.collection_artifacts(path, source, excluded_outputs)
            state.absorb_artifacts(artifacts)
            incoming_revision = cls._docs_incoming_revision(
                state.canonical,
                source_root,
                source,
                artifacts,
                previous=state.previous_revision(path),
            )
            revision = cls._docs_collect_revision(
                state.canonical,
                incoming_revision,
                artifacts,
                state.desired,
                states=state.states,
            )
            state.record_revision(revision)

    @classmethod
    def _collect_all_sources(
        cls,
        root: Path,
        configuration: m.Infra.PlanCollectionConfig,
        state: _CollectionState,
        excluded_outputs: tuple[Path, ...],
    ) -> None:
        """Run every configured source through its collection adapter.

        Raises:
            ValueError: If private source cannot publish; or if file source
                requires publication approval.

        """
        for source in configuration.sources:
            paths = cls.collection_source_files(root, source, excluded_outputs)
            if source.adapter == "private-inventory":
                if source.publication != "private":
                    msg = f"private source cannot publish: {source.id}"
                    raise ValueError(msg)
                state.record_private(source, paths)
                continue
            state.require_publishable(source)
            source_root = cls.collection_source_root(root, source)
            cls._collect_source_paths(
                source_root,
                source,
                paths,
                state,
                excluded_outputs,
            )
            state.record_public(source, paths)

    @staticmethod
    def _collection_index_text(
        revisions: Sequence[m.Infra.PlanCollectionRevision],
    ) -> str:
        """Render the collected-plan index markdown.

        Returns:
            The resulting ``str``.

        """
        lines = [
            "# Collected plans",
            "",
            "Source order only; execution status and closure belong to Beads.",
            "",
        ]
        lines.extend(
            f"- [{revision.identity}]({revision.canonical_path.name})"
            f" — {revision.source_updated_at or 'source update unknown'}"
            + (
                " (chronology unresolved: no timezone-aware instant)"
                if revision.source_updated_at_utc is None
                else ""
            )
            for revision in revisions
        )
        index, _changed = FlextInfraUtilitiesDocsContract.docs_contract_update_toc(
            "\n".join(lines) + "\n",
        )
        return index

    @classmethod
    def _planned_collection_bundle(
        cls,
        root: Path,
        state: _CollectionState,
        revisions: Sequence[m.Infra.PlanCollectionRevision],
    ) -> m.Infra.PlanCollectionBundle:
        """Plan every desired output and assemble the collection bundle.

        Returns:
            The resulting ``m.Infra.PlanCollectionBundle``.

        Raises:
            ValueError: If a destination is undeclared.

        """
        canonical = state.canonical
        projection = state.projection
        state.record_manifest()
        state.mirror_projection()
        plans: list[m.Infra.CodegenFilePlan] = []
        for path, content in sorted(state.desired.items()):
            owner = root if path.is_relative_to(canonical) else projection
            if owner is None:
                msg = f"undeclared collection destination: {path}"
                raise ValueError(msg)
            planned = FlextInfraUtilitiesDocsContract.docs_file_plan(
                owner,
                path,
                content,
                desired_mode=c.Infra.DOCS_ARTIFACT_MODE,
                inputs=tuple(state.states.values()),
            ).unwrap()
            if path in state.states and planned.before != state.states[path]:
                msg = f"collection publication target changed after capture: {path}"
                raise ValueError(msg)
            plans.append(planned)
        return m.Infra.PlanCollectionBundle(
            files=tuple(plans),
            revisions=tuple(revisions),
            coverage=tuple(state.coverage),
        )

    @classmethod
    def docs_collect_plan_files(
        cls,
        repository_root: Path,
        configuration: m.Infra.PlanCollectionConfig,
        *,
        inputs: tuple[m.Cli.AtomicFileState, ...] = (),
    ) -> m.Infra.PlanCollectionBundle:
        """Capture sources before any canonical or home projection writes.

        Returns:
            The resulting ``m.Infra.PlanCollectionBundle``.

        """
        root, canonical, projection = cls._validated_collection_roots(
            repository_root,
            configuration,
        )
        cls._require_unique_sources(configuration)
        states: MutableMapping[Path, m.Cli.AtomicFileState] = {
            state.path: state for state in inputs
        }
        manifest, excluded_outputs = cls.docs_collection_manifest(
            canonical,
            projection,
            states,
        )
        state = cls._CollectionState(canonical, projection, manifest, configuration)
        state.states = states
        if not configuration.enabled:
            return cls._disabled_collection_bundle(root, state)
        state.absorb_owned_artifacts()
        cls._collect_all_sources(root, configuration, state, excluded_outputs)
        revisions = state.sorted_revisions()
        index_text = cls._collection_index_text(revisions)
        state.desired[canonical / "collection-index.md"] = index_text.encode()
        state.verify_immutable_owned()
        return cls._planned_collection_bundle(root, state, revisions)

    @classmethod
    def docs_verify_plan_collection(
        cls,
        repository_root: Path,
        configuration: m.Infra.PlanCollectionConfig,
        *,
        inputs: tuple[m.Cli.AtomicFileState, ...] = (),
    ) -> bool:
        """Verify canonical evidence without collecting sources or writing output.

        Returns:
            True only after every original observation remains unchanged.

        Raises:
            FileNotFoundError: If the canonical manifest is absent.
            ValueError: If collection is disabled or evidence is incomplete.

        """
        if not configuration.enabled:
            msg = "collection verification requires enabled collection"
            raise ValueError(msg)
        _root, canonical, _projection = cls._validated_collection_roots(
            repository_root, configuration,
        )
        cls._require_unique_sources(configuration)
        states: MutableMapping[Path, m.Cli.AtomicFileState] = {
            state.path: state for state in inputs
        }
        before = cls.collection_capture(canonical / "collection-manifest.json", states)
        if before.content is None:
            raise FileNotFoundError(before.path)
        manifest = m.Infra.PlanCollectionManifest.model_validate_json(before.content)
        cls._verify_collection_associations(configuration, manifest)
        cls._validate_revision_locators(manifest)
        cls._verify_collection_artifacts(canonical, manifest, states)
        cls._verify_collection_revisions(canonical, manifest, states)
        FlextInfraUtilitiesDocsContract.atomic_verify_binary_file_states(
            tuple(states.values()),
        ).unwrap()
        return True

    @classmethod
    def _verify_collection_associations(
        cls,
        configuration: m.Infra.PlanCollectionConfig,
        manifest: m.Infra.PlanCollectionManifest,
    ) -> None:
        """Require the published source association and coverage proof.

        Raises:
            ValueError: If associations, coverage or publication authorization differ.

        """
        if manifest.configuration_sha256 != cls.collection_configuration_digest(configuration):
            msg = "collection configuration differs from published association proof"
            raise ValueError(msg)
        sources = {source.id: source for source in configuration.sources}
        coverage = {item.source_id: item for item in manifest.coverage}
        if len(coverage) != len(manifest.coverage) or set(coverage) != set(sources):
            msg = "published collection source coverage is incomplete or duplicated"
            raise ValueError(msg)
        for identity, source in sources.items():
            item = coverage[identity]
            if (
                source.adapter != "files"
                or source.publication != "plan-artifacts"
                or item.adapter != source.adapter
                or item.provider != source.provider
                or item.private_paths
            ):
                msg = f"source has no complete publishable collection proof: {identity}"
                raise ValueError(msg)
            if item.status != ("collected" if item.files else "empty"):
                msg = f"published collection source coverage is inconsistent: {identity}"
                raise ValueError(msg)

    @classmethod
    def _verify_collection_artifacts(
        cls,
        canonical: Path,
        manifest: m.Infra.PlanCollectionManifest,
        states: MutableMapping[Path, m.Cli.AtomicFileState],
    ) -> None:
        """Verify every manifest-owned canonical file through its original snapshot.

        Raises:
            ValueError: If the index or owned artifact inventory is incomplete or changed.

        """
        paths = tuple(
            cls._validated_owned_path(artifact.relative_path)
            for artifact in manifest.artifacts
        )
        if len(set(paths)) != len(paths) or Path("collection-index.md") not in paths:
            msg = "published collection artifact inventory is incomplete or duplicated"
            raise ValueError(msg)
        for artifact in manifest.artifacts:
            observed = cls.collection_capture(canonical / artifact.relative_path, states)
            if (
                not cls._artifact_matches(observed, artifact)
                or observed.mode != c.Infra.DOCS_ARTIFACT_MODE
            ):
                msg = f"published collection artifact is missing or changed: {observed.path}"
                raise ValueError(msg)

    @classmethod
    def _verify_collection_revisions(
        cls,
        canonical: Path,
        manifest: m.Infra.PlanCollectionManifest,
        states: MutableMapping[Path, m.Cli.AtomicFileState],
    ) -> None:
        """Compare immutable provenance and incoming digests with their published owner.

        Raises:
            ValueError: If revision evidence is absent, duplicated or changed.

        """
        identities = tuple((item.identity, item.digest) for item in manifest.revisions)
        if len(set(identities)) != len(identities):
            msg = "published collection revision identities are duplicated"
            raise ValueError(msg)
        for revision in manifest.revisions:
            incoming = canonical / cls._validated_owned_path(
                revision.canonical_path.with_suffix("") / "incoming" / revision.digest,
            )
            names = (Path(revision.source_path.name), *(
                Path(revision.source_path.name).with_suffix("") / name
                for name in revision.attachments
            ))
            paths = (
                incoming / "plan.md",
                *(incoming / "attachments" / name for name in revision.attachments),
            )
            required = (canonical / revision.canonical_path, incoming / "provenance.json", *paths)
            if any(path not in states or states[path].content is None for path in required):
                msg = f"published collection revision has no complete owned evidence: {revision.identity}"
                raise ValueError(msg)
            provenance = m.Infra.PlanCollectionRevision.model_validate_json(
                states[incoming / "provenance.json"].content,
            )
            if provenance != revision or cls.collection_revision_digest(
                tuple((name, states[path]) for name, path in zip(names, paths, strict=True)),
            ) != revision.digest:
                msg = f"published collection revision provenance or digest differs: {revision.identity}"
                raise ValueError(msg)

    @classmethod
    def _docs_incoming_revision(
        cls,
        canonical: Path,
        source_root: Path,
        source: m.Infra.PlanCollectionSource,
        artifacts: tuple[m.Cli.AtomicFileState, ...],
        *,
        previous: m.Infra.PlanCollectionRevision | None,
    ) -> m.Infra.PlanCollectionRevision:
        """Derive the revision one collected plan and its companions represent.

        ``artifacts`` starts with the plan itself, followed by its companion
        attachments; a previously recorded revision keeps its identity and its
        canonical destination, which must stay inside ``canonical``.

        Returns:
            The resulting ``m.Infra.PlanCollectionRevision``.

        Raises:
            ValueError: If plan content absent; or if absent collected artifact.

        """
        path = artifacts[0].path
        identity = (
            previous.identity
            if previous is not None
            else sha256(
                f"{source.id}:{path.relative_to(source_root).as_posix()}".encode(),
            ).hexdigest()
        )
        digest = cls.collection_revision_digest(
            tuple((artifact.path.relative_to(path.parent), artifact) for artifact in artifacts),
        )
        plan = artifacts[0].content
        if plan is None:
            msg = f"plan content absent: {path}"
            raise ValueError(msg)
        original, normalized = cls.collection_source_updated(
            plan,
            source.updated_fields,
        )
        target = canonical / (
            previous.canonical_path
            if previous is not None
            else Path(f"{source.id}-{path.stem}-{identity[:16]}.md")
        )
        return m.Infra.PlanCollectionRevision(
            identity=identity,
            provider=source.provider,
            source_id=source.id,
            source_path=path.relative_to(source_root),
            driver=source.driver,
            driver_version=source.driver_version,
            digest=digest,
            canonical_path=target.relative_to(canonical),
            source_updated_at=normalized or original,
            source_updated_at_original=original,
            source_updated_at_utc=normalized,
            collected_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            attachments=tuple(
                attachment.path.relative_to(path.with_suffix("")).as_posix()
                for attachment in artifacts[1:]
            ),
        )

    @classmethod
    def _docs_collect_revision(
        cls,
        canonical: Path,
        incoming_revision: m.Infra.PlanCollectionRevision,
        artifacts: tuple[m.Cli.AtomicFileState, ...],
        desired: MutableMapping[Path, bytes],
        *,
        states: MutableMapping[Path, m.Cli.AtomicFileState],
    ) -> m.Infra.PlanCollectionRevision:
        """Keep curated canonical text intact while recording incoming revisions.

        Returns:
            The resulting ``m.Infra.PlanCollectionRevision``.

        Raises:
            ValueError: If plan content absent; or if attachment content absent; or if
                incoming revision receipt identity changed.

        """
        target = canonical / incoming_revision.canonical_path
        incoming = target.with_suffix("") / "incoming" / incoming_revision.digest
        plan = artifacts[0].content
        if plan is None:
            msg = f"plan content absent: {artifacts[0].path}"
            raise ValueError(msg)
        existing = cls.collection_capture(target, states)
        desired[target] = existing.content if existing.content is not None else plan
        desired[incoming / "plan.md"] = plan
        for name, attachment in zip(
            incoming_revision.attachments,
            artifacts[1:],
            strict=True,
        ):
            if attachment.content is None:
                msg = f"attachment content absent: {artifacts[0].path}"
                raise ValueError(msg)
            desired[incoming / "attachments" / name] = attachment.content
        revision = incoming_revision
        receipt_path = incoming / "provenance.json"
        receipt = cls.collection_capture(receipt_path, states)
        if receipt.content is not None:
            recorded = m.Infra.PlanCollectionRevision.model_validate_json(
                receipt.content,
            )
            if (recorded.identity, recorded.digest) != (
                revision.identity,
                revision.digest,
            ):
                msg = f"incoming revision receipt identity changed: {receipt_path}"
                raise ValueError(msg)
            revision = recorded
        desired[receipt_path] = (
            receipt.content
            if receipt.content is not None
            else (revision.model_dump_json(indent=2) + "\n").encode()
        )
        return revision


__all__: list[str] = ["FlextInfraUtilitiesDocsCollection"]
