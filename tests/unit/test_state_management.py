"""测试模块状态管理功能."""

from pathlib import Path

import pytest

from symphra_modules import ModuleManager
from symphra_modules.core import (
    FileStateStore,
    Module,
    ModuleNotFoundError,
    ModuleState,
)


# 测试模块定义
class SimpleModule(Module):
    """简单测试模块."""

    name = "simple"
    version = "1.0.0"
    dependencies = []

    def __init__(self) -> None:
        super().__init__()
        self.bootstrapped = False
        self.started = False

    def bootstrap(self) -> None:
        """Bootstrap 初始化."""
        self.bootstrapped = True

    def start(self) -> None:
        """启动模块."""
        self.started = True

    def stop(self) -> None:
        """停止模块."""
        self.started = False


class DependentModule(Module):
    """有依赖的测试模块."""

    name = "dependent"
    version = "1.0.0"
    dependencies = ["simple"]

    def start(self) -> None:
        """启动模块."""
        pass

    def stop(self) -> None:
        """停止模块."""
        pass


class TestBootstrap:
    """测试 Bootstrap 功能."""

    def test_bootstrap_module(self, tmp_path: Path) -> None:
        """测试 bootstrap 模块."""
        # 创建测试模块目录
        modules_dir = tmp_path / "modules"
        modules_dir.mkdir()

        # 创建测试模块文件
        module_file = modules_dir / "simple_module.py"
        module_file.write_text(
            """
from symphra_modules.core import Module

class SimpleModule(Module):
    name = "simple"
    version = "1.0.0"
    dependencies = []

    def __init__(self):
        super().__init__()
        self.bootstrapped = False
        self.started = False

    def bootstrap(self):
        self.bootstrapped = True

    def start(self):
        self.started = True

    def stop(self):
        self.started = False
"""
        )

        # 创建管理器并加载模块
        manager = ModuleManager(modules_dir)
        manager.load("simple")

        # Bootstrap 模块
        manager.bootstrap("simple")

        # 验证状态
        module = manager.get_module("simple")
        assert module is not None
        assert module.state == ModuleState.INITIALIZED
        assert module.bootstrapped is True
        assert module.started is False

    def test_bootstrap_without_load(self, tmp_path: Path) -> None:
        """测试在未加载模块时 bootstrap 应该失败."""
        manager = ModuleManager(tmp_path)

        with pytest.raises(ModuleNotFoundError):
            manager.bootstrap("nonexistent")

    def test_bootstrap_then_start(self, tmp_path: Path) -> None:
        """测试 bootstrap 后可以启动模块."""
        # 创建测试模块目录
        modules_dir = tmp_path / "modules"
        modules_dir.mkdir()

        # 创建测试模块文件
        module_file = modules_dir / "simple_module.py"
        module_file.write_text(
            """
from symphra_modules.core import Module

class SimpleModule(Module):
    name = "simple"
    version = "1.0.0"
    dependencies = []

    def __init__(self):
        super().__init__()
        self.bootstrapped = False
        self.started = False

    def bootstrap(self):
        self.bootstrapped = True

    def start(self):
        self.started = True

    def stop(self):
        self.started = False
"""
        )

        # 创建管理器并加载模块
        manager = ModuleManager(modules_dir)
        manager.load("simple")
        manager.bootstrap("simple")

        # 启动模块
        manager.start("simple")

        # 验证状态
        module = manager.get_module("simple")
        assert module is not None
        assert module.state == ModuleState.STARTED
        assert module.bootstrapped is True
        assert module.started is True


class TestInstallUninstall:
    """测试安装/卸载功能."""

    def test_install_module(self, tmp_path: Path) -> None:
        """测试安装模块."""
        # 创建测试模块目录
        modules_dir = tmp_path / "modules"
        modules_dir.mkdir()

        # 创建测试模块文件
        module_file = modules_dir / "simple_module.py"
        module_file.write_text(
            """
from symphra_modules.core import Module

class SimpleModule(Module):
    name = "simple"
    version = "1.0.0"
    dependencies = []
"""
        )

        # 创建管理器
        manager = ModuleManager(modules_dir)

        # 安装模块（会自动加载）
        manager.install("simple")

        # 验证模块已安装
        module = manager.get_module("simple")
        assert module is not None
        assert module.state in [ModuleState.INSTALLED, ModuleState.LOADED]

    def test_uninstall_module(self, tmp_path: Path) -> None:
        """测试卸载模块."""
        # 创建测试模块目录
        modules_dir = tmp_path / "modules"
        modules_dir.mkdir()

        # 创建测试模块文件
        module_file = modules_dir / "simple_module.py"
        module_file.write_text(
            """
from symphra_modules.core import Module

class SimpleModule(Module):
    name = "simple"
    version = "1.0.0"
    dependencies = []
"""
        )

        # 创建管理器并加载模块
        manager = ModuleManager(modules_dir)
        manager.load("simple")

        # 卸载模块
        manager.uninstall("simple")

        # 验证模块已卸载
        module = manager.get_module("simple")
        assert module is None

    def test_uninstall_running_module(self, tmp_path: Path) -> None:
        """测试卸载正在运行的模块."""
        # 创建测试模块目录
        modules_dir = tmp_path / "modules"
        modules_dir.mkdir()

        # 创建测试模块文件
        module_file = modules_dir / "simple_module.py"
        module_file.write_text(
            """
from symphra_modules.core import Module

class SimpleModule(Module):
    name = "simple"
    version = "1.0.0"
    dependencies = []

    def start(self):
        pass

    def stop(self):
        pass
"""
        )

        # 创建管理器并加载、启动模块
        manager = ModuleManager(modules_dir)
        manager.load("simple")
        manager.start("simple")

        # 验证模块正在运行
        module = manager.get_module("simple")
        assert module is not None
        assert module.state == ModuleState.STARTED

        # 卸载模块（应该先停止再卸载）
        manager.uninstall("simple")

        # 验证模块已卸载
        module = manager.get_module("simple")
        assert module is None


