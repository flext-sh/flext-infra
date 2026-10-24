"""Conformance repository selection and checkout topology resolution.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, p, r, t
from flext_infra.codegen import FlextInfraCodegenPreconditions
from flext_infra.workspace import FlextInfraWorkspaceDetector


class FlextInfraCodegenConformPlanTopologyMixin:
    """Resolve the selected repositories, their checkouts, and planning targets."""

    if TYPE_CHECKING:
        initial_workspace: m.Infra.WorkspaceSpec | None

        def _record_file_failure(
            self,
            path: Path,
            error: str,
            *,
            exception: BaseException | None = None,
        ) -> None: ...

    def _planning_workspace(
        self,
        request: m.Infra.CodegenConformRequest,
        root: Path,
        *,
        inputs: m.Infra.CodegenInputs,
    ) -> p.Result[
        t.Triple[
            m.Infra.WorkspaceSpec,
            m.Infra.RepositoryConformTarget,
            m.Infra.RepositoryRef,
        ]
    ]:
        """Load the planning workspace and its current conformance target.

        Returns:
            The resulting ``p.Result[t.Triple[m.Infra.WorkspaceSpec,
                m.Infra.RepositoryConformTarget, m.Infra.RepositoryRef]]``.

        """
        result_type = r[
            t.Triple[
                m.Infra.WorkspaceSpec,
                m.Infra.RepositoryConformTarget,
                m.Infra.RepositoryRef,
            ]
        ]
        workspace = self.initial_workspace
        if workspace is None:
            workspace_result = FlextInfraWorkspaceDetector.load_workspace_spec(
                root,
                inputs=inputs,
                allow_unprovisioned_members=(
                    request.what in c.Infra.ALLOW_UNPROVISIONED_SURFACES
                ),
            )
            if workspace_result.failure:
                return result_type.from_failure(workspace_result)
            workspace = workspace_result.value
        current_repository = workspace.repository
        if (
            self.initial_workspace is None
            and request.what not in c.Infra.DECLARED_TARGET_SURFACES
        ):
            current_target_result = FlextInfraWorkspaceDetector.conform_target(
                root,
                workspace,
                inputs=inputs,
            )
            if current_target_result.failure:
                return result_type.from_failure(current_target_result)
            current_target = current_target_result.value
            current_repository = current_target.repository
        else:
            current_target = m.Infra.RepositoryConformTarget(
                repository=current_repository,
                root=root,
                toolchain_root=root,
                make_profile=current_repository.role,
                beads=workspace.beads,
                project=workspace.project,
                canonical_project_name=current_repository.distribution,
                ci_enabled=True,
                publishes_release=current_repository.publishes_release,
                gascity_enabled=workspace.gascity_enabled,
                external_dependency_paths=workspace.external_dependency_paths,
            )
        return result_type.ok((workspace, current_target, current_repository))

    def _repository_planning_inputs(
        self,
        repository_root: Path,
        workspace: m.Infra.WorkspaceSpec,
        current_target: m.Infra.RepositoryConformTarget,
        repository: m.Infra.RepositoryRef,
        *,
        inputs: m.Infra.CodegenInputs,
    ) -> p.Result[
        t.Triple[
            Path,
            m.Infra.RepositoryConformTarget,
            m.Infra.WorkspaceSpec,
        ]
    ]:
        """Resolve one repository's checkout root, target, and local workspace.

        Returns:
            The resulting ``p.Result[t.Triple[Path,
                m.Infra.RepositoryConformTarget, m.Infra.WorkspaceSpec]]``.

        """
        result_type = r[
            t.Triple[
                Path,
                m.Infra.RepositoryConformTarget,
                m.Infra.WorkspaceSpec,
            ]
        ]
        is_current_repository = repository.name == current_target.repository.name
        if is_current_repository:
            return result_type.ok(
                (repository_root, current_target, workspace),
            )
        local = self._member_local_workspace(
            workspace,
            repository,
            repository_root,
            inputs=inputs,
        )
        if local.failure:
            return result_type.from_failure(local)
        local_workspace = local.value
        target_result = FlextInfraWorkspaceDetector.conform_target(
            repository_root,
            local_workspace,
            inputs=inputs,
        )
        if target_result.failure:
            return result_type.from_failure(target_result)
        target = target_result.value.model_copy(
            update={"toolchain_root": current_target.toolchain_root},
        )
        if repository.path != Path():
            target = target.model_copy(update={"repository": repository})
        return result_type.ok((repository_root, target, local_workspace))

    def _resolved_repository_root(
        self,
        root: Path,
        workspace: m.Infra.WorkspaceSpec,
        current_target: m.Infra.RepositoryConformTarget,
        repository: m.Infra.RepositoryRef,
    ) -> p.Result[Path]:
        """Resolve and authenticate one repository's checkout root.

        Returns:
            The resulting ``p.Result[Path]``.

        """
        result_type = r[Path]
        is_current_repository = repository.name == current_target.repository.name
        if is_current_repository:
            repository_root = current_target.root
            if repository_root != root:
                return result_type.fail(
                    "current conformance target differs from the requested root: "
                    f"{repository_root} != {root}",
                )
            return result_type.ok(repository_root)
        # The governing root is the requested checkout, never the
        # previous iteration's member: resolving the second declared
        # repository against the first produced <root>/alpha/beta.
        repository_root_result = self._repository_root(root, workspace, repository)
        if repository_root_result.failure:
            return result_type.from_failure(repository_root_result)
        repository_root = repository_root_result.value
        if repository_root.exists() and not repository_root.is_dir():
            return result_type.fail(
                f"declared repository path is not a directory: {repository_root}",
            )
        if not repository_root.is_dir() and self.initial_workspace is None:
            return result_type.fail(
                f"declared repository checkout is missing: {repository_root}",
            )
        return result_type.ok(repository_root)

    @staticmethod
    def _member_local_workspace(
        workspace: m.Infra.WorkspaceSpec,
        repository: m.Infra.RepositoryRef,
        repository_root: Path,
        *,
        inputs: m.Infra.CodegenInputs,
    ) -> p.Result[m.Infra.WorkspaceSpec]:
        """Load the local workspace a declared member plans from.

        Returns:
            The resulting ``p.Result[m.Infra.WorkspaceSpec]``.

        """
        declared_member = FlextInfraWorkspaceDetector.load_workspace_spec(
            repository_root,
            inputs=inputs,
        )
        if declared_member.failure or repository.path == Path():
            return declared_member
        # The parent owns topology; the member owns its local project metadata.
        return r[m.Infra.WorkspaceSpec].ok(
            m.Infra.WorkspaceSpec(
                name=repository.name,
                docs_audit=declared_member.value.docs_audit,
                beads=workspace.beads,
                repository=repository.model_copy(update={"path": Path()}),
                project=declared_member.value.project,
                namespace_scan_dirs=declared_member.value.namespace_scan_dirs,
                candidate_dependencies=workspace.candidate_dependencies,
            ),
        )

    def _bind_codegen_sources(
        self,
        files: t.SequenceOf[m.Infra.CodegenFilePlan],
        inputs: m.Infra.CodegenInputs,
    ) -> t.VariadicTuple[m.Infra.CodegenFilePlan]:
        """Bind each file to the same captured configuration without duplicate sources.

        Returns:
            Valid file plans; source conflicts retain their target issue and cause.

        """
        complete: list[m.Infra.CodegenFilePlan] = []
        for file in files:
            sources = FlextInfraCodegenPreconditions.unique_states(
                (*file.source_states, *inputs.sources),
            )
            if sources.failure:
                self._record_file_failure(
                    file.path,
                    sources.error or "configuration source identity conflicts",
                    exception=sources.exception,
                )
                continue
            complete.append(
                file.model_copy(
                    update={"source_states": sources.value},
                ),
            )
        return tuple(complete)

    @staticmethod
    def _select_repositories(
        request: m.Infra.CodegenConformRequest,
        workspace: m.Infra.WorkspaceSpec,
        current_repository: m.Infra.RepositoryRef,
    ) -> p.Result[t.VariadicTuple[m.Infra.RepositoryRef]]:
        """Resolve self/subprojects/all from the local read-only topology.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Infra.RepositoryRef]]``.

        """
        scope = c.Infra.CodegenConformScope(request.scope)
        selected: t.VariadicTuple[m.Infra.RepositoryRef]
        if scope is c.Infra.CodegenConformScope.SELF:
            selected = (current_repository,)
        elif scope is c.Infra.CodegenConformScope.DECLARED:
            if not workspace.subprojects:
                return r[t.VariadicTuple[m.Infra.RepositoryRef]].fail(
                    "subprojects scope requires local .gitmodules entries",
                )
            selected = tuple(workspace.subprojects)
        else:
            selected = (workspace.repository, *workspace.subprojects)
        mutable = tuple(
            repository
            for repository in selected
            if repository.codegen is not c.Infra.CodegenKind.NONE
            and not repository.read_only
        )
        if not mutable:
            return r[t.VariadicTuple[m.Infra.RepositoryRef]].fail(
                "selected repositories do not permit code generation",
            )
        return r[t.VariadicTuple[m.Infra.RepositoryRef]].ok(mutable)

    @staticmethod
    def _repository_root(
        root: Path,
        workspace: p.Infra.WorkspaceSpec,
        repository: p.Infra.RepositoryRef,
    ) -> p.Result[Path]:
        """Resolve one declared checkout without escaping its workspace owner.

        Returns:
            The resulting ``p.Result[Path]``.

        """
        if repository.name == workspace.repository.name:
            return r[Path].ok(root)
        resolved_root = root.resolve()
        resolved: Path = (resolved_root / repository.path).resolve()
        if not resolved.is_relative_to(resolved_root):
            return r[Path].fail(
                "declared repository path escapes workspace root: "
                f"{repository.path.as_posix()}",
            )
        return r[Path].ok(resolved)


__all__: list[str] = ["FlextInfraCodegenConformPlanTopologyMixin"]
