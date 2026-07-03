"""Unit tests for the ENFORCE-080 project alias migrator."""

from __future__ import annotations

from flext_infra.transformers.project_alias_migrator import (
    FlextInfraRefactorProjectAliasMigrator,
)


class TestsFlextInfraRefactorProjectAliasMigrator:
    """Behavior contract for FlextInfraRefactorProjectAliasMigrator."""

    def test_migrates_owned_aliases_to_local_facades(self) -> None:
        source = (
            "from __future__ import annotations\n\n"
            "from flext_core import c, m, t, u\n\n"
            "x: t.StrSequence = ()\n"
        )
        transformer = FlextInfraRefactorProjectAliasMigrator(
            current_project="flext_infra"
        )
        updated, changes = transformer.apply_to_source(source)
        assert "from flext_core import c, m, t, u" not in updated
        assert "from flext_infra.constants import c" in updated
        assert "from flext_infra.models import m" in updated
        assert "from flext_infra.typings import t" in updated
        assert "from flext_infra.utilities import u" in updated
        assert len(changes) == 4

    def test_keeps_unowned_aliases_in_flext_core(self) -> None:
        source = (
            "from __future__ import annotations\n\n"
            "from flext_core import c, r\n\n"
            "log = r.Result\n"
        )
        transformer = FlextInfraRefactorProjectAliasMigrator(
            current_project="flext_infra"
        )
        updated, changes = transformer.apply_to_source(source)
        assert "from flext_core import r" in updated
        assert "from flext_infra.constants import c" in updated
        assert "from flext_infra" not in updated.split("from flext_core import r")[1]
        assert len(changes) == 1

    def test_migrates_parenthesized_multiline_import(self) -> None:
        source = (
            "from __future__ import annotations\n\n"
            "from flext_core import (\n"
            "    c,\n"
            "    m,\n"
            "    r,\n"
            ")\n\n"
            "VALUE = c.MAX_SIZE\n"
        )
        transformer = FlextInfraRefactorProjectAliasMigrator(
            current_project="flext_infra"
        )
        updated, changes = transformer.apply_to_source(source)
        assert "from flext_core import" not in updated
        assert "from flext_infra.constants import c" in updated
        assert "from flext_infra.models import m" in updated
        assert "from flext_core import r" in updated
        assert len(changes) == 3

    def test_no_change_when_project_owns_no_aliases(self) -> None:
        source = (
            "from __future__ import annotations\n\n"
            "from flext_core import c, t\n\n"
            "x = 1\n"
        )
        owners = {"flext_core": ("c", "m", "p", "t", "u")}
        transformer = FlextInfraRefactorProjectAliasMigrator(
            current_project="unknown_project",
            project_alias_owners=owners,
        )
        updated, changes = transformer.apply_to_source(source)
        assert updated == source
        assert changes == []

    def test_migrates_aliased_import_name(self) -> None:
        source = (
            "from __future__ import annotations\n\n"
            "from flext_core import c as constants_ns\n\n"
            "x = constants_ns.MAX_SIZE\n"
        )
        transformer = FlextInfraRefactorProjectAliasMigrator(
            current_project="flext_infra"
        )
        updated, changes = transformer.apply_to_source(source)
        assert "from flext_core import c as constants_ns" not in updated
        assert "from flext_infra.constants import c as constants_ns" in updated
        assert len(changes) == 1

    def test_removes_flext_core_import_when_all_aliases_migrated(self) -> None:
        source = (
            "from __future__ import annotations\n\n"
            "from flext_core import c\n\n"
            "x = c.MAX_SIZE\n"
        )
        transformer = FlextInfraRefactorProjectAliasMigrator(
            current_project="flext_infra"
        )
        updated, changes = transformer.apply_to_source(source)
        assert "from flext_core import" not in updated
        assert "from flext_infra.constants import c" in updated
        assert len(changes) == 1

    def test_no_change_without_flext_core_import(self) -> None:
        source = (
            "from __future__ import annotations\n\n"
            "from flext_infra.constants import c\n\n"
            "x = c.MAX_SIZE\n"
        )
        transformer = FlextInfraRefactorProjectAliasMigrator(
            current_project="flext_infra"
        )
        updated, changes = transformer.apply_to_source(source)
        assert updated == source
        assert changes == []
