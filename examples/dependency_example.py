"""依赖解析使用示例."""

from symphra_modules import DependencyResolver, ModuleMetadata


def main() -> None:
    """主函数."""
    # 创建依赖解析器
    resolver = DependencyResolver()

    # 添加模块及其依赖关系
    # 模块 A: 无依赖
    resolver.add_module(
        ModuleMetadata(
            name="module_a",
            version="1.0.0",
            description="基础模块 A",
            dependencies=[],
        )
    )

    # 模块 B: 依赖 A
    resolver.add_module(
        ModuleMetadata(
            name="module_b",
            version="1.0.0",
            description="模块 B，依赖 A",
            dependencies=["module_a"],
        )
    )

    # 模块 C: 依赖 A 和 B
    resolver.add_module(
        ModuleMetadata(
            name="module_c",
            version="1.0.0",
            description="模块 C，依赖 A 和 B",
            dependencies=["module_a", "module_b"],
        )
    )

    # 模块 D: 依赖 B
    resolver.add_module(
        ModuleMetadata(
            name="module_d",
            version="1.0.0",
            description="模块 D，依赖 B",
            dependencies=["module_b"],
        )
    )

    # 解析加载顺序
    print("\n=== 完整加载顺序（拓扑排序） ===")
    load_order = resolver.resolve()
    print(f"加载顺序: {' -> '.join(load_order)}")

    # 获取单个模块的加载顺序
    print("\n=== 加载模块 C 所需的顺序 ===")
    module_c_order = resolver.get_load_order_for_module("module_c")
    print(f"加载顺序: {' -> '.join(module_c_order)}")

    print("\n=== 加载模块 D 所需的顺序 ===")
    module_d_order = resolver.get_load_order_for_module("module_d")
    print(f"加载顺序: {' -> '.join(module_d_order)}")

    # 演示循环依赖检测
    print("\n=== 循环依赖检测示例 ===")
    resolver_circular = DependencyResolver()

    resolver_circular.add_module(ModuleMetadata(name="module_x", dependencies=["module_y"]))
    resolver_circular.add_module(ModuleMetadata(name="module_y", dependencies=["module_x"]))

    try:
        resolver_circular.resolve()
    except Exception as e:
        print(f"检测到循环依赖: {e}")


if __name__ == "__main__":
    main()
