"""Runner collection-manifest, Markdown and worker accounting behind pytest hooks.

The runner resolves selected node IDs once and passes that ordered manifest as
pytest arguments. Testmon still records dependencies in every worker, but its
worker-local stable/unstable classification must not define xdist's index order.
Missing, additional or duplicate tests fail loudly. The same installed plugin
records warning identities before report-log reduces their categories to names.
The plugin's hook class only orchestrates these utilities.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import time
from collections.abc import Generator, MutableMapping, Sequence
from hashlib import sha256
from importlib.metadata import version
from pathlib import Path
from sys import modules, monitoring
from traceback import format_exception
from types import CodeType, ModuleType, SimpleNamespace
from typing import ClassVar, TypeIs
from warnings import WarningMessage

from flext_cli import u
from pytest_markdown_docs import plugin as markdown_plugin
from pytest_markdown_docs.plugin import extract_fence_tests

from flext_infra import c, m, p, t
from flext_infra._utilities import FlextInfraUtilitiesPytest


class FlextInfraUtilitiesPytestCollection:
    """Collection, Markdown and worker accounting for the runner's pytest plugin."""

    markdown_state: ClassVar[
        t.Infra.Pytest.StashKey[m.Infra.PytestMarkdownCollection]
    ] = t.Infra.Pytest.StashKey()
    collection_workers: ClassVar[t.Infra.Pytest.StashKey[set[str]]] = (
        t.Infra.Pytest.StashKey()
    )
    collection_worker_ids: ClassVar[
        t.Infra.Pytest.StashKey[dict[str, tuple[str, ...]]]
    ] = t.Infra.Pytest.StashKey()
    collection_worker_manifests: ClassVar[
        t.Infra.Pytest.StashKey[dict[str, m.Infra.PytestCollectionManifest]]
    ] = t.Infra.Pytest.StashKey()

    @staticmethod
    def markdown_item(
        item: t.Infra.Pytest.Item,
    ) -> TypeIs[t.Infra.Pytest.MarkdownItem]:
        """Return whether ``item`` is a Markdown fence test of a Markdown file.

        Returns:
            Whether the SDK collected ``item`` from a Markdown text file.

        """
        return isinstance(item, t.Infra.Pytest.MarkdownInlinePythonItem) and isinstance(
            item.parent, t.Infra.Pytest.MarkdownTextFile
        )

    @staticmethod
    def markdown_origin(
        definition: t.Infra.Pytest.FenceDefinition,
        root: Path,
    ) -> m.Infra.PytestMarkdownOrigin:
        """Bind the SDK definition without compiling or interpreting its source.

        Returns:
            The resulting ``m.Infra.PytestMarkdownOrigin``.

        """
        return m.Infra.PytestMarkdownOrigin(
            source_path=definition.source_path.resolve().relative_to(root).as_posix(),
            start_line=definition.start_line,
            source_sha256=sha256(definition.source.encode("utf-8")).hexdigest(),
            max_retries=definition.max_retries,
        )

    @classmethod
    def markdown_collect_start(cls, collector: t.Infra.Pytest.Collector) -> None:
        """Measure eligibility before the real collector can omit any item."""
        if not isinstance(collector, t.Infra.Pytest.MarkdownTextFile):
            return
        state = collector.config.stash[cls.markdown_state]
        parser = collector.config.hook.pytest_markdown_docs_markdown_it()
        syntax = t.Infra.Pytest.FenceSyntax(
            collector.config.getoption("markdowndocs_syntax")
        )
        definitions = extract_fence_tests(
            parser,
            collector.path.read_text(encoding="utf-8"),
            start_line_offset=0,
            source_path=collector.path,
            markdown_type=collector.path.suffix.removeprefix("."),
            fence_syntax=syntax,
        )
        state.eligible.extend(
            cls.markdown_origin(definition, collector.config.rootpath)
            for definition in definitions
        )

    @classmethod
    def markdown_item_collected(cls, item: t.Infra.Pytest.Item) -> None:
        """Retain actual Markdown node identities before selector hooks run."""
        if not cls.markdown_item(item):
            return
        state = item.config.stash[cls.markdown_state]
        observation = m.Infra.PytestMarkdownItem(
            node_id=item.nodeid,
            origin=cls.markdown_origin(item.test_definition, item.config.rootpath),
        )
        state.collected.append(observation)
        item.user_properties.append((
            "flext_markdown_origin",
            observation.model_dump_json(),
        ))

    @classmethod
    def markdown_deselected(cls, items: list[t.Infra.Pytest.Item]) -> None:
        """Account for selector effects through their public notification."""
        for item in items:
            if cls.markdown_item(item):
                item.config.stash[cls.markdown_state].deselected.append(item.nodeid)

    @staticmethod
    def markdown_module_scope(item: t.Infra.Pytest.Item) -> Generator[None]:
        """Scope the unregistered execution module shipped by SDK 0.9.2.

        Remove this compatibility hook when the supplier owns registration.
        Only its local ``types`` binding changes; the real runner and the
        interpreter-wide ``types.ModuleType`` remain untouched.
        """
        if (
            not isinstance(item, t.Infra.Pytest.MarkdownInlinePythonItem)
            or version("pytest-markdown-docs") != "0.9.2"
        ):
            yield
            return
        registrations: list[tuple[str, ModuleType, tuple[ModuleType, ...]]] = []

        def registered_module(name: str) -> ModuleType:
            """Register exactly the module whose dictionary the SDK executes.

            Returns:
                The native module registered for this execution scope.

            """
            module = ModuleType(name)
            previous = (modules[name],) if name in modules else ()
            registrations.append((name, module, previous))
            modules[name] = module
            return module

        with FlextInfraUtilitiesPytest.Pytest.monkeypatch_context() as patch:
            patch.setattr(
                markdown_plugin,
                "types",
                SimpleNamespace(ModuleType=registered_module),
            )
            try:
                yield
            finally:
                for name, module, previous in reversed(registrations):
                    if modules.get(name) is not module:
                        continue
                    if previous:
                        modules[name] = previous[0]
                    else:
                        del modules[name]

    @classmethod
    def markdown_runtest_call(cls, item: t.Infra.Pytest.Item) -> Generator[None]:
        """Observe the real runner without replacing its execution method.

        Raises:
            RuntimeError: If Markdown execution requires exactly one runner attempt.

        """
        if not cls.markdown_item(item):
            yield
            return
        tool = monitoring.PROFILER_ID
        code = item.runner.runtest.__code__
        observer = cls.MarkdownAttempts(code)
        monitoring.use_tool_id(tool, "flext-markdown-attempts")
        try:
            monitoring.register_callback(
                tool,
                monitoring.events.PY_START,
                observer.start,
            )
            monitoring.register_callback(
                tool,
                monitoring.events.PY_UNWIND,
                observer.unwind,
            )
            monitoring.set_local_events(tool, code, monitoring.events.PY_START)
            monitoring.set_events(tool, monitoring.events.PY_UNWIND)
            try:
                yield
            except BaseException as error:
                if (
                    observer.first_error is not None
                    and observer.first_error is not error
                ):
                    raise observer.first_error from error
                raise
            finally:
                proof = m.Infra.PytestMarkdownAttempt(
                    node_id=item.nodeid,
                    attempts=observer.attempts,
                    first_exception_type=(
                        None
                        if observer.first_error is None
                        else type(observer.first_error).__qualname__
                    ),
                    first_exception_traceback=(
                        None
                        if observer.first_error is None
                        else "".join(format_exception(observer.first_error))
                    ),
                )
                item.user_properties.append((
                    "flext_markdown_attempt",
                    proof.model_dump_json(),
                ))
            if observer.first_error is not None:
                raise observer.first_error
            if observer.attempts != 1:
                msg = (
                    "Markdown execution requires exactly one runner attempt: "
                    f"{item.nodeid}"
                )
                raise RuntimeError(msg)
        finally:
            monitoring.set_events(tool, 0)
            monitoring.set_local_events(tool, code, 0)
            monitoring.register_callback(tool, monitoring.events.PY_START, None)
            monitoring.register_callback(tool, monitoring.events.PY_UNWIND, None)
            monitoring.free_tool_id(tool)

    class MarkdownAttempts:
        """One runtest-hook observer using native interpreter events."""

        def __init__(self, code: CodeType) -> None:
            self.code = code
            self.attempts = 0
            self.first_error: BaseException | None = None

        def start(self, _code: CodeType, _instruction_offset: int) -> None:
            """Count every entry into the already-selected SDK runner."""
            del _code, _instruction_offset
            self.attempts += 1

        def unwind(
            self,
            code: CodeType,
            _instruction_offset: int,
            exception: BaseException,
        ) -> None:
            """Retain the first exception before the plugin can retry it."""
            del _instruction_offset
            if code is self.code and self.first_error is None:
                self.first_error = exception

    @staticmethod
    def collection_add_options(parser: t.Infra.Pytest.Parser) -> None:
        """Require explicit activation by the canonical runner."""
        parser.addoption(
            c.Infra.PYTEST_SELECTED_COLLECTION_OPTION,
            default=None,
            help="Manifest whose ordered node-ID selection every worker enforces.",
        )
        parser.addoption(
            c.Infra.PYTEST_COLLECTION_MANIFEST_OPTION,
            default=None,
            help="Path where the session publishes its observed final items.",
        )
        parser.addoption(
            c.Infra.PYTEST_SUITE_STOP_OPTION,
            type=float,
            default=None,
            help="Monotonic instant after which the session stops gracefully.",
        )

    @classmethod
    def collection_configure(cls, config: t.Infra.Pytest.Config) -> None:
        """Pin testmon outside the checkout; record warnings once.

        pytest-testmon opens ``TESTMON_DATAFILE`` in its own configure hook
        and otherwise creates ``.testmondata`` in the working directory. The
        canonical test verbs export the external database, so an activation
        without it (or pointing inside the rootdir) is refused before
        testmon can write into the repository.

        Raises:
            UsageError: When testmon is active without an absolute
                external datafile.

        """
        testmon_active = any(
            config.getoption(dest, default=False)
            for dest in c.Infra.PYTEST_TESTMON_ACTIVATION_DESTS
        ) and not config.getoption(c.Infra.PYTEST_TESTMON_DISABLE_DEST, default=False)
        if testmon_active:
            datafile = u.Cli.process_env().get(c.Infra.PYTEST_ENV_TESTMON_DATAFILE, "")
            database = Path(datafile.strip())
            if not datafile.strip() or not database.is_absolute():
                msg = (
                    f"pytest-testmon requires an absolute external "
                    f"{c.Infra.PYTEST_ENV_TESTMON_DATAFILE}; run the canonical "
                    "make test verb"
                )
                raise c.Infra.Pytest.UsageError(msg)
            if database.resolve().is_relative_to(config.rootpath.resolve()):
                msg = f"testmon database must be outside the checkout: {database}"
                raise c.Infra.Pytest.UsageError(msg)
        config.stash[cls.markdown_state] = m.Infra.PytestMarkdownCollection()
        if cls.suite_manifest_target(config) is not None:
            config.stash[cls.collection_workers] = set()
            config.stash[cls.collection_worker_ids] = {}
            config.stash[cls.collection_worker_manifests] = {}
        report_log = config.getoption("report_log", default=None)
        if report_log and not hasattr(config, "workerinput"):
            config.pluginmanager.register(cls.WarningAccounting(Path(report_log)))
        stop_at = config.getoption(c.Infra.PYTEST_SUITE_STOP_OPTION)
        if stop_at is not None and not hasattr(config, "workerinput"):
            config.pluginmanager.register(cls.SuiteStop(stop_at_monotonic=stop_at))

    @staticmethod
    def suite_manifest_target(config: t.Infra.Pytest.Config) -> Path | None:
        """Read the existing manifest destination for an executing suite.

        Returns:
            The invocation's requested destination, or no suite observation.

        """
        target: str | None = config.getoption(
            c.Infra.PYTEST_COLLECTION_MANIFEST_OPTION,
        )
        if target is None or config.getoption("collectonly"):
            return None
        return Path(target)

    @staticmethod
    def worker_identity(node: t.Infra.Pytest.WorkerController) -> str:
        """Read the native worker gateway identity as a validated string.

        Returns:
            The identity the distributed controller assigned to this worker.

        """
        return u.type_adapter(str).validate_python(
            vars(node.gateway).get("id"), strict=True
        )

    @classmethod
    def collection_configure_node(cls, node: t.Infra.Pytest.WorkerController) -> None:
        """Admit each actual native worker into this invocation's inventory.

        Raises:
            ValueError: If the native worker identity was already admitted.

        """
        if cls.suite_manifest_target(node.config) is None:
            return
        workers = node.config.stash[cls.collection_workers]
        identity = cls.worker_identity(node)
        if identity in workers:
            msg = f"duplicate pytest worker admission: {identity}"
            raise ValueError(msg)
        workers.add(identity)

    @classmethod
    def collection_node_finished(
        cls,
        node: t.Infra.Pytest.WorkerController,
        ids: Sequence[str],
    ) -> None:
        """Retain the controller's native node order before test dispatch.

        Raises:
            ValueError: If the worker is unadmitted, its collection repeats,
                or its node IDs contain duplicates or empty identifiers.

        """
        if cls.suite_manifest_target(node.config) is None:
            return
        identity = cls.worker_identity(node)
        workers = node.config.stash[cls.collection_workers]
        observed = node.config.stash[cls.collection_worker_ids]
        node_ids = tuple(ids)
        if identity not in workers or identity in observed:
            msg = f"unadmitted or repeated pytest worker collection: {identity}"
            raise ValueError(msg)
        if len(node_ids) != len(set(node_ids)) or any(not item for item in node_ids):
            msg = f"pytest worker collected duplicate or empty node IDs: {identity}"
            raise ValueError(msg)
        observed[identity] = node_ids

    @classmethod
    def collection_node_down(
        cls,
        node: t.Infra.Pytest.WorkerController,
        error: object | None,
    ) -> None:
        """Publish one manifest after every admitted worker supplies its facts.

        Raises:
            TypeError: If the observed worker's payload is not JSON text.
            ValueError: If the worker is unadmitted, its manifest repeats,
                the payload is invalid, its IDs differ from native collection,
                or the admitted workers' complete manifests disagree.

        """
        target = cls.suite_manifest_target(node.config)
        if target is None or error is not None:
            return
        identity = cls.worker_identity(node)
        workers = node.config.stash[cls.collection_workers]
        observed = node.config.stash[cls.collection_worker_ids]
        manifests = node.config.stash[cls.collection_worker_manifests]
        if identity not in workers or identity in manifests:
            msg = f"unadmitted or repeated pytest worker manifest: {identity}"
            raise ValueError(msg)
        if identity not in observed:
            # Native shutdown can discard a late collection notification while
            # still delivering workeroutput. That payload cannot prove its own
            # missing collection authority; every worker remains required.
            return
        key = c.Infra.PYTEST_WORKER_COLLECTION_KEY
        if key not in node.workeroutput:
            # A worker that never completed collection provides no inventory.
            # Its native failure cannot authorize another worker's subset.
            return
        payload = node.workeroutput[key]
        if not isinstance(payload, str):
            msg = "pytest worker collection payload must be JSON text"
            raise TypeError(msg)
        manifest = m.Infra.PytestCollectionManifest.model_validate_json(
            payload,
            strict=True,
        )
        if manifest.node_ids != observed[identity]:
            msg = f"pytest worker manifest differs from native collection: {identity}"
            raise ValueError(msg)
        manifests[identity] = manifest
        if manifests.keys() != workers:
            return
        reference = next(iter(manifests.values()))
        if any(item != reference for item in manifests.values()):
            msg = "pytest worker collection manifests disagree"
            raise ValueError(msg)
        cls.write_collection_manifest(reference, target)

    @classmethod
    def collection_finish(cls, session: t.Infra.Pytest.Session) -> Generator[None]:
        """Validate before xdist publishes worker IDs, preserving raw failures.

        Both manifest routes are runner-passed options: a session that names
        neither imports no model. A requested manifest loads only its owning
        model module, never the whole model facade, because every runner
        collection process pays that import.

        Raises:
            ValueError: If Runner collection manifest contains duplicate node IDs; or if
                Runner collection differs from selection.
            TypeError: If the native worker has no output channel.

        """
        selected: str | None = session.config.getoption(
            c.Infra.PYTEST_SELECTED_COLLECTION_OPTION,
        )
        if selected is not None:
            manifest = m.Infra.PytestCollectionManifest.model_validate_json(
                Path(selected).read_text(encoding="utf-8"),
            )
            order = {node_id: index for index, node_id in enumerate(manifest.node_ids)}
            collected = [item.nodeid for item in session.items]
            if len(order) != len(manifest.node_ids) or len(set(collected)) != len(
                collected,
            ):
                msg = "Runner collection manifest contains duplicate node IDs"
                raise ValueError(msg)
            if set(collected) != set(order):
                missing = sorted(set(order) - set(collected))
                unexpected = sorted(set(collected) - set(order))
                msg = (
                    f"Runner collection differs from selection: "
                    f"{missing=}, {unexpected=}"
                )
                raise ValueError(msg)
            session.items.sort(key=lambda item: order[item.nodeid])
        yield
        target: str | None = session.config.getoption(
            c.Infra.PYTEST_COLLECTION_MANIFEST_OPTION,
        )
        if target is None:
            return
        collect_only = session.config.getoption("collectonly")
        if not collect_only and session.testsfailed:
            return
        if (
            not collect_only
            and not hasattr(session.config, "workerinput")
            and session.config.pluginmanager.getplugin("dsession") is not None
        ):
            # The distributed controller owns no local pytest items.
            return
        manifest = cls.collection_manifest(session)
        if not collect_only and hasattr(session.config, "workerinput"):
            worker_output = vars(session.config).get("workeroutput")
            if not isinstance(worker_output, MutableMapping):
                msg = "native pytest worker has no output channel"
                raise TypeError(msg)
            worker_output[c.Infra.PYTEST_WORKER_COLLECTION_KEY] = (
                manifest.model_dump_json()
            )
            return
        cls.write_collection_manifest(manifest, Path(target))

    @classmethod
    def collection_manifest(
        cls,
        session: t.Infra.Pytest.Session,
    ) -> m.Infra.PytestCollectionManifest:
        """Bind final items and independent Markdown observations.

        Returns:
            The actual manifest after testmon and every collection hook.

        """
        state = session.config.stash[cls.markdown_state]
        return m.Infra.PytestCollectionManifest(
            node_ids=tuple(item.nodeid for item in session.items),
            markdown_eligible=tuple(state.eligible),
            markdown_collected=tuple(state.collected),
            markdown_deselected=tuple(state.deselected),
        )

    @staticmethod
    def write_collection_manifest(
        manifest: m.Infra.PytestCollectionManifest,
        target: Path,
    ) -> None:
        """Publish the observed manifest through its existing atomic writer."""
        u.Cli.atomic_write_text_file(target, manifest.model_dump_json() + "\n").unwrap()

    class SuiteStop:
        """End the session gracefully at the runner's derived stop instant.

        The controller stops dispatch through the same path as max-failures:
        xdist queues the shutdown marker, so each worker's final item runs
        with no successor and pytest-testmon flushes every batched result.
        A process-deadline SIGTERM instead discards the unflushed batches.

        When every collected item has already completed, nothing is left to
        stop and the stop request would only recolor a finished green suite
        red, so the request is suppressed at that boundary.
        """

        def __init__(self, *, stop_at_monotonic: float) -> None:
            self.stop_at_monotonic = stop_at_monotonic
            self.session: t.Infra.Pytest.Session | None = None
            self.completed_items: set[str] = set()

        def pytest_sessionstart(self, session: t.Infra.Pytest.Session) -> None:
            """Bind the controller session that owns the stop decision."""
            self.session = session

        def pytest_runtest_logreport(self, report: t.Infra.Pytest.TestReport) -> None:
            """Request the stop once a completed item crosses the instant.

            The request is suppressed when this item was the last one still
            pending: a suite that already finished must end green instead of
            being interrupted after its own final result.

            Raises:
                TypeError: If the native distributed controller has no stop port.

            """
            session = self.session
            if session is None or report.when != "teardown":
                return
            self.completed_items.add(report.nodeid)
            # The instant is computed in the runner parent and handed to this
            # process as a CLI option; a clock skew between the two (or a
            # stale parent clock) must never stop a suite whose deadline has
            # not actually passed on this process's own monotonic clock.
            if time.monotonic() < self.stop_at_monotonic:
                return
            total_items = len(session.items)
            if total_items and len(self.completed_items) >= total_items:
                return
            # Testmon writes an in-flight coverage batch only when it attaches
            # nodes_files_lines to a teardown report. Stopping earlier leaves
            # selected rows without durable execution data on the next run.
            if not getattr(report, "nodes_files_lines", None):
                return
            reason = f"suite stop instant {self.stop_at_monotonic:.3f} reached"
            controller = session.config.pluginmanager.getplugin("dsession")
            if controller is None:
                if not session.shouldstop:
                    session.shouldstop = reason
                return
            if not isinstance(controller, p.Infra.PytestStopController):
                msg = "native distributed pytest controller has no stop port"
                raise TypeError(msg)
            shouldstop = u.type_adapter(bool | str).validate_python(
                controller.shouldstop,
                strict=True,
            )
            if not shouldstop:
                controller.shouldstop = reason

    class WarningAccounting:
        """Preserve the real class identity of every recorded warning."""

        def __init__(self, report_log: Path) -> None:
            self.report = report_log.with_suffix(
                c.Infra.PYTEST_WARNING_EVENTS_SUFFIX,
            )
            self.report.parent.mkdir(parents=True, exist_ok=True)
            self.report.write_text("", encoding="utf-8")

        @FlextInfraUtilitiesPytest.Pytest.hookimpl(tryfirst=True)
        def pytest_warning_recorded(self, warning_message: WarningMessage) -> None:
            """Record the real warning once before report-log serializes it."""
            category = warning_message.category
            event = m.Infra.PytestWarningEvent(
                category=category.__name__,
                category_module=category.__module__,
                category_qualname=category.__qualname__,
                filename=warning_message.filename,
                lineno=warning_message.lineno,
                message=str(warning_message.message),
            )
            with self.report.open("a", encoding="utf-8") as stream:
                stream.write(event.model_dump_json() + "\n")


__all__: list[str] = ["FlextInfraUtilitiesPytestCollection"]
