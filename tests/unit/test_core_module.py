"""核心模块（Module基类）单元测试.

测试Module类的基本功能、属性、生命周期方法等。
"""

import asyncio
from datetime import datetime

import pytest

from symphra_modules import Module, ModuleState, call_module_method, is_async_module


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

    def test_module_loaded_at(self) -> None:
        """测试模块加载时间."""

        class TestModule(Module):
            name = "test"

        before = datetime.now()
        mod = TestModule()
        after = datetime.now()

        assert before <= mod.loaded_at <= after

    def test_module_repr(self) -> None:
        """测试模块字符串表示."""

        class TestModule(Module):
            name = "test"

        mod = TestModule()
        repr_str = repr(mod)
        assert "TestModule" in repr_str
        assert "test" in repr_str
        assert "loaded" in repr_str.lower()


class TestModuleHelpers:
    """测试模块辅助函数."""

    def test_is_async_module(self) -> None:
        """测试异步模块检测."""

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
