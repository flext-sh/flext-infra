"""Execute migrated dynamic environment boundaries with real typed policy.

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

import inspect
import sys
from os.path import commonpath
from pathlib import Path

import pytest

from flext_infra import FlextInfraConfig, config, infra, settings
from flext_infra.workspace import FlextInfraRopeWorkspace
from tests import c, m, tm, u


class TestsFlextInfraDynamicEnvironmentCutover:
    """Preserve unset, empty, and populated values without default normalization."""

    @pytest.mark.parametrize("declared_owner_present", [False, True])
    def test_declared_settings_owner_is_required_without_legacy_fallback(
        self, tmp_path: Path, *, declared_owner_present: bool
    ) -> None:
        """The public planner requires the declared owner, not an old filename."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = package / "consumer.py"
        access = (
            "os.environ.get(str(config.Infra.codegen.make.mypy_cache."
            "data_home_environment_variable))"
        )
        current_owner = Path(inspect.getfile(type(settings)))
        original = tm.ok(
            u.Cli.atomic_read_binary_file_state(current_owner, required=True)
        )
        supplier = tm.not_none(u.Infra.project_root(current_owner))
        supplier_name = u.Infra.project_name_from_payload(
            supplier, u.Infra.pyproject_payload(supplier / c.PYPROJECT_FILENAME)
        )
        declared = tm.ok(
            u.Infra.project_codegen_inputs(
                supplier,
                tm.ok(u.Infra.load_codegen_inputs(supplier)),
                projections=(
                    m.Infra.CodegenLayerProjection(
                        path=FlextInfraConfig.config_layer_paths_for_repository(
                            supplier, filename=c.Infra.CODEGEN_CONFIG_FILENAME
                        )[1],
                        values={
                            "Infra": {
                                "codegen": {
                                    "runtime_module_overrides": {
                                        supplier_name: {"settings": "runtime_settings"},
                                    }
                                }
                            }
                        },
                    ),
                ),
            )
        )
        names = u.Infra.runtime_module_names(
            project_name=supplier_name, codegen=declared.spec
        )
        owner = (
            current_owner.with_name(f"{names['settings']}.py")
            if declared_owner_present
            else current_owner
        )
        sources = {
            path: (
                "import os\nfrom flext_infra import config\n"
                "def read_value():\n"
                f"    return {access}\n"
            ),
            owner: tm.not_none(original.content).decode(c.DEFAULT_ENCODING),
        }
        before = tm.ok(u.Cli.atomic_read_binary_file_state(owner, required=False))
        if declared_owner_present:
            tm.that(before.content, eq=None)
        with infra.rope_workspace(root) as rope:
            if not declared_owner_present:
                with pytest.raises(ValueError, match="declared settings owner"):
                    u.Infra.plan_dynamic_environment_cutover(
                        rope_workspace=rope,
                        sources=sources,
                        findings=(self._finding(path.relative_to(root), access),),
                        dependency_codegen={supplier: declared},
                    )
                tm.ok(u.Cli.atomic_verify_binary_file_states((before,)))
                return
            with pytest.raises(ValueError, match="policy belongs to another root"):
                u.Infra.plan_dynamic_environment_cutover(
                    rope_workspace=rope,
                    sources=sources,
                    findings=(self._finding(path.relative_to(root), access),),
                    dependency_codegen={
                        supplier: tm.ok(u.Infra.load_codegen_inputs(root))
                    },
                )
            with (
                u.Infra.facade_source_project(
                    Path(commonpath((root, supplier))),
                    planned_sources=sources,
                    project_roots=(root, supplier),
                ) as (project, _),
                FlextInfraRopeWorkspace.open_workspace(
                    root,
                    rope_repository_root=Path(project.root.real_path),
                    source_project=project,
                ) as captured,
            ):
                tm.that(captured.rope_project.source_text(owner), eq=sources[owner])
                tm.that(captured.rope_project.source_query(owner, "isfile"))
                edits = tm.ok(
                    u.Infra.plan_dynamic_environment_cutover(
                        rope_workspace=captured,
                        sources=sources,
                        findings=(self._finding(path.relative_to(root), access),),
                        dependency_codegen={supplier: declared},
                    )
                )
                tm.that(len(edits), eq=1)
                sources[path] = edits[0].updated_source
                tm.that(
                    tm.ok(
                        u.Infra.plan_dynamic_environment_cutover(
                            rope_workspace=captured,
                            sources=sources,
                            findings=(self._finding(path.relative_to(root), access),),
                            dependency_codegen={supplier: declared},
                        )
                    ),
                    eq=(),
                )
        tm.ok(u.Cli.atomic_verify_binary_file_states((original, before)))

    @pytest.mark.parametrize("value", [None, "", "literal value"])
    @pytest.mark.parametrize("required", [False, True])
    def test_real_settings_consumer_preserves_lookup_contract(
        self,
        tmp_path: Path,
        value: str | None,
        *,
        required: bool,
    ) -> None:
        """Test real settings consumer preserves lookup contract."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = package / "consumer.py"
        access = (
            "os.environ[str(policy.data_home_environment_variable)]"
            if required
            else "os.environ.get(str(policy.data_home_environment_variable))"
        )
        source = (
            "import os\nimport sys\nfrom flext_infra import config\n"
            "from flext_tests import tm\n"
            "def read_value():\n"
            "    policy = config.Infra.codegen.make.mypy_cache\n"
            f"    return {access}\n"
            "if sys.argv[1] == 'missing-required':\n"
            "    try:\n"
            "        read_value()\n"
            "    except KeyError as error:\n"
            "        assert error.args == (str(config.Infra.codegen.make.mypy_cache"
            ".data_home_environment_variable),)\n"
            "    else:\n"
            "        tm.reject('required key was defaulted')\n"
            "else:\n"
            "    print(repr(read_value()))\n"
        )
        settings_path = Path(inspect.getfile(type(settings)))
        sources = {
            path: source,
            settings_path: settings_path.read_text(encoding="utf-8"),
        }
        finding = self._finding(path.relative_to(root), access)
        with infra.rope_workspace(root) as rope:
            edits = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.DYNAMIC_ENVIRONMENT,
                    rope_workspace=rope,
                    sources=sources,
                    findings=(finding,),
                ),
            )
            tm.that(len(edits), eq=1)
            sources[path] = edits[0].updated_source
            remaining = tm.ok(
                u.Infra.plan_semantic_cutover(
                    c.Infra.SemanticCutoverPhase.DYNAMIC_ENVIRONMENT,
                    rope_workspace=rope,
                    sources=sources,
                    findings=(finding,),
                ),
            )
        tm.that(remaining, empty=True)
        path.write_text(sources[path], encoding="utf-8")
        key = str(config.Infra.codegen.make.mypy_cache.data_home_environment_variable)
        environment: dict[str, str] = {} if value is None else {key: value}
        mode = "missing-required" if required and value is None else "value"
        output = tm.ok(
            u.Cli.run_raw(
                (sys.executable, "-I", str(path), mode),
                options=m.Cli.ProcessOptions(
                    env=environment,
                    remove_env_keys=(key,) if value is None else (),
                ),
            ),
        )
        tm.that(u.Cli.process_succeeded(output.outcome), eq=True, msg=output.stderr)
        tm.that(output.stdout, eq="" if mode == "missing-required" else f"{value!r}\n")

    @pytest.mark.parametrize(
        "access",
        ["os.environ.get('STATIC_KEY')", "os.environ.get(unknown_key)"],
    )
    def test_unproven_environment_key_stays_red(
        self,
        tmp_path: Path,
        access: str,
    ) -> None:
        """Test unproven environment key stays red."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        path = package / "consumer.py"
        source = f"import os\ndef value(unknown_key: str):\n    return {access}\n"
        with (
            infra.rope_workspace(root) as rope,
            pytest.raises(ValueError, match=r"typed-config provenance"),
        ):
            u.Infra.plan_semantic_cutover(
                c.Infra.SemanticCutoverPhase.DYNAMIC_ENVIRONMENT,
                rope_workspace=rope,
                sources={path: source},
                findings=(self._finding(path.relative_to(root), access),),
            )

    @staticmethod
    def _finding(path: Path, access: str) -> m.Infra.ModOccurrence:
        (rule,) = c.Infra.SEMANTIC_CUTOVER_RULE_IDS[
            c.Infra.SemanticCutoverPhase.DYNAMIC_ENVIRONMENT
        ]
        return m.Infra.ModOccurrence(
            rule_file=f"{rule}.yml",
            rule_id=rule,
            repository="fixture",
            file=path,
            range={},
            text=access,
            actionable=False,
            classification=c.Infra.ModScanFindingClass.DETECTION_ONLY,
        )
