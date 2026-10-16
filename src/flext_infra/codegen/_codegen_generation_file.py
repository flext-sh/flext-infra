"""Canonical generated package artifact selection.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from pathlib import Path

from flext_infra import c, m, t, u
from flext_infra.codegen import FlextInfraCodegenGenerationStandardMixin


class FlextInfraCodegenGenerationFileMixin(FlextInfraCodegenGenerationStandardMixin):
    """Render canonical initializer artifacts from one validated plan."""

    @classmethod
    def init_template_paths(cls) -> t.VariadicTuple[Path]:
        """Return the closed lazy-init template input set.

        Returns:
            The closed lazy-init template input set.

        """
        return (cls._template_path(c.Infra.TEMPLATE_ROOT_INIT),)

    @classmethod
    def render_init(cls, plan: m.Infra.LazyInitPlan) -> str:
        """Render a lazy facade for each importable package boundary.

        Every package uses the same declared-export PEP 562 contract.

        Returns:
            The resulting ``str``.

        """
        bootstrap_root = c.Infra.LAZY_BOOTSTRAP_ROOT_PACKAGE
        current_pkg = plan.context.current_pkg
        if current_pkg.startswith(f"{bootstrap_root}."):
            root = plan.context.pkg_dir
            for _ in current_pkg.split(".")[1:]:
                root = root.parent
            loader = root.parent.joinpath(
                *c.Infra.LAZY_BOOTSTRAP_MODULE.split("."),
            ).with_suffix(c.Infra.EXT_PYTHON)
            tree = ast.parse(loader.read_text(encoding=c.DEFAULT_ENCODING))
            dependencies = {
                node.module.rsplit(".", maxsplit=1)[0]
                for node in tree.body
                if isinstance(node, ast.ImportFrom) and node.module
            }
            if any(
                dependency == current_pkg or dependency.startswith(f"{current_pkg}.")
                for dependency in dependencies
            ):
                imports = cls.generate_type_checking(
                    cls._group_imports(cls._type_checking_filtered(plan)),
                    include_flext_types=False,
                    local_package_root=current_pkg,
                    root_names=frozenset({bootstrap_root}),
                )
                runtime = "\n".join(
                    line.removeprefix("    ")
                    for line in imports
                    if line != "if TYPE_CHECKING:"
                )
                docstring = cls._format_root_package_docstring(
                    current_pkg,
                    u.Infra.copyright_notice(plan.context.pkg_dir),
                )
                exports = cls._format_exports_tuple(plan.exports)
                return (
                    f"{c.Infra.AUTOGEN_HEADER}\n"
                    f"{docstring}\n\n"
                    "from __future__ import annotations\n\n"
                    f"{runtime}\n\n"
                    f"__all__: tuple[str, ...] = {exports}\n"
                )
        return cls._render_root(plan)


__all__: list[str] = ["FlextInfraCodegenGenerationFileMixin"]
