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

import sys
from collections.abc import Mapping, MutableMapping
from functools import cache, lru_cache
from importlib.metadata import packages_distributions
from importlib.util import find_spec
from pathlib import Path
from types import MappingProxyType

from flext_cli import u
from packaging.utils import canonicalize_name

from flext_infra import c, config, m, p, r, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesCodemodBindingChain,
    FlextInfraUtilitiesCodemodRules,
    FlextInfraUtilitiesDeclarationPayload,
    FlextInfraUtilitiesImportLaw,
    FlextInfraUtilitiesProjectDiscovery,
    FlextInfraUtilitiesPyproject,
)
from flext_infra._utilities._codemod_project_import_graph import (
    FlextInfraUtilitiesCodemodProjectImportGraphMixin,
)
from flext_infra._utilities._codemod_project_snapshot import (
    FlextInfraUtilitiesCodemodProjectSnapshotMixin,
)
from flext_infra._utilities._rope_analysis.asthelpers import (
    FlextInfraUtilitiesRopeAnalysisAstHelpers,
)
from flext_infra._utilities._rope_analysis.exports import (
    FlextInfraUtilitiesRopeAnalysisExports,
)


class FlextInfraUtilitiesCodemodProject(
    FlextInfraUtilitiesCodemodBindingChain.FlextInfraUtilitiesCodemodBindingChain,
    FlextInfraUtilitiesCodemodProjectImportGraphMixin,
    FlextInfraUtilitiesCodemodProjectSnapshotMixin,
):
    """Evaluate rule context over project facts: packages, layers, graphs."""

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
            c.Infra.CodemodContextPredicate.PAYLOAD_DECLARATION,
            c.Infra.CodemodContextPredicate.PROTOCOL_DECLARATION,
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
        project: p.Infra.RopeProject | None = None,
        sources: t.MappingKV[Path, str] | None = None,
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
                c.Infra.CodemodContextPredicate.PAYLOAD_DECLARATION,
                c.Infra.CodemodContextPredicate.PROTOCOL_DECLARATION,
            }:
                if (
                    cls._declaration_condition_admits(
                        admission, condition, source, project, sources
                    )
                    is not condition.holds
                ):
                    return False
                continue
            if condition.predicate in {
                c.Infra.CodemodContextPredicate.RESOLVED_SYMBOL,
                c.Infra.CodemodContextPredicate.EMITTED_SYMBOL,
                c.Infra.CodemodContextPredicate.SAME_BINDING,
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
            own = FlextInfraUtilitiesPyproject.project_package_name(owner)
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


__all__: list[str] = ["FlextInfraUtilitiesCodemodProject"]
