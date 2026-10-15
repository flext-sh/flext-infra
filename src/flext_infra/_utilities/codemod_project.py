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
from collections import deque
from collections.abc import Generator, Mapping, MutableMapping
from contextlib import closing, contextmanager
from functools import cache, lru_cache
from importlib.metadata import packages_distributions
from importlib.util import find_spec
from pathlib import Path
from types import MappingProxyType

from flext_cli import u
from packaging.utils import canonicalize_name

from flext_infra import c, config, m, p, r, t
from flext_infra._utilities import (
    FlextInfraFlextUtilitiesCodemodBindingChain,
    FlextInfraUtilitiesBase,
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesCodemodRules,
    FlextInfraUtilitiesDeclarationPayload,
    FlextInfraUtilitiesImportLaw,
    FlextInfraUtilitiesProjectDiscovery,
    FlextInfraUtilitiesPyproject,
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeImports,
    FlextInfraUtilitiesRopeRuntime,
    FlextInfraUtilitiesRopeRuntimeModules,
)
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


class FlextInfraUtilitiesCodemodProject(
    FlextInfraFlextUtilitiesCodemodBindingChain.FlextInfraUtilitiesCodemodBindingChain
):
    """Evaluate rule context over project facts: packages, layers, graphs."""

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

        Returns:
            The runtime import graph and the module name of each file.

        """
        with FlextInfraUtilitiesRopeCore.open_project(root) as project:
            return cls.snapshot_import_graph(project)

    @classmethod
    def snapshot_import_graph(
        cls,
        project: p.Infra.RopeProject,
    ) -> t.Pair[t.MappingKV[str, frozenset[str]], t.MappingKV[Path, str]]:
        """Read runtime imports from an immutable proposed-source Rope graph.

        Returns:
            The resulting ``t.Pair[t.MappingKV[str, frozenset[str]], t.MappingKV[Path,
                str]]``.

        Raises:
            ValueError: If rope could not name module.
        """
        raw: MutableMapping[str, set[str]] = {}
        modules: MutableMapping[Path, str] = {}
        aliases: MutableMapping[str, str] = {}
        for resource in FlextInfraUtilitiesRopeCore.python_resources(project):
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
                )
            )
            aliases.update({
                f"{name}.{export}": provider
                for export, provider in provider_aliases.items()
            })
        known = frozenset(raw)
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

    @staticmethod
    def _source_scan_ignored(root: Path, file_path: Path) -> bool:
        """Return whether ``file_path`` lies in a source-scan-ignored tree.

        The names are the codegen artifact SSOT (``source_scan_ignored``),
        the same list Rope uses when it builds the import graph. ``legado``
        is one of those names.

        Returns:
            Whether ``file_path`` lies in a source-scan-ignored tree.

        """
        resolved = file_path.resolve()
        root_resolved = root.resolve()
        parts = (
            resolved.relative_to(root_resolved).parts
            if resolved.is_relative_to(root_resolved)
            else resolved.parts
        )
        return bool(
            frozenset(config.Infra.codegen.source_scan_ignored).intersection(parts),
        )

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
                and not cls._source_scan_ignored(root, file_path)
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
        return m.Infra.CodemodProjectFacts(
            own_package=(
                FlextInfraUtilitiesPyproject.project_package_name(resolved)
                if predicates & c.Infra.CODEMOD_PACKAGE_CONTEXT_PREDICATES
                else None
            ),
            predicates=predicates,
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
        return (file_path if file_path.is_absolute() else root / file_path).resolve()

    @staticmethod
    def codemod_binding_requirements(
        rules: t.SequenceOf[m.Infra.CodemodRule],
    ) -> t.Pair[frozenset[str], t.StrSequence]:
        """Elect binding inputs only for the rules that actually found code.

        Returns:
            Rule identities requiring inference and their declared symbol owners.
        """
        predicates = {
            c.Infra.CodemodContextPredicate.RESOLVED_SYMBOL,
            c.Infra.CodemodContextPredicate.EMITTED_SYMBOL,
            c.Infra.CodemodContextPredicate.SAME_BINDING,
            c.Infra.CodemodContextPredicate.EXECUTABLE_OCCURRENCE,
            c.Infra.CodemodContextPredicate.UNREFERENCED_IMPORT,
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
                    c.Infra.CodemodContextPredicate.RESOLVED_SYMBOL,
                    c.Infra.CodemodContextPredicate.EMITTED_SYMBOL,
                }
            ),
        )
        return frozenset(rule.id for rule in selected), modules

    @classmethod
    def codemod_context_admits(
        cls,
        admission: m.Infra.CodemodAdmission,
        *,
        project: p.Infra.RopeProject,
        sources: t.MappingKV[Path, str],
    ) -> bool:
        """Return whether one finding satisfies its rule's project context.

        ``admission.captures`` maps each metavariable of the finding to its
        ast-grep single capture (``{"text": ...}``) or transformed value (a
        string). A declared variable the finding did not capture is a rule
        defect and raises; the syntactic match alone never stands in for it.

        ``admission.facts`` is the admission pass's project snapshot; it must
        have been built for every predicate the rule names.

        Returns:
            Whether one finding satisfies its rule's project context.

        Raises:
            ValueError: If the facts were not built for a predicate of the rule.

        """
        root = admission.root
        rule = admission.rule
        captures = admission.captures
        facts = admission.facts
        missing = {condition.predicate for condition in rule.context} - facts.predicates
        if missing:
            msg = (
                f"{rule.id}: project facts were not built for predicates "
                f"{sorted(missing)}"
            )
            raise ValueError(msg)
        source = cls.codemod_source_path(root, admission.file_path)
        for condition in rule.context:
            if condition.predicate in {
                c.Infra.CodemodContextPredicate.RESOLVED_SYMBOL,
                c.Infra.CodemodContextPredicate.EMITTED_SYMBOL,
                c.Infra.CodemodContextPredicate.SAME_BINDING,
                c.Infra.CodemodContextPredicate.EXECUTABLE_OCCURRENCE,
                c.Infra.CodemodContextPredicate.UNREFERENCED_IMPORT,
            }:
                holds = cls._occurrence_binding_holds(
                    (root, source, project), condition, captures, sources
                )
                if holds is not condition.holds:
                    return False
                continue
            # A condition binds the capture of the branch that matched: a rule
            # variable the matching branch does not capture leaves it vacuous.
            # The plan proved every context variable occurs in the rule.
            if condition.variable not in captures:
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
    @contextmanager
    def codemod_binding_project(
        root: Path,
        snapshot: m.Infra.CodemodBindingSnapshot,
    ) -> Generator[t.Pair[p.Infra.RopeProject, t.MappingKV[Path, str]]]:
        """Own one immutable binding graph for the complete admission pass.

        Yields:
            The frozen Rope graph and its complete authenticated source closure.
        """
        sources = MappingProxyType({
            state.path.resolve(): state.content.decode("utf-8")
            for state in snapshot.states
            if state.content is not None
        })
        with (
            FlextInfraUtilitiesRopeCore.open_project(root) as live,
            closing(
                FlextInfraUtilitiesRopeRuntimeModules.snapshot_project(
                    live, sources, captured=snapshot
                )
            ) as project,
            project.frozen_layout(),
        ):
            yield project, sources

    @classmethod
    def codemod_binding_snapshot(
        cls,
        root: Path,
        source_states: tuple[m.Cli.AtomicFileState, ...] = (),
        modules: t.StrSequence = (),
    ) -> m.Infra.CodemodBindingSnapshot:
        """Capture Python owners and their static import closure before inference.

        Returns:
            The resulting ``m.Infra.CodemodBindingSnapshot``.

        Raises:
            ValueError: If binding source snapshots disagree.
        """
        states: t.MutableMappingKV[Path, m.Cli.AtomicFileState] = {}
        for state in source_states:
            if states.setdefault(state.path.resolve(), state) != state:
                msg = f"binding source snapshots disagree: {state.path}"
                raise ValueError(msg)
        with (
            FlextInfraUtilitiesRopeCore.open_project(root) as project,
            project.frozen_layout(),
        ):
            lookup = m.Infra.CodemodImportResources()
            pending = [
                project.get_resource(path.relative_to(root.resolve()).as_posix())
                for path in states
            ]
            pending.extend(
                resource
                for name in modules
                if (resource := project.find_module(name)) is not None
            )
            scheduled = {resource.real_path for resource in pending}
            search_roots = tuple(
                folder
                for folder in (
                    *project.get_source_folders(),
                    *project.get_python_path_folders(),
                )
                if isinstance(folder, p.Infra.RopeRoot)
            )
            visited: set[Path] = set()
            while pending:
                fetched = cls._snapshot_module_tree(
                    states,
                    visited,
                    pending.pop(),
                )
                if fetched is None:
                    continue
                path, resource, tree = fetched
                visited.add(path)
                for imported in cls._snapshot_import_resources(
                    project,
                    resource,
                    tree,
                    lookup,
                    search_roots,
                ):
                    if imported.real_path not in scheduled:
                        scheduled.add(imported.real_path)
                        pending.append(imported)
        return m.Infra.CodemodBindingSnapshot(states=tuple(states.values()))

    @staticmethod
    def _snapshot_module_tree(
        states: t.MutableMappingKV[Path, m.Cli.AtomicFileState],
        visited: set[Path],
        resource: t.Infra.RopeResource,
    ) -> t.Triple[Path, t.Infra.RopeResource, ast.Module] | None:
        """Authenticate one pending module and parse its snapshot source.

        Returns:
            The resolved path, live resource, and parsed tree, or ``None``
            when the resource carries no governable Python source.

        Raises:
            TypeError: If binding package has no source resource contract.
            ValueError: If binding source is absent.

        """
        path = Path(resource.real_path).resolve()
        if path.is_dir():
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
        if (
            path in visited
            or not path.is_file()
            or path.suffix not in {c.Infra.EXT_PYTHON, c.Infra.EXT_PYTHON_STUB}
        ):
            return None
        state = states.get(path)
        if state is None:
            state = u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()
            states[path] = state
        if state.content is None:
            msg = f"binding source is absent: {path}"
            raise ValueError(msg)
        return (
            path,
            resource,
            ast.parse(state.content.decode("utf-8"), filename=str(path)),
        )

    @classmethod
    def _snapshot_import_resources(
        cls,
        project: p.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        tree: ast.Module,
        lookup: m.Infra.CodemodImportResources,
        search_roots: t.SequenceOf[p.Infra.RopeRoot],
    ) -> list[t.Infra.RopeResource]:
        """Collect the Rope resources of every import inside one module tree.

        Returns:
            The pending resources named by the module's import statements.

        """
        found: list[t.Infra.RopeResource] = []
        relative_roots = (
            (resource.parent,) if isinstance(resource.parent, p.Infra.RopeRoot) else ()
        )
        folders = ((*search_roots, *relative_roots), relative_roots)
        pending = deque[ast.stmt | ast.ExceptHandler | ast.match_case](tree.body)
        while pending:
            node = pending.popleft()
            if isinstance(node, ast.Import | ast.ImportFrom):
                found.extend(
                    cls._snapshot_node_import_resources(
                        project,
                        resource,
                        node,
                        lookup,
                        folders,
                    ),
                )
            # Imports are statements. Exception handlers and match cases are
            # the two non-statement owners of statement suites; expression and
            # annotation trees cannot contain an import.
            pending.extend(
                child
                for child in ast.iter_child_nodes(node)
                if isinstance(child, ast.stmt | ast.ExceptHandler | ast.match_case)
            )
        return found

    @classmethod
    def _snapshot_node_import_resources(
        cls,
        project: p.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        node: ast.AST,
        lookup: m.Infra.CodemodImportResources,
        folders: t.Pair[
            t.SequenceOf[p.Infra.RopeRoot],
            t.SequenceOf[p.Infra.RopeRoot],
        ],
    ) -> list[t.Infra.RopeResource]:
        """Collect the Rope resources of one import statement's targets.

        Returns:
            The pending resources named by the statement, possibly empty.

        """
        found: list[t.Infra.RopeResource] = []
        imports = (
            tuple(alias.name for alias in node.names)
            if isinstance(node, ast.Import)
            else (node.module or "",)
            if isinstance(node, ast.ImportFrom)
            else ()
        )
        level = node.level if isinstance(node, ast.ImportFrom) else 0
        for name in imports:
            imported = cls._snapshot_imported_resource(
                project,
                resource,
                name,
                level=level,
                lookup=lookup,
            )
            if imported is not None:
                found.append(imported)
        if not isinstance(node, ast.ImportFrom):
            return found
        for alias in node.names:
            if alias.name == "*":
                continue
            child = cls._snapshot_child_imported_resource(
                (project, resource),
                (node.module or "", alias.name),
                level=level,
                lookup=lookup,
                folders=folders[1 if level else 0],
            )
            if child is not None:
                found.append(child)
        return found

    @staticmethod
    def _snapshot_child_imported_resource(
        frame: t.Pair[p.Infra.RopeProject, t.Infra.RopeResource],
        names: t.Pair[str, str],
        *,
        level: int,
        lookup: m.Infra.CodemodImportResources,
        folders: t.SequenceOf[p.Infra.RopeRoot],
    ) -> t.Infra.RopeResource | None:
        """Resolve descendants in the SDK's complete search-root order.

        The SDK elects a same-named directory before a module file. Only an
        elected folder can contain descendants in that search root; later
        roots retain their independent package and namespace resolution.

        Returns:
            The first real child module in the native resolution order.

        """
        project, resource = frame
        modules_by_name = lookup.modules
        parent_name, child_name = names
        qualified = f"{parent_name}.{child_name}" if parent_name else child_name
        key = (qualified, resource.parent.real_path, level)
        if key in modules_by_name:
            return modules_by_name[key]
        modules_by_name[key] = None
        for folder in folders:
            parent_key = (parent_name, folder.real_path, level or 1)
            if parent_key not in modules_by_name:
                modules_by_name[parent_key] = project.find_relative_module(
                    parent_name, folder, level or 1
                )
            elected = modules_by_name[parent_key]
            if elected is None:
                continue
            if elected.real_path not in lookup.folders:
                lookup.folders[elected.real_path] = (
                    elected if isinstance(elected, p.Infra.RopeRoot) else None
                )
            parent = lookup.folders[elected.real_path]
            if parent is None:
                continue
            child_key = (child_name, parent.real_path, 1)
            if child_key not in modules_by_name:
                modules_by_name[child_key] = project.find_relative_module(
                    child_name, parent, 1
                )
            child = modules_by_name[child_key]
            if child is not None:
                modules_by_name[key] = child
                break
        return modules_by_name[key]

    @staticmethod
    def _snapshot_imported_resource(
        project: p.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        name: str,
        *,
        level: int,
        lookup: m.Infra.CodemodImportResources,
    ) -> t.Infra.RopeResource | None:
        """Resolve one imported module name relative to the importing package.

        Returns:
            The imported module resource, or ``None`` when Rope cannot find it.

        """
        modules_by_name = lookup.modules
        folder = resource.parent
        key = (name, folder.real_path, level)
        if key in modules_by_name:
            return modules_by_name[key]
        if level:
            modules_by_name[key] = project.find_relative_module(name, folder, level)
            return modules_by_name[key]
        # Source and Python-path folders are frozen for this snapshot. Their
        # absolute-module lookup is shared by every importing module; only the
        # final importing-folder lookup is local to the occurrence.
        absolute = (name, None, 0)
        if absolute not in modules_by_name:
            modules_by_name[absolute] = project.find_module(name)
        imported = modules_by_name[absolute]
        modules_by_name[key] = (
            imported
            if imported is not None
            else project.find_relative_module(name, folder, 1)
        )
        return modules_by_name[key]

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
            case c.Infra.CodemodContextPredicate.PAYLOAD_DECLARATION:
                with FlextInfraUtilitiesRopeCore.open_project(root) as project:
                    resource = FlextInfraUtilitiesRopeRuntime.require_file_resource(
                        project.get_resource(
                            file_path.relative_to(root).as_posix(),
                        ),
                        file_path,
                    )
                    declarations = tuple(
                        node
                        for node in ast.walk(ast.parse(resource.read()))
                        if isinstance(node, ast.ClassDef) and node.name == captured[0]
                    )
                    return (
                        len(declarations) == 1
                        and FlextInfraUtilitiesDeclarationPayload.payload_declaration(
                            project,
                            file_path,
                            declarations[0],
                        )
                        is not None
                    )
            case _ if predicate in c.Infra.CODEMOD_PACKAGE_CONTEXT_PREDICATES:
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
                    own = FlextInfraUtilitiesPyproject.project_package_name(owner)
                return cls._context_package_holds(
                    root,
                    predicate,
                    captured,
                    own,
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
    def _context_package_holds(
        cls,
        root: Path,
        predicate: c.Infra.CodemodContextPredicate,
        captured: t.Pair[str, str | None],
        own: str,
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
        module = cls._top_module(value)
        match predicate:
            case c.Infra.CodemodContextPredicate.STDLIB_MODULE:
                return module in sys.stdlib_module_names
            case c.Infra.CodemodContextPredicate.OWN_PACKAGE:
                # The project owns its public package and its internal tiers
                # (tests, examples, scripts); an absolute import between them
                # never crosses a package boundary.
                return module == own or module in c.Infra.NON_PUBLIC_LAZY_ROOTS
            case c.Infra.CodemodContextPredicate.RUNTIME_PACKAGE:
                return module in facts.runtime_modules
            case c.Infra.CodemodContextPredicate.FACADE_PACKAGE:
                return module in facts.runtime_modules and bool(
                    cls._codemod_runtime_aliases(root, module, own),
                )
            case c.Infra.CodemodContextPredicate.RUNTIME_ALIAS:
                return value in cls._codemod_runtime_aliases(
                    root,
                    own if of is None else cls._top_module(of),
                    own,
                )
            case c.Infra.CodemodContextPredicate.LOCAL_ALIAS:
                layout = FlextInfraUtilitiesCodegenNamespace.layout(root)
                if layout is None:
                    msg = f"project layout is unresolved: {root}"
                    raise ValueError(msg)
                return value in layout.runtime_aliases
            case c.Infra.CodemodContextPredicate.COMPOSE_MODULE:
                return cls._is_compose_module(value, module, own, root, facts, file_path)
            case _:
                message = f"predicate is not package-scoped: {predicate}"
                raise ValueError(message)

    @classmethod
    def _is_compose_module(
        cls,
        value: str,
        module: str,
        own: str,
        root: Path,
        facts: m.Infra.CodemodProjectFacts,
        file_path: Path,
    ) -> bool:
        """Prove one captured module path is a canonical compose module.

        The family-shape contract sanctions the public compose surface
        ``<package>.<leaf>``: exactly one canonical leaf below a package root,
        never a deeper path and never a private leaf. The own package admits
        the leaf only when it declares the module file; a runtime package of
        the dependency closure admits the canonical leaf name.

        Returns:
            The resulting ``bool``.

        Raises:
            ValueError: If the project layout is unresolved.

        """
        parts = value.split(".")
        if len(parts) != 2 or parts[1] not in c.Infra.CODEMOD_COMPOSE_MODULE_LEAVES:
            return False
        if module != own:
            return module in facts.runtime_modules
        owner = FlextInfraUtilitiesProjectDiscovery.nearest_project_root(
            root, file_path
        )
        layout = FlextInfraUtilitiesCodegenNamespace.layout(owner) if owner else None
        if layout is None:
            msg = f"project layout is unresolved: {file_path}"
            raise ValueError(msg)
        return (layout.package_dir / f"{parts[1]}{c.Infra.EXT_PYTHON}").is_file()

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
            case c.Infra.CodemodContextPredicate.MODULE_EXPORT:
                return value in cls._module_exports(file_path)
            case c.Infra.CodemodContextPredicate.FILE_FAMILY:
                return value in cls._file_families(file_path)
            case c.Infra.CodemodContextPredicate.PACKAGE_EXPORT:
                if of is None:
                    msg = f"predicate {predicate} requires an 'of' capture"
                    raise ValueError(msg)
                return value in cls._package_exports(of)
            case c.Infra.CodemodContextPredicate.FACADE_MODULE:
                return bool(
                    frozenset(config.Infra.tooling.lazy_init.import_layer_order)
                    & cls._module_exports(file_path),
                )
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
            case c.Infra.CodemodContextPredicate.FAMILY_BASE:
                return cls._family_package_has_base(file_path)
            case c.Infra.CodemodContextPredicate.FAMILY_BASE_FILE:
                return cls._family_base_file(root, file_path)
            case c.Infra.CodemodContextPredicate.LAYER_ZERO_FILE:
                located = FlextInfraUtilitiesImportLaw.import_namespace(root, file_path)
                return located is not None and (
                    FlextInfraUtilitiesImportLaw.import_module_role(located[1])
                    == "layer0"
                )
            case c.Infra.CodemodContextPredicate.IMPORT_CYCLE:
                return cls.import_closes_cycle(root, file_path, value, of, facts)
            case c.Infra.CodemodContextPredicate.COMPOSES_FAMILY:
                return cls.composes_family_package(file_path, value)
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
        closure = FlextInfraUtilitiesCodemodRules.codemod_runtime_closure(
            project[1],
            FlextInfraUtilitiesCodemodRules.codemod_distributions(),
        )
        return frozenset(
            module
            for module, providers in cls._installed_import_packages().items()
            if providers & closure
        )

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
    def _module_exports(file_path: Path) -> frozenset[str]:
        """Names one module source declares in its own ``__all__``.

        Returns:
            The resulting ``frozenset[str]``.

        """
        return frozenset(
            FlextInfraUtilitiesRopeAnalysisExports.public_export_names_source(
                file_path.read_text(encoding=c.DEFAULT_ENCODING),
            ),
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
            if facade.is_file()
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
        condition: m.Infra.CodemodContextCondition,
    ) -> bool:
        """Return whether an import reaches a later layer than its module's.

        Layers and their order are the tooling import-layer order. A
        module's layer is a family it belongs to (its own ``__all__`` or its
        family package's facade) or the layer its stem names (``settings``,
        ``base``, ``api``); an imported letter is its own layer. A rule may
        name the layer to compare with (``arg``) instead of the module's, and
        the layer an imported name that is no layer stands for (``as``).

        Returns:
            Whether an import reaches a later layer than its module's.

        """
        order = tuple(config.Infra.tooling.lazy_init.import_layer_order)
        owner = cls._layer_rank(
            order,
            frozenset(condition.arg) if condition.arg else cls._path_layers(file_path),
        )
        if owner is None:
            return False
        if imported in order:
            target_layers: frozenset[str] = frozenset({imported})
        elif imported.isidentifier() and condition.as_:
            target_layers = frozenset(condition.as_)
        else:
            target = cls._own_module_path(root, file_path, imported)
            if target is None:
                return False
            target_layers = cls._path_layers(target)
        target_rank = cls._layer_rank(order, target_layers)
        return target_rank is not None and target_rank > owner

    @staticmethod
    def _has_class_stem(root: Path, file_path: Path, name: str) -> bool:
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
        owner = FlextInfraUtilitiesProjectDiscovery.nearest_project_root(
            root, file_path
        )
        if owner is None:
            msg = f"project owner is unresolved: {file_path}"
            raise ValueError(msg)
        layout = FlextInfraUtilitiesCodegenNamespace.layout(owner)
        if layout is None:
            msg = f"project layout is unresolved: {owner}"
            raise ValueError(msg)
        prefix = FlextInfraUtilitiesCodegenNamespace.project_prefix(
            file_path,
            project_layout=layout,
        )
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

    @classmethod
    def _path_layers(cls, path: Path) -> frozenset[str]:

        order = frozenset(config.Infra.tooling.lazy_init.import_layer_order)
        stems = {
            part.removeprefix("_").removesuffix(c.Infra.EXT_PYTHON)
            for part in (path.name, *(parent.name for parent in path.parents))
        }
        families = cls._file_families(path) if path.is_file() else frozenset[str]()
        return families | (order & stems)

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
