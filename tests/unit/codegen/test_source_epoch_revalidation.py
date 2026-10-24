"""Authenticated incremental source epochs and bounded concurrent-edit planning.

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

from flext_infra import config, p
from tests import c, m, t, tm, u


class TestsFlextInfraSourceEpochRevalidation:
    """Observe real filesystem edits through the public authenticated planner."""

    @staticmethod
    def test_native_source_membership_excludes_runtime_cache_children(
        tmp_path: Path,
    ) -> None:
        """Native child enumeration must not elect volatile interpreter byproducts."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        cache = package / "__pycache__"
        cache.mkdir()
        with u.Infra.facade_source_project(root) as (project, _, _):
            resource = project.get_folder(package.relative_to(root).as_posix())
            children = {child.name for child in resource.get_children()}
            tm.that(cache.name in children, eq=False)
            cache.rmdir()
            project.verify_source_states()
            tm.that(
                {child.name for child in resource.get_children()},
                eq=children,
            )

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
                "c = ChildConstants\n"
                '__all__ = ["ChildConstants", "c"]\n',
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
                    tm.that(provider in consumed, eq=True)
                    tm.that(base in consumed, eq=True)
                    tm.that(unrelated in consumed, eq=False)

    @staticmethod
    def test_source_adoption_does_not_adopt_permission_failures(
        tmp_path: Path,
    ) -> None:
        """An unreadable source is a causal IO error, not verified stale evidence."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "provider.py"
        source.write_text("VALUE = 1\n", encoding=c.DEFAULT_ENCODING)
        with u.Infra.facade_source_project(root) as (project, _, _):
            with project.source_consumption() as consumed:
                project.source_text(source)
            mode = source.stat().st_mode
            with project.source_successor() as successor:
                source.chmod(0)
                try:
                    with pytest.raises(ValueError, match="Permission denied"):
                        successor.adopt_source_consumption(consumed.receipt())
                finally:
                    source.chmod(mode)
            tm.that(project.source_epoch_failure, eq=None)

    @staticmethod
    def test_source_successor_preserves_original_consumer_exception(
        tmp_path: Path,
    ) -> None:
        """A consumer's syntax error escapes unchanged instead of being retried."""
        root, _package = u.Tests.create_lazy_init_workspace(tmp_path)
        original = SyntaxError("invalid consumer input")
        with (
            u.Infra.facade_source_project(root) as (project, _, _),
            pytest.raises(SyntaxError) as failure,
            project.source_successor(),
        ):
            raise original
        tm.that(failure.value is original, eq=True)

    @staticmethod
    def test_source_adoption_rejects_invalid_topology(tmp_path: Path) -> None:
        """An alias policy failure must escape, not turn into a drift receipt."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "provider.py"
        alias = package / "candidate.py"
        source.write_text("VALUE = 1\n", encoding=c.DEFAULT_ENCODING)
        with u.Infra.facade_source_project(root) as (project, _, _):
            with project.source_consumption() as consumed:
                tm.that(project.source_query(alias, "isfile"), eq=False)
            with project.source_successor() as successor:
                alias.symlink_to(source)
                try:
                    with pytest.raises(OSError, match="physical alias"):
                        successor.adopt_source_consumption(consumed.receipt())
                finally:
                    alias.unlink()

    @staticmethod
    def test_successor_adopts_only_authentic_independent_receipts(
        tmp_path: Path,
    ) -> None:
        """Old evidence stays immutable; adoption reissues only current evidence."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        changed = package / "changed.py"
        independent = package / "independent.py"
        changed.write_text("VALUE = 1\n", encoding=c.DEFAULT_ENCODING)
        independent.write_text("VALUE = 2\n", encoding=c.DEFAULT_ENCODING)
        contexts = ExitStack()
        project, _, _ = contexts.enter_context(u.Infra.facade_source_project(root))
        with project.source_consumption() as stale:
            project.source_text(changed)
        with project.source_consumption() as valid:
            original = project.source_state(independent)
        with project.source_consumption() as dependent:
            project.replay_source_consumption(stale.receipt())
            project.source_text(independent)
        changed.write_text("VALUE = 3\n", encoding=c.DEFAULT_ENCODING)
        with pytest.raises(ValueError, match="atomic source changed") as failure:
            contexts.close()
        tm.that(project.source_epoch_failure is failure.value, eq=True)
        with project.source_successor() as successor:
            adopted = tm.ok(successor.adopt_source_consumption(valid.receipt()))
            tm.that(adopted is valid.receipt(), eq=False)
            tm.that(
                successor.adopt_source_consumption(stale.receipt()).failure, eq=True
            )
            tm.that(
                successor.adopt_source_consumption(dependent.receipt()).failure, eq=True
            )
            with pytest.raises(ValueError, match="predecessor-issued"):
                successor.adopt_source_consumption(valid.receipt().model_copy())
            with successor.source_consumption() as replayed:
                successor.replay_source_consumption(adopted)
                tm.that(successor.source_state(independent) is original, eq=True)
                tm.that(successor.source_text(changed), eq="VALUE = 3\n")
            tm.that(original in replayed.receipt().inputs, eq=True)
            with (
                successor.source_consumption(),
                pytest.raises(ValueError, match="original epoch"),
            ):
                successor.replay_source_consumption(valid.receipt())
        tm.that(project.source_epoch_failure is failure.value, eq=True)
        tm.that(project.source_text(changed), eq="VALUE = 1\n")

    @staticmethod
    def test_successor_rechecks_absence_and_expanded_dependency_closure(
        tmp_path: Path,
    ) -> None:
        """A new election invalidates its actual consumer and replayed dependents."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        born = package / "born.py"
        contexts = ExitStack()
        project, _, _ = contexts.enter_context(u.Infra.facade_source_project(root))
        with project.source_consumption() as election:
            tm.that(project.source_query(born, "isfile"), eq=False)
        with project.source_consumption() as dependent:
            project.replay_source_consumption(election.receipt())
        born.write_text("VALUE = 1\n", encoding=c.DEFAULT_ENCODING)
        with pytest.raises(ValueError, match="source"):
            contexts.close()
        with project.source_successor() as successor:
            tm.that(
                successor.adopt_source_consumption(election.receipt()).failure, eq=True
            )
            tm.that(
                successor.adopt_source_consumption(dependent.receipt()).failure, eq=True
            )
            with successor.source_consumption() as expanded:
                tm.that(successor.source_query(born, "isfile"), eq=True)
                successor.source_text(born)
        born.write_text("VALUE = 2\n", encoding=c.DEFAULT_ENCODING)
        with successor.source_successor() as next_epoch:
            tm.that(
                next_epoch.adopt_source_consumption(expanded.receipt()).failure, eq=True
            )
            tm.that(next_epoch.source_text(born), eq="VALUE = 2\n")

    @staticmethod
    @pytest.mark.parametrize("topology", [False, True])
    def test_planner_recomputes_changed_closure_and_reuses_independent_decisions(
        tmp_path: Path,
        *,
        topology: bool,
    ) -> None:
        """Schedule a real post-planning edit without replacing production owners."""
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
        observed: list[m.Infra.CodegenPhaseAnalysis] = []
        edits = 0

        def observe(frame: FrameType, event: str, _value: p.AttributeProbe) -> None:
            nonlocal edits
            if event == "call" and frame.f_code.co_name == "_isolated_plan":
                directory = cast("Path", frame.f_locals["pkg_dir"])
                calls[directory] = calls.get(directory, 0) + 1
            if (
                event == "return"
                and frame.f_code.co_name == "_plan_attempt"
                and not edits
            ):
                result = cast("p.Result[m.Infra.CodegenPhaseAnalysis]", _value)
                observed.append(result.value)
                destination = left / "born.py" if topology else source
                destination.write_text(
                    "class After: pass\n__all__ = ['After']\n",
                    encoding=c.DEFAULT_ENCODING,
                )
                edits += 1

        previous = sys.getprofile()
        try:
            sys.setprofile(observe)
            if not config.Infra.codegen.source_replan_limit:
                with pytest.raises(ValueError, match="source"):
                    u.Tests.create_lazy_init_service(root).plan_files()
                return
            analysis = tm.ok(u.Tests.create_lazy_init_service(root).plan_files())
        finally:
            sys.setprofile(previous)
        tm.that(analysis.exception, eq=None)
        rendered = b"\n".join(file.desired_content or b"" for file in analysis.files)
        tm.that(b"After" in rendered, eq=True)
        tm.that(calls[left], eq=2)
        if not topology:
            tm.that(calls[right], eq=1)
            first = next(
                file
                for file in observed[0].files
                if file.path == right / c.Infra.INIT_PY
            )
            reused = next(file for file in analysis.files if file.path == first.path)
            tm.that(reused is first, eq=True)

    @staticmethod
    def test_continuous_edits_exhaust_configured_bound(tmp_path: Path) -> None:
        """Continuous writers leave a red original conflict, never an unbounded loop."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "provider.py"
        source.write_text(
            "class Before: pass\n__all__ = ['Before']\n", encoding=c.DEFAULT_ENCODING
        )
        edits = 0
        conflicts: list[BaseException] = []

        def observe(frame: FrameType, event: str, _value: p.AttributeProbe) -> None:
            nonlocal edits
            if event == "return" and frame.f_code.co_name == "verify_source_states":
                owner = cast("p.Infra.RopeProject", frame.f_locals["self"])
                conflict = owner.source_epoch_failure
                if conflict is not None:
                    conflicts.append(conflict)
            if event == "return" and frame.f_code.co_name == "_plan_attempt":
                edits += 1
                source.write_text(
                    f"class After{edits}: pass\n__all__ = ['After{edits}']\n",
                    encoding=c.DEFAULT_ENCODING,
                )

        previous = sys.getprofile()
        try:
            sys.setprofile(observe)
            with pytest.raises(ValueError, match="atomic source changed") as failure:
                u.Tests.create_lazy_init_service(root).plan_files()
        finally:
            sys.setprofile(previous)
        tm.that(edits, eq=config.Infra.codegen.source_replan_limit + 1)
        tm.that(failure.value is conflicts[0], eq=True)
