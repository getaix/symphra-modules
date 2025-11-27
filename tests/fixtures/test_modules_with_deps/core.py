"""基础模块 - 无依赖."""

from symphra_modules.abc import BaseModule
from symphra_modules.config import ModuleMetadata


class CoreModule(BaseModule):
    """核心模块 - 无依赖."""

    @property
    def metadata(self) -> ModuleMetadata:
        """模块元数据."""
        return ModuleMetadata(
            name="core",
            version="1.0.0",
            description="核心模块",
            dependencies=[],
        )

    def start(self) -> None:
        """启动模块."""
        pass

    def stop(self) -> None:
        """停止模块."""
        pass
