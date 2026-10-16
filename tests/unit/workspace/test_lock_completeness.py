"""The committed uv.lock carries every distribution it references.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from json import dumps
from pathlib import Path

import pytest

from flext_infra.workspace import (
    FlextInfraWorkspaceDetector,
    FlextInfraWorkspaceLockCompleteness,
)
from tests import c, m, t, tm, u


class TestsFlextInfraWorkspaceLockCompleteness:
    """An interrupted resolution must never pass as a complete lock."""

    @staticmethod
    def _selected_lock(root: Path) -> Path:
        """Consume the same physical owner and resolver view as public validation.

        Returns:
            The resolved lock path.

        """
        return tm.ok(FlextInfraWorkspaceDetector.resolution_context(root)).lock_path

    def test_native_leaf_omissions_have_fresh_empty_groups(self) -> None:
        """UV omits empty edge collections without omitting package identity."""
        payload = (
            '{"name":"audit-leaf","version":"1.0",'
            '"source":{"registry":"https://example.com/simple"}}'
        )
        first = m.Infra.LockedPackage.model_validate_json(payload)
        second = m.Infra.LockedPackage.model_validate_json(payload)
        tm.that(first.dependencies, eq=())
        tm.that(first.resolution_markers, eq=())
        tm.that(len(first.optional_dependencies), eq=0)
        tm.that(len(first.dev_dependencies), eq=0)
        tm.that(first.optional_dependencies is second.optional_dependencies, eq=False)
        tm.that(first.dev_dependencies is second.dev_dependencies, eq=False)
        tm.that(
            m.Infra.LockedPackage.model_validate_json(
                first.model_dump_json(by_alias=True),
            ),
            eq=first,
        )

    @pytest.mark.parametrize("missing", ["name", "version", "source"])
    def test_required_locked_identity_never_defaults(self, missing: str) -> None:
        """Collection defaults cannot turn an incomplete identity into a package."""
        package = m.Infra.LockedPackage.model_validate_json(
            '{"name":"audit-leaf","version":"1.0",'
            '"source":{"registry":"https://example.com/simple"}}'
        )
        payload = package.model_dump_json(by_alias=True, exclude={missing})
        with pytest.raises(ValueError, match=missing):
            m.Infra.LockedPackage.model_validate_json(payload)

    def test_native_edge_identity_and_groups_survive_round_trip(self) -> None:
        """Typed defaults preserve provided sources, extras, groups and markers."""
        payload = """{
            "name": "audit-root", "version": "1.0",
            "source": {"virtual": "."},
            "dependencies": [{
                "name": "audit-edge", "version": "2.0",
                "source": {"registry": "https://example.com/simple"},
                "marker": "python_version >= '3.13'", "extra": ["feature"]
            }],
            "optional-dependencies": {"feature": [{"name": "audit-optional"}]},
            "dev-dependencies": {"audit": [{"name": "audit-dev"}]},
            "resolution-markers": ["sys_platform == 'linux'"]
        }"""
        package = m.Infra.LockedPackage.model_validate_json(payload)
        tm.that(package.dependencies[0].version, eq="2.0")
        tm.that(package.dependencies[0].source is not None, eq=True)
        tm.that(package.dependencies[0].extra, eq=("feature",))
        tm.that(package.dependencies[0].marker, eq="python_version >= '3.13'")
        tm.that(package.optional_dependencies["feature"][0].name, eq="audit-optional")
        tm.that(package.dev_dependencies["audit"][0].name, eq="audit-dev")
        tm.that(package.resolution_markers, eq=("sys_platform == 'linux'",))
        tm.that(
            m.Infra.LockedPackage.model_validate_json(
                package.model_dump_json(by_alias=True),
            ),
            eq=package,
        )

    def test_a_native_lock_passes_without_mutation(
        self,
        duplicate_project: Path,
    ) -> None:
        """The real once-provisioned consumer keeps its immutable lock bytes."""
        lock = self._selected_lock(duplicate_project)
        before = lock.read_bytes()
        tm.ok(FlextInfraWorkspaceLockCompleteness.validate(duplicate_project))
        tm.that(lock.read_bytes(), eq=before)

    def test_malformed_manifest_groups_fail_without_lock_mutation(
        self,
        duplicate_project: Path,
    ) -> None:
        """Native manifest validation precedes permissive requirement extraction."""
        lock = self._selected_lock(duplicate_project)
        before = lock.read_bytes()
        path = duplicate_project / c.PYPROJECT_FILENAME
        document = tm.ok(u.Cli.toml_read_document(path))
        u.Cli.toml_sync_value(
            document,
            c.Infra.DEPENDENCY_GROUPS,
            {"invalid-audit-group": [42]},
        )
        tm.ok(u.Cli.files_write_text(path, u.Cli.toml_dumps(document)))
        tm.fail(FlextInfraWorkspaceLockCompleteness.validate(duplicate_project))
        tm.that(lock.read_bytes(), eq=before)

    def test_a_partial_lock_fails_loud_without_repairing_it(
        self, duplicate_project: Path
    ) -> None:
        """Removing a real active package never passes as an empty closure."""
        lock = self._selected_lock(duplicate_project)
        document = tm.ok(u.Cli.toml_read_document(lock))
        payload = tm.ok(u.Cli.toml_read_json(lock))
        inventory = m.Infra.LockedEnvironment.model_validate_json(dumps(payload))
        name = c.Tests.CONSUMER_MODULES[0]
        tm.that(any(item.name == name for item in inventory.package), eq=True)
        u.Cli.toml_sync_value(
            document,
            "package",
            [
                entry
                for entry in u.Cli.json_as_sequence(payload["package"])
                if u.Cli.json_as_mapping(entry)["name"] != name
            ],
        )
        tm.ok(u.Cli.files_write_text(lock, u.Cli.toml_dumps(document)))
        before = lock.read_bytes()
        tm.fail(FlextInfraWorkspaceLockCompleteness.validate(duplicate_project))
        tm.that(lock.read_bytes(), eq=before)

    @pytest.mark.parametrize(
        "marker",
        ['python_version < "0"', 'extra == "unselected-audit-extra"'],
    )
    def test_inactive_distribution_metadata_is_not_a_resolved_edge(
        self,
        duplicate_project: Path,
        marker: str,
    ) -> None:
        """Metadata for inactive markers/extras does not create phantom packages."""
        lock = self._selected_lock(duplicate_project)
        payload = tm.ok(u.Cli.toml_read_json(lock))
        inventory = m.Infra.LockedEnvironment.model_validate_json(dumps(payload))
        supplier = next(item for item in inventory.package if item.source.registry)
        rows: t.JsonValueList = [
            {
                **u.Cli.json_as_mapping(entry),
                "metadata": {
                    **u.Cli.json_as_mapping(
                        u.Cli.json_as_mapping(entry).get("metadata"),
                    ),
                    "requires-dist": [
                        *u.Cli.json_as_sequence(
                            u.Cli.json_as_mapping(
                                u.Cli.json_as_mapping(entry).get("metadata"),
                            ).get("requires-dist"),
                        ),
                        {
                            "name": "inactive-audit-dependency",
                            "marker": marker,
                        },
                    ],
                },
            }
            if u.Cli.json_as_mapping(entry)["name"] == supplier.name
            else entry
            for entry in u.Cli.json_as_sequence(payload["package"])
        ]
        document = u.Cli.toml_document_from_mapping({**payload, "package": rows})
        tm.ok(u.Cli.files_write_text(lock, u.Cli.toml_dumps(document)))
        before = lock.read_bytes()
        tm.ok(FlextInfraWorkspaceLockCompleteness.validate(duplicate_project))
        tm.that(lock.read_bytes(), eq=before)

    @pytest.mark.parametrize(
        "text",
        [
            "not [valid toml {{{",
            "",
            "package = []",
            'package = ["invalid"]',
            (
                '[[package]]\nname = ""\nversion = "1"\n'
                'source = {registry = "https://example.com"}'
            ),
        ],
    )
    def test_an_invalid_lock_fails_loud(self, tmp_path: Path, text: str) -> None:
        """Malformed syntax, empty inventories and invalid typed rows fail."""
        lock = tmp_path / c.Infra.UV_LOCK_FILENAME
        lock.write_text(text, encoding="utf-8")
        tm.fail(FlextInfraWorkspaceLockCompleteness.validate_lock_file(lock))

    def test_a_missing_lock_fails_loud(self, tmp_path: Path) -> None:
        """No committed lock is a loud absence, never an empty pass."""
        tm.fail(
            FlextInfraWorkspaceLockCompleteness.validate_lock_file(
                tmp_path / c.Infra.UV_LOCK_FILENAME,
            ),
        )

    def test_the_infra_checkout_lock_is_complete(self) -> None:
        """The repository's own committed lock always passes its own gate."""
        root = Path(__file__).parents[3]
        tm.ok(FlextInfraWorkspaceLockCompleteness.validate(root))

    def test_public_validation_uses_the_elected_view(
        self,
        duplicate_project: Path,
    ) -> None:
        """A malformed legacy root lock cannot replace a complete selected view."""
        lock = self._selected_lock(duplicate_project)
        before = lock.read_bytes()
        legacy = duplicate_project / c.Infra.UV_LOCK_FILENAME
        tm.that(legacy != lock, eq=True)
        legacy.write_text("package = []\n", encoding="utf-8")

        tm.ok(FlextInfraWorkspaceLockCompleteness.validate(duplicate_project))

        tm.that(lock.read_bytes(), eq=before)
        tm.that(legacy.read_text(encoding="utf-8"), eq="package = []\n")
