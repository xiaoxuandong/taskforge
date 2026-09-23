"""TaskForge 最小执行器：带超时地跑一条命令，永不抛异常。

设计原则见 docs/decisions/0001-executor-never-raises.md：
成功、失败、超时、启动失败，全部收敛成同一种返回形状 TaskResult，
调用方（未来的 worker / agent loop）只需要看字段，不需要写 try/except。
"""
import json
import subprocess
import time
from dataclasses import dataclass

# 超时时使用的退出码。
# 选 124 是因为 shell 的 timeout 命令也用这个值，属于业界惯例。
TIMEOUT_EXIT_CODE = 124
# 命令压根启动不起来时使用（找不到命令、没有执行权限等）。
START_FAILED_EXIT_CODE = 127


@dataclass(frozen=True)
class TaskSpec:
    """一次要执行的命令。

    workdir 预留给未来版本：v0 阶段不实现，但字段位置先留出来，
    将来加它不需要改调用方的签名。这条决策属于课程级，
    记在学习工作区的 decisions/0002-reserve-workdir-without-implementing.md，
    不是本仓库的 docs/decisions/0002（那条讲的是 squash merge 策略）。
    """

    cmd: list[str]
    timeout: float = 30.0


@dataclass(frozen=True)
class TaskResult:
    """执行结果。成功、失败、超时共用这一种形状。"""

    exit_code: int
    stdout: str
    stderr: str
    timed_out: bool
    duration_ms: int

    @property
    def succeeded(self) -> bool:
        return self.exit_code == 0 and not self.timed_out


def run_task(spec: TaskSpec) -> TaskResult:
    """执行命令并返回结果。永不抛异常。"""
    start = time.monotonic()

    def elapsed_ms() -> int:
        return int((time.monotonic() - start) * 1000)

    try:
        completed = subprocess.run(
            spec.cmd,
            capture_output=True,
            text=True,
            timeout=spec.timeout,
        )
        return TaskResult(
            exit_code=completed.returncode,
            stdout=completed.stdout,
            stderr=completed.stderr,
            timed_out=False,
            duration_ms=elapsed_ms(),
        )

    except subprocess.TimeoutExpired as exc:
        # subprocess.run 在抛出这个异常之前，已经在内部
        # kill() 了子进程并 wait() 回收，所以这里不需要我们
        # 自己再杀一次——但只有直接子进程会被杀掉，孙进程不会
        # （第 1 课 Step 4 的实验验证过这件事）。
        return TaskResult(
            exit_code=TIMEOUT_EXIT_CODE,
            stdout=_as_text(exc.stdout),
            stderr=_as_text(exc.stderr),
            timed_out=True,
            duration_ms=elapsed_ms(),
        )

    except OSError as exc:
        # 命令找不到（FileNotFoundError）、没有执行权限等，
        # 都是 OSError 的子类，一网打尽。
        return TaskResult(
            exit_code=START_FAILED_EXIT_CODE,
            stdout="",
            stderr=str(exc),
            timed_out=False,
            duration_ms=elapsed_ms(),
        )


def _as_text(value: str | bytes | None) -> str:
    """TimeoutExpired 的 stdout/stderr 可能是 bytes 也可能是 None，统一成字符串。"""
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return value
