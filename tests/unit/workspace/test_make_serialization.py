"""Public runtime contract for the config-owned Make operation graph."""

from __future__ import annotations

import sys
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeoutError
from pathlib import Path

import pytest
from filelock import FileLock
from flext_core import r
from flext_infra import c, config, m, p, u
from flext_infra.codegen.conform import FlextInfraCodegenConform
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector
from flext_infra.workspace.make_generation import FlextInfraMakeGenerationService
from flext_infra.workspace.make_serialization import FlextInfraMakeSerializationService
from flext_tests import tm
from tests import u as test_u


_MAKE = config.Infra.codegen.make
_OPERATIONS = {operation.name: operation for operation in _MAKE.operations}
_POLICY_FAILURE_CASES = tuple(
    (verb, handler, True, "read-only")
    for verb in _MAKE.verbs
    for handler in verb.handlers
    if handler.apply_policy == "never"
) + tuple(
    (verb, handler, False, "requires")
    for verb in _MAKE.verbs
    for handler in verb.handlers
    if handler.apply_policy == "required"
)
_POLICY_FAILURE_IDS = tuple(
    f"{verb.name}-{handler.what}-{'apply' if applying else 'read'}"
    for verb, handler, applying, _message in _POLICY_FAILURE_CASES
)
_REQUIRED_INPUT_CASES = tuple(
    (verb, handler)
    for verb in _MAKE.verbs
    for handler in verb.handlers
    if handler.required_inputs
)
_REQUIRED_INPUT_IDS = tuple(
    f"{verb.name}-{handler.what}" for verb, handler in _REQUIRED_INPUT_CASES
)


@pytest.fixture
def make_repository(tmp_path: Path) -> Path:
    """Create one provider-governed standalone repository fixture."""
    root = tmp_path / "make-runtime-probe"
    package = root / "src" / "make_runtime_probe"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("", encoding="utf-8")
    (root / c.Infra.PYPROJECT_FILENAME).write_text(
        "[project]\n"
        'name = "make-runtime-probe"\n'
        'version = "0.1.0"\n'
        'requires-python = ">=3.13,<3.14"\n',
        encoding="utf-8",
    )
    (root / c.Infra.MAKEFILE_FILENAME).write_text(
        "# selected Make owner\n", encoding="utf-8"
    )
    provider = config.Infra.codegen.default_provider_spec
    test_u.Tests.initialize_git_repo(
        root, f"{provider.base_url.rstrip('/')}/make-runtime-probe.git"
    )
    return root


