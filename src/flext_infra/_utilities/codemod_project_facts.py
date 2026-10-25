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
from collections.abc import Mapping
from importlib.util import find_spec
from pathlib import Path

from flext_cli import u
from packaging.utils import canonicalize_name

from flext_infra import FlextInfraConfig, c, config, m, p, t
from flext_infra._utilities import FlextInfraUtilitiesWorkspaceSnapshot
from flext_infra._utilities._rope_analysis.exports import (
    FlextInfraUtilitiesRopeAnalysisExports,
)
from flext_infra._utilities._rope_analysis.sourcescan import (
    FlextInfraUtilitiesRopeAnalysisSourceScan,
)
from flext_infra._utilities._rope_source_bases_runtime import (
    FlextInfraUtilitiesRopeSourceBasesRuntime,
)
from flext_infra._utilities._semantic_cutover.declaration_payload import (
    FlextInfraUtilitiesDeclarationPayload,
)
from flext_infra._utilities.codemod_native_package_utilities import (
    FlextInfraUtilitiesCodemodNativePackageUtilities,
)
from flext_infra._utilities.codemod_native_utilities import (
    FlextInfraUtilitiesCodemodNativeUtilities,
)
from flext_infra._utilities.codemod_project import FlextInfraUtilitiesCodemodProject
from flext_infra._utilities.codemod_rules import FlextInfraUtilitiesCodemodRules
from flext_infra._utilities.codemod_scopes import FlextInfraUtilitiesCodemodScopes
from flext_infra._utilities.facade_members import FlextInfraUtilitiesFacadeMembers
from flext_infra._utilities.import_law import FlextInfraUtilitiesImportLaw
from flext_infra._utilities.namespace import FlextInfraUtilitiesCodegenNamespace
from flext_infra._utilities.pyproject import FlextInfraUtilitiesPyproject
from flext_infra._utilities.rope_core import FlextInfraUtilitiesRopeCore


