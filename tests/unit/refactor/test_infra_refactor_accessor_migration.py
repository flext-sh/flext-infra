"""Unit tests for the accessor migration orchestrator's rewrite contract.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from flext_infra import c, config, infra, m
from flext_infra.refactor.accessor_migration import (
    FlextInfraAccessorMigrationOrchestrator,
)
from tests import tm, u

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra import t

_SOURCE_NAME = next(iter(c.ENFORCEMENT_ACCESSOR_RENAMES))
_REPLACEMENT_NAME = c.ENFORCEMENT_ACCESSOR_RENAMES[_SOURCE_NAME][0]


def _legacy_module_source() -> str:
    """Return a module defining and calling the catalog's first rename source."""
    return (
        "from __future__ import annotations\n"
        "\n"
        f"def {_SOURCE_NAME}(flag: bool) -> bool:\n"
        "    return flag\n"
        "\n"
        "\n"
        f"value = {_SOURCE_NAME}(True)\n"
    )


def _materialize_fixture(tmp_path: Path) -> t.Triple[Path, Path, Path]:
    """Build one workspace whose origin-named package owns the rename target.

    Returns:
        The resulting ``t.Triple[Path, Path, Path]``.
    """
    workspace, project, pkg = u.Tests.namespace_workspace(
        tmp_path,
        package_name="flext_core",
        pyproject=(
            f"[project]\nname='flext-core'\nversion='{config.Infra.initial_project_version}'\n"
        ),
    )
    _ = u.Tests.src_package(
        workspace,
        "workspace_root",
        pyproject=(
            "[project]\nname='workspace-root'\n"
            f"version='{config.Infra.initial_project_version}'\n"
        ),
    )
    origin_file = pkg / "legacy.py"
    _ = origin_file.write_text(_legacy_module_source(), encoding="utf-8")
    foreign_pkg = project / "src" / "other_pkg"
    foreign_pkg.mkdir(parents=True, exist_ok=True)
    _ = (foreign_pkg / "__init__.py").write_text("", encoding="utf-8")
    foreign_file = foreign_pkg / "legacy.py"
    _ = foreign_file.write_text(_legacy_module_source(), encoding="utf-8")
    u.Tests.provision_checkout(workspace)
    return workspace, origin_file, foreign_file


