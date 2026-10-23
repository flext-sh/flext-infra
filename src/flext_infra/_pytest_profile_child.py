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
import traceback
from collections.abc import Callable
from importlib.machinery import PathFinder
from importlib.util import find_spec, module_from_spec, spec_from_file_location
from pathlib import Path
from types import ModuleType
from typing import ClassVar


class FlextInfraPytestProfileChild:
    """Own the bootstrap, startup handoff and launcher of profiled children.

    The parent's check constants own the clock module and environment names
    and inject them into every rendered payload, so this parent-free transport
    declares no names of its own.
    """

    _startup_retire: ClassVar[Callable[[], None] | None] = None

    @staticmethod
    def load_clock(clock_module: str) -> ModuleType:
        """Resolve the clock module from its installed file, parent-free.

        Returns:
            The imported clock owner module.

        Raises:
            ModuleNotFoundError: If the package origin is unresolved.
            ImportError: If the clock file has no executable loader.

        """
        clock = sys.modules.get(clock_module)
        if clock is not None:
            return clock
        package = find_spec(clock_module.split(".", 1)[0])
        if package is None or package.origin is None:
            raise ModuleNotFoundError(clock_module)
        clock_path = Path(package.origin).with_name(
            clock_module.rsplit(".", 1)[1] + ".py"
        )
        clock_spec = spec_from_file_location(clock_module, clock_path)
        if clock_spec is None or clock_spec.loader is None:
            raise ImportError(clock_module)
        clock = module_from_spec(clock_spec)
        sys.modules[clock_module] = clock
        clock_spec.loader.exec_module(clock)
        return clock

    @classmethod
    def bootstrap(cls, clock_module: str) -> tuple[ModuleType, cProfile.Profile]:
        """Start the shared process profiler after resolving the clock.

        Returns:
            The clock module and the active process profiler.

        """
        clock = cls.load_clock(clock_module)
        return clock, clock.FlextInfraPytestClock.start_profiler()

    @classmethod
    def startup(
        cls, sitecustomize: str, clock_module: str, child_root_env: str
    ) -> None:
        """Run the profiled sitecustomize handoff for one descendant process.

        Args:
            sitecustomize: The stub file path owning the startup directory.
            clock_module: The injected clock module name.
            child_root_env: The injected descendant profile root variable.

        """
        clock = cls.load_clock(clock_module)
        profile = clock.FlextInfraPytestClock.start_profiler()
        output = Path(os.environ[child_root_env])
        profile_output = output / f"{os.getpid()}.pstats"
        entry_index = len(sys.orig_argv) - len(sys.argv)
        native_profile = (
            sys.argv[:1] == ["-m"]
            and entry_index >= 1
            and sys.orig_argv[entry_index - 1 : entry_index + 1] == ["-m", "cProfile"]
        )
        if not native_profile:
            cls._startup_retire = (
                clock.FlextInfraPytestClock.register_signal_checkpoint(
                    profile,
                    profile_output,
                )
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
    def launcher(
        cls, clock_module: str, child_root_env: str, process_directory_env: str
    ) -> None:
        """Run pytest under this process profile and publish its artifact.

        The launcher enables run-owned startup instrumentation for
        descendants, including pytester children, while still executing the
        existing site customization. Pytest installs assertion rewriting
        before any plugin package is imported; its ``SystemExit`` still sets
        the native exit status.

        Args:
            clock_module: The injected clock module name.
            child_root_env: The injected descendant profile root variable.
            process_directory_env: The injected descendant directory variable.

        """
        clock, profile = cls.bootstrap(clock_module)
        output = Path(sys.argv.pop(1))
        if cls._startup_retire is not None:
            atexit.unregister(clock.FlextInfraPytestClock.publish_profile)
            cls._startup_retire()
            cls._startup_retire = None
        retire = clock.FlextInfraPytestClock.register_signal_checkpoint(profile, output)
        try:
            directory = os.environ.get(process_directory_env)
            if directory is not None:
                children = output.resolve().parent / directory
                startup = children / "startup"
                startup.mkdir(parents=True, exist_ok=True)
                (startup / "sitecustomize.py").write_text(
                    cls.startup_stub(clock_module, child_root_env),
                    encoding="utf-8",
                )
                inherited = os.environ.get("PYTHONPATH", "")
                previous = os.environ.get(child_root_env)
                if previous is not None:
                    previous_startup = str(Path(previous) / "startup")
                    inherited = os.pathsep.join(
                        path
                        for path in inherited.split(os.pathsep)
                        if path != previous_startup
                    )
                os.environ[child_root_env] = str(children)
                os.environ["PYTHONPATH"] = str(startup) + (
                    os.pathsep + inherited if inherited else ""
                )
            runpy.run_module("pytest", run_name="__main__", alter_sys=True)
        finally:
            primary = sys.exception()
            try:
                clock.FlextInfraPytestClock.publish_profile(profile, output)
            except BaseException as publication_failure:
                if primary is None or (
                    isinstance(primary, SystemExit)
                    and (primary.code is None or primary.code == 0)
                ):
                    raise
                primary.add_note(
                    "profile publication failed:\n"
                    + "".join(
                        traceback.format_exception(publication_failure, chain=False)
                    )
                )
                if isinstance(primary, SystemExit):
                    try:
                        traceback.print_exception(publication_failure, chain=False)
                    except (OSError, ValueError) as diagnostic_failure:
                        primary.add_note(
                            f"profile failure diagnostic failed: {diagnostic_failure}"
                        )
            finally:
                retire()

    @classmethod
    def bootstrap_stub(cls, clock_module: str) -> str:
        """Render the ``python -c`` payload binding ``clock`` and ``profile``.

        Returns:
            The parent-free stub leaving the clock and profiler bound.

        """
        return cls._stub(
            f"clock, profile = child.{cls.__name__}.{cls.bootstrap.__name__}"
            f"({clock_module!r})",
        )

    @classmethod
    def startup_stub(cls, clock_module: str, child_root_env: str) -> str:
        """Render the descendant ``sitecustomize`` payload.

        Returns:
            The parent-free stub invoking the startup handoff.

        """
        return cls._stub(
            f"child.{cls.__name__}.{cls.startup.__name__}"
            f"(__file__, {clock_module!r}, {child_root_env!r})"
        )

    @classmethod
    def launcher_stub(
        cls, clock_module: str, child_root_env: str, process_directory_env: str
    ) -> str:
        """Render the profiled ``python -c`` pytest launcher payload.

        Returns:
            The parent-free stub invoking the canonical launcher, whose
            first argument is the output profile artifact.

        """
        return cls._stub(
            f"child.{cls.__name__}.{cls.launcher.__name__}"
            f"({clock_module!r}, {child_root_env!r}, {process_directory_env!r})"
        )

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
            "child = sys.modules.get(spec.name)\n"
            "if child is None:\n"
            "    child = module_from_spec(spec)\n"
            "    sys.modules[spec.name] = child\n"
            "    spec.loader.exec_module(child)\n"
            f"{call}\n"
        )


__all__: list[str] = ["FlextInfraPytestProfileChild"]
