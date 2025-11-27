"""模块管理器.

这个模块实现了主要的 ModuleManager 类，作为所有组件的协调者。
职责：协调加载器、依赖解析器和生命周期管理器，提供简洁的公共 API。
本类是线程安全的，所有修改共享状态的操作都使用锁保护。
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from typing import Any

from .core import Module, ModuleState, StateStore
from .core.exceptions import CircularDependencyError, ModuleNotFoundError, ModuleStateError
from .dependency import DependencyResolver
from .lifecycle import LifecycleManager
from .loader import FileSystemLoader, ModuleLoader

logger = logging.getLogger(__name__)


class ModuleManager:
    """模块管理器 - 优雅的API设计.

    ModuleManager 是整个框架的门面（Facade），协调各个组件：
    - ModuleLoader: 负责发现和加载模块类
    - DependencyResolver: 负责解析依赖关系
    - LifecycleManager: 负责管理模块实例生命周期

    Example:
        >>> manager = ModuleManager("./modules")
        >>> manager.load("user")  # 自动加载依赖
        >>> manager.start("user")  # 启动模块
        >>> manager.stop("user")   # 停止模块

        # 异步使用
        >>> await manager.load_async("user")
        >>> await manager.start_async("user")

        # 上下文管理器
        >>> with ModuleManager("./modules") as manager:
        ...     manager.load("user")
        ...     manager.start("user")
    """

    def __init__(
        self,
        module_dir: str | Path | list[str] | list[Path] = "modules",
        loader: ModuleLoader | None = None,
        ignored_modules: set[str] | None = None,
        state_store: StateStore | None = None,
    ) -> None:
        """初始化模块管理器.

        Args:
            module_dir: 模块目录路径或路径列表
            loader: 自定义加载器（可选，默认使用 FileSystemLoader）
            ignored_modules: 忽略的模块名称集合（黑名单），如果提供了 state_store，将从存储加载
            state_store: 状态持久化存储（可选，用于持久化模块状态和黑名单）
        """
        # 规范化模块目录
        if isinstance(module_dir, (str, Path)):
            directories = [Path(module_dir)]
        else:
            directories = [Path(d) for d in module_dir]

        # 初始化组件
        self._loader = loader or FileSystemLoader(directories)
        self._resolver = DependencyResolver()
        self._lifecycle = LifecycleManager()

        # 状态持久化存储（可选）
        self._state_store = state_store

        # 线程锁，保护共享状态
        self._lock = threading.RLock()

        # 忽略的模块（黑名单）
        # 如果提供了 state_store，从存储加载忽略列表
        if self._state_store:
            self._ignored_modules = self._state_store.load_ignored_modules()
            # 如果手动提供了 ignored_modules，合并到加载的列表中
            if ignored_modules:
                self._ignored_modules.update(ignored_modules)
                self._state_store.save_ignored_modules(self._ignored_modules)
        else:
            self._ignored_modules = ignored_modules or set()

        # 发现模块并过滤掉被忽略的
        all_modules = self._loader.discover()
        self._available_modules = {
            name: cls for name, cls in all_modules.items() if name not in self._ignored_modules
        }

        ignored_count = len(all_modules) - len(self._available_modules)
        if ignored_count > 0:
            logger.info(
                f"模块管理器已初始化: 发现 {len(all_modules)} 个模块，"
                f"可用 {len(self._available_modules)} 个，忽略 {ignored_count} 个"
            )
        else:
            logger.info(f"模块管理器已初始化: 发现 {len(self._available_modules)} 个可用模块")

    def __enter__(self) -> ModuleManager:
        """上下文管理器入口."""
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """上下文管理器出口."""
        try:
            logger.info("退出上下文管理器，正在停止所有模块...")
            self.stop_all()
            logger.info("所有模块已安全停止")
        except Exception as e:
            logger.error(f"退出上下文管理器时停止模块失败: {type(e).__name__}: {e}")

    # ========================================================================
    # 核心 API
    # ========================================================================

    def _validate_module_name(self, name: str) -> None:
        """验证模块名称的合法性.

        Args:
            name: 模块名称

        Raises:
            ValueError: 模块名称无效
        """
        if not name or not isinstance(name, str):
            raise ValueError("模块名称不能为空且必须是字符串")
        if not name.strip():
            raise ValueError("模块名称不能为空白字符")
        # 检查是否包含非法字符（仅允许字母、数字、下划线、连字符）
        if not all(c.isalnum() or c in ("_", "-") for c in name):
            raise ValueError(f"模块名称 '{name}' 包含非法字符，仅允许字母、数字、下划线和连字符")

    def load(self, name: str, force: bool = False) -> Module:
        """加载模块（自动解析并加载所有依赖）.

        Args:
            name: 模块名称
            force: 是否强制重新加载

        Returns:
            模块实例

        Raises:
            ValueError: 模块名称无效
            ModuleNotFoundError: 模块不存在
            CircularDependencyError: 循环依赖
            DependencyError: 依赖缺失
        """
        # 输入验证
        self._validate_module_name(name)

        # 如果不是强制重新加载且已加载，则直接返回（优化：只调用一次 get_instance）
        if not force:
            instance = self._lifecycle.get_instance(name)
            if instance:
                return instance

        # 解析依赖，获取加载顺序
        try:
            load_order = self._resolver.resolve(name, self._available_modules)
        except CircularDependencyError:
            raise

        # 按顺序加载模块
        for module_name in load_order:
            if not self._lifecycle.has_instance(module_name) or force:
                module_class = self._available_modules[module_name]
                self._lifecycle.create_instance(module_class)

        instance = self._lifecycle.get_instance(name)
        if not instance:
            raise ModuleNotFoundError(f"加载模块 '{name}' 失败")

        return instance

    async def load_async(self, name: str, force: bool = False) -> Module:
        """异步加载模块.

        Args:
            name: 模块名称
            force: 是否强制重新加载

        Returns:
            模块实例
        """
        import asyncio

        return await asyncio.to_thread(self.load, name, force)

    def start(self, name: str) -> None:
        """启动模块（自动启动所有依赖）.

        Args:
            name: 模块名称

        Raises:
            ValueError: 模块名称无效
            ModuleNotFoundError: 模块不存在
        """
        # 输入验证
        self._validate_module_name(name)

        # 检查模块是否已加载（优化：只调用一次 get_instance）
        target_instance = self._lifecycle.get_instance(name)
        if not target_instance:
            raise ModuleNotFoundError(f"模块 '{name}' 未加载，请先调用 load() 方法")

        # 获取启动顺序（包括依赖）
        try:
            all_modules = self._resolver.get_graph().topological_sort()
            # 获取所有已加载的实例（优化：批量获取，减少锁操作）
            all_instances = self._lifecycle.get_all_instances()
            # 只启动已加载的模块，直到目标模块
            modules_to_start = []
            for module_name in all_modules:
                if module_name in all_instances:
                    modules_to_start.append(module_name)
                if module_name == name:
                    break
        except Exception:
            # 如果获取失败，只启动当前模块
            modules_to_start = [name]
            all_instances = {name: target_instance}

        # 按顺序启动
        for module_name in modules_to_start:
            instance = all_instances.get(module_name)
            if instance and instance.state != ModuleState.STARTED:
                self._lifecycle.start_module(module_name)

    async def start_async(self, name: str) -> None:
        """异步启动模块.

        Args:
            name: 模块名称
        """
        import asyncio

        # 在线程中检查实例是否存在（避免阻塞事件循环）
        has_instance = await asyncio.to_thread(self._lifecycle.has_instance, name)
        if not has_instance:
            raise ModuleNotFoundError(f"模块 '{name}' 未加载，请先调用 load_async() 方法")

        # 在线程中获取启动顺序
        def _get_start_order() -> list[str]:
            try:
                all_modules = self._resolver.get_graph().topological_sort()
                modules_to_start = []
                for module_name in all_modules:
                    if self._lifecycle.has_instance(module_name):
                        modules_to_start.append(module_name)
                    if module_name == name:
                        break
                return modules_to_start
            except Exception:
                return [name]

        modules_to_start = await asyncio.to_thread(_get_start_order)

        # 按顺序异步启动
        for module_name in modules_to_start:
            # 在线程中获取实例并检查状态
            def _check_should_start(name: str = module_name) -> bool:
                instance = self._lifecycle.get_instance(name)
                return instance is not None and instance.state != ModuleState.STARTED

            should_start = await asyncio.to_thread(_check_should_start)
            if should_start:
                await self._lifecycle.start_module_async(module_name)

    def stop(self, name: str) -> None:
        """停止模块.

        Args:
            name: 模块名称
        """
        if not self._lifecycle.has_instance(name):
            raise ModuleNotFoundError(f"模块 '{name}' 未加载")

        self._lifecycle.stop_module(name)

    async def stop_async(self, name: str) -> None:
        """异步停止模块.

        Args:
            name: 模块名称
        """
        import asyncio

        # 在线程中检查实例是否存在（避免阻塞事件循环）
        has_instance = await asyncio.to_thread(self._lifecycle.has_instance, name)
        if not has_instance:
            raise ModuleNotFoundError(f"模块 '{name}' 未加载")

        await self._lifecycle.stop_module_async(name)

    def unload(self, name: str) -> None:
        """卸载模块.

        Args:
            name: 模块名称
        """
        if not self._lifecycle.has_instance(name):
            raise ModuleNotFoundError(f"模块 '{name}' 未加载")

        # 先停止模块
        instance = self._lifecycle.get_instance(name)
        if instance and instance.state == ModuleState.STARTED:
            try:
                self.stop(name)
            except Exception as e:
                logger.warning(f"停止模块 {name} 失败: {e}")

        # 移除实例
        self._lifecycle.remove_instance(name)

    # ========================================================================
    # 批量操作 API
    # ========================================================================

    def load_all(self, force: bool = False) -> dict[str, Module]:
        """加载所有模块.

        Args:
            force: 是否强制重新加载

        Returns:
            模块名到模块实例的映射
        """
        logger.info(f"开始批量加载 {len(self._available_modules)} 个模块...")
        modules = {}
        success_count = 0
        error_count = 0

        for name in self._available_modules:
            try:
                modules[name] = self.load(name, force)
                success_count += 1
            except Exception as e:
                error_count += 1
                logger.error(f"加载模块 '{name}' 失败: {type(e).__name__}: {e}")

        logger.info(f"批量加载完成: 成功 {success_count} 个，失败 {error_count} 个")
        return modules

    async def load_all_async(self, force: bool = False) -> dict[str, Module]:
        """异步加载所有模块.

        Args:
            force: 是否强制重新加载

        Returns:
            模块名到模块实例的映射
        """
        import asyncio

        return await asyncio.to_thread(self.load_all, force)

    def start_all(self) -> None:
        """启动所有已加载的模块."""
        # 获取所有已加载的实例（优化：批量获取，减少锁操作）
        all_instances = self._lifecycle.get_all_instances()
        logger.info(f"开始批量启动 {len(all_instances)} 个已加载的模块...")

        try:
            # 获取拓扑排序顺序
            all_modules = self._resolver.get_graph().topological_sort()
        except Exception:
            # 如果失败，使用实例顺序
            all_modules = list(all_instances.keys())
            logger.warning("依赖图拓扑排序失败，使用模块加载顺序启动")

        success_count = 0
        error_count = 0

        # 按顺序启动
        for name in all_modules:
            instance = all_instances.get(name)
            if instance:
                try:
                    if instance.state != ModuleState.STARTED:
                        self._lifecycle.start_module(name)
                        success_count += 1
                except Exception as e:
                    error_count += 1
                    logger.error(f"启动模块 '{name}' 失败: {type(e).__name__}: {e}")

        logger.info(f"批量启动完成: 成功 {success_count} 个，失败 {error_count} 个")

    async def start_all_async(self) -> None:
        """异步启动所有已加载的模块."""
        import asyncio

        # 在线程中获取启动顺序
        def _get_start_order() -> list[str]:
            try:
                all_modules = self._resolver.get_graph().topological_sort()
            except Exception:
                all_modules = list(self._lifecycle.get_all_instances().keys())
            return all_modules

        all_modules = await asyncio.to_thread(_get_start_order)

        for name in all_modules:
            # 在线程中检查实例是否存在
            has_instance = await asyncio.to_thread(self._lifecycle.has_instance, name)
            if has_instance:
                try:
                    # 在线程中获取实例并检查状态
                    def _check_should_start(module_name: str = name) -> bool:
                        instance = self._lifecycle.get_instance(module_name)
                        return instance is not None and instance.state != ModuleState.STARTED

                    should_start = await asyncio.to_thread(_check_should_start)
                    if should_start:
                        await self._lifecycle.start_module_async(name)
                except Exception as e:
                    logger.error(f"异步启动模块 {name} 失败: {e}")

    def stop_all(self) -> None:
        """停止所有已启动的模块（按依赖反序）."""
        # 获取所有已加载的实例（优化：批量获取，减少锁操作）
        all_instances = self._lifecycle.get_all_instances()
        logger.info(f"开始批量停止 {len(all_instances)} 个模块...")

        try:
            all_modules = self._resolver.get_graph().topological_sort()
            stop_order = list(reversed(all_modules))
        except Exception:
            stop_order = list(reversed(list(all_instances.keys())))
            logger.warning("依赖图拓扑排序失败，使用模块逆序停止")

        success_count = 0
        error_count = 0

        for name in stop_order:
            if name in all_instances:
                try:
                    self._lifecycle.stop_module(name)
                    success_count += 1
                except Exception as e:
                    error_count += 1
                    logger.error(f"停止模块 '{name}' 失败: {type(e).__name__}: {e}")

        logger.info(f"批量停止完成: 成功 {success_count} 个，失败 {error_count} 个")

    async def stop_all_async(self) -> None:
        """异步停止所有已启动的模块."""
        import asyncio

        # 在线程中获取停止顺序
        def _get_stop_order() -> list[str]:
            try:
                all_modules = self._resolver.get_graph().topological_sort()
                stop_order = list(reversed(all_modules))
            except Exception:
                instances = self._lifecycle.get_all_instances()
                stop_order = list(reversed(list(instances.keys())))
            return stop_order

        stop_order = await asyncio.to_thread(_get_stop_order)

        for name in stop_order:
            # 在线程中检查实例是否存在
            has_instance = await asyncio.to_thread(self._lifecycle.has_instance, name)
            if has_instance:
                try:
                    await self._lifecycle.stop_module_async(name)
                except Exception as e:
                    logger.error(f"异步停止模块 {name} 失败: {e}")

    # ========================================================================
    # 查询 API
    # ========================================================================

    def list_modules(self) -> list[str]:
        """列出所有可用模块（线程安全）.

        Returns:
            模块名称列表（已排序）
        """
        with self._lock:
            return sorted(self._available_modules.keys())

    def list_loaded_modules(self) -> list[str]:
        """列出所有已加载的模块.

        Returns:
            已加载模块名称列表（已排序）
        """
        return sorted(self._lifecycle.get_all_instances().keys())

    def list_started_modules(self) -> list[str]:
        """列出所有已启动的模块.

        Returns:
            已启动模块名称列表（已排序）
        """
        instances = self._lifecycle.get_all_instances()
        return sorted(
            name for name, module in instances.items() if module.state == ModuleState.STARTED
        )

    def get_module(self, name: str) -> Module | None:
        """获取已加载的模块实例.

        Args:
            name: 模块名称

        Returns:
            模块实例，未加载则返回 None
        """
        return self._lifecycle.get_instance(name)

    def get_module_info(self, name: str) -> dict[str, Any]:
        """获取模块信息.

        Args:
            name: 模块名称

        Returns:
            包含模块信息的字典

        Raises:
            ModuleNotFoundError: 模块不存在
        """
        if name not in self._available_modules:
            raise ModuleNotFoundError(f"模块不存在: {name}")

        module_class = self._available_modules[name]
        instance = self._lifecycle.get_instance(name)

        from .core.module import is_async_module

        info = {
            "name": name,
            "version": getattr(module_class, "version", "0.1.0"),
            "dependencies": getattr(module_class, "dependencies", []),
            "loaded": instance is not None,
            "state": instance.state.value if instance else None,
            "loaded_at": instance.loaded_at if instance else None,
            "is_async": is_async_module(instance) if instance else False,
        }

        return info

    # ========================================================================
    # 管理 API
    # ========================================================================

    def rediscover(self) -> None:
        """重新发现模块（线程安全）.

        重新扫描模块目录，更新模块类列表。
        适用于热重载等场景。
        """
        with self._lock:
            old_count = len(self._available_modules)
            all_modules = self._loader.discover()
            # 过滤掉被忽略的模块
            self._available_modules = {
                name: cls for name, cls in all_modules.items() if name not in self._ignored_modules
            }
            new_count = len(self._available_modules)
            logger.info(f"重新发现模块: {old_count} -> {new_count}")

    def bootstrap(self, name: str) -> None:
        """Bootstrap 模块（初始化但不启动）.

        Args:
            name: 模块名称

        Raises:
            ModuleNotFoundError: 模块不存在或未加载
        """
        if not self._lifecycle.has_instance(name):
            raise ModuleNotFoundError(f"模块 '{name}' 未加载，请先调用 load() 方法")

        self._lifecycle.bootstrap_module(name)

        # 持久化状态
        self._save_module_state(name)

    def _save_module_state(self, name: str) -> None:
        """保存模块状态到持久化存储.

        Args:
            name: 模块名称
        """
        if self._state_store:
            instance = self._lifecycle.get_instance(name)
            if instance:
                self._state_store.save_state(name, instance.state)

    def ignore_module(self, name: str) -> None:
        """忽略模块（加入黑名单）（线程安全）.

        Args:
            name: 模块名称
        """
        with self._lock:
            self._ignored_modules.add(name)
            # 如果模块已经在可用列表中，移除它
            if name in self._available_modules:
                del self._available_modules[name]
                logger.info(f"模块 '{name}' 已加入黑名单")

            # 持久化黑名单
            if self._state_store:
                self._state_store.save_ignored_modules(self._ignored_modules)

    def unignore_module(self, name: str) -> None:
        """取消忽略模块（从黑名单移除）（线程安全）.

        Args:
            name: 模块名称
        """
        with self._lock:
            if name in self._ignored_modules:
                self._ignored_modules.discard(name)
                logger.info(f"模块 '{name}' 已从黑名单移除")

                # 持久化黑名单
                if self._state_store:
                    self._state_store.save_ignored_modules(self._ignored_modules)

        # 重新发现该模块（在锁外调用，因为 rediscover 自己会加锁）
        self.rediscover()

    def install(self, name: str) -> None:
        """安装模块（状态: DISCOVERED -> INSTALLED）.

        注意：这个方法主要用于状态管理。
        实际的模块实例创建在 load() 方法中进行。

        Args:
            name: 模块名称

        Raises:
            ModuleNotFoundError: 模块不存在
        """
        if name not in self._available_modules:
            raise ModuleNotFoundError(f"模块 '{name}' 不存在，无法安装")

        # 如果已经有实例，检查状态
        instance = self._lifecycle.get_instance(name)
        if instance:
            from .core.state import is_valid_transition

            if not is_valid_transition(instance.state, ModuleState.INSTALLED):
                raise ModuleStateError(f"无法安装模块 '{name}'，当前状态: {instance.state.value}")
            instance._state = ModuleState.INSTALLED
            logger.info(f"模块 '{name}' 已安装")

            # 持久化状态
            self._save_module_state(name)
        else:
            # 如果没有实例，创建实例（状态会自动设为 INSTALLED）
            self.load(name)

    def uninstall(self, name: str) -> None:
        """卸载模块（状态 -> UNINSTALLED，终态）.

        Args:
            name: 模块名称

        Raises:
            ModuleNotFoundError: 模块不存在或未加载
        """
        if not self._lifecycle.has_instance(name):
            raise ModuleNotFoundError(f"模块 '{name}' 未加载，无法卸载")

        instance = self._lifecycle.get_instance(name)
        if not instance:
            raise ModuleNotFoundError(f"模块 '{name}' 实例不存在")

        # 如果正在运行，先停止
        if instance.state == ModuleState.STARTED:
            try:
                self.stop(name)
            except Exception as e:
                logger.warning(f"停止模块 {name} 失败: {e}")

        # 设置为卸载状态（终态）
        instance._state = ModuleState.UNINSTALLED

        # 持久化状态
        self._save_module_state(name)

        # 移除实例
        self._lifecycle.remove_instance(name)
        logger.info(f"模块 '{name}' 已卸载")

    def enable(self, name: str) -> None:
        """启用模块（状态: DISABLED -> INSTALLED）.

        Args:
            name: 模块名称

        Raises:
            ModuleNotFoundError: 模块不存在或未加载
            ModuleStateError: 状态转换无效
        """
        if not self._lifecycle.has_instance(name):
            raise ModuleNotFoundError(f"模块 '{name}' 未加载，请先调用 load() 方法")

        instance = self._lifecycle.get_instance(name)
        if not instance:
            raise ModuleNotFoundError(f"模块 '{name}' 实例不存在")

        from .core.state import is_valid_transition

        if instance.state != ModuleState.DISABLED:
            logger.warning(f"模块 '{name}' 不是禁用状态，当前状态: {instance.state.value}")
            return

        if not is_valid_transition(instance.state, ModuleState.INSTALLED):
            raise ModuleStateError(f"无法启用模块 '{name}'，当前状态: {instance.state.value}")

        instance._state = ModuleState.INSTALLED
        logger.info(f"模块 '{name}' 已启用")

        # 持久化状态
        self._save_module_state(name)

    def disable(self, name: str) -> None:
        """禁用模块（状态 -> DISABLED）.

        Args:
            name: 模块名称

        Raises:
            ModuleNotFoundError: 模块不存在或未加载
        """
        if not self._lifecycle.has_instance(name):
            raise ModuleNotFoundError(f"模块 '{name}' 未加载")

        instance = self._lifecycle.get_instance(name)
        if not instance:
            raise ModuleNotFoundError(f"模块 '{name}' 实例不存在")

        # 如果正在运行，先停止
        if instance.state == ModuleState.STARTED:
            try:
                self.stop(name)
            except Exception as e:
                logger.warning(f"停止模块 {name} 失败: {e}")

        # 设置为禁用状态
        instance._state = ModuleState.DISABLED
        logger.info(f"模块 '{name}' 已禁用")

        # 持久化状态
        self._save_module_state(name)
