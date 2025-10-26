"""配置模块测试."""

from datetime import datetime

from symphra_modules.config import ModuleInfo, ModuleMetadata, ModuleState


def test_module_state_enum() -> None:
    """测试模块状态枚举."""
    assert ModuleState.NOT_INSTALLED == "not_installed"
    assert ModuleState.LOADED == "loaded"
    assert ModuleState.INSTALLED == "installed"
    assert ModuleState.STARTED == "started"
    assert ModuleState.STOPPED == "stopped"
    assert ModuleState.ERROR == "error"


def test_module_metadata_defaults() -> None:
    """测试模块元数据默认值."""
    metadata = ModuleMetadata(name="test_module")
    assert metadata.name == "test_module"
    assert metadata.type == "module"
    assert metadata.category is None
    assert metadata.tags == []
    assert metadata.version == "0.0.1"
    assert metadata.description == ""
    assert metadata.author == []
    assert metadata.dependencies == []
    assert metadata.optional_dependencies == []
    assert metadata.config_schema is None


def test_module_metadata_full() -> None:
    """测试完整的模块元数据."""
    metadata = ModuleMetadata(
        name="test_module",
        type="plugin",
        category="utils",
        tags=["test", "demo"],
        version="1.0.0",
        description="测试模块",
        author=[{"name": "Test", "email": "test@example.com"}],
        dependencies=["dep1", "dep2"],
        optional_dependencies=["opt1"],
        config_schema={"type": "object"},
    )
    assert metadata.name == "test_module"
    assert metadata.type == "plugin"
    assert metadata.category == "utils"
    assert metadata.tags == ["test", "demo"]
    assert metadata.version == "1.0.0"
    assert metadata.description == "测试模块"
    assert len(metadata.author) == 1
    assert metadata.dependencies == ["dep1", "dep2"]
    assert metadata.optional_dependencies == ["opt1"]
    assert metadata.config_schema == {"type": "object"}


def test_module_info_defaults() -> None:
    """测试模块信息默认值."""
    metadata = ModuleMetadata(name="test")
    info = ModuleInfo(metadata=metadata)
    assert info.metadata == metadata
    assert info.state == ModuleState.NOT_INSTALLED
    assert info.installed_at is None
    assert info.loaded_at is None
    assert info.started_at is None
    assert info.config == {}


def test_module_info_full() -> None:
    """测试完整的模块信息."""
    metadata = ModuleMetadata(name="test")
    now = datetime.now()
    config = {"key": "value"}

    info = ModuleInfo(
        metadata=metadata,
        state=ModuleState.STARTED,
        installed_at=now,
        loaded_at=now,
        started_at=now,
        config=config,
    )
    assert info.metadata == metadata
    assert info.state == ModuleState.STARTED
    assert info.installed_at == now
    assert info.loaded_at == now
    assert info.started_at == now
    assert info.config == config
