"""ModuleManager 错误处理测试.

测试覆盖：
- 各种错误处理路径
- 异常情况下的行为
- 边缘情况处理
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from symphra_modules import ModuleManager
from symphra_modules.core import ModuleState
from symphra_modules.core.exceptions import ModuleNotFoundError


def test_load_nonexistent_module(tmp_path: Path) -> None:
    """测试加载不存在的模块."""
    manager = ModuleManager(tmp_path)

    # 应该抛出DependencyError（因为模块不在available_modules中）
    from symphra_modules.core.exceptions import DependencyError

    with pytest.raises(DependencyError, match="依赖错误"):
        manager.load("nonexistent")


def test_stop_unloaded_module(tmp_path: Path) -> None:
    """测试停止未加载的模块."""
    manager = ModuleManager(tmp_path)

    with pytest.raises(ModuleNotFoundError, match="未加载"):
        manager.stop("nonexistent")


@pytest.mark.asyncio
async def test_stop_async_unloaded_module(tmp_path: Path) -> None:
    """测试异步停止未加载的模块."""
    manager = ModuleManager(tmp_path)

    with pytest.raises(ModuleNotFoundError, match="未加载"):
        await manager.stop_async("nonexistent")


def test_unload_unloaded_module(tmp_path: Path) -> None:
    """测试卸载未加载的模块."""
    manager = ModuleManager(tmp_path)

    with pytest.raises(ModuleNotFoundError, match="未加载"):
        manager.unload("nonexistent")


def test_start_with_dependency_resolution_error(tmp_path: Path) -> None:
    """测试依赖解析失败时的启动."""
    # 创建一个模块
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

    # 模拟依赖解析失败
    with patch.object(
        manager._resolver.get_graph(), "topological_sort", side_effect=Exception("Mocked error")
    ):
        # 即使解析失败，也应该能启动当前模块
        manager.start("test")

    # 验证模块已启动
    module = manager.get_module("test")
    assert module is not None
    assert module.state == ModuleState.STARTED


@pytest.mark.asyncio
async def test_start_async_with_dependency_resolution_error(tmp_path: Path) -> None:
    """测试依赖解析失败时的异步启动."""
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

    # 模拟依赖解析失败
    with patch.object(
        manager._resolver.get_graph(), "topological_sort", side_effect=Exception("Mocked error")
    ):
        # 即使解析失败，也应该能启动当前模块
        await manager.start_async("test")

    # 验证模块已启动
    module = manager.get_module("test")
    assert module is not None
    assert module.state == ModuleState.STARTED


@pytest.mark.asyncio
async def test_start_async_unloaded_module(tmp_path: Path) -> None:
    """测试异步启动未加载的模块."""
    manager = ModuleManager(tmp_path)

    with pytest.raises(ModuleNotFoundError, match="未加载"):
        await manager.start_async("nonexistent")


def test_reload_without_loader(tmp_path: Path) -> None:
    """测试在没有loader的情况下reload."""
    manager = ModuleManager(tmp_path)

    # 手动设置loader为None
    manager._loader = None  # type: ignore

    # reload应该抛出错误或安全处理
    with pytest.raises((AttributeError, Exception)):
        manager.reload()


def test_start_all_with_some_failures(tmp_path: Path) -> None:
    """测试批量启动时部分模块失败."""
    # 创建多个模块，其中一个会失败
    (tmp_path / "good1.py").write_text(
        """
from symphra_modules import Module

class GoodModule1(Module):
    name = "good1"
    version = "1.0.0"
    dependencies = []

    def start(self):
        pass
"""
    )

    (tmp_path / "bad.py").write_text(
        """
from symphra_modules import Module

class BadModule(Module):
    name = "bad"
    version = "1.0.0"
    dependencies = []

    def start(self):
        raise RuntimeError("Start failed")
"""
    )

    (tmp_path / "good2.py").write_text(
        """
from symphra_modules import Module

class GoodModule2(Module):
    name = "good2"
    version = "1.0.0"
    dependencies = []

    def start(self):
        pass
