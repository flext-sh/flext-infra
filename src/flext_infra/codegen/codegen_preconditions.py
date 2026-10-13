"""Immutable source and journal preconditions for generation transactions.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import json
import tomllib
from collections.abc import MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, r, u
from flext_infra.codegen import (
    FlextInfraMiseArtifactsState,
    FlextInfraMiseArtifactsVerification,
)

if TYPE_CHECKING:
    from flext_infra import p, t

_ENGINE_DISTRIBUTION = "flext-infra"


class FlextInfraCodegenPreconditions:
    """Validate source consistency and receipt ownership before publishing."""

    @staticmethod
    def rendering_engine(repository_root: Path) -> p.Result[bool]:
        """Prove the executing engine is the flext-infra the target's lock pins.

        A standalone consumer resolves flext-infra from its ``uv.lock``; an
        engine foreign to that pin renders with templates the target never
        declared — the split brain that forced hand repairs on generated
        files. The fleet's own checkout and any editable binding render from
        their own tree and are exempt; a target without a lock is the same
        case (nothing declares an engine to agree with).

        Returns:
            The resulting ``p.Result[bool]``.

        """
        result_type = r[bool]
        lock_path = repository_root / c.Infra.UV_LOCK_FILENAME
        if not lock_path.is_file():
            return result_type.ok(True)
        matches = u.installed_distributions(name=_ENGINE_DISTRIBUTION)
        if len(matches) != 1:
            return result_type.fail(
                f"rendering engine distribution count mismatch: "
                f"distribution={_ENGINE_DISTRIBUTION} expected=1 "
                f"actual={len(matches)}",
            )
        distribution = matches[0]
        direct_url = distribution.read_text(c.Infra.DISTRIBUTION_DIRECT_URL_FILE)
        provenance = json.loads(direct_url) if direct_url else {}
        if provenance.get("dir_info", {}).get("editable"):
            return result_type.ok(True)
        lock = tomllib.loads(lock_path.read_text(encoding=c.DEFAULT_ENCODING))
        pinned = next(
            (
                package
                for package in lock.get("package", ())
                if package.get("name") == _ENGINE_DISTRIBUTION
            ),
            None,
        )
        if pinned is None:
            return result_type.ok(True)
        source = pinned.get("source", {})
        if source.get("editable") is not None:
            return result_type.ok(True)
        locked_commit = (source.get("git") or "").rsplit("#", 1)[-1] or None
        running_commit = provenance.get("vcs_info", {}).get("commit_id")
        if locked_commit is not None and running_commit is not None:
            if running_commit == locked_commit:
                return result_type.ok(True)
            return result_type.fail(
                f"rendering engine {_ENGINE_DISTRIBUTION}@{running_commit} "
                f"is not the locked pin {_ENGINE_DISTRIBUTION}@{locked_commit}: "
                "the environment is stale — cure: uv sync (stale environment) "
                "or make upg (stale pin); never a hand-edited generated file",
            )
        locked_version = pinned.get("version")
        if locked_version is not None and distribution.version != locked_version:
            return result_type.fail(
                f"rendering engine {_ENGINE_DISTRIBUTION}@{distribution.version} "
                f"is not the locked pin {_ENGINE_DISTRIBUTION}@{locked_version}: "
                "the environment is stale — cure: uv sync (stale environment) "
                "or make upg (stale pin); never a hand-edited generated file",
            )
        return result_type.ok(True)

    @staticmethod
    def phase_sources(
        phase: str,
        plans: t.VariadicTuple[m.Infra.CodegenFilePlan],
    ) -> p.Result[t.VariadicTuple[t.Pair[str, m.Cli.AtomicFileState]]]:
        """Reject conflicting observations and tag each source with its phase.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[t.Pair[str,
                m.Cli.AtomicFileState]]]``.

        """
        return FlextInfraCodegenPreconditions.unique_states(
            tuple(source for plan in plans for source in plan.source_states)
        ).map(lambda sources: tuple((phase, source) for source in sources))

    @staticmethod
    def unique_states(
        states: t.VariadicTuple[m.Cli.AtomicFileState],
    ) -> p.Result[t.VariadicTuple[m.Cli.AtomicFileState]]:
        """Preserve the first identity per path and refuse conflicting snapshots.

        Returns:
            The authenticated ordered union or its first identity conflict.

        """
        result_type = r[tuple[m.Cli.AtomicFileState, ...]]
        by_path: MutableMapping[Path, m.Cli.AtomicFileState] = {}
        for file_state in states:
            if by_path.setdefault(file_state.path, file_state) != file_state:
                return result_type.fail(
                    f"planner observed two states for {file_state.path}"
                )
        return result_type.ok(tuple(by_path.values()))

    @staticmethod
    def prepublication_barriers(
        plan: m.Infra.MiseToolchainWorkspacePlan,
        sources: t.VariadicTuple[m.Cli.AtomicFileState],
        destinations: t.VariadicTuple[m.Cli.AtomicFileState],
    ) -> p.Result[bool]:
        """Require unchanged source and destination identities before writing.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        source_barrier = FlextInfraCodegenPreconditions.unique_states(sources).flat_map(
            FlextInfraMiseArtifactsVerification.states_current
        )
        if source_barrier.failure:
            return source_barrier
        destination_barrier = FlextInfraMiseArtifactsVerification.states_current(
            destinations,
        )
        if destination_barrier.failure:
            return destination_barrier
        return FlextInfraMiseArtifactsVerification.sources(plan)

    @staticmethod
    def unchanged_journal(
        session: m.Infra.CodegenTransactionSession,
        changed_error: str,
    ) -> p.Result[m.Infra.CodegenTransactionSession]:
        """Require the complete journal receipt; a lease cannot authorize replacement.

        Returns:
            The resulting ``p.Result[m.Infra.CodegenTransactionSession]``.

        """
        result_type = r[m.Infra.CodegenTransactionSession]
        observed = FlextInfraMiseArtifactsState.journal_state(session.plan.layout)
        observed_snapshot = (
            None
            if observed.failure
            else FlextInfraMiseArtifactsState.journal_snapshot(observed.value)
        )
        expected = session.journal_state
        if observed.failure or observed_snapshot != expected:
            return result_type.fail(
                observed.error or changed_error,
                error_data={
                    "cleanup_error": "journal authority mismatch vs session receipt",
                },
            )
        return result_type.ok(session)


__all__: list[str] = ["FlextInfraCodegenPreconditions"]
