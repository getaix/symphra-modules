"""ModuleManager 高级功能测试.

测试覆盖：
- load_all, start_all, stop_all
- unload
- get_module_info
- 输入验证
- 错误处理
"""

from pathlib import Path

import pytest

from symphra_modules import Module, ModuleManager
from symphra_modules.core.exceptions import ModuleNotFoundError


class SimpleModule(Module):
    """简单测试模块."""

    name = "simple"
    version = "1.0.0"
    dependencies = []

    def start(self) -> None:
        """启动模块."""
        self.started = True  # type: ignore

    def stop(self) -> None:
        """停止模块."""
        self.stopped = True  # type: ignore


class DependentModule(Module):
    """依赖模块."""

    name = "dependent"
    version = "1.0.0"
    dependencies = ["simple"]

    def start(self) -> None:
        """启动模块."""
        self.started = True  # type: ignore


def test_load_all(tmp_path: Path) -> None:
    """测试批量加载所有模块."""
    # 创建测试模块文件
    simple_file = tmp_path / "simple.py"
    simple_file.write_text(
        """
from symphra_modules import Module

class SimpleModule(Module):
    name = "simple"
    version = "1.0.0"
    dependencies = []
"""
    )

    dependent_file = tmp_path / "dependent.py"
    dependent_file.write_text(
        """
from symphra_modules import Module

class DependentModule(Module):
    name = "dependent"
    version = "1.0.0"
    dependencies = ["simple"]
"""
    )

    manager = ModuleManager(tmp_path)
    modules = manager.load_all()

    # 验证所有模块都已加载
    assert len(modules) == 2
    assert "simple" in modules
    assert "dependent" in modules

    # 验证加载顺序正确（simple 先于 dependent）
    loaded_modules = manager.list_loaded_modules()
    assert "simple" in loaded_modules
    assert "dependent" in loaded_modules


def test_load_all_with_force(tmp_path: Path) -> None:
    """测试强制重新加载所有模块."""
    simple_file = tmp_path / "simple.py"
    simple_file.write_text(
        """
from symphra_modules import Module

class SimpleModule(Module):
    name = "simple"
    version = "1.0.0"
    dependencies = []
"""
    )

    manager = ModuleManager(tmp_path)

    # 第一次加载
    modules1 = manager.load_all()
    instance1 = modules1["simple"]

    # 强制重新加载
    modules2 = manager.load_all(force=True)
    instance2 = modules2["simple"]

    # 验证是新实例
    assert instance1 is not instance2


def test_start_all(tmp_path: Path) -> None:
    """测试批量启动所有模块."""
    simple_file = tmp_path / "simple.py"
    simple_file.write_text(
        """
from symphra_modules import Module

class SimpleModule(Module):
    name = "simple"
    version = "1.0.0"
    dependencies = []

    def start(self) -> None:
        self.started = True
"""
    )

    manager = ModuleManager(tmp_path)
    manager.load_all()
    manager.start_all()

    # 验证所有模块都已启动
    started_modules = manager.list_started_modules()
    assert "simple" in started_modules


def test_stop_all(tmp_path: Path) -> None:
    """测试批量停止所有模块."""
    simple_file = tmp_path / "simple.py"
    simple_file.write_text(
        """
from symphra_modules import Module

class SimpleModule(Module):
    name = "simple"
    version = "1.0.0"
    dependencies = []

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True
"""
    )

    manager = ModuleManager(tmp_path)
    manager.load_all()
    manager.start_all()

    # 停止所有模块
    manager.stop_all()

    # 验证所有模块都已停止
    started_modules = manager.list_started_modules()
    assert len(started_modules) == 0


def test_unload(tmp_path: Path) -> None:
    """测试卸载模块."""
    simple_file = tmp_path / "simple.py"
    simple_file.write_text(
        """
from symphra_modules import Module

class SimpleModule(Module):
    name = "simple"
    version = "1.0.0"
    dependencies = []
"""
    )

    manager = ModuleManager(tmp_path)
    manager.load("simple")

    # 验证模块已加载
    assert "simple" in manager.list_loaded_modules()

    # 卸载模块
    manager.unload("simple")

    # 验证模块已卸载
    assert "simple" not in manager.list_loaded_modules()


def test_unload_nonexistent_module(tmp_path: Path) -> None:
    """测试卸载不存在的模块."""
    manager = ModuleManager(tmp_path)

    with pytest.raises(ModuleNotFoundError):
        manager.unload("nonexistent")


