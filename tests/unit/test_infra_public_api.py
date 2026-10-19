"""Public API contract tests for flext_infra facades.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path

import flext_infra
from flext_infra.codegen import FlextInfraCodegenConform
from tests import tm


class TestsFlextInfraPublicApi:
    """Exercise the root public package metadata against its pyproject."""

    @staticmethod
    def test_public_runtime_metadata_matches_public_constants() -> None:
        """Test public runtime metadata matches public constants."""
        metadata = tm.ok(
            flext_infra.u.Infra.read_project_metadata_result(
                Path(__file__).resolve().parents[2],
            ),
        )

        tm.that(flext_infra.__title__, eq=metadata.project.name)
        tm.that(flext_infra.__version__, eq=metadata.project.version)
        tm.that(flext_infra.__description__, eq=metadata.project.description)
        tm.that(flext_infra.__url__, eq=metadata.project.urls.homepage)
        tm.that(metadata.project.authors, empty=False)
        tm.that(flext_infra.__author__, eq=metadata.project.authors[0].name)

    @staticmethod
    def test_conform_invocations_keep_independent_mutable_state(tmp_path: Path) -> None:
        """Each public invocation owns its diagnostics without copying caller ports."""
        ports = flext_infra.infra.codegen_conform_collaborators()
        first = flext_infra.m.Infra.CodegenConformState(
            repository_root=tmp_path,
            ports=ports,
        )
        second = flext_infra.m.Infra.CodegenConformState(
            repository_root=tmp_path,
            ports=ports,
        )
        issue = flext_infra.m.Infra.Issue(
            file=str(tmp_path),
            line=0,
            column=0,
            code=flext_infra.c.Infra.ToolOutcome.ERROR.value,
            message="Invocation-local planning failure",
        )
        first.planning_issues.append(issue)
        first.planning_exception = ValueError(issue.message)
        first.scaffolded_repository = True

        assert first.ports is ports
        assert second.ports is ports
        tm.that(first.planning_issues, eq=[issue])
        tm.that(second.planning_issues, empty=True)
        assert second.planning_exception is None
        assert not second.scaffolded_repository

    @staticmethod
    def test_codegen_handlers_are_inherited_without_replacing_health(
        tmp_path: Path,
    ) -> None:
        """Public names stay API-bound while health remains a different operation."""
        api = flext_infra.FlextInfra(repository_root=tmp_path)
        assert "codegen_generate" not in flext_infra.FlextInfra.__dict__
        assert "codegen_conform" not in flext_infra.FlextInfra.__dict__
        assert "execute" in flext_infra.FlextInfra.__dict__
        assert api.codegen_generate.__self__ is api
        assert api.codegen_conform.__self__ is api
        before = tm.ok(api.execute())
        for root in (tmp_path / "first", tmp_path / "second"):
            generated = api.codegen_generate(
                flext_infra.m.Infra.CodegenGenerateRequest(
                    root=root,
                    what=flext_infra.c.Infra.CodegenConformSurface.DEPENDENCIES,
                ),
            )
            conformed = api.codegen_conform(
                flext_infra.m.Infra.CodegenConformRequest(
                    root=root,
                    what=flext_infra.c.Infra.CodegenConformSurface.DEPENDENCIES,
                    mode=flext_infra.c.Infra.CodegenConformMode.APPLY,
                ),
            )
            assert generated.failure
            assert conformed.failure
            assert not root.exists()
        tm.that(tm.ok(api.execute()), eq=before)
        assert not hasattr(api, "request")
        assert not hasattr(api, "planning_issues")

    @staticmethod
    def test_conform_engine_keeps_explicit_runtime_seeds_and_ports(
        tmp_path: Path,
    ) -> None:
        """Fresh public engines retain actual consumed capabilities by identity."""
        api = flext_infra.FlextInfra.with_settings(flext_infra.settings)
        ports = api.codegen_conform_collaborators()
        runtime_settings = api.settings
        initial_context = api.context
        engines = tuple(
            FlextInfraCodegenConform(
                repository_root=root,
                request=flext_infra.m.Infra.CodegenConformRequest(root=root),
                ports=ports,
                runtime_settings=runtime_settings,
                initial_context=initial_context,
            )
            for root in (tmp_path / "first", tmp_path / "second")
        )
        first, second = engines
        for engine in engines:
            assert engine.ports is ports
            assert engine.runtime_settings is runtime_settings
            assert engine.initial_context is initial_context
            assert engine.settings is runtime_settings
            assert engine.context is initial_context
            assert engine.request is not None
            tm.that(engine.repository_root, eq=engine.request.root)
        assert first is not second
        assert first.request is not second.request
        first.scaffolded_repository = True
        first.planning_exception = ValueError("First invocation failure")
        assert not second.scaffolded_repository
        assert second.planning_exception is None
        tm.that(second.planning_issues, empty=True)

    @staticmethod
    def test_codegen_routes_register_dto_classes_as_runtime_values() -> None:
        """Typed handlers still accept the native CLI's concrete schema values."""
        api = flext_infra.FlextInfra()
        generated = flext_infra.m.Cli.ResultCommandRoute(
            name="generate",
            help_text="Generate managed projections",
            model_cls=flext_infra.m.Infra.CodegenGenerateRequest,
            handler=api.codegen_generate,
        )
        conformed = flext_infra.m.Cli.ResultCommandRoute(
            name="conform",
            help_text="Conform managed projections",
            model_cls=flext_infra.m.Infra.CodegenConformRequest,
            handler=api.codegen_conform,
        )
        assert generated.model_cls is flext_infra.m.Infra.CodegenGenerateRequest
        assert conformed.model_cls is flext_infra.m.Infra.CodegenConformRequest
        assert generated.handler == api.codegen_generate
        assert conformed.handler == api.codegen_conform
