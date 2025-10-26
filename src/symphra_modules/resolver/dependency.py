"""依赖解析器实现."""

from collections import defaultdict, deque

from symphra_modules.config import ModuleMetadata
from symphra_modules.exceptions import ModuleDependencyError


class DependencyGraph:
    """依赖关系图."""

    def __init__(self) -> None:
        """初始化依赖图."""
        self._graph: dict[str, set[str]] = defaultdict(set)  # 模块 -> 依赖的模块集合
        self._reverse_graph: dict[str, set[str]] = defaultdict(set)  # 模块 -> 依赖它的模块集合
        self._modules: dict[str, ModuleMetadata] = {}

    def add_module(self, metadata: ModuleMetadata) -> None:
        """添加模块到依赖图.

        Args:
            metadata: 模块元数据
        """
        name = metadata.name
        self._modules[name] = metadata

        # 初始化空依赖集合（即使没有依赖）
        if name not in self._graph:
            self._graph[name] = set()

        # 添加依赖关系
        for dep in metadata.dependencies:
            self._graph[name].add(dep)
            self._reverse_graph[dep].add(name)

    def get_dependencies(self, name: str) -> set[str]:
        """获取模块的直接依赖.

        Args:
            name: 模块名称

        Returns:
            依赖的模块名称集合
        """
        return self._graph.get(name, set())

    def get_dependents(self, name: str) -> set[str]:
        """获取依赖该模块的模块.

        Args:
            name: 模块名称

        Returns:
            依赖该模块的模块名称集合
        """
        return self._reverse_graph.get(name, set())

    def has_module(self, name: str) -> bool:
        """检查模块是否存在.

        Args:
            name: 模块名称

        Returns:
            是否存在
        """
        return name in self._modules

    def get_all_modules(self) -> list[str]:
        """获取所有模块名称.

        Returns:
            模块名称列表
        """
        return list(self._modules.keys())


class DependencyResolver:
    """依赖解析器 - 使用拓扑排序解析模块加载顺序."""

    def __init__(self) -> None:
        """初始化解析器."""
        self.graph = DependencyGraph()

    def add_module(self, metadata: ModuleMetadata) -> None:
        """添加模块.

        Args:
            metadata: 模块元数据
        """
        self.graph.add_module(metadata)

    def resolve(self) -> list[str]:
        """解析模块加载顺序（拓扑排序）.

        使用 Kahn 算法进行拓扑排序。

        Returns:
            按依赖顺序排列的模块名称列表

        Raises:
            ModuleDependencyError: 存在循环依赖或缺失依赖时抛出
        """
        # 检查缺失的依赖
        self._check_missing_dependencies()

        # 计算每个模块的入度（被依赖的次数）
        in_degree: dict[str, int] = defaultdict(int)
        for module in self.graph.get_all_modules():
            in_degree[module] = 0

        for module in self.graph.get_all_modules():
            for _dep in self.graph.get_dependencies(module):
                in_degree[module] += 1

        # 找到所有入度为 0 的模块（没有依赖的模块）
        queue: deque[str] = deque()
        for module in self.graph.get_all_modules():
            if in_degree[module] == 0:
                queue.append(module)

        result: list[str] = []

        while queue:
            # 取出一个入度为 0 的模块
            current = queue.popleft()
            result.append(current)

            # 对于所有依赖当前模块的模块，减少其入度
            for dependent in self.graph.get_dependents(current):
                in_degree[dependent] -= 1
                if in_degree[dependent] == 0:
                    queue.append(dependent)

        # 如果结果数量不等于模块总数，说明存在循环依赖
        if len(result) != len(self.graph.get_all_modules()):
            circular = self._detect_circular_dependencies(in_degree)
            raise ModuleDependencyError(
                "检测到循环依赖",
                circular_dependencies=circular,
            )

        return result

    def _check_missing_dependencies(self) -> None:
        """检查缺失的依赖.

        Raises:
            ModuleDependencyError: 存在缺失依赖时抛出
        """
        missing_deps: dict[str, list[str]] = {}

        for module in self.graph.get_all_modules():
            missing: list[str] = []
            for dep in self.graph.get_dependencies(module):
                if not self.graph.has_module(dep):
                    missing.append(dep)

            if missing:
                missing_deps[module] = missing

        if missing_deps:
            # 格式化错误消息
            error_details = []
            for module, deps in missing_deps.items():
                error_details.append(f"{module}: {', '.join(deps)}")

            raise ModuleDependencyError(
                f"缺失依赖: {'; '.join(error_details)}",
                missing_dependencies=list(missing_deps.keys()),
            )

    def _detect_circular_dependencies(self, in_degree: dict[str, int]) -> list[str]:
        """检测循环依赖.

        Args:
            in_degree: 模块入度映射

        Returns:
            参与循环依赖的模块列表
        """
        circular: list[str] = []
        for module, degree in in_degree.items():
            if degree > 0:
                circular.append(module)
        return circular

    def get_load_order_for_module(self, name: str) -> list[str]:
        """获取加载特定模块所需的顺序（包括其所有依赖）.

        Args:
            name: 模块名称

        Returns:
            按依赖顺序排列的模块名称列表（包含该模块自身）

        Raises:
            ModuleDependencyError: 模块不存在或依赖有问题时抛出
        """
        if not self.graph.has_module(name):
            raise ModuleDependencyError(f"模块不存在: {name}", module_name=name)

        # 使用 DFS 收集所有依赖
        visited: set[str] = set()
        stack: list[str] = []
        visiting: set[str] = set()  # 用于检测循环依赖

        def dfs(module: str) -> None:
            if module in visited:
                return
            if module in visiting:
                # 检测到循环依赖
                raise ModuleDependencyError(
                    f"检测到循环依赖，涉及模块: {module}",
                    module_name=module,
                    circular_dependencies=[module],
                )

            visiting.add(module)

            # 先处理依赖
            for dep in self.graph.get_dependencies(module):
                if not self.graph.has_module(dep):
                    raise ModuleDependencyError(
                        f"缺失依赖: {module} 依赖 {dep}",
                        module_name=module,
                        missing_dependencies=[dep],
                    )
                dfs(dep)

            visiting.remove(module)
            visited.add(module)
            stack.append(module)

        dfs(name)
        return stack
