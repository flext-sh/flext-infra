"""End-to-end tests for canonical lazy-init artifact processing."""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from tests.constants import c
from tests.utilities import u


# mro-i6nq.10: Tests exercise real apply/check behavior through the public service.
class TestsFlextInfraLazyInitProcessing:
    """Validate root manifests, thin roots, eager children, and idempotence."""

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
            contains=(
                "from flext_test_project.__unit__ import __all__ as __all__"
            ),
        )
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
        u.Tests.write_lazy_init_namespace_module(
            package_root / "models.py",
            class_name="FlextTestsModels",
            alias="m",
        )
        apply_service = u.Tests.create_lazy_init_service(workspace_root)
        check_service = u.Tests.create_lazy_init_service(workspace_root)

        apply_result = apply_service.generate_inits(check_only=False)
        check_result = check_service.generate_inits(check_only=True)

        tm.that(apply_result, eq=0)
        tm.that(check_result, eq=0)
        tm.that(check_service.modified_files, empty=True)

    def test_child_package_uses_eager_sibling_imports(self, tmp_path: Path) -> None:
        """Non-root packages contain only eager sibling imports and __all__."""
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
        tm.that(result, eq=0)
        tm.that(
            child_content,
            contains="from flext_test_project.services.demo import",
        )
        tm.that(child_content, contains="FlextTestsService")
        tm.that(child_content, contains="service")
        tm.that(child_content, lacks="flext_core.lazy")
        tm.that(child_content, lacks="TYPE_CHECKING")
        tm.that(child_content, lacks="__unit__")
        compile(child_content, "services/__init__.py", "exec")


__all__: list[str] = ["TestsFlextInfraLazyInitProcessing"]
