"""Symphra Modules - 优雅的 Python 模块化框架.

这是一个高性能、高质量的 Python 模块管理库，支持：
- 声明式依赖管理
- 自动循环依赖检测 (Kahn 算法)
- 模块生命周期管理
- 异步操作支持
- 性能监控
- 线程安全和协程安全

Example:
    >>> from symphra_modules import Module, ModuleManager
    >>>
    >>> class DatabaseModule(Module):
    ...     name = "database"
    ...
    ...     def start(self) -> None:
    ...         print("数据库已连接")
    >>>
    >>> manager = ModuleManager("./modules")
    >>> db = manager.load("database")
    >>> manager.start("database")
    数据库已连接
"""

from __future__ import annotations

__version__ = "2.0.0"

# 核心类和函数
from .core import (
    CircularDependencyError,
    DependencyError,
    FileStateStore,
    LoaderError,
    MemoryStateStore,
    Module,
    ModuleError,
    ModuleNotFoundError,
    ModuleState,
    ModuleStateError,
    StateStore,
    call_module_method,
    is_async_module,
)

# 依赖解析
from .dependency import DependencyGraph, DependencyResolver

# 生命周期管理
from .lifecycle import LifecycleManager

# 加载器
from .loader import FileSystemLoader, ModuleLoader

# 主管理器
from .manager import ModuleManager

__all__ = [
    # 版本
    "__version__",
    # 核心类
    "Module",
    "ModuleState",
    "ModuleManager",
    # 异常
    "ModuleError",
    "CircularDependencyError",
    "DependencyError",
    "LoaderError",
    "ModuleNotFoundError",
    "ModuleStateError",
    # 工具函数
    "call_module_method",
    "is_async_module",
    # 持久化
    "StateStore",
    "MemoryStateStore",
    "FileStateStore",
    # 高级组件（可选使用）
    "DependencyGraph",
    "DependencyResolver",
    "ModuleLoader",
    "FileSystemLoader",
    "LifecycleManager",
]
