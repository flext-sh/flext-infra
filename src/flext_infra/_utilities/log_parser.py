"""Read the reports tools wrote back: SARIF findings and JUnit documents.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from defusedxml import ElementTree as DefusedET
from flext_cli import u

from flext_infra import c, m, p, r, t

if TYPE_CHECKING:
    from pathlib import Path


class FlextInfraUtilitiesLogParser:
    """Read the reports tools wrote back into typed values."""

    @staticmethod
    def check_report_findings(
        repository_root: Path,
        *,
        reports_dir: Path,
    ) -> p.Result[t.VariadicTuple[m.Infra.SarifResult]]:
        """Read the SARIF report ``check run`` wrote into typed findings.

        ``reports_dir`` is the exact invocation directory printed by ``check run``,
        not its shared base. Relative values are anchored at ``repository_root``.
        No implicit latest report is selected from concurrent or historical runs.

        Returns:
            The resulting ``p.Result[t.VariadicTuple[m.Infra.SarifResult]]``.

        """
        report_dir = (
            reports_dir if reports_dir.is_absolute() else repository_root / reports_dir
        )
        sarif_path = report_dir / c.Infra.CHECK_REPORT_SARIF_FILENAME
        if not sarif_path.is_file():
            return r[t.VariadicTuple[m.Infra.SarifResult]].fail(
                f"check report not found: {sarif_path}",
            )
        return u.validate_value(
            m.Infra.SarifReport,
            sarif_path.read_text(encoding=c.DEFAULT_ENCODING),
            from_json=True,
        ).map(lambda report: tuple(res for run in report.runs for res in run.results))

    @staticmethod
    def junit_report_root(junit: Path) -> p.Infra.XmlElementLike | None:
        """Parse one JUnit report with the safe XML parser.

        A malformed document raises the parser's own error unchanged; a parsed
        document without a root keeps the parser's typed absence for the caller.

        Returns:
            The document root, or ``None`` when the document has none.

        """
        return DefusedET.parse(junit).getroot()


__all__: list[str] = ["FlextInfraUtilitiesLogParser"]
