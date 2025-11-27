"""补充测试用例，提升代码覆盖率到 90%.

专门覆盖未被测试的代码路径：
- core/module.py 的默认实现和边缘情况
- dependency/graph.py 的 remove_node 和 get_all_nodes
- manager.py 的列表路径、异常处理等
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from symphra_modules import Module, ModuleManager
from symphra_modules.core import FileStateStore, ModuleState
from symphra_modules.core.module import is_async_module
from symphra_modules.dependency.graph import DependencyGraph

# ============================================================================
# core/module.py 测试
# ============================================================================


def test_module_default_bootstrap() -> None:
    """测试模块默认的 bootstrap 实现（空操作）."""

    class MinimalModule(Module):
        name = "minimal"
        version = "1.0.0"

    module = MinimalModule()
    # 调用默认的 bootstrap，应该不抛异常
    module.bootstrap()  # 覆盖 line 52


def test_module_default_start() -> None:
    """测试模块默认的 start 实现（空操作）."""

    class MinimalModule(Module):
        name = "minimal"
        version = "1.0.0"

    module = MinimalModule()
    # 调用默认的 start，应该不抛异常
    module.start()  # 覆盖 line 59


@pytest.mark.asyncio
async def test_module_default_stop_async() -> None:
    """测试模块默认的 stop_async 实现（调用同步方法）."""

    class MinimalModule(Module):
        name = "minimal"
        version = "1.0.0"

        def __init__(self) -> None:
            super().__init__()
            self.stop_called = False

        def stop(self) -> None:
            self.stop_called = True

    module = MinimalModule()
    # 调用默认的 stop_async，应该调用同步的 stop
    await module.stop_async()  # 覆盖 line 82
    assert module.stop_called


def test_is_async_module_missing_method() -> None:
    """测试 is_async_module 当模块缺少异步方法时返回 False."""

    class NoAsyncModule(Module):
        name = "no_async"
        version = "1.0.0"

        # 删除继承的异步方法
        def __delattr__(self, name: str) -> None:
            pass

    module = NoAsyncModule()
    # 手动删除异步方法属性
    if hasattr(module, "start_async"):
        delattr(module, "start_async")

    # 缺少方法时应该返回 False
    result = is_async_module(module)  # 覆盖 line 115
    assert result is False


def test_is_async_module_non_coroutine_method() -> None:
    """测试 is_async_module 当方法不是协程时返回 False."""

    class SyncMethodModule(Module):
        name = "sync_method"
        version = "1.0.0"

        # 覆盖为非协程方法
        def start_async(self) -> None:  # type: ignore
            pass

        def stop_async(self) -> None:  # type: ignore
            pass

    module = SyncMethodModule()
    result = is_async_module(module)  # 覆盖 line 125
    assert result is False


def test_is_async_module_cannot_get_source() -> None:
    """测试 is_async_module 当无法获取源码时返回 True."""

    class BuiltinLikeModule(Module):
        name = "builtin_like"
        version = "1.0.0"

    module = BuiltinLikeModule()

    # Mock inspect.getsource 使其抛出异常
    with patch("symphra_modules.core.module.inspect.getsource", side_effect=OSError):
        result = is_async_module(module)  # 覆盖 lines 138-140
        # 无法获取源码时，假设是真正的异步实现
        assert result is True


# ============================================================================
# dependency/graph.py 测试
# ============================================================================


def test_dependency_graph_remove_node() -> None:
    """测试 DependencyGraph.remove_node 方法."""
    graph = DependencyGraph()

    # 添加节点
    graph.add_node("A", [])
    graph.add_node("B", ["A"])
    graph.add_node("C", ["A", "B"])

    # 移除节点 B
    graph.remove_node("B")  # 覆盖 lines 69-79

    # 验证 B 已被移除
    assert not graph.has_node("B")

    # 验证 C 的依赖中不再有 B
    c_deps = graph.get_dependencies("C")
    assert "B" not in c_deps
    assert "A" in c_deps

    # 验证拓扑排序仍然有效
    result = graph.topological_sort()
    assert "B" not in result
    assert "A" in result
    assert "C" in result


def test_dependency_graph_remove_nonexistent_node() -> None:
    """测试移除不存在的节点（不应报错）."""
    graph = DependencyGraph()
    graph.add_node("A", [])

    # 移除不存在的节点，应该不抛异常
    graph.remove_node("nonexistent")  # 覆盖 lines 69-79

    # 验证图仍然正常
    assert graph.has_node("A")


def test_dependency_graph_get_all_nodes() -> None:
    """测试 DependencyGraph.get_all_nodes 方法."""
    graph = DependencyGraph()

    # 添加多个节点
    graph.add_node("A", [])
    graph.add_node("B", ["A"])
    graph.add_node("C", ["B"])

    # 获取所有节点
    all_nodes = graph.get_all_nodes()  # 覆盖 lines 176-177

    # 验证返回所有节点
    assert len(all_nodes) == 3
    assert "A" in all_nodes
    assert "B" in all_nodes
    assert "C" in all_nodes


# ============================================================================
# manager.py 测试
# ============================================================================


def test_manager_with_multiple_module_directories(tmp_path: Path) -> None:
    """测试 ModuleManager 使用多个模块目录."""
    # 创建两个目录
    dir1 = tmp_path / "modules1"
    dir2 = tmp_path / "modules2"
    dir1.mkdir()
    dir2.mkdir()

    # 在第一个目录创建模块
    (dir1 / "module1.py").write_text(
        """
