"""Fail-closed jscpd duplicate-code detector."""

from __future__ import annotations

import ast
import shutil
import time
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, override

from flext_core import r
from flext_infra import c, m, t, u
from flext_infra.gates.base_gate import FlextInfraGate

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraDuplicationGate(FlextInfraGate):
    """Report every clone owned by one project from a fresh workspace scan."""

    gate_id: ClassVar[str] = "duplication"
    gate_name: ClassVar[str] = "Code Duplication"
    can_fix: ClassVar[bool] = False

    # flext-pulj: process results stay structural outside the Pydantic boundary.
    _scan_cache: ClassVar[dict[str, p.Cli.CommandOutput]] = {}
    _python_behavior_cache: ClassVar[
        dict[tuple[str, int, int], tuple[tuple[int, int], ...]]
    ] = {}

    @override
    def check(
        self, project_dir: Path, ctx: m.Infra.GateContext
    ) -> m.Infra.GateExecution:
        """Run and validate jscpd, then expose every owned clone as an error."""
        _ = ctx
        started = time.monotonic()
        scan = self._scan_workspace()
        parsed = self._issues_from_report(scan, project_dir)
        issues = (
            parsed.value if parsed.success else (self._failure_issue(parsed.error),)
        )
        if not issues and scan.outcome.raw_return_code not in {0, 1}:
            issues = (self._tool_failure_issue(scan),)
        return self._build_check_gate_execution(
            project_dir,
            passed=not issues,
            issues=issues,
            raw_output="\n".join(part for part in (scan.stdout, scan.stderr) if part),
            started=started,
        )

    def _scan_workspace(self) -> p.Cli.CommandOutput:
        """Create one fresh report; tool, scope, and report failures escape."""
        binary = shutil.which(c.Infra.JSCPD_BINARY)
        if binary is None:
            return m.Cli.CommandOutput(
                stdout="",
                stderr=(
                    f"{c.Infra.JSCPD_BINARY} not found on PATH; `make setup` "
                    "provisions it from codegen.toolchain.jscpd_version"
                ),
                # jscpd itself exits 1 when it finds clones, so an absent binary
                # must not borrow that code or the gate would read it as a scan.
                outcome=m.Cli.ProcessOutcome(
                    raw_return_code=c.Infra.PROCESS_COMMAND_NOT_FOUND_EXIT_CODE,
                    timed_out=False,
                    forwarded_signal=None,
                ),
            )
        scope = self._render_scope_dirs()
        if scope.failure:
            return m.Cli.CommandOutput(
                stdout="",
                stderr=scope.error or "workspace scope resolution failed",
                outcome=m.Cli.ProcessOutcome(
                    raw_return_code=1, timed_out=False, forwarded_signal=None
                ),
            )
        if not scope.value:
            return m.Cli.CommandOutput(
                stdout="",
                stderr="jscpd scope resolved no source or test directories",
                outcome=m.Cli.ProcessOutcome(
                    raw_return_code=1, timed_out=False, forwarded_signal=None
                ),
            )
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
            "--config",
            str(config_path),
            "--reporters",
            "json",
            "--output",
            str(report_dir),
            *scope.value,
        )
        result = self._run(cmd, self._repository_root, timeout=c.Infra.TIMEOUT_LONG)
        return self._load_report(report_dir, result)

    def _render_scope_dirs(self) -> p.Result[t.StrSequence]:
        """Every discovered workspace project's existing ``src``/``tests`` trees.

        Reuses the same workspace-topology discovery every other check-scoping
        path uses (``u.Infra.resolve_projects``) — never a second hardcoded
        project list.
        """
        discovered = u.Infra.resolve_projects(self._repository_root, ())
        if discovered.failure:
            return r[t.StrSequence].from_failure(discovered)
        return r[t.StrSequence].ok(
            tuple(
                str(project.path / candidate)
                for project in discovered.value
                for candidate in self._existing_check_dirs(project.path)
            )
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

    @staticmethod
    def _load_report(
        report_dir: Path, result: p.Cli.CommandOutput
    ) -> p.Cli.CommandOutput:
        """Load the JSON report jscpd writes to disk; stdout carries console noise only."""
        report_path = report_dir / c.Infra.JSCPD_REPORT_FILENAME
        if not report_path.is_file():
            return result
        return m.Cli.CommandOutput(
            stdout=report_path.read_text(encoding="utf-8"),
            stderr=result.stderr,
            outcome=m.Cli.ProcessOutcome(
                raw_return_code=result.outcome.raw_return_code,
                timed_out=result.outcome.timed_out,
                forwarded_signal=result.outcome.forwarded_signal,
            ),
        )

    @staticmethod
    def _resolve_binary() -> str | None:
        """Locate the mise-provisioned jscpd on PATH; None when absent."""
        return shutil.which(c.Infra.JSCPD_BINARY)

    def _tool_failure_issue(self, scan: p.Cli.CommandOutput) -> m.Infra.Issue:
        """Scanner absence/crash must never read as a clean pass."""
        return m.Infra.Issue(
            file=c.Infra.PYPROJECT_FILENAME,
            line=1,
            column=0,
            code=self.gate_id,
            message=scan.stderr or "jscpd execution failed",
            severity=str(c.Infra.GateSeverity.ERROR.value),
        )

    @staticmethod
    def _failure_issue(message: str | None) -> m.Infra.Issue:
        """Represent malformed or absent jscpd output as a blocking issue."""
        return m.Infra.Issue(
            file=c.Infra.PYPROJECT_FILENAME,
            line=1,
            column=0,
            code=FlextInfraDuplicationGate.gate_id,
            message=message or "jscpd returned no parseable report",
            severity=str(c.Infra.GateSeverity.ERROR.value),
        )

    @classmethod
    def _issues_from_report(
        cls, scan: p.Cli.CommandOutput, project_dir: Path
    ) -> p.Result[tuple[m.Infra.Issue, ...]]:
        """Extract one Issue per clone side that falls inside ``project_dir``."""
        if not scan.stdout.strip():
            return r[tuple[m.Infra.Issue, ...]].fail("jscpd returned empty JSON report")
        parsed = u.Cli.json_parse(scan.stdout)
        if parsed.failure:
            return r[tuple[m.Infra.Issue, ...]].from_failure(parsed)
        data = u.Cli.json_as_mapping(parsed.value)
        prefix = str(project_dir)
        issues: list[m.Infra.Issue] = []
        for duplicate in u.Cli.json_deep_mapping_list(data, "duplicates"):
            first = u.Cli.json_deep_mapping(duplicate, "firstFile")
            second = u.Cli.json_deep_mapping(duplicate, "secondFile")
            first_name = u.Cli.json_pick_str(first, "name")
            second_name = u.Cli.json_pick_str(second, "name")
            if not cls._is_semantic_clone(duplicate, first, second):
                continue
            if first_name.startswith(prefix):
                issues.append(
                    cls._issue_from_duplicate(
                        duplicate, first, first_name, second_name, project_dir
                    )
                )
            elif second_name.startswith(prefix) and second_name != first_name:
                issues.append(
                    cls._issue_from_duplicate(
                        duplicate, second, second_name, first_name, project_dir
                    )
                )
        return r[tuple[m.Infra.Issue, ...]].ok(tuple(issues))

    @classmethod
    def _is_semantic_clone(
        cls, duplicate: t.JsonMapping, first: t.JsonMapping, second: t.JsonMapping
    ) -> bool:
        """Require executable Python behavior on both sides of a clone.

        jscpd is the candidate detector, not the semantic authority. Python
        module licenses, docstrings, imports, ``TYPE_CHECKING`` blocks, class
        shells, function signatures, and declaration-only assignments are
        intentionally repeated language structure rather than competing
        implementations. A candidate remains blocking when both source ranges
        contain an executable statement. Unreadable or unparsable input stays
        blocking because absence of semantic proof can never produce green.
        Non-Python formats likewise remain blocking until their own semantic
        classifier exists.
        """
        if u.Cli.json_pick_str(duplicate, "format") != "python":
            return True
        return cls._range_has_python_behavior(first) and cls._range_has_python_behavior(
            second
        )

    @classmethod
    def _range_has_python_behavior(cls, side: t.JsonMapping) -> bool:
        """Return whether one jscpd source range encloses executable behavior."""
        file_name = u.Cli.json_pick_str(side, "name")
        path = Path(file_name)
        try:
            identity = path.stat()
        except OSError:
            return True
        key = (file_name, identity.st_mtime_ns, identity.st_size)
        ranges = cls._python_behavior_cache.get(key)
        if ranges is None:
            ranges = cls._python_behavior_ranges(path)
            cls._python_behavior_cache[key] = ranges
        start = u.Cli.json_nested_int(side, "startLoc", "line", default=1)
        end = u.Cli.json_nested_int(side, "endLoc", "line", default=start)
        return any(
            start <= node_start and node_end <= end for node_start, node_end in ranges
        )

    @staticmethod
    def _python_behavior_ranges(path: Path) -> tuple[tuple[int, int], ...]:
        """Parse one module into ranges for statements with runtime behavior."""
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except (OSError, SyntaxError, UnicodeError):
            return ((1, 2**31 - 1),)
        parents = {
            child: parent
            for parent in ast.walk(tree)
            for child in ast.iter_child_nodes(parent)
        }

        def inside_function(node: ast.AST) -> bool:
            parent = parents.get(node)
            while parent is not None:
                if isinstance(parent, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    return True
                parent = parents.get(parent)
            return False

        def is_declaration(node: ast.stmt) -> bool:
            if isinstance(
                node,
                (
                    ast.ClassDef,
                    ast.FunctionDef,
                    ast.AsyncFunctionDef,
                    ast.Import,
                    ast.ImportFrom,
                    ast.Pass,
                    ast.Global,
                    ast.Nonlocal,
                ),
            ):
                return True
            if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant):
                return True
            if (
                isinstance(node, ast.If)
                and isinstance(node.test, ast.Name)
                and node.test.id == "TYPE_CHECKING"
            ):
                return True
            return isinstance(
                node, (ast.Assign, ast.AnnAssign)
            ) and not inside_function(node)

        return tuple(
            (node.lineno, node.end_lineno)
            for node in ast.walk(tree)
            if isinstance(node, ast.stmt)
            and node.end_lineno is not None
            and not is_declaration(node)
        )

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
            severity=str(c.Infra.GateSeverity.ERROR.value),
        )


__all__: list[str] = ["FlextInfraDuplicationGate"]
