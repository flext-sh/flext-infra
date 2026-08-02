"""Unified, fail-closed conformance for new and existing repositories.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import hashlib
import os
import re
from fnmatch import fnmatchcase
from pathlib import Path
from typing import Annotated, Literal, override

from flext_infra import c, config, m, p, r, s, t, u
from flext_infra.deps.modernizer import FlextInfraPyprojectModernizer
from flext_infra.services.codegen import FlextInfraCodegen
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector

_GITMODULE_SECTION_RE = re.compile(r'(?m)^\[submodule "[^"]+"\]\s*$')
_GITMODULE_PATH_RE = re.compile(r"(?m)^[ \t]*path[ \t]*=[ \t]*(.+?)[ \t]*$")


class FlextInfraCodegenConform(s[m.Infra.CodegenResult]):
    """Plan every selected output, then atomically write only a clean plan."""

    class SurfaceContract(m.Value):
        """Typed ownership contract for one requested conformance surface."""

        surface: c.Infra.CodegenConformSurface = m.Field(
            description="Config-declared template surface selected for planning"
        )
        complete_governed: bool = m.Field(
            default=False, description="Whether every governed output is represented"
        )
        dependencies_only: bool = m.Field(
            default=False, description="Whether planning is dependency-only"
        )
        delegates: bool = m.Field(
            default=True, description="Whether delegated templates are planned"
        )
        pyproject: bool = m.Field(
            default=True, description="Whether project metadata is planned"
        )
        templates: bool = m.Field(
            default=True, description="Whether managed templates are planned"
        )

    @classmethod
    def _surface_contract(
        cls, surface: c.Infra.CodegenConformSurface
    ) -> SurfaceContract:
        match surface:
            case c.Infra.CodegenConformSurface.ALL:
                return cls.SurfaceContract(surface=surface, complete_governed=True)
            case c.Infra.CodegenConformSurface.DEPENDENCIES:
                return cls.SurfaceContract(
                    surface=surface,
                    dependencies_only=True,
                    delegates=False,
                    templates=False,
                )
            case c.Infra.CodegenConformSurface.PYPROJECT:
                return cls.SurfaceContract(
                    surface=surface, delegates=False, templates=False
                )
            case c.Infra.CodegenConformSurface.GITMODULES:
                return cls.SurfaceContract(surface=surface, pyproject=False)
            case _:
                msg = f"Unsupported codegen conform surface: {surface}"
                raise ValueError(msg)

    # NOTE (multi-agent, mro-wkii.17 / agent: codex): this is the only
    # orchestrator for Make/toolchain/source conformance. Rendering stays in
    # flext-cli; Git-source TOML policy and attached detection are composed from
    # their separately owned u.Infra/workspace services.
    request: Annotated[
        m.Infra.CodegenConformRequest | None,
        m.Field(default=None, exclude=True, description="Validated conform request"),
    ] = None
    initial_workspace: Annotated[
        m.Infra.WorkspaceSpec | None,
        m.Field(
            default=None,
            exclude=True,
            description="Validated initial manifest included in the atomic plan",
        ),
    ] = None
    initial_workspace_root: Annotated[
        Path | None,
        m.Field(
            default=None,
            exclude=True,
            description="Manifest-owner root for an initial attached project",
        ),
    ] = None
    initial_execution_context: Annotated[
        m.Infra.MakeExecutionContext | None,
        m.Field(
            default=None,
            exclude=True,
            description="Already normalized Make topology and repository selection",
        ),
    ] = None
    projection_operation: Annotated[
        Literal["scaffold", "conform", "generate"],
        m.Field(
            default="conform",
            exclude=True,
            description="Config-selected projection operation",
        ),
    ] = "conform"

    @classmethod
    def execute_request(
        cls,
        request: m.Infra.CodegenConformRequest,
        initial_workspace: m.Infra.WorkspaceSpec | None = None,
    ) -> p.Result[m.Infra.CodegenResult]:
        """Execute one already validated public CLI request."""
        service = cls(
            workspace_root=request.root.expanduser().resolve(),
            request=request,
            initial_workspace=initial_workspace,
        )
        return service.execute()

    @override
    def execute(self) -> p.Result[m.Infra.CodegenResult]:
        """Calculate and verify drift without mutating the selected repositories."""
        request = self.request or m.Infra.CodegenConformRequest(
            root=self.workspace_root
        )
        planned = self.plan(request)
        if planned.failure:
            return r[m.Infra.CodegenResult].fail(
                planned.error or "codegen conform planning failed"
            )
        plan = planned.value
        valid = self.validate_plan(plan, allow_missing_beads=False)
        if valid.failure:
            return r[m.Infra.CodegenResult].fail(
                valid.error or "codegen conform validation failed"
            )
        changed = tuple(file for file in plan.files if file.changed)
        if changed:
            paths = ", ".join(str(file.path) for file in changed)
            return r[m.Infra.CodegenResult].fail(f"codegen drift detected: {paths}")
        return r[m.Infra.CodegenResult].ok(m.Infra.CodegenResult(plan=plan))

    def validate_plan(
        self, plan: m.Infra.CodegenPlan, *, allow_missing_beads: bool
    ) -> p.Result[bool]:
        """Validate one calculated plan without applying any file mutation."""
        blocked = tuple(file for file in plan.files if file.blocked)
        if blocked:
            details = "; ".join(
                f"{file.path}: {file.reason or 'managed WIP'}" for file in blocked
            )
            return r[bool].fail(f"codegen conform blocked before writes: {details}")
        ancestry_violations = tuple(
            (ancestry, reference)
            for ancestry in plan.branch_ancestry
            for reference in ancestry.references
            if reference.ancestor is False
        )
        if ancestry_violations:
            details = "; ".join(
                (
                    f"{reference.reference}@{reference.sha} does not descend from "
                    f"{ancestry.baseline_reference}@{ancestry.baseline_sha}"
                )
                for ancestry, reference in ancestry_violations
            )
            return r[bool].fail(f"governed branch ancestry violations: {details}")
        for beads_plan in plan.beads:
            beads_preflight = self.verify_beads_plan(
                beads_plan, allow_missing=allow_missing_beads
            )
            if beads_preflight.failure:
                return r[bool].fail(
                    beads_preflight.error or "Beads lifecycle preflight failed"
                )
        return r[bool].ok(True)

    def plan(
        self, request: m.Infra.CodegenConformRequest
    ) -> p.Result[m.Infra.CodegenPlan]:
        """Build and validate the complete selection without writing."""
        config_spec = config.Infra.codegen
        root = request.root.expanduser().resolve()
        workspace_root = (self.initial_workspace_root or root).expanduser().resolve()
        workspace = self.initial_workspace
        execution_context = self.initial_execution_context
        if execution_context is not None:
            if root != execution_context.target.root.resolve():
                return r[m.Infra.CodegenPlan].fail(
                    "generation root differs from the normalized Make target"
                )
            workspace_root = execution_context.workspace_root.resolve()
            workspace = execution_context.workspace
        elif workspace is None:
            workspace_root_result = FlextInfraWorkspaceDetector.resolve_workspace_root(
                root
            )
            if workspace_root_result.failure:
                return r[m.Infra.CodegenPlan].fail(
                    workspace_root_result.error or "workspace root resolution failed"
                )
            workspace_root = workspace_root_result.value
            workspace_result = FlextInfraWorkspaceDetector.load_workspace_spec(
                workspace_root
            )
            if workspace_result.failure:
                return r[m.Infra.CodegenPlan].fail(
                    workspace_result.error or "workspace manifest load failed"
                )
            workspace = workspace_result.value
        current_repository = (
            execution_context.target.repository
            if execution_context is not None
            else workspace.repository
        )
        if root != workspace_root:
            try:
                current_path = root.relative_to(workspace_root).as_posix()
            except ValueError as exc:
                return r[m.Infra.CodegenPlan].fail_op(
                    "repository workspace resolution", exc
                )
            current_matches = tuple(
                repository
                for repository in workspace.members
                if repository.path.as_posix() == current_path
            )
            if len(current_matches) != 1:
                return r[m.Infra.CodegenPlan].fail(
                    f"repository is not one declared workspace member: {current_path}"
                )
            current_repository = current_matches[0]
        if execution_context is not None:
            current_target = execution_context.target
        elif self.initial_workspace is None:
            current_target_result = FlextInfraWorkspaceDetector.conform_target(
                root, workspace
            )
            if current_target_result.failure:
                return r[m.Infra.CodegenPlan].fail(
                    current_target_result.error
                    or "repository conformance target resolution failed"
                )
            current_target = current_target_result.value
            current_repository = current_target.repository
        else:
            baseline_branch_result = u.Infra.repository_baseline_branch(
                root, declared_branch=current_repository.branch
            )
            if baseline_branch_result.failure:
                return r[m.Infra.CodegenPlan].fail(
                    baseline_branch_result.error
                    or f"integration baseline resolution failed: {root}"
                )
            current_repository_role = current_repository.role
            profile_by_role = {
                c.Infra.RepositoryRole.WORKSPACE_ROOT: (
                    c.Infra.MakeProfile.WORKSPACE_ROOT
                ),
                c.Infra.RepositoryRole.WORKSPACE_MEMBER: (
                    c.Infra.MakeProfile.WORKSPACE_MEMBER
                ),
                c.Infra.RepositoryRole.STANDALONE: c.Infra.MakeProfile.STANDALONE,
            }
            current_make_profile = profile_by_role.get(current_repository_role)
            if current_make_profile is None:
                return r[m.Infra.CodegenPlan].fail(
                    "initial repository role cannot receive conformance: "
                    f"{current_repository_role.value}"
                )
            current_target = m.Infra.RepositoryConformTarget(
                repository=current_repository,
                root=root,
                make_profile=current_make_profile,
                beads_enabled=(
                    current_make_profile == c.Infra.MakeProfile.WORKSPACE_ROOT
                ),
                routing_only=False,
                canonical_project_name=current_repository.distribution,
                baseline_branch=baseline_branch_result.value,
                ci_enabled=True,
                external_dependency_paths=workspace.external_dependency_paths,
                technical_branch_patterns=(
                    config_spec.branch_policy.technical_branch_patterns
                ),
                governed_branch_patterns=(config_spec.governed_branch_patterns),
            )
        if execution_context is not None:
            selected = tuple(item.repository for item in execution_context.targets)
        else:
            selected_result = self._select_repositories(
                request, workspace, current_repository
            )
            if selected_result.failure:
                return r[m.Infra.CodegenPlan].fail(
                    selected_result.error or "repository selection failed"
                )
            selected = selected_result.value
        contract = self._surface_contract(c.Infra.CodegenConformSurface(request.what))
        ledger_root_result = self._beads_ledger_root(workspace_root)
        if ledger_root_result.failure:
            return r[m.Infra.CodegenPlan].fail(
                ledger_root_result.error or "Beads ledger root resolution failed"
            )
        principal_root = ledger_root_result.value
        files: list[m.Infra.CodegenFilePlan] = []
        beads_plans: list[m.Infra.BeadsPlan] = []
        ancestry_plans: list[m.Infra.BranchAncestryPlan] = []
        for repository in selected:
            repository_root = self._repository_root(
                workspace_root, workspace, repository
            )
            if repository_root.exists() and not repository_root.is_dir():
                return r[m.Infra.CodegenPlan].fail(
                    f"declared repository path is not a directory: {repository_root}"
                )
            if not repository_root.is_dir() and self.initial_workspace is None:
                return r[m.Infra.CodegenPlan].fail(
                    f"declared repository checkout is missing: {repository_root}"
                )
            if repository.name == current_target.repository.name:
                target = current_target
            else:
                target_result = FlextInfraWorkspaceDetector.conform_target(
                    repository_root, workspace
                )
                if target_result.failure:
                    return r[m.Infra.CodegenPlan].fail(
                        target_result.error
                        or f"repository target resolution failed: {repository_root}"
                    )
                target = target_result.value
            # NOTE (multi-agent, mro-45r9): attached members consume the parent
            # topology SSOT; a duplicate member-local manifest is never required.
            # mro-j47u (codex): existing repositories cannot reach the scaffold
            # catalog. Project creation is the only template-rendering lifecycle.
            if (
                self.initial_workspace is not None
                and repository.name == current_target.repository.name
            ):
                repository_plan = self._plan_scaffold_repository(
                    root=repository_root,
                    repository=repository,
                    target=target,
                    workspace=workspace,
                    codegen=config_spec,
                    contract=contract,
                )
            else:
                repository_plan = self._plan_existing_repository(
                    root=repository_root,
                    workspace_root=workspace_root,
                    repository=repository,
                    target=target,
                    workspace=workspace,
                    codegen=config_spec,
                    contract=contract,
                )
            if repository_plan.failure:
                return r[m.Infra.CodegenPlan].fail(
                    repository_plan.error
                    or f"repository planning failed: {repository_root}"
                )
            governed = self._complete_governed_plans(
                repository_root,
                repository_plan.value,
                config_spec,
                contract,
                target=target,
                workspace=workspace,
            )
            if governed.failure:
                return r[m.Infra.CodegenPlan].fail(
                    governed.error
                    or f"artifact ownership planning failed: {repository_root}"
                )
            files.extend(governed.value)
            prefix_result = self.declared_beads_prefix(
                target.root, default_prefix=target.canonical_project_name
            )
            if prefix_result.failure:
                return r[m.Infra.CodegenPlan].fail(
                    prefix_result.error
                    or f"Beads tracker declaration failed: {target.root}"
                )
            beads_plans.append(
                m.Infra.BeadsPlan(
                    repository_root=repository_root,
                    enabled=target.beads_enabled,
                    canonical_prefix=prefix_result.value,
                    expected_version=config_spec.toolchain.beads.reported_version,
                    expected_checksum=config_spec.toolchain.beads.checksum,
                    expected_schema=config_spec.toolchain.beads.expected_schema,
                    ledger_root=principal_root,
                    ledger_id=workspace.ledger_id,
                )
            )
            if self.initial_workspace is None:
                ancestry_result = self._branch_ancestry_plan(target)
                if ancestry_result.failure:
                    return r[m.Infra.CodegenPlan].fail(
                        ancestry_result.error
                        or f"branch ancestry inventory failed: {repository_root}"
                    )
                ancestry_plans.append(ancestry_result.value)
        return r[m.Infra.CodegenPlan].ok(
            m.Infra.CodegenPlan(
                request=request,
                repositories=selected,
                workspace=workspace,
                beads=tuple(beads_plans),
                branch_ancestry=tuple(ancestry_plans),
                files=tuple(files),
            )
        )

    @staticmethod
    def _surface_relative_path(
        entry: m.Infra.ManagedSurfaceSpec, workspace: m.Infra.WorkspaceSpec | None
    ) -> p.Result[Path]:
        """Resolve one catalog path from the typed project identity."""
        project = workspace.project if workspace is not None else None
        values = {
            "package_name": project.package_name if project is not None else "",
            "ns": project.namespace if project is not None else "",
        }
        try:
            rendered = entry.path.format(**values)
        except (KeyError, ValueError) as exc:
            return r[Path].fail_op(f"surface path resolution: {entry.path}", exc)
        relative = Path(rendered)
        if relative.is_absolute() or relative == Path() or ".." in relative.parts:
            return r[Path].fail(f"surface path escapes repository root: {rendered}")
        return r[Path].ok(relative)

    def _complete_governed_plans(
        self,
        root: Path,
        planned: t.SequenceOf[m.Infra.CodegenFilePlan],
        codegen: m.Infra.CodegenConfigSpec,
        contract: SurfaceContract,
        *,
        target: m.Infra.RepositoryConformTarget,
        workspace: m.Infra.WorkspaceSpec | None = None,
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Attach ownership metadata and represent every governed root artifact.

        Only the ``ALL`` surface completes the full governed set; the
        pyproject-scoped surfaces (``DEPENDENCIES``/``PYPROJECT``) keep the plan
        restricted to what their own planners already produced.
        """
        governed_by_path: dict[Path, m.Infra.ManagedSurfaceSpec] = {}
        for item in codegen.surfaces.entries:
            target_allows_entry = (
                target.make_profile in item.profiles
                and (not item.requires_ci or target.ci_enabled)
                and (
                    not item.requires_beads
                    or target.beads_enabled
                    or target.routing_only
                )
            )
            if not target_allows_entry or not self._entry_matches_surface(
                item, contract
            ):
                continue
            relative_result = self._surface_relative_path(item, workspace)
            if relative_result.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    relative_result.error
                    or f"surface path resolution failed: {item.path}"
                )
            relative = relative_result.value
            if relative in governed_by_path:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    f"surface paths collide after rendering: {relative}"
                )
            governed_by_path[relative] = item
        completed: list[m.Infra.CodegenFilePlan] = []
        represented: set[Path] = set()
        for file in planned:
            relative = file.path.relative_to(root)
            governed = governed_by_path.get(relative)
            if governed is None:
                completed.append(file)
                continue
            represented.add(relative)
            completed.append(
                file.model_copy(
                    update={"owner": governed.owner, "policy": governed.policy}
                )
            )
        if not contract.complete_governed:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(tuple(completed))
        for relative, governed in governed_by_path.items():
            if relative in represented:
                continue
            path = root / relative
            if path.exists() and not path.is_file():
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    f"governed artifact is not a regular file: {path}"
                )
            current = ""
            if path.is_file():
                read = u.Cli.files_read_text(path)
                if read.failure:
                    return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                        read.error or f"governed artifact read failed: {path}"
                    )
                current = read.value
            digest = u.Cli.sha256_content(current) if path.is_file() else ""
            if governed.policy == "merge" and governed.delegate == "vscode-settings":
                # Owner-merge dispatch: owners with a canonical document merge
                # (vscode settings today) produce their rendered content here.
                merged = FlextInfraCodegen.render_vscode_settings(root)
                if merged.failure:
                    return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                        merged.error or f"vscode settings merge failed: {path}"
                    )
                if merged.value != current:
                    completed.append(
                        m.Infra.CodegenFilePlan(
                            path=path,
                            owner=governed.owner,
                            policy=governed.policy,
                            rendered=merged.value,
                            expected_sha256=u.Cli.sha256_content(merged.value),
                            current_sha256=digest,
                            changed=True,
                        )
                    )
                    continue
            if governed.policy == "merge" and relative.as_posix() == c.Infra.GITIGNORE:
                # NOTE (mro-jnm1.2): the canonical .gitignore body is rendered
                # from the same base/gitignore.j2 + computed
                # CodegenConfigSpec.gitignore_sections used by `codegen new` —
                # ONE render mechanism derived from the artifact SSOT.
                # Per-project exception fields land with mro-jnm1.3.
                rendered_gitignore = FlextInfraCodegenConform._render_gitignore(
                    codegen,
                    profile=target.make_profile,
                    project_name=target.canonical_project_name,
                    workspace=workspace,
                )
                if rendered_gitignore.failure:
                    return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                        rendered_gitignore.error or f"gitignore render failed: {path}"
                    )
                if rendered_gitignore.value != current:
                    completed.append(
                        m.Infra.CodegenFilePlan(
                            path=path,
                            owner=governed.owner,
                            policy=governed.policy,
                            rendered=rendered_gitignore.value,
                            expected_sha256=u.Cli.sha256_content(
                                rendered_gitignore.value
                            ),
                            current_sha256=digest,
                            changed=True,
                        )
                    )
                    continue
            completed.append(
                m.Infra.CodegenFilePlan(
                    path=path,
                    owner=governed.owner,
                    policy=governed.policy,
                    rendered=current,
                    expected_sha256=digest or u.Cli.sha256_content(current),
                    current_sha256=digest,
                    changed=False,
                )
            )
        return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(tuple(completed))

    @staticmethod
    def _package_root() -> Path:
        """Return the installed flext-infra package root."""
        return Path(__file__).resolve().parent.parent

    @staticmethod
    def _template_path(
        templates_root: Path, entry: m.Infra.ManagedSurfaceSpec
    ) -> p.Result[Path]:
        """Resolve one declared template without escaping the catalog root."""
        if entry.source is None:
            return r[Path].fail(f"surface has no template source: {entry.path}")
        source = (templates_root / entry.source).resolve()
        if not source.is_relative_to(templates_root) or not source.is_file():
            return r[Path].fail(
                f"template source is missing or escapes its root: {entry.source}"
            )
        return r[Path].ok(source)

    @staticmethod
    def render_project_gitignore(
        codegen: m.Infra.CodegenConfigSpec,
        *,
        profile: c.Infra.MakeProfile,
        project_name: str,
        workspace: m.Infra.WorkspaceSpec | None = None,
    ) -> p.Result[str]:
        """Render the canonical ``.gitignore`` for one named project.

        Public seam consumed by the layout engine (mro-0wuz): per-project
        layout ``gitignore_additions`` from the layout SSOT are appended as
        one trailing derived section so conform and layout never diverge.
        """
        return FlextInfraCodegenConform._render_gitignore(
            codegen, profile=profile, project_name=project_name, workspace=workspace
        )

    @staticmethod
    def _render_gitignore(
        codegen: m.Infra.CodegenConfigSpec,
        *,
        profile: c.Infra.MakeProfile,
        project_name: str | None = None,
        workspace: m.Infra.WorkspaceSpec | None = None,
    ) -> p.Result[str]:
        """Render the canonical ``.gitignore`` body via the single template.

        NOTE (mro-jnm1.2): ``codegen new`` renders ``base/gitignore.j2`` with
        the full project context; conform renders the same template with the
        codegen config — both consume the same computed ``gitignore_sections``
        projection, so the body is byte-identical.
        """
        entry = next(
            (
                item
                for item in codegen.surfaces.entries
                if item.path == c.Infra.GITIGNORE
            ),
            None,
        )
        if entry is None:
            return r[str].fail(
                "gitignore template is missing from codegen configuration"
            )
        templates_root = (
            FlextInfraCodegenConform._package_root()
            / "templates"
            / codegen.surfaces.root
        ).resolve()
        sections = [
            section
            for section in codegen.gitignore_sections
            if not section.profiles or profile in section.profiles
        ]
        # The deny-all root policy (`/*` + `/*/`) would swallow every governed
        # member directory, so their whitelist is DERIVED from the live workspace
        # topology instead of a hardcoded name glob: declaring a member in
        # `config/workspace.yaml` is the single source that makes it trackable.
        # Nested paths need every ancestor unignored, otherwise git never
        # descends far enough to reach the member itself.
        member_patterns: list[str] = []
        if workspace is not None and profile == c.Infra.MakeProfile.WORKSPACE_ROOT:
            for member in workspace.members:
                parts = member.path.as_posix().strip("/").split("/")
                # Every ancestor is unignored so git can descend into the
                # member, then its contents are unignored with the `/**` form.
                prefixes = [
                    "/".join(parts[:depth]) for depth in range(1, len(parts) + 1)
                ]
                candidates = [f"!/{prefix}/" for prefix in prefixes]
                candidates.append(f"!/{prefixes[-1]}/**")
                for pattern in candidates:
                    if pattern not in member_patterns:
                        member_patterns.append(pattern)
        if member_patterns:
            sections.append(
                m.Infra.ScaffoldGitignoreSectionSpec(
                    name="WHITELIST: governed workspace members (derived)",
                    patterns=tuple(member_patterns),
                )
            )
        if project_name is not None:
            override = codegen.layout.project_overrides.get(project_name)
            if override is not None and override.gitignore_additions:
                sections.append(
                    m.Infra.ScaffoldGitignoreSectionSpec(
                        name=c.Infra.GITIGNORE_LAYOUT_SECTION_NAME,
                        patterns=override.gitignore_additions,
                    )
                )
        source = FlextInfraCodegenConform._template_path(templates_root, entry)
        if source.failure:
            return r[str].fail(source.error or "gitignore template source is invalid")
        context = m.Infra.GitignoreRenderSpec(gitignore_sections=tuple(sections))
        return u.Cli.template_render(source.value, context)

    @staticmethod
    def _select_repositories(
        request: m.Infra.CodegenConformRequest,
        workspace: m.Infra.WorkspaceSpec,
        current_repository: m.Infra.RepositoryRef,
    ) -> p.Result[tuple[m.Infra.RepositoryRef, ...]]:
        """Resolve self/members/all from the governing topology manifest."""
        scope = c.Infra.CodegenConformScope(request.scope)
        if scope == c.Infra.CodegenConformScope.SELF:
            selected = (current_repository,)
        elif scope == c.Infra.CodegenConformScope.MEMBERS:
            if not workspace.members:
                return r[tuple[m.Infra.RepositoryRef, ...]].fail(
                    "members scope requires a workspace-root manifest"
                )
            selected = tuple(workspace.members)
        else:
            selected = (workspace.repository, *workspace.members)
        mutable = tuple(
            repository
            for repository in selected
            if repository.codegen != c.Infra.CodegenKind.NONE
            and not repository.read_only
        )
        if not mutable:
            return r[tuple[m.Infra.RepositoryRef, ...]].fail(
                "selected repositories do not permit code generation"
            )
        return r[tuple[m.Infra.RepositoryRef, ...]].ok(mutable)

    @staticmethod
    def _repository_root(
        root: Path, workspace: p.Infra.WorkspaceSpec, repository: p.Infra.RepositoryRef
    ) -> Path:
        """Resolve one selected checkout without sibling discovery."""
        if repository.name == workspace.repository.name:
            return root
        resolved: Path = (root / repository.path).resolve()
        return resolved

    @staticmethod
    def _scaffold_python_dirs(
        entries: t.SequenceOf[m.Infra.ManagedSurfaceSpec], profile: c.Infra.MakeProfile
    ) -> t.StrSequence:
        """Return Python roots the selected scaffold manifest actually creates."""
        # NOTE (multi-agent, mro-wkii.17.9.2.1): derive future roots from both
        # declarative owners so scaffold and existing-tree discovery converge.
        generated_roots = {
            Path(entry.path).parts[0]
            for entry in entries
            if profile in entry.profiles
            and entry.delegate == "render"
            and Path(entry.path).parts
        }
        return tuple(
            directory
            for directory in config.Infra.tooling.tools.pyright.path_rules.env_dirs
            if directory in generated_roots
        )

    def _plan_scaffold_repository(
        self,
        *,
        root: Path,
        repository: m.Infra.RepositoryRef,
        target: m.Infra.RepositoryConformTarget,
        workspace: m.Infra.WorkspaceSpec,
        codegen: m.Infra.CodegenConfigSpec,
        contract: SurfaceContract,
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Render the complete scaffold for ``codegen new`` only."""
        project = workspace.project
        if project is None:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                f"scaffold workspace has no project metadata: {workspace.name}"
            )
        profile = target.make_profile
        pyproject = root / c.Infra.PYPROJECT_FILENAME
        # mro-j47u (codex): new and existing repositories share the exact same
        # root-scoped modernizer pipeline, so first generation is a fixed point.
        # NOTE(mro-p68a.5, agent codex): a declared member consumes its parent
        # tooling profile even before the atomic scaffold creates files on disk.
        tooling_root = target.root
        modernizer = FlextInfraPyprojectModernizer(workspace_root=tooling_root)
        declared_python_dirs = self._scaffold_python_dirs(
            codegen.surfaces.entries, profile
        )
        tooling_result = modernizer.resolve_tooling_context(
            project_name=repository.distribution,
            package_name=project.package_name,
            path=pyproject,
            declared_python_dirs=declared_python_dirs,
        )
        if tooling_result.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                tooling_result.error or f"tooling render failed: {pyproject}"
            )
        context_result = self._project_render_context(
            repository, target, workspace, codegen, tooling_runtime=tooling_result.value
        )
        if context_result.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                context_result.error or "project render context is invalid"
            )
        context = context_result.value
        effective_make = context.make
        uv_exclude_dependencies = tuple(
            item
            for item in codegen.uv_exclude_dependencies
            if item.project == repository.distribution
        )
        planned: list[m.Infra.CodegenFilePlan] = []
        templates_root = (
            self._package_root() / "templates" / codegen.surfaces.root
        ).resolve()
        seen_destinations: set[str] = set()
        for entry in codegen.surfaces.entries:
            if profile not in entry.profiles:
                continue
            if not self._entry_matches_surface(entry, contract):
                continue
            if entry.requires_ci and not target.ci_enabled:
                continue
            if entry.requires_beads and not (
                target.beads_enabled or target.routing_only
            ):
                continue
            if entry.delegate == "vscode-settings":
                continue
            source = self._template_path(templates_root, entry)
            if source.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    source.error or f"template source is invalid: {entry.path}"
                )
            destination = entry.path.format(
                package_name=context.package_name, ns=context.ns
            )
            relative = Path(destination)
            if relative.is_absolute() or ".." in relative.parts:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    f"template destination escapes repository root: {destination}"
                )
            if destination in seen_destinations:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    f"duplicate template destination: {destination}"
                )
            seen_destinations.add(destination)
            path = root / relative
            if path.exists() and not path.is_file():
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    f"template destination is not a regular file: {path}"
                )
            for parent in path.parents:
                if parent == root:
                    break
                if parent.exists() and not parent.is_dir():
                    return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                        f"template destination parent is not a directory: {parent}"
                    )
        for entry in codegen.surfaces.entries:
            if profile not in entry.profiles:
                continue
            if not self._entry_matches_surface(entry, contract):
                continue
            if not contract.delegates:
                continue
            if entry.requires_ci and not target.ci_enabled:
                continue
            if entry.requires_beads and not (
                target.beads_enabled or target.routing_only
            ):
                continue
            # mro-i6nq.10: One formatted path governs validation and planning.
            destination = entry.path.format(
                package_name=context.package_name, ns=context.ns
            )
            if entry.delegate == "manifest":
                # NOTE (multi-agent, mro-wkii.17 / agent: uv_overlay_owner):
                # template rendering retains the canonical context instance.
                source = self._template_path(templates_root, entry)
                if source.failure:
                    return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                        source.error or f"manifest template is invalid: {entry.path}"
                    )
                rendered_manifest = u.Cli.template_render(source.value, context)
                if rendered_manifest.failure:
                    return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                        rendered_manifest.error
                        or f"manifest render failed: {entry.source}"
                    )
                manifest_validation = self._validate_initial_manifest(
                    rendered_manifest.value, workspace
                )
                if manifest_validation.failure:
                    return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                        manifest_validation.error
                        or "initial workspace manifest validation failed"
                    )
                manifest_plan = self._file_plan(
                    root,
                    destination,
                    rendered_manifest.value,
                    surface=entry,
                    block_existing=True,
                )
                if manifest_plan.failure:
                    return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                        manifest_plan.error or "workspace manifest planning failed"
                    )
                planned.append(manifest_plan.value)
                continue
            if entry.delegate != "render":
                continue
            if entry.surface == c.Infra.CodegenConformSurface.PYPROJECT:
                continue
            artifact_context = self._artifact_render_context(
                dist=context.dist,
                repository=repository,
                target=target,
                workspace=workspace,
                codegen=codegen,
                entry=entry,
                tooling_runtime=tooling_result.value,
                project_context=context,
                make=effective_make,
            )
            if artifact_context.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    artifact_context.error
                    or f"artifact render context failed: {destination}"
                )
            source = self._template_path(templates_root, entry)
            if source.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    source.error or f"template source is invalid: {entry.path}"
                )
            rendered = u.Cli.template_render(source.value, artifact_context.value)
            if rendered.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    rendered.error or f"template render failed: {entry.source}"
                )
            file_plan = self._file_plan(
                root, destination, rendered.value, surface=entry, block_existing=True
            )
            if file_plan.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    file_plan.error or f"managed file planning failed: {entry.path}"
                )
            planned.append(file_plan.value)
        if not contract.pyproject:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(tuple(planned))
        pyproject_entry = next(
            (
                item
                for item in codegen.surfaces.entries
                if item.surface == c.Infra.CodegenConformSurface.PYPROJECT
                and profile in item.profiles
                and item.delegate == "render"
            ),
            None,
        )
        if pyproject_entry is None:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                "pyproject template is missing from codegen configuration"
            )
        pyproject_source = self._template_path(templates_root, pyproject_entry)
        if pyproject_source.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                pyproject_source.error or "pyproject template source is invalid"
            )
        pyproject_render = u.Cli.template_render(pyproject_source.value, context)
        if pyproject_render.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                pyproject_render.error or "pyproject template render failed"
            )
        initial_tooling = modernizer.conform_source(
            pyproject_render.value,
            path=pyproject,
            declared_python_dirs=declared_python_dirs,
        )
        if initial_tooling.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                initial_tooling.error or f"initial tooling conform failed: {pyproject}"
            )
        prepared_result = u.Infra.pyproject_conform(
            initial_tooling.value,
            providers=codegen.providers,
            workspace=workspace,
            workspace_mode=c.Infra.WorkspaceMode.STANDALONE,
            toolchain=codegen.toolchain,
            required_dev_dependencies=codegen.scaffold.project.dev,
            uv_exclude_dependencies=uv_exclude_dependencies,
        )
        if prepared_result.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                prepared_result.error or f"pyproject prepare failed: {pyproject}"
            )
        final_tooling = modernizer.conform_source(
            prepared_result.value,
            path=pyproject,
            declared_python_dirs=declared_python_dirs,
        )
        if final_tooling.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                final_tooling.error or f"final tooling conform failed: {pyproject}"
            )
        pyproject_plan = self._file_plan(
            root,
            c.Infra.PYPROJECT_FILENAME,
            final_tooling.value,
            surface=pyproject_entry,
            block_existing=True,
        )
        if pyproject_plan.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                pyproject_plan.error or f"pyproject planning failed: {pyproject}"
            )
        planned.append(pyproject_plan.value)
        return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(tuple(planned))

    def _plan_existing_repository(
        self,
        *,
        root: Path,
        workspace_root: Path,
        repository: m.Infra.RepositoryRef,
        target: m.Infra.RepositoryConformTarget,
        workspace: m.Infra.WorkspaceSpec,
        codegen: m.Infra.CodegenConfigSpec,
        contract: SurfaceContract,
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Conform every declared managed surface in an existing repository."""
        pyproject = root / c.Infra.PYPROJECT_FILENAME
        if not pyproject.is_file():
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                f"existing repository has no pyproject.toml: {root}; "
                "scaffold templates are available only through codegen new"
            )
        metadata = u.read_project_metadata(root)
        if metadata.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                metadata.error or f"project metadata load failed: {root}"
            )
        dist = metadata.value.project.name
        if dist != repository.distribution:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                "PEP 621 project name does not match catalog distribution: "
                f"{dist} != {repository.distribution}"
            )
        pyproject_read = u.Cli.files_read_text(pyproject)
        if pyproject_read.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                pyproject_read.error or f"pyproject read failed: {pyproject}"
            )
        pyproject_surfaces = tuple(
            item
            for item in codegen.surfaces.entries
            if item.path == c.Infra.PYPROJECT_FILENAME
        )
        if len(pyproject_surfaces) != 1:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                "pyproject must resolve exactly one catalog surface"
            )
        pyproject_surface = pyproject_surfaces[0]
        workspace_mode = {
            c.Infra.MakeProfile.WORKSPACE_ROOT: c.Infra.WorkspaceMode.WORKSPACE,
            c.Infra.MakeProfile.WORKSPACE_MEMBER: (
                c.Infra.WorkspaceMode.WORKSPACE_MEMBER
            ),
            c.Infra.MakeProfile.STANDALONE: c.Infra.WorkspaceMode.STANDALONE,
        }[target.make_profile]
        uv_exclude_dependencies = tuple(
            item
            for item in codegen.uv_exclude_dependencies
            if item.project == repository.distribution
        )
        if contract.dependencies_only:
            dependency_result = u.Infra.pyproject_dependencies_conform(
                pyproject_read.value,
                providers=codegen.providers,
                workspace=workspace,
                workspace_mode=workspace_mode,
            )
            if dependency_result.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    dependency_result.error
                    or f"pyproject dependency conform failed: {pyproject}"
                )
            dependency_plan = self._file_plan(
                root,
                c.Infra.PYPROJECT_FILENAME,
                dependency_result.value,
                surface=pyproject_surface,
            )
            if dependency_plan.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    dependency_plan.error
                    or f"pyproject dependency planning failed: {pyproject}"
                )
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok((dependency_plan.value,))
        modernizer = FlextInfraPyprojectModernizer(workspace_root=workspace_root)
        tooling_context = modernizer.resolve_tooling_context(
            project_name=repository.distribution,
            package_name=metadata.value.package_name,
            path=pyproject,
            declared_python_dirs=(
                config.Infra.tooling.tools.pyright.path_rules.source_dir,
            ),
        )
        if tooling_context.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                tooling_context.error or f"tooling render failed: {pyproject}"
            )
        if not contract.pyproject:
            return self._plan_existing_templates(
                root=root,
                repository=repository,
                target=target,
                workspace=workspace,
                codegen=codegen,
                tooling_runtime=tooling_context.value,
                contract=contract,
            )
        prepared_result = u.Infra.pyproject_conform(
            pyproject_read.value,
            providers=codegen.providers,
            workspace=workspace,
            workspace_mode=workspace_mode,
            toolchain=codegen.toolchain,
            required_dev_dependencies=codegen.scaffold.project.dev,
            uv_exclude_dependencies=uv_exclude_dependencies,
        )
        if prepared_result.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                prepared_result.error or f"pyproject preparation failed: {pyproject}"
            )
        # Dependency topology is conformed before tooling so the modernizer is
        # the final owner of TOML ordering, comments, and type-checker settings.
        # It preserves the already canonical dependency source declarations.
        tooling_result = modernizer.conform_source(
            prepared_result.value, path=pyproject
        )
        if tooling_result.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                tooling_result.error or f"tooling conform failed: {pyproject}"
            )
        pyproject_plan = self._file_plan(
            root,
            c.Infra.PYPROJECT_FILENAME,
            tooling_result.value,
            surface=pyproject_surface,
        )
        if pyproject_plan.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                pyproject_plan.error or f"pyproject planning failed: {pyproject}"
            )
        planned = [pyproject_plan.value]
        if not contract.templates:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(tuple(planned))
        # The surface catalog is the sole owner and render manifest.
        managed_result = self._plan_existing_templates(
            root=root,
            repository=repository,
            target=target,
            workspace=workspace,
            codegen=codegen,
            tooling_runtime=tooling_context.value,
            contract=contract,
        )
        if managed_result.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                managed_result.error or f"managed template planning failed: {root}"
            )
        planned.extend(managed_result.value)
        return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(tuple(planned))

    def _plan_existing_templates(
        self,
        *,
        root: Path,
        repository: m.Infra.RepositoryRef,
        target: m.Infra.RepositoryConformTarget,
        workspace: m.Infra.WorkspaceSpec,
        codegen: m.Infra.CodegenConfigSpec,
        tooling_runtime: m.Infra.ToolingRuntimeContext,
        contract: SurfaceContract,
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Render configured overwrite-owned templates for an existing tree."""
        profile = target.make_profile
        templates_root = (
            self._package_root() / "templates" / codegen.surfaces.root
        ).resolve()
        planned: list[m.Infra.CodegenFilePlan] = []
        effective_make = u.Infra.repository_make_spec(codegen.make, repository)
        if effective_make.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                effective_make.error or "repository Make graph resolution failed"
            )
        for entry in codegen.surfaces.entries:
            if (
                entry.policy == "manual"
                or entry.surface == c.Infra.CodegenConformSurface.PYPROJECT
                or entry.delegate != "render"
            ):
                continue
            if not self._entry_matches_surface(entry, contract):
                continue
            if entry.requires_ci and not target.ci_enabled:
                continue
            if profile not in entry.profiles:
                continue
            if entry.requires_beads and not (
                target.beads_enabled or target.attached_standalone
            ):
                continue
            path = root / entry.path
            artifact_context = self._artifact_render_context(
                dist=repository.distribution,
                repository=repository,
                target=target,
                workspace=workspace,
                codegen=codegen,
                entry=entry,
                tooling_runtime=tooling_runtime,
                project_context=None,
                make=effective_make.value,
            )
            if artifact_context.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    f"managed artifact context failed for {entry.path}: "
                    f"{artifact_context.error or '<no diagnostic>'}"
                )
            source = self._template_path(templates_root, entry)
            if source.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    source.error or f"template source is invalid: {entry.path}"
                )
            rendered = u.Cli.template_render(source.value, artifact_context.value)
            if rendered.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    rendered.error or f"template render failed: {entry.source}"
                )
            rendered_content = rendered.value
            if entry.merge_strategy == "gitmodules" and path.is_file():
                current = u.Cli.files_read_text(path)
                if current.failure:
                    return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                        current.error or f"managed file read failed: {path}"
                    )
                rendered_content = self._merge_gitmodules(
                    current.value,
                    rendered.value,
                    managed_paths=frozenset(
                        member.path.as_posix() for member in workspace.members
                    ),
                )
            file_plan = self._file_plan(
                root, entry.path, rendered_content, surface=entry
            )
            if file_plan.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    file_plan.error or f"managed file planning failed: {entry.path}"
                )
            planned.append(file_plan.value)
        return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(tuple(planned))

    @staticmethod
    def _workspace_root_rel(target: m.Infra.RepositoryConformTarget) -> str:
        """Derive the governing root from the typed repository relation."""
        if (
            target.make_profile != c.Infra.MakeProfile.WORKSPACE_MEMBER
            or target.attached_standalone
        ):
            return "."
        member_path = target.repository.path
        if (
            member_path.is_absolute()
            or not member_path.parts
            or member_path == Path()
            or ".." in member_path.parts
        ):
            msg = f"workspace member path is not relative: {member_path.as_posix()}"
            raise ValueError(msg)
        return Path(*(os.pardir for _ in member_path.parts)).as_posix()

    @staticmethod
    def _merge_gitmodules(
        current: str, managed: str, *, managed_paths: frozenset[str]
    ) -> str:
        """Replace governed submodule sections and preserve every foreign block."""
        matches = tuple(_GITMODULE_SECTION_RE.finditer(current))
        if not matches:
            preserved = current
        else:
            parts = [current[: matches[0].start()]]
            for index, match in enumerate(matches):
                end = (
                    matches[index + 1].start()
                    if index + 1 < len(matches)
                    else len(current)
                )
                block = current[match.start() : end]
                path_match = _GITMODULE_PATH_RE.search(block)
                if path_match is None or path_match.group(1) not in managed_paths:
                    parts.append(block)
            preserved = "".join(parts)
        if not managed:
            return preserved
        separator = "" if not preserved or preserved.endswith("\n\n") else "\n"
        return f"{preserved}{separator}{managed}"

    @staticmethod
    def _infra_repository(
        workspace: m.Infra.WorkspaceSpec,
    ) -> p.Result[m.Infra.RepositoryRef]:
        """Resolve the repository that owns the infrastructure CLI.

        The owner is read from the live workspace topology when that topology
        declares it. A standalone consumer legitimately declares no
        flext-infra member, so the reference is then derived from the provider
        contract. Either way nothing is looked up in a project catalog, which
        flext-infra is forbidden to own.
        """
        matches = tuple(
            item
            for item in (workspace.repository, *workspace.members)
            if item.distribution == config.Infra.name
        )
        if len(matches) > 1:
            return r[m.Infra.RepositoryRef].fail(
                "workspace topology declares more than one "
                f"{config.Infra.name} checkout"
            )
        if matches:
            return r[m.Infra.RepositoryRef].ok(matches[0])
        return r[m.Infra.RepositoryRef].ok(
            u.Infra.derived_repository_ref(
                config.Infra.name, provider=config.Infra.codegen.default_provider_spec
            )
        )

    @staticmethod
    def _repository_provider(
        repository: m.Infra.RepositoryRef, codegen: m.Infra.CodegenConfigSpec
    ) -> p.Result[m.Infra.ProviderSpec]:
        """Resolve one repository to exactly one provider-owned policy."""
        resolved: p.Result[m.Infra.ProviderSpec] = u.Infra.repository_provider(
            repository, codegen.providers
        )
        return resolved

    @classmethod
    def _managed_gitlinks(
        cls, workspace: m.Infra.WorkspaceSpec
    ) -> p.Result[tuple[m.Infra.ManagedGitlinkSpec, ...]]:
        """Project repository-owned baselines for mutable governed members."""
        resolved = tuple(
            m.Infra.ManagedGitlinkSpec(repository=repository, branch=repository.branch)
            for repository in workspace.members
        )
        return r[tuple[m.Infra.ManagedGitlinkSpec, ...]].ok(resolved)

    @staticmethod
    def _infra_source_root_rel(
        target: m.Infra.RepositoryConformTarget,
        workspace: m.Infra.WorkspaceSpec,
        infra_repository: m.Infra.RepositoryRef,
    ) -> str | None:
        """Return a local engine source path only when the workspace declares it."""
        workspace_repositories: tuple[m.Infra.RepositoryRef, ...] = (
            workspace.repository,
            *workspace.members,
        )
        local: m.Infra.RepositoryRef | None = next(
            (
                item
                for item in workspace_repositories
                if item.distribution == infra_repository.distribution
                and item.url == infra_repository.url
                and item.provider == infra_repository.provider
            ),
            None,
        )
        if local is None:
            return None
        workspace_root_rel = FlextInfraCodegenConform._workspace_root_rel(target)
        local_path: Path = local.path
        return (Path(workspace_root_rel) / local_path).as_posix()

    def _artifact_render_context(
        self,
        *,
        dist: str,
        repository: m.Infra.RepositoryRef,
        target: m.Infra.RepositoryConformTarget,
        workspace: m.Infra.WorkspaceSpec,
        codegen: m.Infra.CodegenConfigSpec,
        entry: m.Infra.ManagedSurfaceSpec,
        tooling_runtime: m.Infra.ToolingRuntimeContext,
        project_context: m.Infra.ProjectRenderContext | None,
        make: m.Infra.MakeSpec,
    ) -> p.Result[p.Model]:
        """Resolve one projection through its config-declared typed context."""
        context_kind = entry.render_context
        if context_kind == "gitignore":
            profile = target.make_profile
            sections = tuple(
                section
                for section in codegen.gitignore_sections
                if not section.profiles or profile in section.profiles
            )
            overlay = next(
                (
                    item
                    for item in workspace.repository_policy_overlays
                    if item.project == repository.distribution
                ),
                None,
            )
            if overlay is not None and overlay.extra_ignored_patterns:
                sections = (
                    *sections,
                    m.Infra.ScaffoldGitignoreSectionSpec(
                        name="Project-local exceptions",
                        patterns=overlay.extra_ignored_patterns,
                    ),
                )
            return r[p.Model].ok(
                m.Infra.GitignoreRenderSpec(gitignore_sections=sections)
            )
        if context_kind == "sgconfig":
            # Why (ai-hub-qwoc): the ast-grep contract is identical for every
            # governed repository, so it renders straight from the codegen SSOT.
            return r[p.Model].ok(codegen.sgconfig)
        if context_kind == "make-workflow":
            return r[p.Model].ok(m.Infra.MakeWorkflowRenderSpec(dist=dist, make=make))
        if context_kind == "toolchain":
            return r[p.Model].ok(codegen.toolchain)
        if context_kind == "tooling":
            return r[p.Model].ok(config.Infra.tooling)
        if context_kind == "beads":
            server = codegen.toolchain.beads.server
            if server is None:
                return r[p.Model].fail(
                    "Beads ledger server is not declared in the toolchain SSOT"
                )
            prefix_result = self.declared_beads_prefix(
                target.root, default_prefix=target.canonical_project_name
            )
            if prefix_result.failure:
                return r[p.Model].fail(
                    prefix_result.error
                    or f"Beads tracker declaration failed: {target.root}"
                )
            issue_prefix = prefix_result.value
            return r[p.Model].ok(
                m.Infra.BeadsConfigRenderSpec(
                    issue_prefix=issue_prefix,
                    database=workspace.ledger_id or issue_prefix,
                    server=server,
                    routing=target.routing_only,
                )
            )
        if context_kind == "github":
            workspace_repositories = (
                tuple(workspace.members)
                if target.make_profile == c.Infra.MakeProfile.WORKSPACE_ROOT
                else ()
            )
            return r[p.Model].ok(
                m.Infra.GithubWorkflowRenderSpec(
                    dist=dist,
                    repository_branch=repository.branch,
                    production_branch=codegen.branch_policy.production_branch,
                    python_version=codegen.toolchain.python_version,
                    github_actions=codegen.github_actions,
                    make=make,
                    workspace_repositories=workspace_repositories,
                    checkout_submodules=codegen.checkout_submodules_overrides.get(
                        dist, codegen.checkout_submodules
                    ),
                )
            )
        if context_kind == "docker":
            return r[p.Model].ok(
                m.Infra.DistroDockerRenderSpec(
                    package_name=dist.replace("-", "_"),
                    python_version=codegen.toolchain.python_version,
                )
            )
        if context_kind == "make":
            return self.make_render_context(
                repository,
                target,
                workspace,
                codegen,
                make=make,
                tooling_runtime=tooling_runtime,
            )
        if context_kind == "project" and project_context is not None:
            return r[p.Model].ok(project_context)
        if context_kind != "project":
            return r[p.Model].fail(
                f"unsupported template render context: {context_kind}"
            )
        context_result = self._project_render_context(
            repository, target, workspace, codegen, tooling_runtime=tooling_runtime
        )
        if context_result.failure:
            return r[p.Model].fail(
                context_result.error or f"managed artifact context failed: {entry.path}"
            )
        return r[p.Model].ok(context_result.value)

    def _entry_matches_surface(
        self, entry: m.Infra.ManagedSurfaceSpec, contract: SurfaceContract
    ) -> bool:
        """Select projections only through the typed template manifest."""
        if self.projection_operation not in entry.operations:
            return False
        if self.projection_operation != "conform":
            return True
        if contract.surface == c.Infra.CodegenConformSurface.ALL:
            return True
        matches_surface: bool = entry.surface == contract.surface
        return matches_surface

    @staticmethod
    def make_render_context(
        repository: m.Infra.RepositoryRef,
        target: m.Infra.RepositoryConformTarget,
        workspace: m.Infra.WorkspaceSpec,
        codegen: m.Infra.CodegenConfigSpec,
        *,
        make: m.Infra.MakeSpec,
        tooling_runtime: m.Infra.ToolingRuntimeContext,
    ) -> p.Result[m.Infra.MakeRenderContext]:
        """Build the typed context consumed by the generated Makefile."""
        profile = target.make_profile
        infra_repository = FlextInfraCodegenConform._infra_repository(workspace)
        if infra_repository.failure:
            return r[m.Infra.MakeRenderContext].fail(
                infra_repository.error
                or "infrastructure CLI repository resolution failed"
            )
        infra_provider = FlextInfraCodegenConform._repository_provider(
            infra_repository.value, codegen
        )
        if infra_provider.failure:
            return r[m.Infra.MakeRenderContext].fail(
                infra_provider.error or "infrastructure provider resolution failed"
            )
        members = (
            tuple(workspace.members)
            if profile == c.Infra.MakeProfile.WORKSPACE_ROOT
            else ()
        )
        gitlinks = FlextInfraCodegenConform._managed_gitlinks(workspace)
        if gitlinks.failure:
            return r[m.Infra.MakeRenderContext].fail(
                gitlinks.error or "managed Gitlink resolution failed"
            )
        return r[m.Infra.MakeRenderContext].ok(
            m.Infra.MakeRenderContext(
                make=make,
                make_engine_path=codegen.surfaces.make_engine_path,
                runtime_environment_dir=(
                    config.Infra.tooling.tools.pyright.path_rules.venv_name
                ),
                tooling_runtime=tooling_runtime,
                dist=repository.distribution,
                infra_repository=infra_repository.value,
                infra_repository_branch=infra_repository.value.branch,
                infra_source_root_rel=FlextInfraCodegenConform._infra_source_root_rel(
                    target, workspace, infra_repository.value
                ),
                python_version=codegen.toolchain.python_version,
                uv_link_mode=codegen.toolchain.uv_link_mode,
                profile=next(item for item in codegen.profiles if item.name == profile),
                workspace_root_rel=FlextInfraCodegenConform._workspace_root_rel(target),
                workspace_repositories=members,
                workspace_gitlinks=gitlinks.value,
            )
        )

    @staticmethod
    def _project_render_context(
        repository: m.Infra.RepositoryRef,
        target: m.Infra.RepositoryConformTarget,
        workspace: m.Infra.WorkspaceSpec,
        codegen: m.Infra.CodegenConfigSpec,
        *,
        tooling_runtime: m.Infra.ToolingRuntimeContext,
    ) -> p.Result[m.Infra.ProjectRenderContext]:
        """Build the complete typed context consumed by project templates."""
        if workspace.project is None:
            return r[m.Infra.ProjectRenderContext].fail(
                f"workspace has no project metadata: {workspace.name}"
            )
        project = workspace.project
        dependency_profile = next(
            (
                item
                for item in codegen.scaffold.project.dependency_profiles
                if item.upstream == project.upstream
            ),
            None,
        )
        if dependency_profile is None:
            return r[m.Infra.ProjectRenderContext].fail(
                f"unsupported scaffold upstream: {project.upstream}"
            )
        if project.license not in codegen.scaffold.project.supported_licenses:
            supported = ", ".join(codegen.scaffold.project.supported_licenses)
            return r[m.Infra.ProjectRenderContext].fail(
                f"unsupported scaffold license: {project.license}; "
                f"supported licenses: {supported}"
            )
        profile = target.make_profile
        infra_repository = FlextInfraCodegenConform._infra_repository(workspace)
        if infra_repository.failure:
            return r[m.Infra.ProjectRenderContext].fail(
                infra_repository.error
                or "infrastructure CLI repository resolution failed"
            )
        infra_provider = FlextInfraCodegenConform._repository_provider(
            infra_repository.value, codegen
        )
        if infra_provider.failure:
            return r[m.Infra.ProjectRenderContext].fail(
                infra_provider.error or "infrastructure provider resolution failed"
            )
        repository_provider = FlextInfraCodegenConform._repository_provider(
            repository, codegen
        )
        if repository_provider.failure:
            return r[m.Infra.ProjectRenderContext].fail(
                repository_provider.error or "repository provider resolution failed"
            )
        members = (
            tuple(workspace.members)
            if profile == c.Infra.MakeProfile.WORKSPACE_ROOT
            else ()
        )
        gitlinks = FlextInfraCodegenConform._managed_gitlinks(workspace)
        if gitlinks.failure:
            return r[m.Infra.ProjectRenderContext].fail(
                gitlinks.error or "managed Gitlink resolution failed"
            )
        packaged_data_dirs = (
            tuple(
                data_dir
                for data_dir in config.Infra.tooling.tools.hatch.packaged_data_dirs
                if any(
                    profile in entry.profiles
                    and Path(entry.path).parts
                    and Path(entry.path).parts[0] == data_dir
                    for entry in codegen.surfaces.entries
                )
            )
            if profile != c.Infra.MakeProfile.WORKSPACE_ROOT
            else ()
        )
        # Emit only the .gitignore sections that apply to this profile: a
        # section with no declared profiles is universal; a workspace-root-only
        # section (member-directory allowlist, workspace manifest, submodule/
        # Beads coordination) never reaches a member or standalone .gitignore.
        profile_gitignore_sections = tuple(
            section
            for section in codegen.gitignore_sections
            if not section.profiles or profile in section.profiles
        )
        make = u.Infra.repository_make_spec(codegen.make, repository)
        if make.failure:
            return r[m.Infra.ProjectRenderContext].fail(
                make.error or "repository Make graph resolution failed"
            )
        return r[m.Infra.ProjectRenderContext].ok(
            m.Infra.ProjectRenderContext(
                scaffold=codegen.scaffold,
                gitignore_sections=profile_gitignore_sections,
                dependency_profile=dependency_profile,
                make=make.value,
                make_engine_path=codegen.surfaces.make_engine_path,
                runtime_environment_dir=(
                    config.Infra.tooling.tools.pyright.path_rules.venv_name
                ),
                tooling_runtime=tooling_runtime,
                dist=repository.distribution,
                is_package=repository.package,
                infra_repository=infra_repository.value,
                infra_repository_branch=infra_repository.value.branch,
                infra_source_root_rel=FlextInfraCodegenConform._infra_source_root_rel(
                    target, workspace, infra_repository.value
                ),
                python_version=codegen.toolchain.python_version,
                uv_link_mode=codegen.toolchain.uv_link_mode,
                profile=next(item for item in codegen.profiles if item.name == profile),
                workspace_root_rel=FlextInfraCodegenConform._workspace_root_rel(target),
                workspace_repositories=members,
                workspace_gitlinks=gitlinks.value,
                tooling=config.Infra.tooling,
                environment_path_prepends=(codegen.toolchain.environment_path_prepends),
                beads_tool_selector=codegen.toolchain.beads.selector,
                beads_tool_version=codegen.toolchain.beads.version,
                beads_enabled=target.beads_enabled,
                canonical_project_name=target.canonical_project_name,
                const_name=project.constant_name,
                package_name=project.package_name,
                packaged_data_dirs=packaged_data_dirs,
                class_stem=project.class_stem,
                ns=project.namespace,
                ns_attr=project.namespace_attribute,
                alias=project.alias,
                env_prefix=project.environment_prefix,
                upstream=project.upstream,
                description=project.description,
                version=project.version,
                license=project.license,
                python_required_version=codegen.toolchain.python_required_version,
                kubectl_version=codegen.toolchain.kubectl_version,
                helm_version=codegen.toolchain.helm_version,
                kind_version=codegen.toolchain.kind_version,
                taplo_version=codegen.toolchain.taplo_version,
                ast_grep_version=codegen.toolchain.ast_grep_version,
                gitleaks_version=codegen.toolchain.gitleaks_version,
                author_name=project.author_name,
                author_email=project.author_email,
                repository=project.homepage,
                homepage=project.homepage,
                documentation=project.documentation,
                flext_git_base_url=codegen.default_provider_spec.base_url,
                workspace_manifest_version=c.Infra.WORKSPACE_MANIFEST_VERSION,
                workspace_repository=repository,
                year=project.year,
                workspace_exclusions=tuple(workspace.exclusions),
                workspace_policy_overlays=tuple(workspace.repository_policy_overlays),
            )
        )

    @classmethod
    def _validate_initial_manifest(
        cls, rendered: str, expected: m.Infra.WorkspaceSpec
    ) -> p.Result[bool]:
        """Validate rendered manifest syntax, canonical model, and exact payload."""
        parsed = u.Cli.yaml_parse(rendered)
        if parsed.failure:
            return r[bool].fail(parsed.error or "workspace manifest YAML is invalid")
        try:
            validated = m.Infra.WorkspaceSpec.model_validate(parsed.value)
        except c.ValidationError as exc:
            return r[bool].fail_op("workspace manifest model validation", exc)
        if validated != expected:
            return r[bool].fail("rendered workspace manifest differs from input model")
        return r[bool].ok(True)

    def _file_plan(
        self,
        root: Path,
        relative_path: str,
        rendered: str,
        *,
        surface: m.Infra.ManagedSurfaceSpec,
        block_existing: bool = False,
    ) -> p.Result[m.Infra.CodegenFilePlan]:
        """Compare one expected output under its catalog ownership policy."""
        path = root / relative_path
        if path.exists() and not path.is_file():
            return r[m.Infra.CodegenFilePlan].fail(
                f"managed destination is not a regular file: {path}"
            )
        current = ""
        if path.is_file():
            read = u.Cli.files_read_text(path)
            if read.failure:
                return r[m.Infra.CodegenFilePlan].fail(
                    read.error or f"managed file read failed: {path}"
                )
            current = read.value
        expected_sha = u.Cli.sha256_content(rendered)
        current_sha = u.Cli.sha256_content(current) if path.is_file() else ""
        changed = current != rendered
        existing_conflict = changed and path.is_file() and block_existing
        return r[m.Infra.CodegenFilePlan].ok(
            m.Infra.CodegenFilePlan(
                path=path,
                owner=surface.owner,
                policy=surface.policy,
                rendered=rendered,
                expected_sha256=expected_sha,
                current_sha256=current_sha,
                changed=changed,
                blocked=existing_conflict,
                reason=(
                    "existing content conflicts with initial generation"
                    if existing_conflict
                    else ""
                ),
            )
        )

    def plan_managed_file(
        self, root: Path, relative_path: str, rendered: str
    ) -> p.Result[m.Infra.CodegenFilePlan]:
        """Plan one configured managed path through its canonical owner policy."""
        path = Path(relative_path)
        owners = tuple(
            item
            for item in config.Infra.codegen.surfaces.entries
            if Path(item.path) == path
        )
        if len(owners) != 1:
            return r[m.Infra.CodegenFilePlan].fail(
                "managed path must resolve exactly one owner: "
                f"{relative_path} ({len(owners)})"
            )
        owner = owners[0]
        planned = self._file_plan(root, relative_path, rendered, surface=owner)
        if planned.failure:
            return r[m.Infra.CodegenFilePlan].fail(
                planned.error or f"managed file planning failed: {relative_path}"
            )
        return planned

    @staticmethod
    def _beads_ledger_root(workspace_root: Path) -> p.Result[Path]:
        """Resolve the principal checkout owning the workspace ledger."""
        probe = u.Cli.capture(
            [c.Infra.GIT, "rev-parse", "--is-inside-work-tree"], cwd=workspace_root
        )
        if probe.failure or probe.value.strip() != "true":
            return r[Path].ok(workspace_root)
        principal = u.Infra.git_primary_worktree_root(workspace_root)
        if principal.failure:
            return r[Path].fail(
                principal.error or "unable to resolve the principal worktree"
            )
        return r[Path].ok(principal.value)

    @staticmethod
    def _beads_binary(ledger_root: Path) -> p.Result[Path]:
        """Resolve the mise-managed Beads binary pinned by the ledger root."""
        resolved = u.Cli.run_raw(["mise", "which", "bd"], cwd=ledger_root)
        if resolved.failure or resolved.value.exit_code != 0:
            return r[Path].fail(f"mise-managed Beads CLI is unavailable: {ledger_root}")
        binary = Path(resolved.value.stdout.strip())
        if not binary.is_file():
            return r[Path].fail(f"mise-resolved Beads CLI is not a file: {binary}")
        return r[Path].ok(binary)

    @classmethod
    def run_beads_command(
        cls, plan: m.Infra.BeadsPlan, *arguments: str
    ) -> p.Result[p.Cli.CommandOutput]:
        """Run the ledger-root Beads binary, never an ambient PATH resolution."""
        ledger_root = plan.ledger_root
        binary = cls._beads_binary(ledger_root)
        if binary.failure:
            return r[p.Cli.CommandOutput].fail(
                binary.error or "mise-managed Beads CLI is unavailable"
            )
        return u.Cli.run_raw([str(binary.value), *arguments], cwd=ledger_root)

    @staticmethod
    def beads_declaration(
        repository_root: Path,
    ) -> p.Result[m.Infra.BeadsTrackerDeclaration]:
        """Parse the repository's committed tracker declaration, once.

        mro-o0cc: a committed ``.beads/config.yaml`` (e.g. the shared ``mro``
        ledger on the machine-wide Dolt server) is the tracker declaration for
        that repository; deriving the namespace from the repository name and
        rejecting the declared one inverted the SSOT. The file is parsed at
        this boundary into a validated model — absence and an invalid payload
        are failures the caller decides about, never a substituted string.
        """
        config_path = repository_root / ".beads" / "config.yaml"
        if not config_path.is_file():
            return r[m.Infra.BeadsTrackerDeclaration].fail(
                f"repository declares no Beads tracker: {config_path}"
            )
        loaded = u.Cli.yaml_load_mapping(config_path)
        try:
            declaration = m.Infra.BeadsTrackerDeclaration.model_validate({
                "issue_prefix": loaded.get("issue-prefix")
            })
        except c.ValidationError as exc:
            return r[m.Infra.BeadsTrackerDeclaration].fail_op(
                f"Beads tracker declaration is invalid: {config_path}", exc
            )
        return r[m.Infra.BeadsTrackerDeclaration].ok(declaration)

    @classmethod
    def declared_beads_prefix(
        cls, repository_root: Path, *, default_prefix: str
    ) -> p.Result[str]:
        """Return the committed tracker prefix or the new-project default.

        mro-o0cc: a committed ``.beads/config.yaml`` (e.g. the shared ``mro``
        ledger on the machine-wide Dolt server) is the tracker declaration for
        that repository; deriving the namespace from the repository name and
        rejecting the declared one inverted the SSOT; the derived name is only
        the default for repositories without a committed tracker config.
        """
        config_path = repository_root / ".beads" / "config.yaml"
        if not config_path.is_file():
            return r[str].ok(default_prefix)
        declaration = cls.beads_declaration(repository_root)
        if declaration.failure:
            return r[str].fail(
                declaration.error or f"invalid Beads tracker declaration: {config_path}"
            )
        return r[str].ok(declaration.value.issue_prefix)

    @classmethod
    def verify_beads_plan(
        cls, plan: m.Infra.BeadsPlan, *, allow_missing: bool
    ) -> p.Result[bool]:
        """Validate the principal ledger route and fail closed on disagreement.

        Worktrees that route to a principal ledger never own the tracker
        lifecycle: verification is skipped there and re-run at the real tree on
        apply.
        """
        if plan.routes_to_principal_ledger:
            return r[bool].ok(True)
        if os.environ.get(c.Infra.ENV_VAR_GITHUB_ACTIONS) == "true":
            # CI runners are ephemeral and do not carry a live Dolt tracker;
            # the Beads lifecycle is owned by development machines, not CI.
            return r[bool].ok(True)
        if not plan.enabled:
            beads_dir = plan.repository_root / ".beads"
            if beads_dir.exists():
                return r[bool].fail(
                    f"Beads is disabled but tracker state exists: {beads_dir}"
                )
            return r[bool].ok(True)
        ledger_root = plan.ledger_root
        version = cls.run_beads_command(plan, "version")
        if version.failure or version.value.exit_code != 0:
            return r[bool].fail(f"mise-managed Beads CLI is unavailable: {ledger_root}")
        version_parts = version.value.stdout.strip().split()
        match version_parts:
            case ["bd", "version", actual_version, *_]:
                pass
            case _:
                actual_version = ""
        if actual_version != plan.expected_version:
            return r[bool].fail(
                "mise-managed Beads CLI version mismatch: "
                f"{actual_version or '<unparseable>'} != {plan.expected_version}"
            )
        if plan.expected_checksum is not None:
            binary = cls._beads_binary(ledger_root)
            if binary.failure:
                return r[bool].fail(
                    binary.error or "mise-managed Beads CLI is unavailable"
                )
            digest = hashlib.sha256(binary.value.read_bytes()).hexdigest()
            if digest != plan.expected_checksum:
                return r[bool].fail(
                    "mise-managed Beads CLI checksum mismatch: "
                    f"{digest} != {plan.expected_checksum}"
                )
        beads_dir = ledger_root / ".beads"
        if not beads_dir.exists():
            if allow_missing:
                return r[bool].ok(True)
            return r[bool].fail(f"Beads ledger is missing: {beads_dir}")
        if not beads_dir.is_dir():
            return r[bool].fail(f"Beads ledger path is not a directory: {beads_dir}")
        info = cls.run_beads_command(plan, "info", "--json")
        if info.failure or info.value.exit_code != 0:
            return r[bool].fail(f"Beads ledger inspection failed: {beads_dir}")
        parsed = u.Cli.json_parse(info.value.stdout)
        if parsed.failure:
            return r[bool].fail(f"Beads info returned invalid JSON: {beads_dir}")
        payload = u.Cli.json_as_mapping(parsed.value)
        tracker_config = u.Cli.json_deep_mapping(payload, "config")
        issue_prefix = u.Cli.json_pick_str(tracker_config, "issue_prefix")
        if issue_prefix != plan.canonical_prefix:
            return r[bool].fail(
                "Beads namespace mismatch: "
                f"{issue_prefix or '<missing>'} != {plan.canonical_prefix}"
            )
        return r[bool].ok(True)

    @staticmethod
    def _technical_branch(reference: str, patterns: t.StrSequence) -> bool:
        """Match one Git ref against the typed technical-branch policy."""
        short = reference
        for prefix in ("refs/heads/", "refs/remotes/origin/"):
            if short.startswith(prefix):
                short = short.removeprefix(prefix)
                break
        return any(
            fnmatchcase(short, pattern) or fnmatchcase(reference, pattern)
            for pattern in patterns
        )

    @classmethod
    def _branch_ancestry_plan(
        cls, target: m.Infra.RepositoryConformTarget
    ) -> p.Result[m.Infra.BranchAncestryPlan]:
        """Inventory governed refs and prove descent from the provider baseline."""
        root = target.root
        baseline_reference = f"refs/remotes/origin/{target.baseline_branch}"
        baseline_command = (c.Infra.GIT, "rev-parse", "--verify", baseline_reference)
        baseline_result = u.Cli.run_raw(baseline_command, cwd=root)
        if baseline_result.failure:
            return r[m.Infra.BranchAncestryPlan].fail(
                "provider baseline command failed: "
                f"command={' '.join(baseline_command)}; error={baseline_result.error}"
            )
        if baseline_result.value.exit_code != 0:
            return r[m.Infra.BranchAncestryPlan].fail(
                "provider baseline ref is missing: "
                f"{baseline_reference}; command={' '.join(baseline_command)}; "
                f"exit={baseline_result.value.exit_code}; "
                f"stderr={baseline_result.value.stderr.strip() or '<empty>'}"
            )
        baseline_sha = baseline_result.value.stdout.strip()
        current_branch_result = u.Cli.run_raw(
            (c.Infra.GIT, "rev-parse", "--abbrev-ref", "HEAD"), cwd=root
        )
        current_branch_ref = ""
        if current_branch_result.success and current_branch_result.value.exit_code == 0:
            current_branch = current_branch_result.value.stdout.strip()
            if current_branch != "HEAD":
                current_branch_ref = f"refs/heads/{current_branch}"
        refs_command = (
            c.Infra.GIT,
            "for-each-ref",
            "--format=%(refname)%09%(objectname)",
            "refs/heads",
            "refs/remotes/origin",
        )
        refs_result = u.Cli.run_raw(refs_command, cwd=root)
        if refs_result.failure:
            return r[m.Infra.BranchAncestryPlan].fail(
                "cannot enumerate governed refs: "
                f"command={' '.join(refs_command)}; error={refs_result.error}"
            )
        if refs_result.value.exit_code != 0:
            return r[m.Infra.BranchAncestryPlan].fail(
                "cannot enumerate governed refs: "
                f"command={' '.join(refs_command)}; "
                f"exit={refs_result.value.exit_code}; "
                f"stderr={refs_result.value.stderr.strip() or '<empty>'}"
            )
        observations: list[tuple[str, str]] = []
        for line in refs_result.value.stdout.splitlines():
            reference, separator, sha = line.partition("\t")
            if not separator or not reference or not sha:
                return r[m.Infra.BranchAncestryPlan].fail(
                    f"malformed Git ref inventory entry: {line}"
                )
            if reference == "refs/remotes/origin/HEAD":
                continue
            observations.append((reference, sha))
        worktrees_command = (c.Infra.GIT, "worktree", "list", "--porcelain")
        worktrees_result = u.Cli.run_raw(worktrees_command, cwd=root)
        if worktrees_result.failure:
            return r[m.Infra.BranchAncestryPlan].fail(
                "cannot enumerate registered worktrees: "
                f"command={' '.join(worktrees_command)}; "
                f"error={worktrees_result.error}"
            )
        if worktrees_result.value.exit_code != 0:
            return r[m.Infra.BranchAncestryPlan].fail(
                "cannot enumerate registered worktrees: "
                f"command={' '.join(worktrees_command)}; "
                f"exit={worktrees_result.value.exit_code}; "
                f"stderr={worktrees_result.value.stderr.strip() or '<empty>'}"
            )
        worktree_path = ""
        worktree_sha = ""
        worktree_branch = "detached"
        worktree_bare = False
        for line in (*worktrees_result.value.stdout.splitlines(), ""):
            if line.startswith("worktree "):
                worktree_path = line.removeprefix("worktree ")
            elif line.startswith("HEAD "):
                worktree_sha = line.removeprefix("HEAD ")
            elif line.startswith("branch "):
                worktree_branch = line.removeprefix("branch ")
            elif line == "bare":
                worktree_bare = True
            elif not line and worktree_path:
                if worktree_bare:
                    worktree_path = ""
                    worktree_sha = ""
                    worktree_branch = "detached"
                    worktree_bare = False
                    continue
                if not worktree_sha:
                    return r[m.Infra.BranchAncestryPlan].fail(
                        f"worktree has no HEAD: {worktree_path}"
                    )
                if Path(worktree_path).resolve() != root.resolve():
                    worktree_path = ""
                    worktree_sha = ""
                    worktree_branch = "detached"
                    worktree_bare = False
                    continue
                if worktree_branch == "detached":
                    # Detached checkouts (e.g., temporary CI/worktree transactions)
                    # are not governed branch refs; skip them.
                    worktree_path = ""
                    worktree_sha = ""
                    worktree_branch = "detached"
                    worktree_bare = False
                    continue
                observations.append((
                    f"worktree:{worktree_path}:{worktree_branch}",
                    worktree_sha,
                ))
                worktree_path = ""
                worktree_sha = ""
                worktree_branch = "detached"
                worktree_bare = False
        references: list[m.Infra.BranchAncestryRef] = []
        for reference, sha in sorted(observations):
            policy_reference = (
                reference.rpartition(":")[2]
                if reference.startswith("worktree:")
                else reference
            )
            # mro-e9j0.6: ancestry is a development-line rule. Only refs on the
            # governed allowlist are gated; parked releases (0.10/0.11), snapshots
            # and lane branches are inventoried but must never block conform.
            excluded = cls._technical_branch(
                policy_reference, target.technical_branch_patterns
            ) or not cls._technical_branch(
                policy_reference, target.governed_branch_patterns
            )
            # Only enforce ancestry on active checkouts: the current branch and
            # registered worktrees. Shared local/remote branches that are not
            # currently checked out are excluded from this repository-local gate.
            if not excluded and not reference.startswith("worktree:"):
                is_remote = reference.startswith("refs/remotes/")
                is_other_local = (
                    reference.startswith("refs/heads/")
                    and reference != current_branch_ref
                )
                if is_remote or is_other_local:
                    excluded = True
            ancestor: bool | None = None
            if not excluded:
                ancestry_command = (
                    c.Infra.GIT,
                    "merge-base",
                    "--is-ancestor",
                    baseline_sha,
                    sha,
                )
                ancestry_result = u.Cli.run_raw(ancestry_command, cwd=root)
                if ancestry_result.failure:
                    return r[m.Infra.BranchAncestryPlan].fail(
                        "cannot validate branch ancestry: "
                        f"{reference}; command={' '.join(ancestry_command)}; "
                        f"error={ancestry_result.error}"
                    )
                if ancestry_result.value.exit_code not in {0, 1}:
                    return r[m.Infra.BranchAncestryPlan].fail(
                        "Git ancestry validation failed: "
                        f"{reference}; command={' '.join(ancestry_command)}; "
                        f"exit={ancestry_result.value.exit_code}; "
                        f"stderr={ancestry_result.value.stderr.strip() or '<empty>'}"
                    )
                ancestor = ancestry_result.value.exit_code == 0
            references.append(
                m.Infra.BranchAncestryRef(
                    reference=reference, sha=sha, excluded=excluded, ancestor=ancestor
                )
            )
        return r[m.Infra.BranchAncestryPlan].ok(
            m.Infra.BranchAncestryPlan(
                repository_root=root,
                baseline_reference=baseline_reference,
                baseline_sha=baseline_sha,
                references=tuple(references),
            )
        )


__all__: list[str] = ["FlextInfraCodegenConform"]
