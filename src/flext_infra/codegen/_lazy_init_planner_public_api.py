"""Public-API static helpers for the lazy-init planner."""

from __future__ import annotations

import ast
from pathlib import Path

from flext_infra import c, m, t


class FlextInfraCodegenLazyInitPlannerPublicApiMixin:
    @staticmethod
    def _is_public_root_export(
        name: str,
        lazy_map: t.LazyAliasMap,
        *,
        root_pkg: str,
        root_namespace_files: t.StrSequence,
        explicit_public_exports: frozenset[str] = frozenset(),
    ) -> bool:
        """Return whether a root-facade export belongs in the external API."""
        if name in c.Infra.PUBLISHED_ALL_EXCLUDE:
            return False
        module_path = lazy_map[name][0]
        if name in c.Infra.ALIAS_NAMES:
            return True
        if "_fixtures" in module_path.split("."):
            return True
        if name in explicit_public_exports:
            return True
        prefix = f"{root_pkg}."
        if not module_path.startswith(prefix):
            return False
        local_module = module_path.removeprefix(prefix)
        if "." in local_module or local_module.startswith("_"):
            return False
        return f"{local_module}.py" in root_namespace_files

    @staticmethod
    def _root_public_contract_exports(pkg_dir: Path) -> frozenset[str]:
        """Read explicit public root exports from the package ``_exports.py`` file."""
        exports_path = pkg_dir / c.Infra.ROOT_EXPORTS_FILENAME
        if not exports_path.is_file():
            return frozenset()
        source = exports_path.read_text(encoding=c.Cli.ENCODING_DEFAULT)
        tree = ast.parse(source, filename=str(exports_path))
        exports: set[str] = set()
        for statement in tree.body:
            exports.update(
                FlextInfraCodegenLazyInitPlannerPublicApiMixin._public_export_statement_names(
                    statement,
                )
            )
        return frozenset(exports)

    @staticmethod
    def _lazy_import_registry_wrapper(
        pkg_dir: Path,
        current_pkg: str,
    ) -> m.Infra.LazyInitRegistryWrapper | None:
        """Return thin-wrapper registry metadata for test packages."""
        if not (
            current_pkg == c.Infra.DIR_TESTS
            or current_pkg.startswith(f"{c.Infra.DIR_TESTS}.")
        ):
            return None
        exports_path = pkg_dir / c.Infra.ROOT_EXPORTS_FILENAME
        if exports_path.is_file():
            names = frozenset(
                name
                for name in (
                    FlextInfraCodegenLazyInitPlannerPublicApiMixin._all_exports(
                        exports_path
                    )
                )
                if name.endswith("LAZY_IMPORTS")
            )
            if len(names) != 1:
                return None
            registry_name = next(iter(names))
            generated = exports_path.read_text(
                encoding=c.Cli.ENCODING_DEFAULT,
            ).startswith(c.Infra.AUTOGEN_HEADER)
        else:
            registry_name = (
                FlextInfraCodegenLazyInitPlannerPublicApiMixin._registry_name(
                    pkg_dir,
                    current_pkg,
                )
            )
            generated = True
        registry_module = (
            f"{current_pkg}.{c.Infra.ROOT_EXPORTS_FILENAME.removesuffix('.py')}"
        )
        return m.Infra.LazyInitRegistryWrapper.model_validate({
            "module": registry_module,
            "name": registry_name,
            "generated": generated,
        })

    @staticmethod
    def _registry_name(pkg_dir: Path, current_pkg: str) -> str:
        """Return the canonical lazy registry symbol for a test package."""
        segments = tuple(segment for segment in current_pkg.split(".") if segment)
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

    @staticmethod
    def _all_exports(exports_path: Path) -> frozenset[str]:
        """Read literal ``__all__`` names from a Python module."""
        source = exports_path.read_text(encoding=c.Cli.ENCODING_DEFAULT)
        tree = ast.parse(source, filename=str(exports_path))
        exports: set[str] = set()
        for statement in tree.body:
            exports.update(
                FlextInfraCodegenLazyInitPlannerPublicApiMixin._all_export_statement_names(
                    statement
                )
            )
        return frozenset(exports)

    @staticmethod
    def _all_export_statement_names(statement: ast.stmt) -> frozenset[str]:
        """Extract literal names from a module ``__all__`` assignment."""
        match statement:
            case ast.Assign(targets=targets, value=value):
                if any(
                    FlextInfraCodegenLazyInitPlannerPublicApiMixin._is_all_exports_target(
                        target
                    )
                    for target in targets
                ):
                    return FlextInfraCodegenLazyInitPlannerPublicApiMixin._literal_string_names(
                        value
                    )
            case ast.AnnAssign(target=target, value=value):
                if value is not None and (
                    FlextInfraCodegenLazyInitPlannerPublicApiMixin._is_all_exports_target(
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
    def _is_all_exports_target(target: ast.expr) -> bool:
        """Return whether an assignment target declares module ``__all__``."""
        return isinstance(target, ast.Name) and target.id == "__all__"

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

    @staticmethod
    def _literal_string_names(node: ast.AST) -> frozenset[str]:
        """Extract string literals from a tuple/list/set AST node."""
        if not isinstance(node, ast.Tuple | ast.List | ast.Set):
            return frozenset()
        names: set[str] = set()
        for item in node.elts:
            if not isinstance(item, ast.Constant) or not isinstance(item.value, str):
                return frozenset()
            names.add(item.value)
        return frozenset(names)
