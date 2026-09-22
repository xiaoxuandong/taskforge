"""测试共用的 fixture。

pytest 会自动发现 conftest.py，不需要 import：
放在这里的 fixture，tests/ 下所有测试文件都能直接用。
"""

import sys
from collections.abc import Callable

import pytest

from taskforge.executor import TaskResult, TaskSpec, run_task

# run_python fixture 的类型。
# `...` 表示「参数不做检查」——因为 _run 带默认参数 timeout，
# 用 Callable 精确描述会很啰嗦，这里只钉死返回类型 TaskResult。
RunPython = Callable[..., TaskResult]


@pytest.fixture
def run_python() -> RunPython:
    """返回一个函数：传一段 Python 代码字符串，跑它并返回 TaskResult。

    用当前解释器（sys.executable）而不是写死 "python"，
    这样在任何虚拟环境 / CI 机器上都跑的是同一个 Python。
    """

    def _run(code: str, timeout: float = 30.0) -> TaskResult:
        return run_task(TaskSpec(cmd=[sys.executable, "-c", code], timeout=timeout))

    return _run
