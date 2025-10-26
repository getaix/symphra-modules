"""模块加载器基类."""

import inspect
from abc import ABC, abstractmethod
from typing import Any

from symphra_modules.abc import BaseModule, ModuleInterface, ModuleMetadata
from symphra_modules.utils import get_logger

logger = get_logger()


class ModuleLoader(ABC):
    """模块加载器抽象基类."""

    @abstractmethod
    def load(self, source: str) -> dict[str, type[ModuleInterface]]:
        """从源加载模块.

        Args:
            source: 模块源（目录路径、包名等）

        Returns:
            模块名到模块类的映射字典
        """

    @abstractmethod
    def discover(self, source: str) -> list[str]:
        """发现可用的模块.

        Args:
            source: 模块源

        Returns:
            模块名称列表
        """

    def _is_valid_module_class(self, obj: Any) -> bool:
        """检查对象是否是有效的模块类.

        Args:
            obj: 待检查的对象

        Returns:
            是否为有效的模块类
        """
        # 跳过抽象类和自身
        if obj is BaseModule or inspect.isabstract(obj):
            return False

        # 必须是类
        if not inspect.isclass(obj):
            return False

        # 检查必需的属性和方法
        required_attrs = ["metadata", "install", "start", "stop"]
        if not all(hasattr(obj, attr) for attr in required_attrs):
            return False

        # 检查 metadata 是否是 property
        return isinstance(getattr(type(obj), "metadata", None), property)

    def _validate_module_instance(self, obj: type[ModuleInterface]) -> bool:
        """验证模块实例是否有效.

        Args:
            obj: 模块类

        Returns:
            是否可以成功实例化并获取元数据
        """
        try:
            instance = obj()
            metadata = instance.metadata
            return isinstance(metadata, ModuleMetadata)
        except Exception as e:
            logger.warning(f"无法实例化模块类 {obj.__name__}: {e}")
            return False

    def _find_module_classes(self, module: Any) -> dict[str, type[ModuleInterface]]:
        """在模块中查找有效的模块类.

        Args:
            module: 要搜索的 Python 模块

        Returns:
            模块名到模块类的映射字典
        """
        module_classes: dict[str, type[ModuleInterface]] = {}

        # 获取模块中的所有类
        for name, obj in inspect.getmembers(module, inspect.isclass):
            # 基本有效性检查
            if not self._is_valid_module_class(obj):
                continue

            # 实例验证
            if self._validate_module_instance(obj):
                module_classes[name] = obj

        return module_classes
