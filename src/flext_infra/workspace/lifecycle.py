"""Serial lifecycle validation through each governed repository's public Make verbs.

Copyright (c) 2026 FLEXT Team. All rights reserved.
SPDX-License-Identifier: MIT
"""

from __future__ import annotations

from pathlib import Path
from time import monotonic

from flext_infra import c, m, p, r, t, u
from flext_infra.workspace import (
    FlextInfraWorkspaceDetector,
    FlextInfraWorkspaceEnvironmentProvenance,
)


class FlextInfraWorkspaceLifecycle:
    """Validate declared topology without Git publication or private Make handlers."""

    @staticmethod
    def plan_request(
        request: p.Infra.WorkspaceRequest,
    ) -> p.Result[m.Infra.LifecycleReport]:
        """Declare public commands before execution without provisioning sources.

        Returns:
            Ordered root and member commands from the declared lifecycle.

        """
        root = request.repository_root.expanduser().resolve()
        inputs = u.Infra.load_codegen_inputs(root)
        if inputs.failure:
            return r[m.Infra.LifecycleReport].from_failure(inputs)
        make = inputs.value.spec.make
        loaded = FlextInfraWorkspaceDetector.load_workspace_spec(root)
        if loaded.failure:
            return r[m.Infra.LifecycleReport].from_failure(loaded)
        workspace = loaded.value
        scope = (
            root,
            *(
                root / member.path
                for member in u.Infra.mutable_flext_members(workspace)
            ),
        )
        commands = tuple(
            (
                repository,
                step,
                (c.Infra.MAKE, step.verb)
                if repository == root
                else (
                    c.Infra.MAKE,
                    "-f",
                    str(repository / c.Infra.MAKEFILE_FILENAME),
                    step.verb,
                ),
            )
            for step in make.lifecycle_steps
            for repository in (scope if step.scope == "each" else (root,))
        )
        output_dir = root / c.Infra.LIFECYCLE_REPORT_RELATIVE_PATH.with_suffix("")
        ci = make.ci
        context: t.Infra.LifecycleContext = (
            "ci" if u.Infra.env_value(ci.variable).strip() == ci.value else "local"
        )
        scoped_members = context == "local"
        receipts = [
            m.Infra.LifecycleReceipt(
                command=command,
                cwd=root,
                repository_root=repository,
                environment_root=u.Infra.runtime_environment_dir(
                    root,
                    runtime_root=root if context == "ci" else None,
                ).resolve(),
                execution_context=context,
                applicable=(
                    None
                    if context in step.contexts
                    and (repository == root or scoped_members)
                    else False
                ),
                applicability_reason=(
                    None
                    if context in step.contexts
                    and (repository == root or scoped_members)
                    else "CI invocation owns only its root"
                    if repository != root and not scoped_members
                    else f"{context} is outside the step's declared contexts"
                ),
                output_file=output_dir / f"{index:04d}-{command[-1]}.log",
            )
            for index, (repository, step, command) in enumerate(commands)
        ]
        report = m.Infra.LifecycleReport(
            workspace_root=root,
            scope=scope,
            observed_files=tuple(Path(name) for name in make.lifecycle_observed_files),
            receipts=tuple(receipts),
        )
        return r[m.Infra.LifecycleReport].ok(report)

    @classmethod
    def execute_request(
        cls,
        request: p.Infra.WorkspaceRequest,
    ) -> p.Result[m.Infra.LifecycleReport]:
        """Run declared public commands serially with first-failure accounting.

        Returns:
            Completed receipts or the original causal failure.

        """
        planned = cls.plan_request(request)
        if planned.failure:
            return r[m.Infra.LifecycleReport].from_failure(planned)
        report = planned.value
        published = cls._publish(report)
        if published.failure:
            return r[m.Infra.LifecycleReport].from_failure(published)
        return cls._execute_report(report)

    @classmethod
    def _execute_report(
        cls,
        report: m.Infra.LifecycleReport,
    ) -> p.Result[m.Infra.LifecycleReport]:
        """Execute applicable rows and preserve the first causal receipt.

        Returns:
            Reached and unreached receipt accounting or the native failure.

        """
        receipts = list(report.receipts)
        eligible: frozenset[Path] | None = None
        for index, receipt in enumerate(receipts):
            if receipt.applicable is False:
                continue
            if receipt.repository_root != report.workspace_root and eligible is None:
                selected = cls._member_eligibility(report)
                if selected.failure:
                    receipts[index] = receipt.model_copy(
                        update={"error": selected.error},
                    )
                    report = report.model_copy(update={"receipts": tuple(receipts)})
                    cls._published_progress(report, selected)
                    return r[m.Infra.LifecycleReport].from_failure(selected)
                eligible = selected.value
            executed = cls._executed_receipt(report, receipt, eligible)
            if executed.failure:
                return r[m.Infra.LifecycleReport].from_failure(executed)
            receipts[index], original = executed.value
            report = report.model_copy(update={"receipts": tuple(receipts)})
            failure = cls._published_progress(report, original)
            if failure is not None:
                return failure
            failed = receipts[index]
            if failed.error is not None:
                return cls._failed_progress(failed.error, original)
        return r[m.Infra.LifecycleReport].ok(report)

    @classmethod
    def _member_eligibility(
        cls,
        report: m.Infra.LifecycleReport,
    ) -> p.Result[frozenset[Path]]:
        """Resolve the workspace's authenticated editable member roots.

        Args:
            report: The lifecycle report being executed.

        Returns:
            The eligible member roots under the workspace root, or the
            editable election failure.

        """
        selected = FlextInfraWorkspaceEnvironmentProvenance.editable_members(
            report.workspace_root,
        )
        if selected.failure:
            return r[frozenset[Path]].from_failure(selected)
        return r[frozenset[Path]].ok(
            frozenset(report.workspace_root / member.path for member in selected.value)
        )

    @classmethod
    def _executed_receipt(
        cls,
        report: m.Infra.LifecycleReport,
        receipt: m.Infra.LifecycleReceipt,
        eligible: frozenset[Path] | None,
    ) -> p.Result[
        t.Pair[m.Infra.LifecycleReceipt, p.Result[p.Cli.ProcessOutcome] | None]
    ]:
        """Run one applicable receipt or mark its unauthenticated destination.

        Args:
            report: The lifecycle report being executed.
            receipt: The applicable receipt being executed.
            eligible: The authenticated editable member roots, or ``None``
                before the first workspace-relative election.

        Returns:
            The executed or reclassified receipt with its process outcome.

        """
        result_type = r[
            t.Pair[m.Infra.LifecycleReceipt, p.Result[p.Cli.ProcessOutcome] | None]
        ]
        if receipt.repository_root == report.workspace_root:
            return result_type.ok(cls.run_receipt(receipt, report.observed_files))
        if eligible is not None and receipt.repository_root not in eligible:
            return result_type.ok((
                receipt.model_copy(
                    update={
                        "applicable": False,
                        "applicability_reason": (
                            "dependency has no authenticated editable source"
                        ),
                    },
                ),
                None,
            ))
        return result_type.ok(cls.run_receipt(receipt, report.observed_files))

    @classmethod
    def _published_progress(
        cls,
        report: m.Infra.LifecycleReport,
        cause: p.Result[p.Cli.ProcessOutcome] | p.Result[frozenset[Path]] | None,
    ) -> p.Result[m.Infra.LifecycleReport] | None:
        """Publish incremental progress and classify its failure, if any.

        Args:
            report: The report advanced with the executed receipt.
            cause: The causal process outcome of the advanced receipt.

        Returns:
            ``None`` when progress published cleanly, else the classified
            causal failure to propagate.

        """
        published = cls._publish(report)
        if not published.failure:
            return None
        if cause is not None and cause.failure:
            u.Cli.error(f"receipt publication failed: {published.error}")
            if cause.exception is not None:
                cause.exception.add_note(
                    f"receipt publication failed: {published.error}",
                )
            return r[m.Infra.LifecycleReport].from_failure(cause)
        return r[m.Infra.LifecycleReport].from_failure(published)

    @staticmethod
    def _failed_progress(
        failed_error: str,
        original: p.Result[p.Cli.ProcessOutcome] | None,
    ) -> p.Result[m.Infra.LifecycleReport]:
        """Preserve the first causal receipt failure of one executed row.

        Args:
            failed_error: The executed receipt's recorded error.
            original: The executed process outcome, when the receipt ran.

        Returns:
            The causal process failure, or the receipt error failure.

        """
        if original is not None and original.failure:
            return r[m.Infra.LifecycleReport].from_failure(original)
        return r[m.Infra.LifecycleReport].fail(failed_error)

    @staticmethod
    def _observed(
        root: Path,
        relative_paths: t.VariadicTuple[Path],
    ) -> p.Result[t.VariadicTuple[m.Infra.LifecycleFileObservation]]:
        """Read the config-declared bounded file observations.

        Returns:
            Physical file states, including absent leaves.

        """
        states: list[m.Infra.LifecycleFileObservation] = []
        for relative in relative_paths:
            observed = u.Cli.atomic_read_binary_file_state(
                root / relative, required=False
            )
            if observed.failure:
                return r[
                    t.VariadicTuple[m.Infra.LifecycleFileObservation]
                ].from_failure(
                    observed,
                )
            content = observed.value.content
            states.append(
                m.Infra.LifecycleFileObservation(
                    path=observed.value.path,
                    sha256=None if content is None else u.Cli.sha256_bytes(content),
                    mode=observed.value.mode,
                    size=0 if content is None else len(content),
                ),
            )
        return r[t.VariadicTuple[m.Infra.LifecycleFileObservation]].ok(tuple(states))

    @classmethod
    def run_receipt(
        cls,
        receipt: m.Infra.LifecycleReceipt,
        relative_paths: t.VariadicTuple[Path],
    ) -> t.Pair[m.Infra.LifecycleReceipt, p.Result[p.Cli.ProcessOutcome]]:
        """Reap the original command and observe only declared evidence files.

        Returns:
            The receipt with native outcome, elapsed time and bounded effects.

        """
        before = cls._observed(receipt.repository_root or receipt.cwd, relative_paths)
        if before.failure:
            return (
                receipt.model_copy(update={"error": before.error}),
                r[p.Cli.ProcessOutcome].from_failure(before),
            )
        u.Cli.info(f"[validate-lifecycle] {receipt.cwd}: {' '.join(receipt.command)}")
        started = monotonic()
        run = u.Cli.run_to_file(
            receipt.command,
            receipt.output_file,
            cwd=receipt.cwd,
            options=m.Cli.ProcessOptions(
                remove_env_keys=c.Infra.ORCHESTRATOR_REMOVE_ENV_KEYS,
                live=True,
            ),
        )
        elapsed = monotonic() - started
        outcome = (
            None
            if run.failure
            else m.Cli.ProcessOutcome.model_validate(run.value, from_attributes=True)
        )
        after = cls._observed(receipt.repository_root or receipt.cwd, relative_paths)
        error = run.error if run.failure else None
        if run.success and not u.Cli.process_succeeded(run.value):
            error = (
                f"failed ({run.value.raw_return_code}): {' '.join(receipt.command)} "
                f"in {receipt.cwd}; timed_out={run.value.timed_out}, "
                f"forwarded_signal={run.value.forwarded_signal}; "
                f"output={receipt.output_file}"
            )
            run = r[p.Cli.ProcessOutcome].fail(error)
        if error is None and after.failure:
            error = after.error
            run = r[p.Cli.ProcessOutcome].from_failure(after)
        observed_receipt = receipt.model_copy(
            update={
                "applicable": True,
                "before_files": before.value,
                "after_files": () if after.failure else after.value,
                "elapsed_seconds": elapsed,
                "environment_root": u.Infra.runtime_environment_dir(
                    receipt.cwd,
                    runtime_root=(
                        receipt.cwd if receipt.execution_context == "ci" else None
                    ),
                ).resolve(),
                "outcome": outcome,
                "error": error,
            },
        )
        return observed_receipt, run

    @staticmethod
    def _publish(report: m.Infra.LifecycleReport) -> p.Result[Path]:
        """Persist reached and unreached command accounting.

        Returns:
            The report's published evidence path.

        """
        return u.Infra.publish_refactor_report_evidence(
            report.workspace_root,
            report,
            relative_path=c.Infra.LIFECYCLE_REPORT_RELATIVE_PATH,
        )


__all__: list[str] = ["FlextInfraWorkspaceLifecycle"]
