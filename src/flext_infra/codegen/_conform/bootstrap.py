"""Conform service root: validated request state and toolchain policy.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableMapping
from pathlib import Path
from typing import TYPE_CHECKING, Annotated

from flext_infra import c, m, s, t, u

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraCodegenConformBootstrap(s[m.Infra.CodegenResult]):
    """Root of the conform chain: request state and toolchain policy projections.

    This is the only orchestrator for Make/toolchain/source conformance.
    Rendering stays in flext-cli; Git-source TOML policy and attached detection
    are composed from their separately owned u.Infra/workspace services.
    """

    request: Annotated[
        m.Infra.CodegenConformRequest | None,
        m.Field(default=None, exclude=True, description="Validated conform request"),
    ] = None
    repository_root: Annotated[
        Path,
        m.Field(default=Path(), exclude=True, description="Conform repository root"),
    ] = Path()
    initial_workspace: Annotated[
        m.Infra.WorkspaceSpec | None,
        m.Field(
            default=None,
            exclude=True,
            description="Validated scaffold specification included in the atomic plan",
        ),
    ] = None
    ports: Annotated[
        m.Infra.CodegenConformPorts | None,
        m.Field(
            default=None,
            exclude=True,
            description=(
                "Docs planner and fresh-import probe wired by the facade; the "
                "complete surface fails before any effect without them"
            ),
        ),
    ] = None
    planning_issues: Annotated[
        list[m.Infra.Issue],
        m.Field(
            default_factory=list,
            exclude=True,
            description="Native file planning failures retained by this invocation",
        ),
    ]

    def _record_file_failure(self, path: Path, error: str) -> None:
        """Retain an actual target failure through the shared diagnostic model."""
        self.planning_issues.append(
            m.Infra.Issue(
                file=str(path),
                line=0,
                column=0,
                code=c.Infra.ToolOutcome.ERROR.value,
                message=error,
            ),
        )

    @staticmethod
    def link_mode(
        repository: m.Infra.RepositoryRef,
        toolchain: p.Infra.ToolchainSpec,
    ) -> str:
        """Resolve the repository override through one codegen authority.

        Returns:
            The resulting ``str``.

        """
        return repository.uv_link_mode or toolchain.uv_link_mode

    @staticmethod
    def _discover_script_verbs(
        repository_root: Path,
    ) -> t.VariadicTuple[m.Infra.MakeVerbSpec]:
        """Discover script verbs from scripts/<verb>/all.sh in the repository root.

        The filesystem is the SSOT: a verb is emitted only when its all.sh
        entrypoint exists. No manual list is required.

        Returns:
            The resulting ``t.VariadicTuple[m.Infra.MakeVerbSpec]``.

        """
        scripts_dir = repository_root / c.Infra.DIR_SCRIPTS
        if not scripts_dir.is_dir():
            return ()
        discovered = [
            m.Infra.MakeVerbSpec(
                name=entry.name,
                description=f"Script command: {entry.name}",
            )
            for entry in sorted(scripts_dir.iterdir())
            if entry.is_dir() and (entry / "all.sh").is_file()
        ]
        return tuple(discovered)

    @staticmethod
    def _declared_environment_imports(
        target: m.Infra.RepositoryConformTarget,
        workspace: m.Infra.WorkspaceSpec,
    ) -> t.VariadicTuple[t.Pair[str, Path]]:
        """Resolve diagnostic package identities from their declared projects.

        Returns:
            Package names and exact project roots, without guessing distribution names.

        Raises:
            ValueError: If declared package namespace is unresolved.
        """
        roots = (
            *((target.root,) if target.repository.package else ()),
            *(
                target.root / member.path
                for member in workspace.subprojects
                if target.make_profile is c.Infra.MakeProfile.WORKSPACE
                and member.package
            ),
        )
        imports = tuple((u.Infra.project_package_name(root), root) for root in roots)
        if any(not name for name, _root in imports):
            msg = f"declared package namespace is unresolved: {target.root}"
            raise ValueError(msg)
        return imports

    @staticmethod
    def _merge_extra_verbs(
        declared: t.VariadicTuple[m.Infra.MakeVerbSpec],
        discovered: t.VariadicTuple[m.Infra.MakeVerbSpec],
        canonical_names: frozenset[str],
    ) -> t.VariadicTuple[m.Infra.MakeVerbSpec]:
        """Union declared and discovered script verbs deduplicated by name.

        Why: object-level dedup never converges because declared
        verbs carry their canonical config descriptions while discoveries carry
        ``Script command: <name>``, so every verb entered ``extra_verbs`` twice
        and the generated Makefile emitted colliding ``_builtin-<verb>``
        recipes. The declared config verb is the writable authority and wins;
        a discovery is dropped when it would shadow a canonical ``make.verbs``
        builtin, whose native ``_builtin-<verb>`` implementation is the only
        owner of that name in the generated Makefile.

        Returns:
            The resulting ``t.VariadicTuple[m.Infra.MakeVerbSpec]``.

        Raises:
            ValueError: If config extra_verbs declares canonical verb.

        """
        merged: MutableMapping[str, m.Infra.MakeVerbSpec] = {}
        for verb in discovered:
            if verb.name in canonical_names:
                continue
            merged.setdefault(verb.name, verb)
        for verb in declared:
            if verb.name in canonical_names:
                msg = (
                    f"config extra_verbs declares canonical verb {verb.name!r}; "
                    "extra verbs must never shadow canonical make.verbs builtins"
                )
                raise ValueError(msg)
            merged[verb.name] = verb
        return tuple(merged.values())

    @classmethod
    def surface_contract(
        cls,
        surface: c.Infra.CodegenConformSurface,
    ) -> m.Infra.CodegenConformSurfaceContract:
        """Resolve a declared surface without defaulting an invalid input.

        Returns:
            The contract owned by the declared conformance surface.

        """
        match surface:
            case c.Infra.CodegenConformSurface.ALL:
                return m.Infra.CodegenConformSurfaceContract(complete_governed=True)
            case (
                c.Infra.CodegenConformSurface.LAZY_INIT
                | c.Infra.CodegenConformSurface.FACADES
            ):
                return m.Infra.CodegenConformSurfaceContract(
                    delegates=False,
                    pyproject=False,
                    templates=False,
                    custom=False,
                )
            case c.Infra.CodegenConformSurface.PYPROJECT:
                return m.Infra.CodegenConformSurfaceContract(
                    destinations=frozenset({c.PYPROJECT_FILENAME}),
                    delegates=False,
                    templates=False,
                    custom=False,
                )
            case c.Infra.CodegenConformSurface.DEPENDENCIES:
                return m.Infra.CodegenConformSurfaceContract(
                    destinations=frozenset({c.PYPROJECT_FILENAME}),
                    delegates=False,
                    custom=False,
                )
            case c.Infra.CodegenConformSurface.MAKEFILE:
                # The Makefile's bootstrap runs the generated lock publisher, so
                # a recovered Makefile without it could never finish make upg.
                return m.Infra.CodegenConformSurfaceContract(
                    destinations=c.Infra.MAKEFILE_BOOTSTRAP_DESTINATIONS,
                    pyproject=False,
                    custom=False,
                )
            case c.Infra.CodegenConformSurface.DOCS_CONFIG:
                destination = (
                    Path(c.Infra.DIR_DOCS) / c.Infra.DOCS_CONFIG_FILENAME
                ).as_posix()
                return m.Infra.CodegenConformSurfaceContract(
                    destinations=frozenset({destination}),
                    pyproject=False,
                    custom=False,
                )
            case c.Infra.CodegenConformSurface.ENVRC:
                return m.Infra.CodegenConformSurfaceContract(
                    destinations=frozenset({c.Infra.ENVRC_FILENAME}),
                    delegates=False,
                    pyproject=False,
                    custom=False,
                )
            case c.Infra.CodegenConformSurface.MISE_CONFIG:
                return m.Infra.CodegenConformSurfaceContract(
                    destinations=frozenset({c.Infra.MISE_TOML_FILENAME}),
                    delegates=False,
                    pyproject=False,
                    custom=False,
                )


__all__: list[str] = ["FlextInfraCodegenConformBootstrap"]
