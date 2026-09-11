"""Generated-file plan decisions exposed through ``u.Infra``."""

from __future__ import annotations

import difflib
from collections.abc import Generator
from contextlib import contextmanager
from itertools import islice
from typing import TYPE_CHECKING, Literal

from filelock import FileLock
from flext_cli import m as cli_m, u

from flext_core import r
from flext_infra import m, p, t

if TYPE_CHECKING:
    from pathlib import Path


class FlextInfraUtilitiesCodegenFilePlan:
    """Derive generated-file effects from immutable planning data."""

    @staticmethod
    @contextmanager
    def codegen_transaction_lease(journal_path: Path) -> Generator[None]:
        """Hold native ownership without unlinking the journal's lock identity."""
        lock_path = journal_path.with_name(f"{journal_path.name}.lock")
        with FileLock(
            lock_path,
            timeout=0,
            blocking=False,
            mode=0o600,
            fallback_to_soft=False,
            preserve_lock_file=True,
            close_error_policy="raise",
        ):
            yield

    @staticmethod
    def planned_file(
        project: Path,
        target: Path,
        *,
        required: bool,
        desired_content: bytes | None,
        desired_mode: int | None,
        source_states: t.SequenceOf[cli_m.Cli.AtomicFileState] = (),
        owner: str = "",
        policy: Literal["full", "merge", "create-only", "delegated", "manual"]
        | None = None,
    ) -> p.Result[m.Infra.CodegenFilePlan]:
        """Capture one destination's before state and bind it to its desired state.

        ``required`` says whether the destination must already exist: a removal
        plan reads an existing file, a publication plan tolerates its absence.
        """
        before = u.Cli.atomic_read_binary_file_state(target, required=required)
        if before.failure:
            return r[m.Infra.CodegenFilePlan].from_failure(before)
        return r[m.Infra.CodegenFilePlan].ok(
            m.Infra.CodegenFilePlan(
                project=project,
                path=target,
                before=before.value,
                desired_content=desired_content,
                desired_mode=desired_mode,
                source_states=tuple(source_states),
                owner=owner,
                policy=policy,
            )
        )

    @staticmethod
    def required_file_states(
        paths: t.IterableOf[Path],
    ) -> p.Result[t.VariadicTuple[cli_m.Cli.AtomicFileState]]:
        """Snapshot descriptor-authenticated states for an inventoried path set.

        Every path must exist: an absent input is a planning defect, not an empty
        snapshot.
        """
        states: list[cli_m.Cli.AtomicFileState] = []
        for path in sorted(set(paths)):
            state = u.Cli.atomic_read_binary_file_state(path, required=True)
            if state.failure:
                return r[tuple[cli_m.Cli.AtomicFileState, ...]].from_failure(state)
            states.append(state.value)
        return r[tuple[cli_m.Cli.AtomicFileState, ...]].ok(tuple(states))

    @staticmethod
    def codegen_file_before_state(
        plan: m.Infra.CodegenFilePlan,
    ) -> p.Result[cli_m.Cli.AtomicFileState]:
        """Return a publishable state only after its parent physically exists."""
        if isinstance(plan.before, cli_m.Cli.AtomicDirectoryChainPlan):
            return r[cli_m.Cli.AtomicFileState].fail(
                f"codegen destination parent is absent: {plan.path.parent}"
            )
        return r[cli_m.Cli.AtomicFileState].ok(plan.before)

    @staticmethod
    def atomic_file_state_differs(
        before: cli_m.Cli.AtomicFileState,
        *,
        desired_content: bytes | None,
        desired_mode: int | None,
    ) -> bool:
        """Whether desired content or mode differs from an observed leaf state."""
        return before.content != desired_content or before.mode != desired_mode

    @staticmethod
    def codegen_file_requires_effect(plan: m.Infra.CodegenFilePlan) -> bool:
        """Whether publication must change a generated-file destination."""
        if isinstance(plan.before, cli_m.Cli.AtomicDirectoryChainPlan):
            return plan.desired_content is not None
        return FlextInfraUtilitiesCodegenFilePlan.atomic_file_state_differs(
            plan.before,
            desired_content=plan.desired_content,
            desired_mode=plan.desired_mode,
        )

    @staticmethod
    def codegen_file_drift_report(
        plans: t.SequenceOf[m.Infra.CodegenFilePlan], *, limit: int = 40
    ) -> str:
        """Bounded unified diff per drifted plan, for fail-loud drift diagnosis.

        The committed (before) side is compared against the rendered
        (desired) side so a red gate names the exact delta instead of a bare
        path list; mode-only drift is stated explicitly.
        """
        parts: list[str] = []
        for plan in plans:
            if isinstance(plan.before, cli_m.Cli.AtomicDirectoryChainPlan):
                parts.append(f"{plan.path}: absent parent chain gains content")
                continue
            raw_before = plan.before.content
            old_text = (
                raw_before
                if isinstance(raw_before, str)
                else (raw_before or b"").decode("utf-8", errors="replace")
            )
            new_text = (plan.desired_content or b"").decode("utf-8", errors="replace")
            header = (
                f"--- {plan.path}"
                f" (committed mode={oct(plan.before.mode) if plan.before.mode is not None else 'none'})"
                f"\n+++ {plan.path} (rendered mode={oct(plan.desired_mode or 0)})"
            )
            diff = tuple(
                islice(
                    difflib.unified_diff(
                        old_text.splitlines(), new_text.splitlines(), lineterm=""
                    ),
                    limit,
                )
            )
            parts.append(
                "\n".join((header, *diff))
                if diff
                else (
                    f"{header}\n(content equal: mode-only drift "
                    f"observed={oct(plan.before.mode) if plan.before.mode is not None else 'none'} "
                    f"desired={oct(plan.desired_mode) if plan.desired_mode is not None else 'none'})"
                )
            )
        return "\n----\n".join(parts)


__all__: list[str] = ["FlextInfraUtilitiesCodegenFilePlan"]
