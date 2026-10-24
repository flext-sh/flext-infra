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

from flext_infra import c, config, m, p, t
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
        """Standard library: ``sys.stdlib_module_names`` plus declared backports.

        Returns:
            The ``stdlib-module`` utility rule.

        """
        del project
        backports = config.Infra.tooling.lazy_init.stdlib_backports
        return {
            c.Infra.CodemodContextPredicate.STDLIB_MODULE.value: (
                cls.codemod_module_names_rule(
                    tuple(sorted({*sys.stdlib_module_names, *backports}))
                )
            ),
        }

    @staticmethod
    def codemod_generated_module_utilities(
        project: Path,
    ) -> t.MappingKV[str, t.JsonMapping]:
        """Generated module: a module whose first line is the generator header.

        The same header ``generated_source`` reads proves a file is a
        generator projection, so rules skip generated files through this one
        derived fact instead of listing file names.

        Returns:
            The ``generated-module`` utility rule.

        """
        del project
        return {
            c.Infra.CodemodContextPredicate.GENERATED_MODULE.value: {
                "kind": "module",
                "has": {
                    "kind": "comment",
                    "nthChild": 1,
                    "regex": rf"^{re.escape(c.Infra.AUTOGEN_HEADER)}$",
                },
            },
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
    def codemod_native_generated(
        cls, project: Path, spec: m.Infra.CodegenAstGrepSpec
    ) -> m.Infra.CodemodNativeGenerated:
        """Render every generated utility, then every rule document, in memory.

        Renderers run after the producers because rendered rules reference the
        generated utilities through ``matches``. Only ``make mod`` consumes
        them: its native cascade stages them; nothing is projected to disk.

        Returns:
            The project's generated utility and rule documents keyed by id.

        """
        root = project.absolute()
        return m.Infra.CodemodNativeGenerated(
            utilities=cls.codemod_native_utilities(root, spec.producers),
            rules=cls.codemod_native_rules(root, spec),
        )

    @classmethod
    def codemod_native_render(
        cls,
        project: Path,
        entry: m.Infra.CodegenAstGrepRendererSpec,
        facts: dict[str, p.Model],
    ) -> t.MappingKV[str, t.JsonMapping]:
        """Run one renderer, passing its facts model computed once per generation.

        Returns:
            The renderer's rule documents keyed by rule id, strictly validated.

        Raises:
            TypeError: If the renderer or its facts producer is not declared,
                or the facts producer returns no model.

        """
        renderer = getattr(cls, entry.name, None)
        if not callable(renderer):
            msg = f"ast-grep rule renderer is not declared: {entry.name}"
            raise TypeError(msg)
        adapter = u.type_adapter(TypeForm(t.MappingKV[str, t.JsonMapping]))
        if entry.facts is None:
            return adapter.validate_python(renderer(project), strict=True)
        if entry.facts not in facts:
            producer = getattr(cls, entry.facts, None)
            if not callable(producer):
                msg = f"ast-grep facts producer is not declared: {entry.facts}"
                raise TypeError(msg)
            model = producer(project)
            if not isinstance(model, p.Model):
                msg = f"ast-grep facts producer returned no model: {entry.facts}"
                raise TypeError(msg)
            facts[entry.facts] = model
        return adapter.validate_python(
            renderer(project, facts[entry.facts]), strict=True
        )

    @classmethod
    def codemod_native_rules(
        cls, project: Path, spec: m.Infra.CodegenAstGrepSpec
    ) -> t.MappingKV[str, t.JsonMapping]:
        """Run every registered renderer and merge its rule documents by id.

        Returns:
            Every generated native rule document keyed by its rule id.

        Raises:
            ValueError: If a rule id repeats, names an unregistered shape, or
                disagrees with its document id.

        """
        documents: dict[str, t.JsonMapping] = {}
        facts: dict[str, p.Model] = {}
        for entry in spec.renderers:
            rendered = cls.codemod_native_render(project, entry, facts)
            for rule_id, document in rendered.items():
                shape = rule_id.partition(c.Infra.CODEMOD_GENERATED_ID_SEPARATOR)[0]
                if shape not in entry.shapes:
                    msg = (
                        f"ast-grep renderer {entry.name} emitted an unregistered "
                        f"shape: {rule_id}"
                    )
                    raise ValueError(msg)
                if rule_id in documents:
                    msg = f"ast-grep rule id rendered twice: {rule_id}"
                    raise ValueError(msg)
                if document.get("id") != rule_id:
                    msg = f"ast-grep rule document id disagrees with {rule_id}"
                    raise ValueError(msg)
                documents[rule_id] = document
        return MappingProxyType(dict(sorted(documents.items())))

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
