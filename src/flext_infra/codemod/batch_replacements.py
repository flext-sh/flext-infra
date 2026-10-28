"""Transport ast-grep JSON replacements to the existing guarded publisher.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import sys
from collections.abc import Mapping, MutableMapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, r, t, u
from flext_infra.transformers import FlextInfraTransformersSemanticPublication

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraModReplacements:
    """Preserve exact engine rewrites without granting it filesystem effects."""

    @staticmethod
    def generator_owned(
        entries: Sequence[m.Infra.ModOccurrence],
    ) -> t.StrTuple:
        """Name the findings whose file the canonical generator owns.

        One entry per file and rule; the per-finding detail stays in the mod
        findings report.

        Returns:
            Sorted ``generator:<file>:<rule>`` identities.

        """
        return tuple(
            sorted({
                f"generator:{item.file}:{item.rule_id}"
                for item in entries
                if item.source_owner == "generator"
            }),
        )

    @classmethod
    def require_authored(
        cls,
        entries: Sequence[m.Infra.ModOccurrence],
    ) -> p.Result[bool]:
        """Refuse to write generated files: their findings are generator repairs.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        generated = cls.generator_owned(entries)
        if generated:
            return r[bool].fail(
                "generated findings require canonical generator repair: "
                + ", ".join(generated),
            )
        return r[bool].ok(value=True)

    @classmethod
    def publish[FindingT: m.Infra.ModOccurrence](
        cls,
        root: Path,
        report: m.Infra.ModOccurrenceReport[FindingT],
        *,
        exact_replacements: bool = False,
    ) -> p.Result[bool]:
        """Validate byte coordinates and publish complete file plans.

        Args:
            root: Repository root the finding paths are relative to.
            report: The scanned findings whose actionable fixes publish.
            exact_replacements: Publish exact byte-span replacements instead
                of recomposed CST output.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        allowed = cls.require_authored(
            tuple(finding for finding in report.entries if finding.actionable),
        )
        if allowed.failure:
            return allowed
        grouped: MutableMapping[Path, list[m.Infra.ModOccurrence]] = {}
        for finding in report.entries:
            if finding.actionable:
                grouped.setdefault(root / finding.file, []).append(finding)
        plans: list[m.Infra.SemanticFilePlan] = []
        for path, findings in sorted(grouped.items()):
            plan = cls._path_plan(
                root,
                path,
                findings,
                exact_replacements=exact_replacements,
            )
            if plan.failure:
                if plan.error_code == c.Infra.MOD_SCAN_SOURCE_DRIFT_ERROR_CODE:
                    sys.stderr.write(f"mod: publish deferred drifted source: {path}\n")
                    sys.stderr.flush()
                    continue
                return r[bool].from_failure(plan)
            plans.append(plan.value)
        published = (
            FlextInfraTransformersSemanticPublication.publish_semantic_file_plans(
                plans, repository_root=root
            )
        )
        if published.failure:
            return r[bool].from_failure(published)
        return r[bool].ok(value=True)

    @classmethod
    def _path_plan(
        cls,
        root: Path,
        path: Path,
        findings: Sequence[m.Infra.ModOccurrence],
        *,
        exact_replacements: bool = False,
        compose_only: bool = False,
    ) -> p.Result[m.Infra.SemanticFilePlan]:
        """Validate one path's actionable findings into one publication plan.

        Returns:
            The resulting ``p.Result[m.Infra.SemanticFilePlan]``.

        """
        before = findings[0].source_state
        if before is None or before.content is None:
            return r[m.Infra.SemanticFilePlan].fail(
                f"actionable finding lacks authenticated state: {path}",
            )
        replacements: list[tuple[int, int, bytes]] = []
        observed = (
            before
            if compose_only
            else u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()
        )
        for finding in findings:
            if (
                finding.source_state != before
                or finding.replacement is None
                or observed != before
            ):
                return r[m.Infra.SemanticFilePlan].fail(
                    f"inconsistent actionable finding source: {path}",
                    error_code=c.Infra.MOD_SCAN_SOURCE_DRIFT_ERROR_CODE,
                )
            coordinates = cls._finding_replacement(
                before.content,
                finding,
                finding.replacement,
                path,
            )
            if coordinates.failure:
                return r[m.Infra.SemanticFilePlan].from_failure(coordinates)
            replacements.append(coordinates.value)
        updated = cls._apply_replacements(before.content, replacements, path)
        if updated.failure:
            return r[m.Infra.SemanticFilePlan].from_failure(updated)
        candidate = (
            r[bytes].ok(updated.value)
            if compose_only
            else cls._normalized_candidate(
                root,
                path,
                before.content,
                updated.value,
                exact_replacements=exact_replacements,
            )
        )

        def semantic_plan(content: bytes) -> m.Infra.SemanticFilePlan:
            return m.Infra.SemanticFilePlan(
                project=u.Infra.project_root(path) or root,
                path=path,
                before=before,
                desired_content=content,
                desired_mode=before.mode,
                changes=tuple(finding.rule_id for finding in findings),
            )

        return candidate.map(semantic_plan)

    @classmethod
    def compose[FindingT: m.Infra.ModOccurrence](
        cls, root: Path, report: m.Infra.ModOccurrenceReport[FindingT]
    ) -> p.Result[tuple[m.Infra.SemanticFilePlan, ...]]:
        """Compose authenticated candidate bytes without admission or live effects.

        Returns:
            Exact syntax plans; final normalization and gates belong to convergence.

        """
        grouped: MutableMapping[Path, list[m.Infra.ModOccurrence]] = {}
        for finding in report.entries:
            if finding.actionable and finding.source_owner != "generator":
                grouped.setdefault(root / finding.file, []).append(finding)
        plans: list[m.Infra.SemanticFilePlan] = []
        for path, findings in sorted(grouped.items()):
            planned = cls._path_plan(root, path, findings, compose_only=True)
            if planned.failure:
                return r[tuple[m.Infra.SemanticFilePlan, ...]].from_failure(planned)
            plans.append(planned.value)
        return r[tuple[m.Infra.SemanticFilePlan, ...]].ok(tuple(plans))

    @classmethod
    def admit(
        cls, root: Path, plans: Sequence[m.Infra.SemanticFilePlan]
    ) -> p.Result[tuple[m.Infra.SemanticFilePlan, ...]]:
        """Normalize and judge only complete syntax candidates against originals.

        Returns:
            Accepted plans or the first native admission failure.

        """
        accepted: list[m.Infra.SemanticFilePlan] = []
        for plan in plans:
            if plan.before.content is None or plan.desired_content is None:
                return r[tuple[m.Infra.SemanticFilePlan, ...]].fail(
                    f"syntax candidate lacks authenticated bytes: {plan.path}"
                )
            normalized = cls._normalized_candidate(
                root, plan.path, plan.before.content, plan.desired_content
            )
            if normalized.failure:
                return r[tuple[m.Infra.SemanticFilePlan, ...]].from_failure(normalized)
            accepted.append(
                plan.model_copy(update={"desired_content": normalized.value})
            )
        return r[tuple[m.Infra.SemanticFilePlan, ...]].ok(tuple(accepted))

    @staticmethod
    def _finding_replacement(
        content: bytes,
        finding: m.Infra.ModOccurrence,
        replacement: str,
        path: Path,
    ) -> p.Result[tuple[int, int, bytes]]:
        """Validate one finding's byte coordinates against the authenticated bytes.

        Returns:
            The resulting ``(start, end, replacement)`` replacement triple.

        """
        offsets = finding.replacement_offsets
        raw_match = finding.range.get("byteOffset")
        if offsets is None or not isinstance(raw_match, Mapping):
            return r[tuple[int, int, bytes]].fail(
                f"ast-grep finding lacks byte coordinates: {path}:{finding.rule_id}",
            )
        matched = m.Infra.ModReplacementOffsets.model_validate(raw_match)
        if not (0 <= offsets.start <= offsets.end <= len(content)) or not (
            0 <= matched.start <= matched.end <= len(content)
        ):
            return r[tuple[int, int, bytes]].fail(
                f"ast-grep byte coordinates escape source: {path}",
            )
        if content[matched.start : matched.end] != finding.text.encode(
            c.DEFAULT_ENCODING,
        ):
            return r[tuple[int, int, bytes]].fail(
                f"ast-grep match differs from authenticated source: {path}",
            )
        return r[tuple[int, int, bytes]].ok((
            offsets.start,
            offsets.end,
            replacement.encode(c.DEFAULT_ENCODING),
        ))

    @staticmethod
    def _apply_replacements(
        content: bytes,
        replacements: Sequence[tuple[int, int, bytes]],
        path: Path,
    ) -> p.Result[bytes]:
        """Apply one path's replacements back-to-front, rejecting overlaps.

        Returns:
            The resulting updated content.

        """
        updated = content
        boundary = len(updated)
        for start, end, replacement in sorted(replacements, reverse=True):
            if end > boundary:
                return r[bytes].fail(f"ast-grep replacements overlap: {path}")
            updated = updated[:start] + replacement + updated[end:]
            boundary = start
        return r[bytes].ok(updated)

    @classmethod
    def _normalized_candidate(
        cls,
        root: Path,
        path: Path,
        before: bytes,
        candidate: bytes,
        *,
        exact_replacements: bool = False,
    ) -> p.Result[bytes]:
        """Judge final normalized bytes before the atomic publisher has effects.

        Returns:
            Accepted bytes, or the first normalization or Ruff delta failure.

        """
        baseline = u.Infra.lint_snapshot(
            path,
            root,
            gates=(c.Infra.LINT,),
            source=before.decode(c.DEFAULT_ENCODING),
        )
        if exact_replacements:
            final: p.Result[str] = r[str].ok(candidate.decode(c.DEFAULT_ENCODING))
            ast.parse(final.value, filename=str(path))
        else:
            normalized = u.Infra.normalize_source(
                root,
                path,
                candidate.decode(c.DEFAULT_ENCODING),
                before_source=before.decode(c.DEFAULT_ENCODING),
            )
            if normalized.failure:
                return r[bytes].from_failure(normalized)
            stripped = u.Infra.strip_type_checking_scaffold(normalized.value)
            final = (
                normalized
                if stripped == normalized.value
                else u.Infra.normalize_source(
                    root,
                    path,
                    stripped,
                    before_source=before.decode(c.DEFAULT_ENCODING),
                )
            )
        if final.failure:
            return r[bytes].from_failure(final)
        introduced = u.Infra.lint_new_errors(
            baseline,
            u.Infra.lint_snapshot(
                path, root, gates=(c.Infra.LINT,), source=final.value
            ),
        )
        if introduced:
            return r[bytes].fail(
                f"mod introduced Ruff findings in {path}: "
                + "\n".join(line for lines in introduced.values() for line in lines),
            )
        return r[bytes].ok(final.value.encode(c.DEFAULT_ENCODING))


__all__: list[str] = ["FlextInfraModReplacements"]