"""
    )

    manager = ModuleManager(tmp_path)
    manager.load_all()

    # start_all应该记录错误但不抛异常
    manager.start_all()

    # 验证至少有一个模块启动失败
    bad = manager.get_module("bad")
    assert bad is not None
    # 坏的模块状态不应该是STARTED
    assert bad.state != ModuleState.STARTED


def test_disable_without_state_store(tmp_path: Path) -> None:
    """测试在没有state_store的情况下disable模块."""
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
    manager.load("test")

    # disable应该正常工作即使没有state_store
    manager.disable("test")

    module = manager.get_module("test")
    assert module is not None
    assert module.state == ModuleState.DISABLED


def test_enable_disabled_module_without_state_store(tmp_path: Path) -> None:
    """测试在没有state_store的情况下enable模块."""
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
    manager.load("test")
    manager.disable("test")

    # enable应该正常工作即使没有state_store
    manager.enable("test")

    module = manager.get_module("test")
    assert module is not None
    assert module.state == ModuleState.INSTALLED


def test_get_module_info_nonexistent_module(tmp_path: Path) -> None:
    """测试获取不存在模块的信息."""
    manager = ModuleManager(tmp_path)

    # get_module_info对于不存在的模块会抛出ModuleNotFoundError
    with pytest.raises(ModuleNotFoundError, match="模块不存在"):
        manager.get_module_info("nonexistent")


def test_list_started_modules_with_stopped_modules(tmp_path: Path) -> None:
    """测试列出已启动模块（包含已停止的模块）."""
    (tmp_path / "test1.py").write_text(
        """
from symphra_modules import Module

class TestModule1(Module):
    name = "test1"
    version = "1.0.0"
    dependencies = []

    def start(self):
        pass

    def stop(self):
        pass
"""
    )

    (tmp_path / "test2.py").write_text(
        """
from symphra_modules import Module

class TestModule2(Module):
    name = "test2"
    version = "1.0.0"
    dependencies = []

    def start(self):
        pass
"""
    )

    manager = ModuleManager(tmp_path)
    manager.load_all()
    manager.start_all()

    # 停止一个模块
    manager.stop("test1")

    # 只有test2应该在启动列表中
    started = manager.list_started_modules()
    assert "test2" in started
    assert "test1" not in started


def test_validate_module_name_with_special_chars(tmp_path: Path) -> None:
    """测试包含特殊字符的模块名验证."""
    manager = ModuleManager(tmp_path)

    # 测试包含路径分隔符
    with pytest.raises(ValueError, match="包含非法字符"):
        manager.load("test/module")

    # 测试包含反斜杠
    with pytest.raises(ValueError, match="包含非法字符"):
        manager.load("test\\module")

    # 测试包含空格
    with pytest.raises(ValueError, match="包含非法字符"):
        manager.load("test module")


@pytest.mark.asyncio
async def test_load_all_async_with_ignored_modules(tmp_path: Path) -> None:
    """测试异步加载所有模块，包含被忽略的模块."""
    (tmp_path / "test1.py").write_text(
        """
from symphra_modules import Module

class TestModule1(Module):
    name = "test1"
    version = "1.0.0"
    dependencies = []
"""
    )

    (tmp_path / "test2.py").write_text(
        """
from symphra_modules import Module

class TestModule2(Module):
    name = "test2"
    version = "1.0.0"
    dependencies = []
"""
    )

    manager = ModuleManager(tmp_path)

    # 忽略一个模块
    manager.ignore_module("test1")

    # 异步加载所有模块
    modules = await manager.load_all_async()

    # 只应该加载test2
    assert "test2" in modules
    assert "test1" not in modules


def test_bootstrap_with_dependencies(tmp_path: Path) -> None:
    """测试bootstrap有依赖的模块."""
    (tmp_path / "base.py").write_text(
        """
from symphra_modules import Module

class BaseModule(Module):
    name = "base"
    version = "1.0.0"
    dependencies = []

    def bootstrap(self):
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

    def bootstrap(self):
        pass
"""
    )

    manager = ModuleManager(tmp_path)
    manager.load_all()

    # Bootstrap依赖模块
    manager.bootstrap("dependent")

    # 验证两个模块都已初始化
    base = manager.get_module("base")
    dependent = manager.get_module("dependent")

    assert base is not None
    assert dependent is not None
    assert dependent.state == ModuleState.INITIALIZED
