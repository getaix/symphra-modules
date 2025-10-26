"""事件系统使用示例."""

from symphra_modules import (
    BaseModule,
    Event,
    EventBus,
    ModuleLoadedEvent,
    ModuleManager,
    ModuleMetadata,
    ModuleStartedEvent,
)


# 定义一个示例模块
class DemoModule(BaseModule):
    """演示模块."""

    @property
    def metadata(self) -> ModuleMetadata:
        """模块元数据."""
        return ModuleMetadata(
            name="demo",
            version="1.0.0",
            description="演示模块",
        )

    def start(self) -> None:
        """启动模块."""
        print(f"模块 {self.metadata.name} 正在启动...")


def on_module_loaded(event: Event) -> None:
    """模块加载事件处理器."""
    print(f"[事件] 模块已加载: {event.module_name}")


def on_module_started(event: Event) -> None:
    """模块启动事件处理器."""
    print(f"[事件] 模块已启动: {event.module_name} at {event.timestamp}")


def on_any_event(event: Event) -> None:
    """通配符事件处理器 - 接收所有事件."""
    print(f"[通配符] 事件类型: {event.event_type}, 模块: {event.module_name}")


def main() -> None:
    """主函数."""
    # 创建事件总线
    event_bus = EventBus()

    # 订阅特定事件
    event_bus.subscribe("module.loaded", on_module_loaded)
    event_bus.subscribe("module.started", on_module_started)

    # 订阅所有事件
    event_bus.subscribe("*", on_any_event)

    # 手动发布事件演示
    print("\n=== 手动发布事件 ===")
    event_bus.publish(ModuleLoadedEvent("test_module"))
    event_bus.publish(ModuleStartedEvent("test_module"))

    # 在实际使用中，事件会由 Registry 或 Manager 自动发布
    print("\n=== 事件系统集成演示 ===")
    manager = ModuleManager()
    manager.registry.register("demo", DemoModule)


if __name__ == "__main__":
    main()
