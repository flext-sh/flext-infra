"""Source-only normalization of legacy protocol declarations.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from flext_infra.protocols_bootstrap import (
    consolidate_protocol_owners,
    normalize_model_alias_source,
    normalize_model_alias_tree,
    normalize_protocol_source,
    plan_protocol_facades,
)
from tests import c, p, tm, u


class TestsProtocolSourceBootstrap:
    """Exercise the pre-import stdlib protocol repair entrypoint."""

    @staticmethod
    def checked_run(
        command: tuple[str, ...],
        *,
        cwd: Path | None = None,
        env: dict[str, str] | None = None,
    ) -> p.Cli.CommandOutput:
        """Run one child process and require its successful exit.

        Returns:
            The captured output of the successful child process.

        """
        output = tm.ok(u.Cli.run_raw(command, cwd=cwd, env=env))
        tm.ok(u.Cli.process_succeeded(output.outcome), msg=output.stderr)
        return output

    class TestsModelAliasNormalization:
        """Model alias metadata moves onto Pydantic fields."""

        @staticmethod
        def test_moves_direct_field_aliases_and_preserves_inherited_defaults() -> None:
            """Direct metadata becomes field metadata across local model inheritance."""
            source = (
                "from typing import Annotated\n"
                "from flext_infra import m\n\n"
                "class Base(m.ContractModel):\n"
                "    dependency_groups: Annotated[\n"
                "        dict[str, str], 'native', "
                "m.Field(alias='dependency-groups', default={}, description='groups')\n"
                "    ] = {}\n\n"
                "class Child(Base):\n"
                "    tags: Annotated[list[str], m.Field(validation_alias='tag-list')] "
                "= m.Field(default_factory=list, description='tags')\n"
            )

            normalized = normalize_model_alias_source(source)

            tm.that(
                normalized, has="dependency_groups: Annotated[dict[str, str], 'native']"
            )
            tm.that(
                normalized,
                has="m.Field({}, alias='dependency-groups', description='groups')",
            )
            tm.that(normalized, has="tags: list[str] = m.Field(default_factory=list, ")
            tm.that(normalized, has="description='tags', validation_alias='tag-list')")
            tm.that(normalize_model_alias_source(normalized), eq=normalized)

        @staticmethod
        def test_moves_markdown_config_alias_metadata_to_its_field() -> None:
            """Arbitrary-types config models promote alias metadata from Annotated."""
            source = (
                "from typing import Annotated\n"
                "from flext_infra import m\n\n"
                "class Config:\n"
                "    class MarkdownConfig(m.ArbitraryTypesModel):\n"
                "        projected_blocks: Annotated[\n"
                "            tuple[str, ...],\n"
                "            m.Field(alias='projected-blocks', description='blocks'),\n"
                "        ]\n"
            )

            normalized = normalize_model_alias_source(source)

            tm.that(normalized, has="projected_blocks: tuple[str, ...] = m.Field(")
            tm.that(normalized, has="alias='projected-blocks', description='blocks'")
            tm.that(normalized, lacks="Annotated[")
            tm.that(normalize_model_alias_source(normalized), eq=normalized)

        @staticmethod
        def test_moves_field_only_exclude_metadata_to_its_assignment() -> None:
            """Field-only metadata is not left in Pydantic's Annotated alias path."""
            source = (
                "from typing import Annotated\n"
                "from flext_infra import m\n\n"
                "class RuntimeContext(m.ArbitraryTypesModel):\n"
                "    document: Annotated[object | None, "
                "m.Field(exclude=True, description='context')] = None\n"
            )

            normalized = normalize_model_alias_source(source)

            tm.that(normalized, has="document: object | None = m.Field(")
            tm.that(normalized, has="None, exclude=True, description='context'")
            tm.that(normalize_model_alias_source(normalized), eq=normalized)

        @staticmethod
        def test_moves_type_alias_field_names_to_pydantic_declarations() -> None:
            """Alias-only field names move without discarding ordinary metadata."""
            source = (
                "from typing import Annotated, TypeAlias\n"
                "from flext_infra import m\n\n"
                "type DependencyGroups = Annotated[\n"
                "    dict[str, str], 'native', "
                "m.Field(alias='dependency-groups', description='groups')\n"
                "]\n\n"
                "class Holder:\n"
                "    class Payload(m.ContractModel):\n"
                "        dependency_groups: DependencyGroups\n"
            )

            normalized = normalize_model_alias_source(source)

            tm.that(
                normalized,
                has=(
                    "Annotated[dict[str, str], 'native', m.Field(description='groups')]"
                ),
            )
            tm.that(
                normalized,
                has=(
                    "dependency_groups: Annotated[DependencyGroups, "
                    "m.Field(alias='dependency-groups')]"
                ),
            )
            tm.that(normalize_model_alias_source(normalized), eq=normalized)

        @staticmethod
        def test_ignores_protocols_nonmodels_and_nonalias_field_metadata() -> None:
            """Only proven Pydantic fields receive metadata promoted from aliases."""
            source = (
                "from typing import Annotated, Protocol, TypeAlias\n"
                "from flext_infra import m\n\n"
                "type Named = Annotated[str, m.Field(alias='wire')]\n"
                "type Documented = Annotated[str, m.Field(description='keep')]\n\n"
                "class Ports(Protocol):\n"
                "    name: Named\n\n"
                "class Plain:\n"
                "    name: Named\n\n"
                "class NotAModel(m.String):\n"
                "    name: Named\n\n"
                "class Payload(m.ContractModel):\n"
                "    name: Named\n"
                "    documented: Documented\n"
            )

            normalized = normalize_model_alias_source(source)

            tm.that(normalized, has="class Ports(Protocol):\n    name: Named")
            tm.that(normalized, has="class Plain:\n    name: Named")
            tm.that(normalized, has="class NotAModel(m.String):\n    name: Named")
            tm.that(normalized, has="documented: Documented")
            tm.that(normalized, has="name: Annotated[Named, m.Field(alias='wire')]")
            tm.that(
                normalized,
                has="type Documented = Annotated[str, m.Field(description='keep')]",
            )

        @staticmethod
        def test_model_alias_tree_normalizes_runtime_models_not_protocols(
            tmp_path: Path,
        ) -> None:
            """The pre-import pass covers runtime models outside ``_models`` only."""
            root = tmp_path / "repository"
            models = root / "src" / "demo" / "_models"
            protocols = root / "src" / "demo" / "_protocols"
            runtime = root / "src" / "demo" / "runtime"
            models.mkdir(parents=True)
            protocols.mkdir(parents=True)
            runtime.mkdir(parents=True)
            (root / "pyproject.toml").write_text(
                '[project]\nname = "demo"\n', encoding="utf-8"
            )
            model = models / "payload.py"
            model.write_text(
                "from typing import Annotated\n"
                "from demo import m\n\n"
                "type WireName = Annotated[str, m.Field(alias='wire-name')]\n\n"
                "class Payload(m.BaseModel):\n"
                "    name: WireName\n",
                encoding="utf-8",
            )
            protocol = protocols / "payload.py"
            protocol_source = (
                "from typing import Protocol\nclass Payload(Protocol):\n    name: str\n"
            )
            protocol.write_text(protocol_source, encoding="utf-8")
            runtime_model = runtime / "config.py"
            runtime_model.write_text(
                "from typing import Annotated\n"
                "from demo import m\n\n"
                "class RuntimeConfig(m.ArbitraryTypesModel):\n"
                "    projected_blocks: Annotated[\n"
                "        tuple[str, ...], m.Field(alias='projected-blocks')\n"
                "    ]\n",
                encoding="utf-8",
            )

            changed = normalize_model_alias_tree(root)

            tm.that(changed, eq=(model, runtime_model))
            tm.that(
                model.read_text(encoding="utf-8"),
                has="name: Annotated[WireName, m.Field(alias='wire-name')]",
            )
            tm.that(
                runtime_model.read_text(encoding="utf-8"),
                has=(
                    "projected_blocks: tuple[str, ...] = "
                    "m.Field(alias='projected-blocks')"
                ),
            )
            tm.that(protocol.read_text(encoding="utf-8"), eq=protocol_source)
            tm.that(normalize_model_alias_tree(root), eq=())

    class TestsProtocolSourceNormalization:
        """Protocol sources normalize through the bootstrap."""

        @staticmethod
        def test_normalizes_protocols_without_touching_models_and_repeats(
            tmp_path: Path,
        ) -> None:
            """Test normalizes protocols without touching models and repeats."""
            root = tmp_path / "repository"
            root.mkdir()
            (root / "pyproject.toml").write_text(
                '[project]\nname = "flext-infra"\n', encoding="utf-8"
            )
            protocols = root / "src" / "flext_infra" / "_protocols"
            protocols.mkdir(parents=True)
            module = protocols / "mixed.py"
            module.write_text(
                "from __future__ import annotations\n"
                "from typing import TYPE_CHECKING, Annotated, Protocol\n"
                "from pydantic import BaseModel, Field\n"
                "from flext_infra import m\n"
                "\n"
                "class Models:\n"
                "    class Payload(BaseModel):\n"
                "        title: Annotated[str, Field(description='keep')]\n"
                "\n"
                "class Ports:\n"
                "    class Reader(Protocol):\n"
                "        title: Annotated[str, 'public-λ', "
                "m.Field(description='drop')]\n"
                "        count: int = m.Field(default=0)\n"
                "        receipt: p.Cli.AtomicFileState | None\n"
                "\n"
                "class Other(Protocol):\n"
                "    enabled: Annotated[bool, m.Field(description='drop')]\n",
                encoding="utf-8",
            )
            entrypoint = (
                Path(__file__).parents[3]
                / "src"
                / "flext_infra"
                / "protocols_bootstrap.py"
            )
            command = (sys.executable, "-P", str(entrypoint), str(root))
            first = TestsProtocolSourceBootstrap.checked_run(command)
            normalized = module.read_text(encoding="utf-8")
            second = TestsProtocolSourceBootstrap.checked_run(command)

            tm.that(first.stdout, has="normalized protocol modules: 1")
            tm.that(second.stdout, has="normalized protocol modules: 0")
            tm.that(normalized, has="title: Annotated[str, 'public-λ']")
            tm.that(normalized, has="        count: int\n")
            tm.that(normalized, lacks="= ...")
            tm.that(normalized, has="enabled: bool")
            tm.that(normalized.count("@runtime_checkable"), eq=2)
            tm.that(normalized, has="from typing import runtime_checkable")
            tm.that(normalized, has="title: Annotated[str, Field(description='keep')]")
            tm.that(normalized, lacks="from flext_infra import m")
            tm.that(normalized, has="if TYPE_CHECKING:\n    from flext_infra import p")
            tm.that(normalized, lacks="\nfrom flext_infra import p\n")

        @staticmethod
        def test_preserves_runtime_generic_protocol_base() -> None:
            """Generic bases evaluate their facade binding during class creation."""
            source = (
                "from __future__ import annotations\n"
                "from typing import Protocol\n"
                "from flext_cli import p, t\n"
                "class Ports:\n"
                "    class Service(p.Service[t.JsonDict], Protocol):\n"
                "        def execute(self) -> p.Result[t.JsonDict]: ...\n"
            )
            normalized = normalize_protocol_source(source, package_name="flext_infra")
            tm.that(normalized, has="from flext_cli import p, t")
            tm.that(normalized, lacks="from flext_infra import p")
            tm.that(normalized, has="p.Service[t.JsonDict]")
            compile(normalized, "<native-protocol-base>", "exec")

        @staticmethod
        @c.Tests.MARK.parametrize(
            ("future", "runtime"), [(True, False), (True, True), (False, False)]
        )
        def test_preserves_declared_facade_origin_and_runtime_uses(
            tmp_path: Path,
            native_consumer: p.Tests.NativeConsumer,
            *,
            future: bool,
            runtime: bool,
        ) -> None:
            """Real protocol imports keep their origin and evaluated references."""
            source = (
                ("from __future__ import annotations\n" if future else "")
                + "from typing import Protocol\n"
                + "from flext_cli import p\n"
                + "class Reader(Protocol):\n"
                + "    def read(self) -> p.Result[bool]: ...\n"
                + ("result_contract = p.Result\n" if runtime else "")
            )
            normalized = normalize_protocol_source(source, package_name="flext_infra")
            expected = ("    " if future and not runtime else "") + (
                "from flext_cli import p"
            )
            tm.ok(expected in normalized.splitlines())
            tm.ok("from flext_infra import p" not in normalized)
            tm.that(
                normalize_protocol_source(normalized, package_name="flext_infra"),
                eq=normalized,
            )
            (tmp_path / "runtime_protocol.py").write_text(normalized, encoding="utf-8")
            probe = (
                "from runtime_protocol import result_contract\n"
                "from flext_cli import p\n"
                "from flext_tests import tm\n"
                "tm.ok(result_contract is p.Result)\n"
                if runtime
                else (
                    "from runtime_protocol import Reader\n"
                    "from typing import is_protocol\n"
                    "from flext_tests import tm\n"
                    "tm.ok(is_protocol(Reader))\n"
                )
            )
            native_consumer(
                f"sys.path.insert(0, {str(tmp_path)!r})\n{probe}",
                cwd=tmp_path,
            )

        @staticmethod
        def test_invalid_protocol_source_retains_original_syntax_error(
            tmp_path: Path,
        ) -> None:
            """Projection preserves the compiler's first failure and source location."""
            source = (
                "from typing import Protocol, runtime_checkable\n"
                "\n"
                "class Ports:\n"
                "    @runtime_checkable\n"
                "    class Broken(Protocol):\n"
                "        ready: bool\n"
                "        @property\n"
                "\n"
                "    @runtime_checkable\n"
                "    class Valid(Protocol):\n"
                "        @property\n"
                "        def name(self) -> str: ...\n"
            )
            filename = str(tmp_path / "decorators.py")
            with u.Tests.raises(SyntaxError) as original:
                compile(source, filename, "exec")
            with u.Tests.raises(SyntaxError) as projected:
                normalize_protocol_source(
                    source, package_name="flext_infra", filename=filename
                )
            tm.that(type(projected.value), eq=type(original.value))
            tm.that(projected.value.args, eq=original.value.args)

    class TestsBootstrapFacadeMembers:
        """Published members bind on the loaded facade."""

    class TestsProtocolImportCanonicalization:
        """Protocol facade imports converge canonically."""

        @staticmethod
        def test_protocol_members_declare_types_without_values() -> None:
            """A Protocol member keeps its type; no Ellipsis value is assigned."""
            source = (
                "from __future__ import annotations\n"
                "from typing import Protocol, TypeAlias\n\n"
                "class FlextProtocolsReport:\n"
                "    class Package(Protocol):\n"
                "        cut: str\n"
                "        observed_until: str | None = None\n"
                "        total: int = 0\n"
                "        Alias: TypeAlias = int\n"
            )
            rendered = normalize_protocol_source(source, package_name="flext_core")

            tm.that(rendered, has="        observed_until: str | None\n")
            tm.that(rendered, has="        total: int\n")
            tm.that(rendered, has="        Alias: TypeAlias = int\n")
            tm.that(rendered, lacks="= ...")
            tm.that(rendered, lacks="= None")
            tm.that(
                normalize_protocol_source(rendered, package_name="flext_core"),
                eq=rendered,
            )

        @staticmethod
        def test_normalized_protocol_source_has_no_pydantic_import() -> None:
            """The source-only normalizer leaves a Pydantic-free protocol module."""
            source = (
                "from __future__ import annotations\n"
                "from typing import Annotated, Protocol\n"
                "from pydantic import Field\n"
                "from flext_core import m\n\n"
                "class FlextProtocolsConfig:\n"
                "    class ConfigDocument(Protocol):\n"
                "        data: Annotated[str, m.Field(description='drop')]\n"
                "        parent: p.ConfigDocument\n"
            )
            rendered = normalize_protocol_source(source, package_name="flext_core")

            tm.that(rendered, lacks="pydantic")
            tm.that(rendered, lacks="m.Field")
            tm.that(rendered, has="@runtime_checkable")
            tm.that(rendered, has="if TYPE_CHECKING:\n    from flext_core import p")
            tm.that(rendered.count("TYPE_CHECKING"), eq=2)

        @staticmethod
        def test_canonicalizes_competing_lazy_protocol_facade_imports(
            tmp_path: Path,
        ) -> None:
            """Deferred root and ``protocols`` imports converge to one root import."""
            source = (
                "from __future__ import annotations\n"
                "from typing import TYPE_CHECKING, Protocol\n\n"
                "if TYPE_CHECKING:\n"
                "    from example_package.protocols import p\n\n"
                "if TYPE_CHECKING:\n"
                "    from example_package import p\n\n"
                "class Ports:\n"
                "    class Item(Protocol):\n"
                "        value: p.Item\n"
            )
            normalized = normalize_protocol_source(
                source, package_name="example_package"
            )

            tm.that(
                normalize_protocol_source(normalized, package_name="example_package"),
                eq=normalized,
            )
            tm.that(normalized.count("from example_package import p"), eq=1)
            tm.that(normalized, lacks="from example_package.protocols import p")
            tm.that(
                normalized, has="if TYPE_CHECKING:\n    from example_package import p"
            )

            package = tmp_path / "example_package"
            protocols = package / "_protocols"
            protocols.mkdir(parents=True)
            (package / "__init__.py").write_text("", encoding="utf-8")
            (protocols / "__init__.py").write_text("", encoding="utf-8")
            (protocols / "ports.py").write_text(normalized, encoding="utf-8")
            environment = {**os.environ, "PYTHONPATH": str(tmp_path)}
            TestsProtocolSourceBootstrap.checked_run(
                (sys.executable, "-c", "import example_package._protocols.ports"),
                cwd=tmp_path,
                env=environment,
            )

        @staticmethod
        def test_canonicalizes_multiple_type_checking_blocks_without_overlap() -> None:
            """Deferred ``p`` imports converge and keep sibling facade imports."""
            source = (
                "from __future__ import annotations\n"
                "from typing import TYPE_CHECKING, Protocol\n\n"
                "if TYPE_CHECKING:\n"
                "    from example_package.protocols import p\n\n"
                "if TYPE_CHECKING:\n"
                "    from example_package import t\n"
                "    from example_package import p\n\n"
                "class Ports:\n"
                "    class Item(Protocol):\n"
                "        value: p.Item\n"
                "        metadata: t.JsonValue\n"
            )

            normalized = normalize_protocol_source(
                source, package_name="example_package"
            )

            tm.that(
                normalize_protocol_source(normalized, package_name="example_package"),
                eq=normalized,
            )
            tm.that(normalized.count("from example_package import p"), eq=1)
            tm.that(normalized, lacks="from example_package.protocols import p")
            tm.that(normalized, has="    from example_package import t")
            compile(normalized, "<multiple-type-checking-blocks>", "exec")

    class TestsProtocolFacadePublication:
        """Protocol facades publish canonical holders."""

        @staticmethod
        def test_merges_existing_lazy_exports_with_generated_protocol_holders(
            tmp_path: Path,
        ) -> None:
            """A generated protocol barrel retains live owned mappings per render."""
            root = tmp_path / "repository"
            protocol_root = root / "src" / "flext_infra" / "_protocols"
            protocol_root.mkdir(parents=True)
            (protocol_root.parent / "__init__.py").touch()
            core = root / "src" / "flext_core"
            core.mkdir()
            (core / "__init__.py").touch()
            (core / "lazy.py").write_text(
                "from importlib import import_module\n\n"
                "def install_lazy_exports("
                "name, namespace, mapping, *, public_exports):\n"
                "    def resolve(attribute):\n"
                "        module = import_module(mapping[attribute], name)\n"
                "        value = getattr(module, attribute)\n"
                "        namespace[attribute] = value\n"
                "        return value\n"
                "    namespace['__getattr__'] = resolve\n",
                encoding="utf-8",
            )
            (protocol_root / "legacy.py").write_text(
                "class ExistingBarrelExport:\n    pass\n",
                encoding="utf-8",
            )
            (protocol_root / "generated.py").write_text(
                "class FlextInfraProtocolsGenerated:\n    pass\n",
                encoding="utf-8",
            )
            barrel = protocol_root / "__init__.py"
            barrel.write_text(
                "# AUTO-GENERATED FILE — Regenerate with: make gen\n"
                "from types import MappingProxyType\n"
                "from flext_core.lazy import install_lazy_exports\n"
                "__all__ = ('ExistingBarrelExport',)\n"
                "install_lazy_exports(__name__, globals(), "
                "MappingProxyType({'ExistingBarrelExport': '.legacy'}), "
                "public_exports=__all__)\n",
                encoding="utf-8",
            )

            u.Infra.publish_protocol_facades(root)
            rendered = barrel.read_text(encoding="utf-8")
            u.Infra.publish_protocol_facades(root)

            tm.that(barrel.read_text(encoding="utf-8"), eq=rendered)
            tm.that(rendered, has='"ExistingBarrelExport": ".legacy"')
            tm.that(rendered, has='"FlextInfraProtocolsGenerated": ".generated"')
            environment = {**os.environ, "PYTHONPATH": str(root / "src")}
            TestsProtocolSourceBootstrap.checked_run(
                (
                    sys.executable,
                    "-c",
                    (
                        "from flext_infra._protocols import ("
                        "ExistingBarrelExport, FlextInfraProtocolsGenerated); "
                        "assert ExistingBarrelExport.__name__ == "
                        "'ExistingBarrelExport'; "
                        "assert FlextInfraProtocolsGenerated.__name__ == "
                        "'FlextInfraProtocolsGenerated'"
                    ),
                ),
                cwd=root,
                env=environment,
            )

        @staticmethod
        def test_composes_private_partition_into_one_canonical_public_owner(
            tmp_path: Path,
        ) -> None:
            """Partition members stay private while their parent holder is public."""
            root = tmp_path / "repository"
            protocol_root = root / "src" / "flext_infra" / "_protocols"
            partition = protocol_root / "_codegen"
            partition.mkdir(parents=True)
            (protocol_root.parent / "__init__.py").touch()
            for module, holder in (
                ("fix", "FlextInfraProtocolsCodegenFix"),
                ("lazy_init", "FlextInfraProtocolsCodegenLazyInit"),
                ("pipeline", "FlextInfraProtocolsCodegenPipeline"),
                ("scaffold", "FlextInfraProtocolsCodegenScaffold"),
                ("transaction", "FlextInfraProtocolsCodegenTransaction"),
            ):
                (partition / f"{module}.py").write_text(
                    f"class {holder}:\n    pass\n", encoding="utf-8"
                )

            u.Infra.publish_protocol_facades(root)
            owner = protocol_root / "codegen.py"
            rendered = owner.read_text(encoding="utf-8")
            barrel = (protocol_root / "__init__.py").read_text(encoding="utf-8")
            u.Infra.publish_protocol_facades(root)

            tm.that(owner.read_text(encoding="utf-8"), eq=rendered)
            tm.that(rendered, has="class FlextInfraProtocolsCodegen(")
            tm.that(rendered, has="FlextInfraProtocolsCodegenFix")
            tm.that(rendered, has="FlextInfraProtocolsCodegenTransaction")
            tm.that(barrel, has='"FlextInfraProtocolsCodegen": ".codegen"')
            tm.that(barrel, lacks='FlextInfraProtocolsCodegenFix": "._codegen.fix')
            tm.that(
                barrel,
                lacks='FlextInfraProtocolsCodegenTransaction": "._codegen.transaction',
            )
            facade = (root / "src" / "flext_infra" / "protocols.py").read_text(
                encoding="utf-8"
            )
            tm.that(facade.count("FlextInfraProtocolsCodegen"), eq=2)

        @staticmethod
        def test_reduces_aggregate_facade_to_maximal_canonical_holders(
            tmp_path: Path,
        ) -> None:
            """The aggregate imports an owner, not the parts it already contains."""
            root = tmp_path / "repository"
            package = root / "src" / "flext_infra"
            protocol_root = package / "_protocols"
            protocol_root.mkdir(parents=True)
            (package / "__init__.py").touch()
            cli = root / "src" / "flext_cli"
            cli.mkdir()
            (cli / "__init__.py").write_text(
                "class FlextCliProtocols:\n    pass\n", encoding="utf-8"
            )
            core = root / "src" / "flext_core"
            core.mkdir()
            (core / "__init__.py").touch()
            (core / "lazy.py").write_text(
                "def install_lazy_exports("
                "name, namespace, mapping, *, public_exports):\n"
                "    return None\n",
                encoding="utf-8",
            )
            (protocol_root / "b.py").write_text(
                "class FlextInfraProtocolsB:\n    pass\n", encoding="utf-8"
            )
            (protocol_root / "c.py").write_text(
                "class FlextInfraProtocolsC:\n    pass\n", encoding="utf-8"
            )
            (protocol_root / "a.py").write_text(
                "from flext_infra._protocols.b import FlextInfraProtocolsB\n"
                "from flext_infra._protocols.c import FlextInfraProtocolsC\n\n"
                "class FlextInfraProtocolsA("
                "FlextInfraProtocolsB, FlextInfraProtocolsC):\n"
                "    pass\n",
                encoding="utf-8",
            )

            u.Infra.publish_protocol_facades(root)

            facade = (package / "protocols.py").read_text(encoding="utf-8")
            tm.that(facade, has="class Infra(\n        FlextInfraProtocolsA,")
            tm.that(facade, lacks="FlextInfraProtocolsB,")
            tm.that(facade, lacks="FlextInfraProtocolsC,")
            environment = {**os.environ, "PYTHONPATH": str(root / "src")}
            TestsProtocolSourceBootstrap.checked_run(
                (
                    sys.executable,
                    "-c",
                    (
                        "from flext_infra.protocols import p; "
                        "assert p.Infra.__bases__[0].__name__ == 'FlextInfraProtocolsA'"
                    ),
                ),
                cwd=root,
                env=environment,
            )

        @staticmethod
        def test_inherits_nested_protocol_members_on_aggregate_facade(
            tmp_path: Path,
        ) -> None:
            """The facade exposes the original nested protocol through its MRO."""
            root = tmp_path / "repository"
            package = root / "src" / "flext_infra"
            protocol_root = package / "_protocols"
            protocol_root.mkdir(parents=True)
            (package / "__init__.py").touch()
            cli = root / "src" / "flext_cli"
            cli.mkdir()
            (cli / "__init__.py").write_text(
                "class FlextCliProtocols:\n    pass\n", encoding="utf-8"
            )
            core = root / "src" / "flext_core"
            core.mkdir()
            (core / "__init__.py").touch()
            (core / "lazy.py").write_text(
                "def install_lazy_exports("
                "name, namespace, mapping, *, public_exports):\n"
                "    return None\n",
                encoding="utf-8",
            )
            (protocol_root / "alpha.py").write_text(
                "class FlextInfraProtocolsAlpha:\n    class Unique:\n        pass\n",
                encoding="utf-8",
            )
            (protocol_root / "beta.py").write_text(
                "class FlextInfraProtocolsBeta:\n    class Duplicate:\n        pass\n",
                encoding="utf-8",
            )
            (protocol_root / "gamma.py").write_text(
                "class FlextInfraProtocolsGamma:\n    class Duplicate:\n        pass\n",
                encoding="utf-8",
            )

            u.Infra.publish_protocol_facades(root)

            environment = {**os.environ, "PYTHONPATH": str(root / "src")}
            TestsProtocolSourceBootstrap.checked_run(
                (
                    sys.executable,
                    "-c",
                    (
                        "from flext_infra.protocols import p; "
                        "from flext_infra._protocols.alpha import "
                        "FlextInfraProtocolsAlpha; "
                        "assert p.Infra.Unique is FlextInfraProtocolsAlpha.Unique; "
                        "assert not hasattr(p.Infra, 'm')"
                    ),
                ),
                cwd=root,
                env=environment,
            )

        @staticmethod
        def test_generated_aggregate_facade_passes_scoped_ruff_check(
            tmp_path: Path,
        ) -> None:
            """The source bootstrap emits a self-contained, Ruff-clean public facade."""
            root = tmp_path / "repository"
            package = root / "src" / "flext_infra"
            protocol_root = package / "_protocols"
            protocol_root.mkdir(parents=True)
            (package / "__init__.py").touch()
            (root / "pyproject.toml").write_text(
                '[project]\nname = "flext-infra"\n', encoding="utf-8"
            )
            cli = root / "src" / "flext_cli"
            cli.mkdir()
            (cli / "__init__.py").write_text(
                "class FlextCliProtocols:\n    pass\n", encoding="utf-8"
            )
            core = root / "src" / "flext_core"
            core.mkdir()
            (core / "__init__.py").touch()
            (core / "lazy.py").write_text(
                "from importlib import import_module\n\n"
                "def install_lazy_exports("
                "name, namespace, mapping, *, public_exports):\n"
                "    def resolve(attribute):\n"
                "        module = import_module(mapping[attribute], name)\n"
                "        value = getattr(module, attribute)\n"
                "        namespace[attribute] = value\n"
                "        return value\n"
                "    namespace['__getattr__'] = resolve\n",
                encoding="utf-8",
            )
            for module, holder in (
                ("zeta", "FlextInfraProtocolsZeta"),
                ("alpha", "FlextInfraProtocolsAlpha"),
                (
                    "project_artifacts",
                    "FlextInfraProtocolsProjectArtifacts",
                ),
            ):
                (protocol_root / f"{module}.py").write_text(
                    f"class {holder}:\n    pass\n", encoding="utf-8"
                )

            u.Infra.publish_protocol_facades(root)

            facade = package / "protocols.py"
            source = facade.read_text(encoding="utf-8")
            tm.that(source, has="Copyright (c) 2026 FLEXT Team. All rights reserved.")
            tm.that(source, has="SPDX-License-Identifier: MIT")
            tm.that(
                source.index("_protocols.alpha") < source.index("_protocols.zeta"),
                truth=True,
            )
            barrel = protocol_root / "__init__.py"
            barrel_source = barrel.read_text(encoding="utf-8")
            tm.that(barrel_source, has="if TYPE_CHECKING:")
            for module, holder in (
                ("alpha", "FlextInfraProtocolsAlpha"),
                (
                    "project_artifacts",
                    "FlextInfraProtocolsProjectArtifacts",
                ),
                ("zeta", "FlextInfraProtocolsZeta"),
            ):
                tm.that(
                    barrel_source, has=f"from flext_infra._protocols.{module} import"
                )
                tm.that(barrel_source, has=holder)
            TestsProtocolSourceBootstrap.checked_run(
                (
                    str(Path(sys.executable).with_name("ruff")),
                    "check",
                    "--config",
                    str(Path(__file__).parents[3] / "pyproject.toml"),
                    str(facade),
                ),
            )
            TestsProtocolSourceBootstrap.checked_run(
                (
                    str(Path(sys.executable).with_name("ruff")),
                    "check",
                    "--config",
                    str(Path(__file__).parents[3] / "pyproject.toml"),
                    str(barrel),
                ),
            )
            environment = {**os.environ, "PYTHONPATH": str(root / "src")}
            TestsProtocolSourceBootstrap.checked_run(
                (
                    sys.executable,
                    "-c",
                    (
                        "from flext_infra import _protocols\n"
                        "assert not any(name in vars(_protocols) for name in "
                        "_protocols.__all__)\n"
                        "for name in _protocols.__all__:\n"
                        "    assert getattr(_protocols, name).__name__ == name\n"
                    ),
                ),
                cwd=root,
                env=environment,
            )

        @staticmethod
        def test_rejects_cyclic_canonical_holder_inheritance(tmp_path: Path) -> None:
            """A genuine owner cycle fails before a broken facade is rendered."""
            root = tmp_path / "repository"
            protocol_root = root / "src" / "flext_infra" / "_protocols"
            protocol_root.mkdir(parents=True)
            (protocol_root.parent / "__init__.py").touch()
            (protocol_root / "left.py").write_text(
                "from flext_infra._protocols.right import FlextInfraProtocolsRight\n"
                "class FlextInfraProtocolsLeft(FlextInfraProtocolsRight):\n    pass\n",
                encoding="utf-8",
            )
            (protocol_root / "right.py").write_text(
                "from flext_infra._protocols.left import FlextInfraProtocolsLeft\n"
                "class FlextInfraProtocolsRight(FlextInfraProtocolsLeft):\n    pass\n",
                encoding="utf-8",
            )

            with u.Tests.raises(ValueError, match="cyclic protocol holder inheritance"):
                u.Infra.publish_protocol_facades(root)

        @staticmethod
        def test_relocates_divergent_generated_base_contract_to_canonical_owner(
            tmp_path: Path,
        ) -> None:
            """A stale generated Base duplicate yields to its model-path owner."""
            root = tmp_path / "repository"
            protocol_root = root / "src" / "flext_infra" / "_protocols"
            protocol_root.mkdir(parents=True)
            (protocol_root.parent / "__init__.py").touch()
            model_root = root / "src" / "flext_infra" / "_models"
            model_root.mkdir()
            (model_root / "workspace.py").write_text(
                (
                    "class FlextInfraModelsWorkspace:\n"
                    "    class ProjectInfo:\n        pass\n"
                ),
                encoding="utf-8",
            )
            base = protocol_root / "base.py"
            base.write_text(
                "# AUTO-GENERATED FILE - Source bootstrap legacy protocol holder.\n"
                "from typing import Protocol, runtime_checkable\n\n"
                "class FlextInfraProtocolsBase(Protocol):\n"
                "    @runtime_checkable\n"
                "    class ProjectInfo(Protocol):\n"
                "        @property\n"
                "        def region(self) -> str: ...\n",
                encoding="utf-8",
            )
            workspace = protocol_root / "workspace.py"
            projected = (
                "from typing import Protocol, runtime_checkable\n\n"
                "class FlextInfraProtocolsWorkspace(Protocol):\n"
                "    @runtime_checkable\n"
                "    class ProjectInfo(Protocol):\n"
                "        @property\n"
                "        def name(self) -> str: ...\n"
            )

            (root / "pyproject.toml").write_text(
                '[project]\nname="flext-infra"\n', encoding="utf-8"
            )
            retired = consolidate_protocol_owners(
                root,
                {workspace.relative_to(root): projected},
            )
            workspace.write_text(projected, encoding="utf-8")
            u.Infra.publish_protocol_facades(root)

            tm.that(retired, eq=(base,))
            tm.that(base.read_text(encoding="utf-8"), lacks="class ProjectInfo")
            environment = {**os.environ, "PYTHONPATH": str(root / "src")}
            TestsProtocolSourceBootstrap.checked_run(
                (
                    sys.executable,
                    "-c",
                    (
                        "from flext_infra.protocols import p; "
                        "from flext_infra._protocols.workspace import "
                        "FlextInfraProtocolsWorkspace; "
                        "assert p.Infra.ProjectInfo is "
                        "FlextInfraProtocolsWorkspace.ProjectInfo; "
                        "assert hasattr(p.Infra.ProjectInfo, 'name'); "
                        "assert not hasattr(p.Infra.ProjectInfo, 'region')"
                    ),
                ),
                cwd=root,
                env=environment,
            )

        @staticmethod
        def test_keeps_protocol_only_base_contract_in_fresh_public_facade(
            tmp_path: Path,
        ) -> None:
            """A relocated model contract keeps sibling protocol-only ports."""
            root = tmp_path / "repository"
            package = root / "src" / "flext_infra"
            protocol_root = package / "_protocols"
            protocol_root.mkdir(parents=True)
            (package / "__init__.py").touch()
            cli = root / "src" / "flext_cli"
            cli.mkdir()
            (cli / "__init__.py").write_text(
                "class FlextCliProtocols:\n    pass\n", encoding="utf-8"
            )
            core = root / "src" / "flext_core"
            core.mkdir()
            (core / "__init__.py").touch()
            (core / "lazy.py").write_text(
                "def install_lazy_exports("
                "name, namespace, mapping, *, public_exports):\n"
                "    return None\n",
                encoding="utf-8",
            )
            model_root = package / "_models"
            model_root.mkdir()
            (model_root / "workspace.py").write_text(
                (
                    "class FlextInfraModelsWorkspace:\n"
                    "    class ProjectInfo:\n        pass\n"
                ),
                encoding="utf-8",
            )
            base = protocol_root / "base.py"
            base.write_text(
                "# AUTO-GENERATED FILE - Source bootstrap legacy protocol holder.\n"
                "from typing import Protocol, runtime_checkable\n\n"
                "class FlextInfraProtocolsBase(Protocol):\n"
                "    @runtime_checkable\n"
                "    class ProjectInfo(Protocol):\n"
                "        name: str\n\n"
                "    @runtime_checkable\n"
                "    class DocsArtifactPlannerFactory(Protocol):\n"
                "        def __call__(self) -> object: ...\n",
                encoding="utf-8",
            )
            workspace = protocol_root / "workspace.py"
            projected = (
                "from typing import Protocol, runtime_checkable\n\n"
                "class FlextInfraProtocolsWorkspace(Protocol):\n"
                "    @runtime_checkable\n"
                "    class ProjectInfo(Protocol):\n"
                "        name: str\n"
            )
            workspace.write_text(projected, encoding="utf-8")
            (protocol_root / "__init__.py").write_text(
                "# AUTO-GENERATED FILE - Source bootstrap protocol exports.\n",
                encoding="utf-8",
            )

            (root / "pyproject.toml").write_text(
                '[project]\nname="flext-infra"\n', encoding="utf-8"
            )
            consolidate_protocol_owners(root, {workspace.relative_to(root): projected})
            planned = plan_protocol_facades(root)

            tm.that(base.read_text(encoding="utf-8"), lacks="class ProjectInfo")
            facade = planned[package / "protocols.py"]
            tm.that(facade, has="FlextInfraProtocolsBase")
            (protocol_root / "__init__.py").write_text(
                planned[protocol_root / "__init__.py"], encoding="utf-8"
            )
            (package / "protocols.py").write_text(facade, encoding="utf-8")
            environment = {**os.environ, "PYTHONPATH": str(root / "src")}
            TestsProtocolSourceBootstrap.checked_run(
                (
                    sys.executable,
                    "-c",
                    (
                        "from flext_infra.protocols import p; "
                        "assert p.Infra.DocsArtifactPlannerFactory; "
                        "assert getattr(p.Infra.DocsArtifactPlannerFactory, "
                        "'_is_runtime_protocol', False); "
                        "assert not hasattr(p.Infra, 'm')"
                    ),
                ),
                cwd=root,
                env=environment,
            )

        @staticmethod
        def test_rejects_incompatible_legacy_contract_during_relocation(
            tmp_path: Path,
        ) -> None:
            """An authored divergence is never silently replaced by bootstrap."""
            root = tmp_path / "repository"
            protocol_root = root / "src" / "flext_infra" / "_protocols"
            protocol_root.mkdir(parents=True)
            model_root = root / "src" / "flext_infra" / "_models"
            model_root.mkdir()
            (model_root / "workspace.py").write_text(
                (
                    "class FlextInfraModelsWorkspace:\n"
                    "    class ProjectInfo:\n        pass\n"
                ),
                encoding="utf-8",
            )
            (protocol_root / "base.py").write_text(
                "from typing import Protocol\n\n"
                "class FlextInfraProtocolsBase(Protocol):\n"
                "    class ProjectInfo(Protocol):\n"
                "        region: str\n",
                encoding="utf-8",
            )
            workspace = protocol_root / "workspace.py"
            projected = (
                "from typing import Protocol\n\n"
                "class FlextInfraProtocolsWorkspace(Protocol):\n"
                "    class ProjectInfo(Protocol):\n"
                "        name: str\n"
            )

            (root / "pyproject.toml").write_text(
                '[project]\nname="flext-infra"\n', encoding="utf-8"
            )
            with u.Tests.raises(
                ValueError, match="incompatible legacy protocol contract"
            ):
                consolidate_protocol_owners(
                    root,
                    {workspace.relative_to(root): projected},
                )
