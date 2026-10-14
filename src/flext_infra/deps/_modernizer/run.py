"""Select workspace pyprojects, modernize them, and verify the build backend.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, r, t, u
from flext_infra.deps._modernizer.document import RenderPolicy

if TYPE_CHECKING:
    from collections.abc import MutableMapping

    from flext_infra import p
    from flext_infra.deps._modernizer.document import RenderPolicySpec


class FlextInfraPyprojectModernizerRun:
    """Drive file selection, modernization, reporting, and post-write checks."""

    if TYPE_CHECKING:
        # Members supplied by the composed modernizer service.
        audit: bool
        check_only: bool
        skip_check: bool
        skip_comments: bool
        rewrite_constraints: bool
        git_source_url_prefix: str | None
        git_source_ref_from: str | None
        git_source_ref_to: str | None

        @property
        def root(self) -> Path: ...

        @property
        def effective_dry_run(self) -> bool: ...

        @property
        def project_names(self) -> t.StrSequence | None: ...

        @staticmethod
        def _read_document_state(
            path: Path,
            *,
            source: str | None = None,
        ) -> p.Result[m.Infra.PyprojectDocumentState]: ...

        def _process_document_state(
            self,
            state: m.Infra.PyprojectDocumentState,
            *,
            canonical_dev: t.StrSequence,
            dry_run: bool,
            skip_comments: bool,
            source_migration: m.Infra.GitSourceReferenceMigration | None = None,
        ) -> p.Result[t.StrSequence]: ...

        def _render_document_state(
            self,
            state: m.Infra.PyprojectDocumentState,
            changes: t.StrSequence,
            *,
            policy: RenderPolicySpec,
        ) -> p.Result[t.StrSequence]: ...

    def _selected_project_paths(self) -> p.Result[t.SequenceOf[Path]]:
        """Resolve selected names by path, directory basename, or declared name.

        Returns:
            The resulting ``p.Result[t.SequenceOf[Path]]``.

        """
        result_type = r[t.SequenceOf[Path]]
        declared = {
            name: self.root / name
            for name in u.Infra.workspace_project_paths(self.root)
        }
        resolved_root = self.root.resolve()
        outside = sorted(
            name
            for name, path in declared.items()
            if not path.resolve().is_relative_to(resolved_root)
        )
        if outside:
            return result_type.fail(
                f"workspace subprojects outside root: {', '.join(outside)}",
            )
        aliases: MutableMapping[str, t.MutableSequenceOf[Path]] = {}
        for path in declared.values():
            aliases.setdefault(path.name, []).append(path)
            # A declared subproject whose pyproject cannot be read or named
            # would otherwise vanish from the alias map and resurface as a
            # false "missing" or "ambiguous" project further down.
            state = self._read_document_state(path / c.PYPROJECT_FILENAME)
            if state.failure:
                # A declared member's unreadable pyproject is a broken
                # workspace contract, not a selectable absence: the canonical
                # docs-scope reader owns the typed error for invalid TOML and
                # names the offending file, and that raise must leave the run
                # instead of being demoted into an exit-code log line.
                _ = u.Infra.project_state(path)
                return result_type.fail(
                    f"workspace subproject {path} has an unreadable pyproject: "
                    f"{state.error}",
                )
            name = u.Infra.project_name_from_payload(
                state.value.pyproject_path,
                state.value.payload,
            )
            if path not in aliases.setdefault(name, []):
                aliases[name].append(path)
        selected = [name for name in self.project_names or () if name != "."]
        paths: t.MutableSequenceOf[Path] = []
        missing: t.MutableSequenceOf[str] = []
        ambiguous: t.MutableSequenceOf[str] = []
        for name in selected if self.project_names else declared:
            matches = [declared[name]] if name in declared else aliases.get(name, [])
            if len(matches) > 1:
                ambiguous.append(name)
            elif not matches or not matches[0].is_dir():
                missing.append(name)
            else:
                paths.append(matches[0])
        if ambiguous:
            return result_type.fail(
                f"ambiguous projects: {', '.join(sorted(ambiguous))}",
            )
        if missing:
            return result_type.fail(f"unknown projects: {', '.join(sorted(missing))}")
        return result_type.ok(paths)

    def run(self) -> int:
        """Run pyproject modernization for the workspace.

        Returns:
            The resulting ``int``.

        """
        check_mode = self.audit or self.check_only
        dry_run = check_mode or self.effective_dry_run
        migration = self._resolved_source_migration()
        if migration.failure:
            u.Cli.error(migration.error or "git source migration failed")
            return 2
        source_migration = migration.value
        # Modernization writes only the requested repository root and its
        # declared subprojects, never siblings.
        include_root = not self.project_names or "." in self.project_names
        project_paths = self._selected_project_paths()
        if project_paths.failure:
            u.Cli.error(project_paths.error or "project selection failed")
            return 2
        root_pyproject = self.root / c.PYPROJECT_FILENAME
        validated = self._validated_root(root_pyproject, include_root=include_root)
        if validated.failure:
            return 2
        if self.rewrite_constraints:
            return self._rewrite_constraints(validated.value, dry_run=dry_run)
        found = u.Infra.find_all_pyproject_files(
            self.root,
            skip_dirs=c.Infra.PYPROJECT_SKIP_DIRS,
            project_paths=project_paths.value,
        )
        if found.failure:
            u.Cli.error(found.error or "pyproject discovery failed")
            return 2
        files = {*found.value}
        if include_root and root_pyproject.is_file():
            files.add(root_pyproject)
        scanned = self._scan_documents(
            sorted(files),
            validated,
            root_pyproject,
            dry_run=dry_run,
            source_migration=source_migration,
        )
        return self._reported_exit(
            scanned,
            check_mode=check_mode,
            dry_run=dry_run,
            migrated=source_migration is not None,
        )

    def _resolved_source_migration(
        self,
    ) -> p.Result[m.Infra.GitSourceReferenceMigration | None]:
        """Resolve the requested Git reference migration options.

        Returns:
            The resolved migration, ``None`` when none is requested, or the
            first option validation failure.

        """
        result_type = r[m.Infra.GitSourceReferenceMigration | None]
        source_options = (
            self.git_source_url_prefix,
            self.git_source_ref_from,
            self.git_source_ref_to,
        )
        if not any(value is not None for value in source_options):
            return result_type.ok(value=None)
        prefix, old_ref, new_ref = source_options
        if prefix is None or old_ref is None or new_ref is None:
            return result_type.fail(
                "Git reference migration requires URL prefix, source ref and "
                "target ref together",
            )
        if not prefix.endswith("/"):
            return result_type.fail(
                "Git source URL prefix must end with '/' to preserve owner boundaries",
            )
        if self.rewrite_constraints:
            return result_type.fail(
                "Git reference migration and runtime constraint rewriting are "
                "separate operations",
            )
        return result_type.ok(
            m.Infra.GitSourceReferenceMigration(
                url_prefix=prefix,
                source_ref=old_ref,
                target_ref=new_ref,
            ),
        )

    def _reported_exit(
        self,
        scanned: p.Result[
            t.Triple[
                t.MappingKV[str, t.StrSequence],
                t.SequenceOf[m.Infra.PyprojectDocumentState],
                t.SequenceOf[Path],
            ]
        ],
        *,
        check_mode: bool,
        dry_run: bool,
        migrated: bool,
    ) -> int:
        """Report the scanned violations and derive the run exit code.

        Args:
            scanned: The completed document scan or its failure.
            check_mode: Whether the run audits or checks without writing.
            dry_run: Whether no file may be written.
            migrated: Whether a Git reference migration owned the run.

        Returns:
            The resulting process exit code.

        """
        if scanned.failure:
            u.Cli.error(scanned.error or "document scan failed")
            return 2
        violations, states, invalid_paths = scanned.value
        total = self._report_violations(violations, dry_run=dry_run)
        if check_mode and total > 0:
            return 1
        if migrated or dry_run or self.skip_check:
            return 0
        return self._run_build_check(states, invalid_paths=invalid_paths)

    @staticmethod
    def _report_violations(
        violations: t.MappingKV[str, t.StrSequence],
        *,
        dry_run: bool,
    ) -> int:
        """Emit every change grouped by file with the closing total.

        Returns:
            The total change count across all files.

        """
        total = sum(len(changes) for changes in violations.values())
        for rel_path, changes in violations.items():
            u.Cli.info(f"{rel_path}:")
            for change in changes:
                u.Cli.info(f"  - {change}")
        if violations:
            u.Cli.info(f"Total: {total} change(s) across {len(violations)} file(s)")
            if dry_run:
                u.Cli.info("(dry-run — no files modified)")
        return total

    def _validated_root(
        self,
        root_pyproject: Path,
        *,
        include_root: bool,
    ) -> p.Result[m.Infra.PyprojectDocumentState]:
        """Read and validate the root document state for the requested scope.

        Returns:
            The resulting validated root document state.

        """
        root_state = self._read_document_state(root_pyproject)
        if root_state.failure:
            return root_state
        if include_root:
            try:
                _ = u.Infra.project_name_from_payload(
                    root_pyproject,
                    root_state.value.payload,
                )
            except c.EXC_TYPE_VALIDATION as exc:
                u.Cli.error(str(exc))
                return r[m.Infra.PyprojectDocumentState].fail(str(exc), exception=exc)
        return root_state

    def _scan_documents(
        self,
        ordered: t.SequenceOf[Path],
        root_state: p.Result[m.Infra.PyprojectDocumentState],
        root_pyproject: Path,
        *,
        dry_run: bool,
        source_migration: m.Infra.GitSourceReferenceMigration | None = None,
    ) -> p.Result[
        t.Triple[
            t.MappingKV[str, t.StrSequence],
            t.SequenceOf[m.Infra.PyprojectDocumentState],
            t.SequenceOf[Path],
        ]
    ]:
        """Process every ordered pyproject and collect the modernization scan.

        Returns:
            The resulting ``(violations, states, invalid_paths)`` triple.

        """
        outcome = r[
            t.Triple[
                t.MappingKV[str, t.StrSequence],
                t.SequenceOf[m.Infra.PyprojectDocumentState],
                t.SequenceOf[Path],
            ]
        ]
        violations: MutableMapping[str, t.StrSequence] = {}
        states: t.MutableSequenceOf[m.Infra.PyprojectDocumentState] = []
        invalid_paths: t.MutableSequenceOf[Path] = []
        drift_reported = False
        # A migration run never pins development floors: the declared set is
        # authoritative while the reference migration rewrites Git sources.
        canonical_dev: t.StrSequence = (
            ()
            if source_migration is not None or root_state.failure
            else t.Infra.STR_SEQ_ADAPTER.validate_python(
                u.Infra.canonical_dev_dependencies_from_payload(
                    root_state.value.payload
                ),
            )
        )
        for index, file_path in enumerate(ordered, start=1):
            u.Cli.progress(index, len(ordered), str(file_path), c.Infra.CLI_GROUP_DEPS)
            state = (
                root_state
                if file_path.resolve() == root_pyproject.resolve()
                else self._read_document_state(file_path)
            )
            if state.failure:
                invalid_paths.append(file_path)
                changes: t.StrSequence = ("invalid TOML",)
            else:
                processed = self._process_document_state(
                    state.value,
                    canonical_dev=canonical_dev,
                    dry_run=dry_run,
                    skip_comments=self.skip_comments,
                    source_migration=source_migration,
                )
                if processed.failure:
                    return outcome.from_failure(processed)
                changes = processed.value
                if changes and not drift_reported:
                    drift_reported = True
                    diff_lines = u.Infra.unified_diff_lines(
                        state.value.original_rendered,
                        state.value.rendered,
                        fromfile=f"{file_path}:before",
                        tofile=f"{file_path}:after",
                        max_lines=c.Infra.EDIT_DIFF_PREVIEW_MAX_LINES,
                    )
                    u.Cli.info(
                        "deps: first rendered drift\n" + "".join(diff_lines).rstrip(),
                    )
                states.append(state.value)
            if changes:
                resolved = file_path.resolve()
                violations[
                    str(resolved.relative_to(self.root.resolve()))
                    if resolved.is_relative_to(self.root.resolve())
                    else str(resolved)
                ] = changes
        return outcome.ok((dict(violations), tuple(states), tuple(invalid_paths)))

    def _rewrite_constraints(
        self,
        root_state: m.Infra.PyprojectDocumentState,
        *,
        dry_run: bool,
    ) -> int:
        """Write resolved floors to the target's own requirement declarations.

        Returns:
            The resulting ``int``.

        Raises:
            TypeError: If ``not isinstance(entries, list)``; or if
                ``isinstance(requirement, Mapping)``; or if ``not
                isinstance(requirement, str)``.
            ValueError: If the project table is absent or the dependency owner
                changed between the read and the write.

        """
        try:
            root_project_name = u.Infra.project_name_from_payload(
                root_state.pyproject_path,
                root_state.payload,
            )
        except c.EXC_TYPE_VALIDATION as exc:
            u.Cli.error(str(exc))
            return 2
        if dry_run:
            return 0
        versions = u.Infra.resolved_dependency_versions()
        internal_names = (
            *u.Infra.workspace_project_paths(self.root),
            root_project_name,
        )
        project = u.Cli.toml_mapping_child(root_state.payload, c.Infra.PROJECT)
        if project is None:
            msg = f"project declaration is absent: {root_state.pyproject_path}"
            raise ValueError(msg)
        sections = (
            ("project", {c.Infra.DEPENDENCIES: project.get(c.Infra.DEPENDENCIES, [])}),
            (
                "project.optional-dependencies",
                u.Cli.toml_mapping_child(project, c.Infra.OPTIONAL_DEPENDENCIES) or {},
            ),
            (
                c.Infra.DEPENDENCY_GROUPS,
                u.Cli.toml_mapping_child(root_state.payload, c.Infra.DEPENDENCY_GROUPS)
                or {},
            ),
        )
        changes = self._rewritten_constraint_sections(
            sections,
            versions=versions,
            internal_names=internal_names,
        )
        if not changes:
            return 0
        before = u.Cli.atomic_read_binary_file_state(
            root_state.pyproject_path,
            required=True,
        ).unwrap()
        return self._published_constraint_floors(root_state, tuple(changes), before)

    @classmethod
    def _rewritten_constraint_sections(
        cls,
        sections: t.SequenceOf[t.Pair[str, t.MappingKV[str, t.JsonValue]]],
        *,
        versions: t.MappingKV[str, str],
        internal_names: t.StrSequence,
    ) -> list[str]:
        """Rewrite every declared requirement to its resolved runtime floor.

        Args:
            sections: Ordered requirement sections with their requirement
                groups.
            versions: Resolved dependency versions of the provisioned runtime.
            internal_names: Workspace member names exempted from floor pins.

        Returns:
            The change notes of every rewritten requirement.

        Raises:
            TypeError: If a declared requirement group entry is not a string.

        """
        changes: list[str] = []
        for section, groups in sections:
            for name, entries in groups.items():
                if not isinstance(entries, list):
                    msg = f"{section}.{name} must be a requirement array"
                    raise TypeError(msg)
                for index, requirement in enumerate(entries):
                    mapping = isinstance(requirement, Mapping)
                    if mapping and section == c.Infra.DEPENDENCY_GROUPS:
                        continue
                    if mapping or not isinstance(requirement, str):
                        msg = f"{section}.{name} requires requirement strings"
                        raise TypeError(msg)
                    rewritten = u.Infra.rewrite_requirement_constraint(
                        requirement,
                        resolved_versions=versions,
                        internal_names=internal_names,
                    )
                    if rewritten is not None:
                        entries[index] = rewritten
                        changes.append(
                            f"{section}.{name}: {requirement} -> {rewritten}"
                        )
        return changes

    def _published_constraint_floors(
        self,
        root_state: m.Infra.PyprojectDocumentState,
        changes: t.StrSequence,
        before: m.Cli.AtomicFileState,
    ) -> int:
        """Publish the rewritten requirement floors atomically.

        Args:
            root_state: Validated root document state owning the floors.
            changes: Change notes of every rewritten requirement.
            before: Authenticated pre-publication state of the document.

        Returns:
            The resulting process exit code.

        Raises:
            ValueError: If the dependency owner changed between the read and
                the write.

        """
        if before.content != root_state.original_rendered.encode(c.DEFAULT_ENCODING):
            msg = f"dependency owner changed during read: {root_state.pyproject_path}"
            raise ValueError(msg)
        rendered = self._render_document_state(
            root_state,
            tuple(changes),
            policy=RenderPolicy(
                dry_run=True,
                skip_comments=True,
                format_source=False,
                preserve_layout=True,
            ),
        )
        if rendered.failure:
            rendered.unwrap()
        u.Cli.atomic_write_binary_file_guarded(
            before,
            root_state.rendered.encode(c.DEFAULT_ENCODING),
            permission_mode=before.mode,
        ).unwrap()
        u.Cli.info(
            "deps: target requirement floors updated from the provisioned runtime"
        )
        for change in changes:
            u.Cli.info(f"  - {change}")
        return 0

    @staticmethod
    def _run_build_check(
        states: t.SequenceOf[m.Infra.PyprojectDocumentState],
        *,
        invalid_paths: t.SequenceOf[Path],
    ) -> int:
        """Validate every pyproject declares the hatchling build backend.

        Returns:
            The resulting ``int``.

        """
        warnings = [f"{path}: invalid TOML" for path in invalid_paths]
        for state in states:
            build_system = u.Cli.toml_mapping_child(state.payload, "build-system")
            backend = (
                None
                if build_system is None
                else u.norm_str(str(build_system.get("build-backend", "")))
            )
            if backend is None:
                warnings.append(f"{state.pyproject_path}: missing [build-system]")
            elif backend != "hatchling.build":
                warnings.append(
                    f"{state.pyproject_path}: expected hatchling.build, got {backend}",
                )
        for warning in warnings:
            u.Cli.info(warning)
        return 1 if warnings else 0


__all__: list[str] = ["FlextInfraPyprojectModernizerRun"]
