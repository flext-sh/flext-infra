"""Immutable source-bundle preparation for the documentation generator.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from time import perf_counter
from typing import TYPE_CHECKING

from flext_infra import c, m, r, t, u
from flext_infra.codegen.codegen_preconditions import FlextInfraCodegenPreconditions

if TYPE_CHECKING:
    from collections.abc import Iterator

    from flext_infra import p

type _DocsScopeArtifacts = t.Pair[
    m.Infra.DocScope,
    t.VariadicTuple[t.Triple[Path, Path, str | None]],
]
type _DocsBundleSources = tuple[
    t.VariadicTuple[m.Cli.AtomicFileState],
    t.VariadicTuple[Path],
    Path | None,
    t.VariadicTuple[m.Cli.AtomicDirectoryChainPlan],
]
type _DocsScopeCaptures = t.Triple[
    t.VariadicTuple[Path],
    t.VariadicTuple[m.Cli.AtomicFileState],
    t.VariadicTuple[m.Cli.AtomicDirectoryChainPlan],
]


class FlextInfraDocGeneratorBundleMixin:
    """Freeze one render and every authenticated input before planning."""

    @classmethod
    def _prepare_batches(
        cls,
        request: m.Infra.DocsGenerateRequest,
    ) -> Iterator[p.Result[m.Infra.DocsGenerationBundle]]:
        """Capture the next owning scope only after the preceding batch settles.

        Args:
            request: The documentation generation request containing repository root and
              output directory.

        Yields:
            Results of the documentation generation bundle preparation for each batch.
        """
        roots = u.Infra.docs_repository_roots(request.repository_root)
        if roots.failure:
            yield r[m.Infra.DocsGenerationBundle].from_failure(roots)
            return
        root = roots.value[0]
        declaration = u.Cli.atomic_read_binary_file_state(
            root / c.Infra.GITMODULES,
            required=False,
        )
        if declaration.failure:
            yield r[m.Infra.DocsGenerationBundle].from_failure(declaration)
            return
        output_dir = u.Cli.resolve_optional_path(
            request.output_dir,
            default=Path(c.Infra.DEFAULT_DOCS_OUTPUT_DIR),
        )
        scopes = cls._validated_scopes(root, request, output_dir)
        if scopes.failure:
            yield r[m.Infra.DocsGenerationBundle].from_failure(scopes)
            return
        selected, aggregate = scopes.value
        yield from cls._scope_batches(root, declaration.value, selected, aggregate)

    @classmethod
    def _scope_batches(
        cls,
        root: Path,
        declaration: m.Cli.AtomicFileState,
        selected: t.VariadicTuple[m.Infra.DocScope],
        aggregate: t.VariadicTuple[m.Infra.DocScope],
    ) -> Iterator[p.Result[m.Infra.DocsGenerationBundle]]:
        """Yield one settled bundle per non-collocated selected scope.

        Args:
            root: The authenticated repository root.
            declaration: The frozen ``.gitmodules`` file state.
            selected: The selected documentation output scopes.
            aggregate: The aggregate scopes over the complete project catalog.

        Yields:
            Results of the documentation generation bundle preparation for each batch.
        """
        root_scope = next(
            (scope for scope in selected if scope.name == c.Infra.RK_ROOT),
            None,
        )
        for scope in selected:
            if cls._is_collocated_workspace_project(scope, root_scope=root_scope):
                continue
            producer = FlextInfraCodegenPreconditions.capture_producer()
            if producer.failure:
                yield r[m.Infra.DocsGenerationBundle].from_failure(producer)
                return
            captured = cls._scope_batch_captures(root, declaration, scope, aggregate)
            if captured.failure:
                yield r[m.Infra.DocsGenerationBundle].from_failure(captured)
                return
            source_roots, states, directories = captured.value
            governance = cls._captured_governance_source(root, states)
            if governance.failure:
                yield r[m.Infra.DocsGenerationBundle].from_failure(governance)
                return
            batch_scopes = (
                scope,
                *(
                    item
                    for item in selected
                    if cls._is_collocated_workspace_project(
                        item,
                        root_scope=scope if scope.name == c.Infra.RK_ROOT else None,
                    )
                ),
            )
            rendered = cls._rendered_scopes(
                root,
                (batch_scopes, aggregate),
                states,
                directories,
                governance.value,
            )
            if rendered.failure:
                yield r[m.Infra.DocsGenerationBundle].from_failure(rendered)
                return
            yield cls._validated_bundle(
                root,
                rendered.value,
                (
                    states,
                    source_roots,
                    scope.path if scope.name != c.Infra.RK_ROOT else None,
                    directories,
                ),
                producer=producer.value,
            )

    @classmethod
    def _scope_batch_captures(
        cls,
        root: Path,
        declaration: m.Cli.AtomicFileState,
        scope: m.Infra.DocScope,
        aggregate: t.VariadicTuple[m.Infra.DocScope],
    ) -> p.Result[_DocsScopeCaptures]:
        """Authenticate one scope's sources against the frozen declaration.

        Args:
            root: The authenticated repository root.
            declaration: The frozen ``.gitmodules`` file state.
            scope: The documentation output scope being captured.
            aggregate: The aggregate scopes over the complete project catalog.

        Returns:
            The resulting ``(source_roots, source_states, source_directories)``
            triple.

        """
        result_type = r[_DocsScopeCaptures]
        source_roots = u.Infra.docs_scope_source_roots(root, scope, aggregate)
        source_scope = scope.path if scope.name != c.Infra.RK_ROOT else None
        paths = u.Infra.docs_source_paths_for_roots(
            source_roots,
            source_scope=source_scope,
        )
        if paths.failure:
            return result_type.from_failure(paths)
        sources = u.Infra.required_file_states(paths.value)
        if sources.failure:
            return result_type.from_failure(sources)
        manifest = u.Cli.atomic_read_binary_file_state(
            declaration.path,
            required=False,
        )
        if manifest.failure:
            return result_type.from_failure(manifest)
        if manifest.value != declaration:
            return result_type.fail(
                "docs scope inventory changed before batch admission",
            )
        states = tuple(
            sorted(
                {
                    item.path: item
                    for item in (
                        *sources.value,
                        declaration,
                    )
                }.values(),
                key=lambda item: item.path,
            )
        )
        directories = u.Infra.docs_source_directories(
            source_roots,
            source_scope=source_scope,
        )
        if directories.failure:
            return result_type.from_failure(directories)
        return result_type.ok((source_roots, states, directories.value))

    @staticmethod
    def _is_collocated_workspace_project(
        scope: m.Infra.DocScope,
        *,
        root_scope: m.Infra.DocScope | None,
    ) -> bool:
        """Return whether a project scope shares the aggregate root path.

        ``root_scope`` is ``None`` whenever the root does not participate as
        a docs output scope (e.g. conform's DECLARED scope); no scope can be
        collocated with an absent root.

        Returns:
            Whether a project scope shares the aggregate root path.

        """
        return (
            root_scope is not None
            and scope.name != c.Infra.RK_ROOT
            and scope.path == root_scope.path
        )

    @staticmethod
    def _validate_scope_targets(
        scopes: t.SequenceOf[m.Infra.DocScope],
        output_dir: Path,
    ) -> p.Result[bool]:
        """Require builders to preserve each lexical scope and report target.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        for scope in scopes:
            expected = scope.path / output_dir
            if scope.report_dir != expected:
                return r[bool].fail(
                    "docs report directory is aliased or escaped: "
                    f"expected {expected}, observed {scope.report_dir}",
                )
        return r[bool].ok(value=True)

    @classmethod
    def _prepare_request(
        cls,
        request: m.Infra.DocsGenerateRequest,
    ) -> p.Result[m.Infra.DocsGenerationBundle]:
        """Render one canonical docs artifact inventory from the frozen snapshot.

        Publication admits sources and topology once per owning scope batch.

        Returns:
            The resulting ``p.Result[m.Infra.DocsGenerationBundle]``.

        """
        producer = FlextInfraCodegenPreconditions.capture_producer()
        if producer.failure:
            return r[m.Infra.DocsGenerationBundle].from_failure(producer)
        started_at = perf_counter()
        sources = cls._discovered_sources(request, started_at)
        if sources.failure:
            return r[m.Infra.DocsGenerationBundle].from_failure(sources)
        repository_root, selected_roots, source_states = sources.value
        roots = u.Infra.docs_repository_roots(
            repository_root,
            tuple(selected_roots),
        )
        if roots.failure:
            return r[m.Infra.DocsGenerationBundle].from_failure(roots)
        directories = u.Infra.docs_source_directories(roots.value)
        if directories.failure:
            return r[m.Infra.DocsGenerationBundle].from_failure(directories)
        rendered = cls._rendered_scope_inventory(
            repository_root,
            request,
            source_states,
            directories.value,
        )
        if rendered.failure:
            return r[m.Infra.DocsGenerationBundle].from_failure(rendered)
        return cls._validated_bundle(
            repository_root,
            rendered.value,
            (source_states, roots.value, None, directories.value),
            producer=producer.value,
        )

    @classmethod
    def _rendered_scope_inventory(
        cls,
        repository_root: Path,
        request: m.Infra.DocsGenerateRequest,
        source_states: t.VariadicTuple[m.Cli.AtomicFileState],
        source_directories: t.VariadicTuple[m.Cli.AtomicDirectoryChainPlan],
    ) -> p.Result[list[_DocsScopeArtifacts]]:
        """Resolve the docs scopes, their governance source and artifacts.

        Args:
            repository_root: Repository root owning the docs inventory.
            request: Canonical docs generation request.
            source_states: Authenticated docs source states.
            source_directories: Authenticated source directory chains.

        Returns:
            The rendered scope artifacts, or the first resolution failure.
        """
        output_dir = u.Cli.resolve_optional_path(
            request.output_dir,
            default=Path(c.Infra.DEFAULT_DOCS_OUTPUT_DIR),
        )
        scopes = cls._validated_scopes(repository_root, request, output_dir)
        if scopes.failure:
            return r[list[_DocsScopeArtifacts]].from_failure(scopes)
        governance = cls._captured_governance_source(repository_root, source_states)
        if governance.failure:
            return r[list[_DocsScopeArtifacts]].from_failure(governance)
        return cls._rendered_scopes(
            repository_root,
            scopes.value,
            source_states,
            source_directories,
            governance.value,
        )

    @classmethod
    def _discovered_sources(
        cls,
        request: m.Infra.DocsGenerateRequest,
        started_at: float,
    ) -> p.Result[t.Triple[Path, list[Path], t.VariadicTuple[m.Cli.AtomicFileState]]]:
        """Discover, select, and authenticate the docs source inventory.

        Returns:
            The resulting ``(repository_root, selected_roots, source_states)``
            triple.

        """
        result_type = r[
            t.Triple[Path, list[Path], t.VariadicTuple[m.Cli.AtomicFileState]]
        ]
        roots = u.Infra.docs_repository_roots(request.repository_root)
        if roots.failure:
            return result_type.from_failure(roots)
        repository_root = roots.value[0]
        selected_names = u.Infra.normalize_sequence_values(request.projects) or ()
        selected_roots: list[Path] = []
        for name in selected_names:
            selector = Path(name)
            if selector.is_absolute() or ".." in selector.parts:
                return result_type.fail(
                    f"docs project selector escapes workspace: {name}",
                )
            selected_roots.append(repository_root / selector)
        source_paths = u.Infra.docs_source_paths(repository_root, tuple(selected_roots))
        if source_paths.failure:
            return result_type.from_failure(source_paths)
        u.Cli.info(
            f"docs: discovered {len(source_paths.value)} source paths in "
            f"{perf_counter() - started_at:.2f}s",
        )
        source_roots = u.Infra.docs_repository_roots(
            repository_root, tuple(selected_roots)
        )
        if source_roots.failure:
            return result_type.from_failure(source_roots)
        sources = cls._captured_source_states(source_paths.value, source_roots.value)
        if sources.failure:
            return result_type.from_failure(sources)
        u.Cli.info(
            f"docs: authenticated {len(sources.value)} source paths in "
            f"{perf_counter() - started_at:.2f}s",
        )
        return result_type.ok((repository_root, selected_roots, sources.value))

    @staticmethod
    def _captured_source_states(
        paths: t.VariadicTuple[Path],
        roots: t.SequenceOf[Path],
    ) -> p.Result[t.VariadicTuple[m.Cli.AtomicFileState]]:
        """Retain the configuration reader's declared absence witnesses.

        Args:
            paths: Declared docs source paths to authenticate.
            roots: Repository roots whose configuration inputs are consulted.

        Returns:
            The authenticated source states with every declared absence
            witness retained.
        """
        result_type = r[t.VariadicTuple[m.Cli.AtomicFileState]]
        captured = u.Infra.required_file_states(paths)
        if captured.failure:
            return result_type.from_failure(captured)
        states = list(captured.value)
        for root in roots:
            configuration = u.Infra.load_config_document_inputs(
                root,
                filename=c.Infra.CODEGEN_CONFIG_FILENAME,
            )
            if configuration.failure:
                return result_type.from_failure(configuration)
            states.extend(configuration.value.sources)
        return FlextInfraCodegenPreconditions.unique_states(tuple(states))

    @classmethod
    def _validated_scopes(
        cls,
        repository_root: Path,
        request: m.Infra.DocsGenerateRequest,
        output_dir: Path,
    ) -> p.Result[
        t.Pair[
            t.VariadicTuple[m.Infra.DocScope],
            t.VariadicTuple[m.Infra.DocScope],
        ]
    ]:
        """Build and target-validate the selected and aggregate doc scopes.

        Returns:
            The resulting ``(selected_scopes, aggregate_scopes)`` pair.

        """
        result_type = r[
            t.Pair[
                t.VariadicTuple[m.Infra.DocScope],
                t.VariadicTuple[m.Infra.DocScope],
            ]
        ]
        selected = u.Infra.build_scopes(
            repository_root,
            request.projects,
            output_dir,
            include_root=request.include_root,
        )
        if selected.failure:
            return result_type.from_failure(selected)
        selected_targets = cls._validate_scope_targets(selected.value, output_dir)
        if selected_targets.failure:
            return result_type.from_failure(selected_targets)
        # Why (X-47): the aggregate inventory always includes root (independent
        # of `request.include_root`) because `docs_root_artifacts` needs the
        # complete project catalog whenever the root scope IS rendered; it is
        # simply unused when `selected` excludes root.
        aggregate = u.Infra.build_scopes(
            repository_root,
            None,
            output_dir,
            include_root=True,
        )
        if aggregate.failure:
            return result_type.from_failure(aggregate)
        aggregate_targets = cls._validate_scope_targets(aggregate.value, output_dir)
        if aggregate_targets.failure:
            return result_type.from_failure(aggregate_targets)
        return result_type.ok((tuple(selected.value), tuple(aggregate.value)))

    @classmethod
    def _rendered_scopes(
        cls,
        repository_root: Path,
        scopes: t.Pair[
            t.VariadicTuple[m.Infra.DocScope],
            t.VariadicTuple[m.Infra.DocScope],
        ],
        source_states: t.VariadicTuple[m.Cli.AtomicFileState],
        source_directories: t.VariadicTuple[m.Cli.AtomicDirectoryChainPlan] = (),
        governance_source: m.Infra.CodegenBootstrapSource | None = None,
    ) -> p.Result[list[_DocsScopeArtifacts]]:
        """Render one docs artifact set per selected scope.

        Returns:
            The resulting per-scope rendered artifacts.

        """
        selected, aggregate = scopes
        selected = tuple(
            u.Infra.docs_scope_from_sources(scope, source_states).model_copy(
                update={"governance_source": governance_source}
            )
            for scope in selected
        )
        if any(scope.name == c.Infra.RK_ROOT for scope in selected):
            aggregate = tuple(
                u.Infra.docs_scope_from_sources(scope, source_states).model_copy(
                    update={"governance_source": governance_source}
                )
                for scope in aggregate
            )
        root_scope: m.Infra.DocScope | None = (
            selected[0] if selected and selected[0].name == c.Infra.RK_ROOT else None
        )
        rendered: list[_DocsScopeArtifacts] = []
        for scope in selected:
            scope_started_at = perf_counter()
            if cls._is_collocated_workspace_project(scope, root_scope=root_scope):
                rendered.append((scope, ()))
                continue
            artifacts = u.Infra.docs_scope_artifacts(
                scope,
                repository_root=repository_root,
                aggregate_scopes=aggregate,
                source_states=source_states,
                source_directories=source_directories,
            )
            if artifacts.failure:
                return r[list[_DocsScopeArtifacts]].from_failure(artifacts)
            rendered.append((scope, artifacts.value))
            u.Cli.info(
                f"docs: rendered {scope.name} artifacts={len(artifacts.value)} "
                f"elapsed={perf_counter() - scope_started_at:.2f}s",
            )
        return r[list[_DocsScopeArtifacts]].ok(rendered)

    @classmethod
    def _normalized_scope_artifacts(
        cls,
        rendered: list[_DocsScopeArtifacts],
    ) -> p.Result[list[m.Infra.DocsScopeArtifacts]]:
        """Normalize rendered artifacts and bind each to its owning scope.

        Returns:
            The resulting normalized per-scope artifact sets.

        """
        normalized = u.Infra.docs_normalize_artifacts(
            tuple(artifact for _scope, artifacts in rendered for artifact in artifacts),
        )
        if normalized.failure:
            return r[list[m.Infra.DocsScopeArtifacts]].from_failure(normalized)
        normalized_scopes: list[m.Infra.DocsScopeArtifacts] = []
        offset = 0
        for scope, scope_artifacts in rendered:
            size = len(scope_artifacts)
            normalized_artifacts: list[m.Infra.DocsRenderedArtifact] = []
            for project, target, content in normalized.value[offset : offset + size]:
                if project != scope.path:
                    return r[list[m.Infra.DocsScopeArtifacts]].fail(
                        f"docs artifact owner differs from scope: {target}",
                    )
                normalized_content = content
                if normalized_content is not None and target.suffix == ".md":
                    normalized_content = c.Infra.FENCE_NOTEST_RE.sub(
                        r"```\1",
                        normalized_content,
                    )
                    normalized_content = u.Infra.docs_contract_update_toc(
                        normalized_content,
                    )[0]
                normalized_artifacts.append(
                    m.Infra.DocsRenderedArtifact(
                        relative_path=target.relative_to(project),
                        desired_content=(
                            None
                            if normalized_content is None
                            else normalized_content.encode(c.DEFAULT_ENCODING)
                        ),
                        desired_mode=(
                            c.Infra.DOCS_ARTIFACT_MODE
                            if normalized_content is not None
                            else None
                        ),
                    ),
                )
            normalized_scopes.append(
                m.Infra.DocsScopeArtifacts(
                    scope=scope,
                    artifacts=tuple(normalized_artifacts),
                ),
            )
            offset += size
        return r[list[m.Infra.DocsScopeArtifacts]].ok(normalized_scopes)

    @classmethod
    def _validated_bundle(
        cls,
        repository_root: Path,
        rendered: list[_DocsScopeArtifacts],
        sources: _DocsBundleSources,
        *,
        producer: m.Infra.CodegenPhaseAnalysis,
    ) -> p.Result[m.Infra.DocsGenerationBundle]:
        """Validate the rendered docs generation bundle.

        Args:
            repository_root: The root path of the repository.
            rendered: The list of rendered documentation scope artifacts.
            sources: The captured source states, roots, scope and directories
                of the documentation inventory.
            producer: The captured producer analysis of the generation.

        Returns:
            The resulting ``p.Result[m.Infra.DocsGenerationBundle]``.

        """
        source_states, source_roots, source_scope, source_directories = sources
        normalized = cls._normalized_scope_artifacts(rendered)
        if normalized.failure:
            return r[m.Infra.DocsGenerationBundle].from_failure(normalized)
        validated_bundle: p.Result[m.Infra.DocsGenerationBundle] = u.validate_value(
            m.Infra.DocsGenerationBundle,
            {
                "scopes": tuple(normalized.value),
                "producer": producer,
                "source_states": source_states,
                "source_roots": source_roots,
                "source_scope": source_scope,
                "source_directories": source_directories,
                "repository_root": repository_root,
            },
        )
        if validated_bundle.failure:
            return r[m.Infra.DocsGenerationBundle].fail_op(
                "docs generation bundle validation",
                validated_bundle.error,
            )
        return r[m.Infra.DocsGenerationBundle].ok(validated_bundle.value)

    @classmethod
    def _captured_governance_source(
        cls,
        repository_root: Path,
        source_states: t.VariadicTuple[m.Cli.AtomicFileState],
    ) -> p.Result[m.Infra.CodegenBootstrapSource]:
        """Capture the referenced governance owner before rendering its links.

        Args:
            repository_root: The root path of the repository.
            source_states: The captured source states of the documentation files.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenBootstrapSource]``.
        """
        result_type = r[m.Infra.CodegenBootstrapSource]
        inputs = u.Infra.load_codegen_inputs(repository_root)
        if inputs.failure:
            return result_type.from_failure(inputs)
        captured = {item.path: item for item in source_states}
        if any(captured.get(item.path) != item for item in inputs.value.sources):
            return result_type.fail(
                "governance configuration differs from captured docs sources",
            )
        ref = cls._governance_source_ref(repository_root, inputs.value)
        if ref.failure:
            return result_type.from_failure(ref)
        return result_type.ok(
            m.Infra.CodegenBootstrapSource(url=c.Infra.GITHUB_REPO_URL, ref=ref.value)
        )

    @classmethod
    def _governance_source_ref(
        cls,
        repository_root: Path,
        inputs: m.Infra.CodegenInputs,
    ) -> p.Result[str]:
        """Resolve the governance owner's published Git reference.

        An origin that owns the canonical governance repository resolves its
        own integration line; every other checkout follows the declared
        dependency family line.

        Args:
            repository_root: Repository root whose governance is resolved.
            inputs: Loaded codegen inputs of the repository.

        Returns:
            The governance owner's Git reference, or the first resolution
            failure.
        """
        result_type = r[str]
        identity = u.Infra.git_identity(
            m.Infra.GitRepoRequest(repo_root=repository_root)
        )
        if identity.failure:
            return result_type.from_failure(identity)
        owned = cls._own_governance_branch(
            repository_root,
            identity.value.origin_remote,
            inputs,
        )
        if owned.failure:
            return result_type.from_failure(owned)
        if owned.value is not None:
            return result_type.ok(owned.value)
        line = u.Infra.flext_integration_line(
            codegen=inputs.spec,
            repository_root=repository_root,
        )
        if line.failure:
            return result_type.from_failure(line)
        if c.Infra.GITHUB_REPO_URL.rsplit("/", maxsplit=1)[0] != (
            line.value.base_url.rstrip("/")
        ):
            return result_type.fail(
                "governance owner differs from the captured dependency family",
            )
        return result_type.ok(line.value.branch)

    @classmethod
    def _own_governance_branch(
        cls,
        repository_root: Path,
        origin: str | None,
        inputs: m.Infra.CodegenInputs,
    ) -> p.Result[str | None]:
        """Resolve the integration line when the origin owns the governance.

        Args:
            repository_root: Repository root whose governance is resolved.
            origin: Origin remote URL, or ``None`` without one.
            inputs: Loaded codegen inputs of the repository.

        Returns:
            The owned governance branch, or ``None`` when another owner's
            family line governs, or the first resolution failure.
        """
        result_type = r[str | None]
        if origin is None:
            return result_type.ok(value=None)
        page = u.Infra.validate_git_remote_url(origin)
        if page.failure:
            return result_type.from_failure(page)
        if page.value.rstrip("/").removesuffix(".git") != c.Infra.GITHUB_REPO_URL:
            return result_type.ok(value=None)
        branch = u.Infra.resolve_integration_branch(
            repository_root,
            policy_branch=inputs.spec.branch_policy.integration_branch,
            inputs=inputs,
        )
        if branch.failure:
            return result_type.from_failure(branch)
        return result_type.ok(value=branch.value)


__all__: list[str] = ["FlextInfraDocGeneratorBundleMixin"]
