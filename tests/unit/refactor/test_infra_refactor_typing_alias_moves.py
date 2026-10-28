"""Tests for refactor typing-alias namespace-move rewriting.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from flext_infra.workspace import FlextInfraRopeWorkspace
from tests import c, tm, u

if TYPE_CHECKING:
    from pathlib import Path

from tests import t


@pytest.mark.slow
class TestsFlextInfraRefactorInfraRefactorTypingAliasMoves:
    """Behavior contract for typing-alias namespace-move rewriting."""

    @staticmethod
    def _write_file(path: Path, content: str) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    @staticmethod
    def _non_module_files(package_root: Path) -> tuple[str, ...]:
        """Return files the rewrite left beside the package modules.

        Returns:
            Files the rewrite left beside the package modules.

        """
        return tuple(
            sorted(
                path.name
                for path in package_root.iterdir()
                if path.is_file() and path.suffix != ".py"
            ),
        )

    @classmethod
    def _build_project(cls, tmp_path: Path) -> t.Pair[Path, Path]:
        project_root = tmp_path / "flext-demo"
        package_root = project_root / "src" / "demo_pkg"
        cls._write_file(
            project_root / c.PYPROJECT_FILENAME,
            '[project]\nname = "flext-demo"\nversion = "0.1.0"\n',
        )
        cls._write_file(project_root / "Makefile", "check:\n\t@true\n")
        cls._write_file(
            package_root / "__init__.py",
            "from __future__ import annotations\n",
        )
        u.Tests.provision_checkout(project_root)
        return (project_root, package_root)

    def test_rewrite_manual_protocol_violations_uses_public_runtime_api(
        self,
        tmp_path: Path,
    ) -> None:
        """Test rewrite manual protocol violations uses public runtime api."""
        project_root, package_root = self._build_project(tmp_path)
        protocols_file = package_root / "protocols.py"
        source_file = package_root / "service.py"
        consumer_file = package_root / "consumer.py"
        self._write_file(
            protocols_file,
            "from __future__ import annotations\n\nclass ExistingProtocol:\n    pass\n",
        )
        self._write_file(
            source_file,
            (
                "from __future__ import annotations\n\n"
                "from typing import Protocol\n\n"
                "class External(Protocol):\n"
                "    def call(self) -> str:\n"
                '        """Return the external value."""\n'
                "        ...\n"
            ),
        )
        self._write_file(
            consumer_file,
            (
                "from __future__ import annotations\n\n"
                "from demo_pkg.service import External\n\n"
                "def use(dep: External) -> External:\n"
                "    return dep\n"
            ),
        )

        u.Infra.rewrite_manual_protocol_violations(
            project_root=project_root,
            py_files=[source_file, consumer_file],
            names_by_file={source_file: {"External"}},
        )

        tm.that(
            source_file.read_text(encoding="utf-8"),
            lacks="class External(Protocol):",
        )
        tm.that(
            consumer_file.read_text(encoding="utf-8"),
            has="from demo_pkg.protocols import External",
        )
        protocols_text = protocols_file.read_text(encoding="utf-8")
        tm.that(protocols_text, has="from typing import Protocol")
        tm.that(protocols_text, has="class External(Protocol):")
        tm.that(self._non_module_files(package_root), eq=())

    def test_rewrite_manual_typing_alias_violations_uses_public_runtime_api(
        self,
        tmp_path: Path,
    ) -> None:
        """Test rewrite manual typing alias violations uses public runtime api."""
        project_root, package_root = self._build_project(tmp_path)
        typings_file = package_root / "typings.py"
        source_file = package_root / "service.py"
        self._write_file(
            typings_file,
            "from __future__ import annotations\n\nTYPE_READY = True\n",
        )
        self._write_file(
            source_file,
            (
                "from __future__ import annotations\n\n"
                "from collections.abc import Mapping\n"
                "from typing import TypeAlias\n\n"
                "PayloadMap: TypeAlias = t.StrMapping\n"
                "value = 1\n"
            ),
        )

        u.Infra.rewrite_manual_typing_alias_violations(
            project_root=project_root,
            names_by_file={source_file: {"PayloadMap"}},
        )

        source_text = source_file.read_text(encoding="utf-8")
        typings_text = typings_file.read_text(encoding="utf-8")
        tm.that(source_text, lacks="PayloadMap: TypeAlias = t.StrMapping")
        tm.that(typings_text, has="type PayloadMap = t.StrMapping")
        tm.that(typings_text, lacks="from typing import TypeAlias")
        tm.that(typings_text, has="from flext_core import t")
        tm.that(self._non_module_files(package_root), eq=())

    def test_typing_alias_move_keeps_class_publications_pep613(
        self,
        tmp_path: Path,
    ) -> None:
        """A moved alias of a class keeps binding the class; aliases become PEP 695."""
        project_root, package_root = self._build_project(tmp_path)
        typings_file = package_root / "typings.py"
        source_file = package_root / "service.py"
        self._write_file(
            typings_file,
            "from __future__ import annotations\n\nTYPE_READY = True\n",
        )
        self._write_file(
            package_root / "owner.py",
            "from __future__ import annotations\n\n\nclass Owner:\n    value = 7\n",
        )
        self._write_file(
            source_file,
            (
                "from __future__ import annotations\n\n"
                "from typing import TypeAlias\n\n"
                "from demo_pkg.owner import Owner\n\n"
                "Published: TypeAlias = Owner\n"
                "Payload: TypeAlias = dict[str, int]\n"
                "value = 1\n"
            ),
        )

        u.Infra.rewrite_manual_typing_alias_violations(
            project_root=project_root,
            names_by_file={source_file: {"Published", "Payload"}},
        )

        typings_text = typings_file.read_text(encoding="utf-8")
        tm.that(typings_text, has="Published: TypeAlias = Owner")
        tm.that(typings_text, lacks="type Published")
        tm.that(typings_text, has="type Payload = dict[str, int]")

    @pytest.mark.parametrize(
        "declaration",
        [
            "type Alias = Literal['[']",
            "type Alias = Literal['value']  # [ unmatched comment",
            "type Alias[T] = tuple[T, Literal['[']]",
        ],
    )
    def test_typing_alias_statement_spans_preserve_runtime_and_unrelated_source(
        self,
        tmp_path: Path,
        declaration: str,
    ) -> None:
        """Move complete declarations, not brackets inside payloads or comments."""
        project_root, package_root = self._build_project(tmp_path)
        source_file = package_root / "service.py"
        self._write_file(
            source_file,
            "from __future__ import annotations\n\n"
            "from collections import deque as PublishedQueue\n"
            "from typing import Literal\n\n"
            f"{declaration}\n"
            "value = 'retained'\n"
            "def retained() -> str:\n"
            "    return value\n",
        )
        self._write_file(
            package_root / "consumer.py",
            "from demo_pkg.service import Alias, retained\nPublished = Alias\n"
            "__all__ = ('Published', 'retained')\n",
        )

        u.Infra.rewrite_manual_typing_alias_violations(
            project_root=project_root,
            names_by_file={source_file: {"Alias"}},
        )

        source = source_file.read_text(encoding="utf-8")
        target = (package_root / "typings.py").read_text(encoding="utf-8")
        tm.that(source, has='value = "retained"')
        tm.that(source, has="def retained() -> str:")
        tm.that(source, lacks="from typing import Literal")
        tm.that(source, lacks=declaration)
        tm.that(target, has="type Alias")
        tm.that(target, lacks="def retained")
        tm.that(
            u.Tests.run_lazy_init_probe(
                "from typing import get_args\n"
                "from demo_pkg import consumer, service, typings\n"
                "print(consumer.Published is typings.Alias)\n"
                "print(consumer.retained() == service.value == 'retained')\n"
                "print(service.PublishedQueue([1]).popleft() == 1)\n"
                "args = get_args(typings.Alias.__value__)\n"
                "print(get_args(args[-1]) == ('[',) "
                "if typings.Alias.__type_params__ else args in (('[',), ('value',)))\n",
                python_paths=(str(package_root.parent),),
            ),
            eq=["True"] * 4,
        )
        sources = {
            path: path.read_text(encoding="utf-8")
            for path in package_root.rglob("*.py")
        }
        u.Infra.rewrite_manual_typing_alias_violations(
            project_root=project_root,
            names_by_file={source_file: {"Alias"}},
        )
        for path, source in sources.items():
            tm.that(path.read_text(encoding="utf-8"), eq=source)

    @pytest.mark.parametrize("existing_target", [False, True])
    def test_typing_alias_cutover_preserves_all_consumer_bindings(
        self,
        tmp_path: Path,
        *,
        existing_target: bool,
    ) -> None:
        """Publish aliases and mixed consumer imports as one protected move."""
        project_root, package_root = self._build_project(tmp_path)
        source_file = package_root / "service.py"
        typings_file = package_root / "typings.py"
        if existing_target:
            self._write_file(typings_file, "from __future__ import annotations\n")
        self._write_file(
            source_file,
            "type AnyAlias = str\n"
            "type CleanAlias = int\n"
            "type NestedAnyAlias = list[AnyAlias]\n"
            "value = 1\n"
            "__all__ = ('AnyAlias', 'CleanAlias', 'NestedAnyAlias', 'value')\n",
        )
        self._write_file(
            package_root / "consumer.py",
            "from typing import Annotated, Literal\n"
            "from demo_pkg.service import AnyAlias as Renamed, CleanAlias, value\n"
            "Published = Renamed\n"
            "Clean = CleanAlias\n"
            "PublishedValue = value\n"
            "Metadata = Annotated[CleanAlias, 'AnyAlias']\n"
            "Label = Literal['AnyAlias']\n"
            "def shadow(Renamed: str) -> str:\n"
            "    return Renamed\n",
        )
        self._write_file(
            package_root / "second.py",
            "from .service import AnyAlias, NestedAnyAlias as Nested\n"
            "Published = AnyAlias\n"
            "NestedPublished = Nested\n",
        )

        u.Infra.rewrite_manual_typing_alias_violations(
            project_root=project_root,
            names_by_file={source_file: {"AnyAlias", "CleanAlias", "NestedAnyAlias"}},
        )

        tm.that(source_file.read_text(encoding="utf-8"), lacks="import AnyAlias")
        tm.that(
            u.Tests.run_lazy_init_probe(
                "from typing import get_args\n"
                "from demo_pkg import consumer, second, service, typings\n"
                "print(consumer.Published is second.Published is typings.AnyAlias)\n"
                "print(consumer.Clean is typings.CleanAlias)\n"
                "print(second.NestedPublished is typings.NestedAnyAlias)\n"
                "print(get_args(typings.NestedAnyAlias.__value__)[0] "
                "is typings.AnyAlias)\n"
                "print(get_args(consumer.Metadata)[1] == 'AnyAlias')\n"
                "print(get_args(consumer.Label) == ('AnyAlias',))\n"
                "print(consumer.shadow('local') == 'local')\n"
                "print(consumer.PublishedValue == service.value)\n"
                "print(not hasattr(service, 'AnyAlias'))\n",
                python_paths=(str(package_root.parent),),
            ),
            eq=["True"] * 9,
        )

    @pytest.mark.parametrize("ambiguous_binding", [False, True])
    def test_rejected_typing_alias_cutover_restores_every_source(
        self,
        tmp_path: Path,
        *,
        ambiguous_binding: bool,
    ) -> None:
        """Planning ambiguity or real lint rejection leaves the complete move intact."""
        project_root, package_root = self._build_project(tmp_path)
        source_file = package_root / "service.py"
        typings_file = package_root / "typings.py"
        consumer_file = package_root / "consumer.py"
        originals = {
            source_file: (
                "type Alias = str\n"
                if ambiguous_binding
                else "class LocalType:\n    pass\n\ntype Alias = LocalType\n"
            ),
            typings_file: "from __future__ import annotations\ntype Existing = bytes\n",
            consumer_file: (
                (
                    "from demo_pkg.typings import Existing as Alias\n"
                    if ambiguous_binding
                    else ""
                )
                + "from demo_pkg.service import Alias\nPublished = Alias\n"
            ),
        }
        for path, source in originals.items():
            self._write_file(path, source)

        with pytest.raises(RuntimeError):
            u.Infra.rewrite_manual_typing_alias_violations(
                project_root=project_root,
                names_by_file={source_file: {"Alias"}},
                gates=("lint",),
            )

        for path, source in originals.items():
            tm.that(path.read_text(encoding="utf-8"), eq=source)

    @pytest.mark.parametrize(
        "consumer_source",
        [
            "import demo_pkg.other\nPublished = demo_pkg.other.Value\n",
            "import demo_pkg.service as service\nPublished = service.value\n",
            "from demo_pkg import service\nPublished = service.value\n",
            "from demo_pkg import *\nPublished = Value\n",
            (
                "from typing import TYPE_CHECKING\n"
                "if TYPE_CHECKING:\n    from .unavailable import Unrelated\n"
                "value: 'Unrelated'\n"
            ),
            (
                "import demo_pkg.service as service\n"
                "def shadow(service):\n    return service.Alias\n"
            ),
            "from . import service\nLabel = 'service.Alias'\n",
            (
                "from typing import Literal, Annotated\n"
                "from . import service\n"
                "type Label = Literal['service.Alias']\n"
                "type Marked = Annotated[str, 'service.Alias']\n"
            ),
        ],
    )
    def test_unrelated_imports_leave_typing_alias_plan_unchanged(
        self,
        tmp_path: Path,
        consumer_source: str,
    ) -> None:
        """Module spelling alone does not establish a selected alias consumer."""
        root, package = self._build_project(tmp_path)
        source = package / "service.py"
        consumer = package / "consumer.py"
        self._write_file(source, "type Alias = str\nvalue = 1\n")
        self._write_file(package / "other.py", "class Value:\n    pass\n")
        self._write_file(
            package / "__init__.py",
            "from .other import Value\n__all__ = ('Value',)\n",
        )
        self._write_file(consumer, consumer_source)

        with FlextInfraRopeWorkspace.open_workspace(root) as rope:
            prepared = u.Infra.plan_from_import_aliases(
                rope.rope_project,
                tm.not_none(rope.resource(consumer)),
                source_module="demo_pkg.service",
                target_module="demo_pkg.typings",
                aliases=("Alias",),
            )

        tm.ok(prepared is None)
        tm.that(consumer.read_text(encoding="utf-8"), eq=consumer_source)
        tm.fail(package.joinpath("typings.py").exists())

    @pytest.mark.parametrize("exposes_alias", [False, True])
    def test_ancestor_star_import_uses_selected_export_identity(
        self,
        tmp_path: Path,
        *,
        exposes_alias: bool,
    ) -> None:
        """An ancestor star is relevant only when its exports expose the alias."""
        root, package = self._build_project(tmp_path)
        self._write_file(package / "service.py", "type Alias = str\nvalue = 1\n")
        exports = "('Alias', 'value')" if exposes_alias else "('value',)"
        self._write_file(
            package / "__init__.py",
            f"from .service import Alias, value\n__all__ = {exports}\n",
        )
        consumer = package / "consumer.py"
        original = "from demo_pkg import *\nPublished = value\n"
        self._write_file(consumer, original)

        with FlextInfraRopeWorkspace.open_workspace(root) as rope:
            resource = tm.not_none(rope.resource(consumer))
            if exposes_alias:
                with pytest.raises(RuntimeError, match="unsupported Rope module/star"):
                    u.Infra.plan_from_import_aliases(
                        rope.rope_project,
                        resource,
                        source_module="demo_pkg.service",
                        target_module="demo_pkg.typings",
                        aliases=("Alias",),
                    )
            else:
                tm.that(
                    u.Infra.plan_from_import_aliases(
                        rope.rope_project,
                        resource,
                        source_module="demo_pkg.service",
                        target_module="demo_pkg.typings",
                        aliases=("Alias",),
                    ),
                    eq=None,
                )

        tm.that(consumer.read_text(encoding="utf-8"), eq=original)
        tm.fail(package.joinpath("typings.py").exists())

    @pytest.mark.parametrize("separator", ["\u2028", "\u2029", "\f"])
    def test_typing_alias_plan_preserves_physical_lines_and_import_comments(
        self,
        tmp_path: Path,
        separator: str,
    ) -> None:
        """Actual string separators and formfeed must not shift AST edit offsets."""
        root, package = self._build_project(tmp_path)
        self._write_file(package / "service.py", "type Alias = str\nvalue = 1\n")
        self._write_file(package / "typings.py", "type Alias = str\n")
        consumer = package / "consumer.py"
        prefix = f"Label = 'left{separator}right'\n"
        original = (
            prefix + "\ffrom .service import (\n"
            "    Alias as Bound,  # retain alias comment\n"
            "    value,  # retain value comment\n"
            ")  # retain trailing comment\n"
            "Published = Bound\nPublishedValue = value\n"
        )
        self._write_file(consumer, original)

        with FlextInfraRopeWorkspace.open_workspace(root) as rope:
            prepared = tm.not_none(
                u.Infra.plan_from_import_aliases(
                    rope.rope_project,
                    tm.not_none(rope.resource(consumer)),
                    source_module="demo_pkg.service",
                    target_module="demo_pkg.typings",
                    aliases=("Alias",),
                )
            )

        tm.that(consumer.read_text(encoding="utf-8"), eq=original)
        tm.that(prepared, has=prefix)
        for comment in (
            "# retain alias comment",
            "# retain value comment",
            "# retain trailing comment",
        ):
            tm.that(prepared, has=comment)
        self._write_file(consumer, prepared)
        tm.that(
            u.Tests.run_lazy_init_probe(
                "from demo_pkg import consumer, service, typings\n"
                "print(consumer.Published is typings.Alias)\n"
                "print(consumer.PublishedValue == service.value)\n"
                f"print(consumer.Label == 'left{separator}right')\n",
                python_paths=(str(package.parent),),
            ),
            eq=["True"] * 3,
        )

    @pytest.mark.parametrize("mixed", [False, True])
    def test_non_ascii_inline_import_plan_preserves_bytes_or_rejects(
        self,
        tmp_path: Path,
        *,
        mixed: bool,
    ) -> None:
        """UTF-8 columns retain semicolons/comments; mixed inline forms fail intact."""
        root, package = self._build_project(tmp_path)
        self._write_file(package / "service.py", "type Alias = str\nvalue = 1\n")
        self._write_file(package / "typings.py", "type Alias = str\n")
        consumer = package / "consumer.py"
        names = "Alias, value" if mixed else "Alias"
        original = (
            f"Label = 'caf\u00e9'; from .service import {names}; "
            "Published = Alias  # retain trailing comment\n"
        )
        self._write_file(consumer, original)

        with FlextInfraRopeWorkspace.open_workspace(root) as rope:
            resource = tm.not_none(rope.resource(consumer))
            if mixed:
                with pytest.raises(RuntimeError, match="unsupported Rope inline mixed"):
                    u.Infra.plan_from_import_aliases(
                        rope.rope_project,
                        resource,
                        source_module="demo_pkg.service",
                        target_module="demo_pkg.typings",
                        aliases=("Alias",),
                    )
            else:
                prepared = tm.not_none(
                    u.Infra.plan_from_import_aliases(
                        rope.rope_project,
                        resource,
                        source_module="demo_pkg.service",
                        target_module="demo_pkg.typings",
                        aliases=("Alias",),
                    )
                )
                tm.that(
                    prepared,
                    eq=original.replace("from .service", "from demo_pkg.typings"),
                )

        tm.that(consumer.read_text(encoding="utf-8"), eq=original)

    def test_typing_alias_cutover_preserves_scoped_relative_imports(
        self,
        tmp_path: Path,
    ) -> None:
        """Function, class and typing-only imports retain their original scopes."""
        project_root, package_root = self._build_project(tmp_path)
        source_file = package_root / "service.py"
        consumer_file = package_root / "consumer.py"
        self._write_file(source_file, "type Alias = str\nvalue = 1\n")
        self._write_file(package_root / "typings.py", "type Existing = bytes\n")
        self._write_file(
            consumer_file,
            "from typing import TYPE_CHECKING\n"
            "from .typings import Existing as Local\n"
            "PublishedExisting = Local\n"
            "if TYPE_CHECKING:\n"
            "    from .service import Alias as Annotation\n"
            "def typed(value: 'Annotation') -> 'Annotation':\n"
            "    return value\n"
            "def scoped():\n"
            "    from .service import Alias as Local, value\n"
            "    return Local, value\n"
            "class Owner:\n"
            "    from .service import Alias as Local\n"
            "    Published = Local\n"
            "def shadow(Local):\n"
            "    return Local\n",
        )

        u.Infra.rewrite_manual_typing_alias_violations(
            project_root=project_root,
            names_by_file={source_file: {"Alias"}},
        )

        tm.that(
            consumer_file.read_text(encoding="utf-8"),
            has=(
                "if TYPE_CHECKING:\n"
                "    from demo_pkg.typings import Alias as Annotation"
            ),
        )
        tm.that(
            u.Tests.run_lazy_init_probe(
                "from demo_pkg import consumer, service, typings\n"
                "print(consumer.scoped()[0] is typings.Alias)\n"
                "print(consumer.scoped()[1] == service.value)\n"
                "print(consumer.Owner.Published is typings.Alias)\n"
                "print(consumer.shadow('local') == 'local')\n"
                "print(consumer.PublishedExisting is typings.Existing)\n"
                "print(not hasattr(consumer, 'Annotation'))\n",
                python_paths=(str(package_root.parent),),
            ),
            eq=["True"] * 6,
        )

    def test_typing_alias_cutover_preserves_interleaved_binding_captures(
        self,
        tmp_path: Path,
    ) -> None:
        """Repeated imports cannot be merged or sorted across runtime captures."""
        project_root, package_root = self._build_project(tmp_path)
        source_file = package_root / "service.py"
        consumer_file = package_root / "consumer.py"
        self._write_file(source_file, "type Alias = str\n")
        self._write_file(package_root / "other.py", "type Alias = bytes\n")
        self._write_file(
            consumer_file,
            "from .service import Alias as Bound\n"
            "Before = Bound\n"
            "from .other import Alias as Bound\n"
            "After = Bound\n"
            "from .service import Alias as Bound\n"
            "Last = Bound\n",
        )

        u.Infra.rewrite_manual_typing_alias_violations(
            project_root=project_root,
            names_by_file={source_file: {"Alias"}},
        )

        tm.that(
            u.Tests.run_lazy_init_probe(
                "from demo_pkg import consumer, other, typings\n"
                "print(consumer.Before is consumer.Last is typings.Alias)\n"
                "print(consumer.After is other.Alias)\n"
                "print(consumer.Before is not consumer.After)\n",
                python_paths=(str(package_root.parent),),
            ),
            eq=["True"] * 3,
        )

    @pytest.mark.parametrize("moved_first", [False, True])
    def test_typing_alias_mixed_import_rejects_repeated_bound_names(
        self,
        tmp_path: Path,
        *,
        moved_first: bool,
    ) -> None:
        """Reject bindings whose order cannot survive native import normalization."""
        project_root, package_root = self._build_project(tmp_path)
        source_file = package_root / "service.py"
        self._write_file(source_file, "type Alias = str\nvalue = bytes\n")
        names = (
            "Alias as Bound, value as Bound"
            if moved_first
            else "value as Bound, Alias as Bound"
        )
        self._write_file(
            package_root / "consumer.py",
            f"from .service import {names}\nPublished = Bound\n",
        )

        originals = {
            path: path.read_bytes()
            for path in (source_file, package_root / "consumer.py")
        }
        with pytest.raises(RuntimeError, match="conflicting Rope imported binding"):
            u.Infra.rewrite_manual_typing_alias_violations(
                project_root=project_root,
                names_by_file={source_file: {"Alias"}},
            )
        for path, original in originals.items():
            tm.that(path.read_bytes(), eq=original)
        tm.fail((package_root / "typings.py").exists())

        expected = "service.value" if moved_first else "service.Alias"
        tm.that(
            u.Tests.run_lazy_init_probe(
                "from demo_pkg import consumer, service\n"
                f"print(consumer.Published is {expected})\n",
                python_paths=(str(package_root.parent),),
            ),
            eq=["True"],
        )

    @pytest.mark.parametrize("existing_target", [False, True])
    @pytest.mark.parametrize(
        "consumer_source",
        [
            "import demo_pkg.service as module\nPublished = module.Alias\n",
            "import demo_pkg.service\nPublished = demo_pkg.service.Alias\n",
            "from demo_pkg import service as module\nPublished = module.Alias\n",
            "from . import service\nPublished = service.Alias\n",
            "from .service import *\nPublished = Alias\n",
            "if True:\n    from .service import *\nPublished = Alias\n",
            (
                "def scoped():\n"
                "    import demo_pkg.service as module\n"
                "    return module.Alias\n"
            ),
            (
                "from . import service\n"
                "def consume(value: 'service.Alias'):\n"
                "    return value\n"
            ),
            (
                "from . import service\n"
                "def produce() -> 'service.Alias':\n"
                "    return 'value'\n"
            ),
        ],
    )
    def test_unsupported_typing_alias_consumers_reject_before_publication(
        self,
        tmp_path: Path,
        consumer_source: str,
        *,
        existing_target: bool,
    ) -> None:
        """Unsupported identities leave consumers, declarations and absence intact."""
        project_root, package_root = self._build_project(tmp_path)
        source_file = package_root / "service.py"
        typings_file = package_root / "typings.py"
        originals = {
            source_file: "type Alias = str\n",
            package_root / "consumer.py": consumer_source,
            package_root / "supported.py": (
                "from .service import Alias\nPublished = Alias\n"
            ),
        }
        if existing_target:
            originals[typings_file] = "from __future__ import annotations\n"
        for path, source in originals.items():
            self._write_file(path, source)

        with pytest.raises(RuntimeError, match="unsupported Rope"):
            u.Infra.rewrite_manual_typing_alias_violations(
                project_root=project_root,
                names_by_file={source_file: {"Alias"}},
            )

        for path, source in originals.items():
            tm.that(path.read_text(encoding="utf-8"), eq=source)
        tm.that(typings_file.exists(), eq=existing_target)

    @pytest.mark.parametrize("existing_target", [False, True])
    @pytest.mark.parametrize(
        "mutation",
        [
            "__all__.append('Alias')",
            "__all__.extend(['Alias'])",
            "__all__ += ['Alias']",
        ],
    )
    def test_mutated_star_exports_reject_before_typing_alias_publication(
        self,
        tmp_path: Path,
        mutation: str,
        *,
        existing_target: bool,
    ) -> None:
        """A mutable export list never proves a selected binding is excluded."""
        root, package = self._build_project(tmp_path)
        source = package / "service.py"
        destination = package / "typings.py"
        originals = {
            source: (
                f"type Alias = str\nvalue = bytes\n__all__ = ['value']\n{mutation}\n"
            ),
            package / "consumer.py": "from .service import *\nPublished = Alias\n",
        }
        if existing_target:
            originals[destination] = "from __future__ import annotations\n"
        for path, content in originals.items():
            self._write_file(path, content)
        with pytest.raises(RuntimeError, match="unsupported Rope"):
            u.Infra.rewrite_manual_typing_alias_violations(
                project_root=root,
                names_by_file={source: {"Alias"}},
            )
        for path, original in originals.items():
            tm.that(path.read_text(encoding="utf-8"), eq=original)
        tm.that(destination.exists(), eq=existing_target)

    @pytest.mark.parametrize("scoped", [False, True])
    def test_relative_target_binding_conflict_rejects_typing_alias_cutover(
        self,
        tmp_path: Path,
        *,
        scoped: bool,
    ) -> None:
        """Relative target imports participate in same-scope collision checks."""
        project_root, package_root = self._build_project(tmp_path)
        source_file = package_root / "service.py"
        imports = (
            "from .typings import Existing as Alias\n"
            "from .service import Alias\n"
            "Published = Alias\n"
        )
        consumer = (
            "def scoped():\n"
            + "".join(f"    {line}\n" for line in imports.splitlines())
            if scoped
            else imports
        )
        originals = {
            source_file: "type Alias = str\n",
            package_root / "typings.py": "type Existing = bytes\n",
            package_root / "consumer.py": consumer,
        }
        for path, source in originals.items():
            self._write_file(path, source)

        with pytest.raises(RuntimeError, match="ambiguous Rope target binding"):
            u.Infra.rewrite_manual_typing_alias_violations(
                project_root=project_root,
                names_by_file={source_file: {"Alias"}},
            )

        for path, source in originals.items():
            tm.that(path.read_text(encoding="utf-8"), eq=source)
