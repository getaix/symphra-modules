"""基础使用示例."""

from symphra_modules import BaseModule, ModuleManager, ModuleMetadata


# 定义一个示例模块
class HelloModule(BaseModule):
    """示例模块 - Hello World."""

    @property
    def metadata(self) -> ModuleMetadata:
        """模块元数据."""
        return ModuleMetadata(
            name="hello",
            version="1.0.0",
            description="一个简单的 Hello World 模块",
            author=[{"name": "Demo", "email": "demo@example.com"}],
        )

    def start(self) -> None:
        """启动模块."""
        print(f"Hello from {self.metadata.name}!")

    def stop(self) -> None:
        """停止模块."""
        print(f"Goodbye from {self.metadata.name}!")


def main() -> None:
    """主函数."""
    # 创建模块管理器
    manager = ModuleManager(module_dirs=["plugins"])

    # 手动注册模块（在实际使用中，模块会从目录自动加载）
    manager.registry.register("hello", HelloModule)

    # 安装模块
    print("\n=== 安装模块 ===")
    manager.install_module("hello")

    # 启动模块
    print("\n=== 启动模块 ===")
    manager.start_module("hello")

    # 检查状态
    print("\n=== 模块状态 ===")
    print(f"已加载的模块: {manager.list_modules()}")
    print(f"已安装的模块: {manager.list_installed_modules()}")

    # 停止模块
    print("\n=== 停止模块 ===")
    manager.stop_module("hello")

    # 卸载模块
    print("\n=== 卸载模块 ===")
    manager.uninstall_module("hello")


if __name__ == "__main__":
    main()
