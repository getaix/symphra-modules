"""ABC模块测试."""

import asyncio

import pytest

from symphra_modules.abc import BaseModule, ModuleInterface, call_module_method, is_async_module
from symphra_modules.config import ModuleMetadata
from symphra_modules.exceptions import ModuleConfigError


class TestModule(BaseModule):
    """测试模块."""

    @property
    def metadata(self) -> ModuleMetadata:
        """模块元数据."""
        return ModuleMetadata(name="test_module", version="1.0.0")


class AsyncTestModule(BaseModule):
    """异步测试模块."""

    @property
    def metadata(self) -> ModuleMetadata:
        """模块元数据."""
        return ModuleMetadata(name="async_test_module")

    async def start(self) -> None:
        """异步启动."""
        await asyncio.sleep(0.001)

    async def stop(self) -> None:
        """异步停止."""
        await asyncio.sleep(0.001)


def test_base_module_init() -> None:
    """测试基类初始化."""
    module = TestModule()
    assert module.get_config() == {}

    module_with_config = TestModule({"key": "value"})
    assert module_with_config.get_config() == {"key": "value"}


def test_base_module_metadata() -> None:
    """测试模块元数据."""
    module = TestModule()
    assert module.metadata.name == "test_module"
    assert module.metadata.version == "1.0.0"


def test_base_module_bootstrap() -> None:
    """测试bootstrap方法."""
    module = TestModule()
    # bootstrap默认为空实现，不应抛出异常
    module.bootstrap()


def test_base_module_install() -> None:
    """测试install方法."""
    module = TestModule()
    module.install({"key": "value"})
    assert module.get_config() == {"key": "value"}


def test_base_module_uninstall() -> None:
    """测试uninstall方法."""
    module = TestModule()
    # uninstall默认调用stop，不应抛出异常
    module.uninstall()


def test_base_module_configure() -> None:
    """测试configure方法."""
    module = TestModule()
    module.configure({"key": "value"})
    assert module.get_config() == {"key": "value"}


def test_base_module_configure_validation_failure() -> None:
    """测试配置验证失败."""

    class StrictModule(BaseModule):
        @property
        def metadata(self) -> ModuleMetadata:
            return ModuleMetadata(name="strict")

        def validate_config(self, config: dict | None = None) -> bool:
            return False

    module = StrictModule()
    with pytest.raises(ModuleConfigError) as exc_info:
        module.configure({"key": "value"})
    assert "配置验证失败" in str(exc_info.value)


def test_base_module_start_stop() -> None:
    """测试start和stop方法."""
    module = TestModule()
    # 默认实现为空，不应抛出异常
    module.start()
    module.stop()


def test_base_module_reload() -> None:
    """测试reload方法."""
    module = TestModule()
    # reload默认调用stop和start
    module.reload()


def test_base_module_get_config() -> None:
    """测试获取配置."""
    module = TestModule({"key": "value"})
    config = module.get_config()
    assert config == {"key": "value"}
    # 应返回副本
    config["new_key"] = "new_value"
    assert module.get_config() == {"key": "value"}


def test_base_module_validate_config() -> None:
    """测试配置验证."""
    module = TestModule()
    # 默认总是返回True
    assert module.validate_config({}) is True
    assert module.validate_config({"key": "value"}) is True


def test_is_async_module_sync() -> None:
    """测试检测同步模块."""
    module = TestModule()
    assert is_async_module(module) is False


def test_is_async_module_async() -> None:
    """测试检测异步模块."""
    module = AsyncTestModule()
    assert is_async_module(module) is True


@pytest.mark.asyncio
async def test_call_module_method_sync() -> None:
    """测试调用同步方法."""
    module = TestModule()
    # 调用同步方法
    await call_module_method(module, "start")
    await call_module_method(module, "stop")


@pytest.mark.asyncio
async def test_call_module_method_async() -> None:
    """测试调用异步方法."""
    module = AsyncTestModule()
    # 调用异步方法
    await call_module_method(module, "start")
    await call_module_method(module, "stop")


@pytest.mark.asyncio
async def test_call_module_method_not_exists() -> None:
    """测试调用不存在的方法."""
    module = TestModule()
    with pytest.raises(AttributeError) as exc_info:
        await call_module_method(module, "non_existent_method")
    assert "non_existent_method" in str(exc_info.value)


def test_module_interface_protocol() -> None:
    """测试ModuleInterface协议."""
    module = TestModule()
    # 检查是否符合协议
    assert isinstance(module, ModuleInterface)
    assert hasattr(module, "metadata")
    assert hasattr(module, "bootstrap")
    assert hasattr(module, "install")
    assert hasattr(module, "start")
    assert hasattr(module, "stop")
