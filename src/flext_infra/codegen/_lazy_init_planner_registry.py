"""Lazy registry wrapper decisions for the lazy-init planner."""

from __future__ import annotations

import ast
from pathlib import Path

from flext_infra import c, m


class FlextInfraCodegenLazyInitPlannerRegistryMixin:
    """Resolve thin-wrapper registry metadata for generated lazy init files."""

    @staticmethod
    def _lazy_import_registry_wrapper(
        pkg_dir: Path,
        current_pkg: str,
    ) -> m.Infra.LazyInitRegistryWrapper | None:
        """Return thin-wrapper registry metadata for a package."""
        if not current_pkg:
            return None
        exports_path = pkg_dir / c.Infra.ROOT_EXPORTS_FILENAME
        if exports_path.is_file():
            names = FlextInfraCodegenLazyInitPlannerRegistryMixin._all_exports(
                exports_path
            )
            lazy_names = frozenset(
                name for name in names if name.endswith("LAZY_IMPORTS")
            )
            if len(lazy_names) > 1:
                msg = f"{exports_path}: expected one LAZY_IMPORTS export, got {sorted(lazy_names)!r}"
                raise ValueError(msg)
            if lazy_names:
                return m.Infra.LazyInitRegistryWrapper.model_validate({
                    "module": f"{current_pkg}.{exports_path.stem}",
                    "name": next(iter(lazy_names)),
                    "generated": exports_path.read_text(
                        encoding=c.Cli.ENCODING_DEFAULT,
                    ).startswith(c.Infra.AUTOGEN_HEADER),
                })
            if current_pkg == c.Infra.DIR_TESTS or current_pkg.startswith(
                f"{c.Infra.DIR_TESTS}."
            ):
                msg = (
                    f"{exports_path}: tests registry must export one LAZY_IMPORTS name"
                )
                raise ValueError(msg)
        module_stem = "_exports_lazy" if exports_path.is_file() else exports_path.stem
        return m.Infra.LazyInitRegistryWrapper.model_validate({
            "module": f"{current_pkg}.{module_stem}",
            "name": FlextInfraCodegenLazyInitPlannerRegistryMixin._registry_name(
                pkg_dir,
                current_pkg,
            ),
            "generated": True,
        })

    @staticmethod
    def _registry_name(pkg_dir: Path, current_pkg: str) -> str:
        """Return the canonical lazy registry symbol for a package."""
        segments = tuple(segment for segment in current_pkg.split(".") if segment)
        if current_pkg == c.Infra.DIR_TESTS or current_pkg.startswith(
            f"{c.Infra.DIR_TESTS}."
        ):
            project_dir = pkg_dir
            for _segment in segments:
                project_dir = project_dir.parent
            project_token = project_dir.name.replace("-", "_").upper()
            suffix_tokens = tuple(segment.upper() for segment in segments[1:])
            return "_".join((
                c.Infra.DIR_TESTS.upper(),
                project_token,
                *suffix_tokens,
                "LAZY_IMPORTS",
            ))
        return f"{current_pkg.replace('.', '_').upper()}_LAZY_IMPORTS"

    @staticmethod
    def _all_exports(exports_path: Path) -> frozenset[str]:
        """Read literal ``__all__`` names from a Python module."""
        source = exports_path.read_text(encoding=c.Cli.ENCODING_DEFAULT)
        tree = ast.parse(source, filename=str(exports_path))
        exports: set[str] = set()
        try:
            for statement in tree.body:
                exports.update(
                    FlextInfraCodegenLazyInitPlannerRegistryMixin._all_export_statement_names(
                        statement
                    )
                )
        except (TypeError, ValueError) as exc:
            msg = f"{exports_path}: {exc}"
            raise ValueError(msg) from exc
        return frozenset(exports)

    @staticmethod
    def _all_export_statement_names(statement: ast.stmt) -> frozenset[str]:
        """Extract literal names from a module ``__all__`` assignment."""
        match statement:
            case ast.Assign(targets=targets, value=value):
                if any(
                    FlextInfraCodegenLazyInitPlannerRegistryMixin._is_all_exports_target(
                        target
                    )
                    for target in targets
                ):
                    return FlextInfraCodegenLazyInitPlannerRegistryMixin._literal_string_names(
                        value
                    )
            case ast.AnnAssign(target=target, value=value):
                if value is not None and (
                    FlextInfraCodegenLazyInitPlannerRegistryMixin._is_all_exports_target(
                        target
                    )
                ):
                    return FlextInfraCodegenLazyInitPlannerRegistryMixin._literal_string_names(
                        value
                    )
            case _:
                return frozenset()
        return frozenset()

    @staticmethod
    def _is_all_exports_target(target: ast.expr) -> bool:
        """Return whether an assignment target declares module ``__all__``."""
        return isinstance(target, ast.Name) and target.id == "__all__"

    @staticmethod
    def _literal_string_names(node: ast.AST) -> frozenset[str]:
        """Extract string literals from a tuple/list/set AST node."""
        if not isinstance(node, ast.Tuple | ast.List | ast.Set):
            msg = "export declaration must be a literal tuple/list/set of strings"
            raise TypeError(msg)
        names: set[str] = set()
        for item in node.elts:
            if not isinstance(item, ast.Constant) or not isinstance(item.value, str):
                msg = "export declaration contains a non-string literal"
                raise TypeError(msg)
            names.add(item.value)
        return frozenset(names)


__all__: list[str] = ["FlextInfraCodegenLazyInitPlannerRegistryMixin"]
