"""Run orchestration mixin for pyproject modernization."""

from __future__ import annotations

from collections.abc import MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, p, r, t, u


class FlextInfraPyprojectModernizerRunMixin:
    """Drive file iteration, modernization, and post-write build checks."""

    if TYPE_CHECKING:
        root: Path
        audit: bool
        check_only: bool
        effective_dry_run: bool
        skip_check: bool
        skip_comments: bool
        rewrite_constraints: bool
        project_names: t.StrSequence | None
        constraint_policy: c.Infra.DependencyConstraintPolicy

        def _read_document_state(
            self, path: Path
        ) -> p.Result[m.Infra.PyprojectDocumentState]: ...

        def _process_document_state(
            self,
            state: m.Infra.PyprojectDocumentState,
            *,
            canonical_dev: t.StrSequence,
            dry_run: bool,
            skip_comments: bool,
            rewrite_constraints: bool = False,
            locked_versions: t.MappingKV[str, str] | None = None,
            internal_names: t.StrSequence = (),
            constraint_policy: c.Infra.DependencyConstraintPolicy = c.Infra.DependencyConstraintPolicy.FLOOR,
        ) -> t.StrSequence: ...

    def process_file(
        self,
        path: Path,
        *,
        canonical_dev: t.StrSequence,
        dry_run: bool,
        skip_comments: bool,
    ) -> t.StrSequence:
        """Process one pyproject.toml file and collect changes."""
        document_state_result = self._read_document_state(path)
        if document_state_result.failure:
            return ["invalid TOML"]
        return self._process_document_state(
            document_state_result.value,
            canonical_dev=canonical_dev,
            dry_run=dry_run,
            skip_comments=skip_comments,
            rewrite_constraints=False,
        )

    def run(self) -> int:
        """Run pyproject modernization for the workspace."""
        check_mode = self.audit or self.check_only
        dry_run = check_mode or self.effective_dry_run
        project_names = list(self.project_names or [])
        project_paths: t.SequenceOf[Path] | None = None
        if project_names:
            selected_projects = u.Infra.resolve_projects(self.root, project_names)
            if selected_projects.failure:
                u.Cli.error(
                    selected_projects.error or "failed to resolve selected projects",
                )
                return 2
            project_paths = [project.path for project in selected_projects.value]
        files_result = u.Infra.find_all_pyproject_files(
            self.root,
            skip_dirs=c.Infra.SKIP_DIRS,
            project_paths=project_paths,
        )
        files: t.SequenceOf[Path] = (
            [] if files_result.failure else sorted(files_result.unwrap())
        )
        root_state_result = self._read_document_state(
            self.root / c.Infra.PYPROJECT_FILENAME
        )
        if root_state_result.failure:
            return 2
        root_state = root_state_result.value
        canonical_dev: t.StrSequence = t.Infra.STR_SEQ_ADAPTER.validate_python(
            u.Infra.canonical_dev_dependencies_from_payload(root_state.payload),
        )
        locked_versions: t.MappingKV[str, str] = {}
        internal_names: t.StrSequence = ()
        if self.rewrite_constraints:
            lock_path = self.root / "uv.lock"
            locked_versions = u.Infra.locked_dependency_versions(lock_path)
            if not locked_versions:
                u.Cli.error(f"missing or invalid uv.lock at {lock_path}")
                return 2
            try:
                root_project_name = u.Infra.project_name_from_payload(
                    root_state.pyproject_path,
                    root_state.payload,
                )
            except c.EXC_TYPE_VALIDATION as exc:
                u.Cli.error(str(exc))
                return 2
            internal_names = tuple(
                sorted(
                    set(u.Infra.workspace_member_names(self.root)) | {root_project_name}
                )
            )
        violations: MutableMapping[str, t.StrSequence] = {}
        document_states: t.MutableSequenceOf[m.Infra.PyprojectDocumentState] = []
        invalid_paths: t.MutableSequenceOf[Path] = []
        total = 0
        for file_path in files:
            document_state_result = (
                r[m.Infra.PyprojectDocumentState].ok(root_state)
                if file_path.resolve() == root_state.pyproject_path.resolve()
                else self._read_document_state(file_path)
            )
            if document_state_result.failure:
                invalid_paths.append(file_path)
                changes = ["invalid TOML"]
            else:
                document_state = document_state_result.value
                document_states.append(document_state)
                changes = self._process_document_state(
                    document_state,
                    canonical_dev=canonical_dev,
                    dry_run=dry_run,
                    skip_comments=self.skip_comments,
                    rewrite_constraints=self.rewrite_constraints,
                    locked_versions=locked_versions,
                    internal_names=internal_names,
                    constraint_policy=self.constraint_policy,
                )
            if not changes:
                continue
            rel = str(file_path.relative_to(self.root))
            violations[rel] = changes
            total += len(changes)
        if violations:
            for rel_path, changes in violations.items():
                u.Cli.info(f"{rel_path}:")
                for change in changes:
                    u.Cli.info(f"  - {change}")
            u.Cli.info(
                f"Total: {total} change(s) across {len(violations)} file(s)",
            )
            if dry_run:
                u.Cli.info("(dry-run — no files modified)")
        if check_mode and total > 0:
            return 1
        if not dry_run and (not self.skip_check):
            return self._run_build_check(
                document_states,
                invalid_paths=invalid_paths,
            )
        return 0

    def _run_build_check(
        self,
        document_states: t.SequenceOf[m.Infra.PyprojectDocumentState],
        *,
        invalid_paths: t.SequenceOf[Path] = (),
    ) -> int:
        """Validate pyproject.toml files have hatchling build backend."""
        has_warning = False
        for invalid_path in invalid_paths:
            u.Cli.info(f"{invalid_path}: invalid TOML")
            has_warning = True
        for document_state in document_states:
            path = document_state.pyproject_path
            build_sys = u.Cli.toml_mapping_child(document_state.payload, "build-system")
            if build_sys is None:
                u.Cli.info(f"{path}: missing [build-system]")
                has_warning = True
                continue
            backend = u.norm_str(str(build_sys.get("build-backend", "")))
            if backend != "hatchling.build":
                u.Cli.info(f"{path}: expected hatchling.build, got {backend}")
                has_warning = True
        return 1 if has_warning else 0


__all__: list[str] = ["FlextInfraPyprojectModernizerRunMixin"]
