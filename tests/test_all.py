"""测试套件 - Symphra Modules."""

import tempfile
from pathlib import Path

import pytest

from symphra_modules import (
    CircularDependencyError,
    DependencyError,
    DependencyGraph,
    Module,
    ModuleManager,
    ModuleNotFoundError,
    ModuleState,
)


class TestModule:
    """测试模块基类."""

    def test_module_basic(self) -> None:
        """测试基本模块定义."""

        class SimpleModule(Module):
            name = "simple"

        mod = SimpleModule()
        assert mod.name == "simple"
        assert mod.state == ModuleState.LOADED
        assert mod.version == "0.1.0"

    def test_module_with_dependencies(self) -> None:
        """测试带依赖的模块."""

        class DBModule(Module):
            name = "database"
            dependencies = ["config"]

        assert DBModule.dependencies == ["config"]
        assert DBModule.name == "database"

    def test_module_lifecycle(self) -> None:
        """测试模块生命周期."""

        class LifecycleModule(Module):
            name = "lifecycle"

            def __init__(self) -> None:
                super().__init__()
                self.started = False
                self.stopped = False

            def start(self) -> None:
                self.started = True

            def stop(self) -> None:
                self.stopped = True

        mod = LifecycleModule()
        assert not mod.started
        assert not mod.stopped

        mod.start()
        assert mod.started

        mod.stop()
        assert mod.stopped


class TestDependencyGraph:
    """测试依赖图."""

    def test_topological_sort_simple(self) -> None:
        """测试简单拓扑排序."""
        graph = DependencyGraph()
        graph.add_node("a", ["b", "c"])
        graph.add_node("b", ["c"])
        graph.add_node("c", [])

        order = graph.topological_sort()

        # c 应该在 b 前面, b 应该在 a 前面
        assert order.index("c") < order.index("b")
        assert order.index("b") < order.index("a")

    def test_topological_sort_complex(self) -> None:
        """测试复杂拓扑排序."""
        graph = DependencyGraph()
        graph.add_node("app", ["database", "cache"])
        graph.add_node("database", ["config"])
        graph.add_node("cache", ["config"])
        graph.add_node("config", [])

        order = graph.topological_sort()

        # config 必须最先
        assert order[0] == "config"
        # database 和 cache 在 app 前面
        assert order.index("database") < order.index("app")
        assert order.index("cache") < order.index("app")

    def test_circular_dependency_detection(self) -> None:
        """测试循环依赖检测."""
        graph = DependencyGraph()
        graph.add_node("a", ["b"])
        graph.add_node("b", ["c"])
        graph.add_node("c", ["a"])  # 循环!

        with pytest.raises(CircularDependencyError) as exc:
            graph.topological_sort()

        assert len(exc.value.cycle) > 0
        # 循环中应包含 a, b, c
        cycle_names = set(exc.value.cycle)
        assert "a" in cycle_names or "b" in cycle_names or "c" in cycle_names

    def test_self_dependency(self) -> None:
        """测试自依赖检测."""
        graph = DependencyGraph()
        graph.add_node("a", ["a"])  # 自依赖

        with pytest.raises(CircularDependencyError):
            graph.topological_sort()


class TestModuleManager:
    """测试模块管理器."""

    @pytest.fixture
    def temp_modules_dir(self) -> str:
        """创建临时模块目录."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试模块文件

            # 简单模块
            simple_module = """
from symphra_modules import Module

class SimpleModule(Module):
    name = "simple"
    version = "1.0.0"

    def start(self):
        pass
"""
            Path(tmpdir, "simple.py").write_text(simple_module)

            # 配置模块
            config_module = """
from symphra_modules import Module

class ConfigModule(Module):
    name = "config"

    def start(self):
        pass
"""
            Path(tmpdir, "config.py").write_text(config_module)

            # 数据库模块 (依赖 config)
            db_module = """
from symphra_modules import Module

class DatabaseModule(Module):
    name = "database"
    dependencies = ["config"]

    def start(self):
        pass
"""
            Path(tmpdir, "database.py").write_text(db_module)

            # 缓存模块 (依赖 config)
            cache_module = """
from symphra_modules import Module

class CacheModule(Module):
    name = "cache"
    dependencies = ["config"]

    def start(self):
        pass
"""
            Path(tmpdir, "cache.py").write_text(cache_module)

            # 应用模块 (依赖 database 和 cache)
            app_module = """
from symphra_modules import Module

class AppModule(Module):
    name = "app"
    dependencies = ["database", "cache"]

    def start(self):
        pass
