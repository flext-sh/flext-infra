"""Pure physical-state comparison primitives for Mise artifact verification.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import m, r, t, u
from flext_infra.codegen._mise_artifacts_files import FlextInfraMiseArtifactsFiles

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraMiseArtifactsComparison:
    """Prove live filesystem state against authenticated snapshots.

    Pure comparison leaf shared by verification, transaction state, and
    generation preconditions; it imports only facade letters and the exact
    filesystem-state primitives, never a sibling verification module.
    """

    @classmethod
    def states_current(
        cls,
        states: t.VariadicTuple[m.Cli.AtomicFileState],
        *,
        journal: m.Infra.CodegenTransactionJournal | None = None,
    ) -> p.Result[bool]:
        """Prove every full file state still equals its authenticated snapshot.

        Compare content, mode, and physical identity within the caller's scope.
        Parent identities may change only through the supplied native journal's
        exact directory-creation receipts. Each destination still has its own
        guarded write; this check does not claim multi-file OS atomicity.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        for expected in states:
            if expected.parent_device is None and journal is not None:
                rebound = cls.bind_source_parent(expected, journal)
                if rebound.failure:
                    return r[bool].from_failure(rebound)
                rebound_expected = rebound.value
            else:
                rebound_expected = expected
            observed = FlextInfraMiseArtifactsFiles.read_state(
                rebound_expected.path,
                required=rebound_expected.content is not None,
            )
            if observed.failure:
                return r[bool].from_failure(observed)
            if observed.value != rebound_expected:
                content_changed = observed.value.content != rebound_expected.content
                expected_digest = (
                    FlextInfraMiseArtifactsFiles.digest(rebound_expected.content)
                    if rebound_expected.content is not None
                    else None
                )
                observed_digest = (
                    FlextInfraMiseArtifactsFiles.digest(observed.value.content)
                    if observed.value.content is not None
                    else None
                )
                message = (
                    f"generation authenticated state changed: {rebound_expected.path}; "
                    f"content_changed={content_changed}; "
                    f"expected_sha256={expected_digest}; "
                    f"observed_sha256={observed_digest}; "
                    "expected="
                    f"{rebound_expected.model_dump_json(exclude={'content'})}; "
                    f"observed={observed.value.model_dump_json(exclude={'content'})}"
                )
                return r[bool].fail(message, exception=ValueError(message))
        return r[bool].ok(value=True)

    @classmethod
    def bind_source_parent(
        cls,
        expected: m.Cli.AtomicFileState,
        journal: m.Infra.CodegenTransactionJournal,
    ) -> p.Result[m.Cli.AtomicFileState]:
        """Recognize only parent identities created under the durable absence witness.

        Returns:
            The resulting ``p.Result[m.Cli.AtomicFileState]``.

        """
        result = r[m.Cli.AtomicFileState]
        source = next(
            (
                item
                for item in (*journal.sources, *journal.outputs)
                if item.path == expected.path and item.absent_parent is not None
            ),
            None,
        )
        if (
            source is None
            or source.absent_parent is None
            or expected.content is not None
        ):
            return result.fail(
                f"generation source has no absence witness: {expected.path}",
            )
        witness = source.absent_parent
        current = u.Cli.atomic_plan_directory_chain(witness.target)
        if current.failure:
            return result.from_failure(current)
        if current.value == witness:
            return result.ok(expected)
        ancestry = cls._verified_parent_ancestry(journal, witness)
        if ancestry.failure:
            return result.from_failure(ancestry)
        observed = current.value
        if observed.directories or observed.anchor_ancestry != ancestry.value:
            return result.fail(
                f"generation source parent identity changed: {expected.path}",
            )
        return result.ok(
            expected.model_copy(
                update={
                    "parent_device": ancestry.value[-1][0],
                    "parent_inode": ancestry.value[-1][1],
                },
            ),
        )

    @classmethod
    def _verified_parent_ancestry(
        cls,
        journal: m.Infra.CodegenTransactionJournal,
        witness: m.Cli.AtomicDirectoryChainPlan,
    ) -> p.Result[t.VariadicTuple[t.Pair[int, int]]]:
        """Rebuild the parent ancestry chain from journal-created directories.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[t.Pair[int, int]]]``.

        """
        result_type = r[t.VariadicTuple[t.Pair[int, int]]]
        created = {
            item.created.path: item.created
            for item in journal.directories
            if item.created is not None and item.disposition == "generated"
        }
        ancestry = list(witness.anchor_ancestry)
        for path in witness.directories:
            identity = created.get(path)
            if identity is None or identity.device is None or identity.inode is None:
                return result_type.fail(
                    f"generation source parent was not created by this journal: {path}",
                )
            if (identity.parent_device, identity.parent_inode) != ancestry[-1]:
                return result_type.fail(
                    (
                        f"generation source parent ancestry "
                        f"differs from its journal: {path}"
                    ),
                )
            ancestry.append((identity.device, identity.inode))
        return result_type.ok(tuple(ancestry))

    @classmethod
    def sources(
        cls,
        plan: m.Infra.MiseToolchainWorkspacePlan,
        published: t.VariadicTuple[m.Infra.CodegenStagedFile] = (),
    ) -> p.Result[bool]:
        """Prove every Mise config source equals its expected full snapshot.

        Before publication the expectation is the plan-time snapshot. After
        it, every config source this transaction published itself replaces or
        joins that snapshot with its staged identity (``publications_live``
        already proved that identity live); any other change is foreign.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        for project in plan.projects:
            current = u.Infra.snapshot_config_sources(project.layout.root)
            if current.failure:
                return r[bool].from_failure(current)
            if current.value != cls._expected_sources(project, published):
                return r[bool].fail(f"Mise sources changed: {project.layout.selector}")
        return r[bool].ok(value=True)

    @staticmethod
    def _expected_sources(
        project: m.Infra.MiseToolchainProjectState,
        published: t.VariadicTuple[m.Infra.CodegenStagedFile],
    ) -> t.VariadicTuple[m.Cli.AtomicFileState]:
        """Return the plan-time sources with this transaction's own config writes.

        Returns:
            The expected sources, ordered by path like the snapshot.

        """
        own = {
            item.before.path: item
            for item in published
            if u.Infra.direct_config_source(project.layout.root, item.before.path)
        }
        kept = (item for item in project.config.sources if item.path not in own)
        landed = (
            item.replacement.model_copy(
                update={
                    "path": item.before.path,
                    "parent_device": item.before.parent_device,
                    "parent_inode": item.before.parent_inode,
                },
            )
            for item in own.values()
            if item.replacement is not None
        )
        return tuple(sorted((*kept, *landed), key=lambda item: item.path))

    @classmethod
    def same_directory_identity(
        cls,
        expected: m.Cli.AtomicPhysicalTreeEntry,
        observed: m.Cli.AtomicPhysicalTreeEntry,
    ) -> bool:
        return (
            expected.path,
            expected.kind,
            expected.parent_device,
            expected.parent_inode,
            expected.parent_mount_id,
            expected.mode,
            expected.device,
            expected.inode,
            expected.mount_id,
            expected.uid,
            expected.gid,
            expected.file_attributes,
            expected.reparse_tag,
        ) == (
            observed.path,
            observed.kind,
            observed.parent_device,
            observed.parent_inode,
            observed.parent_mount_id,
            observed.mode,
            observed.device,
            observed.inode,
            observed.mount_id,
            observed.uid,
            observed.gid,
            observed.file_attributes,
            observed.reparse_tag,
        )


__all__: list[str] = ["FlextInfraMiseArtifactsComparison"]
