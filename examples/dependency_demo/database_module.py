"""数据库模块 - 基础服务,无依赖."""

from symphra_modules import BaseModule, ModuleMetadata


class DatabaseModule(BaseModule):
    """数据库连接模块."""

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="database",
            version="1.0.0",
            description="提供数据库连接服务",
            dependencies=[],  # 无依赖
        )

    def start(self) -> None:
        print("✅ 数据库模块已启动 - 连接建立")

    def stop(self) -> None:
        print("🛑 数据库模块已停止 - 连接关闭")

    def get_connection(self) -> str:
        """获取数据库连接."""
        return "DatabaseConnection(host=localhost, db=myapp)"
