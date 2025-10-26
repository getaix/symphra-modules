"""模块接口和基类定义."""

import asyncio
import inspect
from abc import ABC, abstractmethod
from typing import Any, Protocol, runtime_checkable

from symphra_modules.config import ModuleMetadata


@runtime_checkable
class ModuleInterface(Protocol):
    """模块接口协议."""

    @property
    def metadata(self) -> ModuleMetadata:
        """获取模块元数据."""
        ...

    def bootstrap(self) -> None:
        """模块引导，注册依赖等操作."""
        ...

    def install(self, config: dict[str, Any] | None = None) -> None:
        """安装模块."""
        ...

    def uninstall(self) -> None:
        """卸载模块."""
        ...

    def configure(self, config: dict[str, Any] | None = None) -> None:
        """配置模块."""
        ...

    def start(self) -> None:
        """启动模块."""
        ...

    def stop(self) -> None:
        """停止模块."""
        ...

    def reload(self) -> None:
        """重载模块."""
        ...

    def get_config(self) -> dict[str, Any]:
        """获取当前配置."""
        ...

    def validate_config(self, config: dict[str, Any] | None = None) -> bool:
        """验证配置."""
        ...


class BaseModule(ABC):
    """模块基类，提供默认实现."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        """初始化模块.

        Args:
            config: 初始配置（可选）
        """
        self._config = config or {}

    # 使用 __slots__ 降低每个模块实例的内存占用
    __slots__ = ("_config",)

    @property
    @abstractmethod
    def metadata(self) -> ModuleMetadata:
        """获取模块元数据 - 子类必须实现."""

    def bootstrap(self) -> None:
        """模块引导，注册依赖等操作.

        默认实现为空，子类可覆盖此方法执行初始化逻辑。
        """
        pass

    def install(self, config: dict[str, Any] | None = None) -> None:
        """安装模块的默认实现.

        Args:
            config: 安装配置（可选）
        """
        if config:
            self.configure(config)

    def uninstall(self) -> None:
        """卸载模块的默认实现.

        默认行为是先停止模块。
        """
        self.stop()

    def configure(self, config: dict[str, Any] | None = None) -> None:
        """配置模块.

        Args:
            config: 配置字典（可选）

        Raises:
            ModuleConfigError: 配置验证失败时抛出
        """
        if config and self.validate_config(config):
            self._config.update(config)
        elif config:
            from symphra_modules.exceptions import ModuleConfigError

            raise ModuleConfigError(
                f"配置验证失败: {self.metadata.name}",
                module_name=self.metadata.name,
            )

    def start(self) -> None:
        """启动模块的默认实现.

        子类应覆盖此方法实现实际的启动逻辑。
        """
        pass

    def stop(self) -> None:
        """停止模块的默认实现.

        子类应覆盖此方法实现实际的停止逻辑。
        """
        pass

    def reload(self) -> None:
        """重载模块的默认实现.

        默认行为是先停止再启动。
        """
        self.stop()
        self.start()

    def get_config(self) -> dict[str, Any]:
        """获取当前配置.

        Returns:
            配置字典的副本
        """
        return self._config.copy() if self._config else {}

    def validate_config(self, config: dict[str, Any] | None = None) -> bool:
        """验证配置 - 默认实现.

        默认总是返回 True，子类应覆盖此方法实现实际的验证逻辑。

        Args:
            config: 待验证的配置（可选）

        Returns:
            验证是否通过
        """
        return True


def is_async_module(module: object) -> bool:
    """检测模块是否实现了异步方法.

    Args:
        module: 要检测的模块实例

    Returns:
        如果模块的核心方法是协程函数则返回 True
    """
    # 检查关键方法是否为协程函数
    key_methods = ["install", "uninstall", "start", "stop", "configure"]
    for method_name in key_methods:
        if hasattr(module, method_name):
            method = getattr(module, method_name)
            if inspect.iscoroutinefunction(method):
                return True
    return False


async def call_module_method(
    module: object,
    method_name: str,
    *args: Any,
    **kwargs: Any,
) -> Any:
    """统一调用模块方法（自动检测同步/异步）.

    Args:
        module: 模块实例
        method_name: 方法名称
        *args: 位置参数
        **kwargs: 关键字参数

    Returns:
        方法返回值

    Raises:
        AttributeError: 方法不存在时抛出
    """
    if not hasattr(module, method_name):
        raise AttributeError(f"模块 {type(module).__name__} 没有方法 {method_name}")

    method = getattr(module, method_name)

    # 如果是协程函数，直接 await
    if inspect.iscoroutinefunction(method):
        return await method(*args, **kwargs)

    # 如果是同步函数，在执行器中运行
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, lambda: method(*args, **kwargs))
