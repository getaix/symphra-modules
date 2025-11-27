"""异步模块演示."""

import asyncio
import tempfile
from pathlib import Path

from symphra_modules import Module, ModuleManager


class AsyncDatabaseModule(Module):
    """异步数据库模块."""

    name = "async_database"
    version = "1.0.0"
    dependencies = []

    def __init__(self) -> None:
        super().__init__()
        self.connected = False

    async def start_async(self) -> None:
        """异步启动数据库连接."""
        print("⏳ 正在连接数据库...")
        await asyncio.sleep(0.1)  # 模拟异步连接
        self.connected = True
        print("✅ 数据库连接成功")

    async def stop_async(self) -> None:
        """异步关闭数据库连接."""
        print("⏳ 正在关闭数据库连接...")
        await asyncio.sleep(0.1)  # 模拟异步关闭
        self.connected = False
        print("🛑 数据库连接已关闭")


class AsyncCacheModule(Module):
    """异步缓存模块."""

    name = "async_cache"
    version = "1.0.0"
    dependencies = []

    def __init__(self) -> None:
        super().__init__()
        self.running = False

    async def start_async(self) -> None:
        """异步启动缓存."""
        print("⏳ 正在启动缓存...")
        await asyncio.sleep(0.05)  # 模拟异步启动
        self.running = True
        print("✅ 缓存启动成功")

    async def stop_async(self) -> None:
        """异步停止缓存."""
        print("⏳ 正在停止缓存...")
        await asyncio.sleep(0.05)  # 模拟异步停止
        self.running = False
        print("🛑 缓存已停止")


class AsyncUserModule(Module):
    """异步用户模块."""

    name = "async_user"
    version = "1.0.0"
    dependencies = ["async_database", "async_cache"]

    def __init__(self) -> None:
        super().__init__()
        self.initialized = False

    async def start_async(self) -> None:
        """异步启动用户模块."""
        print("⏳ 正在初始化用户模块...")
        await asyncio.sleep(0.05)  # 模拟异步初始化
        self.initialized = True
        print("✅ 用户模块初始化成功")

    async def stop_async(self) -> None:
        """异步停止用户模块."""
        print("⏳ 正在清理用户模块...")
        await asyncio.sleep(0.05)  # 模拟异步清理
        self.initialized = False
        print("🛑 用户模块已清理")


async def main() -> None:
    """主函数."""
    print("=" * 60)
    print("Symphra Modules - 异步模块演示")
    print("=" * 60)
    print()

    # 创建临时模块目录
    with tempfile.TemporaryDirectory() as tmpdir:
        # 写入模块文件
        modules = {
            "async_database.py": AsyncDatabaseModule,
            "async_cache.py": AsyncCacheModule,
            "async_user.py": AsyncUserModule,
        }

        for filename, module_class in modules.items():
            # 获取模块源代码
            import inspect

            source = inspect.getsource(module_class)

            # 写入文件
            module_file = Path(tmpdir) / filename
            with open(module_file, "w") as f:
                f.write("import asyncio\n")
                f.write("from symphra_modules import Module\n\n")
                f.write(source)

        print(f"📁 临时模块目录: {tmpdir}")
        print()

        # 创建模块管理器
        print("🔍 发现模块...")
        manager = ModuleManager(tmpdir)

        # 列出所有模块
        modules_list = manager.list_modules()
        print(f"   找到 {len(modules_list)} 个模块: {', '.join(modules_list)}")
        print()

        # 异步加载 user 模块 (自动加载所有依赖)
        print("📦 异步加载 user 模块 (自动解析依赖)...")
        await manager.load_async("async_user")
        print("   user 模块已加载")
        print()

        # 异步启动所有模块
        print("🚀 异步启动所有模块...")
        print()

        # 按依赖顺序启动
        await manager.start_async("async_database")
        await manager.start_async("async_cache")
        await manager.start_async("async_user")

        print()

        # 显示模块状态
        print("📊 模块状态:")
        for name in ["async_database", "async_cache", "async_user"]:
            module = manager.get_module(name)
            if module:
                print(f"   {name}: {module._state.value}")
        print()

        # 异步停止所有模块
        print("🛑 异步停止所有模块...")
        print()

        # 按依赖反序停止
        await manager.stop_async("async_user")
        await manager.stop_async("async_cache")
        await manager.stop_async("async_database")

        print()

        print("=" * 60)
        print("异步演示完成!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
