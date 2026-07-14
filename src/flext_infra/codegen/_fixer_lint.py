"""Rope-verified lint remediation pass for the canonical codegen fixer."""

from __future__ import annotations

import tokenize
from io import StringIO
from pathlib import Path

from flext_infra import c, config, m, p, t
from flext_infra.codegen._fixer_refactor import FlextInfraCodegenFixerRefactorMixin
from flext_infra.gates.ruff_lint import FlextInfraRuffLintGate


class FlextInfraCodegenFixerLintMixin(FlextInfraCodegenFixerRefactorMixin):
    """Apply configured Ruff remediations after Rope verifies every target."""

    @classmethod
    def _run_lint_remediation(
        cls,
        ctx: m.Infra.FixContext,
        project_path: Path,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
    ) -> None:
        """Apply every configured Ruff remediation and prove the codes are gone."""
        rules = cls._ruff_issue_rules()
        if not rules:
            return
        files = cls._ruff_rule_files(project_path, rules)
        if not files:
            return
        rope_workspace.refresh()
        gate = FlextInfraRuffLintGate(rope_workspace.rope_workspace_root)
        gate_ctx = m.Infra.GateContext(
            workspace=rope_workspace.rope_workspace_root,
            reports_dir=project_path / c.Infra.REPORTS_DIR_NAME / "codegen-auto-fix",
            apply_fixes=False,
            check_only=True,
            fail_fast=True,
        )
        before = gate.check_files(files, project_path, gate_ctx)
        cls._raise_for_parse_failure(before)
        modified = cls._apply_configured_issues(
            ctx=ctx,
            project_path=project_path,
            rope_workspace=rope_workspace,
            issues=before.issues,
            rules=rules,
        )
        if not modified:
            return
        rope_workspace.refresh()
        after = gate.check_files(files, project_path, gate_ctx)
        cls._raise_for_parse_failure(after)
        remaining = tuple(
            issue
            for issue in after.issues
            if any(issue.code == rule.code for rule in rules)
        )
        if remaining:
            first = remaining[0]
            msg = (
                "configured Ruff remediation remained after apply: "
                f"{first.code} {first.file}:{first.line}:{first.column}"
            )
            raise RuntimeError(msg)

    @staticmethod
    def _ruff_issue_rules() -> tuple[m.Infra.StaticRuffIssueRule, ...]:
        """Return configured Ruff rules without duplicating policy in Python."""
        return tuple(
            rule
            for rule in config.Infra.enforcement.rules
            if isinstance(rule, m.Infra.StaticRuffIssueRule)
        )

    @staticmethod
    def _ruff_rule_files(
        project_path: Path, rules: t.SequenceOf[m.Infra.StaticRuffIssueRule]
    ) -> tuple[Path, ...]:
        """Return Python files below the roots declared by selected rules."""
        roots = tuple(dict.fromkeys(root for rule in rules for root in rule.roots))
        return tuple(
            sorted(
                (
                    file_path
                    for root in roots
                    for file_path in (project_path / root).rglob(
                        c.Infra.EXT_PYTHON_GLOB
                    )
                    if file_path.is_file()
                ),
                key=Path.as_posix,
            )
        )

    @staticmethod
    def _raise_for_parse_failure(execution: m.Infra.GateExecution) -> None:
        """Fail loudly when Ruff output did not become typed diagnostics."""
        parse_failure = next(
            (issue for issue in execution.issues if issue.code == "PARSE_ERROR"), None
        )
        if parse_failure is not None:
            raise RuntimeError(parse_failure.message)

    @classmethod
    def _apply_configured_issues(
        cls,
        *,
        ctx: m.Infra.FixContext,
        project_path: Path,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        issues: t.SequenceOf[m.Infra.Issue],
        rules: t.SequenceOf[m.Infra.StaticRuffIssueRule],
    ) -> frozenset[Path]:
        """Group configured diagnostics by file and apply each file once."""
        grouped: t.MutableMappingKV[
            Path,
            t.MutableSequenceOf[t.Pair[m.Infra.Issue, m.Infra.StaticRuffIssueRule]],
        ] = {}
        for issue in issues:
            rule = next((item for item in rules if item.code == issue.code), None)
            if rule is None:
                continue
            file_path = cls._issue_path(project_path, issue.file)
            cls._validate_rule_path(project_path, file_path, rule)
            grouped.setdefault(file_path, []).append((issue, rule))
        modified: set[Path] = set()
        for file_path, entries in grouped.items():
            cls._apply_file_entries(
                ctx=ctx,
                file_path=file_path,
                rope_workspace=rope_workspace,
                entries=entries,
            )
            modified.add(file_path)
        return frozenset(modified)

    @staticmethod
    def _issue_path(project_path: Path, issue_file: str) -> Path:
        """Resolve one Ruff filename against its project boundary."""
        candidate = Path(issue_file)
        return (
            candidate if candidate.is_absolute() else project_path / candidate
        ).resolve()

    @staticmethod
    def _validate_rule_path(
        project_path: Path, file_path: Path, rule: m.Infra.StaticRuffIssueRule
    ) -> None:
        """Prove one diagnostic belongs to a configured project-relative root."""
        resolved_project = project_path.resolve()
        if not file_path.is_relative_to(resolved_project):
            message = f"Ruff diagnostic escaped project root: {file_path}"
            raise RuntimeError(message)
        relative = file_path.relative_to(resolved_project)
        if not relative.parts or relative.parts[0] not in rule.roots:
            msg = f"Ruff diagnostic is outside configured roots: {relative}"
            raise RuntimeError(msg)

    @classmethod
    def _apply_file_entries(
        cls,
        *,
        ctx: m.Infra.FixContext,
        file_path: Path,
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        entries: t.SequenceOf[t.Pair[m.Infra.Issue, m.Infra.StaticRuffIssueRule]],
    ) -> None:
        """Render all insertions against one stable Rope/source snapshot."""
        source = rope_workspace.source(file_path)
        semantic_objects = rope_workspace.objects(
            file_path, include_local_scopes=True, include_references=False
        )
        insertions: t.MutableSequenceOf[t.Pair[int, str]] = []
        fixed: t.MutableSequenceOf[
            t.Pair[m.Infra.Issue, m.Infra.StaticRuffIssueRule]
        ] = []
        for issue, rule in entries:
            semantic_object = next(
                (
                    item
                    for item in semantic_objects
                    if item.line == issue.line
                    and item.kind in rule.scope_kinds
                    and item.name.startswith(rule.name_prefix)
                ),
                None,
            )
            if semantic_object is None:
                msg = (
                    "Rope could not prove configured Ruff target: "
                    f"{file_path}:{issue.line} {issue.code}"
                )
                raise RuntimeError(msg)
            body_index, indentation = cls._function_body_insertion(
                source, issue.line, semantic_object.name
            )
            summary = semantic_object.name.removeprefix(rule.name_prefix).replace(
                "_", " "
            )
            try:
                docstring = rule.docstring_template.format(summary=summary)
            except (KeyError, ValueError) as exc:
                msg = f"Invalid docstring template for {rule.kind}: {exc}"
                raise RuntimeError(msg) from exc
            insertions.append((body_index, f'{indentation}"""{docstring}"""\n'))
            fixed.append((issue, rule))
        lines: t.MutableSequenceOf[str] = list(source.splitlines(keepends=True))
        for body_index, rendered in sorted(insertions, reverse=True):
            lines.insert(body_index, rendered)
        updated = "".join(lines)
        resource = rope_workspace.resource(file_path)
        if resource is None:
            message = f"Rope resource unavailable for {file_path}"
            raise RuntimeError(message)
        resource.write(updated)
        ctx.files_modified.add(str(file_path))
        ctx.violations_fixed.extend(
            m.Infra.CensusViolation(
                module=str(file_path),
                rule=issue.code,
                line=issue.line,
                message=rule.detail,
                fixable=True,
            )
            for issue, rule in fixed
        )

    @staticmethod
    def _function_body_insertion(
        source: str, definition_line: int, name: str
    ) -> t.Pair[int, str]:
        """Return the first body-line index and indentation for a Rope function."""
        tokens = tuple(tokenize.generate_tokens(StringIO(source).readline))
        definition_index = next(
            (
                index
                for index, token in enumerate(tokens)
                if token.type == tokenize.NAME
                and token.string == "def"
                and token.start[0] == definition_line
            ),
            None,
        )
        if definition_index is None:
            message = f"Function definition token unavailable for {name}"
            raise RuntimeError(message)
        indentation = next(
            (
                token
                for token in tokens[definition_index + 1 :]
                if token.type == tokenize.INDENT
            ),
            None,
        )
        if indentation is None:
            message = f"Multiline function body unavailable for {name}"
            raise RuntimeError(message)
        return indentation.start[0] - 1, indentation.string


__all__: tuple[str, ...] = ("FlextInfraCodegenFixerLintMixin",)
