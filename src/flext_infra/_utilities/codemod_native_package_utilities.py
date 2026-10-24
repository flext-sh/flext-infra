"""Package-scope SSOT facts generated as native ast-grep utility rules.

The names a package publishes and the facade-family packages a project owns
are read statically: package initializers through the Griffe owner, family
directories from the facade-family declarations. Nothing is imported, so a
tests-tier package is as valid a scope as the public package.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
from contextlib import closing
from pathlib import Path, PurePosixPath

from flext_cli import u

from flext_infra import FlextInfraConfig, c, m, t
from flext_infra._utilities.codemod_rules import FlextInfraUtilitiesCodemodRules
from flext_infra._utilities.namespace import FlextInfraUtilitiesCodegenNamespace
from flext_infra._utilities.pyproject import FlextInfraUtilitiesPyproject
from flext_infra._utilities.python_model import FlextInfraUtilitiesPythonModel
from flext_infra._utilities.rope_analysis_workspace import (
    FlextInfraUtilitiesRopeAnalysisWorkspace,
)
from flext_infra._utilities.rope_core import FlextInfraUtilitiesRopeCore


class FlextInfraUtilitiesCodemodNativePackageUtilities:
    """Derive package export and facade-family package utility rules."""

    @staticmethod
    def codemod_exact_names_rule(names: t.StrSequence) -> t.JsonMapping:
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
        project: Path,
    ) -> m.Infra.CodemodPackageExportsFacts:
        """Package facts: exports, directory and direct children of each package.

        Exports are the ``__all__`` each initializer declares, read through the
        Griffe owner (a package without a literal ``__all__`` exports nothing);
        the directory and the child modules and packages come from the same
        source index.

        Returns:
            The typed package facts the utilities and renderers consume.

        """
        root = project.absolute()
        with closing(FlextInfraUtilitiesRopeCore.init_rope_workspace(root)) as rope:
            index = FlextInfraUtilitiesRopeAnalysisWorkspace.index_rope_workspace(
                rope, root
            )
            owned = tuple(
                entry
                for entry in index.modules_by_path.values()
                if entry.module_name and entry.file_path.is_relative_to(root)
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
            run = FlextInfraUtilitiesPythonModel.python_model_run(rope, packages)
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
        cls, project: Path
    ) -> t.MappingKV[str, t.JsonMapping]:
        """One ``exports--<dotted package>`` utility per package of the project.

        Returns:
            The package export utilities rendered from the export facts.

        """
        facts = cls.codemod_package_export_facts(project)
        return {
            f"{c.Infra.CODEMOD_PACKAGE_EXPORTS_UTILITY}"
            f"{c.Infra.CODEMOD_GENERATED_ID_SEPARATOR}{package}": (
                cls.codemod_exact_names_rule(names)
            )
            for package, names in facts.exports.items()
        }

    @staticmethod
    def codemod_facade_family_package_utilities(
        project: Path,
    ) -> t.MappingKV[str, t.JsonMapping]:
        """Facade-family packages: ``<own root>._<family>`` of every family.

        The family directories come from the facade-family declarations, so a
        layer-zero singleton module (``pkg._settings``) is not a family package.

        Returns:
            The ``facade-family-package`` utility rule of the project.

        """
        roots = sorted({
            FlextInfraUtilitiesPyproject.project_package_name(project.absolute()),
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
    def _codemod_name_utils() -> t.JsonMapping:
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
        return {
            "binding": dict(binding),
            "local-binding": {
                "all": [
                    {"matches": "binding"},
                    *(
                        {"not": {"inside": {"kind": kind, "stopBy": "end"}}}
                        for kind in ("import_from_statement", "import_statement")
                    ),
                ],
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
    ) -> t.MappingKV[str, t.StrTuple]:
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
    ) -> t.MappingKV[str, str]:
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
        cls, project: Path, facts: m.Infra.CodemodPackageExportsFacts
    ) -> t.MappingKV[str, t.JsonMapping]:
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
    def _codemod_header_rule(cls, names: t.StrSequence) -> t.JsonMapping:
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
                    "all": [
                        {"matches": "use"},
                        cls.codemod_exact_names_rule(names),
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
        cls, project: Path, facts: m.Infra.CodemodPackageExportsFacts
    ) -> t.MappingKV[str, t.JsonMapping]:
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
        del project
        resolvable = cls.codemod_header_resolvable_names(facts)
        utils = cls._codemod_name_utils()
        documents: dict[str, t.JsonMapping] = {}
        for package, children in sorted(facts.modules.items()):
            branches = [
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
        cls, package: str, branches: t.SequenceOf[t.JsonMapping]
    ) -> t.JsonMapping:
        """Match ``<child>.<Name>`` bound by a module-object import of ``package``.

        Returns:
            The native rule of one ``module-member`` document.

        """
        return {
            "all": [
                {"kind": "attribute"},
                {"any": list(branches)},
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
                            *(
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
                            ),
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
    ) -> t.MappingKV[str, t.JsonMapping]:
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
        branches: dict[str, list[t.JsonMapping]] = {}
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
        cls, module: str, names: t.StrSequence
    ) -> t.JsonMapping:
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


__all__: list[str] = ["FlextInfraUtilitiesCodemodNativePackageUtilities"]
