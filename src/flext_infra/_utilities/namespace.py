"""Canonical codegen namespace utilities shared by census and auto-fix."""

from __future__ import annotations

from collections.abc import MutableMapping, MutableSequence, Sequence
from pathlib import Path
from typing import ClassVar, Final

from flext_cli import u
from flext_infra import (
    FlextInfraUtilitiesDiscovery,
    FlextInfraUtilitiesDocsScope,
    FlextInfraUtilitiesParsing,
    FlextInfraUtilitiesRope,
    c,
    m,
    p,
    r,
    t,
)
from flext_infra._utilities.base import FlextInfraUtilitiesBase


class FlextInfraUtilitiesCodegenNamespace:
    """Canonical namespace helpers for codegen discovery, parsing, and fixes."""

    _governance_cache: ClassVar[
        MutableMapping[str, m.Infra.ConstantsGovernanceConfig]
    ] = {}
    _governance_file: Final[Path] = (
        Path(__file__).parent.parent / "rules" / "constants-governance.yml"
    )

    @classmethod
    def _is_rule_fixable(cls, rule_id: str, module: str) -> bool:
        cached = cls._governance_cache.get("config")
        if cached is None:
            raw = u.Cli.yaml_load_mapping(cls._governance_file)
            cached = m.Infra.ConstantsGovernanceConfig.model_validate(raw)
            cls._governance_cache["config"] = cached
        for rule in cached.rules:
            if rule.id != rule_id:
                continue
            if not rule.fixable:
                return False
            if rule.fixable_exclusion is None:
                return True
            return not module.endswith(rule.fixable_exclusion)
        return False

    @staticmethod
    def _lazy_init_config() -> m.Infra.LazyInitConfig:
        """Return the validated lazy-init policy document."""
        config = FlextInfraUtilitiesBase.load_tool_config()
        if config.failure:
            msg = config.error or "lazy-init configuration is unavailable"
            raise RuntimeError(msg)
        return config.unwrap().lazy_init

    @classmethod
    def is_root_namespace_file(cls, file_name: str) -> bool:
        """Return whether *file_name* is a governed root-namespace facade file."""
        return file_name in cls._lazy_init_config().root_namespace_files

    @staticmethod
    def project_class_stem(*, project_name: str) -> str:
        """Derive the canonical facade class stem from a project name."""
        normalized = u.norm_str(project_name, case="lower").replace(
            "_",
            "-",
        )
        if normalized == c.Infra.PKG_CORE:
            return "Flext"
        if normalized.startswith(c.Infra.PKG_PREFIX_HYPHEN):
            tail = normalized.removeprefix(c.Infra.PKG_PREFIX_HYPHEN)
            parts = [part for part in tail.split("-") if part]
            return "Flext" + "".join(part.capitalize() for part in parts)
        parts = [part for part in normalized.split("-") if part]
        return "".join(part.capitalize() for part in parts) if parts else ""

    @staticmethod
    def package_alias(*, package_name: str) -> str:
        """Derive the canonical root API alias from the import package."""
        root = package_name.split(".", maxsplit=1)[0]
        if root.startswith(c.Infra.PKG_PREFIX_UNDERSCORE):
            return root.removeprefix(c.Infra.PKG_PREFIX_UNDERSCORE)
        return root

    @classmethod
    def module_policy(
        cls,
        file_path: Path,
        *,
        rel_path: Path | None = None,
        current_pkg: str = "",
    ) -> m.Infra.NamespaceModulePolicy:
        """Return the derived Pydantic policy for one governed module."""
        config = cls._lazy_init_config()
        package_name = (
            current_pkg
            or FlextInfraUtilitiesDiscovery.discover_package_from_file(
                file_path,
            )
        )
        resolved_rel_path = rel_path or Path(file_path.name)
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
            else config.public_file_suffixes.get(file_path.name)
        )
        expected_alias = (
            family_alias
            if family_alias is not None
            else config.public_file_aliases.get(file_path.name)
        )
        family_tokens = (
            tuple(config.private_family_tokens.get(family_alias, ()))
            if family_alias is not None
            else (expected_family,)
            if expected_family
            else ()
        )
        package_parts = tuple(part for part in package_name.split(".") if part)
        package_depth = len(package_parts)
        is_fixture_module = file_path.parent.name == "_fixtures"
        is_family_module = any(
            part in c.Infra.FAMILY_DIRECTORIES.values()
            for part in resolved_rel_path.parts
        )
        is_family_package = family_alias is not None or any(
            part in c.Infra.FAMILY_DIRECTORIES.values() for part in package_parts
        )
        is_services_module = "services" in resolved_rel_path.parts
        is_services_package = "services" in package_parts
        is_namespace_file = resolved_rel_path.name in config.root_namespace_files
        is_governed_namespace = (
            expected_alias is not None or expected_family is not None
        )
        is_root_namespace = (
            is_namespace_file
            and len(resolved_rel_path.parts) == 1
            and package_depth <= 1
        )
        if (
            expected_alias is None
            and is_root_namespace
            and resolved_rel_path.name == c.Infra.API_PY
        ):
            expected_alias = cls.package_alias(package_name=package_name)
        surface_name = package_parts[0] if package_parts else ""
        if surface_name not in config.surface_prefixes:
            surface_name = "src"
        is_src_surface = surface_name == "src"
        enforce_contract = (
            is_fixture_module
            or is_family_module
            or is_services_module
            or is_governed_namespace
            or is_root_namespace
        )
        export_symbols = (
            is_src_surface
            or is_fixture_module
            or is_family_module
            or is_family_package
            or is_services_module
            or is_services_package
            or is_namespace_file
            or is_root_namespace
        )
        is_private_module = file_path.stem.startswith("_")
        include_in_lazy_init = not file_path.stem[:1].isdigit() and (
            not is_private_module or is_fixture_module or is_family_package
        )
        type_checking_imports = tuple(
            name
            for name in dict.fromkeys((
                *config.public_file_aliases.values(),
                *config.inherited_exports.get(surface_name, ()),
            ))
            if name.isidentifier()
        )
        project_root = FlextInfraUtilitiesDiscovery.discover_project_root_from_file(
            file_path,
        )
        project_prefix = ""
        if project_root is not None:
            prefix = cls.project_class_stem(
                project_name=(
                    FlextInfraUtilitiesDocsScope.package_name(project_root)
                    or project_root.name
                ),
            )
            if prefix:
                try:
                    rel_parts = file_path.relative_to(project_root).parts
                except ValueError:
                    project_prefix = prefix
                else:
                    surface_prefix = (
                        config.surface_prefixes.get(rel_parts[0], "")
                        if rel_parts
                        else ""
                    )
                    project_prefix = (
                        f"{surface_prefix}{prefix}" if surface_prefix else prefix
                    )
        return m.Infra.NamespaceModulePolicy(
            enforce_contract=enforce_contract,
            export_symbols=export_symbols,
            include_in_lazy_init=include_in_lazy_init,
            project_prefix=project_prefix,
            expected_alias=expected_alias,
            expected_family=expected_family,
            family_tokens=family_tokens,
            accepted_suffixes=((expected_family,) if expected_family else ()),
            allow_main_export=file_path.name in config.main_export_files,
            allow_type_alias=(
                file_path.name == c.Infra.TYPINGS_PY
                or file_path.parent.name == "_typings"
            ),
            is_fixture_module=is_fixture_module,
            type_checking_imports=type_checking_imports,
        )

    @classmethod
    def discover_codegen_projects(
        cls,
        workspace_root: Path,
        *,
        projects: Sequence[p.Infra.ProjectInfo] | None = None,
    ) -> r[Sequence[p.Infra.ProjectInfo]]:
        """Discover only projects that participate in codegen automation."""
        if projects is None:
            projects_result = FlextInfraUtilitiesDocsScope.discover_projects(
                workspace_root,
            )
            if not projects_result.success:
                return r[Sequence[p.Infra.ProjectInfo]].fail(
                    projects_result.error or "project discovery failed",
                )
            discovered = projects_result.unwrap()
        else:
            discovered = projects
        selected = tuple(
            project
            for project in discovered
            if project.name not in c.Infra.EXCLUDED_PROJECTS
            and not (project.path / c.Infra.GO_MOD).exists()
        )
        return r[Sequence[p.Infra.ProjectInfo]].ok(selected)

    @classmethod
    def parse_namespace_validation(
        cls,
        validation: r[m.Infra.ValidationReport],
    ) -> r[tuple[m.Infra.CensusViolation, ...]]:
        """Convert validator output into typed census violations."""
        if validation.failure:
            return r[tuple[m.Infra.CensusViolation, ...]].fail(
                validation.error or "namespace validation failed",
            )
        report = validation.unwrap()
        parsed: list[m.Infra.CensusViolation] = []
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
                    fixable=cls._is_rule_fixable(
                        rule,
                        module,
                    ),
                )
            )
        return r[tuple[m.Infra.CensusViolation, ...]].ok(tuple(parsed))

    @classmethod
    def normalize_canonical_facades(
        cls,
        *,
        pkg_dir: Path,
        ctx: m.Infra.FixContext,
    ) -> None:
        """Normalize canonical facade base classes for codegen auto-fix."""
        for file_name, base_import, base_name in (
            (
                c.Infra.CONSTANTS_PY,
                "from flext_core import FlextConstants as Constants",
                "Constants",
            ),
            (
                c.Infra.TYPINGS_PY,
                "from flext_core import FlextTypes as Types",
                "Types",
            ),
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
        ctx: m.Infra.FixContext,
    ) -> None:
        if not file_path.is_file():
            return
        with FlextInfraUtilitiesRope.open_project(file_path.parent) as rope_project:
            resource: t.Infra.RopeResource | None = (
                FlextInfraUtilitiesRope.get_resource_from_path(
                    rope_project,
                    file_path,
                )
            )
            if resource is None:
                return
            source = resource.read()
            updated, class_name = cls._normalize_facade_base_source(
                rope_project=rope_project,
                resource=resource,
                source=source,
                base_import=base_import,
                base_name=base_name,
            )
            if updated == source or not class_name:
                return
            resource.write(updated)
        ctx.files_modified.add(str(file_path))
        ctx.fix(
            module=str(file_path),
            rule="NAMESPACE",
            line=1,
            message=f"normalized {class_name} to inherit from {base_name}",
        )

    @classmethod
    def _normalize_facade_base_source(
        cls,
        *,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        source: str,
        base_import: str,
        base_name: str,
    ) -> tuple[str, str]:
        class_infos = sorted(
            FlextInfraUtilitiesRope.get_class_info(rope_project, resource),
            key=lambda item: item.line,
        )
        if not class_infos:
            return source, ""
        class_name = class_infos[0].name
        lines = source.splitlines()
        header_idx = class_infos[0].line - 1
        if header_idx < 0 or header_idx >= len(lines):
            return source, ""
        rewritten_header = cls._normalize_class_header(
            line=lines[header_idx],
            class_name=class_name,
            base_name=base_name,
        )
        if rewritten_header == lines[header_idx] and base_import in source:
            return source, class_name
        lines[header_idx] = rewritten_header
        updated = "\n".join(lines)
        if source.endswith("\n"):
            updated += "\n"
        if base_import not in updated:
            updated = cls._insert_import_line(source=updated, import_line=base_import)
        return updated, class_name

    @staticmethod
    def _normalize_class_header(*, line: str, class_name: str, base_name: str) -> str:
        stripped = line.strip()
        prefix = f"class {class_name}"
        if not stripped.startswith(prefix) or not stripped.endswith(":"):
            return line
        indent = line[: len(line) - len(line.lstrip())]
        return f"{indent}class {class_name}({base_name}):"

    @classmethod
    def _insert_import_line(cls, *, source: str, import_line: str) -> str:
        lines = source.splitlines()
        if import_line in lines:
            return source
        insert_at = FlextInfraUtilitiesParsing.find_import_insert_position(
            lines,
            past_existing=False,
        )
        before = lines[:insert_at]
        after = lines[insert_at:]
        inserted: MutableSequence[str] = list(before)
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
        initial_violations: Sequence[m.Infra.CensusViolation],
        remaining_violations: Sequence[m.Infra.CensusViolation],
    ) -> tuple[
        tuple[m.Infra.CensusViolation, ...],
        tuple[m.Infra.CensusViolation, ...],
    ]:
        """Split initial violations into fixed and still-skipped groups."""
        if not initial_violations:
            return ((), ())
        source_cache: MutableMapping[str, Sequence[str]] = {}
        remaining_keys = frozenset(
            cls._build_violation_key(
                violation=violation,
                project_path=project_path,
                source_cache=source_cache,
            )
            for violation in remaining_violations
        )
        fixed: MutableSequence[m.Infra.CensusViolation] = []
        skipped: MutableSequence[m.Infra.CensusViolation] = []
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
    def _read_source_lines(project_path: Path, module: str) -> Sequence[str]:
        module_path = project_path / module
        if not module_path.is_file():
            return ()
        return module_path.read_text(encoding=c.Infra.ENCODING_DEFAULT).splitlines()

    @classmethod
    def _build_violation_key(
        cls,
        *,
        violation: m.Infra.CensusViolation,
        project_path: Path,
        source_cache: MutableMapping[str, Sequence[str]],
    ) -> m.Infra.ViolationKey:
        if violation.module not in source_cache:
            source_cache[violation.module] = cls._read_source_lines(
                project_path,
                violation.module,
            )
        return m.Infra.ViolationKey.from_violation(
            violation,
            source_cache[violation.module],
        )


__all__ = ["FlextInfraUtilitiesCodegenNamespace"]
