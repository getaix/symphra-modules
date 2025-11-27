"""模块基类定义.

这个模块定义了所有模块必须继承的基类。
"""

from __future__ import annotations

import inspect
from abc import ABC
from datetime import datetime
from typing import Any, ClassVar

from .state import ModuleState


class Module(ABC):
    """模块基类 - 简洁优雅的设计.

    所有模块必须继承此类。子类只需定义：
    1. name: 模块名称（必须）
    2. version: 模块版本（可选，默认 "0.1.0"）
    3. dependencies: 依赖列表（可选，默认 []）
    4. start(): 启动逻辑（可选）
    5. stop(): 停止逻辑（可选）

    Example:
        >>> class DatabaseModule(Module):
        ...     name = "database"
        ...     version = "1.0.0"
        ...     dependencies = []
        ...
        ...     def start(self) -> None:
        ...         print("数据库已连接")
    """

    # 类变量 - 子类必须定义 name，其他可选
    name: ClassVar[str]
    version: ClassVar[str] = "0.1.0"
    dependencies: ClassVar[list[str]] = []

    def __init__(self) -> None:
        """初始化模块实例."""
        self._state = ModuleState.LOADED
        self._loaded_at = datetime.now()

    def bootstrap(self) -> None:
        """Bootstrap 模块 - 子类可覆盖.

        在此方法中实现模块的初始化准备工作，但不启动服务。
        例如：加载配置、验证依赖、准备资源等。
        """
        pass

    def start(self) -> None:
        """启动模块 - 子类可覆盖.

        在此方法中实现模块的初始化逻辑。
        """
        pass

    def stop(self) -> None:
        """停止模块 - 子类可覆盖.

        在此方法中实现模块的清理逻辑。
        """
        pass

    async def start_async(self) -> None:
        """异步启动模块 - 子类可覆盖.

        在此方法中实现模块的异步初始化逻辑。
        默认实现调用同步方法。
        """
        self.start()

    async def stop_async(self) -> None:
        """异步停止模块 - 子类可覆盖.

        在此方法中实现模块的异步清理逻辑。
        默认实现调用同步方法。
        """
        self.stop()

    @property
    def state(self) -> ModuleState:
        """获取模块状态."""
        return self._state

    @property
    def loaded_at(self) -> datetime:
        """获取模块加载时间."""
        return self._loaded_at

    def __repr__(self) -> str:
        """返回模块的字符串表示."""
        return f"<{self.__class__.__name__}(name={self.name}, state={self.state.value})>"


def is_async_module(module: Module) -> bool:
    """检查模块是否支持异步方法.

    判断标准：
    1. 模块有 start_async 和 stop_async 方法
    2. 这些方法是协程函数（使用 async def 定义）
    3. 这些方法不是基类的默认实现

    Args:
        module: 模块实例

    Returns:
        如果是真正的异步模块返回 True，否则返回 False
    """
    # 检查方法是否存在
    if not (hasattr(module, "start_async") and hasattr(module, "stop_async")):
        return False

    start_async_method = module.start_async
    stop_async_method = module.stop_async

    # 检查方法是否为协程函数
    if not (
        inspect.iscoroutinefunction(start_async_method)
        and inspect.iscoroutinefunction(stop_async_method)
    ):
        return False

    # 简单检查：如果方法的源码中包含对同步方法的调用，则认为是默认实现
    try:
        start_async_source = inspect.getsource(start_async_method)
        stop_async_source = inspect.getsource(stop_async_method)

        # 如果异步方法中调用了同步方法，则认为是默认实现
        is_default_start = "self.start()" in start_async_source
        is_default_stop = "self.stop()" in stop_async_source

        # 如果两个都是默认实现，则不是真正的异步模块
        return not (is_default_start and is_default_stop)
    except Exception:
        # 如果无法获取源码，则假设是真正的异步实现
        return True


async def call_module_method(module: Module, method_name: str, *args: Any, **kwargs: Any) -> Any:
    """调用模块方法，自动处理同步/异步.

    此函数会自动检测方法是同步还是异步，并使用正确的方式调用。

    Args:
        module: 模块实例
        method_name: 方法名称
        *args: 位置参数
        **kwargs: 关键字参数

    Returns:
        方法的返回值
    """
    method = getattr(module, method_name)
    if inspect.iscoroutinefunction(method):
        return await method(*args, **kwargs)
    else:
        return method(*args, **kwargs)
