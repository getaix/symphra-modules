"""API模块 - 依赖 core 和 database."""

from symphra_modules.abc import BaseModule
from symphra_modules.config import ModuleMetadata


class ApiModule(BaseModule):
    """API模块 - 依赖 core 和 database."""

    @property
    def metadata(self) -> ModuleMetadata:
        """模块元数据."""
        return ModuleMetadata(
            name="api",
            version="1.0.0",
            description="API模块",
            dependencies=["core", "database"],
        )

    def start(self) -> None:
        """启动模块."""
        pass

    def stop(self) -> None:
        """停止模块."""
        pass
