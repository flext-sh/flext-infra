"""Canonical codegen namespace utilities shared by census and auto-fix.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import MutableMapping
from pathlib import Path
from typing import ClassVar, Final

from flext_cli import u
from flext_infra import c, config, m, p, r, t
from flext_infra._utilities.discovery import FlextInfraUtilitiesDiscovery
from flext_infra._utilities.docs_scope import FlextInfraUtilitiesDocsScope
from flext_infra._utilities.rope_analysis import FlextInfraUtilitiesRopeAnalysis
from flext_infra._utilities.rope_core import FlextInfraUtilitiesRopeCore
from flext_infra._utilities.rope_source import FlextInfraUtilitiesRopeSource


class FlextInfraUtilitiesCodegenNamespace:
    """Canonical namespace helpers for codegen discovery, parsing, and fixes."""

    _governance_cache: ClassVar[
        MutableMapping[str, p.Infra.ConstantsGovernanceConfig]
    ] = {}
    _governance_file: Final[Path] = (
        Path(__file__).parent.parent / "rules" / "constants-governance.yml"
    )

    @classmethod
    def _is_rule_fixable(cls, rule_id: str, module: str) -> bool:
        """Is rule fixable."""
        cached = cls._governance_cache.get("settings")
        if cached is None:
            raw = u.Cli.yaml_load_mapping(cls._governance_file)
            cached = m.Infra.ConstantsGovernanceConfig.model_validate(raw)
            cls._governance_cache["settings"] = cached
        for rule in cached.rules:
            if rule.id != rule_id:
                continue
            if not rule.fixable:
                return False
            if rule.fixable_exclusion is None:
                return True
            return not module.endswith(rule.fixable_exclusion)
        return False

    @classmethod
    def _lazy_init_config(cls) -> p.Infra.LazyInitConfig:
        """Return the validated lazy-init policy document."""
        return config.Infra.tooling.lazy_init

    @classmethod
    def matches_root_namespace_file(cls, file_name: str) -> bool:
        """Return whether *file_name* is a governed root-namespace facade file."""
        return (
            file_name in cls._lazy_init_config().root_namespace_files
            or cls.runtime_singleton_export(file_name) is not None
        )

    @staticmethod
    def runtime_singleton_export(file_name: str) -> str | None:
        """Return the sole public singleton owned by a sanctioned runtime module."""
        return next(
            (
                Path(module_file).stem.removeprefix("_")
                for module_file, *_ in c.Infra.RUNTIME_MODULES
                if file_name == module_file
            ),
            None,
        )

    @classmethod
    def surface_name(cls, package_name: str) -> str:
        """Return the configured surface name for one import package."""
        parts = tuple(part for part in package_name.split(".") if part)
        if not parts:
            return ""
        settings = cls._lazy_init_config()
        return parts[0] if parts[0] in settings.surface_prefixes else "src"

    @classmethod
    def matches_project_namespace_package(cls, package_name: str) -> bool:
        """Return whether a package behaves like a project namespace root.

        Project package roots under ``src/`` qualify, as do namespace packages under
        governed wrapper surfaces like ``tests/``, ``examples/``, and ``scripts/``.
        Ordinary nested runtime subpackages such as ``<pkg>.services`` do not.
        """
        parts = tuple(part for part in package_name.split(".") if part)
        if not parts:
            return False
        return len(parts) == 1

    @classmethod
    def ordered_namespace_exports(
        cls, *, package_dir: Path, package_name: str, export_names: t.StrSequence
    ) -> t.StrSequence:
        """Order root-package exports with alias hierarchy preserved."""
        ordered_unique = tuple(dict.fromkeys(export_names))
        export_set = set(ordered_unique)
        settings = cls._lazy_init_config()
        local_aliases = tuple(
            alias
            for file_name, alias in settings.public_file_aliases.items()
            if alias in export_set and (package_dir / file_name).is_file()
        )
        inherited_aliases = tuple(
            alias
            for alias in settings.inherited_exports.get(
                cls.surface_name(package_name), ()
            )
            if alias in export_set and alias not in local_aliases
        )
        configured_aliases = tuple(dict.fromkeys((*local_aliases, *inherited_aliases)))
        preferred_aliases = tuple(
            alias for alias in c.Infra.PUBLIC_ROOT_ALIAS_ORDER if alias in export_set
        )
        ordered_aliases = tuple(
            dict.fromkeys((
                *preferred_aliases,
                *(
                    alias
                    for alias in configured_aliases
                    if alias not in preferred_aliases
                ),
            ))
        )
        alias_set = set(ordered_aliases)
        other_exports = tuple(name for name in ordered_unique if name not in alias_set)
        return (*other_exports, *ordered_aliases)

    @staticmethod
    def package_alias(*, package_name: str) -> str:
        """Derive the canonical root API alias from the import package."""
        root = package_name.split(".", maxsplit=1)[0]
        if root.startswith(c.Infra.PKG_PREFIX_UNDERSCORE):
            return root.removeprefix(c.Infra.PKG_PREFIX_UNDERSCORE)
        return root

    @classmethod
    def _runtime_aliases(cls, package_dir: Path) -> t.StrSequence:
        """Return the runtime aliases actually published by one package root."""
        return tuple(
            alias
            for file_name, alias in cls._lazy_init_config().public_file_aliases.items()
            if alias.isidentifier() and (package_dir / file_name).is_file()
        )

    @classmethod
    def layout(
        cls, project_root: Path, *, project: p.Infra.ProjectInfo | None = None
    ) -> p.Infra.RopeProjectLayout | None:
        """Return the canonical project layout contract for one project root."""
        resolved_root = project_root.resolve()
        package_name = (
            project.package_name
            if project is not None and project.package_name
            else FlextInfraUtilitiesDiscovery.package_name(resolved_root)
        )
        if not package_name:
            return None
        project_name = (
            project.name
            if project is not None and project.name
            else FlextInfraUtilitiesDocsScope.project_name_from_payload(
                resolved_root,
                FlextInfraUtilitiesDocsScope.project_payload(resolved_root),
            )
            if (resolved_root / c.PYPROJECT_FILENAME).is_file()
            else resolved_root.name
        )
        class_name_source = (
            project_name
            if project_name != resolved_root.name
            else package_name.split(".", maxsplit=1)[0].replace("_", "-")
        )
        src_dir = resolved_root / c.Infra.DEFAULT_SRC_DIR
        package_dir = src_dir / Path(*package_name.split("."))
        return m.Infra.RopeProjectLayout(
            project_root=resolved_root,
            project_name=project_name,
            package_name=package_name,
            package_alias=cls.package_alias(package_name=package_name),
            class_stem=u.derive_class_stem(class_name_source),
            src_dir=src_dir,
            package_dir=package_dir,
            init_path=package_dir / c.Infra.INIT_PY,
            runtime_aliases=cls._runtime_aliases(package_dir),
        )

    @classmethod
    def _resolve_family(
        cls, file_path: Path, settings: p.Infra.LazyInitConfig
    ) -> tuple[str | None, str | None, str | None, t.StrSequence]:
        """Return (family_alias, expected_family, expected_alias, family_tokens)."""
        family_alias = next(
            (
                alias
                for alias, directory in c.Infra.FAMILY_DIRECTORIES.items()
                if file_path.parent.name == directory
            ),
            None,
        )
        expected_family = (
            c.Infra.FAMILY_SUFFIXES[family_alias]
            if family_alias is not None
            else settings.public_file_suffixes.get(file_path.name)
        )
        expected_alias = (
            family_alias
            if family_alias is not None
            else settings.public_file_aliases.get(file_path.name)
        )
        family_tokens: t.StrSequence = (
            tuple(settings.private_family_tokens.get(family_alias, ()))
            if family_alias is not None
            else (expected_family,)
            if expected_family
            else ()
        )
        return family_alias, expected_family, expected_alias, family_tokens

    @classmethod
    def _resolve_module_flags(
        cls,
        file_path: Path,
        resolved_rel_path: Path,
        package_parts: t.StrSequence,
        family_alias: str | None,
        expected_alias: str | None,
        expected_family: str | None,
        settings: p.Infra.LazyInitConfig,
    ) -> tuple[bool, bool, bool, bool, bool, bool, str | None]:
        """Return all is_* booleans and resolved surface_name.

        Returns: (is_fixture_module, is_family_module, is_family_package,
                  is_services_module, is_root_namespace, is_governed_namespace,
                  resolved expected_alias)
        """
        package_depth = len(package_parts)
        is_fixture_module = file_path.parent.name == "_fixtures"
        family_dir_values = set(c.Infra.FAMILY_DIRECTORIES.values())
        is_family_module = any(
            part in family_dir_values for part in resolved_rel_path.parts
        )
        is_family_package = family_alias is not None or any(
            part in family_dir_values for part in package_parts
        )
        is_services_module = "services" in resolved_rel_path.parts
        runtime_singleton_export = (
            cls.runtime_singleton_export(resolved_rel_path.name)
            if len(resolved_rel_path.parts) == 1 and package_depth <= 1
            else None
        )
        is_namespace_file = (
            resolved_rel_path.name in settings.root_namespace_files
            or runtime_singleton_export is not None
        )
        is_governed_namespace = (
            expected_alias is not None or expected_family is not None
        )
        is_root_namespace = (
            is_namespace_file
            and len(resolved_rel_path.parts) == 1
            and package_depth <= 1
        )
        resolved_alias = expected_alias or runtime_singleton_export
        if (
            resolved_alias is None
            and is_root_namespace
            and resolved_rel_path.name == c.Infra.API_PY
        ):
            resolved_alias = cls.package_alias(
                package_name=".".join(package_parts) if package_parts else ""
            )
        return (
            is_fixture_module,
            is_family_module,
            is_family_package,
            is_services_module,
            is_root_namespace,
            is_governed_namespace,
            resolved_alias,
        )

    @classmethod
    def _resolve_project_prefix(
        cls, file_path: Path, settings: p.Infra.LazyInitConfig
    ) -> str:
        """Derive the class-stem prefix for one file inside a project."""
        project_root = FlextInfraUtilitiesDiscovery.project_root(file_path)
        if project_root is None:
            return ""
        layout = cls.layout(project_root)
        if layout is None:
            return ""
        class_stem: str = layout.class_stem
        try:
            rel_parts = file_path.relative_to(project_root).parts
        except ValueError:
            return class_stem
        surface_prefix = (
            settings.surface_prefixes.get(rel_parts[0], "") if rel_parts else ""
        )
        return f"{surface_prefix}{class_stem}" if surface_prefix else class_stem

    @classmethod
    def policy(
        cls, file_path: Path, *, rel_path: Path | None = None, current_pkg: str = ""
    ) -> p.Infra.NamespaceModulePolicy:
        """Return the derived Pydantic policy for one governed module."""
        settings = cls._lazy_init_config()
        package_name = current_pkg or FlextInfraUtilitiesDiscovery.package_name(
            file_path
        )
        resolved_rel_path = rel_path or Path(file_path.name)
        package_parts = tuple(part for part in package_name.split(".") if part)

        family_alias, expected_family, expected_alias, family_tokens = (
            cls._resolve_family(file_path, settings)
        )
        (
            is_fixture_module,
            is_family_module,
            is_family_package,
            is_services_module,
            is_root_namespace,
            is_governed_namespace,
            expected_alias,
        ) = cls._resolve_module_flags(
            file_path,
            resolved_rel_path,
            package_parts,
            family_alias,
            expected_alias,
            expected_family,
            settings,
        )

        surface_name = package_parts[0] if package_parts else ""
        if surface_name not in settings.surface_prefixes:
            surface_name = "src"
        # mro-wkii.17.26 (codex): pytest's validated collection patterns define
        # implementation modules; their module-local __all__ is not package ABI.
        normalized_test_path = resolved_rel_path.with_name(
            resolved_rel_path.name.removeprefix("_")
        )
        is_pytest_module = any(
            normalized_test_path.match(pattern)
            for pattern in config.Infra.tooling.tools.pytest.python_files
        )

        enforce_contract = (
            is_fixture_module
            or is_family_module
            or is_services_module
            or is_governed_namespace
            or is_root_namespace
        )
        export_symbols = not is_pytest_module
        is_private_module = file_path.stem.startswith("_")
        is_private_package = file_path.parent.name.startswith("_")
        include_in_lazy_init = not is_pytest_module and (
            not file_path.stem[:1].isdigit()
            and (
                not is_private_module
                or is_fixture_module
                or is_family_package
                or is_root_namespace
                # mro-wkii.17.26 (Codex): private packages own their valid direct
                # implementation siblings; numeric module names remain forbidden.
                or is_private_package
            )
        )
        type_checking_imports = tuple(
            name
            for name in dict.fromkeys((
                *settings.public_file_aliases.values(),
                *settings.inherited_exports.get(surface_name, ()),
            ))
            if name.isidentifier()
        )
        return m.Infra.NamespaceModulePolicy(
            enforce_contract=enforce_contract,
            export_symbols=export_symbols,
            include_in_lazy_init=include_in_lazy_init,
            project_prefix=cls._resolve_project_prefix(file_path, settings),
            expected_alias=expected_alias,
            expected_family=expected_family,
            family_tokens=family_tokens,
            accepted_suffixes=((expected_family,) if expected_family else ()),
            allow_main_export=file_path.name in settings.main_export_files,
            allow_type_alias=(
                file_path.name == c.Infra.TYPINGS_PY
                or file_path.parent.name == c.Infra.FAMILY_DIRECTORIES["t"]
            ),
            is_fixture_module=is_fixture_module,
            type_checking_imports=type_checking_imports,
        )

    @classmethod
    def projects(
        cls,
        workspace_root: Path,
        *,
        projects: t.SequenceOf[p.Infra.ProjectInfo] | None = None,
    ) -> p.Result[t.SequenceOf[p.Infra.ProjectInfo]]:
        """Discover only projects that participate in codegen automation."""
        if projects is None:
            projects_result = FlextInfraUtilitiesDocsScope.discover_projects(
                workspace_root
            )
            if not projects_result.success:
                return r[t.SequenceOf[p.Infra.ProjectInfo]].fail(
                    projects_result.error or "project discovery failed"
                )
            discovered = projects_result.unwrap()
        else:
            discovered = projects
        selected = tuple(
            project
            for project in discovered
            if (project.path / c.PYPROJECT_FILENAME).exists()
        )
        return r[t.SequenceOf[p.Infra.ProjectInfo]].ok(selected)

    @classmethod
    def parse_namespace_validation(
        cls, validation: p.Result[p.Infra.ValidationReport]
    ) -> p.Result[tuple[p.Infra.CensusViolation, ...]]:
        """Convert validator output into typed census violations."""
        if validation.failure:
            return r[tuple[p.Infra.CensusViolation, ...]].fail(
                validation.error or "namespace validation failed"
            )
        report = validation.unwrap()
        parsed: list[p.Infra.CensusViolation] = []
        for violation in report.violations:
            match = c.Infra.VIOLATION_PATTERN.match(violation)
            if match is None:
                continue
            rule = match.group("rule")
            module = match.group("module")
            parsed.append(
                m.Infra.CensusViolation(
                    module=module,
                    rule=rule,
                    line=int(match.group("line")),
                    message=match.group("message"),
                    fixable=cls._is_rule_fixable(rule, module),
                )
            )
        return r[tuple[p.Infra.CensusViolation, ...]].ok(tuple(parsed))

    @classmethod
    def normalize_canonical_facades(
        cls, *, pkg_dir: Path, ctx: p.Infra.FixContext
    ) -> None:
        """Normalize canonical facade base classes for codegen auto-fix."""
        for file_name, base_import, base_name in (
            (
                c.Infra.CONSTANTS_PY,
                "from flext_core import FlextConstants as Constants",
                "Constants",
            ),
            (c.Infra.TYPINGS_PY, "from flext_core import FlextTypes as Types", "Types"),
        ):
            cls._normalize_facade_base(
                file_path=pkg_dir / file_name,
                base_import=base_import,
                base_name=base_name,
                ctx=ctx,
            )

    @classmethod
    def _normalize_facade_base(
        cls,
        *,
        file_path: Path,
        base_import: str,
        base_name: str,
        ctx: p.Infra.FixContext,
    ) -> None:
        """Add the canonical flext-core base to a *baseless* facade class only.

        A facade that already declares a base inherits from its proper owning
        project — flext-core directly, or an intermediate such as flext-web
        (``FlextApiConstants(FlextWebConstants)``). Those are left untouched:
        the pass never rebases an already-parented facade onto flext-core, so
        it is idempotent and correct across project boundaries.
        """
        if not file_path.is_file():
            return
        with FlextInfraUtilitiesRopeCore.open_project(file_path.parent) as rope_project:
            resource: t.Infra.RopeResource | None = (
                FlextInfraUtilitiesRopeCore.get_resource_from_path(
                    rope_project, file_path
                )
            )
            if resource is None:
                return
            source = resource.read()
            class_infos = sorted(
                FlextInfraUtilitiesRopeAnalysis.get_class_info(rope_project, resource),
                key=lambda item: item.line,
            )
            if not class_infos:
                return
            class_info = class_infos[0]
            if class_info.bases:
                return
            lines = source.splitlines()
            header_idx = class_info.line - 1
            if not 0 <= header_idx < len(lines):
                return
            rewritten_header = cls._normalize_class_header(
                line=lines[header_idx], class_name=class_info.name, base_name=base_name
            )
            if rewritten_header == lines[header_idx]:
                return
            lines[header_idx] = rewritten_header
            updated = "\n".join(lines)
            if source.endswith("\n"):
                updated += "\n"
            if base_import not in updated:
                updated = cls._insert_import_line(
                    source=updated, import_line=base_import
                )
            if updated == source:
                return
            resource.write(updated)
            ctx.files_modified.add(str(file_path))
            ctx.fix(
                module=str(file_path),
                rule="NAMESPACE",
                line=1,
                message=(f"normalized {class_info.name} to inherit from {base_name}"),
            )

    @staticmethod
    def _normalize_class_header(*, line: str, class_name: str, base_name: str) -> str:
        """Normalize class header."""
        stripped = line.strip()
        prefix = f"class {class_name}"
        if not stripped.startswith(prefix) or not stripped.endswith(":"):
            return line
        indent = line[: len(line) - len(line.lstrip())]
        return f"{indent}class {class_name}({base_name}):"

    @classmethod
    def _insert_import_line(cls, *, source: str, import_line: str) -> str:
        """Insert an import after the module docstring and future imports.

        Uses the docstring-aware position helper so the import can never land
        inside a multi-line module docstring (the cause of the F821/"unexpected
        indent" corruption).


        Returns:
            Source text with the import inserted at the canonical position.
        """
        lines = source.splitlines()
        if import_line in lines:
            return source
        insert_at = (
            FlextInfraUtilitiesRopeSource.index_after_docstring_and_future_imports(
                lines
            )
        )
        before = lines[:insert_at]
        after = lines[insert_at:]
        inserted: t.MutableSequenceOf[str] = list(before)
        if inserted and inserted[-1]:
            inserted.append("")
        inserted.append(import_line)
        if after and after[0]:
            inserted.append("")
        inserted.extend(after)
        return "\n".join(inserted) + ("\n" if source.endswith("\n") else "")

    @classmethod
    def classify_violation_outcomes(
        cls,
        *,
        project_path: Path,
        initial_violations: t.SequenceOf[p.Infra.CensusViolation],
        remaining_violations: t.SequenceOf[p.Infra.CensusViolation],
    ) -> tuple[
        tuple[p.Infra.CensusViolation, ...], tuple[p.Infra.CensusViolation, ...]
    ]:
        """Split initial violations into fixed and still-skipped groups."""
        if not initial_violations:
            return ((), ())
        source_cache: MutableMapping[str, t.StrSequence] = {}
        remaining_keys = frozenset(
            cls._build_violation_key(
                violation=violation,
                project_path=project_path,
                source_cache=source_cache,
            )
            for violation in remaining_violations
        )
        fixed: t.MutableSequenceOf[p.Infra.CensusViolation] = []
        skipped: t.MutableSequenceOf[p.Infra.CensusViolation] = []
        for violation in initial_violations:
            key = cls._build_violation_key(
                violation=violation,
                project_path=project_path,
                source_cache=source_cache,
            )
            if violation.fixable and key not in remaining_keys:
                fixed.append(violation)
                continue
            skipped.append(violation)
        return (tuple(fixed), tuple(skipped))

    @staticmethod
    def _read_source_lines(project_path: Path, module: str) -> t.StrSequence:
        """Read source lines."""
        module_path = project_path / module
        if not module_path.is_file():
            return ()
        return module_path.read_text(encoding=c.Cli.ENCODING_DEFAULT).splitlines()

    @classmethod
    def _build_violation_key(
        cls,
        *,
        violation: p.Infra.CensusViolation,
        project_path: Path,
        source_cache: MutableMapping[str, t.StrSequence],
    ) -> p.Infra.ViolationKey:
        """Build violation key."""
        if violation.module not in source_cache:
            source_cache[violation.module] = cls._read_source_lines(
                project_path, violation.module
            )
        return m.Infra.ViolationKey.from_violation(
            violation, source_cache[violation.module]
        )


__all__: list[str] = ["FlextInfraUtilitiesCodegenNamespace"]
