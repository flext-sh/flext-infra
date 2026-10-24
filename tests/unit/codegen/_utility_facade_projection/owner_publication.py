"""Public evidence for declared utility-facade owner publication.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Literal

import pytest

from flext_infra import config
from flext_infra.codegen import FlextInfraCodegenConformExecute
from tests import c, m, p, t, tm, u


class UtilityFacadeOwnerPublication:
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
        with u.Infra.facade_source_project(root) as (project, sources):
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
            FlextInfraCodegenConformExecute(
                state=m.Infra.CodegenConformState(repository_root=root),
            ).plan(
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
        with u.Infra.facade_source_project(root) as (project, sources):
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
        with u.Infra.facade_source_project(root) as (project, sources):
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
        with u.Infra.facade_source_project(root) as (project, sources):
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
        with u.Infra.facade_source_project(root) as (project, sources):
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
            "service = u.Tests.create_lazy_init_service(root)\n"
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
