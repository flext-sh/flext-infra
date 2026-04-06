from __future__ import annotations

import tomlkit
from flext_tests import tm
from tomlkit.toml_document import TOMLDocument

from flext_infra import FlextInfraDependencyPathSync

_PATH_SYNC = FlextInfraDependencyPathSync()
_rewrite_pep621 = _PATH_SYNC._rewrite_pep621


class TestRewritePep621:
    def test_rewrite_pep621_no_project(self) -> None:
        doc = TOMLDocument()
        changes, _ = _rewrite_pep621(doc, internal_names=set())
        tm.that(changes, eq=[])

    def test_rewrite_pep621_no_dependencies(self) -> None:
        doc = TOMLDocument()
        doc["project"] = tomlkit.table()
        changes, _ = _rewrite_pep621(doc, internal_names=set())
        tm.that(changes, eq=[])

    def test_rewrite_pep621_non_list_dependencies(self) -> None:
        doc = TOMLDocument()
        doc["project"] = {"dependencies": "not-a-list"}
        changes, _ = _rewrite_pep621(doc, internal_names=set())
        tm.that(changes, eq=[])

    def test_rewrite_pep621_rewrite_path_dep(self) -> None:
        doc = TOMLDocument()
        doc["project"] = {
            "dependencies": ["flext-core @ file://.flext-deps/flext-core"],
        }
        changes, deps = _rewrite_pep621(
            doc,
            internal_names={"flext-core"},
        )
        assert len(changes) > 0
        unwrapped = doc.unwrap()
        # _rewrite_pep621 strips the path reference, leaving just the package name
        tm.that(unwrapped["project"]["dependencies"][0], eq="flext-core")
        tm.that("flext-core" in deps, eq=True)

    def test_rewrite_pep621_skip_external_dep(self) -> None:
        doc = TOMLDocument()
        doc["project"] = {"dependencies": ["requests>=2.0.0"]}
        changes, _ = _rewrite_pep621(
            doc,
            internal_names={"flext-core"},
        )
        tm.that(changes, eq=[])

    def test_rewrite_pep621_with_marker(self) -> None:
        doc = TOMLDocument()
        doc["project"] = {
            "dependencies": [
                'flext-core @ file://.flext-deps/flext-core ; python_version >= "3.8"',
            ],
        }
        changes, _ = _rewrite_pep621(
            doc,
            internal_names={"flext-core"},
        )
        assert len(changes) > 0
        unwrapped = doc.unwrap()
        tm.that(unwrapped["project"]["dependencies"][0], has='python_version >= "3.8"')

    def test_rewrite_pep621_non_string_item(self) -> None:
        doc = TOMLDocument()
        doc["project"] = {
            "dependencies": [123, "flext-core @ file://.flext-deps/flext-core"],
        }
        changes, _ = _rewrite_pep621(
            doc,
            internal_names={"flext-core"},
        )
        tm.that(changes, eq=[])
        unwrapped = doc.unwrap()
        tm.that(
            unwrapped["project"]["dependencies"],
            eq=[123, "flext-core @ file://.flext-deps/flext-core"],
        )

    def test_rewrite_pep621_subproject_mode(self) -> None:
        doc = TOMLDocument()
        doc["project"] = {
            "dependencies": ["flext-core @ file://.flext-deps/flext-core"],
        }
        changes, _ = _rewrite_pep621(
            doc,
            internal_names={"flext-core"},
        )
        assert len(changes) > 0
        unwrapped = doc.unwrap()
        # path rewriting (../flext-core) is done by _rewrite_uv_sources, not _rewrite_pep621
        tm.that(unwrapped["project"]["dependencies"][0], eq="flext-core")


def test_rewrite_pep621_non_string_item() -> None:
    doc = tomlkit.document()
    project = tomlkit.table()
    project["dependencies"] = [123]
    doc["project"] = project
    changes, _ = _rewrite_pep621(
        doc,
        internal_names={"flext-core"},
    )
    tm.that(len(changes), eq=0)


def test_rewrite_pep621_no_project_table() -> None:
    doc = tomlkit.document()
    changes, _ = _rewrite_pep621(
        doc,
        internal_names={"flext-core"},
    )
    tm.that(len(changes), eq=0)


def test_rewrite_pep621_invalid_path_dep_regex() -> None:
    doc = tomlkit.document()
    project = tomlkit.table()
    project["dependencies"] = ["  flext-core @ file://.flext-deps/flext-core"]
    doc["project"] = project
    changes, _ = _rewrite_pep621(
        doc,
        internal_names={"flext-core"},
    )
    # PEP621_NAME_RE allows leading whitespace, so this WILL extract name and create change
    tm.that(len(changes), eq=1)
