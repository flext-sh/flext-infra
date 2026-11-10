"""Generated module-member and import-header rules rewrite module-object access.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from tests import c, p, tm, u


class TestsFlextInfraCodemodModuleMemberImportHeader:
    """A member reached through a child package object imports from the child."""

    @u.Tests.fixture
    @staticmethod
    def project_tree(
        tmp_path: Path, session_runtime: p.Tests.SessionRuntime
    ) -> tuple[Path, Path]:
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
        tm.ok(
            u.Tests.create_python_environment(
                repository,
                dependency_projects=u.Tests.python_dependency_projects(repository),
                session_runtime=session_runtime,
            )
        )
        return repository, package

    @staticmethod
    def _apply(repository: Path, sources: Path) -> None:
        """Stage the project's generated rules and utilities as make mod does."""
        with u.Infra.codemod_workspace_snapshot(repository) as snapshot:
            documents = {
                **u.Infra.codemod_module_member_rules(
                    snapshot,
                    repository,
                    u.Infra.codemod_package_export_facts(snapshot, repository),
                ),
                **u.Infra.codemod_import_header_rules(
                    snapshot,
                    repository,
                    u.Infra.codemod_workspace_export_facts(snapshot, repository),
                ),
            }
            utilities = {
                **u.Infra.codemod_own_package_utilities(snapshot, repository),
                **u.Infra.codemod_facade_package_utilities(snapshot, repository),
                **u.Infra.codemod_package_export_utilities(snapshot, repository),
            }
        catalog = repository.parent / "catalog"
        tm.ok(
            u.Cli.yaml_dump(
                catalog / "sgconfig.yml",
                {"ruleDirs": ["rules"], "utilDirs": ["utils"]},
            )
        )
        (catalog / "utils").mkdir(parents=True, exist_ok=True)
        for identity, rule in utilities.items():
            tm.ok(
                u.Cli.yaml_dump(
                    catalog / "utils" / f"{identity}.yml",
                    u.Infra.codemod_native_utility_document(identity, rule),
                )
            )
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
        project_tree: tuple[Path, Path],
    ) -> None:
        """``gates.DemoGate`` becomes ``DemoGate`` imported from the child package."""
        repository, package = project_tree
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
    def test_provider_root_object_read_imports_the_name(
        project_tree: tuple[Path, Path],
    ) -> None:
        """``flext_core.FlextLazyMember`` becomes ``FlextLazyMember`` from its root."""
        repository, package = project_tree
        consumer = package / "provider.py"
        consumer.write_text(
            "from __future__ import annotations\n\n"
            "import flext_core\n\n\n"
            "class Probe:\n"
            '    """Probe."""\n\n'
            "    member: flext_core.FlextLazyMember | None = None\n",
            encoding=c.DEFAULT_ENCODING,
        )
        TestsFlextInfraCodemodModuleMemberImportHeader._apply(repository, package)
        rewritten = consumer.read_text(encoding=c.DEFAULT_ENCODING)
        tm.that(
            rewritten,
            has=[
                "from flext_core import FlextLazyMember\n",
                "member: FlextLazyMember | None = None",
            ],
        )
        tm.that(rewritten, lacks="flext_core.FlextLazyMember")

    @staticmethod
    def test_generic_annotation_imports_its_free_member(
        project_tree: tuple[Path, Path],
    ) -> None:
        """Generic arguments use names rather than declaring type parameters."""
        repository, package = project_tree
        consumer = package / "annotation.py"
        consumer.write_text(
            "from __future__ import annotations\n\n"
            f"from {package.name} import gates\n\n"
            "class Probe:\n    values: list[gates.DemoGate]\n",
            encoding=c.DEFAULT_ENCODING,
        )
        TestsFlextInfraCodemodModuleMemberImportHeader._apply(repository, package)
        tm.that(
            consumer.read_text(encoding=c.DEFAULT_ENCODING),
            has=[
                f"from {package.name}.gates import DemoGate\n",
                "values: list[DemoGate]",
            ],
        )

    @staticmethod
    def test_type_parameter_bound_imports_its_free_member(
        project_tree: tuple[Path, Path],
    ) -> None:
        """A PEP 695 bound is a use while its declared parameter is a binding."""
        repository, package = project_tree
        consumer = package / "bound.py"
        consumer.write_text(
            "from __future__ import annotations\n\n"
            f"from {package.name} import gates\n\n"
            "class Probe[T: gates.DemoGate]:\n    value: T\n",
            encoding=c.DEFAULT_ENCODING,
        )
        TestsFlextInfraCodemodModuleMemberImportHeader._apply(repository, package)
        tm.that(
            consumer.read_text(encoding=c.DEFAULT_ENCODING),
            has=[
                f"from {package.name}.gates import DemoGate\n",
                "class Probe[T: DemoGate]",
            ],
        )

    @staticmethod
    def test_header_preserves_names_bound_by_another_owner(
        project_tree: tuple[Path, Path],
    ) -> None:
        """Importing a free name never also imports an existing local homonym."""
        repository, package = project_tree
        (package / "gates" / c.Infra.INIT_PY).write_text(
            "from .base import DemoGate\n\n"
            "class Existing:\n    pass\n\n"
            '__all__ = ("DemoGate", "Existing")\n',
            encoding=c.DEFAULT_ENCODING,
        )
        consumer = package / "binding.py"
        consumer.write_text(
            "from __future__ import annotations\n\n"
            f"from {package.name} import gates\n\n"
            "class Existing:\n    pass\n\n"
            "class Probe:\n"
            "    value: gates.DemoGate\n"
            "    existing: Existing\n",
            encoding=c.DEFAULT_ENCODING,
        )
        TestsFlextInfraCodemodModuleMemberImportHeader._apply(repository, package)
        rewritten = consumer.read_text(encoding=c.DEFAULT_ENCODING)
        tm.that(rewritten, has=f"from {package.name}.gates import DemoGate\n")
        tm.that(rewritten, lacks=f"from {package.name}.gates import Existing")

    @staticmethod
    def test_local_homonym_of_the_child_is_never_rewritten(
        project_tree: tuple[Path, Path],
    ) -> None:
        """A module rebinding the child's name locally keeps its attribute access."""
        repository, package = project_tree
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
