"""Real local installation preserves consumer resolution and isolation.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
import sysconfig
from pathlib import Path
from textwrap import dedent

import pytest

from flext_infra import config
from tests import c, m, tm, u


class TestsFlextInfraBindingInstall:
    """Exercise the public binding CLI with real consumer and supplier packages."""

    @staticmethod
    def _seed_candidate_projects(
        supplier: Path,
        consumer: Path,
        extra: Path,
        workspace: Path,
        *,
        scenario: str,
    ) -> None:
        """Initialize the governed consumer, supplier, and extra roots.

        The composed-member scenario makes the consumer a workspace member:
        its runtime environment is the workspace's, so its own environment
        path must not borrow it.
        """
        if scenario == "borrowed-member":
            u.Tests.WorktreeFixture.initialize_governed_project(
                workspace,
                "binding-workspace",
                beads=u.Tests.BeadsIdentity(
                    workspace="binding-workspace",
                    database="binding-workspace",
                    issue_prefix="binding-workspace",
                ),
            )
        for root, name in (
            (supplier, "binding-candidate"),
            (consumer, "binding-consumer"),
        ):
            u.Tests.WorktreeFixture.initialize_governed_project(
                root,
                name,
                beads=u.Tests.BeadsIdentity(
                    workspace=name,
                    database=name,
                    issue_prefix=name,
                ),
            )
        extra.mkdir()
        for root, name, optional in (
            (extra, "binding-extra", ""),
            (
                supplier,
                "binding-candidate",
                (
                    "\n[project.optional-dependencies]\n"
                    f'feature = ["binding-extra @ {extra.as_uri()}"]\n'
                ),
            ),
        ):
            dependencies = (
                f'dependencies = ["binding-candidate @ '
                f'{(workspace / "unavailable-candidate").as_uri()}"]\n'
                if scenario == "transitive-source" and root == extra
                else ""
            )
            (root / c.PYPROJECT_FILENAME).write_text(
                '[build-system]\nrequires = ["setuptools"]\n'
                'build-backend = "setuptools.build_meta"\n'
                f'[project]\nname = "{name}"\nversion = "1.0.0"\n'
                f"{dependencies}{optional}"
                f'\n[tool.setuptools]\npy-modules = ["{name.replace("-", "_")}"]\n',
                encoding=c.DEFAULT_ENCODING,
            )
            (root / f"{name.replace('-', '_')}.py").write_text(
                'VALUE = "installed"\n',
                encoding=c.DEFAULT_ENCODING,
            )

    @staticmethod
    def _declare_consumer_dependency(scenario: str, consumer: Path) -> bytes:
        """Write the consumer's declared dependency contract for one scenario.

        Returns:
            The declaration bytes the binding run must leave untouched.

        """
        inactive = "; python_version < '0'"
        marker = inactive if scenario == "inactive" else ""
        policy = tuple(
            declaration
            for enabled, declaration in (
                (
                    scenario in {"override", "override-constraint"},
                    'override-dependencies = ["binding-candidate==1"]',
                ),
                (
                    scenario == "inactive-override",
                    f'override-dependencies = ["binding-candidate==1{inactive}"]',
                ),
                (
                    scenario in {"constraint", "override-constraint"},
                    'constraint-dependencies = ["binding-candidate>=2"]',
                ),
            )
            if enabled
        )
        constraints = "\n[tool.uv]\n" + "\n".join(policy) if policy else ""
        minimum = (
            "2"
            if scenario in {"override", "override-constraint", "inactive-override"}
            else "1"
        )
        declaration = consumer / c.PYPROJECT_FILENAME
        declaration.write_text(
            '[project]\nname = "binding-consumer"\nversion = "1.0.0"\n'
            f'dependencies = ["Binding_Candidate[feature]>={minimum}{marker}"]\n'
            f"{constraints}",
            encoding=c.DEFAULT_ENCODING,
        )
        return declaration.read_bytes()

    @staticmethod
    def _compose_consumer_environment(
        tmp_path: Path,
        consumer: Path,
        workspace: Path,
        *,
        scenario: str,
    ) -> Path:
        """Materialize the consumer runtime environment for one scenario.

        The composed member borrows the workspace environment through its own
        symlink; the borrowed scenario swaps the physical directory for a
        foreign symlinked environment.

        Returns:
            The consumer's resolved runtime environment directory.

        """
        if scenario == "borrowed-member":
            u.Tests.WorktreeFixture.attach_submodule(
                workspace,
                consumer,
                distribution="binding-consumer",
                relative_path=consumer.name,
            )
            tm.ok(u.Tests.create_python_environment(workspace))
            (consumer / c.Infra.ENVIRONMENT_DIRECTORY).symlink_to(
                u.Infra.runtime_environment_dir(consumer),
                target_is_directory=True,
            )
        else:
            tm.ok(u.Tests.create_python_environment(consumer))
        environment = u.Infra.runtime_environment_dir(consumer)
        if scenario == "borrowed":
            foreign = tmp_path / "foreign-environment"
            environment.rename(foreign)
            environment.symlink_to(foreign, target_is_directory=True)
        return environment

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize(
        "scenario",
        [
            "extras",
            "transitive-source",
            "constraint",
            "inactive",
            "borrowed",
            "borrowed-member",
            "override",
            "override-constraint",
            "inactive-override",
        ],
    )
    def test_binding_uses_consumer_contract(
        tmp_path: Path,
        scenario: str,
    ) -> None:
        """Install extras or reject incompatible, inactive, and borrowed candidates."""
        supplier, consumer, extra, workspace = (
            tmp_path / name for name in ("supplier", "consumer", "extra", "workspace")
        )
        if scenario == "borrowed-member":
            consumer = workspace / consumer.name
        TestsFlextInfraBindingInstall._seed_candidate_projects(
            supplier,
            consumer,
            extra,
            workspace,
            scenario=scenario,
        )
        declaration = consumer / c.PYPROJECT_FILENAME
        original = TestsFlextInfraBindingInstall._declare_consumer_dependency(
            scenario,
            consumer,
        )
        environment = TestsFlextInfraBindingInstall._compose_consumer_environment(
            tmp_path,
            consumer,
            workspace,
            scenario=scenario,
        )
        python = (
            Path(
                sysconfig.get_path(
                    "scripts",
                    scheme="venv",
                    vars={"base": str(environment), "platbase": str(environment)},
                ),
            )
            / c.Infra.PromotedSelector.VENV_PYTHON
        )
        ci = config.Infra.codegen.make.ci
        outcome = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-m",
                    "flext_infra",
                    "workspace",
                    "flext-binding",
                    "--repository-root",
                    str(consumer),
                    "--flext-root",
                    str(supplier),
                    "--python",
                    str(python),
                ),
                options=m.Cli.ProcessOptions(env={ci.variable: ci.local_value}),
            ),
        )
        output = f"{outcome.stdout}{outcome.stderr}"
        tm.that(declaration.read_bytes(), eq=original)
        if scenario not in {"extras", "override", "transitive-source"}:
            tm.that(outcome.outcome.raw_return_code != 0, eq=True, msg=output)
            if scenario == "inactive":
                tm.that(output, has="no active declared dependency")
            elif scenario in {"borrowed", "borrowed-member"}:
                tm.that(output, has="physical consumer environment")
            else:
                tm.that(output, has="binding-candidate")
            return
        tm.that(u.Cli.process_succeeded(outcome.outcome), eq=True, msg=output)
        installed = tm.ok(
            u.Cli.run((
                str(python),
                "-c",
                (
                    "import binding_candidate, binding_extra; "
                    "print(binding_candidate.VALUE, binding_extra.VALUE)"
                ),
            )),
        )
        tm.that(installed.stdout.strip(), eq="installed installed")
        (supplier / "binding_candidate.py").write_text(
            'VALUE = "current-worktree"\n',
            encoding=c.DEFAULT_ENCODING,
        )
        rebound = tm.ok(
            u.Cli.run((
                str(python),
                "-c",
                "import binding_candidate; print(binding_candidate.VALUE)",
            )),
        )
        tm.that(rebound.stdout.strip(), eq="current-worktree")

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize("attached", [False, True])
    @pytest.mark.parametrize("origin_case", ["compiler", "nested", "valid"])
    def test_checkout_generator_consumes_the_provisioned_public_sdk(
        attached: bool,
        origin_case: str,
    ) -> None:
        """Exercise real YAML/TOML generation and authenticate loaded suppliers.

        Only the generator checkout is selected, as in the native Make owner.
        Its upstream SDK must come from the provisioned environment, not an
        additional source-path override that hides a mixed checkout/install.
        """
        checkout = Path(__file__).resolve().parents[3]
        root = u.Infra.runtime_environment_dir(checkout).parent
        context = checkout if attached else root
        status = tm.ok(u.Tests.run_isolated_make(["status"], cwd=root))
        consumer = dedent("""\
            import inspect
            import sys
            from dataclasses import dataclass
            from importlib.metadata import distribution
            from pathlib import Path
            from sys import argv

            from flext_cli import FlextCliConfig
            from flext_core import m as core_models
            from flext_infra import (
                FlextInfraWorkspaceDetector,
                FlextInfraWorkspaceEnvironmentProvenance,
                c, config, m, u,
            )

            cli_config = FlextCliConfig.fetch_global()
            cli_roundtrip = FlextCliConfig.model_validate(cli_config.model_dump())
            assert cli_roundtrip.Cli == cli_config.Cli
            root = Path(argv[1])
            workspace = FlextInfraWorkspaceDetector.load_workspace_spec(root).unwrap()
            declared_sources = {}
            for repository in (workspace.repository, *workspace.subprojects):
                if repository.package:
                    expected = (root / repository.path).resolve()
                    package = u.Infra.project_package_name(expected)
                    if repository.editable:
                        declared_sources[package] = expected
                    artifact = distribution(repository.distribution)
                    raw = artifact.read_text(c.Infra.DISTRIBUTION_DIRECT_URL_FILE)
                    receipt = (
                        m.Infra.DirectUrlReceipt.model_validate_json(raw)
                        if raw
                        else None
                    )
                    print(repository.distribution, artifact.version,
                          artifact.locate_file(""),
                          receipt.vcs_info if receipt else None,
                          receipt.dir_info if receipt else None,
                          flush=True)
            origins = []
            for supplier in u.Cli.__mro__:
                package = supplier.__module__.split(".")[0]
                if package in declared_sources:
                    module = sys.modules[supplier.__module__]
                    origin = Path(inspect.getfile(supplier)).resolve()
                    print("supplier", supplier, "module", module.__file__,
                          "definition", origin, "expected", declared_sources[package],
                          flush=True)
                    origins.append((origin, declared_sources[package]))
            documents = u.Cli.yaml_parse_documents(
                "first: value\\n---\\nsecond: value\\n"
            ).unwrap()
            assert tuple(documents) == ({"first": "value"}, {"second": "value"})
            yaml_origin = Path(
                inspect.getfile(inspect.unwrap(u.Cli.yaml_parse_documents))
            ).resolve()
            print("yaml definition", yaml_origin, flush=True)
            assert not declared_sources or origins
            assert all(origin.is_relative_to(expected) for origin, expected in origins)
            yaml_package = u.Cli.yaml_parse_documents.__module__.split(".")[0]
            if yaml_package in declared_sources:
                assert yaml_origin.is_relative_to(declared_sources[yaml_package])
            source = u.Cli.files_read_text(root / c.PYPROJECT_FILENAME).unwrap()
            document = u.Cli.toml_parse_text(source)
            assert document is not None
            groups = u.Cli.toml_table_child(document, c.Infra.DEPENDENCY_GROUPS)
            assert groups is not None
            comments = u.Cli.toml_array_item_comments(groups, str(c.Infra.DEV))
            values = u.Cli.toml_as_string_list(
                u.Cli.toml_value(groups, str(c.Infra.DEV))
            )
            assert len(comments) == len(values)
            toolchain = config.Infra.codegen.toolchain
            rendered = u.Infra.pyproject_conform(
                source,
                workspace=workspace,
                required_dev_dependencies=config.Infra.codegen.scaffold.project.dev,
                uv_resolution=m.Infra.UvResolutionSpec(
                    link_mode=toolchain.uv_link_mode,
                    constraint_dependencies=tuple(toolchain.uv_constraint_dependencies),
                    exclude_dependencies=tuple(config.Infra.codegen.uv_exclude_dependencies),
                    environments=tuple(toolchain.uv_environments),
                ),
                options=u.Infra.PyprojectConformOptions(
                    repository_root=root,
                    flext_line=u.Infra.flext_integration_line(
                        codegen=config.Infra.codegen, repository_root=root,
                    ).unwrap(),
                ),
            ).unwrap()
            assert u.Cli.toml_parse_text(rendered) is not None
            builder_type = dataclass(init=False, unsafe_hash=True)(core_models.Base)
            builder_type.Recursive = builder_type
            state = core_models.ContractModel.model_validate({})
            builder = core_models.Identity(state=state)
            assert builder.build() == state
            print("native generated", repr(builder), hash(builder), flush=True)
            origin_case = argv[2]
            if origin_case == "nested":
                function = inspect.unwrap(builder_type.build)
                unwrap_model = inspect.unwrap(FlextCliConfig.model_validate)
                external = inspect.getfile(unwrap_model)
                function.__code__ = function.__code__.replace(co_filename=external)
                print("external nested definition", function.__code__.co_filename,
                      flush=True)
            elif origin_case == "compiler":
                module = sys.modules[builder_type.__module__]
                recipient = vars(module)[builder_type.__qualname__.split(".")[0]]
                recipient.__hash__ = builder_type.__hash__
                print("transplanted compiler definition", recipient,
                      builder_type.__hash__.__qualname__, flush=True)
            provenance = FlextInfraWorkspaceEnvironmentProvenance.validate(root)
            if origin_case == "valid":
                provenance.unwrap()
            else:
                assert provenance.failure, "Wrong defining owner was authenticated"
                print("rejected", provenance.error, flush=True)
            """)
        outcome = tm.ok(
            u.Cli.run_raw(
                (sys.executable, "-c", consumer, str(root), origin_case),
                cwd=context,
                options=m.Cli.ProcessOptions(
                    env={"PYTHONPATH": str(checkout / c.Infra.DEFAULT_SRC_DIR)},
                    remove_env_keys=(
                        "MYPYPATH",
                        "VIRTUAL_ENV",
                        "UV_PROJECT",
                        "UV_PROJECT_ENVIRONMENT",
                    ),
                ),
            ),
        )
        u.Tests.record_dependency_command_output(outcome)
        tm.that(
            u.Cli.process_succeeded(outcome.outcome),
            eq=True,
            msg=outcome.stdout + outcome.stderr,
        )
        namespace = u.Infra.project_package_name(root)
        tm.that(
            u.Cli.process_succeeded(status.outcome),
            eq=True,
            msg=status.stdout + status.stderr,
        )
        tm.that(
            status.stdout,
            has=[
                f"runtime-import-module name={namespace!r} origin=",
                f"runtime-import-code module={namespace!r}",
                "co_filename=",
                "cached=",
                "path=",
            ],
        )
