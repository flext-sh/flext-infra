"""Public-API static helpers for the lazy-init planner."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import override

from flext_infra import c
from flext_infra.codegen._lazy_init_planner_public_root import (
    FlextInfraCodegenLazyInitPlannerPublicRootMixin,
)
from flext_infra.codegen._lazy_init_planner_registry import (
    FlextInfraCodegenLazyInitPlannerRegistryMixin,
)


class FlextInfraCodegenLazyInitPlannerPublicApiMixin(
    FlextInfraCodegenLazyInitPlannerPublicRootMixin,
    FlextInfraCodegenLazyInitPlannerRegistryMixin,
):
    """Root public contract helpers for the lazy-init planner."""

    @staticmethod
    @override
    def _root_public_contract_exports(pkg_dir: Path) -> frozenset[str]:
        """Read explicit public root exports from the package ``_exports.py`` file."""
        exports_path = pkg_dir / c.Infra.ROOT_EXPORTS_FILENAME
        if not exports_path.is_file():
            return frozenset()
        source = exports_path.read_text(encoding=c.Cli.ENCODING_DEFAULT)
        tree = ast.parse(source, filename=str(exports_path))
        exports: set[str] = set()
        try:
            for statement in tree.body:
                exports.update(
                    FlextInfraCodegenLazyInitPlannerPublicApiMixin._public_export_statement_names(
                        statement,
                    )
                )
        except (TypeError, ValueError) as exc:
            msg = f"{exports_path}: {exc}"
            raise ValueError(msg) from exc
        return frozenset(exports)

    @staticmethod
    def _public_export_statement_names(statement: ast.stmt) -> frozenset[str]:
        """Extract public export names from one assignment statement."""
        match statement:
            case ast.Assign(targets=targets, value=value):
                if any(
                    FlextInfraCodegenLazyInitPlannerPublicApiMixin._is_public_exports_target(
                        target
                    )
                    for target in targets
                ):
                    return FlextInfraCodegenLazyInitPlannerPublicApiMixin._literal_string_names(
                        value
                    )
            case ast.AnnAssign(target=target, value=value):
                if value is not None and (
                    FlextInfraCodegenLazyInitPlannerPublicApiMixin._is_public_exports_target(
                        target
                    )
                ):
                    return FlextInfraCodegenLazyInitPlannerPublicApiMixin._literal_string_names(
                        value
                    )
            case _:
                return frozenset()
        return frozenset()

    @staticmethod
    def _is_public_exports_target(target: ast.expr) -> bool:
        """Return whether an assignment target declares root public exports."""
        return isinstance(target, ast.Name) and target.id.endswith(
            c.Infra.ROOT_PUBLIC_EXPORTS_SUFFIX
        )


__all__: list[str] = ["FlextInfraCodegenLazyInitPlannerPublicApiMixin"]
