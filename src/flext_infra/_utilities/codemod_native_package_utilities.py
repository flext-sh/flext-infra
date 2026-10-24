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
from pathlib import Path

from flext_infra import c, t
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

    @classmethod
    def codemod_package_export_utilities(
        cls, project: Path
    ) -> t.MappingKV[str, t.JsonMapping]:
        """Package exports: the ``__all__`` each package initializer declares.

        One utility per package, ``exports--<dotted package>``, read through
        the Griffe owner from the initializer source; a package without a
        literal ``__all__`` exports nothing.

        Returns:
            The package export utilities of every package of the project.

        """
        root = project.absolute()
        with closing(FlextInfraUtilitiesRopeCore.init_rope_workspace(root)) as rope:
            index = FlextInfraUtilitiesRopeAnalysisWorkspace.index_rope_workspace(
                rope, root
            )
            packages = {
                entry.module_name: entry.file_path
                for entry in index.modules_by_path.values()
                if entry.module_name
                and entry.file_path.name == c.Infra.INIT_PY
                and entry.file_path.is_relative_to(root)
            }
            run = FlextInfraUtilitiesPythonModel.python_model_run(rope, packages)
            return {
                f"{c.Infra.CODEMOD_PACKAGE_EXPORTS_UTILITY}"
                f"{c.Infra.CODEMOD_GENERATED_ID_SEPARATOR}{package}": (
                    cls.codemod_exact_names_rule(
                        FlextInfraUtilitiesPythonModel.python_model_exports(
                            FlextInfraUtilitiesPythonModel.python_model_module_at(
                                run, path, package
                            )
                        )
                        or ()
                    )
                )
                for package, path in sorted(packages.items())
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


__all__: list[str] = ["FlextInfraUtilitiesCodemodNativePackageUtilities"]
