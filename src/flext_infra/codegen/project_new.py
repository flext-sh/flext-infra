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
from flext_infra.codegen.publisher import FlextInfraCodegenPublisher
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector

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
    repository_url: Annotated[
        str, m.Field(description="Canonical Git clone URL for the new repository.")
    ] = ""
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

    @staticmethod
    def _with_workspace_registration(
        planner: FlextInfraCodegenConform,
        plan: m.Infra.CodegenPlan,
        workspace_root: Path,
        rendered_manifest: str | None,
    ) -> p.Result[m.Infra.CodegenPlan]:
        """Include the handwritten parent-manifest update in one publication plan."""
        if rendered_manifest is None:
            return r[m.Infra.CodegenPlan].ok(plan)
        relative_path = Path(
            c.CONFIG_DIR_NAME, c.Infra.WORKSPACE_MANIFEST_FILENAME
        ).as_posix()
        manifest_plan = planner.plan_managed_file(
            workspace_root, relative_path, rendered_manifest
        )
        if manifest_plan.failure:
            return r[m.Infra.CodegenPlan].fail(
                manifest_plan.error or "workspace member registration planning failed"
            )
        registered_file = manifest_plan.value
        if any(item.path == registered_file.path for item in plan.files):
            return r[m.Infra.CodegenPlan].fail(
                f"workspace registration path is already planned: {registered_file.path}"
            )
        return r[m.Infra.CodegenPlan].ok(
            plan.model_copy(update={"files": (*plan.files, registered_file)})
        )

    @override
    def execute(self) -> p.Result[m.Infra.CodegenResult]:
        """Build one typed manifest and delegate all output to conform."""
        if self.effective_dry_run:
            return r[m.Infra.CodegenResult].fail("codegen new requires apply mode")
        provider = next(
            (
                item
                for item in config.Infra.codegen.providers
                if item.name == self.provider
            ),
            None,
        )
        # The URL comes from the caller or is derived from the provider
        # contract. flext-infra keeps no catalog of existing projects to
        # consult, so scaffolding a new project needs no prior knowledge of it.
        package_name = self.package_name or self.name.replace("-", "_")
        class_stem = u.derive_class_stem(self.name)
        derived_namespace = class_stem.removeprefix("Flext")
        project_namespace = self.project_namespace or derived_namespace or class_stem
        alias = u.Infra.package_alias(package_name=package_name)
        provider_url = (
            f"{provider.base_url}/{self.name}.git" if provider is not None else ""
        )
        repository_url = self.repository_url or provider_url
        if not repository_url:
            return r[m.Infra.CodegenResult].fail(
                f"repository URL is required for provider: {self.provider}"
            )
        if provider is None:
            return r[m.Infra.CodegenResult].fail(
                f"repository branch is required for provider: {self.provider}"
            )
        repository_page = repository_url.removesuffix(".git")
        project = m.Infra.ProjectSpec(
            package_name=package_name,
            class_stem=class_stem,
            namespace=project_namespace,
            constant_name=self.name,
            namespace_attribute=alias,
            alias=alias,
            environment_prefix=f"{package_name.upper()}_",
            description=(
                self.description or f"{class_stem} — FLEXT typed integration package"
            ),
            version=self.version,
            license=self.license,
            author_name=self.author_name,
            author_email=self.author_email,
            upstream=self.upstream,
            homepage=repository_page,
            documentation=repository_page,
            year=self.year,
        )
        root = self.output_root.expanduser().resolve()
        workspace_root = root
        rendered_manifest: str | None = None
        if self.kind is c.Infra.ProjectKind.INTERNAL:
            workspace_root = self.workspace_root.expanduser().resolve()
            try:
                repository_path = root.relative_to(workspace_root)
            except ValueError as exc:
                return r[m.Infra.CodegenResult].fail_op(
                    "internal project workspace relation", exc
                )
            if repository_path == Path():
                return r[m.Infra.CodegenResult].fail(
                    "internal project root must be below its workspace root"
                )
            repository = m.Infra.RepositoryRef(
                name=self.name,
                distribution=self.name,
                provider=self.provider,
                branch=provider.branch,
                url=repository_url,
                path=repository_path,
                role=c.Infra.RepositoryRole.WORKSPACE_MEMBER,
                state=c.Infra.RepositoryState.ACTIVE,
                checkout=c.Infra.CheckoutKind.SUBMODULE,
                codegen=c.Infra.CodegenKind.CONFORM,
                package=True,
                editable=True,
                read_only=False,
            )
            registration = u.Infra.workspace_register_member(workspace_root, repository)
            if registration.failure:
                return r[m.Infra.CodegenResult].fail(
                    registration.error or "workspace member registration failed"
                )
            parent_workspace, rendered_manifest = registration.value
            physical = FlextInfraWorkspaceDetector.validate_registered_member(
                root, workspace_root, parent_workspace
            )
            if physical.failure:
                return r[m.Infra.CodegenResult].fail(
                    physical.error
                    or "internal project must be a registered Git submodule"
                )
            if physical.value is not c.Infra.WorkspaceMode.WORKSPACE_MEMBER:
                return r[m.Infra.CodegenResult].fail(
                    "internal project is not a governed workspace member"
                )
            workspace = parent_workspace.model_copy(update={"project": project})
        else:
            repository = m.Infra.RepositoryRef(
                name=self.name,
                distribution=self.name,
                provider=self.provider,
                branch=provider.branch,
                url=repository_url,
                path=Path(),
                role=c.Infra.RepositoryRole.STANDALONE,
                state=c.Infra.RepositoryState.ACTIVE,
                checkout=c.Infra.CheckoutKind.INDEPENDENT,
                codegen=c.Infra.CodegenKind.CONFORM,
                package=True,
                editable=False,
                read_only=False,
            )
            workspace = m.Infra.WorkspaceSpec(
                version=c.Infra.WORKSPACE_MANIFEST_VERSION,
                name=self.name,
                repository=repository,
                project=project,
            )
        request = m.Infra.CodegenConformRequest(
            root=root, scope=c.Infra.CodegenConformScope.SELF
        )
        planner = FlextInfraCodegenConform(
            workspace_root=request.root,
            initial_workspace=workspace,
            initial_workspace_root=workspace_root,
            projection_operation="scaffold",
        )
        planned = planner.plan(request)
        if planned.failure:
            return r[m.Infra.CodegenResult].fail(
                planned.error or "project scaffold planning failed"
            )
        complete_plan = self._with_workspace_registration(
            planner, planned.value, workspace_root, rendered_manifest
        )
        if complete_plan.failure:
            return r[m.Infra.CodegenResult].fail(
                complete_plan.error or "project scaffold plan is incomplete"
            )
        valid = planner.validate_plan(complete_plan.value, allow_missing_beads=True)
        if valid.failure:
            return r[m.Infra.CodegenResult].fail(
                valid.error or "project scaffold validation failed"
            )
        published = FlextInfraCodegenPublisher.apply(complete_plan.value)
        if published.failure:
            return r[m.Infra.CodegenResult].fail(
                published.error or "project scaffold publication failed"
            )
        verified = planner.plan(request)
        if verified.failure:
            return r[m.Infra.CodegenResult].fail(
                verified.error or "project scaffold verification failed"
            )
        verified_plan = self._with_workspace_registration(
            planner, verified.value, workspace_root, rendered_manifest
        )
        if verified_plan.failure:
            return r[m.Infra.CodegenResult].fail(
                verified_plan.error or "project scaffold verification is incomplete"
            )
        if self.kind is c.Infra.ProjectKind.INTERNAL:
            target = u.Infra.repository_conform_target(root)
            if target.failure:
                return r[m.Infra.CodegenResult].fail(
                    target.error or "generated workspace member is not attached"
                )
            if target.value.make_profile is not c.Infra.MakeProfile.WORKSPACE_MEMBER:
                return r[m.Infra.CodegenResult].fail(
                    "generated internal project did not resolve as a workspace member"
                )
        residual = tuple(item for item in verified_plan.value.files if item.changed)
        if residual:
            paths = ", ".join(str(item.path) for item in residual)
            return r[m.Infra.CodegenResult].fail(
                f"project scaffold did not reach a fixed point: {paths}"
            )
        return r[m.Infra.CodegenResult].ok(
            m.Infra.CodegenResult(
                plan=verified_plan.value, written_files=published.value
            )
        )


__all__: list[str] = ["FlextInfraCodegenProjectNew"]
