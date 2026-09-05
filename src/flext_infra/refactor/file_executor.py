"""Direct file-rule execution through the public Rope workspace."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c, m, u
from flext_infra.transformers.class_nesting import (
    FlextInfraRefactorClassNestingTransformer,
)
from flext_infra.transformers.nested_class_propagation import (
    FlextInfraNestedClassPropagationTransformer,
)

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import p, t


class FlextInfraRefactorFileExecutor:
    """Execute semantic file rules selected by the refactor service."""

    def _apply_file_rule_selection(
        self,
        kind: c.Infra.RefactorFileRuleKind,
        _settings: t.MappingKV[str, t.Infra.InfraValue],
        rope_workspace: p.Infra.RopeWorkspaceDsl,
        file_path: Path,
    ) -> m.Infra.Result:
        """Apply one supported semantic file rule in memory."""
        _ = kind
        source = rope_workspace.source(file_path)
        violations = u.Infra.class_nesting_plan(rope_workspace, file_path).unwrap()
        class_map = {
            violation.class_name: violation.target_namespace for violation in violations
        }
        changes: list[str] = []
        updated = source
        if class_map:
            nesting = FlextInfraRefactorClassNestingTransformer(class_map)
            updated, nesting_changes = nesting.apply_to_source(
                updated, existing_names=set(class_map) | set(class_map.values())
            )
            changes.extend(nesting_changes)
            propagation = FlextInfraNestedClassPropagationTransformer({
                name: f"{target}.{name}" for name, target in class_map.items()
            })
            updated, propagation_changes = propagation.apply_to_source(updated)
            changes.extend(propagation_changes)
        return m.Infra.Result(
            file_path=file_path,
            success=True,
            modified=updated != source,
            changes=changes,
            refactored_code=updated,
        )


__all__: list[str] = ["FlextInfraRefactorFileExecutor"]
