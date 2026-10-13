"""Real-source regression evidence for staged semantic cutovers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import importlib.util
import sys
from typing import TYPE_CHECKING

import pytest
from flext_cli import u as cli_u

from flext_core import u as core_u
from flext_infra import infra
from flext_infra.codemod import FlextInfraCodemodSemanticApply
from tests import c, m, t, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraSemanticPhaseContract:
    """Require planned and published sources to reach the same fixed point."""

    @staticmethod
    def test_declaring_model_factory_preserves_public_empty_roundtrips(
        tmp_path: Path,
    ) -> None:
        """The model primitive and projected utility preserve real consumer defaults."""
        consumer = tmp_path / "declaration_factory_consumer.py"
        consumer.write_text(
            "from flext_core import m, t, u\n"
            "from typing_extensions import TypeForm\n"
            "type Bag[T] = t.MutableSequenceOf[T]\n"
            "class ModelOwned(m.ContractModel):\n"
            "    values: Bag[str] = m.Field(default_factory=m.empty("
            'TypeForm(Bag[str])), description="Consumer values")\n'
            "class UtilityProjected(m.ContractModel):\n"
            "    values: Bag[str] = m.Field(default_factory=u.empty("
            'TypeForm(Bag[str])), description="Consumer values")\n'
            "def verify():\n"
            "    model_default = ModelOwned()\n"
            "    utility_default = UtilityProjected()\n"
            "    assert model_default.model_dump_json() == "
            "utility_default.model_dump_json()\n"
            "    for model in (ModelOwned, UtilityProjected):\n"
            "        first, second = model(), model()\n"
            "        explicit = model.model_validate_json('{\"values\": []}')\n"
            "        first.values.append('consumer value')\n"
            "        assert second.model_dump_json() == explicit.model_dump_json()\n"
            "        restored = model.model_validate_json(first.model_dump_json())\n"
            "        assert restored.values == first.values\n"
            "verify()\n",
            encoding=c.DEFAULT_ENCODING,
        )
        specification = importlib.util.spec_from_file_location(
            consumer.stem,
            consumer,
        )
        if specification is None or specification.loader is None:
            pytest.fail("real declaration consumer has no import loader")
        module = importlib.util.module_from_spec(specification)
        sys.modules[specification.name] = module
        try:
            specification.loader.exec_module(module)
        finally:
            sys.modules.pop(specification.name)

    @staticmethod
    @pytest.mark.parametrize("shadowed", [False, True])
    def test_member_contextual_packages_keep_independent_owners(
        tmp_path: Path, *, shadowed: bool
    ) -> None:
        """Equal contextual import names in separate projects remain independent."""
        root, _package = u.Tests.create_lazy_init_workspace(tmp_path)
        sources: t.MutableMappingKV[Path, str] = {}
        consumers: list[Path] = []
        for name in ("first_member", "second_member"):
            member = u.Tests.mk_project(
                root,
                name,
                pyproject=f'[project]\nname = "{name}"\nversion = "1.0.0"\n',
                with_src=True,
            )
            u.Tests.initialize_git_repo(member)
            provider = member / "src" / name / "utilities.py"
            sources[provider] = (
                "from flext_cli import FlextCliUtilities\n"
                "class MemberUtilities(FlextCliUtilities):\n    pass\n"
            )
            context = member / "consumer_context"
            context.mkdir()
            path = context / "consumer.py"
            consumers.append(path)
            sources.update({
                context / "__init__.py": (
                    "from .utilities import ConsumerContextUtilities as u\n"
                ),
                context / "utilities.py": (
                    "from first_member.utilities import MemberUtilities\n"
                    "class ConsumerContextUtilities(MemberUtilities):\n"
                    + (
                        "    json_dict_adapter = None\n"
                        if shadowed and name == "second_member"
                        else "    pass\n"
                    )
                ),
                path: (
                    "from flext_cli import t\n"
                    "from consumer_context import u\n"
                    "value = t.json_dict_adapter().validate_python({'name': 'value'})\n"
                ),
            })
        u.Tests.declare_workspace_projects(root, ("first_member", "second_member"))
        for path, source in sources.items():
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        with infra.rope_workspace(root) as rope:
            planned = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                rope_workspace=rope,
                sources=sources,
            )
        if shadowed:
            tm.fail(planned, has="receiver is shadowed")
            for path, source in sources.items():
                tm.that(path.read_text(encoding="utf-8"), eq=source)
            return
        edits = tm.ok(planned)
        tm.that(tuple(edit.file_path for edit in edits), eq=tuple(consumers))
        for edit in edits:
            tm.that(edit.updated_source, has="u.json_dict_adapter()")
            tm.that(
                edit.file_path.read_text(encoding="utf-8"), eq=sources[edit.file_path]
            )

    @staticmethod
    def test_local_utility_binding_preserves_global_cli_runtime(tmp_path: Path) -> None:
        """Reusing a sufficient local core import must not replace global CLI u."""
        tm.that(tm.ok(cli_u.Cli.env_read("FIELD", {"FIELD": "value"})), eq="value")
        tm.that(hasattr(core_u, "Cli"), eq=False)
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = package / "consumer.py"
        unaffected = (
            'def existing():\n    return u.Cli.env_read("FIELD", {"FIELD": "value"})\n'
        )
        source = (
            "from flext_cli import u\n"
            "def migrated():\n"
            "    from flext_core import t, u\n"
            '    return t.scalar_mapping_adapter().validate_python({"name": "value"})\n'
            + unaffected
        )
        path.write_text(source, encoding="utf-8")
        phase = c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION
        with infra.rope_workspace(root) as rope:
            planned = tm.ok(
                u.Infra.plan_semantic_cutover(
                    phase, rope_workspace=rope, sources={path: source}
                )
            )
            tm.that(len(planned), eq=1)
            updated = planned[0].updated_source
            tm.that(updated, has="from flext_cli import u")
            tm.that(updated, has="    from flext_core import u")
            tm.that(updated, has=unaffected)
            tm.that(updated, has="    return u.scalar_mapping_adapter()")
            tm.that(updated.count("from flext_core import"), eq=1)
            remaining = tm.ok(
                u.Infra.plan_semantic_cutover(
                    phase, rope_workspace=rope, sources={path: updated}
                )
            )
        tm.that(remaining, empty=True)
        tm.that(path.read_text(encoding="utf-8"), eq=source)

    @staticmethod
    def _reviewed_behavior_provider(
        package: Path,
        variant: str,
    ) -> t.MutableMappingKV[Path, str]:
        """Declare a governed provider with real core inheritance and utility MRO.

        Returns:
            Source declarations consumed by the real semantic planner.

        """
        provider = package.parent / "flext_reviewed"
        private = provider / "_utilities"
        private.mkdir(parents=True)
        sources = {
            provider / "__init__.py": (
                "from .typings import t\nfrom .utilities import u\n"
                '__all__ = ["t", "u"]\n'
            ),
            provider / "typings.py": (
                "from flext_core import t as core_t\n"
                "class FlextReviewedTypes(core_t):\n    pass\n"
                't = FlextReviewedTypes\n__all__ = ["FlextReviewedTypes", "t"]\n'
            ),
            private / "base.py": (
                "from flext_core import u as core_u\n"
                "class FlextReviewedBase(core_u):\n"
                "    @classmethod\n"
                "    def scalar_mapping_adapter(cls):\n"
                "        return cls.type_adapter(str)\n"
                '__all__ = ["FlextReviewedBase"]\n'
            ),
            private / "derived.py": (
                "from .base import FlextReviewedBase\n"
                "class FlextReviewedDerived(FlextReviewedBase):\n"
                "    @classmethod\n"
                "    def scalar_mapping_adapter(cls):\n"
                "        return cls.type_adapter(int)\n"
                '__all__ = ["FlextReviewedDerived"]\n'
            ),
            private / "unused.py": (
                "class FlextReviewedUnused:\n"
                "    @staticmethod\n"
                "    def scalar_mapping_adapter():\n        return None\n"
                '__all__ = ["FlextReviewedUnused"]\n'
            ),
            provider / "utilities.py": (
                "from ._utilities.derived import FlextReviewedDerived\n"
                "class FlextReviewedUtilities(FlextReviewedDerived):\n    pass\n"
                "u = FlextReviewedUtilities\n"
                '__all__ = ["FlextReviewedUtilities", "u"]\n'
            ),
        }
        if variant == "orphan":
            sources.pop(private / "derived.py")
            sources.pop(private / "unused.py")
            sources[provider / "utilities.py"] = (
                "class FlextReviewedUtilities:\n    pass\n"
                "u = FlextReviewedUtilities\n"
                '__all__ = ["FlextReviewedUtilities", "u"]\n'
            )
        elif variant == "diamond":
            sources[private / "right.py"] = (
                "from .base import FlextReviewedBase\n"
                "class FlextReviewedRight(FlextReviewedBase):\n    pass\n"
                '__all__ = ["FlextReviewedRight"]\n'
            )
            sources[provider / "utilities.py"] = (
                "from ._utilities.derived import FlextReviewedDerived\n"
                "from ._utilities.right import FlextReviewedRight\n"
                "class FlextReviewedUtilities("
                "FlextReviewedDerived, FlextReviewedRight):\n"
                "    pass\n"
                "u = FlextReviewedUtilities\n"
                '__all__ = ["FlextReviewedUtilities", "u"]\n'
            )
        elif variant == "masked":
            sources[private / "derived.py"] = sources[private / "derived.py"].replace(
                "        return cls.type_adapter(int)\n",
                "        return cls.type_adapter(int)\n"
                "    scalar_mapping_adapter = None\n",
            )
        elif variant == "static-internal":
            sources[private / "derived.py"] = (
                sources[private / "derived.py"]
                .replace("@classmethod", "@staticmethod")
                .replace(
                    "def scalar_mapping_adapter(cls)", "def scalar_mapping_adapter()"
                )
                .replace("cls.type_adapter", "FlextReviewedBase.type_adapter")
            )
        return sources

    @staticmethod
    def test_reviewer_counterexamples_reject_atomically(tmp_path: Path) -> None:
        """Reproduce each unsafe identity, pending import and public-owner election."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = package / "consumer.py"
        provider = TestsFlextInfraSemanticPhaseContract._reviewed_behavior_provider(
            package, "orphan"
        )
        cases = {
            "unresolved competitor": (
                "if condition:\n    from flext_core import t\n"
                "else:\n    from unrelated_package import t\n"
                "value = t.scalar_mapping_adapter()\n"
            ),
            "pending imports": (
                "from flext_core import t as core_t\n"
                "from flext_cli import t as cli_t\n"
                "def first():\n    return core_t.scalar_mapping_adapter()\n"
                "def second():\n    return cli_t.json_dict_adapter()\n"
            ),
            "pending module imports": (
                "from flext_core import t as core_t\n"
                "from flext_cli import t as cli_t\n"
                "first = core_t.scalar_mapping_adapter()\n"
                "second = cli_t.json_dict_adapter()\n"
            ),
            "unreachable owner": (
                "from flext_reviewed import t\nvalue = t.scalar_mapping_adapter()\n"
            ),
        }
        accepted: list[str] = []
        for case, source in cases.items():
            sources = {**provider, path: source}
            for source_path, content in sources.items():
                source_path.write_text(content, encoding="utf-8")
            with infra.rope_workspace(root) as rope:
                planned = u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                    rope_workspace=rope,
                    sources=sources,
                )
            if planned.success:
                accepted.append(case)
            else:
                expected = (
                    "ambiguous imported identity"
                    if case == "unresolved competitor"
                    else "not reachable through public utilities"
                    if case == "unreachable owner"
                    else "conflicting relocated behavior import destination"
                )
                tm.fail(planned, has=expected)
            for source_path, content in sources.items():
                tm.that(source_path.read_text(encoding="utf-8"), eq=content)
        tm.that(accepted, eq=[])

    @staticmethod
    @pytest.mark.parametrize("variant", ["override", "diamond", "static-internal"])
    def test_public_utility_c3_elects_effective_owner(
        tmp_path: Path,
        variant: str,
    ) -> None:
        """A reachable derived override wins; exported uncomposed helpers do not."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = (
            package.parent / "flext_reviewed" / "consumer.py"
            if variant == "static-internal"
            else package / "consumer.py"
        )
        source = "from flext_reviewed import t\nvalue = t.scalar_mapping_adapter()\n"
        sources = {
            **TestsFlextInfraSemanticPhaseContract._reviewed_behavior_provider(
                package, variant
            ),
            path: source,
        }
        for source_path, content in sources.items():
            source_path.write_text(content, encoding="utf-8")
        phase = c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION
        with infra.rope_workspace(root) as rope:
            planned = tm.ok(
                u.Infra.plan_semantic_cutover(
                    phase, rope_workspace=rope, sources=sources
                )
            )
            tm.that(tuple(edit.file_path for edit in planned), eq=(path,))
            updated = planned[0].updated_source
            if variant == "static-internal":
                tm.that(updated, has="from flext_reviewed._utilities.derived import")
                tm.that(
                    updated, has="value = FlextReviewedDerived.scalar_mapping_adapter()"
                )
            else:
                tm.that(updated, has="from flext_reviewed import u")
                tm.that(updated, has="value = u.scalar_mapping_adapter()")
            remaining = tm.ok(
                u.Infra.plan_semantic_cutover(
                    phase, rope_workspace=rope, sources={**sources, path: updated}
                )
            )
        tm.that(remaining, empty=True)
        for source_path, content in sources.items():
            tm.that(source_path.read_text(encoding="utf-8"), eq=content)

    @staticmethod
    @pytest.mark.parametrize("variant", ["masked", "internal"])
    def test_utility_owner_masks_and_context_reject_atomically(
        tmp_path: Path,
        variant: str,
    ) -> None:
        """Reject later non-method masks and internal class-dependent dispatch."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        sources = TestsFlextInfraSemanticPhaseContract._reviewed_behavior_provider(
            package, variant
        )
        path = (
            package.parent / "flext_reviewed" / "consumer.py"
            if variant == "internal"
            else package / "consumer.py"
        )
        sources[path] = (
            "from flext_reviewed import t\nvalue = t.scalar_mapping_adapter()\n"
        )
        for source_path, content in sources.items():
            source_path.write_text(content, encoding="utf-8")
        with infra.rope_workspace(root) as rope:
            planned = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                rope_workspace=rope,
                sources=sources,
            )
        tm.fail(
            planned,
            has="requires facade dispatch"
            if variant == "internal"
            else "not reachable through public utilities",
        )
        for source_path, content in sources.items():
            tm.that(source_path.read_text(encoding="utf-8"), eq=content)

    @staticmethod
    @pytest.mark.parametrize("utilities_import", ["", "from flext_core import u\n"])
    def test_named_adapter_factories_bind_public_utilities(
        tmp_path: Path,
        utilities_import: str,
    ) -> None:
        """Discover real core factory owners and insert the missing public import."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = package / "consumer.py"
        source = (
            "from flext_core import t\n"
            + utilities_import
            + "value = t.strict_str_sequence_adapter().validate_python(['scope'])\n"
            + "other = t.scalar_mapping_adapter().validate_python({'name': 'value'})\n"
            + "untouched = 't.scalar_mapping_adapter()'\n"
            + "def local(t):\n    return t.scalar_mapping_adapter()\n"
        )
        path.write_text(source, encoding="utf-8")
        phase = c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION
        with infra.rope_workspace(root) as rope:
            planned = tm.ok(
                u.Infra.plan_semantic_cutover(
                    phase, rope_workspace=rope, sources={path: source}
                )
            )
            tm.that(len(planned), eq=1)
            updated = planned[0].updated_source
            tm.that(updated, has="u.strict_str_sequence_adapter()")
            tm.that(updated, has="u.scalar_mapping_adapter()")
            tm.that(updated, has="from flext_core import u")
            tm.that(updated, has="def local(t):\n    return t.scalar_mapping_adapter()")
            tm.that(updated, has="'t.scalar_mapping_adapter()'")
            remaining = tm.ok(
                u.Infra.plan_semantic_cutover(
                    phase, rope_workspace=rope, sources={path: updated}
                )
            )
        tm.that(remaining, empty=True)
        tm.that(path.read_text(encoding="utf-8"), eq=source)

    @staticmethod
    def test_named_adapter_factories_reject_shadowed_utilities(tmp_path: Path) -> None:
        """A locally bound utilities receiver cannot receive a factory rewrite."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = package / "consumer.py"
        source = (
            "from flext_core import t\n"
            "def local(u):\n    return t.scalar_mapping_adapter()\n"
        )
        path.write_text(source, encoding="utf-8")
        with infra.rope_workspace(root) as rope:
            planned = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                rope_workspace=rope,
                sources={path: source},
            )
        tm.fail(planned, has="receiver is shadowed")
        tm.that(path.read_text(encoding="utf-8"), eq=source)

    @staticmethod
    @pytest.mark.parametrize("binding", ["inherited", "override", "mask"])
    def test_contextual_utilities_resolve_real_inherited_members(
        tmp_path: Path,
        binding: str,
    ) -> None:
        """Contextual lazy facades reuse only the identical effective declaration.

        Raises:
            RuntimeError: If the published fixture has no source module loader.

        """
        root = u.Tests.create_lazy_init_workspace(tmp_path)[0]
        contextual = root / "consumer_context"
        contextual.mkdir()
        path = contextual / "consumer.py"
        source = (
            "from flext_cli import t\n"
            "from consumer_context import u\n"
            "value = t.json_dict_adapter().validate_python({'name': 'value'})\n"
            "items = t.json_list_adapter().validate_python(['value'])\n"
        )
        member = (
            "    @staticmethod\n    def json_dict_adapter():\n        return None\n"
            if binding == "override"
            else "    json_dict_adapter = None\n"
            if binding == "mask"
            else "    pass\n"
        )
        sources = {
            contextual / "__init__.py": (
                "from types import MappingProxyType\n"
                "from flext_core.lazy import install_lazy_exports\n"
                "__all__ = ('ConsumerContextUtilities', 'u')\n"
                "install_lazy_exports(__name__, globals(), MappingProxyType({"
                "'ConsumerContextUtilities': '.utilities', 'u': '.utilities'}), "
                "public_exports=__all__)\n"
            ),
            contextual / "utilities.py": (
                "from flext_tests import FlextTestsUtilities\n"
                "from flext_cli import FlextCliUtilities\n"
                "class ConsumerContextUtilities("
                "FlextTestsUtilities, FlextCliUtilities):\n"
                + member
                + "u = ConsumerContextUtilities\n"
                + "__all__ = ['ConsumerContextUtilities', 'u']\n"
            ),
            path: source,
        }
        for source_path, content in sources.items():
            tm.ok(u.Cli.atomic_write_text_file(source_path, content))
        phase = c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION
        updated = source
        with infra.rope_workspace(root) as rope:
            planned = u.Infra.plan_semantic_cutover(
                phase, rope_workspace=rope, sources=sources
            )
            if binding != "inherited":
                tm.fail(planned, has="receiver is shadowed")
            else:
                edits = tm.ok(planned)
                tm.that(tuple(edit.file_path for edit in edits), eq=(path,))
                updated = edits[0].updated_source
                tm.that(updated, has="from consumer_context import u")
                tm.that(updated, has="u.json_dict_adapter()")
                tm.that(updated, has="u.json_list_adapter()")
                tm.that("from flext_cli import u" in updated, eq=False)
                tm.that(
                    tm.ok(
                        u.Infra.plan_semantic_cutover(
                            phase,
                            rope_workspace=rope,
                            sources={**sources, path: updated},
                        )
                    ),
                    empty=True,
                )
        for source_path, content in sources.items():
            tm.that(source_path.read_text(encoding="utf-8"), eq=content)
        if binding == "inherited":
            tm.ok(u.Cli.atomic_write_text_file(path, updated))
            package_spec = importlib.util.spec_from_file_location(
                contextual.name, contextual / "__init__.py"
            )
            consumer_spec = importlib.util.spec_from_file_location(
                f"{contextual.name}.consumer", path
            )
            if (
                package_spec is None
                or package_spec.loader is None
                or consumer_spec is None
                or consumer_spec.loader is None
            ):
                msg = "Published contextual consumer has no loader"
                raise RuntimeError(msg)
            loaded_package = importlib.util.module_from_spec(package_spec)
            consumer = importlib.util.module_from_spec(consumer_spec)
            tm.that(contextual.name in sys.modules, eq=False)
            sys.modules[contextual.name] = loaded_package
            try:
                package_spec.loader.exec_module(loaded_package)
                consumer_spec.loader.exec_module(consumer)
                tm.that(consumer.value, eq={"name": "value"})
                tm.that(consumer.items, eq=["value"])
            finally:
                sys.modules.pop(f"{contextual.name}.utilities", None)
                sys.modules.pop(contextual.name)

    @staticmethod
    def test_named_adapter_factories_reject_ambiguous_imports(tmp_path: Path) -> None:
        """Two imported typing identities cannot elect a utilities receiver."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = package / "consumer.py"
        source = (
            "from flext_core import t\n"
            "from flext_cli import t\n"
            "value = t.scalar_mapping_adapter()\n"
        )
        path.write_text(source, encoding="utf-8")
        with infra.rope_workspace(root) as rope:
            planned = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                rope_workspace=rope,
                sources={path: source},
            )
        tm.fail(planned, has="ambiguous imported identity")
        tm.that(path.read_text(encoding="utf-8"), eq=source)

    @staticmethod
    @pytest.mark.parametrize("inherited_import", [False, True])
    def test_relocated_behavior_runs_through_its_real_consumer(
        tmp_path: Path,
        inherited_import: bool,
    ) -> None:
        """Typing facade imports are removed while the utility behavior runs."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        typing_family = u.Infra.facade_family_declared_by(c.Infra.TYPINGS_PY)
        utility_family = u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY)
        stem = u.derive_class_stem(root.name)
        typing_owner = f"{stem}{typing_family.suffix}"
        utility_owner = f"{stem}{utility_family.suffix}"
        parser_owner = f"{utility_owner}Parser"
        utility_directory = package / utility_family.directory
        utility_directory.mkdir()
        sources = {
            package / c.Infra.INIT_PY: (
                f"from {package.name}.typings import t\n"
                f"from {package.name}.utilities import u\n"
                '__all__ = ["t", "u"]\n'
            ),
            package / c.Infra.TYPINGS_PY: (
                f"class {typing_owner}:\n    pass\nt = {typing_owner}\n"
            ),
            utility_directory / "parser.py": (
                f"class {parser_owner}:\n"
                "    @staticmethod\n"
                "    def parse(value: str) -> str:\n"
                "        return value.upper()\n"
                f'__all__ = ["{parser_owner}"]\n'
            ),
            package / c.Infra.UTILITIES_PY: (
                f"from {package.name}.{utility_family.directory}.parser "
                f"import {parser_owner}\n"
                f"class {utility_owner}({parser_owner}):\n    pass\n"
                f"u = {utility_owner}\n"
            ),
            package / "consumer.py": (
                f"from {package.name}.typings import {typing_owner}\n"
                f"value = {typing_owner}.parse('aligned')\n"
            ),
            package / "unrelated.py": (
                f"from {package.name}.typings import {typing_owner}\n"
                f"owner = {typing_owner}.__name__\n"
                "value = 'unchanged'.upper()\n"
            ),
        }
        if inherited_import:
            consumer_package = package.with_name(f"{package.name}_consumer")
            consumer_package.mkdir()
            consumer_owner = f"{utility_owner}Consumer"
            sources[consumer_package / c.Infra.INIT_PY] = (
                f"from {package.name}.utilities import {utility_owner}\n"
                f"class {consumer_owner}({utility_owner}):\n    pass\n"
                f"u = {consumer_owner}\n"
                f'__all__ = ["{consumer_owner}", "u"]\n'
            )
            sources[package / "consumer.py"] = (
                f"from {consumer_package.name} import u\n"
                f"from {package.name}.typings import {typing_owner}\n"
                f"value = {typing_owner}.parse('aligned')\n"
                "existing = u.parse('existing')\n"
            )
        for path, source in sources.items():
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        tm.that(
            u.Infra.public_export_names_source(
                sources[utility_directory / "parser.py"],
            ),
            eq=(parser_owner,),
        )
        with infra.rope_workspace(root) as rope:
            edits = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.DECLARATION_RELOCATION,
                    rope_workspace=rope,
                    sources=sources,
                ),
            )
        tm.that(edits, empty=False)
        for edit in edits:
            tm.ok(u.Cli.atomic_write_text_file(edit.file_path, edit.updated_source))
        result = tm.ok(
            u.Cli.run(
                [
                    sys.executable,
                    "-c",
                    (
                        f"from {package.name}.consumer import value; "
                        f"from {package.name}.unrelated import "
                        "owner, value as unrelated; "
                        "print(value, unrelated, owner)"
                    ),
                ],
                cwd=root,
                options=m.Cli.ProcessOptions(
                    env={
                        c.Infra.ORCHESTRATOR_ENV_PYTHONPATH: str(
                            root / c.Infra.DEFAULT_SRC_DIR,
                        ),
                    },
                ),
            ),
        )
        tm.that(result.stdout.strip(), eq=f"ALIGNED UNCHANGED {typing_owner}")

    @staticmethod
    @pytest.mark.parametrize("guarded", [False, True])
    @pytest.mark.parametrize(
        "upstream_import",
        [
            "from flext_core import c as core_c",
            "from flext_core.constants import FlextConstants as core_c",
        ],
    )
    def test_constant_consumers_resolve_upstream_binding_without_shadow_rewrites(
        tmp_path: Path,
        upstream_import: str,
        *,
        guarded: bool,
    ) -> None:
        """Inherited constants use the existing facade and reach a fixed point."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        family = u.Infra.facade_family_declared_by(c.Infra.CONSTANTS_PY)
        owner = f"{u.derive_class_stem(root.name)}{family.suffix}"
        path = package / "consumer.py"
        shadowed = "def local(core_c):\n    return core_c.PRIMITIVES_TYPES\n"
        sources = {
            package / c.Infra.CONSTANTS_PY: (
                "from flext_cli import c\n"
                f"class {owner}(c):\n    pass\n"
                f"c = {owner}\n"
                f'__all__ = ["{owner}", "c"]\n'
            ),
            package / c.Infra.INIT_PY: 'from .constants import c\n__all__ = ["c"]\n',
            path: (
                f"{upstream_import}\n"
                f"from {package.name} import c\n"
                "upstream = core_c.PRIMITIVES_TYPES\n"
                "downstream = c.PRIMITIVES_TYPES\n\n"
                f"{shadowed}"
            ),
        }
        if guarded:
            sources[path] = (
                "from __future__ import annotations\n"
                "from typing import TYPE_CHECKING\n"
                f"from {package.name} import c\n"
                "# Keep the provider documentation.\n"
                "if TYPE_CHECKING:  # Annotation boundary.\n"
                f"    {upstream_import}\n"
                "def annotated(value: core_c):\n"
                "    return c.PRIMITIVES_TYPES\n"
                "downstream = c.PRIMITIVES_TYPES\n\n"
                f"{shadowed}"
            )
        for source_path, source in sources.items():
            source_path.write_text(source, encoding="utf-8")
        phase = c.Infra.SemanticCutoverPhase.CONSTANT_CONSUMERS
        with infra.rope_workspace(root) as rope:
            planned = u.Infra.plan_semantic_cutover(
                phase,
                rope_workspace=rope,
                sources=sources,
            )
            tm.ok(planned)
            tm.that(tuple(edit.file_path for edit in planned.value), eq=(path,))
            updated = planned.value[0].updated_source
            if guarded:
                tm.that(updated, has="def annotated(value: c):")
                tm.that(updated, has="# Keep the provider documentation.")
                tm.that(updated, has="# Annotation boundary.")
                tm.that(updated, lacks="TYPE_CHECKING")
            else:
                tm.that(updated, has="upstream = c.PRIMITIVES_TYPES")
            tm.that(updated, has="downstream = c.PRIMITIVES_TYPES")
            tm.that(updated, has=shadowed)
            tm.that(updated.count(f"from {package.name} import c"), eq=1)
            tm.that(upstream_import in updated, eq=False)
            remaining = u.Infra.plan_semantic_cutover(
                phase,
                rope_workspace=rope,
                sources={**sources, path: updated},
            )
        tm.ok(remaining)
        tm.that(remaining.value, empty=True)
        for source_path, source in sources.items():
            tm.that(source_path.read_text(encoding="utf-8"), eq=source)

    @staticmethod
    @pytest.mark.parametrize("case", ["ambiguous", "cyclic"])
    def test_constant_consumers_reject_unproven_upstream_bindings(
        tmp_path: Path,
        case: str,
    ) -> None:
        """Competing terminal identities and export cycles never yield edits."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        upstream = package.parent / "flext_upstream"
        upstream.mkdir()
        family = u.Infra.facade_family_declared_by(c.Infra.CONSTANTS_PY)
        owner = f"{u.derive_class_stem(root.name)}{family.suffix}"
        sources = {
            package / c.Infra.CONSTANTS_PY: (
                f'class {owner}:\n    pass\nc = {owner}\n__all__ = ["{owner}", "c"]\n'
            ),
            package / "consumer.py": (
                "from flext_upstream import c as core_c\n"
                f"from {package.name} import c\n"
                "value = core_c.PRIMITIVES_TYPES\n"
            ),
            upstream / c.Infra.INIT_PY: (
                "from .left import Left as c\nfrom .right import Right as c\n"
                if case == "ambiguous"
                else "from .loop import c\n"
            ),
            upstream / "left.py": "class Left:\n    pass\n",
            upstream / "right.py": "class Right:\n    pass\n",
            upstream / "loop.py": "from . import c\n",
        }
        for path, source in sources.items():
            path.write_text(source, encoding="utf-8")
        with infra.rope_workspace(root) as rope:
            planned = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CONSTANT_CONSUMERS,
                rope_workspace=rope,
                sources=sources,
            )
        tm.fail(planned, has=case)
        tm.that(planned.error, has="flext_upstream.c")
        for path, source in sources.items():
            tm.that(path.read_text(encoding="utf-8"), eq=source)

    @staticmethod
    def test_annotations_and_nesting_complete_in_one_atomic_cutover(
        tmp_path: Path,
    ) -> None:
        """Test annotations and nesting complete in one atomic cutover."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        # Publication runs through the codegen transaction, which coordinates
        # only inside an exact Git worktree root, exactly as in production.
        u.Tests.initialize_git_repo(root)
        family = u.Infra.facade_family_declared_by(c.Infra.CONSTANTS_PY)
        owner = f"{u.derive_class_stem(root.name)}{family.suffix}"
        path = package / "constants.py"
        u.Tests.write_lazy_init_namespace_module(
            path,
            class_name=owner,
            alias="c",
            extra_class_names=(f"{owner}Member",),
        )
        tm.ok(u.Tests.provision_python_project_environment(root))
        source = path.read_text(encoding="utf-8").replace(
            "from __future__ import annotations\n",
            "",
        )
        path.write_text(source, encoding="utf-8")
        # Semantic publication runs inside a codegen transaction, which only
        # coordinates through a real repository rooted at the project.
        u.Tests.initialize_git_repo(root)
        finding = m.Infra.ModScanFinding(
            rule_file="require-future-annotations.yml",
            rule_id="require-future-annotations",
            repository=root.name,
            file=path.relative_to(root),
            range={},
            text=source,
            actionable=False,
            classification=c.Infra.ModScanFindingClass.DETECTION_ONLY,
            payload={},
        )
        report = m.Infra.ModScanReport(
            findings=1,
            actionable=0,
            detection_only=1,
            non_actionable_with_fix=0,
            files=frozenset({path}),
            entries=(finding,),
        )
        with infra.rope_workspace(root) as rope:
            tm.ok(
                FlextInfraCodemodSemanticApply.apply(
                    root,
                    report,
                    rope,
                    source_preview=infra.source_preview(root),
                    workspace_factory=infra.rope_workspace,
                )
            )
        published = path.read_text(encoding="utf-8")
        tm.that(published, has="from __future__ import annotations")
        tm.that(published, has=f"    class {owner}Member")
        with infra.rope_workspace(root) as rope:
            tm.ok(
                FlextInfraCodemodSemanticApply.apply(
                    root,
                    report,
                    rope,
                    source_preview=infra.source_preview(root),
                    workspace_factory=infra.rope_workspace,
                )
            )
        tm.that(path.read_text(encoding="utf-8"), eq=published)

    @staticmethod
    def test_nesting_replans_proposed_sources_without_publishing(
        tmp_path: Path,
    ) -> None:
        """Test nesting replans proposed sources without publishing."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        family = u.Infra.facade_family_declared_by(c.Infra.CONSTANTS_PY)
        owner = f"{u.derive_class_stem(root.name)}{family.suffix}"
        path = package / "constants.py"
        u.Tests.write_lazy_init_namespace_module(
            path,
            class_name=owner,
            alias="c",
            extra_class_names=(f"{owner}Member",),
        )
        original = path.read_text(encoding="utf-8")
        nesting = c.Infra.SemanticCutoverPhase.CLASS_NESTING
        with infra.rope_workspace(root) as rope:
            planned = u.Infra.plan_semantic_cutover(
                nesting,
                rope_workspace=rope,
                sources={path: original},
            )
            tm.ok(planned)
            tm.that(len(planned.value), eq=1)
            tm.that(
                planned.value[0].changes,
                eq=(f"nested {owner}Member under {owner}",),
            )
            remaining = u.Infra.plan_semantic_cutover(
                nesting,
                rope_workspace=rope,
                sources={path: planned.value[0].updated_source},
            )
        tm.ok(remaining)
        tm.that(remaining.value, empty=True)
        tm.that(path.read_text(encoding="utf-8"), eq=original)

    @staticmethod
    def test_nesting_reports_every_module_without_an_owner_as_a_failure(
        tmp_path: Path,
    ) -> None:
        """Rival stem-carrying classes leave the owner undecidable: the plan fails."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = package / "models.py"
        stem = (
            f"{u.derive_class_stem(root.name)}"
            f"{u.Infra.facade_family_declared_by(c.Infra.MODELS_PY).suffix}"
        )
        source = (
            f"class {stem}FirstCandidate:\n    pass\n\n"
            f"class {stem}SecondCandidate:\n    pass\n\n"
            f'__all__ = ["{stem}FirstCandidate", "{stem}SecondCandidate"]\n'
        )
        path.write_text(source, encoding="utf-8")
        with infra.rope_workspace(root) as rope:
            planned = u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CLASS_NESTING,
                rope_workspace=rope,
                sources={path: source},
            )
        tm.fail(planned, has="requires exactly one declared module owner")
