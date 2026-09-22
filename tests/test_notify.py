from taskforge.notify import notify_task_done


def test_notify_writes_failure_status() -> None:
    lines: list[str] = []
    notify_task_done("t1", success=False, now=lambda: 1000.0, write_line=lines.append)

    assert lines == ["[1000.0] task t1 finished, success=False\n"]


def test_notify_writes_success_status() -> None:
    lines: list[str] = []
    notify_task_done("t2", success=True, now=lambda: 2000.0, write_line=lines.append)

    assert lines == ["[2000.0] task t2 finished, success=True\n"]
