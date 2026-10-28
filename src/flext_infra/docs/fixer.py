"""Documentation fixer service.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import Sequence
from pathlib import Path
from typing import TYPE_CHECKING, override

from flext_infra import c, m, r, u
from flext_infra.docs import FlextInfraDocGenerator, FlextInfraDocServiceBase

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraDocFixer(FlextInfraDocServiceBase):
    """Fix links and TOCs across governed FLEXT docs scopes."""

    def fix(
        self,
        repository_root: Path,
        *,
        projects: Sequence[str] | None = None,
        output_dir: Path | None = None,
        apply: bool = False,
    ) -> p.Result[Sequence[m.Infra.DocsPhaseReport]]:
        """Run documentation fixes across project scopes.

        Returns:
            The resulting ``p.Result[Sequence[m.Infra.DocsPhaseReport]]``.

        Raises:
            ValueError: When a managed merge-policy file owns a selected path or a
                planned repair carries no proposed bytes.

        """
        root = repository_root.expanduser().absolute()
        with u.Cli.file_changes_lock(u.Infra.mutation_lock_path(root).unwrap()):
            prepared = FlextInfraDocGenerator(
                repository_root=root,
                selected_projects=projects,
                output_dir=output_dir,
            ).prepare_bundle()
            if prepared.failure:
                return r[Sequence[m.Infra.DocsPhaseReport]].from_failure(prepared)
            bundle = prepared.value
            elected: list[
                tuple[
                    m.Infra.DocScope,
                    tuple[m.Cli.AtomicFileState, ...],
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
                        u.Cli.atomic_read_binary_file_state(
                            path, required=True
                        ).unwrap()
                        for path in selected
                        if path not in generated and path not in managed
                    ),
                ))
            plans = tuple(
                (scope, *self._plan_scope(scope, sources)) for scope, sources in elected
            )
            reports: list[m.Infra.DocsPhaseReport] = []
            for scope, files, items in plans:
                for file in files:
                    if apply:
                        if file.desired_content is None:
                            msg = f"docs repair has no proposed bytes: {file.path}"
                            raise ValueError(msg)
                        u.Cli.atomic_write_binary_file_guarded(
                            file.before,
                            file.desired_content,
                            permission_mode=file.desired_mode,
                        ).unwrap()
                reports.append(self._scope_report(scope, items, apply=apply))
            return r[Sequence[m.Infra.DocsPhaseReport]].ok(tuple(reports))

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
        scope: m.Infra.DocScope,
        sources: Sequence[m.Cli.AtomicFileState],
    ) -> tuple[
        tuple[m.Infra.SemanticFilePlan, ...],
        tuple[m.Infra.DocsPhaseItemModel, ...],
    ]:
        """Compose authored repairs against read bytes without publication.

        Returns:
            The planned file repairs and their phase items.

        Raises:
            FileNotFoundError: When a selected source has no content.

        """
        planned: list[m.Infra.SemanticFilePlan] = []
        collected: list[m.Infra.DocsPhaseItemModel] = []
        for before in sources:
            if before.content is None:
                raise FileNotFoundError(before.path)
            original = before.content.decode(c.DEFAULT_ENCODING)
            updated, item = u.Infra.docs_process_markdown_file(
                before.path, content=original
            )
            fixed = u.Infra.docs_fix_python_codeblocks(
                scope, path=before.path, content=updated
            )
            final, toc_changed = (
                u.Infra.docs_contract_update_toc(fixed)
                if fixed != updated
                else (updated, 0)
            )
            if final.encode(c.DEFAULT_ENCODING) == before.content:
                continue
            planned.append(
                m.Infra.SemanticFilePlan(
                    project=scope.path,
                    path=before.path,
                    before=before,
                    desired_content=final.encode(c.DEFAULT_ENCODING),
                    desired_mode=before.mode,
                )
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
        scope: m.Infra.DocScope,
        items: Sequence[m.Infra.DocsPhaseItemModel],
        *,
        apply: bool,
    ) -> m.Infra.DocsPhaseReport:
        """Report the existing authored repair semantics after publication.

        Returns:
            The resulting ``m.Infra.DocsPhaseReport``.

        """
        u.Infra.docs_write_fix_reports(scope, items=items, apply=apply)
        report = m.Infra.DocsPhaseReport(
            phase="fix",
            scope=scope.name,
            changed_files=len(items),
            applied=apply,
            items=tuple(items),
            result=(
                c.Infra.ResultStatus.OK
                if apply or not items
                else c.Infra.ResultStatus.FAIL
            ),
            reason=f"changes:{len(items)}",
            passed=apply or not items,
        )
        self.logger.info(
            "docs_fix_scope_completed",
            project=scope.name,
            phase="fix",
            result=report.result,
            reason=report.reason,
        )
        return report


__all__: list[str] = ["FlextInfraDocFixer"]
