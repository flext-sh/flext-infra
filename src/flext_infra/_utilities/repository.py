"""Canonical repository-to-provider resolution utilities."""

from __future__ import annotations

from pathlib import Path

from flext_cli import u
from flext_core import r
from flext_infra.constants import c
from flext_infra.models import m
from flext_infra.protocols import p
from flext_infra.typings import t


class FlextInfraUtilitiesRepository:
    """Resolve provider-owned policy for one governed repository."""

    @staticmethod
    def derived_repository_ref(
        distribution: str,
        *,
        provider: m.Infra.ProviderSpec,
        role: c.Infra.RepositoryRole = c.Infra.RepositoryRole.WORKSPACE_MEMBER,
        checkout: c.Infra.CheckoutKind = c.Infra.CheckoutKind.SUBMODULE,
    ) -> m.Infra.RepositoryRef:
        """Derive one repository reference from generic provider policy.

        flext-infra owns no catalog of the projects it serves, so a governed
        distribution that the live workspace does not declare is still
        resolvable: its canonical source is the provider contract plus its own
        distribution name. Nothing here is looked up; everything is derived.
        """
        return m.Infra.RepositoryRef(
            name=distribution,
            distribution=distribution,
            url=f"{provider.base_url.rstrip('/')}/{distribution}.git",
            path=Path(distribution),
            role=role,
            provider=provider.name,
            branch=provider.branch,
            checkout=checkout,
            codegen=c.Infra.CodegenKind.CONFORM,
            package=True,
            editable=True,
            read_only=False,
        )

    @staticmethod
    def repository_provider(
        repository: p.Infra.RepositoryRef, providers: t.SequenceOf[m.Infra.ProviderSpec]
    ) -> p.Result[m.Infra.ProviderSpec]:
        """Return the unique typed provider declared by ``repository.provider``."""
        matches = tuple(
            provider for provider in providers if provider.name == repository.provider
        )
        if len(matches) != 1:
            return r[m.Infra.ProviderSpec].fail(
                f"repository provider must resolve exactly once: {repository.provider}"
            )
        return r[m.Infra.ProviderSpec].ok(matches[0])

    @staticmethod
    def repository_make_spec(
        base: m.Infra.MakeSpec, repository: m.Infra.RepositoryRef
    ) -> p.Result[m.Infra.MakeSpec]:
        """Return one revalidated Make graph for the selected repository."""
        extras = repository.extra_verbs
        if bool(extras) != (repository.script_dispatch is not None):
            return r[m.Infra.MakeSpec].fail(
                "repository extra verbs and script dispatcher must be declared together"
            )
        operations = {operation.name: operation for operation in base.operations}
        invalid = tuple(
            verb.name
            for verb in extras
            if (operation := operations.get(verb.operation)) is None
            or operation.executor != "script"
        )
        if invalid:
            return r[m.Infra.MakeSpec].fail(
                "repository extra verbs must reference one script operation: "
                f"{', '.join(invalid)}"
            )
        payload: dict[str, object] = {
            field_name: getattr(base, field_name)
            for field_name in type(base).model_fields
        }
        payload["verbs"] = (*base.verbs, *extras)
        try:
            return r[m.Infra.MakeSpec].ok(m.Infra.MakeSpec.model_validate(payload))
        except (c.ValidationError, TypeError, ValueError) as exc:
            return r[m.Infra.MakeSpec].fail_op("repository Make graph validation", exc)

    @classmethod
    def workspace_register_member(
        cls, workspace_root: Path, member: m.Infra.RepositoryRef
    ) -> p.Result[tuple[m.Infra.WorkspaceSpec, str]]:
        """Append one governed member to the handwritten manifest round-trip."""
        if member.role is not c.Infra.RepositoryRole.WORKSPACE_MEMBER:
            return r[tuple[m.Infra.WorkspaceSpec, str]].fail(
                f"invalid governed workspace member: {member.name}"
            )
        manifest_path = (
            workspace_root / c.CONFIG_DIR_NAME / c.Infra.WORKSPACE_MANIFEST_FILENAME
        )
        current = u.Cli.files_read_text(manifest_path)
        if current.failure:
            return r[tuple[m.Infra.WorkspaceSpec, str]].fail(
                current.error or f"workspace manifest read failed: {manifest_path}"
            )
        observed = cls.workspace_spec_load(workspace_root)
        if observed.failure:
            return r[tuple[m.Infra.WorkspaceSpec, str]].fail(
                observed.error or f"workspace manifest load failed: {manifest_path}"
            )
        if observed.value.repository.role is not c.Infra.RepositoryRole.WORKSPACE_ROOT:
            return r[tuple[m.Infra.WorkspaceSpec, str]].fail(
                f"workspace manifest owner is not a root: {workspace_root}"
            )
        loaded = u.Cli.yaml_roundtrip_load_map(manifest_path)
        if loaded.failure:
            return r[tuple[m.Infra.WorkspaceSpec, str]].fail(
                loaded.error or f"workspace manifest parse failed: {manifest_path}"
            )
        document = loaded.value
        try:
            declared = m.Infra.WorkspaceSpec.model_validate(
                u.Cli.yaml_to_plain(document)
            )
        except c.ValidationError as exc:
            return r[tuple[m.Infra.WorkspaceSpec, str]].fail_op(
                f"workspace manifest validation ({manifest_path})", exc
            )
        conflicts = tuple(
            repository
            for repository in (declared.repository, *declared.members)
            if repository.name == member.name
            or repository.distribution == member.distribution
            or repository.path == member.path
        )
        if conflicts and (len(conflicts) != 1 or conflicts[0] != member):
            return r[tuple[m.Infra.WorkspaceSpec, str]].fail(
                "workspace member identity conflicts with the manifest: "
                f"{member.name}/{member.distribution}/{member.path.as_posix()}"
            )
        if conflicts:
            registered = declared
            rendered_text = current.value
        else:
            members = document.get("members")
            if members is None:
                u.Cli.yaml_overlay_preserving_order(document, {"members": []})
                members = document.get("members")
            if not isinstance(members, list):
                return r[tuple[m.Infra.WorkspaceSpec, str]].fail(
                    f"workspace manifest members must be a sequence: {manifest_path}"
                )
            payload = member.model_dump(mode="json", exclude_computed_fields=True)
            members.append(u.Cli.yaml_deep_to_commented(payload))
            try:
                registered = m.Infra.WorkspaceSpec.model_validate(
                    u.Cli.yaml_to_plain(document)
                )
            except c.ValidationError as exc:
                return r[tuple[m.Infra.WorkspaceSpec, str]].fail_op(
                    f"workspace member registration ({manifest_path})", exc
                )
            rendered = u.Cli.yaml_roundtrip_dump_text(document)
            if rendered.failure:
                return r[tuple[m.Infra.WorkspaceSpec, str]].fail(
                    rendered.error
                    or f"workspace manifest render failed: {manifest_path}"
                )
            rendered_text = rendered.value
        return r[tuple[m.Infra.WorkspaceSpec, str]].ok((
            registered.model_copy(
                update={
                    "external_dependency_paths": tuple(
                        path
                        for path in observed.value.external_dependency_paths
                        if path != member.path
                    )
                }
            ),
            rendered_text,
        ))

    @classmethod
    def repository_baseline_branch(
        cls, repository_root: Path, declared_branch: str | None = None
    ) -> p.Result[str]:
        """Return the integration baseline the repository actually publishes.

        A repository's published remote HEAD owns its initial integration
        branch. A unique cached remote-tracking branch supports isolated/offline
        checkouts. The provider value is only the default for a repository that
        has not published a branch yet.

        ``declared_branch`` carries the provider-owned branch for a repository
        that cannot have published anything yet (project creation). Without it, a checkout
        with no integration branch fails closed instead of guessing.
        """
        from flext_infra.utilities import u

        published = u.Infra.git_capture(
            repository_root, ("ls-remote", "--symref", "origin", "HEAD")
        )
        if published.success:
            published_branches = tuple(
                reference.removeprefix("ref: refs/heads/")
                for line in published.value.splitlines()
                for reference, separator, target in (line.partition("\t"),)
                if separator
                and target == "HEAD"
                and reference.startswith("ref: refs/heads/")
            )
            if len(published_branches) == 1:
                return r[str].ok(published_branches[0])
            if published_branches:
                return r[str].fail(
                    f"repository publishes multiple default branches: {repository_root}"
                )

        cached = u.Infra.git_capture(
            repository_root,
            ("for-each-ref", "--format=%(refname)", "refs/remotes/origin"),
        )
        if cached.success:
            prefix = "refs/remotes/origin/"
            cached_branches = tuple(
                reference.removeprefix(prefix)
                for reference in cached.value.splitlines()
                if reference.startswith(prefix) and reference != f"{prefix}HEAD"
            )
            if len(cached_branches) == 1:
                return r[str].ok(cached_branches[0])
            if declared_branch and declared_branch in cached_branches:
                return r[str].ok(declared_branch)
            if cached_branches:
                return r[str].fail(
                    "repository integration branch is ambiguous: "
                    f"{', '.join(cached_branches)}"
                )
        if declared_branch:
            return r[str].ok(declared_branch)
        return r[str].fail(
            f"repository publishes no integration branch: {repository_root}"
        )

    @staticmethod
    def workspace_spec_load(repository_root: Path) -> p.Result[m.Infra.WorkspaceSpec]:
        """Load governed topology and derive observed external Git dependencies."""
        from flext_infra.workspace.detector import FlextInfraWorkspaceDetector

        return FlextInfraWorkspaceDetector.load_workspace_spec(repository_root)

    @staticmethod
    def repository_conform_target(
        repository_root: Path, workspace: m.Infra.WorkspaceSpec | None = None
    ) -> p.Result[m.Infra.RepositoryConformTarget]:
        """Return typed effective policy inferred from live repository topology."""
        from flext_infra.workspace.detector import FlextInfraWorkspaceDetector

        resolved_workspace = workspace
        if resolved_workspace is None:
            loaded = FlextInfraWorkspaceDetector.load_workspace_spec(repository_root)
            if loaded.failure:
                return r[m.Infra.RepositoryConformTarget].fail(
                    loaded.error or "workspace manifest load failed"
                )
            resolved_workspace = loaded.value
        return FlextInfraWorkspaceDetector.conform_target(
            repository_root, resolved_workspace
        )


__all__: tuple[str, ...] = ("FlextInfraUtilitiesRepository",)
