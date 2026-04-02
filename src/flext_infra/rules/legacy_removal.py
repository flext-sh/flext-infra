"""Rule that removes legacy compatibility code patterns."""

from __future__ import annotations

import re
from collections.abc import Mapping, MutableSequence, Sequence

from pydantic import ValidationError

from flext_infra import (
    INFRA_MAPPING_ADAPTER,
    INFRA_SEQ_ADAPTER,
    FlextInfraUtilitiesRope,
    c,
    t,
    u,
)


class FlextInfraRefactorLegacyRemovalRule:
    """Remove aliases, deprecated classes, wrappers and import bypass blocks."""

    def __init__(self, config: Mapping[str, t.Infra.InfraValue]) -> None:
        """Initialize rule metadata from rule config."""
        self.config = dict(config)
        rule_id = self.config.get(c.Infra.ReportKeys.ID, c.Infra.Defaults.UNKNOWN)
        self.rule_id = str(rule_id)

    def apply(
        self,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        *,
        dry_run: bool = False,
    ) -> tuple[str, t.StrSequence]:
        """Apply configured legacy-removal transforms to resource."""
        source = FlextInfraUtilitiesRope.read_source(resource)
        changes: MutableSequence[str] = []
        fix_action = u.Infra.get_str_key(
            self.config,
            c.Infra.ReportKeys.FIX_ACTION,
            lower=True,
        )
        new_source = source
        if "alias" in self.rule_id or fix_action == "remove":
            new_source, alias_changes = self._remove_aliases(
                rope_project,
                resource,
                new_source,
            )
            changes.extend(alias_changes)
        if "deprecated" in self.rule_id or fix_action == "remove_and_update_refs":
            new_source, deprecated_changes = self._remove_deprecated(
                new_source,
            )
            changes.extend(deprecated_changes)
        if "wrapper" in self.rule_id or fix_action == "inline_and_remove":
            new_source, wrapper_changes = self._remove_wrappers(new_source)
            changes.extend(wrapper_changes)
        if "bypass" in self.rule_id or fix_action == "keep_try_only":
            new_source, bypass_changes = self._remove_import_bypasses(
                new_source,
            )
            changes.extend(bypass_changes)
        if new_source != source and not dry_run:
            FlextInfraUtilitiesRope.write_source(
                rope_project,
                resource,
                new_source,
                description="legacy removal",
            )
        return (new_source, changes)

    def _typed_config(self) -> Mapping[str, t.Infra.InfraValue]:
        """Get self.config validated as Mapping[str, InfraValue]."""
        return INFRA_MAPPING_ADAPTER.validate_python(self.config)

    @staticmethod
    def _normalize_string_items(value: t.Infra.InfraValue) -> t.StrSequence:
        if not isinstance(value, (list, tuple, set)):
            return []
        try:
            items: Sequence[t.Infra.InfraValue] = INFRA_SEQ_ADAPTER.validate_python(
                value
            )
        except ValidationError:
            return []
        return [item for item in items if isinstance(item, str)]

    def _remove_aliases(
        self,
        rope_project: t.Infra.RopeProject,
        resource: t.Infra.RopeResource,
        source: str,
    ) -> tuple[str, t.StrSequence]:
        """Remove module-level identity aliases via rope."""
        typed_config = self._typed_config()
        allow_aliases = set(
            self._normalize_string_items(
                typed_config.get("allow_aliases", []),
            ),
        )
        allow_target_suffixes = tuple(
            self._normalize_string_items(
                typed_config.get("allow_target_suffixes", []),
            ),
        )
        new_source, removed = FlextInfraUtilitiesRope.remove_module_level_aliases(
            rope_project,
            resource,
            allow=allow_aliases,
            apply=False,
        )
        changes: MutableSequence[str] = []
        for alias_desc in removed:
            target = alias_desc.split(" = ")[0] if " = " in alias_desc else ""
            if allow_target_suffixes and target.endswith(allow_target_suffixes):
                continue
            changes.append(f"Removed alias: {alias_desc}")
        return (new_source if changes else source, changes)

    @staticmethod
    def _remove_deprecated(source: str) -> tuple[str, t.StrSequence]:
        """Remove classes/functions decorated with @deprecated."""
        deprecated_re = re.compile(
            r"^@deprecated.*\n(?:class|def)\s+(\w+).*?(?=\n(?:class |def |@|\Z))",
            re.MULTILINE | re.DOTALL,
        )
        changes: MutableSequence[str] = []
        new_source = source
        for match in deprecated_re.finditer(source):
            changes.append(f"Removed deprecated: {match.group(1)}")
        new_source = deprecated_re.sub("", source)
        return (new_source, changes)

    @staticmethod
    def _remove_wrappers(source: str) -> tuple[str, t.StrSequence]:
        """Inline single-return passthrough wrappers as aliases."""
        wrapper_re = re.compile(
            r"^def\s+(\w+)\s*\([^)]*\)[^:]*:\s*\n"
            r"\s+return\s+(\w+)\s*\([^)]*\)\s*$",
            re.MULTILINE,
        )
        changes: MutableSequence[str] = []
        new_source = source
        for match in wrapper_re.finditer(source):
            wrapper_name = match.group(1)
            target_name = match.group(2)
            new_source = new_source.replace(
                match.group(0),
                f"{wrapper_name} = {target_name}",
            )
            changes.append(f"Inlined wrapper: {wrapper_name} -> {target_name}")
        return (new_source, changes)

    @staticmethod
    def _remove_import_bypasses(source: str) -> tuple[str, t.StrSequence]:
        """Remove try/except ImportError blocks that bypass imports."""
        bypass_re = re.compile(
            r"^try:\s*\n\s+from\s+\S+\s+import\s+\S+.*?\n"
            r"except\s+ImportError.*?(?=\n(?:class |def |@|try:|\Z))",
            re.MULTILINE | re.DOTALL,
        )
        changes: MutableSequence[str] = []
        for _match in bypass_re.finditer(source):
            changes.append("Removed import bypass block")
        new_source = bypass_re.sub("", source)
        return (new_source, changes)


__all__ = ["FlextInfraRefactorLegacyRemovalRule"]
