"""Usage census orchestrator logic.

Delegates core file crawling to `u.Infra` and applies rope-oriented discovery.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import time
from collections.abc import MutableSequence
from pathlib import Path

from flext_core import r
from flext_infra import (
    FlextInfraCensusImportDiscoveryVisitor,
    FlextInfraCensusUsageCollector,
    c,
    m,
    u,
)


class FlextInfraRefactorCensus:
    """Census execution engine resolving family usage patterns."""

    @staticmethod
    def render_text(report: m.Infra.UtilitiesCensusReport) -> str:
        """Render the census report cleanly."""
        return u.Infra.render_census_report(report)

    def run(
        self,
        workspace_root: Path,
        *,
        target: m.Infra.MROFamilyTarget | None = None,
    ) -> r[m.Infra.UtilitiesCensusReport]:
        """Execute the workspace census."""
        target = target or u.Infra.build_mro_target(
            c.Infra.CENSUS_DEFAULT_FAMILY,
        )
        t0 = time.monotonic()
        u.Infra.header(f"Usage Census — family={target.family} ({target.class_suffix})")

        pkg = (
            workspace_root
            / target.core_project
            / c.Infra.DEFAULT_SRC_DIR
            / target.package_dir
        )
        facade = (
            workspace_root
            / target.core_project
            / c.Infra.DEFAULT_SRC_DIR
            / target.facade_module
        )

        # 1-3. Metadata & Discovery
        u.Infra.progress(1, 5, "Metadata gathering", "metadata")
        parsed = (
            u.Infra.extract_public_methods_from_dir(pkg)
            if pkg.is_dir()
            else u.Infra.extract_public_methods_from_file(pkg)
        )
        methods = {
            cls: [
                m.Infra.CensusMethodInfo(name=n, method_type=t, source_file=s)
                for n, t, s in lst
            ]
            for cls, lst in parsed.items()
        }
        index = {cls: {mi.name for mi in ms} for cls, ms in methods.items()}

        flat = u.Infra.build_facade_alias_map(facade, target.facade_class_prefix)
        inner = u.Infra.build_facade_inner_class_map(facade, target.facade_class_prefix)

        # 4. Scanning & Visitors
        u.Infra.progress(4, 5, "scan-files", "rope+visitors")
        files_result = u.Infra.iter_workspace_python_modules(
            workspace_root,
            exclude_packages=frozenset({target.core_project}),
        )
        if files_result.failure:
            return r[m.Infra.UtilitiesCensusReport].fail(
                f"Failed to discover files: {files_result.error}",
            )
        modules = files_result.value
        files = [file_path for _, file_path in modules]
        roots = [project_root for project_root, _ in modules]

        recs: MutableSequence[m.Infra.CensusUsageRecord] = []
        errs = usage = 0
        for i, fp in enumerate(files, 1):
            if i % 500 == 0:
                u.Infra.info(f"  [{i}/{len(files)}] scanned...")

            project = u.Infra.identify_project_by_roots(fp, roots)
            try:
                source = fp.read_text(encoding=c.Infra.ENCODING_DEFAULT)
            except (OSError, UnicodeDecodeError):
                errs += 1
                continue
            imp = FlextInfraCensusImportDiscoveryVisitor(
                family_alias=target.family,
                facade_class_prefix=target.facade_class_prefix,
            )
            imp.scan_source(source)
            col = FlextInfraCensusUsageCollector(
                method_index=index,
                flat_aliases=flat,
                inner_class_map=inner,
                alias_locals=imp.alias_locals,
                direct_imports=imp.direct_imports,
                file_path=fp,
                project_name=project,
            )
            col.scan_source(source)
            if col.records:
                usage += 1
                recs.extend(col.records)

        u.Infra.info(f"Files with usage: {usage}, parse errors: {errs}")

        # 5. Rollup and format
        u.Infra.progress(5, 5, "aggregate", "report")
        rep = u.Infra.aggregate_usage_metrics(methods, recs, len(files), errs)
        u.Infra.summary(
            m.Infra.SummaryStats(
                verb="census",
                total=rep.total_methods,
                success=rep.total_methods - rep.total_unused,
                failed=rep.total_unused,
                skipped=errs,
                elapsed=time.monotonic() - t0,
            )
        )
        return r[m.Infra.UtilitiesCensusReport].ok(rep)


__all__ = ["FlextInfraRefactorCensus"]
