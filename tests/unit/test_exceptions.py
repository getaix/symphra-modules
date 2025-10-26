"""异常模块测试."""

import pytest

from symphra_modules.exceptions import (
    ConfigValidationError,
    EventError,
    ModuleConfigError,
    ModuleDependencyError,
    ModuleError,
    ModuleLoadError,
    ModuleNotFoundException,
    ModuleStateError,
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
