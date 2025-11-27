"""依赖图实现.

这个模块实现了基于 Kahn 算法的依赖图和拓扑排序。
职责：管理节点和依赖关系，执行拓扑排序，检测循环依赖。
"""

from __future__ import annotations

import threading
from typing import TYPE_CHECKING

from ..core.exceptions import CircularDependencyError

if TYPE_CHECKING:
    from collections.abc import Sequence


class DependencyGraph:
    """依赖图 - 使用 Kahn 算法进行拓扑排序.

    职责：
    - 添加节点和依赖关系
    - 执行拓扑排序
    - 检测循环依赖
    - 线程安全操作

    时间复杂度: O(V + E)，其中 V 是节点数，E 是边数
    """

    def __init__(self) -> None:
        """初始化依赖图."""
        # 存储节点及其依赖关系: {节点名: {依赖节点集合}}
        self._nodes: dict[str, set[str]] = {}
        # 线程锁，保护共享状态
        self._lock = threading.RLock()
        # 缓存拓扑排序结果
        self._cached_sort: list[str] | None = None
        self._dirty = True

    def add_node(self, name: str, dependencies: Sequence[str]) -> None:
        """添加节点及其依赖关系.

        Args:
            name: 节点名称
            dependencies: 依赖的节点列表
        """
        with self._lock:
            # 确保当前节点在图中
            if name not in self._nodes:
                self._nodes[name] = set()

            # 添加依赖关系
            self._nodes[name].update(dependencies)

            # 确保依赖节点也在图中
            for dep in dependencies:
                if dep not in self._nodes:
                    self._nodes[dep] = set()

            # 标记缓存为脏
            self._dirty = True

    def remove_node(self, name: str) -> None:
        """移除节点.

        Args:
            name: 节点名称
        """
        with self._lock:
            if name in self._nodes:
                # 移除节点
                del self._nodes[name]

                # 移除所有对此节点的依赖
                for node_deps in self._nodes.values():
                    node_deps.discard(name)

                # 标记缓存为脏
                self._dirty = True

    def topological_sort(self) -> list[str]:
        """执行拓扑排序 - Kahn 算法.

        使用 Kahn 算法进行拓扑排序，确保依赖关系正确。
        结果会被缓存，除非依赖图被修改。

        Returns:
            排序后的节点列表

        Raises:
            CircularDependencyError: 存在循环依赖
        """
        with self._lock:
            # 如果缓存有效，直接返回
            if not self._dirty and self._cached_sort is not None:
                return self._cached_sort.copy()

            # 构建邻接表和入度表
            # adj_list[node] 表示依赖于 node 的节点集合
            # in_degree[node] 表示 node 的入度（node 依赖的节点数）
            adj_list: dict[str, set[str]] = {node: set() for node in self._nodes}
            in_degree: dict[str, int] = dict.fromkeys(self._nodes, 0)

            # 构建邻接表和计算入度
            for node in self._nodes:
                for dep in self._nodes[node]:
                    # node 依赖于 dep
                    # 所以添加边 dep -> node
                    adj_list[dep].add(node)
                    in_degree[node] += 1

            # 入度为 0 的节点入队（没有依赖或依赖已处理完）
            queue = [node for node, degree in in_degree.items() if degree == 0]
            result: list[str] = []

            while queue:
                # 取出入度为 0 的节点（可以执行的节点）
                current = queue.pop(0)
                result.append(current)

                # 更新依赖于当前节点的节点的入度
                for neighbor in adj_list[current]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)

            # 检测循环依赖
            if len(result) != len(self._nodes):
                # 找到未处理的节点（存在循环依赖）
                remaining = list(set(self._nodes.keys()) - set(result))
                raise CircularDependencyError(remaining)

            # 缓存结果
            self._cached_sort = result.copy()
            self._dirty = False

            return result

    def clear(self) -> None:
        """清空依赖图."""
        with self._lock:
            self._nodes.clear()
            self._cached_sort = None
            self._dirty = True

    def has_node(self, name: str) -> bool:
        """检查节点是否存在.

        Args:
            name: 节点名称

        Returns:
            如果节点存在返回 True，否则返回 False
        """
        with self._lock:
            return name in self._nodes

    def get_dependencies(self, name: str) -> set[str]:
        """获取节点的直接依赖.

        Args:
            name: 节点名称

        Returns:
            依赖节点的集合
        """
        with self._lock:
            return self._nodes.get(name, set()).copy()

    def get_all_nodes(self) -> list[str]:
        """获取所有节点名称.

        Returns:
            节点名称列表
        """
        with self._lock:
            return list(self._nodes.keys())
