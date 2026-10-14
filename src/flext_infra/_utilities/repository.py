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
from urllib.parse import urlparse

from flext_cli import u
from packaging.requirements import Requirement

from flext_infra import c, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesDependencies,
    FlextInfraUtilitiesGit,
    FlextInfraUtilitiesGitSemanticPublishMixin,
    FlextInfraUtilitiesGitWorktreeDiscoveryMixin,
    FlextInfraUtilitiesProjectManagedArtifacts,
    FlextInfraUtilitiesPyproject,
)


class FlextInfraUtilitiesRepository:
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

    @staticmethod
    def ref_is_commit(ref: str) -> bool:
        """Whether one Git ref names a commit rather than an integration line.

        uv.lock, written only by ``make upg``, owns every resolved commit. In a
        generated pyproject a commit ref is projection residue that generation
        re-renders on the family line; in a hand-authored source it is a pin
        beside the lock and fails loudly.

        Returns:
            The resulting ``bool``.

        """
        return c.Infra.GIT_COMMIT_OID_RE.fullmatch(ref) is not None

    @staticmethod
    def declared_git_source(requirement: str) -> p.Result[t.Pair[str, str]]:
        """Parse one requirement's declared direct Git source.

        Returns ``(canonical_url, ref)`` for a requirement that declares
        ``name @ git+URL@REF``, or the empty pair when the requirement declares
        no direct source at all. The declared line is the only authority for the
        dependency's canonical URL and branch: canonicalization normalizes the
        transport scheme (``ssh://``, SCP-style, ``http``) to ``https`` and
        never invents an organization, host, or ref. A declared source that is
        not a Git URL, or a Git URL without a ref, fails loudly. Whether a
        commit ref is projection residue or a hand-authored pin is the
        caller's decision (``ref_is_commit``).

        Returns:
            The resulting ``p.Result[t.Pair[str, str]]``.

        """
        requirement_part, _, _ = requirement.partition(";")
        head_match = c.Infra.PEP621_REQUIREMENT_HEAD_RE.match(requirement_part.strip())
        if head_match is None:
            return r[t.Pair[str, str]].fail(f"invalid requirement head: {requirement}")
        _, at_separator, source = requirement_part.partition("@")
        if not at_separator:
            # Plain workspace requirement: no direct git source is declared.
            # Success payloads are never None (flext-core result law), so the
            # caller reads the empty pair as "no declared source".
            return r[t.Pair[str, str]].ok(("", ""))
        source = source.strip()
        if not source.startswith(c.Infra.GIT_URL_SCHEME_PREFIX):
            return r[t.Pair[str, str]].fail(
                f"internal dependency direct source must be a git URL: {requirement}",
            )
        url, ref_separator, ref = source.rpartition("@")
        url = url.removeprefix(c.Infra.GIT_URL_SCHEME_PREFIX).strip()
        ref = ref.strip()
        if not ref_separator or not ref:
            return r[t.Pair[str, str]].fail(
                f"internal dependency git source must declare a branch or ref: "
                f"{requirement}",
            )
        canonical = FlextInfraUtilitiesRepository._canonical_https_url(url)
        if canonical.failure:
            return r[t.Pair[str, str]].from_failure(canonical)
        return r[t.Pair[str, str]].ok((canonical.value, ref))

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

        The line is a fact of the infrastructure dependency, never of the
        consumer's own identity: every internal ``flext-*`` floor renders from
        it, so a repository living in another organization still resolves the
        whole family from one source. It is detected, never cataloged, from the
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
        normalized_url = url.removesuffix(".git")
        suffix = f"/{distribution}"
        if not normalized_url.endswith(suffix):
            return r[m.Infra.WorkspaceIntegrationSpec].fail(
                f"infrastructure source must be the {distribution} repository: {url}",
            )
        organization, separator, _ = (
            FlextInfraUtilitiesGitWorktreeDiscoveryMixin.git_remote_identity(
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
        metadata = FlextInfraUtilitiesPyproject.read_project_metadata_result(
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
        declared_line = cls._declared_flext_source(repository_root)
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
        origin = FlextInfraUtilitiesGitSemanticPublishMixin.git_remote_url(
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
    ) -> p.Result[t.Pair[str, str]]:
        """Return the own declaration's explicit scaffold dependency source.

        It declares the family line when the generated pyproject carries none
        (every internal requirement is commit residue of a retired pin). Being
        hand-authored, a commit ref there is a pin beside uv.lock and fails.

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
            # Absence is an EMPTY payload, never None (flext-core result law).
            return r[t.Pair[str, str]].ok(("", ""))
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

    @staticmethod
    def _canonical_https_url(url: str) -> p.Result[str]:
        """Canonicalize one Git remote URL to its HTTPS form, fail loud.

        Returns:
            The resulting ``p.Result[str]``.

        """
        if url.startswith("https://"):
            candidate = url
        elif url.startswith("http://"):
            candidate = f"https://{url.removeprefix('http://')}"
        elif url.startswith("ssh://"):
            candidate = f"https://{url.removeprefix('ssh://').removeprefix('git@')}"
        elif url.startswith("git@") and ":" in url:
            host, _, path = url.removeprefix("git@").partition(":")
            candidate = f"https://{host}/{path}"
        else:
            return r[str].fail(f"git remote url is not canonicalizable to HTTPS: {url}")
        # A URL without a host (``https:///repo``) or without a repository
        # path (``https://host``) carries no origin identity: reject it as a
        # declared remote rather than letting a generated source point at it.
        parsed = urlparse(candidate)
        if not parsed.netloc or not parsed.path.strip("/"):
            return r[str].fail(
                f"git remote url must name a host and repository path: {url}",
            )
        return r[str].ok(candidate)

    @classmethod
    def _declared_dependency_payload(
        cls,
        pyproject_path: Path,
    ) -> p.Result[t.JsonMapping]:
        """Read and parse the owner-recovered pyproject declaration.

        Returns:
            The parsed pyproject mapping as one result payload.

        """
        # Identity detection consumes the same owner-recovered declaration as
        # metadata and template composition. Raw projection bytes may still
        # carry managed merge blocks while the transaction is only planning.

        text = FlextInfraUtilitiesPyproject.live_pyproject_text(pyproject_path)
        if text.failure:
            return r[t.JsonMapping].from_failure(text)
        payload = u.Cli.toml_mapping_from_text(text.value)
        if payload is None:
            return r[t.JsonMapping].fail(
                f"pyproject is not valid TOML: {pyproject_path}",
            )
        return r[t.JsonMapping].ok(payload)

    @classmethod
    def _declared_dependency_lines(
        cls,
        payload: t.JsonMapping,
        *,
        pyproject_path: Path,
        prefix: str,
    ) -> p.Result[t.MutableMappingKV[t.Pair[str, str], str]]:
        """Collect the declared ``<prefix>*`` line sources of one pyproject.

        Returns:
            The declared base-url/ref lines mapped to one witness requirement.

        """
        lines: t.MutableMappingKV[t.Pair[str, str], str] = {}
        for requirement in cls._dependency_requirements(payload):
            parsed = cls._declared_requirement_line(requirement, prefix)
            if parsed.failure:
                return r[t.MutableMappingKV[t.Pair[str, str], str]].from_failure(parsed)
            if parsed.value[0]:
                lines.setdefault(parsed.value, requirement)
        if len(lines) > 1:
            declared = "; ".join(sorted(lines.values()))
            return r[t.MutableMappingKV[t.Pair[str, str], str]].fail(
                f"{pyproject_path.name} declares conflicting {prefix}* line sources "
                f"(one family, one provider and ref): {declared}",
            )
        return r[t.MutableMappingKV[t.Pair[str, str], str]].ok(lines)

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
        """Return the family line the pyproject declares, as a source for one member.

        Internal dependencies name one provider base URL and one integration
        line; uv.lock alone records the commit each line resolves to, so a
        commit ref left in the projection declares no line. A plain
        (source-less) requirement names a workspace dependency whose URL the
        workspace manifest owns. The line supplies the source of
        ``distribution``.

        Returns:
            The family line the pyproject declares, as a source for one member.

        """
        payload = cls._declared_dependency_payload(pyproject_path)
        if payload.failure:
            return r[t.Pair[str, str]].from_failure(payload)
        lines = cls._declared_dependency_lines(
            payload.value,
            pyproject_path=pyproject_path,
            prefix=prefix,
        )
        if lines.failure:
            return r[t.Pair[str, str]].from_failure(lines)
        if lines.value:
            (base_url, ref), _ = next(iter(lines.value.items()))
            return r[t.Pair[str, str]].ok((f"{base_url}/{distribution}.git", ref))
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
            The provider URL and ref, or the empty pair for a non-line.
        """
        name = FlextInfraUtilitiesDependencies.dep_name(requirement)
        if name is None or not name.startswith(prefix):
            return r[t.Pair[str, str]].ok(("", ""))
        parsed = cls.declared_git_source(requirement)
        if parsed.failure:
            return parsed
        url, ref = parsed.value
        if not url:
            return parsed
        if not url.startswith("https://"):
            return r[t.Pair[str, str]].fail(
                f"declared internal dependency provenance must be HTTPS: {requirement}",
            )
        repo_slug = url.removesuffix(".git").rsplit("/", 1)[-1]
        if repo_slug.replace("_", "-") != name:
            return r[t.Pair[str, str]].fail(
                f"internal dependency source must be the {name} repository: "
                f"{requirement}",
            )
        line = (
            ("", "")
            if cls.ref_is_commit(ref)
            else (url.removesuffix(".git").rsplit("/", 1)[0], ref)
        )
        return r[t.Pair[str, str]].ok(line)

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
            FlextInfraUtilitiesGitWorktreeDiscoveryMixin.git_submodule_declarations(
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
            metadata = FlextInfraUtilitiesPyproject.read_project_metadata_result(
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
            FlextInfraUtilitiesGitWorktreeDiscoveryMixin.git_remote_identity(
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
                base_url=url.removesuffix(".git").rsplit("/", 1)[0],
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
            FlextInfraUtilitiesGitWorktreeDiscoveryMixin.git_remote_identity(
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
        primary_root = identity.primary_root
        if not primary_root.is_relative_to(superproject_root):
            error = ValueError(
                f"submodule identity escapes its superproject: {primary_root}",
            )
            return r[str].fail(str(error), exception=error)
        contract = FlextInfraUtilitiesGit.git_submodule_declaration(
            m.Infra.GitSubmoduleContractRequest(
                repo_root=superproject_root,
                member_path=primary_root.relative_to(superproject_root).as_posix(),
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
            "integration branch must be published by Git: "
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
        this check reads the live remote-tracking ref for exactly that line.
        A repository that does not publish it has no integration baseline and
        fails loud — there is no name list to guess from and no default to
        invent.

        Returns:
            The declared integration branch the repository publishes.

        """
        reference = f"refs/remotes/origin/{declared_branch}"
        resolved = FlextInfraUtilitiesGitSemanticPublishMixin.git_ref_exists(
            m.Infra.GitRefRequest(repo_root=repository_root, reference=reference),
        )
        if resolved.success and resolved.value.value:
            return r[str].ok(declared_branch)
        return r[str].fail(
            "repository publishes no integration branch "
            f"(declared {declared_branch}): {repository_root}",
        )


__all__: t.VariadicTuple[str] = ("FlextInfraUtilitiesRepository",)
