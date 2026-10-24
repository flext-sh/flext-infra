"""Own-package codemod role contracts: family bases, layer zero and process owners.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import pytest

from flext_infra import config
from flext_infra.codemod import FlextInfraModGateEngine
from tests import c, m, t, tm, u
from tests.unit.codemod.context_own_package_support import (
    TestsFlextInfraContextOwnPackageSupport,
)


class TestsFlextInfraCodemodContextOwnPackageRoles:
    """Source roles follow native definitions, never filenames."""

    @staticmethod
    @pytest.mark.parametrize(
        ("relative", "admitted"),
        [("_utilities/base.py", True), ("_utilities/_behavior/base.py", False)],
    )
    def test_family_base_role_requires_the_immediate_declared_facade(
        mod_workspace: Path, relative: str, *, admitted: bool
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
        rule = TestsFlextInfraContextOwnPackageSupport.private_import_rule().model_copy(
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
    @pytest.mark.parametrize("name", ["flext-role-probe", "external-role-probe"])
    @pytest.mark.parametrize("surface", ["src", "tests", "scripts", "examples"])
    @pytest.mark.parametrize("attached", [False, True])
    def test_layer_zero_role_uses_the_actual_member_namespace(
        tmp_path: Path, name: str, surface: str, *, attached: bool
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
        rule = TestsFlextInfraContextOwnPackageSupport.private_import_rule().model_copy(
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
            content = (
                f"import {package.name}\n"
                f"import {package.name}._settings\n"
                f"import {package.name}._models\n"
                f"import {package.name}._utilities\n\n{source}"
                if relative == "consumer.py"
                else source
            )
            path = package / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.parent != package:
                (path.parent / c.Infra.INIT_PY).write_text(
                    "", encoding=c.DEFAULT_ENCODING
                )
            path.write_text(content, encoding=c.DEFAULT_ENCODING)
            sources.append(path)
            original[path] = content
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

    @staticmethod
    def test_bound_layer_zero_role_uses_original_native_module_identity(
        mod_workspace: Path,
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
        rule = TestsFlextInfraContextOwnPackageSupport.private_import_rule().model_copy(
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
                for name in (c.Infra.INIT_PY, *contents)
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
                for name in (c.Infra.INIT_PY, *contents)
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
                            arg=(f"{namespace}.producer", c.HandlerMode.COMMAND),
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
                for name in (c.Infra.INIT_PY, *contents)
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
    def test_pytest_plugin_modules_are_layer_zero() -> None:
        """Installed pytest11 plugins are layer zero; ordinary modules stay consumers."""
        plugins = u.Infra.pytest_plugin_modules()
        tm.that(plugins, empty=False)
        for module in plugins:
            tm.that(u.Infra.import_module_role(module), eq="layer0", msg=module)
        packaged = sorted(module for module in plugins if "." in module)
        ordinary = f"{packaged[0].partition('.')[0]}.ordinary_pytest_consumer"
        tm.that(ordinary in plugins, eq=False)
        tm.that(u.Infra.import_module_role(ordinary), eq="consumer")
