"""Import-law engine: scoped bindings, hoisting, and provider identity contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest

from flext_infra import m
from flext_infra.codemod import FlextInfraImportNormalizationPhase
from tests import c, tm, u
from tests.unit.refactor.import_normalization_support import (
    TestsFlextInfraRefactorImportNormalizationSupport,
)

if TYPE_CHECKING:
    from pathlib import Path


class TestsFlextInfraRefactorImportNormalizationBindings(
    TestsFlextInfraRefactorImportNormalizationSupport,
):
    """Binding, hoisting, and provider rules observed through ``normalize_source``."""

    @classmethod
    def test_nested_config_models_are_family_sources_not_layer_zero(
        cls, tmp_path: Path
    ) -> None:
        """Domain config MRO assembly remains valid source for generated facets."""
        project, package = cls._project(tmp_path)
        family = u.Infra.facade_families()["m"]
        module = package / family.directory / "_config" / "base.py"
        source = (
            f"from demo_pkg.{family.directory}._config.part import ConfigPart\n"
            "class ConfigModels(ConfigPart):\n    pass\n"
            "__all__ = ['ConfigModels']\n"
        )
        tm.that(
            u.Infra.import_module_role("demo_pkg._models._config.base"), eq="family"
        )
        tm.that(
            u.Infra.normalize_import_source(
                project_root=project, file_path=module, source=source
            ),
            eq=None,
        )

    @classmethod
    @pytest.mark.parametrize("letter", sorted(u.Infra.facade_families()))
    def test_missing_reverse_runtime_letter_is_not_synthesized(
        cls, tmp_path: Path, letter: str
    ) -> None:
        """A missing higher own alias is a defect, never a new runtime edge."""
        project, package = cls._project(tmp_path)
        families = u.Infra.facade_families()
        higher = [
            name
            for name, family in families.items()
            if u.Infra.module_import_layer(f"demo_pkg.{family.module}")
            > u.Infra.module_import_layer(f"demo_pkg.{families[letter].module}")
        ]
        cls._lazy_init(
            package, {name: f".{family.module}" for name, family in families.items()}
        )
        for name in higher:
            with pytest.raises(ValueError, match="forbidden reverse namespace import"):
                u.Infra.normalize_import_source(
                    project_root=project,
                    file_path=package / families[letter].directory / "declaration.py",
                    source=f"value = {name}.Value\n",
                )
            module = package / families[letter].directory / "annotations.py"
            normalized = cls._normalize(
                project,
                module,
                "from __future__ import annotations\n"
                f"def describe(value: {name}.Value) -> str:\n    return 'value'\n",
            )
            tm.that(
                normalized,
                has=f"if TYPE_CHECKING:\n    from demo_pkg import {name}\n",
            )
            tm.that(
                u.Infra.normalize_import_source(
                    project_root=project, file_path=module, source=normalized
                ),
                eq=None,
            )

    @classmethod
    def test_internal_tier_alias_binds_through_tier_root(cls, tmp_path: Path) -> None:
        """An internal tier imports root aliases from its own root."""
        project, _ = cls._project(tmp_path)
        tier = project / "tests"
        cls._lazy_init(tier, {"r": "flext_tests", "c": ".constants"})
        normalized = cls._normalize(
            project,
            tier / "unit" / "test_demo.py",
            "from __future__ import annotations\n"
            "\n"
            "from demo_pkg import c\n"
            "from flext_tests import r\n"
            "\n"
            "\n"
            "def test_demo() -> None:\n"
            "    assert r.ok(c)\n",
        )

        tm.that(normalized, has="from tests import c, r\n")
        tm.that(normalized, has="from tests import c, r, t\n")

    @classmethod
    def test_relative_import_becomes_absolute(cls, tmp_path: Path) -> None:
        """A service consumes its helper through the absolute lazy package."""
        project, package = cls._project(tmp_path)
        (package / "_utilities" / "helper.py").write_text(
            "class DemoHelper:\n"
            "    @staticmethod\n"
            "    def read(value):\n        return value\n"
            "__all__ = ['DemoHelper']\n",
            encoding="utf-8",
        )
        cls._lazy_init(package / "services", {"run": ".worker"})
        target = package / "services" / "worker.py"
        normalized = cls._normalize(
            project,
            target,
            "from __future__ import annotations\n"
            "\n"
            "from .._utilities.helper import DemoHelper\n"
            "\n"
            "\n"
            "def run() -> str:\n"
            "    return DemoHelper.read('lazy-value')\n"
            "__all__ = ['run']\n",
        )
        target.write_text(normalized, encoding="utf-8")
        result = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-c",
                    "from demo_pkg.services import run; print(run())",
                ),
                cwd=project,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            ),
        )
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True, msg=result.stderr)
        tm.that(result.stdout.strip(), eq="lazy-value")
        tm.that(
            u.Infra.normalize_import_source(
                project_root=project,
                file_path=target,
                source=normalized,
            ),
            eq=None,
        )

    @classmethod
    def test_import_guard_becomes_plain_import(cls, tmp_path: Path) -> None:
        """A ``try/except ImportError`` guard becomes its plain imports."""
        project, package = cls._project(tmp_path)
        normalized = cls._normalize(
            project,
            package / "services" / "worker.py",
            "from __future__ import annotations\n"
            "\n"
            "try:\n"
            "    import json\n"
            "except ImportError:\n"
            "    json = None\n"
            "\n"
            "\n"
            "def run() -> str:\n"
            "    return json.dumps({})\n",
        )

        tm.that(normalized, lacks="except ImportError")
        tm.that(normalized, has="\nimport json\n")

    @classmethod
    def test_normalization_is_idempotent(cls, tmp_path: Path) -> None:
        """A second pass over the normalized module changes nothing."""
        project, package = cls._project(tmp_path)
        target = package / "services" / "worker.py"
        first = cls._normalize(
            project,
            target,
            "from __future__ import annotations\n"
            "\n"
            "from flext_core import r\n"
            "\n"
            "\n"
            "def run() -> object:\n"
            "    from demo_pkg._models.record import DemoRecord\n"
            "\n"
            "    return r.ok(DemoRecord)\n",
        )

        second = u.Infra.normalize_import_source(
            project_root=project,
            file_path=target,
            source=first,
        )

        tm.that(second, eq=None)

    @classmethod
    def test_unbound_tier_letters_bind_through_tier_root(
        cls,
        tmp_path: Path,
    ) -> None:
        """A test module reading unbound tier letters imports them from its root."""
        project, _ = cls._project(tmp_path)
        tier = project / "tests"
        cls._lazy_init(tier, {"c": ".constants", "u": ".utilities"})
        target = tier / "unit" / "test_demo.py"
        normalized = cls._normalize(
            project,
            target,
            '"""Demo tests."""\n'
            "\n"
            "from __future__ import annotations\n"
            "\n"
            "\n"
            "def test_demo(value: int) -> None:\n"
            "    assert u.Demo.run(c.Demo.NAME, value)\n",
        )

        tm.that(normalized, has="from tests import c, r, u\n")
        tm.that(
            u.Infra.normalize_import_source(
                project_root=project,
                file_path=target,
                source=normalized,
            ),
            eq=None,
        )

    @classmethod
    def test_locally_bound_letter_is_not_imported(cls, tmp_path: Path) -> None:
        """A letter the module binds itself is never imported from its root."""
        project, _ = cls._project(tmp_path)
        tier = project / "tests"
        cls._lazy_init(tier, {"c": ".constants"})
        result = u.Infra.normalize_import_source(
            project_root=project,
            file_path=tier / "unit" / "test_demo.py",
            source=(
                "from __future__ import annotations\n"
                "\n"
                "\n"
                "def test_demo(c: int) -> None:\n"
                "    assert c\n"
            ),
        )

        tm.that(result, eq=None)

    @classmethod
    def test_tier_owner_drops_import_of_its_own_definition(
        cls,
        tmp_path: Path,
    ) -> None:
        """A tier facade module never imports the alias it defines from its root."""
        project, _ = cls._project(tmp_path)
        tier = project / "tests"
        cls._lazy_init(tier, {"c": ".constants"})
        target = tier / "constants.py"
        normalized = cls._normalize(
            project,
            target,
            "from __future__ import annotations\n"
            "\n"
            "from tests import c, r\n"
            "\n"
            "\n"
            "class TestsDemoConstants:\n"
            "    NAME = 'tier-value'\n"
            "\n"
            "\n"
            "c = TestsDemoConstants\n"
            "__all__ = ['TestsDemoConstants', 'c']\n",
        )
        target.write_text(normalized, encoding="utf-8")
        result = tm.ok(
            u.Cli.run(
                (sys.executable, "-c", "from tests import c, r; print(c.NAME)"),
                cwd=project,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(project)}),
            ),
        )
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True, msg=result.stderr)
        tm.that(result.stdout.strip(), eq="tier-value")
        tm.that(
            u.Infra.normalize_import_source(
                project_root=project,
                file_path=target,
                source=normalized,
            ),
            eq=None,
        )

    @classmethod
    def test_distinct_inline_providers_fail_before_consumer_publication(
        cls,
        tmp_path: Path,
    ) -> None:
        """Reject conflicting inline providers through the native publisher caller."""
        u.Tests.run_native_callable(cls.scenario_distinct_providers, tmp_path)

    @classmethod
    def scenario_distinct_providers(
        cls,
        tmp_path: Path,
    ) -> None:
        """Refuse a global binding that would change two real local consumers."""
        project, package = cls._project(tmp_path)
        for provider, value in (
            ("first_provider", "first provider"),
            ("second_provider", "second provider"),
        ):
            (package.parent / f"{provider}.py").write_text(
                f"def value() -> str:\n    return {value!r}\n",
                encoding="utf-8",
            )
        consumer = package / "consumer.py"
        consumer.write_text(
            "def first() -> str:\n"
            "    from first_provider import value\n"
            "    return value()\n\n"
            "def second() -> str:\n"
            "    from second_provider import value\n"
            "    return value()\n",
            encoding="utf-8",
        )
        command = (
            sys.executable,
            "-c",
            "from demo_pkg.consumer import first, second; print(first(), second())",
        )
        options = m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)})
        before = tm.ok(u.Cli.run(command, cwd=project, options=options))
        tm.that(u.Cli.process_succeeded(before.outcome), eq=True, msg=before.stderr)
        tm.that(before.stdout.strip(), eq="first provider second provider")
        with pytest.raises(ValueError, match="conflicting inline import providers"):
            FlextInfraImportNormalizationPhase.apply_files(project, (consumer,))
        after = tm.ok(u.Cli.run(command, cwd=project, options=options))
        tm.that(u.Cli.process_succeeded(after.outcome), eq=True, msg=after.stderr)
        tm.that(after.stdout, eq=before.stdout)

    @classmethod
    @pytest.mark.parametrize(
        ("source", "expected"),
        [
            (
                (
                    "def read_failure() -> str:\n"
                    "    try:\n"
                    "        raise ValueError('handler failure')\n"
                    "    except ValueError as e:\n"
                    "        return str(e)\n"
                    "\n"
                    "print(read_failure())\n"
                ),
                "handler failure",
            ),
            (
                "match 'pattern value':\n    case str() as s:\n        print(s)\n",
                "pattern value",
            ),
            (
                "match ['pattern value']:\n    case [*s]:\n        print(s[0])\n",
                "pattern value",
            ),
            (
                (
                    "match {'value': 'pattern value'}:\n"
                    "    case {**s}:\n"
                    "        print(s['value'])\n"
                ),
                "pattern value",
            ),
        ],
    )
    def test_local_bindings_do_not_load_a_facade_provider(
        cls,
        tmp_path: Path,
        source: str,
        expected: str,
    ) -> None:
        """Exception and pattern bindings execute without a facade dependency."""
        project, package = cls._project(tmp_path)
        cls._lazy_init(
            package,
            {"e": ".unavailable_provider", "s": ".unavailable_provider"},
        )
        module = package / "handler.py"
        normalized = u.Infra.normalize_import_source(
            project_root=project,
            file_path=module,
            source=source,
        )
        module.write_text(
            normalized if normalized is not None else source,
            encoding="utf-8",
        )
        result = tm.ok(
            u.Cli.run(
                (sys.executable, str(module)),
                cwd=project,
            ),
        )
        tm.ok(u.Cli.process_succeeded(result.outcome))
        tm.that(result.stdout.strip(), eq=expected)
        tm.that(
            u.Infra.normalize_import_source(
                project_root=project,
                file_path=module,
                source=module.read_text(encoding="utf-8"),
            ),
            eq=None,
        )

    @classmethod
    @pytest.mark.parametrize(
        "module_name",
        ["_config", "_settings", "_models/provider"],
    )
    def test_declarations_keep_external_providers(
        cls,
        tmp_path: Path,
        module_name: str,
    ) -> None:
        """Authored declarations instantiate through their real external provider."""
        project, package = cls._project(tmp_path)
        module = package / f"{module_name}.py"
        source = (
            "from flext_core import m\n\n"
            "class DemoConfig(m.BaseModel):\n"
            "    value: str\n\n"
            "print(DemoConfig(value='validated-value').value)\n"
        )
        normalized = u.Infra.normalize_import_source(
            project_root=project,
            file_path=module,
            source=source,
        )
        module.write_text(
            normalized if normalized is not None else source,
            encoding="utf-8",
        )
        outcome = tm.ok(
            u.Cli.run(
                (sys.executable, str(module)),
                cwd=project,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            ),
        )
        tm.ok(u.Cli.process_succeeded(outcome.outcome))
        tm.that(outcome.stdout.strip(), eq="validated-value")
        tm.that(
            u.Infra.normalize_import_source(
                project_root=project,
                file_path=module,
                source=module.read_text(encoding="utf-8"),
            ),
            eq=None,
        )

    @classmethod
    @pytest.mark.parametrize(
        "consumer",
        [
            "def consume():\n    return s()\n",
            "def consume(s=s()):\n    return s\n",
            (
                "@(lambda value: lambda function: function)(s())\n"
                "def consume():\n    return s()\n"
            ),
            "VALUES = [s for s in [s()]]\ndef consume():\n    return VALUES[0]\n",
            "def consume():\n    return [s for s in [s()]][0]\n",
        ],
    )
    @pytest.mark.parametrize(
        "local_body",
        [
            (
                "    try:\n"
                "        raise ValueError('local-value')\n"
                "    except ValueError as s:\n"
                "        return str(s)\n"
            ),
            "    match 'local-value':\n        case s:\n            return s\n",
        ],
    )
    def test_local_binding_does_not_hide_another_scope_provider(
        cls,
        tmp_path: Path,
        local_body: str,
        consumer: str,
    ) -> None:
        """A local capture and a separate global lazy provider both execute."""
        project, package = cls._project(tmp_path)
        cls._lazy_init(package, {"s": ".provider"})
        (package / "provider.py").write_text(
            "def s():\n    return 'provider-value'\n\n__all__ = ['s']\n",
            encoding="utf-8",
        )
        module = package / "consumer.py"
        source = (
            f"def capture():\n{local_body}\n"
            f"{consumer}\n"
            "print(capture())\nprint(consume())\n"
        )
        normalized = u.Infra.normalize_import_source(
            project_root=project,
            file_path=module,
            source=source,
        )
        module.write_text(
            normalized if normalized is not None else source,
            encoding="utf-8",
        )
        outcome = tm.ok(
            u.Cli.run(
                (sys.executable, str(module)),
                cwd=project,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            ),
        )
        tm.ok(u.Cli.process_succeeded(outcome.outcome))
        tm.that(outcome.stdout.splitlines(), eq=["local-value", "provider-value"])
        tm.that(
            u.Infra.normalize_import_source(
                project_root=project,
                file_path=module,
                source=module.read_text(encoding="utf-8"),
            ),
            eq=None,
        )


class TestsFlextInfraInheritedFacadeImportNormalization(
    TestsFlextInfraRefactorImportNormalizationSupport,
):
    """Inherited facade routes preserve runtime behavior and graph ownership."""

    @classmethod
    def test_planned_retirements_do_not_restore_a_discarded_import_cycle(
        cls, tmp_path: Path
    ) -> None:
        """The same captured witnesses retain tombstones through both plan passes."""
        project, package = cls._project(tmp_path)
        retired = (package / "retired_a.py", package / "retired_b.py")
        retired[0].write_text(
            "from demo_pkg.retired_b import Beta\nclass Alpha(Beta):\n    pass\n",
            encoding=c.DEFAULT_ENCODING,
        )
        retired[1].write_text(
            "from demo_pkg.retired_a import Alpha\nclass Beta(Alpha):\n    pass\n",
            encoding=c.DEFAULT_ENCODING,
        )
        (package / "_utilities" / "helper.py").write_text(
            "class DemoHelper:\n    marker = 'retirement'\n__all__ = ['DemoHelper']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        target = package / "consumer.py"
        target.write_text(
            "from demo_pkg._utilities.helper import DemoHelper\n"
            "value = DemoHelper.marker\n",
            encoding=c.DEFAULT_ENCODING,
        )
        with u.Infra.workspace_snapshot(project, (project,)) as snapshot:
            captured = u.Infra.workspace_sources(snapshot)
            sources = {path: entry.text for path, entry in captured.items()}
            live = u.Infra.plan_import_normalization(
                project,
                (target,),
                sources=sources,
                declared_files=(),
                snapshot=snapshot,
            )
            tm.that(live.failure, eq=True)
            tm.that(live.error, has="runtime dependency cycles")
            tombstones = tuple(
                m.Infra.CodegenFilePlan(
                    project=project,
                    path=path,
                    before=captured[path].state,
                    desired_content=None,
                    desired_mode=None,
                )
                for path in retired
            )
            for path in retired:
                del sources[path]
            planned = tm.ok(
                u.Infra.plan_import_normalization(
                    project,
                    (target,),
                    sources=sources,
                    declared_files=tombstones,
                    snapshot=snapshot,
                )
            )
            tm.that(planned, length=1)
            tm.that(planned[0].before, eq=captured[target].state)
            sources[target] = tm.not_none(planned[0].desired_content).decode(
                c.DEFAULT_ENCODING
            )
            tm.that(
                tm.ok(
                    u.Infra.plan_import_normalization(
                        project,
                        (target,),
                        sources=sources,
                        declared_files=tombstones,
                        snapshot=snapshot,
                    )
                ),
                eq=(),
            )
            for path in retired:
                tm.that(path.read_bytes(), eq=captured[path].state.content)
        tm.ok(u.Infra.publish_codegen_plans(project, (*tombstones, *planned)))
        for path in retired:
            tm.that(path.exists(), eq=False)
        process = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-c",
                    "from demo_pkg.consumer import value; assert value == 'retirement'",
                ),
                cwd=project,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            )
        )
        tm.ok(u.Cli.process_succeeded(process.outcome))

    @classmethod
    def test_inherited_facades_preserve_runtime_and_lexical_aliases(
        cls, tmp_path: Path
    ) -> None:
        """Application members use local MRO without capturing shadowed names."""
        project, package = cls._inherited_project(tmp_path)
        target = package / "services" / "worker.py"
        source = (
            "from upstream_pkg import c, m, u\n"
            "\n"
            "def run(value: str) -> str:\n"
            "    return u.render(m.render(c.render(value)))\n"
            "\n"
            "def shadow(m: str) -> str:\n"
            "    return m\n"
        )
        target.write_text(source, encoding=c.DEFAULT_ENCODING)
        normalized = cls._normalize(project, target, source)
        tm.that(normalized, has="from demo_pkg import c, m, u")
        tm.that(normalized, has="return m")
        target.write_text(normalized, encoding=c.DEFAULT_ENCODING)
        process = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-c",
                    (
                        "from demo_pkg.services.worker import run, shadow; "
                        "assert run('unchanged') == 'unchanged'; "
                        "assert shadow('local') == 'local'"
                    ),
                ),
                cwd=project,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            )
        )
        tm.ok(u.Cli.process_succeeded(process.outcome))
        tm.that(
            u.Infra.normalize_import_source(
                project_root=project, file_path=target, source=normalized
            ),
            eq=None,
        )

    @classmethod
    def test_inherited_facade_override_rejects_before_publication(
        cls, tmp_path: Path
    ) -> None:
        """An overriding local method cannot replace the upstream consumer."""
        project, package = cls._inherited_project(tmp_path, override_member=True)
        target = package / "services" / "worker.py"
        source = (
            "from upstream_pkg import m\n"
            "\n"
            "def run(value: str) -> str:\n"
            "    return m.render(value)\n"
        )
        target.write_text(source, encoding=c.DEFAULT_ENCODING)
        with pytest.raises(ValueError, match="local facade changes consumed member"):
            u.Infra.normalize_import_source(
                project_root=project, file_path=target, source=source
            )
        tm.that(target.read_text(encoding=c.DEFAULT_ENCODING), eq=source)

    @classmethod
    @pytest.mark.parametrize("typing_edge", [False, True])
    def test_lazy_publication_and_typing_edge_are_not_runtime_cycles(
        cls, tmp_path: Path, *, typing_edge: bool
    ) -> None:
        """A cold lazy import remains executable after the shared batch plan."""
        project, package = cls._project(tmp_path)
        cls._lazy_init(package / "services", {"DemoRunner": ".worker"})
        models = package / u.Infra.facade_families()["m"].module
        models = models.with_suffix(".py")
        models.write_text(
            (
                "from typing import TYPE_CHECKING\n"
                "if TYPE_CHECKING:\n"
                "    from demo_pkg.services import DemoRunner\n"
                if typing_edge
                else ""
            )
            + "class m:\n"
            "    @staticmethod\n"
            "    def render(value: str) -> str:\n"
            "        return value\n"
            "__all__ = ['m']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        target = package / "services" / "worker.py"
        target.write_text(
            f"from demo_pkg.{models.stem} import m\n"
            "class DemoRunner:\n"
            "    @staticmethod\n"
            "    def run(value: str) -> str:\n"
            "        return m.render(value)\n"
            "__all__ = ['DemoRunner']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        with u.Infra.workspace_snapshot(project, (project,)) as snapshot:
            sources = {
                path: entry.text
                for path, entry in u.Infra.workspace_sources(snapshot).items()
            }
            plans = tm.ok(
                u.Infra.plan_import_normalization(
                    project,
                    (target,),
                    sources=sources,
                    declared_files=(),
                    snapshot=snapshot,
                )
            )
        tm.that(plans, length=1)
        desired = tm.not_none(plans[0].desired_content).decode(c.DEFAULT_ENCODING)
        tm.that(desired, has="from demo_pkg import m")
        target.write_text(desired, encoding=c.DEFAULT_ENCODING)
        tm.that(
            u.Infra.normalize_import_source(
                project_root=project, file_path=target, source=desired
            ),
            eq=None,
        )
        process = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-c",
                    (
                        "from demo_pkg.services import DemoRunner; "
                        "assert DemoRunner.run('cold') == 'cold'"
                    ),
                ),
                cwd=project,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            )
        )
        tm.ok(u.Cli.process_succeeded(process.outcome))

    @classmethod
    def test_planned_foreign_homonyms_do_not_expand_member_ownership(
        cls, tmp_path: Path
    ) -> None:
        """Another member's incompatible facade cannot enter this batch's scope."""
        project, package = cls._inherited_project(tmp_path)
        other, other_package = cls._inherited_project(
            project / "nested", override_member=True
        )
        target = package / "services" / "worker.py"
        foreign = other_package / "services" / "worker.py"
        source = "from upstream_pkg import m\nvalue = m.render('member')\n"
        for path in (target, foreign):
            path.write_text(source, encoding=c.DEFAULT_ENCODING)
        with (
            u.Infra.workspace_snapshot(project, (project, other)) as snapshot,
            u.Infra.workspace_snapshot(other, (other,)) as other_snapshot,
        ):
            sources = {
                path: entry.text
                for path, entry in u.Infra.workspace_sources(snapshot).items()
            }
            sources.update({
                path: entry.text
                for path, entry in u.Infra.workspace_sources(other_snapshot).items()
            })
            plans = tm.ok(
                u.Infra.plan_import_normalization(
                    project,
                    (target, foreign),
                    sources=sources,
                    declared_files=(),
                    snapshot=snapshot,
                )
            )
        tm.that(tuple(plan.path for plan in plans), eq=(target,))
        tm.that(
            tm.not_none(plans[0].desired_content).decode(c.DEFAULT_ENCODING),
            has="from demo_pkg import m",
        )
        tm.that(target.read_text(encoding=c.DEFAULT_ENCODING), eq=source)
        tm.that(foreign.read_text(encoding=c.DEFAULT_ENCODING), eq=source)

    @classmethod
    def test_runtime_cycle_rejects_the_batch_without_publishing(
        cls, tmp_path: Path
    ) -> None:
        """A cycle rejected by cold Python import also rejects the batch plan."""
        project, package = cls._project(tmp_path)
        target = package / "alpha.py"
        source = "from demo_pkg.beta import Beta\nclass Alpha(Beta):\n    pass\n"
        target.write_text(source, encoding=c.DEFAULT_ENCODING)
        (package / "beta.py").write_text(
            "from demo_pkg.alpha import Alpha\nclass Beta(Alpha):\n    pass\n",
            encoding=c.DEFAULT_ENCODING,
        )
        with u.Infra.workspace_snapshot(project, (project,)) as snapshot:
            planned = u.Infra.plan_import_normalization(
                project,
                (target,),
                sources={
                    path: entry.text
                    for path, entry in u.Infra.workspace_sources(snapshot).items()
                },
                declared_files=(),
                snapshot=snapshot,
            )
        tm.that(planned.failure, eq=True)
        tm.that(planned.error, has="runtime dependency cycles")
        tm.that(target.read_text(encoding=c.DEFAULT_ENCODING), eq=source)
        process = tm.ok(
            u.Cli.run(
                (sys.executable, "-c", "from demo_pkg.alpha import Alpha"),
                cwd=project,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            )
        )
        tm.that(u.Cli.process_succeeded(process.outcome), eq=False)
