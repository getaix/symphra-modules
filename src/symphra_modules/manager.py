"""模块管理器实现."""

from typing import Any

from symphra_modules.abc import ModuleInterface
from symphra_modules.config import ModuleState
from symphra_modules.exceptions import ModuleNotFoundException
from symphra_modules.loader import DirectoryLoader, PackageLoader
from symphra_modules.registry import ModuleRegistry
from symphra_modules.utils import get_logger

logger = get_logger()


class ModuleManager:
    """模块管理器 - 统一的模块管理门面."""

    def __init__(
        self,
        module_dirs: list[str] | None = None,
        exclude_modules: set[str] | None = None,
    ) -> None:
        """初始化模块管理器.

        Args:
            module_dirs: 模块目录列表，默认为 ["modules"]
            exclude_modules: 排除的模块名称集合（不区分大小写）
        """
        self.registry = ModuleRegistry()
        self.module_dirs = module_dirs if module_dirs is not None else ["modules"]
        # 排除列表：用于忽略并非真正模块的目录/包（例如 common 为通用基类集合）
        _exmods = exclude_modules or {"common"}
        self.exclude_modules = {m.lower() for m in _exmods}
        self._directory_loader = DirectoryLoader()
        self._package_loader = PackageLoader()
        self._modules_cache: dict[str, dict[str, type[ModuleInterface]]] = {}
        self._discover_cache: dict[str, list[str]] = {}

    def _invalidate_directory_cache(self, directory: str | None = None) -> None:
        """失效目录缓存，支持单目录或全部清理.

        Args:
            directory: 要清理的目录，None 表示清理所有缓存
        """
        if directory is not None:
            self._modules_cache.pop(directory, None)
            self._discover_cache.pop(directory, None)
        else:
            self._modules_cache.clear()
            self._discover_cache.clear()

    def _get_modules_from_directory(self, directory: str) -> dict[str, type[ModuleInterface]]:
        """获取目录中的模块，带缓存.

        Args:
            directory: 目录路径

        Returns:
            模块类字典
        """
        if directory not in self._modules_cache:
            modules = self._directory_loader.load(directory)
            self._modules_cache[directory] = modules
        return self._modules_cache[directory]

    def _discover_from_directory(self, directory: str) -> list[str]:
        """发现目录模块名称，带缓存.

        Args:
            directory: 目录路径

        Returns:
            模块名称列表
        """
        if directory not in self._discover_cache:
            names = self._directory_loader.discover(directory)
            self._discover_cache[directory] = names
        return self._discover_cache[directory]

    @staticmethod
    def _match_module_by_name(
        modules: dict[str, type[ModuleInterface]],
        target_name: str,
    ) -> type[ModuleInterface] | None:
        """在模块字典中按名称匹配模块类（忽略大小写与 Module 后缀）.

        Args:
            modules: 模块类字典
            target_name: 目标模块名

        Returns:
            匹配的模块类，未找到则返回 None
        """
        name_lower = target_name.lower()
        candidates = {name_lower, f"{name_lower}module"}
        for module_name, module_class in modules.items():
            if module_name.lower() in candidates:
                return module_class
        return None

    def load_module(self, name: str, source: str | None = None, source_type: str = "directory") -> ModuleInterface:
        """加载模块并注册到注册表，返回模块实例.

        Args:
            name: 模块名称
            source: 模块源（可选）
            source_type: 源类型（"directory" 或 "package"）

        Returns:
            模块实例

        Raises:
            ModuleNotFoundException: 模块未找到时抛出
        """
        # 已加载则直接返回
        if self.registry.is_loaded(name):
            existing = self.registry.get(name)
            assert existing is not None
            return existing

        found_module: type[ModuleInterface] | None = None

        if source:
            if source_type == "directory":
                modules = self._get_modules_from_directory(source)
                found_module = self._match_module_by_name(modules, name)
            elif source_type == "package":
                modules = self._package_loader.load(source)
                found_module = modules.get(name) or modules.get(f"{name}Module")
        else:
            # 从配置的目录查找
            for module_dir in self.module_dirs:
                try:
                    modules = self._get_modules_from_directory(module_dir)
                    found_module = self._match_module_by_name(modules, name)
                    if found_module:
                        break
                except Exception as e:
                    logger.warning(f"无法从目录 {module_dir} 加载模块: {e}")

        if not found_module:
            raise ModuleNotFoundException(f"找不到模块: {name}", module_name=name)

        # 注册模块（将类传入注册表，由注册表负责实例化与生命周期）
        module_instance = self.registry.register(name, found_module)  # type: ignore[arg-type]
        return module_instance

    def load_all_modules(self) -> dict[str, ModuleInterface]:
        """加载所有可用模块.

        Returns:
            模块名到模块实例的映射
        """
        modules: dict[str, ModuleInterface] = {}
        available_modules = self.discover_modules()

        for module_name in available_modules:
            try:
                module = self.load_module(module_name)
                modules[module_name] = module
            except Exception as e:
                # 对于被排除的"非模块目录"，仅记录告警以降低噪音
                if module_name.lower() in self.exclude_modules:
                    logger.warning(f"忽略非模块目录: {module_name}")
                else:
                    logger.error(f"加载模块失败: {module_name} - {e}")

        return modules

    def discover_modules(self, source: str | None = None, source_type: str = "directory") -> list[str]:
        """发现可用模块名称列表.

        Args:
            source: 模块源（可选）
            source_type: 源类型

        Returns:
            模块名称列表
        """
        discovered: list[str] = []
        if source:
            try:
                if source_type == "directory":
                    names = self._discover_from_directory(source)
                elif source_type == "package":
                    names = self._package_loader.discover(source)
                else:
                    names = []
                discovered.extend(names)
            except Exception as e:
                logger.warning(f"发现模块失败: {e}")
            # 过滤排除列表
            filtered = [n for n in set(discovered) if n.lower() not in self.exclude_modules]
            return sorted(filtered)

        # 遍历默认目录
        for module_dir in self.module_dirs:
            try:
                names = self._discover_from_directory(module_dir)
                discovered.extend(names)
            except Exception as e:
                logger.warning(f"无法在目录 {module_dir} 中发现模块: {e}")
        # 过滤排除列表
        filtered = [n for n in set(discovered) if n.lower() not in self.exclude_modules]
        return sorted(filtered)

    def get_module(self, name: str) -> ModuleInterface:
        """获取已加载的模块.

        Args:
            name: 模块名称

        Returns:
            模块实例

        Raises:
            ModuleNotFoundException: 模块未找到时抛出
        """
        module = self.registry.get(name)
        if module is None:
            raise ModuleNotFoundException(f"模块未找到: {name}")
        return module

    def unload_module(self, name: str) -> None:
        """卸载模块.

        Args:
            name: 模块名称
        """
        try:
            self.registry.unregister(name)
            logger.info(f"模块已卸载: {name}")
        except ModuleNotFoundException:
            # 模块未加载，忽略错误
            logger.debug(f"尝试卸载未加载的模块: {name}")

    def list_modules(self) -> list[str]:
        """列出所有已加载的模块.

        Returns:
            模块名称列表
        """
        return self.registry.list_modules()

    def is_module_loaded(self, name: str) -> bool:
        """检查模块是否已加载.

        Args:
            name: 模块名称

        Returns:
            是否已加载
        """
        return self.registry.is_loaded(name)

    def list_installed_modules(self) -> list[str]:
        """列出已安装（包含 installed/started/stopped）的模块名称.

        Returns:
            已安装模块名称列表
        """
        names: set[str] = set()
        for st in (ModuleState.INSTALLED, ModuleState.STARTED, ModuleState.STOPPED):
            try:
                names.update(self.registry.list_modules_by_state(st))
            except Exception as e:
                logger.debug(f"列出某状态模块失败: {st} - {e}")
                continue
        return sorted(names)

    def install_module(self, name: str, config: dict[str, Any] | None = None, source: str | None = None) -> None:
        """安装指定模块：必要时自动加载后再安装.

        Args:
            name: 模块名称
            config: 配置字典（可选）
            source: 模块源（可选）
        """
        if not self.registry.is_loaded(name):
            self.load_module(name, source)
        self.registry.install(name, config or {})

    def uninstall_module(self, name: str) -> None:
        """卸载模块（若在运行则先停止由注册表处理）.

        Args:
            name: 模块名称
        """
        self.registry.uninstall(name)

    def start_module(self, name: str) -> None:
        """启动模块.

        Args:
            name: 模块名称
        """
        # 若未加载，尝试加载
        if not self.registry.is_loaded(name):
            self.load_module(name)
        self.registry.start(name)

    def stop_module(self, name: str) -> None:
        """停止模块.

        Args:
            name: 模块名称
        """
        self.registry.stop(name)

    def reload_module(self, name: str) -> None:
        """重载模块.

        Args:
            name: 模块名称
        """
        # 失效缓存
        self._invalidate_directory_cache()
        if not self.registry.is_loaded(name):
            self.load_module(name)
        self.registry.reload(name)

    def start_all_modules(self) -> None:
        """启动所有已安装/已停止的模块."""
        for name in self.list_installed_modules():
            try:
                self.registry.start(name)
            except Exception as e:
                logger.warning(f"启动模块失败: {name} - {e}")

    def stop_all_modules(self) -> None:
        """停止所有运行中的模块."""
        for name in self.registry.list_modules_by_state(ModuleState.STARTED):
            try:
                self.registry.stop(name)
            except Exception as e:
                logger.warning(f"停止模块失败: {name} - {e}")

    def reload_all_modules(self) -> None:
        """重载所有已加载的模块."""
        for name in self.list_modules():
            try:
                self.registry.reload(name)
            except Exception as e:
                logger.warning(f"重载模块失败: {name} - {e}")
