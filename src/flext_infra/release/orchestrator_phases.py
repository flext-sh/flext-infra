"""Release phase implementations: build, publish, and version.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_core import r
from flext_infra import c, m, p, t, u
from flext_infra.release._orchestrator_publish import (
    FlextInfraReleaseOrchestratorPublishMixin,
)

logger = u.fetch_logger(__name__)


class FlextInfraReleaseOrchestratorPhases(FlextInfraReleaseOrchestratorPublishMixin):
    """Build and version phase implementations (publish via the mixin)."""

    @staticmethod
    def _run_make(project_path: Path, verb: str) -> p.Result[t.Pair[int, str]]:
        """Execute a make command for a project and return (exit_code, output)."""
        result = u.Cli.run_raw([c.Infra.MAKE, "-C", str(project_path), verb])
        if result.failure:
            return r[t.Pair[int, str]].fail(result.error or "make execution failed")
        output_model = result.value
        output = (output_model.stdout + "\n" + output_model.stderr).strip()
        return r[t.Pair[int, str]].ok((output_model.exit_code, output))

    def phase_build(self, ctx: p.Infra.ReleasePhaseDispatchConfig) -> p.Result[bool]:
        """Execute the build phase and write build-report.json."""
        workspace_root = ctx.workspace_root
        version = ctx.version
        project_names = ctx.project_names
        output_dir = (
            u.Cli.resolve_report_dir(
                workspace_root, c.Infra.PROJECT, c.Infra.RK_RELEASE
            )
            / f"v{version}"
        )
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            return r[bool].fail_op("report dir creation", exc)
        targets = self._build_targets(workspace_root, project_names)
        records: t.MutableSequenceOf[p.Infra.BuildRecord] = []
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
            u.write_file(log, output + "\n", encoding=c.Cli.ENCODING_DEFAULT)
            records.append(
                m.Infra.BuildRecord(
                    project=name, path=str(path), exit_code=code, log=str(log)
                )
            )
            logger.info("release_phase_build_project", project=name, exit_code=code)
        report = m.Infra.BuildReport(
            version=version,
            total=len(records),
            failures=failures,
            records=list(records),
        )
        u.Cli.json_write(
            output_dir / "build-report.json",
            report.model_dump(mode="json"),
            m.Cli.JsonWriteOptions(sort_keys=True),
        )
        logger.info(
            "release_phase_build_report", report=str(output_dir / "build-report.json")
        )
        if failures:
            return r[bool].fail(f"build failed: {failures} project(s)")
        return r[bool].ok(True)

    def phase_version(self, ctx: p.Infra.ReleasePhaseDispatchConfig) -> p.Result[bool]:
        """Execute versioning phase across workspace and selected projects."""
        target = f"{ctx.version}-dev" if ctx.dev_suffix else ctx.version
        parse_result = u.Infra.parse_semver(ctx.version)
        if parse_result.failure:
            return r[bool].fail(parse_result.error or "invalid version")
        files = self._version_files(ctx.workspace_root, ctx.project_names)
        changed = self._version_update_files(files, target, dry_run=ctx.dry_run)
        if ctx.dry_run:
            logger.info("release_phase_version_checked", checked_version=target)
        logger.info("release_phase_version_summary", files_changed=changed)
        return r[bool].ok(True)

    def _version_update_files(
        self, files: t.SequenceOf[Path], target: str, *, dry_run: bool
    ) -> int:
        """Update version in each file, returning count of changed files."""
        changed = 0
        for path in files:
            if not path.exists():
                continue
            content = u.Cli.files_read_text(path).unwrap()
            match = c.Infra.VERSION_RE.search(content)
            if match and match.group(1) == target:
                continue
            changed += 1
            if not dry_run:
                u.Infra.replace_project_version(path.parent, target)
            logger.info("release_version_file_updated", path=str(path), target=target)
        return changed

    # These methods are defined in the main orchestrator class and
    # will be resolved via MRO when the main class inherits this mixin.
    def _build_targets(
        self, workspace_root: Path, project_names: t.StrSequence
    ) -> t.SequenceOf[t.Pair[str, Path]]:
        """Build targets."""
        raise NotImplementedError

    def _version_files(
        self, workspace_root: Path, project_names: t.StrSequence
    ) -> t.SequenceOf[Path]:
        """Version files."""
        raise NotImplementedError


__all__: list[str] = ["FlextInfraReleaseOrchestratorPhases"]
