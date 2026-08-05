"""Batch ast-grep rule application guarded by the operator safety circuit.

Circuit contract (``make mod APPLY=Y``): measure ruff + pyrefly error counts
before the batch apply, checkpoint the tree (commit when dirty), apply every
rule declared by the project sgconfig, then re-measure. Any count increase
rolls the tree back to the checkpoint and fails loud; equal or lower counts
keep the applied fixes.
"""  # ruff:ignore[implicit-namespace-package]

from __future__ import annotations

from pathlib import Path
from typing import Annotated, Final, override

from flext_cli import cli
from flext_infra import m, p, r, t, u
from flext_infra.base import FlextInfraServiceBase
from flext_infra.codemod.batch_gates import (
    FlextInfraModGateEngine,
    FlextInfraModGateSnapshot,
)

_CHECKPOINT_MESSAGE: Final[str] = "chore(git): checkpoint before ast-grep batch apply"
_SGCONFIG_FILENAME: Final[str] = "sgconfig.yml"


class FlextInfraCodemodBatchApply(FlextInfraServiceBase[t.Cli.ResultValue]):
    """Apply one sgconfig's ast-grep rules under the baseline rollback circuit."""

    config: Annotated[
        str | None,
        m.Field(
            description="ast-grep sgconfig path; defaults to <workspace>/sgconfig.yml"
        ),
    ] = None

    @staticmethod
    def _checkpoint(root: Path) -> p.Result[str]:
        """Record the pre-apply state: checkpoint commit when dirty, else HEAD."""
        status = u.Infra.git_status(m.Infra.GitStatusRequest(repo_root=root))
        if status.failure:
            return r[str].fail(status.error or "git status failed")
        if status.value.dirty:
            checkpoint = u.Infra.git_checkpoint_worktree(
                root, message=_CHECKPOINT_MESSAGE
            )
            if checkpoint.failure:
                return r[str].fail(checkpoint.error or "checkpoint commit failed")
            return r[str].ok(checkpoint.value)
        head = u.Infra.git_repository_head(m.Infra.GitRepoRequest(repo_root=root))
        if head.failure:
            return r[str].fail(head.error or "failed to resolve HEAD")
        return r[str].ok(head.value.oid)

    @staticmethod
    def _rollback(root: Path, checkpoint_sha: str) -> str | None:
        """Restore tracked paths to the checkpoint; return an error on failure."""
        restored = u.Infra.git_checkout_restore(m.Infra.GitRepoRequest(repo_root=root))
        if restored.failure:
            return (
                restored.error
                or f"rollback failed; restore manually to {checkpoint_sha}"
            )
        return None

    def _sgconfig(self) -> p.Result[Path]:
        """Resolve the sgconfig the batch apply consumes."""
        candidate = (
            Path(self.config).resolve()
            if self.config
            else self.workspace_root / _SGCONFIG_FILENAME
        )
        if not candidate.is_file():
            return r[Path].fail(f"ast-grep sgconfig not found: {candidate}")
        return r[Path].ok(candidate)

    @override
    def execute(self) -> p.Result[t.Cli.ResultValue]:
        """Run check mode (report pending fixes) or the guarded apply circuit."""
        root = self.workspace_root
        config_result = self._sgconfig()
        if config_result.failure:
            return r[t.Cli.ResultValue].fail(
                config_result.error or "sgconfig resolution failed"
            )
        config = config_result.value
        effective_dry_run: bool = self.effective_dry_run
        if effective_dry_run:
            pending = FlextInfraModGateEngine.scan(root, config, fix=False)
            if pending.failure:
                return r[t.Cli.ResultValue].fail(
                    pending.error or "ast-grep scan failed"
                )
            if pending.value:
                return r[t.Cli.ResultValue].fail(
                    f"{pending.value} pending ast-grep fix(es) under {config}"
                )
            cli.display_text("mod: no pending ast-grep fixes")
            return r[t.Cli.ResultValue].ok(True)
        return self._execute_apply(root, config)

    def _execute_apply(self, root: Path, config: Path) -> p.Result[t.Cli.ResultValue]:
        """Measure, checkpoint, batch-apply, re-measure, roll back on regression."""
        baseline = FlextInfraModGateEngine.measure(root)
        if baseline.failure:
            return r[t.Cli.ResultValue].fail(
                baseline.error or "baseline measure failed"
            )
        checkpoint = self._checkpoint(root)
        if checkpoint.failure:
            return r[t.Cli.ResultValue].fail(checkpoint.error or "checkpoint failed")
        checkpoint_sha = checkpoint.value
        pending = FlextInfraModGateEngine.scan(root, config, fix=False)
        if pending.failure:
            return r[t.Cli.ResultValue].fail(pending.error or "ast-grep scan failed")
        applied = FlextInfraModGateEngine.scan(root, config, fix=True)
        if applied.failure:
            return self._fail_with_rollback(
                root, checkpoint_sha, applied.error or "ast-grep fix pass failed"
            )
        final = FlextInfraModGateEngine.measure(root)
        if final.failure:
            return r[t.Cli.ResultValue].fail(final.error or "final measure failed")
        if FlextInfraModGateEngine.circuit_broken(baseline.value, final.value):
            regression = (
                f"mod circuit: gates regressed "
                f"(ruff {baseline.value.ruff_errors}→{final.value.ruff_errors}, "
                f"pyrefly {baseline.value.pyrefly_errors}→{final.value.pyrefly_errors})"
            )
            return self._fail_with_rollback(root, checkpoint_sha, regression)
        cli.display_text(
            f"mod: applied {pending.value} ast-grep fix(es); "
            f"ruff {baseline.value.ruff_errors}→{final.value.ruff_errors}, "
            f"pyrefly {baseline.value.pyrefly_errors}→{final.value.pyrefly_errors}; "
            f"checkpoint {checkpoint_sha}"
        )
        return r[t.Cli.ResultValue].ok(True)

    @staticmethod
    def _fail_with_rollback(
        root: Path, checkpoint_sha: str, detail: str
    ) -> p.Result[t.Cli.ResultValue]:
        """Roll back to the checkpoint and fail loud with the circuit detail."""
        rollback_error = FlextInfraCodemodBatchApply._rollback(root, checkpoint_sha)
        if rollback_error is not None:
            return r[t.Cli.ResultValue].fail(f"{detail}; {rollback_error}")
        return r[t.Cli.ResultValue].fail(f"{detail}; rolled back to {checkpoint_sha}")


__all__: list[str] = ["FlextInfraCodemodBatchApply", "FlextInfraModGateSnapshot"]
