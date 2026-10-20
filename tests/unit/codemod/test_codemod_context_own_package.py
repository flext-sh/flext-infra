"""The own-package codemod predicate spans the project's internal tiers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import config
from flext_infra.codemod import FlextInfraModGateEngine
from tests import c, m, t, tm, u


class TestsFlextInfraCodemodContextOwnPackage:
    """An import between a project's own namespaces never crosses an owner."""

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize("producer", [False, True])
    @pytest.mark.parametrize("module_import", [False, True])
    def test_own_utility_import_requires_the_declared_producer_family(
        mod_workspace: Path,
        *,
        producer: bool,
        module_import: bool,
    ) -> None:
        """Consumer categories never borrow a real facade producer's role."""
        family = u.Infra.facade_families()["u"]
        tests_root = mod_workspace / c.Infra.DIR_TESTS
        tm.ok(u.Cli.ensure_dir(tests_root))
        tm.ok(
            u.Cli.atomic_write_text_file(
                tests_root / c.Infra.INIT_PY,
                f"from .{family.module} import u\n",
            )
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                tests_root / f"{family.module}.py",
                "from flext_core import u\n__all__ = ['u']\n",
            )
        )
        source = (
            (tests_root if producer else tests_root / "unit")
            / f"_{family.module}"
            / "probe.py"
        )
        tm.ok(u.Cli.ensure_dir(source.parent))
        tm.ok(
            u.Cli.atomic_write_text_file(
                source,
                f"import {tests_root.name}.{family.module}\n"
                if module_import
                else f"from {tests_root.name} import u\n",
            )
        )
        plan = tm.ok(u.Infra.codemod_rule_plan(mod_workspace))
        selection = tuple(
            rule.id
            for rule in plan.rules
            if any(
                condition.predicate is c.Infra.CodemodContextPredicate.FILE_FAMILY
                and condition.holds
                for condition in rule.context
            )
        )
        tm.that(selection, empty=False)
        report = tm.ok(
            FlextInfraModGateEngine.scan(
                mod_workspace,
                fix=False,
                selection=selection,
                source_files=(source,),
            )
        )
        tm.that(bool(report.entries), eq=producer)

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
        tm.fail(admitted)

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
        tm.ok(admitted)

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

    @pytest.mark.parametrize("name", ["flext-role-probe", "external-role-probe"])
    @pytest.mark.parametrize("surface", ["src", "tests", "scripts", "examples"])
    @pytest.mark.parametrize("attached", [False, True])
    def test_layer_zero_role_uses_the_actual_member_namespace(
        self, tmp_path: Path, name: str, surface: str, *, attached: bool
    ) -> None:
        """Identical roles retain their verdict across names and entry roots."""
        workspace = u.Tests.mk_project(
            tmp_path,
            "role-workspace",
            pyproject='[project]\nname = "role-workspace"\nversion = "1.0.0"\n',
            with_src=True,
        )
        member = u.Tests.mk_project(
            workspace if attached else tmp_path,
            name,
            pyproject=f'[project]\nname = "{name}"\nversion = "1.0.0"\n',
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
        if attached:
            u.Tests.declare_workspace_projects(workspace, (member.name,))
        namespace = u.Infra.project_package_name(member)
        package = (
            member / c.Infra.DEFAULT_SRC_DIR / namespace
            if surface == c.Infra.DEFAULT_SRC_DIR
            else member / surface
        )
        package.mkdir(parents=True, exist_ok=True)
        (package / c.Infra.INIT_PY).write_text("", encoding=c.DEFAULT_ENCODING)
        rule = self._private_import_rule().model_copy(
            update={
                "context": (
                    m.Infra.CodemodContextCondition(
                        variable="MOD",
                        predicate=c.Infra.CodemodContextPredicate.LAYER_ZERO_FILE,
                        holds=True,
                    ),
                ),
            }
        )
        for relative, expected in (
            ("_config.py", True),
            ("_settings/part.py", True),
            ("_config/__init__.py", True),
            ("_models/_config.py", False),
            ("_utilities/_settings.py", False),
            ("consumer.py", False),
        ):
            source = package / relative
            source.parent.mkdir(parents=True, exist_ok=True)
            source.write_text("import os\n", encoding=c.DEFAULT_ENCODING)
            for root in (workspace, member) if attached else (member,):
                tm.that(
                    u.Infra.codemod_context_admits(
                        m.Infra.CodemodAdmission(
                            root=root,
                            rule=rule,
                            file_path=source,
                            captures={"MOD": {"text": "os"}},
                            facts=u.Infra.codemod_project_facts(root, (rule,)),
                        ),
                    ),
                    eq=expected,
                    msg=f"{root}: {surface}/{relative}",
                )

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize("surface", ["src", "tests", "scripts", "examples"])
    def test_library_boundary_scans_owned_code_without_filename_waivers(
        mod_workspace: Path, surface: str
    ) -> None:
        """Layer-zero imports are valid; homonyms and consumers remain visible.

        Visibility is asserted across the library boundary scan.
        """
        namespace = u.Infra.project_package_name(mod_workspace)
        package = (
            mod_workspace / c.Infra.DEFAULT_SRC_DIR / namespace
            if surface == c.Infra.DEFAULT_SRC_DIR
            else mod_workspace / surface
        )
        package.mkdir(parents=True, exist_ok=True)
        (package / c.Infra.INIT_PY).write_text("", encoding=c.DEFAULT_ENCODING)
        sources: t.MutableSequenceOf[Path] = []
        expected: set[Path] = set()
        original: t.MutableMappingKV[Path, str] = {}
        for relative, source, finding in (
            ("_config.py", "from pydantic import BaseModel\n", False),
            ("_settings/part.py", "from pydantic import BaseModel\n", False),
            ("_models/_config.py", "from pydantic import BaseModel\n", True),
            ("_utilities/_settings.py", "from pydantic import BaseModel\n", True),
            ("consumer.py", "from pydantic import BaseModel\n", True),
            ("ordinary.py", 'message = "from pydantic import BaseModel"\n', False),
        ):
            path = package / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(source, encoding=c.DEFAULT_ENCODING)
            sources.append(path)
            original[path] = source
            if finding:
                expected.add(path.resolve())
        report = tm.ok(
            FlextInfraModGateEngine.scan(
                mod_workspace,
                fix=False,
                selection=("ban-direct-pydantic-import",),
                source_files=tuple(sources),
            ),
        )
        tm.that(
            {
                u.Infra.codemod_source_path(mod_workspace, entry.file)
                for entry in report.entries
            },
            eq=expected,
        )
        for path, source in original.items():
            tm.that(path.read_text(encoding=c.DEFAULT_ENCODING), eq=source)

    def test_bound_layer_zero_role_uses_original_native_module_identity(
        self, mod_workspace: Path
    ) -> None:
        """A new live nested manifest cannot change an original semantic role."""
        namespace = u.Infra.project_package_name(mod_workspace)
        package = mod_workspace / c.Infra.DEFAULT_SRC_DIR / namespace
        boundary = package / "_config"
        boundary.mkdir()
        initializer = boundary / c.Infra.INIT_PY
        initializer.write_text("", encoding=c.DEFAULT_ENCODING)
        source = boundary / "part.py"
        source.write_text("import os\n", encoding=c.DEFAULT_ENCODING)
        rule = self._private_import_rule().model_copy(
            update={
                "context": (
                    m.Infra.CodemodContextCondition(
                        variable="MOD",
                        predicate=c.Infra.CodemodContextPredicate.LAYER_ZERO_FILE,
                        holds=True,
                    ),
                ),
            }
        )
        snapshot = u.Infra.codemod_binding_snapshot(
            mod_workspace,
            tuple(
                tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
                for path in (package / c.Infra.INIT_PY, initializer, source)
            ),
        )
        facts = u.Infra.codemod_project_facts(mod_workspace, (rule,))
        with u.Infra.codemod_binding_project(
            mod_workspace, u.Infra.codemod_source_epoch(snapshot)
        ) as (project, sources):
            (boundary / c.PYPROJECT_FILENAME).write_text(
                '[project]\nname = "new-unrelated-owner"\nversion = "1.0.0"\n',
                encoding=c.DEFAULT_ENCODING,
            )
            tm.that(
                u.Infra.codemod_context_admits(
                    m.Infra.CodemodAdmission(
                        root=mod_workspace,
                        rule=rule,
                        file_path=source,
                        captures={"MOD": {"text": "os"}},
                        facts=facts,
                        snapshot=snapshot,
                    ),
                    project=project,
                    sources=sources,
                ),
                eq=True,
            )

    @staticmethod
    @pytest.mark.parametrize("implementation", ["_native_process", "relocated_owner"])
    def test_process_implementation_role_follows_native_definitions_not_names(
        mod_workspace: Path, implementation: str
    ) -> None:
        """Public aliases, MRO and helper definitions elect the actual owner."""
        namespace = u.Infra.project_package_name(mod_workspace)
        package = mod_workspace / c.Infra.DEFAULT_SRC_DIR / namespace
        contents = {
            "_process_base.py": "class ProcessBase:\n    pass\n",
            "_process_helper.py": "def environment():\n    return {}\n",
            f"{implementation}.py": (
                "import subprocess\nfrom ._process_base import ProcessBase\n"
                "from ._process_helper import environment\n"
                "class NativeProcess(ProcessBase):\n"
                "    @staticmethod\n    def start(command):\n"
                "        return subprocess.Popen(command, env=environment())\n"
            ),
            "process_api.py": (
                f"from .{implementation} import NativeProcess as Process\n"
            ),
            "processes.py": "import subprocess\nclass NativeProcess:\n    pass\n",
            "runtime.py": "from .process_api import Process\nimport subprocess\n",
            "shadow.py": (
                "from .process_api import Process\nProcess = None\nimport subprocess\n"
            ),
        }
        for relative, text in contents.items():
            (package / relative).write_text(text, encoding=c.DEFAULT_ENCODING)
        rule = (
            tm
            .ok(
                u.Infra.codemod_rule_plan(
                    mod_workspace, rule_ids=("ban-subprocess-outside-run-owner",)
                )
            )
            .rules[0]
            .model_copy(
                update={
                    "context": (
                        m.Infra.CodemodContextCondition(
                            variable="IMPORT",
                            predicate=c.Infra.CodemodContextPredicate.IMPLEMENTATION_OWNER,
                            arg=(f"{namespace}.process_api", "Process.start"),
                            holds=False,
                        ),
                    ),
                }
            )
        )
        _, modules = u.Infra.codemod_binding_requirements((rule,))
        snapshot = u.Infra.codemod_binding_snapshot(
            mod_workspace,
            tuple(
                tm.ok(
                    u.Cli.atomic_read_binary_file_state(package / name, required=True)
                )
                for name in contents
            ),
            modules,
        )
        facts = u.Infra.codemod_project_facts(mod_workspace, (rule,))
        with u.Infra.codemod_binding_project(
            mod_workspace, u.Infra.codemod_source_epoch(snapshot)
        ) as (project, sources):
            (package / f"{implementation}.py").write_text(
                "class UnrelatedReplacement:\n    pass\n",
                encoding=c.DEFAULT_ENCODING,
            )
            for relative, admitted in (
                (f"{implementation}.py", False),
                ("_process_base.py", False),
                ("_process_helper.py", False),
                ("processes.py", True),
                ("runtime.py", True),
                ("shadow.py", True),
            ):
                tm.that(
                    u.Infra.codemod_context_admits(
                        m.Infra.CodemodAdmission(
                            root=mod_workspace,
                            rule=rule,
                            file_path=package / relative,
                            captures={"IMPORT": {"text": "import subprocess"}},
                            facts=facts,
                            snapshot=snapshot,
                        ),
                        project=project,
                        sources=sources,
                    ),
                    eq=admitted,
                    msg=relative,
                )

    @staticmethod
    @pytest.mark.parametrize("implementation", ["_native_logger", "relocated_logger"])
    def test_logging_native_owner_follows_constructor_helpers_not_consumers(
        mod_workspace: t.Infra.RopeSourcePath, implementation: str
    ) -> None:
        """A native backend moves with its primitive, not its facade consumers."""
        namespace = u.Infra.project_package_name(mod_workspace)
        package = mod_workspace / c.Infra.DEFAULT_SRC_DIR / namespace
        contents = {
            "_logging_base.py": "class LoggingBase:\n    pass\n",
            "_logging_sink.py": (
                "import structlog\n"
                "class NativeSink:\n"
                "    def create(self, name):\n"
                "        return structlog.get_logger(name)\n"
            ),
            f"{implementation}.py": (
                "from ._logging_base import LoggingBase\n"
                "from ._logging_sink import NativeSink\n"
                "class NativeLogging(LoggingBase):\n"
                "    @staticmethod\n"
                "    def fetch(name):\n"
                "        return NativeSink().create(name)\n"
            ),
            "logging_api.py": (
                f"from .{implementation} import NativeLogging as Utilities\n"
            ),
            "loggings.py": "import structlog\nclass NativeLogging:\n    pass\n",
            "consumer.py": "from .logging_api import Utilities\nimport structlog\n",
            "shadow.py": (
                "from .logging_api import Utilities\n"
                "Utilities = None\nimport structlog\n"
            ),
        }
        for relative, text in contents.items():
            (package / relative).write_text(text, encoding=c.DEFAULT_ENCODING)
        rule = (
            tm
            .ok(
                u.Infra.codemod_rule_plan(
                    mod_workspace, rule_ids=("ban-direct-structlog-import",)
                )
            )
            .rules[0]
            .model_copy(
                update={
                    "context": (
                        m.Infra.CodemodContextCondition(
                            variable="MODULE",
                            predicate=c.Infra.CodemodContextPredicate.IMPLEMENTATION_OWNER,
                            arg=(f"{namespace}.logging_api", "Utilities.fetch"),
                            holds=False,
                        ),
                    ),
                }
            )
        )
        _, modules = u.Infra.codemod_binding_requirements((rule,))
        snapshot = u.Infra.codemod_binding_snapshot(
            mod_workspace,
            tuple(
                tm.ok(
                    u.Cli.atomic_read_binary_file_state(package / name, required=True)
                )
                for name in contents
            ),
            modules,
        )
        facts = u.Infra.codemod_project_facts(mod_workspace, (rule,))
        with u.Infra.codemod_binding_project(
            mod_workspace, u.Infra.codemod_source_epoch(snapshot)
        ) as (project, sources):
            (package / f"{implementation}.py").write_text(
                "class NativeLogging:\n    pass\n", encoding=c.DEFAULT_ENCODING
            )
            for relative, admitted in (
                (f"{implementation}.py", False),
                ("_logging_base.py", False),
                ("_logging_sink.py", False),
                ("loggings.py", True),
                ("consumer.py", True),
                ("shadow.py", True),
            ):
                tm.that(
                    u.Infra.codemod_context_admits(
                        m.Infra.CodemodAdmission(
                            root=mod_workspace,
                            rule=rule,
                            file_path=package / relative,
                            captures={"MODULE": {"text": "structlog"}},
                            facts=facts,
                            snapshot=snapshot,
                        ),
                        project=project,
                        sources=sources,
                    ),
                    eq=admitted,
                    msg=relative,
                )

    @staticmethod
    @pytest.mark.parametrize("implementation", ["_native_hook", "moved_entrypoint"])
    @pytest.mark.parametrize("framework_import", [False, True])
    def test_isolated_execution_role_uses_original_producer_and_entrypoint(
        mod_workspace: Path, implementation: str, *, framework_import: bool
    ) -> None:
        """Only a declared native entrypoint with stdlib-only imports has the role."""
        namespace = u.Infra.project_package_name(mod_workspace)
        package = mod_workspace / c.Infra.DEFAULT_SRC_DIR / namespace
        hook = "import os\nclass Hook:\n    pass\nvalue = os.getenv('ROLE_PROBE')\n"
        contents = {
            "execution.py": (
                "from flext_cli import m\nE = m.Cli.PythonScriptExecution\n"
            ),
            f"{implementation}.py": hook
            + ("from flext_cli import u\n" if framework_import else ""),
            "public_hook.py": f"from .{implementation} import Hook\n",
            "producer.py": (
                "from .execution import E\nfrom .public_hook import Hook\n"
                "def command():\n"
                "    execution = E(module=Hook.__module__, "
                "role='isolated-stdlib')\n"
                "    return execution.python_flags, execution.module\n"
            ),
            "hook_client.py": hook,
            "bootstrap.py": hook,
            "application.py": "import os\nvalue = os.getenv('ROLE_PROBE')\n",
        }
        for relative, text in contents.items():
            (package / relative).write_text(text, encoding=c.DEFAULT_ENCODING)
        rule = (
            tm
            .ok(
                u.Infra.codemod_rule_plan(
                    mod_workspace, rule_ids=("ban-ambient-environ-read",)
                )
            )
            .rules[0]
            .model_copy(
                update={
                    "context": (
                        m.Infra.CodemodContextCondition(
                            variable="GETENV",
                            predicate=c.Infra.CodemodContextPredicate.ISOLATED_EXECUTION,
                            arg=(f"{namespace}.producer", "command"),
                            holds=False,
                        ),
                    ),
                }
            )
        )
        _, modules = u.Infra.codemod_binding_requirements((rule,))
        snapshot = u.Infra.codemod_binding_snapshot(
            mod_workspace,
            tuple(
                tm.ok(
                    u.Cli.atomic_read_binary_file_state(package / name, required=True)
                )
                for name in contents
            ),
            modules,
        )
        facts = u.Infra.codemod_project_facts(mod_workspace, (rule,))
        with u.Infra.codemod_binding_project(
            mod_workspace, u.Infra.codemod_source_epoch(snapshot)
        ) as (project, sources):
            (package / "producer.py").write_text(
                "def command():\n    return None\n", encoding=c.DEFAULT_ENCODING
            )
            (package / f"{implementation}.py").write_text(
                hook if framework_import else hook + "from flext_cli import u\n",
                encoding=c.DEFAULT_ENCODING,
            )
            for relative, admitted in (
                (f"{implementation}.py", framework_import),
                ("hook_client.py", True),
                ("bootstrap.py", True),
                ("application.py", True),
            ):
                tm.that(
                    u.Infra.codemod_context_admits(
                        m.Infra.CodemodAdmission(
                            root=mod_workspace,
                            rule=rule,
                            file_path=package / relative,
                            captures={"GETENV": {"text": "os.getenv"}},
                            facts=facts,
                            snapshot=snapshot,
                        ),
                        project=project,
                        sources=sources,
                    ),
                    eq=admitted,
                    msg=relative,
                )

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
    @pytest.mark.parametrize("surface", ["tests", "scripts", "examples"])
    def test_internal_tiers_are_own_namespaces(
        self,
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
            (tm.ok(u.Cli.atomic_read_binary_file_state(consumer, required=True)),),
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
