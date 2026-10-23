"""Generation preserves authored runtime outside declared family composition.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from contextlib import ExitStack, nullcontext
from pathlib import Path
from re import escape
from typing import Literal

import pytest

from flext_infra import codegen, config, workspace
from tests import c, m, p, tm, u


class TestsFlextInfraFacadeAuthoredRuntime:
    """Exercise preservation through generation and a fresh public consumer."""

    @staticmethod
    @pytest.mark.parametrize("consume", [False, True])
    def test_capture_pins_originals_without_promoting_unused_inputs(
        tmp_path: Path,
        *,
        consume: bool,
    ) -> None:
        """Prefetch is not consumption; actual readers still get the original epoch."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "provider.py"
        text = "__all__ = []\n"
        source.write_text(text, encoding=c.DEFAULT_ENCODING)
        expectation = (
            pytest.raises(ValueError, match=escape(str(source)))
            if consume
            else nullcontext()
        )
        with expectation, u.Infra.facade_source_project(root) as binding:
            project = binding[0]
            with project.source_capture():
                original = project.source_state(source)
            tm.that(
                source in {state.path for state in project.consumed_source_states()},
                eq=False,
            )
            source.write_text(
                text + "# Changed after capture\n", encoding=c.DEFAULT_ENCODING
            )
            with project.source_consumption() as scope:
                if consume:
                    tm.that(project.source_text(source), eq=text)
            tm.that(scope.receipt().inputs, eq=(original,) if consume else ())

    @staticmethod
    @pytest.mark.parametrize("directory", [False, True])
    @pytest.mark.parametrize("descendant", ["child.py", "nested/child.py"])
    def test_negative_query_below_original_file_uses_native_ancestor_proof(
        tmp_path: Path,
        descendant: str,
        *,
        directory: bool,
    ) -> None:
        """Reject a file-to-directory change, not irrelevant ancestor file bytes."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "provider.py"
        source.write_text("__all__ = []\n", encoding=c.DEFAULT_ENCODING)
        expectation = (
            pytest.raises(ValueError, match=escape(str(source)))
            if directory
            else nullcontext()
        )
        with expectation, u.Infra.facade_source_project(root) as binding:
            project = binding[0]
            with project.source_consumption() as scope:
                predicates: tuple[Literal["exists", "isfile", "isdir"], ...] = (
                    "exists",
                    "isfile",
                    "isdir",
                )
                for predicate in predicates:
                    tm.that(
                        project.source_query(source / descendant, predicate), eq=False
                    )
            tm.that(scope.receipt().inputs, eq=())
            tm.that(
                any(
                    inventory.root.path == package
                    and (source.name, "isdir") in inventory.queries
                    for inventory in scope.receipt().source_directories
                ),
                eq=True,
            )
            if directory:
                source.unlink()
                source.mkdir()
            else:
                source.write_text(
                    "# Changed bytes, still not a directory\n",
                    encoding=c.DEFAULT_ENCODING,
                )

    @staticmethod
    def test_declared_retirement_and_binary_reads_keep_original_effect_inputs(
        tmp_path: Path,
    ) -> None:
        """Use the native selected view without restoring retired or binary bytes."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "provider.py"
        dependency = package / "dependency.py"
        binary = package / "opaque.bin"
        source.write_text("__all__ = []\n", encoding=c.DEFAULT_ENCODING)
        dependency.write_text("__all__ = []\n", encoding=c.DEFAULT_ENCODING)
        binary.write_bytes(b"\x00\xff")
        original = tm.ok(u.Cli.atomic_read_binary_file_state(source))
        incoming = tm.ok(u.Cli.atomic_read_binary_file_state(dependency))
        opaque = tm.ok(u.Cli.atomic_read_binary_file_state(binary))
        plans = (
            m.Infra.CodegenFilePlan(
                project=root,
                path=source,
                before=original,
                desired_content=None,
                desired_mode=None,
                source_states=(incoming,),
            ),
            m.Infra.CodegenFilePlan(
                project=root,
                path=binary,
                before=opaque,
                desired_content=b"\xff\x00",
                desired_mode=opaque.mode,
                source_states=(incoming,),
            ),
        )
        with u.Infra.facade_source_project(
            root, source_states=(original, incoming, opaque), declared_files=plans
        ) as binding:
            project = binding[0]
            with project.source_consumption() as scope:
                tm.fail(project.source_query(source, "isfile"))
                tm.fail(source in project.source_children(package))
                tm.that(project.source_bytes(binary), eq=b"\xff\x00")
            states = {state.path: state for state in scope.receipt().inputs}
            tm.that(states[source], eq=original)
            tm.that(states[dependency], eq=incoming)
            tm.that(states[binary], eq=opaque)
            with pytest.raises(FileNotFoundError, match="retired"):
                project.source_bytes(source)
        tm.that(binary.read_bytes(), eq=opaque.content)
        tm.that(source.read_bytes(), eq=original.content)

    @staticmethod
    def test_repeated_overlay_reads_keep_transitive_original_bytes(
        tmp_path: Path,
    ) -> None:
        """Every overlay consumer rejects a changed original producer dependency."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "provider.py"
        dependency = package / "dependency.py"
        source.write_text("__all__ = []\n", encoding=c.DEFAULT_ENCODING)
        dependency.write_text("__all__ = []\n", encoding=c.DEFAULT_ENCODING)
        original = tm.ok(u.Cli.atomic_read_binary_file_state(source))
        incoming = tm.ok(u.Cli.atomic_read_binary_file_state(dependency))
        proposed = b"class Published: pass\n__all__ = ['Published']\n"
        plan = m.Infra.CodegenFilePlan(
            project=root,
            path=source,
            before=original,
            desired_content=proposed,
            desired_mode=original.mode,
            source_states=(incoming,),
        )
        with ExitStack() as contexts:
            project, _, _ = contexts.enter_context(
                u.Infra.facade_source_project(root, declared_files=(plan,)),
            )
            with project.source_consumption() as first:
                tm.that(project.source_bytes(source), eq=proposed)
            with project.source_consumption() as repeated:
                tm.that(project.source_bytes(source), eq=proposed)
            dependency.write_text(
                "# Changed producer input\n", encoding=c.DEFAULT_ENCODING
            )
            for scope in (first, repeated):
                tm.that(
                    {state.path for state in scope.receipt().inputs},
                    has=dependency,
                )
                rejected = u.Cli.atomic_verify_binary_file_states(
                    scope.receipt().inputs
                )
                tm.ok(rejected.failure)
                tm.that(rejected.error, contains=str(dependency))
            tm.that(source.read_bytes(), eq=original.content)
            with pytest.raises(ValueError, match=escape(str(dependency))):
                contexts.close()

    @staticmethod
    def test_isolated_native_consumers_share_original_transitive_receipts(
        tmp_path: Path,
    ) -> None:
        """Warming one PyCore cannot hide provider reads from another artifact."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        provider = package / "provider.py"
        tm.ok(
            u.Cli.atomic_write_text_file(
                provider,
                "class Provider: pass\n__all__ = ['Provider']\n",
            ),
        )
        for name in ("first", "second"):
            tm.ok(
                u.Cli.atomic_write_text_file(
                    package / f"{name}.py",
                    f"from {package.name}.provider import Provider\n"
                    "class Consumer(Provider): pass\n__all__ = ['Consumer']\n",
                ),
            )
        with u.Infra.facade_source_project(root) as (project, _, _):
            warmed = u.Infra.require_semantic_module(
                project.get_module(f"{package.name}.first"),
            )
            tm.that(
                len(warmed.get_attribute("Consumer").get_object().get_superclasses()),
                eq=1,
            )
            with (
                project.source_consumption() as first,
                project.source_consumer() as consumer,
            ):
                module = u.Infra.require_semantic_module(
                    consumer.get_module(f"{package.name}.first"),
                )
                tm.that(
                    len(
                        module.get_attribute("Consumer").get_object().get_superclasses()
                    ),
                    eq=1,
                )
            with (
                project.source_consumption() as second,
                project.source_consumer() as consumer,
            ):
                module = u.Infra.require_semantic_module(
                    consumer.get_module(f"{package.name}.second"),
                )
                tm.that(
                    len(
                        module.get_attribute("Consumer").get_object().get_superclasses()
                    ),
                    eq=1,
                )
            first_provider = tuple(
                state for state in first.receipt().inputs if state.path == provider
            )
            second_provider = tuple(
                state for state in second.receipt().inputs if state.path == provider
            )
            tm.that(len(first_provider), eq=1)
            tm.that(second_provider, eq=first_provider)
            with (
                project.source_consumption() as replayed,
                project.source_consumer() as consumer,
            ):
                consumer.replay_source_consumption(first.receipt())
            tm.that(replayed.receipt().inputs, eq=first.receipt().inputs)

    @staticmethod
    def test_source_scopes_retain_repeated_original_reads(tmp_path: Path) -> None:
        """A cache consumer receives the original bytes, never a cumulative delta."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "provider.py"
        unrelated = package / "unrelated.py"
        tm.ok(u.Cli.atomic_write_text_file(source, "__all__ = []\n"))
        tm.ok(u.Cli.atomic_write_text_file(unrelated, "__all__ = []\n"))
        with u.Infra.facade_source_project(root) as (project, _, _):
            with project.source_consumption() as first:
                original = project.source_state(source)
            with project.source_consumption() as separate:
                project.source_state(unrelated)
            with project.source_consumption() as repeated:
                tm.that(project.source_state(source), eq=original)
            with project.source_consumption() as consumer:
                project.replay_source_consumption(first.receipt())
            tm.that(first.receipt().inputs, eq=(original,))
            tm.that(repeated.receipt().inputs, eq=(original,))
            tm.that(consumer.receipt().inputs, eq=(original,))
            tm.that(
                tuple(state.path for state in separate.receipt().inputs),
                eq=(unrelated,),
            )

    @staticmethod
    def test_source_scopes_keep_exact_negative_queries(tmp_path: Path) -> None:
        """Repeated misses do not inherit unrelated selectors or membership reads."""
        root, _ = u.Tests.create_lazy_init_workspace(tmp_path)
        with u.Infra.facade_source_project(root) as (project, _, _):
            with project.source_consumption() as first:
                tm.fail(project.root.has_child("missing.py"))
            with project.source_consumption():
                tm.fail(project.root.has_child("other.py"))
                project.root.get_children()
            with project.source_consumption() as repeated:
                tm.fail(project.root.has_child("missing.py"))
            with project.source_consumption() as cached:
                project.replay_source_consumption(first.receipt())
            for scope in (first, repeated, cached):
                inventories = tuple(
                    inventory
                    for inventory in scope.receipt().source_directories
                    if inventory.root.path == root
                )
                tm.that(len(inventories), eq=1)
                tm.that(inventories[0].queries, eq=(("missing.py", "exists"),))
                tm.fail(inventories[0].membership_queried)

    @staticmethod
    @pytest.mark.parametrize("absent_parent", [False, True])
    def test_aggregate_source_queries_coalesce_roots_without_widening_consumers(
        tmp_path: Path,
        *,
        absent_parent: bool,
    ) -> None:
        """Union repeated parent witnesses only at the aggregate receipt boundary."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        parent = package / "absent" if absent_parent else package
        with u.Infra.facade_source_project(root) as (project, _, _):
            with project.source_consumption() as first:
                tm.fail(project.source_query(parent / "first.py", "exists"))
            with project.source_consumption() as separate:
                tm.fail(project.source_query(parent / "second.py", "isfile"))
                tm.fail(project.source_query(parent / "first.py", "isdir"))
                if absent_parent:
                    with pytest.raises(FileNotFoundError):
                        project.source_children(parent)
                else:
                    project.source_children(parent)
            with project.source_consumption() as repeated:
                project.replay_source_consumption(first.receipt())
                tm.fail(project.source_query(parent / "first.py", "exists"))
            for scope in (first, repeated):
                receipts = (
                    tuple(
                        item
                        for item in scope.receipt().source_query_topology
                        if item.target == parent
                    )
                    if absent_parent
                    else tuple(
                        item
                        for item in scope.receipt().source_directories
                        if item.root.path == parent
                    )
                )
                tm.that(len(receipts), eq=1)
                tm.that(receipts[0].queries, eq=(("first.py", "exists"),))
                tm.fail(receipts[0].membership_queried)
            aggregate = (
                tuple(
                    item
                    for item in project.consumed_source_topology()
                    if item.target == parent
                )
                if absent_parent
                else tuple(
                    item
                    for item in project.consumed_source_directories()
                    if item.root.path == parent
                )
            )
            tm.that(len(aggregate), eq=1)
            tm.that(
                aggregate[0].queries,
                eq=(
                    ("first.py", "exists"),
                    ("first.py", "isdir"),
                    ("second.py", "isfile"),
                ),
            )
            tm.ok(aggregate[0].membership_queried)
            separate_receipts = (
                separate.receipt().source_query_topology
                if absent_parent
                else separate.receipt().source_directories
            )
            tm.that(
                any(
                    ("first.py", "exists") in item.queries for item in separate_receipts
                ),
                eq=False,
            )

    @staticmethod
    def test_source_scopes_reject_unissued_and_incomplete_receipts(
        tmp_path: Path,
    ) -> None:
        """A copied receipt and an unfinished consumer cannot authenticate a hit."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        with u.Infra.facade_source_project(root) as (project, _, _):
            with project.source_consumption() as scope:
                project.source_state(package / "absent.py", required=False)
                with pytest.raises(ValueError, match="no completed receipt"):
                    scope.receipt()
            with pytest.raises(ValueError, match="original epoch"):
                project.replay_source_consumption(scope.receipt().model_copy())
            with pytest.raises(ValueError, match="active consumer"):
                project.replay_source_consumption(scope.receipt())
            failure = RuntimeError("consumer failed")
            scopes: list[p.Infra.RopeSourceConsumption] = []

            def fail_consumer() -> None:
                with project.source_consumption() as failed:
                    scopes.append(failed)
                    project.source_state(package / "absent.py", required=False)
                    raise failure

            with pytest.raises(RuntimeError, match="consumer failed") as caught:
                fail_consumer()
            tm.ok(caught.value is failure)
            with pytest.raises(ValueError, match="no completed receipt"):
                scopes[0].receipt()

    @staticmethod
    def test_nested_source_scopes_propagate_original_receipts(tmp_path: Path) -> None:
        """Nested cache work belongs both to its own result and to its consumer."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "provider.py"
        tm.ok(u.Cli.atomic_write_text_file(source, "__all__ = []\n"))
        with u.Infra.facade_source_project(root) as (project, _, _):
            with (
                project.source_consumption() as outer,
                project.source_consumption() as inner,
            ):
                project.source_state(source)
                tm.fail(project.root.has_child("missing.py"))
            tm.that(outer.receipt().inputs, eq=inner.receipt().inputs)
            tm.that(
                outer.receipt().source_directories,
                eq=inner.receipt().source_directories,
            )
            tm.that(
                outer.receipt().source_query_topology,
                eq=inner.receipt().source_query_topology,
            )

    @staticmethod
    def test_replayed_source_receipt_never_recaptures_changed_bytes(
        tmp_path: Path,
    ) -> None:
        """A replay retains old evidence and the epoch verifier rejects the edit."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "provider.py"
        tm.ok(u.Cli.atomic_write_text_file(source, "__all__ = []\n"))
        with ExitStack() as contexts:
            project, _, _ = contexts.enter_context(u.Infra.facade_source_project(root))
            with project.source_consumption() as provider:
                original = project.source_state(source)
            tm.ok(u.Cli.atomic_write_text_file(source, "# Changed epoch\n"))
            with project.source_consumption() as consumer:
                project.replay_source_consumption(provider.receipt())
                tm.that(project.source_state(source), eq=original)
            tm.that(consumer.receipt().inputs, eq=(original,))
            with pytest.raises(ValueError, match="atomic source changed"):
                contexts.close()

    @staticmethod
    def test_identical_in_place_rewrite_keeps_source_epoch_valid(
        tmp_path: Path,
    ) -> None:
        """A byte-identical same-inode rewrite is not a divergent source change."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "provider.py"
        content = "__all__ = []\n"
        tm.ok(u.Cli.atomic_write_text_file(source, content))
        inode_before = source.stat().st_ino
        with u.Infra.facade_source_project(root) as (project, _, _):
            with project.source_consumption() as provider:
                original = project.source_state(source)
            with source.open("wb") as handle:
                handle.write(content.encode(c.DEFAULT_ENCODING))
            tm.that(source.stat().st_ino, eq=inode_before)
            with project.source_consumption() as consumer:
                project.replay_source_consumption(provider.receipt())
            tm.that(project.source_state(source), eq=original)
            tm.that(consumer.receipt().inputs, eq=(original,))

    @staticmethod
    def test_divergent_in_place_rewrite_fails_source_epoch(
        tmp_path: Path,
    ) -> None:
        """A genuinely divergent same-inode rewrite fails with content evidence."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        source = package / "provider.py"
        tm.ok(u.Cli.atomic_write_text_file(source, "__all__ = []\n"))

        def diverge() -> None:
            with u.Infra.facade_source_project(root) as (project, _, _):
                with project.source_consumption() as provider:
                    expected = project.source_state(source)
                    tm.ok(project.source_query(source, "isfile"))
                with project.source_consumption():
                    tm.ok(project.source_query(source, "exists"))
                inventories = tuple(
                    item
                    for item in project.consumed_source_directories()
                    if item.root.path == package
                )
                tm.that(len(inventories), eq=1)
                tm.that(
                    inventories[0].queries,
                    eq=((source.name, "exists"), (source.name, "isfile")),
                )
                with source.open("wb") as handle:
                    handle.write(b"__all__ = ['diverged']\n")
                tm.that(source.stat().st_ino, eq=expected.inode)
                with project.source_consumption():
                    project.replay_source_consumption(provider.receipt())

        with pytest.raises(
            ValueError, match=escape(f"atomic source changed: {source}")
        ):
            diverge()

    @staticmethod
    def test_negative_query_receipts_keep_original_absent_topology(
        tmp_path: Path,
    ) -> None:
        """An absent candidate under an absent parent is guarded after replay."""
        root, _ = u.Tests.create_lazy_init_workspace(tmp_path)
        missing = root / "absent"
        with ExitStack() as contexts:
            project, _, _ = contexts.enter_context(u.Infra.facade_source_project(root))
            folder = project.get_folder(missing.relative_to(root).as_posix())
            with project.source_consumption() as provider:
                tm.fail(folder.has_child("provider.py"))
            with project.source_consumption() as consumer:
                project.replay_source_consumption(provider.receipt())
            witnesses = tuple(
                witness
                for witness in consumer.receipt().source_query_topology
                if witness.target == missing
            )
            tm.that(len(witnesses), eq=1)
            tm.that(witnesses[0].queries, eq=(("provider.py", "exists"),))
            missing.mkdir()
            tm.ok(
                u.Cli.atomic_write_text_file(
                    missing / "provider.py",
                    "__all__ = []\n",
                ),
            )
            with pytest.raises(ValueError, match="source directory"):
                contexts.close()

    @staticmethod
    @pytest.mark.parametrize("depth", [1, 2])
    @pytest.mark.parametrize("relative", [False, True])
    @pytest.mark.parametrize(
        "segment", ["child", "descriptive_namespace_for_deep_native_owner_projection"]
    )
    def test_generated_imports_preserve_relative_alias_levels(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
        depth: int,
        segment: str,
        *,
        relative: bool,
    ) -> None:
        """Execute elected own imports alongside ancestor and external imports."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        children = (segment,) * depth
        child = package.joinpath(*children)
        child.mkdir(parents=True)
        namespace = ".".join((package.name, *children))
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / "sibling.py",
                "SENTINEL = 'native-sibling'\n",
            )
        )
        provider = child / "provider.py"
        tm.ok(u.Cli.atomic_write_text_file(provider, "LOCAL_SENTINEL = object()\n"))
        groups = {
            (
                f"{'.' * (depth + 1)}sibling" if relative else f"{package.name}.sibling"
            ): (("sibling", ""),),
            "pathlib": (("Path", "Path"),),
            f"{namespace}.{provider.stem}": (("LOCAL_SENTINEL", "LOCAL_SENTINEL"),),
        }
        width = u.Infra.native_tool_setting(
            config.Infra.tooling, "ruff", "line-length", int
        )
        if len(f"    from {namespace}.{provider.stem} import (") > width:
            with pytest.raises(ValueError, match="Absolute import owner"):
                codegen.FlextInfraCodegenGeneration.generate_type_checking(
                    groups,
                    include_flext_types=False,
                    local_package_root=namespace,
                )
            tm.fail((child / c.Infra.INIT_PY).exists())
            return
        imports = codegen.FlextInfraCodegenGeneration.generate_type_checking(
            groups,
            include_flext_types=False,
            local_package_root=namespace,
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                child / c.Infra.INIT_PY,
                "TYPE_CHECKING = True\n\n" + "\n".join(imports) + "\n",
            )
        )
        native_consumer(
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            "import pathlib\n"
            f"import {namespace}.{provider.stem} as provider\n"
            f"from {namespace} import LOCAL_SENTINEL, Path, sibling\n"
            "assert Path is pathlib.Path\n"
            "assert sibling.SENTINEL == 'native-sibling'\n"
            "assert LOCAL_SENTINEL is provider.LOCAL_SENTINEL\n",
            cwd=root,
        )

    @staticmethod
    @pytest.mark.parametrize("generated_name", config.Infra.codegen.generated_sources)
    def test_generated_barrel_does_not_elect_an_authored_facade(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
        generated_name: str,
    ) -> None:
        """Ignored generated providers remain importable without owning facades."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        generated = package / generated_name
        generated.mkdir()
        provider = generated / "provider.py"
        tm.ok(
            u.Cli.atomic_write_text_file(
                provider,
                "class GeneratedProvider:\n"
                "    marker = 'native-provider'\n"
                "__all__ = ['GeneratedProvider']\n",
            )
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                root / ".gitignore",
                f"/{generated.relative_to(root).as_posix()}/\n",
            )
        )
        service = u.Tests.create_lazy_init_service(root)
        analysis = tm.ok(service.plan_files())
        with u.Infra.facade_source_project(
            root, declared_files=analysis.files
        ) as binding:
            project, consumed, sources = binding
            tm.fail(any(path.is_relative_to(generated) for path in sources))
            planned = {
                file.path: file.desired_content.decode(c.DEFAULT_ENCODING)
                for file in analysis.files
                if file.path.suffix == c.Infra.EXT_PYTHON
                and file.desired_content is not None
            }
            tm.that(
                u.Infra.runtime_evaluated_base_classes(
                    root,
                    {**sources, **planned},
                    u.Tests.runtime_evaluated_roots(),
                    source_project=project,
                ),
                eq=tuple(sorted(u.Tests.runtime_evaluated_roots())),
            )
            tm.that(
                u.Infra.render_utility_facade(
                    package, family="p", project=project, sources=sources
                ),
                eq=None,
            )
            module = u.Infra.require_semantic_module(
                project.get_module(f"{package.name}.{generated.name}.{provider.stem}")
            )
            tm.not_none(module.get_attribute("GeneratedProvider").get_object())
            tm.that({state.path for state in consumed()[0]}, has=provider.resolve())
        tm.ok(u.Tests.materialize_lazy_init(service))
        native_consumer(
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            f"provider = importlib.import_module("
            f"{f'{package.name}.{generated.name}.{provider.stem}'!r})\n"
            "assert provider.GeneratedProvider.marker == 'native-provider'\n",
            cwd=root,
        )

    @staticmethod
    def test_shared_source_project_keeps_native_stdlib_election(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
    ) -> None:
        """The authenticated graph resolves the interpreter's virtual stdlib."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / "consumer.py",
                "from collections.abc import Mapping\n"
                "class Consumer(Mapping):\n"
                '    """Native stdlib inheritance contract."""\n'
                "__all__ = ['Consumer']\n",
            )
        )
        with u.Infra.facade_source_project(root) as binding:
            project, _, sources = binding
            tm.that(
                u.Infra.runtime_evaluated_base_classes(
                    root,
                    sources,
                    u.Tests.runtime_evaluated_roots(),
                    source_project=project,
                ),
                eq=tuple(sorted(u.Tests.runtime_evaluated_roots())),
            )
        tm.ok(u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)))
        native_consumer(
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            "from collections.abc import Mapping\n"
            f"from {package.name} import Consumer\n"
            "assert issubclass(Consumer, Mapping)\n",
            cwd=root,
        )

    @staticmethod
    @pytest.mark.parametrize("consumer_fails", [False, True])
    def test_changed_source_preserves_consumer_exception(
        tmp_path: Path,
        *,
        consumer_fails: bool,
    ) -> None:
        """Changed inputs reject success but never replace a consumer's exception."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = package / c.Infra.INIT_PY
        tm.ok(u.Cli.atomic_write_text_file(path, ""))
        failure = RuntimeError("consumer failed before source verification")

        def consume_changed_source() -> None:
            """Exercise one complete public source epoch."""
            with u.Infra.facade_source_project(root) as (project, _, _):
                project.get_pymodule(
                    project.get_resource(path.relative_to(root).as_posix())
                )
                tm.ok(u.Cli.atomic_write_text_file(path, "# Changed source epoch\n"))
                if consumer_fails:
                    raise failure

        with pytest.raises(
            RuntimeError if consumer_fails else ValueError,
            match=r"consumer failed|atomic source changed",
        ) as caught:
            consume_changed_source()
        tm.that(caught.value is failure, eq=consumer_fails)

    @staticmethod
    def test_declared_projection_preserves_authored_bindings(
        native_consumer: p.Tests.NativeConsumer,
        tmp_path: Path,
    ) -> None:
        """Unrelated authored bindings keep working after the family is published."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        family = u.Infra.facade_family_declared_by(c.Infra.UTILITIES_PY)
        facade = package / c.Infra.UTILITIES_PY
        sources = {
            package / c.Infra.INIT_PY: "",
            package / family.directory / "owner.py": (
                "class Owner:\n    marker = 'owner'\n__all__ = ['Owner']\n"
            ),
            package / family.directory / "support.py": (
                "class AuthoredSupport:\n"
                "    @staticmethod\n"
                "    def render(value):\n"
                "        return value.upper()\n"
                "__all__ = []\n"
            ),
            facade: (
                f"from {package.name}.{family.directory}.owner import Owner\n"
                f"from {package.name}.{family.directory}.support "
                "import AuthoredSupport\n"
                "def authored_value(value):\n"
                "    return AuthoredSupport.render(value)\n"
                "class Utilities(Owner):\n"
                "    @classmethod\n"
                "    def read(cls, value):\n"
                "        return authored_value(value) + ':' + cls.marker\n"
                "u = Utilities\n"
                "__all__ = ['Utilities', 'u']\n"
            ),
        }
        for path, source in sources.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        rendered = tm.not_none(u.Infra.render_utility_facade(package))
        tm.ok(u.Cli.atomic_write_text_file(facade, rendered))
        tm.ok(u.Tests.materialize_lazy_init(u.Tests.create_lazy_init_service(root)))
        tm.that(u.Infra.render_utility_facade(package), eq=rendered)
        native_consumer(
            f"sys.path.insert(0, {str(package.parent)!r})\n"
            f"from {package.name} import u\n"
            "assert u.read('value') == 'VALUE:owner'\n"
            "class Receiver(u):\n"
            "    marker = 'receiver'\n"
            "assert Receiver.read('value') == 'VALUE:receiver'\n",
            cwd=root,
        )

    @staticmethod
    def test_checkout_environment_is_never_a_planning_source(tmp_path: Path) -> None:
        """Dependency modules read from the checkout environment stay inputs only.

        Premise (70dc29f1b9 regression): the lazy-init plans carry every state
        their native reads consumed, including dependency modules installed in
        the checkout-local environment. Those states entered the planned-source
        map, so the facade planner treated the installed dependency as a
        project package and republished its facade inside the environment
        (cosmos-charts lost an importable flext_cli this way).
        """
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        installed = (
            root
            / c.Infra.ENVIRONMENT_DIRECTORY
            / "lib"
            / "site-packages"
            / "flext_dependency"
        )
        files = {
            package / c.Infra.INIT_PY: "",
            installed / c.Infra.INIT_PY: "",
            installed / c.Infra.UTILITIES_PY: "class Dependency:\n    pass\n",
        }
        for path, source in files.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        states = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            for path in files
        )
        with u.Infra.facade_source_project(root, source_states=states) as binding:
            project, consumed, sources = binding
            project.get_pymodule(
                project.get_resource(
                    (installed / c.Infra.UTILITIES_PY).relative_to(root).as_posix()
                )
            )
            tm.that(
                {path.resolve() for path in sources},
                eq={(package / c.Infra.INIT_PY).resolve()},
            )
            tm.that(
                {state.path.resolve() for state in consumed()[0]},
                has=(installed / c.Infra.UTILITIES_PY).resolve(),
            )

    @staticmethod
    @pytest.mark.parametrize("failed_stage", ["sources", "tooling"])
    def test_failed_planning_retains_only_a_completed_source_cohort(
        tmp_path: Path,
        failed_stage: Literal["sources", "tooling"],
    ) -> None:
        """Reject source cycles before retaining output for a later tooling failure."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        u.Tests.write_standalone_workspace_manifest(root, root.name)
        model = u.Infra.facade_families()["m"]
        utility = u.Infra.facade_families()["u"]
        facade = package / f"{model.module}.py"
        barrel = package / model.directory / c.Infra.INIT_PY
        utility_facade = package / f"{utility.module}.py"
        sources = {
            barrel: (
                f"{c.Infra.AUTOGEN_HEADER}\nfrom .base import ProviderBase\n"
                "from .departed import DepartedOwner\n"
                "__all__ = ['ProviderBase', 'DepartedOwner']\n"
            ),
            barrel.parent / "base.py": (
                "class ProviderBase:\n    marker = 'provider'\n"
                "__all__ = ['ProviderBase']\n"
            ),
            barrel.parent / "departed.py": (
                "class DepartedOwner:\n    departed = 'retained'\n__all__ = []\n"
            ),
            facade: (
                f"{c.Infra.AUTOGEN_HEADER}\n"
                f"from {package.name}.{model.directory} "
                "import ProviderBase, DepartedOwner\n"
                "class ProviderModels(ProviderBase, DepartedOwner):\n    pass\n"
                "m = ProviderModels\n__all__ = ['ProviderModels', 'm']\n"
            ),
            package / utility.directory / c.Infra.INIT_PY: "",
            package / utility.directory / "owner.py": (
                f"from {package.name} import m\n"
                "class ConsumerOwner(m):\n    pass\n__all__ = ['ConsumerOwner']\n"
            ),
            utility_facade: (
                "class ConsumerUtilities:\n    pass\n"
                "u = ConsumerUtilities\n__all__ = ['ConsumerUtilities', 'u']\n"
            ),
        }
        if failed_stage == "sources":
            sources.update({
                package / "cycle_first.py": (
                    "from . import cycle_second\n__all__ = []\n"
                ),
                package / "cycle_second.py": (
                    "from . import cycle_first\n__all__ = []\n"
                ),
            })
        for path, content in sources.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            tm.ok(u.Cli.atomic_write_text_file(path, content))
        tooling = root / c.CONFIG_DIR_NAME / "tooling.yaml"
        tm.ok(u.Cli.yaml_dump(tooling, {"Infra": {"tooling": {"settings": []}}}))
        incoming = tm.ok(u.Tests.create_lazy_init_service(root).plan_files()).files
        tm.that(len(incoming), gt=0)
        tm.fail(facade in {file.path for file in incoming})
        originals = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            for path in (
                package / c.Infra.INIT_PY,
                *sources,
                tooling,
                root / c.PYPROJECT_FILENAME,
            )
        )
        inputs = tm.ok(u.Infra.load_codegen_inputs(root))
        spec = tm.ok(
            workspace.FlextInfraWorkspaceDetector.load_workspace_spec(
                root, inputs=inputs
            )
        )
        outcome = codegen.FlextInfraCodegenConform.plan_repository_task(
            m.Infra.CodegenRepositoryPlanTask(
                root=root,
                workspace=spec,
                current_target=tm.ok(
                    workspace.FlextInfraWorkspaceDetector.conform_target(
                        root, spec, inputs=inputs
                    )
                ),
                repository=spec.repository,
                surface=c.Infra.CodegenConformSurface.ALL,
                selected_inputs=inputs,
                provider_plans=incoming,
            )
        )
        tm.that(outcome.failed, eq=True)
        if failed_stage == "sources":
            tm.that(outcome.error, has="projected runtime import cycle")
            tm.that(outcome.files, eq=())
        else:
            tm.that(outcome.error, has="settings")
            tm.that(isinstance(outcome.exception, m.ValidationError), eq=True)
            projected = {file.path: file for file in outcome.files}
            tm.that(set(projected), has=facade)
            tm.that(set(projected), has=barrel)
            tm.that(set(projected), has=utility_facade)
            tm.that(set(projected), has=package / c.Infra.INIT_PY)
            tm.that(
                projected[facade].before,
                eq=next(state for state in originals if state.path == facade),
            )
            tm.fail(b"DepartedOwner" in tm.not_none(projected[facade].desired_content))
            with u.Infra.facade_source_project(
                root, source_states=originals, declared_files=outcome.files
            ) as binding:
                tm.that(
                    tm.not_none(
                        u.Infra.render_utility_facade(
                            package, project=binding[0], sources=binding[2]
                        )
                    ).encode(c.DEFAULT_ENCODING),
                    eq=projected[utility_facade].desired_content,
                )
        tm.ok(u.Cli.atomic_verify_binary_file_states(originals))

    @staticmethod
    @pytest.mark.parametrize("declared", [False, True])
    def test_unpublished_provider_facet_precedes_native_consumer(
        native_consumer: p.Tests.NativeConsumer,
        installed_dependency_path: Path,
        tmp_path: Path,
        *,
        declared: bool,
    ) -> None:
        """Bind a complete supplier candidate without publishing its original files."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        provider_root, provider = u.Tests.create_lazy_init_workspace(
            installed_dependency_path,
            project_name="provider_project",
            package_name="provider_package",
        )
        families = u.Infra.facade_families()
        model_facade = provider / f"{families['m'].module}.py"
        model_barrel = provider / families["m"].directory / c.Infra.INIT_PY
        consumer_facade = package / f"{families['u'].module}.py"
        sources = {
            provider / c.Infra.INIT_PY: (
                f"from .{families['m'].module} import m\n__all__ = ['m']\n"
            ),
            model_barrel: (
                f"{c.Infra.AUTOGEN_HEADER}\nfrom .base import ProviderBase\n"
                "from .departed import DepartedOwner\n"
                "__all__ = ['ProviderBase', 'DepartedOwner']\n"
            ),
            model_barrel.parent / "base.py": (
                "class ProviderBase:\n"
                "    marker = 'provider'\n"
                "__all__ = ['ProviderBase']\n"
            ),
            model_barrel.parent / "departed.py": (
                "class DepartedOwner:\n    departed = 'retained'\n__all__ = []\n"
            ),
            model_facade: (
                f"{c.Infra.AUTOGEN_HEADER}\n"
                f"from {provider.name}.{families['m'].directory} "
                "import ProviderBase, DepartedOwner\n"
                "class ProviderModels(ProviderBase, DepartedOwner):\n    pass\n"
                "m = ProviderModels\n__all__ = ['ProviderModels', 'm']\n"
            ),
            package / c.Infra.INIT_PY: "",
            package / families["u"].directory / c.Infra.INIT_PY: "",
            package / families["u"].directory / "owner.py": (
                f"from {provider.name} import m\n"
                f"class ConsumerOwner({'m' if declared else 'm.DepartedOwner'}):\n"
                "    pass\n"
                "__all__ = ['ConsumerOwner']\n"
            ),
            consumer_facade: (
                "class ConsumerUtilities:\n    pass\n"
                "u = ConsumerUtilities\n__all__ = ['ConsumerUtilities', 'u']\n"
            ),
        }
        for path, source in sources.items():
            path.parent.mkdir(parents=True, exist_ok=True)
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        originals = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            for path in sources
        )
        by_path = {state.path: state for state in originals}
        plans = {
            file.path: file
            for file in tm.ok(
                u.Tests.create_lazy_init_service(provider_root).plan_files()
            ).files
        }
        with (
            tm.scope(python_paths=(str(provider.parent),)),
            nullcontext()
            if declared
            else pytest.raises(
                ValueError,
                match=(
                    r"^Missing inherited class member: "
                    r".*:ProviderModels:\d+\.DepartedOwner$"
                ),
            ),
        ):
            with u.Infra.facade_source_project(
                provider_root,
                source_states=originals,
                declared_files=tuple(plans.values()),
            ) as binding:
                plans[model_facade] = m.Infra.CodegenFilePlan(
                    project=provider_root,
                    path=model_facade,
                    before=by_path[model_facade],
                    desired_content=tm.not_none(
                        u.Infra.render_utility_facade(
                            provider,
                            family="m",
                            project=binding[0],
                            sources=binding[2],
                        )
                    ).encode(c.DEFAULT_ENCODING),
                    desired_mode=tm.not_none(by_path[model_facade].mode),
                    source_states=binding[1]()[0],
                )
            with u.Infra.facade_source_project(
                root, source_states=originals, declared_files=tuple(plans.values())
            ) as binding:
                consumer = tm.not_none(
                    u.Infra.render_utility_facade(
                        package, project=binding[0], sources=binding[2]
                    )
                )
                plans[consumer_facade] = m.Infra.CodegenFilePlan(
                    project=root,
                    path=consumer_facade,
                    before=by_path[consumer_facade],
                    desired_content=consumer.encode(c.DEFAULT_ENCODING),
                    desired_mode=tm.not_none(by_path[consumer_facade].mode),
                    source_states=binding[1]()[0],
                )
                tm.that({state.path for state in binding[1]()[0]}, has=model_facade)
            with u.Infra.facade_source_project(
                root, source_states=originals, declared_files=tuple(plans.values())
            ) as binding:
                plans.update(
                    (file.path, file)
                    for file in tm.ok(
                        u.Tests.create_lazy_init_service(root).plan_files(
                            source_project=binding[0]
                        )
                    ).files
                )
            with u.Infra.facade_source_project(
                root, source_states=originals, declared_files=tuple(plans.values())
            ) as binding:
                tm.that(
                    u.Infra.render_utility_facade(
                        package, project=binding[0], sources=binding[2]
                    ),
                    eq=consumer,
                )
            tm.ok(u.Cli.atomic_verify_binary_file_states(originals))
        if not declared:
            tm.ok(u.Cli.atomic_verify_binary_file_states(originals))
            return
        candidate = tmp_path / "candidate"
        for state in originals:
            destination = candidate / state.path.relative_to(
                provider.parent
                if state.path.is_relative_to(provider)
                else package.parent
            )
            destination.parent.mkdir(parents=True, exist_ok=True)
            tm.ok(
                u.Cli.atomic_write_text_file(
                    destination,
                    tm.not_none(state.content).decode(c.DEFAULT_ENCODING),
                )
            )
        for file in plans.values():
            destination = candidate / file.path.relative_to(
                provider.parent
                if file.path.is_relative_to(provider)
                else package.parent
            )
            destination.parent.mkdir(parents=True, exist_ok=True)
            tm.ok(
                u.Cli.atomic_write_text_file(
                    destination,
                    tm.not_none(file.desired_content).decode(c.DEFAULT_ENCODING),
                )
            )
        native_consumer(
            "from flext_tests import tm\n"
            f"sys.path.insert(0, {str(candidate)!r})\n"
            f"from {package.name}.{families['u'].module} import u\n"
            f"from {provider.name} import m\n"
            f"from {provider.name}.{families['m'].directory}.departed "
            "import DepartedOwner\n"
            "tm.that(u.marker, eq=m.marker)\n"
            "tm.fail(hasattr(m, 'departed'))\n"
            "tm.that(DepartedOwner.departed, eq='retained')\n",
            cwd=root,
        )
        tm.ok(u.Cli.atomic_verify_binary_file_states(originals))

    @staticmethod
    @pytest.mark.parametrize("declared", [False, True])
    def test_planned_provider_export_precedes_native_consumer(
        native_consumer: p.Tests.NativeConsumer,
        installed_dependency_path: Path,
        tmp_path: Path,
        *,
        declared: bool,
    ) -> None:
        """A stale live barrel never replaces the provider's planned export."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        provider_root, provider = u.Tests.create_lazy_init_workspace(
            installed_dependency_path,
            project_name="provider_project",
            package_name="provider_package",
        )
        family = u.Infra.facade_family_declared_by(c.Infra.PROTOCOLS_PY)
        barrel = provider / family.directory / c.Infra.INIT_PY
        barrel.parent.mkdir()
        tm.ok(u.Cli.atomic_write_text_file(barrel, ""))
        public_name = "ProviderBase" if declared else "OtherProviderBase"
        tm.ok(
            u.Cli.atomic_write_text_file(
                barrel.parent / "base.py",
                u.Tests.runtime_root_import() + f"class {public_name}(RuntimeRoot):\n"
                '    """Explicitly published empty protocol owner."""\n'
                f"__all__ = [{public_name!r}]\n",
            ),
        )
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / "consumer.py",
                f"from {provider.name}.{family.directory} "
                "import ProviderBase\n"
                "class Consumer(ProviderBase):\n"
                '    """Consumer of the generated provider barrel."""\n'
                "__all__ = ['Consumer']\n",
            ),
        )
        provider_service = u.Tests.create_lazy_init_service(provider_root)
        provider_analysis = tm.ok(provider_service.plan_files())
        original_barrel = tm.ok(
            u.Cli.atomic_read_binary_file_state(barrel, required=True)
        )
        with ExitStack() as stack:
            stack.enter_context(tm.scope(python_paths=(str(provider.parent),)))
            if not declared:
                stack.enter_context(
                    pytest.raises(
                        u.Infra.rope_attribute_not_found_error_types(),
                        match="Attribute ProviderBase not found",
                    )
                )
            project, consumed, sources = stack.enter_context(
                u.Infra.facade_source_project(
                    root,
                    declared_files=provider_analysis.files,
                )
            )
            roots = u.Infra.runtime_evaluated_base_classes(
                root,
                sources,
                u.Tests.runtime_evaluated_roots(),
                source_project=project,
            )
            tm.that(
                roots,
                has=f"{provider.name}.{family.directory}.ProviderBase",
            )
            tm.that(
                {state.path for state in consumed()[0]},
                has=barrel.resolve(),
            )
        tm.that(
            tm.ok(u.Cli.atomic_read_binary_file_state(barrel, required=True)),
            eq=original_barrel,
        )
        if declared:
            with tm.scope(python_paths=(str(provider.parent),)):
                tm.ok(u.Tests.materialize_lazy_init(provider_service))
                tm.ok(
                    u.Tests.materialize_lazy_init(
                        u.Tests.create_lazy_init_service(root)
                    )
                )
            native_consumer(
                f"sys.path.insert(0, {str(provider.parent)!r})\n"
                f"sys.path.insert(0, {str(package.parent)!r})\n"
                f"from {provider.name}.{family.directory} "
                "import ProviderBase\n"
                f"from {package.name} import Consumer\n"
                "assert ProviderBase.__module__ == "
                f"{f'{provider.name}.{family.directory}.base'!r}\n"
                "assert issubclass(Consumer, ProviderBase)\n",
                cwd=root,
            )
