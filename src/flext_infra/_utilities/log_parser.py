"""Read the reports tools wrote back: SARIF findings and JUnit documents.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from pathlib import Path

from defusedxml import ElementTree as DefusedET
from flext_cli import u

from flext_infra import c, m, p, r


class FlextInfraUtilitiesLogParser:
    """Read the reports tools wrote back into typed values."""

    @staticmethod
    def check_report_findings(
        repository_root: Path,
        *,
        reports_dir: Path,
    ) -> p.Result[tuple[m.Infra.SarifResult, ...]]:
        """Read the SARIF report ``check run`` wrote into typed findings.

        ``reports_dir`` is the exact invocation directory printed by ``check run``,
        not its shared base. Relative values are anchored at ``repository_root``.
        No implicit latest report is selected from concurrent or historical runs.

        Returns:
            The resulting ``p.Result[tuple[m.Infra.SarifResult, ...]]``.

        """
        report_dir = (
            reports_dir if reports_dir.is_absolute() else repository_root / reports_dir
        )
        sarif_path = report_dir / c.Infra.CHECK_REPORT_SARIF_FILENAME
        if not sarif_path.is_file():
            return r[tuple[m.Infra.SarifResult, ...]].fail(
                f"check report not found: {sarif_path}",
            )
        return u.validate_value(
            m.Infra.SarifReport,
            sarif_path.read_text(encoding=c.DEFAULT_ENCODING),
            from_json=True,
        ).map(lambda report: tuple(res for run in report.runs for res in run.results))

    @staticmethod
    def mypy_build_sources(stderr: str, project_dir: Path) -> tuple[Path, ...]:
        """Read the selected sources and completion proof from Mypy's verbose trace.

        Mypy prints each ``BuildSource`` path as a Python string literal, so the
        literal is decoded once here, at the tool-output boundary.

        Returns:
            The resolved source paths Mypy reported, in trace order.

        Raises:
            TypeError: If a reported source path is not a string literal.
            ValueError: If an entry is malformed, no source is reported, or the
                trace lacks completion evidence.

        """
        lines = stderr.splitlines()
        sources: list[Path] = []
        for line in lines:
            if c.Infra.MYPY_BUILD_SOURCE_MARKER not in line:
                continue
            match = c.Infra.MYPY_BUILD_SOURCE_RE.search(line)
            if match is None:
                msg = f"Malformed Mypy native source entry: {line}"
                raise ValueError(msg)
            raw_path = ast.literal_eval(match.group(1))
            if not isinstance(raw_path, str):
                msg = f"Mypy native source path is not a string: {line}"
                raise TypeError(msg)
            sources.append((project_dir / raw_path).resolve())
        if not sources:
            msg = "Mypy native build trace contains no selected sources"
            raise ValueError(msg)
        if not any(c.Infra.MYPY_BUILD_FINISHED_MARKER in line for line in lines):
            msg = "Mypy native build trace lacks completion evidence"
            raise ValueError(msg)
        return tuple(sources)

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
