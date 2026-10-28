"""Logging ownership transfer evidence for staged semantic cutovers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

from typing import TYPE_CHECKING

import pytest

from flext_infra import infra
from flext_infra.codemod import FlextInfraCodemodSemanticApply
from flext_infra.workspace import FlextInfraRopeWorkspace
from tests import c, m, r, t, tm, u

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraSemanticLoggingTransfer:
    """Native receivers, old owners and generated exports cut over together."""

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
        root, package = (
            TestsFlextInfraSemanticLoggingTransfer._prepare_logging_transfer(
                tmp_path, case
            )
        )
        legacy = package / "services" / "logging_integration.py"
        report: m.Infra.ModOccurrenceReport[m.Infra.ModOccurrence] = (
            m.Infra.ModOccurrenceReport(
                files=frozenset({package / "logging_consumer.py"}), entries=()
            )
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
                TestsFlextInfraSemanticLoggingTransfer._plan_logging_source_drift(
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
                    workspace_factory=infra.rope_workspace,
                )
        else:
            TestsFlextInfraSemanticLoggingTransfer._publish_logging_transfer(
                root, package, report
            )
            return
        for path, contents in original.items():
            tm.that(path.read_bytes(), eq=contents)

    @staticmethod
    def _prepare_logging_transfer(
        tmp_path: t.Infra.RopeSourcePath, case: str
    ) -> tuple[Path, Path]:
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
        TestsFlextInfraSemanticLoggingTransfer._write_logging_sources(
            package, namespace, owner, domain, case
        )
        TestsFlextInfraSemanticLoggingTransfer._write_logging_recipe(
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
            "-> tuple[str, bool]:\n"
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
            "-> tuple[str, bool]:\n"
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
            "evidence: tuple[str, tuple[str, bool]] = (\n"
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
            u.Infra.facade_source_project(root) as (project, _sources),
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
                    workspace_factory=infra.rope_workspace,
                )
            )
        tm.fail(changed_again)
        TestsFlextInfraSemanticLoggingTransfer._verify_logging_consumer(
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
