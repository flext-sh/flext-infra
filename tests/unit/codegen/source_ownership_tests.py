"""Declared project queries and immutable dependency payload boundaries.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
import threading
from contextlib import ExitStack, nullcontext
from pathlib import Path
from re import escape
from types import FrameType

import pytest

from flext_infra import config, infra
from flext_infra.codegen import FlextInfraCodegenLazyInit, FlextInfraStagedPackage
from tests import c, m, p, tm, u


class TestsFlextInfraSourceOwnership:
    """Exercise the native source reader through its public planning facade."""

    @staticmethod
    @pytest.mark.parametrize("width", ["short", "wrapped"])
    def test_future_local_exports_keep_the_elected_package_resource(
        tmp_path: Path, installed_dependency_path: Path, width: str
    ) -> None:
        """An ambient regular package cannot replace an elected future declaration."""
        root = u.Tests.git_repository(tmp_path / "planned")
        package_name = "future_owned"
        if width == "wrapped":
            limit = u.Infra.native_tool_setting(
                config.Infra.tooling, "ruff", "line-length", int
            )
            while len(f"    from {package_name}._constants.settings import (") <= limit:
                package_name += "_x"
        provider = installed_dependency_path / package_name
        provider.mkdir()
        (provider / c.Infra.INIT_PY).write_text(
            "__all__ = []\n", encoding=c.DEFAULT_ENCODING
        )
        (root / c.PYPROJECT_FILENAME).write_text(
            "[project]\nname = 'future-owned'\nversion = '1.0.0'\n"
            "authors = [{name = 'Native Source Test'}]\n"
            "license = 'MIT'\n"
            "[tool.hatch.build.targets.wheel]\n"
            f"packages = ['src/{package_name}']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        package = root / c.Infra.DEFAULT_SRC_DIR / package_name
        settings = package / "_constants" / "settings.py"
        planned = {
            settings: (
                "class FlextFutureOwnedSettingsConstants: pass\n"
                "c = FlextFutureOwnedSettingsConstants\n"
                "__all__ = ['FlextFutureOwnedSettingsConstants', 'c']\n"
            ),
        }
        with u.Infra.facade_source_project(root, planned_sources=planned) as (
            project,
            _,
            _,
        ):
            tm.that(project.source_query(settings, "isfile"), eq=True)
            tm.that(
                Path(tm.not_none(project.find_module(package_name)).real_path),
                eq=provider,
            )
            analysis = tm.ok(
                FlextInfraCodegenLazyInit(repository_root=root).plan_files(
                    source_project=project
                )
            )
            tm.that(analysis.issues, eq=())
            target = next(
                file
                for file in analysis.files
                if file.path == settings.parent / c.Infra.INIT_PY
            )
            text = tm.not_none(target.desired_content).decode(c.DEFAULT_ENCODING)
            tm.that(text, contains="FlextFutureOwnedSettingsConstants")
            tm.ok(u.Cli.atomic_verify_binary_file_states(analysis.inputs))
            tm.fail(package.exists())

    @staticmethod
    @pytest.mark.parametrize(
        "surface",
        [
            c.Infra.CodegenConformSurface.LAZY_INIT,
            c.Infra.CodegenConformSurface.FACADES,
        ],
    )
    def test_scoped_publication_does_not_consume_unselected_tracked_content(
        tmp_path: Path,
        session_runtime: p.Tests.SessionRuntime,
        surface: c.Infra.CodegenConformSurface,
    ) -> None:
        """Unselected tracked guides may change after sealing source effects."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        layout = tm.not_none(u.Infra.layout(root))
        family = u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY)
        utilities = package / c.Infra.UTILITIES_PY
        u.Tests.write_lazy_init_namespace_module(
            utilities, class_name=f"{layout.class_stem}{family.suffix}", alias="u"
        )
        owner = package / family.directory
        owner.mkdir()
        (owner / c.Infra.INIT_PY).write_text("", encoding=c.DEFAULT_ENCODING)
        (owner / "reader.py").write_text(
            "class Reader:\n"
            "    @staticmethod\n"
            "    def read() -> int:\n"
            "        return 1\n"
            "__all__ = ['Reader']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        guide = root / "docs" / "guides" / "execution-context.md"
        guide.parent.mkdir(parents=True)
        guide.write_text("# Original unselected guide\n", encoding=c.DEFAULT_ENCODING)
        u.Tests.git_bootstrap(root, ("add", "--", str(guide.relative_to(root))))
        tm.ok(
            u.Tests.create_python_environment(
                root,
                dependency_projects=u.Tests.python_dependency_projects(root),
                session_runtime=session_runtime,
            )
        )
        changed = threading.Event()

        def observe(frame: FrameType, event: str, _value: p.AttributeProbe) -> None:
            if (
                event == "return"
                and frame.f_code.co_qualname
                == "FlextInfraStagedPackage._source_plan_project"
                and not changed.is_set()
            ):
                changed.set()
                guide.write_text(
                    "# Concurrent guide update\n", encoding=c.DEFAULT_ENCODING
                )

        request = m.Infra.CodegenGenerateRequest(
            root=root,
            what=surface,
            module=(
                package.name
                if surface == c.Infra.CodegenConformSurface.LAZY_INIT
                else f"{package.name}.{utilities.stem}"
            ),
        )
        previous, previous_threads = sys.getprofile(), threading.getprofile()
        try:
            sys.setprofile(observe)
            threading.setprofile(observe)
            tm.ok(infra.codegen_generate(request))
        finally:
            sys.setprofile(previous)
            threading.setprofile(previous_threads)
        tm.ok(changed.is_set())
        target = (
            package / c.Infra.INIT_PY
            if surface == c.Infra.CodegenConformSurface.LAZY_INIT
            else utilities
        )
        published = target.read_bytes()
        tm.ok(infra.codegen_generate(request))
        tm.that(target.read_bytes(), eq=published)
        tm.that(
            u.Tests.run_lazy_init_probe(
                f"from {package.name}.utilities import u\n"
                f"assert u.__name__ == {f'{layout.class_stem}{family.suffix}'!r}\n"
                + (
                    "assert u.read() == 1\n"
                    if surface == c.Infra.CodegenConformSurface.FACADES
                    else f"import {package.name} as package\nassert package.u is u\n"
                )
                + "print('consumed')\n",
                python_paths=(str(layout.src_dir),),
                cwd=root,
            ),
            eq=["consumed"],
        )
        tm.that(
            guide.read_text(encoding=c.DEFAULT_ENCODING),
            eq="# Concurrent guide update\n",
        )

    @staticmethod
    @pytest.mark.parametrize(
        "cohort",
        [
            "unselected",
            "explicit-document",
            "explicit-template",
            "config",
            "python",
            "provider",
            "provider-unimported",
            "inode",
        ],
    )
    def test_source_election_keeps_only_actual_content_dependencies(
        tmp_path: Path, cohort: str
    ) -> None:
        """Explicit evidence and complete Python closure remain immutable."""
        root = u.Tests.git_repository(tmp_path)
        package = u.Tests.src_package(
            root,
            "elected_receiver",
            pyproject="[project]\nname = 'elected-receiver'\nversion = '1.0.0'\n",
        )
        provider = u.Tests.src_package(
            root / "provider",
            "elected_provider",
            pyproject="[project]\nname = 'elected-provider'\nversion = '1.0.0'\n",
        )
        (root / c.Infra.GITMODULES).write_text(
            '[submodule "provider"]\n\tpath = provider\n', encoding=c.DEFAULT_ENCODING
        )
        target = package / "consumer.py"
        target.write_text(
            "from elected_provider import VALUE\nRESULT = VALUE\n",
            encoding=c.DEFAULT_ENCODING,
        )
        dependency = provider / c.Infra.INIT_PY
        dependency.write_text("VALUE = 1\n", encoding=c.DEFAULT_ENCODING)
        payload = {
            "unselected": root / "docs" / "guide.md",
            "explicit-document": root / "docs" / "guide.md",
            "explicit-template": root / "templates" / "view.j2",
            "config": root / c.Infra.CODEGEN_CONFIG_DIR / "resource.txt",
            "python": package / "support.py",
            "provider": dependency,
            "provider-unimported": provider / "clock.py",
            "inode": dependency,
        }[cohort]
        payload.parent.mkdir(parents=True, exist_ok=True)
        payload.write_text("VALUE = 1\n", encoding=c.DEFAULT_ENCODING)
        u.Tests.git_bootstrap(root, ("add", "--", str(payload.relative_to(root))))
        before = tm.ok(u.Cli.atomic_read_binary_file_state(payload, required=True))
        plan = tm.ok(
            FlextInfraStagedPackage.plan_sources(
                root,
                {target: target.read_text(encoding=c.DEFAULT_ENCODING) + "\n"},
                options=m.Infra.StageSourceOptions(
                    inputs=(before,) if cohort.startswith("explicit-") else (),
                ),
            )
        )
        tm.that(
            payload in {state.path for state in plan.inputs}, eq=cohort != "unselected"
        )
        if cohort == "inode":
            payload.rename(payload.with_suffix(".preserved"))
            payload.write_bytes(tm.not_none(before.content))
        else:
            payload.write_text("VALUE = 2\n", encoding=c.DEFAULT_ENCODING)
        current = FlextInfraStagedPackage.source_inputs_current(plan)
        if cohort == "unselected":
            tm.ok(current)
        else:
            tm.fail(current)
            tm.that(current.error, has=str(payload))

    @staticmethod
    @pytest.mark.parametrize(
        "mutation", ["membership", "negative-frontier", "provider"]
    )
    def test_scoped_election_retains_original_query_frontiers(
        tmp_path: Path, mutation: str
    ) -> None:
        """Removing unrelated content never removes topology or provider witnesses."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        frontier = package / "pending" / "provider.py"
        with u.Infra.facade_source_project(root) as (project, _, _):
            tm.fail(project.source_query(frontier, "isfile"))
            receipt = consumed.receipt()
        target = package / "consumer.py"
        plan = tm.ok(
            FlextInfraStagedPackage.plan_sources(
                root,
                {target: "VALUE = 1\n"},
                options=m.Infra.StageSourceOptions(
                    inputs=receipt.inputs,
                ),
            )
        )
        if mutation == "membership":
            (package / "arrived.py").write_text(
                "VALUE = 2\n", encoding=c.DEFAULT_ENCODING
            )
        elif mutation == "negative-frontier":
            frontier.parent.mkdir()
        else:
            u.Tests.src_package(
                root / "new-provider",
                "new_provider",
                pyproject="[project]\nname = 'new-provider'\nversion = '1.0.0'\n",
            )
            (root / c.Infra.GITMODULES).write_text(
                '[submodule "new-provider"]\n\tpath = new-provider\n',
                encoding=c.DEFAULT_ENCODING,
            )
        tm.fail(FlextInfraStagedPackage.source_inputs_current(plan))
        tm.fail(target.exists())

    @staticmethod
    @pytest.mark.parametrize("nested", [False, True])
    def test_dependency_membership_is_not_project_ownership(
        tmp_path: Path, *, nested: bool
    ) -> None:
        """The elected runtime has the same query boundary inside or outside root."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        runtime = (root if nested else tmp_path) / "dependency_runtime"
        runtime.mkdir()
        source = runtime / "provider.py"
        source.write_text("class Provider:\n    pass\n", encoding=c.DEFAULT_ENCODING)
        candidate = runtime / "new_package" / "__init__.py"
        with (
            tm.scope(python_paths=(str(runtime),)),
            u.Infra.facade_source_project(root) as (project, _, _),
        ):
            tm.fail(project.source_query(candidate, "isfile"))
            tm.that(project.source_children(runtime), has=source)
            tm.fail(project.source_query(candidate, "isfile"))
            tm.that(scope.receipt().source_query_topology, eq=())
            tm.that(scope.receipt().source_directories, eq=())
            candidate.parent.mkdir()
            candidate.write_text("", encoding=c.DEFAULT_ENCODING)
            tm.that(project.source_text(source), eq="class Provider:\n    pass\n")
            tm.that(
                {state.path for state in project.consumed_source_states()}, has=source
            )
            tm.that(project.source_query(package / "absent.py", "isfile"), eq=False)

    @staticmethod
    @pytest.mark.parametrize("nested", [False, True])
    @pytest.mark.parametrize("payload", ["provider.py", "provider.dist-info/METADATA"])
    def test_dependency_payload_attestation_remains_immutable(
        tmp_path: Path, payload: str, *, nested: bool
    ) -> None:
        """Dependency source and metadata reads reject byte changes in either layout."""
        root, _ = u.Tests.create_lazy_init_workspace(tmp_path)
        runtime = (root if nested else tmp_path) / "dependency_runtime"
        source = runtime / payload
        source.parent.mkdir(parents=True)
        source.write_text("original\n", encoding=c.DEFAULT_ENCODING)
        with tm.scope(python_paths=(str(runtime),)), ExitStack() as contexts:
            project, _, _ = contexts.enter_context(u.Infra.facade_source_project(root))
            tm.that(project.source_text(source), eq="original\n")
            source.write_text("changed\n", encoding=c.DEFAULT_ENCODING)
            with pytest.raises(ValueError, match=escape(str(source))):
                contexts.close()

    @staticmethod
    @pytest.mark.parametrize(c.MergeStrategy.REPLACE, [False, True])
    def test_declared_source_ancestry_remains_authenticated(
        tmp_path: Path, *, replace: bool
    ) -> None:
        """A runtime import root cannot demote a more specific declared source root."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        candidate = package / "absent" / "provider.py"
        expectation = (
            pytest.raises(ValueError, match="source directory ancestry changed")
            if replace
            else nullcontext()
        )
        with (
            tm.scope(python_paths=(str(root),)),
            expectation,
            u.Infra.facade_source_project(root) as (project, _, _),
        ):
            tm.fail(project.source_query(candidate, "isfile"))
            tm.that(
                any(
                    item.target == candidate.parent
                    for item in scope.receipt().source_query_topology
                ),
                eq=True,
            )
            if replace:
                candidate.parent.mkdir()
