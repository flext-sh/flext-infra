"""Semantic publication through the shared codegen file publisher.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from contextlib import closing
from os.path import commonpath
from pathlib import Path

from flext_infra import c, config, m, p, r, t, u
from flext_infra.codegen import FlextInfraCodegenLazyInit, FlextInfraStagedPackage


class FlextInfraSemanticPublication:
    """Plan semantic file effects once and publish them through one owner."""

    @classmethod
    def publish_semantic_artifact_plans(
        cls,
        plans: t.SequenceOf[m.Infra.CodegenFilePlan],
        *,
        repository_root: Path,
        options: m.Infra.SemanticPublicationOptions | None = None,
        publish: bool = True,
    ) -> p.Result[t.VariadicTuple[Path]]:
        """Compose declared projections, then publish or report pending effects.

        A declared validator accepts the previewed candidate tree before any
        live destination changes.

        Returns:
            Published paths, the paths a publication would change when
            ``publish`` is false, or the first planning/publication failure.

        """
        selected = m.Infra.SemanticPublicationOptions() if options is None else options
        composed = cls._with_projections(
            plans, repository_root, selected.projection_roots
        )
        if composed.failure:
            return r[tuple[Path, ...]].from_failure(composed)
        if not publish:
            return cls._pending_paths(composed.value)
        if selected.validator is not None:
            accepted = cls._accepted_candidate(
                composed.value, repository_root, selected
            )
            if accepted.failure:
                return r[tuple[Path, ...]].from_failure(accepted)
        return u.Infra.publish_codegen_plans(repository_root, composed.value)

    @staticmethod
    def _accepted_candidate(
        plans: t.SequenceOf[m.Infra.CodegenFilePlan],
        repository_root: Path,
        options: m.Infra.SemanticPublicationOptions,
    ) -> p.Result[bool]:
        """Preview the normalized candidate and run the consumer validator on it.

        Returns:
            Acceptance of the previewed candidate, or the first preview or
            validator failure.

        """
        validator = options.validator
        if validator is None:
            return r[bool].ok(value=True)
        changes = u.Infra.normalized_codegen_changes(plans)
        if changes.failure:
            return r[bool].from_failure(changes)
        workspaces = tuple(
            dict.fromkeys(
                u.Infra.import_project_roots(root)[0].resolve()
                for root in options.projection_roots
            )
        )
        scope = (
            r[Path].ok(Path(commonpath(workspaces)))
            if len(workspaces) > 1
            else FlextInfraStagedPackage.workspace_root(
                workspaces[0] if workspaces else repository_root.resolve()
            )
        )
        if scope.failure:
            return r[bool].from_failure(scope)
        relative = repository_root.resolve().relative_to(scope.value)
        previewed = FlextInfraStagedPackage().preview_sources(
            repository_root,
            {
                change.path: None
                if change.desired_content is None
                else change.desired_content.decode(c.DEFAULT_ENCODING)
                for change in changes.value
            },
            lambda view_root, _paths: validator(view_root / relative),
            options=m.Infra.CodegenSourcePreviewOptions(
                workspaces=workspaces if len(workspaces) > 1 else (),
                modes={
                    change.path: change.desired_mode
                    for change in changes.value
                    if change.desired_mode is not None
                },
            ),
        )
        accepted = previewed.flat_map(lambda verdict: verdict)
        if accepted.success and not accepted.value:
            return r[bool].fail("semantic candidate acceptance rejected")
        return accepted

    @classmethod
    def publish_semantic_file_plans(
        cls,
        plans: t.SequenceOf[m.Infra.SemanticFilePlan],
        *,
        repository_root: Path,
        options: m.Infra.SemanticPublicationOptions | None = None,
        codegen: m.Infra.CodegenConfigSpec | None = None,
    ) -> p.Result[t.VariadicTuple[Path]]:
        """Publish every changed semantic file plan.

        ``None`` content means no semantic change, never deletion.

        Returns:
            Published paths, or the first planning/publication failure.

        """
        concrete = cls.plan_semantic_file_plans(plans, codegen)
        if concrete.failure:
            return r[tuple[Path, ...]].from_failure(concrete)
        return cls.publish_semantic_artifact_plans(
            concrete.value, repository_root=repository_root, options=options
        )

    @staticmethod
    def plan_semantic_file_plans(
        plans: t.SequenceOf[m.Infra.SemanticFilePlan],
        codegen: m.Infra.CodegenConfigSpec | None = None,
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Convert every changed semantic plan into one owned codegen file plan.

        A generated source outside the declared template inventory requires
        canonical generator repair and is rejected here.

        Returns:
            The concrete codegen file plans, or the first rejected plan.

        """
        result_type = r[tuple[m.Infra.CodegenFilePlan, ...]]
        files: list[m.Infra.CodegenFilePlan] = []
        template_sources = u.Infra.codegen_template_sources(
            config.Infra.codegen if codegen is None else codegen,
        )
        for plan in plans:
            if plan.desired_content is None:
                continue
            if plan.desired_mode is None:
                return result_type.fail(f"semantic desired mode is absent: {plan.path}")
            if (
                plan.path.resolve() not in template_sources
                and plan.before.content is not None
                and plan.before.content.decode(c.DEFAULT_ENCODING).startswith(
                    c.Infra.AUTOGEN_HEADERS,
                )
            ):
                return result_type.fail(
                    "generated findings require canonical generator repair: "
                    f"{plan.path}"
                )
            files.append(
                m.Infra.CodegenFilePlan(
                    project=plan.project,
                    path=plan.path,
                    before=plan.before,
                    desired_content=plan.desired_content,
                    desired_mode=plan.desired_mode,
                    owner="semantic",
                ),
            )
        return result_type.ok(tuple(files))

    @staticmethod
    def edit_file_plans(
        root: Path,
        edits: t.SequenceOf[p.Infra.SemanticMigrationEdit],
        *,
        owner: str,
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Bind each final edit to its destination's current state, once.

        Returns:
            One plan per edit, or the first destination read failure.

        """
        result_type = r[tuple[m.Infra.CodegenFilePlan, ...]]
        files: list[m.Infra.CodegenFilePlan] = []
        for edit in edits:
            before = u.Infra.codegen_target_snapshot(edit.file_path)
            if before.failure:
                return result_type.from_failure(before)
            files.append(
                m.Infra.CodegenFilePlan(
                    project=u.Infra.project_root(edit.file_path) or root,
                    path=edit.file_path,
                    before=before.value,
                    desired_content=None
                    if edit.retire_file
                    else edit.updated_source.encode(c.DEFAULT_ENCODING),
                    desired_mode=None
                    if edit.retire_file
                    else before.value.mode
                    if before.value.content is not None
                    else config.Infra.codegen.modes.file_default,
                    owner=owner,
                )
            )
        return result_type.ok(tuple(files))

    @staticmethod
    def _pending_paths(
        plans: t.SequenceOf[m.Infra.CodegenFilePlan],
    ) -> p.Result[t.VariadicTuple[Path]]:
        """Report the destinations a publication of ``plans`` would change.

        Returns:
            The pending paths, or the first normalization failure.

        """
        changes = u.Infra.normalized_codegen_changes(plans)
        if changes.failure:
            return r[tuple[Path, ...]].from_failure(changes)
        return r[tuple[Path, ...]].ok(
            tuple(
                change.path
                for change in changes.value
                if u.Infra.atomic_file_state_differs(
                    change.before,
                    desired_content=change.desired_content,
                    desired_mode=change.desired_mode,
                )
            )
        )

    @staticmethod
    def _with_projections(
        plans: t.SequenceOf[m.Infra.CodegenFilePlan],
        repository_root: Path,
        projection_roots: t.VariadicTuple[Path],
    ) -> p.Result[t.VariadicTuple[m.Infra.CodegenFilePlan]]:
        """Join the lazy-init projections the planned sources require.

        Each declared workspace projects its own roots: a cross-root campaign
        composes one projection per import workspace, never one Rope view
        spanning foreign checkouts.

        Returns:
            The semantic plans plus their projections, or the first conflict.

        """
        result_type = r[tuple[m.Infra.CodegenFilePlan, ...]]
        if not projection_roots:
            return result_type.ok(tuple(plans))
        repository = repository_root.resolve()
        workspaces: dict[Path, list[Path]] = {}
        for root in dict.fromkeys(projection_roots):
            resolved = root.resolve()
            workspace = (
                repository
                if resolved.is_relative_to(repository)
                else u.Infra.import_project_roots(resolved)[0].resolve()
            )
            workspaces.setdefault(workspace, []).append(resolved)
        combined = {plan.path: plan for plan in plans}
        for workspace, scope_roots in workspaces.items():
            scoped = tuple(
                plan for plan in plans if plan.path.resolve().is_relative_to(workspace)
            )
            roots = tuple(
                dict.fromkeys((
                    *scope_roots,
                    *(plan.project.resolve() for plan in scoped),
                ))
            )
            with (
                u.Infra.open_project(workspace, project_roots=roots) as live,
                closing(
                    u.Infra.planned_project(
                        live,
                        election=u.Infra.native_election(live),
                        declared_files=scoped,
                    )
                ) as source_project,
            ):
                generated = FlextInfraCodegenLazyInit(
                    repository_root=workspace,
                    project_scope_roots=tuple(scope_roots),
                ).plan_files(source_project=source_project)
            if generated.failure:
                return result_type.from_failure(generated)
            for item in generated.value:
                previous = combined.get(item.path)
                if previous is not None and previous.before != item.before:
                    return result_type.fail(
                        "semantic projection changed its original destination: "
                        f"{item.path}"
                    )
                combined[item.path] = item
        return result_type.ok(tuple(combined.values()))


__all__: list[str] = ["FlextInfraSemanticPublication"]
