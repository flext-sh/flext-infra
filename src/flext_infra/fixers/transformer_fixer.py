"""Transformer-based fix adapter for enforcement rules with syntactic rewrites.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from typing import ClassVar, override

from flext_core._models.enforcement import FlextModelsEnforcement as me
from flext_infra.fixers.base import FlextInfraFixerAdapter
from flext_infra.fixers.result import FlextInfraFixersResult as fr
from flext_infra.models import m
from flext_infra.transformers.bare_except import FlextInfraRefactorBareExcept
from flext_infra.transformers.base import FlextInfraRopeTransformer
from flext_infra.transformers.future_import import FlextInfraRefactorFutureImport
from flext_infra.transformers.open_encoding import FlextInfraRefactorOpenEncoding
from flext_infra.transformers.print_to_logger import FlextInfraRefactorPrintToLogger
from flext_infra.transformers.remove_breakpoint import (
    FlextInfraRefactorRemoveBreakpoint,
)
from flext_infra.transformers.typing_unifier import FlextInfraRefactorTypingUnifier
from flext_infra.typings import t
from flext_infra.utilities import u


class FlextInfraTransformerFixerAdapter(FlextInfraFixerAdapter):
    """Apply fixes by running a rope/source transformer per file.

    Targets are canonical transformer short-names declared in the enforcement
    catalog. Each transformer must expose ``apply_to_source(source) -> (str, changes)``.
    """

    kind: ClassVar[str] = "transformer"

    def __init__(self, workspace_root: Path) -> None:
        """Bind the workspace root used to resolve relative file paths."""
        super().__init__(workspace_root)

    # Canonical transformer registry. New deterministic transformers register here.
    _TRANSFORMERS: ClassVar[
        dict[
            str,
            type[FlextInfraRopeTransformer],
        ]
    ] = {
        "bare_except": FlextInfraRefactorBareExcept,
        "future_import": FlextInfraRefactorFutureImport,
        "open_encoding": FlextInfraRefactorOpenEncoding,
        "print_to_logger": FlextInfraRefactorPrintToLogger,
        "remove_breakpoint": FlextInfraRefactorRemoveBreakpoint,
        "typing_unifier": FlextInfraRefactorTypingUnifier,
    }

    @override
    def can_fix(
        self,
        fix_action: me.EnforcementFixAction,
    ) -> bool:
        """Return whether this adapter handles ``fix_action``."""
        return fix_action.kind == self.kind

    @override
    def fix_project(
        self,
        project_dir: Path,
        violations: t.SequenceOf[tuple[me.EnforcementRuleSpec, t.AttributeProbe]],
        ctx: m.Infra.FixEnforcementCommand,
    ) -> fr.ProjectFixResult:
        """Apply transformer fixes file-by-file for the given violations."""
        if not violations:
            return fr.ProjectFixResult(project=project_dir.name)
        rule, _probe = violations[0]
        fix_action = rule.fix_action
        if fix_action is None:
            return fr.ProjectFixResult(project=project_dir.name)
        transformer_cls = self._TRANSFORMERS.get(fix_action.target)
        if transformer_cls is None:
            return fr.ProjectFixResult(
                project=project_dir.name,
                failed=(
                    fr.FailedFix(
                        rule_id=rule.id,
                        file_path=str(project_dir),
                        error=f"transformer {fix_action.target} not registered",
                    ),
                ),
            )
        fixed: list[fr.FixedViolation] = []
        skipped: list[fr.SkippedViolation] = []
        failed: list[fr.FailedFix] = []
        files_modified: set[str] = set()
        file_paths = self._collect_file_paths(violations, project_dir)
        for file_path in file_paths:
            result = self._fix_file(
                file_path=file_path,
                transformer_cls=transformer_cls,
                fix_action=fix_action,
                ctx=ctx,
            )
            fixed.extend(result.fixed)
            skipped.extend(result.skipped)
            failed.extend(result.failed)
            files_modified.update(result.files_modified)
        return fr.ProjectFixResult(
            project=project_dir.name,
            fixed=tuple(fixed),
            skipped=tuple(skipped),
            failed=tuple(failed),
            files_modified=tuple(files_modified),
        )

    def _fix_file(
        self,
        file_path: Path,
        transformer_cls: type[FlextInfraRopeTransformer],
        fix_action: me.EnforcementFixAction,
        ctx: m.Infra.FixEnforcementCommand,
    ) -> fr.ProjectFixResult:
        """Run one transformer against one file."""
        read = u.Cli.files_read_text(file_path)
        if read.failure:
            return fr.ProjectFixResult(
                project=file_path.parent.name,
                failed=(
                    fr.FailedFix(
                        rule_id="",
                        file_path=str(file_path),
                        error=read.error or "unable to read file",
                    ),
                ),
            )
        source = read.value
        transformer = self._build_transformer(
            transformer_cls=transformer_cls,
            fix_action=fix_action,
            file_path=file_path,
        )
        updated, changes = transformer.apply_to_source(source)
        if not changes:
            return fr.ProjectFixResult(
                project=file_path.parent.name,
                skipped=(
                    fr.SkippedViolation(
                        rule_id="",
                        file_path=str(file_path),
                        reason="no changes produced",
                    ),
                ),
            )
        if ctx.dry_run:
            return fr.ProjectFixResult(
                project=file_path.parent.name,
                fixed=(
                    fr.FixedViolation(
                        rule_id="",
                        file_path=str(file_path),
                        message=f"would apply {len(changes)} change(s)",
                    ),
                ),
            )
        write = u.Cli.files_write_text(file_path, updated)
        if write.failure:
            return fr.ProjectFixResult(
                project=file_path.parent.name,
                failed=(
                    fr.FailedFix(
                        rule_id="",
                        file_path=str(file_path),
                        error=write.error or "unable to write file",
                    ),
                ),
            )
        return fr.ProjectFixResult(
            project=file_path.parent.name,
            fixed=(
                fr.FixedViolation(
                    rule_id="",
                    file_path=str(file_path),
                    message=f"applied {len(changes)} change(s)",
                ),
            ),
            files_modified=(str(file_path),),
        )

    @staticmethod
    def _build_transformer(
        transformer_cls: type[FlextInfraRopeTransformer],
        fix_action: me.EnforcementFixAction,
        file_path: Path,
    ) -> FlextInfraRopeTransformer:
        """Instantiate a transformer with params declared in the catalog."""
        params = dict(fix_action.params)
        if transformer_cls is FlextInfraRefactorTypingUnifier:
            targets_value = params.get("targets", [])
            targets: t.StrSequence = (
                targets_value if isinstance(targets_value, (list, tuple)) else []
            )
            canonical_map: dict[frozenset[str], str] = {}
            if "dict" in targets:
                canonical_map[frozenset({"dict[K, V]"})] = "t.MappingKV[K, V]"
                canonical_map[frozenset({"dict[str, Any]"})] = (
                    "t.MappingKV[str, t.JsonValue]"
                )
            return FlextInfraRefactorTypingUnifier(
                canonical_map=canonical_map,
                file_path=file_path,
            )
        if transformer_cls is FlextInfraRefactorPrintToLogger:
            return FlextInfraRefactorPrintToLogger(file_path=file_path)
        # Remaining enforcement transformers require no runtime params.
        return transformer_cls()

    @staticmethod
    def _collect_file_paths(
        violations: t.SequenceOf[tuple[me.EnforcementRuleSpec, t.AttributeProbe]],
        project_dir: Path,
    ) -> tuple[Path, ...]:
        """Extract unique file paths from violation probes."""
        seen: set[Path] = set()
        paths: list[Path] = []
        for _rule, probe in violations:
            raw = getattr(probe, "file_path", None) or getattr(probe, "file", "")
            if not raw:
                continue
            path = Path(raw)
            if not path.is_absolute():
                path = project_dir / path
            path = path.resolve()
            if path not in seen and path.is_file():
                seen.add(path)
                paths.append(path)
        return tuple(paths)


__all__: list[str] = ["FlextInfraTransformerFixerAdapter"]
