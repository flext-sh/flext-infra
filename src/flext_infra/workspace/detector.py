"""Repository-local workspace detection from immutable Git topology inputs.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, override

from flext_infra import c, config, m, r, settings, u
from flext_infra.base import s
from flext_infra.workspace import FlextInfraWorkspaceGovernance

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraWorkspaceDetector(
    FlextInfraWorkspaceGovernance,
    s[c.Infra.MakeProfile],
):
    """Classify a repository only from files and Git facts inside that checkout."""

    @classmethod
    def resolution_context(
        cls,
        repository_root: Path,
    ) -> p.Result[m.Infra.WorkspaceRuntimeContext]:
        """Elect native resolution inputs without package metadata or members.

        Returns:
            The elected runtime whose selected install view stays inside its
            physical runtime, or the first election or containment failure.

        """
        result_type = r[m.Infra.WorkspaceRuntimeContext]
        election = cls.runtime_election(repository_root)
        if election.failure:
            return result_type.from_failure(election)
        context = election.value
        if not context.resolution_root.resolve().is_relative_to(context.runtime_root):
            return result_type.fail(
                "UV resolution directory leaves its physical runtime"
            )
        return election

    @classmethod
    def runtime_election(
        cls,
        repository_root: Path,
    ) -> p.Result[m.Infra.WorkspaceRuntimeContext]:
        """Elect one repository's physical native workspace and runtime.

        Native runtime discovery owns workspace membership. The elected owner's
        manifest and lock also own resolution, independently of installation mode.

        Returns:
            The elected runtime context, or the first election failure.

        """
        result_type = r[m.Infra.WorkspaceRuntimeContext]
        request = m.Infra.GitRepoRequest(repo_root=repository_root)
        identity = u.Infra.git_show_toplevel(request)
        if identity.failure:
            return result_type.from_failure(identity)
        git_root = identity.value.repository_root.resolve()
        submitted = repository_root.expanduser().resolve()
        project_root = next(
            (
                directory
                for directory in (submitted, *submitted.parents)
                if directory.is_relative_to(git_root)
                and (directory / c.PYPROJECT_FILENAME).is_file()
            ),
            git_root,
        )
        runtime = u.Infra.runtime_owner_root(project_root)
        if runtime.failure:
            return result_type.from_failure(runtime)
        runtime_root = runtime.value
        return result_type.ok(
            m.Infra.WorkspaceRuntimeContext(
                project_root=project_root,
                runtime_root=runtime_root,
                resolution_root=runtime_root,
                pyproject_path=runtime_root / c.PYPROJECT_FILENAME,
                lock_path=runtime_root / c.Infra.UV_LOCK_FILENAME,
                environment_path=runtime_root / c.Infra.ENVIRONMENT_DIRECTORY,
                standalone=settings.Infra.github_actions == c.ParserBooleanToken.TRUE,
            ),
        )

    @classmethod
    def _resolved_beads(
        cls,
        resolved_root: Path,
        declaration: m.Infra.RepositoryDeltaSpec,
    ) -> p.Result[tuple[m.Infra.BeadsProjectSpec | None, bool]]:
        """Resolve the declared Beads ledger under the repository policy.

        Returns:
            The resulting workspace Beads specification with a presence flag
            (False when the repository policy opts out).

        """
        result_type = r[tuple[m.Infra.BeadsProjectSpec | None, bool]]
        beads_enabled = declaration.beads_enabled
        if not beads_enabled:
            if declaration.gascity_enabled:
                return result_type.fail(
                    "Gas City requires Beads participation in the repository policy",
                )
            return result_type.ok((None, False))
        beads_result = cls.load_beads_spec(resolved_root)
        if beads_result.failure:
            return result_type.from_failure(beads_result)
        return result_type.ok((beads_result.value, True))

    @staticmethod
    def _beads_path(repository_root: Path) -> Path:
        """Return the repository-local Beads identity path when enabled.

        Returns:
            The repository-local Beads identity path when enabled.

        """
        return repository_root / c.CONFIG_DIR_NAME / c.Infra.BEADS_CONFIG_FILENAME

    @classmethod
    def _composed_beads_identity_error(
        cls,
        subproject_root: Path,
        workspace_beads: m.Infra.BeadsProjectSpec,
    ) -> str | None:
        member_identity_path = (
            subproject_root / c.CONFIG_DIR_NAME / c.Infra.BEADS_CONFIG_FILENAME
        )
        # Detection observes the topology; it does not enforce the ledger-route
        # prohibition. Refusing to load a workspace because one composed project
        # still carries the old cross-project symlink makes the migration
        # impossible to perform — nothing can plan the fix for a repository it
        # cannot describe. `codegen conform` owns the prohibition and rejects
        # the link there, per repository and within the requested scope.
        if not member_identity_path.is_file():
            return (
                "missing required member Beads routing identity: "
                f"{member_identity_path}"
            )
        member_identity_result = cls.load_beads_spec(subproject_root)
        if member_identity_result.failure:
            return member_identity_result.error
        member_identity = member_identity_result.value
        member_key = (
            member_identity.workspace,
            member_identity.database,
            member_identity.issue_prefix,
        )
        workspace_key = (
            workspace_beads.workspace,
            workspace_beads.database,
            workspace_beads.issue_prefix,
        )
        if member_key != workspace_key:
            return (
                "member Beads routing identity differs from the workspace ledger: "
                f"{member_key} != {workspace_key}"
            )
        return None

    @classmethod
    def load_beads_spec(
        cls,
        repository_root: Path,
    ) -> p.Result[m.Infra.BeadsProjectSpec]:
        """Load and validate the required local ``config/beads.yaml``.

        Returns:
            The resulting ``p.Result[m.Infra.BeadsProjectSpec]``.

        """
        resolved_root = repository_root.expanduser().resolve()
        beads_path = cls._beads_path(resolved_root)
        if not beads_path.is_file():
            return r[m.Infra.BeadsProjectSpec].fail(
                f"missing required repository-local Beads configuration: {beads_path}",
            )
        loaded = u.Cli.config_load(beads_path, expand_env=False)
        if loaded.failure:
            return r[m.Infra.BeadsProjectSpec].fail(
                f"invalid repository-local Beads configuration ({beads_path}): "
                f"{loaded.error or 'configuration load failed'}",
            )
        validated: p.Result[m.Infra.BeadsProjectSpec] = u.validate_value(
            m.Infra.BeadsProjectSpec,
            loaded.value.data,
        )
        if validated.failure:
            return r[m.Infra.BeadsProjectSpec].fail_op(
                f"Beads configuration model validation ({beads_path})",
                validated.error,
            )
        return r[m.Infra.BeadsProjectSpec].ok(validated.value)

    @staticmethod
    def _git_origin_url(repository_root: Path) -> p.Result[str]:
        """Read the repository's required origin without inventing one.

        Returns:
            The resulting ``p.Result[str]``.

        """
        result = u.Infra.git_remote_url(
            m.Infra.GitRemoteUrlRequest(repo_root=repository_root, remote="origin"),
        )
        if result.failure or not result.value.text.strip():
            return r[str].fail(
                result.error or f"repository origin is required: {repository_root}",
            )
        return r[str].ok(result.value.text.strip())

    @classmethod
    def _declared_provider_name(
        cls,
        repository_root: Path,
        *,
        origin_url: str,
    ) -> p.Result[str]:
        """Detect the provider key the repository declares for itself.

        With a workspace manifest, the declaration is real only if the live
        Git origin carries the same organization identity as the declared URL
        (the same discrimination ``git_remote_identity`` gives every remote
        shape). Post-G1, repositories without a manifest take their provider
        identity from the live Git origin organization itself — no catalog,
        no invented rows.

        Returns:
            The resulting ``p.Result[str]``.

        """
        del repository_root
        origin_organization, origin_separator, _ = u.Infra.git_remote_identity(
            origin_url,
        ).partition("/")
        if not origin_separator:
            return r[str].fail(
                "governed repository Git origin must name an owner and "
                f"repository: {origin_url}",
            )
        return r[str].ok(origin_organization)

    @staticmethod
    def _configured_repository_ref(
        declaration: m.Infra.RepositoryDeltaSpec,
        *,
        observed: m.Infra.RepositoryRef,
    ) -> p.Result[tuple[m.Infra.RepositoryRef, bool, m.Infra.ProjectSpec | None]]:
        """Load a selected repository manifest and reconcile it with Git truth.

        The checkout's own manifest is mandatory for identity: its complete
        typed ``repository`` record is authoritative for repository policy and
        must agree with the immutable identity and topology observed from Git.
        The matched repository policy overlay's Gas City participation rides
        along: ``True`` when the manifest declares no overlay.

        Returns:
            The resulting ``p.Result[tuple[m.Infra.RepositoryRef, bool,
                m.Infra.ProjectSpec | None]]``.

        """
        values = observed.model_dump(round_trip=True)
        values.update(
            declaration.model_dump(
                include=set(m.Infra.RepositoryRef.model_fields),
                round_trip=True,
            ),
        )
        validated = u.validate_value(m.Infra.RepositoryRef, values)
        if validated.failure:
            return r[
                tuple[m.Infra.RepositoryRef, bool, m.Infra.ProjectSpec | None]
            ].from_failure(validated)
        return r[tuple[m.Infra.RepositoryRef, bool, m.Infra.ProjectSpec | None]].ok((
            validated.value,
            declaration.gascity_enabled,
            declaration.project,
        ))

    @classmethod
    def _reconciled_origin(
        cls,
        repository_root: Path,
        *,
        path: Path,
        declared_url: str | None,
    ) -> p.Result[tuple[str, str]]:
        """Reconcile the live origin with its declared URL and provider identity.

        Returns:
            The resulting ``(live origin URL, declared provider name)`` pair.

        """
        result_type = r[tuple[str, str]]
        origin = cls._git_origin_url(repository_root)
        if origin.failure:
            return result_type.from_failure(origin)
        if declared_url is not None and u.Infra.git_remote_identity(
            origin.value,
        ) != u.Infra.git_remote_identity(declared_url):
            return result_type.fail(
                f"subproject origin differs from its .gitmodules URL: "
                f"{path.as_posix()}",
            )
        provider_result = cls._declared_provider_name(
            repository_root,
            origin_url=origin.value,
        )
        if provider_result.failure:
            return result_type.from_failure(provider_result)
        return result_type.ok((origin.value, provider_result.value))

    @classmethod
    def _local_repository_ref(
        cls,
        repository_root: Path,
        *,
        path: Path = Path(),
        composed: bool = False,
        declared_url: str | None = None,
        native_metadata: m.Infra.ProjectMetadataState | None = None,
    ) -> p.Result[m.Infra.RepositoryRef]:
        """Build identity from validated checkout metadata and native Git inputs.

        Returns:
            The resulting ``p.Result[m.Infra.RepositoryRef]``.

        """
        metadata_path = repository_root / c.PYPROJECT_FILENAME
        if native_metadata is not None:
            project_name = native_metadata.metadata.project.name
            package = u.Infra.project_package_participation(native_metadata.packaging)
        elif metadata_path.exists() or metadata_path.is_symlink():
            metadata = u.Infra.read_project_metadata_state(repository_root)
            if metadata.failure:
                return r[m.Infra.RepositoryRef].from_failure(metadata)
            project_name = metadata.value.metadata.project.name
            package = u.Infra.project_package_participation(
                metadata.value.packaging,
            )
        else:
            scaffold = cls._declared_scaffold_project(repository_root)
            if scaffold.failure:
                return r[m.Infra.RepositoryRef].from_failure(scaffold)
            project_name = scaffold.value.constant_name
            # The explicit ProjectSpec declares the import package the existing
            # scaffold planner materializes; no PEP metadata exists yet.
            package = True
        origin = cls._reconciled_origin(
            repository_root,
            path=path,
            declared_url=declared_url,
        )
        if origin.failure:
            return r[m.Infra.RepositoryRef].from_failure(origin)
        origin_url, provider_name = origin.value
        canonical_url = u.Infra.validate_git_remote_url(declared_url or origin_url)
        if canonical_url.failure:
            return r[m.Infra.RepositoryRef].from_failure(canonical_url)
        effective_url = canonical_url.value
        role = (
            c.Infra.MakeProfile.WORKSPACE
            if (repository_root / c.Infra.GITMODULES).is_file()
            else c.Infra.MakeProfile.STANDALONE
        )
        _, separator, repository_name = u.Infra.git_remote_identity(
            origin_url,
        ).partition("/")
        if not separator or not repository_name:
            return r[m.Infra.RepositoryRef].fail(
                f"Git origin does not identify a repository: {origin_url}",
            )
        # The manifest is the identity authority: the provider key is the one
        # the repository itself declares and the declared URL organization was
        # just reconciled against the live origin, so no catalog may override
        # either. Native packaging declarations own participation; source
        # exports remain independently accountable to their actual check owner.
        return r[m.Infra.RepositoryRef].ok(
            m.Infra.RepositoryRef(
                name=repository_name,
                distribution=project_name,
                url=effective_url,
                path=path,
                role=role,
                provider=provider_name,
                kind=c.Infra.ProjectKind.INTERNAL_FLEXT,
                codegen=c.Infra.CodegenKind.CONFORM,
                package=package,
                # The checkout's own root package is its environment's
                # editable install by the uv contract — the lock records
                # `editable = "."` for the project root in every standalone
                # checkout, and the provenance law compares this flag
                # against that record. Workspace-attached members carry
                # their attachment; the self root carries the contract.
                editable=composed or path == Path(),
                # A composed tree is attached by its declared gitlink; the
                # immutable provenance gate binds its HEAD to that gitlink.
                checkout=(
                    c.Infra.CheckoutKind.SUBMODULE.value
                    if composed
                    else c.Infra.CheckoutKind.ROOT.value
                ),
                read_only=False,
            ),
        )

    @classmethod
    def _declared_scaffold_project(
        cls,
        repository_root: Path,
    ) -> p.Result[m.Infra.ProjectSpec]:
        """Admit a prepared tree with its complete own generation declaration.

        Returns:
            The declared project, or the original Git/configuration failure.

        """
        result_type = r[m.Infra.ProjectSpec]
        inputs = u.Infra.exact_worktree_root(repository_root).flat_map(
            lambda _: u.Infra.load_codegen_inputs(repository_root)
        )
        if inputs.failure:
            return result_type.from_failure(inputs)
        project = cls._scaffold_project_declaration(repository_root, inputs.value)
        if project.failure:
            return project
        provenance = cls._scaffold_provenance(
            repository_root, inputs.value, project.value
        )
        if provenance.failure:
            return result_type.from_failure(provenance)
        fresh = cls._require_new_scaffold(repository_root)
        if fresh.failure:
            return result_type.from_failure(fresh)
        return project

    @staticmethod
    def _scaffold_project_declaration(
        repository_root: Path,
        inputs: m.Infra.CodegenInputs,
    ) -> p.Result[m.Infra.ProjectSpec]:
        """Require the project, integration, kind and dependency declarations.

        Returns:
            The declared project, or the typed declaration failure.

        """
        result_type = r[m.Infra.ProjectSpec]
        declaration = inputs.spec.repository
        if declaration.project is None:
            error = FileNotFoundError(
                f"repository has no {c.PYPROJECT_FILENAME} or explicit "
                f"project declaration: {repository_root}",
            )
            return result_type.fail(str(error), exception=error)
        if (
            declaration.integration is None
            or "kind" not in declaration.model_fields_set
        ):
            return result_type.fail(
                "new project requires its own integration and kind declarations: "
                f"{repository_root}",
            )
        if declaration.project.flext_source is None:
            return result_type.fail(
                "new project requires explicit dependency provenance: "
                f"{repository_root}",
            )
        return result_type.ok(declaration.project)

    @staticmethod
    def _scaffold_provenance(
        repository_root: Path,
        inputs: m.Infra.CodegenInputs,
        project: m.Infra.ProjectSpec,
    ) -> p.Result[bool]:
        """Require infrastructure provenance on an integration line.

        Returns:
            Success when the declared source resolves to an integration line.

        """
        flext_source = project.flext_source
        if flext_source is None:
            return r[bool].fail(
                "new project requires explicit dependency provenance: "
                f"{repository_root}",
            )
        source = u.Infra.declared_git_source(flext_source)
        if source.failure:
            return r[bool].from_failure(source)
        if u.Infra.dep_name(flext_source) != inputs.spec.infra_repository.distribution:
            return r[bool].fail(
                "new project provenance must declare its infrastructure dependency: "
                f"{flext_source}",
            )
        source_url, source_ref = source.value
        if u.Infra.ref_is_commit(source_ref):
            return r[bool].fail(
                "new project provenance requires an integration line, not a commit: "
                f"{flext_source}",
            )
        line = u.Infra.flext_integration_line(
            codegen=inputs.spec,
            repository_root=repository_root,
            bootstrap_source=m.Infra.CodegenBootstrapSource(
                url=source_url, ref=source_ref
            ),
        )
        if line.failure:
            return r[bool].from_failure(line)
        return r[bool].ok(value=True)

    @staticmethod
    def _require_new_scaffold(repository_root: Path) -> p.Result[bool]:
        """Require a tree with no manifest history and no authored Python sources.

        Returns:
            Success for a new scaffold, or the typed rejection.

        """
        path_request = m.Infra.GitRelativePathRequest(
            repo_root=repository_root,
            relative_path=c.PYPROJECT_FILENAME,
        )
        tracked = u.Infra.git_is_tracked(path_request)
        if tracked.failure:
            return r[bool].from_failure(tracked)
        history = u.Infra.git_path_has_history(path_request)
        if history.failure:
            return r[bool].from_failure(history)
        if tracked.value.value or history.value.value:
            return r[bool].fail(
                f"established repository is missing {c.PYPROJECT_FILENAME}: "
                f"{repository_root}",
            )
        sources = u.Infra.git_source_scope_paths(repository_root)
        if sources is None:
            return r[bool].fail(
                f"new-project source inventory has no Git owner: {repository_root}",
            )
        authored = tuple(
            path for path in sources if path.suffix in c.Infra.PYTHON_SOURCE_SUFFIXES
        )
        if authored:
            return r[bool].fail(
                "repository with existing Python sources is not a new scaffold: "
                f"{', '.join(str(path) for path in authored)}",
            )
        return r[bool].ok(value=True)

    @classmethod
    def _load_subprojects(
        cls,
        repository_root: Path,
        *,
        workspace_beads: m.Infra.BeadsProjectSpec | None,
        inputs: m.Infra.CodegenInputs,
        allow_unprovisioned_members: bool = False,
    ) -> p.Result[
        tuple[
            tuple[m.Infra.RepositoryRef, ...],
            tuple[Path, ...],
            tuple[m.Infra.GitSubmoduleDeclaration, ...],
        ]
    ]:
        """Validate every direct governed .gitmodules entry before planning writes.

        Read the native declarations once and pass each original object through
        its member's contract and checkout decisions in declaration order.

        Returns:
            The resulting repository refs, external paths and pending declarations.

        """
        declared = u.Infra.git_submodule_declarations(repository_root)
        result_type = r[
            tuple[
                tuple[m.Infra.RepositoryRef, ...],
                tuple[Path, ...],
                tuple[m.Infra.GitSubmoduleDeclaration, ...],
            ]
        ]
        if declared.failure:
            return result_type.from_failure(declared)
        if not declared.value:
            return result_type.ok(((), (), ()))
        subprojects: list[m.Infra.RepositoryRef] = []
        external: list[Path] = []
        pending: list[m.Infra.GitSubmoduleDeclaration] = []
        # The workspace-declared line owns the baseline: a fleet integrating on
        # a versioned release line (0.12.0-dev) declares it, and resolution
        # checks exactly that line — no conventional fallback names exist.
        baseline = u.Infra.resolve_integration_branch(
            repository_root,
            policy_branch=inputs.spec.branch_policy.integration_branch,
            inputs=inputs,
        )
        if baseline.failure:
            return result_type.from_failure(baseline)
        context = m.Infra.SubprojectLoadContext(
            integration_branch=baseline.value,
            workspace_beads=workspace_beads,
            allow_unprovisioned_members=allow_unprovisioned_members,
        )
        for declaration in declared.value:
            loaded = cls._load_subproject(
                repository_root,
                declaration,
                context=context,
            )
            if loaded.failure:
                return result_type.from_failure(loaded)
            if isinstance(loaded.value, m.Infra.GitSubmoduleDeclaration):
                pending.append(loaded.value)
                continue
            if isinstance(loaded.value, Path):
                external.append(loaded.value)
                continue
            subprojects.append(loaded.value)
        return result_type.ok((tuple(subprojects), tuple(external), tuple(pending)))

    @classmethod
    def _load_subproject(
        cls,
        repository_root: Path,
        declaration: m.Infra.GitSubmoduleDeclaration,
        *,
        context: m.Infra.SubprojectLoadContext,
    ) -> p.Result[m.Infra.RepositoryRef | Path | m.Infra.GitSubmoduleDeclaration]:
        """Load one governed entry, or its declared path for external entries.

        A native Git false management declaration marks a read-only external
        dependency. An absent flag inherits participation. Managed entries
        resolve their package identity from a provisioned checkout; setup may
        retain an unprovisioned entry as its parsed Git declaration only.
        The native declaration owner validates that captured object's URL and
        branch before the management decision; this loader does not reread Git.

        Returns:
            The resulting ``p.Result[m.Infra.RepositoryRef | Path |
            m.Infra.GitSubmoduleDeclaration]``.

        """
        result_type = r[m.Infra.RepositoryRef | Path | m.Infra.GitSubmoduleDeclaration]
        contract = u.Infra.git_require_submodule_contract(declaration)
        if contract.failure:
            return result_type.from_failure(contract)
        path = contract.value.path
        if contract.value.managed is False:
            return result_type.ok(path)
        subproject_root = cls._governed_subproject_root(
            repository_root,
            path,
            branch=contract.value.branch,
            context=context,
        )
        if subproject_root.failure:
            return result_type.from_failure(subproject_root)
        return cls._undeclared_subproject(
            subproject_root.value,
            contract.value,
            context=context,
        )

    @staticmethod
    def _governed_subproject_root(
        repository_root: Path,
        path: Path,
        *,
        branch: str,
        context: m.Infra.SubprojectLoadContext,
    ) -> p.Result[Path]:
        """Return the checkout root of a governed entry on the integration line.

        Returns:
            The resolved checkout root, or the branch or escape failure.

        """
        if not u.Infra.gitmodule_branch_is_governed(
            branch,
            integration_branch=context.integration_branch,
        ):
            return r[Path].fail(
                "governed subproject branch differs from the workspace "
                f"integration line: {path.as_posix()}",
            )
        subproject_root = (repository_root / path).resolve()
        if not subproject_root.is_relative_to(repository_root):
            return r[Path].fail(
                f"subproject escapes workspace root: {path.as_posix()}",
            )
        return r[Path].ok(subproject_root)

    @classmethod
    def _undeclared_subproject(
        cls,
        subproject_root: Path,
        declaration: m.Infra.GitSubmoduleDeclaration,
        *,
        context: m.Infra.SubprojectLoadContext,
    ) -> p.Result[m.Infra.RepositoryRef | Path | m.Infra.GitSubmoduleDeclaration]:
        """Resolve a provisioned checkout without a second identity catalog.

        Returns:
            Its observed identity, or the same native declaration for setup.

        """
        result_type = r[m.Infra.RepositoryRef | Path | m.Infra.GitSubmoduleDeclaration]
        if not (subproject_root / c.Infra.GIT_DIR).exists():
            if not context.allow_unprovisioned_members:
                error = FileNotFoundError(
                    "governed subproject checkout is missing: "
                    f"{declaration.path.as_posix()}",
                )
                return result_type.fail(str(error), exception=error)
            return result_type.ok(declaration)
        return cls._checkout_subproject(
            subproject_root,
            declaration.path,
            declared_url=declaration.url,
            context=context,
        )

    @classmethod
    def _checkout_subproject(
        cls,
        subproject_root: Path,
        path: Path,
        *,
        declared_url: str,
        context: m.Infra.SubprojectLoadContext,
    ) -> p.Result[m.Infra.RepositoryRef | Path | m.Infra.GitSubmoduleDeclaration]:
        """Derive a composed member from its provisioned Python checkout.

        Returns:
            The member reference carrying its own declared commands.

        """
        result_type = r[m.Infra.RepositoryRef | Path | m.Infra.GitSubmoduleDeclaration]
        routed = cls._beads_route_gate(subproject_root, context.workspace_beads)
        if routed.failure:
            return result_type.from_failure(routed)
        repository = cls._local_repository_ref(
            subproject_root,
            path=path,
            composed=True,
            declared_url=declared_url,
        )
        if repository.failure:
            return result_type.from_failure(repository)
        return cls._member_commands_ref(
            subproject_root,
            repository.value,
            workspace_beads=context.workspace_beads,
        )

    @classmethod
    def _beads_route_gate(
        cls,
        subproject_root: Path,
        workspace_beads: m.Infra.BeadsProjectSpec | None,
    ) -> p.Result[bool]:
        """Require a composed member to follow the workspace Beads ledger.

        Returns:
            Success when the member routes to the workspace ledger or owns a
            valid ledger of its own.

        """
        if workspace_beads is None:
            return r[bool].ok(value=True)
        if (subproject_root / c.Infra.BEADS_DIRNAME).is_symlink():
            route_error = cls._composed_beads_identity_error(
                subproject_root,
                workspace_beads,
            )
            if route_error is not None:
                return r[bool].fail(
                    "composed project must follow the workspace Beads ledger: "
                    f"{route_error}",
                )
            return r[bool].ok(value=True)
        beads = cls.load_beads_spec(subproject_root)
        if beads.failure:
            return r[bool].from_failure(beads)
        return r[bool].ok(value=True)

    @classmethod
    def _member_commands_ref(
        cls,
        subproject_root: Path,
        repository: m.Infra.RepositoryRef,
        *,
        workspace_beads: m.Infra.BeadsProjectSpec | None,
    ) -> p.Result[m.Infra.RepositoryRef | Path | m.Infra.GitSubmoduleDeclaration]:
        """Attach the commands a member declares in its own manifest.

        Returns:
            The member reference with its declared commands.

        """
        result_type = r[m.Infra.RepositoryRef | Path | m.Infra.GitSubmoduleDeclaration]
        del workspace_beads
        inputs = u.Infra.load_repository_declaration_inputs(subproject_root)
        if inputs.failure:
            return result_type.from_failure(inputs)
        declaration = inputs.value.spec
        configured = cls._configured_repository_ref(
            declaration,
            observed=repository,
        )
        if configured.failure:
            return result_type.from_failure(configured)
        return result_type.ok(configured.value[0])

    @staticmethod
    def _bootstrap_source(
        resolved_root: Path,
        declaration: m.Infra.RepositoryDeltaSpec,
    ) -> p.Result[m.Infra.CodegenBootstrapSource]:
        """Elect the declared dependency source of a repository without a manifest.

        Returns:
            The declared bootstrap source.

        """
        result_type = r[m.Infra.CodegenBootstrapSource]
        project = declaration.project
        if project is None or project.flext_source is None:
            return result_type.fail(
                f"new project has no declared dependency source: {resolved_root}",
            )
        source = u.Infra.declared_git_source(project.flext_source)
        if source.failure:
            return result_type.from_failure(source)
        return result_type.ok(
            m.Infra.CodegenBootstrapSource(url=source.value[0], ref=source.value[1])
        )

    @classmethod
    def load_workspace_spec(
        cls,
        repository_root: Path,
        *,
        project_metadata: p.ProjectMetadata | None = None,
        allow_unprovisioned_members: bool = False,
        inputs: m.Infra.CodegenInputs | None = None,
    ) -> p.Result[m.Infra.WorkspaceSpec]:
        """Load local identity and validate local, read-only Git topology.

        Existing manifests need no bootstrap source. Success carries the complete
        workspace, never an optional value transported as a Result payload.

        Returns:
            The resulting ``p.Result[m.Infra.WorkspaceSpec]``.

        """
        del project_metadata
        resolved_root = repository_root.expanduser().resolve()
        authenticated = cls._authenticated_identity(resolved_root)
        if authenticated.failure:
            return r[m.Infra.WorkspaceSpec].from_failure(authenticated)
        identity = authenticated.value
        resolved_inputs = cls._resolved_codegen_inputs(resolved_root, inputs)
        if resolved_inputs.failure:
            return r[m.Infra.WorkspaceSpec].from_failure(resolved_inputs)
        inputs_value = resolved_inputs.value
        declaration = inputs_value.spec.repository or m.Infra.RepositoryDeltaSpec()
        workspace = cls._resolved_workspace_topology(
            resolved_root,
            identity,
            inputs=inputs_value,
            declaration=declaration,
            allow_unprovisioned_members=allow_unprovisioned_members,
        )
        if workspace.failure:
            return r[m.Infra.WorkspaceSpec].from_failure(workspace)
        external_consumers = u.Infra.discover_external_consumers(
            resolved_root,
            inputs_value,
        )
        if external_consumers.failure:
            return r[m.Infra.WorkspaceSpec].from_failure(external_consumers)
        (workspace_beads, resolved_refs, name) = workspace.value
        bootstrap_source: m.Infra.CodegenBootstrapSource | None = None
        if not (resolved_root / c.PYPROJECT_FILENAME).exists():
            bootstrap = cls._bootstrap_source(resolved_root, declaration)
            if bootstrap.failure:
                return r[m.Infra.WorkspaceSpec].from_failure(bootstrap)
            bootstrap_source = bootstrap.value
        return r[m.Infra.WorkspaceSpec].ok(
            m.Infra.WorkspaceSpec(
                name=name,
                flext_source=bootstrap_source,
                beads=workspace_beads,
                gascity_enabled=resolved_refs[0][1],
                repository=resolved_refs[0][0],
                project=resolved_refs[0][2],
                namespace_scan_dirs=declaration.namespace_scan_dirs,
                integration=declaration.integration,
                candidate_dependencies=declaration.candidate_dependencies,
                candidate_bootstrap_targets=declaration.candidate_bootstrap_targets,
                docs_audit=declaration.docs_audit,
                subprojects=tuple(resolved_refs[1][0]),
                pending_subprojects=tuple(resolved_refs[1][2]),
                external_dependency_paths=tuple(resolved_refs[1][1]),
                external_consumers=external_consumers.value,
            ),
        )

    @classmethod
    def _resolved_codegen_inputs(
        cls,
        resolved_root: Path,
        inputs: m.Infra.CodegenInputs | None,
    ) -> p.Result[m.Infra.CodegenInputs]:
        """Return the given codegen inputs or load them from the checkout.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenInputs]``.

        """
        if inputs is not None:
            return r[m.Infra.CodegenInputs].ok(inputs)
        return u.Infra.load_codegen_inputs(resolved_root)

    @classmethod
    def _resolved_workspace_topology(
        cls,
        resolved_root: Path,
        identity: m.Infra.GitIdentityReport,
        *,
        inputs: m.Infra.CodegenInputs,
        declaration: m.Infra.RepositoryDeltaSpec,
        allow_unprovisioned_members: bool,
    ) -> p.Result[
        tuple[
            m.Infra.BeadsProjectSpec | None,
            tuple[
                tuple[m.Infra.RepositoryRef, bool, m.Infra.ProjectSpec | None],
                tuple[
                    Sequence[m.Infra.RepositoryRef],
                    Sequence[Path],
                    Sequence[m.Infra.GitSubmoduleDeclaration],
                ],
            ],
            str,
        ]
    ]:
        """Resolve the Beads ledger, repository refs, and workspace name.

        Returns:
            The resulting ``(beads ledger, resolved refs, workspace name)``
            triple.

        """
        result_type = r[
            tuple[
                m.Infra.BeadsProjectSpec | None,
                tuple[
                    tuple[m.Infra.RepositoryRef, bool, m.Infra.ProjectSpec | None],
                    tuple[
                        Sequence[m.Infra.RepositoryRef],
                        Sequence[Path],
                        Sequence[m.Infra.GitSubmoduleDeclaration],
                    ],
                ],
                str,
            ]
        ]
        beads = cls._effective_workspace_beads(resolved_root, identity, declaration)
        if beads.failure:
            return result_type.from_failure(beads)
        workspace_beads = beads.value[0] if beads.value else None
        refs = cls._resolved_workspace_refs(
            resolved_root,
            workspace_beads,
            inputs=inputs,
            composed=identity.is_attached_submodule,
            allow_unprovisioned_members=allow_unprovisioned_members,
        )
        if refs.failure:
            return result_type.from_failure(refs)
        named = cls._workspace_name(workspace_beads, refs.value[0][0])
        if named.failure:
            return result_type.from_failure(named)
        return result_type.ok((workspace_beads, refs.value, named.value))

    @classmethod
    def _authenticated_identity(
        cls,
        resolved_root: Path,
    ) -> p.Result[m.Infra.GitIdentityReport]:
        """Authenticate the repository root, its Git identity, and its manifest.

        Returns:
            The resulting ``(identity, manifest)`` pair.

        """
        result_type = r[m.Infra.GitIdentityReport]
        if not resolved_root.is_dir():
            return result_type.fail(
                f"repository root is not a directory: {resolved_root}",
            )
        identity = u.Infra.git_identity(m.Infra.GitRepoRequest(repo_root=resolved_root))
        if identity.failure:
            return result_type.from_failure(identity)
        return result_type.ok(identity.value)

    @classmethod
    def _effective_workspace_beads(
        cls,
        resolved_root: Path,
        identity: m.Infra.GitIdentityReport,
        declaration: m.Infra.RepositoryDeltaSpec,
    ) -> p.Result[tuple[m.Infra.BeadsProjectSpec, ...]]:
        """Resolve the effective Beads ledger from the declared policy overlay.

        Returns:
            The effective ledger as a 0-or-1 tuple; a Beads-free repository is
            the empty tuple, never a ``None`` success payload.

        """
        resolved_beads = cls._resolved_beads(
            resolved_root,
            declaration,
        )
        if resolved_beads.failure:
            return r[tuple[m.Infra.BeadsProjectSpec, ...]].from_failure(
                resolved_beads,
            )
        return cls._effective_beads(
            resolved_root,
            identity,
            resolved_beads.value[0],
        )

    @classmethod
    def _effective_beads(
        cls,
        resolved_root: Path,
        identity: m.Infra.GitIdentityReport,
        beads: m.Infra.BeadsProjectSpec | None,
    ) -> p.Result[tuple[m.Infra.BeadsProjectSpec, ...]]:
        """Resolve the effective Beads ledger, inheriting through submodules.

        Returns:
            The effective workspace Beads specification as a 0-or-1 tuple.

        """
        result_type = r[tuple[m.Infra.BeadsProjectSpec, ...]]
        member_root = identity.primary_root
        member_beads = member_root / c.Infra.BEADS_DIRNAME
        if not (
            beads is not None
            and identity.is_attached_submodule
            and member_beads.is_symlink()
        ):
            return result_type.ok(() if beads is None else (beads,))
        superproject_root = identity.superproject_root
        if superproject_root is None:
            return result_type.fail(
                f"Git submodule has no superproject: {resolved_root}",
            )
        inherited = cls._inherited_member_beads(superproject_root, member_root)
        if inherited.failure:
            return result_type.from_failure(inherited)
        inherited_beads, _loaded_member = inherited.value
        route_error = cls._composed_beads_identity_error(resolved_root, inherited_beads)
        if route_error is not None:
            return result_type.fail(
                "composed project must follow the workspace Beads ledger: "
                f"{route_error}",
            )
        return result_type.ok((inherited_beads,))

    @classmethod
    def _inherited_member_beads(
        cls,
        superproject_root: Path,
        member_root: Path,
    ) -> p.Result[tuple[m.Infra.BeadsProjectSpec, m.Infra.RepositoryRef]]:
        """Load the superproject's Beads ledger and the member's governed ref.

        Resolve this independent member's native declaration once, after its
        integration context has been elected.

        Returns:
            The resulting ``(inherited_beads, loaded_member)`` pair.

        """
        result_type = r[tuple[m.Infra.BeadsProjectSpec, m.Infra.RepositoryRef]]
        inherited_beads = cls.load_beads_spec(superproject_root)
        if inherited_beads.failure:
            return result_type.from_failure(inherited_beads)
        if not member_root.is_relative_to(superproject_root):
            return result_type.fail(
                f"Git submodule escapes its superproject: {member_root}",
            )
        member_path = member_root.relative_to(superproject_root)
        # Same owner as the parent load: the declared versioned integration
        # line resolves against published Git, never against a name list.
        baseline = u.Infra.resolve_integration_branch(
            superproject_root,
            policy_branch=config.Infra.codegen.branch_policy.integration_branch,
        )
        if baseline.failure:
            return result_type.from_failure(baseline)
        context = m.Infra.SubprojectLoadContext(
            integration_branch=baseline.value,
            workspace_beads=inherited_beads.value,
        )
        loaded_member = u.Infra.git_submodule_declaration(
            m.Infra.GitSubmoduleContractRequest(
                repo_root=superproject_root,
                member_path=member_path.as_posix(),
            ),
        ).flat_map(
            lambda declaration: cls._load_subproject(
                superproject_root,
                declaration,
                context=context,
            ),
        )
        undeclared = f"Git submodule is not a declared governed project: {member_root}"
        if loaded_member.failure:
            return result_type.from_failure(loaded_member)
        member_ref = loaded_member.value
        if not isinstance(member_ref, m.Infra.RepositoryRef):
            return result_type.fail(undeclared)
        return result_type.ok((inherited_beads.value, member_ref))

    @classmethod
    def _resolved_workspace_refs(
        cls,
        resolved_root: Path,
        beads: m.Infra.BeadsProjectSpec | None,
        *,
        inputs: m.Infra.CodegenInputs,
        composed: bool,
        allow_unprovisioned_members: bool,
    ) -> p.Result[
        tuple[
            tuple[m.Infra.RepositoryRef, bool, m.Infra.ProjectSpec | None],
            tuple[
                Sequence[m.Infra.RepositoryRef],
                Sequence[Path],
                Sequence[m.Infra.GitSubmoduleDeclaration],
            ],
        ]
    ]:
        """Resolve the repository ref and the composed subproject topology.

        Returns:
            The resulting ``((repository_ref, gascity_enabled, declared_project),
            (subprojects, external))`` pair pair.

        """
        result_type = r[
            tuple[
                tuple[m.Infra.RepositoryRef, bool, m.Infra.ProjectSpec | None],
                tuple[
                    Sequence[m.Infra.RepositoryRef],
                    Sequence[Path],
                    Sequence[m.Infra.GitSubmoduleDeclaration],
                ],
            ]
        ]
        repository = cls._local_repository_ref(resolved_root, composed=composed)
        if repository.failure:
            return result_type.from_failure(repository)
        topology = cls._load_subprojects(
            resolved_root,
            workspace_beads=beads,
            inputs=inputs,
            allow_unprovisioned_members=allow_unprovisioned_members,
        )
        if topology.failure:
            return result_type.from_failure(topology)
        subprojects, external, pending = topology.value
        observed_repository = repository.value.model_copy(
            update={
                "role": (
                    c.Infra.MakeProfile.WORKSPACE
                    if subprojects or external or pending
                    else c.Infra.MakeProfile.STANDALONE
                ),
            },
        )
        declaration = inputs.spec.repository or m.Infra.RepositoryDeltaSpec()
        declared_repository = cls._configured_repository_ref(
            declaration,
            observed=observed_repository,
        )
        if declared_repository.failure:
            return result_type.from_failure(declared_repository)
        return result_type.ok(
            (declared_repository.value, (subprojects, external, pending)),
        )

    @staticmethod
    def _workspace_name(
        beads: m.Infra.BeadsProjectSpec | None,
        repository: m.Infra.RepositoryRef,
    ) -> p.Result[str]:
        """Resolve the workspace name from Beads or the declared manifest.

        Returns:
            The resulting workspace name.

        """
        if beads is not None:
            return r[str].ok(beads.workspace)
        return r[str].ok(repository.name)

    @classmethod
    def _canonical_project_name(cls, resolved_root: Path) -> p.Result[str]:
        """Resolve the canonical project name from its manifest or scaffold.

        Returns:
            The canonical project name, or the original metadata failure.

        """
        metadata_path = resolved_root / c.PYPROJECT_FILENAME
        if metadata_path.exists() or metadata_path.is_symlink():
            return u.Infra.read_project_metadata_result(resolved_root).map(
                lambda metadata: metadata.project.name
            )
        return cls._declared_scaffold_project(resolved_root).map(
            lambda scaffold: scaffold.constant_name
        )

    @classmethod
    def conform_target(
        cls,
        repository_root: Path,
        workspace_spec: m.Infra.WorkspaceSpec | None = None,
        *,
        project_metadata: p.ProjectMetadata | None = None,
        inputs: m.Infra.CodegenInputs | None = None,
    ) -> p.Result[m.Infra.RepositoryConformTarget]:
        """Resolve a target exclusively from the requested checkout.

        Returns:
            The resulting ``p.Result[m.Infra.RepositoryConformTarget]``.

        """
        del project_metadata
        resolved_root = repository_root.expanduser().resolve()
        workspace = workspace_spec
        if workspace is None:
            loaded = cls.load_workspace_spec(resolved_root, inputs=inputs)
            if loaded.failure:
                return r[m.Infra.RepositoryConformTarget].from_failure(loaded)
            workspace = loaded.value
        if workspace.repository.path != Path():
            return r[m.Infra.RepositoryConformTarget].fail(
                "local workspace repository path must be '.'",
            )
        canonical = cls._canonical_project_name(resolved_root)
        if canonical.failure:
            return r[m.Infra.RepositoryConformTarget].from_failure(canonical)
        canonical_project_name = canonical.value
        if canonical_project_name != workspace.repository.distribution:
            return r[m.Infra.RepositoryConformTarget].fail(
                "project metadata and repository identity differ: "
                f"{canonical_project_name} != {workspace.repository.distribution}",
            )
        if inputs is None:
            captured = u.Infra.load_codegen_inputs(resolved_root)
            if captured.failure:
                return r[m.Infra.RepositoryConformTarget].from_failure(captured)
            inputs = captured.value
        declaration = inputs.spec.repository or m.Infra.RepositoryDeltaSpec()
        return r[m.Infra.RepositoryConformTarget].ok(
            m.Infra.RepositoryConformTarget(
                repository=workspace.repository,
                root=resolved_root,
                toolchain_root=resolved_root,
                make_profile=workspace.repository.role,
                beads=workspace.beads,
                project=workspace.project,
                canonical_project_name=canonical_project_name,
                ci_enabled=declaration.ci_enabled,
                publishes_release=workspace.repository.publishes_release,
                gascity_enabled=workspace.gascity_enabled,
                external_dependency_paths=workspace.external_dependency_paths,
            ),
        )

    @staticmethod
    def resolve_repository_root(repository_root: Path) -> p.Result[Path]:
        """Return the requested checkout; parent and primary trees are irrelevant.

        Returns:
            The requested checkout; parent and primary trees are irrelevant.

        """
        resolved_root = repository_root.expanduser().resolve()
        if not resolved_root.is_dir():
            return r[Path].fail(f"repository root is not a directory: {resolved_root}")
        return r[Path].ok(resolved_root)

    @staticmethod
    def workspace_analysis_exclusion_paths(
        workspace: m.Infra.WorkspaceSpec,
    ) -> tuple[Path, ...]:
        """Return read-only external Git dependencies excluded from analysis.

        Returns:
            Read-only external Git dependencies excluded from analysis.

        """
        return workspace.external_dependency_paths

    @classmethod
    def analysis_exclusion_paths(
        cls,
        repository_root: Path,
    ) -> p.Result[tuple[Path, ...]]:
        """Load exclusions for governed repositories; ignore ungoverned trees.

        Returns:
            The resulting ``p.Result[tuple[Path, ...]]``.

        """
        resolved_root = repository_root.expanduser().resolve()
        if not (resolved_root / c.Infra.GITMODULES).is_file():
            return r[tuple[Path, ...]].ok(())
        if not (resolved_root / c.GIT_DIR_NAME).exists():
            return r[tuple[Path, ...]].ok(())
        return u.Infra.git_submodule_declarations(resolved_root).map(
            lambda declarations: tuple(
                declaration.path
                for declaration in declarations
                if declaration.managed is False
            ),
        )

    @classmethod
    def analysis_excluded_top_dirs(
        cls,
        repository_root: Path,
    ) -> p.Result[frozenset[str]]:
        """Return the first segments of the read-only external topology paths.

        This is the analysis scope that discovery utilities receive from their
        callers: the topology owner computes it, the utilities only apply it.

        Returns:
            The first segments of the read-only external topology paths.

        """
        return cls.analysis_exclusion_paths(repository_root).map(
            lambda paths: frozenset(path.parts[0] for path in paths if path.parts),
        )

    def detect(self, project_root: Path) -> p.Result[c.Infra.MakeProfile]:
        """Classify from governed members, not mere vendored Git topology.

        Returns:
            The resulting ``p.Result[c.Infra.MakeProfile]``.

        """
        try:
            resolved_root = project_root.expanduser().resolve()
        except c.EXC_OS_RUNTIME_TYPE as exc:
            return r[c.Infra.MakeProfile].fail_op("Workspace detection", exc)
        if not resolved_root.is_dir():
            return r[c.Infra.MakeProfile].fail(
                f"project root is not a directory: {resolved_root}",
            )
        workspace = self.load_workspace_spec(resolved_root)
        if workspace.failure:
            return r[c.Infra.MakeProfile].from_failure(workspace)
        return r[c.Infra.MakeProfile].ok(workspace.value.repository.role)

    @override
    def execute(self) -> p.Result[c.Infra.MakeProfile]:
        """Execute workspace detection for the configured root.

        Returns:
            The resulting ``p.Result[c.Infra.MakeProfile]``.

        """
        return self.detect(self.repository_root)


__all__: list[str] = ["FlextInfraWorkspaceDetector"]
