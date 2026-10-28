"""Fix helpers for docs services.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

from flext_cli import u

from flext_infra import c, config, m, t
from flext_infra._utilities import FlextInfraUtilitiesDocs
from flext_infra._utilities._docs import (
    FlextInfraUtilitiesDocsContract,
    FlextInfraUtilitiesDocsGithubLinks,
)

if TYPE_CHECKING:
    from pathlib import Path


class FlextInfraUtilitiesDocsFix:
    """Reusable fix helpers exposed through ``u.Infra``."""

    @staticmethod
    def docs_maybe_fix_link(md_file: Path, raw_link: str) -> str | None:
        """Return a corrected link target when a simple fix is possible.

        Returns:
            A corrected link target when a simple fix is possible.

        """
        if FlextInfraUtilitiesDocs.docs_is_secure_web_url(raw_link):
            return FlextInfraUtilitiesDocsGithubLinks.docs_rewrite_github_url(
                raw_link,
                repository_root=md_file.parent,
            )
        result: str | None = None
        if not (
            FlextInfraUtilitiesDocs.docs_is_external(raw_link)
            or raw_link.startswith(c.Infra.DOCS_FRAGMENT_PREFIX)
        ):
            base = raw_link.split("#", maxsplit=1)[0]
            if (
                base
                and not (md_file.parent / base).exists()
                and not base.endswith(".md")
            ):
                md_candidate = md_file.parent / f"{base}.md"
                if md_candidate.exists():
                    result = f"{base}.md{raw_link[len(base) :]}"
        return result

    @staticmethod
    def docs_fix_python_codeblocks(
        scope: m.Infra.DocScope,
        *,
        path: Path,
        content: str,
    ) -> str:
        """Plan fenced-code lint repairs against one captured Markdown source.

        Apply only fixes that ``ruff`` resolves completely. An unfixable
        diagnostic fails this phase with the original process detail so the
        authored Markdown can be corrected before publication.

        Returns:
            Repaired source bytes without publishing the source file.

        Raises:
            RuntimeError: If ruff cannot fix or verify a fenced block.

        """
        rel = path.relative_to(scope.path).as_posix()
        common = (
            sys.executable,
            "-m",
            c.Infra.RUFF,
            c.Infra.VERB_CHECK,
            "--extend-ignore",
            ",".join(c.Infra.PYTHON_FENCE_RUFF_EXTEND_IGNORE),
            "--stdin-filename",
            f"{rel}#block.py",
            "-",
        )
        replacements: t.MutableMappingKV[m.Cli.MarkdownFence, t.StrPair] = {}
        for fence in filter(
            FlextInfraUtilitiesDocs.docs_is_python_fence,
            u.Cli.markdown_fences(content),
        ):
            fixed = u.Cli.run_raw(
                (*common, *config.Infra.codegen.make.ruff.lint_fix),
                cwd=scope.path,
                options=m.Cli.ProcessOptions(input_data=fence.code.encode()),
            ).unwrap()
            if not u.Cli.process_succeeded(fixed.outcome):
                msg = f"Ruff could not fix {rel}: {fixed.stdout}\n{fixed.stderr}"
                raise RuntimeError(msg)
            verified = u.Cli.run_raw(
                (*common, *config.Infra.codegen.make.ruff.lint_check),
                cwd=scope.path,
                options=m.Cli.ProcessOptions(input_data=fixed.stdout.encode()),
            ).unwrap()
            if not u.Cli.process_succeeded(verified.outcome) or verified.stderr:
                msg = (
                    f"Ruff could not verify {rel}: {verified.stdout}\n{verified.stderr}"
                )
                raise RuntimeError(msg)
            if fixed.stdout != fence.code:
                replacements[fence] = (fence.info, fixed.stdout)
        return u.Cli.markdown_rewrite_fences(content, replacements)

    @staticmethod
    def docs_rewrite_bare_notest(content: str, info_format: str) -> t.Pair[str, int]:
        """Rewrite every bare ``<lang> notest`` fence info through one format.

        ``pymdownx.superfences`` rejects the bare second token and leaks the
        block as prose; authored docs take the ``attr_list`` form and generated
        docs drop the marker.

        Returns:
            The rewritten document and the number of rewritten fences.

        """
        replacements = {
            fence: (info_format.format(language), fence.code)
            for fence in u.Cli.markdown_fences(content)
            for language, _, marker in (fence.info.partition(" "),)
            if marker.strip() == c.Infra.MARKDOWN_CODE_SKIP_MARKER
            and not language.startswith("{")
        }
        return (
            u.Cli.markdown_rewrite_fences(content, replacements),
            len(replacements),
        )

    @staticmethod
    def docs_process_markdown_file(
        md_file: Path,
        *,
        content: str,
    ) -> t.Pair[str, m.Infra.DocsPhaseItemModel]:
        """Plan link, fence and TOC repairs without reading or writing the file.

        Returns:
            The repaired source and its existing phase item summary.

        """
        updated, link_count = u.Cli.markdown_rewrite_link_targets(
            content,
            lambda link: FlextInfraUtilitiesDocsFix.docs_maybe_fix_link(
                md_file,
                link.target,
            ),
        )
        updated, fence_count = FlextInfraUtilitiesDocsFix.docs_rewrite_bare_notest(
            updated,
            c.Infra.DOCS_NOTEST_ATTR_INFO_FORMAT,
        )
        updated, toc_changed = FlextInfraUtilitiesDocsContract.docs_contract_update_toc(
            updated,
        )
        return (
            updated,
            m.Infra.DocsPhaseItemModel(
                phase="fix",
                file=md_file.as_posix(),
                links=link_count + fence_count,
                toc=toc_changed,
            ),
        )

    @staticmethod
    def docs_write_fix_reports(
        scope: m.Infra.DocScope,
        *,
        items: t.SequenceOf[m.Infra.DocsPhaseItemModel],
        apply: bool,
    ) -> None:
        """Persist the standard fix summary and markdown report."""
        FlextInfraUtilitiesDocs.docs_write_phase_reports(
            scope,
            phase="fix",
            table=m.Cli.TableRenderRequest(
                title="Docs Fix Report",
                columns=("file", "link_fixes", "toc_updates"),
                rows=tuple(
                    (item.file, str(item.links), str(item.toc)) for item in items
                ),
            ),
            apply=apply,
        )


__all__: list[str] = ["FlextInfraUtilitiesDocsFix"]
