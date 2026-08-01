"""Public managed Git tool release service."""

from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Annotated, override

from flext_core import r
from flext_infra import c, m, p, u
from flext_infra.base import s
from flext_infra.release._managed_git_tool_install import (
    FlextInfraManagedGitToolInstallMixin,
)


class FlextInfraManagedGitToolRelease(
    FlextInfraManagedGitToolInstallMixin, s[m.Infra.ManagedGitToolReleaseResult]
):
    """Acquire, build, probe, persist, and activate one exact Git executable."""

    manifest: Annotated[
        Path, m.Field(description="JSON ManagedGitToolRelease manifest path")
    ]

    @classmethod
    def release(
        cls, spec: m.Infra.ManagedGitToolRelease, *, apply: bool
    ) -> p.Result[m.Infra.ManagedGitToolReleaseResult]:
        """Execute the complete managed release transaction for one typed spec."""
        try:
            with TemporaryDirectory(prefix="flext-managed-git-tool-") as temporary:
                return cls._release_in_temporary_root(
                    spec, Path(temporary), apply=apply
                )
        except OSError as exc:
            return r[m.Infra.ManagedGitToolReleaseResult].fail_op(
                "manage isolated Git tool release transaction", exc
            )

    @classmethod
    def _release_in_temporary_root(
        cls, spec: m.Infra.ManagedGitToolRelease, temporary_root: Path, *, apply: bool
    ) -> p.Result[m.Infra.ManagedGitToolReleaseResult]:
        """Run the release stages within one already-isolated directory."""
        source = cls._prepare_managed_git_source(spec, temporary_root)
        if source.failure:
            return r[m.Infra.ManagedGitToolReleaseResult].fail(
                source.error or "managed Git source preparation failed"
            )
        built = cls._build_managed_git_tool(spec, source.value)
        if built.failure:
            return r[m.Infra.ManagedGitToolReleaseResult].fail(
                built.error or "managed Git tool build failed"
            )
        probes = cls._probe_managed_git_tool(spec, source.value)
        if probes.failure:
            return r[m.Infra.ManagedGitToolReleaseResult].fail(
                probes.error or "managed Git tool probe failed"
            )
        return cls._finish_managed_git_tool_release(
            spec, source.value, probes.value, temporary_root, apply=apply
        )

    @override
    def execute(self) -> p.Result[m.Infra.ManagedGitToolReleaseResult]:
        """Load one strict JSON manifest and execute its release transaction."""
        manifest_path = (
            self.manifest
            if self.manifest.is_absolute()
            else (self.workspace_root / self.manifest).resolve()
        )
        read = u.Cli.files_read_text(manifest_path)
        if read.failure:
            return r[m.Infra.ManagedGitToolReleaseResult].fail(
                read.error or f"read managed Git tool manifest failed: {manifest_path}"
            )
        try:
            spec = m.Infra.ManagedGitToolRelease.model_validate_json(read.value)
        except c.ValidationError as exc:
            return r[m.Infra.ManagedGitToolReleaseResult].fail_op(
                f"validate managed Git tool manifest {manifest_path}", exc
            )
        return self.release(spec, apply=self.apply_changes)


__all__: list[str] = ["FlextInfraManagedGitToolRelease"]
