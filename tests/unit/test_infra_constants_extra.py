"""Tests for flext_infra.constants — Check, Github, Encoding, alias, and consistency.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import hashlib
import inspect
import sys
from pathlib import Path

from flext_infra import config
from tests import c, m, tm, u


class TestsFlextInfraConstantsInfraExtra:
    """Tests for Check namespace constants."""

    @staticmethod
    def test_projection_executes_actual_source_artifact(tmp_path: Path) -> None:
        """The real source artifact executes with its public contracts intact."""
        package = Path(inspect.getfile(c)).parent
        staged = tmp_path / package.name
        projected = tm.not_none(u.Infra.render_utility_facade(package, family="c"))
        for path in package.rglob("*.py"):
            tm.ok(
                u.Cli.atomic_write_text_file(
                    staged / path.relative_to(package), path.read_text(encoding="utf-8")
                )
            )
        tm.ok(u.Cli.atomic_write_text_file(staged / "constants.py", projected))
        digest = hashlib.sha256(projected.encode()).hexdigest()
        output = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    (
                        "import hashlib, inspect\nfrom pathlib import Path\n"
                        "from flext_infra import c\n"
                        "artifact = Path(inspect.getfile(c))\n"
                        f"assert artifact == Path({str(staged / 'constants.py')!r}), "
                        "str(artifact)\n"
                        "assert {'c', 't', 'm', 'p', 'u'} <= "
                        "set(c.Infra.ALIAS_NAMES), sorted(c.Infra.ALIAS_NAMES)\n"
                        "assert c.Infra.PytestExecutionMode.FULL == 'full'\n"
                        "assert c.Infra.MergeConflictControl.SEPARATOR == '======='\n"
                        "assert c.Infra.compile('contract').fullmatch('contract')\n"
                        "print(hashlib.sha256(artifact.read_bytes()).hexdigest())\n"
                    ),
                ),
                cwd=tmp_path,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(tmp_path)}),
            )
        )
        tm.that(u.Cli.process_succeeded(output.outcome), eq=True, msg=output.stderr)
        tm.that(output.stdout.strip(), eq=digest)

    @staticmethod
    def test_projection_preserves_c3_after_base_detachment(tmp_path: Path) -> None:
        """Declared owners retain real class dispatch without a reverse base import."""
        root, package = u.Tests.create_lazy_init_workspace(tmp_path)
        directory = u.Infra.facade_family_declared_by(c.Infra.CONSTANTS_PY).directory
        sources = {
            package / "__init__.py": (
                f"from {package.name}.constants import Constants, c\n"
                "__all__ = ['Constants', 'c']\n"
            ),
            package / directory / "__init__.py": (
                "from .base import Base\nfrom .shared import Shared\n"
                "from .make import Make\nfrom .source import Source\n"
                "__all__ = ['Base', 'Shared', 'Make', 'Source']\n"
            ),
            package / directory / "shared.py": (
                "class Shared:\n    marker = 'shared'\n"
                "    @classmethod\n    def dispatch(cls):\n        return cls.marker\n"
                "__all__ = ['Shared']\n"
            ),
            package / directory / "make.py": (
                "class Make:\n    command = 'declared'\n__all__ = ['Make']\n"
            ),
            package / directory / "source.py": (
                "class Source:\n    marker = 'source'\n"
                "    class Token:\n        pass\n__all__ = ['Source']\n"
            ),
            package / directory / "base.py": (
                f"from {package.name}.{directory}.shared import Shared\n"
                f"from {package.name}.{directory}.make import Make\n"
                f"from {package.name}.{directory}.source import Source\n"
                "class Base(Shared, Make, Source):\n    local = 'base'\n"
                "__all__ = ['Base']\n"
            ),
            package / "constants.py": (
                f"from {package.name}.{directory}.base import Base\n"
                f"from {package.name}.{directory}.source import Source\n"
                "class Constants:\n    class Domain(Base, Source):\n        pass\n"
                "c = Constants\n__all__ = ['Constants', 'c']\n"
            ),
        }
        for path, source in sources.items():
            tm.ok(u.Cli.atomic_write_text_file(path, source))
        projected = tm.not_none(u.Infra.render_utility_facade(package, family="c"))
        tm.ok(u.Cli.atomic_write_text_file(package / "constants.py", projected))
        tm.ok(
            u.Cli.atomic_write_text_file(
                package / directory / "base.py",
                "class Base:\n    local = 'base'\n__all__ = ['Base']\n",
            )
        )
        output = tm.ok(
            u.Cli.run_raw(
                (
                    sys.executable,
                    "-c",
                    (
                        f"from {package.name} import c\n"
                        f"from {package.name}.{directory}.source import Source\n"
                        "assert c.Domain.dispatch() == 'shared'\n"
                        "assert c.Domain.command == 'declared'\n"
                        "assert c.Domain.local == 'base'\n"
                        "assert c.Domain.Token is Source.Token\n"
                        "assert [base.__name__ for base in c.Domain.__mro__]"
                        ".count('Domain') == 1\n"
                        "print(c.__module__)\n"
                    ),
                ),
                cwd=root,
                options=m.Cli.ProcessOptions(env={"PYTHONPATH": str(package.parent)}),
            )
        )
        tm.that(u.Cli.process_succeeded(output.outcome), eq=True, msg=output.stderr)
        tm.that(output.stdout.strip(), eq=f"{package.name}.constants")
        tm.that(u.Infra.render_utility_facade(package, family="c"), eq=projected)

    @staticmethod
    def test_github_constants_are_strings() -> None:
        """Test github constants are strings."""
        tm.that(c.Infra.GITHUB_REPO_URL, is_=str)
        tm.that(c.Infra.GITHUB_REPO_NAME, is_=str)

    @staticmethod
    def test_encoding_constant_is_string() -> None:
        """Test encoding constant is string."""
        tm.that(c.Infra.ENCODING_DEFAULT, is_=str)

    @staticmethod
    def test_c_alias_is_string() -> None:
        """Test c alias is string."""
        tm.that(c, is_=type)

    @staticmethod
    def test_excluded_dirs_are_immutable() -> None:
        """Test excluded dirs are immutable."""
        excluded = config.Infra.codegen.analysis_excluded_dirs
        tm.that(excluded, is_=tuple)

    @staticmethod
    def test_all_status_values_are_uppercase() -> None:
        """Test all status values are uppercase."""
        tm.ok(c.Infra.ResultStatus.PASSED.isupper())
        tm.ok(c.Infra.ResultStatus.FAIL.isupper())
        tm.ok(c.Infra.ResultStatus.OK.isupper())
        tm.ok(c.Infra.ResultStatus.WARN.isupper())

    @staticmethod
    def test_all_gate_values_are_lowercase() -> None:
        """Test all gate values are lowercase."""
        gates = [
            c.Infra.LINT,
            c.Infra.FORMAT,
            c.Infra.PYREFLY,
            c.Infra.MYPY,
            c.Infra.PYRIGHT,
            c.Infra.SECURITY,
            c.Infra.MARKDOWN,
        ]
        for gate in gates:
            tm.that(gate.islower(), eq=True, msg=f"Gate {gate} should be lowercase")

    @staticmethod
    def test_excluded_dirs_no_duplicates() -> None:
        """Test excluded dirs no duplicates."""
        common = config.Infra.codegen.analysis_excluded_dirs
        doc = config.Infra.codegen.docs_excluded_dirs
        tm.that(len(common), eq=len(set(common)))
        tm.that(len(doc), eq=len(set(doc)))
