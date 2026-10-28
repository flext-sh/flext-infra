"""Generated-file plan decisions exposed through ``u.Infra``.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import difflib
from itertools import islice
from typing import TYPE_CHECKING

from flext_cli import m as cli_m, u

from flext_infra import c, m, p, r, t

if TYPE_CHECKING:
    from pathlib import Path


class FlextInfraUtilitiesCodegenFilePlan:
    """Derive generated-file effects from immutable planning data."""

    @staticmethod
    def codegen_compose_file_plans(
        plans: t.SequenceOf[m.Infra.CodegenFilePlan],
        *,
        ordered: bool = False,
    ) -> tuple[m.Infra.CodegenFilePlan, ...]:
        """Compose authenticated effects, advancing bytes only for ordered phases.

        Returns:
            One effect per destination with its original witness and dependencies.

        """
        files: dict[Path, m.Infra.CodegenFilePlan] = {}
        for file in plans:
            previous = files.get(file.path)
            if previous is None:
                files[file.path] = file
                continue
            conflicts = tuple(
                name
                for name, equal in (
                    ("project", previous.project == file.project),
                    ("path", previous.path == file.path),
                    ("before", previous.before == file.before),
                    ("owner", previous.owner == file.owner),
                    ("policy", previous.policy == file.policy),
                    ("tracking", previous.tracking == file.tracking),
                    ("index_before", previous.index_before == file.index_before),
                    (
                        "desired_content",
                        ordered or previous.desired_content == file.desired_content,
                    ),
                    (
                        "desired_mode",
                        ordered or previous.desired_mode == file.desired_mode,
                    ),
                )
                if not equal
            )
            if conflicts:
                file_plan = FlextInfraUtilitiesCodegenFilePlan
                diagnostic = file_plan.codegen_duplicate_effect_diagnostic((
                    previous,
                    file,
                ))
                message = (
                    f"candidate has competing file authority: {file.path}; "
                    f"ordered={ordered}; competing_fields={conflicts}; {diagnostic}"
                )
                failure = ValueError(message)
                raise failure
            dependencies = tuple(
                dict.fromkeys((
                    *previous.tracking_dependencies,
                    *file.tracking_dependencies,
                ))
            )
            selected = file if ordered else previous
            files[file.path] = (
                selected
                if selected.before is previous.before
                and dependencies == selected.tracking_dependencies
                else m.Infra.CodegenFilePlan(
                    project=selected.project,
                    path=selected.path,
                    before=previous.before,
                    desired_content=selected.desired_content,
                    desired_mode=selected.desired_mode,
                    owner=selected.owner,
                    policy=selected.policy,
                    tracking=selected.tracking,
                    index_before=selected.index_before,
                    tracking_dependencies=dependencies,
                )
            )
        return tuple(files.values())

    @classmethod
    def codegen_stage_file_plans(
        cls,
        index: t.MutableMappingKV[Path, m.Infra.CodegenFilePlan],
        plans: t.SequenceOf[m.Infra.CodegenFilePlan],
        *,
        ordered: bool = False,
    ) -> None:
        """Check peer declarations before advancing the caller's candidate index."""
        peers = cls.codegen_compose_file_plans(plans)
        composed = cls.codegen_compose_file_plans(
            (*index.values(), *peers), ordered=ordered
        )
        index.update((plan.path, plan) for plan in composed)

    @classmethod
    def codegen_duplicate_effect_diagnostic(
        cls,
        plans: t.SequenceOf[m.Infra.CodegenFilePlan],
    ) -> str:
        """Describe bounded duplicate declarations without exposing source bytes.

        Returns:
            Duplicate paths, ownership and exact in-memory byte digests.

        """
        grouped: dict[Path, list[m.Infra.CodegenFilePlan]] = {}
        for plan in plans:
            grouped.setdefault(plan.path, []).append(plan)
        duplicates = tuple(items for items in grouped.values() if len(items) > 1)
        details = tuple(
            f"path={plan.path} project={plan.project} owner={plan.owner!r} "
            f"before_sha256={cls._diagnostic_content_digest(plan.before.content)} "
            f"desired_sha256={cls._diagnostic_content_digest(plan.desired_content)} "
            f"before_mode={plan.before.mode} desired_mode={plan.desired_mode} "
            f"before_path={plan.before.path} "
            f"before_parent_device={plan.before.parent_device} "
            f"before_parent_inode={plan.before.parent_inode} "
            f"before_device={plan.before.device} before_inode={plan.before.inode} "
            f"before_link_count={plan.before.link_count} "
            f"before_file_attributes={plan.before.file_attributes} "
            f"before_reparse_tag={plan.before.reparse_tag} "
            f"policy={plan.policy} tracking={plan.tracking} "
            f"index_retirement={plan.index_before is not None} "
            f"tracking_dependencies={plan.tracking_dependencies[:5]}"
            for items in duplicates[:5]
            for plan in items[:5]
        )
        return f"duplicate_paths={len(duplicates)}; " + "; ".join(details)

    @staticmethod
    def _diagnostic_content_digest(content: bytes | None) -> str:
        """Keep absence distinct from an empty file in native effect diagnostics.

        Returns:
            The content digest, or the existing absence marker.

        """
        return u.Cli.sha256_bytes(content) if content is not None else "absent"

    @staticmethod
    def source_file_plan_from_edit(
        root: Path,
        edit: p.Infra.SemanticMigrationEdit,
        *,
        source_project: p.Infra.RopeProject,
        declared_files: t.MappingKV[Path, m.Infra.CodegenFilePlan],
    ) -> m.Infra.CodegenFilePlan:
        """Bind a semantic edit to its original candidate publication witness.

        Returns:
            The source plan retaining prior ownership and CAS state.

        Raises:
            ValueError: If the edit does not consume the authenticated candidate.

        """
        path = edit.file_path
        if not path.is_relative_to(root):
            message = f"semantic source edit escapes its repository: {path}"
            raise ValueError(message)
        if edit.original_source is None:
            message = f"semantic source edit has no original candidate witness: {path}"
            raise ValueError(message)
        previous = declared_files.get(path)
        original = edit.original_source.encode(c.DEFAULT_ENCODING)
        if source_project.source_text(path) != edit.original_source or (
            previous is not None and previous.desired_content != original
        ):
            message = f"semantic edit differs from its source candidate: {path}"
            raise ValueError(message)
        before = (
            previous.before
            if previous is not None
            else source_project.source_state(path)
        )
        mode = previous.desired_mode if previous is not None else before.mode
        if mode is None:
            message = f"semantic source edit has no publication mode: {path}"
            raise ValueError(message)
        if previous is None:
            return m.Infra.CodegenFilePlan(
                project=root,
                path=path,
                before=before,
                desired_content=edit.updated_source.encode(c.DEFAULT_ENCODING),
                desired_mode=mode,
            )
        return m.Infra.CodegenFilePlan(
            project=previous.project,
            path=path,
            before=before,
            desired_content=edit.updated_source.encode(c.DEFAULT_ENCODING),
            desired_mode=mode,
            owner=previous.owner,
            policy=previous.policy,
            tracking=previous.tracking,
            index_before=previous.index_before,
            tracking_dependencies=previous.tracking_dependencies,
        )

    @staticmethod
    def codegen_target_snapshot(path: Path) -> p.Result[cli_m.Cli.AtomicFileState]:
        """Observe the destination state a plan guards; absence is a state.

        Returns:
            The observed file state, or the propagated read failure.

        """
        return u.Cli.atomic_read_binary_file_state(path, required=False)

    @staticmethod
    def codegen_initializer_is_authored(content: bytes | None) -> bool:
        """Elect initializer ownership from content and declared generator markers.

        Returns:
            Whether a nonempty existing initializer belongs to its author.

        """
        return (
            content is not None
            and bool(content.strip())
            and not content.startswith(
                c.Infra.AUTOGEN_HEADER.encode(c.DEFAULT_ENCODING),
            )
        )

    @staticmethod
    def generated_source(path: Path) -> bool:
        """Prove a source file is a generator projection from its declared marker.

        A generated file opens with one of the declared generator headers; its
        content is the generator's obligation, owned by the template that
        renders it. Read failures propagate.

        Returns:
            Whether the file's first line carries a declared generator header.

        """
        with path.open(encoding=c.DEFAULT_ENCODING) as handle:
            return handle.readline().startswith(c.Infra.AUTOGEN_HEADER)

    @staticmethod
    def required_file_states(
        paths: t.IterableOf[Path],
    ) -> p.Result[tuple[cli_m.Cli.AtomicFileState, ...]]:
        """Snapshot descriptor-authenticated states for an inventoried path set.

        Every path must exist: an absent input is a planning defect, not an empty
        snapshot.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[cli_m.Cli.AtomicFileState]]``.

        """
        states: list[cli_m.Cli.AtomicFileState] = []
        for path in sorted(set(paths)):
            state = u.Cli.atomic_read_binary_file_state(path, required=True)
            if state.failure:
                return r[tuple[cli_m.Cli.AtomicFileState, ...]].from_failure(state)
            states.append(state.value)
        return r[tuple[cli_m.Cli.AtomicFileState, ...]].ok(tuple(states))

    @staticmethod
    def atomic_file_state_differs(
        before: m.Cli.AtomicFileState,
        *,
        desired_content: bytes | None,
        desired_mode: int | None,
    ) -> bool:
        """Compare the owner's exact bytes, absence marker, and permission bits.

        Both content fields are binary contracts. Decoding with replacement
        would hide distinct invalid UTF-8 bytes; treating None as empty bytes
        would erase the distinction between an absent and an empty file.

        Returns:
            The resulting ``bool``.

        """
        return before.content != desired_content or before.mode != desired_mode

    @staticmethod
    def codegen_file_requires_effect(plan: m.Infra.CodegenFilePlan) -> bool:
        """Whether publication must change a generated-file destination.

        Returns:
            Whether bytes, mode or declared tracking require publication.

        """
        if plan.index_before is not None:
            return True
        return FlextInfraUtilitiesCodegenFilePlan.atomic_file_state_differs(
            plan.before,
            desired_content=plan.desired_content,
            desired_mode=plan.desired_mode,
        )

    @staticmethod
    def codegen_fixed_point(
        plans: t.SequenceOf[m.Infra.CodegenFilePlan],
        *,
        subject: str,
    ) -> p.Result[bool]:
        """Reject a re-plan that still has to change any generated destination.

        Returns:
            Success only when no plan requires an effect; otherwise the failure
            names every residual destination with its bounded residual diff.

        """
        residual = tuple(
            plan
            for plan in plans
            if FlextInfraUtilitiesCodegenFilePlan.codegen_file_requires_effect(plan)
        )
        if residual:
            names = ", ".join(str(plan.path) for plan in residual)
            drift = FlextInfraUtilitiesCodegenFilePlan.codegen_file_drift_report(
                residual,
            )
            return r[bool].fail(
                f"{subject} did not reach a fixed point: {names}\n{drift}",
            )
        return r[bool].ok(value=True)

    @staticmethod
    def codegen_file_drift_report(
        plans: t.SequenceOf[m.Infra.CodegenFilePlan],
        *,
        limit: int = 40,
    ) -> str:
        """Report a bounded byte-exact diff, including line endings and presence.

        Escaped byte lines preserve CRLF, missing final newlines, and non-UTF-8
        content. Only equal bytes with different modes are mode-only drift.
        The observed side is the captured physical file, independent of Git state.

        Returns:
            The resulting ``str``.

        Raises:
            ValueError: If codegen drift report limit must be positive.

        """
        if limit <= 0:
            msg = "codegen drift report limit must be positive"
            raise ValueError(msg)
        parts: list[str] = []
        for plan in plans:
            raw_before = plan.before.content
            old_lines = tuple(
                repr(line) for line in (raw_before or b"").splitlines(keepends=True)
            )
            new_lines = tuple(
                repr(line)
                for line in (plan.desired_content or b"").splitlines(keepends=True)
            )
            observed_mode = (
                oct(plan.before.mode) if plan.before.mode is not None else "absent"
            )
            rendered_mode = (
                oct(plan.desired_mode) if plan.desired_mode is not None else "absent"
            )
            header = (
                f"--- {plan.path} (observed mode={observed_mode})"
                f"\n+++ {plan.path} (rendered mode={rendered_mode})"
            )
            diff = tuple(
                islice(difflib.unified_diff(old_lines, new_lines, lineterm=""), limit),
            )
            if diff:
                parts.append("\n".join((header, *diff)))
                continue
            old_bytes = (
                raw_before.encode("utf-8")
                if isinstance(raw_before, str)
                else (raw_before or b"")
            )
            new_bytes = plan.desired_content or b""
            if old_bytes == new_bytes:
                parts.append(
                    f"{header}\n(content equal: mode-only drift "
                    f"observed={observed_mode} desired={rendered_mode})",
                )
                continue
            # Lines are equal but bytes are not: name the exact tail difference
            # (line endings / trailing newline) instead of a false mode claim.
            parts.append(
                f"{header}\n(lines equal, bytes differ: observed {len(old_bytes)}B "
                f"tail={old_bytes[-24:]!r}; rendered {len(new_bytes)}B "
                f"tail={new_bytes[-24:]!r})",
            )
        return "\n----\n".join(parts)


__all__: list[str] = ["FlextInfraUtilitiesCodegenFilePlan"]
