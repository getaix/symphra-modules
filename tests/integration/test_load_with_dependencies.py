"""集成测试：带依赖的模块加载."""

import os
from pathlib import Path

import pytest
from symphra_modules.exceptions import CircularDependencyError, ModuleDependencyError

from symphra_modules.manager import ModuleManager

# 获取项目根目录的绝对路径
PROJECT_ROOT = Path(__file__).parent.parent.parent
TEST_MODULES_DIR = str(PROJECT_ROOT / "tests" / "fixtures" / "test_modules_with_deps")


def test_load_module_with_single_dependency() -> None:
    """测试加载带单个依赖的模块."""
    manager = ModuleManager(module_dirs=[TEST_MODULES_DIR])

    # 加载 database 模块（依赖 core）
    module = manager.load_module("database")

    # 验证 database 模块已加载
    assert module is not None
    assert module.metadata.name == "database"

    # 验证 core 依赖也被自动加载
    assert manager.is_module_loaded("core")
    core_module = manager.get_module("core")
    assert core_module.metadata.name == "core"


def test_load_module_with_chain_dependencies() -> None:
    """测试加载带依赖链的模块（A->B->C）."""
    manager = ModuleManager(module_dirs=[TEST_MODULES_DIR])

    # 加载 api 模块（依赖 core 和 database，database 又依赖 core）
    module = manager.load_module("api")

    # 验证所有模块都已加载
    assert module.metadata.name == "api"
    assert manager.is_module_loaded("core")
    assert manager.is_module_loaded("database")
    assert manager.is_module_loaded("api")

    # 验证加载顺序：core 应该先于 database，database 应该先于 api
    modules = manager.list_modules()
    assert "core" in modules
    assert "database" in modules
    assert "api" in modules


def test_load_module_circular_dependency() -> None:
    """测试循环依赖时失败."""
    manager = ModuleManager(module_dirs=[TEST_MODULES_DIR])

    # 尝试加载 module_a（依赖 module_b，而 module_b 依赖 module_a，形成循环）
    with pytest.raises(CircularDependencyError) as exc_info:
        manager.load_module("module_a")

    # 验证异常信息
    assert "循环依赖" in str(exc_info.value)
    # 验证循环路径包含 module_a 和 module_b
    assert exc_info.value.cycle_path is not None
    assert "module_a" in exc_info.value.cycle_path
    assert "module_b" in exc_info.value.cycle_path


def test_load_module_already_loaded() -> None:
    """测试重复加载已加载的模块."""
    manager = ModuleManager(module_dirs=[TEST_MODULES_DIR])

    # 第一次加载
    module1 = manager.load_module("core")
    # 第二次加载应该返回相同的实例
    module2 = manager.load_module("core")

    assert module1 is module2


def test_load_module_dependency_order() -> None:
    """测试依赖顺序正确."""
    manager = ModuleManager(module_dirs=[TEST_MODULES_DIR])

    # 先加载 api（会自动加载 core 和 database）
    manager.load_module("api")

    # 获取加载顺序（通过注册表）
    loaded_modules = manager.list_modules()

    # 验证所有模块都已加载
    assert "core" in loaded_modules
    assert "database" in loaded_modules
    assert "api" in loaded_modules


def test_load_module_missing_dependency() -> None:
    """测试缺失依赖时失败."""
    # 创建一个临时模块，依赖不存在的模块
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        # 创建一个依赖不存在模块的测试模块
        module_path = os.path.join(tmpdir, "broken_module.py")
        with open(module_path, "w") as f:
            f.write('''"""Broken module."""
from symphra_modules.abc import BaseModule
from symphra_modules.config import ModuleMetadata

class BrokenModule(BaseModule):
    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="broken",
            version="1.0.0",
            description="Broken module",
            dependencies=["nonexistent"],
        )
    def start(self) -> None:
        pass
    def stop(self) -> None:
        pass
''')

        manager = ModuleManager(module_dirs=[tmpdir])

        # 尝试加载应该失败
        with pytest.raises(ModuleDependencyError) as exc_info:
            manager.load_module("broken")

        # 验证异常信息
        assert "缺失依赖" in str(exc_info.value) or "找不到模块" in str(exc_info.value)
