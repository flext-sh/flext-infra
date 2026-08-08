"""Heavy ``u.Cli`` utility namespace materialized on demand."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_cli._utilities._options_parts.flextcliutilitiesoptions_part_02 import (
    FlextCliUtilitiesOptions,
)
from flext_cli._utilities.auth import FlextCliUtilitiesAuth
from flext_cli._utilities.cmd import FlextCliUtilitiesCmd
from flext_cli._utilities.commands import FlextCliUtilitiesCommands
from flext_cli._utilities.config import FlextCliUtilitiesConfig
from flext_cli._utilities.conversion import FlextCliUtilitiesConversion
from flext_cli._utilities.env import FlextCliUtilitiesEnv
from flext_cli._utilities.file_test_helpers import FlextCliUtilitiesFileTestHelpersMixin
from flext_cli._utilities.files import FlextCliUtilitiesFiles
from flext_cli._utilities.formatters import FlextCliUtilitiesFormatters
from flext_cli._utilities.framework import FlextCliUtilitiesFramework
from flext_cli._utilities.json import FlextCliUtilitiesJson
from flext_cli._utilities.matching import FlextCliUtilitiesMatching
from flext_cli._utilities.model_commands import FlextCliUtilitiesModelCommands
from flext_cli._utilities.output import FlextCliUtilitiesOutput
from flext_cli._utilities.params import FlextCliUtilitiesParams
from flext_cli._utilities.pipeline import FlextCliUtilitiesPipeline
from flext_cli._utilities.processes import FlextCliUtilitiesProcesses
from flext_cli._utilities.prompts import FlextCliUtilitiesPrompts
from flext_cli._utilities.rules import FlextCliUtilitiesRules
from flext_cli._utilities.runtime import FlextCliUtilitiesRuntime
from flext_cli._utilities.settings import FlextCliUtilitiesSettings
from flext_cli._utilities.tables import FlextCliUtilitiesTables
from flext_cli._utilities.template import FlextCliUtilitiesTemplate
from flext_cli._utilities.toml import FlextCliUtilitiesToml
from flext_cli._utilities.validation import FlextCliUtilitiesValidation
from flext_cli._utilities.yaml import FlextCliUtilitiesYaml
from flext_cli._utilities.yaml_model import FlextCliUtilitiesYamlModel

if TYPE_CHECKING:
    from flext_cli._utilities.docx import FlextCliUtilitiesDocx
    from flext_cli._utilities.xlsx import FlextCliUtilitiesXlsx
else:
    try:
        from flext_cli._utilities.docx import FlextCliUtilitiesDocx
    except ModuleNotFoundError:

        class FlextCliUtilitiesDocx:
            """Fallback when python-docx is not installed."""

    try:
        from flext_cli._utilities.xlsx import FlextCliUtilitiesXlsx
    except ModuleNotFoundError:

        class FlextCliUtilitiesXlsx:
            """Fallback when openpyxl is not installed."""


class FlextCliUtilitiesCli(
    FlextCliUtilitiesAuth,
    FlextCliUtilitiesCmd,
    FlextCliUtilitiesCommands,
    FlextCliUtilitiesConfig,
    FlextCliUtilitiesConversion,
    FlextCliUtilitiesEnv,
    FlextCliUtilitiesTemplate,
    FlextCliUtilitiesFileTestHelpersMixin,
    FlextCliUtilitiesFiles,
    FlextCliUtilitiesFramework,
    FlextCliUtilitiesFormatters,
    FlextCliUtilitiesJson,
    FlextCliUtilitiesMatching,
    FlextCliUtilitiesModelCommands,
    FlextCliUtilitiesOptions,
    FlextCliUtilitiesOutput,
    FlextCliUtilitiesParams,
    FlextCliUtilitiesPipeline,
    FlextCliUtilitiesPrompts,
    FlextCliUtilitiesProcesses,
    FlextCliUtilitiesRules,
    FlextCliUtilitiesRuntime,
    FlextCliUtilitiesSettings,
    FlextCliUtilitiesTables,
    FlextCliUtilitiesToml,
    FlextCliUtilitiesValidation,
    FlextCliUtilitiesXlsx,
    FlextCliUtilitiesDocx,
    FlextCliUtilitiesYaml,
    FlextCliUtilitiesYamlModel,
):
    """Command line interface specific utilities composed via MRO."""


__all__: tuple[str, ...] = ("FlextCliUtilitiesCli",)
