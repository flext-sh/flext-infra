"""Real public semantic publication, candidates and consumers.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
import threading
from pathlib import Path

import pytest

from flext_infra import codemod, infra, transformers, workspace
from tests import c, m, p, r, t, tm, u


class TestsFlextInfraSemanticPublicationTransactions:
    """Publish semantic candidates atomically and prove the real public consumers."""

    @staticmethod
    def test_cold_public_cli_composes_semantic_ports_without_an_import_cycle() -> None:
        """A fresh native CLI process must finish API composition before dispatch."""
        u.Tests.run_native_callable(
            TestsFlextInfraSemanticPublicationTransactions._scenario_cold_cli
        )

    @staticmethod
    def _scenario_cold_cli() -> None:
        """Spawn retains the native thread hook and the real public capture graph."""
        reference = workspace.FlextInfraWorkspaceNativeReference
        tm.that(threading.excepthook is threading.__excepthook__, truth=True)
        selections = tm.ok(reference.producer_selections(threading.Thread.__init__, ()))
        before = tm.ok(reference.capture(selections))
        tm.ok(
            any(
                item.kind != "alias"
                and item.supplier == threading.excepthook.__module__
                and item.qualname == threading.excepthook.__qualname__
                for item in before.bindings
            )
        )
        result = tm.ok(u.Cli.run((sys.executable, "-I", "-m", "flext_infra", "--help")))
        tm.ok(u.Cli.process_succeeded(result.outcome))
        tm.ok(reference.compare(before, tm.ok(reference.capture(selections))))

    @staticmethod
    def test_public_workspace_factory_preserves_selected_rope_root(
        tmp_path: Path,
    ) -> None:
        """The injected factory preserves the existing scoped workspace contract."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = package / "consumer.py"
        source = "VALUE = 1\n"
        path.write_text(source, encoding=c.DEFAULT_ENCODING)
        with infra.rope_workspace(root, root) as rope:
            tm.not_none(rope.module(path))
            tm.that(rope.source(path), eq=source)

    def test_joint_phases_reconcile_an_unchanged_initializer_later_owned_by_lazy_init(
        self,
        mod_workspace: Path,
    ) -> None:
        """Joint phases reconcile an initializer that lazy init later owns.

        The unchanged initializer is reconciled against the declared exports.

        """
        u.Tests.run_native_callable(self._scenario_initializer_receipt, mod_workspace)

    @staticmethod
    def _scenario_initializer_receipt(mod_workspace: Path) -> None:
        """Keep the historical initializer proof while consuming declared exports."""
        package = mod_workspace / "src" / mod_workspace.name
        declaration = package / "service.py"
        original = (
            "class DeclaredService:\n"
            "    @staticmethod\n"
            "    def normalize(value: str) -> str:\n"
            "        return value.strip().lower()\n\n"
            "__all__ = ('DeclaredService',)\n"
        )
        declaration.write_text(original, encoding=c.DEFAULT_ENCODING)
        initializer = package / c.Infra.INIT_PY
        states = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            for path in (declaration, initializer)
        )
        plans = tuple(
            m.Infra.CodegenFilePlan(
                project=mod_workspace,
                path=state.path,
                before=state,
                desired_content=(
                    original.replace(".lower()", ".upper()").encode(c.DEFAULT_ENCODING)
                    if state.path == declaration
                    else state.content
                ),
                desired_mode=state.mode,
            )
            for state in states
        )
        tm.ok(
            transformers.FlextInfraSemanticPublication.publish_semantic_artifact_plans(
                plans,
                repository_root=mod_workspace,
                options=m.Infra.SemanticPublicationOptions(
                    projection_roots=(mod_workspace,),
                ),
            ),
        )
        output = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-c",
                    (
                        f"from {mod_workspace.name} import DeclaredService; "
                        "assert DeclaredService.normalize(' live ') == 'LIVE'"
                    ),
                ),
                cwd=mod_workspace,
                options=m.Cli.ProcessOptions(
                    env={"PYTHONPATH": str(package.parent)},
                ),
            ),
        )
        tm.ok(u.Cli.process_succeeded(output.outcome))

    def test_artifact_publication_creates_absent_parent_directories(
        self,
        mod_workspace: Path,
    ) -> None:
        """Artifact publication creates the absent parents of a new destination."""
        u.Tests.run_native_callable(self._scenario_absent_parents, mod_workspace)

    @staticmethod
    def _scenario_absent_parents(mod_workspace: Path) -> None:
        """Publish a new nested module and import it through its real consumer."""
        publication = transformers.FlextInfraSemanticPublication
        package = mod_workspace / "src" / mod_workspace.name
        target = package / "relocated" / "nested" / "service.py"
        source = (
            "class DeclaredService:\n"
            "    @staticmethod\n"
            "    def normalize(value: str) -> str:\n"
            "        return value.strip().upper()\n\n"
            "__all__ = ('DeclaredService',)\n"
        )
        plan = m.Infra.CodegenFilePlan(
            project=mod_workspace,
            path=target,
            before=tm.ok(u.Cli.atomic_read_binary_file_state(target)),
            desired_content=source.encode(c.DEFAULT_ENCODING),
            desired_mode=package.stat().st_mode & 0o666,
        )
        tm.ok(
            publication.publish_semantic_artifact_plans(
                (plan,),
                repository_root=mod_workspace,
                options=m.Infra.SemanticPublicationOptions(
                    projection_roots=(mod_workspace,),
                ),
            )
        )
        consumer = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-c",
                    (
                        f"from {mod_workspace.name}.relocated.nested import "
                        "DeclaredService; "
                        "assert DeclaredService.normalize(' live ') == 'LIVE'"
                    ),
                ),
                cwd=mod_workspace,
                options=m.Cli.ProcessOptions(
                    env={"PYTHONPATH": str(package.parent)},
                ),
            ),
        )
        tm.ok(u.Cli.process_succeeded(consumer.outcome))
        tm.that(target.read_text(encoding=c.DEFAULT_ENCODING), eq=source)

    def test_artifact_publication_retires_old_package_with_its_move(
        self,
        mod_workspace: Path,
    ) -> None:
        """A package move retires the old module and publishes the new one together."""
        u.Tests.run_native_callable(self._scenario_retired_package, mod_workspace)

    @staticmethod
    def _scenario_retired_package(mod_workspace: Path) -> None:
        """The moved module imports through its real consumer; the old one is gone."""
        package = mod_workspace / c.Infra.DEFAULT_SRC_DIR / mod_workspace.name
        previous = package / "previous" / "service.py"
        current = package / "current" / previous.name
        previous.parent.mkdir()
        previous.write_text('VALUE = "previous"\n', encoding=c.DEFAULT_ENCODING)
        original = tm.ok(u.Cli.atomic_read_binary_file_state(previous, required=True))
        desired = 'VALUE = "current"\n'
        plans = (
            m.Infra.CodegenFilePlan(
                project=mod_workspace,
                path=previous,
                before=original,
                desired_content=None,
                desired_mode=None,
            ),
            m.Infra.CodegenFilePlan(
                project=mod_workspace,
                path=current,
                before=tm.ok(u.Cli.atomic_read_binary_file_state(current)),
                desired_content=desired.encode(c.DEFAULT_ENCODING),
                desired_mode=original.mode,
            ),
        )
        published = tm.ok(
            transformers.FlextInfraSemanticPublication.publish_semantic_artifact_plans(
                plans, repository_root=mod_workspace
            )
        )
        tm.that(set(published), eq={previous, current})
        tm.fail(previous.exists())
        tm.that(current.read_text(encoding=c.DEFAULT_ENCODING), eq=desired)
        consumer = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-c",
                    (
                        f"from {package.name}.{current.parent.name}.service "
                        f"import VALUE; assert VALUE == {current.parent.name!r}"
                    ),
                ),
                cwd=mod_workspace,
                options=m.Cli.ProcessOptions(
                    env={c.Infra.ORCHESTRATOR_ENV_PYTHONPATH: str(package.parent)},
                ),
            ),
        )
        tm.ok(u.Cli.process_succeeded(consumer.outcome))

    @pytest.mark.parametrize("unchanged", [False, True])
    def test_stub_retirement_and_consumer_annotations_publish_together(
        self,
        mod_workspace: Path,
        *,
        unchanged: bool,
    ) -> None:
        """An authenticated absent-state stub plan shares its consumer's group."""
        u.Tests.run_native_callable(
            self._scenario_stub_retirement,
            mod_workspace,
            unchanged=unchanged,
        )

    @staticmethod
    def _scenario_stub_retirement(mod_workspace: Path, *, unchanged: bool) -> None:
        """The staged real consumer runs without a retiring local stub."""
        package = mod_workspace / c.Infra.DEFAULT_SRC_DIR / mod_workspace.name
        source = package / "consumer.py"
        stub = source.with_suffix(".pyi")
        desired = "def normalize(value: str) -> str:\n    return value.strip()\n"
        source.write_text(
            desired
            if unchanged
            else desired.replace("value: str", "value").replace(" -> str", ""),
            encoding=c.DEFAULT_ENCODING,
        )
        stub.write_text(
            "def normalize(value: str) -> str: ...\n", encoding=c.DEFAULT_ENCODING
        )
        states = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            for path in (source, stub)
        )
        plans = tuple(
            m.Infra.CodegenFilePlan(
                project=mod_workspace,
                path=state.path,
                before=state,
                desired_content=None
                if state.path == stub
                else desired.encode(c.DEFAULT_ENCODING),
                desired_mode=None if state.path == stub else state.mode,
            )
            for state in states
        )

        def validate(candidate_root: Path) -> p.Result[bool]:
            tm.fail((candidate_root / stub.relative_to(mod_workspace)).exists())
            consumer = tm.ok(
                u.Cli.run(
                    (
                        sys.executable,
                        "-c",
                        (
                            f"from {package.name}.consumer import normalize; assert "
                            f"normalize(' live ') == 'live'"
                        ),
                    ),
                    cwd=candidate_root,
                    options=m.Cli.ProcessOptions(
                        env={
                            c.Infra.ORCHESTRATOR_ENV_PYTHONPATH: str(
                                candidate_root / c.Infra.DEFAULT_SRC_DIR
                            ),
                        }
                    ),
                )
            )
            tm.ok(u.Cli.process_succeeded(consumer.outcome))
            return r[bool].ok(value=True)

        tm.ok(
            transformers.FlextInfraSemanticPublication.publish_semantic_artifact_plans(
                plans,
                repository_root=mod_workspace,
                options=m.Infra.SemanticPublicationOptions(validator=validate),
            )
        )
        tm.fail(stub.exists())
        tm.that(source.read_text(encoding=c.DEFAULT_ENCODING), eq=desired)

    @staticmethod
    def test_no_effect_publication_requires_true_acceptance(
        mod_workspace: Path,
    ) -> None:
        """A successful false result rejects publication without filesystem effects."""
        publication = transformers.FlextInfraSemanticPublication
        before = tuple(
            (path, path.stat().st_mode, path.read_bytes() if path.is_file() else None)
            for path in sorted(mod_workspace.rglob("*"))
        )
        calls = 0
        accepted = False

        def validate(_candidate_root: Path) -> p.Result[bool]:
            nonlocal calls
            calls += 1
            return r[bool].ok(accepted)

        rejected = publication.publish_semantic_file_plans(
            (),
            repository_root=mod_workspace,
            options=m.Infra.SemanticPublicationOptions(validator=validate),
        )
        tm.that(calls, eq=1)
        accepted = True
        published = publication.publish_semantic_file_plans(
            (),
            repository_root=mod_workspace,
            options=m.Infra.SemanticPublicationOptions(validator=validate),
        )
        tm.that(calls, eq=2)
        tm.that(
            tuple(
                (
                    path,
                    path.stat().st_mode,
                    path.read_bytes() if path.is_file() else None,
                )
                for path in sorted(mod_workspace.rglob("*"))
            ),
            eq=before,
        )
        tm.that(tm.ok(published), eq=())
        tm.fail(rejected)

    @staticmethod
    @pytest.mark.parametrize("raises", [False, True])
    def test_no_effect_publication_retains_validator_failure(
        mod_workspace: Path,
        *,
        raises: bool,
    ) -> None:
        """An explicit consumer rejection cannot become a no-effect success."""
        publication = transformers.FlextInfraSemanticPublication
        path = mod_workspace / "consumer.py"
        source = 'raise RuntimeError("consumer rejected")\n'
        path.write_text(source, encoding="utf-8")
        failure = RuntimeError("consumer rejected")

        def reject(candidate_root: Path) -> p.Result[bool]:
            consumer = tm.ok(
                u.Cli.run_raw((
                    sys.executable,
                    str(candidate_root / path.relative_to(mod_workspace)),
                ))
            )
            tm.fail(u.Cli.process_succeeded(consumer.outcome))
            if raises:
                raise failure
            return r[bool].fail(str(failure), exception=failure)

        options = m.Infra.SemanticPublicationOptions(validator=reject)
        if raises:
            with pytest.raises(RuntimeError) as raised:
                publication.publish_semantic_file_plans(
                    (), repository_root=mod_workspace, options=options
                )
            tm.ok(raised.value is failure)
        else:
            rejected = publication.publish_semantic_file_plans(
                (), repository_root=mod_workspace, options=options
            )
            tm.fail(rejected, has=str(failure))
            tm.ok(rejected.exception is failure)
        tm.that(path.read_text(encoding="utf-8"), eq=source)

    @pytest.mark.slow
    @pytest.mark.parametrize("rejected", [False, True])
    def test_unchanged_semantic_entry_validates_generated_public_consumer(
        self,
        tmp_path: Path,
        *,
        rejected: bool,
    ) -> None:
        """An unchanged semantic entry validates the generated public consumer.

        Stale exports cannot be accepted without the entry's gates.

        """
        u.Tests.run_native_callable(
            self._scenario_unchanged_entry,
            tmp_path,
            rejected=rejected,
        )

    @staticmethod
    def _scenario_unchanged_entry(tmp_path: Path, *, rejected: bool) -> None:
        """The real semantic entry cannot accept stale exports without its gates."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        u.Tests.provision_checkout(root)
        notice = u.Infra.copyright_notice(root)
        path = package / "service.py"
        source = (
            f'"""Public candidate service.\n\n{notice}\n"""\n\n'
            "from __future__ import annotations\n\n\n"
            "class FlextTestProjectService:\n"
            '    """Execute the fixture consumer contract."""\n\n'
            "    @staticmethod\n"
            "    def execute() -> bool:\n"
            '        """Return the fixture service health.\n\n'
            "        Returns:\n"
            "            Whether the fixture service is healthy.\n\n"
            '        """\n'
            "        return True\n\n\n"
            + ('raise RuntimeError("consumer rejected")\n\n' if rejected else "")
            + '__all__ = ["FlextTestProjectService"]\n'
        )
        path.write_text(source, encoding="utf-8")
        initializer = package / c.Infra.INIT_PY
        initializer.write_text("", encoding="utf-8")
        original = initializer.read_bytes()
        report: m.Infra.ModOccurrenceReport[m.Infra.ModOccurrence] = (
            m.Infra.ModOccurrenceReport(
                files=frozenset(),
                entries=(),
            )
        )
        with infra.rope_workspace(root) as rope:
            result = codemod.FlextInfraCodemodSemanticApply.apply(
                root,
                report,
                rope,
                workspace_factory=infra.rope_workspace,
            )
        if rejected:
            tm.fail(result)
        else:
            tm.ok(result)
        tm.ok(initializer.read_bytes() != original)
        consumer = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    (
                        f"from {package.name} import FlextTestProjectService; "
                        "assert FlextTestProjectService.execute()"
                    ),
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(
                    env={
                        c.Infra.ORCHESTRATOR_ENV_PYTHONPATH: str(package.parent),
                    },
                ),
            ),
        )
        tm.that(u.Cli.process_succeeded(consumer.outcome), eq=not rejected)
        if rejected:
            tm.that(consumer.stderr, has="consumer rejected")
        tm.that(path.read_text(encoding="utf-8"), eq=source)

    def test_publication_refreshes_warm_normalized_export_route(
        self,
        mod_workspace: Path,
    ) -> None:
        """Publication refreshes the warm normalized export route.

        A moved declaration routes identically in warm and fresh consumers.

        """
        u.Tests.run_native_callable(self._scenario_warm_exports, mod_workspace)

    @staticmethod
    def _scenario_warm_exports(mod_workspace: Path) -> None:
        """A moved declaration routes identically in warm and fresh consumers."""
        package = mod_workspace / c.Infra.DEFAULT_SRC_DIR / mod_workspace.name
        previous = package / "previous.py"
        current = package / "current.py"
        consumer_path = package / "consumer.py"
        for path, exported in ((previous, True), (current, False)):
            path.write_text(
                "class DeclaredService:\n"
                "    @staticmethod\n"
                "    def execute() -> str:\n"
                f"        return {path.stem!r}\n\n"
                f"__all__ = {['DeclaredService'] if exported else []!r}\n",
                encoding=c.DEFAULT_ENCODING,
            )
        tm.ok(
            transformers.FlextInfraSemanticPublication.publish_semantic_file_plans(
                (),
                repository_root=mod_workspace,
                options=m.Infra.SemanticPublicationOptions(
                    projection_roots=(mod_workspace,)
                ),
            ),
        )
        original_source = (
            f"from {package.name}.{previous.stem} import DeclaredService\n\n"
            "def run() -> str:\n"
            "    return DeclaredService.execute()\n"
        )
        warmed = tm.not_none(
            u.Infra.normalize_import_source(
                project_root=mod_workspace,
                file_path=consumer_path,
                source=original_source,
            ),
        )
        tm.that(warmed, has=f"from {package.name} import DeclaredService\n")
        candidate = original_source.replace(previous.stem, current.stem)
        plans: list[m.Infra.SemanticFilePlan] = []
        for path in (previous, current):
            before = tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            outgoing: t.StrSequence = ["DeclaredService"] if path == previous else []
            incoming: t.StrSequence = [] if path == previous else ["DeclaredService"]
            plans.append(
                m.Infra.SemanticFilePlan(
                    project=mod_workspace,
                    path=path,
                    before=before,
                    desired_content=tm
                    .not_none(before.content)
                    .decode(c.DEFAULT_ENCODING)
                    .replace(
                        f"__all__ = {outgoing!r}",
                        f"__all__ = {incoming!r}",
                    )
                    .encode(c.DEFAULT_ENCODING),
                    desired_mode=before.mode,
                ),
            )

        def validate(candidate_root: Path) -> p.Result[bool]:
            candidate_consumer = candidate_root / consumer_path.relative_to(
                mod_workspace
            )
            normalized = tm.not_none(
                u.Infra.normalize_import_source(
                    project_root=candidate_root,
                    file_path=candidate_consumer,
                    source=candidate,
                ),
            )
            tm.that(normalized, eq=warmed)
            tm.that(
                u.Infra.normalize_import_source(
                    project_root=candidate_root,
                    file_path=candidate_consumer,
                    source=normalized,
                ),
                eq=None,
            )
            fresh = tm.ok(
                u.Cli.run(
                    (
                        sys.executable,
                        "-c",
                        (
                            "from pathlib import Path\n"
                            "from flext_infra import u\n"
                            "normalized = u.Infra.normalize_import_source(\n"
                            f"    project_root=Path({str(candidate_root)!r}),\n"
                            f"    file_path=Path({str(candidate_consumer)!r}),\n"
                            f"    source={candidate!r},\n"
                            ")\n"
                            f"assert normalized == {normalized!r}\n"
                            f"{normalized}\n"
                            f"assert run() == {current.stem!r}\n"
                        ),
                    ),
                    cwd=candidate_root,
                    options=m.Cli.ProcessOptions(
                        env={
                            c.Infra.ORCHESTRATOR_ENV_PYTHONPATH: str(
                                candidate_root
                                / package.parent.relative_to(mod_workspace)
                            ),
                        },
                    ),
                ),
            )
            tm.ok(u.Cli.process_succeeded(fresh.outcome))
            return r[bool].ok(value=True)

        tm.ok(
            transformers.FlextInfraSemanticPublication.publish_semantic_file_plans(
                plans,
                repository_root=mod_workspace,
                options=m.Infra.SemanticPublicationOptions(
                    projection_roots=(mod_workspace,), validator=validate
                ),
            ),
        )
        initializer = package / c.Infra.INIT_PY
        published = initializer.read_bytes()
        tm.ok(
            transformers.FlextInfraSemanticPublication.publish_semantic_file_plans(
                (),
                repository_root=mod_workspace,
                options=m.Infra.SemanticPublicationOptions(
                    projection_roots=(mod_workspace,), validator=validate
                ),
            ),
        )
        tm.that(initializer.read_bytes(), eq=published)

    def test_projection_only_publication_serves_real_public_consumer(
        self,
        mod_workspace: Path,
    ) -> None:
        """A projection-only publication generates declared exports.

        Authored work in progress stays unchanged.

        """
        u.Tests.run_native_callable(self._scenario_projection_consumer, mod_workspace)

    @staticmethod
    def _scenario_projection_consumer(mod_workspace: Path) -> None:
        """Generate declared exports without changing authored WIP."""
        package = mod_workspace / "src" / mod_workspace.name
        declaration = package / "service.py"
        source = "class DeclaredService:\n    pass\n\n__all__ = ['DeclaredService']\n"
        declaration.write_text(source, encoding="utf-8")
        initializer = package / c.Infra.INIT_PY
        initializer.write_text("", encoding="utf-8")
        original = initializer.read_bytes()
        tm.ok(
            transformers.FlextInfraSemanticPublication.publish_semantic_file_plans(
                (),
                repository_root=mod_workspace,
                options=m.Infra.SemanticPublicationOptions(
                    projection_roots=(mod_workspace,)
                ),
            )
        )
        tm.that(initializer.read_bytes() != original, eq=True)
        consumer = tm.ok(
            u.Cli.run(
                (
                    sys.executable,
                    "-c",
                    (
                        f"from {mod_workspace.name} import DeclaredService; "
                        "assert isinstance(DeclaredService(), DeclaredService)"
                    ),
                ),
                cwd=mod_workspace,
                options=m.Cli.ProcessOptions(
                    env={c.Infra.ORCHESTRATOR_ENV_PYTHONPATH: str(package.parent)},
                ),
            ),
        )
        tm.ok(u.Cli.process_succeeded(consumer.outcome))
        tm.that(declaration.read_text(encoding="utf-8"), eq=source)
