"""模块管理系统的异常定义."""


class ModuleError(Exception):
    """模块系统的基类异常."""

    def __init__(self, message: str, module_name: str | None = None) -> None:
        """初始化异常.

        Args:
            message: 错误消息
            module_name: 模块名称（可选）
        """
        super().__init__(message)
        self.module_name = module_name


class ModuleNotFoundException(ModuleError):
    """模块未找到异常."""


class ModuleLoadError(ModuleError):
    """模块加载失败异常."""


class ModuleConfigError(ModuleError):
    """模块配置异常."""


class ConfigValidationError(ModuleConfigError):
    """配置验证错误异常."""


class ModuleStateError(ModuleError):
    """模块状态异常."""

    def __init__(
        self,
        message: str,
        module_name: str | None = None,
        current_state: str | None = None,
        expected_states: list[str] | None = None,
    ) -> None:
        """初始化状态异常.

        Args:
            message: 错误消息
            module_name: 模块名称（可选）
            current_state: 当前状态（可选）
            expected_states: 期望状态列表（可选）
        """
        super().__init__(message, module_name)
        self.current_state = current_state
        self.expected_states = expected_states or []


class ModuleDependencyError(ModuleError):
    """模块依赖错误异常."""

    def __init__(
        self,
        message: str,
        module_name: str | None = None,
        missing_dependencies: list[str] | None = None,
        circular_dependencies: list[str] | None = None,
    ) -> None:
        """初始化依赖异常.

        Args:
            message: 错误消息
            module_name: 模块名称（可选）
            missing_dependencies: 缺失的依赖列表（可选）
            circular_dependencies: 循环依赖列表（可选）
        """
        super().__init__(message, module_name)
        self.missing_dependencies = missing_dependencies or []
        self.circular_dependencies = circular_dependencies or []


class EventError(ModuleError):
    """事件系统错误异常."""
