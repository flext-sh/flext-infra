"""Phase: Inject managed/custom markers into pyproject.toml."""

from __future__ import annotations

from flext_infra import c, config, t, u


class FlextInfraInjectCommentsPhase:
    """Inject managed/custom markers into pyproject.toml."""

    _MYPY_RATIONALE_HEADER = (
        "# FLEXT mypy suppression rationale (validated at the facade-FLEXT boundary):"
    )
    _RUFF_RATIONALE_HEADER = (
        "# FLEXT Ruff suppression rationale (validated against semantic facet order):"
    )
    _PYRIGHT_RATIONALE_HEADER = "# FLEXT Pyright suppression rationale (validated at the facade-FLEXT boundary):"
    _STRIP_PREFIXES: t.StrSequence = (
        "# [MANAGED]",
        "# [CUSTOM]",
        "# [AUTO]",
        "# Sections with [",
        "# FLEXT mypy[",
        "# FLEXT ruff[",
        "# FLEXT pyright[",
    )

    @staticmethod
    def _rationale_lines(header: str, items: t.StrMapping, tag: str) -> t.StrSequence:
        """Render one tool's evidence-backed suppression comments."""
        return (
            header,
            *(
                f"# FLEXT {tag}[{code}]: {rationale}"
                for code, rationale in sorted(items.items())
            ),
        )

    @classmethod
    def _mypy_rationale_lines(cls) -> t.StrSequence:
        """Render evidence-backed Mypy exclusions from the tooling SSOT."""
        return cls._rationale_lines(
            cls._MYPY_RATIONALE_HEADER,
            config.Infra.tooling.tools.mypy.disabled_error_codes,
            "mypy",
        )

    @classmethod
    def _ruff_rationale_lines(cls) -> t.StrSequence:
        """Render evidence-backed Ruff exclusions from the tooling SSOT."""
        return cls._rationale_lines(
            cls._RUFF_RATIONALE_HEADER,
            config.Infra.tooling.tools.ruff.lint.ignored_rule_rationales,
            "ruff",
        )

    @classmethod
    def _pyright_rationale_lines(cls) -> t.StrSequence:
        """Render evidence-backed Pyright exclusions from the tooling SSOT."""
        return cls._rationale_lines(
            cls._PYRIGHT_RATIONALE_HEADER,
            config.Infra.tooling.tools.pyright.global_suppression_rationales,
            "pyright",
        )

    @staticmethod
    def _is_section_header(line: str) -> bool:
        """Is section header."""
        stripped = line.strip()
        return stripped.startswith("[") and stripped.endswith("]")

    @classmethod
    def _managed_marker_lines(cls) -> t.Infra.StrSet:
        """Return banner and rationale lines to strip."""
        markers = {c.Infra.LEGACY_AUTO_BANNER_LINE}
        markers.update(c.Infra.BANNER.splitlines())
        markers.update(cls._mypy_rationale_lines())
        markers.update(cls._ruff_rationale_lines())
        markers.update(cls._pyright_rationale_lines())
        return markers

    @classmethod
    def _strip_managed_lines(
        cls, lines: t.StrSequence
    ) -> t.Pair[t.StrSequence, t.StrSequence]:
        """Strip managed lines."""
        changes: t.MutableSequenceOf[str] = []
        managed_lines = cls._managed_marker_lines()
        cleaned: t.MutableSequenceOf[str] = []
        skip_broken_group_section = False
        broken_removed = False
        for line in lines:
            stripped = line.strip()
            if skip_broken_group_section:
                if cls._is_section_header(line):
                    skip_broken_group_section = False
                else:
                    continue
            if stripped.startswith(tuple(cls._STRIP_PREFIXES)):
                continue
            if stripped == "[group.dev.dependencies]":
                skip_broken_group_section = True
                broken_removed = True
                continue
            if stripped in managed_lines:
                continue
            cleaned.append(line)
        if broken_removed:
            changes.append("broken [group.dev.dependencies] section removed")
        return cleaned, changes

    @staticmethod
    def _collapse_blank_lines(lines: t.StrSequence) -> t.StrSequence:
        """Collapse repeated blank lines into a single canonical separator."""
        normalized: t.MutableSequenceOf[str] = []
        previous_blank = False
        for line in lines:
            is_blank = not line.strip()
            if is_blank and previous_blank:
                continue
            normalized.append(line)
            previous_blank = is_blank
        return normalized

    def apply(self, rendered: str) -> t.Pair[str, t.StrSequence]:
        """Inject managed banner/markers and return updated TOML plus change messages."""
        changes: t.MutableSequenceOf[str] = []
        lines = rendered.splitlines()
        cleaned_lines, cleanup_changes = self._strip_managed_lines(lines)
        changes.extend(cleanup_changes)
        banner_lines = c.Infra.BANNER.splitlines()
        first_content = next(
            (index for index, line in enumerate(cleaned_lines) if line.strip()),
            len(cleaned_lines),
        )
        content_lines = cleaned_lines[first_content:]
        out: t.MutableSequenceOf[str] = [*banner_lines, ""]
        if lines[: len(banner_lines)] != banner_lines:
            changes.append("managed banner injected")
        emitted_markers: set[str] = set()
        for line in content_lines:
            stripped = line.strip()
            markers_result = u.Infra.pyproject_section_markers(stripped)
            if markers_result.failure:
                raise RuntimeError(
                    markers_result.error or "pyproject section markers failed"
                )
            for marker in markers_result.value:
                if marker not in emitted_markers:
                    out.append(marker)
                    changes.append(f"marker injected for {stripped}")
                    emitted_markers.add(marker)
            out.append(line)
            if stripped == "[tool.mypy]":
                out.extend(self._mypy_rationale_lines())
                changes.append("Mypy suppression rationales injected")
            elif stripped == "[tool.ruff.lint]":
                out.extend(self._ruff_rationale_lines())
                changes.append("Ruff suppression rationales injected")
            elif stripped == "[tool.pyright]":
                out.extend(self._pyright_rationale_lines())
                changes.append("Pyright suppression rationales injected")
        updated = "\n".join(self._collapse_blank_lines(out)).rstrip() + "\n"
        original = rendered.rstrip() + "\n"
        if updated == original:
            return (updated, [])
        return (updated, changes)


__all__: list[str] = ["FlextInfraInjectCommentsPhase"]
