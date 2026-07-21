"""Tests for migrate-to-mro automation."""

from __future__ import annotations

from pathlib import Path

import pytest
from flext_tests import tm

from tests import u
from flext_infra.refactor.migrate_to_class_mro import (
    FlextInfraRefactorMigrateToClassMRO,
)


class TestsFlextInfraRefactorInfraRefactorMigrateToClassMro:
    """Behavior contract for test_infra_refactor_migrate_to_class_mro."""

    def test_migrate_to_mro_moves_constant_and_rewrites_reference(
        self, tmp_path: Path
    ) -> None:
        project_root = tmp_path / "sample"
        src_pkg = project_root / "src" / "sample_pkg"
        src_pkg.mkdir(parents=True)
        _ = (project_root / "pyproject.toml").write_text(
            "[project]\nname='sample'\n", encoding="utf-8"
        )
        _ = (project_root / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
        _ = (src_pkg / "__init__.py").write_text("", encoding="utf-8")
        _ = (src_pkg / "constants.py").write_text(
            "from __future__ import annotations\nfrom typing import Final\n\nVALUE: Final[int] = 42\n\nclass SampleConstants:\n    pass\n\nc = SampleConstants\n",
            encoding="utf-8",
        )
        _ = (src_pkg / "consumer.py").write_text(
            "from sample_pkg.constants import VALUE\n\nresult = VALUE\n",
            encoding="utf-8",
        )
        report = FlextInfraRefactorMigrateToClassMRO(workspace_root=project_root).run(
            target="constants", apply=True
        )
        constants_source = (src_pkg / "constants.py").read_text(encoding="utf-8")
        consumer_source = (src_pkg / "consumer.py").read_text(encoding="utf-8")
        tm.that(report.errors, empty=True)
        tm.that(
            "VALUE: Final[int] = 42"
            not in constants_source.split("class SampleConstants:")[0],
            eq=True,
        )
        tm.that(
            constants_source.split("class SampleConstants:", maxsplit=1)[1],
            has="VALUE: Final[int] = 42",
        )
        # Consumer import rewritten: VALUE → c.VALUE with facade alias import.
        tm.that(consumer_source, has="from sample_pkg.constants import c")
        tm.that(consumer_source, has="result = c.VALUE")

    def test_migrate_to_mro_inlines_alias_constant_into_constants_class(
        self, tmp_path: Path
    ) -> None:
        project_root = tmp_path / "sample"
        src_pkg = project_root / "src" / "sample_pkg"
        src_pkg.mkdir(parents=True)
        _ = (project_root / "pyproject.toml").write_text(
            "[project]\nname='sample'\n", encoding="utf-8"
        )
        _ = (project_root / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
        _ = (src_pkg / "__init__.py").write_text("", encoding="utf-8")
        _ = (src_pkg / "constants.py").write_text(
            "from __future__ import annotations\nfrom typing import Final\n\n_TIMEOUT: Final[int] = 30\n\nclass SampleConstants:\n    TIMEOUT = _TIMEOUT\n\nc = SampleConstants\n",
            encoding="utf-8",
        )
        _ = (src_pkg / "consumer.py").write_text(
            "from sample_pkg.constants import _TIMEOUT\n\nvalue = _TIMEOUT\n",
            encoding="utf-8",
        )
        report = FlextInfraRefactorMigrateToClassMRO(workspace_root=project_root).run(
            target="constants", apply=True
        )
        constants_source = (src_pkg / "constants.py").read_text(encoding="utf-8")
        consumer_source = (src_pkg / "consumer.py").read_text(encoding="utf-8")
        tm.that(report.errors, empty=True)
        tm.that(
            "_TIMEOUT: Final[int] = 30"
            not in constants_source.split("class SampleConstants:", maxsplit=1)[0],
            eq=True,
        )
        tm.that(constants_source, has="TIMEOUT: Final[int] = 30")
        tm.that("TIMEOUT = _TIMEOUT" not in constants_source, eq=True)
        # Consumer import rewritten: _TIMEOUT → c.TIMEOUT with facade alias import.
        tm.that(consumer_source, has="from sample_pkg.constants import c")
        tm.that(consumer_source, has="value = c.TIMEOUT")

    def test_migrate_to_mro_normalizes_facade_alias_to_c(self, tmp_path: Path) -> None:
        project_root = tmp_path / "sample"
        src_pkg = project_root / "src" / "sample_pkg"
        src_pkg.mkdir(parents=True)
        _ = (project_root / "pyproject.toml").write_text(
            "[project]\nname='sample'\n", encoding="utf-8"
        )
        _ = (project_root / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
        _ = (src_pkg / "__init__.py").write_text("", encoding="utf-8")
        _ = (src_pkg / "constants.py").write_text(
            "from __future__ import annotations\nfrom typing import Final\n\nVALUE: Final[int] = 42\n\nclass SampleConstants:\n    pass\n\nc = SampleConstants\n",
            encoding="utf-8",
        )
        _ = (src_pkg / "consumer.py").write_text(
            "from sample_pkg.constants import VALUE\nfrom sample_pkg.constants import c as constants\n\nresult = VALUE\n",
            encoding="utf-8",
        )
        report = FlextInfraRefactorMigrateToClassMRO(workspace_root=project_root).run(
            target="constants", apply=True
        )
        consumer_source = (src_pkg / "consumer.py").read_text(encoding="utf-8")
        tm.that(report.errors, empty=True)
        # Consumer import rewritten: VALUE → c.VALUE with facade alias import.
        tm.that(consumer_source, has="from sample_pkg.constants import c")
        tm.that(consumer_source, has="result = c.VALUE")

    def test_migrate_to_mro_rejects_unknown_target(self, tmp_path: Path) -> None:
        project_root = tmp_path / "sample"
        project_root.mkdir(parents=True)
        migrator = FlextInfraRefactorMigrateToClassMRO(workspace_root=project_root)
        with pytest.raises(ValueError, match="unsupported target"):
            _ = migrator.run(target="unknown", apply=False)

    def test_migrate_typings_rewrites_references_with_t_alias(
        self, tmp_path: Path
    ) -> None:
        project_root = tmp_path / "sample"
        src_pkg = project_root / "src" / "sample_pkg"
        src_pkg.mkdir(parents=True)
        _ = (project_root / "pyproject.toml").write_text(
            "[project]\nname='sample'\n", encoding="utf-8"
        )
        _ = (project_root / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
        _ = (src_pkg / "__init__.py").write_text("", encoding="utf-8")
        _ = (src_pkg / "typings.py").write_text(
            "from __future__ import annotations\nfrom typing import TypeAlias\n\nValueType: TypeAlias = str | int\n\nclass SampleTypes:\n    pass\n\nt = SampleTypes\n",
            encoding="utf-8",
        )
        _ = (src_pkg / "consumer.py").write_text(
            "from sample_pkg.typings import ValueType\n\nvalue: ValueType = 1\n",
            encoding="utf-8",
        )
        report = FlextInfraRefactorMigrateToClassMRO(workspace_root=project_root).run(
            target="typings", apply=True
        )
        typings_source = (src_pkg / "typings.py").read_text(encoding="utf-8")
        consumer_source = (src_pkg / "consumer.py").read_text(encoding="utf-8")
        tm.that(report.errors, empty=True)
        tm.that(
            "ValueType: TypeAlias = str | int"
            not in typings_source.split("class SampleTypes:", maxsplit=1)[0],
            eq=True,
        )
        tm.that(
            typings_source.split("class SampleTypes:", maxsplit=1)[1],
            has="ValueType: TypeAlias = str | int",
        )
        # Consumer import rewritten: ValueType → t.ValueType with facade alias import.
        tm.that(consumer_source, has="from sample_pkg.typings import t")
        tm.that(consumer_source, has="value: t.ValueType = 1")

    def test_migrate_protocols_rewrites_references_with_p_alias(
        self, tmp_path: Path
    ) -> None:
        project_root = tmp_path / "sample"
        src_pkg = project_root / "src" / "sample_pkg"
        src_pkg.mkdir(parents=True)
        _ = (project_root / "pyproject.toml").write_text(
            "[project]\nname='sample'\n", encoding="utf-8"
        )
        _ = (project_root / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
        _ = (src_pkg / "__init__.py").write_text("", encoding="utf-8")
        _ = (src_pkg / "protocols.py").write_text(
            "from __future__ import annotations\nfrom typing import Protocol, runtime_checkable\n\nclass SampleProtocols:\n    pass\n\n@runtime_checkable\nclass Greeter(Protocol):\n    def greet(self) -> str:\n        ...\n\np = SampleProtocols",
            encoding="utf-8",
        )
        _ = (src_pkg / "consumer.py").write_text(
            "from sample_pkg.protocols import Greeter\n\ndef call_greet(protocol: Greeter) -> str:\n    return protocol.greet()",
            encoding="utf-8",
        )
        report = FlextInfraRefactorMigrateToClassMRO(workspace_root=project_root).run(
            target="protocols", apply=True
        )
        protocols_source = (src_pkg / "protocols.py").read_text(encoding="utf-8")
        consumer_source = (src_pkg / "consumer.py").read_text(encoding="utf-8")
        tm.that(report.errors, empty=True)
        tm.that(
            "class Greeter(Protocol):"
            not in protocols_source.split("class SampleProtocols:", maxsplit=1)[0],
            eq=True,
        )
        tm.that(
            "@runtime_checkable"
            not in protocols_source.split("class SampleProtocols:", maxsplit=1)[0],
            eq=True,
        )
        tm.that(
            protocols_source.split("class SampleProtocols:", maxsplit=1)[1],
            has="@runtime_checkable\n    class Greeter(Protocol):",
        )
        # Consumer import rewritten: Greeter → p.Greeter with facade alias import.
        tm.that(consumer_source, has="from sample_pkg.protocols import p")
        tm.that(consumer_source, has="def call_greet(protocol: p.Greeter) -> str:")

    def test_discover_project_roots_without_nested_git_dirs(
        self, tmp_path: Path
    ) -> None:
        workspace_root = tmp_path / "workspace"
        workspace_root.mkdir(parents=True)

        project_root = workspace_root / "proj-a"
        project_root.mkdir(parents=True)
        _ = (project_root / "pyproject.toml").write_text(
            "[project]\nname='proj-a'\n", encoding="utf-8"
        )
        _ = (project_root / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
        (project_root / "src").mkdir(parents=True)

        discovered = u.Infra.discover_project_roots(
            workspace_root=workspace_root
        )
        tm.that(discovered, eq=[project_root])

    def test_mro_scan_respects_namespace_scan_dirs_src_only(
        self, tmp_path: Path
    ) -> None:
        project_root = tmp_path / "sample"
        src_pkg = project_root / "src" / "sample_pkg"
        tests_dir = project_root / "tests"
        src_pkg.mkdir(parents=True)
        tests_dir.mkdir(parents=True)
        _ = (project_root / "pyproject.toml").write_text(
            "[project]\nname='sample'\n\n[tool.flext.namespace]\nscan_dirs = ['src']\n",
            encoding="utf-8",
        )
        _ = (project_root / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
        _ = (src_pkg / "constants.py").write_text(
            "from __future__ import annotations\n\nSRC_VALUE = 1\n\nclass SampleConstants:\n    pass\n\nc = SampleConstants\n",
            encoding="utf-8",
        )
        _ = (tests_dir / "constants.py").write_text(
            "from __future__ import annotations\n\nTEST_VALUE = 2\n\nclass TestConstants:\n    pass\n\nc = TestConstants\n",
            encoding="utf-8",
        )

        reports, scanned = u.Infra.scan_workspace(
            workspace_root=project_root, target="constants"
        )
        report_files = {
            Path(report.file).relative_to(project_root).as_posix() for report in reports
        }

        tm.that(scanned, eq=1)
        tm.that(report_files, eq={"src/sample_pkg/constants.py"})

    def test_migrate_to_mro_moves_manual_uppercase_assignment(
        self, tmp_path: Path
    ) -> None:
        project_root = tmp_path / "sample"
        src_pkg = project_root / "src" / "sample_pkg"
        src_pkg.mkdir(parents=True)
        _ = (project_root / "pyproject.toml").write_text(
            "[project]\nname='sample'\n", encoding="utf-8"
        )
        _ = (project_root / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
        _ = (src_pkg / "__init__.py").write_text("", encoding="utf-8")
        _ = (src_pkg / "constants.py").write_text(
            "from __future__ import annotations\n\nVALUE = 42\n\nclass SampleConstants:\n    pass\n\nc = SampleConstants\n",
            encoding="utf-8",
        )
        _ = (src_pkg / "consumer.py").write_text(
            "from sample_pkg.constants import VALUE\n\nresult = VALUE\n",
            encoding="utf-8",
        )
        report = FlextInfraRefactorMigrateToClassMRO(workspace_root=project_root).run(
            target="constants", apply=True
        )
        constants_source = (src_pkg / "constants.py").read_text(encoding="utf-8")
        consumer_source = (src_pkg / "consumer.py").read_text(encoding="utf-8")
        tm.that(report.errors, empty=True)
        tm.that(
            "VALUE = 42" not in constants_source.split("class SampleConstants:")[0],
            eq=True,
        )
        tm.that(
            constants_source.split("class SampleConstants:", maxsplit=1)[1],
            has="VALUE = 42",
        )
        # Consumer import rewritten: VALUE → c.VALUE with facade alias import.
        tm.that(consumer_source, has="from sample_pkg.constants import c")
        tm.that(consumer_source, has="result = c.VALUE")

    def test_migrate_to_mro_is_idempotent_on_second_run(self, tmp_path: Path) -> None:
        """A second consecutive apply run must be a true no-op (census delta 0).

        Regression for the all-or-nothing SafetyManager rollback: converged
        files stay committed, so once a constant lives inside the facade class
        it is no longer a candidate and re-running produces zero migrations.
        """
        project_root = tmp_path / "sample"
        src_pkg = project_root / "src" / "sample_pkg"
        src_pkg.mkdir(parents=True)
        _ = (project_root / "pyproject.toml").write_text(
            "[project]\nname='sample'\n", encoding="utf-8"
        )
        _ = (project_root / "Makefile").write_text("all:\n\t@true\n", encoding="utf-8")
        _ = (src_pkg / "__init__.py").write_text("", encoding="utf-8")
        _ = (src_pkg / "constants.py").write_text(
            "from __future__ import annotations\nfrom typing import Final\n\nVALUE: Final[int] = 42\n\nclass SampleConstants:\n    pass\n\nc = SampleConstants\n",
            encoding="utf-8",
        )
        _ = (src_pkg / "consumer.py").write_text(
            "from sample_pkg.constants import VALUE\n\nresult = VALUE\n",
            encoding="utf-8",
        )
        service = FlextInfraRefactorMigrateToClassMRO(workspace_root=project_root)
        first = service.run(target="constants", apply=True)
        tm.that(first.errors, empty=True)
        tm.that(len(first.migrations) >= 1, eq=True)
        second = service.run(target="constants", apply=True)
        tm.that(second.errors, empty=True)
        tm.that(len(second.migrations), eq=0)
        tm.that(len(second.rewrites), eq=0)
        tm.that(second.remaining_violations, eq=0)
