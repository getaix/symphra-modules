"""依赖图高级测试.

测试覆盖：
- 复杂依赖图
- 边缘情况
- 错误处理
"""

import pytest

from symphra_modules.core.exceptions import CircularDependencyError
from symphra_modules.dependency.graph import DependencyGraph


def test_add_module_without_dependencies() -> None:
    """测试添加没有依赖的模块."""
    graph = DependencyGraph()
    graph.add_node("module1", [])

    assert graph.has_node("module1")
    assert graph.get_dependencies("module1") == set()


def test_add_module_with_single_dependency() -> None:
    """测试添加有单个依赖的模块."""
    graph = DependencyGraph()
    graph.add_node("base", [])
    graph.add_node("dependent", ["base"])

    assert graph.get_dependencies("dependent") == {"base"}


def test_add_module_with_multiple_dependencies() -> None:
    """测试添加有多个依赖的模块."""
    graph = DependencyGraph()
    graph.add_node("base1", [])
    graph.add_node("base2", [])
    graph.add_node("dependent", ["base1", "base2"])

    deps = graph.get_dependencies("dependent")
    assert "base1" in deps
    assert "base2" in deps


def test_has_module() -> None:
    """测试检查模块是否存在."""
    graph = DependencyGraph()
    graph.add_node("module1", [])

    assert graph.has_node("module1")
    assert not graph.has_node("nonexistent")


def test_get_dependencies_nonexistent_module() -> None:
    """测试获取不存在模块的依赖."""
    graph = DependencyGraph()

    # 获取不存在模块的依赖应返回空集合
    assert graph.get_dependencies("nonexistent") == set()


def test_topological_sort_empty_graph() -> None:
    """测试空图的拓扑排序."""
    graph = DependencyGraph()
    result = graph.topological_sort()

    assert result == []


def test_topological_sort_single_module() -> None:
    """测试单个模块的拓扑排序."""
    graph = DependencyGraph()
    graph.add_node("module1", [])

    result = graph.topological_sort()
    assert result == ["module1"]


def test_topological_sort_linear_dependencies() -> None:
    """测试线性依赖链的拓扑排序."""
    graph = DependencyGraph()
    graph.add_node("a", [])
    graph.add_node("b", ["a"])
    graph.add_node("c", ["b"])
    graph.add_node("d", ["c"])

    result = graph.topological_sort()

    # 验证顺序：a 必须在 b 前面，b 必须在 c 前面，c 必须在 d 前面
    assert result.index("a") < result.index("b")
    assert result.index("b") < result.index("c")
    assert result.index("c") < result.index("d")


def test_topological_sort_diamond_dependencies() -> None:
    """测试菱形依赖的拓扑排序."""
    graph = DependencyGraph()
    #     a
    #    / \
    #   b   c
    #    \ /
    #     d
    graph.add_node("a", [])
    graph.add_node("b", ["a"])
    graph.add_node("c", ["a"])
    graph.add_node("d", ["b", "c"])

    result = graph.topological_sort()

    # a 必须在最前面
    assert result[0] == "a"
    # b 和 c 必须在 d 前面
    assert result.index("b") < result.index("d")
    assert result.index("c") < result.index("d")


def test_topological_sort_multiple_roots() -> None:
    """测试多个根节点的拓扑排序."""
    graph = DependencyGraph()
    graph.add_node("root1", [])
    graph.add_node("root2", [])
    graph.add_node("child1", ["root1"])
    graph.add_node("child2", ["root2"])

    result = graph.topological_sort()

    # 验证依赖关系
    assert result.index("root1") < result.index("child1")
    assert result.index("root2") < result.index("child2")


def test_circular_dependency_direct() -> None:
    """测试直接循环依赖检测."""
    graph = DependencyGraph()
    graph.add_node("a", [])
    graph.add_node("b", ["a"])
    graph.add_node("a", ["b"])  # 修改 a 使其依赖 b，形成循环 a->b->a

    # 循环依赖在拓扑排序时被检测
    with pytest.raises(CircularDependencyError) as exc_info:
        graph.topological_sort()

    error_msg = str(exc_info.value)
    assert "循环依赖" in error_msg or "Circular" in error_msg


