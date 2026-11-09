"""Cold protocol publication uses source C3 and authenticated native effects.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from flext_infra.protocols_bootstrap import plan_protocol_facades
from tests import p, tm, u


class TestsColdProtocolPublication:
    """Exercise the documented source bootstrap against actual physical trees."""

    @staticmethod
    def _repository(tmp_path: Path) -> Path:
        root = tmp_path / "repository"
        package = root / "src/flext_infra"
        protocols = package / "_protocols"
        protocols.mkdir(parents=True)
        (root / "pyproject.toml").write_text(
            '[project]\nname="flext-infra"\n', encoding="utf-8"
        )
        (package / "__init__.py").touch()
        (package / "protocols.py").write_text(
            'raise RuntimeError("uninitialized target facade")\n', encoding="utf-8"
        )
        (protocols / "parent.py").write_text(
            "from typing import Protocol, runtime_checkable\n"
            "class FlextInfraProtocolsParent:\n"
            "    @runtime_checkable\n"
            "    class Receipt(Protocol):\n"
            "        @property\n        def root(self) -> str: ...\n",
            encoding="utf-8",
        )
        (protocols / "child.py").write_text(
            "from flext_infra._protocols.parent import "
            "FlextInfraProtocolsParent as Parent\n"
            "class FlextInfraProtocolsChild(Parent): pass\n",
            encoding="utf-8",
        )
        return root

    @staticmethod
    def _bootstrap(root: Path) -> p.Cli.CommandOutput:
        entrypoint = (
            Path(__file__).parents[3] / "src/flext_infra/protocols_bootstrap.py"
        )
        return tm.ok(
            u.Cli.run_raw(
                (sys.executable, "-P", str(entrypoint), str(root)),
                cwd=root,
                remove_env_keys=("PYTHONPATH",),
            )
        )

    @classmethod
    def test_cold_bootstrap_preserves_native_imports_and_is_idempotent(
        cls, tmp_path: Path
    ) -> None:
        """A broken target facade is repaired without executing it or shadowing Git."""
        root = cls._repository(tmp_path)
        first = cls._bootstrap(root)
        tm.ok(u.Cli.process_succeeded(first.outcome), msg=first.stderr)
        snapshots = {
            path: (path.stat().st_ino, path.read_bytes())
            for path in (root / "src").rglob("*.py")
        }
        second = cls._bootstrap(root)
        tm.ok(u.Cli.process_succeeded(second.outcome), msg=second.stderr)
        tm.that(
            {path: (path.stat().st_ino, path.read_bytes()) for path in snapshots},
            eq=snapshots,
        )
        consumer = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-P",
                    "-c",
                    (
                        "from pathlib import Path\n"
                        "from typing import is_protocol\n"
                        "from flext_infra.protocols import p\n"
                        "assert is_protocol(p.Infra.Receipt)\n"
                        "assert isinstance(Path.cwd(), p.Infra.Receipt)\n"
                        "assert p.Infra.__bases__[0].__name__ == "
                        "'FlextInfraProtocolsChild'\n"
                    ),
                ),
                cwd=root,
                env={**os.environ, "PYTHONPATH": str(root / "src")},
            )
        )
        tm.ok(u.Cli.process_succeeded(consumer.outcome), msg=consumer.stderr)

    @classmethod
    def test_input_changed_after_capture_rejects_before_publication(
        cls, tmp_path: Path
    ) -> None:
        """A real write between native capture and planning cannot be overwritten."""
        root = cls._repository(tmp_path)
        source = root / "src/flext_infra/_protocols/parent.py"
        facade = root / "src/flext_infra/protocols.py"
        before = facade.read_bytes()
        consumer = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-P",
                    "-c",
                    (
                        "import sys\nfrom pathlib import Path\n"
                        "from flext_infra._utilities.protocol_publication import "
                        "FlextInfraUtilitiesProtocolPublication\n"
                        f"root = Path({str(root)!r})\n"
                        f"source = Path({str(source)!r})\n"
                        "mutated = False\n"
                        "def change(event, args):\n"
                        "    global mutated\n"
                        "    if not mutated and event == 'compile' and "
                        "args[1] == str(source):\n"
                        "        mutated = True\n"
                        "        source.write_text(source.read_text() + '# observed "
                        "external edit\\n')\n"
                        "sys.addaudithook(change)\n"
                        "try:\n    FlextInfraUtilitiesProtocolPublication."
                        "publish_protocol_facades(root)\n"
                        "except ValueError as error:\n"
                        "    assert 'changed' in str(error)\n"
                        "else:\n    raise AssertionError('changed input was "
                        "accepted')\n"
                        "assert mutated\n"
                    ),
                ),
                cwd=root,
                remove_env_keys=("PYTHONPATH",),
            )
        )
        tm.ok(u.Cli.process_succeeded(consumer.outcome), msg=consumer.stderr)
        tm.that(facade.read_bytes(), eq=before)
        tm.ok(source.read_text().endswith("# observed external edit\n"))
        tm.ok(not (source.parent / "__init__.py").exists())

    @classmethod
    def test_c3_incompatibility_and_shadowing_fail_before_effects(
        cls, tmp_path: Path
    ) -> None:
        """A source graph authenticates imported bases and rejects impossible C3."""
        root = cls._repository(tmp_path)
        protocols = root / "src/flext_infra/_protocols"
        for name in ("First", "Second"):
            (protocols / f"{name.lower()}.py").write_text(
                f"class FlextInfraProtocols{name}: pass\n", encoding="utf-8"
            )
        for owner, bases in (
            ("Left", "FlextInfraProtocolsFirst, FlextInfraProtocolsSecond"),
            ("Right", "FlextInfraProtocolsSecond, FlextInfraProtocolsFirst"),
        ):
            (protocols / f"{owner.lower()}.py").write_text(
                "from flext_infra._protocols.first import FlextInfraProtocolsFirst\n"
                "from flext_infra._protocols.second import FlextInfraProtocolsSecond\n"
                f"class FlextInfraProtocols{owner}({bases}): pass\n",
                encoding="utf-8",
            )
        before = {path: path.read_bytes() for path in (root / "src").rglob("*.py")}
        with u.Tests.raises(ValueError, match="inconsistent C3"):
            plan_protocol_facades(root)
        tm.that({path: path.read_bytes() for path in before}, eq=before)
        (protocols / "left.py").unlink()
        (protocols / "right.py").unlink()
        child = protocols / "child.py"
        child.write_text(
            child.read_text().replace(
                "class FlextInfraProtocolsChild",
                "Parent = object\nclass FlextInfraProtocolsChild",
            ),
            encoding="utf-8",
        )
        with u.Tests.raises(ValueError, match="authenticated runtime declaration"):
            plan_protocol_facades(root)
