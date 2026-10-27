"""Contract tests for the empty-render publication guard.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from flext_infra import FlextInfraConfig
from flext_infra.codegen import FlextInfraCodegenConform
from tests import c, m, p, tm, u


class TestsFlextInfraArtifactRenderEmptyGuard:
    """A managed render that produced no content must fail loud, never publish.

    A workflow fragment gated on an undeclared capability layer (the
    ``private_dependency_auth`` incident, bead cosmos-dxtk7) rendered 0 bytes
    and was emitted verbatim: consumers inspected the directory, saw the
    artifact present, and concluded the capability was delivered while every
    step it owns was silently absent. The render funnel owns the refusal:
    empty render in, typed planning issue out, naming the template, the
    destination, and the declaration cause.
    """

    @staticmethod
    def _plan_render(
        tmp_path: Path,
        content: str,
    ) -> tuple[p.Result[m.Infra.CodegenPlan], Path, Path]:
        """Plan a template declared through the target's repository-local config.

        Returns:
            The planning result, template source path, and destination path.

        """
        root = tmp_path / "project"
        root.mkdir()
        codegen = tm.ok(u.Infra.load_codegen_inputs(root)).spec
        entry = next(
            entry
            for entry in codegen.templates.entries
            if entry.destination == c.Infra.MAKEFILE_FILENAME
        )
        source = tm.not_none(entry.source)
        templates = tmp_path / "templates"
        shutil.copytree(u.Infra.codegen_templates_root(codegen), templates)
        # A nonempty conditional source renders exactly the supplied test content.
        (templates / source).write_text(
            "{% if false %}undeclared capability{% endif %}" + content,
            encoding="utf-8",
        )
        _, _, local_config = FlextInfraConfig.config_layer_paths_for_repository(
            root,
            filename=c.Infra.CODEGEN_CONFIG_FILENAME,
        )
        local_config.parent.mkdir()
        tm.ok(
            u.Cli.yaml_dump(
                local_config,
                {"Infra": {"codegen": {"templates": {"root": str(templates)}}}},
            ),
        )
        effective = tm.ok(u.Infra.load_codegen_inputs(root)).spec
        tm.that(u.Infra.codegen_templates_root(effective), eq=templates)
        u.Tests.copy_tracked_mise_seeds(root)
        u.Tests.initialize_git_repo(root)
        repository = u.Tests.repository_ref("fixture-project")
        workspace = u.Tests.workspace_spec(
            repository,
            project=u.Tests.project_spec(repository.name),
        )
        request = u.Tests.conform_request(
            root,
            what=c.Infra.CodegenConformSurface.MAKEFILE,
        )
        planned = FlextInfraCodegenConform.Generate(
            repository_root=root,
            state=m.Infra.CodegenConformState(
                repository_root=root,
                initial_workspace=workspace,
                request=request,
            ),
        ).plan(request)
        return planned, source, root / entry.destination

    @staticmethod
    def test_empty_render_fails_loud_naming_template_and_cause(
        tmp_path: Path,
    ) -> None:
        """A 0-byte render produces a planning issue naming template and cause."""
        refused, source, destination = (
            TestsFlextInfraArtifactRenderEmptyGuard._plan_render(
                tmp_path,
                "",
            )
        )
        plan = tm.ok(refused)
        tm.ok(bool(plan.issues))
        diagnostic = "\n".join(issue.message for issue in plan.issues)
        tm.that(
            diagnostic,
            has=str(source),
        )
        tm.that(
            diagnostic,
            has=destination.name,
        )
        tm.that(diagnostic, has="render produced no content")
        tm.that(diagnostic, has="consumer declaration error")
        tm.fail(any(file.path == destination for file in plan.files))
        tm.fail(destination.exists())

    @staticmethod
    def test_whitespace_render_fails_loud_with_template_stage_prefix(
        tmp_path: Path,
    ) -> None:
        """A whitespace-only render is refused and carries the planner banner."""
        refused, _, destination = TestsFlextInfraArtifactRenderEmptyGuard._plan_render(
            tmp_path,
            "  \n\t\n",
        )
        plan = tm.ok(refused)
        tm.ok(bool(plan.issues))
        diagnostic = "\n".join(issue.message for issue in plan.issues)
        tm.that(diagnostic, has="stage=templates ")
        tm.that(diagnostic, has="repository=")
        tm.that(diagnostic, has="publishing a 0-byte artifact is forbidden")
        tm.fail(any(file.path == destination for file in plan.files))
        tm.fail(destination.exists())

    @staticmethod
    def test_rendered_content_passes_through_verbatim(
        tmp_path: Path,
    ) -> None:
        """A render with real content passes through byte-exact."""
        content = "ready:\n\t@echo ready\n"
        kept, _, destination = TestsFlextInfraArtifactRenderEmptyGuard._plan_render(
            tmp_path,
            content,
        )
        tm.fail(kept.failure)
        plan = tm.ok(kept)
        tm.fail(bool(plan.issues))
        tm.that(u.Tests.planned_text(plan, destination.name), eq=content)
        tm.fail(destination.exists())

    @staticmethod
    @pytest.mark.parametrize("publishes_contract", [False, True])
    def test_source_plan_seals_installed_family_root_imports(
        tmp_path: Path,
        native_consumer: p.Tests.NativeConsumer,
        *,
        publishes_contract: bool,
    ) -> None:
        """The actual family census contributes native supplier bytes before effects."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        family_name = f"{c.NAMESPACE_FAMILY_PREFIX}family_contract"
        project_name = family_name.replace("_", "-")
        family_root, family = u.Tests.create_lazy_init_workspace(
            root,
            project_name=project_name,
            package_name=family_name,
        )
        (root / ".gitmodules").write_text(
            f'[submodule "{project_name}"]\n'
            f"    path = {project_name}\n"
            f"    url = https://example.invalid/{project_name}.git\n",
            encoding=c.DEFAULT_ENCODING,
        )
        (family / "__init__.py").write_text(
            "from typing import TYPE_CHECKING\n"
            "from .__version__ import __version__\n"
            "from .marker import c\n__all__ = ['c']\n"
            "if TYPE_CHECKING:\n    from .typing_only import OnlyForTyping\n"
            + (
                f"_LAZY_IMPORTS = {{'c': ('{family_name}.marker', 'Constants')}}\n"
                if publishes_contract
                else ""
            ),
            encoding=c.DEFAULT_ENCODING,
        )
        (family / "marker.py").write_text(
            "class Constants: pass\nc = Constants\n", encoding=c.DEFAULT_ENCODING
        )
        (family / "__version__.py").write_text(
            "__version__ = '1'\n", encoding=c.DEFAULT_ENCODING
        )
        (family / "typing_only.py").write_text(
            "class OnlyForTyping: pass\n", encoding=c.DEFAULT_ENCODING
        )
        metadata = family.parent / f"{family_name}-1.dist-info"
        metadata.mkdir()
        (metadata / "METADATA").write_text(
            f"Metadata-Version: 2.1\nName: {project_name}\nVersion: 1\n",
            encoding=c.DEFAULT_ENCODING,
        )
        (metadata / "top_level.txt").write_text(
            family.name + "\n", encoding=c.DEFAULT_ENCODING
        )
        native_consumer(
            "from flext_core import u\n"
            "from flext_infra.codegen import FlextInfraStagedPackage as staging\n"
            "root, family_root, package, family = map(Path, sys.argv[1:])\n"
            "candidates = u.family_discovery_candidates()\n"
            "assert family.name in {name for _, name in candidates}\n"
            "published = family.name in u.project_alias_owners()\n"
            f"assert published is {publishes_contract!r}\n"
            "target = package / 'chosen.py'\n"
            "plan = staging.plan_sources(root, {target: 'value = 1\\n'}).unwrap()\n"
            "assert family.name in {layout.package_name for layout in plan.layouts}\n"
            "sealed = {state.path: state for state in plan.inputs}\n"
            "for name in ('__init__.py', '__version__.py', 'marker.py'):\n"
            "    path = family / name\n"
            "    assert sealed[path].content == path.read_bytes()\n"
            "assert family / 'typing_only.py' not in sealed\n"
            "assert family_root / 'pyproject.toml' not in sealed\n"
            "assert not target.exists()\n",
            str(root),
            str(family_root),
            str(package),
            str(family),
            cwd=family.parent,
        )

    @staticmethod
    def test_normalized_python_output_is_repaired_and_idempotent(
        tmp_path: Path,
    ) -> None:
        """Generated Python passes the destination's lint and format repair once."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        destination = package / "prepared.py"
        plan = m.Infra.CodegenFilePlan(
            project=root,
            path=destination,
            before=tm.ok(u.Cli.atomic_read_binary_file_state(destination)),
            desired_content=b"values=dict(answer=42)\n",
            desired_mode=c.Infra.CONFIG_SPEC[1],
        )
        normalized = tm.ok(u.Infra.normalized_codegen_changes((plan,)))
        emitted = tm.not_none(normalized[0].desired_content)
        tm.that(emitted.decode(c.DEFAULT_ENCODING), eq="values = dict(answer=42)\n")
        repeated = tm.ok(
            u.Infra.normalized_codegen_changes((
                m.Infra.CodegenFilePlan(
                    project=root,
                    path=destination,
                    before=plan.before,
                    desired_content=emitted,
                    desired_mode=c.Infra.CONFIG_SPEC[1],
                ),
            ))
        )
        tm.that(repeated[0].desired_content, eq=emitted)
        tm.fail(destination.exists())

    @staticmethod
    def test_public_check_schema_cannot_redirect_candidate_runtime() -> None:
        """The public CLI payload never exposes a physical runtime override."""
        schema = m.Infra.RunCommand.model_json_schema(by_alias=True)
        properties = schema["properties"]
        tm.fail("runtime_root" in properties)
        tm.fail("runtime-root" in properties)

    @staticmethod
    def test_project_normalization_uses_each_destination_policy(
        tmp_path: Path,
    ) -> None:
        """Each owning project normalizes under only its own lint policy."""
        workspace = u.Tests.create_lazy_init_workspace(tmp_path)[0]
        plans: list[m.Infra.CodegenFilePlan] = []
        for name, selected in (("first", "F"), ("second", "UP")):
            root, package = u.Tests.create_lazy_init_workspace(
                workspace,
                project_name=f"prepared-{name}",
                package_name=f"prepared_{name}",
            )
            metadata = root / c.PYPROJECT_FILENAME
            document = tm.not_none(
                u.Cli.toml_parse_text(metadata.read_text(encoding=c.DEFAULT_ENCODING))
            )
            document["tool"] = {"ruff": {"lint": {"select": [selected]}}}
            metadata.write_text(u.Cli.toml_dumps(document), encoding=c.DEFAULT_ENCODING)
            destination = package / "prepared.py"
            plans.append(
                m.Infra.CodegenFilePlan(
                    project=root,
                    path=destination,
                    before=tm.ok(u.Cli.atomic_read_binary_file_state(destination)),
                    desired_content=b"import os\n\nvalue = 1\n",
                    desired_mode=c.Infra.CONFIG_SPEC[1],
                )
            )
        first, second = tm.ok(u.Infra.normalized_codegen_changes(tuple(plans)))
        tm.fail(b"import os" in tm.not_none(first.desired_content))
        tm.ok(b"import os" in tm.not_none(second.desired_content))
        tm.fail(any(plan.path.exists() for plan in plans))

    @staticmethod
    def test_normalization_reads_the_pyproject_staged_in_the_same_plan_set(
        tmp_path: Path,
    ) -> None:
        """A tooling change staged with a candidate governs that candidate's repair."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        metadata = root / c.PYPROJECT_FILENAME
        document = tm.not_none(
            u.Cli.toml_parse_text(metadata.read_text(encoding=c.DEFAULT_ENCODING))
        )
        document["tool"] = {"ruff": {"lint": {"select": ["UP040"]}}}
        metadata.write_text(u.Cli.toml_dumps(document), encoding=c.DEFAULT_ENCODING)
        staged = tm.not_none(
            u.Cli.toml_parse_text(metadata.read_text(encoding=c.DEFAULT_ENCODING))
        )
        staged["tool"] = {
            "ruff": {"lint": {"select": ["UP040"], "unfixable": ["UP040"]}}
        }
        destination = package / "facade.py"
        candidate = (
            b"from typing import TypeAlias\n\n\n"
            b"class Facade:\n    Owner: TypeAlias = int\n"
        )

        def plan(content: bytes, path: Path) -> m.Infra.CodegenFilePlan:
            return m.Infra.CodegenFilePlan(
                project=root,
                path=path,
                before=tm.ok(u.Cli.atomic_read_binary_file_state(path)),
                desired_content=content,
                desired_mode=c.Infra.CONFIG_SPEC[1],
            )

        stale = tm.ok(
            u.Infra.normalized_codegen_changes((plan(candidate, destination),))
        )
        tm.that(tm.not_none(stale[0].desired_content), has=b"type Owner = int")
        current = tm.ok(
            u.Infra.normalized_codegen_changes((
                plan(u.Cli.toml_dumps(staged).encode(c.DEFAULT_ENCODING), metadata),
                plan(candidate, destination),
            ))
        )
        emitted = tm.not_none(current[1].desired_content)
        tm.that(emitted, has=b"Owner: TypeAlias = int")
        tm.that(emitted, lacks=b"type Owner")
