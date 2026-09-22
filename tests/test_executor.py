"""四种边界情况各钉死一个测试：成功、失败、超时、启动不起来。"""

import pytest

from taskforge.executor import (
    START_FAILED_EXIT_CODE,
    TIMEOUT_EXIT_CODE,
    TaskSpec,
    run_task,
)
from tests.conftest import RunPython


def test_successful_command(run_python: RunPython) -> None:
    """成功的命令：退出码 0，拿到输出，没超时。"""
    result = run_python("print('hello')")

    assert result.exit_code == 0
    assert result.stdout.strip() == "hello"
    assert result.timed_out is False
    assert result.duration_ms >= 0


def test_failing_command(run_python: RunPython) -> None:
    """命令自己失败：退出码原样记录，不抛异常。

    这条守的是 ADR 0001 的核心承诺——执行器不把失败变成异常，
    而是让调用方从 exit_code 字段里看到原始退出码。
    """
    result = run_python("import sys; sys.exit(3)")

    assert result.exit_code == 3
    assert result.timed_out is False


@pytest.mark.slow
def test_timeout_kills_the_command(run_python: RunPython) -> None:
    """超时：标记 timed_out，给专门的退出码。"""
    result = run_python("import time; time.sleep(5)", timeout=0.2)

    assert result.timed_out is True
    assert result.exit_code == TIMEOUT_EXIT_CODE


@pytest.mark.parametrize(
    "bad_cmd",
    [
        ["this-command-does-not-exist-xyz"],
        ["/dev/null"],  # 存在但不可执行
    ],
)
def test_command_cannot_start(bad_cmd: list[str]) -> None:
    """命令压根起不来：也变成结果，不抛异常。"""
    result = run_task(TaskSpec(cmd=bad_cmd))

    assert result.exit_code == START_FAILED_EXIT_CODE
    assert result.timed_out is False
    assert result.stderr != ""


@pytest.mark.slow
def test_succeeded_is_true_only_when_exit_zero_and_not_timed_out(
    run_python: RunPython,
) -> None:
    ok = run_python("pass")
    failed = run_python("import sys; sys.exit(1)")
    timed_out = run_python("import time; time.sleep(5)", timeout=0.2)

    assert ok.succeeded is True
    assert failed.succeeded is False
    assert timed_out.succeeded is False
