"""Deterministic build and staged runtime probes for managed Git tools."""

from __future__ import annotations

import os
from pathlib import Path
from flext_core import r
from flext_infra import c, m, p, t, u
from flext_infra.release._managed_git_tool_source import (
    FlextInfraManagedGitToolSourceMixin,
)


class FlextInfraManagedGitToolBuildMixin(FlextInfraManagedGitToolSourceMixin):
    """Build one staged executable and prove its real public behavior."""

    @staticmethod
    def _expand_managed_command(
        command: t.StrSequence, stage: m.Infra.ManagedGitToolSourceStage
    ) -> p.Result[t.StrSequence]:
        replacements = {
            c.Infra.MANAGED_GIT_TOOL_ARTIFACT_PLACEHOLDER: str(stage.artifact_path),
            c.Infra.MANAGED_GIT_TOOL_OUTPUT_PLACEHOLDER: str(stage.output_root),
            c.Infra.MANAGED_GIT_TOOL_SOURCE_PLACEHOLDER: str(stage.source_root),
        }
        expanded: list[str] = []
        for raw_token in command:
            token = raw_token
            for marker, value in replacements.items():
                token = token.replace(marker, value)
            if "{" in token or "}" in token:
                return r[t.StrSequence].fail(
                    f"managed command contains an unknown placeholder: {raw_token}"
                )
            expanded.append(token)
        if not expanded or not Path(expanded[0]).is_absolute():
            return r[t.StrSequence].fail(
                "managed command executable must resolve to an absolute path"
            )
        return r[t.StrSequence].ok(tuple(expanded))

    @staticmethod
    def _managed_build_environment(
        spec: m.Infra.ManagedGitToolRelease, stage: m.Infra.ManagedGitToolSourceStage
    ) -> dict[str, str]:
        environment = {item.name: item.value for item in spec.build_environment}
        environment["SOURCE_DATE_EPOCH"] = str(stage.snapshot.source_date_epoch)
        return environment

    @classmethod
    def _build_managed_git_tool(
        cls,
        spec: m.Infra.ManagedGitToolRelease,
        stage: m.Infra.ManagedGitToolSourceStage,
    ) -> p.Result[bool]:
        command_result = cls._expand_managed_command(spec.build_command, stage)
        if command_result.failure:
            return r[bool].fail(
                command_result.error or "managed build command expansion failed"
            )
        if stage.artifact_path.exists():
            return r[bool].fail(
                f"managed build artifact already exists: {stage.artifact_path}"
            )
        build = u.Cli.run_raw(
            command_result.value,
            cwd=stage.source_root,
            timeout=c.Infra.TIMEOUT_LONG,
            env=cls._managed_build_environment(spec, stage),
            remove_env_keys=tuple(os.environ),
        )
        if build.failure:
            return r[bool].fail(build.error or "managed Git tool build failed")
        if build.value.exit_code != 0:
            detail = (build.value.stderr or build.value.stdout).strip()
            return r[bool].fail(
                detail or f"managed Git tool build exited {build.value.exit_code}"
            )
        artifact = stage.artifact_path
        if not artifact.is_file() or artifact.is_symlink():
            return r[bool].fail(
                f"managed build did not emit one regular file: {artifact}"
            )
        if not os.access(artifact, os.X_OK):
            return r[bool].fail(f"managed build artifact is not executable: {artifact}")
        observed_digest = u.Cli.sha256_file(artifact)
        if observed_digest != spec.artifact.sha256:
            return r[bool].fail(
                "managed build artifact SHA-256 mismatch: "
                f"expected {spec.artifact.sha256}, found {observed_digest}"
            )
        return r[bool].ok(True)

    @classmethod
    def _probe_managed_git_tool(
        cls,
        spec: m.Infra.ManagedGitToolRelease,
        stage: m.Infra.ManagedGitToolSourceStage,
    ) -> p.Result[tuple[m.Infra.ManagedGitToolProbeReceipt, ...]]:
        receipts: list[m.Infra.ManagedGitToolProbeReceipt] = []
        for probe in spec.probes:
            command_result = cls._expand_managed_command(probe.command, stage)
            if command_result.failure:
                return r[tuple[m.Infra.ManagedGitToolProbeReceipt, ...]].fail(
                    command_result.error
                    or f"managed probe expansion failed: {probe.name}"
                )
            observed = u.Cli.run_raw(
                command_result.value,
                cwd=stage.source_root,
                timeout=c.Infra.TIMEOUT_MEDIUM,
                env=cls._managed_build_environment(spec, stage),
                remove_env_keys=tuple(os.environ),
            )
            if observed.failure:
                return r[tuple[m.Infra.ManagedGitToolProbeReceipt, ...]].fail(
                    observed.error or f"managed probe execution failed: {probe.name}"
                )
            if observed.value.exit_code != 0:
                detail = (observed.value.stderr or observed.value.stdout).strip()
                return r[tuple[m.Infra.ManagedGitToolProbeReceipt, ...]].fail(
                    detail or f"managed probe exited non-zero: {probe.name}"
                )
            output = f"{observed.value.stdout}\n{observed.value.stderr}"
            missing = tuple(
                fragment
                for fragment in probe.expected_output_contains
                if fragment not in output
            )
            if missing:
                return r[tuple[m.Infra.ManagedGitToolProbeReceipt, ...]].fail(
                    f"managed probe {probe.name} lacks required output: "
                    f"{', '.join(missing)}"
                )
            receipts.append(
                m.Infra.ManagedGitToolProbeReceipt(
                    name=probe.name,
                    command=command_result.value,
                    stdout=observed.value.stdout,
                    stderr=observed.value.stderr,
                    output_sha256=u.Cli.sha256_content(output),
                )
            )
        return r[tuple[m.Infra.ManagedGitToolProbeReceipt, ...]].ok(tuple(receipts))


__all__: list[str] = ["FlextInfraManagedGitToolBuildMixin"]
