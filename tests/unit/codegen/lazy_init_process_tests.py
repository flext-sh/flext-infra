"""End-to-end tests for canonical lazy-init artifact processing."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from flext_tests import tm

from tests.constants import c
from tests.utilities import u

if TYPE_CHECKING:
    from _pytest.capture import CaptureFixture


# mro-i6nq.10: Tests exercise real apply/check behavior through the public service.
class TestsFlextInfraLazyInitProcessing:
    """Validate manifest-backed packages and generation idempotence."""

    def test_apply_generates_manifest_and_thin_root(self, tmp_path: Path) -> None:
        """Apply writes the root manifest before its thin consumer."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(tmp_path)
        u.Tests.write_lazy_init_namespace_module(
            package_root / "models.py",
            class_name="FlextTestsModels",
            alias="m",
            docstring="Models.",
        )

        result = u.Tests.run_lazy_init(workspace_root)

        init_content = (package_root / c.Infra.INIT_PY).read_text(
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        unit_content = (package_root / c.Infra.UNIT_PY).read_text(
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        tm.that(result, eq=0)
        tm.that(unit_content, contains='".models": (')
        tm.that(unit_content, contains='    "FlextTestsModels",')
        tm.that(unit_content, contains='    "m",')
        # mro-i6nq.10: Assert manifest ownership, independent of import formatting.
        tm.that(
            init_content,
            contains="from flext_test_project.__unit__ import (",
        )
        tm.that(init_content, contains="PUBLIC_EXPORTS as _PUBLIC_EXPORTS,")
        tm.that(
            init_content,
            contains="public_exports=_PUBLIC_EXPORTS",
        )
        tm.that(init_content, contains="__all__: tuple[str, ...]")
        tm.that(init_content, contains="install_lazy_exports(")
        tm.that(init_content, lacks="LAZY_MODULES: dict")
        compile(unit_content, "__unit__.py", "exec")
        compile(init_content, "__init__.py", "exec")

    def test_check_only_reports_both_root_artifacts_without_writing(
        self,
        tmp_path: Path,
    ) -> None:
        """Check-only reports expected drift and preserves every byte."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(tmp_path)
        u.Tests.write_lazy_init_namespace_module(
            package_root / "models.py",
            class_name="FlextTestsModels",
            alias="m",
        )
        init_path = package_root / c.Infra.INIT_PY
        unit_path = package_root / c.Infra.UNIT_PY
        original_init = init_path.read_bytes()
        service = u.Tests.create_lazy_init_service(workspace_root)

        result = service.generate_inits(check_only=True)

        tm.that(result, eq=0)
        tm.that(init_path.read_bytes(), eq=original_init)
        tm.that(unit_path.exists(), eq=False)
        tm.that(str(init_path) in service.modified_files, eq=True)
        tm.that(str(unit_path) in service.modified_files, eq=True)

    def test_apply_then_check_is_idempotent(self, tmp_path: Path) -> None:
        """A completed apply leaves no drift for the next check-only run."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(tmp_path)
        package_root.joinpath("service.py").write_text(
            "from __future__ import annotations\n\n"
            "class FlextTestsService:\n"
            "    pass\n\n"
            '__all__: list[str] = ["FlextTestsService"]\n',
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        apply_service = u.Tests.create_lazy_init_service(workspace_root)
        check_service = u.Tests.create_lazy_init_service(workspace_root)

        apply_result = apply_service.generate_inits(check_only=False)
        check_result = check_service.generate_inits(check_only=True)

        tm.that(apply_result, eq=0)
        tm.that(check_result, eq=0)
        tm.that(check_service.modified_files, empty=True)

    def test_generated_manifests_are_not_rediscovered_as_public_exports(
        self,
        tmp_path: Path,
        capsys: CaptureFixture[str],
    ) -> None:
        """A second generation pass ignores its own support modules."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(tmp_path)
        for child_name, class_name, alias in (
            ("_constants", "FlextTestsConstants", "c"),
            ("_models", "FlextTestsModels", "m"),
        ):
            child_root = package_root / child_name
            child_root.mkdir()
            child_root.joinpath(c.Infra.INIT_PY).write_text(
                "",
                encoding=c.Cli.ENCODING_DEFAULT,
            )
            u.Tests.write_lazy_init_namespace_module(
                child_root / "declarations.py",
                class_name=class_name,
                alias=alias,
            )

        tm.that(u.Tests.run_lazy_init(workspace_root), eq=0)
        _ = capsys.readouterr()
        tm.that(u.Tests.run_lazy_init(workspace_root, check_only=True), eq=0)
        captured = capsys.readouterr()
        output = f"{captured.out}\n{captured.err}"

        tm.that(output, contains="0 warnings")
        tm.that(output, lacks="export collision")

    def test_child_package_uses_manifest_and_thin_initializer(
        self,
        tmp_path: Path,
    ) -> None:
        """Non-root packages use the same cycle-safe generated artifacts."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(tmp_path)
        child_root = package_root / "services"
        child_root.mkdir()
        (child_root / c.Infra.INIT_PY).write_text(
            "",
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        u.Tests.write_lazy_init_namespace_module(
            child_root / "demo.py",
            class_name="FlextTestsService",
            alias="service",
        )

        result = u.Tests.run_lazy_init(workspace_root)

        child_content = (child_root / c.Infra.INIT_PY).read_text(
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        child_unit_content = (child_root / c.Infra.UNIT_PY).read_text(
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        tm.that(result, eq=0)
        tm.that(
            child_content,
            contains="from flext_test_project.services.__unit__ import (",
        )
        tm.that(child_content, contains="install_lazy_exports(")
        runtime_content = child_content.partition("if TYPE_CHECKING:")[0]
        tm.that(
            runtime_content,
            lacks="from flext_test_project.services.demo import",
        )
        tm.that(child_unit_content, contains='".demo": (')
        tm.that(child_unit_content, contains='    "FlextTestsService",')
        tm.that(child_unit_content, contains='    "service",')
        compile(child_unit_content, "services/__unit__.py", "exec")
        compile(child_content, "services/__init__.py", "exec")

    def test_private_foundation_package_uses_lazy_manifest(
        self,
        tmp_path: Path,
    ) -> None:
        """Private foundations keep cycle-safe manifests instead of eager imports."""
        workspace_root, package_root = u.Tests.create_lazy_init_workspace(tmp_path)
        private_root = package_root / "_models"
        private_root.mkdir()
        (private_root / c.Infra.INIT_PY).write_text(
            "",
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        u.Tests.write_lazy_init_namespace_module(
            private_root / "demo.py",
            class_name="FlextTestsPrivateModels",
            alias="m",
        )

        result = u.Tests.run_lazy_init(workspace_root)

        init_content = (private_root / c.Infra.INIT_PY).read_text(
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        unit_content = (private_root / c.Infra.UNIT_PY).read_text(
            encoding=c.Cli.ENCODING_DEFAULT,
        )
        tm.that(result, eq=0)
        # NOTE (multi-agent): mro-i6nq.10 proves the cycle-safe private route.
        tm.that(unit_content, contains='".demo": (')
        tm.that(init_content, contains="flext_test_project._models.__unit__")
        tm.that(init_content, contains="install_lazy_exports(")
        runtime_content = init_content.partition("if TYPE_CHECKING:")[0]
        tm.that(
            runtime_content,
            lacks="from flext_test_project._models.demo import",
        )
        compile(unit_content, "_models/__unit__.py", "exec")
        compile(init_content, "_models/__init__.py", "exec")


__all__: list[str] = ["TestsFlextInfraLazyInitProcessing"]
