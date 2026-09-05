"""Strict jscpd gate backed by a fresh, typed report."""

from __future__ import annotations

import shutil
import time
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, override

from flext_infra import c, m, u
from flext_infra.gates.base_gate import FlextInfraGate

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraDuplicationGate(FlextInfraGate):
    """Report every clone owned by one project from a fresh workspace scan."""

    gate_id: ClassVar[str] = "duplication"
    gate_name: ClassVar[str] = "Code Duplication"
    can_fix: ClassVar[bool] = False
    tool_name: ClassVar[str] = c.Infra.SARIF_TOOL_INFO["duplication"][0]
    tool_url: ClassVar[str] = c.Infra.SARIF_TOOL_INFO["duplication"][1]

    @override
    def check(
        self, project_dir: Path, ctx: m.Infra.GateContext
    ) -> m.Infra.GateExecution:
        """Run and validate jscpd, then expose every owned clone as an error."""
        _ = ctx
        started = time.monotonic()
        scan = self._scan_workspace()
        issues = self._issues_from_report(scan, project_dir)
        return self._build_check_gate_execution(
            project_dir,
            passed=not issues,
            issues=issues,
            raw_output="\n".join(part for part in (scan.stdout, scan.stderr) if part),
            started=started,
        )

    def _scan_workspace(self) -> m.Infra.JscpdScan:
        """Create one fresh report; tool, scope, and report failures escape."""
        binary = shutil.which(c.Infra.JSCPD_BINARY)
        if binary is None:
            raise FileNotFoundError(c.Infra.JSCPD_BINARY)
        scope = self._scope_paths()
        config_path = self._render_config()
        report_dir = self._repository_root / c.Infra.JSCPD_REPORT_DIRNAME
        report_path = report_dir / c.Infra.JSCPD_REPORT_FILENAME
        if report_path.is_symlink() or (
            report_path.exists() and not report_path.is_file()
        ):
            msg = f"jscpd report target is not a physical file: {report_path}"
            raise ValueError(msg)
        if report_path.is_file():
            report_path.unlink()
        cmd = (
            binary,
            "--no-gitignore",
            "--config",
            str(config_path),
            "--reporters",
            "json",
            "--output",
            str(report_dir),
            *scope,
        )
        output = self._run(cmd, self._repository_root, timeout=c.Infra.TIMEOUT_LONG)
        raw_output = self._raw_output(output)
        if output.exit_code not in {0, 1}:
            raise RuntimeError(raw_output or f"jscpd exited {output.exit_code}")
        if not report_path.is_file():
            raise FileNotFoundError(report_path)
        report = m.Infra.JscpdReport.model_validate_json(
            report_path.read_text(encoding=c.Cli.ENCODING_DEFAULT)
        )
        if output.exit_code == 1 and report.statistics.total.clones == 0:
            raise RuntimeError(raw_output or "jscpd failed without clone evidence")
        return m.Infra.JscpdScan(
            exit_code=output.exit_code,
            report=report,
            stderr=output.stderr,
            stdout=output.stdout,
        )

    def _scope_paths(self) -> t.StrSequence:
        """Resolve canonical source, test, config, and template roots once."""
        projects = u.Infra.resolve_projects(self._repository_root, ()).unwrap()
        scope = tuple(
            str(path)
            for project in projects
            for dirname in c.Infra.JSCPD_SCOPE_DIRNAMES
            if (path := project.path / dirname).is_dir()
        )
        if not scope:
            msg = f"jscpd found no canonical scope under {self._repository_root}"
            raise ValueError(msg)
        return scope

    def _render_config(self) -> Path:
        """Materialize the jscpd config from this gate's typed SSOT.

        A generated-at-scan-time projection, never a second hand-edited
        source; regenerating with unchanged constants produces byte-identical
        content (idempotent).
        """
        config = m.Infra.JscpdConfig(
            absolute=True,
            formatsExts={
                name: tuple(extensions)
                for name, extensions in c.Infra.JSCPD_FORMAT_EXTENSIONS.items()
            },
            ignore=tuple(c.Infra.JSCPD_IGNORE_PATTERNS),
            minLines=c.Infra.JSCPD_MIN_LINES,
            minTokens=c.Infra.JSCPD_MIN_TOKENS,
            mode=c.Infra.JSCPD_MODE,
            noColors=True,
            noTips=True,
            reporters=(c.Infra.OUTPUT_JSON,),
            threshold=c.Infra.JSCPD_THRESHOLD_PERCENT,
        )
        config_path = (
            self._repository_root
            / c.Infra.JSCPD_REPORT_DIRNAME
            / c.Infra.JSCPD_CONFIG_FILENAME
        )
        u.Cli.ensure_dir(config_path.parent).unwrap()
        rendered = config.model_dump_json(by_alias=True)
        u.Cli.atomic_write_text_file(config_path, rendered).unwrap()
        return config_path

    @classmethod
    def _issues_from_report(
        cls, scan: m.Infra.JscpdScan, project_dir: Path
    ) -> tuple[m.Infra.Issue, ...]:
        """Extract one issue per clone side physically owned by ``project_dir``."""
        issues: list[m.Infra.Issue] = []
        root = project_dir.resolve()
        for duplicate in scan.report.duplicates:
            sides = (duplicate.first_file, duplicate.second_file)
            for own_side, other_side in (sides, tuple(reversed(sides))):
                own_path = Path(own_side.name)
                if own_path.is_relative_to(root) and own_path != Path(other_side.name):
                    issues.append(cls._issue(duplicate, own_side, other_side, root))
        return tuple(issues)

    @classmethod
    def _issue(
        cls,
        duplicate: m.Infra.JscpdDuplicate,
        own_side: m.Infra.JscpdFile,
        other_side: m.Infra.JscpdFile,
        root: Path,
    ) -> m.Infra.Issue:
        """Map one validated clone side to a strict error."""
        return m.Infra.Issue(
            file=str(Path(own_side.name).relative_to(root)),
            line=own_side.start_location.line,
            column=own_side.start_location.column,
            code=cls.gate_id,
            message=(
                f"{duplicate.lines}-line ({duplicate.tokens}-token) clone of "
                f"{other_side.name} "
                f"— extend one owner, rewire consumers, delete the duplicate"
            ),
            severity=c.Infra.GateSeverity.ERROR.value,
        )


__all__: list[str] = ["FlextInfraDuplicationGate"]
