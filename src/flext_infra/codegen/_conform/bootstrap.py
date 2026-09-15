"""Bootstrap environment and toolchain policy projections."""

from __future__ import annotations

from collections.abc import MutableMapping
from pathlib import Path

from ... import c, m, t, u


class FlextInfraCodegenConformBootstrap:
    """Bootstrap environment and toolchain policy projections."""

    @staticmethod
    def _mise_bootstrap_environment() -> m.Infra.MiseBootstrapEnvironmentSpec:
        """Project the single generated Mise isolation contract into templates."""
        return u.Infra.mise_bootstrap_environment()

    @staticmethod
    def _link_mode(
        repository: m.Infra.RepositoryRef, toolchain: m.Infra.ToolchainSpec
    ) -> str:
        """Resolve the repository override through one codegen authority."""
        return repository.uv_link_mode or toolchain.uv_link_mode

    @staticmethod
    def _dependency_cooldown_policy(
        repository: m.Infra.RepositoryRef, toolchain: m.Infra.ToolchainSpec
    ) -> tuple[tuple[str, ...], MutableMapping[str, str]]:
        """Compose fleet defaults with the repository's narrower policy."""
        exclusions = dict.fromkeys(toolchain.dependency_cooldown_exclusions)
        overrides = dict(toolchain.dependency_cooldown_overrides)
        for package in repository.dependency_cooldown_exclusions:
            overrides.pop(package, None)
            exclusions[package] = None
        for package, cutoff in repository.dependency_cooldown_overrides.items():
            exclusions.pop(package, None)
            overrides[package] = cutoff
        return tuple(exclusions), overrides

    @staticmethod
    def _discover_script_verbs(
        repository_root: Path,
    ) -> t.VariadicTuple[m.Infra.MakeVerbSpec]:
        """Discover script verbs from scripts/<verb>/all.sh in the repository root.

        The filesystem is the SSOT: a verb is emitted only when its all.sh
        entrypoint exists. No manual list is required.
        """
        scripts_dir = repository_root / "scripts"
        if not scripts_dir.is_dir():
            return ()
        discovered = [
            m.Infra.MakeVerbSpec(
                name=entry.name, description=f"Script command: {entry.name}"
            )
            for entry in sorted(scripts_dir.iterdir())
            if entry.is_dir() and (entry / "all.sh").is_file()
        ]
        return tuple(discovered)

    @staticmethod
    def _merge_extra_verbs(
        declared: t.VariadicTuple[m.Infra.MakeVerbSpec],
        discovered: t.VariadicTuple[m.Infra.MakeVerbSpec],
        canonical_names: frozenset[str],
    ) -> t.VariadicTuple[m.Infra.MakeVerbSpec]:
        """Union declared and discovered script verbs deduplicated by name.

        Why (cosmos-3flk9): object-level dedup never converges because declared
        verbs carry their canonical config descriptions while discoveries carry
        ``Script command: <name>``, so every verb entered ``extra_verbs`` twice
        and the generated Makefile emitted colliding ``_builtin-<verb>``
        recipes. The declared config verb is the writable authority and wins;
        a discovery is dropped when it would shadow a canonical ``make.verbs``
        builtin, whose native ``_builtin-<verb>`` implementation is the only
        owner of that name in the generated Makefile.
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
    def _surface_contract(
        cls, surface: c.Infra.CodegenConformSurface
    ) -> m.Infra.CodegenConformSurfaceContract:
        match surface:
            case c.Infra.CodegenConformSurface.ALL:
                return m.Infra.CodegenConformSurfaceContract(complete_governed=True)
            case c.Infra.CodegenConformSurface.DEPENDENCIES:
                return m.Infra.CodegenConformSurfaceContract(
                    destinations=frozenset({c.Infra.PYPROJECT_FILENAME}),
                    delegates=False,
                    custom=False,
                )
            case c.Infra.CodegenConformSurface.PYPROJECT:
                return m.Infra.CodegenConformSurfaceContract(
                    destinations=frozenset({c.Infra.PYPROJECT_FILENAME}),
                    delegates=False,
                    custom=False,
                )
            case c.Infra.CodegenConformSurface.MAKEFILE:
                return m.Infra.CodegenConformSurfaceContract(
                    destinations=frozenset({c.Infra.MAKEFILE_FILENAME}),
                    pyproject=False,
                    custom=False,
                )
            case _:
                msg = f"Unsupported codegen conform surface: {surface}"
                raise ValueError(msg)
