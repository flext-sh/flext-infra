"""Fixed-effect plan collection through the shared codegen publisher.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from typing import TYPE_CHECKING

from flext_infra import m, r, u

if TYPE_CHECKING:
    from flext_infra import p


class FlextInfraDocCollector:
    """Publish only fully supported source associations."""

    @classmethod
    def collect(cls, request: m.Infra.DocsCollectRequest) -> p.Result[bool]:
        """Parse the configuration, collect sources, and publish their plans.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        configuration = cls._configuration(request)
        if configuration.failure:
            return r[bool].from_failure(configuration)
        root = request.repository_root
        bundle = u.Infra.docs_collect_plan_files(root, configuration.value)
        incomplete = tuple(
            item for item in bundle.coverage if item.adapter == "private-inventory"
        )
        if incomplete:
            pending = ", ".join(
                f"{item.source_id}:{item.status}:{item.files}" for item in incomplete
            )
            return r[bool].fail(
                f"plan source extraction is incomplete; private "
                f"inventories are not extracted plans: {pending}",
            )
        published = u.Infra.publish_codegen_plans(root, bundle.files)
        if published.failure:
            return r[bool].from_failure(published)
        lock = u.Infra.mutation_lock_path(root)
        if lock.failure:
            return r[bool].from_failure(lock)
        with u.Cli.file_changes_lock(lock.value):
            return cls._prune_bundle_directories(bundle)

    @staticmethod
    def _configuration(
        request: m.Infra.DocsCollectRequest,
    ) -> p.Result[m.Infra.PlanCollectionConfig]:
        """Require a physical root and parse the collection configuration.

        Returns:
            The parsed collection configuration, or the first failure.

        """
        result_type = r[m.Infra.PlanCollectionConfig]
        root = request.repository_root
        if not root.is_absolute() or ".." in root.parts or root.resolve() != root:
            return result_type.fail(
                f"plan collection repository root is not a physical "
                f"absolute path: {root}",
            )
        configuration_path = request.configuration
        if not configuration_path.is_absolute():
            configuration_path = root / configuration_path
        captured = u.Cli.atomic_read_binary_file_state(
            configuration_path,
            required=True,
        )
        if captured.failure:
            return result_type.from_failure(captured)
        if captured.value.content is None:
            return result_type.fail(
                f"plan collection configuration is absent: {configuration_path}",
            )
        parsed = u.Cli.yaml_parse(captured.value.content.decode("utf-8"))
        if parsed.failure:
            return result_type.from_failure(parsed)
        return u.validate_value(
            m.Infra.PlanCollectionConfig,
            parsed.value,
            strict=False,
        )

    @staticmethod
    def _prune_bundle_directories(
        bundle: m.Infra.PlanCollectionBundle,
    ) -> p.Result[bool]:
        """Delete the bundle's empty prunable directories.

        Returns:
            The resulting ``p.Result[bool]``.

        """
        for directory in bundle.prunable_directories:
            observed = u.Cli.atomic_read_empty_directory_state(
                directory,
                required=False,
            )
            if observed.failure:
                return r[bool].from_failure(observed)
            if not observed.value.exists:
                continue
            removed = u.Cli.atomic_delete_empty_directory_guarded(observed.value)
            if removed.failure:
                return r[bool].from_failure(removed)
        return r[bool].ok(value=True)


__all__: list[str] = ["FlextInfraDocCollector"]
