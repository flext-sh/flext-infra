"""Authenticated source epochs: a concurrent edit fails loud and is never re-planned.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from collections.abc import Callable, Generator
from contextlib import ExitStack, contextmanager
from pathlib import Path
from types import FrameType

import pytest

from flext_infra import config, p
from flext_infra.codegen import FlextInfraCodegenLazyInit, FlextInfraStagedPackage
from tests import c, m, t, tm, u


class TestsFlextInfraSourceEpochRevalidation:
    """Observe real filesystem edits through the public authenticated planner."""

    @staticmethod
    @pytest.mark.parametrize("dependent", [False, True])
    def test_original_publications_select_consumed_sources(
        tmp_path: Path, *, dependent: bool
    ) -> None:
        """Shared finalization replays original outputs, not the warmed read union."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "provider.py"
        unrelated = root / "unrelated.py"
        original = "class Published: pass\n__all__ = ['Published']\n"
        source.write_text(original, encoding=c.DEFAULT_ENCODING)
        unrelated.write_text(original, encoding=c.DEFAULT_ENCODING)
        publications: list[t.Pair[Path, m.Infra.CodegenPhaseAnalysis]] = []
        failures: list[m.Infra.CodegenPhaseAnalysis] = []
        with u.Infra.facade_source_project(
            root, source_publications=(publications, failures)
        ) as (project, _, _):
            tm.that(project.source_text(unrelated), eq=original)
            analysis = tm.ok(
                FlextInfraCodegenLazyInit(
                    repository_root=root,
                    project_scope_roots=(root,),
                    target_module=package.name,
                ).plan_files(source_project=project, source_publications=publications)
            )
            tm.that(analysis.exception, none=True)
            tm.that(len(publications), gt=0)
            (source if dependent else unrelated).write_text(
                "class Changed: pass\n", encoding=c.DEFAULT_ENCODING
            )
        tm.that(bool(failures), eq=dependent)
        if dependent:
            failure = failures[0]
            tm.that(str(failure.exception), has=str(source))
            tm.that(tm.not_none(failure.exception).__traceback__, none=False)
            tm.that(
                failure.failed_targets[0][1],
                where=lambda receipt: any(
                    receipt is original_receipt for _, original_receipt in publications
                ),
            )
        tm.that(len(analysis.files), gt=0)

    @staticmethod
    def test_publication_handoff_rejects_copied_native_receipt(tmp_path: Path) -> None:
        """A data-equivalent copy cannot replace the source issuer's evidence."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "provider.py"
        source.write_text("VALUE = 1\n", encoding=c.DEFAULT_ENCODING)
        publications: list[t.Pair[Path, m.Infra.CodegenPhaseAnalysis]] = []
        failures: list[m.Infra.CodegenPhaseAnalysis] = []
        with ExitStack() as contexts:
            project, _, _ = contexts.enter_context(
                u.Infra.facade_source_project(
                    root, source_publications=(publications, failures)
                )
            )
            with project.source_consumption() as consumption:
                project.source_text(source)
            publications.append((package, consumption.receipt().model_copy()))
            with pytest.raises(
                ValueError, match="does not belong to this original epoch"
            ):
                contexts.close()
        tm.that(failures, eq=[])

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
        excluded = tuple(
            package / name for name in config.Infra.codegen.source_scan_ignored
        )
        for cache in excluded:
            cache.mkdir()
        with ExitStack() as lifecycle:
            project, _, _ = lifecycle.enter_context(u.Infra.facade_source_project(root))
            resource = project.get_folder(package.relative_to(root).as_posix())
            children = {child.name for child in resource.get_children()}
            tm.that(any(cache.name in children for cache in excluded), truth=False)
            project.verify_source_states()
            for cache in excluded:
                cache.rmdir()
            tm.that(
                {child.name for child in resource.get_children()},
                eq=children,
            )
            project.verify_source_states()
            for cache in excluded:
                cache.mkdir()
            project.verify_source_states()
            lifecycle.close()

    @staticmethod
    @pytest.mark.parametrize("suffix", [".py", ".pyi"])
    def test_native_source_membership_rejects_added_source(
        tmp_path: Path, suffix: str
    ) -> None:
        """Source and prohibited stub additions remain membership changes."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        with ExitStack() as lifecycle:
            project, _, _ = lifecycle.enter_context(u.Infra.facade_source_project(root))
            resource = project.get_folder(package.relative_to(root).as_posix())
            resource.get_children()
            inputs = project.consumed_source_states()
            directories = project.consumed_source_directories()
            topology = project.consumed_source_topology()
            source_name = f"new_source{suffix}"
            destination = package / source_name
            destination.write_text("", encoding=c.DEFAULT_ENCODING)
            tampered = tuple(
                inventory.model_copy(
                    update={
                        "membership_queries": tuple(
                            tuple(sorted({*selection, source_name}))
                            for selection in inventory.membership_queries
                        ),
                    }
                )
                for inventory in directories
            )
            tm.fail(
                FlextInfraStagedPackage.plan_sources(
                    root,
                    {destination: "value = 1\n"},
                    options=m.Infra.StageSourceOptions(
                        inputs=inputs,
                        source_directories=tampered,
                        source_query_topology=topology,
                    ),
                ),
                has="differs from admitted policy",
            )
            tm.that(destination.read_text(encoding=c.DEFAULT_ENCODING), eq="")
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
        (provider_root / c.PYPROJECT_FILENAME).write_text(
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
            source_options=m.Infra.StageSourceOptions(
                inputs=(original,), declared_files=(declaration,)
            ),
        ) as (project, _, _):
            with project.source_consumption() as consumed:
                tm.that(project.source_text(source), eq=desired)
            witnesses = tuple(
                state for state in consumed.receipt().inputs if state.path == source
            )
            tm.that(witnesses, eq=(original,))
        tm.that(source.read_text(encoding=c.DEFAULT_ENCODING), eq="VALUE = 1\n")

    @staticmethod
    @contextmanager
    def _edit_after_package_planning(
        edit: Callable[[], int | None],
    ) -> Generator[t.MutableMappingKV[str, int]]:
        """Apply one real edit each time package planning returns; count both events.

        Yields:
            Counts keyed by ``plan_all_inits`` and by each planned package directory.

        """
        counts: t.MutableMappingKV[str, int] = {}

        def observe(frame: FrameType, event: str, _: p.AttributeProbe) -> None:
            name = frame.f_code.co_name
            if event == "call" and name == "_package_plan":
                key = str(frame.f_locals["pkg_dir"])
            elif event == "return" and name == "plan_all_inits":
                key = name
                edit()
            else:
                return
            counts[key] = counts.get(key, 0) + 1

        previous = sys.getprofile()
        sys.setprofile(observe)
        try:
            yield counts
        finally:
            sys.setprofile(previous)

    @staticmethod
    @pytest.mark.parametrize("topology", [False, True])
    def test_planner_retains_original_source_change(
        tmp_path: Path,
        *,
        topology: bool,
    ) -> None:
        """A failed dependency keeps its original cause and independent plans."""
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
        destination = left / "born.py" if topology else source
        with TestsFlextInfraSourceEpochRevalidation._edit_after_package_planning(
            lambda: destination.write_text(
                "class After: pass\n__all__ = ['After']\n",
                encoding=c.DEFAULT_ENCODING,
            )
        ) as counts:
            analysis = tm.ok(u.Tests.create_lazy_init_service(root).plan_files())
        tm.that(analysis.exception, none=False)
        tm.that(tm.not_none(analysis.exception).__traceback__, none=False)
        tm.that(str(analysis.exception), has="source")
        tm.that({path for path, _ in analysis.failed_targets}, has=left)
        tm.that({file.path for file in analysis.files}, has=right / c.Infra.INIT_PY)
        tm.that(counts["plan_all_inits"], eq=1)
        tm.that(counts[str(left)], eq=1)
        tm.that(counts[str(right)], eq=1)

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
        with (
            TestsFlextInfraSourceEpochRevalidation._edit_after_package_planning(
                lambda: source.write_text(
                    "class After: pass\n__all__ = ['After']\n",
                    encoding=c.DEFAULT_ENCODING,
                )
            ) as counts,
            pytest.raises(ValueError, match="source") as failure,
            u.Infra.facade_source_project(root) as (project, _, _),
        ):
            u.Tests.create_lazy_init_service(root).plan_files(source_project=project)
        tm.that(counts["plan_all_inits"], eq=1)
        tm.that(failure.value.__context__, none=True)

    @staticmethod
    def test_planner_does_not_retry_unreadable_repository_metadata(
        tmp_path: Path,
    ) -> None:
        """A failed metadata read retains its native cause, without retry."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        metadata = root / c.PYPROJECT_FILENAME
        (package / "provider.py").write_text(
            "class Published: pass\n__all__ = ['Published']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        mode = metadata.stat().st_mode
        try:
            with TestsFlextInfraSourceEpochRevalidation._edit_after_package_planning(
                lambda: metadata.chmod(0)
            ) as counts:
                analysis = tm.ok(u.Tests.create_lazy_init_service(root).plan_files())
            tm.that(isinstance(analysis.exception, PermissionError), truth=True)
            tm.that(tm.not_none(analysis.exception).__traceback__, none=False)
            tm.that(str(analysis.exception), has=metadata.name)
        finally:
            metadata.chmod(mode)
        tm.that(counts["plan_all_inits"], eq=1)

    @staticmethod
    def test_planner_retains_changed_repository_metadata(tmp_path: Path) -> None:
        """A real metadata edit retains its original failure and stays on disk."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        metadata = root / c.PYPROJECT_FILENAME
        edited = (
            metadata.read_text(encoding=c.DEFAULT_ENCODING)
            + "# Concurrent repository metadata edit\n"
        )
        (package / "provider.py").write_text(
            "class Published: pass\n__all__ = ['Published']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        with TestsFlextInfraSourceEpochRevalidation._edit_after_package_planning(
            lambda: metadata.write_text(edited, encoding=c.DEFAULT_ENCODING)
        ) as counts:
            analysis = tm.ok(u.Tests.create_lazy_init_service(root).plan_files())
        tm.that(analysis.exception, none=False)
        tm.that(tm.not_none(analysis.exception).__traceback__, none=False)
        tm.that(str(analysis.exception), has=str(metadata))
        tm.that(counts["plan_all_inits"], eq=1)
        tm.that(metadata.read_text(encoding=c.DEFAULT_ENCODING), eq=edited)
