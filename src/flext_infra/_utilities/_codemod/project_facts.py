"""Project facts every catalog rule reads natively, by stable identity.

A catalog rule whose meaning depends on the project it scans (which packages
publish facades, which aliases the own package binds, which modules compose
a family) references the fact through ``matches: <id>`` in its constraints.
Each producer here derives one such fact from its source of truth as a native
utility; the project's generated provider stages them under their stable ids,
so a native ``ast-grep scan`` of the stage reproduces every finding without
any admission after the scan. A fact that is a set of files (the layer-zero
modules, a facade family's members) is a file scope instead: the stage
writes it into the ``files``/``ignores`` of the catalog rule that names it
under ``metadata.scope``.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import re
import sys
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import cast

from packaging.utils import canonicalize_name

from flext_infra import FlextInfraConfig, c, config, m, p, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesFacadeMembers,
    FlextInfraUtilitiesImportLaw,
    FlextInfraUtilitiesPytest,
    FlextInfraUtilitiesWorkspaceSnapshot,
)
from flext_infra._utilities._codemod import (
    FlextInfraUtilitiesCodemodNative,
    FlextInfraUtilitiesCodemodNativePackage,
    FlextInfraUtilitiesCodemodProject,
    FlextInfraUtilitiesCodemodRules,
    FlextInfraUtilitiesCodemodScopes,
)
from flext_infra._utilities._pyproject import FlextInfraUtilitiesPyprojectConform
from flext_infra._utilities._rope import (
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeRuntime,
    FlextInfraUtilitiesRopeRuntimeTypes,
    FlextInfraUtilitiesRopeSourceBasesRuntime,
)
from flext_infra._utilities._semantic_cutover import (
    FlextInfraUtilitiesDeclarationPayload,
)


class FlextInfraUtilitiesCodemodProjectFacts:
    """Derive the stable project-fact utilities and file scopes rules reference."""

    @classmethod
    def codemod_facade_package_utilities(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> Mapping[str, t.JsonMapping]:
        """Facade package: the own package or a reached package publishing aliases.

        Returns:
            The ``facade-package`` utility rule of the project.

        """
        return {
            c.Infra.CODEMOD_FACADE_PACKAGE_UTILITY: (
                FlextInfraUtilitiesCodemodNative.codemod_module_names_rule(
                    FlextInfraUtilitiesCodemodNativePackage.codemod_facade_packages(
                        snapshot, project
                    )
                )
            ),
        }

    @classmethod
    def codemod_alias_utilities(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> Mapping[str, t.JsonMapping]:
        """Runtime aliases: the own package's, and each imported package's.

        ``local-alias`` matches a name the own package publishes as a runtime
        alias. ``runtime-alias`` matches an imported name that is a runtime
        alias of the very package its import statement names.
        Both identities remain present with empty facts for non-package roots.

        Returns:
            The ``local-alias`` and ``runtime-alias`` utility rules.

        """
        aliases = cls._reached_facade_aliases(snapshot, project)
        own = FlextInfraUtilitiesPyprojectConform.project_package_name(
            project.absolute()
        )
        return {
            c.Infra.CODEMOD_LOCAL_ALIAS_UTILITY: cls._fact_exact_names(
                tuple(aliases[own]) if own else ()
            ),
            c.Infra.CODEMOD_RUNTIME_ALIAS_UTILITY: cls._fact_imported_from(aliases),
        }

    @classmethod
    def codemod_imported_export_utilities(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> Mapping[str, t.JsonMapping]:
        """Package exports: what an import of a package's members may rebind to.

        Per-repository resolution law: a package's declared exports come from
        this project's own indexed tree only. A reached package whose tree
        lives in another repository resolves nowhere here and contributes no
        export fact; installed environments are never consulted, where
        divergent member libraries would leak into the rule.

        The import law (docs guide "Imports and family composition"): a
        public name is imported from a package whose generated initializer
        exports it. ``owning-package-export`` pairs each name with the exact
        package whose ``__all__`` declares it; ``package-published-import``
        marks the module path of an import statement that its parent package
        publishes entirely, the one fact the deep-import rewrite reads.

        Returns:
            The ``package-published-import`` and ``owning-package-export``
            utility rules of the project.

        """
        facts = FlextInfraUtilitiesCodemodNativePackage.codemod_package_export_facts(
            snapshot, project
        )
        return {
            c.Infra.CODEMOD_PACKAGE_PUBLISHED_IMPORT_UTILITY: (
                cls._fact_package_published_import(facts)
            ),
            c.Infra.CODEMOD_OWNING_PACKAGE_EXPORT_UTILITY: cls._fact_imported_from(
                {package: frozenset(names) for package, names in facts.exports.items()},
                exact=True,
            ),
        }

    @classmethod
    def _fact_package_published_import(
        cls, facts: p.Infra.CodemodPackageExportsFacts
    ) -> t.JsonMapping:
        """Match the module path a parent package publishes the whole import of.

        One branch per package that has an initializer: it matches the module
        path of a ``from <package>.<module> import ...`` statement when every
        imported name is in the package's published ``__all__`` and no sibling
        import in the same file from another module of that package imports
        an unpublished name. Both conditions are all-or-nothing, so the whole
        header of a package's members moves together or stays untouched. A
        package without an initializer publishes nothing and a child that is
        itself a package is a legal import target, so neither is a branch.

        Returns:
            A native rule over the module-path ``dotted_name`` node.

        """
        branches: list[t.JsonValue] = []
        for package, children in sorted(facts.modules.items()):
            published = tuple(
                name for name in facts.exports.get(package, ()) if name.isidentifier()
            )
            modules = tuple(
                f"{package}.{leaf}"
                for leaf in children
                if f"{package}.{leaf}" not in facts.exports
            )
            if not published or not modules:
                continue
            unpublished: t.JsonDict = {
                "any": [
                    {
                        "all": [
                            {"kind": "dotted_name"},
                            {
                                "not": {
                                    "inside": {
                                        "kind": "import_from_statement",
                                        "field": "module_name",
                                    }
                                }
                            },
                            {"not": cls._fact_exact_names(published)},
                        ]
                    },
                    {
                        "all": [
                            {"kind": "aliased_import"},
                            {
                                "not": {
                                    "has": {
                                        "field": "name",
                                        **cls._fact_exact_names(published),
                                    }
                                }
                            },
                        ]
                    },
                    {"kind": "wildcard_import"},
                ]
            }
            branches.append({
                **cls._fact_exact_names(modules),
                "inside": {
                    "kind": "import_from_statement",
                    "field": "module_name",
                    "all": [
                        {"not": {"has": unpublished}},
                        {
                            "inside": {
                                "kind": "module",
                                "stopBy": "end",
                                "not": {
                                    "has": {
                                        "stopBy": "end",
                                        "kind": "import_from_statement",
                                        "all": [
                                            {
                                                "has": {
                                                    "field": "module_name",
                                                    **cls._fact_exact_names(modules),
                                                }
                                            },
                                            {"has": unpublished},
                                        ],
                                    }
                                },
                            }
                        },
                    ],
                },
            })
        if not branches:
            return {"regex": c.Infra.CODEMOD_NEVER_MATCH_REGEX}
        return {"kind": "dotted_name", "any": branches}

    @classmethod
    def codemod_compose_module_utilities(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> Mapping[str, t.JsonMapping]:
        """Compose module: ``<package>.<leaf>`` for a canonical family leaf.

        The own package composes a leaf it declares beside its family
        packages; a runtime-closure package composes every canonical leaf, the
        family shape being the fleet-wide contract.

        Returns:
            The ``compose-module`` utility rule of the project.

        """
        del snapshot
        root = project.absolute()
        own = FlextInfraUtilitiesPyprojectConform.project_package_name(root)
        layout = FlextInfraUtilitiesCodegenNamespace.layout(root)
        leaves = c.Infra.FAMILY_COMPOSE_MODULES
        runtime = FlextInfraUtilitiesCodemodNative.codemod_runtime_modules
        modules = {
            *(
                f"{own}.{leaf}"
                for leaf in leaves
                if layout is not None
                and (layout.package_dir / f"{leaf}{c.Infra.EXT_PYTHON}").is_file()
            ),
            *(f"{package}.{leaf}" for package in runtime(root) for leaf in leaves),
        }
        return {
            c.Infra.CODEMOD_COMPOSE_MODULE_UTILITY: cls._fact_exact_names(
                tuple(modules)
            )
        }

    @classmethod
    def codemod_file_scopes(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> Mapping[str, t.StrTuple]:
        """File scopes: layer-zero modules, facade modules and family members.

        ``layer-zero`` holds the modules the import law ranks layer zero;
        ``facade-module`` the modules whose own ``__all__`` declares a facade
        letter; ``facade-family-<letter>`` the modules of that letter's family: the
        letters a module's own ``__all__`` declares, and those of the facade
        module of every private family package it lives in. The letter
        vocabulary is the tooling import-layer order; no file name is mapped
        to a letter. ``private-family-<family>`` groups the modules of each
        private family package and ``top-package-<package>`` the modules of
        each top-level package.

        Returns:
            Project-relative POSIX paths keyed by scope selector. Fixed selectors
            remain present and empty when a non-package root has no source layout.

        """
        root = project.resolve()
        letters = frozenset(config.Infra.tooling.lazy_init.import_layer_order)
        files = frozenset(
            FlextInfraUtilitiesWorkspaceSnapshot.workspace_python_files(snapshot, root)
        )

        def declared(module: Path) -> frozenset[str]:
            return letters.intersection(cls._source_exports(snapshot, files, module))

        families: dict[str, list[str]] = {}
        facades: list[str] = []
        for path in files:
            relative = path.relative_to(root)
            own = declared(path)
            if own:
                facades.append(relative.as_posix())
            family_facades = (
                root
                / package.parent
                / f"{package.name.removeprefix('_')}{c.Infra.EXT_PYTHON}"
                for package in relative.parents
                if package.name.startswith("_") and not package.name.startswith("__")
            )
            for letter in own.union(*map(declared, family_facades)):
                families.setdefault(letter, []).append(relative.as_posix())
        return {
            c.Infra.CODEMOD_LAYER_ZERO_SCOPE: (
                FlextInfraUtilitiesCodemodNativePackage.codemod_layer_zero_files(
                    snapshot, root
                )
            ),
            c.Infra.CODEMOD_FACADE_MODULE_SCOPE: tuple(sorted(facades)),
            # Every letter's family is published, empty or not, so a rule may
            # name any of them.
            **{
                f"{c.Infra.CODEMOD_FAMILY_SCOPE_PREFIX}{letter}": tuple(
                    sorted(families.get(letter, ()))
                )
                for letter in sorted(letters)
            },
            **cls._module_group_scopes(snapshot, root),
        }

    @staticmethod
    def _source_exports(
        snapshot: p.Infra.WorkspaceSnapshot,
        files: frozenset[Path],
        module: Path,
    ) -> frozenset[str]:
        """Read the names one member module's own ``__all__`` publishes.

        Returns:
            The published names; none for a path the member does not list.

        """
        if module not in files:
            return frozenset()
        return frozenset(
            FlextInfraUtilitiesWorkspaceSnapshot.workspace_public_exports(
                snapshot, module
            )
        )

    @classmethod
    def codemod_layout_scopes(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> Mapping[str, t.StrTuple]:
        """File scopes of the project's package layout verdicts.

        ``lacks-layer-<layer>`` holds every package ``__init__.py`` whose
        package provides no such layer (no module declaring the letter, no
        ``<layer>``/``_<layer>`` module, no ``<layer>`` subpackage);
        ``family-without-base`` the modules of a private family package that
        has no ``base.py``; ``family-base-file`` each family package's ``base.py``
        beside the package root; ``composition-root`` the package-root
        composition module (``<package>/api.py``); ``family-role`` the modules
        the import law gives the family role; ``class-stem-<stems>`` the modules
        whose class
        must carry one of those stems; ``incomplete-composition-<namespace>``
        the facade modules whose nested ``namespace`` misses a class its
        family package declares.

        Returns:
            Project-relative POSIX paths keyed by scope selector.

        Raises:
            ValueError: If the project layout is unresolved.

        """
        order = tuple(config.Infra.tooling.lazy_init.import_layer_order)
        # Fixed selectors exist even when the project supplies no package layout.
        scopes: dict[str, list[str]] = {
            c.Infra.CODEMOD_FAMILY_WITHOUT_BASE_SCOPE: [],
            c.Infra.CODEMOD_FAMILY_BASE_SCOPE: [],
            c.Infra.CODEMOD_COMPOSITION_ROOT_SCOPE: [],
            c.Infra.CODEMOD_FAMILY_ROLE_SCOPE: [],
            **{
                f"{c.Infra.CODEMOD_LACKS_LAYER_SCOPE_PREFIX}{layer}": []
                for layer in order
            },
        }
        root = project.resolve()
        layout = FlextInfraUtilitiesCodegenNamespace.layout(root)
        if layout is None:
            if not (root / c.Infra.DEFAULT_SRC_DIR).is_dir():
                return dict.fromkeys(scopes, ())
            msg = f"project layout is unresolved: {root}"
            raise ValueError(msg)
        files = frozenset(
            FlextInfraUtilitiesWorkspaceSnapshot.workspace_python_files(snapshot, root)
        )

        def exported(module: Path) -> frozenset[str]:
            return cls._source_exports(snapshot, files, module)

        def family_package(directory: Path) -> bool:
            facade = (
                directory.parent
                / f"{directory.name.removeprefix('_')}{c.Infra.EXT_PYTHON}"
            )
            return (
                directory.name.startswith("_")
                and not directory.name.startswith("__")
                and bool(frozenset(order) & exported(facade))
            )

        namespaces = FlextInfraUtilitiesCodegenNamespace.repository_namespace_packages(
            root
        )
        for path in files:
            relative = path.relative_to(root)
            for selector in (
                *cls._missing_layers(
                    path,
                    order,
                    frozenset(
                        alias
                        for module in path.parent.glob(f"*{c.Infra.EXT_PYTHON}")
                        if module.name != c.Infra.INIT_PY
                        for alias in exported(module)
                    )
                    if path.name == c.Infra.INIT_PY
                    else frozenset(),
                ),
                *(
                    (c.Infra.CODEMOD_FAMILY_WITHOUT_BASE_SCOPE,)
                    if any(
                        not (
                            root / directory / c.Infra.IMPORT_LAW_FAMILY_BASE_FILE
                        ).is_file()
                        for directory in next(
                            (
                                (directory,)
                                for directory in relative.parents
                                if family_package(root / directory)
                            ),
                            (),
                        )
                    )
                    else ()
                ),
                *(
                    (c.Infra.CODEMOD_FAMILY_BASE_SCOPE,)
                    if path.name == c.Infra.IMPORT_LAW_FAMILY_BASE_FILE
                    and path.parent.parent == layout.package_dir
                    and family_package(path.parent)
                    else ()
                ),
                *(
                    (c.Infra.CODEMOD_COMPOSITION_ROOT_SCOPE,)
                    if path.name == c.Infra.API_PY and path.parent == layout.package_dir
                    else ()
                ),
                cls._class_stem_scope(path, root, layout, namespaces),
                *cls._family_peer_scope(snapshot, files, path, order),
                *(
                    f"{c.Infra.CODEMOD_INCOMPLETE_COMPOSITION_SCOPE_PREFIX}{name}"
                    for name in cls._incomplete_namespaces(
                        snapshot, path, facade=bool(frozenset(order) & exported(path))
                    )
                ),
            ):
                scopes.setdefault(selector, []).append(relative.as_posix())
        scopes[c.Infra.CODEMOD_FAMILY_ROLE_SCOPE] = list(
            FlextInfraUtilitiesCodemodNativePackage.codemod_role_files(
                snapshot, root, (c.Infra.IMPORT_LAW_FAMILY_ROLE,)
            )
        )
        return {
            selector: tuple(sorted(found)) for selector, found in sorted(scopes.items())
        }

    @staticmethod
    def _missing_layers(
        path: Path, order: Sequence[str], aliases: frozenset[str]
    ) -> Sequence[str]:
        """Name the layers the package an ``__init__.py`` opens does not provide.

        ``aliases`` are the letters the package's modules declare.

        Returns:
            One ``lacks-layer-<layer>`` selector per missing layer; none for
            any other module.

        """
        if path.name != c.Infra.INIT_PY:
            return ()
        package = path.parent
        return tuple(
            f"{c.Infra.CODEMOD_LACKS_LAYER_SCOPE_PREFIX}{layer}"
            for layer in order
            if layer not in aliases
            and not (package / f"{layer}{c.Infra.EXT_PYTHON}").is_file()
            and not (package / f"_{layer}{c.Infra.EXT_PYTHON}").is_file()
            and not (package / layer / c.Infra.INIT_PY).is_file()
        )

    @staticmethod
    def _class_stem_scope(
        path: Path,
        root: Path,
        layout: p.Infra.RopeProjectLayout,
        namespaces: Sequence[str],
    ) -> str:
        """Name the class-stem group of one module.

        A module of a declared namespace package or of the tests tree carries
        its surface-prefixed stem; elsewhere the bare stem also names
        scenario classes.

        Returns:
            The ``class-stem-<stems>`` selector, stems comma-separated.

        """
        prefix = FlextInfraUtilitiesCodegenNamespace.project_prefix(
            path, project_layout=layout
        )
        strict = path.relative_to(root).parts[0] in namespaces or path.is_relative_to(
            root / c.Infra.DIR_TESTS
        )
        stems = {prefix} if strict else {prefix, layout.class_stem}
        return f"{c.Infra.CODEMOD_CLASS_STEM_SCOPE_PREFIX}{','.join(sorted(stems))}"

    @classmethod
    def _family_peer_scope(
        cls,
        snapshot: p.Infra.WorkspaceSnapshot,
        files: frozenset[Path],
        path: Path,
        order: Sequence[str],
    ) -> Sequence[str]:
        """Name the family-peer group of one facade module.

        A family peer of a facade module is a class whose final CamelCase word
        is that of a class the module declares, or a class one of its family
        packages declares; the group key is that regex.

        Returns:
            The ``family-peer-<regex>`` selector of a facade module; none for
            any other module.

        """
        declared = cls._source_exports(snapshot, files, path)
        if not frozenset(order) & declared:
            return ()
        words = sorted({
            name[max(i for i, char in enumerate(name) if char.isupper()) :]
            for name in declared
            if name[:1].isupper()
        })
        inits = (
            path.parent / f"_{path.stem}" / c.Infra.INIT_PY,
            *(
                directory / c.Infra.INIT_PY
                for directory in path.parents
                if directory.name.startswith("_")
                and not directory.name.startswith("__")
            ),
        )
        names = sorted({
            name
            for init in inits
            for name in cls._source_exports(snapshot, files, init)
        })
        branches = (
            *((f"(?:{'|'.join(map(re.escape, words))})$",) if words else ()),
            *((f"^(?:{'|'.join(map(re.escape, names))})$",) if names else ()),
        )
        peer = "|".join(branches) if branches else c.Infra.CODEMOD_NEVER_MATCH_REGEX
        return (f"{c.Infra.CODEMOD_FAMILY_PEER_SCOPE_PREFIX}{peer}",)

    @staticmethod
    def _incomplete_namespaces(
        snapshot: p.Infra.WorkspaceSnapshot, path: Path, *, facade: bool
    ) -> Sequence[str]:
        """Name the nested namespaces of a facade module its family misses.

        Returns:
            Each nested class of a top-level class that does not compose
            every class its family package declares; none for a module that
            declares no facade letter.

        """
        if not facade:
            return ()
        module = FlextInfraUtilitiesRopeCore.resolve_pymodule(
            snapshot.engine,
            FlextInfraUtilitiesRopeRuntime.file_resource_at(snapshot.engine, path),
        )
        return tuple(
            nested.pyobject.get_name()
            for top in FlextInfraUtilitiesCodemodProject.declared_class_scopes(
                module.get_scope()
            )
            for nested in FlextInfraUtilitiesCodemodProject.declared_class_scopes(top)
            if not FlextInfraUtilitiesCodemodProject.composes_family_package(
                snapshot, path, nested.pyobject.get_name()
            )
        )

    @classmethod
    def codemod_declaration_scopes(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> Mapping[str, t.StrTuple]:
        """File scopes of the model and payload classes the family modules declare.

        ``model-class-<name>`` holds the family modules whose top-level class
        ``name`` reaches the model base through its native ancestry;
        ``payload-class-<name>`` those outside the models layer whose nested
        class ``name`` is a payload declaration (a model whose body only
        declares data); inside the models layer a nested payload is where it
        belongs, so it is never asked there. Every ancestry is answered by
        one source C3 resolver over the project's captured sources, so each
        ancestor is resolved once; only an admitted model's body is read
        through Rope. A class that declares no base derives only from
        ``object``, so only classes with bases are asked.

        Returns:
            Project-relative POSIX paths keyed by scope selector.

        """
        root = project.resolve()
        law = FlextInfraUtilitiesImportLaw
        snapshots = FlextInfraUtilitiesWorkspaceSnapshot
        models_layer = tuple(config.Infra.tooling.lazy_init.import_layer_order).index(
            c.Infra.FacadeFamily.M
        )
        sources = {
            located[1]: (path, snapshots.workspace_source(snapshot, path).text)
            for path in snapshots.workspace_python_files(snapshot, root)
            if path.suffix == c.Infra.EXT_PYTHON
            and (located := law.snapshot_import_namespace(snapshot, root, path))
            is not None
        }
        # (relative path, qualified class, selector) per asked class.
        questions: list[tuple[str, str, str]] = []
        family = cls._family_files(snapshot, root)
        for module, (path, _text) in sources.items():
            relative = path.relative_to(root).as_posix()
            if relative not in family:
                continue
            in_models = law.module_import_layer(module) == models_layer
            for top in snapshots.workspace_module_tree(snapshot, path).body:
                if not isinstance(top, ast.ClassDef):
                    continue
                if top.bases:
                    questions.append((
                        relative,
                        top.name,
                        f"{c.Infra.CODEMOD_MODEL_CLASS_SCOPE_PREFIX}{top.name}",
                    ))
                if not in_models:
                    questions.extend(
                        (
                            relative,
                            qualified,
                            f"{c.Infra.CODEMOD_PAYLOAD_CLASS_SCOPE_PREFIX}{name}",
                        )
                        for qualified, name in cls._nested_classes(top, top.name)
                    )
        modules = {
            path.relative_to(root).as_posix(): module
            for module, (path, _text) in sources.items()
        }
        scopes: dict[str, set[str]] = {}
        rope = snapshot.engine
        reached = FlextInfraUtilitiesRopeSourceBasesRuntime.source_class_reaches(
            rope,
            sources,
            tuple(
                m.Infra.SourceClassReference(
                    target=modules[relative],
                    attributes=tuple(qualified.split(".")),
                    qualified_base=f"{modules[relative]}.{qualified}",
                )
                for relative, qualified, _selector in questions
            ),
            tuple(
                m.Infra.SourceClassReference(
                    target=identity.rpartition(".")[0],
                    attributes=(identity.rpartition(".")[2],),
                    qualified_base=identity,
                )
                for identity in (
                    c.Infra.PYDANTIC_MODEL_IDENTITY,
                    c.Infra.PYDANTIC_SETTINGS_IDENTITY,
                )
            ),
        )
        for (relative, qualified, selector), anchors in zip(
            questions, reached, strict=True
        ):
            if c.Infra.PYDANTIC_MODEL_IDENTITY not in anchors:
                continue
            if selector.startswith(c.Infra.CODEMOD_PAYLOAD_CLASS_SCOPE_PREFIX) and (
                c.Infra.PYDANTIC_SETTINGS_IDENTITY in anchors
                or FlextInfraUtilitiesDeclarationPayload.payload_body(
                    rope, root / relative, qualified
                )
                is None
            ):
                continue
            scopes.setdefault(selector, set()).add(relative)
        return {
            selector: tuple(sorted(found)) for selector, found in sorted(scopes.items())
        }

    @staticmethod
    def _family_files(
        snapshot: p.Infra.WorkspaceSnapshot, root: Path
    ) -> frozenset[str]:
        """Name the project's facade family modules.

        Returns:
            Project-relative POSIX paths of the family modules.

        """
        return frozenset(
            FlextInfraUtilitiesCodemodNativePackage.codemod_role_files(
                snapshot, root, (c.Infra.IMPORT_LAW_FAMILY_ROLE,)
            )
        )

    @classmethod
    def _nested_classes(
        cls, owner: ast.ClassDef, prefix: str
    ) -> Sequence[tuple[str, str]]:
        """List every class with bases nested in a class body, outside functions.

        Returns:
            Each nested class's qualified and short name.

        """
        return tuple(
            found
            for nested in owner.body
            if isinstance(nested, ast.ClassDef)
            for found in (
                *(((f"{prefix}.{nested.name}", nested.name),) if nested.bases else ()),
                *cls._nested_classes(nested, f"{prefix}.{nested.name}"),
            )
        )

    @classmethod
    def codemod_requested_utilities(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> Mapping[str, t.JsonMapping]:
        """Utilities the packaged catalog requests by a parametrized identity.

        ``library-member-owner-<library>-<letter>`` matches a public member of
        that library whose runtime object the letter owns, by the facade
        member policy. ``generic-specialization`` matches an alias name the
        ``p`` facade of a reached facade package declares as a specialization
        of the same-named ``t`` generic. ``protocol-model-path`` matches a
        dotted path ``p`` publishes as a protocol and ``m`` as its model twin;
        ``model-sdk-type-name`` matches a library type name ``t`` owns that
        ``p`` or ``m`` re-spells.

        Returns:
            Every requested utility keyed by its identity.

        """
        utilities: dict[str, t.JsonMapping] = {}
        prefix = c.Infra.CODEMOD_LIBRARY_MEMBER_OWNER_UTILITY_PREFIX
        specialization = c.Infra.CODEMOD_GENERIC_SPECIALIZATION_UTILITY
        model_path = c.Infra.CODEMOD_PROTOCOL_MODEL_PATH_UTILITY
        sdk_type = c.Infra.CODEMOD_MODEL_SDK_TYPE_UTILITY
        # Every request family shares one catalog read.
        references = cls._catalog_references((
            prefix,
            specialization,
            model_path,
            sdk_type,
        ))
        requested: dict[str, list[str]] = {}
        selectors: list[tuple[str, str, str]] = []
        for identity in references:
            if not identity.startswith(prefix):
                continue
            library, _separator, letter = identity.removeprefix(prefix).rpartition("-")
            requested.setdefault(library, []).append(letter)
            selectors.append((identity, library, letter))
        members = {
            library: FlextInfraUtilitiesFacadeMembers.library_members_owned_by(
                library, letters, source_project=snapshot.engine
            )
            for library, letters in requested.items()
        }
        for identity, library, letter in selectors:
            utilities[identity] = cls._fact_exact_names(
                cls._published_members(library, letter, members[library][letter])
            )
        if any(identity.startswith(specialization) for identity in references):
            utilities[specialization] = cls._fact_exact_names(
                cls._specialized_aliases(snapshot, project)
            )
        if model_path in references:
            utilities[model_path] = cls._fact_protocol_model_paths(snapshot, project)
        if sdk_type in references:
            utilities[sdk_type] = cls._fact_model_sdk_type_names(snapshot, project)
        artifact_roots = config.Infra.codegen.exclusions.scenario_data_roots
        alternatives = "|".join(
            r"[/\\.]".join(re.escape(part) for part in Path(root).parts)
            for root in artifact_roots
        )
        utilities["artifact-root-reference"] = {
            "regex": (
                rf"""(?:^|["'/\\])(?:{alternatives})(?:[/\\.]|["'])"""
                if alternatives
                else c.Infra.CODEMOD_NEVER_MATCH_REGEX
            )
        }
        return utilities

    @staticmethod
    def _published_members(
        library: str, letter: str, classified: t.StrTuple
    ) -> t.StrTuple:
        """Keep the classified members that the library's published surface carries.

        The kind classification says which letter would own a member; the
        letter only publishes what its owner declares. For the function
        letter, flext-infra's ``u.Infra.<Library>`` surface is that owner, so
        a function the owner leaves unpublished (its name belongs to another
        member of the facade) is never a rewrite target. A library or letter
        without such an owner publishes by classification alone.

        Returns:
            The classified names the owner publishes, or all when none owns.

        """
        owner = FlextInfraUtilitiesPytest.Pytest
        function_letter = config.Infra.tooling.facade_members.owners[
            c.Infra.FacadeMemberKind.FUNCTION
        ]
        if letter != function_letter or library != owner.__name__.lower():
            return classified
        published = frozenset(name for name in dir(owner) if not name.startswith("_"))
        return tuple(name for name in classified if name in published)

    @classmethod
    def codemod_implementation_scopes(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> Mapping[str, t.StrTuple]:
        """File scopes of the implementation closures the catalog requests.

        ``implementation-owner-<module> <primitive>`` holds the project's
        modules in the native implementation closure of that public
        primitive: only the project that owns the primitive's package has any.

        Returns:
            Project-relative POSIX paths keyed by scope selector.

        """
        root = project.absolute()
        own = FlextInfraUtilitiesPyprojectConform.project_package_name(root)
        prefix = c.Infra.CODEMOD_IMPLEMENTATION_OWNER_SCOPE_PREFIX
        requested = cls._catalog_references(prefix)
        scopes: dict[str, t.StrTuple] = {}
        owned = [
            selector
            for selector in requested
            if selector.removeprefix(prefix).partition(" ")[0].partition(".")[0] == own
        ]
        for selector in requested:
            scopes[selector] = ()
        if not owned:
            return scopes
        for selector in owned:
            module, _separator, primitive = selector.removeprefix(prefix).partition(" ")
            closure = FlextInfraUtilitiesCodemodProject.implementation_owner_modules(
                snapshot.engine,
                m.Infra.CodemodPrimitiveOwner(arg=(module, primitive)),
            )
            scopes[selector] = tuple(
                sorted(
                    path.resolve().relative_to(root.resolve()).as_posix()
                    for path in closure
                    if path.resolve().is_relative_to(root.resolve())
                )
            )
        return scopes

    @classmethod
    def _fact_protocol_model_paths(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> t.JsonMapping:
        """Match a dotted path ``p`` publishes as a protocol and ``m`` as its model.

        A protocol member is structural and never constructs; the model at the
        same path in the same facade package is the constructor. The fact is
        proven per reached facade package from the native source of both
        letters: a path counts only when no reached package publishes the
        protocol without a model at that path, so a rewrite never guesses.
        Both letters spell the same twin, so one fact serves the rewrite toward
        the model (a construction names ``m``) and toward the protocol (a type
        position names ``p``).

        Returns:
            A native ``regex`` rule over the text of a ``p``- or ``m``-rooted
            dotted path.

        """
        letters = (c.Infra.FacadeFamily.P, c.Infra.FacadeFamily.M)
        project_source = snapshot.engine
        resolver_factory = (
            FlextInfraUtilitiesRopeSourceBasesRuntime.source_member_resolver_factory(
                project_source,
                sources=FlextInfraUtilitiesWorkspaceSnapshot.project_captured_sources(
                    project_source
                ),
            )
        )
        modeled: set[str] = set()
        unmodeled: set[str] = set()
        for package in FlextInfraUtilitiesCodemodNativePackage.codemod_facade_packages(
            snapshot, project
        ):
            facades = FlextInfraUtilitiesFacadeMembers.facade_source_classes(
                package, letters, source_project=project_source
            )
            protocols, models = (facades.get(letter) for letter in letters)
            if protocols is None:
                continue
            for path, model, orphan in cls._facade_class_pairs(protocols, models):
                if orphan or (
                    model is not None
                    and (
                        FlextInfraUtilitiesFacadeMembers.class_kind(
                            model,
                            resolver_factory=resolver_factory,
                            source_project=project_source,
                        )
                        is c.Infra.FacadeMemberKind.MODEL
                    )
                ):
                    modeled.add(path)
                else:
                    unmodeled.add(path)
        listed = sorted(modeled - unmodeled)
        if not listed:
            return {"regex": c.Infra.CODEMOD_NEVER_MATCH_REGEX}
        alternatives = "|".join(re.escape(path) for path in listed)
        roots = "|".join(re.escape(letter) for letter in letters)
        return {"regex": rf"^(?:{roots})\.(?:{alternatives})$"}

    @classmethod
    def _fact_model_sdk_type_names(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> t.JsonMapping:
        """Match a library type name ``t`` owns that ``p`` or ``m`` re-spells.

        The ``t`` family declares each library type once, as an alias of the
        library object (``type ConfigDict = pydantic.ConfigDict``); a type
        position reads that alias, never the protocol or model letter that
        re-publishes the name. A name counts when a reached facade package's
        ``t`` publishes an alias whose native origin lies in a module that is
        neither the standard library nor a reached FLEXT facade package, and
        the same package's ``p`` or ``m`` publishes the same name. An alias of
        a first-party type, of a union or of a standard-library generic stays
        with its own twin. The set is read from the native source of the
        letters, never listed.

        Returns:
            A native ``regex`` rule over the text of a ``p``- or ``m``-rooted
            library type name.

        """
        owner = c.Infra.FacadeFamily.T
        spellings = (c.Infra.FacadeFamily.P, c.Infra.FacadeFamily.M)
        project_source = snapshot.engine
        packages = FlextInfraUtilitiesCodemodNativePackage.codemod_facade_packages(
            snapshot, project
        )
        first_party = frozenset((
            *sys.stdlib_module_names,
            *config.Infra.tooling.lazy_init.stdlib_backports,
            *packages,
        ))
        names: set[str] = set()
        for package in packages:
            facades = FlextInfraUtilitiesFacadeMembers.facade_source_classes(
                package, (owner, *spellings), source_project=project_source
            )
            typings = facades.get(owner)
            if typings is None:
                continue
            respelled = {
                name
                for letter in spellings
                if letter in facades
                for name in FlextInfraUtilitiesFacadeMembers.facade_source_members(
                    facades[letter], source_project=project_source
                )
            }
            published = FlextInfraUtilitiesFacadeMembers.facade_source_members(
                typings, source_project=project_source
            )
            names.update(
                name
                for name, binding in published.items()
                if name in respelled
                and cls._library_alias(
                    binding, source_project=project_source, first_party=first_party
                )
            )
        if not names:
            return {"regex": c.Infra.CODEMOD_NEVER_MATCH_REGEX}
        alternatives = "|".join(re.escape(name) for name in sorted(names))
        roots = "|".join(re.escape(letter) for letter in spellings)
        return {"regex": rf"^(?:{roots})\.(?:{alternatives})$"}

    @staticmethod
    def _library_alias(
        binding: p.Infra.RopePyName,
        *,
        source_project: p.Infra.RopeProject,
        first_party: frozenset[str],
    ) -> bool:
        """Prove a ``t`` member aliases one object a library declares.

        Returns:
            Whether the alias resolves natively to a module outside
            ``first_party``; a union, a missing alias or an unresolved origin
            is not a library alias.

        """
        runtime = FlextInfraUtilitiesRopeRuntime
        alias = runtime.annotation_alias_definition(binding)
        if alias is None:
            return False
        declaration, scope = alias
        if isinstance(declaration.value, ast.BinOp):
            return False
        origin = runtime.annotation_origin(source_project, declaration.value, scope)
        if origin is None:
            return False
        module, _line = runtime.definition_location(origin)
        return (
            module is not None
            and module.get_name().partition(".")[0] not in first_party
        )

    @classmethod
    def _facade_class_pairs(
        cls,
        protocols: p.Infra.RopeClassObject,
        models: p.Infra.RopeClassObject | None,
    ) -> Sequence[tuple[str, p.Infra.RopeClassObject | None, bool]]:
        """Pair every nested class of the protocol facade with its model path twin.

        The walk descends the published ``p`` namespaces; the ``m`` class at the
        same dotted path is resolved segment by segment, absent when any
        segment is not a class. A public ``m`` class whose name ``p`` does not
        publish at that level is an orphan path: ``p`` cannot resolve it, so a
        ``p`` construction there names the ``m`` class.

        Returns:
            Each dotted class path with its ``m`` class (or ``None``) and
            whether only ``m`` publishes it.

        """
        types = FlextInfraUtilitiesRopeRuntimeTypes
        pairs: list[tuple[str, p.Infra.RopeClassObject | None, bool]] = []
        pending: list[
            tuple[
                str,
                p.Infra.RopeClassObject,
                p.Infra.RopeClassObject | None,
                frozenset[int],
            ]
        ] = [("", protocols, models, frozenset({id(protocols)}))]
        while pending:
            prefix, protocol, model, lineage = pending.pop()
            twins = (
                cast(Mapping[str, p.Infra.RopePyName], {})
                if model is None
                else model.get_attributes()
            )
            published = protocol.get_attributes()
            pairs.extend(
                (f"{prefix}{name}", None, True)
                for name, twin in twins.items()
                if name not in published
                and not name.startswith("_")
                and types.abstract_class(twin.get_object())
            )
            for name, binding in published.items():
                nested = binding.get_object()
                if name.startswith("_") or not types.abstract_class(nested):
                    continue
                if id(nested) in lineage:
                    continue
                twin = twins.get(name)
                twin_class = None if twin is None else twin.get_object()
                path = f"{prefix}{name}"
                counterpart = twin_class if types.abstract_class(twin_class) else None
                pairs.append((path, counterpart, False))
                pending.append((
                    f"{path}.",
                    nested,
                    counterpart,
                    lineage | {id(nested)},
                ))
        return tuple(pairs)

    @staticmethod
    def _specialized_aliases(
        snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> Sequence[str]:
        """Name the ``p`` aliases that specialize the same-named ``t`` generic.

        Returns:
            The specialized alias names across the reached facade packages.

        """
        packages = FlextInfraUtilitiesCodemodNativePackage.codemod_facade_packages
        return tuple(
            sorted({
                name
                for package in packages(snapshot, project)
                for name in FlextInfraUtilitiesFacadeMembers.specialized_aliases(
                    package, source_project=snapshot.engine
                )
            })
        )

    @staticmethod
    def _catalog_references(prefix: str | tuple[str, ...]) -> Sequence[str]:
        """Collect the parametrized identities the packaged catalog references.

        A ``matches`` utility identity or a ``metadata.scope`` selector that
        starts with ``prefix`` is a request this module's producers answer.

        Returns:
            The sorted distinct requested identities.

        """
        catalog = (
            FlextInfraConfig.ssot_config_dir().parent / c.Infra.CODEMOD_CONFIG_RELPATH
        )
        documents: dict[Path, Sequence[t.JsonMapping]] = {}
        FlextInfraUtilitiesCodemodRules.codemod_catalog_rules(
            canonicalize_name(c.Infra.PKG_INFRA_UNDERSCORE),
            catalog,
            documents=documents,
        ).unwrap()
        found: set[str] = set()
        pending: list[t.JsonValue | t.JsonMapping] = [
            document for loaded in documents.values() for document in loaded
        ]
        while pending:
            value = pending.pop()
            if isinstance(value, str):
                if value.startswith(prefix):
                    found.add(value)
            elif isinstance(value, Mapping):
                pending.extend(value.values())
            elif isinstance(value, list):
                pending.extend(value)
        return tuple(sorted(found))

    @classmethod
    def codemod_partitioned_shapes(cls) -> t.StrTuple:
        """Name every catalog rule that declares ``metadata.scope.partition``.

        The partitioned renderer may emit exactly these shapes: the catalog's
        own declarations are their registry.

        Returns:
            The sorted ids of the partitioned catalog rules.

        """
        rules, _documents = cls._infra_catalog()
        return tuple(sorted(rule.id for rule in rules if rule.partitioned))

    @staticmethod
    def _infra_catalog() -> tuple[
        Sequence[p.Infra.CodemodRule],
        Mapping[Path, Sequence[t.JsonMapping]],
    ]:
        """Read the packaged catalog's validated rules and parsed documents.

        Returns:
            The catalog rules and every catalog file's documents.

        """
        catalog = (
            FlextInfraConfig.ssot_config_dir().parent / c.Infra.CODEMOD_CONFIG_RELPATH
        )
        documents: dict[Path, Sequence[t.JsonMapping]] = {}
        rules = FlextInfraUtilitiesCodemodRules.codemod_catalog_rules(
            canonicalize_name(c.Infra.PKG_INFRA_UNDERSCORE),
            catalog,
            documents=documents,
        ).unwrap()
        return rules, documents

    @classmethod
    def codemod_partitioned_rules(
        cls,
        snapshot: p.Infra.WorkspaceSnapshot,
        project: Path,
        facts: p.Infra.CodemodScopeFacts,
    ) -> Mapping[str, t.JsonMapping]:
        """Render every partitioned catalog rule over the project's file groups.

        A catalog rule whose verdict pairs a captured value with the file it
        is found in (a facade letter and the module's family, a private family
        and its members) declares ``metadata.scope.partition``; it is never
        elected as authored, and this renderer emits its per-group native
        documents for the project over the generation's file scopes.

        Returns:
            The generated documents keyed by rule id.

        """
        del snapshot
        root = project.absolute()
        rules, documents = cls._infra_catalog()
        scopes = facts.scopes
        package = FlextInfraUtilitiesPyprojectConform.project_package_name(root)
        utilities = FlextInfraUtilitiesCodemodRules.codemod_provider_utility_rules(
            FlextInfraConfig.ssot_config_dir().parent / c.Infra.CODEMOD_CONFIG_RELPATH
        )
        rendered: dict[str, t.JsonMapping] = {}
        for rule in rules:
            if not rule.partitioned:
                continue
            (document,) = (
                document
                for document in documents[rule.resource.resolve()]
                if document.get("id") == rule.id
            )
            rendered.update({
                identity: FlextInfraUtilitiesCodemodScopes.codemod_embedded_utilities(
                    native, utilities
                )
                for identity, native in (
                    FlextInfraUtilitiesCodemodScopes.codemod_partitioned_documents(
                        document, scopes, rule.id, package
                    ).items()
                )
            })
        return rendered

    @staticmethod
    def _module_group_scopes(
        snapshot: p.Infra.WorkspaceSnapshot, root: Path
    ) -> Mapping[str, t.StrTuple]:
        """Group the project's modules by private family and by top-level package.

        A private family is a dotted module path up to its first
        ``_``-prefixed segment; its members are the modules inside that tree,
        the family package itself and its facade (the path with the
        underscore removed). A top-level package groups every module whose
        dotted name starts with it.

        Returns:
            Project-relative POSIX paths keyed by
            ``private-family-<dotted family>`` and ``top-package-<package>``.

        """
        modules: dict[str, str] = {}
        for path in FlextInfraUtilitiesWorkspaceSnapshot.workspace_python_files(
            snapshot, root
        ):
            located = FlextInfraUtilitiesImportLaw.snapshot_import_namespace(
                snapshot, root, path
            )
            if located is not None:
                modules[located[1]] = path.relative_to(root).as_posix()
        members: dict[str, set[str]] = {}
        tops: dict[str, set[str]] = {}
        for module, relative in modules.items():
            parts = module.split(".")
            tops.setdefault(parts[0], set()).add(relative)
            private = next(
                (
                    index
                    for index, part in enumerate(parts)
                    if part.startswith("_") and not part.startswith("__")
                ),
                None,
            )
            if private is not None:
                members.setdefault(".".join(parts[: private + 1]), set()).add(relative)
        for family in tuple(members):
            *parent, package = family.split(".")
            facade = modules.get(".".join((*parent, package.removeprefix("_"))))
            if facade is not None:
                members[family].add(facade)
        return {
            **{
                f"{c.Infra.CODEMOD_PRIVATE_FAMILY_SCOPE_PREFIX}{family}": tuple(
                    sorted(found)
                )
                for family, found in sorted(members.items())
            },
            **{
                f"{c.Infra.CODEMOD_TOP_PACKAGE_SCOPE_PREFIX}{package}": tuple(
                    sorted(found)
                )
                for package, found in sorted(tops.items())
            },
        }

    @staticmethod
    def _reached_facade_aliases(
        snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> Mapping[str, frozenset[str]]:
        """Read every reached facade package's runtime aliases.

        The own package's aliases come from its source layout; an installed
        package's from its generated lazy exports.

        Returns:
            Runtime aliases keyed by facade package.

        Raises:
            ValueError: If the own project layout is unresolved.

        """
        root = project.absolute()
        own = FlextInfraUtilitiesPyprojectConform.project_package_name(root)
        layout = FlextInfraUtilitiesCodegenNamespace.layout(root)
        if layout is None:
            if not (root / c.Infra.DEFAULT_SRC_DIR).is_dir():
                return {}
            msg = f"project layout is unresolved: {root}"
            raise ValueError(msg)
        packages = FlextInfraUtilitiesCodemodNativePackage.codemod_facade_packages
        return {
            package: (
                frozenset(layout.runtime_aliases)
                if package == own
                else FlextInfraUtilitiesCodemodNativePackage.codemod_provider_aliases(
                    snapshot, package
                )
            )
            for package in packages(snapshot, root)
        }

    @staticmethod
    def _fact_exact_names(names: Sequence[str]) -> t.JsonDict:
        """Match exactly one of ``names``, or nothing when there is none.

        Returns:
            A native ``regex`` rule over the captured text.

        """
        listed = sorted(set(names))
        if not listed:
            return {"regex": c.Infra.CODEMOD_NEVER_MATCH_REGEX}
        alternatives = "|".join(re.escape(name) for name in listed)
        return {"regex": f"^(?:{alternatives})$"}

    @classmethod
    def _fact_imported_from(
        cls, names: Mapping[str, frozenset[str]], *, exact: bool = False
    ) -> t.JsonMapping:
        """Match an imported name listed for the package its import names.

        ``exact`` pairs the name with exactly that package; otherwise with
        the package and every module path below it.

        Returns:
            A native rule pairing each name with its import statement's package.

        """
        boundary = "$" if exact else r"(?:\.|$)"
        branches: list[t.JsonValue] = [
            {
                **cls._fact_exact_names(tuple(found)),
                "inside": {
                    "kind": "import_from_statement",
                    "stopBy": "end",
                    "has": {
                        "field": "module_name",
                        "regex": rf"^{re.escape(package)}{boundary}",
                    },
                },
            }
            for package, found in sorted(names.items())
            if found
        ]
        if not branches:
            return {"regex": c.Infra.CODEMOD_NEVER_MATCH_REGEX}
        return {"any": branches}


__all__: list[str] = ["FlextInfraUtilitiesCodemodProjectFacts"]
