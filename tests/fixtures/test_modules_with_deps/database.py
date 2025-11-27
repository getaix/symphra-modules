"""数据库模块 - 依赖 core."""

from symphra_modules.abc import BaseModule
from symphra_modules.config import ModuleMetadata


class DatabaseModule(BaseModule):
    """数据库模块 - 依赖 core."""

    @property
    def metadata(self) -> ModuleMetadata:
        """模块元数据."""
        return ModuleMetadata(
            name="database",
            version="1.0.0",
            description="数据库模块",
            dependencies=["core"],
        )

    def start(self) -> None:
        """启动模块."""
        pass

    def stop(self) -> None:
        """停止模块."""
        pass
