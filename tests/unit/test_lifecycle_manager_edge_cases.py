"""LifecycleManager 边缘情况测试.

测试覆盖：
- 错误处理路径
- 状态检查分支
- 异步方法的特殊路径
"""

from pathlib import Path

import pytest

from symphra_modules import ModuleManager
from symphra_modules.core import ModuleState
from symphra_modules.core.exceptions import ModuleNotFoundError, ModuleStateError
from symphra_modules.lifecycle.manager import LifecycleManager


def test_start_nonexistent_module() -> None:
    """测试启动不存在的模块."""
    manager = LifecycleManager()

    with pytest.raises(ModuleNotFoundError, match="模块 'nonexistent' 未创建实例"):
        manager.start_module("nonexistent")


def test_start_already_started_module(tmp_path: Path) -> None:
    """测试启动已经启动的模块."""
    module_file = tmp_path / "test.py"
    module_file.write_text(
        """
from symphra_modules import Module

class TestModule(Module):
    name = "test"
    version = "1.0.0"
    dependencies = []

    def start(self):
        pass
"""
    )

    manager = ModuleManager(tmp_path)
    manager.load("test")
    manager.start("test")

    # 再次启动，应该跳过并记录警告
    manager.start("test")

    # 验证状态仍然是STARTED
    module = manager.get_module("test")
    assert module is not None
    assert module.state == ModuleState.STARTED


def test_start_module_with_invalid_state(tmp_path: Path) -> None:
    """测试从无效状态启动模块."""
    module_file = tmp_path / "test.py"
    module_file.write_text(
        """
from symphra_modules import Module

class TestModule(Module):
    name = "test"
    version = "1.0.0"
    dependencies = []
"""
    )

    manager = ModuleManager(tmp_path)
    module = manager.load("test")

    # 手动设置为DISABLED状态
    module._state = ModuleState.DISABLED

    # 尝试启动应该失败
    with pytest.raises(ModuleStateError, match="无法启动模块"):
        manager.start("test")


def test_stop_nonexistent_module() -> None:
    """测试停止不存在的模块."""
    manager = LifecycleManager()

    with pytest.raises(ModuleNotFoundError, match="模块 'nonexistent' 未创建实例"):
        manager.stop_module("nonexistent")


def test_stop_not_started_module(tmp_path: Path) -> None:
    """测试停止未启动的模块."""
    module_file = tmp_path / "test.py"
    module_file.write_text(
        """
from symphra_modules import Module

class TestModule(Module):
    name = "test"
    version = "1.0.0"
    dependencies = []
"""
    )

    manager = ModuleManager(tmp_path)
    manager.load("test")

    # 停止未启动的模块，应该跳过并记录警告
    manager.stop("test")

    # 验证状态仍然是LOADED
    module = manager.get_module("test")
    assert module is not None
    assert module.state == ModuleState.LOADED


def test_bootstrap_nonexistent_module() -> None:
    """测试bootstrap不存在的模块."""
    manager = LifecycleManager()

    with pytest.raises(ModuleNotFoundError, match="模块 'nonexistent' 未创建实例"):
        manager.bootstrap_module("nonexistent")


def test_bootstrap_already_initialized_module(tmp_path: Path) -> None:
    """测试bootstrap已经初始化的模块."""
    module_file = tmp_path / "test.py"
    module_file.write_text(
        """
from symphra_modules import Module

class TestModule(Module):
    name = "test"
    version = "1.0.0"
    dependencies = []

    def bootstrap(self):
        pass
"""
    )

    manager = ModuleManager(tmp_path)
    manager.load("test")
    manager.bootstrap("test")

    # 再次bootstrap，应该跳过并记录警告
    manager.bootstrap("test")

    # 验证状态仍然是INITIALIZED
    module = manager.get_module("test")
    assert module is not None
    assert module.state == ModuleState.INITIALIZED


def test_bootstrap_with_invalid_state(tmp_path: Path) -> None:
    """测试从无效状态bootstrap模块."""
    module_file = tmp_path / "test.py"
    module_file.write_text(
        """
from symphra_modules import Module

class TestModule(Module):
    name = "test"
    version = "1.0.0"
    dependencies = []
"""
    )

    manager = ModuleManager(tmp_path)
    module = manager.load("test")

    # 手动设置为DISABLED状态
    module._state = ModuleState.DISABLED

    # 尝试bootstrap应该失败
    with pytest.raises(ModuleStateError, match="无法初始化模块"):
        manager.bootstrap("test")


def test_remove_instance(tmp_path: Path) -> None:
    """测试移除模块实例."""
    module_file = tmp_path / "test.py"
    module_file.write_text(
        """
from symphra_modules import Module

class TestModule(Module):
    name = "test"
    version = "1.0.0"
    dependencies = []
"""
    )

    manager = ModuleManager(tmp_path)
    manager.load("test")

    # 验证实例存在
    assert manager.get_module("test") is not None

    # 移除实例
    manager._lifecycle.remove_instance("test")

    # 验证实例已移除
    assert manager._lifecycle.get_instance("test") is None


@pytest.mark.asyncio
async def test_start_async_nonexistent_module() -> None:
    """测试异步启动不存在的模块."""
    manager = LifecycleManager()

    with pytest.raises(ModuleNotFoundError, match="模块 'nonexistent' 未创建实例"):
        await manager.start_module_async("nonexistent")


@pytest.mark.asyncio
async def test_start_async_already_started_module(tmp_path: Path) -> None:
    """测试异步启动已经启动的模块."""
    module_file = tmp_path / "test.py"
    module_file.write_text(
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

    # 再次启动，应该跳过
    await manager.start_async("test")

    # 验证状态仍然是STARTED
    module = manager.get_module("test")
    assert module is not None
    assert module.state == ModuleState.STARTED


@pytest.mark.asyncio
async def test_start_async_with_invalid_state(tmp_path: Path) -> None:
    """测试从无效状态异步启动模块."""
    module_file = tmp_path / "test.py"
    module_file.write_text(
        """
from symphra_modules import Module

class TestModule(Module):
    name = "test"
    version = "1.0.0"
    dependencies = []
"""
    )

    manager = ModuleManager(tmp_path)
    module = await manager.load_async("test")

    # 手动设置为DISABLED状态
    module._state = ModuleState.DISABLED

    # 尝试启动应该失败
    with pytest.raises(ModuleStateError, match="无法异步启动模块"):
        await manager.start_async("test")


@pytest.mark.asyncio
async def test_stop_async_nonexistent_module() -> None:
    """测试异步停止不存在的模块."""
    manager = LifecycleManager()

    with pytest.raises(ModuleNotFoundError, match="模块 'nonexistent' 未创建实例"):
        await manager.stop_module_async("nonexistent")


@pytest.mark.asyncio
async def test_stop_async_not_started_module(tmp_path: Path) -> None:
    """测试异步停止未启动的模块."""
    module_file = tmp_path / "test.py"
    module_file.write_text(
        """
from symphra_modules import Module

class TestModule(Module):
    name = "test"
    version = "1.0.0"
    dependencies = []
"""
    )

    manager = ModuleManager(tmp_path)
    await manager.load_async("test")

    # 停止未启动的模块，应该跳过
    await manager.stop_async("test")

    # 验证状态仍然是LOADED
    module = manager.get_module("test")
    assert module is not None
    assert module.state == ModuleState.LOADED
