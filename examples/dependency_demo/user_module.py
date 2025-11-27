"""用户模块 - 依赖 database 和 cache."""

from symphra_modules import BaseModule, ModuleMetadata


class UserModule(BaseModule):
    """用户管理模块 - 依赖数据库和缓存."""

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="user",
            version="1.0.0",
            description="用户管理服务",
            dependencies=["database", "cache"],  # 声明依赖
        )

    def start(self) -> None:
        print("✅ 用户模块已启动 - 依赖 database 和 cache")

    def stop(self) -> None:
        print("🛑 用户模块已停止")

    def get_user(self, user_id: int) -> dict:
        """获取用户信息."""
        # 注意: 这里只是演示,实际应该通过服务定位器获取依赖
        return {"id": user_id, "name": f"User_{user_id}", "email": f"user{user_id}@example.com"}
