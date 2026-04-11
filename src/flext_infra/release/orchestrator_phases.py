"""Release phase implementations: build, publish, and version.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableSequence, Sequence
from pathlib import Path

from flext_infra import c, m, r, s, t, u


class FlextInfraReleaseOrchestratorPhases(s[bool]):
    """Build, publish, and version phase implementations."""

    @staticmethod
    def _run_make(project_path: Path, verb: str) -> r[t.Infra.Pair[int, str]]:
        """Execute a make command for a project and return (exit_code, output)."""
        result = u.Cli.run_raw([
            c.Infra.MAKE,
            "-C",
            str(project_path),
            verb,
        ])
        if result.failure:
            return r[t.Infra.Pair[int, str]].fail(
                result.error or "make execution failed"
            )
        output_model = result.value
        output = (output_model.stdout + "\n" + output_model.stderr).strip()
        return r[t.Infra.Pair[int, str]].ok((output_model.exit_code, output))

    def phase_build(
        self,
        ctx: m.Infra.ReleasePhaseDispatchConfig,
    ) -> r[bool]:
        """Execute the build phase and write build-report.json."""
        workspace_root = ctx.workspace_root
        version = ctx.version
        project_names = ctx.project_names
        output_dir = (
            u.Infra.get_report_dir(
                workspace_root,
                c.Infra.PROJECT,
                c.Infra.RK_RELEASE,
            )
            / f"v{version}"
        )
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            return r[bool].fail(f"report dir creation failed: {exc}")
        targets = self._build_targets(workspace_root, project_names)
        records: MutableSequence[m.Infra.BuildRecord] = []
        failures = 0
        for name, path in targets:
            make_result = self._run_make(path, c.Infra.DIR_BUILD)
            if make_result.failure:
                code = 1
                output = make_result.error or "make execution failed"
            else:
                code, output = make_result.value
            if code != 0:
                failures += 1
            log = output_dir / f"build-{name}.log"
            u.write_file(log, output + "\n", encoding=c.Infra.ENCODING_DEFAULT)
            records.append(
                m.Infra.BuildRecord(
                    project=name,
                    path=str(path),
                    exit_code=code,
                    log=str(log),
                ),
            )
            self.logger.info(
                "release_phase_build_project",
                project=name,
                exit_code=code,
            )
        report = m.Infra.BuildReport(
            version=version,
            total=len(records),
            failures=failures,
            records=list(records),
        )
        u.Cli.json_write(
            output_dir / "build-report.json",
            report.model_dump(mode="json"),
            sort_keys=True,
        )
        self.logger.info(
            "release_phase_build_report",
            report=str(output_dir / "build-report.json"),
        )
        if failures:
            return r[bool].fail(f"build failed: {failures} project(s)")
        return r[bool].ok(True)

    def phase_publish(
        self,
        ctx: m.Infra.ReleasePhaseDispatchConfig,
    ) -> r[bool]:
        """Execute publish phase: notes, changelog, tag, optional push."""
        workspace_root = ctx.workspace_root
        tag = ctx.tag
        notes_dir = (
            u.Infra.get_report_dir(
                workspace_root,
                c.Infra.PROJECT,
                c.Infra.RK_RELEASE,
            )
            / tag
        )
        try:
            notes_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            return r[bool].fail(f"report dir creation failed: {exc}")
        notes_path = notes_dir / "RELEASE_NOTES.md"
        notes_result = self._generate_notes(ctx, notes_path)
        if notes_result.failure:
            return notes_result
        if not notes_path.exists():
            return r[bool].fail(
                f"release notes generation did not create {notes_path}",
            )
        if not ctx.dry_run:
            apply_result = self._publish_apply(
                workspace_root=workspace_root,
                version=ctx.version,
                tag=tag,
                notes_path=notes_path,
                push=ctx.push,
            )
            if apply_result.failure:
                return apply_result
        self.logger.info("release_phase_publish", tag=tag, dry_run=ctx.dry_run)
        return r[bool].ok(True)

    def _publish_apply(
        self,
        *,
        workspace_root: Path,
        version: str,
        tag: str,
        notes_path: Path,
        push: bool,
    ) -> r[bool]:
        """Apply changelog, tag, and optional push for publish phase."""
        changelog_result = u.Infra.update_changelog(
            workspace_root,
            version,
            tag,
            notes_path,
        )
        if changelog_result.failure:
            return changelog_result
        tag_result = self._create_tag(workspace_root, tag)
        if tag_result.failure:
            return tag_result
        if push:
            push_result = self._push_release(workspace_root, tag)
            if push_result.failure:
                return push_result
        return r[bool].ok(True)

    def phase_version(
        self,
        ctx: m.Infra.ReleasePhaseDispatchConfig,
    ) -> r[bool]:
        """Execute versioning phase across workspace and selected projects."""
        target = f"{ctx.version}-dev" if ctx.dev_suffix else ctx.version
        parse_result = u.Infra.parse_semver(ctx.version)
        if parse_result.failure:
            return r[bool].fail(parse_result.error or "invalid version")
        files = self._version_files(ctx.workspace_root, ctx.project_names)
        changed = self._version_update_files(files, target, dry_run=ctx.dry_run)
        if ctx.dry_run:
            self.logger.info("release_phase_version_checked", checked_version=target)
        self.logger.info("release_phase_version_summary", files_changed=changed)
        return r[bool].ok(True)

    def _version_update_files(
        self,
        files: Sequence[Path],
        target: str,
        *,
        dry_run: bool,
    ) -> int:
        """Update version in each file, returning count of changed files."""
        changed = 0
        for path in files:
            if not path.exists():
                continue
            content = path.read_text(encoding=c.Infra.ENCODING_DEFAULT)
            match = c.Infra.VERSION_RE.search(content)
            if match and match.group(1) == target:
                continue
            changed += 1
            if not dry_run:
                u.Infra.replace_project_version(path.parent, target)
            self.logger.info(
                "release_version_file_updated",
                path=str(path),
                target=target,
            )
        return changed

    # These methods are defined in the main orchestrator class and
    # will be resolved via MRO when the main class inherits this mixin.
    def _build_targets(
        self,
        workspace_root: Path,
        project_names: t.StrSequence,
    ) -> Sequence[t.Infra.Pair[str, Path]]:
        raise NotImplementedError

    def _generate_notes(
        self,
        ctx: m.Infra.ReleasePhaseDispatchConfig,
        output_path: Path,
    ) -> r[bool]:
        raise NotImplementedError

    def _create_tag(self, workspace_root: Path, tag: str) -> r[bool]:
        raise NotImplementedError

    def _push_release(self, workspace_root: Path, tag: str) -> r[bool]:
        raise NotImplementedError

    def _version_files(
        self,
        workspace_root: Path,
        project_names: t.StrSequence,
    ) -> Sequence[Path]:
        raise NotImplementedError


__all__ = ["FlextInfraReleaseOrchestratorPhases"]
