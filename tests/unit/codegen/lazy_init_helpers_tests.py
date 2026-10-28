"""Behavior tests for public lazy-init generation.

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

import pytest

import flext_infra
from tests import c, tm, u


class TestsFlextInfraLazyInitHelpers:
    """Validate lazy-init through the public service surface only."""

    @staticmethod
    @pytest.mark.parametrize(
        ("relative", "expected"),
        [
            ("src/test_pkg/__init__.py", "test_pkg"),
            ("tests/unit/__init__.py", "tests.unit"),
            ("examples/tests/__init__.py", "examples.tests"),
            ("infra/pulumi/lib/__init__.py", "infra.pulumi.lib"),
        ],
    )
    def test_discover_package_from_detected_namespaces(
        tmp_path: Path, relative: str, expected: str
    ) -> None:
        """Every root folder of a declared project is a namespace; src is stripped."""
        tmp_path.joinpath(c.PYPROJECT_FILENAME).write_text(
            "[project]\nname = 'demo'\nversion = '0.1.0'\n",
            encoding=c.DEFAULT_ENCODING,
        )
        initializer = tmp_path / relative
        initializer.parent.mkdir(parents=True)
        initializer.write_text("", encoding=c.DEFAULT_ENCODING)
        tm.that(u.Infra.package_name(initializer), eq=expected)

    @staticmethod
    def test_root_generation_uses_real_classes_and_aliases(
        tmp_path: Path,
    ) -> None:
        """Publish real root declarations through the inline lazy contract."""
        repository_root, package_root = u.Tests.demo_lazy_init_workspace(tmp_path)
        u.Tests.write_lazy_init_namespace_module(
            package_root / "models.py",
            class_name="FlextModelsDemo",
            alias="m",
            docstring="Models.",
        )

        tm.that(u.Tests.run_lazy_init(repository_root), eq=0)
        init_content = u.Tests.generated_init(package_root)
        exports_content = u.Tests.generated_init(package_root)

        tm.that(init_content, has="import install_lazy_exports")
        tm.that(init_content, has='"m": ".models"')
        tm.that(exports_content, has='"FlextModelsDemo"')
        tm.that(exports_content, has='"m"')

    @staticmethod
    @pytest.mark.parametrize("generated_init", [False, True])
    def test_non_flext_root_respects_initializer_ownership(
        tmp_path: Path,
        *,
        generated_init: bool,
    ) -> None:
        """Apply content ownership equally to every governed source package."""
        # External consumers such as ai_hub are
        # first-class FLEXT packages; prefix-specific planning created dual truth.
        repository_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="ai-hub",
            package_name="ai_hub",
        )
        original = (
            f"{c.Infra.AUTOGEN_HEADER}\n" if generated_init else ""
        ) + '"""Existing initializer."""\n'
        package_root.joinpath(c.Infra.INIT_PY).write_text(
            original,
            encoding=c.DEFAULT_ENCODING,
        )
        u.Tests.write_lazy_init_namespace_module(
            package_root / "models.py",
            class_name="AiHubModels",
            alias="m",
            docstring="AI Hub models.",
        )

        tm.that(u.Tests.run_lazy_init(repository_root), eq=0)
        generated = u.Tests.generated_init(package_root)

        if not generated_init:
            tm.that(generated, eq=original)
            return
        tm.that(generated, has="AUTO-GENERATED FILE")
        tm.that(generated, has='"AiHubModels"')
        tm.that(generated, has='"m"')
        tm.that(generated, lacks="Existing initializer")

    @staticmethod
    def test_private_modules_do_not_export_from_root(tmp_path: Path) -> None:
        """Keep private sibling modules outside the public package contract."""
        repository_root, package_root = u.Tests.demo_lazy_init_workspace(tmp_path)
        (package_root / "_internal.py").write_text(
            "from __future__ import annotations\n\n"
            "class FlextDemoInternal:\n    pass\n",
            encoding=c.DEFAULT_ENCODING,
        )

        tm.that(u.Tests.run_lazy_init(repository_root), eq=0)
        tm.that(u.Tests.generated_init(package_root), lacks="FlextDemoInternal")

    @staticmethod
    def test_root_regeneration_preserves_declared_abi_only(
        tmp_path: Path,
    ) -> None:
        """Keep module-local public helpers outside the package-root ABI."""
        repository_root, package_root = u.Tests.demo_lazy_init_workspace(tmp_path)
        package_root.joinpath(c.Infra.INIT_PY).write_text(
            '__all__: tuple[str, ...] = ("FlextDemoConstants", "FlextDemoLazy", "c")\n',
            encoding=c.DEFAULT_ENCODING,
        )
        package_root.joinpath(c.Infra.CONSTANTS_PY).write_text(
            "class FlextDemoConstants:\n"
            '    """Canonical constants facade."""\n\n'
            "class FlextDemoConstantsEnforcement:\n"
            '    """Module-local composition class."""\n\n'
            "c = FlextDemoConstants\n\n"
            '__all__ = ("FlextDemoConstants", '
            '"FlextDemoConstantsEnforcement", "c")\n',
            encoding=c.DEFAULT_ENCODING,
        )
        package_root.joinpath("lazy.py").write_text(
            "class FlextDemoLazy:\n"
            '    """Canonical lazy facade."""\n\n'
            "class FlextDemoLazyAttribute:\n"
            '    """Module-local implementation type."""\n\n'
            "def lazy_attribute() -> None:\n"
            '    """Module-local helper."""\n\n'
            '__all__ = ("FlextDemoLazy", "FlextDemoLazyAttribute", '
            '"lazy_attribute")\n',
            encoding=c.DEFAULT_ENCODING,
        )

        tm.that(u.Tests.run_lazy_init(repository_root), eq=0)
        generated = u.Tests.generated_init(package_root)
        has_all, exports = u.Tests.extract_lazy_init_exports(generated)

        tm.ok(has_all)
        tm.that(exports, eq=("FlextDemoConstants", "FlextDemoLazy", "c"))
        tm.that(generated, lacks="FlextDemoConstantsEnforcement")
        tm.that(generated, lacks="FlextDemoLazyAttribute")
        tm.that(generated, lacks="lazy_attribute")

    @staticmethod
    def test_root_regeneration_prunes_contract_name_without_owner(
        tmp_path: Path,
    ) -> None:
        """Remove stale projected names that have no current source owner."""
        repository_root, package_root = u.Tests.demo_lazy_init_workspace(tmp_path)
        declared_contract = (
            f"{c.Infra.AUTOGEN_HEADER}\n"
            '__all__: tuple[str, ...] = ("FlextModelsDemo", "FlextDemoMissing", "m")\n'
        )
        package_root.joinpath(c.Infra.INIT_PY).write_text(
            declared_contract,
            encoding=c.DEFAULT_ENCODING,
        )
        u.Tests.write_lazy_init_namespace_module(
            package_root / "models.py",
            class_name="FlextModelsDemo",
            alias="m",
        )

        tm.that(u.Tests.run_lazy_init(repository_root), eq=0)
        generated = u.Tests.generated_init(package_root)

        # The prior projection is never an ABI
        # owner; regeneration converges it to declarations that still exist.
        tm.that(generated, has='"FlextModelsDemo"')
        tm.that(generated, has='"m"')
        tm.that(generated, lacks="FlextDemoMissing")
        tm.that(generated, ne=declared_contract)

    @staticmethod
    def test_private_child_packages_do_not_widen_root_api(tmp_path: Path) -> None:
        """Keep private child declarations outside the public root contract."""
        repository_root, package_root = u.Tests.demo_lazy_init_workspace(tmp_path)
        child_dir = package_root / "_enforcement"
        child_dir.mkdir()
        (child_dir / c.Infra.INIT_PY).write_text("", encoding=c.DEFAULT_ENCODING)
        (child_dir / "engine.py").write_text(
            "class FlextDemoEnforcementEngine:\n"
            '    """Internal engine."""\n\n'
            '__all__ = ["FlextDemoEnforcementEngine"]\n',
            encoding=c.DEFAULT_ENCODING,
        )

        tm.that(u.Tests.run_lazy_init(repository_root), eq=0)
        exports_content = u.Tests.generated_init(package_root)
        public_exports = exports_content.split(
            "__all__: tuple[str, ...] =",
            maxsplit=1,
        )[1]

        # Private child classes never become root ABI.
        tm.that(exports_content, lacks="FlextDemoEnforcementEngine")
        tm.that(public_exports, lacks="FlextDemoEnforcementEngine")
        tm.that(public_exports, lacks='"_enforcement"')
        tm.that(u.Tests.run_lazy_init(repository_root, check_only=True), eq=0)

    @staticmethod
    def test_regeneration_prunes_stale_private_direct_imports(
        tmp_path: Path,
    ) -> None:
        """Derive root attributes from public facades, never a stale init literal."""
        repository_root, package_root = u.Tests.demo_lazy_init_workspace(tmp_path)
        u.Tests.write_lazy_init_namespace_module(
            package_root / "models.py",
            class_name="FlextModelsDemo",
            alias="m",
        )
        utilities_dir = package_root / "_utilities"
        utilities_dir.mkdir()
        utilities_dir.joinpath(c.Infra.INIT_PY).write_text(
            "",
            encoding=c.DEFAULT_ENCODING,
        )
        conversion_path = utilities_dir / "conversion.py"
        conversion_path.write_text(
            "class FlextDemoConversion:\n"
            '    """Supported direct root import."""\n\n'
            '__all__ = ["FlextDemoConversion"]\n',
            encoding=c.DEFAULT_ENCODING,
        )

        tm.that(u.Tests.run_lazy_init(repository_root), eq=0)
        generated = u.Tests.generated_init(package_root)
        tm.that(generated, lacks="_DIRECT_IMPORTS")
        tm.that(generated, lacks="FlextDemoConversion")

        extra_path = utilities_dir / "extra.py"
        extra_path.write_text(
            "class FlextDemoExtra:\n"
            '    """New internal name outside the frozen contract."""\n\n'
            '__all__ = ["FlextDemoExtra"]\n',
            encoding=c.DEFAULT_ENCODING,
        )
        tm.that(u.Tests.run_lazy_init(repository_root), eq=0)
        tm.that(u.Tests.generated_init(package_root), lacks="FlextDemoExtra")

        conversion_path.unlink()
        check_service = u.Tests.create_lazy_init_service(repository_root)
        tm.ok(check_service.plan_files().success)
        tm.that(u.Tests.generated_init(package_root), eq=generated)

    @staticmethod
    def test_private_subpackage_facade_never_becomes_root_public(
        tmp_path: Path,
    ) -> None:
        """Keep even a final implementation facade private below the root."""
        repository_root, package_root = u.Tests.demo_lazy_init_workspace(tmp_path)
        models_dir = package_root / "_models"
        parts_dir = models_dir / "_base"
        parts_dir.mkdir(parents=True)
        for package_dir in (models_dir, parts_dir):
            package_dir.joinpath(c.Infra.INIT_PY).write_text(
                "",
                encoding=c.DEFAULT_ENCODING,
            )
        parts_dir.joinpath("Flextmodelsdemobase_part_01.py").write_text(
            "class FlextModelsDemoBase:\n"
            '    """Private implementation part."""\n\n'
            '__all__ = ["FlextModelsDemoBase"]\n',
            encoding=c.DEFAULT_ENCODING,
        )
        models_dir.joinpath("base.py").write_text(
            "from ._base.Flextmodelsdemobase_part_01 import "
            "FlextModelsDemoBase as FlextModelsDemoBasePart01\n\n"
            "class FlextModelsDemoBase(FlextModelsDemoBasePart01):\n"
            '    """Public facade."""\n\n'
            '__all__ = ["FlextModelsDemoBase"]\n',
            encoding=c.DEFAULT_ENCODING,
        )

        tm.that(u.Tests.run_lazy_init(repository_root), eq=0)
        generated = u.Tests.generated_init(package_root)

        tm.that(generated, lacks="FlextModelsDemoBase")
        tm.that(generated, lacks="._models.base")
        tm.that(generated, lacks="._models._base.Flextmodelsdemobase_part_01")

    @staticmethod
    def test_explicit_all_exports_keep_public_aliases_only(
        tmp_path: Path,
    ) -> None:
        """Respect an explicit module export contract without leaking siblings."""
        repository_root, package_root = u.Tests.demo_lazy_init_workspace(tmp_path)
        (package_root / "api.py").write_text(
            "from __future__ import annotations\n\n"
            "class FlextDemo:\n"
            "    pass\n\n"
            "demo = FlextDemo()\n"
            "hidden = FlextDemo()\n\n"
            '__all__: list[str] = ["FlextDemo", "demo"]\n',
            encoding=c.DEFAULT_ENCODING,
        )

        tm.that(u.Tests.run_lazy_init(repository_root), eq=0)
        exports_content = u.Tests.generated_init(package_root)

        tm.that(exports_content, has='"FlextDemo"')
        tm.that(exports_content, has='"demo"')
        tm.that(exports_content, lacks="hidden")

    @staticmethod
    def test_child_packages_never_widen_the_public_root(tmp_path: Path) -> None:
        """Keep every child-package declaration behind its owning facade."""
        repository_root, package_root = u.Tests.demo_lazy_init_workspace(tmp_path)
        child_dir = package_root / "services"
        child_dir.mkdir()
        (child_dir / c.Infra.INIT_PY).write_text("", encoding=c.DEFAULT_ENCODING)
        (child_dir / "service.py").write_text(
            "from __future__ import annotations\n\n"
            "class FlextDemoService:\n"
            "    pass\n\n"
            '__all__: list[str] = ["FlextDemoService"]\n',
            encoding=c.DEFAULT_ENCODING,
        )
        (child_dir / "colors.py").write_text(
            'from __future__ import annotations\n\nBLUE = "blue"\n\n'
            '__all__: list[str] = ["BLUE"]\n',
            encoding=c.DEFAULT_ENCODING,
        )
        (child_dir / "cli.py").write_text(
            "from __future__ import annotations\n\n"
            'def main() -> str:\n    return "ok"\n',
            encoding=c.DEFAULT_ENCODING,
        )
        u.Tests.write_lazy_init_namespace_module(
            child_dir / "models.py",
            class_name="FlextModelsDemoServices",
            alias="m",
            docstring="Models.",
        )

        tm.that(u.Tests.run_lazy_init(repository_root), eq=0)
        exports_content = u.Tests.generated_init(package_root)

        tm.that(exports_content, has='"services"')
        child_content = u.Tests.generated_init(child_dir)
        for name in ("FlextDemoService", "BLUE", "FlextModelsDemoServices", "m"):
            tm.that(exports_content, lacks=f'"{name}"')
            tm.that(child_content, has=f'"{name}"')
        tm.that(child_content, lacks='"main"')

    @staticmethod
    def test_generated_constants_owner_never_widens_parent_map(
        tmp_path: Path,
    ) -> None:
        """Test generated constants owner never widens parent map."""
        repository_root, package_root = u.Tests.demo_lazy_init_workspace(tmp_path)
        u.Tests.write_lazy_init_namespace_module(
            package_root / "models.py",
            class_name="FlextModelsDemo",
            alias="m",
        )

        tm.that(u.Tests.run_lazy_init(repository_root), eq=0)
        first = u.Tests.generated_init(package_root)
        tm.that(u.Tests.run_lazy_init(repository_root, check_only=True), eq=0)

        tm.that(u.Tests.generated_init(package_root), eq=first)
        tm.that(first, lacks='"._constants"')

    @staticmethod
    def test_tests_root_facade_is_generated_lazily(tmp_path: Path) -> None:
        """Generate the tests root facade with local publics and inherited aliases."""
        repository_root, _package_root = u.Tests.demo_lazy_init_workspace(tmp_path)
        tests_root = repository_root / c.Infra.DIR_TESTS
        tests_root.mkdir()
        tests_root.joinpath(c.Infra.INIT_PY).write_text(
            "",
            encoding=c.DEFAULT_ENCODING,
        )
        tests_root.joinpath(c.Infra.CONSTANTS_PY).write_text(
            "from __future__ import annotations\n\n"
            "class TestsFlextDemoConstants:\n"
            "    pass\n\n"
            "c = TestsFlextDemoConstants\n\n"
            '__all__: list[str] = ["TestsFlextDemoConstants", "c"]\n',
            encoding=c.DEFAULT_ENCODING,
        )
        child_dir = tests_root / "unit"
        child_dir.mkdir()
        (child_dir / c.Infra.INIT_PY).write_text("", encoding=c.DEFAULT_ENCODING)
        (child_dir / "child.py").write_text(
            "from __future__ import annotations\n\n"
            "class Child:\n"
            "    pass\n\n"
            '__all__: list[str] = ["Child"]\n',
            encoding=c.DEFAULT_ENCODING,
        )

        tm.that(u.Tests.run_lazy_init(repository_root), eq=0)
        init_content = tests_root.joinpath(c.Infra.INIT_PY).read_text(
            encoding=c.DEFAULT_ENCODING,
        )
        # Lazy inits cover EVERY python surface (src, tests, examples,
        # scripts): the tests root is a generated PEP 562 facade too.
        tm.that(init_content, has="install_lazy_exports(")
        tm.that(init_content, has='"TestsFlextDemoConstants"')
        compile(init_content, "tests/__init__.py", "exec")
        check_service = u.Tests.create_lazy_init_service(repository_root)
        tm.that(u.Tests.lazy_init_effects(check_service.plan_files()), empty=True)

    @staticmethod
    def test_root_aliases_follow_transitive_parent_exports_from_source(
        tmp_path: Path,
    ) -> None:
        """Order inherited aliases by the canonical facade dependency chain."""
        repository_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-meltano",
            package_name="flext_meltano",
        )
        _, core_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-core",
            package_name="flext_core",
        )
        u.Tests.write_lazy_init_namespace_module(
            core_root / "result.py",
            class_name="FlextCoreResult",
            alias="r",
            docstring="Result.",
        )
        core_root.joinpath(c.Infra.CONSTANTS_PY).write_text(
            "from __future__ import annotations\n\n"
            "class FlextCoreConstants:\n"
            "    pass\n\n"
            '__all__: list[str] = ["FlextCoreConstants"]\n',
            encoding=c.DEFAULT_ENCODING,
        )
        _, cli_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-cli",
            package_name="flext_cli",
        )
        cli_root.joinpath(c.Infra.INIT_PY).write_text(
            '__all__: list[str] = ["c", "r"]\n',
            encoding=c.DEFAULT_ENCODING,
        )
        cli_root.joinpath(c.Infra.CONSTANTS_PY).write_text(
            "from __future__ import annotations\n\n"
            "from flext_core import FlextCoreConstants\n\n"
            "class FlextCliConstants(FlextCoreConstants):\n"
            "    pass\n\n"
            '__all__: list[str] = ["FlextCliConstants"]\n',
            encoding=c.DEFAULT_ENCODING,
        )
        package_root.joinpath(c.Infra.CONSTANTS_PY).write_text(
            "from __future__ import annotations\n\n"
            "from flext_cli import c\n\n"
            "class FlextMeltanoConstants(c):\n"
            "    pass\n\n"
            '__all__: list[str] = ["FlextMeltanoConstants"]\n',
            encoding=c.DEFAULT_ENCODING,
        )

        tm.that(u.Tests.run_lazy_init(repository_root), eq=0)
        init_content = u.Tests.generated_init(package_root)
        exports_content = u.Tests.generated_init(package_root)

        tm.that(init_content, lacks="_LAZY_MODULES")
        entries, _refs = u.Infra.lazy_import_mapping_source(exports_content)
        tm.that(dict(entries).get("flext_cli", ()), has="r")
        tm.that(init_content, has="__all__: tuple[str, ...]")
        tm.that(init_content, has="install_lazy_exports(")
        tm.that(init_content, lacks="_root_typing_parts")
        ruff_ordered_aliases = ("c", "d", "e", "h", "m", "p", "r", "s", "t", "u", "x")
        for alias_name in ruff_ordered_aliases:
            tm.that(init_content, has=f'    "{alias_name}",')
        has_all, public_exports = u.Tests.extract_lazy_init_exports(init_content)
        tm.ok(has_all)
        # __all__ follows RUF022; dependency order remains
        # exclusively in the static facade imports.
        alias_positions = tuple(
            public_exports.index(alias) for alias in ruff_ordered_aliases
        )
        tm.that(alias_positions, eq=tuple(sorted(alias_positions)))
        # ADR-018 p.1: the owner of a letter is the module that DECLARES it in
        # its own ``__all__``. This facade extends the parent's ``c`` but
        # declares only its class, so every letter here is inherited from the
        # nearest declaring facade — ``c`` included. Extending a letter is not
        # declaring it; the B1 fix writes the declaration when the module means
        # to own it, and until then the generator propagates, never infers.
        tm.that(
            init_content.splitlines(),
            has="    from flext_cli import c, d, e, h, m, p, r, s, t, u, x",
        )
        tm.that(init_content, lacks="FlextMeltanoConstants as c")
        tm.that(dict(entries).get("flext_cli", ()), has="c")
        tm.that(dict(entries).get(".constants", ()), has="FlextMeltanoConstants")

    @staticmethod
    def test_existing_root_composes_public_parent_aliases(tmp_path: Path) -> None:
        """Test existing root composes public parent aliases."""
        repository_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-demo",
            package_name="flext_demo",
        )
        u.Tests.write_project_beads_config(repository_root, "flext-demo")
        package_root.joinpath(c.Infra.CONSTANTS_PY).write_text(
            "from __future__ import annotations\n\n"
            "from flext_cli import c\n\n"
            "class FlextDemoConstants(c):\n"
            "    pass\n\n"
            '__all__: list[str] = ["FlextDemoConstants", "c"]\n',
            encoding=c.DEFAULT_ENCODING,
        )

        tm.that(u.Tests.run_lazy_init(repository_root), eq=0)
        generated = u.Tests.generated_init(package_root)
        exports = u.Tests.generated_init(package_root)
        entries, _refs = u.Infra.lazy_import_mapping_source(exports)
        tm.that(dict(entries).get("flext_cli", ()), has="r")
        tm.that(generated, has='    "r",')
        tm.that(generated, has='    "c",')

    @staticmethod
    def test_generated_parent_initializer_is_not_an_alias_owner(
        tmp_path: Path,
    ) -> None:
        """Ignore stale aliases that exist only in a generated parent projection."""
        repository_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-child",
            package_name="flext_child",
        )
        parent_root = repository_root / c.Infra.DEFAULT_SRC_DIR / "flext_parent"
        parent_root.mkdir(parents=True)
        parent_root.joinpath(c.Infra.INIT_PY).write_text(
            f'{c.Infra.AUTOGEN_HEADER}\n__all__ = ("x",)\n',
            encoding=c.DEFAULT_ENCODING,
        )
        parent_root.joinpath(c.Infra.CONSTANTS_PY).write_text(
            "class FlextParentConstants:\n"
            "    pass\n\n"
            '__all__ = ("FlextParentConstants",)\n',
            encoding=c.DEFAULT_ENCODING,
        )
        package_root.joinpath(c.Infra.CONSTANTS_PY).write_text(
            "from flext_parent import c\n\n"
            "class FlextChildConstants(c):\n"
            "    pass\n\n"
            '__all__ = ("FlextChildConstants",)\n',
            encoding=c.DEFAULT_ENCODING,
        )

        service = u.Tests.create_lazy_init_service(repository_root).model_copy(
            update={"target_module": "flext_child"},
        )
        planned = tm.ok(service.plan_files())
        generated = next(
            u.Tests.codegen_file_text(plan)
            for plan in planned
            if plan.path == package_root.joinpath(c.Infra.INIT_PY).resolve()
        )

        tm.that(generated, lacks='"x"')
        tm.that(generated, lacks='"flext_parent": ("x",)')

    @staticmethod
    def test_installed_parent_alias_uses_the_nearest_actual_owner(
        tmp_path: Path,
    ) -> None:
        """An installed parent re-exporting a letter serves it, not its owner.

        Each installed package has the published FLEXT shape (ADR-018 p.1-2):
        a facade module declares its letter in its own ``__all__`` and the
        package initializer only propagates it. The child inherits ``r``
        through ``nearest_parent``, which re-exports it from the declaring
        ``owner_parent``; the election names the nearest re-exporting parent
        (operator ruling 2026-09-23). Every installed module raises on import,
        so the planner can only read them by path.
        """
        repository_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-child",
            package_name="flext_child",
        )
        installed_root = tmp_path / "installed"
        guard = 'raise RuntimeError("must not import")\n'
        sys.path.insert(0, str(installed_root))
        try:
            nearest = installed_root / "nearest_parent"
            owner = installed_root / "owner_parent"
            nearest.mkdir(parents=True)
            owner.mkdir(parents=True)
            owner.joinpath("result.py").write_text(
                "class OwnerParentResult:\n    pass\n\n"
                "r = OwnerParentResult\n"
                f'__all__ = ("OwnerParentResult", "r")\n{guard}',
                encoding=c.DEFAULT_ENCODING,
            )
            owner.joinpath(c.Infra.INIT_PY).write_text(
                "from .result import OwnerParentResult, r\n\n"
                f'__all__ = ("OwnerParentResult", "r")\n{guard}',
                encoding=c.DEFAULT_ENCODING,
            )
            nearest.joinpath(c.Infra.CONSTANTS_PY).write_text(
                "class NearestParentConstants:\n    pass\n\n"
                "c = NearestParentConstants\n"
                f'__all__ = ("NearestParentConstants", "c")\n{guard}',
                encoding=c.DEFAULT_ENCODING,
            )
            nearest.joinpath(c.Infra.INIT_PY).write_text(
                "from owner_parent import r\n\n"
                "from .constants import NearestParentConstants, c\n\n"
                f'__all__ = ("NearestParentConstants", "c", "r")\n{guard}',
                encoding=c.DEFAULT_ENCODING,
            )
            package_root.joinpath(c.Infra.CONSTANTS_PY).write_text(
                "from nearest_parent import NearestParentConstants\n\n"
                "class FlextChildConstants(NearestParentConstants):\n"
                "    pass\n\n"
                "c = FlextChildConstants\n"
                '__all__ = ("FlextChildConstants", "c")\n',
                encoding=c.DEFAULT_ENCODING,
            )

            tm.that(u.Tests.run_lazy_init(repository_root), eq=0)
            generated = u.Tests.generated_init(package_root)
            entries, _refs = u.Infra.lazy_import_mapping_source(generated)
            sources = dict(entries)

            tm.that(sources.get("nearest_parent", ()), has="r")
            tm.that(sources, lacks="owner_parent")
            tm.that(u.Tests.run_lazy_init(repository_root, check_only=True), eq=0)
        finally:
            sys.path.remove(str(installed_root))

    @staticmethod
    def test_non_flext_root_derives_inherited_aliases_beyond_stale_all(
        tmp_path: Path,
    ) -> None:
        """Derive the root ABI from facade owners, never the prior projection."""
        # ai_hub's stale __all__ omitted r and became a second SSOT;
        # regeneration must follow the declared composition parent.
        repository_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="ai-hub",
            package_name="ai_hub",
        )
        package_root.joinpath(c.Infra.INIT_PY).write_text(
            f"{c.Infra.AUTOGEN_HEADER}\n"
            '__all__: tuple[str, ...] = ("AiHubModels", "m")\n',
            encoding=c.DEFAULT_ENCODING,
        )
        u.Tests.write_lazy_init_namespace_module(
            package_root / "models.py",
            class_name="AiHubModels",
            alias="m",
        )
        package_root.joinpath(c.Infra.CONSTANTS_PY).write_text(
            "from __future__ import annotations\n\n"
            "from flext_infra import c as upstream\n\n"
            "class AiHubConstants(upstream):\n"
            "    pass\n\n"
            "c = AiHubConstants\n"
            '__all__ = ("AiHubConstants", "c")\n',
            encoding=c.DEFAULT_ENCODING,
        )

        tm.that(u.Tests.run_lazy_init(repository_root), eq=0)
        generated = u.Tests.generated_init(package_root)
        has_all, public_exports = u.Tests.extract_lazy_init_exports(generated)

        tm.ok(has_all)
        published_aliases = c.Infra.ALIAS_NAMES.intersection(flext_infra.__all__)
        inherited_aliases = published_aliases - {"c", "m"}
        tm.that(published_aliases, has="r")
        tm.that(published_aliases, lacks="tc")
        tm.that(c.Infra.ALIAS_NAMES.intersection(public_exports), eq=published_aliases)
        entries, _refs = u.Infra.lazy_import_mapping_source(generated)
        tm.that(
            dict(entries).get("flext_infra", ()), eq=tuple(sorted(inherited_aliases))
        )
        tm.that(
            u.Tests.run_lazy_init_probe(
                "import ai_hub\nimport flext_infra\n"
                "from flext_tests import tm\n"
                f"for name in {tuple(sorted(inherited_aliases))!r}:\n"
                "    assert getattr(ai_hub, name) is getattr(flext_infra, name)\n"
                "assert ai_hub.c is ai_hub.AiHubConstants\n"
                "assert flext_infra.c in ai_hub.c.__mro__\n"
                "assert ai_hub.c is not flext_infra.c\n"
                "assert ai_hub.m is ai_hub.AiHubModels\n"
                "assert 'tc' not in ai_hub.__all__\n"
                "try:\n    from ai_hub import tc\n"
                "except ImportError:\n    print('undeclared alias rejected')\n"
                "else:\n    tm.reject('tc has no public owner')\n"
                "print('published alias identities preserved')\n",
                python_paths=(str(repository_root / "src"), *sys.path),
                cwd=repository_root,
            ),
            eq=["undeclared alias rejected", "published alias identities preserved"],
        )
        tm.that(u.Tests.run_lazy_init(repository_root, check_only=True), eq=0)
        tm.that(u.Tests.generated_init(package_root), eq=generated)

    @staticmethod
    def test_root_keeps_declared_public_git_and_work_services(
        tmp_path: Path,
    ) -> None:
        """Publish service owners declared by root namespace configuration."""
        repository_root, package_root = u.Tests.demo_lazy_init_workspace(tmp_path)
        package_root.joinpath("git.py").write_text(
            "class FlextDemoGitService:\n"
            '    """Public Git service."""\n\n'
            '__all__ = ("FlextDemoGitService",)\n',
            encoding=c.DEFAULT_ENCODING,
        )
        package_root.joinpath("work.py").write_text(
            "class FlextDemoWorkService:\n"
            '    """Public work service."""\n\n'
            '__all__ = ("FlextDemoWorkService",)\n',
            encoding=c.DEFAULT_ENCODING,
        )

        tm.that(u.Tests.run_lazy_init(repository_root), eq=0)
        generated = u.Tests.generated_init(package_root)
        exports = u.Tests.generated_init(package_root)

        tm.that(generated, has='"FlextDemoGitService"')
        tm.that(generated, has='"FlextDemoWorkService"')
        entries, _refs = u.Infra.lazy_import_mapping_source(exports)
        tm.that(dict(entries).get(c.GIT_DIR_NAME, ()), has="FlextDemoGitService")
        tm.that(dict(entries).get(".work", ()), has="FlextDemoWorkService")

    @staticmethod
    def test_nested_tests_namespace_uses_public_test_facades(
        tmp_path: Path,
    ) -> None:
        """Generate nested test namespaces with their local publics."""
        repository_root, package_root = u.Tests.demo_lazy_init_workspace(tmp_path)
        package_root.joinpath(c.Infra.RESULT_PY).write_text(
            "from __future__ import annotations\n\nclass FlextDemoResult:\n    pass\n",
            encoding=c.DEFAULT_ENCODING,
        )
        tests_unit_root = repository_root / c.Infra.DIR_TESTS / "unit"
        tests_unit_root.mkdir(parents=True)
        tests_unit_root.joinpath(c.Infra.INIT_PY).write_text(
            "",
            encoding=c.DEFAULT_ENCODING,
        )
        # `__all__` is the publication contract on EVERY surface — a module
        # that declares nothing publishes nothing, in tests exactly as in src.
        # The fixture declares its publics like every other module here does,
        # so what this test proves is the tests-namespace routing, not the
        # unrelated question of undeclared symbols.
        tests_unit_root.joinpath(c.Infra.CONSTANTS_PY).write_text(
            "from __future__ import annotations\n\n"
            "class TestsFlextDemoUnitConstants:\n"
            "    pass\n\n"
            "c = TestsFlextDemoUnitConstants\n\n"
            '__all__: list[str] = ["TestsFlextDemoUnitConstants", "c"]\n',
            encoding=c.DEFAULT_ENCODING,
        )
        tests_unit_root.joinpath(c.Infra.MODELS_PY).write_text(
            "from __future__ import annotations\n\n"
            "class TestsFlextDemoUnitModels:\n"
            "    pass\n\n"
            "m = TestsFlextDemoUnitModels\n\n"
            '__all__: list[str] = ["TestsFlextDemoUnitModels", "m"]\n',
            encoding=c.DEFAULT_ENCODING,
        )

        tm.that(u.Tests.run_lazy_init(repository_root), eq=0)
        init_content = tests_unit_root.joinpath(c.Infra.INIT_PY).read_text(
            encoding=c.DEFAULT_ENCODING,
        )
        for public_name in ("c", "m"):
            tm.that(init_content, has=f'"{public_name}"')
        for undeclared_name in set(c.Infra.TEST_RUNTIME_ALIAS_TARGETS) - {"c", "m"}:
            tm.that(init_content, lacks=f'"{undeclared_name}"')
        tm.that(init_content, lacks="FlextDemoResult")
