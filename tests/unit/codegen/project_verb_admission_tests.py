"""A project admission override may name the project's own public verbs.

Every scenario writes a real ``config/codegen.yaml`` project layer, loads it
through the public codegen boundary and, when admitted, renders the generated
Makefile through the conform owner.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

from flext_infra import config
from tests import c, m, t, tm, u

pytestmark = c.Tests.MARK.slow


class TestsFlextInfraCodegenProjectVerbAdmission:
    """Admission overrides validate against canonical plus project verbs."""

    PROJECT = "fixture-project"

    @staticmethod
    def _declare(
        tmp_path: Path,
        extra_verbs: tuple[m.Infra.MakeVerbSpec, ...],
        overrides: t.JsonMapping,
    ) -> Path:
        """Write one project layer declaring verbs and admission overrides.

        Returns:
            The generated fixture repository root.

        """
        name = TestsFlextInfraCodegenProjectVerbAdmission.PROJECT
        root = tmp_path / name
        u.Tests.WorktreeFixture.write_python_project(root, name)
        u.Tests.initialize_git_repo(root, origin_url=u.Tests.repository_ref(name).url)
        declaration = m.Infra.RepositoryDeltaSpec.model_validate({
            "project": u.Tests.project_spec(name),
            "integration": u.Tests.integration(),
            "extra_verbs": extra_verbs,
        })
        tm.ok(
            u.Cli.yaml_dump(
                root / c.CONFIG_DIR_NAME / c.Infra.CODEGEN_CONFIG_FILENAME,
                {
                    "Infra": {
                        "codegen": {
                            "repository": declaration.model_dump(
                                mode="json", exclude_unset=True
                            ),
                            "make": {"admission": {"overrides": dict(overrides)}},
                        },
                    },
                },
            )
        )
        return root

    @staticmethod
    def test_canonical_verb_override_merges_over_library_overrides(
        tmp_path: Path,
    ) -> None:
        """A project override of a canonical verb keeps the library overrides."""
        root = TestsFlextInfraCodegenProjectVerbAdmission._declare(
            tmp_path, (), {c.Infra.VERB_CHECK: {"max_load5": 97}}
        )
        limits = tm.ok(u.Infra.load_codegen_inputs(root)).spec.make.admission
        tm.that(limits.verb_limits[c.Infra.VERB_CHECK].max_load5, eq=97)
        library = config.Infra.codegen.make.admission
        tm.that(set(library.overrides) <= set(limits.overrides), eq=True)
        tm.that(limits.max_load5, eq=library.max_load5)

    @staticmethod
    def test_project_verb_override_renders_its_admission_block(
        tmp_path: Path,
    ) -> None:
        """An override naming a project extra verb renders its admission limit."""
        root = TestsFlextInfraCodegenProjectVerbAdmission._declare(
            tmp_path,
            (m.Infra.MakeVerbSpec(name="deploy", description="Deploy the project."),),
            {"deploy": {"max_load5": 160}},
        )
        inputs = tm.ok(u.Infra.load_codegen_inputs(root))
        tm.that(inputs.spec.make.admission.verb_limits["deploy"].max_load5, eq=160)
        repository = u.Tests.repository_ref(
            TestsFlextInfraCodegenProjectVerbAdmission.PROJECT,
            role=c.Infra.MakeProfile.STANDALONE,
        ).model_copy(update={"extra_verbs": inputs.spec.repository.extra_verbs})
        rendered = u.Tests.conform_makefile_text(
            root, u.Tests.workspace_spec(repository)
        )
        tm.that(
            rendered,
            has=(
                "ifeq ($(ADMISSION_VERB),deploy)\n"
                "override ADMISSION_MAX_LOAD5 := 160.0\n"
            ),
        )

    @staticmethod
    def test_unknown_verb_override_fails_loud(tmp_path: Path) -> None:
        """An override naming no canonical or project verb is refused."""
        root = TestsFlextInfraCodegenProjectVerbAdmission._declare(
            tmp_path, (), {"undeclared-verb": {"max_load5": 160}}
        )
        tm.fail(
            u.Infra.load_codegen_inputs(root),
            has="make.admission names undeclared verbs: ['undeclared-verb']",
        )

    @staticmethod
    @c.Tests.MARK.parametrize(
        ("gate_key", "gate_value"),
        [("host_load_gate", False), ("gated_verbs", ["tests-full"])],
    )
    def test_tracked_project_layer_cannot_declare_the_load_gate(
        tmp_path: Path,
        gate_key: str,
        gate_value: t.JsonValue,
    ) -> None:
        """Only the packaged SSOT or the untracked local layer owns the gate."""
        root = TestsFlextInfraCodegenProjectVerbAdmission._declare(tmp_path, (), {})
        layer = root / c.CONFIG_DIR_NAME / c.Infra.CODEGEN_CONFIG_FILENAME
        declared = u.Cli.yaml_load_mapping(layer)
        tm.ok(
            u.Cli.yaml_dump(
                layer,
                u.config_merge(
                    declared,
                    {
                        "Infra": {
                            "codegen": {
                                "make": {"admission": {gate_key: gate_value}},
                            },
                        },
                    },
                ),
            )
        )
        tm.fail(
            u.Infra.load_codegen_inputs(root),
            has=f"make.admission.{gate_key} is declared only by",
        )

    @staticmethod
    @c.Tests.MARK.parametrize(
        ("gate", "gated", "refused"),
        [
            (True, ["help"], True),
            (False, ["help"], False),
            (True, [], False),
        ],
    )
    def test_local_layer_load_gate_decides_the_refusal(
        tmp_path: Path,
        *,
        gate: bool,
        gated: list[t.JsonValue],
        refused: bool,
    ) -> None:
        """A limit below any host load refuses only a gated verb with the gate on."""
        root, _ = u.Tests.render_make_environment(
            tmp_path,
            c.Infra.MakeProfile.STANDALONE,
            shape=u.Tests.MakeEnvironmentShape(
                local_admission={
                    "host_load_gate": gate,
                    "max_load5": 0.001,
                    "gated_verbs": gated,
                },
            ),
        )
        process = tm.ok(
            u.Tests.run_isolated_make(["--no-print-directory", "help"], cwd=root)
        )
        tm.that(u.Cli.process_succeeded(process.outcome), eq=not refused)
        if refused:
            tm.that(process.stderr, has="Refused: 5-minute load average")

    @staticmethod
    @c.Tests.MARK.parametrize(
        ("phase", "refused"),
        [
            (None, False),
            (c.Infra.CheckPhase.PRIMARY, False),
            (c.Infra.CheckPhase.COMPLETE, True),
        ],
    )
    def test_gated_check_full_refuses_only_the_complete_phase(
        tmp_path: Path,
        *,
        phase: c.Infra.CheckPhase | None,
        refused: bool,
    ) -> None:
        """A bare check is the primary form; only the complete phase is check-full."""
        root, _ = u.Tests.render_make_environment(
            tmp_path,
            c.Infra.MakeProfile.STANDALONE,
            shape=u.Tests.MakeEnvironmentShape(
                local_admission={
                    "host_load_gate": True,
                    "max_load5": 0.001,
                    "gated_verbs": ["check-full"],
                },
            ),
        )
        selector = [] if phase is None else [f"CHECK_PHASE={phase.value}"]
        process = tm.ok(
            u.Tests.run_isolated_make(
                ["--no-print-directory", c.Infra.VERB_CHECK, *selector], cwd=root
            )
        )
        tm.that("of 'check-full'" in process.stderr, eq=refused)
