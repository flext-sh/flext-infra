"""Integration tests for current ``flext_infra`` public cross-module flows."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from flext_infra import config, m, r, u
from flext_infra.workspace.detector import FlextInfraWorkspaceDetector
from flext_infra.workspace.make_generation import FlextInfraMakeGenerationService
from flext_infra.workspace.make_serialization import FlextInfraMakeSerializationService
from flext_tests import tm
from tests import u as test_u

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = [pytest.mark.integration]


class TestsFlextInfraIntegrationInfraIntegration:
    """Integration tests for the current infrastructure runtime surfaces."""

    def test_detector_and_make_services_share_typed_context(
        self, tmp_path: Path
    ) -> None:
        """Route one isolated repository through detector, serializer, and generator."""
        root = tmp_path / "integration-probe"
        (root / "src" / "integration_probe").mkdir(parents=True)
        (root / "src" / "integration_probe" / "__init__.py").write_text(
            "", encoding="utf-8"
        )
        (root / "pyproject.toml").write_text(
            "[project]\n"
            'name = "integration-probe"\n'
            'version = "0.1.0"\n'
            'requires-python = ">=3.13,<3.14"\n',
            encoding="utf-8",
        )
        makefile = root / "Makefile"
        makefile.write_text("# selected Make owner\n", encoding="utf-8")
        provider = config.Infra.codegen.default_provider_spec
        test_u.Tests.initialize_git_repo(
            root, f"{provider.base_url.rstrip('/')}/integration-probe.git"
        )

        workspace: m.Infra.WorkspaceSpec = tm.ok(
            FlextInfraWorkspaceDetector.load_workspace_spec(root)
        )
        target: m.Infra.RepositoryConformTarget = tm.ok(
            FlextInfraWorkspaceDetector.conform_target(root, workspace)
        )
        tm.that(target.repository, eq=workspace.repository)

        make = config.Infra.codegen.make
        operations = {operation.name: operation for operation in make.operations}
        help_verb = next(
            verb
            for verb in make.verbs
            if operations[verb.operation].executor == "bootstrap"
            and operations[verb.operation].scope == "self"
        )
        serialized = FlextInfraMakeSerializationService.model_validate({
            "workspace_root": root,
            "verb": help_verb.name,
            "makefile": makefile,
            "selector_value": help_verb.default_what,
            "apply_token": make.apply_absent_value,
            "make_level": 0,
        })
        tm.ok(serialized.execute())

        generation_operation = next(
            operation
            for operation in make.operations
            if operation.executor == "generation"
        )
        generation_verb = next(
            verb for verb in make.verbs if verb.operation == generation_operation.name
        )
        generation_handler = next(
            handler
            for handler in generation_verb.handlers
            if handler.what == generation_verb.default_what
        )
        profile = next(
            item
            for item in config.Infra.codegen.profiles
            if item.name == target.make_profile
        )
        context = m.Infra.MakeExecutionContext(
            workspace_root=root,
            workspace=workspace,
            target=target,
            profile=profile,
            environment_root=root,
            targets=(
                m.Infra.MakeTargetSpec(repository=target.repository, root=target.root),
            ),
            invocation=m.Infra.MakeInvocationSpec(
                verb=generation_verb,
                operation=generation_operation,
                handler=generation_handler,
                applying=False,
                target_scope="profile",
                inputs=(),
            ),
            make=make,
        )

        tm.fail(
            FlextInfraMakeGenerationService.execute_for(context, applying=False),
            has="generated surface drift detected",
        )

    def test_output_methods_are_callable_via_public_facade(self) -> None:
        """Expose reporting methods through the real CLI utility facade."""
        for method in (
            u.Cli.status,
            u.Cli.summary,
            u.Cli.error,
            u.Cli.warning,
            u.Cli.info,
            u.Cli.header,
            u.Cli.progress,
        ):
            tm.that(callable(method), eq=True)

    def test_service_result_chaining_with_map(self) -> None:
        """Preserve values across consecutive result mappings."""
        result = r[int].ok(10).map(lambda value: value * 2).map(lambda value: value + 5)
        tm.ok(result)
        tm.that(result.value, eq=25)

    def test_service_result_chaining_with_flat_map(self) -> None:
        """Compose result-producing services without leaving the result boundary."""
        result = (
            r[int]
            .ok(10)
            .flat_map(lambda value: r[int].ok(value * 2))
            .flat_map(lambda value: r[int].ok(value + 5))
        )
        tm.ok(result)
        tm.that(result.value, eq=25)

    def test_service_result_chaining_failure_propagation(self) -> None:
        """Stop a chain at the first failure and preserve its diagnostic."""
        result = (
            r[int]
            .ok(10)
            .flat_map(lambda value: r[int].ok(value * 2))
            .flat_map(lambda _: r[int].fail("intentional error"))
            .flat_map(lambda value: r[int].ok(value + 5))
        )
        tm.fail(result)
        tm.that(result.error, is_=str)
        tm.that(result.error, has="intentional error")

    def test_service_result_chaining_with_mixed_operations(self) -> None:
        """Compose map and flat-map operations through one typed result."""
        result = (
            r[int]
            .ok(5)
            .map(lambda value: value * 2)
            .flat_map(lambda value: r[int].ok(value + 3))
            .map(lambda value: value * 2)
        )
        tm.ok(result)
        tm.that(result.value, eq=26)

    def test_cli_capture_git_current_branch_in_real_repo(self, tmp_path: Path) -> None:
        """Detect a branch through the canonical CLI runtime surface."""
        repo_root = tmp_path / "repo"
        repo_root.mkdir()
        tm.ok(u.Cli.run_checked(["git", "init"], cwd=repo_root))
        tm.ok(
            u.Cli.run_checked(
                ["git", "config", "user.email", "infra@example.com"], cwd=repo_root
            )
        )
        tm.ok(
            u.Cli.run_checked(
                ["git", "config", "user.name", "Infra Test"], cwd=repo_root
            )
        )
        (repo_root / "README.md").write_text("infra test\n", encoding="utf-8")
        tm.ok(u.Cli.run_checked(["git", "add", "README.md"], cwd=repo_root))
        tm.ok(u.Cli.run_checked(["git", "commit", "-m", "initial"], cwd=repo_root))
        branch: str = tm.ok(
            u.Cli.capture(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=repo_root)
        )
        tm.that(branch, ne="")

    def test_command_runner_capture_executes_real_command(self) -> None:
        """Capture a real external command through the public CLI utility."""
        captured: str = tm.ok(
            u.Cli.capture(["python3", "-c", "print('infra-ok')"])
        )
        tm.that(captured, eq="infra-ok")


__all__: tuple[str, ...] = ()
