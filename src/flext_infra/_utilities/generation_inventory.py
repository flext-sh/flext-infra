"""Authenticated, stdlib-AST source inventory for declaration projection.

This owner intentionally has no Rope dependency.  Generation reads each elected
source once, parses those captured bytes once, and carries the corresponding
atomic witness to the shared publisher.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import hashlib
from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from pathlib import Path

from flext_cli import u

from flext_infra import c, m, p, r
from flext_infra._utilities import FlextInfraUtilitiesIterationDirectory


@dataclass(frozen=True)
class FlextInfraGenerationSource:
    """One authenticated Python source and its invocation-local AST."""

    path: Path
    member: Path
    state: m.Cli.AtomicFileState
    digest: str
    text: str
    tree: ast.Module


@dataclass(frozen=True)
class FlextInfraGenerationInventory:
    """The complete source inventory for one generation repository scope."""

    root: Path
    members: tuple[Path, ...]
    sources: Mapping[Path, FlextInfraGenerationSource]


class FlextInfraUtilitiesGenerationInventory:
    """Build the generation-only source inventory from atomic observations."""

    @classmethod
    def generation_inventory(
        cls, root: Path, members: Iterable[Path] = ()
    ) -> p.Result[FlextInfraGenerationInventory]:
        """Capture and parse every elected source without opening a Rope project.

        Returns:
            The immutable inventory, or the first source/parse failure.

        """
        result_type = r[FlextInfraGenerationInventory]
        root = root.resolve()
        elected = tuple(dict.fromkeys(item.resolve() for item in (root, *members)))
        if any(not member.is_relative_to(root) for member in elected):
            return result_type.fail("generation inventory member escapes root")
        sources: dict[Path, FlextInfraGenerationSource] = {}
        for member in elected:
            if not member.is_dir():
                return result_type.fail(
                    f"generation inventory member is absent: {member}"
                )
            nested = tuple(
                other
                for other in elected
                if other != member and other.is_relative_to(member)
            )
            for candidate in sorted(member.rglob(c.Infra.EXT_PYTHON_GLOB)):
                path = candidate.resolve()
                if any(path.is_relative_to(other) for other in nested) or (
                    FlextInfraUtilitiesIterationDirectory.source_scan_ignored_path(
                        member, path
                    )
                ):
                    continue
                observed = u.Cli.atomic_read_binary_file_state(path, required=True)
                if observed.failure:
                    return result_type.from_failure(observed)
                state = observed.value
                if state.content is None:
                    return result_type.fail(f"generation source is absent: {path}")
                try:
                    text = state.content.decode(c.DEFAULT_ENCODING)
                    tree = ast.parse(text, filename=str(path))
                except (UnicodeDecodeError, SyntaxError) as exception:
                    return result_type.fail(
                        f"generation source cannot be parsed: {path}: {exception}"
                    )
                sources[path] = FlextInfraGenerationSource(
                    path=path,
                    member=member,
                    state=state,
                    digest=hashlib.sha256(state.content).hexdigest(),
                    text=text,
                    tree=tree,
                )
        return result_type.ok(
            FlextInfraGenerationInventory(root=root, members=elected, sources=sources)
        )


__all__: list[str] = [
    "FlextInfraGenerationInventory",
    "FlextInfraGenerationSource",
    "FlextInfraUtilitiesGenerationInventory",
]