"""
            Path(tmpdir, "app.py").write_text(app_module)

            yield tmpdir

    def test_discover_modules(self, temp_modules_dir: str) -> None:
        """测试发现模块."""
        manager = ModuleManager(temp_modules_dir)
        modules = manager.list_modules()

        assert "simple" in modules
        assert "config" in modules
        assert "database" in modules
        assert "cache" in modules
        assert "app" in modules
        assert len(modules) == 5

    def test_load_simple_module(self, temp_modules_dir: str) -> None:
        """测试加载简单模块."""
        manager = ModuleManager(temp_modules_dir)
        simple = manager.load("simple")

        assert simple is not None
        assert simple.state == ModuleState.LOADED
        assert manager.get_module("simple") is simple

    def test_load_with_dependencies(self, temp_modules_dir: str) -> None:
        """测试加载带依赖的模块."""
        manager = ModuleManager(temp_modules_dir)

        # 加载 database 应该自动加载 config
        db = manager.load("database")
        assert db is not None

        # config 应该也被加载了
        config = manager.get_module("config")
        assert config is not None

    def test_dependency_resolution_order(self, temp_modules_dir: str) -> None:
        """测试依赖解析顺序."""
        manager = ModuleManager(temp_modules_dir)

        # 加载 app 应该按正确顺序加载所有依赖
        app = manager.load("app")
        assert app is not None

        # 所有依赖都应该被加载
        assert manager.get_module("config") is not None
        assert manager.get_module("database") is not None
        assert manager.get_module("cache") is not None

    def test_load_nonexistent_module(self, temp_modules_dir: str) -> None:
        """测试加载不存在的模块."""
        manager = ModuleManager(temp_modules_dir)

        # 加载不存在的模块会抛出 DependencyError（在依赖解析阶段）
        with pytest.raises((ModuleNotFoundError, DependencyError)):
            manager.load("nonexistent")

    def test_start_module(self, temp_modules_dir: str) -> None:
        """测试启动模块."""
        manager = ModuleManager(temp_modules_dir)
        simple = manager.load("simple")

        manager.start("simple")
        assert simple.state == ModuleState.STARTED

    def test_stop_module(self, temp_modules_dir: str) -> None:
        """测试停止模块."""
        manager = ModuleManager(temp_modules_dir)
        simple = manager.load("simple")
        manager.start("simple")

        manager.stop("simple")
        assert simple.state == ModuleState.STOPPED

    def test_start_nonloaded_module(self, temp_modules_dir: str) -> None:
        """测试启动未加载的模块."""
        manager = ModuleManager(temp_modules_dir)

        with pytest.raises(ModuleNotFoundError):
            manager.start("simple")

    def test_circular_dependency_detection(self) -> None:
        """测试循环依赖检测."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建循环依赖的模块
            a_module = """
from symphra_modules import Module

class AModule(Module):
    name = "a"
    dependencies = ["b"]
"""
            Path(tmpdir, "a.py").write_text(a_module)

            b_module = """
from symphra_modules import Module

class BModule(Module):
    name = "b"
    dependencies = ["c"]
"""
            Path(tmpdir, "b.py").write_text(b_module)

            c_module = """
from symphra_modules import Module

class CModule(Module):
    name = "c"
    dependencies = ["a"]  # 循环!
"""
            Path(tmpdir, "c.py").write_text(c_module)

            manager = ModuleManager(tmpdir)

            with pytest.raises(CircularDependencyError):
                manager.load("a")

    def test_missing_dependency(self) -> None:
        """测试缺失依赖."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建依赖不存在的模块
            module_code = """
from symphra_modules import Module

class MyModule(Module):
    name = "mymodule"
    dependencies = ["nonexistent"]
"""
            Path(tmpdir, "mymodule.py").write_text(module_code)

            manager = ModuleManager(tmpdir)

            with pytest.raises(DependencyError):
                manager.load("mymodule")

    def test_empty_directory(self) -> None:
        """测试空目录."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ModuleManager(tmpdir)
            assert manager.list_modules() == []

    def test_nonexistent_directory(self) -> None:
        """测试不存在的目录."""
        manager = ModuleManager("/nonexistent/path")
        assert manager.list_modules() == []


class TestModuleIntegration:
    """集成测试."""

    def test_complete_workflow(self) -> None:
        """测试完整工作流."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建完整的模块系统
            config_module = """
from symphra_modules import Module

class ConfigModule(Module):
    name = "config"

    def __init__(self):
        super().__init__()
        self.data = {}

    def start(self):
        self.data["loaded"] = True
"""
            Path(tmpdir, "config.py").write_text(config_module)

            app_module = """
from symphra_modules import Module

class AppModule(Module):
    name = "app"
    dependencies = ["config"]

    def __init__(self):
        super().__init__()
        self.running = False

    def start(self):
        self.running = True

    def stop(self):
        self.running = False
"""
            Path(tmpdir, "app.py").write_text(app_module)

            # 创建管理器
            manager = ModuleManager(tmpdir)

            # 发现模块
            assert len(manager.list_modules()) == 2

            # 加载模块
            app = manager.load("app")
            config = manager.get_module("config")
            assert app is not None
            assert config is not None

            # 启动模块
            manager.start("config")
            manager.start("app")
            assert app.running  # type: ignore
            assert config.data["loaded"]  # type: ignore

            # 停止模块
            manager.stop("app")
            assert not app.running  # type: ignore
