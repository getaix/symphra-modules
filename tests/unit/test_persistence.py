"""测试状态持久化功能."""

import json
from pathlib import Path

from symphra_modules.core import (
    FileStateStore,
    MemoryStateStore,
    ModuleState,
)


class TestMemoryStateStore:
    """测试内存状态存储."""

    def test_save_and_load_state(self) -> None:
        """测试保存和加载模块状态."""
        store = MemoryStateStore()

        # 保存状态
        store.save_state("test_module", ModuleState.STARTED)

        # 加载状态
        state = store.load_state("test_module")
        assert state == ModuleState.STARTED

    def test_load_nonexistent_state(self) -> None:
        """测试加载不存在的模块状态."""
        store = MemoryStateStore()

        # 加载不存在的状态应返回 None
        state = store.load_state("nonexistent")
        assert state is None

    def test_save_and_load_ignored_modules(self) -> None:
        """测试保存和加载忽略的模块列表."""
        store = MemoryStateStore()

        # 保存忽略列表
        ignored = {"module1", "module2", "module3"}
        store.save_ignored_modules(ignored)

        # 加载忽略列表
        loaded = store.load_ignored_modules()
        assert loaded == ignored

    def test_update_state(self) -> None:
        """测试更新已存在的状态."""
        store = MemoryStateStore()

        # 初始状态
        store.save_state("test_module", ModuleState.LOADED)
        assert store.load_state("test_module") == ModuleState.LOADED

        # 更新状态
        store.save_state("test_module", ModuleState.STARTED)
        assert store.load_state("test_module") == ModuleState.STARTED


