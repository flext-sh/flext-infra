"""Behavior tests for composing a facade from its declared family providers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
from typing import TYPE_CHECKING, ClassVar

from flext_infra.workspace import FlextInfraRopeWorkspace
from tests import c, tm, u

pytestmark = c.Tests.MARK.slow

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraFacadeComponentSource:
    """Validate that the composed facade is built from the facade's own source."""

    @staticmethod
    def test_nested_namespace_from_family_keeps_facade_source(
        tmp_path: Path,
    ) -> None:
        """A nested namespace whose base lives in the family stays the facade's.

        Premise: inspecting the namespace's family bases must not rebind the
        facade resource. When it did, the composed text came from the last
        inspected provider module while the class layout came from the facade,
        splicing the facade header into the provider body.
        """
        root, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-sample",
            package_name="flext_sample",
        )
        family = u.Infra.facade_family_declared_by(c.Infra.CONSTANTS_PY)
        directory = package / family.directory
        (package / c.Infra.INIT_PY).write_text("", encoding=c.DEFAULT_ENCODING)
        (directory / c.Infra.INIT_PY).parent.mkdir(parents=True, exist_ok=True)
        (directory / c.Infra.INIT_PY).write_text(
            "from flext_sample_constants import FlextSampleConstantsBase\n"
            "__all__ = ['FlextSampleConstantsBase']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        (directory / "base.py").write_text(
            '"""Provider body that must never become the facade."""\n\n'
            "class FlextSampleConstantsBase:\n"
            "    PROVIDER_ONLY = 'provider-only-marker'\n"
            "    PADDING = (\n"
            + "".join(f"        'line-{index}',\n" for index in range(40))
            + "    )\n\n"
            "__all__ = ['FlextSampleConstantsBase']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        facade = package / c.Infra.CONSTANTS_PY
        facade.write_text(
            '"""Sample facade."""\n\n'
            "from flext_sample._constants import FlextSampleConstantsBase\n\n\n"
            "class FlextSampleConstants:\n"
            "    class Sample(FlextSampleConstantsBase):\n"
            "        pass\n\n\n"
            "c = FlextSampleConstants\n"
            "__all__ = ['FlextSampleConstants', 'c']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        with FlextInfraRopeWorkspace.open_workspace(root) as rope:
            rendered = tm.ok(
                u.Infra.facade_component_source(
                    rope.rope_project,
                    facade,
                    directory,
                    family=c.Infra.FacadeFamily.C,
                )
            )
        ast.parse(rendered)
        tm.that(rendered, has="class FlextSampleConstants")
        tm.that("provider-only-marker" in rendered, eq=False)

    @staticmethod
    def _sample_family(
        tmp_path: Path, parts: dict[str, str], facade: str
    ) -> tuple[Path, Path, Path]:
        """Write a ``flext_sample`` constants family and its facade.

        Returns:
            The workspace root, the family directory and the facade path.

        """
        root, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-sample",
            package_name="flext_sample",
        )
        family = u.Infra.facade_family_declared_by(c.Infra.CONSTANTS_PY)
        directory = package / family.directory
        (package / c.Infra.INIT_PY).write_text("", encoding=c.DEFAULT_ENCODING)
        directory.mkdir(parents=True, exist_ok=True)
        (directory / c.Infra.INIT_PY).write_text(
            "".join(
                f"from flext_sample._constants.{module} import {name}\n"
                for module, name in ((name.lower(), name) for name in parts)
            )
            + f"__all__ = {sorted(parts)!r}\n",
            encoding=c.DEFAULT_ENCODING,
        )
        for name, body in parts.items():
            (directory / f"{name.lower()}.py").write_text(
                '"""Sample part."""\n\n'
                "from typing import ClassVar\n\n\n"
                f"class {name}:\n{body}\n\n"
                f"__all__ = [{name!r}]\n",
                encoding=c.DEFAULT_ENCODING,
            )
        path = package / c.Infra.CONSTANTS_PY
        path.write_text(
            '"""Sample facade."""\n\n'
            "from flext_core import FlextConstants\n\n"
            "from flext_sample._constants import "
            + ", ".join(sorted(parts))
            + "\n\n\n"
            + facade
            + "\n\nc = FlextSampleConstants\n"
            "__all__ = ['FlextSampleConstants', 'c']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        return root, directory, path

    @staticmethod
    def _render(root: Path, directory: Path, facade: Path) -> str:
        """Render the facade once through the public composition owner.

        Returns:
            The rendered facade source.

        """
        with FlextInfraRopeWorkspace.open_workspace(root) as rope:
            return tm.ok(
                u.Infra.facade_component_source(
                    rope.rope_project, facade, directory, family=c.Infra.FacadeFamily.C
                )
            )

    @staticmethod
    def _class_bases(source: str, *path: str) -> list[str]:
        """Read the base expressions of a (nested) class.

        Returns:
            The class's base expressions in declaration order.

        """
        body: list[ast.stmt] = ast.parse(source).body
        node: ast.ClassDef | None = None
        for name in path:
            node = next(
                item
                for item in body
                if isinstance(item, ast.ClassDef) and item.name == name
            )
            body = node.body
        return [ast.unparse(base) for base in tm.not_none(node).bases]

    PARTS: ClassVar[dict[str, str]] = {
        "FlextSampleConstantsBase": "    MARKER: ClassVar[str] = 'base'\n",
        "FlextSampleConstantsExtra": "    EXTRA: ClassVar[str] = 'extra'\n",
    }

    @c.Tests.MARK.parametrize(
        "facade",
        [
            (
                "class FlextSampleConstants(\n"
                "    FlextConstants,\n"
                "    # authored note between bases\n"
                "    FlextSampleConstantsBase,\n"
                "    FlextSampleConstantsExtra,\n"
                "):\n"
                '    """Sample constants."""'
            ),
            (
                "class FlextSampleConstants(\n"
                "    FlextConstants, FlextSampleConstantsBase\n"
                "):\n"
                '    """Sample constants."""\n\n'
                "    class Sample(\n"
                "        FlextSampleConstantsExtra,\n"
                "    ):\n"
                '        """Domain namespace."""'
            ),
            'class FlextSampleConstants(FlextConstants):\n    """Sample constants."""',
            (
                "class FlextSampleConstants(\n"
                "    FlextConstants,\n"
                "    FlextSampleConstantsBase,\n"
                "    FlextSampleConstantsExtra,\n"
                "):\n"
                '    """Sample constants."""\n\n'
                "    class Sample(\n"
                "        FlextSampleConstantsBase,\n"
                "        FlextSampleConstantsExtra,\n"
                "    ):\n"
                '        """Domain namespace."""'
            ),
        ],
        ids=["flat", "root-and-multiline-nested", "family-only", "trailing-run"],
    )
    def test_own_parts_compose_the_nested_domain_namespace(
        self, tmp_path: Path, facade: str
    ) -> None:
        """Own parts never flatten onto a facade composed on an upstream family.

        Premise (flext-0in0k.32): with no inherited namespace the planner
        composed the package parts on the outer class, so ``c.Sample`` did
        not exist; a facade with parts on both the root and the nested class
        composed them twice. The outer class keeps only the upstream family,
        the nested domain class composes every part, and a second render of
        the generated facade is byte-identical.
        """
        root, directory, path = self._sample_family(tmp_path, self.PARTS, facade)
        rendered = self._render(root, directory, path)
        tm.that(
            self._class_bases(rendered, "FlextSampleConstants"), eq=["FlextConstants"]
        )
        tm.that(
            sorted(self._class_bases(rendered, "FlextSampleConstants", "Sample")),
            eq=sorted(self.PARTS),
        )
        path.write_text(rendered, encoding=c.DEFAULT_ENCODING)
        tm.that(self._render(root, directory, path), eq=rendered)

    def test_holder_part_composes_its_domain_class(self, tmp_path: Path) -> None:
        """A part that only holds the domain class contributes ``Part.<Domain>``.

        Composing the holder whole would nest the namespace twice
        (``c.Sample.Sample.X``); its own domain class keeps ``c.Sample.X``.
        """
        root, directory, path = self._sample_family(
            tmp_path,
            {
                "FlextSampleConstantsBase": "    class Sample:\n"
                "        MARKER: ClassVar[str] = 'held'\n"
            },
            "class FlextSampleConstants(FlextConstants, FlextSampleConstantsBase):\n"
            '    """Sample constants."""',
        )
        rendered = self._render(root, directory, path)
        tm.that(
            self._class_bases(rendered, "FlextSampleConstants", "Sample"),
            eq=["FlextSampleConstantsBase.Sample"],
        )

    def test_earlier_generated_header_is_rewritten(self, tmp_path: Path) -> None:
        """A facade still carrying the pre-ADR-037 header gets the current one.

        Premise: the facade kept its whole prefix, so a header naming the
        retired ``make gen`` verb survived every ``make check``. The marker
        keeps the file generated; the line is rewritten to
        ``c.Infra.AUTOGEN_HEADER`` and a second render is byte-identical.
        """
        root, directory, path = self._sample_family(
            tmp_path,
            self.PARTS,
            "class FlextSampleConstants(FlextConstants, "
            + ", ".join(sorted(self.PARTS))
            + "):\n"
            '    """Sample constants."""',
        )
        path.write_text(
            f"{c.Infra.AUTOGEN_MARKER}Regenerate with: make gen\n"
            + path.read_text(encoding=c.DEFAULT_ENCODING),
            encoding=c.DEFAULT_ENCODING,
        )
        rendered = self._render(root, directory, path)
        tm.that(rendered.partition("\n")[0], eq=c.Infra.AUTOGEN_HEADER)
        path.write_text(rendered, encoding=c.DEFAULT_ENCODING)
        tm.that(self._render(root, directory, path), eq=rendered)

    def test_part_declaring_the_domain_beside_members_composes_whole(
        self, tmp_path: Path
    ) -> None:
        """A part with a real domain class beside other members composes whole.

        ``flext-tap-ldap`` precedent: consumers read ``p.TapLdap.TapLdap``
        and ``p.TapLdap.Root`` through the nested namespace.
        """
        root, directory, path = self._sample_family(
            tmp_path,
            {
                "FlextSampleConstantsBase": "    OTHER: ClassVar[str] = 'loose'\n\n"
                "    class Sample:\n"
                "        MARKER: ClassVar[str] = 'held'\n"
            },
            "class FlextSampleConstants(FlextConstants, FlextSampleConstantsBase):\n"
            '    """Sample constants."""',
        )
        rendered = self._render(root, directory, path)
        tm.that(
            self._class_bases(rendered, "FlextSampleConstants", "Sample"),
            eq=["FlextSampleConstantsBase"],
        )

    @staticmethod
    def test_upstream_base_keeps_comments_and_layout(
        tmp_path: Path,
    ) -> None:
        """Composing on an upstream family keeps its class name and the layout.

        Premise (flext-7snh0): the canonicalizer re-rendered the whole facade,
        dropping every comment. The upstream base stays its class name
        (ADR-028 Decision 10, ``facade-base-by-class-name``) and the authored
        domain namespace survives with its note.
        """
        root, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-sample",
            package_name="flext_sample",
        )
        family = u.Infra.facade_family_declared_by(c.Infra.CONSTANTS_PY)
        directory = package / family.directory
        (package / c.Infra.INIT_PY).write_text("", encoding=c.DEFAULT_ENCODING)
        directory.mkdir(parents=True, exist_ok=True)
        (directory / c.Infra.INIT_PY).write_text("", encoding=c.DEFAULT_ENCODING)
        facade = package / c.Infra.CONSTANTS_PY
        facade.write_text(
            '"""Sample facade."""\n\n'
            "from typing import ClassVar\n\n"
            "from flext_core import FlextConstants\n\n\n"
            "class FlextSampleConstants(FlextConstants):\n"
            "    # Authored note that must survive the canonical projection.\n"
            "    class Sample:\n"
            "        MARKER: ClassVar[str] = 'kept'\n\n\n"
            "c = FlextSampleConstants\n"
            "__all__ = ['FlextSampleConstants', 'c']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        with FlextInfraRopeWorkspace.open_workspace(root) as rope:
            rendered = tm.ok(
                u.Infra.facade_component_source(
                    rope.rope_project,
                    facade,
                    directory,
                    family=c.Infra.FacadeFamily.C,
                )
            )
        ast.parse(rendered)
        tm.that(rendered, has="# Authored note that must survive")
        tm.that(rendered, has="from flext_core import FlextConstants")
        tm.that(rendered, has="class FlextSampleConstants(FlextConstants):")
        tm.that(rendered, has="    class Sample:")
