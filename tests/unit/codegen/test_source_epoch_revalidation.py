"""Authenticated source epochs: a concurrent edit fails loud and is never re-planned.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from contextlib import ExitStack
from pathlib import Path
from types import FrameType
from typing import cast

import pytest

from flext_infra import p
from tests import c, m, t, tm, u


class TestsFlextInfraSourceEpochRevalidation:
    """Observe real filesystem edits through the public authenticated planner."""

    @staticmethod
    def test_warm_empty_exports_retain_source_dependency(tmp_path: Path) -> None:
        """Sibling ancestry warms an empty module without losing its byte proof."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        consumer = package / "a_consumer"
        provider = package / "z_provider"
        for directory in (consumer, provider):
            directory.mkdir()
            (directory / c.Infra.INIT_PY).write_text("", encoding=c.DEFAULT_ENCODING)
        source = provider / "provider.py"
        source.write_text(
            "class Base: pass\n__all__: list[str] = []\n",
            encoding=c.DEFAULT_ENCODING,
        )
        (consumer / "consumer.py").write_text(
            f"from {package.name}.z_provider.provider import Base\n"
            "class Consumer(Base): pass\n__all__ = ['Consumer']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        with u.Infra.facade_source_project(root) as (project, _, _):
            analysis = tm.ok(
                u.Tests.create_lazy_init_service(root).plan_files(
                    source_project=project
                )
            )
            tm.that(analysis.exception, none=True)
            planned = next(
                file
                for file in analysis.files
                if file.path == provider / c.Infra.INIT_PY
            )
            tm.that(
                source in {state.path for state in planned.source_states},
                truth=True,
            )

    @staticmethod
    def test_native_source_membership_excludes_runtime_cache_children(
        tmp_path: Path,
    ) -> None:
        """Native child enumeration must not elect volatile interpreter byproducts."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        cache = package / "__pycache__"
        cache.mkdir()
        with ExitStack() as lifecycle:
            project, _, _ = lifecycle.enter_context(u.Infra.facade_source_project(root))
            resource = project.get_folder(package.relative_to(root).as_posix())
            children = {child.name for child in resource.get_children()}
            tm.that(cache.name in children, truth=False)
            project.verify_source_states()
            cache.rmdir()
            tm.that(
                {child.name for child in resource.get_children()},
                eq=children,
            )
            with pytest.raises(ValueError, match="source directory membership changed"):
                lifecycle.close()

    @staticmethod
    @pytest.mark.parametrize("nested_consumer", [False, True])
    def test_published_native_ancestry_survives_warm_export_name_cache(
        tmp_path: Path,
        *,
        nested_consumer: bool,
    ) -> None:
        """Two-hop supplier bases stay proven without consuming unrelated modules."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        provider_root = tmp_path / "upstream-provider"
        provider_package = provider_root / "src" / "upstream_provider"
        provider_package.mkdir(parents=True)
        (provider_root / "pyproject.toml").write_text(
            '[project]\nname = "upstream-provider"\nversion = "0.0.1"\n',
            encoding=c.DEFAULT_ENCODING,
        )
        (provider_package / c.Infra.INIT_PY).write_text(
            'from .provider import c\n__all__ = ["c"]\n',
            encoding=c.DEFAULT_ENCODING,
        )
        base = provider_package / "base.py"
        base.write_text(
            "class BaseConstants(list): pass\n", encoding=c.DEFAULT_ENCODING
        )
        provider = provider_package / "provider.py"
        provider.write_text(
            "from .base import BaseConstants\n"
            "class ProviderConstants(BaseConstants): pass\n"
            'c = ProviderConstants\n__all__ = ["c"]\n',
            encoding=c.DEFAULT_ENCODING,
        )
        unrelated = provider_package / "unrelated.py"
        unrelated.write_text("class Unrelated: pass\n", encoding=c.DEFAULT_ENCODING)
        (package / c.Infra.CONSTANTS_PY).write_text(
            "from upstream_provider import c as upstream_c\n"
            "class FlextTestProjectConstants(upstream_c): pass\n"
            "c = FlextTestProjectConstants\n"
            '__all__ = ["FlextTestProjectConstants", "c"]\n',
            encoding=c.DEFAULT_ENCODING,
        )
        consumers = [package]
        if nested_consumer:
            child = package / "child"
            child.mkdir()
            (child / c.Infra.CONSTANTS_PY).write_text(
                "from upstream_provider import c as upstream_c\n"
                "class ChildConstants(upstream_c): pass\n"
                '__all__ = ["ChildConstants"]\n',
                encoding=c.DEFAULT_ENCODING,
            )
            consumers.append(child)
        with u.Infra.facade_source_project(
            tmp_path, project_roots=(root, provider_root)
        ) as (project, _, _):
            for _ in range(2):
                analysis = tm.ok(
                    u.Tests.create_lazy_init_service(root).plan_files(
                        source_project=project
                    )
                )
                tm.that(analysis.exception, eq=None)
                for consumer in consumers:
                    planned = next(
                        file
                        for file in analysis.files
                        if file.path == consumer / c.Infra.INIT_PY
                    )
                    consumed = {state.path for state in planned.source_states}
                    tm.that(provider in consumed, truth=True)
                    tm.that(base in consumed, truth=True)
                    tm.that(unrelated in consumed, truth=False)

    @staticmethod
    def test_declared_overlay_retains_repeated_original_witness(
        tmp_path: Path,
    ) -> None:
        """A destination also consumed as input retains one original authority."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "provider.py"
        source.write_text("VALUE = 1\n", encoding=c.DEFAULT_ENCODING)
        original = tm.ok(u.Cli.atomic_read_binary_file_state(source, required=True))
        desired = "VALUE = 2\n"
        declaration = m.Infra.CodegenFilePlan(
            project=root,
            path=source,
            desired_content=desired.encode(c.DEFAULT_ENCODING),
            desired_mode=original.mode,
            before=original,
            source_states=(original,),
        )
        with u.Infra.facade_source_project(
            root,
            source_states=(original,),
            declared_files=(declaration,),
        ) as (project, _, _):
            with project.source_consumption() as consumed:
                tm.that(project.source_text(source), eq=desired)
            witnesses = tuple(
                state for state in consumed.receipt().inputs if state.path == source
            )
            tm.that(witnesses, eq=(original,))
        tm.that(source.read_text(encoding=c.DEFAULT_ENCODING), eq="VALUE = 1\n")

    @staticmethod
    @pytest.mark.parametrize("topology", [False, True])
    def test_planner_raises_original_source_change(
        tmp_path: Path,
        *,
        topology: bool,
    ) -> None:
        """A real edit after planning raises once; no package is planned again."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        left = package / "left"
        right = package / "right"
        left.mkdir()
        right.mkdir()
        source = left / "provider.py"
        source.write_text(
            "class Before: pass\n__all__ = ['Before']\n", encoding=c.DEFAULT_ENCODING
        )
        (right / "provider.py").write_text(
            "class Independent: pass\n__all__ = ['Independent']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        calls: t.MutableMappingKV[Path, int] = {}
        edits = 0

        def observe(frame: FrameType, event: str, _: p.AttributeProbe) -> None:
            nonlocal edits
            if event == "call" and frame.f_code.co_name == "_package_plan":
                directory = cast("Path", frame.f_locals["pkg_dir"])
                calls[directory] = calls.get(directory, 0) + 1
            if (
                event == "return"
                and frame.f_code.co_name == "plan_all_inits"
                and not edits
            ):
                destination = left / "born.py" if topology else source
                destination.write_text(
                    "class After: pass\n__all__ = ['After']\n",
                    encoding=c.DEFAULT_ENCODING,
                )
                edits += 1

        previous = sys.getprofile()
        try:
            sys.setprofile(observe)
            with pytest.raises(ValueError, match="source"):
                u.Tests.create_lazy_init_service(root).plan_files()
        finally:
            sys.setprofile(previous)
        tm.that(edits, eq=1)
        tm.that(calls[left], eq=1)
        tm.that(calls[right], eq=1)

    @staticmethod
    def test_injected_planner_propagates_original_source_change(
        tmp_path: Path,
    ) -> None:
        """The injected epoch raises its own failure; the owner adds no other one."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "provider.py"
        source.write_text(
            "class Before: pass\n__all__ = ['Before']\n", encoding=c.DEFAULT_ENCODING
        )
        edits = 0

        def observe(frame: FrameType, event: str, _: p.AttributeProbe) -> None:
            nonlocal edits
            if (
                event == "return"
                and frame.f_code.co_name == "plan_all_inits"
                and not edits
            ):
                source.write_text(
                    "class After: pass\n__all__ = ['After']\n",
                    encoding=c.DEFAULT_ENCODING,
                )
                edits += 1

        previous = sys.getprofile()
        try:
            sys.setprofile(observe)
            with (
                pytest.raises(ValueError, match="source") as failure,
                u.Infra.facade_source_project(root) as (project, _, _),
            ):
                u.Tests.create_lazy_init_service(root).plan_files(
                    source_project=project
                )
        finally:
            sys.setprofile(previous)
        tm.that(edits, eq=1)
        tm.that(failure.value.__context__, none=True)

    @staticmethod
    def test_planner_does_not_retry_unreadable_repository_metadata(
        tmp_path: Path,
    ) -> None:
        """A failed metadata observation escapes with its native cause, without retry."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        metadata = root / c.PYPROJECT_FILENAME
        (package / "provider.py").write_text(
            "class Published: pass\n__all__ = ['Published']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        mode = metadata.stat().st_mode
        attempts = 0

        def observe(frame: FrameType, event: str, _: p.AttributeProbe) -> None:
            nonlocal attempts
            if event == "return" and frame.f_code.co_name == "plan_all_inits":
                attempts += 1
                metadata.chmod(0)

        previous = sys.getprofile()
        try:
            sys.setprofile(observe)
            with pytest.raises(PermissionError, match="Permission denied"):
                u.Tests.create_lazy_init_service(root).plan_files()
        finally:
            sys.setprofile(previous)
            metadata.chmod(mode)
        tm.that(attempts, eq=1)

    @staticmethod
    def test_planner_raises_changed_repository_metadata(tmp_path: Path) -> None:
        """A real metadata edit during planning raises once and is kept on disk."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        metadata = root / c.PYPROJECT_FILENAME
        original = metadata.read_text(encoding=c.DEFAULT_ENCODING)
        (package / "provider.py").write_text(
            "class Published: pass\n__all__ = ['Published']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        edits = 0

        def observe(frame: FrameType, event: str, _: p.AttributeProbe) -> None:
            nonlocal edits
            if (
                event == "return"
                and frame.f_code.co_name == "plan_all_inits"
                and not edits
            ):
                metadata.write_text(
                    original + "# Concurrent repository metadata edit\n",
                    encoding=c.DEFAULT_ENCODING,
                )
                edits += 1

        previous = sys.getprofile()
        try:
            sys.setprofile(observe)
            with pytest.raises(ValueError, match="source"):
                u.Tests.create_lazy_init_service(root).plan_files()
        finally:
            sys.setprofile(previous)
        tm.that(edits, eq=1)
        tm.that(
            metadata.read_text(encoding=c.DEFAULT_ENCODING),
            eq=original + "# Concurrent repository metadata edit\n",
        )
