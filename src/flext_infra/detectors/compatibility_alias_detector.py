"""Detect removable compatibility alias assignments and imports.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from flext_infra import c, m, t, u


class FlextInfraCompatibilityAliasDetector:
    """Detect compatibility alias assignments and non-canonical facade imports."""

    @staticmethod
    def detect_file(
        ctx: m.Infra.DetectorContext,
    ) -> t.SequenceOf[m.Infra.CompatibilityAliasViolation]:
        """Detect compatibility aliases in a single file.

        Covers two kinds:
        - module-level ``CapName = CapName`` compatibility assignments;
        - ``from <pkg> import <LongFacadeClass>`` where a canonical short alias
          exists in ``c.ENFORCEMENT_COMPATIBILITY_ALIAS_RENAMES``.
        """
        resource = u.Infra.fetch_python_resource(ctx.rope_project, ctx.file_path)
        if resource is None:
            return []
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
        imported_long_names: set[str] = set()
        for from_import in u.Infra.get_absolute_from_imports(
            ctx.rope_project,
            resource,
        ):
            module_name = from_import.module_name
            for name, alias in from_import.names_and_aliases:
                canonical_alias = alias_renames.get(name)
                if canonical_alias is None or alias is not None:
                    continue
                if name in imported_long_names:
                    continue
                imported_long_names.add(name)
                line_number = u.Infra.find_import_line(
                    lines=lines,
                    module_name=module_name,
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
        return violations


__all__: list[str] = ["FlextInfraCompatibilityAliasDetector"]
