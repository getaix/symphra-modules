"""事件系统测试."""

import pytest

from symphra_modules.events import (
    Event,
    EventBus,
    ModuleErrorEvent,
    ModuleInstalledEvent,
    ModuleLoadedEvent,
    ModuleStartedEvent,
    ModuleStoppedEvent,
    ModuleUninstalledEvent,
    ModuleUnregisteredEvent,
)
from symphra_modules.exceptions import EventError


def test_module_loaded_event() -> None:
    """测试模块加载事件."""
    event = ModuleLoadedEvent("test_module")
    assert event.event_type == "module.loaded"
    assert event.module_name == "test_module"
    assert event.data is None
    assert event.timestamp is not None


def test_module_loaded_event_with_data() -> None:
    """测试带数据的模块加载事件."""
    data = {"key": "value"}
    event = ModuleLoadedEvent("test_module", data=data)
    assert event.data == data


def test_module_installed_event() -> None:
    """测试模块安装事件."""
    event = ModuleInstalledEvent("test_module")
    assert event.event_type == "module.installed"
    assert event.module_name == "test_module"


def test_module_started_event() -> None:
    """测试模块启动事件."""
    event = ModuleStartedEvent("test_module")
    assert event.event_type == "module.started"
    assert event.module_name == "test_module"


def test_module_stopped_event() -> None:
    """测试模块停止事件."""
    event = ModuleStoppedEvent("test_module")
    assert event.event_type == "module.stopped"
    assert event.module_name == "test_module"


def test_module_uninstalled_event() -> None:
    """测试模块卸载事件."""
    event = ModuleUninstalledEvent("test_module")
    assert event.event_type == "module.uninstalled"
    assert event.module_name == "test_module"


def test_module_unregistered_event() -> None:
    """测试模块注销事件."""
    event = ModuleUnregisteredEvent("test_module")
    assert event.event_type == "module.unregistered"
    assert event.module_name == "test_module"


def test_module_error_event() -> None:
    """测试模块错误事件."""
    error = ValueError("测试错误")
    event = ModuleErrorEvent("test_module", error)
    assert event.event_type == "module.error"
    assert event.module_name == "test_module"
    assert event.data is not None
    assert event.data["error"] == "测试错误"
    assert event.data["error_type"] == "ValueError"


def test_event_bus_subscribe() -> None:
    """测试事件订阅."""
    bus = EventBus()
    called = []

    def handler(event: Event) -> None:
        called.append(event)

    bus.subscribe("module.loaded", handler)
    assert len(bus.get_subscribers("module.loaded")) == 1


def test_event_bus_subscribe_invalid_handler() -> None:
    """测试订阅无效处理器."""
    bus = EventBus()
    with pytest.raises(EventError) as exc_info:
        bus.subscribe("module.loaded", "not_callable")  # type: ignore[arg-type]
    assert "可调用对象" in str(exc_info.value)


def test_event_bus_publish() -> None:
    """测试事件发布."""
    bus = EventBus()
    called = []

    def handler(event: Event) -> None:
        called.append(event)

    bus.subscribe("module.loaded", handler)
    event = ModuleLoadedEvent("test_module")
    bus.publish(event)

    assert len(called) == 1
    assert called[0] == event


def test_event_bus_wildcard_subscribe() -> None:
    """测试通配符订阅."""
    bus = EventBus()
    called = []

    def handler(event: Event) -> None:
        called.append(event.event_type)

    bus.subscribe("*", handler)

    bus.publish(ModuleLoadedEvent("test"))
    bus.publish(ModuleStartedEvent("test"))
    bus.publish(ModuleStoppedEvent("test"))

    assert len(called) == 3
    assert "module.loaded" in called
    assert "module.started" in called
    assert "module.stopped" in called


def test_event_bus_multiple_handlers() -> None:
    """测试多个处理器."""
    bus = EventBus()
    calls = {"handler1": 0, "handler2": 0}

    def handler1(event: Event) -> None:
        calls["handler1"] += 1

    def handler2(event: Event) -> None:
        calls["handler2"] += 1

    bus.subscribe("module.loaded", handler1)
    bus.subscribe("module.loaded", handler2)

    bus.publish(ModuleLoadedEvent("test"))

    assert calls["handler1"] == 1
    assert calls["handler2"] == 1


def test_event_bus_unsubscribe() -> None:
    """测试取消订阅."""
    bus = EventBus()
    called = []

    def handler(event: Event) -> None:
        called.append(event)

    bus.subscribe("module.loaded", handler)
    bus.unsubscribe("module.loaded", handler)

    bus.publish(ModuleLoadedEvent("test"))
    assert len(called) == 0


def test_event_bus_clear() -> None:
    """测试清除所有订阅."""
    bus = EventBus()

    def handler(event: Event) -> None:
        pass

    bus.subscribe("module.loaded", handler)
    bus.subscribe("*", handler)

    bus.clear()

    assert len(bus.get_subscribers("module.loaded")) == 0
    assert len(bus.get_subscribers("*")) == 0


def test_event_bus_handler_exception() -> None:
    """测试处理器异常不影响其他处理器."""
    bus = EventBus()
    calls = {"handler1": 0, "handler2": 0}

    def handler1(event: Event) -> None:
        calls["handler1"] += 1
        raise ValueError("处理器1错误")

    def handler2(event: Event) -> None:
        calls["handler2"] += 1

    bus.subscribe("module.loaded", handler1)
    bus.subscribe("module.loaded", handler2)

    bus.publish(ModuleLoadedEvent("test"))

    # 即使handler1抛出异常，handler2也应该被调用
    assert calls["handler1"] == 1
    assert calls["handler2"] == 1
