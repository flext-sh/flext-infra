"""``codegen new`` — create a project through the canonical conform pipeline.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

# NOTE (multi-agent, mro-wkii.14 / agent: codegen): new file per operator live
# order (ULW). ctx via u.derive_class_stem (no parallel detection, ADR-005 §9);
# accessor typing/config+settings symmetry fixed in templates in the same lane.
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Annotated, override

from flext_core import r
from flext_infra import c, config, m, u
from flext_infra.base import s
from flext_infra.codegen.conform import FlextInfraCodegenConform

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraCodegenProjectNew(s[m.Infra.CodegenResult]):
    """Create a new FLEXT project (internal member or external standalone)."""

    name: Annotated[
        str,
        m.Field(
            min_length=1,
            description="Distribution name in kebab-case (e.g. flext-demo / acme-demo).",
        ),
    ]
    kind: Annotated[
        c.Infra.ProjectKind,
        m.Field(description="Project kind: internal (monorepo member) or external."),
    ]
    output_root: Annotated[
        Path, m.Field(description="Directory that becomes the generated project root.")
    ]
    package_name: Annotated[
        str, m.Field(description="Python package name (default: name with '-'→'_').")
    ] = ""
    # NOTE (multi-agent, mro-wkii.14 / agent: codegen): field renamed
    # ``namespace``→``project_namespace`` to avoid colliding with the inherited
    # base field ``target_namespace`` (alias ``namespace``); CLI flag stays ``--ns``.
    project_namespace: Annotated[
        str,
        m.Field(
            alias="ns",
            description="Facade namespace slot (default: class stem minus 'Flext').",
        ),
    ] = ""
    description: Annotated[
        str, m.Field(default="", description="Project description (default: derived).")
    ] = ""
    # NOTE (multi-agent, mro-wkii.4.15 / agent: codex): project config owns the
    # already-validated version value consumed directly by project generation.
    version: Annotated[
        str,
        m.Field(description="Initial project version (default: config.Infra.version)."),
    ] = config.Infra.version
    provider: Annotated[
        str, m.Field(min_length=1, description="Configured Git provider key.")
    ]
    license: Annotated[
        str, m.Field(min_length=1, description="SPDX project license identifier.")
    ]
    author_name: Annotated[
        str, m.Field(min_length=1, description="Author/maintainer display name.")
    ]
    author_email: Annotated[
        str, m.Field(min_length=3, description="Author/maintainer email.")
    ]
    upstream: Annotated[str, m.Field(description="Upstream facade module (flext_cli).")]
    year: Annotated[int, m.Field(ge=2025, description="Deterministic copyright year.")]

    @override
    def execute(self) -> p.Result[m.Infra.CodegenResult]:
        """Build one typed manifest and delegate all output to conform."""
        if self.effective_dry_run:
            return r[m.Infra.CodegenResult].fail("codegen new requires apply mode")
        kind = c.Infra.ProjectKind(self.kind)
        profile = (
            c.Infra.MakeProfile.WORKSPACE_MEMBER
            if kind is c.Infra.ProjectKind.INTERNAL
            else c.Infra.MakeProfile.STANDALONE
        )
        role = (
            c.Infra.RepositoryRole.WORKSPACE_MEMBER
            if kind is c.Infra.ProjectKind.INTERNAL
            else c.Infra.RepositoryRole.STANDALONE
        )
        provider = next(
            (
                item
                for item in config.Infra.codegen.providers
                if item.name == self.provider
            ),
            None,
        )
        if provider is None:
            return r[m.Infra.CodegenResult].fail(
                f"unknown codegen repository provider: {self.provider}"
            )
        known = next(
            (
                item
                for item in config.Infra.codegen.repositories
                if item.name == self.name
            ),
            None,
        )
        if known is not None and known.provider != provider.name:
            return r[m.Infra.CodegenResult].fail(
                f"repository provider differs from catalog: {self.name}"
            )
        package_name = self.package_name or self.name.replace("-", "_")
        class_stem = u.derive_class_stem(self.name)
        derived_namespace = class_stem.removeprefix("Flext")
        project_namespace = self.project_namespace or derived_namespace or class_stem
        alias = u.Infra.package_alias(package_name=package_name)
        repository_url = (
            known.url if known is not None else f"{provider.base_url}/{self.name}.git"
        )
        repository_branch = known.branch if known is not None else provider.branch
        repository_page = repository_url.removesuffix(".git")
        repository = m.Infra.RepositoryRef(
            name=self.name,
            distribution=known.distribution if known is not None else self.name,
            provider=provider.name,
            url=repository_url,
            branch=repository_branch,
            path=Path(),
            role=role,
            state=c.Infra.RepositoryState.ACTIVE,
            profile=profile,
            checkout=(
                c.Infra.CheckoutKind.SUBMODULE
                if kind is c.Infra.ProjectKind.INTERNAL
                else c.Infra.CheckoutKind.INDEPENDENT
            ),
            codegen=c.Infra.CodegenKind.CONFORM,
            package=True,
            editable=kind is c.Infra.ProjectKind.INTERNAL,
            read_only=False,
        )
        workspace = m.Infra.WorkspaceSpec(
            version=c.Infra.WORKSPACE_MANIFEST_VERSION,
            name=self.name,
            repository=repository,
            project=m.Infra.ProjectSpec(
                package_name=package_name,
                class_stem=class_stem,
                namespace=project_namespace,
                constant_name=self.name,
                namespace_attribute=alias,
                alias=alias,
                environment_prefix=f"{package_name.upper()}_",
                description=(
                    self.description
                    or f"{class_stem} — FLEXT typed integration package"
                ),
                version=self.version,
                license=self.license,
                author_name=self.author_name,
                author_email=self.author_email,
                upstream=self.upstream,
                homepage=repository_page,
                documentation=repository_page,
                workspace_root_rel=(
                    ".." if profile is c.Infra.MakeProfile.WORKSPACE_MEMBER else "."
                ),
                year=self.year,
            ),
        )
        request = m.Infra.CodegenConformRequest(
            root=self.output_root.expanduser().resolve(),
            scope=c.Infra.CodegenConformScope.SELF,
            mode=c.Infra.CodegenConformMode.APPLY,
        )
        return FlextInfraCodegenConform.execute_request(
            request, initial_workspace=workspace
        )


__all__: list[str] = ["FlextInfraCodegenProjectNew"]
