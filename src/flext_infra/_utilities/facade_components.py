"""Facade component calls use their identity-proven composed public receiver.

Every facade letter, and every namespace class nested in it, composes family
component classes by MRO. A consumer that calls a method through the component
class instead of its composed facade namespace bypasses the facade alphabet.
The generated rules derive both receiver identities from native composition;
constructors and entity references retain their declared owners.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import re
import sys
from importlib.metadata import packages_distributions
from pathlib import Path

from flext_infra import c, config, p, t
from flext_infra._utilities import (
    FlextInfraUtilitiesFacadeMembers,
    FlextInfraUtilitiesProjectDiscovery,
    FlextInfraUtilitiesPyproject,
)
from flext_infra._utilities._codemod.codemod_native_package_utilities import (
    FlextInfraUtilitiesCodemodNativePackageUtilities,
)
from flext_infra._utilities._codemod.codemod_native_utilities import (
    FlextInfraUtilitiesCodemodNativeUtilities,
)
from flext_infra._utilities._rope.rope_runtime_modules import (
    FlextInfraUtilitiesRopeRuntimeModules,
)
from flext_infra._utilities._rope.rope_runtime_types import (
    FlextInfraUtilitiesRopeRuntimeTypes,
)
from flext_infra._utilities._semantic_cutover.declaration_payload import (
    FlextInfraUtilitiesDeclarationPayload,
)
from flext_infra._utilities.workspace_snapshot import (
    FlextInfraUtilitiesWorkspaceSnapshot,
)


class FlextInfraUtilitiesFacadeComponents:
    """Derive component-to-namespace references and render their relocation."""

    @classmethod
    def facade_component_references(
        cls, project: Path, *, source_project: p.Infra.RopeProject
    ) -> t.MappingKV[t.StrPair, frozenset[str]]:
        """Map each facade namespace to the component references it composes.

        A facade letter, or a namespace class nested in it, composes family
        component classes by MRO (``class Infra(FlextInfraConstantsPytest)``).
        Each public method a lineage component declares yields the exact
        ``Component.member`` text under ``letter`` or ``letter.Namespace``
        when the namespace binds the identical object; a reference two
        namespaces would both claim is ambiguous and never relocates.

        Returns:
            Component references keyed by the composing root package and the
            ``letter[.Namespace]`` target.

        """
        claims: dict[str, set[t.StrPair]] = {}
        for (base, member), targets in cls._component_claims(
            project, source_project=source_project
        ).items():
            reference = f"{base.get_name()}.{member}"
            claims.setdefault(reference, set()).update(
                (root, target) for root, target, _holder in targets
            )
        references: dict[t.StrPair, set[str]] = {}
        for reference, targets in claims.items():
            if len(targets) == 1:
                references.setdefault(next(iter(targets)), set()).add(reference)
        return {key: frozenset(found) for key, found in sorted(references.items())}

    @staticmethod
    def _facade_namespace_holders(
        root: str, letters: t.StrSequence, *, source_project: p.Infra.RopeProject
    ) -> t.SequenceOf[tuple[p.Infra.RopeClassObject, str]]:
        """List each facade letter and its recursively nested public namespaces.

        Returns:
            Each holder class with its ``letter[.Namespace]`` reference text.

        Raises:
            ValueError: A facade namespace has no native class scope.

        """
        holders: list[tuple[p.Infra.RopeClassObject, str]] = []
        for letter, facade in FlextInfraUtilitiesFacadeMembers.facade_source_classes(
            root, letters, source_project=source_project
        ).items():
            pending = [(facade, letter)]
            while pending:
                holder, target = pending.pop()
                holders.append((holder, target))
                if not FlextInfraUtilitiesRopeRuntimeTypes.py_class(holder):
                    message = f"facade namespace has no native scope: {root}.{target}"
                    raise ValueError(message)
                for nested in holder.get_scope().get_scopes():
                    if nested.get_kind() != "Class":
                        continue
                    value = FlextInfraUtilitiesRopeRuntimeTypes.require_class_object(
                        nested.pyobject, f"{root}.{target}"
                    )
                    if not value.get_name().startswith("_"):
                        pending.append((value, f"{target}.{value.get_name()}"))
        return tuple(holders)

    @staticmethod
    def _component_ancestors(
        holder: p.Infra.RopeClassObject,
    ) -> t.VariadicTuple[p.Infra.RopeClassObject]:
        """Traverse native ancestry without electing a second method order.

        Returns:
            The resulting ``t.VariadicTuple[p.Infra.RopeClassObject]``.

        """
        pending = list(FlextInfraUtilitiesDeclarationPayload.direct_bases(holder))
        seen: set[p.Infra.RopeClassObject] = set()
        ancestors: list[p.Infra.RopeClassObject] = []
        while pending:
            base = FlextInfraUtilitiesRopeRuntimeTypes.require_class_object(
                pending.pop(), "facade component ancestry"
            )
            if base in seen:
                continue
            seen.add(base)
            ancestors.append(base)
            pending.extend(FlextInfraUtilitiesDeclarationPayload.direct_bases(base))
        return tuple(ancestors)

    @classmethod
    def _composed_methods(
        cls,
        root: str,
        letters: t.StrSequence,
        holder: p.Infra.RopeClassObject,
        *,
        source_project: p.Infra.RopeProject,
    ) -> t.SequenceOf[t.Pair[p.Infra.RopeClassObject, str]]:
        """Keep component receivers only when their effective method is identical.

        Returns:
            The resulting ``t.SequenceOf[t.Pair[p.Infra.RopeClassObject, str]]``.

        """
        members = FlextInfraUtilitiesFacadeMembers
        facades = tuple(
            members.facade_source_classes(
                root, letters, source_project=source_project
            ).values()
        )
        holder_members = members.facade_source_members(
            holder, source_project=source_project
        )
        return tuple(
            (base, member)
            for base in cls._component_ancestors(holder)
            if (module := base.get_module()) is not None
            and (
                (
                    name
                    := FlextInfraUtilitiesProjectDiscovery.module_name_for_provider(
                        module, source_project=source_project
                    )
                )
                == root
                or name.startswith(f"{root}.")
            )
            and base not in facades
            for member, binding in members.facade_source_members(
                base, source_project=source_project
            ).items()
            if members.declared_by_package(
                base, member, root, source_project=source_project
            )
            and FlextInfraUtilitiesRopeRuntimeTypes.py_function(binding.get_object())
            and member in holder_members
            and FlextInfraUtilitiesRopeRuntimeModules.same_name(
                holder_members[member], binding
            )
        )

    @classmethod
    def _component_claims(
        cls, project: Path, *, source_project: p.Infra.RopeProject
    ) -> t.MappingKV[
        t.Pair[p.Infra.RopeClassObject, str],
        t.SequenceOf[t.Triple[str, str, p.Infra.RopeClassObject]],
    ]:
        """Retain native receiver identities while discovering public composition.

        Returns:
            The resulting ``t.MappingKV[t.Pair[p.Infra.RopeClassObject, str],
                t.SequenceOf[t.Triple[str, str, p.Infra.RopeClassObject]]]``.

        """
        package = FlextInfraUtilitiesPyproject.project_package_name(project)
        letters = sorted(set(config.Infra.tooling.facade_members.owners.values()))
        claims: dict[
            t.Pair[p.Infra.RopeClassObject, str],
            list[t.Triple[str, str, p.Infra.RopeClassObject]],
        ] = {}
        for root in FlextInfraUtilitiesFacadeMembers.facade_member_lineage(
            package, letters, source_project=source_project
        ):
            for holder, target in cls._facade_namespace_holders(
                root, letters, source_project=source_project
            ):
                for identity in cls._composed_methods(
                    root, letters, holder, source_project=source_project
                ):
                    claims.setdefault(identity, []).append((root, target, holder))
        return claims

    @staticmethod
    def _component_facade(value: p.Infra.RopeClassObject) -> bool:
        """Recognize a sibling facade backed by its native private child domain.

        Returns:
            The resulting ``bool``.

        """
        module = value.get_module()
        resource = None if module is None else module.get_resource()
        return (
            resource is not None
            and not resource.is_folder()
            and resource.parent.has_child(f"_{Path(resource.real_path).stem}")
        )

    @classmethod
    def _component_calls(
        cls,
        module: p.Infra.RopePyModule,
        claims: t.MappingKV[
            t.Pair[p.Infra.RopeClassObject, str],
            t.SequenceOf[t.Triple[str, str, p.Infra.RopeClassObject]],
        ],
    ) -> t.SequenceOf[t.Triple[ast.Attribute, str, str]]:
        """Prove both the imported component and its lexical facade receiver.

        Returns:
            The resulting ``t.SequenceOf[t.Triple[ast.Attribute, str, str]]``.

        Raises:
            TypeError: If component consumer has no native module tree.
            ValueError: If component method has competing bound facades; or if component
                method has no native source segment.

        """
        tree = module.get_ast()
        if not isinstance(tree, ast.Module):
            message = (
                f"component consumer has no native module tree: {module.get_name()}"
            )
            raise TypeError(message)
        bases = {
            id(node)
            for declaration in ast.walk(tree)
            if isinstance(declaration, ast.ClassDef)
            for base in declaration.bases
            for node in ast.walk(base)
        }
        references: list[t.Triple[ast.Attribute, str, str]] = []
        for call in ast.walk(tree):
            if (
                not isinstance(call, ast.Call)
                or not isinstance(reference := call.func, ast.Attribute)
                or id(reference) in bases
            ):
                continue
            destination = cls._component_destination(module, reference, claims)
            if destination is None:
                continue
            text = ast.get_source_segment(module.source_code, reference)
            if text is None:
                message = "component method has no native source segment"
                raise ValueError(message)
            references.append((reference, text, destination))
        return tuple(references)

    @classmethod
    def _component_destination(
        cls,
        module: p.Infra.RopePyModule,
        reference: ast.Attribute,
        claims: t.MappingKV[
            t.Pair[p.Infra.RopeClassObject, str],
            t.SequenceOf[t.Triple[str, str, p.Infra.RopeClassObject]],
        ],
    ) -> str | None:
        """Elect an already bound facade for one native component call.

        Returns:
            The identity-proven destination, or none without a bound facade.

        Raises:
            ValueError: If the method has competing bound facade destinations.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        types = FlextInfraUtilitiesRopeRuntimeTypes
        offset = runtime.source_offset(module.source_code, reference)
        scope = module.get_source_binding_index().context_at(offset).environment
        receiver = runtime.resolve_symbol(scope, reference.value)
        if (
            receiver is None
            or not types.abstract_class(component := receiver.get_object())
            or cls._component_facade(component)
        ):
            return None
        targets = claims.get((component, reference.attr), ())
        original = runtime.resolve_symbol(scope, reference)
        if original is None or not types.py_function(original.get_object()):
            return None
        destinations = cls._bound_destinations(scope, reference, original, targets)
        if len(destinations) > 1:
            message = (
                "component method has competing bound facades: "
                f"{module.get_name()}:{ast.unparse(reference)}: "
                f"{sorted(destinations)}"
            )
            raise ValueError(message)
        return next(iter(destinations)) if destinations else None

    @staticmethod
    def _bound_destinations(
        scope: p.Infra.RopeScope,
        reference: ast.Attribute,
        original: p.Infra.RopePyName,
        targets: t.SequenceOf[t.Triple[str, str, p.Infra.RopeClassObject]],
    ) -> set[str]:
        """Retain effective native callable identities in the consumer scope.

        Returns:
            Bound facade calls resolving to the original native callable.

        """
        runtime = FlextInfraUtilitiesRopeRuntimeModules
        destinations: set[str] = set()
        for _root, target, holder in targets:
            public = runtime.resolve_symbol(scope, ast.parse(target, mode="eval").body)
            if public is None or public.get_object() is not holder:
                continue
            destination = f"{target}.{reference.attr}"
            actual = runtime.resolve_symbol(
                scope, ast.parse(destination, mode="eval").body
            )
            if actual is not None and runtime.same_name(original, actual):
                destinations.add(destination)
        return destinations

    @staticmethod
    def _consumer_module(
        engine: p.Infra.RopeProject, path: Path
    ) -> p.Infra.RopePyModule:
        """Load one native source module through the captured project owner.

        Returns:
            The source module authenticated by the captured project.

        Raises:
            TypeError: If the consumer is not a native source module.

        """
        resource = engine.get_file(
            path.relative_to(Path(engine.root.real_path)).as_posix()
        )
        module = FlextInfraUtilitiesRopeRuntimeTypes.require_parsed_module(
            engine.get_pymodule(resource, force_errors=True)
        )
        if not FlextInfraUtilitiesRopeRuntimeTypes.source_module(module):
            message = f"component consumer has no native source module: {path}"
            raise TypeError(message)
        return module

    @staticmethod
    def _call_witness(node: ast.Attribute, original: str, source: str) -> t.JsonDict:
        """Translate Python UTF-8 byte columns to ast-grep character ranges.

        Returns:
            The exact source-text and character-range witness for this call.

        Raises:
            ValueError: If the call lacks a complete native source position.

        """
        if node.end_lineno is None or node.end_col_offset is None:
            message = "component call has no complete native position"
            raise ValueError(message)
        lines = source.splitlines()
        return {
            "regex": f"^{re.escape(original)}$",
            "range": {
                "start": {
                    "line": node.lineno - 1,
                    "column": len(
                        lines[node.lineno - 1]
                        .encode("utf-8")[: node.col_offset]
                        .decode("utf-8")
                    ),
                },
                "end": {
                    "line": node.end_lineno - 1,
                    "column": len(
                        lines[node.end_lineno - 1]
                        .encode("utf-8")[: node.end_col_offset]
                        .decode("utf-8")
                    ),
                },
            },
        }

    @classmethod
    def _component_rule(
        cls,
        rule_id: str,
        relative: str,
        namespace: str,
        calls: t.SequenceOf[t.Triple[ast.Attribute, str, str]],
        source: str,
    ) -> t.JsonMapping:
        """Group native call witnesses by consumer file and public namespace.

        Returns:
            One declarative rule for the identity-proven calls and replacements.

        Raises:
            ValueError: If a source spelling has competing facade destinations.

        """
        witnesses: list[t.JsonValue] = []
        replacements: dict[str, str] = {}
        for node, original, destination in calls:
            witnesses.append(cls._call_witness(node, original, source))
            if original in replacements and replacements[original] != destination:
                message = (
                    "component spelling has competing namespace destinations: "
                    f"{relative}:{original}"
                )
                raise ValueError(message)
            replacements[original] = destination
        rewriters: list[t.JsonValue] = [
            {
                "id": f"to-{index}",
                "rule": {"regex": f"^{re.escape(original)}$"},
                "fix": destination,
            }
            for index, (original, destination) in enumerate(
                sorted(replacements.items())
            )
        ]
        return {
            "id": rule_id,
            "language": c.Infra.CODEMOD_PYTHON_LANGUAGE,
            "severity": "error",
            "files": [f"**/{relative}"],
            "rule": {
                "kind": "attribute",
                "pattern": "$REF",
                "inside": {"kind": "call", "field": "function"},
                "any": witnesses,
            },
            "rewriters": rewriters,
            "transform": {
                "RELOCATED": {
                    "rewrite": {
                        "source": "$REF",
                        "rewriters": [f"to-{index}" for index in range(len(rewriters))],
                    }
                }
            },
            "fix": "$RELOCATED",
            "message": (
                "Call the component method through its composed public "
                f"facade `{namespace}`."
            ),
        }

    @classmethod
    def codemod_facade_component_rules(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> t.MappingKV[str, t.JsonMapping]:
        """Render native-proven component calls through their bound public facade.

        Calls share one rule per consumer file and public namespace, with exact
        native call-range alternatives. Bindings elect both receivers before
        rendering; spelling alone never admits a shadowed name. Constructors,
        class bases and entity references remain unchanged.

        Returns:
            Rules for the identity-proven calls in the captured project sources.

        """
        root = project.absolute()
        claims = cls._component_claims(root, source_project=snapshot.engine)
        if not claims:
            return {}
        prefix = (
            f"{c.Infra.FACADE_COMPONENT_RELOCATE_SHAPE}"
            f"{c.Infra.CODEMOD_GENERATED_ID_SEPARATOR}"
            f"{FlextInfraUtilitiesPyproject.project_package_name(root)}"
        )
        rules: dict[str, t.JsonMapping] = {}
        for path in FlextInfraUtilitiesWorkspaceSnapshot.workspace_python_files(
            snapshot, root
        ):
            module = cls._consumer_module(snapshot.engine, path)
            groups: dict[str, list[t.Triple[ast.Attribute, str, str]]] = {}
            for witness in cls._component_calls(module, claims):
                groups.setdefault(witness[2].rpartition(".")[0], []).append(witness)
            for namespace, calls in sorted(groups.items()):
                rule_id = (
                    f"{prefix}{c.Infra.CODEMOD_GENERATED_ID_SEPARATOR}{len(rules)}"
                )
                rules[rule_id] = cls._component_rule(
                    rule_id,
                    path.relative_to(root).as_posix(),
                    namespace,
                    calls,
                    module.source_code,
                )
        return rules

    @classmethod
    def facade_library_prefixes(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> t.StrTuple:
        """Name every third-party distribution the project's imports resolve to.

        Each top-level module the project imports that is neither the standard
        library, the own package nor a FLEXT facade package is mapped to the
        installed distributions that provide it (``git`` resolves to
        ``gitpython``, so the capability prefix ``git_`` is not a library
        prefix). Nothing is listed: the set is the dependency declaration as
        installed.

        Returns:
            The normalized distribution names, sorted.

        """
        root = project.absolute()
        native = FlextInfraUtilitiesCodemodNativePackageUtilities
        known = {
            *sys.stdlib_module_names,
            *native.codemod_facade_packages(snapshot, root),
            *FlextInfraUtilitiesCodemodNativeUtilities.codemod_own_package_names(root),
        }
        providers = packages_distributions()
        return tuple(
            sorted({
                distribution.lower().replace("-", "_").replace(".", "_")
                for module in native.codemod_imported_top_modules(snapshot, root)
                if module not in known and not module.startswith("_")
                for distribution in providers.get(module, ())
            })
        )

    @classmethod
    def codemod_library_member_name_rules(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> t.MappingKV[str, t.JsonMapping]:
        """Render the one rule banning a library-prefixed facade member.

        A facade export is prefixed by its capability (``git_``,
        ``refactor_``, ``workspace_``), never by the third-party library that
        implements it (``rope_project``, ``RopeProject``, ``pytest_runner``):
        only the c/t/p/m/u families know the library (ADR-028; operator
        ruling 2026-10-25). The prefixes are the installed distributions of
        the project's imports (``facade_library_prefixes``). Detection-only:
        the rename map is produced from this scan and applied by the mass
        rename tooling with a deprecated-signature window.

        Returns:
            The single rule document keyed by its rule id, or nothing when the
            project imports no third-party library.

        """
        root = project.absolute()
        prefixes = cls.facade_library_prefixes(snapshot, root)
        if not prefixes:
            return {}
        snake = "|".join(re.escape(prefix) for prefix in prefixes)
        camel = "|".join(
            re.escape(prefix.replace("_", " ").title().replace(" ", ""))
            for prefix in prefixes
        )
        letters = "|".join(
            re.escape(letter)
            for letter in sorted(
                set(config.Infra.tooling.facade_members.owners.values())
            )
        )
        package = FlextInfraUtilitiesPyproject.project_package_name(root)
        rule_id = (
            f"{c.Infra.FACADE_LIBRARY_MEMBER_SHAPE}"
            f"{c.Infra.CODEMOD_GENERATED_ID_SEPARATOR}{package}"
        )
        return {
            rule_id: {
                "id": rule_id,
                "language": c.Infra.CODEMOD_PYTHON_LANGUAGE,
                "severity": "error",
                "rule": {
                    "kind": "attribute",
                    "regex": rf"^(?:{letters})\.",
                    "has": {
                        "field": "attribute",
                        "regex": rf"^(?:(?:{snake})(?:_|$)|(?:{camel})(?:[A-Z]|$))",
                    },
                },
                "message": (
                    "Facade member prefixed by a library name: export it under "
                    "its capability prefix instead."
                ),
            }
        }


__all__: list[str] = ["FlextInfraUtilitiesFacadeComponents"]
