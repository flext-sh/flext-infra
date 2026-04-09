"""Pattern correction rules for high-volume violations."""

from __future__ import annotations

from collections.abc import Mapping

from flext_infra import (
    c,
    t,
    u,
)
from flext_infra._utilities.rope_source import FlextInfraUtilitiesRopeSource


class FlextInfraRefactorPatternCorrectionsRule:
    """Apply corrective refactors for high-volume pattern violations."""

    def __init__(self, config: Mapping[str, t.Infra.InfraValue]) -> None:
        """Initialize rule metadata from rule config."""
        self.config = dict(config)

    def apply(
        self,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        *,
        dry_run: bool = False,
    ) -> t.Infra.TransformResult:
        """Apply configured pattern corrections to resource."""
        source = FlextInfraUtilitiesRopeSource.read_source(resource)
        fix_action = u.Infra.get_str_key(
            self.config,
            c.Infra.ReportKeys.FIX_ACTION,
            case="lower",
        )
        if fix_action == "convert_dict_to_mapping_annotations":
            include_returns = bool(
                self.config.get("include_return_annotations", False),
            )
            replacements: t.StrMapping = {
                "dict[": "Mapping[",
                "Dict[": "Mapping[",
            }
            if include_returns:
                replacements = dict(replacements)
            new_source, count = FlextInfraUtilitiesRopeSource.batch_replace_annotations(
                rope_project,
                resource,
                replacements,
                apply=not dry_run,
            )
            if count > 0:
                return (
                    new_source,
                    [f"Converted {count} dict annotations to Mapping"],
                )
            return (source, [])
        if fix_action == "remove_redundant_casts":
            raw_types = self.config.get("redundant_type_targets", [])
            removable_types = set(u.Infra.string_list(raw_types))
            new_source, count = FlextInfraUtilitiesRopeSource.remove_redundant_cast(
                rope_project,
                resource,
                apply=not dry_run,
            )
            if count > 0 and removable_types:
                return (
                    new_source,
                    [f"Removed {count} redundant cast() calls"],
                )
            return (source, [])
        if fix_action == "fix_silent_failure_sentinels":
            new_source, changes = (
                FlextInfraUtilitiesRopeSource.fix_silent_failure_sentinels(
                    rope_project,
                    resource,
                    apply=not dry_run,
                )
            )
            return new_source, list(changes)
        return (source, [])


__all__ = ["FlextInfraRefactorPatternCorrectionsRule"]
