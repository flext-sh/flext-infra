"""Unit tests for the ENFORCE-080 project alias migrator."""

from __future__ import annotations

from pathlib import Path

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
            current_project="flext_infra",
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
            current_project="flext_infra",
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
            current_project="flext_infra",
        )
        updated, changes = transformer.apply_to_source(source)
        assert "from flext_core import" in updated
        assert "from flext_infra.constants import c" in updated
        assert "from flext_infra.models import m" in updated
        assert "r" in updated
        assert len(changes) == 2

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

    def test_migrates_long_name_aliased_to_canonical(self) -> None:
        source = (
            "from __future__ import annotations\n\n"
            "from flext_core import FlextConstants as c\n\n"
            "x = c.MAX_SIZE\n"
        )
        transformer = FlextInfraRefactorProjectAliasMigrator(
            current_project="flext_infra",
        )
        updated, changes = transformer.apply_to_source(source)
        assert "from flext_core import FlextConstants as c" not in updated
        assert "from flext_infra.constants import c" in updated
        assert len(changes) == 1

    def test_keeps_non_canonical_alias_bound_name(self) -> None:
        source = (
            "from __future__ import annotations\n\n"
            "from flext_core import c as constants_ns\n\n"
            "x = constants_ns.MAX_SIZE\n"
        )
        transformer = FlextInfraRefactorProjectAliasMigrator(
            current_project="flext_infra",
        )
        updated, changes = transformer.apply_to_source(source)
        assert updated == source
        assert changes == []

    def test_removes_flext_core_import_when_all_aliases_migrated(self) -> None:
        source = (
            "from __future__ import annotations\n\n"
            "from flext_core import c\n\n"
            "x = c.MAX_SIZE\n"
        )
        transformer = FlextInfraRefactorProjectAliasMigrator(
            current_project="flext_infra",
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
            current_project="flext_infra",
        )
        updated, changes = transformer.apply_to_source(source)
        assert updated == source
        assert changes == []

    def test_migrates_submodule_alias_import(self) -> None:
        source = (
            "from __future__ import annotations\n\n"
            "from flext_core.utilities import FlextUtilities as u\n\n"
            "x = u.MAX_SIZE\n"
        )
        transformer = FlextInfraRefactorProjectAliasMigrator(
            current_project="flext_ldif",
        )
        updated, changes = transformer.apply_to_source(source)
        assert "from flext_core.utilities import FlextUtilities as u" not in updated
        assert "from flext_ldif.utilities import u" in updated
        assert len(changes) == 1

    def test_preserves_existing_local_alias(self) -> None:
        source = (
            "from __future__ import annotations\n\n"
            "from flext_core.utilities import FlextUtilities as u\n"
            "from flext_ldif.utilities import u\n\n"
            "x = u.MAX_SIZE\n"
        )
        transformer = FlextInfraRefactorProjectAliasMigrator(
            current_project="flext_ldif",
        )
        updated, changes = transformer.apply_to_source(source)
        assert "from flext_core.utilities import FlextUtilities as u" not in updated
        assert updated.count("from flext_ldif.utilities import u") == 1
        assert len(changes) == 1

    def test_skips_type_checking_imports(self) -> None:
        source = (
            "from __future__ import annotations\n\n"
            "from typing import TYPE_CHECKING\n\n"
            "if TYPE_CHECKING:\n"
            "    from flext_core import t\n\n"
            "x = 1\n"
        )
        transformer = FlextInfraRefactorProjectAliasMigrator(
            current_project="flext_infra",
        )
        updated, changes = transformer.apply_to_source(source)
        assert "from flext_core import t" in updated
        assert changes == []

    def test_skip_alias_source_packages(self) -> None:
        source = (
            "from __future__ import annotations\n\n"
            "from flext_core import c\n\n"
            "x = c.MAX_SIZE\n"
        )
        transformer = FlextInfraRefactorProjectAliasMigrator(
            current_project="flext_core",
        )
        updated, changes = transformer.apply_to_source(source)
        assert updated == source
        assert changes == []

    def test_keeps_core_aliases_inside_private_facade_implementation(self) -> None:
        source = (
            "from __future__ import annotations\n\n"
            "from flext_core import m, t\n\n"
            "class Demo(m.Base):\n"
            "    names: t.StrSequence = ()\n"
        )
        transformer = FlextInfraRefactorProjectAliasMigrator(
            file_path=Path("/workspace/flext-ldif/src/flext_ldif/_models/base.py"),
        )
        updated, changes = transformer.apply_to_source(source)
        assert updated == source
        assert changes == []

    def test_keeps_core_aliases_inside_public_facade_file(self) -> None:
        source = (
            "from __future__ import annotations\n\n"
            "from flext_core import c\n\n"
            "class FlextObservabilityConstants(c):\n"
            "    class Observability:\n"
            "        VALUE = 1\n\n"
            "c = FlextObservabilityConstants\n"
        )
        transformer = FlextInfraRefactorProjectAliasMigrator(
            file_path=Path(
                "/workspace/flext-observability/src/flext_observability/constants.py",
            ),
        )
        updated, changes = transformer.apply_to_source(source)
        assert updated == source
        assert changes == []
