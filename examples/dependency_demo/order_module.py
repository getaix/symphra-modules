"""订单模块 - 依赖 user 和 database (形成依赖链)."""

from symphra_modules import BaseModule, ModuleMetadata


class OrderModule(BaseModule):
    """订单管理模块 - 依赖用户模块."""

    @property
    def metadata(self) -> ModuleMetadata:
        return ModuleMetadata(
            name="order",
            version="1.0.0",
            description="订单管理服务",
            dependencies=["user", "database"],  # 依赖链: order -> user -> database
        )

    def start(self) -> None:
        print("✅ 订单模块已启动 - 依赖 user 和 database")

    def stop(self) -> None:
        print("🛑 订单模块已停止")

    def create_order(self, user_id: int, product: str) -> dict:
        """创建订单."""
        return {"order_id": 12345, "user_id": user_id, "product": product, "status": "created"}
