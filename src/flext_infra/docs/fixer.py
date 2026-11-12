"""Documentation fixer service.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import override

from flext_infra import c, m, p, r, u
from flext_infra.docs import FlextInfraDocGenerator, FlextInfraDocServiceBase


class FlextInfraDocFixer(FlextInfraDocServiceBase):
    """Fix links and TOCs across governed FLEXT docs scopes."""

    def fix(
        self,
        repository_root: Path,
        *,
        projects: Sequence[str] | None = None,
        output_dir: Path | None = None,
        apply: bool = False,
    ) -> p.Result[Sequence[p.Infra.DocsPhaseReport]]:
        """Run documentation fixes across project scopes.

        Returns:
            The resulting ``p.Result[Sequence[p.Infra.DocsPhaseReport]]``.

        Raises:
            ValueError: When a managed merge-policy file owns a selected path or a
                planned repair carries no proposed bytes.

        """
        root = repository_root.expanduser().absolute()
        prepared = FlextInfraDocGenerator(
            repository_root=root,
            selected_projects=projects,
            output_dir=output_dir,
        ).prepare_bundle()
        if prepared.failure:
            return r[Sequence[p.Infra.DocsPhaseReport]].from_failure(prepared)
        bundle = prepared.value
        elected: list[
            tuple[
                p.Infra.DocScope,
                tuple[p.Cli.AtomicFileState, ...],
            ]
        ] = []
        # Every ownership boundary is checked before the first repair effect.
        for scoped in bundle.scopes:
            scope = scoped.scope
            loaded = u.Infra.load_codegen_inputs(scope.repository_root).unwrap()
            selected = u.Infra.iter_scope_markdown_files(scope)
            managed = {
                scope.repository_root / item.path: item
                for item in loaded.spec.managed_file_specs
            }
            generated = {
                scope.path / artifact.relative_path for artifact in scoped.artifacts
            }
            for path in selected:
                ownership = managed.get(path)
                if ownership is not None and ownership.policy == "merge":
                    msg = (
                        f"authored docs repair requires a Markdown region "
                        f"compositor for {path}; declared owner={ownership.owner}"
                    )
                    raise ValueError(msg)
            elected.append((
                scope,
                tuple(
                    u.Cli.atomic_read_binary_file_state(path, required=True).unwrap()
                    for path in selected
                    if path not in generated and path not in managed
                ),
            ))
        plans = tuple(
            (scope, *self._plan_scope(scope, sources)) for scope, sources in elected
        )
        # Planning is read-only; the whole repair publishes as one verified batch,
        # so the mutation lock covers the effect and never the computation.
        changes = tuple(
            m.Cli.FileChange(
                path=file.path,
                before=file.before,
                desired_content=file.desired_content,
                desired_mode=(
                    file.desired_mode
                    if file.desired_mode is not None
                    else c.Infra.CONFIG_SPEC[1]
                ),
            )
            for _scope, files, _items in plans
            for file in files
            if apply and file.desired_content is not None
        )
        for _scope, files, _items in plans:
            for file in files:
                if apply and file.desired_content is None:
                    msg = f"docs repair has no proposed bytes: {file.path}"
                    raise ValueError(msg)
        if changes:
            u.Cli.publish_file_changes(
                changes,
                lock_path=u.Infra.mutation_lock_path(root).unwrap(),
            ).unwrap()
        reports = tuple(
            self._scope_report(scope, items, apply=apply)
            for scope, _files, items in plans
        )
        return r[Sequence[p.Infra.DocsPhaseReport]].ok(reports)

    @override
    def execute(self) -> p.Result[bool]:
        """Execute the configured docs fix flow.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        return self._propagate_phase_outcome(
            "fix",
            self.fix(
                repository_root=self.repository_root,
                projects=self.selected_projects,
                output_dir=self.output_dir,
                apply=self.apply_changes,
            ),
            failure_predicate=lambda report: not report.passed,
        )

    @staticmethod
    def _plan_scope(
        scope: p.Infra.DocScope,
        sources: Sequence[p.Cli.AtomicFileState],
    ) -> tuple[
        tuple[p.Infra.SemanticFilePlan, ...],
        tuple[p.Infra.DocsPhaseItemModel, ...],
    ]:
        """Compose authored repairs against read bytes without publication.

        Returns:
            The planned file repairs and their phase items.

        Raises:
            FileNotFoundError: When a selected source has no content.

        """
        planned: list[p.Infra.SemanticFilePlan] = []
        collected: list[p.Infra.DocsPhaseItemModel] = []
        for before in sources:
            if before.content is None:
                raise FileNotFoundError(before.path)
            original = before.content.decode(c.DEFAULT_ENCODING)
            updated, item = u.Infra.docs_process_markdown_file(
                before.path, content=original
            )
            fixed = u.Infra.fix_python_codeblocks(
                scope, path=before.path, content=updated
            )
            final, toc_changed = (
                u.Infra.contract_update_toc(fixed) if fixed != updated else (updated, 0)
            )
            if final.encode(c.DEFAULT_ENCODING) == before.content:
                continue
            planned.append(
                m.Infra.SemanticFilePlan.model_validate({
                    "project": (scope.path),
                    "path": (before.path),
                    "before": (before),
                    "desired_content": (final.encode(c.DEFAULT_ENCODING)),
                    "desired_mode": (before.mode),
                })
            )
            collected.append(
                item.model_copy(
                    update={
                        "file": before.path.relative_to(scope.path).as_posix(),
                        "toc": int(bool(item.toc or toc_changed)),
                        "codeblocks": int(fixed != updated),
                    }
                )
            )
        return tuple(planned), tuple(collected)

    def _scope_report(
        self,
        scope: p.Infra.DocScope,
        items: Sequence[p.Infra.DocsPhaseItemModel],
        *,
        apply: bool,
    ) -> p.Infra.DocsPhaseReport:
        """Report the existing authored repair semantics after publication.

        Returns:
            The resulting ``m.Infra.DocsPhaseReport``.

        """
        u.Infra.docs_write_fix_reports(scope, items=items, apply=apply)
        report = m.Infra.DocsPhaseReport.model_validate({
            "phase": "fix",
            "scope": scope.name,
            "changed_files": len(items),
            "applied": apply,
            "items": tuple(items),
            "result": (
                c.Infra.ResultStatus.OK
                if apply or not items
                else c.Infra.ResultStatus.FAIL
            ),
            "reason": f"changes:{len(items)}",
            "passed": apply or not items,
        })
        self.logger.info(
            "fix_scope_completed",
            project=scope.name,
            phase="fix",
            result=report.result,
            reason=report.reason,
        )
        return report


__all__: list[str] = ["FlextInfraDocFixer"]
