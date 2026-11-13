"""A consumer repository owns configuration, documentation and tests only.

A ``consumer`` deployment or client repository pins the distribution it
consumes and owns no ``src`` package: generation reaches a fixed point, the
generated manifest is an unpackaged uv project, and the gate selection follows
the layout owner. Every scenario runs through real temporary repositories.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import shutil
from pathlib import Path

from flext_infra import config, infra
from flext_infra.check.gate_registry import FlextInfraGateRegistry
from flext_infra.codegen import (
    FlextInfraCodegenConform,
    FlextInfraCodegenMakeBootstrap,
    FlextInfraCodegenScaffolder,
)
from flext_infra.docs import FlextInfraDocGenerator
from tests import c, m, p, t, tm, u


class TestsFlextInfraCodegenConsumerProject:
    """The consumer kind generates a project without a package of its own."""

    CONSUMED = (
        "dc-recon @ git+ssh://git@github.com/datacosmos-br/cosmos-recon.git"
        "@a0032c04d32af7c189f1943c2897c075bc8f3ab1"
    )

    @staticmethod
    def _declare(root: Path, name: str, *, packaged: bool = False) -> Path:
        """Create one checkout: its declaration, docs and one test.

        Returns:
            The repository root, declared as a consumer unless ``packaged``.

        """
        root.mkdir(parents=True, exist_ok=True)
        repository = u.Tests.repository_ref(name, role=c.Infra.MakeProfile.STANDALONE)
        integration = u.Tests.integration()
        u.Tests.initialize_unborn_git_repo(
            root, origin_url=repository.url, branch=integration.branch
        )
        u.Tests.copy_tracked_mise_seeds(root)
        u.Tests.write_project_beads_config(root, name)
        return TestsFlextInfraCodegenConsumerProject._write_declaration(
            root, name, packaged=packaged
        )

    @staticmethod
    def _write_declaration(root: Path, name: str, *, packaged: bool) -> Path:
        """Write the declaration, docs and test of one checkout.

        Returns:
            The repository root.

        """
        integration = u.Tests.integration()
        project = u.Tests.project_spec(name)
        if not packaged:
            project = project.model_copy(
                update={
                    "package_name": None,
                    "upstream": "dc_recon",
                    "runtime_dependency_overlay": (
                        TestsFlextInfraCodegenConsumerProject.CONSUMED,
                    ),
                }
            )
        declaration = m.Infra.RepositoryDeltaSpec.model_validate({
            "project": project,
            "integration": integration,
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
                        },
                    },
                },
            )
        )
        (root / "docs").mkdir(exist_ok=True)
        (root / "docs" / "index.md").write_text("# Consumer\n", encoding="utf-8")
        (root / c.Infra.DIR_TESTS).mkdir(exist_ok=True)
        (root / c.Infra.DIR_TESTS / "test_consumed.py").write_text(
            '"""Consumer test."""\n', encoding="utf-8"
        )
        return root

    @u.Tests.fixture(scope="class")
    @staticmethod
    def generated(tmp_path_factory: t.Tests.TempPathFactory) -> Path:
        """Bootstrap one consumer repository through the public init owner.

        Returns:
            The repository root after its first generation.

        """
        root = TestsFlextInfraCodegenConsumerProject._declare(
            tmp_path_factory.mktemp("consumer"), "client-incident"
        )
        tm.ok(
            FlextInfraCodegenMakeBootstrap(
                repository_root=root, apply_changes=True
            ).execute(),
            eq=True,
        )
        return root

    @staticmethod
    def _declaration(
        project: p.Infra.ProjectSpec,
    ) -> p.Result[m.Infra.RepositoryDeltaSpec]:
        """Validate one repository declaration through its public model.

        Returns:
            The validated declaration or its validation failure.

        """
        payload: t.JsonDict = {"project": project.model_dump(mode="json")}
        return u.validate_value(m.Infra.RepositoryDeltaSpec, payload)

    @staticmethod
    def test_a_project_without_a_package_is_a_consumer() -> None:
        """The omitted package elects the consumer kind; shipped code is refused."""
        declare = TestsFlextInfraCodegenConsumerProject._declaration
        project = u.Tests.project_spec("client-incident")
        consumer = project.model_copy(update={"package_name": None})
        detected = c.Infra.ProjectKind.INTERNAL_FLEXT
        tm.that(
            tm.ok(declare(consumer)).governing_kind(detected),
            eq=c.Infra.ProjectKind.CONSUMER,
        )
        tm.that(tm.ok(declare(project)).governing_kind(detected), eq=detected)
        tm.fail(
            declare(consumer.model_copy(update={"root_modules": ("x",)})),
            has="ships no package",
        )

    @staticmethod
    @c.Tests.MARK.slow
    def test_generated_manifest_is_an_unpackaged_uv_project(generated: Path) -> None:
        """The manifest carries the pinned dependency and no build target."""
        document = tm.not_none(
            u.Cli.toml_parse_text(
                (generated / c.PYPROJECT_FILENAME).read_text(encoding="utf-8")
            )
        )
        tm.that(document.get("build-system"), none=True)
        project = u.Cli.toml_mapping_child(document, "project") or {}
        tm.that(
            project.get("dependencies"),
            eq=[TestsFlextInfraCodegenConsumerProject.CONSUMED],
        )
        tool = u.Cli.toml_mapping_child(document, c.Infra.TOOL) or {}
        tm.that((u.Cli.toml_mapping_child(tool, "uv") or {}).get("package"), eq=False)
        hatch = u.Cli.toml_mapping_child(tool, "hatch") or {}
        tm.that(hatch.get("build"), none=True)
        tm.that(
            (u.Cli.toml_mapping_child(tool, "flext") or {}).get("docs"),
            eq={},
        )
        tm.that((generated / c.Infra.DEFAULT_SRC_DIR).exists(), eq=False)
        tm.that(
            (generated / "README.md").read_text(encoding="utf-8"),
            lacks=":::",
        )

    @staticmethod
    @c.Tests.MARK.slow
    def test_generation_reaches_a_fixed_point(generated: Path) -> None:
        """The generation after the first publishes nothing."""
        again = tm.ok(
            FlextInfraCodegenConform.Generate.execute_request(
                u.Tests.conform_request(
                    generated,
                    what=c.Infra.CodegenConformSurface.ALL,
                    scope=c.Infra.CodegenConformScope.SELF,
                    mode=c.Infra.CodegenConformMode.APPLY,
                ),
                execution_context=infra,
            )
        )
        tm.that(again.written_files, eq=())

    @staticmethod
    @c.Tests.MARK.slow
    def test_only_the_package_gates_are_not_applicable(generated: Path) -> None:
        """The gates over a package's own source skip; every other gate runs."""
        u.Tests.commit_git_changes(generated, "generate the consumer project")
        registry = FlextInfraGateRegistry()
        selected = registry.applicable_gate_ids(
            registry.gate_ids,
            generated,
            m.Infra.GateContext(
                repository_root=generated,
                reports_dir=generated,
                scope_facts=u.Infra.ScopeFacts(),
            ),
        )
        tm.that(
            set(registry.gate_ids) - set(selected),
            eq={c.Infra.FRESH_IMPORT, c.Infra.DEPS},
        )

    @staticmethod
    def test_test_facades_compose_the_declared_upstream(tmp_path: Path) -> None:
        """Seeds name the upstream's facades and no package of the repository."""
        (tmp_path / c.Infra.DIR_TESTS).mkdir()
        project = u.Tests.project_spec("client-incident").model_copy(
            update={"package_name": None, "upstream": "dc_recon"}
        )
        seeds = FlextInfraCodegenScaffolder.plan_stems(
            tmp_path, project, config.Infra.codegen.scaffold, ()
        )
        planned = {seed.path.relative_to(tmp_path).as_posix() for seed in seeds}
        tm.that(planned, has="tests/constants.py")
        tm.that(planned, has="tests/_utilities/base.py")
        tm.that(planned, lacks="tests/base.py")
        tm.that(any(path.startswith("src/") for path in planned), eq=False)
        constants = next(
            seed for seed in seeds if seed.path.name == c.Infra.CONSTANTS_PY
        )
        tm.that(
            tm.not_none(constants.desired_content).decode("utf-8"),
            has="from dc_recon import c as source_c",
        )

    @staticmethod
    @c.Tests.MARK.slow
    def test_scaffold_reports_the_facades_of_a_consumer(generated: Path) -> None:
        """``codegen scaffold`` selects the consumer root and seeds its tests."""
        [result] = tm.ok(
            FlextInfraCodegenScaffolder(repository_root=generated).run(dry_run=True)
        )
        created = {Path(path).name for path in result.files_created}
        for name in ("constants.py", "models.py", "utilities.py"):
            tm.that(created, has=name)
        tm.that((generated / c.Infra.DIR_TESTS / "constants.py").exists(), eq=False)

    @staticmethod
    def test_a_source_package_contradicts_a_new_consumer(tmp_path: Path) -> None:
        """A consumer owns no ``src`` tree: authored sources there are refused."""
        root = TestsFlextInfraCodegenConsumerProject._declare(
            tmp_path / "client-incident", "client-incident"
        )
        package = root / c.Infra.DEFAULT_SRC_DIR / "client"
        package.mkdir(parents=True)
        (package / "__init__.py").write_text("", encoding="utf-8")
        tm.fail(
            FlextInfraCodegenMakeBootstrap(
                repository_root=root, apply_changes=True
            ).execute(),
            has="not a new scaffold",
        )

    @staticmethod
    def _generate(root: Path) -> tuple[Path, ...]:
        """Run the public generator over one checkout.

        Returns:
            The files the run wrote.

        """
        return tm.ok(
            FlextInfraCodegenConform.Generate.execute_request(
                u.Tests.conform_request(
                    root,
                    what=c.Infra.CodegenConformSurface.ALL,
                    scope=c.Infra.CodegenConformScope.SELF,
                    mode=c.Infra.CodegenConformMode.APPLY,
                ),
                execution_context=infra,
            )
        ).written_files

    # The conversion generates one project three times: its stages exceed the
    # slow budget, so its tests carry no slow marker and run unbudgeted.
    @u.Tests.fixture(scope="class")
    @staticmethod
    def packaged(tmp_path_factory: t.Tests.TempPathFactory) -> Path:
        """Bootstrap one packaged project, then commit it.

        Returns:
            The repository root holding the generated packaged project.

        """
        root = TestsFlextInfraCodegenConsumerProject._declare(
            tmp_path_factory.mktemp("conversion") / "client-incident",
            "client-incident",
            packaged=True,
        )
        (root / c.Infra.DIR_TESTS / "test_consumed.py").unlink()
        tm.ok(
            FlextInfraCodegenMakeBootstrap(
                repository_root=root, apply_changes=True
            ).execute(),
            eq=True,
        )
        u.Tests.commit_git_changes(root, "packaged project")
        return root

    @u.Tests.fixture(scope="class")
    @staticmethod
    def converted(packaged: Path) -> Path:
        """Drop the package and its declaration, then generate once.

        Returns:
            The repository root after the first generation as a consumer.

        """
        cls = TestsFlextInfraCodegenConsumerProject
        # The package and the test facades composing it leave together.
        shutil.rmtree(packaged / c.Infra.DEFAULT_SRC_DIR)
        shutil.rmtree(packaged / c.Infra.DIR_TESTS)
        (packaged / c.Infra.DIR_TESTS).mkdir()
        cls._write_declaration(packaged, "client-consumer", packaged=False)
        cls._generate(packaged)
        return packaged

    @staticmethod
    def test_a_packaged_project_owns_its_package_and_build_targets(
        packaged: Path,
    ) -> None:
        """The packaged baseline of the conversion has what a consumer drops."""
        text = (packaged / c.PYPROJECT_FILENAME).read_text(encoding="utf-8")
        tm.that(text, has="client_incident")
        tm.that(
            (packaged / c.Infra.DEFAULT_SRC_DIR / "client_incident").is_dir(), eq=True
        )

    @staticmethod
    def test_a_converted_project_generates_the_consumer_manifest(
        converted: Path,
    ) -> None:
        """Generation alone drops the package, its build targets and its self pin."""
        text = (converted / c.PYPROJECT_FILENAME).read_text(encoding="utf-8")
        document = tm.not_none(u.Cli.toml_parse_text(text))
        tm.that(document.get("build-system"), none=True)
        tool = u.Cli.toml_mapping_child(document, c.Infra.TOOL) or {}
        tm.that((u.Cli.toml_mapping_child(tool, "uv") or {}).get("package"), eq=False)
        tm.that((u.Cli.toml_mapping_child(tool, "hatch") or {}).get("build"), none=True)
        tm.that(text, lacks="client_incident")
        project = u.Cli.toml_mapping_child(document, "project") or {}
        tm.that(project.get("scripts"), none=True)
        tm.that(project.get("name"), eq="client-consumer")
        tm.that(
            project.get("dependencies"),
            has=TestsFlextInfraCodegenConsumerProject.CONSUMED,
        )

    @staticmethod
    def test_a_converted_project_reaches_a_fixed_point(converted: Path) -> None:
        """The generation after the conversion publishes nothing."""
        tm.that(TestsFlextInfraCodegenConsumerProject._generate(converted), eq=())

    @staticmethod
    @c.Tests.MARK.slow
    def test_docs_of_a_consumer_collect_no_package_api(generated: Path) -> None:
        """A consumer's API pages hold no empty directive and no stray whitespace."""
        tm.ok(
            FlextInfraDocGenerator(
                repository_root=generated, selected_projects=["."]
            ).generate(
                m.Infra.DocsGenerateRequest(repository_root=generated, projects=["."])
            )
        )
        api = generated / "docs" / "api-reference" / "generated"
        public = (api / "public-api.md").read_text(encoding="utf-8")
        tm.that(public, lacks=":::")
        tm.that(public, has="consumed distribution")
        for page in api.rglob("*.md"):
            text = page.read_text(encoding="utf-8")
            tm.that(text, lacks=":::")
            tm.that(
                [line for line in text.splitlines() if line != line.rstrip()],
                eq=[],
            )
        tm.that(
            (generated / "docs" / "api-reference" / "README.md").read_text(
                encoding="utf-8"
            ),
            lacks="src//",
        )
