"""ModuleManager 生命周期管理测试.

测试覆盖：
- install, uninstall
- enable, disable
- bootstrap
- ignore_module, unignore_module
"""

from pathlib import Path

import pytest

from symphra_modules import Module, ModuleManager
from symphra_modules.core import FileStateStore, ModuleState
from symphra_modules.core.exceptions import ModuleNotFoundError


class TestModule(Module):
    """测试模块."""

    name = "test_module"
    version = "1.0.0"
    dependencies = []

    def __init__(self) -> None:
        """初始化."""
        super().__init__()
        self.started = False
        self.stopped = False
        self.bootstrapped = False

    def bootstrap(self) -> None:
        """Bootstrap."""
        self.bootstrapped = True

    def start(self) -> None:
        """启动."""
        self.started = True

    def stop(self) -> None:
        """停止."""
        self.stopped = True


def test_bootstrap_module(tmp_path: Path) -> None:
    """测试 bootstrap 模块."""
    # 创建测试模块文件
    module_file = tmp_path / "test_module.py"
    module_file.write_text(
        """
from symphra_modules import Module

class TestModule(Module):
    name = "test_module"
    version = "1.0.0"
    dependencies = []

    def __init__(self):
        super().__init__()
        self.bootstrapped = False

    def bootstrap(self):
        self.bootstrapped = True
"""
    )

    manager = ModuleManager(tmp_path)
    module = manager.load("test_module")

    # Bootstrap 模块
    manager.bootstrap("test_module")

    # 验证状态
    assert module.state == ModuleState.INITIALIZED
    assert module.bootstrapped  # type: ignore


def test_bootstrap_nonexistent_module(tmp_path: Path) -> None:
    """测试 bootstrap 不存在的模块."""
    manager = ModuleManager(tmp_path)

    with pytest.raises(ModuleNotFoundError):
        manager.bootstrap("nonexistent")


def test_install_module(tmp_path: Path) -> None:
    """测试安装模块."""
    module_file = tmp_path / "test_module.py"
    module_file.write_text(
        """
from symphra_modules import Module

class TestModule(Module):
    name = "test_module"
    version = "1.0.0"
    dependencies = []
"""
    )

    manager = ModuleManager(tmp_path)

    # 安装模块（会自动加载）
    manager.install("test_module")

    # 验证模块已加载且状态正确
    module = manager.get_module("test_module")
    assert module is not None
    assert module.state in [ModuleState.LOADED, ModuleState.INSTALLED]


def test_install_nonexistent_module(tmp_path: Path) -> None:
    """测试安装不存在的模块."""
    manager = ModuleManager(tmp_path)

    with pytest.raises(ModuleNotFoundError):
        manager.install("nonexistent")


def test_uninstall_module(tmp_path: Path) -> None:
    """测试卸载模块."""
    module_file = tmp_path / "test_module.py"
    module_file.write_text(
        """
from symphra_modules import Module

class TestModule(Module):
    name = "test_module"
    version = "1.0.0"
    dependencies = []
"""
    )

    manager = ModuleManager(tmp_path)
    manager.load("test_module")

    # 卸载模块
    manager.uninstall("test_module")

    # 验证模块已移除
    assert manager.get_module("test_module") is None


def test_uninstall_running_module(tmp_path: Path) -> None:
    """测试卸载正在运行的模块（应该先停止）."""
    module_file = tmp_path / "test_module.py"
    module_file.write_text(
        """
from symphra_modules import Module

class TestModule(Module):
    name = "test_module"
    version = "1.0.0"
    dependencies = []

    def start(self):
        pass

    def stop(self):
        pass
"""
    )

    manager = ModuleManager(tmp_path)
    manager.load("test_module")
    manager.start("test_module")

    # 卸载运行中的模块
    manager.uninstall("test_module")

    # 验证模块已移除
    assert manager.get_module("test_module") is None


