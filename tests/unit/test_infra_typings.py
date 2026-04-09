"""Behavior tests for the public ``t`` typing facade."""

from __future__ import annotations

from pathlib import Path

from flext_tests import tm

from tests import t, u


class TestInfraTypingAdapters:
    """Validate public adapters exposed by ``t``."""

    def test_json_mapping_adapter_validates_nested_cli_payload(self) -> None:
        payload = t.Cli.JSON_MAPPING_ADAPTER.validate_python({
            "tool": {"name": "infra"},
            "enabled": True,
        })

        tm.that(payload["enabled"], eq=True)
        tm.that(payload["tool"], eq={"name": "infra"})

    def test_json_list_adapter_validates_mixed_cli_values(self) -> None:
        items = t.Cli.JSON_LIST_ADAPTER.validate_python(["infra", 1, True])

        tm.that(list(items), eq=["infra", 1, True])

    def test_infra_mapping_adapter_validates_real_workspace_payload(self) -> None:
        payload = t.Infra.INFRA_MAPPING_ADAPTER.validate_python({
            "python": {"version": "3.13"},
            "paths": ["src", "tests"],
            "enabled": True,
        })

        tm.that(payload["python"], eq={"version": "3.13"})
        tm.that(payload["paths"], eq=["src", "tests"])
        tm.that(payload["enabled"], eq=True)

    def test_str_seq_adapter_validates_project_name_sequences(self) -> None:
        values = t.Infra.STR_SEQ_ADAPTER.validate_python(
            ("flext-core", "flext-infra"),
        )

        tm.that(list(values), eq=["flext-core", "flext-infra"])

    def test_container_mapping_adapter_accepts_paths_and_nested_scalars(self) -> None:
        payload = t.Infra.CONTAINER_MAPPING_ADAPTER.validate_python({
            "root": Path("/tmp/flext"),
            "settings": {"enabled": True},
        })

        tm.that(payload["root"], eq=Path("/tmp/flext"))
        tm.that(payload["settings"], eq={"enabled": True})


class TestInfraTypingGuards:
    """Validate public guard helpers that consume typing contracts."""

    def test_registerable_service_guard_accepts_real_public_values(self) -> None:
        tm.that(u.is_registerable_service({"service": "infra"}), eq=True)
        tm.that(u.is_registerable_service(["a", "b"]), eq=True)
        tm.that(u.is_registerable_service(Path("/tmp/flext")), eq=True)

    def test_factory_and_resource_guards_accept_callables(self) -> None:
        def build_service() -> str:
            return "ok"

        tm.that(u.is_factory(build_service), eq=True)
        tm.that(u.is_resource(build_service), eq=True)
