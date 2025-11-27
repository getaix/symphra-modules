"""核心异常定义.

这个模块定义了所有的异常类型，遵循单一职责原则。
"""

from __future__ import annotations


class ModuleError(Exception):
    """模块系统基础异常."""

    pass


class CircularDependencyError(ModuleError):
    """循环依赖异常.

    当检测到模块间存在循环依赖时抛出此异常。
    """

    def __init__(self, cycle: list[str]) -> None:
        """初始化循环依赖异常.

        Args:
            cycle: 循环依赖的模块列表
        """
        self.cycle = cycle
        cycle_str = " -> ".join(cycle)
        msg = f"检测到循环依赖: {cycle_str}\n"
        msg += "请检查模块的 dependencies 配置，确保没有循环引用"
        super().__init__(msg)


class DependencyError(ModuleError):
    """依赖错误异常.

    当模块的依赖项不存在或无法满足时抛出此异常。
    """

    def __init__(self, module_name: str, missing_deps: list[str] | None = None) -> None:
        """初始化依赖错误异常.

        Args:
            module_name: 模块名称
            missing_deps: 缺失的依赖列表
        """
        self.module_name = module_name
        self.missing_deps = missing_deps or []

        if self.missing_deps:
            deps_str = "、".join(self.missing_deps)
            msg = f"模块 '{module_name}' 的依赖项不存在: {deps_str}\n"
            msg += "请确保所有依赖模块都已正确安装和配置"
        else:
            msg = f"模块 '{module_name}' 存在依赖错误"

        super().__init__(msg)


class ModuleNotFoundError(ModuleError):
    """模块未找到异常.

    当请求的模块不存在时抛出此异常。
    """

    def __init__(self, message: str, module_name: str | None = None) -> None:
        """初始化模块未找到异常.

        Args:
            message: 错误消息
            module_name: 模块名称（可选）
        """
        self.module_name = module_name
        super().__init__(message)


class ModuleStateError(ModuleError):
    """模块状态错误异常.

    当对处于不正确状态的模块执行操作时抛出此异常。
    """

    def __init__(
        self,
        message: str,
        module_name: str | None = None,
        current_state: str | None = None,
        expected_state: str | None = None,
    ) -> None:
        """初始化模块状态错误异常.

        Args:
            message: 错误消息
            module_name: 模块名称（可选）
            current_state: 当前状态（可选）
            expected_state: 期望状态（可选）
        """
        self.module_name = module_name
        self.current_state = current_state
        self.expected_state = expected_state

        full_message = message
        if current_state and expected_state:
            full_message += f"\n当前状态: {current_state}, 期望状态: {expected_state}"
            full_message += "\n请先将模块切换到正确的状态后再执行此操作"

        super().__init__(full_message)


class LoaderError(ModuleError):
    """加载器错误异常.

    当模块加载过程中发生错误时抛出此异常。
    """

    def __init__(
        self, message: str, file_path: str | None = None, cause: Exception | None = None
    ) -> None:
        """初始化加载器错误异常.

        Args:
            message: 错误消息
            file_path: 出错的文件路径（可选）
            cause: 原始异常（可选）
        """
        self.file_path = file_path
        self.cause = cause

        full_message = message
        if file_path:
            full_message += f"\n文件路径: {file_path}"
        if cause:
            full_message += f"\n原因: {type(cause).__name__}: {str(cause)}"
            full_message += "\n请检查模块文件的语法和依赖是否正确"

        super().__init__(full_message)