class TestFileStateStore:
    """测试文件状态存储."""

    def test_save_and_load_state(self, tmp_path: Path) -> None:
        """测试保存和加载模块状态到文件."""
        state_file = tmp_path / "test_states.json"
        store = FileStateStore(state_file)

        # 保存状态
        store.save_state("test_module", ModuleState.STARTED)

        # 加载状态
        state = store.load_state("test_module")
        assert state == ModuleState.STARTED

        # 验证文件存在
        assert state_file.exists()

    def test_load_nonexistent_state(self, tmp_path: Path) -> None:
        """测试加载不存在的模块状态."""
        state_file = tmp_path / "test_states.json"
        store = FileStateStore(state_file)

        # 加载不存在的状态应返回 None
        state = store.load_state("nonexistent")
        assert state is None

    def test_save_and_load_ignored_modules(self, tmp_path: Path) -> None:
        """测试保存和加载忽略的模块列表到文件."""
        state_file = tmp_path / "test_states.json"
        store = FileStateStore(state_file)

        # 保存忽略列表
        ignored = {"module1", "module2", "module3"}
        store.save_ignored_modules(ignored)

        # 加载忽略列表
        loaded = store.load_ignored_modules()
        assert loaded == ignored

    def test_persistence_across_instances(self, tmp_path: Path) -> None:
        """测试多个存储实例间的数据持久化."""
        state_file = tmp_path / "test_states.json"

        # 第一个实例保存数据
        store1 = FileStateStore(state_file)
        store1.save_state("module1", ModuleState.STARTED)
        store1.save_ignored_modules({"ignored1", "ignored2"})

        # 第二个实例加载数据
        store2 = FileStateStore(state_file)
        assert store2.load_state("module1") == ModuleState.STARTED
        assert store2.load_ignored_modules() == {"ignored1", "ignored2"}

    def test_file_content_format(self, tmp_path: Path) -> None:
        """测试文件内容格式正确性."""
        state_file = tmp_path / "test_states.json"
        store = FileStateStore(state_file)

        # 保存一些数据
        store.save_state("module1", ModuleState.STARTED)
        store.save_ignored_modules({"ignored1"})

        # 读取并验证JSON格式
        with open(state_file, encoding="utf-8") as f:
            data = json.load(f)

        assert "states" in data
        assert "ignored_modules" in data
        assert data["states"]["module1"] == "started"
        assert "ignored1" in data["ignored_modules"]

    def test_create_parent_directory(self, tmp_path: Path) -> None:
        """测试自动创建父目录."""
        state_file = tmp_path / "subdir" / "test_states.json"
        store = FileStateStore(state_file)

        # 保存数据应自动创建父目录
        store.save_state("test_module", ModuleState.LOADED)

        assert state_file.exists()
        assert state_file.parent.exists()

    def test_update_existing_state(self, tmp_path: Path) -> None:
        """测试更新已存在的状态."""
        state_file = tmp_path / "test_states.json"
        store = FileStateStore(state_file)

        # 初始状态
        store.save_state("test_module", ModuleState.LOADED)
        assert store.load_state("test_module") == ModuleState.LOADED

        # 更新状态
        store.save_state("test_module", ModuleState.STARTED)
        assert store.load_state("test_module") == ModuleState.STARTED

        # 验证文件中的数据
        store2 = FileStateStore(state_file)
        assert store2.load_state("test_module") == ModuleState.STARTED

    def test_multiple_modules_state(self, tmp_path: Path) -> None:
        """测试保存多个模块的状态."""
        state_file = tmp_path / "test_states.json"
        store = FileStateStore(state_file)

        # 保存多个模块状态
        store.save_state("module1", ModuleState.LOADED)
        store.save_state("module2", ModuleState.STARTED)
        store.save_state("module3", ModuleState.STOPPED)

        # 验证所有状态
        assert store.load_state("module1") == ModuleState.LOADED
        assert store.load_state("module2") == ModuleState.STARTED
        assert store.load_state("module3") == ModuleState.STOPPED

    def test_delete_state(self, tmp_path: Path) -> None:
        """测试删除模块状态."""
        state_file = tmp_path / "test_states.json"
        store = FileStateStore(state_file)

        # 保存状态
        store.save_state("test_module", ModuleState.STARTED)
        assert store.load_state("test_module") == ModuleState.STARTED

        # 删除状态
        store.delete_state("test_module")
        assert store.load_state("test_module") is None

    def test_delete_nonexistent_state(self, tmp_path: Path) -> None:
        """测试删除不存在的状态（应该不抛异常）."""
        state_file = tmp_path / "test_states.json"
        store = FileStateStore(state_file)

        # 删除不存在的状态不应该抛异常
        store.delete_state("nonexistent")

    def test_list_states(self, tmp_path: Path) -> None:
        """测试列出所有模块状态."""
        state_file = tmp_path / "test_states.json"
        store = FileStateStore(state_file)

        # 保存多个状态
        store.save_state("module1", ModuleState.LOADED)
        store.save_state("module2", ModuleState.STARTED)
        store.save_state("module3", ModuleState.STOPPED)

        # 列出所有状态
        states = store.list_states()
        assert len(states) == 3
        assert states["module1"] == ModuleState.LOADED
        assert states["module2"] == ModuleState.STARTED
        assert states["module3"] == ModuleState.STOPPED

    def test_corrupted_file_recovery(self, tmp_path: Path) -> None:
        """测试损坏文件的恢复."""
        state_file = tmp_path / "test_states.json"

        # 创建损坏的JSON文件
        with open(state_file, "w", encoding="utf-8") as f:
            f.write("{ invalid json }")

        # 应该能够正常创建store（会自动恢复）
        store = FileStateStore(state_file)

        # 应该返回空数据
        assert store.load_state("any_module") is None
        assert store.load_ignored_modules() == set()

    def test_invalid_state_value(self, tmp_path: Path) -> None:
        """测试加载无效状态值."""
        state_file = tmp_path / "test_states.json"

        # 手动创建包含无效状态值的文件
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump({"states": {"module1": "invalid_state"}, "ignored_modules": []}, f)

        store = FileStateStore(state_file)
        # 加载无效状态应返回 None
        assert store.load_state("module1") is None

    def test_list_states_with_invalid_values(self, tmp_path: Path) -> None:
        """测试列出状态时跳过无效值."""
        state_file = tmp_path / "test_states.json"

        # 创建包含有效和无效状态的文件
        with open(state_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "states": {
                        "module1": "started",
                        "module2": "invalid_state",
                        "module3": "stopped",
                    },
                    "ignored_modules": [],
                },
                f,
            )

        store = FileStateStore(state_file)
        states = store.list_states()

        # 应该只包含有效状态
        assert len(states) == 2
        assert "module1" in states
        assert "module3" in states
        assert "module2" not in states

    def test_empty_ignored_modules(self, tmp_path: Path) -> None:
        """测试空的忽略模块列表."""
        state_file = tmp_path / "test_states.json"
        store = FileStateStore(state_file)

        # 保存空列表
        store.save_ignored_modules(set())

        # 加载应该返回空集合
        loaded = store.load_ignored_modules()
        assert loaded == set()
        assert len(loaded) == 0
