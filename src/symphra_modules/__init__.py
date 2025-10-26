"""Symphra Modules - 高性能 Python 模块管理库.

这是一个轻量级、高性能的 Python 模块管理库,提供动态加载、
生命周期管理、依赖解析和异步支持。

基本用法::

    from symphra_modules import ModuleManager, BaseModule, ModuleMetadata

    class MyModule(BaseModule):
        @property
        def metadata(self) -> ModuleMetadata:
            return ModuleMetadata(name="my_module")

        def start(self) -> None:
            print("模块启动!")

    manager = ModuleManager()
    manager.load_module("my_module")
    manager.start_module("my_module")
"""

# 核心公共 API - 按需导入以提高启动速度
from symphra_modules.abc import BaseModule, ModuleInterface
from symphra_modules.config import ModuleMetadata, ModuleState
from symphra_modules.exceptions import (
    ModuleConfigError,
    ModuleDependencyError,
    ModuleError,
    ModuleLoadError,
    ModuleNotFoundException,
    ModuleStateError,
)
from symphra_modules.manager import ModuleManager

__version__ = "0.1.0"

# 简化的公共 API - 只导出最常用的类
__all__ = [
    # 核心类
    "ModuleManager",  # 主要入口点
    "BaseModule",  # 模块基类
    "ModuleInterface",  # 模块接口
    # 配置
    "ModuleMetadata",  # 模块元数据
    "ModuleState",  # 模块状态
    # 核心异常
    "ModuleError",  # 基础异常
    "ModuleNotFoundException",  # 模块未找到
    "ModuleLoadError",  # 加载错误
    "ModuleConfigError",  # 配置错误
    "ModuleStateError",  # 状态错误
    "ModuleDependencyError",  # 依赖错误
]


# 提供懒加载支持 - 高级功能按需导入
def __getattr__(name: str):
    """懒加载高级功能."""
    # 加载器
    if name == "DirectoryLoader":
        from symphra_modules.loader import DirectoryLoader

        return DirectoryLoader
    if name == "PackageLoader":
        from symphra_modules.loader import PackageLoader

        return PackageLoader
    if name == "ModuleLoader":
        from symphra_modules.loader import ModuleLoader

        return ModuleLoader

    # 注册表和解析器
    if name == "ModuleRegistry":
        from symphra_modules.registry import ModuleRegistry

        return ModuleRegistry
    if name == "DependencyResolver":
        from symphra_modules.resolver import DependencyResolver

        return DependencyResolver
    if name == "DependencyGraph":
        from symphra_modules.resolver import DependencyGraph

        return DependencyGraph

    # 事件系统
    if name == "EventBus":
        from symphra_modules.events import EventBus

        return EventBus
    if name in ("Event", "ModuleLoadedEvent", "ModuleStartedEvent", "ModuleStoppedEvent"):
        from symphra_modules import events

        return getattr(events, name)

    # 工具函数
    if name in ("is_async_module", "call_module_method"):
        from symphra_modules import abc

        return getattr(abc, name)

    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
