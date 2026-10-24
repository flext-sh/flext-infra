"""Semantic publication through the shared codegen file publisher.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from contextlib import closing
from pathlib import Path

from flext_infra import c, config, m, p, r, t, u
from flext_infra._utilities._rope.project import FlextInfraRopeProject
from flext_infra.codegen import FlextInfraCodegenLazyInit


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
        published = u.Infra.publish_codegen_plans(repository_root, composed.value)
        if published.failure or selected.validator is None:
            return published
        accepted = selected.validator(repository_root)
        if accepted.failure:
            return r[tuple[Path, ...]].from_failure(accepted)
        if not accepted.value:
            return r[tuple[Path, ...]].fail("semantic acceptance rejected")
        return published

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

        Returns:
            The semantic plans plus their projections, or the first conflict.

        """
        result_type = r[tuple[m.Infra.CodegenFilePlan, ...]]
        if not projection_roots:
            return result_type.ok(tuple(plans))
        roots = tuple(
            dict.fromkeys((*projection_roots, *(plan.project for plan in plans)))
        )
        with (
            u.Infra.open_project(repository_root, project_roots=roots) as live,
            closing(
                FlextInfraRopeProject.from_atomic_reads(
                    live,
                    election=u.Infra.native_election(live),
                    declared_files=tuple(plans),
                )
            ) as source_project,
        ):
            generated = FlextInfraCodegenLazyInit(
                repository_root=repository_root,
                project_scope_roots=projection_roots,
            ).plan_files(source_project=source_project)
        if generated.failure:
            return result_type.from_failure(generated)
        combined = {plan.path: plan for plan in plans}
        for item in generated.value:
            previous = combined.get(item.path)
            if previous is not None and previous.before != item.before:
                return result_type.fail(
                    f"semantic projection changed its original destination: {item.path}"
                )
            combined[item.path] = item
        return result_type.ok(tuple(combined.values()))


__all__: list[str] = ["FlextInfraSemanticPublication"]
