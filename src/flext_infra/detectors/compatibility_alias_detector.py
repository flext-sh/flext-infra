"""Detect removable compatibility alias assignments and imports.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from rope.refactor.importutils.importinfo import FromImport

from flext_infra.constants import c
from flext_infra.models import m
from flext_infra.typings import t
from flext_infra.utilities import u


class FlextInfraCompatibilityAliasDetector:
    """Detect compatibility alias assignments and non-canonical facade imports."""

    @classmethod
    def fix_action_for(
        cls,
        violation: m.Infra.CompatibilityAliasViolation,
        *,
        current_project: str,
    ) -> str:
        """Return the catalog fix action for a compatibility-alias violation.

        - ``rewrite_foreign_canonical_alias`` when the current project re-exports
          the alias locally and the violation points back at the project package.
        - ``rewrite_compatibility_alias`` for all other cases.
        """
        if (
            violation.module_name == current_project
            and violation.alias_name == violation.target_name
        ):
            return "rewrite_foreign_canonical_alias"
        return "rewrite_compatibility_alias"

    @staticmethod
    def detect_file(
        ctx: m.Infra.DetectorContext,
    ) -> t.SequenceOf[m.Infra.CompatibilityAliasViolation]:
        """Detect compatibility aliases in a single file.

        Covers:
        - module-level ``CapName = CapName`` compatibility assignments;
        - ``from <pkg> import <LongFacadeClass>`` where a canonical short alias
          exists in ``c.ENFORCEMENT_COMPATIBILITY_ALIAS_RENAMES`` and the long
          name is imported without that canonical short alias.
        """
        resource = u.Infra.fetch_python_resource(ctx.rope_project, ctx.file_path)
        if resource is None:
            return ()
        file_path = ctx.file_path
        source = resource.read()
        lines = source.splitlines()
        violations: list[m.Infra.CompatibilityAliasViolation] = []
        for line_number, line in enumerate(lines, start=1):
            match = c.Infra.COMPAT_ALIAS_RE.match(line)
            if match is None:
                continue
            alias_name, target_name = match.group(1), match.group(2)
            if alias_name in c.Infra.COMPAT_SKIP_NAMES or alias_name == target_name:
                continue
            if alias_name.isupper() and target_name.isupper():
                continue
            violations.append(
                m.Infra.CompatibilityAliasViolation(
                    file=str(file_path),
                    line=line_number,
                    alias_name=alias_name,
                    target_name=target_name,
                )
            )
        if u.Infra.looks_like_facade_file(file_path=file_path, source=source):
            return violations
        alias_renames = c.ENFORCEMENT_COMPATIBILITY_ALIAS_RENAMES
        local_alias_targets = _local_alias_targets(source)
        imported_long_names: set[str] = set()
        canonical_aliases_by_module: dict[str, set[str]] = {}
        current_module = u.Infra.package_name(file_path)
        for from_import in _all_from_imports(ctx.rope_project, resource):
            module_name = _resolve_imported_module(
                current_module=current_module,
                from_import=from_import,
            )
            for name, alias in from_import.names_and_aliases:
                bound_name = alias if alias is not None else name
                if bound_name in alias_renames.values():
                    canonical_aliases_by_module.setdefault(module_name, set()).add(
                        bound_name
                    )
        for from_import in _all_from_imports(ctx.rope_project, resource):
            module_name = _resolve_imported_module(
                current_module=current_module,
                from_import=from_import,
            )
            for name, alias in from_import.names_and_aliases:
                canonical_alias = alias_renames.get(name)
                if canonical_alias is None or alias is not None:
                    continue
                if name in imported_long_names:
                    continue
                if local_alias_targets.get(canonical_alias) == name:
                    # The long name is intentionally imported to seed a local
                    # canonical alias (e.g. ``c = FlextConstants``); not a
                    # compatibility-alias violation.
                    continue
                if canonical_alias in canonical_aliases_by_module.get(
                    module_name, set()
                ):
                    # The canonical short alias is also imported from the same
                    # module; this is a re-export/facade file, not a consumer
                    # compatibility-alias violation.
                    continue
                imported_long_names.add(name)
                line_number = _find_import_line(
                    lines=lines,
                    module_name=module_name,
                    imported_name=name,
                    alias_name=alias,
                )
                violations.append(
                    m.Infra.CompatibilityAliasViolation(
                        file=str(file_path),
                        line=line_number,
                        alias_name=name,
                        target_name=canonical_alias,
                        module_name=module_name,
                    )
                )

        # ENFORCE-080: canonical alias imported from flext_core when the
        # current project re-exports the same slot locally.
        project_alias_owners = c.ENFORCEMENT_PROJECT_ALIAS_OWNERS
        current_package = current_module.split(".")[0]
        local_aliases = project_alias_owners.get(current_package)
        if local_aliases and not u.Infra.looks_like_facade_file(
            file_path=file_path,
            source=source,
        ):
            for from_import in _all_from_imports(ctx.rope_project, resource):
                module_name = _resolve_imported_module(
                    current_module=current_module,
                    from_import=from_import,
                )
                if module_name != c.Infra.PKG_CORE_UNDERSCORE:
                    continue
                for name, alias in from_import.names_and_aliases:
                    bound_name = alias if alias is not None else name
                    if bound_name not in local_aliases:
                        continue
                    line_number = _find_import_line(
                        lines=lines,
                        module_name=module_name,
                        imported_name=name,
                        alias_name=alias,
                    )
                    violations.append(
                        m.Infra.CompatibilityAliasViolation(
                            file=str(file_path),
                            line=line_number,
                            alias_name=bound_name,
                            target_name=bound_name,
                            module_name=current_package,
                        )
                    )
        return violations


def _all_from_imports(
    rope_project: t.Infra.RopeProject,
    resource: t.Infra.RopeResource,
) -> t.SequenceOf[FromImport]:
    """Return all ``from ... import ...`` descriptors in a module (absolute + relative)."""
    module_imports = u.Infra.get_module_imports(rope_project, resource)
    if module_imports is None:
        return ()
    import_statements = u.Infra.import_statements(module_imports)
    return tuple(
        import_stmt.import_info
        for import_stmt in import_statements
        if isinstance(import_stmt.import_info, FromImport)
    )


def _resolve_imported_module(
    *,
    current_module: str,
    from_import: FromImport,
) -> str:
    """Return the absolute module name for a possibly-relative ``FromImport``."""
    module_name = from_import.module_name
    if from_import.level == 0:
        return module_name
    if not current_module:
        return module_name
    current_parts = current_module.split(".")
    if from_import.level > len(current_parts):
        return module_name
    package_parts = current_parts[: -from_import.level]
    if module_name:
        return ".".join(package_parts + [module_name])
    return ".".join(package_parts)


def _find_import_line(
    *,
    lines: t.StrSequence,
    module_name: str,
    imported_name: str,
    alias_name: str | None,
) -> int:
    """Return the 1-based line number of the relevant ``from`` import."""
    for index, line in enumerate(lines, start=1):
        stripped = line.strip()
        if not stripped.startswith("from "):
            continue
        if imported_name in stripped and (alias_name is None or alias_name in stripped):
            return index
    return u.Infra.find_import_line(lines=lines, module_name=module_name) or 1


def _local_alias_targets(source: str) -> t.StrMapping:
    """Collect ``canonical_alias = LongFacadeName`` assignments in source."""
    targets: dict[str, str] = {}
    for match in c.Infra.FACADE_ALIAS_RE.finditer(source):
        alias = match.group(1)
        target = match.group(2)
        targets[alias] = target
    return targets


__all__: list[str] = ["FlextInfraCompatibilityAliasDetector"]
