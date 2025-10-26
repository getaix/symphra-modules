"""模块注册表实现."""

from typing import Any

from symphra_modules.abc import BaseModule, ModuleInterface
from symphra_modules.config import ModuleInfo, ModuleState
from symphra_modules.exceptions import ModuleNotFoundException, ModuleStateError
from symphra_modules.utils import get_logger, now

logger = get_logger()


class ModuleRegistry:
    """模块注册表，管理模块实例和生命周期."""

    def __init__(self) -> None:
        """初始化注册表."""
        self._modules: dict[str, ModuleInterface] = {}
        self._module_info: dict[str, ModuleInfo] = {}

    def register(
        self, name: str, module_class: type[BaseModule], config: dict[str, Any] | None = None
    ) -> ModuleInterface:
        """注册模块.

        Args:
            name: 模块名称
            module_class: 模块类
            config: 初始配置（可选）

        Returns:
            模块实例

        Raises:
            ModuleStateError: 模块已注册时抛出
        """
        if name in self._modules:
            raise ModuleStateError(f"模块 {name} 已经注册")

        module_instance = module_class(config)
        module_instance.bootstrap()  # 调用引导方法

        # 创建模块信息
        module_info = ModuleInfo(
            metadata=module_instance.metadata,
            state=ModuleState.LOADED,
            loaded_at=now(),
        )
        self._modules[name] = module_instance
        self._module_info[name] = module_info
        logger.info(f"模块 {name} 注册成功")

        return module_instance

    def unregister(self, name: str) -> None:
        """注销模块.

        Args:
            name: 模块名称
        """
        _, info = self._get_module_and_info(name)
        if info.state == ModuleState.STARTED:
            self.stop(name)

        del self._modules[name]
        del self._module_info[name]

        logger.info(f"模块 {name} 注销成功")

    def install(self, name: str, config: dict[str, Any] | None = None) -> None:
        """安装模块.

        Args:
            name: 模块名称
            config: 安装配置（可选）

        Raises:
            ModuleStateError: 状态不正确时抛出
        """
        module, info = self._get_module_and_info(name)

        # 已加载的模块才允许安装
        if info.state != ModuleState.LOADED:
            raise ModuleStateError(
                f"模块 {name} 状态错误，当前状态为 {info.state}，期望状态为 {ModuleState.LOADED}",
                module_name=name,
                current_state=info.state,
                expected_states=[ModuleState.LOADED],
            )

        try:
            module.install(config)
            info.state = ModuleState.INSTALLED
            info.installed_at = now()

            if config:
                module.configure(config)
                info.config = config

            logger.info(f"模块 {name} 安装成功")
        except Exception as e:
            info.state = ModuleState.ERROR
            raise ModuleStateError(f"模块 {name} 安装失败: {e}", module_name=name) from e

    def uninstall(self, name: str) -> None:
        """卸载模块.

        Args:
            name: 模块名称

        Raises:
            ModuleStateError: 状态不正确时抛出
        """
        module, info = self._get_module_and_info(name)

        if info.state not in [
            ModuleState.INSTALLED,
            ModuleState.STOPPED,
        ]:
            raise ModuleStateError(
                f"无法卸载模块 {name}，当前状态为 {info.state}",
                module_name=name,
                current_state=info.state,
                expected_states=[ModuleState.INSTALLED, ModuleState.STOPPED],
            )
        try:
            module.uninstall()
            info.state = ModuleState.LOADED
            info.installed_at = None
            info.started_at = None
            logger.info(f"模块 {name} 卸载成功")
        except Exception as e:
            info.state = ModuleState.ERROR
            raise ModuleStateError(f"模块 {name} 卸载失败: {e}", module_name=name) from e

    def start(self, name: str) -> None:
        """启动模块.

        Args:
            name: 模块名称

        Raises:
            ModuleStateError: 状态不正确时抛出
        """
        module, info = self._get_module_and_info(name)

        if info.state not in [ModuleState.INSTALLED, ModuleState.STOPPED]:
            raise ModuleStateError(
                f"无法启动模块 {name}，当前状态为 {info.state}",
                module_name=name,
                current_state=info.state,
                expected_states=[ModuleState.INSTALLED, ModuleState.STOPPED],
            )
        try:
            module.start()
            info.state = ModuleState.STARTED
            info.started_at = now()

            logger.info(f"模块 {name} 启动成功")

        except Exception as e:
            info.state = ModuleState.ERROR
            raise ModuleStateError(f"模块 {name} 启动失败: {e}", module_name=name) from e

    def stop(self, name: str) -> None:
        """停止模块.

        Args:
            name: 模块名称

        Raises:
            ModuleStateError: 停止失败时抛出
        """
        module, info = self._get_module_and_info(name)

        if info.state != ModuleState.STARTED:
            return  # 模块未启动，无需停止

        try:
            module.stop()
            info.state = ModuleState.STOPPED
            info.started_at = None

            logger.info(f"模块 {name} 停止成功")

        except Exception as e:
            info.state = ModuleState.ERROR
            raise ModuleStateError(f"模块 {name} 停止失败: {e}", module_name=name) from e

    def reload(self, name: str) -> None:
        """重载模块.

        Args:
            name: 模块名称

        Raises:
            ModuleStateError: 重载失败时抛出
        """
        module, _ = self._get_module_and_info(name)
        try:
            module.reload()
            logger.info(f"模块 {name} 重载成功")
        except Exception as e:
            self._module_info[name].state = ModuleState.ERROR
            raise ModuleStateError(f"模块 {name} 重载失败: {e}", module_name=name) from e

    def configure(self, name: str, config: dict[str, Any] | None = None) -> None:
        """配置模块.

        Args:
            name: 模块名称
            config: 配置字典（可选）

        Raises:
            ModuleStateError: 配置失败时抛出
        """
        module, info = self._get_module_and_info(name)

        try:
            module.configure(config)
            info.config = config or {}
            logger.info(f"模块 {name} 配置成功")
        except Exception as e:
            raise ModuleStateError(f"模块 {name} 配置失败: {e}", module_name=name) from e

    def get(self, name: str) -> ModuleInterface | None:
        """获取模块实例.

        Args:
            name: 模块名称

        Returns:
            模块实例，如果不存在则返回 None
        """
        return self._modules.get(name)

    def get_info(self, name: str) -> ModuleInfo | None:
        """获取模块信息.

        Args:
            name: 模块名称

        Returns:
            模块信息，如果不存在则返回 None
        """
        return self._module_info.get(name)

    def list_modules(self) -> list[str]:
        """列出所有已加载模块的名称.

        Returns:
            模块名称列表
        """
        return list(self._modules.keys())

    def list_modules_by_state(self, state: ModuleState) -> list[str]:
        """根据状态列出模块名称.

        Args:
            state: 模块状态

        Returns:
            符合状态的模块名称列表
        """
        return [name for name, info in self._module_info.items() if info.state == state]

    def get_module_states(self) -> dict[str, ModuleState]:
        """获取所有模块状态.

        Returns:
            模块名到状态的映射
        """
        return {name: info.state for name, info in self._module_info.items()}

    def is_installed(self, name: str) -> bool:
        """检查模块是否已安装.

        Args:
            name: 模块名称

        Returns:
            是否已安装
        """
        info = self.get_info(name)
        return info is not None and info.state in [
            ModuleState.INSTALLED,
            ModuleState.STARTED,
            ModuleState.STOPPED,
        ]

    def is_loaded(self, name: str) -> bool:
        """检查模块是否已加载.

        Args:
            name: 模块名称

        Returns:
            是否已加载
        """
        return name in self._modules

    def is_started(self, name: str) -> bool:
        """检查模块是否已启动.

        Args:
            name: 模块名称

        Returns:
            是否已启动
        """
        info = self.get_info(name)
        return info is not None and info.state == ModuleState.STARTED

    def _ensure_module_loaded(self, name: str) -> None:
        """确保模块已加载.

        Args:
            name: 模块名称

        Raises:
            ModuleNotFoundException: 模块未注册时抛出
        """
        if name not in self._modules:
            raise ModuleNotFoundException(f"模块 {name} 未注册", module_name=name)

    def _get_module_and_info(self, name: str) -> tuple[ModuleInterface, ModuleInfo]:
        """获取模块实例和信息.

        Args:
            name: 模块名称

        Returns:
            (模块实例, 模块信息)元组

        Raises:
            ModuleNotFoundException: 模块未注册时抛出
        """
        self._ensure_module_loaded(name)
        return self._modules[name], self._module_info[name]
