"""Real-source regression evidence for staged semantic cutovers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import importlib.util
import sys
from typing import TYPE_CHECKING

import pytest

from flext_infra import infra
from flext_infra.codemod import FlextInfraCodemodSemanticApply
from flext_infra.workspace import FlextInfraRopeWorkspace
from tests import c, m, r, t, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraSemanticPhaseContract:
    """Require planned and published sources to reach the same fixed point."""

    @staticmethod
    @pytest.mark.parametrize(
        "case",
        [
            "complete",
            "marker",
            "dynamic",
            "member-alias",
            "signature",
            "external",
            "unused-import",
            "module-marker",
            "opaque",
            "source-drift",
            "call-carrier",
            "subscript-carrier",
            "shared-export-line",
            "chained-exports",
            "mixed-exports",
        ],
    )
    def test_logging_ownership_transfer_uses_the_real_mod_publication_group(
        tmp_path: t.Infra.RopeSourcePath, case: str
    ) -> None:
        """Native receivers, old owners and generated exports cut over together."""
        root, package = TestsFlextInfraSemanticPhaseContract._prepare_logging_transfer(
            tmp_path, case
        )
        legacy = package / "services" / "logging_integration.py"
        report = m.Infra.ModOccurrenceReport[m.Infra.ModOccurrence](
            files=frozenset({package / "logging_consumer.py"}), entries=()
        )
        original = {
            path: path.read_bytes()
            for path in (
                legacy,
                package / "_utilities" / "domains.py",
                package / c.Infra.API_PY,
                package / "logging_consumer.py",
                root / c.Infra.CODEMOD_ROPE_CONTRACTS_RELPATH,
            )
        }
        if case == "source-drift":
            with pytest.raises(ValueError, match=r"source|directory|identity"):
                TestsFlextInfraSemanticPhaseContract._plan_logging_source_drift(
                    root, report, legacy, original[legacy]
                )
        elif case != "complete":
            messages = {
                "marker": "marker/dynamic",
                "dynamic": "marker/dynamic",
                "member-alias": "surviving native usage",
                "signature": "callable signature",
                "external": "outside its project|external library",
                "unused-import": "surviving imported alias",
                "module-marker": "surviving module usage",
                "opaque": "unproven transferred receiver",
                "call-carrier": "marker/dynamic",
                "subscript-carrier": "marker/dynamic",
                "shared-export-line": "shares a source line",
                "chained-exports": "literal __all__",
                "mixed-exports": "literal __all__|dynamic exports",
            }
            with (
                infra.rope_workspace(root) as workspace,
                pytest.raises(ValueError, match=messages[case]),
            ):
                FlextInfraCodemodSemanticApply.apply(
                    root,
                    report,
                    workspace,
                    source_preview=infra.source_preview(root),
                    workspace_factory=infra.rope_workspace,
                )
        else:
            TestsFlextInfraSemanticPhaseContract._publish_logging_transfer(
                root, package, report
            )
            return
        for path, contents in original.items():
            tm.that(path.read_bytes(), eq=contents)

    @staticmethod
    def _prepare_logging_transfer(
        tmp_path: t.Infra.RopeSourcePath, case: str
    ) -> t.Pair[Path, Path]:
        """Prepare real source owners and their generated publication baseline.

        Returns:
            The workspace root and declared package directory.

        """
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        layout = u.Infra.layout(root)
        if layout is None:
            pytest.fail("logging fixture must have a declared package layout")
        namespace, owner = layout.package_name, layout.class_stem
        domain = u.derive_class_stem(u.Infra.package_alias(package_name=namespace))
        TestsFlextInfraSemanticPhaseContract._write_logging_sources(
            package, namespace, owner, domain, case
        )
        TestsFlextInfraSemanticPhaseContract._write_logging_recipe(
            root, namespace, owner, domain, case
        )
        facade = package / c.Infra.UTILITIES_PY
        facade.write_text(
            f"class {owner}Utilities:\n"
            f"    class {domain}:\n"
            "        pass\n"
            f"u = {owner}Utilities\n"
            f"__all__ = ['{owner}Utilities', 'u']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        u.Tests.commit_git_changes(root, "Declare logging transfer sources")
        # Match the adapter worker's SOURCE-PREP without deleting legacy sources.
        tm.ok(u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)))
        rendered = u.Infra.render_utility_facade(package)
        if rendered is None:
            pytest.fail(
                "the logging utility owner must have a native facade projection"
            )
        before = tm.ok(u.Cli.atomic_read_binary_file_state(facade, required=True))
        tm.ok(
            u.Tests.materialize_codegen_plans(
                r.ok((
                    m.Infra.CodegenFilePlan(
                        project=root,
                        path=facade,
                        before=before,
                        desired_content=rendered.encode(c.DEFAULT_ENCODING),
                        desired_mode=before.mode,
                    ),
                ))
            )
        )
        tm.ok(u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)))
        if case in {"shared-export-line", "chained-exports", "mixed-exports"}:
            legacy = package / "services" / "logging_integration.py"
            legacy_name = f"{owner}Logging"
            unsafe_exports = (
                f"__all__ = [{legacy_name!r}]; side_effect()\n"
                if case == "shared-export-line"
                else (
                    f"PUBLIC = __all__ = [{legacy_name!r}]\n"
                    if case == "chained-exports"
                    else f"__all__ = [{legacy_name!r}, side_effect()]\n"
                )
            )
            legacy.write_text(
                legacy.read_text(encoding=c.DEFAULT_ENCODING).replace(
                    f"__all__ = [{legacy_name!r}]\n", unsafe_exports
                ),
                encoding=c.DEFAULT_ENCODING,
            )
        return root, package

    @staticmethod
    def _write_logging_sources(
        package: Path, namespace: str, owner: str, domain: str, case: str
    ) -> None:
        """Write the legacy owner, native provider and consumer counterexample."""
        legacy_name, utility_name = f"{owner}Logging", f"{owner}UtilitiesDomains"
        legacy = package / "services" / "logging_integration.py"
        provider = package / "_utilities" / "domains.py"
        api = package / c.Infra.API_PY
        consumer = package / "logging_consumer.py"
        for directory in (legacy.parent, provider.parent):
            directory.mkdir(parents=True, exist_ok=True)
        legacy.write_text(
            "from __future__ import annotations\n"
            f"class {legacy_name}:\n"
            "    class ContextStage:\n"
            "        def __call__(self, event: str) -> str:\n"
            "            return event\n"
            f"__all__ = [{legacy_name!r}]\n",
            encoding=c.DEFAULT_ENCODING,
        )
        api.write_text(
            "from __future__ import annotations\n"
            f"from {namespace} import t\n"
            f"from {namespace}.services.logging_integration import {legacy_name}\n"
            f"class {owner}({legacy_name}):\n"
            "    @staticmethod\n"
            "    def compose_logging(value: str, *, enabled: bool = True) "
            "-> t.Pair[str, bool]:\n"
            "        return value, enabled\n"
            "    def unrelated(self) -> str:\n"
            "        return 'other-domain'\n"
            f"__all__ = [{owner!r}]\n",
            encoding=c.DEFAULT_ENCODING,
        )
        default = "False" if case == "signature" else "True"
        provider.write_text(
            "from __future__ import annotations\n"
            f"from {namespace} import p, t\n"
            f"class {utility_name}:\n"
            "    class ContextStage:\n"
            "        def __init__(self, *, context: p.AttributeProbe) -> None:\n"
            "            self._context = context\n"
            "        def __call__(self, event: str) -> str:\n"
            "            return event\n"
            "    @staticmethod\n"
            f"    def compose_logging(value: str, *, enabled: bool = {default}) "
            "-> t.Pair[str, bool]:\n"
            "        return value, enabled\n"
            f"__all__ = [{utility_name!r}]\n",
            encoding=c.DEFAULT_ENCODING,
        )
        suffix = {
            "complete": "",
            "marker": "marker = hasattr(API, 'compose_logging')\n",
            "dynamic": "selected = 'ContextStage'\nmarker = getattr(API, selected)\n",
            "member-alias": "marker = API.ContextStage\n",
            "signature": "",
            "external": "",
            "unused-import": (
                f"from {namespace}.services.logging_integration "
                f"import {legacy_name} as Spare\n"
            ),
            "module-marker": (
                f"import {namespace}.services.logging_integration as legacy_module\n"
                "marker = legacy_module.__name__\n"
            ),
            "opaque": (
                "def unknown_owner(candidate):\n    return candidate.ContextStage()\n"
            ),
            "source-drift": "",
            "call-carrier": "marker = getattr(API(), 'ContextStage')\n",
            "subscript-carrier": "marker = getattr((API,)[0], 'compose_logging')\n",
            "shared-export-line": "",
            "chained-exports": "",
            "mixed-exports": "",
        }[case]
        consumer.write_text(
            "from __future__ import annotations\n"
            f"from {namespace}.api import {owner} as API\n"
            f"from {namespace} import t, u\n"
            "class Unrelated:\n"
            "    @staticmethod\n"
            "    def compose_logging(value: str) -> str:\n"
            "        return value\n"
            "instance = API()\n"
            f"direct = u.{domain}.ContextStage(context=API())\n"
            "configure = API.compose_logging\n"
            "evidence: t.Pair[str, t.Pair[str, bool]] = (\n"
            "    instance.ContextStage()('event'), configure('configured')\n"
            ")\n"
            "shadow = Unrelated.compose_logging('unrelated')\n"
            "HELP = 'compose_logging and ContextStage are documentation'\n" + suffix,
            encoding=c.DEFAULT_ENCODING,
        )

    @staticmethod
    def _write_logging_recipe(
        root: Path, namespace: str, owner: str, domain: str, case: str
    ) -> None:
        """Declare the paired native context and compose ownership transfers."""
        legacy_name, utility_name = f"{owner}Logging", f"{owner}UtilitiesDomains"
        recipe = root / c.Infra.CODEMOD_ROPE_CONTRACTS_RELPATH
        recipe.parent.mkdir(parents=True, exist_ok=True)
        context_owner = (
            ("logging", "getLogger")
            if case == "external"
            else (
                f"{namespace}.services.logging_integration",
                f"{legacy_name}.ContextStage",
            )
        )
        rules = m.Infra.RopeContractRules(
            rules=(
                m.Infra.RopeContractRule(
                    id="logging-context-owner",
                    pattern="${receiver}.ContextStage()",
                    goal=f"u.{domain}.ContextStage(context=${{receiver}})",
                    arguments={"receiver": f"name={namespace}.api.{owner}"},
                    imports={"u": f"from {namespace} import u"},
                    bindings={
                        f"u.{domain}.ContextStage": (
                            f"{namespace}._utilities.domains.{utility_name}.ContextStage"
                        )
                    },
                    ownership_transfer=context_owner,
                ),
                m.Infra.RopeContractRule(
                    id="logging-compose-owner",
                    pattern="${receiver}.compose_logging",
                    goal=f"u.{domain}.compose_logging",
                    arguments={"receiver": f"name={namespace}.api.{owner}"},
                    imports={"u": f"from {namespace} import u"},
                    bindings={
                        f"u.{domain}.compose_logging": (
                            f"{namespace}._utilities.domains.{utility_name}.compose_logging"
                        )
                    },
                    ownership_transfer=(f"{namespace}.api", f"{owner}.compose_logging"),
                ),
            )
        )
        tm.ok(u.Cli.yaml_dump(recipe, rules.model_dump(mode="json")))

    @staticmethod
    def _plan_logging_source_drift(
        root: Path,
        report: m.Infra.ModOccurrenceReport[m.Infra.ModOccurrence],
        legacy: Path,
        original: bytes,
    ) -> None:
        """Replace a planned source inode without changing its bytes."""
        with (
            u.Infra.facade_source_project(root) as (project, _consumed, _sources),
            FlextInfraRopeWorkspace.open_workspace(
                root, source_project=project
            ) as workspace,
        ):
            inventory = FlextInfraCodemodSemanticApply.source_inventory(
                root, report, source_project=project
            )
            tm.ok(
                FlextInfraCodemodSemanticApply.plan(root, report, workspace, inventory)
            )
            replacement = legacy.with_suffix(".replacement")
            replacement.write_bytes(original)
            replacement.replace(legacy)

    @staticmethod
    def _publish_logging_transfer(
        root: Path,
        package: Path,
        report: m.Infra.ModOccurrenceReport[m.Infra.ModOccurrence],
    ) -> None:
        """Publish the cutover and prove idempotence and consumer behavior."""
        legacy = package / "services" / "logging_integration.py"
        provider = package / "_utilities" / "domains.py"
        api = package / c.Infra.API_PY
        consumer = package / "logging_consumer.py"
        service_init = legacy.parent / c.Infra.INIT_PY
        layout = tm.not_none(u.Infra.layout(root))
        namespace, owner = layout.package_name, layout.class_stem
        legacy_name = f"{owner}Logging"
        tm.ok(u.Tests.provision_python_project_environment(root))
        with infra.rope_workspace(root) as workspace:
            inventory = FlextInfraCodemodSemanticApply.source_inventory(root, report)
            transferred = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.CONTRACT_NORMALIZATION,
                    rope_workspace=workspace,
                    sources=inventory,
                )
            )
            carrier = next(edit for edit in transferred if edit.file_path == provider)
            tm.that(carrier.original_source, eq=carrier.updated_source)
            composed = tm.ok(
                FlextInfraCodemodSemanticApply.plan(root, report, workspace, inventory)
            )
            tm.ok(provider in {edit.file_path for edit in composed})
            tm.that(
                api in {edit.file_path for edit in composed if edit.retire_file},
                eq=False,
            )
            tm.ok(
                FlextInfraCodemodSemanticApply.apply(
                    root,
                    report,
                    workspace,
                    source_preview=infra.source_preview(root),
                    workspace_factory=infra.rope_workspace,
                )
            )
        tm.fail(legacy.exists())
        tm.that(
            "def compose_logging" in api.read_text(encoding=c.DEFAULT_ENCODING),
            eq=False,
        )
        tm.fail(legacy_name in api.read_text(encoding=c.DEFAULT_ENCODING))
        if service_init.exists():
            tm.that(
                legacy_name in service_init.read_text(encoding=c.DEFAULT_ENCODING),
                eq=False,
            )
        tm.that(
            consumer.read_text(encoding=c.DEFAULT_ENCODING),
            has="compose_logging and ContextStage are documentation",
        )
        with infra.rope_workspace(root) as workspace:
            changed_again = tm.ok(
                FlextInfraCodemodSemanticApply.apply(
                    root,
                    report,
                    workspace,
                    source_preview=infra.source_preview(root),
                    workspace_factory=infra.rope_workspace,
                )
            )
        tm.fail(changed_again)
        TestsFlextInfraSemanticPhaseContract._verify_logging_consumer(
            root, namespace, owner
        )
        tm.fail(legacy.exists())

    @staticmethod
    def _verify_logging_consumer(root: Path, namespace: str, owner: str) -> None:
        """Execute the published consumer and detect surviving legacy owners."""
        probe = root / "verify_logging_cutover.py"
        probe.write_text(
            f"from {namespace}.api import {owner} as API\n"
            f"from {namespace}.logging_consumer import evidence, shadow\n"
            "if evidence != ('event', ('configured', True)) or shadow != 'unrelated':\n"
            "    raise RuntimeError('logging consumer changed behavior')\n"
            "if API().unrelated() != 'other-domain':\n"
            "    raise RuntimeError('an unrelated domain changed')\n"
            "if hasattr(API, 'ContextStage') or hasattr(API, 'compose_logging'):\n"
            "    raise RuntimeError("
            "'old logging owners remain as compatibility stubs')\n",
            encoding=c.DEFAULT_ENCODING,
        )
        outcome = tm.ok(
            u.Cli.run_raw((str(u.Infra.runtime_python(root)), str(probe)), cwd=root)
        )
        tm.that(outcome.outcome.raw_return_code, eq=0, msg=outcome.stderr)

    @staticmethod
    def test_utility_factory_preserves_public_empty_roundtrips(
        tmp_path: Path,
    ) -> None:
        """Utility-owned factories preserve model defaults and JSON round-trips."""
        consumer = tmp_path / "declaration_factory_consumer.py"
        consumer.write_text(
            "from flext_core import m, t, u\n"
            "from typing_extensions import TypeForm\n"
            "type Bag[T] = t.MutableSequenceOf[T]\n"
            "class Consumer(m.ContractModel):\n"
            "    values: Bag[str] = m.Field(default_factory=u.empty("
            'TypeForm(Bag[str])), description="Consumer values")\n'
            "def verify():\n"
            "    first, second = Consumer(), Consumer()\n"
            "    explicit = Consumer.model_validate_json('{\"values\": []}')\n"
            "    first.values.append('consumer value')\n"
            "    assert second.model_dump_json() == explicit.model_dump_json()\n"
            "    restored = Consumer.model_validate_json(first.model_dump_json())\n"
            "    assert restored.values == first.values\n"
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
        tm.that(tm.ok(u.Cli.env_read("FIELD", {"FIELD": "value"})), eq="value")
        tm.fail(hasattr(u, "Cli"))
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
                "from flext_core import u\n"
                "class FlextReviewedBase(u):\n"
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
                "def first():\n    return t.scalar_mapping_adapter()\n"
                "def second():\n    return t.json_dict_adapter()\n"
            ),
            "pending module imports": (
                "from flext_core import t as core_t\n"
                "from flext_cli import t as cli_t\n"
                "first = t.scalar_mapping_adapter()\n"
                "second = t.json_dict_adapter()\n"
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
    @pytest.mark.parametrize(
        "variant", [c.MergeStrategy.OVERRIDE, "diamond", "static-internal"]
    )
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
    @pytest.mark.parametrize("binding", ["inherited", c.MergeStrategy.OVERRIDE, "mask"])
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
            if binding == c.MergeStrategy.OVERRIDE
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
                tm.fail("from flext_cli import u" in updated)
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
            tm.fail(contextual.name in sys.modules)
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
        *,
        inherited_import: bool,
    ) -> None:
        """Repeated typing references relocate while the real utility runs."""
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
                f"value = {typing_owner}.parse({typing_owner}.parse('aligned'))\n"
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
                f"value = {typing_owner}.parse({typing_owner}.parse('aligned'))\n"
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
        shadowed = "def local(core_c):\n    return c.PRIMITIVES_TYPES\n"
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
                "upstream = c.PRIMITIVES_TYPES\n"
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
            tm.fail(upstream_import in updated)
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
                "value = c.PRIMITIVES_TYPES\n"
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
        with (
            infra.rope_workspace(root) as rope,
            pytest.raises(ValueError, match=case) as raised,
        ):
            u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CONSTANT_CONSUMERS,
                rope_workspace=rope,
                sources=sources,
            )
        tm.that(str(raised.value), has="flext_upstream.c")
        for path, source in sources.items():
            tm.that(path.read_text(encoding="utf-8"), eq=source)

    @staticmethod
    @pytest.mark.parametrize("alias", ["c", "constants"])
    @pytest.mark.parametrize("guarded", [False, True])
    def test_nonprefixed_constants_qualify_public_owners_without_value_dedupe(
        tmp_path: Path, alias: str, *, guarded: bool
    ) -> None:
        """Published project owners preserve SDK ancestry, domains and lexical scope."""
        root, package = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="signal-hub", package_name="signal_hub"
        )
        family = package / "_constants"
        family.mkdir()
        consumer = package / "consumer.py"
        private = package / "private_consumer.py"
        declaration = f"from {package.name} import c"
        if alias != "c":
            declaration += f" as {alias}"
        sources = {
            family / "base.py": (
                "from enum import StrEnum\n"
                "class SignalConstantsBase:\n"
                "    TOKEN = 'shared-domain-value'\n"
                "    EXISTING = 'nested-domain-value'\n"
                "    class Mode(StrEnum):\n"
                "        READY = 'ready'\n"
            ),
            family / "other.py": (
                "from enum import StrEnum\n"
                "class SignalConstantsOther:\n"
                "    OTHER_TOKEN = 'shared-domain-value'\n"
                "    class OtherMode(StrEnum):\n"
                "        READY = 'ready'\n"
            ),
            package / c.Infra.CONSTANTS_PY: (
                "from flext_infra import c as upstream\n"
                f"from {package.name}._constants.base import SignalConstantsBase\n"
                f"from {package.name}._constants.other import SignalConstantsOther\n"
                "class SignalHubConstants(upstream):\n"
                "    class SignalHub:\n"
                "        EXISTING = 'published-flat-value'\n"
                "        Base = SignalConstantsBase\n"
                "        Other = SignalConstantsOther\n"
                "c = SignalHubConstants\n"
                "__all__ = ['SignalHubConstants', 'c']\n"
            ),
            package / c.Infra.INIT_PY: "from .constants import c\n__all__ = ['c']\n",
            consumer: (
                '"""c.SignalHub.TOKEN remains documentation."""\n'
                "from __future__ import annotations\n"
                "from pathlib import Path\n"
                "from typing import TYPE_CHECKING\n"
                + (
                    f"if TYPE_CHECKING:\n    {declaration}\n"
                    if guarded
                    else f"{declaration}\n"
                )
                + f"def accept(value: {alias}.SignalHub.Mode):\n    return value\n"
                + (
                    ""
                    if guarded
                    else (
                        f"value = {alias}.SignalHub.Mode.READY\n"
                        f"published = {alias}.SignalHub.Base.Mode.READY\n"
                        f"flat = {alias}.SignalHub.EXISTING\n"
                        f"other = {alias}.SignalHub.OtherMode.READY\n"
                        f"token = {alias}.SignalHub.TOKEN\n"
                        f"other_token = {alias}.SignalHub.OTHER_TOKEN\n"
                        f"sdk = {alias}.Cli.FILE_FORMAT_JSON\n"
                        f"infra = {alias}.Infra.GIT_OID_HEX_LENGTH_SHA1\n"
                        f"core = {alias}.PRIMITIVES_TYPES\n"
                    )
                )
                + f"note = '{alias}.SignalHub.TOKEN'\n"
                + "location = Path(__file__).name\n"
                + f"# {alias}.SignalHub.TOKEN is not an executable reference.\n"
                + f"def shadow({alias}):\n    return {alias}.SignalHub.TOKEN\n"
            ),
            private: (
                "from __future__ import annotations\n"
                "from flext_infra import c\n"
                f"from {package.name}._constants.base import "
                "SignalConstantsBase as Internal\n"
                "value = Internal.Mode.READY\n"
                "def accept(value: Internal):\n    return value\n"
                "sdk = c.Cli.FILE_FORMAT_JSON\n"
            ),
        }
        for path, source in sources.items():
            path.write_text(source, encoding=c.DEFAULT_ENCODING)
        originals = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            for path in sources
        )
        phase = c.Infra.SemanticCutoverPhase.CONSTANT_CONSUMERS
        with infra.rope_workspace(root) as rope:
            edits = tm.ok(
                u.Infra.plan_semantic_cutover(
                    phase, rope_workspace=rope, sources=sources
                )
            )
        tm.that({edit.file_path for edit in edits}, eq={consumer, private})
        tm.ok(u.Cli.atomic_verify_binary_file_states(originals))
        proposed = {
            **sources,
            **{edit.file_path: edit.updated_source for edit in edits},
        }
        for edit in edits:
            tm.ok(u.Cli.atomic_write_text_file(edit.file_path, edit.updated_source))
        with infra.rope_workspace(root) as rope:
            tm.that(
                tm.ok(
                    u.Infra.plan_semantic_cutover(
                        phase, rope_workspace=rope, sources=proposed
                    )
                ),
                empty=True,
            )
        probe = (
            "from typing import get_type_hints\n"
            f"from {package.name} import c, consumer, private_consumer\n"
            "from flext_infra import c as sdk\n"
            "class Local:\n    class SignalHub:\n        TOKEN = 'local'\n"
            "assert consumer.shadow(Local) == 'local'\n"
            f"assert consumer.location == {consumer.name!r}\n"
            f"assert consumer.note == '{alias}.SignalHub.TOKEN'\n"
            "assert consumer.__doc__ == 'c.SignalHub.TOKEN remains documentation.'\n"
            f"namespace = {{**vars(consumer), '{alias}': c}}\n"
            "assert get_type_hints(consumer.accept, globalns=namespace)['value'] "
            "is c.SignalHub.Base.Mode\n"
            "assert private_consumer.value is c.SignalHub.Base.Mode.READY\n"
            "assert get_type_hints(private_consumer.accept)['value'] "
            "is c.SignalHub.Base\n"
            "assert private_consumer.sdk == sdk.Cli.FILE_FORMAT_JSON\n"
        )
        if not guarded:
            probe += (
                "assert consumer.value is c.SignalHub.Base.Mode.READY\n"
                "assert consumer.published is c.SignalHub.Base.Mode.READY\n"
                "assert consumer.flat == c.SignalHub.EXISTING\n"
                "assert consumer.flat != c.SignalHub.Base.EXISTING\n"
                "assert consumer.other is c.SignalHub.Other.OtherMode.READY\n"
                "assert consumer.value == consumer.other\n"
                "assert type(consumer.value) is not type(consumer.other)\n"
                "assert consumer.token == c.SignalHub.Base.TOKEN\n"
                "assert consumer.other_token == c.SignalHub.Other.OTHER_TOKEN\n"
                "assert consumer.sdk == sdk.Cli.FILE_FORMAT_JSON\n"
                "assert consumer.infra == sdk.Infra.GIT_OID_HEX_LENGTH_SHA1\n"
                "assert consumer.core is sdk.PRIMITIVES_TYPES\n"
            )
        output = tm.ok(
            u.Cli.run_raw(
                (sys.executable, "-c", probe),
                cwd=root,
                options=m.Cli.ProcessOptions(
                    env={c.Infra.ORCHESTRATOR_ENV_PYTHONPATH: str(package.parent)}
                ),
            )
        )
        tm.that(u.Cli.process_succeeded(output.outcome), eq=True, msg=output.stderr)
        tm.that(
            consumer.read_text(encoding=c.DEFAULT_ENCODING),
            has=f"# {alias}.SignalHub.TOKEN is not an executable reference.",
        )

    @staticmethod
    @pytest.mark.parametrize(
        "case", ["same-value", "different-value", "identity-depth"]
    )
    def test_nonprefixed_constants_reject_competing_publications_before_writes(
        tmp_path: Path, case: str
    ) -> None:
        """Neither equal values nor a shorter path elect a competing public owner."""
        root, package = u.Tests.create_lazy_init_workspace(
            tmp_path, project_name="signal-hub", package_name="signal_hub"
        )
        family = package / "_constants"
        family.mkdir()
        sources = {
            family / "base.py": "class Chosen:\n    TOKEN = 'domain-value'\n",
            package / c.Infra.INIT_PY: "from .constants import c\n__all__ = ['c']\n",
            package / c.Infra.CONSTANTS_PY: (
                f"from {package.name}._constants.base import Chosen\n"
                "class SignalHubConstants:\n"
                "    class SignalHub:\n"
                "        Base = Chosen\n"
                + (
                    "        class Nested:\n            Published = Chosen\n"
                    if case == "identity-depth"
                    else (
                        "        class Other:\n"
                        "            TOKEN = "
                        + ("'domain-value'\n" if case == "same-value" else "'other'\n")
                    )
                )
                + "c = SignalHubConstants\n__all__ = ['SignalHubConstants', 'c']\n"
            ),
            package / "consumer.py": (
                f"from {package.name}._constants.base import Chosen\n"
                "value = Chosen.TOKEN\n"
                if case == "identity-depth"
                else f"from {package.name} import c\nvalue = c.SignalHub.TOKEN\n"
            ),
        }
        for path, source in sources.items():
            path.write_text(source, encoding=c.DEFAULT_ENCODING)
        originals = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            for path in sources
        )
        with (
            infra.rope_workspace(root) as rope,
            pytest.raises(ValueError, match="ambiguous public owners"),
        ):
            u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.CONSTANT_CONSUMERS,
                rope_workspace=rope,
                sources=sources,
            )
        tm.ok(u.Cli.atomic_verify_binary_file_states(originals))

    @staticmethod
    def test_annotations_and_nesting_complete_in_one_atomic_cutover(
        tmp_path: Path,
    ) -> None:
        """Test annotations and nesting complete in one atomic cutover."""
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
        tm.ok(u.Tests.provision_python_project_environment(root))
        source = path.read_text(encoding="utf-8").replace(
            "from __future__ import annotations\n",
            "",
        )
        path.write_text(source, encoding="utf-8")
        finding = m.Infra.ModOccurrence(
            rule_file="require-future-annotations.yml",
            rule_id="require-future-annotations",
            repository=root.name,
            file=path.relative_to(root),
            range={},
            text=source,
            actionable=False,
            classification=c.Infra.ModScanFindingClass.DETECTION_ONLY,
        )
        report = m.Infra.ModOccurrenceReport(
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
