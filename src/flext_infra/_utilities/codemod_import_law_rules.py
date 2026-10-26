"""Import-law rules over the whole project: layer direction and cycles.

A module's import-layer rank and the runtime import graph are verdicts over
the whole project. This family renders the layer-direction law as native
rule documents (one per importing layer, plus the layer-zero windows) and
reports every module of a runtime import cycle, so mod and check block on the
same facts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from pathlib import Path

from flext_cli import u

from flext_infra import FlextInfraConfig, c, config, m, p, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodemodRules,
    FlextInfraUtilitiesImportLaw,
    FlextInfraUtilitiesNamespaceConfig,
    FlextInfraUtilitiesProjectDiscovery,
    FlextInfraUtilitiesPyproject,
    FlextInfraUtilitiesRopeAnalysisWorkspace,
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesWorkspaceSnapshot,
)
from flext_infra._utilities._rope_analysis.sourcescan import (
    FlextInfraUtilitiesRopeAnalysisSourceScan,
)
from flext_infra._utilities._rope_source_bases_runtime import (
    FlextInfraUtilitiesRopeSourceBasesRuntime,
)
from flext_infra._utilities.codemod_native_package_utilities import (
    FlextInfraUtilitiesCodemodNativePackageUtilities,
)
from flext_infra._utilities.codemod_native_utilities import (
    FlextInfraUtilitiesCodemodNativeUtilities,
)
from flext_infra._utilities.codemod_project import FlextInfraUtilitiesCodemodProject


class FlextInfraUtilitiesCodemodImportLawRules:
    """Render the import-layer direction law and report runtime import cycles."""

    @classmethod
    def codemod_import_cycle_issues(cls, root: Path) -> t.VariadicTuple[m.Infra.Issue]:
        """Report every module the runtime import graph places in a cycle.

        The cycle is a whole-graph verdict over each governed project's
        module-level imports (ENFORCE-006): one issue per member module names
        the complete cycle, so mod and check block on the same graph.

        Returns:
            One blocking issue per module of every runtime import cycle.

        """
        resolved = root.resolve()
        issues: list[m.Infra.Issue] = []
        for project_root in FlextInfraUtilitiesProjectDiscovery.governed_project_roots(
            resolved
        ):
            if not FlextInfraUtilitiesNamespaceConfig.namespace_enabled(project_root):
                continue
            graph, modules = FlextInfraUtilitiesCodemodProject.project_import_graph(
                project_root
            )
            cycles = FlextInfraUtilitiesCodemodProject.project_import_cycles(graph)
            issues.extend(
                m.Infra.Issue(
                    file=path.relative_to(resolved).as_posix(),
                    line=1,
                    column=1,
                    code=c.Infra.CODEMOD_IMPORT_CYCLE_CODE,
                    message=(
                        f"Runtime import of `{module}` closes an import cycle "
                        f"({' -> '.join(sorted(cycles[module]))}): break it at "
                        "the module that does not own the dependency."
                    ),
                )
                for path, module in sorted(modules.items())
                if module in cycles
            )
        return tuple(issues)

    @classmethod
    def codemod_reverse_import_rules(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> t.MappingKV[str, t.JsonMapping]:
        """Render the import-layer direction law, one document per layer.

        Each module's layer is the import law's path role, with the native
        service ancestry electing ``services`` for an ``other`` module. A
        runtime import of a later layer's letter from the OWN package root,
        or of a later own module, is banned; ``if TYPE_CHECKING:`` imports are
        annotations. An upstream FLEXT package's letters are the hierarchical
        composition the own facades build on, never a reverse import of the
        own facade under assembly (operator rulings 2026-10-25, tracker keys
        ``operator-ruling-2026-10-25-upstream-letter-canonical`` and
        ``operator-ruling-2026-10-25-models-u-imports-pydantic-home``).
        Layer-zero modules compare against ``u``, and their settings/config
        modules never import the protocols facade at runtime.

        Returns:
            The rendered rule documents keyed by rule id.

        """
        root = project.absolute()
        package = FlextInfraUtilitiesPyproject.project_package_name(root)
        order = tuple(config.Infra.tooling.lazy_init.import_layer_order)
        layer_zero = frozenset(
            FlextInfraUtilitiesCodemodNativePackageUtilities.codemod_layer_zero_files(
                snapshot, root
            )
        )
        ranks = cls._project_layer_ranks(snapshot, root)
        facts = (
            cls._runtime_letter_ranks(order),
            cls._reverse_import_targets(ranks),
            FlextInfraUtilitiesCodemodNativeUtilities.codemod_own_package_names(root),
        )
        guard = FlextInfraUtilitiesCodemodRules.codemod_provider_utility_rule(
            FlextInfraConfig.ssot_config_dir().parent / c.Infra.CODEMOD_CONFIG_RELPATH,
            c.Infra.CODEMOD_TYPE_CHECKING_GUARD_UTILITY,
        )
        documents: dict[str, t.JsonMapping] = {}
        for rank, layer in enumerate(order):
            files = sorted(
                relative
                for relative, owner in ranks.values()
                if owner == rank
                and relative not in layer_zero
                and Path(relative).name != c.Infra.INIT_PY
            )
            documents.update(
                cls._layer_reverse_document(
                    (package, layer, files),
                    cls._reverse_import_document(facts, (rank, len(order)), guard),
                )
            )
        documents.update(
            cls._settings_reverse_documents(package, sorted(layer_zero), facts, guard)
        )
        return documents

    @staticmethod
    def _layer_reverse_document(
        layer: t.Triple[str, str, t.StrSequence],
        document: t.JsonMapping | None,
    ) -> t.MappingKV[str, t.JsonMapping]:
        """Bind one importing layer's body to the layer's own files.

        Returns:
            The layer's rule document keyed by its id, or nothing when the
            layer owns no file or bans no later target.

        """
        package, name, files = layer
        if not files or document is None:
            return {}
        separator = c.Infra.CODEMOD_GENERATED_ID_SEPARATOR
        rule_id = (
            f"{c.Infra.CODEMOD_REVERSE_IMPORT_SHAPE}{separator}"
            f"{package}{separator}{name}"
        )
        return {
            rule_id: {
                "id": rule_id,
                "files": [f"**/{relative}" for relative in files],
                **document,
                "message": (
                    "Reverse runtime import: lazy exports and compose modules "
                    "do not change layer ownership. Move runtime behavior to "
                    "its owning layer; TYPE_CHECKING is only valid when the "
                    "dependency is exclusively an annotation."
                ),
            }
        }

    @staticmethod
    def _reverse_import_targets(
        ranks: t.MappingKV[str, t.Pair[str, int]],
    ) -> t.MappingKV[str, int]:
        """Rank every dotted own module a runtime import may target.

        A package root is no layer of its own: its letters are judged by the
        letter branch, so only dotted modules are layer targets. An upstream
        package's modules are composition, not a reverse own import; a deep
        path into them is the deep-import and private-import laws'.

        Returns:
            Each dotted own module mapped to its layer rank.

        """
        return {
            module: rank for module, (_relative, rank) in ranks.items() if "." in module
        }

    @classmethod
    def _settings_reverse_documents(
        cls,
        package: str,
        zero: t.StrSequence,
        facts: t.Triple[t.MappingKV[str, int], t.MappingKV[str, int], t.StrSequence],
        guard: t.JsonMapping,
    ) -> t.MappingKV[str, t.JsonMapping]:
        """Render the layer-zero windows: up to ``u``, and protocols in settings.

        Returns:
            The bounded reverse-import documents keyed by rule id.

        """
        order = tuple(config.Infra.tooling.lazy_init.import_layer_order)
        separator = c.Infra.CODEMOD_GENERATED_ID_SEPARATOR
        documents: dict[str, t.JsonMapping] = {}
        bounded = (
            (
                c.Infra.CODEMOD_REVERSE_IMPORT_SETTINGS_SHAPE,
                zero,
                (order.index(c.Infra.FacadeFamily.U), len(order)),
                (
                    "Reverse runtime import in a settings layer: only the "
                    "declaration facades up to `u` are runtime imports here."
                ),
            ),
            (
                c.Infra.CODEMOD_SETTINGS_PROTOCOLS_SHAPE,
                [
                    relative
                    for relative in zero
                    if Path(relative).stem.lstrip("_")
                    in c.Infra.IMPORT_LAW_ROOT_SINGLETONS
                ],
                (
                    order.index(c.Infra.FacadeFamily.T),
                    order.index(c.Infra.FacadeFamily.P) + 1,
                ),
                "The protocols facade is TYPE_CHECKING-only in a settings layer.",
            ),
        )
        for shape, files, window, message in bounded:
            document = cls._reverse_import_document(facts, window, guard)
            if files and document is not None:
                rule_id = f"{shape}{separator}{package}"
                documents[rule_id] = {
                    "id": rule_id,
                    "files": [f"**/{relative}" for relative in files],
                    **document,
                    "message": message,
                }
        return documents

    @staticmethod
    def _reverse_import_document(
        facts: t.Triple[t.MappingKV[str, int], t.MappingKV[str, int], t.StrSequence],
        window: t.Pair[int, int],
        guard: t.JsonMapping,
    ) -> t.JsonMapping | None:
        """Build the native body banning runtime imports above ``window[0]``.

        Targets rank strictly above the owner layer and below ``window[1]``.

        Returns:
            The rule body, or ``None`` when no letter or module is later.

        """
        letters, targets, facade_packages = facts
        owner, ceiling = window
        later_letters = sorted(
            letter for letter, rank in letters.items() if owner < rank < ceiling
        )
        later_modules = sorted(
            module for module, rank in targets.items() if owner < rank < ceiling
        )
        exact = (
            FlextInfraUtilitiesCodemodNativePackageUtilities.codemod_exact_names_rule
        )
        branches: list[t.JsonValue] = []
        if later_letters:
            branches.append({
                "kind": "dotted_name",
                **exact(later_letters),
                "not": {
                    "inside": {"kind": "import_from_statement", "field": "module_name"}
                },
                "inside": {
                    "kind": "import_from_statement",
                    "stopBy": "end",
                    "has": {
                        "field": "module_name",
                        "kind": "dotted_name",
                        **exact(facade_packages),
                    },
                },
            })
        if later_modules:
            module_rule: t.JsonDict = {"kind": "dotted_name", **exact(later_modules)}
            branches.extend((
                {
                    **module_rule,
                    "inside": {"kind": "import_from_statement", "field": "module_name"},
                },
                {
                    **module_rule,
                    "inside": {"kind": "import_statement", "stopBy": "end"},
                },
            ))
        if not branches:
            return None
        guard_id = c.Infra.CODEMOD_TYPE_CHECKING_GUARD_UTILITY
        return {
            "language": c.Infra.CODEMOD_PYTHON_LANGUAGE,
            "severity": "error",
            "utils": {guard_id: dict(guard)},
            "rule": {"not": {"matches": guard_id}, "any": branches},
        }

    @classmethod
    def _project_layer_ranks(
        cls,
        snapshot: p.Infra.WorkspaceSnapshot,
        root: Path,
    ) -> t.MappingKV[str, t.Pair[str, int]]:
        """Rank every module of the project in the import-layer order.

        A module whose path names no layer holds ``services`` when one of its
        classes derives from the service root; that native ancestry is only
        resolved for the modules a syntactic class-name pre-election admits.

        Returns:
            Each dotted module mapped to its relative path and layer rank.

        """
        snapshots = FlextInfraUtilitiesWorkspaceSnapshot
        sources = {
            path: snapshots.workspace_source(snapshot, path).text
            for path in snapshots.workspace_python_files(snapshot, root)
        }
        trees = {
            path: snapshots.workspace_module_tree(snapshot, path) for path in sources
        }
        order = tuple(config.Infra.tooling.lazy_init.import_layer_order)
        located = {
            path: found
            for path in sources
            if (
                found := FlextInfraUtilitiesImportLaw.snapshot_import_namespace(
                    snapshot, root, path
                )
            )
            is not None
        }
        ranks = {
            path: FlextInfraUtilitiesImportLaw.module_import_layer(
                ".".join(path.relative_to(root).with_suffix("").parts)
            )
            for path in located
        }
        other = order.index(c.Infra.IMPORT_LAW_OTHER_LAYER)
        candidates = cls._service_candidates(
            {path: trees[path] for path, rank in ranks.items() if rank == other},
            trees,
        )
        for path in cls._service_modules(root, sources, candidates, trees):
            ranks[path] = order.index("services")
        return {
            found[1]: (path.relative_to(root).as_posix(), ranks[path])
            for path, found in located.items()
        }

    @staticmethod
    def _service_candidates(
        others: t.MappingKV[Path, ast.Module], sources: t.MappingKV[Path, ast.Module]
    ) -> frozenset[Path]:
        """Pre-elect the modules a class of which may derive from the service root.

        Class names propagate from the service root ``s`` through every
        project class whose syntactic bases name one of them; only a module
        declaring such a class can hold the services role, which the native
        ancestry then proves.

        Returns:
            The ``other`` modules whose classes may descend from ``s``.

        """
        declared: dict[Path, list[t.Pair[str, frozenset[str]]]] = {}
        names = {"s"}
        for path, tree in sources.items():
            names.update(
                node.value.id
                for node in tree.body
                if isinstance(node, ast.Assign)
                and isinstance(node.value, ast.Name)
                and any(
                    isinstance(target, ast.Name) and target.id == "s"
                    for target in node.targets
                )
            )
            declared[path] = list(
                FlextInfraUtilitiesRopeAnalysisSourceScan.module_class_base_names(tree)
            )
        while True:
            grown = names | {
                name
                for classes in declared.values()
                for name, bases in classes
                if bases & names
            }
            if grown == names:
                break
            names = grown
        return frozenset(
            path
            for path in others
            if any(name in names and name != "s" for name, _bases in declared[path])
        )

    @classmethod
    def _service_modules(
        cls,
        root: Path,
        sources: t.MappingKV[Path, str],
        candidates: frozenset[Path],
        trees: t.MappingKV[Path, ast.Module],
    ) -> frozenset[Path]:
        """Elect the candidate modules declaring a class of the service root.

        The base-layer modules binding the service root ``s`` and each
        candidate's own top-level classes come from the parsed sources; one
        source C3 resolver then answers every ancestry, resolving each
        ancestor once.

        Returns:
            The candidate modules that hold the services role.

        """
        if not candidates:
            return frozenset()
        order = tuple(config.Infra.tooling.lazy_init.import_layer_order)
        base_layer = order.index(c.Infra.IMPORT_LAW_BASE_LAYER)
        modules = {
            FlextInfraUtilitiesRopeAnalysisWorkspace.module_name_for_file(
                path, project_root=root
            ): (path, text)
            for path, text in sources.items()
            if path.suffix == c.Infra.EXT_PYTHON
        }
        roots = tuple(
            m.Infra.SourceClassReference(
                target=name, attributes=("s",), qualified_base=f"{name}.s"
            )
            for name, (path, text) in modules.items()
            if FlextInfraUtilitiesImportLaw.module_import_layer(
                ".".join(path.relative_to(root).with_suffix("").parts)
            )
            == base_layer
            and "s" in cls._module_level_bindings(trees[path])
        )
        declared = tuple(
            (
                path,
                m.Infra.SourceClassReference(
                    target=name,
                    attributes=(node.name,),
                    qualified_base=f"{name}.{node.name}",
                ),
            )
            for name, (path, text) in modules.items()
            if path in candidates
            for node in trees[path].body
            if isinstance(node, ast.ClassDef)
        )
        if not roots or not declared:
            return frozenset()
        with (
            FlextInfraUtilitiesRopeCore.open_project(root) as project,
            project.frozen_layout(),
        ):
            reached = FlextInfraUtilitiesRopeSourceBasesRuntime.source_class_reaches(
                project,
                modules,
                tuple(reference for _path, reference in declared),
                roots,
            )
        return frozenset(
            path
            for (path, _reference), anchors in zip(declared, reached, strict=True)
            if anchors
        )

    @staticmethod
    def _module_level_bindings(tree: ast.Module) -> frozenset[str]:
        """Name every module-level assignment, import or class binding.

        Returns:
            The names the module body binds.

        """
        return frozenset(
            name
            for node in tree.body
            for name in (
                *(
                    target.id
                    for target in (
                        node.targets
                        if isinstance(node, ast.Assign)
                        else (node.target,)
                        if isinstance(node, ast.AnnAssign)
                        else ()
                    )
                    if isinstance(target, ast.Name)
                ),
                *(
                    alias.asname or alias.name.split(".")[0]
                    for alias in (
                        node.names
                        if isinstance(node, ast.Import | ast.ImportFrom)
                        else ()
                    )
                ),
                *((node.name,) if isinstance(node, ast.ClassDef) else ()),
            )
        )

    @staticmethod
    def _runtime_letter_ranks(order: t.StrSequence) -> t.MappingKV[str, int]:
        """Rank every runtime facade letter in the import-layer order.

        A letter naming a layer is that layer; a declared layer alias ranks
        with its layer; every other runtime alias stands for ``base``.

        Returns:
            Each runtime letter mapped to its layer rank.

        """
        aliases = config.Infra.tooling.lazy_init.layer_aliases
        return {
            letter: order.index(
                letter
                if letter in order
                else aliases.get(letter, c.Infra.IMPORT_LAW_BASE_LAYER)
            )
            for letter in u.runtime_alias_names(c.Infra.PKG_CORE_UNDERSCORE)
        }


__all__: list[str] = ["FlextInfraUtilitiesCodemodImportLawRules"]
