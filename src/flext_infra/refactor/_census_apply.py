"""Census fix application + post-apply regeneration — extracted concern."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import TYPE_CHECKING

from flext_infra import c, m, p, t, u
from flext_infra.codegen.lazy_init import FlextInfraCodegenLazyInit
from flext_infra.detectors.compatibility_alias_detector import (
    FlextInfraCompatibilityAliasDetector,
)
from flext_infra.detectors.manual_typing_alias_detector import (
    FlextInfraManualTypingAliasDetector,
)
from flext_infra.detectors.mro_completeness_detector import (
    FlextInfraMROCompletenessDetector,
)

_log = u.fetch_logger(__name__)


class FlextInfraRefactorCensusApplyMixin:
    """Apply supported auto-fixes + removal candidates, then regenerate inits.

    Composed into FlextInfraRefactorCensus via inheritance; borrows the
    detector-context / fix-key / runtime-alias-rewrite helpers + root +
    dry_run_gate_names from the facade and sibling mixins via MRO.
    """

    if TYPE_CHECKING:

        @property
        def root(self) -> Path: ...

        @property
        def dry_run_gate_names(self) -> t.StrSequence: ...
        @staticmethod
        def _detector_context(
            rope: p.Infra.RopeWorkspaceDsl,
            file_path: Path,
            *,
            convention: m.Infra.RopeModuleConvention | None = None,
            parse_failures: t.MutableSequenceOf[m.Infra.ParseFailureViolation]
            | None = None,
        ) -> m.Infra.DetectorContext: ...
        @staticmethod
        def _fix_key(file_path: Path, object_name: str, action: str = "") -> str: ...
        @staticmethod
        def _rewrite_runtime_alias_source(
            source: str, *, alias: str, target_name: str
        ) -> str: ...

    def _apply_supported_fixes(
        self,
        rope: p.Infra.RopeWorkspaceDsl,
        report: m.Infra.Census.WorkspaceReport,
    ) -> frozenset[str]:
        """Apply supported fixes."""
        applied: set[str] = set()
        touched_paths: set[Path] = set()
        requested_fixes: dict[tuple[Path, str], set[str]] = defaultdict(set)
        for project in report.projects:
            for fix in project.fixes:
                requested_fixes[Path(fix.source_file), fix.action].add(fix.object_name)
        for (file_path, action), object_names in requested_fixes.items():
            parse_failures: list[m.Infra.ParseFailureViolation] = []
            ctx = self._detector_context(rope, file_path, parse_failures=parse_failures)
            changed = False
            if action == "rewrite_runtime_alias":
                convention = rope.convention(file_path)
                alias = convention.module_policy.expected_alias or ""
                target_name = next(iter(sorted(object_names)), "")
                if not alias or not target_name:
                    continue
                source = rope.source(file_path)
                updated = self._rewrite_runtime_alias_source(
                    source,
                    alias=alias,
                    target_name=target_name,
                )
                if updated == source:
                    continue
                resource = rope.resource(file_path)
                if resource is None:
                    continue
                resource.write(updated)
                changed = True
            elif action == "rewrite_manual_typing_alias":
                if ctx.project_root is None:
                    continue
                violations = tuple(
                    violation
                    for violation in FlextInfraManualTypingAliasDetector.detect_file(
                        ctx
                    )
                    if violation.name in object_names
                )
                if not violations:
                    continue
                u.Infra.rewrite_manual_typing_alias_violations(
                    project_root=ctx.project_root,
                    violations=violations,
                    parse_failures=parse_failures,
                )
                changed = True
            elif action == "rewrite_compatibility_alias":
                violations = tuple(
                    violation
                    for violation in FlextInfraCompatibilityAliasDetector.detect_file(
                        ctx,
                    )
                    if violation.alias_name in object_names
                )
                if not violations:
                    continue
                u.Infra.rewrite_compatibility_alias_violations(
                    violations=violations,
                    parse_failures=parse_failures,
                )
                changed = True
            elif action == "rewrite_mro_completeness":
                violations = tuple(
                    violation
                    for violation in FlextInfraMROCompletenessDetector.detect_file(ctx)
                    if violation.facade_class in object_names
                )
                if not violations:
                    continue
                u.Infra.rewrite_mro_completeness_violations(
                    violations=violations,
                    parse_failures=parse_failures,
                )
                changed = True
            if not changed:
                continue
            touched_paths.add(file_path.resolve())
            applied.update(
                self._fix_key(file_path, object_name, action)
                for object_name in object_names
            )
        for candidate in report.removal_candidates:
            apply_result = u.Infra.apply_simple_removal_candidate(
                rope,
                self.root,
                candidate,
                gates=self.dry_run_gate_names,
            )
            if apply_result.failure:
                msg = apply_result.error or (
                    "simple removal apply failed for "
                    f"{candidate.file_path}:{candidate.line} {candidate.object_name}"
                )
                raise RuntimeError(msg)
            if apply_result.unwrap_or(False):
                applied.add(
                    self._fix_key(Path(candidate.file_path), candidate.object_name)
                )
                touched_paths.add(Path(candidate.file_path).resolve())
                touched_paths.update(
                    Path(site.file_path).resolve()
                    for site in (
                        *candidate.test_reference_sites,
                        *candidate.example_reference_sites,
                        *candidate.script_reference_sites,
                    )
                )
        if applied:
            self._regenerate_inits_via_codegen()
            self._ruff_fix_touched_files(touched_paths)
            rope.reload()
        return frozenset(applied)

    @staticmethod
    def _ruff_fix_touched_files(paths: Iterable[Path]) -> None:
        """Normalize trailing newlines + import sort on touched files.

        Scope is ``--select I,W`` only (not ``F``/``E``) so unused-import removal
        does not fight the lazy-init ``TYPE_CHECKING`` re-exports; failures are
        logged via the ``r[T]`` channel, never suppressed.
        """
        existing = sorted({str(path) for path in paths if path.is_file()})
        if not existing:
            return
        check_result = u.Cli.run_raw(
            ["ruff", "check", "--fix", "--select", "I,W", *existing],
            timeout=c.Infra.TIMEOUT_SHORT,
        )
        if check_result.failure:
            _log.warning(
                "ruff_check_fix_cosmetic_failed",
                error=check_result.error or "ruff check --fix failed",
                files=len(existing),
            )
        format_result = u.Cli.run_raw(
            ["ruff", "format", *existing],
            timeout=c.Infra.TIMEOUT_SHORT,
        )
        if format_result.failure:
            _log.warning(
                "ruff_format_cosmetic_failed",
                error=format_result.error or "ruff format failed",
                files=len(existing),
            )

    def _regenerate_inits_via_codegen(self) -> None:
        """Regenerate every ``__init__.py`` via the canonical lazy-init service."""
        FlextInfraCodegenLazyInit(workspace=self.root).generate_inits(
            check_only=False,
        )


__all__: list[str] = ["FlextInfraRefactorCensusApplyMixin"]
