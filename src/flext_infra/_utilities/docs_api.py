"""Public API extraction helpers for code-driven documentation."""

from __future__ import annotations

import re
from collections.abc import Mapping, MutableSequence, Sequence
from pathlib import Path

from flext_infra import c, m, t
from flext_infra._utilities.discovery_scanning import (
    FlextInfraUtilitiesDiscoveryScanning,
)
from flext_infra._utilities.docs_scope import FlextInfraUtilitiesDocsScope
from flext_infra._utilities.rope_core import FlextInfraUtilitiesRopeCore
from flext_infra._utilities.rope_helpers import FlextInfraUtilitiesRopeHelpers


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
    _STRING_RE: re.Pattern[str] = re.compile(r"""["']([a-zA-Z0-9_\.]+)["']""")

    @staticmethod
    def _module_file(project_root: Path, module_name: str) -> Path:
        """Resolve a Python module path to its file path."""
        parts = module_name.split(".")
        base = project_root / c.Infra.Paths.DEFAULT_SRC_DIR / parts[0]
        return (
            base / c.Infra.Files.INIT_PY
            if len(parts) == 1
            else base.joinpath(*parts[1:]).with_suffix(c.Infra.Extensions.PYTHON)
        )

    @classmethod
    def _assignment_strings(cls, source: str, name: str) -> Sequence[str]:
        """Collect literal string values from one module-level assignment."""
        for (
            assignment_name,
            value,
        ) in FlextInfraUtilitiesRopeHelpers.get_module_level_assignments(source):
            if assignment_name == name:
                return cls._STRING_RE.findall(value)
        return []

    @staticmethod
    def _has_module_docstring(source: str) -> bool:
        """Return whether source starts with a module docstring."""
        for line in source.splitlines():
            stripped = line.strip()
            if not stripped:
                continue
            return stripped.startswith(('"""', "'''"))
        return False

    @staticmethod
    def _has_symbol_docstring(source: str, symbol_name: str) -> bool:
        """Return whether one exported class/function starts with a docstring."""
        for kind in ("class", "function"):
            block = FlextInfraUtilitiesRopeHelpers.extract_definition(
                source,
                symbol_name,
                kind=kind,
            )
            if block is None:
                continue
            for line in block.splitlines()[1:]:
                stripped = line.strip()
                if not stripped:
                    continue
                return stripped.startswith(('"""', "'''"))
        return False

    @staticmethod
    def _project_keywords(project_meta: Mapping[str, object]) -> Sequence[str]:
        """Return normalized project keywords from ``pyproject.toml`` metadata."""
        raw = project_meta.get("keywords")
        if not isinstance(raw, list):
            return []
        return [str(item).strip() for item in raw if str(item).strip()]

    @staticmethod
    def _rope_public_symbols(
        project_root: Path,
        target_map: Mapping[str, str],
    ) -> Sequence[str]:
        """Use Rope to verify which exported symbols resolve in real modules."""
        rope_project = FlextInfraUtilitiesRopeCore.init_rope_project(project_root)
        try:
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
                pymodule = FlextInfraUtilitiesRopeCore.get_pycore(
                    rope_project,
                ).resource_to_pyobject(resource)
                if export_name in pymodule.get_attributes():
                    symbols.append(export_name)
            return tuple(dict.fromkeys(symbols))
        finally:
            rope_project.close()

    @staticmethod
    def public_contract(
        project_root: Path,
        package_name: str,
    ) -> Mapping[str, object]:
        """Build the public API contract from pyproject, exports, and Rope validation."""
        payload = FlextInfraUtilitiesDocsScope.pyproject_payload(project_root)
        docs_meta = FlextInfraUtilitiesDocsScope.project_docs_meta(project_root)
        exclude_docs = FlextInfraUtilitiesDocsScope.docs_meta_list(
            project_root,
            "exclude_docs",
        )
        project_meta_value = payload.get(c.Infra.PROJECT)
        project_meta: t.Infra.ContainerDict = (
            project_meta_value if isinstance(project_meta_value, Mapping) else {}
        )
        project_urls_value = project_meta.get("urls")
        project_urls: t.Infra.ContainerDict = (
            project_urls_value if isinstance(project_urls_value, Mapping) else {}
        )
        if not package_name:
            site_title = (
                str(docs_meta.get("site_title", "")).strip()
                or str(project_meta.get("name", "")).strip()
            )
            return {
                "package_name": "",
                "description": str(project_meta.get("description", "")).strip(),
                "version": str(project_meta.get(c.Infra.VERSION, "")).strip(),
                "site_title": site_title,
                "site_url": str(
                    project_urls.get("Documentation")
                    or project_urls.get("Homepage")
                    or ""
                ).strip(),
                "repo_url": str(
                    project_urls.get("Repository") or project_urls.get("Homepage") or ""
                ).strip(),
                "exports": [],
                "aliases": [],
                "facades": [],
                "public_symbols": [],
                "target_map": {},
                "modules": [],
                "exclude_docs": exclude_docs,
            }
        init_path = (
            project_root
            / c.Infra.Paths.DEFAULT_SRC_DIR
            / package_name
            / c.Infra.Files.INIT_PY
        )
        if not init_path.exists():
            return FlextInfraUtilitiesDocsApi.public_contract(project_root, "")
        source = init_path.read_text(encoding=c.Infra.Encoding.DEFAULT)
        all_exports = list(
            FlextInfraUtilitiesDocsApi._assignment_strings(source, "__all__")
        )
        target_map = FlextInfraUtilitiesDiscoveryScanning.extract_lazy_import_targets(
            init_path
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
        include_modules = docs_meta.get("module_include")
        exclude_modules = docs_meta.get("module_exclude")
        if isinstance(include_modules, list):
            modules = sorted({
                str(item).strip()
                for item in include_modules
                if str(item).strip().startswith(package_name)
            })
        if isinstance(exclude_modules, list):
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
        facades = [name for name in public_symbols if name.startswith("Flext")]
        return {
            "package_name": package_name,
            "description": str(project_meta.get("description", "")).strip(),
            "keywords": FlextInfraUtilitiesDocsApi._project_keywords(project_meta),
            "version": str(project_meta.get(c.Infra.VERSION, "")).strip(),
            "site_title": str(docs_meta.get("site_title", "")).strip()
            or str(project_meta.get("name", "")).strip(),
            "site_url": str(
                project_urls.get("Documentation") or project_urls.get("Homepage") or ""
            ).strip(),
            "repo_url": str(
                project_urls.get("Repository") or project_urls.get("Homepage") or ""
            ).strip(),
            "exports": all_exports,
            "aliases": aliases,
            "facades": facades,
            "module_exports": module_exports,
            "public_symbols": public_symbols,
            "target_map": dict(target_map),
            "modules": modules,
            "exclude_docs": exclude_docs,
        }

    @staticmethod
    def docstring_issues(
        project_root: Path,
        contract: Mapping[str, object],
    ) -> Sequence[m.Infra.AuditIssue]:
        """Return audit issues for public modules and exports missing docstrings."""
        package_name = str(contract.get("package_name", ""))
        target_map = contract.get("target_map", {})
        modules = contract.get("modules", [])
        issues: MutableSequence[m.Infra.AuditIssue] = []
        if package_name:
            root_module = FlextInfraUtilitiesDocsApi._module_file(
                project_root, package_name
            )
            if root_module.exists():
                source = root_module.read_text(encoding=c.Infra.Encoding.DEFAULT)
                if not FlextInfraUtilitiesDocsApi._has_module_docstring(source):
                    issues.append(
                        m.Infra.AuditIssue(
                            file=root_module.relative_to(project_root).as_posix(),
                            issue_type="missing_docstring",
                            severity="medium",
                            message="package module is missing a docstring",
                        ),
                    )
        for module_name in modules if isinstance(modules, list) else []:
            module_file = FlextInfraUtilitiesDocsApi._module_file(
                project_root, str(module_name)
            )
            if not module_file.exists():
                continue
            source = module_file.read_text(encoding=c.Infra.Encoding.DEFAULT)
            if not FlextInfraUtilitiesDocsApi._has_module_docstring(source):
                issues.append(
                    m.Infra.AuditIssue(
                        file=module_file.relative_to(project_root).as_posix(),
                        issue_type="missing_docstring",
                        severity="medium",
                        message=f"public module `{module_name}` is missing a docstring",
                    ),
                )
        if not isinstance(target_map, dict):
            return issues
        for export_name, module_name in target_map.items():
            if (
                export_name in FlextInfraUtilitiesDocsApi._ALIAS_EXPORTS
                or export_name.startswith("__")
            ):
                continue
            module_file = FlextInfraUtilitiesDocsApi._module_file(
                project_root, str(module_name)
            )
            if not module_file.exists():
                continue
            source = module_file.read_text(encoding=c.Infra.Encoding.DEFAULT)
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


__all__ = ["FlextInfraUtilitiesDocsApi"]
