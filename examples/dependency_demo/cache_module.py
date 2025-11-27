"""缓存模块 - 基础服务,无依赖."""

from symphra_modules import BaseModule, ModuleMetadata


class CacheModule(BaseModule):
    """缓存服务模块."""

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="cache",
            version="1.0.0",
            description="提供缓存服务",
            dependencies=[],  # 无依赖
        )

    def start(self) -> None:
        print("✅ 缓存模块已启动 - Redis 连接建立")

    def stop(self) -> None:
        print("🛑 缓存模块已停止 - Redis 连接关闭")

    def get(self, key: str) -> str | None:
        """从缓存获取数据."""
        return f"cached_value_for_{key}"

    def set(self, key: str, value: str) -> None:
        """设置缓存数据."""
        print(f"缓存已设置: {key} = {value}")