def test_circular_dependency_indirect() -> None:
    """测试间接循环依赖检测."""
    graph = DependencyGraph()

    # 创建循环: a -> b -> c -> a
    graph.add_node("a", [])
    graph.add_node("b", ["a"])
    graph.add_node("c", ["b"])
    graph.add_node("a", ["c"])  # 修改 a 使其依赖 c，形成循环

    # 循环依赖在拓扑排序时被检测
    with pytest.raises(CircularDependencyError):
        graph.topological_sort()


def test_self_dependency() -> None:
    """测试自我依赖检测."""
    graph = DependencyGraph()

    # 自依赖会导致循环
    graph.add_node("a", ["a"])
    with pytest.raises(CircularDependencyError):
        graph.topological_sort()


def test_update_module_dependencies() -> None:
    """测试更新模块的依赖."""
    graph = DependencyGraph()
    graph.add_node("base", [])
    graph.add_node("module", ["base"])

    # 更新依赖（添加新依赖）
    graph.add_node("base2", [])
    graph.add_node("module", ["base", "base2"])

    deps = graph.get_dependencies("module")
    assert "base" in deps
    assert "base2" in deps


def test_graph_caching() -> None:
    """测试拓扑排序的缓存机制."""
    graph = DependencyGraph()
    graph.add_node("a", [])
    graph.add_node("b", ["a"])

    # 第一次排序
    result1 = graph.topological_sort()

    # 第二次排序（应该使用缓存）
    result2 = graph.topological_sort()

    assert result1 == result2


def test_graph_cache_invalidation() -> None:
    """测试缓存失效."""
    graph = DependencyGraph()
    graph.add_node("a", [])

    # 第一次排序
    result1 = graph.topological_sort()
    assert result1 == ["a"]

    # 添加新模块应该使缓存失效
    graph.add_node("b", ["a"])
    result2 = graph.topological_sort()

    assert len(result2) == 2
    assert result1 != result2


def test_complex_dependency_graph() -> None:
    """测试复杂依赖图."""
    graph = DependencyGraph()

    # 创建复杂的依赖关系
    #       a
    #      / \
    #     b   c
    #    / \ / \
    #   d   e   f
    #    \ / \ /
    #     g   h

    graph.add_node("a", [])
    graph.add_node("b", ["a"])
    graph.add_node("c", ["a"])
    graph.add_node("d", ["b"])
    graph.add_node("e", ["b", "c"])
    graph.add_node("f", ["c"])
    graph.add_node("g", ["d", "e"])
    graph.add_node("h", ["e", "f"])

    result = graph.topological_sort()

    # 验证基本的依赖关系
    assert result.index("a") < result.index("b")
    assert result.index("a") < result.index("c")
    assert result.index("b") < result.index("d")
    assert result.index("b") < result.index("e")
    assert result.index("c") < result.index("e")
    assert result.index("c") < result.index("f")
    assert result.index("d") < result.index("g")
    assert result.index("e") < result.index("g")
    assert result.index("e") < result.index("h")
    assert result.index("f") < result.index("h")


def test_get_dependents() -> None:
    """测试获取依赖某个模块的所有模块."""
    graph = DependencyGraph()
    graph.add_node("base", [])
    graph.add_node("dep1", ["base"])
    graph.add_node("dep2", ["base"])
    graph.add_node("dep3", ["dep1"])

    # DependencyGraph 不提供 get_dependents 方法
    # 我们可以通过拓扑排序和依赖关系来验证
    result = graph.topological_sort()

    # base 应该在 dep1 和 dep2 之前
    assert result.index("base") < result.index("dep1")
    assert result.index("base") < result.index("dep2")
    # dep1 应该在 dep3 之前
    assert result.index("dep1") < result.index("dep3")


def test_isolated_modules() -> None:
    """测试孤立模块（没有依赖也不被依赖）."""
    graph = DependencyGraph()
    graph.add_node("isolated1", [])
    graph.add_node("isolated2", [])
    graph.add_node("isolated3", [])

    result = graph.topological_sort()

    # 所有模块都应该在结果中
    assert len(result) == 3
    assert "isolated1" in result
    assert "isolated2" in result
    assert "isolated3" in result
