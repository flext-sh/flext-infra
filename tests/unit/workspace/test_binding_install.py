"""Real local installation preserves consumer resolution and isolation.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from collections.abc import (
    Iterable,
    Iterator,
    Mapping,
    MutableMapping,
    MutableSequence,
    Sequence,
)

import sys
from pathlib import Path
from textwrap import dedent

import pytest

from tests import c, m, tm, u


class TestsFlextInfraBindingInstall:
    """Exercise the generator checkout against the provisioned public SDK."""

    @staticmethod
    @pytest.mark.slow
    @pytest.mark.parametrize("attached", [False, True])
    @pytest.mark.parametrize("origin_case", ["compiler", "nested", "valid"])
    def test_checkout_generator_consumes_the_provisioned_public_sdk(
        *,
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
            from flext_infra import c, config, m, u, workspace

            cli_config = FlextCliConfig.fetch_global()
            cli_roundtrip = FlextCliConfig.model_validate(cli_config.model_dump())
            assert cli_roundtrip.Cli == cli_config.Cli
            root = Path(argv[1])
            workspace_spec = workspace.FlextInfraWorkspaceDetector.load_workspace_spec(
                root
            ).unwrap()
            declared_sources = {}
            for repository in (workspace_spec.repository, *workspace_spec.subprojects):
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
                workspace=workspace_spec,
                required_dev_dependencies=config.Infra.codegen.scaffold.project.dev,
                uv_resolution=m.Infra.UvResolutionSpec(
                    link_mode=toolchain.uv_link_mode,
                    constraint_dependencies=tuple(toolchain.uv_constraint_dependencies),
                    environments=tuple(toolchain.uv_environments),
                ),
                options=u.Infra.PyprojectConformOptions(
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
            provenance = workspace.FlextInfraWorkspaceEnvironmentProvenance.validate(
                root
            )
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
