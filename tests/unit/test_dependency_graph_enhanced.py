"""依赖图增强功能测试."""

from symphra_modules.config import ModuleMetadata
from symphra_modules.resolver import DependencyGraph


def test_remove_module_basic() -> None:
    """测试基本的模块移除功能."""
    graph = DependencyGraph()
    graph.add_module(ModuleMetadata(name="a"))
    graph.add_module(ModuleMetadata(name="b", dependencies=["a"]))

    # 移除模块 b
    graph.remove_module("b")

    assert not graph.has_module("b")
    assert graph.has_module("a")
    assert graph.get_dependencies("b") == set()


def test_remove_module_cleans_dependencies() -> None:
    """测试移除模块时正确清理依赖关系."""
    graph = DependencyGraph()
    graph.add_module(ModuleMetadata(name="base"))
    graph.add_module(ModuleMetadata(name="module1", dependencies=["base"]))
    graph.add_module(ModuleMetadata(name="module2", dependencies=["base"]))

    # 移除 base 模块
    graph.remove_module("base")

    # base 应该被移除
    assert not graph.has_module("base")

    # module1 和 module2 对 base 的依赖应该被清理
    assert "base" not in graph.get_dependencies("module1")
    assert "base" not in graph.get_dependencies("module2")


def test_remove_module_cleans_reverse_dependencies() -> None:
    """测试移除模块时正确清理反向依赖关系."""
    graph = DependencyGraph()
    graph.add_module(ModuleMetadata(name="base"))
    graph.add_module(ModuleMetadata(name="module1", dependencies=["base"]))

    # 移除 module1
    graph.remove_module("module1")

    # base 的依赖者列表应该不再包含 module1
    assert "module1" not in graph.get_dependents("base")


def test_remove_nonexistent_module() -> None:
    """测试移除不存在的模块不抛出异常."""
    graph = DependencyGraph()
    graph.add_module(ModuleMetadata(name="a"))

    # 移除不存在的模块应该不抛出异常
    graph.remove_module("nonexistent")

    # 原有模块应该保持不变
    assert graph.has_module("a")


def test_copy_creates_independent_graph() -> None:
    """测试 copy 方法创建独立的依赖图副本."""
    graph = DependencyGraph()
    graph.add_module(ModuleMetadata(name="a"))
    graph.add_module(ModuleMetadata(name="b", dependencies=["a"]))

    # 创建副本
    copied_graph = graph.copy()

    # 修改副本不应影响原图
    copied_graph.add_module(ModuleMetadata(name="c"))

    assert copied_graph.has_module("c")
    assert not graph.has_module("c")


def test_copy_preserves_all_data() -> None:
    """测试 copy 方法正确复制所有数据."""
    graph = DependencyGraph()
    graph.add_module(ModuleMetadata(name="a"))
    graph.add_module(ModuleMetadata(name="b", dependencies=["a"]))
    graph.add_module(ModuleMetadata(name="c", dependencies=["a", "b"]))

    copied_graph = graph.copy()

    # 验证所有模块都被复制
    assert copied_graph.has_module("a")
    assert copied_graph.has_module("b")
    assert copied_graph.has_module("c")

    # 验证依赖关系被正确复制
    assert copied_graph.get_dependencies("b") == {"a"}
    assert copied_graph.get_dependencies("c") == {"a", "b"}

    # 验证反向依赖关系被正确复制
    assert copied_graph.get_dependents("a") == {"b", "c"}
    assert copied_graph.get_dependents("b") == {"c"}


def test_copy_deep_independence() -> None:
    """测试 copy 方法创建深拷贝（修改集合不互相影响）."""
    graph = DependencyGraph()
    graph.add_module(ModuleMetadata(name="a"))
    graph.add_module(ModuleMetadata(name="b", dependencies=["a"]))

    copied_graph = graph.copy()

    # 在副本中移除模块
    copied_graph.remove_module("b")

    # 原图应该保持不变
    assert graph.has_module("b")
    assert graph.get_dependencies("b") == {"a"}
    assert "b" in graph.get_dependents("a")


def test_get_reverse_dependencies_basic() -> None:
    """测试基本的反向依赖获取."""
    graph = DependencyGraph()
    graph.add_module(ModuleMetadata(name="base"))
    graph.add_module(ModuleMetadata(name="module1", dependencies=["base"]))
    graph.add_module(ModuleMetadata(name="module2", dependencies=["base"]))

    reverse_deps = graph.get_reverse_dependencies("base")

    # 应该包含直接依赖 base 的模块
    assert "base" in reverse_deps
    assert reverse_deps["base"] == {"module1", "module2"}


def test_get_reverse_dependencies_transitive() -> None:
    """测试传递性反向依赖获取."""
    graph = DependencyGraph()
    graph.add_module(ModuleMetadata(name="a"))
    graph.add_module(ModuleMetadata(name="b", dependencies=["a"]))
    graph.add_module(ModuleMetadata(name="c", dependencies=["b"]))
    graph.add_module(ModuleMetadata(name="d", dependencies=["c"]))

    reverse_deps = graph.get_reverse_dependencies("a")

    # 应该包含所有传递性依赖 a 的模块
    assert "a" in reverse_deps
    assert reverse_deps["a"] == {"b"}

    assert "b" in reverse_deps
    assert reverse_deps["b"] == {"c"}

    assert "c" in reverse_deps
    assert reverse_deps["c"] == {"d"}


def test_get_reverse_dependencies_nonexistent() -> None:
    """测试获取不存在模块的反向依赖."""
    graph = DependencyGraph()
    graph.add_module(ModuleMetadata(name="a"))

    reverse_deps = graph.get_reverse_dependencies("nonexistent")

    # 应该返回空字典
    assert reverse_deps == {}


def test_get_reverse_dependencies_no_dependents() -> None:
    """测试获取没有依赖者的模块的反向依赖."""
    graph = DependencyGraph()
    graph.add_module(ModuleMetadata(name="a"))
    graph.add_module(ModuleMetadata(name="b"))

    reverse_deps = graph.get_reverse_dependencies("a")

    # 应该返回空字典（没有模块依赖 a）
    assert reverse_deps == {}


def test_get_reverse_dependencies_complex() -> None:
    """测试复杂依赖图的反向依赖获取."""
    graph = DependencyGraph()
    graph.add_module(ModuleMetadata(name="core"))
    graph.add_module(ModuleMetadata(name="db", dependencies=["core"]))
    graph.add_module(ModuleMetadata(name="api", dependencies=["core", "db"]))
    graph.add_module(ModuleMetadata(name="web", dependencies=["api"]))

    reverse_deps = graph.get_reverse_dependencies("core")

    # core 的直接依赖者
    assert "core" in reverse_deps
    assert reverse_deps["core"] == {"db", "api"}

    # db 的直接依赖者
    assert "db" in reverse_deps
    assert reverse_deps["db"] == {"api"}

    # api 的直接依赖者
    assert "api" in reverse_deps
    assert reverse_deps["api"] == {"web"}
