"""模块监控功能集成测试."""

import tempfile
from pathlib import Path

from symphra_modules import Module, ModuleManager


class UserModule(Module):
    """用户模块."""

    name = "user"
    dependencies = ["database"]

    def start(self) -> None:
        """启动模块."""
        pass


class DatabaseModule(Module):
    """数据库模块."""

    name = "database"
    dependencies = []

    def start(self) -> None:
        """启动模块."""
        pass


class TestModuleMonitoringIntegration:
    """模块监控功能集成测试."""

    def setup_method(self) -> None:
        """设置测试环境."""
        # 创建临时目录和模块文件
        self.temp_dir = tempfile.TemporaryDirectory()
        self.module_dir = Path(self.temp_dir.name) / "modules"
        self.module_dir.mkdir()

        # 创建数据库模块文件
        database_module_content = """
from symphra_modules import Module

class DatabaseModule(Module):
    name = "database"
    dependencies = []

    def start(self) -> None:
        pass
"""
        (self.module_dir / "database.py").write_text(database_module_content.strip())

        # 创建用户模块文件
        user_module_content = """
from symphra_modules import Module

class UserModule(Module):
    name = "user"
    dependencies = ["database"]

    def start(self) -> None:
        pass
"""
        (self.module_dir / "user.py").write_text(user_module_content.strip())

    def teardown_method(self) -> None:
        """清理测试环境."""
        self.temp_dir.cleanup()

    def test_monitoring_with_module_loading(self) -> None:
        """测试模块加载时的监控."""
        # 创建启用监控的ModuleManager
        manager = ModuleManager(str(self.module_dir), enable_monitoring=True)

        # 加载模块
        manager.load("user")

        # 启动模块
        manager.start("user")

        # 验证监控记录
        load_records = manager.get_load_records()
        start_records = manager.get_start_records()

        # 应该有3条加载记录（database, user, 以及load调用返回的user）
        assert len(load_records) >= 2
        assert len(start_records) >= 2

        # 验证模块名称
        loaded_modules = {record.module_name for record in load_records}
        started_modules = {record.module_name for record in start_records}

        assert "database" in loaded_modules
        assert "user" in loaded_modules
        assert "database" in started_modules
        assert "user" in started_modules

    def test_monitoring_data_export(self) -> None:
        """测试监控数据导出."""
        # 创建启用监控的ModuleManager
        manager = ModuleManager(str(self.module_dir), enable_monitoring=True)

        # 加载并启动模块
        manager.load("user")
        manager.start("user")

        # 导出监控数据
        data = manager.export_monitoring_data("json")

        # 验证导出的数据包含必要的字段
        assert '"load_records"' in data
        assert '"start_records"' in data
        assert '"memory_records"' in data
        assert '"method_call_records"' in data

        # 验证数据格式
        import json

        parsed_data = json.loads(data)
        assert "load_records" in parsed_data
        assert "start_records" in parsed_data
