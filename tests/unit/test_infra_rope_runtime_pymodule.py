"""Behavior tests for the rope runtime module predicate.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from contextlib import ExitStack, closing
from typing import TYPE_CHECKING

import pytest

from flext_infra.workspace import FlextInfraRopeWorkspace
from tests import c, m, p, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraRopeRuntimePymodule:
    """Validate the module predicate over rope modules and packages."""

    @staticmethod
    @pytest.mark.parametrize("reuse_binding", [False, True])
    @pytest.mark.parametrize("admitted", [False, True])
    def test_native_restructuring_preserves_admission_and_import_bindings(
        tmp_path: Path,
        *,
        reuse_binding: bool,
        admitted: bool,
    ) -> None:
        """Real native changes respect identity alternatives and import policy."""
        (tmp_path / "provider.py").write_text(
            "class Old:\n    value = 'old'\n"
            "class Alternative:\n    value = 'alternative'\n"
            "class New:\n    value = 'new'\n"
            "class Existing:\n    value = 'existing'\n"
            "class Foreign:\n    value = 'foreign'\n",
            encoding=c.DEFAULT_ENCODING,
        )
        consumer = tmp_path / "consumer.py"
        consumer.write_text(
            "from provider import Old as Alias, Foreign\n"
            + ("from provider import Existing as New\n" if reuse_binding else "")
            + "print(Alias.value, Foreign.value)\n",
            encoding=c.DEFAULT_ENCODING,
        )
        expected_module = "consumer" if admitted else "unselected"

        def accept(
            module: p.Infra.RopePyModule,
            match: p.Infra.RopeContractMatch,
        ) -> bool:
            return (
                module.get_name() == expected_module
                and "Alias" in module.get_scope().get_defined_names()
                and match.get_ast("owner") is not None
            )

        with closing(u.Infra.init_rope_project(tmp_path)) as project:
            project.do(
                u.Infra.restructure_changes(
                    project,
                    m.Infra.RopeRestructureRequest(
                        pattern="${owner}.value",
                        goal="New.value",
                        arguments={
                            "owner": ("name=provider.Old", "name=provider.Alternative")
                        },
                        resources=(project.get_resource(consumer.name),),
                        imports={"New": "from provider import New"},
                        match_filter=accept,
                    ),
                )
            )
        expected_value = ("existing" if reuse_binding else "new") if admitted else "old"
        output = tm.ok(u.Cli.run((sys.executable, str(consumer))))
        tm.that(output.stdout, eq=f"{expected_value} foreign\n")

    @staticmethod
    @pytest.mark.parametrize("captured", [False, True])
    def test_relative_lookup_preserves_native_folder_and_absent_context(
        tmp_path: Path,
        *,
        captured: bool,
    ) -> None:
        """Live and captured projects retain one native relative lookup contract."""
        package = tmp_path / "pkg"
        package.mkdir()
        initializer = package / c.Infra.INIT_PY
        owner = package / "owner.py"
        initializer.write_text("", encoding=c.DEFAULT_ENCODING)
        owner.write_text(
            "class PublishedContract:\n    pass\n", encoding=c.DEFAULT_ENCODING
        )
        with ExitStack() as stack:
            live = stack.enter_context(closing(u.Infra.init_rope_project(tmp_path)))
            project = (
                stack.enter_context(
                    closing(
                        u.Infra.snapshot_project(
                            live,
                            {
                                initializer: initializer.read_text(
                                    encoding=c.DEFAULT_ENCODING
                                ),
                                owner: owner.read_text(encoding=c.DEFAULT_ENCODING),
                            },
                        )
                    )
                )
                if captured
                else live
            )
            folder = project.get_folder(package.name)
            tm.that(
                project.find_relative_module("owner", folder, 1),
                eq=project.get_resource(owner.relative_to(tmp_path).as_posix()),
            )
            tm.that(
                u.Infra
                .require_semantic_module(
                    project.get_relative_module("owner", folder, 1)
                )
                .get_attribute("PublishedContract")
                .get_object()
                .get_name(),
                eq="PublishedContract",
            )
            tm.that(project.find_relative_module("owner", None, 1), none=True)
            with pytest.raises(u.Infra.rope_module_not_found_error_types()):
                project.get_relative_module("owner", None, 1)

    @staticmethod
    def test_blocked_stdlib_module_preserves_native_import_state(
        tmp_path: Path,
    ) -> None:
        """A native blocked-import sentinel does not break project construction."""
        u.Tests.run_lazy_init_probe(
            "import sys\n"
            "from contextlib import closing\n"
            "from pathlib import Path\n"
            "from flext_infra import u\n"
            "factory = u.Infra.init_rope_project\n"
            "assert 'idlelib' in sys.stdlib_module_names\n"
            "sys.modules['idlelib'] = None\n"
            "with closing(factory(Path(sys.argv[1]))) as project:\n"
            "    assert Path(project.root.real_path) == Path(sys.argv[1]).resolve()\n"
            "assert sys.modules['idlelib'] is None\n",
            python_paths=(),
            arguments=(str(tmp_path),),
        )

    @staticmethod
    def test_regular_package_precedes_namespace_in_captured_sources(
        tmp_path: Path,
    ) -> None:
        """The same source package wins before and after capturing its files."""
        roots = (tmp_path / "first", tmp_path / "second")
        namespace, package = (root / "provider" for root in roots)
        namespace.mkdir(parents=True)
        package.mkdir(parents=True)
        (namespace / "portion.py").write_text(
            "VALUE = 1\n", encoding=c.DEFAULT_ENCODING
        )
        initializer = package / c.Infra.INIT_PY
        source = "class PublishedContract:\n    pass\n"
        initializer.write_text(source, encoding=c.DEFAULT_ENCODING)
        with (
            closing(
                u.Infra.new_project(
                    str(tmp_path),
                    ropefolder="",
                    save_objectdb=False,
                    filter_lists=((), tuple(root.name for root in roots)),
                )
            ) as original,
            closing(u.Infra.snapshot_project(original, {})) as captured,
        ):
            tm.that(
                u.Infra
                .require_semantic_module(original.get_module("provider"))
                .get_attribute("PublishedContract")
                .get_object()
                .get_name(),
                eq="PublishedContract",
            )
            initializer.unlink()
            tm.that(
                u.Infra
                .require_semantic_module(captured.get_module("provider"))
                .get_attribute("PublishedContract")
                .get_object()
                .get_name(),
                eq="PublishedContract",
            )

    @staticmethod
    def test_snapshot_project_uses_only_captured_sources(tmp_path: Path) -> None:
        """A later disk edit cannot change the closed Rope source view."""
        captured = tmp_path / "captured.py"
        captured.write_text("VALUE = 42\n", encoding=c.Infra.ENCODING_DEFAULT)
        with (
            closing(u.Infra.init_rope_project(tmp_path)) as original,
            closing(
                u.Infra.snapshot_project(
                    original,
                    {captured: captured.read_text(encoding=c.Infra.ENCODING_DEFAULT)},
                ),
            ) as project,
        ):
            captured.unlink()
            (tmp_path / "uncaptured.py").write_text(
                "VALUE = 99\n", encoding=c.Infra.ENCODING_DEFAULT
            )
            resource = u.Infra.require_file_resource(
                tm.not_none(project.find_module("captured")), captured
            )
            tm.that(resource.read(), eq="VALUE = 42\n")
            tm.that(project.find_module("uncaptured"), none=True)

    @staticmethod
    def test_declared_package_root_resolves_its_qualified_name(
        tmp_path: Path,
    ) -> None:
        """A declared package folder exposes its real qualified import.

        Raises:
            AssertionError: If declared package root did not resolve its qualified name.

        """
        package = tmp_path / "qualified_package"
        initializer = package / c.Infra.INIT_PY
        source = "class PublishedContract:\n    pass\n"
        package.mkdir()
        initializer.write_text(source, encoding=c.Infra.ENCODING_DEFAULT)
        with (
            closing(
                u.Infra.new_project(
                    str(tmp_path),
                    ropefolder="",
                    save_objectdb=False,
                    filter_lists=((), (package.name,)),
                ),
            ) as original,
            closing(
                u.Infra.snapshot_project(original, {initializer: source}),
            ) as project,
        ):
            resource = project.find_module(package.name)
            tm.that(resource, none=False)
            if resource is None:
                msg = "declared package root did not resolve its qualified name"
                raise AssertionError(msg)
            module = u.Infra.resolve_pymodule(project, resource)
            tm.that(
                module.get_attribute("PublishedContract").get_object().get_name(),
                eq="PublishedContract",
            )
            tm.not_none(u.Infra.resolve_module_imports(project, resource))

    @staticmethod
    @pytest.mark.parametrize("regular_package", [False, True])
    def test_module_precedes_namespace_but_not_regular_package(
        tmp_path: Path,
        *,
        regular_package: bool,
    ) -> None:
        """Python source wins over a data directory, not an initialized package.

        Raises:
            AssertionError: If Native Rope finder did not resolve the fixture module.

        """
        root = tmp_path / "consumer"
        source = root / "src"
        source.mkdir(parents=True)
        (source / "contract.py").write_text(
            "class ModuleContract:\n    pass\n",
            encoding=c.Infra.ENCODING_DEFAULT,
        )
        package = source / "contract"
        package.mkdir()
        if regular_package:
            (package / c.Infra.INIT_PY).write_text(
                "class PackageContract:\n    pass\n",
                encoding=c.Infra.ENCODING_DEFAULT,
            )
        with FlextInfraRopeWorkspace.open_workspace(root) as workspace:
            resource = workspace.rope_project.find_module("contract")
            tm.that(resource, none=False)
            if resource is None:
                message = "Native Rope finder did not resolve the fixture module"
                raise AssertionError(message)
            module = u.Infra.resolve_pymodule(workspace.rope_project, resource)
            expected = "PackageContract" if regular_package else "ModuleContract"
            tm.that(module.get_attribute(expected).get_object().get_name(), eq=expected)

    @staticmethod
    def test_pymodule_contract_accepts_packages(tmp_path: Path) -> None:
        """A rope PyPackage satisfies the pymodule contract beside PyModule.

        ``find_module`` resolves an installed third-party package to its
        folder resource and ``get_pymodule`` returns a ``PyPackage`` for it;
        external base resolution (``pydantic.BaseModel`` and friends) reads
        attributes through packages, so the validated boundary must accept
        both shapes (fleet gen regression 2026-10-05).

        Raises:
            ValueError: If fixture modules are missing from the snapshot project.

        """
        package_root = tmp_path / "pkg"
        package_root.mkdir()
        init_module = package_root / "__init__.py"
        init_module.write_text("VALUE = 1\n")
        plain_module = tmp_path / "plain.py"
        plain_module.write_text("VALUE = 2\n")
        sources = {
            init_module: init_module.read_text(),
            plain_module: plain_module.read_text(),
        }
        with (
            closing(u.Infra.init_rope_project(tmp_path)) as original,
            closing(u.Infra.snapshot_project(original, sources)) as project,
        ):
            plain_resource = project.find_module("plain")
            pkg_resource = project.find_module("pkg")
            if plain_resource is None or pkg_resource is None:
                msg = "fixture modules missing from the snapshot project"
                raise ValueError(msg)
            pymodule = u.Infra.resolve_pymodule(
                project,
                plain_resource,
            )
            pypackage = u.Infra.resolve_pymodule(
                project,
                pkg_resource,
            )
            tm.that(u.Infra.require_parsed_module(pymodule) is pymodule)
            tm.that(u.Infra.require_parsed_module(pypackage) is pypackage)
            assert pypackage.get_attribute("VALUE") is not None
            for name, member in (
                ("plain", "VALUE"),
                ("pkg", "VALUE"),
                ("builtins", "len"),
                ("os", "getenv"),
            ):
                native = project.get_module(name)
                admitted = u.Infra.require_semantic_module(native)
                tm.that(admitted is native)
                tm.not_none(admitted.get_attributes().get(member))
            with pytest.raises(TypeError, match="native semantic module"):
                u.Infra.require_semantic_module(plain_resource)
            with pytest.raises(TypeError, match="non-parsed module"):
                u.Infra.require_parsed_module(project.get_module("builtins"))

    @staticmethod
    @pytest.mark.parametrize("ambiguous", [False, True])
    def test_native_definition_token_identity(
        tmp_path: Path, *, ambiguous: bool
    ) -> None:
        """A unique definition resolves; two same-line uses remain ambiguous."""
        source = "value = 1; print(value)\n" if ambiguous else "value = 1\n"
        path = tmp_path / "consumer.py"
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        with (
            closing(u.Infra.init_rope_project(tmp_path)) as original,
            closing(u.Infra.snapshot_project(original, {path: source})) as project,
        ):
            module = u.Infra.resolve_pymodule(project, project.get_resource(path.name))
            binding = module.get_attribute("value")
            if ambiguous:
                with pytest.raises(RuntimeError, match="definition binding token"):
                    u.Infra.find_identifier_offset_in_lines(
                        source.splitlines(keepends=True),
                        line=1,
                        symbol="value",
                        pyname=binding,
                    )
            else:
                tm.that(
                    u.Infra.find_identifier_offset_in_lines(
                        source.splitlines(keepends=True),
                        line=1,
                        symbol="value",
                        pyname=binding,
                    ),
                    eq=source.index("value"),
                )
