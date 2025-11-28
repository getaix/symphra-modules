"""模块加载性能测试.

测试大量模块加载、依赖解析的性能表现。
"""

import tempfile
import time
from pathlib import Path

import pytest

from symphra_modules import ModuleManager


class TestLoadPerformance:
    """测试模块加载性能."""

    def test_load_single_module_performance(self) -> None:
        """测试单个模块加载性能."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建一个简单模块
            module_code = """
from symphra_modules import Module

class TestModule(Module):
    name = "test"
"""
            Path(tmpdir, "test.py").write_text(module_code)

            manager = ModuleManager(tmpdir)

            # 测量加载时间
            start = time.time()
            manager.load("test")
            elapsed = time.time() - start

            # 单个模块加载应该在100ms以内
            assert elapsed < 0.1, f"加载耗时 {elapsed:.3f}s，超过阈值"

    def test_load_multiple_modules_performance(self) -> None:
        """测试批量加载多个模块的性能."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建50个简单模块
            num_modules = 50
            for i in range(num_modules):
                module_code = f"""
from symphra_modules import Module

class Module{i}(Module):
    name = "module{i}"
"""
                Path(tmpdir, f"module{i}.py").write_text(module_code)

            manager = ModuleManager(tmpdir)

            # 测量批量加载时间
            start = time.time()
            manager.load_all()
            elapsed = time.time() - start

            # 50个模块应该在2秒内加载完成
            assert elapsed < 2.0, f"加载{num_modules}个模块耗时 {elapsed:.3f}s，超过阈值"

            # 计算平均每个模块的加载时间
            avg_time = elapsed / num_modules
            print(f"\n平均每个模块加载耗时: {avg_time*1000:.2f}ms")

    def test_load_with_dependencies_performance(self) -> None:
        """测试带依赖的模块加载性能."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建一个依赖链: a -> b -> c -> d -> e
            deps = ["a", "b", "c", "d", "e"]
            for i, name in enumerate(deps):
                dep = deps[i + 1] if i < len(deps) - 1 else None
                if dep:
                    module_code = f"""
from symphra_modules import Module

class Module{name.upper()}(Module):
    name = "{name}"
    dependencies = ["{dep}"]
"""
                else:
                    module_code = f"""
from symphra_modules import Module

class Module{name.upper()}(Module):
    name = "{name}"
"""
                Path(tmpdir, f"{name}.py").write_text(module_code)

            manager = ModuleManager(tmpdir)

            # 测量依赖解析和加载时间
            start = time.time()
            manager.load("a")
            elapsed = time.time() - start

            # 5层依赖链应该在500ms内完成
            assert elapsed < 0.5, f"依赖解析和加载耗时 {elapsed:.3f}s，超过阈值"

    def test_discover_performance(self) -> None:
        """测试模块发现性能."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建100个模块
            num_modules = 100
            for i in range(num_modules):
                module_code = f"""
from symphra_modules import Module

class Module{i}(Module):
    name = "module{i}"
"""
                Path(tmpdir, f"module{i}.py").write_text(module_code)

            # 测量发现时间
            start = time.time()
            manager = ModuleManager(tmpdir)
            elapsed = time.time() - start

            # 发现100个模块应该在1秒内完成
            assert elapsed < 1.0, f"发现{num_modules}个模块耗时 {elapsed:.3f}s，超过阈值"

            # 验证发现的模块数量
            assert len(manager.list_modules()) == num_modules

    def test_rediscover_performance(self) -> None:
        """测试重新发现模块的性能."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建50个模块
            for i in range(50):
                module_code = f"""
from symphra_modules import Module

class Module{i}(Module):
    name = "module{i}"
"""
                Path(tmpdir, f"module{i}.py").write_text(module_code)

            manager = ModuleManager(tmpdir)
            initial_count = len(manager.list_modules())

            # 测量重新发现时间
            start = time.time()
            manager.rediscover()
            elapsed = time.time() - start

            # 重新发现应该很快（因为是重新扫描）
            assert elapsed < 0.5, f"重新发现耗时 {elapsed:.3f}s，超过阈值"

            # 模块数量应该不变
            assert len(manager.list_modules()) == initial_count

    def test_complex_dependency_graph_performance(self) -> None:
        """测试复杂依赖图的性能."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建一个菱形依赖图
            # app -> [db, cache] -> config
            modules = {
                "config": [],
                "db": ["config"],
                "cache": ["config"],
                "app": ["db", "cache"],
            }

            for name, deps in modules.items():
                dep_str = str(deps) if deps else "[]"
                module_code = f"""
from symphra_modules import Module

class {name.capitalize()}Module(Module):
    name = "{name}"
    dependencies = {dep_str}
"""
                Path(tmpdir, f"{name}.py").write_text(module_code)

            manager = ModuleManager(tmpdir)

            # 测量加载时间
            start = time.time()
            manager.load("app")
            elapsed = time.time() - start

            # 菱形依赖图应该在200ms内完成
            assert elapsed < 0.2, f"复杂依赖图解析耗时 {elapsed:.3f}s，超过阈值"

            # 验证所有依赖都已加载
            assert manager.get_module("config") is not None
            assert manager.get_module("db") is not None
            assert manager.get_module("cache") is not None
            assert manager.get_module("app") is not None

    def test_start_all_performance(self) -> None:
        """测试批量启动模块的性能."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建30个模块
            num_modules = 30
            for i in range(num_modules):
                module_code = f"""
from symphra_modules import Module

class Module{i}(Module):
    name = "module{i}"

    def start(self):
        pass
"""
                Path(tmpdir, f"module{i}.py").write_text(module_code)

            manager = ModuleManager(tmpdir)
            manager.load_all()

            # 测量批量启动时间
            start = time.time()
            manager.start_all()
            elapsed = time.time() - start

            # 30个模块应该在1秒内启动完成
            assert elapsed < 1.0, f"启动{num_modules}个模块耗时 {elapsed:.3f}s，超过阈值"

    def test_memory_usage_with_many_modules(self) -> None:
        """测试大量模块的内存使用."""
        import sys

        with tempfile.TemporaryDirectory() as tmpdir:
            # 创建100个模块
            num_modules = 100
            for i in range(num_modules):
                module_code = f"""
from symphra_modules import Module

class Module{i}(Module):
    name = "module{i}"
"""
                Path(tmpdir, f"module{i}.py").write_text(module_code)

            # 测量内存使用
            manager = ModuleManager(tmpdir)

            # 获取manager对象大小（简单估计）
            size = sys.getsizeof(manager)

            # 管理器本身应该是轻量级的（< 10KB）
            assert size < 10 * 1024, f"管理器大小 {size} bytes，超过阈值"

            # 加载所有模块
            manager.load_all()

            # 验证模块加载成功
            assert len(manager.list_loaded_modules()) == num_modules
