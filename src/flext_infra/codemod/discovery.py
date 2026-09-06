"""Discover ast-grep rules from installed FLEXT packages in cascade order."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path
from typing import TYPE_CHECKING, Final

from flext_infra import r, t, u

if TYPE_CHECKING:
    from flext_infra import p

# Cascade order: last wins on rule ID conflict. The local project is appended
# by the caller through ``extra_packages`` so it always overrides the library.
_CASCADE_PACKAGES: Final[tuple[str, ...]] = ("flext_core", "flext_cli", "flext_infra")


def rule_documents(rule: Path) -> p.Result[t.SequenceOf[t.JsonMapping]]:
    """Parse every non-empty YAML document of one ast-grep rule file.

    ast-grep keys rules by ``id`` and rejects a duplicate id, so every
    document must declare one; a file that does not is a defect of that file,
    never a rule to skip.
    """
    documents: list[t.JsonMapping] = []
    for raw_document in rule.read_text(encoding="utf-8").split("\n---"):
        if not any(
            line.strip() and not line.lstrip().startswith("#")
            for line in raw_document.splitlines()
        ):
            continue
        parsed = u.Cli.yaml_parse(raw_document)
        if parsed.failure:
            return r[t.SequenceOf[t.JsonMapping]].fail(
                parsed.error or f"invalid ast-grep rule document in {rule}"
            )
        rule_id = parsed.value.get("id")
        if not isinstance(rule_id, str) or not rule_id:
            return r[t.SequenceOf[t.JsonMapping]].fail(
                f"ast-grep rule document missing required id: {rule}"
            )
        documents.append(parsed.value)
    return r[t.SequenceOf[t.JsonMapping]].ok(tuple(documents))


def index_rules_by_id(
    rules: dict[str, Path], rule_files: t.SequenceOf[Path], *, source: str
) -> p.Result[bool]:
    """Register ``rule_files`` into ``rules`` keyed by ast-grep rule id.

    A later source overrides an earlier one on the same id (cascade
    contract). Two files of the SAME source claiming one id is a defect:
    ast-grep would refuse the batch, so discovery refuses it first.
    """
    claimed: dict[str, Path] = {}
    for rule_file in rule_files:
        documents = rule_documents(rule_file)
        if documents.failure:
            return r[bool].from_failure(documents)
        for document in documents.value:
            rule_id = str(document["id"])
            owner = claimed.get(rule_id)
            if owner is not None and owner != rule_file:
                return r[bool].fail(
                    f"duplicate ast-grep rule id {rule_id!r} in {source}: "
                    f"{owner} and {rule_file}"
                )
            claimed[rule_id] = rule_file
            rules[rule_id] = rule_file
    return r[bool].ok(True)


def discover_rules(*extra_packages: str) -> p.Result[t.SequenceOf[Path]]:
    """Discover ast-grep rule files from installed packages.

    Rules are read from each package's ``codemod/rules/`` directory via
    importlib.resources, so they travel inside the wheel instead of being
    projected into every repository. Packages are searched in cascade order;
    later packages override earlier ones on rule id conflict. A cascade
    package that cannot be resolved is a broken environment, not an empty
    contribution.

    Returns the sorted, id-deduplicated rule file paths.
    """
    rules: dict[str, Path] = {}
    for pkg_name in (*_CASCADE_PACKAGES, *extra_packages):
        rules_dir = Path(str(files(pkg_name) / "codemod" / "rules"))
        if not rules_dir.is_dir():
            continue
        indexed = index_rules_by_id(
            rules, tuple(sorted(rules_dir.rglob("*.yml"))), source=pkg_name
        )
        if indexed.failure:
            return r[t.SequenceOf[Path]].from_failure(indexed)
    return r[t.SequenceOf[Path]].ok(tuple(sorted(set(rules.values()))))


__all__: list[str] = ["discover_rules", "index_rules_by_id", "rule_documents"]
