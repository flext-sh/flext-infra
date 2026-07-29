"""Repository-local workspace manifests are the sole consumer authority."""

from __future__ import annotations

from pathlib import Path

from flext_infra import c, m
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_tests import tm


def _repository(
    name: str,
    *,
    path: str,
    role: c.Infra.RepositoryRole,
    state: c.Infra.RepositoryState = c.Infra.RepositoryState.ACTIVE,
) -> m.Infra.RepositoryRef:
    profile = (
        c.Infra.MakeProfile.WORKSPACE_ROOT
        if role is c.Infra.RepositoryRole.WORKSPACE_ROOT
        else c.Infra.MakeProfile.WORKSPACE_MEMBER
    )
    return m.Infra.RepositoryRef(
        name=name,
        distribution=name,
        provider="acme-hosting",
        url=f"https://github.com/acme-hosting/{name}.git",
        branch="development",
        path=Path(path),
        role=role,
        state=state,
        profile=profile,
        checkout=(
            c.Infra.CheckoutKind.ROOT
            if role is c.Infra.RepositoryRole.WORKSPACE_ROOT
            else c.Infra.CheckoutKind.SUBMODULE
        ),
        codegen=(
            c.Infra.CodegenKind.NONE
            if role is c.Infra.RepositoryRole.CONTENT_ONLY
            else c.Infra.CodegenKind.CONFORM
        ),
        package=role is c.Infra.RepositoryRole.WORKSPACE_MEMBER,
        editable=role is c.Infra.RepositoryRole.WORKSPACE_MEMBER,
        read_only=role is c.Infra.RepositoryRole.CONTENT_ONLY,
    )


class TestsCodegenCatalogExtensions:
    def test_conform_has_no_global_workspace_catalog_validator(self) -> None:
        tm.that(
            hasattr(FlextInfraCodegenConform, "_validate_workspace_catalog"), eq=False
        )

    def test_local_manifest_conforms_without_global_repository_rows(
        self, tmp_path: Path
    ) -> None:
        root = _repository(
            "acme-platform", path=".", role=c.Infra.RepositoryRole.WORKSPACE_ROOT
        ).model_copy(
            update={
                "extra_verbs": (
                    m.Infra.MakeVerbSpec(name="audit", default_what="all"),
                ),
                "script_dispatch": m.Infra.ScriptDispatchSpec(
                    dispatcher="scripts/dispatch.py", roots=("scripts",)
                ),
            }
        )
        workspace = m.Infra.WorkspaceSpec(
            version=c.Infra.WORKSPACE_MANIFEST_VERSION,
            name=root.name,
            repository=root,
            project=m.Infra.ProjectSpec(
                package_name="acme_platform",
                class_stem="AcmePlatform",
                namespace="AcmePlatform",
                constant_name="acme-platform",
                namespace_attribute="acme_platform",
                alias="acme",
                environment_prefix="ACME_PLATFORM_",
                description="Product-neutral platform fixture",
                version="0.1.0",
                license="MIT",
                author_name="Acme Team",
                author_email="engineering@example.com",
                upstream="flext_core",
                homepage="https://example.com/acme-platform",
                documentation="https://example.com/acme-platform/docs",
                workspace_root_rel=".",
                year=2026,
            ),
            members=(
                _repository(
                    "acme-charts",
                    path="acme-charts",
                    role=c.Infra.RepositoryRole.WORKSPACE_MEMBER,
                ),
            ),
            content_only=(
                _repository(
                    "acme-content",
                    path="acme-content",
                    role=c.Infra.RepositoryRole.CONTENT_ONLY,
                    state=c.Infra.RepositoryState.CONTENT_ONLY,
                ),
            ),
        )

        result = FlextInfraCodegenConform(initial_workspace=workspace).plan(
            m.Infra.CodegenConformRequest(
                root=tmp_path,
                what=c.Infra.CodegenConformSurface.MAKEFILE,
                scope=c.Infra.CodegenConformScope.SELF,
                mode=c.Infra.CodegenConformMode.CHECK,
            )
        )

        plan = tm.ok(result)
        tm.that(tuple(item.name for item in plan.repositories), eq=(root.name,))


__all__: tuple[str, ...] = ()
