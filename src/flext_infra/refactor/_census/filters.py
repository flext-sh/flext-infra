"""Census duplicate grouping and object/analysis filters.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections import defaultdict
from collections.abc import MutableMapping, Sequence
from typing import ClassVar

from flext_infra import m


class FlextInfraRefactorCensusFilters:
    """Duplicate detection and inclusion filters.

    Composed into FlextInfraRefactorCensus via inheritance; self-contained
    static helpers over report Object/convention models (no census state).
    """

    _MIN_DUPLICATE_DEFINITIONS: ClassVar[int] = 2

    @staticmethod
    def duplicate_groups(
        project_objects: tuple[Sequence[m.Infra.Object], ...],
    ) -> tuple[m.Infra.DuplicateGroup, ...]:
        """Duplicate groups.

        Returns:
            The resulting ``tuple[m.Infra.DuplicateGroup, ...],``.

        """

        def object_location(item: m.Infra.Object) -> tuple[str, str, int]:
            return item.project, item.file_path, item.line

        groups: MutableMapping[tuple[str, str, str], list[m.Infra.Object]] = (
            defaultdict(list)
        )
        payloads: MutableMapping[str, list[m.Infra.Object]] = defaultdict(list)
        for item in (obj for objects in project_objects for obj in objects):
            owner = item.scope_path.rpartition(".")[0]
            groups[item.kind, item.name, owner].append(item)
            if item.payload_fingerprint:
                payloads[item.payload_fingerprint].append(item)
        duplicates: list[m.Infra.DuplicateGroup] = []
        for key in sorted(groups):
            definitions = groups[key]
            if (
                len(definitions)
                < FlextInfraRefactorCensusFilters._MIN_DUPLICATE_DEFINITIONS
            ):
                continue
            canonical = min(definitions, key=object_location)
            duplicates.append(
                m.Infra.DuplicateGroup(
                    name=definitions[0].name,
                    kind=definitions[0].kind,
                    definitions=definitions,
                    canonical=canonical.project,
                    value_identical=len({item.fingerprint for item in definitions})
                    == 1,
                ),
            )
        for fingerprint in sorted(payloads):
            definitions = sorted(payloads[fingerprint], key=object_location)
            if (
                len(definitions)
                < FlextInfraRefactorCensusFilters._MIN_DUPLICATE_DEFINITIONS
            ):
                continue
            owners = {
                (item.name, item.scope_path.rpartition(".")[0]) for item in definitions
            }
            if len(owners) == 1:
                continue
            duplicates.append(
                m.Infra.DuplicateGroup(
                    name=definitions[0].name,
                    kind=definitions[0].kind,
                    definitions=definitions,
                    canonical=definitions[0].project,
                    value_identical=False,
                    semantic_candidate=True,
                ),
            )
        return tuple(duplicates)

    @staticmethod
    def _include_object(
        item: m.Infra.Object,
        *,
        selected_families: frozenset[str],
        selected_kinds: frozenset[str] | None,
    ) -> bool:
        """Return whether one inventory object passes the kind and family filters.

        Returns:
            Whether one inventory object passes the kind and family filters.

        """
        if selected_kinds and item.kind not in selected_kinds:
            return False
        if not selected_families:
            return True
        return (
            item.actual_tier.lower() in selected_families
            or item.expected_tier.lower() in selected_families
        )

    @staticmethod
    def _include_rule(
        rule: str,
        *,
        rule_names: Sequence[str] | None,
        selected_rules: frozenset[str] | None = None,
    ) -> bool:
        """Include rule.

        ``selected_rules`` is a precomputed frozenset of ``rule_names``;
        callers in hot loops MUST pass it to avoid per-call set construction.

        Returns:
            The resulting ``bool``.

        """
        if selected_rules is None:
            return rule_names is None or rule in frozenset(rule_names)
        return rule in selected_rules


__all__: list[str] = ["FlextInfraRefactorCensusFilters"]