class TestEnableDisable:
    """测试启用/禁用功能."""

    def test_disable_module(self, tmp_path: Path) -> None:
        """测试禁用模块."""
        # 创建测试模块目录
        modules_dir = tmp_path / "modules"
        modules_dir.mkdir()

        # 创建测试模块文件
        module_file = modules_dir / "simple_module.py"
        module_file.write_text(
            """
from symphra_modules.core import Module

class SimpleModule(Module):
    name = "simple"
    version = "1.0.0"
    dependencies = []

    def stop(self):
        pass
"""
        )

        # 创建管理器并加载模块
        manager = ModuleManager(modules_dir)
        manager.load("simple")

        # 禁用模块
        manager.disable("simple")

        # 验证模块已禁用
        module = manager.get_module("simple")
        assert module is not None
        assert module.state == ModuleState.DISABLED

    def test_disable_running_module(self, tmp_path: Path) -> None:
        """测试禁用正在运行的模块."""
        # 创建测试模块目录
        modules_dir = tmp_path / "modules"
        modules_dir.mkdir()

        # 创建测试模块文件
        module_file = modules_dir / "simple_module.py"
        module_file.write_text(
            """
from symphra_modules.core import Module

class SimpleModule(Module):
    name = "simple"
    version = "1.0.0"
    dependencies = []

    def start(self):
        pass

    def stop(self):
        pass
"""
        )

        # 创建管理器并加载、启动模块
        manager = ModuleManager(modules_dir)
        manager.load("simple")
        manager.start("simple")

        # 验证模块正在运行
        module = manager.get_module("simple")
        assert module is not None
        assert module.state == ModuleState.STARTED

        # 禁用模块（应该先停止再禁用）
        manager.disable("simple")

        # 验证模块已禁用
        module = manager.get_module("simple")
        assert module is not None
        assert module.state == ModuleState.DISABLED

    def test_enable_disabled_module(self, tmp_path: Path) -> None:
        """测试启用已禁用的模块."""
        # 创建测试模块目录
        modules_dir = tmp_path / "modules"
        modules_dir.mkdir()

        # 创建测试模块文件
        module_file = modules_dir / "simple_module.py"
        module_file.write_text(
            """
from symphra_modules.core import Module

class SimpleModule(Module):
    name = "simple"
    version = "1.0.0"
    dependencies = []

    def stop(self):
        pass
"""
        )

        # 创建管理器并加载模块
        manager = ModuleManager(modules_dir)
        manager.load("simple")

        # 禁用模块
        manager.disable("simple")
        assert manager.get_module("simple").state == ModuleState.DISABLED  # type: ignore

        # 启用模块
        manager.enable("simple")

        # 验证模块已启用
        module = manager.get_module("simple")
        assert module is not None
        assert module.state == ModuleState.INSTALLED


class TestIgnoreModule:
    """测试忽略模块功能."""

    def test_ignore_module(self, tmp_path: Path) -> None:
        """测试忽略模块."""
        # 创建测试模块目录
        modules_dir = tmp_path / "modules"
        modules_dir.mkdir()

        # 创建测试模块文件
        module_file = modules_dir / "simple_module.py"
        module_file.write_text(
            """
from symphra_modules.core import Module

class SimpleModule(Module):
    name = "simple"
    version = "1.0.0"
    dependencies = []
"""
        )

        # 创建管理器
        manager = ModuleManager(modules_dir)

        # 验证模块在可用列表中
        assert "simple" in manager.list_modules()

        # 忽略模块
        manager.ignore_module("simple")

        # 验证模块不在可用列表中
        assert "simple" not in manager.list_modules()

    def test_unignore_module(self, tmp_path: Path) -> None:
        """测试取消忽略模块."""
        # 创建测试模块目录
        modules_dir = tmp_path / "modules"
        modules_dir.mkdir()

        # 创建测试模块文件
        module_file = modules_dir / "simple_module.py"
        module_file.write_text(
            """
from symphra_modules.core import Module

class SimpleModule(Module):
    name = "simple"
    version = "1.0.0"
    dependencies = []
"""
        )

        # 创建管理器并忽略模块
        manager = ModuleManager(modules_dir, ignored_modules={"simple"})

        # 验证模块不在可用列表中
        assert "simple" not in manager.list_modules()

        # 取消忽略
        manager.unignore_module("simple")

        # 验证模块在可用列表中
        assert "simple" in manager.list_modules()

    def test_ignored_modules_with_state_store(self, tmp_path: Path) -> None:
        """测试忽略模块列表持久化."""
        # 创建测试模块目录
        modules_dir = tmp_path / "modules"
        modules_dir.mkdir()

        # 创建测试模块文件
        module_file = modules_dir / "simple_module.py"
        module_file.write_text(
            """
from symphra_modules.core import Module

class SimpleModule(Module):
    name = "simple"
    version = "1.0.0"
    dependencies = []
"""
        )

        # 创建状态存储
        state_file = tmp_path / "states.json"
        store = FileStateStore(state_file)

        # 第一个管理器忽略模块
        manager1 = ModuleManager(modules_dir, state_store=store)
        manager1.ignore_module("simple")

        # 第二个管理器加载相同的状态存储
        manager2 = ModuleManager(modules_dir, state_store=store)

        # 验证模块在第二个管理器中也被忽略
        assert "simple" not in manager2.list_modules()
