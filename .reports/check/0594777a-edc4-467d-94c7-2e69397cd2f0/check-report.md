# Workspace Check Report

Generated: 2026-11-19 23:27:23 UTC
Check phase: complete
Execution: COMPLETE
Projects reached: 1/1

## Summary

| Project | Status | Findings |
| --- |---:|---:|
| flext-m6igj | FAIL | 1 |

## Details

### flext-m6igj
Root: `/home/marlonsc/flext/.claude/worktrees/kilo-code-flext-violations-89bd05/worktrees/flext-m6igj`
- lint: PASS (0 issues)
  - Native output receipt: [lint.raw.log](file:///home/marlonsc/flext/.claude/worktrees/kilo-code-flext-violations-89bd05/worktrees/flext-m6igj/.reports/check/0594777a-edc4-467d-94c7-2e69397cd2f0/flext-m6igj/lint.raw.log)
- markdown: PASS (0 issues)
  - Native output receipt: [markdown.raw.log](file:///home/marlonsc/flext/.claude/worktrees/kilo-code-flext-violations-89bd05/worktrees/flext-m6igj/.reports/check/0594777a-edc4-467d-94c7-2e69397cd2f0/flext-m6igj/markdown.raw.log)
- deps: FAIL (1 issues)
  - /home/marlonsc/flext/.claude/worktrees/kilo-code-flext-violations-89bd05/worktrees/flext-m6igj:0:0 [error] Traceback (most recent call last):
  File "/home/marlonsc/flext/.claude/worktrees/kilo-code-flext-violations-89bd05/worktrees/flext-m6igj/src/flext_infra/gates/deps.py", line 475, in _scan
    scan = self._capture_with_retry(project_dir, report_dir)
  File "/home/marlonsc/flext/.claude/worktrees/kilo-code-flext-violations-89bd05/worktrees/flext-m6igj/src/flext_infra/gates/deps.py", line 327, in _capture_with_retry
    captured.unwrap()  # non-transient: fail loud immediately
    ~~~~~~~~~~~~~~~^^
  File "/home/marlonsc/flext/.claude/worktrees/kilo-code-flext-violations-89bd05/worktrees/flext-m6igj/.venv/lib/python3.13/site-packages/flext_core/_result/unwrap.py", line 51, in unwrap
    return self.value
           ^^^^^^^^^^
  File "/home/marlonsc/flext/.claude/worktrees/kilo-code-flext-violations-89bd05/worktrees/flext-m6igj/.venv/lib/python3.13/site-packages/flext_core/_result/behavior.py", line 58, in value
    self._raise_failure()
    ~~~~~~~~~~~~~~~~~~~^^
  File "/home/marlonsc/flext/.claude/worktrees/kilo-code-flext-violations-89bd05/worktrees/flext-m6igj/.venv/lib/python3.13/site-packages/flext_core/_result/behavior.py", line 73, in _raise_failure
    raise error
  File "/home/marlonsc/flext/.claude/worktrees/kilo-code-flext-violations-89bd05/worktrees/flext-m6igj/.venv/lib/python3.13/site-packages/flext_cli/_utilities/_runtime/process_execution.py", line 66, in _execute_streamed_process
    cls._execute_lifecycle(request, state, timing)
    ~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/marlonsc/flext/.claude/worktrees/kilo-code-flext-violations-89bd05/worktrees/flext-m6igj/.venv/lib/python3.13/site-packages/flext_cli/_utilities/_runtime/process_execution.py", line 143, in _execute_lifecycle
    start_result = cls._start_contained_process(
        m.Cli.RuntimeSpawnCommand(
    ...<12 lines>...
        ),
    )
  File "/home/marlonsc/flext/.claude/worktrees/kilo-code-flext-violations-89bd05/worktrees/flext-m6igj/.venv/lib/python3.13/site-packages/flext_cli/_utilities/_runtime/process_start.py", line 61, in _start_contained_process
    process = cls._spawn_streamed_process(command, stdin_handle, options=contained)
  File "/home/marlonsc/flext/.claude/worktrees/kilo-code-flext-violations-89bd05/worktrees/flext-m6igj/.venv/lib/python3.13/site-packages/flext_cli/_utilities/runtime.py", line 94, in _spawn_streamed_process
    return spawn_streamed_process(
        command.cmd,
    ...<3 lines>...
        options=options,
    )
  File "/home/marlonsc/flext/.claude/worktrees/kilo-code-flext-violations-89bd05/worktrees/flext-m6igj/.venv/lib/python3.13/site-packages/flext_cli/_utilities/native_runtime.py", line 80, in spawn_streamed_process
    return subprocess.Popen(
           ~~~~~~~~~~~~~~~~^
        list(cmd),
        ^^^^^^^^^^
    ...<13 lines>...
        pass_fds=options.pass_fds,
        ^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/home/marlonsc/.local/share/mise/installs/python/3.13.17/lib/python3.13/subprocess.py", line 1040, in __init__
    self._execute_child(args, executable, preexec_fn, close_fds,
    ~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
                        pass_fds, cwd, env,
                        ^^^^^^^^^^^^^^^^^^^
    ...<5 lines>...
                        gid, gids, uid, umask,
                        ^^^^^^^^^^^^^^^^^^^^^^
                        start_new_session, process_group)
                        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/marlonsc/.local/share/mise/installs/python/3.13.17/lib/python3.13/subprocess.py", line 1992, in _execute_child
    raise child_exception_type(errno_num, err_msg, err_filename)
FileNotFoundError: [Errno 2] No such file or directory: '/home/marlonsc/flext/.claude/worktrees/kilo-code-flext-violations-89bd05/worktrees/flext-m6igj/.venv/bin/deptry'
[Errno 2] No such file or directory: '/home/marlonsc/flext/.claude/worktrees/kilo-code-flext-violations-89bd05/worktrees/flext-m6igj/.venv/bin/deptry'
{"error":"execution error: [Errno 2] No such file or directory: '/home/marlonsc/flext/.claude/worktrees/kilo-code-flext-violations-89bd05/worktrees/flext-m6igj/.venv/bin/deptry'"}
  - Native output receipt: [deps.raw.log](file:///home/marlonsc/flext/.claude/worktrees/kilo-code-flext-violations-89bd05/worktrees/flext-m6igj/.reports/check/0594777a-edc4-467d-94c7-2e69397cd2f0/flext-m6igj/deps.raw.log)
