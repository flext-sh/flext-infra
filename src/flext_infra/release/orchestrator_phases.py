"""Release phase implementations: build, publish, and version.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import hashlib
from collections.abc import MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import c, m, p, t, u
from flext_infra.release._orchestrator_publish import (
    FlextInfraReleaseOrchestratorPublishMixin,
)
from flext_infra.release._release_artifact_build import (
    FlextInfraReleaseArtifactBuildMixin,
)

logger = u.fetch_logger(__name__)


class FlextInfraReleaseOrchestratorPhases(
    FlextInfraReleaseOrchestratorPublishMixin, FlextInfraReleaseArtifactBuildMixin
):
    """Build and version phase implementations (publish via the mixin)."""

    if TYPE_CHECKING:

        def _build_targets(
            self, workspace_root: Path, project_names: t.StrSequence
        ) -> p.Result[t.SequenceOf[t.Pair[str, Path]]]: ...

        def _version_files(
            self, workspace_root: Path, project_names: t.StrSequence
        ) -> p.Result[t.SequenceOf[Path]]: ...

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
        target = f"{ctx.version}.dev0" if ctx.dev_suffix else ctx.version
        parse_result = u.Infra.parse_semver(target)
        if parse_result.failure:
            return r[bool].fail(parse_result.error or "invalid version")
        process_environment = u.Cli.process_env()
        if (
            not ctx.dry_run
            and process_environment.get(c.Infra.WORKTREE_TRANSACTION_ENV) != "1"
        ):
            return self._version_worktree_transaction(ctx)
        manifest_result = self._version_workspace_manifest_plan(
            ctx.workspace_root, target
        )
        if manifest_result.failure:
            return r[bool].fail(
                manifest_result.error or "workspace manifest version update failed"
            )
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
        manifest_changed = False
        for manifest_path, current_manifest, updated_manifest in manifest_result.value:
            manifest_changed = current_manifest != updated_manifest
            if manifest_changed and not ctx.dry_run:
                write_result = u.Cli.atomic_write_text_file(
                    manifest_path, updated_manifest
                )
                if write_result.failure:
                    return r[bool].fail(
                        write_result.error
                        or f"write workspace manifest version failed: {manifest_path}"
                    )
            if manifest_changed:
                logger.info(
                    "release_workspace_manifest_version_updated",
                    path=str(manifest_path),
                    target=target,
                )
        if ctx.dry_run:
            logger.info("release_phase_version_checked", checked_version=target)
        logger.info(
            "release_phase_version_summary",
            files_changed=changed_result.value,
            manifest_changed=manifest_changed,
        )
        return r[bool].ok(True)

    @staticmethod
    def _version_worktree_transaction(
        ctx: p.Infra.ReleasePhaseDispatchConfig,
    ) -> p.Result[bool]:
        """Apply one complete version delta through the canonical transaction."""
        command: t.MutableSequenceOf[str] = [
            c.Infra.CLI_GROUP_RELEASE,
            c.Infra.VERB_RUN,
            "--workspace",
            str(ctx.workspace_root),
            "--phase",
            c.Infra.ReleasePhase.VERSION,
            "--version",
            ctx.version,
            "--interactive",
            "0",
            "--create-branches",
            "0",
            "--apply",
        ]
        if ctx.project_names:
            command.extend(("--projects", ",".join(ctx.project_names)))
        if ctx.dev_suffix:
            command.append("--dev-suffix")
        transaction_result = u.Infra.execute_worktree_transaction(
            m.Infra.WorktreeTransactionRequest(
                workspace_root=ctx.workspace_root,
                command=tuple(command),
                apply_patch=True,
                timeout_seconds=c.Infra.WORKTREE_TRANSACTION_TIMEOUT_SECONDS,
            )
        )
        if transaction_result.failure:
            return r[bool].fail(
                transaction_result.error or "release version transaction failed"
            )
        report = transaction_result.value
        if report.breakage_detected or not report.applied:
            return r[bool].fail(u.Infra.render_worktree_transaction_report(report))
        logger.info(
            "release_phase_version_transaction",
            transaction_id=report.transaction_id,
            summary=report.summary,
        )
        return r[bool].ok(True)

    @staticmethod
    def _version_workspace_manifest_plan(
        workspace_root: Path, target: str
    ) -> p.Result[t.SequenceOf[t.Triple[Path, str, str]]]:
        """Render a validated round-trip manifest version update when declared."""
        manifest_path = (
            workspace_root / c.CONFIG_DIR_NAME / c.Infra.WORKSPACE_MANIFEST_FILENAME
        )
        if not manifest_path.is_file():
            return r[t.SequenceOf[t.Triple[Path, str, str]]].ok(())
        current_result = u.Cli.files_read_text(manifest_path)
        if current_result.failure:
            return r[t.SequenceOf[t.Triple[Path, str, str]]].fail(
                current_result.error
                or f"read workspace manifest failed: {manifest_path}"
            )
        loaded = u.Cli.yaml_roundtrip_load_map(manifest_path)
        if loaded.failure:
            return r[t.SequenceOf[t.Triple[Path, str, str]]].fail(
                loaded.error or f"parse workspace manifest failed: {manifest_path}"
            )
        document = loaded.value
        project = document.get(c.Infra.PROJECT)
        if not isinstance(project, MutableMapping):
            return r[t.SequenceOf[t.Triple[Path, str, str]]].fail(
                f"workspace manifest project must be a mapping: {manifest_path}"
            )
        current_version = project.get(c.Infra.VERSION)
        if not isinstance(current_version, str) or not current_version:
            return r[t.SequenceOf[t.Triple[Path, str, str]]].fail(
                f"workspace manifest project.version is missing: {manifest_path}"
            )
        project[c.Infra.VERSION] = target
        try:
            _ = m.Infra.WorkspaceSpec.model_validate(u.Cli.yaml_to_plain(document))
        except c.ValidationError as exc:
            return r[t.SequenceOf[t.Triple[Path, str, str]]].fail_op(
                f"validate workspace manifest version ({manifest_path})", exc
            )
        rendered = u.Cli.yaml_roundtrip_dump_text(document)
        if rendered.failure:
            return r[t.SequenceOf[t.Triple[Path, str, str]]].fail(
                rendered.error or f"render workspace manifest failed: {manifest_path}"
            )
        return r[t.SequenceOf[t.Triple[Path, str, str]]].ok((
            (manifest_path, current_result.value, rendered.value),
        ))

    def _version_update_files(
        self, files: t.SequenceOf[Path], target: str, *, dry_run: bool
    ) -> p.Result[int]:
        """Update version in each file, returning count of changed files."""
        updates: t.MutableSequenceOf[t.Triple[Path, str, str]] = []
        for path in files:
            content_result = u.Cli.files_read_text(path)
            if content_result.failure:
                return r[int].fail(
                    content_result.error or f"read version file failed: {path}"
                )
            match = c.Infra.VERSION_RE.search(content_result.value)
            if match and match.group(1) == target:
                continue
            rendered = u.Infra.render_project_version(content_result.value, target)
            if rendered.failure:
                return r[int].fail(f"{rendered.error} in {path}")
            updates.append((path, content_result.value, rendered.value))

        for path, _current, updated in updates:
            if not dry_run:
                write_result = u.Cli.atomic_write_text_file(path, updated)
                if write_result.failure:
                    return r[int].fail(
                        write_result.error or f"write project version failed: {path}"
                    )
            logger.info("release_version_file_updated", path=str(path), target=target)
        return r[int].ok(len(updates))


__all__: list[str] = ["FlextInfraReleaseOrchestratorPhases"]
