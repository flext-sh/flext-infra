"""Release phase implementations: build, publish, and version.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import c, m, t, u
from flext_infra.release._orchestrator_publish import (
    FlextInfraReleaseOrchestratorPublishMixin,
)
from flext_infra.release._release_artifact_build import (
    FlextInfraReleaseArtifactBuildMixin,
)

if TYPE_CHECKING:
    from flext_infra import p

logger = u.fetch_logger(__name__)


class FlextInfraReleaseOrchestratorPhases(
    FlextInfraReleaseOrchestratorPublishMixin, FlextInfraReleaseArtifactBuildMixin
):
    """Build and version phase implementations (publish via the mixin)."""

    def _build_project_record(
        self,
        ctx: p.Infra.ReleasePhaseDispatchConfig,
        policy: p.Infra.BuildPolicy,
        name: str,
        path: Path,
        output_dir: Path,
    ) -> p.Result[p.Infra.BuildRecord]:
        """Build one project and convert fail-loud errors into report records."""
        record_result = self._build_release_record(
            project=name,
            project_path=path,
            output_dir=output_dir,
            build_constraints_path=Path(policy.build_constraints_path),
            gitleaks_config_path=Path(policy.gitleaks_policy_path),
            version=ctx.version,
            dry_run=ctx.dry_run,
        )
        if record_result.success:
            return record_result
        log = output_dir / f"build-{name}.log"
        write_result = self._write_release_text(
            log, (record_result.error or "release build failed") + "\n"
        )
        if write_result.failure:
            return r[p.Infra.BuildRecord].fail(
                write_result.error or f"write failed build log: {name}"
            )
        return r[p.Infra.BuildRecord].ok(
            self._build_record(
                project=name, project_path=path, log_path=log, exit_code=1
            )
        )

    def _build_records(
        self,
        ctx: p.Infra.ReleasePhaseDispatchConfig,
        policy: p.Infra.BuildPolicy,
        targets: t.SequenceOf[t.Pair[str, Path]],
        output_dir: Path,
    ) -> p.Result[t.SequenceOf[p.Infra.BuildRecord]]:
        """Build every selected project and retain its strict report record."""
        records: t.MutableSequenceOf[p.Infra.BuildRecord] = []
        for name, path in targets:
            record_result = self._build_project_record(
                ctx, policy, name, path, output_dir
            )
            if record_result.failure:
                return r[t.SequenceOf[p.Infra.BuildRecord]].fail(
                    record_result.error or f"release build record failed: {name}"
                )
            record = record_result.value
            records.append(record)
            logger.info(
                "release_phase_build_project", project=name, exit_code=record.exit_code
            )
        return r[t.SequenceOf[p.Infra.BuildRecord]].ok(tuple(records))

    @staticmethod
    def _snapshot_policy_file(source: Path, destination: Path) -> p.Result[str]:
        """Persist immutable policy bytes and return their SHA-256 digest."""
        try:
            content = source.read_bytes()
        except OSError as exc:
            return r[str].fail_op(f"read release policy {source}", exc)
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            return r[str].fail_op(
                f"create release policy directory {destination.parent}", exc
            )
        try:
            if destination.exists():
                if destination.read_bytes() != content:
                    return r[str].fail(
                        f"immutable release policy collision: {destination}"
                    )
            else:
                destination.write_bytes(content)
            return r[str].ok(hashlib.sha256(content).hexdigest())
        except OSError as exc:
            return r[str].fail_op(f"persist release policy {destination}", exc)

    @classmethod
    def _snapshot_build_policy(
        cls, workspace_root: Path, output_dir: Path
    ) -> p.Result[p.Infra.BuildPolicy]:
        """Capture one immutable policy pair before the first project build."""
        policy_dir = output_dir / "policy"
        constraints_path = policy_dir / "build-constraints.txt"
        constraints_result = cls._snapshot_policy_file(
            workspace_root / c.Infra.RELEASE_BUILD_CONSTRAINTS_PATH, constraints_path
        )
        if constraints_result.failure:
            return r[p.Infra.BuildPolicy].fail(
                constraints_result.error or "snapshot build constraints failed"
            )
        gitleaks_path = policy_dir / "gitleaks-release.toml"
        gitleaks_result = cls._snapshot_policy_file(
            workspace_root / c.Infra.RELEASE_GITLEAKS_CONFIG_PATH, gitleaks_path
        )
        if gitleaks_result.failure:
            return r[p.Infra.BuildPolicy].fail(
                gitleaks_result.error or "snapshot Gitleaks policy failed"
            )
        return r[p.Infra.BuildPolicy].ok(
            m.Infra.BuildPolicy(
                build_constraints_path=str(constraints_path.resolve()),
                build_constraints_sha256=constraints_result.value,
                gitleaks_policy_path=str(gitleaks_path.resolve()),
                gitleaks_policy_sha256=gitleaks_result.value,
            )
        )

    @classmethod
    def _write_build_report(
        cls,
        ctx: p.Infra.ReleasePhaseDispatchConfig,
        policy: p.Infra.BuildPolicy,
        output_dir: Path,
        records: t.SequenceOf[p.Infra.BuildRecord],
    ) -> p.Result[int]:
        """Persist the strict build report and return its failure count."""
        failures = sum(record.exit_code != 0 for record in records)
        report = m.Infra.BuildReport(
            version=ctx.version,
            total=len(records),
            failures=failures,
            records=tuple(records),
            dry_run=ctx.dry_run,
            build_constraints_sha256=policy.build_constraints_sha256,
            gitleaks_policy_sha256=policy.gitleaks_policy_sha256,
        )
        write_result = u.Cli.json_write(
            output_dir / "build-report.json",
            report.model_dump(mode="json"),
            m.Cli.JsonWriteOptions(sort_keys=True),
        )
        if write_result.failure:
            return r[int].fail(write_result.error or "write build report failed")
        logger.info(
            "release_phase_build_report", report=str(output_dir / "build-report.json")
        )
        return r[int].ok(failures)

    def phase_build(self, ctx: p.Infra.ReleasePhaseDispatchConfig) -> p.Result[bool]:
        """Build registry-safe member artifacts and write build-report.json."""
        output_dir = (
            u.Cli.resolve_report_dir(
                ctx.workspace_root, c.Infra.PROJECT, c.Infra.RK_RELEASE
            )
            / f"v{ctx.version}"
        )
        try:
            output_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            return r[bool].fail_op("report dir creation", exc)
        targets_result = self._build_targets(ctx.workspace_root, ctx.project_names)
        if targets_result.failure:
            return r[bool].fail(
                targets_result.error or "release build target resolution failed"
            )
        if not targets_result.value:
            return r[bool].fail("release build selected no publishable projects")
        policy_result = self._snapshot_build_policy(ctx.workspace_root, output_dir)
        if policy_result.failure:
            return r[bool].fail(
                policy_result.error or "release build policy snapshot failed"
            )
        records_result = self._build_records(
            ctx, policy_result.value, targets_result.value, output_dir
        )
        if records_result.failure:
            return r[bool].fail(records_result.error or "release build records failed")
        report_result = self._write_build_report(
            ctx, policy_result.value, output_dir, records_result.value
        )
        if report_result.failure:
            return r[bool].fail(report_result.error or "write build report failed")
        if report_result.value:
            return r[bool].fail(f"build failed: {report_result.value} project(s)")
        return r[bool].ok(True)

    def phase_version(self, ctx: p.Infra.ReleasePhaseDispatchConfig) -> p.Result[bool]:
        """Execute versioning phase across workspace and selected projects."""
        target = f"{ctx.version}-dev" if ctx.dev_suffix else ctx.version
        parse_result = u.Infra.parse_semver(ctx.version)
        if parse_result.failure:
            return r[bool].fail(parse_result.error or "invalid version")
        files_result = self._version_files(ctx.workspace_root, ctx.project_names)
        if files_result.failure:
            return r[bool].fail(
                files_result.error or "release version file resolution failed"
            )
        changed_result = self._version_update_files(
            files_result.value, target, dry_run=ctx.dry_run
        )
        if changed_result.failure:
            return r[bool].fail(changed_result.error or "release version update failed")
        if ctx.dry_run:
            logger.info("release_phase_version_checked", checked_version=target)
        logger.info("release_phase_version_summary", files_changed=changed_result.value)
        return r[bool].ok(True)

    def _version_update_files(
        self, files: t.SequenceOf[Path], target: str, *, dry_run: bool
    ) -> p.Result[int]:
        """Update version in each file, returning count of changed files."""
        changed = 0
        for path in files:
            content_result = u.Cli.files_read_text(path)
            if content_result.failure:
                return r[int].fail(
                    content_result.error or f"read version file failed: {path}"
                )
            match = c.Infra.VERSION_RE.search(content_result.value)
            if match and match.group(1) == target:
                continue
            changed += 1
            if not dry_run:
                replace_result = u.Infra.replace_project_version(path.parent, target)
                if replace_result.failure:
                    return r[int].fail(
                        replace_result.error
                        or f"replace project version failed: {path}"
                    )
            logger.info("release_version_file_updated", path=str(path), target=target)
        return r[int].ok(changed)


__all__: list[str] = ["FlextInfraReleaseOrchestratorPhases"]
