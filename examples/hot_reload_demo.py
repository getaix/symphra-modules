"""热重载演示."""

import tempfile
import time
from pathlib import Path
from threading import Thread

from symphra_modules import Module, ModuleManager


class DemoModule(Module):
    """演示模块."""

    name = "demo"
    version = "1.0.0"
    dependencies = []

    def __init__(self) -> None:
        super().__init__()
        self.version_num = 1
        self.started = False

    def start(self) -> None:
        """启动模块."""
        self.started = True
        print(f"✅ 模块启动 (版本 {self.version_num})")

    def stop(self) -> None:
        """停止模块."""
        self.started = False
        print(f"🛑 模块停止 (版本 {self.version_num})")


def create_module_file(directory: str, version: int = 1) -> None:
    """创建模块文件."""
    content = f"""
from symphra_modules import Module

class DemoModule(Module):
    name = "demo"
    version = "1.0.{version}"
    dependencies = []

    def __init__(self) -> None:
        super().__init__()
        self.version_num = {version}
        self.started = False

    def start(self) -> None:
        self.started = True
        print("✅ 模块启动 (版本 {{}})".format(self.version_num))

    def stop(self) -> None:
        self.started = False
        print("🛑 模块停止 (版本 {{}})".format(self.version_num))
"""

    module_file = Path(directory) / "demo.py"
    with open(module_file, "w") as f:
        f.write(content)


def main() -> None:
    """主函数."""
    print("=" * 60)
    print("Symphra Modules - 热重载演示")
    print("=" * 60)
    print()
    print("💡 演示说明:")
    print("1. 模块管理器将监控模块目录")
    print("2. 修改模块文件后，系统会自动重载模块")
    print("3. 按 Ctrl+C 退出演示")
    print()

    # 创建临时模块目录
    with tempfile.TemporaryDirectory() as tmpdir:
        print(f"📁 模块目录: {tmpdir}")
        print()

        # 创建初始模块文件
        create_module_file(tmpdir, 1)
        print("📄 创建初始模块文件 (版本 1)")
        print()

        # 创建模块管理器并启用热重载
        manager = ModuleManager(tmpdir, enable_hot_reload=True)
        manager.enable_hot_reload_monitoring()
        print("🔍 启用热重载监控")
        print()

        # 加载并启动模块
        print("📦 加载演示模块...")
        manager.load("demo")
        manager.start("demo")
        print()

        def update_module() -> None:
            """更新模块文件."""
            time.sleep(3)
            print("🔄 3秒后更新模块文件到版本 2...")
            time.sleep(3)
            create_module_file(tmpdir, 2)
            print("📄 模块文件已更新到版本 2")

            time.sleep(3)
            print("🔄 3秒后更新模块文件到版本 3...")
            time.sleep(3)
            create_module_file(tmpdir, 3)
            print("📄 模块文件已更新到版本 3")

        # 启动更新线程
        update_thread = Thread(target=update_module)
        update_thread.daemon = True
        update_thread.start()

        # 等待用户中断
        try:
            print("⏳ 监控中... 修改模块文件将触发自动重载")
            print("   (等待30秒后自动退出)")
            time.sleep(30)
        except KeyboardInterrupt:
            print("\n👋 演示结束")

        # 禁用监控
        manager.disable_hot_reload_monitoring()
        print("🔍 热重载监控已禁用")


if __name__ == "__main__":
    main()
