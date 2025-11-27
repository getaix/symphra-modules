"""ModuleManager 异步操作测试.

测试覆盖：
- load_all_async
- start_all_async, stop_all_async
- 异步错误处理
"""

from pathlib import Path

import pytest

from symphra_modules import ModuleManager
from symphra_modules.core import ModuleState


@pytest.mark.asyncio
async def test_load_all_async(tmp_path: Path) -> None:
    """测试异步批量加载."""
    # 创建多个模块
    for i in range(3):
        (tmp_path / f"module{i}.py").write_text(
            f"""
from symphra_modules import Module

class Module{i}(Module):
    name = "module{i}"
    version = "1.0.0"
    dependencies = []
"""
        )

    manager = ModuleManager(tmp_path)
    modules = await manager.load_all_async()

    # 验证所有模块都已加载
    assert len(modules) == 3
    for i in range(3):
        assert f"module{i}" in modules


@pytest.mark.asyncio
async def test_load_all_async_with_force(tmp_path: Path) -> None:
    """测试异步强制重新加载."""
    (tmp_path / "test.py").write_text(
        """
from symphra_modules import Module

class TestModule(Module):
    name = "test"
    version = "1.0.0"
    dependencies = []
"""
    )

    manager = ModuleManager(tmp_path)

    # 第一次加载
    modules1 = await manager.load_all_async()
    instance1 = modules1["test"]

    # 强制重新加载
    modules2 = await manager.load_all_async(force=True)
    instance2 = modules2["test"]

    # 应该是不同的实例
    assert instance1 is not instance2


@pytest.mark.asyncio
async def test_start_all_async(tmp_path: Path) -> None:
    """测试异步批量启动."""
    (tmp_path / "test.py").write_text(
        """
from symphra_modules import Module

class TestModule(Module):
    name = "test"
    version = "1.0.0"
    dependencies = []

    def __init__(self):
        super().__init__()
        self.started = False

    async def start_async(self):
        self.started = True
"""
    )

    manager = ModuleManager(tmp_path)
    await manager.load_all_async()
    await manager.start_all_async()

    # 验证模块已启动
    module = manager.get_module("test")
    assert module is not None
    assert module.state == ModuleState.STARTED


@pytest.mark.asyncio
async def test_stop_all_async(tmp_path: Path) -> None:
    """测试异步批量停止."""
    (tmp_path / "test.py").write_text(
        """
from symphra_modules import Module

class TestModule(Module):
    name = "test"
    version = "1.0.0"
    dependencies = []

    def __init__(self):
        super().__init__()
        self.stopped = False

    async def start_async(self):
        pass

    async def stop_async(self):
        self.stopped = True
"""
    )

    manager = ModuleManager(tmp_path)
    await manager.load_all_async()
    await manager.start_all_async()

    # 停止所有模块
    await manager.stop_all_async()

    # 验证模块已停止
    started_modules = manager.list_started_modules()
    assert len(started_modules) == 0


@pytest.mark.asyncio
async def test_async_with_dependencies(tmp_path: Path) -> None:
    """测试异步操作处理依赖关系."""
    # 创建有依赖的模块
    (tmp_path / "base.py").write_text(
        """
from symphra_modules import Module

class BaseModule(Module):
    name = "base"
    version = "1.0.0"
    dependencies = []

    async def start_async(self):
        pass
"""
    )

    (tmp_path / "dependent.py").write_text(
        """
from symphra_modules import Module

class DependentModule(Module):
    name = "dependent"
    version = "1.0.0"
    dependencies = ["base"]

    async def start_async(self):
        pass
"""
    )

    manager = ModuleManager(tmp_path)
    await manager.load_all_async()
    await manager.start_all_async()

    # 验证两个模块都已启动
    assert "base" in manager.list_started_modules()
    assert "dependent" in manager.list_started_modules()