class TestsFlextInfraRefactorInfraRefactorAccessorMigration:
    """Behavior contract for test_infra_refactor_accessor_migration."""

    @staticmethod
    def test_catalog_rules_resolve_against_one_original_source(tmp_path: Path) -> None:
        """Earlier renames must not shift later rules' semantic coordinates."""
        workspace, origin_file, foreign_file = _materialize_fixture(tmp_path)
        declarations = "\n\n".join(
            f"def {name}(flag: bool) -> bool:\n    return flag"
            for name in c.ENFORCEMENT_ACCESSOR_RENAMES
        )
        calls = ", ".join(f"{name}(True)" for name in c.ENFORCEMENT_ACCESSOR_RENAMES)
        source = f"{declarations}\n\nvalue = ({calls})\n"
        _ = origin_file.write_text(source, encoding="utf-8")
        _ = foreign_file.write_text(source, encoding="utf-8")

        result = FlextInfraAccessorMigrationOrchestrator(
            source_preview=infra.source_preview(workspace),
            repository_root=workspace,
            apply_changes=False,
        ).execute()

        tm.that(result.failure, eq=False)
        tm.that(
            result.value.automated_change_count,
            eq=len(c.ENFORCEMENT_ACCESSOR_RENAMES) * 2,
        )
        tm.that(origin_file.read_text(encoding="utf-8"), eq=source)
        tm.that(foreign_file.read_text(encoding="utf-8"), eq=source)
        actual = tuple(
            (change.original_name, change.replacement_name)
            for file_report in result.value.files
            for change in file_report.automated_changes
        )
        for name, (replacement, _reason) in c.ENFORCEMENT_ACCESSOR_RENAMES.items():
            tm.that(actual.count((name, replacement)), eq=2)

    @staticmethod
    def test_preview_limit_does_not_limit_validation(tmp_path: Path) -> None:
        """A display limit cannot remove a candidate from lint accounting."""
        workspace, origin_file, _foreign_file = _materialize_fixture(tmp_path)
        _ = (origin_file.parent / "another.py").write_text(
            _legacy_module_source(), encoding="utf-8"
        )
        limited = FlextInfraAccessorMigrationOrchestrator(
            source_preview=infra.source_preview(workspace),
            repository_root=workspace,
            apply_changes=False,
            preview_limit=1,
        ).execute()
        complete = FlextInfraAccessorMigrationOrchestrator(
            source_preview=infra.source_preview(workspace),
            repository_root=workspace,
            apply_changes=False,
        ).execute()

        tm.that(limited.failure, eq=False)
        tm.that(complete.failure, eq=False)
        tm.that(len(limited.value.files), eq=1)
        tm.that(
            limited.value.automated_change_count,
            eq=complete.value.automated_change_count,
        )
        tm.that(limited.value.lint_before_totals, eq=complete.value.lint_before_totals)
        tm.that(limited.value.lint_after_totals, eq=complete.value.lint_after_totals)
        tm.that(
            limited.value.new_lint_error_totals,
            eq=complete.value.new_lint_error_totals,
        )
        tm.that(origin_file.read_text(encoding="utf-8"), eq=_legacy_module_source())

    @staticmethod
    def test_workspace_selection_includes_member_without_root_selector(
        tmp_path: Path,
    ) -> None:
        """The workspace recipe must not narrow the backend to its root alone."""
        workspace, origin_file, _foreign_file = _materialize_fixture(tmp_path)
        complete = FlextInfraAccessorMigrationOrchestrator(
            source_preview=infra.source_preview(workspace),
            repository_root=workspace,
            apply_changes=False,
        ).execute()
        root_only = FlextInfraAccessorMigrationOrchestrator(
            source_preview=infra.source_preview(workspace),
            repository_root=workspace,
            selected_projects=(".",),
            apply_changes=False,
        ).execute()

        tm.that(complete.failure, eq=False)
        tm.that(root_only.failure, eq=False)
        tm.that(complete.value.automated_change_count > 0, eq=True)
        tm.that(root_only.value.automated_change_count, eq=0)
        tm.that(complete.value.files_scanned > root_only.value.files_scanned, eq=True)
        tm.that(origin_file.read_text(encoding="utf-8"), eq=_legacy_module_source())

    @staticmethod
    def test_dry_run_reports_pending_change_and_writes_nothing(
        tmp_path: Path,
    ) -> None:
        """A run without ``apply`` never writes sources and says it is dry."""
        workspace, origin_file, _foreign_file = _materialize_fixture(tmp_path)
        source_before = origin_file.read_text(encoding="utf-8")
        orchestrator = FlextInfraAccessorMigrationOrchestrator(
            source_preview=infra.source_preview(workspace),
            repository_root=workspace,
            apply_changes=False,
        )

        result = orchestrator.execute()

        tm.that(result.failure, eq=False)
        tm.that(result.value.dry_run, eq=True)
        tm.that(result.value.automated_change_count > 0, eq=True)
        tm.that(origin_file.read_text(encoding="utf-8"), eq=source_before)

    @staticmethod
    def test_dry_run_publishes_the_report_receipt(tmp_path: Path) -> None:
        """Every run publishes the structured receipt under ``.reports``."""
        workspace, _origin_file, _foreign_file = _materialize_fixture(tmp_path)
        orchestrator = FlextInfraAccessorMigrationOrchestrator(
            source_preview=infra.source_preview(workspace),
            repository_root=workspace,
            apply_changes=False,
        )

        result = orchestrator.execute()

        tm.that(result.failure, eq=False)
        receipt = (
            workspace / c.Infra.ACCESSOR_MIGRATION_REPORT_RELATIVE_PATH
        ).resolve()
        tm.that(receipt.exists(), eq=True)
        published = json.loads(receipt.read_text(encoding="utf-8"))
        tm.that(published["dry_run"], eq=True)
        tm.that(published["workspace"], eq=str(workspace))

    @staticmethod
    def test_apply_renames_origin_owned_and_leaves_foreign_homonym(
        tmp_path: Path,
    ) -> None:
        """Only occurrences defined inside the origin package are renamed."""
        workspace, origin_file, foreign_file = _materialize_fixture(tmp_path)
        orchestrator = FlextInfraAccessorMigrationOrchestrator(
            source_preview=infra.source_preview(workspace),
            repository_root=workspace,
            apply_changes=True,
        )

        result = orchestrator.execute()

        tm.that(result.failure, eq=False)
        tm.that(result.value.dry_run, eq=False)
        origin_source = origin_file.read_text(encoding="utf-8")
        tm.that(origin_source, has=f"def {_REPLACEMENT_NAME}(")
        tm.that(origin_source, has=f"= {_REPLACEMENT_NAME}(True)")
        tm.that(origin_source, lacks=f"def {_SOURCE_NAME}(")
        foreign_source = foreign_file.read_text(encoding="utf-8")
        tm.that(foreign_source, eq=_legacy_module_source())
        skipped_reasons = tuple(
            change.reason
            for file_report in result.value.files
            for change in file_report.warnings
            if change.reason.startswith("Skipped homonym")
        )
        tm.that(skipped_reasons, empty=False)

    @staticmethod
    def test_apply_is_idempotent_on_the_second_pass(tmp_path: Path) -> None:
        """A second pass over the migrated tree finds nothing left to rename."""
        workspace, origin_file, _foreign_file = _materialize_fixture(tmp_path)
        first = FlextInfraAccessorMigrationOrchestrator(
            source_preview=infra.source_preview(workspace),
            repository_root=workspace,
            apply_changes=True,
        ).execute()
        tm.that(first.failure, eq=False)
        migrated_source = origin_file.read_text(encoding="utf-8")

        second = FlextInfraAccessorMigrationOrchestrator(
            source_preview=infra.source_preview(workspace),
            repository_root=workspace,
            apply_changes=True,
        ).execute()

        tm.that(second.failure, eq=False)
        tm.that(second.value.automated_change_count, eq=0)
        tm.that(origin_file.read_text(encoding="utf-8"), eq=migrated_source)

    @staticmethod
    def test_module_filter_selects_bindings_without_truncating_consumers(
        tmp_path: Path,
    ) -> None:
        """A module selector narrows ownership, not the coupled source inventory."""
        workspace, _origin_file, _foreign_file = _materialize_fixture(tmp_path)
        unfiltered = FlextInfraAccessorMigrationOrchestrator(
            source_preview=infra.source_preview(workspace),
            repository_root=workspace,
            apply_changes=False,
        ).execute()
        tm.that(unfiltered.failure, eq=False)

        filtered = FlextInfraAccessorMigrationOrchestrator(
            source_preview=infra.source_preview(workspace),
            repository_root=workspace,
            apply_changes=False,
            target_module="flext_core.legacy",
        ).execute()

        tm.that(filtered.failure, eq=False)
        tm.that(
            filtered.value.files_scanned,
            eq=unfiltered.value.files_scanned,
        )
        tm.that(filtered.value.files_scanned > 0, eq=True)

    @staticmethod
    def test_manual_warnings_preserve_real_sdk_overrides(
        tmp_path: Path,
    ) -> None:
        """An actual Rope SDK superclass owns the override, not its local spelling."""
        workspace, _project, pkg = u.Tests.namespace_workspace(
            tmp_path,
            package_name="flext_core",
            pyproject=(
                f"[project]\nname='flext-core'\nversion='{config.Infra.initial_project_version}'\n"
            ),
        )
        advisory_file = pkg / "advisory.py"
        _ = advisory_file.write_text(
            "from __future__ import annotations\n"
            "from rope.base.project import Project\n"
            "\n"
            "class Owned:\n"
            "    def get_value(self) -> int:\n"
            "        return 1\n"
            "\n"
            "\n"
            "class Adapter(Project):\n"
            "    def get_source_folders(self):\n"
            "        return super().get_source_folders()\n",
            encoding="utf-8",
        )
        u.Tests.provision_checkout(workspace)
        orchestrator = FlextInfraAccessorMigrationOrchestrator(
            source_preview=infra.source_preview(workspace),
            repository_root=workspace,
            apply_changes=True,
        )

        result = orchestrator.execute()

        tm.that(result.failure, eq=False)
        advisory_source = advisory_file.read_text(encoding="utf-8")
        tm.that(advisory_source, has="def get_value(self) -> int:")
        tm.that(advisory_source, has="def get_source_folders(self):")
        warning_names = tuple(
            change.original_name
            for file_report in result.value.files
            for change in file_report.warnings
        )
        tm.that(warning_names, has="get_value")
        tm.that(warning_names, lacks="get_source_folders")

    @staticmethod
    @pytest.mark.parametrize("decorator", ("", "@staticmethod\n    ", "@classmethod\n    "))
    def test_core_prefix_policy_discovers_methods_outside_legacy_catalog(
        tmp_path: Path,
        decorator: str,
    ) -> None:
        """The canonical prefix policy, not seventeen names, owns discovery."""
        workspace, origin_file, _foreign_file = _materialize_fixture(tmp_path)
        policy = m.MethodShapeParams.model_validate(
            c.ENFORCEMENT_PREDICATE_SPECS["no_accessor_methods"]["params"]
        )
        name = f"{next(iter(policy.forbidden_prefixes))}owned_probe"
        tm.that(name in c.ENFORCEMENT_ACCESSOR_RENAMES, eq=False)
        source = (
            f"class Owned:\n    {decorator}def {name}(self) -> bool:\n"
            "        return True\n"
            f"\nclass Derived(Owned):\n    {decorator}def {name}(self) -> bool:\n"
            "        return False\n"
        )
        _ = origin_file.write_text(source, encoding="utf-8")
        result = FlextInfraAccessorMigrationOrchestrator(
            source_preview=infra.source_preview(workspace),
            repository_root=workspace,
            apply_changes=False,
        ).execute()

        tm.that(result.failure, eq=False)
        findings = tuple(
            warning
            for file in result.value.files
            for warning in file.warnings
            if warning.original_name == name
        )
        tm.that(findings, len=1)
        tm.that(findings[0].reason, has=f"flext_core.legacy.Owned.{name}")
        tm.that(findings[0].replacement_name, eq="")
        tm.that(origin_file.read_text(encoding="utf-8"), eq=source)

    @staticmethod
    def test_local_functions_retain_nested_class_method_discovery(
        tmp_path: Path,
    ) -> None:
        """Local bindings and nested introducing classes remain in the same inventory."""
        workspace, origin_file, _foreign_file = _materialize_fixture(tmp_path)
        policy = m.MethodShapeParams.model_validate(
            c.ENFORCEMENT_PREDICATE_SPECS["no_accessor_methods"]["params"]
        )
        name = f"{next(iter(policy.forbidden_prefixes))}owned_probe"
        source = (
            "def factory(flag: bool):\n"
            "    def process_single_item(value: bool) -> bool:\n"
            "        return value\n"
            f"    def {_SOURCE_NAME}(value: bool) -> bool:\n"
            "        return process_single_item(value)\n"
            "    class Owned:\n"
            "        class Nested:\n"
            f"            def {name}(self) -> bool:\n"
            "                return True\n"
            f"    return {_SOURCE_NAME}(flag), Owned.Nested\n"
        )
        _ = origin_file.write_text(source, encoding="utf-8")
        result = FlextInfraAccessorMigrationOrchestrator(
            source_preview=infra.source_preview(workspace),
            repository_root=workspace,
            apply_changes=False,
        ).execute()

        tm.that(result.failure, eq=False)
        changes = tuple(
            change
            for file in result.value.files
            for change in file.automated_changes
            if change.original_name == _SOURCE_NAME
        )
        tm.that(changes, len=2)
        findings = tuple(
            warning
            for file in result.value.files
            for warning in file.warnings
            if warning.original_name == name
        )
        tm.that(findings, len=1)
        tm.that(findings[0].reason, has=f"factory.Owned.Nested.{name}")
        tm.that(origin_file.read_text(encoding="utf-8"), eq=source)

    @staticmethod
    def test_unresolved_owned_accessor_ancestry_fails_before_changes(
        tmp_path: Path,
    ) -> None:
        """A genuinely unresolved introducing contract never becomes empty coverage."""
        workspace, origin_file, _foreign_file = _materialize_fixture(tmp_path)
        policy = m.MethodShapeParams.model_validate(
            c.ENFORCEMENT_PREDICATE_SPECS["no_accessor_methods"]["params"]
        )
        name = f"{next(iter(policy.forbidden_prefixes))}owned_probe"
        source = f"class Owned(MissingBase):\n    def {name}(self):\n        return True\n"
        _ = origin_file.write_text(source, encoding="utf-8")

        with pytest.raises(ValueError, match="unresolved accessor class ancestry: Owned"):
            _ = FlextInfraAccessorMigrationOrchestrator(
                source_preview=infra.source_preview(workspace),
                repository_root=workspace,
                apply_changes=False,
            ).execute()

        tm.that(origin_file.read_text(encoding="utf-8"), eq=source)

    @staticmethod
    def test_facade_namespace_selects_utilities_and_external_consumers(
        tmp_path: Path,
    ) -> None:
        """The public u binding selects its MRO, never a literal u directory."""
        workspace, origin_file, foreign_file = _materialize_fixture(tmp_path)
        pkg = origin_file.parent
        family = u.Infra.facade_families()["u"]
        project = pkg.parent.parent
        implementation = u.Tests.src_package(
            project,
            f"flext_core/_{family.module}",
            pyproject=(project / "pyproject.toml").read_text(encoding="utf-8"),
        )
        owned_file = implementation / "owned.py"
        source = (
            f"class UtilityOwner:\n    def {_SOURCE_NAME}(self, flag: bool) -> bool:\n"
            "        return flag\n"
        )
        _ = owned_file.write_text(source, encoding="utf-8")
        _ = (pkg / f"{family.module}.py").write_text(
            f"from flext_core._{family.module}.owned import UtilityOwner\n\n"
            "class UtilityFacade(UtilityOwner):\n    pass\n\n"
            "u = UtilityFacade\n__all__ = ['UtilityFacade', 'u']\n",
            encoding="utf-8",
        )
        consumer = foreign_file.parent / "consumer.py"
        _ = consumer.write_text(
            f"from flext_core.{family.module} import u\n"
            f"value = u().{_SOURCE_NAME}(True)\n",
            encoding="utf-8",
        )
        result = FlextInfraAccessorMigrationOrchestrator(
            source_preview=infra.source_preview(workspace),
            repository_root=workspace,
            target_namespace="u",
            apply_changes=True,
        ).execute()

        tm.that(result.failure, eq=False)
        tm.that(owned_file.read_text(encoding="utf-8"), has=f"def {_REPLACEMENT_NAME}(")
        tm.that(
            consumer.read_text(encoding="utf-8"), has=f"u().{_REPLACEMENT_NAME}(True)"
        )
        tm.that(origin_file.read_text(encoding="utf-8"), eq=_legacy_module_source())
        tm.that(foreign_file.read_text(encoding="utf-8"), eq=_legacy_module_source())

    @staticmethod
    def test_unknown_namespace_is_not_successful_empty_selection(
        tmp_path: Path,
    ) -> None:
        """Unknown facade contracts must fail instead of returning green zero."""
        workspace, _origin_file, _foreign_file = _materialize_fixture(tmp_path)
        with pytest.raises(
            ValueError, match="accessor namespace selected no published facade"
        ):
            _ = FlextInfraAccessorMigrationOrchestrator(
                source_preview=infra.source_preview(workspace),
                repository_root=workspace,
                target_namespace="missing_facade",
                apply_changes=False,
            ).execute()