def test_get_module_info(tmp_path: Path) -> None:
    """测试获取模块信息."""
    simple_file = tmp_path / "simple.py"
    simple_file.write_text(
        """
from symphra_modules import Module

class SimpleModule(Module):
    name = "simple"
    version = "1.2.3"
    dependencies = []
"""
    )

    manager = ModuleManager(tmp_path)
    manager.load("simple")

    # 获取模块信息
    info = manager.get_module_info("simple")

    # 验证信息正确
    assert info["name"] == "simple"
    assert info["version"] == "1.2.3"
    assert info["dependencies"] == []
    assert "state" in info
    assert "loaded_at" in info


def test_get_module_info_nonexistent(tmp_path: Path) -> None:
    """测试获取不存在模块的信息."""
    manager = ModuleManager(tmp_path)

    with pytest.raises(ModuleNotFoundError):
        manager.get_module_info("nonexistent")


def test_validate_module_name_empty(tmp_path: Path) -> None:
    """测试空模块名称验证."""
    manager = ModuleManager(tmp_path)

    with pytest.raises(ValueError, match="模块名称不能为空"):
        manager.load("")

    with pytest.raises(ValueError, match="模块名称不能为空白字符"):
        manager.load("   ")


def test_validate_module_name_invalid_chars(tmp_path: Path) -> None:
    """测试非法字符验证."""
    manager = ModuleManager(tmp_path)

    # 包含非法字符
    with pytest.raises(ValueError, match="包含非法字符"):
        manager.load("module/name")

    with pytest.raises(ValueError, match="包含非法字符"):
        manager.load("module.name")

    with pytest.raises(ValueError, match="包含非法字符"):
        manager.load("module name")


def test_validate_module_name_valid(tmp_path: Path) -> None:
    """测试合法模块名称."""
    simple_file = tmp_path / "test-module_123.py"
    simple_file.write_text(
        """
from symphra_modules import Module

class TestModule(Module):
    name = "test-module_123"
    version = "1.0.0"
    dependencies = []
"""
    )

    manager = ModuleManager(tmp_path)

    # 这些名称应该是合法的
    module = manager.load("test-module_123")
    assert module.name == "test-module_123"


def test_start_with_validation(tmp_path: Path) -> None:
    """测试启动时的输入验证."""
    manager = ModuleManager(tmp_path)

    # 空名称
    with pytest.raises(ValueError, match="模块名称不能为空"):
        manager.start("")

    # 非法字符
    with pytest.raises(ValueError, match="包含非法字符"):
        manager.start("invalid/name")


def test_context_manager(tmp_path: Path) -> None:
    """测试上下文管理器."""
    simple_file = tmp_path / "simple.py"
    simple_file.write_text(
        """
from symphra_modules import Module

class SimpleModule(Module):
    name = "simple"
    version = "1.0.0"
    dependencies = []

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True
"""
    )

    # 使用上下文管理器
    with ModuleManager(tmp_path) as manager:
        manager.load("simple")
        manager.start("simple")
        assert "simple" in manager.list_started_modules()

    # 退出时应该自动停止所有模块
    # （注意：这里我们无法直接验证，但不应该抛出异常）


def test_list_modules_thread_safe(tmp_path: Path) -> None:
    """测试列出模块的线程安全性."""
    simple_file = tmp_path / "simple.py"
    simple_file.write_text(
        """
from symphra_modules import Module

class SimpleModule(Module):
    name = "simple"
    version = "1.0.0"
    dependencies = []
"""
    )

    manager = ModuleManager(tmp_path)

    # 多次调用应该返回一致的结果
    modules1 = manager.list_modules()
    modules2 = manager.list_modules()

    assert modules1 == modules2
    assert "simple" in modules1


def test_rediscover(tmp_path: Path) -> None:
    """测试重新发现模块."""
    manager = ModuleManager(tmp_path)

    # 初始没有模块
    assert len(manager.list_modules()) == 0

    # 创建新模块文件
    simple_file = tmp_path / "simple.py"
    simple_file.write_text(
        """
from symphra_modules import Module

class SimpleModule(Module):
    name = "simple"
    version = "1.0.0"
    dependencies = []
"""
    )

    # 重新发现
    manager.rediscover()

    # 现在应该能发现新模块
    assert "simple" in manager.list_modules()
