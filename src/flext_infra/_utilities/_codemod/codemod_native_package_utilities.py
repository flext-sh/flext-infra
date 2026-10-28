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

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

import ast
import re
from collections.abc import Mapping, Sequence
from importlib import import_module
from importlib.util import find_spec
from pathlib import Path, PurePosixPath
from typing import is_protocol

from flext_cli import u

from flext_infra import FlextInfraConfig, c, m, p, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesImportLaw,
    FlextInfraUtilitiesPythonModel,
    FlextInfraUtilitiesWorkspaceSnapshot,
)
from flext_infra._utilities._codemod import FlextInfraUtilitiesCodemodRules
from flext_infra._utilities._pyproject import FlextInfraUtilitiesPyprojectConform
from flext_infra._utilities._rope._analysis.rope_analysis_workspace import (
    FlextInfraUtilitiesRopeAnalysisWorkspace,
)
from flext_infra._utilities._rope._analysis.sourcescan import (
    FlextInfraUtilitiesRopeAnalysisSourceScan,
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
    ) -> m.Infra.CodemodPackageExportsFacts:
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
    def codemod_package_export_utilities(
        cls, snapshot: p.Infra.WorkspaceSnapshot, project: Path
    ) -> Mapping[str, t.JsonMapping]:
        """One ``exports--<dotted package>`` utility per package of the project.

        Returns:
            The package export utilities rendered from the export facts.

        """
        facts = cls.codemod_package_export_facts(snapshot, project)
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

        Returns:
            The ``facade-family-package`` utility rule of the project.

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
                    {"not": {"inside": {"kind": "attribute", "field": "attribute"}}},
                    {"not": {"inside": {"kind": "keyword_argument", "field": "name"}}},
                ]
            },
        }

    @staticmethod
    def _codemod_declaring_packages(
        facts: m.Infra.CodemodPackageExportsFacts,
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
        cls, facts: m.Infra.CodemodPackageExportsFacts
    ) -> Mapping[str, str]:
        """Names whose canonical package import is unambiguous from any module.

        A name resolves when exactly one shallowest package declares it; a
        module inside a deeper declaring package imports it from that package.

        Returns:
            Resolvable name to its shallowest declaring package.

        """
        resolvable: dict[str, str] = {}
        for name, packages in cls._codemod_declaring_packages(facts).items():
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
        facts: m.Infra.CodemodPackageExportsFacts,
    ) -> Mapping[str, t.JsonMapping]:
        """Insert the nearest declaring package's import for unbound names.

        One rule per package and scope inserts, after the module's first
        future or plain import, one ``from <package> import ...`` line with
        every name that package resolves in that scope, when the module uses
        one of them without binding it anywhere; the Ruff import-fix stage
        prunes the unused names and orders the block. A module inside a
        declaring package imports from the deepest declaring package that
        contains it; every other module imports from the unique shallowest
        declaring package.

        Returns:
            The generated ``import-header`` rule documents keyed by id.

        """
        del snapshot
        del project
        directories = facts.directories
        groups: dict[tuple[str, str | None, t.StrTuple], set[str]] = {}
        resolvable = cls.codemod_header_resolvable_names(facts)
        for name, packages in cls._codemod_declaring_packages(facts).items():
            if name not in resolvable:
                continue
            for package in packages:
                home = PurePosixPath(directories[package])
                nested = tuple(
                    sorted(
                        directories[other]
                        for other in packages
                        if other != package
                        and (
                            package == resolvable[name]
                            or PurePosixPath(directories[other]).is_relative_to(home)
                        )
                    )
                )
                scope = None if package == resolvable[name] else home.as_posix()
                groups.setdefault((package, scope, nested), set()).add(name)
        utils = cls._codemod_name_utils()
        documents: dict[str, t.JsonMapping] = {}
        # The root scope is None; order it before every directory scope.
        for (package, scope, nested), names in sorted(
            groups.items(),
            key=lambda item: (
                item[0][0],
                item[0][1] is not None,
                item[0][1] or "",
                item[0][2],
            ),
        ):
            qualifier = (
                package
                if scope is None and not nested
                else f"{package}{c.Infra.CODEMOD_GENERATED_ID_SEPARATOR}"
                + u.Cli.sha256_content(f"{scope}\0{'\0'.join(nested)}")[:12]
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
                "fix": f"$ANCHOR\nfrom {package} import {', '.join(sorted(names))}",
            }
            if scope is not None:
                document["files"] = [cls._codemod_directory_glob(scope)]
            if nested:
                document["ignores"] = [
                    cls._codemod_directory_glob(directory) for directory in nested
                ]
            documents[rule_id] = document
        return documents

    @classmethod
    def _codemod_header_rule(cls, names: Sequence[str]) -> t.JsonDict:
        """Anchor on the first future or plain import of a module using ``names``.

        Returns:
            The native rule of one ``import-header`` document.

        """
        imports = ("import_from_statement", "import_statement")
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
                        cls.codemod_exact_names_rule(names),
                        {"matches": "use"},
                        {"pattern": "$USED"},
                        {
                            "not": {
                                "inside": {
                                    "kind": "module",
                                    "stopBy": "end",
                                    "has": {
                                        "stopBy": "end",
                                        "all": [
                                            {"pattern": "$USED"},
                                            {"matches": "binding"},
                                        ],
                                    },
                                }
                            }
                        },
                    ],
                },
            },
        }

    @classmethod
    def codemod_module_member_rules(
        cls,
        snapshot: p.Infra.WorkspaceSnapshot,
        project: Path,
        facts: m.Infra.CodemodPackageExportsFacts,
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
    def _codemod_nearest_publisher(
        facts: m.Infra.CodemodPackageExportsFacts, module: str, name: str
    ) -> str | None:
        """Nearest package containing ``module`` whose ``__all__`` declares ``name``.

        Returns:
            The dotted package, or ``None`` when no ancestor publishes the name.

        """
        package = module.rpartition(".")[0]
        while package:
            if name in facts.exports.get(package, ()):
                return package
            package = package.rpartition(".")[0]
        return None

    @classmethod
    def codemod_package_deep_import_rules(
        cls, project: Path, facts: m.Infra.CodemodPackageExportsFacts
    ) -> Mapping[str, t.JsonMapping]:
        """Rebind a one-name import from a module to its nearest publishing package.

        For each package P, one rule matches ``from <module> import <Name>``
        for every module file below P whose nearest package publishing
        ``Name`` is P, and rewrites it to ``from P import <Name>``. Module files
        and publish sets come from the package facts; a child package is never
        a module file, and a package's own initializer is never rewritten.

        Returns:
            The generated ``deep-import`` rule documents keyed by id.

        """
        del project
        branches: dict[str, list[t.JsonValue]] = {}
        for package, children in sorted(facts.modules.items()):
            for leaf in children:
                module = f"{package}.{leaf}"
                if module in facts.exports:
                    continue
                targets: dict[str, list[str]] = {}
                for owner, names in facts.exports.items():
                    if not module.startswith(f"{owner}."):
                        continue
                    targets[owner] = [
                        name
                        for name in names
                        if name.isidentifier()
                        and cls._codemod_nearest_publisher(facts, module, name) == owner
                    ]
                for owner, names in sorted(targets.items()):
                    if names:
                        branches.setdefault(owner, []).append(
                            cls._codemod_deep_import_branch(module, names)
                        )
        documents: dict[str, t.JsonMapping] = {}
        for owner, alternatives in sorted(branches.items()):
            rule_id = (
                f"{c.Infra.CODEMOD_DEEP_IMPORT_SHAPE}"
                f"{c.Infra.CODEMOD_GENERATED_ID_SEPARATOR}{owner}"
            )
            documents[rule_id] = {
                "id": rule_id,
                "language": c.Infra.CODEMOD_PYTHON_LANGUAGE,
                "message": (
                    f"Import the name from `{owner}`, its nearest publishing "
                    "package, not from a module below it."
                ),
                "ignores": [f"**/{c.Infra.INIT_PY}"],
                "rule": {
                    "kind": "import_from_statement",
                    "regex": c.Infra.CODEMOD_SINGLE_NAME_IMPORT_REGEX,
                    "any": alternatives,
                },
                "fix": f"from {owner} import $NAME",
            }
        return documents

    @classmethod
    def _codemod_deep_import_branch(
        cls, module: str, names: Sequence[str]
    ) -> t.JsonDict:
        """Match an import of one of ``names`` from exactly ``module``.

        Returns:
            The native branch of one ``deep-import`` document.

        """
        return {
            "all": [
                {
                    "has": {
                        "field": "module_name",
                        **cls.codemod_exact_names_rule((module,)),
                    }
                },
                {
                    "has": {
                        "field": "name",
                        "kind": "dotted_name",
                        "pattern": "$NAME",
                        **cls.codemod_exact_names_rule(names),
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
        return tuple(
            sorted(
                path.relative_to(root).as_posix()
                for path in FlextInfraUtilitiesWorkspaceSnapshot.workspace_python_files(
                    snapshot, root
                )
                if (located := law.snapshot_import_namespace(snapshot, root, path))
                is not None
                and located[1].split(".")[0] == package
                and law.import_module_role(located[1], namespace=package) in roles
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
        roots = FlextInfraUtilitiesRopeAnalysisSourceScan.module_absolute_import_roots
        imported: set[str] = set()
        for path in snapshots.workspace_python_files(snapshot, root):
            snapshots.workspace_source(snapshot, path)
            imported.update(roots(snapshots.workspace_module_tree(snapshot, path)))
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
            tree = snapshots.workspace_module_tree(snapshot, path)
            bound = {
                alias.asname or alias.name: alias.name
                for node in ast.walk(tree)
                if isinstance(node, ast.Import)
                for alias in node.names
            }
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
                    if module != own
                    and find_spec(module) is not None
                    and u.runtime_alias_names(module)
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
        return {rule_id: document}

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
        return {
            rule_id: document,
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
            for node in ast.walk(state.tree):
                if not isinstance(node, (ast.Import, ast.ImportFrom)):
                    continue
                for alias in node.names:
                    target = (
                        node.module or ""
                        if isinstance(node, ast.ImportFrom)
                        else alias.name
                    )
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
