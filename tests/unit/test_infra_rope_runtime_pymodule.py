"""Behavior tests for the rope runtime module predicate.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from contextlib import ExitStack, closing
from typing import TYPE_CHECKING

from flext_infra import infra
from flext_infra.workspace import FlextInfraRopeWorkspace
from tests import c, m, p, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraRopeRuntimePymodule:
    """Validate the module predicate over rope modules and packages."""

    @staticmethod
    @c.Tests.MARK.parametrize(
        ("package_name", "export", "owner"),
        [
            ("flext_core", "r", "flext_core.result.FlextResult"),
            ("flext_cli", "m", "flext_cli.models.FlextCliModels"),
            ("flext_api", "p", "flext_api.protocols.FlextApiProtocols"),
        ],
    )
    def test_native_sdk_resolves_real_lazy_publication_identity(
        tmp_path: Path, package_name: str, export: str, owner: str
    ) -> None:
        """Actual SDK package attributes agree with their declared live suppliers."""
        root, _package = u.Tests.create_lazy_init_workspace(tmp_path)
        with infra.rope_workspace(root) as workspace:
            project = workspace.rope_project
            package = u.Infra.require_semantic_module(project.get_module(package_name))
            native = package.get_attribute(export)
            supplier = u.Infra.qualified_name(project, owner)
            tm.ok(u.Infra.same_name(supplier, native))
            tm.ok(
                u.Infra.same_name(
                    native, u.Infra.qualified_name(project, f"{package_name}.{export}")
                )
            )

    @staticmethod
    def test_qualified_explicit_module_retains_original_snapshot_syntax_failure(
        tmp_path: Path,
    ) -> None:
        """A valid alternate publication cannot replace a malformed selected module."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        initializer = package / c.Infra.INIT_PY
        initializer.write_text(
            "from typing import TYPE_CHECKING\n"
            "from flext_core.lazy import install_lazy_exports\n"
            "if TYPE_CHECKING:\n    from .published import FlextResult\n"
            "install_lazy_exports(__name__, globals(), "
            "{'FlextResult': '.published'}, public_exports=('FlextResult',))\n",
            encoding=c.DEFAULT_ENCODING,
        )
        source = "from flext_core.result import FlextResult\n"
        requested = package / "requested.py"
        requested.write_text(source, encoding=c.DEFAULT_ENCODING)
        (package / "published.py").write_text(source, encoding=c.DEFAULT_ENCODING)
        with (
            infra.rope_workspace(root) as live,
            closing(
                u.Infra.snapshot_project(
                    live.rope_project, {requested: "def invalid(:\n"}
                )
            ) as project,
        ):
            with u.Tests.raises(
                u.Infra.exception_type("rope.base.exceptions", "ModuleSyntaxError")
            ) as error:
                u.Infra.qualified_name(
                    project, "FlextResult", module_name=f"{package.name}.requested"
                )
            tm.that(str(error.value), has=requested.name)
            tm.ok(
                u.Infra.same_name(
                    u.Infra.qualified_name(project, "flext_core.result.FlextResult"),
                    u.Infra.qualified_name(project, f"{package.name}.FlextResult"),
                )
            )
        tm.that(requested.read_text(encoding=c.DEFAULT_ENCODING), eq=source)

    @staticmethod
    def _published_name(attribute: p.Infra.RopePyName) -> str:
        """Resolve the declared name of the native object behind one attribute.

        Returns:
            The name reported by the native named object.

        """
        return u.Infra.require_named_object(
            attribute.get_object(), "published attribute"
        ).get_name()

    @staticmethod
    @c.Tests.MARK.parametrize("reuse_binding", [False, True])
    @c.Tests.MARK.parametrize("admitted", [False, True])
    def test_contract_restructuring_preserves_identity_and_import_bindings(
        tmp_path: Path,
        *,
        reuse_binding: bool,
        admitted: bool,
    ) -> None:
        """Contract restructuring honors identity alternatives and import policy."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        provider = f"{package.name}.provider"
        (package / "provider.py").write_text(
            "class Old:\n    value = 'old'\n"
            "class Alternative:\n    value = 'alternative'\n"
            "class New:\n    value = 'new'\n"
            "class Existing:\n    value = 'existing'\n"
            "class Foreign:\n    value = 'foreign'\n",
            encoding=c.DEFAULT_ENCODING,
        )
        consumer = package / "consumer.py"
        source = (
            f"from {provider} import Old as Alias, Foreign\n"
            + (f"from {provider} import Existing as New\n" if reuse_binding else "")
            + "print(Alias.value, Foreign.value)\n"
        )
        consumer.write_text(source, encoding=c.DEFAULT_ENCODING)
        owners = (f"name={provider}.Old",) if admitted else ()
        rule = m.Infra.RopeContractRule(
            id="restructure-old-value",
            pattern="${owner}.value",
            goal="New.value",
            arguments={"owner": (*owners, f"name={provider}.Alternative")},
            imports={"New": f"from {provider} import New"},
        )
        with infra.rope_workspace(root) as workspace:
            edits = tm.ok(
                u.Infra.plan_contract_rules(workspace, {consumer: source}, (rule,))
            )
        tm.that(consumer.read_text(encoding=c.DEFAULT_ENCODING), eq=source)
        tm.that(len(edits), eq=int(admitted))
        for edit in edits:
            tm.that(edit.file_path.resolve(), eq=consumer.resolve())
            consumer.write_text(edit.updated_source, encoding=c.DEFAULT_ENCODING)
            with infra.rope_workspace(root) as workspace:
                tm.that(
                    tm.ok(
                        u.Infra.plan_contract_rules(
                            workspace, {consumer: edit.updated_source}, (rule,)
                        )
                    ),
                    empty=True,
                )
        expected_value = ("existing" if reuse_binding else "new") if admitted else "old"
        output = tm.ok(
            u.Cli.run(
                (sys.executable, "-c", f"import {package.name}.consumer"),
                cwd=root,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            )
        )
        tm.that(output.stdout, eq=f"{expected_value} foreign\n")

    @staticmethod
    @c.Tests.MARK.parametrize(
        "value",
        [
            '(\n        "first"\n        " second"\n    )',
            '(\n        "only"\n    )',
            "call(\n        1,\n    )",
        ],
    )
    def test_contract_restructuring_keeps_multiline_values_parseable(
        tmp_path: Path,
        value: str,
    ) -> None:
        """A wildcard whose source spans lines keeps the brackets it relied on."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        consumer = package / "consumer.py"
        source = (
            "from typing import Final\n\n"
            "def call(item: int) -> str:\n    return str(item)\n\n"
            f"class Owner:\n    VALUE: Final[str] = {value}\n"
        )
        consumer.write_text(source, encoding=c.DEFAULT_ENCODING)
        rule = m.Infra.RopeContractRule(
            id="final-to-classvar",
            pattern="${name}: ${final}[${contract}] = ${value}",
            goal="${name}: ClassVar[${contract}] = ${value}",
            arguments={"final": "name=typing.Final"},
            imports={"ClassVar": "from typing import ClassVar"},
        )
        with infra.rope_workspace(root) as workspace:
            edits = tm.ok(
                u.Infra.plan_contract_rules(workspace, {consumer: source}, (rule,))
            )
        tm.that(len(edits), eq=1)
        updated = edits[0].updated_source
        tm.that(updated, contains="VALUE: ClassVar[str] = ")
        values: list[str] = []
        for text in (source, updated):
            consumer.write_text(text, encoding=c.DEFAULT_ENCODING)
            output = tm.ok(
                u.Cli.run(
                    (
                        sys.executable,
                        "-c",
                        (
                            f"from {package.name}.consumer import Owner; "
                            f"print(Owner.VALUE)"
                        ),
                    ),
                    cwd=root,
                    options=m.Cli.ProcessOptions(
                        env={"PYTHONPATH": str(package.parent)}
                    ),
                )
            )
            values.append(output.stdout)
        tm.that(values[1], eq=values[0])

    @staticmethod
    @c.Tests.MARK.parametrize("package", [False, True])
    def test_selected_source_resource_preserves_native_public_scope(
        tmp_path: Path,
        *,
        package: bool,
    ) -> None:
        """Source-resource resolution retains the elected module and bindings."""
        provider = tmp_path / "provider"
        if package:
            provider.mkdir()
        source = provider / c.Infra.INIT_PY if package else provider.with_suffix(".py")
        source.write_text(
            "class PublishedContract:\n    pass\n", encoding=c.DEFAULT_ENCODING
        )
        with closing(u.Infra.init_rope_project(tmp_path)) as project:
            selected = u.Infra.require_semantic_module(project.get_module("provider"))
            resource = tm.not_none(selected.get_resource())
            parsed = u.Infra.resolve_pymodule(project, resource)
            tm.ok(parsed is selected)
            tm.ok(
                parsed.get_scope().get_names()["PublishedContract"]
                is selected.get_attribute("PublishedContract")
            )

    @staticmethod
    @c.Tests.MARK.parametrize("captured", [False, True])
    def test_relative_lookup_preserves_native_folder_and_missing_module(
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
                TestsFlextInfraRopeRuntimePymodule._published_name(
                    u.Infra.require_semantic_module(
                        project.get_relative_module("owner", folder, 1)
                    ).get_attribute("PublishedContract")
                ),
                eq="PublishedContract",
            )
            tm.that(project.find_relative_module("missing", folder, 1), none=True)
            with u.Tests.raises(u.Infra.rope_unresolved_error_types()):
                project.get_relative_module("missing", folder, 1)

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
    def test_regular_package_precedes_namespace_in_snapshot_view(
        tmp_path: Path,
    ) -> None:
        """The same source package wins in the live view and its snapshot view."""
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
                TestsFlextInfraRopeRuntimePymodule._published_name(
                    u.Infra.require_semantic_module(
                        original.get_module("provider")
                    ).get_attribute("PublishedContract")
                ),
                eq="PublishedContract",
            )
            tm.that(
                TestsFlextInfraRopeRuntimePymodule._published_name(
                    u.Infra.require_semantic_module(
                        captured.get_module("provider")
                    ).get_attribute("PublishedContract")
                ),
                eq="PublishedContract",
            )

    @staticmethod
    def test_snapshot_project_overlays_proposed_sources_without_writing(
        tmp_path: Path,
    ) -> None:
        """A proposed source is visible in the snapshot view and never written."""
        planned = tmp_path / "planned.py"
        with (
            closing(u.Infra.init_rope_project(tmp_path)) as original,
            closing(
                u.Infra.snapshot_project(original, {planned: "VALUE = 42\n"}),
            ) as project,
        ):
            resource = u.Infra.require_file_resource(
                tm.not_none(project.find_module("planned")), planned
            )
            tm.that(resource.read(), eq="VALUE = 42\n")
            tm.that(planned.exists(), eq=False)

    @staticmethod
    def test_declared_package_root_resolves_its_qualified_name(
        tmp_path: Path,
    ) -> None:
        """A declared package folder exposes its real qualified import."""
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
                tm.reject(msg)
            module = u.Infra.resolve_pymodule(project, resource)
            tm.that(
                TestsFlextInfraRopeRuntimePymodule._published_name(
                    module.get_attribute("PublishedContract")
                ),
                eq="PublishedContract",
            )
            tm.not_none(u.Infra.resolve_module_imports(project, resource))

    @staticmethod
    @c.Tests.MARK.parametrize("regular_package", [False, True])
    def test_module_precedes_namespace_but_not_regular_package(
        tmp_path: Path,
        *,
        regular_package: bool,
    ) -> None:
        """Python source wins over a data directory, not an initialized package."""
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
                tm.reject(message)
            module = u.Infra.resolve_pymodule(workspace.rope_project, resource)
            expected = "PackageContract" if regular_package else "ModuleContract"
            tm.that(
                TestsFlextInfraRopeRuntimePymodule._published_name(
                    module.get_attribute(expected)
                ),
                eq=expected,
            )

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
            tm.that(pypackage.get_attribute("VALUE"), none=False)
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
            with u.Tests.raises(TypeError, match="native semantic module"):
                u.Infra.require_semantic_module(plain_resource)
            with u.Tests.raises(TypeError, match="non-parsed module"):
                u.Infra.require_parsed_module(project.get_module("builtins"))

    @staticmethod
    @c.Tests.MARK.parametrize(
        ("source", "ambiguous"),
        [
            ("value = 1\n", False),
            ("value = 1; print(value)\n", False),
            ("value = 1; value = 2\n", True),
        ],
    )
    def test_native_definition_token_identity(
        tmp_path: Path, source: str, *, ambiguous: bool
    ) -> None:
        """One write resolves despite reads; multiple writes remain ambiguous."""
        path = tmp_path / "consumer.py"
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        with (
            closing(u.Infra.init_rope_project(tmp_path)) as original,
            closing(u.Infra.snapshot_project(original, {path: source})) as project,
        ):
            module = u.Infra.resolve_pymodule(project, project.get_resource(path.name))
            binding = module.get_attribute("value")
            if ambiguous:
                with u.Tests.raises(RuntimeError, match="definition binding token"):
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