def test_disable_module(tmp_path: Path) -> None:
    """测试禁用模块."""
    module_file = tmp_path / "test_module.py"
    module_file.write_text(
        """
from symphra_modules import Module

class TestModule(Module):
    name = "test_module"
    version = "1.0.0"
    dependencies = []
"""
    )

    manager = ModuleManager(tmp_path)
    module = manager.load("test_module")

    # 禁用模块
    manager.disable("test_module")

    # 验证状态
    assert module.state == ModuleState.DISABLED


def test_disable_running_module(tmp_path: Path) -> None:
    """测试禁用正在运行的模块（应该先停止）."""
    module_file = tmp_path / "test_module.py"
    module_file.write_text(
        """
from symphra_modules import Module

class TestModule(Module):
    name = "test_module"
    version = "1.0.0"
    dependencies = []

    def start(self):
        pass

    def stop(self):
        pass
"""
    )

    manager = ModuleManager(tmp_path)
    module = manager.load("test_module")
    manager.start("test_module")

    # 禁用运行中的模块
    manager.disable("test_module")

    # 验证状态
    assert module.state == ModuleState.DISABLED


def test_enable_disabled_module(tmp_path: Path) -> None:
    """测试启用被禁用的模块."""
    module_file = tmp_path / "test_module.py"
    module_file.write_text(
        """
from symphra_modules import Module

class TestModule(Module):
    name = "test_module"
    version = "1.0.0"
    dependencies = []
"""
    )

    manager = ModuleManager(tmp_path)
    module = manager.load("test_module")

    # 先禁用
    manager.disable("test_module")
    assert module.state == ModuleState.DISABLED

    # 再启用
    manager.enable("test_module")
    assert module.state == ModuleState.INSTALLED


def test_ignore_module(tmp_path: Path) -> None:
    """测试忽略模块."""
    # 创建两个模块
    (tmp_path / "module1.py").write_text(
        """
from symphra_modules import Module

class Module1(Module):
    name = "module1"
    version = "1.0.0"
    dependencies = []
"""
    )
    (tmp_path / "module2.py").write_text(
        """
from symphra_modules import Module

class Module2(Module):
    name = "module2"
    version = "1.0.0"
    dependencies = []
"""
    )

    manager = ModuleManager(tmp_path)

    # 初始应该发现两个模块
    assert len(manager.list_modules()) == 2

    # 忽略一个模块
    manager.ignore_module("module1")

    # 现在应该只有一个模块
    modules = manager.list_modules()
    assert len(modules) == 1
    assert "module2" in modules
    assert "module1" not in modules


def test_unignore_module(tmp_path: Path) -> None:
    """测试取消忽略模块."""
    (tmp_path / "test_module.py").write_text(
        """
from symphra_modules import Module

class TestModule(Module):
    name = "test_module"
    version = "1.0.0"
    dependencies = []
"""
    )

    manager = ModuleManager(tmp_path)

    # 先忽略
    manager.ignore_module("test_module")
    assert "test_module" not in manager.list_modules()

    # 取消忽略
    manager.unignore_module("test_module")

    # 现在应该能看到
    assert "test_module" in manager.list_modules()


def test_ignored_modules_with_state_store(tmp_path: Path) -> None:
    """测试忽略模块列表的持久化."""
    state_file = tmp_path / "states.json"
    module_dir = tmp_path / "modules"
    module_dir.mkdir()

    (module_dir / "test_module.py").write_text(
        """
from symphra_modules import Module

class TestModule(Module):
    name = "test_module"
    version = "1.0.0"
    dependencies = []
"""
    )

    # 第一个管理器忽略模块
    store1 = FileStateStore(state_file)
    manager1 = ModuleManager(module_dir, state_store=store1)
    manager1.ignore_module("test_module")

    # 第二个管理器应该自动加载忽略列表
    store2 = FileStateStore(state_file)
    manager2 = ModuleManager(module_dir, state_store=store2)

    # 验证模块仍然被忽略
    assert "test_module" not in manager2.list_modules()
