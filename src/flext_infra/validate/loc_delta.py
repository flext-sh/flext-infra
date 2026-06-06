"""Net-LOC-delta validator (AGENTS.md §3.5).

A commit whose subject is labelled ``refactor``/``deduplicate``/``cleanup``/
``yagni``/``simplify`` MUST show ``insertions - deletions <= 0``. Non-labelled
commits (feat/fix/docs/…) are exempt — they may legitimately add lines.
"""

from __future__ import annotations

from typing import override

from flext_infra import c, p, r, s, u


class FlextInfraLocDeltaValidator(s[bool]):
    """Fail refactor/cleanup commits that grow the codebase (net positive LOC)."""

    @classmethod
    def evaluate(cls, *, subject: str, insertions: int, deletions: int) -> r[None]:
        """Pure rule: net positive delta on a labelled commit is a violation."""
        lowered = subject.lower()
        if not any(label in lowered for label in c.Infra.REFACTOR_COMMIT_LABELS):
            return r[None].ok(None)
        delta = insertions - deletions
        if delta > 0:
            return r[None].fail(
                f"net-LOC-delta violation (§3.5): '{subject}' adds +{delta} "
                f"(insertions={insertions}, deletions={deletions}); refactor/cleanup "
                "commits must be net non-positive",
            )
        return r[None].ok(None)

    @staticmethod
    def _sum_numstat(numstat: str) -> tuple[int, int]:
        """Sum insertions/deletions from `git diff --numstat` output (skip binary)."""
        insertions = 0
        deletions = 0
        for line in numstat.splitlines():
            match line.split("\t"):
                case [added, removed, *_] if added.isdigit() and removed.isdigit():
                    insertions += int(added)
                    deletions += int(removed)
                case _:
                    continue
        return insertions, deletions

    @override
    def execute(self) -> p.Result[bool]:
        """Evaluate the workspace HEAD commit's labelled net-LOC delta."""
        subject_result = u.Cli.run_raw(
            ["git", "log", "-1", "--format=%s"],
            cwd=self.workspace_root,
            timeout=30,
        )
        if subject_result.failure:
            return r[bool].fail(subject_result.error or "git subject read failed")
        numstat_result = u.Cli.run_raw(
            ["git", "diff", "--numstat", "HEAD~1", "HEAD"],
            cwd=self.workspace_root,
            timeout=30,
        )
        if numstat_result.failure:
            return r[bool].fail(numstat_result.error or "git numstat read failed")
        insertions, deletions = self._sum_numstat(numstat_result.value.stdout)
        verdict = self.evaluate(
            subject=subject_result.value.stdout.strip(),
            insertions=insertions,
            deletions=deletions,
        )
        if verdict.failure:
            return r[bool].fail(verdict.error or "net-LOC-delta violation")
        return r[bool].ok(True)


__all__: list[str] = ["FlextInfraLocDeltaValidator"]
