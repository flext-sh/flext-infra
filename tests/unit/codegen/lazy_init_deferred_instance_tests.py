"""Declared configuration roots are deferred to their first attribute read.

A project declares the configuration roots whose validation is costly; the
generated initializer publishes each as a stand-in, so importing the package
(and every module that imports the root from it) validates no configuration,
while the first attribute read validates and fails exactly as an eager import.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import sys
from pathlib import Path

from tests import c, tm, u


class TestsFlextInfraCodegenLazyInitDeferredInstance:
    """The initializer defers a declared root that requires absent settings."""

    @staticmethod
    def _workspace(tmp_path: Path) -> tuple[Path, Path]:
        """Create a package whose settings require an environment value.

        Returns:
            The repository root and its package directory.

        """
        repository, package = u.Tests.create_lazy_init_workspace(tmp_path)
        package.joinpath("demo_settings.py").write_text(
            "from pydantic_settings import BaseSettings, SettingsConfigDict\n\n"
            "class DemoSettings(BaseSettings):\n"
            '    """Settings with a required value and no source."""\n\n'
            "    model_config = SettingsConfigDict(\n"
            "        env_prefix='FLEXT_DEFERRED_INSTANCE_ABSENT_'\n"
            "    )\n"
            "    raiz: str\n\n"
            "settings = DemoSettings()\n"
            "__all__ = ['DemoSettings', 'settings']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        package.joinpath("api.py").write_text(
            f"from {package.name} import settings\n\n"
            "class DemoApi:\n"
            '    """Reads its settings only when used."""\n\n'
            "    source = settings\n\n"
            "__all__ = ['DemoApi']\n",
            encoding=c.DEFAULT_ENCODING,
        )
        return repository, package

    def test_declared_root_imports_without_validating(self, tmp_path: Path) -> None:
        """Import validates nothing; the first read raises the ValidationError."""
        repository, package = self._workspace(tmp_path)
        u.Tests.override_repository_declaration(
            repository, {"deferred_instances": ["settings"]}
        )
        tm.that(u.Tests.run_lazy_init(repository), eq=0)
        tm.that(u.Tests.run_lazy_init(repository, check_only=True), eq=0)
        tm.that(
            u.Tests.generated_init(package),
            has=(
                "defer_lazy_instances(\n"
                "    __name__,\n"
                "    globals(),\n"
                '    {"settings": ".demo_settings"},\n'
                '    ("settings",),\n'
                ")\n"
            ),
        )
        tm.that(
            u.Tests.run_lazy_init_probe(
                "import pydantic\n"
                f"import {package.name}.api as api\n"
                "print('imported')\n"
                "try:\n"
                "    api.DemoApi.source.raiz\n"
                "except pydantic.ValidationError as error:\n"
                "    print(type(error).__name__, error.errors()[0]['loc'])\n",
                python_paths=(str(package.parent), *sys.path),
                cwd=repository,
            ),
            eq=["imported", "ValidationError ('raiz',)"],
        )

    def test_undeclared_root_stays_a_plain_lazy_export(self, tmp_path: Path) -> None:
        """Without a declaration the initializer emits no deferral."""
        repository, package = self._workspace(tmp_path)
        tm.that(u.Tests.run_lazy_init(repository), eq=0)
        tm.that(u.Tests.generated_init(package), lacks="defer_lazy_instances")

    def test_declared_root_exported_nowhere_fails(self, tmp_path: Path) -> None:
        """A declared root no initializer exports fails generation loud."""
        repository, _package = self._workspace(tmp_path)
        u.Tests.override_repository_declaration(
            repository, {"deferred_instances": ["absent_root"]}
        )
        tm.fail(
            u.Tests.create_lazy_init_service(repository).plan_files(),
            has="exported by no initializer",
        )
