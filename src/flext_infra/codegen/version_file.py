"""Auto-generate ``__version__.py`` files from the project-metadata SSOT.

Each generated file inherits ``FlextVersion`` from flext-core, with the
project name baked in from ``u.read_project_metadata()`` at generation
time.  No fallback, no hardcoded defaults — ``PackageNotFoundError``
propagates if the package is not installed.

Uses the canonical Jinja2 template ``templates/version_file.py.j2``
and workspace project discovery via ``u.Infra.discover_projects``.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import override

from flext_core import FlextVersion

from flext_infra import FlextInfraCodegenGeneration, FlextInfraServiceBase, c, p, r, u


class FlextInfraCodegenVersionFile(FlextInfraServiceBase[bool]):
    """Generate ``__version__.py`` for every workspace project.

    Projects whose derived version class name equals ``FlextVersion``
    (the base class defined in flext-core) are skipped — that file is
    the SSOT base and is never generated.  Detection is 100% SSOT-derived
    via ``u.derive_class_stem`` + ``c.SPECIAL_NAME_OVERRIDES``.

    Project discovery uses ``u.Infra.discover_projects`` — the canonical
    workspace member list.  No manual directory iteration.
    """

    @override
    def execute(self) -> p.Result[bool]:
        """Generate __version__.py for each discovered project."""
        template = FlextInfraCodegenGeneration.get_template(
            c.Infra.TEMPLATE_VERSION_FILE,
        )
        discovered = u.Infra.discover_projects(self.workspace_root)
        if not discovered.success:
            return r[bool].fail("version-file: project discovery failed")

        generated = 0
        skipped = 0

        for project_info in discovered.value:
            meta = u.read_project_metadata(project_info.path)
            class_name = f"{meta.class_stem}Version"

            if class_name == FlextVersion.__name__:
                skipped += 1
                continue

            if self.project_filter and meta.name != self.project_filter:
                continue

            src_pkg = project_info.path / "src" / meta.package_name
            if not src_pkg.is_dir():
                continue

            target = src_pkg / "__version__.py"
            content = (
                template.render(
                    project_name=meta.name,
                    class_name=class_name,
                ).rstrip()
                + "\n"
            )

            if target.is_file() and target.read_text(encoding="utf-8") == content:
                continue

            if self.check_only or self.dry_run:
                u.Cli.info(f"  stale: {target.relative_to(self.workspace_root)}")
                generated += 1
                continue

            target.write_text(content, encoding="utf-8")
            generated += 1
            u.Cli.info(
                f"  generated: {target.relative_to(self.workspace_root)}",
            )

        verb = "would generate" if (self.check_only or self.dry_run) else "generated"
        u.Cli.info(
            f"version-file: {verb} {generated}, skipped {skipped}",
        )
        return r[bool].ok(True)


__all__: list[str] = ["FlextInfraCodegenVersionFile"]
