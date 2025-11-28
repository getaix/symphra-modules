"""模块状态机单元测试.

测试模块状态转换、状态验证等功能。
"""

import pytest

from symphra_modules import ModuleState
from symphra_modules.core.state import get_state_description, is_valid_transition, VALID_TRANSITIONS


class TestStateTransitions:
    """测试状态转换."""

    def test_get_state_description(self) -> None:
        """测试获取状态描述."""
        desc = get_state_description(ModuleState.LOADED)
        assert "加载" in desc

        desc = get_state_description(ModuleState.STARTED)
        assert "启动" in desc

    def test_all_state_transitions(self) -> None:
        """测试所有有效的状态转换."""
        # 验证一些基本转换
        assert is_valid_transition(ModuleState.LOADED, ModuleState.STARTED)
        assert is_valid_transition(ModuleState.STARTED, ModuleState.STOPPED)
        assert is_valid_transition(ModuleState.STOPPED, ModuleState.STARTED)
        assert is_valid_transition(ModuleState.LOADED, ModuleState.DISABLED)

        # 验证无效转换
        assert not is_valid_transition(ModuleState.UNINSTALLED, ModuleState.LOADED)
        assert not is_valid_transition(ModuleState.STOPPED, ModuleState.LOADED)

    def test_invalid_state_transition(self) -> None:
        """测试无效状态转换."""
        # STOPPED -> LOADED 是无效的
        assert not is_valid_transition(ModuleState.STOPPED, ModuleState.LOADED)

        # LOADED -> STARTED 是有效的
        assert is_valid_transition(ModuleState.LOADED, ModuleState.STARTED)

    def test_terminal_state(self) -> None:
        """测试终态（UNINSTALLED）."""
        # UNINSTALLED 是终态，不能转换到其他状态
        for state in ModuleState:
            if state != ModuleState.UNINSTALLED:
                assert not is_valid_transition(ModuleState.UNINSTALLED, state)

    def test_disabled_state_transitions(self) -> None:
        """测试DISABLED状态的转换."""
        # 可以从多个状态转换到DISABLED
        assert is_valid_transition(ModuleState.LOADED, ModuleState.DISABLED)
        assert is_valid_transition(ModuleState.STOPPED, ModuleState.DISABLED)
        assert is_valid_transition(ModuleState.INSTALLED, ModuleState.DISABLED)

        # 从DISABLED可以转换到INSTALLED
        assert is_valid_transition(ModuleState.DISABLED, ModuleState.INSTALLED)

    def test_state_transitions_completeness(self) -> None:
        """测试状态转换规则的完整性."""
        # 验证所有状态都在转换表中
        for state in ModuleState:
            assert state in VALID_TRANSITIONS

        # 验证所有转换目标也是有效状态
        for source, targets in VALID_TRANSITIONS.items():
            for target in targets:
                assert isinstance(target, ModuleState)

    def test_discovered_to_installed(self) -> None:
        """测试DISCOVERED到INSTALLED的转换."""
        assert is_valid_transition(ModuleState.DISCOVERED, ModuleState.INSTALLED)

    def test_installed_to_initialized(self) -> None:
        """测试INSTALLED到INITIALIZED的转换."""
        assert is_valid_transition(ModuleState.INSTALLED, ModuleState.INITIALIZED)

    def test_initialized_to_started(self) -> None:
        """测试INITIALIZED到STARTED的转换."""
        # INITIALIZED 可以直接启动
        assert is_valid_transition(ModuleState.INITIALIZED, ModuleState.STARTED)

    def test_loaded_to_started(self) -> None:
        """测试LOADED到STARTED的转换."""
        assert is_valid_transition(ModuleState.LOADED, ModuleState.STARTED)

    def test_started_to_stopped(self) -> None:
        """测试STARTED到STOPPED的转换."""
        assert is_valid_transition(ModuleState.STARTED, ModuleState.STOPPED)

    def test_stopped_to_started(self) -> None:
        """测试STOPPED到STARTED的循环."""
        # 可以重新启动已停止的模块
        assert is_valid_transition(ModuleState.STOPPED, ModuleState.STARTED)

    def test_any_to_disabled(self) -> None:
        """测试从任何状态转换到DISABLED."""
        valid_sources = [
            ModuleState.LOADED,
            ModuleState.STOPPED,
            ModuleState.INSTALLED,
            ModuleState.INITIALIZED,
        ]

        for state in valid_sources:
            assert is_valid_transition(state, ModuleState.DISABLED)

    def test_any_to_uninstalled(self) -> None:
        """测试从有效状态转换到UNINSTALLED（终态）."""
        # 只有INSTALLED和DISABLED可以转换到UNINSTALLED
        valid_sources = [
            ModuleState.INSTALLED,
            ModuleState.DISABLED,
        ]

        for state in valid_sources:
            assert is_valid_transition(state, ModuleState.UNINSTALLED)

        # 其他状态不能直接转换到UNINSTALLED
        invalid_sources = [
            ModuleState.LOADED,
            ModuleState.STARTED,
            ModuleState.STOPPED,
        ]

        for state in invalid_sources:
            assert not is_valid_transition(state, ModuleState.UNINSTALLED)
