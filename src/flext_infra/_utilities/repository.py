"""Detected repository identity and integration-branch resolution utilities.

flext-infra ships no provider registry: every repository's provider identity
is detected from that repository's own declarations (its workspace manifest,
its live Git origin, and its declared dependency sources), and every branch
is detected from live Git or declared explicitly by a caller.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from collections.abc import MutableMapping
from pathlib import Path

from flext_cli import u
from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

from flext_infra import c, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesDependencies,
    FlextInfraUtilitiesGit,
    FlextInfraUtilitiesProjectManagedArtifacts,
)
from flext_infra._utilities._git import (
    FlextInfraUtilitiesGitSemanticPublish,
    FlextInfraUtilitiesGitWorktreeDiscovery,
)
from flext_infra._utilities._pyproject.conform import (
    FlextInfraUtilitiesPyprojectConform,
)


class FlextInfraUtilitiesRepository(
    FlextInfraUtilitiesGit,
):
    """Resolve detected identity and branch policy for one governed repository."""

    @classmethod
    def rewrite_git_requirement_reference(
        cls,
        requirement: str,
        migration: m.Infra.GitSourceReferenceMigration,
    ) -> p.Result[str]:
        """Replace a selected explicit Git ref without changing requirement semantics.

        Returns:
            The resulting ``p.Result[str]``.

        """
        parsed = Requirement(requirement)
        if parsed.url is None or not parsed.url.startswith(
            c.Infra.GIT_URL_SCHEME_PREFIX
        ):
            return r[str].ok(requirement)
        source, fragment_separator, fragment = parsed.url.partition("#")
        remote, reference_separator, reference = source.rpartition("@")
        if not reference_separator or reference != migration.source_ref:
            return r[str].ok(requirement)
        declared = cls.declared_git_source(requirement)
        if declared.failure:
            return r[str].from_failure(declared)
        if not declared.value[0].startswith(migration.url_prefix):
            return r[str].ok(requirement)
        replacement = f"{remote}@{migration.target_ref}"
        if fragment_separator:
            replacement = f"{replacement}#{fragment}"
        return r[str].ok(requirement.replace(parsed.url, replacement, 1))

    @staticmethod
    def _dependency_requirement_arrays(
        payload: t.MutableJsonMapping,
    ) -> list[t.JsonValue]:
        """Collect every dependency array of the native project tables.

        Args:
            payload: Mutable parsed pyproject mapping.

        Returns:
            Every raw dependency array of project dependencies, optional
            dependencies, dependency groups and UV override and constraint
            tables.

        """
        project = u.Cli.toml_mapping_path(payload, (c.Infra.PROJECT,))
        if project is not None:
            requirements: list[t.JsonValue] = [project.get(c.Infra.DEPENDENCIES)]
            optional = u.Cli.toml_mapping_path(project, ("optional-dependencies",))
            if optional is not None:
                requirements.extend(optional.values())
        else:
            requirements = []
        groups = u.Cli.toml_mapping_path(payload, ("dependency-groups",))
        if groups is not None:
            requirements.extend(groups.values())
        uv = u.Cli.toml_mapping_path(payload, ("tool", "uv"))
        if uv is not None:
            requirements.extend(
                uv.get(key)
                for key in ("override-dependencies", "constraint-dependencies")
            )
        return requirements

    @classmethod
    def _rewritten_requirement_arrays(
        cls,
        requirements: t.SequenceOf[t.JsonValue],
        migration: m.Infra.GitSourceReferenceMigration,
    ) -> p.Result[t.StrSequence]:
        """Rewrite every selected Git reference inside the dependency arrays.

        Args:
            requirements: Raw dependency arrays collected from the payload.
            migration: Source-reference migration to apply.

        Returns:
            The change notes of every rewritten requirement, or the first
            rewrite failure.

        """
        changes: list[str] = []
        for entries in requirements:
            if not isinstance(entries, list):
                continue
            for index, original in enumerate(entries):
                if not isinstance(original, str):
                    continue
                rewritten = cls.rewrite_git_requirement_reference(original, migration)
                if rewritten.failure:
                    return r[t.StrSequence].from_failure(rewritten)
                if rewritten.value != original:
                    entries[index] = rewritten.value
                    changes.append(
                        f"Git reference {migration.source_ref} -> "
                        f"{migration.target_ref}: {Requirement(original).name}"
                    )
        return r[t.StrSequence].ok(tuple(changes))

    @staticmethod
    def _git_source_tables(
        payload: t.MutableJsonMapping,
    ) -> list[t.MutableJsonMapping]:
        """Collect the native UV and Poetry Git source tables.

        Args:
            payload: Mutable parsed pyproject mapping.

        Returns:
            Every mutable source table that may carry Git source entries.

        """
        tables: list[t.MutableJsonMapping] = []
        uv_sources = u.Cli.toml_mapping_path(payload, ("tool", "uv", "sources"))
        if uv_sources is not None:
            tables.append(uv_sources)
        poetry = u.Cli.toml_mapping_path(payload, ("tool", "poetry"))
        if poetry is not None:
            dependencies = u.Cli.toml_mapping_path(poetry, (c.Infra.DEPENDENCIES,))
            if dependencies is not None:
                tables.append(dependencies)
            poetry_groups = u.Cli.toml_mapping_path(poetry, ("group",))
            if poetry_groups is not None:
                for group in poetry_groups.values():
                    if isinstance(group, MutableMapping):
                        dependencies = u.Cli.toml_mapping_path(
                            group, (c.Infra.DEPENDENCIES,)
                        )
                        if dependencies is not None:
                            tables.append(dependencies)
        return tables

    @classmethod
    def _rewritten_git_source_tables(
        cls,
        tables: t.SequenceOf[t.MutableJsonMapping],
        migration: m.Infra.GitSourceReferenceMigration,
    ) -> p.Result[t.StrSequence]:
        """Rewrite every selected Git reference inside the native source tables.

        Args:
            tables: Mutable source tables collected from the payload.
            migration: Source-reference migration to apply.

        Returns:
            The change notes of every rewritten table entry, or the first
            rewrite failure.

        """
        changes: list[str] = []
        for table in tables:
            for name, value in table.items():
                for entry in value if isinstance(value, list) else (value,):
                    if not isinstance(entry, MutableMapping):
                        continue
                    rewritten = cls._rewrite_git_source_table(name, entry, migration)
                    if rewritten.failure:
                        return r[t.StrSequence].from_failure(rewritten)
                    changes.extend(rewritten.value)
        return r[t.StrSequence].ok(tuple(changes))

    @classmethod
    def rewrite_git_source_references(
        cls,
        payload: t.MutableJsonMapping,
        migration: m.Infra.GitSourceReferenceMigration,
    ) -> p.Result[t.StrSequence]:
        """Migrate only dependency arrays and native UV/Poetry Git source tables.

        Returns:
            The resulting ``p.Result[t.StrSequence]``.

        """
        rewritten_requirements = cls._rewritten_requirement_arrays(
            cls._dependency_requirement_arrays(payload),
            migration,
        )
        if rewritten_requirements.failure:
            return r[t.StrSequence].from_failure(rewritten_requirements)
        rewritten_tables = cls._rewritten_git_source_tables(
            cls._git_source_tables(payload),
            migration,
        )
        if rewritten_tables.failure:
            return r[t.StrSequence].from_failure(rewritten_tables)
        return r[t.StrSequence].ok(
            (*rewritten_requirements.value, *rewritten_tables.value),
        )

    @classmethod
    def _rewrite_git_source_table(
        cls,
        name: str,
        source: t.MutableJsonMapping,
        migration: m.Infra.GitSourceReferenceMigration,
    ) -> p.Result[t.StrSequence]:
        """Retain a native source table's selector type and all other fields.

        Returns:
            The resulting ``p.Result[t.StrSequence]``.

        """
        remote = source.get("git")
        if not isinstance(remote, str):
            return r[t.StrSequence].ok(())
        references = [key for key in ("branch", "rev", "tag") if key in source]
        if not any(source[key] == migration.source_ref for key in references):
            return r[t.StrSequence].ok(())
        if len(references) != 1:
            return r[t.StrSequence].fail(f"ambiguous explicit Git reference for {name}")
        reference_key = references[0]
        declared = cls.declared_git_source(
            f"{name} @ {c.Infra.GIT_URL_SCHEME_PREFIX}{remote}@{migration.source_ref}",
        )
        if declared.failure:
            return r[t.StrSequence].from_failure(declared)
        if not declared.value[0].startswith(migration.url_prefix):
            return r[t.StrSequence].ok(())
        source[reference_key] = migration.target_ref
        return r[t.StrSequence].ok((
            (
                f"Git {reference_key} {migration.source_ref} -> "
                f"{migration.target_ref}: "
                f"{name}"
            ),
        ))

    @classmethod
    def configured_repository_ref(
        cls,
        *,
        codegen: m.Infra.CodegenConfigSpec,
        repository_root: Path,
    ) -> p.Result[m.Infra.RepositoryRef]:
        """Detect one reference for the infrastructure distribution.

        The URL is detected — never looked up in a catalog — from the first
        declaration the checkout carries: its own project identity (the
        checkout is the infrastructure repository, so its live Git origin
        speaks), a declared direct Git dependency source for the distribution,
        or its workspace manifest ``repository``/``members`` declaration. A
        checkout that declares none fails loudly.

        Returns:
            The resulting ``p.Result[m.Infra.RepositoryRef]``.

        """
        source = codegen.infra_repository
        distribution = source.distribution
        line = cls.flext_integration_line(
            codegen=codegen,
            repository_root=repository_root,
        )
        if line.failure:
            return r[m.Infra.RepositoryRef].from_failure(line)
        return r[m.Infra.RepositoryRef].ok(
            m.Infra.RepositoryRef(
                name=distribution,
                distribution=distribution,
                url=f"{line.value.base_url}/{distribution}.git",
                path=Path(distribution),
                role=c.Infra.MakeProfile.STANDALONE,
                provider=source.provider,
                kind=c.Infra.ProjectKind.INTERNAL_FLEXT,
                codegen=c.Infra.CodegenKind.CONFORM,
                package=True,
                editable=True,
                read_only=False,
            ),
        )

    @classmethod
    def flext_integration_line(
        cls,
        *,
        codegen: m.Infra.CodegenConfigSpec,
        repository_root: Path,
        bootstrap_source: m.Infra.CodegenBootstrapSource | None = None,
    ) -> p.Result[m.Infra.WorkspaceIntegrationSpec]:
        """Detect the FLEXT line (provider base URL and branch) a checkout consumes.

        The line is a fact of the exact infrastructure dependency, never of
        another distribution's ref or the consumer's own identity. Family
        distributions share a provider but may declare different refs.
        It is detected, never cataloged, from the
        first declaration the checkout carries — the infrastructure checkout's
        own origin and integration branch, a declared direct Git source for
        the distribution (URL and ref), or the owning workspace manifest's
        member entry on that workspace's integration branch. Two declared
        sources that disagree, or none at all, fail loudly.

        A fully explicit caller declaration (``declared`` carrying both
        organization and base URL) outranks detection: ``codegen new`` has no
        checkout to detect from — the caller declares the provider and
        integration branch up front, and that declaration is the line. A
        provider key plus branch alone is NOT a line (a consumer's own
        provider identity never fabricates one) and detection still runs.

        Returns:
            The resulting ``p.Result[m.Infra.WorkspaceIntegrationSpec]``.

        """
        source = codegen.infra_repository
        distribution = source.distribution
        policy_branch = codegen.branch_policy.integration_branch
        if bootstrap_source is not None:
            if (repository_root / c.PYPROJECT_FILENAME).exists():
                return r[m.Infra.WorkspaceIntegrationSpec].fail(
                    "bootstrap provenance cannot replace existing project sources",
                )
            canonical = cls._canonical_https_url(bootstrap_source.url)
            if canonical.failure:
                return r[m.Infra.WorkspaceIntegrationSpec].from_failure(canonical)
            detected = r[t.Pair[str, str]].ok((canonical.value, bootstrap_source.ref))
        else:
            detected = cls._detected_infra_source(
                repository_root=repository_root,
                distribution=distribution,
                policy_branch=policy_branch,
            )
        if detected.failure:
            return r[m.Infra.WorkspaceIntegrationSpec].from_failure(detected)
        url, ref = detected.value
        # The detected source arrives in either canonical form (with or
        # without the .git suffix — GitHub checkouts omit it); normalize
        # before comparing so URL spelling never fails the line detection.
        normalized_url = url.removesuffix(c.GIT_DIR_NAME)
        suffix = f"/{distribution}"
        if not normalized_url.endswith(suffix):
            return r[m.Infra.WorkspaceIntegrationSpec].fail(
                f"infrastructure source must be the {distribution} repository: {url}",
            )
        organization, separator, _ = (
            FlextInfraUtilitiesGitWorktreeDiscovery.git_remote_identity(
                url,
            ).partition("/")
        )
        if not separator:
            return r[m.Infra.WorkspaceIntegrationSpec].fail(
                f"infrastructure source must name an owner and repository: {url}",
            )
        return r[m.Infra.WorkspaceIntegrationSpec].ok(
            m.Infra.WorkspaceIntegrationSpec(
                provider=source.provider,
                branch=ref,
                organization=organization,
                base_url=normalized_url.removesuffix(suffix),
            ),
        )

    @classmethod
    def flext_integration_line_for_checkout(
        cls,
        *,
        codegen: m.Infra.CodegenConfigSpec,
        repository_root: Path,
        workspace: m.Infra.WorkspaceSpec,
    ) -> p.Result[m.Infra.WorkspaceIntegrationSpec]:
        """Resolve the FLEXT line for one workspace checkout.

        The single owner of the bootstrap provenance decision every line
        consumer shares: a declared ``flext_source`` applies only while the
        checkout has no project file of its own (there would be nothing to
        bootstrap); an existing project file means the line is detected from
        the checkout itself.

        Returns:
            The resulting ``p.Result[m.Infra.WorkspaceIntegrationSpec]``.

        """
        return cls.flext_integration_line(
            codegen=codegen,
            repository_root=repository_root,
            bootstrap_source=(
                workspace.flext_source
                if not (repository_root / c.PYPROJECT_FILENAME).exists()
                else None
            ),
        )

    @classmethod
    def _detected_infra_source(
        cls,
        *,
        repository_root: Path,
        distribution: str,
        policy_branch: str,
    ) -> p.Result[t.Pair[str, str]]:
        """Detect the infrastructure distribution's canonical URL and ref.

        Returns:
            The resulting ``p.Result[t.Pair[str, str]]``.

        """
        metadata = FlextInfraUtilitiesPyprojectConform.read_project_metadata_result(
            repository_root,
        )
        if metadata.success and metadata.value.project.name == distribution:
            return cls._checkout_origin_source(repository_root, policy_branch)
        pyproject_path = repository_root / c.PYPROJECT_FILENAME
        if pyproject_path.is_file():
            declared = cls._declared_dependency_source(
                pyproject_path=pyproject_path,
                distribution=distribution,
                prefix=f"{distribution.partition('-')[0]}-",
                policy_branch=policy_branch,
            )
            if declared.failure or declared.value[0]:
                return declared
        manifest = cls._git_declared_distribution_url(
            repository_root=repository_root,
            distribution=distribution,
        )
        if manifest.failure:
            return r[t.Pair[str, str]].from_failure(manifest)
        if manifest.value:
            return cls.resolve_integration_branch(
                repository_root,
                policy_branch=policy_branch,
            ).map(lambda branch: (manifest.value, branch))
        declared_line = cls._declared_flext_source(
            repository_root, distribution=distribution, policy_branch=policy_branch
        )
        if declared_line.failure or declared_line.value[0]:
            return declared_line
        return r[t.Pair[str, str]].fail(
            f"infrastructure repository {distribution} is undeclared by this "
            f"checkout: no project identity, no direct git dependency line, "
            f"no workspace manifest entry, and no manifest flext_source: "
            f"{repository_root}",
        )

    @classmethod
    def _checkout_origin_source(
        cls,
        repository_root: Path,
        policy_branch: str,
    ) -> p.Result[t.Pair[str, str]]:
        """Resolve an infrastructure checkout's published origin and branch.

        Returns:
            The validated origin URL and integration branch.

        """
        origin = FlextInfraUtilitiesGitSemanticPublish.git_remote_url(
            m.Infra.GitRemoteUrlRequest(
                repo_root=repository_root,
                remote=c.Infra.GIT_DEFAULT_REMOTE,
            ),
        )
        if origin.failure or not origin.value.text.strip():
            return r[t.Pair[str, str]].fail(
                "the infrastructure checkout must publish a Git origin: "
                f"{repository_root}",
            )
        branch = cls.resolve_integration_branch(
            repository_root,
            policy_branch=policy_branch,
        )
        if branch.failure:
            return r[t.Pair[str, str]].from_failure(branch)
        return cls._canonical_https_url(origin.value.text.strip()).map(
            lambda url: (url, branch.value),
        )

    @classmethod
    def _declared_flext_source(
        cls,
        repository_root: Path,
        *,
        distribution: str,
        policy_branch: str,
    ) -> p.Result[t.Pair[str, str]]:
        """Return the own declaration's explicit dependency integration source.

        A scaffold source declares the line directly. An immutable candidate
        declares its repository while the existing branch policy owns the
        integration line; the candidate commit never becomes a branch selector.

        Returns:
            The repository's explicit dependency source, when declared.

        """
        loaded = FlextInfraUtilitiesProjectManagedArtifacts.load_codegen_inputs(
            repository_root,
        )
        if loaded.failure:
            return r[t.Pair[str, str]].from_failure(loaded)
        repository = loaded.value.spec.repository
        project = repository.project
        if project is None or project.flext_source is None:
            candidates = tuple(
                candidate
                for candidate in repository.candidate_dependencies
                if canonicalize_name(candidate.distribution)
                == canonicalize_name(distribution)
            )
            if not candidates:
                return r[t.Pair[str, str]].ok(("", ""))
            return cls._canonical_https_url(candidates[0].url).map(
                lambda url: (url, policy_branch),
            )
        parsed = cls.declared_git_source(project.flext_source)
        if parsed.failure or not cls.ref_is_commit(parsed.value[1]):
            return parsed
        return r[t.Pair[str, str]].fail(
            "project.flext_source declares an integration line, never a commit "
            f"(uv.lock records it and only `make upg` moves it): "
            f"{project.flext_source}",
        )

    @classmethod
    def validate_git_remote_url(cls, url: str) -> p.Result[str]:
        """Return the canonical HTTPS form of one declared Git remote URL.

        A bootstrap declares its remotes before any project metadata exists,
        so an unusable URL must fail here — before a directory or Git effect —
        instead of surfacing later as a generated dependency source.

        Returns:
            The canonical HTTPS form of one declared Git remote URL.

        """
        return cls._canonical_https_url(url.strip())

    @classmethod
    def _declared_dependency_lines(
        cls,
        payload: t.JsonMapping,
        *,
        pyproject_path: Path,
        prefix: str,
    ) -> p.Result[t.MutableMappingKV[t.Pair[str, str], t.Pair[str, str]]]:
        """Collect the declared ``<prefix>*`` line sources of one pyproject.

        Returns:
            Sources keyed by normalized distribution and marker.

        """
        lines: t.MutableMappingKV[t.Pair[str, str], t.Pair[str, str]] = {}
        providers: set[str] = set()
        for requirement in cls._dependency_requirements(payload):
            parsed = cls._declared_requirement_line(requirement, prefix)
            if parsed.failure:
                return r[
                    t.MutableMappingKV[t.Pair[str, str], t.Pair[str, str]]
                ].from_failure(parsed)
            if parsed.value[0]:
                declaration = Requirement(requirement)
                key = (
                    canonicalize_name(declaration.name),
                    str(declaration.marker or ""),
                )
                providers.add(
                    parsed.value[0].removesuffix(c.GIT_DIR_NAME).rsplit("/", 1)[0]
                )
                if len(providers) > 1 or (key in lines and lines[key] != parsed.value):
                    return r[
                        t.MutableMappingKV[t.Pair[str, str], t.Pair[str, str]]
                    ].fail(
                        f"{pyproject_path.name} declares conflicting "
                        f"{prefix}* line sources (one provider per family, "
                        f"one source per distribution and marker): "
                        f"{requirement}",
                    )
                lines[key] = parsed.value
        return r[t.MutableMappingKV[t.Pair[str, str], t.Pair[str, str]]].ok(
            lines,
        )

    @classmethod
    def _declared_workspace_source(
        cls,
        payload: t.JsonMapping,
        *,
        pyproject_path: Path,
        distribution: str,
        policy_branch: str,
    ) -> p.Result[t.Pair[str, str]]:
        """Resolve the workspace-membership source, or an empty payload.

        uv workspace membership IS a declaration: a bare-name requirement of
        the distribution backed by `[tool.uv.sources.<name>] workspace = true`
        resolves through the workspace root's manifest, and the member's
        checkout IS the provider. The superproject integration line (already
        recovered from the workspace root's own manifest by the caller's
        manifest pass) names the published source.

        Returns:
            The published source for one workspace member, or an EMPTY payload
            (never None) when no declared source exists.

        """
        tool = payload.get("tool")
        uv = tool.get("uv") if isinstance(tool, dict) else None
        raw_sources = uv.get("sources") if isinstance(uv, dict) else None
        sources: t.JsonMapping = raw_sources if isinstance(raw_sources, dict) else {}
        entry = sources.get(distribution)
        if isinstance(entry, dict) and entry.get("workspace") is True:
            for requirement in cls._dependency_requirements(payload):
                parsed = re.split(r"[\s;(\[]", requirement.strip(), maxsplit=1)[0]
                if parsed == distribution:
                    return cls.resolve_integration_branch(
                        pyproject_path.parent,
                        policy_branch=policy_branch,
                    ).map(
                        lambda branch: (
                            f"https://github.com/flext-sh/{distribution}.git",
                            branch,
                        ),
                    )
        # No declared source: absence is an EMPTY payload, never None.
        return r[t.Pair[str, str]].ok(("", ""))

    @classmethod
    def _declared_dependency_source(
        cls,
        *,
        pyproject_path: Path,
        distribution: str,
        prefix: str,
        policy_branch: str,
    ) -> p.Result[t.Pair[str, str]]:
        """Return the exact distribution source declared by the pyproject.

        Internal dependencies share a provider, not necessarily a ref.
        uv.lock alone records the commit each line resolves to, so a
        commit ref left in the projection declares no line. A plain
        (source-less) requirement names a workspace dependency whose URL the
        workspace manifest owns. Other distributions never supply its ref.

        Returns:
            The exact distribution's source, or its declared workspace source.

        """
        payload = FlextInfraUtilitiesPyprojectConform.declared_dependency_payload(
            pyproject_path,
        )
        if payload.failure:
            return r[t.Pair[str, str]].from_failure(payload)
        lines = cls._declared_dependency_lines(
            payload.value,
            pyproject_path=pyproject_path,
            prefix=prefix,
        )
        if lines.failure:
            return r[t.Pair[str, str]].from_failure(lines)
        sources = {
            source
            for (name, _), source in lines.value.items()
            if name == canonicalize_name(distribution)
            and not cls.ref_is_commit(source[1])
        }
        if len(sources) > 1:
            return r[t.Pair[str, str]].fail(
                f"{pyproject_path.name} declares ambiguous {distribution} authority",
            )
        if sources:
            (source,) = sources
            return r[t.Pair[str, str]].ok(source)
        return cls._declared_workspace_source(
            payload.value,
            pyproject_path=pyproject_path,
            distribution=distribution,
            policy_branch=policy_branch,
        )

    @staticmethod
    def _dependency_requirements(payload: t.JsonMapping) -> list[str]:
        """Read the declared dependency groups through the shared parser.

        Returns:
            Requirement strings from all declared dependency groups.

        """
        requirements: list[str] = []
        project = payload.get(c.Infra.PROJECT)
        if isinstance(project, dict):
            for key in (c.Infra.DEPENDENCIES, c.Infra.OPTIONAL_DEPENDENCIES):
                requirements.extend(
                    FlextInfraUtilitiesDependencies.raw_requirement_values(
                        project.get(key),
                    ),
                )
        requirements.extend(
            FlextInfraUtilitiesDependencies.raw_requirement_values(
                payload.get(c.Infra.DEPENDENCY_GROUPS),
            ),
        )
        return requirements

    @classmethod
    def _declared_requirement_line(
        cls,
        requirement: str,
        prefix: str,
    ) -> p.Result[t.Pair[str, str]]:
        """Validate one family member's provenance before collecting its line.

        Returns:
            The declared repository URL and ref, or the empty pair for a non-line.

        """
        name = FlextInfraUtilitiesDependencies.dep_name(requirement)
        if name is not None:
            name = canonicalize_name(name)
        if name is None or not name.startswith(prefix):
            return r[t.Pair[str, str]].ok(("", ""))
        parsed = cls.declared_git_source(requirement)
        if parsed.failure:
            return parsed
        url = parsed.value[0]
        if not url:
            return parsed
        if not url.startswith("https://"):
            return r[t.Pair[str, str]].fail(
                f"declared internal dependency provenance must be HTTPS: {requirement}",
            )
        repo_slug = url.removesuffix(c.GIT_DIR_NAME).rsplit("/", 1)[-1]
        if repo_slug.replace("_", "-") != name:
            return r[t.Pair[str, str]].fail(
                f"internal dependency source must be the {name} repository: "
                f"{requirement}",
            )
        return r[t.Pair[str, str]].ok(parsed.value)

    @classmethod
    def _git_declared_distribution_url(
        cls,
        *,
        repository_root: Path,
        distribution: str,
    ) -> p.Result[str]:
        """Resolve a composed distribution from its actual checkout.

        Returns:
            The matching native Git URL, or an empty absence payload.

        """
        result_type = r[str]
        declarations = (
            FlextInfraUtilitiesGitWorktreeDiscovery.git_submodule_declarations(
                repository_root,
            )
        )
        if declarations.failure:
            return result_type.from_failure(declarations)
        for declaration in declarations.value:
            if declaration.managed is False:
                continue
            member_root = (repository_root / declaration.path).resolve()
            if not member_root.is_relative_to(repository_root.resolve()):
                error = ValueError(
                    f"subproject escapes workspace root: {declaration.path}",
                )
                return result_type.fail(str(error), exception=error)
            if not (member_root / c.Infra.GIT_DIR).exists():
                error = FileNotFoundError(
                    "distribution discovery requires a provisioned checkout: "
                    f"{declaration.path}",
                )
                return result_type.fail(str(error), exception=error)
            if not (member_root / c.PYPROJECT_FILENAME).is_file():
                continue
            metadata = FlextInfraUtilitiesPyprojectConform.read_project_metadata_result(
                member_root,
            )
            if metadata.failure:
                return result_type.from_failure(metadata)
            if metadata.value.project.name == distribution:
                return cls._canonical_https_url(declaration.url)
        return result_type.ok("")

    @staticmethod
    def repository_provider(
        repository: p.Infra.RepositoryRef,
    ) -> p.Result[m.Infra.ProviderIdentitySpec]:
        """Detect the provider identity a repository declares for itself.

        The name is the key the repository's own manifest declares and the
        organization and base URL are read from that same declaration's
        canonical URL through the ``git_remote_identity`` normalizer. Nothing
        is matched against configured rows and no branch is fabricated here.

        Returns:
            The resulting ``p.Result[m.Infra.ProviderIdentitySpec]``.

        """
        url = repository.url.strip()
        organization, separator, _ = (
            FlextInfraUtilitiesGitWorktreeDiscovery.git_remote_identity(
                url,
            ).partition("/")
        )
        if not separator:
            return r[m.Infra.ProviderIdentitySpec].fail(
                f"repository url must name an owner and repository: {url}",
            )
        if not url.startswith("https://"):
            return r[m.Infra.ProviderIdentitySpec].fail(
                f"provider identity requires a canonical HTTPS declaration url: {url}",
            )
        return r[m.Infra.ProviderIdentitySpec].ok(
            m.Infra.ProviderIdentitySpec(
                name=repository.provider,
                organization=organization,
                base_url=url.removesuffix(c.GIT_DIR_NAME).rsplit("/", 1)[0],
            ),
        )

    @classmethod
    def repository_page_url(cls, repository: p.Infra.RepositoryRef) -> p.Result[str]:
        """Return the provider HTTPS page of one repository, whatever its transport.

        CI rewrites member origins to SSH deploy-key URLs, so the clone URL is
        never a page URL: the page is the declared provider base URL plus the
        repository segment of the transport-stable ``owner/repository`` identity.

        Returns:
            The provider HTTPS page of one repository, whatever its transport.

        """
        provider = cls.repository_provider(repository)
        if provider.failure:
            return r[str].from_failure(provider)
        owner, separator, name = (
            FlextInfraUtilitiesGitWorktreeDiscovery.git_remote_identity(
                repository.url,
            ).partition("/")
        )
        if not separator or not name or owner != provider.value.organization.casefold():
            return r[str].fail(
                "repository URL does not identify a repository of provider "
                f"{provider.value.name}: {repository.name}",
            )
        return r[str].ok(f"{provider.value.base_url.rstrip('/')}/{name}")

    @classmethod
    def _captured_codegen_inputs(
        cls,
        repository_root: Path,
        inputs: m.Infra.CodegenInputs | None,
    ) -> p.Result[m.Infra.CodegenInputs]:
        """Load the repository codegen inputs when the caller passed none.

        Args:
            repository_root: Repository whose strict policy is loaded.
            inputs: Caller-supplied inputs, or ``None`` to load from disk.

        Returns:
            The effective codegen inputs, or the load failure.

        """
        if inputs is not None:
            return r[m.Infra.CodegenInputs].ok(inputs)
        captured = FlextInfraUtilitiesProjectManagedArtifacts.load_codegen_inputs(
            repository_root,
        )
        if captured.failure:
            return r[m.Infra.CodegenInputs].from_failure(captured)
        return r[m.Infra.CodegenInputs].ok(captured.value)

    @classmethod
    def _submodule_integration_branch(
        cls,
        identity: m.Infra.GitIdentityReport,
        superproject_root: Path,
    ) -> p.Result[str]:
        """Resolve the integration branch declared for one managed member.

        Args:
            identity: Git identity carrying the superproject binding.
            superproject_root: Resolved superproject root of the member.

        Returns:
            The member's declared integration branch, the superproject's
            recursive resolution, or the first declaration failure.

        """
        member_root = (
            identity.repo_root
            if identity.is_attached_submodule
            else identity.primary_root
        )
        if not member_root.is_relative_to(superproject_root):
            error = ValueError(
                f"submodule identity escapes its superproject: {member_root}",
            )
            return r[str].fail(str(error), exception=error)
        contract = FlextInfraUtilitiesGit.git_submodule_declaration(
            m.Infra.GitSubmoduleContractRequest(
                repo_root=superproject_root,
                member_path=member_root.relative_to(superproject_root).as_posix(),
            ),
        )
        if contract.failure:
            return r[str].from_failure(contract)
        branch = contract.value.branch
        if not branch:
            error = ValueError(
                "managed member declares no integration branch in .gitmodules: "
                f"{contract.value.path}",
            )
            return r[str].fail(str(error), exception=error)
        if branch != c.Infra.FOLLOW_SUPERPROJECT_BRANCH:
            return r[str].ok(branch)
        parent_inputs = FlextInfraUtilitiesProjectManagedArtifacts.load_codegen_inputs(
            superproject_root,
        )
        if parent_inputs.failure:
            return r[str].from_failure(parent_inputs)
        return cls.resolve_integration_branch(
            superproject_root,
            policy_branch=(parent_inputs.value.spec.branch_policy.integration_branch),
            inputs=parent_inputs.value,
        )

    @classmethod
    def _published_integration_baseline(
        cls,
        repository_root: Path,
        policy_branch: str,
    ) -> p.Result[str]:
        """Return the declared policy line once published Git carries it.

        Args:
            repository_root: Repository whose remote-tracking refs are probed.
            policy_branch: Workspace-declared policy integration line.

        Returns:
            The published integration baseline, or the loud publication
            failure.

        """
        baseline = cls.repository_baseline_branch(
            repository_root,
            declared_branch=policy_branch,
        )
        if baseline.success:
            return r[str].ok(baseline.value)
        return r[str].fail(
            "integration line must be published by Git: "
            f"{repository_root}: {baseline.error}",
        )

    @classmethod
    def resolve_integration_branch(
        cls,
        repository_root: Path,
        *,
        policy_branch: str,
        declared: str | None = None,
        inputs: m.Infra.CodegenInputs | None = None,
    ) -> p.Result[str]:
        """Return the integration branch one repository integrates on.

        Precedence, every declaration before any Git probe: the repository's
        own manifest (``config/workspace.yaml`` ``integration.branch``); then
        ``declared`` — the declaration that governs this checkout when it
        carries none of its own (its in-memory spec before the manifest is
        written, or the workspace a governed member follows); then the
        workspace's declared policy line (``policy_branch``) checked against
        published Git — one line, one fact, no name list to guess from. When
        none exists the failure is loud and no default is invented.

        Returns:
            The integration branch one repository integrates on.

        """
        captured_inputs = cls._captured_codegen_inputs(repository_root, inputs)
        if captured_inputs.failure:
            return r[str].from_failure(captured_inputs)
        inputs = captured_inputs.value
        repository = inputs.spec.repository
        if repository.integration is not None:
            return r[str].ok(repository.integration.branch)
        if declared and declared.strip():
            return r[str].ok(declared.strip())
        identity = FlextInfraUtilitiesGit.git_identity(
            m.Infra.GitRepoRequest(repo_root=repository_root),
        )
        if identity.failure:
            return r[str].from_failure(identity)
        superproject_root = identity.value.superproject_root
        if identity.value.is_submodule and superproject_root is not None:
            return cls._submodule_integration_branch(
                identity.value,
                superproject_root,
            )
        # The branch a checkout happens to carry is never the answer: a lane
        # rendering its own name into the CI trigger list can never reach a
        # generation fixed point (ADR-018 p.10 — derive from the declaration
        # and from published Git facts, never from the environment).
        return cls._published_integration_baseline(repository_root, policy_branch)

    @staticmethod
    def gitmodule_branch_is_governed(
        declared_branch: str,
        *,
        integration_branch: str | None = None,
    ) -> bool:
        """Accept follow-superproject (``.``) or the detected integration line.

        Returns:
            The resulting ``bool``.

        """
        if declared_branch == c.Infra.FOLLOW_SUPERPROJECT_BRANCH:
            return True
        return integration_branch is not None and declared_branch == integration_branch

    @classmethod
    def repository_baseline_branch(
        cls,
        repository_root: Path,
        *,
        declared_branch: str,
    ) -> p.Result[str]:
        """Return the declared integration line once published Git carries it.

        One declared line, one Git fact: the workspace declares its versioned
        integration line (``codegen.branch_policy.integration_branch``), and
        this check reads the live ref for exactly that name — either the
        published remote-tracking branch or the recorded release tag of the
        same name (a consumer may pin a recorded ``v0.12.x`` tag). A name
        published as both branch and tag is ambiguous and fails loud, and a
        repository that publishes neither has no integration baseline and
        fails loud — there is no name list to guess from and no default to
        invent.

        Returns:
            The declared integration line the repository publishes.

        """
        branch_probe = FlextInfraUtilitiesGitSemanticPublish.git_ref_exists(
            m.Infra.GitRefRequest(
                repo_root=repository_root,
                reference=f"refs/remotes/origin/{declared_branch}",
            ),
        )
        if branch_probe.failure:
            return r[str].from_failure(branch_probe)
        tag_probe = FlextInfraUtilitiesGitSemanticPublish.git_ref_exists(
            m.Infra.GitRefRequest(
                repo_root=repository_root,
                reference=f"refs/tags/{declared_branch}",
            ),
        )
        if tag_probe.failure:
            return r[str].from_failure(tag_probe)
        branch_exists = branch_probe.value.value
        tag_exists = tag_probe.value.value
        if branch_exists and tag_exists:
            return r[str].fail(
                "declared integration line is ambiguous: published as both "
                f"branch and tag ({declared_branch}): {repository_root}",
            )
        if branch_exists or tag_exists:
            return r[str].ok(declared_branch)
        return r[str].fail(
            "repository publishes no integration branch or release tag "
            f"(declared {declared_branch}): {repository_root}",
        )


__all__: t.VariadicTuple[str] = ("FlextInfraUtilitiesRepository",)
