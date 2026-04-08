"""Canonical codegen namespace utilities shared by census and auto-fix."""

from __future__ import annotations

from collections.abc import MutableMapping, MutableSequence, Sequence
from pathlib import Path

from flext_core import r
from flext_infra import c, m, p, t

from .codegen_constants import FlextInfraUtilitiesCodegenGovernance
from .discovery import FlextInfraUtilitiesDiscovery
from .parsing import FlextInfraUtilitiesParsing
from .rope_analysis import FlextInfraUtilitiesRopeAnalysis
from .rope_source import FlextInfraUtilitiesRopeSource


class FlextInfraUtilitiesCodegenNamespace:
    """Canonical namespace helpers for codegen discovery, parsing, and fixes."""

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
        rope_project = FlextInfraUtilitiesRopeSource.init_rope_project(file_path.parent)
        try:
            resource = FlextInfraUtilitiesRopeSource.get_resource_from_path(
                rope_project,
                file_path,
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
