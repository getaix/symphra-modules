"""模块A - 循环依赖测试."""

from symphra_modules.abc import BaseModule
from symphra_modules.config import ModuleMetadata


class ModuleA(BaseModule):
    """模块A - 依赖模块B（形成循环）."""

    @property
    def metadata(self) -> ModuleMetadata:
        """模块元数据."""
        return ModuleMetadata(
            name="module_a",
            version="1.0.0",
            description="模块A",
            dependencies=["module_b"],
        )

    def start(self) -> None:
        """启动模块."""
        pass

    def stop(self) -> None:
        """停止模块."""
        pass