class FlextInfraUtilitiesCodemodProjectFacts:
    """Derive the stable project-fact utilities and file scopes rules reference."""

    @classmethod
    def codemod_facade_package_utilities(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> t.MappingKV[str, t.JsonMapping]:
        """Facade package: the own package or a reached package publishing aliases.

        Returns:
            The ``facade-package`` utility rule of the project.

        """
        return {
            c.Infra.CODEMOD_FACADE_PACKAGE_UTILITY: (
                FlextInfraUtilitiesCodemodNativeUtilities.codemod_module_names_rule(
                    FlextInfraUtilitiesCodemodNativePackageUtilities.codemod_facade_packages(
                        snapshot, project
                    )
                )
            ),
        }

    @classmethod
    def codemod_alias_utilities(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> t.MappingKV[str, t.JsonMapping]:
        """Runtime aliases: the own package's, and each imported package's.

        ``local-alias`` matches a name the own package publishes as a runtime
        alias. ``runtime-alias`` matches an imported name that is a runtime
        alias of the very package its import statement names.

        Returns:
            The ``local-alias`` and ``runtime-alias`` utility rules.

        """
        aliases = cls._reached_facade_aliases(snapshot, project)
        own = FlextInfraUtilitiesPyproject.project_package_name(project.absolute())
        return {
            c.Infra.CODEMOD_LOCAL_ALIAS_UTILITY: cls._fact_exact_names(
                tuple(aliases[own])
            ),
            c.Infra.CODEMOD_RUNTIME_ALIAS_UTILITY: cls._fact_imported_from(aliases),
        }

    @classmethod
    def codemod_imported_export_utilities(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> t.MappingKV[str, t.JsonMapping]:
        """Package export: an imported name its import's root package declares.

        Returns:
            The ``package-export`` utility rule of the project.

        """
        exports: dict[str, frozenset[str]] = {}
        for (
            package
        ) in FlextInfraUtilitiesCodemodNativePackageUtilities.codemod_facade_packages(
            snapshot, project
        ):
            spec = find_spec(package)
            if spec is None or spec.origin is None:
                continue
            exports[package] = frozenset(
                FlextInfraUtilitiesRopeAnalysisExports.public_export_names_source(
                    Path(spec.origin).read_text(encoding=c.DEFAULT_ENCODING)
                )
            )
        return {
            c.Infra.CODEMOD_PACKAGE_EXPORT_UTILITY: cls._fact_imported_from(exports)
        }

    @classmethod
    def codemod_compose_module_utilities(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> t.MappingKV[str, t.JsonMapping]:
        """Compose module: ``<package>.<leaf>`` for a canonical family leaf.

        The own package composes a leaf it declares beside its family
        packages; a runtime-closure package composes every canonical leaf, the
        family shape being the fleet-wide contract.

        Returns:
            The ``compose-module`` utility rule of the project.

        """
        del snapshot
        root = project.absolute()
        own = FlextInfraUtilitiesPyproject.project_package_name(root)
        layout = FlextInfraUtilitiesCodegenNamespace.layout(root)
        leaves = c.Infra.FAMILY_COMPOSE_MODULES
        runtime = FlextInfraUtilitiesCodemodNativeUtilities.codemod_runtime_modules
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
    ) -> t.MappingKV[str, t.StrTuple]:
        """File scopes: layer-zero modules, facade modules and family members.

        ``layer-zero`` holds the modules the import law ranks layer zero;
        ``facade-module`` the modules whose own ``__all__`` declares a facade
        letter; ``facade-family-<letter>`` the modules of that letter's family: the
        letters a module's own ``__all__`` declares, and those of the facade
        module of every private family package it lives in. The letter
        vocabulary is the tooling import-layer order; no file name is mapped
        to a letter. ``private-family-<family>`` groups the modules of each
        private family package.

        Returns:
            Project-relative POSIX paths keyed by scope selector.

        """
        root = project.resolve()
        letters = frozenset(config.Infra.tooling.lazy_init.import_layer_order)
        files = FlextInfraUtilitiesWorkspaceSnapshot.workspace_python_files(
            snapshot, root
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
                FlextInfraUtilitiesCodemodNativePackageUtilities.codemod_layer_zero_files(
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
            **cls._private_family_scopes(snapshot, root),
        }

    @staticmethod
    def _source_exports(
        snapshot: p.Infra.WorkspaceSnapshot,
        files: t.SequenceOf[Path],
        module: Path,
    ) -> frozenset[str]:
        """Read the names one member module's own ``__all__`` publishes.

        Returns:
            The published names; none for a path the member does not list.

        """
        if module not in files:
            return frozenset()
        return frozenset(
            FlextInfraUtilitiesRopeAnalysisExports.public_export_names_source(
                FlextInfraUtilitiesWorkspaceSnapshot.workspace_source(
                    snapshot, module
                ).text
            )
        )

    @classmethod
    def codemod_layout_scopes(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> t.MappingKV[str, t.StrTuple]:
        """File scopes of the project's package layout verdicts.

        ``lacks-layer-<layer>`` holds every package ``__init__.py`` whose
        package provides no such layer (no module declaring the letter, no
        ``<layer>``/``_<layer>`` module, no ``<layer>`` subpackage);
        ``family-without-base`` the modules of a private family package that
        has no ``base.py``; ``family-base-file`` each family package's ``base.py``
        beside the package root; ``family-role`` the modules the import law
        gives the family role; ``class-stem-<stems>`` the modules whose class
        must carry one of those stems; ``incomplete-composition-<namespace>``
        the facade modules whose nested ``namespace`` misses a class its
        family package declares.

        Returns:
            Project-relative POSIX paths keyed by scope selector.

        Raises:
            ValueError: If the project layout is unresolved.

        """
        root = project.resolve()
        layout = FlextInfraUtilitiesCodegenNamespace.layout(root)
        if layout is None:
            msg = f"project layout is unresolved: {root}"
            raise ValueError(msg)
        order = tuple(config.Infra.tooling.lazy_init.import_layer_order)
        files = FlextInfraUtilitiesWorkspaceSnapshot.workspace_python_files(
            snapshot, root
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

        # The fixed selectors and every layer's lack are published, empty or
        # not, so a rule may name any of them.
        scopes: dict[str, list[str]] = {
            c.Infra.CODEMOD_FAMILY_WITHOUT_BASE_SCOPE: [],
            c.Infra.CODEMOD_FAMILY_BASE_SCOPE: [],
            **{
                f"{c.Infra.CODEMOD_LACKS_LAYER_SCOPE_PREFIX}{layer}": []
                for layer in order
            },
        }
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
            FlextInfraUtilitiesCodemodNativePackageUtilities.codemod_role_files(
                snapshot, root, (c.Infra.IMPORT_LAW_FAMILY_ROLE,)
            )
        )
        return {
            selector: tuple(sorted(found)) for selector, found in sorted(scopes.items())
        }

    @staticmethod
    def _missing_layers(
        path: Path, order: t.StrSequence, aliases: frozenset[str]
    ) -> t.StrSequence:
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
        layout: m.Infra.RopeProjectLayout,
        namespaces: t.StrSequence,
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
        files: t.SequenceOf[Path],
        path: Path,
        order: t.StrSequence,
    ) -> t.StrSequence:
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
            name for init in inits for name in cls._source_exports(snapshot, files, init)
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
    ) -> t.StrSequence:
        """Name the nested namespaces of a facade module its family misses.

        Returns:
            Each nested class of a top-level class that does not compose
            every class its family package declares; none for a module that
            declares no facade letter.

        """
        if not facade:
            return ()
        tree = FlextInfraUtilitiesWorkspaceSnapshot.workspace_module_tree(
            snapshot, path
        )
        return tuple(
            nested.name
            for top in tree.body
            if isinstance(top, ast.ClassDef)
            for nested in top.body
            if isinstance(nested, ast.ClassDef)
            and not FlextInfraUtilitiesCodemodProject.composes_family_package(
                path, nested.name
            )
        )

    @classmethod
    def codemod_declaration_scopes(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> t.MappingKV[str, t.StrTuple]:
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
            and (located := law.import_namespace(root, path)) is not None
        }
        # (relative path, qualified class, selector) per asked class.
        questions: list[t.Triple[str, str, str]] = []
        family = cls._family_files(snapshot, root)
        for module, (path, text) in sources.items():
            relative = path.relative_to(root).as_posix()
            if relative not in family:
                continue
            in_models = law.module_import_layer(module) == models_layer
            for top in FlextInfraUtilitiesRopeAnalysisSourceScan.parsed_module(
                text
            ).body:
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
        with FlextInfraUtilitiesRopeCore.open_project(root) as rope:
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
            FlextInfraUtilitiesCodemodNativePackageUtilities.codemod_role_files(
                snapshot, root, (c.Infra.IMPORT_LAW_FAMILY_ROLE,)
            )
        )

    @classmethod
    def _nested_classes(
        cls, owner: ast.ClassDef, prefix: str
    ) -> t.SequenceOf[t.StrPair]:
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
    ) -> t.MappingKV[str, t.JsonMapping]:
        """Utilities the packaged catalog requests by a parametrized identity.

        ``library-member-owner-<library>-<letter>`` matches a public member of
        that library whose runtime object the letter owns, by the facade
        member policy. ``generic-specialization`` matches an alias name the
        ``p`` facade of a reached facade package declares as a specialization
        of the same-named ``t`` generic.

        Returns:
            Every requested utility keyed by its identity.

        """
        utilities: dict[str, t.JsonMapping] = {}
        prefix = c.Infra.CODEMOD_LIBRARY_MEMBER_OWNER_UTILITY_PREFIX
        for identity in cls._catalog_references(prefix):
            library, _separator, letter = identity.removeprefix(prefix).rpartition("-")
            utilities[identity] = cls._fact_exact_names(
                FlextInfraUtilitiesFacadeMembers.library_members_owned_by(
                    library, letter
                )
            )
        if cls._catalog_references(c.Infra.CODEMOD_GENERIC_SPECIALIZATION_UTILITY):
            utilities[c.Infra.CODEMOD_GENERIC_SPECIALIZATION_UTILITY] = (
                cls._fact_exact_names(cls._specialized_aliases(snapshot, project))
            )
        return utilities

    @classmethod
    def codemod_implementation_scopes(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> t.MappingKV[str, t.StrTuple]:
        """File scopes of the implementation closures the catalog requests.

        ``implementation-owner-<module> <primitive>`` holds the project's
        modules in the native implementation closure of that public
        primitive: only the project that owns the primitive's package has any.

        Returns:
            Project-relative POSIX paths keyed by scope selector.

        """
        root = project.absolute()
        own = FlextInfraUtilitiesPyproject.project_package_name(root)
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
            module, _separator, primitive = selector.removeprefix(prefix).partition(
                " "
            )
            closure = (
                FlextInfraUtilitiesCodemodProject.implementation_owner_modules(
                    snapshot.engine,
                    m.Infra.CodemodPrimitiveOwner(arg=(module, primitive)),
                    {},
                )
            )
            scopes[selector] = tuple(
                sorted(
                    path.resolve().relative_to(root.resolve()).as_posix()
                    for path in closure
                    if path.resolve().is_relative_to(root.resolve())
                )
            )
        return scopes

    @staticmethod
    def _specialized_aliases(
        snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> t.StrSequence:
        """Name the ``p`` aliases that specialize the same-named ``t`` generic.

        Returns:
            The specialized alias names across the reached facade packages.

        """
        packages = (
            FlextInfraUtilitiesCodemodNativePackageUtilities.codemod_facade_packages
        )
        return tuple(
            sorted({
                name
                for package in packages(snapshot, project)
                for name in FlextInfraUtilitiesFacadeMembers.specialized_aliases(
                    package
                )
            })
        )

    @staticmethod
    def _catalog_references(prefix: str) -> t.StrSequence:
        """Collect the parametrized identities the packaged catalog references.

        A ``matches`` utility identity or a ``metadata.scope`` selector that
        starts with ``prefix`` is a request this module's producers answer.

        Returns:
            The sorted distinct requested identities.

        """
        catalog = (
            FlextInfraConfig.ssot_config_dir().parent / c.Infra.CODEMOD_CONFIG_RELPATH
        )
        documents: dict[Path, t.SequenceOf[t.JsonMapping]] = {}
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
    def _infra_catalog() -> t.Pair[
        t.SequenceOf[m.Infra.CodemodRule],
        t.MappingKV[Path, t.SequenceOf[t.JsonMapping]],
    ]:
        """Read the packaged catalog's validated rules and parsed documents.

        Returns:
            The catalog rules and every catalog file's documents.

        """
        catalog = (
            FlextInfraConfig.ssot_config_dir().parent / c.Infra.CODEMOD_CONFIG_RELPATH
        )
        documents: dict[Path, t.SequenceOf[t.JsonMapping]] = {}
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
        facts: m.Infra.CodemodScopeFacts,
    ) -> t.MappingKV[str, t.JsonMapping]:
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
        package = FlextInfraUtilitiesPyproject.project_package_name(root)
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
    def _private_family_scopes(
        snapshot: p.Infra.WorkspaceSnapshot, root: Path
    ) -> t.MappingKV[str, t.StrTuple]:
        """Group the project's modules by the private family package they belong to.

        A private family is a dotted module path up to its first
        ``_``-prefixed segment; its members are the modules inside that tree,
        the family package itself and its facade (the path with the
        underscore removed).

        Returns:
            Project-relative POSIX paths keyed by
            ``private-family-<dotted family>``.

        """
        modules: dict[str, str] = {}
        for path in FlextInfraUtilitiesWorkspaceSnapshot.workspace_python_files(
            snapshot, root
        ):
            located = FlextInfraUtilitiesImportLaw.import_namespace(root, path)
            if located is not None:
                modules[located[1]] = path.relative_to(root).as_posix()
        members: dict[str, set[str]] = {}
        for module, relative in modules.items():
            parts = module.split(".")
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
            f"{c.Infra.CODEMOD_PRIVATE_FAMILY_SCOPE_PREFIX}{family}": tuple(
                sorted(found)
            )
            for family, found in sorted(members.items())
        }

    @staticmethod
    def _reached_facade_aliases(
        snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> t.MappingKV[str, frozenset[str]]:
        """Read every reached facade package's runtime aliases.

        The own package's aliases come from its source layout; an installed
        package's from its generated lazy exports.

        Returns:
            Runtime aliases keyed by facade package.

        Raises:
            ValueError: If the own project layout is unresolved.

        """
        root = project.absolute()
        own = FlextInfraUtilitiesPyproject.project_package_name(root)
        layout = FlextInfraUtilitiesCodegenNamespace.layout(root)
        if layout is None:
            msg = f"project layout is unresolved: {root}"
            raise ValueError(msg)
        packages = (
            FlextInfraUtilitiesCodemodNativePackageUtilities.codemod_facade_packages
        )
        return {
            package: (
                frozenset(layout.runtime_aliases)
                if package == own
                else frozenset(u.runtime_alias_names(package))
            )
            for package in packages(snapshot, root)
        }

    @staticmethod
    def _fact_exact_names(names: t.StrSequence) -> t.JsonDict:
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
        cls, names: t.MappingKV[str, frozenset[str]]
    ) -> t.JsonMapping:
        """Match an imported name listed for the package its import names.

        Returns:
            A native rule pairing each name with its import statement's root.

        """
        branches: list[t.JsonValue] = [
            {
                **cls._fact_exact_names(tuple(found)),
                "inside": {
                    "kind": "import_from_statement",
                    "stopBy": "end",
                    "has": {
                        "field": "module_name",
                        "regex": rf"^{re.escape(package)}(?:\.|$)",
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
