"""异步模块测试."""

import asyncio
import tempfile
from pathlib import Path

import pytest

from symphra_modules import (
    Module,
    ModuleManager,
    call_module_method,
    is_async_module,
)


class AsyncTestModule(Module):
    """异步测试模块."""

    name = "async_test"
    version = "1.0.0"
    dependencies = []

    def __init__(self) -> None:
        super().__init__()
        self.async_started = False
        self.async_stopped = False

    async def start_async(self) -> None:
        """异步启动."""
        await asyncio.sleep(0.01)  # 模拟异步操作
        self.async_started = True

    async def stop_async(self) -> None:
        """异步停止."""
        await asyncio.sleep(0.01)  # 模拟异步操作
        self.async_stopped = True


class SyncTestModule(Module):
    """同步测试模块."""

    name = "sync_test"
    version = "1.0.0"
    dependencies = []

    def __init__(self) -> None:
        super().__init__()
        self.started = False
        self.stopped = False

    def start(self) -> None:
        """同步启动."""
        self.started = True

    def stop(self) -> None:
        """同步停止."""
        self.stopped = True


@pytest.mark.asyncio
async def test_async_module_detection() -> None:
    """测试异步模块检测."""
    async_module = AsyncTestModule()
    sync_module = SyncTestModule()

    assert is_async_module(async_module) is True
    assert is_async_module(sync_module) is False


@pytest.mark.asyncio
async def test_call_module_method() -> None:
    """测试调用模块方法."""
    async_module = AsyncTestModule()
    sync_module = SyncTestModule()

    # 测试异步方法调用
    await call_module_method(async_module, "start_async")
    assert async_module.async_started is True

    # 测试同步方法调用
    await call_module_method(sync_module, "start")
    assert sync_module.started is True


@pytest.mark.asyncio
async def test_async_module_lifecycle() -> None:
    """测试异步模块生命周期."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建模块文件
        async_module_code = '''
from symphra_modules import Module

class AsyncTestModule(Module):
    name = "async_test"
    version = "1.0.0"
    dependencies = []

    def __init__(self) -> None:
        super().__init__()
        self.async_started = False
        self.async_stopped = False

    async def start_async(self) -> None:
        """异步启动."""
        import asyncio
        await asyncio.sleep(0.01)  # 模拟异步操作
        self.async_started = True

    async def stop_async(self) -> None:
        """异步停止."""
        import asyncio
        await asyncio.sleep(0.01)  # 模拟异步操作
        self.async_stopped = True
'''
        Path(tmpdir, "async_test.py").write_text(async_module_code)

        # 创建模块管理器
        manager = ModuleManager(tmpdir)

        # 异步加载模块
        module = await manager.load_async("async_test")
        assert module is not None

        # 测试异步启动
        await manager.start_async("async_test")
        assert module._state.name == "STARTED"  # type: ignore

        # 测试异步停止
        await manager.stop_async("async_test")
        assert module._state.name == "STOPPED"  # type: ignore


@pytest.mark.asyncio
async def test_mixed_sync_async_modules() -> None:
    """测试混合同步异步模块."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建异步模块文件
        async_module_code = '''
from symphra_modules import Module

class AsyncTestModule(Module):
    name = "async_test"
    version = "1.0.0"
    dependencies = []

    def __init__(self) -> None:
        super().__init__()
        self.async_started = False
        self.async_stopped = False

    async def start_async(self) -> None:
        """异步启动."""
        import asyncio
        await asyncio.sleep(0.01)  # 模拟异步操作
        self.async_started = True

    async def stop_async(self) -> None:
        """异步停止."""
        import asyncio
        await asyncio.sleep(0.01)  # 模拟异步操作
        self.async_stopped = True
'''
        Path(tmpdir, "async_test.py").write_text(async_module_code)

        # 创建同步模块文件
        sync_module_code = '''
from symphra_modules import Module

class SyncTestModule(Module):
    name = "sync_test"
    version = "1.0.0"
    dependencies = []

    def __init__(self) -> None:
        super().__init__()
        self.started = False
        self.stopped = False

    def start(self) -> None:
        """同步启动."""
        self.started = True

    def stop(self) -> None:
        """同步停止."""
        self.stopped = True
'''
        Path(tmpdir, "sync_test.py").write_text(sync_module_code)

        # 创建模块管理器
        manager = ModuleManager(tmpdir)

        # 测试异步模块
        await manager.load_async("async_test")
        await manager.start_async("async_test")
        async_module = manager.get_module("async_test")
        assert async_module is not None
        assert async_module._state.name == "STARTED"  # type: ignore

        # 测试同步模块
        manager.load("sync_test")
        manager.start("sync_test")
        sync_module = manager.get_module("sync_test")
        assert sync_module is not None
        assert sync_module._state.name == "STARTED"  # type: ignore
