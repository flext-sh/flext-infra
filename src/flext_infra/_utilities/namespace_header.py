"""Derive the canonical namespace import header facts of one project.

Every module of a governed project imports the namespace objects of the
libraries it declares and its own public aliases through one canonical header;
a module of facade letter ``L`` binds its own letter from the upstream package
its facade extends and the letters above its layer only for type checking.
This producer emits the facts as pure data from installed metadata and the
runtime facades; the generated native rules render and enforce the header.
Nothing here lists a package, alias or letter.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import inspect
from importlib import import_module
from pathlib import Path

from packaging.requirements import Requirement
from packaging.utils import canonicalize_name

from flext_infra import c, config, t
from flext_infra._utilities import (
    FlextInfraUtilitiesCodegenNamespace,
    FlextInfraUtilitiesCodemodNativeUtilities,
    FlextInfraUtilitiesCodemodRules,
    FlextInfraUtilitiesPyproject,
)


class FlextInfraUtilitiesNamespaceHeader:
    """Pure facts of the canonical namespace import header of a project."""

    @classmethod
    def namespace_import_header(cls, project: Path) -> t.JsonMapping:
        """Return the import header facts of ``project``.

        ``aliases`` are the lowercase names the package root exports bound to
        a class, plus the layer-zero root singletons it exports. ``namespace``
        maps each namespace object of a directly required library to its
        import package. ``families`` maps every facade letter to its module
        stem, private directory and the package its facade class extends.

        Returns:
            The JSON facts consumed by the generated header rules.

        """
        package = FlextInfraUtilitiesPyproject.project_package_name(project)
        root = import_module(package)
        aliases = sorted(
            name
            for name in cls._root_exports(package)
            if isinstance(getattr(root, name), type)
            or name in c.Infra.IMPORT_LAW_ROOT_SINGLETONS
        )
        families = {
            letter: {
                "module": family.module,
                "directory": family.directory,
                "upstream": cls._upstream(package, letter),
            }
            for letter, family in sorted(
                FlextInfraUtilitiesCodegenNamespace.facade_families().items()
            )
        }
        return {
            "package": package,
            "aliases": aliases,
            "namespace": cls._namespace_objects(project, package),
            "families": families,
            "layers": list(config.Infra.tooling.lazy_init.import_layer_order),
        }

    @staticmethod
    def _root_exports(package: str) -> t.StrSequence:
        """Lowercase public names the package root publishes.

        Returns:
            The exported names that are neither dunders nor class names.

        """
        exported: t.StrSequence = getattr(import_module(package), "__all__", ())
        return tuple(
            name for name in exported if name.islower() and not name.startswith("_")
        )

    @classmethod
    def _namespace_objects(cls, project: Path, package: str) -> t.StrMapping:
        """Map each directly required library's namespace object to its package.

        A namespace object is an exported instance that is not a layer-zero
        root (settings, config, the lazy loader): ``cli`` of the CLI library.

        Returns:
            Namespace object name to the import package providing it.

        """
        requirements = FlextInfraUtilitiesCodemodRules.codemod_project_requirements(
            project
        ).unwrap()[1]
        # A requirement guarded by an extra is not part of the runtime surface.
        parsed = tuple(Requirement(raw) for raw in requirements)
        required = {
            canonicalize_name(requirement.name)
            for requirement in parsed
            if requirement.marker is None or requirement.marker.evaluate({"extra": ""})
        }
        providers = FlextInfraUtilitiesCodemodNativeUtilities.codemod_installed_import_packages()
        letters = tuple(FlextInfraUtilitiesCodegenNamespace.facade_families())
        objects: dict[str, str] = {}
        for module, distributions in sorted(providers.items()):
            if module == package or not distributions & required:
                continue
            dependency = import_module(module)
            # Only a namespace package (one publishing every facade family
            # letter as a class) exposes a namespace object; a third-party
            # library's exported instances are its own surface.
            if not all(
                isinstance(getattr(dependency, letter, None), type)
                for letter in letters
            ):
                continue
            for name in cls._root_exports(module):
                value = getattr(dependency, name)
                if (
                    name in c.Infra.IMPORT_LAW_LAYER_ZERO_ROOTS
                    or isinstance(value, type)
                    or inspect.ismodule(value)
                    or inspect.isroutine(value)
                ):
                    continue
                if objects.setdefault(name, module) != module:
                    msg = (
                        f"namespace object {name} is provided by both "
                        f"{objects[name]} and {module}"
                    )
                    raise ValueError(msg)
        return objects

    @staticmethod
    def _upstream(package: str, letter: str) -> str:
        """The package whose ``letter`` facade this package's ``letter`` extends.

        Returns:
            The first base package that itself publishes ``letter`` as a
            class, or ``package`` when its facade extends no such package.

        """
        facade = getattr(import_module(package), letter, None)
        if not isinstance(facade, type):
            return package
        for base in facade.__mro__[1:]:
            owner = base.__module__.partition(".")[0]
            if owner != package and isinstance(
                getattr(import_module(owner), letter, None), type
            ):
                return owner
        return package


__all__: list[str] = ["FlextInfraUtilitiesNamespaceHeader"]
