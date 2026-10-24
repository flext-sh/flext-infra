"""Project-scope analyses the rule engine evaluates for rule data.

ast-grep matches one file's syntax. Some laws are verdicts over the whole
project: whether a module takes part in an import cycle, whether a facade's
namespace composes every class its family package declares. The engine owns
building those project facts once per admission pass, from the tree as it is
then (a pass after a rewrite reads the rewritten project); rule
documents name the verdict they need through ``metadata.context`` predicates.
No rule lives here: the rule data decides where a fact is asked and what it
means.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import sys
from collections.abc import Generator, Mapping, MutableMapping
from contextlib import closing, contextmanager
from contextvars import ContextVar
from functools import cache, lru_cache
from importlib.metadata import packages_distributions
from importlib.util import find_spec
from pathlib import Path
from types import MappingProxyType
from typing import ClassVar

from flext_cli import u
from packaging.utils import canonicalize_name

from flext_infra import c, config, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesBase,
    FlextInfraUtilitiesCodegenFacades,
    FlextInfraUtilitiesCodegenFilePlan,
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesCodemodBindingChain,
    FlextInfraUtilitiesCodemodRules,
    FlextInfraUtilitiesDeclarationPayload,
    FlextInfraUtilitiesImportLaw,
    FlextInfraUtilitiesIterationDirectory,
    FlextInfraUtilitiesProjectDiscovery,
    FlextInfraUtilitiesPyproject,
    FlextInfraUtilitiesRopeAnalysisWorkspace,
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeImports,
    FlextInfraUtilitiesRopeRuntimeModules,
    FlextInfraUtilitiesRopeRuntimeTypes,
    FlextInfraUtilitiesRopeStructure,
)
from flext_infra._utilities._rope.project import FlextInfraRopeProject
from flext_infra._utilities._rope_analysis.asthelpers import (
    FlextInfraUtilitiesRopeAnalysisAstHelpers,
)
from flext_infra._utilities._rope_analysis.exports import (
    FlextInfraUtilitiesRopeAnalysisExports,
)
from flext_infra._utilities._rope_analysis.importstate import (
    FlextInfraUtilitiesRopeAnalysisImportState,
)
from flext_infra._utilities._rope_source_bases_aliases import (
    FlextInfraUtilitiesRopeSourceBasesAliases,
)
from flext_infra._utilities._rope_source_bases_runtime import (
    FlextInfraUtilitiesRopeSourceBasesRuntime,
)
from flext_infra._utilities.rope_runtime_matching import (
    FlextInfraUtilitiesRopeRuntimeMatching,
)


class FlextInfraUtilitiesCodemodProject(
    FlextInfraUtilitiesCodemodBindingChain.FlextInfraUtilitiesCodemodBindingChain,
    FlextInfraUtilitiesImportLaw,
):
    """Evaluate rule context over project facts: packages, layers, graphs."""

    _module_role_cache: ClassVar[ContextVar[t.MutableMappingKV[Path, int] | None]] = (
        ContextVar("codemod_module_role_cache", default=None)
    )
    _implementation_owner_cache: ClassVar[
        ContextVar[
            t.MutableMappingKV[t.VariadicTuple[str], t.Infra.RopeImplementationPaths]
            | None
        ]
    ] = ContextVar("codemod_implementation_owner_cache", default=None)
    _closed_walk_cache: ClassVar[
        ContextVar[
            t.Triple[
                p.Infra.RopeProject,
                m.Infra.CodemodBindingSnapshot,
                t.Infra.CodemodImportWalkMemo,
            ]
            | None
        ]
    ] = ContextVar("codemod_closed_walk_cache", default=None)
    _class_stem_context: ClassVar[
        ContextVar[
            t.Triple[
                p.Infra.RopeProject,
                t.MutableMappingKV[Path, m.Infra.RopeProjectLayout | None],
                t.MutableMappingKV[str, m.Infra.CodegenPhaseAnalysis],
            ]
            | None
        ]
    ] = ContextVar("codemod_class_stem_context", default=None)
    # Declared import targets are a pure function of source bytes: one parse
    # per content digest serves every capture and rule closure of the process.
    _import_targets: ClassVar[
        t.MutableMappingKV[str, t.VariadicTuple[t.Pair[str | None, t.StrSequence]]]
    ] = {}

    @classmethod
    def project_import_graph(
        cls,
        root: Path,
    ) -> t.Pair[t.MappingKV[str, frozenset[str]], t.MappingKV[Path, str]]:
        """Return the runtime import graph and the module name of each file.

        Edges come from Rope's module-level import table, which leaves
        ``if TYPE_CHECKING:`` imports and function-local imports out: only
        imports that run when the module loads can form a cycle. Each target
        is truncated to the longest module the project defines.

        Live nodes use the workspace indexer's governed inventory, not Rope's
        recursive checkout enumeration. Declared members retain their import
        roots; unrelated checkouts and managed projections are not graph nodes.

        Returns:
            The runtime import graph and the module name of each file.

        """
        resolved = root.resolve()
        with FlextInfraUtilitiesRopeCore.open_project(
            resolved,
            project_roots=FlextInfraUtilitiesProjectDiscovery.governed_project_roots(
                resolved,
            ),
        ) as project:
            resources = tuple(
                FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(
                    project.get_resource(path.relative_to(resolved).as_posix()),
                    path,
                )
                for path in (
                    FlextInfraUtilitiesRopeAnalysisWorkspace.python_and_stub_file_paths(
                        project,
                        resolved,
                    )
                )
                if path.suffix == c.Infra.EXT_PYTHON
            )
            return cls.snapshot_import_graph(project, resources=resources)

    @classmethod
    def snapshot_import_graph(
        cls,
        project: p.Infra.RopeProject,
        *,
        resources: t.SequenceOf[t.Infra.RopeFile] | None = None,
    ) -> t.Pair[t.MappingKV[str, frozenset[str]], t.MappingKV[Path, str]]:
        """Read runtime imports from an immutable proposed-source Rope graph.

        A live caller supplies governed resources. An authenticated candidate
        elects its complete native Python source scope before constructing
        resources; provider receipts do not enlarge that scope. An immutable
        snapshot keeps its captured inventory, including proposed virtual modules.

        Returns:
            The resulting ``t.Pair[t.MappingKV[str, frozenset[str]], t.MappingKV[Path,
                str]]``.

        Raises:
            ValueError: If rope could not name module.

        """
        raw: MutableMapping[str, set[str]] = {}
        modules: MutableMapping[Path, str] = {}
        aliases: MutableMapping[str, str] = {}
        cls.codemod_progress("import graph start")
        due = 0.0
        for resource in (
            FlextInfraUtilitiesRopeCore.python_resources(project)
            if resources is None
            else resources
        ):
            due = cls.codemod_progress(
                f"import graph modules={len(modules)} file={resource.path}",
                due,
            )
            pymodule = FlextInfraUtilitiesRopeCore.resolve_pymodule(project, resource)
            name = pymodule.get_name()
            if not name:
                msg = f"rope could not name module {resource.path}"
                raise ValueError(msg)
            path = Path(resource.real_path).resolve()
            modules[path] = name
            package = name if path.name == c.Infra.INIT_PY else name.rpartition(".")[0]
            raw[name] = set(
                FlextInfraUtilitiesRopeImports.imported_module_paths(
                    FlextInfraUtilitiesRopeCore.resolve_module_imports(
                        project,
                        resource,
                    ),
                    current_package=package,
                ),
            )
            # Requesting a lazy export loads its elected provider module. Merely
            # installing the map does not load every provider in the package.
            provider_aliases = (
                FlextInfraUtilitiesRopeSourceBasesAliases.lazy_module_aliases(
                    name,
                    path,
                    resource.read(),
                    project=project,
                    pymodule=pymodule,
                )
            )
            aliases.update({
                f"{name}.{export}": provider
                for export, provider in provider_aliases.items()
            })
        known = frozenset(raw)
        cls.codemod_progress(f"import graph finish modules={len(modules)}")
        graph = {
            name: frozenset(
                target
                for imported in targets
                if (target := cls._known_prefix(aliases.get(imported, imported), known))
                is not None
                and target != name
            )
            for name, targets in raw.items()
        }
        return graph, modules

    @staticmethod
    def project_import_cycles(
        graph: t.MappingKV[str, frozenset[str]],
    ) -> t.MappingKV[str, frozenset[str]]:
        """Map each module in a runtime import cycle to its cycle's members.

        Returns:
            The resulting ``t.MappingKV[str, frozenset[str]]``.

        """
        cycles: MutableMapping[str, frozenset[str]] = {}
        for component in FlextInfraUtilitiesBase.strongly_connected_components({
            name: set(targets) for name, targets in graph.items()
        }):
            members = frozenset(component)
            if len(members) > 1:
                cycles.update(dict.fromkeys(members, members))
        return cycles

    @classmethod
    def import_closes_cycle(
        cls,
        root: Path,
        file_path: Path,
        imported: str,
        name: str | None,
        facts: m.Infra.CodemodProjectFacts,
    ) -> bool:
        """Return whether one import of ``file_path`` is an edge of a cycle.

        ``imported`` is the import's module as written (relative dots
        included); ``name`` is the imported name of a from-import, which is
        itself a module when the statement imports a submodule.

        Returns:
            Whether one import of ``file_path`` is an edge of a cycle.

        Raises:
            ValueError: If a production module under the package source root is
                absent from the project import graph.

        """
        graph, modules = facts.import_graph, facts.import_modules
        source = modules.get(file_path.resolve())
        if source is None:
            layout = FlextInfraUtilitiesCodegenNamespace.layout(root)
            # Project-level files and trees the source scan already ignores
            # (codegen ``source_scan_ignored``, including ``legado``) have no
            # import-graph node. They are not missing production modules, so
            # an import in one cannot close a cycle of the scanned graph.
            if (
                layout is not None
                and file_path.is_relative_to(layout.src_dir)
                and not FlextInfraUtilitiesIterationDirectory.source_scan_ignored_path(
                    root.resolve(), file_path.resolve()
                )
            ):
                msg = (
                    f"source module is absent from the project import graph: "
                    f"{file_path}"
                )
                raise ValueError(msg)
            return False
        package = (
            source if file_path.name == c.Infra.INIT_PY else source.rpartition(".")[0]
        )
        level = len(imported) - len(imported.lstrip("."))
        absolute = (
            FlextInfraUtilitiesRopeAnalysisImportState.resolve_import_module(
                current_package=package,
                module_name=imported.lstrip("."),
                level=level,
            )
            if level
            else imported
        ) or package
        known = frozenset(graph)
        candidates = (f"{absolute}.{name}", absolute) if name else (absolute,)
        target = next(
            (
                found
                for candidate in candidates
                if (found := cls._known_prefix(candidate, known)) is not None
            ),
            None,
        )
        members = facts.import_cycles.get(source, frozenset())
        return target is not None and target != source and target in members

    @classmethod
    def composes_family_package(cls, facade_file: Path, namespace: str) -> bool:
        """Return whether ``namespace`` in a facade module composes its family.

        The family package of ``<pkg>/<stem>.py`` is ``<pkg>/_<stem>/``. Every
        class a module of that package declares in its ``__all__`` must be
        reachable through the bases of the facade's ``namespace`` class,
        following the bases each package class declares. A facade without a
        family package composes nothing and holds.

        Returns:
            Whether ``namespace`` in a facade module composes its family.

        """
        package = facade_file.parent / f"_{facade_file.stem}"
        if not package.is_dir():
            return True
        bases_by_class: MutableMapping[str, t.StrSequence] = {}
        exported: set[str] = set()
        for module in sorted(package.rglob(f"*{c.Infra.EXT_PYTHON}")):
            if module.name == c.Infra.INIT_PY:
                continue
            source = module.read_text(encoding=c.DEFAULT_ENCODING)
            declared = frozenset(
                FlextInfraUtilitiesRopeAnalysisExports.public_export_names_source(
                    source,
                ),
            )
            for (
                info
            ) in FlextInfraUtilitiesRopeAnalysisAstHelpers.class_info_from_source(
                source,
            ):
                bases_by_class[info.name] = tuple(info.bases)
                if info.name in declared:
                    exported.add(info.name)
        pending = list(cls._nested_class_bases(facade_file, namespace))
        reached: set[str] = set()
        while pending:
            name = pending.pop()
            if name in reached:
                continue
            reached.add(name)
            pending.extend(bases_by_class.get(name, ()))
        return exported <= reached

    @staticmethod
    def _nested_class_bases(facade_file: Path, namespace: str) -> t.StrSequence:
        """Return the base names of class ``namespace`` nested in the facade.

        Returns:
            The base names of class ``namespace`` nested in the facade.

        Raises:
            ValueError: If class.

        """
        tree = FlextInfraUtilitiesRopeAnalysisAstHelpers.parse_string_module(
            facade_file.read_text(encoding=c.DEFAULT_ENCODING),
        ).get_ast()
        for node in FlextInfraUtilitiesRopeAnalysisAstHelpers.walk_ast_nodes(tree):
            if (
                FlextInfraUtilitiesRopeAnalysisAstHelpers.node_kind(node) == "ClassDef"
                and getattr(node, "name", "") == namespace
            ):
                return tuple(
                    name
                    for base in getattr(node, "bases", ()) or ()
                    if (
                        name
                        := FlextInfraUtilitiesRopeAnalysisAstHelpers.class_base_name(
                            base,
                        )
                    )
                )
        msg = f"class {namespace} is not declared in {facade_file}"
        raise ValueError(msg)

    @classmethod
    def codemod_project_facts(
        cls,
        root: Path,
        rules: t.SequenceOf[m.Infra.CodemodRule],
    ) -> m.Infra.CodemodProjectFacts:
        """Build the project facts one admission pass needs, from the tree now.

        Only the facts the rules' predicates ask for are built: the import
        graph and cycles for ``import-cycle``, the runtime closure for the
        runtime and facade package predicates.

        Returns:
            The project facts for the predicates of ``rules``.

        """
        predicates = frozenset(
            condition.predicate for rule in rules for condition in rule.context
        )
        resolved = root.resolve()
        graph: t.MappingKV[str, frozenset[str]] = {}
        modules: t.MappingKV[Path, str] = {}
        if c.Infra.CodemodContextPredicate.IMPORT_CYCLE in predicates:
            graph, modules = cls.project_import_graph(resolved)
        binding_rule_ids, binding_modules = cls.codemod_binding_requirements(rules)
        return m.Infra.CodemodProjectFacts(
            own_package=(
                FlextInfraUtilitiesPyproject.project_package_name(resolved)
                if predicates & c.Infra.CODEMOD_PACKAGE_CONTEXT_PREDICATES
                else None
            ),
            predicates=predicates,
            binding_rule_ids=binding_rule_ids,
            binding_modules=binding_modules,
            import_graph=graph,
            import_modules=modules,
            import_cycles=cls.project_import_cycles(graph),
            runtime_modules=(
                cls._runtime_modules(resolved)
                if predicates & c.Infra.CODEMOD_RUNTIME_CLOSURE_PREDICATES
                else frozenset()
            ),
        )

    @staticmethod
    def codemod_source_path(root: Path, file_path: Path) -> Path:
        """Resolve one finding file path against its project root.

        Returns:
            The absolute source path of the finding.

        """
        candidate = file_path if file_path.is_absolute() else root / file_path
        return (
            candidate.parent.resolve() / candidate.name
            if candidate.suffix == ".pyi"
            else candidate.resolve()
        )

    @staticmethod
    def codemod_binding_requirements(
        rules: t.SequenceOf[m.Infra.CodemodRule],
    ) -> t.Pair[frozenset[str], t.StrSequence]:
        """Elect binding inputs only for the rules that actually found code.

        Returns:
            Rule identities requiring inference and their declared symbol owners.

        """
        predicates = {
            c.Infra.CodemodContextPredicate.DECLARATION_DECORATOR,
            c.Infra.CodemodContextPredicate.MEMBER_RELOCATION,
            c.Infra.CodemodContextPredicate.RESOLVED_SYMBOL,
            c.Infra.CodemodContextPredicate.EMITTED_SYMBOL,
            c.Infra.CodemodContextPredicate.GENERIC_SPECIALIZATION,
            c.Infra.CodemodContextPredicate.SAME_BINDING,
            c.Infra.CodemodContextPredicate.EXECUTABLE_OCCURRENCE,
            c.Infra.CodemodContextPredicate.UNREFERENCED_IMPORT,
            c.Infra.CodemodContextPredicate.PAYLOAD_DECLARATION,
            c.Infra.CodemodContextPredicate.PROTOCOL_DECLARATION,
            c.Infra.CodemodContextPredicate.LAYER_ZERO_FILE,
            c.Infra.CodemodContextPredicate.LATER_LAYER,
            c.Infra.CodemodContextPredicate.IMPLEMENTATION_OWNER,
            c.Infra.CodemodContextPredicate.ISOLATED_EXECUTION,
            c.Infra.CodemodContextPredicate.CANONICAL_STATIC_PUBLICATION,
        }
        selected = tuple(
            rule
            for rule in rules
            if any(condition.predicate in predicates for condition in rule.context)
        )
        modules = tuple(
            dict.fromkeys(
                condition.arg[
                    1
                    if condition.predicate
                    is c.Infra.CodemodContextPredicate.EMITTED_SYMBOL
                    else 0
                ]
                for rule in selected
                for condition in rule.context
                if condition.predicate
                in {
                    c.Infra.CodemodContextPredicate.DECLARATION_DECORATOR,
                    c.Infra.CodemodContextPredicate.RESOLVED_SYMBOL,
                    c.Infra.CodemodContextPredicate.EMITTED_SYMBOL,
                    c.Infra.CodemodContextPredicate.IMPLEMENTATION_OWNER,
                    c.Infra.CodemodContextPredicate.ISOLATED_EXECUTION,
                }
            ),
        )
        modules = tuple(
            dict.fromkeys((
                *modules,
                *(
                    module
                    for rule in selected
                    for condition in rule.context
                    if (
                        condition.predicate
                        is c.Infra.CodemodContextPredicate.MEMBER_RELOCATION
                    )
                    for module in (condition.arg[0], condition.arg[3])
                ),
            ))
        )
        return frozenset(rule.id for rule in selected), modules

    @classmethod
    def codemod_path_findings(
        cls,
        root: Path,
        paths: t.SequenceOf[Path],
        rules: t.SequenceOf[m.Infra.CodemodRule],
    ) -> t.VariadicTuple[m.Infra.AstGrepOwnedPathDiagnostic]:
        """Admit owned-path policy from the shared inventory, without parsing bytes.

        Returns:
            Detection-only records for the same rule and authenticated report route.

        """
        return tuple(
            m.Infra.AstGrepOwnedPathDiagnostic.model_validate({
                "file": path.relative_to(root.resolve()).as_posix(),
                "ruleId": rule.id,
                "severity": "error",
                "message": rule.message,
                "origin": "owned-path",
                "text": "",
                "lines": "",
                "range": {
                    "start": {"line": 0, "column": 0},
                    "end": {"line": 0, "column": 0},
                    "byteOffset": {"start": 0, "end": 0},
                },
            })
            for path in paths
            for rule in rules
            if rule.owned_path_suffix is not None
            and path.suffix == rule.owned_path_suffix
        )

    @classmethod
    def codemod_context_admits(
        cls,
        admission: m.Infra.CodemodAdmission,
        *,
        project: p.Infra.RopeProject | None = None,
        sources: t.MappingKV[Path, str] | None = None,
    ) -> bool:
        """Return whether one finding satisfies its rule's project context.

        ``admission.captures`` maps each metavariable of the finding to its
        ast-grep single capture (``{"text": ...}``) or transformed value (a
        string). A declared variable the finding did not capture is a rule
        defect and raises; the syntactic match alone never stands in for it.

        ``admission.facts`` is the admission pass's project snapshot; it must
        have been built for every predicate the rule names. Missing facts raise
        ValueError at the snapshot validation boundary.

        Returns:
            Whether one finding satisfies its rule's project context.

        """
        root = admission.root
        rule = admission.rule
        captures = admission.captures
        facts = admission.facts
        cls._require_context_facts(admission)
        if rule.owned_path_suffix is not None:
            return admission.file_path.suffix == rule.owned_path_suffix
        source = cls.codemod_source_path(root, admission.file_path)
        for condition in rule.context:
            # Alternative syntax branches bind only their own metavariables.
            # This also applies before native declaration/binding evaluation.
            if condition.variable not in captures:
                continue
            native = cls._native_context_holds(
                admission, condition, source, project, sources
            )
            if native is not None:
                if native is not condition.holds:
                    return False
                continue
            if condition.predicate in {
                c.Infra.CodemodContextPredicate.DECLARATION_DECORATOR,
                c.Infra.CodemodContextPredicate.RESOLVED_SYMBOL,
                c.Infra.CodemodContextPredicate.MEMBER_RELOCATION,
                c.Infra.CodemodContextPredicate.EMITTED_SYMBOL,
                c.Infra.CodemodContextPredicate.SAME_BINDING,
                c.Infra.CodemodContextPredicate.GENERIC_SPECIALIZATION,
                c.Infra.CodemodContextPredicate.EXECUTABLE_OCCURRENCE,
                c.Infra.CodemodContextPredicate.UNREFERENCED_IMPORT,
            }:
                if (
                    cls._binding_condition_admits(
                        admission, condition, source, project, sources
                    )
                    is not condition.holds
                ):
                    return False
                continue
            value = cls._captured_text(rule, condition.variable, captures, source)
            of = (
                cls._captured_text(rule, condition.of, captures, source)
                if condition.of is not None and condition.of in captures
                else None
            )
            holds = cls._context_holds(
                root.resolve(),
                condition,
                (value, of),
                source,
                facts,
            )
            if holds is not condition.holds:
                return False
        return True

    @staticmethod
    def _require_context_facts(admission: m.Infra.CodemodAdmission) -> None:
        """Require the pass snapshot to cover every configured predicate.

        Raises:
            ValueError: If a rule predicate has no project facts.

        """
        missing = {
            condition.predicate for condition in admission.rule.context
        } - admission.facts.predicates
        if missing:
            msg = (
                f"{admission.rule.id}: project facts were not built for predicates "
                f"{sorted(missing)}"
            )
            raise ValueError(msg)

    @classmethod
    def _native_context_holds(
        cls,
        admission: m.Infra.CodemodAdmission,
        condition: m.Infra.CodemodContextCondition,
        source: Path,
        project: p.Infra.RopeProject | None,
        sources: t.MappingKV[Path, str] | None,
    ) -> bool | None:
        """Evaluate native execution and implementation predicates.

        Returns:
            The native verdict, or None for a different predicate.

        Raises:
            ValueError: If a native predicate lacks its original source epoch.

        """
        if condition.predicate in {
            c.Infra.CodemodContextPredicate.PAYLOAD_DECLARATION,
            c.Infra.CodemodContextPredicate.PROTOCOL_DECLARATION,
        }:
            return cls._declaration_condition_admits(
                admission, condition, source, project, sources
            )
        if (
            condition.predicate is c.Infra.CodemodContextPredicate.LATER_LAYER
            and project is not None
            and sources is not None
        ):
            return cls._later_layer(
                admission.root,
                source,
                cls._captured_text(
                    admission.rule, condition.variable, admission.captures, source
                ),
                condition,
                binding=(project, sources),
            )
        if (
            condition.predicate is c.Infra.CodemodContextPredicate.LAYER_ZERO_FILE
            and project is not None
        ):
            return cls._layer_zero_context(admission, source, project, sources)
        messages = {
            c.Infra.CodemodContextPredicate.CANONICAL_STATIC_PUBLICATION: (
                f"{admission.rule.id}: static publication requires its native epoch"
            ),
            c.Infra.CodemodContextPredicate.ISOLATED_EXECUTION: (
                f"{admission.rule.id}: execution context requires its "
                "original native epoch"
            ),
            c.Infra.CodemodContextPredicate.IMPLEMENTATION_OWNER: (
                f"{admission.rule.id}: implementation context requires its native epoch"
            ),
        }
        if condition.predicate not in messages:
            return None
        if (
            admission.snapshot is None
            or project is None
            or sources is None
            or source not in sources
        ):
            raise ValueError(messages[condition.predicate])
        if condition.predicate in {
            c.Infra.CodemodContextPredicate.ISOLATED_EXECUTION,
            c.Infra.CodemodContextPredicate.CANONICAL_STATIC_PUBLICATION,
        }:
            return (
                cls._isolated_execution_holds(project, condition, source, sources)
                if condition.predicate
                is c.Infra.CodemodContextPredicate.ISOLATED_EXECUTION
                else cls._canonical_static_publication(
                    admission, condition, source, project, sources
                )
            )
        # One epoch owns one implementation closure per primitive, for every finding.
        cached = cls._implementation_owner_cache.get()
        owners: t.MutableMappingKV[
            t.VariadicTuple[str], t.Infra.RopeImplementationPaths
        ] = {} if cached is None else cached
        key = tuple(condition.arg)
        if key not in owners:
            owners[key] = cls.implementation_owner_modules(project, condition, sources)
        return source in owners[key]

    @classmethod
    def _static_publication_module(
        cls,
        admission: m.Infra.CodemodAdmission,
        source: Path,
        project: p.Infra.RopeProject,
        sources: t.MappingKV[Path, str],
    ) -> p.Infra.RopePyModule:
        """Resolve a source module only in its original authenticated project epoch.

        Returns:
            The original native source module, without reopening a live substitute.

        Raises:
            ValueError: The capture, source graph, and original snapshot disagree.

        """
        snapshot = admission.snapshot
        if (
            snapshot is None
            or Path(project.root.real_path).resolve() != admission.root.resolve()
        ):
            msg = "static publication requires its original snapshot and project"
            raise ValueError(msg)
        content = sources[source]
        original = next((row for row in snapshot.states if row.path == source), None)
        resource = FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(
            project.get_resource(
                source.relative_to(admission.root.resolve()).as_posix()
            ),
            source,
        )
        module = FlextInfraUtilitiesRopeCore.resolve_pymodule(project, resource)
        if (
            original is None
            or original.content != content.encode("utf-8")
            or module.source_code != content
        ):
            msg = f"static publication differs from its original native epoch: {source}"
            raise ValueError(msg)
        return module

    @classmethod
    def _canonical_static_publication(
        cls,
        admission: m.Infra.CodemodAdmission,
        condition: m.Infra.CodemodContextCondition,
        source: Path,
        project: p.Infra.RopeProject,
        sources: t.MappingKV[Path, str],
    ) -> bool:
        """Prove a generated root's static alias agrees with its native publisher.

        Returns:
            Whether the captured import is the canonical static publication.

        Raises:
            ValueError: The required provider capture is missing.

        """
        module = cls._static_publication_module(admission, source, project, sources)
        content = module.source_code
        capture = m.Infra.AstGrepCapture.model_validate(
            admission.captures[condition.variable]
        )
        span = cls._validated_capture_span(source, capture, content.encode("utf-8"))
        if condition.of is None:
            msg = "static publication requires its provider capture"
            raise ValueError(msg)
        provider = cls._captured_text(
            admission.rule, condition.of, admission.captures, source
        )
        layout = FlextInfraUtilitiesCodegenNamespace.layout(
            admission.root, rope_project=project
        )
        if (
            layout is None
            or source != layout.init_path
            or FlextInfraUtilitiesCodegenFilePlan.codegen_initializer_is_authored(
                content.encode("utf-8")
            )
            or provider.rpartition(".")[0] != layout.package_name
            or capture.text
            not in (
                FlextInfraUtilitiesRopeAnalysisExports.public_export_names_source(
                    content
                )
            )
        ):
            return False
        routes = FlextInfraUtilitiesRopeSourceBasesAliases.lazy_export_bindings(
            layout.package_name, source, content, project=project, pymodule=module
        )
        route = routes.get(capture.text)
        if route is None or (
            route.target != provider or route.attributes != (capture.text,)
        ):
            return False
        declared_resource = project.find_module(provider)
        if declared_resource is None:
            return False
        provider_path = FlextInfraUtilitiesRopeCore.resource_file_path(
            project, declared_resource
        )
        if (
            provider_path is None
            or provider_path.parent != layout.package_dir
            or provider_path.suffix != c.Infra.EXT_PYTHON
            or provider_path not in sources
        ):
            return False
        cls._static_publication_module(admission, provider_path, project, sources)
        policy = FlextInfraUtilitiesCodegenNamespace.publication_policy(
            provider_path,
            rope_project=project,
            project_layout=layout,
            current_pkg=layout.package_name,
        )
        if (
            policy.expected_alias != capture.text
            or not policy.include_in_lazy_init
            or not policy.export_symbols
        ):
            return False
        scope = module.get_scope()
        return (
            cls._static_publication_native_import(
                project, module, (provider, capture.text), (span[1], span[2])
            )
            and cls.stable_binding_chain(
                (project, module, scope), capture.text, len(content), sources
            )
            and cls._binding_symbols_match(
                cls.resolve_declared_binding(
                    project,
                    layout.package_name,
                    capture.text,
                    admission.root.resolve(),
                    sources,
                ),
                FlextInfraUtilitiesRopeRuntimeModules.expression_name(
                    scope, capture.text
                ),
            )
        )

    @classmethod
    def _static_publication_native_import(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        imported: t.StrPair,
        span: t.Pair[int, int],
    ) -> bool:
        """Require the real module guard and installer, not same-spelled locals.

        Returns:
            Whether a static import and the sole native installer share this root.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        content = module.source_code
        start, end = span
        rows = FlextInfraUtilitiesRopeStructure.logical_statements(content)
        imports = tuple(
            row
            for row in rows
            if (
                row.start_offset <= start < end <= row.end_offset
                and row.enclosing_kind == c.Infra.RopeScopeKind.MODULE
                and row.category == c.Infra.StatementCategory.FROM_IMPORT
                and row.type_checking_guarded
            )
        )
        if len(imports) != 1:
            return False
        tree = module.get_ast()
        if not isinstance(tree, ast.Module):
            return False
        scope = module.get_scope()
        expected_guard = runtime.qualified_name(
            project, "TYPE_CHECKING", module_name="typing"
        )
        expected_installer = runtime.qualified_name(
            project, "install_lazy_exports", module_name=c.Infra.LAZY_BOOTSTRAP_MODULE
        )
        guards = tuple(
            node
            for node in tree.body
            if isinstance(node, ast.If)
            and any(
                isinstance(statement, ast.ImportFrom)
                and statement.lineno == imports[0].line
                and statement.module == imported[0]
                and statement.level == 0
                and any(
                    alias.name == imported[1] and alias.asname in {None, imported[1]}
                    for alias in statement.names
                )
                for statement in node.body
            )
        )
        if len(guards) != 1:
            return False
        guard = guards[0].test
        if isinstance(guard, ast.Compare) and (
            len(guard.ops) == len(guard.comparators) == 1
            and isinstance(guard.ops[0], ast.Is)
            and isinstance(guard.comparators[0], ast.Constant)
            and guard.comparators[0].value is True
        ):
            guard = guard.left
        if not isinstance(guard, ast.Name) or not (
            cls._binding_symbols_match(
                expected_guard, runtime.resolve_symbol(scope, guard)
            )
            and cls.single_reaching_binding(
                module,
                scope,
                guard.id,
                len(content),
            )
        ):
            return False
        installers = tuple(
            call
            for node in tree.body
            if isinstance(node, ast.Expr | ast.Assign | ast.AnnAssign)
            for call in (
                node.value.value
                if isinstance(node.value, ast.Subscript)
                else node.value,
            )
            if isinstance(call, ast.Call)
            and cls._binding_symbols_match(
                expected_installer, runtime.resolve_symbol(scope, call.func)
            )
        )
        return len(installers) == 1 and cls.single_reaching_binding(
            module,
            scope,
            ast.unparse(installers[0].func).split(".")[0],
            len(content),
        )

    @staticmethod
    def _layer_zero_context(
        admission: m.Infra.CodemodAdmission,
        source: Path,
        project: p.Infra.RopeProject,
        sources: t.MappingKV[Path, str] | None,
    ) -> bool:
        """Resolve a layer-zero predicate from its captured native module.

        Returns:
            Whether the captured module has the layer-zero role.

        Raises:
            ValueError: If the captured source epoch is missing.

        """
        if admission.snapshot is None or sources is None or source not in sources:
            msg = (
                f"{admission.rule.id}: layer-zero context requires its captured source"
            )
            raise ValueError(msg)
        resource = FlextInfraUtilitiesRopeRuntimeTypes.require_file_resource(
            project.get_resource(
                source.relative_to(admission.root.resolve()).as_posix()
            ),
            source,
        )
        module = FlextInfraUtilitiesRopeCore.resolve_pymodule(project, resource)
        return (
            FlextInfraUtilitiesImportLaw.import_source_role(project, module, source)
            == "layer0"
        )

    @classmethod
    def _isolated_execution_holds(
        cls,
        project: p.Infra.RopeProject,
        condition: p.Infra.CodemodContextOperands,
        source: Path,
        sources: t.MappingKV[Path, str],
    ) -> bool:
        """Read execution metadata at its original native command producer.

        The entrypoint is a native class's declaring module, not a filename
        exemption. Only that exact captured resource can carry the role; its
        original imports must satisfy the declared no-site, stdlib-only contract.

        Returns:
            Whether the isolated-execution condition holds.

        Raises:
            TypeError: When the producer module has no supported Python AST.
            ValueError: When the condition argument shape is wrong, the
                producer is not a native source callable, lies outside the
                captured epoch, or declares an invalid entrypoint identity.

        """
        if len(condition.arg) != c.Infra.PAIRED_CONTEXT_PREDICATE_ARG_COUNT:
            msg = "isolated-execution requires a module and native invocation producer"
            raise ValueError(msg)
        module_name, expression = condition.arg
        producer = cls._execution_producer(project, module_name, expression)
        if producer is None:
            return False
        module, scope = producer
        resource = module.get_resource()
        if resource is None or Path(resource.real_path) not in sources:
            msg = "execution metadata producer is outside the captured epoch"
            raise ValueError(msg)
        tree = module.get_ast()
        if not isinstance(tree, ast.AST):
            msg = "execution metadata producer has no supported Python AST"
            raise TypeError(msg)
        found = False
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not (
                scope.get_body_start() <= node.lineno <= scope.get_end()
            ):
                continue
            target_path = cls._execution_entrypoint(
                project, module, scope, node, sources
            )
            if target_path == source:
                found = True
        if not found:
            return False
        return cls._isolated_imports_hold(sources[source])

    @staticmethod
    def _execution_producer(
        project: p.Infra.RopeProject, module_name: str, expression: str
    ) -> t.Pair[p.Infra.RopeSourceModule, p.Infra.RopeScope] | None:
        """Elect an advertised native invocation producer without a live fallback.

        Returns:
            Its original module and lexical scope, or no unelected provider.

        Raises:
            ValueError: An elected producer lacks the required source capabilities.

        """
        if project.find_module(module_name) is None:
            return None
        producer = FlextInfraUtilitiesRopeRuntimeModules.qualified_name(
            project, expression, module_name=module_name
        ).get_object()
        if not FlextInfraUtilitiesRopeRuntimeTypes.py_function(producer):
            msg = "execution metadata producer is not a native source callable"
            raise ValueError(msg)
        module = producer.get_module()
        scope = producer.get_scope()
        if not FlextInfraUtilitiesRopeRuntimeTypes.source_module(module):
            msg = "execution metadata producer is not a native source callable"
            raise ValueError(msg)
        return module, scope

    @staticmethod
    def _isolated_imports_hold(source: str) -> bool:
        """Prove the selected entrypoint's imports require only the native stdlib.

        Returns:
            Whether every import satisfies the existing isolated-execution contract.

        """
        imports = ast.walk(ast.parse(source))
        return all(
            all(
                alias.name.partition(".")[0] in sys.stdlib_module_names
                for alias in node.names
            )
            if isinstance(node, ast.Import)
            else node.level == 0
            and (node.module or "").partition(".")[0] in sys.stdlib_module_names
            for node in imports
            if isinstance(node, ast.Import | ast.ImportFrom)
        )

    @classmethod
    def _execution_entrypoint(
        cls,
        project: p.Infra.RopeProject,
        module: p.Infra.RopePyModule,
        scope: p.Infra.RopeScope,
        node: ast.Call,
        sources: t.MappingKV[Path, str],
    ) -> Path | None:
        """Resolve one native execution metadata constructor's entrypoint.

        Returns:
            Its source path, or None for an unrelated constructor.

        Raises:
            ValueError: If the metadata or its entrypoint identity is invalid.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        types = FlextInfraUtilitiesRopeRuntimeTypes
        fields = {keyword.arg: keyword.value for keyword in node.keywords}
        if set(fields) != set(m.Cli.PythonScriptExecution.model_fields):
            return None
        position = runtime.source_offset(module.source_code, node.func)
        lexical = runtime.scope_at(module, position)
        if lexical is not scope:
            return None
        constructor = runtime.resolve_symbol(lexical, node.func)
        if constructor is None or not types.py_class(constructor.get_object()):
            return None
        contract = m.Cli.PythonScriptExecution
        expected = runtime.qualified_name(
            project, contract.__qualname__, module_name=contract.__module__
        )
        if not cls._binding_symbols_match(expected, constructor):
            return None
        entry, role = fields["module"], fields["role"]
        if not (
            isinstance(entry, ast.Attribute)
            and entry.attr == "__module__"
            and isinstance(role, ast.Constant)
            and isinstance(role.value, str)
        ):
            msg = (
                "execution metadata requires native entrypoint identity "
                "and its declared role"
            )
            raise ValueError(msg)
        binding = runtime.resolve_symbol(lexical, entry.value)
        if binding is None or not types.py_class(binding.get_object()):
            msg = "execution entrypoint is not a native class declaration"
            raise ValueError(msg)
        target = binding.get_object().get_module()
        if target is None or (target_resource := target.get_resource()) is None:
            msg = "execution entrypoint has no original source resource"
            raise ValueError(msg)
        _ = m.Cli.PythonScriptExecution.model_validate(
            {"module": target.get_name(), "role": role.value},
        )
        target_path = Path(target_resource.real_path)
        if target_path not in sources:
            msg = f"execution entrypoint is outside the captured epoch: {target_path}"
            raise ValueError(msg)
        return target_path

    @classmethod
    def implementation_owner_modules(
        cls,
        project: p.Infra.RopeProject,
        condition: p.Infra.PrimitiveOwnerCondition,
        sources: t.MappingKV[t.Infra.RopeSourcePath, str],
    ) -> t.Infra.RopeImplementationPaths:
        """Derive a primitive's implementation from native definitions and MRO.

        Imported consumers do not enter this closure. Source-defined helper
        calls in the primitive's own namespace and actual declaring-class bases
        do; a same-spelled local symbol cannot substitute for a native owner.

        Returns:
            The declaring module paths of the implementation owner closure.

        Raises:
            ValueError: When the condition argument shape is wrong.

        """
        if len(condition.arg) != c.Infra.PAIRED_CONTEXT_PREDICATE_ARG_COUNT:
            msg = "implementation-owner requires a module and public primitive"
            raise ValueError(msg)
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        types = FlextInfraUtilitiesRopeRuntimeTypes
        module_name, expression = condition.arg
        primitive = runtime.qualified_name(
            project, expression, module_name=module_name
        ).get_object()
        if not types.py_function(primitive):
            msg = (
                "implementation owner is not a source callable: "
                f"{module_name}.{expression}"
            )
            raise ValueError(msg)
        declaration = primitive.get_module()
        namespace = declaration.get_name().partition(".")[0]
        owners: set[Path] = set()
        visited: set[int] = set()
        pending: list[p.Infra.RopePyObject] = [primitive]
        while pending:
            target = pending.pop()
            if id(target) in visited:
                continue
            visited.add(id(target))
            discovered = cls._implementation_target(target, namespace, sources)
            if discovered is None:
                continue
            path, related = discovered
            owners.add(path)
            pending.extend(related)
        return frozenset(owners)

    @staticmethod
    def _implementation_target(
        target: p.Infra.RopePyObject,
        namespace: str,
        sources: t.MappingKV[Path, str],
    ) -> t.Pair[Path, list[p.Infra.RopePyObject]] | None:
        """Collect native implementation edges of one callable or class.

        Returns:
            The source path and related native declarations, when source-defined.

        Raises:
            ValueError: If its source is absent from the captured epoch.
            TypeError: If the module has no supported AST.

        """
        types = FlextInfraUtilitiesRopeRuntimeTypes
        pending: list[p.Infra.RopePyObject] = []
        if not (types.py_class(target) or types.py_function(target)):
            return None
        module = target.get_module()
        scope = target.get_scope()
        if not types.source_module(module):
            return None
        resource = module.get_resource()
        if resource is None:
            msg = "native implementation declaration has no source resource"
            raise ValueError(msg)
        path = Path(resource.real_path)
        if path not in sources:
            msg = f"native implementation source is outside the captured epoch: {path}"
            raise ValueError(msg)
        if types.py_class(target):
            pending.extend(
                base for base in target.get_superclasses() if types.py_class(base)
            )
            pending.extend(
                child.pyobject
                for child in scope.get_scopes()
                if child.get_kind()
                in {c.Infra.RopeScopeKind.FUNCTION, c.Infra.RopeScopeKind.CLASS}
            )
            return path, pending
        parent = scope.parent
        if parent is not None and parent.get_kind() == c.Infra.RopeScopeKind.CLASS:
            pending.append(parent.pyobject)
        tree = module.get_ast()
        if not isinstance(tree, ast.AST):
            msg = "native implementation module has no supported Python AST"
            raise TypeError(msg)
        pending.extend(
            FlextInfraUtilitiesCodemodProject._implementation_calls(
                module, scope, tree, sources[path], namespace
            )
        )
        return path, pending

    @staticmethod
    def _implementation_calls(
        module: p.Infra.RopePyModule,
        scope: p.Infra.RopeScope,
        tree: ast.AST,
        source: str,
        namespace: str,
    ) -> list[p.Infra.RopePyObject]:
        """Resolve same-namespace calls within one exact lexical scope.

        Returns:
            Native helper declarations reachable from calls in the scope.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        types = FlextInfraUtilitiesRopeRuntimeTypes
        pending: list[p.Infra.RopePyObject] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not (
                scope.get_body_start() <= node.lineno <= scope.get_end()
            ):
                continue
            offset = runtime.source_offset(source, node.func)
            lexical = runtime.scope_at(module, offset)
            if lexical is not scope:
                continue
            binding = runtime.resolve_symbol(lexical, node.func)
            if binding is None:
                continue
            helper = binding.get_object()
            provider = helper.get_module()
            if (
                (types.py_function(helper) or types.py_class(helper))
                and provider is not None
                and provider.get_name().partition(".")[0] == namespace
            ):
                pending.append(helper)
        return pending

    @classmethod
    def _declaration_condition_admits(
        cls,
        admission: m.Infra.CodemodAdmission,
        condition: m.Infra.CodemodContextCondition,
        source: Path,
        project: p.Infra.RopeProject | None,
        sources: t.MappingKV[Path, str] | None,
    ) -> bool:
        """Grade one declaration context condition against its payload project.

        Args:
            admission: The admission under evaluation.
            condition: The declaration predicate condition to grade.
            source: The resolved occurrence source path.
            project: The active Rope project of the admission.
            sources: The captured admission sources keyed by path.

        Returns:
            Whether the declaration condition holds for the finding.

        Raises:
            ValueError: If the declaration context lacks its binding snapshot.

        """
        rule = admission.rule
        if condition.variable not in admission.captures:
            return True
        if admission.snapshot is None or project is None or sources is None:
            msg = f"{rule.id}: declaration context requires its binding snapshot"
            raise ValueError(msg)
        capture = m.Infra.AstGrepCapture.model_validate(
            admission.captures[condition.variable],
        )
        _text, start, _end = cls._validated_capture_span(
            source,
            capture,
            sources[source].encode("utf-8"),
        )
        declarations = FlextInfraUtilitiesDeclarationPayload.declaration_names(
            project,
            source,
            capture.text,
            offset=start,
        )
        resolve = (
            FlextInfraUtilitiesDeclarationPayload.payload_declaration
            if condition.predicate
            is c.Infra.CodemodContextPredicate.PAYLOAD_DECLARATION
            else FlextInfraUtilitiesDeclarationPayload.protocol_declaration
        )
        return (
            len(declarations) == 1
            and resolve(
                project,
                source,
                declarations[0],
            )
            is not None
        )

    @classmethod
    def _binding_condition_admits(
        cls,
        admission: m.Infra.CodemodAdmission,
        condition: m.Infra.CodemodContextCondition,
        source: Path,
        project: p.Infra.RopeProject | None,
        sources: t.MappingKV[Path, str] | None,
    ) -> bool:
        """Grade one binding context condition against the active project.

        Args:
            admission: The admission under evaluation.
            condition: The binding predicate condition to grade.
            source: The resolved occurrence source path.
            project: The active Rope project of the admission.
            sources: The captured admission sources keyed by path.

        Returns:
            Whether the binding condition holds for the finding.

        Raises:
            ValueError: If the binding context lacks its snapshot or sources.

        """
        snapshot = admission.snapshot
        if snapshot is None or project is None or sources is None:
            msg = (
                f"{admission.rule.id}: binding context requires its captured snapshot "
                "and active project sources: "
                f"snapshot={snapshot is not None} "
                f"project={project is not None} sources={sources is not None}"
            )
            raise ValueError(msg)
        return cls._occurrence_binding_holds(
            (admission.root, source, project),
            condition,
            admission.captures,
            sources,
        )

    @staticmethod
    def codemod_source_epoch(
        snapshot: m.Infra.CodemodBindingSnapshot,
    ) -> m.Infra.CodemodSourceEpoch:
        """Decode each captured source once for the complete selected-project pass.

        Args:
            snapshot: The binding snapshot whose captured states are decoded.

        Returns:
            The immutable capture epoch shared by the complete pass.

        """
        contents = {
            state.path: state.content
            for state in snapshot.states
            if state.content is not None
        }
        return m.Infra.CodemodSourceEpoch(
            snapshot=snapshot,
            sources=MappingProxyType({
                path: content.decode("utf-8") for path, content in contents.items()
            }),
            contents=MappingProxyType(contents),
        )

    @classmethod
    def identity_source_epoch(
        cls,
        project: p.Infra.RopeProject,
        source_paths: t.SequenceOf[Path],
        identities: t.StrSequence,
    ) -> m.Infra.CodemodSourceEpoch:
        """Capture sources plus every module a resolved identity needs, once.

        A semantic planning snapshot is a closed inventory: an identity such as
        ``pydantic.BaseModel`` resolves only when its module closure was
        captured before planning. Every dotted prefix of each identity is
        offered; a prefix that is not a module resolves to nothing and captures
        nothing. The current native graph elects the desired import closure;
        file receipts retain the original physical preimages for authentication.

        Returns:
            The immutable epoch every snapshot of one planning pass shares.

        """
        modules = tuple(
            dict.fromkeys(
                ".".join(parts[:end])
                for parts in (identity.split(".") for identity in identities)
                for end in range(1, len(parts) + 1)
            )
        )
        selection = m.Infra.CodemodBindingProject(
            root=Path(project.root.real_path),
            source_paths=tuple(source_paths),
            modules=modules,
        )
        if not project.authenticated_sources:
            snapshot = cls.codemod_binding_snapshot(
                selection.root, projects=(selection,)
            )
        else:
            states = {state.path: state for state in project.consumed_source_states()}
            with project.source_consumption(), project.frozen_layout():
                cls._snapshot_project_imports(project, selection, states, ({}, {}))
            snapshot = m.Infra.CodemodBindingSnapshot(states=tuple(states.values()))
        return cls.codemod_source_epoch(snapshot)

    @classmethod
    @contextmanager
    def codemod_binding_project(
        cls,
        root: Path,
        epoch: m.Infra.CodemodSourceEpoch,
    ) -> Generator[t.Pair[p.Infra.RopeProject, t.MappingKV[Path, str]]]:
        """Own one immutable binding graph for the complete admission pass.

        Yields:
            The frozen Rope graph and its complete authenticated source closure.

        """
        sources = epoch.sources
        with (
            FlextInfraUtilitiesRopeCore.open_project(root) as live,
            closing(
                FlextInfraRopeProject.from_atomic_reads(
                    live,
                    (),
                    election=FlextInfraUtilitiesRopeRuntimeModules.native_election(
                        live
                    ),
                )
            ) as layout_project,
            closing(
                FlextInfraUtilitiesRopeRuntimeModules.snapshot_project(
                    live, sources, captured=epoch
                )
            ) as project,
            project.frozen_layout(),
        ):
            token = cls._type_payload_cache.set({})
            roles = cls._module_role_cache.set({})
            owners = cls._implementation_owner_cache.set({})
            walks = cls._closed_walk_cache.set((project, epoch.snapshot, ({}, {})))
            stems = cls._class_stem_context.set((
                FlextInfraUtilitiesCodegenFacades.require_source_project(
                    layout_project
                ),
                {},
                {},
            ))
            try:
                # The admission pass is the consumer of every layout read, so a
                # cached class-stem query replays its receipt into this scope.
                with (
                    layout_project.source_consumption(),
                    FlextInfraUtilitiesRopeRuntimeMatching.semantic_matching_context(),
                ):
                    yield project, sources
                layout_project.verify_source_states()
            finally:
                cls._class_stem_context.reset(stems)
                cls._closed_walk_cache.reset(walks)
                cls._implementation_owner_cache.reset(owners)
                cls._module_role_cache.reset(roles)
                cls._type_payload_cache.reset(token)

    @classmethod
    def codemod_binding_snapshot(
        cls,
        root: Path,
        source_states: tuple[m.Cli.AtomicFileState, ...] = (),
        modules: t.StrSequence = (),
        *,
        projects: t.SequenceOf[m.Infra.CodemodBindingProject] | None = None,
    ) -> m.Infra.CodemodBindingSnapshot:
        """Capture every selected project's owners once before inference.

        Each elected graph retains the same admitted dependency receipts.

        Args:
            root: The root path of the project to capture.
            source_states: A tuple of atomic file states representing the source files.
            modules: A sequence of module names to include in the snapshot.
            projects: An optional sequence of codemod binding projects to consider.

        Returns:
            The resulting ``m.Infra.CodemodBindingSnapshot``..

        """
        states: t.MutableMappingKV[Path, m.Cli.AtomicFileState] = {
            state.path.resolve(): state
            for state in m.Infra.CodemodBindingSnapshot(states=source_states).states
        }
        selections = (
            projects
            if projects is not None
            else (
                m.Infra.CodemodBindingProject(
                    root=root, source_paths=tuple(states), modules=modules
                ),
            )
        )
        for selection in selections:
            with (
                FlextInfraUtilitiesRopeCore.open_project(selection.root) as live,
                closing(
                    FlextInfraRopeProject.from_atomic_reads(
                        live,
                        tuple(states.values()),
                        election=FlextInfraUtilitiesRopeRuntimeModules.native_election(
                            live
                        ),
                    ),
                ) as project,
                project.frozen_layout(),
            ):
                cls._snapshot_project_imports(
                    FlextInfraUtilitiesCodegenFacades.require_source_project(project),
                    selection,
                    states,
                    ({}, {}),
                )
        return m.Infra.CodemodBindingSnapshot(states=tuple(states.values()))

    @classmethod
    def codemod_rule_binding_states(
        cls,
        project: p.Infra.RopeProject,
        snapshot: m.Infra.CodemodBindingSnapshot,
        selection: m.Infra.CodemodBindingProject,
    ) -> t.VariadicTuple[m.Cli.AtomicFileState]:
        """Select a rule's full import closure from its original closed epoch.

        Authentication ends at the rule's repository: supplier and dependency
        modules of the closure are read for inference, never authenticated.

        Returns:
            Original witnesses for the rule's sources and declared owners, without
            dependencies elected solely by another rule, inside the rule's
            repository.

        """
        states = {state.path: state for state in snapshot.states}
        # Every rule of one admission pass walks the same frozen graph: its
        # resolutions and module edges are shared, never rebuilt per rule.
        shared = cls._closed_walk_cache.get()
        memo: t.Infra.CodemodImportWalkMemo = (
            shared[2]
            if shared is not None and shared[0] is project and shared[1] is snapshot
            else ({}, {})
        )
        paths = cls._snapshot_project_imports(
            project, selection, states, memo, closed=True
        )
        repository = selection.root.resolve()
        return tuple(
            state
            for state in snapshot.states
            if state.path in paths and state.path.is_relative_to(repository)
        )

    @classmethod
    def _snapshot_project_imports(
        cls,
        project: p.Infra.RopeProject,
        selection: m.Infra.CodemodBindingProject,
        states: t.MutableMappingKV[Path, m.Cli.AtomicFileState],
        memo: t.Infra.CodemodImportWalkMemo,
        *,
        closed: bool = False,
    ) -> set[Path]:
        """Walk the same transitive import election for capture and rule ownership.

        Returns:
            Every visited Python source in the selected dependency closure.

        """
        lookup, nodes = memo
        pending = [
            project.get_resource(path.relative_to(selection.root.resolve()).as_posix())
            for path in selection.source_paths
        ]
        for name in dict.fromkeys(selection.modules):
            owner = cls._snapshot_imported_resource(
                project, project.root.parent, name, level=0, lookup=lookup
            )
            if owner is not None:
                pending.append(owner)
        scheduled = {resource.real_path for resource in pending}
        visited: set[Path] = set()
        while pending:
            resource = pending.pop()
            key = resource.real_path
            if key not in nodes:
                nodes[key] = cls._snapshot_module_imports(
                    project, states, resource, lookup, closed=closed
                )
            node = nodes[key]
            if node is None or node[0] in visited:
                continue
            visited.add(node[0])
            for target, imported in node[1]:
                if target not in scheduled:
                    scheduled.add(target)
                    pending.append(imported)
        return visited

    @classmethod
    def _snapshot_module_imports(
        cls,
        project: p.Infra.RopeProject,
        states: t.MutableMappingKV[Path, m.Cli.AtomicFileState],
        resource: t.Infra.RopeResource,
        lookup: t.Infra.RopeImportLookup,
        *,
        closed: bool = False,
    ) -> t.Infra.CodemodImportWalkNode:
        """Authenticate one module and resolve its declared import targets.

        Returns:
            The resolved path and each imported resource keyed by its real path,
            or ``None`` when the resource carries no governable Python source.

        Raises:
            TypeError: If binding package has no source resource contract.
            ValueError: If a closed binding dependency is outside its captured epoch.

        """
        path = Path(resource.real_path).resolve()
        if resource.is_folder():
            if not isinstance(resource, p.Infra.RopeRoot):
                msg = f"binding package has no source resource contract: {path}"
                raise TypeError(msg)
            # A package binds through its initializer; a compiled
            # extension's PEP 561 stub package binds through its
            # ``__init__.pyi``. Only a PEP 420 namespace portion, which
            # has neither, carries no module source to read.
            initializer = next(
                (
                    name
                    for name in (c.Infra.INIT_PY, c.Infra.INIT_PYI)
                    if resource.has_child(name)
                ),
                None,
            )
            if initializer is None:
                return None
            resource = resource.get_child(initializer)
            path = Path(resource.real_path).resolve()
        if not project.source_query(path, "isfile") or path.suffix not in {
            c.Infra.EXT_PYTHON,
            c.Infra.EXT_PYTHON_STUB,
        }:
            return None
        state = states.get(path)
        if state is None:
            if closed:
                msg = f"rule binding dependency is outside its captured epoch: {path}"
                raise ValueError(msg)
            state = project.source_state(path, required=False)
            states[path] = state
        source = project.source_text(path)
        digest = u.Cli.sha256_bytes(source.encode(c.DEFAULT_ENCODING))
        if digest not in cls._import_targets:
            cls._import_targets[digest] = (
                FlextInfraUtilitiesRopeImports.source_import_targets(
                    project, source, resource=resource
                )
            )
        return path, tuple(
            (imported.real_path, imported)
            for imported in cls._snapshot_import_resources(
                project, resource.parent, cls._import_targets[digest], lookup
            )
        )

    @classmethod
    def _snapshot_import_resources(
        cls,
        project: p.Infra.RopeProject,
        folder: p.Infra.RopeRoot,
        imports: t.VariadicTuple[t.Pair[str | None, t.StrSequence]],
        lookup: t.Infra.RopeImportLookup,
    ) -> list[t.Infra.RopeResource]:
        """Resolve native import targets through the shared resource cache.

        Returns:
            The pending resources named by the module's import statements.

        """
        found: list[t.Infra.RopeResource] = []
        for declared, names in imports:
            if declared is None:
                found.extend(
                    cls._snapshot_named_resources(project, folder, names, 0, lookup)
                )
                continue
            level = len(declared) - len(declared.lstrip("."))
            module_name = declared[level:]
            package = cls._snapshot_imported_resource(
                project, folder, module_name, level=level, lookup=lookup
            )
            if package is None:
                continue
            found.append(package)
            # ``from M import N`` names a submodule only when M is a package.
            if package.is_folder():
                found.extend(
                    cls._snapshot_named_resources(
                        project,
                        folder,
                        tuple(
                            f"{module_name}.{name}" if module_name else name
                            for name in names
                            if name != "*"
                        ),
                        level,
                        lookup,
                    )
                )
        return found

    @classmethod
    def _snapshot_named_resources(
        cls,
        project: p.Infra.RopeProject,
        folder: p.Infra.RopeRoot,
        names: t.StrSequence,
        level: int,
        lookup: t.Infra.RopeImportLookup,
    ) -> list[t.Infra.RopeResource]:
        """Resolve each imported name in one statement's search scope.

        Returns:
            The resources Rope finds for the names, in declaration order.

        """
        return [
            imported
            for name in names
            if (
                imported := cls._snapshot_imported_resource(
                    project, folder, name, level=level, lookup=lookup
                )
            )
            is not None
        ]

    @staticmethod
    def _regular_package(resource: t.Infra.RopeResource | None) -> bool:
        """Mirror Rope's election of a module or initializer-backed package.

        Returns:
            Whether Rope stops its folder search at this resource.

        """
        return resource is not None and (
            not resource.is_folder()
            or (
                isinstance(resource, p.Infra.RopeRoot)
                and resource.has_child(c.Infra.INIT_PY)
                and not resource.get_child(c.Infra.INIT_PY).is_folder()
            )
        )

    @classmethod
    def _snapshot_imported_resource(
        cls,
        project: p.Infra.RopeProject,
        folder: p.Infra.RopeRoot,
        name: str,
        *,
        level: int,
        lookup: t.Infra.RopeImportLookup,
    ) -> t.Infra.RopeResource | None:
        """Resolve imports in their native absolute or relative search scope.

        Rope consults an absolute import's own folder last, and only while no
        module or regular package owns the top-level name. An owned name is
        folder-independent: it resolves once per walk, each dotted segment
        inside its regular parent package exactly as Rope's own search does.

        Returns:
            The imported module resource, or ``None`` when Rope cannot find it.

        """
        top = name.partition(".")[0]
        if not level and (top, "", 0) not in lookup:
            owner = project.find_module(top)
            lookup[top, "", 0] = owner if cls._regular_package(owner) else None
        if not level and lookup[top, "", 0] is not None:
            return cls._snapshot_owned_resource(project, folder, name, lookup)
        key = (name, folder.real_path, level)
        if key not in lookup:
            lookup[key] = (
                project.find_relative_module(name, folder, level)
                if level
                else project.find_module(name, folder)
            )
        return lookup[key]

    @classmethod
    def _snapshot_owned_resource(
        cls,
        project: p.Infra.RopeProject,
        folder: p.Infra.RopeRoot,
        name: str,
        lookup: t.Infra.RopeImportLookup,
    ) -> t.Infra.RopeResource | None:
        """Resolve an absolute name whose top-level module Rope owns globally.

        Each dotted segment resolves inside its regular parent package exactly
        as Rope's own search does; a namespace parent keeps Rope's full search.

        Returns:
            The imported module resource, or ``None`` when Rope cannot find it.

        """
        if (name, "", 0) not in lookup:
            head, _, tail = name.rpartition(".")
            parent = cls._snapshot_imported_resource(
                project, folder, head, level=0, lookup=lookup
            )
            if parent is None or not parent.is_folder():
                lookup[name, "", 0] = None
            elif isinstance(parent, p.Infra.RopeRoot) and cls._regular_package(parent):
                lookup[name, "", 0] = project.find_relative_module(tail, parent, 1)
            else:
                lookup[name, "", 0] = project.find_module(name)
        return lookup[name, "", 0]

    @staticmethod
    def _captured_text(
        rule: m.Infra.CodemodRule,
        variable: str,
        captures: t.JsonMapping,
        source: Path,
    ) -> str:
        capture = captures.get(variable)
        text = capture.get("text") if isinstance(capture, Mapping) else capture
        if not isinstance(text, str) or not text.strip():
            msg = (
                f"{rule.id}: context variable ${variable} was not captured in {source}"
            )
            raise ValueError(msg)
        return text.strip()

    @staticmethod
    def _codemod_runtime_aliases(root: Path, package: str, own: str) -> frozenset[str]:
        """Read local aliases from source and dependency aliases from runtime.

        Returns:
            The resulting ``frozenset[str]``.

        Raises:
            ValueError: If project layout is unresolved.

        """
        if package == own:
            layout = FlextInfraUtilitiesCodegenNamespace.layout(root)
            if layout is None:
                msg = f"project layout is unresolved: {root}"
                raise ValueError(msg)
            return frozenset(layout.runtime_aliases)
        return frozenset(u.runtime_alias_names(package))

    @classmethod
    def _context_holds(
        cls,
        root: Path,
        condition: m.Infra.CodemodContextCondition,
        captured: t.Pair[str, str | None],
        file_path: Path,
        facts: m.Infra.CodemodProjectFacts,
    ) -> bool:
        """Evaluate one predicate against the project SSOT it names.

        Returns:
            The resulting ``bool``.

        Raises:
            ValueError: If the predicate is not one the engine declares.

        """
        predicate = condition.predicate
        match predicate:
            case _ if predicate in c.Infra.CODEMOD_PACKAGE_CONTEXT_PREDICATES:
                if predicate is c.Infra.CodemodContextPredicate.COMPOSE_MODULE:
                    return cls._compose_module_holds(
                        root,
                        captured[0],
                        cls._resolved_package_own(root, predicate, file_path, facts),
                        facts,
                        file_path,
                    )
                return cls._context_package_holds(
                    root,
                    predicate,
                    captured,
                    facts,
                    file_path,
                )
            case (
                c.Infra.CodemodContextPredicate.MODULE_EXPORT
                | c.Infra.CodemodContextPredicate.FILE_FAMILY
                | c.Infra.CodemodContextPredicate.PACKAGE_EXPORT
                | c.Infra.CodemodContextPredicate.FACADE_MODULE
                | c.Infra.CodemodContextPredicate.LATER_LAYER
                | c.Infra.CodemodContextPredicate.CLASS_STEM
            ):
                return cls._context_module_holds(
                    root,
                    predicate,
                    captured,
                    file_path,
                    condition,
                )
            case c.Infra.CodemodContextPredicate.PACKAGE_LAYERS:
                return cls._package_has_layers(file_path.parent, condition.arg)
            case (
                c.Infra.CodemodContextPredicate.PACKAGE_ROOT_INIT
                | c.Infra.CodemodContextPredicate.FAMILY_BASE
                | c.Infra.CodemodContextPredicate.FAMILY_BASE_FILE
                | c.Infra.CodemodContextPredicate.LAYER_ZERO_FILE
                | c.Infra.CodemodContextPredicate.IMPORT_CYCLE
                | c.Infra.CodemodContextPredicate.COMPOSES_FAMILY
                | c.Infra.CodemodContextPredicate.FAMILY_MEMBER
            ):
                return cls._context_project_holds(
                    root,
                    predicate,
                    captured,
                    file_path,
                    facts,
                )
            case (
                c.Infra.CodemodContextPredicate.RESOLVED_SYMBOL
                | c.Infra.CodemodContextPredicate.GENERIC_SPECIALIZATION
                | c.Infra.CodemodContextPredicate.SAME_BINDING
                | c.Infra.CodemodContextPredicate.EXECUTABLE_OCCURRENCE
                | c.Infra.CodemodContextPredicate.UNREFERENCED_IMPORT
            ):
                msg = (
                    "semantic predicate is owned by the occurrence evaluator, "
                    f"never the project-fact evaluator: {predicate}"
                )
                raise ValueError(msg)
            case _:
                message = f"predicate is not registered in project facts: {predicate}"
                raise ValueError(message)

    @classmethod
    def _resolved_package_own(
        cls,
        root: Path,
        predicate: c.Infra.CodemodContextPredicate,
        file_path: Path,
        facts: m.Infra.CodemodProjectFacts,
    ) -> str:
        """Resolve the owning package name of one package-scope predicate.

        Args:
            root: The repository root of the admission.
            predicate: The package-scope predicate under evaluation.
            file_path: The file whose owning project names the package.
            facts: The admission project facts.

        Returns:
            The owning package name.

        Raises:
            ValueError: If the admission namespace or project owner is
                unresolved.

        """
        own = facts.own_package
        if own is None:
            message = "package predicates require the admission namespace"
            raise ValueError(message)
        if predicate is c.Infra.CodemodContextPredicate.OWN_PACKAGE:
            owner = FlextInfraUtilitiesProjectDiscovery.nearest_project_root(
                root, file_path
            )
            if owner is None:
                message = f"project owner is unresolved: {file_path}"
                raise ValueError(message)
            return FlextInfraUtilitiesPyproject.project_package_name(owner)
        return own

    @classmethod
    def _context_package_holds(
        cls,
        root: Path,
        predicate: c.Infra.CodemodContextPredicate,
        captured: t.Pair[str, str | None],
        facts: m.Infra.CodemodProjectFacts,
        file_path: Path,
    ) -> bool:
        """Evaluate one package-scope predicate.

        Returns:
            The resulting ``bool``.

        Raises:
            ValueError: If project layout is unresolved.

        """
        value, of = captured
        own = cls._resolved_package_own(root, predicate, file_path, facts)
        module = cls._top_module(value)
        match predicate:
            case c.Infra.CodemodContextPredicate.STDLIB_MODULE:
                return module in sys.stdlib_module_names
            case c.Infra.CodemodContextPredicate.OWN_PACKAGE:
                # The project owns its public package and its internal tiers
                # (tests, examples, scripts); an absolute import between them
                # never crosses a package boundary.
                owner = FlextInfraUtilitiesProjectDiscovery.nearest_project_root(
                    root, file_path
                )
                if owner is None:
                    msg = f"project owner is unresolved: {file_path}"
                    raise ValueError(msg)
                namespaces = FlextInfraUtilitiesCodegenNamespace
                return (
                    module == own
                    or module in c.Infra.NON_PUBLIC_LAZY_ROOTS
                    or module in namespaces.repository_namespace_packages(owner)
                )
            case c.Infra.CodemodContextPredicate.RUNTIME_PACKAGE:
                return module in facts.runtime_modules
            case c.Infra.CodemodContextPredicate.FACADE_PACKAGE:
                return (module == own or module in facts.runtime_modules) and bool(
                    cls._codemod_runtime_aliases(root, module, own),
                )
            case c.Infra.CodemodContextPredicate.RUNTIME_ALIAS:
                return value in cls._codemod_runtime_aliases(
                    root,
                    own if of is None else cls._top_module(of),
                    own,
                )
            case c.Infra.CodemodContextPredicate.LOCAL_ALIAS:
                return value in cls._codemod_runtime_aliases(root, own, own)
            case _:
                message = f"predicate is not package-scoped: {predicate}"
                raise ValueError(message)

    @classmethod
    def _compose_module_holds(
        cls,
        root: Path,
        value: str,
        own: str,
        facts: m.Infra.CodemodProjectFacts,
        file_path: Path,
    ) -> bool:
        """Evaluate the ``compose-module`` predicate (the family-shape amendment).

        The captured dotted module is a sanctioned public family compose
        module when it is exactly ``<package>.<leaf>`` for a canonical
        compose leaf: the own package must declare the leaf module file
        beside its private family packages, and a foreign package must belong
        to the project's runtime closure, where the family shape is the
        fleet-wide contract.

        Args:
            root: The root path of the project.
            value: The captured dotted module name.
            own: The own package name.
            facts: The project's codemod facts.
            file_path: The path to the file being evaluated.

        Returns:
            The resulting ``bool``.

        Raises:
            ValueError: If the project layout is unresolved or if the compose module is
              invalid.

        """
        parts = value.split(".")
        if (
            len(parts) != c.Infra.FAMILY_COMPOSE_MODULE_SEGMENTS
            or parts[1] not in c.Infra.FAMILY_COMPOSE_MODULES
        ):
            return False
        top, leaf = parts
        if top == own:
            owner = FlextInfraUtilitiesProjectDiscovery.nearest_project_root(
                root,
                file_path,
            )
            layout = (
                FlextInfraUtilitiesCodegenNamespace.layout(owner) if owner else None
            )
            if layout is None:
                msg = f"project layout is unresolved: {file_path}"
                raise ValueError(msg)
            return (layout.package_dir / f"{leaf}{c.Infra.EXT_PYTHON}").is_file()
        return top in facts.runtime_modules

    @classmethod
    def _context_module_holds(
        cls,
        root: Path,
        predicate: c.Infra.CodemodContextPredicate,
        captured: t.Pair[str, str | None],
        file_path: Path,
        condition: m.Infra.CodemodContextCondition,
    ) -> bool:
        """Evaluate one module-scope predicate.

        Returns:
            The resulting ``bool``.

        Raises:
            ValueError: If project layout is unresolved; or if predicate.

        """
        value, of = captured
        match predicate:
            case (
                c.Infra.CodemodContextPredicate.MODULE_EXPORT
                | c.Infra.CodemodContextPredicate.FACADE_MODULE
            ):
                exports = cls._module_exports(file_path)
                return (
                    value in exports
                    if predicate is c.Infra.CodemodContextPredicate.MODULE_EXPORT
                    else bool(
                        frozenset(config.Infra.tooling.lazy_init.import_layer_order)
                        & exports
                    )
                )
            case c.Infra.CodemodContextPredicate.FILE_FAMILY:
                return value in cls._file_families(file_path)
            case c.Infra.CodemodContextPredicate.PACKAGE_EXPORT:
                if of is None:
                    msg = f"predicate {predicate} requires an 'of' capture"
                    raise ValueError(msg)
                return value in cls._package_exports(of)
            case c.Infra.CodemodContextPredicate.LATER_LAYER:
                return cls._later_layer(root, file_path, value, condition)
            case c.Infra.CodemodContextPredicate.CLASS_STEM:
                return cls._has_class_stem(root, file_path, value)
            case _:
                message = f"predicate is not module-scoped: {predicate}"
                raise ValueError(message)

    @classmethod
    def _context_project_holds(
        cls,
        root: Path,
        predicate: c.Infra.CodemodContextPredicate,
        captured: t.Pair[str, str | None],
        file_path: Path,
        facts: m.Infra.CodemodProjectFacts,
    ) -> bool:
        """Evaluate one project-scope predicate.

        Returns:
            The resulting ``bool``.

        Raises:
            ValueError: If project layout is unresolved.

        """
        value, of = captured
        match predicate:
            case c.Infra.CodemodContextPredicate.PACKAGE_ROOT_INIT:
                return cls._context_root_init_holds(root, file_path)
            case (
                c.Infra.CodemodContextPredicate.FAMILY_BASE
                | c.Infra.CodemodContextPredicate.FAMILY_BASE_FILE
            ):
                return (
                    cls._family_package_has_base(file_path)
                    if predicate is c.Infra.CodemodContextPredicate.FAMILY_BASE
                    else cls._family_base_file(root, file_path)
                )
            case c.Infra.CodemodContextPredicate.LAYER_ZERO_FILE:
                owner = FlextInfraUtilitiesProjectDiscovery.nearest_project_root(
                    root, file_path
                )
                if owner is None:
                    msg = f"project owner is unresolved: {file_path}"
                    raise ValueError(msg)
                located = FlextInfraUtilitiesImportLaw.import_namespace(
                    owner, file_path
                )
                return located is not None and (
                    FlextInfraUtilitiesImportLaw.import_module_role(located[1])
                    == "layer0"
                )
            case c.Infra.CodemodContextPredicate.IMPORT_CYCLE:
                return cls.import_closes_cycle(root, file_path, value, of, facts)
            case c.Infra.CodemodContextPredicate.COMPOSES_FAMILY:
                return cls.composes_family_package(file_path, value)
            case c.Infra.CodemodContextPredicate.FAMILY_MEMBER:
                return cls._family_member(root, file_path, value)
            case _:
                message = f"predicate is not project-scoped: {predicate}"
                raise ValueError(message)

    @classmethod
    def _family_base_file(cls, root: Path, file_path: Path) -> bool:
        """Prove the immediate family leaf from its owner's declared layout.

        Returns:
            Whether the file is a declared family base leaf.

        Raises:
            ValueError: If the project's layout cannot be resolved.

        """
        owner = FlextInfraUtilitiesProjectDiscovery.nearest_project_root(
            root, file_path
        )
        layout = FlextInfraUtilitiesCodegenNamespace.layout(owner) if owner else None
        if layout is None:
            msg = f"project layout is unresolved: {file_path}"
            raise ValueError(msg)
        directory = file_path.parent
        facade = directory.parent / f"{directory.name.removeprefix('_')}.py"
        return (
            file_path.name == f"base{c.Infra.EXT_PYTHON}"
            and directory.parent.resolve() == layout.package_dir.resolve()
            and directory.name.startswith("_")
            and not directory.name.startswith("__")
            and facade.is_file()
            and bool(
                frozenset(config.Infra.tooling.lazy_init.import_layer_order)
                & cls._module_exports(facade)
            )
        )

    @staticmethod
    def _context_root_init_holds(root: Path, file_path: Path) -> bool:
        """Evaluate the ``PACKAGE_ROOT_INIT`` predicate.

        Returns:
            The resulting ``bool``.

        Raises:
            ValueError: If project layout is unresolved.

        """
        layout = FlextInfraUtilitiesCodegenNamespace.layout(root)
        if layout is None:
            msg = f"project layout is unresolved: {root}"
            raise ValueError(msg)
        return file_path.resolve() == layout.init_path.resolve()

    @staticmethod
    def _top_module(value: str) -> str:
        """Return the top-level package of a captured dotted module.

        Returns:
            The top-level package of a captured dotted module.

        """
        return value.split(maxsplit=1)[0].split(".", maxsplit=1)[0]

    @classmethod
    def _runtime_modules(cls, root: Path) -> frozenset[str]:
        """Top-level import names provided by the project's runtime closure.

        Returns:
            The resulting ``frozenset[str]``.

        """
        project = FlextInfraUtilitiesCodemodRules.codemod_project_requirements(
            root,
        ).unwrap()
        if not project[1]:
            return frozenset()
        cls.codemod_progress(
            f"runtime distributions start requirements={len(project[1])} root={root}",
        )
        distributions = FlextInfraUtilitiesCodemodRules.codemod_distributions()
        cls.codemod_progress(
            f"runtime distributions finish distributions={len(distributions)}",
        )
        cls.codemod_progress("runtime dependency closure start")
        closure = FlextInfraUtilitiesCodemodRules.codemod_runtime_closure(
            project[1],
            distributions,
        )
        cls.codemod_progress(
            f"runtime dependency closure finish distributions={len(closure)}",
        )
        cls.codemod_progress("runtime import package metadata start")
        packages = cls._installed_import_packages()
        cls.codemod_progress(
            f"runtime import package metadata finish packages={len(packages)}",
        )
        selected: set[str] = set()
        due = 0.0
        for index, (module, providers) in enumerate(packages.items(), start=1):
            due = cls.codemod_progress(
                f"runtime imports package={index}/{len(packages)} "
                f"module={module} selected={len(selected)}",
                due,
            )
            if providers & closure:
                selected.add(module)
        cls.codemod_progress(f"runtime imports finish modules={len(selected)}")
        return frozenset(selected)

    @staticmethod
    @cache
    def _installed_import_packages() -> t.MappingKV[str, frozenset[str]]:
        """Map each installed import package to its canonical distributions.

        Installed metadata is a fact of the interpreter environment, fixed for
        the life of the process, so it is read once; a project's runtime
        closure over it is still computed per admission pass.

        Returns:
            The resulting ``t.MappingKV[str, frozenset[str]]``.

        """
        return MappingProxyType({
            module: frozenset(canonicalize_name(name) for name in providers)
            for module, providers in packages_distributions().items()
        })

    @staticmethod
    def _family_member(root: Path, file_path: Path, imported: str) -> bool:
        """Return whether a module belongs to the private family it imports.

        The family is the imported path up to its first ``_``-prefixed
        segment; its facade is that path with the underscore removed. The
        finding belongs to it when its dotted module lies inside the family
        tree or is the facade module itself.

        Returns:
            Whether the finding's module is a member or the facade of the family.

        Raises:
            ValueError: If the finding's project or namespace is unresolved.

        """
        owner = FlextInfraUtilitiesProjectDiscovery.nearest_project_root(
            root, file_path
        )
        located = (
            None
            if owner is None
            else FlextInfraUtilitiesImportLaw.import_namespace(owner, file_path)
        )
        if located is None:
            msg = f"module namespace is unresolved: {file_path}"
            raise ValueError(msg)
        parts = imported.split(".")
        private = next(
            (
                index
                for index, part in enumerate(parts)
                if part.startswith("_") and not part.startswith("__")
            ),
            None,
        )
        if private is None:
            return False
        family = ".".join(parts[: private + 1])
        facade = ".".join((*parts[:private], parts[private].removeprefix("_")))
        module = located[1]
        return module in {family, facade} or module.startswith(f"{family}.")

    @classmethod
    def _module_exports(cls, file_path: Path) -> frozenset[str]:
        """Read exports from the active admission epoch, or a standalone source.

        Returns:
            The resulting ``frozenset[str]``.

        Raises:
            ValueError: If the active admission epoch does not contain the source.

        """
        shared = cls._closed_walk_cache.get()
        if shared is None:
            source = file_path.read_text(encoding=c.DEFAULT_ENCODING)
        else:
            state = next(
                (state for state in shared[1].states if state.path == file_path), None
            )
            if state is None or state.content is None:
                msg = f"module exports lack an authenticated source: {file_path}"
                raise ValueError(msg)
            source = state.content.decode(c.DEFAULT_ENCODING)
        return frozenset(
            FlextInfraUtilitiesRopeAnalysisExports.public_export_names_source(source),
        )

    @classmethod
    def _file_families(cls, file_path: Path) -> frozenset[str]:
        """Facade letters of the family a module belongs to.

        A module belongs to the letters its own ``__all__`` declares and to
        those of the facade module of each private family package it lives
        in (``<pkg>/_models/x.py`` belongs to what ``<pkg>/models.py``
        declares). The letter vocabulary is the tooling import-layer order;
        no file name is mapped to a letter.

        Returns:
            The resulting ``frozenset[str]``.

        """
        letters = frozenset(config.Infra.tooling.lazy_init.import_layer_order)
        shared = cls._closed_walk_cache.get()
        facades = (
            file_path,
            *(
                directory.parent / f"{directory.name.removeprefix('_')}.py"
                for directory in file_path.parents
                if directory.name.startswith("_")
                and not directory.name.startswith("__")
            ),
        )
        return frozenset(
            letter
            for facade in facades
            if (
                facade.is_file()
                if shared is None
                else shared[0].source_query(facade, "isfile")
            )
            for letter in letters.intersection(cls._module_exports(facade))
        )

    @classmethod
    @lru_cache(maxsize=256)
    def _package_exports(cls, module: str) -> frozenset[str]:
        """Names an installed module declares in its ``__all__`` (not imported).

        Returns:
            The resulting ``frozenset[str]``.

        Raises:
            ValueError: If module is not importable for its exports.

        """
        spec = find_spec(module)
        if spec is None or spec.origin is None:
            msg = f"module is not importable for its exports: {module}"
            raise ValueError(msg)
        return cls._module_exports(Path(spec.origin))

    @classmethod
    def _later_layer(
        cls,
        root: Path,
        file_path: Path,
        imported: str,
        condition: p.Infra.CodemodContextOperands,
        *,
        binding: t.Pair[p.Infra.RopeProject, t.MappingKV[Path, str]] | None = None,
    ) -> bool:
        """Return whether an import reaches a later layer than its module's.

        Layers and their order are the tooling import-layer order. A
        module's layer is its first architectural role relative to the owned
        repository, including tests and examples outside src. An imported
        letter is its own layer. A rule may
        name the layer to compare with (``arg``) instead of the module's, and
        the layer an imported name that is no layer stands for (``as``).

        Returns:
            Whether an import reaches a later layer than its module's.

        Raises:
            ValueError: If a comparison layer is undeclared or the source
                lies outside its selected repository.

        """
        order = tuple(config.Infra.tooling.lazy_init.import_layer_order)
        if condition.arg:
            owner = cls._layer_rank(order, frozenset(condition.arg))
        else:
            owner = cls._resolved_module_layer(root, file_path, binding)
        if owner is None:
            message = f"import comparison layer is undeclared: {condition.arg!r}"
            raise ValueError(message)
        return cls._import_target_later(
            root, file_path, imported, condition, (owner, binding)
        )

    @classmethod
    def _resolved_module_layer(
        cls,
        root: Path,
        path: Path,
        binding: t.Pair[p.Infra.RopeProject, t.MappingKV[Path, str]] | None,
    ) -> int:
        """Resolve fallback service roles from the pass's authenticated native graph.

        Returns:
            The explicit path layer or its proven service implementation role.

        """
        order = tuple(config.Infra.tooling.lazy_init.import_layer_order)
        namespace = ".".join(path.relative_to(root).with_suffix("").parts)
        rank = FlextInfraUtilitiesImportLaw.module_import_layer(namespace)
        if rank != order.index("other") or binding is None:
            return rank
        cache = cls._module_role_cache.get()
        cached = None if cache is None else cache.get(path)
        if cached is not None:
            return cached
        resolved = cls._native_service_layer(root, path, binding)
        rank = order.index("services") if resolved else rank
        if cache is not None:
            cache[path] = rank
        return rank

    @staticmethod
    def _native_service_layer(
        root: Path,
        path: Path,
        binding: t.Pair[p.Infra.RopeProject, t.MappingKV[Path, str]],
    ) -> bool:
        """Prove service ancestry using the existing authenticated source C3 owner.

        Returns:
            Whether a module-defined class derives from its own service root.

        """
        project, sources = binding
        if path not in sources:
            return False
        native_paths = frozenset(FlextInfraUtilitiesRopeCore.python_file_paths(project))
        if path not in native_paths:
            return False
        modules: t.MutableMappingKV[str, t.Pair[Path, str]] = {}
        roots: list[m.Infra.SourceClassReference] = []
        declarations: list[m.Infra.SourceClassReference] = []
        order = tuple(config.Infra.tooling.lazy_init.import_layer_order)
        for source_path, text in sources.items():
            if (
                source_path.suffix != c.Infra.EXT_PYTHON
                or not source_path.is_relative_to(root)
                or source_path not in native_paths
            ):
                continue
            module = FlextInfraUtilitiesRopeRuntimeTypes.require_parsed_module(
                project.get_pymodule(
                    project.get_resource(source_path.relative_to(root).as_posix())
                )
            )
            name = (
                source_path.stem
                if source_path.parent == root
                else FlextInfraUtilitiesRopeAnalysisWorkspace.module_name_for_file(
                    source_path, project_root=root
                )
            )
            modules[name] = source_path, text
            namespace = ".".join(source_path.relative_to(root).with_suffix("").parts)
            if (
                FlextInfraUtilitiesImportLaw.module_import_layer(namespace)
                == order.index("base")
                and "s" in module.get_attributes()
                and FlextInfraUtilitiesRopeRuntimeTypes.py_class(
                    module.get_attribute("s").get_object()
                )
            ):
                roots.append(
                    m.Infra.SourceClassReference(
                        target=name, attributes=("s",), qualified_base=f"{name}.s"
                    )
                )
            if source_path == path:
                class_names = dict.fromkeys(
                    value.get_name()
                    for attribute in module.get_attributes().values()
                    if FlextInfraUtilitiesRopeRuntimeTypes.py_class(
                        value := attribute.get_object()
                    )
                    and value.get_module() is module
                )
                declarations.extend(
                    m.Infra.SourceClassReference(
                        target=name,
                        attributes=(class_name,),
                        qualified_base=f"{name}.{class_name}",
                    )
                    for class_name in class_names
                )
        if not declarations:
            return False
        return any(
            FlextInfraUtilitiesRopeSourceBasesRuntime.source_class_order(
                project, modules, (service, *declarations)
            )[0]
            != service.qualified_base
            for service in roots
        )

    @classmethod
    def _import_target_later(
        cls,
        root: Path,
        file_path: Path,
        imported: str,
        condition: p.Infra.CodemodContextOperands,
        comparison: t.Pair[
            int, t.Pair[p.Infra.RopeProject, t.MappingKV[Path, str]] | None
        ],
    ) -> bool:
        """Compare an import target with its resolved source layer.

        Returns:
            Whether the target occupies a later layer.

        Raises:
            ValueError: If the target layer or project namespace is undeclared.

        """
        owner, binding = comparison
        order = tuple(config.Infra.tooling.lazy_init.import_layer_order)
        if not condition.as_:
            layout = FlextInfraUtilitiesCodegenNamespace.layout(root)
            if layout is None:
                message = f"import comparison project namespace is undeclared: {root}"
                raise ValueError(message)
            if imported == layout.package_name:
                return False
        if imported in order:
            target_layers: frozenset[str] = frozenset({imported})
        elif imported.isidentifier() and condition.as_:
            target_layers = frozenset(condition.as_)
        else:
            target = cls._own_module_path(root, file_path, imported)
            if target is None:
                if "." not in imported:
                    return False
                target_rank = FlextInfraUtilitiesImportLaw.module_import_layer(imported)
                return target_rank > owner
            return cls._resolved_module_layer(root, target, binding) > owner
        target_rank = cls._layer_rank(order, target_layers)
        if target_rank is None:
            message = f"import target layer is undeclared: {condition.as_!r}"
            raise ValueError(message)
        return target_rank > owner

    @classmethod
    def _has_class_stem(cls, root: Path, file_path: Path, name: str) -> bool:
        """Return whether a class name carries the project's class stem.

        The prefix is the one class nesting derives for the module's owner:
        a module of a non-public lazy root (tests, examples, scripts) carries
        the surface-prefixed stem. Outside the tests tree the bare stem also
        names scenario classes.

        Returns:
            Whether a class name carries the project's class stem.

        Raises:
            ValueError: If project layout is unresolved.

        """
        context = cls._class_stem_context.get()
        source_project = None if context is None else context[0]
        owner = FlextInfraUtilitiesProjectDiscovery.nearest_project_root(
            root, file_path, source_project=source_project
        )
        if owner is None:
            msg = f"project owner is unresolved: {file_path}"
            raise ValueError(msg)
        if context is None:
            layout = FlextInfraUtilitiesCodegenNamespace.layout(owner)
        else:
            project, layouts, receipts = context
            with FlextInfraUtilitiesRopeCore.cached_source_query(
                project, layouts, owner, receipts, str(owner)
            ) as cached:
                if not cached:
                    layouts[owner] = FlextInfraUtilitiesCodegenNamespace.layout(
                        owner, rope_project=project
                    )
                layout = layouts[owner]
        if layout is None:
            msg = f"project layout is unresolved: {owner}"
            raise ValueError(msg)
        prefix = FlextInfraUtilitiesCodegenNamespace.project_prefix(
            file_path,
            project_layout=layout,
            source_project=source_project,
        )
        if file_path.relative_to(owner).parts[0] in (
            FlextInfraUtilitiesCodegenNamespace.repository_namespace_packages(
                owner, source_project=source_project
            )
        ):
            return name.startswith(prefix)
        if file_path.is_relative_to(owner / c.Infra.DIR_TESTS):
            return name.startswith(prefix)
        return name.startswith((prefix, layout.class_stem))

    @classmethod
    def _package_has_layers(cls, package: Path, layers: t.StrSequence) -> bool:
        """Return whether a package provides every named layer.

        A layer is provided by a runtime alias the package's modules declare
        (a facade letter), by a module or private module named for it, or by
        a subpackage of that name.

        Returns:
            Whether a package provides every named layer.

        """
        aliases = frozenset(
            alias
            for module in package.glob(f"*{c.Infra.EXT_PYTHON}")
            if module.name != c.Infra.INIT_PY
            for alias in cls._module_exports(module)
        )
        return all(
            layer in aliases
            or (package / f"{layer}{c.Infra.EXT_PYTHON}").is_file()
            or (package / f"_{layer}{c.Infra.EXT_PYTHON}").is_file()
            or (package / layer / c.Infra.INIT_PY).is_file()
            for layer in layers
        )

    @classmethod
    def _family_package_has_base(cls, file_path: Path) -> bool:
        """Return whether the family package holding a module has ``base.py``.

        A family package is a private directory ``_<stem>`` beside a facade
        module ``<stem>.py`` that declares a facade letter.

        Returns:
            Whether the family package holding a module has ``base.py``.

        """
        letters = frozenset(config.Infra.tooling.lazy_init.import_layer_order)
        for directory in file_path.parents:
            facade = directory.parent / f"{directory.name.removeprefix('_')}.py"
            if (
                directory.name.startswith("_")
                and not directory.name.startswith("__")
                and facade.is_file()
                and letters & cls._module_exports(facade)
            ):
                return (directory / f"base{c.Infra.EXT_PYTHON}").is_file()
        return True

    @staticmethod
    def _layer_rank(order: t.StrSequence, layers: frozenset[str]) -> int | None:
        ranks = [order.index(layer) for layer in layers if layer in order]
        return min(ranks) if ranks else None

    @staticmethod
    def _own_module_path(root: Path, file_path: Path, imported: str) -> Path | None:
        """Resolve an import of the own package to its module file or package.

        Returns:
            The resulting ``Path | None``.

        """
        layout = FlextInfraUtilitiesCodegenNamespace.layout(root)
        if layout is None or not file_path.is_relative_to(layout.src_dir):
            return None
        level = len(imported) - len(imported.lstrip("."))
        parts = [part for part in imported.lstrip(".").split(".") if part]
        if level:
            base = file_path.parent
            for _ in range(level - 1):
                base = base.parent
        else:
            if not parts or parts[0] != layout.package_name:
                return None
            base = layout.src_dir
        target = base.joinpath(*parts)
        module = target.with_suffix(c.Infra.EXT_PYTHON)
        return module if module.is_file() else target

    @classmethod
    def parse_namespace_validation(
        cls,
        validation: p.Result[m.Infra.ValidationReport],
        root: Path,
    ) -> p.Result[t.VariadicTuple[m.Infra.CensusViolation]]:
        """Convert the engine-backed namespace report into census violations.

        A violation is fixable when its rule declares a token fix or a rope
        relocation in the project's rule plan.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Infra.CensusViolation]]``.

        Raises:
            ValueError: If namespace violation does not follow the report format.

        """
        if validation.failure:
            return r[t.VariadicTuple[m.Infra.CensusViolation]].from_failure(validation)
        planned = cls.codemod_rule_plan(root)
        if planned.failure:
            return r[t.VariadicTuple[m.Infra.CensusViolation]].from_failure(planned)
        repairable = frozenset(
            rule.id
            for rule in planned.value.rules
            if rule.fixable
            or rule.relocation is not None
            or rule.id in c.Infra.SEMANTIC_CUTOVER_RULE_IDS.values()
        )
        parsed: list[m.Infra.CensusViolation] = []
        for violation in validation.value.violations:
            match = c.Infra.VIOLATION_PATTERN.match(violation)
            if match is None:
                msg = (
                    f"namespace violation does not follow the report format: "
                    f"{violation}"
                )
                raise ValueError(msg)
            parsed.append(
                m.Infra.CensusViolation(
                    module=match.group("module"),
                    rule=match.group("rule"),
                    line=int(match.group("line")),
                    message=match.group("message"),
                    fixable=match.group("rule") in repairable,
                ),
            )
        return r[t.VariadicTuple[m.Infra.CensusViolation]].ok(tuple(parsed))

    @staticmethod
    def _known_prefix(module: str, known: frozenset[str]) -> str | None:
        """Return the longest dotted prefix of ``module`` the project defines.

        Returns:
            The longest dotted prefix of ``module`` the project defines.

        """
        parts = module.split(".")
        for size in range(len(parts), 0, -1):
            candidate = ".".join(parts[:size])
            if candidate in known:
                return candidate
        return None


__all__: list[str] = ["FlextInfraUtilitiesCodemodProject"]
