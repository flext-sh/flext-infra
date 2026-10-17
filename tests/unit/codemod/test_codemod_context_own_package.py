"""The own-package codemod predicate spans the project's internal tiers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import c, config, m
from tests import t, tm, u


class TestsFlextInfraCodemodContextOwnPackage:
    """An import between a project's own namespaces never crosses an owner."""

    @pytest.mark.parametrize(
        "dependencies",
        [None, (), ("pydantic; python_version < '0'",)],
    )
    @pytest.mark.parametrize(
        "predicate",
        [
            c.Infra.CodemodContextPredicate.RUNTIME_PACKAGE,
            c.Infra.CodemodContextPredicate.FACADE_PACKAGE,
        ],
    )
    def test_empty_declared_runtime_rejects_installed_external_packages(
        self,
        tmp_path: Path,
        dependencies: t.StrSequence | None,
        predicate: c.Infra.CodemodContextPredicate,
    ) -> None:
        """Omitted, empty and inapplicable requirements declare no providers."""
        project = u.Tests.mk_project(
            tmp_path,
            "runtime-probe",
            pyproject='[project]\nname = "runtime-probe"\nversion = "0.1.0"\n',
            with_src=True,
        )
        declaration: t.JsonDict = {
            "project": {"name": "runtime-probe", "version": "0.1.0"},
        }
        if dependencies is not None:
            declaration["project"] = {
                "name": "runtime-probe",
                "version": "0.1.0",
                "dependencies": list(dependencies),
            }
        tm.ok(u.Cli.toml_write_mapping(project / c.PYPROJECT_FILENAME, declaration))
        consumer = project / "consumer.py"
        consumer.write_text(
            "from pydantic import BaseModel\n",
            encoding=c.DEFAULT_ENCODING,
        )
        rule = self._private_import_rule().model_copy(
            update={
                "context": (
                    m.Infra.CodemodContextCondition(
                        variable="MOD",
                        predicate=predicate,
                        holds=True,
                    ),
                ),
            },
        )
        facts = u.Infra.codemod_project_facts(project, (rule,))
        tm.that(facts.runtime_modules, empty=True)
        with u.Infra.codemod_binding_project(
            project,
            u.Infra.codemod_source_epoch(m.Infra.CodemodBindingSnapshot(states=())),
        ) as (rope_project, sources):
            admitted = u.Infra.codemod_context_admits(
                m.Infra.CodemodAdmission(
                    root=project,
                    rule=rule,
                    file_path=consumer,
                    captures={"MOD": {"text": "pydantic"}},
                    facts=facts,
                ),
                project=rope_project,
                sources=sources,
            )
        tm.that(admitted, eq=False)

    def test_declared_installed_runtime_package_is_admitted(
        self,
        tmp_path: Path,
    ) -> None:
        """A nonempty real requirement retains runtime-package admission."""
        project = u.Tests.mk_project(
            tmp_path,
            "runtime-probe",
            pyproject=(
                '[project]\nname = "runtime-probe"\nversion = "0.1.0"\n'
                'dependencies = ["pydantic"]\n'
            ),
            with_src=True,
        )
        consumer = project / "consumer.py"
        consumer.write_text(
            "from pydantic import BaseModel\n",
            encoding=c.DEFAULT_ENCODING,
        )
        rule = self._private_import_rule().model_copy(
            update={
                "context": (
                    m.Infra.CodemodContextCondition(
                        variable="MOD",
                        predicate=c.Infra.CodemodContextPredicate.RUNTIME_PACKAGE,
                        holds=True,
                    ),
                ),
            },
        )
        facts = u.Infra.codemod_project_facts(project, (rule,))
        with u.Infra.codemod_binding_project(
            project,
            u.Infra.codemod_source_epoch(m.Infra.CodemodBindingSnapshot(states=())),
        ) as (rope_project, sources):
            admitted = u.Infra.codemod_context_admits(
                m.Infra.CodemodAdmission(
                    root=project,
                    rule=rule,
                    file_path=consumer,
                    captures={"MOD": {"text": "pydantic"}},
                    facts=facts,
                ),
                project=rope_project,
                sources=sources,
            )
        tm.that(admitted, eq=True)

    @pytest.mark.parametrize(
        ("relative", "admitted"),
        [("_utilities/base.py", True), ("_utilities/_behavior/base.py", False)],
    )
    def test_family_base_role_requires_the_immediate_declared_facade(
        self, mod_workspace: Path, relative: str, *, admitted: bool
    ) -> None:
        """Nested behavior bases never borrow their ancestor's family role."""
        namespace = u.Infra.project_package_name(mod_workspace)
        package = mod_workspace / c.Infra.DEFAULT_SRC_DIR / namespace
        export = config.Infra.tooling.lazy_init.import_layer_order[0]
        (package / "utilities.py").write_text(
            f"__all__ = [{export!r}]\n", encoding="utf-8"
        )
        path = package / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if path.parent.parent != package:
            (path.parent.parent / "behavior.py").write_text(
                f"__all__ = [{export!r}]\n", encoding="utf-8"
            )
        path.write_text("from flext_core import c\n", encoding="utf-8")
        rule = self._private_import_rule().model_copy(
            update={
                "context": (
                    m.Infra.CodemodContextCondition(
                        variable="MOD",
                        predicate=c.Infra.CodemodContextPredicate.FAMILY_BASE_FILE,
                        holds=True,
                    ),
                )
            }
        )
        verdict = u.Infra.codemod_context_admits(
            m.Infra.CodemodAdmission(
                root=mod_workspace,
                rule=rule,
                file_path=path,
                captures={"MOD": {"text": "flext_core"}},
                facts=u.Infra.codemod_project_facts(mod_workspace, (rule,)),
            ),
        )
        tm.that(verdict, eq=admitted)

    @staticmethod
    def _private_import_rule() -> m.Infra.CodemodRule:
        return m.Infra.CodemodRule(
            id="private-import-probe",
            digest="probe",
            provider="probe",
            resource=Path("probe.yml"),
            fixable=False,
            context=(
                m.Infra.CodemodContextCondition(
                    variable="MOD",
                    predicate=c.Infra.CodemodContextPredicate.OWN_PACKAGE,
                    holds=False,
                ),
            ),
        )

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
        self,
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
        rule = self._private_import_rule()
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

    @pytest.mark.parametrize(
        ("module", "admitted"),
        [
            ("demo._support", False),
            ("tests.unit._support", False),
            ("other_package._support", True),
        ],
    )
    def test_internal_tiers_are_own_namespaces(
        self,
        tmp_path: Path,
        module: str,
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
        consumer = project / "tests" / "unit" / "consumer_tests.py"
        consumer.parent.mkdir(parents=True)
        consumer.write_text(f"from {module} import Helper\n", encoding="utf-8")

        rule = self._private_import_rule()
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

    def test_new_pass_reads_the_changed_declared_namespace(
        self, tmp_path: Path
    ) -> None:
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
        rule = self._private_import_rule()
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
                ),
            }
        )
        facts = u.Infra.codemod_project_facts(mod_workspace, (rule,))
        closed = u.Infra.codemod_binding_snapshot(
            mod_workspace,
            (tm.ok(u.Cli.atomic_read_binary_file_state(consumer, required=True)),),
            (module_name,),
        )
        epoch = u.Infra.codemod_source_epoch(closed)
        with u.Infra.codemod_binding_project(mod_workspace, epoch) as (
            project,
            sources,
        ):
            for start, captured, expected in (
                (source.index("Public", source.index("value =")), "Public", True),
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
            (tm.ok(u.Cli.atomic_read_binary_file_state(consumer, required=True)),),
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
