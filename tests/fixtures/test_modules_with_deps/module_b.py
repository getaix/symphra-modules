"""模块B - 循环依赖测试."""

from symphra_modules.abc import BaseModule
from symphra_modules.config import ModuleMetadata


class ModuleB(BaseModule):
    """模块B - 依赖模块A（形成循环）."""

    @property
    def metadata(self) -> ModuleMetadata:
        """模块元数据."""
        return ModuleMetadata(
            name="module_b",
            version="1.0.0",
            description="模块B",
            dependencies=["module_a"],
        )

    def start(self) -> None:
        """启动模块."""
        pass

    def stop(self) -> None:
        """停止模块."""
        pass
