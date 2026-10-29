"""Workspace snapshot models: the one Rope model of a run plus its memos.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import Annotated

from flext_cli import m

from flext_infra import p, t
from flext_infra._models import FlextInfraModelsRefactorGrep
from flext_infra._models._codegen import FlextInfraModelsCodegenLazyInit


class FlextInfraModelsWorkspaceSnapshot:
    """Declarations of the one per-run snapshot of a uv workspace."""

    class WorkspaceSnapshotSource(m.ContractModel):
        """One workspace file read exactly once through the authenticated owner."""

        path: Annotated[Path, m.Field(description="Resolved file path")]
        state: Annotated[
            m.Cli.AtomicFileState,
            m.Field(description="Authenticated state the run reads and publishes"),
        ]
        digest: Annotated[
            t.NonEmptyStr,
            m.Field(description="SHA-256 of the exact file bytes"),
        ]
        module: Annotated[
            str,
            m.Field(description="Dotted module name; empty outside a package"),
        ]
        member: Annotated[Path, m.Field(description="Resolved owning member root")]
        # The family contract strips whitespace; every syntax tree and line
        # position derives from these exact bytes, so they must survive as read.
        text: Annotated[
            str,
            t.StringConstraints(strip_whitespace=False),
            m.Field(description="Exact decoded file text"),
        ]

    class WorkspaceBootstrapDependencies(m.ContractModel):
        """Bootstrap closure bound to native modules and their resolver roots."""

        namespace: Annotated[str, m.Field(description="Publishing namespace")]
        modules: Annotated[
            t.Port[tuple[t.Infra.RopeNativeParsedModule, ...]],
            m.Field(exclude=True, description="Native modules of the source epoch"),
        ]
        source_folders: Annotated[
            tuple[str, ...], m.Field(description="Native source folder election")
        ]
        python_path_folders: Annotated[
            tuple[str, ...], m.Field(description="Native Python path election")
        ]
        source_digests: Annotated[
            tuple[str, ...], m.Field(description="Digests of the elected source bytes")
        ]
        dependencies: Annotated[
            frozenset[str], m.Field(description="Runtime bootstrap dependencies")
        ]

    class WorkspaceSnapshot(m.ContractModel):
        """The one Rope model of a workspace run and the facts derived from it.

        The Rope project is the in-memory model: it lists, reads, parses and
        caches every module lazily and invalidates through its observers. The
        remaining maps start empty and are filled only through their
        ``u.Infra`` owners, once per key, for facts Rope does not model. Each
        read source keeps the authenticated state it was read from, so a file
        that changes during the run fails its verification and its publication
        guard instead of being read stale.
        """

        workspace_root: Annotated[
            Path, m.Field(description="Resolved root of the workspace")
        ]
        members: Annotated[
            tuple[Path, ...],
            m.Field(description="Resolved member roots"),
        ]
        engine: Annotated[
            t.Port[t.Infra.RopeProject],
            m.Field(
                exclude=True,
                description=(
                    "The one source engine project; planned effects enter its overlay"
                ),
            ),
        ]
        python_files: Annotated[
            t.Port[dict[Path, tuple[Path, ...]]],
            m.Field(exclude=True, description="Python sources of each member"),
        ]
        directory_facts: Annotated[
            t.Port[dict[Path, tuple[Path | None, str]]],
            m.Field(
                exclude=True,
                description="Physical directory owner and package name",
            ),
        ]
        python_module_facts: Annotated[
            t.Port[
                dict[
                    t.Infra.RopeNativeParsedModule,
                    FlextInfraModelsCodegenLazyInit.PythonModuleFacts,
                ]
            ],
            m.Field(
                exclude=True,
                description="Shared static facts keyed by the original engine parse",
            ),
        ]
        sources: Annotated[
            t.Port[dict[Path, p.Infra.WorkspaceSnapshotSource]],
            m.Field(exclude=True, description="Authenticated reads of this run"),
        ]
        packages: Annotated[
            t.Port[dict[Path, str]],
            m.Field(exclude=True, description="Dotted package of each directory"),
        ]
        import_edges: Annotated[
            t.Port[dict[Path, tuple[frozenset[str], frozenset[str]]]],
            m.Field(
                exclude=True,
                description="Runtime and typing-only imported modules per source",
            ),
        ]
        bootstrap_dependencies: Annotated[
            t.Port[
                dict[
                    Path,
                    p.Infra.WorkspaceBootstrapDependencies,
                ]
            ],
            m.Field(
                exclude=True, description="Bootstrap facts per native source epoch"
            ),
        ]
        absolute_import_roots: Annotated[
            t.Port[dict[Path, t.StrTuple]],
            m.Field(
                exclude=True,
                description="Absolute imported package roots per captured member",
            ),
        ]
        import_namespaces: Annotated[
            t.Port[dict[tuple[Path, Path], tuple[Path, str] | None]],
            m.Field(
                exclude=True,
                description="Import-law namespace election per consumer and source",
            ),
        ]
        class_ancestors: Annotated[
            t.Port[dict[str, t.StrTuple]],
            m.Field(
                exclude=True,
                description="C3 method order per qualified class identity",
            ),
        ]
        exports: Annotated[
            t.Port[dict[Path, Sequence[str]]],
            m.Field(exclude=True, description="Declared public names per module"),
        ]
        bindings: Annotated[
            t.Port[dict[Path, dict[str, str]]],
            m.Field(
                exclude=True,
                description="Module-level name to bound qualified source per module",
            ),
        ]
        initializer_aliases: Annotated[
            t.Port[dict[Path, dict[str, str]]],
            m.Field(exclude=True, description="Aliases each initializer publishes"),
        ]
        receiver_bindings: Annotated[
            t.Port[dict[tuple[Path, str], Path | None]],
            m.Field(
                exclude=True,
                description="Module each source binds a facade letter from",
            ),
        ]
        facade_paths: Annotated[
            t.Port[dict[tuple[Path, str], Path]],
            m.Field(exclude=True, description="Facade module per package and letter"),
        ]
        pyproject_texts: Annotated[
            t.Port[dict[tuple[Path, str], str]],
            m.Field(
                exclude=True,
                description="Recovered pyproject text per path and digest",
            ),
        ]
        codemod_renderings: Annotated[
            t.Port[
                dict[
                    tuple[Path, str],
                    FlextInfraModelsRefactorGrep.CodemodNativeGenerated,
                ]
            ],
            m.Field(
                exclude=True,
                description=(
                    "Native codemod rendering per member root and render-input digest"
                ),
            ),
        ]


__all__: list[str] = ["FlextInfraModelsWorkspaceSnapshot"]