@pytest.mark.asyncio
async def test_async_start_single_module(tmp_path: Path) -> None:
    """测试异步启动单个模块."""
    (tmp_path / "test.py").write_text(
        """
from symphra_modules import Module

class TestModule(Module):
    name = "test"
    version = "1.0.0"
    dependencies = []

    async def start_async(self):
        pass
"""
    )

    manager = ModuleManager(tmp_path)
    await manager.load_async("test")
    await manager.start_async("test")

    # 验证模块已启动
    module = manager.get_module("test")
    assert module is not None
    assert module.state == ModuleState.STARTED


@pytest.mark.asyncio
async def test_async_stop_single_module(tmp_path: Path) -> None:
    """测试异步停止单个模块."""
    (tmp_path / "test.py").write_text(
        """
from symphra_modules import Module

class TestModule(Module):
    name = "test"
    version = "1.0.0"
    dependencies = []

    async def start_async(self):
        pass

    async def stop_async(self):
        pass
"""
    )

    manager = ModuleManager(tmp_path)
    await manager.load_async("test")
    await manager.start_async("test")
    await manager.stop_async("test")

    # 验证模块已停止
    module = manager.get_module("test")
    assert module is not None
    assert module.state == ModuleState.STOPPED


@pytest.mark.asyncio
async def test_async_with_sync_fallback(tmp_path: Path) -> None:
    """测试异步操作对同步模块的回退."""
    # 创建只有同步方法的模块
    (tmp_path / "test.py").write_text(
        """
from symphra_modules import Module

class TestModule(Module):
    name = "test"
    version = "1.0.0"
    dependencies = []

    def start(self):
        pass

    def stop(self):
        pass
"""
    )

    manager = ModuleManager(tmp_path)
    await manager.load_async("test")
    await manager.start_async("test")

    # 验证同步模块也能用异步方法启动
    module = manager.get_module("test")
    assert module is not None
    assert module.state == ModuleState.STARTED


@pytest.mark.asyncio
async def test_load_all_async_error_handling(tmp_path: Path) -> None:
    """测试异步加载时的错误处理."""
    # 创建一个正常模块和一个有问题的模块
    (tmp_path / "good.py").write_text(
        """
from symphra_modules import Module

class GoodModule(Module):
    name = "good"
    version = "1.0.0"
    dependencies = []
"""
    )

    (tmp_path / "bad.py").write_text(
        """
from symphra_modules import Module

class BadModule(Module):
    name = "bad"
    version = "1.0.0"
    dependencies = ["nonexistent"]  # 依赖不存在
"""
    )

    manager = ModuleManager(tmp_path)

    # load_all_async 应该记录错误但不抛异常
    modules = await manager.load_all_async()

    # 好的模块应该加载成功
    assert "good" in modules


@pytest.mark.asyncio
async def test_start_all_async_error_handling(tmp_path: Path) -> None:
    """测试异步启动时的错误处理."""
    (tmp_path / "error.py").write_text(
        """
from symphra_modules import Module

class ErrorModule(Module):
    name = "error"
    version = "1.0.0"
    dependencies = []

    async def start_async(self):
        raise RuntimeError("Start error")
"""
    )

    manager = ModuleManager(tmp_path)
    await manager.load_all_async()

    # start_all_async 应该记录错误但不抛异常
    await manager.start_all_async()

    # 模块状态应该不是 STARTED
    module = manager.get_module("error")
    assert module is not None
    assert module.state != ModuleState.STARTED


@pytest.mark.asyncio
async def test_stop_all_async_error_handling(tmp_path: Path) -> None:
    """测试异步停止时的错误处理."""
    (tmp_path / "error.py").write_text(
        """
from symphra_modules import Module

class ErrorModule(Module):
    name = "error"
    version = "1.0.0"
    dependencies = []

    async def start_async(self):
        pass

    async def stop_async(self):
        raise RuntimeError("Stop error")
"""
    )

    manager = ModuleManager(tmp_path)
    await manager.load_all_async()
    await manager.start_all_async()

    # stop_all_async 应该记录错误但不抛异常
    await manager.stop_all_async()

    # 尽管有错误，也不应该抛异常
    # （错误被记录到日志）
