"""依赖解析器实现.

这个模块实现了依赖解析逻辑，负责构建和验证依赖关系。
职责：解析模块依赖关系，构建依赖图，检测循环依赖和缺失依赖。
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from ..core.exceptions import CircularDependencyError, DependencyError
from .graph import DependencyGraph

if TYPE_CHECKING:
    from ..core.module import Module


class DependencyResolver:
    """依赖解析器.

    职责：
    - 解析模块的依赖关系
    - 构建完整的依赖图
    - 检测循环依赖
    - 验证依赖完整性
    """

    def __init__(self) -> None:
        """初始化依赖解析器."""
        self._graph = DependencyGraph()

    def resolve(self, module_name: str, available_modules: dict[str, type[Module]]) -> list[str]:
        """解析模块依赖并返回加载顺序.

        Args:
            module_name: 要解析的模块名称
            available_modules: 所有可用的模块类 {name: class}

        Returns:
            按依赖顺序排列的模块名称列表

        Raises:
            DependencyError: 依赖缺失
            CircularDependencyError: 循环依赖
        """
        # 清空旧的依赖图
        self._graph.clear()

        # 递归构建依赖图
        self._build_graph(module_name, available_modules, set())

        # 返回拓扑排序结果
        try:
            return self._graph.topological_sort()
        except CircularDependencyError:
            raise

    def _build_graph(
        self,
        module_name: str,
        available_modules: dict[str, type[Module]],
        visiting: set[str],
    ) -> None:
        """递归构建依赖图.

        Args:
            module_name: 当前模块名称
            available_modules: 所有可用的模块类
            visiting: 当前访问路径中的节点集合（用于检测循环）

        Raises:
            DependencyError: 依赖缺失
            CircularDependencyError: 循环依赖
        """
        # 检查模块是否存在
        if module_name not in available_modules:
            raise DependencyError(module_name=module_name, missing_deps=[])

        # 检测循环依赖
        if module_name in visiting:
            cycle = list(visiting) + [module_name]
            raise CircularDependencyError(cycle)

        # 获取模块的依赖
        module_class = available_modules[module_name]
        dependencies = getattr(module_class, "dependencies", [])

        # 添加到依赖图（如果还没有添加）
        if not self._graph.has_node(module_name):
            self._graph.add_node(module_name, dependencies)

        # 标记当前节点为正在访问
        visiting.add(module_name)

        # 递归处理依赖
        for dep in dependencies:
            if dep not in available_modules:
                raise DependencyError(module_name=module_name, missing_deps=[dep])

            # 递归构建
            self._build_graph(dep, available_modules, visiting)

        # 移除当前节点的访问标记（回溯）
        visiting.discard(module_name)

    def get_graph(self) -> DependencyGraph:
        """获取依赖图对象.

        Returns:
            依赖图实例
        """
        return self._graph
