"""Gate contract per-script checks."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flext_infra.constants import c
from flext_infra.utilities import u
from flext_infra.validate.gate_contract_content import (
    FlextInfraGateContractContentMixin,
)
from flext_infra.validate.gate_contract_models import FlextInfraGateContractModels

if TYPE_CHECKING:
    from pathlib import Path

    from flext_infra.typings import t


class FlextInfraGateContractChecksMixin(FlextInfraGateContractContentMixin):
    """Validate one script against the gate contract."""

    @staticmethod
    def _classify_role(script_path: Path) -> str:
        name = script_path.stem
        is_validator = c.Infra.SKILL_VALIDATOR_NAME_RE.match(name) is not None
        is_fixer = c.Infra.SKILL_FIXER_NAME_RE.match(name) is not None
        is_shared = script_path.as_posix().startswith(("scripts/lib/", "scripts/core/"))
        if is_shared and not (is_validator or is_fixer):
            return "other"
        if is_validator:
            return "validator"
        return "fixer" if is_fixer else "other"

    @staticmethod
    def _read_header(content: str) -> t.StrSequence:
        return content.splitlines()[: c.Infra.SCRIPT_HEADER_MAX_LINES]

    @staticmethod
    def _count_code_lines(content: str, extension: str) -> int:
        return sum(
            1
            for stripped in (line.strip() for line in content.splitlines())
            if stripped
            and not (extension in {".py", ".sh"} and stripped.startswith("#"))
        )

    @staticmethod
    def _check_shebang(
        script: str,
        header: t.StrSequence,
        extension: str,
    ) -> FlextInfraGateContractModels.Violation | None:
        if not header:
            return FlextInfraGateContractModels.Violation(
                check="shebang",
                message="empty file - no shebang found",
                script=script,
            )

        first = header[0]
        match extension:
            case ".py" if not first.startswith("#!/usr/bin/env python"):
                message = f"expected '#!/usr/bin/env python3', got: {first!r}"
            case ".sh" if not first.startswith(
                ("#!/usr/bin/env bash", "#!/bin/bash"),
            ):
                message = f"expected '#!/usr/bin/env bash', got: {first!r}"
            case _:
                message = ""
        return (
            None
            if not message
            else FlextInfraGateContractModels.Violation(
                check="shebang",
                message=message,
                script=script,
            )
        )

    @staticmethod
    def _check_owner_marker(
        script: str,
        header: t.StrSequence,
    ) -> FlextInfraGateContractModels.Violation | None:
        if any(c.Infra.SKILL_OWNER_MARKER_RE.match(line) for line in header):
            return None
        return FlextInfraGateContractModels.Violation(
            check="owner_marker",
            message=(
                "missing Owner-Skill marker in first "
                f"{c.Infra.SCRIPT_HEADER_MAX_LINES} lines"
            ),
            script=script,
        )

    @staticmethod
    def _check_exit_codes(
        script: str,
        content: str,
        extension: str,
    ) -> t.SequenceOf[FlextInfraGateContractModels.Violation]:
        if extension != ".sh":
            return ()

        violations: list[FlextInfraGateContractModels.Violation] = []
        for i, line in enumerate(content.splitlines(), 1):
            match = c.Infra.SKILL_BASH_EXIT_RE.match(line)
            if match is None:
                continue
            code = int(match.group(1))
            if code not in c.Infra.SCRIPT_EXIT_CODE_VALUES:
                violations.append(
                    FlextInfraGateContractModels.Violation(
                        check="exit_code",
                        message=f"line {i}: exit {code} - only 0/1/2/3 allowed",
                        script=script,
                    ),
                )
        return tuple(violations)

    def _check_min_code_lines(
        self,
        script: str,
        content: str,
        extension: str,
        role: str,
    ) -> FlextInfraGateContractModels.Violation | None:
        if role == "other":
            return None
        code_lines = self._count_code_lines(content, extension)
        if code_lines >= c.Infra.SCRIPT_MIN_CODE_LINES:
            return None
        return FlextInfraGateContractModels.Violation(
            check="min_code_lines",
            message=(
                f"{role} has only {code_lines} code lines "
                f"(minimum {c.Infra.SCRIPT_MIN_CODE_LINES}) - may be a stub"
            ),
            script=script,
            severity=c.Infra.GateSeverity.WARNING.value,
        )

    def _validate_script(
        self,
        root: Path,
        script_path: Path,
        *,
        check_all: bool,
    ) -> FlextInfraGateContractModels.ScriptInfo:
        script = script_path.as_posix()
        extension = script_path.suffix
        role = self._classify_role(script_path)
        if role == "other" and not check_all:
            return FlextInfraGateContractModels.ScriptInfo(
                extension=extension,
                path=script,
                role=role,
            )

        read = u.Cli.files_read_text(root / script_path)
        if read.failure:
            unreadable = FlextInfraGateContractModels.Violation(
                check="readable",
                message=read.error or "could not read file",
                script=script,
            )
            return FlextInfraGateContractModels.ScriptInfo(
                extension=extension,
                path=script,
                role=role,
                violations=(unreadable,),
            )
        content = read.value

        header = self._read_header(content)
        violations: list[FlextInfraGateContractModels.Violation] = [
            *self._check_exit_codes(script, content, extension),
            *self._check_interactive(script, content, extension),
            *self._check_artifact_naming(script, content),
        ]
        violations.extend(
            violation
            for violation in (
                self._check_shebang(script, header, extension),
                self._check_owner_marker(script, header),
                self._check_min_code_lines(script, content, extension, role),
            )
            if violation is not None
        )
        return FlextInfraGateContractModels.ScriptInfo(
            extension=extension,
            path=script,
            role=role,
            violations=tuple(violations),
        )


__all__: list[str] = ["FlextInfraGateContractChecksMixin"]
