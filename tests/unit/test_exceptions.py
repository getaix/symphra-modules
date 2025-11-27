"""异常模块测试."""

from symphra_modules.exceptions import (
    CircularDependencyError,
    ConfigValidationError,
    EventError,
    ModuleConfigError,
    ModuleDependencyError,
    ModuleError,
    ModuleLoadError,
    ModuleNotFoundException,
    ModuleStateError,
    ServiceAlreadyExistsError,
    ServiceNotFoundException,
    UndeclaredDependencyError,
)


def test_module_error() -> None:
    """测试基础异常."""
    error = ModuleError("测试错误", module_name="test_module")
    assert str(error) == "测试错误"
    assert error.module_name == "test_module"


def test_module_error_without_module_name() -> None:
    """测试不带模块名的异常."""
    error = ModuleError("测试错误")
    assert error.module_name is None


def test_module_not_found_exception() -> None:
    """测试模块未找到异常."""
    error = ModuleNotFoundException("模块未找到", module_name="missing")
    assert str(error) == "模块未找到"
    assert error.module_name == "missing"
    assert isinstance(error, ModuleError)


def test_module_load_error() -> None:
    """测试模块加载错误."""
    error = ModuleLoadError("加载失败", module_name="test")
    assert str(error) == "加载失败"
    assert isinstance(error, ModuleError)


def test_module_config_error() -> None:
    """测试模块配置错误."""
    error = ModuleConfigError("配置错误", module_name="test")
    assert str(error) == "配置错误"
    assert isinstance(error, ModuleError)


def test_config_validation_error() -> None:
    """测试配置验证错误."""
    error = ConfigValidationError("验证失败", module_name="test")
    assert str(error) == "验证失败"
    assert isinstance(error, ModuleConfigError)
    assert isinstance(error, ModuleError)


def test_module_state_error() -> None:
    """测试模块状态错误."""
    error = ModuleStateError(
        "状态错误",
        module_name="test",
        current_state="loaded",
        expected_states=["installed", "started"],
    )
    assert str(error) == "状态错误"
    assert error.module_name == "test"
    assert error.current_state == "loaded"
    assert error.expected_states == ["installed", "started"]
    assert isinstance(error, ModuleError)


def test_module_state_error_defaults() -> None:
    """测试模块状态错误默认值."""
    error = ModuleStateError("状态错误")
    assert error.expected_states == []
    assert error.current_state is None


def test_module_dependency_error() -> None:
    """测试模块依赖错误."""
    error = ModuleDependencyError(
        "依赖错误",
        module_name="test",
        missing_dependencies=["dep1", "dep2"],
        circular_dependencies=["module_a", "module_b"],
    )
    assert str(error) == "依赖错误"
    assert error.module_name == "test"
    assert error.missing_dependencies == ["dep1", "dep2"]
    assert error.circular_dependencies == ["module_a", "module_b"]
    assert isinstance(error, ModuleError)


def test_module_dependency_error_defaults() -> None:
    """测试模块依赖错误默认值."""
    error = ModuleDependencyError("依赖错误")
    assert error.missing_dependencies == []
    assert error.circular_dependencies == []


def test_event_error() -> None:
    """测试事件错误."""
    error = EventError("事件错误", module_name="test")
    assert str(error) == "事件错误"
    assert isinstance(error, ModuleError)


def test_circular_dependency_error_basic() -> None:
    """测试基本的循环依赖异常."""
    error = CircularDependencyError(
        "检测到循环依赖",
        cycle_path=["A", "B", "C", "A"],
    )

    assert "循环依赖" in str(error)
    assert error.cycle_path == ["A", "B", "C", "A"]


def test_circular_dependency_error_format_cycle() -> None:
    """测试循环路径格式化."""
    error = CircularDependencyError(
        "检测到循环依赖",
        cycle_path=["module_a", "module_b", "module_c", "module_a"],
    )

    formatted = error.format_cycle()
    assert formatted == "module_a -> module_b -> module_c -> module_a"


def test_circular_dependency_error_empty_cycle() -> None:
    """测试空循环路径."""
    error = CircularDependencyError("检测到循环依赖")

    assert error.cycle_path == []
    assert error.format_cycle() == ""


def test_circular_dependency_error_with_module_name() -> None:
    """测试带模块名的循环依赖异常."""
    error = CircularDependencyError(
        "检测到循环依赖",
        cycle_path=["A", "B", "A"],
        module_name="A",
    )

    assert error.module_name == "A"
    assert error.cycle_path == ["A", "B", "A"]


def test_circular_dependency_error_kwargs_propagation() -> None:
    """测试 kwargs 参数传递."""
    error = CircularDependencyError(
        "检测到循环依赖",
        cycle_path=["A", "B", "A"],
        module_name="A",
    )

    # cycle_path 应该被自动设置为 circular_dependencies
    assert error.circular_dependencies == ["A", "B", "A"]


def test_undeclared_dependency_error_basic() -> None:
    """测试基本的未声明依赖异常."""
    error = UndeclaredDependencyError(
        "未声明的依赖",
        from_module="module_a",
        to_module="module_b",
    )

    assert "未声明" in str(error)
    assert error.from_module == "module_a"
    assert error.to_module == "module_b"
    assert error.module_name == "module_a"  # 应该自动设置为 from_module


def test_undeclared_dependency_error_with_module_name() -> None:
    """测试带自定义模块名的未声明依赖异常."""
    error = UndeclaredDependencyError(
        "未声明的依赖",
        from_module="module_a",
        to_module="module_b",
        module_name="custom_module",
    )

    assert error.from_module == "module_a"
    assert error.to_module == "module_b"
    assert error.module_name == "custom_module"


def test_service_not_found_error_basic() -> None:
    """测试基本的服务未找到异常."""
    error = ServiceNotFoundException("服务未找到")

    assert "服务未找到" in str(error)
    assert error.service_name is None


def test_service_not_found_error_with_name() -> None:
    """测试带服务名的服务未找到异常."""
    error = ServiceNotFoundException(
        "服务未找到: my_service",
        service_name="my_service",
    )

    assert "my_service" in str(error)
    assert error.service_name == "my_service"


def test_service_already_exists_error_basic() -> None:
    """测试基本的服务已存在异常."""
    error = ServiceAlreadyExistsError("服务已存在")

    assert "服务已存在" in str(error)
    assert error.service_name is None


def test_service_already_exists_error_with_name() -> None:
    """测试带服务名的服务已存在异常."""
    error = ServiceAlreadyExistsError(
        "服务已存在: my_service",
        service_name="my_service",
    )

    assert "my_service" in str(error)
    assert error.service_name == "my_service"
