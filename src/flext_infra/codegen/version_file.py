"""Auto-generate ``__version__.py`` files from the project-metadata SSOT.

Each generated file inherits ``FlextVersion`` from flext-core, with the
project name baked in from ``u.read_project_metadata()`` at generation
time.  No fallback, no hardcoded defaults — ``PackageNotFoundError``
propagates if the package is not installed.

Uses the canonical Jinja2 template ``templates/version_file.py.j2`` for the
repository explicitly supplied by the consumer.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, override

from flext_core import r
from flext_core.__version__ import FlextVersion
from flext_infra import c, u
from flext_infra.base import s

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraCodegenVersionFile(s[bool]):
    """Generate ``__version__.py`` for the current repository.

    Projects whose derived version class name equals ``FlextVersion``
    (the base class defined in flext-core) are skipped — that file is
    the SSOT base and is never generated.  Detection is 100% SSOT-derived
    via ``u.derive_class_stem`` from installed generated lazy exports.

    No directory iteration or topology-derived dispatch is performed.
    """

    @override
    def execute(self) -> p.Result[bool]:
        """Generate the repository-owned ``__version__.py``."""
        # NOTE (multi-agent, mro-p4s3.2 / agent: uv_overlay_owner): the exact
        # source metadata model crosses the sole CLI rendering boundary.
        template_path = (
            Path(__file__).resolve().parent.parent
            / "templates"
            / c.Infra.TEMPLATE_VERSION_FILE
        )
        metadata_result = u.read_project_metadata(self.workspace_root)
        if metadata_result.failure:
            return r[bool].fail(
                metadata_result.error
                or f"version-file: cannot load {self.workspace_root}"
            )
        meta = metadata_result.value
        if self.project_filter and meta.project.name != self.project_filter:
            return r[bool].fail(f"unknown project: {self.project_filter}")
        if f"{meta.class_stem}Version" == FlextVersion.__name__:
            u.Cli.info("version-file: generated 0, skipped 1")
            return r[bool].ok(True)
        src_pkg = self.workspace_root / "src" / meta.package_name
        if not src_pkg.is_dir():
            u.Cli.info("version-file: generated 0, skipped 0")
            return r[bool].ok(True)
        target = src_pkg / "__version__.py"
        rendered = u.Cli.template_render(template_path, meta)
        if rendered.failure:
            return r[bool].fail(
                rendered.error or f"version-file: cannot render {target}"
            )
        if target.is_file():
            current = u.Cli.files_read_text(target)
            if current.failure:
                return r[bool].fail(
                    current.error or f"version-file: cannot read {target}"
                )
            if current.value == rendered.value:
                u.Cli.info("version-file: generated 0, skipped 0")
                return r[bool].ok(True)
        verb = "would generate" if (self.check_only or self.dry_run) else "generated"
        if self.check_only or self.dry_run:
            u.Cli.info(f"  stale: {target.relative_to(self.workspace_root)}")
        else:
            write_result = u.Cli.atomic_write_text_file(target, rendered.value)
            if write_result.failure:
                return r[bool].fail(
                    write_result.error or f"version-file: cannot write {target}"
                )
            u.Cli.info(f"  generated: {target.relative_to(self.workspace_root)}")
        u.Cli.info(f"version-file: {verb} 1, skipped 0")
        return r[bool].ok(True)


__all__: list[str] = ["FlextInfraCodegenVersionFile"]
