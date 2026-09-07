"""Canonical process-exit classification and hermetic child-environment utilities."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra import c, config

if TYPE_CHECKING:
    from flext_infra import t


class FlextInfraUtilitiesProcess:
    """Normalize external process exits and derive hermetic child environments."""

    @staticmethod
    def process_exit_classification(exit_code: int) -> str:
        """Classify a process exit without discarding its original status."""
        if exit_code == c.Infra.PROCESS_TIMEOUT_EXIT_CODE:
            return "timeout"
        if exit_code < 0:
            return f"signal={-exit_code}"
        if exit_code > c.Infra.PROCESS_SIGNAL_EXIT_OFFSET:
            return f"signal={exit_code - c.Infra.PROCESS_SIGNAL_EXIT_OFFSET}"
        return "failure"

    @staticmethod
    def make_hermetic_env_remove_keys() -> t.StrSequence:
        """Return every Make-owned variable a gate child process must not inherit.

        GNU make exports command-line assignments (``APPLY=Y``, ``WHAT=x``) and
        its own recursion state to every child, so pytest and any ``make`` a
        test spawns would otherwise see the outer verb's selectors and refuse
        (``verb help is read-only and does not accept APPLY``). The set is
        derived from the declared owners only: the orchestrator recursion keys,
        the generated Makefile's project and workspace variables, the
        config-owned selector and apply variable, the settings identity
        variable, the pytest-specific keys, and the host presentation-forcing
        signals. No list is repeated here.
        """
        make = config.Infra.codegen.make
        ordered: dict[str, None] = dict.fromkeys((
            *c.Infra.ORCHESTRATOR_REMOVE_ENV_KEYS,
            *(name for name, _default in c.Infra.PROJECT_VARIABLE_DEFAULTS),
            *(name for name, _default in c.Infra.WORKSPACE_VARIABLE_DEFAULTS),
            make.selector,
            make.apply_variable,
            c.Infra.ENV_VAR_STANDALONE,
            *c.Infra.PYTEST_INHERITED_ENV_REMOVE_KEYS,
            *c.Infra.PRESENTATION_FORCING_ENV_KEYS,
        ))
        return tuple(ordered)


__all__: list[str] = ["FlextInfraUtilitiesProcess"]
