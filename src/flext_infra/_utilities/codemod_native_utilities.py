"""Project SSOT facts generated as native ast-grep utility rules.

ast-grep matches one file's syntax; a rule whose meaning depends on the
project it runs in (its own package, the standard library, the runtime
dependency closure) reads that fact as a native utility rule the rule
references through ``matches``. Each producer derives one family of those
utilities from an existing source of truth; ``make gen`` writes them into the
project's catalog overlay, so a native ``ast-grep scan`` and the engine see
the same rule semantics.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
import sys
from functools import cache
from importlib.metadata import packages_distributions
from pathlib import Path
from types import MappingProxyType

from flext_cli import u
from packaging.utils import canonicalize_name
from typing_extensions import TypeForm

from flext_infra import c, m, t
from flext_infra._utilities.codegen_file_plan import FlextInfraUtilitiesCodegenFilePlan
from flext_infra._utilities.codemod_rules import FlextInfraUtilitiesCodemodRules
from flext_infra._utilities.import_law import FlextInfraUtilitiesImportLaw
from flext_infra._utilities.namespace import FlextInfraUtilitiesCodegenNamespace
from flext_infra._utilities.pyproject import FlextInfraUtilitiesPyproject


class FlextInfraUtilitiesCodemodNativeUtilities:
    """Derive native ast-grep utility rules from project sources of truth."""

    @staticmethod
    def codemod_native_utility_document(
        utility_id: str, rule: t.JsonMapping
    ) -> t.JsonMapping:
        """Wrap one native rule object as an ast-grep utility rule document.

        Returns:
            The utility document ast-grep loads from a ``utilDirs`` entry.

        """
        return {
            "id": utility_id,
            "language": c.Infra.CODEMOD_PYTHON_LANGUAGE,
            "rule": dict(rule),
        }

    @staticmethod
    def codemod_module_names_rule(names: t.StrSequence) -> t.JsonMapping:
        """Match a captured dotted module whose top-level package is listed.

        The top-level package is the captured text up to its first dot or
        whitespace, the same reading the import law applies to a module.

        Returns:
            A native ``regex`` rule over the captured module text.

        """
        alternatives = "|".join(re.escape(name) for name in sorted(set(names)))
        return {"regex": rf"^(?:{alternatives})(?:[.\s]|$)"}

    @classmethod
    def codemod_own_package_utilities(
        cls, project: Path
    ) -> t.MappingKV[str, t.JsonMapping]:
        """Own package: the public package, internal tiers, declared namespaces.

        An absolute import between the project's package and its internal
        tiers (tests, examples, scripts) never crosses a package boundary.

        Returns:
            The ``own-package`` utility rule of the project.

        """
        names = (
            FlextInfraUtilitiesPyproject.project_package_name(project),
            *c.Infra.NON_PUBLIC_LAZY_ROOTS,
            *FlextInfraUtilitiesCodegenNamespace.repository_namespace_packages(project),
        )
        return {
            c.Infra.CodemodContextPredicate.OWN_PACKAGE.value: (
                cls.codemod_module_names_rule(names)
            ),
        }

    @classmethod
    def codemod_stdlib_module_utilities(
        cls, project: Path
    ) -> t.MappingKV[str, t.JsonMapping]:
        """Standard library: the interpreter's ``sys.stdlib_module_names``.

        Returns:
            The ``stdlib-module`` utility rule.

        """
        del project
        return {
            c.Infra.CodemodContextPredicate.STDLIB_MODULE.value: (
                cls.codemod_module_names_rule(tuple(sys.stdlib_module_names))
            ),
        }

    @classmethod
    def codemod_runtime_package_utilities(
        cls, project: Path
    ) -> t.MappingKV[str, t.JsonMapping]:
        """Runtime package: an import package of the runtime dependency closure.

        Returns:
            The ``runtime-package`` utility rule of the project.

        """
        modules = cls.codemod_runtime_modules(project)
        return {
            c.Infra.CodemodContextPredicate.RUNTIME_PACKAGE.value: (
                cls.codemod_module_names_rule(tuple(modules))
                if modules
                else {"regex": c.Infra.CODEMOD_NEVER_MATCH_REGEX}
            ),
        }

    @classmethod
    def codemod_runtime_modules(cls, root: Path) -> frozenset[str]:
        """Top-level import names provided by the project's runtime closure.

        Returns:
            The import packages whose distributions the closure contains.

        """
        progress = FlextInfraUtilitiesImportLaw.codemod_progress
        project = FlextInfraUtilitiesCodemodRules.codemod_project_requirements(
            root,
        ).unwrap()
        if not project[1]:
            return frozenset()
        progress(
            f"runtime distributions start requirements={len(project[1])} root={root}",
        )
        distributions = FlextInfraUtilitiesCodemodRules.codemod_distributions()
        progress(f"runtime distributions finish distributions={len(distributions)}")
        progress("runtime dependency closure start")
        closure = FlextInfraUtilitiesCodemodRules.codemod_runtime_closure(
            project[1],
            distributions,
        )
        progress(f"runtime dependency closure finish distributions={len(closure)}")
        progress("runtime import package metadata start")
        packages = cls.codemod_installed_import_packages()
        progress(f"runtime import package metadata finish packages={len(packages)}")
        selected: set[str] = set()
        due = 0.0
        for index, (module, providers) in enumerate(packages.items(), start=1):
            due = progress(
                f"runtime imports package={index}/{len(packages)} "
                f"module={module} selected={len(selected)}",
                due,
            )
            if providers & closure:
                selected.add(module)
        progress(f"runtime imports finish modules={len(selected)}")
        return frozenset(selected)

    @staticmethod
    @cache
    def codemod_installed_import_packages() -> t.MappingKV[str, frozenset[str]]:
        """Map each installed import package to its canonical distributions.

        Installed metadata is a fact of the interpreter environment, fixed for
        the life of the process, so it is read once; a project's runtime
        closure over it is still computed per call.

        Returns:
            Import package to the canonical names of its distributions.

        """
        return MappingProxyType({
            module: frozenset(canonicalize_name(name) for name in providers)
            for module, providers in packages_distributions().items()
        })

    @classmethod
    def codemod_native_utility_sources(
        cls, project: Path, spec: m.Infra.CodegenAstGrepSpec
    ) -> t.MappingKV[Path, str]:
        """Render every generated utility rule file of one project.

        Returns:
            Absolute destination to its generated YAML text, header first.

        """
        directory = project.absolute() / spec.utilities_dir
        return MappingProxyType({
            directory / f"{utility_id}{c.Infra.CODEMOD_RULE_SUFFIX}": (
                f"{c.Infra.AUTOGEN_HEADER}\n"
                f"{u.Cli.yaml_dump_str(document, sort_keys=True)}"
            )
            for utility_id, document in cls.codemod_native_utilities(
                project, spec.producers
            ).items()
        })

    @staticmethod
    def codemod_native_utility_stale(
        project: Path,
        spec: m.Infra.CodegenAstGrepSpec,
        produced: t.IterableOf[Path],
    ) -> t.VariadicTuple[Path]:
        """Return generated utility files no producer emits any more.

        Only files opening with a declared generator header are retired; an
        authored file in the directory is never touched.

        Returns:
            The stale generated files, in path order.

        """
        directory = project.absolute() / spec.utilities_dir
        if not directory.is_dir():
            return ()
        wanted = frozenset(produced)
        return tuple(
            path
            for path in sorted(directory.glob(f"*{c.Infra.CODEMOD_RULE_SUFFIX}"))
            if path not in wanted
            and FlextInfraUtilitiesCodegenFilePlan.generated_source(path)
        )

    @classmethod
    def codemod_native_utilities(
        cls, project: Path, producers: t.StrSequence
    ) -> t.MappingKV[str, t.JsonMapping]:
        """Run every registered producer and merge its utilities by id.

        Returns:
            Every utility document keyed by its utility id.

        Raises:
            TypeError: If a producer is not a declared utility producer.
            ValueError: If two producers emit the same utility id.

        """
        documents: dict[str, t.JsonMapping] = {}
        adapter = u.type_adapter(TypeForm(t.MappingKV[str, t.JsonMapping]))
        for name in producers:
            producer = getattr(cls, name, None)
            if not callable(producer):
                msg = f"ast-grep utility producer is not declared: {name}"
                raise TypeError(msg)
            emitted = adapter.validate_python(producer(project), strict=True)
            for utility_id, rule in emitted.items():
                if utility_id in documents:
                    msg = f"ast-grep utility id produced twice: {utility_id}"
                    raise ValueError(msg)
                documents[utility_id] = cls.codemod_native_utility_document(
                    utility_id, rule
                )
        return MappingProxyType(dict(sorted(documents.items())))


__all__: list[str] = ["FlextInfraUtilitiesCodemodNativeUtilities"]
