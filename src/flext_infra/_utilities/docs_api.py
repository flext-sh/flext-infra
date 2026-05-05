"""Public API extraction helpers for code-driven documentation."""

from __future__ import annotations

from collections.abc import (
    Mapping,
)
from pathlib import Path

from flext_infra import (
    FlextInfraUtilitiesDocsScope,
    FlextInfraUtilitiesRopeAnalysis,
    FlextInfraUtilitiesRopeCore,
    FlextInfraUtilitiesRopeHelpers,
    c,
    m,
    t,
    u,
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
        normalized_items: dict[str, str] = {
            key: str(entry) for key, entry in items.items()
        }
        return normalized_items

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
                return c.Infra.STRING_LITERAL_RE.findall(value)
        return []

    @staticmethod
    def _export_target_map(
        source: str,
        package_name: str,
        exports: t.StrSequence,
    ) -> t.StrMapping:
        """Resolve exported symbols to their defining import modules when possible."""
        return FlextInfraUtilitiesRopeAnalysis.export_target_modules_source(
            source,
            package_name,
            exports,
        )

    @staticmethod
    def _has_module_docstring(source: str) -> bool:
        """Return whether source starts with a module docstring."""
        return FlextInfraUtilitiesRopeAnalysis.module_has_docstring_source(source)

    @staticmethod
    def _assignment_docstrings(source: str) -> set[str]:
        """Return assignment names followed by a literal docstring expression."""
        return set(
            FlextInfraUtilitiesRopeAnalysis.assignment_docstrings_source(source),
        )

    @staticmethod
    def _has_symbol_docstring(source: str, symbol_name: str) -> bool:
        """Return whether one exported class/function starts with a docstring."""
        if FlextInfraUtilitiesRopeAnalysis.symbol_has_docstring_source(
            source,
            symbol_name,
        ):
            return True
        return symbol_name in FlextInfraUtilitiesDocsApi._assignment_docstrings(source)

    @staticmethod
    def _project_keywords(
        project_meta: t.MappingKV[str, t.Infra.InfraValue],
    ) -> t.StrSequence:
        """Return normalized project keywords from ``pyproject.toml`` metadata."""
        return [
            text
            for entry in FlextInfraUtilitiesDocsApi._string_values(
                project_meta.get("keywords", [])
            )
            if (text := entry.strip())
        ]

    @staticmethod
    def _rope_public_symbols(
        project_root: Path,
        target_map: t.StrMapping,
    ) -> t.StrSequence:
        """Use Rope to verify which exported symbols resolve in real modules."""
        with FlextInfraUtilitiesRopeCore.open_project(project_root) as rope_project:
            symbols: t.MutableSequenceOf[str] = []
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
        meta = FlextInfraUtilitiesDocsApi._extract_project_metadata(project_root)
        if not package_name:
            return t.Infra.INFRA_MAPPING_ADAPTER.validate_python({
                "package_name": "",
                "description": meta.description,
                "version": meta.version,
                "site_title": meta.site_title,
                "site_url": meta.site_url,
                "repo_url": meta.repo_url,
                "exports": [],
                "aliases": [],
                "facades": [],
                "public_symbols": [],
                "target_map": {},
                "modules": [],
                "exclude_docs": list(meta.exclude_docs),
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
        aliases, module_exports, symbol_exports = (
            FlextInfraUtilitiesDocsApi._classify_exports(all_exports, target_map)
        )
        modules = FlextInfraUtilitiesDocsApi._resolve_modules(
            package_name=package_name,
            target_map=target_map,
            docs_meta=meta.docs_meta,
        )
        rope_symbols = FlextInfraUtilitiesDocsApi._rope_public_symbols(
            project_root,
            target_map,
        )
        public_symbols = [
            name for name in rope_symbols if name in symbol_exports
        ] or symbol_exports
        metadata = u.read_project_constants("flext-infra")
        facades = [
            name
            for name in public_symbols
            if name.startswith(metadata.TIER_FACADE_PREFIX["src"])
        ]
        return t.Infra.INFRA_MAPPING_ADAPTER.validate_python({
            "package_name": package_name,
            "description": meta.description,
            "keywords": FlextInfraUtilitiesDocsApi._project_keywords(
                meta.project_meta,
            ),
            "version": meta.version,
            "site_title": meta.site_title,
            "site_url": meta.site_url,
            "repo_url": meta.repo_url,
            "exports": all_exports,
            "aliases": aliases,
            "facades": facades,
            "module_exports": module_exports,
            "public_symbols": public_symbols,
            "target_map": dict(target_map),
            "modules": modules,
            "exclude_docs": list(meta.exclude_docs),
        })

    @staticmethod
    def _extract_project_metadata(
        project_root: Path,
    ) -> m.Infra.DocsProjectMeta:
        """Pull pyproject + docs metadata into a strongly-typed view."""
        payload = FlextInfraUtilitiesDocsScope.project_payload(project_root)
        docs_meta = FlextInfraUtilitiesDocsScope.project_docs_meta(project_root)
        exclude_docs = FlextInfraUtilitiesDocsScope.docs_meta_list(
            project_root,
            "exclude_docs",
        )
        project_meta_value = payload.get(c.Infra.PROJECT)
        project_meta: t.Infra.ContainerDict = (
            t.Infra.INFRA_MAPPING_ADAPTER.validate_python(
                project_meta_value if isinstance(project_meta_value, Mapping) else {},
            )
        )
        project_urls_value = project_meta.get("urls")
        project_urls: t.Infra.ContainerDict = (
            t.Infra.INFRA_MAPPING_ADAPTER.validate_python(
                project_urls_value if isinstance(project_urls_value, Mapping) else {},
            )
        )
        site_title = (
            str(docs_meta.get("site_title", "")).strip()
            or str(project_meta.get("name", "")).strip()
        )
        site_url = str(
            project_urls.get("Documentation") or project_urls.get("Homepage") or "",
        ).strip()
        repo_url = str(
            project_urls.get("Repository") or project_urls.get("Homepage") or "",
        ).strip()
        return m.Infra.DocsProjectMeta(
            project_meta=project_meta,
            docs_meta=docs_meta,
            exclude_docs=exclude_docs,
            site_title=site_title,
            site_url=site_url,
            repo_url=repo_url,
            description=str(project_meta.get("description", "")).strip(),
            version=str(project_meta.get(c.Infra.VERSION, "")).strip(),
        )

    @staticmethod
    def _classify_exports(
        all_exports: t.StrSequence,
        target_map: t.StrMapping,
    ) -> tuple[list[str], list[str], list[str]]:
        """Split ``__all__`` entries into ``(aliases, module_exports, symbol_exports)``."""
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
            and not name.startswith("_")
            and name not in module_exports
        ]
        return aliases, module_exports, symbol_exports

    @staticmethod
    def _resolve_modules(
        *,
        package_name: str,
        target_map: t.StrMapping,
        docs_meta: t.MappingKV[str, t.Infra.InfraValue],
    ) -> list[str]:
        """Compute the doc-eligible module list with include/exclude overrides."""
        include_modules = FlextInfraUtilitiesDocsApi._string_values(
            docs_meta.get("module_include"),
        )
        exclude_modules = FlextInfraUtilitiesDocsApi._string_values(
            docs_meta.get("module_exclude"),
        )
        if include_modules:
            modules = sorted({
                item.strip()
                for item in include_modules
                if item.strip().startswith(package_name)
            })
        else:
            modules = sorted({
                module
                for module in target_map.values()
                if module.startswith(package_name)
                and "._" not in module
                and not module.endswith(".__version__")
            })
        if exclude_modules:
            excluded = {item.strip() for item in exclude_modules if item.strip()}
            modules = [module for module in modules if module not in excluded]
        return modules

    @staticmethod
    def docstring_issues(
        project_root: Path,
        contract: t.Infra.ContainerDict,
    ) -> t.SequenceOf[m.Infra.AuditIssue]:
        """Return audit issues for public modules and exports missing docstrings."""
        package_name = str(contract.get("package_name", ""))
        module_list = FlextInfraUtilitiesDocsApi._string_values(
            contract.get("modules", [])
        )
        target_map = FlextInfraUtilitiesDocsApi._string_mapping(
            contract.get("target_map", {})
        )
        issues: t.MutableSequenceOf[m.Infra.AuditIssue] = []
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
