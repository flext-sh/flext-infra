"""Docs-audit per-issue-type detectors (token/scope/ownership/docstring/codeblock).

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import re
import sys
import tempfile
from collections.abc import MutableMapping, MutableSequence, Sequence
from pathlib import Path

from flext_cli import u

from flext_infra import c, config, m, p
from flext_infra._utilities._docs import (
    FlextInfraUtilitiesDocsApi,
    FlextInfraUtilitiesDocsBase,
    FlextInfraUtilitiesDocsScope,
)
from flext_infra._utilities._rope import FlextInfraUtilitiesRopeCore


class FlextInfraUtilitiesDocsAuditDetectors:
    """Self-contained docs-audit issue detectors.

    Composed into FlextInfraUtilitiesDocsAudit via inheritance; each detector
    is an independent ``u.Infra.docs_*_issues`` entry over one ``DocScope``.
    """

    @staticmethod
    def docs_text_token_issues(
        scope: p.Infra.DocScope,
        *,
        tokens: Sequence[str],
        issue_type: str,
    ) -> Sequence[p.Infra.AuditIssue]:
        """Collect token-presence issues in the complete Markdown scope.

        Returns:
            The resulting ``Sequence[p.Infra.AuditIssue]``.

        """
        issues: MutableSequence[p.Infra.AuditIssue] = []
        if not tokens:
            return issues
        for md_file in FlextInfraUtilitiesDocsBase.iter_scope_markdown_files(scope):
            rel = md_file.relative_to(scope.path).as_posix()
            text = md_file.read_text(encoding=c.DEFAULT_ENCODING)
            for token in tokens:
                if token in text:
                    issues.append(
                        m.Infra.AuditIssue(
                            file=rel,
                            issue_type=issue_type,
                            severity="medium",
                            message=f"contains `{token}`",
                        ),
                    )
        return issues

    @staticmethod
    def docs_placeholder_issues(
        scope: p.Infra.DocScope,
        *,
        patterns: Sequence[str],
    ) -> Sequence[p.Infra.AuditIssue]:
        """Find unfinished markers using declared lexical patterns.

        Returns:
            The resulting ``Sequence[p.Infra.AuditIssue]``.

        """
        issues: MutableSequence[p.Infra.AuditIssue] = []
        compiled = tuple(re.compile(pattern) for pattern in patterns)
        for md_file in FlextInfraUtilitiesDocsBase.iter_scope_markdown_files(scope):
            rel = md_file.relative_to(scope.path).as_posix()
            content = md_file.read_text(encoding=c.DEFAULT_ENCODING)
            for pattern in compiled:
                if pattern.search(content):
                    issues.append(
                        m.Infra.AuditIssue(
                            file=rel,
                            issue_type="placeholder",
                            severity="medium",
                            message=f"matches placeholder pattern `{pattern.pattern}`",
                        ),
                    )
        return issues

    @staticmethod
    def docs_machine_path_issues(
        scope: p.Infra.DocScope,
        *,
        historical_evidence_files: tuple[Path, ...],
        container_home_identities: Sequence[str],
    ) -> Sequence[p.Infra.AuditIssue]:
        """Collect per-user absolute paths frozen into markdown outside the root.

        A path rooted at one operator's home binds the document to one
        machine. The detector inverts the ownership question: a matched
        ``/home/<user>`` or ``/Users/<user>`` path is only documentation
        when it points inside this checkout (the checkout's own declared
        location) or at a container/CI identity whose home the declared
        docs-audit contract owns as an image contract
        (``container_home_identities``). Everything else is a machine-local
        leak. Only exact declared dated evidence files retain the observed
        machine path.

        Returns:
            The resulting ``Sequence[p.Infra.AuditIssue]``.

        """
        issues: MutableSequence[p.Infra.AuditIssue] = []
        container_identities = frozenset(container_home_identities)
        evidence = set(historical_evidence_files)
        for md_file in FlextInfraUtilitiesDocsBase.iter_scope_markdown_files(scope):
            rel = md_file.relative_to(scope.path).as_posix()
            if Path(rel) in evidence:
                continue
            text = md_file.read_text(encoding=c.DEFAULT_ENCODING)
            for line_number, line in enumerate(text.splitlines(), start=1):
                for match in c.Infra.MACHINE_PATH_RE.finditer(line):
                    user = match.group(c.ContextScope.USER)
                    if user in container_identities:
                        continue
                    if FlextInfraUtilitiesDocsAuditDetectors._path_inside_root(
                        line,
                        match.start(),
                        scope.path,
                    ):
                        continue
                    issues.append(
                        m.Infra.AuditIssue(
                            file=rel,
                            issue_type="machine-path",
                            severity="high",
                            message=(
                                f"line {line_number} embeds machine-local path "
                                f"`{match.group(0)}`"
                            ),
                        ),
                    )
        return issues

    @staticmethod
    def _path_inside_root(line: str, start: int, root: Path) -> bool:
        """Return whether the absolute path token at ``start`` sits under root.

        The token extends from the match start across the maximal run of
        path characters the line holds, so nested checkout paths resolve
        against the checkout root instead of only their home prefix. The
        detector regex guarantees the token starts with ``/``.

        Returns:
            The resulting ``bool``.

        """
        end = start
        while end < len(line) and (line[end].isalnum() or line[end] in "/._-~"):
            end += 1
        try:
            return Path(line[start:end]).is_relative_to(root.resolve())
        except OSError:
            return False

    @staticmethod
    def scope_boundary_issues(
        scope: p.Infra.DocScope,
    ) -> Sequence[p.Infra.AuditIssue]:
        """Collect references to excluded non-FLEXT roots in root docs.

        A mention counts only when the excluded root appears as a path
        reference: the token followed by a path separator. Bare prose uses
        of the token (an English word, a brand name, an identifier suffix
        like ``example-org``) are not directory references and never
        were.

        Returns:
            The resulting ``Sequence[p.Infra.AuditIssue]``.

        """
        if scope.name != c.Infra.RK_ROOT:
            return []
        issues: MutableSequence[p.Infra.AuditIssue] = []
        excluded = sorted(FlextInfraUtilitiesDocsScope.excluded_roots(scope.path))
        patterns = [
            re.compile(rf"(^|[^A-Za-z0-9_]){re.escape(token)}[/\\]", re.IGNORECASE)
            for token in excluded
        ]
        for md_file in [
            scope.path / "README.md",
            *FlextInfraUtilitiesDocsBase.iter_scope_markdown_files(scope),
        ]:
            if not md_file.exists():
                continue
            text = md_file.read_text(encoding=c.DEFAULT_ENCODING)
            for token, pattern in zip(excluded, patterns, strict=True):
                if pattern.search(text):
                    issues.append(
                        m.Infra.AuditIssue(
                            file=md_file.relative_to(scope.path).as_posix(),
                            issue_type="scope_boundary",
                            severity="high",
                            message=f"root docs mention out-of-scope project `{token}`",
                        ),
                    )
        return issues

    @staticmethod
    def generated_ownership_issues(
        scope: p.Infra.DocScope,
    ) -> Sequence[p.Infra.AuditIssue]:
        """Collect manual API pages that duplicate generated ownership.

        Returns:
            The resulting ``Sequence[p.Infra.AuditIssue]``.

        """
        issues: MutableSequence[p.Infra.AuditIssue] = []
        api_reference = scope.path / c.Infra.DIR_DOCS / "api-reference"
        candidates: MutableSequence[Path] = (
            sorted(api_reference.rglob("*.md")) if api_reference.exists() else []
        )
        relative_paths = tuple(
            path.relative_to(scope.path / c.Infra.DIR_DOCS) for path in candidates
        )
        excluded = FlextInfraUtilitiesDocsScope.excluded_doc_paths(
            scope.path,
            relative_paths,
        )
        for path, relative_path in zip(candidates, relative_paths, strict=True):
            rel = path.relative_to(scope.path).as_posix()
            if relative_path in excluded:
                continue
            if rel == "docs/api-reference/README.md" or rel.startswith(
                "docs/api-reference/generated/",
            ):
                continue
            issues.append(
                m.Infra.AuditIssue(
                    file=rel,
                    issue_type="generated_ownership",
                    severity="medium",
                    message="manual API page duplicates generated API ownership",
                ),
            )
        return issues

    @staticmethod
    def docs_public_docstring_issues(
        scope: p.Infra.DocScope,
    ) -> Sequence[p.Infra.AuditIssue]:
        """Collect missing docstring issues for public exports and modules.

        Returns:
            The resulting ``Sequence[p.Infra.AuditIssue]``.

        """
        if scope.name == c.Infra.RK_ROOT or not scope.package_name:
            return []
        with FlextInfraUtilitiesRopeCore.open_project(scope.path) as rope_project:
            contract = FlextInfraUtilitiesDocsApi.public_contract(
                scope.path,
                scope.package_name,
                rope_project=rope_project,
            )
            return FlextInfraUtilitiesDocsApi.docstring_issues(
                scope.path, contract, rope_project=rope_project
            )

    @staticmethod
    def docs_public_docstring_coverage(
        scope: p.Infra.DocScope,
    ) -> p.Infra.DocstringCoverage | None:
        """Aggregate docstring coverage for a project scope (None at root).

        Returns:
            The resulting ``m.Infra.DocstringCoverage | None``.

        """
        if scope.name == c.Infra.RK_ROOT or not scope.package_name:
            return None
        with FlextInfraUtilitiesRopeCore.open_project(scope.path) as rope_project:
            contract = FlextInfraUtilitiesDocsApi.public_contract(
                scope.path,
                scope.package_name,
                rope_project=rope_project,
            )
            return FlextInfraUtilitiesDocsApi.docstring_coverage(
                scope.path, contract, rope_project=rope_project
            )

    @staticmethod
    def docs_python_codeblock_issues(
        scope: p.Infra.DocScope,
    ) -> Sequence[p.Infra.AuditIssue]:
        """Lint embedded ``python`` fenced blocks under one docs scope.

        Captures every ``python`` fenced block via ``u.Infra.docs_is_python_fence``
        and gates the complete capture in one native ``ruff check`` invocation
        over one temporary file per fence. Every fence keeps its own file, so a
        symbol defined in one block never satisfies another block, while the
        scope pays one interpreter and project-config load instead of one per
        fence. Failures land as ``m.Infra.AuditIssue`` records flowing through
        the standard audit report pipeline.

        Returns:
            The resulting ``Sequence[p.Infra.AuditIssue]``.

        """
        documents: MutableSequence[tuple[str, int, bytes]] = []
        for md_file in FlextInfraUtilitiesDocsBase.iter_scope_markdown_files(scope):
            rel = md_file.relative_to(scope.path).as_posix()
            content = md_file.read_text(encoding=c.DEFAULT_ENCODING)
            if content.startswith(c.Infra.DOCS_PROJECTION_MARKER):
                # A projected guide's fences are validated once at their
                # workspace source; re-linting the copy under the member's
                # import order only reports the projection context.
                continue
            documents.extend(
                (rel, index, fence.code.encode())
                for index, fence in enumerate(
                    filter(
                        FlextInfraUtilitiesDocsBase.docs_is_python_fence,
                        u.Cli.markdown_fences(content),
                    ),
                )
            )
        if not documents:
            return []
        return FlextInfraUtilitiesDocsAuditDetectors._python_codeblock_issues(
            scope,
            documents,
        )

    @staticmethod
    def _python_codeblock_issues(
        scope: p.Infra.DocScope,
        documents: Sequence[tuple[str, int, bytes]],
    ) -> Sequence[p.Infra.AuditIssue]:
        """Check every captured fence in one native ruff process.

        Returns:
            The resulting ``Sequence[p.Infra.AuditIssue]``.

        """
        with tempfile.TemporaryDirectory(prefix="flext-docs-codeblocks-") as scratch:
            targets: MutableMapping[str, tuple[str, int]] = {}
            for position, (rel, index, code) in enumerate(documents):
                filename = f"block_{position:04d}.py"
                (Path(scratch) / filename).write_bytes(code)
                targets[filename] = (rel, index)
            # Ruff via running interpreter (venv SSOT);
            # bare "ruff" breaks when .venv/bin is not on PATH (CI docs audit).
            command: MutableSequence[str] = [
                sys.executable,
                "-m",
                c.Infra.RUFF,
                c.Infra.VERB_CHECK,
                *config.Infra.codegen.make.ruff.lint_check,
                "--extend-ignore",
                ",".join(c.Infra.PYTHON_FENCE_RUFF_EXTEND_IGNORE),
                "--no-cache",
                "--output-format",
                "concise",
            ]
            manifest = scope.path / c.PYPROJECT_FILENAME
            if manifest.is_file():
                command.extend(("--config", manifest.as_posix()))
            command.append(scratch)
            outcome = u.Cli.run_raw(command, cwd=scope.path)
            if outcome.failure:
                return FlextInfraUtilitiesDocsAuditDetectors._codeblock_failure(
                    documents,
                    outcome.error or "ruff process failed",
                )
            grouped: MutableMapping[tuple[str, int], MutableSequence[str]] = {}
            for line in outcome.value.stdout.splitlines():
                prefix, separator, _ = line.partition(":")
                target = targets.get(Path(prefix).name)
                if separator and target is not None:
                    grouped.setdefault(target, []).append(line)
            found: MutableSequence[p.Infra.AuditIssue] = []
            for rel, index, _ in documents:
                lines = grouped.get((rel, index))
                if lines:
                    found.append(
                        m.Infra.AuditIssue(
                            file=rel,
                            issue_type="python_codeblock",
                            severity="medium",
                            message=f"block #{index}: " + "\n".join(lines),
                        ),
                    )
            if outcome.value.stderr and not found:
                return FlextInfraUtilitiesDocsAuditDetectors._codeblock_failure(
                    documents,
                    outcome.value.stderr.strip(),
                )
            if (
                not found
                and not u.Cli.process_succeeded(outcome.value.outcome)
                and not outcome.value.stderr
            ):
                return FlextInfraUtilitiesDocsAuditDetectors._codeblock_failure(
                    documents,
                    f"ruff exit {outcome.value.outcome.raw_return_code}",
                )
            return found

    @staticmethod
    def _codeblock_failure(
        documents: Sequence[tuple[str, int, bytes]],
        detail: str,
    ) -> Sequence[p.Infra.AuditIssue]:
        """Report one native invocation failure against every captured fence.

        Returns:
            The resulting ``Sequence[p.Infra.AuditIssue]``.

        """
        return [
            m.Infra.AuditIssue(
                file=rel,
                issue_type="python_codeblock",
                severity="medium",
                message=f"block #{index}: {detail}",
            )
            for rel, index, _ in documents
        ]


__all__: list[str] = ["FlextInfraUtilitiesDocsAuditDetectors"]
