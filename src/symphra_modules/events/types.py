"""事件类型定义."""

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from symphra_modules.utils import now


@dataclass
class Event:
    """事件基类."""

    event_type: str  # 事件类型
    module_name: str  # 模块名称
    timestamp: datetime  # 时间戳
    data: dict[str, Any] | None = None  # 附加数据


@dataclass
class ModuleLoadedEvent(Event):
    """模块加载事件."""

    def __init__(self, module_name: str, data: dict[str, Any] | None = None) -> None:
        """初始化加载事件.

        Args:
            module_name: 模块名称
            data: 附加数据（可选）
        """
        super().__init__(
            event_type="module.loaded",
            module_name=module_name,
            timestamp=now(),
            data=data,
        )


@dataclass
class ModuleInstalledEvent(Event):
    """模块安装事件."""

    def __init__(self, module_name: str, data: dict[str, Any] | None = None) -> None:
        """初始化安装事件.

        Args:
            module_name: 模块名称
            data: 附加数据（可选）
        """
        super().__init__(
            event_type="module.installed",
            module_name=module_name,
            timestamp=now(),
            data=data,
        )


@dataclass
class ModuleStartedEvent(Event):
    """模块启动事件."""

    def __init__(self, module_name: str, data: dict[str, Any] | None = None) -> None:
        """初始化启动事件.

        Args:
            module_name: 模块名称
            data: 附加数据（可选）
        """
        super().__init__(
            event_type="module.started",
            module_name=module_name,
            timestamp=now(),
            data=data,
        )


@dataclass
class ModuleStoppedEvent(Event):
    """模块停止事件."""

    def __init__(self, module_name: str, data: dict[str, Any] | None = None) -> None:
        """初始化停止事件.

        Args:
            module_name: 模块名称
            data: 附加数据（可选）
        """
        super().__init__(
            event_type="module.stopped",
            module_name=module_name,
            timestamp=now(),
            data=data,
        )


@dataclass
class ModuleUninstalledEvent(Event):
    """模块卸载事件."""

    def __init__(self, module_name: str, data: dict[str, Any] | None = None) -> None:
        """初始化卸载事件.

        Args:
            module_name: 模块名称
            data: 附加数据（可选）
        """
        super().__init__(
            event_type="module.uninstalled",
            module_name=module_name,
            timestamp=now(),
            data=data,
        )


@dataclass
class ModuleUnregisteredEvent(Event):
    """模块注销事件."""

    def __init__(self, module_name: str, data: dict[str, Any] | None = None) -> None:
        """初始化注销事件.

        Args:
            module_name: 模块名称
            data: 附加数据（可选）
        """
        super().__init__(
            event_type="module.unregistered",
            module_name=module_name,
            timestamp=now(),
            data=data,
        )


@dataclass
class ModuleErrorEvent(Event):
    """模块错误事件."""

    def __init__(
        self,
        module_name: str,
        error: Exception,
        data: dict[str, Any] | None = None,
    ) -> None:
        """初始化错误事件.

        Args:
            module_name: 模块名称
            error: 异常对象
            data: 附加数据（可选）
        """
        error_data = data or {}
        error_data["error"] = str(error)
        error_data["error_type"] = type(error).__name__

        super().__init__(
            event_type="module.error",
            module_name=module_name,
            timestamp=now(),
            data=error_data,
        )
