"""模块状态持久化接口.

这个模块定义了状态持久化的抽象接口和实现。
业务系统可以通过实现 StateStore 接口来自定义状态存储方式（如数据库、Redis 等）。
所有实现都是线程安全的。
"""

from __future__ import annotations

import json
import threading
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from .state import ModuleState


class StateStore(ABC):
    """状态存储抽象接口.

    业务系统可以实现此接口来自定义状态存储方式：
    - 数据库存储（MySQL、PostgreSQL 等）
    - NoSQL 存储（MongoDB、Redis 等）
    - 文件存储
    - 云存储
    """

    @abstractmethod
    def save_state(self, module_name: str, state: ModuleState) -> None:
        """保存模块状态.

        Args:
            module_name: 模块名称
            state: 模块状态
        """
        pass

    @abstractmethod
    def load_state(self, module_name: str) -> ModuleState | None:
        """加载模块状态.

        Args:
            module_name: 模块名称

        Returns:
            模块状态，如果不存在返回 None
        """
        pass

    @abstractmethod
    def delete_state(self, module_name: str) -> None:
        """删除模块状态.

        Args:
            module_name: 模块名称
        """
        pass

    @abstractmethod
    def list_states(self) -> dict[str, ModuleState]:
        """列出所有模块状态.

        Returns:
            模块名到状态的映射
        """
        pass

    @abstractmethod
    def save_ignored_modules(self, ignored_modules: set[str]) -> None:
        """保存忽略的模块列表.

        Args:
            ignored_modules: 忽略的模块名称集合
        """
        pass

    @abstractmethod
    def load_ignored_modules(self) -> set[str]:
        """加载忽略的模块列表.

        Returns:
            忽略的模块名称集合
        """
        pass


class MemoryStateStore(StateStore):
    """内存状态存储 - 仅用于测试和临时存储."""

    def __init__(self) -> None:
        """初始化内存存储."""
        self._states: dict[str, ModuleState] = {}
        self._ignored_modules: set[str] = set()

    def save_state(self, module_name: str, state: ModuleState) -> None:
        """保存模块状态到内存."""
        self._states[module_name] = state

    def load_state(self, module_name: str) -> ModuleState | None:
        """从内存加载模块状态."""
        return self._states.get(module_name)

    def delete_state(self, module_name: str) -> None:
        """从内存删除模块状态."""
        if module_name in self._states:
            del self._states[module_name]

    def list_states(self) -> dict[str, ModuleState]:
        """列出所有模块状态."""
        return self._states.copy()

    def save_ignored_modules(self, ignored_modules: set[str]) -> None:
        """保存忽略的模块列表."""
        self._ignored_modules = ignored_modules.copy()

    def load_ignored_modules(self) -> set[str]:
        """加载忽略的模块列表."""
        return self._ignored_modules.copy()


class FileStateStore(StateStore):
    """文件状态存储 - 将状态保存到 JSON 文件.

    线程安全：所有公共方法都使用锁保护。
    """

    def __init__(self, file_path: str | Path = ".module_states.json") -> None:
        """初始化文件存储.

        Args:
            file_path: 状态文件路径，默认为当前目录下的 .module_states.json
        """
        self._file_path = Path(file_path)
        self._data: dict[str, Any] = self._load_data()
        # 使用可重入锁保护数据和文件操作
        self._lock = threading.RLock()

    def _load_data(self) -> dict[str, Any]:
        """从文件加载数据."""
        if not self._file_path.exists():
            return {"states": {}, "ignored_modules": []}

        try:
            with open(self._file_path, encoding="utf-8") as f:
                data = json.load(f)
                # 确保数据结构正确
                if not isinstance(data, dict):
                    return {"states": {}, "ignored_modules": []}
                if "states" not in data:
                    data["states"] = {}
                if "ignored_modules" not in data:
                    data["ignored_modules"] = []
                return data
        except Exception:
            # 如果文件损坏，返回空数据
            return {"states": {}, "ignored_modules": []}

    def _save_data(self) -> None:
        """保存数据到文件."""
        try:
            # 确保父目录存在
            self._file_path.parent.mkdir(parents=True, exist_ok=True)

            with open(self._file_path, "w", encoding="utf-8") as f:
                json.dump(self._data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            raise RuntimeError(f"保存状态文件失败: {e}") from e

    def save_state(self, module_name: str, state: ModuleState) -> None:
        """保存模块状态到文件（线程安全）.

        Args:
            module_name: 模块名称
            state: 模块状态
        """
        with self._lock:
            self._data["states"][module_name] = state.value
            self._save_data()

    def load_state(self, module_name: str) -> ModuleState | None:
        """从文件加载模块状态（线程安全）.

        Args:
            module_name: 模块名称

        Returns:
            模块状态，如果不存在返回 None
        """
        with self._lock:
            state_value = self._data["states"].get(module_name)
            if state_value is None:
                return None

            try:
                return ModuleState(state_value)
            except ValueError:
                # 如果状态值无效，返回 None
                return None

    def delete_state(self, module_name: str) -> None:
        """从文件删除模块状态（线程安全）.

        Args:
            module_name: 模块名称
        """
        with self._lock:
            if module_name in self._data["states"]:
                del self._data["states"][module_name]
                self._save_data()

    def list_states(self) -> dict[str, ModuleState]:
        """列出所有模块状态（线程安全）.

        Returns:
            模块名到状态的映射
        """
        with self._lock:
            result = {}
            for name, value in self._data["states"].items():
                try:
                    result[name] = ModuleState(value)
                except ValueError:
                    # 跳过无效状态
                    continue
            return result

    def save_ignored_modules(self, ignored_modules: set[str]) -> None:
        """保存忽略的模块列表（线程安全）.

        Args:
            ignored_modules: 忽略的模块名称集合
        """
        with self._lock:
            self._data["ignored_modules"] = list(ignored_modules)
            self._save_data()

    def load_ignored_modules(self) -> set[str]:
        """加载忽略的模块列表（线程安全）.

        Returns:
            忽略的模块名称集合
        """
        with self._lock:
            return set(self._data.get("ignored_modules", []))
