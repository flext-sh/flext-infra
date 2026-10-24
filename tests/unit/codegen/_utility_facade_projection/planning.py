"""Public evidence for utility-facade source planning.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import sys
from functools import partial
from pathlib import Path

import pytest

from tests import c, m, p, r, t, tm, u
from tests.unit.codegen._utility_facade_projection.publication import (
    UtilityFacadePublication,
)


class UtilityFacadePlanning(UtilityFacadePublication):
    """Exercise source election, future owners and projection planning."""

    def _future_exposure_sources(
        self, tmp_path: Path, scope: str
    ) -> tuple[
        list[Path],
        list[m.Infra.RopeProjectLayout],
        t.MutableMappingKV[Path, str],
        list[str],
    ]:
        """Declare original and planned providers for each exposure scenario.

        Returns:
            Project roots, layouts, planned sources and runtime probe statements.

        """
        roots: list[Path] = []
        layouts: list[m.Infra.RopeProjectLayout] = []
        desired: t.MutableMappingKV[Path, str] = {}
        scripts: list[str] = []
        for suffix in ("first", "second") if scope == "independent" else ("first",):
            root, package = u.Tests.create_lazy_init_workspace(
                tmp_path,
                project_name=f"flext-{suffix}",
                package_name=f"flext_{suffix}",
            )
            roots.append(root)
            layout = tm.not_none(u.Infra.layout(root))
            layouts.append(layout)
            family = u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY)
            self._write(package / family.directory / c.Infra.INIT_PY, "")
            facade_class = f"{layout.class_stem}{family.suffix}"
            self._write(
                package / c.Infra.UTILITIES_PY,
                '"""Declared public utility composition."""\n\n'
                f"class {facade_class}:\n    pass\n\n"
                f"u = {facade_class}\n"
                f"__all__ = [{facade_class!r}, 'u']\n",
            )
            for module in ("first", "second") if scope == "collision" else ("first",):
                provider = package / family.directory / f"{module}.py"
                self._write(
                    provider,
                    '"""Original loose declaration."""\n\n'
                    "def read() -> str:\n"
                    f"    return {suffix!r}\n\n__all__ = ['read']\n",
                )
                desired[provider] = (
                    '"""Future structurally owned declaration."""\n\n'
                    "class Owner:\n"
                    "    @staticmethod\n"
                    "    def read() -> str:\n"
                    f"        return {suffix!r}\n\n__all__ = ['Owner']\n"
                )
            scripts.append(
                f"from {layout.package_name} import u as {suffix}\n"
                f"assert {suffix}.read() == {suffix!r}\n"
                f"assert any(base.__name__ == 'Owner' for base in {suffix}.__mro__)\n"
                f"assert not hasattr({suffix}, 'Owner')\n"
            )
        return roots, layouts, desired, scripts

    @staticmethod
    def _future_facade_plans(
        tmp_path: Path,
        scope: str,
        layouts: list[m.Infra.RopeProjectLayout],
        originals: tuple[m.Cli.AtomicFileState, ...],
        plans: tuple[m.Infra.CodegenFilePlan, ...],
    ) -> list[m.Infra.CodegenFilePlan]:
        """Render future facades while proving collisions preserve originals.

        Returns:
            Facade plans for the elected layouts, or none after a collision.

        """
        by_path = {state.path: state for state in originals}
        facade_plans: list[m.Infra.CodegenFilePlan] = []
        with u.Infra.facade_source_project(
            tmp_path,
            declared_files=plans,
            project_roots=tuple(layout.project_root for layout in layouts),
        ) as (project, sources):
            for layout in layouts:
                package = layout.package_dir
                if scope == "collision":
                    rejected = r[str | None].create_from_callable(
                        partial(
                            u.Infra.render_utility_facade,
                            package,
                            project=project,
                            sources=sources,
                        ),
                    )
                    tm.fail(rejected, has="Owner")
                    tm.ok(u.Cli.atomic_verify_binary_file_states(originals))
                    return []
                facade = package / c.Infra.UTILITIES_PY
                rendered = tm.not_none(
                    u.Infra.render_utility_facade(
                        package, project=project, sources=sources
                    ),
                )
                facade_plans.append(
                    m.Infra.CodegenFilePlan(
                        project=layout.project_root,
                        path=facade,
                        before=by_path[facade],
                        desired_content=rendered.encode(c.DEFAULT_ENCODING),
                        desired_mode=tm.not_none(by_path[facade].mode),
                    ),
                )
        return facade_plans

    @pytest.mark.parametrize("scope", ["single", "independent", "collision"])
    def test_future_exposure_uses_planned_owners(
        self, tmp_path: Path, scope: str
    ) -> None:
        """Project future MRO exports without publishing or conflating providers."""
        roots, layouts, desired, scripts = self._future_exposure_sources(
            tmp_path, scope
        )
        originals = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            for root in roots
            for path in (
                root / c.PYPROJECT_FILENAME,
                *u.Infra.discover_python_files(
                    root, workspace_excluded_top_dirs=frozenset()
                ),
            )
        )
        by_path = {state.path: state for state in originals}
        plans = tuple(
            m.Infra.CodegenFilePlan(
                project=next(root for root in roots if path.is_relative_to(root)),
                path=path,
                before=by_path[path],
                desired_content=source.encode(c.DEFAULT_ENCODING),
                desired_mode=tm.not_none(by_path[path].mode),
            )
            for path, source in desired.items()
        )
        facade_plans = self._future_facade_plans(
            tmp_path, scope, layouts, originals, plans
        )
        if scope == "collision":
            return
        service = u.Tests.create_lazy_init_service(tmp_path)
        service.project_scope_roots = tuple(roots)
        with u.Infra.facade_source_project(
            tmp_path,
            declared_files=(*plans, *facade_plans),
            project_roots=tuple(roots),
        ) as (project, _):
            combined = {
                plan.path: plan
                for plan in (
                    *plans,
                    *facade_plans,
                    *tm.ok(service.plan_files(source_project=project)),
                )
            }
        files = tuple(combined.values())
        tm.ok(u.Cli.atomic_verify_binary_file_states(originals))
        for plan in plans:
            projected = combined[plan.path]
            tm.that(projected.before, eq=plan.before)
            tm.that(projected.desired_content, eq=plan.desired_content)
        with u.Infra.facade_source_project(
            tmp_path,
            declared_files=files,
            project_roots=tuple(roots),
        ) as (project, _):
            for file in tm.ok(service.plan_files(source_project=project)):
                tm.that(file.desired_content, eq=combined[file.path].desired_content)
                tm.that(file.desired_mode, eq=combined[file.path].desired_mode)
        candidate = tmp_path / "candidate"
        for state in originals:
            if state.content is not None:
                self._write(
                    candidate / state.path.relative_to(tmp_path),
                    state.content.decode(c.DEFAULT_ENCODING),
                )
        for file in files:
            path = candidate / file.path.relative_to(tmp_path)
            if file.desired_content is None:
                path.unlink(missing_ok=True)
            else:
                self._write(path, file.desired_content.decode(c.DEFAULT_ENCODING))
        cold = tm.ok(
            u.Cli.run_raw(
                (sys.executable, "-c", "\n".join(scripts)),
                cwd=candidate,
                options=m.Cli.ProcessOptions(
                    env={
                        "PYTHONPATH": os.pathsep.join(
                            str(candidate / layout.src_dir.relative_to(tmp_path))
                            for layout in layouts
                        ),
                    },
                ),
            ),
        )
        tm.that(u.Cli.process_succeeded(cold.outcome), eq=True, msg=cold.stderr)
        tm.ok(u.Cli.atomic_verify_binary_file_states(originals))

    @classmethod
    def _render_and_execute_constants_consumer(
        cls,
        package: Path,
        facade: Path,
        *,
        expected_stdout: str,
    ) -> str:
        """Render the ``c`` family facade and read it back from a real consumer.

        Returns:
            The rendered facade source that was projected and executed.

        """
        service = u.Tests.create_lazy_init_service(package.parent.parent)
        tm.ok(u.Tests.materialize_lazy_init(service))
        rendered = tm.not_none(u.Infra.render_utility_facade(package, family="c"))
        cls._write(facade, rendered)
        output = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    "from flext_sample.constants import c\nprint(c.Sample.value)\n",
                ),
                options=m.Cli.ProcessOptions(
                    env={"PYTHONPATH": str(package.parent)},
                ),
            ),
        )
        tm.that(u.Cli.process_succeeded(output.outcome), eq=True, msg=output.stderr)
        tm.that(output.stdout.strip(), eq=expected_stdout)
        return rendered

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
        root, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-sample",
            package_name="flext_sample",
        )
        conflicted = (
            c.Infra.AUTOGEN_HEADER + "\n<<<<<<< HEAD\n=======\n>>>>>>> incoming\n"
        )
        self._write(package / "__init__.py", conflicted)
        self._write(
            package / "codemod" / consumer_name,
            "import sys\n"
            + import_statement
            + "\n\nsys.getdefaultencoding()\nu.Sample.plan_cutover()\n",
        )
        self._write(
            package / "_utilities" / "semantic_cutover.py",
            "class FlextSampleUtilitiesSemanticCutover:\n"
            "    @staticmethod\n"
            "    def plan_cutover() -> str:\n"
            "        return 'selected'\n"
            "class _PrivateCutover:\n"
            "    @staticmethod\n"
            "    def plan_cutover() -> str:\n"
            "        return 'private'\n"
            "__all__ = ['FlextSampleUtilitiesSemanticCutover']\n",
        )
        self._write(
            package / "_utilities" / "internal_owner.py",
            "class InternalOwner:\n"
            "    @staticmethod\n"
            "    def internal_step() -> None:\n"
            "        pass\n"
            "class OtherInternalOwner:\n"
            "    @staticmethod\n"
            "    def internal_step() -> None:\n"
            "        pass\n",
        )
        self._write(
            package / "_utilities" / "internal_consumer.py",
            "from flext_sample._utilities.internal_owner import InternalOwner\n"
            "InternalOwner.internal_step()\n",
        )
        facade = package / "utilities.py"
        self._write(
            package / "_utilities" / "existing.py",
            "class Existing:\n"
            "    @staticmethod\n"
            "    def existing_step() -> str:\n"
            "        return 'existing'\n__all__ = ['Existing']\n",
        )
        self._write(
            facade,
            "from flext_core import FlextUtilities\n"
            "from flext_sample._utilities.existing import Existing\n\n"
            "class FlextSampleUtilities(FlextUtilities):\n"
            "    class Sample(\n"
            "        Existing,\n"
            "    ):\n"
            "        pass\n\n"
            "u = FlextSampleUtilities\n\n"
            '__all__ = ["FlextSampleUtilities", "u"]\n',
        )
        initial_facade = tm.ok(
            u.Cli.atomic_read_binary_file_state(facade, required=True),
        )
        initial_init = tm.ok(
            u.Cli.atomic_read_binary_file_state(package / "__init__.py", required=True),
        )
        updated = tm.not_none(u.Infra.render_utility_facade(package))

        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(facade, required=True)),
            eq=initial_facade,
        )
        tm.that(
            tm.ok(
                u.Cli.atomic_read_binary_file_state(
                    package / "__init__.py",
                    required=True,
                ),
            ),
            eq=initial_init,
        )
        self._write(facade, updated)
        self._write(package / "__init__.py", "from flext_sample.utilities import u\n")
        tm.ok(u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)))
        result = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    (
                        "from flext_sample import u; "
                        "assert u.Sample.plan_cutover() == 'selected'; "
                        "assert u.Sample.existing_step() == 'existing'; "
                        "assert not hasattr(u.Sample, 'internal_step')"
                    ),
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            ),
        )
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True, msg=result.stderr)

    @pytest.mark.parametrize("member_path", ["provider", "libraries/provider"])
    def test_declared_workspace_import_resolves_without_adopting_foreign_owner(
        self,
        tmp_path: Path,
        member_path: str,
    ) -> None:
        """Sibling facade calls resolve from declarations, not ambient installs."""
        package = tmp_path / "receiver" / "src" / "flext_sample"
        foreign = tmp_path / member_path / "src" / "foreign_facade"
        self._write(
            tmp_path / ".gitmodules",
            '[submodule "receiver"]\n\tpath = receiver\n'
            f'[submodule "provider"]\n\tpath = {member_path}\n',
        )
        for directory, distribution in (
            (package.parent.parent, "receiver"),
            (foreign.parent.parent, "provider"),
        ):
            project = u.Tests.project_spec(distribution)
            self._write(
                directory / c.PYPROJECT_FILENAME,
                f'[project]\nname = "{distribution}"\nversion = "1.0.0"\n'
                f'authors = [{{name = "{project.author_name}", '
                f'email = "{project.author_email}"}}]\n'
                f'license = "{project.license}"\n'
                + (
                    'dependencies = ["provider"]\n'
                    if distribution == "receiver"
                    else ""
                ),
            )
        self._write(package / "__init__.py", "")
        self._write(foreign / "__init__.py", "from .utilities import u\n")
        self._write(
            foreign / "utilities.py",
            "class Foreign:\n    class Sample:\n"
            "        @staticmethod\n        def foreign_only() -> str:\n"
            "            return 'foreign'\nu = Foreign\n",
        )
        self._write(
            package / "foreign_consumer.py",
            "from foreign_facade import u\nu.Sample.foreign_only()\n",
        )
        self._write(
            package / "consumer.py",
            "from flext_sample import u\nu.Sample.required()\n",
        )
        self._write(
            package / "_utilities" / "owner.py",
            "class Owner:\n    @staticmethod\n"
            "    def required() -> str:\n        return 'local'\n"
            "__all__ = ['Owner']\n",
        )
        self._write(
            package / "_utilities" / "foreign.py",
            "class ForeignOwner:\n    @staticmethod\n"
            "    def foreign_only() -> str:\n        return 'wrong'\n",
        )
        facade = package / "utilities.py"
        original = (
            "class Facade:\n    class Sample:\n        pass\n"
            "u = Facade\n__all__ = ['Facade', 'u']\n"
        )
        self._write(facade, original)
        rendered = tm.not_none(u.Infra.render_utility_facade(package))
        tm.that(facade.read_text(), eq=original)
        self._write(facade, rendered)
        tm.ok(
            u.Tests.materialize_lazy_init(
                u.Tests.create_lazy_init_service(package.parent.parent),
            ),
        )
        tm.that(u.Infra.render_utility_facade(package), eq=rendered)
        result = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    (
                        "from flext_sample import u; "
                        "from flext_sample._utilities import Owner; "
                        "from foreign_facade import u as foreign; "
                        "assert u.Sample.required is Owner.required; "
                        "assert u.Sample.required() == 'local'; "
                        "assert not hasattr(u.Sample, 'foreign_only'); "
                        "assert foreign.Sample.foreign_only() == 'foreign'; "
                        "print('identities-proven')"
                    ),
                ),
                cwd=package.parent.parent,
                options=m.Cli.ProcessOptions(
                    env={
                        "PYTHONPATH": os.pathsep.join(
                            (str(package.parent), str(foreign.parent)),
                        ),
                    },
                ),
            ),
        )
        tm.that(u.Cli.process_succeeded(result.outcome), eq=True, msg=result.stderr)
        tm.that(result.stdout.strip(), eq="identities-proven")

    def test_unresolved_consumer_import_remains_a_consumer_failure(
        self,
        tmp_path: Path,
    ) -> None:
        """Declared projection preserves an unrelated consumer's native failure."""
        package = tmp_path / "src" / "flext_sample"
        self._write(package / "__init__.py", "")
        self._write(
            package / "_utilities" / "owner.py",
            "class Owner:\n    pass\n__all__ = ['Owner']\n",
        )
        self._write(
            package / "utilities.py",
            "class Facade:\n    class Sample:\n        pass\n\n"
            "u = Facade\n__all__ = ['Facade', 'u']\n",
        )
        consumer = package / "consumer.py"
        source = "from nonexistent_facade_owner import u\nu.Sample.required()\n"
        self._write(consumer, source)
        facade = package / "utilities.py"
        before = tm.ok(u.Cli.atomic_read_binary_file_state(facade, required=True))
        rendered = tm.not_none(u.Infra.render_utility_facade(package))
        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(facade, required=True)),
            eq=before,
        )
        self._write(facade, rendered)
        output = tm.ok(
            u.Cli.run_raw(
                (sys.executable, "-c", "import flext_sample.consumer"),
                options=m.Cli.ProcessOptions(
                    env={"PYTHONPATH": str(package.parent)},
                ),
            ),
        )
        tm.fail(u.Cli.process_succeeded(output.outcome))
        tm.that(
            output.stderr,
            has="ModuleNotFoundError: No module named 'nonexistent_facade_owner'",
        )
        tm.that(consumer.read_text(encoding=c.DEFAULT_ENCODING), eq=source)

    def test_inherited_aggregator_keeps_one_behavior_owner(
        self, tmp_path: Path
    ) -> None:
        """A pure MRO aggregate preserves its defining owner's public behavior."""
        root, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-sample",
            package_name="flext_sample",
        )
        provider = package.with_name(f"{package.name}_provider")
        self._write(package / "__init__.py", "from .utilities import u\n")
        self._write(
            package / "consumer.py", "from flext_sample import u\nu.Sample.read()\n"
        )
        self._write(
            provider / "reader.py",
            "class Reader:\n"
            "    @classmethod\n"
            "    def read(cls) -> str:\n"
            "        return cls._value()\n"
            "    @staticmethod\n"
            "    def _value() -> str:\n"
            "        return 'read'\n"
            "__all__ = ['Reader']\n",
        )
        self._write(
            provider / "__init__.py",
            f"from {provider.name}.reader import Reader\n__all__ = ['Reader']\n",
        )
        self._write(
            package / "_utilities" / "document.py",
            f"from {provider.name} import Reader\n"
            "class Document(Reader):\n    pass\n__all__ = ['Document']\n",
        )
        facade = package / "utilities.py"
        source = (
            "from ._utilities.document import Document\n"
            "class Utilities:\n"
            "    class Sample(Document):\n        pass\n"
            "u = Utilities\n__all__ = ['Utilities', 'u']\n"
        )
        self._write(facade, source)
        rendered = tm.not_none(u.Infra.render_utility_facade(package))
        tm.that(facade.read_text(), eq=source)
        self._write(facade, rendered)
        tm.ok(u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)))
        tm.that(u.Infra.render_utility_facade(package), eq=rendered)
        output = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    "from flext_sample import u\nprint(u.Sample.read())\n",
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            )
        )
        tm.that(u.Cli.process_succeeded(output.outcome), eq=True, msg=output.stderr)
        tm.that(output.stdout.strip(), eq="read")
        tm.that(facade.read_text(), eq=rendered)

    def test_rejects_competing_declared_owners(self, tmp_path: Path) -> None:
        """Fail before projection when two publishers claim one public name."""
        _, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-sample",
            package_name="flext_sample",
        )
        family = u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY)
        self._write(package / "__init__.py", "")
        for module in ("first", "second"):
            self._write(
                package / family.directory / f"{module}.py",
                "class Owner:\n"
                "    @staticmethod\n"
                "    def plan_cutover() -> None:\n"
                "        pass\n"
                "__all__ = ['Owner']\n",
            )
        facade = package / c.Infra.UTILITIES_PY
        original = (
            "from flext_cli import u\n\n"
            "class FlextSampleUtilities(u):\n"
            "    class Sample(u):\n"
            "        pass\n\n"
            "u = FlextSampleUtilities\n\n"
            '__all__ = ["FlextSampleUtilities", "u"]\n'
        )
        self._write(facade, original)

        with pytest.raises(ValueError, match="Competing declared facade owner names"):
            u.Infra.render_utility_facade(package)
        tm.that(facade.read_text(), eq=original)

    def test_rejects_competing_inherited_namespaces(self, tmp_path: Path) -> None:
        """Reject an ambiguous facade without dropping either declaration body."""
        _, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-sample",
            package_name="flext_sample",
        )
        family = u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY)
        facade = package / c.Infra.UTILITIES_PY
        source = (
            "from flext_cli import u\n"
            "class FlextSampleUtilities(u):\n"
            "    class Sample(u):\n        declaration = 'first'\n"
            "    class Extra(u):\n        declaration = 'second'\n"
            "u = FlextSampleUtilities\n"
            '__all__ = ["FlextSampleUtilities", "u"]\n'
        )
        self._write(facade, source)
        (package / family.directory).mkdir()

        with pytest.raises(ValueError, match="competing inherited utility namespaces"):
            u.Infra.render_utility_facade(package)
        tm.that(facade.read_text(encoding=c.DEFAULT_ENCODING), eq=source)

    def test_unmaterialized_family_projects_executable_owner_composition(
        self,
        tmp_path: Path,
        native_consumer: p.Tests.NativeConsumer,
    ) -> None:
        """Plan virtual family owners before executing their generated public facade."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        family = u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY)
        owners = package / family.directory
        facade = package / f"{family.module}.py"
        original = (
            "class Utilities:\n    pass\nu = Utilities\n__all__ = ['Utilities', 'u']\n"
        )
        self._write(facade, original)
        self._write(
            package / c.Infra.INIT_PY,
            f"from .{family.module} import Utilities, u\n"
            "__all__ = ['Utilities', 'u']\n",
        )
        planned = {
            owners / c.Infra.INIT_PY: "",
            owners / "base.py": (
                "class BaseOwner:\n"
                "    marker = 'base'\n"
                "    class Contract:\n        pass\n"
                "    @classmethod\n    def read(cls) -> str:\n"
                "        return cls.marker\n"
                "__all__ = ['BaseOwner']\n"
            ),
            owners / "child.py": (
                "from .base import BaseOwner\n"
                "class ChildOwner(BaseOwner):\n    marker = 'child'\n"
                "__all__ = ['ChildOwner']\n"
            ),
        }
        with u.Infra.facade_source_project(root, planned_sources=planned) as (
            project,
            sources,
        ):
            rendered = tm.not_none(
                u.Infra.render_utility_facade(package, project=project, sources=sources)
            )
        tm.fail(owners.exists())
        tm.that(facade.read_text(encoding=c.DEFAULT_ENCODING), eq=original)
        with u.Infra.facade_source_project(
            root, planned_sources={**planned, facade: rendered}
        ) as (project, sources):
            tm.that(
                u.Infra.render_utility_facade(
                    package, project=project, sources=sources
                ),
                eq=rendered,
            )
        tm.fail(owners.exists())
        for path, source in planned.items():
            self._write(path, source)
        self._write(facade, rendered)
        native_consumer(
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            f"from {package.name} import Utilities, u\n"
            f"from {package.name}.{family.directory}.base import BaseOwner\n"
            f"from {package.name}.{family.directory}.child import ChildOwner\n"
            "assert u is Utilities\n"
            "assert u.__mro__[1:3] == (ChildOwner, BaseOwner)\n"
            "assert u.Contract is ChildOwner.Contract is BaseOwner.Contract\n"
            "assert u.read() == 'child'\n"
            "class Receiver(u):\n    marker = 'receiver'\n"
            "assert Receiver.read() == 'receiver'\n",
            cwd=root,
        )

    @pytest.mark.parametrize("virtual", [False, True])
    def test_rejects_owners_without_a_public_facade(
        self, tmp_path: Path, *, virtual: bool
    ) -> None:
        """Utility owners without a facade have no public surface at all."""
        package = tmp_path / "src" / "flext_sample"
        package.mkdir(parents=True)
        family = u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY)
        owner = package / family.directory / "owner.py"
        source = "class Owner:\n    pass\n__all__ = ['Owner']\n"
        if not virtual:
            self._write(owner, source)

        with (
            u.Infra.facade_source_project(
                tmp_path, planned_sources={owner: source} if virtual else {}
            ) as (project, sources),
            pytest.raises(ValueError, match="have no public facade"),
        ):
            u.Infra.render_utility_facade(package, project=project, sources=sources)

    @staticmethod
    @pytest.mark.parametrize("present", [False, True])
    def test_empty_owner_directory_needs_no_facade(
        tmp_path: Path, *, present: bool
    ) -> None:
        """An absent or preflight-created empty family needs no public surface."""
        package = tmp_path / "src" / "flext_sample"
        package.mkdir(parents=True)
        if present:
            family = u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY)
            (package / family.directory).mkdir()
        tm.that(u.Infra.render_utility_facade(package), eq=None)

    @pytest.mark.parametrize(
        "consumer_source",
        ["def invalid(:\n", "class TestInvalid(\n"],
    )
    def test_unrelated_malformed_consumer_does_not_block_declared_projection(
        self,
        tmp_path: Path,
        consumer_source: str,
    ) -> None:
        """Compose valid declarations without analyzing unrelated test bodies."""
        _, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-sample",
            package_name="flext_sample",
        )
        family = u.Infra.facade_family_declared_by(c.Infra.CONSTANTS_PY)
        self._write(package / c.Infra.INIT_PY, "")
        self._write(
            package / family.directory / "owner.py",
            "class Owner:\n    value = 'declared'\n__all__ = ['Owner']\n",
        )
        facade = package / c.Infra.CONSTANTS_PY
        source = (
            f"from flext_sample.{family.directory}.owner import Owner\n"
            "class Facade:\n    class Sample(Owner):\n        pass\n"
            "c = Facade\n__all__ = ['Facade', 'c']\n"
        )
        self._write(facade, source)
        consumer = package / "unit" / "test_incomplete.py"
        self._write(consumer, consumer_source)

        self._render_and_execute_constants_consumer(
            package,
            facade,
            expected_stdout="declared",
        )
        tm.that(consumer.read_text(encoding=c.DEFAULT_ENCODING), eq=consumer_source)

    def test_stale_projected_base_order_is_regenerated_from_owner_ancestry(
        self,
        tmp_path: Path,
    ) -> None:
        """An invalid old projection cannot override its valid source owners."""
        _, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-sample",
            package_name="flext_sample",
        )
        family = u.Infra.facade_family_declared_by(c.Infra.CONSTANTS_PY)
        self._write(package / c.Infra.INIT_PY, "")
        self._write(
            package / family.directory / "base_owner.py",
            "class BaseOwner:\n    value = 'base'\n__all__ = ['BaseOwner']\n",
        )
        self._write(
            package / family.directory / "child_owner.py",
            f"from flext_sample.{family.directory}.base_owner import BaseOwner\n"
            "class ChildOwner(BaseOwner):\n    value = 'child'\n"
            "__all__ = ['ChildOwner']\n",
        )
        facade = package / c.Infra.CONSTANTS_PY
        self._write(
            facade,
            f"from flext_sample.{family.directory}.base_owner import BaseOwner\n"
            f"from flext_sample.{family.directory}.child_owner import ChildOwner\n"
            "class Facade:\n    class Sample(BaseOwner, ChildOwner):\n        pass\n"
            "c = Facade\n__all__ = ['Facade', 'c']\n",
        )
        rendered = self._render_and_execute_constants_consumer(
            package,
            facade,
            expected_stdout="child",
        )
        repeated = u.Infra.render_utility_facade(package, family="c")
        tm.that(
            repeated,
            eq=rendered,
            msg=f"Initial projection: {rendered!r}\nRepeated projection: {repeated!r}",
        )

    @pytest.mark.parametrize("generated", [True, False])
    def test_initializer_ownership_controls_consumer_parsing(
        self,
        tmp_path: Path,
        *,
        generated: bool,
    ) -> None:
        """Only generated propagation is excluded from authored consumer analysis."""
        package = tmp_path / "src" / "flext_sample"
        self._write(
            package / "_utilities" / "owner.py",
            "class Owner:\n    pass\n__all__ = ['Owner']\n",
        )
        original = (
            "from flext_sample._utilities.owner import Owner\n"
            "class Facade:\n    class Domain(Owner):\n        pass\n"
            "u = Facade\n__all__ = ['Facade', 'u']\n"
        )
        self._write(package / "utilities.py", original)
        conflicted = (
            c.Infra.AUTOGEN_HEADER + "\n" if generated else ""
        ) + "<<<<<<< HEAD\n=======\n>>>>>>> incoming\n"
        initializer = package / c.Infra.INIT_PY
        self._write(initializer, conflicted)

        if generated:
            tm.not_none(u.Infra.render_utility_facade(package))
            tm.that((package / "utilities.py").read_text(), eq=original)
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

    def test_nested_namespace_owner_is_never_also_composed_whole(
        self,
        tmp_path: Path,
    ) -> None:
        """An owner composed through its nested namespace class stays nested only.

        Premise: ``Owner.Sample`` already carries the owner's contribution to
        the ``Sample`` namespace; composing ``Owner`` whole beside it duplicates
        the owner in the MRO. A projection that carries both is repaired.
        """
        _, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-sample",
            package_name="flext_sample",
        )
        family = u.Infra.facade_family_declared_by(c.Infra.CONSTANTS_PY)
        self._write(package / c.Infra.INIT_PY, "")
        self._write(
            package / family.directory / "nested_owner.py",
            "class NestedOwner:\n"
            "    class Sample:\n        value = 'nested'\n"
            "__all__ = ['NestedOwner']\n",
        )
        facade = package / c.Infra.CONSTANTS_PY
        self._write(
            facade,
            f"from flext_sample.{family.directory}.nested_owner import NestedOwner\n"
            "class Facade:\n"
            "    class Sample(NestedOwner, NestedOwner.Sample):\n        pass\n"
            "c = Facade\n__all__ = ['Facade', 'c']\n",
        )
        rendered = self._render_and_execute_constants_consumer(
            package,
            facade,
            expected_stdout="nested",
        )
        tm.that(rendered, has="class Sample(NestedOwner.Sample)")
        tm.that(u.Infra.render_utility_facade(package, family="c"), eq=rendered)

    def test_type_facade_imports_its_owner_through_the_family_package(
        self,
        tmp_path: Path,
    ) -> None:
        """The projected type facade keeps its private owner alias.

        Premise: the owner is imported through the family package's lazy
        exports; a per-module import was rewritten to the package form and
        lost its ``as`` alias, leaving a class that inherits its own name.
        """
        root, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-sample",
            package_name="flext_sample",
        )
        family = u.Infra.facade_family_declared_by(c.Infra.TYPINGS_PY)
        owners = package / family.directory
        self._write(
            owners / "sample.py",
            '"""Sample type owner."""\n\n'
            "class FlextSampleTypes:\n"
            "    class Sample:\n        type Name = str\n\n"
            "t = FlextSampleTypes\n\n"
            "__all__: list[str] = ['FlextSampleTypes', 't']\n",
        )
        self._write(
            owners / c.Infra.INIT_PY,
            "from flext_sample._typings.sample import FlextSampleTypes, t\n"
            "__all__ = ['FlextSampleTypes', 't']\n",
        )
        facade = package / c.Infra.TYPINGS_PY
        self._write(
            facade,
            '"""Sample public types."""\n\n'
            "class FlextSampleTypes:\n    pass\n\n"
            "t = FlextSampleTypes\n\n"
            "__all__: list[str] = ['FlextSampleTypes', 't']\n",
        )
        with u.Infra.facade_source_project(root) as (project, sources):
            rendered = u.Infra.render_type_facade(
                package, facade, dict(sources), project=project
            )
        tm.that(
            rendered,
            has=(
                f"from flext_sample.{family.directory} import "
                "FlextSampleTypes as _FlextSampleTypes"
            ),
        )
        tm.that(rendered, has="class FlextSampleTypes(_FlextSampleTypes)")
        self._write(facade, rendered)
        with u.Infra.facade_source_project(root) as (project, sources):
            tm.that(
                u.Infra.render_type_facade(
                    package, facade, dict(sources), project=project
                ),
                eq=rendered,
            )
        output = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    (
                        "from flext_sample.typings import t\n"
                        "from flext_sample._typings import FlextSampleTypes\n"
                        "assert t.__mro__[1] is FlextSampleTypes\n"
                        "print(t.Sample.Name.__value__.__name__)\n"
                    ),
                ),
                options=m.Cli.ProcessOptions(
                    env={"PYTHONPATH": str(package.parent)},
                ),
            ),
        )
        tm.that(u.Cli.process_succeeded(output.outcome), eq=True, msg=output.stderr)
        tm.that(output.stdout.strip(), eq="str")
