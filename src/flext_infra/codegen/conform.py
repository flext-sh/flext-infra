"""Unified, fail-closed conformance for new and existing repositories.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Annotated, override

from flext_core import r
from flext_infra import config, p
from flext_infra.base import s
from flext_infra.constants import c
from flext_infra.deps.modernizer import FlextInfraPyprojectModernizer
from flext_infra.deps.phases.ensure_ruff import FlextInfraEnsureRuffConfigPhase
from flext_infra._utilities.project_managed_artifacts import (
    FlextInfraUtilitiesProjectManagedArtifacts,
)
from flext_infra.models import m
from flext_infra.services.codegen import FlextInfraCodegen
from flext_infra.typings import t
from flext_infra.utilities import u
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector


class FlextInfraCodegenConform(s[m.Infra.CodegenResult]):
    """Plan every selected output, then atomically write only a clean plan."""

    @staticmethod
    def _link_mode(toolchain: m.Infra.ToolchainSpec) -> str:
        """Read link mode from its sole tooling owner."""
        link_mode = toolchain.uv_link_mode
        if not isinstance(link_mode, str):
            msg = "resolved uv link mode must be a string"
            raise TypeError(msg)
        return link_mode

    @classmethod
    def _surface_contract(
        cls, surface: c.Infra.CodegenConformSurface
    ) -> m.Infra.CodegenConformSurfaceContract:
        match surface:
            case c.Infra.CodegenConformSurface.ALL:
                return m.Infra.CodegenConformSurfaceContract(complete_governed=True)
            case c.Infra.CodegenConformSurface.DEPENDENCIES:
                return m.Infra.CodegenConformSurfaceContract(
                    destinations=frozenset({c.Infra.PYPROJECT_FILENAME}),
                    dependencies_only=True,
                    delegates=False,
                    templates=False,
                )
            case c.Infra.CodegenConformSurface.PYPROJECT:
                return m.Infra.CodegenConformSurfaceContract(
                    destinations=frozenset({c.Infra.PYPROJECT_FILENAME}),
                    delegates=False,
                    templates=False,
                )
            case c.Infra.CodegenConformSurface.MAKEFILE:
                return m.Infra.CodegenConformSurfaceContract(
                    destinations=frozenset({c.Infra.MAKEFILE_FILENAME}), pyproject=False
                )
            case _:
                msg = f"Unsupported codegen conform surface: {surface}"
                raise ValueError(msg)

    # NOTE (multi-agent, mro-wkii.17 / agent: codex): this is the only
    # orchestrator for Make/toolchain/source conformance. Rendering stays in
    # flext-cli; Git-source TOML policy and topology detection are composed from
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
        """Run check or apply and require a verified fixed point."""
        request = self.request or m.Infra.CodegenConformRequest(
            root=self.workspace_root
        )
        u.Cli.header("Codegen Conform")
        u.Cli.info(
            f"stage=plan mode={request.mode} scope={request.scope} "
            f"what={request.what} root={request.root}"
        )
        planned = self.plan(request)
        if planned.failure:
            return r[m.Infra.CodegenResult].fail(
                planned.error or "codegen conform planning failed"
            )
        plan = planned.value
        mode = c.Infra.CodegenConformMode(request.mode)
        changed = tuple(file for file in plan.files if file.changed)
        if mode is c.Infra.CodegenConformMode.CHECK:
            if changed:
                paths = ", ".join(str(file.path) for file in changed)
                return r[m.Infra.CodegenResult].fail(f"codegen drift detected: {paths}")
            return r[m.Infra.CodegenResult].ok(m.Infra.CodegenResult(plan=plan))
        written: list[Path] = []
        total_changed = len(changed)
        u.Cli.info(f"stage=apply changed={total_changed}")
        for write_index, file in enumerate(changed, start=1):
            u.Cli.emit_raw(f"  write [{write_index}/{total_changed}] {file.path}\n")
            if file.absent:
                target = file.path.expanduser().resolve()
                try:
                    target.relative_to(plan.request.root.expanduser().resolve())
                except ValueError:
                    return r[m.Infra.CodegenResult].fail(
                        f"absent path escapes repository root: {file.path}"
                    )
                if target.exists():
                    if not target.is_file():
                        return r[m.Infra.CodegenResult].fail(
                            f"absent path is not a regular file: {target}"
                        )
                    removed = r.create_from_callable(
                        lambda path=target: (path.unlink(), path)[1],
                        error_code="E_CODEGEN_ABSENT_UNLINK",
                    )
                    if removed.failure:
                        return r[m.Infra.CodegenResult].fail(
                            removed.error or f"absent path unlink failed: {target}"
                        )
                written.append(file.path)
                continue
            result = u.Cli.atomic_write_text_file(file.path, file.rendered)
            if result.failure:
                return r[m.Infra.CodegenResult].fail(
                    result.error
                    or (
                        f"stage=apply position={write_index}/{total_changed} "
                        f"path={file.path}: atomic write failed"
                    )
                )
            written.append(file.path)
        u.Cli.info("stage=verify-fixed-point")
        verified = self.plan(request)
        if verified.failure:
            return r[m.Infra.CodegenResult].fail(
                verified.error
                or "stage=verify-fixed-point: post-apply conform verification failed"
            )
        verified_plan = verified.value
        residual = tuple(file for file in verified_plan.files if file.changed)
        if residual:
            paths = ", ".join(str(file.path) for file in residual)
            return r[m.Infra.CodegenResult].fail(
                f"codegen apply did not reach a fixed point: {paths}"
            )
        return r[m.Infra.CodegenResult].ok(
            m.Infra.CodegenResult(plan=verified_plan, written_files=tuple(written))
        )

    def plan(
        self, request: m.Infra.CodegenConformRequest
    ) -> p.Result[m.Infra.CodegenPlan]:
        """Build and validate the complete selection without writing."""
        config_spec = config.Infra.codegen
        root = request.root.expanduser().resolve()
        workspace = self.initial_workspace
        if workspace is None:
            workspace_result = FlextInfraWorkspaceDetector.load_workspace_spec(root)
            if workspace_result.failure:
                return r[m.Infra.CodegenPlan].fail(
                    workspace_result.error or "repository metadata load failed"
                )
            workspace = workspace_result.value
        current_repository = workspace.repository
        if self.initial_workspace is None:
            current_target_result = FlextInfraWorkspaceDetector.conform_target(root)
            if current_target_result.failure:
                return r[m.Infra.CodegenPlan].fail(
                    current_target_result.error
                    or "repository conformance target resolution failed"
                )
            current_target = current_target_result.value
            current_repository = current_target.repository
        else:
            topology_result = FlextInfraWorkspaceDetector().detect(root)
            if topology_result.failure:
                return r[m.Infra.CodegenPlan].fail(
                    topology_result.error or "repository topology detection failed"
                )
            current_target = m.Infra.RepositoryConformTarget(
                repository=current_repository,
                root=root,
                topology=topology_result.value,
                managed=True,
                canonical_project_name=current_repository.distribution,
                ci_enabled=True,
            )
        selected = (current_repository,)
        contract = self._surface_contract(c.Infra.CodegenConformSurface(request.what))
        files: list[m.Infra.CodegenFilePlan] = []
        environments: list[m.Infra.UvEnvironmentPlan] = []
        total_repositories = len(selected)
        u.Cli.info(f"stage=plan repositories={total_repositories}")
        for repository_index, repository in enumerate(selected, start=1):
            repository_started = time.monotonic()
            u.Cli.progress(
                repository_index, total_repositories, repository.name, "conform"
            )
            repository_root = root
            if repository_root.exists() and not repository_root.is_dir():
                return r[m.Infra.CodegenPlan].fail(
                    f"declared repository path is not a directory: {repository_root}"
                )
            if not repository_root.is_dir() and self.initial_workspace is None:
                return r[m.Infra.CodegenPlan].fail(
                    f"declared repository checkout is missing: {repository_root}"
                )
            target = current_target
            # mro-j47u (codex): existing repositories cannot reach the scaffold
            # catalog. Project creation is the only template-rendering lifecycle.
            if (
                self.initial_workspace is not None
                and repository.name == workspace.repository.name
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
                    workspace_root=root,
                    repository=repository,
                    target=target,
                    workspace=workspace,
                    codegen=config_spec,
                    contract=contract,
                )
            if repository_plan.failure:
                return r[m.Infra.CodegenPlan].fail(
                    repository_plan.error
                    or (
                        f"stage=plan position={repository_index}/"
                        f"{total_repositories} repository={repository.name}: "
                        f"repository planning failed: {repository_root}"
                    )
                )
            governed = self._complete_governed_plans(
                repository_root, repository_plan.value, config_spec, contract
            )
            if governed.failure:
                return r[m.Infra.CodegenPlan].fail(
                    governed.error
                    or (
                        f"stage=plan position={repository_index}/"
                        f"{total_repositories} repository={repository.name}: "
                        f"artifact ownership planning failed: {repository_root}"
                    )
                )
            files.extend(governed.value)
            environments.append(
                self._uv_environment_plan(root=repository_root, config=config_spec)
            )
            u.Cli.status(
                "conform",
                repository.name,
                result=True,
                elapsed=time.monotonic() - repository_started,
            )
        return r[m.Infra.CodegenPlan].ok(
            m.Infra.CodegenPlan(
                request=request,
                repositories=selected,
                workspace=workspace,
                make_spec=config_spec.make,
                uv_environments=tuple(environments),
                files=tuple(files),
            )
        )

    @staticmethod
    def _complete_governed_plans(
        root: Path,
        planned: t.SequenceOf[m.Infra.CodegenFilePlan],
        codegen: m.Infra.CodegenConfigSpec,
        contract: m.Infra.CodegenConformSurfaceContract,
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Attach ownership metadata and represent every governed root artifact.

        Only the ``ALL`` surface completes the full governed set; the
        pyproject-scoped surfaces (``DEPENDENCIES``/``PYPROJECT``) keep the plan
        restricted to what their own planners already produced.
        """
        governed_by_path = {item.path: item for item in codegen.managed_files}
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
            if (
                governed.policy == "merge"
                and governed.owner == c.Infra.CODEGEN_OWNER_VSCODE
            ):
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
                rendered_gitignore = FlextInfraCodegenConform._render_gitignore(codegen)
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
    def render_project_gitignore(codegen: m.Infra.CodegenConfigSpec) -> p.Result[str]:
        """Render the topology- and project-neutral canonical ``.gitignore``."""
        return FlextInfraCodegenConform._render_gitignore(codegen)

    @staticmethod
    def _render_gitignore(codegen: m.Infra.CodegenConfigSpec) -> p.Result[str]:
        """Render the canonical ``.gitignore`` body via the single template.

        NOTE (mro-jnm1.2): ``codegen new`` renders ``base/gitignore.j2`` with
        the full project context; conform renders the same template with the
        codegen config — both consume the same computed ``gitignore_sections``
        projection, so the body is byte-identical.
        """
        entry = next(
            (
                item
                for item in codegen.templates.entries
                if item.destination == c.Infra.GITIGNORE
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
            / codegen.templates.root
        ).resolve()
        context = m.Infra.GitignoreRenderSpec(
            gitignore_sections=tuple(codegen.gitignore_sections)
        )
        return u.Cli.template_render(templates_root / entry.source, context)

    @staticmethod
    def _planned_python_dirs(
        root: Path, entries: t.SequenceOf[p.Infra.TemplateEntrySpec]
    ) -> t.StrSequence:
        """Return every Python root present after the atomic codegen plan."""
        generated_roots = {
            Path(entry.destination).parts[0]
            for entry in entries
            if entry.delegate == "render" and Path(entry.destination).parts
        }
        return tuple(
            directory
            for directory in config.Infra.tooling.tools.pyright.path_rules.env_dirs
            if (root / directory).is_dir() or directory in generated_roots
        )

    def _plan_scaffold_repository(
        self,
        *,
        root: Path,
        repository: m.Infra.RepositoryRef,
        target: m.Infra.RepositoryConformTarget,
        workspace: m.Infra.WorkspaceSpec,
        codegen: m.Infra.CodegenConfigSpec,
        contract: m.Infra.CodegenConformSurfaceContract,
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Render the complete scaffold for ``codegen new`` only."""
        project = workspace.project
        pyproject = root / c.Infra.PYPROJECT_FILENAME
        # mro-j47u (codex): new and existing repositories share the exact same
        # root-scoped modernizer pipeline, so first generation is a fixed point.
        # The selected repository consumes its own tooling contract before the
        # atomic scaffold creates files on disk.
        tooling_root = target.root
        modernizer = FlextInfraPyprojectModernizer(
            workspace_root=tooling_root, skip_check=True
        )
        declared_python_dirs = self._planned_python_dirs(
            root, codegen.templates.entries
        )
        tooling_result = modernizer.resolve_tooling_context(
            project_name=repository.distribution,
            package_name=project.package_name,
            path=pyproject,
            declared_python_dirs=declared_python_dirs,
            declared_python_dirs_are_complete=True,
        )
        if tooling_result.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                tooling_result.error or f"tooling render failed: {pyproject}"
            )
        context_result = self._project_render_context(
            repository,
            target,
            workspace,
            codegen,
            tooling_runtime=tooling_result.value,
            repository_root=pyproject.parent,
        )
        if context_result.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                context_result.error or "project render context is invalid"
            )
        context = context_result.value
        uv_exclude_dependencies = tuple(
            item
            for item in codegen.uv_exclude_dependencies
            if item.project == repository.distribution
        )
        planned: list[m.Infra.CodegenFilePlan] = []
        templates_root = (
            self._package_root() / "templates" / codegen.templates.root
        ).resolve()
        seen_destinations: set[str] = set()
        for entry in codegen.templates.entries:
            if (
                contract.destinations is not None
                and entry.destination not in contract.destinations
            ):
                continue
            source = (templates_root / entry.source).resolve()
            if not source.is_relative_to(templates_root) or not source.is_file():
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    f"template source is missing or escapes its root: {entry.source}"
                )
            destination = entry.destination.format(
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
        for entry in codegen.templates.entries:
            if (
                contract.destinations is not None
                and entry.destination not in contract.destinations
            ):
                continue
            if not contract.delegates:
                continue
            # mro-i6nq.10: One formatted path governs validation and planning.
            destination = entry.destination.format(
                package_name=context.package_name, ns=context.ns
            )
            if entry.delegate != "render":
                continue
            if destination == c.Infra.PYPROJECT_FILENAME:
                continue
            preserved = self._repository_owned_workflow_plan(root, destination)
            if preserved.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    preserved.error or f"workflow provenance read failed: {destination}"
                )
            if preserved.value:
                planned.extend(preserved.value)
                continue
            artifact_context = self._artifact_render_context(
                dist=context.dist,
                repository=repository,
                repository_root=root,
                target=target,
                workspace=workspace,
                codegen=codegen,
                destination=destination,
                tooling_runtime=tooling_result.value,
                project_context=context,
            )
            if artifact_context.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    artifact_context.error
                    or f"artifact render context failed: {destination}"
                )
            rendered = u.Cli.template_render(
                templates_root / entry.source, artifact_context.value
            )
            if rendered.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    rendered.error
                    or (
                        f"stage=templates repository={repository.name} "
                        f"template={entry.source}: template render failed"
                    )
                )
            validated = self._validate_rendered_template(
                root=root,
                source=entry.source,
                destination=destination,
                rendered=rendered.value,
            )
            if validated.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    validated.error or f"rendered template is invalid: {entry.source}"
                )
            rendered_content = self._compose_project_artifact(
                root, destination, validated.value
            )
            if rendered_content.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    rendered_content.error
                    or f"managed artifact composition failed: {destination}"
                )
            file_plan = self._file_plan(root, destination, rendered_content.value)
            if file_plan.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    file_plan.error
                    or f"managed file planning failed: {entry.destination}"
                )
            planned.append(file_plan.value)
        if not contract.pyproject:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(tuple(planned))
        pyproject_entry = next(
            (
                item
                for item in codegen.templates.entries
                if item.destination == c.Infra.PYPROJECT_FILENAME
                and item.delegate == "render"
            ),
            None,
        )
        if pyproject_entry is None:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                "pyproject template is missing from codegen configuration"
            )
        pyproject_render = u.Cli.template_render(
            templates_root / pyproject_entry.source, context
        )
        if pyproject_render.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                pyproject_render.error or "pyproject template render failed"
            )
        validated_pyproject = self._validate_rendered_template(
            root=root,
            source=pyproject_entry.source,
            destination=c.Infra.PYPROJECT_FILENAME,
            rendered=pyproject_render.value,
        )
        if validated_pyproject.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                validated_pyproject.error or "rendered pyproject template is invalid"
            )
        initial_tooling = modernizer.conform_source(
            validated_pyproject.value,
            path=pyproject,
            format_source=False,
            declared_python_dirs=declared_python_dirs,
            declared_python_dirs_are_complete=True,
        )
        if initial_tooling.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                initial_tooling.error or f"initial tooling conform failed: {pyproject}"
            )
        prepared_result = u.Infra.pyproject_conform(
            initial_tooling.value,
            providers=codegen.providers,
            workspace=workspace,
            toolchain=codegen.toolchain,
            required_dev_dependencies=codegen.scaffold.project.dev,
            uv_link_mode=None,
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
            declared_python_dirs_are_complete=True,
        )
        if final_tooling.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                final_tooling.error or f"final tooling conform failed: {pyproject}"
            )
        pyproject_plan = self._file_plan(
            root, c.Infra.PYPROJECT_FILENAME, final_tooling.value
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
        contract: m.Infra.CodegenConformSurfaceContract,
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Conform every declared managed surface in an existing repository."""
        u.Cli.info(f"  stage=pyproject repository={repository.name}")
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
        uv_exclude_dependencies = tuple(
            item
            for item in codegen.uv_exclude_dependencies
            if item.project == repository.distribution
        )
        if contract.dependencies_only:
            dependency_result = u.Infra.pyproject_dependencies_conform(
                pyproject_read.value, providers=codegen.providers, workspace=workspace
            )
            if dependency_result.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    dependency_result.error
                    or f"pyproject dependency conform failed: {pyproject}"
                )
            dependency_plan = self._file_plan(
                root, c.Infra.PYPROJECT_FILENAME, dependency_result.value
            )
            if dependency_plan.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    dependency_plan.error
                    or f"pyproject dependency planning failed: {pyproject}"
                )
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok((dependency_plan.value,))
        modernizer = FlextInfraPyprojectModernizer(
            workspace_root=workspace_root, skip_check=True
        )
        declared_python_dirs = self._planned_python_dirs(
            root, codegen.templates.entries
        )
        tooling_context = modernizer.resolve_tooling_context(
            project_name=repository.distribution,
            package_name=metadata.value.package_name,
            path=pyproject,
            declared_python_dirs=declared_python_dirs,
            declared_python_dirs_are_complete=True,
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
            toolchain=codegen.toolchain,
            required_dev_dependencies=codegen.scaffold.project.dev,
            uv_link_mode=None,
            uv_exclude_dependencies=uv_exclude_dependencies,
        )
        if prepared_result.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                prepared_result.error or f"pyproject preparation failed: {pyproject}"
            )
        # Dependency topology is conformed before tooling so the modernizer is
        # the final owner of TOML ordering, comments, and type-checker settings.
        # It preserves the already canonical dependency source declarations.
        # Managed roots this plan materializes (tests/) count as analyzer roots
        # already in the plan, so apply and its verification are one fixed point.
        tooling_result = modernizer.conform_source(
            prepared_result.value,
            path=pyproject,
            declared_python_dirs=declared_python_dirs,
            declared_python_dirs_are_complete=True,
        )
        if tooling_result.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                tooling_result.error or f"tooling conform failed: {pyproject}"
            )
        pyproject_plan = self._file_plan(
            root, c.Infra.PYPROJECT_FILENAME, tooling_result.value
        )
        if pyproject_plan.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                pyproject_plan.error or f"pyproject planning failed: {pyproject}"
            )
        planned = [pyproject_plan.value]
        if not contract.templates:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(tuple(planned))
        # NOTE(mro-p68a.5, agent codex): managed_files is the existing-tree
        # ownership SSOT; templates.entries remains the single render manifest.
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
        contract: m.Infra.CodegenConformSurfaceContract,
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Render configured overwrite-owned templates for an existing tree."""
        u.Cli.info(f"  stage=templates repository={repository.name}")
        templates_root = (
            self._package_root() / "templates" / codegen.templates.root
        ).resolve()
        planned: list[m.Infra.CodegenFilePlan] = []
        for managed in codegen.managed_files:
            if not target.ci_enabled and managed.path.parts[:2] == (
                ".github",
                "workflows",
            ):
                continue
            if (
                contract.destinations is not None
                and managed.path.as_posix() not in contract.destinations
            ):
                continue
            if managed.policy in {"delegated", "manual"} or managed.path == Path(
                c.Infra.PYPROJECT_FILENAME
            ):
                continue
            entries = tuple(
                entry
                for entry in codegen.templates.entries
                if entry.destination == managed.path.as_posix()
                and entry.delegate == "render"
            )
            if not entries:
                continue
            if len(entries) != 1:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    f"managed file requires exactly one render template: {managed.path}"
                )
            entry = entries[0]
            u.Cli.emit_raw(f"  template {entry.source} -> {entry.destination}\n")
            relative = Path(entry.destination)
            if relative.is_absolute() or ".." in relative.parts:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    f"managed destination escapes repository root: {entry.destination}"
                )
            path = (root / relative).resolve()
            try:
                path.relative_to(root.resolve())
            except ValueError:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    f"managed destination escapes repository root: {entry.destination}"
                )
            if managed.policy == "create-only" and path.is_file():
                current = u.Cli.files_read_text(path)
                if current.failure:
                    return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                        current.error or f"managed file read failed: {path}"
                    )
                file_plan = self._file_plan(root, entry.destination, current.value)
                if file_plan.failure:
                    return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                        file_plan.error
                        or f"managed file planning failed: {entry.destination}"
                    )
                planned.append(file_plan.value)
                continue
            if managed.policy == "create-only" and path.exists():
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    f"create-only destination is not a regular file: {path}"
                )
            if managed.policy == "create-only":
                continue
            preserved = self._repository_owned_workflow_plan(root, entry.destination)
            if preserved.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    preserved.error
                    or f"workflow provenance read failed: {entry.destination}"
                )
            if preserved.value:
                planned.extend(preserved.value)
                continue
            artifact_context = self._artifact_render_context(
                dist=repository.distribution,
                repository=repository,
                repository_root=root,
                target=target,
                workspace=workspace,
                codegen=codegen,
                destination=entry.destination,
                tooling_runtime=tooling_runtime,
                project_context=None,
            )
            if artifact_context.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    artifact_context.error
                    or f"managed artifact context failed: {entry.destination}"
                )
            rendered = u.Cli.template_render(
                templates_root / entry.source, artifact_context.value
            )
            if rendered.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    rendered.error or f"template render failed: {entry.source}"
                )
            validated = self._validate_rendered_template(
                root=root,
                source=entry.source,
                destination=entry.destination,
                rendered=rendered.value,
            )
            if validated.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    validated.error or f"rendered template is invalid: {entry.source}"
                )
            rendered_content = validated.value
            composed = self._compose_project_artifact(
                root, entry.destination, rendered_content
            )
            if composed.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    composed.error
                    or f"managed artifact composition failed: {entry.destination}"
                )
            rendered_content = composed.value
            file_plan = self._file_plan(root, entry.destination, rendered_content)
            if file_plan.failure:
                return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                    file_plan.error
                    or f"managed file planning failed: {entry.destination}"
                )
            planned.append(file_plan.value)
        return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(tuple(planned))

    @staticmethod
    def _compose_project_artifact(
        repository_root: Path, destination: str, rendered: str
    ) -> p.Result[str]:
        """Apply typed project overlays after canonical template rendering."""
        if destination != c.Infra.MISE_TOML_FILENAME:
            return r[str].ok(rendered)
        return FlextInfraUtilitiesProjectManagedArtifacts.compose_mise_toml(
            repository_root, rendered
        )

    @staticmethod
    def _validate_rendered_template(
        *, root: Path, source: Path, destination: str, rendered: str
    ) -> p.Result[str]:
        """Reject unresolved Git conflict fences before any artifact is written."""
        for line_number, line in enumerate(rendered.splitlines(), start=1):
            marker = next(
                (
                    prefix
                    for prefix in c.Infra.MERGE_CONFLICT_MARKER_PREFIXES
                    if line.startswith(prefix)
                ),
                None,
            )
            if marker is not None:
                return r[str].fail(
                    "rendered template contains merge conflict marker: "
                    f"source={source}; destination={root / destination}; "
                    f"root={root}; line={line_number}; marker={line}"
                )
        return r[str].ok(rendered)

    @staticmethod
    def _infra_repository() -> p.Result[m.Infra.RepositoryRef]:
        """Derive the published infrastructure CLI source from its provider."""
        return r[m.Infra.RepositoryRef].ok(
            u.Infra.derived_repository_ref(
                config.Infra.name, provider=config.Infra.codegen.providers[0]
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

    def _artifact_render_context(
        self,
        *,
        dist: str,
        repository: m.Infra.RepositoryRef,
        repository_root: Path,
        target: m.Infra.RepositoryConformTarget,
        workspace: m.Infra.WorkspaceSpec,
        codegen: m.Infra.CodegenConfigSpec,
        destination: str,
        tooling_runtime: m.Infra.ToolingRuntimeContext,
        project_context: m.Infra.ProjectRenderContext | None,
    ) -> p.Result[p.Model]:
        """Resolve one governed artifact to its canonical typed render input."""
        if destination == c.Infra.GITIGNORE:
            return r[p.Model].ok(
                m.Infra.GitignoreRenderSpec(
                    gitignore_sections=tuple(codegen.gitignore_sections)
                )
            )
        if destination == "sgconfig.yml":
            # Why (ai-hub-qwoc): the ast-grep contract is identical for every
            # governed repository, so it renders straight from the codegen SSOT.
            return r[p.Model].ok(codegen.sgconfig)
        if destination == ".pre-commit-config.yaml":
            return r[p.Model].ok(
                m.Infra.MakeWorkflowRenderSpec(dist=dist, make=codegen.make)
            )
        if destination in {".envrc", ".mise.toml", ".python-version"}:
            return r[p.Model].ok(codegen.toolchain)
        if destination.startswith(".github/"):
            provider = self._repository_provider(repository, codegen)
            if provider.failure:
                return r[p.Model].fail(
                    provider.error or "workflow provider resolution failed"
                )
            # Why: ci.yml.j2 iterates this to build its push/pull_request branch
            # filters, so an unsupplied value fails the render outright. The
            # repository's own integration branch is the only branch this layer
            # can name from resolved data; a fleet-wide list hardcoded here would
            # make every repository trigger on branches it does not have.
            branch = provider.value.branch
            return r[p.Model].ok(
                m.Infra.GithubWorkflowRenderSpec(
                    dist=dist,
                    repository_branch=branch,
                    ci_trigger_branches=(branch, "main"),
                    python_version=codegen.toolchain.python_version,
                    mise_version=codegen.toolchain.mise_version,
                    dependency_cooldown_days=(
                        codegen.toolchain.dependency_cooldown_days
                    ),
                    github_actions=codegen.github_actions,
                    make=codegen.make,
                    # Why: dependabot.yml.j2 branches on this and the model
                    # declares it, but the .github/ spec never supplied it, so
                    # every render died with "'has_devcontainer' is undefined".
                    # Dependabot rejects its ENTIRE config when an ecosystem
                    # names a directory that is absent, so this is read from the
                    # checkout rather than declared: a stale flag would silently
                    # disable Dependabot for the repository.
                    has_devcontainer=(repository_root / ".devcontainer").is_dir(),
                    checkout_submodules=codegen.checkout_submodules,
                )
            )
        destination_path = Path(destination)
        if (
            destination_path.parent.as_posix() == "tests/fixtures/ci/docker"
            and destination_path.suffix == ".Dockerfile"
        ):
            return r[p.Model].ok(
                m.Infra.DistroDockerRenderSpec(
                    package_name=dist.replace("-", "_"),
                    python_version=codegen.toolchain.python_version,
                    make=codegen.make,
                )
            )
        if destination == c.Infra.MAKEFILE_FILENAME:
            infra_repository = self._infra_repository()
            if infra_repository.failure:
                return r[p.Model].fail(
                    infra_repository.error
                    or "infrastructure CLI repository resolution failed"
                )
            infra_provider = self._repository_provider(infra_repository.value, codegen)
            if infra_provider.failure:
                return r[p.Model].fail(
                    infra_provider.error or "infrastructure provider resolution failed"
                )
            return r[p.Model].ok(
                m.Infra.MakefileRenderSpec(
                    pytest=config.Infra.tooling.tools.pytest,
                    dist=dist,
                    infra_cli=config.Infra.name,
                    infra_repository=infra_repository.value,
                    infra_repository_branch=infra_provider.value.branch,
                    uv_version=codegen.toolchain.uv_version,
                    mise_version=codegen.toolchain.mise_version,
                    mise_lock_platforms=codegen.toolchain.mise_lock_platforms,
                    uv_link_mode=FlextInfraCodegenConform._link_mode(codegen.toolchain),
                    uv_exclude_newer=codegen.toolchain.uv_exclude_newer,
                    dependency_cooldown_exclusions=(
                        codegen.toolchain.dependency_cooldown_exclusions
                    ),
                    dependency_cooldown_overrides=(
                        codegen.toolchain.dependency_cooldown_overrides
                    ),
                    make=codegen.make,
                    mypy_memory_limit_mb=c.Infra.MYPY_MEMORY_LIMIT_MB_DEFAULT,
                    mypy_timeout_seconds=c.Infra.MYPY_TIMEOUT_SECONDS_DEFAULT,
                    mypy_timeout_exit_code=c.Infra.PROCESS_TIMEOUT_EXIT_CODE,
                    mypy_signal_exit_offset=c.Infra.PROCESS_SIGNAL_EXIT_OFFSET,
                    prlimit_command=c.Infra.PRLIMIT_COMMAND,
                    prlimit_address_space_option=(c.Infra.PRLIMIT_ADDRESS_SPACE_OPTION),
                    timeout_command=c.Infra.TIMEOUT_COMMAND,
                    timeout_kill_after_seconds=c.Infra.TIMEOUT_KILL_AFTER_SECONDS,
                    pytest_process_timeout_seconds=(
                        config.Infra.tooling.tools.pytest.process_timeout_seconds
                    ),
                )
            )
        if project_context is not None:
            return r[p.Model].ok(project_context)
        context_result = self._project_render_context(
            repository,
            target,
            workspace,
            codegen,
            tooling_runtime=tooling_runtime,
            repository_root=repository_root,
        )
        if context_result.failure:
            return r[p.Model].fail(
                context_result.error
                or f"managed artifact context failed: {destination}"
            )
        return r[p.Model].ok(context_result.value)

    @staticmethod
    def make_render_context(
        repository: m.Infra.RepositoryRef,
        codegen: m.Infra.CodegenConfigSpec,
        *,
        tooling_runtime: m.Infra.ToolingRuntimeContext,
    ) -> p.Result[m.Infra.MakeRenderContext]:
        """Build the typed context consumed by the generated Makefile."""
        infra_repository = FlextInfraCodegenConform._infra_repository()
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
        return r[m.Infra.MakeRenderContext].ok(
            m.Infra.MakeRenderContext(
                pytest=config.Infra.tooling.tools.pytest,
                make=codegen.make,
                mypy_memory_limit_mb=c.Infra.MYPY_MEMORY_LIMIT_MB_DEFAULT,
                mypy_timeout_seconds=c.Infra.MYPY_TIMEOUT_SECONDS_DEFAULT,
                mypy_timeout_exit_code=c.Infra.PROCESS_TIMEOUT_EXIT_CODE,
                mypy_signal_exit_offset=c.Infra.PROCESS_SIGNAL_EXIT_OFFSET,
                prlimit_command=c.Infra.PRLIMIT_COMMAND,
                prlimit_address_space_option=c.Infra.PRLIMIT_ADDRESS_SPACE_OPTION,
                timeout_command=c.Infra.TIMEOUT_COMMAND,
                timeout_kill_after_seconds=c.Infra.TIMEOUT_KILL_AFTER_SECONDS,
                tooling_runtime=tooling_runtime,
                dist=repository.distribution,
                infra_cli=config.Infra.name,
                infra_repository=infra_repository.value,
                infra_repository_branch=infra_provider.value.branch,
                python_version=codegen.toolchain.python_version,
                uv_version=codegen.toolchain.uv_version,
                mise_version=codegen.toolchain.mise_version,
                mise_lock_platforms=codegen.toolchain.mise_lock_platforms,
                uv_link_mode=FlextInfraCodegenConform._link_mode(codegen.toolchain),
                uv_exclude_newer=codegen.toolchain.uv_exclude_newer,
                dependency_cooldown_exclusions=(
                    codegen.toolchain.dependency_cooldown_exclusions
                ),
                dependency_cooldown_overrides=(
                    codegen.toolchain.dependency_cooldown_overrides
                ),
                # ProjectRenderContext replaces this with the composed map.
                # Pass the neutral value explicitly so Pydantic never deep-copies
                # the MappingProxyType model default while building the base.
                ruff_per_file_ignores={},
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
        repository_root: Path,
    ) -> p.Result[m.Infra.ProjectRenderContext]:
        """Build the complete typed context consumed by project templates."""
        project = workspace.project
        upstream_dependencies = next(
            (
                item
                for item in codegen.scaffold.project.upstreams
                if item.upstream == project.upstream
            ),
            None,
        )
        if upstream_dependencies is None:
            return r[m.Infra.ProjectRenderContext].fail(
                f"unsupported scaffold upstream: {project.upstream}"
            )
        if project.license not in codegen.scaffold.project.supported_licenses:
            supported = ", ".join(codegen.scaffold.project.supported_licenses)
            return r[m.Infra.ProjectRenderContext].fail(
                f"unsupported scaffold license: {project.license}; "
                f"supported licenses: {supported}"
            )
        make_context = FlextInfraCodegenConform.make_render_context(
            repository, codegen, tooling_runtime=tooling_runtime
        )
        if make_context.failure:
            return r[m.Infra.ProjectRenderContext].fail(
                make_context.error or "Make render context resolution failed"
            )
        repository_provider = FlextInfraCodegenConform._repository_provider(
            repository, codegen
        )
        if repository_provider.failure:
            return r[m.Infra.ProjectRenderContext].fail(
                repository_provider.error or "repository provider resolution failed"
            )
        flext_provider = repository_provider.value
        packaged_data_dirs = tuple(
            data_dir
            for data_dir in config.Infra.tooling.tools.hatch.packaged_data_dirs
            if any(
                Path(entry.destination).parts
                and Path(entry.destination).parts[0] == data_dir
                for entry in codegen.templates.entries
            )
        )
        return r[m.Infra.ProjectRenderContext].ok(
            m.Infra.ProjectRenderContext(
                **make_context.value.model_dump(
                    by_alias=True,
                    exclude={"ruff_per_file_ignores"},
                    exclude_computed_fields=True,
                ),
                scaffold=codegen.scaffold,
                gitignore_sections=tuple(codegen.gitignore_sections),
                upstream_dependencies=upstream_dependencies,
                tooling=config.Infra.tooling,
                # Why: the fleet policy alone is not the effective Ruff contract.
                # A repository may carry an operator-authorized exemption in its
                # own config/*.yaml ManagedArtifacts block, and ensure_ruff
                # composes the two when it edits a pyproject in place. The
                # template rendered only the fleet map, so a full render silently
                # dropped the local overlay -- flext-infra's own _rope exemption
                # disappeared on every conform and returned 12 SLF001 findings
                # the operator had already ruled on. Compose here so both paths
                # produce the same effective map.
                ruff_per_file_ignores=(
                    FlextInfraEnsureRuffConfigPhase.compose_per_file_ignores(
                        repository_root
                    )
                ),
                environment_path_prepends=(codegen.toolchain.environment_path_prepends),
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
                qlty_version=codegen.toolchain.qlty_version,
                taplo_version=codegen.toolchain.taplo_version,
                ast_grep_version=codegen.toolchain.ast_grep_version,
                gitleaks_version=codegen.toolchain.gitleaks_version,
                tokei_version=codegen.toolchain.tokei_version,
                author_name=project.author_name,
                author_email=project.author_email,
                repository=project.homepage,
                homepage=project.homepage,
                documentation=project.documentation,
                flext_git_base_url=flext_provider.base_url,
                flext_git_branch=flext_provider.branch,
                repository_provider=repository.provider,
                repository_git_url=repository.url,
                repository_branch=repository_provider.value.branch,
                year=project.year,
            )
        )

    def _file_plan(
        self, root: Path, relative_path: str, rendered: str
    ) -> p.Result[m.Infra.CodegenFilePlan]:
        """Compare one expected output and mark whether it changed."""
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
        return r[m.Infra.CodegenFilePlan].ok(
            m.Infra.CodegenFilePlan(
                path=path,
                rendered=rendered,
                expected_sha256=expected_sha,
                current_sha256=current_sha,
                changed=changed,
                blocked=False,
                reason="",
            )
        )

    @staticmethod
    def _repository_owned_workflow_plan(
        root: Path, relative_path: str
    ) -> p.Result[t.SequenceOf[m.Infra.CodegenFilePlan]]:
        """Preserve an existing workflow unless it declares managed provenance."""
        relative = Path(relative_path)
        if relative.parts[:2] != (".github", "workflows"):
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(())
        path = root / relative
        if not path.exists():
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(())
        if not path.is_file():
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                f"workflow destination is not a regular file: {path}"
            )
        read = u.Cli.files_read_text(path)
        if read.failure:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].fail(
                read.error or f"workflow provenance read failed: {path}"
            )
        if c.Infra.WORKFLOW_MANAGED_PROVENANCE in read.value:
            return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok(())
        digest = u.Cli.sha256_content(read.value)
        return r[t.SequenceOf[m.Infra.CodegenFilePlan]].ok((
            m.Infra.CodegenFilePlan(
                path=path,
                rendered=read.value,
                expected_sha256=digest,
                current_sha256=digest,
                changed=False,
                blocked=False,
                reason="repository-owned workflow has no [MANAGED] provenance",
            ),
        ))

    @staticmethod
    def _uv_environment_plan(
        *, root: Path, config: m.Infra.CodegenConfigSpec
    ) -> m.Infra.UvEnvironmentPlan:
        """Describe this repository's exact local setup."""
        return m.Infra.UvEnvironmentPlan(
            project_root=root,
            environment_root=root,
            lock_path=root / c.Infra.UV_LOCK_FILENAME,
            python_version=config.toolchain.python_version,
            groups=("dev", "codegen"),
            editable_repositories=(),
        )


__all__: list[str] = ["FlextInfraCodegenConform"]
