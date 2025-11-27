"""模块加载器基类.

这个模块定义了模块加载器的抽象接口。
职责：定义模块发现和加载的接口。
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..core.module import Module


class ModuleLoader(ABC):
    """模块加载器抽象基类.

    定义了模块加载器必须实现的接口。
    """

    @abstractmethod
    def discover(self) -> dict[str, type[Module]]:
        """发现所有可用模块.

        Returns:
            模块名到模块类的映射 {name: class}
        """
        pass

    @abstractmethod
    def load_class(self, name: str) -> type[Module]:
        """加载指定模块的类.

        Args:
            name: 模块名称

        Returns:
            模块类

        Raises:
            LoaderError: 加载失败
        """
        pass
