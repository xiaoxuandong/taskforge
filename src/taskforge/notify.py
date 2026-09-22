import time
from collections.abc import Callable


def notify_task_done(
    task_id: str,
    success: bool,
    *,
    now: Callable[[], float] = time.time,
    write_line: Callable[[str], None] | None = None,
) -> None:
    """任务跑完了，记一条日志。"""
    timestamp = now()
    line = f"[{timestamp}] task {task_id} finished, success={success}\n"
    if write_line is not None:
        write_line(line)
    else:
        with open("/tmp/taskforge-demo.log", "a") as f:
            f.write(line)
