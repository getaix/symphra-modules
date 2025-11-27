"""依赖解析器增强功能测试."""

import pytest
from symphra_modules.config import ModuleMetadata
from symphra_modules.exceptions import ModuleDependencyError
from symphra_modules.resolver import DependencyResolver


def test_validate_no_cycles_success() -> None:
    """测试无循环时 validate_no_cycles 返回 True."""
    resolver = DependencyResolver()
    resolver.add_module(ModuleMetadata(name="a"))
    resolver.add_module(ModuleMetadata(name="b", dependencies=["a"]))
    resolver.add_module(ModuleMetadata(name="c", dependencies=["a", "b"]))

    # 应该成功返回 True
    result = resolver.validate_no_cycles()
    assert result is True


def test_validate_no_cycles_failure() -> None:
    """测试有循环时 validate_no_cycles 抛出异常."""
    resolver = DependencyResolver()
    resolver.add_module(ModuleMetadata(name="a", dependencies=["b"]))
    resolver.add_module(ModuleMetadata(name="b", dependencies=["c"]))
    resolver.add_module(ModuleMetadata(name="c", dependencies=["a"]))

    # 应该抛出循环依赖异常
    with pytest.raises(ModuleDependencyError) as exc_info:
        resolver.validate_no_cycles()
    assert "循环依赖" in str(exc_info.value)


def test_get_dependency_chain_simple() -> None:
    """测试简单依赖链的获取."""
    resolver = DependencyResolver()
    resolver.add_module(ModuleMetadata(name="a"))
    resolver.add_module(ModuleMetadata(name="b", dependencies=["a"]))
    resolver.add_module(ModuleMetadata(name="c", dependencies=["b"]))

    chain = resolver.get_dependency_chain("c")

    # 应该返回完整的依赖链
    assert chain == ["a", "b", "c"]


def test_get_dependency_chain_complex() -> None:
    """测试复杂依赖链的获取."""
    resolver = DependencyResolver()
    resolver.add_module(ModuleMetadata(name="core"))
    resolver.add_module(ModuleMetadata(name="db", dependencies=["core"]))
    resolver.add_module(ModuleMetadata(name="cache", dependencies=["core"]))
    resolver.add_module(ModuleMetadata(name="api", dependencies=["db", "cache"]))

    chain = resolver.get_dependency_chain("api")

    # core 必须在最前面
    assert chain[0] == "core"
    # api 必须在最后面
    assert chain[-1] == "api"
    # db 和 cache 必须在 api 之前
    assert "db" in chain and "cache" in chain
    assert chain.index("db") < chain.index("api")
    assert chain.index("cache") < chain.index("api")


def test_get_dependency_chain_no_dependencies() -> None:
    """测试没有依赖的模块."""
    resolver = DependencyResolver()
    resolver.add_module(ModuleMetadata(name="standalone"))

    chain = resolver.get_dependency_chain("standalone")

    # 应该只包含模块自己
    assert chain == ["standalone"]


def test_get_dependency_chain_nonexistent() -> None:
    """测试获取不存在模块的依赖链."""
    resolver = DependencyResolver()
    resolver.add_module(ModuleMetadata(name="a"))

    with pytest.raises(ModuleDependencyError) as exc_info:
        resolver.get_dependency_chain("nonexistent")
    assert "模块不存在" in str(exc_info.value)


def test_check_runtime_dependency_declared() -> None:
    """测试已声明的依赖通过检查."""
    resolver = DependencyResolver()
    resolver.add_module(ModuleMetadata(name="a"))
    resolver.add_module(ModuleMetadata(name="b", dependencies=["a"]))

    # 已声明的依赖应该返回 True
    result = resolver.check_runtime_dependency("b", "a")
    assert result is True


def test_check_runtime_dependency_undeclared() -> None:
    """测试未声明的依赖抛出异常."""
    resolver = DependencyResolver()
    resolver.add_module(ModuleMetadata(name="a"))
    resolver.add_module(ModuleMetadata(name="b"))  # b 没有声明依赖 a

    # 未声明的依赖应该抛出异常
    with pytest.raises(ModuleDependencyError) as exc_info:
        resolver.check_runtime_dependency("b", "a")
    assert "未声明的依赖" in str(exc_info.value)


def test_check_runtime_dependency_circular() -> None:
    """测试会导致循环的依赖抛出异常."""
    resolver = DependencyResolver()
    resolver.add_module(ModuleMetadata(name="a", dependencies=["b"]))
    resolver.add_module(ModuleMetadata(name="b", dependencies=["c"]))
    resolver.add_module(ModuleMetadata(name="c"))

    # 尝试让 c 依赖 a，这会形成循环
    # 但是我们需要先在图中声明这个依赖，所以这个测试略有不同
    # 我们测试反向的情况：a -> b -> c，然后检查 c -> a
    with pytest.raises(ModuleDependencyError) as exc_info:
        # c 声明依赖 a 会形成循环 (因为 a -> b -> c)
        resolver.add_module(ModuleMetadata(name="c", dependencies=["a"]))
        resolver.check_runtime_dependency("c", "a")
    assert "循环" in str(exc_info.value)


def test_check_runtime_dependency_from_module_not_found() -> None:
    """测试源模块不存在时抛出异常."""
    resolver = DependencyResolver()
    resolver.add_module(ModuleMetadata(name="a"))

    with pytest.raises(ModuleDependencyError) as exc_info:
        resolver.check_runtime_dependency("nonexistent", "a")
    assert "模块不存在" in str(exc_info.value)


def test_check_runtime_dependency_to_module_not_found() -> None:
    """测试目标模块不存在时抛出异常."""
    resolver = DependencyResolver()
    resolver.add_module(ModuleMetadata(name="a"))

    with pytest.raises(ModuleDependencyError) as exc_info:
        resolver.check_runtime_dependency("a", "nonexistent")
    assert "模块不存在" in str(exc_info.value)


def test_check_runtime_dependency_transitive_circular() -> None:
    """测试传递性循环依赖检测."""
    resolver = DependencyResolver()
    resolver.add_module(ModuleMetadata(name="a", dependencies=["b"]))
    resolver.add_module(ModuleMetadata(name="b", dependencies=["c"]))
    resolver.add_module(ModuleMetadata(name="c", dependencies=["d"]))
    resolver.add_module(ModuleMetadata(name="d"))

    # d 依赖 a 会形成循环: a -> b -> c -> d -> a
    # 首先让 d 声明依赖 a
    resolver.graph._graph["d"].add("a")

    with pytest.raises(ModuleDependencyError) as exc_info:
        resolver.check_runtime_dependency("d", "a")
    assert "循环" in str(exc_info.value)
