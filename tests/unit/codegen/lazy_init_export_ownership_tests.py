"""Public owner boundaries, collisions and native identity of lazy-init exports.

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
from collections.abc import Sequence
from pathlib import Path

import pytest

from tests import c, tm, u


class TestsFlextInfraLazyInitOwnership:
    """Validate public owner boundaries, collisions and native identity."""

    @staticmethod
    def test_root_rejects_symbols_from_deep_descendant_packages(
        tmp_path: Path,
    ) -> None:
        """Keep deeply nested declarations behind their package facade."""
        repository_root, package_root = u.Tests.demo_lazy_init_workspace(tmp_path)
        deep_dir = package_root / "services" / "http"
        deep_dir.mkdir(parents=True)
        (package_root / "services" / c.Infra.INIT_PY).write_text(
            "",
            encoding=c.DEFAULT_ENCODING,
        )
        deep_dir.joinpath(c.Infra.INIT_PY).write_text(
            "",
            encoding=c.DEFAULT_ENCODING,
        )
        deep_dir.joinpath("transport.py").write_text(
            "from __future__ import annotations\n\n"
            "class FlextDemoHttpTransport:\n"
            "    pass\n\n"
            '__all__: list[str] = ["FlextDemoHttpTransport"]\n',
            encoding=c.DEFAULT_ENCODING,
        )

        tm.that(u.Tests.run_lazy_init(repository_root), eq=0)
        exports_content = u.Tests.generated_init(package_root)

        tm.that(exports_content, lacks="FlextDemoHttpTransport")
        tm.that(exports_content, has='"services"')
        tm.that(
            u.Tests.run_lazy_init_probe(
                "import flext_demo\n"
                "from flext_demo import services\n"
                "from flext_demo.services import http\n"
                "from flext_demo.services.http import FlextDemoHttpTransport\n"
                "from flext_demo.services.http.transport import "
                "FlextDemoHttpTransport as owner\n"
                "from flext_tests import tm\n"
                "assert services is flext_demo.services\n"
                "assert http is services.http\n"
                "assert FlextDemoHttpTransport is owner\n"
                "try:\n    from flext_demo import FlextDemoHttpTransport\n"
                "except ImportError:\n    print('deep root export rejected')\n"
                "else:\n    tm.reject('deep owner widened root API')\n"
                "print('owning package identity preserved')\n",
                python_paths=(str(repository_root / "src"), *sys.path),
                cwd=repository_root,
            ),
            eq=["deep root export rejected", "owning package identity preserved"],
        )
        tm.that(u.Tests.run_lazy_init(repository_root, check_only=True), eq=0)
        tm.that(
            u.Tests.generated_init(package_root),
            eq=exports_content,
        )

    @staticmethod
    def test_independent_packages_accept_same_export_name_without_warnings(
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """A public name belongs to its package, not a workspace-wide census."""
        repository_root, package_root = u.Tests.demo_lazy_init_workspace(tmp_path)
        other_package = package_root.with_name("independent_package")
        other_package.mkdir()
        other_package.joinpath(c.Infra.INIT_PY).write_text(
            "",
            encoding=c.DEFAULT_ENCODING,
        )
        for package in (package_root, other_package):
            package.joinpath("holder.py").write_text(
                "class SharedPackageDeclaration:\n    pass\n\n"
                '__all__ = ["SharedPackageDeclaration"]\n',
                encoding=c.DEFAULT_ENCODING,
            )

        tm.that(u.Tests.run_lazy_init(repository_root), eq=0)
        tm.that(u.Tests.run_lazy_init(repository_root, check_only=True), eq=0)
        captured = capsys.readouterr()
        tm.that(captured.out + captured.err, lacks="WARN:")

    @staticmethod
    def test_unpublished_module_homonyms_do_not_compete_for_exports(
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
    ) -> None:
        """Independent implementation declarations need no global renaming."""
        repository_root, package_root = u.Tests.demo_lazy_init_workspace(tmp_path)
        for module in ("first", "second"):
            package_root.joinpath(f"{module}.py").write_text(
                "class ModuleLocalDeclaration:\n    pass\n\n__all__: list[str] = []\n",
                encoding=c.DEFAULT_ENCODING,
            )

        tm.that(u.Tests.run_lazy_init(repository_root), eq=0)
        tm.that(u.Tests.run_lazy_init(repository_root, check_only=True), eq=0)
        captured = capsys.readouterr()
        tm.that(captured.out + captured.err, lacks="WARN:")

    @staticmethod
    @pytest.mark.parametrize("export_names", [("Shared",), ("Shared", "Other")])
    def test_duplicate_public_export_fails_before_generation(
        tmp_path: Path,
        capsys: pytest.CaptureFixture[str],
        export_names: Sequence[str],
    ) -> None:
        """Two owners of one public name stop the phase before any file plan.

        Both modules declare the same public name, so nothing can decide which
        one owns it. Picking the first, the last, or merging them would make
        the disagreement invisible exactly where it matters, so planning
        refuses and names the collision instead of generating a facade.
        """
        repository_root, package_root = u.Tests.demo_lazy_init_workspace(tmp_path)
        before = u.Tests.generated_init(package_root)
        for index, name in enumerate(export_names):
            owner_dir = package_root if index == 0 else package_root / name.lower()
            if owner_dir != package_root:
                owner_dir.mkdir()
                (owner_dir / c.Infra.INIT_PY).write_bytes(b"")
            for module_name in ("api", "service"):
                (owner_dir / f"{module_name}.py").write_text(
                    "from __future__ import annotations\n\n"
                    f"class {name}:\n    pass\n\n"
                    f"__all__: list[str] = [{name!r}]\n",
                    encoding=c.DEFAULT_ENCODING,
                )
        initializers = tuple(package_root.rglob(c.Infra.INIT_PY))
        original_bytes = tuple(path.read_bytes() for path in initializers)

        planned = u.Tests.create_lazy_init_service(repository_root).plan_files()

        tm.fail(planned, has="ambiguous")
        tm.that(str(planned.error), has=f"{len(export_names)} collision(s)")
        captured = capsys.readouterr()
        for name in export_names:
            tm.that(captured.out + captured.err, has=f"export collision for {name!r}")
        tm.that(tuple(path.read_bytes() for path in initializers), eq=original_bytes)
        # The refusal is PRE-EFFECT: the facade on disk is untouched and never
        # gained the contested name.
        after = u.Tests.generated_init(package_root)
        tm.that(after, eq=before)
        tm.that(after, lacks="Shared")

    @staticmethod
    def test_duplicate_facade_letter_fails_before_generation(
        tmp_path: Path,
    ) -> None:
        """Two same-level owners of one facade letter stop pre-effect.

        The letter channel is governed exactly like every public name: when two
        modules of one package both declare the same letter, nothing can decide
        which one owns it, so planning refuses loudly and names the collision
        instead of silently electing a winner behind the disagreement.
        """
        repository_root, package_root = u.Tests.demo_lazy_init_workspace(tmp_path)
        before = u.Tests.generated_init(package_root)
        for module_name, class_name in (
            ("constants", "AlphaConstants"),
            ("culture", "CultureConstants"),
        ):
            (package_root / f"{module_name}.py").write_text(
                "from __future__ import annotations\n\n"
                f"class {class_name}:\n    pass\n\n"
                f"c = {class_name}\n\n"
                f'__all__: list[str] = ["{class_name}", "c"]\n',
                encoding=c.DEFAULT_ENCODING,
            )

        planned = u.Tests.create_lazy_init_service(repository_root).plan_files()

        tm.fail(planned, has="ambiguous")
        # The refusal is PRE-EFFECT: no facade gains either contested owner.
        after = u.Tests.generated_init(package_root)
        tm.that(after, eq=before)
        tm.that(after, lacks="AlphaConstants")
        tm.that(after, lacks="CultureConstants")
        tm.that(after, lacks='"c"')

    @staticmethod
    @pytest.mark.parametrize(
        "modules",
        [("holder_part_01", "holder_part_99"), ("api", "_api")],
    )
    def test_legacy_filename_shapes_do_not_authenticate_competing_owners(
        tmp_path: Path, modules: tuple[str, str]
    ) -> None:
        """Old filenames never make distinct declarations reexports."""
        repository, package = u.Tests.demo_lazy_init_workspace(tmp_path)
        before = u.Tests.generated_init(package)
        for module in modules:
            (package / f"{module}.py").write_text(
                "class Shared:\n    pass\n\n__all__ = ['Shared']\n",
                encoding=c.DEFAULT_ENCODING,
            )

        tm.fail(
            u.Tests.create_lazy_init_service(repository).plan_files(), has="ambiguous"
        )
        tm.that(u.Tests.generated_init(package), eq=before)

    @staticmethod
    def test_nested_facade_publishes_private_children_root_withholds_them(
        tmp_path: Path,
    ) -> None:
        """A nested package publishes its ``_x`` children; the facade root does not.

        Operator ruling 2026-10-24: export what ``__all__`` holds. Only the
        public facade root withholds private children and their exports.
        """
        repository, package = u.Tests.demo_lazy_init_workspace(tmp_path)
        domain = package / "_runtime"
        records = domain / "_records"
        records.mkdir(parents=True)
        (records / "owner.py").write_text(
            "class RecordOwner:\n"
            "    class Record:\n        marker = 'native'\n\n"
            "__all__ = ['RecordOwner']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        facade_source = (
            "from ._records.owner import RecordOwner\n\n"
            "class RuntimeFacade(RecordOwner):\n    pass\n\n"
            "def encode(value: str) -> str:\n    return value\n\n"
            "type Payload = tuple[str, int]\n\n"
        )
        (domain / "facade.py").write_text(
            facade_source + "__all__ = ['RuntimeFacade', 'encode', 'Payload']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        (package / "runtime.py").write_text(
            "from ._runtime.facade import Payload, RuntimeFacade, encode\n\n"
            "__all__ = ['RuntimeFacade', 'encode', 'Payload']\n",
            encoding=c.DEFAULT_ENCODING,
        )

        tm.that(u.Tests.run_lazy_init(repository), eq=0)
        tm.that(
            u.Tests.generated_init(domain),
            has='"RecordOwner": "._records.owner"',
        )
        tm.that(u.Tests.generated_init(domain), lacks='"_records": "._records"')
        tm.that(u.Tests.generated_init(package), lacks=["RecordOwner", "_runtime"])
        tm.that(
            u.Tests.run_lazy_init_probe(
                f"import {package.name} as public\n"
                f"from {package.name}._runtime import RecordOwner\n"
                f"from {package.name}._runtime._records.owner "
                "import RecordOwner as implementation\n"
                "print(public.RuntimeFacade.Record.marker)\n"
                "print(public.encode('payload'))\n"
                "print(public.encode.__module__ == "
                f"'{package.name}._runtime.facade')\n"
                "print(public.Payload.__module__ == "
                f"'{package.name}._runtime.facade')\n"
                "print(public.Payload.__value__ == tuple[str, int])\n"
                "print('RecordOwner' not in public.__all__)\n"
                "print(RecordOwner is implementation)\n",
                python_paths=(str(package.parent),),
                cwd=repository,
            ),
            eq=["native", "payload", "True", "True", "True", "True", "True"],
        )
        initializers = tuple(package.rglob(c.Infra.INIT_PY))
        before = tuple(path.read_bytes() for path in initializers)
        tm.that(u.Tests.run_lazy_init(repository), eq=0)
        tm.that(u.Tests.run_lazy_init(repository, check_only=True), eq=0)
        tm.that(tuple(path.read_bytes() for path in initializers), eq=before)

        # Explicit publication changes the private facade's contract, not
        # the identity of the implementation owner or a public homonym.
        (domain / "facade.py").write_text(
            facade_source
            + "__all__ = ['RuntimeFacade', 'encode', 'Payload', 'RecordOwner']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        (package / "records.py").write_text(
            "class RecordOwner:\n    marker = 'public'\n\n__all__ = ['RecordOwner']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        tm.that(u.Tests.run_lazy_init(repository), eq=0)
        tm.that(
            u.Tests.run_lazy_init_probe(
                f"import {package.name} as public\n"
                f"from {package.name}._runtime import RecordOwner as private_owner\n"
                f"from {package.name}._runtime import RuntimeFacade\n"
                f"from {package.name}._runtime._records.owner "
                "import RecordOwner as implementation\n"
                f"from {package.name}.records import RecordOwner as declared\n"
                "print(private_owner is implementation)\n"
                "print(public.RecordOwner is declared)\n"
                "print(public.RecordOwner is not private_owner)\n"
                "print(public.RecordOwner.marker)\n"
                "print(implementation in RuntimeFacade.__mro__)\n",
                python_paths=(str(package.parent),),
                cwd=repository,
            ),
            eq=["True", "True", "True", "public", "True"],
        )
        before = tuple(path.read_bytes() for path in initializers)
        tm.that(u.Tests.run_lazy_init(repository), eq=0)
        tm.that(u.Tests.run_lazy_init(repository, check_only=True), eq=0)
        tm.that(tuple(path.read_bytes() for path in initializers), eq=before)

    @staticmethod
    @pytest.mark.parametrize(
        "modules",
        [("holder_part_99", "holder_part_01"), ("foundation", "runtime")],
    )
    def test_native_introducing_subclass_owns_composed_behavior(
        tmp_path: Path, modules: tuple[str, str]
    ) -> None:
        """Ancestry elects the facade independently of legacy numbering."""
        repository, package = u.Tests.demo_lazy_init_workspace(tmp_path)
        original, facade = modules
        (package / f"{original}.py").write_text(
            "class Shared:\n"
            "    marker = 'initial'\n"
            "    def read(self) -> str:\n        return self.marker\n\n"
            "__all__ = ['Shared']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        (package / f"{facade}.py").write_text(
            f"from .{original} import Shared as SharedBase\n\n"
            "class Shared(SharedBase):\n    marker = 'composed'\n\n"
            "__all__ = ['Shared']\n",
            encoding=c.DEFAULT_ENCODING,
        )

        tm.that(u.Tests.run_lazy_init(repository), eq=0)
        tm.that(
            u.Tests.run_lazy_init_probe(
                f"from {package.name} import Shared\n"
                "print(Shared().read())\n"
                f"print(Shared.__module__ == '{package.name}.{facade}')\n",
                python_paths=(str(package.parent),),
                cwd=repository,
            ),
            eq=["composed", "True"],
        )
        tm.that(u.Tests.run_lazy_init(repository, check_only=True), eq=0)
