"""Render-bundle preparation for the documentation generator.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from functools import partial
from pathlib import Path
from time import perf_counter

from flext_infra import c, m, p, r, u

type _DocsScopeArtifacts = tuple[
    m.Infra.DocScope,
    tuple[tuple[Path, Path, str | None], ...],
]


class FlextInfraDocsGeneratorBundle:
    """Render the configured docs inventory once before planning."""

    type _DocsPresentationInputs = tuple[
        m.Infra.CodegenBootstrapSource | None,
        tuple[m.Infra.CodegenFilePlan, ...],
        tuple[m.Infra.CodegenFilePlan, ...],
    ]
    type _DocsRenderedInventory = tuple[
        list[_DocsScopeArtifacts], tuple[m.Infra.CodegenFilePlan, ...]
    ]

    @staticmethod
    def _presentation_metadata(
        scopes: Sequence[m.Infra.DocScope],
        declared_files: tuple[m.Infra.CodegenFilePlan, ...] = (),
    ) -> p.Result[tuple[m.Infra.CodegenFilePlan, ...]]:
        """Prepare only authorial YAML and the owned pyproject locale leaf.

        Returns:
            Exact metadata plans, without Python or tooling source planning.

        """
        result_type = r[tuple[m.Infra.CodegenFilePlan, ...]]
        ownership = u.Infra.pyproject_managed_file()
        if ownership.failure:
            return result_type.from_failure(ownership)
        plans: list[m.Infra.CodegenFilePlan] = []
        declared = {plan.path: plan for plan in declared_files}
        for root in dict.fromkeys(scope.path for scope in scopes):
            declaration = u.Infra.load_repository_declaration_inputs(root)
            if declaration.failure:
                return result_type.from_failure(declaration)
            previous = declared.get(root / c.PYPROJECT_FILENAME)
            source = (
                r[m.Cli.AtomicFileState].ok(previous.before)
                if previous is not None
                else u.Cli.atomic_read_binary_file_state(
                    root / c.PYPROJECT_FILENAME,
                    required=declaration.value.spec.project is not None,
                )
            )
            if source.failure:
                return result_type.from_failure(source)
            content = (
                previous.desired_content
                if previous is not None
                else source.value.content
            )
            if content is None:
                continue
            decoded = r[str].create_from_callable(
                partial(content.decode, c.DEFAULT_ENCODING)
            )
            if decoded.failure:
                return result_type.from_failure(decoded)
            projected = u.Infra.project_documentation_metadata(
                decoded.value, declaration.value.spec.project
            )
            if projected.failure:
                return result_type.from_failure(projected)
            plans.append(
                m.Infra.CodegenFilePlan(
                    project=root,
                    path=source.value.path,
                    before=source.value,
                    desired_content=projected.value.encode(c.DEFAULT_ENCODING),
                    desired_mode=(
                        previous.desired_mode
                        if previous is not None
                        else source.value.mode
                    ),
                    owner=(
                        previous.owner
                        if previous is not None
                        else ownership.value.owner
                    ),
                    policy=(
                        previous.policy
                        if previous is not None
                        else ownership.value.policy
                    ),
                    tracking=previous.tracking if previous is not None else "versioned",
                    index_before=(
                        previous.index_before if previous is not None else None
                    ),
                    tracking_dependencies=(
                        previous.tracking_dependencies if previous is not None else ()
                    ),
                )
            )
        return result_type.ok(tuple(plans))

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
        scopes: Sequence[m.Infra.DocScope],
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
        declared_files: tuple[m.Infra.CodegenFilePlan, ...] = (),
    ) -> p.Result[m.Infra.DocsGenerationBundle]:
        """Render one inventory from the live workspace sources.

        Returns:
            The rendered bundle, or its original input or rendering failure.

        """
        roots = u.Infra.docs_repository_roots(request.repository_root)
        if roots.failure:
            return r[m.Infra.DocsGenerationBundle].from_failure(roots)
        repository_root = roots.value[0]
        rendered = cls._rendered_scope_inventory(
            repository_root, request, declared_files
        )
        if rendered.failure:
            return r[m.Infra.DocsGenerationBundle].from_failure(rendered)
        return cls._validated_bundle(
            repository_root,
            rendered.value[0],
            metadata_files=rendered.value[1],
        )

    @classmethod
    def _rendered_scope_inventory(
        cls,
        repository_root: Path,
        request: m.Infra.DocsGenerateRequest,
        declared_files: tuple[m.Infra.CodegenFilePlan, ...] = (),
    ) -> p.Result[FlextInfraDocsGeneratorBundle._DocsRenderedInventory]:
        """Resolve the docs scopes, their governance source and artifacts.

        Args:
            repository_root: Repository root owning the docs inventory.
            request: Canonical docs generation request.
            declared_files: Managed candidate effects supplying presentation metadata.

        Returns:
            The rendered scope artifacts, or the first resolution failure.

        """
        output_dir = u.Cli.resolve_optional_path(
            request.output_dir,
            default=Path(c.Infra.DEFAULT_DOCS_OUTPUT_DIR),
        )
        result_type = r[FlextInfraDocsGeneratorBundle._DocsRenderedInventory]
        scopes = cls._validated_scopes(repository_root, request, output_dir)
        if scopes.failure:
            return result_type.from_failure(scopes)
        metadata = cls._presentation_metadata(scopes.value[0], declared_files)
        if metadata.failure:
            return result_type.from_failure(metadata)
        contract = u.Infra.docs_make_contract_plans(repository_root, declared_files)
        if contract.failure:
            return result_type.from_failure(contract)
        contract_files = contract.value
        published_metadata = (
            *metadata.value,
            *(
                plan
                for plan in contract_files
                if any(scope.path == plan.project for scope in scopes.value[0])
            ),
        )
        governance = cls._governance_source(repository_root)
        if governance.failure:
            return result_type.from_failure(governance)
        rendered = cls._rendered_scopes(
            repository_root,
            scopes.value,
            (governance.value, published_metadata, contract_files),
        )
        if rendered.failure:
            return result_type.from_failure(rendered)
        return result_type.ok((rendered.value, published_metadata))

    @classmethod
    def _validated_scopes(
        cls,
        repository_root: Path,
        request: m.Infra.DocsGenerateRequest,
        output_dir: Path,
    ) -> p.Result[
        tuple[
            tuple[m.Infra.DocScope, ...],
            tuple[m.Infra.DocScope, ...],
        ]
    ]:
        """Build and target-validate the selected and aggregate doc scopes.

        Returns:
            The resulting ``(selected_scopes, aggregate_scopes)`` pair.

        """
        result_type = r[
            tuple[
                tuple[m.Infra.DocScope, ...],
                tuple[m.Infra.DocScope, ...],
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
        scopes: tuple[
            tuple[m.Infra.DocScope, ...],
            tuple[m.Infra.DocScope, ...],
        ],
        presentation: FlextInfraDocsGeneratorBundle._DocsPresentationInputs = (
            None,
            (),
            (),
        ),
    ) -> p.Result[list[_DocsScopeArtifacts]]:
        """Render one docs artifact set per selected scope.

        Returns:
            The resulting per-scope rendered artifacts.

        """
        selected, aggregate = scopes
        governance_source, metadata_files, declared_files = presentation
        projections = {
            plan.project: plan
            for plan in metadata_files
            if plan.path.name == c.PYPROJECT_FILENAME
        }
        selected = tuple(
            u.Infra.scope_from_sources(
                scope,
                metadata_projection=projections.get(scope.path),
                governance_source=governance_source,
                declared_files=declared_files,
            )
            for scope in selected
        )
        if any(scope.name == c.Infra.RK_ROOT for scope in selected):
            aggregate = tuple(
                u.Infra.scope_from_sources(
                    scope,
                    governance_source=governance_source,
                    declared_files=declared_files,
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
            try:
                artifacts = u.Infra.scope_artifacts(
                    scope,
                    repository_root=repository_root,
                    aggregate_scopes=aggregate,
                )
            except SyntaxError as exc:
                return r[list[_DocsScopeArtifacts]].fail(
                    f"cannot render documentation source for {scope.name}: {exc}",
                    exception=exc,
                )
            if artifacts.failure:
                return r[list[_DocsScopeArtifacts]].from_failure(artifacts)
            rendered.append((scope, artifacts.value))
            u.Cli.emit_raw(
                f"{c.Cli.OUTPUT_LOG_LEVEL_INFO}: docs: rendered "
                f"{scope.name} artifacts={len(artifacts.value)} "
                f"elapsed={perf_counter() - scope_started_at:.2f}s\n",
                error=True,
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
                    normalized_content = u.Infra.docs_rewrite_bare_notest(
                        normalized_content,
                        "{}",
                    )[0]
                    normalized_content = u.Infra.contract_update_toc(
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
        *,
        metadata_files: tuple[m.Infra.CodegenFilePlan, ...] = (),
    ) -> p.Result[m.Infra.DocsGenerationBundle]:
        """Validate the rendered docs generation bundle.

        Args:
            repository_root: The root path of the repository.
            rendered: The list of rendered documentation scope artifacts.
            metadata_files: Owned presentation metadata in this same publication.

        Returns:
            The resulting ``p.Result[m.Infra.DocsGenerationBundle]``.

        """
        normalized = cls._normalized_scope_artifacts(rendered)
        if normalized.failure:
            return r[m.Infra.DocsGenerationBundle].from_failure(normalized)
        validated_bundle = r[m.Infra.DocsGenerationBundle].create_from_callable(
            partial(
                m.Infra.DocsGenerationBundle,
                scopes=tuple(normalized.value),
                metadata_files=metadata_files,
                repository_root=repository_root,
            )
        )
        if validated_bundle.failure:
            return r[m.Infra.DocsGenerationBundle].fail_op(
                "docs generation bundle validation",
                validated_bundle.error,
            )
        return r[m.Infra.DocsGenerationBundle].ok(validated_bundle.value)

    @classmethod
    def _governance_source(
        cls,
        repository_root: Path,
    ) -> p.Result[m.Infra.CodegenBootstrapSource]:
        """Resolve the referenced governance owner before rendering its links.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenBootstrapSource]``.

        """
        result_type = r[m.Infra.CodegenBootstrapSource]
        inputs = u.Infra.load_codegen_inputs(repository_root)
        if inputs.failure:
            return result_type.from_failure(inputs)
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
        origin = identity.value.origin_remote
        if origin is not None:
            page = u.Infra.validate_git_remote_url(origin)
            if page.failure:
                return result_type.from_failure(page)
            if (
                page.value.rstrip("/").removesuffix(c.GIT_DIR_NAME)
                == c.Infra.GITHUB_REPO_URL
            ):
                branch = u.Infra.resolve_integration_branch(
                    repository_root,
                    policy_branch=inputs.spec.branch_policy.integration_branch,
                    inputs=inputs,
                )
                if branch.failure:
                    return result_type.from_failure(branch)
                return result_type.ok(branch.value)
        family = cls._family_governance_ref(repository_root, inputs)
        if family.failure:
            return result_type.from_failure(family)
        return result_type.ok(family.value)

    @classmethod
    def _family_governance_ref(
        cls,
        repository_root: Path,
        inputs: m.Infra.CodegenInputs,
    ) -> p.Result[str]:
        """Resolve the declared dependency family line.

        Returns:
            The dependency family branch, or the first resolution failure.

        """
        result_type = r[str]
        line = u.Infra.flext_integration_line(
            codegen=inputs.spec,
            repository_root=repository_root,
        )
        if line.failure:
            return result_type.from_failure(line)
        if line.value.base_url is None:
            return result_type.fail(
                "detected integration line without a base URL",
            )
        if c.Infra.GITHUB_REPO_URL.rsplit("/", maxsplit=1)[0] != (
            line.value.base_url.rstrip("/")
        ):
            return result_type.fail(
                "governance owner differs from the captured dependency family",
            )
        return result_type.ok(line.value.branch)


__all__: list[str] = ["FlextInfraDocsGeneratorBundle"]
