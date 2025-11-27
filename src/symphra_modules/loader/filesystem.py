"""文件系统模块加载器.

这个模块实现了从文件系统加载模块的功能。
职责：从指定目录发现和加载 Python 模块文件。
本模块是线程安全的。
"""

from __future__ import annotations

import importlib.util
import logging
import sys
import threading
from typing import TYPE_CHECKING

from ..core.exceptions import LoaderError
from .base import ModuleLoader

if TYPE_CHECKING:
    from pathlib import Path

    from ..core.module import Module

logger = logging.getLogger(__name__)


class FileSystemLoader(ModuleLoader):
    """文件系统模块加载器.

    职责：
    - 扫描指定目录下的 Python 文件
    - 动态导入模块
    - 提取 Module 子类
    - 线程安全的缓存管理
    """

    def __init__(self, directories: list[Path]) -> None:
        """初始化文件系统加载器.

        Args:
            directories: 要扫描的目录列表
        """
        self._directories = directories
        self._modules_cache: dict[str, type[Module]] = {}
        # 使用可重入锁保护缓存
        self._lock = threading.RLock()

    def discover(self) -> dict[str, type[Module]]:
        """发现所有可用模块（线程安全）.

        Returns:
            模块名到模块类的映射
        """
        modules: dict[str, type[Module]] = {}

        for directory in self._directories:
            discovered = self._discover_in_directory(directory)
            modules.update(discovered)

        # 更新缓存（使用锁保护）
        with self._lock:
            self._modules_cache = modules
        return modules

    def _discover_in_directory(self, directory: Path) -> dict[str, type[Module]]:
        """在指定目录中发现模块.

        Args:
            directory: 目录路径

        Returns:
            模块名到模块类的映射
        """
        modules: dict[str, type[Module]] = {}

        if not directory.exists():
            logger.warning(f"模块目录不存在: {directory}")
            return modules

        if not directory.is_dir():
            logger.warning(f"路径不是目录: {directory}")
            return modules

        # 遍历 Python 文件
        for file_path in directory.glob("*.py"):
            # 跳过私有文件
            if file_path.name.startswith("_"):
                continue

            try:
                discovered = self._load_from_file(file_path)
                modules.update(discovered)
            except Exception as e:
                logger.error(f"加载模块文件失败 {file_path}: {e}", exc_info=True)

        return modules

    def _load_from_file(self, file_path: Path) -> dict[str, type[Module]]:
        """从文件中加载模块.

        Args:
            file_path: 文件路径

        Returns:
            模块名到模块类的映射
        """
        from ..core.module import Module

        modules: dict[str, type[Module]] = {}

        # 动态导入模块
        module_name = file_path.stem
        spec = importlib.util.spec_from_file_location(module_name, file_path)

        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            sys.modules[module_name] = module
            spec.loader.exec_module(module)

            # 查找 Module 子类
            for attr_name in dir(module):
                attr = getattr(module, attr_name)

                if (
                    isinstance(attr, type)
                    and issubclass(attr, Module)
                    and attr is not Module
                    and hasattr(attr, "name")
                ):
                    modules[attr.name] = attr
                    logger.debug(
                        f"发现模块: {attr.name} (版本: {getattr(attr, 'version', '0.1.0')})"
                    )

        return modules

    def load_class(self, name: str) -> type[Module]:
        """加载指定模块的类（线程安全）.

        Args:
            name: 模块名称

        Returns:
            模块类

        Raises:
            LoaderError: 模块不存在
        """
        with self._lock:
            if name in self._modules_cache:
                return self._modules_cache[name]

        # 重新发现模块（discover 方法自己会加锁）
        self.discover()

        with self._lock:
            if name not in self._modules_cache:
                raise LoaderError(f"模块 '{name}' 未找到")
            return self._modules_cache[name]

    def reload(self) -> None:
        """重新加载所有模块（线程安全）.

        清空缓存并重新发现模块。
        """
        with self._lock:
            self._modules_cache.clear()
        # discover 方法自己会加锁
        self.discover()
