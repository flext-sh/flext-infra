"""Repository-local workspace detection from immutable Git topology inputs.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, override

from flext_infra import c, config, m, r, s, t, u
from flext_infra._utilities.workspace_inventory import (
    FlextInfraUtilitiesWorkspaceInventory,
)
from flext_infra.workspace import FlextInfraWorkspaceGovernanceMixin

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraWorkspaceDetector(
    FlextInfraWorkspaceGovernanceMixin,
    s[c.Infra.MakeProfile],
):
    """Classify a repository only from files and Git facts inside that checkout."""

    @classmethod
    def _resolved_beads(
        cls,
        resolved_root: Path,
        declaration: m.Infra.RepositoryDeltaSpec,
    ) -> p.Result[t.Pair[m.Infra.BeadsProjectSpec | None, bool]]:
        """Resolve the declared Beads ledger under the repository policy.

        Returns:
            The resulting workspace Beads specification with a presence flag
            (False when the repository policy opts out).

        """
        result_type = r[t.Pair[m.Infra.BeadsProjectSpec | None, bool]]
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
    ) -> p.Result[t.Triple[m.Infra.RepositoryRef, bool, m.Infra.ProjectSpec | None]]:
        """Load a selected repository manifest and reconcile it with Git truth.

        The checkout's own manifest is mandatory for identity: its complete
        typed ``repository`` record is authoritative for repository policy and
        must agree with the immutable identity and topology observed from Git.
        The matched repository policy overlay's Gas City participation rides
        along: ``True`` when the manifest declares no overlay.

        Returns:
            The resulting ``p.Result[t.Triple[m.Infra.RepositoryRef, bool,
                m.Infra.ProjectSpec | None]]``.

        """
        values = observed.model_dump(round_trip=True)
        values.update(
            declaration.model_dump(
                include=frozenset(m.Infra.RepositoryRef.model_fields),
                round_trip=True,
            ),
        )
        validated = u.validate_value(m.Infra.RepositoryRef, values)
        if validated.failure:
            return r[
                t.Triple[m.Infra.RepositoryRef, bool, m.Infra.ProjectSpec | None]
            ].from_failure(validated)
        return r[t.Triple[m.Infra.RepositoryRef, bool, m.Infra.ProjectSpec | None]].ok((
            validated.value,
            declaration.gascity_enabled,
            declaration.project,
        ))

    @classmethod
    def _local_repository_ref(
        cls,
        repository_root: Path,
        *,
        path: Path = Path(),
        composed: bool = False,
        declared_url: str | None = None,
    ) -> p.Result[m.Infra.RepositoryRef]:
        """Build identity from validated checkout metadata and native Git inputs.

        Returns:
            The resulting ``p.Result[m.Infra.RepositoryRef]``.

        """
        metadata = u.Infra.read_project_metadata_result(repository_root)
        if metadata.failure:
            return r[m.Infra.RepositoryRef].from_failure(metadata)
        project_name = metadata.value.project.name
        origin = cls._git_origin_url(repository_root)
        if origin.failure:
            return r[m.Infra.RepositoryRef].from_failure(origin)
        if declared_url is not None and u.Infra.git_remote_identity(
            origin.value,
        ) != u.Infra.git_remote_identity(declared_url):
            return r[m.Infra.RepositoryRef].fail(
                f"subproject origin differs from its .gitmodules URL: "
                f"{path.as_posix()}",
            )
        canonical_url = u.Infra.validate_git_remote_url(declared_url or origin.value)
        if canonical_url.failure:
            return r[m.Infra.RepositoryRef].from_failure(canonical_url)
        effective_url = canonical_url.value
        provider_result = cls._declared_provider_name(
            repository_root,
            origin_url=origin.value,
        )
        if provider_result.failure:
            return r[m.Infra.RepositoryRef].from_failure(provider_result)
        role = (
            c.Infra.MakeProfile.WORKSPACE
            if (repository_root / c.Infra.GITMODULES).is_file()
            else c.Infra.MakeProfile.STANDALONE
        )
        _, separator, repository_name = u.Infra.git_remote_identity(
            origin.value,
        ).partition("/")
        if not separator or not repository_name:
            return r[m.Infra.RepositoryRef].fail(
                f"Git origin does not identify a repository: {origin.value}",
            )
        # The manifest is the identity authority: the provider key is the one
        # the repository itself declares and the declared URL organization was
        # just reconciled against the live origin, so no catalog may override
        # either. Package participation stays an observed fact for a
        # manifest-less checkout (the observed state IS the identity): the
        # canonical layout resolution returns the typed "not a Python package
        # project" signal for such roots, and declaring a package there made
        # the fresh-import guard demand an importable layout no repository
        # publishes. A flext-* checkout that cannot resolve its package fails
        # the discovery contract loudly instead of being declared one.
        return r[m.Infra.RepositoryRef].ok(
            m.Infra.RepositoryRef(
                name=repository_name,
                distribution=project_name,
                url=effective_url,
                path=path,
                role=role,
                provider=provider_result.value,
                kind=c.Infra.ProjectKind.INTERNAL_FLEXT,
                codegen=c.Infra.CodegenKind.CONFORM,
                package=u.Infra.layout(repository_root) is not None,
                # The checkout's own root package is its environment's
                # editable install by the uv contract — the lock records
                # `editable = "."` for the project root in every standalone
                # checkout, and the provenance law compares this flag
                # against that record. Workspace-attached members carry
                # their attachment; the self root carries the contract.
                editable=composed or path == Path(),
                read_only=False,
            ),
        )

    @classmethod
    def _load_subprojects(
        cls,
        repository_root: Path,
        *,
        workspace_beads: m.Infra.BeadsProjectSpec | None,
        inputs: m.Infra.CodegenInputs,
        allow_unprovisioned_members: bool = False,
    ) -> p.Result[
        t.Triple[
            t.VariadicTuple[m.Infra.RepositoryRef],
            t.VariadicTuple[Path],
            t.VariadicTuple[m.Infra.GitSubmoduleDeclaration],
        ]
    ]:
        """Validate every direct governed .gitmodules entry before planning writes.

        Returns:
            The resulting ``p.Result[t.Pair[t.VariadicTuple[m.Infra.RepositoryRef],
                t.VariadicTuple[Path]]]``.

        """
        declared = u.Infra.git_submodule_declarations(repository_root)
        result_type = r[
            t.Triple[
                t.VariadicTuple[m.Infra.RepositoryRef],
                t.VariadicTuple[Path],
                t.VariadicTuple[m.Infra.GitSubmoduleDeclaration],
            ]
        ]
        if declared.failure:
            return result_type.from_failure(declared)
        if not declared.value:
            return result_type.ok(((), (), ()))
        subprojects: list[m.Infra.RepositoryRef] = []
        external: list[Path] = []
        pending: list[m.Infra.GitSubmoduleDeclaration] = []
        # The workspace-declared preference owns the baseline order: a fleet
        # integrating on a versioned release line (0.12.0-dev) is not covered
        # by the provider's conventional fallback names alone.
        baseline = u.Infra.resolve_integration_branch(
            repository_root,
            preference=(inputs.spec.branch_policy.integration_branch_preference),
            inputs=inputs,
        )
        if baseline.failure:
            return result_type.from_failure(baseline)
        context = m.Infra.SubprojectLoadContext(
            integration_branch=baseline.value if baseline.success else None,
            workspace_beads=workspace_beads,
            allow_unprovisioned_members=allow_unprovisioned_members,
        )
        for declaration in declared.value:
            loaded = cls._load_subproject(
                repository_root,
                declaration.path,
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
        path: Path,
        *,
        context: m.Infra.SubprojectLoadContext,
    ) -> p.Result[m.Infra.RepositoryRef | Path | m.Infra.GitSubmoduleDeclaration]:
        """Load one governed entry, or its declared path for external entries.

        A native Git false management declaration marks a read-only external
        dependency. An absent flag inherits participation. Managed entries
        resolve their package identity from a provisioned checkout; setup may
        retain an unprovisioned entry as its parsed Git declaration only.

        Returns:
                    The resulting ``p.Result[m.Infra.RepositoryRef | Path | m.Infra.GitSubmoduleDeclaration]``.

        """
        result_type = r[m.Infra.RepositoryRef | Path | m.Infra.GitSubmoduleDeclaration]
        contract = u.Infra.git_submodule_declaration(
            m.Infra.GitSubmoduleContractRequest(
                repo_root=repository_root,
                member_path=path.as_posix(),
            ),
        )
        if contract.failure:
            return result_type.from_failure(contract)
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
            repository_root,
            subproject_root.value,
            path,
            declared_url=contract.value.url,
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
        repository_root: Path,
        subproject_root: Path,
        path: Path,
        *,
        declared_url: str,
        context: m.Infra.SubprojectLoadContext,
    ) -> p.Result[m.Infra.RepositoryRef | Path | m.Infra.GitSubmoduleDeclaration]:
        """Resolve a provisioned checkout without a second identity catalog.

        Returns:
            Its observed identity, or its pending Git declaration for setup.
        """
        result_type = r[m.Infra.RepositoryRef | Path | m.Infra.GitSubmoduleDeclaration]
        if not (subproject_root / c.Infra.GIT_DIR).exists():
            if not context.allow_unprovisioned_members:
                error = FileNotFoundError(
                    f"governed subproject checkout is missing: {path.as_posix()}",
                )
                return result_type.fail(str(error), exception=error)
            pending = u.Infra.git_submodule_declaration(
                m.Infra.GitSubmoduleContractRequest(
                    repo_root=repository_root,
                    member_path=path.as_posix(),
                ),
            )
            if pending.failure:
                return result_type.from_failure(pending)
            return result_type.ok(pending.value)
        return cls._checkout_subproject(
            subproject_root,
            path,
            declared_url=declared_url,
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

        Returns:
            The resulting ``p.Result[m.Infra.WorkspaceSpec]``.

        """
        del project_metadata
        resolved_root = repository_root.expanduser().resolve()
        authenticated = cls._authenticated_identity(resolved_root)
        if authenticated.failure:
            return r[m.Infra.WorkspaceSpec].from_failure(authenticated)
        identity = authenticated.value
        if inputs is None:
            captured = u.Infra.load_codegen_inputs(resolved_root)
            if captured.failure:
                return r[m.Infra.WorkspaceSpec].from_failure(captured)
            inputs = captured.value
        declaration = inputs.spec.repository or m.Infra.RepositoryDeltaSpec()
        beads = cls._effective_workspace_beads(resolved_root, identity, declaration)
        if beads.failure:
            return r[m.Infra.WorkspaceSpec].from_failure(beads)
        workspace_beads = beads.value[0] if beads.value else None
        refs = cls._resolved_workspace_refs(
            resolved_root,
            workspace_beads,
            inputs=inputs,
            composed=identity.is_attached_submodule,
            allow_unprovisioned_members=allow_unprovisioned_members,
        )
        if refs.failure:
            return r[m.Infra.WorkspaceSpec].from_failure(refs)
        (
            (repository_ref, gascity_enabled, declared_project),
            (subprojects, external, pending),
        ) = refs.value
        named = cls._workspace_name(workspace_beads, repository_ref)
        if named.failure:
            return r[m.Infra.WorkspaceSpec].from_failure(named)
        external_consumers = (
            FlextInfraUtilitiesWorkspaceInventory.discover_external_consumers(
                resolved_root,
                inputs,
            )
        )
        if external_consumers.failure:
            return r[m.Infra.WorkspaceSpec].from_failure(external_consumers)
        return r[m.Infra.WorkspaceSpec].ok(
            m.Infra.WorkspaceSpec(
                name=named.value,
                beads=workspace_beads,
                gascity_enabled=gascity_enabled,
                repository=repository_ref,
                project=declared_project,
                namespace_scan_dirs=declaration.namespace_scan_dirs,
                integration=declaration.integration,
                docs_audit=declaration.docs_audit,
                subprojects=tuple(subprojects),
                pending_subprojects=tuple(pending),
                external_dependency_paths=tuple(external),
                external_consumers=external_consumers.value,
            ),
        )

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
    ) -> p.Result[t.VariadicTuple[m.Infra.BeadsProjectSpec]]:
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
            return r[t.VariadicTuple[m.Infra.BeadsProjectSpec]].from_failure(
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
    ) -> p.Result[t.VariadicTuple[m.Infra.BeadsProjectSpec]]:
        """Resolve the effective Beads ledger, inheriting through submodules.

        Returns:
            The effective workspace Beads specification as a 0-or-1 tuple.

        """
        result_type = r[t.VariadicTuple[m.Infra.BeadsProjectSpec]]
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
    ) -> p.Result[t.Pair[m.Infra.BeadsProjectSpec, m.Infra.RepositoryRef]]:
        """Load the superproject's Beads ledger and the member's governed ref.

        Returns:
            The resulting ``(inherited_beads, loaded_member)`` pair.

        """
        result_type = r[t.Pair[m.Infra.BeadsProjectSpec, m.Infra.RepositoryRef]]
        inherited_beads = cls.load_beads_spec(superproject_root)
        if inherited_beads.failure:
            return result_type.from_failure(inherited_beads)
        if not member_root.is_relative_to(superproject_root):
            return result_type.fail(
                f"Git submodule escapes its superproject: {member_root}",
            )
        member_path = member_root.relative_to(superproject_root)
        # Same owner as the parent load: the declared preference resolves a
        # versioned integration line the provider fallback names miss.
        baseline = u.Infra.resolve_integration_branch(
            superproject_root,
            preference=(
                config.Infra.codegen.branch_policy.integration_branch_preference
            ),
        )
        loaded_member = cls._load_subproject(
            superproject_root,
            member_path,
            context=m.Infra.SubprojectLoadContext(
                integration_branch=(baseline.value if baseline.success else None),
                workspace_beads=inherited_beads.value,
            ),
        )
        undeclared = f"Git submodule is not a declared governed project: {member_root}"
        if loaded_member.failure:
            return result_type.fail(loaded_member.error or undeclared)
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
        t.Pair[
            t.Triple[m.Infra.RepositoryRef, bool, m.Infra.ProjectSpec | None],
            t.Triple[
                t.SequenceOf[m.Infra.RepositoryRef],
                t.SequenceOf[Path],
                t.SequenceOf[m.Infra.GitSubmoduleDeclaration],
            ],
        ]
    ]:
        """Resolve the repository ref and the composed subproject topology.

        Returns:
            The resulting ``((repository_ref, gascity_enabled, declared_project),
            (subprojects, external))`` pair pair.

        """
        result_type = r[
            t.Pair[
                t.Triple[m.Infra.RepositoryRef, bool, m.Infra.ProjectSpec | None],
                t.Triple[
                    t.SequenceOf[m.Infra.RepositoryRef],
                    t.SequenceOf[Path],
                    t.SequenceOf[m.Infra.GitSubmoduleDeclaration],
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
        metadata = u.Infra.read_project_metadata_result(resolved_root)
        if metadata.failure:
            return r[m.Infra.RepositoryConformTarget].from_failure(metadata)
        canonical_project_name = metadata.value.project.name
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
    ) -> t.VariadicTuple[Path]:
        """Return read-only external Git dependencies excluded from analysis.

        Returns:
            Read-only external Git dependencies excluded from analysis.

        """
        return workspace.external_dependency_paths

    @classmethod
    def analysis_exclusion_paths(
        cls,
        repository_root: Path,
    ) -> p.Result[t.VariadicTuple[Path]]:
        """Load exclusions for governed repositories; ignore ungoverned trees.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[Path]]``.

        """
        resolved_root = repository_root.expanduser().resolve()
        if not (resolved_root / c.Infra.GITMODULES).is_file():
            return r[t.VariadicTuple[Path]].ok(())
        if not (resolved_root / ".git").exists():
            return r[t.VariadicTuple[Path]].ok(())
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
