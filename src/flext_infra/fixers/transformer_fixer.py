"""Transformer-based fix adapter for enforcement rules with syntactic rewrites.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import ClassVar, override

from flext_core._models.enforcement import FlextModelsEnforcement as me
from flext_infra._utilities.rope_imports import FlextInfraUtilitiesRopeImports
from flext_infra.constants import c
from flext_infra.fixers.base import FlextInfraFixerAdapter
from flext_infra.fixers.result import FlextInfraFixersResult as fr
from flext_infra.models import m
from flext_infra.protocols import p
from flext_infra.transformers.base import FlextInfraRopeTransformer
from flext_infra.transformers.compatibility_alias import (
    FlextInfraRefactorCompatibilityAlias,
)
from flext_infra.transformers.future_import import FlextInfraRefactorFutureImport
from flext_infra.transformers.hardcoded_version import (
    FlextInfraRefactorHardcodedVersion,
)
from flext_infra.transformers.import_modernizer import (
    FlextInfraRefactorImportModernizer,
)
from flext_infra.transformers.mro_remover import FlextInfraRefactorMRORemover
from flext_infra.transformers.open_encoding import FlextInfraRefactorOpenEncoding
from flext_infra.transformers.pattern import FlextInfraRefactorPatternTransformer
from flext_infra.transformers.project_alias_migrator import (
    FlextInfraRefactorProjectAliasMigrator,
)
from flext_infra.transformers.typing_dict_attr import (
    FlextInfraRefactorTypingDictAttr,
)
from flext_infra.transformers.typing_dict_import import (
    FlextInfraRefactorTypingDictImport,
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
        "compatibility_alias": FlextInfraRefactorCompatibilityAlias,
        "future_import": FlextInfraRefactorFutureImport,
        "hardcoded_version": FlextInfraRefactorHardcodedVersion,
        "import_modernizer": FlextInfraRefactorImportModernizer,
        "mro_remover": FlextInfraRefactorMRORemover,
        "open_encoding": FlextInfraRefactorOpenEncoding,
        "pattern": FlextInfraRefactorPatternTransformer,
        "project_alias_migrator": FlextInfraRefactorProjectAliasMigrator,
        "rewrite_foreign_canonical_alias": FlextInfraRefactorProjectAliasMigrator,
        "typing_dict_attr": FlextInfraRefactorTypingDictAttr,
        "typing_dict_import": FlextInfraRefactorTypingDictImport,
        "typing_unifier": FlextInfraRefactorTypingUnifier,
    }

    @override
    def can_fix(
        self,
        fix_action: me.EnforcementFixAction,
    ) -> bool:
        """Return whether this adapter handles ``fix_action``."""
        return fix_action.kind == self.kind and fix_action.target in self._TRANSFORMERS

    @override
    def fix_project(
        self,
        project_dir: Path,
        violations: t.SequenceOf[tuple[me.EnforcementRuleSpec, p.AttributeProbe]],
        ctx: m.Infra.FixEnforcementCommand,
    ) -> fr.ProjectFixResult:
        """Apply transformer fixes file-by-file for the given violations."""
        if not violations:
            return fr.ProjectFixResult(project=project_dir.name)
        fixed: list[fr.FixedViolation] = []
        previewed: list[fr.PreviewedViolation] = []
        skipped: list[fr.SkippedViolation] = []
        failed: list[fr.FailedFix] = []
        files_modified: set[str] = set()
        for target, target_violations in self._group_violations_by_target(
            violations,
        ).items():
            transformer_cls = self._TRANSFORMERS.get(target)
            if transformer_cls is None:
                rule_id = target_violations[0][0].id
                failed.append(
                    fr.FailedFix(
                        rule_id=rule_id,
                        file_path=str(project_dir),
                        error=f"transformer {target} not registered",
                    ),
                )
                continue
            fix_action = target_violations[0][0].fix_action
            file_paths = self._collect_file_paths(target_violations, project_dir)
            for file_path in file_paths:
                if self._is_owned_library_exempt(project_dir, fix_action, file_path):
                    skipped.append(
                        fr.SkippedViolation(
                            rule_id=target_violations[0][0].id,
                            file_path=str(file_path),
                            reason=(
                                f"project {project_dir.name} owns library abstraction"
                            ),
                        ),
                    )
                    continue
                result = self._fix_file(
                    file_path=file_path,
                    transformer_cls=transformer_cls,
                    fix_action=fix_action,
                    ctx=ctx,
                    rule_id=target_violations[0][0].id,
                )
                fixed.extend(result.fixed)
                previewed.extend(result.previewed)
                skipped.extend(result.skipped)
                failed.extend(result.failed)
                files_modified.update(result.files_modified)
        if ctx.apply and files_modified:
            normalize_result = self._normalize_imports(tuple(files_modified))
            if normalize_result.failure:
                failed.append(
                    fr.FailedFix(
                        rule_id="",
                        file_path=str(project_dir),
                        error=normalize_result.error or "import normalization failed",
                    ),
                )
        return fr.ProjectFixResult(
            project=project_dir.name,
            fixed=tuple(fixed),
            previewed=tuple(previewed),
            skipped=tuple(skipped),
            failed=tuple(failed),
            files_modified=tuple(files_modified),
        )

    @staticmethod
    def _is_owned_library_exempt(
        project_dir: Path,
        fix_action: me.EnforcementFixAction | None,
        file_path: Path,
    ) -> bool:
        """Skip import modernization inside the library's owning project.

        Direct imports of pydantic/structlog/oracledb/ldap3 are allowed within
        the project that owns the abstraction facade; consumers must route
        through that facade.
        """
        _ = file_path
        if fix_action is None or fix_action.target != "import_modernizer":
            return False
        imports_to_remove = u.Cli.json_as_sequence(
            fix_action.params.get("imports_to_remove"),
        )
        for module in imports_to_remove:
            if not isinstance(module, str):
                continue
            owner = c.ENFORCEMENT_LIBRARY_OWNERS.get(module)
            if owner == project_dir.name:
                return True
        return False

    def _normalize_imports(
        self,
        file_paths: t.SequenceOf[str],
    ) -> p.Result[bool]:
        """Run rope+ruff import cleanup on files touched by transformers.

        Keeps canonical runtime-alias imports (c/m/p/t/u) that Ruff may consider
        unused because they are referenced inside string annotations or via
        lazy exports.
        """
        paths = tuple(Path(path) for path in file_paths)
        with u.Infra.open_project(self._workspace_root) as rope_project:
            return FlextInfraUtilitiesRopeImports.normalize_imports(
                rope_project,
                file_paths=paths,
                preserve_canonical_aliases=True,
            )

    def _fix_file(
        self,
        file_path: Path,
        transformer_cls: type[FlextInfraRopeTransformer],
        fix_action: me.EnforcementFixAction | None,
        ctx: m.Infra.FixEnforcementCommand,
        *,
        rule_id: str = "",
    ) -> fr.ProjectFixResult:
        """Run one transformer against one file."""
        if fix_action is None:
            return fr.ProjectFixResult(
                project=file_path.parent.name,
                skipped=(
                    fr.SkippedViolation(
                        rule_id=rule_id,
                        file_path=str(file_path),
                        reason="missing fix_action in catalog",
                    ),
                ),
            )
        read = u.Cli.files_read_text(file_path)
        if read.failure:
            return fr.ProjectFixResult(
                project=file_path.parent.name,
                failed=(
                    fr.FailedFix(
                        rule_id=rule_id,
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
                        rule_id=rule_id,
                        file_path=str(file_path),
                        reason="no changes produced",
                    ),
                ),
            )
        if not ctx.apply:
            return fr.ProjectFixResult(
                project=file_path.parent.name,
                previewed=(
                    fr.PreviewedViolation(
                        rule_id=rule_id,
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
                        rule_id=rule_id,
                        file_path=str(file_path),
                        error=write.error or "unable to write file",
                    ),
                ),
            )
        return fr.ProjectFixResult(
            project=file_path.parent.name,
            fixed=(
                fr.FixedViolation(
                    rule_id=rule_id,
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
                tuple(item for item in targets_value if isinstance(item, str))
                if isinstance(targets_value, (list, tuple))
                else ()
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
        if transformer_cls in {
            FlextInfraRefactorTypingDictImport,
            FlextInfraRefactorTypingDictAttr,
        }:
            return transformer_cls(file_path=file_path)
        if transformer_cls is FlextInfraRefactorProjectAliasMigrator:
            return FlextInfraRefactorProjectAliasMigrator(file_path=file_path)
        if transformer_cls is FlextInfraRefactorImportModernizer:
            imports_to_remove = tuple(
                name
                for name in u.Cli.json_as_sequence(
                    params.get("imports_to_remove"),
                )
                if isinstance(name, str)
            )
            symbols_to_replace = {
                k: str(v)
                for k, v in u.Cli.json_as_mapping(
                    params.get("symbols_to_replace"),
                ).items()
                if isinstance(k, str) and isinstance(v, (str, int, float))
            }
            runtime_aliases = {
                name
                for name in u.Cli.json_as_sequence(
                    params.get("runtime_aliases"),
                )
                if isinstance(name, str)
            }
            blocked_aliases = {
                name
                for name in u.Cli.json_as_sequence(
                    params.get("blocked_aliases"),
                )
                if isinstance(name, str)
            }
            return FlextInfraRefactorImportModernizer(
                imports_to_remove=imports_to_remove,
                symbols_to_replace=symbols_to_replace,
                runtime_aliases=runtime_aliases,
                blocked_aliases=blocked_aliases,
            )
        if transformer_cls is FlextInfraRefactorPatternTransformer:
            required_alias = params.get("required_alias", "")
            alias_module = params.get("alias_module", "")
            return FlextInfraRefactorPatternTransformer(
                patterns=u.Cli.json_as_mapping_list(params.get("patterns")),
                required_alias=required_alias
                if isinstance(required_alias, str)
                else "",
                alias_module=alias_module if isinstance(alias_module, str) else "",
                file_path=file_path,
            )
        # Remaining enforcement transformers require no runtime params.
        return transformer_cls()

    @staticmethod
    def _collect_file_paths(
        violations: t.SequenceOf[tuple[me.EnforcementRuleSpec, p.AttributeProbe]],
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

    @staticmethod
    def _group_violations_by_target(
        violations: t.SequenceOf[tuple[me.EnforcementRuleSpec, p.AttributeProbe]],
    ) -> dict[str, list[tuple[me.EnforcementRuleSpec, p.AttributeProbe]]]:
        """Group violations by the transformer target declared in ``fix_action``."""
        grouped: dict[
            str,
            list[tuple[me.EnforcementRuleSpec, p.AttributeProbe]],
        ] = defaultdict(list)
        for rule, probe in violations:
            fix_action = rule.fix_action
            if fix_action is None:
                continue
            grouped[fix_action.target].append((rule, probe))
        return grouped


__all__: list[str] = ["FlextInfraTransformerFixerAdapter"]
