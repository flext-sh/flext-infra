"""Published runtime identities of generated lazy package artifacts.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import difflib
import sys
from pathlib import Path

import pytest

from flext_infra import infra
from tests import c, m, p, t, tm, u


class TestsFlextInfraLazyInitPublishedRuntime:
    """Consume published package identities and enforce admission before effects."""

    @staticmethod
    def _generate_package(tmp_path: Path) -> t.Pair[Path, Path]:
        repository_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-lazy-demo",
            package_name="flext_lazy_demo",
        )
        package_root.joinpath("api.py").write_text(
            "from pathlib import Path\n"
            "COUNTER = Path(__file__).with_name('imports.txt')\n"
            "COUNTER.write_text("
            "COUNTER.read_text() + 'x' if COUNTER.exists() else 'x')\n"
            "class FlextDemo:\n    pass\n"
            "primary = FlextDemo\n"
            "__all__ = ('FlextDemo', 'primary')\n",
            encoding=c.DEFAULT_ENCODING,
        )
        tm.that(u.Tests.run_lazy_init(repository_root), eq=0)
        return repository_root, package_root

    def test_generated_root_preserves_lazy_runtime_contract(
        self,
        tmp_path: Path,
    ) -> None:
        """Test generated root preserves lazy runtime contract."""
        repository_root, package_root = self._generate_package(tmp_path)
        tm.that(
            u.Tests.run_lazy_init_probe(
                "import sys\n"
                "import flext_lazy_demo as package\n"
                "print('flext_lazy_demo.api' not in sys.modules)\n"
                "print(package.__all__ == ('FlextDemo', 'primary'))\n"
                "print(dir(package) == list(package.__all__))\n"
                "first = package.FlextDemo\n"
                "print(first is package.FlextDemo is package.primary)\n",
                python_paths=(str(repository_root / c.Infra.DEFAULT_SRC_DIR),),
            ),
            eq=["True"] * 4,
        )
        tm.that(package_root.joinpath("imports.txt").read_text(), eq="x")

    @staticmethod
    def test_generated_version_metadata_survives_public_export_traversal(
        tmp_path: Path,
    ) -> None:
        """Resolving the version class cannot shadow the declared version scalar."""
        repository, package = u.Tests.create_lazy_init_workspace(tmp_path)
        metadata = tm.ok(u.Infra.read_project_metadata_result(repository))
        version_name = c.Infra.DUNDER_VERSION
        version = metadata.project.version
        package.joinpath(f"{version_name}.py").write_text(
            "class FlextVersion:\n"
            f"    {version_name}: str = {version!r}\n"
            f"{version_name} = FlextVersion.{version_name}\n"
            f"__title__ = {metadata.project.name!r}\n"
            f"__all__ = ('FlextVersion', {version_name!r}, '__title__')\n",
            encoding=c.DEFAULT_ENCODING,
        )
        tm.that(u.Tests.run_lazy_init(repository), eq=0)
        tm.that(
            u.Tests.run_lazy_init_probe(
                f"import {package.name} as generated\n"
                "print(isinstance(generated.FlextVersion, type))\n"
                f"print({version_name!r} in generated.__all__)\n"
                "print(all(getattr(generated, name) is not None\n"
                "          for name in generated.__all__\n"
                f"          if name != {version_name!r}))\n"
                f"value = getattr(generated, {version_name!r})\n"
                f"print(isinstance(value, str) and value == {version!r})\n",
                python_paths=(str(package.parent),),
            ),
            eq=["True"] * 4,
        )

    @staticmethod
    def test_generated_root_never_invents_undeclared_api_alias(
        tmp_path: Path,
    ) -> None:
        """Test generated root never invents undeclared api alias."""
        repository_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-bare",
            package_name="flext_bare",
        )
        package_root.joinpath("api.py").write_text(
            "class FlextBare:\n    pass\n__all__ = ('FlextBare',)\n",
            encoding=c.DEFAULT_ENCODING,
        )
        tm.that(u.Tests.run_lazy_init(repository_root), eq=0)
        tm.that(
            u.Tests.run_lazy_init_probe(
                "import flext_bare as package\n"
                "print(package.__all__ == ('FlextBare',))\n"
                "print(all(hasattr(package, name) for name in package.__all__))\n",
                python_paths=(str(repository_root / c.Infra.DEFAULT_SRC_DIR),),
            ),
            eq=["True", "True"],
        )

    @staticmethod
    def test_generated_model_alias_preserves_mro_and_pydantic_roundtrip(
        tmp_path: Path,
    ) -> None:
        """Resolve deferred annotations through the generated public model alias."""
        repository, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-runtime-model",
            package_name="flext_runtime_model",
        )
        package_root.joinpath("models.py").write_text(
            "from __future__ import annotations\n"
            "from flext_core import FlextModels\n"
            "class FlextRuntimeModels(FlextModels):\n"
            "    class Payload(FlextModels.ContractModel):\n"
            '        count: int = FlextModels.Field(description="Payload count.")\n'
            "m = FlextRuntimeModels\n"
            "__all__ = ('FlextRuntimeModels', 'm')\n",
            encoding=c.DEFAULT_ENCODING,
        )
        tm.that(u.Tests.run_lazy_init(repository), eq=0)
        probe = (
            "import sys\n"
            "from flext_core import FlextModels, e\n"
            "import flext_runtime_model as package\n"
            "print('flext_runtime_model.models' not in sys.modules)\n"
            "models = package.m\n"
            "print(models is package.FlextRuntimeModels is package.m)\n"
            "print(issubclass(models, FlextModels))\n"
            "payload = models.Payload.model_validate({'count': 7})\n"
            "print(payload.count == 7)\n"
            "print(models.Payload.model_validate_json(payload.model_dump_json())"
            " == payload)\n"
            "try:\n"
            "    models.Payload.model_validate({'count': 'invalid'})\n"
            "except e.PydanticValidationError as error:\n"
            "    print('count' in str(error))\n"
            "print(dir(package) == list(package.__all__))\n"
        )
        tm.that(
            u.Tests.run_lazy_init_probe(
                probe,
                python_paths=(str(repository / c.Infra.DEFAULT_SRC_DIR),),
            ),
            eq=["True"] * 7,
        )

    @staticmethod
    @pytest.mark.parametrize("same_named_export", [False, True])
    def test_child_package_preserves_export_ownership(
        tmp_path: Path,
        *,
        same_named_export: bool,
    ) -> None:
        """A child's own exports never replace its parent's package binding."""
        repository, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-child-runtime",
            package_name="flext_child_runtime",
        )
        child = package_root / "child"
        child.mkdir()
        package_root.joinpath(c.Infra.INIT_PY).write_text(
            "from . import child as child\n__all__ = ('child',)\n",
            encoding=c.DEFAULT_ENCODING,
        )
        (child / c.Infra.INIT_PY).write_text("", encoding=c.DEFAULT_ENCODING)
        (child / "api.py").write_text(
            "class PublishedChild:\n    pass\n"
            + (
                "child = PublishedChild\n__all__ = ('PublishedChild', 'child')\n"
                if same_named_export
                else "__all__ = ('PublishedChild',)\n"
            ),
            encoding=c.DEFAULT_ENCODING,
        )
        tm.that(u.Tests.run_lazy_init(repository), eq=0)
        probe = (
            "import flext_child_runtime as package\n"
            "import flext_child_runtime.child as child\n"
            "print(package.child is child)\n"
            "print('PublishedChild' not in package.__all__)\n"
            "print(isinstance(child.PublishedChild(), child.PublishedChild))\n"
        )
        if same_named_export:
            probe += "print(child.child is child.PublishedChild)\n"
        tm.that(
            u.Tests.run_lazy_init_probe(
                probe,
                python_paths=(str(repository / c.Infra.DEFAULT_SRC_DIR),),
            ),
            eq=["True"] * (4 if same_named_export else 3),
        )

    @staticmethod
    def test_empty_package_preserves_its_unmanaged_initializer(tmp_path: Path) -> None:
        """No published declarations means no generated root contract is invented."""
        repository, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-empty-runtime",
            package_name="flext_empty_runtime",
        )
        package_root.joinpath("api.py").write_text(
            "__all__ = ()\n",
            encoding=c.DEFAULT_ENCODING,
        )
        initializer = package_root / c.Infra.INIT_PY
        initializer.write_text(
            '"""Authored package without published declarations."""\n',
            encoding=c.DEFAULT_ENCODING,
        )
        original = initializer.read_text(encoding=c.DEFAULT_ENCODING)
        tm.that(u.Tests.run_lazy_init(repository), eq=0)
        tm.that(initializer.read_text(encoding=c.DEFAULT_ENCODING), eq=original)
        probe = (
            "import flext_empty_runtime as package\n"
            "print(not hasattr(package, '__all__'))\n"
            "try:\n"
            "    package.undeclared\n"
            "except AttributeError as error:\n"
            "    print('undeclared' in str(error))\n"
        )
        tm.that(
            u.Tests.run_lazy_init_probe(
                probe,
                python_paths=(str(repository / c.Infra.DEFAULT_SRC_DIR),),
            ),
            eq=["True", "True"],
        )

    @staticmethod
    def test_generated_root_preserves_import_failures(tmp_path: Path) -> None:
        """Test generated root preserves import failures."""
        repository_root, package_root = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-failure",
            package_name="flext_failure",
        )
        package_root.joinpath("api.py").write_text(
            "raise ModuleNotFoundError('missing runtime dependency')\n"
            "class FlextDemo:\n    pass\n"
            "__all__ = ('FlextDemo',)\n",
            encoding=c.DEFAULT_ENCODING,
        )
        tm.that(u.Tests.run_lazy_init(repository_root), eq=0)
        tm.that(
            u.Tests.run_lazy_init_probe(
                "import flext_failure as package\n"
                "try:\n"
                "    package.FlextDemo\n"
                "except ModuleNotFoundError as error:\n"
                "    print(str(error) == 'missing runtime dependency')\n",
                python_paths=(str(repository_root / c.Infra.DEFAULT_SRC_DIR),),
            ),
            eq=["True"],
        )

    @staticmethod
    @pytest.mark.parametrize("absent", [False, True])
    def test_public_generation_repairs_existing_and_absent_initializers(
        tmp_path: Path,
        session_runtime: p.Tests.SessionRuntime,
        *,
        absent: bool,
    ) -> None:
        """Generate artifacts without rewriting authored source."""
        repository, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-source-only",
            package_name="flext_source_only",
        )
        u.Tests.write_lazy_init_namespace_module(
            package / "models.py",
            class_name="FlextSourceOnlyModels",
            alias="m",
        )
        tm.that(u.Tests.run_lazy_init(repository), eq=0)
        initializer = package / c.Infra.INIT_PY
        original = initializer.read_bytes()
        if absent:
            initializer.unlink()
        authored = package / "api.py"
        authored.write_text(
            "import os\n\n"
            "class FlextSourceOnlyApi:\n"
            '    """Authored public API with an intentionally unused import."""\n'
            "__all__ = ('FlextSourceOnlyApi',)\n",
            encoding=c.DEFAULT_ENCODING,
        )
        child = package / "child"
        child.mkdir()
        child.joinpath("api.py").write_text(
            "from flext_source_only.api import FlextSourceOnlyApi\n"
            "class FlextSourceOnlyChild(FlextSourceOnlyApi):\n"
            '    """Authored child using the real public parent."""\n'
            "__all__ = ('FlextSourceOnlyChild',)\n",
            encoding=c.DEFAULT_ENCODING,
        )
        before = {path: path.read_bytes() for path in package.rglob("*.py")}
        request = m.Infra.CodegenGenerateRequest(
            root=repository,
            what=c.Infra.CodegenConformSurface.LAZY_INIT,
            scope=c.Infra.CodegenConformScope.SELF,
        )
        tm.ok(
            u.Tests.create_python_environment(
                repository,
                dependency_projects=u.Tests.python_dependency_projects(repository),
                session_runtime=session_runtime,
            )
        )
        tm.ok(infra.codegen_generate(request))
        tm.fail(initializer.read_bytes() == original)
        tm.ok((child / c.Infra.INIT_PY).is_file())
        generated = {path: path.read_bytes() for path in package.rglob(c.Infra.INIT_PY)}
        tm.ok(infra.codegen_generate(request))
        for path, original in generated.items():
            current = path.read_bytes()
            tm.that(
                current,
                eq=original,
                msg="\n".join(
                    difflib.unified_diff(
                        original.decode(c.DEFAULT_ENCODING).splitlines(),
                        current.decode(c.DEFAULT_ENCODING).splitlines(),
                        fromfile=f"first/{path.name}",
                        tofile=f"second/{path.name}",
                    )
                ),
            )
        for path, content in before.items():
            if path != initializer:
                tm.that(path.read_bytes(), eq=content)
        tm.that(
            u.Tests.run_lazy_init_probe(
                "import sys\nimport flext_source_only as package\n"
                "print('flext_source_only.api' not in sys.modules)\n"
                "print('flext_source_only.child.api' not in sys.modules)\n"
                "from flext_source_only.api import FlextSourceOnlyApi\n"
                "print(package.FlextSourceOnlyApi is FlextSourceOnlyApi)\n"
                "print(issubclass(package.child.FlextSourceOnlyChild, "
                "FlextSourceOnlyApi))\n"
                "print(package.m is package.FlextSourceOnlyModels)\n"
                "print(dir(package) == list(package.__all__))\n"
                "print(all(getattr(package, name) is not None "
                "for name in package.__all__))\n",
                python_paths=(str(repository / c.Infra.DEFAULT_SRC_DIR),),
            ),
            eq=["True"] * 7,
        )

    @staticmethod
    @pytest.mark.parametrize("cyclic", [False, True])
    def test_public_generation_rejects_authored_import_failures_before_publication(
        tmp_path: Path,
        session_runtime: p.Tests.SessionRuntime,
        *,
        cyclic: bool,
    ) -> None:
        """Reject missing and cyclic authored imports before publication."""
        repository, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-source-only",
            package_name="flext_source_only",
        )
        u.Tests.write_lazy_init_namespace_module(
            package / "models.py", class_name="FlextSourceOnlyModels", alias="m"
        )
        tm.that(u.Tests.run_lazy_init(repository), eq=0)
        authored = package / "api.py"
        authored.write_text(
            (
                "from flext_source_only.child.api import FlextSourceOnlyChild\n"
                if cyclic
                else "raise ModuleNotFoundError('unavailable runtime dependency')\n"
            )
            + "class FlextSourceOnlyApi:\n    pass\n"
            "__all__ = ('FlextSourceOnlyApi',)\n",
            encoding=c.DEFAULT_ENCODING,
        )
        child = package / "child"
        child.mkdir()
        (child / "api.py").write_text(
            "from flext_source_only.api import FlextSourceOnlyApi\n"
            "class FlextSourceOnlyChild:\n    pass\n"
            "__all__ = ('FlextSourceOnlyChild',)\n",
            encoding=c.DEFAULT_ENCODING,
        )
        before = tuple(
            tm.ok(u.Cli.atomic_read_binary_file_state(path, required=True))
            for path in package.rglob("*.py")
        )
        tm.ok(
            u.Tests.create_python_environment(
                repository,
                dependency_projects=u.Tests.python_dependency_projects(repository),
                session_runtime=session_runtime,
            )
        )
        rejected = infra.codegen_generate(
            m.Infra.CodegenGenerateRequest(
                root=repository,
                what=c.Infra.CodegenConformSurface.LAZY_INIT,
                scope=c.Infra.CodegenConformScope.SELF,
            )
        )
        tm.fail(
            rejected,
            has="ImportError" if cyclic else "unavailable runtime dependency",
        )
        tm.ok(u.Cli.atomic_verify_binary_file_states(before))
        tm.fail((child / c.Infra.INIT_PY).exists())

    @staticmethod
    def test_conflicted_generated_initializer_is_rebuilt_from_declarations(
        tmp_path: Path,
    ) -> None:
        """Generated bytes are outputs, including while a merge is unresolved."""
        repository, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-rebuilt",
            package_name="flext_rebuilt",
        )
        declaration = package / "models.py"
        u.Tests.write_lazy_init_namespace_module(
            declaration,
            class_name="FlextRebuiltModels",
            alias="m",
            docstring="Models.",
        )
        tm.that(u.Tests.run_lazy_init(repository), eq=0)
        initializer = package / c.Infra.INIT_PY
        canonical = initializer.read_text(encoding=c.DEFAULT_ENCODING)
        conflicted = canonical + (
            "\n<<<<<<< HEAD\n__all__ = ['stale']\n"
            "=======\n__all__ = ['obsolete']\n>>>>>>> incoming\n"
        )
        initializer.write_text(conflicted, encoding=c.DEFAULT_ENCODING)
        with infra.rope_workspace(repository) as rope:
            layout = tm.not_none(rope.layout(repository))
            tm.that(layout.runtime_aliases, eq=("m",))
        tm.that(initializer.read_text(encoding=c.DEFAULT_ENCODING), eq=conflicted)

        tm.that(u.Tests.run_lazy_init(repository), eq=0)

        tm.that(initializer.read_text(encoding=c.DEFAULT_ENCODING), eq=canonical)
        tm.that(
            u.Tests.run_lazy_init_probe(
                "import flext_rebuilt as generated\n"
                "from flext_rebuilt.models import FlextRebuiltModels\n"
                "print(generated.m is FlextRebuiltModels)\n"
                "print(all(hasattr(generated, name) for name in generated.__all__))\n",
                python_paths=(str(repository / c.Infra.DEFAULT_SRC_DIR),),
            ),
            eq=["True", "True"],
        )
        declaration.write_text(
            "<<<<<<< HEAD\n=======\n>>>>>>> incoming\n",
            encoding=c.DEFAULT_ENCODING,
        )
        with infra.rope_workspace(repository) as rope, pytest.raises(SyntaxError):
            rope.layout(repository)

    @staticmethod
    def test_internal_facade_requires_its_local_declaration(
        tmp_path: Path,
    ) -> None:
        """An undeclared letter propagates the declaring root's binding.

        Operator ruling (tier-alias propagation): a module declaring the
        letter wins. A facet that declares no letter inherits the root's
        declared letter, and the generator never rewrites the facet to
        substitute a local class for it.
        """
        repository, package = u.Tests.create_lazy_init_workspace(
            tmp_path,
            project_name="flext-local",
            package_name="flext_local",
        )
        package.joinpath("constants.py").write_text(
            "class Parent:\n    class Domain:\n        pass\n"
            "c = Parent\n__all__ = ('Parent', 'c')\n",
            encoding=c.DEFAULT_ENCODING,
        )
        examples = repository / "examples"
        examples.mkdir()
        examples.joinpath("__init__.py").write_text("", encoding=c.DEFAULT_ENCODING)
        facet = examples / "constants.py"
        facet_source = (
            "from flext_local.constants import Parent\n"
            "class Local(Parent):\n    pass\n__all__ = ('Local',)\n"
        )
        facet.write_text(facet_source, encoding=c.DEFAULT_ENCODING)
        tm.that(u.Tests.run_lazy_init(repository), eq=0)
        # The facet declares no letter, so the generator leaves it untouched:
        # no runtime-alias repair may invent a local binding for one.
        tm.that(facet.read_text(encoding=c.DEFAULT_ENCODING), eq=facet_source)
        exports = u.Infra.public_export_names_source(
            examples.joinpath("__init__.py").read_text(encoding=c.DEFAULT_ENCODING),
        )
        tm.ok("c" in exports)
        probe = (
            "import examples as generated\n"
            "import examples.constants as local\n"
            "import flext_local.constants as parent\n"
            "print('c' in generated.__all__)\n"
            "print(generated.c is parent.c)\n"
            "print(generated.c is parent.Parent)\n"
            "print(generated.c is local.Local)\n"
            "print(all(hasattr(generated, name) for name in generated.__all__))\n"
        )
        tm.that(
            u.Tests.run_lazy_init_probe(
                probe,
                python_paths=(
                    str(repository),
                    str(repository / c.Infra.DEFAULT_SRC_DIR),
                    *sys.path,
                ),
                cwd=repository,
            ),
            eq=["True", "True", "True", "False", "True"],
        )
