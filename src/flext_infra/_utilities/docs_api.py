"""Public API extraction helpers for code-driven documentation."""

from __future__ import annotations

import ast
from collections.abc import (
    Mapping,
    MutableSequence,
    Sequence,
)
from pathlib import Path

from flext_infra import (
    FlextInfraUtilitiesDocsScope,
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeHelpers,
    c,
    m,
    t,
)


class FlextInfraUtilitiesDocsApi:
    """Extract public package metadata, exports, modules, and docstring issues."""

    _ALIAS_EXPORTS: tuple[str, ...] = (
        "c",
        "d",
        "e",
        "h",
        "m",
        "p",
        "r",
        "s",
        "t",
        "u",
        "x",
    )
    _STRING_RE: t.Infra.RegexPattern = c.Infra.STRING_LITERAL_RE

    @staticmethod
    def _string_values(value: t.Infra.InfraValue | None) -> t.StrSequence:
        """Normalize one infra sequence payload into strings."""
        try:
            items = t.Infra.INFRA_SEQ_ADAPTER.validate_python(value)
        except c.ValidationError:
            return []
        return [str(item) for item in items]

    @staticmethod
    def _string_mapping(value: t.Infra.InfraValue | None) -> t.StrMapping:
        """Normalize one infra mapping payload into string keys and values."""
        try:
            items = t.Infra.INFRA_MAPPING_ADAPTER.validate_python(value)
        except c.ValidationError:
            return {}
        return {str(key): str(entry) for key, entry in items.items()}

    @staticmethod
    def _module_file(project_root: Path, module_name: str) -> Path:
        """Resolve a Python module path to its file path."""
        parts = module_name.split(".")
        src_dir: str = c.Infra.DEFAULT_SRC_DIR
        init_py: str = c.Infra.INIT_PY
        ext_python: str = c.Infra.EXT_PYTHON
        base = project_root / src_dir / parts[0]
        return (
            base / init_py
            if len(parts) == 1
            else base.joinpath(*parts[1:]).with_suffix(ext_python)
        )

    @classmethod
    def _assignment_strings(cls, source: str, name: str) -> t.StrSequence:
        """Collect literal string values from one module-level assignment."""
        for (
            assignment_name,
            value,
        ) in FlextInfraUtilitiesRopeHelpers.get_module_level_assignments(source):
            if assignment_name == name:
                return cls._STRING_RE.findall(value)
        return []

    @staticmethod
    def _export_target_map(
        source: str,
        package_name: str,
        exports: t.StrSequence,
    ) -> t.StrMapping:
        """Resolve exported symbols to their defining import modules when possible."""
        export_names = {name for name in exports if name}
        target_map: dict[str, str] = dict.fromkeys(export_names, package_name)
        try:
            tree = ast.parse(source)
        except SyntaxError:
            return target_map
        for node in ast.walk(tree):
            if not isinstance(node, ast.ImportFrom) or not node.module:
                continue
            if node.names[0].name == "*":
                continue
            module_name = node.module
            if node.level:
                module_name = f"{package_name}.{module_name}"
            for alias in node.names:
                export_name = alias.asname or alias.name
                if export_name in export_names:
                    target_map[export_name] = module_name
        return target_map

    @staticmethod
    def _has_module_docstring(source: str) -> bool:
        """Return whether source starts with a module docstring."""
        try:
            return ast.get_docstring(ast.parse(source)) is not None
        except SyntaxError:
            return False

    @staticmethod
    def _assignment_docstrings(source: str) -> set[str]:
        """Return assignment names followed by a literal docstring expression."""
        try:
            module = ast.parse(source)
        except SyntaxError:
            return set()
        documented: set[str] = set()
        body = module.body
        for index, node in enumerate(body[:-1]):
            next_node = body[index + 1]
            if not (
                isinstance(next_node, ast.Expr)
                and isinstance(next_node.value, ast.Constant)
                and isinstance(next_node.value.value, str)
            ):
                continue
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        documented.add(target.id)
                continue
            if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                documented.add(node.target.id)
                continue
            if isinstance(node, ast.TypeAlias):
                documented.add(node.name.id)
        return documented

    @staticmethod
    def _has_symbol_docstring(source: str, symbol_name: str) -> bool:
        """Return whether one exported class/function starts with a docstring."""
        try:
            module = ast.parse(source)
        except SyntaxError:
            return False
        for node in module.body:
            if (
                isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == symbol_name
            ):
                return ast.get_docstring(node) is not None
        return symbol_name in FlextInfraUtilitiesDocsApi._assignment_docstrings(source)

    @staticmethod
    def _project_keywords(
        project_meta: Mapping[str, t.Infra.InfraValue],
    ) -> t.StrSequence:
        """Return normalized project keywords from ``pyproject.toml`` metadata."""
        return [
            text
            for entry in FlextInfraUtilitiesDocsApi._string_values(
                project_meta.get("keywords", [])
            )
            if (text := str(entry).strip())
        ]

    @staticmethod
    def _rope_public_symbols(
        project_root: Path,
        target_map: t.StrMapping,
    ) -> t.StrSequence:
        """Use Rope to verify which exported symbols resolve in real modules."""
        with FlextInfraUtilitiesRopeCore.open_project(project_root) as rope_project:
            symbols: MutableSequence[str] = []
            for export_name, module_name in target_map.items():
                module_file = FlextInfraUtilitiesDocsApi._module_file(
                    project_root, module_name
                )
                if not module_file.exists():
                    continue
                resource = FlextInfraUtilitiesRopeCore.get_resource_from_path(
                    rope_project,
                    module_file,
                )
                if resource is None:
                    continue
                pymodule = FlextInfraUtilitiesRopeCore.get_pymodule(
                    rope_project,
                    resource,
                )
                if export_name in pymodule.get_attributes():
                    symbols.append(export_name)
            return tuple(dict.fromkeys(symbols))

    @staticmethod
    def public_contract(
        project_root: Path,
        package_name: str,
    ) -> t.Infra.ContainerDict:
        """Build the public API contract from pyproject, exports, and Rope validation."""
        payload = FlextInfraUtilitiesDocsScope.project_payload(project_root)
        docs_meta = FlextInfraUtilitiesDocsScope.project_docs_meta(project_root)
        exclude_docs = FlextInfraUtilitiesDocsScope.docs_meta_list(
            project_root,
            "exclude_docs",
        )
        project_meta_value = payload.get(c.Infra.PROJECT)
        project_meta: t.Infra.ContainerDict = (
            t.Infra.INFRA_MAPPING_ADAPTER.validate_python(
                project_meta_value if isinstance(project_meta_value, Mapping) else {}
            )
        )
        project_urls_value = project_meta.get("urls")
        project_urls: t.Infra.ContainerDict = (
            t.Infra.INFRA_MAPPING_ADAPTER.validate_python(
                project_urls_value if isinstance(project_urls_value, Mapping) else {}
            )
        )
        site_title = (
            str(docs_meta.get("site_title", "")).strip()
            or str(project_meta.get("name", "")).strip()
        )
        site_url = str(
            project_urls.get("Documentation") or project_urls.get("Homepage") or ""
        ).strip()
        repo_url = str(
            project_urls.get("Repository") or project_urls.get("Homepage") or ""
        ).strip()
        description = str(project_meta.get("description", "")).strip()
        version = str(project_meta.get(c.Infra.VERSION, "")).strip()
        if not package_name:
            return t.Infra.INFRA_MAPPING_ADAPTER.validate_python({
                "package_name": "",
                "description": description,
                "version": version,
                "site_title": site_title,
                "site_url": site_url,
                "repo_url": repo_url,
                "exports": [],
                "aliases": [],
                "facades": [],
                "public_symbols": [],
                "target_map": {},
                "modules": [],
                "exclude_docs": list(exclude_docs),
            })
        init_path = (
            project_root / c.Infra.DEFAULT_SRC_DIR / package_name / c.Infra.INIT_PY
        )
        if not init_path.exists():
            return FlextInfraUtilitiesDocsApi.public_contract(project_root, "")
        source = init_path.read_text(encoding=c.Cli.ENCODING_DEFAULT)
        all_exports = list(
            FlextInfraUtilitiesDocsApi._assignment_strings(source, "__all__")
        )
        target_map = FlextInfraUtilitiesDocsApi._export_target_map(
            source,
            package_name,
            all_exports,
        )
        modules = sorted(
            {
                module
                for module in target_map.values()
                if module.startswith(package_name)
                and "._" not in module
                and not module.endswith(".__version__")
            },
        )
        aliases = [
            name
            for name in all_exports
            if name in FlextInfraUtilitiesDocsApi._ALIAS_EXPORTS
        ]
        module_exports = [
            name
            for name in all_exports
            if not name.startswith("_")
            and name not in FlextInfraUtilitiesDocsApi._ALIAS_EXPORTS
            and target_map.get(name, "").split(".")[-1] == name
            and name[:1].islower()
        ]
        symbol_exports = [
            name
            for name in all_exports
            if name not in FlextInfraUtilitiesDocsApi._ALIAS_EXPORTS
            and not name.startswith("__")
            and not name.startswith("_")
            and name not in module_exports
        ]
        include_modules = FlextInfraUtilitiesDocsApi._string_values(
            docs_meta.get("module_include")
        )
        exclude_modules = FlextInfraUtilitiesDocsApi._string_values(
            docs_meta.get("module_exclude")
        )
        if include_modules:
            modules = sorted({
                str(item).strip()
                for item in include_modules
                if str(item).strip().startswith(package_name)
            })
        if exclude_modules:
            excluded = {
                str(item).strip() for item in exclude_modules if str(item).strip()
            }
            modules = [module for module in modules if module not in excluded]
        public_symbols = [
            name
            for name in FlextInfraUtilitiesDocsApi._rope_public_symbols(
                project_root, target_map
            )
            if name in symbol_exports
        ]
        if not public_symbols:
            public_symbols = symbol_exports
        facades = [
            name
            for name in public_symbols
            if name.startswith(c.TIER_FACADE_PREFIX["src"])
        ]
        return t.Infra.INFRA_MAPPING_ADAPTER.validate_python({
            "package_name": package_name,
            "description": description,
            "keywords": FlextInfraUtilitiesDocsApi._project_keywords(project_meta),
            "version": version,
            "site_title": site_title,
            "site_url": site_url,
            "repo_url": repo_url,
            "exports": all_exports,
            "aliases": aliases,
            "facades": facades,
            "module_exports": module_exports,
            "public_symbols": public_symbols,
            "target_map": dict(target_map),
            "modules": modules,
            "exclude_docs": list(exclude_docs),
        })

    @staticmethod
    def docstring_issues(
        project_root: Path,
        contract: t.Infra.ContainerDict,
    ) -> Sequence[m.Infra.AuditIssue]:
        """Return audit issues for public modules and exports missing docstrings."""
        package_name = str(contract.get("package_name", ""))
        module_list = FlextInfraUtilitiesDocsApi._string_values(
            contract.get("modules", [])
        )
        target_map = FlextInfraUtilitiesDocsApi._string_mapping(
            contract.get("target_map", {})
        )
        issues: MutableSequence[m.Infra.AuditIssue] = []
        module_docstring_checks = [
            (module_name, f"public module `{module_name}` is missing a docstring")
            for module_name in module_list
        ]
        if package_name:
            module_docstring_checks.insert(
                0,
                (package_name, "package module is missing a docstring"),
            )
        for module_name, message in module_docstring_checks:
            module_file = FlextInfraUtilitiesDocsApi._module_file(
                project_root, module_name
            )
            if not module_file.exists():
                continue
            source = module_file.read_text(encoding=c.Cli.ENCODING_DEFAULT)
            if FlextInfraUtilitiesDocsApi._has_module_docstring(source):
                continue
            issues.append(
                m.Infra.AuditIssue(
                    file=module_file.relative_to(project_root).as_posix(),
                    issue_type="missing_docstring",
                    severity="medium",
                    message=message,
                ),
            )
        export_docstring_checks = [
            (export_name, module_name)
            for export_name, module_name in target_map.items()
            if export_name not in FlextInfraUtilitiesDocsApi._ALIAS_EXPORTS
            and not export_name.startswith("__")
        ]
        for export_name, module_name in export_docstring_checks:
            module_file = FlextInfraUtilitiesDocsApi._module_file(
                project_root, module_name
            )
            if not module_file.exists():
                continue
            source = module_file.read_text(encoding=c.Cli.ENCODING_DEFAULT)
            if FlextInfraUtilitiesDocsApi._has_symbol_docstring(source, export_name):
                continue
            issues.append(
                m.Infra.AuditIssue(
                    file=module_file.relative_to(project_root).as_posix(),
                    issue_type="missing_docstring",
                    severity="medium",
                    message=f"exported symbol `{export_name}` is missing a docstring",
                ),
            )
        return issues


__all__: list[str] = ["FlextInfraUtilitiesDocsApi"]
