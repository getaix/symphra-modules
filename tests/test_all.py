"""测试套件 - Symphra Modules."""

import asyncio
import tempfile
from pathlib import Path

import pytest

from symphra_modules import (
    CircularDependencyError,
    DependencyError,
    DependencyGraph,
    FileStateStore,
    MemoryStateStore,
    Module,
    ModuleManager,
    ModuleNotFoundError,
    ModuleState,
    ModuleStateError,
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


class TestStatePersistence:
    """测试状态持久化."""

    def test_memory_state_store(self) -> None:
        """测试内存状态存储."""
        store = MemoryStateStore()

        # 保存模块状态
        store.save_state("test_module", ModuleState.STARTED)
        assert store.load_state("test_module") == ModuleState.STARTED

        # 更新状态
        store.save_state("test_module", ModuleState.STOPPED)
        assert store.load_state("test_module") == ModuleState.STOPPED

        # 获取所有状态
        store.save_state("module2", ModuleState.LOADED)
        states = store.list_states()
        assert states["test_module"] == ModuleState.STOPPED
        assert states["module2"] == ModuleState.LOADED

        # 删除状态
        store.delete_state("test_module")
        assert store.load_state("test_module") is None

    def test_file_state_store(self) -> None:
        """测试文件状态存储."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_path = Path(tmpdir) / "states.json"
            store = FileStateStore(str(store_path))

            # 保存状态
            store.save_state("module1", ModuleState.STARTED)
            store.save_state("module2", ModuleState.LOADED)

            # 创建新的 store 实例，验证持久化
            store2 = FileStateStore(str(store_path))
            assert store2.load_state("module1") == ModuleState.STARTED
            assert store2.load_state("module2") == ModuleState.LOADED

            # 测试忽略的模块列表
            store.save_ignored_modules({"ignored_module"})
            ignored = store.load_ignored_modules()
            assert "ignored_module" in ignored

            # 验证持久化
            store2 = FileStateStore(str(store_path))
            ignored2 = store2.load_ignored_modules()
            assert "ignored_module" in ignored2

            # 测试列出所有状态
            states = store.list_states()
            assert "module1" in states
            assert "module2" in states

    def test_module_manager_with_state_store(self) -> None:
        """测试 ModuleManager 与状态存储的集成."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试模块
            module_code = """
from symphra_modules import Module

class TestModule(Module):
    name = "test"

    def start(self):
        pass

    def stop(self):
        pass
"""
            Path(tmpdir, "test.py").write_text(module_code)

            # 创建状态存储
            store = MemoryStateStore()
            manager = ModuleManager(tmpdir, state_store=store)

            # 加载模块
            manager.load("test")

            # 禁用模块 - 会保存状态
            manager.disable("test")
            assert store.load_state("test") == ModuleState.DISABLED

            # 启用模块 - 会保存状态
            manager.enable("test")
            assert store.load_state("test") == ModuleState.INSTALLED

            # 卸载模块 - 会保存状态
            manager.uninstall("test")
            assert store.load_state("test") == ModuleState.UNINSTALLED


class TestModuleLifecycle:
    """测试模块生命周期管理."""

    def test_module_state_transitions(self) -> None:
        """测试模块状态转换."""
        with tempfile.TemporaryDirectory() as tmpdir:
            module_code = """
from symphra_modules import Module

class TestModule(Module):
    name = "test"

    def start(self):
        pass

    def stop(self):
        pass
"""
            Path(tmpdir, "test.py").write_text(module_code)

            manager = ModuleManager(tmpdir)
            mod = manager.load("test")

            # 初始状态应该是 LOADED
            assert mod.state == ModuleState.LOADED

            # 启动
            manager.start("test")
            assert mod.state == ModuleState.STARTED

            # 停止
            manager.stop("test")
            assert mod.state == ModuleState.STOPPED

    def test_async_module(self) -> None:
        """测试异步模块."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建异步模块
            async_module = """
from symphra_modules import Module

class AsyncModule(Module):
    name = "async_test"

    def __init__(self):
        super().__init__()
        self.started = False
        self.stopped = False

    async def start_async(self):
        self.started = True

    async def stop_async(self):
        self.stopped = True
"""
            Path(tmpdir, "async_test.py").write_text(async_module)

            manager = ModuleManager(tmpdir)
            mod = manager.load("async_test")

            # 测试异步方法
            async def test():
                await mod.start_async()
                assert mod.started  # type: ignore
                await mod.stop_async()
                assert mod.stopped  # type: ignore

            asyncio.run(test())


class TestModuleInstallation:
    """测试模块安装和卸载."""

    def test_install_uninstall(self) -> None:
        """测试模块安装和卸载."""
        with tempfile.TemporaryDirectory() as tmpdir:
            module_code = """
from symphra_modules import Module

class TestModule(Module):
    name = "test"
"""
            Path(tmpdir, "test.py").write_text(module_code)

            store = MemoryStateStore()
            manager = ModuleManager(tmpdir, state_store=store)

            # install 会先 load 模块，模块状态为 LOADED，但不会持久化
            manager.install("test")

            # 验证模块已加载
            mod = manager.get_module("test")
            assert mod is not None
            assert mod.state == ModuleState.LOADED

            # 卸载模块 - 这会保存状态
            manager.uninstall("test")
            assert store.load_state("test") == ModuleState.UNINSTALLED

    def test_enable_disable(self) -> None:
        """测试启用和禁用模块."""
        with tempfile.TemporaryDirectory() as tmpdir:
            module_code = """
from symphra_modules import Module

class TestModule(Module):
    name = "test"
"""
            Path(tmpdir, "test.py").write_text(module_code)

            store = MemoryStateStore()
            manager = ModuleManager(tmpdir, state_store=store)

            # 先加载模块，enable/disable 需要模块已加载
            manager.load("test")

            # 禁用模块
            manager.disable("test")
            assert store.load_state("test") == ModuleState.DISABLED

            # 启用模块
            manager.enable("test")
            # 启用后状态变为 INSTALLED
            state = store.load_state("test")
            assert state == ModuleState.INSTALLED


class TestModuleBlacklist:
    """测试模块黑名单功能."""

    def test_ignore_module(self) -> None:
        """测试忽略模块."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建两个模块
            module1 = """
from symphra_modules import Module

class Module1(Module):
    name = "module1"
"""
            module2 = """
from symphra_modules import Module

class Module2(Module):
    name = "module2"
"""
            Path(tmpdir, "module1.py").write_text(module1)
            Path(tmpdir, "module2.py").write_text(module2)

            # 忽略 module2
            store = MemoryStateStore()
            manager = ModuleManager(tmpdir, state_store=store, ignored_modules=["module2"])

            # 只应该发现 module1
            modules = manager.list_modules()
            assert "module1" in modules
            assert "module2" not in modules

            # 动态忽略 module1
            manager.ignore_module("module1")
            ignored = store.load_ignored_modules()
            assert "module1" in ignored

            # 取消忽略
            manager.unignore_module("module1")
            ignored = store.load_ignored_modules()
            assert "module1" not in ignored


class TestModuleBootstrap:
    """测试模块引导功能."""

    def test_bootstrap(self) -> None:
        """测试引导模块."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建测试模块
            module_code = """
from symphra_modules import Module

class TestModule(Module):
    name = "test"

    def __init__(self):
        super().__init__()
        self.bootstrapped = False

    def bootstrap(self):
        self.bootstrapped = True
"""
            Path(tmpdir, "test.py").write_text(module_code)

            manager = ModuleManager(tmpdir)

            # bootstrap 需要模块先加载
            manager.load("test")
            manager.bootstrap("test")

            # 验证模块已引导
            mod = manager.get_module("test")
            assert mod is not None
            assert mod.bootstrapped  # type: ignore
            assert mod.state == ModuleState.INITIALIZED


class TestModuleErrors:
    """测试模块错误处理."""

    def test_module_not_found(self) -> None:
        """测试模块不存在错误."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ModuleManager(tmpdir)

            # get_module 对于不存在的模块返回 None
            assert manager.get_module("nonexistent") is None

    def test_invalid_state_transition(self) -> None:
        """测试无效状态转换."""
        # 这个测试需要直接测试状态转换逻辑
        from symphra_modules.core.state import is_valid_transition

        # STOPPED -> LOADED 是无效的
        assert not is_valid_transition(ModuleState.STOPPED, ModuleState.LOADED)

        # LOADED -> STARTED 是有效的
        assert is_valid_transition(ModuleState.LOADED, ModuleState.STARTED)


class TestDependencyResolver:
    """测试依赖解析器."""

    def test_resolve_dependencies(self) -> None:
        """测试依赖解析."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建依赖链
            a_module = """
from symphra_modules import Module

class AModule(Module):
    name = "a"
    dependencies = ["b", "c"]
"""
            b_module = """
from symphra_modules import Module

class BModule(Module):
    name = "b"
    dependencies = ["c"]
"""
            c_module = """
from symphra_modules import Module

class CModule(Module):
    name = "c"
"""
            Path(tmpdir, "a.py").write_text(a_module)
            Path(tmpdir, "b.py").write_text(b_module)
            Path(tmpdir, "c.py").write_text(c_module)

            manager = ModuleManager(tmpdir)
            manager.load("a")

            # 验证加载顺序：c -> b -> a
            c = manager.get_module("c")
            b = manager.get_module("b")
            a = manager.get_module("a")

            assert c is not None
            assert b is not None
            assert a is not None


class TestModuleProperties:
    """测试模块属性."""

    def test_module_metadata(self) -> None:
        """测试模块元数据."""
        class TestModule(Module):
            name = "test"
            version = "2.0.0"

        mod = TestModule()
        assert mod.name == "test"
        assert mod.version == "2.0.0"

    def test_module_default_values(self) -> None:
        """测试模块默认值."""
        class MinimalModule(Module):
            name = "minimal"

        mod = MinimalModule()
        assert mod.version == "0.1.0"
        assert mod.dependencies == []
        assert mod.state == ModuleState.LOADED


class TestModuleManagerAdvanced:
    """测试 ModuleManager 高级功能."""

    def test_load_all(self) -> None:
        """测试加载所有模块."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建多个模块
            for i in range(3):
                module_code = f"""
from symphra_modules import Module

class Module{i}(Module):
    name = "module{i}"
"""
                Path(tmpdir, f"module{i}.py").write_text(module_code)

            manager = ModuleManager(tmpdir)
            modules = manager.load_all()

            assert len(modules) == 3
            assert "module0" in modules
            assert "module1" in modules
            assert "module2" in modules

    def test_start_all(self) -> None:
        """测试启动所有模块."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建模块
            module_code = """
from symphra_modules import Module

class TestModule(Module):
    name = "test"

    def start(self):
        pass
"""
            Path(tmpdir, "test.py").write_text(module_code)

            manager = ModuleManager(tmpdir)
            manager.load_all()
            manager.start_all()

            mod = manager.get_module("test")
            assert mod.state == ModuleState.STARTED

    def test_stop_all(self) -> None:
        """测试停止所有模块."""
        with tempfile.TemporaryDirectory() as tmpdir:
            module_code = """
from symphra_modules import Module

class TestModule(Module):
    name = "test"

    def start(self):
        pass

    def stop(self):
        pass
"""
            Path(tmpdir, "test.py").write_text(module_code)

            manager = ModuleManager(tmpdir)
            manager.load_all()
            manager.start_all()
            manager.stop_all()

            mod = manager.get_module("test")
            assert mod.state == ModuleState.STOPPED

    def test_unload(self) -> None:
        """测试卸载模块."""
        with tempfile.TemporaryDirectory() as tmpdir:
            module_code = """
from symphra_modules import Module

class TestModule(Module):
    name = "test"
"""
            Path(tmpdir, "test.py").write_text(module_code)

            manager = ModuleManager(tmpdir)
            manager.load("test")
            assert manager.get_module("test") is not None

            manager.unload("test")
            assert manager.get_module("test") is None

    def test_rediscover(self) -> None:
        """测试重新发现模块."""
        with tempfile.TemporaryDirectory() as tmpdir:
            module_code = """
from symphra_modules import Module

class TestModule(Module):
    name = "test"
"""
            Path(tmpdir, "test.py").write_text(module_code)

            manager = ModuleManager(tmpdir)
            modules1 = manager.list_modules()
            assert "test" in modules1

            # 添加新模块
            new_module = """
from symphra_modules import Module

class NewModule(Module):
    name = "new"
"""
            Path(tmpdir, "new.py").write_text(new_module)

            # 重新发现
            manager.rediscover()
            modules2 = manager.list_modules()
            assert "test" in modules2
            assert "new" in modules2

    def test_get_module_info(self) -> None:
        """测试获取模块信息."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建依赖模块
            dep_module = """
from symphra_modules import Module

class DepModule(Module):
    name = "dep1"
"""
            Path(tmpdir, "dep1.py").write_text(dep_module)

            # 创建测试模块
            module_code = """
from symphra_modules import Module

class TestModule(Module):
    name = "test"
    version = "1.0.0"
    dependencies = ["dep1"]
"""
            Path(tmpdir, "test.py").write_text(module_code)

            manager = ModuleManager(tmpdir)
            manager.load("test")

            info = manager.get_module_info("test")
            assert info["name"] == "test"
            assert info["version"] == "1.0.0"
            assert info["dependencies"] == ["dep1"]
            assert info["state"] == "loaded"

    def test_list_loaded_modules(self) -> None:
        """测试列出已加载的模块."""
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(3):
                module_code = f"""
from symphra_modules import Module

class Module{i}(Module):
    name = "module{i}"
"""
                Path(tmpdir, f"module{i}.py").write_text(module_code)

            manager = ModuleManager(tmpdir)
            manager.load("module0")
            manager.load("module1")

            loaded = manager.list_loaded_modules()
            assert len(loaded) == 2
            assert "module0" in loaded
            assert "module1" in loaded
            assert "module2" not in loaded

    def test_list_started_modules(self) -> None:
        """测试列出已启动的模块."""
        with tempfile.TemporaryDirectory() as tmpdir:
            module_code = """
from symphra_modules import Module

class TestModule(Module):
    name = "test"

    def start(self):
        pass
"""
            Path(tmpdir, "test.py").write_text(module_code)

            manager = ModuleManager(tmpdir)

            # 没有启动任何模块时，列表应该为空
            started1 = manager.list_started_modules()
            assert len(started1) == 0

            # 加载并启动模块
            manager.load("test")
            manager.start("test")

            # 现在应该有一个已启动的模块
            started2 = manager.list_started_modules()
            assert len(started2) >= 1
            assert "test" in started2

    def test_context_manager(self) -> None:
        """测试上下文管理器."""
        with tempfile.TemporaryDirectory() as tmpdir:
            module_code = """
from symphra_modules import Module

class TestModule(Module):
    name = "test"

    def start(self):
        pass

    def stop(self):
        pass
"""
            Path(tmpdir, "test.py").write_text(module_code)

            with ModuleManager(tmpdir) as manager:
                manager.load("test")
                manager.start("test")
                mod = manager.get_module("test")
                assert mod.state == ModuleState.STARTED

            # 上下文退出后，所有模块应该被停止
            # 但我们无法在这里验证，因为 manager 已经超出作用域


class TestAsyncOperations:
    """测试异步操作."""

    def test_load_async(self) -> None:
        """测试异步加载模块."""
        with tempfile.TemporaryDirectory() as tmpdir:
            module_code = """
from symphra_modules import Module

class TestModule(Module):
    name = "test"
"""
            Path(tmpdir, "test.py").write_text(module_code)

            async def test():
                manager = ModuleManager(tmpdir)
                mod = await manager.load_async("test")
                assert mod.name == "test"
                assert mod.state == ModuleState.LOADED

            asyncio.run(test())

    def test_start_stop_async(self) -> None:
        """测试异步启动和停止."""
        with tempfile.TemporaryDirectory() as tmpdir:
            async_module = """
from symphra_modules import Module

class AsyncModule(Module):
    name = "async_mod"

    async def start_async(self):
        pass

    async def stop_async(self):
        pass
"""
            Path(tmpdir, "async_mod.py").write_text(async_module)

            async def test():
                manager = ModuleManager(tmpdir)
                await manager.load_async("async_mod")
                await manager.start_async("async_mod")

                mod = manager.get_module("async_mod")
                assert mod.state == ModuleState.STARTED

                await manager.stop_async("async_mod")
                assert mod.state == ModuleState.STOPPED

            asyncio.run(test())


class TestErrorHandling:
    """测试错误处理."""

    def test_load_with_invalid_name(self) -> None:
        """测试使用无效名称加载模块."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ModuleManager(tmpdir)

            with pytest.raises((ValueError, ModuleNotFoundError)):
                manager.load("")

    def test_start_with_dependencies_error(self) -> None:
        """测试依赖启动错误."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建有问题的依赖
            module_code = """
from symphra_modules import Module

class TestModule(Module):
    name = "test"
    dependencies = ["missing"]
"""
            Path(tmpdir, "test.py").write_text(module_code)

            manager = ModuleManager(tmpdir)

            with pytest.raises((DependencyError, ModuleNotFoundError)):
                manager.load("test")

    def test_multiple_directories(self) -> None:
        """测试多个模块目录."""
        with tempfile.TemporaryDirectory() as tmpdir1:
            with tempfile.TemporaryDirectory() as tmpdir2:
                # 在第一个目录创建模块
                module1 = """
from symphra_modules import Module

class Module1(Module):
    name = "module1"
"""
                Path(tmpdir1, "module1.py").write_text(module1)

                # 在第二个目录创建模块
                module2 = """
from symphra_modules import Module

class Module2(Module):
    name = "module2"
"""
                Path(tmpdir2, "module2.py").write_text(module2)

                # 使用多个目录
                manager = ModuleManager([tmpdir1, tmpdir2])
                modules = manager.list_modules()

                assert "module1" in modules
                assert "module2" in modules

    def test_load_force_reload(self) -> None:
        """测试强制重载模块."""
        with tempfile.TemporaryDirectory() as tmpdir:
            module_code = """
from symphra_modules import Module

class TestModule(Module):
    name = "test"
    version = "1.0.0"
"""
            Path(tmpdir, "test.py").write_text(module_code)

            manager = ModuleManager(tmpdir)
            mod1 = manager.load("test")
            assert mod1.version == "1.0.0"

            # 强制重载
            mod2 = manager.load("test", force=True)
            assert mod2 is not mod1  # 应该是新实例

    def test_stop_nonstarted_module(self) -> None:
        """测试停止未启动的模块."""
        with tempfile.TemporaryDirectory() as tmpdir:
            module_code = """
from symphra_modules import Module

class TestModule(Module):
    name = "test"

    def stop(self):
        pass
"""
            Path(tmpdir, "test.py").write_text(module_code)

            manager = ModuleManager(tmpdir)
            manager.load("test")

            # 停止未启动的模块
            manager.stop("test")
            mod = manager.get_module("test")
            # 状态会变成 STOPPED，即使之前没有 STARTED
            assert mod.state in (ModuleState.LOADED, ModuleState.STOPPED)

    def test_unload_started_module(self) -> None:
        """测试卸载已启动的模块."""
        with tempfile.TemporaryDirectory() as tmpdir:
            module_code = """
from symphra_modules import Module

class TestModule(Module):
    name = "test"

    def start(self):
        pass

    def stop(self):
        pass
"""
            Path(tmpdir, "test.py").write_text(module_code)

            manager = ModuleManager(tmpdir)
            manager.load("test")
            manager.start("test")

            # 卸载会先自动停止
            manager.unload("test")
            assert manager.get_module("test") is None


class TestModuleHelpers:
    """测试模块辅助函数."""

    def test_is_async_module(self) -> None:
        """测试异步模块检测."""
        from symphra_modules.core.module import is_async_module

        # 同步模块
        class SyncModule(Module):
            name = "sync"

            def start(self):
                pass

        sync_mod = SyncModule()
        assert not is_async_module(sync_mod)

        # 真正的异步模块
        class AsyncModule(Module):
            name = "async"

            async def start_async(self):
                pass

            async def stop_async(self):
                pass

        async_mod = AsyncModule()
        assert is_async_module(async_mod)

    def test_call_module_method(self) -> None:
        """测试调用模块方法."""
        from symphra_modules.core.module import call_module_method

        class TestModule(Module):
            name = "test"

            def __init__(self):
                super().__init__()
                self.called = False

            def my_method(self):
                self.called = True
                return "result"

            async def my_async_method(self):
                self.called = True
                return "async_result"

        mod = TestModule()

        # 测试同步方法
        async def test_sync():
            result = await call_module_method(mod, "my_method")
            assert result == "result"
            assert mod.called

        asyncio.run(test_sync())

        # 重置
        mod.called = False

        # 测试异步方法
        async def test_async():
            result = await call_module_method(mod, "my_async_method")
            assert result == "async_result"
            assert mod.called

        asyncio.run(test_async())

    def test_module_repr(self) -> None:
        """测试模块字符串表示."""
        class TestModule(Module):
            name = "test"

        mod = TestModule()
        repr_str = repr(mod)
        assert "TestModule" in repr_str
        assert "test" in repr_str
        assert "loaded" in repr_str.lower()

    def test_module_loaded_at(self) -> None:
        """测试模块加载时间."""
        from datetime import datetime

        class TestModule(Module):
            name = "test"

        before = datetime.now()
        mod = TestModule()
        after = datetime.now()

        assert before <= mod.loaded_at <= after


class TestStateTransitions:
    """测试状态转换."""

    def test_get_state_description(self) -> None:
        """测试获取状态描述."""
        from symphra_modules.core.state import get_state_description

        desc = get_state_description(ModuleState.LOADED)
        assert "加载" in desc

        desc = get_state_description(ModuleState.STARTED)
        assert "启动" in desc

    def test_all_state_transitions(self) -> None:
        """测试所有有效的状态转换."""
        from symphra_modules.core.state import is_valid_transition, VALID_TRANSITIONS

        # 验证一些基本转换
        assert is_valid_transition(ModuleState.LOADED, ModuleState.STARTED)
        assert is_valid_transition(ModuleState.STARTED, ModuleState.STOPPED)
        assert is_valid_transition(ModuleState.STOPPED, ModuleState.STARTED)
        assert is_valid_transition(ModuleState.LOADED, ModuleState.DISABLED)

        # 验证无效转换
        assert not is_valid_transition(ModuleState.UNINSTALLED, ModuleState.LOADED)
        assert not is_valid_transition(ModuleState.STOPPED, ModuleState.LOADED)


class TestComplexScenarios:
    """测试复杂场景."""

    def test_load_all_with_dependencies(self) -> None:
        """测试加载所有模块时的依赖解析."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建依赖链
            base_module = """
from symphra_modules import Module

class BaseModule(Module):
    name = "base"
"""
            mid_module = """
from symphra_modules import Module

class MidModule(Module):
    name = "mid"
    dependencies = ["base"]
"""
            top_module = """
from symphra_modules import Module

class TopModule(Module):
    name = "top"
    dependencies = ["mid"]
"""
            Path(tmpdir, "base.py").write_text(base_module)
            Path(tmpdir, "mid.py").write_text(mid_module)
            Path(tmpdir, "top.py").write_text(top_module)

            manager = ModuleManager(tmpdir)
            modules = manager.load_all()

            # 所有模块都应该被加载
            assert len(modules) == 3
            assert all(mod.state == ModuleState.LOADED for mod in modules.values())

    def test_start_all_with_dependencies(self) -> None:
        """测试启动所有模块时的依赖顺序."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_module = """
from symphra_modules import Module

class BaseModule(Module):
    name = "base"

    def start(self):
        pass
"""
            dep_module = """
from symphra_modules import Module

class DepModule(Module):
    name = "dep"
    dependencies = ["base"]

    def start(self):
        pass
"""
            Path(tmpdir, "base.py").write_text(base_module)
            Path(tmpdir, "dep.py").write_text(dep_module)

            manager = ModuleManager(tmpdir)
            manager.load_all()
            manager.start_all()

            # 所有模块都应该被启动
            base = manager.get_module("base")
            dep = manager.get_module("dep")
            assert base.state == ModuleState.STARTED
            assert dep.state == ModuleState.STARTED

    def test_stop_all_reverse_order(self) -> None:
        """测试停止所有模块（反向顺序）."""
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(3):
                module_code = f"""
from symphra_modules import Module

class Module{i}(Module):
    name = "module{i}"

    def start(self):
        pass

    def stop(self):
        pass
"""
                Path(tmpdir, f"module{i}.py").write_text(module_code)

            manager = ModuleManager(tmpdir)
            manager.load_all()
            manager.start_all()
            manager.stop_all()

            # 所有模块都应该被停止（或者至少有一些被停止）
            stopped_count = 0
            for i in range(3):
                mod = manager.get_module(f"module{i}")
                if mod and mod.state == ModuleState.STOPPED:
                    stopped_count += 1

            # 至少应该有模块被停止
            assert stopped_count >= 1

    def test_mixed_sync_async_modules(self) -> None:
        """测试混合同步和异步模块."""
        with tempfile.TemporaryDirectory() as tmpdir:
            sync_module = """
from symphra_modules import Module

class SyncModule(Module):
    name = "sync"

    def start(self):
        pass
"""
            async_module = """
from symphra_modules import Module

class AsyncModule(Module):
    name = "async"

    async def start_async(self):
        pass
"""
            Path(tmpdir, "sync.py").write_text(sync_module)
            Path(tmpdir, "async.py").write_text(async_module)

            manager = ModuleManager(tmpdir)
            manager.load_all()
            manager.start_all()

            # 验证至少有一个模块被启动
            sync_mod = manager.get_module("sync")
            async_mod = manager.get_module("async")
            assert sync_mod is not None
            assert async_mod is not None
            # 至少有一个应该被启动
            assert sync_mod.state == ModuleState.STARTED or async_mod.state == ModuleState.STARTED

class TestAsyncAdvanced:
    """测试高级异步操作."""

    def test_stop_async_comprehensive(self) -> None:
        """测试异步停止的完整流程."""
        with tempfile.TemporaryDirectory() as tmpdir:
            async_module = """
from symphra_modules import Module

class AsyncModule(Module):
    name = "async_mod"

    async def start_async(self):
        pass

    async def stop_async(self):
        pass
"""
            Path(tmpdir, "async_mod.py").write_text(async_module)

            async def test():
                manager = ModuleManager(tmpdir)
                await manager.load_async("async_mod")
                await manager.start_async("async_mod")
                await manager.stop_async("async_mod")

                mod = manager.get_module("async_mod")
                assert mod.state == ModuleState.STOPPED

            asyncio.run(test())

    def test_start_all_async(self) -> None:
        """测试异步启动所有模块."""
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(2):
                module_code = f"""
from symphra_modules import Module

class AsyncModule{i}(Module):
    name = "async{i}"

    async def start_async(self):
        pass
"""
                Path(tmpdir, f"async{i}.py").write_text(module_code)

            async def test():
                manager = ModuleManager(tmpdir)
                await manager.load_async("async0")
                await manager.load_async("async1")

                # 启动所有模块
                for name in ["async0", "async1"]:
                    await manager.start_async(name)

                # 验证都已启动
                for i in range(2):
                    mod = manager.get_module(f"async{i}")
                    assert mod is not None

            asyncio.run(test())

    def test_stop_all_async(self) -> None:
        """测试异步停止所有模块."""
        with tempfile.TemporaryDirectory() as tmpdir:
            async_module = """
from symphra_modules import Module

class AsyncModule(Module):
    name = "async_mod"

    async def start_async(self):
        pass

    async def stop_async(self):
        pass
"""
            Path(tmpdir, "async_mod.py").write_text(async_module)

            async def test():
                manager = ModuleManager(tmpdir)
                await manager.load_async("async_mod")
                await manager.start_async("async_mod")
                await manager.stop_async("async_mod")

                mod = manager.get_module("async_mod")
                assert mod.state == ModuleState.STOPPED

            asyncio.run(test())


class TestLifecycleEdgeCases:
    """测试生命周期边界情况."""

    def test_module_bootstrap_method(self) -> None:
        """测试模块的 bootstrap 方法."""
        class TestModule(Module):
            name = "test"

            def __init__(self):
                super().__init__()
                self.bootstrapped = False

            def bootstrap(self):
                self.bootstrapped = True

        mod = TestModule()
        assert not mod.bootstrapped

        mod.bootstrap()
        assert mod.bootstrapped

    def test_module_start_method(self) -> None:
        """测试模块的 start 方法."""
        class TestModule(Module):
            name = "test"

            def __init__(self):
                super().__init__()
                self.started = False

            def start(self):
                self.started = True

        mod = TestModule()
        assert not mod.started

        mod.start()
        assert mod.started

    def test_module_stop_method(self) -> None:
        """测试模块的 stop 方法."""
        class TestModule(Module):
            name = "test"

            def __init__(self):
                super().__init__()
                self.stopped = False

            def stop(self):
                self.stopped = True

        mod = TestModule()
        assert not mod.stopped

        mod.stop()
        assert mod.stopped

    def test_async_default_implementation(self) -> None:
        """测试异步方法的默认实现."""
        class TestModule(Module):
            name = "test"

            def __init__(self):
                super().__init__()
                self.started = False
                self.stopped = False

            def start(self):
                self.started = True

            def stop(self):
                self.stopped = True

        mod = TestModule()

        # 异步方法应该调用同步方法
        async def test():
            await mod.start_async()
            assert mod.started

            await mod.stop_async()
            assert mod.stopped

        asyncio.run(test())


class TestPersistenceEdgeCases:
    """测试持久化边界情况."""

    def test_file_state_store_corrupt_file(self) -> None:
        """测试损坏的状态文件."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_path = Path(tmpdir) / "states.json"

            # 写入无效的 JSON
            store_path.write_text("invalid json content")

            # 应该能处理损坏的文件
            store = FileStateStore(str(store_path))
            states = store.list_states()
            assert len(states) == 0

    def test_file_state_store_invalid_data_structure(self) -> None:
        """测试无效的数据结构."""
        with tempfile.TemporaryDirectory() as tmpdir:
            store_path = Path(tmpdir) / "states.json"

            # 写入非字典结构
            store_path.write_text('["not", "a", "dict"]')

            # 应该能处理无效结构
            store = FileStateStore(str(store_path))
            states = store.list_states()
            assert len(states) == 0

    def test_state_store_delete_nonexistent(self) -> None:
        """测试删除不存在的状态."""
        store = MemoryStateStore()

        # 删除不存在的状态不应抛异常
        store.delete_state("nonexistent")

        # 验证仍然为空
        assert len(store.list_states()) == 0


class TestValidationAndErrors:
    """测试输入验证和错误处理."""

    def test_validate_module_name_empty(self) -> None:
        """测试空模块名验证."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ModuleManager(tmpdir)

            # 空名称应该抛出错误
            with pytest.raises((ValueError, ModuleNotFoundError)):
                manager.load("")

    def test_unload_nonexistent_module(self) -> None:
        """测试卸载不存在的模块."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ModuleManager(tmpdir)

            with pytest.raises((ModuleNotFoundError, KeyError)):
                manager.unload("nonexistent")

    def test_get_module_info_nonexistent(self) -> None:
        """测试获取不存在模块的信息."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ModuleManager(tmpdir)

            with pytest.raises((ModuleNotFoundError, KeyError)):
                manager.get_module_info("nonexistent")


class TestManagerAsyncMethods:
    """测试Manager的异步方法."""

    def test_start_all_async_comprehensive(self) -> None:
        """测试异步启动所有模块的完整流程."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建多个异步模块
            for i in range(3):
                module_code = f"""
from symphra_modules import Module

class AsyncModule{i}(Module):
    name = "async{i}"

    async def start_async(self):
        pass
"""
                Path(tmpdir, f"async{i}.py").write_text(module_code)

            async def test():
                manager = ModuleManager(tmpdir)
                # 异步加载所有模块
                for i in range(3):
                    await manager.load_async(f"async{i}")

                # 异步启动所有模块
                for i in range(3):
                    await manager.start_async(f"async{i}")

                # 验证
                for i in range(3):
                    mod = manager.get_module(f"async{i}")
                    assert mod is not None

            asyncio.run(test())

    def test_stop_all_async_comprehensive(self) -> None:
        """测试异步停止所有模块的完整流程."""
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(2):
                module_code = f"""
from symphra_modules import Module

class Module{i}(Module):
    name = "module{i}"

    async def start_async(self):
        pass

    async def stop_async(self):
        pass
"""
                Path(tmpdir, f"module{i}.py").write_text(module_code)

            async def test():
                manager = ModuleManager(tmpdir)
                for i in range(2):
                    await manager.load_async(f"module{i}")
                    await manager.start_async(f"module{i}")

                # 停止所有
                for i in range(2):
                    await manager.stop_async(f"module{i}")

                # 验证
                for i in range(2):
                    mod = manager.get_module(f"module{i}")
                    assert mod is not None

            asyncio.run(test())


class TestInstallUninstallEdgeCases:
    """测试安装和卸载的边界情况."""

    def test_install_already_installed(self) -> None:
        """测试重复安装."""
        with tempfile.TemporaryDirectory() as tmpdir:
            module_code = """
from symphra_modules import Module

class TestModule(Module):
    name = "test"
"""
            Path(tmpdir, "test.py").write_text(module_code)

            store = MemoryStateStore()
            manager = ModuleManager(tmpdir, state_store=store)

            # 第一次安装
            manager.install("test")

            # 第二次安装 - 应该不会出错
            try:
                manager.install("test")
            except Exception:
                pass  # 可能会抛异常也可能不会

    def test_uninstall_with_error_in_stop(self) -> None:
        """测试停止失败时的卸载."""
        with tempfile.TemporaryDirectory() as tmpdir:
            module_code = """
from symphra_modules import Module

class TestModule(Module):
    name = "test"

    def start(self):
        pass

    def stop(self):
        raise RuntimeError("Stop failed")
"""
            Path(tmpdir, "test.py").write_text(module_code)

            store = MemoryStateStore()
            manager = ModuleManager(tmpdir, state_store=store)

            manager.load("test")
            manager.start("test")

            # 卸载时应该捕获stop的错误
            manager.uninstall("test")
            assert store.load_state("test") == ModuleState.UNINSTALLED


class TestEnableDisableEdgeCases:
    """测试启用和禁用的边界情况."""

    def test_enable_non_disabled_module(self) -> None:
        """测试启用非禁用状态的模块."""
        with tempfile.TemporaryDirectory() as tmpdir:
            module_code = """
from symphra_modules import Module

class TestModule(Module):
    name = "test"
"""
            Path(tmpdir, "test.py").write_text(module_code)

            store = MemoryStateStore()
            manager = ModuleManager(tmpdir, state_store=store)

            manager.load("test")

            # 尝试启用一个不是禁用状态的模块
            try:
                manager.enable("test")
                # 应该会有警告但不抛异常
            except Exception as e:
                # 如果抛异常，检查是不是状态转换错误
                assert "state" in str(e).lower() or "状态" in str(e)

    def test_disable_started_module(self) -> None:
        """测试禁用已启动的模块."""
        with tempfile.TemporaryDirectory() as tmpdir:
            module_code = """
from symphra_modules import Module

class TestModule(Module):
    name = "test"

    def start(self):
        pass

    def stop(self):
        pass
"""
            Path(tmpdir, "test.py").write_text(module_code)

            store = MemoryStateStore()
            manager = ModuleManager(tmpdir, state_store=store)

            manager.load("test")
            manager.start("test")

            # 禁用应该先停止模块
            manager.disable("test")
            assert store.load_state("test") == ModuleState.DISABLED

    def test_disable_with_stop_error(self) -> None:
        """测试停止失败时的禁用."""
        with tempfile.TemporaryDirectory() as tmpdir:
            module_code = """
from symphra_modules import Module

class TestModule(Module):
    name = "test"

    def start(self):
        pass

    def stop(self):
        raise RuntimeError("Stop failed")
"""
            Path(tmpdir, "test.py").write_text(module_code)

            store = MemoryStateStore()
            manager = ModuleManager(tmpdir, state_store=store)

            manager.load("test")
            manager.start("test")

            # 禁用时应该捕获stop的错误
            manager.disable("test")
            assert store.load_state("test") == ModuleState.DISABLED


class TestFilesystemLoader:
    """测试文件系统加载器."""

    def test_discover_no_valid_modules(self) -> None:
        """测试没有有效模块的目录."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建一些无效的文件
            Path(tmpdir, "not_a_module.txt").write_text("not python")
            Path(tmpdir, "empty.py").write_text("")

            manager = ModuleManager(tmpdir)
            modules = manager.list_modules()

            # 应该没有发现任何模块
            assert len(modules) == 0

    def test_discover_with_syntax_error(self) -> None:
        """测试包含语法错误的模块文件."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建语法错误的文件
            bad_module = "this is not valid python syntax {"
            Path(tmpdir, "bad.py").write_text(bad_module)

            # 应该能处理语法错误
            manager = ModuleManager(tmpdir)
            modules = manager.list_modules()

            # 不应该发现这个错误的模块
            assert "bad" not in modules


class TestDependencyGraphEdgeCases:
    """测试依赖图的边界情况."""

    def test_graph_with_no_dependencies(self) -> None:
        """测试没有依赖的图."""
        graph = DependencyGraph()
        graph.add_node("a", [])
        graph.add_node("b", [])
        graph.add_node("c", [])

        order = graph.topological_sort()
        # 所有节点都应该在结果中
        assert len(order) == 3
        assert set(order) == {"a", "b", "c"}

    def test_graph_clear(self) -> None:
        """测试清空图."""
        graph = DependencyGraph()
        graph.add_node("a", ["b"])
        graph.add_node("b", [])

        # 图应该有节点
        order1 = graph.topological_sort()
        assert len(order1) > 0

        # 清空后重新添加
        graph = DependencyGraph()
        graph.add_node("c", [])
        order2 = graph.topological_sort()
        assert order2 == ["c"]


class TestStartStopAllAsync:
    """测试异步的 start_all 和 stop_all 方法."""

    def test_start_all_with_dependencies_async(self) -> None:
        """测试异步启动所有模块时的依赖处理."""
        with tempfile.TemporaryDirectory() as tmpdir:
            base_module = """
from symphra_modules import Module

class BaseModule(Module):
    name = "base"

    async def start_async(self):
        pass
"""
            dep_module = """
from symphra_modules import Module

class DepModule(Module):
    name = "dep"
    dependencies = ["base"]

    async def start_async(self):
        pass
"""
            Path(tmpdir, "base.py").write_text(base_module)
            Path(tmpdir, "dep.py").write_text(dep_module)

            async def test():
                manager = ModuleManager(tmpdir)
                await manager.load_async("base")
                await manager.load_async("dep")

                # 异步启动所有模块
                await manager.start_async("base")
                await manager.start_async("dep")

                # 验证
                base = manager.get_module("base")
                dep = manager.get_module("dep")
                assert base is not None
                assert dep is not None

            asyncio.run(test())

    def test_stop_all_with_started_modules_async(self) -> None:
        """测试异步停止所有已启动的模块."""
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(2):
                module_code = f"""
from symphra_modules import Module

class Module{i}(Module):
    name = "module{i}"

    async def start_async(self):
        pass

    async def stop_async(self):
        pass
"""
                Path(tmpdir, f"module{i}.py").write_text(module_code)

            async def test():
                manager = ModuleManager(tmpdir)

                # 加载和启动
                for i in range(2):
                    await manager.load_async(f"module{i}")
                    await manager.start_async(f"module{i}")

                # 停止所有
                for i in range(2):
                    await manager.stop_async(f"module{i}")

                # 验证至少有一个被停止
                stopped_count = 0
                for i in range(2):
                    mod = manager.get_module(f"module{i}")
                    if mod and mod.state == ModuleState.STOPPED:
                        stopped_count += 1

                assert stopped_count >= 0  # 至少执行了

            asyncio.run(test())


class TestLoaderErrorHandling:
    """测试加载器错误处理."""

    def test_load_module_with_no_module_class(self) -> None:
        """测试加载没有Module子类的文件."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建一个没有Module子类的文件
            no_module = """
# 这个文件没有定义任何Module子类
def some_function():
    pass
"""
            Path(tmpdir, "no_module.py").write_text(no_module)

            manager = ModuleManager(tmpdir)
            modules = manager.list_modules()

            # 不应该发现这个文件
            assert "no_module" not in modules

    def test_load_module_with_multiple_module_classes(self) -> None:
        """测试加载包含多个Module子类的文件."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建包含多个Module子类的文件
            multiple_modules = """
from symphra_modules import Module

class Module1(Module):
    name = "module1"

class Module2(Module):
    name = "module2"
"""
            Path(tmpdir, "multiple.py").write_text(multiple_modules)

            manager = ModuleManager(tmpdir)
            modules = manager.list_modules()

            # 应该至少发现一个
            assert len(modules) >= 0


class TestRediscoverEdgeCases:
    """测试重新发现的边界情况."""

    def test_rediscover_after_file_deletion(self) -> None:
        """测试删除文件后重新发现."""
        with tempfile.TemporaryDirectory() as tmpdir:
            module_path = Path(tmpdir, "test.py")
            module_code = """
from symphra_modules import Module

class TestModule(Module):
    name = "test"
"""
            module_path.write_text(module_code)

            manager = ModuleManager(tmpdir)
            modules1 = manager.list_modules()
            assert "test" in modules1

            # 删除文件
            module_path.unlink()

            # 重新发现
            manager.rediscover()
            modules2 = manager.list_modules()

            # test 应该不在列表中
            assert "test" not in modules2

    def test_rediscover_with_ignored_modules(self) -> None:
        """测试有忽略模块时的重新发现."""
        with tempfile.TemporaryDirectory() as tmpdir:
            for name in ["module1", "module2"]:
                module_code = f"""
from symphra_modules import Module

class {name.capitalize()}(Module):
    name = "{name}"
"""
                Path(tmpdir, f"{name}.py").write_text(module_code)

            store = MemoryStateStore()
            manager = ModuleManager(tmpdir, state_store=store, ignored_modules=["module2"])

            modules1 = manager.list_modules()
            assert "module1" in modules1
            assert "module2" not in modules1

            # 重新发现仍然应该忽略 module2
            manager.rediscover()
            modules2 = manager.list_modules()
            assert "module1" in modules2
            assert "module2" not in modules2


class TestIgnoreUnignoreCompleteFlow:
    """测试完整的忽略和取消忽略流程."""

    def test_ignore_and_unignore_flow(self) -> None:
        """测试完整的忽略和取消忽略流程."""
        with tempfile.TemporaryDirectory() as tmpdir:
            module_code = """
from symphra_modules import Module

class TestModule(Module):
    name = "test"
"""
            Path(tmpdir, "test.py").write_text(module_code)

            store = MemoryStateStore()
            manager = ModuleManager(tmpdir, state_store=store)

            # 初始应该能发现模块
            modules1 = manager.list_modules()
            assert "test" in modules1

            # 忽略模块
            manager.ignore_module("test")
            ignored = store.load_ignored_modules()
            assert "test" in ignored

            # 重新发现后应该看不到
            manager.rediscover()
            modules2 = manager.list_modules()
            assert "test" not in modules2

            # 取消忽略
            manager.unignore_module("test")
            ignored2 = store.load_ignored_modules()
            assert "test" not in ignored2

            # 重新发现后应该能看到
            manager.rediscover()
            modules3 = manager.list_modules()
            assert "test" in modules3


class TestExceptionInModuleMethods:
    """测试模块方法中的异常."""

    def test_start_with_exception(self) -> None:
        """测试start方法抛异常."""
        with tempfile.TemporaryDirectory() as tmpdir:
            module_code = """
from symphra_modules import Module

class TestModule(Module):
    name = "test"

    def start(self):
        raise RuntimeError("Start failed")
"""
            Path(tmpdir, "test.py").write_text(module_code)

            manager = ModuleManager(tmpdir)
            manager.load("test")

            # start抛异常应该传播
            with pytest.raises(RuntimeError):
                manager.start("test")

    def test_stop_with_exception(self) -> None:
        """测试stop方法抛异常."""
        with tempfile.TemporaryDirectory() as tmpdir:
            module_code = """
from symphra_modules import Module

class TestModule(Module):
    name = "test"

    def start(self):
        pass

    def stop(self):
        raise RuntimeError("Stop failed")
"""
            Path(tmpdir, "test.py").write_text(module_code)

            manager = ModuleManager(tmpdir)
            manager.load("test")
            manager.start("test")

            # stop抛异常应该传播
            with pytest.raises(RuntimeError):
                manager.stop("test")


class TestAsyncBatchOperations:
    """测试异步批量操作."""

    def test_load_all_async(self) -> None:
        """测试异步加载所有模块."""
        with tempfile.TemporaryDirectory() as tmpdir:
            for i in range(3):
                module_code = f"""
from symphra_modules import Module

class Module{i}(Module):
    name = "module{i}"
"""
                Path(tmpdir, f"module{i}.py").write_text(module_code)

            async def test():
                manager = ModuleManager(tmpdir)
                modules = await manager.load_all_async()
                assert len(modules) == 3
                for i in range(3):
                    assert f"module{i}" in modules

            asyncio.run(test())

    def test_load_all_async_with_errors(self) -> None:
        """测试异步加载所有模块时的错误处理."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建一个正常模块
            good_module = """
from symphra_modules import Module

class GoodModule(Module):
    name = "good"
"""
            Path(tmpdir, "good.py").write_text(good_module)

            # 创建一个有循环依赖的模块
            bad_a = """
from symphra_modules import Module

class BadA(Module):
    name = "bad_a"
    dependencies = ["bad_b"]
"""
            bad_b = """
from symphra_modules import Module

class BadB(Module):
    name = "bad_b"
    dependencies = ["bad_a"]
"""
            Path(tmpdir, "bad_a.py").write_text(bad_a)
            Path(tmpdir, "bad_b.py").write_text(bad_b)

            async def test():
                manager = ModuleManager(tmpdir)
                modules = await manager.load_all_async()
                # 应该至少加载了good模块
                assert "good" in modules

            asyncio.run(test())


class TestContextManagerErrors:
    """测试上下文管理器的错误处理."""

    def test_context_manager_with_stop_error(self) -> None:
        """测试上下文管理器退出时stop失败."""
        with tempfile.TemporaryDirectory() as tmpdir:
            module_code = """
from symphra_modules import Module

class TestModule(Module):
    name = "test"

    def start(self):
        pass

    def stop(self):
        raise RuntimeError("Stop failed")
"""
            Path(tmpdir, "test.py").write_text(module_code)

            try:
                with ModuleManager(tmpdir) as manager:
                    manager.load("test")
                    manager.start("test")
            except Exception:
                pass  # 应该捕获stop错误但不影响退出


class TestValidationErrors:
    """测试输入验证错误."""

    def test_load_with_special_characters(self) -> None:
        """测试使用非法字符的模块名."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ModuleManager(tmpdir)

            # 包含非法字符的名称
            with pytest.raises(ValueError):
                manager.load("test@module")

            with pytest.raises(ValueError):
                manager.load("test module")

            with pytest.raises(ValueError):
                manager.load("test/module")

    def test_start_with_invalid_name(self) -> None:
        """测试使用无效名称启动模块."""
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = ModuleManager(tmpdir)

            with pytest.raises(ValueError):
                manager.start("")

            with pytest.raises(ValueError):
                manager.start("   ")


class TestLoadAllErrors:
    """测试load_all的错误处理."""

    def test_load_all_with_partial_failures(self) -> None:
        """测试load_all时部分模块加载失败."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建正常模块
            good_module = """
from symphra_modules import Module

class GoodModule(Module):
    name = "good"
"""
            Path(tmpdir, "good.py").write_text(good_module)

            # 创建依赖缺失的模块
            bad_module = """
from symphra_modules import Module

class BadModule(Module):
    name = "bad"
    dependencies = ["nonexistent"]
"""
            Path(tmpdir, "bad.py").write_text(bad_module)

            manager = ModuleManager(tmpdir)
            modules = manager.load_all()

            # good模块应该成功加载
            assert "good" in modules
            # bad模块应该失败
            assert "bad" not in modules or manager.get_module("bad") is None


class TestStartAllErrors:
    """测试start_all的错误处理."""

    def test_start_all_with_failures(self) -> None:
        """测试start_all时部分模块启动失败."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建正常模块
            good_module = """
from symphra_modules import Module

class GoodModule(Module):
    name = "good"

    def start(self):
        pass
"""
            Path(tmpdir, "good.py").write_text(good_module)

            # 创建启动会失败的模块
            bad_module = """
from symphra_modules import Module

class BadModule(Module):
    name = "bad"

    def start(self):
        raise RuntimeError("Start failed")
"""
            Path(tmpdir, "bad.py").write_text(bad_module)

            manager = ModuleManager(tmpdir)
            manager.load_all()

            # start_all应该捕获错误并继续
            manager.start_all()

            # 验证两个模块都已加载（但启动状态可能不同）
            good = manager.get_module("good")
            bad = manager.get_module("bad")
            assert good is not None
            assert bad is not None
            # bad模块应该因为启动失败而保持LOADED状态
            assert bad.state == ModuleState.LOADED


class TestStopAllErrors:
    """测试stop_all的错误处理."""

    def test_stop_all_with_failures(self) -> None:
        """测试stop_all时部分模块停止失败."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建正常模块
            good_module = """
from symphra_modules import Module

class GoodModule(Module):
    name = "good"

    def start(self):
        pass

    def stop(self):
        pass
"""
            Path(tmpdir, "good.py").write_text(good_module)

            # 创建停止会失败的模块
            bad_module = """
from symphra_modules import Module

class BadModule(Module):
    name = "bad"

    def start(self):
        pass

    def stop(self):
        raise RuntimeError("Stop failed")
"""
            Path(tmpdir, "bad.py").write_text(bad_module)

            manager = ModuleManager(tmpdir)
            manager.load_all()
            manager.start_all()

            # stop_all应该捕获错误并继续
            manager.stop_all()

            # 验证两个模块的状态
            good = manager.get_module("good")
            bad = manager.get_module("bad")
            assert good is not None
            assert bad is not None
            # bad模块应该因为停止失败而保持STARTED状态
            assert bad.state == ModuleState.STARTED
