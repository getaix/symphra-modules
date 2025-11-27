"""依赖解析器测试."""

import pytest
from symphra_modules.config import ModuleMetadata
from symphra_modules.exceptions import ModuleDependencyError
from symphra_modules.resolver import DependencyGraph, DependencyResolver


def test_dependency_graph_add_module() -> None:
    """测试添加模块到依赖图."""
    graph = DependencyGraph()
    metadata = ModuleMetadata(name="test", dependencies=["dep1", "dep2"])

    graph.add_module(metadata)

    assert graph.has_module("test")
    assert graph.get_dependencies("test") == {"dep1", "dep2"}


def test_dependency_graph_get_dependents() -> None:
    """测试获取依赖者."""
    graph = DependencyGraph()
    graph.add_module(ModuleMetadata(name="base"))
    graph.add_module(ModuleMetadata(name="module1", dependencies=["base"]))
    graph.add_module(ModuleMetadata(name="module2", dependencies=["base"]))

    dependents = graph.get_dependents("base")
    assert dependents == {"module1", "module2"}


def test_dependency_graph_get_all_modules() -> None:
    """测试获取所有模块."""
    graph = DependencyGraph()
    graph.add_module(ModuleMetadata(name="module1"))
    graph.add_module(ModuleMetadata(name="module2"))

    modules = graph.get_all_modules()
    assert set(modules) == {"module1", "module2"}


def test_dependency_resolver_simple_order() -> None:
    """测试简单的依赖顺序解析."""
    resolver = DependencyResolver()
    resolver.add_module(ModuleMetadata(name="base"))
    resolver.add_module(ModuleMetadata(name="dependent", dependencies=["base"]))

    order = resolver.resolve()
    assert order == ["base", "dependent"]


def test_dependency_resolver_complex_order() -> None:
    """测试复杂的依赖顺序解析."""
    resolver = DependencyResolver()
    resolver.add_module(ModuleMetadata(name="a"))
    resolver.add_module(ModuleMetadata(name="b", dependencies=["a"]))
    resolver.add_module(ModuleMetadata(name="c", dependencies=["a", "b"]))
    resolver.add_module(ModuleMetadata(name="d", dependencies=["b"]))

    order = resolver.resolve()

    # a必须在最前面
    assert order[0] == "a"
    # b必须在c和d之前
    b_index = order.index("b")
    assert order.index("c") > b_index
    assert order.index("d") > b_index


def test_dependency_resolver_circular_dependency() -> None:
    """测试循环依赖检测."""
    resolver = DependencyResolver()
    resolver.add_module(ModuleMetadata(name="a", dependencies=["b"]))
    resolver.add_module(ModuleMetadata(name="b", dependencies=["a"]))

    with pytest.raises(ModuleDependencyError) as exc_info:
        resolver.resolve()
    assert "循环依赖" in str(exc_info.value)


def test_dependency_resolver_missing_dependency() -> None:
    """测试缺失依赖检测."""
    resolver = DependencyResolver()
    resolver.add_module(ModuleMetadata(name="a", dependencies=["missing"]))

    with pytest.raises(ModuleDependencyError) as exc_info:
        resolver.resolve()
    assert "缺失依赖" in str(exc_info.value)


def test_dependency_resolver_get_load_order_for_module() -> None:
    """测试获取单个模块的加载顺序."""
    resolver = DependencyResolver()
    resolver.add_module(ModuleMetadata(name="a"))
    resolver.add_module(ModuleMetadata(name="b", dependencies=["a"]))
    resolver.add_module(ModuleMetadata(name="c", dependencies=["a", "b"]))

    order = resolver.get_load_order_for_module("c")
    assert order == ["a", "b", "c"]


def test_dependency_resolver_get_load_order_module_not_found() -> None:
    """测试获取不存在模块的加载顺序."""
    resolver = DependencyResolver()
    with pytest.raises(ModuleDependencyError) as exc_info:
        resolver.get_load_order_for_module("nonexistent")
    assert "模块不存在" in str(exc_info.value)


def test_dependency_resolver_get_load_order_circular() -> None:
    """测试单模块加载顺序的循环依赖检测."""
    resolver = DependencyResolver()
    resolver.add_module(ModuleMetadata(name="a", dependencies=["b"]))
    resolver.add_module(ModuleMetadata(name="b", dependencies=["a"]))

    with pytest.raises(ModuleDependencyError) as exc_info:
        resolver.get_load_order_for_module("a")
    assert "循环依赖" in str(exc_info.value)


def test_dependency_resolver_get_load_order_missing() -> None:
    """测试单模块加载顺序的缺失依赖检测."""
    resolver = DependencyResolver()
    resolver.add_module(ModuleMetadata(name="a", dependencies=["missing"]))

    with pytest.raises(ModuleDependencyError) as exc_info:
        resolver.get_load_order_for_module("a")
    assert "缺失依赖" in str(exc_info.value)


def test_dependency_resolver_independent_modules() -> None:
    """测试独立模块的解析."""
    resolver = DependencyResolver()
    resolver.add_module(ModuleMetadata(name="a"))
    resolver.add_module(ModuleMetadata(name="b"))
    resolver.add_module(ModuleMetadata(name="c"))

    order = resolver.resolve()
    # 独立模块顺序不确定，但应该包含所有模块
    assert set(order) == {"a", "b", "c"}
    assert len(order) == 3
