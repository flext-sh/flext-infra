"""Workspace root Makefile generator.

Manages the root ``Makefile`` in a FLEXT workspace.  The file is
100% generated from a Jinja2 template stored inside ``flext_infra``.
Custom workspace targets go in ``workspace_custom.mk`` (auto-included).

Bootstrap flow (first run, no template yet):
  - Reads the current ``Makefile`` and registers it as the canonical template.
  - Adds ``@generated`` header and ``-include workspace_custom.mk``.
  - Parameterises ``PR_BRANCH`` from the current git branch.

Subsequent runs:
  - Reads the stored template, renders ``{{ pr_branch }}``.
  - SHA-256 idempotency skips writes when content is unchanged.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_core import r
from flext_infra import c, p, u
from flext_infra.workspace._workspace_makefile_template import (
    FlextInfraWorkspaceMakefileTemplateMixin,
)

if TYPE_CHECKING:
    from pathlib import Path


class FlextInfraWorkspaceMakefileGenerator(FlextInfraWorkspaceMakefileTemplateMixin):
    """Generate and keep the workspace root Makefile in sync with flext_infra.

    The canonical source of truth is
    ``flext_infra/templates/workspace_makefile.mk.j2``.  Edit that file
    to change workspace-level verbs; then run ``make sync`` to propagate.
    """

    def generate(self, workspace_root: Path, *, apply: bool = True) -> p.Result[bool]:
        """Regenerate the workspace root Makefile from the stored template.

        Args:
            workspace_root: Path to the workspace root (contains Makefile).
            apply: If True, write the Makefile; otherwise only report whether
                it would change.

        Returns:
            r with True if Makefile was written, False if unchanged,
            failure on I/O error.

        """
        makefile = workspace_root / c.Infra.MAKEFILE_FILENAME

        if not self.template_path.exists():
            return self._bootstrap_template(makefile, apply=apply)

        pr_branch = self._current_branch(workspace_root)
        render_result = self._render_template(pr_branch=pr_branch)
        if render_result.failure:
            return r[bool].fail(render_result.error or "template render failed")
        content = render_result.value

        if makefile.exists():
            read = u.Cli.files_read_text(makefile)
            if read.failure:
                return r[bool].fail(read.error or "Makefile read failed")
            if u.Cli.sha256_content(read.value) == u.Cli.sha256_content(content):
                return r[bool].ok(False)

        if not apply:
            return r[bool].ok(True)
        return u.Cli.atomic_write_text_file(makefile, content)

    def _bootstrap_template(self, makefile: Path, *, apply: bool) -> p.Result[bool]:
        """Create the template from the current Makefile (one-time bootstrap)."""
        result: p.Result[bool]
        if not makefile.exists():
            result = r[bool].ok(False)
        else:
            read = u.Cli.files_read_text(makefile)
            if read.failure:
                result = r[bool].fail(read.error or "Makefile read failed")
            else:
                content = read.value
                if c.Infra.MAKEFILE_GENERATED_MARKER in content:
                    result = r[bool].ok(False)
                else:
                    pr_branch = self._current_branch(makefile.parent)
                    template_content = self._build_template_lines(content)

                    try:
                        if not apply:
                            result = r[bool].ok(True)
                            return result
                        result = self._write_bootstrap_template(
                            makefile=makefile,
                            pr_branch=pr_branch,
                            template_content=template_content,
                        )
                    except OSError as exc:
                        result = r[bool].fail_op("template bootstrap", exc)
        return result

    @staticmethod
    def _current_branch(workspace_root: Path) -> str:
        """Return the source branch, including inside a detached transaction."""
        capture_result = u.Cli.capture(
            ["git", "-C", str(workspace_root), "rev-parse", "--abbrev-ref", "HEAD"],
            timeout=5,
        )
        if capture_result.success:
            branch = capture_result.value
            if branch and branch != c.Infra.GIT_HEAD:
                return str(branch)

        # mro-wkii.17.26 (codex): resolve the branch behind a detached checkpoint.
        for revision in ("HEAD^", "HEAD"):
            refs_result = u.Cli.capture(
                [
                    "git",
                    "-C",
                    str(workspace_root),
                    "for-each-ref",
                    "--format=%(refname:short)",
                    "--points-at",
                    revision,
                    "refs/heads",
                ],
                timeout=5,
            )
            if refs_result.failure:
                continue
            branches = tuple(
                line.strip()
                for line in str(refs_result.value).splitlines()
                if line.strip()
            )
            if len(branches) == 1:
                return branches[0]
        return str(c.Infra.GIT_MAIN)


__all__: list[str] = ["FlextInfraWorkspaceMakefileGenerator"]
