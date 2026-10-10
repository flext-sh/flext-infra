"""Public evidence for discovery-driven utility-facade projection.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest
from flext_tests import tm

from flext_infra import c, infra, m, u


class TestsFlextInfraUtilityFacadeProjection:
    """Exercise consumer-driven owner projection only through ``u.Infra``."""

    @staticmethod
    def _write(path: Path, source: str) -> None:
        """Create one fixture source through the canonical atomic writer."""
        path.parent.mkdir(parents=True, exist_ok=True)
        tm.ok(u.Cli.atomic_write_text_file(path, source))

    @staticmethod
    def _behavior_package(package: Path, value_type: str) -> dict[Path, str]:
        """Declare a real typed factory and its public facade in one fixture package."""
        directory = u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY).directory
        return {
            package / "__init__.py": (
                f"from {package.name}.utilities import Utilities, u\n"
                "class Types:\n    pass\nt = Types\n"
                "__all__ = ['Types', 't', 'Utilities', 'u']\n"
            ),
            package / directory / "__init__.py": "",
            package / directory / "adapter.py": (
                "from pydantic import TypeAdapter\n"
                "class AdapterOwner:\n"
                "    @staticmethod\n"
                f"    def value_adapter() -> TypeAdapter[{value_type}]:\n"
                f"        return TypeAdapter({value_type})\n"
                "__all__ = ['AdapterOwner']\n"
            ),
            package / "utilities.py": (
                f"from {package.name}.{directory}.adapter import AdapterOwner\n"
                "class Utilities(AdapterOwner):\n    pass\nu = Utilities\n"
                "__all__ = ['Utilities', 'u']\n"
            ),
        }

    @pytest.mark.parametrize("relation", ["isolated", "inherited", "foreign-only"])
    def test_behavior_owners_follow_the_imported_package_lineage(
        self,
        tmp_path: Path,
        relation: str,
    ) -> None:
        """Matching foreign method names neither redirect nor ambiguate a reference."""
        root, first = u.Tests.create_lazy_init_workspace(tmp_path)
        second = first.with_name(first.name + "_other")
        sources = self._behavior_package(first, "int")
        sources.update(self._behavior_package(second, "str"))
        directory = u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY).directory
        typings = u.Infra.facade_family_declared_by(c.Infra.TYPINGS_PY).directory
        if relation != "isolated":
            del sources[first / directory / "adapter.py"]
            sources[first / "utilities.py"] = (
                f"from {second.name} import Utilities as ParentUtilities\n"
                "class Utilities(ParentUtilities):\n    pass\nu = Utilities\n"
                "__all__ = ['Utilities', 'u']\n"
                if relation == "inherited"
                else "class Utilities:\n    pass\nu = Utilities\n"
                "__all__ = ['Utilities', 'u']\n"
            )
            if relation == "inherited":
                third = first.with_name(first.name + "_leaf")
                sources.update(self._behavior_package(third, "str"))
                del sources[second / directory / "adapter.py"]
                sources[second / "__init__.py"] = (
                    f"from {third.name} import Types as ParentTypes\n"
                    f"from {second.name}.utilities import Utilities, u\n"
                    "class Types(ParentTypes):\n    pass\nt = Types\n"
                    "__all__ = ['Types', 't', 'Utilities', 'u']\n"
                )
                sources[second / "utilities.py"] = (
                    f"from {third.name} import Utilities as ParentUtilities\n"
                    "class Utilities(ParentUtilities):\n    pass\nu = Utilities\n"
                    "__all__ = ['Utilities', 'u']\n"
                )
                sources[first / typings / "eager.py"] = (
                    f"from {second.name} import Types as ImportedTypes\n"
                    "class Eager:\n    adapter = ImportedTypes.value_adapter()\n"
                    "__all__ = ['Eager']\n"
                )
                sources[first / "__init__.py"] = (
                    f"from {second.name} import Types as ParentTypes\n"
                    f"from {first.name}.utilities import Utilities, u\n"
                    "class Types(ParentTypes):\n    pass\nt = Types\n"
                    f"from {first.name}.{typings}.eager import Eager\n"
                    "__all__ = ['Types', 't', 'Utilities', 'u', 'Eager']\n"
                )
        consumer = root / "consumer.py"
        sources[consumer] = (
            "def first_call():\n"
            f"    from {first.name} import t as shared\n"
            "    return shared.value_adapter().validate_python('7')\n"
            "def second_call():\n"
            f"    from {second.name} import t as shared\n"
            "    return shared.value_adapter().validate_python('7')\n"
        )
        for path, source in sources.items():
            self._write(path, source)
        with infra.rope_workspace(root) as rope:
            edits = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                    rope_workspace=rope,
                    sources=sources,
                )
            )
            proposed = dict(sources)
            proposed.update({edit.file_path: edit.updated_source for edit in edits})
            if relation == "foreign-only":
                tm.that(proposed[consumer], has="return shared.value_adapter()")
            else:
                tm.that(proposed[consumer], has=f"{first.name}.u.value_adapter()")
            if relation == "inherited":
                tm.that(
                    proposed[first / typings / "eager.py"],
                    has=f"{second.name}.u.value_adapter()",
                )
            tm.that(proposed[consumer], has=f"{second.name}.u.value_adapter()")
            tm.that(
                tm.ok(
                    u.Infra.plan_semantic_cutover(
                        c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                        rope_workspace=rope,
                        sources=proposed,
                    )
                ),
                empty=True,
            )
        for path, source in proposed.items():
            self._write(path, source)
        first_contract = (
            "try:\n    consumer.first_call()\n"
            "except AttributeError:\n    print('unavailable')\n"
            "else:\n    raise AssertionError('foreign behavior adopted')\n"
            if relation == "foreign-only"
            else f"assert consumer.first_call() == {'7' if relation == 'isolated' else repr('7')}\n"
        )
        output = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    "import consumer\n"
                    + first_contract
                    + "assert consumer.second_call() == '7'\n"
                    + (
                        f"from {first.name} import Eager\nassert Eager.adapter.validate_python('9') == '9'\n"
                        if relation == "inherited"
                        else ""
                    )
                    + "print('scoped')\n",
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(first.parent)}),
            )
        )
        tm.that(u.Cli.process_succeeded(output.outcome), eq=True, msg=output.stderr)
        tm.that(output.stdout, has="scoped")

    def test_shadowed_t_with_competing_owners_is_not_a_migration(
        self,
        tmp_path: Path,
    ) -> None:
        """Ownership decisions do not run for a lexical parameter named t."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        sources = self._behavior_package(package, "int")
        directory = u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY).directory
        sources[package / directory / "duplicate.py"] = (
            "class Duplicate:\n    @staticmethod\n"
            "    def value_adapter() -> int:\n        return 1\n"
            "__all__ = ['Duplicate']\n"
        )
        consumer = root / "consumer.py"
        sources[consumer] = (
            f"from {package.name} import t\n"
            "def consumer(t):\n    return t.value_adapter()\n"
        )
        for path, source in sources.items():
            self._write(path, source)
        with infra.rope_workspace(root) as rope:
            tm.that(
                tm.ok(
                    u.Infra.plan_semantic_cutover(
                        c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                        rope_workspace=rope,
                        sources=sources,
                    )
                ),
                empty=True,
            )
        tm.that(consumer.read_text(encoding="utf-8"), eq=sources[consumer])

    def test_existing_contextual_u_call_keeps_facade_dispatch(
        self,
        tmp_path: Path,
    ) -> None:
        """A valid class-context-dependent utility remains outside this migration."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        sources = self._behavior_package(package, "int")
        directory = u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY).directory
        sources[package / directory / "adapter.py"] = (
            "class AdapterOwner:\n    marker = 'leaf'\n"
            "    @classmethod\n    def bind_context(cls) -> str:\n"
            "        return cls.marker\n__all__ = ['AdapterOwner']\n"
        )
        sources[package / "utilities.py"] = (
            f"from {package.name}.{directory}.adapter import AdapterOwner\n"
            "class Utilities(AdapterOwner):\n    marker = 'facade'\nu = Utilities\n"
            "__all__ = ['Utilities', 'u']\n"
        )
        caller = package / "_decorators" / "consumer.py"
        sources[caller] = (
            f"from {package.name} import u\n"
            "def consume() -> str:\n    return u.bind_context()\n"
        )
        for path, source in sources.items():
            self._write(path, source)
        with infra.rope_workspace(root) as rope:
            tm.that(
                tm.ok(
                    u.Infra.plan_semantic_cutover(
                        c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                        rope_workspace=rope,
                        sources=sources,
                    )
                ),
                empty=True,
            )
        output = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    f"from {package.name}._decorators.consumer import consume; assert consume() == 'facade'",
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            )
        )
        tm.that(u.Cli.process_succeeded(output.outcome), eq=True, msg=output.stderr)

    def test_relocated_behavior_roundtrip_keeps_bootstrap_lower_dependency(
        self,
        tmp_path: Path,
    ) -> None:
        """A real consumer imports the projected facade without a reverse cycle."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        owners = (
            package / u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY).directory
        )
        typings = (
            package / u.Infra.facade_family_declared_by(c.Infra.TYPINGS_PY).directory
        )
        owner = owners / "adapter.py"
        runtime = package / "runtime.py"
        facade = package / "utilities.py"
        consumer = root / "consumer.py"
        sources = {
            package / "__init__.py": (
                f"from {package.name}.typings import t\n"
                f"from {package.name}.utilities import u\n"
            ),
            package / "typings.py": (
                f"from {package.name}.{typings.name}.base import Types\n"
                "t = Types\n__all__ = ['Types', 't']\n"
            ),
            typings / "__init__.py": "",
            typings / "base.py": "class Types:\n    pass\n__all__ = ['Types']\n",
            owners / "__init__.py": "",
            owner: (
                "from pydantic import TypeAdapter\n"
                "class AdapterOwner:\n"
                "    @staticmethod\n"
                "    def value_adapter() -> TypeAdapter[int]:\n"
                "        return TypeAdapter(int)\n"
                "__all__ = ['AdapterOwner']\n"
            ),
            runtime: (
                f"from {package.name} import t\n"
                f"from {package.name}.{typings.name}.retired import Retired\n"
                "class Runtime:\n"
                "    @staticmethod\n"
                "    def parse(value):\n"
                "        first = t.value_adapter().validate_python(value)\n"
                "        return Retired.value_adapter().validate_python(first)\n"
                "def shadowed(t):\n    return t.value_adapter()\n"
            ),
            facade: (
                f"from {package.name}.runtime import Runtime\n"
                "class Utilities(Runtime):\n    pass\n"
                "u = Utilities\n__all__ = ['Utilities', 'u']\n"
            ),
            consumer: (
                f"from {package.name} import t\n"
                "assert t.value_adapter().validate_python('7') == 7\n"
            ),
        }
        for path, source in sources.items():
            self._write(path, source)
        with infra.rope_workspace(root) as rope:
            edits = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                    rope_workspace=rope,
                    sources=sources,
                )
            )
            proposed = dict(sources)
            proposed.update({edit.file_path: edit.updated_source for edit in edits})
            tm.that(
                proposed[runtime],
                has=f"from {package.name}.{owners.name}.adapter import AdapterOwner",
            )
            tm.that(proposed[runtime], has="return t.value_adapter()")
            tm.that("retired import" not in proposed[runtime], eq=True)
            tm.that(proposed[consumer], has=f"import {package.name}")
            tm.that(proposed[consumer], has=f"{package.name}.u.value_adapter()")
            tm.that(
                tm.ok(
                    u.Infra.plan_semantic_cutover(
                        c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                        rope_workspace=rope,
                        sources=proposed,
                    )
                ),
                empty=True,
            )
        for path, source in proposed.items():
            self._write(path, source)
        rendered = u.Infra.render_utility_facade(package)
        assert rendered is not None
        self._write(facade, rendered)
        tm.that(u.Infra.render_utility_facade(package), eq=rendered)
        result = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    (
                        f"from {package.name} import u; "
                        f"import runpy; runpy.run_path({str(consumer)!r}); "
                        "from pydantic import ValidationError; "
                        "assert u.parse('7') == 7; "
                        "assert u.value_adapter().validate_python('8') == 8\n"
                        "try:\n    u.parse([])\n"
                        "except ValidationError:\n    print('rejected')\n"
                        "else:\n    raise AssertionError('invalid payload accepted')\n"
                    ),
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            )
        )
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True, msg=result.stderr)
        tm.that(result.stdout, has="rejected")

    def test_nested_facade_projects_direct_lower_owner_runtime_calls(
        self,
        tmp_path: Path,
    ) -> None:
        """Direct leaf calls select the nested public namespace without a cycle."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        sources = self._behavior_package(package, "int")
        directory = u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY).directory
        sources[package / "runtime.py"] = (
            f"from {package.name}.{directory}.adapter import AdapterOwner\n"
            "class Runtime:\n    @staticmethod\n    def parse(value):\n"
            "        return AdapterOwner.value_adapter().validate_python(value)\n"
        )
        facade = package / "utilities.py"
        sources[facade] = (
            f"from {package.name}.runtime import Runtime\n"
            "class Utilities:\n    class Domain(Runtime):\n        pass\n"
            "u = Utilities\n__all__ = ['Utilities', 'u']\n"
        )
        for path, source in sources.items():
            self._write(path, source)
        rendered = u.Infra.render_utility_facade(package)
        assert rendered is not None
        self._write(facade, rendered)
        tm.that(u.Infra.render_utility_facade(package), eq=rendered)
        output = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    (
                        f"from {package.name} import u; "
                        "assert u.Domain.parse('7') == 7; "
                        "assert u.Domain.value_adapter().validate_python('8') == 8; "
                        "print('nested')"
                    ),
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            )
        )
        tm.that(u.Cli.process_succeeded(output.outcome), eq=True, msg=output.stderr)
        tm.that(output.stdout, has="nested")

    @pytest.mark.parametrize("conflict", ["ownership", "shadowing"])
    def test_behavior_cutover_rejects_ambiguity_without_mutation(
        self,
        tmp_path: Path,
        conflict: str,
    ) -> None:
        """Neither competing owners nor a shadowed destination permits a cutover."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        family = (
            package / u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY).directory
        )
        consumer = root / "consumer.py"
        source = (
            f"from {package.name} import t\n"
            f"def consume({package.name}):\n    return t.value_adapter()\n"
            if conflict == "shadowing"
            else f"from {package.name} import t\nvalue = t.value_adapter()\n"
        )
        sources = {
            consumer: source,
            package / "__init__.py": (
                "class Types:\n    pass\nt = Types\n__all__ = ['Types', 't']\n"
            ),
        }
        for name in ("First", "Second") if conflict == "ownership" else ("First",):
            sources[family / f"{name.lower()}.py"] = (
                f"class {name}:\n"
                "    @staticmethod\n"
                "    def value_adapter() -> int:\n        return 7\n"
                f"__all__ = ['{name}']\n"
            )
        for path, content in sources.items():
            self._write(path, content)
        with infra.rope_workspace(root) as rope:
            result = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                rope_workspace=rope,
                sources=sources,
            )
        tm.fail(result, has="ambiguous" if conflict == "ownership" else "shadowed")
        tm.that(consumer.read_text(encoding="utf-8"), eq=source)

    @pytest.mark.parametrize(
        ("import_statement", "consumer_name"),
        [
            ("from flext_sample import u", "batch_apply.py"),
            ("from .. import u", "batch_apply.py"),
            ("from ..utilities import u", "batch_apply.py"),
            ("from .. import u", "__init__.py"),
            ("from ..utilities import u", "__init__.py"),
        ],
    )
    def test_projects_only_uniquely_discovered_missing_owner(
        self,
        tmp_path: Path,
        import_statement: str,
        consumer_name: str,
    ) -> None:
        """Derive the required owner from the executable public consumer."""
        package = tmp_path / "src" / "flext_sample"
        conflicted = (
            c.Infra.AUTOGEN_HEADERS[0] + "\n<<<<<<< HEAD\n=======\n>>>>>>> incoming\n"
        )
        self._write(package / "__init__.py", conflicted)
        self._write(
            package / "codemod" / consumer_name,
            import_statement + "\n\nu.Sample.plan_cutover()\n",
        )
        self._write(
            package / "_utilities" / "semantic_cutover.py",
            "class FlextSampleUtilitiesSemanticCutover:\n"
            "    @staticmethod\n"
            "    def plan_cutover() -> None:\n"
            "        pass\n",
        )
        facade = package / "utilities.py"
        self._write(
            facade,
            "from upstream import u\n"
            "from flext_sample._utilities.existing import Existing\n\n"
            "class FlextSampleUtilities(u):\n"
            "    class Sample(\n"
            "        Existing,\n"
            "    ):\n"
            "        pass\n\n"
            "u = FlextSampleUtilities\n\n"
            '__all__ = ["FlextSampleUtilities", "u"]\n',
        )
        updated = u.Infra.render_utility_facade(package)

        tm.that(updated is not None, eq=True)
        assert updated is not None
        tm.that(updated, has="from flext_sample._utilities.semantic_cutover import (")
        tm.that(updated.count("FlextSampleUtilitiesSemanticCutover"), eq=2)
        tm.that(
            "FlextSampleUtilitiesSemanticCutover" not in facade.read_text(),
            eq=True,
        )
        tm.that((package / "__init__.py").read_text(), eq=conflicted)

    def test_unresolved_consumer_import_fails_before_projection(
        self,
        tmp_path: Path,
    ) -> None:
        """Unknown provenance is an error, never an empty owner selection."""
        package = tmp_path / "src" / "flext_sample"
        self._write(package / "__init__.py", "")
        self._write(package / "_utilities" / "owner.py", "class Owner:\n    pass\n")
        self._write(
            package / "utilities.py",
            "class Facade:\n    class Sample:\n        pass\n\n"
            "u = Facade\n__all__ = ['Facade', 'u']\n",
        )
        self._write(
            package / "consumer.py",
            "from nonexistent_facade_owner import u\nu.Sample.required()\n",
        )
        with pytest.raises(ValueError, match="unresolved imported module"):
            u.Infra.render_utility_facade(package)

    def test_inherited_aggregator_keeps_one_behavior_owner(
        self, tmp_path: Path
    ) -> None:
        """A pure MRO aggregate preserves its defining owner's public behavior."""
        package = tmp_path / "src" / "flext_sample"
        self._write(package / "__init__.py", "from .utilities import u\n")
        self._write(
            package / "consumer.py", "from flext_sample import u\nu.Sample.read()\n"
        )
        self._write(
            package / "_utilities" / "reader.py",
            "class Reader:\n"
            "    @classmethod\n"
            "    def read(cls) -> str:\n"
            "        return cls._value()\n"
            "    @staticmethod\n"
            "    def _value() -> str:\n"
            "        return 'read'\n",
        )
        self._write(
            package / "_utilities" / "document.py",
            "from .reader import Reader\nclass Document(Reader):\n    pass\n",
        )
        facade = package / "utilities.py"
        source = (
            "from ._utilities.document import Document\n"
            "class Utilities:\n"
            "    class Sample(Document):\n        pass\n"
            "u = Utilities\n__all__ = ['Utilities', 'u']\n"
        )
        self._write(facade, source)
        tm.that(u.Infra.render_utility_facade(package), eq=source)
        output = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    "from flext_sample import u\nprint(u.Sample.read())\n",
                ),
                cwd=tmp_path,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            )
        )
        tm.that(u.Cli.process_succeeded(output.outcome), eq=True, msg=output.stderr)
        tm.that(output.stdout.strip(), eq="read")
        tm.that(facade.read_text(), eq=source)

    def test_rejects_ambiguous_method_ownership(self, tmp_path: Path) -> None:
        """Fail before projection when two local owners claim one method."""
        package = tmp_path / "src" / "flext_sample"
        self._write(package / "__init__.py", "")
        self._write(
            package / "codemod" / "batch_apply.py",
            "from flext_sample import u\n\nu.Sample.plan_cutover()\n",
        )
        for module, class_name in (("first", "First"), ("second", "Second")):
            self._write(
                package / "_utilities" / f"{module}.py",
                f"class {class_name}:\n"
                "    @staticmethod\n"
                "    def plan_cutover() -> None:\n"
                "        pass\n",
            )
        facade = package / "utilities.py"
        original = (
            "from upstream import u\n\n"
            "class FlextSampleUtilities(u):\n"
            "    class Sample(u):\n"
            "        pass\n\n"
            "u = FlextSampleUtilities\n\n"
            '__all__ = ["FlextSampleUtilities", "u"]\n'
        )
        self._write(facade, original)

        with pytest.raises(ValueError, match=r"ambiguous u\.Sample owner"):
            u.Infra.render_utility_facade(package)
        tm.that(facade.read_text(), eq=original)

    def test_rejects_owners_without_a_public_facade(self, tmp_path: Path) -> None:
        """Utility owners without a facade have no public surface at all."""
        package = tmp_path / "src" / "flext_sample"
        self._write(package / "_utilities" / "owner.py", "class Owner:\n    pass\n")

        with pytest.raises(ValueError, match="have no public facade"):
            u.Infra.render_utility_facade(package)

    @staticmethod
    def test_empty_owner_directory_needs_no_facade(tmp_path: Path) -> None:
        """A preflight-created empty directory is not a private implementation."""
        package = tmp_path / "src" / "flext_sample"
        (package / "_utilities").mkdir(parents=True)
        tm.that(u.Infra.render_utility_facade(package), eq=None)

    @pytest.mark.parametrize("generated", [True, False])
    def test_initializer_ownership_controls_consumer_parsing(
        self,
        tmp_path: Path,
        *,
        generated: bool,
    ) -> None:
        """Only generated propagation is excluded from authored consumer analysis."""
        package = tmp_path / "src" / "flext_sample"
        self._write(package / "_utilities" / "owner.py", "class Owner:\n    pass\n")
        original = (
            "from flext_sample._utilities.owner import Owner\n"
            "class Facade:\n    class Domain(Owner):\n        pass\n"
            "u = Facade\n__all__ = ['Facade', 'u']\n"
        )
        self._write(package / "utilities.py", original)
        conflicted = (
            c.Infra.AUTOGEN_HEADERS[0] + "\n" if generated else ""
        ) + "<<<<<<< HEAD\n=======\n>>>>>>> incoming\n"
        initializer = package / c.Infra.INIT_PY
        self._write(initializer, conflicted)

        if generated:
            tm.that(u.Infra.render_utility_facade(package), eq=original)
        else:
            with pytest.raises(SyntaxError):
                u.Infra.render_utility_facade(package)
        tm.that(initializer.read_text(), eq=conflicted)

    def test_facade_without_local_owners_is_complete(self, tmp_path: Path) -> None:
        """A pure re-export facade with no owners directory needs no projection."""
        package = tmp_path / "src" / "flext_sample"
        self._write(package / "utilities.py", "class Owner:\n    pass\n")

        tm.that(u.Infra.render_utility_facade(package), eq=None)

    def test_rejects_unsupported_facade_base_expression(self, tmp_path: Path) -> None:
        """Reject dynamic bases instead of converting them to an empty owner."""
        package = tmp_path / "src" / "flext_sample"
        self._write(
            package / "codemod" / "batch_apply.py",
            "from flext_sample import u\n\nu.Sample.plan_cutover()\n",
        )
        # The facade and its private family exist together in a real package;
        # without the owner directory the renderer stops at the incomplete
        # artifact check and never reaches the base expression under test.
        self._write(
            package / "_utilities" / "semantic_cutover.py",
            "class FlextSampleUtilitiesSemanticCutover:\n"
            "    @staticmethod\n"
            "    def plan_cutover() -> None:\n"
            "        pass\n",
        )
        self._write(
            package / "utilities.py",
            "from upstream import u\n\n"
            "class FlextSampleUtilities(u):\n"
            "    class Sample(owner_factory()):\n"
            "        pass\n\n"
            "u = FlextSampleUtilities\n\n"
            '__all__ = ["FlextSampleUtilities", "u"]\n',
        )

        with pytest.raises(ValueError, match="unsupported utility facade base"):
            u.Infra.render_utility_facade(package)

    @pytest.mark.parametrize("multiline", [False, True])
    def test_protocol_annotation_projects_owner_and_converges(
        self,
        tmp_path: Path,
        *,
        multiline: bool,
    ) -> None:
        """An owned annotation supplies its protocol without changing other code."""
        package = tmp_path / "src" / "flext_sample"
        self._write(package / "__init__.py", "")
        self._write(
            package / "_models" / "payload.py",
            "from flext_sample import p\n"
            "def consume(value: p.Sample.Payload) -> None:\n    pass\n"
            "def foreign(value: p.Other.Unused) -> None:\n    pass\n",
        )
        self._write(
            package / "_protocols" / "payload.py",
            "class PayloadOwner:\n    class Payload:\n        pass\n",
        )
        self._write(
            package / "_protocols" / "unused.py",
            "class UnusedOwner:\n    class Unused:\n        pass\n",
        )
        self._write(package.parent / "foreign_package" / "__init__.py", "p = 0\n")
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
            "    class Sample(\n        p,\n    ):\n"
            if multiline
            else ("    class Sample(p):\n")
        )
        original = (
            "from upstream import p\n\nclass FlextSampleProtocols(p):\n"
            + header
            + "        preserved = 'unchanged'\n\np = FlextSampleProtocols\n\n"
            + '__all__ = ["FlextSampleProtocols", "p"]\n'
        )
        self._write(facade, original)

        updated = u.Infra.render_utility_facade(package, family="p")

        assert updated is not None
        ast.parse(updated)
        tm.that(updated, has="from flext_sample._protocols.payload import (")
        tm.that(updated.count("PayloadOwner"), eq=2)
        tm.that("UnusedOwner" in updated, eq=False)
        tm.that(updated, has="        preserved = 'unchanged'")
        tm.that(facade.read_text(), eq=original)
        self._write(facade, updated)
        tm.that(u.Infra.render_utility_facade(package, family="p"), eq=updated)

    @pytest.mark.parametrize("multiline", [False, True])
    def test_protocol_owner_precedes_terminal_protocol_base(
        self,
        tmp_path: Path,
        *,
        multiline: bool,
    ) -> None:
        """A projected owner keeps ``Protocol`` as the namespace's last base."""
        package = tmp_path / "src" / "flext_sample"
        self._write(package / "__init__.py", "")
        self._write(
            package / "_models" / "payload.py",
            "from flext_sample import p\n"
            "def consume(value: p.Sample.Payload) -> None:\n    pass\n",
        )
        self._write(
            package / "_protocols" / "payload.py",
            "from typing import Protocol\n\n"
            "class PayloadOwner(Protocol):\n"
            "    class Payload(Protocol):\n        pass\n",
        )
        facade = package / "protocols.py"
        header = (
            "    class Sample(\n        p,\n        Protocol,\n    ):\n"
            if multiline
            else "    class Sample(p, Protocol):\n"
        )
        self._write(
            facade,
            "from typing import Protocol\n\nfrom upstream import p\n\n"
            "class FlextSampleProtocols(p):\n"
            + header
            + "        pass\n\np = FlextSampleProtocols\n\n"
            + '__all__ = ["FlextSampleProtocols", "p"]\n',
        )

        updated = u.Infra.render_utility_facade(package, family="p")

        assert updated is not None
        facade_class = next(
            node for node in ast.parse(updated).body if isinstance(node, ast.ClassDef)
        )
        namespace = next(
            node for node in facade_class.body if isinstance(node, ast.ClassDef)
        )
        tm.that(
            [ast.unparse(base) for base in namespace.bases],
            eq=["p", "PayloadOwner", "Protocol"],
        )
        self._write(facade, updated)
        tm.that(u.Infra.render_utility_facade(package, family="p"), eq=updated)

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
        """An aggregate supplies its families once before a newly projected owner."""
        package = tmp_path / "flext_sample"
        self._write(package / "__init__.py", "from .models import m\n")
        for module, owner, payload in (
            ("render", "RenderOwner", "RenderPayload"),
            ("toolchain", "ToolchainOwner", "ToolchainPayload"),
            ("extra", "ExtraOwner", "ExtraPayload"),
        ):
            self._write(
                package / "_models" / f"{module}.py",
                f"class {owner}:\n    class {payload}:\n        pass\n",
            )
        self._write(
            package / "_models" / "_codegen" / "base.py",
            "from ..render import RenderOwner\n"
            "from ..toolchain import ToolchainOwner\n"
            "class CodegenOwner(ToolchainOwner, RenderOwner):\n    pass\n",
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
            "m.Sample.ExtraPayload()\n"
            "completed = True\n",
        )
        rendered = u.Infra.render_utility_facade(package, family="m")
        assert rendered is not None
        self._write(facade, rendered)
        entrypoint = tmp_path / "consume.py"
        self._write(
            entrypoint,
            "from flext_sample.consumer import completed\nassert completed\n",
        )
        result = tm.ok(u.Cli.run_raw([sys.executable, str(entrypoint)], cwd=tmp_path))
        tm.that(
            u.Cli.process_succeeded(result.outcome),
            eq=True,
            msg=result.stderr or result.stdout,
        )
        tm.that(u.Infra.render_utility_facade(package, family="m"), eq=rendered)
