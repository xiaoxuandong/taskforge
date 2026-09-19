"""四种边界情况各钉死一个测试：成功、失败、超时、启动不起来。"""

import sys

from taskforge.executor import (
    START_FAILED_EXIT_CODE,
    TIMEOUT_EXIT_CODE,
    TaskSpec,
    run_task,
)


def test_successful_command() -> None:
    """成功的命令：退出码 0，拿到输出，没超时。"""
    result = run_task(TaskSpec(cmd=[sys.executable, "-c", "print('hello')"]))

    assert result.exit_code == 0
    assert result.stdout.strip() == "hello"
    assert result.timed_out is False
    assert result.duration_ms >= 0


def test_failing_command() -> None:
    """命令自己失败：退出码原样记录，不抛异常。"""
    result = run_task(TaskSpec(cmd=[sys.executable, "-c", "import sys; sys.exit(3)"]))

    assert result.exit_code == 3
    assert result.timed_out is False


def test_timeout_kills_the_command() -> None:
    """超时：标记 timed_out，给专门的退出码。"""
    result = run_task(
        TaskSpec(cmd=[sys.executable, "-c", "import time; time.sleep(5)"], timeout=0.2)
    )

    assert result.timed_out is True
    assert result.exit_code == TIMEOUT_EXIT_CODE


def test_command_not_found() -> None:
    """命令不存在：也变成结果，不抛异常。"""
    result = run_task(TaskSpec(cmd=["this-command-does-not-exist-xyz"]))

    assert result.exit_code == START_FAILED_EXIT_CODE
    assert result.timed_out is False
    assert result.stderr != ""
