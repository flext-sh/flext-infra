"""Census-derived constant consumer cutover across declared workspace members.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import cProfile
import pstats
from pathlib import Path

from flext_cli import cli

from flext_infra import c, config, m, p, t
from flext_infra._utilities import (
    FlextInfraUtilitiesPrivateImportAncestry,
    FlextInfraUtilitiesPrivateImportFacades,
)
from flext_infra._utilities._semantic_cutover.edits import (
    FlextInfraUtilitiesSemanticCutoverEdits,
)
from flext_infra._utilities._semantic_cutover.private_import_cst import (
    FlextInfraUtilitiesSemanticCutoverPrivateImportCst,
)


class FlextInfraUtilitiesSemanticConstantConsumers(
    FlextInfraUtilitiesSemanticCutoverPrivateImportCst,
    FlextInfraUtilitiesSemanticCutoverEdits,
):
    """Derive constant paths from declarations and rewrite proven bindings."""

    @classmethod
    def _plan_constant_consumers(
        cls,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        sources: t.MappingKV[Path, str],
    ) -> p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]:
        """Resolve every imported constants owner once for the complete census.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]``.

        """
        profile_path = (
            rope_workspace.repository_root / c.Infra.MOD_SCAN_REPORT_RELATIVE_PATH
        ).with_name(f"{c.Infra.SemanticCutoverPhase.CONSTANT_CONSUMERS}.pstats")
        profile_path.parent.mkdir(parents=True, exist_ok=True)
        profiler = cProfile.Profile()
        profiler.enable()
        try:
            return cls._profiled_constant_consumers(rope_workspace, sources)
        finally:
            profiler.disable()
            profiler.dump_stats(profile_path)
            policy = config.Infra.tooling.tools.pytest
            pstats.Stats(profiler).sort_stats(policy.profile_sort).print_stats(
                policy.profile_limit,
            )

    @classmethod
    def _profiled_constant_consumers(
        cls,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        sources: t.MappingKV[Path, str],
    ) -> p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]:
        """Profile the actual bulk census pipeline through its public owner.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Infra.SemanticMigrationEdit]]``.
        """
        facade_owner = FlextInfraUtilitiesPrivateImportFacades
        cli.display_text(f"census: resolve constants imports in {len(sources)} modules")
        statements = tuple(
            ast.unparse(node)
            for path, source in cls._editable_sources(sources)
            for node in ast.walk(ast.parse(source, filename=str(path)))
            if isinstance(node, ast.ImportFrom)
            and node.module
            and node.module.startswith(c.Infra.PKG_PREFIX_UNDERSCORE)
            and not node.level
        )
        modules = facade_owner.source_modules(sources, statements)
        cli.display_text(f"census: indexed {len(modules)} source identities")
        discovered = facade_owner.discover(modules)
        owners = {
            package: tuple(owner for owner in declarations if owner[1] == "c")
            for package, declarations in discovered.items()
        }
        bindings, _exports = facade_owner.declared_exports(modules)
        cli.display_text(f"census: indexed {len(bindings)} declared bindings")
        ancestry = FlextInfraUtilitiesPrivateImportAncestry
        bases = ancestry.FlextInfraUtilitiesPrivateImportAncestry.class_bases(
            modules,
        )
        references: t.MutableMappingKV[t.Pair[str, str], str | None] = {}
        cli.display_text(f"census: indexed {len(bases)} class declarations")
        family_modules = frozenset(
            name
            for declarations in owners.values()
            for _tree, _alias, _root, file_name in declarations
            for name in (Path(file_name).stem, f"_{Path(file_name).stem}")
        )
        constant_names = frozenset((
            "c",
            *(
                root_name
                for declarations in owners.values()
                for _tree, _alias, root_name, _file_name in declarations
            ),
            *(
                identity.rsplit(".", 1)[-1]
                for identity in bases
                if family_modules.intersection(identity.split("."))
            ),
        ))

        def rewrite(path: Path, source: str) -> t.Infra.TransformResult:
            if not any(
                imported.name in constant_names
                and not (imported.name == "c" and imported.asname is None)
                for node in ast.walk(ast.parse(source, filename=str(path)))
                if isinstance(node, ast.ImportFrom)
                and node.module
                and node.module.startswith(c.Infra.PKG_PREFIX_UNDERSCORE)
                for imported in node.names
            ):
                return source, ()
            return cls._rewrite_constant_consumer(
                path,
                source,
                rope_workspace,
                (owners, bindings, bases),
                references,
            )

        return cls._semantic_edits(cls._editable_sources(sources), rewrite)

    @classmethod
    def _rewrite_constant_consumer(
        cls,
        path: Path,
        source: str,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        index: t.Infra.ConstantFacadeIndex,
        references: t.MutableMappingKV[t.Pair[str, str], str | None],
    ) -> t.Infra.TransformResult:
        facade_owner = FlextInfraUtilitiesPrivateImportFacades
        convention = rope_workspace.convention(path)
        policy = convention.module_policy
        if policy.expected_alias == "c" or policy.expected_family == "Constants":
            return source, ()
        layout = convention.project_layout
        if layout is None:
            return source, ()
        tree = ast.parse(source, filename=str(path))
        package = cls._constant_facade_package(tree, layout.package_name, path)
        context = (tree, package, index, references)
        removals, replacements = cls._constant_replacement_state(context)
        if not replacements:
            return source, ()
        facade_owner.require_unshadowed_alias(
            tree,
            package,
            "c",
            path,
            removals,
        )
        plan = m.Infra.PrivateImportRewritePlan(
            removals={module: frozenset(names) for module, names in removals.items()},
            obsolete_imports={},
            replacements=replacements,
            public_imports={"c": package},
        )
        updated = cls._rewrite_private_import_source(
            source,
            plan,
            runtime_public_imports=frozenset({"c"}),
        )
        return updated, tuple(
            f"constant consumer {identity} -> {reference}"
            for identity, reference in sorted(replacements.items())
        )

    @classmethod
    def _constant_replacement_state(
        cls,
        context: t.Infra.ConstantConsumerContext,
    ) -> t.Pair[
        t.MutableMappingKV[str, set[str]],
        t.MutableStrMapping,
    ]:
        tree, package, index, references = context
        facade_owner = FlextInfraUtilitiesPrivateImportFacades
        owners, bindings, bases = index
        removals: t.MutableMappingKV[str, set[str]] = {}
        replacements: t.MutableStrMapping = {}
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom) or not node.module or node.level:
                continue
            for imported in node.names:
                if imported.name == "c" and imported.asname is None:
                    continue
                qualified = f"{node.module}.{imported.name}"
                key = package, qualified
                if key not in references:
                    references[key] = facade_owner.public_reference(
                        owners=owners.get(package, ()),
                        package=package,
                        qualified=qualified,
                        bindings=bindings,
                        class_bases=bases,
                    )
                reference = references[key]
                if reference is None:
                    continue
                local_name = imported.asname or imported.name
                if cls._is_composition_base(tree, local_name):
                    continue
                removals.setdefault(node.module, set()).add(imported.name)
                replacements[qualified] = reference
        return removals, replacements

    @staticmethod
    def _is_composition_base(tree: ast.AST, local_name: str) -> bool:
        return any(
            isinstance(base, ast.Name) and base.id == local_name
            for declaration in ast.walk(tree)
            if isinstance(declaration, ast.ClassDef)
            for base in declaration.bases
        )

    @staticmethod
    def _constant_facade_package(
        tree: ast.Module,
        declared_package: str,
        path: Path,
    ) -> str:
        """Select the existing c binding, or the module's declared facade.

        Returns:
            The resolved constants facade package name.

        Raises:
            ValueError: If multiple constants facades are bound as ``c``.

        """
        public_packages = {
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom)
            and node.module
            and not node.level
            and any(item.name == "c" and item.asname is None for item in node.names)
        }
        if len(public_packages) > 1:
            msg = f"multiple constants facades bound as c in {path}"
            raise ValueError(msg)
        return next(iter(public_packages), declared_package)


__all__: list[str] = ["FlextInfraUtilitiesSemanticConstantConsumers"]
