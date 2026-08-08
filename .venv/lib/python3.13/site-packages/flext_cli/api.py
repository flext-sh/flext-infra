"""Public API facade for flext-cli.

Copyright (c) 2025 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from typing import override

from flext_cli import m, p, r, t, u
from flext_cli.services.auth import FlextCliAuth
from flext_cli.services.cli import FlextCliCli
from flext_cli.services.cli_params import FlextCliCommonParams
from flext_cli.services.cmd import FlextCliCmd
from flext_cli.services.docx import FlextCliDocx
from flext_cli.services.file_tools import FlextCliFileTools
from flext_cli.services.formatters import FlextCliFormatters
from flext_cli.services.output import FlextCliOutput
from flext_cli.services.pipeline import FlextCliPipeline
from flext_cli.services.pptx import FlextCliPptx
from flext_cli.services.prompts import FlextCliPrompts
from flext_cli.services.rules import FlextCliRules
from flext_cli.services.runtime import FlextCliRuntime
from flext_cli.services.tables import FlextCliTables
from flext_cli.services.xlsx import FlextCliXlsx
from flext_cli.services.yaml_model import FlextCliYamlModel


class FlextCli(
    FlextCliAuth,
    FlextCliCli,
    FlextCliCmd,
    FlextCliCommonParams,
    FlextCliDocx,
    FlextCliFileTools,
    FlextCliFormatters,
    FlextCliOutput,
    FlextCliPipeline,
    FlextCliPrompts,
    FlextCliPptx,
    FlextCliRules,
    FlextCliRuntime,
    FlextCliTables,
    FlextCliXlsx,
    FlextCliYamlModel,
):
    """Coordinate CLI operations and expose domain services.

    MRO facade over CLI services (auth, cli, cmd, params, docx, file_tools,
    formatters, output, pipeline, prompts, pptx, rules, runtime, tables,
    xlsx, yaml-model).
    All operations return r[T].
    """

    @override
    def execute(self) -> p.Result[m.Cli.RuntimeStatus]:
        """Report the public CLI runtime surface state."""
        return r[m.Cli.RuntimeStatus].ok(u.Cli.cmd_status())


cli: FlextCli = FlextCli.fetch_global()
"""Process-wide ``FlextCli`` facade singleton exposing every CLI service via MRO."""


__all__: t.MutableSequenceOf[str] = ["FlextCli", "cli"]
