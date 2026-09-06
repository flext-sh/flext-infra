"""Destination-local staging for generic generated-file plans."""

from __future__ import annotations

import stat
from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import m, u
from flext_infra.codegen import (
    _mise_artifacts_files as files,
    _mise_artifacts_process as process,
)

if TYPE_CHECKING:
    from flext_infra import p


_PHASES = frozenset({"conform", "lazy-init", "docs"})


def stage_file_plans(
    layout: m.Infra.MiseToolchainWorkspaceLayout,
    phase: str,
    plans: tuple[m.Infra.CodegenFilePlan, ...],
) -> p.Result[tuple[m.Infra.CodegenStagedFile, ...]]:
    """Stage one exact phase without changing any live destination."""
    result_type = r[tuple[m.Infra.CodegenStagedFile, ...]]
    if phase not in _PHASES:
        return result_type.fail(f"unsupported generation phase: {phase}")
    changed = tuple(
        plan for plan in plans if u.Infra.codegen_file_requires_effect(plan)
    )
    paths = tuple(plan.path for plan in changed)
    if len(set(paths)) != len(paths):
        return result_type.fail(f"duplicate {phase} generation destination")
    publications: list[m.Infra.CodegenStagedFile] = []
    phase_roots: set[Path] = set()
    for index, file_plan in enumerate(changed):
        before_result = u.Infra.codegen_file_before_state(file_plan)
        if before_result.failure:
            return result_type.fail(
                f"{phase} destination parent was not materialized before staging: "
                f"{file_plan.path.parent}"
            )
        before = before_result.value
        project = next(
            (item for item in layout.projects if item.root == file_plan.project), None
        )
        if project is None or project.transaction_root is None:
            return result_type.fail(
                f"{phase} file has no transaction participant: {file_plan.path}"
            )
        current = files.read_state(file_plan.path, required=False)
        if current.failure:
            return result_type.from_failure(current)
        if current.value != before:
            return result_type.fail(
                f"{phase} destination changed after planning: {file_plan.path}"
            )
        if not file_plan.path.parent.is_dir() or file_plan.path.parent.is_symlink():
            return result_type.fail(
                f"{phase} destination parent is not physical: {file_plan.path.parent}"
            )
        try:
            parent_state = file_plan.path.parent.lstat()
            transaction_parent = project.transaction_root.parent.lstat()
        except OSError as exc:
            return result_type.fail_op(f"inspect {phase} staging filesystem", exc)
        reparse = getattr(parent_state, "st_file_attributes", 0) & getattr(
            stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0
        )
        if (
            not stat.S_ISDIR(parent_state.st_mode)
            or reparse
            or parent_state.st_dev != transaction_parent.st_dev
        ):
            return result_type.fail(
                f"{phase} staging is not on destination filesystem: {file_plan.path}"
            )
        replacement: m.Cli.AtomicFileState | None = None
        if file_plan.desired_content is not None:
            desired_mode = file_plan.desired_mode
            if desired_mode is None:
                return result_type.fail(
                    f"{phase} desired mode is absent: {file_plan.path}"
                )
            phase_root = project.transaction_root / f"phase-{phase}"
            if phase_root not in phase_roots:
                phase_root_before = u.Cli.atomic_read_empty_directory_state(
                    phase_root, required=False
                )
                if phase_root_before.failure:
                    return result_type.from_failure(phase_root_before)
                if phase_root_before.value.exists:
                    return result_type.fail(
                        f"{phase} staging root already exists: {phase_root}"
                    )
                created = u.Cli.atomic_create_empty_directory_guarded(
                    phase_root_before.value, permission_mode=0o700
                )
                if created.failure:
                    return result_type.from_failure(created)
                phase_roots.add(phase_root)
            staged_path = phase_root / f"{index:06d}.replacement"
            staged = process.write_new(
                staged_path, file_plan.desired_content, desired_mode
            )
            if staged.failure:
                return result_type.from_failure(staged)
            staged_state = files.read_state(staged_path, required=True)
            if staged_state.failure:
                return result_type.from_failure(staged_state)
            replacement = staged_state.value
        publications.append(
            m.Infra.CodegenStagedFile(
                phase=phase,
                project=file_plan.project,
                before=before,
                replacement=replacement,
            )
        )
    return result_type.ok(tuple(publications))


__all__: list[str] = ["stage_file_plans"]
