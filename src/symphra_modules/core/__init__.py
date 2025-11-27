"""核心模块.

导出核心类型、异常、状态和持久化接口。
"""

from .exceptions import (
    CircularDependencyError,
    DependencyError,
    LoaderError,
    ModuleError,
    ModuleNotFoundError,
    ModuleStateError,
)
from .module import Module, call_module_method, is_async_module
from .persistence import FileStateStore, MemoryStateStore, StateStore
from .state import ModuleState, is_valid_transition

__all__ = [
    # 模块基类
    "Module",
    "is_async_module",
    "call_module_method",
    # 状态
    "ModuleState",
    "is_valid_transition",
    # 持久化
    "StateStore",
    "MemoryStateStore",
    "FileStateStore",
    # 异常
    "ModuleError",
    "CircularDependencyError",
    "DependencyError",
    "LoaderError",
    "ModuleNotFoundError",
    "ModuleStateError",
]
