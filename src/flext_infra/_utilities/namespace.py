"""Canonical codegen namespace utilities shared by census and auto-fix."""

from __future__ import annotations

from collections.abc import MutableMapping, MutableSequence, Sequence
from pathlib import Path
from typing import ClassVar

from flext_cli import r, u
from flext_infra import (
    FlextInfraUtilitiesCodegenGovernance,
    FlextInfraUtilitiesDiscovery,
    FlextInfraUtilitiesParsing,
    FlextInfraUtilitiesRopeAnalysis,
    FlextInfraUtilitiesRopeSource,
    c,
    m,
    p,
    t,
)


class FlextInfraUtilitiesCodegenNamespace:
    """Canonical namespace helpers for codegen discovery, parsing, and fixes."""

    _GENINIT_SURFACE_PREFIXES: ClassVar[t.StrMapping] = {
        c.Infra.Directories.TESTS: "Tests",
        c.Infra.Directories.EXAMPLES: "Examples",
        c.Infra.Directories.SCRIPTS: "Scripts",
    }

    _GENINIT_ROOT_NAMESPACE_FILES: tuple[str, ...] = (
        "api.py",
        "base.py",
        "cli.py",
        c.Infra.Files.CONSTANTS_PY,
        "helpers.py",
        c.Infra.Files.MODELS_PY,
        c.Infra.Files.PROTOCOLS_PY,
        "service.py",
        "services.py",
        "settings.py",
        c.Infra.Files.TYPINGS_PY,
        c.Infra.Files.UTILITIES_PY,
    )
    _GENINIT_PUBLIC_FILE_ALIASES: ClassVar[t.StrMapping] = {
        c.Infra.Files.CONSTANTS_PY: "c",
        "helpers.py": "h",
        c.Infra.Files.MODELS_PY: "m",
        c.Infra.Files.PROTOCOLS_PY: "p",
        "service.py": "s",
        c.Infra.Files.TYPINGS_PY: "t",
        c.Infra.Files.UTILITIES_PY: "u",
    }
    _GENINIT_PUBLIC_FILE_SUFFIXES: ClassVar[t.StrMapping] = {
        c.Infra.Files.CONSTANTS_PY: "Constants",
        "helpers.py": "Helpers",
        c.Infra.Files.MODELS_PY: "Models",
        c.Infra.Files.PROTOCOLS_PY: "Protocols",
        c.Infra.Files.TYPINGS_PY: "Types",
        c.Infra.Files.UTILITIES_PY: "Utilities",
    }
    _GENINIT_PRIVATE_FAMILY_TOKENS: ClassVar[dict[str, tuple[str, ...]]] = {
        "c": ("Constants",),
        "m": ("Models",),
        "p": ("Protocols",),
        "t": ("Types", "Typing"),
        "u": ("Utilities",),
    }

    @classmethod
    def is_root_namespace_file(cls, file_name: str) -> bool:
        """Return whether *file_name* is a governed root-namespace facade file."""
        return file_name in cls._GENINIT_ROOT_NAMESPACE_FILES

    @staticmethod
    def discover_project_root(path: Path) -> Path | None:
        """Return the nearest project root containing ``pyproject.toml``."""
        start = path.parent if path.is_file() else path
        for candidate in (start, *start.parents):
            if (candidate / c.Infra.Files.PYPROJECT_FILENAME).is_file():
                return candidate
        return None

    @classmethod
    def derive_project_prefix(cls, path: Path) -> str:
        """Return the canonical project class prefix for *path*."""
        project_root = cls.discover_project_root(path)
        if project_root is None:
            return ""
        prefix = cls._derive_prefix(project_root) or cls.project_class_stem(
            project_name=project_root.name,
        )
        if not prefix:
            return ""
        try:
            rel_parts = path.relative_to(project_root).parts
        except ValueError:
            return prefix
        surface_prefix = cls._surface_prefix(rel_parts)
        return f"{surface_prefix}{prefix}" if surface_prefix else prefix

    @staticmethod
    def _derive_prefix(project_root: Path) -> str:
        """Derive the expected class prefix from the canonical ``src/`` package."""
        src_dir = project_root / c.Infra.Paths.DEFAULT_SRC_DIR
        if not src_dir.is_dir():
            return ""
        for child in sorted(src_dir.iterdir()):
            if child.is_dir() and (child / c.Infra.Files.INIT_PY).exists():
                if child.name == c.Infra.Packages.CORE_UNDERSCORE:
                    return "Flext"
                return "".join(part.title() for part in child.name.split("_"))
        return ""

    @staticmethod
    def _surface_prefix(rel_parts: tuple[str, ...]) -> str:
        """Return the facade surface prefix for top-level tests/examples/scripts."""
        if not rel_parts:
            return ""
        return FlextInfraUtilitiesCodegenNamespace._GENINIT_SURFACE_PREFIXES.get(
            rel_parts[0],
            "",
        )

    @staticmethod
    def project_class_stem(*, project_name: str) -> str:
        """Derive the canonical facade class stem from a project name."""
        normalized = u.norm_str(project_name, case="lower").replace(
            "_",
            "-",
        )
        if normalized == c.Infra.Packages.CORE:
            return "Flext"
        if normalized.startswith(c.Infra.Packages.PREFIX_HYPHEN):
            tail = normalized.removeprefix(c.Infra.Packages.PREFIX_HYPHEN)
            parts = [part for part in tail.split("-") if part]
            return "Flext" + "".join(part.capitalize() for part in parts)
        parts = [part for part in normalized.split("-") if part]
        return "".join(part.capitalize() for part in parts) if parts else ""

    @classmethod
    def geninit_expected_alias(cls, file_path: Path) -> str | None:
        """Return the canonical alias allowed at module level for *file_path*."""
        if file_path.parent.name in c.Infra.FAMILY_DIRECTORIES.values():
            family = cls.geninit_expected_family(file_path)
            if family is None:
                return None
            return next(
                (
                    alias
                    for alias, suffix in c.Infra.FAMILY_SUFFIXES.items()
                    if suffix == family
                ),
                None,
            )
        return cls._GENINIT_PUBLIC_FILE_ALIASES.get(file_path.name)

    @staticmethod
    def geninit_expected_api_singleton_alias(file_path: Path) -> str | None:
        """Return the canonical singleton alias allowed in a root ``api.py``."""
        if file_path.name != "api.py":
            return None
        package_name = FlextInfraUtilitiesDiscovery.discover_package_from_file(
            file_path
        )
        if not package_name or "." in package_name:
            return None
        if package_name.startswith(c.Infra.Packages.PREFIX_UNDERSCORE):
            return package_name.removeprefix(c.Infra.Packages.PREFIX_UNDERSCORE)
        return None

    @classmethod
    def geninit_expected_family(cls, file_path: Path) -> str | None:
        """Return the canonical namespace family suffix for *file_path*."""
        for alias, directory in c.Infra.FAMILY_DIRECTORIES.items():
            if file_path.parent.name == directory:
                return c.Infra.FAMILY_SUFFIXES[alias]
        if file_path.parent.name == "services":
            if file_path.name == "base.py":
                return "ServiceBase"
            return "Mixin"
        if file_path.name == "service.py":
            return "Service"
        if file_path.name == "services.py":
            return "Services"
        return cls._GENINIT_PUBLIC_FILE_SUFFIXES.get(file_path.name)

    @classmethod
    def geninit_expected_family_tokens(cls, file_path: Path) -> tuple[str, ...]:
        """Return accepted family markers for private namespace modules."""
        for alias, directory in c.Infra.FAMILY_DIRECTORIES.items():
            if file_path.parent.name == directory:
                return cls._GENINIT_PRIVATE_FAMILY_TOKENS.get(alias, ())
        family = cls.geninit_expected_family(file_path)
        return (family,) if family else ()

    @classmethod
    def should_enforce_geninit_contract(
        cls,
        rel_path: Path,
        *,
        current_pkg: str = "",
    ) -> bool:
        """Return True when ``gen-init`` must enforce strict namespace shape."""
        if any(part in c.Infra.FAMILY_DIRECTORIES.values() for part in rel_path.parts):
            return True
        if "services" in rel_path.parts:
            return True
        if rel_path.name not in cls._GENINIT_ROOT_NAMESPACE_FILES:
            return False
        package_depth = len([part for part in current_pkg.split(".") if part])
        return package_depth <= 1

    @classmethod
    def discover_codegen_projects(
        cls,
        workspace_root: Path,
        *,
        projects: Sequence[p.Infra.ProjectInfo] | None = None,
    ) -> r[Sequence[p.Infra.ProjectInfo]]:
        """Discover only projects that participate in codegen automation."""
        if projects is None:
            projects_result = FlextInfraUtilitiesDiscovery.discover_projects(
                workspace_root,
            )
            if not projects_result.is_success:
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
            and not (project.path / c.Infra.Files.GO_MOD).exists()
        )
        return r[Sequence[p.Infra.ProjectInfo]].ok(selected)

    @classmethod
    def parse_namespace_validation(
        cls,
        validation: r[m.Infra.ValidationReport],
    ) -> r[tuple[m.Infra.CensusViolation, ...]]:
        """Convert validator output into typed census violations."""
        if validation.is_failure:
            return r[tuple[m.Infra.CensusViolation, ...]].fail(
                validation.error or "namespace validation failed",
            )
        report = validation.unwrap()
        return r[tuple[m.Infra.CensusViolation, ...]].ok(
            cls.parse_census_violations(report.violations),
        )

    @classmethod
    def parse_census_violations(
        cls,
        violations: Sequence[str],
    ) -> tuple[m.Infra.CensusViolation, ...]:
        """Parse raw validator lines into typed violations."""
        return tuple(
            parsed
            for violation in violations
            if (parsed := cls.parse_census_violation(violation)) is not None
        )

    @staticmethod
    def parse_census_violation(
        violation: str,
    ) -> m.Infra.CensusViolation | None:
        """Parse a single namespace violation string into a typed model."""
        match = c.Infra.VIOLATION_PATTERN.match(violation)
        if match is None:
            return None
        rule = match.group("rule")
        module = match.group("module")
        return m.Infra.CensusViolation(
            module=module,
            rule=rule,
            line=int(match.group("line")),
            message=match.group("message"),
            fixable=FlextInfraUtilitiesCodegenGovernance.is_rule_fixable(rule, module),
        )

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
                c.Infra.Files.CONSTANTS_PY,
                "from flext_core import FlextConstants as Constants",
                "Constants",
            ),
            (
                c.Infra.Files.TYPINGS_PY,
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
        rope_project: t.Infra.RopeProject = (
            FlextInfraUtilitiesRopeSource.init_rope_project(file_path.parent)
        )
        try:
            resource: t.Infra.RopeResource | None = (
                FlextInfraUtilitiesRopeSource.get_resource_from_path(
                    rope_project,
                    file_path,
                )
            )
            if resource is None:
                return
            source = FlextInfraUtilitiesRopeSource.read_source(resource)
            updated, class_name = cls._normalize_facade_base_source(
                rope_project=rope_project,
                resource=resource,
                source=source,
                base_import=base_import,
                base_name=base_name,
            )
            if updated == source or not class_name:
                return
            FlextInfraUtilitiesRopeSource.write_source(
                rope_project,
                resource,
                updated,
                description=f"normalize facade base in <{resource.path}>",
            )
        finally:
            rope_project.close()
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
            FlextInfraUtilitiesRopeAnalysis.get_class_info(rope_project, resource),
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
        return module_path.read_text(encoding=c.Infra.Encoding.DEFAULT).splitlines()

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
