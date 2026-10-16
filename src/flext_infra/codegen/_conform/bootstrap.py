"""Conform service root: validated request state and toolchain policy.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableMapping
from pathlib import Path
from typing import Annotated, assert_never

from typing_extensions import TypeForm

from flext_infra import c, m, p, s, t, u


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
        t.MutableSequenceOf[m.Infra.Issue],
        m.Field(
            exclude=True,
            description="Native file planning failures retained by this invocation",
        ),
    ] = m.Field(default_factory=u.empty(TypeForm(t.MutableSequenceOf[m.Infra.Issue])))

    planning_exception: BaseException | None = m.Field(
        default=None,
        exclude=True,
        description="First native file planning cause",
    )
    producer: m.Infra.CodegenPhaseAnalysis | None = m.Field(
        default=None, exclude=True, description="Producer captured before planning"
    )
    docs_planner: p.Infra.DocsArtifactPlanner | None = m.Field(
        default=None,
        exclude=True,
        description="Actual docs planner retained before effects",
    )
    docs_producer: m.Infra.CodegenPhaseAnalysis | None = m.Field(
        default=None,
        exclude=True,
        description="Original docs producer captured before effects",
    )

    def _record_file_failure(
        self,
        path: Path,
        error: str,
        *,
        exception: BaseException | None = None,
    ) -> None:
        """Retain an actual target failure through the shared diagnostic model."""
        if self.planning_exception is None:
            self.planning_exception = exception
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

    def _declared_environment_imports(
        self,
        target: m.Infra.RepositoryConformTarget,
        workspace: m.Infra.WorkspaceSpec,
    ) -> t.VariadicTuple[t.Pair[str, Path]]:
        """Resolve diagnostic package identities from their declared projects.

        Paths stay relative to the target root so the rendered Makefile is
        environment-independent: an absolute root would embed the generating
        checkout's path and drift against CI's different workspace path.

        Returns:
            Package names and project roots relative to the target root, without
            guessing distribution names.

        Raises:
            ValueError: If the initial project declaration or a package namespace
                is unresolved.

        """
        roots: list[t.Pair[str, Path]] = []
        if target.repository.package:
            if (
                target.project is None
                and self.initial_workspace is not None
                and target.repository.name == self.initial_workspace.repository.name
                and not (target.root / c.PYPROJECT_FILENAME).exists()
            ):
                msg = f"scaffold environment has no project metadata: {target.root}"
                raise ValueError(msg)
            # The target root is the repository being conformed. At plan time a
            # scaffold's pyproject is planned, not yet on disk, so the declared
            # ProjectSpec owns the import name; reading the pyproject here failed
            # on the not-yet-materialized file. The declared name and the disk
            # resolution of a conformed repository are the same identity.
            declared_name = (
                target.project.package_name if target.project is not None else ""
            )
            roots.append(
                (declared_name or u.Infra.project_package_name(target.root), Path()),
            )
        if target.make_profile is c.Infra.MakeProfile.WORKSPACE:
            roots.extend(
                (u.Infra.project_package_name(target.root / member.path), member.path)
                for member in workspace.subprojects
                if member.package
            )
        imports = tuple(roots)
        if any(not name for name, _root in imports):
            msg = f"declared package namespace is unresolved: {target.root}"
            raise ValueError(msg)
        return tuple(imports)

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
        *,
        codegen: m.Infra.CodegenConfigSpec,
    ) -> m.Infra.CodegenConformSurfaceContract:
        """Resolve one admitted surface into its conformance contract.

        Args:
            surface: The declared conformance surface.
            codegen: The codegen configuration owning managed destinations.

        Returns:
            The contract owned by the declared conformance surface.

        """
        match surface:
            case c.Infra.CodegenConformSurface.ALL:
                contract = m.Infra.CodegenConformSurfaceContract(complete_governed=True)
            case c.Infra.CodegenConformSurface.RUNTIME_BINDINGS:
                contract = m.Infra.CodegenConformSurfaceContract(
                    destinations=cls._runtime_binding_destinations(codegen),
                    runtime_bindings=True,
                    delegates=False,
                    pyproject=False,
                    templates=False,
                    custom=False,
                )
            case (
                c.Infra.CodegenConformSurface.LAZY_INIT
                | c.Infra.CodegenConformSurface.FACADES
            ):
                contract = m.Infra.CodegenConformSurfaceContract(
                    delegates=False,
                    pyproject=False,
                    templates=False,
                    custom=False,
                )
            case c.Infra.CodegenConformSurface.PYPROJECT:
                contract = m.Infra.CodegenConformSurfaceContract(
                    destinations=cls._pyproject_destinations(codegen),
                    delegates=False,
                    templates=False,
                    custom=False,
                )
            case c.Infra.CodegenConformSurface.DEPENDENCIES:
                # The dependency planner projects the root pyproject and every
                # uv resolution pyproject, so the surface owns the same derived
                # destination set as PYPROJECT; a second enumeration refused
                # the resolution inputs a candidate needs before `make upg`.
                contract = m.Infra.CodegenConformSurfaceContract(
                    destinations=cls._pyproject_destinations(codegen),
                    delegates=False,
                    custom=False,
                )
            case (
                c.Infra.CodegenConformSurface.MAKEFILE
                | c.Infra.CodegenConformSurface.DOCS_CONFIG
            ):
                # The Makefile's bootstrap runs the generated lock publisher, so
                # a recovered Makefile without it could never finish make upg.
                contract = m.Infra.CodegenConformSurfaceContract(
                    destinations=(
                        c.Infra.MAKEFILE_BOOTSTRAP_DESTINATIONS
                        if surface is c.Infra.CodegenConformSurface.MAKEFILE
                        else frozenset({
                            (
                                Path(c.Infra.DIR_DOCS) / c.Infra.DOCS_CONFIG_FILENAME
                            ).as_posix()
                        })
                    ),
                    pyproject=False,
                    custom=False,
                )
            case c.Infra.CodegenConformSurface.WORKFLOWS:
                contract = m.Infra.CodegenConformSurfaceContract(
                    destinations=frozenset(
                        entry.destination
                        for entry in codegen.templates.entries
                        if Path(entry.destination).is_relative_to(
                            c.Infra.GITHUB_WORKFLOWS_RELATIVE_PATH,
                        )
                    ),
                    delegates=False,
                    pyproject=False,
                    tooling=False,
                    custom=False,
                )
            case (
                c.Infra.CodegenConformSurface.ENVRC
                | c.Infra.CodegenConformSurface.MISE_CONFIG
            ):
                contract = m.Infra.CodegenConformSurfaceContract(
                    destinations=frozenset({
                        c.Infra.ENVRC_FILENAME
                        if surface is c.Infra.CodegenConformSurface.ENVRC
                        else c.Infra.MISE_TOML_FILENAME
                    }),
                    delegates=False,
                    pyproject=False,
                    custom=False,
                )
            case _:
                assert_never(surface)
        return contract

    @staticmethod
    def _runtime_binding_destinations(
        codegen: m.Infra.CodegenConfigSpec,
    ) -> frozenset[str]:
        """Collect the managed runtime binding destinations.

        Args:
            codegen: The codegen configuration owning managed file specs.

        Returns:
            The managed runtime binding paths as POSIX strings.

        """
        return frozenset(
            item.path.as_posix()
            for item in codegen.managed_file_specs
            if item.runtime_binding
        )

    @staticmethod
    def _pyproject_destinations(
        codegen: m.Infra.CodegenConfigSpec,
    ) -> frozenset[str]:
        """Collect the managed pyproject destinations.

        Args:
            codegen: The codegen configuration owning resolution pyprojects.

        Returns:
            The root and resolution pyproject paths as POSIX strings.

        """
        return frozenset(
            path.as_posix()
            for path in (Path(c.PYPROJECT_FILENAME), *codegen.uv_resolution_pyprojects)
        )


__all__: list[str] = ["FlextInfraCodegenConformBootstrap"]
