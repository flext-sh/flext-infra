"""Single publication owner for validated codegen plans."""

from __future__ import annotations

from pathlib import Path

from flext_core import r
from flext_infra import m, p, u
from flext_infra.codegen.conform import FlextInfraCodegenConform


class FlextInfraCodegenPublisher:
    """Publish one prevalidated plan without owning planning or policy."""

    @staticmethod
    def _preflight_files(plan: m.Infra.CodegenPlan) -> p.Result[bool]:
        """Revalidate the complete live file set before the first write."""
        paths = tuple(item.path for item in plan.files)
        if len(set(paths)) != len(paths):
            return r[bool].fail("codegen plan contains duplicate managed paths")
        for item in plan.files:
            if item.blocked:
                return r[bool].fail(
                    item.reason or f"managed file is blocked: {item.path}"
                )
            if item.path.exists() and not item.path.is_file():
                return r[bool].fail(
                    f"managed destination is not a regular file: {item.path}"
                )
            current_digest = ""
            if item.path.is_file():
                current = u.Cli.files_read_text(item.path)
                if current.failure:
                    return r[bool].fail(
                        current.error or f"managed file read failed: {item.path}"
                    )
                current_digest = u.Cli.sha256_content(current.value)
            if current_digest != item.current_sha256:
                return r[bool].fail(f"managed file changed after planning: {item.path}")
        return r[bool].ok(True)

    @staticmethod
    def _preflight_beads(plan: m.Infra.CodegenPlan) -> p.Result[bool]:
        """Validate every external ledger dependency before file publication."""
        for beads_plan in plan.beads:
            verified = FlextInfraCodegenConform.verify_beads_plan(
                beads_plan, allow_missing=True
            )
            if verified.failure:
                return r[bool].fail(
                    verified.error or "Beads lifecycle preflight failed"
                )
        return r[bool].ok(True)

    @staticmethod
    def _apply_beads(plan: m.Infra.BeadsPlan) -> p.Result[bool]:
        """Apply the planned principal ledger lifecycle, then verify it."""
        if not plan.enabled:
            return r[bool].ok(False)
        beads_dir = plan.ledger_root / ".beads"
        changed = not beads_dir.exists()
        if changed:
            initialized = FlextInfraCodegenConform.run_beads_command(
                plan,
                "init",
                "--init-if-missing",
                "--non-interactive",
                "--skip-agents",
                "--prefix",
                plan.canonical_prefix,
            )
            if initialized.failure or initialized.value.exit_code != 0:
                return r[bool].fail(
                    f"Beads ledger initialization failed: {plan.ledger_root}"
                )
        verified = FlextInfraCodegenConform.verify_beads_plan(plan, allow_missing=False)
        if verified.failure:
            return r[bool].fail(
                verified.error or f"Beads ledger verification failed: {beads_dir}"
            )
        return r[bool].ok(changed)

    @classmethod
    def apply(cls, plan: m.Infra.CodegenPlan) -> p.Result[tuple[Path, ...]]:
        """Preflight the full plan, replace each file atomically, then apply Beads."""
        files_ready = cls._preflight_files(plan)
        if files_ready.failure:
            return r[tuple[Path, ...]].fail(
                files_ready.error or "codegen file preflight failed"
            )
        beads_ready = cls._preflight_beads(plan)
        if beads_ready.failure:
            return r[tuple[Path, ...]].fail(
                beads_ready.error or "Beads lifecycle preflight failed"
            )
        written: list[Path] = []
        for item in (candidate for candidate in plan.files if candidate.changed):
            applied = u.Cli.atomic_write_text_file(item.path, item.rendered)
            if applied.failure:
                return r[tuple[Path, ...]].fail(
                    applied.error or f"atomic codegen write failed: {item.path}"
                )
            written.append(item.path)
        for beads_plan in plan.beads:
            beads_applied = cls._apply_beads(beads_plan)
            if beads_applied.failure:
                return r[tuple[Path, ...]].fail(
                    beads_applied.error or "Beads lifecycle apply failed"
                )
        return r[tuple[Path, ...]].ok(tuple(written))


__all__: list[str] = ["FlextInfraCodegenPublisher"]
