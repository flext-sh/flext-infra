"""Authored transport for the profiled pytest child processes.

The bootstrap, startup and launcher behaviors own the parent-free child
transport: every payload resolves the clock and this module from their
installed files without importing the parent package, keeping framework
imports out of measured child startup. The check constants render their
``python -c`` payloads from this module, so the transport cannot drift
from this single authored source.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

import atexit
import cProfile
import os
import runpy
import sys
from importlib.machinery import PathFinder
from importlib.util import find_spec, module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType
from typing import ClassVar


class FlextInfraPytestProfileChild:
    """Own the bootstrap, startup handoff and launcher of profiled children."""

    CLOCK_MODULE: ClassVar[str] = "flext_infra._pytest_clock"
    CHILD_ROOT_ENV: ClassVar[str] = "FLEXT_PYTEST_PROFILE_CHILD_ROOT"
    PROCESS_DIRECTORY_ENV: ClassVar[str] = "FLEXT_PYTEST_PROFILE_PROCESS_DIRECTORY"

    @classmethod
    def load_clock(cls) -> ModuleType:
        """Resolve the clock module from its installed file, parent-free.

        Returns:
            The imported clock owner module.

        Raises:
            ModuleNotFoundError: If the package origin is unresolved.
            ImportError: If the clock file has no executable loader.

        """
        clock = sys.modules.get(cls.CLOCK_MODULE)
        if clock is not None:
            return clock
        package = find_spec(cls.CLOCK_MODULE.split(".", 1)[0])
        if package is None or package.origin is None:
            raise ModuleNotFoundError(cls.CLOCK_MODULE)
        clock_path = Path(package.origin).with_name(
            cls.CLOCK_MODULE.rsplit(".", 1)[1] + ".py"
        )
        clock_spec = spec_from_file_location(cls.CLOCK_MODULE, clock_path)
        if clock_spec is None or clock_spec.loader is None:
            raise ImportError(cls.CLOCK_MODULE)
        clock = module_from_spec(clock_spec)
        sys.modules[cls.CLOCK_MODULE] = clock
        clock_spec.loader.exec_module(clock)
        return clock

    @classmethod
    def bootstrap(cls) -> tuple[ModuleType, cProfile.Profile]:
        """Start the shared process profiler after resolving the clock.

        Returns:
            The clock module and the active process profiler.

        """
        clock = cls.load_clock()
        return clock, clock.FlextInfraPytestClock.start_profiler()

    @classmethod
    def startup(cls, sitecustomize: str) -> None:
        """Run the profiled sitecustomize handoff for one descendant process.

        Args:
            sitecustomize: The stub file path owning the startup directory.

        """
        clock = cls.load_clock()
        profile = clock.FlextInfraPytestClock.start_profiler()
        output = Path(os.environ[cls.CHILD_ROOT_ENV])
        profile_output = output / f"{os.getpid()}.pstats"
        entry_index = len(sys.orig_argv) - len(sys.argv)
        native_profile = (
            sys.argv[:1] == ["-m"]
            and entry_index >= 1
            and sys.orig_argv[entry_index - 1 : entry_index + 1] == ["-m", "cProfile"]
        )
        if not native_profile:
            clock.FlextInfraPytestClock.register_signal_checkpoint(
                profile,
                profile_output,
            )
            atexit.register(
                clock.FlextInfraPytestClock.publish_profile,
                profile,
                profile_output,
            )
        startup = str(Path(sitecustomize).parent)
        original = PathFinder.find_spec(
            "sitecustomize",
            [path for path in sys.path if path != startup],
        )
        if original is not None and original.loader is not None:
            module = module_from_spec(original)
            sys.modules["sitecustomize"] = module
            original.loader.exec_module(module)
        if native_profile:
            clock.FlextInfraPytestClock.publish_profile(profile, profile_output)
            profile.disable()

    @classmethod
    def launcher(cls) -> None:
        """Run pytest under this process profile and publish its artifact.

        The launcher enables run-owned startup instrumentation for
        descendants, including pytester children, while still executing the
        existing site customization. Pytest installs assertion rewriting
        before any plugin package is imported; its ``SystemExit`` still sets
        the native exit status.

        """
        clock, profile = cls.bootstrap()
        output = Path(sys.argv.pop(1))
        clock.FlextInfraPytestClock.register_signal_checkpoint(profile, output)
        try:
            directory = os.environ.get(cls.PROCESS_DIRECTORY_ENV)
            if directory is not None:
                children = output.resolve().parent / directory
                startup = children / "startup"
                startup.mkdir(parents=True, exist_ok=True)
                (startup / "sitecustomize.py").write_text(
                    cls.startup_stub(),
                    encoding="utf-8",
                )
                inherited = os.environ.get("PYTHONPATH", "")
                previous = os.environ.get(cls.CHILD_ROOT_ENV)
                if previous is not None:
                    previous_startup = str(Path(previous) / "startup")
                    inherited = os.pathsep.join(
                        path
                        for path in inherited.split(os.pathsep)
                        if path != previous_startup
                    )
                os.environ[cls.CHILD_ROOT_ENV] = str(children)
                os.environ["PYTHONPATH"] = str(startup) + (
                    os.pathsep + inherited if inherited else ""
                )
            runpy.run_module("pytest", run_name="__main__", alter_sys=True)
        finally:
            clock.FlextInfraPytestClock.publish_profile(profile, output)

    @classmethod
    def bootstrap_stub(cls) -> str:
        """Render the ``python -c`` payload binding ``clock`` and ``profile``.

        Returns:
            The parent-free stub leaving the clock and profiler bound.

        """
        return cls._stub(
            f"clock, profile = child.{cls.__name__}.{cls.bootstrap.__name__}()",
        )

    @classmethod
    def startup_stub(cls) -> str:
        """Render the descendant ``sitecustomize`` payload.

        Returns:
            The parent-free stub invoking the startup handoff.

        """
        return cls._stub(f"child.{cls.__name__}.{cls.startup.__name__}(__file__)")

    @classmethod
    def launcher_stub(cls) -> str:
        """Render the profiled ``python -c`` pytest launcher payload.

        Returns:
            The parent-free stub invoking the canonical launcher, whose
            first argument is the output profile artifact.

        """
        return cls._stub(f"child.{cls.__name__}.{cls.launcher.__name__}()")

    @classmethod
    def _stub(cls, call: str) -> str:
        """Render the parent-free child loader invoking ``call``.

        Args:
            call: The child invocation appended to the rendered loader.

        Returns:
            The complete ``python -c`` payload text.

        """
        package = __name__.rpartition(".")[0]
        filename = f"{__name__.rpartition('.')[2]}.py"
        return (
            "import sys\n"
            "from pathlib import Path\n"
            "from importlib.util import find_spec, module_from_spec, "
            "spec_from_file_location\n"
            f"package = find_spec({package!r})\n"
            "if package is None or package.origin is None:\n"
            f"    raise ModuleNotFoundError({__name__!r})\n"
            f"child_path = Path(package.origin).with_name({filename!r})\n"
            f"spec = spec_from_file_location({__name__!r}, child_path)\n"
            "if spec is None or spec.loader is None:\n"
            f"    raise ImportError({__name__!r})\n"
            "child = module_from_spec(spec)\n"
            "sys.modules[spec.name] = child\n"
            "spec.loader.exec_module(child)\n"
            f"{call}\n"
        )


__all__: list[str] = ["FlextInfraPytestProfileChild"]
