"""Public evidence for declared utility-facade projection.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path
from typing import Literal

import pytest

from flext_infra import config
from flext_infra.codegen import FlextInfraCodegenConform
from tests import c, m, p, t, tm, u


class UtilityFacadePublication:
    """Exercise public facade publication and native contract identities."""

    @pytest.mark.parametrize(
        "binding", ["canonical", "foreign", "renamed", "duplicate", "annotation"]
    )
    @pytest.mark.parametrize("model", [False, True])
    @pytest.mark.parametrize("constructor", ["ConfigDict", "m.ConfigDict"])
    def test_explicit_owner_config_requires_canonical_metadata(
        self,
        tmp_path: Path,
        binding: str,
        native_consumer: p.Tests.NativeConsumer,
        constructor: str,
        *,
        model: bool,
    ) -> None:
        """Preserve native owner configuration without admitting ambiguous aliases."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        directory = u.Infra.facade_families()["u"].directory
        self._write(package / "__init__.py", "")
        self._write(
            package / directory / "__init__.py",
            "from .owner import Owner, Foreign\n__all__ = ['Owner', 'Foreign']\n",
        )
        self._write(
            package / directory / "owner.py",
            "from pydantic import BaseModel, ConfigDict\n"
            "from flext_core import m\n"
            + ("class Owner(BaseModel):\n" if model else "class Owner:\n")
            + f"    model_config = {constructor}(ignored_types=(type,))\n"
            "class Foreign:\n    model_config = {}\n"
            "__all__ = ['Owner']\n",
        )
        metadata = {
            "canonical": "    model_config = Owner.model_config\n",
            "foreign": "    model_config = Foreign.model_config\n",
            "renamed": "    Other = Owner.model_config\n",
            "duplicate": (
                "    model_config = Owner.model_config\n    model_config = Owner\n"
            ),
            "annotation": "    model_config: type[Owner] = Owner.model_config\n",
        }[binding]
        facade = package / "utilities.py"
        self._write(
            facade,
            f"from {package.name}.{directory} import Owner, Foreign\n"
            "class Utilities:\n" + metadata + "    Cli = Owner\nu = Utilities\n"
            "__all__ = ['Utilities', 'u']\n",
        )
        if binding != "canonical":
            with pytest.raises(
                ValueError, match="Ambiguous explicit facade class binding"
            ):
                u.Infra.render_utility_facade(package)
            return
        rendered = tm.not_none(u.Infra.render_utility_facade(package))
        self._write(facade, rendered)
        tm.that(u.Infra.render_utility_facade(package), eq=rendered)
        native_consumer(
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            f"from {package.name}.utilities import u\n"
            f"from {package.name}.{directory}.owner import Owner\n"
            "assert Owner not in u.__mro__\n"
            "assert u.model_config == Owner.model_config\n"
            "assert u.Cli is Owner\n",
            cwd=root,
        )

    def test_initializer_retires_exports_moved_into_class_owners(
        self,
        tmp_path: Path,
    ) -> None:
        """Generated barrels follow live owners, not their obsolete export map."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        child = package / "services"
        module = child / "engine.py"
        self._write(package / "__init__.py", "")
        self._write(child / "__init__.py", "")
        self._write(
            module, "def build_plan():\n    return 7\n__all__ = ['build_plan']\n"
        )
        tm.ok(u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)))
        self._write(
            module,
            "class Engine:\n    @staticmethod\n"
            "    def build_plan():\n        return 7\n"
            "__all__ = ['Engine']\n",
        )
        tm.ok(u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)))
        rendered = (child / "__init__.py").read_text(encoding="utf-8")
        tm.that("build_plan" in rendered, eq=False)
        tm.ok(u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)))
        tm.that((child / "__init__.py").read_text(encoding="utf-8"), eq=rendered)
        result = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    (
                        f"from {package.name}.services import Engine; "
                        "assert Engine.build_plan() == 7"
                    ),
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            )
        )
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True, msg=result.stderr)

    @pytest.mark.parametrize("family", tuple(u.Infra.facade_families()))
    @pytest.mark.parametrize("nested", [False, True])
    @pytest.mark.parametrize(
        "publication",
        [
            (origin, source_root)
            for origin in ("leaf", "barrel")
            for source_root in (
                None,
                *config.Infra.tooling.tools.pyright.path_rules.test_like_dirs,
                "auxiliary",
            )
        ],
    )
    def test_explicit_owner_classes_preserve_publication_identity(
        self,
        tmp_path: Path,
        family: Literal["c", "t", "p", "m", "u"],
        publication: t.Pair[str, str | None],
        *,
        nested: bool,
    ) -> None:
        """Class publications remain usable as real Pydantic annotation owners."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        u.Tests.standalone_workspace(root, root.name)
        if publication[1] is not None:
            package = root / publication[1]
        u.Tests.copy_tracked_mise_seeds(root)
        definition = u.Infra.facade_families()[family]
        self._write(package / "__init__.py", "")
        self._write(
            package / definition.directory / "__init__.py",
            "from .base import OwnerBase\n"
            "from .vocabulary import OwnerVocabulary\n"
            "__all__ = ['OwnerBase', 'OwnerVocabulary']\n",
        )
        for module, name in (("base", "OwnerBase"), ("vocabulary", "OwnerVocabulary")):
            self._write(
                package / definition.directory / f"{module}.py",
                "from pydantic import BaseModel\n"
                + (
                    f"class {name}(BaseModel):\n    value: int = 7\n"
                    if module == "base"
                    else f"class {name}:\n    value = 7\n"
                )
                + f"    class {name}Entity:\n        pass\n"
                f"__all__ = [{name!r}]\n",
            )
        facade = package / f"{definition.module}.py"
        indent = "        " if nested else "    "
        owner_module = f"{package.name}.{definition.directory}"
        imports = (
            f"from {owner_module}.base import OwnerBase as LocalBase\n"
            f"from {owner_module}.vocabulary import OwnerVocabulary\n"
            if publication[0] == "leaf"
            else f"from {owner_module} import OwnerBase as LocalBase, OwnerVocabulary\n"
        )
        self._write(
            facade,
            '"""Explicit public class facade."""\n'
            + imports
            + "class PublicFacade:\n"
            + ("    class Sample:\n" if nested else "")
            + f"{indent}Base = LocalBase\n"
            + f"{indent}Vocabulary = OwnerVocabulary\n"
            + f"{family} = PublicFacade\n"
            + f"__all__ = ['PublicFacade', {family!r}]\n",
        )
        with u.Infra.facade_source_project(root) as (project, _, sources):
            rendered = (
                u.Infra.render_type_facade(package, facade, sources, project=project)
                if family == "t"
                else tm.not_none(
                    u.Infra.render_utility_facade(
                        package, family=family, project=project, sources=sources
                    )
                )
            )
        plan = tm.ok(
            FlextInfraCodegenConform(repository_root=root).plan(
                u.Tests.conform_request(
                    root,
                    what=c.Infra.CodegenConformSurface.ALL,
                    scope=c.Infra.CodegenConformScope.SELF,
                    mode=c.Infra.CodegenConformMode.CHECK,
                )
            )
        )
        tm.that(plan.issues, empty=True, msg=str(plan.issues))
        tm.that(
            u.Tests.codegen_file_text(
                next(file for file in plan.files if file.path == facade)
            ),
            eq=rendered,
        )
        self._write(facade, rendered)
        if publication[0] == "barrel":
            self._write(package / definition.directory / "__init__.py", "")
        with u.Infra.facade_source_project(root) as (project, _, sources):
            repeated = (
                u.Infra.render_type_facade(package, facade, sources, project=project)
                if family == "t"
                else u.Infra.render_utility_facade(
                    package, family=family, project=project, sources=sources
                )
            )
        tm.that(repeated, eq=rendered)
        result = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    "from importlib import import_module\n"
                    f"facade = import_module('{package.name}.{definition.module}')"
                    ".PublicFacade\n"
                    + ("facade = facade.Sample\n" if nested else "")
                    + f"base = import_module('{package.name}."
                    f"{definition.directory}.base').OwnerBase\n"
                    + f"vocabulary = import_module('{package.name}."
                    f"{definition.directory}.vocabulary').OwnerVocabulary\n"
                    + "assert facade.Base is base\n"
                    + "assert facade.Vocabulary is vocabulary\n"
                    + "assert facade.__bases__ == (object,)\n"
                    + "assert not hasattr(facade, 'value')\n"
                    + "assert not hasattr(facade, 'OwnerBaseEntity')\n"
                    + "from pydantic import BaseModel\n"
                    + "class Payload(BaseModel):\n    item: facade.Base\n"
                    + "payload = Payload.model_validate({'item': {'value': 9}})\n"
                    + "assert type(payload.item) is base\n"
                    + "assert payload.model_dump() == {'item': {'value': 9}}\n",
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            )
        )
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True, msg=result.stderr)

    @pytest.mark.parametrize("family", ["c", "m", "p", "u"])
    @pytest.mark.parametrize("stale_base", [False, True])
    def test_explicit_class_bindings_preserve_authored_upstream_contract(
        self,
        tmp_path: Path,
        family: Literal["c", "m", "p", "u"],
        *,
        stale_base: bool,
    ) -> None:
        """Keep authored bindings and upstream bases without inventing publications."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        spec = u.Infra.facade_families()[family]
        self._write(package / "__init__.py", "")
        self._write(package / spec.directory / "__init__.py", "")
        for name in ("Contracts", "Schema"):
            self._write(
                package / spec.directory / f"{name.lower()}.py",
                f"class SampleFacade{name}:\n"
                f"    class {name}Entity:\n        pass\n"
                f"    {name.upper()}_VALUE = 7\n"
                f"__all__ = ['SampleFacade{name}']\n",
            )
        self._write(
            package.parent / "upstream.py",
            "class Framework:\n    class Sample:\n        pass\n",
        )
        facade = package / f"{spec.module}.py"
        self._write(
            facade,
            "from typing import ClassVar\n"
            "from upstream import Framework\n"
            f"from {package.name}.{spec.directory}.contracts "
            "import SampleFacadeContracts\n\n"
            "class SampleFacade(Framework):\n"
            "    class Sample("
            + ("SampleFacadeContracts, Framework.Sample" if stale_base else "")
            + "):\n"
            "        Contracts: ClassVar[type[SampleFacadeContracts]] = "
            "SampleFacadeContracts\n"
            f"{family} = SampleFacade\n"
            f"__all__ = ['SampleFacade', '{family}']\n",
        )
        rendered = tm.not_none(u.Infra.render_utility_facade(package, family=family))
        self._write(facade, rendered)
        tm.that(u.Infra.render_utility_facade(package, family=family), eq=rendered)
        result = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    (
                        f"from {package.name}.{spec.module} import {family} as facade\n"
                        f"from {package.name}.{spec.directory}.contracts "
                        "import SampleFacadeContracts\n"
                        f"from {package.name}.{spec.directory}.schema "
                        "import SampleFacadeSchema\n"
                        "from upstream import Framework\n"
                        "assert facade.__bases__ == (Framework,)\n"
                        "assert facade.Sample.__bases__ == "
                        + ("(Framework.Sample,)\n" if stale_base else "(object,)\n")
                        + "assert facade.Sample.Contracts is SampleFacadeContracts\n"
                        "assert facade.Sample.Contracts.ContractsEntity is "
                        "SampleFacadeContracts.ContractsEntity\n"
                        "assert not hasattr(facade.Sample, 'Schema')\n"
                        "assert not hasattr(facade.Sample, 'CONTRACTS_VALUE')\n"
                        "assert not hasattr(facade.Sample, 'SampleFacadeContracts')\n"
                    ),
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            )
        )
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True, msg=result.stderr)

    @pytest.mark.parametrize("family", ["c", "t", "p", "m", "u"])
    @pytest.mark.parametrize(
        "invalid",
        [
            "Other = missing",
            "Other = Owner.value",
            "Base = Owner\n    Base = Owner",
            "Other: type[str] = Owner",
            "type Other = str",
        ],
    )
    def test_explicit_publication_rejects_ambiguous_bindings(
        self,
        tmp_path: Path,
        family: Literal["c", "t", "p", "m", "u"],
        invalid: str,
    ) -> None:
        """Invalid publications fail through the public boundary for every family."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        spec = u.Infra.facade_families()[family]
        self._write(package / "__init__.py", "")
        self._write(package / spec.directory / "__init__.py", "")
        self._write(
            package / spec.directory / "owner.py",
            "class Owner:\n    value = 7\n__all__ = ['Owner']\n",
        )
        facade = package / f"{spec.module}.py"
        self._write(
            facade,
            '"""Explicit publication."""\n'
            f"from {package.name}.{spec.directory}.owner import Owner\n"
            "class PublicFacade:\n    Base = Owner\n"
            f"    {invalid}\n{family} = PublicFacade\n"
            f"__all__ = ['PublicFacade', '{family}']\n",
        )
        with u.Infra.facade_source_project(root) as (project, _, sources):
            if family == "t":
                with pytest.raises(ValueError, match=r"[Aa]mbiguous|Non-class binding"):
                    u.Infra.render_type_facade(
                        package, facade, sources, project=project
                    )
            else:
                with pytest.raises(ValueError, match=r"[Aa]mbiguous|Non-class binding"):
                    u.Infra.render_utility_facade(
                        package, family=family, project=project, sources=sources
                    )

    @pytest.mark.parametrize("family", ["c", "t", "m", "p", "u"])
    def test_unselected_inherited_sdk_contract_keeps_real_mro(
        self,
        tmp_path: Path,
        family: Literal["c", "t", "m", "p", "u"],
        native_consumer: p.Tests.NativeConsumer,
    ) -> None:
        """Class-only publication does not globally migrate existing SDK inheritance."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        spec = u.Infra.facade_families()[family]
        self._write(package / "__init__.py", "")
        self._write(package / spec.directory / "__init__.py", "")
        self._write(
            package / spec.directory / "owner.py",
            "from pydantic import BaseModel\n"
            "class Owner(BaseModel):\n    value: int\n"
            "__all__ = ['Owner']\n",
        )
        facade = package / f"{spec.module}.py"
        self._write(
            facade,
            '"""Inherited SDK facade."""\n'
            f"from {package.name}.{spec.directory}.owner import Owner\n"
            "class PublicFacade(Owner):\n    pass\n"
            f"{family} = PublicFacade\n__all__ = ['PublicFacade', '{family}']\n",
        )
        with u.Infra.facade_source_project(root) as (project, _, sources):
            rendered = (
                u.Infra.render_type_facade(package, facade, sources, project=project)
                if family == "t"
                else tm.not_none(
                    u.Infra.render_utility_facade(
                        package, family=family, project=project, sources=sources
                    )
                )
            )
        self._write(facade, rendered)
        with u.Infra.facade_source_project(root) as (project, _, sources):
            repeated = (
                u.Infra.render_type_facade(package, facade, sources, project=project)
                if family == "t"
                else u.Infra.render_utility_facade(
                    package, family=family, project=project, sources=sources
                )
            )
        tm.that(repeated, eq=rendered)
        native_consumer(
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            f"from {package.name}.{spec.module} import PublicFacade\n"
            f"from {package.name}.{spec.directory}.owner import Owner\n"
            "assert PublicFacade.__bases__ == (Owner,)\n"
            "assert PublicFacade.model_validate({'value': 8}).value == 8\n",
            cwd=root,
        )

    @pytest.mark.parametrize("header", ["plain", "protocol", "commented"])
    def test_long_protocol_owner_bases_are_canonical_before_publication(
        self,
        tmp_path: Path,
        header: str,
    ) -> None:
        """Long owner composition preserves comments, identities and a fixed point."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        self._write(package / "__init__.py", "")
        self._write(package / "_protocols" / "__init__.py", "")
        width = u.Infra.native_tool_setting(
            config.Infra.tooling, "ruff", "line-length", int
        )
        names = tuple(f"Owner{index}" + "X" * (width // 4) for index in range(5))
        imports: list[str] = []
        aliases: list[str] = []
        for index, name in enumerate(names):
            self._write(
                package / "_protocols" / f"owner_{index}.py",
                "from typing import Protocol\n\n"
                f"class {name}:\n"
                f"    class Contract{index}(Protocol):\n"
                "        value: str\n"
                f"__all__ = [{name!r}]\n",
            )
            imports.append(
                f"from {package.name}._protocols.owner_{index} import {name}\n"
            )
            aliases.append(f"        Contract{index} = {name}.Contract{index}\n")
        self._write(
            package / "_protocols" / "__init__.py",
            "".join(
                f"from .owner_{index} import {name}\n"
                for index, name in enumerate(names)
            )
            + f"__all__ = {list(names)!r}\n",
        )
        self._write(
            package.parent / "upstream.py",
            "class ExistingOwner:\n    pass\n",
        )
        declaration = {
            "plain": "    class Sample:\n",
            "protocol": "    class Sample(Protocol):\n",
            "commented": (
                "    class Sample(  # Preserve opening\n"
                "        ExistingOwner,  # Preserve existing owner\n"
                "    ):\n"
            ),
        }[header]
        facade = package / "protocols.py"
        self._write(
            facade,
            "from typing import Protocol\nfrom upstream import ExistingOwner\n"
            + "".join(imports)
            + "\nclass SampleProtocols:\n"
            + declaration
            + "".join(aliases)
            + "\np = SampleProtocols\n__all__ = ['SampleProtocols', 'p']\n",
        )
        rendered = tm.not_none(u.Infra.render_utility_facade(package, family="p"))
        tm.that(max(map(len, rendered.splitlines())), lte=width)
        for name in names:
            tm.that(rendered, has=f"        {name},\n")
        if header == "commented":
            tm.that(rendered, has="# Preserve opening")
            tm.that(rendered, has="# Preserve existing owner")
        self._write(facade, rendered)
        tm.that(u.Infra.render_utility_facade(package, family="p"), eq=rendered)
        output = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    (
                        "from importlib import import_module\n"
                        f"p = import_module({(package.name + '.protocols')!r}).p\n"
                        f"names = {names!r}\n"
                        "owners = tuple(import_module("
                        f"{(package.name + '._protocols.owner_')!r} + str(index))"
                        ".__dict__[name] for index, name in enumerate(names))\n"
                        "assert tuple(base for base in p.Sample.__mro__ "
                        "if base in owners)"
                        " == owners\n"
                        "for index, owner in enumerate(owners):\n"
                        "    name = 'Contract' + str(index)\n"
                        "    assert getattr(p.Sample, name) is getattr(owner, name)\n"
                    ),
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            ),
        )
        tm.that(u.Cli.process_succeeded(output.outcome), eq=True, msg=output.stderr)

    @pytest.mark.parametrize("length_delta", [0, 16])
    @pytest.mark.parametrize("parenthesized", [False, True])
    def test_published_import_width_preserves_mro_and_lazy_exports(
        self,
        tmp_path: Path,
        length_delta: int,
        *,
        parenthesized: bool,
    ) -> None:
        """Preserve MRO and lazy exports around the configured import budget.

        Verify generated exports in the fresh consumer, not the publisher's
        previously imported empty initializer, which file publication cannot reload.
        """
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        self._write(package / c.Infra.INIT_PY, "")
        width = u.Infra.native_tool_setting(
            config.Infra.tooling, "ruff", "line-length", int
        )
        owner = "Owner" + "X" * ((width + length_delta) // 2)
        family = u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY)
        self._write(package / family.directory / c.Infra.INIT_PY, "")
        module = "owner_" + "x" * max(
            0, width - len(f"from {package.name}.{family.directory}.owner_ import (")
        )
        self._write(
            package / family.directory / f"{module}.py",
            f'class {owner}:\n    """Canonical behavior owner."""\n'
            '    marker = "owner"\n'
            "    @classmethod\n    def read(cls) -> str:\n"
            "        return cls.marker\n"
            f'__all__ = ["{owner}"]\n',
        )
        barrel_name = f"{package.name}.{family.directory}"
        owner_module = f"{barrel_name}.{module}"
        facade = package / c.Infra.UTILITIES_PY
        self._write(
            facade,
            '"""Public utility facade.\n\n'
            "Copyright (c) 2026 FLEXT Team. All rights reserved.\n"
            'SPDX-License-Identifier: MIT\n"""\n\n'
            f"from {package.name}.{family.directory}.{module} import "
            f"{f'({owner})' if parenthesized else owner}\n\n\n"
            f'class Utilities({owner}):\n    """Compose the canonical owner."""\n\n\n'
            'u = Utilities\n\n__all__ = ["Utilities", "u"]\n',
        )
        script = (
            "from pathlib import Path\n"
            "from flext_infra import config, u\n"
            "from tests import c, r, tm, u as test_u\n"
            f"root = Path({str(root)!r})\n"
            f"package = Path({str(package)!r})\n"
            f"facade = Path({str(facade)!r})\n"
            "tm.that(u.Infra.native_tool_setting("
            "config.Infra.tooling, 'ruff', 'line-length', int), "
            f"eq={width})\n"
            "from importlib import import_module\n"
            f"before = import_module({(package.name + '.utilities')!r}).u\n"
            "expected = tuple(item.__name__ for item in before.__mro__)\n"
            "class Receiver(before):\n    marker = 'facade'\n"
            "tm.that(before.read(), eq='owner')\n"
            "tm.that(Receiver.read(), eq='facade')\n"
            "rendered = tm.not_none(u.Infra.render_utility_facade(package))\n"
            "tm.ok(u.Cli.atomic_write_text_file(facade, rendered))\n"
            "from runpy import run_path\n"
            "projected = run_path(str(facade))['u']\n"
            "tm.that(projected.read(), eq='owner')\n"
            "class ProjectedReceiver(projected):\n    marker = 'facade'\n"
            "tm.that(ProjectedReceiver.read(), eq='facade')\n"
            "service = test_u.Tests.create_lazy_init_service(root)\n"
            "tm.ok(test_u.Tests.materialize_lazy_init(service))\n"
            "tm.that(u.Infra.render_utility_facade(package), eq=rendered)\n"
            "initializer = package / '__init__.py'\n"
            "published = tm.ok(u.Cli.atomic_read_binary_file_state(\n"
            "    initializer, required=True))\n"
            "tm.ok(test_u.Tests.materialize_lazy_init(service))\n"
            "tm.that(tm.ok(u.Cli.atomic_read_binary_file_state(\n"
            "    initializer, required=True)), eq=published)\n"
            "tm.that(u.Infra.render_utility_facade(package), eq=rendered)\n"
            "with u.Infra.facade_source_project(root) as binding:\n"
            f"    barrel = binding[0].get_module({barrel_name!r})\n"
            f"    leaf = binding[0].get_module({owner_module!r})\n"
            f"    tm.that(barrel.get_attributes()[{owner!r}].get_object() is "
            f"leaf.get_attributes()[{owner!r}].get_object(), eq=True)\n"
            "for path in (initializer, package / "
            f"{family.directory!r} / '__init__.py', facade):\n"
            "    state = tm.ok(u.Cli.atomic_read_binary_file_state(\n"
            "        path, required=True))\n"
            "    tm.that(max(map(len, state.content.decode().splitlines())), "
            f"lte={width})\n"
            "print(repr(expected))\n"
        )
        environment = {
            "PYTHONPATH": str(Path(__file__).resolve().parents[4])
            + ":"
            + str(package.parent),
        }
        result = tm.ok(
            u.Cli.run_raw(
                (sys.executable, "-c", script),
                cwd=root,
                options=m.Cli.ProcessOptions(env=environment),
            )
        )
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True, msg=result.stderr)
        consumer = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    (
                        "from importlib import import_module\n"
                        "from tests import c, r, tm\n"
                        f"from {package.name} import u\n"
                        f"barrel = import_module({barrel_name!r})\n"
                        f"leaf = import_module({owner_module!r})\n"
                        f"tm.that(barrel.{owner} is leaf.{owner}, eq=True)\n"
                        "class Receiver(u):\n    marker = 'facade'\n"
                        "tm.that(u.read(), eq='owner')\n"
                        "tm.that(Receiver.read(), eq='facade')\n"
                        "print(repr(tuple(item.__name__ for item in u.__mro__)))\n"
                    ),
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(env=environment),
            )
        )
        tm.that(
            u.Cli.process_succeeded(consumer.outcome),
            eq=True,
            msg=(
                f"consumer stderr:\n{consumer.stderr}\n"
                f"consumer stdout:\n{consumer.stdout}\n"
                f"publisher stdout:\n{result.stdout}\n"
                "published __init__.py:\n"
                f"{
                    (package / c.Infra.INIT_PY).read_text(encoding=c.DEFAULT_ENCODING)
                }\n"
                "published utilities.py:\n"
                f"{facade.read_text(encoding=c.DEFAULT_ENCODING)}"
            ),
        )
        tm.ok(result.stdout.endswith(consumer.stdout))
        checked = tm.ok(
            u.Cli.run_raw(
                (
                    c.Infra.RUFF,
                    c.Infra.CHECK,
                    "--no-fix",
                    "--config",
                    str(Path(__file__).resolve().parents[4] / c.PYPROJECT_FILENAME),
                    "--line-length",
                    str(width),
                    str(facade),
                    str(package / c.Infra.INIT_PY),
                ),
                cwd=root,
            )
        )
        tm.that(
            u.Cli.process_succeeded(checked.outcome),
            eq=True,
            msg=checked.stdout + checked.stderr,
        )
        consumer_path = package.parent / "consumer.py"
        self._write(
            consumer_path,
            f"from {barrel_name} import (\n    {owner},\n)\n\n"
            f"value: {owner} = {owner}()\n"
            f"owner: type[{owner}] = {owner}\n",
        )
        for checker in ("mypy", "pyright"):
            result = tm.ok(
                u.Cli.run_raw(
                    (
                        sys.executable,
                        "-m",
                        checker,
                        str(consumer_path),
                    ),
                    cwd=root,
                    options=m.Cli.ProcessOptions(env=environment),
                ),
            )
            tm.that(
                u.Cli.process_succeeded(result.outcome),
                eq=True,
                msg=result.stdout + result.stderr,
            )

    @staticmethod
    def _write(path: Path, source: str) -> None:
        """Create one fixture source through the canonical atomic writer."""
        path.parent.mkdir(parents=True, exist_ok=True)
        tm.ok(u.Cli.atomic_write_text_file(path, source))
        root = next(
            (parent for parent in path.parents if (parent / c.GIT_DIR_NAME).exists()),
            None,
        )
        if root is not None:
            u.Tests.git_bootstrap(root, ("add", "--", str(path.relative_to(root))))

    @pytest.mark.parametrize("family", ["u", "m"])
    @pytest.mark.parametrize("departure", ["absent", "moved", "unpublished"])
    def test_departed_generated_owner_ignores_barrel_export_freshness(
        self,
        tmp_path: Path,
        departure: str,
        family: Literal["u", "m"],
        native_consumer: p.Tests.NativeConsumer,
    ) -> None:
        """Current leaf owners determine the first plan without publishing inputs."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        declaration = u.Infra.facade_families()[family]
        owners = package / declaration.directory
        barrel = owners / c.Infra.INIT_PY
        facade = package / f"{declaration.module}.py"
        marker = c.Infra.AUTOGEN_HEADER + "\n"
        original = (
            marker + f"from {package.name}.{declaration.directory} import "
            "ClientOwner, DepartedOwner\n"
            "class Utilities:\n"
            "    class Domain(ClientOwner, DepartedOwner):\n        pass\n"
            f"{family} = Utilities\n__all__ = ['Utilities', {family!r}]\n"
        )
        stale = marker + "__all__ = ['ClientOwner', 'DepartedOwner']\n"
        refreshed = (
            marker + "from .client import ClientOwner\n__all__ = ['ClientOwner']\n"
        )
        if departure == "unpublished":
            stale = (
                marker + "from .client import ClientOwner\n"
                "from .departed import DepartedOwner\n"
                "__all__ = ['ClientOwner', 'DepartedOwner']\n"
            )
        sources = {
            package / c.Infra.INIT_PY: "",
            owners / "client.py": (
                "class ClientOwner:\n    marker = 'current'\n"
                "__all__ = ['ClientOwner']\n"
            ),
            barrel: stale,
            facade: original,
        }
        if departure == "moved":
            sources[package / "services" / "runtime.py"] = (
                "class DepartedOwner:\n    marker = 'moved'\n"
                "__all__ = ['DepartedOwner']\n"
            )
        elif departure == "unpublished":
            sources[owners / "departed.py"] = (
                "class DepartedOwner:\n    departed = 'retained-implementation'\n"
                "__all__ = []\n"
            )
        for path, source in sources.items():
            self._write(path, source)
        originals = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            for path in sources
        )
        projections: list[str] = []
        for candidate in (stale, refreshed):
            with u.Infra.facade_source_project(
                root,
                source_options=m.Infra.StageSourceOptions(inputs=originals),
                planned_sources={barrel: candidate},
            ) as (project, _, contents):
                rendered = tm.not_none(
                    u.Infra.render_utility_facade(
                        package, family=family, project=project, sources=contents
                    )
                )
                projections.append(rendered)
            tm.ok(u.Cli.atomic_verify_binary_file_states(originals))
            with u.Infra.facade_source_project(
                root,
                source_options=m.Infra.StageSourceOptions(inputs=originals),
                planned_sources={barrel: candidate, facade: rendered},
            ) as (project, _, contents):
                tm.that(
                    u.Infra.render_utility_facade(
                        package, family=family, project=project, sources=contents
                    ),
                    eq=rendered,
                )
            tm.ok(u.Cli.atomic_verify_binary_file_states(originals))
        tm.that(projections[0], eq=projections[1])
        tm.fail("DepartedOwner" in projections[0])
        candidate = tmp_path / "candidate" / "src" / package.name
        for path, source in sources.items():
            self._write(candidate / path.relative_to(package), source)
        self._write(candidate / facade.name, projections[0])
        self._write(candidate / declaration.directory / c.Infra.INIT_PY, refreshed)
        native_consumer(
            "from flext_tests import tm\n"
            f"sys.path.insert(0, {str(candidate.parent)!r})\n"
            f"from {package.name}.{declaration.module} import {family}\n"
            f"tm.that({family}.Domain.marker, eq='current')\n"
            f"tm.fail(hasattr({family}.Domain, 'departed'))\n",
            cwd=root,
        )
        tm.ok(u.Cli.atomic_verify_binary_file_states(originals))

    @pytest.mark.parametrize(
        "ownership",
        [
            "authored-facade",
            "authored-barrel",
            "unrelated-module",
            "declared-alias",
            "unresolved-external",
        ],
    )
    def test_unresolved_base_requires_generated_family_provenance(
        self,
        tmp_path: Path,
        ownership: str,
        native_consumer: p.Tests.NativeConsumer,
    ) -> None:
        """Missing owners are rejected while declared aliases retain native identity."""
        _, package = u.Tests.create_lazy_init_workspace(tmp_path)
        family = u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY)
        owners = package / family.directory
        marker = c.Infra.AUTOGEN_HEADER + "\n"
        provider = (
            f"{package.name}.unrelated"
            if ownership == "unrelated-module"
            else f"{package.name}.{family.directory}"
        )
        if ownership == "unresolved-external":
            provider = f"{package.name}_absent"
        imported = (
            "ClientOwner as MissingOwner"
            if ownership == "declared-alias"
            else "MissingOwner"
        )
        sources = {
            package / c.Infra.INIT_PY: "",
            owners / c.Infra.INIT_PY: (
                ("" if ownership == "authored-barrel" else marker) + "__all__ = []\n"
            ),
            owners / "client.py": (
                "class ClientOwner:\n    pass\n__all__ = ['ClientOwner']\n"
            ),
            package / "unrelated.py": "__all__ = []\n",
            package / c.Infra.UTILITIES_PY: (
                ("" if ownership == "authored-facade" else marker)
                + f"from {provider} import {imported}\n"
                "class Utilities:\n    class Domain(MissingOwner):\n        pass\n"
                "u = Utilities\n__all__ = ['Utilities', 'u']\n"
            ),
        }
        for path, source in sources.items():
            self._write(path, source)
        originals = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            for path in sources
        )
        cause = (
            "unresolved imported module:"
            if ownership == "unresolved-external"
            else "Facade base has no source owner:.*MissingOwner"
        )
        if ownership == "declared-alias":
            rendered = tm.not_none(u.Infra.render_utility_facade(package))
            tm.ok(u.Cli.atomic_verify_binary_file_states(originals))
            candidate = tmp_path / "candidate" / package.name
            for path, source in sources.items():
                self._write(candidate / path.relative_to(package), source)
            self._write(candidate / c.Infra.UTILITIES_PY, rendered)
            native_consumer(
                "from flext_tests import tm\n"
                f"sys.path.insert(0, {str(candidate.parent)!r})\n"
                f"from {package.name}.utilities import u\n"
                f"from {package.name}.{family.directory}.client import ClientOwner\n"
                "tm.that(u.Domain.__bases__[0] is ClientOwner, truth=True)\n",
                cwd=candidate.parent,
            )
        else:
            with pytest.raises(ValueError, match=cause):
                u.Infra.render_utility_facade(package)
        tm.ok(u.Cli.atomic_verify_binary_file_states(originals))

    def test_owner_inheriting_a_sourceless_stdlib_module_orders_natively(
        self,
        tmp_path: Path,
    ) -> None:
        """An owner based on a frozen stdlib alias keeps its native C3 order.

        ``collections.abc`` has no source file on the supported interpreter;
        the planning project must resolve it like the live project does.
        """
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        directory = u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY).directory
        facade = package / c.Infra.UTILITIES_PY
        sources = {
            package / "__init__.py": (
                f"from {package.name}.utilities import Utilities, u\n"
                "__all__ = ['Utilities', 'u']\n"
            ),
            package / directory / "__init__.py": (
                f"from {package.name}.{directory}.registry import RegistryOwner\n"
                "__all__ = ['RegistryOwner']\n"
            ),
            package / directory / "registry.py": (
                "from collections.abc import Iterator, Mapping\n"
                "class RegistryOwner(Mapping):\n"
                "    def __getitem__(self, key: str) -> str:\n"
                "        return key\n"
                "    def __iter__(self) -> Iterator[str]:\n"
                "        return iter(('registry-value',))\n"
                "    def __len__(self) -> int:\n"
                "        return 1\n"
                "__all__ = ['RegistryOwner']\n"
            ),
            facade: (
                f"from {package.name}.{directory} import RegistryOwner\n"
                "class Utilities(RegistryOwner):\n"
                "    pass\n"
                "u = Utilities\n__all__ = ['Utilities', 'u']\n"
            ),
        }
        for path, source in sources.items():
            self._write(path, source)
        rendered = tm.not_none(u.Infra.render_utility_facade(package))
        self._write(facade, rendered)
        tm.ok(u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)))
        tm.that(u.Infra.render_utility_facade(package), eq=rendered)
        result = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    (
                        "from collections.abc import Mapping; "
                        f"from {package.name} import u; "
                        "assert issubclass(u, Mapping); "
                        "print(list(u()))"
                    ),
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            ),
        )
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True, msg=result.stderr)
        tm.that(result.stdout.strip(), eq="['registry-value']")

    @pytest.mark.parametrize("multiline", [False, True])
    def test_protocol_annotation_projects_owner_and_converges(
        self,
        tmp_path: Path,
        *,
        multiline: bool,
    ) -> None:
        """An owned annotation supplies its protocol without changing other code."""
        root, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-sample",
            package_name="flext_sample",
        )
        self._write(package / "__init__.py", "")
        self._write(
            package / "services" / "payload.py",
            "from flext_sample import p\n"
            "def consume(value: p.Sample.Payload) -> None:\n    pass\n"
            "def foreign(value: p.Other.Unused) -> None:\n    pass\n",
        )
        self._write(
            package / "_protocols" / "payload.py",
            "from typing import Protocol, runtime_checkable\n"
            "class PayloadOwner:\n"
            "    preserved = 'unchanged'\n"
            "    @runtime_checkable\n"
            "    class Payload(Protocol):\n"
            "        value: str\n"
            "__all__ = ['PayloadOwner']\n",
        )
        self._write(
            package / "_protocols" / "unused.py",
            "class UnusedOwner:\n    class Unused:\n        pass\n",
        )
        self._write(
            package.parent / "foreign_package" / "__init__.py",
            "from flext_core import p\n__all__ = ['p']\n",
        )
        self._write(
            package / "foreign_consumer.py",
            "from foreign_package import p\n"
            "def foreign(value: p.Sample.Unused) -> None:\n    pass\n",
        )
        self._write(
            package / "shadowed_consumer.py",
            "from flext_sample import p\n"
            "def parameter(p):\n    return p.Sample.Unused\n"
            "def assigned():\n    p = 0\n    return p.Sample.Unused\n",
        )
        facade = package / "protocols.py"
        header = (
            "    class Sample(\n        FlextProtocols,\n    ):\n"
            if multiline
            else ("    class Sample(FlextProtocols):\n")
        )
        original = (
            "from flext_core import FlextProtocols\n\n"
            "class FlextSampleProtocols(FlextProtocols):\n"
            + header
            + "        pass\n\np = FlextSampleProtocols\n\n"
            + '__all__ = ["FlextSampleProtocols", "p"]\n'
        )
        self._write(facade, original)

        service = u.Tests.create_lazy_init_service(root)
        family = u.Infra.facade_family_declared_by(facade.name)
        service.target_module = f"{package.name}.{family.directory}"
        tm.ok(u.Tests.materialize_lazy_init(service))
        before = tm.ok(u.Cli.atomic_read_binary_file_state(facade, required=True))
        updated = tm.not_none(u.Infra.render_utility_facade(package, family="p"))

        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(facade, required=True)),
            eq=before,
        )
        self._write(facade, updated)
        tm.that(u.Infra.render_utility_facade(package, family="p"), eq=updated)
        tm.ok(u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)))
        result = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    (
                        "from flext_sample import p\n"
                        "class Value:\n    value = 'payload'\n"
                        "assert isinstance(Value(), p.Sample.Payload)\n"
                        "assert p.Sample.preserved == 'unchanged'\n"
                        "assert not hasattr(p.Sample, 'Unused')\n"
                    ),
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            ),
        )
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True, msg=result.stderr)

    @pytest.mark.parametrize("multiline", [False, True])
    @pytest.mark.parametrize("organizer_protocol", [False, True])
    @pytest.mark.parametrize("import_alias", [False, True])
    @pytest.mark.parametrize(
        "owner_state", [(False, False), (False, True), (True, False), (True, True)]
    )
    def test_protocol_owner_precedes_terminal_protocol_base(
        self,
        tmp_path: Path,
        *,
        multiline: bool,
        organizer_protocol: bool,
        import_alias: bool,
        owner_state: tuple[bool, bool],
    ) -> None:
        """Both source forms import and expose the real structural protocol."""
        shadow, inherited_owner = owner_state
        root, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-sample",
            package_name="flext_sample",
        )
        self._write(package / "__init__.py", "")
        self._write(
            package.parent / "upstream.py",
            "from typing import Protocol\n"
            "class ParentProtocols(Protocol):\n    pass\n"
            "p = ParentProtocols\n__all__ = ['ParentProtocols', 'p']\n",
        )
        self._write(
            package / "services" / "payload.py",
            "from flext_sample import p\n"
            "def consume(value: p.Sample.Payload) -> None:\n    pass\n",
        )
        self._write(
            package / "_protocols" / "payload.py",
            "from typing import Protocol, runtime_checkable\n\n"
            f"class PayloadOwner{'(Protocol)' if organizer_protocol else ''}:\n"
            "    @runtime_checkable\n"
            "    class Payload(Protocol):\n        value: str\n"
            "__all__ = ['PayloadOwner']\n",
        )
        self._write(
            package / "other.py",
            "from typing import Protocol\n"
            "class PayloadOwner:\n"
            "    class Payload(Protocol):\n        other: int\n",
        )
        facade = package / "protocols.py"
        owner_name = "ImportedOwner" if import_alias else "PayloadOwner"
        bases = f"{owner_name}, p" if shadow and inherited_owner else "p"
        header = (
            f"    class Sample(\n        {bases},\n        Protocol,\n    ):\n"
            if multiline
            else f"    class Sample({bases}, Protocol):\n"
        )
        owner_import = (
            f"from flext_sample._protocols import PayloadOwner as {owner_name}\n"
            if shadow
            else ""
        )
        body = (
            (
                f"        Payload: type[{owner_name}.Payload] = (\n"
                f"            {owner_name}.Payload\n"
                "        )\n"
                if multiline
                else (
                    f"        Payload: type[{owner_name}.Payload] = "
                    f"{owner_name}.Payload\n"
                )
            )
            if shadow
            else "        pass\n"
        )
        self._write(
            facade,
            "from typing import Protocol\n\nfrom upstream import p\n\n"
            "from flext_sample.other import PayloadOwner as OtherOwner\n"
            + owner_import
            + "\n"
            + "class FlextSampleProtocols(p):\n"
            + header
            + body
            + "        Unrelated: type[OtherOwner.Payload] = OtherOwner.Payload\n"
            + "\np = FlextSampleProtocols\n\n"
            + '__all__ = ["FlextSampleProtocols", "p"]\n',
        )

        service = u.Tests.create_lazy_init_service(root)
        family = u.Infra.facade_family_declared_by(facade.name)
        service.target_module = f"{package.name}.{family.directory}"
        tm.ok(u.Tests.materialize_lazy_init(service))
        updated = tm.not_none(u.Infra.render_utility_facade(package, family="p"))
        self._write(facade, updated)
        tm.that(u.Infra.render_utility_facade(package, family="p"), eq=updated)
        tm.ok(u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)))
        output = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    (
                        "from flext_sample import p\n"
                        "from typing import get_type_hints\n"
                        "from flext_sample._protocols import PayloadOwner\n"
                        "from flext_sample.other import PayloadOwner as OtherOwner\n"
                        "class Value:\n    value = 'payload'\n"
                        "class Missing:\n    pass\n"
                        "assert p.Sample.Payload is PayloadOwner.Payload\n"
                        "assert p.Sample.Unrelated is OtherOwner.Payload\n"
                        "assert get_type_hints(p.Sample)['Unrelated'] == "
                        "type[OtherOwner.Payload]\n"
                        "assert PayloadOwner in p.Sample.__mro__\n"
                        "assert 'Payload' not in get_type_hints(p.Sample)\n"
                        "assert isinstance(Value(), p.Sample.Payload)\n"
                        "assert not isinstance(Missing(), p.Sample.Payload)\n"
                        "print('protocol-proven')\n"
                    ),
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            ),
        )
        tm.that(u.Cli.process_succeeded(output.outcome), eq=True, msg=output.stderr)
        tm.that(output.stdout.strip(), eq="protocol-proven")

    @pytest.mark.parametrize(
        ("published", "actual"),
        [("AclAllow", "AclTarget"), ("RegistryBound", "ServerReference")],
    )
    @pytest.mark.parametrize("managed", [False, True])
    @pytest.mark.parametrize("collision", [False, True])
    def test_protocol_projection_rejects_unproven_renamed_contract(
        self,
        tmp_path: Path,
        published: str,
        actual: str,
        *,
        managed: bool,
        collision: bool,
    ) -> None:
        """Managed projections consume source contracts, never obsolete aliases."""
        root, package = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="flext-sample", package_name="flext_sample"
        )
        self._write(package / "__init__.py", "")
        self._write(
            package / "_protocols" / "payload.py",
            "from typing import Protocol\n"
            "class PayloadOwner:\n"
            f"    class {actual}(Protocol):\n        value: str\n"
            + (
                f"    class {published}(Protocol):\n        registry: str\n"
                if collision
                else ""
            )
            + "__all__ = ['PayloadOwner']\n",
        )
        facade = package / "protocols.py"
        self._write(
            facade,
            (f"{c.Infra.AUTOGEN_HEADER}\n" if managed else "")
            + "from flext_sample._protocols import PayloadOwner\n"
            "class FlextSampleProtocols:\n"
            "    class Sample(PayloadOwner):\n"
            f"        {published}: type[PayloadOwner.{actual}] = "
            f"PayloadOwner.{actual}\n"
            "p = FlextSampleProtocols\n"
            "__all__ = ['FlextSampleProtocols', 'p']\n",
        )
        service = u.Tests.create_lazy_init_service(root)
        service.target_module = f"{package.name}._protocols"
        tm.ok(u.Tests.materialize_lazy_init(service))
        if managed:
            rendered = tm.not_none(u.Infra.render_utility_facade(package, family="p"))
            self._write(facade, rendered)
            tm.that(u.Infra.render_utility_facade(package, family="p"), eq=rendered)
            tree = ast.parse(rendered)
            tm.that(
                any(
                    isinstance(node, ast.AnnAssign)
                    and isinstance(node.target, ast.Name)
                    and node.target.id == published
                    for node in ast.walk(tree)
                ),
                eq=False,
            )
            return
        with pytest.raises(ValueError, match="ambiguous protocol class attribute"):
            u.Infra.render_utility_facade(package, family="p")

    @pytest.mark.parametrize("family", ["p", "m"])
    @pytest.mark.parametrize("annotation", ["none", "matching", "unresolved"])
    def test_generated_contract_aliases_use_canonical_inherited_declarations(
        self,
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
        family: Literal["p", "m"],
        *,
        annotation: Literal["none", "matching", "unresolved"],
    ) -> None:
        """Derived aliases cannot replace real contracts or create legacy names."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        declaration = u.Infra.facade_families()[family]
        directory = declaration.directory
        module = f"{declaration.module}{c.Infra.EXT_PYTHON}"
        self._write(package / c.Infra.INIT_PY, "")
        protocol = family == "p"
        base = "Protocol" if protocol else "BaseModel"
        decorator = "    @runtime_checkable\n" if protocol else ""
        self._write(
            package / directory / "payload.py",
            (
                "from typing import Protocol, runtime_checkable\n"
                if protocol
                else "from pydantic import BaseModel\n"
            )
            + "class PayloadOwner:\n"
            + decorator
            + f"    class RegistryBound({base}):\n        registry: str\n"
            + decorator
            + f"    class ServerReference({base}):\n        server_type: str\n"
            + decorator
            + f"    class AclTarget({base}):\n        target_dn: str\n"
            + "__all__ = ['PayloadOwner']\n",
        )
        self._write(
            package / "foreign.py",
            "class ForeignOwner:\n    class Extra:\n        pass\n",
        )
        facade = package / module
        self._write(
            facade,
            c.Infra.AUTOGEN_HEADERS[0]
            + "\n"
            + ("from typing import Protocol, runtime_checkable\n" if protocol else "")
            + f"from {package.name}.{directory} import PayloadOwner\n"
            + f"from {package.name}.foreign import ForeignOwner\n"
            + "class Facade:\n"
            + ("    @runtime_checkable\n" if protocol else "")
            + "    class Sample(PayloadOwner"
            + (", Protocol" if protocol else "")
            + "):\n"
            + "".join(
                f"        {published}"
                + (
                    f": type[PayloadOwner.{actual}]"
                    if annotation == "matching"
                    else ": type[MissingContract]"
                    if annotation == "unresolved"
                    else ""
                )
                + f" = PayloadOwner.{actual}\n"
                for published, actual in (
                    ("AclAllow", "AclTarget"),
                    ("RegistryBound", "ServerReference"),
                )
            )
            + "        Extra = ForeignOwner.Extra\n"
            + "        marker = 'retained'\n"
            + f"{family} = Facade\n__all__ = ['Facade', '{family}']\n",
        )
        service = u.Tests.create_lazy_init_service(root)
        service.target_module = f"{package.name}.{directory}"
        tm.ok(u.Tests.materialize_lazy_init(service))
        rendered = tm.not_none(u.Infra.render_utility_facade(package, family=family))
        self._write(facade, rendered)
        tm.that(u.Infra.render_utility_facade(package, family=family), eq=rendered)
        tm.ok(u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)))
        native_consumer(
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            f"from {package.name} import {family} as public\n"
            f"from {package.name}.{directory} import PayloadOwner\n"
            f"from {package.name}.foreign import ForeignOwner\n"
            "assert public.Sample.RegistryBound is PayloadOwner.RegistryBound\n"
            "assert public.Sample.ServerReference is PayloadOwner.ServerReference\n"
            "assert public.Sample.AclTarget is PayloadOwner.AclTarget\n"
            "assert public.Sample.Extra is ForeignOwner.Extra\n"
            "assert public.Sample.marker == 'retained'\n"
            "assert not hasattr(public.Sample, 'AclAllow')\n"
            + (
                "class Bound:\n    registry = 'bound'\n"
                "class Reference:\n    server_type = 'reference'\n"
                "bound = Bound()\nreference = Reference()\n"
                "assert isinstance(bound, public.Sample.RegistryBound)\n"
                "assert not isinstance(reference, public.Sample.RegistryBound)\n"
                if protocol
                else "bound = public.Sample.RegistryBound(registry='bound')\n"
            )
            + "assert bound.registry == 'bound'\n",
            cwd=root,
        )

    @staticmethod
    def test_codegen_models_are_usable_through_the_composed_facade() -> None:
        """Consume both codegen families through the actual generated namespace."""
        context = m.Infra.ModuleSkeletonRenderContext(
            class_name="GeneratedPayload",
            base_class="PayloadBase",
            base_module="fixture_base",
            docstring="Generated payload fixture.",
        )
        tm.that(
            m.Infra.ModuleSkeletonRenderContext.model_validate(context.model_dump()),
            eq=context,
        )

    @staticmethod
    def test_process_options_is_usable_through_the_inherited_public_model() -> None:
        """The real process producer exposes its payload through the model MRO."""
        payload = b"  process input\n"
        environment = {"FLEXT_PROCESS_FIXTURE": "child value"}
        options = m.Cli.ProcessOptions(env=environment, input_data=payload)

        tm.that(options.input_data, eq=payload)
        tm.that(options.env, eq=environment)
        tm.that(
            m.Cli.ProcessOptions.model_validate(options.model_dump()),
            eq=options,
        )

    def test_model_projection_preserves_inherited_family_order_at_runtime(
        self,
        tmp_path: Path,
    ) -> None:
        """Declared model owners compose before any consumer requests their payload."""
        root, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-sample",
            package_name="flext_sample",
        )
        self._write(package / "__init__.py", "from .models import m\n")
        for module, owner, payload in (
            ("render", "RenderOwner", "RenderPayload"),
            ("toolchain", "ToolchainOwner", "ToolchainPayload"),
            ("extra", "ExtraOwner", "ExtraPayload"),
        ):
            self._write(
                package / "_models" / f"{module}.py",
                f"class {owner}:\n    class {payload}:\n        pass\n"
                f"__all__ = ['{owner}']\n",
            )
        self._write(
            package / "_models" / "_codegen" / "base.py",
            "from ..render import RenderOwner\n"
            "from ..toolchain import ToolchainOwner\n"
            "class CodegenOwner(ToolchainOwner, RenderOwner):\n    pass\n"
            "__all__ = ['CodegenOwner']\n",
        )
        facade = package / "models.py"
        self._write(
            facade,
            "from ._models._codegen.base import CodegenOwner\n"
            "class Facade:\n    class Sample(CodegenOwner):\n        pass\n"
            "m = Facade\n__all__ = ['Facade', 'm']\n",
        )
        consumer = package / "consumer.py"
        self._write(
            consumer,
            "from flext_sample import m\n"
            "m.Sample.RenderPayload()\n"
            "m.Sample.ToolchainPayload()\n"
            "completed = True\n",
        )
        rendered = tm.not_none(u.Infra.render_utility_facade(package, family="m"))
        self._write(facade, rendered)
        tm.ok(u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)))
        entrypoint = root / "consume.py"
        self._write(
            entrypoint,
            "from flext_sample.consumer import completed\n"
            "from flext_sample import m\nm.Sample.ExtraPayload()\nassert completed\n",
        )
        result = tm.ok(
            u.Cli.run_raw(
                [sys.executable, str(entrypoint)],
                cwd=root,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            ),
        )
        tm.that(
            u.Cli.process_succeeded(result.outcome),
            eq=True,
            msg=result.stderr or result.stdout,
        )
        tm.that(u.Infra.render_utility_facade(package, family="m"), eq=rendered)

    @pytest.mark.parametrize("family", ["p", "m"])
    @pytest.mark.parametrize("compact", [False, True])
    @pytest.mark.parametrize("generated", [False, True])
    def test_class_alias_removal_obeys_effective_diamond_owner(
        self,
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
        family: Literal["p", "m"],
        *,
        compact: bool,
        generated: bool,
    ) -> None:
        """C3 beats the left base's inherited alias and keeps adjacent statements."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        module = c.Infra.PROTOCOLS_PY if family == "p" else c.Infra.MODELS_PY
        directory = u.Infra.facade_family_declared_by(module).directory
        facade = package / module
        self._write(package / c.Infra.INIT_PY, "")
        self._write(
            package / directory / "owners.py",
            "class RootPart:\n    class Payload:\n        pass\n"
            "class LeftPart(RootPart):\n    pass\n"
            "class RightPart(RootPart):\n    class Payload:\n        pass\n"
            "__all__ = ['RootPart', 'LeftPart', 'RightPart']\n",
        )
        self._write(
            facade,
            (c.Infra.AUTOGEN_HEADERS[0] + "\n" if generated else "")
            + f"from {package.name}.{directory}.owners import LeftPart, RightPart\n"
            "class Facade(LeftPart, RightPart):"
            + (
                " Payload = RightPart.Payload; marker = 'retained'\n"
                if compact
                else "\n    Payload = RightPart.Payload\n"
            )
            + f"{family} = Facade\n__all__ = ['Facade', '{family}']\n",
        )
        service = u.Tests.create_lazy_init_service(root)
        service.target_module = f"{package.name}.{directory}"
        tm.ok(u.Tests.materialize_lazy_init(service))
        rendered = tm.not_none(u.Infra.render_utility_facade(package, family=family))
        self._write(facade, rendered)
        tm.that(u.Infra.render_utility_facade(package, family=family), eq=rendered)
        tm.ok(u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)))
        native_consumer(
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            f"from {package.name} import {family} as public\n"
            f"from {package.name}.{directory} import RootPart, LeftPart, RightPart\n"
            "assert LeftPart.Payload is RootPart.Payload\n"
            "assert public.Payload is RightPart.Payload\n"
            "assert public.Payload is not RootPart.Payload\n"
            "assert 'Payload' not in vars(public)\n"
            + ("assert public.marker == 'retained'\n" if compact else ""),
            cwd=root,
        )
