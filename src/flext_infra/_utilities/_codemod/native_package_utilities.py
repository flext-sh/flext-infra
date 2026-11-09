"""Package-scope SSOT facts generated as native ast-grep utility rules.

The names a package publishes and the facade-family packages a project owns
are read statically: package initializers through the Griffe owner, family
directories from the facade-family declarations. No project module is
imported, so a tests-tier package is as valid a scope as the public package;
only a library the protocols family names is imported, to read whether the
named object is a protocol.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import builtins
import re
from collections.abc import Mapping, Sequence
from importlib import import_module
from pathlib import Path, PurePosixPath
from typing import is_protocol

from flext_cli import u

from flext_infra import FlextInfraConfig, c, config, m, p, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesFacadeMembers,
    FlextInfraUtilitiesImportLaw,
    FlextInfraUtilitiesProjectDiscovery,
    FlextInfraUtilitiesPythonModel,
    FlextInfraUtilitiesWorkspaceSnapshot,
)
from flext_infra._utilities._codemod import (
    FlextInfraUtilitiesCodemodNative,
    FlextInfraUtilitiesCodemodRules,
)
from flext_infra._utilities._pyproject import FlextInfraUtilitiesPyprojectConform
from flext_infra._utilities._rope import (
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeRuntime,
    FlextInfraUtilitiesRopeSourceBasesAliases,
)
from flext_infra._utilities._rope._analysis.rope_analysis_workspace import (
    FlextInfraUtilitiesRopeAnalysisWorkspace,
)


class FlextInfraUtilitiesCodemodNativePackage:
    """Derive package export and facade-family package utility rules."""

    @staticmethod
    def codemod_exact_names_rule(names: Sequence[str]) -> t.JsonDict:
        """Match a captured identifier that is exactly one of ``names``.

        Returns:
            A native ``regex`` rule, or the never-matching rule for no names.

        """
        if not names:
            return {"regex": c.Infra.CODEMOD_NEVER_MATCH_REGEX}
        alternatives = "|".join(re.escape(name) for name in sorted(set(names)))
        return {"regex": rf"^(?:{alternatives})$"}

    @staticmethod
    def codemod_package_export_facts(
        snapshot: p.Infra.WorkspaceSnapshot,
        project: Path,
    ) -> p.Infra.CodemodPackageExportsFacts:
        """Package facts: exports, directory and direct children of each package.

        Exports are the ``__all__`` each initializer declares, read through the
        injected snapshot's source engine (a package without a literal
        ``__all__`` exports nothing); the directory and the child modules and
        packages come from the same source index. Only files owned by this
        repository contribute package facts; nested repositories are handled by
        their own invocation.

        Returns:
            The typed package facts the utilities and renderers consume.

        """
        root = project.resolve()
        index = FlextInfraUtilitiesRopeAnalysisWorkspace.index_rope_workspace(
            snapshot, root
        )
        project_files = frozenset(
            FlextInfraUtilitiesWorkspaceSnapshot.workspace_python_files(snapshot, root)
        )
        owned = tuple(
            entry
            for entry in index.modules_by_path.values()
            if entry.module_name and entry.file_path in project_files
        )
        packages = {
            entry.module_name: entry.file_path
            for entry in owned
            if entry.file_path.name == c.Infra.INIT_PY
        }
        children: dict[str, set[str]] = {package: set() for package in packages}
        for entry in owned:
            parent, separator, leaf = entry.module_name.rpartition(".")
            if separator and parent in children:
                children[parent].add(leaf)
        run = FlextInfraUtilitiesPythonModel.python_model_run(snapshot.engine, packages)
        return m.Infra.CodemodPackageExportsFacts(
            exports={
                package: tuple(
                    FlextInfraUtilitiesPythonModel.python_model_exports(
                        FlextInfraUtilitiesPythonModel.python_model_module_at(
                            run, path, package
                        )
                    )
                    or ()
                )
                for package, path in sorted(packages.items())
            },
            directories={
                package: path.parent.relative_to(root).as_posix()
                for package, path in sorted(packages.items())
            },
            modules={
                package: tuple(sorted(names))
                for package, names in sorted(children.items())
            },
        )

    @classmethod
    def codemod_workspace_export_facts(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> p.Infra.CodemodPackageExportsFacts:
        """Package facts of the project plus its declared provider packages.

        Provider rewire rules introduce facade letters and names that only
        provider distributions declare, and the run's snapshot is deliberately
        repository-scoped, so the header stage additionally reads each
        declared dependency's installed initializer (the same static
        ``__all__`` extraction the repository facts use). The project's own
        packages keep precedence on any name collision.

        Returns:
            The merged typed package facts of the project and its providers.

        """
        own = project.resolve()
        merged_exports: dict[str, t.StrTuple] = {}
        merged_directories: dict[str, str] = {}
        merged_modules: dict[str, t.StrTuple] = {}
        facts = cls.codemod_package_export_facts(snapshot, own)
        for package, names in facts.exports.items():
            merged_exports.setdefault(package, names)
        for package, directory in facts.directories.items():
            merged_directories.setdefault(package, directory)
        for package, children in facts.modules.items():
            merged_modules.setdefault(package, children)
        run = FlextInfraUtilitiesPythonModel.python_model_run(snapshot.engine, {})
        for package in cls._codemod_provider_candidates(own):
            exports = cls._codemod_installed_package_exports(snapshot, run, package)
            if exports is None:
                continue
            # An installed provider contains no module of this project, so it
            # has no project directory: it is never a header's scope.
            merged_exports.setdefault(package, exports)
            merged_modules.setdefault(package, ())
        return m.Infra.CodemodPackageExportsFacts(
            exports=merged_exports,
            directories=merged_directories,
            modules=merged_modules,
        )

    @staticmethod
    def _codemod_provider_candidates(project: Path) -> t.StrTuple:
        """Import metadata candidates supplied by the runtime closure.

        Metadata names are not proof of importability or facade ownership.
        The installed initializer's native lazy declarations elect providers.

        Returns:
            The metadata candidates, excluding the already-owned package.

        """
        own = FlextInfraUtilitiesPyprojectConform.project_package_name(project)
        return tuple(
            sorted(
                module
                for module in FlextInfraUtilitiesCodemodNative.codemod_runtime_modules(
                    project
                )
                if module != own
            )
        )

    @staticmethod
    def _codemod_installed_initializer(
        snapshot: p.Infra.WorkspaceSnapshot,
        package: str,
    ) -> p.Infra.RopeSourceModule | None:
        """Elect a native installed package initializer without executing it.

        Returns:
            The source initializer, or no package declaration for this candidate.

        """
        resource = snapshot.engine.find_module(package)
        if resource is None or FlextInfraUtilitiesRopeRuntime.file_resource(resource):
            return None
        initializer = Path(resource.real_path) / c.Infra.INIT_PY
        if not initializer.is_file():
            return None
        return FlextInfraUtilitiesRopeRuntime.require_source_module(
            FlextInfraUtilitiesRopeCore.resolve_pymodule(
                snapshot.engine,
                FlextInfraUtilitiesRopeRuntime.file_resource_at(
                    snapshot.engine, initializer
                ),
            )
        )

    @classmethod
    def codemod_provider_aliases(
        cls,
        snapshot: p.Infra.WorkspaceSnapshot,
        package: str,
    ) -> frozenset[str]:
        """Read the package's declared runtime aliases through the native source.

        Returns:
            Its one-letter lazy aliases, without package execution.

        Raises:
            ValueError: If an elected native initializer has no source resource.

        """
        module = cls._codemod_installed_initializer(snapshot, package)
        if module is None:
            return frozenset()
        resource = module.get_resource()
        if resource is None:
            message = f"installed package initializer has no resource: {package}"
            raise ValueError(message)
        routes = FlextInfraUtilitiesRopeSourceBasesAliases.lazy_module_aliases(
            package,
            Path(resource.real_path),
            module.source_code,
            project=snapshot.engine,
            pymodule=module,
        )
        return frozenset(
            alias for alias in routes if len(alias) == 1 and alias.islower()
        )

    @classmethod
    def _codemod_installed_package_exports(
        cls,
        snapshot: p.Infra.WorkspaceSnapshot,
        run: p.Infra.PythonModelRun,
        package: str,
    ) -> t.StrTuple | None:
        """Statically read one installed package initializer's ``__all__``.

        Rope's module finder elects the package folder on the project's
        python path; its initializer is read by the same static model the
        repository facts use.

        Returns:
            The declared names, or ``None`` when the package publishes no
            initializer the static model can read.

        Raises:
            ValueError: If an elected facade loses its native initializer resource.

        """
        if not cls.codemod_provider_aliases(snapshot, package):
            return None
        declaring = cls._codemod_installed_initializer(snapshot, package)
        if declaring is None:
            message = f"elected facade initializer disappeared: {package}"
            raise ValueError(message)
        resource = declaring.get_resource()
        if resource is None:
            message = f"elected facade initializer has no resource: {package}"
            raise ValueError(message)
        initializer = Path(resource.real_path)
        module = FlextInfraUtilitiesPythonModel.python_model_module_at(
            run, initializer, package
        )
        exports = FlextInfraUtilitiesPythonModel.python_model_exports(module)
        return None if exports is None else tuple(exports)

    @classmethod
    def codemod_package_export_utilities(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> Mapping[str, t.JsonMapping]:
        """Render one ``exports--<dotted package>`` utility per package.

        One utility exists per package of the project and its declared
        providers. The import-header rules read the workspace export facts (project plus
        provider packages) and reference each root package's utility; the
        utilities must come from the same facts, or a readable provider
        ``__all__`` leaves its reference undefined and the native scan fails
        to parse.

        Returns:
            The package export utilities rendered from the export facts.

        """
        facts = cls.codemod_workspace_export_facts(snapshot, project)
        return {
            f"{c.Infra.CODEMOD_PACKAGE_EXPORTS_UTILITY}"
            f"{c.Infra.CODEMOD_GENERATED_ID_SEPARATOR}{package}": (
                cls.codemod_exact_names_rule(names)
            )
            for package, names in facts.exports.items()
        }

    @staticmethod
    def codemod_facade_family_package_utilities(
        snapshot: p.Infra.WorkspaceSnapshot,
        project: Path,
    ) -> Mapping[str, t.JsonMapping]:
        """Facade-family packages: ``<own root>._<family>`` of every family.

        The family directories come from the facade-family declarations, so a
        layer-zero singleton module (``pkg._settings``) is not a family package.
        The same computation yields the collapsed spelling ``<root>_<family>``
        (separator dropped), a module that never exists.

        Returns:
            The ``facade-family-package`` and
            ``collapsed-facade-family-package`` utility rules of the project.

        """
        del snapshot
        roots = sorted({
            FlextInfraUtilitiesPyprojectConform.project_package_name(
                project.absolute()
            ),
            *c.Infra.NON_PUBLIC_LAZY_ROOTS,
        })
        directories = sorted({
            family.directory
            for family in FlextInfraUtilitiesCodegenNamespace.facade_families().values()
        })
        packages = "|".join(re.escape(name) for name in roots)
        families = "|".join(re.escape(name) for name in directories)
        return {
            c.Infra.CODEMOD_FACADE_FAMILY_PACKAGE_UTILITY: {
                "regex": rf"^(?:{packages})\.(?:{families})(?:[.\s]|$)"
            },
            c.Infra.CODEMOD_COLLAPSED_FACADE_FAMILY_PACKAGE_UTILITY: {
                "regex": rf"^(?:{packages})(?:{families})$"
            },
        }

    @staticmethod
    def _codemod_name_utils() -> t.JsonDict:
        """Local utilities of the generated shapes: a binding and a free use.

        The binding rule is the universal catalog's ``name-binding`` utility,
        embedded because generated rules are staged outside its provider.

        Returns:
            The ``utils`` mapping every generated name shape carries.

        """
        binding = FlextInfraUtilitiesCodemodRules.codemod_provider_utility_rule(
            FlextInfraConfig.ssot_config_dir().parent / c.Infra.CODEMOD_CONFIG_RELPATH,
            c.Infra.CODEMOD_NAME_BINDING_UTILITY,
        )
        outside_imports: list[t.JsonValue] = [
            {"not": {"inside": {"kind": kind, "stopBy": "end"}}}
            for kind in ("import_from_statement", "import_statement")
        ]
        return {
            "binding": dict(binding),
            "local-binding": {
                "all": [{"matches": "binding"}, *outside_imports],
            },
            "use": {
                "all": [
                    {"kind": "identifier"},
                    {"not": {"matches": "binding"}},
                    # An import statement only binds: the imported name of an
                    # aliased import binds nothing, and is no use either.
                    *outside_imports,
                    {"not": {"inside": {"kind": "attribute", "field": "attribute"}}},
                    {"not": {"inside": {"kind": "keyword_argument", "field": "name"}}},
                    # A match class pattern spells ``m.Family.Model()`` as one
                    # dotted_name: only its first identifier is a use.
                    {
                        "not": {
                            "all": [
                                {"inside": {"kind": "dotted_name"}},
                                {"follows": {"kind": "identifier", "stopBy": "end"}},
                            ]
                        }
                    },
                ]
            },
        }

    @staticmethod
    def _codemod_declaring_packages(
        facts: p.Infra.CodemodPackageExportsFacts,
    ) -> Mapping[str, t.StrTuple]:
        """Every public non-dunder name to the packages whose ``__all__`` declares it.

        Returns:
            Name to its declaring packages, shallowest first.

        """
        declaring: dict[str, list[str]] = {}
        for package, names in facts.exports.items():
            for name in names:
                if name.isidentifier() and not name.startswith("__"):
                    declaring.setdefault(name, []).append(package)
        return {
            name: tuple(sorted(packages, key=lambda item: (item.count("."), item)))
            for name, packages in sorted(declaring.items())
        }

    @classmethod
    def codemod_header_resolvable_names(
        cls, facts: p.Infra.CodemodPackageExportsFacts
    ) -> Mapping[str, str]:
        """Names whose canonical package import is unambiguous from any module.

        A name resolves when exactly one shallowest package declares it; a
        module inside a deeper declaring package imports it from that package.

        Returns:
            Resolvable name to its shallowest declaring package.

        """
        resolvable: dict[str, str] = {}
        for name, packages in cls._codemod_declaring_packages(facts).items():
            # A Python builtin is always bound: a provider publishing a
            # builtin-shadowing member (pulumi publishes `set`) must never
            # make the header stage import over the builtin.
            if hasattr(builtins, name):
                continue
            depth = packages[0].count(".")
            if sum(package.count(".") == depth for package in packages) == 1:
                resolvable[name] = packages[0]
        return resolvable

    @staticmethod
    def _codemod_directory_glob(directory: str) -> str:
        """Match every file under one project-relative directory, wherever staged.

        Returns:
            The native glob.

        """
        return f"**/{PurePosixPath(directory).as_posix()}/**"

    @classmethod
    def codemod_import_header_rules(
        cls,
        snapshot: p.Infra.WorkspaceSnapshot,
        project: Path,
        facts: p.Infra.CodemodPackageExportsFacts,
    ) -> Mapping[str, t.JsonMapping]:
        """Render the letter-binding law: one binding per letter, from its owner.

        Every document is an ``import-header`` shape. One rule per package and
        scope inserts, after the module's first future or plain import, one
        ``from <package> import <name>`` line for an actual unbound use. The
        fixed-point loop binds remaining free names; already-bound names keep
        their existing semantic owner. A module inside a declaring package
        imports from the deepest declaring package that contains it; every
        other module imports from the unique shallowest declaring package, and
        gets no header when that package is ambiguous.

        A facade-family module (the modules of one letter's family, per
        top-level package) never binds that letter, nor a later one, from its
        own package: the family assembles that facade. Those letters bind from
        the upstream package the facade composes, the own-package binding is
        removed, and a letter bound from two origins keeps the upstream one.
        Outside the families every letter binds from the own package root.

        Returns:
            The generated ``import-header`` rule documents keyed by id.

        """
        root = project.resolve()
        families = cls._codemod_letter_families(snapshot, root)
        upstreams = cls._codemod_letter_upstreams((snapshot, root), facts, families)
        carved: dict[tuple[str, str], set[str]] = {}
        for family, files in families.items():
            for name in cls._codemod_forbidden_letters(facts, upstreams, family):
                carved.setdefault((family[0], name), set()).update(files)
        documents = dict(
            cls._codemod_header_documents(
                facts, {key: tuple(sorted(files)) for key, files in carved.items()}
            )
        )
        documents.update(
            cls._codemod_family_binding_documents(
                (snapshot, root), facts, families, upstreams
            )
        )
        return documents

    @classmethod
    def _codemod_header_documents(
        cls,
        facts: p.Infra.CodemodPackageExportsFacts,
        carve: Mapping[tuple[str, str], t.StrTuple],
    ) -> Mapping[str, t.JsonMapping]:
        """Insert the nearest declaring package's import for unbound names.

        A letter never binds from the package whose family module needs it:
        those family files are carved out of the package's document, and the
        family documents bind them from the upstream.

        Returns:
            The generated header documents keyed by id.

        """
        directories = facts.directories
        groups: dict[tuple[str, str | None, t.StrTuple, t.StrTuple], set[str]] = {}
        resolvable = cls.codemod_header_resolvable_names(facts)
        for name, packages in cls._codemod_declaring_packages(facts).items():
            # A module inside a declaring package always resolves the name to
            # the deepest declaring package containing it, even when the
            # shallowest declaration is ambiguous (``u`` published by both the
            # source package and the ``tests`` tier): only the unscoped rule
            # needs a unique shallowest package.
            # An installed provider has no project directory: it is never a
            # scope and never an ignored nested scope.
            root = resolvable.get(name)
            located = tuple(package for package in packages if package in directories)
            for package in packages:
                if package != root and package not in directories:
                    continue
                home = PurePosixPath(directories.get(package, "."))
                nested = tuple(
                    sorted(
                        directories[other]
                        for other in located
                        if other != package
                        and (
                            package == root
                            or PurePosixPath(directories[other]).is_relative_to(home)
                        )
                    )
                )
                scope = None if package == root else home.as_posix()
                carved = carve.get((package, name), ())
                groups.setdefault((package, scope, nested, carved), set()).add(name)
        utils = cls._codemod_name_utils()
        documents: dict[str, t.JsonMapping] = {}
        # The root scope is None; order it before every directory scope.
        for (package, scope, nested, carved), names in sorted(
            groups.items(),
            key=lambda item: (
                item[0][0],
                item[0][1] is not None,
                item[0][1] or "",
                item[0][2],
                item[0][3],
            ),
        ):
            qualifier = (
                package
                if scope is None and not nested and not carved
                else f"{package}{c.Infra.CODEMOD_GENERATED_ID_SEPARATOR}"
                + u.Cli.sha256_content(
                    f"{scope}\0{'\0'.join(nested)}\0{'\0'.join(carved)}"
                )[:12]
            )
            rule_id = (
                f"{c.Infra.CODEMOD_IMPORT_HEADER_SHAPE}"
                f"{c.Infra.CODEMOD_GENERATED_ID_SEPARATOR}{qualifier}"
            )
            document: dict[str, t.JsonValue] = {
                "id": rule_id,
                "language": c.Infra.CODEMOD_PYTHON_LANGUAGE,
                "message": f"Import the names `{package}` publishes from it.",
                "utils": dict(utils),
                "rule": cls._codemod_header_rule(sorted(names)),
                "fix": f"$ANCHOR\nfrom {package} import $USED",
            }
            if scope is not None:
                document["files"] = [cls._codemod_directory_glob(scope)]
            ignores: list[t.JsonValue] = [
                *(cls._codemod_directory_glob(directory) for directory in nested),
                *cls._codemod_file_globs(carved),
            ]
            if ignores:
                document["ignores"] = ignores
            documents[rule_id] = document
        return documents

    @staticmethod
    def _codemod_file_globs(files: Sequence[str]) -> list[str]:
        """Match each project-relative file, wherever staged.

        Returns:
            The native globs.

        """
        return [f"**/{relative}" for relative in files]

    @staticmethod
    def _codemod_letter_rank(letter: str) -> int:
        """Rank a runtime facade letter in the import-layer order.

        A letter naming a layer is that layer; a declared layer alias ranks
        with its layer; every other letter stands for ``base``.

        Returns:
            The letter's layer rank.

        """
        order = tuple(config.Infra.tooling.lazy_init.import_layer_order)
        return order.index(
            letter
            if letter in order
            else config.Infra.tooling.lazy_init.layer_aliases.get(
                letter, c.Infra.IMPORT_LAW_BASE_LAYER
            )
        )

    @staticmethod
    def _codemod_package_letters(
        facts: p.Infra.CodemodPackageExportsFacts, package: str
    ) -> frozenset[str]:
        """Name the one-letter facade aliases one package publishes.

        Returns:
            The package's letters.

        """
        return frozenset(
            name
            for name in facts.exports.get(package, ())
            if len(name) == 1 and name.islower()
        )

    @staticmethod
    def _codemod_namespace_owner(
        parts: Sequence[str], namespaces: frozenset[str]
    ) -> str:
        """Elect the facade package owning one module, at any nesting depth.

        Outside a declared repository namespace the owner is the top package.
        Inside one, it is the package holding the facade modules: the path up to
        the first private family component (``_models``), or the module's own
        package for a public module (``infra.pulumi.lib.models``).

        Returns:
            The dotted owner package.

        """
        if parts[0] not in namespaces:
            return parts[0]
        for index, part in enumerate(parts):
            if part.startswith("_") and not part.startswith("__"):
                return ".".join(parts[:index])
        return ".".join(parts[:-1])

    @staticmethod
    def _codemod_letter_families(
        snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> Mapping[tuple[str, str], t.StrTuple]:
        """Group each letter's family modules by their top-level package.

        A family is the modules of one facade letter inside one package (the
        public package, an internal tier, or an independent package under a
        declared repository namespace): the modules whose own ``__all__``
        declares the letter and those of the private family package of such a
        facade module. Its members assemble that package's facade.

        Returns:
            Project-relative family files keyed by ``(package, letter)``.

        """
        root = project.resolve()
        files = frozenset(
            FlextInfraUtilitiesWorkspaceSnapshot.workspace_python_files(snapshot, root)
        )
        namespaces = frozenset(
            FlextInfraUtilitiesCodegenNamespace.repository_namespace_packages(root)
        )

        exports = FlextInfraUtilitiesWorkspaceSnapshot.workspace_public_exports

        def letters(module: Path) -> frozenset[str]:
            if module not in files:
                return frozenset()
            return frozenset(
                name
                for name in exports(snapshot, module)
                if len(name) == 1 and name.islower()
            )

        grouped: dict[tuple[str, str], list[str]] = {}
        for path in sorted(files):
            relative = path.relative_to(root)
            if relative.name == c.Infra.INIT_PY:
                continue
            facades = (
                root
                / package.parent
                / f"{package.name.removeprefix('_')}{c.Infra.EXT_PYTHON}"
                for package in relative.parents
                if package.name.startswith("_") and not package.name.startswith("__")
            )
            parts = FlextInfraUtilitiesProjectDiscovery.module_name_for_file(
                path, project_root=root
            ).split(".")
            owner = FlextInfraUtilitiesCodemodNativePackage._codemod_namespace_owner(
                parts, namespaces
            )
            for letter in letters(path).union(*map(letters, facades)):
                grouped.setdefault((owner, letter), []).append(relative.as_posix())
        return {key: tuple(found) for key, found in sorted(grouped.items())}

    @classmethod
    def _codemod_letter_upstreams(
        cls,
        context: tuple[p.Infra.WorkspaceSnapshot, Path],
        facts: p.Infra.CodemodPackageExportsFacts,
        families: Mapping[tuple[str, str], t.StrTuple],
    ) -> Mapping[tuple[str, str], t.StrTuple]:
        """Elect the upstream packages each package composes for each letter.

        An internal tier composes the public package's letters. The public
        package and every package under a declared repository namespace
        (independent packages, never tiers) compose every other package whose
        same letter their facade class derives from, read from the facade
        module's own imports in base (MRO) order. A facade composing several
        upstreams keeps all of them: each family module later binds the one
        exposing the names it reads, never the own package. A letter without a
        facade of its own takes the package's common upstreams, when every
        facade of the package agrees on them.

        Returns:
            The ordered upstream packages keyed by ``(package, letter)``;
            letters without one are absent.

        """
        snapshot, root = context
        public = FlextInfraUtilitiesPyprojectConform.project_package_name(root)
        namespaces = frozenset(
            FlextInfraUtilitiesCodegenNamespace.repository_namespace_packages(root)
        )
        run = FlextInfraUtilitiesPythonModel.python_model_run(snapshot.engine, {})
        upstreams: dict[tuple[str, str], t.StrTuple] = {}
        for (package, letter), files in families.items():
            if package != public and package.partition(".")[0] not in namespaces:
                candidates: t.StrTuple = (
                    (public,)
                    if letter in cls._codemod_package_letters(facts, public)
                    else ()
                )
            else:
                candidates = cls._codemod_facade_upstreams(
                    (run, root, namespaces), ((package, letter), files)
                )
            if candidates:
                upstreams[package, letter] = candidates
        for package in {package for package, _letter in families}:
            common = {up for (owner, _l), up in upstreams.items() if owner == package}
            if len(common) == 1:
                (elected,) = common
                for letter in cls._codemod_package_letters(facts, package):
                    upstreams.setdefault((package, letter), elected)
        return upstreams

    @staticmethod
    def _codemod_elect_family_upstreams(
        snapshot: p.Infra.WorkspaceSnapshot,
        root: Path,
        letter: str,
        bindings: tuple[t.StrTuple, t.StrTuple],
    ) -> Mapping[str, t.StrTuple]:
        """Partition family files by the upstream that exposes what each reads.

        A facade composing one upstream binds every file from it. A facade
        composing several elects, per file, the first upstream in base (MRO)
        order whose published ``letter`` facade natively exposes every
        attribute the file reads from ``letter``; a file reading none of it
        takes the first upstream. A file whose reads no single upstream
        exposes (its own facade's namespace, a name split across upstreams)
        has no lawful binding and fails, never falls back to the own package.

        Returns:
            Upstream package to the family files bound from it.

        Raises:
            ValueError: If no composed upstream exposes a file's reads.

        """
        candidates, files = bindings
        if len(candidates) == 1:
            return {candidates[0]: files}
        exposed: dict[str, frozenset[str]] = {}

        def exposes(upstream: str, reads: frozenset[str]) -> bool:
            if not reads:
                return True
            if upstream not in exposed:
                facade = FlextInfraUtilitiesFacadeMembers.facade_source_classes(
                    upstream, (letter,), source_project=snapshot.engine
                ).get(letter)
                exposed[upstream] = (
                    frozenset()
                    if facade is None
                    else frozenset(facade.get_attributes())
                )
            return reads <= exposed[upstream]

        elected: dict[str, list[str]] = {}
        for relative in files:
            reads = frozenset(
                node.attr
                for node in ast.walk(
                    FlextInfraUtilitiesWorkspaceSnapshot.workspace_module_tree(
                        snapshot, root / relative
                    )
                )
                if isinstance(node, ast.Attribute)
                and isinstance(node.value, ast.Name)
                and node.value.id == letter
            )
            owner = next(
                (upstream for upstream in candidates if exposes(upstream, reads)),
                None,
            )
            if owner is None:
                message = (
                    f"no composed upstream exposes `{letter}` reads of {relative}: "
                    f"{', '.join(sorted(reads))} (upstreams: {', '.join(candidates)}); "
                    "a family module never binds its own letter (ENFORCE-051): "
                    "read a sibling class through the family package"
                )
                raise ValueError(message)
            elected.setdefault(owner, []).append(relative)
        return {upstream: tuple(found) for upstream, found in elected.items()}

    @staticmethod
    def _codemod_facade_upstreams(
        context: tuple[p.Infra.PythonModelRun, Path, frozenset[str]],
        family: tuple[tuple[str, str], t.StrTuple],
    ) -> t.StrTuple:
        """Packages whose same letter a family's facade classes derive from.

        Returns:
            The upstream packages named by the facade modules' own imports,
            in the facade class's base (MRO) order.

        """
        run, root, namespaces = context
        (package, letter), files = family
        candidates: dict[str, None] = {}
        for relative in files:
            module = FlextInfraUtilitiesPythonModel.python_model_module_at(
                run,
                root / relative,
                FlextInfraUtilitiesProjectDiscovery.module_name_for_file(
                    root / relative, project_root=root
                ),
            )
            if letter not in (
                FlextInfraUtilitiesPythonModel.python_model_exports(module) or ()
            ):
                continue
            for base in module.classes.get(module.values.get(letter, ""), ()):
                origin, _, leaf = module.imports.get(base, "").rpartition(".")
                top = (
                    origin
                    if origin.partition(".")[0] in namespaces
                    else origin.partition(".")[0]
                )
                if leaf == letter and top and top != package:
                    candidates.setdefault(top)
        return tuple(candidates)

    @classmethod
    def _codemod_forbidden_letters(
        cls,
        facts: p.Infra.CodemodPackageExportsFacts,
        upstreams: Mapping[tuple[str, str], t.StrTuple],
        family: tuple[str, str],
    ) -> frozenset[str]:
        """Name the letters one family binds from its upstream, not its package.

        Returns:
            The family's own letter and every later letter its package
            publishes, each with a known upstream.

        """
        package, letter = family
        floor = cls._codemod_letter_rank(letter)
        return frozenset(
            name
            for name in {letter, *cls._codemod_package_letters(facts, package)}
            if cls._codemod_letter_rank(name) >= floor and (package, name) in upstreams
        )

    @classmethod
    def _codemod_family_binding_documents(
        cls,
        context: tuple[p.Infra.WorkspaceSnapshot, Path],
        facts: p.Infra.CodemodPackageExportsFacts,
        families: Mapping[tuple[str, str], t.StrTuple],
        upstreams: Mapping[tuple[str, str], t.StrTuple],
    ) -> Mapping[str, t.JsonMapping]:
        """Render the binding law over every package's family and orchestrator modules.

        Inside the family of letter ``L`` of package ``P``, each letter at or
        after ``L`` in the layer order binds from the upstream package ``P``
        composes, never from ``P``; a letter bound from two origins keeps the
        upstream one. Outside the families, every letter binds from ``P``'s
        own root. In both, a letter is imported from a package root, never a
        module path, and never through a package module object.

        Returns:
            The binding documents keyed by id.

        """
        snapshot, root = context
        separator = c.Infra.CODEMOD_GENERATED_ID_SEPARATOR
        shape = c.Infra.CODEMOD_IMPORT_HEADER_SHAPE
        facade_packages = tuple(cls.codemod_facade_packages(snapshot, root))
        documents: dict[str, t.JsonMapping] = {}
        by_package: dict[str, set[str]] = {}
        for (package, letter), files in families.items():
            by_package.setdefault(package, set()).update(files)
            forbidden = cls._codemod_forbidden_letters(
                facts, upstreams, (package, letter)
            )
            if not forbidden:
                continue
            names = "|".join(sorted(forbidden))
            grouped: dict[tuple[str, t.StrTuple], list[str]] = {}
            for name in sorted(forbidden):
                for upstream, bound_files in cls._codemod_elect_family_upstreams(
                    snapshot, root, name, (upstreams[package, name], files)
                ).items():
                    grouped.setdefault((upstream, bound_files), []).append(name)
            for (upstream, bound_files), bound in grouped.items():
                rule_id = separator.join((
                    shape,
                    "family",
                    package,
                    letter,
                    upstream,
                    *(
                        ()
                        if bound_files == files
                        else (u.Cli.sha256_content("\0".join(bound_files))[:12],)
                    ),
                ))
                documents[rule_id] = {
                    "id": rule_id,
                    "language": c.Infra.CODEMOD_PYTHON_LANGUAGE,
                    "message": (
                        f"Bind `{'`, `'.join(bound)}` from `{upstream}` in the "
                        f"`{letter}` family of `{package}`."
                    ),
                    "utils": dict(cls._codemod_name_utils()),
                    "files": [*cls._codemod_file_globs(bound_files)],
                    "rule": cls._codemod_header_rule(bound),
                    "fix": f"$ANCHOR\nfrom {upstream} import $USED",
                }
            documents.update(
                cls._codemod_origin_removal_documents(
                    ("own-letter", package, letter),
                    (
                        (
                            f"The `{letter}` family of `{package}` binds `{names}` "
                            f"from the package it composes, never from `{package}`."
                        ),
                        (),
                    ),
                    (rf"^{re.escape(package)}(?:\.|$)", f"^(?:{names})$"),
                    (cls._codemod_file_globs(files), ()),
                    condition=None,
                )
            )
        for package, files in sorted(by_package.items()):
            documents.update(
                cls._codemod_origin_removal_documents(
                    ("duplicate-origin", package),
                    (
                        (
                            f"A family module of `{package}` binds a letter once, "
                            "from its upstream."
                        ),
                        (),
                    ),
                    (rf"^{re.escape(package)}(?:\.|$)", r"^[a-z]$"),
                    (cls._codemod_file_globs(sorted(files)), ()),
                    condition=cls._codemod_other_origin_condition(
                        rf"^{re.escape(package)}(?:\.|$)"
                    ),
                )
            )
        layer_zero = frozenset(cls.codemod_layer_zero_files(snapshot, root))
        for package, home in sorted(facts.directories.items()):
            letters = cls._codemod_package_letters(facts, package)
            others = [name for name in facade_packages if name != package]
            if not letters or not others:
                continue
            exempt = sorted({*by_package.get(package, ()), *layer_zero})
            documents.update(
                cls._codemod_own_root_document(
                    package, home, letters, cls._codemod_foreign_ignores(exempt)
                )
            )
            documents.update(
                cls._codemod_origin_removal_documents(
                    ("foreign-origin", package),
                    (
                        (
                            f"Outside the families, `{package}` binds every letter "
                            "from its own root, never from another package."
                        ),
                        ("ENFORCE-003", "ENFORCE-080"),
                    ),
                    (
                        r"^(?:" + "|".join(map(re.escape, others)) + r")(?:\.|$)",
                        "^(?:" + "|".join(sorted(letters)) + ")$",
                    ),
                    (
                        [cls._codemod_directory_glob(home)],
                        cls._codemod_foreign_ignores(exempt),
                    ),
                    condition=None,
                )
            )
        if facade_packages:
            documents.update(
                cls._codemod_origin_removal_documents(
                    ("module-path",),
                    (
                        (
                            "A letter is imported from a package root, never from "
                            "a module path."
                        ),
                        ("ENFORCE-003", "ENFORCE-051"),
                    ),
                    (
                        r"^(?:" + "|".join(map(re.escape, facade_packages)) + r")\.",
                        r"^[a-z]$",
                    ),
                    (["**/*.py"], [f"**/{c.Infra.INIT_PY}"]),
                    condition=None,
                )
            )
        documents.update(
            cls._codemod_origin_removal_documents(
                ("typing-duplicate",),
                (
                    (
                        "A name the module binds at runtime is never bound again "
                        "under TYPE_CHECKING."
                    ),
                    ("ENFORCE-003",),
                ),
                (".", r"^[A-Za-z_][A-Za-z0-9_]*$"),
                (["**/*.py"], [f"**/{c.Infra.INIT_PY}"]),
                condition=cls._codemod_runtime_duplicate_condition(),
            )
        )
        documents.update(
            cls._codemod_letter_module_object_documents(facade_packages, facts.exports)
        )
        return documents

    @staticmethod
    def _codemod_comment_free(position: int) -> t.JsonDict:
        """Match the named child at ``position``, comments not counted.

        Returns:
            The native ``nthChild`` rule.

        """
        return {
            "nthChild": {"position": position, "ofRule": {"not": {"kind": "comment"}}}
        }

    @classmethod
    def _codemod_foreign_ignores(cls, exempt: Sequence[str]) -> list[str]:
        """Exclude initializers and family modules from the foreign-origin law.

        Returns:
            The native ignore globs.

        """
        return [f"**/{c.Infra.INIT_PY}", *cls._codemod_file_globs(exempt)]

    @classmethod
    def _codemod_own_root_document(
        cls,
        package: str,
        home: str,
        letters: frozenset[str],
        ignores: Sequence[str],
    ) -> Mapping[str, t.JsonMapping]:
        """Rebind a used, unbound letter from the package's own root.

        The foreign-origin removal leaves the letter unbound; this header
        document binds it from ``package`` in the next pass, so the pair
        converges without an undefined name.

        Returns:
            The one rebinding document keyed by id.

        """
        rule_id = c.Infra.CODEMOD_GENERATED_ID_SEPARATOR.join((
            c.Infra.CODEMOD_IMPORT_HEADER_SHAPE,
            "own-root",
            package,
        ))
        return {
            rule_id: {
                "id": rule_id,
                "language": c.Infra.CODEMOD_PYTHON_LANGUAGE,
                "message": (
                    f"Outside the families, `{package}` binds a used letter "
                    "from its own root."
                ),
                "metadata": {"enforce": ["ENFORCE-003", "ENFORCE-080"]},
                "utils": dict(cls._codemod_name_utils()),
                "files": [cls._codemod_directory_glob(home)],
                "ignores": list(ignores),
                "rule": cls._codemod_header_rule(sorted(letters)),
                "fix": f"$ANCHOR\nfrom {package} import $USED",
            }
        }

    @classmethod
    def _codemod_origin_removal_documents(
        cls,
        identity: tuple[str, ...],
        metadata: tuple[str, Sequence[str]],
        target: tuple[str, str],
        scope: tuple[Sequence[str], Sequence[str]],
        *,
        condition: t.JsonDict | None,
    ) -> Mapping[str, t.JsonMapping]:
        """Remove a bound name from an origin, in every statement shape.

        ``metadata`` is the documents' message and enforced laws; ``scope``
        their file globs and ignores. ``condition``, when given, restricts the
        removal (for example to a module that also binds the name elsewhere).
        A removal paired with a rebinding that claims no laws of its own claims
        none either: both receive the renderer's laws, so a selected theme
        never runs one half of the pair without the other (a family's own-root
        letter removed with no upstream rebinding, or kept with one).

        Returns:
            The four removal documents keyed by id.

        """
        message, enforce = metadata
        files, ignores = scope
        separator = c.Infra.CODEMOD_GENERATED_ID_SEPARATOR
        base = separator.join((c.Infra.CODEMOD_IMPORT_HEADER_SHAPE, *identity))
        documents: dict[str, t.JsonMapping] = {}
        shapes = cls._codemod_origin_removal_shapes(target, condition=condition)
        for kind, (rule, fix) in shapes.items():
            rule_id = f"{base}{separator}{kind}"
            document: dict[str, t.JsonValue] = {
                "id": rule_id,
                "language": c.Infra.CODEMOD_PYTHON_LANGUAGE,
                "message": message,
                "files": list(files),
                "rule": rule,
                "fix": fix,
            }
            if enforce:
                document["metadata"] = {"enforce": list(enforce)}
            if ignores:
                document["ignores"] = list(ignores)
            documents[rule_id] = document
        return documents

    @classmethod
    def _codemod_other_origin_condition(cls, origin: str) -> t.JsonDict:
        """Match a module that also binds ``$NAME`` from another origin.

        Returns:
            The native condition reading ``$NAME``.

        """
        return {
            "inside": {
                "kind": "module",
                "stopBy": "end",
                "has": {
                    "stopBy": "end",
                    "kind": "import_from_statement",
                    "all": [
                        {
                            "has": {
                                "field": "module_name",
                                "regex": ".",
                                "not": {"regex": origin},
                            }
                        },
                        {
                            "has": {
                                "kind": "dotted_name",
                                "pattern": "$NAME",
                                **cls._codemod_comment_free(2),
                            }
                        },
                    ],
                },
            }
        }

    @classmethod
    def _codemod_runtime_duplicate_condition(cls) -> t.JsonDict:
        """Match a ``TYPE_CHECKING`` binding of ``$NAME`` the module makes at runtime.

        The binding sits under an ``if TYPE_CHECKING:`` guard (or is the
        guard's sole statement), and a module-level import outside every guard
        binds the same name from the same origin (``$ORIGIN``). A name bound
        from two origins names two objects (a family's upstream letter and its
        own), so only the same-origin repeat is redundant.

        Returns:
            The native condition reading ``$NAME``.

        """
        guard: t.JsonDict = {
            "kind": "if_statement",
            "has": {
                "field": "condition",
                "regex": c.Infra.CODEMOD_TYPE_CHECKING_TEST_REGEX,
            },
        }
        origin: t.JsonDict = {"field": "module_name", "pattern": "$ORIGIN"}
        return {
            "all": [
                {"any": [guard, {"inside": {"stopBy": "end", **guard}}]},
                {
                    "any": [
                        {"inside": {"kind": "import_from_statement", "has": origin}},
                        {
                            "has": {
                                "stopBy": "end",
                                "kind": "import_from_statement",
                                "has": origin,
                            }
                        },
                    ]
                },
                {
                    "inside": {
                        "kind": "module",
                        "stopBy": "end",
                        "has": {
                            "kind": "import_from_statement",
                            "all": [
                                {"has": origin},
                                {
                                    "has": {
                                        "kind": "dotted_name",
                                        "pattern": "$NAME",
                                        **cls._codemod_comment_free(2),
                                    }
                                },
                            ],
                        },
                    }
                },
            ]
        }

    @classmethod
    def _codemod_origin_removal_shapes(
        cls, target: tuple[str, str], *, condition: t.JsonDict | None
    ) -> Mapping[str, tuple[t.JsonDict, t.JsonValue]]:
        """Native rule and fix of each statement shape a binding removal needs.

        The binding is one name of a ``from <origin> import ...`` statement:
        a name followed by a comma, the last name, the sole name of a
        statement, and the sole statement of an ``if TYPE_CHECKING:`` block each
        need their own native fix. ``condition``, when given, must also hold;
        it reads the removed name as ``$NAME``.

        Returns:
            The rule and fix of each shape keyed by shape name.

        """
        origin, names = target
        own: t.JsonDict = {"field": "module_name", "regex": origin}
        free = cls._codemod_comment_free
        name: t.JsonDict = {"kind": "dotted_name", "regex": names}
        conditions: list[t.JsonValue] = []
        if condition is not None:
            name["pattern"] = "$NAME"
            conditions.append(condition)
        sole: t.JsonDict = {
            "kind": "import_from_statement",
            "all": [
                {"has": own},
                {"has": {**name, **free(2)}},
                {"not": {"has": free(3)}},
            ],
        }
        after_module: t.JsonDict = {
            "follows": {
                "stopBy": "end",
                "any": [{"kind": "dotted_name"}, {"kind": "relative_import"}],
            }
        }
        listed: t.JsonDict = {
            "kind": "import_from_statement",
            "all": [{"has": own}, {"has": free(3)}],
        }
        shapes: dict[str, tuple[t.JsonDict, t.JsonValue]] = {
            "comma": (
                {
                    "all": [
                        name,
                        after_module,
                        {"precedes": {"regex": ","}},
                        {"inside": listed},
                        *conditions,
                    ]
                },
                {"template": "", "expandEnd": {"regex": ","}},
            ),
            "last": (
                {
                    "all": [
                        name,
                        after_module,
                        {"follows": {"regex": ","}},
                        {"not": {"precedes": {"regex": ","}}},
                        {"inside": listed},
                        *conditions,
                    ]
                },
                {"template": "", "expandStart": {"regex": ","}},
            ),
            "statement": (
                {
                    "all": [
                        sole,
                        {
                            "any": [
                                {"inside": {"kind": "module"}},
                                {"inside": {"kind": "block", "has": free(2)}},
                            ]
                        },
                        *conditions,
                    ]
                },
                "",
            ),
            "guard": (
                {
                    "kind": "if_statement",
                    "all": [
                        {
                            "has": {
                                "field": "condition",
                                "regex": c.Infra.CODEMOD_TYPE_CHECKING_TEST_REGEX,
                            }
                        },
                        {
                            "has": {
                                "field": "consequence",
                                "kind": "block",
                                "all": [
                                    {"has": {**sole, **free(1)}},
                                    {"not": {"has": free(2)}},
                                ],
                            }
                        },
                        {"not": {"has": {"field": "alternative", "regex": "."}}},
                        *conditions,
                    ],
                },
                "",
            ),
        }
        return shapes

    @classmethod
    def _codemod_letter_module_object_documents(
        cls, facade_packages: Sequence[str], exports: Mapping[str, Sequence[str]]
    ) -> Mapping[str, t.JsonMapping]:
        """Read a published name bound by name, never through a package object.

        ``pkg.u.x`` becomes ``u.x`` and the header binds ``u`` from its owner.
        A module that declares the letter itself (a facade module) cannot bind
        the package's: it reads ``pkg_u`` instead, bound as ``from pkg import u
        as pkg_u``, the spelling facade modules compose upstream letters with.
        Any other name a root package publishes (``pkg.Service``) follows the
        same law: it is read as ``Service``, bound by ``from pkg import Service``
        through the package's own ``exports--<pkg>`` utility.

        Returns:
            The letter-module-object documents keyed by id.

        """
        separator = c.Infra.CODEMOD_GENERATED_ID_SEPARATOR
        shape = c.Infra.CODEMOD_IMPORT_HEADER_SHAPE
        utils = cls._codemod_name_utils()
        local: t.JsonDict = {
            "inside": {
                "kind": "module",
                "stopBy": "end",
                "has": {
                    "stopBy": "end",
                    "pattern": "$NAME",
                    "matches": "local-binding",
                },
            }
        }
        by_name = f"{shape}{separator}letter-module-object"
        documents: dict[str, t.JsonMapping] = {
            by_name: {
                "id": by_name,
                "language": c.Infra.CODEMOD_PYTHON_LANGUAGE,
                "message": (
                    "Letter `$NAME` read through the package module object "
                    "`$PACKAGE`: bind the letter by name."
                ),
                "ignores": [f"**/{c.Infra.INIT_PY}"],
                "utils": dict(utils),
                # The package and letter tests sit in the rule, before the
                # module-wide ``local`` search: native constraints run only
                # after a rule match, so that search would visit every
                # attribute of every module.
                "rule": {
                    "kind": "attribute",
                    "all": [
                        {
                            "has": cls._codemod_module_object_receiver({
                                "pattern": "$PACKAGE",
                                "not": {"regex": r"\."},
                                "any": [
                                    {"matches": c.Infra.CODEMOD_OWN_PACKAGE_UTILITY},
                                    {
                                        "matches": (
                                            c.Infra.CODEMOD_FACADE_PACKAGE_UTILITY
                                        )
                                    },
                                ],
                            })
                        },
                        {
                            "has": {
                                "field": "attribute",
                                "pattern": "$NAME",
                                "regex": "^[a-z]$",
                            }
                        },
                        {"not": local},
                    ],
                },
                "fix": "$NAME",
            }
        }
        documents.update(cls._codemod_letter_alias_documents(utils, local))
        for package in facade_packages:
            alias = f"{shape}{separator}letter-module-alias{separator}{package}"
            documents[alias] = {
                "id": alias,
                "language": c.Infra.CODEMOD_PYTHON_LANGUAGE,
                "message": (
                    f"Letter `$NAME` read through the `{package}` module object "
                    "in a module that declares `$NAME` itself: bind "
                    f"`{package}_$NAME` from the package."
                ),
                "ignores": [f"**/{c.Infra.INIT_PY}"],
                "utils": dict(utils),
                "constraints": {"NAME": {"regex": "^[a-z]$"}},
                "rule": {
                    "kind": "attribute",
                    "all": [
                        {
                            "has": cls._codemod_module_object_receiver({
                                "regex": f"^{re.escape(package)}$"
                            })
                        },
                        {"has": {"field": "attribute", "pattern": "$NAME"}},
                        local,
                    ],
                },
                "fix": f"{package}_$NAME",
            }
            binder = f"{shape}{separator}letter-alias{separator}{package}"
            documents[binder] = {
                "id": binder,
                "language": c.Infra.CODEMOD_PYTHON_LANGUAGE,
                "message": f"Bind `{package}_<letter>` from `{package}`.",
                "utils": dict(utils),
                "transform": {
                    "LETTER": {
                        "substring": {"source": "$USED", "startChar": len(package) + 1}
                    }
                },
                "rule": cls._codemod_header_rule_regex(
                    rf"^{re.escape(package)}_[a-z]$"
                ),
                "fix": f"$ANCHOR\nfrom {package} import $LETTER as $USED",
            }
        documents.update(cls._codemod_name_module_load_document(utils, local, exports))
        for package in sorted(name for name in exports if "." not in name):
            exact: t.JsonDict = {"regex": f"^{re.escape(package)}$"}
            published = f"{shape}{separator}name-module-object{separator}{package}"
            documents[published] = {
                "id": published,
                "language": c.Infra.CODEMOD_PYTHON_LANGUAGE,
                "message": (
                    f"`$NAME` read through the `{package}` module object: import "
                    f"it by name, `from {package} import $NAME`."
                ),
                "ignores": [f"**/{c.Infra.INIT_PY}"],
                "utils": dict(utils),
                "constraints": {
                    "NAME": {
                        "all": [
                            {
                                "matches": (
                                    f"{c.Infra.CODEMOD_PACKAGE_EXPORTS_UTILITY}"
                                    f"{separator}{package}"
                                )
                            },
                            {"not": {"regex": "^[a-z]$"}},
                            # Module metadata (``pkg.__version__``) is an
                            # attribute of the module object itself.
                            {"not": {"regex": "^__.+__$"}},
                        ]
                    }
                },
                "rule": {
                    "kind": "attribute",
                    "all": [
                        {"has": cls._codemod_module_object_receiver(exact)},
                        {"has": {"field": "attribute", "pattern": "$NAME"}},
                        {"not": local},
                    ],
                },
                "fix": "$NAME",
            }
            documents.update(cls._codemod_dead_module_load_document(package))
        return documents

    @staticmethod
    def _codemod_module_load(package: t.JsonDict) -> t.JsonDict:
        """A literal ``import_module("<package>")`` call loading a module object.

        ``package`` tests the loaded module name, a root or a subpackage.

        Returns:
            The native rule of the call.

        """
        return {
            "kind": "call",
            "all": [
                {
                    "has": {
                        "field": "function",
                        "regex": r"^(?:importlib\.)?import_module$",
                    }
                },
                {
                    "has": {
                        "field": "arguments",
                        "has": {
                            "kind": "string",
                            "nthChild": 1,
                            "has": {"kind": "string_content", **package},
                        },
                    }
                },
            ],
        }

    @classmethod
    def _codemod_name_module_load_document(
        cls,
        utils: t.JsonMapping,
        local: t.JsonDict,
        exports: Mapping[str, Sequence[str]],
    ) -> Mapping[str, t.JsonMapping]:
        """Bind a name read through a dynamically loaded module below a root.

        ``import_module("pkg.sub").Name`` and ``import_module("pkg.sub.mod")
        .Name`` read ``Name``, which the header then binds from its declaring
        package; a root itself belongs to ``name-module-object``. One document
        covers every package: per-package documents would multiply the native
        rule count.

        Returns:
            The one document keyed by id.

        """
        packages = sorted(exports)
        roots = [name for name in packages if "." not in name]
        alternatives = "|".join(map(re.escape, packages))
        rule_id = c.Infra.CODEMOD_GENERATED_ID_SEPARATOR.join((
            c.Infra.CODEMOD_IMPORT_HEADER_SHAPE,
            "name-module-load",
        ))
        names = sorted({name for package in packages for name in exports[package]})
        return {
            rule_id: {
                "id": rule_id,
                "language": c.Infra.CODEMOD_PYTHON_LANGUAGE,
                "message": (
                    "`$NAME` read through the dynamically loaded `$PACKAGE` object: "
                    "import it by name."
                ),
                "ignores": [f"**/{c.Infra.INIT_PY}"],
                "utils": dict(utils),
                "constraints": {
                    "NAME": {
                        "all": [
                            cls.codemod_exact_names_rule(names),
                            {"not": {"regex": "^[a-z]$"}},
                            {"not": {"regex": "^__.+__$"}},
                        ]
                    }
                },
                "rule": {
                    "kind": "attribute",
                    "all": [
                        {
                            "has": {
                                "field": "object",
                                **cls._codemod_module_load({
                                    "pattern": "$PACKAGE",
                                    "regex": rf"^(?:{alternatives})(?:\.\w+)?$",
                                    "not": cls.codemod_exact_names_rule(roots),
                                }),
                            }
                        },
                        {"has": {"field": "attribute", "pattern": "$NAME"}},
                        {"not": local},
                    ],
                },
                "fix": "$NAME",
            }
        }

    @classmethod
    def _codemod_module_object_receiver(cls, package: t.JsonDict) -> t.JsonDict:
        """The ``object`` of an attribute read through a package module object.

        ``pkg.X``, ``import_module("pkg").X`` and ``root.X`` under an enclosing
        ``root = import_module("pkg")`` all read ``X`` through the package
        object; ``package`` tests the package name.

        Returns:
            The native ``has`` rule of the attribute's object.

        """
        load = cls._codemod_module_load(package)
        return {
            "field": "object",
            "any": [
                {"kind": "identifier", **package},
                load,
                {
                    "kind": "identifier",
                    "pattern": "$ROOT",
                    **cls._codemod_enclosing_scope(cls._codemod_name_alias(load)),
                },
            ],
        }

    @staticmethod
    def _codemod_name_alias(right: t.JsonDict) -> t.JsonDict:
        """``$ROOT = <right>``: a local name bound to another object.

        Returns:
            The native rule of the assignment.

        """
        return {
            "kind": "assignment",
            "all": [
                {"has": {"field": "left", "kind": "identifier", "pattern": "$ROOT"}},
                {"has": {"field": "right", **right}},
            ],
        }

    @classmethod
    def _codemod_unread_alias(cls, right: t.JsonDict) -> t.JsonDict:
        """A statement ``$ROOT = <right>`` whose name nothing reads afterwards.

        Returns:
            The native rule of the statement's contents.

        """
        return {
            "has": cls._codemod_name_alias(right),
            "not": cls._codemod_enclosing_scope({
                "kind": "identifier",
                "pattern": "$ROOT",
                "not": {"inside": {"kind": "assignment", "field": "left"}},
            }),
        }

    @classmethod
    def _codemod_letter_alias_documents(
        cls, utils: t.JsonMapping, local: t.JsonDict
    ) -> Mapping[str, t.JsonMapping]:
        """Read a facade letter by name, never through a local alias of it.

        ``models = m`` followed by ``models.Tests.X`` reads ``m.Tests.X``, and
        the alias, once unread, is dropped. Only a letter the module binds by
        import qualifies; a locally bound one-letter name is no facade.

        Returns:
            The read and removal documents keyed by id.

        """
        separator = c.Infra.CODEMOD_GENERATED_ID_SEPARATOR
        shape = c.Infra.CODEMOD_IMPORT_HEADER_SHAPE
        letter: t.JsonDict = {
            "kind": "identifier",
            "pattern": "$NAME",
            "regex": "^[a-z]$",
        }
        ignores = [f"**/{c.Infra.INIT_PY}"]
        read = f"{shape}{separator}letter-local-alias"
        unread = f"{shape}{separator}dead-letter-alias"
        return {
            read: {
                "id": read,
                "language": c.Infra.CODEMOD_PYTHON_LANGUAGE,
                "message": (
                    "Letter `$NAME` read through its local alias `$ROOT`: read "
                    "the letter by name."
                ),
                "ignores": [*ignores],
                "utils": dict(utils),
                "rule": {
                    "kind": "attribute",
                    "all": [
                        {
                            "has": {
                                "field": "object",
                                "kind": "identifier",
                                "pattern": "$ROOT",
                                **cls._codemod_enclosing_scope(
                                    cls._codemod_name_alias(letter)
                                ),
                            }
                        },
                        {"has": {"field": "attribute", "pattern": "$ATTR"}},
                        {"not": local},
                    ],
                },
                "fix": "$NAME.$ATTR",
            },
            unread: {
                "id": unread,
                "language": c.Infra.CODEMOD_PYTHON_LANGUAGE,
                "message": "Local alias `$ROOT` of the letter `$NAME` is never read.",
                "ignores": [*ignores],
                "rule": {
                    "kind": "expression_statement",
                    "inside": {"kind": "function_definition", "stopBy": "end"},
                    **cls._codemod_unread_alias(letter),
                },
                "fix": "",
            },
        }

    @staticmethod
    def _codemod_enclosing_scope(descendant: t.JsonDict) -> t.JsonDict:
        """Inside a function or module holding ``descendant`` at any depth.

        Returns:
            The native ``inside`` rule.

        """
        return {
            "inside": {
                "stopBy": "end",
                "any": [{"kind": "module"}, {"kind": "function_definition"}],
                "has": {"stopBy": "end", **descendant},
            }
        }

    @classmethod
    def _codemod_dead_module_load_document(
        cls, package: str
    ) -> Mapping[str, t.JsonMapping]:
        """Drop a dynamic load of ``package`` inside itself that nothing reads.

        Once every read through the loaded object binds its name, the bare
        ``import_module("pkg")`` statement and an unread ``root = ...`` alias
        are no-ops: a module of ``pkg`` runs only after ``pkg`` is imported.

        Returns:
            The one removal document keyed by id.

        """
        rule_id = c.Infra.CODEMOD_GENERATED_ID_SEPARATOR.join((
            c.Infra.CODEMOD_IMPORT_HEADER_SHAPE,
            "dead-module-load",
            package,
        ))
        load = cls._codemod_module_load({"regex": f"^{re.escape(package)}$"})
        return {
            rule_id: {
                "id": rule_id,
                "language": c.Infra.CODEMOD_PYTHON_LANGUAGE,
                "message": (
                    f"`{package}` is loaded dynamically inside itself and the "
                    "object is never read."
                ),
                "metadata": {"enforce": ["ENFORCE-003"]},
                "files": [f"**/{package}/**/*.py"],
                "rule": {
                    "kind": "expression_statement",
                    "any": [
                        {"all": [{"has": load}, {"not": {"has": {"nthChild": 2}}}]},
                        cls._codemod_unread_alias(load),
                    ],
                },
                "fix": "",
            }
        }

    @classmethod
    def _codemod_header_rule(cls, names: Sequence[str]) -> t.JsonDict:
        """Anchor on the first future or plain import of a module using ``names``.

        Returns:
            The native rule of one ``import-header`` document.

        """
        return cls._codemod_header_anchor(cls.codemod_exact_names_rule(names))

    @classmethod
    def _codemod_header_rule_regex(cls, regex: str) -> t.JsonDict:
        """Anchor on the first import of a module using a name matching ``regex``.

        Returns:
            The native rule of one ``import-header`` document.

        """
        return cls._codemod_header_anchor({"regex": regex})

    @classmethod
    def _codemod_header_anchor(cls, matcher: t.JsonDict) -> t.JsonDict:
        """Anchor on the first future or plain import of a module using a name.

        Returns:
            The native rule of one ``import-header`` document.

        """
        imports = ("import_from_statement", "import_statement")
        bound: t.JsonDict = {"all": [{"pattern": "$USED"}, {"matches": "binding"}]}
        # A use is already bound only by a binding visible where it occurs: one
        # in the module scope or in a function, lambda or comprehension that
        # encloses it. Each scope is searched without entering the scopes it
        # nests (native ``stopBy``), so a comprehension variable or a
        # parameter that merely shares the name binds nothing outside itself.
        # A nested function's own name binds in the searching scope: the stop
        # node is still visited, so it is matched by its ``name`` field.
        # A binding under ``if TYPE_CHECKING:`` serves typing reads only:
        # annotations, type aliases and code inside such a guard, which never
        # runs. A runtime read needs a binding outside every guard.
        own_scope: t.JsonDict = {
            "any": [{"kind": kind} for kind in c.Infra.CODEMOD_NAME_SCOPE_KINDS]
        }
        guarded: t.JsonDict = {
            "inside": {
                "stopBy": "end",
                "kind": "if_statement",
                "has": {
                    "field": "condition",
                    "regex": c.Infra.CODEMOD_TYPE_CHECKING_TEST_REGEX,
                },
            }
        }

        def visible(binding: t.JsonDict) -> t.JsonDict:
            return {
                "inside": {
                    "stopBy": "end",
                    "any": [
                        {"kind": "module"},
                        *({"kind": kind} for kind in c.Infra.CODEMOD_NAME_SCOPE_KINDS),
                    ],
                    "has": {
                        "stopBy": own_scope,
                        "any": [
                            binding,
                            {
                                "kind": "function_definition",
                                "has": {"field": "name", "pattern": "$USED"},
                            },
                        ],
                    },
                }
            }

        typing_use: t.JsonDict = {
            "any": [
                guarded,
                *(
                    {"inside": {"stopBy": "end", "kind": kind}}
                    for kind in ("type", "type_alias_statement")
                ),
            ]
        }
        visible_binding: t.JsonDict = {
            "any": [
                {"all": [typing_use, visible(bound)]},
                visible({"all": [bound, {"not": guarded}]}),
            ]
        }
        return {
            "pattern": "$ANCHOR",
            "any": [
                {"kind": "future_import_statement"},
                {
                    "all": [
                        {"any": [{"kind": kind} for kind in imports]},
                        {"inside": {"kind": "module"}},
                        {
                            "not": {
                                "follows": {
                                    "stopBy": "end",
                                    "any": [
                                        {"kind": kind}
                                        for kind in (
                                            *imports,
                                            "future_import_statement",
                                        )
                                    ],
                                }
                            }
                        },
                    ]
                },
            ],
            "inside": {
                "kind": "module",
                "has": {
                    "stopBy": "end",
                    # The kind and the exact-name test are cheap and narrow the
                    # module walk before the scope-sensitive use and binding tests.
                    "all": [
                        {"kind": "identifier"},
                        matcher,
                        {"matches": "use"},
                        {"pattern": "$USED"},
                        {"not": visible_binding},
                    ],
                },
            },
        }

    @classmethod
    def codemod_module_member_rules(
        cls,
        snapshot: p.Infra.WorkspaceSnapshot,
        project: Path,
        facts: p.Infra.CodemodPackageExportsFacts,
    ) -> Mapping[str, t.JsonMapping]:
        """Reach a member through its package import, never a module object.

        For each package with child packages, one rule rewrites
        ``<child>.<Name>`` to ``Name`` in a module that binds ``<child>`` by
        ``from <package> import <child>``, when the child package publishes
        ``Name``, the import header resolves it, and the module binds neither
        name locally; the header stage then imports ``Name`` and the Ruff
        import-fix stage prunes the module-object import.

        Returns:
            The generated ``module-member`` rule documents keyed by id.

        """
        del snapshot
        del project
        resolvable = cls.codemod_header_resolvable_names(facts)
        utils = cls._codemod_name_utils()
        documents: dict[str, t.JsonMapping] = {}
        for package, children in sorted(facts.modules.items()):
            branches: list[t.JsonDict] = [
                {
                    "all": [
                        {
                            "has": {
                                "field": "object",
                                "kind": "identifier",
                                **cls.codemod_exact_names_rule((child,)),
                                "pattern": "$PKG",
                            }
                        },
                        {
                            "has": {
                                "field": "attribute",
                                "kind": "identifier",
                                **cls.codemod_exact_names_rule(names),
                                "pattern": "$NAME",
                            }
                        },
                    ]
                }
                for child in children
                if (
                    names := tuple(
                        name
                        for name in facts.exports.get(f"{package}.{child}", ())
                        if name in resolvable
                    )
                )
            ]
            if not branches:
                continue
            rule_id = (
                f"{c.Infra.CODEMOD_MODULE_MEMBER_SHAPE}"
                f"{c.Infra.CODEMOD_GENERATED_ID_SEPARATOR}{package}"
            )
            documents[rule_id] = {
                "id": rule_id,
                "language": c.Infra.CODEMOD_PYTHON_LANGUAGE,
                "message": (
                    f"Import the member from its package, not through a "
                    f"`{package}` module object."
                ),
                "utils": dict(utils),
                "rule": cls._codemod_member_rule(package, branches),
                "fix": "$NAME",
            }
        return documents

    @classmethod
    def _codemod_member_rule(
        cls, package: str, branches: Sequence[t.JsonDict]
    ) -> t.JsonDict:
        """Match ``<child>.<Name>`` bound by a module-object import of ``package``.

        Returns:
            The native rule of one ``module-member`` document.

        """
        unbound: list[t.JsonValue] = [
            {
                "not": {
                    "has": {
                        "stopBy": "end",
                        "all": [
                            {"pattern": variable},
                            {"matches": "local-binding"},
                        ],
                    }
                }
            }
            for variable in ("$NAME", "$PKG")
        ]
        return {
            "all": [
                {"kind": "attribute"},
                {"any": list[t.JsonValue](branches)},
                {
                    "inside": {
                        "stopBy": "end",
                        "kind": "module",
                        "all": [
                            {
                                "has": {
                                    "stopBy": "end",
                                    "kind": "import_from_statement",
                                    "all": [
                                        {
                                            "has": {
                                                "field": "module_name",
                                                **cls.codemod_exact_names_rule((
                                                    package,
                                                )),
                                            }
                                        },
                                        {
                                            "has": {
                                                "kind": "dotted_name",
                                                "pattern": "$PKG",
                                                "not": {
                                                    "inside": {
                                                        "kind": "import_from_statement",
                                                        "field": "module_name",
                                                    }
                                                },
                                            }
                                        },
                                    ],
                                }
                            },
                            *unbound,
                        ],
                    }
                },
            ]
        }

    @staticmethod
    def codemod_role_files(
        snapshot: p.Infra.WorkspaceSnapshot, project: Path, roles: Sequence[str]
    ) -> t.StrTuple:
        """Project-relative paths of every module the import law gives a role.

        The same classifier the import law applies (namespace location, then
        module role) decides membership, so the generated rules and the law
        agree on every file.

        Returns:
            The sorted POSIX paths, relative to the project root.

        """
        root = project.resolve()
        law = FlextInfraUtilitiesImportLaw
        package = FlextInfraUtilitiesPyprojectConform.project_package_name(root)
        bootstrap = law.snapshot_bootstrap_dependencies(snapshot, root, package)
        namespaces = frozenset(
            FlextInfraUtilitiesCodegenNamespace.repository_namespace_packages(root)
        )

        def owner(module: str) -> str | None:
            """Elect the import-law namespace that owns one module.

            Returns:
                The public package, the independent ``<namespace>.<pkg>``, or
                None outside both.

            """
            parts = module.split(".")
            if parts[0] == package:
                return package
            return (
                FlextInfraUtilitiesCodemodNativePackage._codemod_namespace_owner(
                    parts, namespaces
                )
                if parts[0] in namespaces
                else None
            )

        return tuple(
            sorted(
                path.relative_to(root).as_posix()
                for path in FlextInfraUtilitiesWorkspaceSnapshot.workspace_python_files(
                    snapshot, root
                )
                if (located := law.snapshot_import_namespace(snapshot, root, path))
                is not None
                and (namespace := owner(located[1])) is not None
                and law.import_module_role(
                    located[1],
                    namespace=namespace,
                    bootstrap=located[1] in bootstrap,
                )
                in roles
            )
        )

    @classmethod
    def codemod_layer_zero_files(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> t.StrTuple:
        """Project-relative paths of every module the import law ranks layer zero.

        Returns:
            The sorted POSIX paths, relative to the project root.

        """
        return cls.codemod_role_files(
            snapshot, project, (c.Infra.IMPORT_LAW_LAYER_ZERO_ROLE,)
        )

    @staticmethod
    def _codemod_binding_index(
        snapshot: p.Infra.WorkspaceSnapshot, path: Path
    ) -> p.Infra.RopeSourceBindingIndex:
        """Rope's source binding index of one snapshot module.

        Returns:
            The index Rope builds over the module's one parse.

        """
        FlextInfraUtilitiesWorkspaceSnapshot.workspace_source(snapshot, path)
        return FlextInfraUtilitiesRopeRuntime.require_source_module(
            FlextInfraUtilitiesRopeCore.resolve_pymodule(
                snapshot.engine,
                FlextInfraUtilitiesRopeRuntime.file_resource_at(snapshot.engine, path),
            )
        ).get_source_binding_index()

    @classmethod
    def codemod_imported_top_modules(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> t.StrTuple:
        """Top-level packages the project's modules import absolutely.

        Returns:
            The sorted distinct top-level module names.

        """
        root = project.resolve()
        if root in snapshot.absolute_import_roots:
            return snapshot.absolute_import_roots[root]
        snapshots = FlextInfraUtilitiesWorkspaceSnapshot
        imported: set[str] = set()
        for path in snapshots.workspace_python_files(snapshot, root):
            imported.update(
                cls._codemod_binding_index(snapshot, path).absolute_import_roots()
            )
        snapshot.absolute_import_roots[root] = tuple(sorted(imported))
        return snapshot.absolute_import_roots[root]

    @classmethod
    def codemod_library_protocol_names(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> t.StrTuple:
        """Library attributes the protocols family names that are protocols.

        Each ``<module>.<Name>`` a protocols-family file reads through an
        ``import`` binding is resolved on its library module; a name whose
        object is a ``typing.Protocol`` is a protocol the family may re-expose
        (ADR-028). Every other library type stays a typings alias.

        Returns:
            The sorted protocol attribute names.

        """
        root = project.resolve()
        snapshots = FlextInfraUtilitiesWorkspaceSnapshot
        families = tuple(
            PurePosixPath(glob.removeprefix("**/").removesuffix("/**"))
            for glob in c.Infra.CODEMOD_PROTOCOLS_FAMILY_GLOBS
        )
        names: set[str] = set()
        for path in snapshots.workspace_python_files(snapshot, root):
            relative = PurePosixPath(path.relative_to(root).as_posix())
            if not any(
                family.name in relative.parts or relative.name == family.name
                for family in families
            ):
                continue
            bound = {
                alias or name: name
                for layout in cls._codemod_binding_index(
                    snapshot, path
                ).import_layouts()
                if layout.module_name is None and layout.level == 0
                for name, alias, _region in layout.aliases
            }
            tree = snapshots.workspace_module_tree(snapshot, path)
            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Attribute)
                    and isinstance(node.value, ast.Name)
                    and node.value.id in bound
                    and is_protocol(
                        getattr(import_module(bound[node.value.id]), node.attr)
                    )
                ):
                    names.add(node.attr)
        return tuple(sorted(names))

    @classmethod
    def codemod_facade_packages(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> t.StrTuple:
        """The own package and every imported package publishing facade aliases.

        A package whose generated lazy exports publish runtime aliases is a
        FLEXT facade package wherever it is installed, the same verdict the
        import law reaches; any other imported package is a library.

        Returns:
            The sorted facade package names the project reaches.

        """
        own = FlextInfraUtilitiesPyprojectConform.project_package_name(
            project.absolute()
        )
        return tuple(
            sorted({
                own,
                *(
                    module
                    for module in cls.codemod_imported_top_modules(snapshot, project)
                    if module != own and cls.codemod_provider_aliases(snapshot, module)
                ),
            })
        )

    @classmethod
    def codemod_external_import_rules(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> Mapping[str, t.JsonMapping]:
        """Ban a library import outside the facade families (ADR-028).

        The module of a live import must be the standard library, the own
        package or a FLEXT facade package; family and layer-zero modules are
        rendered as ``ignores``. Every operand is derived from the project, so
        the native scan and ``make mod`` agree without per-finding admission.

        Returns:
            The external-import rule document keyed by id.

        """
        package = FlextInfraUtilitiesPyprojectConform.project_package_name(
            project.absolute()
        )
        catalog = (
            FlextInfraConfig.ssot_config_dir().parent / c.Infra.CODEMOD_CONFIG_RELPATH
        )
        library = c.Infra.CODEMOD_LIBRARY_IMPORT_NAME_UTILITY
        facade = c.Infra.CODEMOD_FACADE_PACKAGE_UTILITY
        shape = c.Infra.CODEMOD_EXTERNAL_IMPORT_SHAPE
        rule_id = f"{shape}{c.Infra.CODEMOD_GENERATED_ID_SEPARATOR}{package}"
        roles = (c.Infra.IMPORT_LAW_LAYER_ZERO_ROLE, c.Infra.IMPORT_LAW_FAMILY_ROLE)
        document: dict[str, t.JsonValue] = {
            "id": rule_id,
            "language": c.Infra.CODEMOD_PYTHON_LANGUAGE,
            "severity": "error",
            "files": ["**/*.py"],
            "utils": {
                **{
                    name: dict(
                        FlextInfraUtilitiesCodemodRules.codemod_provider_utility_rule(
                            catalog, name
                        )
                    )
                    for name in (library, c.Infra.CODEMOD_TYPE_CHECKING_GUARD_UTILITY)
                },
            },
            "rule": {"all": [{"pattern": "$MODULE"}, {"matches": library}]},
            "constraints": {
                "MODULE": {
                    "not": {
                        "any": [
                            {"matches": (c.Infra.CODEMOD_STDLIB_MODULE_UTILITY)},
                            {"matches": (c.Infra.CODEMOD_OWN_PACKAGE_UTILITY)},
                            {"matches": facade},
                        ]
                    }
                }
            },
            "message": (
                "`$MODULE` is a third-party library imported outside the "
                "c/t/p/m/u facade families."
            ),
        }
        ignores: list[t.JsonValue] = [
            f"**/{path}" for path in cls.codemod_role_files(snapshot, project, roles)
        ]
        if ignores:
            document["ignores"] = ignores
        return FlextInfraUtilitiesCodemodRules.tests_tier_documents(document, ignores)

    @classmethod
    def codemod_library_type_rules(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> Mapping[str, t.JsonMapping]:
        """Ban a library type named inline outside the typings family (ADR-028).

        An attribute of a module the file binds by ``import`` and that is a
        library (not stdlib, own or FLEXT facade package), written as a type in
        an annotation or as an ``isinstance``/``issubclass`` operand, is a
        hidden second typings owner. The typings family and layer-zero modules
        are rendered as ``ignores``; every operand is derived from the project.

        Returns:
            The library-type rule document keyed by id.

        """
        package = FlextInfraUtilitiesPyprojectConform.project_package_name(
            project.absolute()
        )
        facade = c.Infra.CODEMOD_FACADE_PACKAGE_UTILITY
        stdlib = c.Infra.CODEMOD_STDLIB_MODULE_UTILITY
        own = c.Infra.CODEMOD_OWN_PACKAGE_UTILITY
        shape = c.Infra.CODEMOD_LIBRARY_TYPE_SHAPE
        rule_id = f"{shape}{c.Infra.CODEMOD_GENERATED_ID_SEPARATOR}{package}"
        check: t.JsonDict = {
            "inside": {"kind": "argument_list", "inside": {"matches": "check"}}
        }
        layer_zero: list[t.JsonValue] = [
            f"**/{path}" for path in cls.codemod_layer_zero_files(snapshot, project)
        ]
        library: t.JsonDict = {
            "not": {"any": [{"matches": stdlib}, {"matches": own}, {"matches": facade}]}
        }
        document: dict[str, t.JsonValue] = {
            "id": rule_id,
            "language": c.Infra.CODEMOD_PYTHON_LANGUAGE,
            "severity": "error",
            "files": ["**/*.py"],
            "ignores": [
                *c.Infra.CODEMOD_TYPINGS_FAMILY_GLOBS,
                *c.Infra.CODEMOD_PROTOCOLS_FAMILY_GLOBS,
                *layer_zero,
            ],
            "utils": {
                "check": {
                    "kind": "call",
                    "has": {
                        "field": "function",
                        "regex": r"^(?:isinstance|issubclass)$",
                    },
                },
                "library-attribute": {
                    "kind": "attribute",
                    "all": [
                        {
                            "has": {
                                "field": "object",
                                "kind": "identifier",
                                "pattern": "$LIB",
                            }
                        },
                        {"has": {"field": "attribute", "pattern": "$ATTR"}},
                    ],
                    "inside": {
                        "kind": "module",
                        "stopBy": "end",
                        "has": {
                            "stopBy": "end",
                            "kind": "import_statement",
                            "any": [
                                {
                                    "has": {
                                        "kind": "dotted_name",
                                        "all": [
                                            {"pattern": "$LIB"},
                                            {"pattern": "$MODULE"},
                                        ],
                                    }
                                },
                                {
                                    "has": {
                                        "kind": "aliased_import",
                                        "all": [
                                            {
                                                "has": {
                                                    "field": "name",
                                                    "pattern": "$MODULE",
                                                }
                                            },
                                            {
                                                "has": {
                                                    "field": "alias",
                                                    "pattern": "$LIB",
                                                }
                                            },
                                        ],
                                    }
                                },
                            ],
                        },
                    },
                },
            },
            "rule": {
                "matches": "library-attribute",
                "any": [
                    {"inside": {"kind": "type", "stopBy": "end"}},
                    {"all": [{"nthChild": 2}, check]},
                    {
                        "inside": {
                            "stopBy": "end",
                            "any": [
                                {"kind": "binary_operator"},
                                {"kind": "tuple"},
                                {"kind": "parenthesized_expression"},
                            ],
                            "nthChild": 2,
                            **check,
                        }
                    },
                ],
            },
            "constraints": {"MODULE": library},
            "message": (
                "`$MODULE` library type named inline: alias it once in the typings "
                "family and reference it as `t.<Domain>.<Name>`."
            ),
        }
        # The protocols family may re-expose a library protocol; any other
        # library type it names inline still belongs to the typings family.
        protocol_id = f"{rule_id}{c.Infra.CODEMOD_GENERATED_ID_SEPARATOR}protocols"
        protocols = cls.codemod_library_protocol_names(snapshot, project)
        constraints: t.JsonDict = {"MODULE": library}
        if protocols:
            constraints["ATTR"] = {
                "not": {"regex": f"^(?:{'|'.join(map(re.escape, protocols))})$"}
            }
        # The tests-tier delta names pytest types directly (pytest fixtures
        # and hooks); every other library type there still belongs to `t`.
        return {
            **FlextInfraUtilitiesCodemodRules.tests_tier_documents(
                document, layer_zero
            ),
            protocol_id: {
                **document,
                "id": protocol_id,
                "files": list(c.Infra.CODEMOD_PROTOCOLS_FAMILY_GLOBS),
                "ignores": layer_zero,
                "constraints": constraints,
            },
        }

    @classmethod
    def _layer_zero_helpers(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> set[str]:
        """Collect own helpers admitted by the normalization owner's native proof.

        Returns:
            The admitted native module identities.

        Raises:
            ValueError: If a layer-zero source lacks an authenticated namespace.

        """
        sources = {
            path: source.text
            for path, source in (
                FlextInfraUtilitiesWorkspaceSnapshot.workspace_sources(snapshot).items()
            )
        }
        helpers: set[str] = set()
        for relative in cls.codemod_layer_zero_files(snapshot, project):
            path = project.resolve() / relative
            located = FlextInfraUtilitiesImportLaw.snapshot_import_namespace(
                snapshot, project.resolve(), path
            )
            if located is None:
                message = f"Layer-zero module has no native namespace: {path}"
                raise ValueError(message)
            state = m.Infra.ImportLawPass(
                scope=m.Infra.ImportLawScope(
                    project_root=project.resolve(),
                    file_path=path,
                    namespace_dir=located[0],
                    module=located[1],
                    layer=FlextInfraUtilitiesImportLaw.module_import_layer(located[1]),
                    own_exports=frozenset(),
                ),
                tree=FlextInfraUtilitiesWorkspaceSnapshot.workspace_module_tree(
                    snapshot, path
                ),
                parents={},
                bindings={},
                root_exports={},
                sources=sources,
                source_project=snapshot.engine,
            )
            for layout in cls._codemod_binding_index(snapshot, path).import_layouts():
                for name, _alias, _region in layout.aliases:
                    target = layout.module_name or name
                    if target.startswith(f"{state.scope.namespace}.") and (
                        FlextInfraUtilitiesImportLaw.import_law_layer_zero_helper(
                            state, target
                        )
                    ):
                        helpers.add(target)
        return helpers

    @classmethod
    def codemod_layer_zero_rules(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> Mapping[str, t.JsonMapping]:
        """Ban own-root/family imports, admitting only native-proven helpers.

        A settings/config (or lazy-loader) module owns its declarations before
        any facade family exists, so it imports neither its own root facade
        nor an own facade family, TYPE_CHECKING included. Own helpers require
        the normalization owner's complete native identity and acyclicity proof.
        Exact admitted identities are projected, not inferred by regex. The
        layer-zero files are rendered as exact ``files`` globs and the own
        package is the native ``own-package`` utility, so the native scan and
        ``make mod`` consume the same source-derived admission decision.
        Native namespace, helper completeness and cycle errors propagate unchanged.

        Returns:
            The two layer-zero rule documents keyed by id, or nothing when the
            project has no layer-zero module.

        """
        files: list[t.JsonValue] = [
            f"**/{relative}"
            for relative in cls.codemod_layer_zero_files(snapshot, project)
        ]
        if not files:
            return {}
        package = FlextInfraUtilitiesPyprojectConform.project_package_name(
            project.absolute()
        )
        helpers = cls._layer_zero_helpers(snapshot, project)
        separator = c.Infra.CODEMOD_GENERATED_ID_SEPARATOR
        root_name = c.Infra.CODEMOD_ROOT_IMPORTED_NAME_UTILITY
        root_rule = FlextInfraUtilitiesCodemodRules.codemod_provider_utility_rule(
            FlextInfraConfig.ssot_config_dir().parent / c.Infra.CODEMOD_CONFIG_RELPATH,
            root_name,
        )
        own: t.JsonDict = {"MODULE": {"matches": c.Infra.CODEMOD_OWN_PACKAGE_UTILITY}}
        own_module: t.JsonDict = {
            "MODULE": {
                "all": [
                    {"matches": c.Infra.CODEMOD_OWN_PACKAGE_UTILITY},
                    {"not": cls.codemod_exact_names_rule(tuple(helpers))},
                ]
            }
        }
        facade_shape = c.Infra.CODEMOD_LAYER_ZERO_FACADE_IMPORT_SHAPE
        module_shape = c.Infra.CODEMOD_LAYER_ZERO_MODULE_IMPORT_SHAPE
        facade_id = f"{facade_shape}{separator}{package}"
        module_id = f"{module_shape}{separator}{package}"
        return {
            facade_id: {
                "id": facade_id,
                "language": c.Infra.CODEMOD_PYTHON_LANGUAGE,
                "severity": "error",
                "files": files,
                "utils": {root_name: dict(root_rule)},
                "rule": {
                    "matches": root_name,
                    "inside": {
                        "stopBy": "end",
                        "kind": "import_from_statement",
                        "has": {"field": "module_name", "pattern": "$MODULE"},
                    },
                },
                "constraints": own,
                "message": (
                    "Layer-zero settings/config imports from its own root "
                    "`$MODULE`, including TYPE_CHECKING: use native or valid "
                    "upstream contracts, never its own namespace."
                ),
            },
            module_id: {
                "id": module_id,
                "language": c.Infra.CODEMOD_PYTHON_LANGUAGE,
                "severity": "error",
                "files": files,
                "rule": {
                    "any": [
                        {
                            "kind": "import_from_statement",
                            "has": {
                                "field": "module_name",
                                "kind": "dotted_name",
                                "pattern": "$MODULE",
                                "regex": r"\.",
                            },
                        },
                        {
                            "kind": "dotted_name",
                            "pattern": "$MODULE",
                            "any": [
                                {"inside": {"kind": "import_statement"}},
                                {
                                    "inside": {
                                        "kind": "aliased_import",
                                        "field": "name",
                                        "inside": {"kind": "import_statement"},
                                    }
                                },
                            ],
                        },
                    ]
                },
                "constraints": own_module,
                "message": (
                    "Layer-zero settings/config imports its own namespace "
                    "`$MODULE`, including TYPE_CHECKING: use native, valid "
                    "upstream contracts or an identity-proven acyclic layer-zero "
                    "helper."
                ),
            },
        }


__all__: list[str] = ["FlextInfraUtilitiesCodemodNativePackage"]
