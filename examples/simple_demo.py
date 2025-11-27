"""简单演示 - Symphra Modules."""

from symphra_modules import Module, ModuleManager


# 定义模块
class ConfigModule(Module):
    """配置模块 - 基础依赖."""

    name = "config"
    version = "1.0.0"

    def __init__(self) -> None:
        super().__init__()
        self.settings: dict[str, str] = {}

    def start(self) -> None:
        self.settings = {
            "db_host": "localhost",
            "db_port": "5432",
            "cache_ttl": "3600",
        }
        print("✅ 配置模块已启动")
        print(f"   设置: {self.settings}")

    def stop(self) -> None:
        self.settings.clear()
        print("🛑 配置模块已停止")


class DatabaseModule(Module):
    """数据库模块 - 依赖配置."""

    name = "database"
    version = "1.0.0"
    dependencies = ["config"]

    def __init__(self) -> None:
        super().__init__()
        self.connected = False

    def start(self) -> None:
        self.connected = True
        print("✅ 数据库已连接")

    def stop(self) -> None:
        self.connected = False
        print("🛑 数据库已断开")


class CacheModule(Module):
    """缓存模块 - 依赖配置."""

    name = "cache"
    version = "1.0.0"
    dependencies = ["config"]

    def __init__(self) -> None:
        super().__init__()
        self.running = False

    def start(self) -> None:
        self.running = True
        print("✅ 缓存已启动")

    def stop(self) -> None:
        self.running = False
        print("🛑 缓存已停止")


class UserModule(Module):
    """用户模块 - 依赖数据库和缓存."""

    name = "user"
    version = "1.0.0"
    dependencies = ["database", "cache"]

    def __init__(self) -> None:
        super().__init__()
        self.user_count = 0

    def start(self) -> None:
        self.user_count = 100
        print("✅ 用户模块已启动")
        print(f"   用户数量: {self.user_count}")

    def stop(self) -> None:
        print("🛑 用户模块已停止")


def main() -> None:
    """主函数."""
    print("=" * 60)
    print("Symphra Modules - 简单演示")
    print("=" * 60)
    print()

    # 创建临时模块目录
    import tempfile
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmpdir:
        # 写入模块文件
        modules = {
            "config.py": ConfigModule,
            "database.py": DatabaseModule,
            "cache.py": CacheModule,
            "user.py": UserModule,
        }

        for filename, module_class in modules.items():
            # 获取模块源代码
            import inspect

            source = inspect.getsource(module_class)
            # 写入文件
            module_file = Path(tmpdir) / filename
            with open(module_file, "w") as f:
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

        # 加载 user 模块 (自动加载所有依赖)
        print("📦 加载 user 模块 (自动解析依赖)...")
        user = manager.load("user")
        print(f"   user 模块已加载 (状态: {user.state.value})")
        print()

        # 启动所有模块
        print("🚀 启动所有模块...")
        print()
        for name in ["config", "database", "cache", "user"]:
            manager.start(name)
        print()

        # 显示模块状态
        print("📊 模块状态:")
        for name in modules_list:
            module = manager.get_module(name)
            if module:
                print(f"   {name}: {module.state.value}")
        print()

        # 停止所有模块
        print("🛑 停止所有模块...")
        print()
        for name in ["user", "cache", "database", "config"]:
            manager.stop(name)
        print()

        print("=" * 60)
        print("演示完成!")
        print("=" * 60)


if __name__ == "__main__":
    main()
