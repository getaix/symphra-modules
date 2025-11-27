"""模块生命周期管理器.

这个模块负责管理模块实例的生命周期（创建、启动、停止、销毁）。
职责：管理模块实例，执行生命周期操作，确保状态转换的正确性。
"""

from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING

from ..core.exceptions import ModuleNotFoundError, ModuleStateError
from ..core.state import ModuleState, is_valid_transition

if TYPE_CHECKING:
    from ..core.module import Module

logger = logging.getLogger(__name__)


class LifecycleManager:
    """模块生命周期管理器.

    职责：
    - 管理模块实例
    - 执行启动/停止操作
    - 验证状态转换
    - 记录性能数据
    - 线程安全
    """

    def __init__(self) -> None:
        """初始化生命周期管理器."""
        # 存储模块实例: {name: instance}
        self._instances: dict[str, Module] = {}
        # 线程锁
        self._lock = threading.RLock()

    def create_instance(self, module_class: type[Module]) -> Module:
        """创建模块实例.

        Args:
            module_class: 模块类

        Returns:
            模块实例
        """
        # 实例化模块（在锁外执行，避免阻塞）
        instance = module_class()

        # 在锁内保存实例和设置状态
        with self._lock:
            # 设置状态为 LOADED（实例已创建）
            instance._state = ModuleState.LOADED
            self._instances[instance.name] = instance

        logger.info(
            f"模块实例已创建: {instance.name} "
            f"(版本: {getattr(module_class, 'version', '0.1.0')}, "
            f"依赖: {getattr(module_class, 'dependencies', [])})"
        )

        return instance

    def get_instance(self, name: str) -> Module | None:
        """获取模块实例.

        Args:
            name: 模块名称

        Returns:
            模块实例，如果不存在返回 None
        """
        with self._lock:
            return self._instances.get(name)

    def has_instance(self, name: str) -> bool:
        """检查模块实例是否存在.

        Args:
            name: 模块名称

        Returns:
            如果实例存在返回 True
        """
        with self._lock:
            return name in self._instances

    def remove_instance(self, name: str) -> None:
        """移除模块实例.

        Args:
            name: 模块名称
        """
        with self._lock:
            if name in self._instances:
                del self._instances[name]
                logger.info(f"模块实例已移除: {name}")

    def start_module(self, name: str) -> None:
        """启动模块.

        Args:
            name: 模块名称

        Raises:
            ModuleNotFoundError: 模块不存在
            ModuleStateError: 状态转换无效
        """
        # 在锁内检查状态和获取实例
        with self._lock:
            instance = self._instances.get(name)
            if not instance:
                raise ModuleNotFoundError(f"模块 '{name}' 未创建实例")

            # 检查状态转换
            if instance.state == ModuleState.STARTED:
                logger.debug(f"模块 '{name}' 已处于启动状态，跳过重复启动")
                return

            if not is_valid_transition(instance.state, ModuleState.STARTED):
                raise ModuleStateError(
                    f"无法启动模块 '{name}'，当前状态: {instance.state.value}",
                    module_name=name,
                    current_state=instance.state.value,
                    expected_state="LOADED/INITIALIZED/INSTALLED",
                )

        # 启动模块（在锁外执行，避免阻塞）
        instance.start()

        # 更新状态（在锁内执行）
        with self._lock:
            instance._state = ModuleState.STARTED

        logger.info(f"模块 '{name}' 已成功启动 (状态: {ModuleState.STARTED.value})")

    async def start_module_async(self, name: str) -> None:
        """异步启动模块.

        Args:
            name: 模块名称

        Raises:
            ModuleNotFoundError: 模块不存在
            ModuleStateError: 状态转换无效
        """
        import asyncio

        # 在线程中获取实例并检查状态（避免阻塞事件循环）
        def _get_instance_and_check() -> tuple[Module, bool]:
            with self._lock:
                instance = self._instances.get(name)
                if not instance:
                    raise ModuleNotFoundError(f"模块 '{name}' 未创建实例")

                # 检查状态
                if instance.state == ModuleState.STARTED:
                    logger.debug(f"模块 '{name}' 已处于启动状态，跳过异步重复启动")
                    return instance, True  # 返回 (实例, 是否已启动)

                if not is_valid_transition(instance.state, ModuleState.STARTED):
                    raise ModuleStateError(
                        f"无法异步启动模块 '{name}'，当前状态: {instance.state.value}",
                        module_name=name,
                        current_state=instance.state.value,
                        expected_state="LOADED/INITIALIZED/INSTALLED",
                    )

                return instance, False

        instance, already_started = await asyncio.to_thread(_get_instance_and_check)
        if already_started:
            return

        # 异步启动模块（在锁外执行）
        from ..core.module import call_module_method

        await call_module_method(instance, "start_async")

        # 在线程中更新状态（避免阻塞事件循环）
        def _update_state() -> None:
            with self._lock:
                instance._state = ModuleState.STARTED

        await asyncio.to_thread(_update_state)

        logger.info(f"模块 '{name}' 已成功异步启动 (状态: {ModuleState.STARTED.value})")

    def bootstrap_module(self, name: str) -> None:
        """Bootstrap 模块（初始化但不启动）.

        Args:
            name: 模块名称

        Raises:
            ModuleNotFoundError: 模块不存在
            ModuleStateError: 状态转换无效
        """
        # 在锁内检查状态和获取实例
        with self._lock:
            instance = self._instances.get(name)
            if not instance:
                raise ModuleNotFoundError(f"模块 '{name}' 未创建实例")

            # 检查状态转换
            if instance.state == ModuleState.INITIALIZED:
                logger.debug(f"模块 '{name}' 已处于初始化状态，跳过重复初始化")
                return

            if not is_valid_transition(instance.state, ModuleState.INITIALIZED):
                raise ModuleStateError(
                    f"无法初始化模块 '{name}'，当前状态: {instance.state.value}",
                    module_name=name,
                    current_state=instance.state.value,
                    expected_state="LOADED/INSTALLED",
                )

        # 执行 bootstrap（在锁外执行，避免阻塞）
        instance.bootstrap()

        # 更新状态（在锁内执行）
        with self._lock:
            instance._state = ModuleState.INITIALIZED

        logger.info(f"模块 '{name}' 已成功初始化 (状态: {ModuleState.INITIALIZED.value})")

    def stop_module(self, name: str) -> None:
        """停止模块.

        Args:
            name: 模块名称

        Raises:
            ModuleNotFoundError: 模块不存在
        """
        # 在锁内检查状态和获取实例
        with self._lock:
            instance = self._instances.get(name)
            if not instance:
                raise ModuleNotFoundError(f"模块 '{name}' 未创建实例")

            # 检查状态
            if instance.state != ModuleState.STARTED:
                logger.debug(
                    f"模块 '{name}' 未处于启动状态 (当前: {instance.state.value})，跳过停止操作"
                )
                return

        # 停止模块（在锁外执行，避免阻塞）
        instance.stop()

        # 更新状态（在锁内执行）
        with self._lock:
            instance._state = ModuleState.STOPPED

        logger.info(f"模块 '{name}' 已成功停止 (状态: {ModuleState.STOPPED.value})")

    async def stop_module_async(self, name: str) -> None:
        """异步停止模块.

        Args:
            name: 模块名称

        Raises:
            ModuleNotFoundError: 模块不存在
        """
        import asyncio

        # 在线程中获取实例并检查状态（避免阻塞事件循环）
        def _get_instance_and_check() -> tuple[Module | None, bool]:
            with self._lock:
                instance = self._instances.get(name)
                if not instance:
                    raise ModuleNotFoundError(f"模块 '{name}' 未创建实例")

                # 检查状态
                if instance.state != ModuleState.STARTED:
                    logger.debug(
                        f"模块 '{name}' 未处于启动状态 (当前: {instance.state.value})，跳过异步停止操作"
                    )
                    return None, False  # 返回 (实例, 是否需要停止)

                return instance, True

        instance, should_stop = await asyncio.to_thread(_get_instance_and_check)
        if not should_stop or instance is None:
            return

        # 异步停止模块（在锁外执行）
        from ..core.module import call_module_method

        await call_module_method(instance, "stop_async")

        # 在线程中更新状态（避免阻塞事件循环）
        def _update_state() -> None:
            with self._lock:
                instance._state = ModuleState.STOPPED

        await asyncio.to_thread(_update_state)

        logger.info(f"模块 '{name}' 已成功异步停止 (状态: {ModuleState.STOPPED.value})")

    def get_all_instances(self) -> dict[str, Module]:
        """获取所有模块实例.

        Returns:
            模块名到实例的映射
        """
        with self._lock:
            return self._instances.copy()
