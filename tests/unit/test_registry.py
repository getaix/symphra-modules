"""注册表模块测试."""

import pytest
from symphra_modules.abc import BaseModule
from symphra_modules.config import ModuleMetadata, ModuleState
from symphra_modules.exceptions import ModuleNotFoundException, ModuleStateError
from symphra_modules.registry import ModuleRegistry


class DemoModule(BaseModule):
    """演示模块."""

    def __init__(self, config: dict | None = None) -> None:
        super().__init__(config)
        self.started = False
        self.stopped = False

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(name="demo", version="1.0.0")

    def start(self) -> None:
        self.started = True

    def stop(self) -> None:
        self.stopped = True


def test_registry_register() -> None:
    """测试注册模块."""
    registry = ModuleRegistry()
    module = registry.register("demo", DemoModule)

    assert registry.is_loaded("demo")
    assert isinstance(module, DemoModule)
    info = registry.get_info("demo")
    assert info is not None
    assert info.state == ModuleState.LOADED


def test_registry_register_duplicate() -> None:
    """测试重复注册."""
    registry = ModuleRegistry()
    registry.register("demo", DemoModule)

    with pytest.raises(ModuleStateError):
        registry.register("demo", DemoModule)


def test_registry_unregister() -> None:
    """测试注销模块."""
    registry = ModuleRegistry()
    registry.register("demo", DemoModule)
    registry.unregister("demo")

    assert not registry.is_loaded("demo")


def test_registry_install() -> None:
    """测试安装模块."""
    registry = ModuleRegistry()
    registry.register("demo", DemoModule)
    registry.install("demo", {"key": "value"})

    info = registry.get_info("demo")
    assert info is not None
    assert info.state == ModuleState.INSTALLED
    assert info.config == {"key": "value"}


def test_registry_install_wrong_state() -> None:
    """测试错误状态下安装."""
    registry = ModuleRegistry()
    registry.register("demo", DemoModule)
    registry.install("demo")

    with pytest.raises(ModuleStateError):
        registry.install("demo")


def test_registry_uninstall() -> None:
    """测试卸载模块."""
    registry = ModuleRegistry()
    registry.register("demo", DemoModule)
    registry.install("demo")
    registry.uninstall("demo")

    info = registry.get_info("demo")
    assert info is not None
    assert info.state == ModuleState.LOADED


def test_registry_start() -> None:
    """测试启动模块."""
    registry = ModuleRegistry()
    registry.register("demo", DemoModule)
    registry.install("demo")
    registry.start("demo")

    info = registry.get_info("demo")
    assert info is not None
    assert info.state == ModuleState.STARTED

    module = registry.get("demo")
    assert module is not None
    assert isinstance(module, DemoModule)
    assert module.started is True


def test_registry_stop() -> None:
    """测试停止模块."""
    registry = ModuleRegistry()
    registry.register("demo", DemoModule)
    registry.install("demo")
    registry.start("demo")
    registry.stop("demo")

    info = registry.get_info("demo")
    assert info is not None
    assert info.state == ModuleState.STOPPED


def test_registry_stop_not_started() -> None:
    """测试停止未启动的模块."""
    registry = ModuleRegistry()
    registry.register("demo", DemoModule)
    registry.install("demo")
    # 不应抛出异常
    registry.stop("demo")


def test_registry_reload() -> None:
    """测试重载模块."""
    registry = ModuleRegistry()
    registry.register("demo", DemoModule)
    registry.install("demo")
    registry.start("demo")

    module = registry.get("demo")
    assert module is not None
    assert isinstance(module, DemoModule)
    assert module.started is True

    registry.reload("demo")
    # reload调用stop+start
    assert module.stopped is True
    assert module.started is True


def test_registry_configure() -> None:
    """测试配置模块."""
    registry = ModuleRegistry()
    registry.register("demo", DemoModule)
    config = {"test": "value"}
    registry.configure("demo", config)

    module = registry.get("demo")
    assert module is not None
    assert module.get_config() == config


def test_registry_get_nonexistent() -> None:
    """测试获取不存在的模块."""
    registry = ModuleRegistry()
    assert registry.get("nonexistent") is None


def test_registry_get_info_nonexistent() -> None:
    """测试获取不存在模块的信息."""
    registry = ModuleRegistry()
    assert registry.get_info("nonexistent") is None


def test_registry_list_modules() -> None:
    """测试列出所有模块."""
    registry = ModuleRegistry()
    registry.register("demo1", DemoModule)
    registry.register("demo2", DemoModule)

    modules = registry.list_modules()
    assert set(modules) == {"demo1", "demo2"}


def test_registry_list_modules_by_state() -> None:
    """测试按状态列出模块."""
    registry = ModuleRegistry()
    registry.register("demo1", DemoModule)
    registry.register("demo2", DemoModule)
    registry.install("demo1")

    loaded = registry.list_modules_by_state(ModuleState.LOADED)
    installed = registry.list_modules_by_state(ModuleState.INSTALLED)

    assert "demo2" in loaded
    assert "demo1" in installed


def test_registry_get_module_states() -> None:
    """测试获取所有模块状态."""
    registry = ModuleRegistry()
    registry.register("demo1", DemoModule)
    registry.register("demo2", DemoModule)
    registry.install("demo1")

    states = registry.get_module_states()
    assert states["demo1"] == ModuleState.INSTALLED
    assert states["demo2"] == ModuleState.LOADED


def test_registry_is_installed() -> None:
    """测试检查模块是否已安装."""
    registry = ModuleRegistry()
    registry.register("demo", DemoModule)
    assert not registry.is_installed("demo")

    registry.install("demo")
    assert registry.is_installed("demo")

    registry.start("demo")
    assert registry.is_installed("demo")


def test_registry_is_started() -> None:
    """测试检查模块是否已启动."""
    registry = ModuleRegistry()
    registry.register("demo", DemoModule)
    registry.install("demo")
    assert not registry.is_started("demo")

    registry.start("demo")
    assert registry.is_started("demo")


def test_registry_module_not_found() -> None:
    """测试模块未找到异常."""
    registry = ModuleRegistry()

    with pytest.raises(ModuleNotFoundException):
        registry.install("nonexistent")

    with pytest.raises(ModuleNotFoundException):
        registry.unregister("nonexistent")
