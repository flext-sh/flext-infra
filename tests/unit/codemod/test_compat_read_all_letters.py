"""Compat-marked names of any facade letter are admitted, reported and rewired.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.codemod import FlextInfraModGateEngine
from flext_infra.workspace import FlextInfraRopeWorkspace
from tests import c, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraCodemodCompatReadAllLetters:
    """A ``u.X`` pass-through marked for ``m.X`` keeps working until rewired."""

    @staticmethod
    def _project(tmp_path: Path) -> tuple[Path, Path, str]:
        """Write a package whose ``u`` marks ``u.Box`` as moved to ``m.Box``.

        Returns:
            The project root, the consumer module and the package name.

        """
        package_name = f"compat_{tmp_path.name.replace('-', '_')}"
        project_name = package_name.replace("_", "-")
        root = u.Tests.mk_project(
            tmp_path,
            project_name,
            pyproject=f'[project]\nname = "{project_name}"\nversion = "0.1.0"\n',
            with_src=True,
        )
        package = root / c.Infra.DEFAULT_SRC_DIR / package_name
        sources = {
            package / c.Infra.INIT_PY: (
                f"from {package_name}.models import m\n"
                f"from {package_name}.utilities import u\n\n"
                "__all__ = ['m', 'u']\n"
            ),
            package / "models.py": (
                "class SampleModels:\n"
                "    class Box:\n"
                "        pass\n\n\n"
                "m = SampleModels\n\n"
                "__all__ = ['SampleModels', 'm']\n"
            ),
            package / "utilities.py": (
                "from __future__ import annotations\n\n"
                "from typing import Annotated, ClassVar\n"
                "from warnings import deprecated\n\n"
                f"from {package_name}.models import m\n\n\n"
                "class SampleUtilities:\n"
                "    Box: Annotated[\n"
                "        ClassVar,\n"
                '        deprecated("compat: u.Box -> m.Box; fix: read through m"),\n'
                "    ] = m.Box\n\n"
                "    @staticmethod\n"
                "    def label() -> str:\n"
                "        return 'sample'\n\n\n"
                "u = SampleUtilities\n\n"
                "__all__ = ['SampleUtilities', 'u']\n"
            ),
            package / "consumer.py": (
                f"from {package_name} import m, u\n\nBOX = (m, u.Box)\n"
            ),
        }
        for path, content in sources.items():
            tm.ok(u.Cli.ensure_dir(path.parent))
            tm.ok(u.Cli.atomic_write_text_file(path, content))
        return root, package / "consumer.py", package_name

    def test_marked_pass_through_is_admitted_utility_storage(
        self, tmp_path: Path
    ) -> None:
        """``Annotated[ClassVar, marker]`` qualifies storage like ``ClassVar``."""
        root, consumer, _package_name = self._project(tmp_path)
        utilities = consumer.parent / "utilities.py"
        with FlextInfraRopeWorkspace.open_workspace(root) as workspace:
            resource = tm.not_none(workspace.resource(utilities))
            module = u.Infra.require_source_module(
                workspace.rope_project.get_pymodule(resource)
            )
            owner = module.get_attribute("SampleUtilities").get_object()
            tm.that(u.Infra.py_class(owner), eq=True)
            if u.Infra.py_class(owner):
                tm.that(
                    u.Infra.utility_namespace_declaration(
                        workspace.rope_project, owner
                    ),
                    eq=True,
                )

    def test_compat_rule_rewires_the_utilities_read_to_models(
        self, tmp_path: Path
    ) -> None:
        """The one compat rule carries ``u.Box`` with its ``m.Box`` rewrite."""
        root, _consumer, package_name = self._project(tmp_path)
        rule_id = c.Infra.CODEMOD_GENERATED_ID_SEPARATOR.join((
            c.Infra.CODEMOD_COMPAT_READ_SHAPE,
            package_name,
        ))
        with (
            tm.scope(python_paths=[str(root / c.Infra.DEFAULT_SRC_DIR)]),
            u.Infra.codemod_workspace_snapshot(root) as snapshot,
        ):
            rules = u.Infra.codemod_compat_rules(snapshot, root)
        tm.that(tuple(rules), eq=(rule_id,))
        tm.that(
            rules[rule_id]["rewriters"],
            eq=[
                {
                    "id": "to-0",
                    "rule": u.Infra.codemod_exact_names_rule(("u.Box",)),
                    "fix": "m.Box",
                }
            ],
        )

    def test_marked_read_is_reported_and_rewired_to_its_owner(
        self, tmp_path: Path
    ) -> None:
        """One compat rule reports ``u.Box`` and rewrites it to ``m.Box``."""
        root, consumer, package_name = self._project(tmp_path)
        rule_id = c.Infra.CODEMOD_GENERATED_ID_SEPARATOR.join((
            c.Infra.CODEMOD_COMPAT_READ_SHAPE,
            package_name,
        ))
        with tm.scope(python_paths=[str(root / c.Infra.DEFAULT_SRC_DIR)]):
            report = tm.ok(
                FlextInfraModGateEngine.scan(
                    root, fix=True, selection=(rule_id,), source_files=(consumer,)
                )
            )
        tm.that({row.rule_id for row in report.entries}, eq={rule_id})
        tm.that(
            consumer.read_text(encoding=c.DEFAULT_ENCODING),
            eq=f"from {package_name} import m, u\n\nBOX = (m, m.Box)\n",
        )


__all__: list[str] = ["TestsFlextInfraCodemodCompatReadAllLetters"]