from symphra_modules import Module

class Module1(Module):
    name = "module1"
    version = "1.0.0"
    dependencies = []
"""
    )

    # 在第二个目录创建模块
    (dir2 / "module2.py").write_text(
        """
from symphra_modules import Module

class Module2(Module):
    name = "module2"
    version = "1.0.0"
    dependencies = []
"""
    )

    # 使用列表路径创建管理器
    manager = ModuleManager([dir1, dir2])  # 覆盖 line 67

    # 验证两个模块都被发现
    modules = manager.list_modules()
    assert "module1" in modules
    assert "module2" in modules


def test_manager_with_state_store_and_ignored_modules(tmp_path: Path) -> None:
    """测试 ModuleManager 同时使用 state_store 和 ignored_modules 参数."""
    state_file = tmp_path / "states.json"
    module_dir = tmp_path / "modules"
    module_dir.mkdir()

    # 创建测试模块
    (module_dir / "test1.py").write_text(
        """
from symphra_modules import Module

class Test1(Module):
    name = "test1"
    version = "1.0.0"
    dependencies = []
"""
    )

    (module_dir / "test2.py").write_text(
        """
from symphra_modules import Module

class Test2(Module):
    name = "test2"
    version = "1.0.0"
    dependencies = []
"""
    )

    # 创建 state_store，先保存一个忽略的模块
    store = FileStateStore(state_file)
    store.save_ignored_modules({"test1"})

    # 创建管理器时，同时提供 state_store 和额外的 ignored_modules
    manager = ModuleManager(
        module_dir, state_store=store, ignored_modules={"test2"}
    )  # 覆盖 lines 86-87

    # 验证两个模块都被忽略
    modules = manager.list_modules()
    assert "test1" not in modules
    assert "test2" not in modules


def test_manager_context_exit_with_exception(tmp_path: Path) -> None:
    """测试 ModuleManager 上下文管理器退出时的异常处理."""
    module_file = tmp_path / "bad_module.py"
    module_file.write_text(
        """
from symphra_modules import Module

class BadModule(Module):
    name = "bad"
    version = "1.0.0"
    dependencies = []

    def stop(self):
        raise RuntimeError("Stop failed")
"""
    )

    # 使用上下文管理器
    try:
        with ModuleManager(tmp_path) as manager:
            manager.load("bad")
            manager.start("bad")
            # 在退出时会调用 stop_all，bad 模块的 stop 会失败
            # 但不应该抛出异常，只是记录日志
    except Exception:
        # 不应该到这里
        pytest.fail("Context manager should not raise exception on exit")
    # 覆盖 lines 111-112


def test_manager_unload_with_stop_exception(tmp_path: Path) -> None:
    """测试 unload 时停止模块失败的异常处理."""
    module_file = tmp_path / "bad_stop.py"
    module_file.write_text(
        """
from symphra_modules import Module

class BadStopModule(Module):
    name = "bad_stop"
    version = "1.0.0"
    dependencies = []

    def start(self):
        pass

    def stop(self):
        raise RuntimeError("Stop failed!")
"""
    )

    manager = ModuleManager(tmp_path)
    manager.load("bad_stop")
    manager.start("bad_stop")

    # unload 应该尝试停止模块，即使停止失败也应该继续卸载
    manager.unload("bad_stop")  # 覆盖 lines 311-314

    # 验证模块已被卸载
    assert manager.get_module("bad_stop") is None


def test_manager_start_all_with_topological_sort_failure(tmp_path: Path) -> None:
    """测试 start_all 时拓扑排序失败的异常处理."""
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

    # Mock 拓扑排序失败
    with patch.object(
        manager._resolver.get_graph(), "topological_sort", side_effect=Exception("Mocked error")
    ):
        # start_all 应该回退到使用实例顺序
        manager.start_all()  # 覆盖 lines 361-363

    # 验证模块仍然启动成功
    module = manager.get_module("test")
    assert module is not None
    assert module.state == ModuleState.STARTED


# ============================================================================
# 其他边缘情况
# ============================================================================


def test_dependency_graph_remove_updates_cache() -> None:
    """测试移除节点后缓存被标记为脏."""
    graph = DependencyGraph()

    graph.add_node("A", [])
    graph.add_node("B", ["A"])

    # 执行拓扑排序，缓存结果
    result1 = graph.topological_sort()
    assert "B" in result1

    # 移除节点 B
    graph.remove_node("B")

    # 再次执行拓扑排序，应该返回新结果
    result2 = graph.topological_sort()
    assert "B" not in result2
    assert result1 != result2
