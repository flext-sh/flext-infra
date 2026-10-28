"""Generated module-member and import-header rules rewrite module-object access.

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

from pathlib import Path

from tests import c, tm, u


class TestsFlextInfraCodemodModuleMemberImportHeader:
    """A member reached through a child package object imports from the child."""

    @staticmethod
    def _project(tmp_path: Path) -> tuple[Path, Path]:
        """Build a project whose child package publishes one class.

        Returns:
            The repository root and the package root.

        """
        repository, package = u.Tests.create_lazy_init_workspace(tmp_path)
        gates = package / "gates"
        gates.mkdir()
        (gates / "base.py").write_text(
            'class DemoGate:\n    """Gate."""\n\n__all__ = ["DemoGate"]\n',
            encoding=c.DEFAULT_ENCODING,
        )
        (gates / c.Infra.INIT_PY).write_text(
            '"""Gates."""\n\nfrom .base import DemoGate\n\n__all__ = ("DemoGate",)\n',
            encoding=c.DEFAULT_ENCODING,
        )
        return repository, package

    @staticmethod
    def _apply(repository: Path, sources: Path) -> None:
        """Stage the project's generated rules natively and apply them twice."""
        with u.Infra.codemod_workspace_snapshot(repository) as snapshot:
            facts = u.Infra.codemod_package_export_facts(snapshot, repository)
            documents = {
                **u.Infra.codemod_module_member_rules(snapshot, repository, facts),
                **u.Infra.codemod_import_header_rules(snapshot, repository, facts),
            }
        catalog = repository.parent / "catalog"
        tm.ok(
            u.Cli.yaml_dump(
                catalog / "sgconfig.yml",
                {"ruleDirs": ["rules"], "utilDirs": ["utils"]},
            )
        )
        (catalog / "utils").mkdir(parents=True, exist_ok=True)
        for identity, document in documents.items():
            tm.ok(u.Cli.yaml_dump(catalog / "rules" / f"{identity}.yml", document))
        for _pass in range(2):
            tm.ok(
                u.Cli.capture([
                    c.Infra.SG,
                    "scan",
                    "-c",
                    str(catalog / "sgconfig.yml"),
                    "--update-all",
                    str(sources),
                ])
            )

    @staticmethod
    def test_member_and_header_rewrite_a_child_package_object(
        tmp_path: Path,
    ) -> None:
        """``gates.DemoGate`` becomes ``DemoGate`` imported from the child package."""
        repository, package = TestsFlextInfraCodemodModuleMemberImportHeader._project(
            tmp_path
        )
        consumer = package / "consumer.py"
        consumer.write_text(
            "from __future__ import annotations\n\n"
            f"from {package.name} import gates\n\n\n"
            "class Probe(gates.DemoGate):\n"
            '    """Probe."""\n\n'
            "    other: gates.DemoGate | None = None\n",
            encoding=c.DEFAULT_ENCODING,
        )
        TestsFlextInfraCodemodModuleMemberImportHeader._apply(repository, package)
        rewritten = consumer.read_text(encoding=c.DEFAULT_ENCODING)
        tm.that(
            rewritten,
            has=[
                f"from {package.name}.gates import DemoGate\n",
                "class Probe(DemoGate):",
                "other: DemoGate | None = None",
            ],
        )
        tm.that(rewritten, lacks="gates.DemoGate")

    @staticmethod
    def test_local_homonym_of_the_child_is_never_rewritten(tmp_path: Path) -> None:
        """A module rebinding the child's name locally keeps its attribute access."""
        repository, package = TestsFlextInfraCodemodModuleMemberImportHeader._project(
            tmp_path
        )
        consumer = package / "homonym.py"
        source = (
            "from __future__ import annotations\n\n"
            f"from {package.name} import gates\n\n\n"
            "def probe(gates: type[int]) -> int:\n"
            '    """Probe."""\n'
            "    return gates.DemoGate\n"
        )
        consumer.write_text(source, encoding=c.DEFAULT_ENCODING)
        TestsFlextInfraCodemodModuleMemberImportHeader._apply(repository, package)
        tm.that(consumer.read_text(encoding=c.DEFAULT_ENCODING), eq=source)


__all__: list[str] = ["TestsFlextInfraCodemodModuleMemberImportHeader"]
