"""Own-package codemod predicate admission, ownership and occurrence contracts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from tests import c, m, t, tm, u
from tests.unit.codemod.context_own_package_support import (
    TestsFlextInfraContextOwnPackageSupport,
)


class TestsFlextInfraCodemodContextOwnPackageAdmission:
    """Member ownership, internal tiers and occurrence identity stay strict."""

    @staticmethod
    @pytest.mark.parametrize(
        ("module", "admitted"),
        [
            ("demo._support", False),
            ("tests.unit._support", False),
            ("workspace._support", True),
            ("other_package._support", True),
        ],
    )
    def test_member_ownership_matches_workspace_and_local_admission(
        tmp_path: Path,
        module: str,
        *,
        admitted: bool,
    ) -> None:
        """Only the member namespace and its internal tiers share the owner."""
        workspace = u.Tests.mk_project(
            tmp_path,
            "workspace",
            pyproject='[project]\nname = "workspace"\nversion = "1.0.0"\n',
            with_src=True,
        )
        member = u.Tests.mk_project(
            workspace,
            "demo",
            pyproject='[project]\nname = "demo"\nversion = "1.0.0"\n',
            with_src=True,
        )
        for root in (workspace, member):
            u.Tests.initialize_git_repo(root)
            u.Tests.write_workspace_manifest(
                root,
                root.name,
                role=(
                    c.Infra.MakeProfile.WORKSPACE
                    if root == workspace
                    else c.Infra.MakeProfile.STANDALONE
                ),
            )
        u.Tests.declare_workspace_projects(workspace, (member.name,))
        consumer = member / "tests" / "unit" / "consumer_tests.py"
        consumer.parent.mkdir(parents=True)
        consumer.write_text(f"from {module} import Helper\n", encoding="utf-8")
        rule = TestsFlextInfraContextOwnPackageSupport.private_import_rule()
        for root in (workspace, member):
            verdict = u.Infra.codemod_context_admits(
                m.Infra.CodemodAdmission(
                    root=root,
                    rule=rule,
                    file_path=consumer,
                    captures={"MOD": {"text": module}},
                    facts=u.Infra.codemod_project_facts(root, (rule,)),
                ),
            )
            tm.that(verdict, eq=admitted)

    @staticmethod
    @pytest.mark.parametrize(
        ("module", "admitted"),
        [
            ("demo._support", False),
            ("tests.unit._support", False),
            ("other_package._support", True),
        ],
    )
    @pytest.mark.parametrize("surface", ["tests", "scripts", "examples"])
    def test_internal_tiers_are_own_namespaces(
        tmp_path: Path,
        module: str,
        surface: str,
        *,
        admitted: bool,
    ) -> None:
        """Test internal tiers are own namespaces."""
        project = u.Tests.mk_project(
            tmp_path,
            "demo",
            pyproject='[project]\nname = "demo"\nversion = "0.1.0"\n',
            with_src=True,
        )
        tier = project / surface
        tier.mkdir(exist_ok=True)
        (tier / c.Infra.INIT_PY).write_text("", encoding=c.DEFAULT_ENCODING)
        consumer = tier / "unit" / "consumer_tests.py"
        consumer.parent.mkdir(parents=True)
        consumer.write_text(f"from {module} import Helper\n", encoding="utf-8")

        rule = TestsFlextInfraContextOwnPackageSupport.private_import_rule()
        verdict = u.Infra.codemod_context_admits(
            m.Infra.CodemodAdmission(
                root=project,
                rule=rule,
                file_path=consumer,
                captures={"MOD": {"text": module}},
                facts=u.Infra.codemod_project_facts(project, (rule,)),
            ),
        )

        tm.that(verdict, eq=admitted)

    @staticmethod
    @pytest.mark.parametrize(
        ("consumer", "module", "admitted"),
        [
            ("_models/base.py", "demo._models.entity", False),
            ("models.py", "demo._models.entity", False),
            ("services/_parts/run.py", "demo.services._parts.step", False),
            ("services/parts.py", "demo.services._parts.step", False),
            ("_utilities/guards.py", "demo._models.entity", True),
            ("services/runner.py", "demo._models.entity", True),
            ("services/runner.py", "demo.services._parts.step", True),
        ],
    )
    def test_family_internal_imports_admit_only_outsiders(
        tmp_path: Path,
        consumer: str,
        module: str,
        *,
        admitted: bool,
    ) -> None:
        """Only modules outside the family and its facade are admitted."""
        project = u.Tests.mk_project(
            tmp_path,
            "demo",
            pyproject='[project]\nname = "demo"\nversion = "0.1.0"\n',
            with_src=True,
        )
        package = project / c.Infra.DEFAULT_SRC_DIR / "demo"
        package.mkdir(parents=True, exist_ok=True)
        (package / c.Infra.INIT_PY).write_text("", encoding=c.DEFAULT_ENCODING)
        source = package / consumer
        source.parent.mkdir(parents=True, exist_ok=True)
        source.write_text(f"from {module} import Helper\n", encoding="utf-8")
        rule = m.Infra.CodemodRule(
            id="family-internal-import-probe",
            digest="probe",
            provider="probe",
            resource=Path("probe.yml"),
            fixable=False,
            context=(
                m.Infra.CodemodContextCondition(
                    variable="MOD",
                    predicate=c.Infra.CodemodContextPredicate.OWN_PACKAGE,
                    holds=True,
                ),
                m.Infra.CodemodContextCondition(
                    variable="FAMILY",
                    predicate=c.Infra.CodemodContextPredicate.FAMILY_MEMBER,
                    holds=False,
                ),
            ),
        )

        verdict = u.Infra.codemod_context_admits(
            m.Infra.CodemodAdmission(
                root=project,
                rule=rule,
                file_path=source,
                captures={"MOD": {"text": module}, "FAMILY": module},
                facts=u.Infra.codemod_project_facts(project, (rule,)),
            ),
        )

        tm.that(verdict, eq=admitted)

    @staticmethod
    def test_new_pass_reads_the_changed_declared_namespace(tmp_path: Path) -> None:
        """Each admission pass consumes the current declared namespace."""
        project = u.Tests.mk_project(
            tmp_path,
            "demo",
            pyproject='[project]\nname = "demo"\nversion = "0.1.0"\n',
            with_src=True,
        )
        original = u.Infra.project_package_name(project)
        consumer = project / "consumer.py"
        consumer.write_text(
            f"from {original}._support import Helper\n", encoding=c.DEFAULT_ENCODING
        )
        rule = TestsFlextInfraContextOwnPackageSupport.private_import_rule()
        outcomes: t.MutableSequenceOf[bool] = []
        renamed = f"{original}_renamed"
        for namespace in (original, renamed):
            if namespace == renamed:
                (project / c.Infra.DEFAULT_SRC_DIR / original).rename(
                    project / c.Infra.DEFAULT_SRC_DIR / renamed
                )
            tm.ok(
                u.Cli.toml_write_mapping(
                    project / c.PYPROJECT_FILENAME,
                    {
                        "project": {"name": "demo", "version": "0.1.0"},
                        "tool": {"flext": {"docs": {"package_name": namespace}}},
                    },
                )
            )
            facts = u.Infra.codemod_project_facts(project, (rule,))
            outcomes.append(
                u.Infra.codemod_context_admits(
                    m.Infra.CodemodAdmission(
                        root=project,
                        rule=rule,
                        file_path=consumer,
                        captures={"MOD": {"text": f"{original}._support"}},
                        facts=facts,
                    ),
                )
            )
        tm.that(outcomes, eq=[False, True])

    @staticmethod
    @pytest.mark.parametrize("same_generic", [True, False])
    @pytest.mark.parametrize("bind_import", [True, False])
    @pytest.mark.parametrize("package_owner", [True, False])
    def test_generic_specialization_requires_original_binding(
        mod_workspace: Path,
        binding_probe_rule: m.Infra.CodemodRule,
        *,
        same_generic: bool,
        bind_import: bool,
        package_owner: bool,
    ) -> None:
        """A same-named alias of another generic is never a migration target."""
        namespace = u.Infra.project_package_name(mod_workspace)
        module_name = namespace if package_owner else f"{namespace}.generic_owner"
        owner = (
            mod_workspace
            / c.Infra.DEFAULT_SRC_DIR
            / namespace
            / (c.Infra.INIT_PY if package_owner else "generic_owner.py")
        )
        selected = "Value" if same_generic else "Other"
        owner.write_text(
            "class Types:\n"
            "    type Value[T] = str | T\n"
            "    type Other[T] = bytes | T\n"
            "t = Types\n"
            "class Protocols:\n"
            f"    type Value = Types.{selected}[int]\n"
            "p = Protocols\n",
            encoding="utf-8",
        )
        consumer = mod_workspace / "generic_consumer.py"
        imported = "t" if bind_import else "p, t"
        source = f"from {module_name} import {imported}\nvalue: t.Value\n"
        consumer.write_text(source, encoding="utf-8")
        rule = binding_probe_rule.model_copy(
            update={
                "context": (
                    m.Infra.CodemodContextCondition(
                        variable="OWNER",
                        predicate=c.Infra.CodemodContextPredicate.GENERIC_SPECIALIZATION,
                        of="MEMBER",
                        arg=("p", "NAMESPACE") if bind_import else ("p",),
                        holds=True,
                    ),
                ),
            }
        )
        closed = u.Infra.codemod_binding_snapshot(
            mod_workspace,
            tuple(
                tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
                for path in (
                    (
                        mod_workspace
                        / c.Infra.DEFAULT_SRC_DIR
                        / namespace
                        / c.Infra.INIT_PY
                    ),
                    consumer,
                )
            ),
            (module_name,),
        )
        start = source.index("t.Value")
        captures: t.JsonMapping = {
            "NAMESPACE": {
                "text": module_name,
                "range": {"byteOffset": {"start": 5, "end": 5 + len(module_name)}},
            },
            "OWNER": {
                "text": "t",
                "range": {"byteOffset": {"start": start, "end": start + 1}},
            },
            "MEMBER": {
                "text": "Value",
                "range": {"byteOffset": {"start": start + 2, "end": start + 7}},
            },
        }
        with u.Infra.codemod_binding_project(
            mod_workspace,
            u.Infra.codemod_source_epoch(closed),
        ) as (project, sources):
            tm.that(
                u.Infra.codemod_context_admits(
                    m.Infra.CodemodAdmission(
                        root=mod_workspace,
                        rule=rule,
                        file_path=consumer,
                        captures=captures,
                        facts=u.Infra.codemod_project_facts(mod_workspace, (rule,)),
                        snapshot=closed,
                    ),
                    project=project,
                    sources=sources,
                ),
                eq=same_generic,
            )

    @staticmethod
    def _write_occurrence_modules(
        mod_workspace: Path,
        *,
        reexport: bool,
    ) -> tuple[Path, Path, str, str]:
        """Author definer and consumer modules for one occurrence identity case.

        Returns:
            Consumer path, owner path, consumer source, and elected module name.

        """
        namespace = u.Infra.project_package_name(mod_workspace)
        package_root = mod_workspace / c.Infra.DEFAULT_SRC_DIR / namespace
        module_name = f"{namespace}.definer"
        if reexport:
            package = package_root / "definer"
            package.mkdir()
            (package / c.Infra.INIT_PY).write_text(
                "from .utilities import Public, u\n", encoding="utf-8"
            )
            owner = package / "utilities.py"
            module_name = f"{namespace}.definer.utilities"
        else:
            owner = package_root / "definer.py"
        owner.write_text("class Public:\n    pass\nu = Public\n", encoding="utf-8")
        consumer = mod_workspace / "consumer.py"
        source = (
            f"from {namespace}.definer import Public, u\n"
            "note = 'é'\n"
            'template = f"${{UNSET_FOR_THIS_TEST:-{note}}}"\n'
            "label = 'Public'\n"
            "value = Public\n"
            "def independent(Public):\n"
            "    return Public\n"
            "def conditional_owner(flag):\n"
            "    if flag:\n"
            "        conditional = Public\n"
            "    return conditional\n"
        )
        consumer.write_text(source, encoding="utf-8")
        return consumer, owner, source, module_name

    @pytest.mark.parametrize("reexport", [False, True])
    def test_occurrence_identity_is_lexical_and_immutable(
        self,
        mod_workspace: Path,
        binding_probe_rule: m.Infra.CodemodRule,
        *,
        reexport: bool,
    ) -> None:
        """Identical spelling in another scope never borrows a module binding."""
        consumer, owner, source, module_name = self._write_occurrence_modules(
            mod_workspace,
            reexport=reexport,
        )
        rule = binding_probe_rule.model_copy(
            update={
                "context": (
                    m.Infra.CodemodContextCondition(
                        variable="OWNER",
                        predicate=c.Infra.CodemodContextPredicate.RESOLVED_SYMBOL,
                        arg=(module_name, "Public"),
                        holds=True,
                    ),
                    m.Infra.CodemodContextCondition(
                        variable="OWNER",
                        predicate=c.Infra.CodemodContextPredicate.SAME_BINDING,
                        arg=("u",),
                        holds=True,
                    ),
                    m.Infra.CodemodContextCondition(
                        variable="ALTERNATIVE_BRANCH",
                        predicate=c.Infra.CodemodContextPredicate.RESOLVED_SYMBOL,
                        arg=(module_name, "Independent"),
                        holds=True,
                    ),
                ),
            }
        )
        facts = u.Infra.codemod_project_facts(mod_workspace, (rule,))
        closed = u.Infra.codemod_binding_snapshot(
            mod_workspace,
            tuple(
                tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
                for path in dict.fromkeys((
                    (
                        mod_workspace
                        / c.Infra.DEFAULT_SRC_DIR
                        / u.Infra.project_package_name(mod_workspace)
                        / c.Infra.INIT_PY
                    ),
                    owner.parent / c.Infra.INIT_PY,
                    consumer,
                ))
            ),
            (module_name,),
        )
        epoch = u.Infra.codemod_source_epoch(closed)
        with u.Infra.codemod_binding_project(mod_workspace, epoch) as (
            project,
            sources,
        ):
            for start, captured, expected in (
                (source.index("Public", source.index("value =")), "Public", True),
                (source.index("Public", source.index("label =")), "Public", False),
                (
                    source.index("Public", source.index("return Public")),
                    "Public",
                    False,
                ),
                (source.rindex("conditional"), "conditional", False),
            ):
                start_byte = len(source[:start].encode("utf-8"))
                capture: t.JsonMapping = {
                    "OWNER": {
                        "text": captured,
                        "range": {
                            "byteOffset": {
                                "start": start_byte,
                                "end": start_byte + len(captured.encode("utf-8")),
                            }
                        },
                    },
                }
                for _ in range(2):
                    tm.that(
                        u.Infra.codemod_context_admits(
                            m.Infra.CodemodAdmission(
                                root=mod_workspace,
                                rule=rule,
                                file_path=consumer,
                                captures=capture,
                                facts=facts,
                                snapshot=closed,
                            ),
                            project=project,
                            sources=sources,
                        ),
                        eq=expected,
                        msg=f"occurrence at byte {start_byte} expected {expected}",
                    )
        tm.that(consumer.read_text(encoding="utf-8"), eq=source)
        start = source.index("Public", source.index("value ="))
        start_byte = len(source[:start].encode("utf-8"))
        positive: t.JsonMapping = {
            "OWNER": {
                "text": "Public",
                "range": {
                    "byteOffset": {
                        "start": start_byte,
                        "end": start_byte + len("Public"),
                    }
                },
            }
        }
        owner.write_text(
            "class Public:\n    pass\nclass Independent:\n    pass\nu = Independent\n",
            encoding="utf-8",
        )
        with u.Infra.codemod_binding_project(mod_workspace, epoch) as (
            project,
            sources,
        ):
            tm.that(
                u.Infra.codemod_context_admits(
                    m.Infra.CodemodAdmission(
                        root=mod_workspace,
                        rule=rule,
                        file_path=consumer,
                        captures=positive,
                        facts=facts,
                        snapshot=closed,
                    ),
                    project=project,
                    sources=sources,
                ),
                eq=True,
            )
        changed = u.Infra.codemod_binding_snapshot(
            mod_workspace,
            tuple(
                tm.ok(u.Cli.atomic_read_binary_file_state(state.path, required=True))
                for state in closed.states
                if state.path.is_relative_to(mod_workspace)
            ),
            (module_name,),
        )
        with u.Infra.codemod_binding_project(
            mod_workspace, u.Infra.codemod_source_epoch(changed)
        ) as (
            project,
            sources,
        ):
            tm.that(
                u.Infra.codemod_context_admits(
                    m.Infra.CodemodAdmission(
                        root=mod_workspace,
                        rule=rule,
                        file_path=consumer,
                        captures=positive,
                        facts=facts,
                        snapshot=changed,
                    ),
                    project=project,
                    sources=sources,
                ),
                eq=False,
            )
        tm.that(consumer.read_text(encoding="utf-8"), eq=source)
