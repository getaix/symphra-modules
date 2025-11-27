"""模块状态定义.

这个模块定义了模块的完整生命周期状态。
"""

from __future__ import annotations

from enum import Enum


class ModuleState(Enum):
    """模块状态枚举.

    定义了模块在完整生命周期中的所有可能状态。

    生命周期：
    DISCOVERED -> INSTALLED -> INITIALIZED -> LOADED -> STARTED -> STOPPED
                      ↓
                  DISABLED (可以从任何状态进入)
                      ↓
                  UNINSTALLED (终态)
    """

    DISCOVERED = "discovered"  # 已发现，但未安装
    INSTALLED = "installed"  # 已安装，可以使用
    DISABLED = "disabled"  # 已禁用，不会加载
    INITIALIZED = "initialized"  # 已初始化（bootstrap），但未启动
    LOADED = "loaded"  # 已加载，实例已创建
    STARTED = "started"  # 已启动，正在运行
    STOPPED = "stopped"  # 已停止
    UNINSTALLED = "uninstalled"  # 已卸载（终态）


# 状态转换规则（用于验证状态转换的合法性）
VALID_TRANSITIONS: dict[ModuleState, set[ModuleState]] = {
    # 从 DISCOVERED 可以安装
    ModuleState.DISCOVERED: {ModuleState.INSTALLED},
    # 从 INSTALLED 可以初始化、加载、禁用或卸载
    ModuleState.INSTALLED: {
        ModuleState.INITIALIZED,
        ModuleState.LOADED,
        ModuleState.DISABLED,
        ModuleState.UNINSTALLED,
    },
    # 从 DISABLED 可以重新启用或卸载
    ModuleState.DISABLED: {ModuleState.INSTALLED, ModuleState.UNINSTALLED},
    # 从 INITIALIZED 可以启动或禁用
    ModuleState.INITIALIZED: {ModuleState.STARTED, ModuleState.DISABLED},
    # 从 LOADED 可以初始化（bootstrap）、启动、停止或禁用
    ModuleState.LOADED: {
        ModuleState.INITIALIZED,
        ModuleState.STARTED,
        ModuleState.STOPPED,
        ModuleState.DISABLED,
    },
    # 从 STARTED 可以停止或禁用
    ModuleState.STARTED: {ModuleState.STOPPED, ModuleState.DISABLED},
    # 从 STOPPED 可以重新启动或禁用
    ModuleState.STOPPED: {ModuleState.STARTED, ModuleState.DISABLED},
    # UNINSTALLED 是终态，不能转换到其他状态
    ModuleState.UNINSTALLED: set(),
}


def is_valid_transition(from_state: ModuleState, to_state: ModuleState) -> bool:
    """检查状态转换是否有效.

    Args:
        from_state: 当前状态
        to_state: 目标状态

    Returns:
        如果转换有效返回 True，否则返回 False
    """
    return to_state in VALID_TRANSITIONS.get(from_state, set())


def get_state_description(state: ModuleState) -> str:
    """获取状态的描述.

    Args:
        state: 模块状态

    Returns:
        状态描述文本
    """
    descriptions = {
        ModuleState.DISCOVERED: "已发现，等待安装",
        ModuleState.INSTALLED: "已安装，可以使用",
        ModuleState.DISABLED: "已禁用，不会加载",
        ModuleState.INITIALIZED: "已初始化，等待启动",
        ModuleState.LOADED: "已加载，实例已创建",
        ModuleState.STARTED: "已启动，正在运行",
        ModuleState.STOPPED: "已停止",
        ModuleState.UNINSTALLED: "已卸载",
    }
    return descriptions.get(state, "未知状态")
