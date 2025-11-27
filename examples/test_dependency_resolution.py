"""测试依赖解析功能的演示脚本.

演示场景:
1. 正常依赖链加载 (order -> user -> database, cache)
2. 循环依赖检测 (需要手动创建循环依赖模块)
3. 缺失依赖检测
"""

import sys
from pathlib import Path

# 添加项目路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from symphra_modules import ModuleManager  # noqa: E402


def test_normal_dependency_chain():
    """测试正常的依赖链加载."""
    print("=" * 80)
    print("测试 1: 正常依赖链加载")
    print("=" * 80)
    print()

    # 创建模块管理器
    manager = ModuleManager(module_dirs=[str(Path(__file__).parent / "dependency_demo")])

    print("📦 场景: 加载 order 模块")
    print("   依赖链: order -> user -> [database, cache]")
    print()

    try:
        # 加载 order 模块,应该自动加载所有依赖
        order_module = manager.load_module("order")

        print("\n✅ 加载成功!")
        print(f"   Order 模块: {order_module.metadata.name}")

        # 检查依赖是否已加载
        print("\n📋 已加载的模块:")
        for name in ["database", "cache", "user", "order"]:
            if manager.registry.is_loaded(name):
                module = manager.registry.get(name)
                print(f"   ✓ {name}: {module.metadata.description}")

        print("\n🎯 验证: 依赖按正确顺序加载")
        print("   预期顺序: database, cache -> user -> order")

    except Exception as e:
        print(f"\n❌ 加载失败: {e}")
        import traceback

        traceback.print_exc()


def test_load_order():
    """测试加载顺序."""
    print("\n" + "=" * 80)
    print("测试 2: 验证加载顺序")
    print("=" * 80)
    print()

    manager = ModuleManager(module_dirs=[str(Path(__file__).parent / "dependency_demo")])

    print("📦 场景: 直接启动所有模块")
    print()

    try:
        # 加载 order 模块
        manager.load_module("order")

        # 启动所有模块,观察启动顺序
        print("🚀 启动所有模块:")
        for name in ["database", "cache", "user", "order"]:
            if manager.registry.is_loaded(name):
                manager.start_module(name)
                print(f"   ✓ {name} 已启动")

        print("\n✅ 所有模块已启动")

    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        import traceback

        traceback.print_exc()


def test_missing_dependency():
    """测试缺失依赖检测."""
    print("\n" + "=" * 80)
    print("测试 3: 缺失依赖检测")
    print("=" * 80)
    print()

    from symphra_modules.exceptions import ModuleDependencyError

    from symphra_modules import BaseModule, ModuleMetadata

    # 创建一个依赖不存在模块的测试模块
    class TestModule(BaseModule):
        @property
        def metadata(self) -> ModuleMetadata:
            return ModuleMetadata(
                name="test",
                dependencies=["nonexistent_module"],  # 不存在的依赖
            )

    manager = ModuleManager()

    print("📦 场景: 加载依赖不存在模块的模块")
    print("   test -> nonexistent_module (不存在)")
    print()

    try:
        # 手动注册测试模块类到管理器的发现缓存
        # (实际项目中这由 DirectoryLoader 完成)
        manager._modules_cache["test_dir"] = {"test": TestModule}

        # 尝试加载,应该报错
        manager.load_module("test", source="test_dir")

        print("❌ 未检测到缺失依赖 (这不应该发生!)")

    except ModuleDependencyError as e:
        print("✅ 成功检测到缺失依赖!")
        print(f"   错误: {e}")
        print(f"   模块: {e.module_name}")
        print(f"   缺失依赖: {e.missing_dependencies}")
    except Exception as e:
        print(f"⚠️  其他错误: {e}")


def test_dependency_info():
    """查看依赖解析信息."""
    print("\n" + "=" * 80)
    print("测试 4: 依赖解析信息")
    print("=" * 80)
    print()

    manager = ModuleManager(module_dirs=[str(Path(__file__).parent / "dependency_demo")])

    # 加载 order 模块
    manager.load_module("order")

    # 获取依赖解析器
    resolver = manager._dependency_resolver

    print("📊 依赖图信息:")
    print()

    for module_name in resolver.graph.get_all_modules():
        deps = resolver.graph.get_dependencies(module_name)
        dependents = resolver.graph.get_dependents(module_name)

        print(f"📦 {module_name}")
        if deps:
            print(f"   依赖: {', '.join(deps)}")
        else:
            print("   依赖: (无)")

        if dependents:
            print(f"   被依赖: {', '.join(dependents)}")
        else:
            print("   被依赖: (无)")

        # 获取完整依赖链
        chain = resolver.get_dependency_chain(module_name)
        print(f"   加载顺序: {' -> '.join(chain)}")
        print()


if __name__ == "__main__":
    print("🎯 Symphra Modules - 依赖解析功能演示")
    print()

    # 运行所有测试
    test_normal_dependency_chain()
    test_load_order()
    test_missing_dependency()
    test_dependency_info()

    print("\n" + "=" * 80)
    print("✅ 所有测试完成!")
    print("=" * 80)
