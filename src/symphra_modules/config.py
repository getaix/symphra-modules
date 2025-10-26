"""模块配置和元数据定义."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class ModuleState(StrEnum):
    """模块状态枚举."""

    NOT_INSTALLED = "not_installed"  # 未安装
    LOADED = "loaded"  # 已加载
    INSTALLED = "installed"  # 已安装
    STARTED = "started"  # 已启动
    STOPPED = "stopped"  # 已停止
    ERROR = "error"  # 错误


@dataclass
class ModuleMetadata:
    """模块元数据."""

    name: str  # 模块名称
    type: str = "module"  # 模块类型
    category: str | None = None  # 模块类别，默认为未分类
    tags: list[str] = field(default_factory=list)  # 标签
    version: str = "0.0.1"  # 版本号
    description: str = ""  # 描述信息
    author: list[dict[str, str]] = field(default_factory=list)  # 作者信息
    dependencies: list[str] = field(default_factory=list)  # 必需依赖
    optional_dependencies: list[str] = field(default_factory=list)  # 可选依赖
    config_schema: dict[str, Any] | None = None  # 配置模式


@dataclass
class ModuleInfo:
    """模块信息."""

    metadata: ModuleMetadata  # 元数据
    state: ModuleState = ModuleState.NOT_INSTALLED  # 当前状态
    installed_at: datetime | None = None  # 安装时间
    loaded_at: datetime | None = None  # 加载时间
    started_at: datetime | None = None  # 启动时间
    config: dict[str, Any] = field(default_factory=dict)  # 当前配置