class TestsFlextInfraMakeSerialization:
    """Prove current Make policy and dispatch through the public service boundary."""

    @staticmethod
    def _service(
        root: Path,
        verb: m.Infra.MakeVerbSpec,
        handler: m.Infra.MakeHandlerSpec,
        *,
        applying: bool,
        makefile: Path | None = None,
        make_level: int = 0,
    ) -> FlextInfraMakeSerializationService:
        return FlextInfraMakeSerializationService(
            workspace_root=root,
            makefile=makefile or root / c.Infra.MAKEFILE_FILENAME,
            verb=verb.name,
            selector_value=handler.what,
            apply_token=(_MAKE.apply_value if applying else _MAKE.apply_absent_value),
            make_level=make_level,
        )

    @staticmethod
    def _reset_input_environment(monkeypatch: pytest.MonkeyPatch) -> None:
        for input_spec in _MAKE.inputs:
            for variable in input_spec.variables:
                monkeypatch.delenv(
                    f"{_MAKE.input_environment_prefix}{variable}", raising=False
                )

    @staticmethod
    def _seed_required_inputs(
        monkeypatch: pytest.MonkeyPatch, handler: m.Infra.MakeHandlerSpec
    ) -> None:
        input_catalog = {item.name: item for item in _MAKE.inputs}
        for input_name in handler.required_inputs:
            input_spec = input_catalog[input_name]
            raw_value = "Y" if input_spec.codec == "boolean" else input_spec.name
            monkeypatch.setenv(
                f"{_MAKE.input_environment_prefix}{input_spec.variables[0]}", raw_value
            )

    @staticmethod
    def _install_owned_environment(root: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        actual_interpreter = Path(sys.executable).resolve()
        environment = root / config.Infra.tooling.tools.pyright.path_rules.venv_name
        environment.mkdir(parents=True)
        fixture_interpreter = environment / actual_interpreter.name
        fixture_interpreter.symlink_to(actual_interpreter)
        monkeypatch.setattr(sys, "executable", str(fixture_interpreter))

    @staticmethod
    def _help_case() -> tuple[m.Infra.MakeVerbSpec, m.Infra.MakeHandlerSpec]:
        return next(
            (verb, handler)
            for verb in _MAKE.verbs
            for handler in verb.handlers
            if handler.default
            and (operation := _OPERATIONS[verb.operation]).executor == "bootstrap"
            and operation.scope == "self"
            and operation.consistency == "none"
            and operation.mutation == "never"
        )

    @staticmethod
    def _single_flight_git_case() -> tuple[
        m.Infra.MakeVerbSpec, m.Infra.MakeHandlerSpec
    ]:
        return next(
            (verb, handler)
            for verb in _MAKE.verbs
            for handler in verb.handlers
            if handler.default
            and handler.apply_policy == "never"
            and (operation := _OPERATIONS[verb.operation]).consistency
            == "single-flight"
            and operation.mutation == "apply"
            and "git" in operation.requires
            and "environment" not in operation.requires
        )

    def test_config_owns_one_relative_excluded_lock(self) -> None:
        """The typed SSOT owns one safe checkout-relative lock."""
        serialization = _MAKE.serialization

        assert serialization.timeout_seconds > 0
        assert not serialization.lock_path.is_absolute()
        assert serialization.lock_path in serialization.snapshot_excludes
        assert all(not path.is_absolute() for path in serialization.snapshot_excludes)

    def test_serialization_model_rejects_unsafe_paths(self, tmp_path: Path) -> None:
        """Invalid lock ownership is rejected by the typed model."""
        serialization = _MAKE.serialization

        with pytest.raises(ValueError, match="must be snapshot-excluded"):
            m.Infra.MakeSerializationSpec(
                lock_path=serialization.lock_path,
                snapshot_excludes=tuple(
                    path
                    for path in serialization.snapshot_excludes
                    if path != serialization.lock_path
                ),
                timeout_seconds=serialization.timeout_seconds,
            )
        with pytest.raises(ValueError, match="lock paths must be repository-relative"):
            m.Infra.MakeSerializationSpec(
                lock_path=(tmp_path / serialization.lock_path).resolve(),
                snapshot_excludes=serialization.snapshot_excludes,
                timeout_seconds=serialization.timeout_seconds,
            )
        with pytest.raises(
            ValueError, match="snapshot_excludes must be repository-relative"
        ):
            m.Infra.MakeSerializationSpec(
                lock_path=serialization.lock_path,
                snapshot_excludes=(
                    *serialization.snapshot_excludes,
                    (tmp_path / "outside").resolve(),
                ),
                timeout_seconds=serialization.timeout_seconds,
            )

    def test_hook_targets_derive_from_the_handler_graph(self) -> None:
        """Hook aliases remain a projection of configured verbs and handlers."""
        expected = tuple(
            target
            for verb in _MAKE.verbs
            for phase in ("pre", "post")
            for target in (
                f"{phase}-{verb.name}",
                *(f"{phase}-{verb.name}-{handler.what}" for handler in verb.handlers),
            )
        )

        assert _MAKE.hook_targets == expected

    def test_workflow_steps_resolve_through_the_public_boundary(
        self, make_repository: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Every workflow row reaches Makefile ownership after typed resolution."""
        self._install_owned_environment(make_repository, monkeypatch)
        missing_makefile = make_repository / f"{c.Infra.MAKEFILE_FILENAME}.missing"
        verbs = {verb.name: verb for verb in _MAKE.verbs}

        for step in _MAKE.workflow:
            self._reset_input_environment(monkeypatch)
            verb = verbs[step.verb]
            handler = next(item for item in verb.handlers if item.what == step.what)
            self._seed_required_inputs(monkeypatch, handler)
            executed = self._service(
                make_repository,
                verb,
                handler,
                applying=step.apply,
                makefile=missing_makefile,
            ).execute()

            assert executed.failure, f"workflow step unexpectedly ran: {step}"
            assert "selected Make owner does not exist" in (executed.error or ""), step

    @pytest.mark.parametrize(
        ("verb", "handler", "applying", "message"),
        _POLICY_FAILURE_CASES,
        ids=_POLICY_FAILURE_IDS,
    )
    def test_handler_apply_policy_fails_closed_at_the_public_boundary(
        self,
        make_repository: Path,
        monkeypatch: pytest.MonkeyPatch,
        verb: m.Infra.MakeVerbSpec,
        handler: m.Infra.MakeHandlerSpec,
        message: str,
        *,
        applying: bool,
    ) -> None:
        """Every forbidden APPLY polarity is rejected before dispatch."""
        self._reset_input_environment(monkeypatch)

        executed = self._service(
            make_repository, verb, handler, applying=applying
        ).execute()

        assert executed.failure
        assert message in (executed.error or "")

    @pytest.mark.parametrize(
        ("verb", "handler"), _REQUIRED_INPUT_CASES, ids=_REQUIRED_INPUT_IDS
    )
    def test_required_inputs_fail_closed_at_the_public_boundary(
        self,
        make_repository: Path,
        monkeypatch: pytest.MonkeyPatch,
        verb: m.Infra.MakeVerbSpec,
        handler: m.Infra.MakeHandlerSpec,
    ) -> None:
        """Missing config-declared inputs never reach an operation owner."""
        self._reset_input_environment(monkeypatch)

        executed = self._service(
            make_repository, verb, handler, applying=handler.apply_policy != "never"
        ).execute()

        assert executed.failure
        assert all(name in (executed.error or "") for name in handler.required_inputs)

    def test_input_aliases_and_boolean_codec_fail_closed_publicly(
        self, make_repository: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Malformed external input is rejected without testing parser internals."""
        aliased = next(item for item in _MAKE.inputs if len(item.variables) > 1)
        alias_verb, alias_handler = next(
            (verb, handler)
            for verb in _MAKE.verbs
            for handler in verb.handlers
            if handler.default and aliased.name in _OPERATIONS[verb.operation].inputs
        )
        self._reset_input_environment(monkeypatch)
        for index, variable in enumerate(aliased.variables[:2]):
            monkeypatch.setenv(
                f"{_MAKE.input_environment_prefix}{variable}", f"fixture-{index}"
            )

        divergent = self._service(
            make_repository,
            alias_verb,
            alias_handler,
            applying=alias_handler.apply_policy == "required",
        ).execute()

        assert divergent.failure
        assert "divergent aliases" in (divergent.error or "")

        boolean = next(item for item in _MAKE.inputs if item.codec == "boolean")
        boolean_verb, boolean_handler = next(
            (verb, handler)
            for verb in _MAKE.verbs
            for handler in verb.handlers
            if handler.default and boolean.name in _OPERATIONS[verb.operation].inputs
        )
        self._reset_input_environment(monkeypatch)
        monkeypatch.setenv(
            f"{_MAKE.input_environment_prefix}{boolean.variables[0]}", "truthy"
        )

        malformed_boolean = self._service(
            make_repository,
            boolean_verb,
            boolean_handler,
            applying=boolean_handler.apply_policy == "required",
        ).execute()

        assert malformed_boolean.failure
        assert "Make boolean input" in (malformed_boolean.error or "")

    def test_control_separators_fail_closed_at_the_public_boundary(
        self, make_repository: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A control separator cannot cross any configured input codec."""
        input_spec, verb, handler = next(
            (input_spec, verb, handler)
            for input_spec in _MAKE.inputs
            for verb in _MAKE.verbs
            for handler in verb.handlers
            if handler.default and input_spec.name in _OPERATIONS[verb.operation].inputs
        )
        self._reset_input_environment(monkeypatch)
        monkeypatch.setenv(
            f"{_MAKE.input_environment_prefix}{input_spec.variables[0]}",
            f"{input_spec.name}\n{input_spec.name}",
        )

        executed = self._service(
            make_repository, verb, handler, applying=handler.apply_policy == "required"
        ).execute()

        assert executed.failure
        assert "control separators" in (executed.error or "")

    def test_consistency_controls_the_governing_root_lock(
        self, make_repository: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Consistency-none bypasses the lock while single-flight waits for it."""
        self._reset_input_environment(monkeypatch)
        help_verb, help_handler = self._help_case()
        single_flight_verb, single_flight_handler = self._single_flight_git_case()
        lock_path = (make_repository / _MAKE.serialization.lock_path).resolve()
        lock_path.parent.mkdir(parents=True)

        with ThreadPoolExecutor(max_workers=1) as executor:
            with FileLock(
                lock_path, timeout=0, fallback_to_soft=False, preserve_lock_file=True
            ):
                bypassed = self._service(
                    make_repository, help_verb, help_handler, applying=False
                ).execute()
                assert bypassed.success, bypassed.error

                pending = executor.submit(
                    self._service(
                        make_repository,
                        single_flight_verb,
                        single_flight_handler,
                        applying=False,
                    ).execute
                )
                with pytest.raises(FutureTimeoutError):
                    pending.result(timeout=0.1)

            completed = pending.result(timeout=10)

        assert completed.success, completed.error

    def test_read_only_operation_rejects_workspace_drift(
        self, make_repository: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The public guard rejects writes made by a read-only owner."""
        verb, handler = self._help_case()
        original_emit = u.Cli.emit_raw

        def emit_and_drift(text: str) -> None:
            original_emit(text)
            (make_repository / "read-only-drift.txt").write_text(
                "unexpected mutation\n", encoding="utf-8"
            )

        monkeypatch.setattr(u.Cli, "emit_raw", emit_and_drift)

        executed = self._service(
            make_repository, verb, handler, applying=False
        ).execute()

        assert executed.failure
        assert "workspace changed during read-only Make operation" in (
            executed.error or ""
        )
        assert "read-only-drift.txt" in (executed.error or "")

    def test_reentry_and_makefile_ownership_fail_closed(
        self, make_repository: Path
    ) -> None:
        """Only a top-level call and its checkout-owned Makefile may execute."""
        verb, handler = self._help_case()

        reentered = self._service(
            make_repository, verb, handler, applying=False, make_level=1
        ).execute()
        assert reentered.failure
        assert "public Make reentry is forbidden" in (reentered.error or "")

        missing = make_repository / f"{c.Infra.MAKEFILE_FILENAME}.missing"
        missing_owner = self._service(
            make_repository, verb, handler, applying=False, makefile=missing
        ).execute()
        assert missing_owner.failure
        assert "selected Make owner does not exist" in (missing_owner.error or "")

        foreign = make_repository.parent / c.Infra.MAKEFILE_FILENAME
        foreign.write_text("# foreign Make owner\n", encoding="utf-8")
        foreign_owner = self._service(
            make_repository, verb, handler, applying=False, makefile=foreign
        ).execute()
        assert foreign_owner.failure
        assert "must belong to the invoked checkout" in (foreign_owner.error or "")

    def test_conform_and_generation_dispatch_to_distinct_public_owners(
        self, make_repository: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Read-only conform never aliases generation publication."""
        self._install_owned_environment(make_repository, monkeypatch)
        verbs = {verb.name: verb for verb in _MAKE.verbs}
        conform = verbs["conform"]
        generation = verbs["gen"]
        conform_handler = next(
            handler for handler in conform.handlers if handler.default
        )
        generation_handler = next(
            handler for handler in generation.handlers if handler.default
        )
        calls: list[tuple[str, str, bool]] = []

        def conform_execute(
            service: FlextInfraCodegenConform,
        ) -> p.Result[m.Infra.CodegenResult]:
            context = service.initial_execution_context
            assert context is not None
            calls.append(("conform", context.invocation.operation.name, False))
            return r[m.Infra.CodegenResult].fail("conform-owner-sentinel")

        def generation_execute_for(
            context: m.Infra.MakeExecutionContext, *, applying: bool
        ) -> p.Result[m.Infra.CodegenResult]:
            calls.append(("generate", context.invocation.operation.name, applying))
            return r[m.Infra.CodegenResult].fail("generation-owner-sentinel")

        monkeypatch.setattr(FlextInfraCodegenConform, "execute", conform_execute)
        monkeypatch.setattr(
            FlextInfraMakeGenerationService,
            "execute_for",
            staticmethod(generation_execute_for),
        )

        conformed = self._service(
            make_repository, conform, conform_handler, applying=False
        ).execute()
        generated = self._service(
            make_repository, generation, generation_handler, applying=True
        ).execute()

        assert conformed.failure
        assert "conform-owner-sentinel" in (conformed.error or "")
        assert generated.failure
        assert "generation-owner-sentinel" in (generated.error or "")
        assert calls == [
            ("conform", conform.operation, False),
            ("generate", generation.operation, True),
        ]
        assert conform.operation != generation.operation

    def test_repository_extension_dispatches_through_the_script_owner(
        self, make_repository: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A typed repository extension reaches its declared dispatcher."""
        self._reset_input_environment(monkeypatch)
        self._install_owned_environment(make_repository, monkeypatch)
        script_operation = next(
            operation
            for operation in _MAKE.operations
            if operation.executor == "script"
        )
        applying = script_operation.mutation == "apply"
        handler = m.Infra.MakeHandlerSpec(
            what="fixture",
            default=True,
            apply_policy="required" if applying else "never",
            apply_default=applying,
        )
        verb = m.Infra.MakeVerbSpec(
            name="fixture-dispatch",
            operation=script_operation.name,
            handlers=(handler,),
        )
        dispatcher = make_repository / "scripts" / "dispatch.py"
        dispatcher.parent.mkdir(parents=True)
        dispatcher.write_text(
            "import sys\n"
            f"raise SystemExit(0 if sys.argv[1:] == "
            f"{[verb.name, handler.what]!r} else 23)\n",
            encoding="utf-8",
        )
        workspace: m.Infra.WorkspaceSpec = tm.ok(
            FlextInfraWorkspaceDetector.load_workspace_spec(make_repository)
        )
        repository = workspace.repository.model_copy(
            update={
                "extra_verbs": (verb,),
                "script_dispatch": m.Infra.ScriptDispatchSpec(
                    dispatcher=dispatcher.relative_to(make_repository).as_posix()
                ),
            }
        )
        extended_workspace = workspace.model_copy(update={"repository": repository})
        manifest = (
            make_repository / c.CONFIG_DIR_NAME / c.Infra.WORKSPACE_MANIFEST_FILENAME
        )
        manifest.parent.mkdir(parents=True)
        tm.ok(
            u.Cli.yaml_dump(
                manifest, extended_workspace.model_dump(mode="json", exclude_none=True)
            )
        )

        executed = self._service(
            make_repository, verb, handler, applying=applying
        ).execute()

        assert executed.success, executed.error
