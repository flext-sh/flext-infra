"""Immutable persistence and atomic executable activation for managed Git tools."""

from __future__ import annotations

import os
import shutil
from pathlib import Path
from tempfile import TemporaryDirectory
from flext_core import r
from flext_infra import c, m, p, u
from flext_infra.release._managed_git_tool_build import (
    FlextInfraManagedGitToolBuildMixin,
)


class FlextInfraManagedGitToolInstallMixin(FlextInfraManagedGitToolBuildMixin):
    """Persist a complete receipt set and atomically activate its executable."""

    @staticmethod
    def _managed_store_path(spec: m.Infra.ManagedGitToolRelease) -> Path:
        return (spec.artifact_store / spec.release_name / spec.commit_oid).resolve()

    @classmethod
    def _managed_git_tool_receipt(
        cls,
        spec: m.Infra.ManagedGitToolRelease,
        stage: m.Infra.ManagedGitToolSourceStage,
        probes: tuple[m.Infra.ManagedGitToolProbeReceipt, ...],
    ) -> p.Result[m.Infra.ManagedGitToolReleaseReceipt]:
        store = cls._managed_store_path(spec)
        stored_artifact = store / stage.artifact_path.name
        try:
            size = stage.artifact_path.stat().st_size
        except OSError as exc:
            return r[m.Infra.ManagedGitToolReleaseReceipt].fail_op(
                f"inspect managed Git tool artifact {stage.artifact_path}", exc
            )
        return r[m.Infra.ManagedGitToolReleaseReceipt].ok(
            m.Infra.ManagedGitToolReleaseReceipt(
                release_name=spec.release_name,
                source_url=spec.source_url,
                commit_oid=stage.snapshot.commit_oid,
                source_date_epoch=stage.snapshot.source_date_epoch,
                source_archive_sha256=stage.source_archive_sha256,
                artifact=m.Infra.ManagedGitToolArtifactReceipt(
                    store_path=stored_artifact,
                    install_path=spec.artifact.install_path,
                    sha256=spec.artifact.sha256,
                    size=size,
                ),
                probes=probes,
                receipt_path=store / c.Infra.MANAGED_GIT_TOOL_RECEIPT_FILENAME,
            )
        )

    @classmethod
    def _persist_managed_git_tool(
        cls,
        receipt: m.Infra.ManagedGitToolReleaseReceipt,
        stage: m.Infra.ManagedGitToolSourceStage,
        temporary_root: Path,
    ) -> p.Result[bool]:
        receipt_source = temporary_root / c.Infra.MANAGED_GIT_TOOL_RECEIPT_FILENAME
        rendered = receipt.model_dump_json(indent=2) + "\n"
        written = u.Cli.files_write_text(receipt_source, rendered)
        if written.failure:
            return r[bool].fail(written.error or "write managed release receipt failed")
        files = (
            (stage.artifact_path, receipt.artifact.sha256),
            (receipt_source, u.Cli.sha256_file(receipt_source)),
        )
        persisted = cls._persist_file_set(files, receipt.receipt_path.parent)
        if persisted.failure:
            return r[bool].fail(
                persisted.error or "persist managed release artifact set failed"
            )
        if u.Cli.sha256_file(receipt.artifact.store_path) != receipt.artifact.sha256:
            return r[bool].fail("persisted managed executable digest mismatch")
        persisted_receipt = u.Cli.files_read_text(receipt.receipt_path)
        if persisted_receipt.failure or persisted_receipt.value != rendered:
            return r[bool].fail(
                persisted_receipt.error or "persisted managed receipt differs"
            )
        return r[bool].ok(True)

    @staticmethod
    def _activate_managed_git_tool(
        receipt: m.Infra.ManagedGitToolReleaseReceipt,
    ) -> p.Result[bool]:
        source = receipt.artifact.store_path
        destination = receipt.artifact.install_path
        if destination.is_symlink():
            return r[bool].fail(
                f"managed executable destination must not be a symlink: {destination}"
            )
        if destination.exists() and not destination.is_file():
            return r[bool].fail(
                f"managed executable destination is not a file: {destination}"
            )
        if destination.is_file() and (
            u.Cli.sha256_file(destination) == receipt.artifact.sha256
            and os.access(destination, os.X_OK)
        ):
            return r[bool].ok(True)
        ensured = u.Cli.ensure_dir(destination.parent)
        if ensured.failure:
            return r[bool].fail(
                ensured.error or "managed executable parent creation failed"
            )
        try:
            with TemporaryDirectory(
                prefix=f".{destination.name}-", dir=destination.parent
            ) as temporary:
                staged = Path(temporary) / destination.name
                shutil.copy2(source, staged)
                if u.Cli.sha256_file(
                    staged
                ) != receipt.artifact.sha256 or not os.access(staged, os.X_OK):
                    return r[bool].fail(
                        "managed executable activation staging validation failed"
                    )
                staged.replace(destination)
        except OSError as exc:
            return r[bool].fail_op(
                f"atomically activate managed executable {destination}", exc
            )
        if u.Cli.sha256_file(destination) != receipt.artifact.sha256 or not os.access(
            destination, os.X_OK
        ):
            return r[bool].fail("activated managed executable validation failed")
        return r[bool].ok(True)

    @classmethod
    def _finish_managed_git_tool_release(
        cls,
        spec: m.Infra.ManagedGitToolRelease,
        stage: m.Infra.ManagedGitToolSourceStage,
        probes: tuple[m.Infra.ManagedGitToolProbeReceipt, ...],
        temporary_root: Path,
        *,
        apply: bool,
    ) -> p.Result[m.Infra.ManagedGitToolReleaseResult]:
        receipt_result = cls._managed_git_tool_receipt(spec, stage, probes)
        if receipt_result.failure:
            return r[m.Infra.ManagedGitToolReleaseResult].fail(
                receipt_result.error or "managed release receipt failed"
            )
        receipt = receipt_result.value
        if not apply:
            return r[m.Infra.ManagedGitToolReleaseResult].ok(
                m.Infra.ManagedGitToolReleaseResult(
                    receipt=receipt, persisted=False, activated=False
                )
            )
        persisted = cls._persist_managed_git_tool(receipt, stage, temporary_root)
        if persisted.failure:
            return r[m.Infra.ManagedGitToolReleaseResult].fail(
                persisted.error or "managed release persistence failed"
            )
        activated = cls._activate_managed_git_tool(receipt)
        if activated.failure:
            return r[m.Infra.ManagedGitToolReleaseResult].fail(
                activated.error or "managed executable activation failed"
            )
        return r[m.Infra.ManagedGitToolReleaseResult].ok(
            m.Infra.ManagedGitToolReleaseResult(
                receipt=receipt, persisted=True, activated=True
            )
        )


__all__: list[str] = ["FlextInfraManagedGitToolInstallMixin"]
