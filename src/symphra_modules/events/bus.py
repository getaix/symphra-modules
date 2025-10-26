"""事件总线实现."""

from collections import defaultdict
from collections.abc import Callable

from symphra_modules.events.types import Event
from symphra_modules.exceptions import EventError
from symphra_modules.utils import get_logger

logger = get_logger()

# 事件处理器类型定义
EventHandler = Callable[[Event], None]


class EventBus:
    """事件总线 - 简单的发布/订阅实现."""

    def __init__(self) -> None:
        """初始化事件总线."""
        self._handlers: dict[str, list[EventHandler]] = defaultdict(list)
        self._wildcard_handlers: list[EventHandler] = []

    def subscribe(self, event_type: str, handler: EventHandler) -> None:
        """订阅事件.

        Args:
            event_type: 事件类型，使用 "*" 订阅所有事件
            handler: 事件处理器函数

        Raises:
            EventError: 处理器不可调用时抛出
        """
        if not callable(handler):
            raise EventError("事件处理器必须是可调用对象")

        if event_type == "*":
            self._wildcard_handlers.append(handler)
        else:
            self._handlers[event_type].append(handler)

        logger.debug(f"订阅事件: {event_type}")

    def unsubscribe(self, event_type: str, handler: EventHandler) -> None:
        """取消订阅事件.

        Args:
            event_type: 事件类型
            handler: 事件处理器函数
        """
        if event_type == "*":
            if handler in self._wildcard_handlers:
                self._wildcard_handlers.remove(handler)
        else:
            if handler in self._handlers[event_type]:
                self._handlers[event_type].remove(handler)

        logger.debug(f"取消订阅事件: {event_type}")

    def publish(self, event: Event) -> None:
        """发布事件.

        Args:
            event: 事件对象
        """
        logger.debug(f"发布事件: {event.event_type} - {event.module_name}")

        # 调用通配符处理器
        for handler in self._wildcard_handlers:
            self._call_handler(handler, event)

        # 调用特定类型的处理器
        if event.event_type in self._handlers:
            for handler in self._handlers[event.event_type]:
                self._call_handler(handler, event)

    def _call_handler(self, handler: EventHandler, event: Event) -> None:
        """调用事件处理器.

        Args:
            handler: 事件处理器
            event: 事件对象
        """
        try:
            handler(event)
        except Exception as e:
            logger.error(f"事件处理器执行失败: {handler.__name__} - {e}")

    def clear(self) -> None:
        """清除所有订阅."""
        self._handlers.clear()
        self._wildcard_handlers.clear()
        logger.debug("已清除所有事件订阅")

    def get_subscribers(self, event_type: str) -> list[EventHandler]:
        """获取指定事件类型的订阅者.

        Args:
            event_type: 事件类型

        Returns:
            订阅者列表
        """
        if event_type == "*":
            return self._wildcard_handlers.copy()
        return self._handlers.get(event_type, []).copy()
