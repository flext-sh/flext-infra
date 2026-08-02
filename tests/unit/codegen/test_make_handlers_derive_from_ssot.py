"""Typed Make handlers are the sole public verb and workflow source.

The generated Make engine forwards one public verb, selector, and APPLY token
to the workspace serializer, which resolves the typed handler tree.
These tests protect that single-owner graph without parsing YAML or generated
projections.
"""

from __future__ import annotations

from operator import itemgetter

from flext_infra import config
from flext_tests import tm


class TestsMakeHandlersDeriveFromSsot:
    """Validate every computed Make projection against its handler rows."""

    def test_verb_projections_derive_from_handlers(self) -> None:
        """Selectors and defaults never acquire a second handwritten owner."""
        for verb in config.Infra.codegen.make.verbs:
            handlers = verb.handlers
            default = next(handler.what for handler in handlers if handler.default)
            apply_default = next(
                (handler.what for handler in handlers if handler.apply_default), None
            )

            tm.that(verb.whats, eq=tuple(handler.what for handler in handlers))
            tm.that(verb.default_what, eq=default)
            tm.that(verb.apply_default_what, eq=apply_default)
            tm.that(verb.apply_what, eq=apply_default or default)
            tm.that(
                verb.required_apply_whats,
                eq=tuple(
                    handler.what
                    for handler in handlers
                    if handler.apply_policy == "required"
                ),
            )
            tm.that(
                verb.optional_apply_whats,
                eq=tuple(
                    handler.what
                    for handler in handlers
                    if handler.apply_policy == "optional"
                ),
            )
            tm.that(
                verb.never_apply_whats,
                eq=tuple(
                    handler.what
                    for handler in handlers
                    if handler.apply_policy == "never"
                ),
            )

    def test_workflow_projection_derives_from_handler_membership(self) -> None:
        """Workflow order and mutation intent come only from handler rows."""
        declared: list[tuple[int, str, str, bool, tuple[str, ...]]] = []
        for verb in config.Infra.codegen.make.verbs:
            for handler in verb.handlers:
                membership = handler.workflow
                if membership is not None:
                    declared.append((
                        membership.order,
                        verb.name,
                        handler.what,
                        handler.apply_policy != "never",
                        membership.contexts,
                    ))
        declared.sort(key=itemgetter(0))
        expected = tuple(
            (verb, what, applying, contexts)
            for _, verb, what, applying, contexts in declared
        )
        projected = tuple(
            (step.verb, step.what, step.apply, step.contexts)
            for step in config.Infra.codegen.make.workflow
        )

        tm.that(projected, eq=expected)

    def test_generation_operation_has_one_public_verb(self) -> None:
        """The Make generation service is reachable through one config route."""
        make = config.Infra.codegen.make
        operations = tuple(
            operation
            for operation in make.operations
            if operation.executor == "generation"
        )

        tm.that(operations, len=1)
        generation_verbs = tuple(
            verb for verb in make.verbs if verb.operation == operations[0].name
        )
        tm.that(generation_verbs, len=1)
        tm.that(generation_verbs[0].handlers, empty=False)

    def test_conform_and_gen_have_distinct_mutation_contracts(self) -> None:
        """Read-only conformance never aliases generated-surface publication."""
        make = config.Infra.codegen.make
        operations = {operation.name: operation for operation in make.operations}
        verbs = {verb.name: verb for verb in make.verbs}
        conform = verbs["conform"]
        generation = verbs["gen"]

        tm.that(operations[conform.operation].mutation, eq="never")
        tm.that(operations[generation.operation].mutation, eq="apply")
        tm.that(conform.operation, ne=generation.operation)
        tm.that(conform.handlers[0].apply_policy, eq="never")
        tm.that(generation.handlers[0].apply_policy, eq="required")
        tm.that(conform.handlers[0].workflow, is_=None)


__all__: tuple[str, ...] = ()
